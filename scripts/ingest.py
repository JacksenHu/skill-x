#!/usr/bin/env python3
"""Skill X 套件收录器(docs/onboarding-pipeline.md 的机器化实现,纯标准库)。

用法:
  python scripts/ingest.py owner/repo [--branch BRANCH] [--out external.json] [--dry-run]
  python scripts/ingest.py https://example.com/suite.zip --out external.json
  python scripts/ingest.py ./local/path --out external.json

流程(SOP):拉取 -> 清点(manifest 发现/可执行面/许可证) -> 命名空间 -> upsert external.json
人工审查(verified 回填)由维护者在审查可执行面后完成,本脚本不自动置 verified。
"""
import io
import json
import os
import re
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "external.json"

EXEC_EXTS = {".py", ".sh", ".js", ".mjs", ".ts", ".ps1", ".bat", ".cmd", ".rb", ".pl"}
LICENSE_HINTS = [
    ("MIT", re.compile(r"MIT License|Permission is hereby granted, free of charge", re.I)),
    ("Apache-2.0", re.compile(r"Apache License,?\s*Version 2\.0|Apache-2\.0", re.I)),
    ("BSD", re.compile(r"Redistribution and use in source and binary forms", re.I)),
    ("ISC", re.compile(r"ISC License", re.I)),
    ("CC-BY-4.0", re.compile(r"Creative Commons Attribution 4\.0|CC BY 4\.0", re.I)),
]
UA = {"User-Agent": "skill-x-ingest/1.0"}


def http_get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and "github" in url:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_source(src: str):
    """返回 (kind, payload):github / zip-url / local / ssh"""
    if re.fullmatch(r"[\w.-]+/[\w.-]+", src):
        owner, repo = src.split("/", 1)
        return "github", (owner, repo)
    if src.startswith("git@"):
        return "ssh", src
    p = Path(src)
    if p.is_dir():
        return "local", p.resolve()
    if re.match(r"https?://", src) and re.search(r"\.(zip|tar\.gz|tgz)(\?|$)", src):
        return "zip-url", src
    raise SystemExit(f"[!] 无法识别来源格式: {src}(支持 owner/repo / git@ssh / *.zip URL / 本地目录)")


def fetch_github(owner: str, repo: str, branch: str | None) -> Path:
    branches = [branch] if branch else []
    if not branch:
        try:
            info = json.loads(http_get(f"https://api.github.com/repos/{owner}/{repo}", 15))
            branches.append(info.get("default_branch") or "main")
        except Exception:
            pass
        branches += ["main", "master"]
    tmp = Path(tempfile.mkdtemp(prefix="skillx-ingest-"))
    last_err = None
    for br in dict.fromkeys(branches):
        url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{br}"
        try:
            data = http_get(url, 60)
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
                tf.extractall(tmp, filter="data")
            subdirs = [d for d in tmp.iterdir() if d.is_dir()]
            print(f"[+] 拉取成功 {owner}/{repo}@{br} ({len(data)//1024} KB)")
            return subdirs[0] if subdirs else tmp
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"[-] 分支 {br} 拉取失败: {e}")
    raise SystemExit(f"[!] 全部分支拉取失败,最后错误: {last_err}")


def fetch_zip_url(url: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="skillx-ingest-"))
    data = http_get(url, 60)
    if url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(tmp)
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
            tf.extractall(tmp, filter="data")
    subdirs = [d for d in tmp.iterdir() if d.is_dir()]
    print(f"[+] 下载解压成功 {url} ({len(data)//1024} KB)")
    return subdirs[0] if len(subdirs) == 1 else tmp


def find_skill_paths(base: Path):
    """manifest 发现优先级,返回 (skill 目录列表, 发现方式)。"""
    mp = base / ".claude-plugin" / "marketplace.json"
    if mp.is_file():
        skills = []
        doc = json.loads(mp.read_text(encoding="utf-8"))
        for plug in doc.get("plugins", []):
            for rel in plug.get("skills", []):
                d = (base / rel).resolve()
                if (d / "SKILL.md").is_file():
                    skills.append(d)
        if skills:
            return skills, ".claude-plugin/marketplace.json"
    cp = base / ".codex-plugin" / "plugin.json"
    if cp.is_file():
        doc = json.loads(cp.read_text(encoding="utf-8"))
        rel = doc.get("skills")
        if rel:
            d = base / rel
            found = scan_skills_dir(d)
            if found:
                return found, ".codex-plugin/plugin.json"
    wk = base / ".well-known" / "skills" / "index.json"
    if wk.is_file():
        doc = json.loads(wk.read_text(encoding="utf-8"))
        skills = []
        for s in doc.get("skills", []):
            d = (base / ".well-known" / "skills" / s.get("path", "")).parent
            if (d / "SKILL.md").is_file():
                skills.append(d)
        if skills:
            return skills, ".well-known/skills/index.json"
    found = scan_skills_dir(base / "skills")
    if found:
        return found, "scan:skills/"
    if (base / "SKILL.md").is_file():
        return [base], "scan:root"
    return [], "none"


def scan_skills_dir(d: Path, depth: int = 3):
    if not d.is_dir():
        return []
    out = []
    for f in sorted(d.rglob("SKILL.md")):
        rel = f.relative_to(d)
        if len(rel.parts) <= depth:
            out.append(f.parent)
    return out


def parse_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields, cur_key = {}, None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m:
            cur_key = m.group(1)
            fields[cur_key] = m.group(2).strip().strip('"').strip("'")
        elif cur_key and line.startswith((" ", "\t")) and cur_key == "version":
            pass
    return fields


def detect_license(base: Path):
    for f in sorted(base.iterdir()):
        if f.is_file() and re.match(r"(LICEN[SC]E|COPYING|NOTICE)", f.name, re.I):
            head = f.read_text(encoding="utf-8", errors="replace")[:4000]
            for spdx, pat in LICENSE_HINTS:
                m = pat.search(head)
                if m:
                    line_no = head[: m.start()].count("\n") + 1
                    return spdx, f"{f.name}:L{line_no}"
            return "UNKNOWN", f"{f.name}(无白名单关键词命中)"
    return "UNKNOWN", "无 LICENSE 文件"


def scan_executables(base: Path):
    out = []
    for f in sorted(base.rglob("*")):
        try:
            if f.is_symlink():
                continue  # 上游符号链接可能指向无权位置,跳过
            if not f.is_file():
                continue
        except OSError:
            continue
        if f.suffix.lower() in EXEC_EXTS:
            out.append(str(f.relative_to(base)))
        elif f.suffix == "":
            try:
                first = f.open("rb").readline(80)
                if first.startswith(b"#!"):
                    out.append(str(f.relative_to(base)))
            except OSError:
                pass
    return out


def parse_cli(argv):
    """支持 --key value 与 --key=value 与 --flag 三种形式。"""
    args, opts = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            key = a.lstrip("-")
            if "=" in key:
                k, v = key.split("=", 1)
                opts[k] = v
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--") and key in ("out", "branch"):
                opts[key] = argv[i + 1]
                i += 1
            else:
                opts[key] = True
        else:
            args.append(a)
        i += 1
    return args, opts


def main():
    args, opts = parse_cli(sys.argv[1:])
    if not args:
        print(__doc__)
        return 1
    src = args[0]
    out_path = Path(opts.get("out", DEFAULT_OUT))
    dry = "dry-run" in opts
    branch = opts.get("branch") if isinstance(opts.get("branch"), str) else None

    kind, payload = parse_source(src)
    if kind == "github":
        owner, repo = payload
        base = fetch_github(owner, repo, branch)
        namespace = f"{owner}/{repo}"
        upstream = f"https://github.com/{owner}/{repo}"
    elif kind == "zip-url":
        base = fetch_zip_url(payload)
        namespace = re.sub(r"\W+", "-", payload.split("//", 1)[-1])[:60]
        upstream = payload
    elif kind == "local":
        base = payload
        namespace = f"local/{base.name}"
        upstream = str(base)
    else:
        raise SystemExit("[!] SSH 来源请改为:先 git clone 到本地,再用本地路径收录(codeload 不支持 SSH)")

    skills_dirs, via = find_skill_paths(base)
    spdx, evidence = detect_license(base)
    executables = scan_executables(base)

    skills = []
    for d in skills_dirs:
        fm = parse_frontmatter((d / "SKILL.md").read_text(encoding="utf-8", errors="replace"))
        meta_version = ""
        m = re.search(r"version:\s*[\"']?([\w.-]+)", (d / "SKILL.md").read_text(encoding="utf-8", errors="replace"))
        if m:
            meta_version = m.group(1)
        skills.append({
            "name": fm.get("name", d.name),
            "path": str(d.relative_to(base) / "SKILL.md"),
            "description": fm.get("description", "")[:1024],
            "version": meta_version or fm.get("version", ""),
        })

    suite = {
        "namespace": namespace,
        "upstream": upstream,
        "license": {"spdx": spdx, "evidence": evidence, "attribution": "保留上游 LICENSE 与署名" if spdx != "UNKNOWN" else "仅链接,不镜像内容"},
        "ingestedAt": str(date.today()),
        "verified": {"by": None, "at": None, "execReview": "pending"},
        "upstreamStatus": {"lastCheck": None, "alive": True, "failSince": None},
        "manifestVia": via,
        "skills": skills,
        "executables": executables,
    }

    print(f"\n===== 收录清点报告: {namespace} =====")
    print(f"发现方式 : {via}")
    print(f"skill 数 : {len(skills)}")
    for s in skills:
        print(f"  - {s['name']} ({s['path']})")
    print(f"许可证   : {spdx} | 证据: {evidence}")
    print(f"可执行面 : {len(executables)} 个")
    for e in executables:
        print(f"  * {e}")
    if spdx == "UNKNOWN":
        print("[!] 许可证未确认:仅可链接收录,verified 前必须人工确认许可")
    if executables:
        print("[!] 存在可执行文件:需人工逐个审查(红线:未声明外联/凭证读取/混淆/curl|sh)")

    if dry:
        print("\n[dry-run] 未写入 external.json")
        return 0

    doc = {"schemaVersion": 1, "suites": []}
    if out_path.is_file():
        doc = json.loads(out_path.read_text(encoding="utf-8"))
    doc["suites"] = [s for s in doc.get("suites", []) if s.get("namespace") != namespace]
    doc["suites"].append(suite)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n[+] 已 upsert 到 {out_path} (suites: {len(doc['suites'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
