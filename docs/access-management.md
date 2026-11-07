# 安装说明

Skill X 仓库**公开**，安装不需要任何凭据。

## 安装

```bash
# 列出库内全部 skill
npx skills add JacksenHu/skill-x --list

# 安装指定 skill（自动检测本机 agent：claude-code / cursor / codex ...）
npx skills add JacksenHu/skill-x --skill <name>

# 安装到指定 agent
npx skills add JacksenHu/skill-x --skill <name> -a <agent> -g -y
```

## 网络受限时

症状：`npx skills add JacksenHu/skill-x` 报 `schannel: server closed abruptly` 或长时间卡在 Cloning。

原因：CLI 的 `owner/repo` 简写走 `https://github.com` 克隆；在 github.com 被拦截/代理白名单缺失的网络下会失败。

对策（任选）：

1. 用 SSH 形式（需本机已配置 SSH key）：
   ```bash
   npx skills add git@github.com:JacksenHu/skill-x.git --skill <name>
   ```
2. 或让所有 https GitHub 访问改走 SSH：
   ```bash
   git config --global url."git@github.com:".insteadOf "https://github.com/"
   ```
3. 能正常访问 github.com 的网络，直接装即可。

## 本站下载代理

`GET /dl/<ns>/<skill>.tar.gz` 只服务 `external.json` 里已收录的外部套件（重打包为 `<skill>/` 根，带磁盘缓存）。
本站技能库（`skills/<name>/`）直接用上面的 `npx skills add` 安装，不走代理。

## 维护者

- 仓库公开，不需要再发放 PAT 或添加只读协作者。
- 写入权限仍由 GitHub 仓库 Settings → Collaborators 控制（push 权限）。
- 外部套件收录与许可证核查见 [接入 SOP](onboarding-pipeline.md)。
