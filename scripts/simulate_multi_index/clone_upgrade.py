import os
import sys
import json
import time
import base64
import urllib.request
import urllib.error

# Configuration
ES6_URL = os.getenv("ES6_URL", "http://localhost:9200").rstrip("/")
ES9_URL = os.getenv("ES9_URL", "http://localhost:9201").rstrip("/")

ES6_USER = os.getenv("ES6_USER")
ES6_PASS = os.getenv("ES6_PASS")
ES9_USER = os.getenv("ES9_USER", ES6_USER)
ES9_PASS = os.getenv("ES9_PASS", ES6_PASS)

TARGET_ALIAS = os.getenv("ALIAS", "").strip()
MODE = os.getenv("MODE", "migrate").strip().lower()  # "migrate" or "cleanup"
DRY_RUN = os.getenv("DRY_RUN", "false").strip().lower() in ("true", "1", "yes")
CLEAN_SOURCE = os.getenv("CLEAN_SOURCE", "false").strip().lower() in ("true", "1", "yes")

EXCLUDED_SETTINGS = {
    "uuid", "version.created", "version.upgraded",
    "creation_date", "provided_name", "history.uuid"
}

def http_request(url, method="GET", data=None, username=None, password=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")

    if username and password:
        credentials = f"{username}:{password}".encode("utf-8")
        basic_auth = base64.b64encode(credentials).decode("utf-8")
        req.add_header("Authorization", f"Basic {basic_auth}")

    body = json.dumps(data).encode("utf-8") if data is not None else None

    try:
        with urllib.request.urlopen(req, data=body, timeout=300) as response:
            res_content = response.read().decode("utf-8")
            return json.loads(res_content) if res_content else {}
    except urllib.error.HTTPError as ex:
        if method in ("HEAD", "GET") and ex.code == 404:
            return None
        err_msg = ex.read().decode("utf-8")
        print(f"[ERROR] {method} {url} -> HTTP {ex.code}: {err_msg}", file=sys.stderr)
        raise
    except Exception as ex:
        print(f"[ERROR] Connection failed for {method} {url} -> {ex}", file=sys.stderr)
        raise

def index_exists(es_url, index_name, username, password):
    req = urllib.request.Request(f"{es_url}/{index_name}", method="HEAD")
    if username and password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
        req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status == 200
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return False
        raise

def delete_index(es_url, index_name, username, password, dry_run=False):
    if not index_exists(es_url, index_name, username, password):
        return
    if dry_run:
        print(f"[DRY-RUN] Would delete index '{index_name}' on {es_url}")
        return
    print(f"Deleting index '{index_name}' on {es_url}")
    http_request(f"{es_url}/{index_name}", method="DELETE", username=username, password=password)

def wait_for_task(es_url, task_id, username, password):
    """Wait for reindex task and validate failures/created doc counts."""
    while True:
        res = http_request(f"{es_url}/_tasks/{task_id}", username=username, password=password)
        if res.get("completed"):
            resp = res.get("response", {})
            if "error" in resp:
                raise RuntimeError(f"Task root error: {resp['error']}")

            # Check individual document failures
            failures = resp.get("failures", [])
            total = resp.get("total", 0)
            created = resp.get("created", 0)
            updated = resp.get("updated", 0)

            print(f"   -> Reindex stats: Total={total}, Created={created}, Updated={updated}, Failures={len(failures)}")

            if failures:
                sample_err = failures[0]
                raise RuntimeError(f"Reindex failed on documents! Sample error: {json.dumps(sample_err)}")

            if total > 0 and (created + updated) == 0:
                raise RuntimeError("Reindex completed but 0 documents were indexed!")

            break
        time.sleep(5)

def sanitize_settings(settings):
    clean = {}
    for k, v in settings.items():
        if k in EXCLUDED_SETTINGS:
            continue
        if k.startswith("routing.allocation") or k.startswith("version"):
            continue
        if k in ("blocks.write", "blocks.read_only", "blocks.read_only_allow_delete"):
            continue
        clean[k] = v
    return clean

def fetch_aliases(es_url, username, password):
    data = http_request(f"{es_url}/_alias", username=username, password=password)
    aliases_map = {}
    for index_name, meta in data.items():
        for alias_name in meta.get("aliases", {}).keys():
            if not alias_name.endswith("_upgrade"):
                if not TARGET_ALIAS or alias_name == TARGET_ALIAS:
                    aliases_map[alias_name] = index_name
    return aliases_map

def resolve_alias_index(es_url, alias_name, username, password):
    """Resolve an alias to its current underlying index on the specified cluster."""
    data = http_request(f"{es_url}/_alias/{alias_name}", username=username, password=password)
    if not data:
        return None
    # Filter out system indices starting with '.'
    indices = [idx for idx in data.keys() if not idx.startswith(".")]
    return indices[0] if indices else None

def run_es6_migration():
    print("=== Starting Phase 1: ES6 Migration ===")
    aliases = fetch_aliases(ES6_URL, ES6_USER, ES6_PASS)
    if not aliases:
        print("No matching aliases found on ES6.")
        return {}

    for alias, old_index in aliases.items():
        new_index = f"{old_index}_upgrade"
        new_alias = f"{alias}_upgrade"

        print(f"\n[ES6] Processing alias '{alias}' -> Index '{old_index}'")
        if index_exists(ES6_URL, new_index, ES6_USER, ES6_PASS):
            print(f"[ES6] Deleting existing index '{new_index}'...")
            delete_index(ES6_URL, new_index, ES6_USER, ES6_PASS, dry_run=False)

        # Read mapping and settings directly from ES6
        info = http_request(f"{ES6_URL}/{old_index}", username=ES6_USER, password=ES6_PASS)[old_index]
        settings = sanitize_settings(info.get("settings", {}).get("index", {}))
        mappings = info.get("mappings", {})

        print(f"[ES6] Creating index '{new_index}'...")
        http_request(
            f"{ES6_URL}/{new_index}",
            method="PUT",
            data={"settings": {"index": settings}, "mappings": mappings},
            username=ES6_USER,
            password=ES6_PASS
        )

        print(f"[ES6] Reindexing '{old_index}' -> '{new_index}'...")
        task = http_request(
            f"{ES6_URL}/_reindex?wait_for_completion=false",
            method="POST",
            data={"source": {"index": old_index}, "dest": {"index": new_index}},
            username=ES6_USER,
            password=ES6_PASS
        )
        wait_for_task(ES6_URL, task["task"], ES6_USER, ES6_PASS)

        print(f"[ES6] Creating alias '{new_alias}' -> '{new_index}'...")
        http_request(
            f"{ES6_URL}/_aliases",
            method="POST",
            data={"actions": [{"add": {"index": new_index, "alias": new_alias}}]},
            username=ES6_USER,
            password=ES6_PASS
        )

    return aliases

def run_es9_migration(es6_aliases):
    print("\n=== Starting Phase 2: ES9 Migration ===")
    if not es6_aliases:
        print("No ES6 aliases provided to migrate.")
        return

    nodes = http_request(f"{ES9_URL}/_cat/nodes?format=json", username=ES9_USER, password=ES9_PASS)
    if not nodes:
        raise RuntimeError("No nodes available on ES9.")
    target_node = nodes[0]["name"]

    for alias, es6_old_index in es6_aliases.items():
        print(f"\n[ES9] Resolving alias '{alias}' on ES9...")
        es9_old_index = resolve_alias_index(ES9_URL, alias, ES9_USER, ES9_PASS)

        if not es9_old_index:
            print(f"[WARN] Alias '{alias}' does not exist on ES9. Skipping...")
            continue

        es6_source_index = f"{es6_old_index}_upgrade"
        tmp_index = f"{es9_old_index}_tmp"
        final_index = f"{es9_old_index}_upgrade"
        final_alias = f"{alias}_upgrade"
        if index_exists(ES9_URL, final_index, ES9_USER, ES9_PASS):
            print(f"[ES9] Deleting existing index '{final_index}'...")
            delete_index(ES9_URL, final_index, ES9_USER, ES9_PASS, dry_run=False)
        
        if index_exists(ES9_URL, tmp_index, ES9_USER, ES9_PASS):
            print(f"[ES9] Deleting existing temp index '{tmp_index}'...")
            delete_index(ES9_URL, tmp_index, ES9_USER, ES9_PASS, dry_run=False)

        print(f"[ES9] Reading mapping and settings directly from ES9 index '{es9_old_index}'...")
        info = http_request(f"{ES9_URL}/{es9_old_index}", username=ES9_USER, password=ES9_PASS)[es9_old_index]
        settings = sanitize_settings(info.get("settings", {}).get("index", {}))
        mappings = info.get("mappings", {})

        # Create temporary index on ES9 with 5 shards
        settings["number_of_shards"] = 5
        settings["number_of_replicas"] = 0
        print(f"[ES9] Creating temp index '{tmp_index}' on ES9 with ES9's own mapping (shards: 5)...")
        http_request(
            f"{ES9_URL}/{tmp_index}",
            method="PUT",
            data={"settings": {"index": settings}, "mappings": mappings},
            username=ES9_USER,
            password=ES9_PASS
        )

        # Remote Reindex from ES6 into ES9 temp index
        print(f"[ES9] Remote reindexing from ES6 '{es6_source_index}' into ES9 '{tmp_index}'...")
        remote_cfg = {"host": ES6_URL}
        if ES6_USER and ES6_PASS:
            remote_cfg["username"] = ES6_USER
            remote_cfg["password"] = ES6_PASS

        task = http_request(
            f"{ES9_URL}/_reindex?wait_for_completion=false",
            method="POST",
            data={
                "source": {"remote": remote_cfg, "index": es6_source_index},
                "dest": {"index": tmp_index}
            },
            username=ES9_USER,
            password=ES9_PASS
        )
        wait_for_task(ES9_URL, task["task"], ES9_USER, ES9_PASS)

        # Prepare shrink on ES9
        print(f"[ES9] Locking writes and relocating shards to node '{target_node}'...")
        http_request(
            f"{ES9_URL}/{tmp_index}/_settings",
            method="PUT",
            data={
                "settings": {
                    "index.blocks.write": True,
                    "index.routing.allocation.require._name": target_node
                }
            },
            username=ES9_USER,
            password=ES9_PASS
        )

        http_request(
            f"{ES9_URL}/_cluster/health/{tmp_index}?wait_for_no_relocating_shards=true",
            username=ES9_USER,
            password=ES9_PASS
        )

        # Shrink to 1 shard
        print(f"[ES9] Shrinking '{tmp_index}' to '{final_index}' (shards: 1)...")
        http_request(
            f"{ES9_URL}/{tmp_index}/_shrink/{final_index}",
            method="POST",
            data={
                "settings": {
                    "index.number_of_shards": 1,
                    "index.number_of_replicas": 1,
                    "index.blocks.write": None,
                    "index.routing.allocation.require._name": None
                }
            },
            username=ES9_USER,
            password=ES9_PASS
        )

        http_request(
            f"{ES9_URL}/_cluster/health/{final_index}?wait_for_status=yellow",
            username=ES9_USER,
            password=ES9_PASS
        )

        print(f"[ES9] Deleting temporary index '{tmp_index}'...")
        http_request(f"{ES9_URL}/{tmp_index}", method="DELETE", username=ES9_USER, password=ES9_PASS)

        print(f"[ES9] Creating alias '{final_alias}' -> '{final_index}'...")
        http_request(
            f"{ES9_URL}/_aliases",
            method="POST",
            data={"actions": [{"add": {"index": final_index, "alias": final_alias}}]},
            username=ES9_USER,
            password=ES9_PASS
        )

    print("\n=== Migration Completed Successfully ===")

def run_cleanup():
    prefix = "[DRY-RUN] " if DRY_RUN else ""
    print(f"=== Starting Cleanup Mode {prefix}===")

    if TARGET_ALIAS:
        es6_aliases = fetch_aliases(ES6_URL, ES6_USER, ES6_PASS)
        es9_aliases = fetch_aliases(ES9_URL, ES9_USER, ES9_PASS)

        es6_indices = [f"{old_idx}_upgrade" for old_idx in es6_aliases.values()]
        es9_indices = []
        for old_idx in es9_aliases.values():
            es9_indices.extend([f"{old_idx}_tmp", f"{old_idx}_upgrade"])

        if CLEAN_SOURCE:
            es6_indices.extend(list(es6_aliases.values()))
    else:
        cat_es6 = http_request(f"{ES6_URL}/_cat/indices?format=json", username=ES6_USER, password=ES6_PASS)
        es6_indices = [row["index"] for row in cat_es6 if row["index"].endswith("_upgrade")]

        cat_es9 = http_request(f"{ES9_URL}/_cat/indices?format=json", username=ES9_USER, password=ES9_PASS)
        es9_indices = [row["index"] for row in cat_es9 if row["index"].endswith("_upgrade") or row["index"].endswith("_tmp")]

    print(f"\n--- ES6 Cleanup Targets ({len(es6_indices)} indices) ---")
    for idx in set(es6_indices):
        delete_index(ES6_URL, idx, ES6_USER, ES6_PASS, dry_run=DRY_RUN)

    print(f"\n--- ES9 Cleanup Targets ({len(es9_indices)} indices) ---")
    for idx in set(es9_indices):
        delete_index(ES9_URL, idx, ES9_USER, ES9_PASS, dry_run=DRY_RUN)

    print(f"\n=== Cleanup Mode Finished {prefix}===")

if __name__ == "__main__":
    try:
        if MODE == "cleanup":
            run_cleanup()
        else:
            resolved_es6 = run_es6_migration()
            if resolved_es6:
                run_es9_migration(resolved_es6)
    except Exception as error:
        print(f"\n[FATAL] Script failed: {error}", file=sys.stderr)
        sys.exit(1)