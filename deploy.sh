#!/bin/sh
# Vercel build shim: pull current source+data from GitHub, generate the site.
set -e
R=https://raw.githubusercontent.com/Holodeck23/str-rules-tracker/master
mkdir -p data
curl -fsSL $R/build.py -o build.py
curl -fsSL $R/data/markets.json -o data/markets.json
curl -fsSL $R/data/changelog.json -o data/changelog.json
python3 build.py
