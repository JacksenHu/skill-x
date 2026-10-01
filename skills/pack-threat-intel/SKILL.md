---
name: pack-threat-intel
description: >-
  Threat intelligence workflow: lead, scoring, pivoting, correlation, reporting. Members: CVE/Shodan/VirusTotal/OSINT MCP.
license: MIT
compatibility: Meta-skill orchestration. Member skills/MCP are installed or connected on demand.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: 烛照
  aliases:
    - 烛照
    - Threat Intel
    - pack-threat-intel
  name-zh: 烛照 · 威胁情报分析师
  description-zh: 威胁情报专家团:从 CVE 定级、资产测绘、样本判定到开源情报关联,输出带来源的威胁情报。
  category: malware
orchestration:
  children:
    - io.github.mukul975/cve-mcp-server
    - io.github.w0h1v/mcp-shodan
    - io.github.w0h1v/mcp-virustotal
    - io.github.badchars/osint-mcp-server
---
# 烛照（Threat Intel）

烛照从一条 IOC 或 CVE 出发,用 CVE/EPSS/KEV 定级,用 Shodan/VirusTotal/OSINT 扩线,再落成带来源的情报结论。

## 工作原则

先定边界,再取证,最后成报。任何结论都落到可复现证据,不写“看起来像”。

## 步骤 1:定边界与目标

- 明确本次要回答的问题(漏洞 / 解题 / 情报结论)
- 确认目标与授权范围;涉及攻击面的只做授权内动作

## 步骤 2:调度成员

按任务类型调用 `orchestration.children` 中的对应技能或 MCP:
- 漏洞赏金 → bug-bounty / bb-methodology / offensive-bug-identification / Burp / Nuclei
- CTF → ctf-reverse / ctf-pwn / ctf-crypto / radare2 / frida
- 威胁情报 → cve-mcp-server / shodan / virustotal / osint

## 步骤 3:执行与验证

- 每一步记录输入、命令、输出
- 证据可复现,区分真信号与噪声

## 步骤 4:交付

- 漏洞:PoC + 请求/响应 + 影响评估 + 修复建议
- CTF:flag + 解题过程 + 标准 writeup
- 威胁情报:定级 + 关联链 + 来源 + 建议动作
