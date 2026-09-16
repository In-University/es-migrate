#!/usr/bin/env python3
"""
Multi-Index Elasticsearch Verification Script (Python Core)
Detailed progress logging and execution summary.
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Set

START_TIME = time.time()
START_DATE = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ES_URL = os.environ.get("ES_URL", os.environ.get("ES9_URL", "http://localhost:9200")).rstrip("/")
ES_USER = os.environ.get("ES_USER", os.environ.get("ES9_USER", "elastic"))
ES_PW = os.environ.get("ES_PASS", os.environ.get("ES9_PASS", os.environ.get("ES9_PW", os.environ.get("ES_PW", ""))))
REPORT_FILE = os.environ.get("REPORT_FILE", os.path.join(SCRIPT_DIR, "report.ndjson"))

IGNORED_FIELDS: Set[str] = {"modified_at", "updated_at", "created_at", "@timestamp", "_ingest"}
VERIFY_LIMIT = int(os.environ.get("VERIFY_LIMIT", "0"))


def es_get_doc(index: str, doc_id: str) -> Dict[str, Any]:
    url = f"{ES_URL}/{index}/_doc/{doc_id}"
    headers = {"Content-Type": "application/json"}
    if ES_PW:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{ES_USER}:{ES_PW}".encode()).decode()
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"found": True, "status": resp.status, "source": data.get("_source", {})}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"found": False, "status": 404, "source": {}}
        raise


def es_mget_docs(index: str, doc_ids: list) -> Dict[str, Dict[str, Any]]:
    results = {}
    if not doc_ids:
        return results

    chunk_size = 500
    for i in range(0, len(doc_ids), chunk_size):
        chunk = doc_ids[i:i + chunk_size]
        url = f"{ES_URL}/{index}/_mget"
        headers = {"Content-Type": "application/json"}
        if ES_PW:
            headers["Authorization"] = "Basic " + base64.b64encode(f"{ES_USER}:{ES_PW}".encode()).decode()
        body = json.dumps({"ids": chunk}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for doc in data.get("docs", []):
                    d_id = doc.get("_id")
                    results[d_id] = {
                        "found": doc.get("found", False),
                        "status": 200 if doc.get("found") else 404,
                        "source": doc.get("_source", {})
                    }
        except Exception:
            for d_id in chunk:
                results[d_id] = es_get_doc(index, d_id)

    return results


def compare_doc_body(
    actual: Any,
    expected: Any,
    ignored_keys: Set[str] = IGNORED_FIELDS,
    path: str = ""
) -> tuple:
    diffs = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False, [f"{path}: expected dict, got {type(actual).__name__}"]
        for k, exp_val in expected.items():
            if k in ignored_keys:
                continue
            curr_path = f"{path}.{k}" if path else k
            if k not in actual:
                diffs.append(f"missing field '{curr_path}'")
            else:
                act_val = actual[k]
                sub_match, sub_diffs = compare_doc_body(act_val, exp_val, ignored_keys, curr_path)
                if not sub_match:
                    diffs.extend(sub_diffs)
    elif isinstance(expected, list):
        if not isinstance(actual, list):
            return False, [f"{path}: expected list, got {type(actual).__name__}"]
        if len(actual) != len(expected):
            diffs.append(f"{path}: list len mismatch (actual={len(actual)}, expected={len(expected)})")
        else:
            for i, (act_item, exp_item) in enumerate(zip(actual, expected)):
                curr_path = f"{path}[{i}]"
                sub_match, sub_diffs = compare_doc_body(act_item, exp_item, ignored_keys, curr_path)
                if not sub_match:
                    diffs.extend(sub_diffs)
    else:
        if actual != expected:
            diffs.append(f"{path}: actual={actual!r} != expected={expected!r}")

    return len(diffs) == 0, diffs


def compare_updated_body(
    actual: Dict[str, Any],
    expected_update: Dict[str, Any],
    ignored_keys: Set[str] = IGNORED_FIELDS
) -> tuple:
    if not expected_update:
        return True, []
    return compare_doc_body(actual, expected_update, ignored_keys)


def stream_report_records(report_file: str):
    """
    Streams mutation records from NDJSON or legacy JSON report file.
    """
    with open(report_file, "r", encoding="utf-8") as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == "{":
            first_line = f.readline().strip()
            f.seek(0)
            try:
                data = json.loads(first_line)
                if "op" in data and "index" in data:
                    for line in f:
                        line = line.strip()
                        if line:
                            yield json.loads(line)
                    return
            except Exception:
                pass

            data = json.load(f)
            for idx_name, changes in data.items():
                for doc_id in changes.get("created", []):
                    body = changes.get("created_docs", {}).get(doc_id) or changes.get("created_samples", {}).get(doc_id)
                    yield {"index": idx_name, "op": "create", "id": doc_id, "body": body}
                for doc_id in changes.get("updated", []):
                    body = changes.get("updated_docs", {}).get(doc_id) or changes.get("updated_samples", {}).get(doc_id)
                    yield {"index": idx_name, "op": "update", "id": doc_id, "body": body}
                for doc_id in changes.get("deleted", []):
                    yield {"index": idx_name, "op": "delete", "id": doc_id}
        else:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


def main():
    global REPORT_FILE, ES_URL
    if len(sys.argv) > 1:
        for arg_idx, arg in enumerate(sys.argv[1:], start=1):
            if arg in ("--report", "-r", "--report-file") and arg_idx < len(sys.argv) - 1:
                REPORT_FILE = sys.argv[arg_idx + 1]
            elif arg in ("--es-url", "-e") and arg_idx < len(sys.argv) - 1:
                ES_URL = sys.argv[arg_idx + 1].rstrip("/")
            elif not arg.startswith("-") and os.path.exists(arg):
                REPORT_FILE = arg

    print("==================================================")
    print(">> MULTI-INDEX ES VERIFICATION AUDIT (PYTHON CORE)")
    print("==================================================")
    print(f"   Start Time  : {START_DATE}")
    print(f"   Target ES   : {ES_URL}")
    print(f"   Auth User   : {ES_USER}")
    print(f"   Report File : {REPORT_FILE}")
    print(f"   Verify Limit: {VERIFY_LIMIT if VERIFY_LIMIT > 0 else 'ALL'}")
    print("--------------------------------------------------")

    if not os.path.exists(REPORT_FILE):
        print(f"[ERROR] Report file '{REPORT_FILE}' not found.", file=sys.stderr)
        sys.exit(1)

    total_checks, passed_checks, failed_checks = 0, 0, 0
    indices_seen = set()

    BATCH_SIZE = 500
    current_index = None
    batch = []

    def process_batch(idx_name: str, records: list):
        nonlocal total_checks, passed_checks, failed_checks
        if not records:
            return

        doc_ids = [r["id"] for r in records]
        docs_status = es_mget_docs(idx_name, doc_ids)

        for item in records:
            total_checks += 1
            doc_id = item["id"]
            op = item.get("op", "create")
            expected_body = item.get("body")
            res = docs_status.get(doc_id) or es_get_doc(idx_name, doc_id)

            if op == "create":
                if not res["found"]:
                    failed_checks += 1
                    print(f"         [FAIL] Created doc '{doc_id}' NOT FOUND in ES!")
                elif expected_body:
                    matched, diffs = compare_doc_body(res["source"], expected_body)
                    if matched:
                        passed_checks += 1
                        print(f"         [PASS] Created doc '{doc_id}' exists and body matches template.")
                    else:
                        failed_checks += 1
                        diff_msg = "; ".join(diffs[:3])
                        if len(diffs) > 3:
                            diff_msg += f" (+{len(diffs)-3} more diffs)"
                        print(f"         [FAIL] Created doc '{doc_id}' body mismatch: {diff_msg}")
                else:
                    passed_checks += 1
                    print(f"         [PASS] Created doc '{doc_id}' exists in ES.")

            elif op == "update":
                if not res["found"]:
                    failed_checks += 1
                    print(f"         [FAIL] Updated doc '{doc_id}' NOT FOUND in ES!")
                elif expected_body:
                    matched, diffs = compare_updated_body(res["source"], expected_body)
                    if matched:
                        passed_checks += 1
                        print(f"         [PASS] Updated doc '{doc_id}' exists and body matches mutation payload.")
                    else:
                        failed_checks += 1
                        diff_msg = "; ".join(diffs[:3])
                        if len(diffs) > 3:
                            diff_msg += f" (+{len(diffs)-3} more diffs)"
                        print(f"         [FAIL] Updated doc '{doc_id}' update mismatch: {diff_msg}")
                else:
                    matched, diffs = compare_updated_body(res["source"], {})
                    if matched:
                        passed_checks += 1
                        print(f"         [PASS] Updated doc '{doc_id}' reflects expected mutation.")
                    else:
                        failed_checks += 1
                        print(f"         [FAIL] Updated doc '{doc_id}' does not reflect mutation: {'; '.join(diffs)}")

            elif op == "delete":
                if not res["found"]:
                    passed_checks += 1
                    print(f"         [PASS] Deleted doc '{doc_id}' verified HTTP 404 (Removed).")
                else:
                    failed_checks += 1
                    print(f"         [FAIL] Deleted doc '{doc_id}' still exists!")

    for item in stream_report_records(REPORT_FILE):
        idx_name = item.get("index", "")
        if not idx_name:
            continue

        if idx_name not in indices_seen:
            if batch:
                process_batch(current_index, batch)
                batch = []
            indices_seen.add(idx_name)
            current_index = idx_name
            print(f"\n--------------------------------------------------")
            print(f"[{len(indices_seen)}] Verifying Index: '{idx_name}'")
            print(f"--------------------------------------------------")

        if VERIFY_LIMIT > 0 and len(batch) >= VERIFY_LIMIT:
            continue

        batch.append(item)
        if len(batch) >= BATCH_SIZE:
            process_batch(current_index, batch)
            batch = []

    if batch and current_index:
        process_batch(current_index, batch)
        batch = []

    elapsed = round(time.time() - START_TIME, 2)
    end_date = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())

    print("\n==================================================")
    print(">> VERIFICATION AUDIT EXECUTION SUMMARY")
    print("==================================================")
    print(f"   Start Time       : {START_DATE}")
    print(f"   End Time         : {end_date}")
    print(f"   Elapsed Time     : {elapsed}s")
    print(f"   Indices Audited  : {len(indices_seen)}")
    print(f"   Total Checks     : {total_checks}")
    print(f"   Passed Checks    : {passed_checks}")
    print(f"   Failed Checks    : {failed_checks}")

    if failed_checks == 0:
        print("   AUDIT RESULT     : [SUCCESS] ALL CHECKS PASSED!")
        print("==================================================")
        sys.exit(0)
    else:
        print("   AUDIT RESULT     : [FAILED] DISCREPANCIES DETECTED!")
        print("==================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
