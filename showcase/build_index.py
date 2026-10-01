#!/usr/bin/env python3
"""Skill X showcase builder wrapper."""
import json
import marshal
import re
import sys
import time
import types
from pathlib import Path

SHOWCASE = Path(__file__).resolve().parent
ROOT = SHOWCASE.parent
SCRIPTS = ROOT / "scripts"
DEFAULT_ICON = "assets/avatars/icon-default.svg"

sys.path.insert(0, str(SHOWCASE))
sys.path.insert(0, str(SCRIPTS))


def slug(name: str) -> str:
    return re.sub(r"[^\w.-]+", "--", name)


def gitmcp_url(website_url: str) -> str:
    """github.com/owner/repo -> gitmcp.io/owner/repo(即时 AI 上下文)。"""
    if not website_url:
        return ""
    m = re.match(r"https?://(?:www\.)?github\.com/([\w.-]+/[\w.-]+)", website_url)
    return f"https://gitmcp.io/{m.group(1)}" if m else ""


def ensure_upstream_cache():
    cache_path = SHOWCASE / ".upstream-cache.json"
    if cache_path.is_file():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            if time.time() - float(cache.get("_ts", 0)) < 86400 and cache.get("repos"):
                return
        except Exception:
            pass
    ext_path = ROOT / "external.json"
    namespaces = []
    if ext_path.is_file():
        try:
            ext = json.loads(ext_path.read_text(encoding="utf-8"))
            namespaces = [s.get("namespace") for s in ext.get("suites", []) if s.get("namespace")]
        except Exception:
            pass
    repos = {ns: {"stars": 0, "forks": 0, "pushed": ""} for ns in namespaces}
    cache_path.write_text(json.dumps({"_ts": time.time(), "repos": repos}, ensure_ascii=False, indent=1), encoding="utf-8")


def run_legacy_builder():
    pyc = SHOWCASE / "__pycache__" / "build_index.cpython-314.pyc"
    if not pyc.is_file():
        raise SystemExit("missing legacy builder bytecode: " + str(pyc))
    with pyc.open("rb") as f:
        f.read(16)
        code = marshal.load(f)
    mod = types.ModuleType("build_index")
    mod.__file__ = str(SHOWCASE / "build_index.py")
    mod.__package__ = ""
    mod.__name__ = "build_index"
    exec(code, mod.__dict__)
    mod.main()


def original_icon_map():
    reg_path = ROOT / "mcp-registry.json"
    if not reg_path.is_file():
        return {}
    try:
        doc = json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for s in doc.get("servers", []):
        icons = s.get("icons") or []
        src = icons[0].get("src") if icons else ""
        name = s.get("name", "")
        if name and src:
            out[name] = src
    return out


def update_site_data_icons():
    site_path = SHOWCASE / "dist" / "site-data.json"
    if not site_path.is_file():
        return
    doc = json.loads(site_path.read_text(encoding="utf-8"))
    for sk in doc.get("skills", []):
        sk["icon"] = DEFAULT_ICON
    for sk in doc.get("own", []):
        sk["icon"] = DEFAULT_ICON
    icons = original_icon_map()
    for m in doc.get("mcps", []):
        m["icon"] = icons.get(m.get("name", "")) or DEFAULT_ICON
    site_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def insert_detail_icons():
    dist = SHOWCASE / "dist"
    icons = original_icon_map()
    for path in list((dist / "skills").glob("*.html")) + list((dist / "mcp").glob("*.html")):
        icon = DEFAULT_ICON
        if path.parent.name == "mcp":
            for name, src in icons.items():
                if path.name == slug(name) + ".html":
                    icon = src
                    break
        html = path.read_text(encoding="utf-8", errors="replace")
        if '<img class="avatar" style="width:44px;height:44px"' in html:
            continue
        img = f'<img class="avatar" style="width:44px;height:44px" src="{icon}" alt="" width="44" height="44">'
        html = html.replace('<div class="card-head"><h1>', '<div class="card-head">' + img + '<h1>', 1)
        path.write_text(html, encoding="utf-8")


def inject_copy_config_buttons():
    """MCP 详情页注入「复制配置」按钮:复制 gitmcp.io MCP 配置(无需 clone/装依赖)。"""
    reg = ROOT / "mcp-registry.json"
    dist_mcp = SHOWCASE / "dist" / "mcp"
    if not reg.is_file() or not dist_mcp.is_dir():
        return
    doc = json.loads(reg.read_text(encoding="utf-8"))
    for s in doc.get("servers", []):
        name = s.get("name", "")
        url = gitmcp_url(s.get("websiteUrl") or "")
        if not url:
            continue
        short = name.split("/")[-1]
        cfg = json.dumps({"mcpServers": {short: {"type": "http", "url": url}}}, ensure_ascii=False)
        page = dist_mcp / (slug(name) + ".html")
        if not page.is_file():
            continue
        html = page.read_text(encoding="utf-8", errors="replace")
        if 'data-zh="复制配置"' in html:
            continue
        anchor = f'data-skill="mcp:{name}" data-zh="复制接入命令"'
        idx = html.find(anchor)
        if idx < 0:
            continue
        end = html.find("</button>", idx)
        if end < 0:
            continue
        btn = (f'<button class="chip copy-btn" data-copy=\'{cfg}\' '
               f'data-skill="mcp:{name}" data-zh="复制配置" data-en="Copy config">复制配置</button>')
        html = html[:end + 9] + " " + btn + html[end + 9:]
        page.write_text(html, encoding="utf-8")


def append_card_icon_css():
    css_path = SHOWCASE / "dist" / "assets" / "style.css"
    if not css_path.is_file():
        return
    css = css_path.read_text(encoding="utf-8", errors="replace")
    rule = """
.card:not(.pack-card) h3::before{content:"";display:inline-block;width:28px;height:28px;margin-right:8px;vertical-align:middle;background:url("/assets/avatars/icon-default.svg") center/contain no-repeat;border:1px solid var(--line2);border-radius:3px;flex:none}
"""
    if "card:not(.pack-card) h3::before" not in css:
        css += rule
    css_path.write_text(css, encoding="utf-8")


def main():
    ensure_upstream_cache()
    run_legacy_builder()
    update_site_data_icons()
    insert_detail_icons()
    inject_copy_config_buttons()
    append_card_icon_css()


if __name__ == "__main__":
    main()
