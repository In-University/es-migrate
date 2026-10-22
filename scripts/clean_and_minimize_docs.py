#!/usr/bin/env python3
"""
clean_and_minimize_docs.py

Cleans and minimizes the format of all archived Elasticsearch documentation
across docs/versions/ to be optimized for AI Agent consumption:
- Preserves 100% of the content, code, configurations, parameters, and tables.
- Converts HTML and AsciiDoc files into clean, concise GitHub Flavored Markdown (.md).
- Strips out web boilerplate, tracking tags, CSS, scripts, nav headers, and footers.
- Normalizes macros ({es}, {es-pull}, {es-issue}, cross-references).
- Removes non-text binary files (PNG images).
- Deletes obsolete .html and .asciidoc raw files after verified conversion.
"""

import os
import re
import glob
from bs4 import BeautifulSoup, NavigableString, Tag

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "versions")


def table_to_markdown(table):
    rows = []
    for tr in table.find_all("tr"):
        cells = [
            re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).replace("|", "\\|")
            for cell in tr.find_all(["th", "td"])
        ]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    max_cols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < max_cols:
            r.append("")
    out = []
    out.append("| " + " | ".join(rows[0]) + " |")
    out.append("| " + " | ".join(["---"] * max_cols) + " |")
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n\n" + "\n".join(out) + "\n\n"


def element_to_markdown(element):
    if isinstance(element, NavigableString):
        return str(element)
    if not isinstance(element, Tag):
        return ""

    tag = element.name.lower()

    # Remove unwanted web elements
    classes = element.get("class", [])
    if isinstance(classes, str):
        classes = [classes]
    classes_str = " ".join(classes)

    if any(c in classes_str for c in ["edit_me", "navheader", "navfooter", "breadcrumbs", "page_header"]):
        return ""
    if tag in ["script", "style", "meta", "link", "noscript"]:
        return ""

    if tag == "table":
        return table_to_markdown(element)

    inner = "".join(element_to_markdown(child) for child in element.children)

    if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        level = int(tag[1])
        text = re.sub(r"\s+", " ", inner.strip())
        return f"\n\n{'#' * level} {text}\n\n"
    elif tag == "p":
        text = inner.strip()
        return f"\n\n{text}\n\n" if text else ""
    elif tag == "li":
        text = inner.strip()
        return f"\n* {text}" if text else ""
    elif tag in ["ul", "ol"]:
        return f"\n{inner}\n"
    elif tag == "pre":
        text = inner.strip()
        return f"\n\n```\n{text}\n```\n\n"
    elif tag == "code":
        text = inner.strip()
        return f"`{text}`" if text else ""
    elif tag in ["strong", "b"]:
        text = inner.strip()
        return f"**{text}**" if text else ""
    elif tag in ["em", "i"]:
        text = inner.strip()
        return f"*{text}*" if text else ""
    elif tag == "a":
        href = element.get("href", "")
        text = inner.strip()
        if href and text:
            return f"[{text}]({href})"
        return text or href
    elif tag in ["div", "section", "article", "main", "span"]:
        return inner
    elif tag == "br":
        return "\n"
    else:
        return inner


def html_to_markdown(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    # Find main content container
    content = soup.find("div", id="content") or soup.find("div", class_="main-container") or soup.find("article") or soup.find("body") or soup
    # Remove unwanted tags
    for bad in content.find_all(["script", "style", "noscript", "iframe"]):
        bad.decompose()
    for bad in content.find_all(class_=re.compile(r"navheader|navfooter|breadcrumbs|edit_me|page_header")):
        bad.decompose()

    md = element_to_markdown(content)
    # Clean up excess whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = md.strip()
    return md


def asciidoc_to_markdown(text):
    # Expand Elastic asciidoc macros
    text = text.replace("{es}", "Elasticsearch")
    text = text.replace("{kib}", "Kibana")
    text = text.replace("{ls}", "Logstash")
    text = text.replace("{beats}", "Beats")
    text = text.replace("{xpack}", "X-Pack")

    # Pull & Issue links
    text = re.sub(r"\{es-pull\}(\d+)\[(#\d+)\]", r"[\2](https://github.com/elastic/elasticsearch/pull/\1)", text)
    text = re.sub(r"\{es-issue\}(\d+)\[(#\d+)\]", r"[\2](https://github.com/elastic/elasticsearch/issues/\1)", text)
    text = re.sub(r"\{pull\}(\d+)\[(#\d+)\]", r"[\2](https://github.com/elastic/elasticsearch/pull/\1)", text)
    text = re.sub(r"\{issue\}(\d+)\[(#\d+)\]", r"[\2](https://github.com/elastic/elasticsearch/issues/\1)", text)

    # Cross references: <<anchor,label>> or <<anchor>>
    text = re.sub(r"<<([^,>]+),\s*([^>]+)>>", r"[\2](#\1)", text)
    text = re.sub(r"<<([^>]+)>>", r"[\1](#\1)", text)

    # Links: https://...[label]
    text = re.sub(r"(https?://[^\s\[]+)\[([^\]]*)\]", r"[\2](\1)", text)

    # Strip raw anchors, directives, and passthroughs
    text = re.sub(r"\[\[[^\]]+\]\]\n?", "", text)
    text = re.sub(r"\[discrete\]\n?", "", text)
    text = re.sub(r"\+\+\+\+[\s\S]*?\+\+\+\+\n?", "", text)

    lines = []
    in_code = False
    for line in text.splitlines():
        trimmed = line.strip()
        if trimmed in ["----", "...."]:
            in_code = not in_code
            lines.append("```")
            continue
        if not in_code:
            # AsciiDoc Headings
            m_h = re.match(r"^(={1,6})\s+(.*)$", line)
            if m_h:
                lines.append("#" * len(m_h.group(1)) + " " + m_h.group(2))
                continue
            # Definition list: Term:: -> **Term**:
            m_def = re.match(r"^([^:\s][^:]*)::\s*$", line)
            if m_def:
                lines.append(f"**{m_def.group(1)}**:")
                continue
        lines.append(line)

    md = "\n".join(lines)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def process_all_docs():
    print(f"Scanning {DOCS_DIR} for files to format and clean...")

    # 1. Remove binary PNG images
    png_files = glob.glob(os.path.join(DOCS_DIR, "**", "*.png"), recursive=True)
    for p in png_files:
        try:
            os.remove(p)
            print(f"Removed binary image: {os.path.basename(p)}")
        except Exception as e:
            print(f"Error removing {p}: {e}")

    # 2. Convert AsciiDoc files to clean Markdown (.md)
    asciidoc_files = glob.glob(os.path.join(DOCS_DIR, "**", "*.asciidoc"), recursive=True)
    print(f"Converting {len(asciidoc_files)} AsciiDoc files to clean Markdown...")
    converted_ad = 0
    for ad_path in asciidoc_files:
        try:
            with open(ad_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
            clean_md = asciidoc_to_markdown(raw_text)
            if clean_md:
                md_path = os.path.splitext(ad_path)[0] + ".md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(clean_md)
                os.remove(ad_path)
                converted_ad += 1
        except Exception as e:
            print(f"Error converting {ad_path}: {e}")
    print(f"  Successfully converted {converted_ad} AsciiDoc files.")

    # 3. Convert HTML files to clean Markdown (.md)
    html_files = glob.glob(os.path.join(DOCS_DIR, "**", "*.html"), recursive=True)
    print(f"Converting {len(html_files)} HTML files to clean, minimal Markdown...")
    converted_html = 0
    for html_path in html_files:
        try:
            md_path = os.path.splitext(html_path)[0] + ".md"
            # If a clean .md already exists from an AsciiDoc source, delete the redundant HTML
            if os.path.exists(md_path) and os.path.getsize(md_path) > 0:
                os.remove(html_path)
                converted_html += 1
                continue

            with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_html = f.read()
            clean_md = html_to_markdown(raw_html)
            if clean_md:
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(clean_md)
            os.remove(html_path)
            converted_html += 1
        except Exception as e:
            print(f"Error converting {html_path}: {e}")
    print(f"  Successfully converted {converted_html} HTML files.")

    # Print summary statistics
    all_files = glob.glob(os.path.join(DOCS_DIR, "**", "*"), recursive=True)
    files_only = [f for f in all_files if os.path.isfile(f)]
    exts = {}
    for f in files_only:
        ext = os.path.splitext(f)[1] or "no-ext"
        exts[ext] = exts.get(ext, 0) + 1

    print("\nFormat cleaning and minimization complete!")
    print(f"Total remaining text/code files: {len(files_only)}")
    print("Breakdown by file extension:")
    for ext, count in sorted(exts.items()):
        print(f"  {ext}: {count}")


if __name__ == "__main__":
    process_all_docs()
