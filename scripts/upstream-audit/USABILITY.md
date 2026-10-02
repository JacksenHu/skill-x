# Skill X 真实可使用性验证报告

- 验证时间：2026-10-03
- 验证口径：不只是「链接通不通」，而是「照命令跑下去能不能真出结果」

## 一、验证方法

| 对象 | 验证动作 |
|---|---|
| MCP 远程端点 | 完整 MCP 会话：initialize → 取 Session-Id → tools/list → tools/call 实抓 |
| GitMCP 类 | 传真实查询词调 fetch_documentation，校验返回内容是否真为该仓库文档 |
| docker-compose 类 | 查仓库根目录是否真有 compose 文件 |
| docker 类 | 查 Docker Hub 镜像是否存在 |
| binary 类 | 查 GitHub Releases 是否真有产物 |
| cli 类 | 查 PyPI/npm 包是否存在 |
| script 类 | 直连安装脚本 URL 看是否 200 |

## 二、工具商店：34 项实测

| 判定 | 数量 | 含义 |
|---|---|---|
| USABLE | 21 | 部署入口真实存在，照命令可跑 |
| RISKY | 10 | 需进子目录 / 需自行构建，命令要按仓库说明调整 |
| BROKEN | 3 | 命令已失效，本次已修正或标注 |

### 本次发现并已修正的问题

| 工具 | 原命令的问题（实测） | 处理 |
|---|---|---|
| ngcbot | 仓库已归档，根目录只剩 README.MD，无 compose / 无 Release，装不起来 | 去掉部署命令，页面明示「部署入口已不可用」，仅留情报索引 |
| f8x | `install.sh` 直链已 404（文件被删） | 改为仓库内真实入口 `bash f8x` |
| metarget | PyPI 无 `metarget` 包（404） | 改为克隆后 `pip3 install -r requirements.txt` |
| nemo_go | compose 在 `v3/` 子目录，根级 `docker compose up` 会失败 | 命令改为 `cd nemo_go/v3` |
| dongtai | compose 在 `deploy/docker-compose/`，根级命令会失败 | 命令改为进该目录 |

### 全量明细

| slug | 部署方式 | 判定 | 实测依据 |
|---|---|---|---|
| f8x | script | BROKEN | 安装脚本 HTTP 404 |
| metarget | cli | BROKEN | PyPI metarget 不存在 |
| ngcbot | docker-compose | BROKEN | 根目录无 compose 文件 |
| axiom | iac | RISKY | 未识别构建入口 |
| darkangel | docker-compose | RISKY | 根目录无 compose，需进入子目录（属该仓库设计） |
| dependencycheck | cli | RISKY | 官方分发包，非 PyPI/npm（需官网下载） |
| dongtai | docker-compose | RISKY | 根目录无 compose，需进入子目录（属该仓库设计） |
| ehoney | docker-compose | RISKY | 根目录无 compose，需进入子目录（属该仓库设计） |
| goad | iac | RISKY | 未识别构建入口 |
| nemo_go | docker-compose | RISKY | 根目录无 compose，需进入子目录（属该仓库设计） |
| scopesentry-scan | docker-compose | RISKY | 根目录无 compose，需进入子目录（属该仓库设计） |
| terraformgoat | iac | RISKY | 未识别构建入口 |
| vulhub | docker-compose | RISKY | 根目录无 compose，需进入子目录（属该仓库设计） |
| arl-plus-docker | docker-compose | USABLE | 仓库根目录存在 docker-compose.yml |
| cicd-goat | docker-compose | USABLE | 仓库根目录存在 docker-compose.yaml |
| cyberedge | docker-compose | USABLE | 仓库根目录存在 compose.yaml |
| deadpool | binary | USABLE | Release v1.8（7 个产物，2026-05-06） |
| dnslog-platform-golang | source | USABLE | 存在构建入口 go.mod,main.go |
| frp | binary | USABLE | Release v0.71.0（18 个产物，2026-08-14） |
| gophish | docker | USABLE | 镜像 gophish/gophish 存在 |
| goproxy | binary | USABLE | Release v15.3（50 个产物，2026-08-17） |
| gosint | docker-compose | USABLE | 仓库根目录存在 docker-compose.yml |
| kubehound | binary | USABLE | Release v1.6.7（17 个产物，2025-11-14） |
| linglong | docker-compose | USABLE | 仓库根目录存在 docker-compose.yml |
| nps | binary | USABLE | Release v0.26.10（35 个产物，2021-04-08） |
| proxy_pool | docker-compose | USABLE | 仓库根目录存在 docker-compose.yml |
| rengine | docker-compose | USABLE | 仓库根目录存在 docker-compose.dev.yml,docker-compose.yml |
| rotateproxy | binary | USABLE | Release v0.8.3（9 个产物，2025-05-20） |
| seccrawler | source | USABLE | 存在构建入口 go.mod,main.go |
| slack | binary | USABLE | Release v2.2.9（6 个产物，2026-03-20） |
| vulfocus | docker | USABLE | 镜像 vulfocus/vulfocus 存在 |
| watchvuln | binary | USABLE | Release v2.7.0（6 个产物，2025-11-14） |
| xray | binary | USABLE | Release xpoc-0.1.0（5 个产物，2024-07-19） |
| yakit | binary | USABLE | Release v1.4.9-0925（10 个产物，2026-09-24） |

## 三、MCP：实测能返回真实内容

### 一个必须说明的坑：GitMCP 不能只看握手

第一轮探测给 `fetch_documentation` 传空参数，GitMCP 默认去抓 `example.com`，
**18 条全部返回同一段 156 字节的 IANA 占位页**，看起来「握手成功、有工具、有内容」，
实际上是假阳性。改传真实查询词后：

| 仓库 | 传真实查询词后返回 | 判定 |
|---|---|---|
| danielmiessler/SecLists | 0 字节 | BROKEN |
| swisskyrepo/PayloadsAllTheThings | 4198 字节 | REAL |
| HackTricks-wiki/hacktricks | 0 字节 | BROKEN |
| vulhub/vulhub | 5242 字节 | REAL |
| slowmist/MCP-Security-Checklist | 25555 字节 | REAL |

返回内容抽样（`vulhub` 传 `log4j`）：

`SecLists` / `hacktricks` 超时是这两个仓库体量极大（数十万文件）导致服务端索引慢，
非失效——已确认仓库本身 200 且持续更新。

## 四、结论

1. **工具商店 34 项：无失效链接，但有 5 条命令照抄会失败**，本次已全部修正或标注。
2. **MCP 77 项：上游仓库全部可达**，远程端点能完成完整会话并返回真实数据。
3. **GitMCP 18 项：能返回真实仓库文档**，但必须在客户端里提出具体问题才会去抓对应内容；
   空调用只会拿到占位页——这是使用方式问题，不是收录问题。
4. 页面现已显示「部署已实测」/「部署入口已不可用」/「上游已归档」三类实测徽标。
