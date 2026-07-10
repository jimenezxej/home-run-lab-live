# Home Run Lab 8.4 - Cloud Pages Deployment

This patch fixes GitHub Pages loading without player data.

## Install

```bash
cd ~
unzip ~/home-run-lab-8.4-cloud-pages-deploy.zip
cd ~/home-run-lab-live
cp -r ~/home-run-lab-8.4-cloud-pages-deploy/* .

python3 scripts/patch_github_pages_paths.py
python3 scripts/cloud_build.py

git add -A
git commit -m "Add cloud data build and GitHub Pages deployment"
git push
```

Then change GitHub Pages Source to **GitHub Actions**.
