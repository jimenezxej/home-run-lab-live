# Home Run Lab 4.4 Model + Batter Profile Tune

This patch does three important things:

1. TBD pitchers show N/A / dash values only.
   - No neutral fake numbers.
   - No estimated HR/9, FIP, SIERA for TBD starters.

2. Adds hitter profile metrics:
   - KHR
   - Blast%
   - Zone Fit
   - HR Form
   - Full at-bat history sample size
   - ISO
   - Matchup
   - xwOBA
   - xwOBAcon

3. Improves the scoring model so it rewards combinations:
   - Batter power + pitcher weakness
   - Pitch fit + zone fit
   - Weather + park + fly-ball matchup
   - Recent HR form + real contact quality
   - Lineup/longshot value without overranking names

Important: 20–25% HR probability on individual picks is extremely aggressive. This patch does not fake probability.
It separates:
- HR Edge = ranking signal
- Model Probability = estimated probability
- Confidence = data reliability
- Stack Score = how many factors are aligning

## Install

```bash
cd ~
unzip ~/home-run-lab-4.4-model-profile-tune.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-4.4-model-profile-tune/* .
python3 backend/pitchers/enrich_pitchers.py
python3 backend/model/scoring.py
python3 scripts/build_github_pages.py
cd dist
python3 -m http.server 8001
```

Open:

```text
http://localhost:8001
```
