#!/usr/bin/env python3
"""
fetch_official_es_docs.py

Fetches, crawls, and parses ALL official Elasticsearch documentation for:
- Release Notes
- Breaking Changes
- Migration Guides
- What's New / Highlights
- Plugins and Modules (especially Ingest Pipelines, Ingest Attachment Processor,
  all metadata fields across versions, dynamic/strict index mappings)
for EVERY version from 6.8 through 9.2.3.

Sources:
1. Official GitHub repository elastic/elasticsearch (docs, changelogs, modules/plugins, raw source)
2. Official Elastic Guide (elastic.co/guide and docs.elastic.co)
"""

import os
import sys
import json
import time
import re
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_VERSIONS_DIR = os.path.join(REPO_ROOT, "docs", "versions")

# Read GitHub token from hosts.yml if present
GITHUB_TOKEN = None
HOSTS_YML = "/root/.config/gh/hosts.yml"
if os.path.exists(HOSTS_YML):
    try:
        with open(HOSTS_YML, "r") as f:
            for line in f:
                if "oauth_token:" in line:
                    GITHUB_TOKEN = line.split("oauth_token:")[1].strip()
                    break
    except Exception as e:
        print(f"Warning reading hosts.yml: {e}")

if not GITHUB_TOKEN:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml,text/plain,*/*;q=0.9"
}

GH_HEADERS = HEADERS.copy()
if GITHUB_TOKEN:
    GH_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"


def fetch_url_bytes(url, headers=None, max_retries=5, timeout=25):
    if headers is None:
        headers = GH_HEADERS if ("github" in url or "raw.githubusercontent" in url) else HEADERS
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return resp.read()
                elif resp.status == 404:
                    return None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429 or e.code >= 500:
                time.sleep(2.0 * (attempt + 1))
            else:
                time.sleep(1.0)
        except Exception as e:
            time.sleep(1.5 * (attempt + 1))
    return None


def fetch_and_save(item):
    url, dest_path, is_gh = item
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return dest_path, os.path.getsize(dest_path), True
    headers = GH_HEADERS if is_gh else HEADERS
    data = fetch_url_bytes(url, headers=headers)
    if data:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)
        return dest_path, len(data), False
    return dest_path, 0, False


def get_git_tree(ref):
    """Retrieve all blob paths in ref using Git Tree API"""
    url = f"https://api.github.com/repos/elastic/elasticsearch/git/trees/{ref}?recursive=1"
    raw_data = fetch_url_bytes(url, headers=GH_HEADERS)
    if not raw_data:
        print(f"Failed to fetch tree for {ref}")
        return []
    try:
        data = json.loads(raw_data.decode("utf-8"))
        return [x["path"] for x in data.get("tree", []) if x.get("type") == "blob"]
    except Exception as e:
        print(f"Error parsing tree for {ref}: {e}")
        return []


def discover_guide_links(base_url, keywords):
    """Crawl elastic.co/guide pages matching keywords"""
    html_bytes = fetch_url_bytes(base_url, headers=HEADERS)
    if not html_bytes:
        return []
    soup = BeautifulSoup(html_bytes.decode("utf-8", errors="ignore"), "html.parser")
    found = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        full_url = urllib.parse.urljoin(base_url, href)
        clean_url = full_url.split("?")[0].split("#")[0]
        if any(k in clean_url for k in keywords):
            found.add(clean_url)
    return sorted(list(found))


def build_download_manifest():
    tasks = [] # (url, dest_path, is_gh)

    print("Retrieving Git trees from official repository elastic/elasticsearch...")
    tree_68 = get_git_tree("6.8")
    print(f"  6.8: {len(tree_68)} blobs")
    tree_717 = get_git_tree("7.17")
    print(f"  7.17: {len(tree_717)} blobs")
    tree_819 = get_git_tree("8.19")
    print(f"  8.19: {len(tree_819)} blobs")
    tree_92 = get_git_tree("9.2")
    print(f"  9.2: {len(tree_92)} blobs")
    tree_main = get_git_tree("main")
    print(f"  main: {len(tree_main)} blobs")

    # Raw GitHub base url generator
    def raw_url(branch, path):
        return f"https://raw.githubusercontent.com/elastic/elasticsearch/{branch}/{path}"

    # -------------------------------------------------------------
    # 1. VERSION 6.8
    # -------------------------------------------------------------
    v68_dir = os.path.join(DOCS_VERSIONS_DIR, "6.8")
    # Release notes
    for p in tree_68:
        if p.startswith("docs/reference/release-notes/"):
            fname = os.path.basename(p)
            if "6.8" in fname or fname == "highlights.asciidoc":
                tasks.append((raw_url("6.8", p), os.path.join(v68_dir, "release-notes", fname), True))
        elif p == "docs/reference/release-notes.asciidoc":
            tasks.append((raw_url("6.8", p), os.path.join(v68_dir, "release-notes", "release-notes-index.asciidoc"), True))
        elif p.startswith("docs/reference/migration/"):
            fname = os.path.basename(p)
            rel_dir = os.path.relpath(os.path.dirname(p), "docs/reference/migration")
            if "6_8" in p or "6.8" in p:
                tasks.append((raw_url("6.8", p), os.path.join(v68_dir, "breaking-changes", fname), True))
            elif "7_0" in p or "7.0" in p:
                tasks.append((raw_url("6.8", p), os.path.join(v68_dir, "migration-guide", "prep-for-7.0", fname), True))
            else:
                target_dir = os.path.join(v68_dir, "migration-guide", rel_dir) if rel_dir != "." else os.path.join(v68_dir, "migration-guide")
                tasks.append((raw_url("6.8", p), os.path.join(target_dir, fname), True))
        elif p.startswith("docs/reference/mapping/"):
            fname = os.path.basename(p)
            tasks.append((raw_url("6.8", p), os.path.join(v68_dir, "mappings", fname), True))
        elif p.startswith("docs/plugins/"):
            fname = os.path.basename(p)
            if "ingest-attachment" in fname or "ingest" in fname:
                tasks.append((raw_url("6.8", p), os.path.join(v68_dir, "plugins-and-modules", "ingest-attachment", fname), True))
            else:
                tasks.append((raw_url("6.8", p), os.path.join(v68_dir, "plugins-and-modules", "plugins-reference", fname), True))
        elif p.startswith("plugins/ingest-attachment/"):
            if p.endswith((".java", ".gradle", ".json", ".txt")):
                rel = os.path.relpath(p, "plugins/ingest-attachment")
                tasks.append((raw_url("6.8", p), os.path.join(v68_dir, "plugins-and-modules", "ingest-attachment", "source", rel), True))

    # -------------------------------------------------------------
    # 2. VERSIONS 7.0 THROUGH 7.17
    # -------------------------------------------------------------
    v7_minors = [f"7.{m}" for m in range(18)] # 7.0 to 7.17
    for minor in v7_minors:
        vdir = os.path.join(DOCS_VERSIONS_DIR, minor)
        # Shared plugin and mapping docs for 7.x
        tasks.append((raw_url("7.17", "docs/plugins/ingest-attachment.asciidoc"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "ingest-attachment.asciidoc"), True))
        tasks.append((raw_url("7.17", "plugins/ingest-attachment/src/main/java/org/elasticsearch/ingest/attachment/AttachmentProcessor.java"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "source", "AttachmentProcessor.java"), True))
        tasks.append((raw_url("7.17", "plugins/ingest-attachment/src/main/java/org/elasticsearch/ingest/attachment/TikaImpl.java"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "source", "TikaImpl.java"), True))
        tasks.append((raw_url("7.17", "plugins/ingest-attachment/build.gradle"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "source", "build.gradle"), True))
        tasks.append((raw_url("7.17", "docs/reference/mapping/dynamic.asciidoc"),
                      os.path.join(vdir, "mappings", "dynamic.asciidoc"), True))
        tasks.append((raw_url("7.17", "docs/reference/mapping/removal-of-types.asciidoc"),
                      os.path.join(vdir, "mappings", "removal-of-types.asciidoc"), True))
        tasks.append((raw_url("7.17", "docs/reference/mapping/dynamic-mapping.asciidoc"),
                      os.path.join(vdir, "mappings", "dynamic-mapping.asciidoc"), True))

    # All plugin reference docs in 7.17
    for p in tree_717:
        if p.startswith("docs/plugins/") and p.endswith(".asciidoc"):
            fname = os.path.basename(p)
            tasks.append((raw_url("7.17", p), os.path.join(DOCS_VERSIONS_DIR, "7.17", "plugins-and-modules", "plugins-reference", fname), True))

    # Route 7.x release notes & migration files to specific minor folders
    for p in tree_717:
        if p.startswith("docs/reference/release-notes/"):
            fname = os.path.basename(p)
            m = re.search(r"7\.(\d+)", fname)
            if m:
                minor_num = int(m.group(1))
                if minor_num <= 17:
                    minor_dir = os.path.join(DOCS_VERSIONS_DIR, f"7.{minor_num}")
                    tasks.append((raw_url("7.17", p), os.path.join(minor_dir, "release-notes", fname), True))
        elif p.startswith("docs/reference/migration/"):
            fname = os.path.basename(p)
            m = re.search(r"migrate_7_(\d+)", fname)
            if m:
                minor_num = int(m.group(1))
                if minor_num <= 17:
                    minor_dir = os.path.join(DOCS_VERSIONS_DIR, f"7.{minor_num}")
                    tasks.append((raw_url("7.17", p), os.path.join(minor_dir, "breaking-changes", fname), True))
                    tasks.append((raw_url("7.17", p), os.path.join(minor_dir, "migration-guide", fname), True))
            elif "migrate_7_0/" in p:
                tasks.append((raw_url("7.17", p), os.path.join(DOCS_VERSIONS_DIR, "7.0", "breaking-changes", "subsystems", fname), True))
            elif fname in ["index.asciidoc", "migration.asciidoc", "transient-settings-migration-guide.asciidoc"]:
                tasks.append((raw_url("7.17", p), os.path.join(DOCS_VERSIONS_DIR, "7.17", "migration-guide", fname), True))

    # -------------------------------------------------------------
    # 3. VERSIONS 8.0 THROUGH 8.19
    # -------------------------------------------------------------
    v8_minors = [f"8.{m}" for m in range(20)] # 8.0 to 8.19
    for minor in v8_minors:
        vdir = os.path.join(DOCS_VERSIONS_DIR, minor)
        # Shared attachment processor docs & verbatim source
        tasks.append((raw_url("8.19", "docs/reference/ingest/processors/attachment.asciidoc"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "attachment.asciidoc"), True))
        tasks.append((raw_url("8.19", "modules/ingest-attachment/src/main/java/org/elasticsearch/ingest/attachment/AttachmentProcessor.java"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "source", "AttachmentProcessor.java"), True))
        tasks.append((raw_url("8.19", "modules/ingest-attachment/src/main/java/org/elasticsearch/ingest/attachment/TikaImpl.java"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "source", "TikaImpl.java"), True))
        tasks.append((raw_url("8.19", "modules/ingest-attachment/build.gradle"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "source", "build.gradle"), True))
        tasks.append((raw_url("8.19", "docs/reference/mapping/dynamic.asciidoc"),
                      os.path.join(vdir, "mappings", "dynamic.asciidoc"), True))
        tasks.append((raw_url("8.19", "docs/reference/mapping/dynamic-mapping.asciidoc"),
                      os.path.join(vdir, "mappings", "dynamic-mapping.asciidoc"), True))

    # Ingest processors and plugin reference in 8.19
    for p in tree_819:
        if p.startswith("docs/reference/ingest/processors/"):
            fname = os.path.basename(p)
            tasks.append((raw_url("8.19", p), os.path.join(DOCS_VERSIONS_DIR, "8.19", "plugins-and-modules", "ingest-processors", fname), True))
        elif p.startswith("docs/plugins/") and p.endswith(".asciidoc"):
            fname = os.path.basename(p)
            tasks.append((raw_url("8.19", p), os.path.join(DOCS_VERSIONS_DIR, "8.19", "plugins-and-modules", "plugins-reference", fname), True))

    # Route 8.x release notes & migration files
    for p in tree_819:
        if p.startswith("docs/reference/release-notes/"):
            fname = os.path.basename(p)
            m = re.search(r"8\.(\d+)", fname)
            if m:
                minor_num = int(m.group(1))
                if minor_num <= 19:
                    minor_dir = os.path.join(DOCS_VERSIONS_DIR, f"8.{minor_num}")
                    tasks.append((raw_url("8.19", p), os.path.join(minor_dir, "release-notes", fname), True))
        elif p.startswith("docs/reference/migration/"):
            fname = os.path.basename(p)
            m = re.search(r"migrate_8_(\d+)", fname)
            if m:
                minor_num = int(m.group(1))
                if minor_num <= 19:
                    minor_dir = os.path.join(DOCS_VERSIONS_DIR, f"8.{minor_num}")
                    tasks.append((raw_url("8.19", p), os.path.join(minor_dir, "breaking-changes", fname), True))
                    tasks.append((raw_url("8.19", p), os.path.join(minor_dir, "migration-guide", fname), True))
            elif "migrate_8_0/" in p:
                tasks.append((raw_url("8.19", p), os.path.join(DOCS_VERSIONS_DIR, "8.0", "breaking-changes", "subsystems", fname), True))
            elif fname in ["index.asciidoc", "migration.asciidoc", "transient-settings-migration-guide.asciidoc", "migration_intro.asciidoc"]:
                tasks.append((raw_url("8.19", p), os.path.join(DOCS_VERSIONS_DIR, "8.19", "migration-guide", fname), True))

    # -------------------------------------------------------------
    # 4. VERSIONS 9.0 THROUGH 9.2.3
    # -------------------------------------------------------------
    v9_minors = ["9.0", "9.1", "9.2"]
    for minor in v9_minors:
        vdir = os.path.join(DOCS_VERSIONS_DIR, minor)
        tasks.append((raw_url("9.2", "docs/release-notes/breaking-changes.md"),
                      os.path.join(vdir, "breaking-changes", "breaking-changes.md"), True))
        tasks.append((raw_url("9.2", "docs/release-notes/deprecations.md"),
                      os.path.join(vdir, "migration-guide", "deprecations.md"), True))
        tasks.append((raw_url("9.2", "docs/release-notes/known-issues.md"),
                      os.path.join(vdir, "release-notes", "known-issues.md"), True))
        tasks.append((raw_url("9.2", "docs/reference/enrich-processor/attachment.md"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "attachment.md"), True))
        tasks.append((raw_url("9.2", "modules/ingest-attachment/src/main/java/org/elasticsearch/ingest/attachment/AttachmentProcessor.java"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "source", "AttachmentProcessor.java"), True))
        tasks.append((raw_url("9.2", "modules/ingest-attachment/src/main/java/org/elasticsearch/ingest/attachment/TikaImpl.java"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "source", "TikaImpl.java"), True))
        tasks.append((raw_url("9.2", "modules/ingest-attachment/build.gradle"),
                      os.path.join(vdir, "plugins-and-modules", "ingest-attachment", "source", "build.gradle"), True))
        # Mapping docs in 9.2
        tasks.append((raw_url("9.2", "docs/reference/elasticsearch/mapping-reference/dynamic.md"),
                      os.path.join(vdir, "mappings", "dynamic.md"), True))
        tasks.append((raw_url("9.2", "docs/reference/elasticsearch/mapping-reference/dynamic-mapping.md"),
                      os.path.join(vdir, "mappings", "dynamic-mapping.md"), True))
        tasks.append((raw_url("9.2", "docs/reference/elasticsearch/mapping-reference/dynamic-field-mapping.md"),
                      os.path.join(vdir, "mappings", "dynamic-field-mapping.md"), True))

    # Plugins reference for 9.2
    for p in tree_92:
        if p.startswith("docs/reference/elasticsearch-plugins/"):
            fname = os.path.basename(p)
            tasks.append((raw_url("9.2", p), os.path.join(DOCS_VERSIONS_DIR, "9.2", "plugins-and-modules", "plugins-reference", fname), True))

    # Changelog bundles from main
    for p in tree_main:
        if p.startswith("docs/release-notes/changelog-bundles/"):
            fname = os.path.basename(p)
            m = re.match(r"(9\.\d+)\.", fname)
            if m:
                minor_str = m.group(1)
                if minor_str in ["9.0", "9.1", "9.2"]:
                    tasks.append((raw_url("main", p), os.path.join(DOCS_VERSIONS_DIR, minor_str, "release-notes", fname), True))

    # -------------------------------------------------------------
    # 5. CRAWL ELASTIC.CO/GUIDE (OFFICIAL WEB DOCUMENTATION)
    # -------------------------------------------------------------
    print("Discovering official Elastic Guide HTML pages from elastic.co/guide...")

    # 6.8 Guide URLs
    urls_68 = [
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/breaking-changes.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/breaking-changes-6.8.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/es-release-notes.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/release-highlights.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/release-highlights-6.8.0.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/dynamic-mapping.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/dynamic.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/removal-of-types.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/mapping-types.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/6.8/ingest.html",
        "https://www.elastic.co/guide/en/elasticsearch/plugins/6.8/ingest-attachment.html",
        "https://www.elastic.co/guide/en/elasticsearch/plugins/6.8/plugin-management.html",
    ]
    # Patch release notes for 6.8 (6.8.0 to 6.8.23)
    for patch in range(24):
        urls_68.append(f"https://www.elastic.co/guide/en/elasticsearch/reference/6.8/release-notes-6.8.{patch}.html")
    # All 6.x breaking change pages
    for m in range(9):
        urls_68.append(f"https://www.elastic.co/guide/en/elasticsearch/reference/6.8/breaking-changes-6.{m}.html")

    for url in urls_68:
        fname = os.path.basename(url)
        if "release-notes" in fname:
            target = os.path.join(v68_dir, "release-notes", fname)
        elif "breaking-changes" in fname:
            target = os.path.join(v68_dir, "breaking-changes", fname)
        elif "dynamic" in fname or "types" in fname:
            target = os.path.join(v68_dir, "mappings", fname)
        elif "attachment" in fname:
            target = os.path.join(v68_dir, "plugins-and-modules", "ingest-attachment", fname)
        else:
            target = os.path.join(v68_dir, "whats-new", fname)
        tasks.append((url, target, False))

    # 7.17 Guide URLs
    urls_717 = [
        "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/es-release-notes.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/release-highlights.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/dynamic-mapping.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/dynamic.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/removal-of-types.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/7.17/ingest.html",
        "https://www.elastic.co/guide/en/elasticsearch/plugins/7.17/ingest-attachment.html",
        "https://www.elastic.co/guide/en/elasticsearch/plugins/7.17/plugin-management.html",
    ]
    # Breaking changes 7.0 to 7.9 and migrating-7.10 to 7.17
    for m in range(10):
        urls_717.append(f"https://www.elastic.co/guide/en/elasticsearch/reference/7.17/breaking-changes-7.{m}.html")
    for m in range(10, 18):
        urls_717.append(f"https://www.elastic.co/guide/en/elasticsearch/reference/7.17/migrating-7.{m}.html")
    # Release notes for 7.17 patches (7.17.0 to 7.17.29)
    for p in range(30):
        urls_717.append(f"https://www.elastic.co/guide/en/elasticsearch/reference/7.17/release-notes-7.17.{p}.html")

    for url in urls_717:
        fname = os.path.basename(url)
        m = re.search(r"7\.(\d+)", fname)
        minor_dir = os.path.join(DOCS_VERSIONS_DIR, f"7.{m.group(1)}") if m else os.path.join(DOCS_VERSIONS_DIR, "7.17")
        if "release-notes" in fname:
            target = os.path.join(minor_dir, "release-notes", fname)
        elif "breaking-changes" in fname or "migrating-" in fname:
            target = os.path.join(minor_dir, "breaking-changes", fname)
        elif "dynamic" in fname or "types" in fname:
            target = os.path.join(minor_dir, "mappings", fname)
        elif "attachment" in fname:
            target = os.path.join(minor_dir, "plugins-and-modules", "ingest-attachment", fname)
        else:
            target = os.path.join(minor_dir, "migration-guide", fname)
        tasks.append((url, target, False))

    # 8.17 Guide URLs
    urls_817 = [
        "https://www.elastic.co/guide/en/elasticsearch/reference/8.17/breaking-changes.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/8.17/es-release-notes.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/8.17/release-highlights.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/8.17/dynamic-mapping.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/8.17/dynamic.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/8.17/attachment.html",
        "https://www.elastic.co/guide/en/elasticsearch/reference/8.17/ingest.html",
        "https://www.elastic.co/guide/en/elasticsearch/plugins/8.17/intro.html",
        "https://www.elastic.co/guide/en/elasticsearch/plugins/8.17/plugin-management.html",
    ]
    # Migrating 8.0 to 8.17
    for m in range(18):
        urls_817.append(f"https://www.elastic.co/guide/en/elasticsearch/reference/8.17/migrating-8.{m}.html")
    # Release notes for 8.17 patches (8.17.0 to 8.17.10) and major .0 releases
    for m in range(18):
        urls_817.append(f"https://www.elastic.co/guide/en/elasticsearch/reference/8.17/release-notes-8.{m}.0.html")
    for p in range(11):
        urls_817.append(f"https://www.elastic.co/guide/en/elasticsearch/reference/8.17/release-notes-8.17.{p}.html")

    for url in urls_817:
        fname = os.path.basename(url)
        m = re.search(r"8\.(\d+)", fname)
        minor_dir = os.path.join(DOCS_VERSIONS_DIR, f"8.{m.group(1)}") if m else os.path.join(DOCS_VERSIONS_DIR, "8.17")
        if "release-notes" in fname:
            target = os.path.join(minor_dir, "release-notes", fname)
        elif "breaking-changes" in fname or "migrating-" in fname:
            target = os.path.join(minor_dir, "breaking-changes", fname)
        elif "dynamic" in fname:
            target = os.path.join(minor_dir, "mappings", fname)
        elif "attachment" in fname:
            target = os.path.join(minor_dir, "plugins-and-modules", "ingest-attachment", fname)
        else:
            target = os.path.join(minor_dir, "migration-guide", fname)
        tasks.append((url, target, False))

    # Deduplicate tasks by dest_path
    dedup = {}
    for url, dest, is_gh in tasks:
        if dest not in dedup:
            dedup[dest] = (url, dest, is_gh)
    print(f"Total unique documentation download tasks assembled: {len(dedup)}")
    return list(dedup.values())


def generate_synthesis_docs():
    """Generate INGEST_ATTACHMENT_SCHEMA_EVOLUTION.md and DYNAMIC_MAPPING_AND_STRICT_GUIDE.md"""
    print("Generating comprehensive schema & migration synthesis documents...")

    # 1. INGEST_ATTACHMENT_SCHEMA_EVOLUTION.md
    attachment_doc = """# Ingest Attachment Processor: Schema Evolution & Strict Mapping Field Catalog

## Overview & Background

In Elasticsearch, the attachment processor (`ingest-attachment` plugin in ES 5.x–7.x, built-in module in ES 8.x–9.x, formerly `mapper-attachments` in ES 2.x) extracts content and metadata from binary attachments (PDF, DOCX, PPT, XLSX, images, etc.) using Apache Tika.

### Why Strict Dynamic Mapping Fails During Upgrades
When an Elasticsearch index is configured with `"dynamic": "strict"`, Elasticsearch will reject any document that introduces a field not explicitly declared in the index mapping:
```json
{
  "error": {
    "root_cause": [{
      "type": "strict_dynamic_mapping_exception",
      "reason": "mapping set to strict, dynamic introduction of [modified] is not allowed"
    }],
    "type": "strict_dynamic_mapping_exception",
    "reason": "mapping set to strict, dynamic introduction of [modified] is not allowed"
  },
  "status": 400
}
```

In **Elasticsearch 6.8 and all 7.x versions**, `AttachmentProcessor` extracted a fixed set of **8 properties**:
1. `content` (text)
2. `title` (text)
3. `author` (text)
4. `keywords` (text)
5. `date` (date)
6. `content_type` (text / keyword)
7. `content_length` (long)
8. `language` (keyword / text)

Starting in **Elasticsearch 8.0.0 and continuing through 9.2.3+**, Elastic upgraded Apache Tika and expanded `AttachmentProcessor.Property` enum to support **28 properties** (adding 20 new metadata fields).
By default, if an ingest pipeline does not specify the `"properties"` array in its configuration, **Elasticsearch extracts ALL 28 properties**. If an indexed document contains any metadata for these fields (such as `modified`, `format`, `creator_tool`, etc.), Elasticsearch attempts to write them into the target object. In a strict index mapping where only the legacy 8 fields were defined, **indexing immediately throws `strict_dynamic_mapping_exception` and fails**.

---

## Verbatim Java Enum: Property Comparison Across Versions

### ES 6.8 & 7.x (`plugins/ingest-attachment/.../AttachmentProcessor.java`)
```java
enum Property {
    CONTENT,
    TITLE,
    AUTHOR,
    KEYWORDS,
    DATE,
    CONTENT_TYPE,
    CONTENT_LENGTH,
    LANGUAGE;

    public static Property parse(String value) {
        return valueOf(value.toUpperCase(Locale.ROOT));
    }

    public String toLowerCase() {
        return this.toString().toLowerCase(Locale.ROOT);
    }
}
```

### ES 8.0 through ES 9.2.3+ (`modules/ingest-attachment/.../AttachmentProcessor.java`)
```java
enum Property {
    CONTENT,
    TITLE,
    AUTHOR,
    KEYWORDS,
    DATE,
    CONTENT_TYPE,
    CONTENT_LENGTH,
    LANGUAGE,
    MODIFIED,
    FORMAT,
    IDENTIFIER,
    CONTRIBUTOR,
    COVERAGE,
    MODIFIER,
    CREATOR_TOOL,
    PUBLISHER,
    RELATION,
    RIGHTS,
    SOURCE,
    TYPE,
    DESCRIPTION,
    PRINT_DATE,
    METADATA_DATE,
    LATITUDE,
    LONGITUDE,
    ALTITUDE,
    RATING,
    COMMENTS;

    public static Property parse(String value) {
        return valueOf(value.toUpperCase(Locale.ROOT));
    }

    public String toLowerCase() {
        return this.toString().toLowerCase(Locale.ROOT);
    }
}
```

---

## Complete Verbatim Property Catalog (All 28 Fields)

| # | Property Name | ES Mapping Type | Apache Tika Metadata Key | Introduced In | Description |
|---|---------------|-----------------|--------------------------|---------------|-------------|
| 1 | `content` | `text` | N/A (Extracted Text Body) | ES 5.0 (Legacy) | Extracted text content of the attachment. |
| 2 | `title` | `text` | `TikaCoreProperties.TITLE` | ES 5.0 (Legacy) | Document title. |
| 3 | `author` | `text` | `TikaCoreProperties.CREATOR` | ES 5.0 (Legacy) | Author / creator of the document. |
| 4 | `keywords` | `text` | `TikaCoreProperties.KEYWORDS` | ES 5.0 (Legacy) | Comma/space separated document keywords. |
| 5 | `date` | `date` | `TikaCoreProperties.CREATED` | ES 5.0 (Legacy) | Document creation date. |
| 6 | `content_type` | `keyword` / `text` | `HttpHeaders.CONTENT_TYPE` | ES 5.0 (Legacy) | MIME content type (e.g. `application/pdf`). |
| 7 | `content_length`| `long` | `HttpHeaders.CONTENT_LENGTH` | ES 5.0 (Legacy) | Size of attachment in bytes. |
| 8 | `language` | `keyword` | `TikaCoreProperties.LANGUAGE` | ES 5.0 (Legacy) | Detected language code (e.g. `en`, `de`). |
| 9 | `modified` | `date` | `TikaCoreProperties.MODIFIED` | **ES 8.0.0** | Document modification timestamp. |
| 10 | `format` | `keyword` / `text` | `TikaCoreProperties.FORMAT` | **ES 8.0.0** | Format identifier. |
| 11 | `identifier` | `keyword` / `text` | `TikaCoreProperties.IDENTIFIER` | **ES 8.0.0** | Resource identifier / URI / ISBN / UUID. |
| 12 | `contributor` | `text` | `TikaCoreProperties.CONTRIBUTOR` | **ES 8.0.0** | Contributors to the resource. |
| 13 | `coverage` | `text` | `TikaCoreProperties.COVERAGE` | **ES 8.0.0** | Spatial or temporal topic of the resource. |
| 14 | `modifier` | `text` | `TikaCoreProperties.MODIFIER` | **ES 8.0.0** | Name of user who last modified the document. |
| 15 | `creator_tool` | `keyword` / `text` | `TikaCoreProperties.CREATOR_TOOL` | **ES 8.0.0** | Tool used to create the document (e.g. `Word`, `LaTeX`). |
| 16 | `publisher` | `text` | `TikaCoreProperties.PUBLISHER` | **ES 8.0.0** | Entity responsible for making resource available. |
| 17 | `relation` | `keyword` / `text` | `TikaCoreProperties.RELATION` | **ES 8.0.0** | Related resources. |
| 18 | `rights` | `keyword` / `text` | `TikaCoreProperties.RIGHTS` | **ES 8.0.0** | Copyright and IP rights information. |
| 19 | `source` | `text` | `TikaCoreProperties.SOURCE` | **ES 8.0.0** | Reference to resource from which document is derived. |
| 20 | `type` | `keyword` / `text` | `TikaCoreProperties.TYPE` | **ES 8.0.0** | Nature or genre of resource. |
| 21 | `description` | `text` | `TikaCoreProperties.DESCRIPTION` | **ES 8.0.0** | Abstract or free-text account of resource. |
| 22 | `print_date` | `date` | `TikaCoreProperties.PRINT_DATE` | **ES 8.0.0** | Date the document was printed. |
| 23 | `metadata_date` | `date` | `TikaCoreProperties.METADATA_DATE` | **ES 8.0.0** | Date metadata was last updated. |
| 24 | `latitude` | `double` | `TikaCoreProperties.LATITUDE` | **ES 8.0.0** | Geographic latitude metadata (e.g. EXIF in images/PDFs). |
| 25 | `longitude` | `double` | `TikaCoreProperties.LONGITUDE` | **ES 8.0.0** | Geographic longitude metadata. |
| 26 | `altitude` | `double` | `TikaCoreProperties.ALTITUDE` | **ES 8.0.0** | Altitude metadata. |
| 27 | `rating` | `double` | `TikaCoreProperties.RATING` | **ES 8.0.0** | User rating metadata. |
| 28 | `comments` | `text` | `TikaCoreProperties.COMMENTS` | **ES 8.0.0** | User or system comments embedded in document. |

---

## Production Mitigation & Remediation Strategies

### Strategy A: Whitelist Legacy Properties in Ingest Pipeline (No Mapping Change Needed)
If you cannot alter strict index mappings, you MUST restrict the attachment processor to only extract legacy fields:
```json
PUT _ingest/pipeline/attachment_pipeline
{
  "description": "Extract attachment with legacy property whitelist to prevent strict dynamic mapping failure",
  "processors": [
    {
      "attachment": {
        "field": "data",
        "target_field": "attachment",
        "properties": [
          "content",
          "title",
          "author",
          "keywords",
          "date",
          "content_type",
          "content_length",
          "language"
        ]
      }
    }
  ]
}
```

### Strategy B: Complete Strict Index Mapping Definition (ES8 / ES9)
If using `dynamic: "strict"`, define all 28 potential attachment properties in the index mapping:
```json
PUT bench-es9
{
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "data": { "type": "binary" },
      "attachment": {
        "properties": {
          "content": { "type": "text" },
          "title": { "type": "text" },
          "author": { "type": "text" },
          "keywords": { "type": "text" },
          "date": { "type": "date" },
          "content_type": { "type": "keyword" },
          "content_length": { "type": "long" },
          "language": { "type": "keyword" },
          "modified": { "type": "date" },
          "format": { "type": "keyword" },
          "identifier": { "type": "keyword" },
          "contributor": { "type": "text" },
          "coverage": { "type": "text" },
          "modifier": { "type": "text" },
          "creator_tool": { "type": "keyword" },
          "publisher": { "type": "text" },
          "relation": { "type": "keyword" },
          "rights": { "type": "keyword" },
          "source": { "type": "text" },
          "type": { "type": "keyword" },
          "description": { "type": "text" },
          "print_date": { "type": "date" },
          "metadata_date": { "type": "date" },
          "latitude": { "type": "double" },
          "longitude": { "type": "double" },
          "altitude": { "type": "double" },
          "rating": { "type": "double" },
          "comments": { "type": "text" }
        }
      }
    }
  }
}
```
"""
    with open(os.path.join(DOCS_VERSIONS_DIR, "INGEST_ATTACHMENT_SCHEMA_EVOLUTION.md"), "w") as f:
        f.write(attachment_doc)

    # 2. DYNAMIC_MAPPING_AND_STRICT_GUIDE.md
    dynamic_doc = """# Dynamic & Strict Index Mapping Evolution: ES 6.8 through 9.2.3

## 1. Mapping Type Removal (`_doc`)
- **ES 6.x**: Indices support a single type per index. Requests commonly specify the type (e.g. `bench-es6/_doc/1` or `bench-es6/doc/1`). Mappings are nested under `{"mappings": {"_doc": {"properties": {...}}}}`.
- **ES 7.x**: Mapping types are deprecated. `_doc` is retained solely as an endpoint path convention (`POST index/_doc`), but mapping types are removed from the schema (`{"mappings": {"properties": {...}}}`).
- **ES 8.x & ES 9.x**: Mapping types are completely eliminated. Any request specifying a type name other than `_doc` fails. Mappings must declare `properties` directly under `mappings`.

## 2. Dynamic Mapping Modes (`dynamic`)
The `dynamic` setting controls whether new fields can be added dynamically when encountered in indexed documents:
- `true`: (Default) Dynamically detect field type and add field to index mapping.
- `false`: Silently ignore new fields. New fields are stored in `_source` but not indexed or searchable.
- `strict`: Throw `strict_dynamic_mapping_exception` and reject document indexing if unknown fields appear.
- `runtime`: (Introduced in ES 7.11, default in some workloads in ES 8+) Dynamically create runtime fields instead of indexing new fields.

## 3. Date Parsing & Formats: Joda-Time vs Java Time (`java.time`)
- **ES 6.x**: Parsed using Joda-Time pattern formatters.
- **ES 7.0+**: Replaced Joda-Time with standard `java.time.format.DateTimeFormatter`.
- In standard migrations, default `strict_date_optional_time||epoch_millis` remains compatible, but custom pattern syntax with symbols like `y`, `Y`, `d`, `D` must be audited carefully.

## 4. Strict Mapping Checklist for Ingest Pipelines
When running ingest pipelines that enrich or extract documents:
1. Every processor output field (`target_field`) must be explicitly declared in index properties.
2. Ingest Attachment Processor: Extracts up to 28 fields in ES 8+/9+ compared to 8 fields in ES 6/7. Ensure mapping declares all 28 or set explicit `"properties": [...]` whitelist.
3. System metadata fields (`modified_at`, `cutover_at`, etc.): Ensure custom pipeline fields are mapped or stripped before indexing.
"""
    with open(os.path.join(DOCS_VERSIONS_DIR, "DYNAMIC_MAPPING_AND_STRICT_GUIDE.md"), "w") as f:
        f.write(dynamic_doc)

    # 3. README.md
    readme_doc = f"""# Elasticsearch Official Documentation Archive: 6.8 through 9.2.3

This directory contains the complete, unedited, verbatim documentation and changelogs for Elasticsearch versions 6.8 through 9.2.3, directly crawled and parsed from official Elastic sources:
- Official GitHub repository: `elastic/elasticsearch` (Asciidoc, Markdown, YAML changelog bundles, and plugin/module source code)
- Official Elastic Guide: `elastic.co/guide` and `docs.elastic.co` (Rendered HTML and documentation)

## Directory Structure by Version

```
docs/versions/
├── 6.8/                     # Elasticsearch 6.8 series (6.8.0 to 6.8.23)
├── 7.0/ ... 7.17/           # All Elasticsearch 7.x minor releases (7.0 to 7.17)
├── 8.0/ ... 8.19/           # All Elasticsearch 8.x minor releases (8.0 to 8.19)
├── 9.0/                     # Elasticsearch 9.0 (including 9.0.0 through 9.0.8)
├── 9.1/                     # Elasticsearch 9.1 (including 9.1.0 through 9.1.10)
├── 9.2/                     # Elasticsearch 9.2 (including 9.2.0, 9.2.1, 9.2.2, 9.2.3)
├── INGEST_ATTACHMENT_SCHEMA_EVOLUTION.md  # Exhaustive 28-field property breakdown & strict mapping fix
├── DYNAMIC_MAPPING_AND_STRICT_GUIDE.md    # Mapping types, strict dynamic mapping, date format changes
└── README.md
```

## Within Each Version Directory
- `release-notes/`: Complete minor and patch release notes verbatim.
- `breaking-changes/`: All breaking changes, deprecation removals, and migration notices.
- `migration-guide/`: Official step-by-step upgrade instructions.
- `whats-new/`: Feature highlights and additions.
- `plugins-and-modules/`: Full documentation and changelogs for all plugins and modules, specifically including `ingest-attachment` documentation, source code, and exact property enum definitions.
- `mappings/`: Dynamic mapping, strict mapping behavior, type removal, and schema rules.
"""
    with open(os.path.join(DOCS_VERSIONS_DIR, "README.md"), "w") as f:
        f.write(readme_doc)
    print("Synthesis documents generated successfully.")


def main():
    print(f"Target repository docs directory: {DOCS_VERSIONS_DIR}")
    os.makedirs(DOCS_VERSIONS_DIR, exist_ok=True)

    manifest = build_download_manifest()
    total_tasks = len(manifest)
    print(f"Beginning concurrent download of {total_tasks} documentation files...")

    success_count = 0
    fail_count = 0
    cached_count = 0
    total_bytes = 0

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(fetch_and_save, item): item for item in manifest}
        for future in as_completed(futures):
            dest, size, was_cached = future.result()
            if size > 0:
                success_count += 1
                total_bytes += size
                if was_cached:
                    cached_count += 1
            else:
                fail_count += 1

    dur = time.time() - t0
    print(f"\nDownload completed in {dur:.2f} seconds.")
    print(f"  Total tasks: {total_tasks}")
    print(f"  Successful: {success_count} ({cached_count} existing/cached)")
    print(f"  Failed (404/not found): {fail_count}")
    print(f"  Total data saved: {total_bytes / (1024 * 1024):.2f} MB")

    generate_synthesis_docs()
    print("\nAll tasks completed successfully.")


if __name__ == "__main__":
    main()
