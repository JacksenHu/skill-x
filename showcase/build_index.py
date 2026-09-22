#!/usr/bin/env python3
"""Skill X 橱窗站构建器(纯标准库)。

红线:自研 skill 只输出 frontmatter 元数据(name/description/version/license),
SKILL.md 正文绝不进入产物。构建期做泄露断言:
产物 HTML 中不得出现任一自研正文 >=40 字符的样本行,命中即 fail。

输出:showcase/dist/index.html + showcase/dist/site-data.json
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
EXTERNAL = ROOT / "external.json"
DIST = Path(__file__).resolve().parent / "dist"


def parse_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ""
    fields = {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, ""
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            fields[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    body = "\n".join(lines[end + 1:])
    return fields, body


def collect_own_skills():
    skills, bodies = [], []
    for f in sorted(SKILLS_DIR.rglob("SKILL.md")):
        if f.is_symlink():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(text)
        version = ""
        m = re.search(r"version:\s*[\"']?([\w.-]+)", text)
        if m:
            version = m.group(1)
        skills.append({
            "name": fm.get("name", f.parent.name),
            "description": fm.get("description", ""),
            "version": version,
            "license": fm.get("license", ""),
        })
        bodies.append(body)
    return skills, bodies


def collect_external():
    if not EXTERNAL.is_file():
        return []
    doc = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    return [s for s in doc.get("suites", []) if s.get("verified", {}).get("execReview") == "passed"]


def leak_assert(html_text: str, bodies):
    for body in bodies:
        samples = [ln.strip() for ln in body.splitlines() if len(ln.strip()) >= 40][:5]
        for s in samples:
            if html.escape(s) in html_text or s in html_text:
                raise SystemExit(f"[FAIL] 泄露断言命中:产物含自研正文样本 -> {s[:60]}...")
    print(f"[+] 泄露断言通过({len(bodies)} 个自研正文 x 5 样本均未出现在产物)")


def esc(s):
    return html.escape(s or "", quote=True)


def render(own, suites):
    own_cards = "\n".join(
        f'''<div class="card own">
  <div class="card-head"><h3>{esc(s["name"])}</h3><span class="badge auth">安装需授权</span></div>
  <p>{esc(s["description"])}</p>
  <div class="meta">v{esc(s["version"] or "1.0.0")} · {esc(s["license"] or "MIT")} · 自研</div>
</div>''' for s in own)

    suite_sections = []
    total_ext = 0
    for suite in suites:
        total_ext += len(suite["skills"])
        lic = suite["license"]["spdx"]
        lic_badge = lic if lic != "UNKNOWN" else "许可证未确认"
        items = "\n".join(
            f'''<div class="card ext">
  <div class="card-head"><h4>{esc(s["name"])}</h4><span class="badge ext">社区收录</span></div>
  <p>{esc(s["description"][:300])}</p>
</div>''' for s in suite["skills"])
        suite_sections.append(f'''<section class="suite">
  <h3>{esc(suite["namespace"])} <span class="suite-meta">{len(suite["skills"])} skills · {esc(lic_badge)} · <a href="{esc(suite["upstream"])}">上游</a></span></h3>
  <div class="grid">{items}</div>
</section>''')

    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skill X — Agent Skills 注册中心</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:#f6f7f9;color:#1a1d24;line-height:1.6}}
.hero{{background:linear-gradient(135deg,#1a1d24,#2d3748);color:#fff;padding:56px 24px 48px}}
.hero h1{{font-size:34px;letter-spacing:1px}}
.hero p{{margin-top:10px;opacity:.75;max-width:720px}}
.stats{{margin-top:18px;display:flex;gap:22px;font-size:14px}}
.stats b{{font-size:22px;display:block;color:#7dd3fc}}
.wrap{{max-width:1080px;margin:0 auto;padding:32px 24px 64px}}
h2{{margin:28px 0 16px;font-size:20px;border-left:4px solid #0ea5e9;padding-left:10px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.card h3,.card h4{{font-size:15px;font-family:ui-monospace,Consolas,monospace}}
.card p{{font-size:13px;color:#4b5563;margin-top:8px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.card-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}}
.badge{{font-size:11px;padding:2px 8px;border-radius:99px;white-space:nowrap}}
.badge.auth{{background:#fef3c7;color:#92400e}}
.badge.ext{{background:#dcfce7;color:#166534}}
.meta{{margin-top:10px;font-size:12px;color:#9ca3af}}
.suite{{margin-bottom:28px}}
.suite h3{{font-size:16px;font-family:ui-monospace,Consolas,monospace;margin-bottom:12px}}
.suite-meta{{font-size:12px;color:#9ca3af;font-family:inherit}}
.suite-meta a{{color:#0ea5e9;text-decoration:none}}
.notice{{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:14px 18px;font-size:13px;color:#92400e;margin-top:14px}}
footer{{text-align:center;font-size:12px;color:#9ca3af;padding:24px}}
</style></head><body>
<div class="hero">
  <h1>Skill X</h1>
  <p>面向所有 Agent 的安全研究与逆向工程技能注册中心。自研技能经私有渠道授权分发;社区收录技能可直接指向上游安装。</p>
  <div class="stats">
    <span><b>{len(own)}</b>自研技能</span>
    <span><b>{total_ext}</b>社区收录</span>
    <span><b>{len(suites)}</b>收录套件</span>
  </div>
</div>
<div class="wrap">
  <h2>自研技能</h2>
  <div class="grid">{own_cards}</div>
  <div class="notice">自研技能经私有仓库授权分发。获得授权的协作者:<code>GITHUB_TOKEN=&lt;PAT&gt; npx skills add JacksenHu/skill-x --skill &lt;name&gt;</code>。申请授权请联系仓库所有者。</div>
  <h2>社区收录套件</h2>
  {"".join(suite_sections) if suite_sections else "<p>暂无收录</p>"}
</div>
<footer>Skill X · Agent Skills 开放规范(agentskills.io)· 橱窗仅展示元数据</footer>
</body></html>'''


def main():
    own, bodies = collect_own_skills()
    suites = collect_external()
    page = render(own, suites)
    leak_assert(page, bodies)

    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "index.html").write_text(page, encoding="utf-8")
    site_data = {
        "own": own,
        "suites": [{"namespace": s["namespace"], "upstream": s["upstream"],
                    "license": s["license"]["spdx"], "skillCount": len(s["skills"])} for s in suites],
    }
    (DIST / "site-data.json").write_text(json.dumps(site_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] 产物: {DIST / 'index.html'} ({len(page)//1024} KB), 自研 {len(own)}, 收录套件 {len(suites)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
