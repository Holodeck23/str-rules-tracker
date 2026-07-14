#!/usr/bin/env python3
"""Overnight source scanner. Zero dependencies.

Fetches every market's official source page, extracts main content, strips it to comparable text,
diffs against the stored snapshot, and writes scan-report.md flagging what
moved. The report is sorted by confidence using heuristic noise filtering.
Run daily (GitHub Action or launchd).
"""
import json, hashlib, pathlib, datetime, difflib, re, urllib.request, urllib.error, time

ROOT = pathlib.Path(__file__).parent
SNAP = ROOT / "snapshots"; SNAP.mkdir(exist_ok=True)
DATA = json.loads((ROOT / "data" / "markets.json").read_text())
TODAY = datetime.date.today().isoformat()
UA = {"User-Agent": "Mozilla/5.0 (STR-Register source monitor; contact: register@secondshift.agency)"}

NOISE_WORDS = ["termin", "kalender", "zoo", "festival", "concert", "veranstaltung", "spielenachmittag", "ferienprogramm", "krmení", "světového", "fiesta", "carmen", "exhibition", "ausstellung", "sport", "museum"]
SIGNAL_WORDS = ["law", "tax", "short-term", "rental", "ordinance", "ley", "impuesto", "alquiler", "turistico", "kurztrip", "tourismus", "gesetz", "verordnung", "regulamento", "licença", "zoning", "permit"]

def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as e:
            if attempt == retries - 1:
                raise e
            time.sleep(2 ** attempt)
    return ""

def strip_html(raw):
    # Try to extract just the main content to ignore noisy headers/footers/sidebars
    main_match = re.search(r"<main[^>]*>(.*?)</main>", raw, flags=re.S | re.I)
    if main_match:
        raw = main_match.group(1)
    else:
        article_match = re.search(r"<article[^>]*>(.*?)</article>", raw, flags=re.S | re.I)
        if article_match:
            raw = article_match.group(1)
        else:
            content_match = re.search(r"<div[^>]*(id|class)=[\"'](?:[^\"']*\s+)?(?:main|content|page-content)(?:\s+[^\"']*)?[\"'][^>]*>(.*?)</div>", raw, flags=re.S | re.I)
            if content_match:
                raw = content_match.group(2)

    raw = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"&[a-z#0-9]+;", " ", raw)
    # collapse whitespace; drop lines that churn on every load (dates, counters)
    lines = [ln.strip() for ln in re.sub(r"[ \t]+", " ", raw).splitlines()]
    return "\n".join(ln for ln in lines if len(ln) > 30)

def classify_diff(added, removed):
    combined_text = " ".join(added + removed).lower()
    if any(w in combined_text for w in SIGNAL_WORDS):
        return "high"
    if any(w in combined_text for w in NOISE_WORDS):
        return "fluff"
    return "unknown"

high_prob, fluff, unknown, errors, unchanged = [], [], [], [], []
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
    
    category = classify_diff(added, removed)
    item = (slug, url, added, removed)
    if category == "high":
        high_prob.append(item)
    elif category == "fluff":
        fluff.append(item)
    else:
        unknown.append(item)
        
    snap_file.write_text(text)  # advance snapshot; the report preserves the diff

total_changed = len(high_prob) + len(unknown) + len(fluff)
rep = [f"# Scan report — {TODAY}", ""]
rep.append(f"**{total_changed} changed · {len(errors)} unreachable · {len(unchanged)} unchanged/first-run**\n")

def append_category(title, items):
    if items:
        rep.append(f"## {title}\n")
        for slug, url, added, removed in items:
            rep.append(f"### {slug} — {url}")
            if added:
                rep.append("**Added:**")
                rep.extend([f"> + {l[:200]}" for l in added])
            if removed:
                rep.append("**Removed:**")
                rep.extend([f"> - {l[:200]}" for l in removed])
            rep.append("")

append_category("🚨 HIGH PROBABILITY RULE CHANGES", high_prob)
append_category("⚠ UNCATEGORIZED CHANGES (Please Review)", unknown)
append_category("ℹ LIKELY FLUFF (Zoo, Calendars, Events)", fluff)

if errors:
    rep.append("## ✗ Unreachable (check by hand)\n")
    rep += [f"- {s}: {u} — `{e[:120]}`" for s, u, e in errors]
    rep.append("")
rep.append("## Quiet\n")
rep += [f"- {s} ({note})" for s, note in unchanged]
(ROOT / "scan-report.md").write_text("\n".join(rep) + "\n")
print(f"scan {TODAY}: {total_changed} changed, {len(errors)} errors, {len(unchanged)} quiet -> scan-report.md")
