#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按分类收录成熟 GitHub 项目到「安全工具商店」(tools-store/api-import-payload.json)。

候选来自 scripts/crawl_categories.py 产出的 category-candidates.json;
本脚本只收录下方 PICKS 白名单(人工核验过的成熟项目),逐个调 GitHub API
复核 stars/license/pushed_at/归档状态,再生成站点条目。

纪律: 不覆盖已有 slug;不写入未通过核验的条目;输出收录报告。
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy",
           "all_proxy", "GIT_HTTP_PROXY", "GIT_HTTPS_PROXY"):
    os.environ.pop(_k, None)

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
TODAY = time.strftime("%Y-%m-%d")
TOKEN = os.environ.get("GH_TOKEN", "")
UA = "skillx-ingest/1.0"
PAYLOAD = ROOT / "tools-store" / "api-import-payload.json"

# (full_name, category, form, deploy_method, ports, default_port, name_zh, summary)
PICKS = [
    # ---------- recon 侦察测绘 ----------
    ("owasp-amass/amass", "recon", "cli", "binary", [], None, "攻击面测绘",
     "OWASP Amass:深入攻击面测绘与资产发现框架,聚合 DNS、证书、API 与网络爬取多源情报,枚举子域与关联资产。"),
    ("projectdiscovery/subfinder", "recon", "cli", "binary", [], None, "被动子域枚举",
     "ProjectDiscovery Subfinder:快速被动子域枚举工具,聚合数十个公开数据源,输出可直接接入扫描流程的子域清单。"),
    ("mxrch/GHunt", "recon", "cli", "source", [], None, "谷歌账号情报",
     "GHunt:面向 Google 账号的开源情报框架,通过公开接口提取账号关联信息,用于授权范围内的侦察。"),
    ("sundowndev/phoneinfoga", "recon", "cli", "source", [], None, "号码情报",
     "PhoneInfoga:电话号码开源情报收集框架,聚合运营商、归属地与公开线索,支持批量查询。"),
    ("ivre/ivre", "recon", "web", "docker-compose", [80, 443], 80, "网络侦察框架",
     "IVRE:自托管网络侦察框架,整合被动流量、主动扫描与指纹识别,构建可查询的网络资产地图。"),
    ("netalertx/NetAlertX", "recon", "web", "docker-compose", [20211], 20211, "网络可见性",
     "NetAlertX:局域网设备可见性与持续监控平台,发现接入设备、跟踪在线状态并对变更推送告警。"),
    ("blechschmidt/massdns", "recon", "cli", "binary", [], None, "DNS 批量解析",
     "massdns:高性能 DNS 存根解析器,面向大规模子域解析与 DNS 数据集的批量查询。"),

    # ---------- vuln 漏洞扫描 ----------
    ("projectdiscovery/nuclei", "vuln", "cli", "binary", [], None, "模板化漏扫",
     "Nuclei:基于 YAML 模板的快速漏洞扫描器,社区模板覆盖 CVE、错误配置与暴露面检测。"),
    ("anchore/grype", "vuln", "cli", "binary", [], None, "镜像漏洞扫描",
     "Grype:容器镜像与文件系统漏洞扫描器,对照 SBOM 与漏洞库定位已知 CVE。"),
    ("future-architect/vuls", "vuln", "cli", "binary", [], None, "主机漏扫",
     "Vuls:无 Agent 的漏洞扫描器,覆盖 Linux/FreeBSD/Windows 与容器,关联 CVE 与 OVAL 数据。"),
    ("google/osv-scanner", "vuln", "cli", "binary", [], None, "依赖漏洞扫描",
     "OSV-Scanner:Google 开源漏洞扫描器,基于 OSV 数据库检测项目依赖中的已知漏洞。"),
    ("google/tsunami-security-scanner", "vuln", "service", "docker", [8080], 8080, "网络漏扫引擎",
     "Tsunami:Google 通用网络安全扫描引擎,以插件化方式检测高危漏洞并显著降低误报。"),
    ("NVIDIA/garak", "vuln", "cli", "source", [], None, "LLM 漏洞扫描",
     "garak:NVIDIA 的 LLM 漏洞扫描器,对生成式模型做红队式探测,覆盖提示注入、越狱与数据泄露。"),
    ("shadow1ng/fscan", "vuln", "cli", "binary", [], None, "内网综合扫描",
     "fscan:内网综合扫描工具,集成主机存活、端口、服务、漏洞与弱口令探测,适合授权内网评估。"),

    # ---------- lab 靶场实验 ----------
    ("RhinoSecurityLabs/cloudgoat", "lab", "cli", "source", [], None, "云安全靶场",
     "CloudGoat:Rhino Security Labs 的 AWS 漏洞靶场,以场景化方式演练云环境攻击路径。"),
    ("splunk/attack_range", "lab", "cli", "source", [], None, "攻击模拟靶场",
     "Attack Range:可快速搭建的攻击模拟靶场,预置域控、终端与日志采集,用于检测规则验证。"),
    ("GZTimeWalker/GZCTF", "lab", "web", "docker-compose", [80, 443], 80, "CTF 平台",
     "GZCTF:开源 CTF 竞赛平台,支持动态计分、容器化题目与团队赛制。"),
    ("webpwnized/mutillidae", "lab", "web", "docker", [80], 80, "OWASP 靶场",
     "OWASP Mutillidae II:面向 Web 漏洞教学的免费靶场,覆盖 OWASP Top 10 常见缺陷。"),
    ("controlplaneio/simulator", "lab", "cloud", "iac", [], None, "K8s 安全训练",
     "Kubernetes Simulator:聚焦 K8s 安全与攻防的训练平台,以 IaC 方式构建可复现靶场。"),
    ("whgojp/JavaSecLab", "lab", "web", "docker-compose", [8080], 8080, "Java 漏洞靶场",
     "JavaSecLab:Java 漏洞靶场,系统覆盖反序列化、表达式注入、SSRF 等 Java 生态缺陷。"),

    # ---------- tunnel 内网与隧道 ----------
    ("nginx-proxy/nginx-proxy", "tunnel", "service", "docker", [80, 443], 80, "Docker 反向代理",
     "nginx-proxy:Docker 容器反向代理自动化,依据容器环境变量自动生成并热更新 Nginx 配置。"),
    ("oauth2-proxy/oauth2-proxy", "tunnel", "service", "binary", [4180], 4180, "认证反向代理",
     "OAuth2 Proxy:为内部服务前置认证的反向代理,对接 Google/GitHub/OIDC 等身份源。"),
    ("rathole-org/rathole", "tunnel", "service", "binary", [], None, "反向代理隧道",
     "rathole:轻量高性能反向代理隧道,把内网服务安全暴露到公网,资源占用低。"),
    ("Shopify/toxiproxy", "tunnel", "service", "docker", [8474], 8474, "故障模拟代理",
     "Toxiproxy:TCP 代理,用于模拟延迟、超时与断连等网络故障,验证系统韧性。"),
    ("ekzhang/bore", "tunnel", "cli", "binary", [], None, "极简隧道",
     "bore:极简 CLI 隧道工具,一行命令把本地端口暴露到远端,适合快速联调。"),
    ("nicocha30/ligolo-ng", "tunnel", "cli", "binary", [], None, "隧道与横向",
     "Ligolo-ng:隧道与横向移动工具,通过 TUN 接口把内网流量透明接入,配合代理链做授权渗透。"),
    ("tobychui/zoraxy", "tunnel", "web", "docker", [8000], 8000, "HTTP 反代管理器",
     "Zoraxy:通用 HTTP 反向代理与转发管理器,带 Web 面板,便于自托管服务统一入口。"),

    # ---------- defense 蜜罐与防守 ----------
    ("crowdsecurity/crowdsec", "defense", "service", "docker", [], None, "协同防护",
     "CrowdSec:开源 IDS/IPS 与行为检测平台,基于社区共享的攻击签名做协同封禁。"),
    ("bunkerity/bunkerweb", "defense", "web", "docker", [80, 443], 443, "Web 应用防火墙",
     "BunkerWeb:云原生 Web 应用防火墙,开箱集成 ModSecurity/CRS,支持容器与 K8s 部署。"),
    ("owasp-modsecurity/ModSecurity", "defense", "service", "source", [], None, "WAF 引擎",
     "ModSecurity:跨平台开源 Web 应用防火墙引擎,配合 OWASP CRS 拦截常见 Web 攻击。"),
    ("telekom-security/tpotce", "defense", "web", "docker", [64297, 443], 64297, "多蜜罐平台",
     "T-Pot:一体化多蜜罐平台,集成 20+ 蜜罐与可视化面板,用于攻击面诱捕与情报采集。"),
    ("OISF/suricata", "defense", "service", "source", [], None, "网络 IDS",
     "Suricata:高性能网络入侵检测与防御引擎,支持规则匹配、协议解析与流量日志。"),
    ("cowrie/cowrie", "defense", "service", "docker", [2222], 2222, "SSH 蜜罐",
     "Cowrie:中交互 SSH/Telnet 蜜罐,记录暴力破解与交互命令,用于攻击行为研究。"),
    ("ossec/ossec-hids", "defense", "service", "source", [], None, "主机 IDS",
     "OSSEC:开源主机入侵检测系统,覆盖日志分析、文件完整性监控与主动响应。"),
    ("hacklcx/HFish", "defense", "web", "docker-compose", [4433], 4433, "企业蜜罐",
     "HFish:企业级蜜罐平台,支持多协议诱捕与威胁感知,部署简单。"),

    # ---------- intel 威胁情报 ----------
    ("OpenCTI-Platform/opencti", "intel", "web", "docker-compose", [8080], 8080, "情报平台",
     "OpenCTI:开源网络威胁情报平台,以 STIX 2.1 组织实体与关系,支撑情报关联分析。"),
    ("MISP/MISP", "intel", "web", "docker-compose", [80, 443], 443, "情报共享",
     "MISP:开源威胁情报共享平台,标准化 IOC 存储与交换,广泛用于跨组织协同。"),
    ("intelowlproject/IntelOwl", "intel", "web", "docker-compose", [8000], 8000, "情报聚合",
     "IntelOwl:威胁情报聚合与分析平台,批量调用多源引擎对 IOC 做富化与研判。"),
    ("yeti-platform/yeti", "intel", "web", "docker-compose", [80], 80, "情报管理",
     "YETI:面向日常研判的威胁情报库,统一管理观察对象、IOC 与关联关系。"),
    ("thalesgroup-cert/Watcher", "intel", "web", "docker-compose", [80], 80, "情报监控",
     "Watcher:AI 辅助的网络威胁情报监控平台,聚合情报源并对可疑活动告警。"),
    ("certtools/intelmq", "intel", "service", "docker-compose", [], None, "情报处理流水线",
     "IntelMQ:面向 CERT 与安全团队的情报处理流水线,标准化采集、解析与分发。"),
    ("microsoft/msticpy", "intel", "cli", "source", [], None, "微软情报工具",
     "msticpy:微软威胁情报安全工具库,用于日志、情报与调查数据的分析编排。"),

    # ---------- network-engineering-defense 网络与工程防御 ----------
    ("javascript-obfuscator/javascript-obfuscator", "network-engineering-defense", "cli", "source", [], None, "JS 混淆器",
     "JavaScript Obfuscator:功能完整的 JS/Node 代码混淆器,提供控制流变换、字符串加密与死代码注入。"),
    ("burrowers/garble", "network-engineering-defense", "cli", "source", [], None, "Go 混淆",
     "garble:Go 构建混淆工具,重命名标识符、剥离调试信息并支持字面量加密。"),
    ("dashingsoft/pyarmor", "network-engineering-defense", "cli", "source", [], None, "Python 保护",
     "PyArmor:Python 脚本混淆与加密工具,支持绑定机器与过期控制,保护商业代码。"),
    ("x64dbg/ScyllaHide", "network-engineering-defense", "cli", "source", [], None, "反反调试",
     "ScyllaHide:用户态反反调试插件,绕过常见调试器检测,配合 x64dbg 做动态分析。"),
    ("mandiant/flare-floss", "network-engineering-defense", "cli", "binary", [], None, "混淆字符串求解",
     "FLOSS:Mandiant 的混淆字符串自动求解器,静态提取样本中被编码或加密的字符串。"),
    ("HyperDbg/HyperDbg", "network-engineering-defense", "cli", "source", [], None, "硬件调试器",
     "HyperDbg:基于虚拟化的调试器,支持隐蔽断点与内核级追踪,用于深度分析。"),
    ("Guardsquare/proguard", "network-engineering-defense", "cli", "binary", [], None, "Java 混淆",
     "ProGuard:Java 字节码优化与混淆器,压缩体积并重命名符号,是 Android 加固的基础环节。"),
]

LICENSE_OK = {"MIT", "Apache-2.0", "GPL-2.0", "GPL-3.0", "AGPL-3.0", "BSD-2-Clause",
              "BSD-3-Clause", "MPL-2.0", "ISC", "Unlicense", "EUPL-1.2", "NOASSERTION", "UNKNOWN"}


def gh(path):
    h = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request("https://api.github.com" + path, headers=h)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 502, 503):
                time.sleep(5 * (attempt + 1))
                continue
            return e.code, {}
        except Exception:  # noqa: BLE001
            time.sleep(3)
    return 0, {}


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def deploy_command(full_name, method):
    url = "https://github.com/" + full_name
    repo = full_name.split("/", 1)[1]
    if method == "docker-compose":
        return "git clone %s && cd %s && docker compose up -d" % (url, repo)
    if method == "docker":
        return "git clone %s && cd %s && docker build -t %s . && docker run -d %s" % (url, repo, repo.lower(), repo.lower())
    return "git clone %s && cd %s" % (url, repo)


def main():
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    have_slug = {t.get("slug") for t in payload["tools"]}
    have_repo = {(t.get("repo") or "").split("/")[-1].lower() for t in payload["tools"]}

    added, skipped, report = [], [], []
    for full_name, cat, form, method, ports, dport, name_zh, summary in PICKS:
        st, j = gh("/repos/" + full_name)
        if st != 200:
            skipped.append((full_name, "HTTP %s" % st))
            print("SKIP  %-46s HTTP %s" % (full_name, st))
            continue
        lic = ((j.get("license") or {}).get("spdx_id") or "UNKNOWN")
        if j.get("archived"):
            skipped.append((full_name, "archived"))
            print("SKIP  %-46s archived" % full_name)
            continue
        if lic not in LICENSE_OK:
            skipped.append((full_name, "license %s" % lic))
            print("SKIP  %-46s license=%s" % (full_name, lic))
            continue
        repo_name = full_name.split("/", 1)[1]
        sl = slugify(repo_name)
        if sl in have_slug or repo_name.lower() in have_repo:
            skipped.append((full_name, "duplicate"))
            print("SKIP  %-46s duplicate(%s)" % (full_name, sl))
            continue

        payload["tools"].append({
            "slug": sl,
            "name": repo_name,
            "name_zh": name_zh,
            "category_id": cat,
            "summary": summary,
            "description": summary,
            "detail_url": "/tools/%s.html" % sl,
            "repo": full_name,
            "docs_url": "https://github.com/" + full_name,
            "deploy": {
                "method": method,
                "command": deploy_command(full_name, method),
                "compose_file": None,
                "image": None,
            },
            "ports": ports,
            "default_port": dport,
            "form": form,
            "credentials": [],
            "gitmcp": {"enabled": True, "url": "https://gitmcp.io/" + full_name},
            "labels": [cat, method],
            "upstream": {
                "lastCheck": TODAY,
                "alive": True,
                "stars": j.get("stargazers_count"),
                "pushedAt": (j.get("pushed_at") or "")[:19] + "Z",
                "license": lic,
            },
        })
        have_slug.add(sl)
        have_repo.add(repo_name.lower())
        added.append(full_name)
        report.append((full_name, cat, j.get("stargazers_count"), lic))
        print("OK    %-46s %-26s ★%-6d %s" % (full_name, cat, j.get("stargazers_count") or 0, lic))
        sys.stdout.flush()
        time.sleep(0.7)

    PAYLOAD.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n新增 %d 条,跳过 %d 条,工具总数 %d" % (len(added), len(skipped), len(payload["tools"])))
    if skipped:
        print("跳过明细:")
        for f, why in skipped:
            print("   %-46s %s" % (f, why))
    print("\n分类分布:")
    from collections import Counter
    print("  ", dict(Counter(t["category_id"] for t in payload["tools"])))

    rp = ROOT / "scripts" / "upstream-audit" / "category-ingest-report.json"
    json.dump({"at": TODAY, "added": [{"repo": r[0], "category": r[1], "stars": r[2], "license": r[3]} for r in report],
               "skipped": [{"repo": s[0], "reason": s[1]} for s in skipped]},
              open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("报告 -> %s" % rp)


if __name__ == "__main__":
    main()
