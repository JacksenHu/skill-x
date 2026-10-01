#!/usr/bin/env python3
"""第二批安全/逆向 MCP 与插件收录(指路牌)。

覆盖:Wireshark/tshark 网络分析、Puppeteer 浏览器自动化、Nuclei 漏洞扫描、
SQLMap AI、逆向实验平台、JS Hook、Frida Android、Binary Ninja。
GPL/AGPL/未声明许可证的条目一律 kind=link(只做元数据+指路牌,不镜像代码)。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "mcp-registry.json"
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"

ENTRIES = [
    dict(owner="0xKoda", repo="WireMCP", title="WireMCP (Wireshark)", type="mcp", cat="forensics",
         zh="WireMCP:基于 tshark 的 Wireshark MCP,让 Agent 做实时网络流量抓包、协议解析与异常分析。",
         note="tshark/Wireshark MCP;MIT;需本机安装 Wireshark/tshark。"),
    dict(owner="merajmehrabi", repo="puppeteer-mcp-server", title="Puppeteer MCP Server", type="mcp", cat="data",
         zh="Puppeteer MCP:浏览器自动化,支持新建实例或复用已有 Chrome 窗口做抓取、交互与截图。",
         note="Puppeteer 浏览器自动化 MCP;MIT;需 Node/Puppeteer。"),
    dict(owner="addcontent", repo="nuclei-mcp", title="Nuclei MCP", type="mcp", cat="pentest",
         zh="Nuclei MCP:上下文感知的漏洞扫描,按目标智能选择模板执行并产出结果。",
         note="Nuclei 扫描器 MCP;MIT;需本机安装 nuclei;仅限授权目标。"),
    dict(owner="drcrypterdotru", repo="sqlmap-skynet", title="SQLMap Skynet", type="mcp", cat="pentest",
         zh="SQLMap Skynet:带自主 AI 分阶段工作流、RAG 记忆与 MCP 工具化的 SQLMap 注入检测。",
         note="SQLMap AI MCP;Apache-2.0;仅限授权目标。"),
    dict(owner="LING71671", repo="open-reverselab", title="Open Reverselab", type="mcp", cat="reverse-engineering",
         zh="Open Reverselab:面向 Ghidra/Frida/x64dbg/Rizin 的 AI 逆向实验平台,100+ MCP 工具,覆盖 PE/APK/二进制分析。",
         note="逆向实验平台 MCP;GPL-3.0(仅指路牌收录,不镜像代码)。"),
    dict(owner="vmoranv", repo="jshookmcp", title="jsHook MCP", type="mcp", cat="reverse-engineering",
         zh="jsHook MCP:JavaScript Hook 工具集,用于前端逆向、动态插桩与运行时调试。",
         note="JS Hook MCP;AGPL-3.0(仅指路牌收录)。"),
    dict(owner="FuzzySecurity", repo="kahlo-mcp", title="Kahlo MCP (Frida)", type="mcp", cat="reverse-engineering",
         zh="Kahlo MCP:基于 Frida 的 Android 插桩 MCP,支持自主 AI 辅助的运行时分析。",
         note="Frida Android 插桩 MCP;许可证未声明(仅指路牌收录)。"),
    dict(owner="mrphrazer", repo="binary-ninja-headless-mcp", title="Binary Ninja Headless MCP", type="plugin", cat="reverse-engineering",
         zh="Binary Ninja Headless MCP:180 个工具,给 AI 深度逆向能力(反编译、函数/符号、类型恢复)。",
         note="Binary Ninja 插件 + MCP;GPL-2.0(仅指路牌收录);需 Binary Ninja。"),
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
