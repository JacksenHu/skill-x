# MCP server 收录 SOP

> 对应 `docs/onboarding-pipeline.md`（skill 收录）的 MCP 版本。收录入口 `scripts/mcp_ingest.py`，注册表 `mcp-registry.json`，对外只暴露 `reviewed.execReview=passed` 的条目。

## 与 skill 收录的两点本质差异

1. **存的是"条目与指路牌"，不是代码本体**。MCP server 的代码在 npm/pypi/nuget/OCI 或别人运行的远程 URL 上；`mcp-registry.json` 只存官方 `server.json` 元数据 + `_meta.top.skillx/curated` 策展层。无本体可镜像（远程型），或本体走公共包仓库（本地型）。
2. **风险模型倒置**。skill 是静态文本，供应链风险在"可执行脚本面"；MCP stdio 本地包是"安装即在用户机器上跑第三方进程"，远程型则是"把用户凭据连到别人服务器"。所以 MCP 收录多了两条硬检查：**传输类型安全**与**密钥声明完整**。

## 收录流程

### 1. 获取 server.json 底稿

优先从官方 Registry 拉取（已是标准格式，省一次手写）：

```bash
python scripts/mcp_ingest.py --registry-name <ns/name> [--version <ver>] [--dry-run]
```

或本地提供一份手写/作者提交的 server.json：

```bash
python scripts/mcp_ingest.py ./server.json [--out mcp-registry.json] [--dry-run]
```

脚本会做结构校验（name 反向 DNS 格式、packages/remotes 二选一必填、registryType/transport/url 合法、远程必须 https）。

### 2. MCP 特有的两项机器检查（脚本自动跑）

- **传输类型**：`stdio` 本地包 → 标 `riskLevel=high`，提示"安装即本机执行"；纯 `streamable-http`/`sse` 远程 → `low`。
- **密钥声明**：`environmentVariables[].isSecret` 必须标对。凡变量名命中 `KEY/TOKEN/SECRET/PASSWORD` 却没标 `isSecret=true` 的，脚本以 exit=3 **拒绝收录**，直到作者修正。

### 3. 人工审查（回填 `_meta.top.skillx/curated.reviewed`）

机器跑完 `reviewed.execReview=pending`，**不会**进橱窗站和 `/v0/servers`。维护者审查后回填：

- `stdio` 包：审查上游仓库维护状态、是否 typosquat、有无 postinstall/混淆/`curl|sh`。相当于 skill 收录的"可执行面逐个人工审查"。
- 远程型：确认 URL 归属、是否官方一手服务；认证头/env 属用户私域配置，**绝不写进 registry 或橱窗站**。
- 回填 `reviewed: {by, at, execReview: "passed", note}`，并补 `description-zh / category / installHint`。

### 4. 四坑检查（与 skill 同套）

| 坑 | MCP 版含义 |
|---|---|
| 命名空间 | name 反向 DNS 且与官方 Registry 一致，不撞名 |
| 许可证 | 本地包看上游仓库 LICENSE；远程服务看其服务条款，UNKNOWN 仅链接收录 |
| 供应链 | stdio 包逐个审查；脚本面红线（未声明外联/凭证读取/混淆）同样适用 |
| 死链 | 远程 URL 与包坐标定期探活，结果记入 `upstreamStatus` |

## 对外数据形状

`/v0/servers` 返回与官方 Registry 兼容的响应（游标分页），每个条目：

- `server`：剥离 `_meta` 后的纯官方 server.json
- `_meta.top.skillx/curated`：中文描述、分类、kind(local/remote)、riskLevel、installHint
- `_meta.io.modelcontextprotocol.registry/official`：status/publishedAt/isLatest

安装/连接计数走 `POST /api/mcp/install {"name":"<ns/name>"}`，复用现有 `stats.db`（key 前缀 `mcp:`）。

## 收录禁忌

- 不收录/不代理与己方管理资产（lic.yueliai.top、tqai.xyz 及其子域）相关的任何探测类 MCP 条目。
- 不收未标 `isSecret` 的密钥声明（脚本已强制）。
- 不收 `reviewed.execReview != passed` 的条目进任何对外产物。
