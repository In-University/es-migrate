# CV highlights - how to turn evidence into bullets

## Bullet formula

**Action verb + what (generic) + how (tech) + measurable scope/result.**

> Built an automated, rollback-capable migration toolchain (Bash, Python, Terraform) for upgrading a multi-node search cluster across 4 major versions, ~20k lines of code, 30+ runbooks.

- 5-8 bullets, one line to two lines each, strongest first. Past tense, owner verbs (designed, built, automated, led, migrated, reduced), not "responsible for" or "helped with".
- Each bullet needs at least one number from the digest or the user. No number available → prefer a concrete capability over adjectives ("zero-downtime", "automated" only when evidenced).
- **Lines of code**: allowed as scale context ("~20k lines of Terraform/Shell"), never the headline, always the net of bulk/generated commits (the digest already excludes them). Pair with a capability. Prefer "main author of ~60% of a ~30k-line codebase" (blame share) over "wrote 100k lines".

## Work Experience entry (the paste-ready block, section 7.1 of the summary)

The pool of highlights is long; a CV entry is short. Distil it into the block a recruiter actually reads under **Work Experience**, in English unless the user says otherwise:

```
<Job title> | <Company> | <City, Country>                                  <Mon YYYY> - <Mon YYYY>
<One sentence: domain + kind of system + the user's scope, e.g. "Owned the tooling and infrastructure for upgrading large search clusters from Elasticsearch 6 to 9 on GCP.">
- <Bullet 1: strongest, ownership + scale>
- <Bullet 2 ...>
- ... (4-6 bullets)
Tech: <8-12 technologies, most relevant first>
```

Rules:
- **Header**: placeholders `<Job title>`, `<Company>`, `<City, Country>` are left for the user (never invent a title or employer); dates = start of the scan window or first commit to the last day worked, `Mon YYYY` format.
- **Scope sentence**: one line, domain + system type + ownership level (owned, led, built, contributed). No client, product, repo or team names.
- **Bullets**: 4-6, ordered by impact, one line each (about 18-28 words, two lines at most), each opening with a past-tense verb (Designed, Built, Automated, Migrated, Led, Reduced) and carrying **one** concrete number or scale (lines of code as scale, records, indices, environments, tests, versions spanned, team size) plus the tech in brackets or inline. Use only `measured` / `run-log` numbers as results; a `design` number reads "benchmarked on ..."; no `example`, no impact figure the user has not confirmed. Where an impact is still an Open question, write the bullet without it and note the upgrade in section 8.
- **Cover the spread**: at least one bullet each for (a) the main build with its scale, (b) quality/verification, (c) infrastructure or delivery, and, if the evidence exists, (d) documentation/knowledge sharing or (e) leadership/review. Do not spend two bullets on one area.
- **Tech line**: public technology names only, no internal tools.
- **Length**: fits in about 8-10 lines in a one-page CV; if it is longer, cut the weakest bullet.
- Keep it consistent with the rest of the summary: every number here must already appear in the Scale cards.

Example (generic, from a different project):

```
Platform Engineer | <Company> | <City, Country>                       Jul 2025 - Nov 2026
Owned the migration, rollback and verification tooling for upgrading large search clusters from Elasticsearch 6 to 9 on GCP.
- Built a phased, resumable rollback toolchain (Bash, Python; ~5k lines) with journaled pre-images and a verification gate, benchmarked on an 8M-document index.
- Verified 30,000 simulated create/update/delete mutations across 3 indices with zero failures using a Python/Bash simulation harness and a fault-injecting fake cluster.
- Provisioned reproducible GCP environments with Terraform (~20 resources: network, VMs, GKE, Cloud SQL) and Jenkins pipelines with parameterized stages.
- Migrated security users and roles across major versions preserving password hashes, avoiding credential resets.
- Authored ~5k lines of runbooks, test strategy and design docs, and a 1,000-file documentation knowledge base for AI-assisted operations.
Tech: Elasticsearch 6-9, Terraform, GCP (GKE, Compute, Cloud SQL), Kubernetes/Helm, Jenkins, Bash, Python, Docker
```

## Which numbers are credible (take them from each work area's Scale card; keep its provenance in the wording)

| Number | Source | Safe phrasing |
|---|---|---|
| Commits, active months | git | "300+ commits over 18 months" |
| Lines added (code + IaC) | git, bulk excluded | "~20k lines" |
| Share of current code | git blame | "main author (~60%) of ..." |
| Repos / services | git, folders | "across 8 repositories" |
| Tickets resolved, story points, cycle time | Jira | "resolved 150+ tickets across N epics" |
| Epics / projects led | Jira | "delivered N epics" (only if assigned) |
| Data volume / workload | scale card, tag `design` or `run-log` | `design`: "benchmarked on an 8M-document, ~50-field index"; `run-log`: "verified 30,000 mutations with zero failures". Never "migrated N documents" unless the user confirmed production |
| Runbooks / docs | Confluence | "authored 40+ runbooks and design pages (~30k words)" |
| Infra footprint | folders `infra` block | "Terraform for ~100+ resources", "N Helm charts / manifests" |
| Test discipline | folders | "kept ~30% test-to-code ratio" |
| Team size | git contributors | "in a team of ~6 engineers" |
| Reviews / PRs | gh or MR host | "reviewed 200+ pull requests" |

## Evidence → bullet ideas (look for these signals)

- Rollback / verification / dry-run scripts → reliability, "safe by design" migration tooling.
- Terraform + Helm + Dockerfiles + k8s kinds → infrastructure as code, containerization, deployment ownership.
- CI pipeline files, Jenkinsfile → delivery automation.
- Many Confluence runbooks created → operational excellence, knowledge sharing.
- High blame share on a repo with several contributors → ownership.
- Many bug-type tickets resolved with short cycle time → production support/maintenance.
- Epics assigned to the user → planning and delivery of larger initiatives.
- Reviews and merges → collaboration, quality gate.
- Performance/size words in subjects (index, shard, bulk, reindex, cache) → scale work; the actual numbers go to Open questions.

## Numbers only the user knows (put in Open questions, never fill in)

Downtime or maintenance window; data volume (documents, GB/TB); throughput/latency before and after; cost saved; users/customers affected; incident count reduced; time saved per run; SLA/SLO; deadline met.
For each, say where it usually lives: change ticket, post-mortem, dashboard, release notes, performance review.

## Keeping it high level

Replace client and product names with category + scale ("a financial-services client", "a ~10M-document index"); keep technology and method. Specifics belong in interviews, not on the page.
