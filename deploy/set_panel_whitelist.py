#!/usr/bin/env python3
"""调整宝塔面板 API 的 IP 白名单(config/api.json 的 limit_addr)。

面板 API 除白名单外还有 api_sk(request_token)校验,清空白名单不等于裸奔。

用法:
  python deploy/set_panel_whitelist.py --show
  python deploy/set_panel_whitelist.py --open              # 清空 = 放行所有 IP
  python deploy/set_panel_whitelist.py --add 20.* 4.* 13.*  # 追加通配符
  python deploy/set_panel_whitelist.py --restore           # 回滚到最近一次备份
"""
import base64
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paramiko  # noqa: E402

HOST = os.environ.get("SKILLX_SSH_HOST", "124.156.167.163")
USER = os.environ.get("SKILLX_SSH_USER", "root")
KEY = os.environ.get("SKILLX_SSH_KEY",
                     r"C:\Users\24664\workbuddy-ai\天穹\.workbuddy-ai\keys\id_ed25519")
CFG = "/www/server/panel/config/api.json"

REMOTE_SHOW = """
import json
d = json.load(open('%s'))
print('open =', d.get('open'))
print('limit_addr =', d.get('limit_addr'))
print('count =', len(d.get('limit_addr') or []))
""" % CFG

REMOTE_OPEN = """
import json, shutil, time
p = '%s'
shutil.copy(p, p + '.bak.' + time.strftime('%%Y%%m%%d-%%H%%M%%S'))
d = json.load(open(p))
d['limit_addr'] = []
json.dump(d, open(p, 'w'), ensure_ascii=False)
print('NEW limit_addr =', d['limit_addr'])
""" % CFG

REMOTE_RESTORE = """
import glob, shutil
p = '%s'
baks = sorted(glob.glob(p + '.bak.*'))
if not baks:
    print('没有备份可回滚'); raise SystemExit(1)
shutil.copy(baks[-1], p)
print('已回滚自', baks[-1])
""" % CFG


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--show"
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, username=USER, key_filename=KEY, timeout=30)

    def run(code):
        b64 = base64.b64encode(code.encode("utf-8")).decode("ascii")
        _, out, err = cli.exec_command("echo %s | base64 -d | python3 -" % b64, timeout=120)
        o = out.read().decode("utf-8", "replace").strip()
        e = err.read().decode("utf-8", "replace").strip()
        code_rc = out.channel.recv_exit_status()
        if o:
            print(o)
        if e:
            print("[stderr]", e)
        return code_rc

    if mode == "--show":
        rc = run(REMOTE_SHOW)
    elif mode == "--open":
        rc = run(REMOTE_OPEN)
    elif mode == "--restore":
        rc = run(REMOTE_RESTORE)
    elif mode == "--add":
        extra = sys.argv[2:]
        code = """
import json, shutil, time
p = '%s'
shutil.copy(p, p + '.bak.' + time.strftime('%%Y%%m%%d-%%H%%M%%S'))
d = json.load(open(p))
cur = list(d.get('limit_addr') or [])
for x in %r:
    if x not in cur:
        cur.append(x)
d['limit_addr'] = cur
json.dump(d, open(p, 'w'), ensure_ascii=False)
print('NEW limit_addr =', cur)
""" % (CFG, extra)
        rc = run(code)
    else:
        print(__doc__)
        return 2

    cli.close()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
