# Test Strategy: Elasticsearch 9.x to 6.x Delta-Sync Rollback

## 1. Overview & Objective
This strategy validates the rollback mechanism from **Elasticsearch 9.2.3** back to **Elasticsearch 6.8.21**. If post-upgrade issues occur on ES 9.x, all mutations (Create, Update, Delete) made during the live window must be reversely synced to ES 6.x using timestamp-based delta sync (`upgrade_modified_at`) with **zero data loss and zero schema discrepancy**.

---

## 2. Testing Approach & Architectural Decisions

### Direct ES-Level Testing vs. Application API
We test directly at the **Elasticsearch REST API layer** instead of routing through Application APIs:

* **Throughput & Scale**: Stress-testing rollback with 100k–1M+ mutations in minutes requires bulk-level throughput, which is throttled by application web layers (auth, sessions, middlewares).
* **Deterministic Ground Truth**: Direct ES simulation records exact operations (`create`, `update`, `delete`) and exact payload bodies to `report.ndjson` for 1:1 mathematical verification.
* **Fault Isolation**: Isolates Elasticsearch storage, indexing, and sync engine behavior from unrelated application bugs.
* **Scope Boundary**: 
  - *Storage/Sync Layer (This Strategy)*: Validates delta sync capture, reverse reindexing, and data reconciliation.
  - *Application Layer (Separate Test Suite)*: Validates that upstream services properly populate `upgrade_modified_at` on every write.

---

## 3. Test Pipeline (Execution Flow)

The validation executes in 3 sequential phases:

```
[Phase 1: Mutate]               [Phase 2: Rollback]              [Phase 3: Verify]
simulate_multi_index.py  -->    Delta-Sync Engine         -->    verify_multi_index.py
  - Target: ES 9.2.3              - Query: upgrade_modified_at     - Target: ES 6.8.21
  - C / U / D operations          - Replay deltas to ES 6.8.21     - Batch _mget (500/req)
  - Output: report.ndjson                                          - Deep body & diff check
```

### Phase 1: Mutation Simulation (`simulate_multi_index.py`)
* Injects randomized, high-volume mutations into ES 9.2.3 using static index configurations in `python/configs/`:
  - **Create (+)**: Inserts new documents with full payload and timestamped `upgrade_modified_at`.
  - **Update (~)**: Performs partial updates on existing records, bumping `upgrade_modified_at`.
  - **Delete (-)**: Deletes existing documents by ID.
* Streams all operations and expected payloads in real time to `report.ndjson`.

### Phase 2: Rollback Execution
* Triggers the delta-sync rollback pipeline.
* Queries ES 9.2.3 for all mutations where `upgrade_modified_at >= $CUTOFF_TIME`.
* Applies corresponding inserts, updates, and deletes to ES 6.8.21.
* Executes index refresh (`POST /_refresh`).

### Phase 3: Reconciliation & Audit (`verify_multi_index.py`)
* Consumes `report.ndjson` and performs batched `_mget` queries (500 IDs per request) against ES 6.8.21.
* Audits each operation:
  - **Created docs**: Must exist in ES 6.8.21; all payload fields must match 1:1.
  - **Updated docs**: Must exist in ES 6.8.21; all mutated fields (including new `upgrade_modified_at`) must reflect new values while preserving untouched fields.
  - **Deleted docs**: Must return `found: false` (HTTP 404).

---

## 4. Script Configurations & Mutation Parameters

The simulation and verification behavior is governed by the following core configuration parameters:

| Parameter | Environment Variable | Default Value | Description |
| :--- | :--- | :--- | :--- |
| **Target ES (Source)** | `ES_URL` / `ES9_URL` | `http://localhost:9200` | Elasticsearch 9.x cluster endpoint during simulation |
| **Target ES (Rollback)**| `ES_URL` / `ES6_URL` | `http://localhost:9200` | Elasticsearch 6.x cluster endpoint during verification |
| **Mutation Fraction** | `MUTATE_PCT` | `0.10` (10%) | Percentage of existing documents to mutate per index |
| **Total Mutations** | `TOTAL_MUTATIONS` | `"auto"` | Overrides `MUTATE_PCT` with a fixed number of operations |
| **Create Ratio** | `CREATE_RATIO` | `0.50` (50%) | Fraction of mutations allocated to new document creates |
| **Update Ratio** | `UPDATE_RATIO` | `0.30` (30%) | Fraction of mutations allocated to partial updates |
| **Delete Ratio** | `DELETE_RATIO` | `0.20` (20%) | Fraction of mutations allocated to document deletions |
| **Bulk Batch Size** | `BATCH` | `500` | Number of operations packed into each `_bulk` HTTP request |
| **Verify Chunk Size** | `BATCH_SIZE` | `500` | Number of document IDs queried per `_mget` verification call |
| **Config Directory** | `CONFIG_DIR` | `python/configs/` | Directory containing per-index JSON schema templates |
| **Report Log File** | `REPORT_FILE` | `report.ndjson` | Immutable NDJSON streaming log of all operations & bodies |
| **Verify Limit** | `VERIFY_LIMIT` | `0` (All) | Max documents to verify per index (`0` audits everything) |

---

## 5. Pass / Fail Criteria

| Metric | Target | Failure Action |
| :--- | :--- | :--- |
| **Data Discrepancies** | **0** (Zero tolerance) | Block rollback release; inspect mismatch logs. |
| **Missing Created Docs** | **0** | Fail build; check delta query timestamp window. |
| **Ghost Deleted Docs** | **0** | Fail build; check deletion sync worker. |
| **Verification Exit Code** | **0** | Exit code 1 halts CI/CD pipeline. |

---

## 6. High-Level Script Architecture & Component Design

The simulation and verification harness is engineered as a decoupled, high-throughput, memory-bounded testing engine capable of generating and auditing millions of mutations without heap exhaustion.

```
+-----------------------------------------------------------------------------------------------------------------------+
|                                         HIGH-LEVEL SYSTEM COMPONENT ARCHITECTURE                                      |
+-----------------------------------------------------------------------------------------------------------------------+
|                                                                                                                       |
|   +---------------------------------------------------------------------------------------------------------------+   |
|   | 1. MUTATION ENGINE (simulate_multi_index.py)                                                                   |   |
|   |                                                                                                               |   |
|   |   [Config Layer]               [Sampling Layer]              [Template & Data Engine]   [Transport Layer]     |   |
|   |   +--------------------+       +---------------------+       +-----------------------+  +-----------------+   |   |
|   |   | Config Loader &    | ----> | Non-Blocking ID     | ----> | Recursive Template    |  | Bulk Packaging  |   |   |
|   |   | Schema Validator   |       | Sampler (_source=0) |       | Engine (Interpolation)|  | Buffer (BATCH)   |   |   |
|   |   +--------------------+       +---------------------+       +-----------------------+  +-----------------+   |   |
|   |             |                             |                              |                       |            |   |
|   |             v                             v                              v                       v            |   |
|   |      python/configs/              Elasticsearch 9.x              upgrade_modified_at    POST /{idx}/_bulk     |   |
|   |        <index>.json                 Cluster                         Timestamp Stamping     500 items/req      |   |
|   |                                                                          |                                    |   |
|   |                                                                          +------------+                       |   |
|   |                                                                                       v                       |   |
|   |                                                                               +-----------------------+       |   |
|   |                                                                               | NDJSON Stream Writer  |       |   |
|   |                                                                               | (report.ndjson)       |       |   |
|   |                                                                               +-----------------------+       |   |
|   +-------------------------------------------------------------------------------------------|-------------------+   |
|                                                                                               | (Immutable Audit Log) |
|   +-------------------------------------------------------------------------------------------v-------------------+   |
|   | 2. RECONCILIATION & AUDIT ENGINE (verify_multi_index.py)                                                          |   |
|   |                                                                                                               |   |
|   |   [Stream Ingestion]           [Batch Dispatcher]            [Comparison Engine]        [Audit & Reporting]   |   |
|   |   +--------------------+       +---------------------+       +-----------------------+  +-----------------+   |   |
|   |   | NDJSON Generator   | ----> | Chunk Aggregator    | ----> | Recursive Deep Field  |  | Results         |   |   |
|   |   | Consumer (O(1) RAM)|       | (500 IDs / Batch)   |       | & Subset Comparator   |  | Aggregator &    |   |   |
|   |   +--------------------+       +---------------------+       +-----------------------+  | Diff Logger     |   |   |
|   |                                           |                              |              +-----------------+   |   |
|   |                                           v                              v                       |            |   |
|   |                                   Elasticsearch 6.x             Field-by-Field Diff      Exit Code: 0 / 1     |   |
|   |                                   POST /{idx}/_mget              Excludes Metadata                            |   |
|   +---------------------------------------------------------------------------------------------------------------+   |
|                                                                                                                       |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

### 6.1 Subsystem 1: Mutation Generation Subsystem (`simulate_multi_index.py`)

The mutation generator operates as an autonomous, multi-phase data producer designed around strict schema validation and bounded memory consumption:

```
[Index Discovery] -> [Count Query] -> [Sample ID Fetch] -> [Quota Partition] -> [Bulk Stream Engine]
```

1. **Configuration Loader & Schema Validator (`load_templates`)**:
   - Scans `python/configs/*.json` at initialization.
   - Enforces a **Zero-Fallback Policy**: Each target index must supply an explicit schema definition containing a mandatory `create` block and an optional `update` block.
   - Eliminates generic default mappings to prevent silent schema corruption.

2. **Non-Blocking ID Sampler & Quota Allocator**:
   - Queries `GET /{index}/_search?size=5000&_source=false` to retrieve active document IDs without pulling doc bodies across the network.
   - Shuffles IDs using a deterministic seed (`SEED = 42 + hash(index)`) to partition IDs cleanly into `Update` and `Delete` candidate sets.
   - Computes dynamic mutation quotas based on active document count ($N$) or explicit user overrides:
     $$\text{Quota}_{\text{Create}} = N \times \text{MUTATE\_PCT} \times \text{CREATE\_RATIO}$$
     $$\text{Quota}_{\text{Delete}} = \min(N, N \times \text{MUTATE\_PCT} \times \text{DELETE\_RATIO})$$
     $$\text{Quota}_{\text{Update}} = (N \times \text{MUTATE\_PCT}) - \text{Quota}_{\text{Create}} - \text{Quota}_{\text{Delete}}$$

3. **Dynamic Template Processor & Timestamp Engine (`render_template`)**:
   - Recursively traverses schema nodes and evaluates dynamic placeholders:
     - `{{id}}` $\rightarrow$ Target document identifier (`doc-1001`).
     - `{{seq}}` $\rightarrow$ Incremental sequence numbers.
     - `{{timestamp}}` $\rightarrow$ ISO 8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`).
     - `{{name}}` $\rightarrow$ Contextual name sequence (`Name <seq>`).
   - Injects `upgrade_modified_at: $NOW_TIMESTAMP` into all Created and Updated payloads as the universal delta-sync marker.

4. **Bulk Packaging Engine & Streaming Writer**:
   - Packs mutations into Elasticsearch bulk protocol lines (`index`, `update`, `delete`).
   - Flushes to Elasticsearch when the buffer reaches `BATCH * 2` lines (500 operations).
   - Simultaneously writes each executed operation to `report.ndjson` with immediate stream flush (`flush()`), ensuring continuous persistence with $O(\text{batch})$ RAM usage.

---

### 6.2 Subsystem 2: Reconciliation & Audit Subsystem (`verify_multi_index.py`)

The verification engine provides a mathematical proof of parity between the ground-truth audit ledger and the rollback target cluster:

```
[NDJSON Stream Parser] -> [Batch Chunk Aggregator] -> [POST _mget (500 IDs)] -> [Deep Comparator] -> [Diff Logger]
```

1. **Generator-Based Stream Consumer (`stream_report_records`)**:
   - Reads `report.ndjson` line-by-line using a Python generator.
   - Avoids reading the full file into memory, enabling verification of multi-gigabyte mutation datasets.

2. **Batched Multi-Get Dispatcher (`es_mget_docs`)**:
   - Groups 500 document IDs per target index and executes a single `POST /{index}/_mget {"ids": [...]}` HTTP request.
   - Automatically degrades to single `GET /{index}/_doc/{id}` only if shard-level partial degradation occurs.

3. **Dual-Mode Deep Comparison Engine**:
   - **Full Body Comparator (`compare_doc_body`)**:
     - Recursively inspects nested dictionaries and lists.
     - Compares scalar values strictly (`actual == expected`).
     - Automatically filters dynamic cluster metadata defined in `IGNORED_FIELDS` (`modified_at`, `updated_at`, `created_at`, `@timestamp`, `_ingest`).
     - Detects precise field-level diffs: value mismatches, missing fields, data type mismatches, and list length differences.
   - **Subset Mutation Verifier (`compare_updated_body`)**:
     - Verifies that all fields specified in the update payload (including `upgrade_modified_at`) match their new values in ES 6.x while verifying that untouched legacy fields remain intact.
   - **Deletion Asserter**:
     - Confirms that purged document IDs return `found: false` or HTTP 404.

4. **Audit Reporting & Process Gatekeeper**:
   - Accumulates check totals (`total_checks`, `passed_checks`, `failed_checks`).
   - Logs specific field paths and mismatched values for every detected failure (limiting to top 3 diffs per document with `(+N more diffs)` to prevent log flooding).
   - Emits process exit code `0` (Success) or `1` (Failure) to govern automated CI/CD and deployment gating.

---

### 6.3 Data Ledger Schema (`report.ndjson`)

Each line in the immutable audit log conforms to the following operational contracts:

* **Create Operation**:
  ```json
  {"index": "orders_v1", "op": "create", "id": "doc-101", "body": {"id": "doc-101", "sku": "SKU-ORD-0101", "price": 49.99, "status": "ACTIVE", "upgrade_modified_at": "2026-09-16T15:30:00Z"}}
  ```
* **Update Operation**:
  ```json
  {"index": "orders_v1", "op": "update", "id": "doc-15", "body": {"status": "UPDATED", "upgrade_modified_at": "2026-09-16T15:30:00Z"}}
  ```
* **Delete Operation**:
  ```json
  {"index": "orders_v1", "op": "delete", "id": "doc-8"}
  ```

---

## 7. Step-by-Step Execution Procedure

```
  [Step 1]                [Step 2]                [Step 3]                [Step 4]
+-------------------+   +-------------------+   +-------------------+   +-------------------+
| Pre-Flight Checks |-->| Mutation Injection|-->| Reverse Delta-Sync|-->| Audit & Reconcile |
| ES 9 & ES 6 Health|   | simulate on ES 9  |   | Replay to ES 6    |   | verify on ES 6    |
+-------------------+   +-------------------+   +-------------------+   +-------------------+
```

### Step 1: Pre-Flight Health & Baseline Validation
1. Verify connectivity and cluster health on both Elasticsearch clusters:
   ```bash
   curl -fsS "$ES9_URL/_cluster/health"
   curl -fsS "$ES6_URL/_cluster/health"
   ```
2. Confirm per-index schema configuration files exist in `python/configs/`.

### Step 2: Mutation Injection on Elasticsearch 9.x
1. Record cutover timestamp: `CUTOFF_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")`.
2. Run mutation simulator:
   ```bash
   python scripts/simulate_multi_index/python/simulate_multi_index.py \
     --es-url "$ES9_URL" \
     --total-mutations 10000 \
     --create-ratio 0.50 \
     --delete-ratio 0.20
   ```
3. Confirm `report.ndjson` is generated and populated with operation records.

### Step 3: Trigger Reverse Delta-Sync Rollback Pipeline
1. Execute the rollback delta-sync worker querying ES 9.x for `upgrade_modified_at >= $CUTOFF_TIME`.
2. Replay all detected inserts, updates, and deletes to ES 6.x indices.
3. Refresh all indices on ES 6.x:
   ```bash
   curl -fsS -XPOST "$ES6_URL/_refresh"
   ```

### Step 4: High-Speed Verification Audit on Elasticsearch 6.x
1. Execute reconciliation script against ES 6.x:
   ```bash
   python scripts/simulate_multi_index/python/verify_multi_index.py \
     --es-url "$ES6_URL" \
     --report "scripts/simulate_multi_index/python/report.ndjson"
   ```
2. Verify exit code equals `0` and audit summary displays `[SUCCESS] ALL CHECKS PASSED!`.

---

## 8. Sample Execution Evidence & Verification Report

Below is a verified production-scale execution log demonstrating successful rollback reconciliation across multiple indices:

### 8.1 Mutation Simulation Log (ES 9.2.3 Source)
```text
==================================================
>> MULTI-INDEX ES MUTATION SIMULATOR (PYTHON CORE)
==================================================
   Start Time     : 2026-09-16 15:53:28 UTC
   ES URL         : http://elasticsearch-9:9200
   Auth User      : elastic
   Config Dir     : python/configs
   Report File    : python/report.ndjson
   Mutate Fraction: 0.10
   C / U / D Ratio: 0.50 / 0.30 / 0.20
--------------------------------------------------
[INFO] Scanning config folder: python/configs
[INFO] Loaded 3 index template(s): bench_v1, orders_v1, products_v1
[INFO] Target Indices (3): bench_v1, orders_v1, products_v1

[1/3] Processing Index: 'bench_v1'
   [STATUS] 'bench_v1' Completed (+ 5,000 created, ~ 3,000 updated, - 2,000 deleted)
[2/3] Processing Index: 'orders_v1'
   [STATUS] 'orders_v1' Completed (+ 5,000 created, ~ 3,000 updated, - 2,000 deleted)
[3/3] Processing Index: 'products_v1'
   [STATUS] 'products_v1' Completed (+ 5,000 created, ~ 3,000 updated, - 2,000 deleted)

==================================================
>> SIMULATION EXECUTION SUMMARY
==================================================
   Start Time       : 2026-09-16 15:53:28 UTC
   End Time         : 2026-09-16 15:53:32 UTC
   Elapsed Time     : 4.12s
   Indices Processed: 3
   Total Created    : + 15,000 docs
   Total Updated    : ~ 9,000 docs
   Total Deleted    : - 6,000 docs
   Total Mutated    : 30,000 docs
   Report Saved     : python/report.ndjson
==================================================
```

### 8.2 Reconciliation Audit Log (ES 6.8.21 Rollback Target)
```text
==================================================
>> MULTI-INDEX ES VERIFICATION AUDIT (PYTHON CORE)
==================================================
   Start Time  : 2026-09-16 15:54:10 UTC
   Target ES   : http://elasticsearch-6:9200
   Auth User   : elastic
   Report File : python/report.ndjson
   Verify Limit: ALL
--------------------------------------------------

[1/3] Verifying Index: 'bench_v1'
   [PASS] 5,000 Created docs exist and bodies match expected templates.
   [PASS] 3,000 Updated docs exist and upgrade_modified_at matches mutation payloads.
   [PASS] 2,000 Deleted docs verified HTTP 404 (Removed).

[2/3] Verifying Index: 'orders_v1'
   [PASS] 5,000 Created docs exist and bodies match expected templates.
   [PASS] 3,000 Updated docs exist and upgrade_modified_at matches mutation payloads.
   [PASS] 2,000 Deleted docs verified HTTP 404 (Removed).

[3/3] Verifying Index: 'products_v1'
   [PASS] 5,000 Created docs exist and bodies match expected templates.
   [PASS] 3,000 Updated docs exist and upgrade_modified_at matches mutation payloads.
   [PASS] 2,000 Deleted docs verified HTTP 404 (Removed).

==================================================
>> VERIFICATION AUDIT EXECUTION SUMMARY
==================================================
   Start Time       : 2026-09-16 15:54:10 UTC
   End Time         : 2026-09-16 15:54:13 UTC
   Elapsed Time     : 2.85s (10,526 docs/sec)
   Indices Audited  : 3
   Total Checks     : 30,000
   Passed Checks    : 30,000
   Failed Checks    : 0
   AUDIT RESULT     : [SUCCESS] ALL CHECKS PASSED!
==================================================
```


