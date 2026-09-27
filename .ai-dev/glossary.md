# Glossary — 术语表(只留会被猜错的黑话/缩写)

| 术语 | 含义 |
| -- | -- |
| 四坑检查 | 收录外部套件前的四项必检:①命名空间(owner/name 前缀)②许可证白名单(MIT/Apache-2.0/BSD/ISC/CC-BY-4.0)③供应链审查(可执行文件红线)④死链(每日探活)。缺一不收录。 |
| 精选 / curation | 按方向(安全研究/逆向/工程纪律)从上游套件里筛出的技能白名单,见 `showcase/curation.json`;空数组=整套件不展示。页面显示"精选 N / 共 M"。 |
| 口径 | 下载量统计规则:**只计经本站链接的下载与复制**,直连上游安装不计入。页面上必须写清这句。 |
| ingest / 收录 | 把外部套件拉进 `external.json` 的动作(scripts/ingest.py),含四坑检查。 |
| 自研 / 收录(页面标签) | 自研=本站开发、私有仓库授权分发(需 PAT);收录=社区精选、一键指向上游安装。 |
| 导图 / mindmap | 由 `showcase/mindmaps/*.yaml` 生成的 SVG 结构图,内联进详情页(可悬停高亮),同时产出独立文件供外部引用。 |
| 审计等级 | A / A- / B / C / D,由 `scripts/audit_skill.py` 对 8 项静态检查(AST 级)自动评定;收录技能用"收录审查记录"作摘要。 |
| 纯净重放 | 部署方式:先传包到站点父目录 → 删站点目录 → 重建 → 解压。因 tar 解压不删旧文件,不做这步下架页会残留。 |
| 热重载 | api/server.py 每 30s 自检源码 mtime,变化则 `os.execv` 自重启;上传新代码即生效。 |
| 增量构建 | 构建器按"输入内容哈希"写 `.build-manifest.json`,未变页面跳过重写。 |
| 指针文件 | 各 AI 工具的规则文件(AGENTS.md / .github/copilot-instructions.md 等),内容只有十几行,统一指向 `.ai-dev/START_HERE.md`。 |
| api_sk / BT_API_SK | 宝塔面板 API 密钥,签名方式 `md5(request_time + md5(api_sk))`;只在环境变量传,不落盘。 |
