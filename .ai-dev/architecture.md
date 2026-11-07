# Architecture — 架构与"改什么去哪改"

## 数据流

```text
skills/*/SKILL.md ─┐
external.json ─────┼─→ build_index.py ─→ showcase/dist/ ──(sync.py 纯净重放)──→ 站点目录
showcase/*.json ───┘        │                                    nginx(静态)
(双语增补/精选白名单/导图源)  └─→ mindmaps/*.svg(内联进详情页)      │
                                                                 ├─ /api/* ─→ 127.0.0.1:8787(api/server.py)
audit-report.json ───────────────────────────────────────────────┘
```

## 模块分区

| 模块 | 职责 | 关键文件 |
| -- | -- | -- |
| 技能源 | 本站技能(方法论 + 可选 scripts 工具) | skills/<name>/SKILL.md、skills/<name>/scripts/*.py |
| 生成器 | 渲染全部页面/导图/数据接口,增量构建 | showcase/build_index.py |
| 导图 | 受限 YAML → SVG(树形布局、分支配色) | showcase/svg_map.py、showcase/mindmaps/*.yaml |
| 文档提取 | AST 提取 argparse 参数与 docstring | showcase/apidocs.py |
| 审计 | 8 项静态检查(AST 级),产等级 A–D | scripts/audit_skill.py → showcase/audit/audit-report.json |
| 收录 | 拉取外部套件、四坑检查、写 external.json | scripts/ingest.py、scripts/link_check.py、showcase/curation.json |
| 部署 | 宝塔 API 封装 + 一键构建部署 | deploy/bt_deploy.py、deploy/sync.py、deploy/nginx/ |
| 后端 | 计数、推荐、代理下载 | api/server.py、api/registry.json |

## 改什么 → 去哪改(速查)

| 需求 | 改这里 |
| -- | -- |
| 页面文案 / 版式 / 配色 / 动效 | showcase/build_index.py(CSS 常量 + 各 render_* 函数) |
| 新增/修改技能 | skills/<name>/SKILL.md(双语与分类写在 frontmatter 的 metadata) |
| 技能工具参数文档 | 改 scripts/*.py 的 argparse 即自动同步(apidocs.py 提取) |
| 技能思维导图 | showcase/mindmaps/<skill>.yaml → 重建 |
| 工具中文摘要 | showcase/i18n-tools.json |
| 收录技能中文翻译与分类 | showcase/i18n-ext.json |
| 收录/下架某个技能 | showcase/curation.json(include 白名单;空数组=整套件不展示) |
| 新增分类 | build_index.py 的 CATEGORIES + CSS 的 `.cat-<key>` 与 `--c-<key>` |
| 后端接口 | api/server.py(改完 sync.py --api 上传,30s 内热重载生效) |
| /dl/ 代理白名单 | api/registry.json |
| 站点 nginx/安全头 | deploy/nginx/skillx.yueliai.top.conf → sync.py 部署并 reload |
| CI 任务 | .github/workflows/ |

## 关键约束(改前必读)

1. **严格 CSP**:页面零内联 `style`;分类色等动态样式一律用 class(`.cat-<key>{--cat:...}`)。
2. **增量构建**:产物哈希写在 showcase/.build-manifest.json;改了 svg_map.py / apidocs.py 之类生成器代码,要把它的内容纳入 key,否则不会重渲染。
3. **部署用纯净重放**(删站目录→重建→解压):tar 解压不删旧文件,否则下架页会残留。
4. **技能规范**:只用 Agent Skills 基础 frontmatter(name/description/license/metadata);禁用 allowed-tools、context: fork、Hooks。
5. SKILL.md 正文**绝不进任何页面产物**(构建期有泄露断言)。
