# 函数型 MCP 工具集

四个可直接运行的 stdio MCP server，把确定性 CLI 工具封装成 AI 可调用工具：

| 目录 | 工具 | 暴露的工具函数 | 依赖二进制 |
| --- | --- | --- | --- |
| `subfinder-mcp/` | subfinder | `enumerate_subdomains(domain)` | subfinder |
| `nuclei-mcp/` | nuclei | `scan_target(target, tags?, severity?)` | nuclei |
| `naabu-mcp/` | naabu | `scan_ports(host, top_ports?)` | naabu |
| `ffuf-mcp/` | ffuf | `fuzz(url, wordlist, ...)` | ffuf |

## 通用运行方式

```bash
cd <工具目录>
pip install -r requirements.txt
mcp run server.py
```

客户端配置见各目录 `mcp.json`（`command=python, args=[server.py]`）。

## 统一封装模式

每个 `server.py` 只做四件事，改造成其它 CLI 工具照搬即可：

1. `_bin()` —— 定位二进制并做存在性检查；
2. `_build_command()` —— 拼装参数（统一带 `-json -silent` 保证输出可解析）；
3. `_parse()` —— 把 stdout 解析成结构化结果；
4. `@mcp.tool()` —— 声明入参/出参 schema 与给 AI 的描述。

## 命名建议

上架「可调用工具」目录时统一前缀分组：`recon/subfinder`、`scan/nuclei`、`scan/naabu`、`fuzz/ffuf`。
