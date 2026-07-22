#!/usr/bin/env bash
#
# Blue-green rollback, no K8s/Helm/Logstash: plain curl + python, run
# directly from the operator's machine against ES6/ES9's external IPs.
#
# 1. Reads the cutover marker (_meta.cutover_at) from ES9.
# 2. Delta-syncs every doc with updated_at > cutover_at from ES9 to ES6
#    (paginated with search_after, bulk-upserted as full-document replaces).
# 3. Compares bench-es9/bench-es6 counts. If they already match, done --
#    that's the common case and the expensive full-ID-diff pass is skipped.
#    If they differ (deletes happened on ES9 that a delta-by-updated_at
#    query structurally can't see), runs reconcile_deletes.sh to find and
#    remove the difference from ES6.
#
# See docs/MAPPING-DIFFERENCES.md and
# docs/superpowers/specs/2026-07-21-es9-es6-rollback-design.md for why.
#
# Runs from the operator's own machine, so this uses `python`, not
# `python3` -- on Windows/Git Bash there is usually no `python3` on PATH.
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

jqfield() { python -c "import sys,json;print(json.load(sys.stdin)$1)"; }

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo ">> fetching cutover marker from $ES9_URL/$SRC_INDEX/_mapping"
CUTOVER_AT="$(c9 "$ES9_URL/$SRC_INDEX/_mapping" | jqfield "['$SRC_INDEX']['mappings']['_meta']['cutover_at']")"
echo "   cutover_at=$CUTOVER_AT"

echo ">> delta sync: $SRC_INDEX (updated_at > $CUTOVER_AT) -> $DST_INDEX"
search_after=""
total_synced=0
while :; do
  # Sort by updated_at (what we're actually filtering/paging on) with _doc
  # as a tiebreaker -- without it, ties on the exact same updated_at value
  # at a page boundary could get skipped or duplicated across pages.
  if [ -z "$search_after" ]; then
    body='{"size":'"$PAGE_SIZE"',"sort":[{"updated_at":"asc"},"_doc"],"query":{"range":{"updated_at":{"gt":"'"$CUTOVER_AT"'"}}}}'
  else
    body='{"size":'"$PAGE_SIZE"',"sort":[{"updated_at":"asc"},"_doc"],"search_after":'"$search_after"',"query":{"range":{"updated_at":{"gt":"'"$CUTOVER_AT"'"}}}}'
  fi
  resp="$(c9 -XPOST "$ES9_URL/$SRC_INDEX/_search" -H 'Content-Type: application/json' --data-binary "$body")"
  hits="$(python -c "import sys,json;print(len(json.loads(sys.argv[1])['hits']['hits']))" "$resp")"
  [ "$hits" -eq 0 ] && break

  # Full-document replace (index action) into ES6, not a partial update --
  # we already have the whole source from ES9, no need for update+upsert
  # semantics. /_doc/_bulk (not /_bulk): ES6 still has mapping types (see
  # docs/MAPPING-DIFFERENCES.md), and its _bulk API rejects actions with no
  # type ("type is missing").
  python -c "
import sys, json
d = json.loads(sys.argv[1])
for h in d['hits']['hits']:
    print(json.dumps({'index': {'_id': h['_id']}}))
    print(json.dumps(h['_source']))
" "$resp" >"$TMPDIR/page.ndjson"

  c6 -XPOST "$ES6_URL/$DST_INDEX/_doc/_bulk" -H 'Content-Type: application/x-ndjson' \
    --data-binary "@$TMPDIR/page.ndjson" >/dev/null

  total_synced=$((total_synced + hits))
  echo "   synced page: $hits docs (total $total_synced)"

  search_after="$(python -c "
import sys, json
d = json.loads(sys.argv[1])
print(json.dumps(d['hits']['hits'][-1]['sort']))
" "$resp")"
done
echo "   delta sync done: $total_synced doc(s) created/updated on $DST_INDEX"

c6 -XPOST "$ES6_URL/$DST_INDEX/_refresh" >/dev/null
c9 -XPOST "$ES9_URL/$SRC_INDEX/_refresh" >/dev/null

SRC_CNT="$(c9 "$ES9_URL/$SRC_INDEX/_count" | jqfield "['count']")"
DST_CNT="$(c6 "$ES6_URL/$DST_INDEX/_count" | jqfield "['count']")"
echo ">> post-sync counts: $SRC_INDEX=$SRC_CNT $DST_INDEX=$DST_CNT"

if [ "$SRC_CNT" = "$DST_CNT" ]; then
  echo ">> counts match -- no deletes to reconcile against ES9, done."
else
  echo ">> counts differ ($DST_INDEX=$DST_CNT vs $SRC_INDEX=$SRC_CNT) -- deletes"
  echo "   happened on ES9 since cutover; running reconcile_deletes.sh"
  ES6_URL="$ES6_URL" ES9_URL="$ES9_URL" SRC_INDEX="$SRC_INDEX" DST_INDEX="$DST_INDEX" \
    ES6_USER="$ES6_USER" ES6_PW="$ES6_PW" ES9_USER="$ES9_USER" ES9_PW="$ES9_PW" \
    "$SCRIPT_DIR/reconcile_deletes.sh"
fi

echo ">> rollback delta sync complete."
