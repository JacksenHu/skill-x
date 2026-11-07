#!/usr/bin/env python3
"""专家团(pack)收录器 / 注册表同步器(docs/pack-onboarding-pipeline.md 的机器化实现,纯标准库)。

用法:
  python scripts/pack_ingest.py --sync            # 重解析全部 pack:成员解析 + 编排剧本同步 + degraded 状态
  python scripts/pack_ingest.py --check           # 校验 packs.json 与源文件/成员索引一致(漂移 exit=1)
  python scripts/pack_ingest.py ./pack.json       # 收录外部专家团(upsert,execReview=pending)
  python scripts/pack_ingest.py ./pack.json --dry-run

纪律(与 mcp_ingest.py 同套):
- 脚本不自动置 verified;人工审查后回填 reviewed.execReview=passed 才会进对外产物。
- 成员完整性:所有非 optional 成员必须能解析(own-skill / ext-skill / mcp),
  否则拒绝收录;--sync 阶段成员若已下架则标 degraded,不阻断。
- 本站 pack 的编排剧本源文件是 skills/pack-<slug>/SKILL.md,content 字段由 --sync 保持同步。
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_members import load_index, resolve_pack  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "packs.json"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,40}$")
SCENES = {"reverse-engineering", "pentest", "malware", "forensics", "engineering-hygiene",
          "dev-workflow", "data", "web-frontend", "ai-media"}
LICENSE_WHITELIST = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "CC-BY-4.0"}
DEFAULT_AVATAR = "assets/avatars/pack-default.svg"


def read_json(path: Path, default):
    if not Path(path).is_file():
        return default
    return json.loads(Path(path).read_text(encoding="utf-8"))


def own_install(skill: str) -> str:
    return f"npx skills add JacksenHu/skill-x --skill {skill}"


def sync_pack(pack: dict, index: dict) -> dict:
    """重算单个 pack 的成员解析 / 安装命令 / degraded / content(不改入参)。"""
    p = json.loads(json.dumps(pack, ensure_ascii=False))
    res = resolve_pack(p, index)
    p["members"] = res["members"]
    p["degraded"] = res["degraded"]
    if "missingMembers" in p or res["degraded"]:
        p["missingMembers"] = res["missing"]
    else:
        p.pop("missingMembers", None)
    if p.get("origin") == "own" and p.get("skill"):
        p["install"] = own_install(p["skill"])
    src = p.get("source")
    if src:
        f = ROOT / src
        if f.is_file():
            p["content"] = f.read_text(encoding="utf-8")
        else:
            p["contentStale"] = f"源文件不存在: {src}"
    return p


def sync_all(doc: dict, index: dict) -> dict:
    out = {"schemaVersion": doc.get("schemaVersion", 1), "packs": []}
    for pack in doc.get("packs", []):
        out["packs"].append(sync_pack(pack, index))
    return out


def validate_external(pack: dict, index: dict) -> list:
    errs = []
    slug = pack.get("slug", "")
    if not slug or not SLUG_RE.match(slug):
        errs.append(f"slug 不合规(小写字母/数字/连字符,3-41 位): {slug}")
    for f in ("displayName", "displayNameEn", "summary", "summaryEn"):
        if not pack.get(f):
            errs.append(f"缺必填字段: {f}")
    persona = pack.get("persona") or {}
    for f in ("role", "roleEn", "tagline", "scene"):
        if not persona.get(f):
            errs.append(f"缺 persona.{f}")
    if persona.get("scene") and persona["scene"] not in SCENES:
        errs.append(f"persona.scene 非法: {persona['scene']}(可选 {sorted(SCENES)})")
    if pack.get("origin") != "external":
        errs.append("收录输入必须 origin=external(本站 pack 请直接维护 packs.json)")
    if not pack.get("upstream"):
        errs.append("外部专家团必须填 upstream(git/zip/local 来源)")
    if not pack.get("install"):
        errs.append("外部专家团必须填 install(指向上游的安装命令或 URL)")
    lic = (pack.get("license") or {}).get("spdx")
    if lic and lic not in LICENSE_WHITELIST:
        pack.setdefault("_ingestWarnings", []).append(
            f"许可证 {lic} 不在白名单,只允许元数据+安装指引收录(不缓存正文)")
    if not pack.get("members"):
        errs.append("members 不能为空")
    for m in pack.get("members") or []:
        if m.get("type") not in {"own-skill", "ext-skill", "mcp", "cli", "api"}:
            errs.append(f"成员类型非法: {m.get('type')} ({m.get('ref')})")
        if not m.get("ref"):
            errs.append("成员缺 ref")
    if not errs:
        res = resolve_pack(pack, index)
        missing = [r["ref"] for r in res["members"] if not r["resolved"] and not r.get("optional")]
        if missing:
            errs.append(f"成员完整性未过,以下成员未收录/已下架: {', '.join(missing)}")
    return errs


def upsert(pack: dict, out_path: Path):
    doc = read_json(out_path, {"schemaVersion": 1, "packs": []})
    doc["packs"] = [p for p in doc.get("packs", []) if p.get("slug") != pack.get("slug")]
    pack.setdefault("persona", {}).setdefault("avatar", DEFAULT_AVATAR)
    pack["reviewed"] = {"by": None, "at": None, "execReview": "pending",
                        "note": "脚本收录;人工审查人设文案、成员完整性与上游归属后回填"}
    pack.setdefault("upstreamStatus", {"source": "external-ingest", "lastCheck": str(date.today()),
                                       "alive": True, "failSince": None})
    doc["packs"].append(pack)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_cli(argv):
    args, opts = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            key = a.lstrip("-")
            if "=" in key:
                k, v = key.split("=", 1)
                opts[k] = v
            elif key == "out" and i + 1 < len(argv):
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
    out_path = Path(opts.get("out", DEFAULT_OUT))
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    index = load_index()

    if "sync" in opts or "check" in opts:
        doc = read_json(out_path, None)
        if doc is None:
            print(f"[!] 读不到注册表: {out_path}")
            return 1
        new = sync_all(doc, index)
        if "check" in opts:
            drift = []
            old_packs = {p.get("slug"): p for p in doc.get("packs", [])}
            new_packs = {p.get("slug"): p for p in new.get("packs", [])}
            for slug, p in new_packs.items():
                if json.dumps(old_packs.get(slug), ensure_ascii=False, sort_keys=True) != \
                   json.dumps(p, ensure_ascii=False, sort_keys=True):
                    drift.append(slug)
            if drift:
                print("[!] packs.json 与源文件/成员索引不一致,请运行:python scripts/pack_ingest.py --sync")
                for s in drift:
                    print(f"    - {s}")
                return 1
            print(f"[+] 专家团注册表一致({len(new_packs)} 个,无漂移)")
            return 0
        out_path.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for p in new["packs"]:
            flag = "DEGRADED" if p.get("degraded") else "ok"
            print(f"[{flag}] {p['slug']}: 成员 {len(p['members'])} 个,content {len(p.get('content', ''))} 字符")
        print(f"[+] 已同步 -> {out_path}")
        return 0

    if not args:
        print(__doc__)
        return 1
    pack = read_json(Path(args[0]), None)
    if pack is None:
        print(f"[!] 读不到输入文件: {args[0]}")
        return 1
    errs = validate_external(pack, index)
    if errs:
        print("[!] 外部专家团校验未过:")
        for e in errs:
            print(f"    - {e}")
        return 2
    res = resolve_pack(pack, index)
    print(f"\n===== 专家团收录清点报告: {pack['slug']} =====")
    print(f"名称     : {pack.get('displayName')} / {pack.get('displayNameEn')}")
    print(f"来源     : {pack.get('origin')} | {pack.get('upstream')}")
    print(f"许可证   : {(pack.get('license') or {}).get('spdx', 'UNKNOWN')}")
    print(f"成员     : {len(res['members'])} 个(全部已解析)")
    for m in res["members"]:
        print(f"  - {m['type']:10s} {m['ref']}")
    for w in pack.get("_ingestWarnings", []):
        print(f"[!] {w}")
    print("[!] 人工审查前 execReview=pending,不会进入橱窗站与 /v0/packs 输出")
    if "dry-run" in opts:
        print("\n[dry-run] 未写入 packs.json")
        return 0
    upsert(pack, out_path)
    print(f"\n[+] 已 upsert 到 {out_path} (packs: {len(read_json(out_path, {}).get('packs', []))})")
    print("[*] 提示:外部专家团如缓存正文,请把编排剧本放 skills/pack-<slug>/SKILL.md 并改 source 字段")
    return 0


if __name__ == "__main__":
    sys.exit(main())

