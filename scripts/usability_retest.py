#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""串行复测：GitMCP 在并发下会超时，必须串行 + 重试才能区分「真失效」与「被限流」。"""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from usability_mcp import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

mcp = json.load(open(os.path.join(ROOT, "mcp-registry.json"), encoding="utf-8"))
targets = {}
for s in mcp["servers"]:
    cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
    for r in s.get("remotes") or []:
        u = r.get("url")
        if u and u.startswith("http"):
            targets.setdefault(s.get("name"), u)
    hint = cur.get("installHint") or ""
    if "gitmcp.io" in hint:
        import re
        g = re.search(r"gitmcp\.io[:/]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", hint)
        if g:
            targets.setdefault(s.get("name"), "https://gitmcp.io/%s/%s/sse" % (g.group(1), g.group(2)))

print("串行复测 %d 个端点（每个最多 2 次重试）\n" % len(targets))
out = []
for name, url in sorted(targets.items()):
    r = None
    for attempt in range(3):
        r = probe(url, name)
        if r.get("verdict") != "BROKEN":
            break
        time.sleep(2)
    r["name"] = name
    r["attempts"] = attempt + 1
    out.append(r)
    flag = {"USABLE": "OK  ", "EMPTY": "EMPTY", "BROKEN": "FAIL"}.get(r.get("verdict"), "FAIL")
    extra = ""
    if r.get("verdict") == "USABLE":
        extra = " tools=%d len=%d" % (r.get("tool_count", 0), r.get("call_len", 0))
    print("%s %-50s%s | %s" % (flag, name[:50], extra, r.get("reason", ""))[:140])
    sys.stdout.flush()

json.dump(out, open(os.path.join(ROOT, "scripts", "upstream-audit", "usability-mcp-serial.json"), "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
c = Counter(r.get("verdict") for r in out)
print("\nUSABLE=%d EMPTY=%d BROKEN=%d" % (c.get("USABLE", 0), c.get("EMPTY", 0), c.get("BROKEN", 0)))
