# 上游收录与更新同步 SOP

> 回答「上游更新了,我们这里会不会自动更新」:目前**不会自动同步内容**。
> 本文记录收录快照模型、当前自动化边界、以及上游更新时的手动同步步骤与推荐自动化方案。

---

## 1. 当前模型:快照收录 + 每日探活

| 动作 | 脚本 | 产出 |
|---|---|---|
| skill 套件收录 | `scripts/ingest.py owner/repo` | `external.json`(快照) |
| MCP / 插件收录 | `scripts/mcp_ingest.py` | `mcp-registry.json`(条目+指路牌) |
| 专家团收录 | `scripts/pack_ingest.py` | `packs.json` |
| 每日死链探活 | `scripts/link_check.py`(CI `link-check.yml`) | `link-check-report.json` |

每个条目都带两个关键字段:

- `upstream` / `websiteUrl` / `install.url`:上游来源。
- `upstreamStatus`: `{ lastCheck, alive, failSince }`——记录最近一次探活时间与失联状态。
- `ingestedAt`(skill)/ `reviewed.at`(MCP):收录/过审时间。

---

## 2. 自动化的边界(重要)

**只有「死链探活」是自动的**:

- CI 每天跑 `link_check.py`,对 upstream URL 做 HEAD(405/404 回退 GET 首字节)。
- 结果只更新 `upstreamStatus.alive / failSince`。
- 连续 7 天失联 → 提醒下架。

**内容同步(新增技能/改描述/删技能)不是自动的**:

- 上游仓库更新后,我们这边的快照(`external.json` 的 skills 列表、描述、版本)**不会自动变化**。
- 必须有人手动重跑收录脚本,或者落地一个定时重抓任务(见第 5 节)。

---

## 3. 上游更新时的手动同步步骤(skill 套件为例)

```bash
# 1) 重新收录:会删除该 namespace 旧条目并写入新快照,ingestedAt=今天
python scripts/ingest.py owner/repo

# 2) 补新增技能的中文展示(否则会回退英文,违反 publish-checklist)
python scripts/gen_i18n_ext.py
python scripts/gen_suite_mindmaps.py

# 3) 重新审查可执行面,回填 execReview=passed
#    - external.json: verified.by/at/execReview
#    - mcp-registry.json: _meta.top.skillx/curated.reviewed

# 4) 重建 + 部署 + 验收
python showcase/build_index.py
$env:BT_API_SK="<宝塔API密钥>"
python deploy/sync.py --skip-build --api --reload
```

MCP / 插件同步同理:`python scripts/mcp_ingest.py <...>` 后补 `description-zh/category` 与 `reviewed`,再重建部署。

---

## 4. 重跑收录会踩的坑(必须知道)

1. **`ingest.py` 重跑会把 `verified.execReview` 重置为 `pending`** → 该套件会掉出橱窗和对外产物,直到重新回填过审。
2. **新增技能不会自动有中文 `name-zh/description-zh/category`** → 会回退英文展示。
3. **重跑会覆盖旧快照**,如果之前人工改过某个字段(描述/版本),会被上游原文覆盖。
4. **上游强改结构**(技能路径/命名空间/目录层级)→ 收录清单 diff 可能很大,注意命名空间冲突。

> 建议:重跑前 `git diff` 看一眼旧快照,确认哪些字段是人工补的(尤其是 `verified` 和 `i18n`)。

---

## 5. 推荐的自动化方案(待落地,按优先级)

### 方案 A:定期重抓 + diff 报告(推荐先做)

- 每周(或每日)对白名单里的 upstream 重跑 `ingest.py --dry-run` / `mcp_ingest.py --dry-run`。
- 对比旧快照,产出 diff:新增技能 / 删除技能 / 描述变更 / 可执行面变化。
- 有 diff 才提醒维护者人工确认;无 diff 静默。

### 方案 B:CI 重抓 + 自动 PR

- 新增 `sync-upstream.yml`,定期重抓白名单 upstream,自动开 PR。
- PR 里带 diff;合并前人工核对 `verified` 与 i18n。

### 方案 C:把「重抓」做成保留人工字段的 upsert(改造脚本)

- 让 `ingest.py` 重跑时**保留**旧条目的 `verified`、以及已有 i18n 的映射,只更新 skills/描述/版本。
- 这样重抓后不需要每次都重新过审、重新补中文,成本最低。

---

## 6. 当前已收录上游清单(便于核对)

| 类型 | 上游 | 更新方式 |
|---|---|---|
| skill 套件 | `external.json` 的 `suites[].upstream` | 手动重跑 `ingest.py` |
| MCP/插件 | `mcp-registry.json` 的 `servers[].websiteUrl` | 手动重跑 `mcp_ingest.py` |
| 专家团 | `packs.json`(自研 origin=own) | `pack_ingest.py --sync` |
| 死链探活 | 全部 upstream | CI 每日 `link_check.py` |

一句话:**上游更新 ≠ 本站自动更新**;目前只有「死链探活」自动,「内容同步」靠手动重抓,且重抓会重置过审状态、需要补中文。要真正自动化,优先做方案 A 或 C。
