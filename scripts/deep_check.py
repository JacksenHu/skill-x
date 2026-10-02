#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对 RISKY 工具做深挖：递归找 compose、找真实安装入口。"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("GH_TOKEN", "")
COMPOSE = {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
           "docker-compose.dev.yml", "docker-compose.prod.yml"}


def g(u):
    h = {"User-Agent": "x"}
    if TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(u, headers=h)
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 429):
                time.sleep(3)
                continue
            return e.code, b""
        except Exception as e:  # noqa: BLE001
            return 0, str(e).encode()
    return 0, b""


def ls(repo, path=""):
    st, b = g("https://api.github.com/repos/%s/contents/%s" % (repo, path))
    if st != 200:
        return st, []
    try:
        return st, [(x["name"], x["type"]) for x in json.loads(b.decode())]
    except Exception:  # noqa: BLE001
        return st, []


repos = {
    "nemo_go": "hanc00l/nemo_go",
    "scopesentry-scan": "Autumn-27/ScopeSentry-Scan",
    "vulhub": "vulhub/vulhub",
    "ehoney": "seccome/Ehoney",
    "darkangel": "Bywalks/DarkAngel",
    "dongtai": "HXSecurity/DongTai",
    "goad": "Orange-Cyberdefense/GOAD",
    "terraformgoat": "HXSecurity/TerraformGoat",
    "axiom": "pry0cc/axiom",
    "dependencycheck": "jeremylong/DependencyCheck",
}

for slug, repo in repos.items():
    st, items = ls(repo)
    names = [n for n, _ in items]
    dirs = [n for n, t in items if t == "dir"]
    print("=== %s (%s) status=%d" % (slug, repo, st))
    print("  files:", [n for n in names if n.lower() in COMPOSE] or "无根级 compose")
    print("  dirs :", dirs[:10])
    # 递归一层找 compose
    found = []
    for dname in dirs[:14]:
        s2, it2 = ls(repo, dname)
        if s2 != 200:
            continue
        hit = [n for n, t in it2 if n.lower() in COMPOSE]
        if hit:
            found.append(dname + "/" + hit[0])
    if found:
        print("  子目录 compose:", found[:6])
    # 关键入口文件
    keys = [n for n in names if n.lower() in (
        "vagrantfile", "main.go", "go.mod", "makefile", "requirements.txt",
        "setup.py", "package.json", "install.sh", "dockerfile", "readme.md")]
    print("  入口:", keys[:8])
    sys.stdout.flush()
    time.sleep(1)
