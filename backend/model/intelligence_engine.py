#!/usr/bin/env python3
from pathlib import Path
import json, datetime as dt

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def load(path, fallback):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    return fallback

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def clamp(v, lo=0, hi=100):
    try:
        v = float(v)
    except Exception:
        return lo
    return max(lo, min(hi, v))

def n(v, default=0):
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default

def score_power(p):
    pr = p.get("profile", {}) or {}
    season_hr = n(pr.get("seasonHR"))
    pa = max(1, n(pr.get("sampleSize"), 1))
    hr_rate = season_hr / pa * 100
    iso = n(pr.get("iso"), 0.150)
    khr = n(pr.get("khr"), 50)
    blast = n(pr.get("blast"), 50)
    return clamp(khr*.35 + blast*.25 + clamp(hr_rate, 0, 8)*6 + clamp((iso-.120)/.220*100, 0, 100)*.20)

def score_sample(p):
    return clamp(n((p.get("profile", {}) or {}).get("sampleReliability"), 0))

def score_pitcher(p):
    return clamp(n((p.get("scores", {}) or {}).get("pitcher_vulnerability"), 42))

def score_environment(p):
    return clamp(n((p.get("scores", {}) or {}).get("weather"), 50))

def score_form(p):
    s = p.get("scores", {}) or {}
    pr = p.get("profile", {}) or {}
    return clamp((n(s.get("trend"), 50)*.60) + (n(pr.get("hrForm"), 50)*.40))

def lineup_score(p):
    try:
        order = int(p.get("order") or 9)
    except Exception:
        order = 9
    if order <= 2: return 92
    if order <= 4: return 82
    if order <= 6: return 64
    if order <= 8: return 46
    return 35

def public_attention_score(p, paper_rank):
    pr = p.get("profile", {}) or {}
    hr = n(pr.get("seasonHR"))
    try:
        order = int(p.get("order") or 9)
    except Exception:
        order = 9
    rank_attention = max(0, 100 - paper_rank*4)
    hr_attention = clamp(hr * 3.2)
    lineup_attention = 86 if order <= 3 else 64 if order <= 5 else 42
    return clamp(rank_attention*.45 + hr_attention*.35 + lineup_attention*.20)

def underlooked_score(p, paper_rank):
    attention = public_attention_score(p, paper_rank)
    try:
        order = int(p.get("order") or 9)
    except Exception:
        order = 9
    lower_lineup_bonus = 18 if order >= 6 else 10 if order == 5 else 0
    return clamp((100 - attention) + lower_lineup_bonus)

def paper_score(p):
    s = p.get("scores", {}) or {}
    tier = p.get("boardTier")
    tier_bonus = 8 if tier == "Main Board" else -10 if tier == "Deep Longshot" else -3
    power = score_power(p)
    sample = score_sample(p)
    pitcher = score_pitcher(p)
    env = score_environment(p)
    form = score_form(p)
    lineup = lineup_score(p)
    confidence = n(s.get("confidence"), 40)
    edge = n(s.get("hr_edge"), 0)
    score = power*.24 + pitcher*.18 + edge*.17 + sample*.12 + env*.10 + form*.08 + lineup*.06 + confidence*.05 + tier_bonus
    return round(clamp(score), 2)

def longshot_score(p, paper_rank):
    pr = p.get("profile", {}) or {}
    s = p.get("scores", {}) or {}
    pa = n(pr.get("sampleSize"))
    if pa < 35:
        sample_gate = .55
    elif pa < 75:
        sample_gate = .78
    else:
        sample_gate = 1.0

    power = score_power(p)
    pitcher = score_pitcher(p)
    env = score_environment(p)
    form = score_form(p)
    underlooked = underlooked_score(p, paper_rank)
    confidence = n(s.get("confidence"), 40)
    try:
        order = int(p.get("order") or 9)
    except Exception:
        order = 9

    top_paper_penalty = 20 if paper_rank <= 8 else 12 if paper_rank <= 15 else 0
    top_order_penalty = 8 if order <= 3 else 0

    score = (power*.24 + pitcher*.20 + env*.12 + form*.10 + underlooked*.22 + confidence*.07 + n(s.get("stack_score"), 50)*.05 - top_paper_penalty - top_order_penalty) * sample_gate
    return round(clamp(score), 2)

def label_paper(p):
    reasons = []
    pr = p.get("profile", {}) or {}
    s = p.get("scores", {}) or {}
    if n(pr.get("seasonHR")) >= 20: reasons.append("proven season HR power")
    if n(pr.get("sampleSize")) >= 150: reasons.append("strong sample")
    if n(s.get("pitcher_vulnerability")) >= 65: reasons.append("targetable pitcher")
    if n(s.get("weather")) >= 65: reasons.append("weather carry boost")
    if n(s.get("confidence")) >= 65: reasons.append("high confidence")
    if not reasons: reasons.append("balanced profile")
    return reasons[:4]

def label_longshot(p, paper_rank):
    reasons = []
    pr = p.get("profile", {}) or {}
    s = p.get("scores", {}) or {}
    try:
        order = int(p.get("order") or 9)
    except Exception:
        order = 9
    if paper_rank > 15: reasons.append("not an obvious top-board play")
    if order >= 5: reasons.append("lower lineup spot")
    if n(pr.get("seasonHR")) >= 8: reasons.append("real HR pop")
    if n(s.get("pitcher_vulnerability")) >= 60: reasons.append("pitcher can give up damage")
    if n(s.get("weather")) >= 60: reasons.append("environment helps carry")
    if 35 <= n(pr.get("sampleSize")) < 150: reasons.append("smaller but usable sample")
    if not reasons: reasons.append("under-the-radar profile")
    return reasons[:4]

def main():
    scores = load(DATA / "scores.json", {"players": []})
    players = scores.get("players", []) or []

    for p in players:
        p.setdefault("intelligence", {})
        p["intelligence"]["paperScore"] = paper_score(p)

    paper_sorted = sorted(players, key=lambda x: x.get("intelligence", {}).get("paperScore", 0), reverse=True)
    paper_rank = {id(p): i+1 for i,p in enumerate(paper_sorted)}

    for p in players:
        rank = paper_rank.get(id(p), 999)
        p["intelligence"]["paperRank"] = rank
        p["intelligence"]["longshotScore"] = longshot_score(p, rank)
        p["intelligence"]["paperReasons"] = label_paper(p)
        p["intelligence"]["longshotReasons"] = label_longshot(p, rank)

    longshot_sorted = sorted(players, key=lambda x: x.get("intelligence", {}).get("longshotScore", 0), reverse=True)

    out = {
        "version": "7.0",
        "updatedAt": dt.datetime.now().isoformat(),
        "paperBoard": [
            {"rank": i+1, "name": p.get("name"), "team": p.get("team"), "score": p.get("intelligence", {}).get("paperScore"), "hrEdge": p.get("scores", {}).get("hr_edge"), "pa": p.get("profile", {}).get("sampleSize"), "hr": p.get("profile", {}).get("seasonHR"), "reasons": p.get("intelligence", {}).get("paperReasons", [])}
            for i,p in enumerate(paper_sorted[:60])
        ],
        "longshotBoard": [
            {"rank": i+1, "name": p.get("name"), "team": p.get("team"), "score": p.get("intelligence", {}).get("longshotScore"), "paperRank": p.get("intelligence", {}).get("paperRank"), "hrEdge": p.get("scores", {}).get("hr_edge"), "pa": p.get("profile", {}).get("sampleSize"), "hr": p.get("profile", {}).get("seasonHR"), "order": p.get("order"), "reasons": p.get("intelligence", {}).get("longshotReasons", [])}
            for i,p in enumerate(longshot_sorted[:60])
        ],
        "notes": [
            "Home Run Lab uses paperScore: best overall HR profile.",
            "Longshot Lab uses longshotScore: under-the-radar upside, penalizing obvious top paper plays.",
            "These boards are intentionally different."
        ]
    }

    scores["version"] = "7.0"
    scores["intelligenceUpdatedAt"] = out["updatedAt"]
    scores["players"] = players
    save(DATA / "scores.json", scores)
    save(DATA / "intelligence.json", out)
    print("Wrote data/intelligence.json and updated data/scores.json with 7.0 intelligence fields")
    print("Top paper:", [(x["name"], x["score"]) for x in out["paperBoard"][:5]])
    print("Top longshots:", [(x["name"], x["score"]) for x in out["longshotBoard"][:5]])

if __name__ == "__main__":
    main()
