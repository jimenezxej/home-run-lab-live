const state={dashboard:null,selected:null};
const $=s=>document.querySelector(s);
const fmt=(v,d="—",digits=null)=>v===null||v===undefined||v===""?d:(digits!==null&&Number.isFinite(Number(v))?Number(v).toFixed(digits):String(v));
async function loadJSON(name,fallback){
 const base=location.pathname.includes("/home-run-lab-live/")?"/home-run-lab-live/":"./";
 for(const url of [`./${name}`,`${base}${name}`,`./data/${name}`,`${base}data/${name}`]){
  try{const r=await fetch(`${url}?v=${Date.now()}`,{cache:"no-store"});if(r.ok)return await r.json()}catch(e){}
 }
 return fallback;
}
function stat(label,value,digits=null){return `<div class="stat-box"><small>${label}</small><strong>${fmt(value,"—",digits)}</strong></div>`}
function card(p){
 const prob=p.probability===null||p.probability===undefined?"—":`${Number(p.probability).toFixed(1)}%`;
 return `<article class="player-card" data-player="${encodeURIComponent(p.name)}" data-team="${p.team}">
 <div class="player-name">${p.name}</div>
 <div class="player-sub">${p.team} · ${p.lineupOrder?`Batting ${p.lineupOrder}`:"Lineup TBD"}</div>
 <div class="player-score">${Number(p.score||0).toFixed(1)}</div>
 <div class="mini-grid">
  <div><small>PROB</small><strong>${prob}</strong></div>
  <div><small>SOURCE</small><strong>${p.probabilitySource||"model"}</strong></div>
  <div><small>LONGSHOT</small><strong>${Number(p.longshotScore||0).toFixed(1)}</strong></div>
 </div></article>`
}
function render(){
 const games=state.dashboard?.games||[];
 if(!games.length){$("#gameView").innerHTML='<div class="empty">No game intelligence data available.</div>';return}
 if(!state.selected)state.selected=games[0].id;
 const g=games.find(x=>x.id===state.selected)||games[0];

 $("#overviewGrid").innerHTML=[
  ["Games",games.length],
  ["Top Hitter",g.topHitter?.name||"—"],
  ["Top-10 Avg",fmt(g.top10Average,"—",1)],
  ["Weather",fmt(g.weatherScore,"—",1)]
 ].map(([a,b])=>`<div class="metric-card"><small>${a}</small><strong>${b}</strong></div>`).join("");

 $("#gameSelect").innerHTML=games.map(x=>`<option value="${x.id}" ${x.id===g.id?"selected":""}>${x.away} @ ${x.home}</option>`).join("");
 $("#gameStrip").innerHTML=games.map(x=>`<button class="game-pill ${x.id===g.id?"active":""}" data-game="${x.id}">${x.away} @ ${x.home}</button>`).join("");

 $("#gameView").innerHTML=`
 <section class="game-hero">
  <p class="eyebrow">GAME DASHBOARD</p>
  <h2 class="game-title">${g.away} @ ${g.home}</h2>
  <div class="score-band">
   ${stat("GAME SCORE",g.gameScore,1)}
   ${stat("TOP HITTER",g.topHitter?.name)}
   ${stat("TOP-10 AVG",g.top10Average,1)}
   ${stat("WEATHER",g.weatherScore,1)}
  </div>
 </section>
 <section class="content-card">
  <h3>Top Reads In This Game</h3>
  <div class="player-grid">${(g.topReads||[]).map(card).join("")||'<div class="empty">No top reads.</div>'}</div>
 </section>
 <section class="content-card">
  <h3>All Hitters</h3>
  <div class="player-grid">${(g.players||[]).map(card).join("")}</div>
 </section>
 <section class="content-card">
  <h3>Game Longshots</h3>
  <div class="player-grid">${(g.longshots||[]).map(card).join("")||'<div class="empty">No longshots qualified.</div>'}</div>
 </section>`;

 document.querySelectorAll(".player-card").forEach(el=>el.onclick=()=>{
  const p=(g.players||[]).find(x=>x.name===decodeURIComponent(el.dataset.player)&&x.team===el.dataset.team);
  if(!p)return;
  $("#playerModalBody").innerHTML=`<div class="profile-head"><p class="eyebrow">${p.team} PROFILE</p><h2>${p.name}</h2></div>
  <div class="profile-score">${stat("HR EDGE",p.score,1)}${stat("PROBABILITY",p.probability===null?null:`${Number(p.probability).toFixed(1)}%`)}${stat("LONGSHOT",p.longshotScore,1)}</div>
  <div class="profile-section"><h3>Why</h3><div class="reason-box">${p.why||"No verified explanation available."}</div></div>`;
  $("#playerModal").classList.remove("hidden");
 });
}
async function loadData(){
 $("#updateChip").textContent="Updating…";
 state.dashboard=await loadJSON("game-dashboard.json",{games:[]});
 $("#updateChip").textContent="Live data";
 render();
}
$("#gameSelect").onchange=e=>{state.selected=e.target.value;render()};
$("#gameStrip").onclick=e=>{const b=e.target.closest("[data-game]");if(b){state.selected=b.dataset.game;render()}};
$("#refreshBtn").onclick=loadData;
$("#closeModal").onclick=()=>$("#playerModal").classList.add("hidden");
$("#playerModal").onclick=e=>{if(e.target.id==="playerModal")$("#playerModal").classList.add("hidden")};
loadData();
