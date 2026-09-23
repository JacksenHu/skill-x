#!/usr/bin/env python3
"""API 文档自动提取:从 skills/*/scripts/*.py 的 argparse 定义提取参数说明(AST 解析,不执行脚本)。

产出供 build_index.py 的 render_api 使用:
  { "skill-name": [ {"script": "scripts/xxx.py", "args": [("--flag", "help 文本"), ...]}, ... ] }
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"


def extract_args(py_path: Path):
    """提取单个脚本的 add_argument 定义 -> [(flags, help)]。"""
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            continue
        flags, help_text, action = [], "", ""
        for a in node.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                flags.append(a.value)
        for kw in node.keywords:
            if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                help_text = str(kw.value.value)
            if kw.arg == "action" and isinstance(kw.value, ast.Constant):
                action = str(kw.value.value)
        flag_str = " / ".join(flags) if flags else "(positional)"
        if action:
            help_text = f"[{action}] {help_text}".strip()
        out.append((flag_str, help_text))
    return out


def extract_docstring(py_path: Path) -> str:
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8", errors="replace"))
        doc = ast.get_docstring(tree) or ""
        return doc.strip().splitlines()[0] if doc.strip() else ""
    except SyntaxError:
        return ""


def collect():
    """全部自研 skill 的脚本参数文档。"""
    docs = {}
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.is_dir():
            continue
        entries = []
        for py in sorted(scripts_dir.glob("*.py")):
            entries.append({
                "script": f"scripts/{py.name}",
                "summary": extract_docstring(py),
                "args": extract_args(py),
            })
        if entries:
            docs[skill_dir.name] = entries
    return docs


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), ensure_ascii=False, indent=2)[:2000])
