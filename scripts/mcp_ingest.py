#!/usr/bin/env python3
"""Skill X 条目收录器(docs/mcp-onboarding-pipeline.md 的机器化实现,纯标准库)。

用法:
  python scripts/mcp_ingest.py ./server.json [--out mcp-registry.json] [--dry-run]
  python scripts/mcp_ingest.py --registry-name ac.inference.sh/mcp [--out mcp-registry.json]
  python scripts/mcp_ingest.py --type plugin ./plugin.json [--out mcp-registry.json] [--dry-run]

流程(SOP):读取 server.json -> 官方 schema 结构校验 -> 类型特有检查
(MCP: 传输类型/密钥声明; plugin: install.url 域名白名单/安装命令)
-> upsert mcp-registry.json。与 scripts/ingest.py 同纪律:脚本不自动置 verified,
人工审查由维护者回填 _meta.top.skillx/curated.reviewed。
条目类型由 curated.entryType 区分:mcp(缺省) | plugin。
"""
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "mcp-registry.json"
OFFICIAL_API = "https://registry.modelcontextprotocol.io/v0/servers"
SCHEMA_URL = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
UA = {"User-Agent": "skill-x-mcp-ingest/1.0"}

NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?/[a-z0-9._-]+$")
REGISTRY_TYPES = {"npm", "pypi", "nuget", "oci", "mcpb"}
TRANSPORT_TYPES = {"stdio", "streamable-http", "sse"}
REMOTE_TYPES = {"streamable-http", "sse"}
ENTRY_TYPES = {"mcp", "plugin"}
INSTALL_METHODS = {"marketplace", "command", "link"}
# plugin install.url 只允许指向官方一手市场/源码域,防钓鱼指路牌
PLUGIN_URL_DOMAINS = {
    "marketplace.visualstudio.com", "open-vsx.org", "github.com",
    "cursor.directory", "cursor.com", "claude.ai", "openai.com",
    "plugins.jetbrains.com", "chromewebstore.google.com",
}


def load_official(name: str, version: str | None = None) -> dict:
    """从官方 Registry 拉一条 server.json 作收录底稿。"""
    url = f"{OFFICIAL_API}/{name}/versions/"
    url = url.rstrip("/")
    if version:
        url = f"{OFFICIAL_API}/{name}/versions/{version}"
    else:
        url = f"{OFFICIAL_API}/{name}/versions/latest"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        doc = json.loads(r.read().decode("utf-8"))
    return doc.get("server", doc)


def check_structure(srv: dict, entry_type: str = "mcp") -> list[str]:
    errs = []
    for f in ("name", "description", "version"):
        if not srv.get(f):
            errs.append(f"缺必填字段: {f}")
    if srv.get("name") and not NAME_RE.match(srv["name"]):
        errs.append(f"name 不符合反向 DNS 命名空间格式: {srv['name']}")
    pkgs, remotes = srv.get("packages") or [], srv.get("remotes") or []
    if entry_type == "plugin":
        if pkgs or remotes:
            errs.append("plugin 条目 packages/remotes 必须为空(指路牌模式,安装面放 curated.install)")
    elif not pkgs and not remotes:
        errs.append("packages 与 remotes 至少要有其一")
    for i, p in enumerate(pkgs):
        if p.get("registryType") not in REGISTRY_TYPES:
            errs.append(f"packages[{i}].registryType 非法: {p.get('registryType')}")
        if not p.get("identifier"):
            errs.append(f"packages[{i}] 缺 identifier")
        t = (p.get("transport") or {}).get("type")
        if t not in TRANSPORT_TYPES:
            errs.append(f"packages[{i}].transport.type 非法: {t}")
    for i, r in enumerate(remotes):
        if r.get("type") not in REMOTE_TYPES:
            errs.append(f"remotes[{i}].type 非法: {r.get('type')}")
        u = r.get("url", "")
        if not u.startswith("https://"):
            errs.append(f"remotes[{i}].url 必须 https: {u}")
    return errs


def audit(srv: dict) -> dict:
    """MCP 特有的两项检查:传输类型安全 + env 密钥声明。"""
    findings = {"stdio": [], "remote": [], "secrets": [], "missingSecretFlag": []}
    for p in srv.get("packages") or []:
        t = (p.get("transport") or {}).get("type")
        rid = f"{p.get('registryType')}:{p.get('identifier')}@{p.get('version', '?')}"
        if t == "stdio":
            findings["stdio"].append(rid)
        for ev in p.get("environmentVariables") or []:
            nm = ev.get("name", "?")
            if ev.get("isSecret"):
                findings["secrets"].append(nm)
            elif re.search(r"KEY|TOKEN|SECRET|PASSWORD|PASSWD", nm, re.I):
                findings["missingSecretFlag"].append(nm)
    for r in srv.get("remotes") or []:
        findings["remote"].append(f"{r.get('type')}:{r.get('url')}")
    return findings


def risk_level(srv: dict, findings: dict) -> tuple[str, str]:
    if findings["stdio"]:
        ids = ";".join(findings["stdio"])
        return ("high", f"包含 stdio 本地包({ids}):安装即在本机执行第三方代码,收录前必须人工审查包供应链")
    if findings["remote"]:
        return ("low", "纯远程连接,不在本机执行代码;注意 URL 与认证头为用户私域配置,不入库")
    return ("medium", "未识别传输形态,需人工确认")


def audit_plugin(srv: dict, install: dict) -> list[str]:
    """plugin 条目检查:install 结构 + url https + 域名白名单 + 安装命令兜底。"""
    errs = []
    method = install.get("method")
    if method not in INSTALL_METHODS:
        errs.append(f"install.method 非法: {method}(可选 {sorted(INSTALL_METHODS)})")
    url = install.get("url") or ""
    cmd = install.get("command") or ""
    if not url and not cmd:
        errs.append("install.url 与 install.command 至少要有其一")
    if url:
        if not url.startswith("https://"):
            errs.append(f"install.url 必须 https: {url}")
        else:
            host = (urlparse(url).hostname or "").lower()
            if not any(host == d or host.endswith("." + d) for d in PLUGIN_URL_DOMAINS):
                errs.append(f"install.url 域名不在白名单: {host}(防钓鱼指路牌;新增域名需人工评审)")
    clients = install.get("clients")
    if clients is not None and not isinstance(clients, list):
        errs.append("install.clients 必须是数组")
    return errs


def plugin_risk(install: dict) -> tuple[str, str]:
    method = install.get("method", "link")
    if method == "marketplace":
        return ("medium", "客户端扩展/插件:安装即在本机客户端内运行第三方代码;指路牌指向官方市场页,收录前需人工确认市场归属")
    if method == "command":
        return ("medium", "命令安装型插件:用户在本机执行安装命令拉取第三方代码;收录前需人工确认命令指向上游官方来源")
    return ("medium", "链接型插件条目:仅指路,不托管本体;收录前需人工确认链接归属官方")


def upsert(srv: dict, out_path: Path, curated: dict):
    doc = {"schemaVersion": 1, "servers": []}
    if out_path.is_file():
        doc = json.loads(out_path.read_text(encoding="utf-8"))
    key = lambda s: (s.get("name"), s.get("version"))
    doc["servers"] = [s for s in doc.get("servers", []) if key(s) != key(srv)]
    meta = srv.setdefault("_meta", {})
    old = meta.get("top.skillx/curated") or {}
    # 重新收录时保留人工已回填的审查/中文描述/分类字段
    if (old.get("reviewed") or {}).get("execReview") == "passed" and (curated.get("reviewed") or {}).get("execReview") != "passed":
        for k in ("reviewed", "description-zh", "category", "installHint"):
            if k in old and (k not in curated or curated.get(k) in (None, "", "uncategorized")):
                curated[k] = old[k]
    meta["top.skillx/curated"] = curated
    doc["servers"].append(srv)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_cli(argv):
    args, opts = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            key = a.lstrip("-")
            if "=" in key:
                k, v = key.split("=", 1)
                opts[k] = v
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--") and key in ("out", "registry-name", "version", "type"):
                opts[key] = argv[i + 1]
                i += 1
            else:
                opts[key] = True
        else:
            args.append(a)
        i += 1
    return args, opts


def main():
    args, opts = parse_cli(sys.argv[1:])
    if not args and "registry-name" not in opts:
        print(__doc__)
        return 1
    out_path = Path(opts.get("out", DEFAULT_OUT))
    dry = "dry-run" in opts
    entry_type = opts.get("type", "mcp")
    if entry_type not in ENTRY_TYPES:
        print(f"[!] --type 非法: {entry_type}(可选 {sorted(ENTRY_TYPES)})")
        return 1
    if entry_type == "plugin" and "registry-name" in opts:
        print("[!] plugin 条目不支持 --registry-name(官方 Registry 只有 MCP server);请提供本地 plugin.json")
        return 1

    if "registry-name" in opts:
        srv = load_official(opts["registry-name"], opts.get("version"))
        source = f"official-registry:{opts['registry-name']}"
    else:
        srv = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        source = f"local:{args[0]}"

    errs = check_structure(srv, entry_type)
    if errs:
        print("[!] server.json 结构校验未过:")
        for e in errs:
            print(f"    - {e}")
        return 2

    if entry_type == "plugin":
        install = ((srv.get("_meta") or {}).get("top.skillx/curated") or {}).get("install") or {}
        perrs = audit_plugin(srv, install)
        if perrs:
            print("[!] plugin install 校验未过:")
            for e in perrs:
                print(f"    - {e}")
            return 2
        level, note = plugin_risk(install)
        curated = {
            "entryType": "plugin",
            "category": "uncategorized",
            "kind": "link",
            "riskLevel": level,
            "riskNote": note,
            "installHint": install.get("command", ""),
            "install": install,
            "reviewed": {"by": None, "at": None, "execReview": "pending",
                         "note": "脚本收录;人工审查市场归属与上游维护状态后回填"},
            "upstreamStatus": {"source": source, "lastCheck": str(date.today()),
                               "alive": True, "failSince": None},
        }
        print(f"\n===== plugin 收录清点报告: {srv['name']}@{srv['version']} =====")
        print(f"来源     : {source}")
        print(f"安装方式 : {install.get('method')} | url={install.get('url', '') or '—'} | command={install.get('command', '') or '—'}")
        print(f"适用客户端: {', '.join(install.get('clients') or []) or '—'}")
        print(f"风险等级 : {level} | {note}")
        print("[!] 人工审查前 verified=pending,不会进入橱窗站与 /v0/servers 输出")
    else:
        findings = audit(srv)
        level, note = risk_level(srv, findings)
        curated = {
            "entryType": "mcp",
            "category": "uncategorized",
            "kind": "remote" if findings["remote"] and not findings["stdio"] else "local",
            "riskLevel": level,
            "riskNote": note,
            "installHint": "",
            "reviewed": {"by": None, "at": None, "execReview": "pending",
                         "note": "脚本收录;人工审查传输风险与密钥声明后回填"},
            "upstreamStatus": {"source": source, "lastCheck": str(date.today()),
                               "alive": True, "failSince": None},
        }
        print(f"\n===== MCP 收录清点报告: {srv['name']}@{srv['version']} =====")
        print(f"来源     : {source}")
        print(f"传输     : stdio={len(findings['stdio'])} remote={len(findings['remote'])}")
        for x in findings["stdio"]:
            print(f"  - stdio : {x}  [高风险:本机执行]")
        for x in findings["remote"]:
            print(f"  - remote: {x}")
        print(f"密钥声明 : {len(findings['secrets'])} 个 isSecret")
        for x in findings["secrets"]:
            print(f"  * {x}")
        if findings["missingSecretFlag"]:
            print(f"[!] 疑似密钥但未标 isSecret: {', '.join(findings['missingSecretFlag'])} (收录前必须修正)")
            return 3
        print(f"风险等级 : {level} | {note}")
        print("[!] 人工审查前 verified=pending,不会进入橱窗站与 /v0/servers 输出")

    if dry:
        print("\n[dry-run] 未写入 mcp-registry.json")
        return 0
    upsert(srv, out_path, curated)
    print(f"\n[+] 已 upsert 到 {out_path} (servers: {len(json.loads(out_path.read_text(encoding='utf-8'))['servers'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
