# Home Run Lab 4.1 Premium UI

This is the next app-focused upgrade.

It improves:
- Command Center cards
- Home Run Lab player cards
- Longshot Lab
- Pitcher Lab
- Weather Lab
- Momentum Lab
- AI Report
- Centered white/navy/red MLB-style theme

## Install locally

```bash
cd ~
unzip ~/home-run-lab-4.1-premium-ui.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.1-premium-ui/* .
python3 backend/model/scoring.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```

Open:

```text
http://localhost:8001
```
