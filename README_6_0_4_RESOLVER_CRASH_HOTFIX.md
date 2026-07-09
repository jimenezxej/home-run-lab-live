# Home Run Lab 6.0.4 — Resolver Crash Hotfix

This fixes the crash:

```text
IndexError: list index out of range
```

The resolver was failing before it had a chance to map players. This hotfix:
- Prevents empty candidate crashes
- Keeps mapping even when one player fails
- Adds better last-name / initial matching
- Adds a debug file: `data/resolver-debug.json`

## Run

```bash
cd ~
unzip ~/home-run-lab-6.0.4-resolver-crash-hotfix.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-6.0.4-resolver-crash-hotfix/* .

rm -f data/mlb-sports-players-cache.json

python3 backend/hitters/resolve_slate_hitter_stats.py
python3 backend/quality/season_stats_audit.py
python3 backend/model/scoring.py
python3 scripts/build_github_pages.py
python3 scripts/check_pa_mapping.py
```

If PA still fails, send:
```bash
cat data/resolver-debug.json
cat data/season-stats-audit.json
```
