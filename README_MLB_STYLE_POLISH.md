# Home Run Lab 4.0 MLB Style Polish

This is a visual polish update only.

It changes:

- MLB-style navy / red / white color system
- Centered content
- More professional spacing
- Cleaner cards
- Better sidebar/header alignment
- Better table readability
- Better mobile layout
- More polished Weather Lab graphics

## Install

```bash
cd ~
unzip ~/home-run-lab-4.0-mlb-style-polish.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.0-mlb-style-polish/* .
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```

Open:

```text
http://localhost:8001
```
