---
name: pack-ctf
description: >-
  CTF solving workflow: classification, reverse/pwn/crypto, solving, writeup. Members: CTF skill set + radare2/frida MCP.
license: MIT
compatibility: Meta-skill orchestration. Member skills/MCP are installed or connected on demand.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: 破阵
  aliases:
    - 破阵
    - CTF
    - pack-ctf
  name-zh: 破阵 · CTF 解题员
  description-zh: CTF 战队专家团:按题分类调度逆向、PWN、密码与取证技能,结合 radare2/frida 动态分析,输出标准复盘。
  category: reverse-engineering
orchestration:
  children:
    - ljagiello/ctf-skills/ctf-reverse
    - ljagiello/ctf-skills/ctf-pwn
    - ljagiello/ctf-skills/ctf-crypto
    - ljagiello/ctf-skills/solve-challenge
    - io.github.radareorg/radare2-mcp
    - io.github.dnakov/frida-mcp
---
# 破阵（CTF）

破阵先给题目分类,再调度对应技能与工具:二进制交给 radare2/frida,密码交给现成攻击套路,解完按标准格式写复盘。

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
