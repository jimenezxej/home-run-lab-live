# Home Run Lab 4.6.1 Clean Pitcher Lab

This patch reformats the Pitcher Lab so it looks cleaner and more professional.

Install:

```bash
cd ~
unzip ~/home-run-lab-4.6.1-clean-pitcher-lab.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.6.1-clean-pitcher-lab/* .
python3 scripts/patch_clean_pitcher_css.py
python3 scripts/patch_clean_pitcher_lab.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```
