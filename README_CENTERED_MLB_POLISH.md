# Home Run Lab 4.0 Centered MLB App Polish

This update changes the app from a left-sidebar dashboard into a centered,
professional MLB-style web app.

## What changes

- White background
- Navy/red MLB-inspired theme
- Top navigation instead of left sidebar
- Bigger cards and tables
- Centered content
- Larger readable text boxes
- More app-like layout for desktop and phone

## Install

```bash
cd ~
unzip ~/home-run-lab-4.0-centered-mlb-app-polish.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.0-centered-mlb-app-polish/* .
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```

Open:

```text
http://localhost:8001
```
