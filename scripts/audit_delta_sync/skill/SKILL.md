---
name: es-delta-sync-audit
description: |
  Autonomous Elasticsearch Delta Sync Auditor generator for Golang Echo microservices.
  Scans delivery/*_handler.go files, extracts Echo routes and Go struct tags,
  constructs modular JSON audit configurations, runs audit_delta_sync.py, auto-fixes schema errors,
  and outputs a Markdown executive report.
  Use when asked to 'audit delta sync', 'audit echo handlers', or passed a directory path like 'delivery/'.
version: 1.0.0
---

# Golang Echo Elasticsearch Delta Sync Audit Skill

## Overview

This skill provides an autonomous pipeline for auditing Elasticsearch Delta Sync integrity in Golang microservices built with the **Echo** framework. Given a directory path containing Echo HTTP handler files (e.g., `delivery/` or `delivery/http/`), the agent will:

1. Scan all `*_handler.go` files in the target directory.
2. Extract registered Echo HTTP routes (`e.POST`, `g.PUT`, `g.PATCH`, `g.DELETE`) and associated request Go structs (`json:"..."` tags).
3. Create a Markdown TODO breakdown checklist listing all discovered resources.
4. Construct modular JSON audit configurations in `./configs/<domain>/<resource>.json`.
5. Run `audit_delta_sync.py` to validate Delta Sync integrity against Elasticsearch.
6. Self-heal and auto-fix configuration/payload schema mismatches if errors occur.
7. Generate a final Markdown executive summary report.

---

## Skill Directory Structure

```text
skills/es-delta-sync-audit/
├── SKILL.md                          # Main execution instructions
├── references/
│   ├── config_schema.md              # Detailed JSON schema specification for audit_delta_sync.py
│   └── echo_parsing_guide.md         # Guide on parsing Echo router definitions and Go struct tags
└── examples/
    └── sample_config.json            # Reference audit configuration file
```

---

## Step-by-Step Execution Workflow

```
[Step 1: Scan delivery/*_handler.go] -> [Step 2: Markdown Task Checklist]
                                                    |
[Step 5: Final Executive Report] <- [Step 4: Execute & Auto-Fix] <- [Step 3: Generate JSON Configs]
```

---

### Step 1: Scan Echo Handler Files
1. Resolve the user-specified directory path (e.g. `delivery/`, `delivery/http/`, `internal/delivery/`).
2. Search recursively for all Go source files matching the pattern `*_handler.go`.
3. Parse Echo route registrations and map path parameter syntax:
   - Convert Echo `:id` parameters to `{id}` (e.g., `/api/v1/invoices/:id` -> `/api/v1/invoices/{id}`).
4. Trace request body binding (`c.Bind(&req)`) and inspect corresponding Go struct definitions.
5. Extract field names from `json:"..."` struct tags and identify primary key fields (`invoice_id`, `id`, `user_id`, etc.) for `id_field`.

*For detailed Echo parsing rules and Go struct tag extraction examples, see `references/echo_parsing_guide.md`.*

---

### Step 2: Markdown Task Breakdown Checklist
Create a clear Markdown TODO task list outlining the configuration files to be generated, grouped by service domain:

```markdown
## Configuration Generation Checklist

### Domain: Billing
- [ ] `configs/billing/invoices.json` - Base Path: `/api/v1/billing/invoices` (POST, PUT, PATCH, DELETE)
- [ ] `configs/billing/payments.json` - Base Path: `/api/v1/billing/payments` (POST, PUT, DELETE)

### Domain: User Management
- [ ] `configs/user/accounts.json` - Base Path: `/api/v1/users` (POST, PUT, PATCH, DELETE)
```

---

### Step 3: Generate Modular JSON Config Files
Generate individual JSON audit configuration files under `./configs/<domain>/<resource>.json`.

Each file must contain a JSON array of resource definitions. See `references/config_schema.md` for full schema specifications or `examples/sample_config.json` for a complete reference payload.

Standard Structure:
```json
[
  {
    "base_path": "/api/v1/billing/invoices",
    "es_index": "billing_invoices",
    "id_field": "invoice_id",
    "steps": [
      {
        "name": "CREATE",
        "method": "POST",
        "path": "/api/v1/billing/invoices",
        "payload": {
          "invoice_id": "INV-2026-001",
          "amount": 150.0,
          "status": "ACTIVE"
        },
        "es_check": {
          "status": "ACTIVE",
          "amount": 150.0
        }
      },
      {
        "name": "UPDATE",
        "method": "PUT",
        "path": "/api/v1/billing/invoices/{id}",
        "payload": {
          "amount": 300.0,
          "status": "ACTIVE"
        },
        "es_check": {
          "amount": 300.0
        }
      },
      {
        "name": "PATCH",
        "method": "PATCH",
        "path": "/api/v1/billing/invoices/{id}",
        "payload": {
          "status": "INACTIVE"
        },
        "es_check": {
          "status": "INACTIVE"
        }
      },
      {
        "name": "DELETE",
        "method": "DELETE",
        "path": "/api/v1/billing/invoices/{id}"
      }
    ]
  }
]
```

---

### Step 4: Execute Auditor & Self-Healing Loop
1. Run the audit script against target environment:
   ```bash
   python audit_delta_sync.py \
     --config ./configs
   ```

2. **Self-Healing (Auto-Fixing)**:
   - If the script returns HTTP 404, bad payload schema errors, or missing `id_field` errors:
     - Read script error output.
     - Correct the JSON files in `./configs/`.
     - Re-run `audit_delta_sync.py`.
   - If the script reports Elasticsearch Delta Sync failures (e.g. `t_PATCH <= t_UPDATE` monotonicity failure or missing `modified_at`):
     - Record as valid backend synchronization defect.

---

### Step 5: Final Executive Audit Report
Output a Markdown report summarizing the audit results:

```markdown
# Elasticsearch Delta Sync Audit Report

## Audit Scope & Target
- Target Handler Directory: `<SPECIFIED_DIR>`
- Scanned Handler Files: `<FILE_COUNT>` (*_handler.go)
- Backend REST API URL: `<TARGET_URL>`
- Elasticsearch Cluster: `<ES_URL>`

## Inventory & Domain Breakdown
| Service Domain | Base Path | Handler File | Primary Key (`id_field`) | Config File Path |
| :--- | :--- | :--- | :--- | :--- |
| Billing | /api/v1/billing/invoices | delivery/http/invoice_handler.go | invoice_id | configs/billing/invoices.json |

## Audit Execution Results
- Total APIs Audited: `<TOTAL>`
- Passed Delta Sync: `<PASSED>` (`<PASSED_PERCENTAGE>`%)
- Failed Delta Sync: `<FAILED>` (`<FAILED_PERCENTAGE>`%)
- Execution Duration: `<DURATION>`s

## Detected Failures
| Base Path | ES Index | Failed Step | Error Detail | Teardown Status |
| :--- | :--- | :--- | :--- | :--- |
| /api/v1/billing/invoices | billing_invoices | PATCH | ES timestamp older than request call time | Cleaned Up |

## Teardown Rollback Status
All generated test entities were cleaned up via Teardown DELETE calls.
```

---

## Guidelines for Claude Haiku
1. Focus scanning strictly on files matching `*_handler.go` inside the user-specified directory.
2. Read `references/echo_parsing_guide.md` if struct tag or router parsing logic needs clarification.
3. Consult `references/config_schema.md` for exact JSON schema rules.
4. Avoid using decorative emojis in generated files, logs, or reports.
