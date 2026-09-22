# SkillHub

面向所有 AI Agent 的安全研究与逆向工程技能库(红队/白帽方向),遵循 [Agent Skills 开放规范](https://agentskills.io)。

- **私有分发**:本仓库为私有仓库,授权用户通过 `GITHUB_TOKEN` 安装
- **全 Agent 兼容**:skill 只使用规范基础字段,可被 Claude Code、Codex、Cursor、Copilot 等 80+ agent 加载
- **橱窗站**:技能介绍与外部套件收录见 EdgeOne 橱窗站(建设中)

## 安装(授权用户)

```bash
# 列出库内全部 skill
npx skills add <owner>/skillhub --list

# 安装指定 skill(自动检测本机 agent:claude-code / cursor / codex ...)
npx skills add <owner>/skillhub --skill verification-run-hygiene

# 安装到指定 agent
npx skills add <owner>/skillhub --skill verification-run-hygiene -a claude-code
```

凭据配置(任一即可):`GITHUB_TOKEN` / `GH_TOKEN` 环境变量、`gh auth login`、或已配置的 git/SSH 凭据。Token 仅需 `Contents: read` 权限。

## 目录结构

```
skills/<skill-name>/     # 技能(每个含 SKILL.md,可选 scripts/ references/ assets/)
docs/                    # 编写规范与开发文档
scripts/                 # 仓库工具(校验等)
.claude-plugin/          # Claude Code 插件市场清单
.codex-plugin/           # Codex 插件清单
.github/workflows/       # CI:校验与发布
```

## 收录中的技能

| 技能 | 简介 |
|---|---|
| [verification-run-hygiene](skills/verification-run-hygiene/SKILL.md) | 跑验证/回归时保住结果可信度的操作纪律:真回归与假红的判别、18 条硬纪律 |

## 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [《SKILL.md 编写规范》](docs/skill-authoring-guide.md)。
