#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把抓好的插件/专家团套件写入 external.json（结构对齐现有 suite，skills 非空）。"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

suites = json.load(open(ROOT / "scripts" / "upstream-audit" / "anti-reverse-suites.json", encoding="utf-8"))
ep = ROOT / "external.json"
ed = json.loads(ep.read_text(encoding="utf-8"))
have = {s.get("namespace") for s in ed.get("suites", [])}

added = 0
for s in suites:
    ns = s["namespace"]
    if ns in have:
        continue
    rec = {k: v for k, v in s.items() if not k.startswith("_")}
    # 中文名与简介挂到 namespace 上（构建器若读取则生效，不影响结构合法性）
    rec["name-zh"] = s.get("_zh", "").split("：")[0][:40]
    rec["summary-zh"] = s.get("_zh", "")
    ed["suites"].append(rec)
    have.add(ns)
    added += 1

ep.write_text(json.dumps(ed, ensure_ascii=False, indent=1), encoding="utf-8")
print("[+] 套件新增 %d（总数 %d）" % (added, len(ed["suites"])))
