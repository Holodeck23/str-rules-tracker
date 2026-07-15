# STR Rule Tracker

**Short-term rental rules change quietly, and hosts find out when they get fined.** A city halves its night cap, adds a tourist tax, or flips registration from optional to mandatory, and the official page updates with no announcement. This tracks those changes across cities so an operator doesn't have to reread 30 government sites every week.

Live: https://str-rule-tracker.vercel.app

## What it is

A dated, sourced register of short-term rental rules across 30 cities: registration requirements, night caps, tourist taxes, and who is allowed to host. Every entry links to its official source. A nightly scanner watches those sources and flags what moved; a human confirms whether a real rule changed before anything is stamped VERIFIED.

That human step is the point. Automated scrapers go stale and invent things. A VERIFIED entry here means a person read the official page and dated it.

**Current scope, honest:** 30 cities tracked. 3 verified at full depth (process, zones, penalties, enforcement). The other 27 are drafts seeded from public knowledge, clearly labelled Unverified until a human checks them. Nothing is padded to look more complete than it is.

## How it works

**Nightly, automated (`scan.py` via GitHub Actions, 04:00 UTC):**

1. Fetches each city's official source page, extracts the main content, diffs it against the stored snapshot.
2. Classifies each diff: high-signal (rule / tax / permit terms), uncategorized, or likely noise.
3. Tracks consecutive failures per source. A source dead 3+ days is escalated. Sources that block datacenter IPs (reachable in a real browser, never by CI) are tagged `watch: manual` and listed for human review instead of crying wolf every night.
4. If anything needs a human (a high-signal change or a dead source), the workflow fails on purpose, so GitHub's failed-run email becomes the alert channel.

**When the report flags something (human):**

5. Read the flagged page. If a real rule changed, update `data/markets.json` (`status: VERIFIED`, dated) and log it in `data/changelog.json` with the operator translation: what changed, what it costs, the action, the deadline.
6. `python3 build.py` regenerates the site; commit and push deploys via Vercel.

The weekly digest (`digest.py`) turns those changelog entries into a plain-language issue a host can act on. That is the paid product's raw material.

## Repo layout

- `scan.py`: nightly source watcher, Python stdlib only.
- `build.py`: static site generator to `public/`. Never edit `public/` by hand. Emits per-city pages with FAQ / Dataset JSON-LD, an RSS feed, sitemap, and OG images.
- `digest.py`: turns changelog entries into an email-ready weekly issue (`digests/<date>.html` + `.txt`).
- `data/markets.json`: the register. `source` (plus optional `altSources`) is what the scanner watches; `updated` is the only freshness date the site is allowed to claim.
- `data/changelog.json`: dated ledger of real changes; drives the site ledger, the RSS feed, and the digest.

## Conventions

- **Freshness is data-driven, never the build clock.** The site stamps `markets.json.updated`, not today's date. A VERIFIED badge decays with age: fresh, then aging past 45 days, then "review due" past 90.
- **VERIFIED vs Unverified.** Only human-checked entries carry a date. The depth fields (process, who can host, zones, penalties, enforcement) fill in on verification.
- **Manual-watch sources.** `watch: manual` marks a market whose official page blocks CI but works in a browser. 8 of the 30 today; the rest scan nightly.
- **Digest signups.** Set `markets.json.digestEndpoint` to an activated form endpoint (Formspree / FormSubmit / Buttondown). Until then the form degrades to a mailto and nothing breaks.
