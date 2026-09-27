# HANDOFF — 工作记忆(新会话只读 START_HERE + 本文件即可接续)

- 更新时间:2026-09-28
- 当前主线:MCP 安装连接市场(另一会话负责,骨架完成待部署);本站 v2 + 社区卡片 UI 已上线稳定。

## 当前状态(可验证)

- 线上:https://skillx.yueliai.top(6+ 路由全 200;移动端 UA 200;2026-09-28 已部署社区卡片 UI,首页 9 卡片 / 0 行式残留)。
- 内容:5 个自研技能 + 4 个社区精选(addyosmani 25 选 4;vercel-labs 整包因方向不符退出展示)+ 1 个收录套件。
- 能力:双语切换、分类筛选、自研/社区统一卡片 UI、首页顶部实时推荐器、安全审计折叠(AST 级 8 项)、可交互思维导图、下载计数、`/api/recommend`、`/tools.json`、`/audit-report.json`、严格 CSP、纯净重放部署、后端热重载。
- 仓库:HEAD `4c37ec4` 已推送(远端 main 一致);工作区另有 MCP 未提交改动(另一会话在写,本会话不碰)。
- 部署通道与 IP:宝塔 API 已验证;本机出口 `219.132.121.147`(2026-09-28 实测,广东电信动态池)已在白名单,probe 直接通过。
- 本轮新增 MCP 市场(已本地验证,待部署):
  - `mcp-registry.json`(官方 server.json + `_meta.top.skillx/curated` 策展层;种子 ac.inference.sh/mcp@2.0.0 纯远程)
  - `scripts/mcp_ingest.py`(schema 校验+传输/isSecret 检查+upsert;正负路径已验证)
  - `api/server.py`:`GET /v0/servers`(官方兼容游标分页,只放 execReview=passed)+`POST /api/mcp/install`(计数入 stats.db,mcp: 前缀)
  - `showcase/build_index.py`:site-data.json 增 `mcps` 面(只放过审条目,不含密钥/认证头)
  - `deploy/sync.py --api`:补传 mcp-registry.json 到 /www/wwwroot/(server.py 以 BASE.parent 定位)
  - 文档:`docs/mcp-onboarding-pipeline.md`(收录 SOP)、`docs/mcp-marketplace-research.md`(调研)
- 本地实测:GET /v0/servers 返回种子条目;POST install 计数 1→2;ingest stdio 标 high、漏标 isSecret exit=3 拒收;build 通过 mcps count=1。

## 已完成的改动(本轮)

- 社区精选统一为与自研相同的卡片 UI:首页各套件分组内改 `.grid` + `card()`(与自研同款标题/等宽名/三行描述/分类与来源标签),套件详情页同步;删除旧 `row` 分支与 `.list/.row` CSS;卡片链接改绝对路径/`skills/ext-*.html`。
- 验证:build 通过(写入 4 页,泄露断言通过);首页 9 张卡片、无 `class="row"` 残留;ext 详情页与套件页 200;桌面 1280 + 移动 390 截图核对无溢出。
- 部署上线:会话内注入 `BT_API_SK` 跑 `deploy/sync.py` 纯净重放成功;线上首页 9 卡片 / 0 行式,own/suites/ext 页全 200。
- 修复 `deploy/sync.py` Windows 构建输出解码:subprocess 补 `encoding="utf-8", errors="replace"`,不再抛 GBK 线程 traceback 且保留构建日志(已验证 RC 0)。
- 确认出口 IP 与白名单状态(probe 通过),无需再加白名单。
- MCP 市场四层骨架落地(数据/收录/API/消费),沿用 skill 收录纪律(未过审不进对外产物、stdio 标 high 风险、用户密钥永不入库)。
- 收尾协议落地:会话文档 = `.ai-dev/`(devctx),任务前读 START_HERE+HANDOFF、每轮需求结束压缩回写 HANDOFF;已写入 `conventions.md`;老胡 2026-09-28 拍板。

## 下一步(有序)

1. 等老胡决策的三项:
   - 宝塔 API 白名单改成段(避免换 IP 反复拦截)。
   - SSH 禁密码:加固 drop-in 已就位(`/etc/ssh/sshd_config.d/00-skillx-hardening.conf`),**待一次 sshd 重载才生效**——面板 sshd 操作是空转,需他在面板/控制台触发。
   - 思维导图 yaml:目前按技能内容自拟,老胡若给参考链接则提炼替换。
2. MCP 部署由另一会话执行(`deploy/sync.py --api --reload`);部署后线上核对 `/v0/servers` 与 `site-data.json` 的 `mcps`。
3. 可选:橱窗站加"MCP 服务"独立 tab(render_mcps + 导航 + i18n,注意 1000+ 行泄露断言红线区);收录方向标准复审(curation.json 白名单可随时调,可逆)。

## 约束(别违反)

- 页面零内联 style / 零内联脚本(严格 CSP)。
- 自研 SKILL.md 正文不得进任何页面产物。
- api_sk / PAT 不落盘、不入库、不进 memory/.ai-dev(只记"已提供/在用")。
- 部署走 `deploy/sync.py`(纯净重放),不要手工解压覆盖。
- 未过人工审查(execReview=passed)的 MCP 条目不进对外产物(橱窗+/v0/servers)。

## 陷阱区(本次踩到、下次先查 lessons.md)

- 本机 `refs/remotes` 不可写 → merge 用 FETCH_HEAD。
- 宝塔 API 无进程/计划任务接口 → 需要时请老胡面板操作。
- 下载验收别用 `curl -o /dev/null`(Git Bash 下假 0B)。
- 生成器代码改动要让它进入增量 key,否则不重建。
- 改生成器 UI 后要 build + 截图核对(桌面 1280/移动 390),并检查旧 class 残留;旧 "row" 行式清单已移除,新列表一律用 `card()`。
- `deploy/sync.py` 构建子进程输出必须显式 UTF-8 解码(已修);否则 Windows 下报线程 traceback 并吞掉构建日志。
- 审计报告由 CI(Linux)生成:本地 Windows 若再遇 `--check` 漂移,先看是否只是 `generatedAt` 跨日(正常,刷新报告即可),平台差异已由 `as_posix()` + LF 归一消除。
- **apply_patch 一次多 hunk 时可能部分成功部分失败** → 打完必须 Select-String 逐处核对(本轮 server.py 缺 MCP_REGISTRY 加载行、do_POST 残留旧守卫行 404 即此因)。
- 后台 job 起 python 服务随命令退出死亡 → 用独立会话长跑;改 server.py 后等 watch_reload 30 秒自检生效再验。

## 部署闭环(本会话 2026-09-28 执行)
- `deploy/sync.py --api --reload` 纯净重放成功;server.py/registry.json/mcp-registry.json 全上传;nginx vhost 备份后加 `/v0/` 反代并 reload。
- 线上验收:`/api/health` version=2026-09-28.1;`GET /v0/servers` 返回 ac.inference.sh/mcp@2.0.0(official=active);`POST /api/mcp/install` 计数通(线上 stats.db 含 1 条本次测试计数,保留)。
- commit `54c6e20` 已推送 origin main。
- 注意:HANDOFF.md 是多会话共用,本会话只增量追加不覆盖;头部"另一会话负责"为并行会话所写,以其最新改动为准。
