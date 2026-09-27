# Conventions — 项目约定

## 技能(SKILL.md)

- frontmatter 只写基础字段:`name` / `description`(英文)/ `license`;中文与分类写在 `metadata`(`name-zh` / `description-zh` / `category`)。
- **禁用** allowed-tools、context: fork、Hooks。
- 中文名为页面主标题,英文名为技术标识(等宽展示)。
- 自带工具放 `skills/<name>/scripts/`,**纯标准库**;确需第三方时用 try/except 降级并在 help 中提示安装。

## 页面与样式

- 严格 CSP:零内联 style、零内联脚本;动态样式用 class。
- 配色 token 集中在 CSS 的 `:root`;分类色用 `.cat-<key>` 设置 `--cat` 变量。
- 双语:可切换文本用 `data-zh` / `data-en`(输入框类加 `data-attr="placeholder"`);默认中文,localStorage 记 `sx-lang`。
- 动效:只保留必要的一次性浮现与交互反馈;`prefers-reduced-motion` 时全部静止。
- 不写中点点拼接的 meta,不在链接后加箭头。

## 数据文件

- `external.json` 是收录事实(由 ingest.py 生成,勿手改);翻译/分类/精选等**人工增补**放独立文件(i18n-ext.json、curation.json),重跑 ingest 不会覆盖。
- `site-data.json` / `tools.json` / `audit-report.json` 是**对外数据接口**(机器可读),字段名变动视为破坏性变更。

## 提交与部署

- 提交后立即 push(以 GitHub 为唯一真相源)。
- 部署命令:`BT_API_SK=... python deploy/sync.py`。
- `api_sk` 只在环境变量里,不写文件、不进 git、不进 memory。

## 命名

- 自研页 `skills/own-<name>.html`;收录页 `skills/ext-<ns-slug>--<name>.html`;套件页 `suites/<ns-slug>.html`;导图 `mindmaps/<skill>.svg`、套件导图 `mindmaps/suite-<ns-slug>.svg`。

## 上下文与协作(devctx)

- 每个会话/需求:开始前先读 `.ai-dev/START_HERE.md` + `.ai-dev/HANDOFF.md`;需求闭环(或切换工具/模型)时,必须把本轮压缩回写 `HANDOFF.md`——只留目标、可验证结果、有序下一步、新约束/决策、踩坑;不贴对话原文与大段代码/日志。
- 长期规则写进 L2 文档(本文件 / architecture / project-brief / lessons);HANDOFF 只保留活跃工作记忆,超约 120 行先归档。
- 增删/移动源码文件后同步刷新 `code-index.md`;项目文件即共享记忆,提交后立即 push。
- 凭据(api_sk / PAT / token)只走会话环境变量:不落盘、不入库、不进 `.ai-dev`/memory。
