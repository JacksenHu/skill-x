#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 scripts/upstream-audit/report.json 的探测结果写回数据源。

MCP：更新 _meta.top.skillx/curated.upstreamStatus（alive / lastCheck / source），
     若上游仓库已 archived 则写入 archived=true 与 upstreamNote。
工具：写入 tools-store/api-import-payload.json 的 upstream 字段
     （alive / lastCheck / stars / pushedAt / archived）。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-10-03"


def main():
    rep = json.load(open(os.path.join(ROOT, "scripts", "upstream-audit", "report.json"), encoding="utf-8"))

    # ---------------- MCP ----------------
    mcp_path = os.path.join(ROOT, "mcp-registry.json")
    mcp = json.load(open(mcp_path, encoding="utf-8"))
    mcp_rows = {r["name"]: r for r in rep["mcp"]}
    changed = {"mcp": [], "tools": []}

    for s in mcp["servers"]:
        cur = (s.get("_meta") or {}).setdefault("top.skillx/curated", {})
        row = mcp_rows.get(s.get("name"))
        if not row:
            continue
        gh = next((c for c in row["checks"] if c.get("type") == "github"), None)
        alive = True
        note = None
        if gh is not None:
            alive = bool(gh.get("ok"))
            if gh.get("archived"):
                cur["archived"] = True
                note = "上游仓库已归档（archived），不再更新，仍可只读使用。"
            else:
                cur.pop("archived", None)
        for c in row["checks"]:
            if c.get("type") == "pkg:npm" or c.get("type") == "pkg:pypi":
                alive = alive and bool(c.get("version_present", True))
                if not c.get("version_present"):
                    note = "登记的 {registry} 包版本在源站已不存在。".format(registry=c.get("type"))
        status = {
            "source": "audit:upstream_audit.py",
            "lastCheck": TODAY,
            "alive": alive,
            "failSince": None if alive else TODAY,
        }
        if gh and gh.get("pushed_at"):
            status["pushedAt"] = gh["pushed_at"]
        if gh and gh.get("stars") is not None:
            status["stars"] = gh["stars"]
        cur["upstreamStatus"] = status
        if note:
            cur["upstreamNote"] = note
        else:
            cur.pop("upstreamNote", None)
        changed["mcp"].append((s.get("name"), alive, bool(note)))

    with open(mcp_path, "w", encoding="utf-8") as f:
        json.dump(mcp, f, ensure_ascii=False, indent=1)

    # ---------------- TOOLS ----------------
    tp = os.path.join(ROOT, "tools-store", "api-import-payload.json")
    td = json.load(open(tp, encoding="utf-8"))
    trows = {r["slug"]: r for r in rep["tools"]}
    for t in td["tools"]:
        row = trows.get(t.get("slug"))
        if not row:
            continue
        gh = next((c for c in row["checks"] if c.get("type") == "github"), None)
        if not gh:
            continue
        up = {
            "lastCheck": TODAY,
            "alive": bool(gh.get("ok")),
            "stars": gh.get("stars"),
            "pushedAt": gh.get("pushed_at"),
        }
        if gh.get("archived"):
            up["archived"] = True
            up["note"] = "上游仓库已归档（archived），不再更新，仍可只读使用。"
        t["upstream"] = up
        changed["tools"].append((t.get("slug"), up["alive"], bool(gh.get("archived"))))

    with open(tp, "w", encoding="utf-8") as f:
        json.dump(td, f, ensure_ascii=False, indent=1)

    print("MCP 更新 {} 条，异常 {}:".format(len(changed["mcp"]),
          sum(1 for x in changed["mcp"] if not x[1] or x[2])))
    for n, a, nt in changed["mcp"]:
        if not a or nt:
            print("  !", n, "alive=", a, "note=", nt)
    print("TOOLS 更新 {} 条，异常 {}:".format(len(changed["tools"]),
          sum(1 for x in changed["tools"] if not x[1] or x[2])))
    for n, a, ar in changed["tools"]:
        if not a or ar:
            print("  !", n, "alive=", a, "archived=", ar)


if __name__ == "__main__":
    main()
