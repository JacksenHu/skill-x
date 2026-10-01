# subfinder-mcp

把 `projectdiscovery/subfinder` 封装成一个 **函数调用型 MCP server**（stdio transport），
让 AI 助手可以直接调用 `enumerate_subdomains(domain)`。

## 使用

```bash
pip install -r requirements.txt
# 需先安装 subfinder：https://github.com/projectdiscovery/subfinder
mcp run server.py
```

客户端配置见 `mcp.json`（`command=python, args=[server.py]`）。

## 改造为其它 CLI 工具的模板

`server.py` 只做了三件事，换成别的确定性 CLI 工具时照搬即可：

1. `_build_command()` —— 拼装目标二进制 + 参数（最好带 `-json` / `-silent` 让输出可解析）；
2. `_parse()` —— 把 stdout 解析成结构化结果；
3. `@mcp.tool()` —— 声明给 AI 的入参/出参 schema 与描述。

| 工具 | 替换二进制 | 典型参数 | 输出解析 |
| --- | --- | --- | --- |
| nuclei | `nuclei` | `-u target -json` | JSON 行，取 `matched-at`/`info.name` |
| naabu | `naabu` | `-host target -json` | JSON 行，取 `port` |
| katana | `katana` | `-u target -json` | JSON 行，取 `response`/URL |
| ffuf | `ffuf` | `-u URL/FUZZ -w wordlist -json` | JSON 行 |
| gau | `gau` | `domain`（纯文本） | 每行一个 URL，直接去重 |
| waybackurls | `waybackurls` | `domain`（纯文本） | 每行一个 URL，直接去重 |

## 命名建议

上架 gitmcp.io 之外的「可调用工具」目录时，工具名建议统一前缀，例如：
`recon/subfinder`、`scan/nuclei`、`scan/naabu`、`crawl/katana`，便于在工具商店里聚合分组。
