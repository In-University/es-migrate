#!/usr/bin/env bash
#
# Multi-Index Elasticsearch Mutation Simulator (Shell Script Version)
#
# Env Vars:
#   ES_URL       Elasticsearch Base URL        (default http://localhost:9200)
#   ES_USER      Basic Auth Username           (default elastic)
#   ES_PASS      Basic Auth Password           (default "")
#   INDICES      Target indices (comma-sep)    (default bench-es9)
#   SAMPLE_FILE  Path to JSON file or folder   (default sample_templates.json)
#   REPORT_FILE  Path to save report JSON      (default report.json)
#   MUTATE_PCT   Mutation fraction             (default 0.10)
#
set -euo pipefail

ES_URL="${ES_URL:-${ES9_URL:-http://localhost:9200}}"
ES_USER="${ES_USER:-${ES9_USER:-elastic}}"
ES_PW="${ES_PASS:-${ES9_PASS:-${ES9_PW:-${ES_PW:-}}}}"
INDICES_ENV="${INDICES:-${INDEX:-bench-es9}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_FILE="${SAMPLE_FILE:-$SCRIPT_DIR/../sample_templates.json}"
REPORT_FILE="${REPORT_FILE:-$SCRIPT_DIR/report.json}"
MUTATE_PCT="${MUTATE_PCT:-0.10}"

es_curl() {
  if [ -n "$ES_PW" ]; then
    curl -fsS -u "$ES_USER:$ES_PW" "$@"
  else
    curl -fsS "$@"
  fi
}

echo ">> Starting Multi-Index ES Mutation Simulator (Shell Version)"
echo "   ES URL     : $ES_URL"
echo "   Sample Path: $SAMPLE_FILE"
echo "   Report File: $REPORT_FILE"

# Execute Python core wrapper to perform multi-index simulation and write simple report
python -c "
import os, sys, json, time, random, base64, urllib.request, urllib.error

ES_URL = os.environ.get('ES_URL', 'http://localhost:9200').rstrip('/')
ES_USER = os.environ.get('ES_USER', 'elastic')
ES_PW = os.environ.get('ES_PASS', '')
INDICES_ENV = os.environ.get('INDICES_ENV', '')
SAMPLE_FILE = os.environ.get('SAMPLE_FILE', '')
REPORT_FILE = os.environ.get('REPORT_FILE', 'report.json')
MUTATE_PCT = float(os.environ.get('MUTATE_PCT', '0.10'))

WORDS = ['fast', 'durable', 'compact', 'premium', 'eco', 'smart', 'classic', 'pro', 'lite', 'max']

def current_iso_time():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def es_http(method, path, body=None, is_bulk=False):
    url = ES_URL + path
    data = body.encode('utf-8') if is_bulk else (json.dumps(body).encode('utf-8') if body is not None else None)
    headers = {'Content-Type': 'application/x-ndjson'} if is_bulk else {'Content-Type': 'application/json'}
    if ES_PW:
        headers['Authorization'] = 'Basic ' + base64.b64encode(f'{ES_USER}:{ES_PW}'.encode()).decode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        res = resp.read()
        return json.loads(res.decode('utf-8')) if res else {}

def load_templates():
    templates = {}
    def add_content(data):
        if isinstance(data, dict):
            for k, v in data.items():
                templates[k] = v.get('create_template') or v if isinstance(v, dict) else v
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    idx = item.get('es_index') or item.get('index')
                    if idx: templates[idx] = item.get('create_payload') or item
    if os.path.exists(SAMPLE_FILE):
        if os.path.isdir(SAMPLE_FILE):
            for r, _, files in os.walk(SAMPLE_FILE):
                for f in sorted(files):
                    if f.endswith('.json'):
                        with open(os.path.join(r, f), 'r', encoding='utf-8') as fp: add_content(json.load(fp))
        else:
            with open(SAMPLE_FILE, 'r', encoding='utf-8') as fp: add_content(json.load(fp))
    return templates

def render_tmpl(tmpl, seq, doc_id):
    rnd = random.Random(seq)
    now_ts = current_iso_time()
    def proc(node):
        if isinstance(node, dict):
            res = {k: proc(v) for k, v in node.items()}
            if 'modified_at' not in res: res['modified_at'] = now_ts
            return res
        elif isinstance(node, list): return [proc(x) for x in node]
        elif isinstance(node, str):
            if node in ('{{price}}', '{price}'): return round(rnd.uniform(9.99, 499.99), 2)
            val = node.replace('{{seq}}', str(seq)).replace('{seq}', str(seq))
            val = val.replace('{{id}}', doc_id).replace('{id}', doc_id)
            val = val.replace('{{timestamp}}', now_ts).replace('{timestamp}', now_ts)
            val = val.replace('{{name}}', f'Name {seq}').replace('{name}', f'Name {seq}')
            return val
        return node
    return proc(tmpl)

templates = load_templates()
indices = [i.strip() for i in INDICES_ENV.split(',') if i.strip()] if INDICES_ENV else ([k for k in templates if k != 'default'] or ['bench-es9'])

report = {}
for idx in indices:
    cnt = es_http('GET', f'/{idx}/_count').get('count', 0)
    existing = [h['_id'] for h in es_http('GET', f'/{idx}/_search?size=5000&_source=false').get('hits', {}).get('hits', [])] if cnt > 0 else []
    
    touch = 10 if cnt == 0 else max(1, int(cnt * MUTATE_PCT))
    create_n = touch if cnt == 0 else int(touch * 0.10)
    delete_n = 0 if cnt == 0 else min(len(existing), int(touch * 0.20))
    update_n = 0 if cnt == 0 else max(0, touch - create_n - delete_n)
    
    shuffled = list(existing); random.shuffle(shuffled)
    up_ids = shuffled[:update_n]
    del_ids = shuffled[update_n:update_n + delete_n]
    cr_ids = []
    
    bulk = []
    tmpl = templates.get(idx) or templates.get('default') or {'id': 'doc-{{seq}}', 'name': 'Name {{seq}}'}
    
    for i in range(create_n):
        doc_id = f'doc-{cnt + i + 1}'
        doc_data = render_tmpl(tmpl, cnt + i + 1, doc_id)
        bulk.extend([json.dumps({'index': {'_id': doc_id}}), json.dumps(doc_data, separators=(',', ':'))])
        cr_ids.append(doc_id)
        
    now_ts = current_iso_time()
    for idx_seq, doc_id in enumerate(up_ids):
        up_payload = {'updated_at': now_ts, 'modified_at': now_ts, 'simulated_update': True, 'name': f'Name {idx_seq + 1} UPDATED'}
        bulk.extend([json.dumps({'update': {'_id': doc_id}}), json.dumps({'doc': up_payload}, separators=(',', ':'))])
        
    for doc_id in del_ids:
        bulk.append(json.dumps({'delete': {'_id': doc_id}}))
        
    if bulk:
        es_http('POST', f'/{idx}/_bulk', '\n'.join(bulk) + '\n', is_bulk=True)
        es_http('POST', f'/{idx}/_refresh')
        
    report[idx] = {'created': cr_ids, 'updated': up_ids, 'deleted': del_ids}
    print(f'   Done index \'{idx}\': +{len(cr_ids)} created, ~{len(up_ids)} updated, -{len(del_ids)} deleted')

with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)
print(f'>> Report saved to {REPORT_FILE}')
"

echo ">> Multi-Index Simulation Complete!"
