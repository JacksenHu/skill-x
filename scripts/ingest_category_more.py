#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从候选池补充收录成熟项目到工具商店(自动模式,每分类限额 8 条)。"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(_k, None)

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
TODAY = time.strftime("%Y-%m-%d")
PAYLOAD = ROOT / "tools-store" / "api-import-payload.json"
CAND = ROOT / "scripts" / "upstream-audit" / "category-candidates.json"

SEC = {"recon", "vuln", "lab", "tunnel", "defense", "intel", "network-engineering-defense"}
NOISE = re.compile(
    r"awesome[-_]|cheatsheet|handbook|zoomcamp|\bcourse\b|interview|internship|"
    r"roadmap|tutorial|curated list|\bstudy\b|\bguide\b|\bnotes\b|\bbook\b", re.I)
LICENSE_OK = {"MIT", "Apache-2.0", "GPL-2.0", "GPL-3.0", "AGPL-3.0", "BSD-2-Clause",
              "BSD-3-Clause", "MPL-2.0", "ISC", "Unlicense", "EUPL-1.2",
              "NOASSERTION", "UNKNOWN"}
PER_CAT = 8


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    have = {(t.get("repo") or "").split("/")[-1].lower() for t in payload["tools"]}
    have_slug = {t.get("slug") for t in payload["tools"]}
    cands = json.loads(CAND.read_text(encoding="utf-8"))["candidates"]

    by_cat = {}
    for c in cands:
        cat = c["category"]
        if cat not in SEC:
            continue
        if (c["stars"] or 0) < 500:
            continue
        if c["license"] not in LICENSE_OK:
            continue
        if NOISE.search(c["full_name"]) or NOISE.search(c["description"] or ""):
            continue
        repo = c["full_name"].split("/")[-1].lower()
        if repo in have:
            continue
        by_cat.setdefault(cat, []).append(c)

    added = 0
    for cat in sorted(by_cat):
        items = sorted(by_cat[cat], key=lambda x: -(x["stars"] or 0))
        for c in items[:PER_CAT]:
            repo = c["full_name"].split("/")[-1]
            sl = slugify(repo)
            if sl in have_slug:
                continue
            desc = (c["description"] or "").strip().replace("\n", " ")[:180]
            summary = "%s：%s" % (repo, desc) if desc else repo
            payload["tools"].append({
                "slug": sl,
                "name": repo,
                "name_zh": repo,
                "category_id": cat,
                "summary": summary,
                "description": summary,
                "detail_url": "/tools/%s.html" % sl,
                "repo": c["full_name"],
                "docs_url": c["html_url"],
                "deploy": {
                    "method": "source",
                    "command": "git clone %s && cd %s" % (c["html_url"], repo),
                    "compose_file": None,
                    "image": None,
                },
                "ports": [],
                "default_port": None,
                "form": "cli",
                "credentials": [],
                "gitmcp": {"enabled": True, "url": "https://gitmcp.io/%s" % c["full_name"]},
                "labels": [cat, "source"],
                "upstream": {
                    "lastCheck": TODAY,
                    "alive": True,
                    "stars": c["stars"],
                    "pushedAt": (c["pushed_at"] or "") + "T00:00:00Z",
                    "license": c["license"],
                },
            })
            have_slug.add(sl)
            have.add(repo.lower())
            added += 1

    PAYLOAD.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print("新增 %d 条,工具总数 %d" % (added, len(payload["tools"])))
    print("分类分布:", dict(Counter(t["category_id"] for t in payload["tools"])))


if __name__ == "__main__":
    main()
