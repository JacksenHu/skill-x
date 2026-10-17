#!/usr/bin/env bash
# 在服务器上执行:解压新产物 -> 原子替换站点目录 -> 修正属主 -> reload nginx
# 由 .github/workflows/deploy.yml 通过 ssh 'bash -s' 调用。
set -euo pipefail

SITE=/www/wwwroot/skillx.yueliai.top
STAGE=/www/wwwroot/.skillx-stage
OLD=/www/wwwroot/.skillx-old
TAR=/www/wwwroot/skillx-dist.tar.gz

rm -rf "$STAGE"
mkdir -p "$STAGE"
tar xzf "$TAR" -C "$STAGE"
test -f "$STAGE/index.html"
test -d "$STAGE/tools"

rm -rf "$OLD"
mv "$SITE" "$OLD"
mv "$STAGE" "$SITE"
chown -R www:www "$SITE"

nginx -t
(nginx -s reload 2>/dev/null) || (systemctl reload nginx) || (/etc/init.d/nginx reload)

rm -rf "$OLD"
rm -f "$TAR"
echo "[+] 站点已替换,当前顶层:"
ls "$SITE" | head -6
