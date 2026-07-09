#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt
DATA=Path("data")
def load(p,f):
    if p.exists():
        try: return json.loads(p.read_text())
        except Exception: return f
    return f
def save(p,o): p.write_text(json.dumps(o,indent=2))
def main():
    scores=load(DATA/"scores.json",{"players":[]})
    gs=load(DATA/"game-state.json",{"teamState":{}})
    team_state=gs.get("teamState",{})
    active=[]; locked=[]
    for p in scores.get("players",[]):
        st=team_state.get(p.get("team"),{})
        row={**p,"gameState":st,"lockedForBoard":bool(st.get("lockedForBoard"))}
        (locked if row["lockedForBoard"] else active).append(row)
    active_paper=sorted(active,key=lambda x:(x.get("intelligence",{}) or {}).get("paperScore",0),reverse=True)
    active_long=sorted([p for p in active if int((p.get("profile",{}) or {}).get("sampleSize") or 0)>=35 and int((p.get("intelligence",{}) or {}).get("paperRank") or 999)>8],key=lambda x:(x.get("intelligence",{}) or {}).get("longshotScore",0),reverse=True)
    out={"version":"8.3","updatedAt":dt.datetime.now().isoformat(),"activeCount":len(active),"lockedCount":len(locked),"activePaperBoard":active_paper,"activeLongshotBoard":active_long,"lockedPlayers":locked,"gameStateUpdatedAt":gs.get("updatedAt")}
    save(DATA/"live-board.json",out)
    print(f"Live board: {len(active)} active, {len(locked)} locked")
if __name__=="__main__": main()
