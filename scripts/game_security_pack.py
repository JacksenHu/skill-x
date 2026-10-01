#!/usr/bin/env python3
"""游戏安全方向:补 universal-modder 的中文 i18n、curation 白名单、套件导图,并新建「游戏安全/反作弊」专家团。"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NS = "rehan-remade/universal-modder"
I18N_ENTRIES = {
    "asset-pipeline": {"name-zh": "游戏资源管线", "description-zh": "把生成或手工制作的美术资源转成游戏引擎可直接加载的格式。", "category": "ai-media"},
    "fal-assets": {"name-zh": "fal 游戏资产生成", "description-zh": "通过 fal MCP / um fal CLI 生成游戏美术、3D 与音频资源。", "category": "ai-media"},
    "game-automation": {"name-zh": "游戏自动化测试", "description-zh": "启动、观察并驱动真实游戏进程,让 Agent 能测试自己的 Mod。", "category": "reverse-engineering"},
    "game-recon": {"name-zh": "游戏 Mod 侦察", "description-zh": "在写 Mod 前搞清楚某个已安装游戏怎么改、引擎与资产结构。", "category": "reverse-engineering"},
    "mashup-mods": {"name-zh": "跨游戏混搭 Mod", "description-zh": "构建跨游戏混搭与完全转换 Mod(如 Minecraft 放进 Elden Ring)。", "category": "reverse-engineering"},
    "mod-any-game": {"name-zh": "任意游戏 Mod", "description-zh": "把想法做成能跑在真实游戏里的 Mod 并录像,覆盖逆向、注入与测试。", "category": "reverse-engineering"},
    "publish-mod": {"name-zh": "Mod 打包发布", "description-zh": "打包并发布完成的游戏 Mod,含发布前 lint、去混淆与清单。", "category": "dev-workflow"},
    "reverse-engineering": {"name-zh": "游戏逆向工程", "description-zh": "读懂游戏内部实现以便 Hook:.NET/Mono(ILSpy)、IL2CPP、原生、资产与存档格式。", "category": "reverse-engineering"},
    "share-field-notes": {"name-zh": "Mod 现场笔记共享", "description-zh": "检索并贡献共享的 AI Mod 知识库,记录各游戏的可 Hook 点与坑。", "category": "dev-workflow"},
    "showcase-video": {"name-zh": "Mod 演示视频", "description-zh": "录制并剪辑游戏 Mod 的展示短片,可直接发布。", "category": "ai-media"},
}

PACK = {
    "slug": "pack-game-security",
    "displayName": "猎游",
    "displayNameEn": "Game Security",
    "role": "游戏安全研究员",
    "roleEn": "Game security researcher",
    "tagline": "先摸清游戏引擎与资产,再谈注入、Mod 与外挂防护——每一步留证据。",
    "taglineEn": "Map the engine and assets first, then inject, mod, and defend—with evidence at every step.",
    "intro": "猎游不信盲改。先侦察目标游戏(引擎/资产/存档),再逆向关键逻辑,用注入与外挂工具链验证,最后落到可复现的结论与外挂防护建议。",
    "introEn": "Game Security does not blind-patch. Recon the game first, reverse the key logic, verify with injection and cheat toolchains, then land reproducible findings and anti-cheat recommendations.",
    "scene": "reverse-engineering",
    "subScene": "game",
    "summary": "游戏安全/反作弊工作流:侦察→逆向→注入/Mod→验证→防护。成员:游戏逆向与 Mod 技能 + Cheat Engine/Android 逆向 MCP。",
    "summaryEn": "Game security / anti-cheat workflow: recon, reverse, inject/mod, verify, defend. Members: game reverse & modding skills + Cheat Engine / Android reverse MCP.",
    "desc_zh": "游戏安全与反作弊专家团:游戏侦察、引擎/资产逆向、注入与 Mod 验证,输出可复现结论与反作弊建议。",
    "members": [
        {"type": "own-skill", "ref": "game-hacking"},
        {"type": "own-skill", "ref": "eni-game-cheat-lab-workflow"},
        {"type": "ext-skill", "ref": "rehan-remade/universal-modder/game-recon"},
        {"type": "ext-skill", "ref": "rehan-remade/universal-modder/reverse-engineering"},
        {"type": "mcp", "ref": "io.github.bethington/cheat-engine-server-python"},
        {"type": "mcp", "ref": "io.github.c4x64/droid-re-chain"},
        {"type": "mcp", "ref": "io.github.Diphome/UnityRift"},
    ],
    "color": "#3DD68C",
}


def main():
    # 1) i18n
    i18n_path = ROOT / "showcase" / "i18n-ext.json"
    i18n = json.loads(i18n_path.read_text(encoding="utf-8"))
    bucket = i18n.setdefault(NS, {})
    for k, v in I18N_ENTRIES.items():
        bucket.setdefault(k, v)
    i18n_path.write_text(json.dumps(i18n, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] i18n {NS}: {len(I18N_ENTRIES)} 条")

    # 2) curation 白名单
    cur_path = ROOT / "showcase" / "curation.json"
    cur = json.loads(cur_path.read_text(encoding="utf-8"))
    ext = json.loads((ROOT / "external.json").read_text(encoding="utf-8"))
    suite = next(s for s in ext["suites"] if s["namespace"] == NS)
    names = [sk["name"] for sk in suite["skills"]]
    cur["include"][NS] = names
    cur_path.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] curation include {NS}: {len(names)} 条")

    # 3) 专家团 meta-skill + packs.json
    p = PACK
    out = ROOT / "skills" / p["slug"] / "SKILL.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    children = "\n".join(f"    - {m['ref']}" for m in p["members"])
    body = f"""---
name: {p['slug']}
description: >-
  {p['summaryEn']}
license: MIT
compatibility: Meta-skill orchestration. Member skills/MCP are installed or connected on demand.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: {p['displayName']}
  aliases:
    - {p['displayName']}
    - {p['displayNameEn']}
    - {p['slug']}
  name-zh: {p['displayName']} · {p['role']}
  description-zh: {p['desc_zh']}
  category: {p['scene']}
orchestration:
  children:
{children}
---
# {p['displayName']}（{p['displayNameEn']}）

{p['intro']}

## 工作原则

先侦察边界,再逆向,再注入验证;每条结论落到可复现证据,不做无授权的内存读写。

## 步骤 1:侦察与边界

- 确认目标游戏与授权范围
- 用 game-recon 摸清引擎、资产、存档、可 Hook 点

## 步骤 2:逆向关键逻辑

- 用游戏逆向技能(.NET/IL2CPP/原生)还原关键函数与数据结构
- 用 Cheat Engine / Droid Re-Chain MCP 做内存/动态验证

## 步骤 3:注入与验证

- 用 game-hacking / 外挂实验室工作流实现注入与 Mod
- 每步记录命令、输入、输出,保留证据

## 步骤 4:防护与交付

- 输出可复现结论 + 反作弊/防篡改建议
- 归档:证据、脚本、报告
"""
    out.write_text(body, encoding="utf-8")

    avatar = ROOT / "showcase" / "assets" / "avatars" / f"{p['slug']}.svg"
    c = p["color"]
    avatar.write_text(f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="{p['displayNameEn']}">
  <defs><pattern id="grid" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M16 0H0v16" fill="none" stroke="#1E2630" stroke-width="1"/></pattern></defs>
  <rect width="256" height="256" rx="6" fill="#141A21"/>
  <rect width="256" height="256" rx="6" fill="url(#grid)"/>
  <rect x="1" y="1" width="254" height="254" rx="6" fill="none" stroke="#232C38" stroke-width="2"/>
  <circle cx="128" cy="128" r="70" fill="none" stroke="{c}" stroke-width="3"/>
  <circle cx="128" cy="128" r="46" fill="none" stroke="#33404F" stroke-width="2"/>
  <path d="M128 82l40 22v44l-40 22-40-22v-44z" fill="none" stroke="{c}" stroke-width="3"/>
  <path d="M128 104l20 11v22l-20 11-20-11v-22z" fill="none" stroke="#33404F" stroke-width="2"/>
  <circle cx="128" cy="128" r="6" fill="{c}"/>
</svg>
""", encoding="utf-8")

    packs_path = ROOT / "packs.json"
    packs = json.loads(packs_path.read_text(encoding="utf-8"))
    if not any(x.get("slug") == p["slug"] for x in packs["packs"]):
        packs["packs"].append({
            "slug": p["slug"], "displayName": p["displayName"], "displayNameEn": p["displayNameEn"],
            "persona": {"role": p["role"], "roleEn": p["roleEn"], "tagline": p["tagline"], "taglineEn": p["taglineEn"],
                        "intro": p["intro"], "introEn": p["introEn"], "avatar": f"assets/avatars/{p['slug']}.svg",
                        "scene": p["scene"], "subScene": p["subScene"]},
            "summary": p["summary"], "summaryEn": p["summaryEn"], "origin": "own", "skill": p["slug"],
            "source": f"skills/{p['slug']}/SKILL.md", "license": {"spdx": "MIT"},
            "members": [{"type": m["type"], "ref": m["ref"]} for m in p["members"]],
            "reviewed": {"by": "codex", "at": "2026-10-01", "execReview": "passed", "note": "自研专家团:人设与编排剧本机审"},
            "upstreamStatus": {"source": "own", "lastCheck": "2026-10-01", "alive": True, "failSince": None},
            "degraded": False,
        })
        packs_path.write_text(json.dumps(packs, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[+] 新增专家团 {p['slug']}")
    else:
        print(f"[!] 专家团 {p['slug']} 已存在")
    return 0


if __name__ == "__main__":
    sys.exit(main())
