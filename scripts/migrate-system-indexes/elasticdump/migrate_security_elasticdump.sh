#!/usr/bin/env bash
set -e

# =========================================================
# Elasticdump Migration Pipeline for ES6 -> ES9 Security
# =========================================================

ES6_HOST="${ES6_HOST:-10.146.0.10}"
ES6_PORT="${ES6_PORT:-9200}"
ES6_USER="${ES6_USER:-elastic}"
ES6_PW="${ES6_PW:-elastic}"

ES9_HOST="${ES9_HOST:-10.146.0.11}"
ES9_PORT="${ES9_PORT:-9200}"
ES9_USER="${ES9_USER:-elastic}"
ES9_PW="${ES9_PW:-elastic}"

DUMP_FILE="es6_security_dump.json"

echo "======================================================="
echo " Elasticdump ES6 -> ES9 Security Migration Pipeline"
echo "======================================================="

run_elasticdump() {
  local input="$1"
  local output="$2"
  local type="${3:-data}"

  if command -v npx >/dev/null 2>&1; then
    echo ">> Running elasticdump via npx..."
    npx -y elasticdump --input="$input" --output="$output" --type="$type"
  elif command -v docker >/dev/null 2>&1; then
    echo ">> Running elasticdump via Docker (elasticdump/elasticsearch-dump)..."
    local in_target="$input"
    local out_target="$output"
    if [[ "$input" != http* ]]; then
      in_target="/data/$input"
    fi
    if [[ "$output" != http* ]]; then
      out_target="/data/$output"
    fi
    docker run --rm -v "$(pwd):/data" elasticdump/elasticsearch-dump \
      --input="$in_target" \
      --output="$out_target" \
      --type="$type"
  else
    echo "Error: Neither npx nor docker is available to run elasticdump." >&2
    exit 1
  fi
}

echo ">> Step 1: Exporting .security-6 system index from ES6 using elasticdump..."
run_elasticdump \
  "http://${ES6_USER}:${ES6_PW}@${ES6_HOST}:${ES6_PORT}/.security-6" \
  "${DUMP_FILE}" \
  "data"

echo ">> Step 2: Importing dump to intermediate index 'imported-es6-security' on ES9..."
run_elasticdump \
  "${DUMP_FILE}" \
  "http://${ES9_USER}:${ES9_PW}@${ES9_HOST}:${ES9_PORT}/imported-es6-security" \
  "data"

echo ">> Step 3: Parsing dumped documents and registering Roles & Users on ES9..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/apply_dumped_security.py" "${DUMP_FILE}"

echo ""
echo "======================================================="
echo " Elasticdump Security Migration Completed Successfully!"
echo "======================================================="

