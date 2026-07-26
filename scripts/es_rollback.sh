#!/usr/bin/env bash
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
#   ./es_rollback.sh reset       restore refresh_interval, drop state
#
# Env vars:
#   ES6_URL / ES9_URL     base URLs               (default http://localhost:9200)
#   SRC_INDEX             ES9 index               (default bench-es9)
#   DST_INDEX             ES6 index               (default bench-es6)
#   ES6_USER / ES6_PW     auth for ES6            (default elastic / $ELASTIC_PW)
#   ES9_USER / ES9_PW     auth for ES9            (default elastic / $ELASTIC_PW)
#   STATE_DIR             state + journal dir     (default ./.rollback-state)
#   PAGE_SIZE             search page size        (default 5000)
#   MAX_BULK_BYTES        bulk chunk cap          (default 5000000)
#   SAFETY_MARGIN         seconds shaved off cutover_at (default 300)
#   MAX_DELETE_RATIO      refuse deletes above this share of ES6 (default 0.10)
#   MAX_RETRY             HTTP retry attempts     (default 6)
#   FREEZE_WAIT           seconds between freeze samples (default 30)
#   SAMPLE_N              docs compared in verify (default 1000)
#   MGET_BATCH            ids per pre-image _mget (default 1000)
#   SINCE                 override cutover_at     (ISO-8601, optional)
#   ALLOW_PARTIAL         "true" lets the gate pass with dead letters
#   ASSUME_YES            "true" skips the delete-ratio confirmation
#
# Exit codes: 0 ok | 1 fatal | 2 finished with dead letters | 130 interrupted
#
set -euo pipefail

ES6_URL="${ES6_URL:-http://localhost:9200}"
ES9_URL="${ES9_URL:-http://localhost:9200}"
SRC_INDEX="${SRC_INDEX:-bench-es9}"
DST_INDEX="${DST_INDEX:-bench-es6}"
ES6_USER="${ES6_USER:-elastic}"
ES6_PW="${ES6_PW:-${ELASTIC_PW:-}}"
ES9_USER="${ES9_USER:-elastic}"
ES9_PW="${ES9_PW:-${ELASTIC_PW:-}}"
STATE_DIR="${STATE_DIR:-./.rollback-state}"
PAGE_SIZE="${PAGE_SIZE:-5000}"
MAX_BULK_BYTES="${MAX_BULK_BYTES:-5000000}"
SAFETY_MARGIN="${SAFETY_MARGIN:-300}"
MAX_DELETE_RATIO="${MAX_DELETE_RATIO:-0.10}"
MAX_RETRY="${MAX_RETRY:-6}"
FREEZE_WAIT="${FREEZE_WAIT:-10}"
SAMPLE_N="${SAMPLE_N:-1000}"
MGET_BATCH="${MGET_BATCH:-1000}"
ALLOW_PARTIAL="${ALLOW_PARTIAL:-false}"
ASSUME_YES="${ASSUME_YES:-false}"
SINCE="${SINCE:-}"

# comm(1) compares with the same collation sort(1) ordered by. Under a UTF-8
# locale that collation ignores punctuation, so two distinct ids can compare
# equal and comm pairs them wrongly -- here that means deleting the wrong
# documents from ES6. C is a strict bytewise total order, and faster.
export LC_ALL=C

mkdir -p "$STATE_DIR"
STATE_DIR="$(cd "$STATE_DIR" && pwd)"
WORK="$STATE_DIR/work"; mkdir -p "$WORK"

STATE="$STATE_DIR/state.env"
JOURNAL="$STATE_DIR/journal.tsv.gz"
DEADLETTER="$STATE_DIR/deadletter.ndjson"
LOG="$STATE_DIR/run.log"
LOCK="$STATE_DIR/lock"
PIT_FILE="$STATE_DIR/pit_id.txt"
SA_FILE="$STATE_DIR/search_after.json"
RESP="$WORK/resp.json"

INTERRUPTED=0

log()  { printf '%s %s\n' "$(date -u +%H:%M:%S)" "$*" | tee -a "$LOG"; }
warn() { printf '%s WARN %s\n' "$(date -u +%H:%M:%S)" "$*" | tee -a "$LOG" >&2; }
die()  { printf '%s FATAL %s\n' "$(date -u +%H:%M:%S)" "$*" | tee -a "$LOG" >&2; exit 1; }

# ------------------------------------------------------------------- state --
#
# Flat key=value, sourceable by bash. Anything not shell-safe (search_after
# arrays, PIT ids) lives in its own file. Written temp+mv, so a crash can
# never leave a half-written state file behind.

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
#
# Status on stdout, body in $RESP. Deliberately not curl -f: a _bulk that
# returns 200 with per-item errors still has to be read, and a 4xx body
# carries the reason worth showing.

http_req() {
  local user="$1" pw="$2" method="$3" url="$4" ctype="${5:-}" datafile="${6:-}"
  local args=(-sS -u "$user:$pw" -X "$method" "$url" -o "$RESP"
              -w '%{http_code}' --connect-timeout 10 --max-time 600)
  [ -n "$ctype" ] && args+=(-H "Content-Type: $ctype")
  [ -n "$datafile" ] && args+=(--data-binary "@$datafile")
  curl "${args[@]}" 2>>"$LOG" || echo "000"
}

backoff() { awk -v n="$1" 'BEGIN{srand();s=(2^n)*(0.5+rand()/2);if(s>60)s=60;print s}'; }

http_retry() {
  local attempt=0 code
  while :; do
    code="$(http_req "$@")"
    case "$code" in
      2*) printf '%s' "$code"; return 0 ;;
      429|502|503|504|000)
        [ "$INTERRUPTED" -eq 1 ] && { printf '%s' "$code"; return 1; }
        attempt=$((attempt + 1))
        if [ "$attempt" -ge "$MAX_RETRY" ]; then printf '%s' "$code"; return 1; fi
        warn "HTTP $code on $4 -- retry $attempt/$MAX_RETRY"
        sleep "$(backoff "$attempt")" ;;
      *) printf '%s' "$code"; return 1 ;;
    esac
  done
}

es6() { http_retry "$ES6_USER" "$ES6_PW" "$@"; }
es9() { http_retry "$ES9_USER" "$ES9_PW" "$@"; }

# ------------------------------------------------------------- json shaping --

# Search body. Built by jq so PIT ids and search_after arrays are never
# string-interpolated into shell-quoted JSON.
build_body() {
  local mode="$1" pit="$2" since="$3" out="$4" sa_src="$5"
  local sa="null"
  [ -s "$sa_src" ] && sa="$(cat "$sa_src")"
  jq -n --arg mode "$mode" --arg pit "$pit" --arg since "$since" \
        --argjson size "$PAGE_SIZE" --argjson sa "$sa" '
      (if $mode == "delta"
       then { query: {range: {updated_at: {gt: $since}}},
              sort: [{updated_at: "asc"}, {_shard_doc: "asc"}] }
       else { query: {match_all: {}}, sort: [{_shard_doc: "asc"}], _source: false }
       end)
    + { size: $size }
    + (if $pit == "" then {} else { pit: {id: $pit, keep_alive: "15m"} } end)
    + (if $sa == null then { track_total_hits: true } else { search_after: $sa } end)
  ' >"$out"
}

# One ES9 delta page -> id list, bulk chunks capped at MAX_BULK_BYTES, and a
# staged next cursor. Prints "<hits> <last_updated_at>".
split_page() {
  local resp="$1" outdir="$2"
  rm -f "$outdir"/bulk.*.ndjson
  jq -r '.hits.hits[]._id' "$resp" >"$outdir/page.ids"
  # Custom routing has to travel with the document or it lands on a
  # different shard on ES6 and later routed lookups miss it.
  jq -c '.hits.hits[]
         | ({index: ({_id: ._id} + (if ._routing then {routing: ._routing} else {} end))}),
           ._source' "$resp" >"$outdir/page.ndjson"
  jq -c '.hits.hits[-1].sort // empty' "$resp" >"$WORK/next_sa.json"
  # Chunk on byte size, two lines at a time, so an action is never separated
  # from the source line it belongs to.
  awk -v cap="$MAX_BULK_BYTES" -v pre="$outdir/bulk." '
    { a = $0; if ((getline b) <= 0) b = "{}"
      n = length(a) + length(b) + 2
      if (sz > 0 && sz + n > cap) { close(f); i++; sz = 0 }
      f = sprintf("%s%04d.ndjson", pre, i + 0)
      print a >> f; print b >> f; sz += n }
  ' "$outdir/page.ndjson"
  printf '%s %s\n' \
    "$(jq '.hits.hits | length' "$resp")" \
    "$(jq -r '.hits.hits[-1]._source.updated_at // ""' "$resp")"
}

# ES6 _mget response -> journal rows "seq \t id \t found \t source".
# Absent documents (created on ES9 during the window) get found=0; undoing
# one means deleting it, not restoring it.
mget_to_journal() {
  jq -r --argjson seq "$2" --arg op "$3" '
    .docs | to_entries[]
    | "\($seq + .key + 1)\t\(.value._id)\t\($op)\t\(if .value.found then 1 else 0 end)\t\(if .value.found then (.value._source|tojson) else "{}" end)"
  ' "$1"
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
      "$sent" >"$WORK/pairs.tsv"
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
  ' "$resp" >"$WORK/verdict.tsv"
  # action/source are already JSON text, so they drop into the dead letter
  # record as values without any re-escaping.
  awk -F '\t' -v retry="$retry_out" -v dl="$dl" '
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
  ' "$WORK/pairs.tsv" "$WORK/verdict.tsv"
}

# id file -> {"ids":[...]} for _mget, or a delete bulk body.
ids_to_body() {
  local infile="$1" out="$2" kind="$3"
  if [ "$kind" = "mget" ]; then
    jq -R -s -c 'split("\n") | map(rtrimstr("\r")) | map(select(length > 0)) | {ids: .}' \
      "$infile" >"$out"
  else
    jq -R -c 'rtrimstr("\r") | select(length > 0) | {delete: {_id: .}}' "$infile" >"$out"
  fi
}

# ES9 _mget response -> ES6 index bulk body (repairs ES9-only ids).
mget_to_bulk() {
  jq -c '.docs[] | select(.found)
         | ({index: ({_id: ._id} + (if ._routing then {routing: ._routing} else {} end))}),
           ._source' "$1" >"$2"
}

# --------------------------------------------------------------------- PIT --

pit_open() {
  es9 POST "$1/$2/_pit?keep_alive=15m" >/dev/null || return 1
  jq -r '.id' "$RESP"
}

pit_close() {
  [ -n "$2" ] || return 0
  jq -n --arg id "$2" '{id: $id}' >"$WORK/pit.json"
  es9 DELETE "$1/_pit" application/json "$WORK/pit.json" >/dev/null 2>&1 || true
  return 0
}

# ------------------------------------------------------------------ bulk io --

bulk_send() {
  local file="$1" attempt=0
  BULK_OK=0; BULK_FATAL=0
  cp "$file" "$WORK/send.ndjson"
  while :; do
    local code counts ok retry fatal
    code="$(es6 POST "$ES6_URL/$DST_INDEX/_doc/_bulk" application/x-ndjson "$WORK/send.ndjson")" || {
      warn "bulk request failed with HTTP $code"
      return 1
    }
    counts="$(parse_bulk "$RESP" "$WORK/send.ndjson" "$WORK/retry.ndjson" "$DEADLETTER")"
    ok="$(echo "$counts" | awk '{print $1}')"
    retry="$(echo "$counts" | awk '{print $2}')"
    fatal="$(echo "$counts" | awk '{print $3}')"
    BULK_OK=$((BULK_OK + ok)); BULK_FATAL=$((BULK_FATAL + fatal))
    [ "$retry" -eq 0 ] && return 0
    attempt=$((attempt + 1))
    if [ "$attempt" -ge "$MAX_RETRY" ]; then
      warn "$retry item(s) still rejected after $MAX_RETRY attempts -- dead-lettering"
      cat "$WORK/retry.ndjson" >>"$DEADLETTER"
      BULK_FATAL=$((BULK_FATAL + retry))
      return 0
    fi
    warn "$retry item(s) rejected (transient) -- retry $attempt/$MAX_RETRY"
    sleep "$(backoff "$attempt")"
    mv "$WORK/retry.ndjson" "$WORK/send.ndjson"
  done
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
  # Batched independently of PAGE_SIZE. A _mget answers with the full _source
  # of every id it was asked for, so one request per page would pull
  # PAGE_SIZE * document size back at once -- at PAGE_SIZE=100000 and ~1 KB
  # documents that is a 110 MB response for jq to parse in one piece. The
  # write path is already capped by MAX_BULK_BYTES; this keeps the read path
  # flat the same way.
  #
  # JOURNAL_SEQ is committed after every batch, so a crash midway can never
  # hand the same seq to two different pre-images.
  rm -f "$WORK"/pre.*
  split -l "$MGET_BATCH" -a 5 "$idfile" "$WORK/pre."
  for part in "$WORK"/pre.*; do
    [ -s "$part" ] || continue
    ids_to_body "$part" "$WORK/mget.json" mget
    es6 POST "$ES6_URL/$DST_INDEX/_doc/_mget" application/json "$WORK/mget.json" >/dev/null \
      || { warn "pre-image _mget failed -- refusing to write without a journal"; return 1; }
    state_load
    seq="${JOURNAL_SEQ:-0}"
    mget_to_journal "$RESP" "$seq" "$op" | gzip -1 >>"$JOURNAL"
    n="$(wc -l <"$part" | tr -d ' ')"
    state_set JOURNAL_SEQ "$((seq + n))"
  done
  rm -f "$WORK"/pre.*
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

  # The marker came from `date -u` on the ES9 VM; document timestamps came
  # from the application. Those are different clocks. Rewinding the lower
  # bound costs a few redundant overwrites -- harmless, the source is frozen
  # and writes are whole-document replaces -- and removes the skew direction
  # that would otherwise drop documents silently.
  local effective
  effective="$(jq -rn --arg t "$cutover" --argjson m "$SAFETY_MARGIN" '
      ($t | fromdateiso8601) as $e
      | if $e > now then error("future") else ($e - $m | todateiso8601) end
    ' 2>/dev/null)" \
    || die "cutover_at is unusable (not ISO-8601, or in the future): $cutover"
  log "   effective lower bound (-${SAFETY_MARGIN}s): $effective"

  # Every correctness argument below assumes ES9 is standing still: the
  # delta window is closed and the phase 3 diff compares two static sets.
  # Sampling twice is cheap and catches writers nobody remembered to stop.
  local c1 c2 m1 m2
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "count failed"
  c1="$(jq -r '.count' "$RESP")"; m1="$(freeze_max_updated)"
  log "   freeze sample 1: count=$c1 max(updated_at)=$m1 -- waiting ${FREEZE_WAIT}s"
  sleep "$FREEZE_WAIT"
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "count failed"
  c2="$(jq -r '.count' "$RESP")"; m2="$(freeze_max_updated)"
  if [ "$c1" != "$c2" ] || [ "$m1" != "$m2" ]; then
    die "ES9 is still taking writes (count $c1->$c2, max updated_at $m1->$m2).
Stop the writers first, or both the delta window and the id diff are
computed against a moving target."
  fi
  log "   freeze verified: ES9 static over ${FREEZE_WAIT}s"

  PF_CUTOVER="$cutover"; PF_EFFECTIVE="$effective"; PF_SRC_COUNT="$c2"
}

freeze_max_updated() {
  jq -n '{size: 0, aggs: {m: {max: {field: "updated_at"}}}}' >"$WORK/agg.json"
  es9 POST "$ES9_URL/$SRC_INDEX/_search" application/json "$WORK/agg.json" >/dev/null \
    || die "max(updated_at) aggregation failed on $SRC_INDEX"
  jq -r '.aggregations.m.value_as_string // (.aggregations.m.value | tostring)' "$RESP"
}

# ------------------------------------------------------------ refresh state --
#
# bench-es6 ships with refresh_interval: -1 (mapping-es6.json). Left alone,
# nothing written in phase 1 is visible to the phase 3 id export, and the
# diff would read freshly-synced documents as missing from ES6.

refresh_interval_capture() {
  es6 GET "$ES6_URL/$DST_INDEX/_settings" >/dev/null || die "cannot read settings"
  state_set ORIG_REFRESH "$(jq -r '.[].settings.index.refresh_interval // "null"' "$RESP")"
  jq -n '{index: {refresh_interval: "30s"}}' >"$WORK/ri.json"
  es6 PUT "$ES6_URL/$DST_INDEX/_settings" application/json "$WORK/ri.json" >/dev/null \
    || die "cannot set refresh_interval on $DST_INDEX"
  log "   refresh_interval: $ORIG_REFRESH -> 30s (restored by 'reset')"
}

refresh_interval_restore() {
  state_load
  local orig="${ORIG_REFRESH:-}"
  [ -n "$orig" ] || return 0
  if [ "$orig" = "null" ]; then
    jq -n '{index: {refresh_interval: null}}' >"$WORK/ri.json"
  else
    jq -n --arg v "$orig" '{index: {refresh_interval: $v}}' >"$WORK/ri.json"
  fi
  es6 PUT "$ES6_URL/$DST_INDEX/_settings" application/json "$WORK/ri.json" >/dev/null || true
  log "   refresh_interval restored to $orig"
  [ "$orig" = "-1" ] && warn "original was -1; ES6 will not refresh on its own"
  return 0
}

# ------------------------------------------------------------------ phase 1 --

phase_delta() {
  log "== phase 1: delta sync $SRC_INDEX -> $DST_INDEX =="
  state_load
  local since="$EFFECTIVE_SINCE" pit=""
  local synced="${SYNCED:-0}" seen="${SEEN:-0}" dl="${DL_COUNT:-0}"
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
      state_set SYNCED "$synced"; state_set SEEN "$seen"; state_set DL_COUNT "$dl"
      exit 130
    fi

    build_body delta "$pit" "$since" "$WORK/body.json" "$SA_FILE" "$range_op"
    if ! es9 POST "$ES9_URL/_search" application/json "$WORK/body.json" >/dev/null; then
      # An expired PIT (or a node restart) shows up as search_context_missing.
      # ES9 is frozen, so reopening and restarting from the last committed
      # watermark is exactly right: the overlap rewrites identical content.
      if grep -q 'search_context_missing\|No search context found' "$RESP" 2>/dev/null; then
        restarts=$((restarts + 1))
        [ "$restarts" -gt 10 ] && die "PIT expired $restarts times without finishing; raise keep_alive or reduce PAGE_SIZE"
        warn "PIT expired -- reopening, resuming from watermark ${WATERMARK:-$since} (inclusive)"
        pit="$(pit_open "$ES9_URL" "$SRC_INDEX")" || die "cannot reopen PIT"
        printf '%s' "$pit" >"$PIT_FILE"
        state_load; since="${WATERMARK:-$since}"; range_op="gte"; : >"$SA_FILE"
        continue
      fi
      die "delta search failed: $(head -c 400 "$RESP")"
    fi

    if [ "$seen" -eq 0 ] && [ ! -s "$SA_FILE" ]; then
      state_set TOTAL_HITS "$(jq -r '.hits.total.value // .hits.total' "$RESP")"
      log "   delta window contains $TOTAL_HITS doc(s)"
    fi

    local out hits last_ts
    out="$(split_page "$RESP" "$WORK")"
    hits="${out%% *}"; last_ts="${out#* }"
    [ "$hits" -eq 0 ] && break

    journal_preimage "$WORK/page.ids" delta || die "cannot journal pre-images -- aborting before any write"

    local chunk
    for chunk in "$WORK"/bulk.*.ndjson; do
      [ -s "$chunk" ] || continue
      bulk_send "$chunk" || {
        state_set SYNCED "$synced"; state_set SEEN "$seen"; state_set DL_COUNT "$dl"
        die "bulk write failed -- state checkpointed, run 'resume' once ES6 is healthy"
      }
      synced=$((synced + BULK_OK)); dl=$((dl + BULK_FATAL))
    done

    seen=$((seen + hits))
    [ -n "$last_ts" ] && state_set WATERMARK "$last_ts"
    state_set SYNCED "$synced"; state_set SEEN "$seen"; state_set DL_COUNT "$dl"
    # Cursor is promoted only after the page is committed and counted. A
    # crash here re-reads the page on resume, which is idempotent; promoting
    # it earlier would let a crash skip the page entirely.
    mv -f "$WORK/next_sa.json" "$SA_FILE"
    log "   page: $hits docs (seen=$seen synced=$synced deadletter=$dl)"
  done

  pit_close "$ES9_URL" "$pit"; rm -f "$PIT_FILE" "$SA_FILE"
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || warn "refresh failed"
  log "   delta sync finished: seen=$seen synced=$synced deadletter=$dl"
  state_set PHASE DELTA_DONE
}

# ------------------------------------------------------------------ phase 2 --

phase_gate() {
  log "== phase 2: delta gate =="
  state_load
  local total="${TOTAL_HITS:-0}" seen="${SEEN:-0}" dl="${DL_COUNT:-0}"

  # seen can exceed total after a PIT expiry forced a watermark restart --
  # that overlap is re-read, not new work. It must never fall short.
  if [ "$seen" -lt "$total" ]; then
    die "gate FAILED: delta window had $total doc(s) but only $seen were read.
Deletes are NOT safe to reconcile -- the id diff would read the missing
documents as deleted on ES9. Run 'resume' first."
  fi
  if [ "$dl" -gt 0 ] && [ "$ALLOW_PARTIAL" != "true" ]; then
    die "gate FAILED: $dl doc(s) in $DEADLETTER were rejected by ES6.
Fix the cause and resume. ALLOW_PARTIAL=true overrides, but only if you
accept that ES6 will be missing those documents and that the delete
reconciliation may then remove them."
  fi
  [ "$dl" -gt 0 ] && warn "gate passed with $dl dead-lettered doc(s) (ALLOW_PARTIAL)"
  log "   gate passed: seen=$seen >= total=$total, deadletter=$dl"
  state_set PHASE GATE_PASSED
}

# ------------------------------------------------------------------ phase 3 --
#
# Walk every live _id into a file. ES9 uses a PIT; ES6 6.8 has no PIT so it
# uses scroll. Both are consistent snapshots -- plain search_after on _doc is
# not, because _doc ordering shifts as segments merge, which silently skips
# or duplicates ids.

export_ids_es9() {
  local out="$1" pit n
  : >"$out"; : >"$SA_FILE"
  pit="$(pit_open "$ES9_URL" "$SRC_INDEX")" || die "cannot open PIT for id export"
  while :; do
    [ "$INTERRUPTED" -eq 1 ] && { pit_close "$ES9_URL" "$pit"; exit 130; }
    build_body ids "$pit" "" "$WORK/body.json" "$SA_FILE"
    es9 POST "$ES9_URL/_search" application/json "$WORK/body.json" >/dev/null \
      || die "ES9 id export failed: $(head -c 300 "$RESP")"
    n="$(jq '.hits.hits | length' "$RESP")"
    [ "$n" -eq 0 ] && break
    jq -r '.hits.hits[]._id' "$RESP" >>"$out"
    jq -c '.hits.hits[-1].sort' "$RESP" >"$SA_FILE"
  done
  pit_close "$ES9_URL" "$pit"; rm -f "$SA_FILE"
}

export_ids_es6() {
  local out="$1" sid n
  : >"$out"
  jq -n --argjson size "$PAGE_SIZE" \
    '{size: $size, sort: ["_doc"], _source: false, query: {match_all: {}}}' >"$WORK/body.json"
  es6 POST "$ES6_URL/$DST_INDEX/_search?scroll=15m" application/json "$WORK/body.json" >/dev/null \
    || die "ES6 id export failed: $(head -c 300 "$RESP")"
  while :; do
    [ "$INTERRUPTED" -eq 1 ] && exit 130
    n="$(jq '.hits.hits | length' "$RESP")"
    sid="$(jq -r '._scroll_id // ""' "$RESP")"
    [ "$n" -eq 0 ] && break
    jq -r '.hits.hits[]._id' "$RESP" >>"$out"
    jq -n --arg s "$sid" '{scroll: "15m", scroll_id: $s}' >"$WORK/scroll.json"
    es6 POST "$ES6_URL/_search/scroll" application/json "$WORK/scroll.json" >/dev/null || {
      # A scroll cannot be resumed from the middle, and a truncated export
      # would understate ES6's id set -- which turns into wrong deletes.
      die "ES6 scroll context lost mid-export. Re-run 'resume' to restart the id export."
    }
  done
  jq -n --arg s "$sid" '{scroll_id: [$s]}' >"$WORK/scroll.json"
  es6 DELETE "$ES6_URL/_search/scroll" application/json "$WORK/scroll.json" >/dev/null 2>&1 || true
  return 0
}

phase_reconcile() {
  log "== phase 3: reconcile deletes =="
  state_load
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || warn "ES6 refresh failed"
  es9 POST "$ES9_URL/$SRC_INDEX/_refresh" >/dev/null || warn "ES9 refresh failed"

  local c9 c6
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "count failed"; c9="$(jq -r '.count' "$RESP")"
  es6 GET "$ES6_URL/$DST_INDEX/_count" >/dev/null || die "count failed"; c6="$(jq -r '.count' "$RESP")"
  log "   counts before reconcile: $SRC_INDEX=$c9 $DST_INDEX=$c6"

  log "   exporting live ids from ES9/$SRC_INDEX"
  export_ids_es9 "$WORK/es9_ids.raw"
  log "   exporting live ids from ES6/$DST_INDEX"
  export_ids_es6 "$WORK/es6_ids.raw"

  sort -u -T "$WORK" -S 25% -o "$STATE_DIR/es9_ids.sorted" "$WORK/es9_ids.raw"
  sort -u -T "$WORK" -S 25% -o "$STATE_DIR/es6_ids.sorted" "$WORK/es6_ids.raw"
  local n9 n6
  n9="$(wc -l <"$STATE_DIR/es9_ids.sorted" | tr -d ' ')"
  n6="$(wc -l <"$STATE_DIR/es6_ids.sorted" | tr -d ' ')"

  # Without this, an export truncated by a dropped connection looks exactly
  # like "ES9 no longer has these documents", and the diff deletes most of ES6.
  [ "$n9" = "$c9" ] || die "ES9 id export incomplete: $n9 exported vs $c9 counted. Refusing to diff."
  [ "$n6" = "$c6" ] || die "ES6 id export incomplete: $n6 exported vs $c6 counted. Refusing to diff."
  log "   id sets complete: ES9=$n9 ES6=$n6"

  # Both directions, always. Equal counts do not imply equal id sets: N
  # creates and N deletes on ES9 leave the totals matching while both differ.
  comm -23 "$STATE_DIR/es6_ids.sorted" "$STATE_DIR/es9_ids.sorted" >"$STATE_DIR/to_delete"
  comm -13 "$STATE_DIR/es6_ids.sorted" "$STATE_DIR/es9_ids.sorted" >"$STATE_DIR/to_repair"
  local ndel nrep
  ndel="$(wc -l <"$STATE_DIR/to_delete" | tr -d ' ')"
  nrep="$(wc -l <"$STATE_DIR/to_repair" | tr -d ' ')"
  log "   to delete from ES6: $ndel    to repair into ES6: $nrep"

  if [ "$ndel" -gt 0 ]; then
    local over
    over="$(awk -v d="$ndel" -v t="$n6" -v r="$MAX_DELETE_RATIO" \
      'BEGIN{print (t > 0 && d/t > r) ? "yes" : "no"}')"
    if [ "$over" = "yes" ] && [ "$ASSUME_YES" != "true" ]; then
      warn "sample of ids to delete:"; head -5 "$STATE_DIR/to_delete" >&2
      die "$ndel deletes is more than $MAX_DELETE_RATIO of ES6's $n6 documents.
Stopping. Review $STATE_DIR/to_delete, then re-run with ASSUME_YES=true if
this really is what happened on ES9."
    fi
    reconcile_delete_ids "$STATE_DIR/to_delete" "$ndel"
  fi

  # ES9-only ids mean the delta missed a create -- a write that skipped
  # updated_at, or a doc dead-lettered earlier. Repairing beats reporting:
  # ES6 has to have these documents.
  if [ "$nrep" -gt 0 ]; then
    warn "$nrep doc(s) on ES9 are missing from ES6 -- the delta missed them; repairing"
    reconcile_repair_ids "$STATE_DIR/to_repair"
  fi

  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || warn "refresh failed"
  state_set DELETED "$ndel"; state_set REPAIRED "$nrep"
  state_set PHASE RECONCILE_DONE
  log "   reconcile done: deleted=$ndel repaired=$nrep"
}

reconcile_delete_ids() {
  local idfile="$1" total="$2" done_n=0 part
  log "   deleting $total doc(s) from ES6 (journaling pre-images first)"
  rm -f "$WORK"/del.*
  split -l 1000 -a 5 "$idfile" "$WORK/del."
  for part in "$WORK"/del.*; do
    [ -s "$part" ] || continue
    [ "$INTERRUPTED" -eq 1 ] && { log "   interrupted after $done_n deletes"; exit 130; }
    # Deletion is the only irreversible step, so its pre-image is journaled
    # unconditionally; undo restores from it.
    journal_preimage "$part" delete || die "cannot journal pre-images before delete -- aborting"
    ids_to_body "$part" "$WORK/del.ndjson" delete
    bulk_send "$WORK/del.ndjson" || die "bulk delete failed after $done_n"
    done_n=$((done_n + BULK_OK))
  done
  rm -f "$WORK"/del.*
  log "   deleted $done_n doc(s)"
}

reconcile_repair_ids() {
  local idfile="$1" done_n=0 part seq n
  rm -f "$WORK"/rep.*
  split -l 1000 -a 5 "$idfile" "$WORK/rep."
  for part in "$WORK"/rep.*; do
    [ -s "$part" ] || continue
    [ "$INTERRUPTED" -eq 1 ] && exit 130
    ids_to_body "$part" "$WORK/mget9.json" mget
    es9 POST "$ES9_URL/$SRC_INDEX/_mget" application/json "$WORK/mget9.json" >/dev/null \
      || die "repair _mget from ES9 failed"
    mget_to_bulk "$RESP" "$WORK/rep.ndjson"
    # These ids are absent from ES6 by construction, so the pre-image is
    # "absent" -- journal it directly, no _mget needed. Undo deletes them.
    state_load; seq="${JOURNAL_SEQ:-0}"; n="$(wc -l <"$part" | tr -d ' ')"
    awk -v s="$seq" '{printf "%d\t%s\trepair\t0\t{}\n", s + NR, $0}' "$part" | gzip -1 >>"$JOURNAL"
    state_set JOURNAL_SEQ "$((seq + n))"
    bulk_send "$WORK/rep.ndjson" || die "repair bulk failed after $done_n"
    done_n=$((done_n + BULK_OK))
  done
  rm -f "$WORK"/rep.*
  log "   repaired $done_n doc(s)"
}

# ------------------------------------------------------------------ phase 4 --

phase_verify() {
  log "== phase 4: verify =="
  state_load
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || true
  es9 POST "$ES9_URL/$SRC_INDEX/_refresh" >/dev/null || true

  local c9 c6 rc=0
  es9 GET "$ES9_URL/$SRC_INDEX/_count" >/dev/null || die "count failed"; c9="$(jq -r '.count' "$RESP")"
  es6 GET "$ES6_URL/$DST_INDEX/_count" >/dev/null || die "count failed"; c6="$(jq -r '.count' "$RESP")"
  log "   counts: $SRC_INDEX=$c9 $DST_INDEX=$c6"
  [ "$c9" = "$c6" ] || { warn "count mismatch: $c9 vs $c6"; rc=1; }

  # The expected post-reconcile ES6 id set is (es6 - to_delete) + to_repair,
  # and all three files are already on disk, so checking it is free.
  if [ -s "$STATE_DIR/es9_ids.sorted" ] && [ -s "$STATE_DIR/es6_ids.sorted" ]; then
    comm -23 "$STATE_DIR/es6_ids.sorted" "$STATE_DIR/to_delete" >"$WORK/kept"
    sort -u -T "$WORK" -o "$WORK/expected_ids" "$WORK/kept" "$STATE_DIR/to_repair"
    if cmp -s "$WORK/expected_ids" "$STATE_DIR/es9_ids.sorted"; then
      log "   expected ES6 id set matches ES9 exactly"
    else
      warn "expected id set differs from ES9 -- re-exporting ES6 ids to locate it"
      export_ids_es6 "$WORK/es6_now.raw"
      sort -u -T "$WORK" -o "$WORK/es6_now.sorted" "$WORK/es6_now.raw"
      comm -23 "$WORK/es6_now.sorted" "$STATE_DIR/es9_ids.sorted" >"$STATE_DIR/verify_extra"
      comm -13 "$WORK/es6_now.sorted" "$STATE_DIR/es9_ids.sorted" >"$STATE_DIR/verify_missing"
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
      | head -n "$SAMPLE_N" >"$WORK/sample.ids"
    if [ -s "$WORK/sample.ids" ]; then
      ids_to_body "$WORK/sample.ids" "$WORK/s.json" mget
      es9 POST "$ES9_URL/$SRC_INDEX/_mget" application/json "$WORK/s.json" >/dev/null \
        || die "sample _mget on ES9 failed"
      cp "$RESP" "$WORK/s9.resp"
      es6 POST "$ES6_URL/$DST_INDEX/_doc/_mget" application/json "$WORK/s.json" >/dev/null \
        || die "sample _mget on ES6 failed"
      cp "$RESP" "$WORK/s6.resp"
      # jq compares objects structurally, so key order never matters here.
      jq -rn --slurpfile a "$WORK/s9.resp" --slurpfile b "$WORK/s6.resp" '
          ($a[0].docs | map({key: ._id, value: (if .found then ._source else null end)}) | from_entries) as $A
        | ($b[0].docs | map({key: ._id, value: (if .found then ._source else null end)}) | from_entries) as $B
        | $A | keys[] | select($A[.] != $B[.])
      ' >"$STATE_DIR/verify_sample_diff"
      local mism total
      mism="$(wc -l <"$STATE_DIR/verify_sample_diff" | tr -d ' ')"
      total="$(wc -l <"$WORK/sample.ids" | tr -d ' ')"
      if [ "$mism" -gt 0 ]; then
        warn "$mism/$total sampled doc(s) differ -> $STATE_DIR/verify_sample_diff"; rc=1
      else
        log "   content sample: $total doc(s) identical"
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
    | awk -F '\t' '!seen[$2]++' >"$WORK/undo.tsv"
  log "   $(wc -l <"$WORK/undo.tsv" | tr -d ' ') distinct doc(s) to restore"

  rm -f "$WORK"/undopart.*
  split -l 1000 -a 5 "$WORK/undo.tsv" "$WORK/undopart."
  local part total=0
  for part in "$WORK"/undopart.*; do
    [ -s "$part" ] || continue
    # Row layout is seq/id/op/found/source. `op` is audit metadata; undo keys
    # off `found`: 1 means there is a pre-image to put back, 0 means the
    # document did not exist on ES6 before the run, so undoing it is a delete.
    jq -Rc 'split("\t")
            | if .[3] == "1" then ({index: {_id: .[1]}}), (.[4] | fromjson)
              else ({delete: {_id: .[1]}}) end' "$part" >"$WORK/undo.ndjson"
    bulk_send "$WORK/undo.ndjson" || die "undo bulk failed after $total"
    total=$((total + BULK_OK))
  done
  rm -f "$WORK"/undopart.*
  es6 POST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null || true
  log "   undo applied to $total doc(s); $DST_INDEX is back to its pre-run state"
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
  rm -f "$SA_FILE" "$PIT_FILE"; : >"$DEADLETTER"
  phase_preflight
  state_set RUN_ID "$(date -u +%Y%m%dT%H%M%SZ)"
  state_set CUTOVER_AT "$PF_CUTOVER"
  state_set EFFECTIVE_SINCE "$PF_EFFECTIVE"
  state_set SRC_INDEX_S "$SRC_INDEX"; state_set DST_INDEX_S "$DST_INDEX"
  state_set SYNCED 0; state_set SEEN 0; state_set DL_COUNT 0; state_set JOURNAL_SEQ 0
  state_set PHASE DELTA_SYNC
  refresh_interval_capture
  pipeline
}

cmd_resume() {
  state_load
  [ -n "${PHASE:-}" ] || die "no run to resume in $STATE_DIR"
  [ "$PHASE" = "DONE" ] && { log "run already complete"; return 0; }
  acquire_lock
  # Resuming against a different source than the run started on would
  # invalidate every checkpoint.
  [ "${SRC_INDEX_S:-$SRC_INDEX}" = "$SRC_INDEX" ] || die "state belongs to SRC_INDEX=${SRC_INDEX_S}"
  [ "${DST_INDEX_S:-$DST_INDEX}" = "$DST_INDEX" ] || die "state belongs to DST_INDEX=${DST_INDEX_S}"
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
  jq -n --arg s "$PF_EFFECTIVE" '{query: {range: {updated_at: {gt: $s}}}}' >"$WORK/cq.json"
  es9 POST "$ES9_URL/$SRC_INDEX/_count" application/json "$WORK/cq.json" >/dev/null || die "count failed"
  local delta c6; delta="$(jq -r '.count' "$RESP")"
  es6 GET "$ES6_URL/$DST_INDEX/_count" >/dev/null || die "count failed"; c6="$(jq -r '.count' "$RESP")"
  cat <<EOF

plan (nothing written)
  ES9 $SRC_INDEX total      : $PF_SRC_COUNT
  ES6 $DST_INDEX total      : $c6
  delta since $PF_EFFECTIVE : $delta doc(s) to copy
  net count difference      : $((PF_SRC_COUNT - c6))
  journal (approx, gzip)    : $(( (delta * 292) / 1048576 )) MiB
EOF
}

cmd_reset() {
  state_load
  acquire_lock
  refresh_interval_restore
  rm -f "$STATE" "$SA_FILE" "$PIT_FILE"
  rm -rf "$WORK"
  if [ -s "$JOURNAL" ]; then
    warn "journal kept at $JOURNAL -- remove it by hand once you are sure no undo is needed"
  else
    rm -f "$JOURNAL" "$DEADLETTER"
  fi
  log "state cleared"
}

usage() { sed -n '3,62p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

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
