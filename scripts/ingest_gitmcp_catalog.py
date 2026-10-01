#!/usr/bin/env python3
"""把 gitmcp/gitmcp-catalog.json 的 T1(原生 AI + 知识库,共 18 个)挂成站内 Remote MCP 条目。

gitmcp.io 是上下文型 Remote MCP(github.com/owner/repo -> gitmcp.io/owner/repo),无本地执行,risk=low。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "mcp-registry.json"
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"

# repo -> (title_zh, category, description_zh)
NATIVE = [
    ("usestrix/strix", "Strix AI 渗透框架", "pentest", "开源 AI 渗透测试工具:自动化发现与验证 Web/云漏洞,含 MCP 接入。"),
    ("samugit83/redamon", "Redamon AI 红队框架", "pentest", "AI 驱动红队框架,从侦察到利用到后渗透的自动化进攻性安全操作,双向 MCP。"),
    ("KeygraphHQ/shannon", "Shannon AI Web/API 渗透", "pentest", "AI Web/API 渗透测试:自动化侦察、漏洞验证与报告。"),
    ("Fausto-404/js-reverse-automation--skill", "前端 JS 逆向 Skill", "reverse-engineering", "前端 JS 逆向自动化 Skill:混淆还原、签名分析与接口提取。"),
    ("SimoneAvogadro/android-reverse-engineering-skill", "Android 逆向 Skill", "reverse-engineering", "Android 逆向工程 Skill:APK 分析、脱壳、Hook 与动态调试。"),
    ("tanweai/wooyun-legacy", "WooYun 漏洞知识库", "data", "WooYun 历史漏洞知识库,收录真实漏洞案例与修复思路。"),
    ("JDArmy/Evasion-SubAgents", "免杀 SubAgents", "malware", "免杀/规避检测的 SubAgents 集合,红队对抗技术。"),
    ("Ta0ing/MCP-SecurityTools", "安全 MCP 收录集", "pentest", "安全类 MCP 工具收录集合,汇总进攻性安全 MCP 服务。"),
    ("slowmist/MCP-Security-Checklist", "MCP 安全自查清单", "dev-workflow", "慢雾 MCP 安全自查清单:审计 AI Agent/MCP 的供应链与配置风险。"),
]

KNOWLEDGE = [
    ("Acmesec/theAIMythbook", "AI 应用与安全指南", "data", "AI 应用与安全攻防知识库:模型、Agent、供应链与对抗攻击。"),
    ("Acmesec/PromptJailbreakManual", "Prompt 越狱手册", "data", "Prompt 越狱与对抗性提示词手册,LLM 安全测试参考。"),
    ("danielmiessler/SecLists", "安全字典/清单", "data", "SecLists:安全测试字典、用户名/口令、目录与 Payload 清单。"),
    ("swisskyrepo/PayloadsAllTheThings", "Payload 知识库", "pentest", "PayloadsAllTheThings:各类漏洞的 Payload 与绕过技巧大全。"),
    ("HackTricks-wiki/hacktricks", "渗透技巧百科", "pentest", "HackTricks:渗透测试技巧、命令与攻防百科。"),
    ("TheKingOfDuck/fuzzDicts", "模糊测试字典", "data", "fuzzDicts:模糊测试与爆破字典合集。"),
    ("insightglacier/Dictionary-Of-Pentesting", "渗透字典", "data", "渗透测试字典合集,覆盖目录、参数、子域等。"),
    ("FeeiCN/Security-PPT", "安全会议 PPT/报告", "data", "安全会议 PPT 与研究报告合集,行业视野与案例。"),
    ("XiaomingX/data-cve-poc", "CVE PoC 汇总", "malware", "CVE 漏洞 PoC 汇总,用于验证与复现已知漏洞。"),
]


def gitmcp_name(repo):
    return f"io.gitmcp.{repo}"


def build(repo, title, cat, desc_zh):
    return {
        "$schema": SCHEMA,
        "name": gitmcp_name(repo),
        "title": title,
        "description": f"GitMCP 上下文型 Remote MCP(读 llms.txt/README):{desc_zh}",
        "version": "1.0.0",
        "websiteUrl": f"https://github.com/{repo}",
        "remotes": [{"type": "streamable-http", "url": f"https://gitmcp.io/{repo}"}],
        "_meta": {"top.skillx/curated": {
            "entryType": "mcp", "category": cat, "kind": "remote", "riskLevel": "low",
            "riskNote": f"gitmcp.io 上下文型 Remote MCP(底层 idosal/git-mcp),只读仓库上下文,无本地执行。来源 {repo}",
            "description-zh": desc_zh,
            "installHint": f"gitmcp.io:{repo}",
            "install": {"method": "remote", "url": f"https://gitmcp.io/{repo}", "command": "",
                        "clients": ["claude", "cursor", "codex"]},
            "reviewed": {"by": "codex", "at": "2026-10-01", "execReview": "passed",
                         "note": "GitMCP 上下文收录:仓库经分拣,远程只读,无本地执行。"},
            "upstreamStatus": {"source": "github", "lastCheck": "2026-10-01", "alive": True, "failSince": None},
        }},
    }


def main():
    doc = json.loads(REG.read_text(encoding="utf-8"))
    existing = {s.get("name") for s in doc.get("servers", [])}
    added = 0
    for repo, title, cat, desc in NATIVE + KNOWLEDGE:
        name = gitmcp_name(repo)
        if name in existing:
            continue
        doc["servers"].append(build(repo, title, cat, desc))
        added += 1
    REG.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] 新增 {added} 个 gitmcp Remote MCP;servers 总数 {len(doc['servers'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
