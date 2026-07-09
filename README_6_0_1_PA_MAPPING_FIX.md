# Home Run Lab 6.0.1 — PA Mapping Fix

This fixes the issue where every hitter still shows 0 PA.

What changed:
- Uses MLB Stats API league-wide season hitting stats instead of only active roster lookup.
- Pulls all MLB hitters with season totals.
- Stronger name normalization, including accents/suffixes/punctuation.
- Team abbreviation aliases: CHW/CWS, WSN/WSH, ARI/AZ, SD/SDP, SF/SFG, TB/TBR, etc.
- If PA still cannot map, it writes a clear audit with the exact unmapped names.
- Blocks scoring if too many hitters still have 0 PA unless you explicitly allow it.

## Install and run

```bash
cd ~
unzip ~/home-run-lab-6.0.1-pa-mapping-fix.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-6.0.1-pa-mapping-fix/* .

python3 backend/hitters/collect_verified_hitter_stats.py
python3 backend/hitters/attach_verified_hitter_stats.py
python3 backend/quality/season_stats_audit.py
python3 backend/model/scoring.py
python3 scripts/build_github_pages.py
```

Then preview:

```bash
cd ~/homerun-lab/dist
python3 -m http.server 8001
```

## Check the audit

```bash
cat ~/homerun-lab/data/season-stats-audit.json
```

Look for:

```json
"sampleStatsReady": true
```

If it says false, paste the audit output back.
