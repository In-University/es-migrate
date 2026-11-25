# Scale dimensions - how big was each work area?

Every work area gets a **Scale card**: one row per dimension that applies, each with a value and a **provenance tag**. Whole-repo totals are not enough; a reader wants to know how big *this feature* was. Do not stop at lines of code and record counts: walk the catalog below and keep every dimension you can evidence.

## Provenance tags (mandatory on every number)

| Tag | Meaning | May appear in CV bullets? |
|---|---|---|
| `measured` | computed from git/files by a script (`area_scale.py`, digest) | yes |
| `run-log` | printed by a real run captured in a doc, report or test log (timestamps, PASS lines) | yes, say "in testing" |
| `design` | a documented target or sizing assumption (e.g. "benchmark index of 8M docs", capacity tables) | yes, as "designed for / benchmarked on" |
| `example` | illustrative output in a README ("delta 412873 doc(s)") | no, unless the user confirms it was real |
| `config` | a default or parameter value | rarely |
| `ask` | not in the data; goes to Open questions | after the user answers |

Never promote `example`/`design` to a production claim. Say "benchmark" / "test" / "design target" explicitly.

## Catalog

| Dimension | What to capture | How to find it |
|---|---|---|
| **Code** | lines added by me (code/test/config/docs), lines now, files, languages, commits, active days, calendar span | `area_scale.py` -> `areas_scale.json` |
| **Data volume** | records per index/table/topic, GB, growth, batch/page sizes, dataset names (generic) | `scale_hunt.py` groups *documents/records*, *data size*; generator scripts (`TOTAL`, `--count`), seed files, `docs.count` in logs, capacity tables in docs |
| **Data shape** | number of indices/tables/collections, fields per schema (leaf + nested), nested object kinds, shards/replicas | `scale_hunt.py` -> `mapping_files`, *indices*, *shards/replicas*; `jq` on mapping/DDL; migrations folder count |
| **Workload** | mutations/ops per run, creates/updates/deletes mix, delta size, throughput (docs/s), run duration | *throughput*, *tests/scenarios* groups; simulation READMEs; test reports |
| **Infrastructure** | VMs/nodes/clusters/pods, vCPU/RAM/disk, regions/zones, Terraform resources & modules, Helm charts/releases, namespaces, Dockerfiles, environments | `folders.json` infra block; grep `machine_type`, `replicas`, `resource "`; *nodes/hosts*, *compute* groups |
| **Delivery** | pipelines/jobs/stages/parameters, deploy targets, scripts count, modes/commands of a CLI, phases of a workflow | `grep -c "stage("`, `case` branches / `cmd_*` functions, `argparse` subcommands |
| **Quality** | test files, assertions, scenarios, verification checks run/passed, coverage, test:code ratio, dry-run/rollback safeguards | `folders.json` test ratio, `grep -c` assertions, test reports (`Total Checks`, `PASS`) |
| **Integration surface** | services/handlers/routes scanned or touched, systems connected, APIs consumed, versions spanned (e.g. 6.8 -> 9.2) | route counters in `folders.json`, README matrices, version lists |
| **Documentation** | pages/runbooks/specs, words/lines, languages, knowledge-base files | `areas_scale.json` docs lines; Confluence aggregates; `git ls-files docs | wc -l` |
| **Security/compliance** | users/roles/secrets migrated, auth modes, hashing, audit trails | dumps/fixtures (`jq 'length'`), docs |
| **Process** | tickets/epics/story points, PRs merged/reviewed, reviewers, stakeholders, team size | `jira.json`, `gh search prs`, git contributors |
| **Reliability/safety** | rollback steps, idempotency, resumability, journals, locks, verification gates, failure handling | script/phase names in the code; docs "guarantees" sections |
| **Impact** | downtime, time saved, cost, incidents, adoption | never in git; `ask` |

## Procedure per work area

1. Write/refresh `raw/areas.json` (path globs per area) and run `area_scale.py`; fix `unassigned` until nothing important is left out.
2. Run `scale_hunt.py` once for the whole repo; for each area read the candidate lines whose `file` falls in its paths.
3. **Open the context** of each candidate (`sed -n 'N-5,N+10p' file`) and decide its tag. Prefer numbers with a log/timestamp over prose.
4. Fill remaining catalog rows with targeted `grep`/`jq`/`wc` (recipes above). One command per row, smallest first.
5. Rows with nothing found stay empty; rows the data cannot answer become `ask`.

## Wording rules for the scale card

- Quote the unit and the basis: "8M-document, ~50-field benchmark index (design)".
- Ranges beat false precision: "~10k mutations per index across 3 indices (run-log)".
- Name datasets generically ("product catalog index", "orders index"), never by real index/table names.
