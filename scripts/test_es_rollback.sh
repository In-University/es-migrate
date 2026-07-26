#!/usr/bin/env bash
#
# Tests for es_rollback.sh, driven against fake_es.py -- no real
# clusters needed. Two halves: the happy path end to end, then the failure
# paths, which are the ones that actually matter for a tool that deletes
# documents.
#
#   ./test_es_rollback.sh
#
# Requires: bash, curl, jq, python3.
#
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

T="$HERE/.testrun"
rm -rf "$T"; mkdir -p "$T"; cd "$T"
PORT="${PORT:-19277}"
# Probe by running it, not by command -v: on Windows `python3` is often a
# Microsoft Store stub that exists on PATH but is not an interpreter.
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 &&
     "$c" -c 'import sys;sys.exit(0 if sys.version_info[0]==3 else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || { echo "no python3 found (needed only for the fake ES)" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq not found" >&2; exit 1; }

PASS=0; FAIL=0
ok()  { printf '  ok   %s\n' "$1"; PASS=$((PASS + 1)); }
bad() { printf '  FAIL %s\n     expected: %s\n     actual:   %s\n' "$1" "$2" "$3"; FAIL=$((FAIL + 1)); }
eq()  { [ "$2" = "$3" ] && ok "$1" || bad "$1" "$2" "$3"; }

# ES6 holds doc-00..doc-19 as of cutover. Since then, on ES9: doc-01..doc-08
# were updated, doc-20 and doc-21 created, doc-00 hard-deleted. So the delta
# is 10 documents and exactly one delete is pending -- 1/22, comfortably
# under the default blast-radius guard, so the happy path runs unattended.
"$PY" - <<'PY'
import json
old, new = "2026-07-01T00:00:00Z", "2026-07-20T00:00:00Z"
es6 = {f"doc-{i:02d}": {"id": f"doc-{i:02d}", "title": f"orig-{i}", "updated_at": old}
       for i in range(20)}
es9 = {k: dict(v) for k, v in es6.items()}
for i in range(1, 9):
    es9[f"doc-{i:02d}"] = {"id": f"doc-{i:02d}", "title": f"UPD-{i}", "updated_at": new}
for i in (20, 21):
    es9[f"doc-{i:02d}"] = {"id": f"doc-{i:02d}", "title": f"new-{i}", "updated_at": new}
del es9["doc-00"]
json.dump({"store": {
    "bench-es6": {"docs": es6, "settings": {"refresh_interval": "-1"}, "meta": {}},
    "bench-es9": {"docs": es9, "settings": {"refresh_interval": "1s"},
                  "meta": {"cutover_at": "2026-07-10T00:00:00Z"}}}},
    open("seed.json", "w"))
PY

"$PY" "$HERE/fake_es.py" "$PORT" seed.json >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null; :' EXIT
sleep 2

BASE="http://127.0.0.1:$PORT"
export ES6_URL="$BASE" ES9_URL="$BASE" ELASTIC_PW=elastic
export FREEZE_WAIT=1 PAGE_SIZE=3 SAMPLE_N=5

RB=(bash "$HERE/es_rollback.sh")
post()  { curl -s -XPOST "$BASE/$1" -H 'Content-Type: application/json' -d "${2:-{\}}" >/dev/null; }
fresh() { post _reload; }                        # reseed and clear all faults
fault() { post _fault "$1"; }
cnt()   { curl -s -u e:e "$BASE/$1/_count" | jq -r .count; }
ids()   { curl -s -u e:e -XPOST "$BASE/$1/_search" -H 'Content-Type: application/json' \
            -d '{"size":500,"sort":["_doc"],"_source":false,"query":{"match_all":{}}}' \
          | jq -r '[.hits.hits[]._id] | sort | join(" ")'; }
title() { curl -s -u e:e -XPOST "$BASE/$1/_doc/_mget" -H 'Content-Type: application/json' \
            -d "{\"ids\":[\"$2\"]}" | jq -r '.docs[0] | if .found then ._source.title else "ABSENT" end'; }
ph()    { grep "^$2=" "$1/state.env" 2>/dev/null | cut -d= -f2; }
go()    { local d="$1"; shift; rm -rf "$d"; STATE_DIR="$d" "${RB[@]}" "$@"; }

echo "== plan writes nothing =="
fresh
go .p plan >plan.txt 2>&1
eq "reports the 10-doc delta" "yes" "$(grep -qE 'delta since .*: 10 doc' plan.txt && echo yes || echo no)"
eq "ES6 untouched" "20" "$(cnt bench-es6)"

echo
echo "== happy path: delta -> gate -> reconcile -> verify =="
fresh
go .h run >h.txt 2>&1; RC=$?
eq "run completes" "0" "$RC"
eq "phases ran in order" "yes" \
   "$(grep -c 'phase [0-4]' h.txt | awk '{print ($1 == 5) ? "yes" : "no"}')"
eq "ES6 count matches ES9" "$(cnt bench-es9)" "$(cnt bench-es6)"
eq "ES6 id set matches ES9" "$(ids bench-es9)" "$(ids bench-es6)"
eq "updates landed" "UPD-3" "$(title bench-es6 doc-03)"
eq "creates landed" "new-20" "$(title bench-es6 doc-20)"
eq "the ES9 delete propagated" "ABSENT" "$(title bench-es6 doc-00)"
eq "exactly one delete" "1" "$(ph .h DELETED)"
eq "nothing needed repair" "0" "$(ph .h REPAIRED)"
eq "verify passed" "yes" "$(grep -q 'VERIFY PASSED' h.txt && echo yes || echo no)"
eq "final phase DONE" "DONE" "$(ph .h PHASE)"

echo
echo "== the journal records which operation wrote each row =="
# Layout: seq \t id \t op \t found \t source. `op` is audit metadata; `found`
# is what undo keys off. Both create and update go through the delta path --
# only the ES6 _mget result tells them apart, so `found` carries that.
jj() { zcat .h/journal.tsv.gz | awk -F'\t' "$1" | wc -l | tr -d ' '; }
eq "every row has five columns" "0" "$(jj 'NF != 5')"
eq "8 updates journaled with their pre-image" "8" "$(jj '$3=="delta" && $4==1')"
eq "2 creates journaled as id-only" "2" "$(jj '$3=="delta" && $4==0')"
eq "1 delete journaled with its pre-image" "1" "$(jj '$3=="delete" && $4==1')"
eq "no repairs were needed" "0" "$(jj '$3=="repair"')"
eq "a create row carries no source" "{}" \
   "$(zcat .h/journal.tsv.gz | awk -F'\t' '$3=="delta" && $4==0 {print $5; exit}')"
eq "an update row carries the old title" "orig-3" \
   "$(zcat .h/journal.tsv.gz | awk -F'\t' '$2=="doc-03" {print $5; exit}' | jq -r .title)"

echo
echo "== undo restores ES6 exactly =="
STATE_DIR=.h "${RB[@]}" undo >undo.txt 2>&1; RC=$?
eq "undo exits clean" "0" "$RC"
eq "back to 20 docs" "20" "$(cnt bench-es6)"
eq "overwritten doc restored to its pre-image" "orig-3" "$(title bench-es6 doc-03)"
eq "deleted doc restored" "orig-0" "$(title bench-es6 doc-00)"
eq "doc created by the sync removed again" "ABSENT" "$(title bench-es6 doc-20)"

echo
echo "== a second run archives the old journal instead of mixing into it =="
# Sequence numbers restart per run, so two runs sharing one journal would
# make undo's "lowest seq per id" ambiguous and let it restore a post-sync
# image as if it were the original.
fresh
STATE_DIR=.h "${RB[@]}" reset >/dev/null 2>&1
eq "reset keeps the journal for undo" "yes" "$([ -s .h/journal.tsv.gz ] && echo yes || echo no)"
STATE_DIR=.h "${RB[@]}" run >h2.txt 2>&1
eq "the new run archived it" "yes" "$(grep -q 'previous journal archived' h2.txt && echo yes || echo no)"
eq "exactly one archive exists" "1" "$(ls .h/journal.*.tsv.gz 2>/dev/null | wc -l | tr -d ' ')"
eq "the live journal covers only this run" "yes" \
   "$(zcat .h/journal.tsv.gz | awk -F'\t' '{print $1}' | sort -n | uniq -d | wc -l \
      | awk '{print ($1 == 0) ? "yes" : "no"}')"
STATE_DIR=.h "${RB[@]}" undo >/dev/null 2>&1
eq "undo still restores the pre-image" "orig-3" "$(title bench-es6 doc-03)"

echo
echo "== freeze check catches an ES9 still taking writes =="
fresh; fault '{"freeze_break":true}'
go .f preflight >f.txt 2>&1; RC=$?
eq "preflight fails" "1" "$RC"
eq "and says why" "yes" "$(grep -q 'still taking writes' f.txt && echo yes || echo no)"

echo
echo "== a rejected document blocks the delete phase =="
# doc-03 is refused by ES6, so the delta is incomplete. Reconcile must not
# run: the id diff would otherwise read doc-03 as deleted on ES9 and remove
# it -- a failed sync turning into data loss.
fresh; fault '{"bulk_fatal_id":"doc-03"}'
go .d run >d.txt 2>&1; RC=$?
eq "run stops at the gate" "1" "$RC"
eq "gate explains itself" "yes" "$(grep -q 'gate FAILED.*rejected by ES6' d.txt && echo yes || echo no)"
eq "phase stopped at DELTA_DONE" "DELTA_DONE" "$(ph .d PHASE)"
eq "no delete was ever attempted" "" "$(ph .d DELETED)"
eq "the doc deleted on ES9 is still on ES6" "orig-0" "$(title bench-es6 doc-00)"
eq "rejected doc is dead-lettered" "doc-03" "$(jq -r '._id' <.d/deadletter.ndjson | head -1)"
eq "with its error type" "mapper_parsing_exception" "$(jq -r '.error.type' <.d/deadletter.ndjson | head -1)"

echo
echo "== ALLOW_PARTIAL is the only way past, and it is loud =="
fault '{}'
ALLOW_PARTIAL=true STATE_DIR=.d "${RB[@]}" resume >d2.txt 2>&1
eq "override lets reconcile run" "1" "$(ph .d DELETED)"
eq "and it warns" "yes" "$(grep -q 'gate passed with 1 dead-lettered' d2.txt && echo yes || echo no)"

echo
echo "== transient rejections are retried, not lost =="
fresh; fault '{"bulk_429_every":3}'
go .r run >r.txt 2>&1; RC=$?
eq "run completes" "0" "$RC"
eq "nothing dead-lettered" "0" "$(ph .r DL_COUNT)"
eq "counts converge" "$(cnt bench-es9)" "$(cnt bench-es6)"
eq "retries were logged" "yes" "$(grep -q 'rejected (transient)' r.txt && echo yes || echo no)"

echo
echo "== mid-delta failure checkpoints, then resumes =="
fresh; fault '{"bulk_fail_after":2}'
rm -rf .c
MAX_RETRY=2 STATE_DIR=.c "${RB[@]}" run >c.txt 2>&1; RC=$?
eq "run aborts" "1" "$RC"
eq "it says state was checkpointed" "yes" "$(grep -q 'state checkpointed' c.txt && echo yes || echo no)"
eq "partial progress recorded" "yes" "$([ "$(ph .c SEEN)" -gt 0 ] && echo yes || echo no)"
eq "it never reached the gate" "DELTA_SYNC" "$(ph .c PHASE)"
fault '{}'
STATE_DIR=.c "${RB[@]}" resume >c2.txt 2>&1; RC=$?
eq "resume finishes the job" "0" "$RC"
eq "counts converge after resume" "$(cnt bench-es9)" "$(cnt bench-es6)"
eq "id sets converge after resume" "$(ids bench-es9)" "$(ids bench-es6)"
eq "verify passed" "yes" "$(grep -q 'VERIFY PASSED' c2.txt && echo yes || echo no)"

echo
echo "== a truncated id export never reaches the delete step =="
# The ES6 scroll dies partway through phase 3. A short export understates
# ES6's id set, so the run must stop instead of diffing what it has.
fresh; fault '{"scroll_die_after":2}'
go .s run >s.txt 2>&1; RC=$?
eq "run aborts in reconcile" "1" "$RC"
eq "it explains the scroll loss" "yes" "$(grep -q 'scroll context lost' s.txt && echo yes || echo no)"
eq "no deletes happened" "" "$(ph .s DELETED)"

echo
echo "== blast-radius guard on deletes =="
fresh
for i in 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19; do
  printf '{"delete":{"_id":"doc-%s"}}\n' "$i" \
    | curl -s -u e:e -XPOST "$BASE/bench-es9/_doc/_bulk" \
        -H 'Content-Type: application/x-ndjson' --data-binary @- >/dev/null
done
go .b run >b.txt 2>&1; RC=$?
eq "run refuses the mass delete" "1" "$RC"
eq "it quotes the ratio" "yes" "$(grep -q 'more than 0.10 of ES6' b.txt && echo yes || echo no)"
eq "nothing was deleted" "" "$(ph .b DELETED)"
eq "candidates written out for review" "yes" "$([ -s .b/to_delete ] && echo yes || echo no)"
eq "ASSUME_YES is required to proceed" "19" \
   "$(ASSUME_YES=true STATE_DIR=.b "${RB[@]}" resume >b2.txt 2>&1; ph .b DELETED)"

echo
echo "== concurrent runs are refused =="
rm -rf .l; mkdir -p .l/lock; echo "$$" >.l/lock/pid
STATE_DIR=.l "${RB[@]}" verify >l.txt 2>&1; RC=$?
eq "second process refuses to start" "1" "$RC"
eq "it names the holder" "yes" "$(grep -q 'another es_rollback is running' l.txt && echo yes || echo no)"

echo
printf 'passed %d, failed %d\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
