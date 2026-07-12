#!/usr/bin/env python3
"""STR Rules Tracker — static site generator. Zero dependencies.
Daily loop: edit data/markets.json (+ data/changelog.json on changes),
run `python3 build.py`, deploy. Never edit public/ by hand."""
import json, html, pathlib, datetime

ROOT = pathlib.Path(__file__).parent
PUB = ROOT / "public"
DATA = json.loads((ROOT / "data" / "markets.json").read_text())
CHANGELOG = json.loads((ROOT / "data" / "changelog.json").read_text())
TODAY = datetime.date.today().isoformat()
SITE = "The STR Register"
TAGLINE = "Short-term rental rules, city by city. Every claim dated, sourced, and checked by an operating host — not a content farm."
BASE = "https://str-rule-tracker.vercel.app"

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">'

CSS = """
:root{
--paper:#f6f1e7;--paper2:#efe7d6;--card:#fbf8f1;--ink:#1c1814;--ink-soft:#4a4034;--faint:#8a7c68;
--rule:#d8cdb8;--verify:#2d5f5d;--verify-soft:#e3ecea;--pend:#a06514;--pend-soft:#f3e8d2;
--change:#b3402f;--change-soft:#f4e2de;
--serif:'Fraunces',Georgia,serif;--mono:'JetBrains Mono',ui-monospace,Menlo,monospace}
@media(prefers-color-scheme:dark){:root{
--paper:#161310;--paper2:#1d1915;--card:#201c17;--ink:#ece5d8;--ink-soft:#c4b8a4;--faint:#8a7c68;
--rule:#3a332a;--verify:#5fae9d;--verify-soft:#1c2f2c;--pend:#d9a04a;--pend-soft:#332a17;
--change:#d97862;--change-soft:#33201b}}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--serif);margin:0;
padding:0 20px 70px;line-height:1.6;font-optical-sizing:auto;
background-image:radial-gradient(rgba(0,0,0,.022) 1px,transparent 1px);background-size:5px 5px}
.wrap{max-width:1020px;margin:0 auto}
a{color:inherit}
/* masthead */
.mast{border-bottom:3px double var(--ink);padding:30px 0 16px;margin-bottom:8px;text-align:center}
.mast .over{font-family:var(--mono);font-size:11px;letter-spacing:.32em;text-transform:uppercase;color:var(--faint);margin:0 0 10px}
.mast h1,.mast .h1{font-size:clamp(34px,6.5vw,62px);font-weight:900;letter-spacing:-.01em;margin:0;line-height:1.02}
.mast h1 a{text-decoration:none}
.mast .tag{font-style:italic;font-size:clamp(14px,2vw,17px);color:var(--ink-soft);margin:10px auto 0;max-width:62ch}
.dateline{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--ink);
padding:8px 2px;font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-soft);margin-bottom:34px}
.dateline b{color:var(--ink)}
/* stamps */
.stamp{display:inline-block;font-family:var(--mono);font-weight:700;font-size:10.5px;letter-spacing:.1em;
padding:3px 9px;border:2px solid;border-radius:3px;transform:rotate(-2deg);white-space:nowrap;text-transform:uppercase}
.stamp.ok{color:var(--verify);border-color:var(--verify);background:var(--verify-soft)}
.stamp.un{color:var(--pend);border-color:var(--pend);background:var(--pend-soft);border-style:dashed}
.stamp.chg{color:var(--change);border-color:var(--change);background:var(--change-soft)}
/* section heads */
h2{font-size:13px;font-family:var(--mono);font-weight:700;letter-spacing:.24em;text-transform:uppercase;
color:var(--ink);margin:48px 0 14px;display:flex;align-items:center;gap:14px}
h2::after{content:"";flex:1;border-top:1px solid var(--rule)}
h2 .n{color:var(--faint);font-weight:400}
/* register table */
.card{background:var(--card);border:1px solid var(--rule);border-radius:4px;overflow-x:auto;
box-shadow:0 1px 0 var(--rule),0 12px 30px -18px rgba(28,24,20,.25)}
table{width:100%;border-collapse:collapse;font-size:14px}
th{font-family:var(--mono);text-align:left;font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;
color:var(--faint);padding:14px 16px 10px;border-bottom:2px solid var(--ink);white-space:nowrap}
td{padding:13px 16px;border-bottom:1px solid var(--rule);vertical-align:top;font-size:13.5px;color:var(--ink-soft)}
tr:last-child td{border-bottom:none}
tr:hover td{background:var(--paper2)}
td.city{font-family:var(--serif);font-size:16px;font-weight:700;color:var(--ink);white-space:nowrap}
td.city a{text-decoration:none;border-bottom:2px solid var(--verify)}
td.city a:hover{color:var(--verify)}
td.city .co{display:block;font-family:var(--mono);font-weight:400;font-size:10px;letter-spacing:.14em;
text-transform:uppercase;color:var(--faint);margin-top:3px}
td.src{font-family:var(--mono);font-size:11px}
td.src a{color:var(--verify);text-decoration:none}td.src a:hover{text-decoration:underline}
/* ledger */
.ledger{background:var(--card);border:1px solid var(--rule);border-radius:4px;padding:8px 20px}
.ledger ul{list-style:none;margin:0;padding:0}
.ledger li{padding:12px 0;border-bottom:1px dashed var(--rule);font-size:14.5px;display:flex;gap:16px;align-items:baseline}
.ledger li:last-child{border-bottom:none}
.ledger .d{font-family:var(--mono);font-size:11.5px;color:var(--verify);font-weight:600;white-space:nowrap}
.ledger .empty{color:var(--faint);font-style:italic}
/* city page */
.back{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;
color:var(--verify);text-decoration:none;font-weight:700}
.back:hover{text-decoration:underline}
.cityhead{padding:34px 0 22px;border-bottom:3px double var(--ink);margin-bottom:26px}
.cityhead .co{font-family:var(--mono);font-size:11px;letter-spacing:.3em;text-transform:uppercase;color:var(--faint);margin:0 0 8px}
.cityhead h1{font-size:clamp(30px,5.5vw,52px);font-weight:900;margin:0 0 16px;line-height:1.05;text-wrap:balance}
.meta{display:flex;gap:18px;flex-wrap:wrap;align-items:center;font-family:var(--mono);font-size:12px}
.meta a{color:var(--verify)}
.notice{border:2px dashed var(--pend);background:var(--pend-soft);border-radius:4px;
padding:14px 18px;font-size:14.5px;margin:0 0 26px;color:var(--ink)}
.notice b{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--pend)}
dl{display:grid;grid-template-columns:210px 1fr;gap:0;margin:0;background:var(--card);
border:1px solid var(--rule);border-radius:4px;overflow:hidden}
dt{font-family:var(--mono);font-size:10.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
color:var(--faint);padding:15px 18px;border-bottom:1px solid var(--rule);background:var(--paper2)}
dd{margin:0;padding:13px 18px;font-size:15px;border-bottom:1px solid var(--rule);color:var(--ink-soft)}
dt:nth-last-of-type(1),dd:last-of-type{border-bottom:none}
.empty{color:var(--faint);font-style:italic;font-size:13.5px}
@media(max-width:640px){dl{grid-template-columns:1fr}dt{border-bottom:none;padding-bottom:2px}}
footer{margin-top:60px;border-top:3px double var(--ink);padding-top:16px;
font-family:var(--mono);font-size:11px;line-height:1.8;letter-spacing:.04em;color:var(--faint)}
"""

def stamp(m):
    if m["status"] == "VERIFIED":
        return f'<span class="stamp ok">✓ Verified {m["verified"]}</span>'
    return '<span class="stamp un">Unverified</span>'

def masthead(small=False):
    title = f'<p class="h1"><a href="/">{SITE}</a></p>' if small else f'<h1><a href="/">{SITE}</a></h1>'
    return f"""<header class="mast">
<p class="over">Registration · Night caps · Tourist tax · Enforcement</p>
{title}
<p class="tag">{TAGLINE}</p></header>
<div class="dateline"><span>Edition of <b>{TODAY}</b></span><span><b>{len(DATA["markets"])}</b> markets on the register</span><span><a href="/changelog" style="color:var(--verify)">Changelog</a></span></div>"""

def page(title, body, desc, canonical):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
{FONTS}<style>{CSS}</style></head><body><div class="wrap">{body}
<footer>{SITE} — a maintained register, updated daily. Rows stamped UNVERIFIED are seeded drafts awaiting an operator check; rely only on VERIFIED rows and always confirm with the linked official source. Nothing here is legal advice.</footer>
</div></body></html>"""

# ---- index ----
rows = ""
for m in sorted(DATA["markets"], key=lambda x: (x["country"], x["name"])):
    rows += (f'<tr><td class="city"><a href="/rules/{m["slug"]}">{html.escape(m["name"])}</a>'
             f'<span class="co">{html.escape(m["country"])}</span></td>'
             f'<td>{html.escape(m["registration"])}</td><td>{html.escape(m["cap"])}</td>'
             f'<td>{html.escape(m["tax"])}</td><td>{stamp(m)}</td>'
             f'<td class="src"><a href="{html.escape(m["source"])}" rel="nofollow">{html.escape(m["sourceName"])}</a></td></tr>')

recent = "".join(f'<li><span class="d">{html.escape(c["date"])}</span><span><b>{html.escape(c["market"])}</b> — {html.escape(c["change"])}</span></li>' for c in CHANGELOG["entries"][:8]) or '<li class="empty">No rule changes logged yet — the register opened July 2026. Changes appear here the day they are caught.</li>'

index_body = f"""{masthead()}
<h2>The Register <span class="n">— all markets</span></h2>
<div class="card"><table>
<tr><th>Market</th><th>Registration</th><th>Caps / limits</th><th>Tourist tax</th><th>Status</th><th>Official source</th></tr>
{rows}</table></div>
<h2>Recent changes</h2><div class="ledger"><ul>{recent}</ul></div>
"""
PUB.mkdir(exist_ok=True); (PUB / "rules").mkdir(exist_ok=True)
(PUB / "index.html").write_text(page(f"{SITE} — short-term rental rules by city, dated and sourced",
    index_body, TAGLINE, BASE + "/"))

# ---- city pages ----
DEPTH = [("process","Permit process"),("whoCanHost","Who can host"),("zones","Zone restrictions"),
         ("penalties","Penalties"),("enforcement","Platform enforcement")]
for m in DATA["markets"]:
    hist = "".join(f'<li><span class="d">{html.escape(h["date"])}</span><span>{html.escape(h["change"])}</span></li>'
                   for h in m.get("history", [])) or '<li class="empty">No changes recorded since tracking began (July 2026).</li>'
    depth = ""
    for key, label in DEPTH:
        val = m.get(key) or ""
        depth += f'<dt>{label}</dt><dd>{html.escape(val) if val else "<span class=empty>Not yet documented — added on a future verification pass.</span>"}</dd>'
    warn = "" if m["status"] == "VERIFIED" else '<div class="notice"><b>Unverified draft</b> — this entry was seeded from public knowledge and has not yet been checked against the official source. Verify before acting on it.</div>'
    body = f"""<div style="padding-top:26px"><a class="back" href="/">← The full register</a></div>
<div class="cityhead">
<p class="co">{html.escape(m["country"])}</p>
<h1>Short-term rental rules in {html.escape(m["name"])}</h1>
<div class="meta">{stamp(m)}<span>Official source: <a href="{html.escape(m["source"])}" rel="nofollow">{html.escape(m["sourceName"])}</a></span></div>
</div>
{warn}
<dl>
<dt>Registration</dt><dd>{html.escape(m["registration"])}</dd>
<dt>Caps / limits</dt><dd>{html.escape(m["cap"])}</dd>
<dt>Tourist tax</dt><dd>{html.escape(m["tax"])}</dd>
{depth}</dl>
<h2>Change history</h2><div class="ledger"><ul>{hist}</ul></div>
"""
    (PUB / "rules" / f'{m["slug"]}.html').write_text(page(
        f'Short-term rental rules in {m["name"]} ({m["country"]}) — {SITE}',
        body, f'Registration, night caps, and tourist tax for short-term rentals in {m["name"]}, dated and sourced.',
        f'{BASE}/rules/{m["slug"]}'))

# ---- changelog ----
all_log = "".join(f'<li><span class="d">{html.escape(c["date"])}</span><span><b>{html.escape(c["market"])}</b> — {html.escape(c["change"])}</span></li>' for c in CHANGELOG["entries"]) or '<li class="empty">No rule changes logged yet — the register opened July 2026.</li>'
(PUB / "changelog.html").write_text(page(f"Changelog — {SITE}",
    f'{masthead(small=True)}<h2>Every rule change, dated</h2><div class="ledger"><ul>{all_log}</ul></div>',
    "Dated log of every short-term rental rule change on the register.", BASE + "/changelog"))

# ---- sitemap + robots ----
urls = ["", "changelog"] + [f'rules/{m["slug"]}' for m in DATA["markets"]]
(PUB / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    "".join(f'<url><loc>{BASE}/{u}</loc><lastmod>{TODAY}</lastmod></url>' for u in urls) + "</urlset>")
(PUB / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")

print(f"built {2 + len(DATA['markets'])} pages -> public/")
