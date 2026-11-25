#!/usr/bin/env python3
"""Scan git history for what ONE person did.

  discover  list author identities found under --root (so the user can say which are theirs)
  identity  build the identity file by picking rows (numbers) from `discover` output
  scan      per-repo + total metrics for an identity file; writes <out>/git/summary.json
            and <out>/git/<repo>.commits.jsonl (sha, date, subject, line counts)

Examples:
  python scan_git.py discover --root D:/Workspace --json OUT/identities.json
  python scan_git.py identity --discover OUT/identities.json --pick 1,3 --out OUT/identity.json
  python scan_git.py scan --root D:/Workspace --identity OUT/identity.json --out OUT --since 2023-03-01 --blame
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

REFS = ["--branches", "--remotes", "--tags"]  # not --all: that would pull in refs/stash
SEP_REC, SEP_FLD = "\x1e", "\x1f"
CONVENTIONAL = re.compile(r"^(feat|fix|refactor|docs|test|tests|chore|perf|ci|build|revert|style|hotfix)(\([^)]*\))?!?:", re.I)
PR_REF = re.compile(r"\(#(\d+)\)|[Mm]erge pull request #(\d+)|See merge request [^\s]*!(\d+)|Merged PR (\d+)")


# ----------------------------------------------------------------------------- discover


def cmd_discover(args):
    ident = Counter()
    repos_of = defaultdict(set)
    first_last = {}
    repos = []
    for root in args.root:
        repos += [r for r in C.find_repos(root, args.depth) if r not in repos]
    if not repos:
        sys.exit("No git repositories found under: " + ", ".join(args.root))
    for repo in repos:
        out = C.git(repo, "log", *REFS, "--format=%aN" + SEP_FLD + "%aE" + SEP_FLD + "%as")
        for line in out.splitlines():
            parts = line.split(SEP_FLD)
            if len(parts) != 3:
                continue
            key = (parts[0], parts[1].lower())
            ident[key] += 1
            repos_of[key].add(os.path.basename(repo))
            lo, hi = first_last.get(key, (parts[2], parts[2]))
            first_last[key] = (min(lo, parts[2]), max(hi, parts[2]))
    hints = {"git config user.name": C.git(".", "config", "--global", "user.name").strip(),
             "git config user.email": C.git(".", "config", "--global", "user.email").strip()}
    rows = []
    for (name, email), n in ident.most_common():
        rows.append({"name": name, "email": email, "commits": n, "bot": C.is_bot(name, email),
                     "repos": sorted(repos_of[(name, email)]), "first": first_last[(name, email)][0],
                     "last": first_last[(name, email)][1]})
    print(f"Scanned {len(repos)} repo(s). Global git identity hint: {hints}")
    print(f"{'#':>3} {'commits':>7}  {'first':10}  {'last':10}  {'bot':3}  identity  [repos]")
    for i, r in enumerate(rows[: args.top], 1):
        repos_s = ",".join(r["repos"][:4]) + ("…" if len(r["repos"]) > 4 else "")
        print(f"{i:>3} {r['commits']:>7}  {r['first']}  {r['last']}  {'bot' if r['bot'] else '   '}  "
              f"{r['name']} <{r['email']}>  [{repos_s}]")
    if args.json:
        C.write_json(args.json, {"git_config_hint": hints, "repos": repos, "identities": rows})
        C.log("wrote " + args.json)


def cmd_identity(args):
    rows = C.read_json(args.discover)["identities"]
    picks = [int(x) for x in args.pick.split(",") if x.strip()]
    bad = [n for n in picks if not 1 <= n <= len(rows)]
    if bad:
        sys.exit(f"row number(s) out of range 1..{len(rows)}: {bad}")
    chosen = [rows[n - 1] for n in picks]
    ident = {"emails": sorted({r["email"] for r in chosen}),
             "names": sorted({r["name"] for r in chosen}) if args.with_names else []}
    C.write_json(args.out, ident)
    print(f"identity file {args.out}: {len(ident['emails'])} email(s), {len(ident['names'])} name(s); "
          f"covers {sum(r['commits'] for r in chosen)} commits")


# ----------------------------------------------------------------------------- scan


def parse_log(text, ident, bulk_lines, bulk_files, keep_files=False):
    """Parse `git log --numstat` output into one dict per commit authored by `ident`."""
    commits = []
    for rec in text.split(SEP_REC):
        if not rec.strip():
            continue
        head, _, body = rec.partition("\n")
        f = head.split(SEP_FLD)
        if len(f) < 5 or not ident.matches(f[1], f[2]):
            continue
        sha, _name, _email, date, subject = f[0], f[1], f[2], f[3], SEP_FLD.join(f[4:])
        add_cat, del_cat, add_lang = Counter(), Counter(), Counter()
        files = excluded_lines = 0
        paths = []
        flist = []
        modules = Counter()
        for ln in body.splitlines():
            m = ln.split("\t")
            if len(m) != 3:
                continue
            a, d, path = m
            path = C.normalize_numstat_path(path)
            a = 0 if a == "-" else int(a)
            d = 0 if d == "-" else int(d)
            lang, cat = C.classify(path)
            if cat == "excluded":
                excluded_lines += a + d
                continue
            files += 1
            paths.append(path)
            if keep_files:
                flist.append((path, lang, cat, a, d))
            add_cat[cat] += a
            del_cat[cat] += d
            if cat in ("code", "test", "config"):
                add_lang[lang] += a
                modules[C.module_of(path)] += a + d
        loc_add = add_cat["code"] + add_cat["test"] + add_cat["config"]
        is_bulk = loc_add > bulk_lines or files > bulk_files or add_cat["docs"] > 3 * bulk_lines
        commits.append({
            "sha": sha[:10], "date": date, "subject": subject.strip(), "files": files,
            "add": dict(add_cat), "del": dict(del_cat), "excluded_lines": excluded_lines,
            "bulk": is_bulk, "_paths": paths if is_bulk else [], "_files": flist,
            "_lang": add_lang, "_modules": modules,
        })
    return commits


def blame_user(repo, rel, ident):
    out = C.git(repo, "blame", "--line-porcelain", "-w", "-M", "HEAD", "--", rel, timeout=90)
    mine = total = 0
    name = email = None
    for ln in out.splitlines():
        if ln.startswith("author "):
            name = ln[7:]
        elif ln.startswith("author-mail "):
            email = ln[12:].strip("<> ")
        elif ln.startswith("\t") and ln.strip():  # content line of a non-blank source line
            total += 1
            if ident.matches(name, email):
                mine += 1
    return rel, mine, total


def repo_ids(repos):
    """Unique, readable id per repo: basename, or parent__basename when basenames collide."""
    def base(r):
        return os.path.basename(r.rstrip("\\/"))
    count = Counter(base(r) for r in repos)
    return {r: base(r) if count[base(r)] == 1 else os.path.basename(os.path.dirname(r.rstrip("\\/"))) + "__" + base(r)
            for r in repos}


def day_start(d):
    """git treats a bare date as that day at the CURRENT time of day; pin it to 00:00."""
    return d + "T00:00:00" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else d


def day_end(d):
    return d + "T23:59:59" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else d


def scan_repo(repo, name, ident, a):
    since = ["--since=" + day_start(a.since)] if a.since else []
    until = ["--until=" + day_end(a.until)] if a.until else []
    fmt = "--format=" + SEP_REC + SEP_FLD.join(["%H", "%aN", "%aE", "%aI", "%s"])
    mine_raw = C.git(repo, "log", *REFS, "--no-merges", "-M", "--numstat", fmt, *since, *until,
                     *ident.git_author_args())
    commits = parse_log(mine_raw, ident, a.bulk_lines, a.bulk_files)

    merges_raw = C.git(repo, "log", *REFS, "--merges", "--format=" + SEP_REC + SEP_FLD.join(["%H", "%aN", "%aE", "%aI", "%s"]),
                       *since, *until, *ident.git_author_args())
    merges = parse_log(merges_raw, ident, 10**9, 10**9)

    # everyone's commits (counts only) -> team context and the user's share
    everyone = C.git(repo, "log", *REFS, "--no-merges", "--format=%aN" + SEP_FLD + "%aE", *since, *until)
    people = Counter()
    for ln in everyone.splitlines():
        p = ln.split(SEP_FLD)
        if len(p) == 2 and not C.is_bot(p[0], p[1]):
            # all of my identities (work/personal/noreply e-mails) are ONE person
            people["<me>" if ident.matches(p[0], p[1]) else p[1].lower()] += 1
    total_commits = sum(people.values())

    shallow = C.git(repo, "rev-parse", "--is-shallow-repository").strip() == "true"
    remote = C.clean_remote(C.git(repo, "config", "--get", "remote.origin.url"))
    roots = C.git(repo, "log", *REFS, "--max-parents=0", "--format=%as").split()
    repo_first = min(roots) if roots else None

    kept = [c for c in commits if not c["bulk"]]
    bulk = [c for c in commits if c["bulk"]]
    tot_add, tot_del, langs, modules = Counter(), Counter(), Counter(), Counter()
    module_commits = Counter()
    for c in kept:
        for k, v in c["add"].items():
            tot_add[k] += v
        for k, v in c["del"].items():
            tot_del[k] += v
        langs.update(c["_lang"])
        modules.update(c["_modules"])
        module_commits.update(c["_modules"].keys())
    types = Counter()
    for c in commits:
        m = CONVENTIONAL.match(c["subject"])
        types[m.group(1).lower() if m else "other"] += 1
    months = Counter(c["date"][:7] for c in commits)
    days = {c["date"][:10] for c in commits}
    pr_refs = set()
    for c in commits + merges:
        for m in PR_REF.finditer(c["subject"]):
            pr_refs.add(next(g for g in m.groups() if g))

    # files that arrived through bulk commits (archives, imports, mass reformat) are not "my code":
    # leave them out of the repo snapshot and of blame
    files_all = C.list_files(repo, True)
    bulk_paths = set()
    for c in bulk:
        bulk_paths.update(c["_paths"])
    bulk_at_head = sorted(bulk_paths & set(files_all))
    files_keep = [f for f in files_all if f not in bulk_paths]
    snap = C.snapshot(repo, files_keep)
    os.makedirs(os.path.join(a.out, "git"), exist_ok=True)
    with open(os.path.join(a.out, "git", name + ".bulk_paths.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(bulk_at_head))
    blame = None
    if a.blame and commits:
        # files the user touched (numstat again), restricted to files that still exist at HEAD
        touched_paths = set()
        for line in C.git(repo, "log", *REFS, "--no-merges", "-M", "--numstat", "--format=", *since, *until,
                          *ident.git_author_args()).splitlines():
            m = line.split("\t")
            if len(m) == 3:
                touched_paths.add(C.normalize_numstat_path(m[2]))
        head_files = set(files_keep)
        cand = [p for p in touched_paths & head_files if C.classify(p)[1] in ("code", "test", "config")
                and os.path.exists(os.path.join(repo, p))
                and os.path.getsize(os.path.join(repo, p)) <= 1_500_000]
        cand.sort(key=lambda p: -os.path.getsize(os.path.join(repo, p)))
        todo = cand[: a.blame_max_files]
        mine = total = 0
        with ThreadPoolExecutor(max_workers=6) as ex:
            for _rel, m_, t_ in ex.map(lambda p: blame_user(repo, p, ident), todo):
                mine += m_
                total += t_
        repo_loc = snap["code_loc"] + snap["loc_by_category"].get("config", 0)
        blame = {"files_blamed": len(todo), "files_candidates": len(cand), "complete": len(todo) == len(cand),
                 "lines_still_authored_by_me": mine, "lines_in_blamed_files": total,
                 "share_of_repo_code_config_loc_pct": round(100 * mine / repo_loc, 1) if repo_loc else None}

    top_commits = sorted(kept, key=lambda c: -(sum(c["add"].values()) + sum(c["del"].values())))[:15]
    keep_fields = ("sha", "date", "subject", "files", "add", "del")
    summary = {
        "repo": name, "path": repo, "remote": remote, "shallow_clone": shallow,
        "repo_first_commit": repo_first,
        "my_commits": len(commits), "my_merge_commits": len(merges), "pr_refs_seen": len(pr_refs),
        "first_commit": min((c["date"][:10] for c in commits), default=None),
        "last_commit": max((c["date"][:10] for c in commits), default=None),
        "active_days": len(days), "active_months": len(months),
        "commits_by_month": dict(sorted(months.items())),
        "commit_types": dict(types.most_common()),
        "lines_added": dict(tot_add), "lines_deleted": dict(tot_del),
        "code_lines_added": tot_add["code"] + tot_add["test"],
        "code_lines_deleted": tot_del["code"] + tot_del["test"],
        "languages_lines_added": dict(langs.most_common(12)),
        "top_modules": [{"module": m, "lines_touched": n, "commits": module_commits[m]} for m, n in modules.most_common(10)],
        "team": {"contributors": len(people), "total_commits_in_range": total_commits,
                 "my_share_of_commits_pct": round(100 * len(commits) / total_commits, 1) if total_commits else None},
        "bulk_commits_excluded": [{k: c[k] for k in keep_fields} for c in bulk],
        "top_commits": [{k: c[k] for k in keep_fields} for c in top_commits],
        "repo_snapshot": {"files_excluded_as_bulk_imports": len(bulk_at_head), "code_loc": snap["code_loc"], "loc_by_category": snap["loc_by_category"],
                          "top_languages": {k: v["loc"] for k, v in list(snap["loc_by_language"].items())[:8]}},
        "blame": blame,
    }
    jsonl = os.path.join(a.out, "git", name + ".commits.jsonl")
    os.makedirs(os.path.dirname(jsonl), exist_ok=True)
    with open(jsonl, "w", encoding="utf-8", newline="\n") as fh:
        for c in commits:
            fh.write(json.dumps({k: c[k] for k in keep_fields + ("bulk",)}, ensure_ascii=False) + "\n")
    return summary, commits


def cmd_scan(args):
    ident = C.Identity.load(args.identity)
    args.since = C.resolve_since(args.since, args.months)
    C.log(f"window: {args.since or 'all time'} -> {args.until or 'now'}")
    if not (ident.emails or ident.names):
        sys.exit("identity file has no emails/names")
    repos = []
    for root in args.root:
        repos += [r for r in C.find_repos(root, args.depth) if r not in repos]
    if not repos:
        sys.exit("No git repositories found under: " + ", ".join(args.root))
    ids = repo_ids(repos)
    results = []
    for i, repo in enumerate(repos, 1):
        C.log(f"[{i}/{len(repos)}] {repo}")
        if args.fetch:
            C.git(repo, "fetch", "--all", "--prune", "--quiet", timeout=300)
        s, commits = scan_repo(repo, ids[repo], ident, args)
        if s["my_commits"] == 0:
            C.log("   no commits by this identity - skipped")
            continue
        results.append((s, commits))

    # The same repo cloned twice (or a fork) must not be counted twice: totals use each commit once.
    first_owner, unique, shared = {}, [], {}
    for s, commits in results:
        sh = Counter()
        for c in commits:
            owner = first_owner.get(c["sha"])
            if owner is None:
                first_owner[c["sha"]] = s["repo"]
                unique.append(c)
            else:
                sh[owner] += 1
        shared[s["repo"]] = sh
    summaries = [s for s, _c in results]
    for s in summaries:
        sh = shared[s["repo"]]
        s["shares_commits_with"] = dict(sh)
        dup = [o for o, n in sh.items() if n >= 0.9 * s["my_commits"]]
        s["duplicate_of"] = dup[0] if dup else None
    summaries.sort(key=lambda s: -s["my_commits"])

    kept = [c for c in unique if not c["bulk"]]
    add, dele, lang_tot = Counter(), Counter(), Counter()
    for c in kept:
        add.update(c["add"])
        dele.update(c["del"])
        lang_tot.update(c["_lang"])
    dates = [c["date"][:10] for c in unique]
    totals = {
        "repos_with_my_commits": len(summaries), "repos_scanned": len(repos),
        "repos_duplicate_clones": [s["repo"] for s in summaries if s["duplicate_of"]],
        "commits": len(unique),
        "duplicate_commits_dropped": sum(s["my_commits"] for s in summaries) - len(unique),
        "active_days_total": len(set(dates)),
        "code_lines_added": add["code"] + add["test"], "code_lines_deleted": dele["code"] + dele["test"],
        "config_lines_added": add["config"], "docs_lines_added": add["docs"],
        "bulk_commits_excluded": sum(1 for c in unique if c["bulk"]),
        "first_commit": min(dates, default=None), "last_commit": max(dates, default=None),
        "shallow_repos": [s["repo"] for s in summaries if s["shallow_clone"]],
        "languages_lines_added": dict(lang_tot.most_common(15)),
        "note": "totals count each commit once even if several clones contain it; per-repo rows keep their own counts",
    }
    out = {"identity": ident.to_dict(), "since": args.since, "until": args.until,
           "bulk_rule": f"commit excluded from line totals (and its files from snapshot/blame) when it adds >{args.bulk_lines} code/test/config lines, >{3 * args.bulk_lines} docs lines, or touches >{args.bulk_files} files",
           "totals": totals, "repos": summaries}
    C.write_json(os.path.join(args.out, "git", "summary.json"), out)
    print(f"commits={totals['commits']} (dropped {totals['duplicate_commits_dropped']} duplicates) repos={len(summaries)} "
          f"code_lines_added={totals['code_lines_added']} -> {os.path.join(args.out, 'git', 'summary.json')}")
    if totals["repos_duplicate_clones"]:
        print("NOTE duplicate clones (same commits as another repo): " + ", ".join(totals["repos_duplicate_clones"]))
    if totals["shallow_repos"]:
        print("WARNING shallow clones (history truncated): " + ", ".join(totals["shallow_repos"]))


def main():
    C.setup_stdio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discover")
    d.add_argument("--root", action="append", required=True)
    d.add_argument("--depth", type=int, default=4)
    d.add_argument("--top", type=int, default=40)
    d.add_argument("--json")
    d.set_defaults(fn=cmd_discover)
    i = sub.add_parser("identity")
    i.add_argument("--discover", required=True, help="JSON written by `discover --json`")
    i.add_argument("--pick", required=True, help="comma-separated row numbers from the discover table")
    i.add_argument("--with-names", action="store_true", help="also match on author names (riskier: common names)")
    i.add_argument("--out", required=True)
    i.set_defaults(fn=cmd_identity)
    s = sub.add_parser("scan")
    s.add_argument("--root", action="append", required=True,
                   help="repeatable; each is a repo OR a parent folder holding many repos")
    s.add_argument("--identity", required=True, help='JSON file {"emails": [...], "names": [...]}')
    s.add_argument("--out", required=True)
    s.add_argument("--since", help="YYYY-MM-DD or 'all' (default: last --months months)")
    s.add_argument("--months", type=int, default=C.DEFAULT_MONTHS, help="default window when --since is omitted (15)")
    s.add_argument("--until")
    s.add_argument("--depth", type=int, default=4)
    s.add_argument("--bulk-lines", type=int, default=5000)
    s.add_argument("--bulk-files", type=int, default=300)
    s.add_argument("--fetch", action="store_true", help="git fetch --all --prune in every repo first (network)")
    s.add_argument("--blame", action="store_true", help="slow: share of current code still authored by me")
    s.add_argument("--blame-max-files", type=int, default=400)
    s.set_defaults(fn=cmd_scan)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
