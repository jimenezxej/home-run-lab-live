#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

python3 scripts/patch_github_pages_paths.py
python3 scripts/cloud_build.py

git add -A
if ! git diff --cached --quiet; then
  git commit -m "Update Home Run Lab cloud deployment"
fi
git push

echo "GitHub Actions will publish dist/ automatically."
