#!/usr/bin/env bash
#
# Multi-Index ES Mutation Simulator (100% Pure Shell Script)
# Detailed progress logging and execution summary for CI/CD tracing.
#
# Env Vars:
#   ES_URL           Elasticsearch Base URL        (default http://localhost:9200)
#   ES_USER          Basic Auth Username           (default elastic)
#   ES_PASS / ES_PW  Basic Auth Password           (default "")
#   INDICES          Target indices (comma-sep)    (default discovered from templates)
#   SAMPLE_FILE      Path to JSON file or folder   (default sample_templates.json)
#   REPORT_FILE      Path to save report JSON      (default report.json)
#   MUTATE_PCT       Mutation fraction             (default 0.10)
#   CREATE_RATIO     Create fraction of mutations  (default 0.10)
#   UPDATE_RATIO     Update fraction of mutations  (default 0.70)
#   DELETE_RATIO     Delete fraction of mutations  (default 0.20)
#   TOTAL_MUTATIONS  Override fixed mutation count (default "")
#
set -euo pipefail

START_TIME=$(date +%s)
START_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

ES_URL="${ES_URL:-${ES9_URL:-http://localhost:9200}}"
ES_URL="${ES_URL%/}"
ES_USER="${ES_USER:-${ES9_USER:-elastic}}"
ES_PW="${ES_PASS:-${ES9_PASS:-${ES9_PW:-${ES_PW:-}}}}"
INDICES_ENV="${INDICES:-${INDEX:-}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_FILE="${SAMPLE_FILE:-$SCRIPT_DIR/../sample_templates.json}"
REPORT_FILE="${REPORT_FILE:-$SCRIPT_DIR/report.json}"
MUTATE_PCT="${MUTATE_PCT:-0.10}"
CREATE_RATIO="${CREATE_RATIO:-0.30}"
UPDATE_RATIO="${UPDATE_RATIO:-0.60}"
DELETE_RATIO="${DELETE_RATIO:-0.10}"
TOTAL_MUTATIONS="${TOTAL_MUTATIONS:-}"

es_curl() {
  if [ -n "$ES_PW" ]; then
    curl -fsS -u "$ES_USER:$ES_PW" "$@"
  else
    curl -fsS "$@"
  fi
}

echo "=================================================="
echo ">> MULTI-INDEX ES MUTATION SIMULATOR (PURE SHELL)"
echo "=================================================="
echo "   Start Time     : $START_DATE"
echo "   ES URL         : $ES_URL"
echo "   Auth User      : $ES_USER"
echo "   Sample Path    : $SAMPLE_FILE"
echo "   Report File    : $REPORT_FILE"
echo "   Mutate Fraction: $MUTATE_PCT"
echo "   C / U / D Ratio: $CREATE_RATIO / $UPDATE_RATIO / $DELETE_RATIO"
echo "--------------------------------------------------"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: 'jq' command is required but not installed." >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

TEMPLATES_FILE="$TMP_DIR/templates.json"
echo "{}" > "$TEMPLATES_FILE"

# Step 1: Discover templates
echo "[INFO] Loading templates from: $SAMPLE_FILE"
if [ -f "$SAMPLE_FILE" ]; then
  jq -s 'map(if type=="array" then .[] else . end) | map(if has("es_index") or has("index") then {((.es_index // .index)): (.create_payload // .template // .)} else . end) | add // {}' "$SAMPLE_FILE" > "$TEMPLATES_FILE" 2>/dev/null || echo "{}" > "$TEMPLATES_FILE"
  echo "[INFO] Successfully loaded template file."
elif [ -d "$SAMPLE_FILE" ]; then
  echo "[INFO] Scanning folder recursively for JSON files..."
  find "$SAMPLE_FILE" -type f -name "*.json" -exec cat {} + | jq -s 'map(if type=="array" then .[] else . end) | map(if has("es_index") or has("index") then {((.es_index // .index)): (.create_payload // .template // .)} else . end) | add // {}' > "$TEMPLATES_FILE" 2>/dev/null || echo "{}" > "$TEMPLATES_FILE"
  echo "[INFO] Successfully scanned template directory."
else
  echo "[WARN] Sample path '$SAMPLE_FILE' not found. Fallback to default template."
fi

# Step 2: Discover target indices
if [ -n "$INDICES_ENV" ]; then
  IFS=',' read -r -a TARGET_INDICES <<< "$INDICES_ENV"
else
  mapfile -t TARGET_INDICES < <(jq -r 'keys[] | select(. != "default")' "$TEMPLATES_FILE" 2>/dev/null || echo "bench-es9")
fi

if [ ${#TARGET_INDICES[@]} -eq 0 ]; then
  TARGET_INDICES=("bench-es9")
fi

NUM_INDICES=${#TARGET_INDICES[@]}
echo "[INFO] Target Indices ($NUM_INDICES): ${TARGET_INDICES[*]}"

REPORT_JSON="$TMP_DIR/report.json"
echo "{}" > "$REPORT_JSON"

GRAND_TOTAL_CREATED=0
GRAND_TOTAL_UPDATED=0
GRAND_TOTAL_DELETED=0

# Step 3: Run mutation per index
IDX_COUNTER=0
for INDEX in "${TARGET_INDICES[@]}"; do
  INDEX=$(echo "$INDEX" | xargs)
  [ -z "$INDEX" ] && continue
  IDX_COUNTER=$((IDX_COUNTER + 1))

  echo ""
  echo "--------------------------------------------------"
  echo "[$IDX_COUNTER/$NUM_INDICES] Processing Index: '$INDEX'"
  echo "--------------------------------------------------"

  # Fetch count
  echo "   [1/4] Querying existing document count..."
  CNT_RESP="$(es_curl -XGET "$ES_URL/$INDEX/_count" 2>/dev/null || echo '{"count":0}')"
  TOTAL_DOCS=$(echo "$CNT_RESP" | jq '.count // 0')
  echo "         Existing docs count: $TOTAL_DOCS"

  EXISTING_IDS=()
  if [ "$TOTAL_DOCS" -gt 0 ]; then
    echo "   [2/4] Fetching existing document IDs..."
    SEARCH_RESP="$(es_curl -XGET "$ES_URL/$INDEX/_search?size=5000&_source=false" 2>/dev/null || echo '{}')"
    mapfile -t EXISTING_IDS < <(echo "$SEARCH_RESP" | jq -r '.hits.hits[]._id // empty')
    echo "         Retrieved ${#EXISTING_IDS[@]} existing ID(s)."
  fi

  # Calculate targets
  if [ "$TOTAL_DOCS" -eq 0 ]; then
    CREATE_N=${TOTAL_MUTATIONS:-10}
    UPDATE_N=0
    DELETE_N=0
  else
    if [ -n "$TOTAL_MUTATIONS" ]; then
      TOUCH_COUNT="$TOTAL_MUTATIONS"
    else
      TOUCH_COUNT=$(awk "BEGIN {cnt=int($TOTAL_DOCS * $MUTATE_PCT); print (cnt > 1 ? cnt : 1)}")
    fi
    CREATE_N=$(awk "BEGIN {print int($TOUCH_COUNT * $CREATE_RATIO)}")
    DELETE_N=$(awk "BEGIN {d=int($TOUCH_COUNT * $DELETE_RATIO); len=${#EXISTING_IDS[@]}; print (d < len ? d : len)}")
    UPDATE_N=$(awk "BEGIN {u=$TOUCH_COUNT - $CREATE_N - $DELETE_N; print (u > 0 ? u : 0)}")
  fi

  echo "   [3/4] Calculated mutation quotas:"
  echo "         + Creates : $CREATE_N"
  echo "         ~ Updates : $UPDATE_N"
  echo "         - Deletes : $DELETE_N"

  SHUFFLED_IDS=()
  if [ ${#EXISTING_IDS[@]} -gt 0 ]; then
    mapfile -t SHUFFLED_IDS < <(printf "%s\n" "${EXISTING_IDS[@]}" | shuf 2>/dev/null || printf "%s\n" "${EXISTING_IDS[@]}")
  fi

  UPDATE_IDS=("${SHUFFLED_IDS[@]:0:$UPDATE_N}")
  DELETE_IDS=("${SHUFFLED_IDS[@]:$UPDATE_N:$DELETE_N}")
  CREATED_IDS=()

  BULK_FILE="$TMP_DIR/bulk.ndjson"
  : > "$BULK_FILE"

  NOW_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  TMPL_STR="$(jq -c --arg idx "$INDEX" '.[$idx] // .["default"] // {"id":"doc-{{SEQ}}","name":"Item {{SEQ}}","modified_at":"{{TIMESTAMP}}"}' "$TEMPLATES_FILE")"

  # Creates
  for ((i=1; i<=CREATE_N; i++)); do
    SEQ=$((TOTAL_DOCS + i))
    DOC_ID="doc-$SEQ"
    CREATED_IDS+=("$DOC_ID")

    PAYLOAD=$(echo "$TMPL_STR" | sed \
      -e "s/{{SEQ}}/$SEQ/g" \
      -e "s/{{seq}}/$SEQ/g" \
      -e "s/{{ID}}/$DOC_ID/g" \
      -e "s/{{id}}/$DOC_ID/g" \
      -e "s/{{TIMESTAMP}}/$NOW_TS/g" \
      -e "s/{{timestamp}}/$NOW_TS/g" \
      -e "s/{{NOW}}/$NOW_TS/g" \
      -e "s/{{now}}/$NOW_TS/g")

    PAYLOAD=$(echo "$PAYLOAD" | jq -c --arg ts "$NOW_TS" '. + {modified_at: (.modified_at // $ts)}')

    echo "{\"index\":{\"_id\":\"$DOC_ID\"}}" >> "$BULK_FILE"
    echo "$PAYLOAD" >> "$BULK_FILE"
  done

  # Updates
  for ((i=0; i<${#UPDATE_IDS[@]}; i++)); do
    U_ID="${UPDATE_IDS[$i]}"
    UPD_NAME="Name $((i + 1)) UPDATED"
    echo "{\"update\":{\"_id\":\"$U_ID\"}}" >> "$BULK_FILE"
    echo "{\"doc\":{\"updated_at\":\"$NOW_TS\",\"modified_at\":\"$NOW_TS\",\"simulated_update\":true,\"name\":\"$UPD_NAME\"}}" >> "$BULK_FILE"
  done

  # Deletes
  for D_ID in "${DELETE_IDS[@]}"; do
    echo "{\"delete\":{\"_id\":\"$D_ID\"}}" >> "$BULK_FILE"
  done

  echo "   [4/4] Sending bulk mutations to Elasticsearch..."
  if [ -s "$BULK_FILE" ]; then
    es_curl -XPOST "$ES_URL/$INDEX/_bulk" -H 'Content-Type: application/x-ndjson' --data-binary "@$BULK_FILE" >/dev/null 2>&1
    es_curl -XPOST "$ES_URL/$INDEX/_refresh" >/dev/null 2>&1
    echo "         Bulk request acknowledged and index refreshed."
  else
    echo "         No operations to execute."
  fi

  # Record totals
  N_CR=${#CREATED_IDS[@]}
  N_UP=${#UPDATE_IDS[@]}
  N_DEL=${#DELETE_IDS[@]}
  GRAND_TOTAL_CREATED=$((GRAND_TOTAL_CREATED + N_CR))
  GRAND_TOTAL_UPDATED=$((GRAND_TOTAL_UPDATED + N_UP))
  GRAND_TOTAL_DELETED=$((GRAND_TOTAL_DELETED + N_DEL))

  CR_JSON=$(printf '%s\n' "${CREATED_IDS[@]}" | jq -R . | jq -s .)
  UP_JSON=$(printf '%s\n' "${UPDATE_IDS[@]}" | jq -R . | jq -s .)
  DEL_JSON=$(printf '%s\n' "${DELETE_IDS[@]}" | jq -R . | jq -s .)

  jq --arg idx "$INDEX" --argjson cr "$CR_JSON" --argjson up "$UP_JSON" --argjson del "$DEL_JSON" \
    '.[$idx] = {created: $cr, updated: $up, deleted: $del}' "$REPORT_JSON" > "$REPORT_JSON.tmp" && mv "$REPORT_JSON.tmp" "$REPORT_JSON"

  echo "   [STATUS] '$INDEX' Completed (+ $N_CR created, ~ $N_UP updated, - $N_DEL deleted)"
done

cp "$REPORT_JSON" "$REPORT_FILE"

END_TIME=$(date +%s)
END_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "=================================================="
echo ">> SIMULATION EXECUTION SUMMARY"
echo "=================================================="
echo "   Start Time    : $START_DATE"
echo "   End Time      : $END_DATE"
echo "   Elapsed Time  : ${ELAPSED}s"
echo "   Indices Processed: $NUM_INDICES"
echo "   Total Created : + $GRAND_TOTAL_CREATED docs"
echo "   Total Updated : ~ $GRAND_TOTAL_UPDATED docs"
echo "   Total Deleted : - $GRAND_TOTAL_DELETED docs"
echo "   Total Mutated : $((GRAND_TOTAL_CREATED + GRAND_TOTAL_UPDATED + GRAND_TOTAL_DELETED)) docs"
echo "   Report Saved  : $REPORT_FILE"
echo "=================================================="
