#!/usr/bin/env python3
"""Turn the raw JSON in <out>/ into one compact Markdown digest of verified numbers.

  python digest.py --out OUT          -> prints and writes OUT/digest.md

The digest is the ONLY place the summary's numbers should be copied from.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def fmt(n):
    return f"{n:,}" if isinstance(n, int) else str(n)


def table(rows, headers):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def git_section(d):
    t = d["totals"]
    L = ["## Git (personal contribution)", "",
         f"- Identity: {len(d['identity']['emails'])} email(s), {len(d['identity']['names'])} name(s) (see git/summary.json)",
         f"- Window: {d.get('since') or 'all time'} → {d.get('until') or 'now'}; first/last commit {t['first_commit']} → {t['last_commit']}",
         f"- Repos with my commits: {t['repos_with_my_commits']} / {t['repos_scanned']} scanned",
         f"- Commits (each counted once): {fmt(t['commits'])}; active days: {fmt(t['active_days_total'])}",
         f"- Code+test lines added/deleted (bulk commits excluded): +{fmt(t['code_lines_added'])} / -{fmt(t['code_lines_deleted'])}",
         f"- Config/IaC lines added: {fmt(t['config_lines_added'])}; docs lines added: {fmt(t['docs_lines_added'])}",
         f"- Bulk commits excluded from line totals: {t['bulk_commits_excluded']}  (rule: {d['bulk_rule']})",
         f"- Languages by lines added: " + ", ".join(f"{k} {fmt(v)}" for k, v in list(t["languages_lines_added"].items())[:8])]
    if t.get("duplicate_commits_dropped"):
        L.append(f"- Duplicate clones: {t['duplicate_commits_dropped']} repeated commits counted once; "
                 f"duplicate repos: {', '.join(t['repos_duplicate_clones']) or '-'}")
    if t["shallow_repos"]:
        L.append("- ⚠ shallow clones (history truncated): " + ", ".join(t["shallow_repos"]))
    L += ["", table([[r["repo"], r["my_commits"], r["first_commit"], r["last_commit"], fmt(r["code_lines_added"]),
                      fmt(r["lines_added"].get("config", 0)), fmt(r["repo_snapshot"]["code_loc"]),
                      f"{r['team']['my_share_of_commits_pct']}% of {r['team']['contributors']} ppl",
                      (f"{r['blame']['share_of_repo_code_config_loc_pct']}%" + ("" if r['blame']['complete'] else " (partial)")) if r["blame"] else "-"]
                     for r in d["repos"]],
                    ["repo", "my commits", "first", "last", "code +lines", "config +lines", "repo code LOC now (excl. bulk imports)",
                     "my commit share / team", "my share of current LOC (blame)"]), ""]
    bulk, seen_sha = [], set()
    for r in d["repos"]:
        for c in r["bulk_commits_excluded"]:
            if c["sha"] not in seen_sha:
                seen_sha.add(c["sha"])
                bulk.append((r["repo"], c))
    if bulk:
        L += ["### Excluded bulk commits (review: raise --bulk-lines if one is really your work)", "",
              table([[r, c["sha"], c["date"][:10], c["subject"][:70], c["files"], sum(c["add"].values())] for r, c in bulk],
                    ["repo", "sha", "date", "subject", "files", "lines added"]), ""]
    L.append("### Per repo detail\n")
    for r in d["repos"]:
        L += [f"**{r['repo']}**  (remote: {r['remote'] or 'n/a'})",
              f"- commit types: {r['commit_types']}; merges by me: {r['my_merge_commits']}; PR/MR refs seen: {r['pr_refs_seen']}",
              f"- top modules: " + ", ".join(f"{m['module']} ({m['commits']}c)" for m in r["top_modules"][:6]),
              f"- repo snapshot languages (LOC now): {r['repo_snapshot']['top_languages']}",
              "- biggest commits: " + "; ".join(f"{c['sha'][:7]} {c['subject'][:60]}" for c in r["top_commits"][:5]), ""]
    return "\n".join(L)


def folders_section(d):
    t = d["totals_current_snapshot"]
    L = ["## Project scale (current snapshot; NOT personal contribution)", "",
         f"- Filter: {d.get('filter', 'n/a')}; files that came from bulk imports are left out of these snapshots",
         f"- Skipped by filter: {len(d.get('skipped', []))} repo(s)",
         f"- Projects: {len(d['projects'])}; tracked files: {fmt(t.get('tracked_files', 0))}",
         f"- LOC now (non-blank): code {fmt(t.get('loc_code', 0))}, test {fmt(t.get('loc_test', 0))}, config/IaC {fmt(t.get('loc_config', 0))}, docs {fmt(t.get('loc_docs', 0))}",
         f"- Approx HTTP routes: {t.get('http_routes_approx', 0)}; Terraform resources: {t.get('terraform_resources', 0)}; Dockerfiles: {t.get('dockerfiles', 0)}",
         f"- Languages (LOC): " + ", ".join(f"{k} {fmt(v)}" for k, v in list(d["languages_loc"].items())[:8]), ""]
    rows = []
    for p in d["projects"][:25]:
        g, i = p.get("git") or {}, p["infra"]
        shortpath = "/".join(p["path"].replace("\\", "/").rstrip("/").split("/")[-2:])
        rows.append([shortpath, fmt(p["snapshot"]["code_loc"]), p["test_to_code_ratio_pct"], p["tracked_files"],
                     g.get("contributors_all_time", "-"), g.get("contributors_last_12m", "-"),
                     f"{g.get('first_commit', '-')}→{g.get('last_commit', '-')}", g.get("commits_all_authors", "-"),
                     i["http_routes_approx"], i["dockerfiles"], i["terraform_resources"], sum(p["dependencies"].values()),
                     ", ".join(f"{k}:{v['loc']}" for k, v in list(p["snapshot"]["loc_by_language"].items())[:3])])
    if len(d["projects"]) > 25:
        L.append(f"(table shows the 25 largest of {len(d['projects'])} projects by code LOC; the rest are in folders.json)\n")
    L.append(table(rows, ["project", "code LOC", "test %", "files", "contrib (all)", "contrib 12m", "history", "commits",
                          "routes≈", "Dockerfiles", "TF res", "deps", "top langs"]))
    return "\n".join(L) + "\n"


def jira_section(d):
    a = d["aggregates"]["assigned_to_me"]
    r = d["aggregates"]["reported_by_me"]
    L = ["## Jira", "", f"- Instance: {d['instance']} ({d['flavor']}); since {d.get('since') or 'all time'}",
         f"- Issues touched (assigned/reported/worklog): {d['aggregates']['issues_touched_total']}",
         f"- Assigned to me (ever): {a['count']}, done {a['done']}, currently mine {a['currently_assigned_to_me']}; types {a['by_type']}",
         f"- Story points done: {a['story_points_done']} (of {a['story_points_all']}); sprints: {a['sprints_distinct']}; "
         f"median cycle {a['cycle_days_median']} d, mean {a['cycle_days_mean']} d",
         f"- Reported by me: {r['count']} ({r['by_type']}); my logged hours: {d['aggregates']['my_logged_hours_total']}",
         f"- Projects: {a['by_project']}; per year: {a['by_year_created']}; created window {a['first_created']} → {a['last_created']}",
         f"- Components: {a['top_components']}; labels: {a['top_labels']}"]
    if d["warnings"]:
        L.append("- ⚠ warnings: " + " | ".join(d["warnings"]))
    L += ["", "### Top epics (what the work was for)", "", table([[e["epic"], e["summary"], e["issues"]] for e in a["top_epics"]],
                                                              ["epic", "title", "my issues"]), ""]
    return "\n".join(L)


def conf_section(d):
    a = d["aggregates"]
    L = ["## Confluence", "", f"- Instance: {d['instance']} ({d['flavor']}); since {d.get('since') or 'all time'}",
         f"- Pages created by me: {a['pages_created_by_me']}; edited (not created): {a['pages_edited_not_created']}",
         f"- Spaces (created): {a['by_space_created']}; per year: {a['by_year_created']}",
         f"- In my created pages: ~{fmt(a['words_in_my_created_pages'])} words, {a['code_blocks_in_my_created_pages']} code blocks, "
         f"{a['tables_in_my_created_pages']} tables, {a['images_in_my_created_pages']} images"]
    if d["warnings"]:
        L.append("- ⚠ warnings: " + " | ".join(d["warnings"]))
    L += ["", "### Largest pages I created", "", table([[p["title"], p["space"], p["words"]] for p in a["top_pages_by_words"]],
                                                      ["title", "space", "words"]), ""]
    return "\n".join(L)


def areas_section(d):
    rows = []
    for a in d["areas"]:
        m, n = a["mine"], a["now"]
        la, lc = m["lines_added"], n["loc_by_category"]
        rows.append([a["name"], m["commits"], m["files_touched"], fmt(la.get("code", 0) + la.get("test", 0)),
                     fmt(la.get("config", 0)), fmt(la.get("docs", 0)), fmt(n["code_loc"]), fmt(lc.get("config", 0)),
                     n["files"], m["active_days"], f"{m['first']}→{m['last']}",
                     ", ".join(f"{k} {fmt(v)}" for k, v in list(m["top_languages_added"].items())[:3])])
    L = ["## Scale by work area (lines I added vs. size today; bulk imports excluded)", "",
         table(rows, ["area", "commits", "files touched", "code+test added", "config added", "docs added",
                      "code LOC now", "config LOC now", "files now", "active days", "span", "languages added"]), "",
         f"- Unassigned (not in any area): lines added {d.get('unassigned_my_lines_added')}; "
         f"top dirs {[x['dir'] for x in d.get('unassigned_top_dirs', [])[:5]]}",
         f"- {d['note']}", ""]
    return "\n".join(L)


def hunt_section(d):
    L = ["## Scale numbers found in text (CANDIDATES: open the context, tag provenance, never assume production)", ""]
    if d["mapping_files"]:
        L.append("- Schema files: " + "; ".join(f"{m['file']} = {m['leaf_fields']} leaf fields (+{m['object_fields']} objects)"
                                               for m in d["mapping_files"][:5]))
    for group, v in d["groups"].items():
        L += ["", f"**{group}** ({v['total_mentions']} mentions in {v['files']} files)"]
        for it in v["top_by_value"][:6]:
            L.append(f"- {it['value']:,.0f}  `{it['file']}:{it['line']}`  {it['text'][:110]}")
    return "\n".join(L) + "\n"


def main():
    C.setup_stdio()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    parts = ["# Digest of verified numbers", ""]
    for rel, fn in (("git/summary.json", git_section), ("areas_scale.json", areas_section),
                    ("scale_hunt.json", hunt_section), ("folders.json", folders_section),
                    ("jira/jira.json", jira_section), ("confluence/confluence.json", conf_section)):
        path = os.path.join(a.out, rel)
        if os.path.isfile(path):
            parts.append(fn(C.read_json(path)))
        else:
            parts.append(f"## (missing: {rel} — source not collected)\n")
    text = "\n".join(parts)
    with open(os.path.join(a.out, "digest.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
