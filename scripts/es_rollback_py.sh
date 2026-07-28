#!/usr/bin/env bash
#:USAGE
#
# Blue-green rollback controller: bring ES6 back in line with ES9 after a
# period (e.g. 14 days) in which ES9 served all read/write traffic.
#
# Ordering is the whole point: the create/update delta sync must fully
# complete and pass a hard gate BEFORE any delete reconciliation runs.
# Delete reconciliation works by diffing the two indices' live _id sets, and
# that diff is only meaningful once ES6 has received every create and update.
# An interrupted delta sync leaves ES6 missing documents, and the diff would
# read those exact documents as "deleted on ES9" -- turning a failed sync
# into data loss. Hence the phases, and hence the gate.
#
#   0 PREFLIGHT   connectivity, cluster health, indices exist, ES6 writable
#                 and the credentials allowed to write it, cutover marker
#   1 DELTA_SYNC  ES9 (TS_FIELD > cutover) -> ES6, resumable, journaled
#   2 DELTA_GATE  cursor exhausted + no dead letters; blocks phase 3 otherwise
#   3 RECONCILE   live _id set diff, both directions: delete ES6-only,
#                 repair ES9-only
#   4 VERIFY      counts, expected id set, random _source sample
#
# TS_FIELD=all turns phase 1 into a full copy
#
# Assumptions:
#   - ES9 takes no writes for the duration. NOT verified. The rollback runs
#     inside a planned downtime window, so stopping the writers belongs to
#     the runbook. An earlier version sampled the index twice to prove it,
#     which cost FREEZE_WAIT seconds per index and raised a false alarm
#     whenever a shard relocated between the two samples. Every phase below
#     is wrong if this assumption is false.
#   - Every write on ES9 bumped TS_FIELD. The phase 3 reverse diff is
#     the safety net if that ever failed for a create. TS_FIELD=all does not
#     need this assumption at all.
#
# Undo: every document is read from ES6 and journaled BEFORE it is
# overwritten or deleted, so `undo` restores ES6 exactly. No snapshots.
#
# Dependencies: curl, jq, python3, awk, sort, comm, gzip, split.
# NOTE: jq is not part of a stock Ubuntu image -- `apt-get install -y jq`.
#
# Usage:
#   ./es_rollback_py.sh preflight   checks only, writes nothing
#   ./es_rollback_py.sh run         start a fresh run
#   ./es_rollback_py.sh resume      continue an interrupted run
#   ./es_rollback_py.sh status      show phase and counters
#   ./es_rollback_py.sh verify      re-run phase 4 on its own
#   ./es_rollback_py.sh undo        restore ES6 from the journal
#   ./es_rollback_py.sh reset       drop state (keeps the journal)
#
# Env vars, grouped by how often you have any business touching them.
#
# CONNECTION -- set these on every run:
#   ES6_URL / ES9_URL     base URLs               (default http://localhost:9200)
#   SRC_INDEX             ES9 index or alias, the source   (default bench-es9)
#   DST_INDEX             ES6 index or alias, the target   (default bench-es6)
#   TS_FIELD              field the delta window ranges over, e.g.
#                         updated_at or system_update_at   (default updated_at)
#                         "all" = no window, copy every document
#   ES6_USER / ES6_PW     auth for ES6            (default elastic / $ELASTIC_PW)
#   ES9_USER / ES9_PW     auth for ES9            (default elastic / $ELASTIC_PW)
#   STATE_DIR             state + journal dir     (default ./.rollback-state)
#
# PERFORMANCE -- only when a run is too slow or runs out of memory:
#   PAGE_SIZE             search page size        (default 10000, ES cap)
#   MGET_BATCH            ids per pre-image _mget, and per delete/repair
#                         batch                   (default 1000)
#   SLICES                parallel slices for the id walk: "auto" = one per
#                         shard (default), "1" disables, or an explicit count
#   MAX_RETRY             HTTP retry attempts     (default 6)
#   PROGRESS_EVERY        pages between id-walk progress lines (default 50,
#                         0 silences them)
#
# SAFETY -- read the phase they belong to before changing any of these:
#   MAX_DELETE_RATIO      refuse deletes above this share of ES6 (default 0.10)
#   SAMPLE_N              docs compared in verify (default 1000)
#   SINCE                 override cutover_at     (ISO-8601, optional;
#                         ignored when TS_FIELD=all)
#   ALLOW_PARTIAL         "true" lets the gate pass with dead letters
#   ASSUME_YES            "true" skips the delete-ratio confirmation
#
# This script handles ONE index. For several, drive it from the outside:
# es_rollback_all.sh loops over an index -> TS_FIELD map, and the Jenkins
# pipeline runs one stage per index. Both call this script unchanged.
#
# Exit codes: 0 ok | 1 fatal | 2 finished with dead letters | 130 interrupted
#
#:END-USAGE
set -euo pipefail

# ------------------------------------------------------------ config: 1/3 --
# CONNECTION
ES6_URL="${ES6_URL:-http://localhost:9200}"
ES9_URL="${ES9_URL:-http://localhost:9200}"
SRC_INDEX="${SRC_INDEX:-bench-es9}"
DST_INDEX="${DST_INDEX:-bench-es6}"
# The field a write bumps, and therefore the one the delta window ranges
# over. It differs per index (updated_at, system_update_at, ...), so the
# caller passes it; there is no safe default beyond the common case.
#
# The literal "all" means the index has no such field to trust: phase 1 then
# copies every live document instead of a window. Matched case-insensitively
# so ALL and All behave the same -- a mode this expensive should never hinge
# on the shift key.
TS_FIELD="${TS_FIELD:-updated_at}"
case "$(printf '%s' "$TS_FIELD" | tr '[:upper:]' '[:lower:]')" in
  all) ALL_MODE=true; TS_FIELD=all ;;
  *)   ALL_MODE=false ;;
esac
ES6_USER="${ES6_USER:-elastic}"
ES6_PW="${ES6_PW:-${ELASTIC_PW:-}}"
ES9_USER="${ES9_USER:-elastic}"
ES9_PW="${ES9_PW:-${ELASTIC_PW:-}}"
STATE_DIR="${STATE_DIR:-./.rollback-state}"

# ------------------------------------------------------------ config: 2/3 --
# PERFORMANCE. Defaults assume ~1 KB documents on a disk-bound node.
#
# 10000 is the ceiling: index.max_result_window caps `size`, and
# search_after does not lift it.
PAGE_SIZE="${PAGE_SIZE:-10000}"
# Deliberately independent of PAGE_SIZE -- see journal_preimage.
MGET_BATCH="${MGET_BATCH:-1000}"
# auto = one slice per shard (what slices=auto does on _reindex); 1 disables
SLICES="${SLICES:-auto}"
MAX_RETRY="${MAX_RETRY:-6}"
# The id walk is the longest stretch of a run and prints nothing on its own;
# without a heartbeat a healthy export is indistinguishable from a hang.
PROGRESS_EVERY="${PROGRESS_EVERY:-50}"

# ------------------------------------------------------------ config: 3/3 --
# SAFETY. The last three disable a guard -- read the phase that uses one first.
MAX_DELETE_RATIO="${MAX_DELETE_RATIO:-0.10}"
SAMPLE_N="${SAMPLE_N:-1000}"
SINCE="${SINCE:-}"
ALLOW_PARTIAL="${ALLOW_PARTIAL:-false}"
ASSUME_YES="${ASSUME_YES:-false}"

# --------------------------------------------------------------- constants --
# 5 MB per _bulk is Elastic's own guidance; not worth a config knob.
BULK_BYTE_CAP=5000000

# comm(1) compares with the same collation sort(1) ordered by. Under a UTF-8
# locale that collation ignores punctuation, so two distinct ids can compare
# equal and comm pairs them wrongly -- here that means deleting the wrong
# documents from ES6. C is a strict bytewise total order, and faster.
export LC_ALL=C

mkdir -p "$STATE_DIR"
STATE_DIR="$(cd "$STATE_DIR" && pwd)"

# ------------------------------------------------------------------- files --
#
# $STATE_DIR is what a resume or undo depends on; $WORK is scratch any run may
# delete. Inventory and purpose of every file: docs/ES-ROLLBACK.md section 12.
#
# Scratch is "<owner>.<purpose>.<ext>", so a glob matches one owner's files
# only, and split(1) output goes in $PARTS so a batch glob can never match a
# named file. A file is used instead of a pipe for exactly two reasons: it is a
# curl request body (http_retry re-sends the same file after a 429/503, and a
# pipe cannot be re-read), or it is a cursor that must survive a crash.
WORK="$STATE_DIR/work"; mkdir -p "$WORK"
PARTS="$WORK/parts"; mkdir -p "$PARTS"

# Durable, and named for the docs that reference them -- do not rename.
STATE="$STATE_DIR/state.env"
JOURNAL="$STATE_DIR/journal.tsv.gz"
DEADLETTER="$STATE_DIR/deadletter.ndjson"
LOG="$STATE_DIR/run.log"
LOCK="$STATE_DIR/lock"
PIT_FILE="$STATE_DIR/pit_id.txt"
CURSOR_FILE="$STATE_DIR/search_after.json"

RESP="$WORK/http.resp.json"

INTERRUPTED=0

log()  { printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*" | tee -a "$LOG"; }
warn() { printf '%s WARN %s\n' "$(date -u +%H:%M:%S)" "$*" | tee -a "$LOG" >&2; }
die()  { printf '%s FATAL %s\n' "$(date -u +%H:%M:%S)" "$*" | tee -a "$LOG" >&2; exit 1; }

# ------------------------------------------------------------------- state --
#
# Flat key=value, sourceable by bash; anything not shell-safe (search_after
# arrays, PIT ids) gets its own file. Written temp+mv so a crash can never
# leave a half-written state file behind.

state_load() { [ -f "$STATE" ] && . "$STATE" || true; }

state_set() {
  local key="$1" val="$2" tmp="$STATE.tmp"
  touch "$STATE"
  grep -v "^${key}=" "$STATE" >"$tmp" 2>/dev/null || true
  printf '%s=%s\n' "$key" "$val" >>"$tmp"
  mv -f "$tmp" "$STATE"
  eval "$key=\$val"
}

acquire_lock() {
  if ! mkdir "$LOCK" 2>/dev/null; then
    local pid; pid="$(cat "$LOCK/pid" 2>/dev/null || echo "")"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      die "another es_rollback is running (pid $pid)"
    fi
    warn "stale lock from pid ${pid:-unknown}, reclaiming"
    rm -rf "$LOCK"; mkdir "$LOCK"
  fi
  echo "$$" >"$LOCK/pid"
  trap 'rm -rf "$LOCK"' EXIT
}

# -------------------------------------------------------------------- http --

backoff() { awk -v n="$1" 'BEGIN{srand();s=(2^n)*(0.5+rand()/2);if(s>60)s=60;print s}'; }

# http_retry <user> <pw> <method> <url> [content-type] [request-body-file]
#
# Status on stdout, body in $RESP. Deliberately not curl -f: a _bulk that
# returns 200 with per-item errors still has to be read, and a 4xx body
# carries the reason worth showing.
http_retry() {
  local user="$1" pw="$2" method="$3" url="$4" ctype="${5:-}" body="${6:-}"
  local args=(-sS -u "$user:$pw" -X "$method" "$url" -o "$RESP"
              -w '%{http_code}' --connect-timeout 10 --max-time 600)
  [ -n "$ctype" ] && args+=(-H "Content-Type: $ctype")
  [ -n "$body" ] && args+=(--data-binary "@$body")

  local attempt=0 code
  while :; do
    code="$(curl "${args[@]}" 2>>"$LOG" || echo "000")"
    case "$code" in
      2*) printf '%s' "$code"; return 0 ;;
      429|502|503|504|000)
        [ "$INTERRUPTED" -eq 1 ] && { printf '%s' "$code"; return 1; }
        attempt=$((attempt + 1))
        if [ "$attempt" -ge "$MAX_RETRY" ]; then printf '%s' "$code"; return 1; fi
        warn "HTTP $code on $url -- retry $attempt/$MAX_RETRY"
        sleep "$(backoff "$attempt")" ;;
      *) printf '%s' "$code"; return 1 ;;
    esac
  done
}

es6() { http_retry "$ES6_USER" "$ES6_PW" "$@"; }
es9() { http_retry "$ES9_USER" "$ES9_PW" "$@"; }

# ------------------------------------------------------------- json shaping --

# Body for one delta page. Built by jq so PIT ids and search_after arrays are
# never string-interpolated into shell-quoted JSON. `op` is gt or gte -- see
# phase_delta for why that switches.
#
# In ALL_MODE there is no range and no timestamp to sort on, so the sort is
# _shard_doc alone. That tiebreaker is only defined inside a PIT, which is
# exactly where it is used -- and it is the cheapest total order ES offers,
# since a full copy pages through the entire index.
delta_page_body() {
  local pit="$1" since="$2" out="$3" cursor_src="$4" op="${5:-gt}"
  local cursor="null"
  [ -s "$cursor_src" ] && cursor="$(cat "$cursor_src")"
  jq -n --arg pit "$pit" --arg since "$since" --arg op "$op" --arg tsf "$TS_FIELD" \
        --argjson allmode "$ALL_MODE" \
        --argjson size "$PAGE_SIZE" --argjson sa "$cursor" '
      (if $allmode then { query: {match_all: {}}, sort: [{_shard_doc: "asc"}] }
       else { query: {range: {($tsf): {($op): $since}}},
              sort: [{($tsf): "asc"}, {_shard_doc: "asc"}] } end)
    + { size: $size }
    + (if $pit == "" then {} else { pit: {id: $pit, keep_alive: "15m"} } end)
    + (if $sa == null then { track_total_hits: true } else { search_after: $sa } end)
  ' >"$out"
}

# One ES9 delta page -> id list, bulk chunks capped at BULK_BYTE_CAP, and a
# staged next cursor. Prints "<hits> <last_timestamp>".
#
# ALL_MODE passes an empty field name: there is no watermark to record, and a
# source field that happens to be called "all" would otherwise be read as one.
split_delta_page() {
  local resp="$1" tsf="$TS_FIELD"
  [ "$ALL_MODE" = true ] && tsf=""
  rm -f "$WORK"/delta.chunk.*.ndjson
  python3 - "$resp" "$WORK" "$BULK_BYTE_CAP" "$tsf" <<'PY'
import json, sys
resp, work, cap, tsf = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
J = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)
hits = json.load(open(resp, encoding='utf-8'))['hits']['hits']
with open(work + '/delta.page.ids', 'w', encoding='utf-8') as f:
    f.write(''.join(h['_id'] + '\n' for h in hits))
with open(work + '/delta.cursor.next.json', 'w', encoding='utf-8') as f:
    if hits and hits[-1].get('sort') is not None: f.write(J(hits[-1]['sort']) + '\n')
i = sz = 0; out = None
for h in hits:
    meta = {'_id': h['_id']}
    if h.get('_routing'): meta['routing'] = h['_routing']
    a, b = J({'index': meta}), J(h.get('_source', {}))
    n = len(a.encode()) + len(b.encode()) + 2
    if out is None or (sz > 0 and sz + n > cap):
        if out: out.close(); i += 1
        out = open('%s/delta.chunk.%04d.ndjson' % (work, i), 'w', encoding='utf-8'); sz = 0
    out.write(a + '\n' + b + '\n'); sz += n
if out: out.close()
print(len(hits), (hits[-1]['_source'].get(tsf, '') if hits and tsf else ''))
PY
}

# Classify a _bulk response. ES answers 200 even when individual items
# failed, so discarding the body silently drops documents while reporting
# success. Splits into a retry set and a dead letter file; prints
# "<ok> <retry> <fatal> <exhausted>".
parse_bulk() {
  local resp="$1" sent="$2" retry_out="$3" dl="$4" final="${5:-0}" tag="${6:-bulk}"
  python3 - "$resp" "$sent" "$retry_out" "$dl" "$final" "$tag" <<'PY'
import json, sys
resp, sent, retry_out, dl, final, tag = sys.argv[1:7]
final = final == '1'
RETRY_ST = {429, 502, 503, 504}
RETRY_ET = ('es_rejected_execution', 'circuit_breaking', 'cluster_block', 'unavailable_shards')
# Bulk item n -> its action line and, for index ops, its source line.
pairs = []
with open(sent, encoding='utf-8') as f:
    for line in f:
        a = line.rstrip('\n')
        if not a: continue
        if a.lstrip().startswith('{"delete"'): pairs.append((a, None))
        else: pairs.append((a, next(f, '').rstrip('\n') or None))
ok = retry = fatal = exhausted = 0
with open(retry_out, 'w', encoding='utf-8') as rf, open(dl, 'a', encoding='utf-8') as df:
    for i, item in enumerate(json.load(open(resp, encoding='utf-8')).get('items', [])):
        op, b = next(iter(item.items()))
        st = b.get('status', 200); err = b.get('error') or {}
        et = err.get('type', '') if isinstance(err, dict) else ''
        act, src = pairs[i] if i < len(pairs) else (None, None)
        if st < 300 or (op == 'delete' and st == 404): ok += 1; continue
        transient = st in RETRY_ST or any(k in et for k in RETRY_ET)
        if transient and not final:
            retry += 1
            rf.write(act + '\n')
            if src: rf.write(src + '\n')
            continue
        if transient: exhausted += 1
        else: fatal += 1
        df.write(json.dumps({'_id': b.get('_id', ''), 'tag': tag, 'status': st, 'error': err,
                             'retry_exhausted': transient,
                             'action': json.loads(act) if act else None,
                             'source': json.loads(src) if src else None},
                            ensure_ascii=False) + '\n')
print(ok, retry, fatal, exhausted)
PY
}

# id file -> {"ids":[...]} for _mget, or a delete bulk body.
id_list_body() {
  local infile="$1" out="$2" kind="$3"
  if [ "$kind" = "mget" ]; then
    jq -R -s -c 'split("\n") | map(rtrimstr("\r")) | map(select(length > 0)) | {ids: .}' \
      "$infile" >"$out"
  else
    jq -R -c 'rtrimstr("\r") | select(length > 0) | {delete: {_id: .}}' "$infile" >"$out"
  fi
}

# --------------------------------------------------------------------- PIT --

pit_open() {
  es9 POST "$1/$2/_pit?keep_alive=15m" >/dev/null || return 1
  jq -r '.id' "$RESP"
}

pit_close() {
  [ -n "$2" ] || return 0
  jq -n --arg id "$2" '{id: $id}' >"$WORK/pit.close.json"
  es9 DELETE "$1/_pit" application/json "$WORK/pit.close.json" >/dev/null 2>&1 || true
  return 0
}

# ------------------------------------------------------------------ bulk io --
#
# Counts come back in BULK_APPLIED / BULK_DEADLETTERED; stdout already carries
# the HTTP status. bulk.send.ndjson must stay a different path from
# bulk.retry.ndjson -- parse_bulk truncates the retry file before reading what
# was sent.
bulk_send() {
  local file="$1" attempt=0 final=0
  local sent="$file" retry_file="$WORK/bulk.retry.ndjson" tag="${BULK_TAG:-bulk}"
  BULK_APPLIED=0; BULK_DEADLETTERED=0
  while :; do
    local code counts ok retry fatal exhausted
    [ "$attempt" -ge "$((MAX_RETRY - 1))" ] && final=1
    code="$(es6 POST "$ES6_URL/$DST_INDEX/_doc/_bulk" application/x-ndjson "$sent")" || {
      warn "bulk request failed with HTTP $code"
      return 1
    }
    counts="$(parse_bulk "$RESP" "$sent" "$retry_file" "$DEADLETTER" "$final" "$tag")"
    read -r ok retry fatal exhausted <<<"$counts"
    BULK_APPLIED=$((BULK_APPLIED + ok))
    BULK_DEADLETTERED=$((BULK_DEADLETTERED + fatal + exhausted))
    [ "$exhausted" -gt 0 ] && warn "$exhausted item(s) still rejected after $MAX_RETRY attempts -- dead-lettered"
    [ "$retry" -eq 0 ] && return 0
    attempt=$((attempt + 1))
    warn "$retry item(s) rejected (transient) -- retry $attempt/$MAX_RETRY"
    sleep "$(backoff "$attempt")"
    sent="$WORK/bulk.send.ndjson"
    mv "$retry_file" "$sent"
  done
}

deadletter_summary() {
  [ -s "$DEADLETTER" ] || return 0
  log "   $(wc -l <"$DEADLETTER" | tr -d ' ') dead-lettered doc(s) in $DEADLETTER -- top reasons:"
  python3 - "$DEADLETTER" >"$WORK/deadletter.summary" 2>/dev/null <<'PY' || return 0
import json, sys, collections
n, why = collections.Counter(), {}
for line in open(sys.argv[1], encoding='utf-8'):
    try: r = json.loads(line)
    except ValueError: continue
    e = r.get('error') if isinstance(r.get('error'), dict) else {}
    k = (r.get('tag') or '?', r.get('status') or '?', e.get('type') or '-')
    n[k] += 1
    why.setdefault(k, ' '.join((e.get('reason') or '').split())[:120])
for k, c in n.most_common(5):
    print('     %d x %s HTTP %s %s: %s' % (c, k[0], k[1], k[2], why[k]))
PY
  while IFS= read -r line; do log "$line"; done <"$WORK/deadletter.summary"
}

# Read the ES6 pre-image of every id in a file into the journal, before the
# caller overwrites or deletes them.
#
# _mget is realtime -- it reads the translog -- so it returns the current
# value even with refresh_interval unset. A search-based read could miss a
# recent write and journal a stale pre-image.
journal_preimage() {
  local idfile="$1" op="${2:-delta}" part seq n
  [ -s "$idfile" ] || return 0
  # Batched by MGET_BATCH, not PAGE_SIZE: a _mget returns the full _source of
  # every id asked for, so one request per page would hand jq a 110 MB response
  # at PAGE_SIZE=100000. BULK_BYTE_CAP does this for the write path.
  #
  # JOURNAL_SEQ is committed after every batch, so a crash midway can never
  # hand the same seq to two different pre-images.
  rm -f "$PARTS"/preimage.*
  split -l "$MGET_BATCH" -a 5 "$idfile" "$PARTS/preimage."
  for part in "$PARTS"/preimage.*; do
    [ -s "$part" ] || continue
    id_list_body "$part" "$WORK/journal.mget.json" mget
    es6 POST "$ES6_URL/$DST_INDEX/_doc/_mget" application/json "$WORK/journal.mget.json" >/dev/null \
      || { warn "pre-image _mget failed -- refusing to write without a journal"; return 1; }
    state_load
    seq="${JOURNAL_SEQ:-0}"
    # Row layout "seq \t id \t op \t found \t source". Absent documents
    # (created on ES9 during the window) get found=0; undoing one means
    # deleting it, not restoring it.
    jq -r --argjson seq "$seq" --arg op "$op" '
      .docs | to_entries[]
      | "\($seq + .key + 1)\t\(.value._id)\t\($op)\t\(if .value.found then 1 else 0 end)\t\(if .value.found then (.value._source|tojson) else "{}" end)"
    ' "$RESP" | gzip -1 >>"$JOURNAL"
    n="$(wc -l <"$part" | tr -d ' ')"
    state_set JOURNAL_SEQ "$((seq + n))"
  done
  rm -f "$PARTS"/preimage.*
  return 0
}

# ------------------------------------------------------- alias resolution --
resolve_one() {
  local fn="$1" url="$2" name="$3" label="$4" backing n
  RESOLVED=""
  if ! "$fn" GET "$url/_alias/$name" >/dev/null 2>&1; then
    RESOLVED="$name"; log "   $label: $name is a concrete index"; return 0
  fi
  backing="$(jq -r --arg a "$name" \
    'to_entries | map(select(.value.aliases | has($a))) | map(.key) | .[]' "$RESP")"
  if [ -z "$backing" ]; then
    RESOLVED="$name"; log "   $label: $name is a concrete index"; return 0
  fi
  n="$(printf '%s\n' "$backing" | wc -l | tr -d ' ')"
  [ "$n" -eq 1 ] || die "alias $name spans $n indices ($(printf '%s' "$backing" | tr '\n' ' ')).
Point it at exactly one index, or pass that index name directly."
  RESOLVED="$backing"
  log "   $label: alias $name -> $RESOLVED"
  return 0
}

resolve_aliases() {
  for bin in curl jq python3 awk sort comm gzip split; do
    command -v "$bin" >/dev/null 2>&1 || die "missing required tool: $bin"
  done
  [ -n "$ES6_PW" ] || die "set ELASTIC_PW (or ES6_PW)"
  [ -n "$ES9_PW" ] || die "set ELASTIC_PW (or ES9_PW)"
  es9 GET "$ES9_URL/" >/dev/null || die "cannot reach/authenticate ES9 at $ES9_URL"
  es6 GET "$ES6_URL/" >/dev/null || die "cannot reach/authenticate ES6 at $ES6_URL"

  resolve_one es9 "$ES9_URL" "$SRC_INDEX" ES9; SRC_INDEX="$RESOLVED"
  resolve_one es6 "$ES6_URL" "$DST_INDEX" ES6; DST_INDEX="$RESOLVED"
}

# --------------------------------------------------------- preflight checks --
check_health() {
  local fn="$1" url="$2" index="$3" label="$4" status unassigned
  "$fn" GET "$url/_cluster/health/$index" >/dev/null \
    || die "$label: cannot read cluster health for $index"
  status="$(jq -r '.status // "unknown"' "$RESP")"
  unassigned="$(jq -r '.unassigned_shards // 0' "$RESP")"

  if [ "$status" = "red" ]; then
    die "$label: $index is RED -- $unassigned shard(s) unassigned.
Neither side can be read or written completely in this state, and a short id
export turns into wrong deletes in phase 3. Start here:
  curl -u $ES6_USER:\$ELASTIC_PW '$url/_cluster/allocation/explain?pretty'"
  fi
  log "   $label: $index health=$status unassigned=$unassigned"
  # Yellow is the normal state for a single-node ES6 with replicas configured,
  # so it is worth saying out loud but never worth stopping for.
  [ "$status" = "yellow" ] && warn "$label: $index is yellow -- missing replicas only, the rollback can still run"
  return 0
}

# ------------------------------------------------------------------ phase 0 --

phase_preflight() {
  log "== phase 0: preflight (delta field: $TS_FIELD) =="

  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "ES9 index $SRC_INDEX not found"
  es6 GET "$ES6_URL/$DST_INDEX/_count" >/dev/null || die "ES6 index $DST_INDEX not found"
  log "   both indices present"

  check_health es9 "$ES9_URL" "$SRC_INDEX" ES9
  check_health es6 "$ES6_URL" "$DST_INDEX" ES6

  # Two weeks idle is long enough for ES6 to have hit the flood-stage disk
  # watermark and blocked itself. Every write below would fail one at a
  # time; better to say it now, with the fix.
  es6 GET "$ES6_URL/$DST_INDEX/_settings" >/dev/null || die "cannot read $DST_INDEX settings"
  local blocked
  blocked="$(jq -r '.[].settings.index.blocks // {}
                    | to_entries | map(select(.value == true or .value == "true"))
                    | map(.key) | join(",")' "$RESP")"
  if [ -n "$blocked" ]; then
    die "$DST_INDEX is write-blocked ($blocked). Free disk, then:
  curl -u $ES6_USER:\$ELASTIC_PW -XPUT '$ES6_URL/$DST_INDEX/_settings' \\
    -H 'Content-Type: application/json' \\
    -d '{\"index.blocks.read_only_allow_delete\":null,\"index.blocks.read_only\":null,\"index.blocks.write\":null}'"
  fi
  log "   $DST_INDEX is writable"

  local cutover="" effective=""
  if [ "$ALL_MODE" = true ]; then
    log "   TS_FIELD=all -- no delta window, phase 1 copies every document"
    [ -n "$SINCE" ] && warn "SINCE=$SINCE ignored: TS_FIELD=all has no time window"
  else
    if [ -n "$SINCE" ]; then
      cutover="$SINCE"; log "   using SINCE override: $cutover"
    else
      es9 GET "$ES9_URL/$SRC_INDEX/_mapping" >/dev/null || die "cannot read $SRC_INDEX mapping"
      cutover="$(jq -r '.[].mappings._meta.cutover_at // ""' "$RESP")"
      [ -n "$cutover" ] || die "_meta.cutover_at missing on $SRC_INDEX -- pass SINCE=<ISO-8601>, or TS_FIELD=all to copy everything"
      log "   cutover_at=$cutover"
    fi
    effective="$(jq -rn --arg t "$cutover" '
        ($t | fromdateiso8601) as $e
        | if $e > now then error("future") else ($e | todateiso8601) end
      ' 2>/dev/null)" \
      || die "cutover_at is unusable (not ISO-8601, or in the future): $cutover"
    log "   lower bound: $effective"
  fi

  # Outputs of this phase, read by cmd_run.
  PREFLIGHT_CUTOVER_AT="$cutover"
  PREFLIGHT_SINCE="$effective"
}

# ------------------------------------------------------------ refresh state --
#
# refresh_interval is deliberately NOT touched. The explicit _refresh calls in
# phases 1, 3 and 4 already make phase 1's writes visible to the id export; a
# periodic refresh would only add a segment per interval for the whole of phase
# 1, feeding the merge queue on the disk that is already the bottleneck.
# Pre-image reads are unaffected: _mget is realtime and reads the translog.

# ------------------------------------------------------------------ phase 1 --

phase_delta() {
  if [ "$ALL_MODE" = true ]; then
    log "== phase 1: full copy $SRC_INDEX -> $DST_INDEX (TS_FIELD=all) =="
  else
    log "== phase 1: delta sync $SRC_INDEX -> $DST_INDEX on $TS_FIELD =="
  fi
  state_load
  local since="${EFFECTIVE_SINCE:-}" pit="" BULK_TAG=delta
  local synced="${SYNCED:-0}" seen="${SEEN:-0}" deadletters="${DL_COUNT:-0}"
  # `gt` on the first pass; a restart after a PIT expiry switches to `gte` so
  # the whole group sharing the watermark timestamp is re-scanned. With `gt`,
  # any document in that group not yet processed would be skipped for good --
  # a page boundary can fall in the middle of such a group.
  local range_op="gt" restarts=0

  [ -f "$PIT_FILE" ] && pit="$(cat "$PIT_FILE")"
  if [ -z "$pit" ]; then
    pit="$(pit_open "$ES9_URL" "$SRC_INDEX")" || die "cannot open a PIT on ES9"
    printf '%s' "$pit" >"$PIT_FILE"
    log "   opened PIT"
  fi

  while :; do
    if [ "$INTERRUPTED" -eq 1 ]; then
      log "   interrupted -- checkpointed at seen=$seen"
      state_set SYNCED "$synced"; state_set SEEN "$seen"; state_set DL_COUNT "$deadletters"
      exit 130
    fi

    delta_page_body "$pit" "$since" "$WORK/delta.request.json" "$CURSOR_FILE" "$range_op"
    if ! es9 POST "$ES9_URL/_search" application/json "$WORK/delta.request.json" >/dev/null; then
      # An expired PIT (or a node restart) shows up as search_context_missing.
      # ES9 is frozen, so reopening and restarting from the last committed
      # watermark is exactly right: the overlap rewrites identical content.
      if grep -q 'search_context_missing\|No search context found' "$RESP" 2>/dev/null; then
        restarts=$((restarts + 1))
        [ "$restarts" -gt 10 ] && die "PIT expired $restarts times without finishing; raise keep_alive or reduce PAGE_SIZE"
        pit="$(pit_open "$ES9_URL" "$SRC_INDEX")" || die "cannot reopen PIT"
        printf '%s' "$pit" >"$PIT_FILE"
        if [ "$ALL_MODE" = true ]; then
          # _shard_doc is only meaningful inside the PIT that issued it, and
          # with no watermark there is nothing to resume from -- the walk
          # starts over. That is safe, not wasteful-only: every write is a
          # whole-document overwrite of a frozen source, so redoing a page
          # changes nothing. `seen` restarts with it, or the phase 2 gate
          # would weigh a two-pass total against a one-pass TOTAL_HITS and
          # pass a walk that never actually finished.
          warn "PIT expired -- reopening and restarting the full copy from the beginning"
          seen=0; state_set SEEN 0
        else
          warn "PIT expired -- reopening, resuming from watermark ${WATERMARK:-$since} (inclusive)"
          state_load; since="${WATERMARK:-$since}"; range_op="gte"
        fi
        : >"$CURSOR_FILE"
        continue
      fi
      [ "$INTERRUPTED" -eq 1 ] && {
        state_set SYNCED "$synced"; state_set SEEN "$seen"; state_set DL_COUNT "$deadletters"
        log "   interrupted during delta search -- checkpointed at seen=$seen"
        exit 130
      }
      die "delta search failed: $(head -c 200 "$RESP")"
    fi

    if [ "$seen" -eq 0 ] && [ ! -s "$CURSOR_FILE" ]; then
      state_set TOTAL_HITS "$(jq -r '.hits.total.value // .hits.total' "$RESP")"
      if [ "$ALL_MODE" = true ]; then
        log "   full copy covers $TOTAL_HITS doc(s)"
      else
        log "   delta window contains $TOTAL_HITS doc(s)"
      fi
    fi

    local page_summary hits last_ts
    page_summary="$(split_delta_page "$RESP")"
    hits="${page_summary%% *}"; last_ts="${page_summary#* }"
    [ "$hits" -eq 0 ] && break

    journal_preimage "$WORK/delta.page.ids" delta \
      || die "cannot journal pre-images -- aborting before any write"

    local chunk
    for chunk in "$WORK"/delta.chunk.*.ndjson; do
      [ -s "$chunk" ] || continue
      bulk_send "$chunk" || {
        state_set SYNCED "$synced"; state_set SEEN "$seen"; state_set DL_COUNT "$deadletters"
        die "bulk write failed -- state checkpointed, run 'resume' once ES6 is healthy"
      }
      synced=$((synced + BULK_APPLIED)); deadletters=$((deadletters + BULK_DEADLETTERED))
    done

    seen=$((seen + hits))
    [ -n "$last_ts" ] && state_set WATERMARK "$last_ts"
    state_set SYNCED "$synced"; state_set SEEN "$seen"; state_set DL_COUNT "$deadletters"
    # Cursor is promoted only after the page is committed and counted. A
    # crash here re-reads the page on resume, which is idempotent; promoting
    # it earlier would let a crash skip the page entirely.
    mv -f "$WORK/delta.cursor.next.json" "$CURSOR_FILE"
    log "   page: $hits docs (seen=$seen synced=$synced deadletter=$deadletters)"
  done

  pit_close "$ES9_URL" "$pit"; rm -f "$PIT_FILE" "$CURSOR_FILE"
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || warn "refresh failed"
  log "   delta sync finished: seen=$seen synced=$synced deadletter=$deadletters"
  state_set PHASE DELTA_DONE
}

# ------------------------------------------------------------------ phase 2 --

phase_gate() {
  log "== phase 2: delta gate =="
  state_load
  local total="${TOTAL_HITS:-0}" seen="${SEEN:-0}" deadletters="${DL_COUNT:-0}"

  # seen can exceed total after a PIT expiry forced a watermark restart --
  # that overlap is re-read, not new work. It must never fall short.
  if [ "$seen" -lt "$total" ]; then
    die "gate FAILED: delta window had $total doc(s) but only $seen were read.
Deletes are NOT safe to reconcile -- the id diff would read the missing
documents as deleted on ES9. Run 'resume' first."
  fi
  if [ "$deadletters" -gt 0 ] && [ "$ALLOW_PARTIAL" != "true" ]; then
    deadletter_summary
    die "gate FAILED: $deadletters doc(s) in $DEADLETTER were rejected by ES6.
Fix the cause and resume. ALLOW_PARTIAL=true overrides, but only if you
accept that ES6 will be missing those documents and that the delete
reconciliation may then remove them."
  fi
  [ "$deadletters" -gt 0 ] && warn "gate passed with $deadletters dead-lettered doc(s) (ALLOW_PARTIAL)"
  log "   gate passed: seen=$seen >= total=$total, deadletter=$deadletters"
  state_set PHASE GATE_PASSED
}

# ------------------------------------------------------------------ phase 3 --
#
# Walk every live _id into a file. ES9 uses a PIT; ES6 6.8 has no PIT so it
# uses scroll. Both are consistent snapshots -- plain search_after on _doc is
# not, because _doc ordering shifts as segments merge, which silently skips
# or duplicates ids.

# `slices=auto` exists on _reindex, but search/scroll slicing has no such
# value -- the body must name an explicit {id, max}. All auto does there is
# pick the shard count, so do exactly that.
#
# Going past the shard count is a trap, not a tuning knob: at max <= shards a
# slice is just a set of shards, but beyond that Elasticsearch splits *within*
# a shard using a hash filter over every document -- O(N), plus a bitset per
# slice. More slices than shards can end up slower than none.
SLICE_COUNT=1
resolve_slices() {
  local http_fn="$1" url="$2" index="$3" label="$4" shards
  SLICE_COUNT=1
  [ "$SLICES" != "1" ] || return 0

  "$http_fn" GET "$url/$index/_settings" >/dev/null || {
    warn "$label: cannot read shard count -- running the id walk unsliced"; return 0; }
  shards="$(jq -r '.[].settings.index.number_of_shards // 1' "$RESP")"

  if [ "$SLICES" = "auto" ]; then
    SLICE_COUNT="$shards"
  else
    SLICE_COUNT="$SLICES"
    [ "$SLICE_COUNT" -le "$shards" ] || warn \
      "$label: SLICES=$SLICE_COUNT exceeds $shards shard(s) -- slicing falls back to a per-document filter and may be slower than auto"
  fi
  [ "${SLICE_COUNT:-1}" -ge 1 ] || SLICE_COUNT=1
  log "   $label: $shards shard(s) -> $SLICE_COUNT slice(s) for the id walk"
  return 0
}

# Body for one page of an id walk. A slice_max of 1 omits the slice clause,
# so the unsliced case is the same code path with a single walker.
#
# The cursor is JSON text, not a file: unlike the delta cursor it never has to
# survive a crash, because a failed slice restarts its whole walk.
id_walk_body() {
  local pit="$1" cursor="$2" sid="$3" smax="$4" out="$5"
  jq -n --arg p "$pit" --argjson size "$PAGE_SIZE" \
        --argjson i "$sid" --argjson m "$smax" --argjson sa "${cursor:-null}" '
      { query: {match_all: {}}, sort: [{_shard_doc: "asc"}], _source: false, size: $size }
    + (if $p == "" then {} else { pit: {id: $p, keep_alive: "15m"} } end)
    + (if $m > 1 then { slice: {id: $i, max: $m} } else {} end)
    + (if $sa == null then {} else { search_after: $sa } end)
  ' >"$out"
}

# The only progress signal in the longest phase of a run. Every PROGRESS_EVERY
# pages, one line per walker; PROGRESS_EVERY=0 turns it off.
walk_progress() {
  [ "${PROGRESS_EVERY:-0}" -gt 0 ] || return 0
  [ $(( $2 % PROGRESS_EVERY )) -eq 0 ] || return 0
  log "   $1 id walk: $3 ids so far"
}

# Walk one PIT slice into its own file. Runs inside a subshell that has already
# pointed RESP at a private file, and every file it touches is named after the
# slice -- otherwise concurrent slices overwrite each other.
walk_pit_slice() {
  local pit="$1" sid="$2" smax="$3" out="$4" tag="$5"
  local reqf="$WORK/ids.src.$sid.request" cursor="" n pages=0 ids=0
  : >"$out"
  while :; do
    [ "$INTERRUPTED" -eq 1 ] && return 130
    id_walk_body "$pit" "$cursor" "$sid" "$smax" "$reqf"

    es9 POST "$ES9_URL/_search" application/json "$reqf" >/dev/null || {
      [ "$INTERRUPTED" -eq 1 ] && return 130
      warn "$tag id export failed: $(head -c 200 "$RESP")"
      return 1
    }

    n="$(jq '.hits.hits | length' "$RESP")"
    [ "$n" -eq 0 ] && break

    jq -r '.hits.hits[]._id' "$RESP" >>"$out"
    cursor="$(jq -c '.hits.hits[-1].sort' "$RESP")"

    pages=$((pages + 1)); ids=$((ids + n))
    walk_progress "$tag" "$pages" "$ids"
  done
  return 0
}

# ES6 6.8 has no PIT, so each slice is its own scroll with its own scroll_id.
# One request file serves the whole slice: every body is consumed by its
# request before the next one overwrites it.
walk_scroll_slice() {
  local sid="$1" smax="$2" out="$3" tag="$4"
  local reqf="$WORK/ids.dst.$sid.request" cur n pages=0 ids=0
  : >"$out"
  jq -n --argjson size "$PAGE_SIZE" --argjson i "$sid" --argjson m "$smax" '
      { size: $size, sort: ["_doc"], _source: false, query: {match_all: {}} }
    + (if $m > 1 then { slice: {id: $i, max: $m} } else {} end)' >"$reqf"
  es6 POST "$ES6_URL/$DST_INDEX/_search?scroll=15m" application/json "$reqf" >/dev/null || {
    [ "$INTERRUPTED" -eq 1 ] && return 130
    warn "$tag id export failed: $(head -c 200 "$RESP")"; return 1; }

  while :; do
    [ "$INTERRUPTED" -eq 1 ] && return 130
    n="$(jq '.hits.hits | length' "$RESP")"
    cur="$(jq -r '._scroll_id // ""' "$RESP")"
    [ "$n" -eq 0 ] && break

    jq -r '.hits.hits[]._id' "$RESP" >>"$out"
    jq -n --arg s "$cur" '{scroll: "15m", scroll_id: $s}' >"$reqf"

    pages=$((pages + 1)); ids=$((ids + n))
    walk_progress "$tag" "$pages" "$ids"

    es6 POST "$ES6_URL/_search/scroll" application/json "$reqf" >/dev/null || {
      [ "$INTERRUPTED" -eq 1 ] && return 130
      # A scroll cannot be resumed from the middle, and a truncated export
      # would understate ES6's id set -- which turns into wrong deletes.
      warn "$tag scroll context lost mid-export"
      return 1
    }
  done
  jq -n --arg s "$cur" '{scroll_id: [$s]}' >"$reqf"
  es6 DELETE "$ES6_URL/_search/scroll" application/json "$reqf" >/dev/null 2>&1 || true
  return 0
}

# export_ids <src|dst> <sorted-output>
#
# Only the walker and the snapshot mechanism differ between the sides: ES9
# shares one PIT across all slices (the documented pattern, and it keeps them
# on one consistent snapshot), ES6 gives every slice its own scroll. A slice
# that died quietly leaves the output short, which the count guard in
# phase_reconcile catches.
export_ids() {
  local side="$1" out="$2" pit="" i rc=0
  local pids=()

  if [ "$side" = "src" ]; then
    resolve_slices es9 "$ES9_URL" "$SRC_INDEX" ES9
    pit="$(pit_open "$ES9_URL" "$SRC_INDEX")" || die "cannot open PIT for id export"
  else
    resolve_slices es6 "$ES6_URL" "$DST_INDEX" ES6
  fi
  rm -f "$WORK"/ids."$side".*

  for ((i = 0; i < SLICE_COUNT; i++)); do
    ( RESP="$WORK/ids.$side.$i.resp"
      if [ "$side" = "src" ]; then
        walk_pit_slice "$pit" "$i" "$SLICE_COUNT" "$WORK/ids.src.$i.ids" "ES9[$i]"
      else
        walk_scroll_slice "$i" "$SLICE_COUNT" "$WORK/ids.dst.$i.ids" "ES6[$i]"
      fi ) &
    pids+=($!)
  done
  for i in "${pids[@]}"; do wait "$i" || rc=1; done

  [ "$side" = "src" ] && pit_close "$ES9_URL" "$pit"
  if [ "$rc" -ne 0 ]; then
    [ "$INTERRUPTED" -eq 1 ] && {
      log "   interrupted during $side id export -- 'resume' restarts it"; exit 130; }
    die "$side id export: a slice failed; see $LOG. Re-run 'resume' to restart it."
  fi

  sort -u -T "$WORK" -S 25% -o "$out" "$WORK"/ids."$side".*.ids
  rm -f "$WORK"/ids."$side".*
  log "   $side id walk done: $(wc -l <"$out" | tr -d ' ') ids"
  return 0
}

phase_reconcile() {
  log "== phase 3: reconcile deletes =="
  state_load
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || warn "ES6 refresh failed"
  es9 POST "$ES9_URL/$SRC_INDEX/_refresh" >/dev/null || warn "ES9 refresh failed"

  local src_count dst_count
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "count failed"
  src_count="$(jq -r '.count' "$RESP")"
  es6 GET "$ES6_URL/$DST_INDEX/_count" >/dev/null || die "count failed"
  dst_count="$(jq -r '.count' "$RESP")"
  log "   counts before reconcile: $SRC_INDEX=$src_count $DST_INDEX=$dst_count"

  local
  log "   exporting live ids from ES9/$SRC_INDEX"
  export_ids src "$STATE_DIR/es9_ids.sorted"
  log "   exporting live ids from ES6/$DST_INDEX"
  export_ids dst "$STATE_DIR/es6_ids.sorted"

  local src_id_count dst_id_count
  src_id_count="$(wc -l <"$STATE_DIR/es9_ids.sorted" | tr -d ' ')"
  dst_id_count="$(wc -l <"$STATE_DIR/es6_ids.sorted" | tr -d ' ')"

  # Without this, an export truncated by a dropped connection looks exactly
  # like "ES9 no longer has these documents", and the diff deletes most of ES6.
  [ "$src_id_count" = "$src_count" ] \
    || die "ES9 id export incomplete: $src_id_count exported vs $src_count counted. Refusing to diff."
  [ "$dst_id_count" = "$dst_count" ] \
    || die "ES6 id export incomplete: $dst_id_count exported vs $dst_count counted. Refusing to diff."
  log "   id sets complete: ES9=$src_id_count ES6=$dst_id_count"

  # Both directions, always. Equal counts do not imply equal id sets: N
  # creates and N deletes on ES9 leave the totals matching while both differ.
  comm -23 "$STATE_DIR/es6_ids.sorted" "$STATE_DIR/es9_ids.sorted" >"$STATE_DIR/to_delete"
  comm -13 "$STATE_DIR/es6_ids.sorted" "$STATE_DIR/es9_ids.sorted" >"$STATE_DIR/to_repair"
  local delete_count repair_count
  delete_count="$(wc -l <"$STATE_DIR/to_delete" | tr -d ' ')"
  repair_count="$(wc -l <"$STATE_DIR/to_repair" | tr -d ' ')"
  log "   to delete from ES6: $delete_count    to repair into ES6: $repair_count"

  if [ "$delete_count" -gt 0 ]; then
    local over
    over="$(awk -v d="$delete_count" -v t="$dst_id_count" -v r="$MAX_DELETE_RATIO" \
      'BEGIN{print (t > 0 && d/t > r) ? "yes" : "no"}')"
    if [ "$over" = "yes" ] && [ "$ASSUME_YES" != "true" ]; then
      warn "sample of ids to delete:"; head -5 "$STATE_DIR/to_delete" >&2
      die "$delete_count deletes is more than $MAX_DELETE_RATIO of ES6's $dst_id_count documents.
Stopping. Review $STATE_DIR/to_delete, then re-run with ASSUME_YES=true if
this really is what happened on ES9."
    fi
    reconcile_deletes "$STATE_DIR/to_delete" "$delete_count"
  fi

  # ES9-only ids mean the delta missed a create -- a write that skipped
  # updated_at, or a doc dead-lettered earlier. Repairing beats reporting:
  # ES6 has to have these documents.
  if [ "$repair_count" -gt 0 ]; then
    warn "$repair_count doc(s) on ES9 are missing from ES6 -- the delta missed them; repairing"
    reconcile_repairs "$STATE_DIR/to_repair"
  fi

  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || warn "refresh failed"
  state_set DELETED "$delete_count"; state_set REPAIRED "$repair_count"
  state_set PHASE RECONCILE_DONE
  log "   reconcile done: deleted=$delete_count repaired=$repair_count"
}

reconcile_deletes() {
  local idfile="$1" total="$2" applied=0 part BULK_TAG=delete
  log "   deleting $total doc(s) from ES6 (journaling pre-images first)"
  rm -f "$PARTS"/delete.*
  split -l "$MGET_BATCH" -a 5 "$idfile" "$PARTS/delete."
  for part in "$PARTS"/delete.*; do
    [ -s "$part" ] || continue
    [ "$INTERRUPTED" -eq 1 ] && { log "   interrupted after $applied deletes"; exit 130; }
    # Deletion is the only irreversible step, so its pre-image is journaled
    # unconditionally; undo restores from it.
    journal_preimage "$part" delete || die "cannot journal pre-images before delete -- aborting"
    id_list_body "$part" "$WORK/delete.bulk.ndjson" delete
    bulk_send "$WORK/delete.bulk.ndjson" || die "bulk delete failed after $applied"
    applied=$((applied + BULK_APPLIED))
  done
  rm -f "$PARTS"/delete.*
  log "   deleted $applied doc(s)"
}

reconcile_repairs() {
  local idfile="$1" applied=0 part seq n BULK_TAG=repair
  rm -f "$PARTS"/repair.*
  split -l "$MGET_BATCH" -a 5 "$idfile" "$PARTS/repair."
  for part in "$PARTS"/repair.*; do
    [ -s "$part" ] || continue
    [ "$INTERRUPTED" -eq 1 ] && exit 130
    id_list_body "$part" "$WORK/repair.mget.json" mget
    es9 POST "$ES9_URL/$SRC_INDEX/_mget" application/json "$WORK/repair.mget.json" >/dev/null \
      || die "repair _mget from ES9 failed"
    # Routing travels with the document, same reason as in split_delta_page.
    jq -c '.docs[] | select(.found)
           | ({index: ({_id: ._id} + (if ._routing then {routing: ._routing} else {} end))}),
             ._source' "$RESP" >"$WORK/repair.bulk.ndjson"
    # These ids are absent from ES6 by construction, so the pre-image is
    # "absent" -- journal it directly, no _mget needed. Undo deletes them.
    state_load; seq="${JOURNAL_SEQ:-0}"; n="$(wc -l <"$part" | tr -d ' ')"
    awk -v s="$seq" '{printf "%d\t%s\trepair\t0\t{}\n", s + NR, $0}' "$part" | gzip -1 >>"$JOURNAL"
    state_set JOURNAL_SEQ "$((seq + n))"
    bulk_send "$WORK/repair.bulk.ndjson" || die "repair bulk failed after $applied"
    applied=$((applied + BULK_APPLIED))
  done
  rm -f "$PARTS"/repair.*
  log "   repaired $applied doc(s)"
}

# ------------------------------------------------------------------ phase 4 --

phase_verify() {
  log "== phase 4: verify =="
  state_load
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || true
  es9 POST "$ES9_URL/$SRC_INDEX/_refresh" >/dev/null || true

  local src_count dst_count rc=0
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "count failed"
  src_count="$(jq -r '.count' "$RESP")"
  es6 GET "$ES6_URL/$DST_INDEX/_count" >/dev/null || die "count failed"
  dst_count="$(jq -r '.count' "$RESP")"
  log "   counts: $SRC_INDEX=$src_count $DST_INDEX=$dst_count"
  [ "$src_count" = "$dst_count" ] || { warn "count mismatch: $src_count vs $dst_count"; rc=1; }

  # The expected post-reconcile ES6 id set is (es6 - to_delete) + to_repair,
  # and all three files are already on disk, so checking it is free.
  if [ -s "$STATE_DIR/es9_ids.sorted" ] && [ -s "$STATE_DIR/es6_ids.sorted" ]; then
    comm -23 "$STATE_DIR/es6_ids.sorted" "$STATE_DIR/to_delete" \
      | sort -u -T "$WORK" -o "$WORK/verify.expected.ids" - "$STATE_DIR/to_repair"
    if cmp -s "$WORK/verify.expected.ids" "$STATE_DIR/es9_ids.sorted"; then
      log "   expected ES6 id set matches ES9 exactly"
    else
      warn "expected id set differs from ES9 -- re-exporting ES6 ids to locate it"
      export_ids dst "$WORK/verify.dst.sorted"
      comm -23 "$WORK/verify.dst.sorted" "$STATE_DIR/es9_ids.sorted" >"$STATE_DIR/verify_extra"
      comm -13 "$WORK/verify.dst.sorted" "$STATE_DIR/es9_ids.sorted" >"$STATE_DIR/verify_missing"
      warn "extra on ES6:   $(wc -l <"$STATE_DIR/verify_extra" | tr -d ' ') -> $STATE_DIR/verify_extra"
      warn "missing on ES6: $(wc -l <"$STATE_DIR/verify_missing" | tr -d ' ') -> $STATE_DIR/verify_missing"
      rc=1
    fi
  fi

  # Content sample. _source is copied verbatim, so any difference is a real
  # defect rather than a formatting artefact. Fixed seed keeps it repeatable.
  if [ -s "$STATE_DIR/es9_ids.sorted" ] && [ "$SAMPLE_N" -gt 0 ]; then
    awk -v n="$SAMPLE_N" -v t="$(wc -l <"$STATE_DIR/es9_ids.sorted" | tr -d ' ')" \
      'BEGIN{srand(42)} rand() < n/t' "$STATE_DIR/es9_ids.sorted" \
      | head -n "$SAMPLE_N" >"$WORK/verify.sample.ids"
    if [ -s "$WORK/verify.sample.ids" ]; then
      id_list_body "$WORK/verify.sample.ids" "$WORK/verify.sample.mget.json" mget
      # Only the first response needs a copy; the second is read from $RESP.
      es9 POST "$ES9_URL/$SRC_INDEX/_mget" application/json "$WORK/verify.sample.mget.json" >/dev/null \
        || die "sample _mget on ES9 failed"
      cp "$RESP" "$WORK/verify.sample.src.json"
      es6 POST "$ES6_URL/$DST_INDEX/_doc/_mget" application/json "$WORK/verify.sample.mget.json" >/dev/null \
        || die "sample _mget on ES6 failed"
      python3 - "$WORK/verify.sample.src.json" "$RESP" <<'PY' >"$STATE_DIR/verify_sample_diff"
import json, sys
def srcmap(p):
    docs = json.load(open(p, encoding='utf-8'))['docs']
    return {d['_id']: (d.get('_source') if d.get('found') else None) for d in docs}
A, B = srcmap(sys.argv[1]), srcmap(sys.argv[2])
for k in sorted(A):
    if A[k] != B.get(k): print(k)
PY
      local differing sampled
      differing="$(wc -l <"$STATE_DIR/verify_sample_diff" | tr -d ' ')"
      sampled="$(wc -l <"$WORK/verify.sample.ids" | tr -d ' ')"
      if [ "$differing" -gt 0 ]; then
        warn "$differing/$sampled sampled doc(s) differ -> $STATE_DIR/verify_sample_diff"; rc=1
      else
        log "   content sample: $sampled doc(s) identical"
      fi
    fi
  fi

  if [ "$rc" -eq 0 ]; then
    state_set PHASE DONE
    log "   VERIFY PASSED -- ES6 matches ES9; safe to flip traffic back"
  else
    warn "VERIFY FAILED -- do not flip traffic yet"
  fi
  return "$rc"
}

# --------------------------------------------------------------------- undo --

cmd_undo() {
  [ -s "$JOURNAL" ] || die "no journal at $JOURNAL -- nothing to undo"
  acquire_lock
  log "== undo: restoring $DST_INDEX from journal =="

  # A resume re-writes documents an earlier attempt already synced, so a
  # later journal row for an id holds what is really a post-image. Keeping
  # the lowest seq per id recovers the true original in every case.
  zcat "$JOURNAL" \
    | sort -t "$(printf '\t')" -k2,2 -k1,1n -T "$WORK" -S 25% \
    | awk -F '\t' '!seen[$2]++' >"$WORK/undo.rows.tsv"
  log "   $(wc -l <"$WORK/undo.rows.tsv" | tr -d ' ') distinct doc(s) to restore"

  rm -f "$PARTS"/undo.*
  split -l "$MGET_BATCH" -a 5 "$WORK/undo.rows.tsv" "$PARTS/undo."
  local part applied=0 BULK_TAG=undo
  for part in "$PARTS"/undo.*; do
    [ -s "$part" ] || continue
    # Row layout is seq/id/op/found/source. `op` is audit metadata; undo keys
    # off `found`: 1 means there is a pre-image to put back, 0 means the
    # document did not exist on ES6 before the run, so undoing it is a delete.
    jq -Rc 'split("\t")
            | if .[3] == "1" then ({index: {_id: .[1]}}), (.[4] | fromjson)
              else ({delete: {_id: .[1]}}) end' "$part" >"$WORK/undo.bulk.ndjson"
    bulk_send "$WORK/undo.bulk.ndjson" || die "undo bulk failed after $applied"
    applied=$((applied + BULK_APPLIED))
  done
  rm -f "$PARTS"/undo.*
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || true
  log "   undo applied to $applied doc(s); $DST_INDEX is back to its pre-run state"
}

# ------------------------------------------------------------- subcommands --

pipeline() {
  state_load
  case "${PHASE:-DELTA_SYNC}" in
    DELTA_SYNC)     phase_delta; phase_gate; phase_reconcile ;;
    DELTA_DONE)     phase_gate; phase_reconcile ;;
    GATE_PASSED)    phase_reconcile ;;
    RECONCILE_DONE) ;;
    *) die "unknown phase: $PHASE" ;;
  esac
  local rc=0
  phase_verify || rc=$?
  state_load
  if [ "${DL_COUNT:-0}" -gt 0 ]; then
    deadletter_summary
    warn "finished with ${DL_COUNT} dead-lettered doc(s) in $DEADLETTER"
    exit 2
  fi
  exit "$rc"
}

cmd_run() {
  state_load
  if [ -n "${PHASE:-}" ] && [ "$PHASE" != "DONE" ]; then
    die "a run is already in progress (phase=$PHASE). Use 'resume', or 'reset' to discard it."
  fi
  acquire_lock
  # A journal left over from an earlier run has to be moved aside, not
  # appended to. Sequence numbers restart at 0 for each run, so mixing two
  # runs in one file makes "lowest seq per id" ambiguous -- and undo would
  # then be able to pick a post-sync image as if it were the original.
  if [ -s "$JOURNAL" ]; then
    local arch="$STATE_DIR/journal.$(date -u +%Y%m%dT%H%M%SZ).tsv.gz"
    mv "$JOURNAL" "$arch"
    warn "previous journal archived to $arch"
    warn "'undo' only ever replays the current run; restore from an archive by hand"
  fi
  rm -f "$CURSOR_FILE" "$PIT_FILE"; : >"$DEADLETTER"
  phase_preflight
  state_set RUN_ID "$(date -u +%Y%m%dT%H%M%SZ)"
  state_set CUTOVER_AT "$PREFLIGHT_CUTOVER_AT"
  state_set EFFECTIVE_SINCE "$PREFLIGHT_SINCE"
  state_set RUN_SRC_INDEX "$SRC_INDEX"; state_set RUN_DST_INDEX "$DST_INDEX"
  state_set RUN_TS_FIELD "$TS_FIELD"
  state_set SYNCED 0; state_set SEEN 0; state_set DL_COUNT 0; state_set JOURNAL_SEQ 0
  state_set PHASE DELTA_SYNC
  pipeline
}

cmd_resume() {
  state_load
  [ -n "${PHASE:-}" ] || die "no run to resume in $STATE_DIR"
  [ "$PHASE" = "DONE" ] && { log "run already complete"; return 0; }
  acquire_lock
  # Resuming against a different source than the run started on would
  # invalidate every checkpoint.
  [ "${RUN_SRC_INDEX:-$SRC_INDEX}" = "$SRC_INDEX" ] || die "state belongs to SRC_INDEX=${RUN_SRC_INDEX}"
  [ "${RUN_DST_INDEX:-$DST_INDEX}" = "$DST_INDEX" ] || die "state belongs to DST_INDEX=${RUN_DST_INDEX}"
  # Same reasoning for the field: SEEN and TOTAL_HITS were counted against one
  # window, and switching to or away from `all` redefines what they mean.
  [ "${RUN_TS_FIELD:-$TS_FIELD}" = "$TS_FIELD" ] \
    || die "state belongs to TS_FIELD=${RUN_TS_FIELD} (you passed $TS_FIELD) -- 'reset' to start over"
  log "resuming from phase=$PHASE (seen=${SEEN:-0} synced=${SYNCED:-0})"
  pipeline
}

cmd_status() {
  state_load
  [ -n "${PHASE:-}" ] || { echo "no run in $STATE_DIR"; return 0; }
  cat <<EOF
state dir      : $STATE_DIR
run id         : ${RUN_ID:-?}
phase          : $PHASE
ts field       : ${RUN_TS_FIELD:-?}
cutover_at     : ${CUTOVER_AT:-(none: full copy)}
lower bound    : ${EFFECTIVE_SINCE:-(none: full copy)}
phase 1 total  : ${TOTAL_HITS:-?}
seen / synced  : ${SEEN:-0} / ${SYNCED:-0}
dead letters   : ${DL_COUNT:-0}   ($DEADLETTER)
deleted        : ${DELETED:-0}
repaired       : ${REPAIRED:-0}
journal rows   : ${JOURNAL_SEQ:-0}   ($JOURNAL)
EOF
  [ "${DL_COUNT:-0}" -gt 0 ] && deadletter_summary
  case "$PHASE" in
    DELTA_SYNC|DELTA_DONE|GATE_PASSED) echo "next           : ./es_rollback_py.sh resume" ;;
    RECONCILE_DONE)                    echo "next           : ./es_rollback_py.sh verify" ;;
    DONE)                              echo "next           : flip traffic to ES6, then 'reset'" ;;
  esac
}

cmd_reset() {
  state_load
  acquire_lock
  rm -f "$STATE" "$CURSOR_FILE" "$PIT_FILE"
  rm -rf "$WORK"
  if [ -s "$JOURNAL" ]; then
    warn "journal kept at $JOURNAL -- remove it by hand once you are sure no undo is needed"
  else
    rm -f "$JOURNAL" "$DEADLETTER"
  fi
  log "state cleared"
}

# Marker-delimited, not a line range -- a range drifts the moment the header
# is edited, and did.
usage() {
  sed -n '/^#:USAGE$/,/^#:END-USAGE$/{ /^#:/d; s/^# \{0,1\}//; p; }' "$0"
  exit 1
}

main() {
  # Deferred so a page in flight finishes and checkpoints instead of being
  # torn in half. Worst case one page is redone on resume.
  trap 'INTERRUPTED=1; echo; echo ">> interrupt received, finishing current page..."' INT TERM
  # Every command that touches a cluster works on the concrete index, not the
  # alias -- including resume and undo, which never run preflight. status and
  # reset read local files only, so they stay offline.
  case "${1:-}" in
    preflight|run|resume|verify|undo) resolve_aliases ;;
  esac
  case "${1:-}" in
    preflight) phase_preflight; log "preflight OK" ;;
    run)       cmd_run ;;
    resume)    cmd_resume ;;
    status)    cmd_status ;;
    verify)    acquire_lock; phase_verify ;;
    undo)      cmd_undo ;;
    reset)     cmd_reset ;;
    *)         usage ;;
  esac
}

# Sourceable for testing: `ES_ROLLBACK_LIB=1 . es_rollback_py.sh` loads the
# helpers without running a command.
if [ "${ES_ROLLBACK_LIB:-}" != "1" ]; then
  main "$@"
fi
