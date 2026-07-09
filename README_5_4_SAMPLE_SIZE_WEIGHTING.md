# Home Run Lab 5.4 — Sample Size Weighting

Fixes the issue where a tiny-sample hitter can rank too high.

Adds:
- Sample Reliability score
- Sample bucket: tiny / small / thin / moderate / solid / strong
- Shrinkage toward league average for small samples
- Raw HR Edge vs Sample-Adjusted HR Edge vs Confidence-Adjusted HR Edge
- Confidence reduction for tiny samples
- UI columns for PA and reliability

## Install

```bash
cd ~
unzip ~/home-run-lab-5.4-sample-size-weighting.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-5.4-sample-size-weighting/* .
python3 backend/model/scoring.py
python3 scripts/patch_sample_size_ui.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```
