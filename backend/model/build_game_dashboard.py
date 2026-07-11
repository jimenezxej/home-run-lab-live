#!/usr/bin/env python3
from pathlib import Path
import json, math, statistics, datetime as dt

DATA=Path("data")
def load(name,default):
    for p in [DATA/name,Path(name)]:
        try:
            if p.exists(): return json.loads(p.read_text(encoding="utf-8"))
        except: pass
    return default
def save(obj):
    (DATA/"game-dashboard.json").write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf-8")
def num(v,d=None):
    try:
        n=float(v); return n if math.isfinite(n) else d
    except:return d
def norm(v):return str(v or "").strip().upper()
def rows(d):
    if isinstance(d,list):return d
    if isinstance(d,dict):
        for k in ["players","scorecards","hitters","rows"]:
            if isinstance(d.get(k),list):return d[k]
    return []
def first(srcs,keys,default=None):
    for s in srcs:
        if not isinstance(s,dict):continue
        for k in keys:
            if s.get(k) not in (None,""):return s[k]
    return default
def pname(p):return str(first([p,p.get("profile",{}),p.get("raw",{})],["name","playerName","hitter","batter","fullName"],"Unknown"))
def pteam(p):return norm(first([p,p.get("profile",{}),p.get("raw",{})],["team","teamAbbr","batterTeam","club"],""))
def popp(p):return norm(first([p,p.get("matchup",{}),p.get("raw",{})],["opponent","opp","opponentTeam","pitcherTeam"],""))
def porder(p):return first([p,p.get("profile",{}),p.get("raw",{})],["lineupOrder","order","battingOrder","slot"])
def score(p):return max(0,num(first([p,p.get("scorecard",{}),p.get("profile",{})],["paperScore","score","hrEdge","hr_edge","overallScore","modelScore","intelligenceScore","finalScore","edge"],0),0))
def lscore(p):return max(0,num(first([p,p.get("scorecard",{})],["longshotScore","longshot_score","sleeperScore","contrarianScore"],0),0))
def explicit_prob(p):
    x=num(first([p,p.get("scorecard",{}),p.get("profile",{})],["modelProbability","probability","hrProbability","prob","hrProb"]))
    if x is None:return None
    if 0<=x<=1:x*=100
    return max(0,min(100,x))
def percentile(vals,v):
    if not vals:return .5
    return (sum(x<v for x in vals)+.5*sum(x==v for x in vals))/len(vals)
def confidence(p):
    pa=num(first([p,p.get("profile",{})],["pa","PA","sampleSize"],0),0)
    return 1 if pa>=300 else .85 if pa>=150 else .70 if pa>=75 else .55 if pa>=30 else .35 if pa>0 else .25
def estimate_prob(sc,pct,conf):
    return round(max(1,min(25,2+17*pct+max(-3,min(5,(sc-60)*.1))+(conf-.5)*4)),1)
def why(p):
    r=first([p,p.get("scorecard",{})],["why","reason","explanation","reasons"],"")
    return " ".join(map(str,r)) if isinstance(r,list) else str(r or "")
def games(slate):
    raw=[]
    if isinstance(slate,dict):
        for k in ["games","schedule","matchups"]:
            if isinstance(slate.get(k),list):raw=slate[k];break
    out=[]
    for i,g in enumerate(raw):
        if not isinstance(g,dict):continue
        away=norm(first([g,g.get("teams",{}).get("away",{}),g.get("away",{})],["abbreviation","abbr","team","name","away","awayTeam"],""))
        home=norm(first([g,g.get("teams",{}).get("home",{}),g.get("home",{})],["abbreviation","abbr","team","name","home","homeTeam"],""))
        if away and home:out.append({"id":str(g.get("gamePk") or g.get("id") or f"{away}-{home}-{i}"),"away":away,"home":home,"start":g.get("gameDate") or g.get("startTime") or g.get("time"),"venue":first([g,g.get("venue",{})],["name","venue","ballpark"],""),"status":first([g,g.get("status",{})],["detailedState","status"],""),"weather":g.get("weather") or {}})
    return out
def weather_for(g,w):
    if g.get("weather"):return g["weather"]
    if isinstance(w,dict):
        for k in [g["id"],f'{g["away"]}@{g["home"]}',f'{g["away"]}-{g["home"]}']:
            if isinstance(w.get(k),dict):return w[k]
        if isinstance(w.get("games"),dict):
            for k in [g["id"],f'{g["away"]}@{g["home"]}']:
                if isinstance(w["games"].get(k),dict):return w["games"][k]
    return {}
def wscore(w):
    if not isinstance(w,dict):return 0
    x=num(first([w],["impact","weatherBoost","carry","score","rating"]))
    if x is not None:return max(-20,min(20,x))
    t=num(first([w],["temperature","temp","gameTemp"])); wind=num(first([w],["windSpeed","wind","windMph"])); direction=str(first([w],["windDirection","direction"],"")).lower()
    s=0
    if t is not None:s+=max(-5,min(8,(t-70)*.22))
    if wind is not None:s+=min(10,wind*.6) if "out" in direction else -min(10,wind*.6) if "in" in direction else 0
    return round(s,1)
def pitcher_risk(p):
    if not isinstance(p,dict):return 0
    vals=[]
    for key,fn in [("hr9",lambda x:min(100,x/2*100)),("fb",lambda x:min(100,max(0,(x-25)/25*100))),("fip",lambda x:min(100,max(0,(x-2.5)/3.5*100))),("siera",lambda x:min(100,max(0,(x-2.5)/3.5*100))),("xera",lambda x:min(100,max(0,(x-2.5)/3.5*100))),("barrelA",lambda x:min(100,x/12*100))]:
        x=num(p.get(key))
        if x is not None:vals.append(fn(x))
    return round(statistics.fmean(vals),1) if vals else 0
def main():
    slate=load("slate.json",{}); raw_scores=load("scores.json",{"players":[]}); weather=load("weather.json",{}); profiles=load("pitcher-profiles.json",{}); profiles=profiles.get("profiles",profiles) if isinstance(profiles,dict) else {}
    ps=rows(raw_scores); gs=games(slate)
    if not gs:
        seen={}
        for p in ps:
            t,o=pteam(p),popp(p)
            if t and o:seen.setdefault("-".join(sorted([t,o])),{"id":"-".join(sorted([t,o])),"away":t,"home":o,"start":"","venue":"","status":"","weather":{}})
        gs=list(seen.values())
    vals=[score(p) for p in ps]
    enriched=[]
    for p in ps:
        sc=score(p); pr=explicit_prob(p); src="model"
        if pr is None:pr=estimate_prob(sc,percentile(vals,sc),confidence(p));src="model-estimated"
        enriched.append({"name":pname(p),"team":pteam(p),"opponent":popp(p),"lineupOrder":porder(p),"score":round(sc,2),"probability":pr,"probabilitySource":src,"longshotScore":round(lscore(p),2),"why":why(p),"raw":p})
    overall=sorted(enriched,key=lambda x:x["score"],reverse=True)
    rank={(p["name"],p["team"]):i+1 for i,p in enumerate(overall)}
    out=[]
    for g in gs:
        gp=[p for p in enriched if p["team"] in {g["away"],g["home"]}]
        gp.sort(key=lambda x:x["score"],reverse=True)
        top10=gp[:10];top=gp[:4]
        longs=[p for p in gp if p["longshotScore"]>0 or rank.get((p["name"],p["team"]),999)>12]
        longs.sort(key=lambda x:(x["longshotScore"],x["score"]),reverse=True);longs=longs[:4]
        w=weather_for(g,weather); ws=wscore(w)
        prs=[pitcher_risk(profiles.get(g["away"])),pitcher_risk(profiles.get(g["home"]))];prs=[x for x in prs if x>0]
        pr=statistics.fmean(prs) if prs else 0
        top_score=top[0]["score"] if top else 0
        avg=round(statistics.fmean([x["score"] for x in top10]),1) if top10 else 0
        gscore=round(max(0,min(100,top_score*.55+avg*.25+pr*.15+max(0,ws)*.5)),1)
        out.append({**g,"weather":w,"weatherScore":ws,"gameScore":gscore,"topHitter":top[0] if top else None,"top10Average":avg,"topReads":top,"longshots":longs,"players":gp,"pitchers":{"away":profiles.get(g["away"]),"home":profiles.get(g["home"])}})
    out.sort(key=lambda x:x["gameScore"],reverse=True)
    save({"version":"9.1","generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),"slateDate":slate.get("date") if isinstance(slate,dict) else None,"probabilityNote":"model-estimated values are display estimates derived from current model rank, score and sample confidence; they are not guaranteed outcomes","games":out,"slateTopReads":overall[:12]})
    print(f"Wrote data/game-dashboard.json with {len(out)} games and {len(enriched)} hitters.")
if __name__=="__main__":main()
