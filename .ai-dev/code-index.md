# Code Index — 代码地图（自动生成，请勿手改）

- 生成时间：2026-09-27 14:55
- 源码文件：68 个，合计约 5126 行
- 用法：先在本文件定位目标，再精读对应源码；不要全仓遍历。增删/移动文件后用 build_index.py 重建。

## 目录结构

```text
skillhub/
.claude-plugin/
.codex-plugin/
.github/
api/
deploy/
docs/
scripts/
showcase/
skills/
  workflows/
  nginx/
  acceptance/
  audit/
  mindmaps/
  binary-reverse-engineering/
  malware-analysis/
  memory-forensics/
  pentest-methodology/
  verification-run-hygiene/
    references/
    scripts/
    references/
    scripts/
    references/
    scripts/
    references/
    scripts/
    references/
```

## 文件清单（按目录分组）

### (root)

- `CHANGELOG.md` (22 行) — Changelog  <!-- CHANGELOG.md -->
- `CONTRIBUTING.md` (17 行) — 参与贡献  <!-- CONTRIBUTING.md -->
- `README.md` (65 行) — Skill X  <!-- README.md -->
### .github

- `PULL_REQUEST_TEMPLATE.md` (33 行) — 变更说明  <!-- .github/PULL_REQUEST_TEMPLATE.md -->
### .github/workflows

- `audit.yml` (32 行)  <!-- .github/workflows/audit.yml -->
- `link-check.yml` (24 行)  <!-- .github/workflows/link-check.yml -->
- `publish.yml` (23 行)  <!-- .github/workflows/publish.yml -->
- `validate.yml` (17 行)  <!-- .github/workflows/validate.yml -->
### api

- `server.py` (310 行) — Skill X 统计与下载代理后端(零第三方依赖,Python 3.8+ 标准库)。  <!-- api/server.py -->
### deploy

- `bt_deploy.py` (170 行) — 宝塔面板 API 部署工具(Skill X 专用)。  <!-- deploy/bt_deploy.py -->
- `MANUAL_SETUP.md` (39 行) — 手动建站回退指引(api_sk 不可用时)  <!-- deploy/MANUAL_SETUP.md -->
- `sync.py` (74 行) — Skill X 一键构建 + 部署(本地构建 → 宝塔 API 上传 → 站点生效)。  <!-- deploy/sync.py -->
### docs

- `acceptance-testing.md` (44 行) — 对照验收 SOP:装了 ≠ 生效  <!-- docs/acceptance-testing.md -->
- `access-management.md` (74 行) — 授权与安装管理  <!-- docs/access-management.md -->
- `baota-api-notes.md` (49 行) — 腾讯云专享版宝塔 API 能力边界与变通(实操记录)  <!-- docs/baota-api-notes.md -->
- `onboarding-pipeline.md` (67 行) — 套件 / Skill 接入管线(维护 SOP)  <!-- docs/onboarding-pipeline.md -->
- `skill-authoring-guide.md` (68 行) — SKILL.md 编写规范  <!-- docs/skill-authoring-guide.md -->
### docs/acceptance

- `pentest-methodology-demo.md` (39 行) — 对照实验实录:pentest-methodology  <!-- docs/acceptance/pentest-methodology-demo.md -->
- `verification-run-hygiene-demo.md` (45 行) — 对照实验实录:verification-run-hygiene  <!-- docs/acceptance/verification-run-hygiene-demo.md -->
### scripts

- `audit_skill.py` (258 行) — 技能安全审计(自动任务,纯标准库静态扫描)。  <!-- scripts/audit_skill.py -->
- `ingest.py` (314 行) — Skill X 套件收录器(docs/onboarding-pipeline.md 的机器化实现,纯标准库)。  <!-- scripts/ingest.py -->
- `link_check.py` (76 行) — upstream 死链探活(docs/onboarding-pipeline.md §2.4,纯标准库)。  <!-- scripts/link_check.py -->
- `validate.py` (113 行) — SkillHub SKILL.md 规范校验(零第三方依赖)。  <!-- scripts/validate.py -->
### showcase

- `apidocs.py` (77 行) — API 文档自动提取:从 skills/*/scripts/*.py 的 argparse 定义提取参数说明(AST 解析,不执行脚本)。  <!-- showcase/apidocs.py -->
- `build_index.py` (1080 行) — Skill X 橱窗站构建器 v3:双语 / 分类 / 套件中心 / 外置 assets / 增量构建。  <!-- showcase/build_index.py -->
- `svg_map.py` (200 行) — 零依赖 SVG 思维导图渲染器。  <!-- showcase/svg_map.py -->
### showcase/mindmaps

- `binary-reverse-engineering.yaml` (34 行)  <!-- showcase/mindmaps/binary-reverse-engineering.yaml -->
- `malware-analysis.yaml` (29 行)  <!-- showcase/mindmaps/malware-analysis.yaml -->
- `memory-forensics.yaml` (30 行)  <!-- showcase/mindmaps/memory-forensics.yaml -->
- `pentest-methodology.yaml` (35 行)  <!-- showcase/mindmaps/pentest-methodology.yaml -->
- `suite-addyosmani--agent-skills.yaml` (39 行)  <!-- showcase/mindmaps/suite-addyosmani--agent-skills.yaml -->
- `suite-vercel-labs--agent-skills.yaml` (19 行)  <!-- showcase/mindmaps/suite-vercel-labs--agent-skills.yaml -->
- `verification-run-hygiene.yaml` (26 行)  <!-- showcase/mindmaps/verification-run-hygiene.yaml -->
### skills/binary-reverse-engineering

- `SKILL.md` (42 行)  <!-- skills/binary-reverse-engineering/SKILL.md -->
### skills/binary-reverse-engineering/references

- `extended-tool-routing.md` (31 行) — Extended tool/skill routing (absorbed)  <!-- skills/binary-reverse-engineering/references/extended-tool-routing.md -->
- `managed-game.md` (19 行) — Managed and Game Targets  <!-- skills/binary-reverse-engineering/references/managed-game.md -->
- `native-workflow.md` (21 行) — Native Reverse Workflow  <!-- skills/binary-reverse-engineering/references/native-workflow.md -->
- `protocol-reverse.md` (16 行) — Protocol Reverse  <!-- skills/binary-reverse-engineering/references/protocol-reverse.md -->
- `unpacking-obfuscation.md` (20 行) — Unpacking and Obfuscation  <!-- skills/binary-reverse-engineering/references/unpacking-obfuscation.md -->
### skills/binary-reverse-engineering/scripts

- `triage_binary.py` (59 行) — Fast, dependency-free binary triage with hashes, magic, entropy, and strings.  <!-- skills/binary-reverse-engineering/scripts/triage_binary.py -->
### skills/malware-analysis

- `SKILL.md` (41 行)  <!-- skills/malware-analysis/SKILL.md -->
### skills/malware-analysis/references

- `c2-protocol.md` (100 行) — C2 Protocol Decoding  <!-- skills/malware-analysis/references/c2-protocol.md -->
- `detection.md` (117 行) — IOC Extraction and Detection Rules  <!-- skills/malware-analysis/references/detection.md -->
- `ttp-mapping.md` (108 行) — MITRE ATT&CK TTP Mapping  <!-- skills/malware-analysis/references/ttp-mapping.md -->
- `unpacking.md` (101 行) — Unpacking and Anti-Analysis  <!-- skills/malware-analysis/references/unpacking.md -->
### skills/malware-analysis/scripts

- `static_triage.py` (110 行) — Static malware triage: hash, format, entropy, imports, strings, packer hints.  <!-- skills/malware-analysis/scripts/static_triage.py -->
### skills/memory-forensics

- `SKILL.md` (40 行)  <!-- skills/memory-forensics/SKILL.md -->
### skills/memory-forensics/references

- `dump-structures.md` (21 行) — Dumps, Structures, and Pointer Chains  <!-- skills/memory-forensics/references/dump-structures.md -->
- `linux-android.md` (13 行) — Linux and Android Memory Workflow  <!-- skills/memory-forensics/references/linux-android.md -->
- `windows.md` (17 行) — Windows Memory Workflow  <!-- skills/memory-forensics/references/windows.md -->
### skills/memory-forensics/scripts

- `aob_scan.py` (34 行) — Scan a file or dump for AOB patterns such as '48 8B ?? ?? 89'.  <!-- skills/memory-forensics/scripts/aob_scan.py -->
- `dump_strings.py` (19 行) — Extract offset-aware ASCII and UTF-16LE strings from memory dumps.  <!-- skills/memory-forensics/scripts/dump_strings.py -->
### skills/pentest-methodology

- `SKILL.md` (56 行)  <!-- skills/pentest-methodology/SKILL.md -->
### skills/pentest-methodology/references

- `cloud-container.md` (13 行) — Cloud and Container Workflow  <!-- skills/pentest-methodology/references/cloud-container.md -->
- `graphql-realtime.md` (9 行) — GraphQL, WebSocket, and Realtime APIs  <!-- skills/pentest-methodology/references/graphql-realtime.md -->
- `network-identity.md` (12 行) — Network and Identity Workflow  <!-- skills/pentest-methodology/references/network-identity.md -->
- `oauth-jwt.md` (7 行) — OAuth, OIDC, and JWT  <!-- skills/pentest-methodology/references/oauth-jwt.md -->
- `parser-smuggling.md` (7 行) — Parser Differential and Request Smuggling  <!-- skills/pentest-methodology/references/parser-smuggling.md -->
- `race-business.md` (7 行) — Race Conditions and Business Logic  <!-- skills/pentest-methodology/references/race-business.md -->
- `reporting.md` (15 行) — Reporting and Retest  <!-- skills/pentest-methodology/references/reporting.md -->
- `web-api.md` (18 行) — Web and API Workflow  <!-- skills/pentest-methodology/references/web-api.md -->
### skills/pentest-methodology/scripts

- `http_recon.py` (38 行) — Capture a compact HTTP/TLS/header/body snapshot as JSON.  <!-- skills/pentest-methodology/scripts/http_recon.py -->
- `js_routes.py` (26 行) — Extract likely routes, URLs, and API endpoints from local JavaScript bundles.  <!-- skills/pentest-methodology/scripts/js_routes.py -->
- `jwt_inspect.py` (27 行) — Decode JWT header/claims without attempting signature verification.  <!-- skills/pentest-methodology/scripts/jwt_inspect.py -->
- `openapi_inventory.py` (32 行) — Inventory operations, parameters, security, and responses from OpenAPI JSON/YAML.  <!-- skills/pentest-methodology/scripts/openapi_inventory.py -->
- `request_matrix.py` (22 行) — Run a deterministic HTTP request matrix from a JSON case file.  <!-- skills/pentest-methodology/scripts/request_matrix.py -->
### skills/verification-run-hygiene

- `SKILL.md` (337 行)  <!-- skills/verification-run-hygiene/SKILL.md -->
### skills/verification-run-hygiene/references

- `anti-patterns.md` (29 行) — 反模式清单与可归档性  <!-- skills/verification-run-hygiene/references/anti-patterns.md -->
