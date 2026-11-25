#!/usr/bin/env python3
"""Hunt for SCALE numbers that live in text: data volume, index/shard/field counts, infra size, throughput, tests.

Scans tracked text files (md, txt, json, yaml, py, sh, tf, Jenkinsfile ...) for "<number> <unit>" and "unit: number"
patterns and lists them with file:line and the sentence, grouped by kind. Output is CANDIDATES: the LLM reads the
context and decides which number is a real scale fact (production vs example vs test fixture) - see
references/scale-dimensions.md. It also counts fields in JSON mapping/schema files.

  python scale_hunt.py --root <repo> --out RAW [--exclude-prefix docs/versions/] [--paths "scripts/*" ...]

Files that came from bulk imports (RAW/git/<repo>.bulk_paths.txt) are skipped automatically.
Writes RAW/scale_hunt.json.
"""
import argparse
import fnmatch
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import scan_git as G  # noqa: E402

TEXT_EXT = {".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".py", ".sh", ".bash", ".tf", ".tfvars", ".tpl", ".go",
            ".java", ".js", ".ts", ".sql", ".toml", ".ini", ".properties", ".cfg", ".conf", ".ps1"}
NUM = r"(?P<num>\d{1,3}(?:[.,_]\d{3})+|\d+(?:[.,]\d+)?)"
MULT = r"(?P<mult>\s?(?:k|K|M|B|m|million|billion|triệu|nghìn|tỷ)\b)?"
GROUPS = {
    "documents/records": r"(?:docs?|documents?|records?|rows?|entries|bản ghi|tài liệu)(?![\w/])",
    "indices": r"(?:indices|indexes|indexs)\b",
    "shards/replicas": r"(?:shards?|replicas?)\b",
    "fields/columns": r"(?:fields?|columns?|properties|trường)\b",
    "nodes/hosts": r"(?:nodes?|VMs?|instances?|pods?|clusters?|namespaces?|helm (?:modules?|releases?|charts?)|"
                   r"microservices?|services?|environments?|servers?|brokers?)\b",
    "compute": r"(?:v?CPUs?|cores?)\b",
    "data size": r"(?:[KMGT]i?B)\b",
    "throughput": r"(?:docs?|req|requests?|ops|records?|msgs?)\s?/\s?(?:s|sec|second)\b|(?:docs?|records?)/s\b",
    "tests/scenarios": r"(?:tests?|test cases?|cases?|scenarios?|assertions?|checks?|mutations?)\b",
    "api surface": r"(?:endpoints?|routes?|handlers?|APIs?)\b",
    "users/tenants": r"(?:users?|customers?|tenants?|accounts?)\b",
}
UNIT_RX = {g: re.compile(NUM + MULT + r"\s?(?P<unit>" + u + ")") for g, u in GROUPS.items()}
KV_RX = re.compile(r"""["']?(?P<key>doc_?count|docs?_count|num_?docs|total_?docs|documents?|records?|number_of_shards|number_of_replicas|
                       shards|replicas|index_?count|num_?indices|nodes?_?count|node_?count|replica_?count)["']?\s*[:=]\s*(?P<num>\d[\d_,]*)""",
                   re.I | re.X)
MULT_VAL = {"k": 1e3, "nghìn": 1e3, "m": 1e6, "million": 1e6, "triệu": 1e6, "b": 1e9, "billion": 1e9, "tỷ": 1e9}


def to_number(raw):
    raw = raw.strip()
    if re.fullmatch(r"\d{1,3}(?:[.,_]\d{3})+", raw):          # 8.000.000 / 412,873
        return float(re.sub(r"[.,_]", "", raw))
    return float(raw.replace(",", ".").replace("_", ""))      # 1,5 -> 1.5


def mapping_fields(obj):
    """Count leaf fields under any "properties" in an ES-style mapping."""
    leaves = objects = 0

    def walk(node):
        nonlocal leaves, objects
        props = node.get("properties") if isinstance(node, dict) else None
        if not isinstance(props, dict):
            return
        for child in props.values():
            if isinstance(child, dict) and isinstance(child.get("properties"), dict):
                objects += 1
                walk(child)
            else:
                leaves += 1
                if isinstance(child, dict) and isinstance(child.get("fields"), dict):
                    leaves += len(child["fields"])
    if isinstance(obj, dict):
        walk(obj.get("mappings", obj) if "mappings" in obj else obj)
        if not (leaves or objects):
            for v in obj.values():  # {"index-name": {"mappings": {...}}}
                if isinstance(v, dict) and "mappings" in v:
                    walk(v["mappings"])
    return leaves, objects


def main():
    C.setup_stdio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exclude-prefix", action="append", default=[])
    ap.add_argument("--paths", action="append", default=[], help="only scan paths matching these globs")
    ap.add_argument("--per-group", type=int, default=25)
    ap.add_argument("--depth", type=int, default=4)
    a = ap.parse_args()
    repos = []
    for root in a.root:
        repos += [r for r in C.find_repos(root, a.depth) if r not in repos]
    ids = G.repo_ids(repos)
    found = defaultdict(list)
    mappings = []
    scanned = 0
    for repo in repos:
        rid = ids[repo]
        bulk = set()
        bf = os.path.join(a.out, "git", rid + ".bulk_paths.txt")
        if os.path.isfile(bf):
            with open(bf, "r", encoding="utf-8") as fh:
                bulk = {ln for ln in fh.read().split("\n") if ln}
        for rel in C.list_files(repo, True):
            ext = os.path.splitext(rel)[1].lower()
            base = rel.rsplit("/", 1)[-1]
            if rel in bulk or any(rel.startswith(p) for p in a.exclude_prefix) or C.classify(rel)[1] == "excluded":
                continue
            if ext not in TEXT_EXT and "Jenkinsfile" not in base:
                continue
            if a.paths and not any(fnmatch.fnmatch(rel, g) for g in a.paths):
                continue
            full = os.path.join(repo, rel)
            try:
                if os.path.getsize(full) > 1_500_000 or ".tfstate" in rel:
                    continue
                with open(full, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            scanned += 1
            if ext == ".json":
                try:
                    lf, ob = mapping_fields(json.loads(text))
                    if lf:
                        mappings.append({"repo": rid, "file": rel, "leaf_fields": lf, "object_fields": ob})
                except ValueError:
                    pass
            for n, line in enumerate(text.splitlines(), 1):
                if len(line) > 600 or not re.search(r"\d", line):
                    continue
                snippet = re.sub(r"\s+", " ", line).strip()[:200]
                for group, rx in UNIT_RX.items():
                    for m in rx.finditer(line):
                        try:
                            val = to_number(m.group("num"))
                        except ValueError:
                            continue
                        mult = (m.group("mult") or "").strip().lower()
                        val *= MULT_VAL.get(mult, 1)
                        found[group].append({"value": val, "as_written": m.group(0).strip(), "repo": rid,
                                             "file": rel, "line": n, "text": snippet})
                for m in KV_RX.finditer(line):
                    try:
                        val = float(m.group("num").replace(",", "").replace("_", ""))
                    except ValueError:
                        continue
                    found["key: value in configs"].append({"value": val, "as_written": m.group(0).strip(), "repo": rid,
                                                           "file": rel, "line": n, "text": snippet})
    result = {"files_scanned": scanned, "mapping_files": sorted(mappings, key=lambda m: -m["leaf_fields"]), "groups": {}}
    for group, items in found.items():
        seen, picked = set(), []
        for it in sorted(items, key=lambda i: -i["value"]):
            key = (it["file"], it["value"])
            if key in seen:
                continue
            seen.add(key)
            picked.append(it)
        result["groups"][group] = {"total_mentions": len(items), "files": len({i["file"] for i in items}),
                                   "top_by_value": picked[: a.per_group]}
    C.write_json(os.path.join(a.out, "scale_hunt.json"), result)
    print(f"files_scanned={scanned}; mapping files with fields={len(mappings)}")
    for g, v in result["groups"].items():
        print(f"  {g:26} mentions={v['total_mentions']:>4} files={v['files']:>3}")


if __name__ == "__main__":
    main()
