#!/bin/sh
# Vercel build command. The repo is already checked out at build time, so just
# generate the site from local source — no need to re-fetch anything over HTTP.
set -e
python3 build.py
