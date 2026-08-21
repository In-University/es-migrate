# Lab: Elasticsearch Index & RBAC Security Migration (ES6 → ES9)

This lab demonstrates how to migrate Role-Based Access Control (RBAC) security configuration (Roles & Users) from **Elasticsearch 6.8** to **Elasticsearch 9.x**, while preserving granular index permissions and authorization policies.

---

## 1. Overview & Architecture

- **ES6 Source Node (`es6-source`)**:
  - `xpack.security.enabled: true`
  - Admin credentials: `elastic` / `<elastic_password>`
  - Sample Roles created:
    - `bench_reader_role`: Read-only privileges (`read`, `view_index_metadata`) on `bench-*` / `bench-es6*`.
    - `bench_writer_role`: Read/Write privileges (`read`, `write`, `create_doc`, `index`, `delete`) on `bench-*` / `bench-es6*`.
    - `bench_admin_role`: All index privileges (`all`) on `bench-*` + cluster monitoring.
  - Sample Users created:
    - `bench_reader` (Password: `ReaderPass123!`)
    - `bench_writer` (Password: `WriterPass123!`)
    - `bench_admin` (Password: `AdminPass123!`)

- **ES9 Destination Node (`es9-dest`)**:
  - `xpack.security.enabled: true`
  - Admin credentials: `elastic` / `<elastic_password>`
  - **Clean State**: Security enabled, but NO custom roles or users exist yet.

---

## 2. Environment Initialization

Sample security roles and users are **automatically seeded on ES6 during VM startup** via Terraform (`startup-es6.sh.tpl`).

When `terraform apply` completes:
1. ES6 starts with Security enabled and pre-configured with sample roles (`bench_reader_role`, `bench_writer_role`, `bench_admin_role`) and users (`bench_reader`, `bench_writer`, `bench_admin`).
2. ES9 starts with Security enabled, but in a **clean state** (no custom roles/users created yet), ready for the migration lab.

---

## 3. Hands-on Lab: Manual cURL Migration (1 Role & 1 User)

Follow this step-by-step walkthrough to manually migrate a single role (`bench_reader_role`) and user (`bench_reader`) from ES6 to ES9.

### Step 3.1: Inspect Role & User on ES6
```bash
# View role definition on ES6
curl -s -u elastic:elastic "http://10.146.0.10:9200/_security/role/bench_reader_role" | jq .

# View user metadata on ES6
curl -s -u elastic:elastic "http://10.146.0.10:9200/_security/user/bench_reader" | jq .
```

### Step 3.2: Extract Bcrypt Password Hash from ES6
Query the `.security` system index on ES6 directly to extract the bcrypt hash string stored in field `._source.password`:
```bash
# Extract bcrypt hash string directly from ES6 system index
HASH_READER=$(curl -s -u elastic:elastic "http://10.146.0.10:9200/.security/_doc/user-bench_reader" | jq -r '._source.password')

echo "Extracted Hash: $HASH_READER"
# Output example: "$2a$10$UWqWhSf.sfUTVskactnubObYjvdqMJZELktb7NxTLO2O7X26Gy/1m"
```

### Step 3.3: Import Role to ES9
Create `bench_reader_role` on ES9:
```bash
curl -s -u elastic:elastic -XPOST "http://10.146.0.11:9200/_security/role/bench_reader_role" \
  -H "Content-Type: application/json" \
  -d '{
    "cluster": ["monitor"],
    "indices": [
      {
        "names": ["bench-*", "bench-es6*", "bench-es9*"],
        "privileges": ["read", "view_index_metadata"]
      }
    ]
  }'
```

### Step 3.4: Import User with `password_hash` to ES9
Create `bench_reader` on ES9 using `"password_hash"` so the original password remains unchanged:
```bash
curl -s -u elastic:elastic -XPOST "http://10.146.0.11:9200/_security/user/bench_reader" \
  -H "Content-Type: application/json" \
  -d "{
    \"roles\": [\"bench_reader_role\"],
    \"full_name\": \"Bench Reader User\",
    \"email\": \"reader@example.com\",
    \"password_hash\": \"$HASH_READER\"
  }"
```

---

## 4. Automated Security Migration via Python

Alternatively, run the automated Python migration script which handles extracting `password_hash` from ES6's `.security` index and importing roles/users into ES9 automatically:

```bash
# Run from repository root (defaults: ES6=10.146.0.10:9200, ES9=10.146.0.11:9200, password=elastic)
python3 scripts/migrate-system-indexes/hashpassword/migrate_security_es6_to_es9.py

# Optional: Override URLs/credentials if running from localhost port-forward:
ES6_URL="http://localhost:9200" ES9_URL="http://10.146.0.11:9200" ES6_PW="elastic" ES9_PW="elastic" \
python3 scripts/migrate-system-indexes/hashpassword/migrate_security_es6_to_es9.py
```

---

## 5. Verification on ES9

Verify that the migrated users authenticate successfully and RBAC rules are enforced on `bench-es9`:

1. **Authenticate as `bench_reader` on ES9**:
   ```bash
   curl -s -u bench_reader:ReaderPass123! "http://10.146.0.11:9200/_security/_authenticate" | jq .
   ```

2. **Test Read Access on `bench-es9`**:
   ```bash
   curl -s -u bench_reader:ReaderPass123! "http://10.146.0.11:9200/bench-es9/_count"
   # -> HTTP 200 OK
   ```

3. **Test Write Access Denial for `bench_reader`**:
   ```bash
   curl -s -u bench_reader:ReaderPass123! -XPUT "http://10.146.0.11:9200/bench-es9/_doc/test1" \
     -H "Content-Type: application/json" -d '{"title": "test"}'
   # -> HTTP 403 Forbidden ("action [indices:data/write/index] is unauthorized for user [bench_reader]")
   ```

4. **Test Write Access Success for `bench_writer`**:
   ```bash
   curl -s -u bench_writer:WriterPass123! -XPUT "http://10.146.0.11:9200/bench-es9/_doc/test1" \
     -H "Content-Type: application/json" -d '{"title": "test"}'
   # -> HTTP 201 Created
   ```

---

## 6. Resetting / Cleaning Up ES9 Security Definitions

To reset ES9 back to a clean state for re-testing:

### Option A: Automated Cleanup via Python
```bash
python3 scripts/migrate-system-indexes/hashpassword/migrate_security_es6_to_es9.py --clean
```

### Option B: Manual Cleanup via cURL
```bash
# Delete custom users from ES9
curl -s -u elastic:elastic -XDELETE "http://10.146.0.11:9200/_security/user/bench_reader"
curl -s -u elastic:elastic -XDELETE "http://10.146.0.11:9200/_security/user/bench_writer"
curl -s -u elastic:elastic -XDELETE "http://10.146.0.11:9200/_security/user/bench_admin"

# Delete custom roles from ES9
curl -s -u elastic:elastic -XDELETE "http://10.146.0.11:9200/_security/role/bench_reader_role"
curl -s -u elastic:elastic -XDELETE "http://10.146.0.11:9200/_security/role/bench_writer_role"
curl -s -u elastic:elastic -XDELETE "http://10.146.0.11:9200/_security/role/bench_admin_role"

```

---

## Summary

- Both ES6 and ES9 run with Security enabled (`xpack.security.enabled: true`).
- Custom RBAC roles and users are automatically initialized on ES6 at VM startup via Terraform.
- ES9 starts clean for lab hands-on migration practice.
- Security migration script (`migrate_security_es6_to_es9.py`) automates role/user export, transformation, import, and verification.
