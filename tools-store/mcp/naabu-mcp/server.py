#!/usr/bin/env python3
"""Naabu MCP server —— 把 naabu 封装成可被 AI 调用的端口扫描工具。"""
from __future__ import annotations

import json
import shutil
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("naabu")


def _bin() -> str:
    path = shutil.which("naabu")
    if not path:
        raise RuntimeError("naabu 未安装：https://github.com/projectdiscovery/naabu")
    return path


def _build_command(host: str, top_ports: str | None) -> list[str]:
    cmd = [_bin(), "-host", host, "-json", "-silent"]
    if top_ports:
        cmd += ["-top-ports", top_ports]
    return cmd


def _parse(stdout: str) -> list[dict]:
    ports: list[dict] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ports.append(
            {
                "port": rec.get("port"),
                "protocol": rec.get("protocol"),
                "tls": rec.get("tls"),
                "ip": rec.get("ip"),
                "host": rec.get("host"),
            }
        )
    # 去重（按 port/protocol）
    seen = set()
    uniq = []
    for p in ports:
        key = (p.get("port"), p.get("protocol"))
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return sorted(uniq, key=lambda x: (x.get("port") or 0))


@mcp.tool()
def scan_ports(host: str, top_ports: str | None = "1000") -> str:
    """对单个 host 执行快速端口扫描，返回开放的端口列表。

    参数:
        host: 目标主机，例如 example.com 或 1.2.3.4
        top_ports: 扫描 Top N 常用端口，默认 "1000"，传 null 表示全端口

    返回:
        JSON 字符串，包含 host、count、ports。
    """
    if not host or "/" in host or " " in host:
        raise ValueError("host 必须是单个主机名或 IP")

    proc = subprocess.run(
        _build_command(host, top_ports),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"naabu 退出码 {proc.returncode}: {proc.stderr.strip()}")

    ports = _parse(proc.stdout)
    return json.dumps(
        {"host": host, "count": len(ports), "ports": ports},
        ensure_ascii=False,
    )


if __name__ == "__main__":
    mcp.run()
