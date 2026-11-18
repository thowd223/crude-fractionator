/* CDU LIVE - application: sim loop, operator panel, alarms, trends, missions, tour, learn, sound. */
(function () {
  "use strict";
  const { Sim, CRUDES, PRODUCTS, PRICES, LIMITS } = window.CDU;
  const { EQUIP, CONCEPTS, TOUR, MISSIONS, ALARMS } = window.CONTENT;
  const D = window.PLANT.design;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const f0 = (x) => (isFinite(x) ? Math.round(x).toLocaleString("en-US") : "–");
  const f1 = (x) => (isFinite(x) ? x.toFixed(1) : "–");
  const f2 = (x) => (isFinite(x) ? x.toFixed(2) : "–");
  const money = (x) => (x < 0 ? "−$" : "$") + f0(Math.abs(x));
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const sim = new Sim();
  window.sim = sim;
  let speed = 30, paused = false;

  // ================================================================ operator panel
  const CTL = {
    feed: ["Crude charge", "FIC-1001", (s) => `${f1(s.act.feed)} kBPSD`],
    blend: ["Tank 2 share of blend", "FFIC-1000", (s) => `${f1(s.blendAct)} % at unit`],
    cot1: ["Coil outlet temperature", "TIC-1020", (s) => `${f1(s.act.COT1)} °C`],
    o2: ["Flue gas excess O₂", "AIC-1022", (s) => `CO ${f0(s.out.co)} ppm`],
    ttop: ["Column top temperature", "TIC-1030", (s) => `${f1(s.out.Ttop)} °C`],
    kero: ["Kerosene draw", "FIC-1050", (s) => `${f1(s.lag.yields.KERO * 100)} % · cut ${f0(s.act.cuts.c2)} °C`],
    diesel: ["Diesel draw", "FIC-1060", (s) => `${f1(s.lag.yields.DIESEL * 100)} % · cut ${f0(s.act.cuts.c3)} °C`],
    ago: ["AGO draw", "FIC-1070", (s) => `${f1(s.lag.yields.AGO * 100)} % · cut ${f0(s.act.cuts.c4)} °C`],
    sBot: ["Bottom stripping steam", "FIC-1081", (s) => `overflash ${f1(s.out.overflash)} %`],
    tpa: ["Top pumparound duty", "TIC-1041", (s) => `desalter ${f1(s.out.Tdes)} °C`],
    mpa: ["Mid pumparound duty", "TIC-1043", (s) => `CIT ${f1(s.act.CIT)} °C`],
    bpa: ["Bottom pumparound duty", "TIC-1045", (s) => `condenser ${f1(s.out.Qcond)} MW`],
    sKero: ["Kero stripper steam", "FIC-1054", (s) => `flash ${f1(s.q.keroFlash)} °C`],
    sDiesel: ["Diesel stripper steam", "FIC-1064", (s) => `flash ${f1(s.q.dieselFlash)} °C`],
    ww: ["Wash water", "FFIC-1003", (s) => `salt ${f2(s.lag.saltOut)} PTB`],
    mixdp: ["Mix valve ΔP", "PDIC-1005", (s) => `BS&W ${f2(s.out.bsw)} %`],
    demul: ["Demulsifier", "FFIC-1002", (s) => `emulsion ${f2(s.out.emulsion)}`],
    neut: ["Overhead neutraliser", "FFIC-1036", (s) => `pH ${f1(s.out.ohpH)}`],
    cot2: ["Vacuum heater outlet", "TIC-2005", (s) => `${f1(s.act.COT2)} °C`],
    motive: ["Ejector motive steam", "PI-2050", (s) => `top ${f1(s.act.Ptop2)} mbar`],
  };
  const GROUPS = [
    { id: "crude", t: "Crude & throughput", keys: ["feed", "blend"], extra: "crude" },
    { id: "heater", t: "H-101 charge heater", keys: ["cot1", "o2"], extra: "heater" },
    { id: "column", t: "C-101 cut points", keys: ["ttop", "kero", "diesel", "ago", "sBot"] },
    { id: "pa", t: "Pumparounds", keys: ["tpa", "mpa", "bpa"] },
    { id: "strip", t: "Side strippers", keys: ["sKero", "sDiesel"] },
    { id: "desalt", t: "Desalter & overhead", keys: ["ww", "mixdp", "demul", "neut"] },
    { id: "vac", t: "Vacuum unit", keys: ["cot2", "motive"], extra: "vac" },
    { id: "econ", t: "Economics", keys: [], extra: "econ" },
    { id: "safety", t: "Emergency", keys: [], extra: "safety" },
  ];
  const bound = []; // {key, range, num, pv}
  function ctlHTML(k) {
    const [lab, tag] = CTL[k], [mn, mx, st, unit] = LIMITS[k];
    return `<div class="ctl" data-k="${k}"><label for="r_${k}">${lab}<span class="tag">${tag}</span></label><span class="pv" data-pv></span>
      <div class="row"><input type="range" id="r_${k}" min="${mn}" max="${mx}" step="${st}"><input type="number" id="n_${k}" min="${mn}" max="${mx}" step="${st}" aria-label="${lab} setpoint (${unit})"></div>
      <span class="hint">${unit} · design ${window.CDU.DES[k]}</span></div>`;
  }
  function extraHTML(x) {
    if (x === "crude") return `<div class="ctl"><label for="selA">Tank 1</label><span></span><div class="row" style="grid-template-columns:1fr"><select class="sel" id="selA">${Object.entries(CRUDES).map(([k, c]) => `<option value="${k}">${c.name} · ${c.api}°API · $${c.price}</option>`).join("")}</select></div></div>
      <div class="ctl"><label for="selB">Tank 2</label><span></span><div class="row" style="grid-template-columns:1fr"><select class="sel" id="selB">${Object.entries(CRUDES).map(([k, c]) => `<option value="${k}">${c.name} · ${c.api}°API · $${c.price}</option>`).join("")}</select></div></div>
      <div class="rd" data-rd="pumps"></div><div class="btnrow"><button class="btn small" data-act="p101A">P-101A</button><button class="btn small" data-act="p101B">P-101B</button></div>`;
    if (x === "heater") return `<div class="rd" data-rd="heater"></div><div class="btnrow"><button class="btn small" data-act="reset1">Reset SIS &amp; relight H-101</button></div>`;
    if (x === "vac") return `<div class="rd" data-rd="vac"></div><div class="btnrow"><button class="btn small" data-act="motive">Line up HP motive steam bypass</button><button class="btn small" data-act="reset2">Reset SIS &amp; relight H-201</button></div>`;
    if (x === "econ") return `<div class="rd" data-rd="econ"></div><div style="padding:0 16px 12px;display:grid;grid-template-columns:1fr 1fr;gap:6px 10px">${PRODUCTS.map((p) => `<label style="font-size:12px;color:var(--ink-2);display:flex;justify-content:space-between;gap:6px;align-items:center">${p.name}<input type="number" class="price" data-p="${p.key}" value="${p.price}" step="0.5" style="width:62px;background:var(--bg);border:1px solid var(--line-2);border-radius:5px;padding:2px 5px;font:500 12px var(--f-data);text-align:right"></label>`).join("")}
      <label style="font-size:12px;color:var(--ink-2);display:flex;justify-content:space-between;gap:6px;align-items:center">Fuel $/MMBtu<input type="number" class="price" data-p="fuel" value="${PRICES.fuel_usd_mmbtu}" step="0.1" style="width:62px;background:var(--bg);border:1px solid var(--line-2);border-radius:5px;padding:2px 5px;font:500 12px var(--f-data);text-align:right"></label></div>`;
    if (x === "safety") return `<div class="rd"><span>Unit emergency shutdown (SIF-901, SIL 2) closes every trip valve and trips both heaters.</span><span></span></div><div class="btnrow"><button class="btn danger" data-act="esd">ESD-1 · HS-9000</button><button class="btn small" data-act="esdreset">Reset ESD</button><button class="btn small" data-act="resetall">Restore design point</button></div>`;
    return "";
  }
  function groupHTML(g, open) {
    return `<details class="grp" data-g="${g.id}" ${open ? "open" : ""}><summary>${g.t}<span class="st" data-st></span></summary>${g.keys.map(ctlHTML).join("")}${g.extra ? extraHTML(g.extra) : ""}</details>`;
  }
  function renderPanel(eqId) {
    const body = $("#panelBody");
    bound.length = 0;
    if (!eqId) {
      $("#panelTitle").textContent = "Operator handles";
      $("#panelSub").textContent = "Setpoints go to the DCS. The plant answers with real lags: heaters in minutes, the column in tens of minutes.";
      body.innerHTML = GROUPS.map((g, i) => groupHTML(g, i < 3)).join("");
    } else {
      const e = EQUIP[eqId];
      $("#panelTitle").textContent = e.name;
      $("#panelSub").textContent = e.tag;
      const ds = datasheetFor(eqId);
      body.innerHTML = `<div class="eq-card"><button class="btn small" data-act="back">← All handles</button>
        <h4>What it does</h4><p>${e.what}</p><h4>What to watch</h4><p>${e.watch}</p>
        <div class="rd" data-rd="eq-${eqId}" style="padding:4px 0 6px"></div>
        ${ds ? `<h4>Datasheet · ${esc(ds.tag)}</h4><dl>${Object.entries(ds.d).filter(([, v]) => v !== null && v !== "").map(([k, v]) => `<dt>${DSLAB[k] || k}</dt><dd>${esc(typeof v === "number" ? (Math.abs(v) > 100 ? f0(v) : f1(v)) : v)}</dd>`).join("")}</dl>` : ""}</div>
        ${GROUPS.filter((g) => e.groups.includes(g.id)).map((g) => groupHTML(g, true)).join("")}`;
    }
    for (const k of Object.keys(CTL)) {
      const r = $("#r_" + k, body); if (!r) continue;
      const n = $("#n_" + k, body), pv = r.closest(".ctl").querySelector("[data-pv]");
      const set = (v, from) => {
        const [mn, mx] = LIMITS[k]; v = Math.max(mn, Math.min(mx, +v)); if (!isFinite(v)) return;
        sim.sp[k] = v; if (from !== r) r.value = v; if (from !== n) n.value = v;
        r.style.setProperty("--p", ((v - mn) / (mx - mn) * 100).toFixed(1) + "%");
        if (k === "blend") sim.slateKey = "";
      };
      r.addEventListener("input", () => set(r.value, r));
      n.addEventListener("change", () => set(n.value, n));
      set(sim.sp[k]);
      bound.push({ k, r, n, pv, set });
    }
    const sa = $("#selA", body), sb = $("#selB", body);
    if (sa) { sa.value = sim.sp.crudeA; sb.value = sim.sp.crudeB; sa.onchange = () => { sim.sp.crudeA = sa.value; sim.slateKey = ""; }; sb.onchange = () => { sim.sp.crudeB = sb.value; sim.slateKey = ""; }; }
    $$(".price", body).forEach((inp) => inp.addEventListener("change", () => { const v = +inp.value; if (!isFinite(v)) return; if (inp.dataset.p === "fuel") PRICES.fuel_usd_mmbtu = v; else PRODUCTS.find((p) => p.key === inp.dataset.p).price = v; }));
    updatePanel(true);
  }
  const DSLAB = { size: "Size", op_T: "Operating °C", op_P: "Operating barg", des_T: "Design °C", des_P: "Design barg", moc: "Material", duty_kw: "Duty kW", motor_kw: "Motor kW", flow_m3h: "Flow m³/h", head_m: "Head m" };
  const EQTAG = { tanks: "P-101A", preheat: "E-108A", hottrain: "E-108A", desalter: "D-101A", h101: "H-101", c101: "C-101", pa: "C-101", strippers: "C-103", overhead: "D-102", lightends: "C-105", h201: "H-201", c201: "C-201", ejectors: "J-201", products: "A-104" };
  function datasheetFor(id) { const t = EQTAG[id]; const m = t && window.PLANT.layout[t]; return m && m.datasheet ? { tag: t, d: m.datasheet } : null; }

  function rd(rows) { return rows.map(([l, v, c]) => `<span>${l}</span><b class="${c || ""}">${v}</b>`).join(""); }
  function readouts(key) {
    const s = sim, o = s.out, a = s.act, q = s.q;
    switch (key) {
      case "pumps": return rd([["P-101A", s.ev.p101A ? "running" : "stopped", s.ev.p101A ? "good" : "bad"], ["P-101B (spare)", s.ev.p101B ? "running" : "standby", s.ev.p101B ? "good" : ""], ["Blend at unit", `${f1(o.sl.api)} °API · ${f2(o.sl.sulfur)} % S`], ["Crude cost", `$${f1(o.sl.price)}/bbl`]]);
      case "heater": return rd([["Fired / max", `${f1(a.fired1)} / ${f1(o.firedMax1)} MW`, o.limited1 ? "bad" : ""], ["Efficiency", `${f1(o.eff1 * 100)} %`], ["Tube metal (peak)", `${f0(o.TMT1)} °C`, o.TMT1 > 545 ? "bad" : o.TMT1 > 520 ? "warn" : ""], ["Coke layer", `${f2(o.coke1)} mm`], ["Fuel gas", `${f1(o.fuelKgh / 1000)} t/h`], ["Status", s.ev.h1trip ? "TRIPPED" : "firing", s.ev.h1trip ? "bad" : "good"]]);
      case "vac": return rd([["Top / flash zone", `${f1(a.Ptop2)} / ${f0(o.Pfz2)} mbar`, a.Ptop2 > 30 ? "bad" : ""], ["Ejector load", o.ejBroken ? "BROKEN" : `${f0(o.ejLoad * 100)} %`, o.ejBroken ? "bad" : ""], ["Cracked gas", `${f0(o.crackGas)} kg/h`], ["HVGO cut (TBP)", `${f0(a.cutsV.cHvgo)} °C`], ["H-201 fired / max", `${f1(a.fired2)} / ${f1(o.firedMax2)} MW`, o.limited2 ? "bad" : ""], ["HVGO Ni+V / CCR", `${f2(q.hvgoMetals)} ppm / ${f2(q.hvgoCCR)} %`, s.out.specLag.HVGO ? "" : "bad"]]);
      case "econ": { const e = o.econ; return rd([["Product revenue", money(e.revenue) + "/d"], ["Crude", money(-e.crude) + "/d"], ["Fuel gas", money(-e.fuel) + "/d"], ["Steam", money(-e.steam) + "/d"], ["Margin", money(e.margin) + "/d", e.margin > 0 ? "good" : "bad"], ["Per barrel", `$${f2(e.perBbl)}`]]); }
      case "eq-h101": return readouts("heater");
      case "eq-h201": case "eq-c201": case "eq-ejectors": return readouts("vac");
      case "eq-c101": return rd([["Flash zone", `${f1(o.Tfz)} °C · ${f1(o.vapLV * 100)} % vapour`], ["Top", `${f1(o.Ttop)} °C`], ["Overflash", `${f1(o.overflash)} %`, o.overflash < 1 ? "bad" : ""], ["Max tray loading", `${f0(o.floodMax)} % flood`, o.floodMax > 100 ? "bad" : o.floodMax > 90 ? "warn" : ""], ["Cuts (TBP)", `${f0(a.cuts.c1)} / ${f0(a.cuts.c2)} / ${f0(a.cuts.c3)} / ${f0(a.cuts.c4)} °C`]]);
      case "eq-desalter": return rd([["Inlet temperature", `${f1(o.Tdes)} °C`], ["Salt in → out", `${f1(o.saltIn)} → ${f2(s.lag.saltOut)} PTB`, s.lag.saltOut > 3 ? "bad" : ""], ["Efficiency", `${f1(o.desaltEff * 100)} %`], ["BS&W out", `${f2(o.bsw)} %`, o.bsw > 0.3 ? "bad" : ""]]);
      case "eq-overhead": return rd([["Top / dew point", `${f1(o.Ttop)} / ${f1(o.Tdew)} °C`, o.dewMargin < 14 ? "bad" : ""], ["Corrosion", `${f1(s.lag.corr)} mpy`, s.lag.corr > 10 ? "bad" : ""], ["Sour water pH", f1(o.ohpH)], ["Condenser duty", `${f1(o.Qcond)} / ${f1(o.QcondMax)} MW`]]);
      case "eq-preheat": case "eq-hottrain": case "eq-pa": return rd([["Desalter inlet", `${f1(o.Tdes)} °C`], ["CIT to H-101", `${f1(a.CIT)} °C`], ["Pumparound duty", `${f1(sim.sp.tpa + sim.sp.mpa + sim.sp.bpa)} MW`], ["Condenser duty", `${f1(o.Qcond)} MW`]]);
      case "eq-strippers": return rd([["Kero flash / freeze", `${f1(q.keroFlash)} / ${f1(q.keroFreeze)} °C`, s.out.specLag.KERO ? "" : "bad"], ["Diesel T95 / cloud", `${f1(q.dieselT95)} / ${f1(q.dieselCloud)} °C`, s.out.specLag.DIESEL ? "" : "bad"], ["AGO colour", f1(q.agoColor), q.agoColor > 4 ? "bad" : ""]]);
      case "eq-tanks": return rd([["Blend at unit", `${f1(o.sl.api)} °API`], ["Sulfur", `${f2(o.sl.sulfur)} wt%`], ["Salt", `${f1(o.saltIn)} PTB`], ["Ni + V", `${f0(o.sl.metals)} ppm`]]);
      case "eq-lightends": return rd([["LPG", `${f1(s.lag.yields.LPG * 100)} %`], ["Light naphtha", `${f1(s.lag.yields.LN * 100)} %`], ["Heavy naphtha", `${f1(s.lag.yields.HN * 100)} %`], ["HN end point", `${f1(q.hnEP)} °C`, s.out.specLag.HN ? "" : "bad"]]);
      case "eq-products": return rd(PRODUCTS.map((p) => [p.name, `${f1(o.econ.value[p.key].bpd / 1000)} kBPD`, o.econ.value[p.key].off ? "bad" : ""]));
    }
    return "";
  }
  function updatePanel(force) {
    for (const b of bound) {
      b.pv.textContent = CTL[b.k][2](sim);
      if (document.activeElement !== b.r && document.activeElement !== b.n && +b.r.value !== sim.sp[b.k]) b.set(sim.sp[b.k]);
    }
    $$("[data-rd]").forEach((e) => { const h = readouts(e.dataset.rd); if (e._h !== h) { e.innerHTML = h; e._h = h; } });
    $$("[data-act=p101A]").forEach((b) => { b.textContent = sim.ev.p101A ? "Stop P-101A" : "Start P-101A"; });
    $$("[data-act=p101B]").forEach((b) => { b.textContent = sim.ev.p101B ? "Stop P-101B" : "Start P-101B"; b.classList.toggle("primary", !sim.ev.p101A && !sim.ev.p101B); });
    $$("[data-act=reset1]").forEach((b) => { b.disabled = !sim.ev.h1trip; b.style.opacity = sim.ev.h1trip ? 1 : 0.45; b.classList.toggle("primary", sim.ev.h1trip && sim.canReset("h1")); });
    $$("[data-act=reset2]").forEach((b) => { b.disabled = !sim.ev.h2trip; b.style.opacity = sim.ev.h2trip ? 1 : 0.45; });
    const st = { crude: `${f0(sim.act.feed)} kBPSD`, heater: sim.ev.h1trip ? "TRIPPED" : `COT ${f1(sim.act.COT1)} °C`, column: `OF ${f1(sim.out.overflash)} %`, pa: `${f1(sim.sp.tpa + sim.sp.mpa + sim.sp.bpa)} MW`,
      strip: "", desalt: `${f2(sim.lag.saltOut)} PTB`, vac: `${f1(sim.act.Ptop2)} mbar`, econ: money(sim.out.econ.margin) + "/d", safety: sim.ev.esd ? "ESD ACTIVE" : "" };
    $$("details.grp").forEach((d) => { const e = $("[data-st]", d); if (e) e.textContent = st[d.dataset.g] || ""; });
  }
  $("#panelBody").addEventListener("click", (e) => {
    const b = e.target.closest("[data-act]"); if (!b) return;
    const a = b.dataset.act, ev = sim.ev;
    if (a === "back") { window.Mimic.select(null); return; }
    if (a === "p101A") { ev.p101A = !ev.p101A; sim.log("info", `P-101A ${ev.p101A ? "started" : "stopped"} by operator`); }
    if (a === "p101B") { ev.p101B = !ev.p101B; sim.log("info", `P-101B ${ev.p101B ? "started" : "stopped"} by operator`); }
    if (a === "reset1") { if (!sim.resetTrip("h1")) toast("H-101 cannot be relit: restore charge flow above 60 % first."); }
    if (a === "reset2") { if (!sim.resetTrip("h2")) toast("H-201 cannot be relit: restore residue flow first."); }
    if (a === "motive") { sim.sp.motive = 100; if (M) M.fixed = true; sim.log("info", "HP steam bypass lined up to ejector motive header"); }
    if (a === "esd") { if (b.dataset.armed) { ev.esd = true; sim.log("trip", "ESD-1 activated from HS-9000"); delete b.dataset.armed; b.textContent = "ESD-1 · HS-9000"; } else { b.dataset.armed = "1"; b.textContent = "Press again to trip the unit"; setTimeout(() => { if (b.dataset.armed) { delete b.dataset.armed; b.textContent = "ESD-1 · HS-9000"; } }, 4000); } }
    if (a === "esdreset") { if (ev.esd) { ev.esd = false; sim.log("info", "ESD-1 reset. Restart pumps, then reset the heater SIS."); } }
    if (a === "resetall") { sim.reset(); M = null; renderMission(); trend.length = 0; alarmState.clear(); alarmLog.length = 0; renderPanel(window.Mimic.selected); }
    updatePanel();
  });

  window.Mimic.onSelect((id) => { renderPanel(id && EQUIP[id] ? id : null); if (id && window.Field) window.Field.focusId(id); });

  // ================================================================ alarms
  const alarmState = new Map(); // id -> {t, pri, acked}
  const alarmLog = []; // {t, pri, tag, msg, why, id, cleared, acked}
  let lastEventIdx = 0;
  function checkAlarms() {
    const o = sim.out;
    if (sim.act.feed < 5 && sim.ev.esd) { /* unit down: suppress process alarms, keep trips */ }
    for (const a of ALARMS) {
      let on = false, hh = false;
      try { on = a.cond(o, sim); hh = on && a.hh ? a.hh(o, sim) : false; } catch (e) { on = false; }
      if (sim.act.feed < 15 && !["h1trip", "h2trip", "p101"].includes(a.id)) on = false;
      const cur = alarmState.get(a.id);
      const pri = hh ? "HH" : a.pri;
      if (on && (!cur || cur.pri !== pri)) {
        const ent = { t: sim.t, pri, tag: a.tag, msg: a.msg + (hh ? " (high-high)" : ""), why: a.why, id: a.id, cleared: false, acked: false };
        alarmState.set(a.id, { pri, ent }); alarmLog.unshift(ent); beep(pri);
      } else if (!on && cur) { cur.ent.cleared = true; alarmState.delete(a.id); }
    }
    while (lastEventIdx < sim.events.length) {
      const e = sim.events[lastEventIdx++];
      alarmLog.unshift({ t: e.t, pri: e.kind === "trip" ? "T" : "I", tag: e.kind === "trip" ? "SIS" : "OPR", msg: e.msg, cleared: e.kind !== "trip", acked: e.kind !== "trip" });
      if (e.kind === "trip") beep("T");
    }
    if (lastEventIdx > sim.events.length) lastEventIdx = sim.events.length;
    while (alarmLog.length > 60) alarmLog.pop();
    renderAlarms();
  }
  function hhmm(t) { const m = Math.floor(t / 60); return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); }
  function renderAlarms() {
    const box = $("#alarms");
    const html = alarmLog.length ? alarmLog.map((a, i) => `<div class="al ${a.acked ? "" : "new"} ${a.cleared && a.pri !== "I" ? "cleared" : ""}"><span class="t">${hhmm(a.t)}</span><span class="p ${a.pri}">${a.pri === "T" ? "TRIP" : a.pri === "I" ? "EVT" : a.pri}</span><span class="g">${esc(a.tag)}</span><span class="m" title="${esc(a.msg)}">${esc(a.msg)}</span>${a.why ? `<button class="why" data-i="${i}">Why?</button>` : "<span></span>"}</div>`).join("")
      : `<div class="empty">No alarms. The unit is lined out at its design point. Change a handle on the right, or pick a scenario.</div>`;
    if (box._h !== html) { box.innerHTML = html; box._h = html; }
    const active = [...alarmState.values()];
    const unacked = alarmLog.filter((a) => !a.acked && !a.cleared).length;
    const btn = $("#alarmBtn");
    btn.classList.toggle("on", active.length > 0 || unacked > 0);
    btn.classList.toggle("hh", active.some((a) => a.pri === "HH" || a.pri === "T"));
    $("#alarmCount").textContent = `${active.length} alarm${active.length === 1 ? "" : "s"}`;
    if (window.Field) { const tags = new Set(); for (const [id] of alarmState) for (const t of ALARM_TAGS[id] || []) tags.add(t); window.Field.setAlarmTags(tags); }
  }
  const ALARM_TAGS = { h1trip: ["H-101"], tmt: ["H-101"], lim1: ["H-101"], co: ["H-101"], h2trip: ["H-201"], lim2: ["H-201"], crack: ["H-201"], flood: ["C-101"], of: ["C-101"], dry: ["C-101"], dew: ["C-101", "D-102"], corr: ["D-102", "A-101-B1", "A-101-B2", "A-101-B3"], cond: ["A-101-B1", "A-101-B2", "A-101-B3"], salt: ["D-101A", "D-101B"], bsw: ["D-101A", "D-101B"], tdes: ["D-101A", "D-101B"], vac: ["C-201"], ej: ["J-201", "J-202", "J-203"], kero: ["C-102"], diesel: ["C-103"], ago: ["C-104"], hvgo: ["C-201"], p101: ["P-101A", "P-101B"] };
  $("#alarms").addEventListener("click", (e) => { const b = e.target.closest(".why"); if (!b) return; const a = alarmLog[+b.dataset.i]; if (a) showWhy(a); });
  $("#alarmBtn").addEventListener("click", () => { alarmLog.forEach((a) => (a.acked = true)); renderAlarms(); });
  function showWhy(a) {
    const ov = document.createElement("div"); ov.className = "overlay";
    ov.innerHTML = `<div class="modal" style="width:min(560px,100%)"><header><p class="mono" style="margin:0;color:var(--accent)">${esc(a.tag)} · ${a.pri === "T" ? "TRIP" : a.pri}</p><h2>${esc(a.msg)}</h2></header><div class="brief"><p style="margin:0;color:var(--ink-2)">${esc(a.why)}</p><div><button class="btn primary" data-x>Got it</button></div></div></div>`;
    document.body.appendChild(ov); ov.addEventListener("click", (e) => { if (e.target === ov || e.target.closest("[data-x]")) ov.remove(); });
    a.acked = true; renderAlarms();
  }
  function toast(m) { const t = document.createElement("div"); t.className = "toast"; t.textContent = m; document.body.appendChild(t); setTimeout(() => t.remove(), 3500); }

  // ================================================================ sound
  let actx = null, rumble = null, soundOn = false;
  function initAudio() {
    actx = new (window.AudioContext || window.webkitAudioContext)();
    const len = actx.sampleRate * 2, buf = actx.createBuffer(1, len, actx.sampleRate), d = buf.getChannelData(0);
    let last = 0; for (let i = 0; i < len; i++) { const w = Math.random() * 2 - 1; last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; }
    const src = actx.createBufferSource(); src.buffer = buf; src.loop = true;
    const lp = actx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 180;
    rumble = actx.createGain(); rumble.gain.value = 0;
    src.connect(lp); lp.connect(rumble); rumble.connect(actx.destination); src.start();
  }
  function beep(pri) {
    if (!soundOn || !actx) return;
    const n = pri === "HH" || pri === "T" ? 3 : pri === "H" ? 2 : 1;
    for (let i = 0; i < n; i++) {
      const o = actx.createOscillator(), g = actx.createGain(); o.type = "square"; o.frequency.value = pri === "T" ? 520 : 880;
      const t = actx.currentTime + i * 0.22; g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.06, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.16);
      o.connect(g); g.connect(actx.destination); o.start(t); o.stop(t + 0.18);
    }
  }
  $("#soundBtn").addEventListener("click", (e) => {
    soundOn = !soundOn; if (soundOn && !actx) initAudio(); if (actx && actx.state === "suspended") actx.resume();
    e.currentTarget.textContent = soundOn ? "Sound on" : "Sound off"; e.currentTarget.setAttribute("aria-pressed", soundOn);
    if (rumble) rumble.gain.value = soundOn ? 0.12 : 0;
  });

  // ================================================================ trends
  const trend = [];
  const TRENDS = [
    { k: "margin", t: "Margin", u: "k$/d", fmt: (v) => f0(v / 1000), color: "#58c487", span: 40000 },
    { k: "cot1", t: "H-101 COT", u: "°C", fmt: f1, color: "#ff8a4a", span: 6 },
    { k: "diesel", t: "Diesel yield", u: "% crude", fmt: f1, color: "#e8d66a", span: 2 },
    { k: "flood", t: "C-101 max flood", u: "%", fmt: f0, color: "#62c6e3", limit: 100, span: 10 },
    { k: "p2", t: "Vac flash zone", u: "mbar", fmt: f0, color: "#b9a0ff", span: 10 },
    { k: "corr", t: "OH corrosion", u: "mpy", fmt: f1, color: "#f2c94c", limit: 10, span: 4 },
  ];
  $("#trends").innerHTML = TRENDS.map((t) => `<div class="tr"><div class="h"><span>${t.t}</span><span>${t.u}</span></div><div class="v num" data-tv="${t.k}">–</div><canvas data-tc="${t.k}"></canvas></div>`).join("");
  let lastSample = -1e9;
  function sampleTrend() {
    const iv = Math.max(1, Math.min(20, speed * 0.4));
    if (sim.t - lastSample < iv) return;
    lastSample = sim.t; trend.push(sim.snapshot());
    const cut = sim.t - 2 * 3600; while (trend.length && trend[0].t < cut) trend.shift();
    if (trend.length > 900) trend.splice(0, trend.length - 900);
  }
  function drawTrends() {
    for (const t of TRENDS) {
      const c = $(`[data-tc="${t.k}"]`), v = $(`[data-tv="${t.k}"]`);
      if (trend.length) v.textContent = t.fmt(trend[trend.length - 1][t.k]);
      window.Charts.spark(c, trend, t.k, { color: t.color, limit: t.limit, span: t.span });
    }
  }

  // ================================================================ missions
  let M = null;
  function openScenarios() {
    const ov = document.createElement("div"); ov.className = "overlay"; ov.id = "scenOv";
    ov.innerHTML = `<div class="modal"><header><h2>Choose a shift</h2><p>Each scenario starts the unit at its FEED design point: 100,000 BPSD of Arab Light, every number calibrated to the project's heat and material balance. Missions are scored on what the analysers and the safety system see.</p></header>
      <div class="missions">${Object.entries(MISSIONS).map(([k, m]) => `<button class="mcard" data-m="${k}"><span class="k">${m.k}</span><b>${m.t}</b><span>${m.d}</span>${m.obj ? `<small>${m.obj.length} objectives</small>` : ""}</button>`).join("")}</div></div>`;
    document.body.appendChild(ov);
    ov.addEventListener("click", (e) => { if (e.target === ov) { ov.remove(); return; } const b = e.target.closest("[data-m]"); if (b) { ov.remove(); brief(b.dataset.m); } });
  }
  function brief(key) {
    const m = MISSIONS[key];
    if (key === "tour") { startMission("sandbox", true); startTour(); return; }
    if (key === "sandbox") { startMission("sandbox"); toast("Sandbox: the unit is at its design point. It is all yours."); return; }
    const ov = document.createElement("div"); ov.className = "overlay";
    ov.innerHTML = `<div class="modal" style="width:min(640px,100%)"><header><p class="mono" style="margin:0;color:var(--accent)">${m.k}</p><h2>${m.t}</h2><p>${m.d}</p></header>
      <div class="brief"><div><h3 style="margin:0 0 6px;font:600 15px var(--f-display);letter-spacing:.06em;text-transform:uppercase">Objectives</h3><ul class="objectives">${m.obj.map((o) => `<li>${o.t}</li>`).join("")}</ul></div>
      <div><h3 style="margin:0 0 6px;font:600 15px var(--f-display);letter-spacing:.06em;text-transform:uppercase">Shift notes</h3><ul>${m.brief.map((b) => `<li>${b}</li>`).join("")}</ul></div>
      <div style="display:flex;gap:8px"><button class="btn primary" data-go>Take the shift</button><button class="btn" data-x>Back</button></div></div></div>`;
    document.body.appendChild(ov);
    ov.addEventListener("click", (e) => { if (e.target === ov || e.target.closest("[data-x]")) { ov.remove(); openScenarios(); } if (e.target.closest("[data-go]")) { ov.remove(); startMission(key); } });
  }
  function startMission(key, quiet) {
    endTour();
    sim.reset(); trend.length = 0; alarmState.clear(); alarmLog.length = 0; lastEventIdx = 0; lastSample = -1e9;
    const m = MISSIONS[key];
    M = m.obj ? { key, m, t0: sim.t, base: sim.out.econ.margin, st: {}, done: false, alarms: 0 } : null;
    if (M && m.setup) m.setup(sim, M);
    if (m.realtime) setSpeed(1); else setSpeed(30);
    window.Mimic.select(null);
    renderPanel(null); renderMission();
    setTab("console");
  }
  function missionTick() {
    if (!M || M.done) return;
    const m = M.m, el = sim.t - M.t0;
    if (m.tick) m.tick(sim, M);
    for (const o of m.obj) {
      const st = M.st[o.id];
      if (o.keep) { if (st !== "fail" && !o.test(sim, M)) M.st[o.id] = "fail"; }
      else if (!o.end && st !== "done" && o.test(sim, M)) M.st[o.id] = "done";
    }
    if (el >= m.dur) finishMission();
  }
  function finishMission() {
    const m = M.m; M.done = true;
    for (const o of m.obj) { if (o.end) M.st[o.id] = o.test(sim, M) ? "done" : "fail"; if (o.keep && M.st[o.id] !== "fail") M.st[o.id] = "done"; if (!M.st[o.id]) M.st[o.id] = "fail"; }
    const ok = m.obj.filter((o) => M.st[o.id] === "done").length;
    const dm = sim.out.econ.margin - M.base;
    const grade = ok === m.obj.length ? (dm > 0 || M.key !== "squeeze" ? "Shift handed over clean" : "Safe, but no money made") : ok >= m.obj.length - 1 ? "Close: one objective missed" : "Rough shift";
    renderMission();
    setSpeed(0);
    const ov = document.createElement("div"); ov.className = "overlay";
    ov.innerHTML = `<div class="modal" style="width:min(620px,100%)"><header><p class="mono" style="margin:0;color:var(--accent)">${m.t} · debrief</p><h2>${grade}</h2><p>${ok} of ${m.obj.length} objectives met. Margin at hand-over ${money(sim.out.econ.margin)}/day (${dm >= 0 ? "+" : "−"}$${f0(Math.abs(dm))} against the start). Shift P&amp;L ${money(sim.cum.profit)}.</p></header>
      <div class="brief"><ul class="objectives">${m.obj.map((o) => `<li class="${M.st[o.id]}">${o.t}</li>`).join("")}</ul>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary" data-again>Run it again</button><button class="btn" data-more>Other scenarios</button><button class="btn" data-x>Keep the unit running</button></div></div></div>`;
    document.body.appendChild(ov);
    ov.addEventListener("click", (e) => {
      if (e.target.closest("[data-again]")) { ov.remove(); startMission(M.key); }
      else if (e.target.closest("[data-more]")) { ov.remove(); openScenarios(); }
      else if (e.target === ov || e.target.closest("[data-x]")) { ov.remove(); M = null; renderMission(); setSpeed(30); }
    });
  }
  function renderMission() {
    const box = $("#missionBox");
    if (!M) { box.hidden = true; return; }
    box.hidden = false;
    const m = M.m, left = Math.max(0, m.dur - (sim.t - M.t0));
    const dm = sim.out.econ.margin - M.base;
    const html = `<h4>${m.t}<span>${hhmm(left)} left</span></h4><ul class="objectives">${m.obj.map((o) => `<li class="${M.st[o.id] || ""}">${o.t}</li>`).join("")}</ul>
      <p class="mono" style="margin:8px 0 0;font-size:12px;color:var(--ink-2)">Δ margin ${dm >= 0 ? "+" : "−"}$${f0(Math.abs(dm) / 1000)}k/day</p>`;
    if (box._h !== html) { box.innerHTML = html; box._h = html; }
  }
  $("#scenBtn").addEventListener("click", openScenarios);

  // ================================================================ guided tour
  let tourI = -1, coach = null;
  function startTour() { setTab("console"); tourI = 0; showTour(); }
  function endTour() { tourI = -1; if (coach) coach.remove(); coach = null; window.Mimic.focus(null); }
  function showTour() {
    if (tourI < 0) return;
    const st = TOUR[tourI];
    const ring = window.Mimic.focus(st.id);
    if (!coach) { coach = document.createElement("div"); coach.className = "coach"; document.body.appendChild(coach); coach.addEventListener("click", tourNav); }
    coach.innerHTML = `<div class="k">${st.k}</div><h3>${st.t}</h3><p>${st.p}</p><div class="live" data-live></div>
      <div class="nav"><span>${tourI + 1} / ${TOUR.length}</span><button class="btn small" data-t="end">End tour</button>${tourI ? `<button class="btn small" data-t="prev">Back</button>` : ""}<button class="btn small primary" data-t="next">${tourI === TOUR.length - 1 ? "Finish" : "Next"}</button></div>`;
    placeCoach(ring);
    updTourLive();
    if (ring) { const r = ring.getBoundingClientRect(), v = $("#v-console"), vr = v.getBoundingClientRect(); if (r.left < vr.left || r.right > vr.right) v.scrollLeft += r.left - vr.left - 40; }
  }
  function placeCoach(ring) {
    const vw = innerWidth, vh = innerHeight, cw = Math.min(400, vw - 32), ch = coach.offsetHeight || 260;
    let x = 16, y = vh - ch - 16;
    if (ring) {
      const r = ring.getBoundingClientRect();
      x = r.right + 16 + cw < vw - 16 ? r.right + 16 : r.left - cw - 16;
      if (x < 16) x = Math.max(16, Math.min(vw - cw - 16, r.left));
      y = Math.max(70, Math.min(vh - ch - 16, r.top));
      if (vw < 700) { x = 16; y = vh - ch - 16; }
    }
    coach.style.left = x + "px"; coach.style.top = y + "px";
  }
  function updTourLive() { if (!coach || tourI < 0) return; const l = $("[data-live]", coach); if (l) l.textContent = TOUR[tourI].live(sim.out, sim); }
  function tourNav(e) {
    const b = e.target.closest("[data-t]"); if (!b) return;
    const a = b.dataset.t;
    if (a === "end") return endTour();
    if (a === "next") { if (tourI === TOUR.length - 1) { endTour(); toast("Tour complete. Try a mission next: Scenarios, top right."); return; } tourI++; }
    if (a === "prev") tourI = Math.max(0, tourI - 1);
    showTour();
  }
  addEventListener("resize", () => { if (coach) placeCoach(document.querySelector("#mimic .tour-ring")); });
  $("#v-console").addEventListener("scroll", () => { if (coach) placeCoach(document.querySelector("#mimic .tour-ring")); });

  // ================================================================ learn view
  function buildLearn() {
    const h = D.heaters["H-101"], a = D.atm;
    $("#v-learn").innerHTML = `
      <div class="learn-hero"><div class="card"><h2>One unit, every barrel</h2>
        <p>The crude distillation unit is the front door of a refinery. Every barrel the refinery buys goes through it first, and every downstream unit lives on what it makes. This simulator is built on the project's own FEED design: the same equipment numbers, instrument tags and heat and material balance as the 104-document package in this repository.</p>
        <p>The model splits the crude into about 110 boiling-point slices and recalculates heater duty, vaporisation, cut points, product overlaps, qualities, vacuum lift, desalting, corrosion, tray loading and margin several times a second.</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary" data-l="tour">Follow a barrel (guided)</button><button class="btn" data-l="scen">Pick a mission</button></div></div>
        <div class="factgrid">
          <div><small>Charge</small><b>${f0(D.crude.bpsd)} BPSD</b></div><div><small>Crude</small><b>${D.crude.name.replace(" (design)", "")} ${D.crude.api}°API</b></div>
          <div><small>H-101 fired</small><b>${f1(h.Q_fired_kw / 1000)} MW</b></div><div><small>C-101</small><b>6.9 m × 41 trays</b></div>
          <div><small>Flash zone</small><b>${f1(a.T_fz)} °C · ${f2(a.P_fz_barg)} barg</b></div><div><small>Vacuum flash zone</small><b>${f0(D.vac.P_fz_mbar)} mbar(a)</b></div>
          <div><small>Pumparound duty</small><b>${f1((a.pa.TPA.duty_kw + a.pa.MPA.duty_kw + a.pa.BPA.duty_kw) / 1000)} MW</b></div><div><small>Products</small><b>10 streams</b></div>
        </div></div>
      <h3 style="font:600 17px var(--f-display);letter-spacing:.06em;text-transform:uppercase;margin:6px 0 10px">Ideas, each with an experiment</h3>
      <div class="learn">${CONCEPTS.map((c, i) => `<div class="lcard"><span class="k">${c.k}</span><h3>${c.t}</h3><p>${c.p}</p><button class="btn small" data-c="${i}">${c.try.label}</button></div>`).join("")}</div>
      <h3 style="font:600 17px var(--f-display);letter-spacing:.06em;text-transform:uppercase;margin:18px 0 10px">Equipment</h3>
      <div class="learn">${Object.entries(EQUIP).map(([k, e]) => `<div class="lcard"><span class="k">${e.tag}</span><h3>${e.name}</h3><p>${e.what}</p><button class="btn small" data-e="${k}">Open on the console</button></div>`).join("")}</div>`;
    $("#v-learn").addEventListener("click", (e) => {
      const l = e.target.closest("[data-l]"), c = e.target.closest("[data-c]"), q = e.target.closest("[data-e]");
      if (l) { if (l.dataset.l === "tour") brief("tour"); else openScenarios(); }
      if (q) { setTab("console"); window.Mimic.select(q.dataset.e); }
      if (c) runTry(CONCEPTS[+c.dataset.c].try.act);
    });
  }
  function runTry(act) {
    const [kind, a, b] = act.split(":");
    if (kind === "tab") setTab(a);
    if (kind === "select") { setTab("console"); window.Mimic.select(a); }
    if (kind === "mission") brief(a);
    if (kind === "nudge") {
      const [mn, mx] = LIMITS[a]; sim.sp[a] = Math.max(mn, Math.min(mx, +(sim.sp[a] + +b).toFixed(2)));
      setTab(["kero", "ago", "cot1"].includes(a) ? "cuts" : "console");
      const grp = GROUPS.find((g) => g.keys.includes(a));
      renderPanel(null);
      if (grp) { const d = $(`details[data-g="${grp.id}"]`); if (d) { d.open = true; d.scrollIntoView({ block: "nearest" }); } }
      toast(`${CTL[a][0]} set to ${sim.sp[a]} ${LIMITS[a][3]}. Watch the plant respond; restore it from the panel.`);
    }
  }

  // ================================================================ tabs, speed, clock
  function setTab(v) {
    $$("#tabs [role=tab]").forEach((b) => b.setAttribute("aria-selected", b.dataset.v === v ? "true" : "false"));
    for (const id of ["console", "field", "cuts", "learn"]) $("#v-" + id).hidden = id !== v;
    if (v !== "console" && tourI >= 0) endTour();
    if (v === "field") { window.Field.start(); setTimeout(window.Field.resize, 30); }
    if (v === "cuts") window.Charts.updateCuts(sim);
    try { history.replaceState(null, "", "#" + v); } catch (e) { /* sandboxed */ }
  }
  $("#tabs").addEventListener("click", (e) => { const b = e.target.closest("[role=tab]"); if (b) setTab(b.dataset.v); });
  addEventListener("hashchange", () => { const h = location.hash.slice(1); if (["console", "field", "cuts", "learn"].includes(h)) setTab(h); });
  function setSpeed(s) { speed = s; paused = s === 0; $$("#speedSeg button").forEach((b) => b.setAttribute("aria-pressed", +b.dataset.s === s ? "true" : "false")); }
  $("#speedSeg").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) setSpeed(+b.dataset.s); });
  $$(".field-hud [data-cam]").forEach((b) => b.addEventListener("click", () => window.Field.camTo(b.dataset.cam)));
  $("#orbitBtn").addEventListener("click", () => window.Field.orbit());
  window.Field.setSim(sim);
  window.Field.onPick((id) => { window.Mimic.select(id); });
  window.Field.setLabelText((key, s) => {
    const o = s.out, a = s.act;
    switch (key) {
      case "h101": return { title: "heater", lines: [`COT ${f1(a.COT1)} °C`, `${f1(a.fired1)} MW fired`, `TMT ${f0(o.TMT1)} °C`], alarm: s.ev.h1trip || o.TMT1 > 520, hot: true };
      case "c101": return { title: "fractionator", lines: [`top ${f1(o.Ttop)} °C · fz ${f1(o.Tfz)} °C`, `flood ${f0(o.floodMax)} %`, `overflash ${f1(o.overflash)} %`], alarm: o.floodMax > 90 || o.overflash < 1 };
      case "desalter": return { title: "desalters", lines: [`salt ${f2(s.lag.saltOut)} PTB`, `${f1(o.Tdes)} °C`], alarm: s.lag.saltOut > 3 };
      case "c201": return { title: "vacuum", lines: [`${f1(a.Ptop2)} mbar top`, `HVGO cut ${f0(a.cutsV.cHvgo)} °C`], alarm: a.Ptop2 > 30 };
      case "h201": return { title: "heater", lines: [`COT ${f1(a.COT2)} °C`, `${f1(a.fired2)} MW`], alarm: s.ev.h2trip, hot: true };
      case "overhead": return { title: "condensers", lines: [`${f1(o.Qcond)} MW`, `corrosion ${f1(s.lag.corr)} mpy`], alarm: s.lag.corr > 10 };
      case "ejectors": return { title: "ejectors", lines: [o.ejBroken ? "BROKEN" : `load ${f0(o.ejLoad * 100)} %`, `steam ${f0(s.sp.motive)} %`], alarm: o.ejBroken };
      case "lightends": return { title: "splitter", lines: [`HN EP ${f0(s.q.hnEP)} °C`] };
      case "preheat": return { title: "preheat", lines: [`CIT ${f1(a.CIT)} °C`] };
    }
    return { lines: [] };
  });
  $("#mimic").addEventListener("click", (e) => { if (!e.target.closest(".hit")) window.Mimic.select(null); });

  // ================================================================ main loop
  let lastT = performance.now(), acc = 0, slow = 0, slower = 0;
  function frame(now) {
    const dtReal = Math.min(0.25, (now - lastT) / 1000); lastT = now;
    if (!paused) {
      let plant = dtReal * speed;
      const step = Math.max(0.5, Math.min(5, plant / 8));
      let n = 0;
      while (plant > 1e-6 && n < 40) { const h = Math.min(step, plant); sim.lastDt = h; sim.step(h); missionTick(); plant -= h; n++; }
      sampleTrend();
    }
    window.Mimic.update(sim);
    slow += dtReal; slower += dtReal;
    if (slow > 0.25) {
      slow = 0;
      const o = sim.out;
      $("#kMargin").textContent = money(o.econ.margin);
      $("#kMargin").style.color = o.econ.margin >= 0 ? "var(--ok)" : "var(--alarm)";
      $("#kMarginSub").textContent = `USD/day · ${o.econ.perBbl.toFixed(2)} $/bbl`;
      $("#kShift").textContent = money(sim.cum.profit);
      $("#kFeed").textContent = `${f1(sim.act.feed)} kBPSD`;
      const sl = o.sl; $("#kCrude").textContent = sim.blendAct > 0.5 ? `${CRUDES[sim.sp.crudeA].short}/${CRUDES[sim.sp.crudeB].short} ${f0(100 - sim.blendAct)}:${f0(sim.blendAct)} · ${f1(sl.api)}°API` : `${CRUDES[sim.sp.crudeA].name} · ${f1(sl.api)}°API`;
      const tm = Math.floor(sim.t); $("#kClock").textContent = `${String(Math.floor(tm / 3600)).padStart(2, "0")}:${String(Math.floor(tm / 60) % 60).padStart(2, "0")}:${String(tm % 60).padStart(2, "0")}`;
      updatePanel(); checkAlarms(); renderMission(); updTourLive(); drawTrends();
      if (rumble && soundOn) rumble.gain.value = 0.04 + 0.12 * (sim.ev.h1trip ? 0 : sim.act.fired1 / 78);
    }
    if (slower > 1) { slower = 0; window.Charts.updateCuts(sim); }
    requestAnimationFrame(frame);
  }

  // ================================================================ boot
  window.Charts.buildCuts($("#v-cuts"));
  buildLearn();
  renderPanel(null);
  const h0 = location.hash.slice(1);
  setTab(["console", "field", "cuts", "learn"].includes(h0) ? h0 : "console");
  requestAnimationFrame(frame);
  setTimeout(() => { if (!sessionStorageGet("cduSeen")) { openScenarios(); sessionStorageSet("cduSeen", "1"); } }, 400);
  function sessionStorageGet(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
  function sessionStorageSet(k, v) { try { sessionStorage.setItem(k, v); } catch (e) { /* storage blocked */ } }
})();
