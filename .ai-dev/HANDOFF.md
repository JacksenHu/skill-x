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

## MCP 页面渲染闭环(2026-09-28 补,老胡指出线上无 MCP 入口)
- 问题:上轮只做了数据面(site-data.json 有 mcps)和 API,**首页/导航/API 文档页无渲染** → 网页看不到 MCP。
- 修复:导航加独立 `/mcp.html` tab;`collect_mcps()`+`render_mcp()`(MCP 卡片含双语简介/分类/远程或本地/风险徽章/版本/安装命令);`render_api` 补 `/v0/servers`+`/api/mcp/install` 说明与 curl;CSS 加 risk-* 徽章配色。
- 部署:sync.py --skip-build(纯净重放);线上 `/mcp.html` 200、首页导航含 MCP、`/api.html` 含两端点。commit `fb64eeb` 已推送。
- 教训:**数据面接通≠用户可见**,改完必须核对页面渲染与导航入口。

## MCP 详情页闭环(2026-09-28 补,老胡要求卡片可点进详情)
- 修复:collect_mcps 补全字段;mcp_slug();render_mcp 卡片 h3 套链接指向 `/mcp/<slug>.html`;新增 render_mcp_detail(与 skill 详情页同构:card-head/kv 键值表/接入命令块+copy/riskNote/连接端点表或安装包表);main 生成详情页;CATEGORIES 加 ai-media。
- 部署:sync.py --skip-build;线上 `/mcp/ac.inference.sh--mcp.html` 200、列表卡片链接指向详情页。commit `a3e47ab` 已推送。
- 教训:patch 多 hunk 易出语法断裂(本次 `},{"` 断行、CATEGORIES `}` 重复),打完必须 ast.parse 验证再 build。

## MCP 应用程序接入能力(2026-09-28 补,老胡指出无法程序化安装/连接)
- 问题:原 `/v0/servers` 只是只读列表,`/api/mcp/install` 只是记数——应用程序无法通过 API 真正"装"和"连"。
- 修复(接入描述 + 代为连接):
  - `mcp_install_descriptor(name)`:远程 config={type,url};本地 config={command,args,env}(npm→npx -y/pypi→uvx+packageArguments);requiredSecrets 声明;clientSnippets 给 claude/cursor/codex/vscode 可直接写配置的 JSON 片段。
  - `GET /v0/servers/<ns/name>/install` 返回接入描述;`POST /api/mcp/connect {name,client,secrets}` 校验必填密钥→内存拼接填好密钥的客户端片段返回(不落库)+计数(mcp-connect: 前缀)。
- 部署:server.py 热重载;线上 install descriptor 与 connect(claude/codex/vscode)实测通过;api.html 已补文档。commit `dd9dc57` 已推送。线上含 1 条 mcp-connect 测试计数。
- 教训:**"市场"的价值不是列表,是下发可写配置的接入描述**;POST 白名单守卫行 patch 又现重复(本轮 361-362),改后必须 Select-String 核对唯一性。

## 首页改版 + HyperFrames hero(2026-09-28 补,老胡要求)
- 目标:去掉独立技能推荐页(功能已在技能页内),导航改为 首页/技能/MCP/API/关于,新增宣传型首页。
- `showcase/build_index.py`:新增 `render_home()`(品牌 hero + 真实数字带 + 产品实拍 + 技能精选 + MCP 入口 + 收录纪律 + CTA);原技能库迁到 `/skills.html`(推荐器/筛选/卡片全保留);删除 `render_recommend()` 与 `/recommend.html`(构建已自动清理旧产物);导航重写;套件页 active 归入"技能";技能页社区区补"套件中心"入口;`html/body` 改 `overflow-x:clip`;首页样式 + 移动端折叠 + reduced-motion 停播 hero 视频。
- HyperFrames 调用:`showcase/hyperframes/hero/`(design.md + index.html,3 场景/2 转场/确定性时间轴),`hyperframes lint/validate/inspect` 全过;渲染 `showcase/assets/hero-loop.mp4`(1600x900,9s,485KB);`showcase/assets/proof-{skills,detail,mcp}.jpg` 为本站页面 Playwright 实拍。
- 构建:`showcase/assets/` 下的图片/视频按内容哈希复制进 `dist/assets/`;finesse 样式戳已写入 CSS 顶部,`.finesse/log.json` 本地记录且已加入 `.gitignore`。
- 验证:build 17 页 + 泄露断言通过;`/`、`/skills.html`、`/mcp.html`、`/api.html`、`/about.html`、`/suites/`、技能详情、hero mp4 与 proof jpg 全 200;dist 无 `recommend.html`;桌面 1440 + 移动 390 截图核对无溢出。
- 已部署(2026-09-28,纯净重放 686KB):线上首页 200(hero 视频 + 新导航)、`/skills.html`、`/mcp.html`、`/api.html`、`/about.html` 全 200;`hero-loop.mp4`(496534B)与 proof jpg 全 200;`/recommend.html` 已 404 下线。

## 首页 v2:去截图改真实功能 + 滚动动效(2026-09-28 补,老胡要求)
- 首页彻底去掉截图:删除 `.home-proof` 区块与 `proof-*.jpg` 资源(构建现在会清理 dist 里的过时媒体);hero 背景改为纯动效。
- HyperFrames hero 重渲染为"无文字纯动效背景":LIVE INDEX 数字带 → 确定性路径追踪 → 收束框,3 场景 2 转场,`lint/inspect` 全过;`hero-loop.mp4` 8.5s / 348KB 全出血播放,左侧 scrim 保文案可读,reduced-motion 停播。
- 新增"真实功能"区块(可交互,非示意):技能推荐器(真调 `/api/recommend`,失败降级 `/site-data.json`);交互式结构导图(内联真 SVG,悬停高亮/描边绘制);安全审计(真实 `<details>` 折叠，AST 8 项);MCP 接入(真调 `/v0/servers/<name>/install`,切换 Claude/Cursor/Codex/VS Code 片段并可复制)。
- 滚动动效(R2 原生 scroll-driven,零依赖):顶部进度轨、hero 视差+文案渐隐、分区三种不同入场(rise/slide/settle)、h2 强调线随滚动绘制;`prefers-reduced-motion` 全停,无 `animation-timeline` 时由 app.js 用 rAF + IntersectionObserver 降级,另补 `@media print` 终态。
- 验证:build 17 页 + 泄露断言;`#idea` / `#mcp-demo` 锚点截图确认滚动归位与 MCP 命令回显;dist/assets 仅剩 style.css / app.js / hero-loop.mp4;线上 `/api/recommend` 实测 3 条命中。

## 首页 v3:一体化工作台(去掉功能罗列,2026-09-28 补,老胡要求)
- 问题:上一版把四个真实功能写成"真实功能"标题 + 下方平铺,像功能清单;展示设计一般。
- 联网参考(只取模式不抄代码):Magic UI 组件族(`registry.json` 清单 + `bento-grid.tsx` 源码:bento/terminal/dock/number-ticker/border-beam/scroll-progress);Linear/Vercel/Stripe 类产品的 sticky 产品舞台 + 滚动驱动步骤。
- 重构:删除"真实功能"标题与四块平铺面板,改成 `.bench` 一体化工作台 = 左侧 4 步轨道(每步 52vh,驱动滚动) + 右侧 sticky 控制台(顶栏 dots/path/LIVE、4 个真实面板、底部 mono 状态行);滚到哪一步控制台就地切到对应面板(用 rect 判定,避开 IntersectionObserver 同屏竞态),点击步骤也可切;移动端退化为吸顶 tab 行。
- 细节:hero 四个数字改 number-ticker 式滚动计数;控制台顶部流光 beamPulse;导图面板限高可滚;保留零依赖/严格 CSP/reduced-motion 全停/R2 滚动动效。
- 验证:build 17 页 + 泄露断言;`#workbench`→推荐器面板、`#step-audit`→审计面板、`#step-mcp`→MCP 面板逐个截图核对;移动端 390 截图核对吸顶 tab 与面板;dist 无 proof 截图资源。
- 已部署(纯净重放 400KB):线上首页 200(workbench/4 步/4 面板/4 计数器、无 proof 引用)、`/skills.html`、`/mcp.html` 200;`/v0/servers/.../install` 200、`/api/recommend` 200、`hero-loop.mp4` 356789B 200。提交 `4a2dcec`。

## 缓存策略与重启(2026-09-28 补,老胡要求清缓存)
- 资源版本化:`build_index.py` 新增 `ASSET_VER`(CSS + APP_JS + hero 视频内容哈希),`style.css` / `app.js` / `hero-loop.mp4` 均带 `?v=<hash>`;资源一变 URL 就变,不再靠用户手动强刷。当前版本 `v=109d9969`。
- nginx 缓存策略(`deploy/nginx/skillx.yueliai.top.conf`,旧配置已备份):`/` 与 `*.html`、`*.json` → `expires -1`(no-cache);`/assets/*`(css/js/mp4/图片/woff2/ico) → `expires 1y`;`/mindmaps/` → `expires 1h`(保留 CORS)。
- 执行:写 vhost(备份 `deploy/nginx-backup/skillx.yueliai.top.20260928-144322.conf`)→ `sync.py --api --reload`:纯净重放站点、重传 server.py / registry.json / mcp-registry.json 触发后端热重载、nginx reload 返回执行成功。
- 线上核对:`/`、`/skills.html`、`/site-data.json` → `Cache-Control: no-cache`;`/assets/style.css?v=109d9969` → `max-age=31536000`;`/mindmaps/*.svg` → `max-age=3600`;HTML 三处资源均带 `?v=109d9969`;`/api/recommend` 与 `/v0/servers/.../install` 均 200。
