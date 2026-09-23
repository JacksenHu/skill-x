#!/usr/bin/env python3
"""Skill X 一键构建 + 部署(本地构建 → 宝塔 API 上传 → 站点生效)。

用法:
  BT_API_SK=xxx python deploy/sync.py              # 构建 + 部署
  BT_API_SK=xxx python deploy/sync.py --skip-build # 只部署当前 dist
  BT_API_SK=xxx python deploy/sync.py --reload     # 部署后 reload nginx
"""
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bt_deploy import SITE_PATH, call  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "showcase" / "dist"
TAR = ROOT / "showcase" / "skillx-dist.tar.gz"


def main():
    if "--skip-build" not in sys.argv:
        print("[*] 构建 dist …")
        r = subprocess.run([sys.executable, str(ROOT / "showcase" / "build_index.py")],
                           capture_output=True, text=True)
        print((r.stdout or r.stderr).strip())
        if r.returncode != 0:
            print("[!] 构建失败,中止")
            return 1

    if TAR.exists():
        TAR.unlink()
    with tarfile.open(TAR, "w:gz") as tf:
        tf.add(DIST, arcname=".")
    print(f"[+] 打包 {TAR.name}({TAR.stat().st_size // 1024} KB)")

    data = TAR.read_bytes()
    r1 = call("files", "UploadFile", path=SITE_PATH, files={"zunfile": (TAR.name, data)})
    print("UploadFile ->", r1.get("msg"))
    r2 = call("files", "UnZip", sfile=f"{SITE_PATH}/{TAR.name}", dfile=SITE_PATH + "/",
              type="tar.gz", coding="UTF-8", password="")
    print("UnZip ->", r2.get("msg"))
    r3 = call("files", "DeleteFile", path=f"{SITE_PATH}/{TAR.name}")
    print("清理 ->", r3.get("msg"))
    if r1.get("status") and r2.get("status"):
        if "--reload" in sys.argv:
            r4 = call("system", "ServiceAdmin", name="nginx", type="reload")
            print("nginx reload ->", r4.get("msg"))
        print("[+] 部署完成 -> https://skillx.yueliai.top")
        return 0
    print("[!] 部署失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
