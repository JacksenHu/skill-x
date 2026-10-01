#!/usr/bin/env python3
"""把已筛选的安全/逆向/爬虫 MCP 服务与插件收录进 mcp-registry.json(指路牌)。

只 upsert 一次,已存在同名条目不覆盖。许可证/仓库已在收录前经 GitHub API 核验。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "mcp-registry.json"
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"

ENTRIES = [
    dict(owner="0x4m4", repo="hexstrike-ai", title="HexStrike AI", type="mcp", cat="pentest",
         zh="HexStrike AI:让 Agent 自主调用 150+ 网络安全工具,做自动化渗透、漏洞发现与漏洞赏金。",
         note="聚合 150+ 渗透工具的 MCP server;MIT;本地运行,仅限授权目标。",
         install="git clone https://github.com/0x4m4/hexstrike-ai.git"),
    dict(owner="mukul975", repo="cve-mcp-server", title="CVE Intelligence MCP", type="mcp", cat="malware",
         zh="CVE 情报 MCP:27 个工具覆盖 21 个 API,CVE 查询、EPSS、CISA KEV、MITRE ATT&CK、Shodan、VirusTotal。",
         note="威胁情报聚合 MCP;Apache-2.0;需配置各 API 密钥。",
         install="git clone https://github.com/mukul975/cve-mcp-server.git"),
    dict(owner="FuzzingLabs", repo="mcp-security-hub", title="Security Hub MCP", type="mcp", cat="pentest",
         zh="安全工具 MCP 合集:Nmap、Ghidra、Nuclei、SQLMap、Hashcat 等进攻性安全工具接入 AI。",
         note="进攻性安全工具 MCP 合集;MIT;仅限授权目标。",
         install="git clone https://github.com/FuzzingLabs/mcp-security-hub.git"),
    dict(owner="cyproxio", repo="mcp-for-security", title="MCP for Security", type="mcp", cat="pentest",
         zh="安全 MCP 合集:SQLMap、FFUF、Nmap、Masscan 等常用渗透工具接入 AI 工作流。",
         note="渗透工具 MCP 合集;MIT;仅限授权测试。",
         install="git clone https://github.com/cyproxio/mcp-for-security.git"),
    dict(owner="radareorg", repo="radare2-mcp", title="radare2 MCP", type="mcp", cat="reverse-engineering",
         zh="官方 radare2 MCP:让 Agent 驱动 radare2 做二进制反汇编、函数分析与符号重命名。",
         note="官方 radare2 stdio MCP;MIT;需本机安装 radare2。",
         install="git clone https://github.com/radareorg/radare2-mcp.git"),
    dict(owner="dnakov", repo="frida-mcp", title="Frida MCP", type="mcp", cat="reverse-engineering",
         zh="Frida MCP:让 Agent 驱动 Frida 做动态插桩、Hook、内存读写与运行时分析。",
         note="Frida stdio MCP;MIT;需本机安装 frida。",
         install="git clone https://github.com/dnakov/frida-mcp.git"),
    dict(owner="sjkim1127", repo="Reversecore_MCP", title="Reversecore MCP", type="mcp", cat="reverse-engineering",
         zh="Reversecore:基于 Radare2/YARA/LIEF/Capstone 的逆向、恶意样本、取证、漏洞研究与 SAST 一体化 MCP。",
         note="逆向分析 MCP;MIT;聚合多种分析引擎。",
         install="git clone https://github.com/sjkim1127/Reversecore_MCP.git"),
    dict(owner="GH05TCREW", repo="MetasploitMCP", title="Metasploit MCP", type="mcp", cat="pentest",
         zh="Metasploit MCP:让 Agent 通过 MSF RPC 执行模块、管理会话与生成攻击载荷。",
         note="Metasploit RPC 封装 MCP;Apache-2.0;仅限授权环境。",
         install="git clone https://github.com/GH05TCREW/MetasploitMCP.git"),
    dict(owner="six2dez", repo="burp-ai-agent", title="Burp AI Agent", type="plugin", cat="pentest",
         zh="Burp Suite 扩展:内置 MCP 工具、AI 辅助分析、隐私控制与被动/主动扫描。",
         note="Burp Suite 扩展;MIT;需 Burp Suite。",
         install="git clone https://github.com/six2dez/burp-ai-agent.git"),
    dict(owner="Cy-S3c", repo="BurpMCP-Ultra", title="BurpMCP Ultra", type="plugin", cat="pentest",
         zh="Burp Suite MCP:149 个工具覆盖代理、扫描、内联模糊测试、条件竞争、JWT/IDOR 攻击、侦察与 OOB。",
         note="Burp Suite MCP;MIT;需 Burp Suite Professional。",
         install="git clone https://github.com/Cy-S3c/BurpMCP-Ultra.git"),
    dict(owner="w0h1v", repo="mcp-shodan", title="Shodan MCP", type="mcp", cat="data",
         zh="Shodan MCP:搜索联网设备、IP 侦察、DNS 查询与 CVE/CPE 漏洞情报。",
         note="Shodan API 封装 MCP;MIT;需 SHODAN_API_KEY。",
         install="git clone https://github.com/w0h1v/mcp-shodan.git"),
    dict(owner="w0h1v", repo="mcp-virustotal", title="VirusTotal MCP", type="mcp", cat="malware",
         zh="VirusTotal MCP:分析 URL、文件、IP、域名,输出综合安全报告与关系分析。",
         note="VirusTotal API 封装 MCP;MIT;需 VIRUSTOTAL_API_KEY。",
         install="git clone https://github.com/w0h1v/mcp-virustotal.git"),
    dict(owner="badchars", repo="osint-mcp-server", title="OSINT MCP Server", type="mcp", cat="data",
         zh="OSINT MCP:37 个工具、12 个数据源,覆盖 Shodan、VirusTotal、Censys、DNS 侦察、WHOIS、证书透明、BGP、Wayback 等。",
         note="OSINT 聚合 MCP;MIT;需配置各数据源密钥。",
         install="git clone https://github.com/badchars/osint-mcp-server.git"),
    dict(owner="DMontgomery40", repo="pentest-mcp", title="Pentest MCP", type="mcp", cat="pentest",
         zh="渗透测试 MCP:STDIO/HTTP/SSE,集成 nmap、dirbuster、nikto、John the Ripper、hashcat 与字典构建。",
         note="渗透测试 MCP;MIT;仅限授权目标。",
         install="git clone https://github.com/DMontgomery40/pentest-mcp.git"),
    dict(owner="unclecode", repo="crawl4ai", title="Crawl4AI", type="mcp", cat="data",
         zh="Crawl4AI:开源网页爬虫/抓取器,把任意网站转成 LLM 就绪的干净 Markdown,可本地部署或用 Cloud API。",
         note="网页抓取 MCP/库;Apache-2.0;支持本地或云。",
         install="git clone https://github.com/unclecode/crawl4ai.git"),
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
                    "installHint": e["install"],
                    "install": {
                        "method": "link",
                        "url": f"https://github.com/{e['owner']}/{e['repo']}",
                        "command": e["install"],
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
