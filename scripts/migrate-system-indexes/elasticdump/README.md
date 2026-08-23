# Elasticsearch Security Migration via Elasticdump (ES6 → ES9)

This directory contains the pipeline for migrating Elasticsearch Security definitions (Roles, Users, and Bcrypt Password Hashes) using **`elasticdump`** from **ES 6.8** to **ES 9.x**.

---

## 🐳 Docker vs Node.js (`npx`) Execution

`elasticdump` can be executed using either **Node.js (`npx`)** or **Docker** (ideal for production VM environments where Node.js cannot be installed).

### Official Docker Image: `elasticdump/elasticsearch-dump`

| Method | Export / Import Command Pattern |
| :--- | :--- |
| **Node.js (`npx`)** | `npx -y elasticdump --input="..." --output="..." --type=data` |
| **Docker** | `docker run --rm -ti -v $(pwd):/data elasticdump/elasticsearch-dump --input="..." --output="..." --type=data` |

> **💡 Key Docker Usage Notes:**
> - `-v $(pwd):/data`: Mounts the host's current working directory into `/data` inside the container so dump files (`es6_security_dump.json`) are written directly to the host machine.
> - `--net=host`: Add this flag if connecting to an Elasticsearch instance running on `localhost` / `127.0.0.1` of the host VM.

---

## 🛑 Approach 1: Direct Restoration via Elasticdump (FAILS INTENTIONALLY)

Attempting to dump `.security-6` from ES6 and import directly into ES9's system index `.security-7` (or `.security`):

### Via `npx`:
```bash
# 1. Export from ES6:
npx -y elasticdump \
  --input="http://elastic:elastic@10.146.0.10:9200/.security-6" \
  --output="es6_security_dump.json" \
  --type=data

# 2. Direct Import into ES9 System Index (FAILS):
npx -y elasticdump \
  --input="es6_security_dump.json" \
  --output="http://elastic:elastic@10.146.0.11:9200/.security" \
  --type=data
```

### Via Docker:
```bash
# 1. Export from ES6:
docker run --rm -ti -v $(pwd):/data elasticdump/elasticsearch-dump \
  --input="http://elastic:elastic@10.146.0.10:9200/.security-6" \
  --output="/data/es6_security_dump.json" \
  --type=data

# 2. Direct Import into ES9 System Index (FAILS):
docker run --rm -ti -v $(pwd):/data elasticdump/elasticsearch-dump \
  --input="/data/es6_security_dump.json" \
  --output="http://elastic:elastic@10.146.0.11:9200/.security" \
  --type=data
```

### 💡 Solution to Bypass System Index Protection (`allow_restricted_indices: true`):
By default, even the `superuser` role cannot write to restricted indices (`.security`). To allow `elasticdump` to write directly into `.security`, create a custom role with `"allow_restricted_indices": true` and assign it to a migration user:

```bash
# 1. Create role with allow_restricted_indices permission on ES9:
curl -s -u elastic:elastic -XPOST "http://10.146.0.11:9200/_security/role/super_system_admin" \
  -H "Content-Type: application/json" \
  -d '{
    "cluster": ["all"],
    "indices": [
      {
        "names": [".security*"],
        "privileges": ["all"],
        "allow_restricted_indices": true
      }
    ]
  }'

# 2. Create system_migrator user with super_system_admin role on ES9:
curl -s -u elastic:elastic -XPOST "http://10.146.0.11:9200/_security/user/system_migrator" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "MigratorPass123!",
    "roles": ["superuser", "super_system_admin"],
    "full_name": "System Index Migrator"
  }'

# 3. Run elasticdump directly to .security index on ES9:
# Via npx:
npx -y elasticdump \
  --input="es6_security_dump.json" \
  --output='http://system_migrator:MigratorPass123!@10.146.0.11:9200/.security' \
  --type=data

# Via Docker:
docker run --rm -ti -v $(pwd):/data elasticdump/elasticsearch-dump \
  --input="/data/es6_security_dump.json" \
  --output='http://system_migrator:MigratorPass123!@10.146.0.11:9200/.security' \
  --type=data
```

---

## 🏗️ Approach 2: Working 3-Step Pipeline (Intermediate Index → ES9 REST API)

To bypass system index protection while using `elasticdump`, restore the dump to a standard (non-system) intermediate index or parse the dump file, then register the extracted roles and users via ES9 REST APIs:

```mermaid
graph TD;
    A[ES6 Cluster .security-6] -->|1. elasticdump export| B[es6_security_dump.json]
    B -->|2. elasticdump import| C[ES9 Cluster: imported-es6-security index]
    B -->|3. apply_dumped_security.py| D[ES9 REST API: /_security/role & /_security/user]
    C -->|Alternative direct parsing| D
```

1. **Dump (.security-6 → JSON File)**: Export documents from ES6's `.security-6` system index into a local line-delimited JSON file (`es6_security_dump.json`).
2. **Intermediate Index (.security-6 → ES9 `imported-es6-security`)**: Restore the dump into a standard (non-system) index `imported-es6-security` on ES9.
3. **Registration (Parse → ES9 Security REST API)**: Parse the documents (extracting custom roles, native users, and bcrypt `password_hash` strings), strip system metadata keys (`_reserved`), and register them on ES9 via standard `/_security/role` and `/_security/user` APIs using `apply_dumped_security.py`.

---

## 🚀 How to Run the Working Pipeline

### Option A: Automated Pipeline Shell Script (Auto-detects npx or Docker)
```bash
cd scripts/migrate-system-indexes/elasticdump
chmod +x migrate_security_elasticdump.sh
./migrate_security_elasticdump.sh
```

### Option B: Step-by-Step Manual Commands

#### Step 1: Export `.security-6` from ES6 via `elasticdump`
```bash
# Using npx:
npx -y elasticdump \
  --input="http://elastic:elastic@10.146.0.10:9200/.security-6" \
  --output="es6_security_dump.json" \
  --type=data

# Using Docker (Prod VM without Node.js):
docker run --rm -ti -v $(pwd):/data elasticdump/elasticsearch-dump \
  --input="http://elastic:elastic@10.146.0.10:9200/.security-6" \
  --output="/data/es6_security_dump.json" \
  --type=data
```

#### Step 2: Import into ES9 Intermediate Index
```bash
# Using npx:
npx -y elasticdump \
  --input="es6_security_dump.json" \
  --output="http://elastic:elastic@10.146.0.11:9200/imported-es6-security" \
  --type=data

# Using Docker (Prod VM without Node.js):
docker run --rm -ti -v $(pwd):/data elasticdump/elasticsearch-dump \
  --input="/data/es6_security_dump.json" \
  --output="http://elastic:elastic@10.146.0.11:9200/imported-es6-security" \
  --type=data
```

#### Step 3: Apply Roles & Users to ES9 Security APIs
```bash
python3 apply_dumped_security.py es6_security_dump.json
```

---

## 🔍 Verification & Cleanup

### Verify Migrated User on ES9:
```bash
curl -s -u bench_reader:ReaderPass123! "http://10.146.0.11:9200/_security/_authenticate" | jq .
```

### Clean Up Intermediate Index on ES9:
```bash
curl -s -u elastic:elastic -XDELETE "http://10.146.0.11:9200/imported-es6-security"
```

