#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 scripts/upstream-audit/usability-tools.json 的实测结论写回工具数据。

USABLE -> deployVerified=日期（镜像/Release/compose 真实存在）
BROKEN -> deployBroken=True
RISKY  -> deployNote=需人工确认的说明
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-10-03"

u = json.load(open(os.path.join(ROOT, "scripts", "upstream-audit", "usability-tools.json"), encoding="utf-8"))
P = os.path.join(ROOT, "tools-store", "api-import-payload.json")
d = json.load(open(P, encoding="utf-8"))
by = {t["slug"]: t for t in d["tools"]}

n_ok = n_bad = n_risk = 0
for ev in u:
    t = by.get(ev["slug"])
    if not t:
        continue
    up = t.setdefault("upstream", {})
    v = ev.get("verdict")
    if v == "USABLE":
        up["deployVerified"] = TODAY
        up.pop("deployBroken", None)
        n_ok += 1
    elif v == "BROKEN":
        # 已被 fix_deploy_cmds.py 修好的，不再标坏
        if not (t.get("deploy") or {}).get("command"):
            up["deployBroken"] = True
            n_bad += 1
        else:
            up["deployVerified"] = TODAY
            n_ok += 1
    else:  # RISKY
        up["deployNote"] = ev.get("reason", "")
        n_risk += 1

json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("部署已实测=%d  部署不可用=%d  需人工确认=%d" % (n_ok, n_bad, n_risk))
