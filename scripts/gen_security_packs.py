#!/usr/bin/env python3
"""新增 3 个安全方向专家团(自研 meta-skill):寻隙(漏洞赏金)/破阵(CTF)/烛照(威胁情报)。

产物:
- skills/pack-<slug>/SKILL.md(mata-skill 编排剧本)
- showcase/assets/avatars/<slug>.svg(几何徽记头像)
- packs.json 追加条目(origin=own,再跑 pack_ingest.py --sync 解析成员)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PACKS = [
    {
        "slug": "pack-bug-hunter",
        "skill": "pack-bug-hunter",
        "displayName": "寻隙",
        "displayNameEn": "Bug Hunter",
        "role": "漏洞赏金猎人",
        "roleEn": "Bug bounty hunter",
        "tagline": "从攻击面测绘到可复现 PoC,只交带证据的漏洞。",
        "taglineEn": "From attack-surface mapping to reproducible PoC—only submit vulnerabilities with evidence.",
        "intro": "寻隙不扫热闹,只追根因。先锁定攻击面与边界,再按漏洞类别逐个验证,拿到可复现的请求与响应证据后,才写进报告。",
        "introEn": "Bug Hunter chases root causes, not noise. Lock the attack surface, verify each vuln class, and only write up findings backed by reproducible requests and responses.",
        "scene": "pentest",
        "subScene": "bug-bounty",
        "summary": "漏洞赏金工作流:方法论→侦察→漏洞识别→证据固化→报告。成员:Claude-BugHunter 核心 + Claude-Red 漏洞识别 + Burp/Nuclei MCP。",
        "summaryEn": "Bug bounty workflow: methodology, recon, bug identification, evidence hygiene, reporting. Members: Claude-BugHunter core, Claude-Red bug identification, Burp/Nuclei MCP.",
        "desc_zh": "漏洞赏金专家团:攻击面测绘、漏洞识别、证据固化与可复现报告,成员覆盖方法论、红队技巧与 Burp/Nuclei 工具链。",
        "members": [
            {"type": "ext-skill", "ref": "elementalsouls/Claude-BugHunter/bug-bounty"},
            {"type": "ext-skill", "ref": "elementalsouls/Claude-BugHunter/bb-methodology"},
            {"type": "ext-skill", "ref": "SnailSploit/Claude-Red/offensive-bug-identification"},
            {"type": "ext-skill", "ref": "elementalsouls/Claude-BugHunter/evidence-hygiene"},
            {"type": "mcp", "ref": "io.github.Cy-S3c/BurpMCP-Ultra"},
            {"type": "mcp", "ref": "io.github.FuzzingLabs/mcp-security-hub"},
        ],
        "color": "#FF4D4F",
    },
    {
        "slug": "pack-ctf",
        "skill": "pack-ctf",
        "displayName": "破阵",
        "displayNameEn": "CTF",
        "role": "CTF 解题员",
        "roleEn": "CTF solver",
        "tagline": "先分类,再解题:逆向、PWN、密码学各走各的套路,最后交一份标准复盘。",
        "taglineEn": "Classify first, then solve—reverse, pwn, and crypto each follow their own playbook, ending in a standard writeup.",
        "intro": "破阵先给题目分类,再调度对应技能与工具:二进制交给 radare2/frida,密码交给现成攻击套路,解完按标准格式写复盘。",
        "introEn": "CTF classifies the challenge, then dispatches the right skill and tooling—binaries to radare2/frida, crypto to established attack patterns—and writes a standard writeup.",
        "scene": "reverse-engineering",
        "subScene": "ctf",
        "summary": "CTF 解题工作流:分类→逆向/PWN/密码→解题→复盘报告。成员:CTF 技能组 + radare2/frida MCP。",
        "summaryEn": "CTF solving workflow: classification, reverse/pwn/crypto, solving, writeup. Members: CTF skill set + radare2/frida MCP.",
        "desc_zh": "CTF 战队专家团:按题分类调度逆向、PWN、密码与取证技能,结合 radare2/frida 动态分析,输出标准复盘。",
        "members": [
            {"type": "ext-skill", "ref": "ljagiello/ctf-skills/ctf-reverse"},
            {"type": "ext-skill", "ref": "ljagiello/ctf-skills/ctf-pwn"},
            {"type": "ext-skill", "ref": "ljagiello/ctf-skills/ctf-crypto"},
            {"type": "ext-skill", "ref": "ljagiello/ctf-skills/solve-challenge"},
            {"type": "mcp", "ref": "io.github.radareorg/radare2-mcp"},
            {"type": "mcp", "ref": "io.github.dnakov/frida-mcp"},
        ],
        "color": "#FF6B2C",
    },
    {
        "slug": "pack-threat-intel",
        "skill": "pack-threat-intel",
        "displayName": "烛照",
        "displayNameEn": "Threat Intel",
        "role": "威胁情报分析师",
        "roleEn": "Threat intelligence analyst",
        "tagline": "把散落的 CVE、资产与样本线索,串成一条可行动的威胁情报。",
        "taglineEn": "Weave scattered CVEs, assets, and sample leads into actionable threat intelligence.",
        "intro": "烛照从一条 IOC 或 CVE 出发,用 CVE/EPSS/KEV 定级,用 Shodan/VirusTotal/OSINT 扩线,再落成带来源的情报结论。",
        "introEn": "Threat Intel starts from one IOC or CVE, scores it via CVE/EPSS/KEV, pivots through Shodan/VirusTotal/OSINT, and lands sourced intelligence conclusions.",
        "scene": "malware",
        "subScene": "threat-intel",
        "summary": "威胁情报工作流:线索→定级→扩线→关联→成报。成员:CVE/Shodan/VirusTotal/OSINT MCP。",
        "summaryEn": "Threat intelligence workflow: lead, scoring, pivoting, correlation, reporting. Members: CVE/Shodan/VirusTotal/OSINT MCP.",
        "desc_zh": "威胁情报专家团:从 CVE 定级、资产测绘、样本判定到开源情报关联,输出带来源的威胁情报。",
        "members": [
            {"type": "mcp", "ref": "io.github.mukul975/cve-mcp-server"},
            {"type": "mcp", "ref": "io.github.w0h1v/mcp-shodan"},
            {"type": "mcp", "ref": "io.github.w0h1v/mcp-virustotal"},
            {"type": "mcp", "ref": "io.github.badchars/osint-mcp-server"},
        ],
        "color": "#A855F7",
    },
]


def write_metaskill(p):
    d = p["slug"]
    out = ROOT / "skills" / d / "SKILL.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    children = "\n".join(f"    - {m['ref']}" for m in p["members"])
    body = f"""---
name: {p["skill"]}
description: >-
  {p["summaryEn"]}
license: MIT
compatibility: Meta-skill orchestration. Member skills/MCP are installed or connected on demand.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: {p["displayName"]}
  aliases:
    - {p["displayName"]}
    - {p["displayNameEn"]}
    - {p["skill"]}
  name-zh: {p["displayName"]} · {p["role"]}
  description-zh: {p["desc_zh"]}
  category: {p["scene"]}
orchestration:
  children:
{children}
---
# {p["displayName"]}（{p["displayNameEn"]}）

{p["intro"]}

## 工作原则

先定边界,再取证,最后成报。任何结论都落到可复现证据,不写“看起来像”。

## 步骤 1:定边界与目标

- 明确本次要回答的问题(漏洞 / 解题 / 情报结论)
- 确认目标与授权范围;涉及攻击面的只做授权内动作

## 步骤 2:调度成员

按任务类型调用 `orchestration.children` 中的对应技能或 MCP:
- 漏洞赏金 → bug-bounty / bb-methodology / offensive-bug-identification / Burp / Nuclei
- CTF → ctf-reverse / ctf-pwn / ctf-crypto / radare2 / frida
- 威胁情报 → cve-mcp-server / shodan / virustotal / osint

## 步骤 3:执行与验证

- 每一步记录输入、命令、输出
- 证据可复现,区分真信号与噪声

## 步骤 4:交付

- 漏洞:PoC + 请求/响应 + 影响评估 + 修复建议
- CTF:flag + 解题过程 + 标准 writeup
- 威胁情报:定级 + 关联链 + 来源 + 建议动作
"""
    out.write_text(body, encoding="utf-8")
    return out


def write_avatar(p):
    out = ROOT / "showcase" / "assets" / "avatars" / f"{p['slug']}.svg"
    c = p["color"]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="{p['displayNameEn']}">
  <defs>
    <pattern id="grid" width="16" height="16" patternUnits="userSpaceOnUse">
      <path d="M16 0H0v16" fill="none" stroke="#1E2630" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="256" height="256" rx="6" fill="#141A21"/>
  <rect width="256" height="256" rx="6" fill="url(#grid)"/>
  <rect x="1" y="1" width="254" height="254" rx="6" fill="none" stroke="#232C38" stroke-width="2"/>
  <circle cx="128" cy="128" r="66" fill="none" stroke="{c}" stroke-width="3"/>
  <circle cx="128" cy="128" r="44" fill="none" stroke="#33404F" stroke-width="2"/>
  <path d="M128 84v88M84 128h88" stroke="{c}" stroke-width="5" stroke-linecap="square"/>
  <circle cx="128" cy="84" r="5" fill="{c}"/>
  <circle cx="128" cy="172" r="5" fill="#33404F"/>
  <circle cx="84" cy="128" r="5" fill="{c}"/>
  <circle cx="172" cy="128" r="5" fill="#33404F"/>
</svg>
"""
    out.write_text(svg, encoding="utf-8")
    return out


def main():
    reg = ROOT / "packs.json"
    doc = json.loads(reg.read_text(encoding="utf-8"))
    existing = {p.get("slug") for p in doc.get("packs", [])}
    added = []
    for p in PACKS:
        write_metaskill(p)
        write_avatar(p)
        if p["slug"] in existing:
            continue
        entry = {
            "slug": p["slug"],
            "displayName": p["displayName"],
            "displayNameEn": p["displayNameEn"],
            "persona": {
                "role": p["role"], "roleEn": p["roleEn"],
                "tagline": p["tagline"], "taglineEn": p["taglineEn"],
                "intro": p["intro"], "introEn": p["introEn"],
                "avatar": f"assets/avatars/{p['slug']}.svg",
                "scene": p["scene"], "subScene": p["subScene"],
            },
            "summary": p["summary"], "summaryEn": p["summaryEn"],
            "origin": "own",
            "skill": p["skill"],
            "source": f"skills/{p['slug']}/SKILL.md",
            "license": {"spdx": "MIT"},
            "members": [{"type": m["type"], "ref": m["ref"]} for m in p["members"]],
            "reviewed": {"by": "codex", "at": "2026-10-01", "execReview": "passed", "note": "自研专家团:人设与编排剧本机审"},
            "upstreamStatus": {"source": "own", "lastCheck": "2026-10-01", "alive": True, "failSince": None},
            "degraded": False,
        }
        doc["packs"].append(entry)
        added.append(p["slug"])
    reg.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] 新增 packs: {added};总数 {len(doc['packs'])}")
    print("[*] 下一步: python scripts/pack_ingest.py --sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
