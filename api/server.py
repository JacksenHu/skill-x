#!/usr/bin/env python3
"""Skill X 统计与下载代理后端(零第三方依赖,Python 3.8+ 标准库)。

端点:
  POST /api/download          {"skill":"<name>","action":"copy"} -> 计数+1
  GET  /api/stats             -> {"counts": {"<skill>": n, ...}}
  GET  /api/health            -> {"ok": true}
  GET  /dl/<ns>/<skill>.tar.gz -> 白名单(registry.json)代理上游 codeload:
                                  计数 + 重打包为 <skill>/ 根 + 磁盘缓存

安全:
- 仅监听 127.0.0.1(由 nginx 反代暴露)
- 单 IP 限速 60 次/分钟(超出 429)
- /dl/ 严格白名单,非白名单 403(防开放代理滥用)
- 计数写入参数化 SQL
"""
import io
import json
import re
import sqlite3
import tarfile
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
DB = BASE / "stats.db"
CACHE = BASE / "cache"
REGISTRY = json.loads((BASE / "registry.json").read_text(encoding="utf-8"))
RATE_LIMIT = 60  # 次/分钟/IP
UA = {"User-Agent": "skill-x-api/1.0"}
_rate = {}

VALID_KEY = re.compile(r"^[\w./-]{1,120}$")


def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS counts(skill TEXT PRIMARY KEY, n INTEGER NOT NULL DEFAULT 0, updated TEXT)")
    return conn


def bump(skill: str):
    conn = db()
    with conn:
        conn.execute(
            "INSERT INTO counts(skill, n, updated) VALUES(?, 1, datetime('now')) "
            "ON CONFLICT(skill) DO UPDATE SET n = n + 1, updated = datetime('now')",
            (skill,))
    conn.close()


def all_counts():
    conn = db()
    rows = conn.execute("SELECT skill, n FROM counts").fetchall()
    conn.close()
    return {k: v for k, v in rows}


def rate_ok(ip: str) -> bool:
    now = time.time()
    hits = [t for t in _rate.get(ip, []) if now - t < 60]
    if len(hits) >= RATE_LIMIT:
        _rate[ip] = hits
        return False
    hits.append(now)
    _rate[ip] = hits
    return True


def find_suite(ns: str):
    for suite in REGISTRY.get("suites", []):
        if suite.get("namespace") == ns:
            return suite
    return None


def fetch_repack(suite, skill: str) -> bytes:
    """下载上游 tarball,抽出 skills/<skill>/,重打包为 <skill>/ 根。"""
    owner, repo = suite["namespace"].split("/", 1)
    branch = suite.get("branch", "main")
    url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{branch}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    prefix = None
    want_suffix = f"skills/{skill}/SKILL.md"
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf_probe:
        for m in tf_probe.getmembers():
            if m.isfile() and m.name.endswith(want_suffix):
                prefix = m.name[: -len("SKILL.md")]
                break
    out = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf_in, \
         tarfile.open(fileobj=out, mode="w:gz") as tf_out:
        if not prefix:
            raise FileNotFoundError(f"skill {skill} not found in upstream tarball")
        for m in tf_in.getmembers():
            if not m.name.startswith(prefix):
                continue
            rel = m.name[len(prefix):]
            if not rel:
                continue
            m2 = tarfile.TarInfo(f"{skill}/{rel}")
            m2.type, m2.mode, m2.mtime = m.type, m.mode, m.mtime
            if m.isdir():
                tf_out.addfile(m2)
            elif m.isreg():
                m2.size = m.size
                tf_out.addfile(m2, tf_in.extractfile(m))
    return out.getvalue()


class Handler(BaseHTTPRequestHandler):
    server_version = "SkillX/1.0"

    def log_message(self, fmt, *args):
        pass

    def _ip(self):
        return self.headers.get("X-Real-IP") or self.client_address[0]

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _guarded(self):
        if not rate_ok(self._ip()):
            self._json({"error": "rate limited"}, 429)
            return False
        return True

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._json({"ok": True})
        if not self._guarded():
            return
        if path == "/api/stats":
            return self._json({"counts": all_counts()})
        m = re.fullmatch(r"/dl/([\w.-]+/[\w.-]+)/([\w.-]+)\.tar\.gz", path)
        if m:
            return self._dl(m.group(1), m.group(2))
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/download":
            return self._json({"error": "not found"}, 404)
        if not self._guarded():
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 4096:
                return self._json({"error": "payload too large"}, 413)
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._json({"error": "bad json"}, 400)
        skill = str(body.get("skill", "")).strip()
        if not skill or not VALID_KEY.match(skill):
            return self._json({"error": "bad skill"}, 400)
        bump(skill)
        self._json({"ok": True, "skill": skill, "n": all_counts().get(skill, 0)})

    def _dl(self, ns: str, skill: str):
        suite = find_suite(ns)
        if not suite or skill not in (suite.get("skills") or []):
            return self._json({"error": "not in whitelist"}, 403)
        CACHE.mkdir(exist_ok=True)
        cache_file = CACHE / f"{ns.replace('/', '--')}--{skill}.tar.gz"
        bump(f"{ns}/{skill}")
        if cache_file.is_file():
            data = cache_file.read_bytes()
        else:
            try:
                data = fetch_repack(suite, skill)
            except Exception as e:  # noqa: BLE001
                return self._json({"error": f"upstream fetch failed: {e}"}, 502)
            cache_file.write_bytes(data)
        self.send_response(200)
        self.send_header("Content-Type", "application/gzip")
        self.send_header("Content-Disposition", f'attachment; filename="{skill}.tar.gz"')
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 8787), Handler)
    print("skill-x api listening on 127.0.0.1:8787")
    srv.serve_forever()


if __name__ == "__main__":
    main()
