#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GitMCP 端点真实协议探测：initialize -> 取 Mcp-Session-Id -> tools/list -> tools/call。

用于区分「仓库存在且文档可取」与「GitMCP 对任意路径都返回握手成功」。
"""
import json
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://gitmcp.io/{}/sse"


def call(url, method, params=None, session=None, timeout=40):
    h = {
        "User-Agent": "curl/8",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if session:
        h["Mcp-Session-Id"] = session
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(url, headers=h, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(4000), r.headers.get("mcp-session-id")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:800], e.headers.get("mcp-session-id")
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode(), None


def parse(raw):
    """SSE 帧里取 data: 行。"""
    txt = raw.decode("utf-8", "replace")
    for line in txt.splitlines():
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip())
            except Exception:  # noqa: BLE001
                return None
    try:
        return json.loads(txt)
    except Exception:  # noqa: BLE001
        return None


def probe(repo):
    url = BASE.format(repo)
    st, raw, sid = call(url, "initialize", {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "skillx-audit", "version": "1"},
    })
    if st != 200:
        return {"repo": repo, "ok": False, "stage": "initialize", "status": st}
    if not sid:
        return {"repo": repo, "ok": False, "stage": "no-session-id", "status": st,
                "raw": raw.decode("utf-8", "replace")[:200]}
    st2, raw2, _ = call(url, "tools/list", {}, session=sid)
    j2 = parse(raw2)
    tools = []
    if j2 and "result" in j2:
        tools = [t.get("name") for t in j2["result"].get("tools", [])]
    if not tools:
        return {
            "repo": repo, "ok": False, "stage": "tools/list", "status": st2,
            "raw": (raw2.decode("utf-8", "replace"))[:300],
        }
    # 真抓一次文档，验证内容非错误页
    target = "fetch_documentation" if "fetch_documentation" in tools else tools[0]
    st3, raw3, _ = call(url, "tools/call", {"name": target, "arguments": {}}, session=sid)
    t3 = raw3.decode("utf-8", "replace")
    content = ""
    j3 = parse(raw3)
    if j3 and "result" in j3:
        for c in j3["result"].get("content", []):
            content += (c.get("text") or "")[:200]
    empty_markers = ("No documentation found", "not found", "Repository not found", "404")
    usable = bool(content) and not any(m.lower() in content.lower() for m in empty_markers)
    return {
        "repo": repo, "ok": True, "tools": tools, "call_status": st3,
        "usable": usable,
        "call_preview": content[:200] or t3[:200],
    }


if __name__ == "__main__":
    repos = sys.argv[1:] or ["vulhub/vulhub", "__nope__/__notexist__"]
    out = [probe(r) for r in repos]
    print(json.dumps(out, ensure_ascii=False, indent=1))
