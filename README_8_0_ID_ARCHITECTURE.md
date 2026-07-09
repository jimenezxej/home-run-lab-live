# Home Run Lab 8.0 — ID Architecture

This version is about trust.

The app should not rely on shortened names like `Smith`, `Young`, `Winn`, `O'Hoppe`, or `Crow-Armstrong` when attaching season stats.

8.0 adds:
- MLBAM identity map for every slate hitter
- Strict player identity validation
- Suspicious match detection
- Manual correction table for known bad matches
- Season stats attached by verified MLB player ID
- Identity audit report
- Model guardrails for unresolved/suspicious players
- GitHub readiness check that fails if identity mapping is not clean enough

## Install

```bash
cd ~
unzip ~/home-run-lab-8.0-id-architecture.zip
cd ~/homerun-lab
cp -r ~/home-run-lab-8.0-id-architecture/* .

python3 backend/identity/build_player_identity_map.py
python3 backend/hitters/resolve_slate_hitter_stats.py
python3 backend/quality/identity_audit.py
python3 backend/quality/season_stats_audit.py
python3 backend/model/scoring.py
python3 backend/model/intelligence_engine.py
python3 scripts/build_github_pages.py
python3 scripts/check_8_0_identity.py
```

## Preview

```bash
cd ~/homerun-lab/dist
python3 -m http.server 8001
```

## What must pass before GitHub

Run:

```bash
python3 scripts/check_8_0_identity.py
```

You want:
- identityReady: true
- suspiciousCount: 0 or very low
- mappedWithVerifiedId: high
- no obvious wrong matches like pitcher names matched to hitters
