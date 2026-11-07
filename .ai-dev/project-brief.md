# Project Brief — 项目概况

## 一句话定位

Skill X(skillhub)是面向所有 AI Agent 的**安全研究与逆向工程**技能注册中心:技能源托管 GitHub 公开仓库,公开站点 https://skillx.yueliai.top 负责展示、检索、推荐、安全审计与下载统计。

## 用户与核心场景

- **使用者**:安全研究员 / 逆向工程师 / 渗透测试工程师。用 `npx skills add` 装技能给自己的 Agent;核心路径"找技能 → 判断可信 → 复制命令"。
- **维护者**:老胡(决策)+ jacksen(执行)。核心路径"收录外链 → 四坑检查 → 构建 → 一键部署"。

## 技术栈(版本真实)

| 层 | 选型 | 版本 | 备注 |
| -- | -- | -- | -- |
| 语言 | Python | 3.13(构建)/ 服务器自带 python3 | **零第三方依赖,仅标准库** |
| 技能工具 | Python 标准库 | — | 唯一可选依赖 pyyaml(openapi_inventory,try/except 降级) |
| 站点 | 静态站 + 生成器 | showcase/build_index.py v3 | 增量构建(`.build-manifest.json`),产物 showcase/dist/ |
| 后端 | ThreadingHTTPServer | api/server.py | 仅听 127.0.0.1:8787,nginx 反代;内置 mtime 热重载 |
| 存储 | sqlite3 | api/stats.db | 计数表 counts(skill, n) |
| 部署 | 宝塔面板 HTTP API | deploy/bt_deploy.py / sync.py | 签名 md5(request_time + md5(api_sk));纯净重放 |
| CI | GitHub Actions | .github/workflows/audit.yml | 每日 03:00 UTC 刷新审计报告 + 漂移检测 |
| 服务器 | 腾讯云香港 124.156.167.163 | nginx + 宝塔 | 站点 id=2,目录 /www/wwwroot/skillx.yueliai.top |

## 顶层目录结构

- `skills/` — 本站技能源(每目录一个 SKILL.md + 可选 scripts/)
- `showcase/` — 生成器与数据:build_index.py / svg_map.py / apidocs.py / i18n-*.json / curation.json / mindmaps/ / dist/
- `api/` — 后端:server.py、registry.json(/dl/ 白名单)、cache/、stats.db
- `deploy/` — bt_deploy.py、sync.py、nginx/(vhost 与备份)
- `scripts/` — validate.py、ingest.py、link_check.py、audit_skill.py
- `docs/` — 接入 SOP、验收测试、宝塔 API 边界笔记
- `external.json` — 收录套件清单(命名空间/许可证/可执行面/探活)

## 常用命令(仓库根 skillhub/)

```text
python showcase/build_index.py                 # 构建(增量)
BT_API_SK=<sk> python deploy/sync.py           # 构建+部署;--skip-build 只部署;--api 连后端
python scripts/audit_skill.py                  # 安全审计;--check 漂移检测(CI 用)
python scripts/validate.py                     # 本站 SKILL.md 合规校验
python scripts/ingest.py <url>                 # 收录套件
python scripts/link_check.py                   # 上游死链探活
```

## 环境与外部依赖

- 环境变量 `BT_API_SK`(宝塔 api_sk,**会话内使用,不落盘不入库**)。
- 外部服务:宝塔面板 API(部署)、GitHub(源码/上游)、api.github.com(构建期拉 Star/Fork,24h 缓存)。
- 密钥:宝塔面板 → 设置 → API 接口 生成;仓库公开,分发不需要 PAT。
- **宝塔 API 有 IP 白名单**;本机出口 IP 是动态池,建议白名单填段(如 219.132.*)。

## 当前里程碑 / 边界

- 已落地:v2 五阶段(建站 / 双语分类套件中心 / 统计后端 / 导图+API 文档 / CSP+一键部署)+ 设计 v2(深色控制台、首页融合推荐器、可交互导图)。
- 明确不做:服务器构建机(老胡 2026-09-24 决定)、付费服务、前端框架与第三方依赖。
