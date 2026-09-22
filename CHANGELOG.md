# Changelog

## [0.1.0] - 2026-09-22

首个内部里程碑:M0 奠基 + M1 核心包 + 收录管线 + 橱窗站。

### Added
- 仓库骨架:《SKILL.md 编写规范》、接入 SOP(四坑检查)、scripts/validate.py、双生态 manifest(.claude-plugin / .codex-plugin)、CI 骨架
- 自研核心包 5 个 skill:verification-run-hygiene、malware-analysis、memory-forensics、binary-reverse-engineering、pentest-methodology
- scripts/ingest.py 套件收录管线(四种来源/manifest 发现/许可证探测/可执行面扫描)
- 首批社区收录:addyosmani/agent-skills(25,MIT)、vercel-labs/agent-skills(9,许可证未确认仅链接),登记于 external.json
- showcase 橱窗站 v2:多页(首页+自研页+套件页+收录 skill 页共 42 页)+ 前端静态搜索 + 构建期泄露断言;已部署 EdgeOne Pages
- scripts/link_check.py + link-check.yml:每日 upstream 死链探活(artifact 报告)
- docs/access-management.md:授权发放与三种安装方式

### 验收(均已实跑)
- validate.py 5/5 通过;npx skills CLI 发现 5 个自研 skill;端到端安装→卸载→环境还原
- 收录管线对 addyosmani/agent-skills 干跑清点 25 skill;两个套件供应链审查 passed
- 橱窗构建泄露断言:42 页 × 5 个自研正文样本,零泄露

### 待办
- GitHub 私有远程建仓 skill-x(待 PAT)→ SSH 推送 → 分发验证三连
