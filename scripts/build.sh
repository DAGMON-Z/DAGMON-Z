#!/usr/bin/env bash
# Rebuild every generated part of the profile. Safe to run any time.
# A failing step keeps the previous image instead of breaking the README.
set -uo pipefail
cd "$(dirname "$0")/.."

python3 scripts/fetch.py .cache

python3 scripts/make_main.py assets                   || echo "warn: main terminal kept as-is"
python3 scripts/make_live.py .cache assets data/htb.json || echo "warn: stats card kept as-is"
python3 scripts/make_capture.py .cache assets         || echo "warn: capture kept as-is"

# Projects: rebuild cards from scratch so deleted/renamed repos disappear.
tmp=$(mktemp -d)
if python3 scripts/make_projects.py .cache "$tmp"; then
  rm -f assets/proj-*.svg
  mv "$tmp"/proj-*.svg assets/ 2>/dev/null || true
  mv "$tmp"/projects.md .cache/projects.md
else
  echo "warn: projects kept as-is"
fi
rm -rf "$tmp"

python3 scripts/make_readme.py
