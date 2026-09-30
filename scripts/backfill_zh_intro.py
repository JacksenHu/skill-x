#!/usr/bin/env python3
"""Backfill concise Chinese descriptions for imported own skills."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

TEMPLATES = {
    "reverse-engineering": "逆向工程技能「{title}」，覆盖脱壳、反汇编、结构与算法还原等分析流程。",
    "pentest": "渗透测试技能「{title}」，覆盖授权范围内的攻击面识别、精确验证与证据要求。",
    "malware": "恶意样本分析技能「{title}」，覆盖样本分诊、脱壳、行为观测与检测产出。",
    "forensics": "取证分析技能「{title}」，覆盖证据提取、时间线还原与结论验证。",
    "data": "数据采集技能「{title}」，覆盖网页抓取、数据抽取与清洗入库。",
    "dev-workflow": "工程流程技能「{title}」，覆盖任务编排、阶段推进与交付规范。",
    "engineering-hygiene": "工程纪律技能「{title}」，覆盖验证、审计与结果可信度管理。",
}

DEFAULT_TEMPLATE = "「{title}」相关技能，按授权范围与工程纪律执行分析、验证与交付。"


def parse_meta(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    in_meta = False
    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m:
            in_meta = m.group(1) == "metadata"
            continue
        if in_meta:
            mm = re.match(r"^\s+([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
            if mm:
                meta[mm.group(1)] = mm.group(2).strip().strip("\"'")
    return meta


def main():
    names = sys.argv[1:]
    targets = names if names else None
    changed = 0
    for f in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        meta = parse_meta(text)
        if meta.get("license") != "UNKNOWN" or meta.get("version") != "1.0.0":
            continue
        name = f.parent.name
        if targets is not None and name not in targets:
            continue
        title = meta.get("name-zh") or name
        category = meta.get("category") or "engineering-hygiene"
        intro = TEMPLATES.get(category, DEFAULT_TEMPLATE).format(title=title)
        # 替换已有的单行 description-zh
        new_text, n = re.subn(
            r'^\s+description-zh:.*$',
            f'  description-zh: "{intro}"',
            text,
            count=1,
            flags=re.M
        )
        if n:
            f.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"[+] changed={changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
