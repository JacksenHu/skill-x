---
name: pack-attack-surface
description: >-
  Attack-surface mapping and security review expert pack (meta-skill).
  Orchestrates pentest-methodology, API/cloud/supply-chain security skills,
  security-and-hardening and verification-run-hygiene into one workflow: scope,
  enumeration, hypothesis ranking, precise validation and remediation.
license: MIT
compatibility: Meta-skill orchestration. Requires Python 3; target access must be authorized.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: 猎界
  aliases:
    - 猎界
    - 猎界专家团
    - 攻击面专家团
    - AttackSurface
    - pack-attack-surface
  name-zh: 猎界 · 攻击面测绘与安全加固专家团
  description-zh: 从授权范围出发测绘 Web/API/云/供应链攻击面,按影响排序假设、精确验证并给出可复测的修复建议。
  category: pentest
orchestration:
  children:
    - pentest-methodology
    - dhicoc/dsh-reverse-skill/api-security
    - dhicoc/dsh-reverse-skill/pentest-tools
    - dhicoc/dsh-reverse-skill/src-hunter
    - dhicoc/dsh-reverse-skill/cloud-k8s
    - dhicoc/dsh-reverse-skill/supply-chain-security
    - addyosmani/agent-skills/security-and-hardening
    - verification-run-hygiene
---
# 攻击面测绘与安全加固工作流（猎界）

你现在要完成一次授权范围内的攻击面测绘与安全审查。你已安装以下技能，请按步骤串联使用：

- **pentest-methodology**：范围固化、资产清点、请求矩阵、假设排序与验证
- **api-security / pentest-tools / src-hunter**：API、工具链与 SRC 场景的漏洞定位
- **cloud-k8s / supply-chain-security**：云原生与供应链攻击面
- **security-and-hardening**：把发现转成结构性修复建议
- **verification-run-hygiene**：让每条发现可复现、可复测

## 工作原则

先圈定授权边界，再枚举攻击面，再按影响排序。验证只用最小请求集，越权类发现必须拿到“同资源、异身份”的对照证据。越过授权边界的操作不做。

## 步骤 1：范围与规则

使用 **pentest-methodology** 完成：

- 固化授权范围、时间窗、禁止项和证据目录
- 明确目标资产与业务预期行为
- 建立端点、方法、参数与鉴权要求清单

输出：授权范围清单、证据目录结构、初步资产表。

## 步骤 2：攻击面枚举

使用 **pentest-methodology** + **api-security** + **src-hunter** 完成：

- 枚举子域、端口、接口、前端资源、第三方依赖
- 梳理 API 鉴权模型、参数注入面、文件/上传面
- 使用 **cloud-k8s** 与 **supply-chain-security** 检查云配置和依赖风险

输出：攻击面清单、请求矩阵、风险候选列表。

## 步骤 3：假设排序与精确验证

使用 **pentest-methodology** + **pentest-tools** 完成：

- 按影响 × 可达性 × 验证成本排序
- 只读验证优先；越权必须做异身份对照
- 记录 WAF/限速/绕过尝试，但不压测

输出：假设优先级列表、逐条可复现发现与证据。

## 步骤 4：修复与复测

使用 **security-and-hardening** + **verification-run-hygiene** 完成：

- 每条发现给出修复建议与结构性缓解
- 定义复测标准：修复后用什么最小请求验证通过
- 整理报告与证据包，未闭环项单列

输出：安全审查报告、证据包、复测清单。

## 最终输出

整合为一份攻击面测绘交付包：

1. **授权范围与规则**
2. **攻击面与请求矩阵**
3. **发现清单与证据**
4. **修复建议与复测标准**、未闭环项
