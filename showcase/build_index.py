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
}

CSS = """
:root{
  --ink:#14171C; --ink2:#5B626C; --ink3:#8A9099;
  --paper:#F7F8F9; --sheet:#FFFFFF; --rule:#DEE1E6;
  --signal:#2A5BD7; --marker:#E8B31C; --alert:#C0392B; --ok:#1F7A5C;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --mono:ui-monospace,SFMono-Regular,"JetBrains Mono","Cascadia Code",Consolas,monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{font-family:var(--sans);background:var(--paper);color:var(--ink);line-height:1.65;font-size:15px;-webkit-font-smoothing:antialiased}
a{color:var(--signal);text-decoration:none}
a:hover{text-decoration:underline}
:focus-visible{outline:2px solid var(--signal);outline-offset:2px}

/* 顶栏:取证索引式,底部细线,品牌等宽 */
.topnav{position:sticky;top:0;z-index:20;background:var(--sheet);border-bottom:1px solid var(--rule);display:flex;align-items:center;gap:2px;padding:0 20px;height:54px}
.topnav .brand{font-family:var(--mono);font-weight:700;font-size:15px;letter-spacing:.02em;margin-right:20px;color:var(--ink)}
.topnav a.nav{color:var(--ink2);padding:15px 12px;font-size:14px;border-bottom:2px solid transparent}
.topnav a.nav:hover{color:var(--ink);text-decoration:none}
.topnav a.nav.active{color:var(--ink);border-bottom-color:var(--signal);font-weight:600}
.lang-btn{margin-left:auto;font-family:var(--mono);font-size:12px;background:none;border:1px solid var(--rule);border-radius:2px;padding:5px 10px;color:var(--ink2);cursor:pointer}
.lang-btn:hover{border-color:var(--ink3);color:var(--ink)}

.wrap{max-width:1000px;margin:0 auto;padding:26px 20px 64px}
h1{font-size:28px;line-height:1.25;letter-spacing:-.01em;font-weight:700}
h2{font-size:17px;font-weight:700;margin:34px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--rule)}
.h2-sm{font-size:15px;margin-top:24px}
p{max-width:74ch}

/* 首页:索引式标题 + 推荐入口为主角 */
.hero{padding:30px 0 24px;border-bottom:1px solid var(--rule);margin-bottom:8px}
.hero h1{font-size:32px}
.hero .lede{font-size:15px;color:var(--ink2);margin-top:10px;max-width:70ch}
.hero .stats{display:flex;gap:28px;margin-top:20px}
.hero .stats b{font-family:var(--mono);font-size:22px;font-weight:600;display:block;line-height:1.2}
.hero .stats span{font-size:13px;color:var(--ink3)}

/* 推荐器:主入口 */
.finder{margin:22px 0 6px}
.finder textarea{width:100%;padding:14px 16px;border:1px solid var(--rule);border-radius:2px;font:14px/1.6 var(--sans);resize:vertical;background:var(--sheet);min-height:76px}
.finder textarea:focus{outline:none;border-color:var(--signal);box-shadow:0 0 0 3px rgba(42,91,215,.12)}
.finder .act{margin-top:10px;display:flex;gap:10px;flex-wrap:wrap}
.btn{font:inherit;font-size:14px;padding:9px 18px;border:1px solid var(--ink);background:var(--ink);color:#fff;border-radius:2px;cursor:pointer}
.btn:hover{background:#000}
.btn.ghost{background:var(--sheet);color:var(--ink);border-color:var(--rule)}
.btn.ghost:hover{border-color:var(--ink3)}

/* 搜索 + 分类筛选 */
.search{margin:0 0 4px;max-width:640px}
.search input{width:100%;padding:11px 14px;border:1px solid var(--rule);border-radius:2px;font:14px var(--sans);background:var(--sheet)}
.search input:focus{outline:none;border-color:var(--signal);box-shadow:0 0 0 3px rgba(42,91,215,.12)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 2px}
.chip{font-size:12.5px;padding:6px 12px;border:1px solid var(--rule);border-radius:2px;background:var(--sheet);cursor:pointer;color:var(--ink2)}
.chip:hover{border-color:var(--ink3)}
.chip.on{background:var(--ink);border-color:var(--ink);color:#fff}

/* 技能清单:行式(取证清单版式),非圆角卡片堆 */
.list{display:block}
.list>.row{display:grid;grid-template-columns:1fr auto;gap:6px 16px;padding:14px 4px;border-bottom:1px solid var(--rule);align-items:start}
.list>.row:hover{background:rgba(42,91,215,.035)}
.row .name{font-size:15.5px;font-weight:600}
.row .name a{color:var(--ink)}
.row .id{font-family:var(--mono);font-size:12px;color:var(--ink3);margin-top:2px;word-break:break-all}
.row .desc{font-size:13.5px;color:var(--ink2);margin-top:6px;grid-column:1/-1}
.row .facts{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--ink3);grid-column:1/-1;margin-top:2px;flex-wrap:wrap}
.tag{font-family:var(--mono);font-size:11px;padding:2px 7px;border:1px solid var(--rule);border-radius:2px;color:var(--ink2);white-space:nowrap}
.tag.kind-own{border-color:var(--marker);color:#7A5E00}
.tag.kind-ext{border-color:var(--rule);color:var(--ink2)}
.count{font-family:var(--mono);font-size:12px;color:var(--ink3);white-space:nowrap}

/* 兼容旧 grid 容器:整段作为清单 */
.grid{display:block}
.grid.grid-mt{margin-top:14px}

/* 详情页 */
.detail{background:var(--sheet);border:1px solid var(--rule);border-radius:2px;padding:26px 28px;margin-top:16px}
.detail h1{font-size:24px}
.detail .en-name{font-family:var(--mono);font-size:13px;color:var(--ink3);margin-top:6px}
.detail .desc{margin:16px 0;color:var(--ink);font-size:15px;white-space:pre-wrap}
.kv{display:grid;grid-template-columns:132px 1fr;gap:10px 16px;font-size:13.5px;margin:20px 0;padding:16px;background:var(--paper);border:1px solid var(--rule);border-radius:2px}
.kv dt{color:var(--ink3)}
.kv dd{font-family:var(--mono);word-break:break-all}
.kv a{color:var(--signal)}

/* 命令:等宽、可复制、仅墨黑底(不用终端绿) */
.cmd{background:var(--ink);color:#F2F4F7;padding:13px 15px;border-radius:2px;font:13px/1.5 var(--mono);overflow-x:auto;margin:12px 0;white-space:pre;user-select:all}

/* 安全审计:折叠块 */
details.audit{background:var(--sheet);border:1px solid var(--rule);border-radius:2px;margin-top:18px}
details.audit>summary{cursor:pointer;padding:14px 16px;display:flex;align-items:center;gap:10px;font-size:14px;list-style:none;border-left:3px solid transparent}
details.audit>summary::-webkit-details-marker{display:none}
details.audit[open]>summary{border-left-color:var(--marker);border-bottom:1px solid var(--rule)}
.grade{font-family:var(--mono);font-weight:700;font-size:14px;padding:2px 9px;border-radius:2px}
.grade-A{background:#E6F4EE;color:#1F7A5C}
.grade-A-{background:#F2F6E8;color:#5C7A1F}
.grade-B{background:#FBF3DC;color:#8A6410}
.grade-C{background:#FBE9E0;color:#A54818}
.grade-D{background:#FAE4E1;color:#A12A1C}
.audit-meta{font-size:12px;color:var(--ink3);margin-left:auto;font-family:var(--mono)}
.audit-body{padding:4px 16px 16px}
.lvl{font-family:var(--mono);font-size:11px;padding:1px 7px;border-radius:2px;white-space:nowrap}
.lvl-info{background:#EEF0F3;color:#5B626C}
.lvl-low{background:#F2F6E8;color:#5C7A1F}
.lvl-medium{background:#FBF3DC;color:#8A6410}
.lvl-high{background:#FBE9E0;color:#A54818}
.lvl-critical{background:#FAE4E1;color:#A12A1C}
.audit-detail{font-size:12.5px;color:var(--ink2);word-break:break-word;max-width:420px}

/* 表格:参数/审计明细 */
table.api{width:100%;border-collapse:collapse;font-size:13px;margin:14px 0;background:var(--sheet)}
table.api th,table.api td{border:1px solid var(--rule);padding:9px 11px;text-align:left;vertical-align:top}
table.api th{background:var(--paper);font-weight:600}

/* 导图 */
.mmap{background:var(--sheet);border:1px solid var(--rule);border-radius:2px;margin-top:16px;padding:12px;text-align:center}
.mmap img{max-width:100%;height:auto;display:block;margin:0 auto}

/* 套件区 */
.suite{margin-bottom:28px}
.suite h3{font-family:var(--mono);font-size:15px;font-weight:600;margin-bottom:10px}
.suite-meta{font-family:var(--sans);font-size:12.5px;color:var(--ink3);font-weight:400}
.suite-meta a{color:var(--signal)}
.notice{background:#FCFAF0;border:1px solid var(--marker);border-radius:2px;padding:13px 16px;font-size:13px;color:#6B5200;margin-top:14px}
.hint-warn{font-size:13px;color:#8A6410;margin-top:14px}
.hint-ok{font-size:13px;color:var(--ok);margin-top:14px}
.hint-dim{font-size:13px;color:var(--ink3);margin-top:10px;max-width:74ch}
.empty{color:var(--ink3);font-size:14px;padding:26px 4px}
.hidden{display:none!important}
code.inl{font-family:var(--mono);font-size:12px;background:#EEF0F3;padding:1px 5px;border-radius:2px}
footer{text-align:left;font-size:12.5px;color:var(--ink3);padding:24px 20px 40px;border-top:1px solid var(--rule);margin-top:40px}
footer a{color:var(--signal)}

/* 一次性入场:清单逐行浮现(像索引扫描),仅首屏前若干行 */
@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.list>.row{animation:rise .4s cubic-bezier(.2,.7,.3,1) backwards}
.list>.row:nth-child(1){animation-delay:.03s}
.list>.row:nth-child(2){animation-delay:.07s}
.list>.row:nth-child(3){animation-delay:.11s}
.list>.row:nth-child(4){animation-delay:.15s}
.list>.row:nth-child(5){animation-delay:.19s}
.list>.row:nth-child(6){animation-delay:.23s}
.list>.row:nth-child(7){animation-delay:.27s}
.list>.row:nth-child(8){animation-delay:.31s}

@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important}
}

/* 移动端 */
@media (max-width:760px){
  body{font-size:15.5px}
  .topnav{height:auto;padding:8px 12px;flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
  .topnav::-webkit-scrollbar{display:none}
  .topnav .brand{margin-right:14px;font-size:14px}
  .topnav a.nav{padding:8px 10px;font-size:13.5px;white-space:nowrap}
  .lang-btn{padding:5px 9px;font-size:12px}
  .wrap{padding:18px 14px 48px}
  h1{font-size:24px}
  .hero{padding:22px 0 18px}
  .hero h1{font-size:26px}
  .hero .stats{gap:20px}
  .hero .stats b{font-size:19px}
  .list>.row{grid-template-columns:1fr;gap:4px;padding:13px 2px}
  .count{align-self:start}
  .detail{padding:18px 16px}
  .kv{grid-template-columns:1fr;gap:4px}
  .cmd{font-size:12px;padding:11px 12px}
  table.api{display:block;overflow-x:auto;white-space:nowrap}
  .audit-detail{max-width:none;white-space:normal}
  .mmap{padding:8px}
  .btn{padding:11px 16px}
  footer{padding:20px 14px 32px}
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
  setLang(cur());
})();
"""


def esc(s):
    return html.escape(s or "", quote=True)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


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


def ns_slug(ns: str) -> str:
    return re.sub(r"[^\w.-]+", "--", ns)


def leak_assert(pages: dict, bodies):
    for path, text in pages.items():
        for body in bodies:
            for s in [ln.strip() for ln in body.splitlines() if len(ln.strip()) >= 40][:5]:
                if s in text or esc(s) in text:
                    raise SystemExit(f"[FAIL] 泄露断言命中 {path}: {s[:60]}...")
    print(f"[+] 泄露断言通过({len(pages)} 页 x {len(bodies)} 个自研正文)")


def nav(active="skills"):
    def cls(k):
        return ' class="nav active"' if k == active else ' class="nav"'
    return f'''<div class="topnav">
  <a class="brand" href="/">Skill X</a>
  <a href="/"{cls("skills")} data-zh="技能" data-en="Skills">技能</a>
  <a href="/recommend.html"{cls("recommend")} data-zh="技能推荐" data-en="Finder">技能推荐</a>
  <a href="/suites/"{cls("suites")} data-zh="套件" data-en="Suites">套件</a>
  <a href="/api.html"{cls("api")} data-zh="API 文档" data-en="API Docs">API 文档</a>
  <a href="/about.html"{cls("about")} data-zh="关于" data-en="About">关于</a>
  <button class="lang-btn">EN</button>
</div>'''


def page_shell(title, title_en, active, inner):
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Skill X</title>
<link rel="stylesheet" href="/assets/style.css">
</head><body>
{nav(active)}
<div class="wrap">{inner}</div>
<footer><a class="back" href="/">← <span data-zh="返回首页" data-en="Home">返回首页</span></a> · Skill X,Agent Skills 开放规范</footer>
<script src="/assets/app.js"></script>
</body></html>'''


def card(s, kind, page, stat_key):
    cat_label = CATEGORIES.get(s.get("category", ""), s.get("category", ""))
    if kind == "own":
        tag_cls, tag_text = "tag kind-own", "自研"
    else:
        tag_cls, tag_text = "tag kind-ext", "收录"
    search = f'{s["name"]} {s.get("name-zh","")} {s["description"]} {s.get("description-zh","")}'.lower()
    return f'''<div class="row" data-search="{esc(search)}" data-category="{esc(s.get("category",""))}">
  <div class="name"><a href="/{page}">{esc(s.get("name-zh", s["name"]))}</a></div>
  <div class="count" data-stat="{esc(stat_key)}">—</div>
  <div class="id">{esc(s["name"])}</div>
  <p class="desc"><span data-zh="{esc(s.get("description-zh",""))}" data-en="{esc(s["description"][:300])}">{esc(s.get("description-zh",""))}</span></p>
  <div class="facts"><span class="{tag_cls}">{tag_text}</span><span class="tag">{esc(cat_label)}</span></div>
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
  <div class="list">{items}</div>
</section>''')

    inner = f'''
<div class="hero">
  <h1>Skill X</h1>
  <p class="lede"><span data-zh="面向所有 Agent 的安全研究与逆向工程技能注册中心。自研技能经私有渠道授权分发;社区收录技能可一键指向上游安装。" data-en="Security research and reverse-engineering skills for all agents. Own skills via authorized private distribution; community skills install from upstream.">面向所有 Agent 的安全研究与逆向工程技能注册中心。自研技能经私有渠道授权分发;社区收录技能可一键指向上游安装。</span></p>
  <div class="stats">
    <span><b>{len(own)}</b><span data-zh="自研技能" data-en="Own skills">自研技能</span></span>
    <span><b>{total_ext}</b><span data-zh="社区精选" data-en="Curated">社区精选</span></span>
    <span><b>{len(suites)}</b><span data-zh="收录套件" data-en="Suites">收录套件</span></span>
  </div>
</div>
<div class="search"><input id="q" type="search" data-zh="搜索技能名称或关键词(如 逆向 / pentest / TDD)…" data-en="Search skills (e.g. reverse / pentest / TDD)…" data-attr="placeholder" placeholder="搜索技能名称或关键词(如 逆向 / pentest / TDD)…"></div>
{chips_html()}
<div id="empty" class="empty hidden" data-zh="没有匹配的技能" data-en="No matching skills">没有匹配的技能</div>
<h2 data-zh="自研技能" data-en="Own Skills">自研技能</h2>
<div class="list">{own_cards}</div>
<div class="notice"><span data-zh="自研技能经私有仓库授权分发。获得授权的协作者:" data-en="Own skills are distributed via a private repo. Authorized collaborators:">自研技能经私有仓库授权分发。获得授权的协作者:</span><code class="inl">GITHUB_TOKEN=&lt;PAT&gt; npx skills add JacksenHu/skill-x --skill &lt;name&gt;</code></div>
<h2 data-zh="社区精选" data-en="Curated">社区收录</h2>
{"".join(suite_sections) if suite_sections else "<p>暂无收录</p>"}'''
    return page_shell("Skill X — Agent Skills 注册中心", "Skill X", "skills", inner)


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
    <span data-zh="安全审计(点击展开明细)" data-en="Security audit (click to expand)">安全审计(点击展开明细)</span>
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


def render_own_detail(s, tool_entries=None, audit_entry=None, audit_at=""):
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
  <div class="mmap"><img src="/mindmaps/{esc(s["name"])}.svg" alt="思维导图"></div>
  <p class="hint-warn" data-zh="获得授权的协作者可安装:" data-en="Authorized collaborators can install:">获得授权的协作者可安装:</p>
  <div class="cmd">GITHUB_TOKEN=&lt;PAT&gt; npx skills add JacksenHu/skill-x --skill {esc(s["name"])}</div>
  <button class="chip on copy-btn" data-copy="GITHUB_TOKEN=<PAT> npx skills add JacksenHu/skill-x --skill {esc(s["name"])}" data-skill="{esc(s["name"])}" data-zh="复制安装命令" data-en="Copy install command">复制安装命令</button>
</div>
{tools_html}
{render_audit_block(audit_entry, audit_at)}'''
    return page_shell(s.get("name-zh", s["name"]), s["name"], "skills", inner)


def render_ext_detail(suite, s, audit_entry=None, audit_at=""):
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
  <div class="mmap"><a href="/suites/{ns_slug(ns)}.html"><img src="/mindmaps/suite-{ns_slug(ns)}.svg" alt="套件思维导图"></a></div>
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
    return page_shell("套件中心", "Suites", "suites", inner)


def render_suite_detail(suite):
    ns = suite["namespace"]
    lic = suite["license"]["spdx"]
    st = suite.get("stats") or {}
    stars = st.get("stars")
    forks = st.get("forks")
    total = suite.get("totalSkills", len(suite["skills"]))
    picked = len(suite["skills"])
    cards = "\n".join(card(s, "ext", f"../skills/ext-{ns_slug(ns)}--{s['name']}.html", f"{ns}/{s['name']}") for s in suite["skills"])
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
  <div class="mmap"><img src="/mindmaps/suite-{ns_slug(ns)}.svg" alt="套件思维导图"></div>
  <p class="hint-ok" data-zh="整套件安装(含全部上游技能):" data-en="Install whole suite (all upstream skills):">整套件安装(含全部上游技能):</p>
  <div class="cmd">npx skills add {esc(ns)} --skill '*'</div>
  <button class="chip on copy-btn" data-copy="npx skills add {esc(ns)} --skill '*'" data-skill="{esc(ns)}" data-zh="复制套件安装命令" data-en="Copy suite install command">复制套件安装命令</button>
  <p class="hint-dim" data-zh="注:上游套件共 {total} 个技能,本站按方向精选 {picked} 个展示;整套安装仍会包含上游全部技能。" data-en="Note: upstream ships {total} skills; {picked} are curated here; installing the suite still includes all upstream skills.">注:上游套件共 {total} 个技能,本站按方向精选 {picked} 个展示;整套安装仍会包含上游全部技能。</p>
</div>
<h2 data-zh="精选技能" data-en="Curated skills">精选技能</h2>
{chips_html()}
<div class="list">{cards}</div>'''
    return page_shell(ns, ns, "suites", inner)


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
</table>
<h2 class="h2-sm" data-zh="使用示例" data-en="Examples">使用示例</h2>
<div class="cmd">curl -s https://skillx.yueliai.top/api/stats</div>
<div class="cmd">curl -s -X POST -H "Content-Type: application/json" -d '{{"skill":"malware-analysis","action":"copy"}}' https://skillx.yueliai.top/api/download</div>
<div class="cmd">curl -s "https://skillx.yueliai.top/api/recommend?q=想给安卓apk脱壳"</div>
<div class="cmd">curl -s -X POST -H "Content-Type: application/json" -d '{{"query":"测试集体变红怎么排查"}}' https://skillx.yueliai.top/api/recommend</div>
<div class="cmd">curl -s https://skillx.yueliai.top/audit-report.json</div>
<div class="cmd">curl -sO https://skillx.yueliai.top/dl/addyosmani/agent-skills/test-driven-development.tar.gz</div>'''
    return page_shell("API 文档", "API Docs", "api", inner)


def render_recommend():
    inner = '''
<div class="hero">
  <h1 data-zh="技能推荐" data-en="Skill Finder">技能推荐</h1>
  <p class="lede" data-zh="描述你想做的事,从技能库里找出适用的技能 —— 支持自然语言,如「我想分析一个可疑的 exe」「帮我查这个网站的越权问题」「内存里找配置偏移」。" data-en="Describe what you want to do; we find matching skills. Natural language supported.">描述你想做的事,从技能库里找出适用的技能 —— 支持自然语言,如「我想分析一个可疑的 exe」「帮我查这个网站的越权问题」「内存里找配置偏移」。</p>
</div>
<div class="finder">
  <textarea id="idea" rows="3" data-zh="描述你的任务或想法…(Ctrl+Enter 查找)" data-en="Describe your task… (Ctrl+Enter to search)" data-attr="placeholder" placeholder="描述你的任务或想法…(Ctrl+Enter 查找)"></textarea>
  <div class="act"><button class="btn" id="find-btn" data-zh="查找适用技能" data-en="Find skills">查找适用技能</button></div>
</div>
<div id="rec-results" class="grid grid-mt"></div>
<div id="rec-empty" class="empty hidden" data-zh="没有匹配到技能,试着换个说法或输入更具体的任务。" data-en="No matching skills. Try different wording.">没有匹配到技能,试着换个说法或输入更具体的任务。</div>
<p class="hint-dim" data-zh="匹配方式:对输入做中英文分词,与技能名称、简介、分类交叉打分后排序;结果附命中理由。技能安装后由 agent 自动调用。" data-en="Matching: tokenized against skill names, descriptions and categories; results include match reasons.">匹配方式:对输入做中英文分词,与技能名称、简介、分类交叉打分后排序;结果附命中理由。技能安装后由 agent 自动调用。</p>'''
    return page_shell("技能推荐", "Skill Finder", "recommend", inner)


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
    stats = fetch_upstream_stats([s["namespace"] for s in suites])
    for s in suites:
        s["stats"] = stats.get(s["namespace"], {})

    pages = {"index.html": render_index(own, suites)}
    tool_docs = apidocs.collect()
    audit = load_audit()
    audit_at = audit.get("generatedAt", "")
    for s in own:
        pages[s["page"]] = render_own_detail(s, tool_docs.get(s["name"], []),
                                            (audit.get("skills") or {}).get(s["name"]), audit_at)
    pages["suites/index.html"] = render_suites_index(suites)
    for suite in suites:
        ns = suite["namespace"]
        pages[f"suites/{ns_slug(ns)}.html"] = render_suite_detail(suite)
        for s in suite["skills"]:
            pages[f"skills/ext-{ns_slug(ns)}--{s['name']}.html"] = render_ext_detail(
                suite, s, (audit.get("suites") or {}).get(ns), audit_at)
    pages["recommend.html"] = render_recommend()
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

    # 清理过时产物(已下架技能/套件/导图的残留文件,避免旧页面仍可访问)
    valid = set(new_manifest.keys())
    removed = 0
    for f in sorted(DIST.rglob("*")):
        if not f.is_file() or f.is_symlink():
            continue
        rel = str(f.relative_to(DIST)).replace("\\", "/")
        if rel.endswith((".html", ".svg")) and rel not in valid:
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
