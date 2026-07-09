# Home Run Lab 4.0 Full UI Upgrade

This upgrades every tab into the Lab-style interface:

- Command Center
- Home Run Lab
- Longshot Lab
- Pitcher Lab
- Weather Lab
- Momentum Lab
- Live Tracker
- HR Tracker
- AI Report

It uses your current `slate.json`, `scores.json`, `hr-history.json`, and `live-events.json`.
It does not remove your existing pipeline.

## Install

```bash
cd ~
unzip ~/home-run-lab-4.0-full-ui-upgrade.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.0-full-ui-upgrade/* .
python3 backend/model/scoring.py
python3 scripts/build_github_pages.py
python3 scripts/check_project.py
cd dist
python3 -m http.server 8001
```

Open:

```text
http://localhost:8001
```

## Push to GitHub later

Once it looks good locally, we will copy `dist/` contents to GitHub or use `scripts/deploy_github.py`.
