---
name: career-retrospective
description: Use when the user is leaving a job or updating their CV and wants an inventory of everything they did across git repos, Jira, Confluence and project folders, ending in one high-level summary file with a CV-highlights section. Triggers - "nghỉ việc", "viết CV", "tổng hợp những gì đã làm", "scan git/Jira/Confluence", quitting, resignation, performance review evidence, brag document, project scale for resume.
---

# Career Retrospective

## Overview

Reconstruct what **one person** did and **how big it was** from git history, project folders, Jira and Confluence, then write **one high-level summary file** with a CV-highlights section.

**You are the investigator.** Pick the route that fits what you find (`references/playbook.md`); the scripts in `scripts/` are optional accelerators (`references/tools.md`). Every fact can be obtained with plain `git`, `grep`, `jq`, `gh`, `curl` and by reading files; when a script fails or does not fit, do it by hand and continue. Loop back to any step when new evidence changes the picture.

**Two tiers of data:**

| Tier | Where | Content | Audience |
|---|---|---|---|
| **Raw** | `W/raw/` | commit subjects, repo/ticket/page names, URLs, script output | you, to *understand* the work |
| **Summary** | `W/career-summary.md` | work areas with scale cards, tech, CV bullets, at a high level | the user, who reviews and edits it |

Raw is for reading, not quoting: the summary describes the *shape* of the work and leaves out internal names, ticket keys, URLs and hostnames.

`W` = output folder: `<repo>/career-output/` in a project install, else `~/career-retrospective/<YYYY-MM-DD>/`. Raw holds internal details, so when `W` is inside a git repo add it to `.git/info/exclude` (local, touches no tracked file).

## The investigation loop

Each step has a goal, routes in the playbook (section numbers), and an exit check. Do them in order the first time; revisit freely.

### 1. Frame

**Goal:** know what exists and what the user wants. Ask once (AskUserQuestion, at most 2 questions): which folders hold work code (several allowed), and which sources are reachable (Jira/Confluence tokens, git host for PRs). The time window is the **last 15 months** (this user's tenure) unless they say otherwise; defaults (summary in Vietnamese, CV bullets in English) are mentioned at the end, not asked. Create `W/raw`.
**Routes:** playbook 1 (what can I reach?), 3 (window and terrain).
**Exit:** you know which repos/folders/sources you will use and which are unreachable.

### 2. Establish identity

**Goal:** the set of git identities that are the user. Never guess; show candidates and let the user choose; bots are not the user.
**Routes:** playbook 2. Accelerator: `scan_git.py discover` + `identity`.
**Exit:** the user confirmed the identities; third-party clones with other people's commits are recognised.

### 3. Map the terrain

**Goal:** a first picture: repos, size, activity by month, directories, what is imported or generated (it distorts every number), what the user's commits are about.
**Routes:** playbook 3, 4, 6 (pitfalls). Accelerators: `scan_git.py scan`, `scan_folder.py`, `scan_atlassian.py`, `digest.py`.
**Exit:** you can describe each repo in two sentences; bulk/imported islands are listed and shown to the user; failed or missing sources are noted.

### 4. Form work areas

**Goal:** 3-9 areas, each something a CV bullet could be about. Write each as a set of path globs (plus Jira epics / doc spaces if available).
**Routes:** playbook 5. Accelerator: `area_scale.py` (needs the globs in `raw/areas.json`).
**Exit:** little or no meaningful work left unassigned.

### 5. Measure each area (Scale card)

**Goal:** per area, every scale dimension you can evidence, each with a provenance tag. Walk the catalog in `references/scale-dimensions.md` (code, data volume and shape, workload, infrastructure, delivery, quality, integration, docs, security, process, reliability). Do not stop at lines of code and record counts.
**Routes:** playbook 6 (contribution), 7 (hunt for numbers; open the context of each and tag `measured | run-log | design | example | config | ask`), 8 (work that leaves little trace in git). Accelerators: `area_scale.py`, `scale_hunt.py`.
**Exit:** every area has a card; no `design`/`example` number is passed off as production; impact items are `ask`.

### 6. Verify and close gaps

**Goal:** make the numbers trustworthy and list what only the user knows.
**Routes:** playbook 9 (plausibility checks), 10 (when to ask). Recompute any suspicious number by a second route.
**Exit:** every number in your notes passes a check or is flagged; Open questions are specific (metric, where to find it, which bullet it upgrades).

### 7. Write `W/career-summary.md`

**Goal:** high-level, scannable, honest. Follow `references/summary-template.md` (sections, Scale card layout, style) and `references/cv-highlights.md` (bullet formula, credible numbers, evidence-to-bullet ideas). CV bullets include numbers where evidenced, **including lines of code** as scale context, never as the headline.
**Exit:** every number traces to a measurement or to the user; internal names are generalized; provenance is visible in the wording.

### 8. Hand off

Tell the user: where the summary is; what was excluded (bulk imports, unreachable sources); the Open questions only they can answer; that `raw/` holds internal details and is theirs to keep or delete. Everything stays local: no Artifact, no upload.

## Accelerators (optional)

`scripts/` has helpers for identity discovery, git scanning with bulk-commit detection, folder scale, per-area scale, number hunting and Jira/Confluence pulls. Read `references/tools.md` for what each saves you, when to skip it and how to read its output critically. Prefer a one-line manual probe over a script when you need only one number.

## Hard rules

1. Every number in the summary traces to a measurement or to something the user said. Nothing invented; an estimate carries an explicit "(estimate)".
2. High level: describe work by what it is ("internal data-migration platform"), not by repo, client, ticket or page names; no URLs or hostnames. Round numbers (`~20k`, `300+`).
3. Read-only on company systems. No write calls; after a 401/403 do not try other credentials; tokens never go on a command line, into chat or into output.
4. The user confirms identity (step 2) and sees the bulk/imported list (step 3) before anything is written.
5. `design` and `example` figures are never presented as production results.

## Common mistakes

| Mistake | Fix |
|---|---|
| Treating a tool's output as truth | check it against a second route (playbook 9) |
| Stopping when a script fails | take the manual route from the playbook |
| Treating every commit in a folder as the user's | confirm identities; third-party clones exist |
| Headline "wrote 500k lines" | LOC beside a capability; split by category; exclude imports |
| Quoting "codebase of N lines" without checking who wrote it | size today includes imports and teammates; compare with lines the user added |
| Copying a repo or epic name "because it sounds good" | describe what it is |
| Estimating impact ("reduced cost 30%") | Open question for the user, with the exact metric to look up |
| Scanning a shallow or single-branch clone | playbook 1: unshallow / fetch, or report partial history |
| Mixing earlier employers or hobby repos | the 15-month window; ask which roots belong to this job |
