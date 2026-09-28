---
name: pack-abyss-deep-reverse
description: >-
  Deep reverse-engineering expert pack (meta-skill). Orchestrates the
  binary-reverse-engineering and verification-run-hygiene skills into one
  workflow: scope and triage, unpacking, static structure recovery, protocol
  and algorithm reconstruction, then evidence-verified reporting. Use when a
  task needs end-to-end reverse engineering of an unknown binary, firmware
  image, or protected artifact, or when the user asks for the Abyss / 深潜
  expert pack.
license: MIT
compatibility: Meta-skill orchestration. Member skills require Python 3 (stdlib only); analysis tooling (IDA/Ghidra/radare2/Frida) is used when available on the host.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: 深潜
  aliases:
    - 深潜
    - 深潜专家团
    - 深度逆向专家团
    - Abyss
    - pack-abyss-deep-reverse
  name-zh: 深潜 · 深度逆向专家团
  description-zh: 把不透明的二进制摸清边界、拆开结构、验证每一步结论的端到端逆向工作流:识别与脱壳、静态拆解、协议重建、验证收尾。
  category: reverse-engineering
orchestration:
  children:
    - binary-reverse-engineering
    - verification-run-hygiene
---
# 深度逆向工作流（深潜）

你现在要完成一项深度逆向任务。你已安装以下技能，请按步骤串联使用：

- **binary-reverse-engineering**：二进制的识别、脱壳、静态拆解、算法与协议重建
- **verification-run-hygiene**：让每一步结论可复现、可归档，区分真信号与噪声

## 工作原则

先摸边界，再拆结构，最后验证。任何"看起来像"的结论都要落成证据：
偏移、哈希、命令与输出必须能原地复现。跑不通的结论打回重做。

## 步骤 1：边界与识别（获取层）

使用 **Binary Reverse Engineering** 完成：

- 对样本做哈希登记，复制到独立工作目录，**保留原始文件不动**
- 用 `scripts/triage_binary.py` 完成首轮分诊：格式、架构、编译器/运行时线索、保护特征、导入表、字符串
- 明确目标边界：要回答什么问题（后门逻辑 / 授权算法 / 协议格式 / 崩溃根因）

输出：样本指纹 + 首轮分诊结论 + 本次逆向的目标问题清单。

## 步骤 2：脱壳与反混淆（获取层）

使用 **Binary Reverse Engineering** 的脱壳路线：

- 识别壳/虚拟机/控制流平坦化特征，选择静态或动态脱壳路线
- 产出可分析的镜像，记录脱壳过程与工具链版本
- 若无法脱壳，记录卡点与已排除的路线，转入黑盒行为分析

输出：可分析镜像（或替代路线说明）+ 脱壳过程记录。

## 步骤 3：静态拆解与结构重建（分析层）

使用 **Binary Reverse Engineering** 完成：

- 按入口路径建立地址/函数/结构映射，边分析边落图
- 恢复关键数据结构、调度逻辑与边界检查
- 对可疑算法（加密、校验、授权）做定点还原

输出：结构地图 + 关键函数清单 + 初步结论注释。

## 步骤 4：协议与算法重建（分析层）

使用 **Binary Reverse Engineering** 完成：

- 对网络/进程间通信样本做协议重建：消息边界、字段、状态机
- 对算法做等价实现验证：用已知输入对比原始输出
- 记录所有推断的置信度与反例

输出：协议格式文档 + 等价实现 + 对比验证记录。

## 步骤 5：验证收尾（输出层）

使用 **Verification Run Hygiene** 完成：

- 把每个关键结论写成可复现验证：命令、输入、预期输出、实际输出
- 区分真信号与假红/噪声，标注未闭环的假设
- 归档最终产物：报告、恢复的产物、验证脚本

输出：验证报告 + 可复现命令清单 + 未闭环假设列表。

## 最终输出

将以上步骤整合为一份深度逆向交付包：

1. **样本指纹与分诊结论**：哈希、格式、保护特征、目标问题清单
2. **逆向过程记录**：脱壳路线、结构地图、关键函数与数据结构
3. **重建产物**：协议文档、等价算法实现、补丁或分析脚本
4. **验证报告**：每条结论的复现命令与实测输出，未闭环项单独列出
