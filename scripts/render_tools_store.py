#!/usr/bin/env python3
"""生成「安全工具商店」列表页 dist/tools.html 与每个工具的详情页 dist/tools/<slug>.html。

数据源:tools-store/api-import-payload.json(已含 slug/summary/description/detail_url/docs_url)
        + tools-store/categories.json。
复用站内 .card/.chips/.cmd/.copy-btn/.hint-dim 样式与 app.js 的 sxFilter/sxCopy。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOWCASE = ROOT / "showcase"
DIST = SHOWCASE / "dist"
TS = ROOT / "tools-store"
DETAIL_DIR = DIST / "tools"

CAT_COLORS = {
    "recon": "data", "vuln": "pentest", "lab": "dev-workflow",
    "tunnel": "malware", "defense": "forensics", "intel": "reverse-engineering",
}


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def load():
    payload = json.loads((TS / "api-import-payload.json").read_text(encoding="utf-8"))
    cats = json.loads((TS / "categories.json").read_text(encoding="utf-8"))["categories"]
    cat_meta = {c["id"]: c for c in cats}
    tools = payload["tools"]
    return cats, cat_meta, tools


def nav(active):
    items = [
        ("/", "首页", "Home", "index"),
        ("/skills.html", "技能", "Skills", "skills"),
        ("/packages.html", "专家团", "Expert Packs", "packages"),
        ("/mcp.html", "MCP", "MCP", "mcp"),
        ("/plugins.html", "插件", "Plugins", "plugins"),
        ("/tools.html", "工具商店", "Tool Store", "tools"),
        ("/api.html", "API", "API", "api"),
        ("/about.html", "关于", "About", "about"),
    ]
    links = ['<a class="brand" href="/">Skill X</a>']
    for href, zh, en, key in items:
        cls = 'class="nav active"' if key == active else 'class="nav"'
        links.append(f'<a href="{href}" {cls} data-zh="{zh}" data-en="{en}">{zh}</a>')
    links.append('<button class="lang-btn">EN</button>')
    return f'<div class="topnav">{"\n  ".join(links)}</div>'


def footer():
    return ('<footer><a href="/">Skill X</a> · 安全研究 / 逆向工程技能与工具库 · '
            '<a href="/about.html">关于</a></footer>')


def head(title, asset_ver=""):
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Skill X</title>
<link rel="stylesheet" href="/assets/style.css?v={asset_ver}">
</head><body>
<div class="scroll-progress" aria-hidden="true"></div>'''


def meta_html(t, cat_meta):
    cat = t.get("category_id", "")
    cm = cat_meta.get(cat, {})
    deploy = (t.get("deploy") or {}).get("method", "")
    form = t.get("form", "")
    ports = ",".join(str(p) for p in (t.get("ports") or []))
    parts = [
        f'<span class="tag cat">{esc(cm.get("name", cat))}</span>',
        f'<span class="tag kind-ext">{esc(deploy)}</span>',
        f'<span class="tag kind-mcp">{esc(form)}</span>',
    ]
    if ports:
        parts.append(f'<span class="tag">端口 {esc(ports)}</span>')
    return f'<div class="meta">{"".join(parts)}</div>'


def deploy_block(t):
    command = (t.get("deploy") or {}).get("command", "")
    if not command:
        return ""
    copy_btn = (f'<button class="chip on copy-btn" data-copy="{esc(command)}" '
                f'data-skill="tool:{esc(t.get("name", ""))}" data-zh="复制部署命令" '
                f'data-en="Copy deploy command">复制部署命令</button>')
    return f'<div class="cmd">{esc(command)}</div><div class="actions">{copy_btn}</div>'


def card(t, cat_meta):
    cat = t.get("category_id", "")
    name = t.get("name", "")
    name_zh = t.get("name_zh", "") or name
    detail = t.get("detail_url", f"/tools/{t.get('slug', '')}.html")
    docs = t.get("docs_url", "")
    gm = (t.get("gitmcp") or {}).get("url", "")
    command = (t.get("deploy") or {}).get("command", "")
    summary = t.get("summary", "") or t.get("description", "") or ""
    deploy = (t.get("deploy") or {}).get("method", "")
    form = t.get("form", "")
    search = f"{name} {name_zh} {cat} {deploy} {form} {summary}".lower()
    color = CAT_COLORS.get(cat, "dev-workflow")
    actions = []
    if docs:
        actions.append(f'<a class="chip" href="{esc(docs)}" target="_blank" rel="noopener" data-zh="查看源码" data-en="Source">查看源码 ↗</a>')
    if command:
        actions.append(f'<button class="chip on copy-btn" data-copy="{esc(command)}" data-skill="tool:{esc(name)}" data-zh="复制部署命令" data-en="Copy deploy command">复制部署命令</button>')
    if gm:
        actions.append(f'<a class="chip" href="{esc(gm)}" target="_blank" rel="noopener">gitmcp ↗</a>')
    actions_html = f'<div class="actions">{"".join(actions)}</div>' if actions else ""
    summary_html = f'<p class="hint-dim">{esc(summary)}</p>' if summary else ""
    return f'''<div class="card cat-{color}" data-search="{esc(search)}" data-category="{esc(cat)}">
  <h3><a href="{esc(detail)}">{esc(name_zh)}</a></h3>
  <div class="en-name">{esc(name)}</div>
  {meta_html(t, cat_meta)}
  {summary_html}
  {actions_html}
</div>'''


def detail_page(t, cat_meta, cats, asset_ver=""):
    name = t.get("name", "")
    name_zh = t.get("name_zh", "") or name
    docs = t.get("docs_url", "")
    gm = (t.get("gitmcp") or {}).get("url", "")
    repo = t.get("repo", "")
    default_port = t.get("default_port")
    form = t.get("form", "")
    credentials = t.get("credentials") or []
    note = t.get("note", "")
    description = t.get("description", "") or t.get("summary", "") or ""

    chips = ['<a class="chip on" href="/tools.html" data-zh="返回工具商店" data-en="Back to Tool Store">← 返回工具商店</a>']
    if docs:
        chips.append(f'<a class="chip" href="{esc(docs)}" target="_blank" rel="noopener">查看源码 ↗</a>')
    if gm:
        chips.append(f'<a class="chip" href="{esc(gm)}" target="_blank" rel="noopener">gitmcp 上下文 ↗</a>')

    rows = []
    if default_port:
        rows.append(f'<tr><th>默认端口</th><td><code class="inl">{esc(str(default_port))}</code></td></tr>')
    if form:
        rows.append(f'<tr><th>形态</th><td>{esc(form)}</td></tr>')
    if repo:
        rows.append(f'<tr><th>仓库</th><td><code class="inl">{esc(repo)}</code></td></tr>')
    if credentials:
        rows.append(f'<tr><th>第三方凭证</th><td>{esc(", ".join(str(c) for c in credentials))}</td></tr>')
    if note:
        rows.append(f'<tr><th>备注</th><td>{esc(note)}</td></tr>')
    table = f'<table class="api">{"".join(rows)}</table>' if rows else ""

    cmd = deploy_block(t)
    return f'''{head(name_zh + " · 安全工具商店", asset_ver)}
{nav("tools")}
<div class="wrap">
<h2>{esc(name_zh)} <span class="en-name">{esc(name)}</span></h2>
{meta_html(t, cat_meta)}
<p class="hint-dim">{esc(description)}</p>
<div class="chips">{"".join(chips)}</div>
<h3 data-zh="一键部署" data-en="Deploy">一键部署</h3>
{cmd or '<p class="hint-dim">该工具无标准命令行部署入口。</p>'}
{table}
</div>
{footer()}
<script src="/assets/app.js?v={asset_ver}"></script>
</body></html>'''


def list_page(cats, cat_meta, tools, asset_ver=""):
    chips = ['<span class="chip on" data-cat="" data-zh="全部" data-en="All">全部</span>']
    for c in cats:
        chips.append(f'<span class="chip" data-cat="{c["id"]}" data-zh="{esc(c["name"])}" data-en="{esc(c["name_en"])}">{esc(c["name"])}</span>')
    cards = "".join(card(t, cat_meta) for t in tools)
    return f'''{head("安全工具商店", asset_ver)}
{nav("tools")}
<div class="wrap">
<h2 data-zh="安全工具商店" data-en="Security Tool Store">安全工具商店 <span class="n">{len(tools)} 个 · {len(cats)} 类</span></h2>
<p class="hint-dim" data-zh="面向已获授权的安全测试工具软件:一键部署 Docker 服务、二进制工具与靶场/蜜罐/情报平台。部署命令只做指路,本体走 Docker Hub / GitHub,不经过本站。" data-en="Security tools for authorized testing: one-command deploy for Docker services, binaries, labs, honeypots and intel platforms. Deploy commands signpost to Docker Hub / GitHub; nothing is proxied through this site.">面向已获授权的安全测试工具软件:一键部署 Docker 服务、二进制工具与靶场/蜜罐/情报平台。部署命令只做指路,本体走 Docker Hub / GitHub,不经过本站。</p>
<div class="search"><input id="q" type="search" data-zh="按名称或关键词筛选工具…" data-en="Filter tools by name or keyword…" data-attr="placeholder" placeholder="按名称或关键词筛选工具…"></div>
<div class="chips">{''.join(chips)}</div>
<div class="grid">{cards}</div>
</div>
{footer()}
<script src="/assets/app.js?v={asset_ver}"></script>
</body></html>'''


def inject_nav():
    link = '<a href="/tools.html" class="nav" data-zh="工具商店" data-en="Tool Store">工具商店</a>'
    for p in DIST.glob("*.html"):
        html = p.read_text(encoding="utf-8", errors="replace")
        if '/tools.html' in html or p.name == "tools.html":
            continue
        if 'data-zh="工具商店"' in html:
            continue
        anchor = '<a href="/plugins.html" class="nav"'
        idx = html.find(anchor)
        if idx < 0:
            continue
        end = html.find("</a>", idx)
        if end < 0:
            continue
        html = html[:end + 4] + "\n  " + link + html[end + 4:]
        p.write_text(html, encoding="utf-8")


def main(asset_ver=""):
    cats, cat_meta, tools = load()
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for t in tools:
        slug = t.get("slug")
        if not slug:
            continue
        (DETAIL_DIR / f"{slug}.html").write_text(detail_page(t, cat_meta, cats, asset_ver), encoding="utf-8")
        n += 1
    (DIST / "tools.html").write_text(list_page(cats, cat_meta, tools, asset_ver), encoding="utf-8")
    inject_nav()
    print(f"[+] tools.html 生成:{len(tools)} 工具 / {len(cats)} 类;详情页 {n} 个;导航已注入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
