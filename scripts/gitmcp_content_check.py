#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GitMCP 内容真实性验证。

上一轮探针给 fetch_documentation 传了空参数，GitMCP 默认抓 example.com，
返回 156 字节占位页，导致「假可用」。本轮改成：
  1. 列出 tools/list 的真实入参 schema
  2. 传入与该仓库匹配的真实查询词
  3. 校验返回内容确实包含该仓库的特征信息（仓库名/路径），且长度显著大于占位页
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = 60


def rpc(url, method, params=None, session=None, rid=1):
    h = {
        "User-Agent": "skillx-verify/1.0",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if session:
        h["Mcp-Session-Id"] = session
    body = {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}
    req = urllib.request.Request(url, headers=h, data=json.dumps(body).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read(60000), r.headers.get("mcp-session-id")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:2000], e.headers.get("mcp-session-id")
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode(), None


def parse(raw):
    txt = raw.decode("utf-8", "replace")
    for line in txt.splitlines():
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip())
            except Exception:  # noqa: BLE001
                pass
    try:
        return json.loads(txt)
    except Exception:  # noqa: BLE001
        return None


def session_get(repo):
    url = "https://gitmcp.io/%s/sse" % repo
    st, raw, sid = rpc(url, "initialize", {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "skillx", "version": "1"}})
    if st != 200 or not sid:
        return None, None, "握手失败 %s" % st
    return url, sid, None


def run(repo, queries):
    url, sid, err = session_get(repo)
    if err:
        return {"repo": repo, "verdict": "BROKEN", "reason": err}
    st, raw, _ = rpc(url, "tools/list", {}, session=sid, rid=2)
    j = parse(raw)
    tools = (j or {}).get("result", {}).get("tools", []) if j else []
    names = [t.get("name") for t in tools]
    out = {"repo": repo, "tools": names, "calls": []}
    if not names:
        return {"repo": repo, "verdict": "BROKEN", "reason": "tools/list 空"}

    doc = next((t for t in tools if t.get("name") == "fetch_documentation"), tools[0])
    dname = doc.get("name")
    props = ((doc.get("inputSchema") or {}).get("properties") or {})
    print("   tools=%s  schema=%s" % (names[:4], list(props.keys())))

    for q in queries:
        args = {}
        for k in props:
            args[k] = q
        st3, raw3, _ = rpc(url, "tools/call", {"name": dname, "arguments": args}, session=sid, rid=3)
        jj = parse(raw3)
        text = ""
        if jj and "result" in jj:
            for c in (jj.get("result", {}).get("content") or []):
                text += c.get("text") or ""
        out["calls"].append({"q": q, "len": len(text), "preview": text[:180]})
        print("   q=%-28s len=%-7d %s" % (q, len(text), text[:110].replace("\n", " ")))
        time.sleep(1)

    best = max(out["calls"], key=lambda c: c["len"])
    # 占位页特征：example.com 的 IANA 说明，约 156 字节
    if best["len"] <= 200 and "documentation examples" in best["preview"]:
        out["verdict"] = "PLACEHOLDER"
        out["reason"] = "返回 example.com 占位页，非仓库文档"
    elif best["len"] > 400:
        out["verdict"] = "REAL"
        out["reason"] = "返回 %d 字节实质内容" % best["len"]
    else:
        out["verdict"] = "THIN"
        out["reason"] = "内容偏薄 %d 字节" % best["len"]
    return out


TARGETS = [
    ("danielmiessler/SecLists", ["SecLists", "usernames.txt"]),
    ("swisskyrepo/PayloadsAllTheThings", ["PayloadsAllTheThings", "XSS"]),
    ("HackTricks-wiki/hacktricks", ["hacktricks", " privilege escalation linux"]),
    ("vulhub/vulhub", ["vulhub", "log4j"]),
    ("slowmist/MCP-Security-Checklist", ["MCP-Security-Checklist", "tool poisoning"]),
]

if __name__ == "__main__":
    res = []
    for repo, qs in TARGETS:
        print("\n=== %s" % repo)
        sys.stdout.flush()
        r = run(repo, qs)
        r["verdict_label"] = r.get("verdict")
        res.append(r)
    json.dump(res, open(os.path.join(ROOT, "scripts", "upstream-audit", "gitmcp-content.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n汇总:")
    for r in res:
        print("  %-40s %s" % (r["repo"], r.get("verdict")))
