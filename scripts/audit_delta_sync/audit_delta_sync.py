#!/usr/bin/env python3
"""
audit_delta_sync.py - Dynamic Order Elasticsearch Auditor with Strict ES Search API (Bool Must Query).

Elasticsearch Query Strategy:
  - Queries Elasticsearch strictly using the Search API with a boolean term query:
      POST <es_url>/<es_index>/_search
      Payload: { "query": { "bool": { "must": [ { "term": { <id_field>: <entity_id> } } ] } } }
  - Strict: No fallback to GET /_doc path.

Usage:
  python audit_delta_sync.py --target-url http://127.0.0.1:9899 --es-url http://127.0.0.1:9899 --config configs
"""

import argparse
import base64
import glob
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ESAuditor")


# ============================================================================
# DEFAULTS (TIER 3)
# ============================================================================
DEFAULT_TARGET_URL = "http://127.0.0.1:8899"
DEFAULT_ES_URL = "http://127.0.0.1:8899"
DEFAULT_ES_USER = ""
DEFAULT_ES_PASS = ""
DEFAULT_CONFIG_PATH = "configs"
DEFAULT_COOKIE = ""
DEFAULT_WORKERS = 20

HARDCODED_MODIFIED_AT_FIELD = "modified_at"
DEFAULT_ID_FIELD = "id"


# ============================================================================
# 1. STEP DEFINITION & DYNAMIC ROUTE CONFIG
# ============================================================================

@dataclass
class AuditStep:
    name: str                                  # e.g. "CREATE", "UPDATE", "PATCH", "DELETE"
    method: str                                # e.g. "POST", "PUT", "PATCH", "DELETE"
    path: str                                  # e.g. "/api/v1/invoices" or "/api/v1/invoices/{id}"
    payload: Optional[Dict[str, Any]] = None   # JSON request body
    es_check: Optional[Dict[str, Any]] = None  # Expected field values in ES document _source


@dataclass
class BlackboxRouteDefinition:
    base_path: str                            # Primary resource URI prefix (e.g. "/api/v1/billing/invoices")
    es_index: str = ""                        # ES index name
    id_field: str = DEFAULT_ID_FIELD          # Key field name (e.g., "id", "user_id", "invoice_id")
    steps: List[AuditStep] = field(default_factory=list)
    headers: Dict[str, str] = None
    cookies: Dict[str, str] = None

    def get_delete_endpoint(self, entity_id: str) -> Tuple[str, str]:
        """Resolves DELETE endpoint for teardown cleanup."""
        for step in self.steps:
            if step.name == "DELETE" or step.method == "DELETE":
                path = step.path
                if "{id}" in path:
                    path = path.format(id=entity_id)
                elif entity_id and not path.endswith(f"/{entity_id}"):
                    path = f"{path.rstrip('/')}/{entity_id}"
                return step.method, path
        
        # Fallback default delete path
        return "DELETE", f"{self.base_path.rstrip('/')}/{entity_id}"

    @classmethod
    def from_dict(cls, data: dict) -> "BlackboxRouteDefinition":
        base_path = data["base_path"]
        
        derived_index = data.get("es_index", "")
        if not derived_index:
            parts = base_path.strip("/").split("/")
            derived_index = "_".join(parts[-2:]).replace("-", "_")

        id_field = data.get("id_field", DEFAULT_ID_FIELD)

        steps: List[AuditStep] = []
        
        if "steps" in data and isinstance(data["steps"], list):
            for idx, s in enumerate(data["steps"]):
                action_name = s.get("name") or s.get("action") or f"STEP_{idx+1}"
                steps.append(AuditStep(
                    name=action_name.upper(),
                    method=s.get("method", "POST").upper(),
                    path=s.get("path", base_path),
                    payload=s.get("payload", s.get("create_payload")),
                    es_check=s.get("es_check", s.get("es_checks"))
                ))
        else:
            es_checks = data.get("es_checks", {})

            # CREATE Step
            c_payload = data.get("create_payload")
            c_path = data.get("create_path") or base_path
            c_method = data.get("create_method", "POST").upper()
            if c_payload is not None or "create_path" in data:
                steps.append(AuditStep(
                    name="CREATE",
                    method=c_method,
                    path=c_path,
                    payload=c_payload,
                    es_check=es_checks.get("create", c_payload)
                ))

            # UPDATE Step
            u_payload = data.get("update_payload")
            u_path = data.get("update_path") or f"{base_path.rstrip('/')}/{{id}}"
            u_method = data.get("update_method", "PUT").upper()
            if u_payload is not None or "update_path" in data:
                steps.append(AuditStep(
                    name="UPDATE",
                    method=u_method,
                    path=u_path,
                    payload=u_payload,
                    es_check=es_checks.get("update", u_payload)
                ))

            # PATCH Step
            p_payload = data.get("patch_payload")
            p_path = data.get("patch_path") or f"{base_path.rstrip('/')}/{{id}}"
            p_method = data.get("patch_method", "PATCH").upper()
            if p_payload is not None or "patch_path" in data:
                steps.append(AuditStep(
                    name="PATCH",
                    method=p_method,
                    path=p_path,
                    payload=p_payload,
                    es_check=es_checks.get("patch", p_payload)
                ))

            # DELETE Step
            d_path = data.get("delete_path") or f"{base_path.rstrip('/')}/{{id}}"
            d_method = data.get("delete_method", "DELETE").upper()
            if "delete_payload" in data or "delete_path" in data or "delete" in es_checks or len(steps) > 0:
                steps.append(AuditStep(
                    name="DELETE",
                    method=d_method,
                    path=d_path,
                    payload=data.get("delete_payload"),
                    es_check=es_checks.get("delete")
                ))

        return cls(
            base_path=base_path,
            es_index=derived_index,
            id_field=id_field,
            steps=steps,
            headers=data.get("headers", {}),
            cookies=data.get("cookies", {})
        )


def load_route_configs(config_path: str) -> List[BlackboxRouteDefinition]:
    """Loads configs from either a single .json file OR a directory tree."""
    definitions = []
    
    if os.path.isfile(config_path):
        files = [config_path]
    elif os.path.isdir(config_path):
        files = glob.glob(os.path.join(config_path, "**", "*.json"), recursive=True)
    else:
        logger.error(f"Config path '{config_path}' does not exist.")
        return []

    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = json.load(f)
                items = content if isinstance(content, list) else [content]
                for item in items:
                    definitions.append(BlackboxRouteDefinition.from_dict(item))
        except Exception as e:
            logger.error(f"Failed to parse config file {fpath}: {e}")
            
    return definitions


# ============================================================================
# 2. HTTP & ELASTICSEARCH CLIENTS
# ============================================================================

def parse_iso_timestamp(ts_val: Any) -> datetime:
    if not ts_val:
        raise ValueError("Timestamp value is empty or None")
    s = str(ts_val)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class BlackboxClient:
    """REST API & Elasticsearch HTTP Client supporting Cookies & ES Basic Auth."""
    
    def __init__(self, target_url: str, es_url: str, es_user: str = "", es_pass: str = "", default_headers: Optional[Dict[str, str]] = None, cookie_str: str = ""):
        self.target_url = target_url.rstrip("/")
        
        parsed_es = urllib.parse.urlparse(es_url)
        if parsed_es.username and not es_user:
            es_user = parsed_es.username
        if parsed_es.password and not es_pass:
            es_pass = parsed_es.password

        if parsed_es.username:
            clean_netloc = parsed_es.hostname
            if parsed_es.port:
                clean_netloc += f":{parsed_es.port}"
            self.es_url = f"{parsed_es.scheme}://{clean_netloc}{parsed_es.path}".rstrip("/")
        else:
            self.es_url = es_url.rstrip("/")

        self.es_user = es_user
        self.es_pass = es_pass
        self.default_headers = default_headers or {"Content-Type": "application/json"}
        if cookie_str:
            self.default_headers["Cookie"] = cookie_str

    def api_request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None, custom_headers: Optional[Dict[str, str]] = None, custom_cookies: Optional[Dict[str, str]] = None) -> Tuple[int, Dict[str, Any]]:
        url = self.target_url + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        
        headers = dict(self.default_headers)
        if custom_headers:
            headers.update(custom_headers)

        if custom_cookies:
            cookie_items = [f"{k}={v}" for k, v in custom_cookies.items()]
            existing_cookie = headers.get("Cookie", "")
            combined_cookie = f"{existing_cookie}; {'; '.join(cookie_items)}" if existing_cookie else "; ".join(cookie_items)
            headers["Cookie"] = combined_cookie

        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return resp.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            try:
                raw = e.read().decode("utf-8")
                res_data = json.loads(raw) if raw else {}
            except Exception:
                res_data = {"error": f"HTTP {e.code}"}
            return e.code, res_data
        except Exception as e:
            return 500, {"error": str(e)}

    def fetch_es_document(self, es_index: str, id_field: str, entity_id: str, retries: int = 3, delay_sec: float = 0.1) -> Tuple[bool, Dict[str, Any]]:
        """
        Strictly queries Elasticsearch via Search API using bool must term query:
          POST <es_url>/<es_index>/_search
          Payload: { "query": { "bool": { "must": [ { "term": { <id_field>: <entity_id> } } ] } } }
        """
        search_url = f"{self.es_url}/{es_index}/_search"
        headers = {"Content-Type": "application/json"}
        
        if self.es_user or self.es_pass:
            auth_str = f"{self.es_user}:{self.es_pass}"
            b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {b64_auth}"

        # Strict Query: POST /{es_index}/_search with { "query": { "bool": { "must": [ { "term": { id_field: entity_id } } ] } } }
        search_payload = json.dumps({
            "query": {
                "bool": {
                    "must": [
                        { "term": { id_field: entity_id } }
                    ]
                }
            }
        }).encode("utf-8")

        for attempt in range(retries):
            try:
                req = urllib.request.Request(search_url, data=search_payload, method="POST", headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw) if raw else {}
                    hits = data.get("hits", {}).get("hits", [])
                    if hits:
                        source = hits[0].get("_source", {})
                        return True, source
            except Exception:
                pass

            time.sleep(delay_sec)
            
        return False, {}


# ============================================================================
# 3. ELASTICSEARCH DELTA SYNC AUDITOR
# ============================================================================

class ESAuditor:
    """Audits Backend REST API status codes + ES document fields with Safe Teardown Rollback."""
    
    def __init__(self, client: BlackboxClient):
        self.client = client

    def _verify_es_field_values(self, step_name: str, es_doc: Dict[str, Any], expected_fields: Optional[Dict[str, Any]]) -> List[str]:
        errs = []
        if not expected_fields:
            return errs
            
        for key, expected_val in expected_fields.items():
            if key == HARDCODED_MODIFIED_AT_FIELD:
                continue
            actual_val = es_doc.get(key)
            if actual_val != expected_val:
                errs.append(f"ES Field mismatch on {step_name}: field '{key}' expected '{expected_val}', got '{actual_val}'")
        return errs

    def audit_route(self, route: BlackboxRouteDefinition) -> Tuple[bool, List[str]]:
        errors = []
        es_index = route.es_index
        pk = route.id_field
        entity_id = ""
        completed_cleanly = False

        if not route.steps:
            return False, [f"No steps defined for route {route.base_path}"]

        prev_timestamp: Optional[datetime] = None
        prev_step_name: str = ""

        try:
            for step_idx, step in enumerate(route.steps, start=1):
                step_name = f"Step {step_idx} [{step.name}]"

                path = step.path
                if "{id}" in path:
                    path = path.format(id=entity_id)
                elif entity_id and step_idx > 1 and not path.endswith(f"/{entity_id}"):
                    path = f"{path.rstrip('/')}/{entity_id}"

                t_req_start = datetime.now(timezone.utc)

                status, res_api = self.client.api_request(step.method, path, step.payload, route.headers, route.cookies)
                if status not in (200, 201, 204):
                    errors.append(f"{step.method} {path} ({step_name}) Backend API returned status {status}: {res_api}")
                    break

                if not entity_id:
                    extracted_id = str(res_api.get(pk) or (step.payload.get(pk) if step.payload else ""))
                    if extracted_id and extracted_id != "None":
                        entity_id = extracted_id
                    else:
                        errors.append(f"Unable to extract primary key field '{pk}' from {step_name} response/payload")
                        break

                time.sleep(0.01)

                # Strictly query Elasticsearch via Search API (bool must term query matching pk: entity_id)
                found, es_doc = self.client.fetch_es_document(es_index, pk, entity_id)
                if not found:
                    if step.name == "DELETE":
                        completed_cleanly = True
                        break
                    else:
                        errors.append(f"ES Ingestion Error: Document with {pk}='{entity_id}' missing in ES index '{es_index}' on {step_name}")
                        break

                if step.es_check:
                    errors.extend(self._verify_es_field_values(step_name, es_doc, step.es_check))

                ts_raw = es_doc.get(HARDCODED_MODIFIED_AT_FIELD)
                if not ts_raw:
                    errors.append(f"Missing timestamp field '{HARDCODED_MODIFIED_AT_FIELD}' in ES doc ({es_index}/{entity_id}) on {step_name}")
                    break

                try:
                    t_es = parse_iso_timestamp(ts_raw)

                    if not (t_es >= t_req_start):
                        errors.append(f"{step_name} ES timestamp is older than request call time: t_es ({t_es}) < t_req_start ({t_req_start})")

                    if prev_timestamp is not None:
                        if not (t_es > prev_timestamp):
                            errors.append(
                                f"Timestamp monotonicity failure on {step_name}: "
                                f"t_{step.name} ({t_es}) <= t_{prev_step_name} ({prev_timestamp})"
                            )

                    prev_timestamp = t_es
                    prev_step_name = step.name

                except Exception as e:
                    errors.append(f"Invalid ES timestamp format on {step_name}: {e}")
                    break

                if step_idx == len(route.steps) and step.name == "DELETE":
                    completed_cleanly = True

                time.sleep(0.01)

        finally:
            if entity_id and (len(errors) > 0 or not completed_cleanly):
                try:
                    method_del, path_del = route.get_delete_endpoint(entity_id)
                    logger.info(f"[TEARDOWN ROLLBACK] Cleaning up entity '{entity_id}' on {route.base_path} via {method_del} {path_del}")
                    status_del, _ = self.client.api_request(method_del, path_del, custom_headers=route.headers, custom_cookies=route.cookies)
                    if status_del not in (200, 204):
                        logger.warning(f"[TEARDOWN WARNING] Rollback DELETE for '{entity_id}' on {route.base_path} returned status {status_del}")
                except Exception as teardown_err:
                    logger.warning(f"[TEARDOWN EXCEPTION] Rollback failed for entity '{entity_id}' on {route.base_path}: {teardown_err}")

        passed = (len(errors) == 0)
        return passed, errors


# ============================================================================
# 4. MAIN RUNNER
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Elasticsearch Delta Sync Auditor")
    
    parser.add_argument("--target-url", type=str, default=os.getenv("TARGET_URL", DEFAULT_TARGET_URL), help="Backend REST API URL (Env: TARGET_URL)")
    parser.add_argument("--es-url", type=str, default=os.getenv("ES_URL", DEFAULT_ES_URL), help="Elasticsearch Base URL (Env: ES_URL)")
    parser.add_argument("--es-user", type=str, default=os.getenv("ES_USER", DEFAULT_ES_USER), help="Elasticsearch Username (Env: ES_USER)")
    parser.add_argument("--es-pass", type=str, default=os.getenv("ES_PASS", DEFAULT_ES_PASS), help="Elasticsearch Password (Env: ES_PASS)")
    parser.add_argument("--config", type=str, default=os.getenv("AUDIT_CONFIG_PATH", os.getenv("CONFIG_PATH", DEFAULT_CONFIG_PATH)), help="Path to JSON config file or directory (Env: AUDIT_CONFIG_PATH)")
    parser.add_argument("--cookie", type=str, default=os.getenv("AUDIT_COOKIE", os.getenv("COOKIE", DEFAULT_COOKIE)), help="Session Cookie string (Env: AUDIT_COOKIE)")
    parser.add_argument("--workers", type=int, default=int(os.getenv("AUDIT_WORKERS", DEFAULT_WORKERS)), help="Worker threads count (Env: AUDIT_WORKERS)")
    parser.add_argument("--auth-token", type=str, default=os.getenv("AUTH_TOKEN", ""), help="Optional Bearer token for Backend API (Env: AUTH_TOKEN)")
    
    args = parser.parse_args()

    print(f"""
    ========================================================================
     ELASTICSEARCH DELTA SYNC AUDITOR
     Backend API URL : {args.target_url}
     Elasticsearch   : {args.es_url}
     ES Auth (User)  : {args.es_user if args.es_user else '[NONE]'}
     Config Source   : {args.config}
     Hardcoded Field : {HARDCODED_MODIFIED_AT_FIELD} (in ES document)
    ========================================================================
    """)

    routes = load_route_configs(args.config)
    if not routes:
        print(f"[ERROR] No valid route configurations loaded from '{args.config}'. Exiting.")
        sys.exit(1)

    print(f"[INFO] Loaded {len(routes)} API route definitions from '{args.config}'.\n")

    headers = {"Content-Type": "application/json"}
    if args.auth_token:
        headers["Authorization"] = f"Bearer {args.auth_token}"

    client = BlackboxClient(
        target_url=args.target_url,
        es_url=args.es_url,
        es_user=args.es_user,
        es_pass=args.es_pass,
        default_headers=headers,
        cookie_str=args.cookie
    )
    auditor = ESAuditor(client)

    print(f">> Executing Dynamic Steps Order Delta Sync Audits (With Automated Teardown)...")
    t0 = time.time()

    results: List[Tuple[BlackboxRouteDefinition, bool, List[str]]] = []

    def task(r_def: BlackboxRouteDefinition):
        passed, errs = auditor.audit_route(r_def)
        return r_def, passed, errs

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(task, r) for r in routes]
        for f in as_completed(futures):
            results.append(f.result())

    elapsed = time.time() - t0
    print(f"[SUCCESS] Audit completed in {elapsed:.2f}s ({len(routes)/elapsed:.1f} endpoints/sec)!\n")

    total = len(results)
    passed_cnt = sum(1 for _, p, _ in results if p)
    failed_cnt = total - passed_cnt

    print("=" * 80)
    print("  ELASTICSEARCH DELTA SYNC AUDIT REPORT")
    print("=" * 80)
    print(f"  Total APIs Audited   : {total}")
    print(f"  APIs Passed Delta Sync: {passed_cnt} ({passed_cnt/total*100:.1f}%)")
    print(f"  APIs Failed Delta Sync: {failed_cnt} ({failed_cnt/total*100:.1f}%)")

    if failed_cnt > 0:
        print("\n  Detected Failures:")
        for r_def, _, errs in [res for res in results if not res[1]]:
            print(f"    [FAILED] [{r_def.base_path}] (ES Index: {r_def.es_index})")
            print(f"             Errors: {', '.join(errs)}")

    print("\n========================================================================")
    print("  AUDIT PROCESS COMPLETED")
    print("========================================================================\n")


if __name__ == "__main__":
    main()
