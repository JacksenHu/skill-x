# 套件 / Skill 接入管线(维护 SOP)

> 适用范围:任何需要接入本 hub 的外部套件或单个 skill。
> 输入只是一个链接,输出是完成收录 + 橱窗更新 + 验证报告。全程照本管线执行,不跳步。

## 第 0 步:识别来源并拉取

| 来源格式 | 示例 | 拉取方式 |
|---|---|---|
| GitHub 简写 | `owner/repo` | `git clone --depth 1 https://github.com/owner/repo` |
| SSH | `git@github.com:owner/repo.git` | `git clone --depth 1`(需凭据) |
| ZIP 直链 | `https://example.com/marketplace.zip` | 下载解压(≤10 MiB,超限先报备) |
| 本地路径 | `./path/to/marketplace` | 直接读取 |

## 第 1 步:清点

1. manifest 发现优先级:`.claude-plugin/marketplace.json` → `.codex-plugin/plugin.json` → `.well-known/skills/index.json` → 扫描 `skills/` 目录(≤3 层)
2. 产出 skill 清单:name / description / version / 路径
3. 列出**全部可执行面**:
   ```bash
   find . -type f \( -name "*.sh" -o -name "*.py" -o -name "*.js" -o -path "*/hooks/*" -o -path "*/scripts/*" \)
   ```

## 第 2 步:四坑检查(逐项出结论,不许"看着没问题")

### 2.1 命名空间
- 收录条目一律加 `owner/name` 前缀,与本站技能库隔离
- 与库内已有条目(本站 + 已收录)查重,撞名则加来源后缀

### 2.2 许可证
- 白名单:`MIT` / `Apache-2.0` / `BSD-2-Clause` / `BSD-3-Clause` / `ISC` / `CC-BY-4.0`
- 收录时保留 LICENSE 文件与作者署名
- **无许可证或许可证不在白名单** → 只收录元数据 + 安装链接(不镜像内容),标注"许可证未确认"

### 2.3 供应链安全
逐个审查第 1 步列出的可执行文件,红线特征命中即拒收:
- 未在文档中声明的网络外联
- 读取凭证 / 环境变量并外传
- 混淆、base64 藏码、动态执行下载物(`curl ... | sh` 类)
- 安装即自动执行的钩子(hooks 自动跑脚本)
- 命中 → **拒绝收录**,附证据报告

### 2.4 死链
- `external.json` 记录 upstream URL 与收录日期
- CI 每日探活(HEAD 请求):挂了 → 橱窗标注"上游失联";连续 7 天失联 → 下架条目

## 第 3 步:收录

图标规则:每个展示条目默认使用 showcase/assets/avatars/icon-default.svg 占位图标;上游自带图标时,在 showcase/i18n-ext.json 的对应条目补 icon 字段指向官方图标。

新增收录默认以中文展示:除 external.json 外,同步在 `showcase/i18n-ext.json` 为该套件每个展示条目补 `name-zh` / `description-zh` / `category`;未提供中文的条目不得进入橱窗。

向 `external.json` 追加条目:

```json
{
  "name": "owner/skill-name",
  "upstream": { "type": "git|zip|local", "url": "...", "ref": "main", "path": "skills/xxx" },
  "description": "...", "version": "...", "license": "MIT",
  "verified": false,
  "install": "npx skills add owner/repo --skill skill-name",
  "added": "YYYY-MM-DD"
}
```

许可证允许时,同时缓存 frontmatter + 正文用于介绍页;否则只存元数据 + 链接。

## 第 4 步:验证与报告

1. 实际执行安装命令,确认可装、`SKILL.md` 可被发现
2. 输出报告:收录清单 / 四坑逐项结论(通过|标注|拒收) / 验证结果 / 残留风险
