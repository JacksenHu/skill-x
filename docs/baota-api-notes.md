# 腾讯云专享版宝塔 API 能力边界与变通(实操记录)

站点:`skillx.yueliai.top`(香港 124.156.167.163)。所有操作经 `deploy/bt_deploy.py`(签名 `md5(request_time + md5(api_sk))`)。

## 一、API 可用面(实测)

| 模块 | 状态 | 说明 |
|---|---|---|
| `/site` | 部分可用 | 方法名**大小写敏感**:`get_site_types` 通、`AddSite` 需带 `project_type` 参数否则 404(且 404 不代表未执行,建站副作用会完成) |
| `/files` | 全可用 | 上传/解压/读写/复制/建目录/删除,是主要通道 |
| `/acme` | 可用 | `apply_cert_api`(超时属正常,订单已生成)→ `get_order_list` 取 index → `SetCertToSite`(**必须带 siteName**) |
| `/system` | 部分可用 | `ServiceAdmin` 对 **nginx 的 reload/restart 真实生效**;对 **sshd 是空转**(返回"执行成功"但配置未加载) |
| `/data` | 可用 | `getData(table=sites)` 取站点列表/ID |
| `/config` | 可用 | `get_config` 取面板配置 |

## 二、被裁掉的接口(专享版无此模块,勿再重复尝试)

- `/crontab`(计划任务增删查)、`/project` `/python` `/node`(项目管理)、`/safe` `/ssh` `/firewall`(安全/SSH 管理)、`/plugin`(插件安装)、进程管理(`KillProcess`/`GetProcessList`)

**结论**:计划任务、进程启停、SSH 加固、插件安装 → 只能面板网页手动操作;HTTP 场景变化后请先复核。

## 三、Windows 侧文件缺失时的替代信号

- 定位进程:用 `/files?action=GetDir` 列 `/proc`,再逐个读 `/proc/<pid>/cmdline`,即可找到目标进程 PID(无需 shell)

## 四、守护与自愈(必须绝对路径!)

计划任务(SHELL,每分钟)内容:

```bash
pgrep -f "[s]killx-api/server.py" >/dev/null || (cd /www/wwwroot/skillx-api && nohup python3 /www/wwwroot/skillx-api/server.py >> api.log 2>&1 &)
```

**两个坑**:
1. 启动必须用**绝对路径**(`python3 /www/wwwroot/skillx-api/server.py`)。若写成相对路径 `python3 server.py`,进程 cmdline 不含目录,"带路径的 pgrep 模式"永远匹配不到 → 守护每分钟空转、手动 `pkill -f "skillx-api/server.py"` 也杀不掉(实战踩过)
2. `pgrep` 模式用 `[s]` 字符类防自匹配

## 五、部署(纯净重放)

`deploy/sync.py`:构建 → tar → **先传包到站点父目录** → 删站点目录 → 重建 → 解压 → 清理临时包。
原因:tar 解压只覆盖同名文件,**不会删除已下架产物**(曾导致下架页仍可访问)。

后端更新:`sync.py --api` 上传 `server.py`/`registry.json`;server.py 内置 **mtime 热重载**(30 秒自检,变化则 `os.execv` 自重启)→ 上传即生效。首次引入热重载时仍需一次手动重启(旧进程无自检逻辑)。

## 六、敏感操作纪律

- `api_sk` 仅环境变量传入,不落盘、不入库
- 改动前备份(如 `/root/sshd_config.bak-<date>`);写 nginx vhost 前 `GetFileBody` 备份到 `deploy/nginx-backup/`
- 只碰 `skillx.yueliai.top`(站点 id=2)与 `skillx-api` 目录;同机 `lic.yueliai.top` 属他人业务,永不触碰
