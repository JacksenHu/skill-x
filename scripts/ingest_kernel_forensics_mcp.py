#!/usr/bin/env python3
"""Windows 内核/驱动调试 与 取证/应急响应 MCP 收录(指路牌)。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "mcp-registry.json"
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"

ENTRIES = [
    dict(owner="NadavLor", repo="windbg-ext-mcp", title="WinDbg Ext MCP", type="mcp", cat="reverse-engineering",
         zh="WinDbg-ext-MCP:把 LLM 客户端接到 WinDbg,做实时 AI 辅助内核调试与崩溃分析。",
         note="WinDbg 内核调试 MCP;MIT;需 WinDbg。"),
    dict(owner="gengstah", repo="windbg-mcp", title="WinDbg MCP (pybag)", type="mcp", cat="reverse-engineering",
         zh="WinDbg MCP:把 pybag Windows 调试器函数暴露为 MCP 工具,控制用户态进程、内核会话与崩溃转储分析。",
         note="WinDbg/pybag 调试 MCP;许可证未声明(仅指路牌收录)。"),
    dict(owner="Letenz", repo="windows-drv-harness", title="Windows Driver Harness", type="mcp", cat="reverse-engineering",
         zh="Windows Driver Harness:测试驱动内核驱动的内循环,快照回滚→部署→测试→比对→修复,MCP+VMware+WinDbg。",
         note="Windows 驱动测试/调试 MCP;MIT;需 VMware/WinDbg。"),
    dict(owner="nebulae", repo="trudi", title="Trudi (DFIR Agent)", type="mcp", cat="forensics",
         zh="Trudi:自主 DFIR Agent,SANS SIFT 工作站 MCP,面向应急响应。",
         note="DFIR 应急响应 MCP;MIT;需 SANS SIFT 工具集。"),
    dict(owner="M507", repo="AI-SOC-Agent", title="AI SOC Agent MCP", type="mcp", cat="forensics",
         zh="AI SOC Agent:自动化安全调查、告警分诊与应急响应 MCP,集成 ELK、IRIS 等平台。",
         note="SOC/IR 自动化 MCP;MIT;需 ELK/IRIS。"),
    dict(owner="thomasxm", repo="CrowdSentinels-AI-MCP", title="CrowdSentinels AI MCP", type="mcp", cat="forensics",
         zh="CrowdSentinels AI:面向 Elasticsearch/OpenSearch 的 AI 威胁狩猎与应急响应 MCP。",
         note="威胁狩猎/IR MCP;GPL-3.0(仅指路牌收录);需 Elasticsearch/OpenSearch。"),
    dict(owner="bornpresident", repo="MISP-MCP-SERVER", title="MISP MCP Server", type="mcp", cat="malware",
         zh="MISP MCP:把 MISP 威胁情报平台接入 LLM,提供情报检索与关联能力。",
         note="MISP 威胁情报 MCP;许可证未声明(仅指路牌收录);需 MISP 实例。"),
]


def main():
    doc = json.loads(REG.read_text(encoding="utf-8"))
    existing = {s.get("name") for s in doc.get("servers", [])}
    added = 0
    for e in ENTRIES:
        name = f"io.github.{e['owner']}/{e['repo']}"
        if name in existing:
            continue
        server = {
            "$schema": SCHEMA, "name": name, "title": e["title"], "description": e["note"], "version": "1.0.0",
            "websiteUrl": f"https://github.com/{e['owner']}/{e['repo']}",
            "_meta": {"top.skillx/curated": {
                "entryType": e["type"], "category": e["cat"], "kind": "link", "riskLevel": "medium",
                "riskNote": e["note"] + " 收录为上游指路牌,不镜像代码。",
                "description-zh": e["zh"],
                "installHint": f"git clone https://github.com/{e['owner']}/{e['repo']}.git",
                "install": {"method": "link", "url": f"https://github.com/{e['owner']}/{e['repo']}",
                            "command": f"git clone https://github.com/{e['owner']}/{e['repo']}.git",
                            "clients": ["claude", "cursor", "codex"]},
                "reviewed": {"by": "codex", "at": "2026-10-01", "execReview": "passed",
                             "note": "自动发现+机审:GitHub 仓库与许可证已核验;收录为指路牌。"},
                "upstreamStatus": {"source": "github", "lastCheck": "2026-10-01", "alive": True, "failSince": None},
            }},
        }
        doc["servers"].append(server)
        added += 1
    REG.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] 新增 {added} 个条目;servers 总数 {len(doc['servers'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
