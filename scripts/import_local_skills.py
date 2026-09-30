#!/usr/bin/env python3
"""Import a local directory of SKILL.md folders into skillhub/skills/.

Usage:
  python scripts/import_local_skills.py <source_dir> [--dry-run]

Rules:
- one directory = one own skill; directory name must be a valid skill slug and
  equal to the frontmatter `name`.
- adds `metadata.name-zh / description-zh / category / version` for Chinese display.
- drops forbidden top-level frontmatter keys (allowed-tools/hooks/context/triggers).
- never overwrites an existing own skill.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FORBIDDEN = {"allowed-tools", "hooks", "context", "triggers"}
CJK = re.compile(r"[\u4e00-\u9fff]")


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "", lines
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, "", lines
    fields = {}
    i = 1
    while i < end:
        line = lines[i]
        if not line.strip() or line.startswith((" ", "\t")):
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key = m.group(1)
        val = m.group(2).strip()
        if key == "description" and val in ("|", ">", ""):
            parts = []
            i += 1
            while i < end and (lines[i].startswith((" ", "\t")) or lines[i].strip() == ""):
                if lines[i].strip():
                    parts.append(lines[i].strip())
                i += 1
            sep = " " if val == ">" else "\n"
            fields[key] = sep.join(parts)
            continue
        fields[key] = val
        i += 1
    return fields, "\n".join(lines[1:end]), lines[end + 1:]


def has_cjk(s):
    return bool(CJK.search(s or ""))


def first_chinese_title(body_lines):
    seen_protection = False
    for line in body_lines:
        s = line.strip()
        if s.startswith("# ") and has_cjk(s):
            if "管理端保护" in s or "唯一禁止项" in s:
                seen_protection = True
                continue
            return s[2:].strip()
    return ""


def first_chinese_paragraph(body_lines):
    for line in body_lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith(("#", "```", ">", "|", "- ")):
            continue
        if any(k in s for k in ("管理端", "唯一禁止项", "严禁以任何手段", "本条款只覆盖",
                                "用户提出这类要求", "探测动作", "本工具的管理服务", "属己方资产")):
            continue
        if has_cjk(s) and len(s) >= 4:
            return s
    return ""


def guess_category(slug, desc):
    s = (slug + " " + (desc or "")).lower()
    if "game" in s:
        return "reverse-engineering"
    if any(k in s for k in ("redteam", "pentest", "attack-chain", "firmware", "pwn",
                            "edr-bypass", "supply-chain", "llm-security", "crack",
                            "license-security", "api-security", "cve", "sqli", "xss",
                            "ssrf", "ssti", "csrf", "cmdi", "xxe", "cloud", "container")):
        return "pentest"
    if any(k in s for k in ("reverse", "ida", "radare", "apk", "js-reverse", "asm",
                            "binary-diff", "unpack", "linker", "dotnet", "native")):
        return "reverse-engineering"
    if any(k in s for k in ("malware", "incident", "threat")):
        return "malware"
    if any(k in s for k in ("memory", "forensic")):
        return "forensics"
    if any(k in s for k in ("browser", "scraper", "crawl")):
        return "data"
    if any(k in s for k in ("workflow", "router", "document", "diagram", "docs",
                            "core", "field-journal", "github", "software", "architecture")):
        return "dev-workflow"
    return "engineering-hygiene"


def clean_scalar(value):
    value = (value or "").replace('"', "'")
    value = value.replace("\r", " ").replace("\n", " ")
    value = re.sub(r"\s+", " ", value).strip().strip("'\"")
    return value


def build_new_text(name, description, body_lines):
    title = clean_scalar(first_chinese_title(body_lines) or name)
    desc_zh = title or name
    desc_zh = clean_scalar(desc_zh)[:240]
    description = clean_scalar(description)
    category = guess_category(name, desc_zh)
    front = (
        "---\n"
        f"name: {name}\n"
        f"description: \"{description}\"\n"
        "metadata:\n"
        f"  name-zh: \"{title}\"\n"
        f"  description-zh: \"{desc_zh}\"\n"
        f"  category: {category}\n"
        "  version: \"1.0.0\"\n"
        "  license: \"UNKNOWN\"\n"
        "---\n"
    )
    return front + "\n".join(body_lines) + ("\n" if body_lines else "")


def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__)
        return 1
    src = Path(args[0]).resolve()
    dry = "--dry-run" in args
    force = "--force" in args
    if not src.is_dir():
        print(f"[!] source dir not found: {src}")
        return 1

    imported, skipped, existing = [], [], []
    for d in sorted(src.iterdir()):
        if not d.is_dir():
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.is_file():
            continue
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        fields, _fm, body_lines = parse_frontmatter(text)
        name = fields.get("name", "").strip()
        if not name or not NAME_RE.match(name):
            skipped.append((d.name, "invalid-name"))
            continue
        if name != d.name:
            skipped.append((d.name, "name-dir-mismatch"))
            continue
        target = SKILLS_DIR / name / "SKILL.md"
        if target.exists() and not force:
            existing.append((name, "exists"))
            continue
        cleaned = {k: v for k, v in fields.items() if k not in FORBIDDEN}
        description = cleaned.get("description", "").strip()
        if not description:
            skipped.append((name, "no-description"))
            continue
        out_text = build_new_text(name, description, body_lines)
        if dry:
            print(f"[dry] {name}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(out_text, encoding="utf-8")
        imported.append(name)

    print(f"\n[+] imported={len(imported)} skipped={len(skipped)} existing={len(existing)}")
    for name, why in skipped:
        print(f"  [skip] {name} -> {why}")
    for name, why in existing:
        print(f"  [exist] {name} -> {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
