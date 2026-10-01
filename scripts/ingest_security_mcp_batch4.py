#!/usr/bin/env python3
"""第四批:内存取证 MCP 收录(指路牌)。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "mcp-registry.json"
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"

ENTRIES = [
    dict(owner="bornpresident", repo="Volatility-MCP-Server", title="Volatility MCP Server", type="mcp", cat="forensics",
         zh="Volatility MCP:把 Volatility 3 内存取证框架接入 Agent,做进程分析、恶意检测、载荷重建与 YARA 扫描。",
         note="Volatility 3 内存取证 MCP;MIT;需本机安装 Volatility 3。"),
    dict(owner="0xhackerfren", repo="Windows-Memory-Forensics-MCP", title="Windows Memory Forensics MCP", type="mcp", cat="forensics",
         zh="Windows 内存取证 MCP:33 个工具,用 Volatility 3 / MemProcFS / CLR-SOS 后端分析内存转储。",
         note="Windows 内存取证 MCP;MIT;需 Volatility 3/MemProcFS。"),
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
            "$schema": SCHEMA,
            "name": name,
            "title": e["title"],
            "description": e["note"],
            "version": "1.0.0",
            "websiteUrl": f"https://github.com/{e['owner']}/{e['repo']}",
            "_meta": {
                "top.skillx/curated": {
                    "entryType": e["type"],
                    "category": e["cat"],
                    "kind": "link",
                    "riskLevel": "medium",
                    "riskNote": e["note"] + " 收录为上游指路牌,不镜像代码。",
                    "description-zh": e["zh"],
                    "installHint": f"git clone https://github.com/{e['owner']}/{e['repo']}.git",
                    "install": {
                        "method": "link",
                        "url": f"https://github.com/{e['owner']}/{e['repo']}",
                        "command": f"git clone https://github.com/{e['owner']}/{e['repo']}.git",
                        "clients": ["claude", "cursor", "codex"],
                    },
                    "reviewed": {
                        "by": "codex",
                        "at": "2026-10-01",
                        "execReview": "passed",
                        "note": "自动发现+机审:GitHub 仓库与许可证已核验;收录为指路牌。",
                    },
                    "upstreamStatus": {
                        "source": "github",
                        "lastCheck": "2026-10-01",
                        "alive": True,
                        "failSince": None,
                    },
                }
            },
        }
        doc["servers"].append(server)
        added += 1

    REG.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] 新增 {added} 个条目;servers 总数 {len(doc['servers'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
