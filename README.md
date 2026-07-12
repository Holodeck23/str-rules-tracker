# STR Rule Tracker

Short-term rental rules by city — dated, sourced, operator-verified.
Live: https://str-rule-tracker.vercel.app · Bucket: vault/buckets/str-rules/

## Daily loop (~30 min, zero decisions)
1. QUEUE.md rotation says which market is up today.
2. Open that market's `source` URL from `data/markets.json`.
3. No change → set `"verified": "YYYY-MM-DD"`, `"status": "VERIFIED"`.
   Change → update the row, add an entry to the market's `history` AND `data/changelog.json`.
4. `python3 build.py && git add -A && git commit -m "verify: <market>" && git push`
   (deploy: ask claude, or vercel CLI once installed)

Never edit `public/` by hand — it's generated.
Depth fields (process/whoCanHost/zones/penalties/enforcement) fill on later rotation passes.
