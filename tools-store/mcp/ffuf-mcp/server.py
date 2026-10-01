#!/usr/bin/env python3
"""FFuf MCP server —— 把 ffuf 封装成可被 AI 调用的目录/参数模糊测试工具。"""
from __future__ import annotations

import json
import shutil
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ffuf")


def _bin() -> str:
    path = shutil.which("ffuf")
    if not path:
        raise RuntimeError("ffuf 未安装：https://github.com/ffuf/ffuf")
    return path


def _build_command(
    url: str,
    wordlist: str,
    match_codes: str | None,
    filter_codes: str | None,
    extensions: str | None,
) -> list[str]:
    cmd = [_bin(), "-u", url, "-w", wordlist, "-json", "-silent"]
    if match_codes:
        cmd += ["-mc", match_codes]
    if filter_codes:
        cmd += ["-fc", filter_codes]
    if extensions:
        cmd += ["-e", extensions]
    return cmd


def _parse(stdout: str) -> list[dict]:
    results: list[dict] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        results.append(
            {
                "url": rec.get("url"),
                "status": rec.get("status"),
                "length": rec.get("length"),
                "words": rec.get("words"),
                "lines": rec.get("lines"),
                "host": rec.get("host"),
            }
        )
    return results


@mcp.tool()
def fuzz(
    url: str,
    wordlist: str,
    match_codes: str | None = "200,204,301,302,307,401,403",
    filter_codes: str | None = None,
    extensions: str | None = None,
) -> str:
    """对目标 URL 做目录/文件模糊测试（URL 中需包含 FUZZ 占位符）。

    参数:
        url: 含 FUZZ 占位符的目标 URL，例如 https://example.com/FUZZ
        wordlist: 本机字典文件绝对路径
        match_codes: 匹配的 HTTP 状态码（逗号分隔）
        filter_codes: 排除的 HTTP 状态码（逗号分隔）
        extensions: 可选，追加扩展名（逗号分隔），例如 "php,html"

    返回:
        JSON 字符串，包含 url、count、results。
    """
    if "FUZZ" not in url:
        raise ValueError("url 必须包含 FUZZ 占位符")
    if not wordlist:
        raise ValueError("wordlist 不能为空")

    proc = subprocess.run(
        _build_command(url, wordlist, match_codes, filter_codes, extensions),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffuf 退出码 {proc.returncode}: {proc.stderr.strip()}")

    results = _parse(proc.stdout)
    return json.dumps(
        {"url": url, "count": len(results), "results": results},
        ensure_ascii=False,
    )


if __name__ == "__main__":
    mcp.run()
