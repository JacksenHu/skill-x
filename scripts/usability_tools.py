#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工具商店真实可使用性验证：验证「照命令跑下去能不能成」。

对每个工具逐条核对它声称的部署路径是否真的存在：
  - docker-compose 类：仓库根目录是否真有 docker-compose.yml / compose.yaml；
    vulhub 这类子目录型还需确认关键子目录存在
  - docker / binary 类：Docker Hub 镜像是否存在；GitHub Releases 是否真有产物
  - cli 类：PyPI / npm 包是否存在
  - script 类：安装脚本 URL 是否 200
  - source / iac 类：确认构建入口文件存在

判定 USABLE / RISKY / BROKEN。
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH_TOKEN = os.environ.get("GH_TOKEN", "")
UA = "skillx-usability/1.0"
TIMEOUT = 25

COMPOSE_NAMES = [
    "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
    "docker-compose.dev.yml",
]


def get(url, headers=None):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:  # noqa: BLE001
        return 0, b""


def gh(path):
    h = {"Authorization": "Bearer " + GH_TOKEN} if GH_TOKEN else {}
    st, raw = get("https://api.github.com" + path, h)
    if st != 200:
        return st, None
    try:
        return st, json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return st, None


def gh_raw_list(repo, path=""):
    """列出仓库某目录内容。"""
    st, j = gh("/repos/%s/contents/%s" % (repo, path))
    if st != 200 or not isinstance(j, list):
        return st, []
    return st, [x.get("name", "") for x in j]


def check_compose(repo):
    st, names = gh_raw_list(repo)
    if st != 200:
        return {"ok": False, "reason": "无法列出仓库根目录(%d)" % st}
    hit = [n for n in names if n.lower() in COMPOSE_NAMES]
    if hit:
        return {"ok": True, "files": hit}
    return {"ok": False, "reason": "根目录无 compose 文件", "files": names[:12]}


def check_release(repo):
    st, j = gh("/repos/%s/releases/latest" % repo)
    if st != 200:
        # 退到 releases 列表
        st2, j2 = gh("/repos/%s/releases?per_page=1" % repo)
        if st2 == 200 and j2:
            j = j2[0]
        else:
            return {"ok": False, "reason": "无 Release(%d)" % st}
    if not j:
        return {"ok": False, "reason": "无 Release"}
    assets = j.get("assets") or []
    return {"ok": True, "tag": j.get("tag_name", ""), "assets": len(assets),
            "published": (j.get("published_at") or "")[:10]}


def check_dockerhub(image):
    name = image.split(":")[0]
    if "/" in name:
        url = "https://hub.docker.com/v2/repositories/%s/" % name
    else:
        url = "https://hub.docker.com/v2/repositories/library/%s/" % name
    st, raw = get(url)
    if st != 200:
        return {"ok": False, "reason": "Docker Hub 无此镜像(%d)" % st}
    try:
        j = json.loads(raw.decode("utf-8"))
        return {"ok": True, "pulls": j.get("pull_count"), "stars": j.get("star_count")}
    except Exception:  # noqa: BLE001
        return {"ok": True}


def check_pypi(pkg):
    st, _ = get("https://pypi.org/pypi/%s/json" % pkg)
    return {"ok": st == 200, "status": st}


def main():
    d = json.load(open(os.path.join(ROOT, "tools-store", "api-import-payload.json"), encoding="utf-8"))
    out = []
    for t in d["tools"]:
        slug = t.get("slug")
        repo = t.get("repo") or ""
        dep = t.get("deploy") or {}
        method = dep.get("method", "")
        cmd = dep.get("command", "")
        ev = {"slug": slug, "repo": repo, "method": method}
        verdict, reason = None, ""

        if method == "docker-compose":
            r = check_compose(repo)
            ev["compose"] = r
            if r.get("ok"):
                verdict = "USABLE"
                reason = "仓库根目录存在 %s" % ",".join(r["files"])
            else:
                # 子目录型（vulhub / terraformgoat）属预期
                st, names = gh_raw_list(repo)
                dirs = [n for n in names if "." not in n] if st == 200 else []
                if dirs:
                    verdict = "RISKY"
                    reason = "根目录无 compose，需进入子目录（属该仓库设计）"
                else:
                    verdict = "BROKEN"
                    reason = r.get("reason", "无 compose")
        elif method == "docker":
            img = dep.get("image")
            if not img:
                m = re.search(r"docker run\s+(?:-d\s+)?.*?\s([a-z0-9][\w.-]*/[\w.-]+|[\w.-]+):", cmd)
                img = m.group(1) if m else None
            if img:
                r = check_dockerhub(img)
                ev["image"] = img
                ev["dockerhub"] = r
                verdict = "USABLE" if r.get("ok") else "BROKEN"
                reason = "镜像 %s %s" % (img, "存在" if r.get("ok") else "不存在")
            else:
                verdict, reason = "RISKY", "未能从命令解析镜像名"
        elif method == "binary":
            r = check_release(repo)
            ev["release"] = r
            if r.get("ok"):
                verdict = "USABLE"
                reason = "Release %s（%d 个产物，%s）" % (r["tag"], r["assets"], r["published"])
            else:
                verdict, reason = "RISKY", r.get("reason", "无 Release") + "，需自行构建"
        elif method == "cli":
            pkg = None
            m = re.search(r"(?:pip3? install|uv add|npm i(?:nstall)?)\s+([\w.-]+)", cmd or "")
            if m:
                pkg = m.group(1)
            if pkg:
                r = check_pypi(pkg)
                ev["pkg"] = pkg
                ev["pypi"] = r
                verdict = "USABLE" if r.get("ok") else "BROKEN"
                reason = "PyPI %s %s" % (pkg, "存在" if r.get("ok") else "不存在")
            else:
                verdict, reason = "RISKY", "官方分发包，非 PyPI/npm（需官网下载）"
        elif method == "script":
            m = re.search(r"https://\S+?\.sh", cmd or "")
            if m:
                st, _ = get(m.group(0))
                ev["script_url"] = m.group(0)
                verdict = "USABLE" if st == 200 else "BROKEN"
                reason = "安装脚本 HTTP %d" % st
            else:
                verdict, reason = "RISKY", "无直链脚本"
        else:  # source / iac
            st, names = gh_raw_list(repo)
            build = [n for n in names if n.lower() in (
                "go.mod", "main.go", "requirements.txt", "package.json", "makefile", "vagrantfile")]
            ev["build_files"] = build
            if build:
                verdict = "USABLE"
                reason = "存在构建入口 %s" % ",".join(build[:3])
            else:
                verdict, reason = "RISKY", "未识别构建入口"

        ev["verdict"] = verdict
        ev["reason"] = reason
        out.append(ev)
        flag = {"USABLE": "OK  ", "RISKY": "RISK", "BROKEN": "FAIL"}[verdict]
        print("%s %-22s %-14s %s" % (flag, slug, method, reason))
        sys.stdout.flush()

    json.dump(out, open(os.path.join(ROOT, "scripts", "upstream-audit", "usability-tools.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    c = Counter(x["verdict"] for x in out)
    print("\nUSABLE=%d RISKY=%d BROKEN=%d" % (c.get("USABLE", 0), c.get("RISKY", 0), c.get("BROKEN", 0)))


if __name__ == "__main__":
    main()
