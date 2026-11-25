#!/usr/bin/env python3
"""Collect what ONE person did in Jira and Confluence (read-only, stdlib only).

  whoami                       test auth for Jira and Confluence (token masked)
  jira       [--since D]       issues I was assigned / reported / logged work on  -> OUT/jira/jira.json
  confluence [--since D]       pages I created / contributed to                    -> OUT/confluence/confluence.json
  all                          both

Credentials (never passed on the command line, never printed): <skill dir>/.env, extra --env-file
(repeatable, later wins), then real environment variables.

  JIRA_BASE_URL        Data Center: https://jira.corp/jira (with context path)   Cloud: https://x.atlassian.net
  JIRA_TOKEN           DC Personal Access Token (Bearer)  /  Cloud API token
  JIRA_EMAIL           Cloud only (Basic auth). Setting it switches to Basic on DC too.
  CONFLUENCE_BASE_URL  DC: https://wiki.corp/confluence   Cloud: https://x.atlassian.net/wiki
  CONFLUENCE_TOKEN / CONFLUENCE_EMAIL   same rules
  <PRODUCT>_FLAVOR     dc | cloud   (auto: cloud if the host ends with atlassian.net)
  ATLASSIAN_CA_BUNDLE  path to a PEM file for self-signed / corporate CAs
"""
import argparse
import base64
import json
import os
import re
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ApiError(Exception):
    def __init__(self, status, body, url=""):
        super().__init__(f"HTTP {status} for {url}: {body[:300]}")
        self.status = status


# ----------------------------------------------------------------------------- config / http


def load_env(extra_files):
    env = {}
    for path in [os.path.join(SKILL_DIR, ".env")] + list(extra_files or []):
        if not os.path.isfile(path):
            continue
        C.log("env file: " + path)
        with open(path, "r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, _, v = ln.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    env.update({k: v for k, v in os.environ.items() if k.startswith(("JIRA_", "CONFLUENCE_", "ATLASSIAN_"))})
    return env


class Api:
    def __init__(self, env, prefix):
        self.prefix = prefix
        self.base = (env.get(prefix + "_BASE_URL") or "").rstrip("/")
        self.token = env.get(prefix + "_TOKEN") or ""
        self.email = env.get(prefix + "_EMAIL") or ""
        host = urllib.parse.urlparse(self.base).hostname or ""
        self.flavor = (env.get(prefix + "_FLAVOR") or ("cloud" if host.endswith("atlassian.net") else "dc")).lower()
        ca = env.get("ATLASSIAN_CA_BUNDLE")
        self.ctx = ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()

    @property
    def configured(self):
        return bool(self.base and self.token)

    def masked(self):
        t = self.token
        return (t[:3] + "***" + t[-2:]) if len(t) > 8 else "***"

    def headers(self):
        if self.email:
            raw = base64.b64encode(f"{self.email}:{self.token}".encode()).decode()
            auth = "Basic " + raw
        else:
            auth = "Bearer " + self.token
        return {"Authorization": auth, "Accept": "application/json", "User-Agent": "career-retrospective-script"}

    def get(self, path_or_url, params=None, retries=4):
        url = path_or_url if path_or_url.startswith("http") else self.base + path_or_url
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        for attempt in range(retries):
            req = urllib.request.Request(url, headers=self.headers())
            try:
                with urllib.request.urlopen(req, timeout=60, context=self.ctx) as resp:
                    return json.loads(resp.read().decode("utf-8", errors="replace"))
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                if e.code in (429, 502, 503, 504) and attempt < retries - 1:
                    time.sleep(min(int(e.headers.get("Retry-After", 2 ** attempt * 2)), 60))
                    continue
                raise ApiError(e.code, body, url)
            except urllib.error.URLError as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ApiError(0, str(e.reason), url)


def day(s):
    return (s or "")[:10] or None


def parse_dt(s):
    from datetime import datetime
    try:
        return datetime.strptime((s or "")[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def cycle_days(created, resolved):
    c, r = parse_dt(created), parse_dt(resolved)
    return round((r - c).total_seconds() / 86400, 1) if c and r and r >= c else None


def user_ids(u):
    if not u:
        return set()
    return {str(u[k]).lower() for k in ("accountId", "key", "userKey", "name", "username", "emailAddress") if u.get(k)}


# ----------------------------------------------------------------------------- Jira


def jira_me(api):
    return api.get("/rest/api/2/myself")


def jira_fields(api):
    ids = {"story_points": None, "sprint": None, "epic_link": None}
    for f in api.get("/rest/api/2/field"):
        n = (f.get("name") or "").lower()
        if n in ("story points", "story point estimate") and not ids["story_points"]:
            ids["story_points"] = f["id"]
        elif n == "sprint" and not ids["sprint"]:
            ids["sprint"] = f["id"]
        elif n == "epic link" and not ids["epic_link"]:
            ids["epic_link"] = f["id"]
    return ids


def jira_search(api, jql, fields, page=100):
    issues = []
    if api.flavor == "cloud":
        token, seen = None, set()
        while True:
            params = {"jql": jql, "fields": ",".join(fields), "maxResults": page}
            if token:
                params["nextPageToken"] = token
            try:
                data = api.get("/rest/api/3/search/jql", params)
            except ApiError as e:
                if e.status in (404, 410) and not issues:
                    return jira_search_offset(api, jql, fields, page)
                raise
            issues += data.get("issues", [])
            token = data.get("nextPageToken")
            if not token or data.get("isLast") or token in seen or not data.get("issues"):
                return issues
            seen.add(token)
    return jira_search_offset(api, jql, fields, page)


def jira_search_offset(api, jql, fields, page):
    issues, start = [], 0
    while True:
        data = api.get("/rest/api/2/search", {"jql": jql, "fields": ",".join(fields), "startAt": start, "maxResults": page})
        got = data.get("issues", [])
        issues += got
        start += len(got)
        if not got or start >= data.get("total", 0):
            return issues


def sprint_names(v):
    out = []
    for item in v or []:
        if isinstance(item, dict):
            out.append(item.get("name"))
        elif isinstance(item, str):
            m = re.search(r"name=([^,\]]+)", item)
            out.append(m.group(1) if m else item)
    return [x for x in out if x]


def compact_issue(raw, fid, me_ids):
    f = raw.get("fields", {})
    parent = f.get("parent") or {}
    epic = f.get(fid["epic_link"]) if fid["epic_link"] else None
    if not epic and (parent.get("fields", {}).get("issuetype", {}) or {}).get("name") == "Epic":
        epic = parent.get("key")
    sp = f.get(fid["story_points"]) if fid["story_points"] else None
    return {
        "key": raw["key"], "summary": f.get("summary"),
        "type": (f.get("issuetype") or {}).get("name"), "status": (f.get("status") or {}).get("name"),
        "done": ((f.get("status") or {}).get("statusCategory") or {}).get("key") == "done",
        "resolution": (f.get("resolution") or {}).get("name"), "priority": (f.get("priority") or {}).get("name"),
        "project": (f.get("project") or {}).get("key"), "created": day(f.get("created")),
        "resolved": day(f.get("resolutiondate")), "cycle_days": cycle_days(f.get("created"), f.get("resolutiondate")),
        "assignee_is_me": bool(user_ids(f.get("assignee")) & me_ids),
        "reporter_is_me": bool(user_ids(f.get("reporter")) & me_ids),
        "labels": f.get("labels") or [], "components": [c.get("name") for c in f.get("components") or []],
        "epic": epic, "story_points": sp if isinstance(sp, (int, float)) else None,
        "sprints": sprint_names(f.get(fid["sprint"])) if fid["sprint"] else [],
        "time_spent_h_all_users": round((f.get("timespent") or 0) / 3600, 1),
    }


def worklog_hours(api, key, me_ids):
    try:
        data = api.get(f"/rest/api/2/issue/{key}/worklog")
    except ApiError:
        return 0.0
    return sum(w.get("timeSpentSeconds", 0) for w in data.get("worklogs", []) if user_ids(w.get("author")) & me_ids) / 3600


def cmd_jira(api, a):
    me = jira_me(api)
    me_ids = user_ids(me)
    fid = jira_fields(api)
    base_fields = ["summary", "issuetype", "status", "resolution", "priority", "project", "created", "resolutiondate",
                   "assignee", "reporter", "labels", "components", "parent", "timespent"] + [v for v in fid.values() if v]
    since = f' AND updated >= "{a.since}"' if a.since else ""
    queries = {"assignee": "assignee WAS currentUser()", "reporter": "reporter = currentUser()",
               "worklog": "worklogAuthor = currentUser()"}
    issues, warnings = {}, []
    for role, q in queries.items():
        try:
            for raw in jira_search(api, f"({q}){since} ORDER BY created ASC", base_fields):
                it = issues.setdefault(raw["key"], compact_issue(raw, fid, me_ids))
                it.setdefault("roles", [])
                if role not in it["roles"]:
                    it["roles"].append(role)
        except ApiError as e:
            warnings.append(f"JQL '{q}' failed: {e}")
            C.log("WARN " + warnings[-1])
    items = list(issues.values())
    # worklog hours (only issues where I logged work; capped)
    wl_total = 0.0
    if not a.no_worklogs:
        for it in [i for i in items if "worklog" in i["roles"]][: a.max_worklog_issues]:
            it["my_worklog_h"] = round(worklog_hours(api, it["key"], me_ids), 1)
            wl_total += it["my_worklog_h"]
    # epic titles
    epic_keys = sorted({i["epic"] for i in items if i["epic"]})
    epic_title = {}
    for n in range(0, len(epic_keys), 40):
        chunk = epic_keys[n:n + 40]
        try:
            for raw in jira_search(api, "key in (%s)" % ",".join(chunk), ["summary", "status"]):
                epic_title[raw["key"]] = raw["fields"].get("summary")
        except ApiError as e:
            warnings.append(f"epic lookup failed: {e}")
    for it in items:
        it["epic_summary"] = epic_title.get(it["epic"])

    def agg(sel):
        done = [i for i in sel if i["done"]]
        cyc = [i["cycle_days"] for i in done if i["cycle_days"] is not None]
        epics = Counter((i["epic"], i["epic_summary"]) for i in sel if i["epic"])
        return {
            "count": len(sel), "done": len(done), "currently_assigned_to_me": sum(1 for i in sel if i["assignee_is_me"]),
            "by_type": dict(Counter(i["type"] for i in sel).most_common()),
            "by_project": dict(Counter(i["project"] for i in sel).most_common()),
            "by_year_created": dict(sorted(Counter((i["created"] or "")[:4] for i in sel).items())),
            "story_points_done": round(sum(i["story_points"] or 0 for i in done), 1),
            "story_points_all": round(sum(i["story_points"] or 0 for i in sel), 1),
            "cycle_days_median": round(statistics.median(cyc), 1) if cyc else None,
            "cycle_days_mean": round(statistics.mean(cyc), 1) if cyc else None,
            "sprints_distinct": len({s for i in sel for s in i["sprints"]}),
            "top_epics": [{"epic": k, "summary": s, "issues": n} for (k, s), n in epics.most_common(20)],
            "top_components": dict(Counter(c for i in sel for c in i["components"]).most_common(10)),
            "top_labels": dict(Counter(l for i in sel for l in i["labels"]).most_common(10)),
            "first_created": min((i["created"] for i in sel if i["created"]), default=None),
            "last_created": max((i["created"] for i in sel if i["created"]), default=None),
        }
    out = {
        "instance": api.base, "flavor": api.flavor, "me": {"display_name": me.get("displayName")},
        "since": a.since, "field_ids": fid, "warnings": warnings,
        "aggregates": {
            "assigned_to_me": agg([i for i in items if "assignee" in i["roles"]]),
            "reported_by_me": agg([i for i in items if i["reporter_is_me"]]),
            "my_logged_hours_total": round(wl_total, 1),
            "issues_touched_total": len(items),
        },
        "issues": items,
    }
    C.write_json(os.path.join(a.out, "jira", "jira.json"), out)
    ag = out["aggregates"]["assigned_to_me"]
    print(f"jira: {len(items)} issues (assigned {ag['count']}, done {ag['done']}) -> {os.path.join(a.out, 'jira', 'jira.json')}")


# ----------------------------------------------------------------------------- Confluence


def conf_me(api):
    return api.get("/rest/api/user/current")


def body_metrics(html):
    text = re.sub(r"<[^>]+>", " ", html or "")
    return {"words": len(text.split()), "code_blocks": len(re.findall(r'ac:name="code"', html or "")),
            "tables": (html or "").count("<table"), "images": len(re.findall(r"<ac:image|<img\b", html or "")),
            "headings": len(re.findall(r"<h[1-6]\b", html or ""))}


def next_url(api, nxt):
    """`_links.next` is relative; DC omits the context path, Cloud keeps /wiki on the base."""
    if nxt.startswith("http"):
        return nxt
    u = urllib.parse.urlparse(api.base)
    ctx = u.path.rstrip("/")
    if ctx and nxt.startswith(ctx + "/"):
        return f"{u.scheme}://{u.netloc}{nxt}"
    return api.base + nxt


def conf_search(api, cql, expand, limit):
    results, seen, url = [], set(), None
    while True:
        data = api.get(url) if url else api.get("/rest/api/content/search", {"cql": cql, "limit": limit, "expand": expand})
        results += data.get("results", [])
        nxt = (data.get("_links") or {}).get("next")
        if not nxt or not data.get("results") or nxt in seen:
            return results
        seen.add(nxt)
        url = next_url(api, nxt)


def cmd_confluence(api, a):
    me = conf_me(api)
    me_ids = user_ids(me)
    since = f' AND lastmodified >= "{a.since}"' if a.since else ""
    expand = "history,version,space" + ("" if a.no_bodies else ",body.storage")
    limit = 100 if a.no_bodies else 25
    pages, warnings = {}, []
    for role in ("creator", "contributor"):
        cql = f"{role} = currentUser() AND type in (page, blogpost){since} ORDER BY lastmodified DESC"
        try:
            for r in conf_search(api, cql, expand, limit):
                if r["id"] in pages:
                    pages[r["id"]]["roles"].append(role)
                    continue
                hist, ver = r.get("history") or {}, r.get("version") or {}
                p = {"id": r["id"], "type": r.get("type"), "title": r.get("title"),
                     "space": (r.get("space") or {}).get("key"), "space_name": (r.get("space") or {}).get("name"),
                     "created": day(hist.get("createdDate")), "last_modified": day(ver.get("when")),
                     "created_by_me": bool(user_ids(hist.get("createdBy")) & me_ids),
                     "revisions_total": ver.get("number"), "roles": [role],
                     "url": api.base + ((r.get("_links") or {}).get("webui") or "")}
                if not a.no_bodies:
                    p.update(body_metrics(((r.get("body") or {}).get("storage") or {}).get("value")))
                pages[r["id"]] = p
        except ApiError as e:
            warnings.append(f"CQL role={role} failed: {e}")
            C.log("WARN " + warnings[-1])
    items = sorted(pages.values(), key=lambda p: p["created"] or "")
    mine = [p for p in items if p["created_by_me"]]
    out = {
        "instance": api.base, "flavor": api.flavor, "me": {"display_name": me.get("displayName")},
        "since": a.since, "warnings": warnings,
        "aggregates": {
            "pages_created_by_me": len(mine),
            "pages_edited_not_created": len(items) - len(mine),
            "by_space_created": dict(Counter(p["space"] for p in mine).most_common(15)),
            "by_year_created": dict(sorted(Counter((p["created"] or "")[:4] for p in mine).items())),
            "words_in_my_created_pages": sum(p.get("words", 0) for p in mine),
            "code_blocks_in_my_created_pages": sum(p.get("code_blocks", 0) for p in mine),
            "tables_in_my_created_pages": sum(p.get("tables", 0) for p in mine),
            "images_in_my_created_pages": sum(p.get("images", 0) for p in mine),
            "top_pages_by_words": [{"title": p["title"], "space": p["space"], "words": p.get("words"), "url": p["url"]}
                                   for p in sorted(mine, key=lambda p: -p.get("words", 0))[:15]],
            "most_revised_pages": [{"title": p["title"], "revisions": p["revisions_total"], "url": p["url"]}
                                   for p in sorted(items, key=lambda p: -(p["revisions_total"] or 0))[:10]],
        },
        "pages": items,
    }
    C.write_json(os.path.join(a.out, "confluence", "confluence.json"), out)
    print(f"confluence: {len(items)} pages (created {len(mine)}) -> {os.path.join(a.out, 'confluence', 'confluence.json')}")


# ----------------------------------------------------------------------------- main


def main():
    C.setup_stdio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["whoami", "jira", "confluence", "all"])
    ap.add_argument("--out", help="output dir (required except for whoami)")
    ap.add_argument("--since", help="YYYY-MM-DD or 'all' (default: last --months months)")
    ap.add_argument("--months", type=int, default=C.DEFAULT_MONTHS, help="default window when --since is omitted (15)")
    ap.add_argument("--env-file", action="append", default=[])
    ap.add_argument("--no-worklogs", action="store_true")
    ap.add_argument("--max-worklog-issues", type=int, default=300)
    ap.add_argument("--no-bodies", action="store_true", help="Confluence: skip body metrics (faster)")
    a = ap.parse_args()
    if a.cmd != "whoami" and not a.out:
        ap.error("--out is required")
    a.since = C.resolve_since(a.since, a.months)
    if a.cmd != "whoami":
        C.log(f"window: updated since {a.since or 'all time'}")
    env = load_env(a.env_file)
    jira, conf = Api(env, "JIRA"), Api(env, "CONFLUENCE")
    wanted = {"whoami": ("jira", "confluence"), "all": ("jira", "confluence")}.get(a.cmd, (a.cmd,))
    failures = 0
    for name in wanted:
        api = jira if name == "jira" else conf
        if not api.configured:
            print(f"{name}: not configured (need {api.prefix}_BASE_URL and {api.prefix}_TOKEN) - skipped")
            continue
        try:
            if a.cmd == "whoami":
                me = jira_me(api) if name == "jira" else conf_me(api)
                print(f"{name}: OK  {api.flavor}  {api.base}  token={api.masked()}  "
                      f"auth={'basic' if api.email else 'bearer'}  user={me.get('displayName')}")
            elif name == "jira":
                cmd_jira(api, a)
            else:
                cmd_confluence(api, a)
        except ApiError as e:
            failures += 1
            print(f"{name}: FAILED {e}")
            if e.status in (401, 403):
                print("  -> check token / permissions; do not try other credentials")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
