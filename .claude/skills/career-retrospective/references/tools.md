# Optional accelerators (`scripts/`)

Nothing here is required. Each script automates a route from `playbook.md`; use it when it saves time, verify its output the same way you would verify a hand count, and fall back to the manual route when it fails or does not fit. All scripts are stdlib-only Python, read-only on company systems, UTF-8 safe, and accept several `--root`.

`S` = the `scripts/` folder next to `SKILL.md`. Run `python "$S/<name>.py" -h` for every option.

| Script | Saves you from | Skip it when |
|---|---|---|
| `scan_git.py discover / identity` | hand-merging `git shortlog` across many repos; picking identities by row number so no e-mail is typed into a command | one or two repos: `git shortlog -sne` is faster |
| `scan_git.py scan` | per-repo and total commits, lines by category and language, bulk-commit detection, months, team size, optional blame share; each commit counted once across duplicate clones | you only need one number: use the manual recipes |
| `scan_folder.py` | LOC by language/category via `git ls-files`, infra inventory (Dockerfile, Terraform resources, k8s kinds, CI files), test ratio, dependency counts, contributors; `--only-mine` keeps only repos with the user's commits | the question is about one directory: use `git ls-files -- dir` and `wc` |
| `area_scale.py` | per work-area lines added / size today / commits / span from a hand-written `areas.json` (path globs) | areas are few and path-simple: loop `git log --numstat -- <paths>` yourself |
| `scale_hunt.py` | a ranked list of "number + unit" candidates (docs, GB, shards, fields, nodes, throughput, tests) with `file:line`, and field counts of JSON mappings | you already know which document holds the numbers |
| `scan_atlassian.py` | paginated Jira (assigned/reported/worklog) and Confluence (created/contributed) pulls with DC and Cloud differences handled; raw JSON out | the user can export or paste numbers; or only a handful of tickets matter |
| `digest.py` | one Markdown digest of the JSON the scripts wrote | you did not run the scripts |

## Typical use (adapt freely)

```bash
python "$S/scan_git.py" discover --root <dir> [--root <dir2>] --json W/raw/identities.json     # table with row numbers
python "$S/scan_git.py" identity --discover W/raw/identities.json --pick 1,3 --out W/raw/identity.json
python "$S/scan_git.py" scan   --root <dir> --identity W/raw/identity.json --out W/raw [--blame] [--fetch]
python "$S/scan_folder.py"     --root <dir> --only-mine W/raw/git/summary.json --out W/raw
python "$S/area_scale.py"      --root <dir> --identity W/raw/identity.json --areas W/raw/areas.json --out W/raw
python "$S/scale_hunt.py"      --root <dir> --out W/raw --exclude-prefix <archive-dir>/
python "$S/scan_atlassian.py"  whoami [--env-file <path>]   # then: all --out W/raw
python "$S/digest.py"          --out W/raw
```

The default time window is the last 15 months (`--months N`, or `--since YYYY-MM-DD|all`).

## What the outputs mean (read them critically)

- **bulk commit**: >5,000 code/test/config lines, >15,000 docs lines or >300 files in one commit. It is excluded from line totals, and the files it brought in are excluded from "size today" and blame. A real feature that trips the rule is listed in the digest; raise `--bulk-lines` if the user confirms it is theirs.
- **code lines** = `code` + `test` categories; config/IaC, docs and data are reported separately. `loc` = non-blank lines.
- **blame share** = lines still authored by the user in files they touched, divided by code+config lines now (bulk imports excluded). It can be below 100% because of bots, teammates or untouched files.
- **team size** counts all of the user's identities as one person and ignores bots.
- **scale_hunt candidates** are text hits, not facts: open the context and tag provenance.
- **`areas_scale.json`**: a file matching several areas counts in each.
- **Atlassian**: `assignee WAS currentUser()` includes tickets later handed on; `currently_assigned_to_me` is the stricter count. Warnings in the JSON list JQL/CQL that failed.

## Credentials for Jira / Confluence

Put them in `<skill dir>/.env` (template `.env.example`) or pass an existing file with `--env-file` (for example the editing-confluence-runbooks `.env`). Missing values: ask the user to fill the file; never read it aloud, never place a token in a command, in chat or in output. DC uses a Personal Access Token as Bearer; setting `*_EMAIL` switches to Basic (Cloud).
