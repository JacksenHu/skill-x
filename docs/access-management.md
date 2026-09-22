# 授权与安装管理

Skill X 仓库为**私有**。本文件说明授权发放方式与被授权者的安装方法。

## 对被授权者:三种安装方式(任选其一)

### 方式 1:gh CLI(推荐,零配置)

```bash
gh auth login                       # 一次性,浏览器授权
GITHUB_TOKEN=$(gh auth token) npx skills add JacksenHu/skill-x --list
GITHUB_TOKEN=$(gh auth token) npx skills add JacksenHu/skill-x --skill <name>
```

### 方式 2:细粒度 PAT

申请一个 Fine-grained Personal Access Token:
- GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
- Repository access:**Only select repositories → skill-x**
- Permissions:**Contents: Read-only**(安装只需要读)

```bash
GITHUB_TOKEN=<你的PAT> npx skills add JacksenHu/skill-x --skill <name>
# Windows PowerShell:
$env:GITHUB_TOKEN="<你的PAT>"; npx skills add JacksenHu/skill-x --skill <name>
```

### 方式 3:SSH(已配 SSH key 的用户;主站受限网络下推荐)

```bash
npx skills add git@github.com:JacksenHu/skill-x.git --skill <name>
```

skills CLI 凭据回退顺序:git 凭据 → gh → SSH;显式 `GITHUB_TOKEN`/`GH_TOKEN` 环境变量优先。

## 网络环境说明(https clone 失败时)

症状:`npx skills add JacksenHu/skill-x` 报 `schannel: server closed abruptly` 或长时间卡在 Cloning。

原因:CLI 的 `owner/repo` 简写走 `https://github.com` 克隆;在 github.com 主站被拦截/代理白名单缺失的网络下必败(实测于 2026-09-22)。**SSH 通道不受影响。**

对策(任选):
1. 直接用 SSH 形式(方式 3),无需任何配置;
2. 或配置 git 全局重写,让所有 https GitHub 访问自动改走 SSH(对本机所有工具生效):
   ```bash
   git config --global url."git@github.com:".insteadOf "https://github.com/"
   ```
3. 能正常访问 github.com 主站的网络,方式 1/2 均可。

### 指定目标 agent

```bash
# 列出后安装到指定 agent(如 codebuddy / claude-code / cursor / codex)
npx skills add JacksenHu/skill-x --skill <name> -a <agent> -g -y
```

## 对维护者:授权发放

### 加协作者(适合固定成员,可读可推送可选)

```bash
gh api repos/JacksenHu/skill-x/collaborators/<github-username> -X PUT -f permission=pull
```

### 建议

- 临时用户发 PAT(方式 2),可随时吊销,最小权限 Contents:read
- 固定维护成员加 Collaborator(permission=pull 只读 / push 可写)
- 定期 `gh api repos/JacksenHu/skill-x/collaborators` 审查名单

## 红线

- 橱窗站(EdgeOne)只展示自研 skill 的元数据;SKILL.md 正文只存在于本私有仓库,不得复制到任何公开位置
- PAT 不出现在文档、截图、聊天记录中
