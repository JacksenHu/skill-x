#!/usr/bin/env python3
"""Skill X 橱窗站构建器 v2(纯标准库):多页 + 静态搜索。

页面结构:
  dist/index.html                 首页(统计/搜索/自研卡/套件卡)
  dist/skills/own-<name>.html     自研 skill 介绍页(仅元数据,安装需授权)
  dist/skills/ext-<ns>--<name>.html  收录 skill 介绍页(完整 description+上游安装命令)
  dist/suites/<ns-slug>.html      套件详情页
  dist/site-data.json             数据层(供后续 Functions/搜索使用)

红线:自研 SKILL.md 正文绝不进任何产物;构建期对全部 HTML 做泄露断言。
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

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;background:#f6f7f9;color:#1a1d24;line-height:1.6}
.hero{background:linear-gradient(135deg,#1a1d24,#2d3748);color:#fff;padding:48px 24px 40px}
.hero h1{font-size:32px;letter-spacing:1px}
.hero p{margin-top:8px;opacity:.75;max-width:760px;font-size:14px}
.stats{margin-top:16px;display:flex;gap:22px;font-size:13px}
.stats b{font-size:20px;display:block;color:#7dd3fc}
.wrap{max-width:1080px;margin:0 auto;padding:28px 24px 64px}
.search{margin:-22px auto 8px;max-width:640px;position:relative;z-index:2}
.search input{width:100%;padding:12px 16px;border:1px solid #e5e7eb;border-radius:10px;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.search input:focus{outline:2px solid #0ea5e9}
h2{margin:26px 0 14px;font-size:19px;border-left:4px solid #0ea5e9;padding-left:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px 18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}
.card h3,.card h4{font-size:15px;font-family:ui-monospace,Consolas,monospace}
.card h3 a,.card h4 a{color:#1a1d24;text-decoration:none}
.card h3 a:hover,.card h4 a:hover{color:#0ea5e9}
.card p{font-size:13px;color:#4b5563;margin-top:8px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.badge{font-size:11px;padding:2px 8px;border-radius:99px;white-space:nowrap}
.badge.auth{background:#fef3c7;color:#92400e}
.badge.ext{background:#dcfce7;color:#166534}
.badge.own{background:#e0f2fe;color:#075985}
.meta{margin-top:10px;font-size:12px;color:#9ca3af}
.suite{margin-bottom:26px}
.suite h3{font-size:16px;font-family:ui-monospace,Consolas,monospace;margin-bottom:12px}
.suite-meta{font-size:12px;color:#9ca3af}
.suite-meta a{color:#0ea5e9;text-decoration:none}
.notice{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:14px 18px;font-size:13px;color:#92400e;margin-top:14px}
.detail{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:28px 32px;margin-top:18px}
.detail h1{font-size:22px;font-family:ui-monospace,Consolas,monospace}
.detail .desc{margin:16px 0;color:#374151;font-size:15px;white-space:pre-wrap}
.kv{display:grid;grid-template-columns:110px 1fr;gap:8px;font-size:13px;margin:18px 0;padding:14px;background:#f9fafb;border-radius:8px}
.kv dt{color:#9ca3af}.kv dd{font-family:ui-monospace,Consolas,monospace;word-break:break-all}
.cmd{background:#1a1d24;color:#7dd3fc;padding:14px 16px;border-radius:8px;font-family:ui-monospace,Consolas,monospace;font-size:13px;overflow-x:auto;margin:10px 0;user-select:all}
.back{font-size:13px;color:#0ea5e9;text-decoration:none}
.hidden{display:none!important}
.empty{color:#9ca3af;font-size:14px;padding:20px;text-align:center}
footer{text-align:center;font-size:12px;color:#9ca3af;padding:24px}
"""

SEARCH_JS = """
const q = document.getElementById('q');
if (q) {
  const items = [...document.querySelectorAll('[data-search]')];
  q.addEventListener('input', () => {
    const v = q.value.trim().toLowerCase();
    let visible = 0;
    items.forEach(el => {
      const hit = !v || el.dataset.search.includes(v);
      el.classList.toggle('hidden', !hit);
      if (hit) visible++;
    });
    const empty = document.getElementById('empty');
    if (empty) empty.classList.toggle('hidden', visible > 0);
  });
}
"""


def esc(s):
    return html.escape(s or "", quote=True)


def parse_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ""
    fields, end = {}, None
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
    return fields, "\n".join(lines[end + 1:])


def collect_own_skills():
    skills, bodies = [], []
    for f in sorted(SKILLS_DIR.rglob("SKILL.md")):
        if f.is_symlink():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(text)
        m = re.search(r"version:\s*[\"']?([\w.-]+)", text)
        skills.append({
            "name": fm.get("name", f.parent.name),
            "description": fm.get("description", ""),
            "version": m.group(1) if m else "",
            "license": fm.get("license", ""),
            "page": f"skills/own-{fm.get('name', f.parent.name)}.html",
        })
        bodies.append(body)
    return skills, bodies


def collect_external():
    if not EXTERNAL.is_file():
        return []
    doc = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    return [s for s in doc.get("suites", []) if s.get("verified", {}).get("execReview") == "passed"]


def ns_slug(ns: str) -> str:
    return re.sub(r"[^\w.-]+", "--", ns)


def leak_assert(pages: dict, bodies):
    for path, text in pages.items():
        for body in bodies:
            samples = [ln.strip() for ln in body.splitlines() if len(ln.strip()) >= 40][:5]
            for s in samples:
                if s in text or esc(s) in text:
                    raise SystemExit(f"[FAIL] 泄露断言命中 {path}: {s[:60]}...")
    print(f"[+] 泄露断言通过({len(pages)} 页 x {len(bodies)} 个自研正文)")


def page_shell(title: str, inner: str) -> str:
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Skill X</title>
<style>{CSS}</style></head><body>
<div class="wrap">{inner}</div>
<footer><a class="back" href="/">← 返回首页</a> · Skill X · Agent Skills 开放规范</footer>
<script>{SEARCH_JS}</script>
</body></html>'''


def render_own_detail(s):
    inner = f'''<div class="detail">
  <div class="card-head"><h1>{esc(s["name"])}</h1><span class="badge auth">安装需授权</span></div>
  <p class="desc">{esc(s["description"])}</p>
  <dl class="kv">
    <dt>类型</dt><dd>自研(私有分发)</dd>
    <dt>版本</dt><dd>v{esc(s["version"] or "1.0.0")}</dd>
    <dt>许可证</dt><dd>{esc(s["license"] or "MIT")}</dd>
  </dl>
  <p style="font-size:13px;color:#92400e">获得授权的协作者可安装:</p>
  <div class="cmd">GITHUB_TOKEN=&lt;PAT&gt; npx skills add JacksenHu/skill-x --skill {esc(s["name"])}</div>
</div>'''
    return page_shell(s["name"], inner)


def render_ext_detail(suite, s):
    ns = suite["namespace"]
    lic = suite["license"]["spdx"]
    inner = f'''<div class="detail">
  <div class="card-head"><h1>{esc(s["name"])}</h1><span class="badge ext">社区收录</span></div>
  <p class="desc">{esc(s["description"])}</p>
  <dl class="kv">
    <dt>套件</dt><dd>{esc(ns)}</dd>
    <dt>版本</dt><dd>{esc(s.get("version") or "—")}</dd>
    <dt>许可证</dt><dd>{esc(lic if lic != "UNKNOWN" else "未确认(仅链接收录)")}</dd>
    <dt>上游文件</dt><dd>{esc(s["path"])}</dd>
  </dl>
  <p style="font-size:13px;color:#166534">一条命令安装(指向上游仓库):</p>
  <div class="cmd">npx skills add {esc(ns)} --skill {esc(s["name"])}</div>
  <p style="font-size:12px;color:#9ca3af">来源:<a href="{esc(suite["upstream"])}" style="color:#0ea5e9">{esc(suite["upstream"])}</a></p>
</div>'''
    return page_shell(s["name"], inner)


def render_suite(suite):
    ns = suite["namespace"]
    lic = suite["license"]["spdx"]
    cards = []
    for s in suite["skills"]:
        page = f"../skills/ext-{ns_slug(ns)}--{s['name']}.html"
        cards.append(f'''<div class="card ext" data-search="{esc((s["name"] + " " + s["description"]).lower())}">
  <div class="card-head"><h4><a href="{page}">{esc(s["name"])}</a></h4><span class="badge ext">社区收录</span></div>
  <p>{esc(s["description"][:260])}</p>
</div>''')
    inner = f'''<div class="detail">
  <h1>{esc(ns)}</h1>
  <dl class="kv">
    <dt>skill 数</dt><dd>{len(suite["skills"])}</dd>
    <dt>许可证</dt><dd>{esc(lic if lic != "UNKNOWN" else "未确认(仅链接收录)")}</dd>
    <dt>收录日期</dt><dd>{esc(suite.get("ingestedAt", ""))}</dd>
    <dt>上游</dt><dd><a href="{esc(suite["upstream"])}" style="color:#0ea5e9">{esc(suite["upstream"])}</a></dd>
  </dl>
  <p style="font-size:13px;color:#166534">整套件安装:</p>
  <div class="cmd">npx skills add {esc(ns)} --skill '*'</div>
</div>
<h2>套件内技能</h2>
<div class="grid">{"".join(cards)}</div>'''
    return page_shell(ns, inner)


def render_index(own, suites):
    total_ext = sum(len(s["skills"]) for s in suites)
    own_cards = "\n".join(
        f'''<div class="card own" data-search="{esc((s["name"] + " " + s["description"]).lower())}">
  <div class="card-head"><h3><a href="{s["page"]}">{esc(s["name"])}</a></h3><span class="badge auth">安装需授权</span></div>
  <p>{esc(s["description"])}</p>
  <div class="meta">v{esc(s["version"] or "1.0.0")} · {esc(s["license"] or "MIT")} · 自研</div>
</div>''' for s in own)

    suite_sections = []
    for suite in suites:
        ns = suite["namespace"]
        lic = suite["license"]["spdx"]
        lic_badge = lic if lic != "UNKNOWN" else "许可证未确认"
        items = "\n".join(
            f'''<div class="card ext" data-search="{esc((s["name"] + " " + s["description"]).lower())}">
  <div class="card-head"><h4><a href="skills/ext-{ns_slug(ns)}--{s["name"]}.html">{esc(s["name"])}</a></h4><span class="badge ext">社区收录</span></div>
  <p>{esc(s["description"][:260])}</p>
</div>''' for s in suite["skills"])
        suite_sections.append(f'''<section class="suite">
  <h3><a href="suites/{ns_slug(ns)}.html" style="color:inherit;text-decoration:none">{esc(ns)}</a> <span class="suite-meta">{len(suite["skills"])} skills · {esc(lic_badge)} · <a href="{esc(suite["upstream"])}">上游</a></span></h3>
  <div class="grid">{items}</div>
</section>''')

    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skill X — Agent Skills 注册中心</title>
<style>{CSS}</style></head><body>
<div class="hero">
  <h1>Skill X</h1>
  <p>面向所有 Agent 的安全研究与逆向工程技能注册中心。自研技能经私有渠道授权分发;社区收录技能可一键指向上游安装。</p>
  <div class="stats">
    <span><b>{len(own)}</b>自研技能</span>
    <span><b>{total_ext}</b>社区收录</span>
    <span><b>{len(suites)}</b>收录套件</span>
  </div>
</div>
<div class="wrap">
  <div class="search"><input id="q" type="search" placeholder="搜索技能名称或关键词(如 逆向 / pentest / memory / TDD)…"></div>
  <div id="empty" class="empty hidden">没有匹配的技能</div>
  <h2>自研技能</h2>
  <div class="grid">{own_cards}</div>
  <div class="notice">自研技能经私有仓库授权分发。获得授权的协作者:<code>GITHUB_TOKEN=&lt;PAT&gt; npx skills add JacksenHu/skill-x --skill &lt;name&gt;</code>。申请授权请联系仓库所有者。</div>
  <h2>社区收录套件</h2>
  {"".join(suite_sections) if suite_sections else "<p>暂无收录</p>"}
</div>
<footer>Skill X · Agent Skills 开放规范(agentskills.io)· 橱窗仅展示元数据</footer>
<script>{SEARCH_JS}</script>
</body></html>'''


def main():
    own, bodies = collect_own_skills()
    suites = collect_external()

    pages = {"index.html": render_index(own, suites)}
    for s in own:
        pages[s["page"]] = render_own_detail(s)
    for suite in suites:
        ns = suite["namespace"]
        pages[f"suites/{ns_slug(ns)}.html"] = render_suite(suite)
        for s in suite["skills"]:
            pages[f"skills/ext-{ns_slug(ns)}--{s['name']}.html"] = render_ext_detail(suite, s)

    leak_assert(pages, bodies)

    for rel, text in pages.items():
        p = DIST / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    site_data = {
        "own": own,
        "suites": [{"namespace": s["namespace"], "upstream": s["upstream"],
                    "license": s["license"]["spdx"], "skillCount": len(s["skills"]),
                    "skills": [{"name": x["name"], "description": x["description"]} for x in s["skills"]]}
                   for s in suites],
    }
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "site-data.json").write_text(json.dumps(site_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] 产物 {len(pages)} 页 -> {DIST}(自研 {len(own)},套件 {len(suites)},收录 {sum(len(s['skills']) for s in suites)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
