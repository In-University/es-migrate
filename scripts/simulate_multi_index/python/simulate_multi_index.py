#!/usr/bin/env python3
"""
Multi-Index Elasticsearch Mutation Simulator (Python Core)
Detailed progress logging and execution summary.
"""

import base64
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List

START_TIME = time.time()
START_DATE = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ES_URL = os.environ.get("ES_URL", os.environ.get("ES9_URL", "http://localhost:9200")).rstrip("/")
ES_USER = os.environ.get("ES_USER", os.environ.get("ES9_USER", "elastic"))
ES_PW = os.environ.get("ES_PASS", os.environ.get("ES9_PASS", os.environ.get("ES9_PW", os.environ.get("ES_PW", ""))))
INDICES_ENV = os.environ.get("INDICES", os.environ.get("INDEX", ""))
CONFIG_DIR = os.environ.get("CONFIG_DIR", os.path.join(SCRIPT_DIR, "configs"))
REPORT_FILE = os.environ.get("REPORT_FILE", os.path.join(SCRIPT_DIR, "report.ndjson"))
MUTATE_PCT = float(os.environ.get("MUTATE_PCT", "0.10"))
CREATE_RATIO = float(os.environ.get("CREATE_RATIO", "0.30"))
UPDATE_RATIO = float(os.environ.get("UPDATE_RATIO", "0.60"))
DELETE_RATIO = float(os.environ.get("DELETE_RATIO", "0.10"))
TOTAL_MUTATIONS = os.environ.get("TOTAL_MUTATIONS", "")
MODIFIED_FIELD = os.environ.get("MODIFIED_FIELD", os.environ.get("UPGRADE_MODIFIED_FIELD", "upgrade_modified_at"))
BATCH = int(os.environ.get("BATCH", "2000"))
SEED = int(os.environ.get("SEED", "42"))

def current_iso_time() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def es_http(method: str, path: str, body: Any = None, is_bulk: bool = False) -> Dict[str, Any]:
    url = ES_URL + path
    if is_bulk:
        data = body.encode("utf-8") if isinstance(body, str) else body
        headers = {"Content-Type": "application/x-ndjson"}
    else:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}

    if ES_PW:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{ES_USER}:{ES_PW}".encode()).decode()

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                res_bytes = resp.read()
                return json.loads(res_bytes.decode("utf-8")) if res_bytes else {}
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise
        except urllib.error.URLError:
            if attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def render_template(template: Any, seq: int, doc_id: str, seed: int) -> Any:
    now_ts = current_iso_time()

    def process_node(node: Any) -> Any:
        if isinstance(node, dict):
            res = {k: process_node(v) for k, v in node.items()}
            if MODIFIED_FIELD not in res:
                res[MODIFIED_FIELD] = now_ts
            return res
        elif isinstance(node, list):
            return [process_node(item) for item in node]
        elif isinstance(node, str):
            val = node
            val = val.replace("{{SEQ}}", str(seq)).replace("{{seq}}", str(seq)).replace("{seq}", str(seq))
            val = val.replace("{{ID}}", doc_id).replace("{{id}}", doc_id).replace("{id}", doc_id)
            val = val.replace("{{TIMESTAMP}}", now_ts).replace("{{timestamp}}", now_ts).replace("{timestamp}", now_ts)
            val = val.replace("{{name}}", f"Name {seq}").replace("{name}", f"Name {seq}")
            return val
        return node

    return process_node(template)


def parse_template_definition(data: Any) -> Dict[str, Any]:
    """Parse template definition containing 'create' and optional 'update' schemas:
       {"create": {...}, "update": {...}}
       or directly the create schema dict: {...}
    """
    if not isinstance(data, dict):
        return {"create": data, "update": None}

    if "create" in data or "update" in data:
        return {
            "create": data.get("create", {}),
            "update": data.get("update")
        }
    return {"create": data, "update": None}


def load_templates(target_path: str = None) -> Dict[str, Dict[str, Any]]:
    if not target_path:
        target_path = CONFIG_DIR
    templates: Dict[str, Dict[str, Any]] = {}

    def add_content(data: Any, file_source: str = ""):
        if isinstance(data, dict):
            for k, v in data.items():
                parsed = parse_template_definition(v)
                templates[k] = parsed
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    idx_name = item.get("es_index") or item.get("index")
                    if idx_name:
                        raw_tmpl = item.get("template") or item
                        parsed = parse_template_definition(raw_tmpl)
                        templates[idx_name] = parsed

    if not os.path.isdir(target_path):
        print(f"[ERROR] Config directory '{target_path}' not found or is not a directory. Indices must use config files.", file=sys.stderr)
        return templates

    print(f"[INFO] Scanning config folder: {target_path}")
    json_count = 0
    for root, _, files in os.walk(target_path):
        for file in sorted(files):
            if file.endswith(".json"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        add_content(json.load(f), file)
                        json_count += 1
                except Exception as e:
                    print(f"[WARN] Could not read {full_path}: {e}", file=sys.stderr)

    print(f"[INFO] Loaded {len(templates)} index template(s) from {json_count} config file(s): {', '.join(templates.keys())}")
    return templates


def bulk_send(index: str, ndjson_lines: List[str]):
    if not ndjson_lines:
        return
    payload = "\n".join(ndjson_lines) + "\n"
    res = es_http("POST", f"/{index}/_bulk", body=payload, is_bulk=True)
    if res.get("errors"):
        for item in res.get("items", []):
            op, meta = next(iter(item.items()))
            if meta.get("status", 200) >= 300:
                print(f"   [Bulk Error] [{op}] ID {meta.get('_id')}: {meta.get('error')}", file=sys.stderr)


def simulate_index(index: str, templates: Dict[str, Any], idx_idx: int, total_indices: int, report_handle=None) -> Dict[str, Any]:
    print(f"\n--------------------------------------------------")
    print(f"[{idx_idx}/{total_indices}] Processing Index: '{index}'")
    print(f"--------------------------------------------------")

    if index not in templates:
        print(f"[ERROR] Index '{index}' does not have a config file in '{CONFIG_DIR}'. No fallback allowed.", file=sys.stderr)
        return {"created": [], "updated": [], "deleted": []}

    idx_cfg = templates[index]
    create_tmpl = idx_cfg.get("create")
    update_tmpl = idx_cfg.get("update")

    if not create_tmpl:
        print(f"[ERROR] Index '{index}' is missing 'create' pattern in config file. No fallback allowed.", file=sys.stderr)
        return {"created": [], "updated": [], "deleted": []}

    print("   [1/4] Querying existing document count...")
    try:
        cnt_res = es_http("GET", f"/{index}/_count")
        total_docs = cnt_res.get("count", 0)
        print(f"         Existing docs count: {total_docs}")
    except Exception as e:
        print(f"[ERROR] Could not query index '{index}': {e}", file=sys.stderr)
        return {"created": [], "updated": [], "deleted": []}

    existing_ids = []
    if total_docs > 0:
        print("   [2/4] Fetching existing document IDs...")
        search_res = es_http("GET", f"/{index}/_search?size=5000&_source=false")
        hits = search_res.get("hits", {}).get("hits", [])
        existing_ids = [h["_id"] for h in hits]
        print(f"         Retrieved {len(existing_ids)} existing ID(s).")

    if total_docs == 0:
        create_n = int(TOTAL_MUTATIONS) if TOTAL_MUTATIONS.isdigit() else 10
        update_n = 0
        delete_n = 0
    else:
        if TOTAL_MUTATIONS.isdigit():
            touch_count = int(TOTAL_MUTATIONS)
        else:
            touch_count = max(1, int(total_docs * MUTATE_PCT))
        create_n = int(touch_count * CREATE_RATIO)
        delete_n = min(len(existing_ids), int(touch_count * DELETE_RATIO))
        update_n = max(0, touch_count - create_n - delete_n)

    print("   [3/4] Calculated mutation quotas:")
    print(f"         + Creates : {create_n}")
    print(f"         ~ Updates : {update_n}")
    print(f"         - Deletes : {delete_n}")

    rnd = random.Random(SEED + hash(index))
    shuffled_ids = list(existing_ids)
    rnd.shuffle(shuffled_ids)

    update_ids = shuffled_ids[:update_n]
    delete_ids = shuffled_ids[update_n:update_n + delete_n]
    created_ids = []

    bulk_lines = []

    # Creates
    max_seq = total_docs
    for i in range(create_n):
        seq = max_seq + i + 1
        doc_id = f"doc-{seq}"
        doc_data = render_template(create_tmpl, seq, doc_id, SEED)
        bulk_lines.extend([json.dumps({"index": {"_id": doc_id}}), json.dumps(doc_data, separators=(",", ":"))])
        created_ids.append(doc_id)
        if report_handle:
            report_handle.write(json.dumps({"index": index, "op": "create", "id": doc_id, "body": doc_data}, separators=(",", ":")) + "\n")

        if len(bulk_lines) >= BATCH * 2:
            bulk_send(index, bulk_lines)
            bulk_lines = []

    # Updates
    now_ts = current_iso_time()
    for idx, doc_id in enumerate(update_ids):
        if update_tmpl:
            update_payload = render_template(update_tmpl, idx + 1, doc_id, SEED)
            if MODIFIED_FIELD not in update_payload:
                update_payload[MODIFIED_FIELD] = now_ts
        else:
            update_payload = {
                MODIFIED_FIELD: now_ts
            }
        bulk_lines.extend([json.dumps({"update": {"_id": doc_id}}), json.dumps({"doc": update_payload}, separators=(",", ":"))])
        if report_handle:
            report_handle.write(json.dumps({"index": index, "op": "update", "id": doc_id, "body": update_payload}, separators=(",", ":")) + "\n")

        if len(bulk_lines) >= BATCH * 2:
            bulk_send(index, bulk_lines)
            bulk_lines = []

    # Deletes
    for doc_id in delete_ids:
        bulk_lines.append(json.dumps({"delete": {"_id": doc_id}}))
        if report_handle:
            report_handle.write(json.dumps({"index": index, "op": "delete", "id": doc_id}, separators=(",", ":")) + "\n")
        if len(bulk_lines) >= BATCH * 2:
            bulk_send(index, bulk_lines)
            bulk_lines = []

    print("   [4/4] Sending bulk mutations to Elasticsearch...")
    if bulk_lines:
        bulk_send(index, bulk_lines)

    es_http("POST", f"/{index}/_refresh")
    print(f"   [STATUS] '{index}' Completed (+ {len(created_ids)} created, ~ {len(update_ids)} updated, - {len(delete_ids)} deleted)")

    return {
        "created": created_ids,
        "updated": update_ids,
        "deleted": delete_ids
    }


def main():
    global CONFIG_DIR, ES_URL, REPORT_FILE, INDICES_ENV, TOTAL_MUTATIONS, CREATE_RATIO, DELETE_RATIO, UPDATE_RATIO, MUTATE_PCT
    if len(sys.argv) > 1:
        for arg_idx, arg in enumerate(sys.argv[1:], start=1):
            if arg in ("--config-dir", "--config") and arg_idx < len(sys.argv) - 1:
                CONFIG_DIR = sys.argv[arg_idx + 1]
            elif arg in ("--indices", "-i") and arg_idx < len(sys.argv) - 1:
                INDICES_ENV = sys.argv[arg_idx + 1]
            elif arg in ("--es-url", "-e") and arg_idx < len(sys.argv) - 1:
                ES_URL = sys.argv[arg_idx + 1].rstrip("/")
            elif arg in ("--report", "-r", "--report-file") and arg_idx < len(sys.argv) - 1:
                REPORT_FILE = sys.argv[arg_idx + 1]
            elif arg in ("--total-mutations", "-n") and arg_idx < len(sys.argv) - 1:
                TOTAL_MUTATIONS = sys.argv[arg_idx + 1]
            elif arg in ("--create-ratio",) and arg_idx < len(sys.argv) - 1:
                CREATE_RATIO = float(sys.argv[arg_idx + 1])
            elif arg in ("--delete-ratio",) and arg_idx < len(sys.argv) - 1:
                DELETE_RATIO = float(sys.argv[arg_idx + 1])
            elif arg in ("--mutate-pct", "-p") and arg_idx < len(sys.argv) - 1:
                MUTATE_PCT = float(sys.argv[arg_idx + 1])
            elif not arg.startswith("-") and os.path.exists(arg):
                CONFIG_DIR = arg

    print("==================================================")
    print(">> MULTI-INDEX ES MUTATION SIMULATOR (PYTHON CORE)")
    print("==================================================")
    print(f"   Start Time     : {START_DATE}")
    print(f"   ES URL         : {ES_URL}")
    print(f"   Auth User      : {ES_USER}")
    print(f"   Config Dir     : {CONFIG_DIR}")
    print(f"   Report File    : {REPORT_FILE}")
    print(f"   Mutate Fraction: {MUTATE_PCT}")
    print(f"   C / U / D Ratio: {CREATE_RATIO} / {UPDATE_RATIO} / {DELETE_RATIO}")
    print("--------------------------------------------------")

    templates = load_templates()
    if not templates:
        print(f"[ERROR] No index templates found in '{CONFIG_DIR}'. Indices must have config files.", file=sys.stderr)
        sys.exit(1)

    if INDICES_ENV:
        indices = [i.strip() for i in INDICES_ENV.split(",") if i.strip()]
        missing = [idx for idx in indices if idx not in templates]
        if missing:
            print(f"[ERROR] The following indices do not have config files in '{CONFIG_DIR}': {missing}. No fallback allowed.", file=sys.stderr)
            sys.exit(1)
    else:
        indices = sorted(list(templates.keys()))

    print(f"[INFO] Target Indices ({len(indices)}): {', '.join(indices)}")

    tot_cr, tot_up, tot_del = 0, 0, 0
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as rf:
            for idx_idx, idx in enumerate(indices, start=1):
                res = simulate_index(idx, templates, idx_idx, len(indices), report_handle=rf)
                tot_cr += len(res["created"])
                tot_up += len(res["updated"])
                tot_del += len(res["deleted"])
                rf.flush()
    except Exception as e:
        print(f"[ERROR] Could not write report file '{REPORT_FILE}': {e}", file=sys.stderr)

    elapsed = round(time.time() - START_TIME, 2)
    end_date = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())

    print("\n==================================================")
    print(">> SIMULATION EXECUTION SUMMARY")
    print("==================================================")
    print(f"   Start Time       : {START_DATE}")
    print(f"   End Time         : {end_date}")
    print(f"   Elapsed Time     : {elapsed}s")
    print(f"   Indices Processed: {len(indices)}")
    print(f"   Total Created    : + {tot_cr} docs")
    print(f"   Total Updated    : ~ {tot_up} docs")
    print(f"   Total Deleted    : - {tot_del} docs")
    print(f"   Total Mutated    : {tot_cr + tot_up + tot_del} docs")
    print(f"   Report Saved     : {REPORT_FILE}")
    print("==================================================")


if __name__ == "__main__":
    main()
