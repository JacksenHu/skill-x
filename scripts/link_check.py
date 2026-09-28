#!/usr/bin/env python3
"""upstream 死链探活(docs/onboarding-pipeline.md §2.4,纯标准库)。

对 external.json 中每个 suite.upstream、mcp-registry.json 中每个已过审条目的
远程端点/plugin install.url 做 HEAD(405 回退 GET 首字节),3 次指数退避重试。
输出 link-check-report.json;alive=false 打印标注提醒,failSince 超 7 天打印下架提醒。
CI 只上传 artifact,不写仓库。
"""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "external.json"
REPORT = ROOT / "link-check-report.json"
ENTRIES = ROOT / "mcp-registry.json"
UA = {"User-Agent": "skill-x-linkcheck/1.0"}


def probe(url: str, retries: int = 3):
    err = "unknown"
    for i in range(retries):
        try:
            req = urllib.request.Request(url, method="HEAD", headers=UA)
            with urllib.request.urlopen(req, timeout=10) as r:
                return True, r.status
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return True, f"HTTP {e.code} (auth-gated, alive)"  # 认证门控=端点存活
            if e.code in (404, 405):
                # 部分站点(如 VS 市场)对 HEAD 返回 404/405,回退 GET 首字节确认
                try:
                    req = urllib.request.Request(url, headers={**UA, "Range": "bytes=0-0"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        return True, r.status
                except urllib.error.HTTPError as e2:
                    if e2.code in (401, 403):
                        return True, f"HTTP {e2.code} (auth-gated, alive)"
                    err = f"GET-fallback: HTTP {e2.code}"
                except Exception as e2:  # noqa: BLE001
                    err = f"GET-fallback: {e2}"
            else:
                err = f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001
            err = str(e)
        time.sleep(2 ** i)
    return False, err


def main():
    doc = json.loads(EXT.read_text(encoding="utf-8"))
    today = date.today()
    results, dead = [], 0
    for s in doc.get("suites", []):
        url = s.get("upstream", "")
        ok, detail = probe(url)
        st = s.setdefault("upstreamStatus", {})
        st["lastCheck"] = str(today)
        if ok:
            st["alive"], st["failSince"] = True, None
        else:
            dead += 1
            if st.get("alive", True):
                st["failSince"] = str(today)
            st["alive"] = False
            days = (today - datetime.strptime(st["failSince"], "%Y-%m-%d").date()).days
            print(f"[DEAD] {s['namespace']} -> {detail}(连续 {days} 天)")
            if days >= 7:
                print(f"[下架提醒] {s['namespace']} 已连续失联 {days} 天,应从橱窗下架")
        results.append({"namespace": s["namespace"], "upstream": url, "alive": ok, "detail": str(detail)})
        print(f"[{' OK ' if ok else 'FAIL'}] {s['namespace']} ({url})")

    # MCP/plugin 条目:探活远程端点或 plugin install.url,状态回写 curated.upstreamStatus
    if ENTRIES.is_file():
        edoc = json.loads(ENTRIES.read_text(encoding="utf-8"))
        for s in edoc.get("servers", []):
            cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
            if (cur.get("reviewed") or {}).get("execReview") != "passed":
                continue
            entry_type = cur.get("entryType", "mcp")
            remotes = s.get("remotes") or []
            install = cur.get("install") or {}
            url = (remotes[0].get("url") if remotes else "") or install.get("url") or s.get("websiteUrl") or ""
            if not url:
                continue
            name = s.get("name", "?")
            ok, detail = probe(url)
            st = cur.setdefault("upstreamStatus", {})
            st["lastCheck"] = str(today)
            if ok:
                st["alive"], st["failSince"] = True, None
            else:
                dead += 1
                if st.get("alive", True):
                    st["failSince"] = str(today)
                st["alive"] = False
                days = (today - datetime.strptime(st["failSince"], "%Y-%m-%d").date()).days
                print(f"[DEAD] {entry_type}:{name} -> {detail}(连续 {days} 天)")
                if days >= 7:
                    print(f"[下架提醒] {name} 已连续失联 {days} 天,应从橱窗下架")
            results.append({"namespace": name, "upstream": url, "alive": ok, "detail": str(detail), "entryType": entry_type})
            print(f"[{' OK ' if ok else 'FAIL'}] {entry_type}:{name} ({url})")
        ENTRIES.write_text(json.dumps(edoc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT.write_text(json.dumps({"date": str(today), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    # 状态回写 external.json / mcp-registry.json 仅供本地查看;CI 中此改动随运行结束丢弃,artifact 为准
    EXT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n共 {len(results)} 个 upstream,{dead} 个失联。报告: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
