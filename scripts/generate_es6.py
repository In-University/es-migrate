#!/usr/bin/env python3
"""
Create the `bench-es6` index (40-field mapping) on Elasticsearch 6 and bulk-load
synthetic documents. Pure Python 3 standard library -- no pip packages required.

Run this ON the es6 VM (fastest, talks to localhost):
    python3 generate_es6.py

Tunables via environment variables:
    ES_URL   Elasticsearch 6 base URL      (default http://localhost:9200)
    INDEX    target index name             (default bench-es6)
    TOTAL    number of documents           (default 8000000)
    BATCH    docs per _bulk request        (default 10000)
    WORKERS  parallel worker processes     (default = CPU count)
    RESET    drop index first if 'true'    (default true)
    ES_USER  basic-auth user               (default elastic)
    ES_PW    basic-auth password           (required when security is enabled)
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

ES_URL = os.environ.get("ES_URL", "http://localhost:9200").rstrip("/")
ES_USER = os.environ.get("ES_USER", "elastic")
ES_PW = os.environ.get("ES_PW", "")
INDEX = os.environ.get("INDEX", "bench-es6")
TOTAL = int(os.environ.get("TOTAL", "8000000"))
BATCH = int(os.environ.get("BATCH", "10000"))
WORKERS = int(os.environ.get("WORKERS", str(cpu_count())))
RESET = os.environ.get("RESET", "true").lower() == "true"
MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mapping-es6.json")

CATEGORIES = ["electronics", "books", "clothing", "home", "toys", "sports", "beauty", "grocery"]
BRANDS = ["acme", "globex", "initech", "umbrella", "wayne", "stark", "wonka", "cyberdyne"]
STATUSES = ["draft", "active", "archived", "out_of_stock"]
COUNTRIES = ["US", "JP", "VN", "DE", "FR", "GB", "IN", "BR"]
CURRENCIES = ["USD", "JPY", "VND", "EUR", "GBP", "INR", "BRL"]
COLORS = ["red", "green", "blue", "black", "white", "silver", "gold"]
SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
MATERIALS = ["cotton", "steel", "plastic", "wood", "glass", "leather"]
WORDS = ["fast", "durable", "compact", "premium", "eco", "smart", "classic", "pro", "lite", "max"]


def http(method, path, body=None):
    url = ES_URL + path
    data = body.encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/x-ndjson" if path.endswith("_bulk") else "application/json"}
    if ES_PW:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{ES_USER}:{ES_PW}".encode()).decode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.status, resp.read().decode("utf-8")


def sentence(n):
    return " ".join(random.choice(WORDS) for _ in range(n))


def make_doc(i):
    rnd = random.Random(i)  # deterministic per-id content
    n_reviews = rnd.randint(0, 3)
    return {
        "id": "doc-%d" % i,
        "sku": "SKU-%08d" % i,
        "title": "Product %d %s" % (i, rnd.choice(WORDS)),
        "description": sentence(rnd.randint(6, 20)),
        "category": rnd.choice(CATEGORIES),
        "sub_category": rnd.choice(CATEGORIES),
        "brand": rnd.choice(BRANDS),
        "status": rnd.choice(STATUSES),
        "country_code": rnd.choice(COUNTRIES),
        "currency": rnd.choice(CURRENCIES),
        "tags": rnd.sample(WORDS, rnd.randint(1, 4)),
        "price": round(rnd.uniform(1, 5000), 2),
        "discount": round(rnd.uniform(0, 0.9), 2),
        "rating": round(rnd.uniform(1, 5), 1),
        "views": rnd.randint(0, 1000000),
        "stock": rnd.randint(0, 10000),
        "sold_count": rnd.randint(0, 500000),
        "weight_kg": round(rnd.uniform(0.1, 50), 2),
        "width_cm": round(rnd.uniform(1, 200), 1),
        "height_cm": round(rnd.uniform(1, 200), 1),
        "depth_cm": round(rnd.uniform(1, 200), 1),
        "is_active": rnd.random() > 0.3,
        "is_featured": rnd.random() > 0.8,
        "in_stock": rnd.random() > 0.2,
        "created_at": "2023-%02d-%02dT%02d:%02d:00Z" % (rnd.randint(1, 12), rnd.randint(1, 28), rnd.randint(0, 23), rnd.randint(0, 59)),
        "updated_at": "2024-%02d-%02dT%02d:%02d:00Z" % (rnd.randint(1, 12), rnd.randint(1, 28), rnd.randint(0, 23), rnd.randint(0, 59)),
        "published_at": "2024-%02d-01T00:00:00Z" % rnd.randint(1, 12),
        "client_ip": "%d.%d.%d.%d" % (rnd.randint(1, 223), rnd.randint(0, 255), rnd.randint(0, 255), rnd.randint(1, 254)),
        "location": {"lat": round(rnd.uniform(-90, 90), 5), "lon": round(rnd.uniform(-180, 180), 5)},
        "seller_id": "seller-%d" % rnd.randint(1, 50000),
        "seller_name": "Seller %d" % rnd.randint(1, 50000),
        "warehouse_code": "WH-%s" % rnd.choice(COUNTRIES),
        "supplier_id": "sup-%d" % rnd.randint(1, 20000),
        "barcode": "%013d" % rnd.randint(1, 9999999999999),
        "color": rnd.choice(COLORS),
        "size": rnd.choice(SIZES),
        "material": rnd.choice(MATERIALS),
        "rank": rnd.randint(1, 100000),
        "score": round(rnd.uniform(0, 100), 4),
        "reviews": [
            {"author": "user-%d" % rnd.randint(1, 100000), "rating": rnd.randint(1, 5), "comment": sentence(rnd.randint(3, 10))}
            for _ in range(n_reviews)
        ],
    }


def bulk_post(ndjson):
    """POST one bulk batch with retry/backoff on 429 and transient errors."""
    path = "/%s/_doc/_bulk" % INDEX
    for attempt in range(6):
        try:
            status, resp = http("POST", path, ndjson)
            if '"errors":true' in resp:
                # surface a sample of the first error
                doc = json.loads(resp)
                for item in doc.get("items", []):
                    err = item.get("index", {}).get("error")
                    if err:
                        raise RuntimeError("bulk item error: %s" % json.dumps(err)[:400])
            return
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


def worker(rng):
    start, end = rng
    buf = []
    action = '{"index":{"_id":"%s"}}'
    count = 0
    for i in range(start, end):
        doc = make_doc(i)
        buf.append(action % doc["id"])
        buf.append(json.dumps(doc, separators=(",", ":")))
        if len(buf) >= BATCH * 2:
            bulk_post("\n".join(buf) + "\n")
            count += len(buf) // 2
            buf = []
    if buf:
        bulk_post("\n".join(buf) + "\n")
        count += len(buf) // 2
    return count


def chunk_ranges(total, workers):
    per = total // workers
    ranges = []
    s = 0
    for w in range(workers):
        e = total if w == workers - 1 else s + per
        ranges.append((s, e))
        s = e
    return ranges


def main():
    with open(MAPPING_FILE) as f:
        mapping = f.read()

    if RESET:
        try:
            http("DELETE", "/%s" % INDEX)
            print("dropped existing index %s" % INDEX)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise

    http("PUT", "/%s?include_type_name=true" % INDEX, mapping)
    print("created index %s" % INDEX)

    print("loading %d docs, batch=%d, workers=%d -> %s" % (TOTAL, BATCH, WORKERS, ES_URL))
    t0 = time.time()
    ranges = chunk_ranges(TOTAL, WORKERS)
    loaded = 0
    with Pool(WORKERS) as pool:
        for c in pool.imap_unordered(worker, ranges):
            loaded += c
            print("  loaded ~%d / %d (%.0fs)" % (loaded, TOTAL, time.time() - t0))
    dt = time.time() - t0
    print("bulk load done: %d docs in %.0fs (%.0f docs/s)" % (loaded, dt, loaded / max(dt, 1)))

    # restore refresh + verify
    http("PUT", "/%s/_settings" % INDEX, '{"index":{"refresh_interval":"1s"}}')
    http("POST", "/%s/_refresh" % INDEX)
    _, cnt = http("GET", "/%s/_count" % INDEX)
    got = json.loads(cnt)["count"]
    print("final _count = %d (expected %d)" % (got, TOTAL))
    if got != TOTAL:
        print("WARNING: count mismatch!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
