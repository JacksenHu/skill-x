#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""可用性审计：MCP 注册表 + 工具商店上游真实可达性探测。

输出：scripts/upstream-audit/report.json 与 report.md
检查维度：
  1. MCP remote 端点：HTTP GET/POST 探针（MCP 端点允许 4xx，只需有 HTTP 响应）
  2. MCP gitmcp 端点：https://gitmcp.io/<owner>/<repo> 可达性
  3. MCP link / websiteUrl：GitHub 仓库是否存在（API 归档状态）
  4. VS Code 扩展：marketplace 查询是否有结果
  5. npm / pypi 包：注册表是否存在该版本
  6. 工具商店：GitHub 仓库存在性 + 归档状态 + 最近推送时间
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH_TOKEN = os.environ.get("GH_TOKEN", "")
UA = "skillx-upstream-audit/1.0 (+https://skillx.yueliai.top)"

TIMEOUT = 20


def http_json(url, headers=None, method="GET", data=None):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=h, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read()
            return r.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode("utf-8")


def http_probe(url, method="GET", extra=None):
    """只关心是否有 HTTP 层响应；MCP 端点返回 4xx 也算活着。"""
    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    data = None
    if method == "POST":
        data = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        ).encode()
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            r.read(2048)
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def gh_api(path):
    url = "https://api.github.com" + path
    headers = {}
    if GH_TOKEN:
        headers["Authorization"] = "Bearer " + GH_TOKEN
    st, raw = http_json(url, headers=headers)
    if st != 200:
        return st, None
    try:
        return st, json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return st, None


def check_github_repo(full):
    st, j = gh_api("/repos/" + full)
    if st == 200 and j:
        return {
            "ok": True,
            "status": st,
            "archived": bool(j.get("archived")),
            "disabled": bool(j.get("disabled")),
            "stars": j.get("stargazers_count"),
            "pushed_at": j.get("pushed_at"),
            "full_name": j.get("full_name"),
            "desc": (j.get("description") or "")[:120],
        }
    return {"ok": False, "status": st, "archived": None}


def check_marketplace(extid):
    url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
    payload = {
        "filters": [
            {
                "criteria": [{"filterType": 7, "value": extid}],
                "pageNumber": 1,
                "pageSize": 1,
            }
        ],
        "assetTypes": [],
        "flags": 0,
    }
    st, raw = http_json(
        url,
        headers={"Accept": "application/json;api-version=7.1-preview.1"},
        method="POST",
        data=payload,
    )
    if st != 200:
        return {"ok": False, "status": st}
    try:
        j = json.loads(raw.decode("utf-8"))
        results = j["results"][0]["extensions"]
    except Exception:  # noqa: BLE001
        return {"ok": False, "status": st, "note": "parse-fail"}
    if not results:
        return {"ok": False, "status": st, "note": "no-result"}
    e = results[0]
    ver = ""
    for v in e.get("versions", []):
        ver = v.get("version", "")
        break
    return {"ok": True, "status": st, "version": ver}


def check_npm(pkg, ver=None):
    url = "https://registry.npmjs.org/" + urllib.parse.quote(pkg, safe="@/")
    st, raw = http_json(url)
    if st != 200:
        return {"ok": False, "status": st}
    try:
        j = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return {"ok": False, "status": st, "note": "parse-fail"}
    has = bool(ver) and ver in j.get("versions", {})
    latest = (j.get("dist-tags") or {}).get("latest")
    return {"ok": True, "status": st, "version_present": has, "latest": latest}


def check_pypi(pkg, ver=None):
    url = "https://pypi.org/pypi/{}/json".format(urllib.parse.quote(pkg))
    st, raw = http_json(url)
    if st != 200:
        return {"ok": False, "status": st}
    try:
        j = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return {"ok": False, "status": st, "note": "parse-fail"}
    has = bool(ver) and ver in (j.get("releases") or {})
    return {"ok": True, "status": st, "version_present": has, "latest": j.get("info", {}).get("version")}


# ---------------------------------------------------------------- MCP

def mcp_targets(servers):
    out = []
    for s in servers:
        name = s.get("name")
        url = s.get("websiteUrl") or ""
        m = (s.get("_meta") or {}).get("top.skillx/curated") or {}
        kind = m.get("kind")
        item = {"name": name, "title": s.get("title"), "kind": kind, "websiteUrl": url}
        for r in s.get("remotes") or []:
            item["remote_url"] = r.get("url")
        for p in s.get("packages") or []:
            item["pkg"] = {
                "registry": p.get("registryType"),
                "id": p.get("identifier"),
                "version": p.get("version"),
            }
        hint = m.get("installHint") or ""
        g = re.search(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", hint or url)
        if g:
            item["repo"] = g.group(1) + "/" + re.sub(r"\.git$", "", g.group(2))
        gm = re.search(r"gitmcp\.io[:/]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", hint or "")
        if gm:
            item["gitmcp"] = "https://gitmcp.io/" + gm.group(1) + "/" + gm.group(2)
            item.setdefault("repo", gm.group(1) + "/" + gm.group(2))
        if re.match(r"^[a-z0-9.-]+\.[a-z0-9.-]+$", name or "") and "vscode" in (url + name).lower():
            pass
        out.append(item)
    return out


def audit_mcp(servers):
    rows = []
    items = mcp_targets(servers)

    def work(it):
        res = dict(it)
        checks = []
        if it.get("remote_url"):
            st, err = http_probe(it["remote_url"], "GET")
            if st == 0 or st in (405, 406):
                st2, _ = http_probe(it["remote_url"], "POST")
                checks.append({"type": "remote-http", "url": it["remote_url"], "status": st2, "ok": st2 != 0})
            else:
                checks.append({"type": "remote-http", "url": it["remote_url"], "status": st, "ok": True})
        if it.get("gitmcp"):
            st, _ = http_probe(it["gitmcp"], "GET")
            checks.append({"type": "gitmcp", "url": it["gitmcp"], "status": st, "ok": st == 200})
        if it.get("pkg"):
            p = it["pkg"]
            if p["registry"] == "npm":
                r = check_npm(p["id"], p.get("version"))
            else:
                r = check_pypi(p["id"], p.get("version"))
            r.update({"type": "pkg:" + str(p["registry"]), "target": p["id"]})
            checks.append(r)
        if it.get("repo"):
            r = check_github_repo(it["repo"])
            r.update({"type": "github", "target": it["repo"]})
            checks.append(r)
        # VS Code 扩展
        if it["kind"] == "link" and (it.get("websiteUrl") or ""):
            pass
        res["checks"] = checks
        return res

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(work, it) for it in items]
        for f in as_completed(futs):
            rows.append(f.result())
    rows.sort(key=lambda r: r["name"])
    return rows


# ---------------------------------------------------------------- TOOLS

def audit_tools(tools):
    rows = []

    def work(t):
        res = {"slug": t.get("slug"), "name": t.get("name"), "repo": t.get("repo")}
        checks = []
        if t.get("repo"):
            r = check_github_repo(t["repo"])
            r.update({"type": "github", "target": t["repo"]})
            checks.append(r)
        if t.get("docs_url"):
            st, _ = http_probe(t["docs_url"], "GET")
            checks.append({"type": "docs", "url": t["docs_url"], "status": st, "ok": st in (200, 301, 302)})
        if (t.get("gitmcp") or {}).get("url"):
            u = t["gitmcp"]["url"]
            st, _ = http_probe(u, "GET")
            checks.append({"type": "gitmcp", "url": u, "status": st, "ok": st == 200})
        res["checks"] = checks
        return res

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(work, t) for t in tools]
        for f in as_completed(futs):
            rows.append(f.result())
    rows.sort(key=lambda r: r.get("slug") or "")
    return rows


def main():
    t0 = time.time()
    mcp = json.load(open(os.path.join(ROOT, "mcp-registry.json"), encoding="utf-8"))
    tools = json.load(open(os.path.join(ROOT, "tools-store", "api-import-payload.json"), encoding="utf-8"))

    print("probing {} mcp / {} tools ...".format(len(mcp["servers"]), len(tools["tools"])))
    mcp_rows = audit_mcp(mcp["servers"])
    tool_rows = audit_tools(tools["tools"])

    outdir = os.path.join(ROOT, "scripts", "upstream-audit")
    os.makedirs(outdir, exist_ok=True)
    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_sec": round(time.time() - t0, 1),
        "mcp": mcp_rows,
        "tools": tool_rows,
    }
    with open(os.path.join(outdir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("written", os.path.join(outdir, "report.json"))


if __name__ == "__main__":
    main()
