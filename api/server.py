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
import os
import re
import sqlite3
import sys
import tarfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
DB = BASE / "stats.db"
CACHE = BASE / "cache"
REGISTRY = json.loads((BASE / "registry.json").read_text(encoding="utf-8"))
MCP_REGISTRY_PATH = BASE.parent / "mcp-registry.json"
MCP_REGISTRY = json.loads(MCP_REGISTRY_PATH.read_text(encoding="utf-8")) if MCP_REGISTRY_PATH.is_file() else {"servers": []}
SITE_DATA = Path(os.environ.get("SITE_DATA", "/www/wwwroot/skillx.yueliai.top/site-data.json"))
RATE_LIMIT = 60  # 次/分钟/IP
UA = {"User-Agent": "skill-x-api/1.0"}
_rate = {}

VERSION = "2026-09-28.1"
VALID_KEY = re.compile(r"^[\w./-]{1,120}$")

CAT_KW = {
    "reverse-engineering": ["逆向", "反编译", "脱壳", "汇编", "ida", "ghidra", "radare", "补丁", "patch", "还原", "破解", "二进制", "固件", "elf", "pe", "exe", "dll", "apk", "so", "安卓", "混淆"],
    "pentest": ["渗透", "漏洞", "越权", "idor", "注入", "sql", "xss", "ssrf", "扫描", "红队", "靶场", "接口", "api", "鉴权", "认证", "oauth", "jwt", "csrf", "上传", "命令执行"],
    "malware": ["样本", "恶意", "病毒", "木马", "后门", "勒索", "c2", "ioc", "yara", "加壳", "免杀", "远控"],
    "forensics": ["内存", "转储", "dump", "进程", "指针", "偏移", "aob", "特征码", "基址", "崩溃"],
    "engineering-hygiene": ["测试", "回归", "验证", "质量", "审查", "纪律", "假红", "污染"],
    "dev-workflow": ["开发", "流程", "工程", "ci", "部署", "调试"],
}


def tokenize(s: str):
    low = (s or "").lower()
    toks = set(w for w in re.findall(r"[a-z0-9][a-z0-9_.-]+", low) if len(w) >= 2)
    zh = re.sub(r"[^\u4e00-\u9fa5]", "", s or "")
    toks.update(zh[i:i + 2] for i in range(len(zh) - 1))
    return toks


def recommend(query: str, top: int = 6):
    if not SITE_DATA.is_file():
        return None
    data = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    toks = tokenize(query)
    low = (query or "").lower()
    cat_boost = {}
    for cat, kws in CAT_KW.items():
        n = sum(1 for k in kws if k in low)
        if n:
            cat_boost[cat] = n * 6
    scored = []
    for sk in data.get("skills", []):
        score, why = 0, set()
        nm = f"{sk.get('name','')} {sk.get('name-zh','')}".lower()
        desc = f"{sk.get('description','')} {sk.get('description-zh','')}".lower()
        for t in toks:
            if t in nm:
                score += 10
                why.add(t)
            elif t in desc:
                score += 3
                why.add(t)
        c = sk.get("category", "")
        if cat_boost.get(c):
            score += cat_boost[c]
            why.add(c)
        if score > 0:
            scored.append({"skill": sk, "score": score, "why": sorted(why)[:6]})
    scored.sort(key=lambda x: -x["score"])
    out = []
    for item in scored[:top]:
        sk = item["skill"]
        out.append({
            "name": sk.get("name"), "name-zh": sk.get("name-zh"), "kind": sk.get("kind"),
            "description": sk.get("description"), "description-zh": sk.get("description-zh"),
            "category": sk.get("category"), "suite": sk.get("suite"), "page": sk.get("page"),
            "install": sk.get("install"), "score": item["score"], "matched": item["why"],
        })
    return out



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


def mcp_passed():
    """只放出人工审查通过的 MCP server,形状对齐官方 Registry 响应。"""
    out = []
    for s in MCP_REGISTRY.get("servers", []):
        cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
        if (cur.get("reviewed") or {}).get("execReview") != "passed":
            continue
        pub = {k: v for k, v in s.items() if k != "_meta"}
        out.append({
            "server": pub,
            "_meta": {
                "top.skillx/curated": {k: cur[k] for k in ("description-zh", "category", "kind", "riskLevel", "installHint") if k in cur},
                "io.modelcontextprotocol.registry/official": {
                    "status": "active",
                    "publishedAt": (cur.get("reviewed") or {}).get("at"),
                    "isLatest": True,
                },
            },
        })
    return out


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
            return self._json({"ok": True, "version": VERSION})
        if not self._guarded():
            return
        if path == "/api/stats":
            return self._json({"counts": all_counts()})
        if path == "/v0/servers":
            qs = urllib.parse.parse_qs(urlparse(self.path).query)
            try:
                limit = max(1, min(int(qs.get("limit", ["100"])[0]), 100))
            except ValueError:
                limit = 100
            items = mcp_passed()
            cursor = qs.get("cursor", [""])[0]
            start = 0
            if cursor:
                for i, it in enumerate(items):
                    if f"{it['server']['name']}:{it['server']['version']}" == cursor:
                        start = i + 1
                        break
            page = items[start:start + limit]
            nxt = None
            if start + limit < len(items) and page:
                nxt = f"{page[-1]['server']['name']}:{page[-1]['server']['version']}"
            return self._json({"servers": page, "metadata": {"nextCursor": nxt, "count": len(page)}})
        if path == "/api/recommend":
            q = urllib.parse.parse_qs(urlparse(self.path).query).get("q", [""])[0]
            if not q.strip():
                return self._json({"error": "missing query param q"}, 400)
            res = recommend(q)
            if res is None:
                return self._json({"error": "site data unavailable"}, 503)
            return self._json({"query": q, "results": res})
        m = re.fullmatch(r"/dl/([\w.-]+/[\w.-]+)/([\w.-]+)\.tar\.gz", path)
        if m:
            return self._dl(m.group(1), m.group(2))
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/download", "/api/recommend", "/api/mcp/install"):
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
        if path == "/api/mcp/install":
            name = str(body.get("name", "")).strip()
            if not name or not VALID_KEY.match(name):
                return self._json({"error": "bad name"}, 400)
            bump(f"mcp:{name}")
            return self._json({"ok": True, "name": name, "n": all_counts().get(f"mcp:{name}", 0)})
        if path == "/api/recommend":
            q = str(body.get("query", "")).strip()
            if not q:
                return self._json({"error": "missing query"}, 400)
            res = recommend(q)
            if res is None:
                return self._json({"error": "site data unavailable"}, 503)
            return self._json({"query": q, "results": res})
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


def watch_reload():
    """源码 mtime 变化时自动重启(部署新版本后无需手动重启进程)。"""
    src = Path(__file__).resolve()
    try:
        mtime = src.stat().st_mtime
    except OSError:
        return
    while True:
        time.sleep(30)
        try:
            if src.stat().st_mtime != mtime:
                print("source changed, reloading…", flush=True)
                os.execv(sys.executable, [sys.executable, str(src)] + sys.argv[1:])
        except OSError:
            continue


def main():
    threading.Thread(target=watch_reload, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", 8787), Handler)
    print("skill-x api listening on 127.0.0.1:8787", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
