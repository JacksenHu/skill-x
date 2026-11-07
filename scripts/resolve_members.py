#!/usr/bin/env python3
"""专家团成员 ref 解析层(零第三方依赖)。

统一解析专家团成员引用,输出可直接渲染/下发的成员元数据与降级标记。
三个消费方共用本模块:pack_ingest.py(收录)、showcase/build_index.py(橱窗站)、
人工排查(CLI)。

成员类型与 ref 约定:
  own-skill   ref = "<skill-name>"                     本站技能库(skills/<name>/)
  ext-skill   ref = "<owner>/<repo>/<skill-name>"      收录套件中的精选技能(末段为技能名)
  mcp         ref = "<ns/name>"                        mcp-registry.json 中已过审条目(含 plugin)
  cli / api   ref = "<任意稳定标识>"                    第一期预留:须在 pack 定义内联
                                                       name + install 才视为已解析

解析纪律:
- 只认"已过审"的来源:ext 套件须 execReview=passed 且命中 curation 白名单;
  mcp 条目须 reviewed.execReview=passed;meta-skill(pack)不可再作为成员。
- 成员缺失/下架 → resolved=false;非 optional 成员缺失会把整个 pack 标记 degraded。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
EXTERNAL = ROOT / "external.json"
CURATION = ROOT / "showcase" / "curation.json"
MCP_REGISTRY = ROOT / "mcp-registry.json"

MEMBER_TYPES = {"own-skill", "ext-skill", "mcp", "cli", "api"}
PACK_OWN_REPO = "JacksenHu/skill-x"


def _read_json(path: Path, default):
    if not Path(path).is_file():
        return default
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _parse_frontmatter(text: str):
    """返回 (top, meta)。只取平铺键;metadata 下一层缩进键进 meta。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, {}
    top, meta, in_meta = {}, {}, False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m:
            in_meta = m.group(1) == "metadata"
            if not in_meta:
                top[m.group(1)] = m.group(2).strip().strip('"').strip("'")
            continue
        if in_meta:
            mm = re.match(r"^\s+([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
            if mm:
                meta[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    return top, meta


def _slug(name: str) -> str:
    return re.sub(r"[^\w.-]+", "--", name)


def load_index(root: Path = ROOT) -> dict:
    """构建三类成员的解析索引。"""
    root = Path(root)
    own, ext, mcp = {}, {}, {}

    for f in sorted((root / "skills").glob("*/SKILL.md")):
        top, meta = _parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        if meta.get("package_type") == "meta-skill":
            continue  # 专家团编排技能不作为普通成员
        name = top.get("name", f.parent.name)
        own[name] = {
            "name": name,
            "title": meta.get("name-zh", name),
            "description-zh": meta.get("description-zh", top.get("description", "")),
            "description": top.get("description", ""),
            "category": meta.get("category", "engineering-hygiene"),
            "page": f"/skills/own-{name}.html",
            "install": f"npx skills add {PACK_OWN_REPO} --skill {name}",
        }

    external = _read_json(root / "external.json", {"suites": []})
    curation = _read_json(root / "showcase" / "curation.json", {"include": {}})
    for suite in external.get("suites", []):
        if (suite.get("verified") or {}).get("execReview") != "passed":
            continue
        ns = suite.get("namespace", "")
        allow = (curation.get("include") or {}).get(ns)
        lic = (suite.get("license") or {}).get("spdx", "")
        for s in suite.get("skills", []):
            if allow is not None and s.get("name") not in allow:
                continue  # 被方向白名单排除,视同未收录
            key = f"{ns}/{s['name']}"
            ext[key] = {
                "name": key,
                "title": s.get("name", ""),
                "description-zh": s.get("description-zh", s.get("description", "")),
                "description": s.get("description", ""),
                "category": s.get("category", "dev-workflow"),
                "page": f"/skills/ext-{_slug(ns)}--{s['name']}.html",
                "install": f"npx skills add {ns} --skill {s['name']}",
                "suite": ns,
                "license": lic,
            }

    registry = _read_json(root / "mcp-registry.json", {"servers": []})
    for s in registry.get("servers", []):
        cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
        if (cur.get("reviewed") or {}).get("execReview") != "passed":
            continue
        name = s.get("name", "")
        remotes = s.get("remotes") or []
        hint = cur.get("installHint", "")
        if not hint and remotes:
            hint = f"claude mcp add --transport http {name.split('/')[-1]} {remotes[0].get('url', '')}"
        mcp[name] = {
            "name": name,
            "title": s.get("title") or name,
            "description-zh": cur.get("description-zh", s.get("description", "")),
            "description": s.get("description", ""),
            "category": cur.get("category", "dev-workflow"),
            "page": f"/mcp/{_slug(name)}.html",
            "install": hint,
            "entryType": cur.get("entryType", "mcp"),
            "kind": cur.get("kind", "remote" if remotes else "local"),
            "riskLevel": cur.get("riskLevel", "medium"),
            "installPath": f"/v0/servers/{name}/install",
        }
    return {"own": own, "ext": ext, "mcp": mcp}


def resolve_member(member: dict, index: dict) -> dict:
    """解析单个成员;返回带 resolved 标记的成员字典(不修改入参)。"""
    out = {"type": member.get("type", ""), "ref": member.get("ref", "")}
    if member.get("optional"):
        out["optional"] = True
    mtype, ref = out["type"], out["ref"]

    if mtype not in MEMBER_TYPES:
        out.update({"resolved": False, "note": f"未知成员类型: {mtype}"})
        return out
    if mtype == "own-skill":
        d = index["own"].get(ref)
    elif mtype == "ext-skill":
        d = index["ext"].get(ref)
    elif mtype == "mcp":
        d = index["mcp"].get(ref)
    else:  # cli / api:第一期仅支持内联声明
        if member.get("name") and member.get("install"):
            out.update({
                "name": member.get("name"), "title": member.get("title") or member.get("name"),
                "description-zh": member.get("description-zh", ""),
                "category": member.get("category", ""),
                "page": member.get("page", ""),
                "install": member.get("install"),
                "resolved": True,
            })
            return out
        out.update({"resolved": False, "note": f"{mtype} 类型为预留能力:需内联 name + install"})
        return out

    if not d:
        out.update({"resolved": False, "note": f"成员未收录或已下架: {ref}"})
        return out
    out.update(d)
    out["resolved"] = True
    return out


def resolve_members(members, index: dict = None, root: Path = ROOT):
    """解析成员清单;返回 (解析后成员列表, degraded, 未解析成员列表)。"""
    index = index or load_index(root)
    resolved, missing = [], []
    for m in members or []:
        r = resolve_member(m, index)
        if not r["resolved"] and not r.get("optional"):
            missing.append(r)
        resolved.append(r)
    return resolved, bool(missing), missing


def resolve_pack(pack: dict, index: dict = None, root: Path = ROOT) -> dict:
    """解析整个 pack 的成员;返回写回 packs.json 的成员数组与状态。"""
    index = index or load_index(root)
    resolved, degraded, missing = resolve_members(pack.get("members"), index, root)
    return {"members": resolved, "degraded": degraded, "missing": [m["ref"] for m in missing]}


def main():
    """CLI:python scripts/resolve_members.py <packs.json> 打印解析报告。"""
    packs_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "packs.json"
    doc = _read_json(packs_path, None)
    if not doc:
        print(f"[!] 读不到 packs 注册表: {packs_path}")
        return 1
    index = load_index()
    bad = 0
    for pack in doc.get("packs", []):
        res = resolve_pack(pack, index)
        status = "DEGRADED" if res["degraded"] else "OK"
        print(f"[{status}] {pack.get('slug')} 成员 {len(res['members'])} 个")
        for m in res["members"]:
            flag = "ok" if m["resolved"] else ("optional-missing" if m.get("optional") else "MISSING")
            print(f"    - {m['type']:10s} {m['ref']:55s} {flag}")
        if res["degraded"]:
            bad += 1
    print(f"[+] 共 {len(doc.get('packs', []))} 个专家团,降级 {bad} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
