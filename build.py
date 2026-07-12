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
SITE = "STR Rule Tracker"
TAGLINE = "Short-term rental rules, city by city. Every claim dated, sourced, and checked by an operating host — not a content farm."

CSS = """
:root{--bg:#f2f4f3;--card:#fff;--ink:#1c2b30;--muted:#5c6f75;--line:#d8dedc;
--accent:#0e7c66;--accent-soft:#e2f0ec;--amber:#b57614;--amber-soft:#f6ecd9;
--mono:ui-monospace,'SF Mono',Menlo,Consolas,monospace;
--sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
@media(prefers-color-scheme:dark){:root{--bg:#101a1c;--card:#172326;--ink:#e4ecea;
--muted:#8ba3a0;--line:#25373a;--accent:#3fbf9f;--accent-soft:#153730;--amber:#d9a04a;--amber-soft:#33290f}}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);font-family:var(--sans);
margin:0;padding:28px 18px 60px;line-height:1.55}
.wrap{max-width:960px;margin:0 auto}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 6px}
h1{font-size:clamp(24px,4vw,34px);margin:0 0 6px;letter-spacing:-.02em}
h2{font-size:15px;font-family:var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:34px 0 12px}
.sub{color:var(--muted);margin:0 0 8px;max-width:64ch}
.stamp{font-family:var(--mono);font-size:12.5px;color:var(--accent);margin:0 0 26px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:4px 18px 10px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13.5px;font-variant-numeric:tabular-nums}
th{text-align:left;color:var(--muted);font-family:var(--mono);font-weight:600;font-size:11px;
letter-spacing:.07em;text-transform:uppercase;padding:12px 14px 8px 0;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:10px 14px 10px 0;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
td a{color:var(--accent);text-decoration:none;font-weight:600}td a:hover{text-decoration:underline}
.chip{display:inline-block;border-radius:4px;padding:1px 7px;font-size:11px;font-weight:700;font-family:var(--mono);white-space:nowrap}
.chip.ok{background:var(--accent-soft);color:var(--accent)}
.chip.un{background:var(--amber-soft);color:var(--amber)}
.src{font-family:var(--mono);font-size:12px}
.note{background:var(--amber-soft);border:1px solid var(--amber);border-radius:8px;padding:10px 14px;
font-size:13.5px;margin:0 0 22px;color:var(--ink)}
dl{display:grid;grid-template-columns:190px 1fr;gap:10px 18px;margin:0}
dt{font-family:var(--mono);font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;padding-top:2px}
dd{margin:0;font-size:14.5px}
.empty{color:var(--muted);font-style:italic}
.back{font-family:var(--mono);font-size:13px;color:var(--accent);text-decoration:none}
footer{margin-top:40px;color:var(--muted);font-size:12.5px;font-family:var(--mono)}
.log li{margin-bottom:8px;font-size:14px}.log .d{font-family:var(--mono);color:var(--accent);font-size:12.5px}
"""

def page(title, body, desc, canonical):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<style>{CSS}</style></head><body><div class="wrap">{body}
<footer>{SITE} — updated {TODAY}. Rows marked UNVERIFIED are seeded drafts awaiting an operator check; treat only VERIFIED rows as reviewed. Nothing here is legal advice — always confirm with the linked official source.</footer>
</div></body></html>"""

def chip(m):
    if m["status"] == "VERIFIED":
        return f'<span class="chip ok">VERIFIED {m["verified"]}</span>'
    return '<span class="chip un">UNVERIFIED</span>'

# ---- index ----
rows = ""
for m in sorted(DATA["markets"], key=lambda x: (x["country"], x["name"])):
    rows += (f'<tr><td><a href="/rules/{m["slug"]}">{html.escape(m["name"])}</a><br>'
             f'<span class="src" style="color:var(--muted)">{html.escape(m["country"])}</span></td>'
             f'<td>{html.escape(m["registration"])}</td><td>{html.escape(m["cap"])}</td>'
             f'<td>{html.escape(m["tax"])}</td><td>{chip(m)}</td>'
             f'<td class="src"><a href="{html.escape(m["source"])}" rel="nofollow">{html.escape(m["sourceName"])}</a></td></tr>')

recent = "".join(f'<li><span class="d">{html.escape(c["date"])}</span> — <b>{html.escape(c["market"])}</b>: {html.escape(c["change"])}</li>' for c in CHANGELOG["entries"][:8]) or '<li class="empty">No rule changes logged yet — tracking started July 2026.</li>'

index_body = f"""
<p class="eyebrow">City-by-city · dated · sourced</p>
<h1>{SITE}</h1>
<p class="sub">{TAGLINE}</p>
<p class="stamp">Last updated {TODAY} · {len(DATA["markets"])} markets tracked · <a class="back" href="/changelog">full changelog →</a></p>
<div class="card"><table>
<tr><th>Market</th><th>Registration</th><th>Caps / limits</th><th>Tourist tax</th><th>Status</th><th>Source</th></tr>
{rows}</table></div>
<h2>Recent changes</h2><div class="card"><ul class="log">{recent}</ul></div>
"""
PUB.mkdir(exist_ok=True); (PUB / "rules").mkdir(exist_ok=True)
(PUB / "index.html").write_text(page(f"{SITE} — short-term rental rules by city",
    index_body, TAGLINE, "https://str-rule-tracker.vercel.app/"))

# ---- city pages ----
DEPTH = [("process","Permit process"),("whoCanHost","Who can host"),("zones","Zone restrictions"),
         ("penalties","Penalties"),("enforcement","Platform enforcement")]
for m in DATA["markets"]:
    hist = "".join(f'<li><span class="d">{html.escape(h["date"])}</span> — {html.escape(h["change"])}</li>'
                   for h in m.get("history", [])) or '<li class="empty">No changes recorded since tracking began (July 2026).</li>'
    depth = ""
    for key, label in DEPTH:
        val = m.get(key) or ""
        depth += f'<dt>{label}</dt><dd>{html.escape(val) if val else "<span class=empty>Not yet documented — added on a future verification pass.</span>"}</dd>'
    warn = "" if m["status"] == "VERIFIED" else '<div class="note"><b>Unverified draft.</b> This row was seeded from public knowledge and has not yet been checked against the official source below. Verify before acting on it.</div>'
    body = f"""
<a class="back" href="/">← all markets</a>
<p class="eyebrow" style="margin-top:18px">{html.escape(m["country"])}</p>
<h1>Short-term rental rules in {html.escape(m["name"])}</h1>
<p class="stamp">{chip(m)} · official source: <a class="back" href="{html.escape(m["source"])}" rel="nofollow">{html.escape(m["sourceName"])}</a></p>
{warn}
<div class="card" style="padding:18px"><dl>
<dt>Registration</dt><dd>{html.escape(m["registration"])}</dd>
<dt>Caps / limits</dt><dd>{html.escape(m["cap"])}</dd>
<dt>Tourist tax</dt><dd>{html.escape(m["tax"])}</dd>
{depth}</dl></div>
<h2>Change history</h2><div class="card"><ul class="log">{hist}</ul></div>
"""
    (PUB / "rules" / f'{m["slug"]}.html').write_text(page(
        f'Short-term rental rules in {m["name"]} ({m["country"]}) — {SITE}',
        body, f'Registration, night caps, and tourist tax for short-term rentals in {m["name"]}, dated and sourced.',
        f'https://str-rule-tracker.vercel.app/rules/{m["slug"]}'))

# ---- changelog page ----
all_log = "".join(f'<li><span class="d">{html.escape(c["date"])}</span> — <b>{html.escape(c["market"])}</b>: {html.escape(c["change"])}</li>' for c in CHANGELOG["entries"]) or '<li class="empty">No rule changes logged yet — tracking started July 2026.</li>'
(PUB / "changelog.html").write_text(page(f"Changelog — {SITE}",
    f'<a class="back" href="/">← all markets</a><h1>Every rule change, dated</h1><div class="card"><ul class="log">{all_log}</ul></div>',
    "Dated log of every short-term rental rule change we track.", "https://str-rule-tracker.vercel.app/changelog"))

# ---- sitemap + robots ----
urls = ["", "changelog"] + [f'rules/{m["slug"]}' for m in DATA["markets"]]
(PUB / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    "".join(f'<url><loc>https://str-rule-tracker.vercel.app/{u}</loc><lastmod>{TODAY}</lastmod></url>' for u in urls) + "</urlset>")
(PUB / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://str-rule-tracker.vercel.app/sitemap.xml\n")

print(f"built {2 + len(DATA['markets'])} pages -> public/")
