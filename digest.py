#!/usr/bin/env python3
"""Weekly digest generator. Zero dependencies (stdlib only).

Turns changelog entries into an email-ready issue: for each rule change, what
moved, what it does to a host's money/calendar, the action, and the deadline.
This is the paid product's raw material — the bar is "worth the subscription."

Usage:
    python3 digest.py                 # all entries, dated today
    python3 digest.py --since 2026-07-01
    python3 digest.py --date 2026-07-14   # stamp a specific issue date

Writes digests/<issue-date>.html (email-safe) and digests/<issue-date>.txt.
The HTML uses table layout + inline styles so it survives Gmail/Outlook.
"""
import argparse
import datetime
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "digests"; OUT.mkdir(exist_ok=True)
CHANGELOG = json.loads((ROOT / "data" / "changelog.json").read_text())
MARKETS = {m["slug"]: m for m in json.loads((ROOT / "data" / "markets.json").read_text())["markets"]}
BASE = "https://str-rule-tracker.vercel.app"
BRAND = "#2d5f5d"
SEV_COLOR = {"restricted": "#b3402f", "caution": "#a06514", "workable": "#3d6b34"}
SEV_LABEL = {"restricted": "Restricted", "caution": "Caution", "workable": "Workable"}


def market_of(entry):
    return MARKETS.get(entry.get("slug", ""), {})


def source_link(entry):
    m = market_of(entry)
    return m.get("source", BASE), m.get("sourceName", "official source")


def select(since):
    rows = CHANGELOG["entries"]
    if since:
        rows = [c for c in rows if c["date"] >= since]
    return sorted(rows, key=lambda c: c["date"], reverse=True)


# ---------- plain text ----------
def render_txt(entries, issue_date):
    L = []
    L.append("THE STR REGISTER — WEEKLY DIGEST")
    L.append(f"Issue of {issue_date}")
    L.append("=" * 52)
    L.append("")
    if not entries:
        L.append("Quiet week — no verified rule changes across the register.")
        L.append("Nothing to do. We only email when something actually moved.")
    else:
        n = len(entries)
        L.append(f"{n} rule change{'s' if n != 1 else ''} worth your attention this week.")
        L.append("")
        for i, c in enumerate(entries, 1):
            m = market_of(c)
            sev = c.get("severity") or m.get("severity", "")
            tag = f"[{SEV_LABEL.get(sev, '').upper()}] " if sev else ""
            L.append(f"{i}. {tag}{c['market'].upper()}")
            L.append("-" * 52)
            L.append(f"WHAT CHANGED: {c['change']}")
            if c.get("impact"):
                L.append("")
                L.append(f"WHAT IT MEANS: {c['impact']}")
            if c.get("action"):
                L.append("")
                L.append(f"DO THIS: {c['action']}")
            if c.get("deadline"):
                L.append(f"TIMING: {c['deadline']}")
            url, name = source_link(c)
            L.append(f"SOURCE: {name} — {url}")
            L.append(f"FULL ENTRY: {BASE}/rules/{c.get('slug', '')}")
            L.append("")
    L.append("=" * 52)
    L.append(f"The full register — {len(MARKETS)} markets, dated and sourced: {BASE}")
    L.append("You're getting this because you joined the STR Register digest.")
    L.append("Reply STOP to unsubscribe.")
    return "\n".join(L) + "\n"


# ---------- html (email-safe) ----------
def esc(s):
    return html.escape(s or "")


def render_html(entries, issue_date):
    blocks = []
    for c in entries:
        m = market_of(c)
        sev = c.get("severity") or m.get("severity", "caution")
        color = SEV_COLOR.get(sev, BRAND)
        url, name = source_link(c)
        rows = [
            f'<tr><td style="padding:0 0 6px"><span style="display:inline-block;font:700 11px/1 monospace;'
            f'letter-spacing:1px;text-transform:uppercase;color:#fff;background:{color};'
            f'padding:4px 9px;border-radius:3px">{esc(SEV_LABEL.get(sev, ""))}</span></td></tr>',
            f'<tr><td style="font:800 22px/1.2 Georgia,serif;color:#1c1814;padding:4px 0 12px">{esc(c["market"])}</td></tr>',
            f'<tr><td style="font:600 11px/1 monospace;letter-spacing:1px;text-transform:uppercase;'
            f'color:#8a7c68;padding:0 0 4px">What changed</td></tr>',
            f'<tr><td style="font:400 15px/1.6 Georgia,serif;color:#4a4034;padding:0 0 14px">{esc(c["change"])}</td></tr>',
        ]
        if c.get("impact"):
            rows.append(
                f'<tr><td style="font:600 11px/1 monospace;letter-spacing:1px;text-transform:uppercase;'
                f'color:{BRAND};padding:0 0 4px">What it means for you</td></tr>'
                f'<tr><td style="font:400 15px/1.65 Georgia,serif;color:#1c1814;padding:0 0 14px">{esc(c["impact"])}</td></tr>')
        if c.get("action"):
            rows.append(
                f'<tr><td style="padding:0 0 14px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
                f'style="background:#f3e8d2;border-left:4px solid {color};border-radius:0 6px 6px 0"><tr>'
                f'<td style="padding:12px 16px"><span style="font:700 11px/1 monospace;letter-spacing:1px;'
                f'text-transform:uppercase;color:{color}">Do this</span><br>'
                f'<span style="font:400 14px/1.55 Georgia,serif;color:#1c1814">{esc(c["action"])}</span>'
                + (f'<br><span style="font:600 12px/1.5 monospace;color:#8a7c68">Timing: {esc(c["deadline"])}</span>' if c.get("deadline") else "")
                + '</td></tr></table></td></tr>')
        rows.append(
            f'<tr><td style="font:400 12px/1.5 monospace;color:#8a7c68;padding:0 0 4px">'
            f'Source: <a href="{esc(url)}" style="color:{BRAND}">{esc(name)}</a> · '
            f'<a href="{BASE}/rules/{esc(c.get("slug", ""))}" style="color:{BRAND}">full entry</a></td></tr>')
        blocks.append(
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="background:#fcf9f2;border:1px solid #d8cdb8;border-top:4px solid {color};'
            f'border-radius:6px;margin:0 0 20px"><tr><td style="padding:20px 22px">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{"".join(rows)}</table>'
            f'</td></tr></table>')

    if not entries:
        blocks = ['<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
                  'style="background:#fcf9f2;border:1px solid #d8cdb8;border-radius:6px;margin:0 0 20px">'
                  '<tr><td style="padding:26px 22px;font:400 16px/1.6 Georgia,serif;color:#4a4034">'
                  'Quiet week — no verified rule changes across the register. Nothing for you to do. '
                  'We only email when a council actually moves.</td></tr></table>']

    n = len(entries)
    lede = ("Quiet week — nothing moved."
            if not entries else
            f"{n} rule change{'s' if n != 1 else ''} worth your attention this week.")
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#f5efe3;padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">
<tr><td style="padding:4px 4px 18px;border-bottom:2px solid #1c1814">
<span style="font:700 12px/1 monospace;letter-spacing:2px;text-transform:uppercase;color:{BRAND}">The STR Register</span>
<span style="font:400 12px/1 monospace;color:#8a7c68;float:right">Weekly digest · {issue_date}</span></td></tr>
<tr><td style="padding:22px 4px 18px;font:800 26px/1.2 Georgia,serif;color:#1c1814">{esc(lede)}</td></tr>
<tr><td>{"".join(blocks)}</td></tr>
<tr><td style="padding:8px 4px 4px;border-top:2px solid #1c1814">
<p style="font:400 14px/1.6 Georgia,serif;color:#4a4034;margin:14px 0">
The full register tracks {len(MARKETS)} markets, each dated and linked to its official source.
<a href="{BASE}" style="color:{BRAND};font-weight:700">Browse it here →</a></p>
<p style="font:400 11px/1.6 monospace;color:#8a7c68;margin:14px 0 0">
You're getting this because you joined the STR Register digest. This is information, not legal advice —
confirm against the official source before acting. <a href="mailto:register@secondshift.agency?subject=unsubscribe" style="color:#8a7c68">Unsubscribe</a>.</p>
</td></tr></table></td></tr></table></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    args = ap.parse_args()
    entries = select(args.since)
    (OUT / f"{args.date}.html").write_text(render_html(entries, args.date))
    (OUT / f"{args.date}.txt").write_text(render_txt(entries, args.date))
    print(f"digest {args.date}: {len(entries)} entr{'y' if len(entries)==1 else 'ies'} "
          f"-> digests/{args.date}.html + .txt")


if __name__ == "__main__":
    main()
