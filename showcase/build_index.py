#!/usr/bin/env python3
"""Skill X 橱窗站构建器 v3:双语 / 分类 / 套件中心 / 外置 assets / 增量构建。

数据源:
- 自研:skills/<name>/SKILL.md(frontmatter + metadata.name-zh/description-zh/category)
- 收录:external.json + showcase/i18n-ext.json(中文增补)

产物:dist/(index.html, suites/index.html, suites/<ns>.html, skills/*.html,
api.html, about.html, assets/{style.css,app.js}, site-data.json, mindmaps/ 预留)

红线:自研 SKILL.md 正文绝不进任何产物;构建期对全部 HTML 做泄露断言。
增量:.build-manifest.json 记录每页输入哈希,未变页面跳过重写。
"""
import hashlib
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svg_map import parse_map, render_svg  # noqa: E402
import apidocs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
EXTERNAL = ROOT / "external.json"
I18N_EXT = Path(__file__).resolve().parent / "i18n-ext.json"
CURATION = Path(__file__).resolve().parent / "curation.json"
STAR_CACHE = Path(__file__).resolve().parent / ".upstream-cache.json"
DIST = Path(__file__).resolve().parent / "dist"
MANIFEST = Path(__file__).resolve().parent / ".build-manifest.json"
TEMPLATE_VERSION = "3.0"

CATEGORIES = {
    "reverse-engineering": "逆向工程",
    "pentest": "渗透测试",
    "malware": "样本分析",
    "forensics": "内存取证",
    "engineering-hygiene": "工程纪律",
    "dev-workflow": "开发流程",
    "data": "数据",
    "web-frontend": "Web 前端",
    "ai-media": "AI 媒体",
}
CSS = """
/* finesse · register=brand · A=graphite+amber · B=heavy-mono/regular-sans · C=asymmetric-proof-grid · D=hyperframes-loop+scrim · E=forensic-grid · SOUL=8 SPECTACLE=6 DENSITY=4 */
:root{
  --bg:#0A0D11; --surface:#141A21; --surface2:#1A222C; --line:#232C38; --line2:#33404F;
  --text:#E6EAF0; --text2:#98A5B5; --text3:#6A7686;
  --accent:#FF6B2C; --accent2:#FF9351; --signal:#4A9EFF;
  --ok:#3DD68C; --warn:#FFB020; --danger:#FF4D4F;
  --c-reverse-engineering:#FF6B2C; --c-pentest:#FF4D4F; --c-malware:#A855F7; --c-forensics:#17E1C5;
  --c-engineering-hygiene:#4A9EFF; --c-dev-workflow:#8B98A9; --c-web-frontend:#3DD68C; --c-data:#FFB020;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --mono:ui-monospace,SFMono-Regular,"JetBrains Mono","Cascadia Code",Consolas,monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;overflow-x:clip}
body{font-family:var(--sans);background:var(--bg);color:var(--text);line-height:1.65;font-size:15px;-webkit-font-smoothing:antialiased;overflow-x:clip}
a{color:var(--signal);text-decoration:none}
a:hover{text-decoration:underline}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
::selection{background:var(--accent);color:#fff}

.wrap{max-width:1040px;margin:0 auto;padding:0 20px 70px}
h1{font-size:28px;line-height:1.2;letter-spacing:-.02em;font-weight:700}
h2{font-size:16px;font-weight:700;margin:38px 0 14px;padding-bottom:9px;border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:10px}
h2 .n{font-family:var(--mono);font-size:11px;color:var(--text3);font-weight:400}
.h2-sm{font-size:14px;margin-top:22px;border:0;padding:0}
p{max-width:76ch}

/* 顶栏 */
.topnav{position:sticky;top:0;z-index:40;background:rgba(10,13,17,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:2px;padding:0 20px;height:52px}
.topnav .brand{font-family:var(--mono);font-weight:700;font-size:14px;margin-right:18px;color:var(--text);letter-spacing:.01em;display:flex;align-items:center;gap:7px}
.topnav .brand i{width:7px;height:7px;background:var(--accent);display:inline-block;border-radius:1px;box-shadow:0 0 8px var(--accent)}
.topnav a.nav{color:var(--text2);padding:16px 11px;font-size:13.5px;border-bottom:2px solid transparent}
.topnav a.nav:hover{color:var(--text);text-decoration:none}
.topnav a.nav.active{color:var(--text);border-bottom-color:var(--accent)}
.lang-btn{margin-left:auto;font-family:var(--mono);font-size:11.5px;background:none;border:1px solid var(--line2);border-radius:2px;padding:4px 9px;color:var(--text2);cursor:pointer}
.lang-btn:hover{border-color:var(--accent);color:var(--accent)}

/* Hero:网格底 + 扫描光带 + 顶部推荐入口 */
.hero{position:relative;border-bottom:1px solid var(--line);padding:44px 0 34px;margin-bottom:6px;overflow:hidden}
.hero:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.028) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.028) 1px,transparent 1px);background-size:44px 44px;mask-image:linear-gradient(180deg,#000,transparent 92%);pointer-events:none}
.hero:after{content:"";position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,transparent,var(--accent),transparent);opacity:.85;animation:scanline 7s linear infinite}
@keyframes scanline{0%{transform:translateY(0);opacity:0}8%{opacity:.9}92%{opacity:.9}100%{transform:translateY(320px);opacity:0}}
.hero>*{position:relative}
.hero .eyebrow{font-family:var(--mono);font-size:11.5px;color:var(--accent);letter-spacing:.06em}
.hero h1{font-size:44px;margin-top:12px;max-width:22ch}
.hero h1 em{font-style:normal;color:var(--accent)}
.hero .lede{font-size:15.5px;color:var(--text2);margin-top:14px;max-width:60ch}
.hero .stats{display:flex;gap:34px;margin-top:26px}
.hero .stats b{font-family:var(--mono);font-size:30px;font-weight:600;display:block;line-height:1;color:var(--text)}
.hero .stats b.accent{color:var(--accent)}
.hero .stats span{font-size:12px;color:var(--text3)}

/* 推荐搜索框(首页顶部主角) */
.finder{margin-top:26px;max-width:640px;position:relative}
.finder textarea{width:100%;padding:15px 17px;background:var(--surface);border:1px solid var(--line2);border-radius:3px;font:14.5px/1.6 var(--sans);color:var(--text);resize:vertical;min-height:82px;transition:border-color .2s,box-shadow .2s}
.finder textarea::placeholder{color:var(--text3)}
.finder textarea:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,107,44,.16)}
.finder .act{margin-top:10px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.btn{font:inherit;font-size:14px;padding:9px 20px;border:1px solid var(--accent);background:var(--accent);color:#160A04;border-radius:3px;cursor:pointer;font-weight:600;transition:filter .15s,transform .12s}
.btn:hover{filter:brightness(1.12)}
.btn:active{transform:translateY(1px)}
.btn.ghost{background:transparent;color:var(--text2);border-color:var(--line2);font-weight:400}
.btn.ghost:hover{border-color:var(--accent);color:var(--accent)}
.finder .hint{font-size:12px;color:var(--text3)}

/* 推荐结果 */
.recs{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-top:16px}
.rec{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--cat,var(--accent));border-radius:3px;padding:14px 16px;animation:pop .34s cubic-bezier(.2,.7,.3,1) backwards}
@keyframes pop{from{opacity:0;transform:translateY(10px) scale(.985)}to{opacity:1;transform:none}}
.rec .t{font-size:15px;font-weight:600}
.rec .t a{color:var(--text)}
.rec .id{font-family:var(--mono);font-size:11.5px;color:var(--text3);margin-top:3px;word-break:break-all}
.rec .d{font-size:13px;color:var(--text2);margin-top:8px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.rec .why{font-family:var(--mono);font-size:11px;color:var(--accent);margin-top:9px}

/* 搜索 + 分类筛选 */
.search{margin:0 0 4px;max-width:560px}
.search input{width:100%;padding:11px 14px;background:var(--surface);border:1px solid var(--line2);border-radius:3px;font:14px var(--sans);color:var(--text)}
.search input::placeholder{color:var(--text3)}
.search input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,107,44,.16)}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin:16px 0 4px}
.chip{font-size:12.5px;padding:6px 13px;border:1px solid var(--line2);border-radius:2px;background:var(--surface);cursor:pointer;color:var(--text2);transition:all .16s}
.chip:hover{border-color:var(--accent);color:var(--accent)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#160A04;font-weight:600}

/* 技能卡片网格(自研) */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:12px;margin-top:4px}
.grid.grid-mt{margin-top:16px}
.card{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:3px;padding:16px 17px 15px;overflow:hidden;transition:border-color .18s,background .18s,transform .18s;animation:pop .4s cubic-bezier(.2,.7,.3,1) backwards}
.card:before{content:"";position:absolute;left:0;top:0;bottom:0;width:2px;background:var(--cat,var(--accent));transition:width .18s}
.card:hover{border-color:var(--line2);background:var(--surface2);transform:translateY(-2px)}
.card:hover:before{width:4px}
.card h3{font-size:16px}
.card h3 a{color:var(--text)}
.card .en-name{font-family:var(--mono);font-size:11.5px;color:var(--text3);margin-top:3px;word-break:break-all}
.card p{font-size:13px;color:var(--text2);margin-top:9px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card .meta{display:flex;align-items:center;gap:8px;margin-top:12px;flex-wrap:wrap}


/* 标签:分类色编码 */
.cat-reverse-engineering{--cat:var(--c-reverse-engineering)}
.cat-pentest{--cat:var(--c-pentest)}
.cat-malware{--cat:var(--c-malware)}
.cat-forensics{--cat:var(--c-forensics)}
.cat-engineering-hygiene{--cat:var(--c-engineering-hygiene)}
.cat-dev-workflow{--cat:var(--c-dev-workflow)}
.cat-web-frontend{--cat:var(--c-web-frontend)}
.cat-data{--cat:var(--c-data)}
.tag{font-family:var(--mono);font-size:10.5px;padding:2px 7px;border:1px solid var(--line2);border-radius:2px;color:var(--text2);white-space:nowrap}
.tag.cat{border-color:var(--cat,var(--line2));color:var(--cat,var(--text2))}
.tag.kind-own{border-color:var(--accent);color:var(--accent)}
.tag.kind-ext{border-color:var(--line2);color:var(--text2)}
.tag.risk-low{border-color:#3FB96B;color:#3FB96B}
.tag.risk-medium{border-color:var(--warn);color:var(--warn)}
.tag.risk-high,.tag.risk-critical{border-color:var(--danger);color:var(--danger)}
.count{font-family:var(--mono);font-size:12px;color:var(--text3);white-space:nowrap}
.count.hit{color:var(--accent)}

/* 详情页 */
.detail{background:var(--surface);border:1px solid var(--line);border-radius:3px;padding:26px 28px;margin-top:16px}
.detail h1{font-size:26px}
.detail .en-name{font-family:var(--mono);font-size:13px;color:var(--text3);margin-top:6px}
.detail .desc{margin:16px 0;color:var(--text);font-size:15px;white-space:pre-wrap}
.kv{display:grid;grid-template-columns:140px 1fr;gap:10px 16px;font-size:13.5px;margin:20px 0;padding:16px;background:var(--bg);border:1px solid var(--line);border-radius:3px}
.kv dt{color:var(--text3)}
.kv dd{font-family:var(--mono);word-break:break-all;color:var(--text)}
.kv a{color:var(--signal)}

/* 命令块 */
.cmd{position:relative;background:#05070A;border:1px solid var(--line);border-left:3px solid var(--accent);padding:13px 15px;border-radius:3px;font:13px/1.5 var(--mono);color:#E6EAF0;overflow-x:auto;margin:12px 0;white-space:pre;user-select:all}
.cmd:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,107,44,.05),transparent 60%);pointer-events:none}

/* 审计折叠 */
details.audit{background:var(--surface);border:1px solid var(--line);border-radius:3px;margin-top:18px}
details.audit>summary{cursor:pointer;padding:14px 16px;display:flex;align-items:center;gap:10px;font-size:14px;list-style:none;border-left:3px solid transparent;transition:border-color .18s,background .18s}
details.audit>summary::-webkit-details-marker{display:none}
details.audit>summary:hover{background:var(--surface2)}
details.audit[open]>summary{border-left-color:var(--accent);border-bottom:1px solid var(--line)}
.grade{font-family:var(--mono);font-weight:700;font-size:13px;padding:2px 9px;border-radius:2px}
.grade-A{background:rgba(61,214,140,.14);color:var(--ok)}
.grade-A-{background:rgba(157,214,60,.14);color:#A5D63C}
.grade-B{background:rgba(255,176,32,.14);color:var(--warn)}
.grade-C{background:rgba(255,107,44,.14);color:var(--accent)}
.grade-D{background:rgba(255,77,79,.14);color:var(--danger)}
.audit-meta{font-size:11.5px;color:var(--text3);margin-left:auto;font-family:var(--mono)}
.audit-body{padding:4px 16px 16px}
.lvl{font-family:var(--mono);font-size:10.5px;padding:1px 7px;border-radius:2px;white-space:nowrap}
.lvl-info{background:rgba(152,165,181,.12);color:var(--text2)}
.lvl-low{background:rgba(157,214,60,.14);color:#A5D63C}
.lvl-medium{background:rgba(255,176,32,.14);color:var(--warn)}
.lvl-high{background:rgba(255,107,44,.14);color:var(--accent)}
.lvl-critical{background:rgba(255,77,79,.14);color:var(--danger)}
.audit-detail{font-size:12.5px;color:var(--text2);word-break:break-word;max-width:420px}

table.api{width:100%;border-collapse:collapse;font-size:13px;margin:14px 0;background:var(--surface)}
table.api th,table.api td{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}
table.api th{background:var(--bg);font-weight:600;color:var(--text2)}
code.inl{font-family:var(--mono);font-size:12px;background:var(--surface2);padding:1px 5px;border-radius:2px;color:var(--text)}

/* 思维导图:内联 SVG,连线描画 + 节点悬停 */
.mmap{background:var(--surface);border:1px solid var(--line);border-radius:3px;margin-top:16px;padding:14px;overflow-x:auto}
.mmap svg{max-width:100%;height:auto;display:block;margin:0 auto}
.mmap svg .bg{fill:transparent}
.mmap svg rect{fill:var(--surface2);stroke:var(--line2);transition:fill .18s,stroke .18s}
.mmap svg rect.root{fill:rgba(255,107,44,.12);stroke:var(--accent)}
.mmap svg text{fill:var(--text);font-size:13px}
.mmap svg path{stroke-dasharray:400;stroke-dashoffset:400;animation:draw 1.1s ease-out forwards}
@keyframes draw{to{stroke-dashoffset:0}}
.mmap svg g.node:hover rect{fill:var(--accent);stroke:var(--accent)}
.mmap svg g.node:hover text{fill:#160A04}

.suite{margin-bottom:30px}
.suite h3{font-family:var(--mono);font-size:15px;font-weight:600;margin-bottom:10px;color:var(--text)}
.suite-meta{font-family:var(--sans);font-size:12.5px;color:var(--text3);font-weight:400}
.suite-meta a{color:var(--signal)}
.notice{background:rgba(255,107,44,.08);border:1px solid rgba(255,107,44,.35);border-radius:3px;padding:13px 16px;font-size:13px;color:var(--accent2);margin-top:14px}
.hint-warn{font-size:13px;color:var(--accent2);margin-top:14px}
.hint-ok{font-size:13px;color:var(--ok);margin-top:14px}
.hint-dim{font-size:13px;color:var(--text3);margin-top:10px;max-width:76ch}
.empty{color:var(--text3);font-size:14px;padding:26px 4px}
.hidden{display:none!important}
footer{text-align:left;font-size:12.5px;color:var(--text3);padding:22px 20px 40px;border-top:1px solid var(--line);margin-top:44px}
footer a{color:var(--signal)}

/* 首页(品牌面) */
.home-hero{position:relative;margin-left:calc(50% - 50vw);margin-right:calc(50% - 50vw);border-bottom:1px solid var(--line);overflow:hidden;background:#0A0D11;min-height:min(78vh,660px);display:flex;align-items:center}
.home-hero-bg{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);background-size:48px 48px;-webkit-mask-image:radial-gradient(circle at 74% 45%,#000 18%,transparent 78%);mask-image:radial-gradient(circle at 74% 45%,#000 18%,transparent 78%)}
.home-hero-video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center;opacity:.9}
.home-hero-scrim{position:absolute;inset:0;background:radial-gradient(circle at 76% 40%,rgba(255,107,44,.18),transparent 55%),linear-gradient(90deg,rgba(10,13,17,.97) 0%,rgba(10,13,17,.9) 42%,rgba(10,13,17,.5) 100%)}
.home-hero-inner{position:relative;width:100%;max-width:1040px;margin:0 auto;padding:84px 20px 64px}
.home-hero .eyebrow{font-family:var(--mono);font-size:11.5px;color:var(--accent);letter-spacing:.08em}
.home-hero h1{font-size:clamp(46px,7vw,78px);line-height:1;margin-top:16px;letter-spacing:-.01em}
.home-offer{font-size:clamp(19px,2.6vw,27px);font-weight:600;margin-top:16px;max-width:20ch}
.home-lede{font-size:15px;color:var(--text2);margin-top:14px;max-width:56ch}
.home-cta{display:flex;gap:10px;flex-wrap:wrap;margin-top:26px}
.home-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;margin-top:36px;background:var(--line);border:1px solid var(--line);max-width:660px}
.home-stats div{background:rgba(10,13,17,.72);padding:12px 14px}
.home-stats dt{font-size:12px;color:var(--text3)}
.home-stats dd{font-family:var(--mono);font-size:22px;margin-top:4px;line-height:1.2}
.bench,.home-featured,.home-mcp{margin-top:44px}
.bench{display:grid;grid-template-columns:minmax(0,268px) minmax(0,1fr);gap:30px;align-items:start}
.bench-rail{display:flex;flex-direction:column}
.step{appearance:none;background:none;border:0;border-left:1px solid var(--line);color:var(--text2);cursor:pointer;font:inherit;text-align:left;display:flex;flex-direction:column;justify-content:center;gap:7px;min-height:52vh;padding:22px 0 22px 18px;position:relative;transition:color .2s}
.step:before{content:"";position:absolute;left:-1px;top:50%;width:1px;height:0;background:var(--accent);transition:height .28s cubic-bezier(.22,.7,.3,1)}
.step.on{color:var(--text)}
.step.on:before{height:56px;margin-top:-28px}
.step i{font-family:var(--mono);font-size:11.5px;letter-spacing:.08em;color:var(--text3)}
.step.on i{color:var(--accent)}
.step b{font-size:19px;font-weight:650;line-height:1.3}
.step span{font-size:13px;color:var(--text3);max-width:26ch}
.step:hover b{color:var(--accent)}
.bench-stage{position:sticky;top:76px}
.console{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:4px;overflow:hidden;box-shadow:0 26px 60px rgba(0,0,0,.34)}
.console:before{content:"";position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,transparent,var(--accent),transparent);opacity:.2;animation:beamPulse 5.5s ease-in-out infinite;pointer-events:none}
@keyframes beamPulse{0%,100%{opacity:.14}50%{opacity:.72}}
.console-bar{display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--line);background:var(--bg)}
.dots{display:flex;gap:6px}
.dots i{width:9px;height:9px;border-radius:50%;background:var(--line2)}
.dots i:first-child{background:rgba(255,77,79,.7)}
.dots i:nth-child(2){background:rgba(255,176,32,.7)}
.dots i:nth-child(3){background:rgba(61,214,140,.7)}
.console-path{font-family:var(--mono);font-size:11.5px;color:var(--text3)}
.console-live{margin-left:auto;font-family:var(--mono);font-size:10.5px;color:var(--ok);border:1px solid rgba(61,214,140,.4);border-radius:2px;padding:1px 7px}
.console-body{min-height:430px;padding:20px}
.panel{display:none}
.panel.on{display:block;animation:panelIn .34s cubic-bezier(.22,.7,.3,1) both}
@keyframes panelIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.console-foot{padding:10px 14px;border-top:1px solid var(--line);background:var(--bg);font-family:var(--mono);font-size:11.5px;color:var(--text3)}
.panel .finder{margin-top:0}
.panel .mmap{margin-top:0;border:1px solid var(--line);background:var(--bg);max-height:560px;overflow:auto}
.panel .audit{margin-top:0}
.demo-tabs{display:flex;gap:7px;flex-wrap:wrap}
.tab{font-family:inherit;font-size:12.5px;padding:6px 13px;border:1px solid var(--line2);border-radius:2px;background:transparent;cursor:pointer;color:var(--text2);transition:border-color .16s,background .16s,color .16s}
.tab:hover{border-color:var(--accent);color:var(--accent)}
.tab.on{background:var(--accent);border-color:var(--accent);color:#160A04;font-weight:600}
.demo-snippet{margin:12px 0 0;max-height:280px;overflow:auto}
.demo-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:12px}
.home-mcp-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:14px}
.home-mcp-item{display:block;background:var(--surface);border:1px solid var(--line);border-left:2px solid var(--accent);border-radius:3px;padding:14px 16px;transition:border-color .18s,background .18s}
.home-mcp-item:hover{border-color:var(--line2);background:var(--surface2);text-decoration:none}
.home-mcp-item .t{font-size:15px;font-weight:600;color:var(--text)}
.home-mcp-item .id{font-family:var(--mono);font-size:11.5px;color:var(--text3);margin-top:3px;word-break:break-all}
.home-mcp-item .meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.home-more{margin-top:14px}
.home-trust{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);margin-top:34px}
.trust-item{background:var(--bg);padding:18px}
.trust-item b{display:block;font-size:14px}
.trust-item span{display:block;font-size:13px;color:var(--text2);margin-top:8px}
.home-cta-band{margin-top:34px;border-top:1px solid var(--line);padding-top:26px}

/* 滚动动效:R2 原生 scroll-driven;不支持时由 app.js 降级为 IntersectionObserver + rAF,reduced-motion 时全部停在终态 */
.scroll-progress{position:fixed;left:0;right:0;top:0;height:2px;z-index:60;background:linear-gradient(90deg,var(--accent),var(--signal));transform:scaleX(0);transform-origin:0 50%;pointer-events:none}
.reveal-armed{opacity:0;transform:translate3d(0,26px,0);transition:opacity .55s cubic-bezier(.22,.7,.3,1),transform .55s cubic-bezier(.22,.7,.3,1)}
.reveal-armed.reveal-in{opacity:1;transform:none}
@supports (animation-timeline: view()){
  @keyframes rail{from{transform:scaleX(0)}to{transform:scaleX(1)}}
  @keyframes riseIn{from{opacity:0;transform:translate3d(0,30px,0)}to{opacity:1;transform:none}}
  @keyframes slideIn{from{opacity:0;transform:translate3d(-26px,0,0)}to{opacity:1;transform:none}}
  @keyframes settleIn{from{opacity:0;transform:scale(.982)}to{opacity:1;transform:none}}
  @keyframes heroDrift{from{transform:translate3d(0,0,0) scale(1)}to{transform:translate3d(0,54px,0) scale(1.06)}}
  @keyframes heroVeil{from{opacity:1}to{opacity:.42}}
  .scroll-progress{animation:rail linear both;animation-timeline:scroll(root block)}
  .home-hero-video{animation:heroDrift linear both;animation-timeline:scroll(root block);animation-range:0 70vh}
  .home-hero-inner{animation:heroVeil linear both;animation-timeline:scroll(root block);animation-range:0 62vh}
  .reveal{animation:riseIn linear both;animation-timeline:view();animation-range:entry 12% cover 36%}
  .reveal-left{animation-name:slideIn}
  .reveal-scale{animation-name:settleIn}
  .home-trust .reveal:nth-child(2){animation-range:entry 18% cover 42%}
  .home-trust .reveal:nth-child(3){animation-range:entry 24% cover 48%}
  .home-featured>h2,.home-mcp>h2{position:relative}
  .home-featured>h2:after,.home-mcp>h2:after{content:"";position:absolute;left:0;bottom:-1px;width:130px;height:1px;background:var(--accent);transform:scaleX(0);transform-origin:0 50%;animation:rail linear both;animation-timeline:view();animation-range:entry 8% cover 30%}
}

@media print{.reveal,.reveal-armed{opacity:1!important;transform:none!important;animation:none!important}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.mmap svg path{stroke-dashoffset:0}.home-hero-video{display:none}}

@media (max-width:760px){
  body{font-size:15.5px}
  .topnav{height:auto;padding:7px 12px;overflow-x:auto;scrollbar-width:none}
  .topnav::-webkit-scrollbar{display:none}
  .topnav .brand{margin-right:12px;font-size:13px}
  .topnav a.nav{padding:8px 9px;font-size:13px;white-space:nowrap}
  .wrap{padding:0 14px 48px}
  .home-hero{min-height:auto}
  .home-hero-inner{padding:54px 14px 46px}
  .home-hero-video{width:100%;opacity:.5}
  .home-offer{max-width:none}
  .home-stats{grid-template-columns:repeat(2,minmax(0,1fr));max-width:none}
  .bench{display:block;margin-top:30px}
  .bench-rail{flex-direction:row;gap:8px;overflow-x:auto;position:sticky;top:52px;z-index:6;background:var(--bg);padding:6px 0;scrollbar-width:none}
  .bench-rail::-webkit-scrollbar{display:none}
  .step{flex:0 0 auto;min-height:auto;border:1px solid var(--line);border-left:1px solid var(--line);padding:9px 12px;white-space:nowrap;gap:0}
  .step i,.step span{display:none}
  .step b{font-size:13.5px}
  .step.on{border-color:var(--accent);background:rgba(255,107,44,.08)}
  .step.on:before{display:none}
  .bench-stage{position:static;margin-top:12px}
  .console-body{padding:14px;min-height:0}
  .home-trust{grid-template-columns:1fr}
  .hero{padding:28px 0 24px}
  .hero h1{font-size:31px}
  .hero .lede{font-size:14.5px}
  .hero .stats{gap:22px;margin-top:20px}
  .hero .stats b{font-size:24px}
  .finder textarea{min-height:70px;font-size:14px}
  .grid{grid-template-columns:1fr}
  .recs{grid-template-columns:1fr}
  .detail{padding:18px 16px}
  .kv{grid-template-columns:1fr;gap:4px}
  .cmd{font-size:12px;padding:11px 12px}
  table.api{display:block;overflow-x:auto;white-space:nowrap}
  .audit-detail{max-width:none;white-space:normal}
  .mmap{padding:8px}
  .btn{padding:11px 16px;width:100%;text-align:center}
  .finder .act .btn{width:auto}
  footer{padding:18px 14px 32px}
}
"""



APP_JS = """
(function(){
  function cur(){ return localStorage.getItem('sx-lang') || 'zh'; }
  window.setLang = function(l){
    localStorage.setItem('sx-lang', l);
    document.querySelectorAll('[data-zh]').forEach(e=>{
      const v = (l==='en' && e.dataset.en) ? e.dataset.en : e.dataset.zh;
      if (e.dataset.attr) e.setAttribute(e.dataset.attr, v); else e.textContent = v;
    });
    document.querySelectorAll('.lang-btn').forEach(b=>b.textContent = l==='en' ? '中文' : 'EN');
  };
  const lb = document.querySelector('.lang-btn');
  if (lb) lb.addEventListener('click', ()=> setLang(cur()==='en' ? 'zh' : 'en'));

  window.sxFilter = function(){
    const q = (document.getElementById('q')?.value || '').trim().toLowerCase();
    const cat = document.querySelector('.chip.on')?.dataset.cat || '';
    let visible = 0;
    document.querySelectorAll('[data-search]').forEach(el=>{
      const hitQ = !q || el.dataset.search.includes(q);
      const hitC = !cat || el.dataset.category === cat;
      const hit = hitQ && hitC;
      el.classList.toggle('hidden', !hit);
      if (hit) visible++;
    });
    const empty = document.getElementById('empty');
    if (empty) empty.classList.toggle('hidden', visible > 0);
  };
  document.getElementById('q')?.addEventListener('input', sxFilter);
  document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click', ()=>{
    document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));
    c.classList.add('on'); sxFilter();
  }));

  window.sxCopy = function(btn, text, skill){
    navigator.clipboard.writeText(text).then(()=>{
      const old = btn.textContent; btn.textContent = '✓';
      setTimeout(()=>btn.textContent = old, 1200);
      if (skill) fetch('/api/download', {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({skill: skill, action: 'copy'})}).catch(()=>{});
    });
  };
  document.querySelectorAll('.copy-btn').forEach(b=>b.addEventListener('click', ()=>{
    window.sxCopy(b, b.dataset.copy || '', b.dataset.skill || '');
  }));

  fetch('/api/stats').then(r=>r.ok?r.json():null).then(d=>{
    if (!d || !d.counts) return;
    document.querySelectorAll('[data-stat]').forEach(e=>{
      const v = d.counts[e.dataset.stat];
      e.textContent = (v === undefined) ? '0' : String(v);
    });
  }).catch(()=>{});

  /* ---- 技能推荐(优先后端 API,失败降级本地匹配) ---- */
  const CAT_KW = {
    'reverse-engineering': ['逆向','反编译','脱壳','汇编','ida','ghidra','radare','补丁','patch','还原','破解','二进制','固件','elf','pe','exe','dll','apk','so','安卓','混淆'],
    'pentest': ['渗透','漏洞','越权','idor','注入','sql','xss','ssrf','扫描','红队','靶场','接口','api','鉴权','认证','oauth','jwt','csrf','上传','命令执行'],
    'malware': ['样本','恶意','病毒','木马','后门','勒索','c2','ioc','yara','加壳','免杀','远控'],
    'forensics': ['内存','转储','dump','进程','指针','偏移','aob','特征码','基址','崩溃'],
    'engineering-hygiene': ['测试','回归','验证','质量','审查','纪律','假红','污染'],
    'dev-workflow': ['开发','流程','工程','ci','部署','调试']
  };
  function tokenize(s){
    const low = (s||'').toLowerCase();
    const out = new Set();
    (low.match(/[a-z0-9][a-z0-9_.-]+/g)||[]).forEach(w=>{ if(w.length>=2) out.add(w); });
    const zh = (s||'').replace(/[^\u4e00-\u9fa5]/g,'');
    for (let i=0;i<zh.length-1;i++) out.add(zh.slice(i,i+2));
    return [...out];
  }
  function renderRecs(list){
    const box = document.getElementById('rec-results');
    const empty = document.getElementById('rec-empty');
    if (!box) return;
    if (!list || !list.length){ box.innerHTML=''; empty?.classList.remove('hidden'); return; }
    empty?.classList.add('hidden');
    box.innerHTML = list.map(function(r){
      const kind = r.kind === 'own' ? '<span class="badge auth">自研·需授权</span>' : '<span class="badge ext">社区精选</span>';
      const cmd = r.install || '';
      const why = (r.matched || []).join(' · ');
      return '<div class="card"><div class="card-head"><h3><a href="'+r.page+'">'+((r['name-zh'])||r.name)+'</a></h3>'+kind+'</div>'+
        '<div class="en-name">'+r.name+'</div>'+
        '<p>'+((r['description-zh'])||r.description||'')+'</p>'+
        '<div class="meta"><span class="badge cat">'+(r.category||'')+'</span><span class="dl">匹配: '+why+'</span></div>'+
        '<div class="cmd">'+cmd+'</div>'+
        '<button class="chip on copy-btn" data-copy="'+cmd.replace(/"/g,'&quot;')+'" data-skill="'+r.name+'">复制安装命令</button></div>';
    }).join('');
    box.querySelectorAll('.copy-btn').forEach(function(b){
      b.addEventListener('click', function(){ window.sxCopy(b, b.dataset.copy || '', b.dataset.skill || ''); });
    });
  }
  function localRecommend(raw, data){
    const toks = tokenize(raw);
    const low = raw.toLowerCase();
    const catBoost = {};
    Object.keys(CAT_KW).forEach(function(cat){
      let n = 0; CAT_KW[cat].forEach(function(k){ if (low.indexOf(k) >= 0) n++; });
      if (n) catBoost[cat] = n * 6;
    });
    const scored = [];
    (data.skills || []).forEach(function(sk){
      let score = 0; const why = new Set();
      const nm = (sk.name + ' ' + (sk['name-zh']||'')).toLowerCase();
      const desc = ((sk.description||'') + ' ' + (sk['description-zh']||'')).toLowerCase();
      toks.forEach(function(t){
        if (nm.indexOf(t) >= 0){ score += 10; why.add(t); }
        else if (desc.indexOf(t) >= 0){ score += 3; why.add(t); }
      });
      if (catBoost[sk.category]){ score += catBoost[sk.category]; why.add(sk.category); }
      if (score > 0){ sk.score = score; sk.matched = [...why].slice(0,6); scored.push(sk); }
    });
    scored.sort(function(a,b){ return b.score - a.score; });
    return scored.slice(0,6);
  }
  window.sxRecommend = function(){
    const raw = (document.getElementById('idea')?.value || '').trim();
    const box = document.getElementById('rec-results');
    const empty = document.getElementById('rec-empty');
    if (!box) return;
    if (!raw){ box.innerHTML=''; empty?.classList.remove('hidden'); return; }
    box.innerHTML = '<div class="empty">…</div>';
    fetch('/api/recommend', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query: raw})})
      .then(function(r){ return r.ok ? r.json() : Promise.reject(); })
      .then(function(d){ renderRecs(d.results || []); })
      .catch(function(){
        fetch('/site-data.json').then(function(r){ return r.json(); })
          .then(function(data){ renderRecs(localRecommend(raw, data)); })
          .catch(function(){ box.innerHTML=''; empty?.classList.remove('hidden'); });
      });
  };
  document.getElementById('find-btn')?.addEventListener('click', function(){ window.sxRecommend(); });
  document.getElementById('idea')?.addEventListener('keydown', function(e){ if(e.key==='Enter' && (e.ctrlKey||e.metaKey)) window.sxRecommend(); });
  /* 数字递增(进入视口时触发一次,尊重 reduced-motion) */
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function countUp(el){
    const target = parseInt(el.dataset.count || '0', 10) || 0;
    if (reduceMotion){ el.textContent = String(target); return; }
    const dur = 900, t0 = performance.now();
    function step(now){
      const p = Math.min(1, (now - t0) / dur);
      el.textContent = String(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  const counters = document.querySelectorAll('.counter');
  if (counters.length && 'IntersectionObserver' in window){
    const io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if (e.isIntersecting){ countUp(e.target); io.unobserve(e.target); } });
    }, {threshold:.4});
    counters.forEach(function(c){ io.observe(c); });
  } else { counters.forEach(countUp); }

  /* 首页 hero 视频:reduced-motion 时停播,交给静态封面 */
  const heroVideo = document.querySelector('.home-hero-video');
  if (heroVideo && reduceMotion){ heroVideo.pause(); heroVideo.removeAttribute('autoplay'); }

  /* 滚动动效降级:不支持 animation-timeline 时用 rAF 进度条 + IntersectionObserver 入场 */
  const rail = document.querySelector('.scroll-progress');
  const supportsScrollAnim = !!(window.CSS && CSS.supports && CSS.supports('animation-timeline: view()'));
  if (rail && !supportsScrollAnim){
    let ticking = false;
    const syncRail = function(){
      const h = document.documentElement;
      const max = (h.scrollHeight - h.clientHeight) || 1;
      rail.style.transform = 'scaleX(' + Math.min(1, Math.max(0, h.scrollTop / max)) + ')';
    };
    window.addEventListener('scroll', function(){
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function(){ syncRail(); ticking = false; });
    }, { passive: true });
    syncRail();
  }
  if (!supportsScrollAnim && !reduceMotion && 'IntersectionObserver' in window){
    const reveals = document.querySelectorAll('.reveal');
    const io2 = new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if (e.isIntersecting){ e.target.classList.add('reveal-in'); io2.unobserve(e.target); } });
    }, { threshold: .15 });
    reveals.forEach(function(el){ el.classList.add('reveal-armed'); io2.observe(el); });
  }

  /* 首页 MCP 演示:读取真实接入描述,按客户端切换配置片段 */
  /* 工作台:左侧步骤与右侧控制台同步切换(桌面滚动联动,移动端点击切换) */
  const bench = document.getElementById('workbench');
  if (bench){
    const steps = Array.prototype.slice.call(bench.querySelectorAll('.step'));
    const panels = Array.prototype.slice.call(bench.querySelectorAll('.panel'));
    const benchMeta = document.getElementById('bench-meta');
    const metas = ['POST /api/recommend · 自然语言 → 技能排序', 'mindmaps/*.svg · 悬停高亮 · 描边绘制', 'scripts/audit_skill.py · AST 级 8 项', 'GET /v0/servers/<name>/install · clientSnippets'];
    let benchActive = 0;
    const benchSet = function(i){
      if (i === benchActive) return;
      benchActive = i;
      steps.forEach(function(s, k){ s.classList.toggle('on', k === i); s.setAttribute('aria-selected', k === i ? 'true' : 'false'); });
      panels.forEach(function(p, k){ p.classList.toggle('on', k === i); });
      if (benchMeta) benchMeta.textContent = metas[i] || '';
    };
    steps.forEach(function(s, i){ s.addEventListener('click', function(){ benchSet(i); }); });
    if (window.matchMedia('(min-width: 761px)').matches){
      let benchTick = false;
      const syncStep = function(){
        const cy = window.innerHeight * 0.5;
        let best = 0;
        steps.forEach(function(s, i){
          if (s.getBoundingClientRect().top <= cy) best = i;
        });
        benchSet(best);
      };
      window.addEventListener('scroll', function(){
        if (benchTick) return;
        benchTick = true;
        requestAnimationFrame(function(){ syncStep(); benchTick = false; });
      }, { passive: true });
      syncStep();
    }
  }
  const mcpDemo = document.getElementById('mcp-demo');
  if (mcpDemo && mcpDemo.dataset.mcp){
    const snippet = document.getElementById('mcp-snippet');
    const status = document.getElementById('mcp-status');
    const copyBtn = document.getElementById('mcp-copy');
    let snippets = null, client = 'claude';
    const paint = function(){
      if (!snippets || !snippet || !snippets[client]) return;
      snippet.textContent = JSON.stringify(snippets[client], null, 2);
      if (copyBtn) copyBtn.dataset.copy = snippet.textContent;
    };
    mcpDemo.querySelectorAll('[data-client]').forEach(function(b){
      b.addEventListener('click', function(){
        client = b.dataset.client || 'claude';
        mcpDemo.querySelectorAll('[data-client]').forEach(function(x){ x.classList.remove('on'); });
        b.classList.add('on'); paint();
      });
    });
    fetch('/v0/servers/' + mcpDemo.dataset.mcp + '/install')
      .then(function(r){ return r.ok ? r.json() : Promise.reject(); })
      .then(function(d){
        snippets = d.clientSnippets || {};
        if (status) status.textContent = '来自 /v0/servers/' + mcpDemo.dataset.mcp + '/install';
        paint();
      })
      .catch(function(){ if (status) status.textContent = '接口暂不可用,已保留注册表中的接入命令。'; });
  }

  /* 输入即推荐(防抖 400ms,少于 4 字不触发) */
  let recTimer = null;
  const ideaEl = document.getElementById('idea');
  if (ideaEl){
    ideaEl.addEventListener('input', function(){
      if (recTimer) clearTimeout(recTimer);
      const v = ideaEl.value.trim();
      if (v.length < 4){
        if (!v){ const box = document.getElementById('rec-results'); if (box) box.innerHTML = ''; }
        return;
      }
      recTimer = setTimeout(function(){ window.sxRecommend(); }, 400);
    });
  }
  setLang(cur());
})();
"""


def esc(s):
    return html.escape(s or "", quote=True)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def _asset_ver() -> str:
    """静态资源版本号:CSS/JS 与 hero 视频内容变化时自动失效浏览器缓存。"""
    parts = [CSS, APP_JS]
    hero = Path(__file__).resolve().parent / "assets" / "hero-loop.mp4"
    if hero.is_file():
        parts.append(hashlib.sha256(hero.read_bytes()).hexdigest())
    return sha("".join(parts))[:8]


ASSET_VER = _asset_ver()


def parse_frontmatter(text: str):
    """返回 (top_fields, meta_fields, body)。支持 metadata 嵌套键。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, {}, ""
    top, meta, end = {}, {}, None
    in_meta = False
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m:
            in_meta = m.group(1) == "metadata"
            if not in_meta:
                top[m.group(1)] = m.group(2).strip().strip('"').strip("'")
            continue
        if in_meta:
            mm = re.match(r"^\s+([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
            if mm:
                meta[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    if end is None:
        return top, meta, ""
    return top, meta, "\n".join(lines[end + 1:])


def collect_own_skills():
    skills, bodies = [], []
    for f in sorted(SKILLS_DIR.rglob("SKILL.md")):
        if f.is_symlink():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        top, meta, body = parse_frontmatter(text)
        name = top.get("name", f.parent.name)
        skills.append({
            "name": name,
            "name-zh": meta.get("name-zh", name),
            "description": top.get("description", ""),
            "description-zh": meta.get("description-zh", top.get("description", "")),
            "category": meta.get("category", "engineering-hygiene"),
            "version": meta.get("version", ""),
            "license": top.get("license", ""),
            "page": f"skills/own-{name}.html",
            "src": text,
        })
        bodies.append(body)
    return skills, bodies


def load_curation():
    if CURATION.is_file():
        try:
            return json.loads(CURATION.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"include": {}, "excluded": {}}


def fetch_upstream_stats(namespaces):
    """拉取上游仓库 Star/Fork(24h 缓存)。失败不阻断构建。"""
    if STAR_CACHE.is_file():
        try:
            cache = json.loads(STAR_CACHE.read_text(encoding="utf-8"))
            if time.time() - cache.get("_ts", 0) < 86400 and cache.get("repos"):
                return cache["repos"]
        except json.JSONDecodeError:
            pass
    repos = {}
    for ns in namespaces:
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{ns}",
                headers={"User-Agent": "skill-x-build", "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.loads(r.read().decode("utf-8", "replace"))
            repos[ns] = {"stars": d.get("stargazers_count"), "forks": d.get("forks_count"),
                         "pushed": (d.get("pushed_at") or "")[:10]}
        except Exception as e:  # noqa: BLE001
            repos[ns] = {"stars": None, "forks": None, "error": str(e)[:80]}
    try:
        STAR_CACHE.write_text(json.dumps({"_ts": time.time(), "repos": repos}, indent=1), encoding="utf-8")
    except OSError:
        pass
    return repos


def collect_external():
    i18n = json.loads(I18N_EXT.read_text(encoding="utf-8")) if I18N_EXT.is_file() else {}
    curation = load_curation()
    if not EXTERNAL.is_file():
        return [], i18n
    doc = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    suites = [s for s in doc.get("suites", []) if s.get("verified", {}).get("execReview") == "passed"]
    kept = []
    for suite in suites:
        ns = suite["namespace"]
        allow = curation.get("include", {}).get(ns)
        total = len(suite["skills"])
        if allow is not None:
            suite["skills"] = [x for x in suite["skills"] if x["name"] in allow]
        if not suite["skills"]:
            continue  # 无符合方向技能的套件整体不展示
        suite["totalSkills"] = total
        kept.append(suite)
    suites = kept
    for suite in suites:
        table = i18n.get(suite["namespace"], {})
        for s in suite["skills"]:
            extra = table.get(s["name"], {})
            s["name-zh"] = extra.get("name-zh", s["name"])
            s["description-zh"] = extra.get("description-zh", s.get("description", ""))
            s["category"] = extra.get("category", "dev-workflow")
    return suites, i18n


def collect_mcps():
    """读 mcp-registry.json,只返回人工审查通过的条目(渲染用结构)。"""
    reg = ROOT / "mcp-registry.json"
    if not reg.is_file():
        return []
    out = []
    for s in json.loads(reg.read_text(encoding="utf-8")).get("servers", []):
        cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
        if (cur.get("reviewed") or {}).get("execReview") != "passed":
            continue
        pkgs = s.get("packages") or []
        remotes = s.get("remotes") or []
        out.append({
            "name": s.get("name", ""), "title": s.get("title") or s.get("name", ""),
            "description": s.get("description", ""),
            "description-zh": cur.get("description-zh", s.get("description", "")),
            "version": s.get("version", ""),
            "kind": cur.get("kind", "remote" if remotes else "local"),
            "category": cur.get("category", "dev-workflow"),
            "riskLevel": cur.get("riskLevel", "medium"),
            "installHint": cur.get("installHint", ""),
            "remote_url": remotes[0].get("url", "") if remotes else "",
            "remote_type": remotes[0].get("type", "") if remotes else "",
            "pkg_id": f"{pkgs[0].get('registryType')}:{pkgs[0].get('identifier')}" if pkgs else "",
            "websiteUrl": s.get("websiteUrl", ""),
            "repository": (s.get("repository") or {}).get("url", ""),
            "riskNote": cur.get("riskNote", ""),
            "reviewed": cur.get("reviewed") or {},
            "upstreamStatus": cur.get("upstreamStatus") or {},
            "remotes": remotes,
            "packages": pkgs,
        })
    return out


def ns_slug(ns: str) -> str:
    return re.sub(r"[^\w.-]+", "--", ns)


def mcp_slug(name: str) -> str:
    return re.sub(r"[^\w.-]+", "--", name)


def leak_assert(pages: dict, bodies):
    for path, text in pages.items():
        for body in bodies:
            for s in [ln.strip() for ln in body.splitlines() if len(ln.strip()) >= 40][:5]:
                if s in text or esc(s) in text:
                    raise SystemExit(f"[FAIL] 泄露断言命中 {path}: {s[:60]}...")
    print(f"[+] 泄露断言通过({len(pages)} 页 x {len(bodies)} 个自研正文)")


def nav(active="home"):
    def cls(k):
        return ' class="nav active"' if k == active else ' class="nav"'
    return f'''<div class="topnav">
  <a class="brand" href="/">Skill X</a>
  <a href="/"{cls("home")} data-zh="首页" data-en="Home">首页</a>
  <a href="/skills.html"{cls("skills")} data-zh="技能" data-en="Skills">技能</a>
  <a href="/mcp.html"{cls("mcp")} data-zh="MCP" data-en="MCP">MCP</a>
  <a href="/api.html"{cls("api")} data-zh="API" data-en="API">API</a>
  <a href="/about.html"{cls("about")} data-zh="关于" data-en="About">关于</a>
  <button class="lang-btn">EN</button>
</div>'''


def page_shell(title, title_en, active, inner):
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Skill X</title>
<link rel="stylesheet" href="/assets/style.css?v={ASSET_VER}">
</head><body>
<div class="scroll-progress" aria-hidden="true"></div>
{nav(active)}
<div class="wrap">{inner}</div>
<footer><a class="back" href="/">← <span data-zh="返回首页" data-en="Home">返回首页</span></a> · Skill X,Agent Skills 开放规范</footer>
<script src="/assets/app.js?v={ASSET_VER}"></script>
</body></html>'''


def card(s, kind, page, stat_key):
    cat = s.get("category", "")
    cat_label = CATEGORIES.get(cat, cat)
    kind_cls = "kind-own" if kind == "own" else "kind-ext"
    kind_text = "自研" if kind == "own" else "收录"
    search = f'{s["name"]} {s.get("name-zh","")} {s["description"]} {s.get("description-zh","")}'.lower()
    desc_html = f'<span data-zh="{esc(s.get("description-zh",""))}" data-en="{esc(s["description"][:300])}">{esc(s.get("description-zh",""))}</span>'
    return f'''<div class="card cat-{esc(cat)}" data-search="{esc(search)}" data-category="{esc(cat)}">
  <h3><a href="/{page}">{esc(s.get("name-zh", s["name"]))}</a></h3>
  <div class="en-name">{esc(s["name"])}</div>
  <p>{desc_html}</p>
  <div class="meta"><span class="tag cat">{esc(cat_label)}</span><span class="tag {kind_cls}">{kind_text}</span><span class="count" data-stat="{esc(stat_key)}">—</span></div>
</div>'''


def chips_html():
    chips = ['<span class="chip on" data-cat="" data-zh="全部" data-en="All">全部</span>']
    for k, v in CATEGORIES.items():
        chips.append(f'<span class="chip" data-cat="{k}" data-zh="{esc(v)}" data-en="{k}">{esc(v)}</span>')
    return '<div class="chips">' + "".join(chips) + "</div>"


def render_index(own, suites):
    total_ext = sum(len(s["skills"]) for s in suites)
    own_cards = "\n".join(card(s, "own", s["page"], s["name"]) for s in own)
    suite_sections = []
    for suite in suites:
        ns = suite["namespace"]
        lic = suite["license"]["spdx"]
        lic_badge = lic if lic != "UNKNOWN" else "许可证未确认"
        items = "\n".join(card(s, "ext", f"skills/ext-{ns_slug(ns)}--{s['name']}.html", f"{ns}/{s['name']}") for s in suite["skills"])
        suite_sections.append(f'''<section class="suite">
  <h3><a href="suites/{ns_slug(ns)}.html">{esc(ns)}</a> <span class="suite-meta">{len(suite["skills"])} 个技能 {esc(lic_badge)} <a href="{esc(suite["upstream"])}">上游仓库</a></span></h3>
  <div class="grid">{items}</div>
</section>''')

    inner = f'''
<div class="hero">
  <div class="eyebrow">security research skills for AI agents</div>
  <h1>给 AI Agent 的安全研究技能库</h1>
  <p class="lede">逆向、渗透、样本分析、内存取证。自研技能经授权分发,社区精选技能一键指向上游;每个技能都带安全审计、结构导图与可直接调用的工具。</p>
  <div class="stats">
    <span><b class="counter" data-count="{len(own)}">0</b><span>自研技能</span></span>
    <span><b class="counter" data-count="{total_ext}">0</b><span>社区精选</span></span>
    <span><b class="counter" data-count="{len(suites)}">0</b><span>收录套件</span></span>
  </div>
  <div class="finder">
    <textarea id="idea" rows="2" data-zh="描述你要做的事…例如:分析一个可疑的 exe / 排查网站越权 / 内存里找配置偏移" data-en="Describe your task… e.g. analyze a suspicious exe / test IDOR / find offsets in memory" data-attr="placeholder" placeholder="描述你要做的事…例如:分析一个可疑的 exe / 排查网站越权 / 内存里找配置偏移"></textarea>
    <div class="act">
      <button class="btn" id="find-btn" data-zh="查找适用技能" data-en="Find skills">查找适用技能</button>
      <span class="hint" data-zh="Ctrl + Enter 立即查找,或继续浏览下方全部技能" data-en="Ctrl + Enter to search, or keep browsing below">Ctrl + Enter 立即查找,或继续浏览下方全部技能</span>
    </div>
  </div>
  <div class="recs" id="rec-results"></div>
  <div class="empty hidden" id="rec-empty" data-zh="没有匹配到技能,换个说法试试" data-en="No matching skills. Try different wording.">没有匹配到技能,换个说法试试</div>
</div>
<div class="search"><input id="q" type="search" data-zh="按名称或关键词筛选技能…" data-en="Filter skills by name or keyword…" data-attr="placeholder" placeholder="按名称或关键词筛选技能…"></div>
{chips_html()}
<div id="empty" class="empty hidden" data-zh="没有匹配的技能" data-en="No matching skills">没有匹配的技能</div>
<h2 data-zh="自研技能" data-en="Own skills">自研技能 <span class="n">{len(own)} 个 · 私有授权分发</span></h2>
<div class="grid" id="library">{own_cards}</div>
<div class="notice"><span data-zh="自研技能经私有仓库授权分发。获得授权的协作者:" data-en="Own skills are distributed via a private repo. Authorized collaborators:">自研技能经私有仓库授权分发。获得授权的协作者:</span><code class="inl">GITHUB_TOKEN=&lt;PAT&gt; npx skills add JacksenHu/skill-x --skill &lt;name&gt;</code></div>
<h2 data-zh="社区精选" data-en="Curated">社区精选 <span class="n">{total_ext} 个 · 已过四坑检查 · <a href="/suites/">套件中心</a></span></h2>
{"".join(suite_sections) if suite_sections else "<p>暂无收录</p>"}'''
    return page_shell("技能库", "Skills", "skills", inner)


AUDIT_PATH = Path(__file__).resolve().parent / "audit" / "audit-report.json"
LVL_LABEL = {"low": "低", "medium": "中", "high": "高", "critical": "严重"}
AUDIT_EN = {
    "可执行文件面": "Executable surface",
    "危险调用(subprocess/eval/exec/rmtree)": "Dangerous calls",
    "网络外联": "Network egress",
    "凭证读取": "Credential access",
    "SKILL.md 指令注入模式": "Instruction-injection patterns",
    "混淆特征(长 base64/hex)": "Obfuscation markers",
    "第三方依赖": "Third-party deps",
    "文件清单与体积": "File inventory",
    "命名空间": "Namespace",
    "许可证核验": "License verification",
    "可执行面审查": "Executable review",
    "上游存活": "Upstream availability",
}


def load_audit():
    if AUDIT_PATH.is_file():
        try:
            return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def render_audit_block(entry, generated_at=""):
    if not entry:
        return ('<details class="audit"><summary><span class="grade grade-B">—</span>'
                '<span data-zh="安全审计" data-en="Security Audit">安全审计</span>'
                '<span class="audit-meta" data-zh="暂无审计数据" data-en="no data yet">暂无审计数据</span></summary></details>')
    grade = entry.get("grade", "?")
    score = entry.get("score", 0)
    checks = entry.get("checks", [])
    is_ingest = entry.get("source") == "ingestion-review"
    src_zh = "收录审查记录(四坑检查)" if is_ingest else "本仓库静态扫描(AST 级)"
    src_en = "Ingestion review record" if is_ingest else "Repository static scan (AST-level)"
    rows = ""
    for c in checks:
        lvl = c.get("level", "info")
        label_zh = "通过" if lvl == "info" else LVL_LABEL.get(lvl, lvl)
        label_en = "Pass" if lvl == "info" else lvl
        name_zh = c.get("name", "")
        name_en = AUDIT_EN.get(name_zh, name_zh)
        rows += (f"<tr><td><span data-zh=\"{esc(name_zh)}\" data-en=\"{esc(name_en)}\">{esc(name_zh)}</span></td>"
                 f"<td><span class='lvl lvl-{esc(lvl)}'>"
                 f"<span data-zh=\"{esc(label_zh)}\" data-en=\"{esc(label_en)}\">{esc(label_zh)}</span></span></td>"
                 f"<td class='audit-detail'>{esc(c.get('detail', ''))}</td></tr>")
    return f'''<details class="audit">
  <summary>
    <span class="grade grade-{esc(grade)}">{esc(grade)}</span>
    <span data-zh="安全审计,点击展开明细" data-en="Security audit, click to expand">安全审计,点击展开明细</span>
    <span class="audit-meta">{score}/100 · {len(checks)} <span data-zh="项检查" data-en="checks">项检查</span> · {esc(generated_at)}</span>
  </summary>
  <div class="audit-body">
    <table class="api">
      <tr><th data-zh="检查项" data-en="Check">检查项</th><th data-zh="结果" data-en="Result">结果</th><th data-zh="明细" data-en="Detail">明细</th></tr>
      {rows}
    </table>
    <p class="hint-dim"><span data-zh="审计方式:{src_zh};自动生成,随每次构建刷新。" data-en="Method: {src_en}; auto-generated on every build.">审计方式:{src_zh};自动生成,随每次构建刷新。</span></p>
  </div>
</details>'''


def render_own_detail(s, tool_entries=None, audit_entry=None, audit_at="", map_svg=""):
    cat_label = CATEGORIES.get(s.get("category", ""), "")
    tools_html = ""
    if tool_entries:
        rows = ""
        for e in tool_entries:
            args_html = "<br>".join(f"<code class='inl'>{esc(f)}</code> {esc(h)}" for f, h in e["args"]) or "—"
            zh = e.get("summary-zh") or e["summary"]
            rows += (f"<tr><td><code class='inl'>{esc(e['script'])}</code></td>"
                     f"<td><span data-zh=\"{esc(zh)}\" data-en=\"{esc(e['summary'])}\">{esc(zh)}</span></td>"
                     f"<td>{args_html}</td></tr>")
        tools_html = (f"<h2 data-zh='自带工具(随技能安装)' data-en='Bundled tools (installed with the skill)'>自带工具(随技能安装)</h2>"
                      f"<table class='api'><tr><th data-zh='脚本' data-en='Script'>脚本</th>"
                      f"<th data-zh='功能' data-en='Function'>功能</th>"
                      f"<th data-zh='参数' data-en='Args'>参数</th></tr>{rows}</table>"
                      f"<p class='hint-dim' data-zh='纯标准库零依赖,安装技能后由 agent 在本地调用;参数从 argparse 定义自动提取。' "
                      f"data-en='Zero-dependency stdlib tools, invoked locally by the agent after install; args auto-extracted from argparse.'>"
                      f"纯标准库零依赖,安装技能后由 agent 在本地调用;参数从 argparse 定义自动提取。</p>")
    else:
        tools_html = (f"<h2 data-zh='自带工具' data-en='Bundled tools'>自带工具</h2>"
                      f"<p class='hint-dim' data-zh='本技能为方法论/纪律型,无附带脚本。' data-en='Methodology-only skill; no bundled scripts.'>"
                      f"本技能为方法论/纪律型,无附带脚本。</p>")
    inner = f'''<div class="detail">
  <div class="card-head"><h1>{esc(s.get("name-zh", s["name"]))}</h1><span class="badge auth">安装需授权</span></div>
  <div class="en-name">{esc(s["name"])}</div>
  <p class="desc"><span data-zh="{esc(s.get("description-zh",""))}" data-en="{esc(s["description"])}">{esc(s.get("description-zh",""))}</span></p>
  <dl class="kv">
    <dt data-zh="类型" data-en="Type">类型</dt><dd data-zh="自研(私有分发)" data-en="Own (private distribution)">自研(私有分发)</dd>
    <dt data-zh="分类" data-en="Category">分类</dt><dd>{esc(cat_label)}</dd>
    <dt data-zh="版本" data-en="Version">版本</dt><dd>v{esc(s.get("version") or "1.0.0")}</dd>
    <dt data-zh="许可证" data-en="License">许可证</dt><dd>{esc(s.get("license") or "MIT")}</dd>
    <dt data-zh="下载量" data-en="Downloads">下载量</dt><dd><span class="dl" data-stat="{esc(s["name"])}">—</span></dd>
  </dl>
  <div class="mmap">{map_svg}</div>
  <p class="hint-warn" data-zh="获得授权的协作者可安装:" data-en="Authorized collaborators can install:">获得授权的协作者可安装:</p>
  <div class="cmd">GITHUB_TOKEN=&lt;PAT&gt; npx skills add JacksenHu/skill-x --skill {esc(s["name"])}</div>
  <button class="chip on copy-btn" data-copy="GITHUB_TOKEN=<PAT> npx skills add JacksenHu/skill-x --skill {esc(s["name"])}" data-skill="{esc(s["name"])}" data-zh="复制安装命令" data-en="Copy install command">复制安装命令</button>
</div>
{tools_html}
{render_audit_block(audit_entry, audit_at)}'''
    return page_shell(s.get("name-zh", s["name"]), s["name"], "skills", inner)


def render_ext_detail(suite, s, audit_entry=None, audit_at="", map_svg=""):
    ns = suite["namespace"]
    lic = suite["license"]["spdx"]
    lic_text = lic if lic != "UNKNOWN" else "未确认(仅链接收录)"
    install = f"npx skills add {ns} --skill {s['name']}"
    inner = f'''<div class="detail">
  <div class="card-head"><h1>{esc(s.get("name-zh", s["name"]))}</h1><span class="badge ext">社区精选</span></div>
  <div class="en-name">{esc(s["name"])}</div>
  <p class="desc"><span data-zh="{esc(s.get("description-zh",""))}" data-en="{esc(s["description"])}">{esc(s.get("description-zh",""))}</span></p>
  <dl class="kv">
    <dt data-zh="套件" data-en="Suite">套件</dt><dd>{esc(ns)}</dd>
    <dt data-zh="分类" data-en="Category">分类</dt><dd>{esc(CATEGORIES.get(s.get("category",""), ""))}</dd>
    <dt data-zh="许可证" data-en="License">许可证</dt><dd>{esc(lic_text)}</dd>
    <dt data-zh="上游文件" data-en="Upstream">上游文件</dt><dd>{esc(s["path"])}</dd>
    <dt data-zh="下载量" data-en="Downloads">下载量</dt><dd><span class="dl" data-stat="{esc(ns + "/" + s["name"])}">—</span></dd>
  </dl>
  <div class="mmap"><a href="/suites/{ns_slug(ns)}.html">{map_svg}</a></div>
  <p class="hint-ok" data-zh="一条命令安装(指向上游仓库):" data-en="Install with one command (from upstream):">一条命令安装(指向上游仓库):</p>
  <div class="cmd">{esc(install)}</div>
  <button class="chip on copy-btn" data-copy="{esc(install)}" data-skill="{esc(ns + "/" + s["name"])}" data-zh="复制安装命令" data-en="Copy install command">复制安装命令</button>
  <p class="hint-dim" data-zh="下载量统计口径:经本站链接的下载/复制行为;直连上游安装不计入。" data-en="Download stats count downloads/copies via this site only.">下载量统计口径:经本站链接的下载/复制行为;直连上游安装不计入。</p>
</div>
{render_audit_block(audit_entry, audit_at)}'''
    return page_shell(s.get("name-zh", s["name"]), s["name"], "skills", inner)


def render_suites_index(suites):
    cards = []
    for suite in suites:
        ns = suite["namespace"]
        lic = suite["license"]["spdx"]
        lic_badge = lic if lic != "UNKNOWN" else "许可证未确认"
        alive = suite.get("upstreamStatus", {}).get("alive", True)
        status = "🟢 在线" if alive else "🔴 失联"
        st = suite.get("stats") or {}
        stars = st.get("stars")
        star_txt = f"⭐ {stars:,}" if isinstance(stars, int) else "⭐ —"
        forks = st.get("forks")
        fork_txt = f"🍴 {forks:,}" if isinstance(forks, int) else ""
        total = suite.get("totalSkills", len(suite["skills"]))
        picked = len(suite["skills"])
        pick_txt = f"{picked} / {total}" if total != picked else str(picked)
        search = f"{ns} {lic} 套件 suite".lower()
        cards.append(f'''<div class="card" data-search="{esc(search)}" data-category="">
  <div class="card-head"><h3><a href="{ns_slug(ns)}.html">{esc(ns)}</a></h3><span class="badge ext">套件</span></div>
  <div class="facts"><span class="tag kind-ext">{pick_txt} 个技能</span><span class="tag">{esc(lic_badge)}</span><span class="tag">{status}</span><span class="tag">{star_txt}</span><span class="tag">{fork_txt}</span><a href="{esc(suite["upstream"])}">上游仓库</a></div>
</div>''')
    inner = f'''
<h2 data-zh="套件中心" data-en="Suite Center">套件中心</h2>
<p class="hint-dim" data-zh="精选原则:只收录符合 Skill X 方向(安全研究 / 逆向工程 / 工程纪律)的技能;「精选 N / 共 M」表示从上游套件中筛选出的符合方向技能数,完整套件可从上游获取。收录均经四坑检查(命名空间 / 许可证 / 供应链 / 死链)。" data-en="Curation: only skills aligned with security research / reverse engineering / engineering hygiene are listed. Full suites are available upstream.">精选原则:只收录符合 Skill X 方向(安全研究 / 逆向工程 / 工程纪律)的技能;「精选 N / 共 M」表示从上游套件中筛选出的符合方向技能数,完整套件可从上游获取。收录均经四坑检查(命名空间 / 许可证 / 供应链 / 死链)。</p>
<div class="grid grid-mt">{"".join(cards)}</div>
<div class="notice" data-zh="想让你的套件被收录?按接入 SOP 提交链接即可,维护者会完成四坑检查与方向筛选后收录。" data-en="Want your suite listed? Submit a link per the onboarding SOP.">想让你的套件被收录?按接入 SOP 提交链接即可,维护者会完成四坑检查与方向筛选后收录。</div>'''
    return page_shell("套件中心", "Suites", "skills", inner)


def render_suite_detail(suite, map_svg=""):
    ns = suite["namespace"]
    lic = suite["license"]["spdx"]
    st = suite.get("stats") or {}
    stars = st.get("stars")
    forks = st.get("forks")
    total = suite.get("totalSkills", len(suite["skills"]))
    picked = len(suite["skills"])
    cards = "\n".join(card(s, "ext", f"skills/ext-{ns_slug(ns)}--{s['name']}.html", f"{ns}/{s['name']}") for s in suite["skills"])
    inner = f'''<div class="detail">
  <h1>{esc(ns)}</h1>
  <dl class="kv">
    <dt data-zh="精选技能" data-en="Curated">精选技能</dt><dd>{picked} / {total}<span data-zh="(从上游套件按方向筛选)" data-en=" (curated by scope)">(从上游套件按方向筛选)</span></dd>
    <dt data-zh="上游热度" data-en="Upstream">上游热度</dt><dd>⭐ {stars:,} · 🍴 {forks:,}</dd>
    <dt data-zh="本站下载" data-en="Site downloads">本站下载</dt><dd><span class="dl" data-stat="{esc(ns)}">—</span></dd>
    <dt data-zh="许可证" data-en="License">许可证</dt><dd>{esc(lic if lic != "UNKNOWN" else "未确认(仅链接收录)")}</dd>
    <dt data-zh="收录日期" data-en="Ingested">收录日期</dt><dd>{esc(suite.get("ingestedAt", ""))}</dd>
    <dt data-zh="上游" data-en="Upstream">上游</dt><dd><a href="{esc(suite["upstream"])}">{esc(suite["upstream"])}</a></dd>
  </dl>
  <div class="mmap">{map_svg}</div>
  <p class="hint-ok" data-zh="整套件安装(含全部上游技能):" data-en="Install whole suite (all upstream skills):">整套件安装(含全部上游技能):</p>
  <div class="cmd">npx skills add {esc(ns)} --skill '*'</div>
  <button class="chip on copy-btn" data-copy="npx skills add {esc(ns)} --skill '*'" data-skill="{esc(ns)}" data-zh="复制套件安装命令" data-en="Copy suite install command">复制套件安装命令</button>
  <p class="hint-dim" data-zh="注:上游套件共 {total} 个技能,本站按方向精选 {picked} 个展示;整套安装仍会包含上游全部技能。" data-en="Note: upstream ships {total} skills; {picked} are curated here; installing the suite still includes all upstream skills.">注:上游套件共 {total} 个技能,本站按方向精选 {picked} 个展示;整套安装仍会包含上游全部技能。</p>
</div>
<h2 data-zh="精选技能" data-en="Curated skills">精选技能</h2>
{chips_html()}
<div class="grid">{cards}</div>'''
    return page_shell(ns, ns, "skills", inner)


def render_api(own, suites):
    inner = f'''
<h2 data-zh="API 文档" data-en="API Docs">API 文档</h2>
<p class="hint-dim" data-zh="本页仅收录本站对外提供的网络接口;各技能自带的命令行工具(随技能安装、由 agent 本地调用)见对应技能详情页。" data-en="This page lists network APIs only. Bundled CLI tools (installed with each skill, invoked locally by the agent) are documented on each skill page.">本页仅收录本站对外提供的网络接口;各技能自带的命令行工具(随技能安装、由 agent 本地调用)见对应技能详情页。</p>
<table class="api">
<tr><th data-zh="接口" data-en="Endpoint">接口</th><th data-zh="方法" data-en="Method">方法</th><th data-zh="说明" data-en="Description">说明</th></tr>
<tr><td><code class="inl">/api/download</code></td><td>POST</td><td data-zh="记录一次下载/复制。Body: {{"skill":"&lt;name&gt;","action":"copy"}}" data-en="Record a download/copy. Body: skill + action">记录一次下载/复制。Body: <code class="inl">{{"skill":"&lt;name&gt;","action":"copy"}}</code></td></tr>
<tr><td><code class="inl">/api/stats</code></td><td>GET</td><td data-zh="返回全部下载计数 JSON" data-en="Returns all download counters as JSON">返回全部下载计数 JSON</td></tr>
<tr><td><code class="inl">/api/health</code></td><td>GET</td><td data-zh="后端存活检查" data-en="Backend health check">后端存活检查</td></tr>
<tr><td><code class="inl">/dl/&lt;ns&gt;/&lt;skill&gt;.tar.gz</code></td><td>GET</td><td data-zh="经本站代理下载收录技能(计数生效);白名单内套件可用" data-en="Proxied download of listed skills (counted); whitelist only">经本站代理下载收录技能(计数生效);白名单内套件可用</td></tr>
<tr><td><code class="inl">/api/recommend</code></td><td>GET / POST</td><td data-zh="技能推荐:传入自然语言任务描述,返回适用技能排序(含匹配理由/安装命令)。GET 用 ?q=描述;POST 用 {{&quot;query&quot;:&quot;描述&quot;}}" data-en="Skill recommendation: pass a natural-language task; returns ranked skills with match reasons and install commands.">技能推荐:传入自然语言任务描述,返回适用技能排序(含匹配理由/安装命令)。GET 用 <code class="inl">?q=描述</code>;POST 用 <code class="inl">{{"query":"描述"}}</code></td></tr>
<tr><td><code class="inl">/site-data.json</code></td><td>GET</td><td data-zh="全量技能数据(名称/双语简介/分类/安装命令/页面路径)" data-en="Full skill data (names, bilingual descriptions, categories, install commands, page paths)">全量技能数据(名称/双语简介/分类/安装命令/页面路径)</td></tr>
<tr><td><code class="inl">/tools.json</code></td><td>GET</td><td data-zh="自研技能自带工具清单(脚本/功能/argparse 参数,机器可读)" data-en="Bundled tools inventory (scripts, functions, argparse params)">自研技能自带工具清单(脚本/功能/argparse 参数,机器可读)</td></tr>
<tr><td><code class="inl">/audit-report.json</code></td><td>GET</td><td data-zh="安全审计报告(各技能等级/评分/检查项明细,机器可读)" data-en="Security audit report (grades, scores, check details)">安全审计报告(各技能等级/评分/检查项明细,机器可读)</td></tr>
<tr><td><code class="inl">/mindmaps/&lt;skill&gt;.svg</code></td><td>GET</td><td data-zh="思维导图 SVG,已开 CORS,可外部引用" data-en="Mind map SVGs, CORS-enabled">思维导图 SVG,已开 CORS,可外部引用</td></tr>
<tr><td><code class="inl">/v0/servers</code></td><td>GET</td><td data-zh="MCP 服务列表(官方 Registry 兼容,游标分页 ?limit&cursor;只返回已过审条目)" data-en="MCP server list (official Registry-compatible, cursor-paginated; reviewed entries only)">MCP 服务列表(官方 Registry 兼容,游标分页 <code class="inl">?limit&cursor</code>;只返回已过审条目)</td></tr>
<tr><td><code class="inl">/api/mcp/install</code></td><td>POST</td><td data-zh="记录一次 MCP 安装/连接。Body: {{&quot;name&quot;:&quot;&lt;ns/name&gt;&quot;}}" data-en="Record an MCP install/connect. Body: name">记录一次 MCP 安装/连接。Body: <code class="inl">{{"name":"&lt;ns/name&gt;"}}</code></td></tr>
<tr><td><code class="inl">/v0/servers/&lt;ns/name&gt;/install</code></td><td>GET</td><td data-zh="MCP 接入描述:返回应用程序可直接用于安装/连接的结构化 JSON(config/requiredSecrets/clientSnippets 含 claude/cursor/codex/vscode 客户端片段)" data-en="MCP install descriptor: structured JSON for programmatic install/connect (config, requiredSecrets, clientSnippets for claude/cursor/codex/vscode)">MCP 接入描述:返回应用程序可直接用于安装/连接的结构化 JSON(config / requiredSecrets / clientSnippets 含 claude/cursor/codex/vscode 客户端片段)</td></tr>
<tr><td><code class="inl">/api/mcp/connect</code></td><td>POST</td><td data-zh="代为连接:Body {{&quot;name&quot;,&quot;client&quot;,&quot;secrets&quot;}};校验必填密钥后返回填好密钥的客户端配置片段(密钥仅内存拼接返回,不落库)" data-en="Connect on behalf: body name/client/secrets; validates required secrets and returns the filled client config snippet (secrets assembled in memory only, never stored)">代为连接:Body <code class="inl">{{"name","client","secrets"}}</code>;校验必填密钥后返回填好密钥的客户端配置片段(密钥仅内存拼接返回,不落库)</td></tr>
</table>
<h2 class="h2-sm" data-zh="使用示例" data-en="Examples">使用示例</h2>
<div class="cmd">curl -s https://skillx.yueliai.top/api/stats</div>
<div class="cmd">curl -s "https://skillx.yueliai.top/v0/servers?limit=10"</div>
<div class="cmd">curl -s -X POST -H "Content-Type: application/json" -d '{{"name":"ac.inference.sh/mcp"}}' https://skillx.yueliai.top/api/mcp/install</div>
<div class="cmd">curl -s https://skillx.yueliai.top/v0/servers/ac.inference.sh/mcp/install</div>
<div class="cmd">curl -s -X POST -H "Content-Type: application/json" -d '{{"name":"ac.inference.sh/mcp","client":"claude","secrets":{{}}}}' https://skillx.yueliai.top/api/mcp/connect</div>
<div class="cmd">curl -s -X POST -H "Content-Type: application/json" -d '{{"skill":"malware-analysis","action":"copy"}}' https://skillx.yueliai.top/api/download</div>
<div class="cmd">curl -s "https://skillx.yueliai.top/api/recommend?q=想给安卓apk脱壳"</div>
<div class="cmd">curl -s -X POST -H "Content-Type: application/json" -d '{{"query":"测试集体变红怎么排查"}}' https://skillx.yueliai.top/api/recommend</div>
<div class="cmd">curl -s https://skillx.yueliai.top/audit-report.json</div>
<div class="cmd">curl -sO https://skillx.yueliai.top/dl/addyosmani/agent-skills/test-driven-development.tar.gz</div>'''
    return page_shell("API 文档", "API Docs", "api", inner)


def render_mcp(mcps):
    risk_label = {"low": "低风险", "medium": "中风险", "high": "高风险", "critical": "严重"}
    cards = []
    for m in mcps:
        kind_text = "远程" if m["kind"] == "remote" else "本地"
        conn = m["remote_url"] if m["kind"] == "remote" else m["pkg_id"]
        cmd = m["installHint"] or (f"claude mcp add --transport http {m['name'].split('/')[-1]} {m['remote_url']}" if m["kind"] == "remote" else "")
        search = f"{m['name']} {m['title']} {m['description']} {m['description-zh']}".lower()
        cards.append(f'''<div class="card cat-{esc(m['category'])}" data-search="{esc(search)}" data-category="{esc(m['category'])}">
  <h3><a href="/mcp/{mcp_slug(m['name'])}.html">{esc(m['title'])}</a></h3>
  <div class="en-name">{esc(m['name'])}</div>
  <p><span data-zh="{esc(m['description-zh'])}" data-en="{esc(m['description'][:300])}">{esc(m['description-zh'])}</span></p>
  <div class="meta"><span class="tag cat">{esc(CATEGORIES.get(m['category'], m['category']))}</span><span class="tag kind-ext">{kind_text}</span><span class="tag risk-{esc(m['riskLevel'])}">{esc(risk_label.get(m['riskLevel'], m['riskLevel']))}</span><span class="count">v{esc(m['version'])}</span></div>
  <div class="cmd">{esc(cmd)}</div>
</div>''')
    body = "".join(cards) if cards else '<p class="hint-dim" data-zh="暂无已过审的 MCP 服务" data-en="No reviewed MCP servers yet">暂无已过审的 MCP 服务</p>'
    inner = f'''
<h2 data-zh="MCP 服务" data-en="MCP Servers">MCP 服务 <span class="n">{len(mcps)} 个 · 官方 server.json 标准</span></h2>
<p class="hint-dim" data-zh="Model Context Protocol 服务的安装与连接入口。远程服务填入 URL 即可连接;本地包由客户端从公共包仓库拉取并在本机起进程。用户密钥在安装时填入本地配置,不经过本站。" data-en="Install & connect entries for Model Context Protocol servers. Remote ones connect via URL; local packages are pulled by the client from public registries. Secrets are filled locally at install time, never passing through this site.">Model Context Protocol 服务的安装与连接入口。远程服务填入 URL 即可连接;本地包由客户端从公共包仓库拉取并在本机起进程。用户密钥在安装时填入本地配置,不经过本站。</p>
<div class="grid">{body}</div>
<div class="notice"><span data-zh="收录与风险说明:stdio 本地包=在本机执行第三方代码(标高风险),远程服务=连接到他人服务器(标低风险);所有条目均经人工审查(execReview=passed)才放出。" data-en="Curation & risk: stdio local packages execute third-party code on your machine (high risk); remote servers connect to third-party hosts (low risk). All entries pass manual review before listing.">收录与风险说明:stdio 本地包=在本机执行第三方代码(标高风险),远程服务=连接到他人服务器(标低风险);所有条目均经人工审查(execReview=passed)才放出。</span></div>'''
    return page_shell("MCP 服务", "MCP Servers", "mcp", inner)


def render_mcp_detail(m):
    risk_label = {"low": "低风险", "medium": "中风险", "high": "高风险", "critical": "严重"}
    kind_text = "远程" if m["kind"] == "remote" else "本地(stdio)"
    cmd = m["installHint"] or (f"claude mcp add --transport http {m['name'].split('/')[-1]} {m['remote_url']}" if m["kind"] == "remote" else "")
    conn_rows = ""
    if m["kind"] == "remote":
        for r in m["remotes"]:
            conn_rows += f'<tr><td><code class="inl">{esc(r.get("type",""))}</code></td><td><code class="inl">{esc(r.get("url",""))}</code></td></tr>'
        conn_html = (f'<h2 data-zh="连接端点" data-en="Connection endpoints">连接端点</h2>'
                     f'<table class="api"><tr><th data-zh="传输" data-en="Transport">传输</th><th data-zh="URL" data-en="URL">URL</th></tr>{conn_rows}</table>'
                     f'<p class="hint-dim" data-zh="远程服务:URL 填入客户端 MCP 配置即可连接;认证头/API 密钥在安装时填入本地配置,不经过本站。" data-en="Remote server: paste the URL into your client MCP config; auth headers/keys are filled locally at install time, never passing through this site.">远程服务:URL 填入客户端 MCP 配置即可连接;认证头/API 密钥在安装时填入本地配置,不经过本站。</p>')
    else:
        env_table = ""
        for p in m["packages"]:
            envs = ""
            for ev in p.get("environmentVariables") or []:
                req = "必填" if ev.get("isRequired") else "可选"
                sec = " · 密钥" if ev.get("isSecret") else ""
                envs += f'<tr><td><code class="inl">{esc(ev.get("name",""))}</code></td><td>{esc(req + sec)}</td><td>{esc(ev.get("description",""))}</td></tr>'
            if envs:
                env_table = (f'<h3 data-zh="环境变量" data-en="Environment variables">环境变量</h3>'
                             f'<table class="api"><tr><th data-zh="变量" data-en="Variable">变量</th><th data-zh="要求" data-en="Required">要求</th><th data-zh="说明" data-en="Description">说明</th></tr>{envs}</table>')
            conn_rows += (f'<tr><td><code class="inl">{esc(p.get("registryType",""))}</code></td>'
                          f'<td><code class="inl">{esc(p.get("identifier",""))}</code></td>'
                          f'<td>v{esc(p.get("version",""))}</td>'
                          f'<td><code class="inl">{esc((p.get("transport") or {}).get("type",""))}</code></td></tr>')
        conn_html = (f'<h2 data-zh="安装包" data-en="Package">安装包</h2>'
                     f'<table class="api"><tr><th data-zh="仓库" data-en="Registry">仓库</th><th data-zh="标识" data-en="Identifier">标识</th><th data-zh="版本" data-en="Version">版本</th><th data-zh="传输" data-en="Transport">传输</th></tr>{conn_rows}</table>'
                     f'<p class="hint-warn" data-zh="stdio 本地包:安装即在本机执行第三方进程,收录已过人工供应链审查;请确认客户端来源可信。" data-en="stdio local package: installs and runs third-party code on your machine; supply-chain reviewed at curation time.">stdio 本地包:安装即在本机执行第三方进程,收录已过人工供应链审查;请确认客户端来源可信。</p>'
                     + env_table)
    rev = m["reviewed"]
    ups = m["upstreamStatus"]
    alive = ups.get("alive", True)
    status_txt = "🟢 在线" if alive else "🔴 失联"
    links = []
    if m["websiteUrl"]:
        links.append(f'<a href="{esc(m["websiteUrl"])}">官网</a>')
    if m["repository"]:
        links.append(f'<a href="{esc(m["repository"])}">仓库</a>')
    links_html = " · ".join(links) if links else "—"
    inner = f'''<div class="detail">
  <div class="card-head"><h1>{esc(m['title'])}</h1><span class="badge ext">MCP · {kind_text}</span></div>
  <div class="en-name">{esc(m['name'])}</div>
  <p class="desc"><span data-zh="{esc(m['description-zh'])}" data-en="{esc(m['description'])}">{esc(m['description-zh'])}</span></p>
  <dl class="kv">
    <dt data-zh="分类" data-en="Category">分类</dt><dd>{esc(CATEGORIES.get(m['category'], m['category']))}</dd>
    <dt data-zh="版本" data-en="Version">版本</dt><dd>v{esc(m['version'])}</dd>
    <dt data-zh="风险等级" data-en="Risk">风险等级</dt><dd><span class="tag risk-{esc(m['riskLevel'])}">{esc(risk_label.get(m['riskLevel'], m['riskLevel']))}</span></dd>
    <dt data-zh="上游状态" data-en="Upstream">上游状态</dt><dd>{status_txt} · {esc(ups.get('lastCheck') or '—')}</dd>
    <dt data-zh="收录审查" data-en="Review">收录审查</dt><dd>{esc(rev.get('by') or '—')} · {esc(rev.get('at') or '—')}</dd>
    <dt data-zh="外部链接" data-en="Links">外部链接</dt><dd>{links_html}</dd>
  </dl>
  <p class="hint-ok" data-zh="一条命令接入客户端:" data-en="Connect with one command:">一条命令接入客户端:</p>
  <div class="cmd">{esc(cmd)}</div>
  <button class="chip on copy-btn" data-copy="{esc(cmd)}" data-skill="mcp:{esc(m['name'])}" data-zh="复制接入命令" data-en="Copy connect command">复制接入命令</button>
  <p class="hint-dim">{esc(m['riskNote'])}</p>
</div>
{conn_html}'''
    return page_shell(m["title"], m["name"], "mcp", inner)




def render_home(own, suites, mcps, map_svg=""):
    total_ext = sum(len(s["skills"]) for s in suites)
    audit = load_audit()
    audit_at = audit.get("generatedAt", "")
    audit_entry = (audit.get("skills") or {}).get("binary-reverse-engineering")
    featured = "\n".join(card(s, "own", s["page"], s["name"]) for s in own[:3])
    for suite in suites:
        ns = suite["namespace"]
        for s in suite["skills"][:2]:
            featured += "\n" + card(s, "ext", f"skills/ext-{ns_slug(ns)}--{s['name']}.html", f"{ns}/{s['name']}")
    mcp_items = ""
    for m in mcps[:2]:
        is_remote = m.get("kind") == "remote"
        kind_zh = "远程" if is_remote else "本地"
        kind_en = "Remote" if is_remote else "Local"
        risk = esc(m.get("riskLevel", ""))
        mcp_items += (f'<a class="home-mcp-item" href="/mcp/{mcp_slug(m["name"])}.html">'
                      f'<div class="t">{esc(m.get("title", m["name"]))}</div>'
                      f'<div class="id">{esc(m["name"])}</div>'
                      f'<div class="meta"><span class="tag" data-zh="{kind_zh}" data-en="{kind_en}">{kind_zh}</span>'
                      f'<span class="tag risk-{risk}">{risk}</span>'
                      f'<span class="tag">v{esc(m.get("version", ""))}</span></div></a>')
    if not mcp_items:
        mcp_items = ('<p class="hint-dim" data-zh="MCP 服务正在收录中。" '
                     'data-en="MCP servers are being curated.">MCP 服务正在收录中。</p>')
    first_mcp = mcps[0] if mcps else None
    if first_mcp:
        mcp_name = first_mcp["name"]
        mcp_cmd = first_mcp.get("installHint") or (f"claude mcp add --transport http {mcp_name.split('/')[-1]} {first_mcp.get('remote_url','')}" if first_mcp.get("kind") == "remote" else "")
    else:
        mcp_name, mcp_cmd = "", ""
    inner = f'''
<section class="home-hero">
  <div class="home-hero-bg" aria-hidden="true"></div>
  <video class="home-hero-video" src="/assets/hero-loop.mp4?v={ASSET_VER}" autoplay muted loop playsinline preload="metadata" aria-hidden="true"></video>
  <div class="home-hero-scrim" aria-hidden="true"></div>
  <div class="home-hero-inner">
    <p class="eyebrow" data-zh="security research skills for AI agents" data-en="security research skills for AI agents">security research skills for AI agents</p>
    <h1>Skill X</h1>
    <p class="home-offer" data-zh="给 AI Agent 的安全研究技能库" data-en="The security research skill library for AI agents">给 AI Agent 的安全研究技能库</p>
    <p class="home-lede" data-zh="逆向、渗透、样本分析、内存取证。每个技能都带安全审计、结构导图与可直接调用的工具;社区精选技能一键指向上游。" data-en="Reverse engineering, pentesting, malware analysis, memory forensics. Every skill ships with a security audit, a structure map and runnable tools; curated community skills install straight from upstream.">逆向、渗透、样本分析、内存取证。每个技能都带安全审计、结构导图与可直接调用的工具;社区精选技能一键指向上游。</p>
    <div class="home-cta">
      <a class="btn" href="/skills.html" data-zh="浏览技能库" data-en="Browse skills">浏览技能库</a>
      <a class="btn ghost" href="/mcp.html" data-zh="查看 MCP 服务" data-en="Explore MCP servers">查看 MCP 服务</a>
    </div>
    <dl class="home-stats">
      <div><dt data-zh="自研技能" data-en="Own skills">自研技能</dt><dd><span class="counter" data-count="{len(own)}">0</span></dd></div>
      <div><dt data-zh="社区精选" data-en="Curated">社区精选</dt><dd><span class="counter" data-count="{total_ext}">0</span></dd></div>
      <div><dt data-zh="MCP 服务" data-en="MCP servers">MCP 服务</dt><dd><span class="counter" data-count="{len(mcps)}">0</span></dd></div>
      <div><dt data-zh="安全审计项" data-en="Audit checks">安全审计项</dt><dd><span class="counter" data-count="8">0</span></dd></div>
    </dl>
  </div>
</section>

<section class="bench" id="workbench">
  <div class="bench-rail" role="tablist" aria-label="workbench">
    <button class="step on" id="step-finder" data-step="0" role="tab" aria-selected="true"><i>01</i><b data-zh="技能推荐器" data-en="Skill finder">技能推荐器</b><span data-zh="描述任务,返回可用技能" data-en="Describe a task, get matching skills">描述任务,返回可用技能</span></button>
    <button class="step" id="step-map" data-step="1" role="tab" aria-selected="false"><i>02</i><b data-zh="结构导图" data-en="Structure map">结构导图</b><span data-zh="技能的结构与工作流" data-en="Structure and workflow">技能的结构与工作流</span></button>
    <button class="step" id="step-audit" data-step="2" role="tab" aria-selected="false"><i>03</i><b data-zh="安全审计" data-en="Security audit">安全审计</b><span data-zh="AST 级 8 项检查" data-en="8 AST-level checks">AST 级 8 项检查</span></button>
    <button class="step" id="step-mcp" data-step="3" role="tab" aria-selected="false"><i>04</i><b data-zh="MCP 接入" data-en="MCP connect">MCP 接入</b><span data-zh="按客户端生成配置" data-en="Per-client config">按客户端生成配置</span></button>
  </div>
  <div class="bench-stage">
    <div class="console">
      <div class="console-bar"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="console-path">skillx://workbench</span><span class="console-live">LIVE</span></div>
      <div class="console-body">
        <div class="panel on" data-panel="0">
          <div class="finder">
            <textarea id="idea" rows="2" data-zh="例如:分析一个可疑的 exe / 排查接口越权 / 内存里找配置偏移" data-en="e.g. analyze a suspicious exe / test an IDOR / find offsets in memory" data-attr="placeholder" placeholder="例如:分析一个可疑的 exe / 排查接口越权 / 内存里找配置偏移"></textarea>
            <div class="act"><button class="btn" id="find-btn" data-zh="查找适用技能" data-en="Find skills">查找适用技能</button><span class="hint" data-zh="Ctrl + Enter" data-en="Ctrl + Enter">Ctrl + Enter</span></div>
          </div>
          <div class="recs" id="rec-results"></div>
          <div class="empty hidden" id="rec-empty" data-zh="没有匹配到技能,换个说法试试" data-en="No matching skills. Try different wording.">没有匹配到技能,换个说法试试</div>
        </div>
        <div class="panel" data-panel="1">
          <div class="mmap">{map_svg}</div>
        </div>
        <div class="panel" data-panel="2">
          {render_audit_block(audit_entry, audit_at)}
        </div>
        <div class="panel" data-panel="3" id="mcp-demo" data-mcp="{esc(mcp_name)}">
          <div class="demo-tabs">
            <button class="tab on" data-client="claude">Claude</button>
            <button class="tab" data-client="cursor">Cursor</button>
            <button class="tab" data-client="codex">Codex</button>
            <button class="tab" data-client="vscode">VS Code</button>
          </div>
          <pre class="cmd demo-snippet" id="mcp-snippet">{esc(mcp_cmd)}</pre>
          <div class="demo-actions"><button class="tab on copy-btn" id="mcp-copy" data-copy="{esc(mcp_cmd)}" data-skill="mcp:{esc(mcp_name)}" data-zh="复制配置" data-en="Copy config">复制配置</button><span class="hint-dim" id="mcp-status" data-zh="正在读取接入描述…" data-en="Loading install descriptor...">正在读取接入描述…</span></div>
        </div>
      </div>
      <div class="console-foot" id="bench-meta">POST /api/recommend · 自然语言 → 技能排序</div>
    </div>
  </div>
</section>

<section class="home-featured">
  <h2 data-zh="技能精选" data-en="Featured skills">技能精选 <span class="n">{len(own)} 个自研 · {total_ext} 个社区精选</span></h2>
  <div class="grid reveal">{featured}</div>
</section>

<section class="home-mcp">
  <h2 data-zh="MCP 服务" data-en="MCP servers">MCP 服务 <span class="n">{len(mcps)} 个已过审</span></h2>
  <p class="hint-dim" data-zh="按官方 server.json 标准收录,只放人工审查通过的条目;密钥与认证头永不经过本站。" data-en="Curated to the official server.json standard; reviewed entries only; secrets never pass through this site.">按官方 server.json 标准收录,只放人工审查通过的条目;密钥与认证头永不经过本站。</p>
  <div class="home-mcp-list reveal">{mcp_items}</div>
  <p class="home-more"><a class="btn ghost" href="/mcp.html" data-zh="全部 MCP 服务" data-en="All MCP servers">全部 MCP 服务</a></p>
</section>

<section class="home-trust">
  <div class="trust-item reveal"><b data-zh="四坑检查" data-en="Four checks">四坑检查</b><span data-zh="命名空间、许可证、供应链、死链,逐项核验后才收录。" data-en="Namespace, license, supply chain and link liveness are verified before anything is listed.">命名空间、许可证、供应链、死链,逐项核验后才收录。</span></div>
  <div class="trust-item reveal"><b data-zh="只放已过审" data-en="Reviewed only">只放已过审</b><span data-zh="未通过人工审查的条目不会出现在橱窗与 API 输出里。" data-en="Entries that fail human review never reach the catalog or the API output.">未通过人工审查的条目不会出现在橱窗与 API 输出里。</span></div>
  <div class="trust-item reveal"><b data-zh="密钥零留存" data-en="No secrets stored">密钥零留存</b><span data-zh="下载密钥、MCP 凭据只在会话内拼接使用,不落盘、不入库。" data-en="Download keys and MCP credentials are assembled in memory only; nothing is written to disk.">下载密钥、MCP 凭据只在会话内拼接使用,不落盘、不入库。</span></div>
</section>

<section class="home-cta-band reveal">
  <h2 data-zh="开始使用" data-en="Get started">开始使用</h2>
  <p data-zh="浏览技能库,或直接接入 MCP 服务。所有页面与 API 都有真实的审计与收录记录。" data-en="Browse the skill library or connect an MCP server. Every page and API is backed by real review records.">浏览技能库,或直接接入 MCP 服务。所有页面与 API 都有真实的审计与收录记录。</p>
  <div class="home-cta"><a class="btn" href="/skills.html" data-zh="浏览技能库" data-en="Browse skills">浏览技能库</a><a class="btn ghost" href="/api.html" data-zh="API 文档" data-en="API docs">API 文档</a></div>
</section>'''
    return page_shell("Skill X", "Skill X", "home", inner)


def render_about(own, suites):
    total_ext = sum(len(s["skills"]) for s in suites)
    inner = f'''
<h2 data-zh="关于 Skill X" data-en="About Skill X">关于 Skill X</h2>
<div class="detail">
<p class="desc" data-zh="Skill X 是面向所有 AI Agent 的技能注册中心,方向为安全研究与逆向工程(红队/白帽)。自研技能 {len(own)} 个,社区收录 {total_ext} 个({len(suites)} 个套件)。" data-en="Skill X is a skill registry for all AI agents, focused on security research and reverse engineering.">Skill X 是面向所有 AI Agent 的技能注册中心,方向为安全研究与逆向工程(红队/白帽)。自研技能 {len(own)} 个,社区收录 {total_ext} 个({len(suites)} 个套件)。</p>
<dl class="kv">
<dt data-zh="规范" data-en="Spec">规范</dt><dd>Agent Skills(agentskills.io)</dd>
<dt data-zh="源码" data-en="Source">源码</dt><dd>GitHub 私有仓库(授权访问)</dd>
<dt data-zh="安装" data-en="Install">安装</dt><dd>vercel-labs/skills CLI(80+ agent)</dd>
<dt data-zh="下载量口径" data-en="Stats scope">下载量口径</dt><dd data-zh="经本站链接的下载/复制行为;直连上游安装不计入" data-en="Downloads/copies via this site only">经本站链接的下载/复制行为;直连上游安装不计入</dd>
<dt data-zh="收录" data-en="Ingestion">收录</dt><dd data-zh="按接入 SOP 经四坑检查(命名空间/许可证/供应链/死链)后收录" data-en="Ingested via SOP with four checks">按接入 SOP 经四坑检查(命名空间/许可证/供应链/死链)后收录</dd>
</dl>
</div>'''
    return page_shell("关于", "About", "about", inner)


def main():
    own, bodies = collect_own_skills()
    suites, _ = collect_external()
    mcps = collect_mcps()
    stats = fetch_upstream_stats([s["namespace"] for s in suites])
    for s in suites:
        s["stats"] = stats.get(s["namespace"], {})

    # 导图先行渲染(详情页内联,支持悬停与连线动效)
    mmaps = {}
    mind_dir = Path(__file__).resolve().parent / "mindmaps"
    if mind_dir.is_dir():
        for y in sorted(mind_dir.glob("*.yaml")):
            try:
                mmaps[y.stem] = render_svg(parse_map(y.read_text(encoding="utf-8")), "")
            except Exception:
                continue

    pages = {"index.html": render_home(own, suites, mcps, mmaps.get("binary-reverse-engineering", "")),
             "skills.html": render_index(own, suites)}
    tool_docs = apidocs.collect()
    audit = load_audit()
    audit_at = audit.get("generatedAt", "")
    for s in own:
        pages[s["page"]] = render_own_detail(s, tool_docs.get(s["name"], []),
                                            (audit.get("skills") or {}).get(s["name"]), audit_at,
                                            mmaps.get(s["name"], ""))
    pages["suites/index.html"] = render_suites_index(suites)
    for suite in suites:
        ns = suite["namespace"]
        pages[f"suites/{ns_slug(ns)}.html"] = render_suite_detail(suite, mmaps.get(f"suite-{ns_slug(ns)}", ""))
        for s in suite["skills"]:
            pages[f"skills/ext-{ns_slug(ns)}--{s['name']}.html"] = render_ext_detail(
                suite, s, (audit.get("suites") or {}).get(ns), audit_at,
                mmaps.get(f"suite-{ns_slug(ns)}", ""))
    pages["mcp.html"] = render_mcp(mcps)
    for m in mcps:
        pages[f"mcp/{mcp_slug(m['name'])}.html"] = render_mcp_detail(m)
    pages["api.html"] = render_api(own, suites)
    pages["about.html"] = render_about(own, suites)

    leak_assert(pages, bodies)

    old_manifest = {}
    if MANIFEST.is_file():
        try:
            old_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    new_manifest, written, skipped = {}, 0, 0
    src_all = "".join(s["src"] for s in own) + (EXTERNAL.read_text(encoding="utf-8") if EXTERNAL.is_file() else "") + (I18N_EXT.read_text(encoding="utf-8") if I18N_EXT.is_file() else "")

    for rel, text in pages.items():
        key = sha(TEMPLATE_VERSION + rel + src_all + text)
        new_manifest[rel] = key
        p = DIST / rel
        if old_manifest.get(rel) == key and p.is_file():
            skipped += 1
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        written += 1

    mind_dir = Path(__file__).resolve().parent / "mindmaps"
    svg_src = (Path(__file__).resolve().parent / "svg_map.py").read_text(encoding="utf-8")
    mmap_count = 0
    if mind_dir.is_dir():
        for y in sorted(mind_dir.glob("*.yaml")):
            try:
                svg_text = render_svg(parse_map(y.read_text(encoding="utf-8")), y.stem)
            except Exception as e:  # noqa: BLE001
                print(f"[-] 导图渲染失败 {y.name}: {e}(降级:该图不上线)")
                continue
            rel = f"mindmaps/{y.stem}.svg"
            key = sha(TEMPLATE_VERSION + rel + y.read_text(encoding="utf-8") + svg_src)
            new_manifest[rel] = key
            p = DIST / rel
            if old_manifest.get(rel) == key and p.is_file():
                skipped += 1
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(svg_text, encoding="utf-8")
                written += 1
            mmap_count += 1

    assets = DIST / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name, content in [("style.css", CSS), ("app.js", APP_JS)]:
        key = sha(TEMPLATE_VERSION + content)
        new_manifest[f"assets/{name}"] = key
        p = assets / name
        if old_manifest.get(f"assets/{name}") == key and p.is_file():
            skipped += 1
        else:
            p.write_text(content, encoding="utf-8")
            written += 1

    # 静态媒体资源(hero 视频 / 实拍图):原样复制,内容哈希进 manifest
    src_assets = Path(__file__).resolve().parent / "assets"
    if src_assets.is_dir():
        media_ext = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".svg", ".ico", ".mp4", ".webm")
        for f in sorted(src_assets.iterdir()):
            if not f.is_file() or f.suffix.lower() not in media_ext:
                continue
            data = f.read_bytes()
            rel_asset = f"assets/{f.name}"
            key = sha(TEMPLATE_VERSION + f.name + hashlib.sha256(data).hexdigest())
            new_manifest[rel_asset] = key
            p = assets / f.name
            if old_manifest.get(rel_asset) == key and p.is_file():
                skipped += 1
            else:
                p.write_bytes(data)
                written += 1

    # 清理过时产物(已下架技能/套件/导图的残留文件,避免旧页面仍可访问)
    valid = set(new_manifest.keys())
    removed = 0
    for f in sorted(DIST.rglob("*")):
        if not f.is_file() or f.is_symlink():
            continue
        rel = str(f.relative_to(DIST)).replace("\\", "/")
        stale_page = rel.endswith((".html", ".svg")) and rel not in valid
        stale_media = rel.startswith("assets/") and rel not in valid
        if stale_page or stale_media:
            f.unlink()
            removed += 1
            print(f"[-] 清理过时产物: {rel}")

    site_data = {
        "categories": CATEGORIES,
        "own": [{k: s[k] for k in ("name", "name-zh", "description", "description-zh", "category", "version", "license", "page")} for s in own],
        "skills": (
            [{"name": s["name"], "name-zh": s.get("name-zh", s["name"]),
              "description": s["description"], "description-zh": s.get("description-zh", ""),
              "category": s.get("category", ""), "kind": "own",
              "page": "/" + s["page"], "install": f"GITHUB_TOKEN=<PAT> npx skills add JacksenHu/skill-x --skill {s['name']}"}
             for s in own]
            + [{"name": x["name"], "name-zh": x.get("name-zh", x["name"]),
                "description": x["description"], "description-zh": x.get("description-zh", ""),
                "category": x.get("category", ""), "kind": "ext", "suite": st["namespace"],
                "page": f"/skills/ext-{ns_slug(st['namespace'])}--{x['name']}.html",
                "install": f"npx skills add {st['namespace']} --skill {x['name']}"}
               for st in suites for x in st["skills"]]
        ),
        "suites": [{"namespace": s["namespace"], "upstream": s["upstream"], "license": s["license"]["spdx"],
                    "total": s.get("totalSkills", len(s["skills"])),
                    "stats": s.get("stats", {}),
                    "skills": [{"name": x["name"], "name-zh": x.get("name-zh"), "description": x["description"],
                                "description-zh": x.get("description-zh"), "category": x.get("category")} for x in s["skills"]]}
                    for s in suites],
    }
    # MCP 市场面:只放出人工审查通过的条目,绝不含用户密钥/认证头
    mcp_reg = ROOT / "mcp-registry.json"
    mcps = []
    if mcp_reg.is_file():
        for s in json.loads(mcp_reg.read_text(encoding="utf-8")).get("servers", []):
            cur = (s.get("_meta") or {}).get("top.skillx/curated") or {}
            if (cur.get("reviewed") or {}).get("execReview") != "passed":
                continue
            mcps.append({
                "name": s.get("name"), "title": s.get("title") or s.get("name"),
                "description": s.get("description"), "description-zh": cur.get("description-zh", ""),
                "version": s.get("version"), "kind": cur.get("kind"),
                "category": cur.get("category"), "riskLevel": cur.get("riskLevel"),
                "installHint": cur.get("installHint", ""),
                "remotes": [{"type": r.get("type"), "url": r.get("url")} for r in (s.get("remotes") or [])],
                "packages": [{"registryType": p.get("registryType"), "identifier": p.get("identifier"), "version": p.get("version")} for p in (s.get("packages") or [])],
            })
    site_data["mcps"] = mcps
    (DIST / "site-data.json").write_text(json.dumps(site_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 机器可读数据接口:工具清单 + 审计报告(供外部程序调用,nginx 静态提供)
    tools_data = {"generatedAt": time.strftime("%Y-%m-%d"), "version": TEMPLATE_VERSION, "tools": {
        name: [{"script": e["script"], "summary": e["summary"], "summary-zh": e.get("summary-zh"),
                "args": [{"flags": f, "help": h} for f, h in e["args"]]} for e in entries]
        for name, entries in tool_docs.items()}}
    (DIST / "tools.json").write_text(json.dumps(tools_data, ensure_ascii=False, indent=2), encoding="utf-8")
    if AUDIT_PATH.is_file():
        (DIST / "audit-report.json").write_text(AUDIT_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    MANIFEST.write_text(json.dumps(new_manifest, indent=1), encoding="utf-8")
    print(f"[+] 产物 {len(pages)} 页 + 2 assets + {mmap_count} 导图 -> {DIST}(写入 {written},跳过 {skipped},清理 {removed};自研 {len(own)},套件 {len(suites)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
