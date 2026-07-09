# Home Run Lab 5.1 — Pitch Zone Visuals

Adds:
- Pitcher strike-zone visual cards
- Pitch-type frequency display
- Location tendency grid
- Fallback visuals when full pitcher stats are missing
- Morning live-run script

Install:

```bash
cd ~
unzip ~/home-run-lab-5.1-pitch-zone-visuals.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-5.1-pitch-zone-visuals/* .
python3 backend/pitchers/build_pitch_zone_profiles.py
python3 scripts/patch_pitch_zone_ui.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```

Morning runner:

```bash
cd ~/homerun-lab
bash run-live-day.sh
```
