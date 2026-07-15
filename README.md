# STR Rule Tracker

Short-term rental rules by city — dated, sourced, operator-verified.
Live: https://str-rule-tracker.vercel.app

The scanner watches official sources and flags what moved; a human decides whether
a real rule changed and stamps the register. The automation surfaces candidates —
it never edits the rules itself. That human-in-the-loop step is why a VERIFIED entry
can be trusted.

## The loop

**Automated, nightly (`scan.py` via GitHub Actions, 04:00 UTC):**
1. Fetches every market's official source page(s) with browser-like headers + retries.
2. Extracts the main content, diffs it against the stored snapshot.
3. Classifies each diff: 🚨 high-signal (rule/tax/permit terms), ⚠ uncategorized, ℹ likely fluff.
4. Tracks consecutive failures per source in `data/scan-state.json`; a source dead 3+ days
   is escalated in the report.
5. Writes `reports/<date>.md` (+ latest at `scan-report.md`). If anything needs a human
   (a high-signal change or a dead source), it writes `scan-alert.txt` and **the workflow
   fails on purpose** — GitHub's failed-run email is the alert channel.

**Human, when the report flags something:**
6. Read the flagged page. If an actual STR rule changed, edit `data/markets.json`
   (set `"verified": "YYYY-MM-DD"`, `"status": "VERIFIED"`) and add an entry to
   `data/changelog.json` with the operator-translation fields (`impact`, `action`,
   `deadline`, `slug`, `severity`) the digest uses.
7. `python3 build.py` regenerates the site; commit + push deploys it (Vercel build
   command is `deploy.sh` → `python3 build.py`).

## Pieces

- `scan.py` — the nightly source watcher (stdlib only).
- `build.py` — static site generator → `public/`. Never edit `public/` by hand.
  Emits per-city pages with FAQ/Dataset JSON-LD, an RSS feed, sitemap, OG image.
- `digest.py` — turns changelog entries into an email-ready weekly issue
  (`digests/<date>.html` + `.txt`): what changed, what it means for a host's money,
  the action, the deadline. This is the paid product's raw material.
- `data/markets.json` — the register. `source` (+ optional `altSources[]`) is what the
  scanner watches. `updated` is the freshness date the site is allowed to claim.
- `data/changelog.json` — the dated ledger of real changes; drives the site ledger,
  the RSS feed, and the digest.

## Data conventions

- **Freshness is data-driven, never the build clock.** The site stamps
  `data/markets.json.updated`, not `date.today()`. A VERIFIED entry's badge decays with
  age (fresh → aging past 45 days → "review due" past 90).
- **VERIFIED vs Unverified draft.** Seeded-from-public-knowledge entries are labelled
  Unverified until a human checks them against the source. Only VERIFIED entries carry
  a date. Depth fields (process/whoCanHost/zones/penalties/enforcement) fill on verify.
- To enable real digest signups, set `data/markets.json.digestEndpoint` to an activated
  form endpoint (Formspree/FormSubmit/Buttondown). Until then the form degrades to a
  mailto and nothing breaks.
