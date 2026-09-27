#!/usr/bin/env python3
"""Skill X MCP server 收录器(docs/mcp-onboarding-pipeline.md 的机器化实现,纯标准库)。

用法:
  python scripts/mcp_ingest.py ./server.json [--out mcp-registry.json] [--dry-run]
  python scripts/mcp_ingest.py --registry-name ac.inference.sh/mcp [--out mcp-registry.json]

流程(SOP):读取 server.json -> 官方 schema 结构校验 -> MCP 特有检查(传输类型/密钥声明)
-> upsert mcp-registry.json。与 scripts/ingest.py 同纪律:脚本不自动置 verified,
人工审查(传输风险/密钥声明)由维护者回填 _meta.top.skillx/curated.reviewed。
"""
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "mcp-registry.json"
OFFICIAL_API = "https://registry.modelcontextprotocol.io/v0/servers"
SCHEMA_URL = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
UA = {"User-Agent": "skill-x-mcp-ingest/1.0"}

NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?/[a-z0-9._-]+$")
REGISTRY_TYPES = {"npm", "pypi", "nuget", "oci", "mcpb"}
TRANSPORT_TYPES = {"stdio", "streamable-http", "sse"}
REMOTE_TYPES = {"streamable-http", "sse"}


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


def check_structure(srv: dict) -> list[str]:
    errs = []
    for f in ("name", "description", "version"):
        if not srv.get(f):
            errs.append(f"缺必填字段: {f}")
    if srv.get("name") and not NAME_RE.match(srv["name"]):
        errs.append(f"name 不符合反向 DNS 命名空间格式: {srv['name']}")
    pkgs, remotes = srv.get("packages") or [], srv.get("remotes") or []
    if not pkgs and not remotes:
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


def upsert(srv: dict, out_path: Path, curated: dict):
    doc = {"schemaVersion": 1, "servers": []}
    if out_path.is_file():
        doc = json.loads(out_path.read_text(encoding="utf-8"))
    key = lambda s: (s.get("name"), s.get("version"))
    doc["servers"] = [s for s in doc.get("servers", []) if key(s) != key(srv)]
    srv.setdefault("_meta", {})["top.skillx/curated"] = curated
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
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--") and key in ("out", "registry-name", "version"):
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

    if "registry-name" in opts:
        srv = load_official(opts["registry-name"], opts.get("version"))
        source = f"official-registry:{opts['registry-name']}"
    else:
        srv = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        source = f"local:{args[0]}"

    errs = check_structure(srv)
    if errs:
        print("[!] server.json 结构校验未过:")
        for e in errs:
            print(f"    - {e}")
        return 2

    findings = audit(srv)
    level, note = risk_level(srv, findings)
    curated = {
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
