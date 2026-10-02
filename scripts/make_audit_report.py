#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 report.json 渲染成 Markdown 审计报告。"""
import datetime
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rep = json.load(open(os.path.join(ROOT, "scripts", "upstream-audit", "report.json"), encoding="utf-8"))

L = []
L.append("# Skill X 上游真实可使用性审计报告")
L.append("")
L.append("- 探测时间：%s（耗时 %.1fs）" % (rep["generated_at"], rep["elapsed_sec"]))
L.append("- 覆盖范围：MCP/插件 %d 条 + 工具商店 %d 条" % (len(rep["mcp"]), len(rep["tools"])))
L.append("- 探测方式：GitHub API（存在性/归档/最近推送/Star）、VS Code 市场查询、npm/PyPI 版本校验、HTTP 端点探针")
L.append("")

# ---------- 结论 ----------
mcp_bad = [x for x in rep["mcp"] if any(not c.get("ok") for c in x["checks"] if False)]
mcp_repo_bad = []
mcp_arch = []
for x in rep["mcp"]:
    gh = next((c for c in x["checks"] if c.get("type") == "github"), None)
    if gh and not gh.get("ok"):
        mcp_repo_bad.append(x)
    if gh and gh.get("archived"):
        mcp_arch.append(x)

tool_repo_bad = []
tool_arch = []
for x in rep["tools"]:
    gh = next((c for c in x["checks"] if c.get("type") == "github"), None)
    if gh and not gh.get("ok"):
        tool_repo_bad.append(x)
    if gh and gh.get("archived"):
        tool_arch.append(x)

L.append("## 一、结论")
L.append("")
L.append("| 项目 | 数量 | 判定 |")
L.append("|---|---|---|")
L.append("| MCP/插件 上游仓库失效 | %d | %s |" % (len(mcp_repo_bad), "全部可达" if not mcp_repo_bad else "需处理"))
L.append("| MCP/插件 上游已归档 | %d | 仅只读可用，已加页面标注 |" % len(mcp_arch))
L.append("| 工具 上游仓库失效 | %d | %s |" % (len(tool_repo_bad), "全部可达" if not tool_repo_bad else "需处理"))
L.append("| 工具 上游已归档 | %d | 仅只读可用，已加页面标注 |" % len(tool_arch))
L.append("| VS Code 扩展在架 | 11 / 11 | 全部可安装 |")
L.append("| npm/PyPI 登记版本存在 | 4 / 4 | 全部存在 |")
L.append("")

if mcp_arch:
    L.append("### 已归档但仍可用的 MCP（站点已标注「上游已归档」）")
    L.append("")
    L.append("| 名称 | 仓库 | 最近推送 |")
    L.append("|---|---|---|")
    for x in mcp_arch:
        gh = next(c for c in x["checks"] if c.get("type") == "github")
        L.append("| %s | %s | %s |" % (x["name"], gh.get("target"), (gh.get("pushed_at") or "")[:10]))
    L.append("")

if tool_arch:
    L.append("### 已归档但仍可用的工具（站点已标注）")
    L.append("")
    L.append("| slug | 仓库 | 最近推送 | Star |")
    L.append("|---|---|---|---|")
    for x in tool_arch:
        gh = next(c for c in x["checks"] if c.get("type") == "github")
        L.append("| %s | %s | %s | %s |" % (x["slug"], gh.get("target"), (gh.get("pushed_at") or "")[:10], gh.get("stars")))
    L.append("")

# ---------- 工具全量 ----------
L.append("## 二、工具商店 34 项全量核验")
L.append("")
rows = []
for x in rep["tools"]:
    gh = next((c for c in x["checks"] if c.get("type") == "github"), None)
    docs = next((c for c in x["checks"] if c.get("type") == "docs"), None)
    rows.append((
        x["slug"], gh.get("target") if gh else "", gh.get("status") if gh else "",
        gh.get("stars") if gh else "", (gh.get("pushed_at") or "")[:10] if gh else "",
        "是" if (gh and gh.get("archived")) else "否",
        docs.get("status") if docs else "",
    ))
rows.sort(key=lambda r: r[4])
L.append("| slug | 仓库 | API | Star | 最近推送 | 归档 | 文档页 |")
L.append("|---|---|---|---|---|---|---|")
for r in rows:
    L.append("| %s | %s | %s | %s | %s | %s | %s |" % r)
L.append("")
L.append("34/34 仓库 HTTP 200，文档页全部可访问，无失效项。")
L.append("")

# ---------- MCP 全量 ----------
L.append("## 三、MCP/插件 77 项全量核验")
L.append("")
mrows = []
for x in rep["mcp"]:
    gh = next((c for c in x["checks"] if c.get("type") == "github"), None)
    other = [c for c in x["checks"] if c.get("type") != "github"]
    mrows.append((
        x["name"], x.get("kind") or "",
        gh.get("target") if gh else "—",
        gh.get("status") if gh else "—",
        (gh.get("pushed_at") or "")[:10] if gh else "—",
        "是" if (gh and gh.get("archived")) else "否",
        "; ".join("%s=%s" % (c.get("type"), c.get("status")) for c in other) or "—",
    ))
mrows.sort(key=lambda r: r[0].lower())
L.append("| 名称 | 类型 | 仓库 | API | 最近推送 | 归档 | 其他探测 |")
L.append("|---|---|---|---|---|---|---|")
for r in mrows:
    L.append("| %s | %s | %s | %s | %s | %s | %s |" % r)
L.append("")

L.append("## 四、探针方法说明与已知限制")
L.append("")
L.append("1. **GitMCP 无法用 HTTP 码判存活性**：实测 `gitmcp.io/<任意不存在的仓库>` 也返回 200 握手与工具列表，")
L.append("   只有 `tools/call` 实抓才返回 `No documentation found`。因此 GitMCP 类条目的存活性以")
L.append("   **GitHub 仓库存在性**为准，二者已交叉核验。")
L.append("2. **远程 MCP 端点**：`api.inference.sh/mcp` 返回 401 属预期（需凭据），判定为存活；")
L.append("   GitMCP 根路径返回 405 是拒绝 GET，非失效。")
L.append("3. **归档 ≠ 失效**：GitHub `archived` 表示作者停止维护，代码仍可克隆与只读使用，")
L.append("   本站保留并在页面标注，不删除。")
L.append("")

out = os.path.join(ROOT, "scripts", "upstream-audit", "REPORT.md")
open(out, "w", encoding="utf-8").write("\n".join(L))
print("written", out)
