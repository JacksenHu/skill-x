#!/usr/bin/env python3
"""Generate category-based mindmap YAML files for imported own skills."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
MINDMAPS = ROOT / "showcase" / "mindmaps"

CATEGORY_MAPS = {
    "reverse-engineering": {
        "核心能力": ["目标识别", "脱壳与反汇编", "结构与算法还原"],
        "工具链": ["IDA / Ghidra", "Frida / radare2", "angr / 脚本"],
        "验证产出": ["函数与结构映射", "协议 / 格式重建", "可复现报告"],
    },
    "pentest": {
        "授权范围": ["范围固化", "攻击面枚举", "假设排序"],
        "精确验证": ["最小请求集", "异身份对照", "证据固化"],
        "修复复测": ["修复建议", "复测标准", "未闭环项"],
    },
    "malware": {
        "样本分诊": ["指纹登记", "壳与保护面", "目标清单"],
        "行为分析": ["动态观测", "配置提取", "C2 解码"],
        "检测产出": ["IOC", "YARA / Sigma", "分析报告"],
    },
    "forensics": {
        "证据获取": ["转储 / 镜像", "进程与模块", "关键字符串"],
        "结构分析": ["指针链", "签名扫描", "结构重建"],
        "结论验证": ["交叉验证", "时间线还原", "证据归档"],
    },
    "data": {
        "合规边界": ["授权范围", "robots / 条款", "频率控制"],
        "站点侦察": ["静态 / API", "渲染型页面", "反爬风险"],
        "抽取入库": ["样本抽取", "清洗去重", "质量验证"],
    },
    "dev-workflow": {
        "阶段编排": ["任务路由", "阶段推进", "交付规范"],
        "执行与验证": ["可复现命令", "证据记录", "验收检查"],
        "闭环交付": ["结果归档", "未闭环项", "后续动作"],
    },
    "engineering-hygiene": {
        "检查设计": ["参照物固定", "真红 / 假红", "收口范围"],
        "执行纪律": ["先量后改", "结构化验错", "回归归档"],
        "结果可信": ["证据账本", "变异自测", "可复现结论"],
    },
}

DEFAULT_MAP = {
    "核心能力": ["目标识别", "分析验证", "交付产出"],
    "工作流": ["范围确认", "逐步执行", "结果归档"],
    "适用场景": ["授权任务", "证据导向", "可复现验证"],
}


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


def yaml_for(title, category):
    groups = CATEGORY_MAPS.get(category, DEFAULT_MAP)
    lines = [f"root: {title}", "children:"]
    for group, leaves in groups.items():
        lines.append(f"  - label: {group}")
        lines.append("    children:")
        for leaf in leaves:
            lines.append(f"      - label: {leaf}")
    return "\n".join(lines) + "\n"


def main():
    changed = 0
    for f in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        meta = parse_meta(text)
        if meta.get("license") != "UNKNOWN" or meta.get("version") != "1.0.0":
            continue
        name = f.parent.name
        title = meta.get("name-zh") or name
        category = meta.get("category") or "engineering-hygiene"
        out = MINDMAPS / f"{name}.yaml"
        out.write_text(yaml_for(title, category), encoding="utf-8")
        changed += 1
    print(f"[+] generated={changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
