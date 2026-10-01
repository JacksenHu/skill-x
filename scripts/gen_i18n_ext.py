#!/usr/bin/env python3
"""批量生成外部套件的中文展示字段(name-zh / description-zh / category)。

只补 i18n-ext.json 里缺失的条目,不覆盖已有人工翻译;category 只取站内已注册枚举。
用法:
  python scripts/gen_i18n_ext.py [--dry-run]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL = ROOT / "external.json"
I18N = ROOT / "showcase" / "i18n-ext.json"

# 本次需要补的套件(可按需扩展)
TARGET_SUITES = {
    "mukul975/Anthropic-Cybersecurity-Skills",
    "zhaoxuya520/reverse-skill",
    "elementalsouls/Claude-BugHunter",
    "SnailSploit/Claude-Red",
    "ljagiello/ctf-skills",
    "yaklang/hack-skills",
    "newliver666/apk-reverse",
}

# 动词前缀 -> 中文动作
VERB = {
    "analyzing": "分析", "analysing": "分析", "detecting": "检测", "hunting": "排查",
    "performing": "执行", "implementing": "落地", "configuring": "配置", "building": "构建",
    "exploiting": "利用", "auditing": "审计", "conducting": "开展", "collecting": "收集",
    "extracting": "提取", "securing": "加固", "deploying": "部署", "testing": "测试",
    "scanning": "扫描", "recovering": "恢复", "triaging": "分诊", "investigating": "调查",
    "monitoring": "监测", "mapping": "测绘", "emulating": "模拟", "operating": "操作",
    "orchestrating": "编排", "integrating": "集成", "managing": "管理", "processing": "处理",
    "profiling": "画像", "prioritizing": "排序", "remediating": "修复", "validating": "校验",
    "verifying": "验证", "generating": "生成", "tracking": "追踪", "containing": "遏制",
    "correlating": "关联", "relaying": "中继", "hardening": "加固", "fuzzing": "模糊测试",
    "parsing": "解析", "modeling": "建模", "executing": "执行", "assessing": "评估",
    "achieving": "达成", "acquiring": "获取", "benchmarking": "基准", "bypassing": "绕过",
    "coercing": "强制", "defending": "防御", "deobfuscating": "去混淆", "designing": "设计",
    "enumerating": "枚举", "eradicating": "清除", "escaping": "逃逸", "evaluating": "评估",
    "intercepting": "拦截", "migrating": "迁移", "red-teaming": "红队", "responding": "响应",
    "reversing": "逆向", "solving": "解题", "harvesting": "抓取", "scraping": "抓取",
    "crawling": "爬取", "attacking": "攻击", "abusing": "滥用", "hacking": "黑客",
    "moving": "移动", "writing": "编写", "reviewing": "审查", "creating": "创建",
    "setting": "设置", "using": "使用", "applying": "应用", "checking": "检查",
}

STOPWORDS = {"for", "with", "and", "of", "the", "to", "in", "on", "by", "via", "from", "at", "an", "a", "or"}

# 名词/技术术语 -> 中文(保留常见的专有名词原文)
TERM = {
    "active-directory": "Active Directory", "acl": "ACL", "abuse": "滥用",
    "privilege-escalation": "提权", "privesc": "提权", "credential": "凭据", "credentials": "凭据",
    "kerberos": "Kerberos", "kerberoasting": "Kerberoasting", "dpapi": "DPAPI",
    "shadow-credentials": "影子凭据", "lateral-movement": "横向移动", "persistence": "持久化",
    "exfiltration": "数据外泄", "command-and-control": "C2", "c2": "C2", "cobalt-strike": "Cobalt Strike",
    "phishing": "钓鱼", "spearphishing": "鱼叉钓鱼", "ransomware": "勒索软件", "malware": "恶意软件",
    "sql-injection": "SQL 注入", "sqli": "SQL 注入", "xss": "XSS", "ssrf": "SSRF", "csrf": "CSRF",
    "xxe": "XXE", "idor": "IDOR", "jwt": "JWT", "oauth": "OAuth", "deserialization": "反序列化",
    "rce": "RCE", "lfi": "LFI", "ssti": "SSTI", "graphql": "GraphQL", "websocket": "WebSocket",
    "cloud": "云", "aws": "AWS", "azure": "Azure", "gcp": "GCP", "kubernetes": "Kubernetes", "k8s": "K8s",
    "container": "容器", "docker": "Docker", "linux": "Linux", "windows": "Windows", "macos": "macOS",
    "ios": "iOS", "android": "Android", "mobile": "移动", "api": "API", "network": "网络", "dns": "DNS",
    "email": "邮件", "endpoint": "端点", "siem": "SIEM", "splunk": "Splunk", "forensic": "取证",
    "memory": "内存", "disk": "磁盘", "osint": "OSINT", "threat-intelligence": "威胁情报",
    "mitre": "MITRE", "attack": "ATT&CK", "reverse": "逆向", "binary": "二进制", "apk": "APK",
    "dex": "DEX", "crypto": "加密", "pwn": "PWN", "web": "Web", "forensics": "取证", "misc": "杂项",
    "security": "安全", "analysis": "分析", "detection": "检测", "exploitation": "利用",
    "vulnerability": "漏洞", "vulnerabilities": "漏洞", "assessment": "评估", "audit": "审计",
    "compliance": "合规", "incident": "事件", "response": "响应", "recovery": "恢复",
    "backup": "备份", "hardening": "加固", "zero-trust": "零信任", "identity": "身份", "iam": "IAM",
    "saml": "SAML", "sso": "SSO", "scim": "SCIM", "firewall": "防火墙", "ids": "IDS", "ips": "IPS",
    "waf": "WAF", "edr": "EDR", "mfa": "MFA", "ldap": "LDAP", "ntlm": "NTLM", "dcsync": "DCSync",
    "pass-the-hash": "哈希传递", "pass-the-ticket": "票据传递", "golden-ticket": "黄金票据",
    "mimikatz": "Mimikatz", "bloodhound": "BloodHound", "netexec": "NetExec", "impacket": "Impacket",
    "metasploit": "Metasploit", "burpsuite": "Burp Suite", "nmap": "Nmap", "wireshark": "Wireshark",
    "zeek": "Zeek", "volatility": "Volatility", "ghidra": "Ghidra", "ida": "IDA", "radare2": "radare2",
    "frida": "Frida", "jadx": "JADX", "dnspy": "dnSpy", "apktool": "Apktool", "mobsf": "MobSF",
    "hashcat": "Hashcat", "aircrack": "Aircrack", "sqlmap": "SQLMap", "nikto": "Nikto",
    "nessus": "Nessus", "openvas": "OpenVAS", "gophish": "GoPhish", "evilginx": "Evilginx",
    "covenant": "Covenant", "havoc": "Havoc", "sliver": "Sliver", "grype": "Grype", "trivy": "Trivy",
    "semgrep": "Semgrep", "gitleaks": "Gitleaks", "snyk": "Snyk", "falco": "Falco",
    "cis": "CIS", "nist": "NIST", "hipaa": "HIPAA", "gdpr": "GDPR", "pci": "PCI-DSS",
    "iso": "ISO", "soc": "SOC", "cmmc": "CMMC", "rmf": "RMF", "csf": "CSF",
    "firmware": "固件", "uefi": "UEFI", "bootkit": "Bootkit", "rootkit": "Rootkit", "shellcode": "Shellcode",
    "exploit": "利用", "injection": "注入", "overflow": "溢出", "race-condition": "条件竞争",
    "cryptography": "密码学", "encryption": "加密", "decryption": "解密", "cipher": "密码", "rsa": "RSA",
    "ecc": "ECC", "aes": "AES", "lattice": "格", "steganography": "隐写", "protocol": "协议",
    "vm": "虚拟机", "bytecode": "字节码", "js": "JS", "javascript": "JavaScript", "dotnet": ".NET",
    "go": "Go", "rust": "Rust", "elf": "ELF", "pe": "PE", "smali": "Smali", "obfuscation": "混淆",
    "deobfuscation": "去混淆", "unpacking": "脱壳", "smart-contract": "智能合约", "blockchain": "区块链",
    "web3": "Web3", "defi": "DeFi", "llm": "LLM", "ai": "AI", "ml": "ML", "prompt-injection": "提示注入",
    "model": "模型", "rag": "RAG", "vector": "向量", "iot": "物联网", "ot": "OT", "ics": "ICS",
    "scada": "SCADA", "plc": "PLC", "modbus": "Modbus", "bluetooth": "蓝牙", "ble": "BLE",
    "wifi": "WiFi", "wpa": "WPA", "wps": "WPS", "radio": "无线电", "sdr": "SDR", "carving": "文件雕刻",
    "timeline": "时间线", "artifact": "痕迹", "artifacts": "痕迹", "registry": "注册表",
    "prefetch": "预读取", "amcache": "AmCache", "lnk": "LNK", "pst": "PST", "mft": "MFT",
    "volatility3": "Volatility 3", "yara": "YARA", "sigma": "Sigma", "misp": "MISP", "opencti": "OpenCTI",
    "stix": "STIX", "taxii": "TAXII", "ioc": "IOC", "iocs": "IOC", "ttps": "TTP", "navigator": "Navigator",
    "trufflehog": "TruffleHog", "shodan": "Shodan", "subfinder": "Subfinder", "scapy": "Scapy",
    "tshark": "TShark", "suricata": "Suricata", "snort": "Snort", "osquery": "Osquery", "sysmon": "Sysmon",
    "lolbas": "LOLBAS", "lolbins": "LOLBins", "wmi": "WMI", "dcom": "DCOM", "macro": "宏", "pdf": "PDF",
    "office": "Office", "vault": "Vault", "hashicorp": "HashiCorp", "cyberark": "CyberArk",
    "okta": "Okta", "entra": "Entra", "graph": "Graph", "smb": "SMB", "ipv6": "IPv6", "bgp": "BGP",
    "vlan": "VLAN", "arp": "ARP", "icmp": "ICMP", "tls": "TLS", "ssl": "SSL", "http": "HTTP",
    "https": "HTTPS", "dns-tunneling": "DNS 隧道", "domain-fronting": "域前置", "beaconing": "信标",
    "sandbox": "沙箱", "sandbox-escape": "沙箱逃逸", "container-escape": "容器逃逸",
    "recon": "侦察", "reconnaissance": "侦察", "red-team": "红队", "redteam": "红队",
    "purple-team": "紫队", "penetration-test": "渗透测试", "pentest": "渗透测试", "bug-bounty": "漏洞赏金",
    "writeup": "复盘报告", "report": "报告", "reporting": "报告", "methodology": "方法论",
    "checklist": "清单", "triage": "分诊", "threat-hunting": "威胁狩猎", "threat-modeling": "威胁建模",
    "attack-surface": "攻击面", "attack-chain": "攻击链", "kill-chain": "杀伤链", "supply-chain": "供应链",
    "dependency-confusion": "依赖混淆", "typosquatting": "仿冒", "shadow-api": "影子 API",
    "shadow-it": "影子 IT", "mass-assignment": "批量赋值", "open-redirect": "开放重定向",
    "host-header": "Host 头", "http-smuggling": "HTTP 走私", "request-smuggling": "请求走私",
    "cache-poisoning": "缓存投毒", "cache-deception": "缓存欺骗", "parameter-pollution": "参数污染",
    "template-injection": "模板注入", "crlf": "CRLF", "clickjacking": "点击劫持", "cors": "CORS",
    "file-upload": "文件上传", "path-traversal": "路径穿越", "directory-traversal": "目录穿越",
    "nosql": "NoSQL", "type-juggling": "类型混淆", "prototype-pollution": "原型污染",
    "format-string": "格式化字符串", "heap-exploitation": "堆利用", "stack-overflow": "栈溢出",
    "rop": "ROP", "kernel-exploitation": "内核利用", "symbolic-execution": "符号执行",
    "fuzzing": "模糊测试", "hardware-security": "硬件安全", "tpm": "TPM", "secure-boot": "安全启动",
    "hsm": "HSM", "key-management": "密钥管理", "secrets-management": "密钥管理",
    "secrets-scanning": "密钥扫描", "secret-scanning": "密钥扫描", "post-quantum": "后量子",
    "signature": "签名", "sigstore": "Sigstore", "cosign": "Cosign", "provenance": "来源",
    "sbom": "SBOM", "sca": "SCA", "dast": "DAST", "sast": "SAST", "owasp": "OWASP", "zap": "ZAP",
    "restler": "RESTler", "postman": "Postman", "openapi": "OpenAPI", "rest": "REST", "soap": "SOAP",
    "grpc": "gRPC", "serverless": "Serverless", "lambda": "Lambda", "terraform": "Terraform", "iac": "IaC",
    "helm": "Helm", "kubesec": "KubeSec", "opa": "OPA", "rbac": "RBAC", "pfsense": "pfSense",
    "tailscale": "Tailscale", "cloudflare": "Cloudflare", "beyondcorp": "BeyondCorp",
    "applocker": "AppLocker", "fido2": "FIDO2", "duo": "Duo", "saviynt": "Saviynt",
    "sailpoint": "SailPoint", "pam": "PAM", "honeytoken": "蜜标", "honeytokens": "蜜标",
    "honeypot": "蜜罐", "decoy": "诱饵", "deception": "欺骗", "canary": "金丝雀", "darkweb": "暗网",
    "vishing": "语音钓鱼", "smishing": "短信钓鱼", "qr-code": "二维码", "pretext": "话术",
    "social-engineering": "社会工程", "physical-intrusion": "物理入侵", "wireless": "无线",
    "wpa2": "WPA2", "wpa3": "WPA3", "wpa-enterprise": "WPA 企业", "man-in-the-middle": "中间人",
    "arp-spoofing": "ARP 欺骗", "ssl-stripping": "SSL 剥离", "ntlm-relay": "NTLM 中继",
    "certificate": "证书", "ca": "CA", "openssl": "OpenSSL", "pki": "PKI", "adcs": "ADCS",
    "forest-trust": "林信任", "tiered": "分层", "scanner": "扫描器", "enumeration": "枚举",
    "zone-transfer": "区域传送", "subdomain": "子域", "takeover": "接管", "brute-force": "暴力破解",
    "password-cracking": "密码破解", "hash-cracking": "哈希破解", "cracking": "破解", "wordlist": "字典",
    "rate-limiting": "速率限制", "captcha": "验证码", "captcha-bypass": "验证码绕过", "mfa-bypass": "MFA 绕过",
    "authentication": "认证", "authorization": "授权", "access-control": "访问控制", "session": "会话",
    "cookie": "Cookie", "token": "令牌", "algorithm-confusion": "算法混淆", "oidc": "OIDC",
    "oauth2": "OAuth2", "device-code": "设备码", "scope": "作用域", "consent": "授权同意",
    "token-theft": "令牌窃取", "assertion": "断言", "identity-federation": "身份联邦",
    "secrets": "密钥", "secret": "密钥", "key-pair": "密钥对", "key-storage": "密钥存储",
    "key": "密钥", "leak": "泄露", "exposure": "暴露", "misconfig": "配置错误", "misconfiguration": "配置错误",
    "bypass": "绕过", "hunt": "排查", "toolkit": "工具包", "tools": "工具", "course": "课程",
    "development": "开发", "dev": "开发", "auditing": "审计", "offensive": "攻击", "defensive": "防御",
    "ir": "应急响应", "playbook": "剧本", "dashboard": "仪表盘", "framework": "框架",
    "benchmark": "基准", "aging": "老化", "sla": "SLA", "kpi": "KPI", "metrics": "指标",
    "ticketing": "工单", "escalation": "升级", "matrix": "矩阵", "escalation-matrix": "升级矩阵",
    "attack-pattern": "攻击模式", "actor": "组织", "actor-profile": "组织画像", "campaign": "活动",
    "attribution": "归因", "profile": "画像", "group": "组织", "groups": "组织", "threat-actor": "威胁组织",
    "threat-landscape": "威胁态势", "threat-feed": "威胁情报源", "intel": "情报", "intelligence": "情报",
    "enrichment": "富化", "correlation": "关联", "aggregation": "聚合", "sharing": "共享",
    "lifecycle": "生命周期", "management": "管理", "governance": "治理", "recertification": "复审",
    "review": "审查", "certification": "认证", "auditing": "审计", "access": "访问", "recertification": "复审",
    "privileged": "特权", "privilege": "特权", "privesc": "提权", "least-privilege": "最小权限",
    "just-in-time": "即时", "standing": "常驻", "zero-standing": "零常驻", "boundary": "边界",
    "microsegmentation": "微分段", "segmentation": "分段", "isolation": "隔离", "browser-isolation": "浏览器隔离",
    "provisioning": "供应", "deprovisioning": "注销", "identity-governance": "身份治理",
    "role-mining": "角色挖掘", "role": "角色", "entitlement": "授权", "entitlements": "授权",
    "discovery": "发现", "inventory": "盘点", "asset": "资产", "criticality": "关键性",
    "scoring": "评分", "cvss": "CVSS", "prioritization": "优先级", "kev": "KEV", "catalog": "目录",
    "triage": "分诊", "triage": "分诊", "remediation": "修复", "remediation": "修复",
    "patch-management": "补丁管理", "patch-tuesday": "补丁星期二", "patching": "补丁",
    "vulnerability-management": "漏洞管理", "vulnerability-scanning": "漏洞扫描",
    "vulnerability-scan": "漏洞扫描", "scan": "扫描", "scanning": "扫描", "sweep": "扫描",
    "assessment": "评估", "assessment": "评估", "audit": "审计", "testing": "测试",
    "fuzz": "模糊测试", "fuzzing": "模糊测试", "afl": "AFL", "aflplusplus": "AFL++",
    "security-testing": "安全测试", "api-testing": "API 测试", "api-security": "API 安全",
    "web-application": "Web 应用", "web-app": "Web 应用", "thick-client": "厚客户端",
    "mobile-app": "移动应用", "mobile-application": "移动应用", "mobsf": "MobSF",
    "static-analysis": "静态分析", "dynamic-analysis": "动态分析", "runtime": "运行时",
    "self-protection": "自保护", "rasp": "RASP", "monitoring": "监测", "observability": "可观测性",
    "logging": "日志", "logs": "日志", "log": "日志", "audit-log": "审计日志", "audit-logs": "审计日志",
    "event-logs": "事件日志", "event-log": "事件日志", "syslog": "Syslog", "fluentd": "Fluentd",
    "rsyslog": "Rsyslog", "forwarding": "转发", "centralization": "集中", "baselining": "基线",
    "anomaly": "异常", "anomalies": "异常", "detection": "检测", "correlation": "关联",
    "signature": "签名", "signatures": "签名", "rule": "规则", "rules": "规则", "detection-rules": "检测规则",
    "detection-rule": "检测规则", "use-case": "用例", "use-cases": "用例", "tuning": "调优",
    "alert": "告警", "alerts": "告警", "fatigue": "疲劳", "false-positive": "误报",
    "triage": "分诊", "investigation": "调查", "response": "响应", "containment": "遏制",
    "eradication": "清除", "remediation": "修复", "lessons-learned": "复盘", "post-incident": "事后",
    "communication": "沟通", "template": "模板", "templates": "模板", "template": "模板",
    "notification": "通知", "workflow": "流程", "process": "流程", "procedure": "规程",
    "procedures": "规程", "policy": "策略", "policies": "策略", "standard": "标准", "standards": "标准",
    "baseline": "基线", "benchmark": "基准", "hardening": "加固", "configuration": "配置",
    "config": "配置", "setting": "设置", "settings": "设置", "security-controls": "安全控制",
    "controls": "控制", "control": "控制", "guardrails": "护栏", "guardrail": "护栏",
    "mitigations": "缓解", "mitigation": "缓解", "defense": "防御", "protection": "防护",
    "attacks": "攻击", "techniques": "技术", "services": "服务", "level": "级别",
    "image": "镜像", "pipeline": "流水线", "local": "本地", "diff": "差分", "ninja": "Ninja",
    "bb": "漏洞赏金", "ctf": "CTF", "bugcrowd": "Bugcrowd", "sec": "安全", "auth": "认证",
    "vuln": "漏洞", "vulns": "漏洞", "mindset": "思维", "tricks": "技巧", "escape": "逃逸",
    "evasion": "规避", "dumping": "导出", "forging": "伪造", "spraying": "喷洒", "hijacking": "劫持",
    "sideloading": "侧加载", "hollowing": "挖空", "hooking": "Hook", "injecting": "注入",
    "reverse-engineering": "逆向工程", "anti-debugging": "反调试", "anti-forensics": "反取证",
    "exploit-development": "漏洞利用开发", "exploit-dev": "漏洞利用开发", "initial-access": "初始访问",
    "data-exfiltration": "数据外泄", "crash-analysis": "崩溃分析", "crypto-attacks": "密码攻击",
    "web3-audit": "Web3 审计", "web2-recon": "Web2 侦察", "ctf-sandbox": "CTF 沙箱",
    "solve-challenge": "解题", "pentest-tools": "渗透工具", "threat-hunting": "威胁狩猎",
    "pwn-chain": "PWN 链", "src-hunter": "源码猎人", "windows-ad": "Windows AD",
    "windows-av-evasion": "Windows AV 规避", "wifi-wireless": "WiFi 无线", "hack": "黑客",
    "diagram-generator": "图表生成", "docs-generator": "文档生成", "vm-and-bytecode-reverse": "虚拟机与字节码逆向",
    "dsl-vm-reverse": "DSL/VM 逆向", "edr-bypass-re": "EDR 绕过逆向", "go-rust-reverse": "Go/Rust 逆向",
    "mobile-reverse": "移动逆向", "protocol-reverse": "协议逆向", "binary-ninja-reverse": "Binary Ninja 逆向",
    "code-obfuscation": "代码混淆", "deobfuscation": "去混淆", "jndi-injection": "JNDI 注入",
    "xslt-injection": "XSLT 注入", "email-header-injection": "邮件头注入", "dangling-markup-injection": "悬空标记注入",
    "crlf-injection": "CRLF 注入", "expression-language-injection": "EL 注入", "jwt-oauth-token-attacks": "JWT/OAuth 令牌攻击",
    "graphql-and-hidden-parameters": "GraphQL 与隐藏参数", "http2-specific-attacks": "HTTP/2 攻击",
    "ghost-bits-cast-attack": "Ghost Bits Cast 攻击", "dns-rebinding-attacks": "DNS 重绑定攻击",
    "deeplink-vulnerabilities": "DeepLink 漏洞", "bgp-hijacking-vulnerabilities": "BGP 劫持漏洞",
    "sandbox-escape-techniques": "沙箱逃逸技术", "stack-overflow-and-rop": "栈溢出与 ROP",
    "symbolic-execution-tools": "符号执行工具", "lattice-crypto-attacks": "格密码攻击",
    "rsa-attack-techniques": "RSA 攻击技术", "symmetric-cipher-attacks": "对称密码攻击",
    "classical-cipher-analysis": "古典密码分析", "hash-attack-techniques": "哈希攻击技术",
    "recon-for-sec": "安全侦察", "recon-scope-triage": "侦察范围分诊", "injection-checking": "注入检查",
    "file-access-vuln": "文件访问漏洞", "auth-sec": "认证安全", "api-sec": "API 安全",
    "business-logic-vuln": "业务逻辑漏洞", "mid-engagement-ir-detection": "渗透中途应急检测",
    "identity-federation": "身份联邦", "enterprise-vpn-attack": "企业 VPN 攻击", "thick-client": "厚客户端",
    "vmware-vcenter-attack": "VMware vCenter 攻击", "reverse-skill-router": "逆向技能路由",
    "security-arsenal": "安全武器库", "wpa2-psk": "WPA2-PSK", "wpa3-sae": "WPA3-SAE",
    "evil-twin": "邪恶双胞胎", "deauth-disassoc": "去认证", "krack-fragattacks": "KRACK/FragAttacks",
    "lorawan-sub-ghz": "LoRaWAN/Sub-GHz", "zigbee-thread-matter": "Zigbee/Thread/Matter",
    "keylogger-arch": "键盘记录架构", "windows-boundaries": "Windows 边界", "windows-mitigations": "Windows 缓解",
    "vuln-classes": "漏洞类别", "fast-checking": "快速检查", "bug-identification": "漏洞识别",
    "kernel-exploitation": "内核利用", "heap-exploitation": "堆利用", "browser-exploitation": "浏览器利用",
    "format-string-exploitation": "格式化字符串利用", "race-condition": "条件竞争",
    "hash-attack": "哈希攻击", "cipher-attacks": "密码攻击", "deeplink": "DeepLink",
    "unsafe": "不安全", "insecure": "不安全", "misconfigured": "配置错误", "excessive": "过度",
    "broken": "越权", "sensitive": "敏感", "hidden": "隐藏", "parameters": "参数",
    "common-services": "常见服务", "unauthorized-access": "未授权访问", "insecure-files": "不安全文件",
    "passwordless": "无密码", "passwordless-auth": "无密码认证", "standalone": "独立",
    "agentless": "无代理", "threats": "威胁", "actors": "组织", "actor": "组织",
    "leak-site": "泄露站点", "paste-site": "粘贴站点", "dark-web": "暗网",
    "history": "历史", "connections": "连接", "storage": "存储", "accounts": "账号",
    "account": "账号", "misconfigurations": "配置错误", "drift": "漂移", "attempts": "尝试",
    "patterns": "模式", "behavior": "行为", "events": "事件", "rules": "规则",
    "posture": "态势", "coverage": "覆盖", "mapping": "映射", "integration": "集成",
    "scanning": "扫描", "scanner": "扫描器", "source-leak": "源码泄露", "shadow-api": "影子 API",
    "m365": "M365", "m365-entra": "M365/Entra", "entra-attack": "Entra 攻击",
    "okta-attack": "Okta 攻击", "azure-storage": "Azure 存储", "s3": "S3", "bucket": "存储桶",
    "cloud-iam": "云 IAM", "iam-deep": "IAM 深入", "cloud-k8s": "云与 Kubernetes",
    "firmware-pentest": "固件渗透", "hardware-security": "硬件安全", "ot-ics": "OT/ICS",
    "radio-sdr": "无线电 SDR", "traffic-analysis": "流量分析", "pcap": "PCAP",
    "digital-forensics": "数字取证", "memory-forensics": "内存取证", "email-security": "邮件安全",
    "database-security": "数据库安全", "llm-security": "LLM 安全", "ai-security": "AI 安全",
    "supply-chain-security": "供应链安全", "web3": "Web3", "meme-coin": "Meme 币",
    "smart-contract": "智能合约", "foundry": "Foundry", "defi-attack": "DeFi 攻击",
    "wifi-recon": "WiFi 侦察", "bluetooth-ble": "蓝牙 BLE", "bluetooth-classic": "蓝牙经典",
    "offensive-ai-security": "攻击 AI 安全", "offensive-api-abuse": "攻击 API 滥用",
    "offensive-api-security": "攻击 API 安全", "offensive-active-directory": "攻击 Active Directory",
    "offensive-basic-exploitation": "攻击基础利用", "offensive-bug-identification": "攻击漏洞识别",
    "offensive-business-logic": "攻击业务逻辑", "offensive-c2-frameworks": "攻击 C2 框架",
    "offensive-cicd-pipeline": "攻击 CI/CD 流水线", "offensive-cicd-secrets": "攻击 CI/CD 密钥",
    "offensive-container-escape": "攻击容器逃逸", "offensive-crash-analysis": "攻击崩溃分析",
    "offensive-crypto-attacks": "攻击密码", "offensive-dependency-confusion": "攻击依赖混淆",
    "offensive-deserialization": "攻击反序列化", "offensive-edr-evasion": "攻击 EDR 规避",
    "offensive-file-upload": "攻击文件上传", "offensive-fuzzing": "攻击模糊测试",
    "offensive-graphql": "攻击 GraphQL", "offensive-idor": "攻击 IDOR", "offensive-initial-access": "攻击初始访问",
    "offensive-jwt": "攻击 JWT", "offensive-lateral-movement": "攻击横向移动", "offensive-netexec": "攻击 NetExec",
    "offensive-oauth": "攻击 OAuth", "offensive-open-redirect": "攻击开放重定向", "offensive-osint": "攻击 OSINT",
    "offensive-parameter-pollution": "攻击参数污染", "offensive-persistence": "攻击持久化",
    "offensive-phishing": "攻击钓鱼", "offensive-race-condition": "攻击条件竞争", "offensive-rce": "攻击 RCE",
    "offensive-request-smuggling": "攻击请求走私", "offensive-sqli": "攻击 SQL 注入", "offensive-ssrf": "攻击 SSRF",
    "offensive-ssti": "攻击 SSTI", "offensive-tls-attacks": "攻击 TLS", "offensive-toctou": "攻击 TOCTOU",
    "offensive-waf-bypass": "攻击 WAF 绕过", "offensive-xss": "攻击 XSS", "offensive-xxe": "攻击 XXE",
    "offensive-social-engineering": "攻击社会工程", "offensive-advanced-redteam": "攻击高级红队",
    "offensive-data-exfiltration": "攻击数据外泄", "offensive-anti-forensics": "攻击反取证",
    "offensive-iot": "攻击物联网", "offensive-mobile": "攻击移动", "offensive-k8s-attacks": "攻击 K8s",
    "offensive-linux-privesc": "攻击 Linux 提权", "offensive-windows-privesc": "攻击 Windows 提权",
    "offensive-network-attacks": "攻击网络", "offensive-cloud": "攻击云", "offensive-supply-chain": "攻击供应链",
    "offensive-reporting": "攻击报告", "offensive-mitigations": "攻击缓解", "offensive-exploit-development": "攻击漏洞利用开发",
    "detection": "检测", "prevention": "预防", "response": "响应", "recovery": "恢复",
}

CATEGORY_RULES = [
    ("reverse-engineering", ["reverse", "decompil", "deobfuscat", "unpack", "binary", "apk", "dex", "ghidra", "ida-", "radare2", "frida", "jadx", "dnspy", "smali", "bytecode", "vm-", "dotnet-", "js-reverse", "go-rust", "protocol-reverse", "disassembl", "obfuscation", "shellcode", "rop", "exploitation", "kernel-exploit", "heap-exploit", "stack-overflow", "format-string", "pwn", "symbolic-execution", "patch-diff", "unpacking"]),
    ("malware", ["malware", "ransomware", "rootkit", "bootkit", "beacon", "c2", "rat", "trojan", "packed", "macro", "yara", "ioc", "persistence", "sandbox", "cuckoo", "cape", "malpedia", "autoruns", "cobalt"]),
    ("forensics", ["forensic", "memory", "volatility", "artifact", "timeline", "evtx", "registry", "prefetch", "amcache", "carving", "disk-image", "pcap", "wireshark", "network-traffic", "network-forensic", "recovery", "plaso", "timesketch", "kape", "autopsy", "rekall", "hayabusa", "chainsaw"]),
    ("data", ["scrap", "crawl", "osint", "spider", "harvest", "collecting-open-source", "shodan", "dnstwist", "spiderfoot", "subdomain"]),
    ("dev-workflow", ["ci-cd", "devsecops", "pipeline", "gitlab", "github-actions", "terraform", "iac", "sbom", "supply-chain", "dependency-confusion", "secret-scanning", "compliance", "iso-", "nist-", "gdpr", "hipaa", "pci-", "cmmc", "rmf", "csf", "soc2", "audit-", "governance", "management", "policy", "workflow", "reporting", "dashboard", "metrics", "kpi", "sla", "ticketing"]),
]

CATEGORY_ZH = {
    "reverse-engineering": "逆向工程",
    "pentest": "渗透测试",
    "malware": "样本分析",
    "forensics": "内存取证",
    "data": "数据抓取",
    "dev-workflow": "工程流程",
    "engineering-hygiene": "工程纪律",
    "web-frontend": "Web 前端",
    "ai-media": "AI 媒体",
}

DESC_TEMPLATE = {
    "reverse-engineering": "逆向工程技能，覆盖{name}相关的样本分析、脱壳、结构与算法还原。",
    "pentest": "渗透测试技能，覆盖{name}相关的攻击面识别、漏洞验证与利用。",
    "malware": "恶意样本分析技能，覆盖{name}相关的取证、行为分析与检测。",
    "forensics": "数字取证技能，覆盖{name}相关的证据提取、时间线重建与持久化分析。",
    "data": "数据获取技能，覆盖{name}相关的抓取、结构化提取与情报整理。",
    "dev-workflow": "工程技能，覆盖{name}相关的流程、合规与自动化。",
}


def translate_name(name: str) -> str:
    if name in TERM:
        return TERM[name]
    parts = name.split("-")
    out = []
    i = 0
    # 先尝试整词/双词短语匹配,再退化为单词
    while i < len(parts):
        matched = None
        for span in (3, 2, 1):
            if i + span <= len(parts):
                cand = "-".join(parts[i:i + span])
                if cand in TERM:
                    matched = (span, TERM[cand])
                    break
        if matched:
            out.append(matched[1])
            i += matched[0]
        else:
            tok = parts[i]
            if tok in STOPWORDS:
                pass
            elif tok in VERB and i == 0:
                out.append(VERB[tok])
            elif tok in TERM:
                out.append(TERM[tok])
            else:
                # 未命中:保留原文(专有名词/未知词)
                out.append(tok)
            i += 1
    # 清理
    text = " ".join(out)
    text = re.sub(r"\s+", " ", text).strip()
    return text or name


def classify(name: str, desc: str = "") -> str:
    n = name.lower()
    for cat, kws in CATEGORY_RULES:
        if any(k in n for k in kws):
            return cat
    return "pentest"


def main():
    dry = "--dry-run" in sys.argv
    ext = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    i18n = json.loads(I18N.read_text(encoding="utf-8"))

    added = 0
    for suite in ext.get("suites", []):
        ns = suite.get("namespace", "")
        if ns not in TARGET_SUITES:
            continue
        bucket = i18n.get(ns)
        if bucket is None:
            bucket = {}
            i18n[ns] = bucket
        for sk in suite.get("skills", []):
            name = sk.get("name", "")
            if not name or name in bucket:
                continue
            name_zh = translate_name(name)
            cat = classify(name, sk.get("description", ""))
            desc_zh = DESC_TEMPLATE.get(cat, "技能「{name}」。").format(name=name_zh)
            bucket[name] = {"name-zh": name_zh, "description-zh": desc_zh, "category": cat}
            added += 1

    print(f"[+] 新增中文条目 {added} 个")
    if dry:
        print("[dry-run] 未写入")
        return 0
    I18N.write_text(json.dumps(i18n, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] 已写入 {I18N}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
