# 上传 / 发布前检查清单（发布门禁）

> 目的：把「一次收录到真正上线」的每一步固化下来，避免再出现「上架了但名称/介绍还是英文、没有思维导图」这类漏项。
> 本清单适用于 skill（本站/收录）、MCP/插件、专家团（pack）三类条目。**任何一类不满足，不得构建、不得部署。**

---

## 0. 一句话结论

线上可展示的每个条目，必须具备：

1. 中文名（`name-zh`）
2. 中文介绍（`description-zh`）
3. 分类（`category`）
4. 思维导图（`mindmaps/<skill>.svg`，来自 YAML → `svg_map.py`）
5. 图标（有官方图标用官方；没有用默认占位）
6. 通过审查（`execReview=passed`）

只有 `reviewed.execReview == "passed"` 的条目才进入橱窗站和 `/v0/*` 对外产物。

---

## 1. 内容层：先有合规的条目本体

### 1.1 本站 skill
- 目录 `skills/<name>/SKILL.md`，`name` 与目录名一致。
- frontmatter 只用规范基础字段（`name/description/license/compatibility/metadata`）；禁用 `allowed-tools / context: fork / Hooks`。
- 本站 `metadata` 必填 `name-zh / description-zh / category`。
- `description` 三段式（做什么 + 何时用 + 触发关键词），中英文关键词都列。
- 正文 ≤500 行；无 API key / 个人路径 / 私有地址 / 对抗性指令。
- 跑 `python scripts/validate.py`。

### 1.2 外部 skill / 套件
- `python scripts/ingest.py owner/repo [--dry-run]` 入库到 `external.json`。
- 四坑检查（见第 3 节）逐项出结论，不得「看着没问题」。
- 许可证不在白名单的，只收元数据 + 安装链接，不镜像内容。

### 1.3 MCP / Agent 插件
- `python scripts/mcp_ingest.py ./server.json` 或 `--registry-name ns/name`，入库 `mcp-registry.json`。
- 密钥声明检查：变量名命中 `KEY/TOKEN/SECRET/PASSWORD` 却没标 `isSecret=true` → exit=3 拒收。

### 1.4 专家团 pack
- `python scripts/pack_ingest.py ./pack.json` 入库 `packs.json`。
- 成员完整性：所有非 optional 成员必须已收录且过审。
- 本站专家团必须原创头像（SVG）。

---

## 2. 展示层：中文名 / 中文介绍 / 分类 / 思维导图（本次漏项）

> 这是「上架后用户看到的页面」最直接的三个来源，缺一个就是「英文 + 无导图」。

### 2.1 中文名 + 中文介绍 + 分类

- 本站 skill：写在 `SKILL.md` 的 `metadata`（`name-zh / description-zh / category`）。
- 外部套件：写在 `showcase/i18n-ext.json`，按 `namespace → skill 名` 索引：

```json
{
  "owner/repo": {
    "skill-name": {
      "name-zh": "中文名",
      "description-zh": "一句话中文介绍",
      "category": "pentest | reverse-engineering | malware | forensics | engineering-hygiene | dev-workflow | data | web-frontend | ai-media"
    }
  }
}
```

- `category` 只能取站内已注册的分类枚举，不得自造。
- 未提供中文的条目不得进橱窗（构建侧会用英文兜底，但这是「未完成」而非「通过」）。

### 2.2 思维导图

- YAML 源文件放 `showcase/mindmaps/<skill>.yaml`（受限子集：`root:` + `children:` + `- label:`）。
- 用 `showcase/svg_map.py` 渲染成 `showcase/mindmaps/<skill>.svg`。
- 构建时会把 `mindmaps/` 拷进 `dist/mindmaps/`，对外走 `/mindmaps/<skill>.svg`（已开 CORS）。
- 批量生成时，至少保证：根节点 = `name-zh`；一级分支覆盖「场景 / 核心流程 / 工具链 / 输出」。

### 2.3 图标

- MCP/插件优先用官方 `server.json` 的 `icons[0].src`。
- skill 默认用 `showcase/assets/avatars/icon-default.svg`；上游有图标时在 `showcase/i18n-ext.json` 或对应展示条目补 `icon`。

---

## 3. 审查层：四坑 + 过审

### 3.1 四坑检查（逐项出结论）
| 坑 | 检查点 |
|---|---|
| 命名空间 | `owner/name` 前缀、与本站/已收录查重 |
| 许可证 | 白名单 MIT/Apache-2.0/BSD-2/BSD-3/ISC/CC-BY-4.0；不在白名单只收元数据+链接 |
| 供应链 | 可执行面逐个审查：未声明外联 / 凭证读取外传 / 混淆 / `curl|sh` → 拒收 |
| 死链 | upstream 探活，连续 7 天失联下架 |

### 3.2 过审回填
- skill：`external.json` 的 `verified = {by, at, execReview: "passed"}`。
- MCP：`mcp-registry.json` 的 `_meta.top.skillx/curated.reviewed.execReview = "passed"`。
- pack：`packs.json` 的 `reviewed.execReview = "passed"`。
- `pending` 一律不进橱窗站和 `/v0/*`。

---

## 4. 构建层：本地先过

```bash
python showcase/build_index.py
```

检查点：
- 返回码 0；输出「泄露断言通过」。
- 页面数、`site-data.json` 的 suites/skills/mcps/packs 数量与预期一致。
- 抽查技能详情页：中文名、中文介绍、分类、思维导图引用都出现了。

---

## 5. 部署层：纯净重放上线

```bash
$env:BT_API_SK="<宝塔API密钥>"
python deploy/sync.py --skip-build --api --reload
```

- `--api`：同传后端 `server.py / registry.json / mcp-registry.json / packs.json`。
- `--reload`：部署后 reload nginx。
- 关键：tar 解压只覆盖同名文件，不清旧产物，所以 sync.py 用「删站重建」纯净重放。

---

## 6. 验收层：上线后逐项核对

- 首页、技能页、套件页、MCP 页、专家团页、`/api/health` 全 200。
- `site-data.json` 数量正确（suites/skills/mcps/packs）。
- 抽查条目：**中文名、中文介绍、分类、思维导图 `/mindmaps/<skill>.svg` 均可见可访问**。
- `/api/recommend?q=关键词` 能召回。
- 思维导图 SVG 返回 200 且内容非空。

---

## 7. 收尾

- 提交并推送本次 registry 改动（`external.json / curation.json / i18n-ext.json / mindmaps/`）。
- 更新 `HANDOFF.md`（记录已上线内容与遗留项）。

---

## 附：批量补中文/导图的工具

- 中文 i18n 批量生成：`python scripts/gen_i18n_ext.py`（写入 `showcase/i18n-ext.json`，不覆盖已有条目）。
- 思维导图批量生成：`python scripts/gen_mindmaps.py`（写 YAML 并调 `svg_map.py` 出 SVG）。

> 注意：批量生成的中文名/介绍/导图是「可上线兜底」，关键/热门的技能仍需维护者人工润色后再过审。

