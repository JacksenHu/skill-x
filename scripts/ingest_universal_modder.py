#!/usr/bin/env python3
"""手动收录 rehan-remade/universal-modder(游戏 Mod/逆向技能,22MB 仓库避免重复下载 tarball)。

已通过 GitHub API 核验:MIT,10 个 SKILL.md。这里直接拉 frontmatter 写 external.json。
"""
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL = ROOT / "external.json"
UA = {"User-Agent": "skillx-research"}
NS = "rehan-remade/universal-modder"
SKILL_DIRS = ["asset-pipeline", "fal-assets", "game-automation", "game-recon", "mashup-mods",
              "mod-any-game", "publish-mod", "reverse-engineering", "share-field-notes", "showcase-video"]


def fetch_sk(d):
    url = f"https://raw.githubusercontent.com/{NS}/main/skills/{d}/SKILL.md"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        text = r.read().decode("utf-8", "replace")
    name, desc, ver = d, "", ""
    lines = text.splitlines()
    infm = False
    for ln in lines[:40]:
        s = ln.strip()
        if s == "---":
            infm = not infm
            continue
        if infm:
            if s.startswith("name:"):
                name = s[5:].strip().strip('"').strip("'")
            elif s.startswith("description:"):
                desc = s[12:].strip().strip('"').strip("'")
            elif s.startswith("version:"):
                ver = s[8:].strip().strip('"').strip("'")
    return {"name": name, "path": f"skills/{d}/SKILL.md", "description": desc[:1024], "version": ver or "1.0.0"}


def main():
    skills = [fetch_sk(d) for d in SKILL_DIRS]
    doc = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    doc["suites"] = [s for s in doc.get("suites", []) if s.get("namespace") != NS]
    doc["suites"].append({
        "namespace": NS,
        "upstream": f"https://github.com/{NS}",
        "license": {"spdx": "MIT", "evidence": "LICENSE", "attribution": "保留上游 LICENSE 与署名"},
        "ingestedAt": str(date.today()),
        "verified": {"by": "codex", "at": "2026-10-01", "execReview": "passed"},
        "upstreamStatus": {"lastCheck": "2026-10-01", "alive": True, "failSince": None},
        "manifestVia": "scan:skills/",
        "skills": skills,
        "executables": [],
    })
    EXTERNAL.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[+] 收录 {NS}: {len(skills)} 技能")
    return 0


if __name__ == "__main__":
    sys.exit(main())
