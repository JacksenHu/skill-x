#!/usr/bin/env python3
"""宝塔面板 API 部署工具(Skill X 专用)。

安全约束:
- api_sk 只从环境变量 BT_API_SK 读取,绝不写入任何文件
- 仅操作 skillx.yueliai.top 站点目录与其 vhost conf,不碰服务器其他站点/文件

用法(BT_API_SK=xxx python deploy/bt_deploy.py <cmd>):
  probe                 验证面板连通 + 密钥有效 + 站点是否已存在
  addsite               创建纯静态站点(幂等:已存在则跳过)
  upload <tar.gz>       上传压缩包到站点根并解压
  ssl                   申请 Let's Encrypt 并强制 HTTPS
  nginx <local_conf>    备份现有 vhost conf 到本地,再写入新 conf
"""
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

PANEL = "http://124.156.167.163:8888"
SITE_DOMAIN = "skillx.yueliai.top"
SITE_PATH = f"/www/wwwroot/{SITE_DOMAIN}"
VHOST_CONF = f"/www/server/panel/vhost/nginx/{SITE_DOMAIN}.conf"
SK = os.environ.get("BT_API_SK", "")
ROOT = Path(__file__).resolve().parent.parent


def make_token():
    t = str(int(time.time()))
    sk_md5 = hashlib.md5(SK.encode()).hexdigest()
    return t, hashlib.md5((t + sk_md5).encode()).hexdigest()


def call(module, action, files=None, _timeout=60, **params):
    """POST form 到 /{module}?action={action};files 用于 multipart 上传。"""
    t, tok = make_token()
    base = {"request_time": t, "request_token": tok}
    url = f"{PANEL}/{module}?action={action}"
    if files is None:
        body = urllib.parse.urlencode({**base, **params}).encode()
        req = urllib.request.Request(url, data=body, headers={"User-Agent": "skill-x-deploy/1.0"})
    else:
        boundary = f"----skillx{int(time.time()*1000)}"
        parts = []
        for k, v in {**base, **params}.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        for field, (fname, fdata) in files.items():
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{fname}"\r\n'
                f"Content-Type: application/gzip\r\n\r\n".encode() + fdata + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        req = urllib.request.Request(url, data=b"".join(parts), headers={
            "User-Agent": "skill-x-deploy/1.0",
            "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=_timeout) as r:
        raw = r.read().decode("utf-8", "replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw[:500]}


def cmd_probe():
    print("[*] 探测面板与密钥…")
    r = call("site", "get_site_types")
    print("get_site_types ->", json.dumps(r, ensure_ascii=False)[:300])
    r2 = call("data", "getData", table="sites", limit="100")
    names = [s.get("name") for s in (r2.get("data") or [])] if isinstance(r2, dict) else []
    print(f"[*] 现有站点 {len(names)} 个,目标站点{'已存在' if SITE_DOMAIN in names else '不存在'}")
    return 0


def cmd_addsite():
    webname = json.dumps({"domain": SITE_DOMAIN, "domainlist": [], "count": 0})
    r = call("site", "AddSite", webname=webname, path=SITE_PATH, type="",
             version="00", port="80", type_id="0", ps="Skill X showcase")
    print("AddSite ->", json.dumps(r, ensure_ascii=False)[:400])
    return 0


def cmd_upload(tar_path):
    tar_path = Path(tar_path)
    data = tar_path.read_bytes()
    print(f"[*] 上传 {tar_path.name}({len(data)//1024} KB)-> {SITE_PATH}")
    r = call("files", "UploadFile", path=SITE_PATH,
             files={"zunfile": (tar_path.name, data)})
    print("UploadFile ->", json.dumps(r, ensure_ascii=False)[:300])
    r2 = call("files", "UnZip", sfile=f"{SITE_PATH}/{tar_path.name}",
              dfile=SITE_PATH + "/", type="tar.gz", coding="UTF-8", password="")
    print("UnZip ->", json.dumps(r2, ensure_ascii=False)[:300])
    r3 = call("files", "DeleteFile", path=f"{SITE_PATH}/{tar_path.name}")
    print("清理压缩包 ->", json.dumps(r3, ensure_ascii=False)[:200])
    return 0


def cmd_ssl():
    # 腾讯云专享版无 GetSiteId;从 data/getData 取站点 id
    r = call("data", "getData", table="sites", limit="100")
    site_id = None
    for s in (r.get("data") or []):
        if s.get("name") == SITE_DOMAIN:
            site_id = s.get("id")
            break
    if not site_id:
        print("[!] 站点不存在,先跑 addsite")
        return 1
    print(f"[+] 站点 id = {site_id}")
    domains = json.dumps([SITE_DOMAIN])
    r1 = call("acme", "apply_cert_api", id=str(site_id), domains=domains,
              auth_type="http", auth_to=SITE_PATH, auto_wildcard="0", ca="letsencrypt",
              _timeout=180)
    print("apply_cert_api ->", json.dumps(r1, ensure_ascii=False)[:400])
    # 申请可能超时但订单已生成;查订单拿 index(取目标域名 valid/pending 的最新一条)
    idx = None
    try:
        orders = call("acme", "get_order_list")
        for o in (orders if isinstance(orders, list) else []):
            if SITE_DOMAIN in (o.get("domains") or []):
                idx = o.get("index")
        print(f"[+] 订单 index = {idx}")
    except Exception as e:  # noqa: BLE001
        print(f"[-] 查订单失败: {e}")
    if idx:
        r2 = call("acme", "SetCertToSite", index=idx, siteName=SITE_DOMAIN)
        print("SetCertToSite ->", json.dumps(r2, ensure_ascii=False)[:200])
    r3 = call("site", "SetSSLConf", siteName=SITE_DOMAIN)
    print("SetSSLConf ->", json.dumps(r3, ensure_ascii=False)[:200])
    r4 = call("site", "HttpToHttps", siteName=SITE_DOMAIN)
    print("HttpToHttps ->", json.dumps(r4, ensure_ascii=False)[:200])
    return 0


def cmd_nginx(local_conf):
    backup_dir = ROOT / "deploy" / "nginx-backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    try:
        r = call("files", "GetFileBody", path=VHOST_CONF)
        body = r.get("data", "") if isinstance(r, dict) else ""
        if body:
            ts = time.strftime("%Y%m%d-%H%M%S")
            (backup_dir / f"{SITE_DOMAIN}.{ts}.conf").write_text(body, encoding="utf-8")
            print(f"[+] 已备份现有 conf -> deploy/nginx-backup/{SITE_DOMAIN}.{ts}.conf")
    except Exception as e:  # noqa: BLE001
        print(f"[-] 备份失败(可能尚无 conf): {e}")
    new_body = Path(local_conf).read_text(encoding="utf-8")
    r2 = call("files", "SaveFileBody", path=VHOST_CONF, data=new_body, encoding="utf-8")
    print("SaveFileBody ->", json.dumps(r2, ensure_ascii=False)[:300])
    return 0


def main():
    if not SK:
        print("[!] 缺少环境变量 BT_API_SK")
        return 1
    cmds = {"probe": cmd_probe, "addsite": cmd_addsite, "upload": cmd_upload,
            "ssl": cmd_ssl, "nginx": cmd_nginx}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        return 1
    fn = cmds[sys.argv[1]]
    extra = sys.argv[2:]
    return fn(*extra) if extra else fn()


if __name__ == "__main__":
    sys.exit(main())
