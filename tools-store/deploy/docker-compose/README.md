# docker-compose 模板说明

本目录存放可直接被第三方工具商店用于「一键部署」的 compose 模板。

## 已提供的官方/镜像模板

| 文件 | 工具 | 说明 |
| --- | --- | --- |
| `rengine.docker-compose.yml` | reNgine | 官方源码 build 版（需要先 clone 仓库，因 celery/web 均为 `build: ./web`） |
| `arl-plus.docker-compose.yml` | ARL-Plus | 镜像版（`ki9mu/arl-ki9mu:v3.0.1`），clone 仓库后 `docker compose up -d` |
| `proxy-pool.docker-compose.yml` | proxy_pool | 官方源码 build 版（`build: .`） |
| `gophish.docker-compose.yml` | GoPhish | 官方镜像 `gophish/gophish`，可直接 `docker compose up -d` |
| `vulfocus.docker-compose.yml` | Vulfocus | 官方镜像 `vulfocus/vulfocus`，可直接 `docker compose up -d` |

## 其余 docker-compose 型工具

其余工具（Nemo、ScopeSentry、CyberEdge、linglong、gosint、Ehoney、DarkAngel、DongTai、
NGCBot、CI/CD Goat 等）的上线方式统一为「clone 仓库后使用仓库自带 docker-compose」，
原因是它们多为源码 build 或多文件部署，官方 compose 随版本变化。工具商店应把它们的
部署动作抽象为：

```
git clone <repo_url>
cd <repo>
docker compose up -d
```

对应的具体入口统一记录在 `catalog.json` 的 `install` 字段中。
