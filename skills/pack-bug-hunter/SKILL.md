---
name: pack-bug-hunter
description: >-
  Bug bounty workflow: methodology, recon, bug identification, evidence hygiene, reporting. Members: Claude-BugHunter core, Claude-Red bug identification, Burp/Nuclei MCP.
license: MIT
compatibility: Meta-skill orchestration. Member skills/MCP are installed or connected on demand.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: 寻隙
  aliases:
    - 寻隙
    - Bug Hunter
    - pack-bug-hunter
  name-zh: 寻隙 · 漏洞赏金猎人
  description-zh: 漏洞赏金专家团:攻击面测绘、漏洞识别、证据固化与可复现报告,成员覆盖方法论、红队技巧与 Burp/Nuclei 工具链。
  category: pentest
orchestration:
  children:
    - elementalsouls/Claude-BugHunter/bug-bounty
    - elementalsouls/Claude-BugHunter/bb-methodology
    - SnailSploit/Claude-Red/offensive-bug-identification
    - elementalsouls/Claude-BugHunter/evidence-hygiene
    - io.github.Cy-S3c/BurpMCP-Ultra
    - io.github.FuzzingLabs/mcp-security-hub
---
# 寻隙（Bug Hunter）

寻隙不扫热闹,只追根因。先锁定攻击面与边界,再按漏洞类别逐个验证,拿到可复现的请求与响应证据后,才写进报告。

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
