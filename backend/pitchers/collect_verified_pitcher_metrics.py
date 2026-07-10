#!/usr/bin/env python3
from pathlib import Path
from typing import Any
import datetime as dt, json, math, re, sys, unicodedata
import pandas as pd
from pybaseball import cache, pitching_stats, playerid_reverse_lookup

DATA=Path("data"); DATA.mkdir(exist_ok=True)
SEASON=dt.datetime.now().year
TEAM_ALIASES={"CHW":"CWS","WSN":"WSH","AZ":"ARI","SDP":"SD","SFG":"SF","TBR":"TB","KCR":"KC","NYA":"NYY","NYN":"NYM","OAK":"ATH"}
ALIASES={
 "hr9":["HR/9","HR9"],"fb":["FB%","FB_pct","FB"],"gb":["GB%","GB_pct","GB"],
 "fip":["FIP"],"siera":["SIERA"],"xfip":["xFIP","XFIP"],"k_pct":["K%","K_pct"],
 "bb_pct":["BB%","BB_pct"],"ip":["IP"],"era":["ERA"]
}
def load(path, fallback):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except:return fallback
def save(path,obj): path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf-8")
def n(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except:return None
def norm_team(v):
    if v is None:return None
    s=str(v).upper().strip()
    if s in {"-","---","2 TMS","TOT"}:return None
    return TEAM_ALIASES.get(s,s)
def norm_name(v):
    s=unicodedata.normalize("NFKD",str(v or ""))
    s="".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+"," ",s).split())
def metric(row,names,percent=False):
    for name in names:
        if name in row.index:
            x=n(row.get(name))
            if x is not None:
                if percent and 0<=x<=1:x*=100
                return round(x,3)
    return None
def rows_from(raw):
    profiles=raw.get("profiles",raw) if isinstance(raw,dict) else raw
    if isinstance(profiles,dict):
        out=[]
        for k,v in profiles.items():
            if isinstance(v,dict):
                d=dict(v); d["_key"]=k; out.append(d)
        return out
    return [x for x in (profiles or []) if isinstance(x,dict)]
def mlbam(profile):
    for v in [profile.get("playerId"),profile.get("id"),(profile.get("raw") or {}).get("id")]:
        try:
            if v is not None:return int(v)
        except:pass
    return None
def id_map(ids):
    try: df=playerid_reverse_lookup(sorted(set(ids)),key_type="mlbam")
    except Exception as e:
        print("WARNING reverse lookup failed:",e,file=sys.stderr); return {}
    out={}
    for _,r in df.iterrows():
        a,b=n(r.get("key_mlbam")),n(r.get("key_fangraphs"))
        if a is not None and b is not None and b>0: out[int(a)]=int(b)
    return out
def main():
    cache.enable()
    raw=load(DATA/"pitcher-profiles.json",{"profiles":{}})
    profiles=rows_from(raw)
    if not profiles: raise SystemExit("No pitcher profiles found.")
    print(f"Downloading {SEASON} FanGraphs pitching leaderboard...")
    try: fg=pitching_stats(SEASON,SEASON,qual=0,ind=1)
    except Exception as e: raise SystemExit(f"FanGraphs download failed; no data changed: {e}")
    if fg is None or fg.empty: raise SystemExit("FanGraphs returned no rows.")
    for col in ["Name","IDfg"]:
        if col not in fg.columns: raise SystemExit(f"Missing required FanGraphs column: {col}")
    fg=fg.copy()
    fg["_name_norm"]=fg["Name"].map(norm_name)
    fg["_team_norm"]=fg["Team"].map(norm_team) if "Team" in fg.columns else None
    by_fg={int(x):i for i,x in fg["IDfg"].items() if n(x) is not None}
    mapping=id_map([x for x in (mlbam(p) for p in profiles) if x is not None])
    result={}; unresolved=[]; matched=complete=0
    for profile in profiles:
        team=str(profile.get("team") or profile.get("_key") or "")
        profile.pop("_key",None)
        row=None; method=None
        pid=mlbam(profile); fgid=mapping.get(pid) if pid else None
        if fgid in by_fg: row=fg.loc[by_fg[fgid]]; method="mlbam_to_fangraphs"
        if row is None:
            wanted=norm_name(profile.get("name") or (profile.get("raw") or {}).get("name"))
            cand=fg[fg["_name_norm"]==wanted]
            if len(cand)==1: row=cand.iloc[0]; method="exact_name"
            elif len(cand)>1:
                tc=cand[cand["_team_norm"]==norm_team(team)]
                if len(tc)==1: row=tc.iloc[0]; method="exact_name_team"
        profile.setdefault("provenance",{})
        if row is None:
            unresolved.append({"team":team,"name":profile.get("name")})
            for f in ["hr9","fb","gb","fip","siera"]:
                profile[f]=None
                profile["provenance"][f]={"status":"missing","source":None,"reason":"no_verified_fangraphs_match","season":SEASON}
            profile["dataQuality"]="partial"; result[team]=profile; continue
        matched+=1
        values={
          "hr9":metric(row,ALIASES["hr9"]),
          "fb":metric(row,ALIASES["fb"],True),
          "gb":metric(row,ALIASES["gb"],True),
          "fip":metric(row,ALIASES["fip"]),
          "siera":metric(row,ALIASES["siera"]),
          "xfip":metric(row,ALIASES["xfip"]),
          "k_pct":metric(row,ALIASES["k_pct"],True),
          "bb_pct":metric(row,ALIASES["bb_pct"],True),
          "ip":metric(row,ALIASES["ip"]),
          "era":metric(row,ALIASES["era"])
        }
        now=dt.datetime.now(dt.timezone.utc).isoformat()
        for f,v in values.items():
            profile[f]=v
            profile["provenance"][f]={
              "status":"verified" if v is not None else "missing",
              "source":"FanGraphs via pybaseball pitching_stats",
              "season":SEASON,"updatedAt":now,"matchMethod":method,
              "fanGraphsId":int(row["IDfg"]) if n(row["IDfg"]) is not None else None,
              "fanGraphsName":row.get("Name"),"fanGraphsTeam":row.get("Team")
            }
        req=["hr9","fb","gb","fip","siera"]
        miss=[f for f in req if profile.get(f) is None]
        profile["missingFields"]=miss
        profile["realFields"]=sorted(set(profile.get("realFields",[]))|{f for f,v in values.items() if v is not None})
        profile["dataQuality"]="complete" if not miss else "partial"
        profile["verifiedPitcherMetricsSource"]="FanGraphs via pybaseball"
        profile["verifiedPitcherMetricsSeason"]=SEASON
        profile["verifiedPitcherMetricsUpdatedAt"]=now
        profile["verifiedMatchMethod"]=method
        if not miss: complete+=1
        result[team]=profile
    out={
      "version":"verified-pitcher-metrics-1.0",
      "updatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),
      "season":SEASON,"source":"FanGraphs via pybaseball pitching_stats",
      "integrityRule":"Missing values remain null. No neutral or league-average placeholders.",
      "matchedProfiles":matched,"completeRequiredProfiles":complete,
      "unresolvedProfiles":unresolved,"profiles":result
    }
    save(DATA/"pitcher-profiles.json",out)
    save(DATA/"verified-pitcher-metrics-audit.json",{
      "season":SEASON,"totalProfiles":len(profiles),"matchedProfiles":matched,
      "completeRequiredProfiles":complete,"unresolvedProfiles":unresolved,
      "requiredMetrics":["hr9","fb","gb","fip","siera"],"source":out["source"],
      "columnsReceived":[str(c) for c in fg.columns]
    })
    print(f"Verified pitcher metrics: {matched}/{len(profiles)} matched; {complete}/{len(profiles)} complete.")
if __name__=="__main__": main()
