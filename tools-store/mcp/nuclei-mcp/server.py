#!/usr/bin/env python3
"""Nuclei MCP server —— 把 nuclei 封装成可被 AI 调用的漏洞扫描工具。"""
from __future__ import annotations

import json
import shutil
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nuclei")


def _bin() -> str:
    path = shutil.which("nuclei")
    if not path:
        raise RuntimeError("nuclei 未安装：https://github.com/projectdiscovery/nuclei")
    return path


def _build_command(target: str, tags: list[str] | None, severity: list[str] | None) -> list[str]:
    cmd = [_bin(), "-u", target, "-json", "-silent"]
    if tags:
        cmd += ["-tags", ",".join(tags)]
    if severity:
        cmd += ["-severity", ",".join(severity)]
    return cmd


def _parse(stdout: str) -> list[dict]:
    findings: list[dict] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        info = rec.get("info") or {}
        findings.append(
            {
                "template_id": rec.get("template-id") or rec.get("templateID"),
                "name": info.get("name"),
                "severity": info.get("severity"),
                "matched_at": rec.get("matched-at") or rec.get("matched"),
                "type": rec.get("type"),
                "host": rec.get("host"),
            }
        )
    return findings


@mcp.tool()
def scan_target(
    target: str,
    tags: list[str] | None = None,
    severity: list[str] | None = None,
) -> str:
    """对单个目标执行 nuclei 模板化漏洞扫描，返回结构化 findings。

    参数:
        target: 目标 URL 或 host，例如 https://example.com 或 example.com
        tags:   可选，按标签过滤模板，例如 ["cve","rce"]
        severity: 可选，按等级过滤，例如 ["critical","high"]

    返回:
        JSON 字符串，包含 target、count、findings。
    """
    if not target or " " in target:
        raise ValueError("target 必须是单个 URL 或 host")

    proc = subprocess.run(
        _build_command(target, tags, severity),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"nuclei 退出码 {proc.returncode}: {proc.stderr.strip()}")

    findings = _parse(proc.stdout)
    return json.dumps(
        {"target": target, "count": len(findings), "findings": findings},
        ensure_ascii=False,
    )


if __name__ == "__main__":
    mcp.run()
