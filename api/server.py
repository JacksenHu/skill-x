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
PACKS_REGISTRY_PATH = Path(os.environ.get("PACKS_REGISTRY", BASE.parent / "packs.json"))
PACKS_REGISTRY = json.loads(PACKS_REGISTRY_PATH.read_text(encoding="utf-8")) if PACKS_REGISTRY_PATH.is_file() else {"packs": []}
SITE_DATA = Path(os.environ.get("SITE_DATA", "/www/wwwroot/skillx.yueliai.top/site-data.json"))
RATE_LIMIT = 60  # 次/分钟/IP
UA = {"User-Agent": "skill-x-api/1.0"}
_rate = {}

VERSION = "2026-10-02.3"
VALID_KEY = re.compile(r"^[\w./-]{1,120}$")

CAT_KW = {
    "reverse-engineering": ["逆向", "反编译", "脱壳", "汇编", "ida", "ghidra", "radare", "补丁", "patch", "还原", "破解", "二进制", "固件", "elf", "pe", "exe", "dll", "apk", "so", "安卓", "混淆"],
    "pentest": ["渗透", "漏洞", "越权", "idor", "注入", "sql", "xss", "ssrf", "扫描", "红队", "靶场", "接口", "api", "鉴权", "认证", "oauth", "jwt", "csrf", "上传", "命令执行"],
    "malware": ["样本", "恶意", "病毒", "木马", "后门", "勒索", "c2", "ioc", "yara", "加壳", "免杀", "远控"],
    "forensics": ["内存", "转储", "dump", "进程", "指针", "偏移", "aob", "特征码", "基址", "崩溃"],
    "engineering-hygiene": ["测试", "回归", "验证", "质量", "审查", "纪律", "假红", "污染"],
    "dev-workflow": ["开发", "流程", "工程", "ci", "部署", "调试"],
}


def gitmcp_url(website_url: str) -> str:
    """github.com/owner/repo -> gitmcp.io/owner/repo(即时 AI 上下文)。"""
    if not website_url:
        return ""
    m = re.match(r"https?://(?:www\.)?github\.com/([\w.-]+/[\w.-]+)", website_url)
    return f"https://gitmcp.io/{m.group(1)}" if m else ""


SKILL_TARGET_DIRS = {
    "claude": "~/.claude/skills/{name}/",
    "codex": ".agents/skills/{name}/",
    "cursor": ".cursor/skills/{name}/",
    "gemini": "~/.gemini/skills/{name}/",
    "generic": "<skillsRoot>/{name}/",
}

MCP_CONFIG_PATHS = {
    "claude": "~/.claude/.mcp.json",
    "cursor": "~/.cursor/mcp.json",
    "codex": "~/.codex/config.toml 的 mcp_servers 段",
    "vscode": ".vscode/mcp.json",
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
    for pk in data.get("packs", []):
        score, why = 0, set()
        pers = pk.get("persona") or {}
        nm = f"{pk.get('displayName','')} {pk.get('displayNameEn','')} {pk.get('slug','')} {pk.get('skill','')}".lower()
        desc = f"{pk.get('summary','')} {pers.get('role','')} {pers.get('tagline','')}".lower()
        mrefs = " ".join(f"{m.get('ref','')} {m.get('name','')}" for m in pk.get("members", [])).lower()
        for t in toks:
            if t in nm:
                score += 10
                why.add(t)
            elif t in desc or t in mrefs:
                score += 3
                why.add(t)
        c = pers.get("scene", "")
        if cat_boost.get(c):
            score += cat_boost[c]
            why.add(c)
        if score > 0:
            scored.append({"pack": pk, "score": score + 2, "why": sorted(why)[:6]})  # 编排层优先 +2
    scored.sort(key=lambda x: -x["score"])
    out = []
    for item in scored[:top]:
        if "pack" in item:
            pk = item["pack"]
            pers = pk.get("persona") or {}
            out.append({
                "name": pk.get("skill") or pk.get("slug"),
                "name-zh": pk.get("displayName"),
                "kind": "pack",
                "description": pk.get("summaryEn", ""),
                "description-zh": pk.get("summary", ""),
                "category": pers.get("scene", ""),
                "suite": None,
                "page": pk.get("page", ""),
                "install": pk.get("installPrompt", ""),
                "score": item["score"], "matched": item["why"],
            })
            continue
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
    """只放出人工审查通过的条目(MCP/plugin),形状对齐官方 Registry 响应。"""
    out = []
    for s in MCP_REGISTRY.get("servers", []):
        cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
        if (cur.get("reviewed") or {}).get("execReview") != "passed":
            continue
        pub = {k: v for k, v in s.items() if k != "_meta"}
        out.append({
            "server": pub,
            "_meta": {
                "top.skillx/curated": {k: cur[k] for k in ("description-zh", "category", "kind", "riskLevel", "installHint", "entryType") if k in cur},
                "io.modelcontextprotocol.registry/official": {
                    "status": "active",
                    "publishedAt": (cur.get("reviewed") or {}).get("at"),
                    "isLatest": True,
                },
            },
        })
    return out


def mcp_find(name: str):
    """按 name 找已过审条目(原始 server.json + curated)。"""
    for s in MCP_REGISTRY.get("servers", []):
        if s.get("name") != name:
            continue
        cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
        if (cur.get("reviewed") or {}).get("execReview") == "passed":
            return s, cur
    return None, None


def mcp_install_descriptor(name: str):
    """生成应用程序可直接用于 安装/连接 的结构化描述。
    远程型:config={type,url};本地型:config={command,args,env}。
    clientSnippets 给主流客户端可直接写入其 MCP 配置的 JSON 片段。
    requiredSecrets 声明应用需向用户收集哪些密钥(不落库)。"""
    s, cur = mcp_find(name)
    if not s:
        return None
    pkgs = s.get("packages") or []
    remotes = s.get("remotes") or []
    title = s.get("title") or name
    short = name.split("/")[-1]
    secrets = []
    install = cur.get("install") or {}
    if not pkgs and not remotes:
        # plugin 指路牌条目:无包无端点,只返回官方安装指引
        if not install:
            return None
        kind = "link"
        config = {"method": install.get("method", "link"), "command": install.get("command", ""), "url": install.get("url", "")}
        client_snippets = {}
    elif remotes:
        r = remotes[0]
        kind = "remote"
        config = {"type": r.get("type", "streamable-http"), "url": r.get("url", "")}
        for h in r.get("headers") or []:
            if h.get("isSecret"):
                secrets.append({"name": h.get("name"), "description": h.get("description", ""), "isRequired": bool(h.get("isRequired"))})
        client_snippets = {
            "claude": {"mcpServers": {short: {"type": "http", "url": config["url"]}}},
            "cursor": {"mcpServers": {short: {"url": config["url"]}}},
            "codex": {"mcp_servers": {short: {"url": config["url"]}}},
            "vscode": {"servers": {short: {"type": "http", "url": config["url"]}}},
        }
    elif pkgs:
        p = pkgs[0]
        kind = "local"
        rt = p.get("registryType", "npm")
        ident = p.get("identifier", "")
        ver = p.get("version", "")
        runner = {"npm": "npx", "pypi": "uvx", "nuget": "dnx", "oci": "docker", "mcpb": "mcpb"}.get(rt, "npx")
        if runner == "npx":
            args = ["-y", f"{ident}@{ver}" if ver else ident]
        elif runner == "uvx":
            args = [f"{ident}=={ver}" if ver else ident]
        else:
            args = [ident]
        for a in p.get("packageArguments") or []:
            if a.get("type") == "positional":
                args.append(a.get("value", ""))
        env = {}
        for ev in p.get("environmentVariables") or []:
            env[ev.get("name", "")] = ""
            if ev.get("isSecret"):
                secrets.append({"name": ev.get("name"), "description": ev.get("description", ""), "isRequired": bool(ev.get("isRequired"))})
        config = {"command": runner, "args": args, "env": env}
        client_snippets = {
            "claude": {"mcpServers": {short: {"command": runner, "args": args, "env": env}}},
            "cursor": {"mcpServers": {short: {"command": runner, "args": args, "env": env}}},
            "codex": {"mcp_servers": {short: {"command": runner, "args": args, "env": env}}},
            "vscode": {"servers": {short: {"type": "stdio", "command": runner, "args": args, "env": env}}},
        }
    gm = gitmcp_url(s.get("websiteUrl") or "")
    copy_config = ({"mcpServers": {short: {"type": "http", "url": gm}}} if gm
                   else (client_snippets.get("claude") or {}))
    return {
        "name": name, "title": title, "version": s.get("version", ""), "kind": kind,
        "entryType": cur.get("entryType", "mcp"),
        "install": install,
        "config": config,
        "requiredSecrets": secrets,
        "clientSnippets": client_snippets,
        "gitmcpUrl": gm,
        "copyConfig": copy_config,
        "configPaths": MCP_CONFIG_PATHS,
        "riskLevel": cur.get("riskLevel", "medium"),
        "riskNote": cur.get("riskNote", ""),
    }


def pack_passed():
    """只放出人工审查通过的专家团。"""
    return [p for p in PACKS_REGISTRY.get("packs", [])
            if (p.get("reviewed") or {}).get("execReview") == "passed"]


def pack_find(slug: str):
    """按 slug 找已过审专家团。"""
    for p in PACKS_REGISTRY.get("packs", []):
        if p.get("slug") == slug and (p.get("reviewed") or {}).get("execReview") == "passed":
            return p
    return None


def pack_public(p, detail: bool = False):
    """对外专家团形状:列表只放摘要;详情含完整成员安装描述符(含 MCP 接入描述)。"""
    members = []
    for m in p.get("members") or []:
        item = {
            "type": m.get("type"), "ref": m.get("ref"),
            "name": m.get("name", m.get("ref")),
            "title": m.get("title", m.get("ref")),
            "resolved": bool(m.get("resolved")),
            "optional": bool(m.get("optional")),
        }
        if detail:
            item.update({
                "description-zh": m.get("description-zh", ""),
                "category": m.get("category", ""),
                "page": m.get("page", ""),
                "install": m.get("install", ""),
                "installPath": m.get("installPath", ""),
                "note": m.get("note", ""),
            })
            if m.get("type") == "mcp" and m.get("resolved"):
                d = mcp_install_descriptor(m.get("ref"))
                if d:
                    item["mcpInstall"] = d
        members.append(item)
    out = {
        "slug": p.get("slug"),
        "displayName": p.get("displayName"),
        "displayNameEn": p.get("displayNameEn"),
        "persona": p.get("persona") or {},
        "summary": p.get("summary", ""),
        "summaryEn": p.get("summaryEn", ""),
        "origin": p.get("origin", "own"),
        "skill": p.get("skill", ""),
        "install": p.get("install", ""),
        "upstream": p.get("upstream"),
        "license": (p.get("license") or {}).get("spdx", ""),
        "memberCount": len(members),
        "degraded": bool(p.get("degraded")),
        "missingMembers": p.get("missingMembers") or [],
        "members": members,
        "page": f"/packages/{p.get('slug')}.html",
        "installDoc": "/install/pack-install.md",
        "gitmcpUrl": gitmcp_url(p.get("upstream") or "https://github.com/JacksenHu/skill-x"),
        "copyConfig": {"mcpServers": {"skill-x": {"type": "http", "url": "https://gitmcp.io/JacksenHu/skill-x"}}},
        "skillTargetDirs": SKILL_TARGET_DIRS,
        "reviewed": p.get("reviewed") or {},
        "upstreamStatus": p.get("upstreamStatus") or {},
    }
    if detail:
        out["content"] = p.get("content", "")
        out["installMd"] = f"/v0/packs/{p.get('slug')}/install.md"
    return out


def pack_install_md(p) -> str:
    """生成专家团专属安装契约(markdown,给 Agent 读的完整安装步骤)。"""
    slug = p.get("slug")
    persona = p.get("persona") or {}
    members = p.get("members") or []
    counts = {}
    for m in members:
        counts[m.get("type")] = counts.get(m.get("type"), 0) + 1
    L = [f"# 专家团安装契约:{p.get('displayName')}({p.get('displayNameEn')}, {slug})",
         "",
         f"> 来源:https://skillx.yueliai.top/v0/packs/{slug}",
         "", "## 专家团", "",
         f"- 角色:{persona.get('role', '')}",
         f"- 简介:{p.get('summary', '')}",
         "- 成员:{n} 个(自研 {own} / 收录 {ext} / MCP {mcp})".format(
             n=len(members), own=counts.get("own-skill", 0), ext=counts.get("ext-skill", 0), mcp=counts.get("mcp", 0)),
         ]
    if p.get("degraded"):
        L.append(f"- 注意:成员暂不可用({', '.join(p.get('missingMembers') or [])}),安装时跳过并说明")
    L += ["", "## 安装步骤", ""]
    idx = 1
    if p.get("install"):
        L += [f"### 第 {idx} 步:安装专家团编排技能(meta-skill)", "", "```bash", p["install"], "```", ""]
        idx += 1
    L += [f"### 第 {idx} 步:按顺序安装成员", ""]
    for i, m in enumerate(members, 1):
        title = m.get("title") or m.get("ref")
        L.append(f"#### {idx}.{i} {title}({m.get('type')}: {m.get('ref')})")
        L.append("")
        if not m.get("resolved"):
            L += ["- 状态:不可用(已下架/未收录),跳过并向用户说明。", ""]
            continue
        if m.get("type") == "mcp":
            L += [f"- 取接入描述:`GET /v0/servers/{m.get('ref')}/install`(含 claude/cursor/codex/vscode 客户端片段)。",
                  "- 需要密钥时向用户索要;密钥只在本地写入客户端配置,不经过本站。", ""]
            continue
        cmd = m.get("install") or ""
        if cmd:
            L += ["```bash", cmd, "```", ""]
        else:
            L += [f"- 无标准安装命令;详情页:{m.get('page') or '(见专家团详情)'}", ""]
    L += [f"### 第 {idx + 1} 步:回报安装(可选)", "",
          "```bash",
          f"curl -s -X POST -H \"Content-Type: application/json\" -d '{{\"slug\":\"{slug}\"}}' https://skillx.yueliai.top/api/pack/install",
          "```", "",
          "## 失败与回退", "",
          "- 单个成员失败:记录原因,继续安装其余成员,最后汇总。",
          "- API 不可达:改用橱窗页人工指引。",
          "- 自研成员无 GITHUB_TOKEN:跳过自研成员,只装收录成员,并向用户说明。", "",
          "## 验收", "",
          "安装完成后逐项报告:已装成员(名称/类型/安装方式)、未装成员及原因、专家团 meta-skill 是否可被 Agent 加载。", ""]
    return "\n".join(L) + "\n"


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

    def _text(self, text, ctype="text/plain; charset=utf-8", code=200):
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
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
        if path == "/v0/packs":
            qs = urllib.parse.parse_qs(urlparse(self.path).query)
            try:
                limit = max(1, min(int(qs.get("limit", ["100"])[0]), 100))
            except ValueError:
                limit = 100
            items = pack_passed()
            cursor = qs.get("cursor", [""])[0]
            start = 0
            if cursor:
                for i, it in enumerate(items):
                    if it.get("slug") == cursor:
                        start = i + 1
                        break
            page_packs = items[start:start + limit]
            nxt_pack = None
            if start + limit < len(items) and page_packs:
                nxt_pack = page_packs[-1].get("slug")
            return self._json({"packs": [pack_public(p) for p in page_packs],
                               "metadata": {"nextCursor": nxt_pack, "count": len(page_packs)}})
        m_pack_md = re.fullmatch(r"/v0/packs/([a-z0-9-]{3,41})/install\.md", path)
        if m_pack_md:
            p = pack_find(m_pack_md.group(1))
            if not p:
                return self._json({"error": "pack not found or not reviewed"}, 404)
            return self._text(pack_install_md(p), "text/markdown; charset=utf-8")
        m_pack = re.fullmatch(r"/v0/packs/([a-z0-9-]{3,41})", path)
        if m_pack:
            p = pack_find(m_pack.group(1))
            if not p:
                return self._json({"error": "pack not found or not reviewed"}, 404)
            return self._json(pack_public(p, detail=True))
        m_inst = re.fullmatch(r"/v0/servers/([\w.-]+(?:/[\w.-]+)?)/install", path)
        if m_inst:
            d = mcp_install_descriptor(m_inst.group(1))
            if not d:
                return self._json({"error": "server not found or not reviewed"}, 404)
            return self._json(d)
        if path == "/api/recommend":
            qs = urllib.parse.parse_qs(urlparse(self.path).query)
            q = (qs.get("q") or qs.get("query") or [""])[0]
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
        if path not in ("/api/download", "/api/recommend", "/api/mcp/install", "/api/mcp/connect",
                        "/api/plugin/install", "/api/pack/install"):
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
        if path == "/api/mcp/connect":
            name = str(body.get("name", "")).strip()
            client = str(body.get("client", "claude")).strip().lower()
            secrets = body.get("secrets") or {}
            if not name or not VALID_KEY.match(name):
                return self._json({"error": "bad name"}, 400)
            d = mcp_install_descriptor(name)
            if not d:
                return self._json({"error": "server not found or not reviewed"}, 404)
            if client not in d["clientSnippets"]:
                return self._json({"error": f"unsupported client, use one of {sorted(d['clientSnippets'])}"}, 400)
            missing = [s["name"] for s in d["requiredSecrets"] if s.get("isRequired") and not secrets.get(s["name"])]
            if missing:
                return self._json({"error": "missing required secrets", "missing": missing}, 400)
            # 内存中把密钥填进客户端片段返回;不落库、不写日志
            snippet = json.loads(json.dumps(d["clientSnippets"][client]))
            srv_key = next(iter(next(iter(snippet.values())).keys()))
            node = next(iter(snippet.values()))[srv_key]
            if d["kind"] == "local":
                node.setdefault("env", {})
                for k, v in secrets.items():
                    if k in node["env"] or any(s["name"] == k for s in d["requiredSecrets"]):
                        node["env"][k] = v
            else:
                if secrets:
                    node.setdefault("headers", {})
                    for k, v in secrets.items():
                        node["headers"][k] = v
            bump(f"mcp-connect:{name}")
            return self._json({"ok": True, "name": name, "client": client, "configSnippet": snippet, "n": all_counts().get(f"mcp-connect:{name}", 0)})
        if path == "/api/mcp/install":
            name = str(body.get("name", "")).strip()
            if not name or not VALID_KEY.match(name):
                return self._json({"error": "bad name"}, 400)
            bump(f"mcp:{name}")
            return self._json({"ok": True, "name": name, "n": all_counts().get(f"mcp:{name}", 0)})
        if path == "/api/plugin/install":
            name = str(body.get("name", "")).strip()
            if not name or not VALID_KEY.match(name):
                return self._json({"error": "bad name"}, 400)
            s, cur = mcp_find(name)
            if not s or cur.get("entryType", "mcp") != "plugin":
                return self._json({"error": "plugin not found or not reviewed"}, 404)
            bump(f"plugin:{name}")
            return self._json({"ok": True, "name": name, "n": all_counts().get(f"plugin:{name}", 0)})
        if path == "/api/pack/install":
            slug = str(body.get("slug", "")).strip()
            if not slug or not re.fullmatch(r"[a-z0-9-]{3,41}", slug):
                return self._json({"error": "bad slug"}, 400)
            if not pack_find(slug):
                return self._json({"error": "pack not found or not reviewed"}, 404)
            bump(f"pack:{slug}")
            return self._json({"ok": True, "slug": slug, "n": all_counts().get(f"pack:{slug}", 0)})
        if path == "/api/recommend":
            q = str(body.get("query") or body.get("q") or "").strip()
            if not q:
                return self._json({"error": "missing query"}, 400)
            res = recommend(q)
            if res is None:
                return self._json({"error": "site data unavailable"}, 503)
            return self._json({"query": q, "results": res})
        action = str(body.get("action", "copy")).strip()[:24]
        skill = str(body.get("skill", "")).strip()
        if not skill or not VALID_KEY.match(skill):
            return self._json({"error": "bad skill"}, 400)
        bump(skill)
        self._json({"ok": True, "skill": skill, "action": action, "n": all_counts().get(skill, 0)})

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
