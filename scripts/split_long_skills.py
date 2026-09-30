#!/usr/bin/env python3
"""Move oversized SKILL.md bodies into references/ to keep the main file <= 500 lines."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
MAX_LINES = 500


def split_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", lines
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return "", lines
    return "\n".join(lines[:end + 1]), lines[end + 1:]


def main():
    names = sys.argv[1:]
    changed = []
    for name in names:
        f = SKILLS_DIR / name / "SKILL.md"
        if not f.is_file():
            print(f"[!] missing {f}")
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        front, body = split_frontmatter(text)
        if len(body) <= MAX_LINES:
            print(f"[skip] {name} ({len(body)} lines)")
            continue
        ref_dir = f.parent / "references"
        ref_dir.mkdir(parents=True, exist_ok=True)
        ref_file = ref_dir / "DETAIL.md"
        ref_file.write_text("\n".join(body) + "\n", encoding="utf-8")
        new_body = (
            f"# {name}\n\n"
            "本技能正文较长，完整操作说明已拆入渐进式披露文件：\n\n"
            "`references/DETAIL.md`\n\n"
            "请按任务需要加载该引用文件后继续执行。\n"
        )
        f.write_text(front + "\n\n" + new_body, encoding="utf-8")
        changed.append((name, len(body)))
    print(f"[+] split={len(changed)}")
    for name, n in changed:
        print(f"  - {name}: {n} -> references/DETAIL.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
