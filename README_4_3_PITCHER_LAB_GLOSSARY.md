# Home Run Lab 4.3 Pitcher Lab + Glossary

This patch adds:

- Pitcher enrichment / fallback fields
- Derived HR/9, FB%, GB%, FIP, SIERA display fallbacks
- Pitcher data quality labels
- Glossary tab for abbreviations and metrics
- Build script now includes `pitcher-profiles.json` and `glossary.json`

Important: when FanGraphs is unavailable, some advanced metrics are estimated/fallback values. The app now labels that instead of leaving blanks.

## Install

```bash
cd ~
unzip ~/home-run-lab-4.3-pitcher-lab-glossary.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.3-pitcher-lab-glossary/* .
python3 backend/pitchers/enrich_pitchers.py
python3 backend/model/scoring.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```

Open:

```text
http://localhost:8001
```
