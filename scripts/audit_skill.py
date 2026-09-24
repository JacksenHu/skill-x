#!/usr/bin/env python3
"""技能安全审计(自动任务,纯标准库静态扫描)。

对每个自研 skill 执行 8 项静态检查,产出等级(A/B/C/D)与明细;
对收录套件,依据 external.json 的收录审查记录(许可证/可执行面/死链)生成摘要。

输出:showcase/audit/audit-report.json(构建时渲染进各技能详情页折叠区块)

用法:python scripts/audit_skill.py [--check]   # --check:与已有报告对比,不一致则 exit 1(CI 漂移检测)
"""
import ast
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
EXTERNAL = ROOT / "external.json"
OUT = ROOT / "showcase" / "audit" / "audit-report.json"

CODE_EXT = {".py", ".sh", ".js", ".mjs", ".ts", ".ps1", ".bat", ".cmd", ".rb", ".pl"}
DOC_URL_OK = re.compile(
    r"(openssh\.com|agentskills\.io|github\.com|vercel\.(com|app|sh)|nextjs\.org|web\.dev|"
    r"developers\.notion\.com|platform\.openai\.com|docs\.stripe\.com|docs\.anthropic\.com|"
    r"w3\.org|example\.(com|org)|localhost|127\.0\.0\.1|json-schema\.org|rfc-editor\.org)", re.I
)
URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+")
DANGER_RE = re.compile(r"\b(subprocess|os\.system|os\.popen|eval\s*\(|exec\s*\(|shutil\.rmtree|pickle\.loads|marshal\.loads)\b")
NET_RE = re.compile(r"\b(urllib|requests|httpx|socket|http\.client|aiohttp|paramiko|ftplib|smtplib)\b")
CRED_RE = re.compile(r"(os\.environ(\.get)?\s*[\[(]\s*['\"][A-Z0-9_]*(KEY|TOKEN|SECRET|PASS|CRED|AUTH)[A-Z0-9_]*['\"]|getenv\s*\(\s*['\"][A-Z0-9_]*(KEY|TOKEN|SECRET|PASS))")
INJECT_RE = re.compile(
    r"(ignore\s+(all\s+)?(previous|above)\s+instructions|忽略(上述|以上|前面)|disregard\s+.*instructions|"
    r"do\s+not\s+(tell|inform|mention)|不要(告诉|告知|提及)|exfiltrat|send\s+.*\s+to\s+https?://|"
    r"(上传|发送|回传).{0,12}(到|至)\s*https?://|silently\s+(upload|send)|without\s+(telling|informing))", re.I)
B64_RE = re.compile(r"[A-Za-z0-9+/]{120,}={0,2}")
HEX_RE = re.compile(r"(\\x[0-9a-fA-F]{2}){20,}")
STDLIB = set(sys.stdlib_module_names)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def code_files(skill_dir: Path):
    out = []
    for f in sorted(skill_dir.rglob("*")):
        if f.is_symlink() or not f.is_file():
            continue
        if f.suffix.lower() in CODE_EXT:
            out.append(f)
        elif f.suffix == "":
            try:
                if f.open("rb").readline(80).startswith(b"#!"):
                    out.append(f)
            except OSError:
                pass
    return out


NET_MODULES = {"urllib", "requests", "httpx", "socket", "http", "aiohttp", "paramiko", "ftplib", "smtplib", "ssl", "telnetlib", "xmlrpc"}
DANGER_NAMES = re.compile(
    r"^(subprocess\.|os\.(system|popen|remove|unlink|rmdir)|shutil\.rmtree|pickle\.loads|marshal\.loads|"
    r"eval|exec|compile|__import__|pty\.spawn|commands\.)")


def analyze_code(files):
    """AST 级分析:区分硬/可选 import、网络模块、危险调用(避免字符串字面量误报)。"""
    hard, opt, danger, net_calls = set(), set(), [], []
    for f in files:
        if f.suffix != ".py":
            text = read(f)
            for m in DANGER_RE.finditer(text):
                danger.append(f"{f.name}:{text[:m.start()].count(chr(10)) + 1} {m.group(0)}")
            continue
        try:
            tree = ast.parse(read(f))
        except SyntaxError:
            continue
        opt_nodes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.Import, ast.ImportFrom)):
                        opt_nodes.add(id(sub))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    (opt if id(node) in opt_nodes else hard).add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                (opt if id(node) in opt_nodes else hard).add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                fn = node.func
                parts = []
                cur = fn
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                name = ".".join(reversed(parts))
                if name and DANGER_NAMES.match(name):
                    danger.append(f"{f.name}:{node.lineno} {name}")
                if name.split(".")[0] in NET_MODULES:
                    net_calls.append(name)
    return {"hard": sorted(hard), "opt": sorted(opt), "danger": sorted(set(danger)), "net_calls": sorted(set(net_calls))}


def audit_skill(skill_dir: Path):
    files = code_files(skill_dir)
    skill_md = skill_dir / "SKILL.md"
    text_all = read(skill_md) if skill_md.is_file() else ""
    code_text = "\n".join(read(f) for f in files)
    checks = []

    # 1. 可执行面
    checks.append({
        "id": "exec-surface", "name": "可执行文件面", "level": "info" if not files else "low",
        "pass": True, "detail": f"{len(files)} 个可执行文件" + (f":{', '.join(str(f.relative_to(skill_dir)) for f in files[:6])}" if files else "(方法论型技能)"),
    })
    sig = analyze_code(files)
    urls = sorted(set(URL_RE.findall(code_text) + URL_RE.findall(text_all)))
    ext_urls = [u for u in urls if not DOC_URL_OK.search(u)]

    # 2. 危险调用(AST)
    checks.append({
        "id": "dangerous-calls", "name": "危险调用(subprocess/eval/exec/rmtree)", "level": "high" if sig["danger"] else "info",
        "pass": not sig["danger"], "detail": ("命中: " + "; ".join(sig["danger"][:4])) if sig["danger"] else "未发现",
    })
    # 3. 网络外联
    net_mods = [m for m in (sig["hard"] + sig["opt"]) if m in NET_MODULES]
    if ext_urls:
        level, detail = "medium", f"硬编码非文档 URL {len(ext_urls)} 个: " + "; ".join(ext_urls[:3])
    elif net_mods:
        level, detail = "low", f"网络模块 {'/'.join(net_mods)}(工具功能所需: HTTP 抓取/请求), 无硬编码外部 URL"
    else:
        level, detail = "info", "无网络模块, 无外部 URL"
    checks.append({"id": "network", "name": "网络外联", "level": level,
                   "pass": not ext_urls, "detail": detail})
    # 4. 凭证读取
    cred = sorted(set(m[0] if isinstance(m, tuple) else m for m in CRED_RE.findall(code_text)))
    checks.append({
        "id": "credentials", "name": "凭证读取", "level": "critical" if cred else "info",
        "pass": not cred, "detail": ("命中: " + ", ".join(cred[:4])) if cred else "未发现敏感环境变量读取",
    })
    # 5. 指令注入模式(SKILL.md)
    inj = sorted(set(m.group(0) for m in INJECT_RE.finditer(text_all)))
    checks.append({
        "id": "prompt-injection", "name": "SKILL.md 指令注入模式", "level": "high" if inj else "info",
        "pass": not inj, "detail": ("命中: " + "; ".join(inj[:3])) if inj else "未发现",
    })
    # 6. 混淆特征
    b64 = B64_RE.findall(code_text)
    hexs = HEX_RE.findall(code_text)
    checks.append({
        "id": "obfuscation", "name": "混淆特征(长 base64/hex)", "level": "high" if (b64 or hexs) else "info",
        "pass": not (b64 or hexs), "detail": f"长 base64 串 {len(b64)} 处, 长 hex 串 {len(hexs)} 处",
    })
    # 7. 依赖
    hard_tp = [m for m in sig["hard"] if m not in STDLIB]
    opt_tp = [m for m in sig["opt"] if m not in STDLIB]
    if hard_tp:
        dep_level, dep_detail = "medium", "硬依赖非标准库: " + ", ".join(hard_tp)
    elif opt_tp:
        dep_level, dep_detail = "low", "可选依赖(try/except 降级): " + ", ".join(opt_tp)
    else:
        dep_level, dep_detail = "info", "纯标准库"
    checks.append({"id": "deps", "name": "第三方依赖", "level": dep_level,
                   "pass": not hard_tp, "detail": dep_detail})
    # 8. 文件清单
    all_files = [f for f in skill_dir.rglob("*") if f.is_file() and not f.is_symlink()]
    total = sum(f.stat().st_size for f in all_files)
    checks.append({
        "id": "inventory", "name": "文件清单与体积", "level": "info", "pass": True,
        "detail": f"{len(all_files)} 个文件, {total // 1024} KB",
    })

    # 评分
    levels = {c["level"] for c in checks}
    if "critical" in levels:
        grade, score = "D", 40
    elif "high" in levels:
        grade, score = "C", 65
    elif "medium" in levels:
        grade, score = "B", 80
    elif "low" in levels:
        grade, score = "A-", 92
    else:
        grade, score = "A", 100
    return {"grade": grade, "score": score, "checks": checks,
            "scannedFiles": len(all_files), "scannedBytes": total}


def audit_suite(suite):
    """收录套件:基于 external.json 的收录审查记录生成摘要。"""
    lic = suite["license"]
    execs = suite.get("executables") or []
    ver = suite.get("verified") or {}
    alive = (suite.get("upstreamStatus") or {}).get("alive", True)
    checks = [
        {"id": "ns", "name": "命名空间", "level": "info", "pass": True, "detail": suite["namespace"]},
        {"id": "license", "name": "许可证核验", "level": "info" if lic["spdx"] != "UNKNOWN" else "low",
         "pass": lic["spdx"] != "UNKNOWN", "detail": f"{lic['spdx']} | {lic['evidence']}"},
        {"id": "exec-review", "name": "可执行面审查", "level": "low" if execs else "info",
         "pass": ver.get("execReview") == "passed",
         "detail": f"{len(execs)} 个可执行文件,审查结论: {ver.get('execReview')} (维护者 {ver.get('by') or '-'} @ {ver.get('at') or '-'})"},
        {"id": "alive", "name": "上游存活", "level": "info" if alive else "medium", "pass": alive,
         "detail": ("在线" if alive else "失联") + f" | 检查于 {((suite.get('upstreamStatus') or {}).get('lastCheck') or '未探活')}"},
    ]
    levels = {c["level"] for c in checks}
    grade = "B" if "medium" in levels else ("A-" if "low" in levels else "A")
    return {"grade": grade, "score": {"A": 100, "A-": 92, "B": 80}.get(grade, 80),
            "source": "ingestion-review", "checks": checks}


def main():
    report = {"generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
              "skills": {}, "suites": {}}
    for d in sorted(SKILLS_DIR.iterdir()):
        if (d / "SKILL.md").is_file():
            report["skills"][d.name] = audit_skill(d)
    if EXTERNAL.is_file():
        doc = json.loads(read(EXTERNAL))
        for s in doc.get("suites", []):
            report["suites"][s["namespace"]] = audit_suite(s)

    body = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if "--check" in sys.argv:
        old = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if old != body:
            print("[!] 审计报告与仓库记录不一致(存在未提交的变更)")
            return 1
        print("[+] 审计报告一致,无漂移")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8")
    for k, v in report["skills"].items():
        print(f"  [自研] {k}: {v['grade']} ({v['score']}) - " +
              "; ".join(f"{c['name']}={'PASS' if c['pass'] else 'HIT'}" for c in v["checks"] if not c["pass"]) or "all pass")
    for k, v in report["suites"].items():
        print(f"  [收录] {k}: {v['grade']} ({v['score']})")
    print(f"[+] 审计报告 -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
