# Blue-green rollback: ES9 → ES6 delta sync — design

## Problem

The migration workflow is one-directional: `reindex_remote.sh` moves data
ES6 → ES9 once, then (in a real blue-green cutover) traffic would move to
ES9. If ES9 needs to be rolled back after traffic has already moved, ES6 is
stale — it's missing every document created or updated on ES9 since cutover.
There is currently no mechanism to bring ES6 back up to date before flipping
traffic back to it.

## Goal

Given a decision to roll back, bring ES6 up to date with everything that
changed on ES9 since the migration cutover, using infrastructure that only
exists for the duration of the rollback (not a standing service).

## Design

### Sync model: one-shot, idempotent, on-demand

This is **not** continuous replication. ES6 stops receiving writes at
cutover; if rollback is later decided, a single delta-catch-up run pulls
everything changed on ES9 since cutover back into ES6, then traffic flips
back. The sync is idempotent (upsert by document `id`), so a re-run after a
failure or interruption is always safe — it just re-writes the same
documents.

### Cutover marker: `_meta.cutover_at` on the ES9 index

`scripts/reindex_remote.sh` gains one more step after the existing
count-verification: a `PUT bench-es9/_mapping` setting
`_meta.cutover_at = <ISO-8601 timestamp of reindex completion>`. This is
index-level metadata, not a document field — it doesn't affect document
mappings or search.

The rollback job reads this value automatically (a `GET bench-es9/_mapping`
before building the Logstash query) instead of requiring an operator to
remember or manually supply the cutover timestamp. Manual override remains
possible by setting the Helm value directly, but is not the default path.

### Delete detection: ID-diff reconciliation, not a soft-delete field

Delta-by-`updated_at` only sees creates and updates — a hard `DELETE` on ES9
leaves no trace for the sync to find, so a deleted document would silently
remain in ES6 after rollback.

An earlier version of this design closed that gap with an application-level
soft-delete flag (`is_deleted` + `deleted_at`, bumping `updated_at` on
delete instead of hard-deleting) so the existing delta-by-`updated_at`
mechanism would carry the tombstone across like any other update. That
requires the application (and reindex path) to actually adopt soft deletes,
which isn't always an option — the mapping may be effectively frozen, or the
write path may be owned by a team/system that won't take on a new field.
**Given that constraint, this design does not depend on any mapping or
application change at all.**

Instead, deletes are handled by **reconciliation**: after the delta sync
carries across every create/update, a separate pass exports every live
`_id` from both indices (via `search_after`, sorted, so it streams rather
than holding the full set in memory), diffs the two sorted lists, and
bulk-deletes from ES6 whatever no longer exists on ES9. This is the same
technique Elastic's own docs recommend for `jdbc` inputs that can't observe
deletes either — a known, common workaround wherever a sync mechanism only
has a "what changed" signal (`updated_at`) and no "what disappeared" signal.
It costs a full scan of both indices' IDs (cheap — IDs only, no
`_source`), which is acceptable because this only runs once per rollback,
not continuously.

Implemented as `scripts/reconcile_deletes.sh`, run manually after the
Logstash pipeline (below) has drained. It doesn't run inside the rollback
K8s cluster — there's no reason to: it's a one-shot script hitting both
clusters' HTTP APIs directly, and keeping it off the cluster keeps the
Logstash/Helm machinery scoped to what it's actually needed for (streaming
per-document transformation), not set-difference logic that doesn't fit
Logstash's model well.

### Ephemeral K8s + Logstash: `terraform/rollback/`

A third, independent Terraform root (own state,
`terraform/rollback/terraform.tfstate`), applied only when a rollback is
in flight and destroyed immediately after:

- Provisions a **GKE Standard** cluster with a single, manually-sized small
  node (`e2-small`) — not Autopilot. Autopilot was tried first and rejected
  by GCP outright: it mandates a *regional* cluster, and a regional
  cluster's system-workload HA baseline alone needs ~8 vCPU of
  `CPUS_ALL_REGIONS` quota, which the 2 running benchmark VMs
  (`e2-standard-4` × 2 = 8 vCPU) already leave no room for within a default
  12-vCPU project quota — and the ES VMs can't be shut down to make room,
  since Logstash needs both reachable during the sync. A single small
  Standard node fits the remaining headroom; the tradeoff is owning node
  sizing/lifecycle ourselves instead of Autopilot doing it, which is a
  reasonable cost for a cluster that only ever runs one Logstash pod.
- Attaches to the *same* VPC/subnet as `terraform/network/` (read via
  `terraform_remote_state` on the network module's state — see
  [[2026-07-21-network-ip-isolation-design]]), so Logstash reaches ES6 and
  ES9 over their **internal** IPs rather than needing public endpoints.
- Owns its own firewall rule scoped to just the GKE pod CIDR (not an
  extension of the main root's `es-allow-internal`), so pods can reach both
  ES VMs on tcp 9200 without opening anything to the internet, and the rule
  exists exactly as long as the rollback cluster does — no coupling to
  whether `rollback/` has ever been applied from the main root's config.

A Helm release of the official `elastic/logstash` chart runs a single
pipeline:

- **input** (`elasticsearch` plugin, against ES9 `bench-es9`): range query
  `updated_at > <cutover_at>` (the value fetched per above), no `schedule` —
  the plugin scrolls through all matches once and the pipeline ends when
  exhausted. This is what makes the run one-shot rather than continuous.
- **output** (`elasticsearch` plugin, against ES6 `bench-es6`):
  `doc_as_upsert => true`, `document_id` taken from the source document's
  `_id`, so re-running the same window is harmless.

**Runbook**: apply `rollback/` → install the Helm release → watch it reach
completion (pipeline exits, pod stops processing) → run
`scripts/reconcile_deletes.sh` for the delete pass → verify `bench-es6`'s
document count matches ES9's → flip traffic to ES6 → `helm uninstall` the
release → `terraform destroy` in `rollback/`. Nothing about this cluster
persists between rollback events; each one provisions fresh.

### Representing ES6 vs ES9 mapping differences: `docs/MAPPING-DIFFERENCES.md`

A hand-maintained markdown doc (not a script) listing the known structural
differences between the two clusters' index definitions, so anyone touching
either mapping file understands what's version-specific vs. incidental:

- ES6's `_doc` mapping-type wrapper (`mappings._doc.properties`) vs ES9's
  typeless mapping (`mappings.properties`) — mapping types were removed in
  ES7+; this is why the two JSON files have different nesting even though
  the field list is identical.
- Both clusters rely on the default date format
  (`strict_date_optional_time||epoch_millis`) for `created_at`/`updated_at`/
  `published_at`. Called out explicitly because ES6 parses dates via
  Joda-Time and ES7+ via `java.time` — the default format is compatible
  across both, but a custom format string would not necessarily behave
  identically, so this doc is the place to check before anyone adds one.
- No document fields were added for this feature — the rollback path (both
  the create/update delta and the delete reconciliation) works entirely off
  the existing `updated_at` field and `_id`, deliberately, per the
  soft-delete-rejected reasoning above. The only addition is
  `_meta.cutover_at`, which exists only as ES9 index metadata (never a
  document field, never written to ES6).

## Out of scope

- Continuous/scheduled replication ES9 → ES6 (explicitly a one-shot,
  on-demand design).
- A soft-delete flag / any mapping change — explicitly rejected; see
  "Delete detection" above.
- A programmatic mapping-diff tool — documentation only, per decision.
