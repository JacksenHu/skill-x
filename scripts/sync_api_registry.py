#!/usr/bin/env python3
"""Regenerate api/registry.json (the /dl whitelist) from external.json.

external.json keeps per-skill repo-relative paths (layouts differ per upstream);
server.py needs those paths to repack correctly.  api/registry.json used to be
hand-maintained and drifted to 6 suites while external.json has 29.

Usage:
  python scripts/sync_api_registry.py            # rewrite api/registry.json
  python scripts/sync_api_registry.py --check    # exit 1 when drifted (CI)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "external.json"
OUT = ROOT / "api" / "registry.json"


def norm_path(p: str) -> str:
    """Windows separators and leading ./ are noise for tar member matching."""
    return str(p or "").replace("\\", "/").lstrip("./")


def build() -> tuple:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    suites, skipped = [], []
    for s in data.get("suites", []):
        ns = s.get("namespace")
        skills = s.get("skills") or []
        if not ns or not skills:
            skipped.append(ns or s.get("repo") or s.get("name") or "?")
            continue
        names, paths = [], {}
        for item in skills:
            if isinstance(item, str):
                name = item.strip()
                path = f"skills/{name}/SKILL.md"
            else:
                name = str(item.get("name") or "").strip()
                path = str(item.get("path") or "")
            if not name or name in paths:
                continue
            names.append(name)
            if path:
                paths[name] = norm_path(path)
        if not names:
            continue
        entry = {
            "namespace": ns,
            "upstream": s.get("upstream") or s.get("url") or "",
            "branch": s.get("branch") or "main",
            "skills": names,
        }
        if paths:
            entry["paths"] = paths
        suites.append(entry)
    return {"suites": suites}, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare only, exit 1 on drift")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    reg, skipped = build()
    total = sum(len(s["skills"]) for s in reg["suites"])
    out = Path(args.out)

    if args.check:
        if not out.is_file():
            print(f"[check] missing {out}")
            return 1
        old = json.loads(out.read_text(encoding="utf-8"))
        same = old == reg
        print(f"[check] suites={len(reg['suites'])} skills={total} drift={'no' if same else 'YES'}")
        return 0 if same else 1

    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(reg, ensure_ascii=False, indent=2) + "\n")
    print(f"[ok] wrote {out} suites={len(reg['suites'])} skills={total} skipped={len(skipped)}")
    for k in skipped:
        print(f"  skip: {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

