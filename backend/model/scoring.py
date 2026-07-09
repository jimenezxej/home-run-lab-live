#!/usr/bin/env python3
from pathlib import Path
import json, math, sys

def clamp(v, lo=0, hi=100): return max(lo, min(hi, v))
def norm(v, lo, hi, default=50):
    try:
        if v is None or v == "": return default
        v = float(v)
    except Exception: return default
    return clamp(((v-lo)/(hi-lo))*100) if hi != lo else default
def val(v, default=None):
    try:
        if v is None or v == "": return default
        return float(v)
    except Exception: return default
def load(path, fallback):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: return fallback
    return fallback
def is_tbd(p):
    name=str((p or {}).get("name","")).strip().upper()
    return not name or name in {"TBD","TBA","UNKNOWN","—","-"}

def sample_size(h):
    for k in ["pa","PA","plateAppearances","plate_appearances","seasonPA","season_pa"]:
        v=val(h.get(k), None)
        if v is not None: return int(max(0, v)), k
    for k in ["ab","AB","atBats","abs"]:
        v=val(h.get(k), None)
        if v is not None: return int(max(0, v)), k
    return 0, None

def sample_reliability(pa):
    pa=max(0,int(pa or 0))
    if pa<=0: return 5
    return round(clamp(100*(1-math.exp(-pa/145))))
def sample_bucket(pa):
    if pa < 10: return "tiny"
    if pa < 35: return "small"
    if pa < 75: return "thin"
    if pa < 150: return "moderate"
    if pa < 300: return "solid"
    return "strong"
def shrink(value, rel, avg=50): return avg+(value-avg)*(clamp(rel)/100)
def board_tier(pa, rel, conf, edge, stack):
    if pa < 10: return "Deep Longshot"
    if pa < 35: return "Watchlist"
    if rel < 40 or conf < 45: return "Watchlist"
    if pa >= 75 or (rel >= 40 and stack >= 70): return "Main Board"
    return "Watchlist"
def board_rank_score(edge, stack, conf, rel, pa):
    score=edge*.58+stack*.20+conf*.12+rel*.10
    if pa < 10: score*=.62
    elif pa < 35: score*=.76
    elif pa < 75: score*=.90
    return round(clamp(score),2)

def derive_iso(h):
    iso=val(h.get("iso"), val(h.get("ISO"), None))
    if iso is not None: return iso, "verified" if h.get("seasonStatsVerified") else "source"
    xslg=val(h.get("xslg"), val(h.get("xSLG"), None)); avg=val(h.get("avg"), val(h.get("AVG"), None))
    if xslg is not None and avg is not None: return max(.040,min(.420,xslg-avg)), "calculated"
    barrel=val(h.get("barrel"), None); max_ev=val(h.get("maxEV"), None)
    return max(.060,min(.380,.095+(barrel or 7)*.008+((max_ev or 108)-108)*.006)), "estimated"
def derive_xwobacon(h):
    xwc=val(h.get("xwobacon"), val(h.get("xwOBAcon"), None))
    if xwc is not None: return xwc, "verified"
    xwoba=val(h.get("xwoba"), val(h.get("xwOBA"), None))
    if xwoba is not None: return max(.250,min(.620,xwoba+.045)), "calculated"
    barrel=val(h.get("barrel"), None); hard=val(h.get("hardHit"), None); ev=val(h.get("avgEV"), None)
    return max(.270,min(.590,.310+(barrel or 7)*.006+((hard or 38)-38)*.0025+((ev or 89)-89)*.010)), "estimated"

def pitcher_component(p):
    if is_tbd(p): return None, []
    signals=[]; used=[]
    if p.get("hr9") is not None: signals.append(norm(p.get("hr9"),.6,2.3)); used.append("hr9")
    if p.get("barrelA") is not None: signals.append(norm(p.get("barrelA"),4,13)); used.append("barrelA")
    if p.get("hardHitA") is not None: signals.append(norm(p.get("hardHitA"),32,50)); used.append("hardHitA")
    if p.get("fb") is not None: signals.append(norm(p.get("fb"),26,48)); used.append("fb")
    if p.get("gb") is not None: signals.append(100-norm(p.get("gb"),30,55)); used.append("gb")
    if not signals: return None, []
    return clamp(sum(signals)/len(signals)), used
def prob(edge, conf, stack, tbd, rel, tier):
    if tbd: return round(max(1,min(6.5,1.8+edge*.045)),1)
    base=1.8+edge*.075+max(0,stack-60)*.055
    if conf<50: base*=.82
    if rel<35: base*=.72
    elif rel<55: base*=.86
    if tier=="Deep Longshot": base*=.65
    elif tier=="Watchlist": base*=.82
    return round(max(1,min(24.5,base)),1)

def score_player(h,p,g):
    p=p or {}; g=g or {}; tbd=is_tbd(p)
    pa, pa_src=sample_size(h); rel=sample_reliability(pa); bucket=sample_bucket(pa)
    iso, iso_status=derive_iso(h); xwc,xwc_status=derive_xwobacon(h)
    barrel=val(h.get("barrel")); hard=val(h.get("hardHit")); avg_ev=val(h.get("avgEV")); max_ev=val(h.get("maxEV"))
    xwoba=val(h.get("xwoba"), val(h.get("xwOBA"), None))
    last7=val(h.get("last7")); last14=val(h.get("last14")); last30=val(h.get("last30"))
    raw_power=norm(barrel,4,19)*.28+norm(hard,30,58)*.16+norm(avg_ev,86,94)*.14+norm(max_ev,105,118)*.14+norm(iso,.120,.330)*.14+norm(xwc,.330,.520)*.14
    raw_blast=clamp(norm(barrel,5,20)*.42+norm(max_ev,106,118)*.30+norm(hard,32,58)*.28)
    raw_form=clamp(norm(last7,35,90)*.45+norm(last14,35,90)*.30+norm(last30,35,90)*.25)
    raw_khr=clamp(raw_power*.42+raw_blast*.34+raw_form*.24)
    raw_zone=clamp(norm(xwc,.330,.520)*.40+norm(barrel,4,19)*.35+norm(hard,30,58)*.25)
    khr=shrink(raw_khr,rel); blast=shrink(raw_blast,rel); form=shrink(raw_form,rel); zone=shrink(raw_zone,rel)
    pcomp, used=pitcher_component(p); matchup=42 if pcomp is None else pcomp
    power=clamp(khr*.45+blast*.35+norm(iso,.120,.330)*.20)
    raw_power2=clamp(raw_khr*.45+raw_blast*.35+norm(iso,.120,.330)*.20)
    wd=str(g.get("windDir","")).lower(); wind=68 if wd.startswith("out") else 35 if wd.startswith("in") else 50
    weather=clamp(norm(g.get("temp"),50,95)*.42+norm(g.get("wind"),0,18)*.27+wind*.31)
    try: order=int(h.get("order") or 9)
    except Exception: order=9
    lineup=54+(5 if order<=4 else 10 if order>=6 and power>=58 else 0)
    factors=[power,zone,weather,form,blast,lineup]
    if pcomp is not None: factors.append(pcomp)
    strong=len([x for x in factors if x>=65]); stack=clamp(sum(factors)/len(factors)+strong*4)
    raw_edge=clamp(raw_power2*.26+matchup*.18+raw_zone*.15+weather*.10+raw_form*.10+raw_blast*.10+lineup*.06+norm(xwc,.330,.520)*.05+max(0,strong-3)*4)
    edge=clamp(power*.26+matchup*.18+zone*.15+weather*.10+form*.10+blast*.10+lineup*.06+norm(xwc,.330,.520)*.05+max(0,strong-3)*4)
    completeness=len(used)/5 if not tbd else 0
    conf=38 if tbd else clamp(26+int(24*completeness)+int(rel*.30)+(10 if g.get("temp") is not None else 0)+(8 if h.get("seasonStatsVerified") else 0)+(8 if iso_status in {"verified","calculated","source"} else 3))
    if tbd: edge=clamp(edge*.82)
    elif completeness<.6: edge=clamp(edge*(.88+completeness*.12))
    adjusted=clamp(edge*(.72+rel*.0028))
    if pa<10: adjusted=clamp(adjusted*.84)
    elif pa<35: adjusted=clamp(adjusted*.92)
    tier=board_tier(pa,rel,conf,adjusted,stack); brs=board_rank_score(adjusted,stack,conf,rel,pa)
    profile={"sampleSize":pa,"sampleSource":pa_src,"sampleReliability":rel,"sampleBucket":bucket,"seasonHits":h.get("h"),"seasonHR":h.get("hr"),"seasonAB":h.get("ab"),"seasonStatsVerified":h.get("seasonStatsVerified",False),"khr":round(khr),"rawKhr":round(raw_khr),"blast":round(blast),"rawBlast":round(raw_blast),"zoneFit":round(zone),"rawZoneFit":round(raw_zone),"hrForm":round(form),"rawHrForm":round(raw_form),"iso":round(iso,3),"isoStatus":iso_status,"matchup":None if pcomp is None else round(pcomp),"matchupFields":used,"xwoba":None if xwoba is None else round(xwoba,3),"xwobacon":round(xwc,3),"xwobaconStatus":xwc_status}
    reasons=[]
    if not h.get("seasonStatsVerified"): reasons.append("Season PA/H/HR are not verified for this hitter yet; sample confidence reduced.")
    if not h.get("identityTrusted", True): reasons.append("Player identity is unresolved or suspicious; confidence reduced until MLBAM ID is verified.")
    if tier!="Main Board": reasons.append(f"Board tier: {tier}. Sample/data reliability keeps this from being treated as a main-board lock.")
    if pa<10: reasons.append(f"Tiny sample warning: only {pa} PA from {pa_src or 'unknown source'}.")
    elif pa<35: reasons.append(f"Small sample warning: {pa} PA.")
    if tbd: reasons.append("Pitcher is TBD, so pitcher matchup is N/A and confidence is reduced.")
    elif completeness<1: reasons.append("Pitcher profile has missing verified source fields; no fake values were used.")
    if power>=70: reasons.append("Strong sample-adjusted batter power profile.")
    if pcomp is not None and pcomp>=68: reasons.append("Pitcher is targetable using verified available pitcher fields.")
    if weather>=65: reasons.append("Weather/park context supports carry.")
    scorecard={"raw_edge":round(raw_edge,2),"sample_adjusted_edge":round(edge,2),"confidence_adjusted_edge":round(adjusted,2),"board_rank_score":brs,"sample_reliability":rel,"sample_size":pa,"board_tier":tier,"season_hits":h.get("h"),"season_hr":h.get("hr")}
    return {"id":h.get("id") or h.get("name"),"name":h.get("name"),"team":h.get("team"),"order":h.get("order"),"pitcher":"TBD" if tbd else p.get("name","TBD"),"pitcherTBD":tbd,"boardTier":tier,"boardRankScore":brs,"scores":{"hr_edge":round(adjusted),"raw_hr_edge":round(raw_edge),"sample_adjusted_edge":round(edge),"model_probability":prob(adjusted,conf,stack,tbd,rel,tier),"stack_score":round(stack),"power":round(power),"raw_power":round(raw_power2),"pitcher_vulnerability":None if pcomp is None else round(pcomp),"weather":round(weather),"trend":round(form),"zone_fit":round(zone),"confidence":round(conf),"sample_reliability":rel,"pitcher_data_completeness":round(completeness*100)},"profile":profile,"scorecard":scorecard,"provenance":{"pitcherFieldsUsed":used,"isoStatus":iso_status,"xwobaconStatus":xwc_status,"seasonStatsVerified":h.get("seasonStatsVerified",False)},"reasons":reasons or ["Neutral profile; no standout edge detected."],"raw":h}

def main():
    root=Path.cwd(); data=root/"data"; slate_path=data/"slate.json"
    if not slate_path.exists(): slate_path=root/"app"/"slate.json"
    slate=json.loads(slate_path.read_text(encoding="utf-8"))
    pp=load(data/"pitcher-profiles.json",{"profiles":{}})
    games=slate.get("games",[]); hitters=slate.get("hitters",[]); pitchers=pp.get("profiles",{}) or {}
    # Guardrail: warn loudly if season stats are still not attached.
    nonzero_pa = len([h for h in hitters if int(h.get("pa") or 0) > 0])
    if hitters and nonzero_pa == 0:
        print("WARNING: All slate hitters still have 0 PA. Run:")
        print("python3 backend/hitters/collect_verified_hitter_stats.py")
        print("python3 backend/hitters/attach_verified_hitter_stats.py")
        print("python3 backend/quality/season_stats_audit.py")
    team_game={}; opp={}
    for gm in games:
        a,h=gm.get("away"),gm.get("home")
        if a and h: team_game[a]=gm; team_game[h]=gm; opp[a]=h; opp[h]=a
    players=[score_player(h,pitchers.get(opp.get(h.get("team")),{}),team_game.get(h.get("team"),{})) for h in hitters]
    tier_rank={"Main Board":3,"Watchlist":2,"Deep Longshot":1,"Ineligible":0}
    players.sort(key=lambda x:(tier_rank.get(x.get("boardTier"),0),x["boardRankScore"],x["scores"]["stack_score"],x["scores"]["confidence"]),reverse=True)
    (data/"scores.json").write_text(json.dumps({"version":"6.0.1","generatedAt":slate.get("generatedAt"),"players":players},indent=2),encoding="utf-8")
    (data/"scorecards.json").write_text(json.dumps({"version":"6.0.1","players":[{"name":p["name"],"team":p["team"],"boardTier":p["boardTier"],"boardRankScore":p["boardRankScore"],"scorecard":p["scorecard"],"provenance":p["provenance"],"sample":p["profile"].get("sampleSize")} for p in players]},indent=2),encoding="utf-8")
    print(f"Wrote scores.json and scorecards.json with {len(players)} players")
if __name__=="__main__": main()
