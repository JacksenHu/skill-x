#!/usr/bin/env python3
"""Subfinder MCP server —— 把 subfinder 封装成可被 AI 调用的 MCP 工具。

运行方式（stdio transport）：
    pip install -r requirements.txt
    mcp run server.py

或在任意 MCP 客户端中配置：
    command: python
    args: [server.py]
    cwd: <本目录>

改造为其它 CLI 工具（nuclei / naabu / ffuf / dirsearch / gau 等）时，
只需替换 _build_command() 的二进制名、参数与 _parse() 的输出解析逻辑。
"""
from __future__ import annotations

import json
import shutil
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("subfinder")


def _bin() -> str:
    path = shutil.which("subfinder")
    if not path:
        raise RuntimeError(
            "subfinder 未安装。请先安装：https://github.com/projectdiscovery/subfinder"
        )
    return path


def _build_command(domain: str, silent: bool) -> list[str]:
    cmd = [_bin(), "-d", domain, "-json"]
    if silent:
        cmd.append("-silent")
    return cmd


def _parse(stdout: str) -> list[str]:
    hosts: set[str] = set()
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            host = rec.get("host") or rec.get("subdomain")
            if host:
                hosts.add(str(host))
        except json.JSONDecodeError:
            hosts.add(line)
    return sorted(hosts)


@mcp.tool()
def enumerate_subdomains(domain: str, silent: bool = True) -> str:
    """对指定根域名做被动子域名枚举，返回去重后的子域名列表（JSON）。

    参数:
        domain: 目标根域名，例如 example.com
        silent: 是否只输出结果而不输出 banner（默认 True）

    返回:
        JSON 字符串，包含 domain、count、subdomains 三个字段。
    """
    if not domain or "/" in domain or " " in domain:
        raise ValueError("domain 必须是单个根域名，例如 example.com")

    proc = subprocess.run(
        _build_command(domain, silent),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"subfinder 退出码 {proc.returncode}: {proc.stderr.strip()}")

    hosts = _parse(proc.stdout)
    return json.dumps(
        {"domain": domain, "count": len(hosts), "subdomains": hosts},
        ensure_ascii=False,
    )


if __name__ == "__main__":
    mcp.run()
