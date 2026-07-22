#!/usr/bin/env bash
#
# Trigger and monitor a remote reindex from ES6 (source) into ES9 (destination).
# ES9 pulls the data; ES6 only serves reads. Run this ON the es9 VM, or from your
# laptop if firewall rule es-allow-es-admin is enabled.
#
# NOTE: reindex-from-remote does NOT support slicing (slices=auto is rejected and
# manual source.slice is silently ignored, elastic/elasticsearch#136269), so this
# is a single sequential reindex request.
#
# Env vars:
#   ES9_URL      destination base URL         (default http://localhost:9200)
#   ES6_REMOTE   source remote host for ES9   (default http://10.146.0.10:9200)
#   SRC_INDEX    source index                 (default bench-es6)
#   DST_INDEX    destination index            (default bench-es9)
#   SIZE         scroll batch size            (default 5000)
#   MAPPING      dest mapping file            (default ./mapping-es9.json)
#   ES9_USER/ES9_PW   auth for the ES9 API     (default elastic / $ELASTIC_PW)
#   ES6_USER/ES6_PW   auth ES9 uses to pull ES6 (default elastic / $ELASTIC_PW)
#
set -euo pipefail

ES9_URL="${ES9_URL:-http://localhost:9200}"
ES6_REMOTE="${ES6_REMOTE:-http://10.146.0.10:9200}"
SRC_INDEX="${SRC_INDEX:-bench-es6}"
DST_INDEX="${DST_INDEX:-bench-es9}"
SIZE="${SIZE:-5000}"
ES9_USER="${ES9_USER:-elastic}"
ES9_PW="${ES9_PW:-${ELASTIC_PW:-}}"
ES6_USER="${ES6_USER:-elastic}"
ES6_PW="${ES6_PW:-${ELASTIC_PW:-}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAPPING="${MAPPING:-$SCRIPT_DIR/mapping-es9.json}"

# curl helpers carrying basic-auth for each cluster.
c9() { curl -fsS -u "$ES9_USER:$ES9_PW" "$@"; }   # -> ES9
c6() { curl -fsS -u "$ES6_USER:$ES6_PW" "$@"; }   # -> ES6 (for count verify)

jqfield() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }

echo ">> creating destination index $DST_INDEX on $ES9_URL"
c9 -XDELETE "$ES9_URL/$DST_INDEX" >/dev/null 2>&1 || true
c9 -XPUT "$ES9_URL/$DST_INDEX" -H 'Content-Type: application/json' \
  --data-binary "@$MAPPING" | jqfield "['acknowledged']" >/dev/null
echo "   created."

read -r -d '' BODY <<JSON || true
{
  "source": {
    "remote": {
      "host": "$ES6_REMOTE",
      "username": "$ES6_USER",
      "password": "$ES6_PW",
      "socket_timeout": "120s",
      "connect_timeout": "30s"
    },
    "index": "$SRC_INDEX",
    "size": $SIZE
  },
  "dest": { "index": "$DST_INDEX" }
}
JSON

echo ">> triggering remote reindex (size=$SIZE) from $ES6_REMOTE/$SRC_INDEX"
START=$(date +%s)
RESP="$(c9 -XPOST "$ES9_URL/_reindex?wait_for_completion=false&requests_per_second=-1" \
  -H 'Content-Type: application/json' --data-binary "$BODY")"
TASK="$(echo "$RESP" | jqfield "['task']")"
echo "   task: $TASK"

echo ">> polling until complete ..."
while :; do
  resp="$(c9 "$ES9_URL/_tasks/$TASK")"
  completed="$(echo "$resp" | jqfield "['completed']")"
  created="$(echo "$resp" | jqfield "['task']['status']['created']")"
  total="$(echo "$resp" | jqfield "['task']['status']['total']")"
  echo "   completed=$completed created=$created/$total"
  [ "$completed" = "True" ] && break
  sleep 10
done
END=$(date +%s)
ELAPSED=$((END - START))

# Task result: created / updated / conflicts / failures.
resp="$(c9 "$ES9_URL/_tasks/$TASK")"
CREATED="$(echo "$resp"   | jqfield "['task']['status']['created']")"
UPDATED="$(echo "$resp"   | jqfield "['task']['status']['updated']")"
CONFLICTS="$(echo "$resp" | jqfield "['task']['status']['version_conflicts']")"
FAILURES="$(echo "$resp"  | jqfield "['response'].get('failures',[]).__len__()" 2>/dev/null || echo 0)"

# Refresh dest and compare counts.
c9 -XPUT "$ES9_URL/$DST_INDEX/_settings" -H 'Content-Type: application/json' \
  --data '{"index":{"refresh_interval":"1s"}}' >/dev/null
c9 -XPOST "$ES9_URL/$DST_INDEX/_refresh" >/dev/null

SRC_CNT="$(c6 "$ES6_REMOTE/$SRC_INDEX/_count" | jqfield "['count']")"
DST_CNT="$(c9 "$ES9_URL/$DST_INDEX/_count" | jqfield "['count']")"
RATE=$(( DST_CNT / (ELAPSED>0 ? ELAPSED : 1) ))

echo "-------------------------------------------------------"
echo " reindex time     : ${ELAPSED}s  (~${RATE} docs/s)"
echo " created          : ${CREATED}"
echo " updated          : ${UPDATED}"
echo " version_conflicts: ${CONFLICTS}"
echo " failures         : ${FAILURES}"
echo " source count     : ${SRC_CNT}  ($SRC_INDEX)"
echo " dest count       : ${DST_CNT}  ($DST_INDEX)"
echo "-------------------------------------------------------"

if [ "$SRC_CNT" = "$DST_CNT" ] && [ "$FAILURES" -eq 0 ]; then
  echo ">> SUCCESS: counts match ($DST_CNT docs) with no failures"

  # Cutover marker: the blue-green rollback delta sync (ES9 -> ES6) reads this
  # back via GET $DST_INDEX/_mapping to find its lower bound on `updated_at`,
  # so it never depends on an operator remembering the exact cutover time.
  CUTOVER_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  c9 -XPUT "$ES9_URL/$DST_INDEX/_mapping" -H 'Content-Type: application/json' \
    --data "{\"_meta\":{\"cutover_at\":\"$CUTOVER_AT\"}}" >/dev/null
  echo ">> recorded cutover marker: _meta.cutover_at=$CUTOVER_AT"
else
  echo ">> MISMATCH/FAILURE: src=$SRC_CNT dest=$DST_CNT failures=$FAILURES" >&2
  exit 1
fi
