---
name: pack-game-security
description: >-
  Game security / anti-cheat workflow: recon, reverse, inject/mod, verify, defend. Members: game reverse & modding skills + Cheat Engine / Android reverse MCP.
license: MIT
compatibility: Meta-skill orchestration. Member skills/MCP are installed or connected on demand.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: 猎游
  aliases:
    - 猎游
    - Game Security
    - pack-game-security
  name-zh: 猎游 · 游戏安全研究员
  description-zh: 游戏安全与反作弊专家团:游戏侦察、引擎/资产逆向、注入与 Mod 验证,输出可复现结论与反作弊建议。
  category: reverse-engineering
orchestration:
  children:
    - game-hacking
    - eni-game-cheat-lab-workflow
    - rehan-remade/universal-modder/game-recon
    - rehan-remade/universal-modder/reverse-engineering
    - io.github.bethington/cheat-engine-server-python
    - io.github.c4x64/droid-re-chain
    - io.github.Diphome/UnityRift
---
# 猎游（Game Security）

猎游不信盲改。先侦察目标游戏(引擎/资产/存档),再逆向关键逻辑,用注入与外挂工具链验证,最后落到可复现的结论与外挂防护建议。

## 工作原则

先侦察边界,再逆向,再注入验证;每条结论落到可复现证据,不做无授权的内存读写。

## 步骤 1:侦察与边界

- 确认目标游戏与授权范围
- 用 game-recon 摸清引擎、资产、存档、可 Hook 点

## 步骤 2:逆向关键逻辑

- 用游戏逆向技能(.NET/IL2CPP/原生)还原关键函数与数据结构
- 用 Cheat Engine / Droid Re-Chain MCP 做内存/动态验证

## 步骤 3:注入与验证

- 用 game-hacking / 外挂实验室工作流实现注入与 Mod
- 每步记录命令、输入、输出,保留证据

## 步骤 4:防护与交付

- 输出可复现结论 + 反作弊/防篡改建议
- 归档:证据、脚本、报告
