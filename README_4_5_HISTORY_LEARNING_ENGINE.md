# Home Run Lab 4.5 History + Learning Engine

Fixes:
- ISO and xwOBAcon fallbacks so those fields show.
- HR Tracker can show last 30 days.
- Builds 30-day HR history from MLB live feeds.
- Starts model accountability: top 10 / top 12 results vs actual HR hitters.

Install:

```bash
cd ~
unzip ~/home-run-lab-4.5-history-learning-engine.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.5-history-learning-engine/* .
python3 backend/history/build_hr_history.py --days 30
python3 backend/pitchers/enrich_pitchers.py
python3 backend/model/scoring.py
python3 backend/learning/track_model_results.py
python3 scripts/patch_tracker_30_days.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```
