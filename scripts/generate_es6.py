#!/usr/bin/env python3
"""
Create the `bench-es6` index (see mapping-es6.json for the full, ~50-field
schema: product core fields, nested `reviews`, nested `variants`, an
`attributes` object, a `shipping` object, and nested `price_history`) on
Elasticsearch 6 and bulk-load synthetic documents. Pure Python 3 standard
library -- no pip packages required.

Run this ON the es6 VM (fastest, talks to localhost):
    python3 generate_es6.py

Performance notes (why this is faster than a naive per-doc generator):
  - Per-doc randomness avoids `random.randint`/`random.choice`, which do
    rejection-sampling internally (see `_randbelow_with_getrandbits` in the
    stdlib) -- `fi()`/`fp()` below use `random.random()` directly instead,
    which is a straight C call with no rejection loop. Measured ~1.3x on
    doc generation alone.
  - `description` and review `comment` text is picked from a small
    precomputed sentence pool instead of being assembled word-by-word on
    every call -- avoids ~30 extra random calls per document. Measured
    ~1.6x combined with the point above (11.5k -> ~19k docs/s on one core
    in profiling; scale by WORKERS for the real number on your VM).
  - Each worker process reuses one persistent HTTP connection for all its
    `_bulk` requests instead of opening a new TCP connection per request.
  None of this touches ES-side tuning, which usually matters more: this
  mapping already sets `refresh_interval: -1`, `number_of_replicas: 0`, and
  `translog.durability: async` (fsync batched every `sync_interval` instead
  of per request) -- the standard bulk-load knobs, safe here because this is
  disposable benchmark data, not something you need durable if the VM dies
  mid-load.

Tunables via environment variables:
    ES_URL   Elasticsearch 6 base URL      (default http://localhost:9200)
    INDEX    target index name             (default bench-es6)
    TOTAL    number of documents           (default 8000000)
    BATCH    docs per _bulk request        (default 6000 -- larger docs now
             than the original 40-field schema, kept in the ~10 MiB sweet
             spot for _bulk request size)
    WORKERS  parallel worker processes     (default = CPU count)
    RESET    drop index first if 'true'    (default true)
    ES_USER  basic-auth user               (default elastic)
    ES_PW    basic-auth password           (required when security is enabled)
"""
import base64
import http.client
import json
import os
import random
import sys
import time
from urllib.parse import urlparse
import urllib.error
import urllib.request
from multiprocessing import Pool, cpu_count

ES_URL = os.environ.get("ES_URL", "http://localhost:9200").rstrip("/")
ES_USER = os.environ.get("ES_USER", "elastic")
ES_PW = os.environ.get("ES_PW", "")
INDEX = os.environ.get("INDEX", "bench-es6")
TOTAL = int(os.environ.get("TOTAL", "1000000"))
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
WEIGHT_CLASSES = ["light", "medium", "heavy", "oversized"]
PRICE_CHANGE_REASONS = ["promotion", "cost_increase", "clearance", "correction"]
# Fixed, bounded vocabulary for `attributes` keys -- every doc picks a random
# subset of these, but the key set itself never grows, so the dynamic
# `object` mapping never explodes past ~len(ATTRIBUTE_KEYS) fields no matter
# how many documents are indexed.
ATTRIBUTE_KEYS = [
    "battery_life", "warranty_months", "voltage", "connector_type",
    "water_resistance", "material_grade", "noise_level_db", "screen_size_in",
    "bluetooth_version", "charging_type", "origin_country", "eco_label",
    "assembly_required", "max_load_kg",
]

# Precomputed once at import time, independent of doc id -- picking one of
# these is O(1) versus assembling a sentence word-by-word on every call.
# random.Random-seeded from a fixed constant so the pool itself is stable
# across runs (not that it matters for correctness, just for repeatable
# byte sizes when tuning BATCH/journal estimates).
_pool_rng = random.Random(0xC0FFEE)
DESC_POOL = [" ".join(_pool_rng.choice(WORDS) for _ in range(_pool_rng.randint(6, 20))) for _ in range(2000)]
COMMENT_POOL = [" ".join(_pool_rng.choice(WORDS) for _ in range(_pool_rng.randint(3, 10))) for _ in range(2000)]


def fi(rnd, a, b):
    """Fast uniform int in [a, b] -- avoids randint()'s rejection sampling."""
    return a + int(rnd.random() * (b - a + 1))


def fp(rnd, seq):
    """Fast uniform pick from seq -- avoids choice()'s rejection sampling."""
    return seq[int(rnd.random() * len(seq))]


def es_request(method, path, body=None):
    """One-off, non-bulk request (index/mapping management). Not on the hot
    path, so plain urllib is fine here."""
    url = ES_URL + path
    data = body.encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/x-ndjson" if path.endswith("_bulk") else "application/json"}
    if ES_PW:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{ES_USER}:{ES_PW}".encode()).decode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.status, resp.read().decode("utf-8")


def make_doc(i):
    rnd = random.Random(i)  # deterministic per-id content
    n_reviews = fi(rnd, 0, 3)
    n_variants = fi(rnd, 1, 4)
    n_price_history = fi(rnd, 0, 3)
    n_attrs = fi(rnd, 3, 6)
    base_price = round(rnd.uniform(1, 5000), 2)
    return {
        "id": "doc-%d" % i,
        "sku": "SKU-%08d" % i,
        "title": "Product %d %s" % (i, fp(rnd, WORDS)),
        "description": fp(rnd, DESC_POOL),
        "category": fp(rnd, CATEGORIES),
        "sub_category": fp(rnd, CATEGORIES),
        "brand": fp(rnd, BRANDS),
        "status": fp(rnd, STATUSES),
        "country_code": fp(rnd, COUNTRIES),
        "currency": fp(rnd, CURRENCIES),
        "tags": rnd.sample(WORDS, fi(rnd, 1, 4)),
        "price": base_price,
        "discount": round(rnd.uniform(0, 0.9), 2),
        "rating": round(rnd.uniform(1, 5), 1),
        "views": fi(rnd, 0, 1000000),
        "stock": fi(rnd, 0, 10000),
        "sold_count": fi(rnd, 0, 500000),
        "weight_kg": round(rnd.uniform(0.1, 50), 2),
        "width_cm": round(rnd.uniform(1, 200), 1),
        "height_cm": round(rnd.uniform(1, 200), 1),
        "depth_cm": round(rnd.uniform(1, 200), 1),
        "is_active": rnd.random() > 0.3,
        "is_featured": rnd.random() > 0.8,
        "in_stock": rnd.random() > 0.2,
        "created_at": "2023-%02d-%02dT%02d:%02d:00Z" % (fi(rnd, 1, 12), fi(rnd, 1, 28), fi(rnd, 0, 23), fi(rnd, 0, 59)),
        "updated_at": "2024-%02d-%02dT%02d:%02d:00Z" % (fi(rnd, 1, 12), fi(rnd, 1, 28), fi(rnd, 0, 23), fi(rnd, 0, 59)),
        "published_at": "2024-%02d-01T00:00:00Z" % fi(rnd, 1, 12),
        "client_ip": "%d.%d.%d.%d" % (fi(rnd, 1, 223), fi(rnd, 0, 255), fi(rnd, 0, 255), fi(rnd, 1, 254)),
        "location": {"lat": round(rnd.uniform(-90, 90), 5), "lon": round(rnd.uniform(-180, 180), 5)},
        "seller_id": "seller-%d" % fi(rnd, 1, 50000),
        "seller_name": "Seller %d" % fi(rnd, 1, 50000),
        "warehouse_code": "WH-%s" % fp(rnd, COUNTRIES),
        "supplier_id": "sup-%d" % fi(rnd, 1, 20000),
        "barcode": "%013d" % fi(rnd, 1, 9999999999999),
        "color": fp(rnd, COLORS),
        "size": fp(rnd, SIZES),
        "material": fp(rnd, MATERIALS),
        "rank": fi(rnd, 1, 100000),
        "score": round(rnd.uniform(0, 100), 4),
        "reviews": [
            {"author": "user-%d" % fi(rnd, 1, 100000), "rating": fi(rnd, 1, 5), "comment": fp(rnd, COMMENT_POOL)}
            for _ in range(n_reviews)
        ],
        "variants": [
            {
                "sku": "SKU-%08d-V%d" % (i, v),
                "color": fp(rnd, COLORS),
                "size": fp(rnd, SIZES),
                "price": round(base_price * rnd.uniform(0.8, 1.2), 2),
                "stock": fi(rnd, 0, 5000),
                "is_default": v == 0,
            }
            for v in range(n_variants)
        ],
        # Bounded key vocabulary (ATTRIBUTE_KEYS) so the dynamic `object`
        # mapping never grows past a fixed field count; values are always
        # strings so a given key never flips type across documents.
        "attributes": {
            k: "%s-%d" % (fp(rnd, WORDS), fi(rnd, 1, 999))
            for k in rnd.sample(ATTRIBUTE_KEYS, min(n_attrs, len(ATTRIBUTE_KEYS)))
        },
        "shipping": {
            "weight_class": fp(rnd, WEIGHT_CLASSES),
            "free_shipping": rnd.random() > 0.5,
            "handling_days": fi(rnd, 1, 14),
            "regions": rnd.sample(COUNTRIES, fi(rnd, 1, 3)),
        },
        "price_history": [
            {
                "changed_at": "2022-%02d-%02dT00:00:00Z" % (fi(rnd, 1, 12), fi(rnd, 1, 28)),
                "old_price": round(base_price * rnd.uniform(0.7, 1.3), 2),
                "new_price": base_price,
                "reason": fp(rnd, PRICE_CHANGE_REASONS),
            }
            for _ in range(n_price_history)
        ],
    }


# ----------------------------------------------------- persistent _bulk --
# One HTTP connection per worker process, reused across every _bulk request
# it sends, instead of a fresh TCP connection per request.

_parsed = urlparse(ES_URL)
_HOST = _parsed.hostname
_PORT = _parsed.port or (443 if _parsed.scheme == "https" else 80)
_SCHEME = _parsed.scheme
_conn = None


def _get_conn():
    global _conn
    if _conn is None:
        cls = http.client.HTTPSConnection if _SCHEME == "https" else http.client.HTTPConnection
        _conn = cls(_HOST, _PORT, timeout=300)
    return _conn


def _reset_conn():
    global _conn
    try:
        if _conn is not None:
            _conn.close()
    except Exception:
        pass
    _conn = None


def bulk_post(ndjson):
    """POST one bulk batch with retry/backoff on 429 and connection errors."""
    path = "/%s/_doc/_bulk" % INDEX
    data = ndjson.encode("utf-8")
    headers = {"Content-Type": "application/x-ndjson"}
    if ES_PW:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{ES_USER}:{ES_PW}".encode()).decode()
    for attempt in range(6):
        try:
            conn = _get_conn()
            conn.request("POST", path, body=data, headers=headers)
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            if resp.status == 429:
                _reset_conn()
                if attempt < 5:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError("bulk rejected (429) after retries")
            if '"errors":true' in body:
                doc = json.loads(body)
                for item in doc.get("items", []):
                    err = item.get("index", {}).get("error")
                    if err:
                        raise RuntimeError("bulk item error: %s" % json.dumps(err)[:400])
            return
        except (http.client.HTTPException, OSError):
            _reset_conn()
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
    _reset_conn()
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
            es_request("DELETE", "/%s" % INDEX)
            print("dropped existing index %s" % INDEX)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise

    es_request("PUT", "/%s?include_type_name=true" % INDEX, mapping)
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
    es_request("PUT", "/%s/_settings" % INDEX, '{"index":{"refresh_interval":"1s"}}')
    es_request("POST", "/%s/_refresh" % INDEX)
    _, cnt = es_request("GET", "/%s/_count" % INDEX)
    got = json.loads(cnt)["count"]
    print("final _count = %d (expected %d)" % (got, TOTAL))
    if got != TOTAL:
        print("WARNING: count mismatch!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
