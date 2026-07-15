#!/usr/bin/env python3
"""Overnight source scanner. Zero dependencies (stdlib only).

Fetches every market's official source page(s), extracts the main content,
strips it to comparable text, diffs against the stored snapshot, classifies
each diff as signal or noise, and writes a dated report. The HUMAN then reads
the flagged pages and stamps the register — this script NEVER edits
markets.json.

Loud-failure contract (the part that makes the register trustworthy):
- data/scan-state.json tracks consecutive fetch failures per source.
- A source failing >= DEAD_AFTER days is escalated as DEAD in the report.
- scan-alert.txt is written when anything needs a human (high-signal change
  or dead source). The GitHub workflow fails the run AFTER committing, so
  GitHub's failure email becomes the notification channel.
"""
import datetime
import difflib
import hashlib
import html as html_mod
import json
import pathlib
import re
import time
import urllib.error
import urllib.request

try:
    from zoneinfo import ZoneInfo
    NOW = datetime.datetime.now(ZoneInfo("Europe/Vienna"))
except Exception:  # zoneinfo data absent on some minimal runners
    NOW = datetime.datetime.utcnow()

ROOT = pathlib.Path(__file__).parent
SNAP = ROOT / "snapshots"; SNAP.mkdir(exist_ok=True)
REPORTS = ROOT / "reports"; REPORTS.mkdir(exist_ok=True)
DATA = json.loads((ROOT / "data" / "markets.json").read_text())
STATE_FILE = ROOT / "data" / "scan-state.json"
ALERT_FILE = ROOT / "scan-alert.txt"
TODAY = NOW.date().isoformat()
DEAD_AFTER = 3  # consecutive failed days before a source is declared dead

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en,de;q=0.8,es;q=0.6,fr;q=0.6,pt;q=0.6,it;q=0.6,nl;q=0.6",
}

# Diff classification. A change mentioning any signal term is worth a human's
# morning; noise terms are the recurring event/culture churn of city portals.
SIGNAL_WORDS = [
    # en
    "short-term", "short term", "rental", "ordinance", " law", "regulation",
    "registration", "register", "permit", "licence", "license", "zoning",
    "night", "cap", " tax", "fine", "penalt", "enforce", "host", "airbnb",
    "occupancy", "dwelling",
    # de
    "gesetz", "verordnung", "genehmigung", "bewilligung", "anmeldung",
    "registrierung", "zweckentfremdung", "kurzzeitvermietung", "ortstaxe",
    "abgabe", "steuer", "wohnraum", "nächte", "strafe", "bußgeld",
    # es
    "ley", "impuesto", "alquiler", "turístico", "turistica", "licencia",
    "registro", "vivienda", "sanción", "multa",
    # fr
    "meublé", "location", "enregistrement", "taxe", "séjour", "amende",
    # pt
    "regulamento", "licença", "alojamento", "contribuição", "coima",
    # it
    "locazion", "turistich", "regolamento", "sanzion", "soggiorno",
    # nl
    "vergunning", "vakantieverhuur", "nachten", "belasting", "boete",
    "registratie", "huisvesting",
]
NOISE_WORDS = [
    "cookie", "festival", "concert", "exhibition", "ausstellung", "museum",
    "veranstaltung", "termin", "kalender", "zoo", "sport", "spielenachmittag",
    "ferienprogramm", "wetter", "weather", "newsletter", "press release",
    "fiesta", "carmen", "agenda", "opening hours", "öffnungszeiten",
    "holiday closure",
]


def fetch(url, retries=3):
    """GET with browser-like headers, exponential backoff, charset sniffing."""
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read()
                ctype = r.headers.get("Content-Type", "")
            m = re.search(r"charset=([\w-]+)", ctype)
            if not m:  # sniff <meta charset> from the first 2KB
                head = raw[:2048].decode("ascii", errors="ignore")
                m = re.search(r'charset=["\']?([\w-]+)', head)
            enc = m.group(1) if m else "utf-8"
            try:
                return raw.decode(enc, errors="replace")
            except LookupError:
                return raw.decode("utf-8", errors="replace")
        except Exception as e:  # URLError, timeout, ConnectionReset, ...
            last_err = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise last_err


def extract_content(raw):
    """Narrow to the page's main content where the markup allows it.

    <main>/<article> are taken greedily (first open to LAST close) — safe for
    single-occurrence landmarks and immune to the nested-tag truncation a
    non-greedy match suffers. No div-class guessing: stripping nav/header/
    footer/aside handles the rest without risking silent content loss.
    """
    for tag in ("main", "article"):
        m = re.search(rf"<{tag}[^>]*>(.*)</{tag}>", raw, flags=re.S | re.I)
        if m:
            raw = m.group(1)
            break
    raw = re.sub(r"<(nav|header|footer|aside)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return raw


def strip_html(raw):
    raw = re.sub(r"<!--.*?-->", " ", raw, flags=re.S)
    raw = re.sub(r"<(script|style|noscript|svg|template)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = extract_content(raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html_mod.unescape(raw)  # all entities, any case, incl. hex — properly
    lines = [ln.strip() for ln in re.sub(r"[ \t]+", " ", raw).splitlines()]
    # drop very short fragments (menu crumbs, counters) — 25 keeps real rule
    # lines like "Cap: 90 nights per year" that a 30-char bar would lose
    return "\n".join(ln for ln in lines if len(ln) > 25)


def classify_diff(added, removed):
    text = " ".join(added + removed).lower()
    if any(w in text for w in SIGNAL_WORDS):
        return "high"
    if any(w in text for w in NOISE_WORDS):
        return "fluff"
    return "unknown"


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def snap_name(slug, idx):
    return f"{slug}.txt" if idx == 0 else f"{slug}--{idx + 1}.txt"


state = load_state()
high_prob, unknown, fluff, errors, dead, unchanged = [], [], [], [], [], []

for m in DATA["markets"]:
    slug = m["slug"]
    urls = [m["source"]] + m.get("altSources", [])
    for idx, url in enumerate(urls):
        key = f"{slug}#{idx}"
        label = slug if idx == 0 else f"{slug} (alt {idx + 1})"
        snap_file = SNAP / snap_name(slug, idx)
        st = state.setdefault(key, {"fails": 0, "last_ok": ""})
        try:
            text = strip_html(fetch(url))
        except Exception as e:
            st["fails"] += 1
            entry = (label, url, f"{type(e).__name__}: {e}", st["fails"])
            (dead if st["fails"] >= DEAD_AFTER else errors).append(entry)
            continue
        st["fails"] = 0
        st["last_ok"] = TODAY
        if not snap_file.exists():
            snap_file.write_text(text)
            unchanged.append((label, "first snapshot taken"))
            continue
        old = snap_file.read_text()
        if hashlib.sha256(old.encode()).hexdigest() == hashlib.sha256(text.encode()).hexdigest():
            unchanged.append((label, "no change"))
            continue
        diff = list(difflib.unified_diff(old.splitlines(), text.splitlines(), lineterm="", n=0))
        added = [l[1:].strip() for l in diff if l.startswith("+") and not l.startswith("+++")][:12]
        removed = [l[1:].strip() for l in diff if l.startswith("-") and not l.startswith("---")][:12]
        item = (label, url, added, removed)
        {"high": high_prob, "fluff": fluff, "unknown": unknown}[classify_diff(added, removed)].append(item)
        snap_file.write_text(text)  # advance snapshot; the report preserves the diff

# prune state keys for markets/sources that no longer exist
live_keys = {f'{m["slug"]}#{i}' for m in DATA["markets"]
             for i in range(1 + len(m.get("altSources", [])))}
state = {k: v for k, v in state.items() if k in live_keys}
STATE_FILE.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n")

# ---- report ----
total_changed = len(high_prob) + len(unknown) + len(fluff)
rep = [f"# Scan report — {TODAY}", ""]
rep.append(f"**{total_changed} changed · {len(errors)} unreachable · "
           f"{len(dead)} DEAD · {len(unchanged)} quiet**\n")


def section(title, items):
    if not items:
        return
    rep.append(f"## {title}\n")
    for label, url, added, removed in items:
        rep.append(f"### {label} — {url}")
        if added:
            rep.append("**Added:**")
            rep.extend(f"> + {l[:200]}" for l in added)
        if removed:
            rep.append("**Removed:**")
            rep.extend(f"> - {l[:200]}" for l in removed)
        rep.append("")


section("🚨 HIGH-SIGNAL CHANGES — read the page, stamp the register", high_prob)
section("⚠ Uncategorized changes — skim these", unknown)
section("ℹ Likely fluff (events, calendars)", fluff)

if dead:
    rep.append(f"## 🔴 DEAD SOURCES — {DEAD_AFTER}+ days unreachable, replace the URL\n")
    rep += [f"- {s}: {u} — `{e[:120]}` ({n} days)" for s, u, e, n in dead]
    rep.append("")
if errors:
    rep.append("## ✗ Unreachable today (watching)\n")
    rep += [f"- {s}: {u} — `{e[:120]}` (day {n})" for s, u, e, n in errors]
    rep.append("")
rep.append("## Quiet\n")
rep += [f"- {s} ({note})" for s, note in unchanged]

report_text = "\n".join(rep) + "\n"
(REPORTS / f"{TODAY}.md").write_text(report_text)
(ROOT / "scan-report.md").write_text(report_text)  # latest, stable path

# ---- alert contract for the workflow ----
alerts = []
if high_prob:
    alerts.append(f"{len(high_prob)} high-signal change(s): "
                  + ", ".join(i[0] for i in high_prob))
if dead:
    alerts.append(f"{len(dead)} dead source(s): " + ", ".join(d[0] for d in dead))
if alerts:
    ALERT_FILE.write_text("\n".join(alerts) + "\n")
elif ALERT_FILE.exists():
    ALERT_FILE.unlink()

print(f"scan {TODAY}: {total_changed} changed ({len(high_prob)} high-signal), "
      f"{len(errors)} unreachable, {len(dead)} dead, {len(unchanged)} quiet -> reports/{TODAY}.md")
