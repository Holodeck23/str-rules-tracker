#!/usr/bin/env python3
"""Overnight source scanner. Zero dependencies.

Fetches every market's official source page, strips it to comparable text,
diffs against the stored snapshot, and writes scan-report.md flagging what
moved. The HUMAN then reads the flagged pages and stamps the register —
this script never edits markets.json. Run daily (GitHub Action or launchd).
"""
import json, hashlib, pathlib, datetime, difflib, re, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).parent
SNAP = ROOT / "snapshots"; SNAP.mkdir(exist_ok=True)
DATA = json.loads((ROOT / "data" / "markets.json").read_text())
TODAY = datetime.date.today().isoformat()
UA = {"User-Agent": "Mozilla/5.0 (STR-Register source monitor; contact: register@secondshift.agency)"}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")

def strip_html(raw):
    raw = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"&[a-z#0-9]+;", " ", raw)
    # collapse whitespace; drop lines that churn on every load (dates, counters)
    lines = [ln.strip() for ln in re.sub(r"[ \t]+", " ", raw).splitlines()]
    return "\n".join(ln for ln in lines if len(ln) > 30)

changed, errors, unchanged = [], [], []
for m in DATA["markets"]:
    slug, url = m["slug"], m["source"]
    snap_file = SNAP / f"{slug}.txt"
    try:
        text = strip_html(fetch(url))
    except Exception as e:
        errors.append((slug, url, str(e)))
        continue
    if not snap_file.exists():
        snap_file.write_text(text)
        unchanged.append((slug, "first snapshot taken"))
        continue
    old = snap_file.read_text()
    if hashlib.sha256(old.encode()).hexdigest() == hashlib.sha256(text.encode()).hexdigest():
        unchanged.append((slug, "no change"))
        continue
    diff = list(difflib.unified_diff(old.splitlines(), text.splitlines(), lineterm="", n=0))
    added = [l[1:].strip() for l in diff if l.startswith("+") and not l.startswith("+++")][:12]
    removed = [l[1:].strip() for l in diff if l.startswith("-") and not l.startswith("---")][:12]
    changed.append((slug, url, added, removed))
    snap_file.write_text(text)  # advance snapshot; the report preserves the diff

rep = [f"# Scan report — {TODAY}", ""]
rep.append(f"**{len(changed)} changed · {len(errors)} unreachable · {len(unchanged)} unchanged/first-run**\n")
if changed:
    rep.append("## ⚠ CHANGED — review these, then stamp the register\n")
    for slug, url, added, removed in changed:
        rep.append(f"### {slug} — {url}")
        if added:
            rep.append("**Added:**")
            rep += [f"> + {l[:200]}" for l in added]
        if removed:
            rep.append("**Removed:**")
            rep += [f"> - {l[:200]}" for l in removed]
        rep.append("")
if errors:
    rep.append("## ✗ Unreachable (check by hand)\n")
    rep += [f"- {s}: {u} — `{e[:120]}`" for s, u, e in errors]
    rep.append("")
rep.append("## Quiet\n")
rep += [f"- {s} ({note})" for s, note in unchanged]
(ROOT / "scan-report.md").write_text("\n".join(rep) + "\n")
print(f"scan {TODAY}: {len(changed)} changed, {len(errors)} errors, {len(unchanged)} quiet -> scan-report.md")
