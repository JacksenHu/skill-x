#!/usr/bin/env python3
"""SkillHub SKILL.md 规范校验(零第三方依赖)。

检查项(对应 docs/skill-authoring-guide.md):
1. frontmatter 存在且闭合
2. name 必填、命名合规、与目录名一致
3. description 必填、<=1024 字符
4. 禁用顶层字段:allowed-tools / context / hooks / triggers
5. compatibility <=500 字符
6. 正文 <=500 行(超出请拆 references/)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FORBIDDEN_KEYS = {"allowed-tools", "context", "hooks", "triggers"}
MAX_DESC = 1024
MAX_COMPAT = 500
MAX_BODY_LINES = 500


def parse_frontmatter(text: str):
    """返回 ((顶层字段 dict, 正文行数), None) 或 (None, 错误信息)。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "缺少 frontmatter(首行必须是 ---)"
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, "frontmatter 未闭合(缺少结束 ---)"
    fields = {}
    for line in lines[1:end]:
        if not line.strip() or line.startswith((" ", "\t")):
            continue  # 跳过嵌套与列表行
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    body_lines = len(lines) - (end + 1)
    return (fields, body_lines), None


def check_skill(skill_md: Path):
    errors = []
    text = skill_md.read_text(encoding="utf-8")
    parsed, err = parse_frontmatter(text)
    if err:
        return [err]
    fields, body_lines = parsed

    name = fields.get("name", "")
    if not name:
        errors.append("缺少必填字段 name")
    else:
        if not NAME_RE.match(name):
            errors.append(f"name 不合规(需小写字母/数字/连字符): {name}")
        dir_name = skill_md.parent.name
        if name != dir_name:
            errors.append(f"name({name}) 与目录名({dir_name})不一致")

    desc = fields.get("description", "")
    if not desc:
        errors.append("缺少必填字段 description")
    elif len(desc) > MAX_DESC:
        errors.append(f"description 超长: {len(desc)} > {MAX_DESC}")

    for key in FORBIDDEN_KEYS:
        if key in fields:
            errors.append(f"禁用字段 {key}(跨 agent 不兼容;请删除或挪入 metadata)")

    compat = fields.get("compatibility", "")
    if len(compat) > MAX_COMPAT:
        errors.append(f"compatibility 超长: {len(compat)} > {MAX_COMPAT}")

    if body_lines > MAX_BODY_LINES:
        errors.append(f"正文 {body_lines} 行 > {MAX_BODY_LINES},请拆入 references/")

    return errors


def main():
    if not SKILLS_DIR.is_dir():
        print("[!] 未找到 skills/ 目录")
        return 1
    skill_files = sorted(SKILLS_DIR.rglob("SKILL.md"))
    if not skill_files:
        print("[!] skills/ 下未找到任何 SKILL.md")
        return 1

    failed = 0
    for f in skill_files:
        rel = f.relative_to(ROOT)
        errors = check_skill(f)
        if errors:
            failed += 1
            print(f"[FAIL] {rel}")
            for e in errors:
                print(f"       - {e}")
        else:
            print(f"[ OK ] {rel}")

    print(f"\n共 {len(skill_files)} 个 skill,{len(skill_files) - failed} 通过,{failed} 失败")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
