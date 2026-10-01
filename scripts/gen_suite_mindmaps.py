#!/usr/bin/env python3
"""批量生成外部套件的套件级思维导图 YAML(供 build_index 内联成 SVG)。

约定文件名:mindmaps/suite-<namespace 的 slug>.yaml(与 suites/<slug>.html 对齐)。
分组按 i18n-ext.json 里已赋的 category,叶子用 name-zh(缺省回退英文名)。
大套件按组截断,避免 818 节点的巨型 SVG。
用法:
  python scripts/gen_suite_mindmaps.py [--dry-run]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL = ROOT / "external.json"
I18N = ROOT / "showcase" / "i18n-ext.json"
MINDMAPS = ROOT / "showcase" / "mindmaps"

CATEGORY_ZH = {
    "reverse-engineering": "逆向工程",
    "pentest": "渗透测试",
    "malware": "样本分析",
    "forensics": "内存取证",
    "data": "数据抓取",
    "dev-workflow": "工程流程",
    "engineering-hygiene": "工程纪律",
    "web-frontend": "Web 前端",
    "ai-media": "AI 媒体",
}

# 每个分类组最多展示的叶子数,超出用「……等 N 个」兜底
MAX_LEAVES_PER_GROUP = 18


def slug(ns: str) -> str:
    return re.sub(r"[^\w.-]+", "--", ns)


def yaml_line(indent: int, text: str) -> str:
    return "  " * indent + text


def main():
    dry = "--dry-run" in sys.argv
    ext = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    i18n = json.loads(I18N.read_text(encoding="utf-8"))

    targets = [
        "dhicoc/dsh-reverse-skill",
        "thirdwatch-dev/scraping-skills",
        "Nimbleway/agent-skills",
        "Johell1NS/browser-search",
        "mukul975/Anthropic-Cybersecurity-Skills",
        "zhaoxuya520/reverse-skill",
        "elementalsouls/Claude-BugHunter",
        "SnailSploit/Claude-Red",
        "ljagiello/ctf-skills",
        "yaklang/hack-skills",
        "newliver666/apk-reverse",
        "rehan-remade/universal-modder",
    ]

    written = 0
    for suite in ext.get("suites", []):
        ns = suite.get("namespace", "")
        if ns not in targets:
            continue
        skills = suite.get("skills", [])
        if not skills:
            continue

        # 分组:category -> [leaf labels]
        groups = {}
        for sk in skills:
            name = sk.get("name", "")
            entry = (i18n.get(ns) or {}).get(name) or {}
            cat = entry.get("category", "pentest")
            label = entry.get("name-zh") or name
            groups.setdefault(cat, []).append(label)

        lines = [f"root: {ns} 套件", "children:"]
        for cat, labels in groups.items():
            lines.append(yaml_line(1, f"- label: {CATEGORY_ZH.get(cat, cat)}"))
            lines.append(yaml_line(2, "children:"))
            shown = labels[:MAX_LEAVES_PER_GROUP]
            for lab in shown:
                lines.append(yaml_line(3, f"- label: {lab}"))
            if len(labels) > MAX_LEAVES_PER_GROUP:
                lines.append(yaml_line(3, f"- label: ……等 {len(labels)} 个"))

        out = MINDMAPS / f"suite-{slug(ns)}.yaml"
        if dry:
            print(f"[dry-run] {out.name}: {len(skills)} 技能, {len(groups)} 组")
        else:
            out.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"[+] {out.name}: {len(skills)} 技能 -> {len(groups)} 组")
            written += 1

    print(f"[+] 套件导图 {written} 个" if not dry else "[dry-run] 未写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
