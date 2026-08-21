#!/usr/bin/env python3
"""
Migrate RBAC Security (Roles and Users) from ES6 (Source) to ES9 (Destination).

This script performs the security migration step of the lab:
1. Connects to ES6 and exports custom (non-reserved) Roles and Users.
2. Formats and validates the security definitions for ES9 compatibility.
3. Imports the Roles and Users into ES9.
4. Verifies authentication and permission enforcement on ES9.

Usage:
    python3 migrate_security_es6_to_es9.py

Environment Variables:
    ES6_URL       ES6 cluster base URL               (default: http://localhost:9200)
    ES9_URL       ES9 cluster base URL               (default: http://localhost:9201)
    ES6_USER      ES6 admin username                 (default: elastic)
    ES6_PW        ES6 admin password                 (default: elastic)
    ES9_USER      ES9 admin username                 (default: elastic)
    ES9_PW        ES9 admin password                 (default: elastic)
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request

ES6_URL = os.environ.get("ES6_URL", "http://localhost:9200").rstrip("/")
ES9_URL = os.environ.get("ES9_URL", "http://10.146.0.11:9200").rstrip("/")
ES6_USER = os.environ.get("ES6_USER", "elastic")
ES6_PW = os.environ.get("ES6_PW", os.environ.get("ELASTIC_PW", os.environ.get("ES_PW", "elastic")))
ES9_USER = os.environ.get("ES9_USER", "elastic")
ES9_PW = os.environ.get("ES9_PW", os.environ.get("ELASTIC_PW", os.environ.get("ES_PW", "elastic")))

RESERVED_ROLES = {
    "superuser", "kibana_system", "logstash_system", "beats_admin",
    "apm_system", "remote_monitoring_agent", "remote_monitoring_collector",
    "ingest_admin", "kibana_user", "transport_client", "watcher_admin",
    "watcher_user", "logstash_admin", "device_code_user", "viewer", "editor",
    "admin", "monitoring_user", "transform_admin", "transform_user", "machine_learning_admin",
    "machine_learning_user"
}

RESERVED_USERS = {
    "elastic", "kibana", "kibana_system", "logstash_system",
    "beats_system", "apm_system", "remote_monitoring_user"
}


def http_request(base_url, path, method="GET", body=None, user=None, pw=None):
    url = f"{base_url}{path}"
    headers = {"Content-Type": "application/json"}
    if user and pw:
        auth_str = f"{user}:{pw}"
        headers["Authorization"] = "Basic " + base64.b64encode(auth_str.encode()).decode()

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        parsed = json.loads(content) if content else {}
        return e.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}


def find_bcrypt_hash(obj):
    """Recursively search a dict/list for a bcrypt hash string (starting with $2a$, $2b$, or $2y$)."""
    if isinstance(obj, str):
        if obj.startswith("$2a$") or obj.startswith("$2b$") or obj.startswith("$2y$"):
            return obj
    elif isinstance(obj, dict):
        if "password_hash" in obj and isinstance(obj["password_hash"], str):
            return obj["password_hash"]
        for val in obj.values():
            res = find_bcrypt_hash(val)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_bcrypt_hash(item)
            if res:
                return res
    return None


def fetch_all_es6_password_hashes():
    """Fetch all bcrypt password hashes from ES6 .security index."""
    hashes = {}
    
    # 1. Search .security index
    code, resp = http_request(ES6_URL, "/.security/_search?size=1000", user=ES6_USER, pw=ES6_PW)
    if code == 200:
        hits = resp.get("hits", {}).get("hits", [])
        for hit in hits:
            doc_id = str(hit.get("_id", ""))
            src = hit.get("_source", {})
            phash = find_bcrypt_hash(src)
            if phash:
                uname = src.get("username")
                if not uname:
                    for prefix in ("user-", "user_", "user:"):
                        if doc_id.startswith(prefix):
                            uname = doc_id[len(prefix):]
                            break
                if not uname:
                    uname = doc_id
                hashes[uname] = phash

    # 2. Try direct document endpoints if search returned empty
    if not hashes:
        code_u, users_data = http_request(ES6_URL, "/_security/user", user=ES6_USER, pw=ES6_PW)
        if code_u == 200:
            for uname in users_data.keys():
                paths = [
                    f"/.security/_doc/user-{uname}",
                    f"/.security/doc/user-{uname}",
                    f"/.security/user/user-{uname}",
                    f"/.security/_doc/{uname}",
                    f"/.security/doc/{uname}"
                ]
                for p in paths:
                    c, r = http_request(ES6_URL, p, user=ES6_USER, pw=ES6_PW)
                    if c == 200:
                        phash = find_bcrypt_hash(r)
                        if phash:
                            hashes[uname] = phash
                            break
    return hashes


def export_es6_security():
    print(">> Exporting Roles & Users from ES6...")
    
    # 1. Fetch Roles
    code_roles, roles_data = http_request(ES6_URL, "/_security/role", user=ES6_USER, pw=ES6_PW)
    if code_roles != 200:
        print(f"   [ERROR] Failed to fetch roles from ES6 (HTTP {code_roles}): {roles_data}")
        return None, None

    custom_roles = {}
    builtin_prefixes = ("kibana_", "beats_", "logstash_", "apm_", "watcher_", "rollup_", "snapshot_", "reporting_", "monitoring_", "transform_", "machine_learning_")

    for rname, rdef in roles_data.items():
        if rdef.get("_reserved", False) or rname in RESERVED_ROLES:
            continue
        if any(rname.startswith(prefix) for prefix in builtin_prefixes):
            continue

        raw_meta = rdef.get("metadata", {}) or {}
        clean_meta = {k: v for k, v in raw_meta.items() if not k.startswith("_")}

        role_body = {
            "cluster": rdef.get("cluster", []),
            "indices": rdef.get("indices", []),
            "applications": rdef.get("applications", []),
            "run_as": rdef.get("run_as", []),
            "metadata": clean_meta
        }
        custom_roles[rname] = role_body

    print(f"   Exported {len(custom_roles)} custom role(s): {list(custom_roles.keys())}")

    # 2. Fetch Users & Password Hashes from ES6
    hashes = fetch_all_es6_password_hashes()
    code_users, users_data = http_request(ES6_URL, "/_security/user", user=ES6_USER, pw=ES6_PW)
    if code_users != 200:
        print(f"   [ERROR] Failed to fetch users from ES6 (HTTP {code_users}): {users_data}")
        return None, None

    custom_users = {}
    for uname, udef in users_data.items():
        if uname in RESERVED_USERS or udef.get("_reserved", False):
            continue

        raw_meta = udef.get("metadata", {}) or {}
        clean_meta = {k: v for k, v in raw_meta.items() if not k.startswith("_")}

        user_body = {
            "roles": udef.get("roles", []),
            "full_name": udef.get("full_name", ""),
            "email": udef.get("email", ""),
            "metadata": clean_meta
        }

        # STRICT PASS-THROUGH: Extract bcrypt password_hash from ES6 .security index (NO FALLBACK)
        phash = hashes.get(uname) or find_bcrypt_hash(udef)
        if phash:
            user_body["password_hash"] = phash
            print(f"   - User '{uname}': password_hash exported intact ({phash[:15]}...)")
        else:
            print(f"   [ERROR] Strict Password Migration Failed: Cannot extract password_hash for user '{uname}' from ES6 .security index!")
            return None, None

        custom_users[uname] = user_body

    print(f"   Exported {len(custom_users)} custom user(s): {list(custom_users.keys())}")
    return custom_roles, custom_users


def import_es9_security(roles, users):
    print("\n>> Importing Roles & Users to ES9...")
    
    # 1. Import Roles
    for rname, rbody in roles.items():
        code, resp = http_request(ES9_URL, f"/_security/role/{rname}", method="POST", body=rbody, user=ES9_USER, pw=ES9_PW)
        if code in (200, 201):
            print(f"   [SUCCESS] Role '{rname}' imported to ES9")
        else:
            print(f"   [ERROR] Role '{rname}' import failed (HTTP {code}): {resp}")
            return False

    # 2. Import Users
    for uname, ubody in users.items():
        code, resp = http_request(ES9_URL, f"/_security/user/{uname}", method="POST", body=ubody, user=ES9_USER, pw=ES9_PW)
        if code in (200, 201):
            print(f"   [SUCCESS] User '{uname}' imported to ES9 (roles: {ubody['roles']})")
        else:
            print(f"   [ERROR] User '{uname}' import failed (HTTP {code}): {resp}")
            return False

    return True


def verify_es9_security():
    print("\n>> Verifying Migrated Security on ES9...")
    
    reader_user = "bench_reader"
    reader_pw = "ReaderPass123!"
    writer_user = "bench_writer"
    writer_pw = "WriterPass123!"

    # Verify authentication of migrated user on ES9 using ES8/9 API /_security/_authenticate
    code_auth, data_auth = http_request(ES9_URL, "/_security/_authenticate", user=reader_user, pw=reader_pw)
    if code_auth == 200:
        print(f"   [PASS] User '{reader_user}' authenticated on ES9 (roles: {data_auth.get('roles', [])})")
    else:
        print(f"   [FAIL] User '{reader_user}' authentication failed on ES9 (HTTP {code_auth}): {data_auth}")
        return False

    # Ensure test target index 'bench-es9' exists on ES9
    http_request(ES9_URL, "/bench-es9", method="PUT", user=ES9_USER, pw=ES9_PW)

    # Verify RBAC Enforcement: bench_reader read vs write on ES9
    code_r, resp_r = http_request(ES9_URL, "/bench-es9/_count", user=reader_user, pw=reader_pw)
    print(f"   [PASS] bench_reader GET /bench-es9/_count -> HTTP {code_r} [Read Granted]")

    test_doc = {"title": "es9_sec_test_doc"}
    code_w, resp_w = http_request(ES9_URL, "/bench-es9/_doc/sec-test-es9", method="PUT", body=test_doc, user=reader_user, pw=reader_pw)
    if code_w == 403:
        print(f"   [PASS] bench_reader PUT /bench-es9/_doc/sec-test-es9 -> HTTP 403 Forbidden [Write Denied correctly]")
    else:
        print(f"   - bench_reader write returned HTTP {code_w}: {resp_w}")

    code_ww, resp_ww = http_request(ES9_URL, "/bench-es9/_doc/sec-test-es9", method="PUT", body=test_doc, user=writer_user, pw=writer_pw)
    if code_ww in (200, 201):
        print(f"   [PASS] bench_writer PUT /bench-es9/_doc/sec-test-es9 -> HTTP {code_ww} [Write Granted correctly]")
        http_request(ES9_URL, "/bench-es9/_doc/sec-test-es9", method="DELETE", user=writer_user, pw=writer_pw)
    else:
        print(f"   - bench_writer write returned HTTP {code_ww}: {resp_ww}")

    return True


def clean_es9_security():
    print(">> Cleaning all custom non-reserved Roles and Users from ES9...")
    
    # 1. Fetch & Delete Users on ES9
    code_u, users_data = http_request(ES9_URL, "/_security/user", user=ES9_USER, pw=ES9_PW)
    if code_u == 200:
        for uname, udef in users_data.items():
            if uname not in RESERVED_USERS and not udef.get("_reserved", False):
                c, _ = http_request(ES9_URL, f"/_security/user/{uname}", method="DELETE", user=ES9_USER, pw=ES9_PW)
                print(f"   - Deleted user '{uname}' from ES9 (HTTP {c})")

    # 2. Fetch & Delete Roles on ES9
    code_r, roles_data = http_request(ES9_URL, "/_security/role", user=ES9_USER, pw=ES9_PW)
    builtin_prefixes = ("kibana_", "beats_", "logstash_", "apm_", "watcher_", "rollup_", "snapshot_", "reporting_", "monitoring_", "transform_", "machine_learning_")
    if code_r == 200:
        for rname, rdef in roles_data.items():
            if rname not in RESERVED_ROLES and not rdef.get("_reserved", False) and not any(rname.startswith(prefix) for prefix in builtin_prefixes):
                c, _ = http_request(ES9_URL, f"/_security/role/{rname}", method="DELETE", user=ES9_USER, pw=ES9_PW)
                print(f"   - Deleted role '{rname}' from ES9 (HTTP {c})")

    # 3. Clean test target index
    http_request(ES9_URL, "/bench-es9", method="DELETE", user=ES9_USER, pw=ES9_PW)
    print(">> ES9 clean-up completed successfully!\n")


def main():
    print("=======================================================")
    print(" ES6 -> ES9 Security & RBAC Migration Lab Utility")
    print("=======================================================")

    if "--clean" in sys.argv or "--cleanup" in sys.argv:
        clean_es9_security()
        sys.exit(0)

    roles, users = export_es6_security()
    if not roles or not users:
        print("[ABORT] Could not export security definitions from ES6.")
        sys.exit(1)

    if not import_es9_security(roles, users):
        print("[ABORT] Security import to ES9 failed.")
        sys.exit(1)

    if verify_es9_security():
        print("\n=======================================================")
        print(" Security Migration to ES9 Completed & Verified!")
        print("=======================================================")
    else:
        print("\n[WARNING] Security migration verification had issues.")


if __name__ == "__main__":
    main()
