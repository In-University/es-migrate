---
name: editing-confluence-runbooks
description: Use when creating, editing, or reviewing a Confluence page or operational runbook (terraform apply, Jenkins job, Kubernetes rollout, migration steps), or when the user pastes a Confluence / atlassian.net page link and wants its content changed.
---

# Editing Confluence Runbooks

## Overview

Edit Confluence pages through REST API **v1** using **storage format** (XHTML + `ac:` macros). Primary target: self-hosted **Data Center/Server**; a pasted `*.atlassian.net` link works too (testing).

`python scripts/confluence.py` (run `-h`) only talks to the API and checks XML syntax. **All content rules below are yours to check** — the script does not know them.

## Setup

The script reads `<skill dir>/.env` automatically (git-ignored; template: `.env.example`). Real env vars override it; `CONFLUENCE_ENV_FILE=<path>` points to another file.

| Target | Keys | Auth |
|---|---|---|
| Data Center | `CONFLUENCE_BASE_URL` (with context path, e.g. `https://wiki.corp/confluence`), `CONFLUENCE_TOKEN` (PAT) | Bearer (DC ≥ 7.9) |
| Cloud | `CONFLUENCE_BASE_URL=https://<site>.atlassian.net/wiki`, `CONFLUENCE_EMAIL`, `CONFLUENCE_TOKEN` (API token) | Basic |

Start every session with `python scripts/confluence.py whoami` (shows the loaded file, masked token, and tests auth). Missing values → **stop** and ask the user to fill `.env` themselves. Never read `.env` aloud, write tokens into files or page content, or pass them inline in a command.

Keep working files in a temp/scratch dir **outside the repo** (`$WORK`).

## Workflow

1. `get <link> --out $WORK/page.xml` → body + `page.meta.json` (title, version, status). No page id in the link → ask.
2. Copy to `$WORK/page.new.xml` and edit only what the user asked for (keep server attrs like `ac:macro-id` on untouched parts).
3. **Self-review** against the checklist below; fix until every item passes.
4. `check $WORK/page.new.xml` → `syntax: OK`.
5. `diff $WORK/page.xml $WORK/page.new.xml` → show the user, **wait for explicit approval**.
6. `put <link> $WORK/page.new.xml --expect-version <N> --message "<why>" --confirm` (draft without title: add `--title`).
7. `get` again to confirm. Rollback = *Page History → Restore*.

Version mismatch / HTTP 409 → re-`get`, re-apply, back to 3. HTTP 401/403 → report, never try other credentials. Cloud 404/410 on v1 → report; do not switch to v2.

## House Rules

1. **Links only from `references/whitelist.md`.** Every `href`, `ri:url`, and URL inside commands must start with a whitelisted prefix (loopback/in-cluster addresses in commands are fine). Missing or `TODO` entry → **ask**; never invent URLs, job names, clusters, namespaces.
2. **Every step covers STG and PRD.** Prefer one collapsible `expand` per environment (title starts with `STG` / `PRD`); plain `<h3>` sections are acceptable for very short content.
3. **STG and PRD are written independently.** Don't copy STG and swap the env name. PRD typically adds: change-ticket/window check, announcement, backup/snapshot, staged rollout with health check between, second reviewer, alert silence + restore.
4. **Concrete sub-steps.** Numbered `<ol>`; each item is one action with the exact link, parameter table, or command in a `code` macro.
5. **Verify after each step, per environment.** `<h4>Verify</h4>` + table *Check / Expected / If it fails*.
6. **Use a pattern when one exists** (`patterns/`, e.g. terraform apply → `patterns/terraform-apply.md`). Recurring step type with no pattern → ask whether to create one.
7. **Nothing unfilled.** No `TODO` or `{{SLOT}}` left; missing info → ask.

### Step skeleton (preferred form)

```xml
<h2>Step 3: Scale Elasticsearch StatefulSet</h2>
<p>One-line purpose.</p>
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">STG – 2 steps</ac:parameter>
  <ac:rich-text-body>
    <ol><li><p>Action…</p><!-- code macro / link / table --></li></ol>
    <h4>Verify</h4>
    <table><tbody><tr><th>Check</th><th>Expected</th><th>If it fails</th></tr>
      <tr><td>…</td><td>…</td><td>…</td></tr></tbody></table>
  </ac:rich-text-body>
</ac:structured-macro>
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">PRD – 5 steps</ac:parameter>
  <ac:rich-text-body><!-- PRD's own sub-steps + Verify --></ac:rich-text-body>
</ac:structured-macro>
```

## Self-review checklist (before step 4)

- [ ] Every URL matches a whitelist prefix
- [ ] Every step has STG and PRD content; PRD has its own sub-steps, not a renamed copy
- [ ] Every sub-step is one concrete action (command / link / parameter table)
- [ ] Every env of every step ends with a Verify table
- [ ] Pattern used where applicable
- [ ] No `TODO`, `{{…}}`, invented names
- [ ] Only requested sections changed
- [ ] Macro names/params match `references/macros.md` (or copied from the instance)

## References

- `references/macros.md` — storage-format tags and ~60 macros with parameters and version notes.
- `references/whitelist.md` — allowed link prefixes.
- `patterns/` — step patterns.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Cloud/ADF docs used for DC | Storage format; `references/macros.md` |
| `color` on status | `colour` |
| Code without CDATA | `<ac:plain-text-body><![CDATA[…]]></ac:plain-text-body>` |
| Guessing `jira` `serverId` | Copy from an existing page on the instance |
| PUT before approval | Diff → explicit "yes" → `--confirm` |
