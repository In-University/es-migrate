#!/usr/bin/env python3
"""Measure the SCALE of projects: size, stack, infra, tests, team, age.

For every git repo found under each --root it uses `git ls-files` (so .gitignore, node_modules, dist,
target, .terraform are never counted). A --root that holds no repo is walked as a plain folder.

  python scan_folder.py --root D:/Workspace --root D:/Other/project --out OUT
  -> OUT/folders.json
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

MANIFESTS = ("package.json", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts", "requirements.txt",
             "pyproject.toml", "Cargo.toml", "composer.json", "Gemfile", "Chart.yaml", "setup.py")
ROUTE_RE = re.compile(
    r"@(Get|Post|Put|Delete|Patch|Request)Mapping\b|@(app|router|bp|blueprint)\.(get|post|put|delete|patch|route)\(|"
    r"\b(app|router|r|e|g)\.(GET|POST|PUT|DELETE|PATCH)\(|\b(app|router)\.(get|post|put|delete|patch)\(\s*['\"/]|"
    r"\bhttp\.HandleFunc\(|\b(router|mux|r)\.(Get|Post|Put|Delete|Patch|HandleFunc)\(")
ROUTE_EXT = {".java", ".kt", ".py", ".js", ".ts", ".go", ".cs"}
CI_PATTERNS = (".github/workflows/", ".gitlab-ci.yml", "jenkinsfile", "azure-pipelines", "bitbucket-pipelines",
               ".circleci/", ".drone.yml", "cloudbuild.yaml")


def read_text(path, limit=300_000):
    try:
        if os.path.getsize(path) > limit:
            return ""
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def dependency_counts(root, files):
    deps = Counter()
    for rel in files:
        base = rel.rsplit("/", 1)[-1]
        if C.EXCLUDED_DIR_RE.search(rel):
            continue
        if base == "package.json":
            try:
                j = json.loads(read_text(os.path.join(root, rel)) or "{}")
                deps["npm"] += len(j.get("dependencies", {})) + len(j.get("devDependencies", {}))
            except ValueError:
                pass
        elif base == "go.mod":
            t = read_text(os.path.join(root, rel))
            deps["go"] += len(re.findall(r"^(?:require\s+|\s+)[\w.\-/~]+\.[\w.\-/~]+\s+v[\w.\-+]+", t, re.M))
        elif base == "requirements.txt":
            deps["pip"] += sum(1 for ln in read_text(os.path.join(root, rel)).splitlines()
                               if ln.strip() and not ln.lstrip().startswith(("#", "-")))
        elif base == "pom.xml":
            deps["maven"] += read_text(os.path.join(root, rel)).count("<dependency>")
        elif base in ("build.gradle", "build.gradle.kts"):
            deps["gradle"] += len(re.findall(r"^\s*(implementation|api|compileOnly|runtimeOnly|testImplementation)\b",
                                             read_text(os.path.join(root, rel)), re.M))
    return dict(deps)


def infra_signals(root, files):
    low = [f.lower() for f in files]
    sig = {}
    docker_dirs = {os.path.dirname(f) for f in files if f.rsplit("/", 1)[-1].lower().startswith("dockerfile")}
    sig["dockerfiles"] = sum(1 for f in files if f.rsplit("/", 1)[-1].lower().startswith("dockerfile"))
    sig["compose_files"] = sum(1 for f in low if re.search(r"(^|/)(docker-)?compose[^/]*\.ya?ml$", f))
    sig["helm_charts"] = sum(1 for f in files if f.endswith("Chart.yaml"))
    sig["terraform_files"] = sum(1 for f in low if f.endswith(".tf"))
    tf_res = tf_mod = 0
    k8s_kinds = Counter()
    routes = 0
    sql_migrations = sum(1 for f in low if f.endswith(".sql") and re.search(r"migrat|flyway|liquibase|/db/", f))
    scanned_yaml = scanned_code = 0
    for rel in files:
        ext = os.path.splitext(rel)[1].lower()
        if C.classify(rel)[1] == "excluded":
            continue
        if ext == ".tf":
            t = read_text(os.path.join(root, rel))
            tf_res += len(re.findall(r'^\s*resource\s+"', t, re.M))
            tf_mod += len(re.findall(r'^\s*module\s+"', t, re.M))
        elif ext in (".yaml", ".yml") and scanned_yaml < 3000 and "/templates/" not in rel:
            scanned_yaml += 1
            t = read_text(os.path.join(root, rel), 200_000)
            if "apiVersion:" in t:
                for m in re.finditer(r"^kind:\s*(\w+)", t, re.M):
                    k8s_kinds[m.group(1)] += 1
        elif ext in ROUTE_EXT and scanned_code < 4000 and C.classify(rel)[1] == "code":
            scanned_code += 1
            routes += len(ROUTE_RE.findall(read_text(os.path.join(root, rel), 200_000)))
    sig["terraform_resources"] = tf_res
    sig["terraform_modules_used"] = tf_mod
    sig["k8s_manifest_kinds"] = dict(k8s_kinds.most_common(12))
    sig["ci_pipeline_files"] = sum(1 for f in low if any(p in f for p in CI_PATTERNS))
    sig["sql_migration_files"] = sql_migrations
    sig["proto_files"] = sum(1 for f in low if f.endswith(".proto"))
    sig["openapi_specs"] = sum(1 for f in low if re.search(r"(openapi|swagger)[^/]*\.(ya?ml|json)$", f))
    sig["http_routes_approx"] = routes
    sig["deployable_units_by_dockerfile"] = len(docker_dirs)
    return sig


def git_meta(repo, ident=None):
    meta = {}
    n = C.git(repo, "rev-list", "--count", "--branches", "--remotes", "--tags").strip()
    meta["commits_all_authors"] = int(n) if n.isdigit() else None
    dates = C.git(repo, "log", "--branches", "--remotes", "--tags", "--format=%as").split()
    meta["first_commit"], meta["last_commit"] = (min(dates), max(dates)) if dates else (None, None)
    people_all, people_12m = set(), set()
    cutoff = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    for ln in C.git(repo, "log", "--branches", "--remotes", "--tags", "--no-merges",
                    "--format=%aN\x1f%aE\x1f%as").splitlines():
        p = ln.split("\x1f")
        if len(p) == 3 and not C.is_bot(p[0], p[1]):
            who = "<me>" if ident and ident.matches(p[0], p[1]) else p[1].lower()  # my e-mails = one person
            people_all.add(who)
            if p[2] >= cutoff:
                people_12m.add(who)
    meta["contributors_all_time"] = len(people_all)
    meta["contributors_last_12m"] = len(people_12m)
    meta["remote"] = C.clean_remote(C.git(repo, "config", "--get", "remote.origin.url"))
    meta["branches_remote"] = len([b for b in C.git(repo, "branch", "-r").splitlines() if "->" not in b])
    meta["tags"] = len(C.git(repo, "tag").split())
    return meta


def scan_project(path, is_repo, exclude=frozenset(), ident=None):
    files = [f for f in C.list_files(path, is_repo) if f not in exclude]
    snap = C.snapshot(path, files)
    manifests = Counter()
    for rel in files:
        base = rel.rsplit("/", 1)[-1]
        if base in MANIFESTS and not C.EXCLUDED_DIR_RE.search(rel):
            manifests[base] += 1
    test_loc = snap["loc_by_category"].get("test", 0)
    code_only = snap["loc_by_category"].get("code", 0)
    out = {
        "name": os.path.basename(path.rstrip("\\/")), "path": path, "is_git_repo": is_repo,
        "tracked_files": len(files), "files_excluded_as_bulk_imports": len(exclude), "snapshot": snap,
        "test_to_code_ratio_pct": round(100 * test_loc / (test_loc + code_only), 1) if (test_loc + code_only) else None,
        "test_files": snap["files_by_category"].get("test", 0),
        "docs_markdown_files": sum(1 for f in files if f.lower().endswith((".md", ".mdx", ".rst", ".adoc"))),
        "manifests": dict(manifests), "dependencies": dependency_counts(path, files),
        "infra": infra_signals(path, files),
    }
    if is_repo:
        out["git"] = git_meta(path, ident)
    return out


def main():
    C.setup_stdio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", action="append", required=True,
                    help="repeatable; a repo, a parent folder with many repos, or a plain folder")
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--only-mine", metavar="GIT_SUMMARY_JSON",
                    help="path of git/summary.json: keep only repos with my commits in the window and skip "
                         "duplicate clones (plain non-git folders given as --root are kept)")
    a = ap.parse_args()
    mine = ident = None
    if a.only_mine:
        data = C.read_json(a.only_mine)
        mine = {os.path.normcase(os.path.abspath(r["path"])): r for r in data["repos"]}
        ident = C.Identity(data["identity"]["emails"], data["identity"]["names"])
    projects, seen, skipped = [], set(), []
    note_win = None
    if a.only_mine:
        note_win = f"window {data.get('since') or 'all time'} -> {data.get('until') or 'now'}"
    for root in a.root:
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            C.log("skip (not a directory): " + root)
            continue
        repos = C.find_repos(root, a.depth)
        targets = [(r, True) for r in repos] if repos else [(root, False)]
        for path, is_repo in targets:
            if path in seen:
                continue
            seen.add(path)
            if mine is not None and is_repo:
                entry = mine.get(os.path.normcase(os.path.abspath(path)))
                if entry is None:
                    skipped.append({"path": path, "reason": "no commits by me in the window (not my work, or outside it)"})
                    continue
                if entry.get("duplicate_of"):
                    skipped.append({"path": path, "reason": "duplicate clone of " + entry["duplicate_of"]})
                    continue
            C.log(f"[{len(projects) + 1}] {path}")
            exclude = frozenset()
            if mine is not None and is_repo:
                # files that arrived through bulk commits (archives/imports) are not the user's code
                rid = mine[os.path.normcase(os.path.abspath(path))]["repo"]
                bp = os.path.join(os.path.dirname(os.path.abspath(a.only_mine)), rid + ".bulk_paths.txt")
                if os.path.isfile(bp):
                    with open(bp, "r", encoding="utf-8") as fh:
                        exclude = frozenset(ln for ln in fh.read().split("\n") if ln)
            projects.append(scan_project(path, is_repo, exclude, ident))
    tot = Counter()
    lang = Counter()
    for p in projects:
        tot["tracked_files"] += p["tracked_files"]
        for cat, n in p["snapshot"]["loc_by_category"].items():
            tot["loc_" + cat] += n
        for lg, v in p["snapshot"]["loc_by_language"].items():
            if v["category"] in ("code", "test", "config"):
                lang[lg] += v["loc"]
        tot["http_routes_approx"] += p["infra"]["http_routes_approx"]
        tot["terraform_resources"] += p["infra"]["terraform_resources"]
        tot["dockerfiles"] += p["infra"]["dockerfiles"]
    out = {"filter": ("only repos with my commits in the git scan (" + note_win + "), duplicates removed") if mine is not None
                     else "none: every repo found under --root is included, whoever wrote it",
           "skipped": skipped,
           "projects": sorted(projects, key=lambda p: -p["snapshot"]["code_loc"]),
           "totals_current_snapshot": dict(tot), "languages_loc": dict(lang.most_common(15)),
           "note": "Snapshot of what exists NOW in these folders, regardless of who wrote it. "
                   "Use git/summary.json for personal contribution."}
    C.write_json(os.path.join(a.out, "folders.json"), out)
    if skipped:
        C.log(f"skipped {len(skipped)} repo(s) by --only-mine (listed in folders.json)")
    print(f"projects={len(projects)} total_code_loc={tot['loc_code'] + tot['loc_test']} "
          f"-> {os.path.join(a.out, 'folders.json')}")


if __name__ == "__main__":
    main()
