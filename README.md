# STR Rule Tracker

Short-term rental rules by city — dated, sourced, operator-verified.
Live: https://str-rule-tracker.vercel.app · Bucket: vault/buckets/str-rules/

## Daily loop (Fully Automated via GitHub Actions)
1. `scan.py` runs daily via GitHub Actions.
2. It fetches every market's official source page and isolates the `<main>` content.
3. It filters text diffs into 🚨 High Probability, ⚠ Uncategorized, and ℹ Fluff.
4. You receive an email if the GitHub action commits changes to `scan-report.md`.
5. Review the report. If actual STR laws changed, edit `data/markets.json` and `data/changelog.json`.
6. Run `python3 build.py && ./deploy.sh` to update the site.
   (deploy: ask claude, or vercel CLI once installed)

Never edit `public/` by hand — it's generated.
Depth fields (process/whoCanHost/zones/penalties/enforcement) fill on later rotation passes.
