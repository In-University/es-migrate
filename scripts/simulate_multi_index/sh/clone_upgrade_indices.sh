#!/usr/bin/env bash
#
# Clone Elasticsearch Concrete Indices attached to Aliases with '_upgrade' suffix.
# '_reindex' for ES 6.x (Never touches or deletes source indices).
#
# Env Vars:
#   ES_URL           Elasticsearch Base URL        (default http://localhost:9200)
#   ES_USER          Basic Auth Username           (default elastic)
#   ES_PASS / ES_PW  Basic Auth Password           (default "")
#   SUFFIX           Suffix for cloned indices     (default _upgrade)
#   RESET            Drop target index if exists?  (default true)
#   BATCH_SIZE       Scroll batch size for reindex (default 5000)
#
set -euo pipefail

ES_URL="${ES_URL:-${ES9_URL:-${ES6_URL:-http://localhost:9200}}}"
ES_URL="${ES_URL%/}"
ES_USER="${ES_USER:-${ES9_USER:-${ES6_USER:-elastic}}}"
ES_PW="${ES_PASS:-${ES9_PASS:-${ES6_PW:-${ES_PW:-}}}}"
SUFFIX="${SUFFIX:-_upgrade}"
RESET="${RESET:-true}"
BATCH_SIZE="${BATCH_SIZE:-5000}"

es_curl() {
  if [ -n "$ES_PW" ]; then
    curl -fsS -u "$ES_USER:$ES_PW" "$@"
  else
    curl -fsS "$@"
  fi
}

echo ">> ES Alias Concrete Index Cloner (Safe ES6/ES9)"
echo "   Elasticsearch URL : $ES_URL"
echo "   Auth User         : $ES_USER"
echo "   Target Suffix     : $SUFFIX"
echo "   Reindex Batch Size: $BATCH_SIZE"
echo "--------------------------------------------------"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: 'jq' command is required but not installed." >&2
  exit 1
fi

echo ">> Fetching aliases from $ES_URL/_aliases..."
ALIASES_JSON="$(es_curl -XGET "$ES_URL/_aliases" -H 'Content-Type: application/json' || true)"

CONCRETE_INDICES=""
if [ -n "$ALIASES_JSON" ]; then
  CONCRETE_INDICES=$(echo "$ALIASES_JSON" | jq -r 'to_entries[] | select(.key | startswith(".") | not) | select(.value.aliases | length > 0) | .key' 2>/dev/null || true)
fi

if [ -z "$CONCRETE_INDICES" ]; then
  echo ">> No indices with active aliases found. Fetching all non-system indices..."
  CAT_JSON="$(es_curl -XGET "$ES_URL/_cat/indices?format=json" -H 'Content-Type: application/json' || true)"
  if [ -n "$CAT_JSON" ]; then
    CONCRETE_INDICES=$(echo "$CAT_JSON" | jq -r '.[] | .index | select(startswith(".") | not) | select(endswith("'"$SUFFIX"'") | not)' 2>/dev/null || true)
  fi
fi

if [ -z "$CONCRETE_INDICES" ]; then
  echo "WARNING: No concrete indices found on ES cluster."
  exit 0
fi

echo ">> Found concrete index(es):"
for idx in $CONCRETE_INDICES; do
  echo "   - $idx"
done

for SRC_INDEX in $CONCRETE_INDICES; do
  DST_INDEX="${SRC_INDEX}${SUFFIX}"
  echo ""
  echo ">> Cloning Index: '$SRC_INDEX' -> '$DST_INDEX'"

  CHECK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "$ES_USER:$ES_PW" "$ES_URL/$DST_INDEX" || true)
  if [ "$CHECK_STATUS" -eq 200 ]; then
    if [ "$RESET" = "true" ]; then
      echo "   Target index '$DST_INDEX' exists. Resetting (deleting TARGET index only)..."
      es_curl -XDELETE "$ES_URL/$DST_INDEX" >/dev/null 2>&1 || true
    else
      echo "   Target index '$DST_INDEX' already exists. Skipping."
      continue
    fi
  fi

  # Attempt 1: Try Native ES '_clone' API (ES 7.4+ / ES 9)
  echo "   [Attempt 1] Trying Native ES _clone API..."
  es_curl -XPUT "$ES_URL/$SRC_INDEX/_settings" -H 'Content-Type: application/json' \
    -d '{"settings": {"index.blocks.write": true}}' >/dev/null 2>&1 || true

  CLONE_RESP=$(es_curl -XPOST "$ES_URL/$SRC_INDEX/_clone/$DST_INDEX" -H 'Content-Type: application/json' || true)

  es_curl -XPUT "$ES_URL/$SRC_INDEX/_settings" -H 'Content-Type: application/json' \
    -d '{"settings": {"index.blocks.write": null}}' >/dev/null 2>&1 || true

  if echo "$CLONE_RESP" | jq -e '.acknowledged == true' >/dev/null 2>&1; then
    echo "   [SUCCESS] Natively cloned '$SRC_INDEX' -> '$DST_INDEX' (ES 7.4+/ES 9 native clone)"
    continue
  fi

  # Attempt 2: Reindex for ES 6.x (Zero touch on source index)
  echo "   [Attempt 2] Native _clone not supported (ES 6.x detected). Running _reindex..."
  SRC_INFO="$(es_curl -XGET "$ES_URL/$SRC_INDEX" -H 'Content-Type: application/json' || true)"
  if [ -z "$SRC_INFO" ]; then
    echo "   [ERROR] Failed to fetch source index metadata for '$SRC_INDEX'. Skipping."
    continue
  fi

  CREATE_BODY=$(echo "$SRC_INFO" | jq '{
    mappings: (.[keys[0]].mappings // {}),
    settings: {
      index: (((.[keys[0]].settings.index // {}) | del(.provided_name, .creation_date, .uuid, .version, .routing)) + {
        "refresh_interval": "-1",
        "number_of_replicas": "0"
      })
    }
  }' 2>/dev/null || true)

  es_curl -XPUT "$ES_URL/$DST_INDEX" -H 'Content-Type: application/json' --data-binary "$CREATE_BODY" >/dev/null 2>&1 || true

  REINDEX_BODY=$(jq -n --arg src "$SRC_INDEX" --arg dst "$DST_INDEX" --argjson size "$BATCH_SIZE" '{
    slices: "auto",
    conflicts: "proceed",
    source: {
      index: $src,
      size: $size
    },
    dest: {
      index: $dst
    }
  }')

  REINDEX_RESP=$(es_curl -XPOST "$ES_URL/_reindex" -H 'Content-Type: application/json' --data-binary "$REINDEX_BODY" 2>/dev/null || true)
  CREATED_COUNT=$(echo "$REINDEX_RESP" | jq -r '.created // 0')

  echo "   [SUCCESS] Cloned '$SRC_INDEX' -> '$DST_INDEX' ($CREATED_COUNT docs copied)."
done

echo ""
echo ">> All alias concrete indices successfully cloned with suffix '$SUFFIX'!"
