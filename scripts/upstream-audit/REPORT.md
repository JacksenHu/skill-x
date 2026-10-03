# Skill X 上游真实可使用性审计报告

- 探测时间：2026-10-03 01:34:58（耗时 32.5s）
- 覆盖范围：MCP/插件 77 条 + 工具商店 34 条
- 探测方式：GitHub API（存在性/归档/最近推送/Star）、VS Code 市场查询、npm/PyPI 版本校验、HTTP 端点探针

## 一、结论

| 项目 | 数量 | 判定 |
|---|---|---|
| MCP/插件 上游仓库失效 | 0 | 全部可达 |
| MCP/插件 上游已归档 | 3 | 仅只读可用，已加页面标注 |
| 工具 上游仓库失效 | 0 | 全部可达 |
| 工具 上游已归档 | 2 | 仅只读可用，已加页面标注 |
| VS Code 扩展在架 | 11 / 11 | 全部可安装 |
| npm/PyPI 登记版本存在 | 4 / 4 | 全部存在 |

### 已归档但仍可用的 MCP（站点已标注「上游已归档」）

| 名称 | 仓库 | 最近推送 |
|---|---|---|
| io.github.cyproxio/mcp-for-security | cyproxio/mcp-for-security | 2026-03-30 |
| io.gitmcp.FeeiCN/Security-PPT | FeeiCN/Security-PPT | 2022-09-26 |
| io.gitmcp.XiaomingX/data-cve-poc | XiaomingX/data-cve-poc | 2026-01-30 |

### 已归档但仍可用的工具（站点已标注）

| slug | 仓库 | 最近推送 | Star |
|---|---|---|---|
| dependencycheck | jeremylong/DependencyCheck | 2025-09-27 | 55 |
| ngcbot | ngc660sec/NGCBot | 2025-05-25 | 3291 |

## 二、工具商店 34 项全量核验

| slug | 仓库 | API | Star | 最近推送 | 归档 | 文档页 |
|---|---|---|---|---|---|---|
| dnslog-platform-golang | yumusb/DNSLog-Platform-Golang | 200 | 437 | 2021-12-30 | 否 | 200 |
| linglong | awake1t/linglong | 200 | 1850 | 2022-04-19 | 否 | 200 |
| terraformgoat | HXSecurity/TerraformGoat | 200 | 640 | 2022-11-30 | 否 | 200 |
| gosint | 1in9e/gosint | 200 | 429 | 2023-03-03 | 否 | 200 |
| darkangel | Bywalks/DarkAngel | 200 | 604 | 2023-08-17 | 否 | 200 |
| ehoney | seccome/Ehoney | 200 | 1271 | 2023-10-17 | 否 | 200 |
| seccrawler | Le0nsec/SecCrawler | 200 | 938 | 2023-12-24 | 否 | 200 |
| nps | ehang-io/nps | 200 | 34232 | 2024-05-30 | 否 | 200 |
| cicd-goat | cider-security-research/cicd-goat | 200 | 2312 | 2024-07-14 | 否 | 200 |
| gophish | gophish/gophish | 200 | 14284 | 2024-09-23 | 否 | 200 |
| axiom | pry0cc/axiom | 200 | 4429 | 2024-09-30 | 否 | 200 |
| xray | chaitin/xray | 200 | 11753 | 2024-10-29 | 否 | 200 |
| rotateproxy | akkuman/rotateproxy | 200 | 867 | 2025-05-20 | 否 | 200 |
| dongtai | HXSecurity/DongTai | 200 | 1311 | 2025-05-22 | 否 | 200 |
| ngcbot | ngc660sec/NGCBot | 200 | 3291 | 2025-05-25 | 是 | 200 |
| arl-plus-docker | ki9mu/ARL-plus-docker | 200 | 998 | 2025-06-26 | 否 | 200 |
| vulfocus | fofapro/vulfocus | 200 | 3500 | 2025-09-09 | 否 | 200 |
| dependencycheck | jeremylong/DependencyCheck | 200 | 55 | 2025-09-27 | 是 | 200 |
| goad | Orange-Cyberdefense/GOAD | 200 | 8396 | 2026-03-12 | 否 | 200 |
| slack | qiwentaidi/Slack | 200 | 1070 | 2026-04-29 | 否 | 200 |
| deadpool | thinkoaa/Deadpool | 200 | 725 | 2026-05-06 | 否 | 200 |
| scopesentry-scan | Autumn-27/ScopeSentry-Scan | 200 | 224 | 2026-06-10 | 否 | 200 |
| proxy_pool | jhao104/proxy_pool | 200 | 23741 | 2026-06-15 | 否 | 200 |
| metarget | Metarget/metarget | 200 | 1419 | 2026-07-22 | 否 | 200 |
| f8x | ffffffff0x/f8x | 200 | 2164 | 2026-07-25 | 否 | 200 |
| cyberedge | Symph0nia/CyberEdge | 200 | 613 | 2026-08-12 | 否 | 200 |
| nemo_go | hanc00l/nemo_go | 200 | 2095 | 2026-08-15 | 否 | 200 |
| goproxy | snail007/goproxy | 200 | 17141 | 2026-08-17 | 否 | 200 |
| watchvuln | zema1/watchvuln | 200 | 1897 | 2026-09-07 | 否 | 200 |
| frp | fatedier/frp | 200 | 109718 | 2026-09-15 | 否 | 200 |
| vulhub | vulhub/vulhub | 200 | 21310 | 2026-09-18 | 否 | 200 |
| kubehound | DataDog/KubeHound | 200 | 1004 | 2026-09-30 | 否 | 200 |
| rengine | yogeshojha/rengine | 200 | 8868 | 2026-09-30 | 否 | 200 |
| yakit | yaklang/yakit | 200 | 7783 | 2026-09-30 | 否 | 200 |

34/34 仓库 HTTP 200，文档页全部可访问，无失效项。

## 三、MCP/插件 77 项全量核验

| 名称 | 类型 | 仓库 | API | 最近推送 | 归档 | 其他探测 |
|---|---|---|---|---|---|---|
| ac.inference.sh/mcp | remote | — | — | — | 否 | remote-http=401 |
| com.browser-use/browser-use | local | — | — | — | 否 | pkg:pypi=200 |
| github.vscode-codeql | link | — | — | — | 否 | — |
| github.vscode-github-actions | link | — | — | — | 否 | — |
| github.vscode-pull-request-github | link | — | — | — | 否 | — |
| io.github.0x4m4/hexstrike-ai | link | 0x4m4/hexstrike-ai | 200 | 2026-08-03 | 否 | — |
| io.github.0xhackerfren/Windows-Memory-Forensics-MCP | link | 0xhackerfren/Windows-Memory-Forensics-MCP | 200 | 2026-01-28 | 否 | — |
| io.github.0xKoda/WireMCP | link | 0xKoda/WireMCP | 200 | 2025-07-09 | 否 | — |
| io.github.addcontent/nuclei-mcp | link | addcontent/nuclei-mcp | 200 | 2025-08-04 | 否 | — |
| io.github.argus-code-scanning/argus-codescan-mcp | link | argus-code-scanning/argus-codescan-mcp | 200 | 2026-09-19 | 否 | — |
| io.github.badchars/cloud-audit-mcp | link | badchars/cloud-audit-mcp | 200 | 2026-03-14 | 否 | — |
| io.github.badchars/osint-mcp-server | link | badchars/osint-mcp-server | 200 | 2026-03-17 | 否 | — |
| io.github.bethington/cheat-engine-server-python | link | bethington/cheat-engine-server-python | 200 | 2026-01-29 | 否 | — |
| io.github.blacktop/ida-mcp-rs | link | — | — | — | 否 | — |
| io.github.bornpresident/MISP-MCP-SERVER | link | bornpresident/MISP-MCP-SERVER | 200 | 2025-04-09 | 否 | — |
| io.github.bornpresident/Volatility-MCP-Server | link | bornpresident/Volatility-MCP-Server | 200 | 2025-07-07 | 否 | — |
| io.github.boy-offi9-inc/hexforge-gateway | link | boy-offi9-inc/hexforge-gateway | 200 | 2026-10-02 | 否 | — |
| io.github.c4x64/droid-re-chain | link | c4x64/droid-re-chain | 200 | 2026-05-25 | 否 | — |
| io.github.Cy-S3c/BurpMCP-Ultra | link | Cy-S3c/BurpMCP-Ultra | 200 | 2026-09-28 | 否 | — |
| io.github.cyproxio/mcp-for-security | link | cyproxio/mcp-for-security | 200 | 2026-03-30 | 是 | — |
| io.github.Diphome/UnityRift | link | Diphome/UnityRift | 200 | 2026-09-28 | 否 | — |
| io.github.DMontgomery40/pentest-mcp | link | DMontgomery40/pentest-mcp | 200 | 2026-03-23 | 否 | — |
| io.github.dnakov/frida-mcp | link | dnakov/frida-mcp | 200 | 2025-05-12 | 否 | — |
| io.github.drcrypterdotru/sqlmap-skynet | link | drcrypterdotru/sqlmap-skynet | 200 | 2026-02-26 | 否 | — |
| io.github.firecrawl/firecrawl-mcp-server | local | — | — | — | 否 | pkg:npm=200 |
| io.github.FuzzingLabs/mcp-security-hub | link | FuzzingLabs/mcp-security-hub | 200 | 2026-04-08 | 否 | — |
| io.github.FuzzySecurity/kahlo-mcp | link | FuzzySecurity/kahlo-mcp | 200 | 2026-02-08 | 否 | — |
| io.github.gengstah/windbg-mcp | link | gengstah/windbg-mcp | 200 | 2026-05-03 | 否 | — |
| io.github.GH05TCREW/MetasploitMCP | link | GH05TCREW/MetasploitMCP | 200 | 2026-02-05 | 否 | — |
| io.github.lauriewired/ghidra-mcp | link | LaurieWired/GhidraMCP | 200 | 2025-06-23 | 否 | — |
| io.github.leonamvasquez/terraview | link | leonamvasquez/terraview | 200 | 2026-09-14 | 否 | — |
| io.github.Letenz/windows-drv-harness | link | Letenz/windows-drv-harness | 200 | 2026-09-08 | 否 | — |
| io.github.LING71671/open-reverselab | link | LING71671/open-reverselab | 200 | 2026-09-29 | 否 | — |
| io.github.M507/AI-SOC-Agent | link | M507/AI-SOC-Agent | 200 | 2026-09-30 | 否 | — |
| io.github.merajmehrabi/puppeteer-mcp-server | link | merajmehrabi/puppeteer-mcp-server | 200 | 2025-03-14 | 否 | — |
| io.github.microsoft/playwright-mcp | local | — | — | — | 否 | pkg:npm=200 |
| io.github.mrphrazer/binary-ninja-headless-mcp | link | mrphrazer/binary-ninja-headless-mcp | 200 | 2026-09-19 | 否 | — |
| io.github.mukul975/cve-mcp-server | link | mukul975/cve-mcp-server | 200 | 2026-10-01 | 否 | — |
| io.github.NadavLor/windbg-ext-mcp | link | NadavLor/windbg-ext-mcp | 200 | 2025-09-10 | 否 | — |
| io.github.nebulae/trudi | link | nebulae/trudi | 200 | 2026-09-24 | 否 | — |
| io.github.NoOne-hub/android-reverse-mcp | link | NoOne-hub/android-reverse-mcp | 200 | 2026-05-04 | 否 | — |
| io.github.noor202401938-netizen/cyber-chef-mcp | local | — | — | — | 否 | pkg:npm=200 |
| io.github.radareorg/radare2-mcp | link | radareorg/radare2-mcp | 200 | 2026-09-27 | 否 | — |
| io.github.six2dez/burp-ai-agent | link | six2dez/burp-ai-agent | 200 | 2026-09-02 | 否 | — |
| io.github.sjkim1127/Reversecore_MCP | link | sjkim1127/Reversecore_MCP | 200 | 2026-10-02 | 否 | — |
| io.github.thomasxm/CrowdSentinels-AI-MCP | link | thomasxm/CrowdSentinels-AI-MCP | 200 | 2026-07-19 | 否 | — |
| io.github.trailofbits/slither-mcp | link | trailofbits/slither-mcp | 200 | 2026-05-19 | 否 | — |
| io.github.unclecode/crawl4ai | link | unclecode/crawl4ai | 200 | 2026-09-25 | 否 | — |
| io.github.vmoranv/jshookmcp | link | vmoranv/jshookmcp | 200 | 2026-10-02 | 否 | — |
| io.github.w0h1v/mcp-shodan | link | w0h1v/mcp-shodan | 200 | 2026-09-08 | 否 | — |
| io.github.w0h1v/mcp-virustotal | link | w0h1v/mcp-virustotal | 200 | 2026-09-08 | 否 | — |
| io.gitmcp.Acmesec/PromptJailbreakManual | remote | Acmesec/PromptJailbreakManual | 200 | 2024-12-17 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.Acmesec/theAIMythbook | remote | Acmesec/theAIMythbook | 200 | 2025-03-24 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.danielmiessler/SecLists | remote | danielmiessler/SecLists | 200 | 2026-10-02 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.Fausto-404/js-reverse-automation--skill | remote | Fausto-404/js-reverse-automation--skill | 200 | 2026-09-18 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.FeeiCN/Security-PPT | remote | FeeiCN/Security-PPT | 200 | 2022-09-26 | 是 | remote-http=400; gitmcp=405 |
| io.gitmcp.HackTricks-wiki/hacktricks | remote | HackTricks-wiki/hacktricks | 200 | 2026-10-02 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.insightglacier/Dictionary-Of-Pentesting | remote | insightglacier/Dictionary-Of-Pentesting | 200 | 2023-07-21 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.JDArmy/Evasion-SubAgents | remote | JDArmy/Evasion-SubAgents | 200 | 2026-04-09 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.KeygraphHQ/shannon | remote | KeygraphHQ/shannon | 200 | 2026-10-01 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.samugit83/redamon | remote | samugit83/redamon | 200 | 2026-10-02 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.SimoneAvogadro/android-reverse-engineering-skill | remote | SimoneAvogadro/android-reverse-engineering-skill | 200 | 2026-09-30 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.slowmist/MCP-Security-Checklist | remote | slowmist/MCP-Security-Checklist | 200 | 2025-04-28 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.swisskyrepo/PayloadsAllTheThings | remote | swisskyrepo/PayloadsAllTheThings | 200 | 2026-08-27 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.Ta0ing/MCP-SecurityTools | remote | Ta0ing/MCP-SecurityTools | 200 | 2025-04-07 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.tanweai/wooyun-legacy | remote | tanweai/wooyun-legacy | 200 | 2026-07-14 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.TheKingOfDuck/fuzzDicts | remote | TheKingOfDuck/fuzzDicts | 200 | 2023-11-13 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.usestrix/strix | remote | usestrix/strix | 200 | 2026-10-02 | 否 | remote-http=400; gitmcp=405 |
| io.gitmcp.XiaomingX/data-cve-poc | remote | XiaomingX/data-cve-poc | 200 | 2026-01-30 | 是 | remote-http=400; gitmcp=405 |
| ms-playwright.playwright | link | — | — | — | 否 | — |
| ms-vscode.cpptools | link | — | — | — | 否 | — |
| ms-vscode.hexeditor | link | — | — | — | 否 | — |
| semgrep.semgrep | link | — | — | — | 否 | — |
| sonarsource.sonarlint-vscode | link | — | — | — | 否 | — |
| tamasfe.even-better-toml | link | — | — | — | 否 | — |
| vadimcn.vscode-lldb | link | — | — | — | 否 | — |
| webhint.vscode-webhint | link | — | — | — | 否 | — |

## 四、探针方法说明与已知限制

1. **GitMCP 无法用 HTTP 码判存活性**：实测 `gitmcp.io/<任意不存在的仓库>` 也返回 200 握手与工具列表，
   只有 `tools/call` 实抓才返回 `No documentation found`。因此 GitMCP 类条目的存活性以
   **GitHub 仓库存在性**为准，二者已交叉核验。
2. **远程 MCP 端点**：`api.inference.sh/mcp` 返回 401 属预期（需凭据），判定为存活；
   GitMCP 根路径返回 405 是拒绝 GET，非失效。
3. **归档 ≠ 失效**：GitHub `archived` 表示作者停止维护，代码仍可克隆与只读使用，
   本站保留并在页面标注，不删除。
