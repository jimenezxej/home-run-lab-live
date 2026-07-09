# Home Run Lab 6.0.3 — Abbreviated Name PA Fix

This fixes the issue shown in your terminal:

Your slate names are abbreviated:
- `Trout`
- `Soto, J`
- `Lowe, B`
- `Reynolds, B`
- `Alvarez, F`

MLB uses full names:
- `Mike Trout`
- `Juan Soto`
- `Brandon Lowe`
- `Bryan Reynolds`
- `Francisco Alvarez`

6.0.3 adds:
- Last-name-only matching for unique players
- Last-name + first-initial matching
- Comma-name parsing like `Soto, J`
- Suffix handling like `Tatis Jr.`, `Harris II`
- Safer duplicate handling
- A clearer PA audit

## Run this exact sequence

```bash
cd ~
unzip ~/home-run-lab-6.0.3-abbrev-name-pa-fix.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-6.0.3-abbrev-name-pa-fix/* .

python3 backend/hitters/resolve_slate_hitter_stats.py
python3 backend/quality/season_stats_audit.py
python3 backend/model/scoring.py
python3 scripts/build_github_pages.py
python3 scripts/check_pa_mapping.py
```

If this works, `Slate hitters with PA > 0` should no longer be 0.
