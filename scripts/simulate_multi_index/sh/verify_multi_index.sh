#!/usr/bin/env bash
#
# Multi-Index ES Verification Script (100% Pure Shell Script)
# Detailed progress logging and execution summary for CI/CD tracing.
#
# Env Vars:
#   ES_URL       Elasticsearch Base URL        (default http://localhost:9200)
#   ES_USER      Basic Auth Username           (default elastic)
#   ES_PASS      Basic Auth Password           (default "")
#   REPORT_FILE  Path to report JSON           (default report.json)
#
set -euo pipefail

START_TIME=$(date +%s)
START_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

ES_URL="${ES_URL:-${ES9_URL:-http://localhost:9200}}"
ES_URL="${ES_URL%/}"
ES_USER="${ES_USER:-${ES9_USER:-elastic}}"
ES_PW="${ES_PASS:-${ES9_PASS:-${ES9_PW:-${ES_PW:-}}}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_FILE="${REPORT_FILE:-$SCRIPT_DIR/report.json}"

es_curl() {
  if [ -n "$ES_PW" ]; then
    curl -fsS -u "$ES_USER:$ES_PW" "$@"
  else
    curl -fsS "$@"
  fi
}

echo "=================================================="
echo ">> MULTI-INDEX ES VERIFICATION AUDIT (PURE SHELL)"
echo "=================================================="
echo "   Start Time  : $START_DATE"
echo "   Target ES   : $ES_URL"
echo "   Auth User   : $ES_USER"
echo "   Report File : $REPORT_FILE"
echo "--------------------------------------------------"

if [ ! -f "$REPORT_FILE" ]; then
  echo "ERROR: Report file '$REPORT_FILE' not found." >&2
  exit 1
fi

INDICES=$(jq -r 'keys[]' "$REPORT_FILE")
NUM_INDICES=$(echo "$INDICES" | wc -w)

TOTAL=0
PASSED=0
FAILED=0

IDX_COUNTER=0
for INDEX in $INDICES; do
  IDX_COUNTER=$((IDX_COUNTER + 1))
  echo ""
  echo "--------------------------------------------------"
  echo "[$IDX_COUNTER/$NUM_INDICES] Verifying Index: '$INDEX'"
  echo "--------------------------------------------------"

  mapfile -t CREATED_SAMPLES < <(jq -r --arg idx "$INDEX" '.[$idx].created[:5][] // empty' "$REPORT_FILE")
  mapfile -t UPDATED_SAMPLES < <(jq -r --arg idx "$INDEX" '.[$idx].updated[:5][] // empty' "$REPORT_FILE")
  mapfile -t DELETED_SAMPLES < <(jq -r --arg idx "$INDEX" '.[$idx].deleted[:5][] // empty' "$REPORT_FILE")

  echo "   [1/3] Checking CREATED records (${#CREATED_SAMPLES[@]} samples)..."
  for DOC_ID in "${CREATED_SAMPLES[@]}"; do
    [ -z "$DOC_ID" ] && continue
    TOTAL=$((TOTAL + 1))
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "$ES_USER:$ES_PW" "$ES_URL/$INDEX/_doc/$DOC_ID" || true)
    if [ "$STATUS" -eq 200 ]; then
      PASSED=$((PASSED + 1))
      echo "         [PASS] Created doc '$DOC_ID' exists in ES."
    else
      FAILED=$((FAILED + 1))
      echo "         [FAIL] Created doc '$DOC_ID' missing (HTTP $STATUS)!"
    fi
  done

  echo "   [2/3] Checking UPDATED records (${#UPDATED_SAMPLES[@]} samples)..."
  for DOC_ID in "${UPDATED_SAMPLES[@]}"; do
    [ -z "$DOC_ID" ] && continue
    TOTAL=$((TOTAL + 1))
    RESP=$(es_curl -XGET "$ES_URL/$INDEX/_doc/$DOC_ID" 2>/dev/null || echo '{}')
    IS_UPDATED=$(echo "$RESP" | jq -r '._source.simulated_update // false')
    NAME_VAL=$(echo "$RESP" | jq -r '._source.name // ""')
    if [ "$IS_UPDATED" = "true" ] || [[ "$NAME_VAL" == *"UPDATED"* ]]; then
      PASSED=$((PASSED + 1))
      echo "         [PASS] Updated doc '$DOC_ID' reflects expected mutation."
    else
      FAILED=$((FAILED + 1))
      echo "         [FAIL] Updated doc '$DOC_ID' mutation missing!"
    fi
  done

  echo "   [3/3] Checking DELETED records (${#DELETED_SAMPLES[@]} samples)..."
  for DOC_ID in "${DELETED_SAMPLES[@]}"; do
    [ -z "$DOC_ID" ] && continue
    TOTAL=$((TOTAL + 1))
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "$ES_USER:$ES_PW" "$ES_URL/$INDEX/_doc/$DOC_ID" || true)
    if [ "$STATUS" -eq 404 ]; then
      PASSED=$((PASSED + 1))
      echo "         [PASS] Deleted doc '$DOC_ID' verified HTTP 404 (Removed)."
    else
      FAILED=$((FAILED + 1))
      echo "         [FAIL] Deleted doc '$DOC_ID' still exists (HTTP $STATUS)!"
    fi
  done
done

END_TIME=$(date +%s)
END_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "=================================================="
echo ">> VERIFICATION AUDIT EXECUTION SUMMARY"
echo "=================================================="
echo "   Start Time       : $START_DATE"
echo "   End Time         : $END_DATE"
echo "   Elapsed Time     : ${ELAPSED}s"
echo "   Indices Audited  : $NUM_INDICES"
echo "   Total Checks     : $TOTAL"
echo "   Passed Checks    : $PASSED"
echo "   Failed Checks    : $FAILED"

if [ "$FAILED" -eq 0 ]; then
  echo "   AUDIT RESULT     : [SUCCESS] ALL CHECKS PASSED!"
  echo "=================================================="
  exit 0
else
  echo "   AUDIT RESULT     : [FAILED] DISCREPANCIES DETECTED!"
  echo "=================================================="
  exit 1
fi
