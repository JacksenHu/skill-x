# MCP 安装连接市场调研

> 调研时间：2026-09-28。结论先行：**不要从零设计格式，直接复用 MCP 官方 Registry 的 `server.json` 规范 + 参考官方 Registry / mcpm / Cline Marketplace 三个开源项目的三种模式**，把它们映射到 Skill X 现有的 registry.json + server.py + 橱窗站架构上。

## 一、要建的东西是什么

用户要的是「应用程序里的 MCP 安装连接市场」，本质上有四个功能面：

1. **发现（Discovery）**：列出可用的 MCP server（名称、描述、作者、版本、分类、安全标注）
2. **安装（Install）**：把 MCP server 的启动配置写进目标 agent / 应用的配置文件（如 `.mcp.json`、`claude_desktop_config.json`、`~/.codex/config.toml`）
3. **连接（Connect）**：区分本地 stdio 进程型（要装包、起进程）与远程 HTTP/SSE 型（只填 URL 和凭据）
4. **管理（Manage）**：启用/禁用、更新版本、卸载、密钥（env var）托管

Skill X 已有 1（showcase 橱窗站）、半个 2（skills CLI 安装到 80+ agent 目录）、3 的雏形（api/server.py 的注册表 + 下载代理 + 统计）。MCP 市场是在同一套骨架上增加「MCP server 这类新条目类型」，而不是另起炉灶。

## 二、必须对齐的开放标准：官方 MCP Registry + server.json

### 2.1 官方 Registry（modelcontextprotocol/registry）

- 定位：**「MCP server 的应用商店」社区注册表**，2025-09 上线 preview，API 冻结在 v0.1，7.2k+ stars。
- 实时 API：`https://registry.modelcontextprotocol.io/v0/servers?limit=N`，游标分页（`nextCursor`）。
- 架构：Go 服务 + PostgreSQL，可自托管（`make dev-compose`），支持从生产 API 种子数据导入。
- 核心思想：**唯一事实源（single source of truth）**。官方 Registry 是上游，各家市场（VS Code、Cursor、Cline…）是下游镜像/聚合器。Skill X 应该做一个「下游市场」，同步官方数据并叠加自己的策展和安全标注。

来源：https://github.com/modelcontextprotocol/registry（README.md、docs/design/ecosystem-vision.md）

### 2.2 server.json 格式（关键交付物）

每个 MCP server 用一份 `server.json` 描述，schema 地址：
`https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json`

核心字段（已核实）：

| 字段 | 作用 | 对应 Skill X 市场能力 |
|---|---|---|
| `name` | 反向 DNS 命名空间，如 `io.github.user/server` | 与现有 `namespace/skill` 命名一致 |
| `description` / `title` | 展示 | 橱窗站卡片 |
| `version` | semver | 版本管理与更新检测 |
| `packages[]` | **本地安装型**：`registryType`(npm/pypi/nuget/oci/mcpb) + `identifier` + `transport`(stdio) + `runtimeArguments` / `packageArguments` / `environmentVariables` | 安装器据此生成 `command/args/env` |
| `remotes[]` | **远程连接型**：`type`(streamable-http / sse) + `url` + `headers` | 连接管理器据此填 URL 和认证头 |
| `environmentVariables[].isRequired/isSecret` | 声明需要用户填的密钥 | 市场 UI 提示填写并安全存储 |
| `_meta` | 发行方自定义元数据（反向 DNS 命名空间） | Skill X 可塞安全分级、中文描述、下载量 |

**重要结论**：市场条目文件格式 = `server.json`，不要自造。这样条目同时可被官方 Registry、MCP 客户端、Skill X 三方消费。

来源：https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/generic-server-json.md

## 三、可参考的开源项目（三种模式）

### 3.1 modelcontextprotocol/registry —— 标准制定者

- **学什么**：`server.json` schema、`/v0/servers` REST API 形状（游标分页、`_meta.io.modelcontextprotocol.registry/official` 状态字段）、发布校验流程（命名空间所有权验证）。
- **怎么用**：Skill X 的 `api/registry.json` 升级为存 `server.json` 数组（或加一个 `mcp-registry.json`），`server.py` 增加 `/v0/servers` 兼容端点，就能被任何支持官方 Registry 的 MCP 客户端直接消费。
- 注意：官方 API 冻结在 v0.1，v1 仍在开发，跟着 schema 日期版本（2025-12-11）走即可。

### 3.2 pathintegral-institute/mcpm.sh（mcpm）—— 跨客户端安装器

- 1k+ stars，Python CLI，口号「CLI MCP package manager & registry for all platforms and all clients」。
- **学什么**：
  - **客户端探测**：自动识别本机装了哪些 agent（Claude Desktop / Cursor / Windsurf / VS Code…），与 Skill X `npx skills add` 的自动检测思路完全一致，可复用同一套探测代码。
  - **配置写入器**：把 server.json 翻译成各家客户端的配置格式（每家的 JSON/TOML 结构、配置文件路径都不同）。这是「安装」功能的真正工作量所在。
  - **Router / Profile**：把多个 MCP server 聚合在一个本地 router 后面，按 profile 分组启用——对应「管理」功能的进阶形态。
- **怎么用**：可以把 mcpm 当作 Skill X 安装器的后端，或抄它的客户端适配层。

来源：https://github.com/pathintegral-institute/mcpm.sh

### 3.3 cline/mcp-marketplace —— 策展提交流

- 787 stars，Cline 编辑器的官方 MCP 市场仓库。
- **学什么**：**提交-审核-收录管线**。贡献者开 issue 提交（仓库 URL + 400×400 PNG 图标 + 推荐理由），团队审核后入库，客户端一键安装时让 agent 自主完成 clone/构建/配置（靠 README 或 llms-install.md）。
- **怎么用**：直接映射到 Skill X 现有的 `docs/onboarding-pipeline.md` 四坑检查（命名空间 / 许可证 / 供应链 / 死链）。把「skill 收录 SOP」复制一份改成「MCP server 收录 SOP」，外加 MCP 特有的两条检查：**传输类型安全**（stdio 本地进程要标注权限风险）和 **env 密钥声明完整**（`isSecret` 必须标对）。
- 注意：Cline 模式靠 agent 现场装，省去构建托管，但安装成功率取决于 README 质量；Skill X 已有 `api/server.py` 白名单代理 + 缓存，可以做得更确定（预打包 tar.gz，类似现有 `/dl/<ns>/<skill>.tar.gz`）。

来源：https://github.com/cline/mcp-marketplace

### 3.4 反面教材：mcp-get/community-servers

- 68 stars，已 archived（仓库自述不再维护）。
- **教训**：纯社区提交、缺乏与官方标准对齐的注册表会死掉。对齐官方 server.json 是避免重蹈覆辙的关键。

来源：https://github.com/mcp-get/community-servers

## 四、落地到 Skill X 的架构建议

```
skillhub/
├── mcp-registry.json            # 新增:MCP server 条目(server.json 数组 + Skill X _meta)
├── api/
│   └── server.py                # 扩展:+ GET /v0/servers(官方兼容) + /dl/mcp/<ns>/<name>.tar.gz
├── showcase/                    # 扩展:橱窗站加 "MCP 服务" tab,数据源并入 site-data.json
├── scripts/
│   └── mcp_ingest.py            # 新增:收录管线(校验 server.json → 四坑检查 → 写 mcp-registry.json)
└── docs/
    └── mcp-onboarding-pipeline.md  # 新增:MCP 收录 SOP
```

分三步走：

1. **数据层（先行）**：定义 `mcp-registry.json`，每条 = 官方 `server.json` + `_meta.top.skillx/`（中文描述、分类、安全分级、下载量）。写 `scripts/mcp_ingest.py` 做 schema 校验 + 收录检查。
2. **API 层**：`api/server.py` 增加 `GET /v0/servers`（返回官方兼容格式，外部客户端可直接接）与 `GET /v0/servers/{name}/versions/{version}`；本地包走现有 `/dl/` 白名单代理模式，远程 server 只做登记不做代理。
3. **消费层**：橱窗站加 MCP tab；安装侧复用 skills CLI 的 agent 探测，把 server.json 的 `packages[0]` 翻译成目标客户端配置（stdio: `command`/`args`/`env`；remote: `url`/`headers`），或干脆输出 `mcpm install` / `claude mcp add` 命令让用户一键执行。

## 五、安全与风控要点（对应 Skill X 的红队定位）

- **stdio 本地包 = 执行用户机器上的任意代码**，收录时必须过供应链检查（仓库 star/维护状态、package 是否 typosquat、是否有 postinstall 脚本），并在市场上显著标注风险等级。
- **远程 server 的 URL 与认证头**属于连接配置，`isSecret` 的 env/headers 绝不能写进 registry 或橱窗站，只在用户本地配置时填入。
- 保持现有 `server.py` 的纪律：仅监听 127.0.0.1、白名单代理、单 IP 限速、参数化 SQL——MCP 端点同样适用。
- 绝不收录/代理与己方管理资产（lic.yueliai.top、tqai.xyz 及其子域）相关的任何探测类工具条目。

## 六、参考链接汇总

| 项目 | 地址 | 学到的模式 |
|---|---|---|
| 官方 MCP Registry | https://github.com/modelcontextprotocol/registry | server.json 标准 + /v0/servers API |
| server.json schema | https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json | 条目文件格式 |
| mcpm | https://github.com/pathintegral-institute/mcpm.sh | 跨客户端安装器 + router/profile |
| Cline MCP Marketplace | https://github.com/cline/mcp-marketplace | 提交-审核收录管线 |
| mcp-get（已归档） | https://github.com/mcp-get/community-servers | 不对齐标准的失败教训 |
