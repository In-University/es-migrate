# Summary template - `W/career-summary.md`

High level. A reader who has never seen the company should understand the **shape** of the work. The user reads and rewrites the file afterwards, so write clear drafts, not polished prose.

## Style

- **Describe by what it is.** "Internal data-migration platform for a search cluster", "CI/CD pipelines for a microservice estate". Leave out repo, client, product, ticket, page and host names, URLs and people.
- **Public tech names are welcome** (Terraform, Kubernetes, Elasticsearch, Jenkins, Go, PostgreSQL).
- **Round numbers.** `~20k` lines, `300+` commits, `40+` pages. Source every number from `digest.md` or the user.
- **Business impact the data cannot show is a question in section 8**, not a claim.
- **Paraphrase raw material** (commit subjects, issue titles, page titles) to the concept.

## Sections

```markdown
# Career summary - <role/area> (<period, e.g. 2025-08 → 2026-11, 15 months>)

## 1. Snapshot
3-5 lines: domain, kind of systems, the user's scope (individual contributor / owner / lead), team size band, period.

## 2. Work areas
One block per area (3-9 areas), most significant first:
### A. <generic name>
- **What / Why**: ...           - **Tech**: ...        - **Role**: owner / main author (~X% of the area) / contributor
- **Scale card** (every row carries a provenance tag, see scale-dimensions.md; drop rows with nothing to say, keep rows marked ask):

  | Dimension | Value | Basis |
  |---|---|---|
  | Code | ~4.5k lines added (Shell/Python), ~3k now, 13 files, 13 commits over 3 months | measured |
  | Data volume | 8M-document benchmark index; example delta ~400k docs | design / example |
  | Data shape | ~50 fields incl. nested objects, 3 shards | measured |
  | Workload | ... | run-log |
  | Infrastructure | ... | measured |
  | Delivery / Quality / Integration / Docs / Security / Reliability | ... | ... |
- **Outcome**: only what is evidenced or user-confirmed; otherwise "see Open questions"

## 3. Skills and technologies
Grouped: languages (by lines added), infrastructure/IaC, data/search, CI/CD, observability, testing.

## 4. Scale metrics (whole period, plus one comparison table: rows = work areas, columns = commits, lines added, lines now, data volume, infra size)
| Metric | Value | Basis |
|---|---|---|
Commits · active months · repos contributed to · code lines added (excluding generated/bulk imports) ·
share of current codebase still authored by me · tickets resolved · story points · docs/runbooks written ·
test-to-code ratio · environments/pipelines/clusters operated · PRs/MRs merged and reviewed (if collected)

## 5. Ownership and collaboration
Share of commits vs team, reviews done, documentation habits, cross-team work, on-call, mentoring, as far as evidenced.

## 6. Timeline
By quarter (a 15-month window is ~5 quarters), 1-2 lines each: the focus and the main kind of delivery.

## 7. CV highlights
(see cv-highlights.md) - 2 headline lines, 5-8 bullets in English, one skills line, then:

### 7.1 Work Experience entry (paste-ready)
A small block written exactly as an entry under "Work Experience" in a real CV (format and rules in cv-highlights.md): title line, one scope sentence, 4-6 bullets picked from the pool above, one tech line. Placeholders `<Company>`, `<Job title>`, `<City>` stay in angle brackets for the user to fill; dates come from the scan window.

## 8. Open questions (only the user can answer)
Numbered; each names the metric, where to find it, and which bullet it would upgrade
("Downtime during the cutover: ~? minutes, from the change ticket/post-mortem → upgrades bullet 2").

## 9. Data notes
- Excluded from line totals: N bulk commits (imports/archives/reformat)
- Not collected: <sources that failed or were skipped>
- Identity used: <how many git identities, which sources>
```

Language: the body in Vietnamese; section 7 bullets in English unless the user said otherwise.
