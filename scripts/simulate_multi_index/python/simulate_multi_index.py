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
SAMPLE_FILE = os.environ.get("SAMPLE_FILE", os.path.join(SCRIPT_DIR, "sample_templates.json"))
REPORT_FILE = os.environ.get("REPORT_FILE", os.path.join(SCRIPT_DIR, "report.json"))
MUTATE_PCT = float(os.environ.get("MUTATE_PCT", "0.10"))
CREATE_RATIO = float(os.environ.get("CREATE_RATIO", "0.30"))
UPDATE_RATIO = float(os.environ.get("UPDATE_RATIO", "0.60"))
DELETE_RATIO = float(os.environ.get("DELETE_RATIO", "0.10"))
TOTAL_MUTATIONS = os.environ.get("TOTAL_MUTATIONS", "")
BATCH = int(os.environ.get("BATCH", "2000"))
SEED = int(os.environ.get("SEED", "42"))

WORDS = ["fast", "durable", "compact", "premium", "eco", "smart", "classic", "pro", "lite", "max"]


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
    rnd = random.Random(seed + seq)
    now_ts = current_iso_time()
    rand_word = rnd.choice(WORDS)
    rand_price = round(rnd.uniform(9.99, 499.99), 2)

    def process_node(node: Any) -> Any:
        if isinstance(node, dict):
            res = {k: process_node(v) for k, v in node.items()}
            if "modified_at" not in res:
                res["modified_at"] = now_ts
            return res
        elif isinstance(node, list):
            return [process_node(item) for item in node]
        elif isinstance(node, str):
            if node in ("{{price}}", "{price}"):
                return rand_price
            val = node
            val = val.replace("{{SEQ}}", str(seq)).replace("{{seq}}", str(seq)).replace("{seq}", str(seq))
            val = val.replace("{{ID}}", doc_id).replace("{{id}}", doc_id).replace("{id}", doc_id)
            val = val.replace("{{TIMESTAMP}}", now_ts).replace("{{timestamp}}", now_ts).replace("{timestamp}", now_ts)
            val = val.replace("{{random_word}}", rand_word).replace("{random_word}", rand_word)
            val = val.replace("{{name}}", f"Name {seq}").replace("{name}", f"Name {seq}")
            return val
        return node

    return process_node(template)


def load_templates() -> Dict[str, Any]:
    templates = {}

    def add_content(data: Any):
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    tmpl = v.get("create_template") or v
                    templates[k] = tmpl
                else:
                    templates[k] = v
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    idx_name = item.get("es_index") or item.get("index")
                    tmpl = item.get("create_payload") or item.get("template") or item
                    if idx_name:
                        templates[idx_name] = tmpl

    if not os.path.exists(SAMPLE_FILE):
        return templates

    if os.path.isdir(SAMPLE_FILE):
        print(f"[INFO] Scanning folder for sample JSON templates: {SAMPLE_FILE}")
        for root, _, files in os.walk(SAMPLE_FILE):
            for file in sorted(files):
                if file.endswith(".json"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            add_content(json.load(f))
                    except Exception as e:
                        print(f"[WARN] Could not read {full_path}: {e}", file=sys.stderr)
    else:
        print(f"[INFO] Reading single template file: {SAMPLE_FILE}")
        try:
            with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
                add_content(json.load(f))
        except Exception as e:
            print(f"[WARN] Could not read {SAMPLE_FILE}: {e}", file=sys.stderr)

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


def simulate_index(index: str, templates: Dict[str, Any], idx_idx: int, total_indices: int) -> Dict[str, Any]:
    print(f"\n--------------------------------------------------")
    print(f"[{idx_idx}/{total_indices}] Processing Index: '{index}'")
    print(f"--------------------------------------------------")

    print("   [1/4] Querying existing document count...")
    try:
        cnt_res = es_http("GET", f"/{index}/_count")
        total_docs = cnt_res.get("count", 0)
        print(f"         Existing docs count: {total_docs}")
    except Exception as e:
        print(f"[ERROR] Could not query index '{index}': {e}", file=sys.stderr)
        return {"created": [], "updated": [], "deleted": [], "created_samples": {}, "updated_samples": {}}

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

    tmpl = templates.get(index) or templates.get("default") or {
        "id": "doc-{{SEQ}}",
        "name": "Name {{SEQ}}",
        "created_at": "{{TIMESTAMP}}",
        "updated_at": "{{TIMESTAMP}}",
        "modified_at": "{{TIMESTAMP}}"
    }

    bulk_lines = []
    created_samples = {}
    updated_samples = {}

    # Creates
    max_seq = total_docs
    for i in range(create_n):
        seq = max_seq + i + 1
        doc_id = f"doc-{seq}"
        doc_data = render_template(tmpl, seq, doc_id, SEED)
        bulk_lines.extend([json.dumps({"index": {"_id": doc_id}}), json.dumps(doc_data, separators=(",", ":"))])
        created_ids.append(doc_id)
        if len(created_samples) < 5:
            created_samples[doc_id] = doc_data

        if len(bulk_lines) >= BATCH * 2:
            bulk_send(index, bulk_lines)
            bulk_lines = []

    # Updates
    now_ts = current_iso_time()
    for idx, doc_id in enumerate(update_ids):
        update_payload = {
            "updated_at": now_ts,
            "modified_at": now_ts,
            "simulated_update": True,
            "name": f"Name {idx + 1} UPDATED"
        }
        bulk_lines.extend([json.dumps({"update": {"_id": doc_id}}), json.dumps({"doc": update_payload}, separators=(",", ":"))])
        if len(updated_samples) < 5:
            updated_samples[doc_id] = update_payload

        if len(bulk_lines) >= BATCH * 2:
            bulk_send(index, bulk_lines)
            bulk_lines = []

    # Deletes
    for doc_id in delete_ids:
        bulk_lines.append(json.dumps({"delete": {"_id": doc_id}}))
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
        "deleted": delete_ids,
        "created_samples": created_samples,
        "updated_samples": updated_samples
    }


def main():
    print("==================================================")
    print(">> MULTI-INDEX ES MUTATION SIMULATOR (PYTHON CORE)")
    print("==================================================")
    print(f"   Start Time     : {START_DATE}")
    print(f"   ES URL         : {ES_URL}")
    print(f"   Auth User      : {ES_USER}")
    print(f"   Sample Path    : {SAMPLE_FILE}")
    print(f"   Report File    : {REPORT_FILE}")
    print(f"   Mutate Fraction: {MUTATE_PCT}")
    print(f"   C / U / D Ratio: {CREATE_RATIO} / {UPDATE_RATIO} / {DELETE_RATIO}")
    print("--------------------------------------------------")

    templates = load_templates()
    if INDICES_ENV:
        indices = [i.strip() for i in INDICES_ENV.split(",") if i.strip()]
    elif templates:
        indices = [k for k in templates.keys() if k != "default"]
    else:
        indices = ["bench-es9"]

    print(f"[INFO] Target Indices ({len(indices)}): {', '.join(indices)}")
    report_data = {}

    tot_cr, tot_up, tot_del = 0, 0, 0
    for idx_idx, idx in enumerate(indices, start=1):
        res = simulate_index(idx, templates, idx_idx, len(indices))
        report_data[idx] = res
        tot_cr += len(res["created"])
        tot_up += len(res["updated"])
        tot_del += len(res["deleted"])

    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Could not save report: {e}", file=sys.stderr)

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
