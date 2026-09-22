# 手动建站回退指引(api_sk 不可用时)

仅需 5 分钟,在宝塔面板网页操作。**全程不碰其他站点。**

## 1. 建站

面板 → 网站 → 添加站点:
- 域名:`skillx.yueliai.top`
- 根目录:默认 `/www/wwwroot/skillx.yueliai.top`
- PHP 版本:**纯静态**
- 数据库/FTP:均不创建

## 2. 传文件

1. 本地打包:仓库 `showcase/dist/` 内容已打成 `showcase/skillx-dist.tar.gz`(由 jacksen 构建)
2. 面板 → 文件 → 进入 `/www/wwwroot/skillx.yueliai.top/` → 上传该 tar.gz → 右键解压 → 删除压缩包
   (或把 tar.gz 发给服务器后 `tar -xzf skillx-dist.tar.gz -C /www/wwwroot/skillx.yueliai.top/`)

## 3. SSL

站点 `skillx.yueliai.top` → 设置 → SSL → Let's Encrypt → 勾选域名 → 申请 → 开启"强制 HTTPS"。

## 4. 安全基线(可选但建议)

站点设置 → 配置文件,在 443 server 块内追加:

```nginx
server_tokens off;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=31536000" always;
```

参考完整配置:`deploy/nginx/skillx.yueliai.top.conf`(注意证书路径以面板实际生成位置为准)。

## 5. 验收

浏览器打开 `https://skillx.yueliai.top`,应看到 Skill X 橱窗首页(自研 5 + 收录 34,可搜索)。
