#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""真实可使用性验证：不只看 HTTP 通不通，要跑完整 MCP 会话。

对每条 remote/gitmcp 端点：
  1. initialize 握手（带正确的 Accept 头：application/json, text/event-stream）
  2. 取 Mcp-Session-Id
  3. notifications/initialized
  4. tools/list  -> 拿到真实工具清单
  5. tools/call  -> 实抓一次结果，判断内容是否为空壳

判定：
  USABLE   - 握手成功 + 有工具 + 实抓返回了实质内容
  EMPTY    - 握手成功 + 有工具，但实抓返回 "No documentation found" 之类空壳
  BROKEN   - 握手失败 / 无工具 / 协议报错
"""
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = 45

EMPTY_MARKERS = [
    "no documentation found",
    "not found",
    "repository not found",
    "404 not found",
    "failed to fetch",
    "unable to fetch",
    "error fetching",
]


def rpc(url, method, params=None, session=None, rid=1, timeout=TIMEOUT):
    h = {
        "User-Agent": "skillx-usability/1.0",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if session:
        h["Mcp-Session-Id"] = session
    body = {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}
    req = urllib.request.Request(url, headers=h, data=json.dumps(body).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(30000), r.headers.get("mcp-session-id")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:2000], e.headers.get("mcp-session-id")
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode(), None


def parse_sse(raw):
    txt = raw.decode("utf-8", "replace")
    # SSE: 可能有多行 data:
    datas = []
    for line in txt.splitlines():
        if line.startswith("data:"):
            try:
                datas.append(json.loads(line[5:].strip()))
            except Exception:  # noqa: BLE001
                pass
    if datas:
        for d in datas:
            if "result" in d or "error" in d:
                return d
        return datas[0]
    try:
        return json.loads(txt)
    except Exception:  # noqa: BLE001
        return None


def probe(url, repo_hint=""):
    res = {"url": url, "repo": repo_hint}
    st, raw, sid = rpc(url, "initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "skillx-usability", "version": "1.0"},
    })
    res["init_status"] = st
    if st == 0:
        res["verdict"] = "BROKEN"
        res["reason"] = "连接失败/超时"
        return res
    if st >= 400:
        res["verdict"] = "BROKEN"
        res["reason"] = "握手 HTTP %d: %s" % (st, raw.decode("utf-8", "replace")[:150])
        return res
    j = parse_sse(raw)
    if not j or "result" not in j:
        res["verdict"] = "BROKEN"
        res["reason"] = "握手无 result: %s" % (raw.decode("utf-8", "replace")[:150])
        return res
    res["server_info"] = (j["result"].get("serverInfo") or {}).get("name", "")
    sid = sid or ""
    if not sid:
        res["verdict"] = "BROKEN"
        res["reason"] = "握手未下发 Mcp-Session-Id"
        return res

    # initialized 通知
    rpc(url, "notifications/initialized", {}, session=sid)

    st2, raw2, _ = rpc(url, "tools/list", {}, session=sid, rid=2)
    j2 = parse_sse(raw2)
    tools = []
    if j2 and "result" in j2:
        tools = j2["result"].get("tools", []) or []
    res["tool_count"] = len(tools)
    res["tools"] = [t.get("name") for t in tools][:8]
    if not tools:
        res["verdict"] = "BROKEN"
        res["reason"] = "tools/list 空: %s" % (raw2.decode("utf-8", "replace")[:150])
        return res

    # 实抓一次
    names = [t.get("name") for t in tools]
    pick = None
    for pref in ("fetch_documentation", "search_documentation", "fetch_generic_url_content"):
        if pref in names:
            pick = pref
            break
    if pick is None:
        pick = names[0]
    schema = next((t.get("inputSchema") for t in tools if t.get("name") == pick), {}) or {}
    args = {}
    for k, v in (schema.get("properties") or {}).items():
        if v.get("type") == "string":
            if "url" in k.lower():
                args[k] = "https://example.com"
            elif "query" in k.lower() or "q" == k.lower():
                args[k] = "security"
            else:
                args[k] = "test"
    st3, raw3, _ = rpc(url, "tools/call", {"name": pick, "arguments": args}, session=sid, rid=3)
    j3 = parse_sse(raw3)
    text = ""
    if j3 and "result" in j3:
        for c in j3.get("result", {}).get("content", []) or []:
            text += (c.get("text") or "")
    res["call_tool"] = pick
    res["call_status"] = st3
    res["call_len"] = len(text)
    res["call_preview"] = text[:250]
    low = text.lower()
    if st3 == 0:
        res["verdict"] = "BROKEN"
        res["reason"] = "tools/call 超时"
    elif not text.strip():
        res["verdict"] = "EMPTY"
        res["reason"] = "实抓返回空内容"
    elif any(m in low for m in EMPTY_MARKERS) and len(text) < 400:
        res["verdict"] = "EMPTY"
        res["reason"] = "实抓命中空壳标记"
    else:
        res["verdict"] = "USABLE"
        res["reason"] = "握手+列工具+实抓全部返回实质内容"
    return res


def main():
    mcp = json.load(open(os.path.join(ROOT, "mcp-registry.json"), encoding="utf-8"))
    targets = []
    for s in mcp["servers"]:
        cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
        for r in s.get("remotes") or []:
            u = r.get("url")
            if u and u.startswith("http"):
                targets.append((s.get("name"), u))
        hint = cur.get("installHint") or ""
        if "gitmcp.io" in hint:
            import re
            g = re.search(r"gitmcp\.io[:/]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", hint)
            if g:
                targets.append((s.get("name"), "https://gitmcp.io/%s/%s/sse" % (g.group(1), g.group(2))))
    # 去重
    seen = set()
    uniq = []
    for n, u in targets:
        if u in seen:
            continue
        seen.add(u)
        uniq.append((n, u))

    print("真实会话探测 %d 个端点 ..." % len(uniq))
    out = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(probe, u, n): (n, u) for n, u in uniq}
        for f in as_completed(futs):
            n, u = futs[f]
            try:
                r = f.result()
            except Exception as e:  # noqa: BLE001
                r = {"url": u, "repo": n, "verdict": "BROKEN", "reason": str(e)}
            r["name"] = n
            out.append(r)
    out.sort(key=lambda r: r.get("name", ""))

    from collections import Counter
    c = Counter(r.get("verdict") for r in out)
    print("  USABLE=%d EMPTY=%d BROKEN=%d" % (c.get("USABLE", 0), c.get("EMPTY", 0), c.get("BROKEN", 0)))
    print()
    for r in out:
        flag = {"USABLE": "OK  ", "EMPTY": "EMPTY", "BROKEN": "FAIL"}[r.get("verdict", "BROKEN")]
        print("%s %-52s %s" % (flag, r.get("name", "")[:52], r.get("reason", ""))[:130])

    od = os.path.join(ROOT, "scripts", "upstream-audit")
    os.makedirs(od, exist_ok=True)
    json.dump(out, open(os.path.join(od, "usability-mcp.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nwritten", os.path.join(od, "usability-mcp.json"))


if __name__ == "__main__":
    main()
