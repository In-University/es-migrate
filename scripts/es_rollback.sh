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
#   0 PREFLIGHT   connectivity, indices exist, ES6 writable, cutover marker,
#                 and a positive check that ES9 really is frozen
#   1 DELTA_SYNC  ES9 (updated_at > cutover) -> ES6, resumable, journaled
#   2 DELTA_GATE  cursor exhausted + no dead letters; blocks phase 3 otherwise
#   3 RECONCILE   live _id set diff, both directions: delete ES6-only,
#                 repair ES9-only
#   4 VERIFY      counts, expected id set, random _source sample
#
# Assumptions, all checked rather than trusted:
#   - ES9 takes no writes for the duration. Verified in preflight by
#     sampling _count and max(updated_at) twice.
#   - Every write on ES9 bumped `updated_at`. The phase 3 reverse diff is
#     the safety net if that ever failed for a create.
#
# Undo: every document is read from ES6 and journaled BEFORE it is
# overwritten or deleted, so `undo` restores ES6 exactly. No snapshots.
#
# Dependencies: curl, jq, awk, sort, comm, gzip, split.
# NOTE: jq is not part of a stock Ubuntu image -- `apt-get install -y jq`.
#
# Usage:
#   ./es_rollback.sh preflight   checks only, writes nothing
#   ./es_rollback.sh plan        preflight + report delta and count sizes
#   ./es_rollback.sh run         start a fresh run
#   ./es_rollback.sh resume      continue an interrupted run
#   ./es_rollback.sh status      show phase and counters
#   ./es_rollback.sh verify      re-run phase 4 on its own
#   ./es_rollback.sh undo        restore ES6 from the journal
#   ./es_rollback.sh reset       drop state (keeps the journal)
#
# Env vars, grouped by how often you have any business touching them.
#
# CONNECTION -- set these on every run:
#   ES6_URL / ES9_URL     base URLs               (default http://localhost:9200)
#   SRC_INDEX             ES9 index, the source   (default bench-es9)
#   DST_INDEX             ES6 index, the target   (default bench-es6)
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
#
# SAFETY -- read the phase they belong to before changing any of these:
#   SAFETY_MARGIN         seconds shaved off cutover_at (default 300)
#   MAX_DELETE_RATIO      refuse deletes above this share of ES6 (default 0.10)
#   FREEZE_WAIT           seconds between freeze samples (default 10)
#   SAMPLE_N              docs compared in verify (default 1000)
#   SINCE                 override cutover_at     (ISO-8601, optional)
#   ALLOW_PARTIAL         "true" lets the gate pass with dead letters
#   ASSUME_YES            "true" skips the delete-ratio confirmation
#
# DEBUG -- temporary instrumentation, see the block further down:
#   DEBUG_TIMING          "1" adds DEBUG lines attributing time per page
#   DEBUG_EVERY           pages between id-walk DEBUG lines (default 50)
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

# ------------------------------------------------------------ config: 3/3 --
# SAFETY. The last three disable a guard -- read the phase that uses one first.
SAFETY_MARGIN="${SAFETY_MARGIN:-300}"
MAX_DELETE_RATIO="${MAX_DELETE_RATIO:-0.10}"
FREEZE_WAIT="${FREEZE_WAIT:-10}"
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

# ===================== DEBUG timing instrumentation ======================
# TEMPORARY. Answers one question: when a page takes minutes, is the time in
# ES9 reads, ES6 pre-image reads, ES6 writes, or local jq/awk? An I/O-starved
# cluster and a slow script have completely different fixes. Off by default,
# costs nothing when off; enable with DEBUG_TIMING=1.
#
# TO REMOVE: delete this block, then `grep -n 'dbg_' es_rollback.sh` and
# delete those call sites. Every line it prints contains "DEBUG" so
# `grep -v DEBUG` cleans up a captured log.
#
DEBUG_TIMING="${DEBUG_TIMING:-0}"
DBG_SEARCH=0; DBG_JOURNAL=0; DBG_BULK=0; DBG_PAGE_T0=0; DBG_PHASE_T0=0

# Microseconds. EPOCHREALTIME is a bash builtin formatted sec.microsec, so
# stripping the dot costs no process spawn. LC_ALL=C guarantees the dot.
dbg_us() {
  if [ -n "${EPOCHREALTIME:-}" ]; then printf '%s' "${EPOCHREALTIME/./}"
  else printf '%s000000' "$(date -u +%s)"; fi
}

dbg_t0() { [ "$DEBUG_TIMING" = "1" ] || return 0; dbg_us; }

# dbg_add <accumulator-var> <start-us>
dbg_add() {
  [ "$DEBUG_TIMING" = "1" ] || return 0
  [ -n "${2:-}" ] || return 0
  eval "$1=\$(( \${$1:-0} + \$(dbg_us) - \$2 ))"
}

dbg_page_start() {
  [ "$DEBUG_TIMING" = "1" ] || return 0
  DBG_SEARCH=0; DBG_JOURNAL=0; DBG_BULK=0; DBG_PAGE_T0="$(dbg_us)"
}

dbg_page_end() {
  [ "$DEBUG_TIMING" = "1" ] || return 0
  local total local_ms
  total=$(( $(dbg_us) - DBG_PAGE_T0 ))
  local_ms=$(( total - DBG_SEARCH - DBG_JOURNAL - DBG_BULK ))
  printf '%s DEBUG page %s docs | total %sms = es9_search %sms + es6_mget %sms + es6_bulk %sms + local %sms\n' \
    "$(date -u +%H:%M:%S)" "${1:-?}" \
    "$((total / 1000))" "$((DBG_SEARCH / 1000))" "$((DBG_JOURNAL / 1000))" \
    "$((DBG_BULK / 1000))" "$((local_ms / 1000))" | tee -a "$LOG"
}

dbg_phase_start() { [ "$DEBUG_TIMING" = "1" ] || return 0; DBG_PHASE_T0="$(dbg_us)"; }

dbg_phase_end() {
  [ "$DEBUG_TIMING" = "1" ] || return 0
  printf '%s DEBUG %s took %ss\n' "$(date -u +%H:%M:%S)" "$1" \
    "$(( ($(dbg_us) - DBG_PHASE_T0) / 1000000 ))" | tee -a "$LOG"
}

# dbg_step <label> <start-us> -- one-off durations outside the page loop.
dbg_step() {
  [ "$DEBUG_TIMING" = "1" ] || return 0
  printf '%s DEBUG %s took %sms\n' "$(date -u +%H:%M:%S)" "$1" \
    "$(( ($(dbg_us) - $2) / 1000 ))" | tee -a "$LOG"
}

# --- id-export breakdown -------------------------------------------------
# The id walk is the longest stretch of a run, and its cost could be ES's
# fetch phase, the jq parses, or appending to the output file -- different
# fixes, so measure them separately.
DEBUG_EVERY="${DEBUG_EVERY:-50}"
DBG_EXP_BODY=0; DBG_EXP_HTTP=0; DBG_EXP_COUNT=0
DBG_EXP_WRITE=0; DBG_EXP_CURSOR=0; DBG_EXP_IDS=0; DBG_EXP_T0=0

dbg_export_reset() {
  [ "$DEBUG_TIMING" = "1" ] || return 0
  DBG_EXP_BODY=0; DBG_EXP_HTTP=0; DBG_EXP_COUNT=0
  DBG_EXP_WRITE=0; DBG_EXP_CURSOR=0; DBG_EXP_IDS=0
  DBG_EXP_T0="$(dbg_us)"
}

# Average microseconds -> "12.3" milliseconds.
dbg_avg_ms() {
  local n="$2" v
  [ "${n:-0}" -gt 0 ] || n=1
  v=$(( $1 / n ))
  printf '%d.%d' "$((v / 1000))" "$(( (v % 1000) / 100 ))"
}

# dbg_export_total <side> <start-us> <file> <slices>
#
# Per-walker rates are the wrong number to judge slicing by: three walkers at
# 8k ids/s beat one at 11k. Measure ids on disk over the whole export's wall
# clock instead.
dbg_export_total() {
  [ "$DEBUG_TIMING" = "1" ] || return 0
  local side="$1" t0="$2" file="$3" slices="$4" wall ids
  wall=$(( $(dbg_us) - t0 ))
  ids="$(wc -l <"$file" | tr -d ' ')"
  printf '%s DEBUG %s export TOTAL: %s ids in %ss across %s slice(s) = %s ids/s\n' \
    "$(date -u +%H:%M:%S)" "$side" "$ids" "$((wall / 1000000))" "$slices" \
    "$(( ids * 1000000 / (wall > 0 ? wall : 1) ))" | tee -a "$LOG"
}

# dbg_export_tick <side> <pages>
#
# The first three pages always report: waiting for page 50 on a slow export
# means waiting minutes for the first data point.
dbg_export_tick() {
  [ "$DEBUG_TIMING" = "1" ] || return 0
  if [ "$2" -le 3 ] || { [ "${DEBUG_EVERY:-0}" -gt 0 ] && [ $(( $2 % DEBUG_EVERY )) -eq 0 ]; }; then
    dbg_export_summary "$1" "$2"
  fi
}

# dbg_export_summary <side> <pages>
#
# "other" is wall clock minus everything measured. Large "other" means the
# script is the problem; http dominating means the cluster is.
dbg_export_summary() {
  [ "$DEBUG_TIMING" = "1" ] || return 0
  local side="$1" pages="$2" wall other rate
  [ "${pages:-0}" -gt 0 ] || return 0
  wall=$(( $(dbg_us) - DBG_EXP_T0 ))
  other=$(( wall - DBG_EXP_BODY - DBG_EXP_HTTP - DBG_EXP_COUNT - DBG_EXP_WRITE - DBG_EXP_CURSOR ))
  rate=$(( DBG_EXP_IDS * 1000000 / (wall > 0 ? wall : 1) ))
  printf '%s DEBUG %s export: %s pages, %s ids, %ss elapsed, %s ids/s in THIS walker | avg/page: http %sms  write %sms  count %sms  cursor %sms  body %sms  other %sms\n' \
    "$(date -u +%H:%M:%S)" "$side" "$pages" "$DBG_EXP_IDS" "$((wall / 1000000))" "$rate" \
    "$(dbg_avg_ms "$DBG_EXP_HTTP" "$pages")" \
    "$(dbg_avg_ms "$DBG_EXP_WRITE" "$pages")" \
    "$(dbg_avg_ms "$DBG_EXP_COUNT" "$pages")" \
    "$(dbg_avg_ms "$DBG_EXP_CURSOR" "$pages")" \
    "$(dbg_avg_ms "$DBG_EXP_BODY" "$pages")" \
    "$(dbg_avg_ms "$other" "$pages")" | tee -a "$LOG"
}
# =================== end DEBUG timing instrumentation ====================

# ------------------------------------------------------------- json shaping --

# Body for one delta page. Built by jq so PIT ids and search_after arrays are
# never string-interpolated into shell-quoted JSON. `op` is gt or gte -- see
# phase_delta for why that switches.
delta_page_body() {
  local pit="$1" since="$2" out="$3" cursor_src="$4" op="${5:-gt}"
  local cursor="null"
  [ -s "$cursor_src" ] && cursor="$(cat "$cursor_src")"
  jq -n --arg pit "$pit" --arg since "$since" --arg op "$op" \
        --argjson size "$PAGE_SIZE" --argjson sa "$cursor" '
      { query: {range: {updated_at: {($op): $since}}},
        sort: [{updated_at: "asc"}, {_shard_doc: "asc"}], size: $size }
    + (if $pit == "" then {} else { pit: {id: $pit, keep_alive: "15m"} } end)
    + (if $sa == null then { track_total_hits: true } else { search_after: $sa } end)
  ' >"$out"
}

# One ES9 delta page -> id list, bulk chunks capped at BULK_BYTE_CAP, and a
# staged next cursor. Prints "<hits> <last_updated_at>".
split_delta_page() {
  local resp="$1"
  rm -f "$WORK"/delta.chunk.*.ndjson
  jq -r '.hits.hits[]._id' "$resp" >"$WORK/delta.page.ids"
  jq -c '.hits.hits[-1].sort // empty' "$resp" >"$WORK/delta.cursor.next.json"
  # Custom routing has to travel with the document or it lands on a
  # different shard on ES6 and later routed lookups miss it.
  #
  # Chunk on byte size, two lines at a time, so an action is never separated
  # from the source line it belongs to.
  jq -c '.hits.hits[]
         | ({index: ({_id: ._id} + (if ._routing then {routing: ._routing} else {} end))}),
           ._source' "$resp" \
  | awk -v cap="$BULK_BYTE_CAP" -v pre="$WORK/delta.chunk." '
      { a = $0; if ((getline b) <= 0) b = "{}"
        n = length(a) + length(b) + 2
        if (sz > 0 && sz + n > cap) { close(f); i++; sz = 0 }
        f = sprintf("%s%04d.ndjson", pre, i + 0)
        print a >> f; print b >> f; sz += n }'
  printf '%s %s\n' \
    "$(jq '.hits.hits | length' "$resp")" \
    "$(jq -r '.hits.hits[-1]._source.updated_at // ""' "$resp")"
}

# Classify a _bulk response. ES answers 200 even when individual items
# failed, so discarding the body silently drops documents while reporting
# success. Splits into a retry set and a dead letter file; prints
# "<ok> <retry> <fatal>".
parse_bulk() {
  local resp="$1" sent="$2" retry_out="$3" dl="$4"
  : >"$retry_out"
  # Bulk item n -> its action line and (for index ops) its source line.
  awk '{ a = $0
         if (a ~ /^[[:space:]]*\{"delete"/) { printf "%d\t%s\t\n", n++, a }
         else { if ((getline b) <= 0) b = ""; printf "%d\t%s\t%s\n", n++, a, b } }' \
      "$sent" >"$WORK/bulk.pairs.tsv"
  jq -r '
    .items | to_entries[]
    | .key as $i
    | (.value | to_entries[0]) as $e
    | $e.value as $b
    | ($b.status // 200) as $st
    | ($b.error.type // "") as $et
    | (if   $st < 300 then "ok"
       elif $e.key == "delete" and $st == 404 then "ok"
       elif $st == 429 or $st == 502 or $st == 503 or $st == 504 then "retry"
       elif $et | test("es_rejected_execution|circuit_breaking|cluster_block|unavailable_shards")
            then "retry"
       else "fatal" end) as $v
    | "\($i)\t\($v)\t\($st)\t\($b._id // "")\t\(($b.error // {}) | tojson)"
  ' "$resp" \
  | awk -F '\t' -v retry="$retry_out" -v dl="$dl" '
      # action/source are already JSON text, so they drop into the dead letter
      # record as values without any re-escaping.
      NR == FNR { act[$1] = $2; src[$1] = $3; next }
      { if ($2 == "ok") ok++
        else if ($2 == "retry") {
          r++; print act[$1] >> retry; if (src[$1] != "") print src[$1] >> retry
        } else {
          f++
          printf "{\"_id\":\"%s\",\"status\":%s,\"error\":%s,\"action\":%s,\"source\":%s}\n",
                 $4, $3, $5, (act[$1] == "" ? "null" : act[$1]),
                 (src[$1] == "" ? "null" : src[$1]) >> dl
        } }
      END { printf "%d %d %d\n", ok+0, r+0, f+0 }
    ' "$WORK/bulk.pairs.tsv" -
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
  local file="$1" attempt=0
  local sent="$file" retry_file="$WORK/bulk.retry.ndjson"
  BULK_APPLIED=0; BULK_DEADLETTERED=0
  while :; do
    local code counts ok retry fatal _dbg
    _dbg="$(dbg_t0)"
    code="$(es6 POST "$ES6_URL/$DST_INDEX/_doc/_bulk" application/x-ndjson "$sent")" || {
      dbg_add DBG_BULK "$_dbg"
      warn "bulk request failed with HTTP $code"
      return 1
    }
    dbg_add DBG_BULK "$_dbg"
    counts="$(parse_bulk "$RESP" "$sent" "$retry_file" "$DEADLETTER")"
    ok="$(echo "$counts" | awk '{print $1}')"
    retry="$(echo "$counts" | awk '{print $2}')"
    fatal="$(echo "$counts" | awk '{print $3}')"
    BULK_APPLIED=$((BULK_APPLIED + ok)); BULK_DEADLETTERED=$((BULK_DEADLETTERED + fatal))
    [ "$retry" -eq 0 ] && return 0
    attempt=$((attempt + 1))
    if [ "$attempt" -ge "$MAX_RETRY" ]; then
      warn "$retry item(s) still rejected after $MAX_RETRY attempts -- dead-lettering"
      cat "$retry_file" >>"$DEADLETTER"
      BULK_DEADLETTERED=$((BULK_DEADLETTERED + retry))
      return 0
    fi
    warn "$retry item(s) rejected (transient) -- retry $attempt/$MAX_RETRY"
    sleep "$(backoff "$attempt")"
    sent="$WORK/bulk.send.ndjson"
    mv "$retry_file" "$sent"
  done
}

# Read the ES6 pre-image of every id in a file into the journal, before the
# caller overwrites or deletes them.
#
# _mget is realtime -- it reads the translog -- so it returns the current
# value even with refresh_interval unset. A search-based read could miss a
# recent write and journal a stale pre-image.
journal_preimage() {
  local idfile="$1" op="${2:-delta}" part seq n _dbg
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
    _dbg="$(dbg_t0)"
    es6 POST "$ES6_URL/$DST_INDEX/_doc/_mget" application/json "$WORK/journal.mget.json" >/dev/null \
      || { warn "pre-image _mget failed -- refusing to write without a journal"; return 1; }
    dbg_add DBG_JOURNAL "$_dbg"
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

# ------------------------------------------------------------------ phase 0 --

phase_preflight() {
  log "== phase 0: preflight =="

  for bin in curl jq awk sort comm gzip split; do
    command -v "$bin" >/dev/null 2>&1 || die "missing required tool: $bin"
  done
  [ -n "$ES6_PW" ] || die "set ELASTIC_PW (or ES6_PW)"
  [ -n "$ES9_PW" ] || die "set ELASTIC_PW (or ES9_PW)"

  es9 GET "$ES9_URL/" >/dev/null || die "cannot reach/authenticate ES9 at $ES9_URL"
  es6 GET "$ES6_URL/" >/dev/null || die "cannot reach/authenticate ES6 at $ES6_URL"
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "ES9 index $SRC_INDEX not found"
  es6 GET "$ES6_URL/$DST_INDEX/_count" >/dev/null || die "ES6 index $DST_INDEX not found"
  log "   ES9 and ES6 reachable, both indices present"

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

  local cutover
  if [ -n "$SINCE" ]; then
    cutover="$SINCE"; log "   using SINCE override: $cutover"
  else
    es9 GET "$ES9_URL/$SRC_INDEX/_mapping" >/dev/null || die "cannot read $SRC_INDEX mapping"
    cutover="$(jq -r '.[].mappings._meta.cutover_at // ""' "$RESP")"
    [ -n "$cutover" ] || die "_meta.cutover_at missing on $SRC_INDEX -- pass SINCE=<ISO-8601>"
    log "   cutover_at=$cutover"
  fi

  # The marker came from `date -u` on the ES9 VM, document timestamps from the
  # application -- different clocks. Rewinding the lower bound costs a few
  # redundant whole-document overwrites against a frozen source, and removes
  # the skew direction that would otherwise drop documents silently.
  local effective
  effective="$(jq -rn --arg t "$cutover" --argjson m "$SAFETY_MARGIN" '
      ($t | fromdateiso8601) as $e
      | if $e > now then error("future") else ($e - $m | todateiso8601) end
    ' 2>/dev/null)" \
    || die "cutover_at is unusable (not ISO-8601, or in the future): $cutover"
  log "   effective lower bound (-${SAFETY_MARGIN}s): $effective"

  # Every correctness argument below assumes ES9 is standing still. Sampling
  # twice is cheap and catches writers nobody remembered to stop.
  local count_first count_second maxts_first maxts_second
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "count failed"
  count_first="$(jq -r '.count' "$RESP")"; maxts_first="$(src_max_updated_at)"
  log "   freeze sample 1: count=$count_first max(updated_at)=$maxts_first -- waiting ${FREEZE_WAIT}s"
  sleep "$FREEZE_WAIT"
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "count failed"
  count_second="$(jq -r '.count' "$RESP")"; maxts_second="$(src_max_updated_at)"
  if [ "$count_first" != "$count_second" ] || [ "$maxts_first" != "$maxts_second" ]; then
    die "ES9 is still taking writes (count $count_first->$count_second, max updated_at $maxts_first->$maxts_second).
Stop the writers first, or both the delta window and the id diff are
computed against a moving target."
  fi
  log "   freeze verified: ES9 static over ${FREEZE_WAIT}s"

  # Outputs of this phase, read by cmd_run and cmd_plan.
  PREFLIGHT_CUTOVER_AT="$cutover"
  PREFLIGHT_SINCE="$effective"
  PREFLIGHT_SRC_COUNT="$count_second"
}

src_max_updated_at() {
  jq -n '{size: 0, aggs: {m: {max: {field: "updated_at"}}}}' >"$WORK/preflight.maxagg.json"
  es9 POST "$ES9_URL/$SRC_INDEX/_search" application/json "$WORK/preflight.maxagg.json" >/dev/null \
    || die "max(updated_at) aggregation failed on $SRC_INDEX"
  jq -r '.aggregations.m.value_as_string // (.aggregations.m.value | tostring)' "$RESP"
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
  log "== phase 1: delta sync $SRC_INDEX -> $DST_INDEX =="
  dbg_phase_start
  state_load
  local since="$EFFECTIVE_SINCE" pit="" _dbg
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

    dbg_page_start
    delta_page_body "$pit" "$since" "$WORK/delta.request.json" "$CURSOR_FILE" "$range_op"
    _dbg="$(dbg_t0)"
    if ! es9 POST "$ES9_URL/_search" application/json "$WORK/delta.request.json" >/dev/null; then
      dbg_add DBG_SEARCH "$_dbg"
      # An expired PIT (or a node restart) shows up as search_context_missing.
      # ES9 is frozen, so reopening and restarting from the last committed
      # watermark is exactly right: the overlap rewrites identical content.
      if grep -q 'search_context_missing\|No search context found' "$RESP" 2>/dev/null; then
        restarts=$((restarts + 1))
        [ "$restarts" -gt 10 ] && die "PIT expired $restarts times without finishing; raise keep_alive or reduce PAGE_SIZE"
        warn "PIT expired -- reopening, resuming from watermark ${WATERMARK:-$since} (inclusive)"
        pit="$(pit_open "$ES9_URL" "$SRC_INDEX")" || die "cannot reopen PIT"
        printf '%s' "$pit" >"$PIT_FILE"
        state_load; since="${WATERMARK:-$since}"; range_op="gte"; : >"$CURSOR_FILE"
        continue
      fi
      [ "$INTERRUPTED" -eq 1 ] && {
        state_set SYNCED "$synced"; state_set SEEN "$seen"; state_set DL_COUNT "$deadletters"
        log "   interrupted during delta search -- checkpointed at seen=$seen"
        exit 130
      }
      die "delta search failed: $(head -c 200 "$RESP")"
    fi
    dbg_add DBG_SEARCH "$_dbg"

    if [ "$seen" -eq 0 ] && [ ! -s "$CURSOR_FILE" ]; then
      state_set TOTAL_HITS "$(jq -r '.hits.total.value // .hits.total' "$RESP")"
      log "   delta window contains $TOTAL_HITS doc(s)"
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
    dbg_page_end "$hits"
  done

  pit_close "$ES9_URL" "$pit"; rm -f "$PIT_FILE" "$CURSOR_FILE"
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || warn "refresh failed"
  dbg_phase_end "phase 1"
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

# Walk one PIT slice into its own file. Runs inside a subshell that has already
# pointed RESP at a private file, and every file it touches is named after the
# slice -- otherwise concurrent slices overwrite each other.
walk_pit_slice() {
  local pit="$1" sid="$2" smax="$3" out="$4" tag="$5"
  local reqf="$WORK/ids.src.$sid.request" cursor="" n _d _pages=0
  : >"$out"
  dbg_export_reset
  while :; do
    [ "$INTERRUPTED" -eq 1 ] && return 130
    _d="$(dbg_t0)"; id_walk_body "$pit" "$cursor" "$sid" "$smax" "$reqf"; dbg_add DBG_EXP_BODY "$_d"

    _d="$(dbg_t0)"
    es9 POST "$ES9_URL/_search" application/json "$reqf" >/dev/null || {
      [ "$INTERRUPTED" -eq 1 ] && return 130
      warn "$tag id export failed: $(head -c 200 "$RESP")"
      return 1
    }
    dbg_add DBG_EXP_HTTP "$_d"

    _d="$(dbg_t0)"; n="$(jq '.hits.hits | length' "$RESP")"; dbg_add DBG_EXP_COUNT "$_d"
    [ "$n" -eq 0 ] && break

    _d="$(dbg_t0)"; jq -r '.hits.hits[]._id' "$RESP" >>"$out"; dbg_add DBG_EXP_WRITE "$_d"
    _d="$(dbg_t0)"; cursor="$(jq -c '.hits.hits[-1].sort' "$RESP")"; dbg_add DBG_EXP_CURSOR "$_d"

    _pages=$((_pages + 1)); DBG_EXP_IDS=$((DBG_EXP_IDS + n))
    dbg_export_tick "$tag" "$_pages"
  done
  dbg_export_summary "$tag" "$_pages"
  return 0
}

# ES6 6.8 has no PIT, so each slice is its own scroll with its own scroll_id.
# One request file serves the whole slice: every body is consumed by its
# request before the next one overwrites it.
walk_scroll_slice() {
  local sid="$1" smax="$2" out="$3" tag="$4"
  local reqf="$WORK/ids.dst.$sid.request" cur n _d _pages=0
  : >"$out"
  dbg_export_reset
  jq -n --argjson size "$PAGE_SIZE" --argjson i "$sid" --argjson m "$smax" '
      { size: $size, sort: ["_doc"], _source: false, query: {match_all: {}} }
    + (if $m > 1 then { slice: {id: $i, max: $m} } else {} end)' >"$reqf"
  es6 POST "$ES6_URL/$DST_INDEX/_search?scroll=15m" application/json "$reqf" >/dev/null || {
    [ "$INTERRUPTED" -eq 1 ] && return 130
    warn "$tag id export failed: $(head -c 200 "$RESP")"; return 1; }

  while :; do
    [ "$INTERRUPTED" -eq 1 ] && return 130
    _d="$(dbg_t0)"
    n="$(jq '.hits.hits | length' "$RESP")"
    cur="$(jq -r '._scroll_id // ""' "$RESP")"
    dbg_add DBG_EXP_COUNT "$_d"
    [ "$n" -eq 0 ] && break

    _d="$(dbg_t0)"; jq -r '.hits.hits[]._id' "$RESP" >>"$out"; dbg_add DBG_EXP_WRITE "$_d"

    _d="$(dbg_t0)"
    jq -n --arg s "$cur" '{scroll: "15m", scroll_id: $s}' >"$reqf"
    dbg_add DBG_EXP_BODY "$_d"

    _pages=$((_pages + 1)); DBG_EXP_IDS=$((DBG_EXP_IDS + n))
    dbg_export_tick "$tag" "$_pages"

    _d="$(dbg_t0)"
    es6 POST "$ES6_URL/_search/scroll" application/json "$reqf" >/dev/null || {
      [ "$INTERRUPTED" -eq 1 ] && return 130
      # A scroll cannot be resumed from the middle, and a truncated export
      # would understate ES6's id set -- which turns into wrong deletes.
      warn "$tag scroll context lost mid-export"
      return 1
    }
    dbg_add DBG_EXP_HTTP "$_d"
  done
  dbg_export_summary "$tag" "$_pages"
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
  local side="$1" out="$2" pit="" i rc=0 t0
  local pids=()
  t0="$(dbg_t0)"

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
  dbg_export_total "$side" "$t0" "$out" "$SLICE_COUNT"
  return 0
}

phase_reconcile() {
  log "== phase 3: reconcile deletes =="
  dbg_phase_start
  state_load
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || warn "ES6 refresh failed"
  es9 POST "$ES9_URL/$SRC_INDEX/_refresh" >/dev/null || warn "ES9 refresh failed"

  local src_count dst_count
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "count failed"
  src_count="$(jq -r '.count' "$RESP")"
  es6 GET "$ES6_URL/$DST_INDEX/_count" >/dev/null || die "count failed"
  dst_count="$(jq -r '.count' "$RESP")"
  log "   counts before reconcile: $SRC_INDEX=$src_count $DST_INDEX=$dst_count"

  local _dbg
  log "   exporting live ids from ES9/$SRC_INDEX"
  _dbg="$(dbg_t0)"; export_ids src "$STATE_DIR/es9_ids.sorted"; dbg_step "ES9 id export" "$_dbg"
  log "   exporting live ids from ES6/$DST_INDEX"
  _dbg="$(dbg_t0)"; export_ids dst "$STATE_DIR/es6_ids.sorted"; dbg_step "ES6 id export" "$_dbg"

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
  dbg_phase_end "phase 3"
  log "   reconcile done: deleted=$delete_count repaired=$repair_count"
}

reconcile_deletes() {
  local idfile="$1" total="$2" applied=0 part
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
  local idfile="$1" applied=0 part seq n
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
      # jq compares objects structurally, so key order never matters here.
      jq -rn --slurpfile a "$WORK/verify.sample.src.json" --slurpfile b "$RESP" '
          ($a[0].docs | map({key: ._id, value: (if .found then ._source else null end)}) | from_entries) as $A
        | ($b[0].docs | map({key: ._id, value: (if .found then ._source else null end)}) | from_entries) as $B
        | $A | keys[] | select($A[.] != $B[.])
      ' >"$STATE_DIR/verify_sample_diff"
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
  local part applied=0
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
cutover_at     : ${CUTOVER_AT:-?}
effective since: ${EFFECTIVE_SINCE:-?}
delta total    : ${TOTAL_HITS:-?}
seen / synced  : ${SEEN:-0} / ${SYNCED:-0}
dead letters   : ${DL_COUNT:-0}   ($DEADLETTER)
deleted        : ${DELETED:-0}
repaired       : ${REPAIRED:-0}
journal rows   : ${JOURNAL_SEQ:-0}   ($JOURNAL)
EOF
  case "$PHASE" in
    DELTA_SYNC|DELTA_DONE|GATE_PASSED) echo "next           : ./es_rollback.sh resume" ;;
    RECONCILE_DONE)                    echo "next           : ./es_rollback.sh verify" ;;
    DONE)                              echo "next           : flip traffic to ES6, then 'reset'" ;;
  esac
}

cmd_plan() {
  phase_preflight
  jq -n --arg s "$PREFLIGHT_SINCE" '{query: {range: {updated_at: {gt: $s}}}}' >"$WORK/plan.count.json"
  es9 POST "$ES9_URL/$SRC_INDEX/_count" application/json "$WORK/plan.count.json" >/dev/null \
    || die "count failed"
  local delta dst_count; delta="$(jq -r '.count' "$RESP")"
  es6 GET "$ES6_URL/$DST_INDEX/_count" >/dev/null || die "count failed"
  dst_count="$(jq -r '.count' "$RESP")"
  cat <<EOF

plan (nothing written)
  ES9 $SRC_INDEX total      : $PREFLIGHT_SRC_COUNT
  ES6 $DST_INDEX total      : $dst_count
  delta since $PREFLIGHT_SINCE : $delta doc(s) to copy
  net count difference      : $((PREFLIGHT_SRC_COUNT - dst_count))
  journal (approx, gzip)    : $(( (delta * 292) / 1048576 )) MiB
EOF
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
  case "${1:-}" in
    preflight) phase_preflight; log "preflight OK" ;;
    plan)      cmd_plan ;;
    run)       cmd_run ;;
    resume)    cmd_resume ;;
    status)    cmd_status ;;
    verify)    acquire_lock; phase_verify ;;
    undo)      cmd_undo ;;
    reset)     cmd_reset ;;
    *)         usage ;;
  esac
}

# Sourceable for testing: `ES_ROLLBACK_LIB=1 . es_rollback.sh` loads the
# helpers without running a command.
if [ "${ES_ROLLBACK_LIB:-}" != "1" ]; then
  main "$@"
fi
