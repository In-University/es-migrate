# Discovery playbook - choose the route by situation

You are the investigator. Every route below works with plain `git`, `grep`/`git grep`, `jq`, `gh`, `curl` and by reading files; the scripts in `tools.md` only make some routes faster. If a tool fails or does not fit, take the manual route; do not stop. Run one cheap probe, read the result, then decide the next step. Loop back to any section whenever new evidence changes the picture.

Shell: examples are Bash (Git Bash on Windows). On PowerShell translate pipes; keep `-c core.quotepath=off` and UTF-8 in mind for Vietnamese text.

## 1. What can I reach? (decides everything else)

| Situation | Route |
|---|---|
| Repos are cloned locally | scan them (section 3-6) |
| Repos exist only on the host | ask the user to clone (or give URLs and consent). Without clones you can only use host APIs (`gh`, GitLab/Bitbucket REST) for PRs, reviews and file stats; say the history is partial |
| A clone is shallow (`git rev-parse --is-shallow-repository`) | `git fetch --unshallow` (ask first, network); otherwise report truncated history |
| Only the default branch is local | `git fetch --all --prune`; feature branches carry real work. Use `--branches --remotes --tags`, **not** `--all` (it drags in `refs/stash`) |
| Same repo cloned twice / fork | compare commit ids; count each commit once (a quick test: `git rev-list --all | sort` of both, `comm -12`) |
| Several repos in one parent folder | `find <root> -maxdepth 4 -name .git` lists them; third-party clones live there too, so identity (section 2) decides what is "mine" |
| Jira / Confluence reachable | read-only REST with a token the user put in a file (never in a command or in chat). Data Center: Bearer PAT, `/rest/api/2/...`; Cloud: Basic email+token, search is `/rest/api/3/search/jql` with `nextPageToken`. Test with `/rest/api/2/myself` first |
| No tokens | do git + folders, list the missing sources under Open questions, and ask the user to paste rough numbers (tickets closed, pages written) if they want them in |
| Work leaves no trace in git | go to section 8 |

## 2. Who is "me" in git? (never guess)

1. `git config user.name; git config user.email` (global and per repo) gives a hint only.
2. `git shortlog -sne --branches --remotes --tags` in each repo; combine across repos. People change e-mails (work, personal, `...@users.noreply.github.com`, old domain). `.mailmap` may already merge them.
3. Show the user the table (name, e-mail, commits, first/last date, repos) and ask which rows are theirs. A heavy committer in a folder the user merely cloned is the usual trap.
4. Bots (`[bot]`, dependabot, renovate, copilot) are not "me" and are not teammates; keep them out of team size.
5. Match on e-mail first; names collide. Count all of the user's identities as **one** person when you compute team size.

## 3. Scope the window and the terrain

- Window = the user's tenure (default the last 15 months for this user). Pass it as `--since=YYYY-MM-DDT00:00:00` (a bare date means "that day at the current clock time").
- Map before measuring: `git ls-files | cut -d/ -f1 | sort | uniq -c | sort -rn` (top dirs), `git log --format=%ad --date=format:%Y-%m | sort | uniq -c` (activity by month), `git log --diff-filter=A --format='%h %ad %s' --date=short -- <dir> | tail -1` (when a dir was born, by which commit).
- Look for **islands that are not the user's work**: archives, vendored libraries, generated code, imported docs, big JSON/CSV fixtures, lockfiles, `node_modules`, build output. They distort every number; list them before measuring.

## 4. Understand a repo fast (reading order)

README top 60 lines -> manifests (`package.json`, `go.mod`, `pom.xml`, `Chart.yaml`, `*.tf`, `Jenkinsfile`, `docker-compose.yml`) -> top-level dirs -> `git log --reverse --format=%s | head -20` (how it started) -> my commit subjects (`git log --author=<me> --format='%ad %s' --date=short`) -> the 3 biggest commits with `git show --stat <sha> | head -40` -> design docs/specs if any. Stop when you can state purpose, stack and the user's part in two sentences. Read source code only for a file or two, only when purpose is still unclear.

## 5. Group the work into areas (3-9)

Signals, strongest first: directories that move together; commit-subject prefixes/keywords (`feat(rollback)`, "jenkins", "simulate"); time bursts (a week of commits on one theme); Jira epics / Confluence spaces; docs titled after a feature; test files named after a feature. One work area = one thing a CV bullet could be about. A file may sit in two areas; note it instead of forcing a split. Re-cut the areas when a group is too big (>35% of effort) or too small to say anything.

## 6. Measure my contribution (and doubt every number)

Manual recipes (replace `ME` with author patterns; use several `--author=` flags, git ORs them):

```bash
R="--branches --remotes --tags"
# commits, active days, by month
git log $R --no-merges --author=ME --format=%ad --date=short | sort -u | wc -l
# lines added/deleted, with exclusions (pathspec)
git log $R --no-merges --author=ME --numstat --format= -- . ':(exclude)docs/versions' ':(exclude)*.lock' \
  | awk '$1!="-"{a+=$1;d+=$2} END{print "added",a,"deleted",d}'
# by file type: add `| awk` on the path column, or one pathspec per type (':(glob)**/*.py')
# biggest commits (bulk candidates)
git log $R --no-merges --author=ME --shortstat --format='%h %ad %s' --date=short
# lines of a file still authored by me
git blame -w -M --line-porcelain HEAD -- FILE | grep '^author ' | sort | uniq -c | sort -rn
# a feature's footprint
git log $R --no-merges --author=ME --numstat --format= -- scripts/feature_dir/
```

Pitfalls and what to do:

| Pitfall | Test | Fix |
|---|---|---|
| Bulk commit (import, archive, mass reformat) | one commit adds thousands of lines / hundreds of files | exclude it **and the files it brought in** from line counts, blame and "size today"; show the list to the user |
| Data/fixtures counted as code | big JSON/CSV lines | split by category: code, test, config/IaC, docs, data; report code separately |
| Renames shown as add+delete | `-M`; numstat paths like `{old => new}` | use `-M`, normalise paths |
| Generated/vendored/lockfiles | extension and directory | exclude by pathspec |
| Squash merges / rebases | few big commits, author is the merger | trust author of the squash commit but note it; check PR titles |
| Co-authored work | `Co-authored-by:` trailers | mention pair work; do not claim solo ownership |
| "Size today" inflated | code LOC now >> lines I ever added | the difference came from someone else or from an import; find it before quoting "codebase of N lines" |
| Blame share looks too good | ~100% | check imports and whether a bot or teammates changed files |

Sanity rule: a raw number is a lead, not a fact. Compute it twice by different routes (e.g. numstat vs blame, tool vs manual) or explain the gap.

## 7. Find scale numbers (they hide in text)

Where to look, in order of reliability: run logs/reports with timestamps and PASS/FAIL > test fixtures and seed data > generator/loader scripts (`TOTAL=8000000`, `--count`) > Terraform/Helm values (`machine_type`, `replicas`, `count`) > capacity tables and sizing sections in docs > READMEs > code comments > commit messages.

```bash
git grep -nEi '[0-9][0-9.,_]* *(million|triệu|k\b|docs?\b|documents|records|rows|indices|shards|fields|nodes|vcpu|gb|tb|req/s|docs/s)' -- . ':!<archive-dir>'
git grep -nEi '(doc_?count|total|TOTAL|number_of_shards|replicas|batch|page_?size)[ "'\'']*[:=]' -- '*.sh' '*.py' '*.tf' '*.yaml' '*.json'
jq '[.. | objects | select(has("type"))] | length' mapping.json        # fields in a schema
jq -s 'length' file.ndjson ; wc -l file.csv                               # records in a fixture
grep -rhoE 'resource "[a-z_]+"' <dir> --include=*.tf | sort | uniq -c    # IaC inventory
```

**Always open the context** (`sed -n 'N-6,N+12p' file`) and tag provenance (see `scale-dimensions.md`): a timestamped log is `run-log`; a sizing assumption is `design`; an illustrative block ("e.g.", sample output) is `example`; defaults are `config`. Never turn `design`/`example` into a production claim. Quantities in an archived/imported directory are not the user's.

## 8. Work that leaves little trace in git

| Kind of work | Where the evidence is |
|---|---|
| Design, planning, estimation | design docs/specs (commit authorship), Confluence pages created, Jira epics reported/assigned |
| Code review, mentoring | PRs/MRs reviewed (`gh search prs --reviewed-by @me`), review comments counts; ask the user |
| Operations, migrations run, incidents | change tickets, runbooks written, post-mortems, Jenkins job history; mostly **ask** |
| Support / maintenance | Jira bug tickets resolved, cycle time, small commits across many repos |
| Leading a team | PRs reviewed, tickets assigned to others (reporter = me), docs and decisions; commit counts understate it |
| Work done in another system (BI, spreadsheets, dashboards) | ask the user; do not infer |

## 9. Plausibility checks before writing a number

- Lines per active day above ~1,500 sustained? Probably a bulk/generated source.
- More commits than active days x 15? Probably automated.
- Share of codebase >90% in a repo with several contributors? Check imports.
- "Size today" larger than everything the user ever added? Someone else's or imported code is included.
- A dataset figure with no timestamped log nearby? It is `design` or `example`.
- Dates outside the user's tenure? Wrong repo or identity.

## 10. Stop and ask the user when

identity is ambiguous; two areas look alike but ownership is unclear; a number fails a plausibility check and you cannot explain it in two probes; the repo is a fork or clone and authorship is mixed; impact (downtime, cost, users, data volume in production) is needed; a source needs credentials; the user must choose between claiming and omitting something doubtful.
