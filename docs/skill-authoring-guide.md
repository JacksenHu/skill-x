# SKILL.md 编写规范

本库所有 skill 遵循 [Agent Skills 开放规范](https://agentskills.io/specification),并以"**一个 skill 通吃所有 agent**"为硬目标。本规范是贡献的唯一标准。

## 1. 目录结构

```
skills/<skill-name>/
├── SKILL.md          # 必需:frontmatter(元数据)+ Markdown 正文(指令)
├── scripts/          # 可选:可执行脚本(须自包含或写明依赖)
├── references/       # 可选:按需加载的详细文档(每文件聚焦一个主题)
└── assets/           # 可选:模板/图片/数据
```

- `<skill-name>` 必须与 frontmatter 的 `name` 完全一致:小写字母、数字、连字符;不以连字符开头/结尾;无连续连字符;≤64 字符。
- 类目布局允许 `skills/<category>/<skill-name>/`(最多三层)。

## 2. frontmatter 白名单(跨 agent 兼容性的根)

| 字段 | 状态 | 要求 |
|---|---|---|
| `name` | **必用** | 与目录名一致 |
| `description` | **必用** | ≤1024 字符,见第 3 节 |
| `license` | 可用 | 短名(如 `MIT`)或许可证文件名 |
| `compatibility` | 可用 | ≤500 字符,仅在有环境要求时写 |
| `metadata` | 可用 | 任意键值;非标准字段(如 `triggers`)一律挪到这里 |
| `allowed-tools` | **禁用** | Kiro CLI / Zencoder 不支持 |
| `context: fork` | **禁用** | 仅 Claude Code 支持 |
| Hooks | **禁用** | 仅 Claude Code / Cline 支持 |
| 其他自定义顶层字段 | **禁用** | 挪入 `metadata` |

理由:agent 靠 frontmatter 做发现与激活决策,任何字段级不兼容都会让 skill 在部分 agent 上静默失效。

## 3. description 写法(唯一影响所有 agent 效果的字段)

公式:**做什么 + 何时用 + 触发关键词**,三段齐全。

```yaml
# 好
description: 抽取 PDF 文本、表格与表单填充。处理 PDF 文档、表单或用户提到 PDF/抽取/合并时使用。

# 差
description: 帮助处理 PDF。
```

中英文关键词都列(用户可能用任一种语言描述任务);1024 字符内尽量写满真实触发场景。

## 4. 正文

- ≤500 行;超出的详细内容拆到 `references/`(每文件一个主题,正文用相对路径引用,如 `references/REFERENCE.md`)。
- 推荐结构:解决什么问题 → 硬规则/流程(编号)→ 真实案例佐证 → 反模式清单 → 输出纪律。
- 引用本 skill 内文件用**相对路径**,且只从 SKILL.md 出发一级引用。
- **禁止写入**:API key、个人路径、私有基础设施地址、"绕过模型安全策略"类对抗性指令——这类内容一律不进库。

## 5. 渐进式披露自查

1. 只看 `name`+`description`(≈100 token):能否让 agent 正确决定激活?
2. 激活后读正文(≤5000 token):能否独立完成典型任务?
3. `references/` 是否只在确有必要时才被需要?

## 6. 提交前验收清单

- [ ] `python scripts/validate.py` 通过
- [ ] `npx skills add ./ --list` 能列出本 skill
- [ ] description 三段公式齐全,无禁用字段
- [ ] 正文 ≤500 行,references 一级引用
- [ ] 无密钥/个人路径/私有地址
- [ ] 完成一次对照实验(见 CONTRIBUTING.md)并在 PR 中粘贴结果
