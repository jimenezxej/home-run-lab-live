#!/usr/bin/env python3
from pathlib import Path
import shutil,json
ROOT=Path.cwd(); DIST=ROOT/"dist"; PUBLIC=ROOT/"frontend"/"public"; SRC=ROOT/"frontend"/"src"; DATA=ROOT/"data"
def cpdir(src,dst):
    if not src.exists(): return
    for item in src.iterdir():
        target=dst/item.name
        if item.is_dir(): shutil.copytree(item,target,dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(item,target)
def main():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(parents=True); cpdir(PUBLIC,DIST)
    files=["slate.json","scores.json","scorecards.json","intelligence.json",
        "game-dashboard.json","live-board.json","game-state.json","player-identity-map.json","identity-audit.json","manual-player-overrides.json","hitter-season-map.json","season-stats-audit.json","hr-history.json","hr-history-audit.json","live-events.json","pitcher-profiles.json","pitch-zone-profiles.json","truth-audit.json","metric-manifest.json","data-provenance-summary.json","glossary.json","model-results.json","update-status.json","github-readiness.json"]
    for name in files:
        src=DATA/name
        if src.exists(): shutil.copy2(src,DIST/name)
        else: (DIST/name).write_text(json.dumps({},indent=2),encoding="utf-8")
    for name in ["index.html","styles.css","app.js"]:
        shutil.copy2(SRC/name,DIST/name)
    print(f"Built GitHub Pages site in {DIST}")
if __name__=="__main__": main()
