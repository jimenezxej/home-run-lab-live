# Home Run Lab 4.6 Color Guide System

Adds:
- Universal color-coded metric badges
- Batter metric guide
- Pitcher metric guide
- Weather/park guide
- "How to Read the Model" tab
- Better N/A handling
- Color coding across batter and pitcher statistical categories

Install:

```bash
cd ~
unzip ~/home-run-lab-4.6-color-guide-system.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.6-color-guide-system/* .
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```
