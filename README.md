# Skill X

面向所有 AI Agent 的安全研究与逆向工程技能库(红队/白帽方向),遵循 [Agent Skills 开放规范](https://agentskills.io)。

- **私有分发**:本仓库为私有仓库,授权用户通过 `GITHUB_TOKEN` 安装
- **全 Agent 兼容**:skill 只使用规范基础字段,可被 Claude Code、Codex、Cursor、Copilot 等 80+ agent 加载
- **橱窗站**:技能介绍与外部套件收录,多页+搜索 → **https://3f3301ac5aa14f998efefa8913125d01.sg.agentos-app.run**(长期固定链接;内容更新后重新发布即刷新,链接不变)
- **社区收录**:已收录 2 个外部套件共 34 个 skill(见 `external.json`,收录管线见 [接入 SOP](docs/onboarding-pipeline.md))
- **第三方应用接入**:MCP 服务与 Agent 插件统一条目注册表(`mcp-registry.json`,官方 server.json 标准 + `entryType` 区分);插件指路牌只指向官方一手市场(见 [插件收录 SOP](docs/plugin-onboarding-pipeline.md))
- **专家团**:带人设的编排层(自研 + 收录双轨),成员可跨 自研/收录/MCP;安装走《安装契约文档》与 `/v0/packs` API,Agent 读文档即会装(见 [专家团收录 SOP](docs/pack-onboarding-pipeline.md))

## 安装(授权用户)

```bash
# 列出库内全部 skill
GITHUB_TOKEN=<PAT> npx skills add JacksenHu/skill-x --list

# 安装指定 skill(自动检测本机 agent:claude-code / cursor / codex ...)
GITHUB_TOKEN=<PAT> npx skills add JacksenHu/skill-x --skill verification-run-hygiene

# 安装到指定 agent
GITHUB_TOKEN=<PAT> npx skills add JacksenHu/skill-x --skill verification-run-hygiene -a claude-code
```

凭据配置(任一即可):`GITHUB_TOKEN` / `GH_TOKEN` 环境变量、`gh auth login`、或已配置的 git/SSH 凭据。Token 仅需 `Contents: read` 权限。详见 [授权与安装管理](docs/access-management.md)。

## 目录结构

```
skills/<skill-name>/     # 自研技能(每个含 SKILL.md,可选 scripts/ references/ assets/)
docs/                    # 编写规范、接入 SOP(skill/MCP/插件)、授权管理
scripts/                 # 仓库工具(validate / ingest / mcp_ingest / link_check)
showcase/                # 橱窗站构建器与产物(build_index.py -> dist/)
external.json            # 社区收录套件登记(命名空间/许可证/审查/探活状态)
mcp-registry.json        # 统一条目注册表:MCP server + Agent 插件(entryType 区分)
packs.json               # 专家团注册表(人设/成员 ref/编排剧本 content,pack_ingest 维护)
.claude-plugin/          # Claude Code 插件市场清单
.codex-plugin/           # Codex 插件清单
.github/workflows/       # CI:校验、发布、每日死链探活
```

## 收录中的技能

| 技能 | 简介 |
|---|---|
| [verification-run-hygiene](skills/verification-run-hygiene/SKILL.md) | 跑验证/回归时保住结果可信度的操作纪律:真回归与假红的判别、18 条硬纪律 |
| [malware-analysis](skills/malware-analysis/SKILL.md) | 恶意样本分析:脱壳、配置提取、C2 协议解码、IOC/YARA/Sigma 产出 |
| [memory-forensics](skills/memory-forensics/SKILL.md) | 跨平台内存取证:指针链、签名扫描、结构重建、安全补丁与回滚 |
| [binary-reverse-engineering](skills/binary-reverse-engineering/SKILL.md) | 深度逆向:PE/ELF/Mach-O/固件/.NET/IL2CPP、脱壳、协议重建 |
| [pentest-methodology](skills/pentest-methodology/SKILL.md) | 证据驱动渗透:Web/API/OAuth/云原生/AD、请求矩阵、越权契约、复测标准 |

## 社区收录套件

| 套件 | skill 数 | 许可证 | 安装 |
|---|---|---|---|
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 25 | MIT | `npx skills add addyosmani/agent-skills --skill <name>` |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 9 | 未确认(仅链接收录) | `npx skills add vercel-labs/agent-skills --skill <name>` |

收录均通过四坑检查(命名空间/许可证/供应链/死链),明细见 `external.json`。

## 专家团(Expert Packs)

| 专家团 | 人设 | 成员 | 安装 |
|---|---|---|---|
| [深潜 Abyss](skills/pack-abyss-deep-reverse/SKILL.md) | 二进制解剖师 | binary-reverse-engineering + verification-run-hygiene | `npx skills add JacksenHu/skill-x --skill pack-abyss-deep-reverse` |
| [裂空 Rift](skills/pack-rift-pentest/SKILL.md) | 证据驱动渗透主理人 | pentest-methodology + verification-run-hygiene + security-and-hardening | `npx skills add JacksenHu/skill-x --skill pack-rift-pentest` |
| [溯源 Trace](skills/pack-trace-malware/SKILL.md) | 样本溯源分析师 | malware-analysis + memory-forensics | `npx skills add JacksenHu/skill-x --skill pack-trace-malware` |

第三方应用/Agent 接入:读《安装契约文档》 <https://skillx.yueliai.top/install/pack-install.md>,
或调 `GET /v0/packs` / `GET /v0/packs/<slug>` 取成员安装描述符。

## 兼容性

- **实测通过**:CodeBuddy(skills CLI 安装/卸载/环境还原全链路,2026-09-22)
- **官方兼容**:遵循 Agent Skills 开放规范,frontmatter 仅用规范基础字段(name/description/license/compatibility/metadata),未使用 `allowed-tools`/`context: fork`/Hooks 等兼容性受限特性;经 vercel-labs/skills CLI 可安装到其官方目录映射覆盖的 80+ agent(Claude Code、Codex、Cursor、Copilot、Gemini CLI、OpenCode 等)
- **网络说明**:github.com 主站受限的网络请用 SSH 形式安装,见 [授权与安装管理](docs/access-management.md)

## 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [《SKILL.md 编写规范》](docs/skill-authoring-guide.md)。
