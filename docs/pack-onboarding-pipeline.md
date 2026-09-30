# 专家团(pack)收录 SOP

> 对应 `docs/mcp-onboarding-pipeline.md`(MCP 收录)与 `docs/plugin-onboarding-pipeline.md`(插件收录)的专家团版本。
> 收录入口 `scripts/pack_ingest.py`,注册表 `packs.json`,成员解析层 `scripts/resolve_members.py`;
> 对外只暴露 `reviewed.execReview=passed` 的条目。

## 定位:带人设的编排层

图标硬要求:所有专家团必须提供 persona.avatar,且风格与 ssets/avatars/abyss-deep-reverse.svg / ift-pentest.svg / 	race-malware.svg 一致;自研专家团必须创建专属头像,不允许所有新专家团共用同一个占位图。

专家团 = **人设(名称/头像/角色文案) + 跨类型成员编队 + 一份可直接执行的协作剧本(meta-skill)**。

- 成员类型:`own-skill`(自研技能)/ `ext-skill`(社区精选技能)/ `mcp`(MCP 服务)/ `cli` / `api`(后两类为预留,须在 pack 定义内联 `name` + `install` 才视为已解析)。
- 自研专家团的编排剧本源文件在 `skills/pack-<slug>/SKILL.md`(meta-skill,`metadata.package_type=meta-skill` + `orchestration.children`),`packs.json` 的 `content` 字段由 `--sync` 保持同步。
- 外部专家团只存"人设 + 成员清单 + 安装指引",本体留上游;许可证允许时可缓存正文。

## 数据结构(packs.json)

```json
{
  "slug": "abyss-deep-reverse",
  "displayName": "深潜",
  "displayNameEn": "Abyss",
  "persona": {"role": "二进制解剖师", "roleEn": "...", "tagline": "...", "taglineEn": "...",
              "intro": "...", "introEn": "...", "avatar": "assets/avatars/abyss-deep-reverse.svg",
              "scene": "reverse-engineering", "subScene": "binary"},
  "summary": "...", "summaryEn": "...",
  "origin": "own | external",
  "skill": "pack-abyss-deep-reverse",
  "source": "skills/pack-abyss-deep-reverse/SKILL.md",
  "license": {"spdx": "MIT"},
  "members": [{"type": "own-skill", "ref": "binary-reverse-engineering"}],
  "install": "GITHUB_TOKEN=<PAT> npx skills add JacksenHu/skill-x --skill pack-abyss-deep-reverse",
  "content": "<编排剧本全文,由 --sync 同步>",
  "degraded": false,
  "reviewed": {"by": "jacksen", "at": "YYYY-MM-DD", "execReview": "passed"},
  "upstreamStatus": {"source": "own", "lastCheck": "YYYY-MM-DD", "alive": true, "failSince": null}
}
```

成员 ref 约定:自研 = `<skill-name>`(在 `skills/<name>/`);收录 = `<owner>/<repo>/<skill-name>`(末段为技能名);MCP = 官方 `name`(如 `ac.inference.sh/mcp`)。

## 收录流程

### 1. 准备 pack.json 底稿

外部专家团必填:`slug`(小写连字符)/`displayName`/`displayNameEn`/`summary`/`summaryEn`/`persona{role, roleEn, tagline, scene}`/`origin=external`/`upstream`/`install`/`license`/`members`。

```bash
python scripts/pack_ingest.py ./pack.json [--dry-run]
```

脚本会做:slug 与字段结构校验 → 成员完整性解析(所有非 optional 成员必须已收录且过审)→ 许可证白名单提示(不在白名单只允许元数据+指引收录)→ upsert 后置 `execReview=pending`。

### 2. 专家团特有的检查

- **成员完整性(硬性)**:`scripts/resolve_members.py` 逐个解析;任何非 optional 成员未收录/已下架都拒绝收录。
- **人设审查(人工)**:名称/头像/文案不得侵权、仿冒他人品牌或与实际能力不符;头像须为原创资产(或使用 `assets/avatars/pack-default.svg`)。
- **编排剧本审查(人工)**:步骤必须真的调用成员技能;不得包含越权、破坏性或误导性指令;剧本正文会被公开展示,不得写入内部信息。
- **降级规则**:成员下架后 `--sync` 会把对应成员标 `resolved=false` 并把专家团标 `degraded=true`;橱窗/API 仍然输出该专家团,但显著标注、安装契约中提示跳过。

### 3. 同步与一致性

```bash
python scripts/pack_ingest.py --sync    # 重解析成员 + 同步 content + 更新 degraded
python scripts/pack_ingest.py --check   # CI/提交前:漂移则 exit=1
```

> 纪律:改了 `skills/pack-*/SKILL.md` 或成员收录状态后,**先 `--sync` 再构建/部署**;
> 构建时若检测到 content 与源文件不一致会打印红色警告。

### 4. 四坑检查(与 skill/MCP 同套)

| 坑 | 专家团版含义 |
|---|---|
| 命名空间 | slug 与成员 ref 不撞名;外部专家团一律以 slug 隔离 |
| 许可证 | 自研为 MIT;外部看上游 LICENSE,不在白名单只做元数据+指引 |
| 供应链 | 成员必须是站内已过审条目;外部专家团本体不镜像(除许可允许的正文) |
| 死链 | 外部 `upstream` 定期探活,结果记入 `upstreamStatus` |

## 对外数据形状

- `/v0/packs`:游标分页列表(`?limit&cursor`),只放已过审专家团;含人设、成员摘要、`degraded` 标记。
- `/v0/packs/<slug>`:详情;含完整人设、编排剧本正文 `content`、成员安装描述符数组(`install`/`page`,`mcp` 成员附 `mcpInstall` 客户端片段)。
- `/v0/packs/<slug>/install.md`:`text/markdown` 专属安装契约(给 Agent 读的完整步骤)。
- `/install/pack-install.md`:静态全局安装契约(提示词入口,构建期生成到 `dist/install/`)。
- `POST /api/pack/install {"slug": "<slug>"}`:安装回报计数,`stats.db` key 前缀 `pack:`;未过审/未知 slug 返回 404。
- 橱窗站:`/packages.html` 列表页 + `/packages/<slug>.html` 详情页;`site-data.json` 增 `packs` 面(供 `/api/recommend` 与第三方消费)。

## 收录禁忌

- 不收录/不代理与己方管理资产(lic.yueliai.top、tqai.xyz 及其子域)相关的任何探测类专家团条目。
- 不收成员不完整、或引用未过审条目的专家团。
- 不收 `reviewed.execReview != passed` 的条目进任何对外产物。
- 暂不开放开发者自助提交;提交入口作为后续独立迭代。
