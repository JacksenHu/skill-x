#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按站点已有分类,在 GitHub 搜索成熟项目,去重后产出候选池。

成熟度门槛: stars >= MIN_STARS,非 archived,pushed_at 晚于 PUSHED_SINCE。
去重: 排除已收录(技能目录/MCP 注册表/工具商店/套件/专家团)的仓库。
输出: scripts/upstream-audit/category-candidates.json
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, OrderedDict

# 沙箱把 HTTP 代理指向黑洞端口,这里显式清掉以便直连
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy",
           "all_proxy", "GIT_HTTP_PROXY", "GIT_HTTPS_PROXY"):
    os.environ.pop(_k, None)

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("GH_TOKEN", "")
UA = "skillx-crawler/1.0"
MIN_STARS = 250
PUSHED_SINCE = "2024-06-01"

# (category_id, 中文名, [查询词])
CATEGORY_QUERIES = [
    ("reverse-engineering", "逆向工程", [
        "reverse engineering tool",
        "disassembler",
        "decompiler",
        "binary analysis framework",
        "debugger",
    ]),
    ("network-engineering-defense", "网络与工程防御", [
        "obfuscator",
        "anti-debug",
        "code protection",
        "binary hardening",
        "anti cheat",
    ]),
    ("pentest", "渗透测试", [
        "penetration testing framework",
        "exploit framework",
        "web security scanner",
        "bug bounty toolkit",
    ]),
    ("malware", "样本分析", [
        "malware analysis",
        "sandbox analysis",
        "yara rules",
        "c2 framework",
    ]),
    ("forensics", "内存取证", [
        "memory forensics",
        "digital forensics",
        "incident response",
    ]),
    ("engineering-hygiene", "工程纪律", [
        "static analysis",
        "code audit",
        "sbom",
        "secrets detection",
    ]),
    ("dev-workflow", "开发流程", [
        "developer productivity cli",
        "terminal tools",
        "git workflow",
    ]),
    ("data", "数据", [
        "data pipeline",
        "etl framework",
        "data engineering",
    ]),
    ("web-frontend", "Web 前端", [
        "frontend framework",
        "ui component library",
        "web animation",
    ]),
    ("ai-media", "AI 媒体", [
        "text to speech",
        "image generation",
        "video generation ai",
        "audio processing ai",
    ]),
    ("recon", "侦察测绘", [
        "subdomain enumeration",
        "asset discovery",
        "osint framework",
    ]),
    ("vuln", "漏洞扫描", [
        "vulnerability scanner",
        "sast scanner",
        "dependency vulnerability",
    ]),
    ("lab", "靶场实验", [
        "vulnerable lab",
        "ctf platform",
        "security training range",
    ]),
    ("tunnel", "内网与隧道", [
        "tunneling tool",
        "reverse proxy",
        "network proxy",
    ]),
    ("defense", "蜜罐与防守", [
        "honeypot",
        "intrusion detection",
        "waf",
    ]),
    ("intel", "威胁情报", [
        "threat intelligence",
        "ioc feeds",
        "cve database",
    ]),
]


def gh(url):
    h = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, headers=h)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 502, 503):
                time.sleep(6 * (attempt + 1))
                continue
            return e.code, {}
        except Exception:  # noqa: BLE001
            time.sleep(4)
    return 0, {}


def search(q):
    url = ("https://api.github.com/search/repositories?q=%s&sort=stars&order=desc&per_page=20"
           % urllib.parse.quote(q))
    st, j = gh(url)
    if st != 200:
        print("  ! %-52s HTTP %s" % (q, st))
        return []
    items = j.get("items", [])
    print("  %-52s %d 条" % (q, len(items)))
    return items


def repo_fullname(url):
    m = re.match(r"https?://github\.com/([^/]+/[^/#?]+)", (url or "").strip())
    if not m:
        return None
    return m.group(1)[:-4] if m.group(1).endswith(".git") else m.group(1)


def collect_existing():
    """已有收录的 GitHub 仓库全名集合 + 技能/套件命名空间。"""
    known = set()

    def add(u):
        fn = repo_fullname(u)
        if fn:
            known.add(fn.lower())

    try:
        for s in json.load(open(os.path.join(ROOT, "mcp-registry.json"), encoding="utf-8"))["servers"]:
            add(s.get("websiteUrl"))
            cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
            add((cur.get("install") or {}).get("url"))
    except Exception:  # noqa: BLE001
        pass

    try:
        for t in json.load(open(os.path.join(ROOT, "tools-store", "catalog.json"), encoding="utf-8"))["tools"]:
            add("https://github.com/" + (t.get("repo") or ""))
    except Exception:  # noqa: BLE001
        pass

    try:
        for s in json.load(open(os.path.join(ROOT, "external.json"), encoding="utf-8"))["suites"]:
            add(s.get("upstream"))
    except Exception:  # noqa: BLE001
        pass

    try:
        for p in json.load(open(os.path.join(ROOT, "packs.json"), encoding="utf-8"))["packs"]:
            add(p.get("source"))
    except Exception:  # noqa: BLE001
        pass

    return known


def classify(it):
    blob = " ".join([
        it.get("full_name", ""), it.get("description") or "",
        " ".join(it.get("topics") or []),
    ]).lower()
    if "modelcontextprotocol" in blob or re.search(r"\bmcp\b", blob):
        return "mcp"
    if re.search(r"claude[- ]?(code|skills?)|agent[- ]?skills?|\bskills?\b", blob):
        return "skills"
    return "tool"


def main():
    print("已有收录仓库: %d\n" % len(collect_existing()))
    known = collect_existing()
    seen = OrderedDict()
    print("搜索 %d 个分类 ...\n" % len(CATEGORY_QUERIES))

    for cid, cname, queries in CATEGORY_QUERIES:
        print("[%s] %s" % (cid, cname))
        for q in queries:
            full_q = "%s stars:>=%d pushed:>=%s" % (q, MIN_STARS, PUSHED_SINCE)
            for it in search(full_q):
                fn = it.get("full_name")
                if not fn:
                    continue
                if fn.lower() in known:
                    continue
                if it.get("archived"):
                    continue
                rec = seen.get(fn)
                if rec is None:
                    seen[fn] = {
                        "category": cid,
                        "categoryName": cname,
                        "queries": [q],
                        "kind": classify(it),
                        "full_name": fn,
                        "description": (it.get("description") or "")[:220],
                        "stars": it.get("stargazers_count"),
                        "forks": it.get("forks_count"),
                        "language": it.get("language"),
                        "license": ((it.get("license") or {}).get("spdx_id") or ""),
                        "pushed_at": (it.get("pushed_at") or "")[:10],
                        "topics": (it.get("topics") or [])[:12],
                        "html_url": it.get("html_url"),
                    }
                else:
                    rec["queries"].append(q)
            time.sleep(2.2)  # search 限流 30/min

    rows = sorted(seen.values(), key=lambda r: (-(r.get("stars") or 0)))
    od = os.path.join(ROOT, "scripts", "upstream-audit")
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, "category-candidates.json")
    json.dump({"generatedAt": time.strftime("%Y-%m-%d"), "minStars": MIN_STARS,
               "pushedSince": PUSHED_SINCE, "count": len(rows), "candidates": rows},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("\n候选 %d 个 -> %s" % (len(rows), p))
    print("按形态:", dict(Counter(r["kind"] for r in rows)))
    print("按分类:", dict(Counter(r["category"] for r in rows)))
    print("\nTop 50:")
    for r in rows[:50]:
        print("  %-44s ★%-7d %-9s %-26s %s" % (
            r["full_name"][:44], r.get("stars") or 0, r["kind"], r["category"], (r.get("license") or "-")))


if __name__ == "__main__":
    main()
