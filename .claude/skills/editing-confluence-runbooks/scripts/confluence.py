#!/usr/bin/env python3
"""Minimal Confluence REST v1 client (stdlib only). Content rules are NOT checked here.

  resolve <link|id>                       print base URL, auth mode, page id
  get     <link|id> --out FILE            save body.storage to FILE (+ FILE-stem.meta.json)
  check   <FILE>                          storage XML syntax check only
  diff    <OLD> <NEW>                     readable diff of two storage files
  put     <link|id> <FILE> --expect-version N [--title T] [--message M] [--confirm]

  whoami                                  show which .env was loaded and test the credentials

Config: read from <skill>/.env (or the file in CONFLUENCE_ENV_FILE); real env vars win.
  CONFLUENCE_BASE_URL + CONFLUENCE_TOKEN (Data Center PAT, Bearer)
  CONFLUENCE_EMAIL + CONFLUENCE_TOKEN    (*.atlassian.net, Basic)
"""
import argparse, base64, difflib, html.entities, json, os, re, sys
import urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def die(msg):
    sys.exit(f"ERROR: {msg}")


ENV_FILE = Path(os.environ.get("CONFLUENCE_ENV_FILE") or Path(__file__).resolve().parent.parent / ".env")


def load_env_file():
    """Minimal KEY=VALUE reader (# comments, optional quotes, optional 'export '). Never overrides real env."""
    if not ENV_FILE.is_file():
        return False
    for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip().removeprefix("export ").strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if val:
            os.environ.setdefault(key, val)
    return True


# ---------------------------------------------------------------- target + HTTP

def resolve(link):
    env_base = os.environ.get("CONFLUENCE_BASE_URL", "").rstrip("/")
    if link.isdigit():
        if not env_base:
            die("CONFLUENCE_BASE_URL not set")
        return {"base": env_base, "page_id": link, "cloud": ".atlassian.net" in env_base}
    u = urllib.parse.urlparse(link)
    cloud = u.netloc.endswith(".atlassian.net")
    base = f"https://{u.netloc}/wiki" if cloud else env_base
    if not base:
        die("CONFLUENCE_BASE_URL not set")
    t = {"base": base, "cloud": cloud, "page_id": None}
    m = (re.search(r"[?&]pageId=(\d+)", link) or re.search(r"/pages/(?:edit-v2/|edit/)?(\d+)", u.path))
    if m:
        t["page_id"] = m.group(1)
    elif m := re.search(r"/display/([^/]+)/([^/?#]+)", u.path):
        t["space"], t["title"] = (urllib.parse.unquote_plus(x) for x in m.groups())
    else:
        die("cannot find page id in link; ask the user for it")
    return t


def api(t, method, path, payload=None):
    token = os.environ.get("CONFLUENCE_TOKEN") or die("CONFLUENCE_TOKEN not set")
    if t["cloud"]:
        email = os.environ.get("CONFLUENCE_EMAIL") or die("CONFLUENCE_EMAIL not set (Cloud)")
        auth = "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()
    else:
        auth = "Bearer " + token
    req = urllib.request.Request(
        t["base"] + "/rest/api" + path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": auth, "Accept": "application/json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            body = json.loads(body).get("message", body)
        except ValueError:
            pass
        die(f"{method} {path.split('?')[0]} -> HTTP {e.code}: {str(body)[:400]}")
    except urllib.error.URLError as e:
        die(f"cannot reach {t['base']}: {e.reason}")


def fetch(t):
    q = "expand=body.storage,version,space"
    if t["page_id"]:
        try:
            return api(t, "GET", f"/content/{t['page_id']}?{q}")
        except SystemExit:  # unpublished draft is only visible with status=draft
            return api(t, "GET", f"/content/{t['page_id']}?status=draft&{q}")
    res = api(t, "GET", "/content?" + urllib.parse.urlencode(
        {"spaceKey": t["space"], "title": t["title"], "expand": "body.storage,version,space"}))
    return res["results"][0] if res.get("results") else die("page not found by space/title")


# ---------------------------------------------------------------- syntax / diff

def _entities(text):
    keep = {"amp", "lt", "gt", "quot", "apos"}
    return re.sub(r"&([A-Za-z][A-Za-z0-9]*);", lambda m: m.group(0) if m.group(1) in keep
                  else chr(html.entities.name2codepoint.get(m.group(1), 0xFFFD)), text)


def syntax_error(text):
    try:
        ET.fromstring(f'<r xmlns:ac="a" xmlns:ri="r" xmlns:at="t">{_entities(text)}</r>')
    except ET.ParseError as e:
        return str(e)


def _lines(text):
    text = re.sub(r'\s(?:ac:schema-version|ac:macro-id|ac:local-id|local-id)="[^"]*"', "", _entities(text))
    text = re.sub(r"(?=<(?:p|h[1-6]|tr|li|table|ac:structured-macro|ac:parameter|ac:rich-text-body|"
                  r"ac:plain-text-body|ac:layout-section|ac:layout-cell|ac:task)[\s>/])", "\n", text)
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


# ---------------------------------------------------------------- commands

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("resolve").add_argument("link")
    g = s.add_parser("get"); g.add_argument("link"); g.add_argument("--out", required=True)
    s.add_parser("check").add_argument("file")
    d = s.add_parser("diff"); d.add_argument("old"); d.add_argument("new")
    u = s.add_parser("put"); u.add_argument("link"); u.add_argument("file")
    u.add_argument("--expect-version", type=int, required=True)
    u.add_argument("--title"); u.add_argument("--message"); u.add_argument("--confirm", action="store_true")
    s.add_parser("whoami")
    a = p.parse_args()
    loaded = load_env_file()

    if a.cmd == "whoami":
        print(f"env file: {ENV_FILE} ({'loaded' if loaded else 'not found'})")
        for k in ("CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_TOKEN"):
            v = os.environ.get(k, "")
            print(f"  {k} = {(v[:4] + '…' + v[-4:]) if k.endswith('TOKEN') and v else (v or '(empty)')}")
        base = os.environ.get("CONFLUENCE_BASE_URL", "").rstrip("/") or die("CONFLUENCE_BASE_URL not set")
        me = api({"base": base, "cloud": ".atlassian.net" in base}, "GET", "/user/current")
        print(f"auth OK as: {me.get('displayName')} ({me.get('username') or me.get('accountId')})")

    elif a.cmd == "resolve":
        print(json.dumps(resolve(a.link), indent=2))

    elif a.cmd == "get":
        t = resolve(a.link); page = fetch(t); out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page["body"]["storage"]["value"], encoding="utf-8")
        meta = {"id": page["id"], "title": page["title"], "status": page["status"],
                "version": page["version"]["number"], "space": page["space"]["key"], "base": t["base"]}
        out.with_name(out.stem + ".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(meta, indent=2, ensure_ascii=False))

    elif a.cmd == "check":
        err = syntax_error(Path(a.file).read_text(encoding="utf-8-sig"))
        print(f"syntax: ERROR {err}" if err else "syntax: OK")
        sys.exit(1 if err else 0)

    elif a.cmd == "diff":
        old, new = (Path(f).read_text(encoding="utf-8-sig") for f in (a.old, a.new))
        print("\n".join(difflib.unified_diff(_lines(old), _lines(new), "current", "proposed", lineterm="", n=2))
              or "(no changes)")

    elif a.cmd == "put":
        t = resolve(a.link); page = fetch(t); cur = page["version"]["number"]
        if cur != a.expect_version:
            die(f"page is at v{cur}, expected v{a.expect_version}: someone edited it. Re-get and re-apply.")
        body = Path(a.file).read_text(encoding="utf-8-sig")
        if err := syntax_error(body):
            die(f"storage XML syntax: {err}")
        title = a.title or page["title"] or die("draft has no title; pass --title")
        nxt = cur if page["status"] == "draft" else cur + 1  # publishing a draft keeps v1
        print(f"{t['base']} page {page['id']} '{title}' ({page['status']}) v{cur} -> v{nxt}")
        if not a.confirm:
            sys.exit("dry run: add --confirm after the user approves the diff")
        res = api(t, "PUT", f"/content/{page['id']}", {
            "id": page["id"], "type": page["type"], "title": title, "status": "current",
            "space": {"key": page["space"]["key"]},
            "version": {"number": nxt, "message": a.message or ""},
            "body": {"storage": {"value": body, "representation": "storage"}}})
        print(f"updated v{res['version']['number']}: {res['_links']['base']}{res['_links']['webui']}")


if __name__ == "__main__":
    main()
