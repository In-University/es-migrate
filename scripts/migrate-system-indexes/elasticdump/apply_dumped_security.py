#!/usr/bin/env python3
"""
Apply dumped ES6 security index documents to ES9 Security APIs.

Reads elasticdump JSON dump file (es6_security_dump.json) or fetches from
an intermediate index (imported-es6-security) on ES9, parses roles & users,
and registers them into ES9 via REST API by reusing migrate_security_es6_to_es9 modules.
"""

import json
import os
import sys

# Dynamically resolve path to import migrate_security_es6_to_es9 from hashpassword folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
HASHPASSWORD_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "hashpassword"))
if HASHPASSWORD_DIR not in sys.path:
    sys.path.insert(0, HASHPASSWORD_DIR)

from migrate_security_es6_to_es9 import (
    http_request,
    find_bcrypt_hash,
    import_es9_security,
    verify_es9_security,
    RESERVED_ROLES,
    RESERVED_USERS,
    ES9_URL,
    ES9_USER,
    ES9_PW
)

BUILTIN_PREFIXES = ("kibana_", "beats_", "logstash_", "apm_", "watcher_", "rollup_", "snapshot_", "reporting_", "monitoring_", "transform_", "machine_learning_")


def parse_dump_documents(docs):
    roles = {}
    users = {}

    for doc in docs:
        doc_id = str(doc.get("_id", ""))
        src = doc.get("_source", {})
        doc_type = src.get("type", "")

        # Process Role
        if doc_type == "role" or doc_id.startswith("role-"):
            rname = src.get("name") or (doc_id[5:] if doc_id.startswith("role-") else doc_id)
            if rname in RESERVED_ROLES or any(rname.startswith(p) for p in BUILTIN_PREFIXES):
                continue
            raw_meta = src.get("metadata", {}) or {}
            clean_meta = {k: v for k, v in raw_meta.items() if not k.startswith("_")}
            roles[rname] = {
                "cluster": src.get("cluster", []),
                "indices": src.get("indices", []),
                "applications": src.get("applications", []),
                "run_as": src.get("run_as", []),
                "metadata": clean_meta
            }

        # Process User
        elif doc_type == "user" or doc_id.startswith("user-"):
            uname = src.get("username") or (doc_id[5:] if doc_id.startswith("user-") else doc_id)
            if uname in RESERVED_USERS:
                continue
            phash = find_bcrypt_hash(src)
            if not phash:
                print(f"[SKIP] User '{uname}' missing bcrypt password hash in dump.")
                continue

            raw_meta = src.get("metadata", {}) or {}
            clean_meta = {k: v for k, v in raw_meta.items() if not k.startswith("_")}
            users[uname] = {
                "password_hash": phash,
                "roles": src.get("roles", []),
                "full_name": src.get("full_name", ""),
                "email": src.get("email", ""),
                "metadata": clean_meta
            }

    return roles, users


def main():
    dump_file = sys.argv[1] if len(sys.argv) > 1 else "es6_security_dump.json"
    docs = []

    if os.path.exists(dump_file):
        print(f">> Reading dump file: {dump_file}")
        with open(dump_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith("{") and "hits" in content:
                try:
                    parsed = json.loads(content)
                    docs = parsed.get("hits", {}).get("hits", [])
                except Exception:
                    pass
            if not docs:
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        try:
                            docs.append(json.loads(line))
                        except Exception:
                            pass
    else:
        print(f">> Dump file '{dump_file}' not found locally. Fetching from intermediate index 'imported-es6-security' on ES9...")
        code, resp = http_request(ES9_URL, "/imported-es6-security/_search?size=1000", user=ES9_USER, pw=ES9_PW)
        if code == 200:
            hits = resp.get("hits", {}).get("hits", [])
            docs = hits
        else:
            print(f"[ERROR] Could not fetch intermediate index 'imported-es6-security' from ES9 (HTTP {code}): {resp}")
            sys.exit(1)

    print(f">> Parsed {len(docs)} document(s) from dump.")
    roles, users = parse_dump_documents(docs)

    # Reuse import_es9_security from migrate_security_es6_to_es9 module
    if import_es9_security(roles, users):
        verify_es9_security()


if __name__ == "__main__":
    main()
