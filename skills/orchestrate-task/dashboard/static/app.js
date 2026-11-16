"use strict";
// Run board: reads /api/state, shows one decision at a time, writes answers via /api/answer.

const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const cap = s => { s = String(s || ""); return s.charAt(0).toUpperCase() + s.slice(1); };
const sigColor = {d:"var(--done)", n:"var(--green)", w:"var(--amber)", b:"var(--red)", t:"var(--track)", p:"var(--ink-3)"};
const POLL_MS = 4000;

// ---------- token ----------
let TOKEN = "";
(function(){
  const m = location.hash.match(/t=([A-Za-z0-9_-]+)/);
  try {
    if (m) { sessionStorage.setItem("runboard-token", m[1]); }
    TOKEN = (m && m[1]) || sessionStorage.getItem("runboard-token") || "";
  } catch (e) { TOKEN = m ? m[1] : ""; }
  if (m) history.replaceState(null, "", location.pathname);
})();

async function api(path, body){
  const opt = {headers: {"X-Token": TOKEN}};
  if (body !== undefined){ opt.method = "POST"; opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
  const r = await fetch(path, opt);
  const ct = r.headers.get("Content-Type") || "";
  const data = ct.includes("json") ? await r.json() : await r.blob();
  if (!r.ok) throw new Error((data && data.error) || `Request failed (${r.status})`);
  return data;
}

// ---------- state ----------
let S = null, sig = "", shownId = null, picked = null, touched = false, pinned = false, filter = "All", lastError = "";
const sentLocal = new Set();

function openCards(){ return S ? S.cards.filter(c => !c.sent && !sentLocal.has(c.id)) : []; }

async function poll(){
  try {
    const d = await api("/api/state" + (sig ? "?since=" + encodeURIComponent(sig) : ""));
    if (lastError){ lastError = ""; banner(); }
    if (d.unchanged) return;
    sig = d.sig; S = d;
    S.cards.forEach(c => { if (c.sent) sentLocal.delete(c.id); });
    render();
  } catch (e) {
    lastError = e.message.includes("token") ? e.message : "Can't reach the dashboard server. Is it still running?";
    banner();
  } finally {
    clearTimeout(poll.t); poll.t = setTimeout(poll, POLL_MS);
  }
}

function render(){
  header(); banner(); bar(); syncCard(); renderQueue(); renderSent(); renderFeed(); renderTracks();
  if ($("#drawer").classList.contains("open") && openDrawer.id) openDrawer(openDrawer.id, true);
}

// ---------- header ----------
function header(){
  const r = S.run;
  document.title = r.title + " · Run board";
  $("#title").textContent = r.title;
  const n = S.milestones.length;
  $("#meta").textContent = `${r.platform ? "Run on " + r.platform + " with " : ""}${n} milestone${n===1?"":"s"}. ` +
    (r.last_tick ? `Orchestrator last checked at ${r.last_tick}.` : "");
  const b = S.counts.blockers, y = openCards().length;
  $("#c-block").textContent = b ? `${b} blocker${b===1?"":"s"}` : "No blockers";
  $("#chip-block").className = b ? "chip red" : "chip";
  $("#dot-block").style.background = b ? "var(--red)" : "var(--green)";
  $("#c-you").textContent = y ? `${y} for you` : "Nothing for you";
  $("#chip-you").className = y ? "chip amber" : "chip";
  $("#dot-you").style.background = y ? "var(--amber)" : "var(--green)";
  $("#c-ship").textContent = `Shipped ${S.counts.shipped} of ${S.counts.milestones}`;
}

function banner(){
  const el = $("#banner");
  if (lastError){ el.className = "banner err show"; el.textContent = lastError; return; }
  if (S && !S.run.found){ el.className = "banner warn show"; el.textContent = "This folder has no REGISTER.md yet. The board fills in once the orchestrator starts the run."; return; }
  if (S && S.run.stale){
    const mins = Math.round((Date.now()/1000 - S.run.register_changed) / 60);
    el.className = "banner warn show";
    el.textContent = `The orchestrator hasn't updated the run for ${mins} minutes. Answers you send wait until it checks again; if it stopped, resume it in its chat.`;
    return;
  }
  el.className = "banner";
}

function bar(){
  const cells = S.progress.cells;
  $("#bar").innerHTML = cells.map(s => `<span class="${s==="t"?"":esc(s)}"></span>`).join("");
  $("#pct").textContent = S.progress.total ? `${S.progress.done} of ${S.progress.total} goals done` : "No goals yet";
}

// ---------- card ----------
function syncCard(){
  const list = openCards(), top = list[0];
  const shown = list.find(c => c.id === shownId);
  const notice = $("#notice");
  if (shownId && !shown && !$("#sent-ok")){
    notice.innerHTML = `${esc(shownId)} was answered or closed elsewhere, probably in the chat. Showing the next one.`;
    notice.classList.add("show"); setTimeout(() => notice.classList.remove("show"), 6000);
  }
  if (shown && (touched || pinned)){
    if (top && top.id !== shownId && top.queue === "blocker" && shown.queue !== "blocker"){
      notice.innerHTML = `A blocker just arrived: ${esc(top.id)}, ${esc(top.headline)}. <button class="btn" id="go-top">Show it</button>`;
      notice.classList.add("show");
      $("#go-top").onclick = () => { notice.classList.remove("show"); showCard(top); renderQueue(); };
    }
    return;
  }
  if ($("#sent-ok")) return; // confirmation on screen; moves on by itself
  if (!top){ return showEmpty(); }
  if (top.id !== shownId || !shown || JSON.stringify(top) !== showCard.json) showCard(top);
}

function cardOptions(c){
  if (c.options.length) return c.options;
  return [{k:"ok", title: c.recommend ? `OK: ${c.recommend}` : "OK", good: "", cost: ""}];
}

function showEmpty(){
  shownId = null; touched = false; pinned = false; showCard.json = "";
  const el = $("#card");
  el.className = "panel card empty"; el.style.borderLeftColor = "var(--green)";
  el.innerHTML = `<h3>Nothing needs you right now</h3><p>All milestones are moving. New decisions appear here, and the activity list shows what changed.</p>`;
}

function showCard(c, pin){
  shownId = c.id; touched = false; pinned = !!pin; showCard.json = JSON.stringify(c);
  $("#notice").classList.remove("show");
  const opts = cardOptions(c);
  picked = c.options.length ? (c.recommend && opts.some(o => o.k === c.recommend) ? c.recommend : null) : "ok";
  const el = $("#card");
  el.style.borderLeftColor = "";
  const kindClass = c.kind === "blocker" ? "blocker" : (c.kind === "question" ? "question" : "merge");
  el.className = "panel card kind-" + kindClass;
  const tag = {blocker:["red","Blocker"], merge:["amber","Merge"], prod:["amber","Prod approval"], gate:["amber","Approval"], question:["blue","Question"]}[c.kind] || ["blue", cap(c.kind)];
  const age = c.opened ? `${c.queue==="blocker"?"Open since":"Asked at"} ${c.opened}.` : "";
  el.innerHTML = `
    <div class="card-head"><span class="tag ${tag[0]}">${esc(tag[1])} ${esc(c.id)}</span>${c.milestone?`<span class="tag plain lbl">${esc(c.milestone)}</span>`:""}<span class="muted">${esc(age)}${c.queue==="open"?" Open in the chat too.":""}</span></div>
    <h3>${esc(c.headline || "(no headline)")}</h3>
    ${c.body?`<p>${esc(c.body)}</p>`:""}
    ${c.facts.length?`<dl class="facts">${c.facts.map(f=>`<dt>${esc(f.k)}</dt><dd${f.verified===true?' class="verified"':f.verified===false?' class="claimed"':""}>${esc(f.v)}</dd>`).join("")}</dl>`:""}
    ${c.proof.length?`<div class="proof">${c.proof.map(p=>`<span>✓ ${esc(p)}</span>`).join("")}</div>`:""}
    ${c.now||c.after?`<div class="nowafter"><div><small>Now</small>${esc(c.now)}</div><span class="arrow muted">to</span><div><small>After</small>${esc(c.after)}</div></div>`:""}
    ${c.undo?`<p><b>Undo:</b> ${esc(c.undo)}</p>`:""}
    <div class="options" role="radiogroup" aria-label="Options">
      ${opts.map(o=>`<div class="opt" role="radio" tabindex="0" data-k="${esc(o.k)}" aria-checked="${o.k===picked}">
        <span class="key">${o.k==="ok"?"✓":esc(o.k)}</span>
        <div><div class="opt-title">${esc(o.title)} ${o.k===c.recommend?'<span class="pick">Recommended</span>':""}${c.options.length?`<button class="ask-link" data-ask="${esc(o.k)}" type="button">Ask</button>`:""}</div>
        ${o.good||o.cost?`<div class="opt-sub">${o.good?`<b>Good:</b> ${esc(o.good)}. `:""}${o.cost?`<b>Cost:</b> ${esc(o.cost)}.`:""}</div>`:""}</div></div>`).join("")}
    </div>
    ${c.why?`<div class="why"><b>Why ${esc(c.recommend)}:</b> ${esc(c.why)}</div>`:""}
    ${!c.has_card_file?`<p class="hint">The orchestrator didn't write a full card for this one, so only the question and its recommendation are shown. You can also write your own answer below.</p>`:""}
    <label class="sr" for="note">Note for the orchestrator</label>
    <textarea id="note" placeholder="${c.options.length?"Add an instruction for the orchestrator (optional)":"Or write a different answer"}"></textarea>
    <div class="err" id="err" role="alert"></div>
    <div class="actions">
      <button class="btn primary" id="send">Send answer</button>
      <button class="btn" id="ask">Ask about this</button>
      ${c.evidence.length?`<button class="btn" id="ev">Show evidence</button>`:""}
      ${c.options.length>1?`<span class="hint">Keys 1 to ${c.options.length} pick an option.</span>`:""}
    </div>`;
  el.querySelectorAll(".opt").forEach(o => {
    o.onclick = () => choose(o.dataset.k);
    o.onkeydown = e => { if (e.key===" "||e.key==="Enter"){ e.preventDefault(); choose(o.dataset.k); } };
  });
  $("#send").onclick = () => send(c);
  $("#ask").onclick = () => openChat({card:c});
  if ($("#ev")) $("#ev").onclick = () => openViewer(c.evidence, `Evidence for ${c.id}`);
  el.querySelectorAll(".ask-link").forEach(a => a.onclick = e => { e.stopPropagation(); openChat({card:c, opt:a.dataset.ask}); });
  $("#note").oninput = () => { $("#err").textContent = ""; touched = true; };
}

function choose(k){
  picked = k; touched = true;
  document.querySelectorAll(".opt").forEach(o => o.setAttribute("aria-checked", o.dataset.k === k));
  $("#err").textContent = "";
}

async function send(c){
  const note = $("#note").value.trim();
  if (!picked && !note){ $("#err").textContent = "Pick an option or write an answer first."; return; }
  const btn = $("#send"); btn.disabled = true; btn.textContent = "Sending…";
  try {
    const choice = picked === "ok" && !c.options.length && note ? "" : picked || "";
    const r = await api("/api/answer", {card: c.id, choice, note});
    sentLocal.add(c.id);
    const opt = cardOptions(c).find(o => o.k === picked);
    const what = choice ? `${choice==="ok"?"OK":choice}${opt && choice!=="ok" ? ". " + opt.title : ""}` : "your written answer";
    const tickMin = Math.max(1, Math.round((S.run.heartbeat_s || 300) / 60));
    $("#card").querySelector(".actions").outerHTML =
      `<div class="sent show" id="sent-ok"><b>Answer sent: ${esc(what)}.</b><br>Saved as ${esc(r.id)} in ANSWERS.md${note?" with your note":""}. The orchestrator applies it on its next check, within about ${tickMin} minute${tickMin===1?"":"s"}.</div>`;
    document.querySelectorAll(".opt").forEach(o => { o.onclick = null; o.tabIndex = -1; });
    $("#note").disabled = true;
    S.sent = (S.sent || []).concat([{id:r.id, card:c.id, choice, time:r.time}]);
    renderSent(); renderQueue(); header();
    setTimeout(() => { shownId = null; const n = openCards()[0]; n ? showCard(n) : showEmpty(); renderQueue(); $("#card").focus(); toast(n ? "Next decision is up." : "All decisions answered."); }, 2200);
  } catch (e) {
    $("#err").textContent = e.message; btn.disabled = false; btn.textContent = "Send answer";
  }
}

// ---------- side lists ----------
function renderQueue(){
  const rest = openCards().filter(c => c.id !== shownId);
  const col = {blocker:"var(--red)", merge:"var(--amber)", prod:"var(--amber)", gate:"var(--amber)", question:"var(--blue)"};
  $("#queue").innerHTML = rest.length ? rest.map(c => `<li><span class="sig" style="background:${col[c.kind]||"var(--blue)"}"></span>
     <div><button class="link-btn" data-id="${esc(c.id)}">${esc(c.headline)}</button><div class="sub lbl">${esc(c.id)} · ${esc(c.milestone)}</div></div></li>`).join("")
    : `<li><span class="sig" style="background:var(--green)"></span><div>Nothing else is waiting.</div></li>`;
  $("#queue").querySelectorAll(".link-btn").forEach(b => b.onclick = () => { const c = openCards().find(x => x.id === b.dataset.id); if (c){ showCard(c, true); renderQueue(); $("#card").focus(); } });
}

function renderSent(){
  const list = (S.sent || []);
  $("#sent-panel").hidden = !list.length;
  $("#sent").innerHTML = list.map(a => `<li><span class="sig"></span><div>${esc(a.card ? `${a.card}: ${a.choice || "written answer"}` : a.command)}<div class="sub">${esc(a.id)} · sent ${esc((a.time||"").slice(11,16))}</div></div></li>`).join("");
}

function renderFeed(){
  const ids = ["All", ...S.milestones.map(m => m.id).sort((a,b)=>a.localeCompare(b, undefined, {numeric:true}))];
  if (!ids.includes(filter)) filter = "All";
  $("#filters").innerHTML = ids.map(i => `<button class="f" aria-pressed="${i===filter}" data-f="${esc(i)}">${esc(i)}</button>`).join("");
  $("#filters").querySelectorAll(".f").forEach(b => b.onclick = () => { filter = b.dataset.f; renderFeed(); });
  const silent = $("#show-silent").checked;
  const rows = S.feed.filter(f => (filter==="All" || f.m===filter) && (silent || f.lane !== "silent"));
  $("#feed-count").textContent = rows.length > 12 ? `Latest 12 of ${rows.length}` : "";
  const name = id => (S.milestones.find(x => x.id === id) || {}).label || id;
  $("#feed").innerHTML = rows.slice(0, 12).map(f => `<li><time>${esc(f.time)}</time><div><span class="lbl">${esc(name(f.m) || f.goal)}${f.goal && f.goal.includes(".g") ? " · " + esc(f.goal.split(".")[1]) : ""}</span><br>${esc(f.text)}${f.link?` <button class="link-btn" data-path="${esc(f.link.split("#")[0])}">Open</button>`:""}</div></li>`).join("")
    || `<li><time></time><div>No activity${filter==="All"?"":" for " + esc(filter)} yet.</div></li>`;
  $("#feed").querySelectorAll(".link-btn").forEach(b => b.onclick = () => openViewer([b.dataset.path], b.dataset.path));
}
$("#show-silent").onchange = () => S && renderFeed();

// ---------- tracks ----------
function track(m){
  const n = m.goals.length + (m.merge ? 1 : 0);
  const done = m.goals.filter(g => g.s==="d").length + (m.merge==="d" ? 1 : 0);
  const pct = n > 1 ? Math.max(0, (done-1)/(n-1))*100 : 0;
  const stations = m.goals.map(g => { const k = g.id.split(".").pop(); return `<span class="stn ${g.s==="t"?"":esc(g.s)}" title="${esc(k)}: ${esc(g.title)}"><em>${esc(k)}</em></span>`; }).join("")
    + (m.merge ? `<span class="stn m ${m.merge==="t"?"":esc(m.merge)}" title="Merge"><em>merge</em></span>` : "");
  return `<button class="trk" data-id="${esc(m.id)}" aria-label="${esc(m.label)}: ${esc(m.stateLine)}. Open details">
    <div class="trk-name"><span class="lbl">${esc(m.label)}</span><span class="muted">${m.goals.filter(g=>g.s==="d").length} of ${m.goals.length} goals · lease: ${esc(m.lease)}</span></div>
    <div class="line"><span class="fill" style="width:calc(${pct}% - ${pct>0?16*pct/100:0}px)"></span>${stations}</div>
    <div class="trk-state"><b><span class="dot" style="background:${sigColor[m.st]||"var(--track)"}"></span>${esc(m.stateLine)}</b><span class="muted">${esc(m.now ? cap(m.now) + "." : "")}${m.asks.length?` Asks: ${esc(m.asks.join(", "))}.`:""}</span></div>
  </button>`;
}

function renderTracks(){
  $("#tracks").innerHTML = S.milestones.length ? S.milestones.map(track).join("") : `<div class="skeleton">No milestones in REGISTER.md yet.</div>`;
  $("#tracks").querySelectorAll(".trk").forEach(t => t.onclick = () => openDrawer(t.dataset.id));
}

// ---------- drawer ----------
let lastFocus = null;
function openDrawer(id, refresh){
  const m = S.milestones.find(x => x.id === id);
  if (!m){ return closeDrawer(); }
  openDrawer.id = id;
  if (!refresh) lastFocus = document.activeElement;
  const word = {d:"Done", n:"Working", w:"Waiting on you", b:"Blocked", t:"Not started", p:"Paused"};
  const feed = S.feed.filter(f => f.m === m.id).slice(0, 6);
  const paused = m.stateLine === "Paused" || m.milestone_state === "on-hold";
  $("#drawer").innerHTML = `
    <div class="drawer-head"><div><h3 id="dt" style="font-size:18px">${esc(m.label)}</h3><div class="muted" style="font-size:13px">${esc(m.stateLine)}.${m.updated?` Status written ${esc(m.updated.replace("T"," "))}.`:""}</div></div>
    <button class="btn" id="close">Close</button></div>
    ${m.blocked?`<div class="section"><h4>Blocked</h4><dl class="kv"><dt>Needs</dt><dd>${esc(m.blocked.need)}</dd><dt>Why</dt><dd>${esc(m.blocked.diagnosis)}</dd></dl></div>`:""}
    <div class="section"><h4>Goals</h4>
      ${m.goals.map(g => `<div class="goal"><span class="stn ${g.s==="t"?"":esc(g.s)}"></span><div><div class="goal-t">${esc(g.id.split(".").pop())}. ${esc(g.title)}</div>
      <div class="goal-s">${word[g.s]||""}${g.review?`. Review: ${esc(g.review)}`:""}${g.gate&&g.gate!=="n/a"?`. Approval: ${esc(g.gate)}`:""}</div>
      ${g.evidence.length?`<div class="files">${g.evidence.map(p=>`<button data-path="${esc(p)}">${esc(p.replace(/\/$/,"").split("/").pop())}</button>`).join("")}</div>`:""}</div></div>`).join("") || "<p class='muted'>No goals recorded.</p>"}
    </div>
    <div class="section"><h4>Latest</h4><ul class="list feed" style="border:1px solid var(--line);border-radius:8px">
      ${feed.map(f => `<li><time>${esc(f.time)}</time><div>${esc(f.text)}</div></li>`).join("") || "<li><time></time><div>No events yet.</div></li>"}
    </ul></div>
    <div class="section"><h4>Details</h4><dl class="kv">
      <dt>Lease</dt><dd>${esc(m.lease)}</dd>
      ${m.next?`<dt>Next step</dt><dd>${esc(m.next)}</dd>`:""}
      ${m.session?`<dt>Session</dt><dd>${esc(m.session)}</dd>`:""}
      <dt>Status file</dt><dd><button class="link-btn" data-path="${esc(m.status_file)}">${esc(m.status_file)}</button></dd>
    </dl></div>
    <div class="section actions">
      ${m.milestone_state==="active"?`<button class="btn" id="d-pause">${paused?"Resume":"Pause"} ${esc(m.id)}</button>`:""}
      <button class="btn" id="d-ask">Ask about ${esc(m.id)}</button>
    </div>
    <div class="confirm" id="confirm" role="alertdialog" aria-labelledby="cf-t">
      <div id="cf-t"></div>
      <div class="actions"><button class="btn primary" id="cf-yes"></button><button class="btn" id="cf-no">Cancel</button></div>
    </div>`;
  if (!refresh){ $("#drawer").classList.add("open"); $("#scrim").classList.add("open"); $("#close").focus(); }
  $("#close").onclick = closeDrawer;
  $("#drawer").querySelectorAll("[data-path]").forEach(b => b.onclick = () => openViewer([b.dataset.path], b.dataset.path));
  $("#d-ask").onclick = () => { closeDrawer(); openChat({ms:m}); };
  if ($("#d-pause")){
    const verb = paused ? "resume" : "pause";
    $("#d-pause").onclick = () => {
      $("#cf-t").textContent = verb === "pause"
        ? `Pause ${m.id}? Its session stops after its current step and keeps its work. Other milestones keep going.`
        : `Resume ${m.id}? It picks up where it stopped.`;
      $("#cf-yes").textContent = `${cap(verb)} ${m.id}`;
      $("#confirm").classList.add("show"); $("#cf-yes").focus();
    };
    $("#cf-no").onclick = () => $("#confirm").classList.remove("show");
    $("#cf-yes").onclick = async () => {
      try {
        const r = await api("/api/command", {command: verb, milestone: m.id});
        $("#confirm").classList.remove("show");
        toast(`Sent as ${r.id}. The orchestrator will ${verb} ${m.id} on its next check.`);
        poll();
      } catch (e) { toast(e.message); }
    };
  }
}
function closeDrawer(){ openDrawer.id = null; $("#drawer").classList.remove("open"); $("#scrim").classList.remove("open"); if (lastFocus) lastFocus.focus(); }
$("#scrim").onclick = () => { closeViewer(); closeDrawer(); };

// ---------- evidence viewer ----------
let viewerReturn = null;
async function openViewer(paths, title){
  if (!$("#viewer").classList.contains("open")) viewerReturn = document.activeElement;
  $("#vt").textContent = title;
  $("#viewer").classList.add("open"); $("#scrim").classList.add("open");
  $("#viewer-close").focus();
  const body = $("#viewer-body");
  if (paths.length > 1){
    body.innerHTML = `<ul>${paths.map(p => `<li><button class="link-btn" data-path="${esc(p)}">${esc(p)}</button></li>`).join("")}</ul>`;
    body.querySelectorAll("[data-path]").forEach(b => b.onclick = () => openViewer([b.dataset.path], b.dataset.path));
    return;
  }
  const p = paths[0];
  body.innerHTML = `<p class="muted">Loading ${esc(p)}…</p>`;
  try {
    const d = await api("/api/file?path=" + encodeURIComponent(p));
    if (d instanceof Blob){
      const url = URL.createObjectURL(d);
      body.innerHTML = `<img alt="${esc(p)}" src="${url}">`;
      return;
    }
    if (d.kind === "dir"){
      body.innerHTML = d.items.length ? `<ul>${d.items.map(i => `<li><button class="link-btn" data-path="${esc(i.path)}">${esc(i.name)}</button><span class="muted">${i.size!=null?fmtSize(i.size):""}</span></li>`).join("")}</ul>` : `<p class="muted">This folder is empty.</p>`;
      body.querySelectorAll("[data-path]").forEach(b => b.onclick = () => openViewer([b.dataset.path], b.dataset.path));
    } else if (d.kind === "binary"){
      body.innerHTML = `<p>This is a binary file (${fmtSize(d.size)}), so it can't be shown here.</p>`;
    } else {
      body.innerHTML = `${d.truncated?`<p class="muted">Showing the first 512 KB of ${fmtSize(d.size)}.</p>`:""}<pre></pre>`;
      body.querySelector("pre").textContent = d.text;
    }
  } catch (e) { body.innerHTML = `<p class="chat-err">${esc(e.message)}</p>`; }
}
const fmtSize = n => n < 1024 ? `${n} B` : n < 1048576 ? `${(n/1024).toFixed(1)} KB` : `${(n/1048576).toFixed(1)} MB`;
function closeViewer(){ $("#viewer").classList.remove("open"); if (!$("#drawer").classList.contains("open")) $("#scrim").classList.remove("open"); if (viewerReturn) viewerReturn.focus(); }
$("#viewer-close").onclick = closeViewer;

// ---------- side chat ----------
let chatCtx = null, chatReturn = null, thread = [], busy = false;
function ctxKey(c){ return c.card ? c.card.id + (c.opt ? "-opt" + c.opt : "") : c.ms.id; }
function ctxLabel(c){
  if (c.card) return `About: ${c.card.id}, ${c.card.milestone}${c.opt ? `, option ${c.opt}` : ""}`;
  return `About: ${c.ms.label}`;
}
function suggestions(c){
  if (c.opt) return [`What exactly changes with option ${c.opt}?`, `What could go wrong with ${c.opt}?`, `How long would ${c.opt} take?`];
  if (c.card && c.card.kind === "blocker") return ["Why did this happen?", "Show me the evidence", "What else is affected if we wait?"];
  if (c.card && c.card.kind === "merge") return ["What's in this merge?", "What was tested on this exact head?", "What happens after I merge?"];
  if (c.card && c.card.kind === "prod") return ["What exactly runs on production?", "How do we undo it?", "What does it cost?"];
  if (c.card) return ["Why does this need me?", "What happens if I wait?"];
  return [`What is ${c.ms.id} doing right now?`, `What's left for ${c.ms.id}?`, `Any risks for ${c.ms.id}?`];
}
function renderThread(){
  const canNote = chatCtx.card && $("#note") && !$("#note").disabled && shownId === chatCtx.card.id;
  $("#msgs").innerHTML = thread.length ? thread.map((m,i) => m.who === "me"
      ? `<div class="msg me">${esc(m.text)}</div>`
      : `<div class="msg ai">${esc(m.text)}${m.src?`<span class="src">From: ${esc(m.src)}</span>`:""}${canNote?`<button class="btn use" data-i="${i}">Add to my answer as a note</button>`:""}</div>`).join("")
    : `<div class="typing">Ask anything about this. The helper reads the plan, the milestone's status, evidence and reviews.</div>`;
  if (busy) $("#msgs").insertAdjacentHTML("beforeend", `<div class="typing">Reading the run files… this can take a minute.</div>`);
  $("#msgs").querySelectorAll(".use").forEach(b => b.onclick = () => {
    const n = $("#note"); if (!n) return;
    n.value = (n.value ? n.value + "\n" : "") + "From side chat: " + thread[+b.dataset.i].text;
    touched = true; toast("Added to your answer's note.");
  });
  $("#msgs").scrollTop = $("#msgs").scrollHeight;
  $("#sugs").innerHTML = suggestions(chatCtx).map(q => `<button class="sug" type="button">${esc(q)}</button>`).join("");
  $("#sugs").querySelectorAll(".sug").forEach(b => b.onclick = () => ask(b.textContent));
  $("#saved-to").textContent = thread.length ? `Saved to chats/${ctxKey(chatCtx)}.md. The orchestrator reads it with your answer.` : "";
}
async function openChat(c){
  chatReturn = document.activeElement; chatCtx = c; thread = [];
  $("#ctx").textContent = ctxLabel(c);
  const h = S.helper || {};
  $("#chat-note").textContent = h.available
    ? `A read-only helper explains using the run's files. It can't change the run; your decision still goes through the card. Answers by ${h.label}, one model call per question.`
    : `${h.label || "No helper"}. Restart the dashboard with --helper "<agent cli>" to turn the side chat on.`;
  $("#q").disabled = $("#q-send").disabled = !h.available;
  $("#q").value = ""; $("#q-err").textContent = "";
  renderThread();
  $("#chat").classList.add("open"); $("#q").focus();
  try { const d = await api("/api/chat?key=" + encodeURIComponent(ctxKey(c))); if (chatCtx === c){ thread = d.thread; renderThread(); } } catch (e) { /* empty thread is fine */ }
}
function closeChat(){ $("#chat").classList.remove("open"); if (chatReturn) chatReturn.focus(); }
async function ask(q){
  q = (q || "").trim();
  if (!q){ $("#q-err").textContent = "Type a question first."; return; }
  if (busy){ $("#q-err").textContent = "Wait for the current answer first."; return; }
  if (!(S.helper || {}).available){ $("#q-err").textContent = "The side chat is off for this dashboard."; return; }
  const c = chatCtx;
  thread.push({who:"me", text:q}); busy = true; renderThread();
  try {
    const body = c.card ? {card: c.card.id, option: c.opt || "", question: q} : {milestone: c.ms.id, question: q};
    const r = await api("/api/chat", body);
    if (chatCtx === c){ thread.push({who:"ai", text:r.answer, src:r.src}); }
  } catch (e) {
    thread.pop();
    if (chatCtx === c){ $("#q-err").textContent = e.message; $("#q").value = q; }
  } finally { busy = false; if (chatCtx === c) renderThread(); }
}
$("#chat-form").onsubmit = e => { e.preventDefault(); const v = $("#q").value; $("#q").value = ""; ask(v); };
$("#q").oninput = () => $("#q-err").textContent = "";
$("#chat-close").onclick = closeChat;

// ---------- misc ----------
let tt;
function toast(t){ const el = $("#toast"); el.textContent = t; el.classList.add("show"); clearTimeout(tt); tt = setTimeout(() => el.classList.remove("show"), 3200); }

document.addEventListener("keydown", e => {
  if (e.key === "Escape"){
    if ($("#chat").classList.contains("open")) return closeChat();
    if ($("#viewer").classList.contains("open")) return closeViewer();
    if ($("#drawer").classList.contains("open")) return closeDrawer();
  }
  if (["TEXTAREA","INPUT"].includes(document.activeElement.tagName) || e.metaKey || e.ctrlKey || e.altKey) return;
  const c = S && S.cards.find(x => x.id === shownId);
  if (!c || !$("#send") || $("#send").disabled) return;
  const i = parseInt(e.key, 10);
  if (i >= 1 && i <= c.options.length) choose(c.options[i-1].k);
});

const themes = ["system","light","dark"]; let ti = 0;
try { const saved = localStorage.getItem("runboard-theme"); if (saved) ti = Math.max(0, themes.indexOf(saved)); } catch (e) {}
function applyTheme(){
  const t = themes[ti];
  if (t === "system") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", t);
  $("#theme").textContent = "Theme: " + t;
  try { localStorage.setItem("runboard-theme", t); } catch (e) {}
}
$("#theme").onclick = () => { ti = (ti + 1) % 3; applyTheme(); };
applyTheme();

if (!TOKEN){
  lastError = "This page needs the link the dashboard printed when it started (it ends with #t=…).";
  banner();
} else {
  poll();
}
