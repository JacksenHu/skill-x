#!/usr/bin/env python3
"""给 4 个自研 stdio MCP server 补 uv 打包(pyproject.toml)并修正 mcp.json 的 cwd 为可移植路径。

uv 虚拟项目(package=false):依赖声明进 pyproject.toml,客户端用 `uv run server.py` 即可跑,
不再依赖裸 `python + pip install -r requirements.txt`。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MCP_DIR = ROOT / "tools-store" / "mcp"

SERVERS = {
    "subfinder-mcp": ("subfinder", "被动子域名枚举(subfinder)"),
    "nuclei-mcp": ("nuclei", "漏洞扫描(nuclei)"),
    "naabu-mcp": ("naabu", "端口扫描(naabu)"),
    "ffuf-mcp": ("ffuf", "目录/参数模糊测试(ffuf)"),
}


def main():
    for d, (short, desc) in SERVERS.items():
        base = MCP_DIR / d
        if not base.is_dir():
            continue
        # 1) pyproject.toml
        (base / "pyproject.toml").write_text(
            f"""[project]
name = "{d}"
version = "0.1.0"
description = "MCP server wrapping {short} — {desc}"
requires-python = ">=3.10"
dependencies = ["mcp>=1.0.0"]

[tool.uv]
package = false
""", encoding="utf-8")
        # 2) 修正 mcp.json:cwd 改成相对 repo 的占位,命令用 uv run
        mcp_json = base / "mcp.json"
        cfg = json.loads(mcp_json.read_text(encoding="utf-8"))
        srv = cfg["mcpServers"][short]
        srv["command"] = "uv"
        srv["args"] = ["run", "server.py"]
        srv["cwd"] = f"<skillx>/tools-store/mcp/{d}"
        mcp_json.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[+] {d}: pyproject.toml + mcp.json 已修正")
    return 0


if __name__ == "__main__":
    sys.exit(main())
