#!/usr/bin/env python3
"""
Generate simulation configuration files for Elasticsearch indices/aliases.
Queries Elasticsearch for active aliases -> concrete indices, samples 1 record per index,
and creates template configs in configs/<index>.json with:
  - create: sample fields + "upgrade_modified_at": "{{timestamp}}"
  - update: "upgrade_modified_at": "{{timestamp}}"
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_DIR = os.path.join(SCRIPT_DIR, "configs")

ES_URL = os.environ.get("ES_URL", os.environ.get("ES9_URL", os.environ.get("ES6_URL", "http://localhost:9200"))).rstrip("/")
ES_USER = os.environ.get("ES_USER", os.environ.get("ES9_USER", os.environ.get("ES6_USER", "elastic")))
ES_PW = os.environ.get("ES_PASS", os.environ.get("ES9_PASS", os.environ.get("ES6_PW", os.environ.get("ES_PW", ""))))
ENV_INDICES = os.environ.get("INDICES", os.environ.get("CLONE_INDICES", ""))


def es_http(method: str, path: str, body: Optional[Any] = None) -> Any:
    url = f"{ES_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if ES_PW:
        auth = base64.b64encode(f"{ES_USER}:{ES_PW}".encode()).decode()
        headers["Authorization"] = f"Basic {auth}"

    data_bytes = None
    if body is not None:
        data_bytes = json.dumps(body).encode("utf-8") if not isinstance(body, bytes) else body

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        err_msg = e.read().decode("utf-8") if e.fp else str(e)
        print(f"[ERROR] HTTP {e.code} on {method} {path}: {err_msg}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"[ERROR] Network error on {method} {path}: {e}", file=sys.stderr)
        raise


def get_alias_indices() -> tuple:
    """
    Returns a mapping of (alias_name -> list of concrete_index_names, concrete_indices_dict).
    """
    aliases_data = es_http("GET", "/_aliases")
    alias_to_indices: Dict[str, List[str]] = {}
    concrete_indices: Dict[str, List[str]] = {}

    for index_name, meta in aliases_data.items():
        if index_name.startswith("."):
            continue
        aliases = meta.get("aliases", {})
        if aliases:
            concrete_indices[index_name] = list(aliases.keys())
            for alias_name in aliases.keys():
                if alias_name not in alias_to_indices:
                    alias_to_indices[alias_name] = []
                alias_to_indices[alias_name].append(index_name)

    return alias_to_indices, concrete_indices


def get_all_concrete_indices() -> List[str]:
    cat_data = es_http("GET", "/_cat/indices?format=json")
    indices = []
    if isinstance(cat_data, list):
        for item in cat_data:
            idx = item.get("index", "")
            if idx and not idx.startswith("."):
                indices.append(idx)
    return indices


def fetch_sample_doc(index_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetches 1 random/sample document from the target index.
    """
    try:
        search_res = es_http("POST", f"/{index_name}/_search", body={"size": 1, "query": {"match_all": {}}})
        hits = search_res.get("hits", {}).get("hits", [])
        if hits:
            return hits[0].get("_source", {})
    except Exception as e:
        print(f"   [WARN] Could not fetch sample document from '{index_name}': {e}", file=sys.stderr)
    return None


def sanitize_create_template(source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes sample source document into a reusable create template.
    Ensures 'upgrade_modified_at': '{{timestamp}}' is included.
    """
    template = {}
    for k, v in source.items():
        if k in ("id", "_id"):
            template[k] = "{{id}}"
        elif isinstance(v, (int, float, bool, list, dict)):
            template[k] = v
        elif isinstance(v, str):
            template[k] = v
        else:
            template[k] = v

    # Guarantee upgrade_modified_at is set
    template["upgrade_modified_at"] = "{{timestamp}}"
    return template


def build_index_config(index_name: str, sample_source: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Builds the full index configuration containing 'create' and 'update' patterns.
    """
    if sample_source:
        create_tmpl = sanitize_create_template(sample_source)
    else:
        create_tmpl = {
            "id": "{{id}}",
            "name": "Item {{counter}}",
            "status": "active",
            "upgrade_modified_at": "{{timestamp}}"
        }

    update_tmpl = {
        "upgrade_modified_at": "{{timestamp}}"
    }

    return {
        index_name: {
            "create": create_tmpl,
            "update": update_tmpl
        }
    }


def main():
    global ES_URL
    parser = argparse.ArgumentParser(description="Generate simulation configs for Elasticsearch indices/aliases.")
    parser.add_argument("--es-url", default=ES_URL, help=f"Elasticsearch Base URL (default: {ES_URL})")
    parser.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR, help=f"Output directory for config JSONs (default: {DEFAULT_CONFIG_DIR})")
    parser.add_argument("--indices", default=ENV_INDICES, help="Comma-separated list of indices or aliases to generate configs for")
    parser.add_argument("--overwrite", action="store_true", default=True, help="Overwrite existing config files (default: True)")

    args = parser.parse_args()

    ES_URL = args.es_url.rstrip("/")
    config_dir = os.path.abspath(args.config_dir)
    os.makedirs(config_dir, exist_ok=True)

    print("==================================================")
    print(">> ES CONFIG GENERATOR (SAMPLE-BASED AUTO TEMPLATE)")
    print("==================================================")
    print(f"   Elasticsearch URL : {ES_URL}")
    print(f"   Auth User         : {ES_USER}")
    print(f"   Output Config Dir : {config_dir}")
    print(f"   Filter Indices    : {args.indices if args.indices else 'ALL'}")
    print("--------------------------------------------------")

    print("[1/3] Discovering aliases and concrete indices...")
    try:
        alias_to_indices, concrete_with_aliases = get_alias_indices()
    except Exception as e:
        print(f"[FATAL] Failed to connect to Elasticsearch: {e}", file=sys.stderr)
        sys.exit(1)

    target_indices = set()
    if args.indices:
        filter_items = [x.strip() for x in args.indices.split(",") if x.strip()]
        for item in filter_items:
            if item in alias_to_indices:
                target_indices.update(alias_to_indices[item])
            else:
                target_indices.add(item)
    else:
        if concrete_with_aliases:
            target_indices.update(concrete_with_aliases.keys())
        else:
            print("   No active aliases found. Fetching all non-system indices...")
            target_indices.update(get_all_concrete_indices())

    target_indices = sorted(list(target_indices))
    print(f"   Found {len(target_indices)} target concrete index(es): {', '.join(target_indices)}")

    if not target_indices:
        print("[WARNING] No target indices found to generate configuration.", file=sys.stderr)
        sys.exit(0)

    print(f"\n[2/3] Sampling records and generating config files in '{config_dir}'...")
    generated_count = 0
    for idx_name in target_indices:
        print(f"   -> Processing index '{idx_name}'...")
        sample_doc = fetch_sample_doc(idx_name)
        if sample_doc:
            print(f"      [OK] Sample document retrieved ({len(sample_doc)} fields).")
        else:
            print("      [INFO] Index is empty or no doc found. Using standard template.")

        config_data = build_index_config(idx_name, sample_doc)
        output_file = os.path.join(config_dir, f"{idx_name}.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"      [SAVED] {output_file}")
        generated_count += 1

    print("\n[3/3] Execution Summary:")
    print(f"   Total Configs Generated : {generated_count}")
    print(f"   Configs Directory       : {config_dir}")
    print("==================================================")
    print(">> CONFIG GENERATION COMPLETED!")


if __name__ == "__main__":
    main()
