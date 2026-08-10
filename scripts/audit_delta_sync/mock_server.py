#!/usr/bin/env python3
"""
mock_server.py - Standalone Multi-Route REST API & Simulated Elasticsearch Server.

Simulates:
  1. Backend REST API Endpoints (POST, PUT, PATCH, DELETE).
  2. Elasticsearch Document Store & Search API:
     - GET /{es_index}/_doc/{entity_id}
     - POST /{es_index}/_search with { "query": { "bool": { "must": [ { "term": { id_field: entity_id } } ] } } }
"""

import argparse
import json
import logging
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MockServer")


# In-memory ES Store: { index_name: { doc_id: doc_dict } }
GLOBAL_ES_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class MockServerHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        pass

    def _send_json(self, status_code: int, data: Any):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _read_json(self) -> Dict[str, Any]:
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len > 0:
            raw = self.rfile.read(content_len).decode("utf-8")
            return json.loads(raw) if raw else {}
        return {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _get_es_index(self, base_path: str) -> str:
        parts = base_path.strip("/").split("/")
        return "_".join(parts[-2:]).replace("-", "_")

    def do_GET(self):
        raw_path = self.path.split("?")[0].rstrip("/")
        
        if raw_path == "/health":
            return self._send_json(200, {"status": "UP"})

        # SIMULATED ELASTICSEARCH DOCUMENT GET: GET /{index}/_doc/{id}
        if "/_doc/" in raw_path:
            parts = raw_path.strip("/").split("/_doc/")
            if len(parts) == 2:
                es_index, doc_id = parts[0], parts[1]
                res_db = GLOBAL_ES_STORE.get(es_index, {})
                if doc_id in res_db:
                    doc = res_db[doc_id]
                    return self._send_json(200, {
                        "_index": es_index,
                        "_id": doc_id,
                        "_source": doc
                    })
                return self._send_json(404, {"found": False, "_index": es_index, "_id": doc_id})

        return self._send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        raw_path = self.path.split("?")[0].rstrip("/")
        body = self._read_json()
        now = self._now_iso()

        # SIMULATED ELASTICSEARCH SEARCH API: POST /{index}/_search
        if raw_path.endswith("/_search"):
            es_index = raw_path.rsplit("/_search", 1)[0].strip("/")
            res_db = GLOBAL_ES_STORE.get(es_index, {})
            
            # Extract term match key-value from bool must query
            query_must = body.get("query", {}).get("bool", {}).get("must", [])
            search_key, search_val = None, None
            for item in query_must:
                if "term" in item:
                    for k, v in item["term"].items():
                        search_key, search_val = k, str(v)
                        break

            hits = []
            for doc_id, doc in res_db.items():
                if search_key and str(doc.get(search_key)) == search_val:
                    hits.append({"_index": es_index, "_id": doc_id, "_source": doc})
                elif not search_key and doc_id == search_val:
                    hits.append({"_index": es_index, "_id": doc_id, "_source": doc})

            return self._send_json(200, {
                "took": 1,
                "hits": {
                    "total": {"value": len(hits), "relation": "eq"},
                    "hits": hits
                }
            })
        
        # REST API CREATE MUTATION
        es_index = self._get_es_index(raw_path)
        res_db = GLOBAL_ES_STORE.setdefault(es_index, {})
        
        e_id = str(body.get("id") or f"id-{len(res_db)+1}")
        
        doc = dict(body)
        doc["id"] = e_id
        doc["created_at"] = now
        doc["modified_at"] = now
        res_db[e_id] = doc

        return self._send_json(201, {"status": "SUCCESS", "id": e_id})

    def do_PUT(self):
        raw_path = self.path.split("?")[0].rstrip("/")
        parts = raw_path.rsplit("/", 1)
        if len(parts) < 2:
            return self._send_json(400, {"error": "Invalid URL"})
            
        base_path, entity_id = parts[0], parts[1]
        body = self._read_json()
        now = self._now_iso()
        
        es_index = self._get_es_index(base_path)
        res_db = GLOBAL_ES_STORE.setdefault(es_index, {})
        
        existing = res_db.get(entity_id, {})
        doc = dict(body)
        doc["id"] = entity_id
        doc["created_at"] = existing.get("created_at", now)
        doc["modified_at"] = now
        
        res_db[entity_id] = doc
        return self._send_json(200, {"status": "UPDATED", "id": entity_id})

    def do_PATCH(self):
        raw_path = self.path.split("?")[0].rstrip("/")
        parts = raw_path.rsplit("/", 1)
        if len(parts) < 2:
            return self._send_json(400, {"error": "Invalid URL"})
            
        base_path, entity_id = parts[0], parts[1]
        body = self._read_json()
        now = self._now_iso()
        
        es_index = self._get_es_index(base_path)
        res_db = GLOBAL_ES_STORE.get(es_index, {})
        
        if entity_id not in res_db:
            return self._send_json(404, {"error": "Item not found in DB"})
            
        existing = res_db[entity_id]
        updated = dict(existing)
        updated.update(body)
        
        if "invoices-84" in base_path:
            pass # Simulated bug on invoices-84
        else:
            updated["modified_at"] = now
            
        res_db[entity_id] = updated
        return self._send_json(200, {"status": "PATCHED", "id": entity_id})

    def do_DELETE(self):
        raw_path = self.path.split("?")[0].rstrip("/")
        parts = raw_path.rsplit("/", 1)
        if len(parts) < 2:
            return self._send_json(400, {"error": "Invalid URL"})
            
        base_path, entity_id = parts[0], parts[1]
        now = self._now_iso()
        
        es_index = self._get_es_index(base_path)
        res_db = GLOBAL_ES_STORE.get(es_index, {})
        
        if entity_id in res_db:
            existing = res_db[entity_id]
            existing["is_deleted"] = True
            existing["modified_at"] = now
            
        return self._send_json(200, {"status": "DELETED", "id": entity_id})


def start_server(port: int = 8899):
    server = ThreadedHTTPServer(("127.0.0.1", port), MockServerHandler)
    logger.info(f"Mock REST Server & ES Store running on http://127.0.0.1:{port}")
    print(f">> Server ready at http://127.0.0.1:{port} (Press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping Mock Server...")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone REST API & ES Store Server")
    parser.add_argument("--port", type=int, default=8899, help="Server port (default: 8899)")
    args = parser.parse_args()
    start_server(args.port)
