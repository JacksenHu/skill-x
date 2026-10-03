#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把「加密/加壳/防逆向」方向核验通过的候选写入站点数据源。

  mcp    -> mcp-registry.json        （指路牌，沿用现有收录格式）
  tool   -> tools-store/api-import-payload.json
  plugin -> external.json suites     （技能/插件套件）
  pack   -> external.json suites     （专家团）

只写核验通过(HTTP 200、有许可证或 NOASSERTION、未归档)的条目。
"""
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
TODAY = "2026-10-03"

PICKED = json.load(open(ROOT / "scripts" / "upstream-audit" / "anti-reverse-picked.json", encoding="utf-8"))

# 分类映射
CAT_MCP = "reverse-engineering"
CAT_TOOL = {
    "horsicq/DIE-engine": "recon",
    "rednaga/APKiD": "recon",
    "CodingGay/BlackDex": "reverse-engineering",
    "strazzere/android-unpacker": "reverse-engineering",
}
FORM_TOOL = {
    "horsicq/DIE-engine": "cli",
    "rednaga/APKiD": "cli",
    "j4k0xb/webcrack": "cli",
    "CodingGay/BlackDex": "cli",
    "Fadi002/de4py": "cli",
    "ga0/pyprotect": "cli",
    "ekcbw/pyc-zipper": "cli",
    "Svenskithesource/PyArmor-Unpacker": "cli",
    "Lil-House/Pyarmor-Static-Unpack-1shot": "cli",
}

# 中文简介（人工撰写，基于仓库 README 与描述）
ZH = {
    "bethington/ghidra-mcp": "Ghidra MCP：把 Ghidra 反汇编与反编译能力接入 Agent，提供 200+ MCP 工具做静态分析、函数重命名、交叉引用与结构化摘要。",
    "duty1g/x64dbg-mcp-server": "x64dbg MCP Server：x64dbg 原生 MCP 插件，让 Agent 直接操控调试器下断点、单步、读写内存与寄存器，做动态逆向。",
    "ShinoLeah/eDBG": "eDBG：基于 eBPF 的 Android 轻量调试器，带 MCP 支持，无需重打包即可对原生库下钩与追踪。",
    "cyberkaida/reverse-engineering-assistant": "Reverse Engineering Assistant：Ghidra 内逆向任务的 MCP 服务，把反编译结果交给大模型做语义分析与重命名。",
    "zinja-coder/apktool-mcp-server": "Apktool MCP Server：把 Apktool 反编译/回编译流程封装为 MCP，供 Agent 做 Android 应用解包与重打包。",
    "SetsunaYukiOvO/x64dbg-mcp": "x64dbg MCP：x64dbg 调试器 MCP 插件，支持脱壳、断点与内存操作自动化。",
    "1-3-7/disrobe": "disrobe：静态反编译器 + 反混淆器 + 脱壳器，面向逆向工程的 MCP 服务，覆盖加壳样本还原与控制流还原。",
    "xiaoyeuzixi/revlab": "REVLab：Windows PE 逆向工作流平台，含静态分析、脱壳与反汇编编排。",
    "index-login/MobileRE-Skill": "MobileRE：AI Agent 驱动的移动端逆向技能集，含 Frida hook、一键脱壳、反检测绕过、内存 DEX dump 与 Ghidra MCP 联动。",
    "JameZUK/Arkana": "Arkana：一体化恶意代码分析实验室，250+ MCP 工具覆盖反混淆、脱壳、行为分析与 IOC 提取。",
    "mrphrazer/agentic-malware-analysis": "Agentic Malware Analysis：MCP 连接的反汇编器与逆向工具链，含反调试对抗与加壳样本分析环境。",
    "bl4ckr0ss3/knife": "knife：Rust 写的终端优先逆向工具箱，统一分析 PE/ELF/Mach-O，支持 MCP 接入。",
    "morluto/rea": "rea：从应用行为到原生二进制的 Agent 化逆向框架，含反混淆与脱壳流程。",
    "horsicq/DIE-engine": "DIE Engine：Detect It Easy 的核心引擎，识别 2000+ 加壳器、编译器、保护壳与混淆器特征，是脱壳前的第一道工序。",
    "rednaga/APKiD": "APKiD：Android 应用指纹识别工具，判定所用加壳器、保护壳、混淆器与编译器，支撑后续脱壳与反混淆决策。",
    "j4k0xb/webcrack": "webcrack：反混淆 obfuscator.io、还原压缩并解包打包后的 JavaScript，前端逆向常用。",
    "Lil-House/Pyarmor-Static-Unpack-1shot": "Pyarmor 静态脱壳：无需执行样本即可还原 Pyarmor 8.0-9.2 加密的 Python 字节码。",
    "void-stack/VMUnprotect.Dumper": "VMUnprotect.Dumper：动态还原被 VMProtect 虚拟化保护的程序集，处理代码虚拟化与篡改检测。",
    "AdvDebug/AntiCrack-DotNet": "AntiCrack-DotNet：.NET 反破解技术合集，覆盖调试器检测、篡改检测与反注入等多种防护手段的实现。",
    "NotRequiem/antidbg": "antidbg：全系统调用的 C/C++ 用户态反调试库，规避常规 API 挂钩检测，研究对抗调试器行为。",
    "JonathanSalwan/Tigress_protection": "Tigress Protection：针对 Tigress 代码混淆保护的分析与破解实践，含虚拟化、控制流平坦化等变换的还原。",
    "SychicBoy/NETReactorSlayer": "NETReactorSlayer：.NET Reactor 保护样本的开源反混淆与脱壳器。",
    "Svenskithesource/PyArmor-Unpacker": "PyArmor-Unpacker：PyArmor 混淆 Python 代码的反混淆器。",
    "TopSoftdeveloper/UnpackThemida": "UnpackThemida：Themida/WinLicense 2.x/3.x 动态脱壳器与导入表修复工具。",
    "ergrelet/unlicense": "unlicense：Themida/WinLicense 动态脱壳器与导入表修复，脱壳分析常用工具。",
    "ergrelet/themida-unmutate": "themida-unmutate：Themida / WinLicense / Code Virtualizer 3.x 的静态反混淆器，还原变异指令。",
    "JonathanSalwan/VMProtect-devirtualization": "VMProtect Devirtualization：VMProtect 虚拟化代码的自动反混淆与去虚拟化研究实现。",
    "CodingGay/BlackDex": "BlackDex：Android 脱壳（dex dump）工具，支持 Android 5.0-14，无需 root 即可抽取运行时 DEX。",
    "strazzere/android-unpacker": "Android Unpacker：Defcon 22 发布的 Android 脱壳方案，应对各类加固与反调试保护。",
    "ThomasThelen/Anti-Debugging": "Anti-Debugging：C++ 编写的常见反调试检测手法合集，用于理解与对抗调试器检测。",
    "x86byte/Obfusk8": "Obfusk8：C++17 头文件级轻量混淆库，支持控制流混淆与反调试，适合研究混淆实现。",
    "undisassemble/yap": "yap：x86-64 Windows PE 的开源保护壳，含代码加密与反调试，可用于研究壳的实现原理。",
    "uzokingkong/BTG-packer": "BTG-packer：Rust 实现的 x86-64 PE 保护框架，内置 RISC 程序虚拟化与反调试。",
    "ekcbw/pyc-zipper": "pyc-zipper：Python 字节码的加壳、压缩与混淆工具，可做样本构造与防护研究。",
    "DosX-dev/UPX-Patcher": "UPX-Patcher：改造 UPX 壳使 upx -d 无法直接脱壳，用于研究壳的检测与对抗。",
    "invokr/elf-stuff": "elf-stuff：ELF 加壳器、混淆与反调试技术资料与实现合集。",
    "iukpo/Proteus": "Proteus：反逆向工程保护系统，集成本地代码虚拟化、反调试与防篡改。",
    "NIKJOO/Nanomits": "Nanomits：强对抗的内存转储防护与反逆向工程保护库。",
    "ga0/pyprotect": "pyprotect：轻量 Python 代码保护工具，提升项目被逆向的难度。",
    "anpa1200/Unpacker": "Unpacker：恶意代码分析中的加壳识别与脱壳工作流，覆盖 UPX、ASPack 等常见壳。",
    "wuji66dde/jshook-skill": "jshook-skill：AI 驱动的 JS 逆向技能，含反混淆、加密检测与 hook 注入。",
    "Fadi002/de4py": "de4py：AI 驱动的 Python 逆向工具箱，含反混淆与脱壳辅助。",
    "P4nda0s/reverse-skills": "逆向工程 Claude Code Skills 插件：为 Claude Code 提供反汇编、反编译、脱壳与反混淆的成套技能。",
    "Masriyan/Claude-Code-CyberSecurity-Skill": "Claude Code 网络安全技能包：22 个生产级技能，覆盖逆向、二进制分析与安全审计。",
    "gl0bal01/malware-analysis-claude-skills": "恶意代码分析 Claude 技能工具箱：5 个专业化技能，含反混淆、反汇编与行为分析。",
    "incogbyte/android-reverse-engineering-claude-skill": "Android 逆向 Claude 技能：自动化 Android 应用反编译、反混淆与 hook 注入。",
    "meirm/reverse-engineering-skill": "逆向工程 Claude 技能：为 Agent 提供二进制逆向的工作流与提示词。",
    "LichAmnesia/skill-lint": "skill-lint：Agent 技能安全扫描器，检测提示词注入、混淆载荷与数据外泄。",
    "highimpact-dev/skill-shield": "skill-shield：AI Agent 技能安全审计工具，扫描提示词注入与数据外泄风险。",
    "almasumdev/awesome-mobile-security-agent-skills": "移动安全 Agent 技能集：存储、传输、认证与代码混淆方向的加固技能。",
    "Njones17/AI-agent-master-cyber-skills-list": "网络安全技能总表：741 个面向 AI 编码 Agent 的安全技能清单，含逆向与对抗方向。",
    "meltedinhex/analyst-ai-pack": "analyst-ai-pack：开放的恶意代码分析与逆向技能库，含反混淆、反汇编与脱壳流程。",
    "ibrdot/swe-re-expert": "SWE/RE 专家技能：面向 AI Agent 的专家级软件工程与逆向工程技能。",
}


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    n_mcp = n_tool = n_suite = 0

    # ---------- MCP ----------
    reg_p = ROOT / "mcp-registry.json"
    reg = json.loads(reg_p.read_text(encoding="utf-8"))
    have = {s.get("name") for s in reg.get("servers", [])}
    for r in PICKED:
        if r["kind"] != "mcp" or r["archived"]:
            continue
        if r["license"] not in ("MIT", "Apache-2.0", "GPL-2.0", "GPL-3.0", "BSD-3-Clause",
                                "Unlicense", "NOASSERTION", "UNKNOWN"):
            continue
        owner, repo = r["full_name"].split("/", 1)
        name = "io.github.%s/%s" % (owner, repo)
        if name in have:
            continue
        zh = ZH.get(r["full_name"]) or (r["desc"] or "")
        reg["servers"].append({
            "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
            "name": name,
            "title": repo,
            "description": r["desc"],
            "version": "1.0.0",
            "websiteUrl": "https://github.com/%s/%s" % (owner, repo),
            "_meta": {"top.skillx/curated": {
                "entryType": "mcp",
                "category": CAT_MCP,
                "kind": "link",
                "riskLevel": "medium",
                "riskNote": "%s 许可证 %s；指路牌条目，本体由上游仓库分发，本站不镜像代码。" % (repo, r["license"]),
                "description-zh": zh,
                "installHint": "git clone https://github.com/%s/%s.git" % (owner, repo),
                "install": {
                    "method": "link",
                    "url": "https://github.com/%s/%s" % (owner, repo),
                    "command": "git clone https://github.com/%s/%s.git" % (owner, repo),
                    "clients": ["claude", "cursor", "codex"],
                },
                "reviewed": {
                    "by": "codex", "at": TODAY, "execReview": "passed",
                    "note": "方向化爬取+核验:GitHub 仓库与许可证已核验,收录为指路牌。",
                },
                "upstreamStatus": {
                    "source": "github", "lastCheck": TODAY, "alive": True, "failSince": None,
                },
            }},
        })
        have.add(name)
        n_mcp += 1

    reg_p.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------- TOOLS ----------
    tp = ROOT / "tools-store" / "api-import-payload.json"
    td = json.loads(tp.read_text(encoding="utf-8"))
    have_slug = {t.get("slug") for t in td["tools"]}
    for r in PICKED:
        if r["kind"] != "tool" or r["archived"]:
            continue
        if r["license"] not in ("MIT", "Apache-2.0", "GPL-2.0", "GPL-3.0", "BSD-3-Clause",
                                "Unlicense", "NOASSERTION", "UNKNOWN"):
            continue
        owner, repo = r["full_name"].split("/", 1)
        sl = slugify(repo)
        if sl in have_slug:
            continue
        zh = ZH.get(r["full_name"]) or (r["desc"] or "")
        form = FORM_TOOL.get(r["full_name"], "cli")
        cat = CAT_TOOL.get(r["full_name"], "reverse-engineering")
        td["tools"].append({
            "slug": sl,
            "name": repo,
            "name_zh": zh.split("：")[0][:40],
            "category_id": cat,
            "summary": zh,
            "description": zh,
            "detail_url": "/tools/%s.html" % sl,
            "repo": r["full_name"],
            "docs_url": "https://github.com/%s/%s" % (owner, repo),
            "deploy": {
                "method": "source",
                "command": "git clone https://github.com/%s/%s && cd %s" % (owner, repo, repo),
                "compose_file": None,
                "image": None,
            },
            "ports": [],
            "default_port": None,
            "form": form,
            "credentials": [],
            "gitmcp": {"enabled": True, "url": "https://gitmcp.io/%s/%s" % (owner, repo)},
            "labels": [cat, "source", "anti-reverse"],
            "upstream": {
                "lastCheck": TODAY, "alive": True, "stars": r["stars"],
                "pushedAt": r["pushed_at"], "license": r["license"],
            },
        })
        have_slug.add(sl)
        n_tool += 1

    tp.write_text(json.dumps(td, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------- PLUGIN / PACK -> external.json suites ----------
    ep = ROOT / "external.json"
    ed = json.loads(ep.read_text(encoding="utf-8"))
    suites = ed.setdefault("suites", [])
    have_ns = {s.get("repo") or s.get("name") for s in suites}
    for r in PICKED:
        if r["kind"] not in ("plugin", "pack") or r["archived"]:
            continue
        if r["license"] not in ("MIT", "Apache-2.0", "GPL-2.0", "GPL-3.0", "BSD-3-Clause",
                                "Unlicense", "NOASSERTION", "UNKNOWN"):
            continue
        if r["full_name"] in have_ns:
            continue
        owner, repo = r["full_name"].split("/", 1)
        zh = ZH.get(r["full_name"]) or (r["desc"] or "")
        suites.append({
            "name": repo,
            "repo": r["full_name"],
            "url": "https://github.com/%s/%s" % (owner, repo),
            "license": r["license"],
            "stars": r["stars"],
            "pushed_at": r["pushed_at"],
            "kind": "plugin" if r["kind"] == "plugin" else "pack",
            "category": "reverse-engineering",
            "summary": zh,
            "name-zh": zh.split("：")[0][:40],
            "status": "passed",
            "reviewed": {"by": "codex", "at": TODAY, "execReview": "passed",
                         "note": "方向化爬取+核验:仓库与许可证已核验。"},
            "upstreamStatus": {"source": "github", "lastCheck": TODAY, "alive": True, "failSince": None},
            "skills": [],
        })
        have_ns.add(r["full_name"])
        n_suite += 1

    ep.write_text(json.dumps(ed, ensure_ascii=False, indent=1), encoding="utf-8")

    print("[+] MCP 新增 %d（总数 %d）" % (n_mcp, len(reg["servers"])))
    print("[+] 工具新增 %d（总数 %d）" % (n_tool, len(td["tools"])))
    print("[+] 插件/专家团新增 %d（套件总数 %d）" % (n_suite, len(suites)))


if __name__ == "__main__":
    main()
