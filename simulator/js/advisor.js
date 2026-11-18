/* CDU LIVE - AI shift advisor.
 *
 * Claude reads the live plant, tests candidate moves on the process model (what_if) and offers them to the
 * operator as an Apply card (propose_moves). It never moves a setpoint itself. Runs through the artifact's
 * `sample` capability on the viewer's own Claude account; elsewhere (a local file) the panel says so.
 */
(function () {
  "use strict";
  const sim = window.sim, apc = window.apc, App = window.App;
  const { LIMITS, CRUDES } = window.CDU;
  const CTL = App.CTL;
  const $ = (s, r) => (r || document).querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const r1 = (x) => (isFinite(x) ? Math.round(x * 10) / 10 : null);
  const r2 = (x) => (isFinite(x) ? Math.round(x * 100) / 100 : null);
  const KEYS = Object.keys(CTL);

  const box = $("#advisor"), body = $("#panelBody");
  const tH = $("#ptHandles"), tA = $("#ptAdvisor");
  let sample = null, canTools = false, ready = false, why = "starting";
  let busy = null, turns = [], proposalSeq = 0;

  // ------------------------------------------------------------------ the plant as Claude sees it
  function plantState() {
    const s = sim, o = s.out, a = s.act, q = s.q, sl = o.sl;
    const sp = {}; for (const k of KEYS) sp[k] = r2(s.sp[k]);
    const off = Object.entries(o.econ.value).filter(([, v]) => v.off).map(([k, v]) => `${k} → ${v.dest}`);
    return {
      plant_time: App.hhmm(s.t),
      crude: { tank1: CRUDES[s.sp.crudeA].name, tank2: CRUDES[s.sp.crudeB].name, tank2_share_at_unit_pct: r1(s.blendAct), api: r1(sl.api), sulfur_wt: r2(sl.sulfur), salt_ptb: r1(o.saltIn), ni_v_ppm: Math.round(sl.metals), price_usd_bbl: r1(sl.price) },
      status: { charge_pumps: s.ev.p101A || s.ev.p101B ? `running (${[s.ev.p101A && "P-101A", s.ev.p101B && "P-101B"].filter(Boolean).join(", ")})` : "NONE RUNNING", h101: s.ev.h1trip ? "TRIPPED" : "firing", h201: s.ev.h2trip ? "TRIPPED" : "firing", esd_active: s.ev.esd, apc: apc.on ? `on, benefit ${Math.round((o.econ.margin - apc.base) / 1000)} k$/d` : "off", mission: App.mission() },
      setpoints: sp,
      measured: {
        charge_kbpsd: r1(a.feed), cit_C: r1(a.CIT), h101_cot_C: r1(a.COT1), h101_fired_MW: r1(a.fired1), h101_fired_max_MW: r1(o.firedMax1), h101_tube_metal_C: Math.round(o.TMT1), h101_efficiency_pct: r1(o.eff1 * 100), flue_co_ppm: Math.round(o.co),
        flash_zone_C: r1(o.Tfz), vaporised_pct_crude: r1(o.vapLV * 100), overflash_pct: r1(o.overflash), top_C: r1(o.Ttop), water_dew_point_C: r1(o.Tdew), condenser_MW: r1(o.Qcond), condenser_needed_MW: r1(o.QcondReq), condenser_max_MW: r1(o.QcondMax),
        tray_flood_pct: { top: Math.round(o.flood.top), mpa: Math.round(o.flood.mpa), bpa: Math.round(o.flood.bpa), flash_zone: Math.round(o.flood.fz) },
        cut_points_tbp_C: { hn_kero: Math.round(a.cuts.c1), kero_diesel: Math.round(a.cuts.c2), diesel_ago: Math.round(a.cuts.c3), ago_residue: Math.round(a.cuts.c4), hvgo_vr: Math.round(a.cutsV.cHvgo) },
        desalter: { inlet_C: r1(o.Tdes), salt_out_ptb: r2(s.lag.saltOut), efficiency_pct: r1(o.desaltEff * 100), bsw_vol_pct: r2(o.bsw), emulsion_index: r2(o.emulsion) },
        overhead: { corrosion_mpy: r1(s.lag.corr), sour_water_ph: r1(o.ohpH) },
        vacuum: { top_mbar: r1(a.Ptop2), flash_zone_mbar: Math.round(o.Pfz2), ejector_load_pct: Math.round(o.ejLoad * 100), ejector_broken: o.ejBroken, cracked_gas_kg_h: Math.round(o.crackGas), h201_cot_C: r1(a.COT2), h201_fired_MW: r1(a.fired2), h201_fired_max_MW: r1(o.firedMax2) },
      },
      analysers_15min_lag: {
        hn_end_point_C: [r1(q.hnEP), "≤ 190"], kero_flash_C: [r1(q.keroFlash), "≥ 38"], kero_freeze_C: [r1(q.keroFreeze), "≤ -47"],
        diesel_d86_95_C: [r1(q.dieselT95), "≤ 360"], diesel_cloud_C: [r1(q.dieselCloud), "≤ 0"], diesel_flash_C: [r1(q.dieselFlash), "≥ 55"],
        ago_colour: [r1(q.agoColor), "≤ 4"], hvgo_ni_v_ppm: [r2(q.hvgoMetals), "≤ 2.0"], hvgo_carbon_wt: [r2(q.hvgoCCR), "≤ 1.0"],
      },
      yields_pct_crude: Object.fromEntries(Object.entries(s.lag.yields).map(([k, v]) => [k, r1(v * 100)])),
      economics_usd_day: { margin: Math.round(o.econ.margin), per_bbl: r2(o.econ.perBbl), revenue: Math.round(o.econ.revenue), crude: Math.round(o.econ.crude), fuel: Math.round(o.econ.fuel), steam: Math.round(o.econ.steam), off_spec_downgrades: off },
      active_alarms: App.activeAlarms(),
    };
  }

  const HANDLES = KEYS.map((k) => `${k}: ${CTL[k][0]} (${CTL[k][1]}), ${LIMITS[k][0]}–${LIMITS[k][1]} ${LIMITS[k][3]}, design ${window.CDU.DES[k]}`).join("\n");
  const RULES = `You are the shift advisor inside CDU LIVE, a training simulator of a 100,000 BPSD crude and vacuum distillation unit (FEED design on Arab Light: H-101 charge heater, C-101 41-tray atmospheric column with three pumparounds and three side strippers, two-stage desalter, H-201 vacuum heater, C-201 packed vacuum column with three-stage steam ejectors). The person asking is an operator or engineer at a demonstration.

How to answer:
- Lead with the answer. Plain words, at most about 170 words unless they ask for a shift handover or a longer explanation.
- Use this plant's numbers and tags. Explain cause and effect in one or two links ("lower overflash → wash zone dries → residue carries into the AGO").
- When you recommend setpoint changes: ${"{TOOLS}"}
- Recommend few moves, inside the handle ranges, sized like an operator would make them (a few tenths of a percent on draws, a few °C on temperatures).
- If a heater is tripped, a pump is down or the ESD is active, give the immediate safe actions first.
- Light markdown only: short paragraphs, "- " bullets, **bold** for key numbers. No tables, no headings.
- It is a simulator with illustrative prices. Never present its numbers as real plant data. If APC is on, say that APC will keep moving the handles it controls.

Operator handles (key: name (tag), range, design):
${HANDLES}

Specs on the analysers: heavy naphtha end point ≤ 190 °C; kero flash ≥ 38 °C and freeze ≤ -47 °C; diesel D86 95 % ≤ 360 °C, cloud ≤ 0 °C, flash ≥ 55 °C; AGO colour ≤ 4; HVGO Ni+V ≤ 2.0 ppm and carbon ≤ 1.0 wt%. Off-spec streams are downgraded (kero → diesel pool, diesel → AGO price, HVGO → coker feed). Equipment limits: tray flood 100 %, H-101 tube metal 545 °C, H-201 above ~405 °C cracks and loads the ejectors, top temperature at least 14 °C above the water dew point, overflash at least 1 %.`;
  const RULES_TOOLS = "first test them with what_if (try a couple of alternatives if useful), then call propose_moves once with the final set so the operator gets an Apply button. Never say a move has been applied: the operator decides.";
  const RULES_NOTOOLS = "list them as `handle → value` lines. The operator applies them by hand.";

  // ------------------------------------------------------------------ tools
  function cleanChanges(ch) {
    const out = {};
    if (!ch || typeof ch !== "object") return out;
    for (const [k, v] of Object.entries(ch)) {
      if (!LIMITS[k] || k === "blend") continue;
      const n = Number(v); if (!isFinite(n)) continue;
      out[k] = Math.max(LIMITS[k][0], Math.min(LIMITS[k][1], n));
    }
    return out;
  }
  function summarise(p) {
    const q = p.q, o = p.o;
    const cons = window.APCmod.status(p).filter((c) => c.viol || c.room < 0).map((c) => ({ name: c.name, value: r2(c.v), limit: `${c.kind === "max" ? "≤" : "≥"} ${c.hard} ${c.u}` }))
      .concat(window.APCmod.status(p).filter((c) => !c.viol && c.active).map((c) => ({ name: c.name, value: r2(c.v), near_limit: `${c.kind === "max" ? "≤" : "≥"} ${c.hard} ${c.u}` })));
    return {
      margin_usd_day: Math.round(p.margin),
      specs: { hn_end_point: r1(q.hnEP), kero_flash: r1(q.keroFlash), kero_freeze: r1(q.keroFreeze), diesel_d86_95: r1(q.dieselT95), diesel_cloud: r1(q.dieselCloud), diesel_flash: r1(q.dieselFlash), ago_colour: r1(q.agoColor), hvgo_ni_v: r2(q.hvgoMetals), hvgo_carbon: r2(q.hvgoCCR), all_on_spec: Object.values(o.spec).every(Boolean) },
      yields_pct: Object.fromEntries(Object.entries(o.P).map(([k, v]) => [k, r1(v.lv * 100)])),
      unit: { h101_cot: r1(p.COT1), h101_fired_pct_max: Math.round(p.fired1 / o.firedMax1 * 100), tube_metal: Math.round(p.TMT1), max_tray_flood: Math.round(o.floodMax), overflash: r1(o.overflash), vac_top_mbar: r1(o.Ptop2), h201_cot: r1(p.COT2), overhead_corrosion_mpy: r1(o.corr) },
      constraints_over_or_near: cons.slice(0, 8),
    };
  }
  const TOOLS = [
    { name: "get_plant_state", description: "Returns the live plant: setpoints, measurements, analyser qualities with specs, yields, economics and active alarms. The same data as in the question, refreshed now.",
      execute: () => plantState() },
    { name: "what_if", description: "Tests setpoint changes on the steady-state process model without touching the plant. Returns predicted margin (USD/day) and its change, product qualities, yields and any constraint over or near its limit. Use it before recommending moves.",
      inputSchema: { type: "object", properties: { changes: { type: "object", description: "Handle key → new setpoint, e.g. {\"diesel\": 16.5, \"ago\": 6.4}", additionalProperties: { type: "number" } } }, required: ["changes"] },
      execute: (input) => {
        const ch = cleanChanges(input && input.changes);
        if (!Object.keys(ch).length) throw new Error("No valid handle keys. Use keys from the handle list.");
        status("Testing on the model: " + Object.entries(ch).map(([k, v]) => `${CTL[k][0]} ${r2(sim.sp[k])} → ${r2(v)}`).join(", "));
        const base = sim.predict(), p = sim.predict(ch);
        const r = summarise(p);
        r.margin_change_usd_day = Math.round(p.margin - base.margin);
        r.changes_tested = ch;
        r.note = "Steady state once the column settles, about 1-2 plant hours.";
        return r;
      } },
    { name: "propose_moves", description: "Shows the operator a card with these setpoint moves and an Apply button. Call it once, with the final recommended set. Returns when the card is shown; it does not apply anything.",
      inputSchema: { type: "object", properties: { moves: { type: "object", additionalProperties: { type: "number" }, description: "Handle key → new setpoint" }, reason: { type: "string", description: "One sentence: what the moves achieve" } }, required: ["moves", "reason"] },
      execute: (input) => {
        const mv = cleanChanges(input && input.moves);
        if (!Object.keys(mv).length) throw new Error("No valid moves.");
        const base = sim.predict(), p = sim.predict(mv);
        pendingProposal = { id: ++proposalSeq, moves: mv, reason: String((input && input.reason) || ""), gain: p.margin - base.margin, onspec: Object.values(p.o.spec).every(Boolean) };
        return "Shown to the operator with an Apply button.";
      } },
  ];
  let pendingProposal = null;

  // ------------------------------------------------------------------ rendering
  function md(t) {
    const lines = esc(t).split(/\n/);
    let html = "", list = false, para = [];
    const inline = (x) => x.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");
    const flush = () => { if (para.length) { html += `<p>${inline(para.join(" "))}</p>`; para = []; } };
    for (const l of lines) {
      const m = l.match(/^\s*(?:[-*•]|\d+\.)\s+(.*)$/);
      if (m) { flush(); if (!list) { html += "<ul>"; list = true; } html += `<li>${inline(m[1])}</li>`; continue; }
      if (list) { html += "</ul>"; list = false; }
      if (!l.trim()) flush(); else para.push(l.replace(/^#+\s*/, ""));
    }
    flush(); if (list) html += "</ul>";
    return html;
  }
  function render() {
    if (!ready) {
      box.innerHTML = `<div class="adv-empty"><h3>Shift advisor</h3><p>${why === "starting" ? "Connecting to Claude…" : esc(why)}</p></div>`;
      return;
    }
    if (box.dataset.built) return;
    box.dataset.built = "1";
    box.innerHTML = `<div class="adv-log" id="advLog" aria-live="polite"><div class="adv-msg a"><p>I can see the whole unit live. Ask why something is happening, what limits margin, or what to change. I test every suggestion on the process model before I offer it, and nothing moves until you press <b>Apply</b>.</p></div></div>
      <div class="adv-chips">${["What's limiting margin right now?", "Find $50k a day without breaking a spec", "Explain the alarms that are on", "Write my shift handover", "Why does overflash matter here?"].map((c) => `<button class="chip" type="button">${esc(c)}</button>`).join("")}</div>
      <form class="adv-form" id="advForm"><textarea id="advQ" rows="2" placeholder="Ask about the plant…" aria-label="Question for the shift advisor"></textarea><div class="adv-btns"><button class="btn primary" type="submit" id="advSend">Ask</button><button class="btn" type="button" id="advStop" hidden>Stop</button></div></form>`;
    box.querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => ask(b.textContent)));
    $("#advForm").addEventListener("submit", (e) => { e.preventDefault(); const v = $("#advQ").value.trim(); if (v) ask(v); });
    $("#advQ").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#advForm").requestSubmit(); } });
    $("#advStop").addEventListener("click", () => busy && busy.abort());
    box.addEventListener("click", onCard);
  }
  function addMsg(cls, html) { const log = $("#advLog"); const d = document.createElement("div"); d.className = "adv-msg " + cls; d.innerHTML = html; log.appendChild(d); log.scrollTop = log.scrollHeight; return d; }
  let statusEl = null;
  function status(t) { if (statusEl) { statusEl.textContent = t; const log = $("#advLog"); log.scrollTop = log.scrollHeight; } }
  function card(pr) {
    const rows = Object.entries(pr.moves).map(([k, v]) => `<li><span>${esc(CTL[k][0])} <span class="mono" style="color:var(--mute)">${esc(CTL[k][1])}</span></span><b class="mono">${r2(sim.sp[k])} → ${r2(v)} ${esc(LIMITS[k][3])}</b></li>`).join("");
    return `<div class="adv-card" data-p="${pr.id}"><div class="k">Proposed moves</div><p>${esc(pr.reason)}</p><ul>${rows}</ul>
      <p class="mono" style="color:${pr.gain >= 0 ? "var(--ok)" : "var(--alarm)"}">Model: ${pr.gain >= 0 ? "+" : "−"}$${Math.round(Math.abs(pr.gain) / 1000)}k/day · ${pr.onspec ? "all products on spec" : "a spec is predicted off"}</p>
      <div class="adv-btns"><button class="btn primary" data-apply>Apply</button><button class="btn" data-dismiss>Dismiss</button></div></div>`;
  }
  const proposals = {};
  function onCard(e) {
    const c = e.target.closest(".adv-card"); if (!c) return;
    const pr = proposals[c.dataset.p]; if (!pr) return;
    if (e.target.closest("[data-apply]")) {
      for (const [k, v] of Object.entries(pr.moves)) sim.sp[k] = v;
      sim.log("info", "Advisor moves applied by operator: " + Object.entries(pr.moves).map(([k, v]) => `${CTL[k][1]} → ${r2(v)}`).join(", "));
      c.querySelector(".adv-btns").innerHTML = `<span class="pill ok">APPLIED</span>${apc.on ? `<span style="font-size:12px;color:var(--mute)">APC is on and will keep moving the handles it controls.</span>` : ""}`;
      App.toast("Moves applied. The plant will take a while to settle; watch the trends.");
    }
    if (e.target.closest("[data-dismiss]")) c.querySelector(".adv-btns").innerHTML = `<span class="pill warn">DISMISSED</span>`;
  }

  const ERR = {
    not_granted: "Claude was not allowed for this page. The rest of the simulator works as before.",
    sampling_disabled: "Claude is not available for this account.", rate_limited: "Claude is busy for you right now. Try again in a minute.",
    session_expired: "Sign in to Claude again, then ask.", refused: "Claude declined that question. Try asking it another way.",
    empty_completion: "No answer came back. Try a simpler question.", prompt_too_large: "The conversation got too long. Reload the advisor to start fresh.",
  };

  // ------------------------------------------------------------------ ask
  async function ask(q) {
    open();
    if (!ready) return;
    if (busy) busy.abort();
    const ta = $("#advQ"); if (ta) ta.value = "";
    addMsg("u", `<p>${esc(q)}</p>`);
    const out = addMsg("a", `<p class="adv-think">Thinking…</p>`);
    statusEl = document.createElement("div"); statusEl.className = "adv-status"; out.before(statusEl); statusEl.textContent = "Reading the plant…";
    const ctl = new AbortController(); busy = ctl;
    $("#advSend").disabled = true; $("#advStop").hidden = false;
    const msg = `Plant state at ${App.hhmm(sim.t)}:\n${JSON.stringify(plantState())}\n\nOperator: ${q}`;
    const rules = RULES.replace("{TOOLS}", canTools ? RULES_TOOLS : RULES_NOTOOLS);
    const input = [{ role: "user", content: rules }, ...turns.slice(-6), { role: "user", content: msg }];
    pendingProposal = null;
    try {
      const opts = { signal: ctl.signal, onText: ({ text }) => { out.innerHTML = md(text); const log = $("#advLog"); log.scrollTop = log.scrollHeight; } };
      if (canTools) opts.tools = TOOLS; else opts.cache = false;
      const { text, truncated } = await sample(input, opts);
      out.innerHTML = md(text) + (truncated ? `<p class="adv-note">The answer was cut short.</p>` : "");
      turns.push({ role: "user", content: `Operator (at ${App.hhmm(sim.t)}): ${q}` }, { role: "assistant", content: text });
    } catch (e) {
      const keep = e && e.text && e.code !== "refused" ? md(e.text) : "";
      out.innerHTML = keep + (e && e.code === "cancelled" ? `<p class="adv-note">Stopped.</p>` : `<p class="adv-note">${esc(ERR[e && e.code] || "The advisor could not answer. Try again.")}</p>`);
      if (e && (e.code === "not_granted" || e.code === "sampling_disabled")) { ready = false; why = ERR[e.code]; }
    } finally {
      if (statusEl) statusEl.remove(); statusEl = null;
      if (pendingProposal) { proposals[pendingProposal.id] = pendingProposal; addMsg("a card-wrap", card(pendingProposal)); pendingProposal = null; }
      if (busy === ctl) busy = null;
      $("#advSend").disabled = false; $("#advStop").hidden = true;
      if (!ready) { delete box.dataset.built; render(); }
    }
  }

  // ------------------------------------------------------------------ panel tabs
  function open() {
    tA.setAttribute("aria-selected", "true"); tH.setAttribute("aria-selected", "false");
    body.hidden = true; box.hidden = false;
    $("#panelTitle").textContent = "Shift advisor"; $("#panelSub").textContent = "Claude, reading the live plant and testing moves on the model";
    render();
    if (window.innerWidth < 1100) box.scrollIntoView({ block: "start", behavior: "smooth" });
  }
  function close() {
    if (box.hidden) return;
    tA.setAttribute("aria-selected", "false"); tH.setAttribute("aria-selected", "true");
    box.hidden = true; body.hidden = false;
    App.renderPanel();
  }
  tA.addEventListener("click", open);
  tH.addEventListener("click", close);
  const top = $("#advBtn"); if (top) top.addEventListener("click", open);

  // ------------------------------------------------------------------ connect
  (async () => {
    if (!window.claude || typeof window.claude.use !== "function") { why = "The advisor runs on Claude when this page is opened at claude.ai. Everything else in the simulator works without it."; render(); return; }
    try { sample = await window.claude.use("sample"); } catch (e) { sample = null; }
    if (!sample) { why = "Claude is not available in this view. Everything else in the simulator works without it."; render(); return; }
    try { const l = await sample.limits(); canTools = !!(l && l.tools); } catch (e) { canTools = false; }
    ready = true; render();
  })();

  window.Advisor = { open, close, ask: (q) => { open(); if (ready) ask(q); }, available: () => ready };
})();
