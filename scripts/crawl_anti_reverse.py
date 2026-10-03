#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""爬取「加密 / 加壳 / 防解密 / 防反汇编 / 防调试 / 防逆向 / 防破解」方向的上游项目。

分四类搜索候选：
  - mcp    : 名字或描述含 mcp 的仓库（可接进 Agent 的 MCP 服务）
  - tool   : 通用安全工具
  - plugin : Agent 技能/插件仓（skills / plugin / agent 形态）
  - pack   : 专家团/角色集合仓

产出 scripts/upstream-audit/anti-reverse-raw.json（原始候选，待人工核验后入库）。
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import OrderedDict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("GH_TOKEN", "")
UA = "skillx-crawler/1.0"

QUERIES = [
    # MCP
    ("mcp", "mcp obfuscation"),
    ("mcp", "mcp deobfuscate"),
    ("mcp", "mcp unpack"),
    ("mcp", "mcp reverse engineering server"),
    ("mcp", "mcp anti-debug"),
    ("mcp", "modelcontextprotocol packer"),
    ("mcp", "mcp binary analysis"),
    ("mcp", "mcp disassembler"),
    ("mcp", "mcp debugger"),
    # 工具/框架
    ("tool", "packer obfuscator"),
    ("tool", "anti-debug"),
    ("tool", "anti-tamper"),
    ("tool", "code obfuscation"),
    ("tool", "binary obfuscator"),
    ("tool", "unpacker"),
    ("tool", "anti reverse engineering"),
    ("tool", "crackme"),
    ("tool", "software protection"),
    ("tool", "license anti piracy"),
    ("tool", "deobfuscator"),
    ("tool", "control flow flattening"),
    ("tool", "vmprotect"),
    ("tool", "themida"),
    ("tool", "binary instrumentation"),
    ("tool", "dll hijacking protection"),
    # 插件/技能
    ("plugin", "claude skill reverse engineering"),
    ("plugin", "agent skill obfuscation"),
    ("plugin", "codex plugin reverse"),
    ("plugin", "security agent skills packer"),
    ("plugin", "skills anti analysis"),
    # 专家团
    ("pack", "expert agents reverse engineering"),
    ("pack", "agents pack malware analysis"),
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
                time.sleep(4 * (attempt + 1))
                continue
            return e.code, {}
        except Exception:  # noqa: BLE001
            time.sleep(3)
    return 0, {}


def search(kind, q):
    url = ("https://api.github.com/search/repositories?q=%s&sort=stars&order=desc&per_page=25"
           % urllib.parse.quote(q))
    st, j = gh(url)
    if st != 200:
        print("  ! %-40s HTTP %d" % (q, st))
        return []
    items = j.get("items", [])
    print("  %-42s %d 条" % (q, len(items)))
    out = []
    for it in items:
        out.append({
            "kind": kind,
            "query": q,
            "full_name": it.get("full_name"),
            "description": (it.get("description") or "")[:200],
            "stars": it.get("stargazers_count"),
            "language": it.get("language"),
            "license": ((it.get("license") or {}).get("spdx_id") or ""),
            "archived": it.get("archived"),
            "pushed_at": it.get("pushed_at"),
            "topics": (it.get("topics") or [])[:10],
            "html_url": it.get("html_url"),
        })
    return out


def main():
    import urllib.parse
    seen = OrderedDict()
    print("搜索 %d 组关键词 ...\n" % len(QUERIES))
    for kind, q in QUERIES:
        for r in search(kind, q):
            seen.setdefault(r["full_name"], r)
        time.sleep(2)  # GitHub search 限流

    rows = list(seen.values())

    # 相关性打分：命中主题词越多越靠前
    KEYWORDS = [
        "obfuscat", "packer", "packing", "unpack", "anti-debug", "antidebug",
        "anti-reverse", "antireverse", "disassembl", "reverse engineering",
        "deobfuscat", "tamper", "crack", "licens", "protection", "crypter",
        "shell", "malware analysis", "binary analysis", "debugger", "hook",
        "instrumentation", "sandbox", "evasion",
    ]
    def score(r):
        blob = (" ".join([r.get("full_name", ""), r.get("description", "")] + r.get("topics", []))).lower()
        hits = sum(1 for k in KEYWORDS if k in blob)
        r["_hits"] = hits
        r["_keywords"] = [k for k in KEYWORDS if k in blob]
        return hits

    rows = [r for r in rows if score(r) >= 1 and not r.get("archived")]
    rows.sort(key=lambda r: (-r["_hits"], -(r.get("stars") or 0)))

    od = os.path.join(ROOT, "scripts", "upstream-audit")
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, "anti-reverse-raw.json")
    json.dump(rows, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n候选 %d 个 -> %s\n" % (len(rows), p))

    from collections import Counter
    print("按类型:", Counter(r["kind"] for r in rows))
    print("\nTop 40:")
    for r in rows[:40]:
        print("  %-46s ★%-7d %-12s %s" % (
            r["full_name"][:46], r.get("stars") or 0, r["kind"], ",".join(r["_keywords"][:3])))


if __name__ == "__main__":
    main()
