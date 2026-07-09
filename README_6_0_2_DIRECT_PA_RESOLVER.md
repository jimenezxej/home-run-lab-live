# Home Run Lab 6.0.2 — Direct PA Resolver

This fixes the continuing PA=0 issue by changing the strategy.

Instead of relying on a league-wide table to map names, this version:
1. Reads the hitters already in your slate.
2. Resolves each hitter to an MLB player ID.
3. Pulls that exact player's season hitting stats directly from MLB Stats API.
4. Attaches PA, AB, H, HR, AVG, OBP, SLG, OPS, ISO.
5. Prints a clear audit showing exactly who mapped and who failed.

## Run this exact sequence

```bash
cd ~
unzip ~/home-run-lab-6.0.2-direct-pa-resolver.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-6.0.2-direct-pa-resolver/* .

python3 backend/hitters/resolve_slate_hitter_stats.py
python3 backend/quality/season_stats_audit.py
python3 backend/model/scoring.py
python3 scripts/build_github_pages.py
python3 scripts/check_pa_mapping.py
```

Then preview:

```bash
cd ~/homerun-lab/dist
python3 -m http.server 8001
```

## If it still fails

Paste the output of:

```bash
cat data/season-stats-audit.json
python3 scripts/check_pa_mapping.py
```
