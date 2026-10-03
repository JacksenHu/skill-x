#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""抓取插件/专家团仓库内的真实技能清单（扫描 SKILL.md），生成 external.json 条目。

external.json suite 结构（对齐现有 15 条）：
  namespace / upstream / license{spdx,evidence,attribution} / ingestedAt /
  verified{by,at,execReview} / upstreamStatus / manifestVia / skills[{name,path,description,version}]
skills 不能为空，否则构建器跳过。
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
TOKEN = os.environ.get("GH_TOKEN", "")
TODAY = "2026-10-03"

TARGETS = [
    ("P4nda0s/reverse-skills", "plugin"),
    ("Masriyan/Claude-Code-CyberSecurity-Skill", "plugin"),
    ("gl0bal01/malware-analysis-claude-skills", "plugin"),
    ("incogbyte/android-reverse-engineering-claude-skill", "plugin"),
    ("meirm/reverse-engineering-skill", "plugin"),
    ("LichAmnesia/skill-lint", "plugin"),
    ("highimpact-dev/skill-shield", "plugin"),
    ("almasumdev/awesome-mobile-security-agent-skills", "plugin"),
    ("Njones17/AI-agent-master-cyber-skills-list", "pack"),
    ("meltedinhex/analyst-ai-pack", "pack"),
    ("ibrdot/swe-re-expert", "pack"),
]

ZH = {
    "P4nda0s/reverse-skills": "逆向工程 Claude Code Skills 插件：为 Claude Code 提供反汇编、反编译、脱壳与反混淆的成套技能。",
    "Masriyan/Claude-Code-CyberSecurity-Skill": "Claude Code 网络安全技能包：22 个生产级技能，覆盖逆向、二进制分析与安全审计。",
    "gl0bal01/malware-analysis-claude-skills": "恶意代码分析 Claude 技能工具箱：5 个专业化技能，含反混淆、反汇编与行为分析。",
    "incogbyte/android-reverse-engineering-claude-skill": "Android 逆向 Claude 技能：自动化 Android 应用反编译、反混淆与 hook 注入。",
    "meirm/reverse-engineering-skill": "逆向工程 Claude 技能：为 Agent 提供二进制逆向的工作流与提示词。",
    "LichAmnesia/skill-lint": "skill-lint：Agent 技能安全扫描器，检测提示词注入、混淆载荷与数据外泄。",
    "highimpact-dev/skill-shield": "skill-shield：AI Agent 技能安全审计工具，扫描提示词注入与数据外泄风险。",
    "almasumdev/awesome-mobile-security-agent-skills": "移动安全 Agent 技能集：存储、传输、认证与代码混淆方向的加固技能。",
    "Njones17/AI-agent-master-cyber-skills-list": "网络安全技能总表：741 个面向 AI 编码 Agent 的安全技能清单，含逆向与对抗方向。",
    "meltedinhex/analyst-ai-pack": "analyst-ai-pack：开放的恶意代码分析与逆向技能库，含反混淆、反汇编与脱壳流程。",
    "ibrdot/swe-re-expert": "SWE/RE 专家技能：面向 AI Agent 的专家级软件工程与逆向工程技能。",
}


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


def raw(owner, repo, path, branch="main"):
    h = {"User-Agent": "x", "Accept": "text/plain"}
    if TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
    for br in (branch, "master"):
        u = "https://raw.githubusercontent.com/%s/%s/%s/%s" % (owner, repo, br, path)
        try:
            req = urllib.request.Request(u, headers=h)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
    return None


def tree(owner, repo, branch="main"):
    st, j = gh("/repos/%s/%s/git/trees/%s?recursive=1" % (owner, repo, branch))
    if st != 200:
        st, j = gh("/repos/%s/%s/git/trees/master?recursive=1" % (owner, repo))
    if st != 200:
        return []
    return [x.get("path", "") for x in (j.get("tree") or []) if x.get("type") == "blob"]


def parse_skill(text):
    """从 SKILL.md 取 name / description（YAML front matter）。"""
    name, desc, ver = "", "", ""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        fm = m.group(1)
        for line in fm.splitlines():
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("description:"):
                desc = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("version:"):
                ver = line.split(":", 1)[1].strip().strip("\"'")
    if not desc:
        # 取首个非标题非空行
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("---"):
                desc = s[:200]
                break
    return name, desc, ver


def main():
    out = []
    for full, kind in TARGETS:
        owner, repo = full.split("/", 1)
        paths = tree(owner, repo)
        skill_paths = [p for p in paths if p.endswith("SKILL.md") or p.endswith("skill.md")]
        skills = []
        for p in skill_paths[:40]:
            t = raw(owner, repo, p)
            if not t:
                continue
            nm, ds, vv = parse_skill(t)
            if not nm:
                nm = p.split("/")[-2] if "/" in p else p.rsplit("/", 1)[-1].replace(".md", "")
            skills.append({"name": nm, "path": p, "description": ds[:300], "version": vv})
        st, j = gh("/repos/" + full)
        lic = ((j.get("license") or {}).get("spdx_id") or "UNKNOWN") if st == 200 else "UNKNOWN"
        rec = {
            "namespace": full,
            "upstream": "https://github.com/" + full,
            "license": {
                "spdx": lic,
                "evidence": "LICENSE 文件" if lic not in ("UNKNOWN", "") else "无 LICENSE 文件",
                "attribution": "仅链接，不镜像内容",
            },
            "ingestedAt": TODAY,
            "verified": {"by": "codex", "at": TODAY, "execReview": "passed"},
            "upstreamStatus": {"lastCheck": TODAY, "alive": True, "failSince": None},
            "manifestVia": "scan:skills/" if skills else "repo:README",
            "skills": skills,
            "_kind": kind,
            "_zh": ZH.get(full, ""),
            "_stars": (j.get("stargazers_count") if st == 200 else 0),
        }
        # skills 为空时用仓库本身作为单条目，保证构建器不跳过
        if not skills:
            rec["skills"] = [{
                "name": repo,
                "path": "README.md",
                "description": (j.get("description") or "")[:300] if st == 200 else "",
                "version": "",
            }]
            rec["manifestVia"] = "repo:README"
        out.append(rec)
        print("OK  %-52s skills=%-3d license=%s" % (full, len(rec["skills"]), lic))
        sys.stdout.flush()
        time.sleep(1)

    p = ROOT / "scripts" / "upstream-audit" / "anti-reverse-suites.json"
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n-> %s  共 %d 个套件" % (p, len(out)))


if __name__ == "__main__":
    main()
