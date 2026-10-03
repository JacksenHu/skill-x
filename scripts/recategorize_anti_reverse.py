# -*- coding: utf-8 -*-
"""把防逆向/防解密爬取批次整体迁移到新分类「网络与工程防御」。

批次来源: scripts/upstream-audit/anti-reverse-picked.json
  - 13 个 MCP      -> mcp-registry.json
  - 29 个工具      -> tools-store/api-import-payload.json
  - 11 个套件      -> external.json + showcase/i18n-ext.json(188 个技能条目)

同时注册新分类:
  - tools-store/categories.json: reverse-engineering 分类替换为 network-engineering-defense
  - showcase/build_index.py: CATEGORIES / CATEGORIES_EN / CAT_LABELS / CSS 色
  - scripts/render_tools_store.py: CAT_COLORS 映射
  - api/server.py: CAT_KW 推荐关键词 + VERSION 升
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
NEW = "network-engineering-defense"
NEW_ZH = "网络与工程防御"
NEW_EN = "Network & Engineering Defense"
DESC = "网络与工程防御技能，覆盖{name}相关的防护机制、逆向对抗与工程加固。"

sys.path.insert(0, str(ROOT / "scripts"))
from gen_i18n_ext import translate_name  # noqa: E402

picked = json.loads((ROOT / "scripts" / "upstream-audit" / "anti-reverse-picked.json").read_text(encoding="utf-8"))
by_kind = {}
for r in picked:
    by_kind.setdefault(r["kind"], []).append(r["full_name"])


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------- 1) MCP ----------
p = ROOT / "mcp-registry.json"
doc = json.loads(p.read_text(encoding="utf-8"))
want = {"io.github." + f for f in by_kind.get("mcp", [])}
hit = 0
for srv in doc.get("servers", []):
    if srv.get("name") in want:
        cur = (srv.get("_meta") or {}).setdefault("top.skillx/curated", {})
        cur["category"] = NEW
        hit += 1
p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
print("1) MCP recategorized: %d / %d" % (hit, len(want)))

# ---------- 2) TOOLS ----------
p = ROOT / "tools-store" / "api-import-payload.json"
doc = json.loads(p.read_text(encoding="utf-8"))
want_slugs = {slugify(f) for f in by_kind.get("tool", [])}
hit = 0
for t in doc.get("tools", []):
    if t.get("slug") in want_slugs:
        t["category_id"] = NEW
        labels = t.get("labels") or []
        if labels and labels[0] in ("reverse-engineering", "recon"):
            labels[0] = NEW
        hit += 1
p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
print("2) tools recategorized: %d / %d" % (hit, len(want_slugs)))

# ---------- 3) SUITES ----------
p = ROOT / "external.json"
doc = json.loads(p.read_text(encoding="utf-8"))
want_ns = set(by_kind.get("plugin", [])) | set(by_kind.get("pack", []))
suite_skills = {}
hit = 0
for s in doc.get("suites", []):
    ns = s.get("namespace")
    if ns in want_ns:
        s["category"] = NEW
        suite_skills[ns] = [x.get("name") for x in (s.get("skills") or [])]
        hit += 1
p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
total_sk = sum(len(v) for v in suite_skills.values())
print("3) suites tagged: %d / %d (skills %d)" % (hit, len(want_ns), total_sk))

# ---------- 4) I18N ----------
p = ROOT / "showcase" / "i18n-ext.json"
doc = json.loads(p.read_text(encoding="utf-8"))
added = 0
for ns, names in suite_skills.items():
    bucket = doc.get(ns)
    if bucket is None:
        bucket = {}
        doc[ns] = bucket
    for name in names:
        if not name:
            continue
        entry = bucket.get(name)
        if entry is None:
            entry = {}
            added += 1
        entry["category"] = NEW
        if not entry.get("name-zh"):
            entry["name-zh"] = translate_name(name)
        if not entry.get("description-zh"):
            entry["description-zh"] = DESC.format(name=entry["name-zh"])
        bucket[name] = entry
p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print("4) i18n entries: added %d" % added)

# ---------- 5) TOOL CATEGORIES ----------
p = ROOT / "tools-store" / "categories.json"
doc = json.loads(p.read_text(encoding="utf-8"))
done = False
for c in doc.get("categories", []):
    if c.get("id") == "reverse-engineering":
        c["id"] = NEW
        c["name"] = NEW_ZH
        c["name_en"] = NEW_EN
        done = True
if not done and NEW not in [c.get("id") for c in doc.get("categories", [])]:
    doc["categories"].insert(0, {"id": NEW, "name": NEW_ZH, "name_en": NEW_EN, "order": 0})
p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("5) tool categories:", [c["id"] for c in doc["categories"]])

# ---------- 6) build_index.py ----------
p = ROOT / "showcase" / "build_index.py"
b = p.read_text(encoding="utf-8")
edits = [
    ('CATEGORIES = {\n    "reverse-engineering": "逆向工程",\n',
     'CATEGORIES = {\n    "reverse-engineering": "逆向工程",\n    "network-engineering-defense": "网络与工程防御",\n'),
    ('CATEGORIES_EN = {\n    "reverse-engineering": "Reverse Engineering",\n',
     'CATEGORIES_EN = {\n    "reverse-engineering": "Reverse Engineering",\n    "network-engineering-defense": "Network & Engineering Defense",\n'),
    ('CAT_LABELS = {\n    "reverse-engineering": "逆向工程",\n',
     'CAT_LABELS = {\n    "reverse-engineering": "逆向工程",\n    "network-engineering-defense": "网络与工程防御",\n'),
    ('.cat-reverse-engineering{--cat:var(--c-reverse-engineering)}\n',
     '.cat-reverse-engineering{--cat:var(--c-reverse-engineering)}\n.cat-network-engineering-defense{--cat:var(--c-network-engineering-defense)}\n'),
    ('--c-reverse-engineering:#FF6B2C;',
     '--c-reverse-engineering:#FF6B2C; --c-network-engineering-defense:#7DD3FC;'),
]
for old, new in edits:
    assert old in b, "build_index anchor missing: %r" % old[:60]
    b = b.replace(old, new, 1)
p.write_text(b, encoding="utf-8")
print("6) build_index.py patched")

# ---------- 7) render_tools_store.py ----------
p = ROOT / "scripts" / "render_tools_store.py"
u = p.read_text(encoding="utf-8")
old = '    "reverse-engineering": "reverse-engineering",\n'
assert old in u, "cat_colors anchor"
u = u.replace(old, '    "network-engineering-defense": "network-engineering-defense",\n', 1)
p.write_text(u, encoding="utf-8")
print("7) render_tools_store.py patched")

# ---------- 8) server.py ----------
p = ROOT / "api" / "server.py"
v = p.read_text(encoding="utf-8")
old = '    "engineering-hygiene": ["测试", "回归", "验证", "质量", "审查", "纪律", "假红", "污染"],\n'
assert old in v, "CAT_KW anchor"
v = v.replace(old, old + '    "network-engineering-defense": ["加壳", "脱壳", "混淆", "加解密", "防调试", "反调试", "加固", "防逆向", "反破解", "壳"],\n', 1)
v = v.replace('VERSION = "2026-10-03.1"', 'VERSION = "2026-10-03.2"', 1)
p.write_text(v, encoding="utf-8")
print("8) server.py patched")

print("done")
