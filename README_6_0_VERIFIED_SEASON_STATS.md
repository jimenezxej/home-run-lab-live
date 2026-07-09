# Home Run Lab 6.0 — Verified Season Stats Engine

Fixes the problem where every hitter shows 0 PA.

Adds:
- Verified hitter season totals from MLB Stats API.
- PA, AB, H, HR, 2B, 3B, BB, SO, AVG, OBP, SLG, OPS, ISO.
- Attaches those stats to every slate hitter before scoring.
- Adds `season-stats-audit.json` so you can confirm how many players mapped correctly.
- Updates scoring to use verified PA first.

## Install

```bash
cd ~
unzip ~/home-run-lab-6.0-verified-season-stats.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-6.0-verified-season-stats/* .
python3 backend/hitters/collect_verified_hitter_stats.py
python3 backend/hitters/attach_verified_hitter_stats.py
python3 backend/quality/season_stats_audit.py
python3 backend/model/scoring.py
python3 scripts/patch_season_stats_ui.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```
