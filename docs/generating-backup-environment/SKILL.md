---
name: generating-backup-environment
description: Use when creating a parallel -backup environment for GKE Helm modules to test alongside major database and search upgrades (Elasticsearch, PostgreSQL, Datastore)
---

# Generating Backup Environment for Helm Modules

## Overview

When performing major version upgrades on core infrastructure (e.g., Elasticsearch 6 to 9, PostgreSQL 13 to 17), a parallel `-backup` testing environment allows safe validation against cloned or legacy data sources without impacting active workloads.

This skill defines the rules, component routing conventions, and Helm rendering procedures required to generate isolated `{env}-backup` environments for specified GKE microservice modules.

---

## Strict Rules & Constraints

> [!IMPORTANT]
> **Single Environment Rule**: Only focus on **one** environment at a time (e.g., `prf` or `stg`). 
> If the user specifies a module without specifying the environment, you **MUST STOP and ask the user** which environment to target. Never assume or process multiple environments in one run.

> [!IMPORTANT]
> **No Unsolicited Assumptions**: If any naming pattern, variable format, or configuration value is ambiguous, ask the user for clarification before applying changes.

---

## Infrastructure & Service Routing Reference

| Component | Strategy in Backup Environment | Connection / Naming Rule |
| :--- | :--- | :--- |
| **GCS (Google Cloud Storage)** | Shared directly | Keep original bucket configs, permissions, and paths unchanged. |
| **Datastore** | Cloned separately | Point to the dedicated cloned Datastore namespace / instance. |
| **Elasticsearch** | Blue-Green routing to legacy ES6 | Route to internal service: `es-backup-service` (points to old ES6 cluster). |
| **PostgreSQL** | Standalone clone from latest backup | Route via `cloudsql-backup-proxy` pointing to new instance starting with `dev02...` or `stg02...`. |
| **Pub/Sub** | Dedicated backup topic / subscription | Transform topic names: `pubsub-topic` $\rightarrow$ `pubsub-backup-service` (or specific backup topic convention). |
| **App Workloads** | Name isolation on GKE | Append `-backup` to workload names (e.g. `app-deployment` $\rightarrow$ `app-backup-deployment`). |
| **App Resources & Configs** | Preserved | Keep `resources` (CPU/RAM limits), `retry`, replicas, and probe settings unchanged. |

---

## Directory Structure

```text
kubernetes/helm/
├── order/                      # Microservice module folder
│   ├── templates/
│   ├── prf/                    # Existing environment configs
│   ├── prf-backup/             # Generated backup environment config
│   ├── stg/
│   └── prd/
├── product/                    # Microservice module folder
│   ├── templates/
│   ├── ...
└── {env}-backup/               # Rendered manifests folder (sibling to module folders)
    ├── order/
    └── product/
```

---

## Value Transformation Patterns

When creating `{module}/{env}-backup` from `{module}/{env}`:

1. **Workload and Deployment Names**:
   - Add `-backup` suffix to deployment, service, ingress, and secret references where applicable.
   - Example: `order-service` $\rightarrow$ `order-backup-service`.

2. **Database & Cache Endpoints**:
   - Elasticsearch hosts $\rightarrow$ `http://es-backup-service:9200`
   - Postgres host / proxy $\rightarrow$ `cloudsql-backup-proxy` (pointing to `dev02*` or `stg02*`)

3. **Pub/Sub Topics**:
   - `pubsub-topic` $\rightarrow$ `pubsub-backup-service`

4. **Temporary Variable Substitutions**:
   - `XXX` $\rightarrow$ `X111`
   - `YYY` $\rightarrow$ `YYY1`
   *(Keep customizable for user adjustment)*

5. **Untouched Sections**:
   - GCS bucket names and credentials.
   - Resource limits (`requests`, `limits`).
   - Probe, retry, and timeout parameters.

---

## Continuous Learning & Skill Self-Update Protocol

To ensure consistency across multiple module migrations, this skill **must continuously learn and persist confirmed patterns** directly back into this file.

### 1. Triggers for Self-Updating

| Trigger Event | Action | Target Section in `SKILL.md` |
| :--- | :--- | :--- |
| **Variable Finalization** | User confirms real variable names replacing placeholder `XXX`/`YYY` | Update `Value Transformation Patterns` $\rightarrow$ Item 4 |
| **New Service / Infrastructure Pattern** | User clarifies or introduces a new component (e.g., Redis, Kafka, specific Datastore kind) | Update `Infrastructure & Service Routing Reference` table |
| **Module-Specific Exceptions** | User establishes an exception (e.g., specific pod does not need Pub/Sub backup) | Append to `Strict Rules & Constraints` or create a Module Overrides table |
| **Feedback / Correction** | User corrects a generated manifest or naming mistake | Add the failure pattern & fix to `Common Mistakes & Red Flags` |

### 2. Update Execution Rule
Whenever one of the triggers occurs during a session:
1. Immediately invoke `replace_file_content` on this `SKILL.md` file.
2. Confirm the exact change made with a clear reference note.
3. Explicitly inform the user: *"Đã cập nhật quy tắc mới vào skill `generating-backup-environment` tại [SKILL.md](file:///d:/Workspace/es-migrate/.agent/skills/generating-backup-environment/SKILL.md) để áp dụng cho các lần chạy tiếp theo."*

---

## Step-by-Step Execution Workflow

```
1. Identify Target Module & Env
   ├── Target module specified? (e.g., order, product)
   └── Target env specified? (prf, stg, prd)
       └── If NO -> Ask user to choose single target env.

2. Create Module Backup Value Config
   ├── Copy {module}/{env} -> {module}/{env}-backup
   └── Apply transformation rules:
       ├── Append -backup to app/service names
       ├── Point ES to es-backup-service
       ├── Point PG to cloudsql-backup-proxy (dev02/stg02)
       ├── Update Pub/Sub topics to backup pattern
       ├── Apply variable mappings (XXX->X111, YYY->YYY1 or confirmed mappings)
       └── Keep GCS & resource configs intact

3. Render Manifests via Helm Template
   ├── Run helm template targeting {module}/{env}-backup
   └── Output rendered YAMLs into {env}-backup/{module}/ (sibling to module folders)

4. Verify & Report
   ├── Inspect output manifests for naming collisions or unmapped URLs
   └── Report generated files and verify readiness

5. Feedback Loop & Skill Self-Update (MANDATORY)
   ├── Check if user confirmed new variables, naming rules, or corrections
   └── If YES -> Persist updates directly into SKILL.md for future runs
```

### Helm Template Command Pattern

Run the template command to output manifests into the `{env}-backup` directory sibling to the module folders:

```bash
helm template <release-name>-backup kubernetes/helm/<module> \
  -f kubernetes/helm/<module>/<env>-backup/values.yaml \
  --output-dir kubernetes/helm/<env>-backup
```

---

## Common Mistakes & Red Flags

| Red Flag / Mistake | Correction |
| :--- | :--- |
| Processing multiple environments at once | **STOP**. Pick only one target environment per invocation. Ask if unspecified. |
| Altering GCS bucket names or configs | Leave all GCS references identical to the original environment. |
| Modifying CPU/RAM or retry limits | Retain identical resource and retry specs to mirror production conditions. |
| Pointing PostgreSQL to existing PG13 | Ensure connection is routed through `cloudsql-backup-proxy` targeting `dev02...` or `stg02...`. |
| Outputting rendered YAMLs into the module folder | Helm template output must go to `{env}-backup/` at the root Helm directory, sibling to `order/`, `product/`, etc. |
| Forgetting to sync confirmed rules to `SKILL.md` | When user confirms a new rule or fixes a variable, immediately update this skill file. |

