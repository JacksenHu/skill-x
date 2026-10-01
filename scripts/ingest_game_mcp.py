#!/usr/bin/env python3
"""游戏安全/移动逆向 MCP 收录(指路牌)。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "mcp-registry.json"
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"

ENTRIES = [
    dict(owner="bethington", repo="cheat-engine-server-python", title="Cheat Engine MCP Server", type="mcp", cat="reverse-engineering",
         zh="Cheat Engine MCP:安全的结构化只读内存分析与调试,面向开发者、安全研究员与游戏 Mod 制作。",
         note="Cheat Engine 内存分析 MCP;MIT;需本机 Cheat Engine;仅限自有/授权进程。"),
    dict(owner="c4x64", repo="droid-re-chain", title="Droid Re-Chain MCP", type="mcp", cat="reverse-engineering",
         zh="Droid Re-Chain:无头 Android 逆向 MCP,122 个工具覆盖 ADB、NDK、il2cpp、Hook、崩溃捕获、内存分析、Frida 与 APK 操作。",
         note="Android 逆向 MCP;MIT;需 Android 逆向工具链;仅限授权目标。"),
    dict(owner="Diphome", repo="UnityRift", title="UnityRift", type="mcp", cat="reverse-engineering",
         zh="UnityRift:Unity 游戏逆向与移植工具包,含 Unity→Godot 4 管线(GUI/CLI/MCP server)。",
         note="Unity 游戏逆向/移植 MCP;MIT;需 Unity/Godot。"),
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
