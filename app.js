
function statusTag(status){
  if(!status) return "";
  const s=String(status).toLowerCase();
  return `<span class="status-tag ${s}">${s}</span>`;
}

const state = { slate:null, scores:null, history:null, live:null, pitcherProfiles:null, pitchZones:null, updateStatus:null, intelligence:null, glossary:null, tab:"dashboard" };
const $ = (sel) => document.querySelector(sel);
const fmt = (v,d="—") => v===null||v===undefined||Number.isNaN(v)||v===""?d:v;
const num = (v,d=0)=>{const n=Number(v);return Number.isFinite(n)?n:d};

function gradeClass(level){
  return level==="elite"?"elite":level==="good"?"good":level==="avg"?"avg":level==="risk"?"risk":level==="poor"?"poor":"na";
}
function gradeLabel(level){
  return {elite:"Elite",good:"Good",avg:"Avg",risk:"Risk",poor:"Poor",na:"N/A"}[level] || "N/A";
}
function gradeHigher(v, bands){
  if(v===null||v===undefined||v==="") return "na";
  const n=num(v);
  if(n>=bands.elite) return "elite";
  if(n>=bands.good) return "good";
  if(n>=bands.avg) return "avg";
  if(n>=bands.risk) return "risk";
  return "poor";
}
function gradeLower(v, bands){
  if(v===null||v===undefined||v==="") return "na";
  const n=num(v);
  if(n<=bands.elite) return "elite";
  if(n<=bands.good) return "good";
  if(n<=bands.avg) return "avg";
  if(n<=bands.risk) return "risk";
  return "poor";
}
function gradeMetric(metric, v){
  const m = metric.toLowerCase();
  if(v===null||v===undefined||v==="") return "na";

  // Batter / model metrics — higher is better.
  if(["hr_edge","stack","stack_score","khr","zone","zonefit","zone_fit","hrform","hr_form","confidence","power","trend","weather"].includes(m)) {
    return gradeHigher(v,{elite:80,good:70,avg:60,risk:50});
  }
  if(["prob","model_probability"].includes(m)) return gradeHigher(v,{elite:18,good:14,avg:10,risk:6});
  if(["blast","blast%","barrel","barrel%"].includes(m)) return gradeHigher(v,{elite:14,good:11,avg:8,risk:5});
  if(["hardhit","hardhit%"].includes(m)) return gradeHigher(v,{elite:50,good:45,avg:40,risk:35});
  if(["avgev","avg_ev"].includes(m)) return gradeHigher(v,{elite:93,good:91,avg:89,risk:87});
  if(["maxev","max_ev"].includes(m)) return gradeHigher(v,{elite:115,good:112,avg:110,risk:108});
  if(["iso"].includes(m)) return gradeHigher(v,{elite:.280,good:.240,avg:.190,risk:.150});
  if(["xwoba"].includes(m)) return gradeHigher(v,{elite:.400,good:.370,avg:.340,risk:.310});
  if(["xwobacon"].includes(m)) return gradeHigher(v,{elite:.520,good:.480,avg:.440,risk:.400});

  // Pitcher danger metrics — red/poor means tough for hitter, elite means targetable for HR.
  if(["hr9"].includes(m)) return gradeHigher(v,{elite:1.60,good:1.30,avg:1.00,risk:.80});
  if(["barrela","barrel_allowed"].includes(m)) return gradeHigher(v,{elite:10,good:8,avg:6,risk:4});
  if(["hardhita","hardhit_allowed"].includes(m)) return gradeHigher(v,{elite:46,good:42,avg:38,risk:34});
  if(["fb","fb%"].includes(m)) return gradeHigher(v,{elite:44,good:40,avg:35,risk:30});
  if(["gb","gb%"].includes(m)) return gradeLower(v,{elite:36,good:40,avg:46,risk:52});
  if(["xera","fip"].includes(m)) return gradeHigher(v,{elite:4.80,good:4.30,avg:3.80,risk:3.30});
  if(["siera"].includes(m)) return gradeHigher(v,{elite:4.60,good:4.20,avg:3.70,risk:3.30});

  return gradeHigher(v,{elite:80,good:70,avg:60,risk:50});
}
function badgeMetric(metric, v, suffix=""){
  const g=gradeMetric(metric,v);
  if(g==="na") return `<span class="metric-badge na">N/A</span>`;
  return `<span class="metric-badge ${gradeClass(g)}"><b>${fmt(v)}${suffix}</b><small>${gradeLabel(g)}</small></span>`;
}
function smallDot(metric,v){
  const g=gradeMetric(metric,v);
  return `<span class="dot ${gradeClass(g)}" title="${gradeLabel(g)}"></span>`;
}

// HOME_RUN_LAB_GITHUB_PATH_FALLBACK_8_4
async function loadJSON(path, fallback={}){
  const raw = String(path || "").replace(/^\/+/, "");
  const filename = raw.split("/").pop();
  const projectBase = window.location.pathname.includes("/home-run-lab-live/")
    ? "/home-run-lab-live/"
    : "./";
  const candidates = [
    path,
    `./${raw}`,
    `./${filename}`,
    `./data/${filename}`,
    `${projectBase}${filename}`,
    `${projectBase}data/${filename}`
  ].filter(Boolean);

  for (const candidate of [...new Set(candidates)]) {
    try {
      const sep = candidate.includes("?") ? "&" : "?";
      const response = await fetch(`${candidate}${sep}v=${Date.now()}`, {cache:"no-store"});
      if (!response.ok) continue;
      return await response.json();
    } catch (error) {}
  }
  console.warn("Unable to load JSON:", path, candidates);
  return fallback;
}
function players(){return state.scores?.players?.length?state.scores.players:[]}
function games(){return state.slate?.games||[]}
function pitcherProfiles(){return state.pitcherProfiles?.profiles||{}}
function hero(title,desc){return `<div class="hero"><div><h2>${title}</h2><p>${desc}</p></div><div class="pill-row"><span class="pill">${games().length} games</span><span class="pill">${players().length} hitters</span><span class="pill">Updated ${fmt(state.slate?.generatedAt,"—")}</span></div></div>`}

function factorDots(p){
  return `<div class="factor-dots">
    ${smallDot("khr",p.profile?.khr)}${smallDot("blast",p.profile?.blast)}${smallDot("zoneFit",p.profile?.zoneFit)}
    ${smallDot("matchup",p.profile?.matchup)}${smallDot("weather",p.scores?.weather)}${smallDot("hrForm",p.profile?.hrForm)}
  </div>`;
}

function paperPlayers(){
  const rows = [...players()];
  return rows.sort((a,b)=>(b.intelligence?.paperScore||0)-(a.intelligence?.paperScore||0));
}
function longshotPlayers(){
  const rows = [...players()].filter(p=>{
    const pa = Number(p.profile?.sampleSize||0);
    const paperRank = Number(p.intelligence?.paperRank||999);
    return pa >= 35 && paperRank > 8;
  });
  return rows.sort((a,b)=>(b.intelligence?.longshotScore||0)-(a.intelligence?.longshotScore||0));
}

function playerTable(rows){
 return `<div class="table-wrap"><table><thead><tr>
 <th>Signals</th><th>Player</th><th>Team</th><th>Ord</th><th>Pitcher</th><th>Paper</th><th>Longshot</th><th>HR Edge</th><th>Prob</th><th>Stack</th><th>Sample</th><th>H/HR</th><th>Reliability</th><th>KHR</th><th>Blast%</th><th>Zone Fit</th><th>HR Form</th><th>ISO</th><th>xwOBA</th><th>xwOBAcon</th><th>Matchup</th><th>Confidence</th><th>Why</th>
 </tr></thead><tbody>${rows.map(p=>{const pr=p.profile||{};return `<tr>
 <td>${factorDots(p)}</td><td><strong>${fmt(p.name)}</strong></td><td>${fmt(p.team)}</td><td>${fmt(p.order)}</td><td>${p.pitcherTBD?`<span class="metric-badge na">TBD</span>`:fmt(p.pitcher)}</td>
 <td>${badgeMetric("hr_edge",p.intelligence?.paperScore)}</td><td>${badgeMetric("hr_edge",p.intelligence?.longshotScore)}</td><td>${badgeMetric("hr_edge",p.scores?.hr_edge)}</td><td>${badgeMetric("prob",p.scores?.model_probability,"%")}</td><td>${badgeMetric("stack",p.scores?.stack_score)}</td><td>${fmt(pr.sampleSize,"N/A")} PA<br><span class="sample-bucket ${fmt(pr.sampleBucket,"na")}">${fmt(pr.sampleBucket,"N/A")}</span></td><td>${fmt(pr.seasonHits,"N/A")} H<br>${fmt(pr.seasonHR,"N/A")} HR</td><td>${badgeMetric("confidence",p.scores?.sample_reliability)}</td>
 <td>${badgeMetric("khr",pr.khr)}</td><td>${badgeMetric("blast",pr.blast)}</td><td>${badgeMetric("zoneFit",pr.zoneFit)}</td><td>${badgeMetric("hrForm",pr.hrForm)}</td>
 <td>${badgeMetric("iso",pr.iso)}</td><td>${badgeMetric("xwoba",pr.xwoba)}</td><td>${badgeMetric("xwobacon",pr.xwobacon)}</td><td>${badgeMetric("matchup",pr.matchup)}</td><td>${badgeMetric("confidence",p.scores?.confidence)}</td>
 <td class="wrap reason">${(p.reasons||[]).slice(0,3).join(" ")}</td></tr>`}).join("")}</tbody></table></div>`;
}
function dashboard(){const ps=players(),top=ps[0]||{},elite=ps.filter(p=>num(p.scores?.stack_score)>=75).length;return `${hero("Command Center","A control room for today's slate. Auto-updates lineups and probable pitchers during the day. Green means strong HR factor, yellow means neutral, orange/red means caution, gray means unavailable.")}<section class="guide-strip"><span class="legend elite">Elite</span><span class="legend good">Good</span><span class="legend avg">Average</span><span class="legend risk">Caution</span><span class="legend poor">Poor</span><span class="legend na">N/A</span></section><section class="grid"><div class="card kpi"><span class="label">Today's Games</span><span class="value">${games().length}</span><span class="sub">scheduled / loaded</span></div><div class="card kpi"><span class="label">Modeled Hitters</span><span class="value">${ps.length}</span><span class="sub">ranked by HR Edge + Stack</span></div><div class="card kpi"><span class="label">Top HR Edge</span><span class="value">${fmt(top.name)}</span><span class="sub">${badgeMetric("hr_edge",top.scores?.hr_edge)} ${badgeMetric("prob",top.scores?.model_probability,"%")}</span></div><div class="card kpi"><span class="label">Elite Stacks</span><span class="value">${elite}</span><span class="sub">multiple green factors aligned</span></div></section><section class="card" style="margin-top:22px"><h3>Top model board</h3>${playerTable(ps.slice(0,12))}</section>`}

function hrlab(){
  const rows = paperPlayers();
  return `${hero("Home Run Lab","Best home run spots on paper. This board prioritizes proven sample, season HR power, matchup, weather, confidence, and overall HR profile.")}
  <section class="card"><div class="lab-note">This is the clean main board, not the sleeper board. Look for strong PA sample, real season HR production, pitcher vulnerability, and weather support.</div><br>${playerTable(rows.slice(0,80))}</section>`;
}


function longshots(){
  const rows = longshotPlayers();
  return `${hero("Longshot Lab","Under-the-radar HR threats. This board intentionally avoids simply copying the top Home Run Lab plays.")}
  <section class="card">
    <div class="lab-note">Longshots are not the safest plays. They are overlooked profiles with enough sample, real pop, a targetable pitcher, weather/park help, or lower-lineup leverage. Obvious top paper plays are penalized here.</div>
    <br>${playerTable(rows.slice(0,80))}
  </section>`;
}

function qClass(q){return q==="complete"?"good":q==="partial"?"avg":q==="limited"?"risk":"na"}
function pitchMixHtml(mix){if(!mix||!mix.length)return `<span class="sub">Not available yet</span>`;return `<div class="pill-row">${mix.slice(0,5).map(m=>`<span class="pill">${fmt(m.pitch||m.type)} ${fmt(m.pct||m.percent)}%</span>`).join("")}</div>`}

function pitcherDangerScore(p){
  if(!p || p.dataQuality === "tbd") return null;
  const mapScore = (metric, value) => {
    const g = gradeMetric(metric, value);
    if(g === "elite") return 90;
    if(g === "good") return 75;
    if(g === "avg") return 60;
    if(g === "risk") return 44;
    return 32;
  };
  const parts = [
    mapScore("hr9", p.hr9),
    mapScore("barrelA", p.barrelA),
    mapScore("hardHitA", p.hardHitA),
    mapScore("fb", p.fb),
    mapScore("gb", p.gb)
  ];
  return Math.round(parts.reduce((a,b)=>a+b,0)/parts.length);
}
function dangerText(score){
  if(score === null || score === undefined) return "TBD";
  if(score >= 80) return "Attack";
  if(score >= 68) return "Target";
  if(score >= 55) return "Neutral";
  return "Tough";
}
function mixClean(mix){
  if(!mix || !mix.length) return `<span class="pitcher-empty">Pitch mix not available yet</span>`;
  return `<div class="pitch-mix-clean">${mix.slice(0,5).map(m=>`<span class="pitch-chip">${fmt(m.pitch||m.type)} ${fmt(m.pct||m.percent)}%</span>`).join("")}</div>`;
}
function noteBlock(notes){
  if(!notes || !notes.length) return "";
  return `<div class="pitcher-notes"><details><summary>Data notes / fallbacks</summary><ul>${notes.map(n=>`<li>${n}</li>`).join("")}</ul></details></div>`;
}
function qClass(q){return q==="complete"?"good":q==="partial"?"avg":q==="limited"?"risk":"na"}

function pitchZoneFor(team){
  return state.pitchZones?.profiles?.[team] || null;
}
function zoneCell(v){
  const n = Number(v)||0;
  const cls = n>=75 ? "zone-hot" : n>=45 ? "zone-mid" : n>0 ? "zone-cool" : "zone-empty";
  return `<div class="zone-cell ${cls}"><span>${n ? n : ""}</span></div>`;
}
function pitchZoneCard(team){
  const z = pitchZoneFor(team);
  if(!z) return "";
  const status = z.status === "verified_mix" ? "Pitch mix available" : z.status === "missing" ? "Missing" : "Profile placeholder";
  const tag = z.status === "verified_mix" ? "verified" : z.status === "missing" ? "missing" : "estimated";
  return `<div class="zone-card">
    <div class="zone-head">
      <strong>Strike Zone Visual</strong>
      <span class="status-tag ${tag}">${status}</span>
    </div>
    <div class="zone-grid">
      ${(z.zoneGrid||[]).map(zoneCell).join("")}
    </div>
    <div class="pitch-frequency">
      ${(z.mix||[]).map(m=>`<span class="pitch-chip">${fmt(m.pitch)} ${fmt(m.pct)}%</span>`).join("") || `<span class="pitcher-empty">No pitch mix yet</span>`}
    </div>
    <div class="zone-note">${(z.notes||[]).slice(0,2).join(" ")}</div>
  </div>`;
}

function pitchers(){
 const rows=Object.values(pitcherProfiles()).map(p=>({...p,danger:pitcherDangerScore(p)})).sort((a,b)=>num(b.danger,-1)-num(a.danger,-1));
 return `${hero("Pitcher Lab","Clean pitcher danger board. Green target signals mean the pitcher is more attackable for home runs; gray means TBD or unavailable.")}
 <section class="card"><div class="lab-note">Read this tab from a hitter's point of view: high HR/9, high barrel allowed, high hard-hit allowed, high FB%, and low GB% are target signals. TBD pitchers show no fake data.</div></section>
 <section class="pitcher-board" style="margin-top:22px">
 ${rows.map(p=>`<article class="pitcher-card-clean">
   <div class="pitcher-top">
     <div class="pitcher-name-block">
       <strong>${fmt(p.name)}</strong>
       <span>${fmt(p.team)} · ${fmt(p.hand)}HP · <span class="metric-badge ${qClass(p.dataQuality)}"><b>${p.dataQuality}</b><small>Quality</small></span></span>
     </div>
     <div class="pitcher-danger ${gradeClass(gradeMetric("hr_edge",p.danger))}">
       <b>${fmt(p.danger,"N/A")}</b>
       <small>${dangerText(p.danger)}</small>
     </div>
   </div>
   <div class="pitcher-body">
     <div class="pitcher-section-title">Home Run Risk</div>
     <div class="pitcher-metric-grid">
       <div class="pitcher-metric">${badgeMetric("hr9",p.hr9)}<span>HR/9</span></div>
       <div class="pitcher-metric">${badgeMetric("barrelA",p.barrelA,"%")}<span>Barrel Allowed</span></div>
       <div class="pitcher-metric">${badgeMetric("hardHitA",p.hardHitA,"%")}<span>Hard-Hit Allowed</span></div>
       <div class="pitcher-metric">${badgeMetric("fb",p.fb,"%")}<span>Fly Ball Rate</span></div>
     </div>
     <div class="pitcher-section-title">Run Prevention / Batted-Ball Shape</div>
     <div class="pitcher-metric-grid">
       <div class="pitcher-metric">${badgeMetric("gb",p.gb,"%")}<span>Ground Ball Rate</span></div>
       <div class="pitcher-metric">${badgeMetric("xera",p.xera)}<span>xERA</span></div>
       <div class="pitcher-metric">${badgeMetric("fip",p.fip)}<span>FIP</span></div>
       <div class="pitcher-metric">${badgeMetric("siera",p.siera)}<span>SIERA</span></div>
     </div>
     <div class="pitcher-section-title">Pitch Mix</div>
     ${mixClean(p.mix)}
     ${pitchZoneCard(p.team)}
     ${noteBlock(p.notes)}
   </div>
 </article>`).join("")}
 </section>`;
}

function windAngle(dir){const d=String(dir||"").toLowerCase();if(d.includes("out to lf")||d.includes("out to left"))return -35;if(d.includes("out to rf")||d.includes("out to right"))return 35;if(d.startsWith("out"))return 0;if(d.startsWith("in"))return 180;if(d.includes("left to right"))return 90;if(d.includes("right to left"))return -90;return 0}
function carryImpact(g){let score=50;const temp=num(g.temp,72),wind=num(g.wind,0),hum=num(g.humidity,50),dir=String(g.windDir||"").toLowerCase();score+=(temp-72)*.7;if(dir.startsWith("out"))score+=wind*2.2;else if(dir.startsWith("in"))score-=wind*2.4;score+=(hum-50)*.08;return Math.max(0,Math.min(100,Math.round(score)))}
function carryText(s){return s>=78?"Major carry boost":s>=65?"Above-average carry":s>=52?"Slight boost / neutral":s>=40?"Suppressed carry":"Major suppression"}
function weather(){const rows=[...games()].sort((a,b)=>carryImpact(b)-carryImpact(a));return `${hero("Weather Lab","Weather is color-coded by carry impact. Green means the environment helps fly balls carry.")}<section class="weather-grid">${rows.map(g=>{const s=carryImpact(g),park=state.slate?.parks?.[g.park]||{};return `<article class="card"><div class="weather-head"><div><h3>${fmt(g.away)} @ ${fmt(g.home)}</h3><div class="sub">${fmt(park.name||g.park)} · ${fmt(g.status)}</div></div>${badgeMetric("weather",s)}</div><div class="stadium"><div class="field-lines"></div><div class="home-plate"></div><div class="outfield-label">OUTFIELD</div><div class="wind-arrow" style="transform:translate(-50%,-50%) rotate(${windAngle(g.windDir)}deg)">↑</div><div class="wind-chip">${fmt(g.wind,0)} mph · ${fmt(g.windDir,"Neutral")}</div></div><div class="weather-metrics"><div><strong>${fmt(g.temp)}°</strong><span>Temp</span></div><div><strong>${fmt(g.humidity)}%</strong><span>Humidity</span></div><div><strong>${fmt(g.wind)}</strong><span>Wind</span></div><div><strong>${fmt(park.hr)}</strong><span>Park HR</span></div></div><div class="carry-summary"><strong>${carryText(s)}</strong><span>${fmt(g.roofStatus||park.roof,"roof n/a")}</span></div></article>`}).join("")}</section>`}
function momentum(){return `${hero("Momentum Lab","Hot-form indicators are color-coded. Search for green KHR + green HR Form + green xwOBAcon.")}<section class="card">${playerTable([...players()].sort((a,b)=>num(b.profile?.hrForm)-num(a.profile?.hrForm)).slice(0,100))}</section>`}
function live(){const events=state.live?.events||[];return `${hero("Live Tracker","In-game HR feed. Blank early-day feed is normal until games begin or HR events are collected.")}<section class="card"><div class="table-wrap"><table><thead><tr><th>Type</th><th>Date</th><th>Batter</th><th>Pitcher</th><th>Inning</th><th>Pitch</th><th>EV</th><th>LA</th><th>Dist</th><th>Description</th></tr></thead><tbody>${events.map(e=>`<tr><td>${fmt(e.type)}</td><td>${fmt(e.date)}</td><td><strong>${fmt(e.batter)}</strong></td><td>${fmt(e.pitcher)}</td><td>${fmt(e.inning)}</td><td>${fmt(e.pitchType)}</td><td>${fmt(e.exitVelocity)}</td><td>${fmt(e.launchAngle)}</td><td>${fmt(e.distance)}</td><td class="wrap">${fmt(e.description||e.error)}</td></tr>`).join("")}</tbody></table></div></section>`}
function last30Dates(){const out=[];const now=new Date();for(let i=0;i<30;i++){const d=new Date(now);d.setDate(now.getDate()-i);out.push(d.toISOString().slice(0,10));}return out}

function trackerDates(){
  const hist = state.history || {};
  if(hist.dates && hist.dates.length) return hist.dates;
  const out=[];
  const now=new Date();
  for(let i=0;i<30;i++){
    const d=new Date(now);
    d.setDate(now.getDate()-i);
    out.push(d.toISOString().slice(0,10));
  }
  return out;
}
function trackerRowsForDate(dateValue){
  const hist = state.history || {};
  const byDate = hist.byDate || {};
  if(dateValue) return byDate[dateValue] || [];
  return hist.home_runs || [];
}


function hrRows(hrs){
  if(!hrs || !hrs.length){
    return `<div class="card" style="box-shadow:none"><h3>No verified home runs found for this date.</h3><p class="sub">This means either there were no MLB home runs on that date, games have not started, or the MLB feed did not return HR plays yet.</p></div>`;
  }
  return `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Batter</th><th>Team</th><th>Pitcher</th><th>Inning</th><th>Pitch</th><th>EV</th><th>LA</th><th>Dist</th><th>Verified</th><th>Description</th></tr></thead><tbody>${hrs.map(h=>`<tr><td>${fmt(h.date)}</td><td><strong>${fmt(h.batter)}</strong></td><td>${fmt(h.team)}</td><td>${fmt(h.pitcher)}</td><td>${fmt(h.inning)}</td><td>${fmt(h.pitchType)}</td><td>${fmt(h.exitVelocity)}</td><td>${fmt(h.launchAngle)}</td><td>${fmt(h.distance)}</td><td><span class="status-tag verified">MLB</span></td><td class="wrap">${fmt(h.description)}</td></tr>`).join("")}</tbody></table></div>`;
}


function tracker(){
  const hist = state.history || {};
  const dates = trackerDates();
  const hrs = hist.home_runs || [];
  return `${hero("HR Tracker","Verified MLB home run history. Select any of the last 30 dates to see actual home runs from the MLB game feed.")}
  <section class="card">
    <div class="lab-note">Source: ${fmt(hist.source,"MLB Stats API game feed")} | Updated: ${fmt(hist.updatedAt,"N/A")} | Loaded HRs: ${hrs.length}</div>
    <br>
    <div class="searchbar">
      <select id="dateFilter"><option value="">All dates</option>${dates.map(d=>`<option value="${d}">${d}</option>`).join("")}</select>
      <input id="playerFilter" placeholder="Filter player..." />
    </div>
    <div id="trackerCount" class="sub" style="text-align:center;margin-bottom:12px">${hrs.length} verified HRs loaded.</div>
    <div id="trackerTable">${hrRows(hrs)}</div>
  </section>`;
}

function ai(){return `${hero("AI Report","Every recommendation explains which green/yellow/red factors are stacking together.")}<section class="report-box">${players().slice(0,25).map(p=>`<article class="report-player"><div class="player-title"><div><strong>${p.name}</strong><div class="sub">${p.team} · order ${fmt(p.order)} · vs ${fmt(p.pitcher)}</div></div>${badgeMetric("hr_edge",p.scores?.hr_edge)}</div><ul class="factor-list"><li>Model probability: ${fmt(p.scores?.model_probability)}%</li><li>Stack score: ${fmt(p.scores?.stack_score)}</li><li>Sample: ${fmt(p.profile?.sampleSize, 'N/A')} PA · reliability ${fmt(p.scores?.sample_reliability, 'N/A')}</li><li>Raw HR Edge before sample shrinkage: ${fmt(p.scores?.raw_hr_edge, 'N/A')}</li><li>Sample-adjusted edge: ${fmt(p.scores?.sample_adjusted_edge, 'N/A')}</li><li>Pitcher fields used: ${fmt((p.provenance?.pitcherFieldsUsed||[]).join(', '),'N/A')}</li><li>ISO status: ${fmt(p.provenance?.isoStatus)}</li><li>xwOBAcon status: ${fmt(p.provenance?.xwobaconStatus)}</li><li>KHR: ${fmt(p.profile?.khr)}</li><li>Zone fit: ${fmt(p.profile?.zoneFit)}</li><li>Matchup: ${fmt(p.profile?.matchup,"N/A")}</li>${(p.reasons||[]).map(r=>`<li>${r}</li>`).join("")}</ul></article>`).join("")}</section>`}
function guide(){
 const batter=[["HR Edge","75+ elite, 65–74 good, 55–64 average, below 55 caution."],["Model Probability","18%+ elite, 14–18 good, 10–14 average, 6–10 low, under 6 poor."],["KHR","Composite HR-read score. Look for 70+."],["Blast%","Power/contact violence. 14+ elite, 11+ good."],["ISO",".280+ elite, .240+ good, .190+ average."],["xwOBAcon",".520+ elite, .480+ good, .440+ average."],["Zone Fit","Shows whether the hitter profile fits the expected attack shape. 70+ is strong."],["Stack Score","Most important tie-breaker. 75+ means multiple independent factors align."]];
 const pitcher=[["HR/9","Higher is better for hitters. 1.60+ is a major target."],["Barrel Allowed","10%+ is highly targetable."],["HardHit Allowed","46%+ is highly targetable."],["FB%","44%+ means more air-ball exposure."],["GB%","Lower is better for HR hunting. Under 36% is targetable."],["xERA/FIP/SIERA","Higher means weaker run-prevention skill. 4.80+ is highly targetable."]];
 return `${hero("How to Read the Model","Use this guide to quickly understand what the colors mean and which combinations matter most.")}
 <section class="guide-strip"><span class="legend elite">Elite / Strong Target</span><span class="legend good">Good</span><span class="legend avg">Average</span><span class="legend risk">Caution</span><span class="legend poor">Poor / Tough</span><span class="legend na">Unavailable</span></section>
 <section class="grid"><div class="card"><h3>Batter Signals</h3>${batter.map(([t,m])=>`<div class="guide-row"><strong>${t}</strong><p>${m}</p></div>`).join("")}</div><div class="card"><h3>Pitcher Target Signals</h3>${pitcher.map(([t,m])=>`<div class="guide-row"><strong>${t}</strong><p>${m}</p></div>`).join("")}</div><div class="card"><h3>What to Look For</h3><ul class="factor-list"><li>Best spots usually have 4–6 green signals, not just one high stat.</li><li>Prioritize green Stack Score + green KHR + green Matchup + positive Weather.</li><li>TBD pitchers reduce confidence and should not show fake neutral values.</li><li>For longshots, look for lower-lineup hitters with green Blast, ISO, Zone Fit, and a targetable pitcher.</li></ul></div></section>`;
}
function glossary(){const sections=state.glossary?.sections||[];return `${hero("Glossary","Plain-English definitions for the metrics, abbreviations, and model scores used throughout the app.")}<section class="grid">${sections.map(s=>`<div class="card"><h3>${s.title}</h3>${s.items.map(i=>`<div class="report-player" style="margin-bottom:12px"><strong>${i.term}</strong><p class="sub">${i.meaning}</p></div>`).join("")}</div>`).join("")}</section>`}
function render(){const map={dashboard,hrlab,longshots,pitchers,weather,momentum,live,tracker,ai,guide,glossary};$("#content").innerHTML=(map[state.tab]||dashboard)();if(state.tab==="tracker"){const dateFilter=$("#dateFilter"),playerFilter=$("#playerFilter");const apply=()=>{const d=dateFilter.value,q=playerFilter.value.toLowerCase();const byDate=state.history?.byDate||{};const base=d?(byDate[d]||[]):(state.history?.home_runs||[]);const rows=base.filter(h=>(!q||String(h.batter||"").toLowerCase().includes(q)));$("#trackerCount").textContent=`${rows.length} verified HRs ${d?`on ${d}`:"loaded"}.`;$("#trackerTable").innerHTML=hrRows(rows)};dateFilter.addEventListener("change",apply);playerFilter.addEventListener("input",apply)}}
document.addEventListener("click",e=>{const btn=e.target.closest("[data-tab]");if(!btn)return;document.querySelectorAll("[data-tab]").forEach(b=>b.classList.remove("active"));btn.classList.add("active");state.tab=btn.dataset.tab;render()});
if("serviceWorker"in navigator)navigator.serviceWorker.register("sw.js").catch(()=>{});
loadData();setInterval(loadData,60000);
