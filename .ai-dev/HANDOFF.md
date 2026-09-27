# HANDOFF — 工作记忆(新会话只读 START_HERE + 本文件即可接续)

- 更新时间:2026-09-27
- 当前主线:站点 v2 已上线并稳定运行;devctx 已接入;本轮为接手体检 + 审计脚本跨平台漂移修复。

## 当前状态(可验证)

- 线上:https://skillx.yueliai.top(6+ 路由全 200;移动端 UA 200)。
- 内容:5 个自研技能 + 4 个社区精选(addyosmani 25 选 4;vercel-labs 整包因方向不符退出展示)+ 1 个收录套件。
- 能力:双语切换、分类筛选、首页顶部实时推荐器、安全审计折叠(AST 级 8 项)、可交互思维导图、下载计数、`/api/recommend`、`/tools.json`、`/audit-report.json`、严格 CSP、纯净重放部署、后端热重载。
- 最近提交:700190d(chore: adopt devctx);本轮修复(审计跨平台稳定)随本次提交推送。

## 已完成的改动(本轮)

- 修复 `scripts/audit_skill.py` 跨平台漂移:可执行面路径改用 `as_posix()`;文件体积按 LF 归一(`stable_size`)。Windows 本地 `audit_skill.py --check` 不再恒定误报。
- 刷新 `showcase/audit/audit-report.json`(generatedAt 2026-09-27)。
- 接手体检:`doctor --fix` 11 项全绿;`audit_skill.py --check` 一致;`validate.py` 5/5 通过;`build_index.py` 15 页 + 泄露断言通过。

## 下一步(有序)

1. 等老胡决策的三项:
   - 宝塔 API 白名单改成段(避免换 IP 反复拦截)。
   - SSH 禁密码:加固 drop-in 已就位(`/etc/ssh/sshd_config.d/00-skillx-hardening.conf`),**待一次 sshd 重载才生效**——面板 sshd 操作是空转,需他在面板/控制台触发。
   - 思维导图 yaml:目前按技能内容自拟,老胡若给参考链接则提炼替换。
2. 需要时可做:收录方向标准复审(curation.json 白名单可随时调,可逆)。

## 约束(别违反)

- 页面零内联 style / 零内联脚本(严格 CSP)。
- 自研 SKILL.md 正文不得进任何页面产物。
- api_sk 不落盘、不入库、不进 memory。
- 部署走 `deploy/sync.py`(纯净重放),不要手工解压覆盖。

## 陷阱区(本次踩到、下次先查 lessons.md)

- 本机 `refs/remotes` 不可写 → merge 用 FETCH_HEAD。
- 宝塔 API 无进程/计划任务接口 → 需要时请老胡面板操作。
- 下载验收别用 `curl -o /dev/null`(Git Bash 下假 0B)。
- 生成器代码改动要让它进入增量 key,否则不重建。
- 审计报告由 CI(Linux)生成:本地 Windows 若再遇 `--check` 漂移,先看是否只是 `generatedAt` 跨日(正常,刷新报告即可),平台差异已由 `as_posix()` + LF 归一消除。
