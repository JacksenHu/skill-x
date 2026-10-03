#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""核验精选候选：仓库存在、许可证、最近推送、是否真含目标能力（读 README 关键词）。"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("GH_TOKEN", "")

# 精选候选：full_name -> 拟定分类
PICK = [
    # ---- MCP ----
    ("bethington/ghidra-mcp", "mcp"),
    ("duty1g/x64dbg-mcp-server", "mcp"),
    ("ShinoLeah/eDBG", "mcp"),
    ("cyberkaida/reverse-engineering-assistant", "mcp"),
    ("zinja-coder/apktool-mcp-server", "mcp"),
    ("SetsunaYukiOvO/x64dbg-mcp", "mcp"),
    ("1-3-7/disrobe", "mcp"),
    ("xiaoyeuzixi/revlab", "mcp"),
    ("index-login/MobileRE-Skill", "mcp"),
    ("JameZUK/Arkana", "mcp"),
    ("mrphrazer/agentic-malware-analysis", "mcp"),
    ("bl4ckr0ss3/knife", "mcp"),
    ("morluto/rea", "mcp"),
    # ---- 工具 ----
    ("horsicq/DIE-engine", "tool"),
    ("rednaga/APKiD", "tool"),
    ("j4k0xb/webcrack", "tool"),
    ("Lil-House/Pyarmor-Static-Unpack-1shot", "tool"),
    ("void-stack/VMUnprotect.Dumper", "tool"),
    ("AdvDebug/AntiCrack-DotNet", "tool"),
    ("NotRequiem/antidbg", "tool"),
    ("PELock/PELock-Software-Protection-and-Licensing", "tool"),
    ("JonathanSalwan/Tigress_protection", "tool"),
    ("SychicBoy/NETReactorSlayer", "tool"),
    ("Svenskithesource/PyArmor-Unpacker", "tool"),
    ("TopSoftdeveloper/UnpackThemida", "tool"),
    ("ergrelet/unlicense", "tool"),
    ("ergrelet/themida-unmutate", "tool"),
    ("JonathanSalwan/VMProtect-devirtualization", "tool"),
    ("CodingGay/BlackDex", "tool"),
    ("strazzere/android-unpacker", "tool"),
    ("ThomasThelen/Anti-Debugging", "tool"),
    ("x86byte/Obfusk8", "tool"),
    ("vy/lang", "tool"),
    ("undisassemble/yap", "tool"),
    ("uzokingkong/BTG-packer", "tool"),
    ("ekcbw/pyc-zipper", "tool"),
    ("DosX-dev/UPX-Patcher", "tool"),
    ("invokr/elf-stuff", "tool"),
    ("iukpo/Proteus", "tool"),
    ("NIKJOO/Nanomits", "tool"),
    ("ga0/pyprotect", "tool"),
    ("anpa1200/Unpacker", "tool"),
    ("wuji66dde/jshook-skill", "tool"),
    ("Fadi002/de4py", "tool"),
    # ---- 插件 ----
    ("P4nda0s/reverse-skills", "plugin"),
    ("Masriyan/Claude-Code-CyberSecurity-Skill", "plugin"),
    ("gl0bal01/malware-analysis-claude-skills", "plugin"),
    ("incogbyte/android-reverse-engineering-claude-skill", "plugin"),
    ("sector-b79/Malware-And-Reverse-Engineering-Skills", "plugin"),
    ("meirm/reverse-engineering-skill", "plugin"),
    ("LichAmnesia/skill-lint", "plugin"),
    ("highimpact-dev/skill-shield", "plugin"),
    ("almasumdev/awesome-mobile-security-agent-skills", "plugin"),
    # ---- 专家团 ----
    ("Njones17/AI-agent-master-cyber-skills-list", "pack"),
    ("meltedinhex/analyst-ai-pack", "pack"),
    ("ibrdot/swe-re-expert", "pack"),
]


def gh(path):
    h = {"User-Agent": "x"}
    if TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request("https://api.github.com" + path, headers=h)
    for _ in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 502, 503):
                time.sleep(4)
                continue
            return e.code, {}
        except Exception:  # noqa: BLE001
            time.sleep(3)
    return 0, {}


def readme(owner, repo):
    for br in ("main", "master"):
        for nm in ("README.md", "readme.md", "README.MD"):
            h = {"User-Agent": "x", "Accept": "text/plain"}
            if TOKEN:
                h["Authorization"] = "Bearer " + TOKEN
            u = "https://raw.githubusercontent.com/%s/%s/%s/%s" % (owner, repo, br, nm)
            try:
                req = urllib.request.Request(u, headers=h)
                with urllib.request.urlopen(req, timeout=25) as r:
                    return r.read().decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                continue
    return ""


CAP = ["obfuscat", "packer", "unpack", "anti-debug", "antidebug", "anti-reverse",
       "disassembl", "deobfuscat", "tamper", "protect", "crack", "virtualiz",
       "hook", "licens", "crypter"]


def main():
    out = []
    for full, kind in PICK:
        st, j = gh("/repos/" + full)
        if st != 200:
            print("SKIP %-48s HTTP %d" % (full, st))
            continue
        rd = readme(full.split("/")[0], full.split("/")[1])
        low = rd.lower()
        caps = sorted({c for c in CAP if c in low})
        rec = {
            "full_name": full,
            "kind": kind,
            "stars": j.get("stargazers_count"),
            "license": ((j.get("license") or {}).get("spdx_id") or "UNKNOWN"),
            "archived": j.get("archived"),
            "pushed_at": j.get("pushed_at"),
            "desc": (j.get("description") or "")[:160],
            "topics": (j.get("topics") or [])[:8],
            "caps": caps,
            "readme_len": len(rd),
        }
        out.append(rec)
        print("OK   %-48s ★%-6d %-14s %s" % (full, rec["stars"], rec["license"], ",".join(caps[:5])))
        sys.stdout.flush()
        time.sleep(0.6)

    p = os.path.join(ROOT, "scripts", "upstream-audit", "anti-reverse-picked.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n核验 %d 个 -> %s" % (len(out), p))
    bad = [r for r in out if r["archived"] or r["license"] == "UNKNOWN"]
    print("需留意(归档/无许可证):", len(bad))
    for r in bad:
        print("   !", r["full_name"], "archived=%s license=%s" % (r["archived"], r["license"]))


if __name__ == "__main__":
    main()
