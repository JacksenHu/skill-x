#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修正实测会失败的部署命令（2026-10-03 真实核验）。

修正依据（逐条实测）：
  1. ngcbot  仓库只剩 README.MD + 已归档 + 无 Release -> 部署入口彻底消失，标记不可用
  2. f8x     install.sh 已删除(404)，真实入口是仓库内的 f8x 脚本
  3. metarget PyPI 无此包(404)，官方安装方式是克隆后 pip install -r requirements.txt
  4. nemo_go compose 在 v3/ 子目录，根级 `docker compose up -d` 会失败
  5. dongtai compose 在 deploy/docker-compose/ 下，根级命令会失败
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "tools-store", "api-import-payload.json")

d = json.load(open(P, encoding="utf-8"))
by = {t["slug"]: t for t in d["tools"]}

FIX = {
    "f8x": {
        "command": "git clone https://github.com/ffffffff0x/f8x && cd f8x && bash f8x",
        "note": "原 install.sh 直链已失效(404)，当前入口为仓库内的 f8x 脚本。",
    },
    "metarget": {
        "method": "source",
        "command": "git clone https://github.com/Metarget/metarget && cd metarget && pip3 install -r requirements.txt && python3 metarget cnv install cve-2019-5736",
        "note": "PyPI 无 metarget 包，官方安装方式为克隆后本地安装依赖运行。",
    },
    "nemo_go": {
        "command": "git clone https://github.com/hanc00l/nemo_go && cd nemo_go/v3 && docker compose up -d",
        "note": "compose 文件在 v3/ 子目录，需在 v3 下执行。",
    },
    "dongtai": {
        "command": "git clone https://github.com/HXSecurity/DongTai && cd DongTai/deploy/docker-compose && docker compose up -d",
        "note": "compose 文件在 deploy/docker-compose/ 下，根目录直接 up 会失败。",
    },
}

for slug, fix in FIX.items():
    t = by.get(slug)
    if not t:
        print("skip missing", slug)
        continue
    dep = t.setdefault("deploy", {})
    if "method" in fix:
        dep["method"] = fix["method"]
    dep["command"] = fix["command"]
    t["note"] = fix["note"]
    t.setdefault("upstream", {})["deployVerified"] = "2026-10-03"
    print("FIX  %-16s %s" % (slug, fix["command"][:80]))

# ngcbot：上游已归档 + 根目录仅剩 README.MD + 无 Release -> 部署入口消失
nb = by.get("ngcbot")
if nb:
    nb["deploy"]["command"] = ""
    nb["note"] = ("上游仓库已归档且仓库内仅剩 README.MD，无 compose / 无 Release 产物，"
                  "一键部署入口已不可用；此处仅作情报索引保留。")
    nb.setdefault("upstream", {})["deployVerified"] = "2026-10-03"
    nb["upstream"]["deployBroken"] = True
    nb["upstream"]["archived"] = True
    print("BREAK ngcbot           部署入口消失(仅剩 README.MD,无 Release)")

json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwritten", P)
