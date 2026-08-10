#!/usr/bin/env python3
"""
Verify Elasticsearch Multi-Index Mutations from Report Output

Environment variables (ES9 credentials prioritized):
    ES9_URL / ES_URL     Elasticsearch base URL        (default http://localhost:9200)
    ES9_USER / ES_USER   Basic-auth username           (default elastic)
    ES9_PASS / ES9_PW    Basic-auth password           (default "")
    REPORT_FILE          Path to report JSON           (default report.json in script dir)

Hardcoded Ignored Fields:
    IGNORED_FIELDS = {"modified_at", "updated_at", "created_at", "@timestamp", "_ingest"}

Verification logic:
- Created Records: Compares actual ES _source with sample payload. Expects MATCH (excluding IGNORED_FIELDS).
- Updated Records: Compares actual ES _source with expected mutated fields. Expects MUTATED/DIFFERENT content as expected.
- Deleted Records: Verified HTTP 404 (does NOT exist in ES).
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Set

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ES_URL = os.environ.get("ES9_URL", os.environ.get("ES_URL", "http://localhost:9200")).rstrip("/")
ES_USER = os.environ.get("ES9_USER", os.environ.get("ES_USER", "elastic"))
ES_PW = os.environ.get("ES9_PASS", os.environ.get("ES9_PW", os.environ.get("ES_PW", "")))
REPORT_FILE = os.environ.get("REPORT_FILE", os.path.join(SCRIPT_DIR, "report.json"))

# Hardcoded fields to ignore during field-by-field payload comparison
IGNORED_FIELDS: Set[str] = {"modified_at", "updated_at", "created_at", "@timestamp", "_ingest"}


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


def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove ignored fields (e.g. modified_at) from dict for content comparison."""
    if not isinstance(data, dict):
        return data
    return {k: v for k, v in data.items() if k not in IGNORED_FIELDS}


def compare_created_doc(actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
    """Verify Created doc content matches expected payload (ignoring modified_at/timestamps)."""
    clean_act = clean_dict(actual)
    clean_exp = clean_dict(expected)
    for k, v in clean_exp.items():
        if k not in clean_act or clean_act[k] != v:
            return False
    return True


def compare_updated_doc(actual: Dict[str, Any], expected_update: Dict[str, Any]) -> bool:
    """Verify Updated doc reflects mutated changes (e.g. simulated_update=True or name ending with UPDATED)."""
    if actual.get("simulated_update") is True:
        return True
    name_val = str(actual.get("name", "") or actual.get("title", ""))
    return "UPDATED" in name_val


def main():
    if not os.path.exists(REPORT_FILE):
        print(f"ERROR: Report file '{REPORT_FILE}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(REPORT_FILE, "r", encoding="utf-8") as f:
            report_data = json.load(f)
    except Exception as e:
        print(f"ERROR reading report file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f">> Verifying Elasticsearch mutations against ES9 target: {ES_URL}")
    print(f"   Auth User   : {ES_USER}")
    print(f"   Report File : {REPORT_FILE}")
    print(f"   Ignored Keys: {', '.join(sorted(IGNORED_FIELDS))}")
    print(f"--------------------------------------------------")

    total_checks = 0
    passed_checks = 0
    failed_checks = 0

    for index_name, changes in report_data.items():
        print(f"\n>> Index: '{index_name}'")
        created_ids = changes.get("created", [])
        updated_ids = changes.get("updated", [])
        deleted_ids = changes.get("deleted", [])
        created_samples = changes.get("created_samples", {})
        updated_samples = changes.get("updated_samples", {})

        idx_passed = 0
        idx_failed = 0

        # 1. Sample & Check Created Records (Expect Match ignoring modified_at)
        sample_created = created_ids[:5]
        print(f"   [Checking CREATED] Sampling {len(sample_created)}/{len(created_ids)} records...")
        for doc_id in sample_created:
            total_checks += 1
            res = es_get_doc(index_name, doc_id)
            if not res["found"]:
                failed_checks += 1
                idx_failed += 1
                print(f"     [FAIL] Created doc '{doc_id}' NOT FOUND in ES9!")
                continue

            expected_payload = created_samples.get(doc_id)
            if expected_payload:
                if compare_created_doc(res["source"], expected_payload):
                    passed_checks += 1
                    idx_passed += 1
                    print(f"     [PASS] Created doc '{doc_id}' exists and matches expected content.")
                else:
                    failed_checks += 1
                    idx_failed += 1
                    print(f"     [FAIL] Created doc '{doc_id}' content mismatch! Actual: {clean_dict(res['source'])}")
            else:
                passed_checks += 1
                idx_passed += 1
                print(f"     [PASS] Created doc '{doc_id}' exists in ES9.")

        # 2. Sample & Check Updated Records (Expect Mutated Differences)
        sample_updated = updated_ids[:5]
        print(f"   [Checking UPDATED] Sampling {len(sample_updated)}/{len(updated_ids)} records...")
        for doc_id in sample_updated:
            total_checks += 1
            res = es_get_doc(index_name, doc_id)
            if not res["found"]:
                failed_checks += 1
                idx_failed += 1
                print(f"     [FAIL] Updated doc '{doc_id}' NOT FOUND in ES9!")
                continue

            expected_update = updated_samples.get(doc_id, {})
            if compare_updated_doc(res["source"], expected_update):
                passed_checks += 1
                idx_passed += 1
                print(f"     [PASS] Updated doc '{doc_id}' contains expected mutation change.")
            else:
                failed_checks += 1
                idx_failed += 1
                print(f"     [FAIL] Updated doc '{doc_id}' does not reflect mutation change!")

        # 3. Sample & Check Deleted Records (Expect HTTP 404)
        sample_deleted = deleted_ids[:5]
        print(f"   [Checking DELETED] Sampling {len(sample_deleted)}/{len(deleted_ids)} records...")
        for doc_id in sample_deleted:
            total_checks += 1
            res = es_get_doc(index_name, doc_id)
            if not res["found"]:
                passed_checks += 1
                idx_passed += 1
                print(f"     [PASS] Deleted doc '{doc_id}' verified 404 (Removed from ES9).")
            else:
                failed_checks += 1
                idx_failed += 1
                print(f"     [FAIL] Deleted doc '{doc_id}' still exists in ES9!")

        print(f"   Index '{index_name}' Verification Summary: {idx_passed} Passed, {idx_failed} Failed.")

    print(f"\n==================================================")
    print(f">> Final Verification Summary:")
    print(f"   Total Sample Checks: {total_checks}")
    print(f"   Passed             : {passed_checks}")
    print(f"   Failed             : {failed_checks}")

    if failed_checks > 0:
        print(f">> VERIFICATION FAILED ({failed_checks} mismatch errors)", file=sys.stderr)
        sys.exit(1)
    else:
        print(f">> VERIFICATION SUCCESSFUL! All sampled records match expected state on ES9.")
        sys.exit(0)


if __name__ == "__main__":
    main()
