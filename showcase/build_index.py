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
from svg_map import parse_map, render_svg, mmap_html  # noqa: E402
import apidocs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
EXTERNAL = ROOT / "external.json"
PACKS = ROOT / "packs.json"
I18N_EXT = Path(__file__).resolve().parent / "i18n-ext.json"
I18N_PACKS = Path(__file__).resolve().parent / "i18n-packs.json"
CURATION = Path(__file__).resolve().parent / "curation.json"
STAR_CACHE = Path(__file__).resolve().parent / ".upstream-cache.json"
DIST = Path(__file__).resolve().parent / "dist"
MANIFEST = Path(__file__).resolve().parent / ".build-manifest.json"
TEMPLATE_VERSION = "3.2"

sys.path.insert(0, str(ROOT / "scripts"))
from resolve_members import load_index, resolve_pack  # noqa: E402

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
/*
SKILL X · Instrument Console — v4 design system
register=brand · palette=ink/amber-signal · type=display/sans/mono
signature=signal-bars · glow-lift cards · scroll-driven rail
zero inline style/script · strict CSP · zero third-party deps
*/
:root{
  --bg:#06080C; --surface:#0D1219; --surface2:#131A23; --surface3:#1A232F;
  --line:#1A2330; --line2:#2A3747; --line3:#394A5D;
  --text:#EDF2F8; --text2:#97A4B6; --text3:#5D6A7C;
  --accent:#FF6B2C; --accent2:#FFA25C; --accent-deep:#E8551C;
  --signal:#54A8FF;
  --ok:#34D399; --warn:#FBBF24; --danger:#F87171;
  --c-reverse-engineering:#FF6B2C; --c-pentest:#FF5B6E; --c-malware:#B06BFF; --c-forensics:#2AD4C9;
  --c-engineering-hygiene:#54A8FF; --c-dev-workflow:#8B98A9; --c-web-frontend:#34D399; --c-data:#FBBF24;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --mono:ui-monospace,SFMono-Regular,"JetBrains Mono","Cascadia Code",Consolas,monospace;
  --r-sm:4px; --r-md:8px; --r-lg:12px;
  --shadow-card:0 1px 0 rgba(255,255,255,.03) inset,0 12px 34px rgba(0,0,0,.42);
  --shadow-float:0 18px 46px rgba(0,0,0,.5),0 0 0 1px rgba(255,107,44,.16),0 0 32px rgba(255,107,44,.12);
  --ease:cubic-bezier(.22,.7,.3,1);
}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;overflow-x:clip}
body{
  font-family:var(--sans);color:var(--text);line-height:1.7;font-size:15px;
  background:
    radial-gradient(1100px 520px at 82% -8%, rgba(255,107,44,.07), transparent 60%),
    radial-gradient(900px 460px at -8% 12%, rgba(84,168,255,.055), transparent 55%),
    var(--bg);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;overflow-x:clip;
  min-height:100vh;
}
a{color:var(--signal);text-decoration:none}
a:hover{text-decoration:none}
::selection{background:var(--accent);color:#150a04}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:2px}

.wrap{max-width:1120px;margin:0 auto;padding:0 24px 88px}
h1{font-size:32px;line-height:1.16;letter-spacing:-.025em;font-weight:750}
h2{font-size:22px;font-weight:720;letter-spacing:-.015em;margin:64px 0 18px;padding-bottom:13px;border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:11px}
h2 .n{font-family:var(--mono);font-size:12px;color:var(--text3);font-weight:500;letter-spacing:.02em}
.h2-sm{font-size:15px;margin-top:28px;border:0;padding:0}
p{max-width:76ch}

/* ---------- 顶栏 ---------- */
.topnav{
  position:sticky;top:0;z-index:40;
  background:rgba(6,8,12,.78);backdrop-filter:blur(14px) saturate(140%);
  border-bottom:1px solid var(--line);
  display:flex;align-items:center;gap:2px;padding:0 24px;height:56px;
}
.topnav .brand{font-family:var(--mono);font-weight:700;font-size:14.5px;margin-right:22px;color:var(--text);letter-spacing:.01em;display:flex;align-items:center;gap:9px}
.topnav .brand i{width:9px;height:9px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:inline-block;border-radius:2px;box-shadow:0 0 10px rgba(255,107,44,.7);transform:rotate(45deg)}
.topnav .brand b{font-weight:800;color:var(--accent);letter-spacing:-.02em}
.topnav a.nav{color:var(--text2);padding:18px 12px;font-size:13.5px;border-bottom:2px solid transparent;transition:color .18s var(--ease);position:relative}
.topnav a.nav:hover{color:var(--text)}
.topnav a.nav.active{color:var(--text);border-bottom-color:var(--accent)}
.lang-btn{margin-left:auto;font-family:var(--mono);font-size:11.5px;background:none;border:1px solid var(--line2);border-radius:4px;padding:5px 11px;color:var(--text2);cursor:pointer;transition:border-color .18s,color .18s,background .18s}
.lang-btn:hover{border-color:var(--accent);color:var(--accent);background:rgba(255,107,44,.06)}

/* ---------- 内页 hero ---------- */
.hero{position:relative;border-bottom:1px solid var(--line);padding:52px 0 40px;margin-bottom:8px;overflow:hidden}
.hero:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.024) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.024) 1px,transparent 1px);background-size:46px 46px;mask-image:linear-gradient(180deg,#000,transparent 94%);pointer-events:none}
.hero:after{content:"";position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,transparent,var(--accent),transparent);opacity:.8;animation:scanline 7s linear infinite}
@keyframes scanline{0%{transform:translateY(0);opacity:0}8%{opacity:.9}92%{opacity:.9}100%{transform:translateY(360px);opacity:0}}
.hero>*{position:relative}
.hero .eyebrow{font-family:var(--mono);font-size:12px;color:var(--accent);letter-spacing:.1em}
.hero h1{font-size:44px;margin-top:14px;max-width:24ch}
.hero h1 em{font-style:normal;color:var(--accent)}
.hero .lede{font-size:15.5px;color:var(--text2);margin-top:15px;max-width:62ch}
.hero .stats{display:flex;gap:38px;margin-top:28px}
.hero .stats b{font-family:var(--mono);font-size:32px;font-weight:600;display:block;line-height:1;color:var(--text);letter-spacing:-.02em}
.hero .stats b.accent{color:var(--accent)}
.hero .stats span{font-size:12px;color:var(--text3)}

/* ---------- 搜索 / 筛选 ---------- */
.finder{margin-top:28px;max-width:660px;position:relative}
.finder textarea,.search input{width:100%;padding:15px 17px;background:var(--surface);border:1px solid var(--line2);border-radius:var(--r-md);font:14.5px/1.6 var(--sans);color:var(--text);transition:border-color .2s,box-shadow .2s}
.finder textarea::placeholder,.search input::placeholder{color:var(--text3)}
.finder textarea:focus,.search input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,107,44,.15),0 10px 30px rgba(0,0,0,.25)}
.finder textarea{resize:vertical;min-height:86px}
.finder .act{margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.search{margin:0 0 6px;max-width:560px}
.search input{padding:12px 15px;font-size:14px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 6px}
.chip{font-size:12.5px;padding:7px 14px;border:1px solid var(--line2);border-radius:6px;background:var(--surface);cursor:pointer;color:var(--text2);transition:all .18s var(--ease)}
.chip:hover{border-color:var(--accent);color:var(--accent);transform:translateY(-1px)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#150a04;font-weight:650;box-shadow:0 6px 18px rgba(255,107,44,.28)}

/* ---------- 按钮 ---------- */
.btn{font:inherit;font-size:14px;padding:11px 24px;border:1px solid var(--accent);background:linear-gradient(135deg,var(--accent),var(--accent-deep));color:#170a03;border-radius:var(--r-md);cursor:pointer;font-weight:650;position:relative;overflow:hidden;transition:transform .14s var(--ease),box-shadow .2s var(--ease),filter .2s;box-shadow:0 8px 20px rgba(255,107,44,.24)}
.btn:hover{filter:brightness(1.06);transform:translateY(-1px);box-shadow:0 12px 28px rgba(255,107,44,.34)}
.btn:active{transform:translateY(0)}
.btn:after{content:"";position:absolute;top:0;bottom:0;left:-60%;width:40%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.35),transparent);transform:skewX(-20deg);transition:left .5s var(--ease)}
.btn:hover:after{left:120%}
.btn.ghost{background:transparent;color:var(--text2);border-color:var(--line2);font-weight:500;box-shadow:none}
.btn.ghost:hover{border-color:var(--accent);color:var(--accent);box-shadow:0 0 0 1px rgba(255,107,44,.2) inset}
.finder .hint{font-size:12px;color:var(--text3)}

/* ---------- 推荐结果 ---------- */
.recs{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-top:18px}
.rec{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--cat,var(--accent));border-radius:var(--r-md);padding:16px 18px;animation:pop .36s var(--ease) backwards}
@keyframes pop{from{opacity:0;transform:translateY(12px) scale(.985)}to{opacity:1;transform:none}}
.rec .t{font-size:15px;font-weight:650}
.rec .t a{color:var(--text)}
.rec .id{font-family:var(--mono);font-size:11.5px;color:var(--text3);margin-top:3px;word-break:break-all}
.rec .d{font-size:13px;color:var(--text2);margin-top:8px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.rec .why{font-family:var(--mono);font-size:11px;color:var(--accent);margin-top:9px}

/* ---------- 卡片网格 ---------- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin-top:6px}
.grid.grid-mt{margin-top:18px}
.card{
  position:relative;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);
  padding:20px 21px 18px;overflow:hidden;
  box-shadow:var(--shadow-card);
  transition:border-color .22s var(--ease),background .22s var(--ease),transform .22s var(--ease),box-shadow .22s var(--ease);
  animation:pop .44s var(--ease) backwards;
}
.card:before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--cat,var(--accent));opacity:.85;transition:width .22s var(--ease),opacity .22s}
.card:after{content:"";position:absolute;inset:0;border-radius:var(--r-md);background:linear-gradient(135deg,rgba(255,255,255,.05),transparent 42%);pointer-events:none;opacity:0;transition:opacity .22s}
.card:hover{border-color:var(--line3);background:var(--surface2);transform:translateY(-4px);box-shadow:var(--shadow-float)}
.card:hover:before{width:5px;opacity:1}
.card:hover:after{opacity:1}
.card h3{font-size:16.5px;font-weight:680;letter-spacing:-.01em}
.card h3 a{color:var(--text)}
.card h3 a:hover{color:var(--accent)}
.card .en-name{font-family:var(--mono);font-size:11.5px;color:var(--text3);margin-top:4px;word-break:break-all}
.card p{font-size:13.5px;color:var(--text2);margin-top:10px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card .meta{display:flex;align-items:center;gap:8px;margin-top:14px;flex-wrap:wrap}

/* 分类色 */
.cat-reverse-engineering{--cat:var(--c-reverse-engineering)}
.cat-pentest{--cat:var(--c-pentest)}
.cat-malware{--cat:var(--c-malware)}
.cat-forensics{--cat:var(--c-forensics)}
.cat-engineering-hygiene{--cat:var(--c-engineering-hygiene)}
.cat-dev-workflow{--cat:var(--c-dev-workflow)}
.cat-web-frontend{--cat:var(--c-web-frontend)}
.cat-data{--cat:var(--c-data)}

/* ---------- 标签 / 徽标 ---------- */
.tag{font-family:var(--mono);font-size:11px;padding:3px 8px;border:1px solid var(--line2);border-radius:5px;color:var(--text2);white-space:nowrap}
.tag.cat{border-color:var(--cat,var(--line2));color:var(--cat,var(--text2));background:color-mix(in srgb,var(--cat,var(--line2)) 10%,transparent)}
.tag.kind-own{border-color:var(--accent);color:var(--accent);background:rgba(255,107,44,.08)}
.tag.kind-ext{border-color:var(--line2);color:var(--text2)}
.tag.kind-mcp{border-color:var(--signal);color:var(--signal);background:rgba(84,168,255,.08)}
.tag.kind-preview{border-color:var(--line2);color:var(--text3);border-style:dashed}
.tag.risk-low{border-color:#34d399;color:#34d399}
.tag.risk-medium{border-color:var(--warn);color:var(--warn)}
.tag.risk-high,.tag.risk-critical{border-color:var(--danger);color:var(--danger)}
.tag.ok{border-color:#34d399;color:#34d399;background:rgba(52,211,153,.08)}
.tag.warn{border-color:var(--warn);color:var(--warn);background:color-mix(in srgb,var(--warn) 10%,transparent)}
.tag.danger{border-color:var(--danger);color:var(--danger);background:color-mix(in srgb,var(--danger) 10%,transparent)}
.tag.dim{color:var(--text3);border-style:dashed}
.count{font-family:var(--mono);font-size:12px;color:var(--text3);white-space:nowrap}
.count.hit{color:var(--accent)}
.badge{font-family:var(--mono);font-size:11px;padding:3px 9px;border:1px solid var(--line2);border-radius:5px;color:var(--text2);white-space:nowrap}
.badge.auth{border-color:var(--accent);color:var(--accent);background:rgba(255,107,44,.08)}
.badge.ext{border-color:var(--line2);color:var(--text2)}
.badge.cat{border-color:var(--cat,var(--line2));color:var(--cat,var(--text2))}

/* ---------- 专家团 ---------- */
.avatar{width:54px;height:54px;border:1px solid var(--line2);border-radius:var(--r-md);background:var(--bg);flex:none;display:block}
.avatar.xl{width:108px;height:108px;border-radius:var(--r-lg)}
.pack-card .pack-head{display:flex;gap:13px;align-items:flex-start}
.pack-card .pack-head h3{font-size:17px}
.pack-card .role{font-size:12.5px;color:var(--accent);margin-top:9px}
.pack-card p{margin-top:8px}
.persona-hero{display:flex;gap:24px;align-items:flex-start}
.persona-hero .persona-body{min-width:0;flex:1}
.persona-role{font-size:13.5px;color:var(--accent);margin-top:10px}
.persona-tagline{font-size:15.5px;color:var(--text);margin-top:9px}
.member-card .cmd{margin-bottom:10px}
.member-missing{border-color:var(--warn)}

/* ---------- 卡片头部 ---------- */
.card-head{display:flex;align-items:center;gap:11px;flex-wrap:wrap}
.card-head h1,.card-head h3{margin:0}

/* ---------- 详情页 ---------- */
.detail{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);padding:30px 32px;margin-top:18px;box-shadow:var(--shadow-card)}
.detail h1{font-size:28px}
.detail .en-name{font-family:var(--mono);font-size:13px;color:var(--text3);margin-top:7px}
.detail .desc{margin:18px 0;color:var(--text);font-size:15px;white-space:pre-wrap}
.kv{display:grid;grid-template-columns:150px 1fr;gap:11px 18px;font-size:13.5px;margin:22px 0;padding:18px;background:var(--bg);border:1px solid var(--line);border-radius:var(--r-md)}
.kv dt{color:var(--text3)}
.kv dd{font-family:var(--mono);word-break:break-all;color:var(--text)}
.kv a{color:var(--signal)}

/* ---------- 命令块 ---------- */
.cmd{position:relative;background:#05070A;border:1px solid var(--line);border-left:3px solid var(--accent);padding:14px 16px;border-radius:var(--r-md);font:13px/1.6 var(--mono);color:#EDF2F8;overflow-x:auto;margin:13px 0;white-space:pre;user-select:all}
.cmd:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,107,44,.05),transparent 60%);pointer-events:none}

/* ---------- 审计折叠 ---------- */
details.audit{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);margin-top:18px}
details.audit>summary{cursor:pointer;padding:15px 17px;display:flex;align-items:center;gap:10px;font-size:14px;list-style:none;border-left:3px solid transparent;transition:border-color .18s,background .18s}
details.audit>summary::-webkit-details-marker{display:none}
details.audit>summary:hover{background:var(--surface2)}
details.audit[open]>summary{border-left-color:var(--accent);border-bottom:1px solid var(--line)}
.grade{font-family:var(--mono);font-weight:700;font-size:13px;padding:3px 10px;border-radius:5px}
.grade-A{background:rgba(52,211,153,.14);color:var(--ok)}
.grade-A-{background:rgba(163,217,60,.14);color:#A5D63C}
.grade-B{background:rgba(251,191,36,.14);color:var(--warn)}
.grade-C{background:rgba(255,107,44,.14);color:var(--accent)}
.grade-D{background:rgba(248,113,113,.14);color:var(--danger)}
.audit-meta{font-size:11.5px;color:var(--text3);margin-left:auto;font-family:var(--mono)}
.audit-body{padding:6px 17px 17px}
.lvl{font-family:var(--mono);font-size:11px;padding:2px 8px;border-radius:4px;white-space:nowrap}
.lvl-info{background:rgba(151,164,182,.12);color:var(--text2)}
.lvl-low{background:rgba(163,217,60,.14);color:#A5D63C}
.lvl-medium{background:rgba(251,191,36,.14);color:var(--warn)}
.lvl-high{background:rgba(255,107,44,.14);color:var(--accent)}
.lvl-critical{background:rgba(248,113,113,.14);color:var(--danger)}
.audit-detail{font-size:12.5px;color:var(--text2);word-break:break-word;max-width:440px}

/* ---------- API 表格 ---------- */
table.api{width:100%;border-collapse:collapse;font-size:13px;margin:15px 0;background:var(--surface);border-radius:var(--r-md);overflow:hidden}
table.api th,table.api td{border:1px solid var(--line);padding:10px 13px;text-align:left;vertical-align:top}
table.api th{background:var(--bg);font-weight:600;color:var(--text2)}
code.inl{font-family:var(--mono);font-size:12px;background:var(--surface2);padding:2px 6px;border-radius:4px;color:var(--text)}

/* ---------- 思维导图 ---------- */
.mmap{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);margin-top:18px;padding:16px;overflow-x:auto}
.mmap svg{max-width:100%;height:auto;display:block;margin:0 auto}
.mmap svg .bg{fill:transparent}
.mmap svg rect{fill:var(--surface2);stroke:var(--line2);transition:fill .18s,stroke .18s}
.mmap svg rect.root{fill:rgba(255,107,44,.12);stroke:var(--accent)}
.mmap svg text{fill:var(--text);font-size:13px}
.mmap svg path{stroke-dasharray:400;stroke-dashoffset:400;animation:draw 1.1s ease-out forwards}
@keyframes draw{to{stroke-dashoffset:0}}
.mmap svg g.node:hover rect{fill:var(--accent);stroke:var(--accent)}
.mmap svg g.node:hover text{fill:#150a04}

/* ---------- 套件 ---------- */
.suite{margin-bottom:34px}
.suite h3{font-family:var(--mono);font-size:15px;font-weight:600;margin-bottom:12px;color:var(--text)}
.suite-meta{font-family:var(--sans);font-size:12.5px;color:var(--text3);font-weight:400}
.suite-meta a{color:var(--signal)}
.notice{background:rgba(255,107,44,.08);border:1px solid rgba(255,107,44,.32);border-radius:var(--r-md);padding:14px 17px;font-size:13px;color:var(--accent2);margin-top:15px}
.hint-warn{font-size:13px;color:var(--accent2);margin-top:15px}
.hint-ok{font-size:13px;color:var(--ok);margin-top:15px}
.hint-dim{font-size:13px;color:var(--text3);margin-top:11px;max-width:76ch}
.empty{color:var(--text3);font-size:14px;padding:30px 4px}
.hidden{display:none!important}

/* ---------- 页脚 ---------- */
footer{text-align:left;font-size:12.5px;color:var(--text3);padding:26px 24px 44px;border-top:1px solid var(--line);margin-top:52px;background:rgba(6,8,12,.5)}
footer a{color:var(--signal)}

/* ============================================================
   首页(品牌面)
   ============================================================ */
.home-hero{position:relative;margin-left:calc(50% - 50vw);margin-right:calc(50% - 50vw);border-bottom:1px solid var(--line);overflow:hidden;background:#06080C;min-height:min(80vh,700px);display:flex;align-items:center}
.home-hero-bg{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);background-size:50px 50px;-webkit-mask-image:radial-gradient(circle at 74% 44%,#000 20%,transparent 80%);mask-image:radial-gradient(circle at 74% 44%,#000 20%,transparent 80%)}
.home-hero-video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center;opacity:.92}
.home-hero-scrim{position:absolute;inset:0;background:radial-gradient(circle at 76% 40%,rgba(255,107,44,.2),transparent 56%),linear-gradient(90deg,rgba(6,8,12,.97) 0%,rgba(6,8,12,.9) 42%,rgba(6,8,12,.46) 100%)}
.home-hero-inner{position:relative;width:100%;max-width:1120px;margin:0 auto;padding:96px 24px 76px}
.home-hero .eyebrow{font-family:var(--mono);font-size:12px;color:var(--accent);letter-spacing:.12em}
.home-hero h1{font-size:clamp(52px,8vw,88px);line-height:.98;margin-top:18px;letter-spacing:-.03em;font-weight:780}
.home-hero h1 em{font-style:normal;color:var(--accent)}
.home-offer{font-size:clamp(20px,2.7vw,28px);font-weight:620;margin-top:20px;max-width:22ch;letter-spacing:-.01em}
.home-lede{font-size:15.5px;color:var(--text2);margin-top:16px;max-width:56ch}
.home-cta{display:flex;gap:11px;flex-wrap:wrap;margin-top:30px}
.home-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;margin-top:42px;background:var(--line);border:1px solid var(--line);max-width:680px;border-radius:var(--r-md);overflow:hidden}
.home-stats div{background:rgba(13,18,25,.72);padding:15px 16px}
.home-stats dt{font-size:12px;color:var(--text3)}
.home-stats dd{font-family:var(--mono);font-size:24px;margin-top:5px;line-height:1.15;letter-spacing:-.02em}
.home-stats dd .accent{color:var(--accent)}

/* ---------- 一体化工作台 ---------- */
.bench,.home-featured,.home-mcp{margin-top:52px}
.bench{display:grid;grid-template-columns:minmax(0,272px) minmax(0,1fr);gap:34px;align-items:start}
.bench-rail{display:flex;flex-direction:column;position:relative}
.bench-rail:before{content:"";position:absolute;left:0;top:0;bottom:0;width:1px;background:var(--line)}
.step{appearance:none;background:none;border:0;border-left:1px solid var(--line);color:var(--text2);cursor:pointer;font:inherit;text-align:left;display:flex;flex-direction:column;justify-content:center;gap:8px;min-height:54vh;padding:24px 0 24px 22px;position:relative;transition:color .22s}
.step:before{content:"";position:absolute;left:-1px;top:50%;width:2px;height:0;background:linear-gradient(180deg,var(--accent),var(--accent2));transition:height .3s var(--ease);border-radius:1px}
.step.on{color:var(--text)}
.step.on:before{height:60px;margin-top:-30px;box-shadow:0 0 14px rgba(255,107,44,.6)}
.step:focus{outline:none}
.step:focus-visible{outline:2px solid rgba(255,107,44,.42);outline-offset:2px;border-radius:5px}
.step i{font-family:var(--mono);font-size:11.5px;letter-spacing:.1em;color:var(--text3)}
.step.on i{color:var(--accent)}
.step b{font-size:19px;font-weight:680;line-height:1.3;letter-spacing:-.01em}
.step span{font-size:13px;color:var(--text3);max-width:26ch}
.step:hover b{color:var(--accent)}
.bench-stage{position:sticky;top:84px}
.console{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);overflow:hidden;box-shadow:0 30px 70px rgba(0,0,0,.44)}
.console:before{content:"";position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,transparent,var(--accent),transparent);opacity:.25;animation:beamPulse 5.5s ease-in-out infinite;pointer-events:none}
@keyframes beamPulse{0%,100%{opacity:.16}50%{opacity:.8}}
.console-bar{display:flex;align-items:center;gap:13px;padding:11px 15px;border-bottom:1px solid var(--line);background:var(--bg)}
.dots{display:flex;align-items:flex-end;gap:3px;height:11px}
.dots i{width:3px;background:var(--accent);border-radius:1px}
.dots i:first-child{height:5px;opacity:.55}
.dots i:nth-child(2){height:8px;opacity:.78}
.dots i:nth-child(3){height:11px;opacity:1;box-shadow:0 0 7px rgba(255,107,44,.8)}
.console-path{font-family:var(--mono);font-size:11.5px;color:var(--text3)}
.console-live{margin-left:auto;font-family:var(--mono);font-size:10.5px;color:var(--ok);border:1px solid rgba(52,211,153,.4);border-radius:4px;padding:2px 8px;letter-spacing:.06em}
.console-body{min-height:392px;padding:24px 26px}
.panel{display:none}
.panel.on{display:block;animation:panelIn .38s var(--ease) both}
@keyframes panelIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.console-foot{padding:11px 15px;border-top:1px solid var(--line);background:var(--bg);font-family:var(--mono);font-size:11.5px;color:var(--text3)}
.panel .finder{margin-top:0}
.panel .mmap{margin-top:0;border:1px solid var(--line);background:var(--bg);max-height:560px;overflow:auto}
.panel .audit{margin-top:0}
.demo-tabs{display:flex;gap:8px;flex-wrap:wrap}
.tab{font-family:inherit;font-size:12.5px;padding:7px 14px;border:1px solid var(--line2);border-radius:6px;background:transparent;cursor:pointer;color:var(--text2);transition:all .16s var(--ease)}
.tab:hover{border-color:var(--accent);color:var(--accent)}
.tab.on{background:var(--accent);border-color:var(--accent);color:#150a04;font-weight:650;box-shadow:0 6px 16px rgba(255,107,44,.26)}
.demo-snippet{margin:13px 0 0;max-height:280px;overflow:auto}
.demo-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:13px}

/* ---------- 首页 MCP 入口 ---------- */
.home-mcp-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-top:16px}
.home-mcp-item{display:block;background:var(--surface);border:1px solid var(--line);border-left:2px solid var(--accent);border-radius:var(--r-md);padding:16px 18px;transition:border-color .2s,background .2s,transform .2s,box-shadow .2s}
.home-mcp-item:hover{border-color:var(--line3);background:var(--surface2);transform:translateY(-2px);box-shadow:var(--shadow-float)}
.home-mcp-item .t{font-size:15px;font-weight:650;color:var(--text)}
.home-mcp-item .id{font-family:var(--mono);font-size:11.5px;color:var(--text3);margin-top:4px;word-break:break-all}
.home-mcp-item .meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:11px}
.home-more{margin-top:16px}
.home-trust{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);margin-top:38px;border-radius:var(--r-md);overflow:hidden}
.trust-item{background:var(--surface);padding:20px}
.trust-item b{display:block;font-size:14.5px}
.trust-item span{display:block;font-size:13px;color:var(--text2);margin-top:8px}
.home-cta-band{margin-top:40px;border-top:1px solid var(--line);padding-top:30px}

/* ---------- Markdown 内容 ---------- */
.md-body{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-md);padding:24px 28px;margin-top:14px}
.md-body h2{font-size:16px;margin:26px 0 11px;padding-bottom:9px;border-bottom:1px solid var(--line);display:block}
.md-body h2:first-child{margin-top:0}
.md-body h3{font-size:14.5px;margin:19px 0 9px;color:var(--text)}
.md-body p{font-size:13.5px;color:var(--text2);margin:9px 0;max-width:82ch}
.md-body ul,.md-body ol{margin:9px 0 9px 22px;font-size:13.5px;color:var(--text2)}
.md-body li{margin:5px 0}
.md-body code{font-family:var(--mono);font-size:12px;background:var(--surface2);padding:2px 6px;border-radius:4px;color:var(--text)}
.md-body pre{background:#05070A;border:1px solid var(--line);border-left:3px solid var(--accent);padding:13px 15px;border-radius:var(--r-md);overflow-x:auto;margin:13px 0}
.md-body pre code{background:none;padding:0;font-size:12.5px}
.md-body blockquote{border-left:3px solid var(--line2);padding-left:13px;color:var(--text3);margin:11px 0}
.md-body a{color:var(--signal)}
.md-body strong{color:var(--text)}

/* ---------- 滚动动效(R2 原生 scroll-driven,降级由 app.js) ---------- */
.scroll-progress{position:fixed;left:0;right:0;top:0;height:2px;z-index:60;background:linear-gradient(90deg,var(--accent),var(--signal));transform:scaleX(0);transform-origin:0 50%;pointer-events:none}
.reveal-armed{opacity:0;transform:translate3d(0,28px,0);transition:opacity .6s var(--ease),transform .6s var(--ease)}
.reveal-armed.reveal-in{opacity:1;transform:none}
@supports (animation-timeline: view()){
  @keyframes rail{from{transform:scaleX(0)}to{transform:scaleX(1)}}
  @keyframes riseIn{from{opacity:0;transform:translate3d(0,32px,0)}to{opacity:1;transform:none}}
  @keyframes slideIn{from{opacity:0;transform:translate3d(-28px,0,0)}to{opacity:1;transform:none}}
  @keyframes settleIn{from{opacity:0;transform:scale(.98)}to{opacity:1;transform:none}}
  @keyframes heroDrift{from{transform:translate3d(0,0,0) scale(1)}to{transform:translate3d(0,56px,0) scale(1.07)}}
  @keyframes heroVeil{from{opacity:1}to{opacity:.4}}
  .scroll-progress{animation:rail linear both;animation-timeline:scroll(root block)}
  .home-hero-video{animation:heroDrift linear both;animation-timeline:scroll(root block);animation-range:0 72vh}
  .home-hero-inner{animation:heroVeil linear both;animation-timeline:scroll(root block);animation-range:0 64vh}
  .reveal{animation:riseIn linear both;animation-timeline:view();animation-range:entry 12% cover 36%}
  .reveal-left{animation-name:slideIn}
  .reveal-scale{animation-name:settleIn}
  .home-trust .reveal:nth-child(2){animation-range:entry 18% cover 42%}
  .home-trust .reveal:nth-child(3){animation-range:entry 24% cover 48%}
  .home-featured>h2,.home-mcp>h2{position:relative}
  .home-featured>h2:after,.home-mcp>h2:after{content:"";position:absolute;left:0;bottom:-1px;width:140px;height:2px;background:linear-gradient(90deg,var(--accent),transparent);transform:scaleX(0);transform-origin:0 50%;animation:rail linear both;animation-timeline:view();animation-range:entry 8% cover 30%}
}

@media print{.reveal,.reveal-armed{opacity:1!important;transform:none!important;animation:none!important}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.mmap svg path{stroke-dashoffset:0}.home-hero-video{display:none}}

/* ---------- 响应式 ---------- */
@media (max-width:1024px){
  .bench{grid-template-columns:minmax(0,224px) minmax(0,1fr);gap:26px}
  .home-hero h1{font-size:clamp(46px,6.4vw,66px)}
  .wrap{padding:0 20px 72px}
}
@media (max-width:760px){
  body{font-size:15.5px}
  .topnav{height:auto;padding:8px 14px;overflow-x:auto;scrollbar-width:none}
  .topnav::-webkit-scrollbar{display:none}
  .topnav .brand{margin-right:14px;font-size:13.5px}
  .topnav a.nav{padding:9px 10px;font-size:13px;white-space:nowrap}
  .wrap{padding:0 16px 56px}
  .home-hero{min-height:auto}
  .home-hero-inner{padding:58px 16px 48px}
  .home-hero-video{width:100%;opacity:.4}
  .home-hero-scrim{background:radial-gradient(circle at 50% 24%,rgba(255,107,44,.22),transparent 62%),linear-gradient(180deg,rgba(6,8,12,.95) 0%,rgba(6,8,12,.88) 100%)}
  .home-offer{max-width:none}
  .home-stats{grid-template-columns:repeat(2,minmax(0,1fr));max-width:none}
  .bench{display:block;margin-top:34px}
  .bench-rail{flex-direction:row;gap:8px;overflow-x:auto;position:sticky;top:56px;z-index:6;background:var(--bg);padding:7px 0;scrollbar-width:none}
  .bench-rail::-webkit-scrollbar{display:none}
  .bench-rail:before{display:none}
  .step{flex:0 0 auto;min-height:auto;border:1px solid var(--line);border-left:1px solid var(--line);padding:10px 13px;white-space:nowrap;gap:0;border-radius:7px}
  .step i,.step span{display:none}
  .step b{font-size:13.5px}
  .step.on{border-color:var(--accent);background:rgba(255,107,44,.08)}
  .step.on:before{display:none}
  .bench-stage{position:static;margin-top:14px}
  .console-body{padding:16px;min-height:0}
  .home-trust{grid-template-columns:1fr}
  .hero{padding:30px 0 26px}
  .hero h1{font-size:32px}
  .hero .lede{font-size:14.5px}
  .hero .stats{gap:24px;margin-top:22px}
  .hero .stats b{font-size:26px}
  .finder textarea{min-height:72px;font-size:14px}
  .grid{grid-template-columns:1fr}
  .recs{grid-template-columns:1fr}
  .detail{padding:20px 17px}
  .persona-hero{flex-direction:column;gap:15px}
  .avatar.xl{width:90px;height:90px}
  .md-body{padding:18px 15px}
  .kv{grid-template-columns:1fr;gap:4px}
  .cmd{font-size:12px;padding:12px 13px}
  table.api{display:block;overflow-x:auto;white-space:nowrap}
  .audit-detail{max-width:none;white-space:normal}
  .mmap{padding:9px}
  .btn{padding:12px 18px;width:100%;text-align:center}
  .finder .act .btn{width:auto}
  footer{padding:20px 16px 36px}
}
@media (max-width:400px){
  .home-hero h1{font-size:40px}
  .home-stats dd{font-size:20px}
  .console-body{padding:14px}
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
      const kind = r.kind === 'own' ? '<span class="badge auth">自研·需授权</span>' : (r.kind === 'pack' ? '<span class="badge auth">专家团</span>' : '<span class="badge ext">社区精选</span>');
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
        if meta.get("package_type") == "meta-skill":
            continue  # 专家团编排技能(meta-skill)走 collect_packs(),不作为普通技能展示
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
            "entryType": cur.get("entryType", "mcp"),
            "kind": cur.get("kind", "remote" if remotes else "local"),
            "category": cur.get("category", "dev-workflow"),
            "riskLevel": cur.get("riskLevel", "medium"),
            "installHint": cur.get("installHint", ""),
            "install": cur.get("install") or {},
            "remote_url": remotes[0].get("url", "") if remotes else "",
            "remote_type": remotes[0].get("type", "") if remotes else "",
            "pkg_id": f"{pkgs[0].get('registryType')}:{pkgs[0].get('identifier')}" if pkgs else "",
            "websiteUrl": s.get("websiteUrl", ""),
            "repository": (s.get("repository") or {}).get("url", ""),
            "riskNote": cur.get("riskNote", ""),
            "reviewed": cur.get("reviewed") or {},
            "upstreamStatus": cur.get("upstreamStatus") or {},
            "archived": bool(cur.get("archived")),
            "upstreamNote": cur.get("upstreamNote", ""),
            "remotes": remotes,
            "packages": pkgs,
            "tools": cur.get("tools") or [],
            "useCases": cur.get("useCases") or [],
            "tags": cur.get("tags") or [],
        })
    return out


def ns_slug(ns: str) -> str:
    return re.sub(r"[^\w.-]+", "--", ns)


def skill_slug(name: str) -> str:
    """技能页文件名用 slug：替换路径分隔符与非法字符，防止生成非法路径。"""
    bad = set('/:*?"<>|' + chr(92))
    out = "".join("-" if (c in bad or ord(c) < 32) else c for c in (name or ""))
    out = " ".join(out.split())
    return out.strip(" .") or "skill"


def mcp_slug(name: str) -> str:
    return re.sub(r"[^\w.-]+", "--", name)


def collect_packs():
    """读 packs.json,只返回人工审查通过的专家团;成员实时重解析(下架即降级)。"""
    if not PACKS.is_file():
        return []
    i18n = json.loads(I18N_PACKS.read_text(encoding="utf-8")) if I18N_PACKS.is_file() else {}
    table = i18n.get("packs", i18n)  # 兼容 {packs:{slug:{...}}} 与平铺 {slug:{...}} 两种形态
    index = load_index(ROOT)
    out = []
    for p in json.loads(PACKS.read_text(encoding="utf-8")).get("packs", []):
        rev = p.get("reviewed") or {}
        if rev.get("execReview") != "passed":
            continue
        extra = table.get(p.get("slug", "")) or {}
        res = resolve_pack(p, index)
        content = p.get("content", "")
        fresh = True
        src = p.get("source")
        if src and (ROOT / src).is_file():
            file_text = (ROOT / src).read_text(encoding="utf-8", errors="replace")
            fresh = file_text == content
            content = file_text
        persona = {**(p.get("persona") or {}), **(extra.get("persona") or {})}
        out.append({
            "slug": p.get("slug", ""),
            "displayName": extra.get("displayName", p.get("displayName", "")),
            "displayNameEn": extra.get("displayNameEn", p.get("displayNameEn", "")),
            "persona": persona,
            "summary": extra.get("summary", p.get("summary", "")),
            "summaryEn": extra.get("summaryEn", p.get("summaryEn", "")),
            "origin": p.get("origin", "own"),
            "skill": p.get("skill", ""),
            "install": p.get("install", ""),
            "upstream": p.get("upstream"),
            "license": (p.get("license") or {}).get("spdx", ""),
            "members": res["members"],
            "missingMembers": res["missing"],
            "degraded": res["degraded"],
            "content": content,
            "contentFresh": fresh,
            "reviewed": rev,
            "upstreamStatus": p.get("upstreamStatus") or {},
            "page": f"packages/{p.get('slug', '')}.html",
        })
    return out


def media_ver(rel: str) -> str:
    """静态媒体文件内容哈希(8 位),用于 URL 版本号破缓存。"""
    p = Path(__file__).resolve().parent / rel
    if not p.is_file():
        return ASSET_VER
    return hashlib.sha256(p.read_bytes()).hexdigest()[:8]


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
    return f'''<nav class="topnav" aria-label="主导航">
  <a class="brand" href="/">Skill <b>X</b></a>
  <a href="/"{cls("home")} data-zh="首页" data-en="Home">首页</a>
  <a href="/skills.html"{cls("skills")} data-zh="技能" data-en="Skills">技能</a>
  <a href="/packages.html"{cls("packs")} data-zh="专家团" data-en="Expert Packs">专家团</a>
  <a href="/mcp.html"{cls("mcp")} data-zh="MCP" data-en="MCP">MCP</a>
  <a href="/plugins.html"{cls("plugins")} data-zh="插件" data-en="Plugins">插件</a>
  <a href="/api.html"{cls("api")} data-zh="API" data-en="API">API</a>
  <a href="/about.html"{cls("about")} data-zh="关于" data-en="About">关于</a>
  <button class="lang-btn">EN</button>
</nav>'''


def page_shell(title, title_en, active, inner):
    full_title = title if title == "Skill X" else f"{title} · Skill X"
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full_title)}</title>
<link rel="stylesheet" href="/assets/style.css?v={ASSET_VER}">
</head><body>
<div class="scroll-progress" aria-hidden="true"></div>
{nav(active)}
<div class="wrap">{inner}</div>
<footer><a class="back" href="/">← <span data-zh="返回首页" data-en="Home">返回首页</span></a> · Skill X · Agent Skills 开放规范</footer>
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
  <div class="meta"><span class="tag cat">{esc(cat_label)}</span><span class="tag {kind_cls}">{kind_text}</span><span class="count" data-stat="{esc(stat_key)}"></span></div>
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
        items = "\n".join(card(s, "ext", f"skills/ext-{ns_slug(ns)}--{skill_slug(s['name'])}.html", f"{ns}/{s['name']}") for s in suite["skills"])
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
    stars = st.get("stars") or 0
    forks = st.get("forks") or 0
    total = suite.get("totalSkills", len(suite["skills"]))
    picked = len(suite["skills"])
    cards = "\n".join(card(s, "ext", f"skills/ext-{ns_slug(ns)}--{skill_slug(s['name'])}.html", f"{ns}/{s['name']}") for s in suite["skills"])
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
<tr><td><code class="inl">/api/plugin/install</code></td><td>POST</td><td data-zh="记录一次插件安装(仅 entryType=plugin 的过审条目)。Body: {{&quot;name&quot;:&quot;&lt;name&gt;&quot;}}" data-en="Record a plugin install (reviewed entryType=plugin entries only). Body: name">记录一次插件安装(仅 <code class="inl">entryType=plugin</code> 的过审条目)。Body: <code class="inl">{{"name":"&lt;name&gt;"}}</code></td></tr>
<tr><td><code class="inl">/plugins.html</code></td><td>GET</td><td data-zh="插件橱窗页(Agent 插件指路牌列表)" data-en="Plugins showcase page">插件橱窗页(Agent 插件指路牌列表)</td></tr>
<tr><td><code class="inl">/v0/packs</code></td><td>GET</td><td data-zh="专家团列表(游标分页 ?limit&cursor;只返回已过审条目;含人设/成员摘要/降级标记)" data-en="Expert pack list (cursor-paginated, reviewed entries only)">专家团列表(游标分页 <code class="inl">?limit&cursor</code>;只返回已过审条目;含人设 / 成员摘要 / 降级标记)</td></tr>
<tr><td><code class="inl">/v0/packs/&lt;slug&gt;</code></td><td>GET</td><td data-zh="专家团详情:完整人设 + 编排剧本正文 + 成员安装描述符数组(含安装命令与页面链接)" data-en="Expert pack detail: persona, orchestration script, member install descriptors">专家团详情:完整人设 + 编排剧本正文 + 成员安装描述符数组(含安装命令与页面链接)</td></tr>
<tr><td><code class="inl">/v0/packs/&lt;slug&gt;/install.md</code></td><td>GET</td><td data-zh="专家团专属安装契约(markdown;给 Agent 读的完整安装步骤)" data-en="Per-pack install contract (markdown, agent-readable)">专家团专属安装契约(markdown;给 Agent 读的完整安装步骤)</td></tr>
<tr><td><code class="inl">/install/pack-install.md</code></td><td>GET</td><td data-zh="全局安装契约文档(静态;提示词直接指向它即可让任意 Agent 完成安装)" data-en="Global install contract doc (static; point any agent at it)">全局安装契约文档(静态;提示词直接指向它即可让任意 Agent 完成安装)</td></tr>
<tr><td><code class="inl">/api/pack/install</code></td><td>POST</td><td data-zh="记录一次专家团安装。Body: {{&quot;slug&quot;:&quot;&lt;slug&gt;&quot;}}" data-en="Record an expert pack install. Body: slug">记录一次专家团安装。Body: <code class="inl">{{&quot;slug&quot;:&quot;&lt;slug&gt;&quot;}}</code></td></tr>
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
        cmd = m["installHint"] or (f"claude mcp add --transport http {m['name'].split('/')[-1]} {m['remote_url']}" if m["kind"] == "remote" else "")
        search = f"{m['name']} {m['title']} {m['description']} {m['description-zh']}".lower()
        cards.append(f'''<div class="card cat-{esc(m['category'])}" data-search="{esc(search)}" data-category="{esc(m['category'])}">
  <h3><a href="/mcp/{mcp_slug(m['name'])}.html">{esc(m['title'])}</a></h3>
  <div class="en-name">{esc(m['name'])}</div>
  <p><span data-zh="{esc(m['description-zh'])}" data-en="{esc(m['description'][:300])}">{esc(m['description-zh'])}</span></p>
  <div class="meta"><span class="tag cat">{esc(CATEGORIES.get(m['category'], m['category']))}</span><span class="tag kind-ext">{kind_text}</span><span class="tag risk-{esc(m['riskLevel'])}">{esc(risk_label.get(m['riskLevel'], m['riskLevel']))}</span><span class="count">v{esc(m['version'])}</span></div>
  <button class="chip on copy-btn" data-copy="{esc(cmd)}" data-skill="mcp:{esc(m['name'])}" data-zh="复制接入命令" data-en="Copy command">复制接入命令</button>
</div>''')
    body = "".join(cards) if cards else '<p class="hint-dim" data-zh="暂无已过审的 MCP 服务" data-en="No reviewed MCP servers yet">暂无已过审的 MCP 服务</p>'
    inner = f'''
<h2 data-zh="MCP 服务" data-en="MCP Servers">MCP 服务 <span class="n">{len(mcps)} 个 · 官方 server.json 标准</span></h2>
<p class="hint-dim" data-zh="Model Context Protocol 服务的安装与连接入口。远程服务填入 URL 即可连接;本地包由客户端从公共包仓库拉取并在本机起进程。用户密钥在安装时填入本地配置,不经过本站。" data-en="Install & connect entries for Model Context Protocol servers. Remote ones connect via URL; local packages are pulled by the client from public registries. Secrets are filled locally at install time, never passing through this site.">Model Context Protocol 服务的安装与连接入口。远程服务填入 URL 即可连接;本地包由客户端从公共包仓库拉取并在本机起进程。用户密钥在安装时填入本地配置,不经过本站。</p>
<div class="grid">{body}</div>
<div class="notice"><span data-zh="收录与风险说明:stdio 本地包=在本机执行第三方代码(标高风险),远程服务=连接到他人服务器(标低风险);所有条目均经人工审查(execReview=passed)才放出。" data-en="Curation & risk: stdio local packages execute third-party code on your machine (high risk); remote servers connect to third-party hosts (low risk). All entries pass manual review before listing.">收录与风险说明:stdio 本地包=在本机执行第三方代码(标高风险),远程服务=连接到他人服务器(标低风险);所有条目均经人工审查(execReview=passed)才放出。</span></div>'''
    return page_shell("MCP 服务", "MCP Servers", "mcp", inner)


def render_plugins(plugins):
    risk_label = {"low": "低风险", "medium": "中风险", "high": "高风险", "critical": "严重"}
    cards = []
    for m in plugins:
        cmd = m.get("installHint") or (m.get("install") or {}).get("command", "")
        clients = ", ".join((m.get("install") or {}).get("clients") or [])
        search = f"{m['name']} {m['title']} {m['description']} {m['description-zh']}".lower()
        cards.append(f'''<div class="card cat-{esc(m['category'])}" data-search="{esc(search)}" data-category="{esc(m['category'])}">
  <h3><a href="/mcp/{mcp_slug(m['name'])}.html">{esc(m['title'])}</a></h3>
  <div class="en-name">{esc(m['name'])}</div>
  <p><span data-zh="{esc(m['description-zh'])}" data-en="{esc(m['description'][:300])}">{esc(m['description-zh'])}</span></p>
  <div class="meta"><span class="tag cat">{esc(CATEGORIES.get(m['category'], m['category']))}</span><span class="tag kind-ext">插件</span><span class="tag risk-{esc(m['riskLevel'])}">{esc(risk_label.get(m['riskLevel'], m['riskLevel']))}</span><span class="count">v{esc(m['version'])}</span></div>
  <button class="chip on copy-btn" data-copy="{esc(cmd)}" data-skill="plugin:{esc(m['name'])}" data-zh="复制安装命令" data-en="Copy command">复制安装命令</button>
</div>''')
    body = "".join(cards) if cards else '<p class="hint-dim" data-zh="暂无已过审的插件" data-en="No reviewed plugins yet">暂无已过审的插件</p>'
    inner = f'''
<h2 data-zh="Agent 插件" data-en="Agent Plugins">Agent 插件 <span class="n">{len(plugins)} 个 · 官方市场指路牌</span></h2>
<p class="hint-dim" data-zh="面向 AI 编程客户端(VS Code / Cursor / Claude / Codex 等)的插件与扩展入口。本站只做指路:安装命令指向官方一手市场,本体不经本站分发。凭据在安装时填入本地客户端,不经过本站。" data-en="Plugins & extensions for AI coding clients (VS Code / Cursor / Claude / Codex). This site only signposts: install commands point at official first-party marketplaces; nothing is redistributed. Credentials are filled locally, never passing through this site.">面向 AI 编程客户端(VS Code / Cursor / Claude / Codex 等)的插件与扩展入口。本站只做指路:安装命令指向官方一手市场,本体不经本站分发。凭据在安装时填入本地客户端,不经过本站。</p>
<div class="grid">{body}</div>
<div class="notice"><span data-zh="收录与风险说明:插件=安装后在本机客户端内运行第三方代码(标中风险);指路牌只指向官方市场/一手仓库;所有条目均经人工审查(execReview=passed)才放出。" data-en="Curation & risk: plugins run third-party code inside your local client (medium risk); signposts point only to official marketplaces/repos. All entries pass manual review before listing.">收录与风险说明:插件=安装后在本机客户端内运行第三方代码(标中风险);指路牌只指向官方市场/一手仓库;所有条目均经人工审查(execReview=passed)才放出。</span></div>'''
    return page_shell("Agent 插件", "Agent Plugins", "plugins", inner)


def tools_html(m):
    tools = m.get("tools") or []
    if not tools:
        return ""
    rows = "".join(
        f'<tr><td><code class="inl">{esc(t.get("name", ""))}</code></td>'
        f'<td><span data-zh="{esc(t.get("description-zh", t.get("description", "")))}" data-en="{esc(t.get("description", ""))}">{esc(t.get("description-zh", t.get("description", "")))}</span></td></tr>'
        for t in tools)
    return (f'<h2 data-zh="提供工具" data-en="Tools">提供工具 <span class="n">{len(tools)} 个</span></h2>'
            f'<table class="api"><tr><th data-zh="工具" data-en="Tool">工具</th><th data-zh="说明" data-en="Description">说明</th></tr>{rows}</table>')


def cases_html(m):
    cases = m.get("useCases") or []
    if not cases:
        return ""
    items = "".join(
        f'<div class="card"><h3><span data-zh="{esc(c.get("title", ""))}" data-en="{esc(c.get("title-en", c.get("title", "")))}">{esc(c.get("title", ""))}</span></h3>'
        f'<div class="cmd">{esc(c.get("command", ""))}</div></div>'
        for c in cases)
    return (f'<h2 data-zh="使用场景" data-en="Use cases">使用场景 <span class="n">{len(cases)} 个</span></h2>'
            f'<div class="grid">{items}</div>')


def tags_html(m):
    tags = m.get("tags") or []
    if not tags:
        return ""
    chips = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)
    return f'<div class="meta">{chips}</div>'


def _mcp_mindmap(m):
    risk_label = {"low": "低风险", "medium": "中风险", "high": "高风险", "critical": "严重"}
    is_plugin = m.get("entryType", "mcp") == "plugin"
    kind = "插件指路" if is_plugin else ("远程服务" if m.get("kind") == "remote" else "本地 stdio")
    cat = m.get("category", "") or "未分类"
    branches = [("概览", [CATEGORIES.get(cat, cat), f"v{m.get('version', '')}", kind, risk_label.get(m.get("riskLevel"), m.get("riskLevel", "medium"))])]
    tools = m.get("tools") or []
    if tools:
        branches.append(("提供工具", [t.get("name", "") for t in tools[:8]]))
    cases = m.get("useCases") or []
    if cases:
        branches.append(("使用场景", [c.get("title", "")[:24] for c in cases[:6]]))
    tags = m.get("tags") or []
    if tags:
        branches.append(("标签", tags[:8]))
    return mmap_html(m.get("title", m.get("name", "")), branches, "结构导图")


def _pack_mindmap(p):
    pers = p.get("persona") or {}
    scene = pers.get("scene", "") or "未分类"
    branches = [("人设", [pers.get("role", "") or "—", CATEGORIES.get(scene, scene)])]
    members = p.get("members") or []
    if members:
        branches.append(("成员编队", [(m.get("title") or m.get("ref", ""))[:24] for m in members[:10]]))
    branches.append(("安装", [f"meta-skill: pack-{p.get('slug', '')}", "GET /v0/packs/" + p.get("slug", "")]))
    return mmap_html(p.get("displayName", ""), branches, "结构导图")


def _mcp_intro(m):
    risk_label = {"low": "低风险", "medium": "中风险", "high": "高风险", "critical": "严重"}
    is_plugin = m.get("entryType", "mcp") == "plugin"
    kind = "插件/扩展指路牌" if is_plugin else ("远程 MCP 服务" if m.get("kind") == "remote" else "本地 stdio MCP 包")
    cat = CATEGORIES.get(m.get("category", ""), m.get("category", "") or "未分类")
    out = f"「{m.get('title', m.get('name', ''))}」（{m.get('name', '')}）是一个{kind}，归类于「{cat}」，版本 v{m.get('version', '')}，风险等级{risk_label.get(m.get('riskLevel'), m.get('riskLevel', 'medium'))}。"
    desc = m.get("description-zh") or m.get("description", "")
    if desc:
        out += f" {desc.strip('。')}。"
    tools = m.get("tools") or []
    if tools:
        names = "、".join(t.get("name", "") for t in tools[:5])
        more = f" 等 {len(tools)} 个" if len(tools) > 5 else ""
        out += f" 它对外提供 {len(tools)} 个工具：{names}{more}。"
    cases = m.get("useCases") or []
    if cases:
        titles = "、".join(c.get("title", "") for c in cases[:4])
        out += f" 典型使用场景包括：{titles}。"
    if is_plugin:
        clients = ", ".join((m.get("install") or {}).get("clients") or [])
        if clients:
            out += f" 支持客户端：{clients}。"
    elif m.get("kind") == "remote":
        rem = (m.get("remotes") or [{}])[0]
        url = rem.get("url", "")
        if url:
            out += f" 通过远程端点 {url} 连接，无需本地安装。"
    else:
        out += " 以本地 stdio 方式运行，安装后由客户端拉起第三方进程。"
    if m.get("riskNote"):
        out += f" {m['riskNote']}"
    return out


def _pack_intro(p):
    pers = p.get("persona") or {}
    scene = CATEGORIES.get(pers.get("scene", ""), pers.get("scene", "") or "未分类")
    out = f"「{p.get('displayName', '')}」（{p.get('displayNameEn', '')}）是一个{scene}方向的专家团，角色定位为「{pers.get('role', '')}」。"
    if pers.get("tagline"):
        out += f" 一句话定位：{pers.get('tagline', '')}。"
    if pers.get("intro"):
        out += f" {pers['intro'].strip('。')}。"
    members = p.get("members") or []
    if members:
        names = "、".join((m.get("title") or m.get("ref", "")) for m in members[:5])
        more = f" 等 {len(members)} 个" if len(members) > 5 else ""
        out += f" 成员编队共 {len(members)} 个（{names}{more}），按协作剧本顺序安装执行。"
    if p.get("summary"):
        out += f" {p['summary'].strip('。')}。"
    return out


def render_mcp_detail(m):
    risk_label = {"low": "低风险", "medium": "中风险", "high": "高风险", "critical": "严重"}
    is_plugin = m.get("entryType", "mcp") == "plugin"
    method = (m.get("install") or {}).get("method", "link")
    method_zh = {"marketplace": "官方市场", "command": "命令安装", "link": "链接指路"}.get(method, "指路")
    kind_text = (method_zh if is_plugin else ("远程" if m["kind"] == "remote" else "本地(stdio)"))
    install = m.get("install") or {}
    cmd = m["installHint"] or install.get("command", "") or (f"claude mcp add --transport http {m['name'].split('/')[-1]} {m['remote_url']}" if m["kind"] == "remote" else "")
    conn_rows = ""
    if is_plugin:
        clients = ", ".join(install.get("clients") or []) or "—"
        url = install.get("url", "")
        url_link = f'<a href="{esc(url)}">{esc(url)}</a>' if url else "—"
        conn_html = (f'<h2 data-zh="安装来源" data-en="Install source">安装来源</h2>'
                     f'<table class="api"><tr><th data-zh="方式" data-en="Method">方式</th><td><code class="inl">{esc(install.get("method", "link"))}</code></td></tr>'
                     f'<tr><th data-zh="官方市场页" data-en="Marketplace">官方市场页</th><td>{url_link}</td></tr>'
                     f'<tr><th data-zh="适用客户端" data-en="Clients">适用客户端</th><td>{esc(clients)}</td></tr></table>'
                     f'<p class="hint-dim" data-zh="指路牌条目:本体由官方市场分发,本站不托管;安装后在本地客户端内运行第三方代码,收录已过人工审查。" data-en="Signpost entry: distributed by the official marketplace, not hosted here; runs third-party code inside your local client; manually reviewed at curation time.">指路牌条目:本体由官方市场分发,本站不托管;安装后在本地客户端内运行第三方代码,收录已过人工审查。</p>')
    elif m["kind"] == "remote":
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
    if m.get("archived"):
        status_txt = "⚠️ 上游已归档（只读）"
    elif alive:
        status_txt = "🟢 在线"
    else:
        status_txt = "🔴 失联"
    links = []
    if m["websiteUrl"]:
        links.append(f'<a href="{esc(m["websiteUrl"])}">官网</a>')
    if m["repository"]:
        links.append(f'<a href="{esc(m["repository"])}">仓库</a>')
    links_html = " · ".join(links) if links else "—"
    pushed_html = ""
    if ups.get("pushedAt"):
        pushed_html = " · 最近推送 " + esc(str(ups.get("pushedAt"))[:10])
    if m.get("upstreamNote"):
        pushed_html += " · " + esc(m.get("upstreamNote"))
    badge = "MCP" if m.get("entryType", "mcp") == "mcp" else "插件"
    inner = f'''<div class="detail">
  <div class="card-head"><h1>{esc(m['title'])}</h1><span class="badge ext">{badge} · {kind_text}</span></div>
  <div class="en-name">{esc(m['name'])}</div>
  <p class="desc"><span data-zh="{esc(_mcp_intro(m))}" data-en="{esc(m['description'])}">{esc(_mcp_intro(m))}</span></p>
  <dl class="kv">
    <dt data-zh="分类" data-en="Category">分类</dt><dd>{esc(CATEGORIES.get(m['category'], m['category']))}</dd>
    <dt data-zh="版本" data-en="Version">版本</dt><dd>v{esc(m['version'])}</dd>
    <dt data-zh="风险等级" data-en="Risk">风险等级</dt><dd><span class="tag risk-{esc(m['riskLevel'])}">{esc(risk_label.get(m['riskLevel'], m['riskLevel']))}</span></dd>
    <dt data-zh="上游状态" data-en="Upstream">上游状态</dt><dd>{status_txt} · {esc(ups.get('lastCheck') or '—')}{pushed_html}</dd>
    <dt data-zh="收录审查" data-en="Review">收录审查</dt><dd>{esc(rev.get('by') or '—')} · {esc(rev.get('at') or '—')}</dd>
    <dt data-zh="外部链接" data-en="Links">外部链接</dt><dd>{links_html}</dd>
  </dl>
  <p class="hint-ok" data-zh="一条命令接入客户端:" data-en="Install with one command:">一条命令接入客户端:</p>
  <div class="cmd">{esc(cmd)}</div>
  <button class="chip on copy-btn" data-copy="{esc(cmd)}" data-skill="{('plugin:' if is_plugin else 'mcp:')}{esc(m['name'])}" data-zh="复制接入命令" data-en="Copy install command">复制接入命令</button>
  <p class="hint-dim">{esc(m['riskNote'])}</p>
</div>
{conn_html}
{_mcp_mindmap(m)}
{tools_html(m)}{cases_html(m)}{tags_html(m)}'''
    nav_key = "mcp" if m.get("entryType", "mcp") == "mcp" else "plugins"
    return page_shell(m["title"], m["name"], nav_key, inner)




MEMBER_TYPE_LABEL = {
    "own-skill": ("自研技能", "Own skill", "kind-own"),
    "ext-skill": ("社区精选", "Curated", "kind-ext"),
    "mcp": ("MCP 服务", "MCP server", "kind-mcp"),
    "cli": ("CLI 工具", "CLI tool", "kind-preview"),
    "api": ("远程 API", "Remote API", "kind-preview"),
}


def _md_inline(s: str) -> str:
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)

    def link(m):
        url, text = m.group(2), m.group(1)
        if not url.startswith(("https://", "http://", "/")):
            return text
        return f'<a href="{url}">{text}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)


def md_to_html(text: str) -> str:
    """最小 Markdown 渲染:标题/列表/代码块/引用/粗体/行内代码/链接。先转义再上标签。"""
    out, para, list_open, in_code, code_buf = [], [], None, False, []

    def flush_para():
        if para:
            out.append("<p>" + _md_inline(esc(" ".join(para))) + "</p>")
            para.clear()

    def close_list():
        nonlocal list_open
        if list_open:
            out.append(f"</{list_open}>")
            list_open = None

    for raw in (text or "").splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            if in_code:
                out.append("<pre><code>" + esc("\n".join(code_buf)) + "</code></pre>")
                code_buf.clear()
            else:
                flush_para()
                close_list()
            in_code = not in_code
            continue
        if in_code:
            code_buf.append(raw)
            continue
        if not line.strip():
            flush_para()
            close_list()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush_para()
            close_list()
            lvl = min(len(m.group(1)) + 1, 4)
            out.append(f"<h{lvl}>" + _md_inline(esc(m.group(2))) + f"</h{lvl}>")
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m:
            flush_para()
            if list_open != "ul":
                close_list()
                out.append("<ul>")
                list_open = "ul"
            out.append("<li>" + _md_inline(esc(m.group(1))) + "</li>")
            continue
        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m:
            flush_para()
            if list_open != "ol":
                close_list()
                out.append("<ol>")
                list_open = "ol"
            out.append("<li>" + _md_inline(esc(m.group(1))) + "</li>")
            continue
        m = re.match(r"^\s*>\s?(.*)$", line)
        if m:
            flush_para()
            close_list()
            out.append("<blockquote>" + _md_inline(esc(m.group(1))) + "</blockquote>")
            continue
        para.append(line.strip())
    if in_code and code_buf:
        out.append("<pre><code>" + esc("\n".join(code_buf)) + "</code></pre>")
    flush_para()
    close_list()
    return "\n".join(out)


def pack_install_prompt(p) -> str:
    return (f"请阅读 https://skillx.yueliai.top/install/pack-install.md,"
            f"按其中的步骤安装专家团「{p['displayName']}」({p['slug']})。")


def pack_card(p):
    pers = p["persona"]
    scene = pers.get("scene", "")
    avatar = pers.get("avatar") or "assets/avatars/pack-default.svg"
    origin_badge = ('<span class="tag kind-own" data-zh="自研" data-en="Own">自研</span>'
                    if p.get("origin") == "own" else
                    '<span class="tag kind-ext" data-zh="收录" data-en="Curated">收录</span>')
    deg = ('<span class="tag risk-medium" data-zh="成员降级" data-en="Degraded">成员降级</span>'
           if p.get("degraded") else "")
    search = f"{p['displayName']} {p['displayNameEn']} {p['slug']} {p['summary']} {pers.get('role','')} {pers.get('tagline','')} " + " ".join(m.get('ref','') for m in p['members'])
    tagline = pers.get("tagline") or p["summary"]
    tagline_en = pers.get("taglineEn") or p["summaryEn"]
    return f'''<div class="card pack-card cat-{esc(scene)}" data-search="{esc(search.lower())}" data-category="{esc(scene)}">
  <div class="pack-head">
    <img class="avatar" src="/{esc(avatar)}?v={media_ver(avatar)}" alt="" width="52" height="52">
    <div>
      <h3><a href="/{p['page']}">{esc(p['displayName'])}</a></h3>
      <div class="en-name">{esc(p['displayNameEn'])} · {esc(p['slug'])}</div>
    </div>
  </div>
  <div class="role">{esc(pers.get('role',''))}</div>
  <p><span data-zh="{esc(tagline)}" data-en="{esc(tagline_en)}">{esc(tagline)}</span></p>
  <div class="meta"><span class="tag cat">{esc(CATEGORIES.get(scene, scene))}</span>{origin_badge}{deg}<span class="count">{len(p['members'])} <span data-zh="个成员" data-en="members">个成员</span></span></div>
</div>'''


def render_packs(packs):
    cards = "\n".join(pack_card(p) for p in packs)
    body = cards if cards else ('<p class="hint-dim" data-zh="专家团正在收录中。" data-en="Expert packs are being curated.">专家团正在收录中。</p>')
    inner = f'''
<h2 data-zh="专家团" data-en="Expert Packs">专家团 <span class="n">{len(packs)} 个 · 人设 + 编排剧本 + 一键安装</span></h2>
<p class="hint-dim" data-zh="专家团 = 带完整人设的编排层:把自研技能、社区精选与 MCP 服务按场景组队,配一份可直接执行的协作剧本。支持自研与收录两种来源;安装走安装契约文档,Agent 读文档即会安装,第三方应用也可直接调 API。" data-en="An expert pack is a persona-driven orchestration layer: own skills, curated skills and MCP servers grouped by scenario, with an executable collaboration script. Own and curated packs are both supported; installs follow the install contract doc, and third-party apps can call the API directly.">专家团 = 带完整人设的编排层:把自研技能、社区精选与 MCP 服务按场景组队,配一份可直接执行的协作剧本。支持自研与收录两种来源;安装走安装契约文档,Agent 读文档即会安装,第三方应用也可直接调 API。</p>
<div class="search"><input id="q" type="search" data-zh="按名称或关键词筛选专家团…" data-en="Filter expert packs…" data-attr="placeholder" placeholder="按名称或关键词筛选专家团…"></div>
{chips_html()}
<div class="grid grid-mt">{body}</div>
<div class="empty hidden" id="empty" data-zh="没有匹配的专家团" data-en="No matching expert packs">没有匹配的专家团</div>
<div class="notice"><span data-zh="安装契约文档(给 Agent 读的提示词入口):" data-en="Install contract doc (prompt entry for agents):">安装契约文档(给 Agent 读的提示词入口):</span><code class="inl">https://skillx.yueliai.top/install/pack-install.md</code></div>'''
    return page_shell("专家团", "Expert Packs", "packs", inner)


def render_pack_detail(p):
    pers = p["persona"]
    scene = pers.get("scene", "")
    avatar = pers.get("avatar") or "assets/avatars/pack-default.svg"
    body_html = md_to_html(parse_frontmatter(p.get("content") or "")[2])
    member_cards = []
    for m in p["members"]:
        zh, en, cls = MEMBER_TYPE_LABEL.get(m.get("type"), (m.get("type", ""), m.get("type", ""), "kind-preview"))
        if not m.get("resolved"):
            note = m.get("note", "成员暂不可用")
            member_cards.append(f'''<div class="card member-card member-missing">
  <div class="card-head"><h3>{esc(m.get('ref',''))}</h3><span class="tag risk-medium" data-zh="不可用" data-en="Unavailable">不可用</span></div>
  <p class="hint-warn">{esc(note)}</p>
</div>''')
            continue
        title = m.get("title") or m.get("ref", "")
        title_html = f'<a href="{esc(m["page"])}">{esc(title)}</a>' if m.get("page") else esc(title)
        desc = m.get("description-zh") or m.get("description", "")
        cmd = m.get("install") or ""
        if m.get("type") == "mcp":
            path = esc(m.get("installPath", ""))
            cmd_block = (f'<p class="hint-dim" data-zh="接入描述:GET {path}(含客户端配置片段与密钥声明)" '
                         f'data-en="Install descriptor: GET {path}">接入描述:<code class="inl">GET {path}</code>(含客户端配置片段与密钥声明)</p>')
            copy_btn = ""
        elif cmd:
            cmd_block = f'<div class="cmd">{esc(cmd)}</div>'
            copy_btn = (f'<button class="chip on copy-btn" data-copy="{esc(cmd)}" data-skill="{esc(m.get("name", m.get("ref", "")))}" '
                        f'data-zh="复制安装命令" data-en="Copy install command">复制安装命令</button>')
        else:
            cmd_block, copy_btn = "", ""
        member_cards.append(f'''<div class="card member-card cat-{esc(m.get('category', ''))}">
  <div class="card-head"><h3>{title_html}</h3><span class="tag {cls}" data-zh="{esc(zh)}" data-en="{esc(en)}">{esc(zh)}</span></div>
  <div class="en-name">{esc(m.get('ref',''))}</div>
  <p>{esc(desc)}</p>
  {cmd_block}{copy_btn}
</div>''')
    members_html = "\n".join(member_cards)
    prompt = pack_install_prompt(p)
    deg_html = ("" if not p.get("degraded") else
                f'<div class="notice"><span data-zh="部分成员已下架或未收录,安装前请核对成员状态:" data-en="Some members are unavailable; verify before install:">部分成员已下架或未收录,安装前请核对成员状态:</span><code class="inl">{esc(", ".join(p.get("missingMembers") or []))}</code></div>')
    origin_text = "自研专家团" if p.get("origin") == "own" else "收录专家团"
    origin_en = "Own pack" if p.get("origin") == "own" else "Curated pack"
    upstream_html = (f'<a href="{esc(p["upstream"])}">上游来源</a>' if p.get("upstream") else "—")
    status_txt = "部分成员不可用" if p.get("degraded") else "成员齐备"
    install_cmd = p.get("install") or ""
    install_html = (f'<div class="cmd">{esc(install_cmd)}</div><button class="chip on copy-btn" data-copy="{esc(install_cmd)}" data-skill="pack/{esc(p["slug"])}" data-zh="复制安装命令" data-en="Copy install command">复制安装命令</button>' if install_cmd else "")
    inner = f'''<div class="detail persona-hero">
  <img class="avatar xl" src="/{esc(avatar)}?v={media_ver(avatar)}" alt="" width="104" height="104">
  <div class="persona-body">
    <div class="card-head"><h1>{esc(p['displayName'])}</h1><span class="badge auth" data-zh="{origin_text}" data-en="{origin_en}">{origin_text}</span></div>
    <div class="en-name">{esc(p['displayNameEn'])} · {esc(p['slug'])}</div>
    <p class="persona-role"><span data-zh="{esc(pers.get('role',''))}" data-en="{esc(pers.get('roleEn',''))}">{esc(pers.get('role',''))}</span></p>
    <p class="persona-tagline"><span data-zh="{esc(pers.get('tagline',''))}" data-en="{esc(pers.get('taglineEn',''))}">{esc(pers.get('tagline',''))}</span></p>
    <p class="desc"><span data-zh="{esc(_pack_intro(p))}" data-en="{esc(pers.get('introEn',''))}">{esc(_pack_intro(p))}</span></p>
  </div>
</div>
<dl class="kv">
  <dt data-zh="场景" data-en="Scene">场景</dt><dd>{esc(CATEGORIES.get(scene, scene))}</dd>
  <dt data-zh="成员" data-en="Members">成员</dt><dd>{len(p['members'])} 个</dd>
  <dt data-zh="许可证" data-en="License">许可证</dt><dd>{esc(p.get('license') or '—')}</dd>
  <dt data-zh="成员状态" data-en="Status">成员状态</dt><dd>{status_txt}</dd>
  <dt data-zh="收录审查" data-en="Review">收录审查</dt><dd>{esc(p['reviewed'].get('by') or '—')} · {esc(p['reviewed'].get('at') or '—')}</dd>
  <dt data-zh="上游" data-en="Upstream">上游</dt><dd>{upstream_html}</dd>
</dl>
{deg_html}
{_pack_mindmap(p)}
<h2 data-zh="成员编队" data-en="Member squad">成员编队 <span class="n">{len(p['members'])} 个 · 按剧本顺序安装</span></h2>
<div class="grid">{members_html}</div>
<h2 data-zh="协作剧本" data-en="Collaboration script">协作剧本 <span class="n">meta-skill 正文</span></h2>
<div class="md-body">{body_html}</div>
<h2 data-zh="安装" data-en="Install">安装</h2>
<p class="hint-ok" data-zh="给 Agent 的安装提示词(复制后直接发给任意 Agent):" data-en="Install prompt for an agent (copy and send):">给 Agent 的安装提示词(复制后直接发给任意 Agent):</p>
<div class="cmd">{esc(prompt)}</div>
<button class="chip on copy-btn" data-copy="{esc(prompt)}" data-skill="pack/{esc(p["slug"])}" data-zh="复制安装提示词" data-en="Copy install prompt">复制安装提示词</button>
<p class="hint-dim" data-zh="安装该专家团的编排技能(meta-skill,获得完整剧本):" data-en="Install the pack meta-skill (full script included):">安装该专家团的编排技能(meta-skill,获得完整剧本):</p>
{install_html}
<p class="hint-dim" data-zh="程序化接入:GET /v0/packs/{esc(p['slug'])} 取成员安装描述符;契约文档 /install/pack-install.md;安装回报 POST /api/pack/install。" data-en="Programmatic: GET /v0/packs/{esc(p['slug'])} for member descriptors; contract at /install/pack-install.md; report installs via POST /api/pack/install.">程序化接入:<code class="inl">GET /v0/packs/{esc(p['slug'])}</code> 取成员安装描述符;契约文档 <code class="inl">/install/pack-install.md</code>;安装回报 <code class="inl">POST /api/pack/install</code>。</p>'''
    return page_shell(f"{p['displayName']} · 专家团", p['displayNameEn'], "packs", inner)


def render_pack_install_doc(packs):
    """全局安装契约文档(给 Agent 读的提示词入口,静态生成到 /install/pack-install.md)。"""
    rows = [f"- {p['displayName']}({p['displayNameEn']}, slug: {p['slug']})· {p['summary']}" for p in packs]
    lines = [
        "# Skill X 专家团安装契约",
        "",
        "## 概述",
        "",
        "Skill X 是面向安全研究与逆向工程的技能/专家团注册中心,提供橱窗站与公开 API,不提供自有 CLI。",
        "Agent 读取本文档后,用标准 HTTP 请求 + npx skills 即可完成专家团安装;第三方应用程序可直接按同样流程程序化接入。",
        "",
        "## 适用场景(先判断)",
        "",
        "- 仅安装某个专家团 → 直接执行第三节:先拉 GET /v0/packs/<slug>,再按成员清单逐个安装,不要重复询问。",
        "- 想先浏览有哪些专家团 → 读第二节的清单接口或访问橱窗页。",
        "",
        "## 一、前置检查",
        "",
        "- 站点与 API 基址:`https://skillx.yueliai.top`(本机需可联网访问)。",
        "- 安装成员需要能执行 `npx skills`(vercel-labs/skills CLI,支持 80+ agent)。",
        "- 自研成员来自私有仓库,需要用户提供 `GITHUB_TOKEN`(PAT,Contents: read)。没有凭据时:跳过自研成员,只装收录成员,并向用户说明。",
        "",
        "## 二、浏览专家团(可选)",
        "",
        "```bash",
        "curl -s https://skillx.yueliai.top/v0/packs",
        "```",
        "",
        "返回 JSON:每个专家团含 slug / displayName / persona / summary / memberCount / degraded,游标分页(?cursor=&limit=)。",
        "当前已收录的专家团:",
        "",
    ] + (rows or ["- (暂无)"]) + [
        "",
        "## 三、安装专家团(核心流程)",
        "",
        "### 第 1 步:读取专家团详情",
        "",
        "```bash",
        "curl -s https://skillx.yueliai.top/v0/packs/<slug>",
        "```",
        "",
        "详情返回 members[],每个成员带 type / ref / name / title / install / page / resolved:",
        "",
        "- type=own-skill:install 是自研安装命令(含 <PAT> 占位,需替换为用户提供的真实 GITHUB_TOKEN)。",
        "- type=ext-skill:install 是上游安装命令,可直接执行。",
        "- type=mcp:用 ref 调 GET /v0/servers/<ref>/install 取客户端配置片段;需要密钥时向用户索要,密钥只在本地写入客户端配置,不经过本站。",
        "- type=cli/api:预留类型,按 install 字段执行。",
        "",
        "### 第 2 步:安装编排技能(meta-skill)",
        "",
        "专家团本身是一个 meta-skill(详情 install 字段给出命令),安装后 Agent 获得完整协作剧本:",
        "",
        "```bash",
        "GITHUB_TOKEN=<PAT> npx skills add JacksenHu/skill-x --skill pack-<slug>",
        "```",
        "",
        "### 第 3 步:按顺序安装成员",
        "",
        "按成员清单顺序逐个安装;单个成员失败时:记录失败原因,继续安装其余成员,最后汇总。",
        "",
        "### 第 4 步:回报安装(可选)",
        "",
        "```bash",
        "curl -s -X POST -H \"Content-Type: application/json\" -d '{\"slug\":\"<slug>\"}' https://skillx.yueliai.top/api/pack/install",
        "```",
        "",
        "## 四、失败与回退",
        "",
        "- API 不可达:改用橱窗页 https://skillx.yueliai.top/packages/<slug>.html 人工指引。",
        "- 成员 resolved=false(已下架):跳过该成员并说明;degraded=true 的专家团不阻塞其余成员安装。",
        "- skills CLI 找不到全局加载目录:按目标 Agent 文档确认其全局 skills 目录后再装。",
        "",
        "## 五、验收",
        "",
        "安装完成后逐项报告:已装成员(名称/类型/安装方式)、未装成员及原因、专家团 meta-skill 是否可被 Agent 加载。",
        "",
    ]
    return "\n".join(lines) + "\n"


def render_home(own, suites, mcps, packs, map_svg=""):
    total_ext = sum(len(s["skills"]) for s in suites)
    plugins = [m for m in mcps if m.get("entryType", "mcp") == "plugin"]
    audit = load_audit()
    audit_at = audit.get("generatedAt", "")
    audit_entry = (audit.get("skills") or {}).get("binary-reverse-engineering")
    featured = "\n".join(card(s, "own", s["page"], s["name"]) for s in own[:3])
    packs_html = "\n".join(pack_card(p) for p in packs)
    for suite in suites:
        ns = suite["namespace"]
        for s in suite["skills"][:2]:
            featured += "\n" + card(s, "ext", f"skills/ext-{ns_slug(ns)}--{skill_slug(s['name'])}.html", f"{ns}/{s['name']}")
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
    plugin_items = ""
    for m in plugins[:3]:
        risk = esc(m.get("riskLevel", ""))
        plugin_items += (f'<a class="home-mcp-item" href="/mcp/{mcp_slug(m["name"])}.html">'
                         f'<div class="t">{esc(m.get("title", m["name"]))}</div>'
                         f'<div class="id">{esc(m["name"])}</div>'
                         f'<div class="meta"><span class="tag" data-zh="插件" data-en="Plugin">插件</span>'
                         f'<span class="tag risk-{risk}">{risk}</span>'
                         f'<span class="tag">v{esc(m.get("version", ""))}</span></div></a>')
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
    <h1>Skill <em>X</em></h1>
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
  <h2 data-zh="专家团" data-en="Expert packs">专家团 <span class="n">{len(packs)} 个已过审 · 人设 + 编排剧本</span></h2>
  <p class="hint-dim" data-zh="带完整人设的编排层:把自研技能、社区精选与 MCP 服务按场景组队。安装走安装契约文档,Agent 读文档即会安装。" data-en="Persona-driven orchestration: own skills, curated skills and MCP servers grouped by scenario. Installs follow the contract doc that agents can read directly.">带完整人设的编排层:把自研技能、社区精选与 MCP 服务按场景组队。安装走安装契约文档,Agent 读文档即会安装。</p>
  <div class="grid reveal">{packs_html}</div>
  <p class="home-more"><a class="btn ghost" href="/packages.html" data-zh="全部专家团" data-en="All expert packs">全部专家团</a></p>
</section>

<section class="home-mcp">
  <h2 data-zh="MCP 服务" data-en="MCP servers">MCP 服务 <span class="n">{len([m for m in mcps if m.get('entryType','mcp') == 'mcp'])} 个已过审</span></h2>
  <p class="hint-dim" data-zh="按官方 server.json 标准收录,只放人工审查通过的条目;密钥与认证头永不经过本站。" data-en="Curated to the official server.json standard; reviewed entries only; secrets never pass through this site.">按官方 server.json 标准收录,只放人工审查通过的条目;密钥与认证头永不经过本站。</p>
  <div class="home-mcp-list reveal">{mcp_items}</div>
  <p class="home-more"><a class="btn ghost" href="/mcp.html" data-zh="全部 MCP 服务" data-en="All MCP servers">全部 MCP 服务</a></p>
</section>

<section class="home-mcp">
  <h2 data-zh="Agent 插件" data-en="Agent plugins">Agent 插件 <span class="n">{len(plugins)} 个已过审</span></h2>
  <p class="hint-dim" data-zh="AI 编程客户端的插件与扩展,指路牌只指向官方一手市场;本体不经本站分发。" data-en="Plugins & extensions for AI coding clients; signposts point only to official first-party marketplaces; nothing is redistributed.">AI 编程客户端的插件与扩展,指路牌只指向官方一手市场;本体不经本站分发。</p>
  <div class="home-mcp-list reveal">{plugin_items}</div>
  <p class="home-more"><a class="btn ghost" href="/plugins.html" data-zh="全部插件" data-en="All plugins">全部插件</a></p>
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


# ---- 构建后处理(wrapper 集成的图标 / 复制配置 / 卡片图标 CSS)----
DEFAULT_ICON = "assets/avatars/icon-default.svg"
SHOWCASE = Path(__file__).resolve().parent

slug = mcp_slug  # wrapper 兼容别名(与 mcp_slug 同一规则)

def gitmcp_url(website_url: str) -> str:
    """github.com/owner/repo -> gitmcp.io/owner/repo(即时 AI 上下文)。"""
    if not website_url:
        return ""
    m = re.match(r"https?://(?:www\.)?github\.com/([\w.-]+/[\w.-]+)", website_url)
    return f"https://gitmcp.io/{m.group(1)}" if m else ""


CAT_LABELS = {
    "reverse-engineering": "逆向工程",
    "pentest": "渗透测试",
    "malware": "样本分析",
    "forensics": "内存取证",
    "engineering-hygiene": "工程纪律",
    "dev-workflow": "工程流程",
    "data": "数据抓取",
    "web-frontend": "Web 前端",
    "ai-media": "AI 媒体",
}

def original_icon_map():
    reg_path = ROOT / "mcp-registry.json"
    if not reg_path.is_file():
        return {}
    try:
        doc = json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for s in doc.get("servers", []):
        icons = s.get("icons") or []
        src = icons[0].get("src") if icons else ""
        name = s.get("name", "")
        if name and src:
            out[name] = src
    return out

def update_site_data_icons():
    site_path = SHOWCASE / "dist" / "site-data.json"
    if not site_path.is_file():
        return
    doc = json.loads(site_path.read_text(encoding="utf-8"))
    for sk in doc.get("skills", []):
        sk["icon"] = DEFAULT_ICON
    for sk in doc.get("own", []):
        sk["icon"] = DEFAULT_ICON
    icons = original_icon_map()
    for m in doc.get("mcps", []):
        m["icon"] = icons.get(m.get("name", "")) or DEFAULT_ICON
    site_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

def insert_detail_icons():
    dist = SHOWCASE / "dist"
    icons = original_icon_map()
    for path in list((dist / "skills").glob("*.html")) + list((dist / "mcp").glob("*.html")):
        icon = DEFAULT_ICON
        if path.parent.name == "mcp":
            for name, src in icons.items():
                if path.name == slug(name) + ".html":
                    icon = src
                    break
        html = path.read_text(encoding="utf-8", errors="replace")
        if '<img class="avatar" style="width:44px;height:44px"' in html:
            continue
        img = f'<img class="avatar" style="width:44px;height:44px" src="{icon}" alt="" width="44" height="44">'
        html = html.replace('<div class="card-head"><h1>', '<div class="card-head">' + img + '<h1>', 1)
        path.write_text(html, encoding="utf-8")

def inject_copy_config_buttons():
    """MCP 详情页注入「复制配置」按钮:复制 gitmcp.io MCP 配置(无需 clone/装依赖)。"""
    reg = ROOT / "mcp-registry.json"
    dist_mcp = SHOWCASE / "dist" / "mcp"
    if not reg.is_file() or not dist_mcp.is_dir():
        return
    doc = json.loads(reg.read_text(encoding="utf-8"))
    for s in doc.get("servers", []):
        name = s.get("name", "")
        url = gitmcp_url(s.get("websiteUrl") or "")
        if not url:
            continue
        short = name.split("/")[-1]
        cfg = json.dumps({"mcpServers": {short: {"type": "http", "url": url}}}, ensure_ascii=False)
        page = dist_mcp / (slug(name) + ".html")
        if not page.is_file():
            continue
        html = page.read_text(encoding="utf-8", errors="replace")
        if 'data-zh="复制配置"' in html:
            continue
        anchor = f'data-skill="mcp:{name}" data-zh="复制接入命令"'
        idx = html.find(anchor)
        if idx < 0:
            continue
        end = html.find("</button>", idx)
        if end < 0:
            continue
        btn = (f'<button class="chip copy-btn" data-copy=\'{cfg}\' '
               f'data-skill="mcp:{name}" data-zh="复制配置" data-en="Copy config">复制配置</button>')
        html = html[:end + 9] + " " + btn + html[end + 9:]
        page.write_text(html, encoding="utf-8")

def inject_mcp_plugin_filters():
    """给 mcp.html / plugins.html 注入搜索框 + 分类筛选 chips(复用 app.js sxFilter)。"""
    dist = SHOWCASE / "dist"
    for fname in ("mcp.html", "plugins.html"):
        path = dist / fname
        if not path.is_file():
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        if 'id="q"' in html:
            continue
        cats = sorted(set(re.findall(r'data-category="([\w-]+)"', html)))
        chips = ['<span class="chip on" data-cat="" data-zh="全部" data-en="All">全部</span>']
        for c in cats:
            zh = CAT_LABELS.get(c, c)
            chips.append(f'<span class="chip" data-cat="{c}" data-zh="{zh}" data-en="{c}">{zh}</span>')
        block = ('<div class="search"><input id="q" type="search" '
                 'data-zh="按名称或关键词筛选…" data-en="Filter by name or keyword…" '
                 'data-attr="placeholder" placeholder="按名称或关键词筛选…"></div>\n'
                 '<div class="chips">' + "".join(chips) + '</div>\n')
        idx = html.find('<div class="grid">')
        if idx < 0:
            continue
        html = html[:idx] + block + html[idx:]
        path.write_text(html, encoding="utf-8")


def append_card_icon_css():
    css_path = SHOWCASE / "dist" / "assets" / "style.css"
    if not css_path.is_file():
        return
    css = css_path.read_text(encoding="utf-8", errors="replace")
    rule = """
.card:not(.pack-card) h3::before{content:"";display:inline-block;width:28px;height:28px;margin-right:8px;vertical-align:middle;background:url("/assets/avatars/icon-default.svg") center/contain no-repeat;border:1px solid var(--line2);border-radius:3px;flex:none}
"""
    if "card:not(.pack-card) h3::before" not in css:
        css += rule
    css_path.write_text(css, encoding="utf-8")

def main():
    own, bodies = collect_own_skills()
    suites, _ = collect_external()
    mcps = collect_mcps()
    packs = collect_packs()
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

    pages = {"index.html": render_home(own, suites, mcps, packs, mmaps.get("binary-reverse-engineering", "")),
             "skills.html": render_index(own, suites)}
    pages["packages.html"] = render_packs(packs)
    pages["install/pack-install.md"] = render_pack_install_doc(packs)
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
            pages[f"skills/ext-{ns_slug(ns)}--{skill_slug(s['name'])}.html"] = render_ext_detail(
                suite, s, (audit.get("suites") or {}).get(ns), audit_at,
                mmaps.get(f"suite-{ns_slug(ns)}", ""))
    real_mcps = [m for m in mcps if m.get("entryType", "mcp") == "mcp"]
    plugin_entries = [m for m in mcps if m.get("entryType", "mcp") == "plugin"]
    pages["mcp.html"] = render_mcp(real_mcps)
    pages["plugins.html"] = render_plugins(plugin_entries)
    for m in mcps:
        pages[f"mcp/{mcp_slug(m['name'])}.html"] = render_mcp_detail(m)
    for p in packs:
        pages[p["page"]] = render_pack_detail(p)
    stale_packs = [p["slug"] for p in packs if not p["contentFresh"]]
    if stale_packs:
        print(f"[!] 专家团编排剧本与 packs.json 缓存不一致(跑 scripts/pack_ingest.py --sync 可修复): {', '.join(stale_packs)}")
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
    src_all = ("".join(s["src"] for s in own)
               + (EXTERNAL.read_text(encoding="utf-8") if EXTERNAL.is_file() else "")
               + (I18N_EXT.read_text(encoding="utf-8") if I18N_EXT.is_file() else "")
               + (PACKS.read_text(encoding="utf-8") if PACKS.is_file() else "")
                + (I18N_PACKS.read_text(encoding="utf-8") if I18N_PACKS.is_file() else "")
                + "".join(p["content"] for p in packs))

    # 工具商店源数据纳入缓存键：改了工具数据也要重建工具页
    _tools_src = ROOT / "tools-store" / "api-import-payload.json"
    src_all += (_tools_src.read_text(encoding="utf-8") if _tools_src.is_file() else "")

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
        for f in sorted(src_assets.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in media_ext:
                continue
            data = f.read_bytes()
            rel_name = f.relative_to(src_assets).as_posix()
            rel_asset = f"assets/{rel_name}"
            key = sha(TEMPLATE_VERSION + rel_name + hashlib.sha256(data).hexdigest())
            new_manifest[rel_asset] = key
            p = assets / rel_name
            if old_manifest.get(rel_asset) == key and p.is_file():
                skipped += 1
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
                written += 1

    # 清理过时产物(已下架技能/套件/导图的残留文件,避免旧页面仍可访问)
    valid = set(new_manifest.keys())
    removed = 0
    for f in sorted(DIST.rglob("*")):
        if not f.is_file() or f.is_symlink():
            continue
        rel = str(f.relative_to(DIST)).replace("\\", "/")
        if rel == "tools.html" or rel.startswith("tools/"):
            continue  # 工具商店由 render_tools_store 在 manifest 之后生成,不参与清理
        stale_page = rel.endswith((".html", ".svg", ".md")) and rel not in valid
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
                "page": f"/skills/ext-{ns_slug(st['namespace'])}--{skill_slug(x['name'])}.html",
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
                "entryType": cur.get("entryType", "mcp"),
                "category": cur.get("category"), "riskLevel": cur.get("riskLevel"),
                "installHint": cur.get("installHint", ""),
                "install": cur.get("install") or {},
                "page": f"/mcp/{mcp_slug(s.get('name', ''))}.html",
                "remotes": [{"type": r.get("type"), "url": r.get("url")} for r in (s.get("remotes") or [])],
                "packages": [{"registryType": p.get("registryType"), "identifier": p.get("identifier"), "version": p.get("version")} for p in (s.get("packages") or [])],
            })
    site_data["mcps"] = mcps
    # 专家团面:只放出已过审 pack;成员为解析后状态(降级可见),不含任何密钥
    site_data["packs"] = [{
        "slug": p["slug"],
        "displayName": p["displayName"],
        "displayNameEn": p["displayNameEn"],
        "skill": p["skill"],
        "summary": p["summary"],
        "summaryEn": p["summaryEn"],
        "persona": {k: p["persona"].get(k, "") for k in ("role", "roleEn", "tagline", "taglineEn", "scene", "subScene", "avatar")},
        "origin": p["origin"],
        "memberCount": len(p["members"]),
        "members": [{"type": m.get("type"), "ref": m.get("ref"), "name": m.get("name", m.get("ref")), "resolved": m.get("resolved", False)} for m in p["members"]],
        "degraded": p["degraded"],
        "page": "/" + p["page"],
        "install": p["install"],
        "installPrompt": pack_install_prompt(p),
        "installDoc": "/install/pack-install.md",
        "detailApi": f"/v0/packs/{p['slug']}",
    } for p in packs]
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
    print(f"[+] 产物 {len(pages)} 页 + assets + {mmap_count} 导图 -> {DIST}(写入 {written},跳过 {skipped},清理 {removed};自研 {len(own)},套件 {len(suites)},专家团 {len(packs)})")
    update_site_data_icons()
    insert_detail_icons()
    inject_copy_config_buttons()
    inject_mcp_plugin_filters()
    append_card_icon_css()
    try:
        from render_tools_store import main as render_tools
        render_tools(ASSET_VER)
    except Exception as e:  # noqa: BLE001
        print("[!] 工具商店渲染失败:", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
