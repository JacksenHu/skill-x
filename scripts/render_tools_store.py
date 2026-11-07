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

sys.path.insert(0, str(SHOWCASE))
from svg_map import mmap_html  # noqa: E402
from svg_map import mindmap_tree, render_svg  # noqa: E402

CAT_COLORS = {
    "recon": "data", "vuln": "pentest", "lab": "dev-workflow",
    "tunnel": "malware", "defense": "forensics", "intel": "reverse-engineering",
    "network-engineering-defense": "network-engineering-defense",
    "memory-process": "malware",
}


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def scrub_note(s):
    """展示层用语规范化:条目描述中不出现"上游"字样。"""
    out = s or ""
    for a, b in (("上游仓库已归档（archived）", "条目已归档"),
                 ("上游已移除部署产物", "部署产物已不可用"),
                 ("上游仓库", "条目"), ("上游", "条目")):
        out = out.replace(a, b)
    return out


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


def upstream_badge(up):
    """条目徽标：授权收录标注 + 部署入口实测结果（由 scripts/upstream_audit.py 驱动）。"""
    parts = ['<span class="tag ok" title="该条目已获授权收录与分发">已授权收录</span>']
    if up:
        if up.get("deployBroken"):
            parts.append('<span class="tag danger" title="实测：部署入口已消失，无法按命令安装">部署不可用</span>')
        elif up.get("deployVerified"):
            parts.append('<span class="tag ok" title="已实测部署入口（镜像/Release/compose 文件）真实存在">部署已实测</span>')
        if up.get("lastCheck"):
            parts.append('<span class="tag dim">核验 ' + esc(str(up["lastCheck"])) + '</span>')
    return '<div class="meta">' + ''.join(parts) + '</div>'


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


def tool_mindmap(t, cat_meta):
    """五分支结构导图:概览 / 部署 / 能力 / 依赖与授权 / 适用场景。

    收录新工具后必须保证此函数能产出非空分支,否则详情页导图会退化。
    """
    cat = t.get("category_id", "")
    cm = cat_meta.get(cat, {})
    deploy = t.get("deploy") or {}
    method = deploy.get("method") or "—"
    form = t.get("form") or "—"
    ports = [str(x) for x in (t.get("ports") or [])]
    up = t.get("upstream") or {}
    labels = [str(x) for x in (t.get("labels") or []) if x]

    cmd = (deploy.get("command") or "").strip()
    if len(cmd) > 52:
        cmd = cmd[:51] + "…"

    branches = [
        ("概览", [cm.get("name", cat) or "未分类", f"形态 {form}", f"部署 {method}"]),
        ("部署", [f"方式 {method}", cmd or "—", (f"端口 {','.join(ports)}" if ports else "无固定端口")]),
        ("能力", (labels[:5] or ["通用安全工具"])),
        ("依赖与授权", [f"许可证 {up.get('license') or '—'}",
                         f"热度 {up.get('stars') or '—'} ★",
                         "已授权收录与分发"]),
        ("适用场景", [f"{form} 形态",
                       ("本地部署" if method in ("source", "binary", "cli", "script", "iac") else "服务化部署"),
                       "授权安全测试"]),
    ]
    return mmap_html(t.get("name_zh") or t.get("name", ""), branches, "结构导图")


def _tool_branches(t, cat_meta):
    """构造五分支(供内联导图与独立 SVG 导出共用)。"""
    cat = t.get("category_id", "")
    cm = cat_meta.get(cat, {})
    deploy = t.get("deploy") or {}
    method = deploy.get("method") or "—"
    form = t.get("form") or "—"
    ports = [str(x) for x in (t.get("ports") or [])]
    up = t.get("upstream") or {}
    labels = [str(x) for x in (t.get("labels") or []) if x]
    cmd = (deploy.get("command") or "").strip()
    if len(cmd) > 52:
        cmd = cmd[:51] + "…"
    return [
        ("概览", [cm.get("name", cat) or "未分类", f"形态 {form}", f"部署 {method}"]),
        ("部署", [f"方式 {method}", cmd or "—", (f"端口 {','.join(ports)}" if ports else "无固定端口")]),
        ("能力", (labels[:5] or ["通用安全工具"])),
        ("依赖与授权", [f"许可证 {up.get('license') or '—'}",
                         f"热度 {up.get('stars') or '—'} ★",
                         "已授权收录与分发"]),
        ("适用场景", [f"{form} 形态",
                       ("本地部署" if method in ("source", "binary", "cli", "script", "iac") else "服务化部署"),
                       "授权安全测试"]),
    ]


def tool_mindmap_svg(t, cat_meta):
    """导出独立 SVG(供 /mindmaps/tool-<slug>.svg 静态接口)。"""
    name = t.get("name_zh") or t.get("name", "")
    return render_svg(mindmap_tree(name, _tool_branches(t, cat_meta)), "结构导图")


def tool_intro(t, cat_meta):
    cat = t.get("category_id", "")
    cm = cat_meta.get(cat, {})
    cat_name = cm.get("name", cat) or "未分类"
    deploy = (t.get("deploy") or {}).get("method", "") or "—"
    form = t.get("form", "") or "—"
    out = f"「{t.get('name_zh') or t.get('name', '')}」（{t.get('name', '')}）是一款{cat_name}方向的{form}形态安全工具，部署方式为{deploy}。"
    ports = t.get("ports") or []
    if ports:
        out += f" 默认端口 {', '.join(str(x) for x in ports)}。"
    desc = t.get("description", "") or t.get("summary", "")
    if desc:
        out += f" {desc.strip('。')}。"
    return out


def deploy_unavailable(up, note):
    """部署入口不可用时的显式说明。"""
    if (up or {}).get("deployBroken"):
        return ('<p class="hint-warn">⚠️ 部署入口已不可用：'
                + esc(scrub_note(note) or '部署产物已不可用')
                + '</p><p class="hint-dim">本条目仅作情报索引保留，不提供一键部署。</p>')
    return '<p class="hint-dim">该工具无标准命令行部署入口，本条目仅作收录索引。</p>'


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
    up = t.get("upstream") or {}
    detail = t.get("detail_url", f"/tools/{t.get('slug', '')}.html")
    command = (t.get("deploy") or {}).get("command", "")
    summary = t.get("summary", "") or t.get("description", "") or ""
    deploy = (t.get("deploy") or {}).get("method", "")
    form = t.get("form", "")
    search = f"{name} {name_zh} {cat} {deploy} {form} {summary}".lower()
    color = CAT_COLORS.get(cat, "dev-workflow")
    actions = []
    if command:
        actions.append(f'<button class="chip on copy-btn" data-copy="{esc(command)}" data-skill="tool:{esc(name)}" data-zh="复制部署命令" data-en="Copy deploy command">复制部署命令</button>')
    actions_html = f'<div class="actions">{"".join(actions)}</div>' if actions else ""
    summary_html = f'<p class="hint-dim">{esc(summary)}</p>' if summary else ""
    up_html = upstream_badge(up)
    return f'''<div class="card cat-{color}" data-search="{esc(search)}" data-category="{esc(cat)}">
  <h3><a href="{esc(detail)}">{esc(name_zh)}</a></h3>
  <div class="en-name">{esc(name)}</div>
  {up_html}
  {meta_html(t, cat_meta)}
  {summary_html}
  {actions_html}
</div>'''


def detail_page(t, cat_meta, cats, asset_ver=""):
    name = t.get("name", "")
    name_zh = t.get("name_zh", "") or name
    default_port = t.get("default_port")
    form = t.get("form", "")
    credentials = t.get("credentials") or []
    note = t.get("note", "")
    description = t.get("description", "") or t.get("summary", "") or ""
    up = t.get("upstream") or {}

    chips = ['<a class="chip on" href="/tools.html" data-zh="返回工具商店" data-en="Back to Tool Store">← 返回工具商店</a>']

    rows = []
    rows.append('<tr><th>授权</th><td>已授权收录与分发</td></tr>')
    if default_port:
        rows.append(f'<tr><th>默认端口</th><td><code class="inl">{esc(str(default_port))}</code></td></tr>')
    if form:
        rows.append(f'<tr><th>形态</th><td>{esc(form)}</td></tr>')
    if up:
        if up.get("deployVerified"):
            rows.append('<tr><th>部署核验</th><td>已实测</td></tr>')
        elif up.get("deployBroken"):
            rows.append('<tr><th>部署核验</th><td>不可用</td></tr>')
        if up.get("lastCheck"):
            rows.append(f'<tr><th>核验时间</th><td>{esc(str(up.get("lastCheck")))}</td></tr>')
        if up.get("note"):
            rows.append(f'<tr><th>提示</th><td>{esc(scrub_note(up.get("note")))}</td></tr>')
    if credentials:
        rows.append(f'<tr><th>第三方凭证</th><td>{esc(", ".join(str(c) for c in credentials))}</td></tr>')
    if note:
        rows.append(f'<tr><th>备注</th><td>{esc(scrub_note(note))}</td></tr>')
    table = f'<table class="api">{"".join(rows)}</table>' if rows else ""

    cmd = deploy_block(t)
    return f'''{head(name_zh + " · 安全工具商店", asset_ver)}
{nav("tools")}
<div class="wrap">
 <h2>{esc(name_zh)} <span class="en-name">{esc(name)}</span></h2>
 {meta_html(t, cat_meta)}
 {upstream_badge(up)}
 <p class="desc">{esc(tool_intro(t, cat_meta))}</p>
<div class="chips">{"".join(chips)}</div>
<h3 data-zh="一键部署" data-en="Deploy">一键部署</h3>
{cmd or deploy_unavailable(up, note)}
{table}
{tool_mindmap(t, cat_meta)}
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
<p class="hint-dim" data-zh="面向已获授权的安全测试工具软件:一键部署 Docker 服务、二进制工具与靶场/蜜罐/情报平台。条目均已获授权收录;部署命令在本机执行,本体不经过本站。" data-en="Security tools for authorized testing: one-command deploy for Docker services, binaries, labs, honeypots and intel platforms. All entries are authorized for listing; deploy commands run locally, nothing is proxied through this site.">面向已获授权的安全测试工具软件:一键部署 Docker 服务、二进制工具与靶场/蜜罐/情报平台。条目均已获授权收录;部署命令在本机执行,本体不经过本站。</p>
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
        (DIST / "mindmaps").mkdir(parents=True, exist_ok=True)
        (DIST / "mindmaps" / f"tool-{slug}.svg").write_text(tool_mindmap_svg(t, cat_meta), encoding="utf-8")
        n += 1
    (DIST / "tools.html").write_text(list_page(cats, cat_meta, tools, asset_ver), encoding="utf-8")
    inject_nav()
    print(f"[+] tools.html 生成:{len(tools)} 工具 / {len(cats)} 类;详情页 {n} 个;导航已注入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
