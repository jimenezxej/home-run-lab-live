#!/usr/bin/env python3
from pathlib import Path
import json, math, re, unicodedata

DATA=Path("data")
def load(path,fallback):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except:return fallback
def save(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf-8")
def n(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except:return None
def norm(v):
    s=unicodedata.normalize("NFKD",str(v or ""))
    s="".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+"," ",s).split())
def profiles(raw):
    x=raw.get("profiles",raw) if isinstance(raw,dict) else {}
    return x if isinstance(x,dict) else {}
def pitcher_parts(p):
    name=p.get("name") or "Opposing starter"
    hr9,fb,gb,fip,siera=[n(p.get(k)) for k in ["hr9","fb","gb","fip","siera"]]
    barrel,hardhit,xera=[n(p.get(k)) for k in ["barrelA","hardHitA","xera"]]
    out=[]
    risk=[]
    if hr9 is not None:risk.append(f"{hr9:.2f} HR/9")
    if fb is not None:risk.append(f"{fb:.1f}% fly-ball rate")
    if gb is not None:risk.append(f"{gb:.1f}% ground-ball rate")
    if risk:out.append(f"{name} enters with "+", ".join(risk)+".")
    est=[]
    if fip is not None:est.append(f"{fip:.2f} FIP")
    if siera is not None:est.append(f"{siera:.2f} SIERA")
    if xera is not None:est.append(f"{xera:.2f} xERA")
    if est:out.append("Pitcher estimators: "+", ".join(est)+".")
    contact=[]
    if barrel is not None:contact.append(f"{barrel:.1f}% barrels allowed")
    if hardhit is not None:contact.append(f"{hardhit:.1f}% hard-hit allowed")
    if contact:out.append("Contact quality allowed: "+", ".join(contact)+".")
    mix=[x for x in (p.get("mix") or []) if isinstance(x,dict) and x.get("pitch") and n(x.get("pct")) is not None]
    mix.sort(key=lambda x:n(x.get("pct")) or 0,reverse=True)
    if mix:
        out.append("Primary mix: "+", ".join(f"{x['pitch']} {n(x['pct']):.0f}%" for x in mix[:3])+".")
    return out
def first(profile,*keys):
    for k in keys:
        v=profile.get(k)
        if v is not None:return v
    return None
def batter_parts(player):
    p=player.get("profile") or {}
    iso=n(first(p,"iso","ISO"))
    xw=n(first(p,"xwOBAcon","xwobacon"))
    blast=n(first(p,"blast","blastPct","blast%"))
    hr=n(first(p,"seasonHR","hr"))
    pa=n(first(p,"sampleSize","pa","PA"))
    out=[]
    vals=[]
    if iso is not None:vals.append(f"{iso:.3f} ISO")
    if xw is not None:vals.append(f"{xw:.3f} xwOBAcon")
    if blast is not None:vals.append(f"{blast:.1f}% Blast")
    if hr is not None and pa is not None:vals.append(f"{int(hr)} HR in {int(pa)} PA")
    if vals:out.append("Batter profile: "+", ".join(vals)+".")
    return out
def find_pitcher(player,by_team,by_name):
    for key in ["pitcherTeam","opponentTeam","opponent","opp"]:
        v=player.get(key)
        if v in by_team:return by_team[v]
    match=player.get("matchup") or {}
    for key in ["pitcherTeam","opponentTeam","opponent","opp"]:
        v=match.get(key)
        if v in by_team:return by_team[v]
    wanted=norm(player.get("pitcher") or match.get("pitcher"))
    hits=by_name.get(wanted,[])
    return hits[0] if len(hits)==1 else None
def set_reason(player,text):
    for k in ["why","reason","explanation"]:player[k]=text
    if "reasons" in player:player["reasons"]=[text] if isinstance(player["reasons"],list) else text
    if isinstance(player.get("scorecard"),dict):
        player["scorecard"]["why"]=text
        player["scorecard"]["reason"]=text
def process(path,by_team,by_name):
    if not path.exists():return 0
    data=load(path,{})
    rows=data.get("players") or data.get("scorecards") or [] if isinstance(data,dict) else data
    if not isinstance(rows,list):return 0
    changed=0
    for player in rows:
        if not isinstance(player,dict):continue
        pit=find_pitcher(player,by_team,by_name)
        if not pit:continue
        parts=pitcher_parts(pit)+batter_parts(player)
        if not parts:continue
        set_reason(player," ".join(parts));changed+=1
    save(path,data);return changed
def main():
    raw=load(DATA/"pitcher-profiles.json",{"profiles":{}})
    by_team=profiles(raw)
    by_name={}
    for p in by_team.values():by_name.setdefault(norm(p.get("name")),[]).append(p)
    total=0
    for path in [DATA/"scores.json",DATA/"scorecards.json"]:
        c=process(path,by_team,by_name);total+=c;print(f"Updated {c} reasons in {path}")
    if total==0:raise SystemExit("No reasons updated: score records lack a recognized pitcher/opponent mapping.")
if __name__=="__main__":main()
