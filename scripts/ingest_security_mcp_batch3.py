#!/usr/bin/env python3
"""第三批:云安全 / 移动逆向 / Web3 智能合约审计 MCP 收录(指路牌)。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "mcp-registry.json"
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"

ENTRIES = [
    dict(owner="badchars", repo="cloud-audit-mcp", title="Cloud Audit MCP", type="mcp", cat="pentest",
         zh="云安全审计 MCP:AWS、Azure、GCP 的错误配置检测,38 个工具、60+ 项检查。",
         note="云配置审计 MCP;MIT;需各云厂商凭据;仅限自有/授权环境。"),
    dict(owner="argus-code-scanning", repo="argus-codescan-mcp", title="Argus CodeScan MCP", type="mcp", cat="dev-workflow",
         zh="Argus:开源安全扫描器,覆盖 SAST、DAST、SCA、密钥、IaC、Terraform、Ansible,走 CLI 与 MCP。",
         note="多面安全扫描 MCP;MIT;适合开发流程与 CI 集成。"),
    dict(owner="leonamvasquez", repo="terraview", title="TerraView", type="mcp", cat="dev-workflow",
         zh="TerraView:对 Terraform 基础设施做静态与上下文安全分析,在 apply 前检测错误配置与合规风险。",
         note="Terraform 安全分析 MCP;MIT。"),
    dict(owner="boy-offi9-inc", repo="hexforge-gateway", title="HexForge Gateway", type="mcp", cat="reverse-engineering",
         zh="HexForge:自托管逆向工作台,编排 jadx/apktool/adb/frida/APKiD,以 MCP 工具暴露给 Agent。",
         note="Android 逆向工作台 MCP;MIT;需本机 Android 逆向工具链。"),
    dict(owner="NoOne-hub", repo="android-reverse-mcp", title="Android Reverse MCP", type="mcp", cat="reverse-engineering",
         zh="Android Reverse MCP:统一无头网关,集成 JADX 语义分析、APKTool 打包/签名/差分。",
         note="Android 逆向网关 MCP;Apache-2.0;需本机 jadx/apktool。"),
    dict(owner="trailofbits", repo="slither-mcp", title="Slither MCP", type="mcp", cat="pentest",
         zh="Slither MCP:对 Solidity 智能合约做静态分析,检测重入、越权、溢出等漏洞。",
         note="Slither Solidity 静态分析 MCP;AGPL-3.0(仅指路牌收录);需 Slither。"),
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
