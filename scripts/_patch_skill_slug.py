# -*- coding: utf-8 -*-
"""给 build_index.py 加 skill_slug()，并把技能页路径改为 slug 化。"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8")
p = "showcase/build_index.py"
s = io.open(p, encoding="utf-8").read()

anchor = "def mcp_slug(name: str) -> str:"
assert anchor in s, "mcp_slug anchor not found"

block = '''def skill_slug(name: str) -> str:
    """技能页文件名用 slug：替换路径分隔符与非法字符，防止生成非法路径。"""
    bad = set('/:*?"<>|' + chr(92))
    out = "".join("-" if (c in bad or ord(c) < 32) else c for c in (name or ""))
    out = " ".join(out.split())
    return out.strip(" .") or "skill"


'''

s = s.replace(anchor, block + anchor, 1)

n1 = s.count("--{s['name']}.html")
s = s.replace("--{s['name']}.html", "--{skill_slug(s['name'])}.html")
n2 = s.count("--{x['name']}.html")
s = s.replace("--{x['name']}.html", "--{skill_slug(x['name'])}.html")

io.open(p, "w", encoding="utf-8").write(s)
print("patched: s refs=%d, x refs=%d" % (n1, n2))
