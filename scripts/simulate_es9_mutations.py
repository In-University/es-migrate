#!/usr/bin/env python3
"""
Simulate blue-green post-cutover activity on ES9's bench-es9 index: creates,
updates, and hard deletes, so the rollback tooling (scripts/es_rollback.sh)
can be exercised end-to-end.

Two modes, chosen automatically by whether MUTATE_PCT is set:

  - MUTATE_PCT unset -> small fixed-count demo (CREATE_N/UPDATE_N/DELETE_N,
    default 3/3/2). Same behavior as before -- fine for a handful-of-docs
    walkthrough.
  - MUTATE_PCT set (e.g. "0.10") -> percentage-of-index mode for the full
    8M-doc benchmark. Ids are sampled directly as doc-<i> (ids are dense
    integers 0..TOTAL-1, see generate_es6.py) instead of paging through
    _search, and changes are applied via _bulk across parallel worker
    processes so hundreds of thousands of mutations finish in minutes
    instead of hours of one-doc-at-a-time REST calls.

Run this AFTER reindex_remote.sh has migrated ES6 -> ES9. It only touches
ES9 -- ES6 stays exactly as reindex_remote.sh left it; the rollback tooling
has to bring ES6 back in line with these changes on its own.

Tunables via environment variables:
    ES9_URL       Elasticsearch 9 base URL      (default http://localhost:9200)
    INDEX         target index                  (default bench-es9)
    ES_USER       basic-auth user                (default elastic)
    ES_PW         basic-auth password            (required when security is enabled)

    # small fixed-count mode (used when MUTATE_PCT is unset)
    CREATE_N      docs to create                 (default 3)
    UPDATE_N      docs to update                  (default 3)
    DELETE_N      docs to hard-delete             (default 2)

    # percentage mode (used when MUTATE_PCT is set)
    MUTATE_PCT    fraction of the index to touch, e.g. 0.10 for 10%
    CREATE_RATIO  share of the touched docs that are creates  (default 0.10)
    UPDATE_RATIO  share of the touched docs that are updates  (default 0.70)
    DELETE_RATIO  share of the touched docs that are deletes  (default 0.20)
    BATCH         docs per _bulk request          (default 2000)
    WORKERS       parallel worker processes        (default = CPU count)
    SEED          random seed, for repeatable runs (default 42)
"""
import base64
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from multiprocessing import Pool, cpu_count

ES9_URL = os.environ.get("ES9_URL", "http://localhost:9200").rstrip("/")
INDEX = os.environ.get("INDEX", "bench-es9")
ES_USER = os.environ.get("ES_USER", "elastic")
ES_PW = os.environ.get("ES_PW", "")

CREATE_N = int(os.environ.get("CREATE_N", "3"))
UPDATE_N = int(os.environ.get("UPDATE_N", "3"))
DELETE_N = int(os.environ.get("DELETE_N", "2"))

MUTATE_PCT = os.environ.get("MUTATE_PCT", "")
CREATE_RATIO = float(os.environ.get("CREATE_RATIO", "0.10"))
UPDATE_RATIO = float(os.environ.get("UPDATE_RATIO", "0.70"))
DELETE_RATIO = float(os.environ.get("DELETE_RATIO", "0.20"))
BATCH = int(os.environ.get("BATCH", "2000"))
WORKERS = int(os.environ.get("WORKERS", str(cpu_count())))
SEED = int(os.environ.get("SEED", "42"))
INGEST_PIPELINE = os.environ.get("INGEST_PIPELINE", "set_modified_at")

WORDS = ["fast", "durable", "compact", "premium", "eco", "smart", "classic", "pro", "lite", "max"]


def http(method, path, body=None, is_bulk=False):
    url = ES9_URL + path
    if is_bulk:
        data = body.encode("utf-8")
        headers = {"Content-Type": "application/x-ndjson"}
    else:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
    if ES_PW:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{ES_USER}:{ES_PW}".encode()).decode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 5:
                time.sleep(2 ** attempt)
                continue
            raise
        except urllib.error.URLError:
            if attempt < 5:
                time.sleep(2 ** attempt)
                continue
            raise


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def setup_ingest_pipeline():
    print(f">> setting up ingest pipeline '{INGEST_PIPELINE}' on ES9")
    pipeline_body = {
        "description": "Set modified_at timestamp default to ingest time",
        "processors": [
            {
                "set": {
                    "field": "modified_at",
                    "value": "{{_ingest.timestamp}}"
                }
            }
        ]
    }
    http("PUT", f"/_ingest/pipeline/{INGEST_PIPELINE}", pipeline_body)
    http("PUT", f"/{INDEX}/_settings", {"index.default_pipeline": INGEST_PIPELINE})
    print(f"   ingest pipeline '{INGEST_PIPELINE}' set as index.default_pipeline on {INDEX}")


# ---------------------------------------------------------------- small mode --

def run_small_mode():
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
            "modified_at": now(),
        }
        http("PUT", f"/{INDEX}/_doc/{new_id}", doc)
        print(f"   created {new_id}")

    print(f">> updating {len(to_update)} existing docs")
    for doc_id in to_update:
        http("POST", f"/{INDEX}/_update/{doc_id}", {
            "doc": {"title": "UPDATED by rollback simulation", "updated_at": now(), "modified_at": now()}
        })
        print(f"   updated {doc_id}")

    print(f">> hard-deleting {len(to_delete)} existing docs")
    for doc_id in to_delete:
        http("DELETE", f"/{INDEX}/_doc/{doc_id}")
        print(f"   deleted {doc_id}")

    http("POST", f"/{INDEX}/_refresh")
    print(">> done. bench-es9 now has creates/updates/deletes not yet reflected on ES6.")
    print(">> next: run es_rollback.sh (preflight -> plan -> run).")


# ---------------------------------------------------------- percentage mode --

def make_update_action(i):
    doc_id = "doc-%d" % i
    action = '{"update":{"_id":"%s"}}' % doc_id
    src = json.dumps({"doc": {
        "title": "UPDATED by rollback simulation %d" % i,
        "updated_at": now(),
        "modified_at": now(),
    }}, separators=(",", ":"))
    return action + "\n" + src


def make_delete_action(i):
    return '{"delete":{"_id":"doc-%d"}}' % i


def make_create_action(i):
    doc_id = "doc-%d" % i
    rnd = random.Random(i)
    doc = {
        "id": doc_id,
        "sku": "SKU-NEW-%d" % i,
        "title": "Rollback test create %d %s" % (i, rnd.choice(WORDS)),
        "status": "active",
        "is_active": True,
        "in_stock": True,
        "price": round(rnd.uniform(1, 5000), 2),
        "created_at": now(),
        "updated_at": now(),
        "modified_at": now(),
    }
    action = '{"index":{"_id":"%s"}}' % doc_id
    src = json.dumps(doc, separators=(",", ":"))
    return action + "\n" + src


def bulk_post(ndjson):
    path = "/%s/_bulk" % INDEX
    resp = http("POST", path, ndjson, is_bulk=True)
    if resp.get("errors"):
        for item in resp.get("items", []):
            op, meta = next(iter(item.items()))
            if meta.get("status", 200) >= 300:
                print("   bulk item error [%s] %s: %s" % (op, meta.get("_id"), meta.get("error")), file=sys.stderr)


def worker(args):
    kind, ids = args
    maker = {"update": make_update_action, "delete": make_delete_action, "create": make_create_action}[kind]
    buf = []
    count = 0
    for i in ids:
        buf.append(maker(i))
        if len(buf) >= BATCH:
            bulk_post("\n".join(buf) + "\n")
            count += len(buf)
            buf = []
    if buf:
        bulk_post("\n".join(buf) + "\n")
        count += len(buf)
    return kind, count


def chunk(seq, n):
    per = max(1, -(-len(seq) // n))  # ceil division so we never exceed n chunks
    return [seq[i:i + per] for i in range(0, len(seq), per)]


def run_pct_mode():
    pct = float(MUTATE_PCT)
    cnt = http("GET", f"/{INDEX}/_count")
    total = cnt["count"]
    if total == 0:
        print(f"ERROR: {INDEX} is empty -- run reindex_remote.sh first", file=sys.stderr)
        sys.exit(1)

    touch = int(total * pct)
    create_n = int(touch * CREATE_RATIO)
    delete_n = int(touch * DELETE_RATIO)
    update_n = touch - create_n - delete_n

    print(f">> {INDEX} has {total} docs; simulating {pct:.0%} change "
          f"= {touch} doc(s) (create={create_n} update={update_n} delete={delete_n})")

    rnd = random.Random(SEED)
    sampled = rnd.sample(range(total), update_n + delete_n)
    update_ids = sampled[:update_n]
    delete_ids = sampled[update_n:]
    create_ids = list(range(total, total + create_n))

    tasks = []
    for kind, ids in (("update", update_ids), ("delete", delete_ids), ("create", create_ids)):
        if not ids:
            continue
        for part in chunk(ids, WORKERS):
            tasks.append((kind, part))

    t0 = time.time()
    done = {"update": 0, "delete": 0, "create": 0}
    with Pool(WORKERS) as pool:
        for kind, c in pool.imap_unordered(worker, tasks):
            done[kind] += c
            print(f"   progress: update={done['update']}/{update_n} "
                  f"delete={done['delete']}/{delete_n} create={done['create']}/{create_n} "
                  f"({time.time() - t0:.0f}s)")

    http("POST", f"/{INDEX}/_refresh")
    print(f">> done in {time.time() - t0:.0f}s. bench-es9 now has "
          f"{done['create']} create(s), {done['update']} update(s), {done['delete']} delete(s) "
          f"not yet reflected on ES6.")
    print(">> next: ./scripts/es_rollback.sh preflight   (then plan, run)")


def main():
    setup_ingest_pipeline()
    if MUTATE_PCT:
        run_pct_mode()
    else:
        run_small_mode()


if __name__ == "__main__":
    main()
