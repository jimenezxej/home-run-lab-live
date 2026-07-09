# Home Run Lab 7.0 — Intelligence Engine

This version separates:

## Home Run Lab
Best home run spots on paper.

## Longshot Lab
Best overlooked HR threats that are not simply the top paper plays copied over.

## Install

```bash
cd ~
unzip ~/home-run-lab-7.0-intelligence-engine.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-7.0-intelligence-engine/* .

python3 backend/model/intelligence_engine.py
python3 scripts/patch_7_0_ui.py
python3 scripts/build_github_pages.py
python3 scripts/check_7_0_boards.py
```

Preview:

```bash
cd ~/homerun-lab/dist
python3 -m http.server 8001
```
