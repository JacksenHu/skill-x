---
name: pack-webcrawler
description: >-
  Web crawling and data extraction expert pack (meta-skill). Orchestrates
  scraping playbooks, anti-bot handling, Firecrawl/Playwright/Browser Use MCP
  servers and verification-run-hygiene into one workflow: target scoping, legal
  checks, extraction, anti-bot fallback, cleaning, persistence and evidence.
license: MIT
compatibility: Meta-skill orchestration. Requires Python 3 and Node.js 18+; Firecrawl needs an API key for cloud use.
metadata:
  author: skillhub
  version: "1.0.0"
  package_type: meta-skill
  display_name: 蛛网
  aliases:
    - 蛛网
    - 蛛网专家团
    - 爬虫专家团
    - Webcrawler
    - pack-webcrawler
  name-zh: 蛛网 · 网页爬虫与数据抽取专家团
  description-zh: 从授权边界出发做网页抓取、渲染、反爬回退、清洗与入库,全程保留证据并控制频率。
  category: data
orchestration:
  children:
    - thirdwatch-dev/scraping-skills/web-scraping-playbook
    - thirdwatch-dev/scraping-skills/anti-bot-scraping
    - Nimbleway/agent-skills/nimble-web-expert
    - Nimbleway/agent-skills/competitor-intel
    - Johell1NS/browser-search/browser-search
    - io.github.firecrawl/firecrawl-mcp-server
    - io.github.microsoft/playwright-mcp
    - com.browser-use/browser-use
    - verification-run-hygiene
---
# 网页爬虫与数据抽取工作流（蛛网）

你现在要完成一个网页爬取或数据抽取任务。你已安装以下技能和服务，请按步骤串联使用：

- **web-scraping-playbook**：通用抓取与站点分析流程
- **anti-bot-scraping**：识别反爬、降速与回退策略
- **nimble-web-expert / competitor-intel**：实时搜索、抓取与结构化情报
- **browser-search**：自托管搜索与浏览器访问
- **Firecrawl / Playwright / Browser Use MCP**：静态抓取、渲染型抓取和浏览器自动化
- **verification-run-hygiene**：保证结果可复现、可归档

## 工作原则

只采集授权范围内、允许访问的数据。先看 `robots.txt`、服务条款和频率限制，再动手；渲染失败时用降级路线，不靠无脑重试压目标。原始响应与清洗结果分开保存。

## 步骤 1：范围与合规

使用 **web-scraping-playbook** 完成：

- 固化目标 URL、字段、数量和用途
- 检查 `robots.txt`、服务条款、登录/权限要求
- 记录访问频率上限和必须规避的路径

输出：范围清单、合规结论、访问策略。

## 步骤 2：站点侦察

使用 **web-scraping-playbook** + **nimble-web-expert** 完成：

- 识别数据来源是静态 HTML、API 还是渲染型页面
- 检查分页、搜索、过滤和反爬迹象
- 用 **browser-search** 或 Firecrawl 搜索确认结构

输出：数据来源类型、目标端点/选择器、反爬风险。

## 步骤 3：实现抽取

使用 **Firecrawl MCP** 处理静态/API 型页面，**Playwright MCP** 或 **Browser Use MCP** 处理渲染型页面：

- 先做最小样本抽取，验证字段完整
- 遇到验证码/封禁时切换到 **anti-bot-scraping** 的回退策略
- 保持低并发、随机化与退避，不压测目标

输出：可运行抽取脚本、样本数据、反爬回退记录。

## 步骤 4：清洗与入库

使用 **web-scraping-playbook** + **verification-run-hygiene** 完成：

- 去重、归一化、字段校验和异常行处理
- 记录来源 URL、抓取时间、页码和原始响应摘要
- 落盘前校验数量、字段完整性和抽样正确性

输出：清洗后数据集、质量报告、可复现命令。

## 最终输出

整合为一份爬虫交付包：

1. **授权范围与合规记录**
2. **站点侦察与数据来源结论**
3. **抽取实现与反爬回退**
4. **清洗结果与质量验证**、未闭环项
