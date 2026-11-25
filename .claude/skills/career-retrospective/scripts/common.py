"""Shared helpers for the career-retrospective scripts (stdlib only, Python >= 3.8).

Windows notes: every subprocess is decoded as UTF-8 (Vietnamese commit messages),
git runs with core.quotepath=off, and stdout/stderr are reconfigured to UTF-8.
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter

# ----------------------------------------------------------------------------- io


def setup_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def write_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, sort_keys=False)


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ----------------------------------------------------------------------------- time window

DEFAULT_MONTHS = 15  # tenure at the employer being retrospected


def months_ago(months, today=None):
    from datetime import date
    t = today or date.today()
    y, m = divmod(t.year * 12 + (t.month - 1) - months, 12)
    return date(y, m + 1, min(t.day, 28)).isoformat()


def resolve_since(since, months=DEFAULT_MONTHS):
    """None -> last `months` months; 'all'/'none' -> no limit; otherwise the given YYYY-MM-DD."""
    if since is None:
        return months_ago(months)
    return None if since.lower() in ("all", "none") else since


# ----------------------------------------------------------------------------- git


def git(repo, *args, timeout=600):
    """Run git in `repo`, return stdout as str ('' on failure)."""
    cmd = ["git", "-c", "core.quotepath=off", "-C", repo] + list(args)
    try:
        res = subprocess.run(cmd, capture_output=True, encoding="utf-8",
                             errors="replace", timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return res.stdout if res.returncode == 0 else ""


SKIP_WALK_DIRS = {"node_modules", ".terraform", "vendor", "dist", "build", "target",
                  "__pycache__", ".venv", "venv", ".gradle", ".idea", ".vscode", ".cache"}


def find_repos(root, max_depth=4):
    """Return git working-tree roots at or below `root` (does not descend into a repo)."""
    root = os.path.abspath(root)
    if os.path.exists(os.path.join(root, ".git")):
        return [root]
    found = []
    base_depth = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, _files in os.walk(root):
        if os.path.exists(os.path.join(dirpath, ".git")):
            found.append(dirpath)
            dirnames[:] = []
            continue
        if dirpath.rstrip(os.sep).count(os.sep) - base_depth >= max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_WALK_DIRS and not d.startswith(".")]
    return sorted(found)


BOT_RE = re.compile(r"\[bot\]|dependabot|renovate|github-actions|copilot-swe-agent|^bot$|-bot@", re.I)


def is_bot(name, email):
    return bool(BOT_RE.search(name or "") or BOT_RE.search(email or ""))


def clean_remote(url):
    """Strip credentials from a remote URL before it is stored anywhere."""
    return re.sub(r"//[^/@]+@", "//", url or "").strip()


class Identity:
    """Who counts as 'me': exact email and/or name matches (case-insensitive)."""

    def __init__(self, emails=(), names=()):
        self.emails = {e.strip().lower() for e in emails if e and e.strip()}
        self.names = {n.strip().lower() for n in names if n and n.strip()}

    @classmethod
    def load(cls, path):
        data = read_json(path)
        return cls(data.get("emails", []), data.get("names", []))

    def matches(self, name, email):
        return (email or "").strip().lower() in self.emails or (name or "").strip().lower() in self.names

    def git_author_args(self):
        # prefilter only; exact matching happens in Python
        return ["--fixed-strings", "--regexp-ignore-case"] + \
               ["--author=" + v for v in sorted(self.emails | self.names)]

    def to_dict(self):
        return {"emails": sorted(self.emails), "names": sorted(self.names)}


# ----------------------------------------------------------------------------- file classification

CODE = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go", ".java": "Java", ".kt": "Kotlin",
    ".kts": "Kotlin", ".scala": "Scala", ".rs": "Rust", ".c": "C", ".h": "C/C++ header", ".cc": "C++",
    ".cpp": "C++", ".hpp": "C++", ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".ps1": "PowerShell", ".bat": "Batch",
    ".sql": "SQL", ".lua": "Lua", ".r": "R", ".dart": "Dart", ".vue": "Vue", ".svelte": "Svelte",
    ".groovy": "Groovy", ".gradle": "Gradle", ".html": "HTML", ".htm": "HTML", ".css": "CSS",
    ".scss": "CSS", ".sass": "CSS", ".less": "CSS", ".ex": "Elixir", ".exs": "Elixir", ".pl": "Perl",
    ".m": "Objective-C", ".vb": "VB.NET"
}
CONFIG = {
    ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML", ".tf": "Terraform", ".tfvars": "Terraform",
    ".hcl": "HCL", ".ini": "INI", ".properties": "Properties", ".xml": "XML", ".proto": "Protobuf",
    ".tpl": "Helm/Template", ".cfg": "Config", ".conf": "Config", ".env": "Config",
    ".jinja": "Template", ".j2": "Template", ".mustache": "Template",
}
DOCS = {".md": "Markdown", ".mdx": "Markdown", ".rst": "reStructuredText", ".adoc": "AsciiDoc", ".txt": "Text"}
DATA = {".json": "JSON", ".csv": "CSV", ".tsv": "TSV", ".ndjson": "NDJSON", ".jsonl": "NDJSON", ".ipynb": "Notebook"}
SPECIAL_NAMES = {"dockerfile": ("Dockerfile", "config"), "makefile": ("Makefile", "config"),
                 "jenkinsfile": ("Jenkinsfile", "config"), "vagrantfile": ("Vagrant", "config"),
                 "rakefile": ("Ruby", "code"), "gemfile": ("Ruby", "config")}
EXCLUDED_DIR_RE = re.compile(
    r"(^|/)(node_modules|vendor|third_party|dist|build|target|\.terraform|\.git|\.idea|\.vscode|"
    r"__pycache__|\.venv|venv|site-packages|bower_components|\.next|\.nuxt|coverage|__snapshots__|\.gradle)(/|$)")
EXCLUDED_FILE_RE = re.compile(
    r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|go\.sum|poetry\.lock|Cargo\.lock|Gemfile\.lock|"
    r"composer\.lock|Pipfile\.lock|gradle\.lockfile|\.terraform\.lock\.hcl)$|"
    r"\.(min\.js|min\.css|map|lock|svg|png|jpe?g|gif|ico|webp|pdf|zip|gz|tgz|jar|war|class|so|dll|exe|bin|"
    r"woff2?|ttf|eot|mp4|mov|pyc|snap)$|"
    r"(\.pb\.go|_pb2\.py|_pb2_grpc\.py|\.generated\.\w+|_generated\.\w+|\.g\.dart|\.designer\.cs)$", re.I)
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec|specs|e2e|testing)(/|$)|(^|/)test_[^/]+$|_test\.\w+$|"
                     r"\.(test|spec)\.\w+$|Tests?\.(java|kt|cs|scala|php)$", re.I)


def classify(path):
    """Return (language, category). category: code|test|config|docs|data|other|excluded."""
    p = path.replace("\\", "/")
    if EXCLUDED_DIR_RE.search(p) or EXCLUDED_FILE_RE.search(p):
        return ("-", "excluded")
    base = p.rsplit("/", 1)[-1]
    special = SPECIAL_NAMES.get(base.lower())
    if special:
        return special
    ext = os.path.splitext(base)[1].lower()
    if ext in CODE:
        return (CODE[ext], "test" if TEST_RE.search(p) else "code")
    if ext in CONFIG:
        return (CONFIG[ext], "config")
    if ext in DOCS:
        return (DOCS[ext], "docs")
    if ext in DATA:
        return (DATA[ext], "data")
    return (ext or "(none)", "other")


_RENAME_BRACE = re.compile(r"\{([^{}]*) => ([^{}]*)\}")


def normalize_numstat_path(p):
    """`src/{old => new}/x.py` and `old => new` -> the new path."""
    if " => " not in p:
        return p
    if "{" in p:
        p = _RENAME_BRACE.sub(lambda m: m.group(2), p)
        return re.sub(r"/{2,}", "/", p)
    return p.split(" => ", 1)[1]


def module_of(path):
    parts = path.split("/")
    if len(parts) <= 1:
        return "(root)"
    return "/".join(parts[:2]) if len(parts) > 2 else parts[0]


# ----------------------------------------------------------------------------- snapshot (current state of a tree)


def count_lines(abs_path, max_bytes=2_000_000):
    """(lines, nonblank_lines) or None for binary / unreadable / oversized files."""
    try:
        if os.path.getsize(abs_path) > max_bytes:
            return None
        with open(abs_path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    if b"\0" in data[:8000]:
        return None
    lines = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
    nonblank = sum(1 for ln in data.split(b"\n") if ln.strip())
    return lines, nonblank


def list_files(root, is_repo):
    """Tracked files for a repo (respects .gitignore); filesystem walk for a plain folder."""
    if is_repo:
        out = git(root, "ls-files", "-z")
        return [f for f in out.split("\0") if f]
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_WALK_DIRS and d != ".git"]
        for fn in filenames:
            files.append(os.path.relpath(os.path.join(dirpath, fn), root).replace("\\", "/"))
    return files


def snapshot(root, files):
    """LOC by language/category over `files` (paths relative to root). Excluded files are skipped."""
    by_lang = {}
    by_cat = Counter()
    n_files = Counter()
    for rel in files:
        lang, cat = classify(rel)
        if cat in ("excluded", "other"):
            continue
        counted = count_lines(os.path.join(root, rel))
        if counted is None:
            continue
        lines, nonblank = counted
        by_cat[cat] += nonblank
        n_files[cat] += 1
        slot = by_lang.setdefault(lang, {"category": cat, "files": 0, "loc": 0})
        slot["files"] += 1
        slot["loc"] += nonblank
    return {
        "loc_by_category": dict(by_cat),
        "files_by_category": dict(n_files),
        "loc_by_language": dict(sorted(by_lang.items(), key=lambda kv: -kv[1]["loc"])),
        "code_loc": by_cat["code"] + by_cat["test"],
        "note": "loc = non-blank lines; excludes lockfiles, vendored/generated/minified files, binaries and images",
    }
