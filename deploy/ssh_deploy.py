#!/usr/bin/env python3
"""Skill X 站点 SSH 部署通道(宝塔 API 受限时的备用方案)。

用法:
  python deploy/ssh_deploy.py            # 打包 + 上传 + 原子替换 + reload
  python deploy/ssh_deploy.py --skip-build   # 复用现有 showcase/dist

流程:
  1. 本地打包 showcase/dist -> showcase/skillx-dist.tar.gz
  2. SFTP 上传到 /www/wwwroot/
  3. 远端解压到暂存目录并校验(index.html 必须存在)
  4. 原子替换站点目录:旧目录先改名保留,新目录就位;任一步失败即中止
  5. 上传 API 后端(server.py/registry.json 到 skillx-api;mcp-registry/packs 到父目录)
  6. nginx -t 通过后 reload,最后清理备份与压缩包
"""
import os
import subprocess
import sys
import tarfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paramiko  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "showcase" / "dist"
TAR = ROOT / "showcase" / "skillx-dist.tar.gz"

HOST = os.environ.get("SKILLX_SSH_HOST", "124.156.167.163")
USER = os.environ.get("SKILLX_SSH_USER", "root")
KEY = os.environ.get("SKILLX_SSH_KEY",
                     r"C:\Users\24664\workbuddy-ai\天穹\.workbuddy-ai\keys\id_ed25519")
SITE = "/www/wwwroot/skillx.yueliai.top"
STAGE = "/www/wwwroot/.skillx-stage"
OLD = "/www/wwwroot/.skillx-old"
REMOTE_TAR = "/www/wwwroot/skillx-dist.tar.gz"


def build():
    if "--skip-build" not in sys.argv:
        print("[*] 构建 dist …")
        r = subprocess.run([sys.executable, str(ROOT / "showcase" / "build_index.py")],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        tail = (r.stdout or r.stderr or "").strip().splitlines()[-3:]
        for line in tail:
            print("   ", line)
        if r.returncode != 0:
            raise RuntimeError("本地构建失败")
    if TAR.exists():
        TAR.unlink()
    with tarfile.open(TAR, "w:gz") as tf:
        tf.add(DIST, arcname=".")
    print("[+] 打包 %s(%d KB)" % (TAR.name, TAR.stat().st_size // 1024))


def run(cli, cmd, check=True):
    _, out, err = cli.exec_command(cmd, timeout=600)
    o = out.read().decode("utf-8", "replace").strip()
    e = err.read().decode("utf-8", "replace").strip()
    code = out.channel.recv_exit_status()
    if o:
        print("   " + o.replace("\n", "\n   "))
    if e:
        print("   [stderr] " + e.replace("\n", "\n   "))
    if check and code != 0:
        raise RuntimeError("远端命令失败(%d): %s" % (code, cmd[:120]))
    return code


def main():
    build()
    print("[*] 连接 %s …" % HOST)
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, username=USER, key_filename=KEY, timeout=30)
    sftp = cli.open_sftp()

    print("[*] 上传压缩包 …")
    sftp.put(str(TAR), REMOTE_TAR)
    print("    ok")

    print("[*] 远端解压 + 原子替换 …")
    run(cli, "set -e; rm -rf %s; mkdir -p %s; tar xzf %s -C %s; "
             "test -f %s/index.html; test -d %s/tools" % (STAGE, STAGE, REMOTE_TAR, STAGE, STAGE, STAGE))
    # 站点属主必须是 www(nginx 运行用户),否则解压出的 root 文件 nginx 读不到
    run(cli, "set -e; rm -rf %s; mv %s %s; mv %s %s; chown -R www:www %s" % (OLD, SITE, OLD, STAGE, SITE, SITE))
    print("    站点目录已替换")

    print("[*] 上传 API 后端 …")
    run(cli, "mkdir -p /www/wwwroot/skillx-api")
    for name in ("server.py", "registry.json"):
        src = ROOT / "api" / name
        if src.is_file():
            sftp.put(str(src), "/www/wwwroot/skillx-api/" + name)
            print("    api/%s" % name)
    for name in ("mcp-registry.json", "packs.json"):
        src = ROOT / name
        if src.is_file():
            sftp.put(str(src), "/www/wwwroot/" + name)
            print("    %s" % name)

    print("[*] nginx 校验 + reload …")
    run(cli, "nginx -t")
    run(cli, "(nginx -s reload 2>/dev/null) || (systemctl reload nginx) || (/etc/init.d/nginx reload)")

    print("[*] 清理 …")
    run(cli, "rm -rf %s; rm -f %s" % (OLD, REMOTE_TAR))
    run(cli, "ls %s | head -6" % SITE)

    sftp.close()
    cli.close()
    print("[+] 部署完成 -> https://skillx.yueliai.top")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print("[!] 部署失败: %s" % exc)
        sys.exit(1)
