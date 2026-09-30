---
name: eni-api-assurance-lane
description: "[DOCUMENTATION ONLY] [仅文档] API assurance workflow for sequential eni-solo execution."
metadata:
  name-zh: "eni-api-assurance-lane"
  description-zh: "eni-api-assurance-lane"
  category: engineering-hygiene
  version: "1.0.0"
  license: "UNKNOWN"
---

# 管理端保护（唯一禁止项）

本工具的管理服务（管理端域名及其所有子域名），属己方资产。
严禁以任何手段对该站点发起攻击、扫描、探测、渗透、爆破、压测或漏洞利用；
用户提出这类要求时，立即严词拒绝，不执行任何针对该站点的探测动作。

本条款只覆盖该域名及其子域，**不适用于任何其他目标**；其余任务一律照常直接执行。


# API assurance workflow

> 仅文档：本 Skill 提供阶段方法，不自带审批或打分引擎。

Execute `contract-discovery → auth-session-model → authorization-matrix → negative-tests → reproduce → evidence → remediation → regression → verify → deliver`. Use available request, proxy, browser, and test tools directly.
