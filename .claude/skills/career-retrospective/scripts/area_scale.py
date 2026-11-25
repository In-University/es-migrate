#!/usr/bin/env python3
"""Scale per WORK AREA (feature group): what the user added, and how big each area is today.

You (the LLM) define the areas after reading the digest, as path globs, in <raw>/areas.json:

  {"areas": [
     {"name": "Rollback tooling", "paths": ["scripts/es_rollback*", "docs/ES-ROLLBACK*", "scripts/rollback_*"]},
     {"name": "Jenkins module",   "paths": ["terraform/modules/jenkins/"], "repo": "my-repo"}   # repo is optional
  ]}

Path rules: a trailing "/" means "everything under"; otherwise fnmatch ("*" also crosses "/").
A file may match several areas (it is then counted in each). Files that match none are reported as
"unassigned" so you can refine the areas.

  python area_scale.py --root <repo or parent> [...] --identity RAW/identity.json --areas RAW/areas.json --out RAW

Writes RAW/areas_scale.json. Bulk commits (and files they brought in) are excluded, like in scan_git.
"""
import argparse
import fnmatch
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import scan_git as G  # noqa: E402


def matches(path, patterns):
    for pat in patterns:
        if pat.endswith("/"):
            if path.startswith(pat):
                return True
        elif fnmatch.fnmatch(path, pat):
            return True
    return False


def main():
    C.setup_stdio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--identity", required=True)
    ap.add_argument("--areas", required=True)
    ap.add_argument("--out", required=True, help="the raw/ directory (reads git/*.bulk_paths.txt, writes areas_scale.json)")
    ap.add_argument("--since")
    ap.add_argument("--months", type=int, default=C.DEFAULT_MONTHS)
    ap.add_argument("--until")
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--bulk-lines", type=int, default=5000)
    ap.add_argument("--bulk-files", type=int, default=300)
    a = ap.parse_args()
    ident = C.Identity.load(a.identity)
    since = C.resolve_since(a.since, a.months)
    areas = C.read_json(a.areas)["areas"]
    repos = []
    for root in a.root:
        repos += [r for r in C.find_repos(root, a.depth) if r not in repos]
    ids = G.repo_ids(repos)

    acc = {ar["name"]: {"repos": set(), "files_now": 0, "loc_now": Counter(), "lang_now": Counter(),
                        "commits": set(), "dates": set(), "add": Counter(), "del": Counter(), "lang_add": Counter(),
                        "files_touched": set()} for ar in areas}
    unassigned_add, unassigned_dirs = Counter(), Counter()
    for repo in repos:
        rid = ids[repo]
        my_areas = [ar for ar in areas if not ar.get("repo") or ar["repo"] in (rid, os.path.basename(repo))]
        if not my_areas:
            continue
        # history (my non-bulk commits)
        fmt = "--format=" + G.SEP_REC + G.SEP_FLD.join(["%H", "%aN", "%aE", "%aI", "%s"])
        since_a = ["--since=" + G.day_start(since)] if since else []
        until_a = ["--until=" + G.day_end(a.until)] if a.until else []
        raw = C.git(repo, "log", *G.REFS, "--no-merges", "-M", "--numstat", fmt, *since_a, *until_a, *ident.git_author_args())
        commits = G.parse_log(raw, ident, a.bulk_lines, a.bulk_files, keep_files=True)
        for c in commits:
            if c["bulk"]:
                continue
            for path, lang, cat, add, dele in c["_files"]:
                hit = False
                for ar in my_areas:
                    if matches(path, ar["paths"]):
                        hit = True
                        x = acc[ar["name"]]
                        x["repos"].add(rid)
                        x["commits"].add((rid, c["sha"]))
                        x["dates"].add(c["date"][:10])
                        x["add"][cat] += add
                        x["del"][cat] += dele
                        x["files_touched"].add((rid, path))
                        if cat in ("code", "test", "config"):
                            x["lang_add"][lang] += add
                if not hit:
                    unassigned_add[cat] += add
                    unassigned_dirs[C.module_of(path)] += add + dele
        # snapshot (what exists now, minus bulk imports)
        bulk_file = os.path.join(a.out, "git", rid + ".bulk_paths.txt")
        bulk = set()
        if os.path.isfile(bulk_file):
            with open(bulk_file, "r", encoding="utf-8") as fh:
                bulk = {ln for ln in fh.read().split("\n") if ln}
        files = [f for f in C.list_files(repo, True) if f not in bulk]
        for ar in my_areas:
            sel = [f for f in files if matches(f, ar["paths"])]
            if not sel:
                continue
            snap = C.snapshot(repo, sel)
            x = acc[ar["name"]]
            x["repos"].add(rid)
            x["files_now"] += len(sel)
            x["loc_now"].update(snap["loc_by_category"])
            for lg, v in snap["loc_by_language"].items():
                x["lang_now"][lg] += v["loc"]

    out_areas = []
    for ar in areas:
        x = acc[ar["name"]]
        out_areas.append({
            "name": ar["name"], "paths": ar["paths"], "repos": sorted(x["repos"]),
            "now": {"files": x["files_now"], "loc_by_category": dict(x["loc_now"]),
                    "code_loc": x["loc_now"]["code"] + x["loc_now"]["test"],
                    "top_languages": dict(x["lang_now"].most_common(6))},
            "mine": {"commits": len(x["commits"]), "files_touched": len(x["files_touched"]),
                     "first": min(x["dates"], default=None), "last": max(x["dates"], default=None),
                     "active_days": len(x["dates"]),
                     "lines_added": dict(x["add"]), "lines_deleted": dict(x["del"]),
                     "code_lines_added": x["add"]["code"] + x["add"]["test"],
                     "top_languages_added": dict(x["lang_add"].most_common(6))},
        })
    result = {"since": since, "areas": out_areas,
              "unassigned_my_lines_added": dict(unassigned_add),
              "unassigned_top_dirs": [{"dir": d, "lines_touched": n} for d, n in unassigned_dirs.most_common(8)],
              "note": "a file matching several areas is counted in each, so area totals may exceed the repo total"}
    C.write_json(os.path.join(a.out, "areas_scale.json"), result)
    for ar in out_areas:
        print(f"{ar['name'][:44]:44}  commits={ar['mine']['commits']:>3}  +code={ar['mine']['code_lines_added']:>6}  "
              f"now_code_loc={ar['now']['code_loc']:>6}  files_now={ar['now']['files']}")
    if unassigned_add:
        print("unassigned (refine areas.json):", dict(unassigned_add), [d["dir"] for d in result["unassigned_top_dirs"][:5]])


if __name__ == "__main__":
    main()
