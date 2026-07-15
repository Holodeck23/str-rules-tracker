#!/usr/bin/env python3
"""The STR Register — static site generator. Zero dependencies (stdlib only).
Daily loop: edit data/markets.json (+ data/changelog.json on changes),
run `python3 build.py`, deploy. Never edit public/ by hand."""
import datetime
import html
import json
import pathlib

try:
    from zoneinfo import ZoneInfo
    NOW = datetime.datetime.now(ZoneInfo("Europe/Vienna"))
except Exception:
    NOW = datetime.datetime.utcnow()

ROOT = pathlib.Path(__file__).parent
PUB = ROOT / "public"
DATA = json.loads((ROOT / "data" / "markets.json").read_text())
CHANGELOG = json.loads((ROOT / "data" / "changelog.json").read_text())
TODAY = NOW.date()
BUILT = TODAY.isoformat()
# The data date the register asserts — NOT the build clock. This is the
# freshness the site is allowed to claim.
DATA_DATE = DATA.get("updated", BUILT)
SITE = "The STR Register"
BASE = "https://str-rule-tracker.vercel.app"
# Digest capture. Point this at an activated Formspree/FormSubmit/Buttondown
# endpoint. Until then the form degrades to a mailto (see JS + noscript).
FORM_ENDPOINT = DATA.get("digestEndpoint", "")
DIGEST_EMAIL = "register@secondshift.agency"
N = len(DATA["markets"])
VERIFIED_N = sum(1 for m in DATA["markets"] if m["status"] == "VERIFIED")
STALE_DAYS = 90      # a VERIFIED stamp older than this is flagged review-due
AGING_DAYS = 45      # softens the badge between fresh and stale
SEV = {
    "restricted": ("Restricted", "Effectively closed or hostile to new short-term rentals"),
    "caution":    ("Caution",    "Workable, but capped, zoned, or visibly tightening"),
    "workable":   ("Workable",   "Open with registration — do the paperwork and operate"),
}
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">'
FAVICON = '<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect x=%228%22 y=%2228%22 width=%2284%22 height=%2244%22 rx=%226%22 fill=%22none%22 stroke=%22%232d5f5d%22 stroke-width=%227%22 transform=%22rotate(-6 50 50)%22/><text x=%2250%22 y=%2262%22 font-size=%2230%22 font-family=%22monospace%22 font-weight=%22bold%22 fill=%22%232d5f5d%22 text-anchor=%22middle%22 transform=%22rotate(-6 50 50)%22>STR</text></svg>">'
OG_IMG = BASE + "/og.svg"


def parse_date(s):
    try:
        return datetime.date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def days_since(s):
    d = parse_date(s)
    return (TODAY - d).days if d else None


def human_age(n):
    if n is None:
        return ""
    if n <= 0:
        return "today"
    if n == 1:
        return "yesterday"
    if n < 30:
        return f"{n} days ago"
    if n < 60:
        return "about a month ago"
    months = round(n / 30)
    return f"about {months} months ago"


CSS = """
:root{
--paper:#f5efe3;--paper2:#ede4d0;--card:#fcf9f2;--ink:#1c1814;--ink-soft:#4a4034;--faint:#8a7c68;
--rule:#d8cdb8;--verify:#2d5f5d;--verify-soft:#e0ebe8;--pend:#a06514;--pend-soft:#f3e8d2;
--red:#b3402f;--red-soft:#f2ded9;--green:#3d6b34;--green-soft:#e2ebdc;
--serif:'Fraunces',Georgia,serif;--mono:'JetBrains Mono',ui-monospace,Menlo,monospace;
--shadow:0 1px 0 var(--rule),0 14px 34px -20px rgba(28,24,20,.35)}
@media(prefers-color-scheme:dark){:root{
--paper:#15120e;--paper2:#1c1813;--card:#211c15;--ink:#ece5d8;--ink-soft:#c4b8a4;--faint:#8a7c68;
--rule:#3a332a;--verify:#5fae9d;--verify-soft:#1b2c29;--pend:#d9a04a;--pend-soft:#332a17;
--red:#d97862;--red-soft:#33201b;--green:#8fbb84;--green-soft:#212b1d;
--shadow:0 1px 0 var(--rule),0 14px 34px -20px rgba(0,0,0,.6)}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--paper);color:var(--ink);font-family:var(--serif);margin:0;
padding:0 22px 70px;line-height:1.6;font-optical-sizing:auto;
background-image:radial-gradient(rgba(0,0,0,.022) 1px,transparent 1px);background-size:5px 5px}
.wrap{max-width:1080px;margin:0 auto}
a{color:inherit}
.top{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;
padding:16px 0;border-bottom:1px solid var(--rule);font-family:var(--mono);font-size:11.5px;
letter-spacing:.14em;text-transform:uppercase}
.top .brand{font-weight:700;text-decoration:none;display:flex;align-items:center;gap:9px}
.top .brand .seal{display:inline-flex;width:26px;height:26px;border:2px solid var(--verify);
border-radius:4px;transform:rotate(-6deg);align-items:center;justify-content:center;
color:var(--verify);font-size:9px;font-weight:700}
.top nav{display:flex;gap:22px}
.top nav a{text-decoration:none;color:var(--ink-soft)}
.top nav a:hover{color:var(--verify)}
.hero{padding:64px 0 30px;max-width:820px}
.hero .kick{font-family:var(--mono);font-size:11.5px;font-weight:700;letter-spacing:.3em;
text-transform:uppercase;color:var(--verify);margin:0 0 18px}
.hero h1{font-size:clamp(38px,6.4vw,72px);font-weight:850;line-height:1.02;letter-spacing:-.022em;
margin:0 0 20px;text-wrap:balance}
.hero h1 em{font-style:italic;color:var(--verify)}
.hero p{font-size:clamp(16px,2vw,19px);color:var(--ink-soft);max-width:58ch;margin:0 0 26px}
.hero .datestamp{display:inline-block;font-family:var(--mono);font-size:11px;font-weight:700;
letter-spacing:.12em;text-transform:uppercase;color:var(--verify);border:2px solid var(--verify);
background:var(--verify-soft);border-radius:4px;padding:5px 12px;transform:rotate(-2deg)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;
background:var(--rule);border:1px solid var(--rule);border-radius:6px;overflow:hidden;
margin:38px 0 0;box-shadow:var(--shadow)}
.stats div{background:var(--card);padding:16px 18px}
.stats b{display:block;font-size:30px;font-weight:800;line-height:1.1}
.stats span{font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--faint)}
h2{font-size:12.5px;font-family:var(--mono);font-weight:700;letter-spacing:.26em;text-transform:uppercase;
color:var(--ink);margin:58px 0 18px;display:flex;align-items:baseline;gap:14px}
h2::after{content:"";flex:1;border-top:1px solid var(--rule);transform:translateY(-3px)}
.toolbar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:0 0 20px}
.search{flex:1;min-width:220px;position:relative}
.search input{width:100%;font-family:var(--mono);font-size:13.5px;color:var(--ink);
background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:11px 14px 11px 38px;outline:none}
.search input:focus{border-color:var(--verify);box-shadow:0 0 0 3px var(--verify-soft)}
.search::before{content:"⌕";position:absolute;left:13px;top:50%;transform:translateY(-54%);
font-size:17px;color:var(--faint)}
.fbtn{font-family:var(--mono);font-size:10.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
background:var(--card);color:var(--ink-soft);border:1px solid var(--rule);border-radius:99px;
padding:7px 14px;cursor:pointer}
.fbtn[aria-pressed="true"]{border-color:var(--ink);background:var(--ink);color:var(--paper)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.mkt{position:relative;display:block;text-decoration:none;background:var(--card);
border:1px solid var(--rule);border-top:4px solid var(--sev);border-radius:6px;
padding:18px 20px 16px;box-shadow:var(--shadow);transition:transform .16s cubic-bezier(.2,.7,.3,1.2),border-color .16s}
.mkt:hover{transform:translateY(-3px);border-color:var(--sev)}
.mkt.restricted{--sev:var(--red)}.mkt.caution{--sev:var(--pend)}.mkt.workable{--sev:var(--green)}
.mkt .head{display:flex;justify-content:space-between;align-items:start;gap:10px}
.mkt h3{font-size:23px;font-weight:800;margin:0;line-height:1.1}
.mkt .co{font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--faint)}
.sevtag{font-family:var(--mono);font-size:9.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
color:var(--sev);border:1.5px solid var(--sev);border-radius:3px;padding:2px 7px;white-space:nowrap;transform:rotate(-2deg)}
.mkt .verdict{font-size:14.5px;font-style:italic;color:var(--ink-soft);margin:12px 0 14px;min-height:3em}
.mkt .foot{display:flex;justify-content:space-between;align-items:center;border-top:1px dashed var(--rule);
padding-top:10px;font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
.mkt .foot .st.ok{color:var(--verify);font-weight:700}
.mkt .foot .st.aging{color:var(--pend);font-weight:700}
.mkt .foot .st.un{color:var(--faint);font-weight:700}
.legend{display:flex;gap:20px;flex-wrap:wrap;margin:0 0 22px;font-family:var(--mono);font-size:11px;color:var(--ink-soft)}
.legend i{font-style:normal;display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:7px}
.ledger{background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:8px 22px;box-shadow:var(--shadow)}
.ledger ul{list-style:none;margin:0;padding:0}
.ledger li{padding:13px 0;border-bottom:1px dashed var(--rule);font-size:14.5px;display:flex;gap:18px;align-items:baseline}
.ledger li:last-child{border-bottom:none}
.ledger .d{font-family:var(--mono);font-size:11.5px;color:var(--verify);font-weight:700;white-space:nowrap}
.ledger .empty{color:var(--faint);font-style:italic}
.digest{margin-top:58px;background:var(--ink);color:var(--paper);border-radius:8px;
padding:38px 34px;box-shadow:var(--shadow)}
.digest .row{display:flex;gap:26px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.digest h2{color:var(--paper);margin:0 0 8px;display:block}
.digest h2::after{display:none}
.digest .big{font-family:var(--serif);font-size:clamp(22px,3vw,30px);font-weight:800;line-height:1.15;margin:0 0 8px;max-width:22ch}
.digest p{margin:0;color:color-mix(in srgb,var(--paper) 72%,transparent);font-size:14.5px;max-width:46ch}
.dform{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:4px}
.dform input[type=email]{font-family:var(--mono);font-size:13.5px;padding:14px 16px;border-radius:6px;
border:1px solid transparent;min-width:240px;flex:1;background:var(--paper);color:var(--ink);outline:none}
.dform input[type=email]:focus{box-shadow:0 0 0 3px color-mix(in srgb,var(--verify) 60%,transparent)}
.dform button{font-family:var(--mono);font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
color:var(--ink);background:var(--paper);border:0;border-radius:6px;padding:15px 26px;white-space:nowrap;cursor:pointer}
.dform button:hover{background:var(--verify);color:var(--paper)}
.dnote{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;margin-top:12px;
color:color-mix(in srgb,var(--paper) 55%,transparent)}
.dmsg{font-family:var(--mono);font-size:12.5px;margin-top:12px;min-height:1.2em}
.back{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;
color:var(--verify);text-decoration:none;font-weight:700}
.back:hover{text-decoration:underline}
.cityhead{padding:44px 0 26px;margin-bottom:30px;border-bottom:3px double var(--ink)}
.cityhead .co{font-family:var(--mono);font-size:11px;letter-spacing:.3em;text-transform:uppercase;color:var(--faint);margin:0 0 10px}
.cityhead h1{font-size:clamp(32px,5.5vw,56px);font-weight:850;margin:0 0 18px;line-height:1.04;text-wrap:balance}
.meta{display:flex;gap:16px;flex-wrap:wrap;align-items:center;font-family:var(--mono);font-size:12px}
.meta a{color:var(--verify)}
.verdictbox{border-left:5px solid var(--sev);background:var(--card);border-radius:0 6px 6px 0;
padding:18px 22px;margin:0 0 26px;box-shadow:var(--shadow)}
.verdictbox.restricted{--sev:var(--red)}.verdictbox.caution{--sev:var(--pend)}.verdictbox.workable{--sev:var(--green)}
.verdictbox .lbl{font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--sev)}
.verdictbox p{margin:6px 0 0;font-size:clamp(16px,2.2vw,20px);font-style:italic;line-height:1.45}
.stamp{display:inline-block;font-family:var(--mono);font-weight:700;font-size:10.5px;letter-spacing:.1em;
padding:3px 10px;border:2px solid;border-radius:3px;transform:rotate(-2deg);white-space:nowrap;text-transform:uppercase}
.stamp.ok{color:var(--verify);border-color:var(--verify);background:var(--verify-soft)}
.stamp.aging{color:var(--pend);border-color:var(--pend);background:var(--pend-soft)}
.stamp.un{color:var(--faint);border-color:var(--faint);background:transparent;border-style:dashed}
.notice{border:2px dashed var(--pend);background:var(--pend-soft);border-radius:6px;
padding:14px 18px;font-size:14.5px;margin:0 0 26px}
.notice b{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--pend)}
dl{display:grid;grid-template-columns:220px 1fr;margin:0;background:var(--card);
border:1px solid var(--rule);border-radius:6px;overflow:hidden;box-shadow:var(--shadow)}
dt{font-family:var(--mono);font-size:10.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
color:var(--faint);padding:16px 20px;border-bottom:1px solid var(--rule);background:var(--paper2)}
dd{margin:0;padding:14px 20px;font-size:15px;border-bottom:1px solid var(--rule);color:var(--ink-soft)}
dl dt:last-of-type,dl dd:last-of-type{border-bottom:none}
.empty{color:var(--faint);font-style:italic;font-size:13.5px}
@media(max-width:640px){dl{grid-template-columns:1fr}dt{border-bottom:none;padding-bottom:2px}
.digest{padding:28px 22px}.stats{grid-template-columns:repeat(2,1fr)}}
footer{margin-top:64px;border-top:3px double var(--ink);padding-top:18px;
font-family:var(--mono);font-size:11px;line-height:1.9;letter-spacing:.04em;color:var(--faint)}
footer a{color:var(--verify)}
.notfound{padding:90px 0;text-align:center}
.notfound h1{font-size:clamp(40px,8vw,90px);margin:0 0 10px}
"""

JS = """
const q=document.getElementById('q'),cards=[...document.querySelectorAll('.mkt')],
btns=[...document.querySelectorAll('.fbtn')];let sev='all';
function apply(){const t=(q.value||'').toLowerCase();cards.forEach(c=>{
const okT=!t||c.dataset.name.includes(t)||c.dataset.country.includes(t);
const okS=sev==='all'||c.classList.contains(sev);
c.style.display=okT&&okS?'':'none';});}
q&&q.addEventListener('input',apply);
btns.forEach(b=>b.addEventListener('click',()=>{sev=b.dataset.sev;
btns.forEach(x=>x.setAttribute('aria-pressed',x===b));apply();}));
const f=document.getElementById('digestform');
if(f){f.addEventListener('submit',async e=>{
const ep=f.dataset.endpoint,msg=document.getElementById('dmsg');
if(!ep){return;/* no endpoint set: let the mailto fallback link handle it */}
e.preventDefault();msg.textContent='Sending…';
try{const r=await fetch(ep,{method:'POST',headers:{'Accept':'application/json'},body:new FormData(f)});
if(r.ok){f.reset();msg.textContent='✓ You are on the list. First edition on its way.';}
else{msg.innerHTML='Something went wrong — email <a style="color:inherit" href="mailto:'+f.dataset.email+'">'+f.dataset.email+'</a> instead.';}}
catch(err){msg.innerHTML='Offline? Email <a style="color:inherit" href="mailto:'+f.dataset.email+'">'+f.dataset.email+'</a> to join.';}
});}
"""


def stamp(m):
    if m["status"] != "VERIFIED":
        return '<span class="stamp un">Unverified draft</span>'
    age = days_since(m.get("verified", ""))
    when = human_age(age)
    if age is not None and age > STALE_DAYS:
        return f'<span class="stamp aging" title="Re-check due">✓ Verified {when} · review due</span>'
    if age is not None and age > AGING_DAYS:
        return f'<span class="stamp aging">✓ Verified {when}</span>'
    return f'<span class="stamp ok">✓ Verified {when}</span>'


def card_status(m):
    if m["status"] != "VERIFIED":
        return '<span class="st un">unverified</span>'
    age = days_since(m.get("verified", ""))
    cls = "aging" if (age is not None and age > AGING_DAYS) else "ok"
    return f'<span class="st {cls}">✓ verified {human_age(age)}</span>'


def topbar():
    return f"""<div class="top"><a class="brand" href="/"><span class="seal">STR</span>{SITE}</a>
<nav><a href="/#register">Markets</a><a href="/changelog">Changelog</a><a href="/#digest">Weekly digest</a></nav></div>"""


def page(title, body, desc, canonical, js="", jsonld=None, is404=False):
    script = f"<script>{js}</script>" if js else ""
    ld = ""
    if jsonld:
        ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>'
    robots = '<meta name="robots" content="noindex">' if is404 else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">{robots}
<meta property="og:type" content="website"><meta property="og:site_name" content="{html.escape(SITE)}">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{OG_IMG}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}"><meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{OG_IMG}">
<link rel="alternate" type="application/rss+xml" title="{html.escape(SITE)} — rule changes" href="{BASE}/feed.xml">
{FAVICON}{FONTS}<style>{CSS}</style>{ld}</head><body><div class="wrap">{topbar()}{body}
<footer>{SITE} — a maintained register. {VERIFIED_N} of {N} markets are operator-verified against their official source; entries marked <b>Unverified draft</b> are seeded from public knowledge and awaiting a check. Rely on verified entries, and always confirm against the linked official source before acting. Nothing here is legal advice. · <a href="/changelog">Changelog</a> · <a href="/feed.xml">RSS</a></footer>
{script}</div></body></html>"""


def digest_section():
    if FORM_ENDPOINT:
        form = f"""<form id="digestform" class="dform" data-endpoint="{html.escape(FORM_ENDPOINT)}" data-email="{DIGEST_EMAIL}" method="post" action="{html.escape(FORM_ENDPOINT)}">
<input type="email" name="email" required placeholder="you@example.com" aria-label="Your email">
<button type="submit">Join the digest</button></form>
<div id="dmsg" class="dmsg" role="status" aria-live="polite"></div>"""
    else:
        form = f"""<form id="digestform" class="dform" data-endpoint="" data-email="{DIGEST_EMAIL}"
action="mailto:{DIGEST_EMAIL}?subject=Digest%20waitlist&body=Add%20me%20to%20the%20STR%20Register%20weekly%20digest." method="get">
<input type="email" name="email" required placeholder="you@example.com" aria-label="Your email">
<button type="submit">Join the digest</button></form>
<div id="dmsg" class="dmsg" role="status" aria-live="polite"></div>"""
    return f"""<section class="digest" id="digest">
<div class="row"><div><p class="big">One email a week: what changed, and what it means for hosts.</p>
<p>Assembled from this ledger — every rule change across {N} markets, translated into what it does to your calendar, your permit status, and your tax bill. No listicles, no filler.</p></div></div>
{form}
<p class="dnote">Free. One email a week. Unsubscribe anytime.</p></section>"""


# ---- index ----
counts = {k: sum(1 for m in DATA["markets"] if m["severity"] == k) for k in SEV}
cards = ""
for m in sorted(DATA["markets"], key=lambda x: (x["country"], x["name"])):
    cards += f"""<a class="mkt {m["severity"]}" href="/rules/{m["slug"]}" data-name="{html.escape(m["name"].lower(), quote=True)}" data-country="{html.escape(m["country"].lower(), quote=True)}">
<div class="head"><div><h3>{html.escape(m["name"])}</h3><span class="co">{html.escape(m["country"])}</span></div>
<span class="sevtag">{SEV[m["severity"]][0]}</span></div>
<p class="verdict">{html.escape(m["verdict"])}</p>
<div class="foot">{card_status(m)}<span>Full entry →</span></div></a>"""

recent = "".join(f'<li><span class="d">{html.escape(c["date"])}</span><span><b>{html.escape(c["market"])}</b> — {html.escape(c["change"])}</span></li>' for c in CHANGELOG["entries"][:8]) or f'<li class="empty">No rule changes logged yet — the register opened July 2026. From here, every change to any of the {N} markets appears in this ledger, dated, the day it is caught.</li>'

index_body = f"""
<section class="hero">
<p class="kick">The short-term rental rulebook, kept current</p>
<h1>Know the rules <em>before</em> the city knows you.</h1>
<p>Registration, night caps, and tourist taxes for {N} major markets. {VERIFIED_N} are verified against their official source and dated; the rest are seeded drafts, clearly marked. When a council moves, the ledger records it.</p>
<span class="datestamp">Register current as of {DATA_DATE}</span>
<div class="stats">
<div><b>{N}</b><span>markets tracked</span></div>
<div><b>{VERIFIED_N}</b><span>operator-verified</span></div>
<div><b>{counts["restricted"]}</b><span>restricted</span></div>
<div><b>{counts["workable"]}</b><span>workable</span></div>
</div>
</section>
<h2 id="register">The register</h2>
<div class="legend">
<span><i style="background:var(--red)"></i>{SEV["restricted"][1]}</span>
<span><i style="background:var(--pend)"></i>{SEV["caution"][1]}</span>
<span><i style="background:var(--green)"></i>{SEV["workable"][1]}</span>
</div>
<div class="toolbar">
<div class="search"><input id="q" type="search" placeholder="Search city or country…" aria-label="Search markets"></div>
<button class="fbtn" data-sev="all" aria-pressed="true">All</button>
<button class="fbtn" data-sev="restricted" aria-pressed="false">Restricted</button>
<button class="fbtn" data-sev="caution" aria-pressed="false">Caution</button>
<button class="fbtn" data-sev="workable" aria-pressed="false">Workable</button>
</div>
<div class="grid">{cards}</div>
<h2>Recent changes</h2>
<div class="ledger"><ul>{recent}</ul></div>
{digest_section()}
"""

index_ld = {
    "@context": "https://schema.org", "@type": "Dataset",
    "name": SITE, "url": BASE + "/",
    "description": f"Short-term rental registration rules, night caps and tourist taxes for {N} cities worldwide, dated and sourced.",
    "dateModified": DATA_DATE,
    "creator": {"@type": "Organization", "name": "Second Shift"},
    "keywords": "short-term rental, Airbnb regulation, STR rules, tourist tax, night cap",
}
PUB.mkdir(exist_ok=True); (PUB / "rules").mkdir(exist_ok=True)
(PUB / "index.html").write_text(page(
    f"{SITE} — short-term rental rules by city, dated and sourced",
    index_body,
    f"Registration, night caps and tourist taxes for {N} cities — {VERIFIED_N} operator-verified against official sources, all dated. Know the rules before the city knows you.",
    BASE + "/", js=JS, jsonld=index_ld))

# ---- city pages ----
DEPTH = [("process", "Permit process"), ("whoCanHost", "Who can host"), ("zones", "Zone restrictions"),
         ("penalties", "Penalties"), ("enforcement", "Platform enforcement")]
for m in DATA["markets"]:
    hist = "".join(f'<li><span class="d">{html.escape(h["date"])}</span><span>{html.escape(h["change"])}</span></li>'
                   for h in m.get("history", [])) or '<li class="empty">No changes recorded since tracking began (July 2026).</li>'
    depth = ""
    for key, label in DEPTH:
        val = m.get(key) or ""
        if val:
            depth += f'<dt>{label}</dt><dd>{html.escape(val)}</dd>'
    warn = "" if m["status"] == "VERIFIED" else '<div class="notice"><b>Unverified draft</b> — this entry was seeded from public knowledge and has not yet been checked against the official source. Verify before acting on it.</div>'
    body = f"""<div style="padding-top:26px"><a class="back" href="/#register">← The full register</a></div>
<div class="cityhead">
<p class="co">{html.escape(m["country"])}</p>
<h1>Short-term rental rules in {html.escape(m["name"])}</h1>
<div class="meta">{stamp(m)}<span>Official source: <a href="{html.escape(m["source"])}" rel="nofollow noopener" target="_blank">{html.escape(m["sourceName"])}</a></span></div>
</div>
<div class="verdictbox {m["severity"]}"><span class="lbl">{SEV[m["severity"]][0]} — operator's read</span>
<p>{html.escape(m["verdict"])}</p></div>
{warn}
<dl>
<dt>Registration</dt><dd>{html.escape(m["registration"])}</dd>
<dt>Caps / limits</dt><dd>{html.escape(m["cap"])}</dd>
<dt>Tourist tax</dt><dd>{html.escape(m["tax"])}</dd>
{depth}</dl>
<h2>Change history</h2><div class="ledger"><ul>{hist}</ul></div>
"""
    # FAQ structured data — the exact shape answer engines quote.
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": f"Can I run a short-term rental in {m['name']}?",
             "acceptedAnswer": {"@type": "Answer", "text": m["verdict"]}},
            {"@type": "Question", "name": f"Do I need to register a short-term rental in {m['name']}?",
             "acceptedAnswer": {"@type": "Answer", "text": m["registration"]}},
            {"@type": "Question", "name": f"Is there a night cap for short-term rentals in {m['name']}?",
             "acceptedAnswer": {"@type": "Answer", "text": m["cap"]}},
            {"@type": "Question", "name": f"What tourist tax applies to short-term rentals in {m['name']}?",
             "acceptedAnswer": {"@type": "Answer", "text": m["tax"]}},
        ],
    }
    verified_note = f" Verified {m['verified']}." if m["status"] == "VERIFIED" else " Unverified draft — confirm with the official source."
    (PUB / "rules" / f'{m["slug"]}.html').write_text(page(
        f'Short-term rental rules in {m["name"]} ({m["country"]}) — {SITE}',
        body, f'{m["name"]}: {m["verdict"]} Registration, night caps and tourist tax, dated and sourced.{verified_note}',
        f'{BASE}/rules/{m["slug"]}', jsonld=faq))

# ---- changelog ----
all_log = "".join(f'<li><span class="d">{html.escape(c["date"])}</span><span><b>{html.escape(c["market"])}</b> — {html.escape(c["change"])}</span></li>' for c in CHANGELOG["entries"]) or '<li class="empty">No rule changes logged yet — the register opened July 2026.</li>'
(PUB / "changelog.html").write_text(page(f"Changelog — {SITE}",
    f'<div class="cityhead"><p class="co">The ledger</p><h1>Every rule change, dated</h1></div><div class="ledger"><ul>{all_log}</ul></div>',
    "Dated log of every short-term rental rule change on the register — night caps, tourist taxes, registration regimes.", BASE + "/changelog"))

# ---- 404 ----
(PUB / "404.html").write_text(page(f"Not found — {SITE}",
    '<div class="notfound"><h1>404</h1><p>That page isn\'t on the register.</p><p><a class="back" href="/#register">← Back to the full register</a></p></div>',
    "Page not found.", BASE + "/404", is404=True))

# ---- og image (self-contained SVG) ----
(PUB / "og.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">'
    f'<rect width="1200" height="630" fill="#f5efe3"/>'
    f'<rect x="70" y="150" width="150" height="80" rx="10" fill="none" stroke="#2d5f5d" stroke-width="9" transform="rotate(-6 145 190)"/>'
    f'<text x="145" y="205" font-size="40" font-family="monospace" font-weight="bold" fill="#2d5f5d" text-anchor="middle" transform="rotate(-6 145 190)">STR</text>'
    f'<text x="70" y="360" font-size="76" font-family="Georgia,serif" font-weight="800" fill="#1c1814">Know the rules before</text>'
    f'<text x="70" y="450" font-size="76" font-family="Georgia,serif" font-weight="800" fill="#1c1814">the city knows you.</text>'
    f'<text x="70" y="540" font-size="30" font-family="monospace" fill="#2d5f5d">{SITE} · {N} markets · {VERIFIED_N} verified</text>'
    f'</svg>')

# ---- RSS feed of the changelog ----
def rfc822(s):
    d = parse_date(s) or TODAY
    return datetime.datetime(d.year, d.month, d.day, 12, 0, 0).strftime("%a, %d %b %Y %H:%M:%S +0000")

items = "".join(
    f'<item><title>{html.escape(c["market"])} — rule change</title>'
    f'<link>{BASE}/changelog</link>'
    f'<guid isPermaLink="false">{html.escape(c["date"] + "-" + c["market"])}</guid>'
    f'<pubDate>{rfc822(c["date"])}</pubDate>'
    f'<description>{html.escape(c["change"])}</description></item>'
    for c in CHANGELOG["entries"])
(PUB / "feed.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<rss version="2.0"><channel>'
    f'<title>{html.escape(SITE)} — rule changes</title>'
    f'<link>{BASE}/changelog</link>'
    f'<description>Every short-term rental rule change on the register, dated.</description>'
    f'<language>en</language><lastBuildDate>{rfc822(BUILT)}</lastBuildDate>'
    f'{items}</channel></rss>')

# ---- sitemap + robots ----
def lastmod(m):
    return m.get("verified") or m.get("lastChange") or DATA_DATE

sm = [("", DATA_DATE), ("changelog", CHANGELOG["entries"][0]["date"] if CHANGELOG["entries"] else DATA_DATE)]
sm += [(f'rules/{m["slug"]}', lastmod(m)) for m in DATA["markets"]]
(PUB / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    "".join(f'<url><loc>{BASE}/{u}</loc><lastmod>{d}</lastmod></url>' for u, d in sm) + "</urlset>")
(PUB / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
print(f"built {3 + N} pages + feed.xml + og.svg -> public/ (data current {DATA_DATE})")
