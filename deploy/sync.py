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
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
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
    tmp_tar = f"/www/wwwroot/{TAR.name}"
    # 1) 先把压缩包传到站点父目录(删站后压缩包仍在,可重试)
    r1 = call("files", "UploadFile", path="/www/wwwroot", files={"zunfile": (TAR.name, data)})
    print("UploadFile ->", r1.get("msg"))
    # 2) 清空站点目录再重建(纯净部署,杜绝已下架产物残留:tar 覆盖不删旧文件)
    call("files", "DeleteDir", path=SITE_PATH)
    r2 = call("files", "CreateDir", path=SITE_PATH)
    print("站点目录重建 ->", r2.get("msg"))
    # 3) 解压到站点目录
    r3 = call("files", "UnZip", sfile=tmp_tar, dfile=SITE_PATH + "/",
              type="tar.gz", coding="UTF-8", password="")
    print("UnZip ->", r3.get("msg"))
    r4 = call("files", "DeleteFile", path=tmp_tar)
    print("清理临时包 ->", r4.get("msg"))
    if "--api" in sys.argv:
        api_dir = ROOT / "api"
        for fname in ("server.py", "registry.json"):
            src = api_dir / fname
            if src.is_file():
                ra = call("files", "UploadFile", path="/www/wwwroot/skillx-api",
                          files={"zunfile": (fname, src.read_bytes())})
                print(f"后端 {fname} ->", ra.get("msg"))
        print("[+] 后端已更新(server.py 内含热重载,约 30 秒内自动生效)")

    if r1.get("status") and r3.get("status"):
        if "--reload" in sys.argv:
            r5 = call("system", "ServiceAdmin", name="nginx", type="reload")
            print("nginx reload ->", r5.get("msg"))
        print("[+] 部署完成(纯净重放)-> https://skillx.yueliai.top")
        return 0
    print("[!] 部署失败:压缩包保留在", tmp_tar, "可手动重试解压")
    return 1


if __name__ == "__main__":
    sys.exit(main())
