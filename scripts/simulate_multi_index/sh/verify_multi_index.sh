#!/usr/bin/env bash
#
# Multi-Index Elasticsearch Verification Script (Shell Version)
#
# Reads settings directly from env vars:
#   ES_URL       Elasticsearch Base URL        (default http://localhost:9200)
#   ES_USER      Basic Auth Username           (default elastic)
#   ES_PASS      Basic Auth Password           (default "")
#   REPORT_FILE  Path to report JSON           (default report.json)
#
set -euo pipefail

ES_URL="${ES_URL:-${ES9_URL:-http://localhost:9200}}"
ES_USER="${ES_USER:-${ES9_USER:-elastic}}"
ES_PW="${ES_PASS:-${ES9_PASS:-${ES9_PW:-${ES_PW:-}}}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_FILE="${REPORT_FILE:-$SCRIPT_DIR/report.json}"

echo ">> Starting Verification from report: $REPORT_FILE"
echo "   Target ES: $ES_URL"

python -c "
import os, sys, json, base64, urllib.request, urllib.error

ES_URL = os.environ.get('ES_URL', 'http://localhost:9200').rstrip('/')
ES_USER = os.environ.get('ES_USER', 'elastic')
ES_PW = os.environ.get('ES_PASS', '')
REPORT_FILE = os.environ.get('REPORT_FILE', 'report.json')
IGNORED_FIELDS = {'modified_at', 'updated_at', 'created_at', '@timestamp', '_ingest'}

if not os.path.exists(REPORT_FILE):
    print(f'ERROR: Report file {REPORT_FILE} not found.', file=sys.stderr)
    sys.exit(1)

with open(REPORT_FILE, 'r', encoding='utf-8') as f:
    report_data = json.load(f)

def es_get_doc(index, doc_id):
    url = f'{ES_URL}/{index}/_doc/{doc_id}'
    headers = {'Content-Type': 'application/json'}
    if ES_PW:
        headers['Authorization'] = 'Basic ' + base64.b64encode(f'{ES_USER}:{ES_PW}'.encode()).decode()
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return {'found': True, 'source': data.get('_source', {})}
    except urllib.error.HTTPError as e:
        if e.code == 404: return {'found': False, 'source': {}}
        raise

total, passed, failed = 0, 0, 0

for index_name, changes in report_data.items():
    print(f'\n>> Index: \'{index_name}\'')
    created = changes.get('created', [])[:5]
    updated = changes.get('updated', [])[:5]
    deleted = changes.get('deleted', [])[:5]

    for doc_id in created:
        total += 1
        res = es_get_doc(index_name, doc_id)
        if res['found']:
            passed += 1
            print(f'   [PASS] Created doc \'{doc_id}\' exists in ES.')
        else:
            failed += 1
            print(f'   [FAIL] Created doc \'{doc_id}\' missing!')

    for doc_id in updated:
        total += 1
        res = es_get_doc(index_name, doc_id)
        if res['found'] and ('UPDATED' in str(res['source'].get('name', '')) or res['source'].get('simulated_update')):
            passed += 1
            print(f'   [PASS] Updated doc \'{doc_id}\' reflects mutation.')
        else:
            failed += 1
            print(f'   [FAIL] Updated doc \'{doc_id}\' mutation missing!')

    for doc_id in deleted:
        total += 1
        res = es_get_doc(index_name, doc_id)
        if not res['found']:
            passed += 1
            print(f'   [PASS] Deleted doc \'{doc_id}\' verified 404 (Removed).')
        else:
            failed += 1
            print(f'   [FAIL] Deleted doc \'{doc_id}\' still exists!')

print(f'\n>> Verification Complete: {passed}/{total} Passed, {failed} Failed.')
if failed > 0: sys.exit(1)
"

echo ">> Verification finished!"
