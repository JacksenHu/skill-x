# Lessons — 永久教训(踩过第二次的坑才进这里;动手前先扫一眼)

## 服务器 / 宝塔(腾讯云专享版)

1. **API 只开放基础模块**:`/site` `/files` `/acme` `/system`(部分)`/data` `/config` 可用;`crontab`(计划任务)、`/project`(项目)、`/safe` `/ssh` `/firewall`(安全)、`/plugin`、进程管理(KillProcess/GetProcessList)**全被裁**。计划任务、进程启停、SSH 加固只能面板手动。
2. **`system/ServiceAdmin` 不可全信**:对 nginx 的 reload/restart 真实生效;对 sshd 是空转(返回"执行成功"但配置根本没加载)。
3. **方法名大小写敏感**:`get_site_types` 通,`AddSite` 需带 `project_type`;404 不代表未执行(建站副作用会完成),要用 `getData` 判存在性。
4. **有 IP 白名单**,本机出口 IP 是动态池 → 建议填段(219.132.*),否则每次换 IP 就要手动放行。
5. **无 shell 也能定位进程**:用 `files/GetDir` 列 `/proc`,再读 `/proc/<pid>/cmdline`。
6. 改动前先备份:`/root/sshd_config.bak-<date>`;nginx vhost 由 `GetFileBody` 备份到 `deploy/nginx-backup/`。

## 部署

7. **tar 解压不删除旧文件** → 必须"纯净重放"(删站目录→重建→解压),否则下架的技能页仍可访问(实测踩过)。
8. 上传包先放**站点父目录**,再删站重建,失败时包还在、可重试。

## 进程守护

9. **守护脚本必须用绝对路径启动**(`python3 /www/wwwroot/skillx-api/server.py`)。写成相对路径时,进程 cmdline 不含目录,"带路径的 pgrep 模式"永不匹配 → 守护从加上起就从未生效(踩过,排查了很久)。
10. pgrep 模式用 `[s]` 字符类防自匹配。
11. **热重载是新代码才有的能力**:首次引入时旧进程没有自检逻辑,仍需一次手动重启(鸡生蛋),之后才全自动。

## 验证与工具

12. **`curl -o /dev/null` 在 Git Bash 会 exit 23 提前断开**,`size_download` 显示 0 → 下载类验收必须 `-o` 真实文件再看大小(曾被"0B 假象"误导)。
13. **审计用正则会误报**:字符串里的 `socket`、try/except 包裹的可选依赖都会命中 → 危险调用/依赖必须 AST 级判定并区分"功能所需"与"可疑"。
14. 重打包上游 tar 时,目录前缀要按 `skills/<skill>/SKILL.md` 精确匹配;否则会误取 `evals/fixtures/` 下的同名目录。

## 本地 git(本机环境)

15. `refs/remotes` 写入不可靠(fetch 报成功但不落盘):merge/pull 用 `FETCH_HEAD` 而非 `origin/main`;push 用 `git push origin main`。
16. 曾发生 `.git` 目录整体消失(工作区完好)→ 恢复:init + fetch + `reset --mixed FETCH_HEAD` + 重新提交。**提交后立即 push**,以 GitHub 为唯一真相源。

## 代码改造

17. **按函数名切片替换前,先确认区间内夹着哪些定义**:替换 `render_index` → `render_own_detail` 之间的内容时,误删了中间的 `load_audit` / `render_audit_block`(踩过,构建才报错)。
18. SVG 输出用**单引号**(`class='node'`),grep 双引号会误判为 0;深色主题下导图的背景 rect 要用 `fill='none'`,否则出现白块。
19. 严格 CSP 下**不能用 inline style**:分类色等动态样式走 class(`.cat-<key>{--cat:...}`)。
20. 生成器代码(svg_map / apidocs)改动后,增量 key 必须包含其源码哈希,否则产物不刷新。
