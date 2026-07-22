#!/usr/bin/env python3
"""
Simulate blue-green post-cutover activity on ES9's bench-es9 index: a
handful of creates, updates, and hard deletes, so the rollback runbook
(README §5) can be exercised end-to-end on a small dataset instead of the
full 8M-doc benchmark.

Run this AFTER reindex_remote.sh has migrated ES6 -> ES9. It touches only
ES9 -- ES6 stays exactly as reindex_remote.sh left it, which is the point:
the rollback tooling (rollback_sync.sh + reconcile_deletes.sh) has to bring
ES6 back in line with these changes on its own.

Tunables via environment variables:
    ES9_URL    Elasticsearch 9 base URL   (default http://localhost:9200)
    INDEX      target index               (default bench-es9)
    ES_USER    basic-auth user            (default elastic)
    ES_PW      basic-auth password        (required when security is enabled)
    CREATE_N   docs to create             (default 3)
    UPDATE_N   docs to update             (default 3)
    DELETE_N   docs to hard-delete        (default 2)
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

ES9_URL = os.environ.get("ES9_URL", "http://localhost:9200").rstrip("/")
INDEX = os.environ.get("INDEX", "bench-es9")
ES_USER = os.environ.get("ES_USER", "elastic")
ES_PW = os.environ.get("ES_PW", "")
CREATE_N = int(os.environ.get("CREATE_N", "3"))
UPDATE_N = int(os.environ.get("UPDATE_N", "3"))
DELETE_N = int(os.environ.get("DELETE_N", "2"))


def http(method, path, body=None):
    url = ES9_URL + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"}
    if ES_PW:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{ES_USER}:{ES_PW}".encode()).decode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main():
    resp = http("GET", f"/{INDEX}/_search?size=1000&_source=false")
    ids = [h["_id"] for h in resp["hits"]["hits"]]
    if not ids:
        print(f"ERROR: {INDEX} is empty -- run reindex_remote.sh first", file=sys.stderr)
        sys.exit(1)
    if len(ids) < UPDATE_N + DELETE_N:
        print(f"WARNING: only {len(ids)} docs in {INDEX}, reduce UPDATE_N/DELETE_N", file=sys.stderr)

    to_update = ids[:UPDATE_N]
    to_delete = ids[UPDATE_N:UPDATE_N + DELETE_N]

    def doc_num(doc_id):
        try:
            return int(doc_id.split("-")[1])
        except (IndexError, ValueError):
            return -1

    max_i = max((doc_num(i) for i in ids), default=-1)

    print(f">> creating {CREATE_N} new docs")
    for n in range(CREATE_N):
        new_id = f"doc-{max_i + 1 + n}"
        doc = {
            "id": new_id,
            "sku": f"SKU-NEW-{n}",
            "title": f"Rollback test create {n}",
            "status": "active",
            "is_active": True,
            "in_stock": True,
            "price": 9.99,
            "created_at": now(),
            "updated_at": now(),
        }
        http("PUT", f"/{INDEX}/_doc/{new_id}", doc)
        print(f"   created {new_id}")

    print(f">> updating {len(to_update)} existing docs")
    for doc_id in to_update:
        http("POST", f"/{INDEX}/_update/{doc_id}", {
            "doc": {"title": "UPDATED by rollback simulation", "updated_at": now()}
        })
        print(f"   updated {doc_id}")

    print(f">> hard-deleting {len(to_delete)} existing docs")
    for doc_id in to_delete:
        http("DELETE", f"/{INDEX}/_doc/{doc_id}")
        print(f"   deleted {doc_id}")

    http("POST", f"/{INDEX}/_refresh")
    print(">> done. bench-es9 now has creates/updates/deletes not yet reflected on ES6.")
    print(">> next: run rollback_sync.sh (creates/updates) then reconcile_deletes.sh (deletes).")


if __name__ == "__main__":
    main()
