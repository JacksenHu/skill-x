#!/usr/bin/env python3
"""生成「安全工具商店」静态页 dist/tools.html,并把导航注入所有页面。

数据源:tools-store/catalog.json + categories.json(来自 security-tool-store 分拣)。
复用站内 .card/.chips/.cmd/.copy-btn 样式与 app.js 的 sxFilter/sxCopy。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOWCASE = ROOT / "showcase"
DIST = SHOWCASE / "dist"
TS = ROOT / "tools-store"

CAT_COLORS = {
    "recon": "data", "vuln": "pentest", "lab": "dev-workflow",
    "tunnel": "malware", "defense": "forensics", "intel": "reverse-engineering",
}


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def load():
    cats = json.loads((TS / "categories.json").read_text(encoding="utf-8"))["categories"]
    cat_meta = {c["id"]: c for c in cats}
    catalog = json.loads((TS / "catalog.json").read_text(encoding="utf-8"))
    tools = catalog["tools"]
    return cats, cat_meta, tools


def card(t, cat_meta):
    cat = t.get("category", "")
    cm = cat_meta.get(cat, {})
    name = t.get("name", "")
    name_zh = t.get("name_zh", "") or name
    deploy = t.get("deploy", "")
    form = t.get("form", "")
    ports = ",".join(str(p) for p in (t.get("ports") or []))
    install = t.get("install", "") or ""
    repo = t.get("repo", "")
    gitmcp = t.get("gitmcp")
    gm_url = f"https://gitmcp.io/{repo}" if gitmcp and repo else ""
    search = f"{name} {name_zh} {cat} {deploy} {form} {t.get('summary','')}".lower()
    color = CAT_COLORS.get(cat, "dev-workflow")
    meta = "".join([
        f'<span class="tag cat">{esc(cm.get("name", cat))}</span>',
        f'<span class="tag kind-ext">{esc(deploy)}</span>',
        f'<span class="tag kind-mcp">{esc(form)}</span>',
    ])
    if ports:
        meta += f'<span class="tag">端口 {esc(ports)}</span>'
    cmd_html = f'<div class="cmd">{esc(install)}</div>' if install else ""
    copy_btn = (f'<button class="chip on copy-btn" data-copy="{esc(install)}" data-skill="tool:{esc(name)}" '
                f'data-zh="复制部署命令" data-en="Copy deploy command">复制部署命令</button>') if install else ""
    gm_html = (f'<a class="hint-dim" href="{esc(gm_url)}" target="_blank" rel="noopener">gitmcp 上下文 ↗</a>') if gm_url else ""
    summary = t.get("summary", "") or ""
    return f'''<div class="card cat-{color}" data-search="{esc(search)}" data-category="{esc(cat)}">
  <h3><a href="https://github.com/{esc(repo)}" target="_blank" rel="noopener">{esc(name_zh)}</a></h3>
  <div class="en-name">{esc(name)}</div>
  <p>{esc(summary)}</p>
  <div class="meta">{meta}</div>
  {cmd_html}
  {copy_btn}
  {gm_html}
</div>'''


def page(cats, cat_meta, tools):
    chips = ['<span class="chip on" data-cat="" data-zh="全部" data-en="All">全部</span>']
    for c in cats:
        chips.append(f'<span class="chip" data-cat="{c["id"]}" data-zh="{esc(c["name"])}" data-en="{esc(c["name_en"])}">{esc(c["name"])}</span>')
    cards = "".join(card(t, cat_meta) for t in tools)
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>安全工具商店 · Skill X</title>
<link rel="stylesheet" href="/assets/style.css">
</head><body>
<div class="scroll-progress" aria-hidden="true"></div>
<div class="topnav">
  <a class="brand" href="/">Skill X</a>
  <a href="/" class="nav" data-zh="首页" data-en="Home">首页</a>
  <a href="/skills.html" class="nav" data-zh="技能" data-en="Skills">技能</a>
  <a href="/packages.html" class="nav" data-zh="专家团" data-en="Expert Packs">专家团</a>
  <a href="/mcp.html" class="nav" data-zh="MCP" data-en="MCP">MCP</a>
  <a href="/plugins.html" class="nav" data-zh="插件" data-en="Plugins">插件</a>
  <a href="/tools.html" class="nav active" data-zh="工具商店" data-en="Tool Store">工具商店</a>
  <a href="/api.html" class="nav" data-zh="API" data-en="API">API</a>
  <a href="/about.html" class="nav" data-zh="关于" data-en="About">关于</a>
  <button class="lang-btn">EN</button>
</div>
<div class="wrap">
<h2 data-zh="安全工具商店" data-en="Security Tool Store">安全工具商店 <span class="n">{len(tools)} 个 · 6 类</span></h2>
<p class="hint-dim" data-zh="面向已获授权的安全测试工具软件:一键部署 Docker 服务、二进制工具与靶场/蜜罐/情报平台。部署命令只做指路,本体走 Docker Hub / GitHub,不经过本站。工具未经本站代理。" data-en="Security tools for authorized testing: one-command deploy for Docker services, binaries, labs, honeypots and intel platforms. Deploy commands signpost to Docker Hub / GitHub; nothing is proxied through this site.">面向已获授权的安全测试工具软件:一键部署 Docker 服务、二进制工具与靶场/蜜罐/情报平台。部署命令只做指路,本体走 Docker Hub / GitHub,不经过本站。</p>
<div class="search"><input id="q" type="search" data-zh="按名称或关键词筛选工具…" data-en="Filter tools by name or keyword…" data-attr="placeholder" placeholder="按名称或关键词筛选工具…"></div>
<div class="chips">{''.join(chips)}</div>
<div class="grid">{cards}</div>
</div>
<footer><a href="/">Skill X</a> · 安全研究 / 逆向工程技能与工具库 · <a href="/about.html">关于</a></footer>
<script src="/assets/app.js"></script>
</body></html>
'''


def inject_nav():
    link = '<a href="/tools.html" class="nav" data-zh="工具商店" data-en="Tool Store">工具商店</a>'
    for p in DIST.glob("*.html"):
        html = p.read_text(encoding="utf-8", errors="replace")
        if '/tools.html' in html or p.name == "tools.html":
            continue
        if 'data-zh="工具商店"' in html:
            continue
        # 插到「插件」nav 之后
        anchor = '<a href="/plugins.html" class="nav"'
        idx = html.find(anchor)
        if idx < 0:
            continue
        end = html.find("</a>", idx)
        if end < 0:
            continue
        html = html[:end + 4] + "\n  " + link + html[end + 4:]
        p.write_text(html, encoding="utf-8")


def main():
    cats, cat_meta, tools = load()
    (DIST / "tools.html").write_text(page(cats, cat_meta, tools), encoding="utf-8")
    inject_nav()
    print(f"[+] tools.html 生成:{len(tools)} 工具 / {len(cats)} 类;导航已注入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
