#!/usr/bin/env bash
#
# ID-diff reconciliation: find documents deleted on ES9 since cutover and
# delete them from ES6 too.
#
# The updated_at delta sync (rollback_sync.sh + the Logstash pipeline) only
# catches creates/updates -- a hard delete on ES9 leaves no trace for a
# delta-by-updated_at query to find. This script closes that gap without any
# mapping or application change: export every live _id from both indices,
# diff the two sorted lists, and bulk-delete from ES6 whatever no longer
# exists on ES9. Same technique Logstash's own docs recommend for jdbc
# inputs that can't see deletes either -- see docs/MAPPING-DIFFERENCES.md and
# docs/superpowers/specs/2026-07-21-es9-es6-rollback-design.md.
#
# One-shot: run once per rollback, after the create/update delta sync
# (rollback_sync.sh) has finished draining.
#
# Runs from the operator's own machine (not a VM), so this uses `python`,
# not `python3` -- on Windows/Git Bash there is usually no `python3` on
# PATH. If your `python` is Python 2, adjust the print() calls accordingly.
#
# Env vars:
#   ES6_URL / ES9_URL   base URLs               (default http://localhost:9200 both)
#   SRC_INDEX           ES9 index               (default bench-es9)
#   DST_INDEX           ES6 index               (default bench-es6)
#   PAGE_SIZE           search_after page size  (default 5000)
#   ES6_USER/ES6_PW     auth for ES6            (default elastic / $ELASTIC_PW)
#   ES9_USER/ES9_PW     auth for ES9            (default elastic / $ELASTIC_PW)
#
set -euo pipefail

ES6_URL="${ES6_URL:-http://localhost:9200}"
ES9_URL="${ES9_URL:-http://localhost:9200}"
SRC_INDEX="${SRC_INDEX:-bench-es9}"
DST_INDEX="${DST_INDEX:-bench-es6}"
PAGE_SIZE="${PAGE_SIZE:-5000}"
ES6_USER="${ES6_USER:-elastic}"
ES6_PW="${ES6_PW:-${ELASTIC_PW:-}}"
ES9_USER="${ES9_USER:-elastic}"
ES9_PW="${ES9_PW:-${ELASTIC_PW:-}}"

c6() { curl -fsS -u "$ES6_USER:$ES6_PW" "$@"; }
c9() { curl -fsS -u "$ES9_USER:$ES9_PW" "$@"; }

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# Streams every live _id out of $3 on $2 (via curl helper $1), sorted, to $4.
# Pages with search_after on _doc (index order) so it scales past what a
# single request's window would allow, without ever holding the whole result
# set in memory. Sorting on _id itself is not an option -- Elasticsearch
# disallows fielddata access on _id by default and returns 400
# illegal_argument_exception ("Fielddata access on the _id field is
# disallowed") for any attempt to sort/aggregate on it. _doc is the
# documented fast-path sort for search_after when you just need to walk
# every document once, which is exactly this case -- order doesn't matter
# since the output gets sorted separately below for the comm diff.
export_ids() {
  local curl_fn="$1" url="$2" index="$3" out="$4"
  local search_after="" body resp hits
  : >"$out"
  while :; do
    if [ -z "$search_after" ]; then
      body='{"size":'"$PAGE_SIZE"',"sort":["_doc"],"_source":false,"query":{"match_all":{}}}'
    else
      body='{"size":'"$PAGE_SIZE"',"sort":["_doc"],"_source":false,"search_after":['"$search_after"'],"query":{"match_all":{}}}'
    fi
    resp="$($curl_fn -XPOST "$url/$index/_search" -H 'Content-Type: application/json' --data-binary "$body")"
    hits="$(python -c "import sys,json;print(len(json.loads(sys.argv[1])['hits']['hits']))" "$resp")"
    [ "$hits" -eq 0 ] && break
    python -c "
import sys, json
d = json.loads(sys.argv[1])
for h in d['hits']['hits']:
    print(h['_id'])
" "$resp" >>"$out"
    search_after="$(python -c "
import sys, json
d = json.loads(sys.argv[1])
print(json.dumps(d['hits']['hits'][-1]['sort'][0]))
" "$resp")"
  done
  sort -o "$out" "$out"
}

echo ">> exporting live IDs from ES9/$SRC_INDEX"
export_ids c9 "$ES9_URL" "$SRC_INDEX" "$TMPDIR/es9_ids.sorted"
echo "   $(wc -l <"$TMPDIR/es9_ids.sorted") ids"

echo ">> exporting live IDs from ES6/$DST_INDEX"
export_ids c6 "$ES6_URL" "$DST_INDEX" "$TMPDIR/es6_ids.sorted"
echo "   $(wc -l <"$TMPDIR/es6_ids.sorted") ids"

comm -23 "$TMPDIR/es6_ids.sorted" "$TMPDIR/es9_ids.sorted" >"$TMPDIR/deleted_ids"
DELETED_COUNT="$(wc -l <"$TMPDIR/deleted_ids")"
echo ">> $DELETED_COUNT id(s) present on ES6 but no longer on ES9 -- deleting from ES6"

if [ "$DELETED_COUNT" -gt 0 ]; then
  python -c "
import sys
ids = [l.strip() for l in open(sys.argv[1]) if l.strip()]
for i in ids:
    print('{\"delete\":{\"_id\":\"%s\"}}' % i)
" "$TMPDIR/deleted_ids" >"$TMPDIR/bulk_delete.ndjson"
  # /_doc/_bulk, not /_bulk: ES6 still has mapping types (this repo's ES6
  # index uses _doc as its sole type -- see docs/MAPPING-DIFFERENCES.md) and
  # its _bulk API rejects delete actions with no type ("type is missing").
  # ES9 has no such requirement, but DST_INDEX here is always the ES6 side.
  RESP="$(c6 -XPOST "$ES6_URL/$DST_INDEX/_doc/_bulk" -H 'Content-Type: application/x-ndjson' \
    --data-binary "@$TMPDIR/bulk_delete.ndjson")"
  echo "$RESP" | python -c "
import sys, json
d = json.load(sys.stdin)
errs = [i['delete'] for i in d['items'] if i['delete'].get('status', 200) >= 300 and i['delete'].get('status') != 404]
print('bulk delete errors:' , errs[:5] if errs else 'none')
"
  c6 -XPOST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null
fi

echo ">> reconciliation done: ES6/$DST_INDEX's live ID set now matches ES9/$SRC_INDEX's"
