---
name: pack-cipher-unpack
description: >-
  Cryptography, unpacking and reverse engineering expert pack (meta-skill).
  Orchestrates binary-reverse-engineering, IDA/Ghidra/radare2 reverse skills,
  CyberChef MCP and verification-run-hygiene into a single workflow: triage,
  unpacking, algorithm recovery, crypto decoding and evidence-verified delivery.
license: MIT
compatibility: Meta-skill orchestration. Member skills require Python 3 and the relevant analysis tools; CyberChef MCP installs via npx.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: 密枢
  aliases:
    - 密枢
    - 密枢专家团
    - 加密解密专家团
    - Cipher
    - pack-cipher-unpack
  name-zh: 密枢 · 加密解密与脱壳专家团
  description-zh: 把加壳、混淆与加密产物拆开并验证:样本分诊、脱壳、算法还原、CyberChef 编解码、证据收尾。
  category: reverse-engineering
orchestration:
  children:
    - binary-reverse-engineering
    - dhicoc/dsh-reverse-skill/ida-reverse
    - dhicoc/dsh-reverse-skill/ghidra-reverse
    - dhicoc/dsh-reverse-skill/radare2
    - dhicoc/dsh-reverse-skill/js-reverse
    - io.github.noor202401938-netizen/cyber-chef-mcp
    - verification-run-hygiene
---
# 加密解密与脱壳工作流（密枢）

你现在要处理一个加壳、混淆或加密过的目标。你已安装以下技能，请按步骤串联使用：

- **binary-reverse-engineering**：识别格式、脱壳、静态拆解与算法还原
- **IDA / Ghidra / radare2**：在不同工具链上定位关键函数、结构与数据
- **js-reverse**：处理 JavaScript 混淆、签名与前端加密逻辑
- **CyberChef MCP**：对 Base64、Hex、XOR、ROT13、JWT、熵和常见编码做确定性验证
- **verification-run-hygiene**：把每条结论落到可复现证据，区分真信号与噪声

## 工作原则

先确认边界，再拆壳，再还原算法。任何“看起来能解”的结论都要用 CyberChef 或等价脚本复算一遍。原始样本只读，派生文件单独落盘。

## 步骤 1：分诊与登记

使用 **binary-reverse-engineering** 完成：

- 哈希登记，复制到独立工作目录，保留原始样本
- 判断壳、混淆、编译器/运行时特征，列出保护面
- 明确要回答的问题：配置提取 / 算法还原 / 协议格式 / 授权逻辑

输出：样本指纹、保护面清单、目标问题清单。

## 步骤 2：脱壳与去混淆

使用 **binary-reverse-engineering** + 对应的 **IDA / Ghidra / radare2** 技能完成：

- 选择静态或动态脱壳路线，记录工具版本和步骤
- 对 JavaScript 使用 **js-reverse** 做混淆识别与还原
- 无法脱壳时记录卡点，转入黑盒行为路线

输出：可分析镜像或替代路线说明、脱壳过程记录。

## 步骤 3：算法与密钥定位

使用 **binary-reverse-engineering** 和反编译器技能完成：

- 定位加密、解密、校验、签名相关函数和常量
- 还原算法输入输出、密钥来源和状态机
- 对可疑编码使用 **CyberChef MCP** 做快速验证，避免手工算错

输出：算法描述、关键函数清单、密钥/常量位置。

## 步骤 4：确定性验证

使用 **CyberChef MCP** + **verification-run-hygiene** 完成：

- 用已知输入跑通 Base64 / Hex / XOR / JWT / 哈希等操作
- 把每步结果记录为命令、输入、预期输出、实际输出
- 对不确定项标注置信度与反例

输出：验证记录、可复现命令、未闭环项。

## 最终输出

整合为一份加密解密与脱壳交付包：

1. **样本指纹与保护面**
2. **脱壳过程与工具链记录**
3. **算法/密钥还原结论**
4. **CyberChef 与脚本验证记录**、未闭环假设
