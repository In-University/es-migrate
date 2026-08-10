#!/usr/bin/env python3
"""
Multi-Index ES Mutation Simulator

Environment variables:
    ES_URL       Elasticsearch base URL        (default http://localhost:9200)
    ES_USER      Basic-auth username           (default elastic)
    ES_PASS      Basic-auth password           (default "")
    INDICES      Target indices (comma-sep)    (default bench-es9)
    SAMPLE_FILE  Path to sample JSON file or   (default sample_templates.json in script dir)
                 folder containing JSON files
    REPORT_FILE  Path to save simple report    (default report.json in script dir)
    MUTATE_PCT   Fraction of docs to mutate    (default 0.10)
    CREATE_RATIO Share of Creates              (default 0.10)
    UPDATE_RATIO Share of Updates              (default 0.70)
    DELETE_RATIO Share of Deletes              (default 0.20)
    BATCH        Docs per _bulk request        (default 2000)
    SEED         Random seed                   (default 42)
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ES_URL = os.environ.get("ES_URL", "http://localhost:9200").rstrip("/")
ES_USER = os.environ.get("ES_USER", "elastic")
ES_PW = os.environ.get("ES_PASS", os.environ.get("ES_PW", ""))
INDICES_ENV = os.environ.get("INDICES", os.environ.get("INDEX", ""))
SAMPLE_FILE = os.environ.get("SAMPLE_FILE", os.path.join(SCRIPT_DIR, "sample_templates.json"))
REPORT_FILE = os.environ.get("REPORT_FILE", os.path.join(SCRIPT_DIR, "report.json"))
MUTATE_PCT = float(os.environ.get("MUTATE_PCT", "0.10"))
CREATE_RATIO = float(os.environ.get("CREATE_RATIO", "0.10"))
UPDATE_RATIO = float(os.environ.get("UPDATE_RATIO", "0.70"))
DELETE_RATIO = float(os.environ.get("DELETE_RATIO", "0.20"))
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
            val = val.replace("{{seq}}", str(seq)).replace("{seq}", str(seq))
            val = val.replace("{{id}}", doc_id).replace("{id}", doc_id)
            val = val.replace("{{timestamp}}", now_ts).replace("{timestamp}", now_ts)
            val = val.replace("{{random_word}}", rand_word).replace("{random_word}", rand_word)
            val = val.replace("{{name}}", f"Name {seq}").replace("{name}", f"Name {seq}")
            return val
        return node

    return process_node(template)


def load_templates() -> Dict[str, Any]:
    """Load JSON sample templates from either a single file or an entire folder."""
    templates = {}

    def add_content(data: Any):
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    # Check if v is wrapped in create_template
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
        print(f"Warning: SAMPLE_FILE path '{SAMPLE_FILE}' does not exist.", file=sys.stderr)
        return templates

    if os.path.isdir(SAMPLE_FILE):
        print(f">> Scanning folder for sample JSON templates: {SAMPLE_FILE}")
        for root, _, files in os.walk(SAMPLE_FILE):
            for file in sorted(files):
                if file.endswith(".json"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = json.load(f)
                            add_content(content)
                    except Exception as e:
                        print(f"Warning: Could not read {full_path}: {e}", file=sys.stderr)
    else:
        try:
            with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
                add_content(content)
        except Exception as e:
            print(f"Warning: Could not read {SAMPLE_FILE}: {e}", file=sys.stderr)

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


def simulate_index(index: str, templates: Dict[str, Any]) -> Dict[str, Any]:
    print(f">> Simulating index '{index}' on {ES_URL}...")

    try:
        cnt_res = es_http("GET", f"/{index}/_count")
        total_docs = cnt_res.get("count", 0)
    except Exception as e:
        print(f"ERROR: Could not query index '{index}': {e}", file=sys.stderr)
        return {"created": [], "updated": [], "deleted": [], "created_samples": {}, "updated_samples": {}}

    existing_ids = []
    if total_docs > 0:
        search_res = es_http("GET", f"/{index}/_search?size=5000&_source=false")
        hits = search_res.get("hits", {}).get("hits", [])
        existing_ids = [h["_id"] for h in hits]

    if total_docs == 0:
        create_n = 10
        update_n = 0
        delete_n = 0
    else:
        touch_count = max(1, int(total_docs * MUTATE_PCT))
        create_n = int(touch_count * CREATE_RATIO)
        delete_n = min(len(existing_ids), int(touch_count * DELETE_RATIO))
        update_n = max(0, touch_count - create_n - delete_n)

    rnd = random.Random(SEED + hash(index))
    shuffled_ids = list(existing_ids)
    rnd.shuffle(shuffled_ids)

    update_ids = shuffled_ids[:update_n]
    delete_ids = shuffled_ids[update_n:update_n + delete_n]
    created_ids = []

    tmpl = templates.get(index) or templates.get("default") or {
        "id": "doc-{{seq}}",
        "name": "Name {{seq}}",
        "created_at": "{{timestamp}}",
        "updated_at": "{{timestamp}}",
        "modified_at": "{{timestamp}}"
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

    if bulk_lines:
        bulk_send(index, bulk_lines)

    es_http("POST", f"/{index}/_refresh")

    print(f"   Done '{index}': +{len(created_ids)} created, ~{len(update_ids)} updated, -{len(delete_ids)} deleted")

    return {
        "created": created_ids,
        "updated": update_ids,
        "deleted": delete_ids,
        "created_samples": created_samples,
        "updated_samples": updated_samples
    }


def main():
    templates = load_templates()

    # Determine target indices: from env if set, else from loaded template keys (excluding 'default')
    if INDICES_ENV:
        indices = [i.strip() for i in INDICES_ENV.split(",") if i.strip()]
    elif templates:
        indices = [k for k in templates.keys() if k != "default"]
    else:
        indices = ["bench-es9"]

    if not indices:
        print("ERROR: No target indices specified or discovered.", file=sys.stderr)
        sys.exit(1)

    print(f">> Target Indices ({len(indices)}): {', '.join(indices)}")
    simple_report = {}

    for idx in indices:
        simple_report[idx] = simulate_index(idx, templates)

    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(simple_report, f, indent=2)
        print(f">> Report saved to: {REPORT_FILE}")
    except Exception as e:
        print(f"ERROR saving report: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
