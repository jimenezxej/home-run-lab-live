# Home Run Lab 5.3 — Verified HR Tracker + Weather Glossary

Fixes:
- HR Tracker dropdown now connects to actual 30-day MLB home run history.
- Adds a verified HR-history builder using MLB Stats API game feeds.
- Adds a tracker audit file so you can confirm which dates have data.
- Adds weather glossary definitions.

## Install

```bash
cd ~
unzip ~/home-run-lab-5.3-verified-hr-tracker-weather-glossary.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-5.3-verified-hr-tracker-weather-glossary/* .
python3 backend/history/build_hr_history.py --days 30
python3 backend/history/audit_hr_history.py
python3 scripts/patch_tracker_verified_ui.py
python3 scripts/patch_weather_glossary.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```
