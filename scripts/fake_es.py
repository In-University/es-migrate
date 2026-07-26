#!/usr/bin/env python3
"""
Minimal in-memory stand-in for the subset of the Elasticsearch API that
rollback_ctl.sh uses, so the phase machine can be exercised end to end
without two real clusters. Serves an "es6" flavour and an "es9" flavour on
one port, distinguished by index name.

Not a general ES emulator -- only the endpoints the script calls.
"""
import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

LOCK = threading.Lock()

# index name -> {"docs": {id: source}, "meta": {...}, "settings": {...}}
STORE = {}
PITS = {}
SCROLLS = {}
FAULTS = {}          # e.g. {"bulk_429_every": 3, "scroll_die_after": 1}
SEED = [None]      # path to the seed file, for /_reload
COUNTERS = {}


def epoch(ts):
    import datetime
    if ts is None:
        return 0
    try:
        return int(datetime.datetime.fromisoformat(
            ts.replace("Z", "+00:00")).timestamp() * 1000)
    except Exception:
        return 0


def ordered(idx):
    """Stable document order; position doubles as the _shard_doc tiebreaker."""
    return sorted(STORE[idx]["docs"].items(), key=lambda kv: kv[0])


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n).decode() if n else ""

    def do_GET(self):
        self._route("GET")

    def do_PUT(self):
        self._route("PUT")

    def do_POST(self):
        self._route("POST")

    def do_DELETE(self):
        self._route("DELETE")

    def _route(self, method):
        with LOCK:
            try:
                self._handle(method)
            except Exception as e:                      # surface as a 500
                self._send(500, {"error": {"type": "internal", "reason": str(e)}})

    def _handle(self, method):
        u = urlparse(self.path)
        p, q = u.path, parse_qs(u.query)
        raw = self._body()
        # _bulk carries ndjson, not a single JSON object.
        body = {} if p.endswith("_bulk") or not raw.strip().startswith("{") \
            else json.loads(raw)

        if p == "/":
            return self._send(200, {"version": {"number": "9.0.0"}})

        if p == "/_fault":                              # test-only control
            FAULTS.clear(); FAULTS.update(body)
            COUNTERS.clear()
            return self._send(200, {"ok": True})

        if p == "/_reload":                             # test-only: reseed
            STORE.clear()
            STORE.update(json.load(open(SEED[0]))["store"])
            for v in STORE.values():
                v.setdefault("meta", {})
                v.setdefault("settings", {"refresh_interval": "-1"})
            PITS.clear(); SCROLLS.clear(); FAULTS.clear(); COUNTERS.clear()
            return self._send(200, {"ok": True})

        if p == "/_pit" and method == "DELETE":
            PITS.pop(body.get("id"), None)
            return self._send(200, {"succeeded": True})

        m = re.match(r"^/([^/]+)/_pit$", p)
        if m and method == "POST":
            pid = "pit-%d" % (len(PITS) + 1)
            PITS[pid] = m.group(1)
            return self._send(200, {"id": pid})

        if p == "/_search/scroll":
            if method == "DELETE":
                return self._send(200, {"succeeded": True})
            sid = body.get("scroll_id")
            st = SCROLLS.get(sid)
            if st is None:
                return self._send(404, {"error": {
                    "type": "search_context_missing_exception",
                    "reason": "No search context found for id [42]"}})
            COUNTERS["scroll_pages"] = COUNTERS.get("scroll_pages", 0) + 1
            if FAULTS.get("scroll_die_after") and \
                    COUNTERS["scroll_pages"] >= FAULTS["scroll_die_after"]:
                SCROLLS.pop(sid, None)
                return self._send(404, {"error": {
                    "type": "search_context_missing_exception",
                    "reason": "No search context found"}})
            return self._send(200, self._scroll_page(sid))

        if p == "/_search":                             # PIT-based search
            pit = (body.get("pit") or {}).get("id")
            if pit not in PITS:
                return self._send(404, {"error": {
                    "type": "search_context_missing_exception",
                    "reason": "No search context found"}})
            return self._send(200, self._search(PITS[pit], body))

        m = re.match(r"^/([^/]+)/_search$", p)
        if m:
            idx = m.group(1)
            if "scroll" in q:
                sid = "scroll-%d" % (len(SCROLLS) + 1)
                SCROLLS[sid] = {"idx": idx, "pos": 0, "size": body.get("size", 10)}
                return self._send(200, self._scroll_page(sid))
            return self._send(200, self._search(idx, body))

        m = re.match(r"^/([^/]+)/_count$", p)
        if m:
            idx = m.group(1)
            if idx not in STORE:
                return self._send(404, {"error": {"type": "index_not_found_exception"}})
            docs = STORE[idx]["docs"]
            rng = (((body.get("query") or {}).get("range") or {}).get("updated_at") or {})
            if "gt" in rng:
                lo = epoch(rng["gt"])
                n = sum(1 for s in docs.values() if epoch(s.get("updated_at")) > lo)
            else:
                n = len(docs)
            if FAULTS.get("freeze_break") and idx == "bench-es9":
                # A writer that never stopped: each sample sees one more doc
                # than the last. Mutating after n is computed is what makes
                # two consecutive samples disagree.
                k = COUNTERS["cnt"] = COUNTERS.get("cnt", 0) + 1
                docs["late-%d" % k] = {"id": "late-%d" % k,
                                       "updated_at": "2026-07-2%dT00:00:00Z" % (k % 10)}
            return self._send(200, {"count": n})

        m = re.match(r"^/([^/]+)/_settings$", p)
        if m:
            idx = m.group(1)
            if method == "PUT":
                STORE[idx]["settings"].update(body.get("index", body))
                return self._send(200, {"acknowledged": True})
            return self._send(200, {idx: {"settings": {"index": STORE[idx]["settings"]}}})

        m = re.match(r"^/([^/]+)/_mapping$", p)
        if m:
            idx = m.group(1)
            return self._send(200, {idx: {"mappings": {"_meta": STORE[idx]["meta"]}}})

        m = re.match(r"^/([^/]+)/_refresh$", p)
        if m:
            return self._send(200, {"_shards": {"failed": 0}})

        m = re.match(r"^/([^/]+)(?:/_doc)?/_mget$", p)
        if m:
            idx, docs = m.group(1), STORE[m.group(1)]["docs"]
            out = []
            for i in body.get("ids", []):
                if i in docs:
                    out.append({"_id": i, "found": True, "_source": docs[i]})
                else:
                    out.append({"_id": i, "found": False})
            return self._send(200, {"docs": out})

        m = re.match(r"^/([^/]+)(?:/_doc)?/_bulk$", p)
        if m:
            return self._send(200, self._bulk(m.group(1), raw))

        return self._send(404, {"error": {"type": "no_handler", "reason": p}})

    # ------------------------------------------------------------------ ops --

    def _search(self, idx, body):
        docs = ordered(idx)
        rng = (((body.get("query") or {}).get("range") or {}).get("updated_at") or {})
        sort_spec = body.get("sort") or []
        ids_only = body.get("_source") is False
        size = body.get("size", 10)
        sa = body.get("search_after")

        if body.get("aggs"):
            vals = [s.get("updated_at") for _, s in docs if s.get("updated_at")]
            mx = max(vals) if vals else None
            return {"hits": {"total": {"value": len(docs)}, "hits": []},
                    "aggregations": {"m": {"value": epoch(mx) if mx else None,
                                           "value_as_string": mx}}}

        rows = []
        for pos, (doc_id, src) in enumerate(docs):
            if "gt" in rng and epoch(src.get("updated_at")) <= epoch(rng["gt"]):
                continue
            key = [epoch(src.get("updated_at")), pos] if len(sort_spec) == 2 else [pos]
            rows.append((key, doc_id, src))
        rows.sort(key=lambda r: r[0])

        total = len(rows)
        if sa:
            rows = [r for r in rows if r[0] > list(sa)]
        page = rows[:size]
        hits = []
        for key, doc_id, src in page:
            h = {"_id": doc_id, "sort": key}
            if not ids_only:
                h["_source"] = src
            hits.append(h)
        return {"hits": {"total": {"value": total}, "hits": hits}}

    def _scroll_page(self, sid):
        st = SCROLLS[sid]
        docs = ordered(st["idx"])
        page = docs[st["pos"]:st["pos"] + st["size"]]
        st["pos"] += len(page)
        return {"_scroll_id": sid,
                "hits": {"total": {"value": len(docs)},
                         "hits": [{"_id": i, "sort": [n]} for n, (i, _) in enumerate(page)]}}

    def _bulk(self, idx, raw):
        docs = STORE[idx]["docs"]
        COUNTERS["bulks"] = COUNTERS.get("bulks", 0) + 1
        if FAULTS.get("bulk_fail_after") and COUNTERS["bulks"] > FAULTS["bulk_fail_after"]:
            raise RuntimeError("simulated node failure")
        lines = [l for l in raw.split("\n") if l.strip()]
        items, i = [], 0
        while i < len(lines):
            action = json.loads(lines[i])
            op = next(iter(action))
            meta = action[op]
            if op == "delete":
                found = docs.pop(meta["_id"], None) is not None
                items.append({"delete": {"_id": meta["_id"],
                                         "status": 200 if found else 404}})
                i += 1
            else:
                src = json.loads(lines[i + 1])
                COUNTERS["indexed"] = COUNTERS.get("indexed", 0) + 1
                if FAULTS.get("bulk_429_every") and \
                        COUNTERS["indexed"] % FAULTS["bulk_429_every"] == 0:
                    items.append({"index": {"_id": meta["_id"], "status": 429,
                                            "error": {"type": "es_rejected_execution_exception",
                                                      "reason": "simulated"}}})
                elif FAULTS.get("bulk_fatal_id") == meta["_id"]:
                    items.append({"index": {"_id": meta["_id"], "status": 400,
                                            "error": {"type": "mapper_parsing_exception",
                                                      "reason": "simulated"}}})
                else:
                    docs[meta["_id"]] = src
                    items.append({"index": {"_id": meta["_id"], "status": 200}})
                i += 2
        return {"errors": any(next(iter(v.values())).get("status", 200) >= 300
                              for v in items), "items": items}


def main():
    port = int(sys.argv[1])
    SEED[0] = sys.argv[2]
    state = json.load(open(sys.argv[2]))
    STORE.update(state["store"])
    FAULTS.update(state.get("faults", {}))
    for v in STORE.values():
        v.setdefault("meta", {})
        v.setdefault("settings", {"refresh_interval": "-1"})
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)

    def dump(sig=None, frm=None):
        json.dump({"store": STORE}, open(sys.argv[3], "w"))
    import atexit
    atexit.register(dump)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
