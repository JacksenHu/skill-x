# Agent 插件收录 SOP

> 对应 `docs/mcp-onboarding-pipeline.md`（MCP 收录）的插件版本。收录入口 `scripts/mcp_ingest.py --type plugin`，注册表与 MCP 共用 `mcp-registry.json`（`curated.entryType=plugin` 区分），对外只暴露 `reviewed.execReview=passed` 的条目。

## 定位：指路牌模式

插件条目**只存元数据与官方安装指引，本体留上游**（官方市场/一手仓库）。与 MCP 的"条目与指路牌"定位一致，区别是插件没有官方 `server.json` 生态，安装面由策展层 `curated.install` 描述：

```json
"install": {
  "method": "marketplace | command | link",
  "url": "https://marketplace.visualstudio.com/items?itemName=...",   // 可选,官方市场页
  "command": "code --install-extension <id>",                          // 可选,一键安装命令
  "clients": ["vscode", "cursor"]                                       // 可选,适用客户端
}
```

`url` 与 `command` 至少要有其一。`packages`/`remotes` 必须为空（脚本强制）。

## 收录流程

### 1. 准备 plugin.json 底稿

复用 server.json 骨架（`name`/`title`/`description`/`version`），安装面写进 `_meta.top.skillx/curated.install`。`name` 用插件的真实市场标识（如 `ms-vscode.cpptools`）或反向 DNS 命名空间。

```bash
python scripts/mcp_ingest.py --type plugin ./plugin.json [--dry-run]
```

### 2. 插件特有的机器检查（脚本自动跑，exit=2 拒绝）

- **域名白名单**：`install.url` 必须 https，且域名命中白名单——`marketplace.visualstudio.com`、`open-vsx.org`、`github.com`、`cursor.directory`、`cursor.com`、`claude.ai`、`openai.com`、`plugins.jetbrains.com`、`chromewebstore.google.com`。防"指路牌指到钓鱼站"。新增域名需人工评审后改 `scripts/mcp_ingest.py` 的 `PLUGIN_URL_DOMAINS`。
- **安装兜底**：`install.url` 与 `install.command` 至少填一个；`clients` 必须是数组。
- **空安装面**：`packages`/`remotes` 非空直接拒绝（防止把可执行面混进指路牌条目）。

### 3. 人工审查（回填 `_meta.top.skillx/curated.reviewed`）

机器跑完 `reviewed.execReview=pending`，**不会**进橱窗站和 `/v0/servers`。维护者审查：

- **市场归属**：`install.url` 是否指向该插件的官方一手市场页/官方仓库（不是第三方镜像、不是下载站）。
- **上游维护状态**：扩展发布者身份（官方组织/可信个人）、更新频率、安装量；警惕 typosquat 同名扩展。
- **权限面**：扩展声明的权限（调试器/终端/网络）与其功能是否匹配。
- 回填 `reviewed: {by, at, execReview: "passed", note}`，并补 `description-zh / category / installHint`。

### 4. 四坑检查（与 skill/MCP 同套）

| 坑 | 插件版含义 |
|---|---|
| 命名空间 | name 与官方市场标识一致，不撞名 |
| 许可证 | 看上游仓库 LICENSE；UNKNOWN 仅链接收录 |
| 供应链 | 只认官方一手市场/仓库；警惕仿冒发布者 |
| 死链 | `install.url` 定期探活（`scripts/link_check.py` 已覆盖），结果记入 `upstreamStatus` |

## 对外数据形状

- `/v0/servers`：插件条目与 MCP 同出一个端点，`curated.entryType=plugin` 供客户端过滤。
- `/v0/servers/<name>/install`：插件返回 `{kind: "link", config: {method, command, url}, clientSnippets: {}}`。
- 安装计数：`POST /api/plugin/install {"name": "<name>"}`（仅 `entryType=plugin` 且过审，其余 404），`stats.db` key 前缀 `plugin:`。
- 橱窗站：`/plugins.html` 列表页 + `/mcp/<name>.html` 详情页（与 MCP 共用模板，按类型渲染安装来源区）。

## 风险分级

插件统一默认 `medium`：安装即在本机客户端内运行第三方代码。`riskNote` 注明市场归属与凭据边界（凭据为用户本地客户端登录态，永不经过本站）。

## 收录禁忌

- 不收录/不代理与己方管理资产（lic.yueliai.top、tqai.xyz 及其子域）相关的任何探测类插件条目。
- 不收指向第三方下载站/镜像站的指路牌（白名单已强制，人工复核仍是硬要求）。
- 不收 `reviewed.execReview != passed` 的条目进任何对外产物。
- 暂不开放开发者自助提交；提交入口作为后续独立迭代。
