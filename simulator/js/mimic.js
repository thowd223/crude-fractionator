/* CDU LIVE - console mimic (SVG overview of the unit, built in code and bound to the simulator). */
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.getElementById("mimic");
  const PRODUCTS = window.CDU.PRODUCTS;
  const f0 = (x) => (isFinite(x) ? Math.round(x).toLocaleString("en-US") : "–");
  const f1 = (x) => (isFinite(x) ? x.toFixed(1) : "–");
  const f2 = (x) => (isFinite(x) ? x.toFixed(2) : "–");

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    (parent || svg).appendChild(e);
    return e;
  }
  function txt(x, y, s, cls, parent, anchor) { const t = el("text", { x, y, class: cls || "val", "text-anchor": anchor || "start" }, parent); t.textContent = s; return t; }

  // temperature -> colour (steel blue -> amber -> red)
  const TSTOPS = [[20, [93, 138, 168]], [120, [120, 160, 150]], [200, [214, 180, 80]], [280, [235, 150, 60]], [350, [240, 105, 55]], [420, [255, 64, 52]]];
  function tcol(T) {
    if (!isFinite(T)) return "rgb(80,95,103)";
    let a = TSTOPS[0], b = TSTOPS[TSTOPS.length - 1];
    for (let i = 1; i < TSTOPS.length; i++) if (T <= TSTOPS[i][0]) { a = TSTOPS[i - 1]; b = TSTOPS[i]; break; }
    const t = Math.max(0, Math.min(1, (T - a[0]) / (b[0] - a[0] || 1)));
    const c = a[1].map((v, i) => Math.round(v + (b[1][i] - v) * t));
    return `rgb(${c[0]},${c[1]},${c[2]})`;
  }

  // ---------------------------------------------------------------- defs
  const defs = el("defs");
  defs.innerHTML = `
    <radialGradient id="fireGlow" cx="50%" cy="85%" r="75%"><stop offset="0" stop-color="#ffb347" stop-opacity=".95"/><stop offset=".45" stop-color="#ff6a2a" stop-opacity=".45"/><stop offset="1" stop-color="#3a0d05" stop-opacity="0"/></radialGradient>
    <radialGradient id="fireGlow2" cx="50%" cy="85%" r="75%"><stop offset="0" stop-color="#ffb347" stop-opacity=".95"/><stop offset=".45" stop-color="#ff6a2a" stop-opacity=".45"/><stop offset="1" stop-color="#3a0d05" stop-opacity="0"/></radialGradient>
    <linearGradient id="flame" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff4c2"/><stop offset=".35" stop-color="#ffb02e"/><stop offset=".8" stop-color="#ff4e1a" stop-opacity=".7"/><stop offset="1" stop-color="#ff2a00" stop-opacity="0"/></linearGradient>
    <linearGradient id="colGrad" x1="0" y1="0" x2="0" y2="1"></linearGradient>
    <linearGradient id="vacGrad" x1="0" y1="0" x2="0" y2="1"></linearGradient>
    <pattern id="packing" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 6 L6 0" stroke="#ffffff22" stroke-width="1"/></pattern>`;

  const layerPipes = el("g", { id: "pipes" });
  const layerFlows = el("g", { id: "flows" });
  const layerEq = el("g", { id: "equip" });
  const layerTxt = el("g", { id: "texts" });
  const layerTop = el("g", { id: "overlay" });
  const B = {}; // bound elements

  // ---------------------------------------------------------------- streams (polyline paths)
  const STREAMS = [];
  function stream(id, pts, temp, flow, opts) {
    const d = "M" + pts.map((p) => p.join(" ")).join(" L");
    const base = el("path", { d, class: "pipe" }, layerPipes);
    const fl = el("path", { d, class: "flow" + (opts && opts.vapour ? " v" : ""), stroke: "#888" }, layerFlows);
    STREAMS.push({ id, base, fl, temp, flow, last: -1 });
    return fl;
  }

  // ---------------------------------------------------------------- geometry
  const COL = { x: 930, w: 80, top: 60, bot: 650 };
  const trayY = (n) => 85 + (n - 1) * 13;
  const VAC = { x: 1290, w: 80, top: 600, bot: 890 };
  const PROW = { LPG: 50, LN: 110, HN: 175, KERO: 280, DIESEL: 430, AGO: 540, LVGO: 632, HVGO: 702, SLOP: 772, VR: 860 };
  const PX = 1565;

  // ---------------------------------------------------------------- feed: tanks, pumps, preheat, desalters
  function hitGroup(id) { const g = el("g", { class: "hit", "data-eq": id }, layerEq); g.addEventListener("click", () => select(id)); return g; }
  {
    const g = hitGroup("tanks");
    for (const [i, y] of [[0, 80], [1, 232]]) {
      el("rect", { x: 30, y, width: 120, height: 118, rx: 6, class: "vessel" }, g);
      B["tankFill" + i] = el("rect", { x: 31, y: y + 30, width: 118, height: 87, rx: 4, fill: "#3a2a1c", opacity: 0.9 }, g);
      el("path", { d: `M30 ${y + 14} Q90 ${y - 10} 150 ${y + 14}`, fill: "none", stroke: "var(--vessel-edge)" }, g);
      B["tankName" + i] = txt(90, y + 52, "–", "lbl", g, "middle");
      B["tankPct" + i] = txt(90, y + 74, "–", "val", g, "middle");
      B["tankSub" + i] = txt(90, y + 93, "–", "lbl-s", g, "middle");
    }
    txt(90, 368, "CRUDE TANKAGE", "lbl-s", g, "middle");
    // pump P-101
    el("circle", { cx: 195, cy: 415, r: 13, class: "vessel" }, g);
    B.p101 = el("path", { d: "M188 407 L204 415 L188 423 Z", fill: "#58c487" }, g);
    txt(195, 446, "P-101A/B", "lbl-s", g, "middle");
  }
  stream("crudeA", [[150, 140], [172, 140], [172, 415], [182, 415]], () => 30, (o, s) => s.act.feed * (1 - s.blendAct / 100));
  stream("crudeB", [[150, 292], [172, 292], [172, 415]], () => 30, (o, s) => s.act.feed * (s.blendAct / 100));
  {
    const g = hitGroup("preheat");
    el("rect", { x: 232, y: 392, width: 128, height: 46, rx: 5, class: "box" }, g);
    txt(296, 410, "COLD TRAIN", "lbl", g, "middle"); txt(296, 427, "E-101…E-105", "lbl-s", g, "middle");
    B.tdesIn = txt(296, 384, "", "val", g, "middle");
  }
  stream("c1", [[208, 415], [232, 415]], () => 30, (o, s) => s.act.feed);
  {
    const g = hitGroup("desalter");
    for (const [i, x] of [[0, 392], [1, 532]]) {
      el("rect", { x, y: 396, width: 118, height: 38, rx: 19, class: "vessel" }, g);
      B["dsWater" + i] = el("rect", { x: x + 6, y: 420, width: 106, height: 10, rx: 4, fill: "#2d6e93", opacity: 0.85 }, g);
      el("path", { d: `M${x + 36} 401 l6 8 l-5 0 l6 9`, stroke: "#f2c94c", fill: "none", "stroke-width": 1.4 }, g);
      el("path", { d: `M${x + 76} 401 l6 8 l-5 0 l6 9`, stroke: "#f2c94c", fill: "none", "stroke-width": 1.4 }, g);
      txt(x + 59, 452, i ? "D-101B" : "D-101A", "lbl-s", g, "middle");
    }
    B.salt = txt(532, 384, "", "val", g, "middle");
  }
  stream("c2", [[360, 415], [392, 415]], (o) => o.Tdes, (o, s) => s.act.feed);
  stream("c3", [[510, 415], [532, 415]], (o) => o.Tdes, (o, s) => s.act.feed);
  stream("ww", [[392, 470], [392, 440]], () => 120, (o, s) => s.sp.ww * 8, {});
  txt(386, 484, "wash water", "lbl-s", layerTxt, "start");
  {
    const g = hitGroup("hottrain");
    el("circle", { cx: 685, cy: 415, r: 12, class: "vessel" }, g);
    el("path", { d: "M679 408 L693 415 L679 422 Z", fill: "#58c487" }, g);
    txt(685, 446, "P-102", "lbl-s", g, "middle");
    el("rect", { x: 712, y: 392, width: 140, height: 46, rx: 5, class: "box" }, g);
    txt(782, 410, "HOT TRAIN", "lbl", g, "middle"); txt(782, 427, "E-106…E-111", "lbl-s", g, "middle");
    B.cit = txt(782, 456, "", "val", g, "middle");
  }
  stream("c4", [[650, 415], [673, 415]], (o) => o.Tdes, (o, s) => s.act.feed);
  stream("c5", [[697, 415], [712, 415]], (o) => o.Tdes, (o, s) => s.act.feed);
  stream("c6", [[852, 415], [880, 415], [880, 592], [800, 592], [800, 606]], (o, s) => s.act.CIT, (o, s) => s.act.feed);

  // ---------------------------------------------------------------- H-101
  {
    const g = hitGroup("h101");
    el("rect", { x: 744, y: 530, width: 16, height: 66, class: "vessel" }, g); // stack
    B.smoke = el("g", {}, g);
    for (let i = 0; i < 4; i++) el("circle", { cx: 752, cy: 520 - i * 14, r: 5 + i * 2.5, fill: "#9aa5ab", opacity: 0.14 - i * 0.025 }, B.smoke);
    el("rect", { x: 704, y: 606, width: 96, height: 52, rx: 3, class: "vessel" }, g); // convection
    for (let i = 0; i < 4; i++) el("line", { x1: 712, y1: 616 + i * 11, x2: 792, y2: 616 + i * 11, stroke: "#5d6f78", "stroke-width": 2 }, g);
    el("path", { d: "M640 658 L864 658 L864 880 L640 880 Z", class: "vessel" }, g); // radiant
    B.glow1 = el("rect", { x: 642, y: 660, width: 220, height: 218, fill: "url(#fireGlow)", opacity: 0.8 }, g);
    for (let i = 0; i < 9; i++) { el("line", { x1: 650, y1: 668 + i * 23, x2: 650, y2: 680 + i * 23, stroke: "#8a9aa2", "stroke-width": 5, "stroke-linecap": "round" }, g); el("line", { x1: 854, y1: 668 + i * 23, x2: 854, y2: 680 + i * 23, stroke: "#8a9aa2", "stroke-width": 5, "stroke-linecap": "round" }, g); }
    B.flames1 = [];
    for (let i = 0; i < 6; i++) {
      const x = 672 + i * 32;
      const fl = el("path", { d: `M${x - 9} 878 Q${x - 11} 830 ${x} 790 Q${x + 11} 830 ${x + 9} 878 Z`, fill: "url(#flame)", "transform-origin": `${x} 878` }, g);
      B.flames1.push(fl);
    }
    txt(752, 900, "H-101  ATMOSPHERIC HEATER", "lbl", g, "middle");
    B.h1trip = txt(752, 772, "", "lbl", g, "middle");
    B.h1trip.setAttribute("fill", "#ff5b4e");
  }
  stream("tl", [[864, 790], [905, 790], [905, trayY(36)], [COL.x, trayY(36)]], (o, s) => s.act.COT1, (o, s) => s.act.feed * 1.2, { vapour: true });
  B.cot1 = txt(912, 720, "", "val", layerTxt); B.cot1sp = txt(912, 736, "", "val sp", layerTxt);
  txt(912, 704, "COT", "lbl-s", layerTxt);

  // ---------------------------------------------------------------- C-101 + pumparounds + strippers + overhead
  {
    const g = hitGroup("c101");
    el("rect", { x: COL.x, y: COL.top, width: COL.w, height: COL.bot - COL.top, rx: 36, class: "vessel" }, g);
    B.colBody = el("rect", { x: COL.x + 4, y: COL.top + 4, width: COL.w - 8, height: COL.bot - COL.top - 8, rx: 32, fill: "url(#colGrad)", opacity: 0.88 }, g);
    for (let n = 1; n <= 41; n++) el("line", { x1: COL.x + 8, x2: COL.x + COL.w - 8, y1: trayY(n) + 5, y2: trayY(n) + 5, stroke: "#0b1114", "stroke-width": 1, opacity: 0.55 }, g);
    txt(COL.x + COL.w / 2, COL.bot + 22, "C-101", "lbl", g, "middle");
    B.colT = {};
    for (const [k, n] of [["top", 1], ["kero", 10], ["dsl", 22], ["ago", 32], ["fz", 36], ["bot", 41]]) {
      B.colT[k] = txt(COL.x + COL.w / 2, trayY(n) + 9, "", "val", g, "middle");
      B.colT[k].setAttribute("style", "font-size:11px;paint-order:stroke;stroke:#0b1114;stroke-width:3px");
    }
    B.floodRing = el("rect", { x: COL.x - 4, y: COL.top - 4, width: COL.w + 8, height: COL.bot - COL.top + 8, rx: 40, class: "alarm-ring", visibility: "hidden" }, layerTop);
  }
  // pumparounds (left side)
  {
    const g = hitGroup("pa");
    for (const [key, d, r] of [["tpa", 3, 1], ["mpa", 13, 11], ["bpa", 25, 23]]) {
      const yd = trayY(d) + 5, yr = trayY(r) + 5;
      stream("pa_" + key, [[COL.x, yd], [892, yd], [892, yr], [COL.x, yr]], (o, s) => o.profile[d - 1], (o, s) => s.sp[key] * 6);
      el("circle", { cx: 892, cy: (yd + yr) / 2, r: 7, class: "box" }, g);
      el("path", { d: `M886 ${(yd + yr) / 2 + 3} l4 -6 l4 6 l4 -6`, stroke: "#62c6e3", fill: "none", "stroke-width": 1.3 }, g);
      B["pa_" + key] = txt(880, (yd + yr) / 2 + 4, "", "val", g, "end");
      txt(880, (yd + yr) / 2 - 10, key.toUpperCase(), "lbl-s", g, "end");
    }
  }
  // overhead
  {
    const g = hitGroup("overhead");
    el("rect", { x: 1048, y: 14, width: 124, height: 30, rx: 3, class: "box" }, g);
    B.fans = [];
    for (let i = 0; i < 3; i++) { const c = el("g", { transform: `translate(${1070 + i * 40} 29)` }, g); el("circle", { r: 10, fill: "none", stroke: "#5d6f78" }, c); const b = el("path", { d: "M-8 0 L8 0 M0 -8 L0 8", stroke: "#8a9aa2", "stroke-width": 2 }, c); B.fans.push(b); }
    txt(1110, 60, "A-101", "lbl-s", g, "middle");
    el("rect", { x: 1048, y: 92, width: 124, height: 32, rx: 16, class: "vessel" }, g);
    el("rect", { x: 1138, y: 124, width: 18, height: 12, class: "vessel" }, g);
    B.drumLvl = el("rect", { x: 1054, y: 110, width: 112, height: 11, rx: 5, fill: "#8fd3ff", opacity: 0.4 }, g);
    txt(1110, 148, "D-102", "lbl-s", g, "middle");
    B.ttop = txt(1040, 52, "", "val", g, "end"); B.ttopSp = txt(1040, 68, "", "val sp", g, "end");
    B.corrTxt = txt(1185, 150, "", "val", g, "start");
  }
  stream("ovhd", [[970, COL.top], [970, 29], [1048, 29]], (o) => o.Ttop, (o, s) => s.act.feed * 1.4, { vapour: true });
  stream("ovhd2", [[1172, 29], [1186, 29], [1186, 108], [1172, 108]], () => 55, (o, s) => s.act.feed);
  stream("reflux", [[1068, 124], [1068, 168], [1030, 168], [1030, 82], [COL.x + COL.w, 82]], () => 45, (o) => o.refluxKgh / 1500);
  stream("naph", [[1160, 136], [1160, 168], [1218, 168], [1218, 150]], () => 45, (o, s) => s.act.feed * 0.24);
  {
    const g = hitGroup("lightends");
    el("rect", { x: 1206, y: 40, width: 26, height: 170, rx: 13, class: "vessel" }, g);
    el("rect", { x: 1276, y: 30, width: 34, height: 190, rx: 17, class: "vessel" }, g);
    txt(1219, 228, "C-105", "lbl-s", g, "middle"); txt(1293, 238, "C-106", "lbl-s", g, "middle");
  }
  stream("lpg", [[1219, 40], [1219, 26], [1250, 26], [1250, PROW.LPG], [PX, PROW.LPG]], () => 45, (o, s) => s.lag.yields.LPG * s.act.feed * 6);
  stream("stab", [[1219, 210], [1219, 246], [1262, 246], [1262, 150], [1276, 150]], () => 200, (o, s) => s.act.feed * 0.22);
  stream("ln", [[1293, 30], [1293, 18], [1330, 18], [1330, PROW.LN], [PX, PROW.LN]], () => 45, (o, s) => s.lag.yields.LN * s.act.feed * 6);
  stream("hn", [[1293, 220], [1293, 250], [1345, 250], [1345, PROW.HN], [PX, PROW.HN]], () => 45, (o, s) => s.lag.yields.HN * s.act.feed * 6);
  // side strippers
  {
    const g = hitGroup("strippers");
    const S = [["KERO", 10, 196, 72, "C-102"], ["DIESEL", 22, 350, 76, "C-103"], ["AGO", 32, 480, 62, "C-104"]];
    for (const [k, n, y, h, tag] of S) {
      el("rect", { x: 1050, y, width: 30, height: h, rx: 12, class: "vessel" }, g);
      txt(1086, y + 14, tag, "lbl-s", g, "start");
      B["strip" + k] = txt(1086, y + 30, "", "val", g, "start");
    }
  }
  stream("kd", [[COL.x + COL.w, trayY(10) + 4], [1050, trayY(10) + 4]], (o) => o.Tkero, (o, s) => s.sp.kero * 4);
  stream("dd", [[COL.x + COL.w, trayY(22) + 4], [1050, trayY(22) + 4]], (o) => o.Tdiesel, (o, s) => s.sp.diesel * 4);
  stream("ad", [[COL.x + COL.w, trayY(32) + 4], [1050, trayY(32) + 4]], (o) => o.Tago, (o, s) => s.sp.ago * 4);
  stream("kero", [[1065, 268], [1065, PROW.KERO], [PX, PROW.KERO]], () => 45, (o, s) => s.lag.yields.KERO * s.act.feed * 6);
  stream("diesel", [[1065, 426], [1065, PROW.DIESEL], [PX, PROW.DIESEL]], () => 55, (o, s) => s.lag.yields.DIESEL * s.act.feed * 6);
  stream("ago", [[1065, 542], [1065, PROW.AGO], [PX, PROW.AGO]], () => 60, (o, s) => s.lag.yields.AGO * s.act.feed * 6);

  // ---------------------------------------------------------------- VDU
  stream("ar", [[970, COL.bot], [970, 680], [1020, 680], [1020, 700], [1140, 700], [1140, 712]], (o) => o.Tbot1, (o, s) => s.act.feed * 0.4 * 3);
  {
    const g = hitGroup("h201");
    el("path", { d: "M1080 712 L1200 712 L1200 890 L1080 890 Z", class: "vessel" }, g);
    B.glow2 = el("rect", { x: 1082, y: 714, width: 116, height: 174, fill: "url(#fireGlow2)", opacity: 0.8 }, g);
    B.flames2 = [];
    for (let i = 0; i < 3; i++) { const x = 1105 + i * 35; B.flames2.push(el("path", { d: `M${x - 8} 888 Q${x - 10} 850 ${x} 815 Q${x + 10} 850 ${x + 8} 888 Z`, fill: "url(#flame)", "transform-origin": `${x} 888` }, g)); }
    txt(1140, 908, "H-201", "lbl", g, "middle");
    B.h2trip = txt(1140, 800, "", "lbl", g, "middle"); B.h2trip.setAttribute("fill", "#ff5b4e");
  }
  B.cot2 = txt(1206, 760, "", "val", layerTxt); B.cot2sp = txt(1206, 776, "", "val sp", layerTxt); txt(1206, 744, "COT", "lbl-s", layerTxt);
  stream("vtl", [[1200, 820], [1250, 820], [1250, 812], [VAC.x, 812]], (o, s) => s.act.COT2, (o, s) => s.act.feed * 1.1, { vapour: true });
  {
    const g = hitGroup("c201");
    el("rect", { x: VAC.x, y: VAC.top, width: VAC.w, height: VAC.bot - VAC.top, rx: 30, class: "vessel" }, g);
    B.vacBody = el("rect", { x: VAC.x + 4, y: VAC.top + 4, width: VAC.w - 8, height: VAC.bot - VAC.top - 8, rx: 26, fill: "url(#vacGrad)", opacity: 0.88 }, g);
    for (const [y, h] of [[620, 22], [652, 34], [700, 26], [742, 34]]) el("rect", { x: VAC.x + 8, y, width: VAC.w - 16, height: h, fill: "url(#packing)", stroke: "#ffffff22" }, g);
    txt(VAC.x + VAC.w / 2, VAC.bot + 22, "", "lbl", g, "middle");
    B.vacP = txt(VAC.x + VAC.w / 2, 835, "", "val", g, "middle");
    B.vacP.setAttribute("style", "paint-order:stroke;stroke:#0b1114;stroke-width:3px");
    txt(VAC.x - 8, 905, "C-201", "lbl", g, "start");
  }
  {
    const g = hitGroup("ejectors");
    for (let i = 0; i < 3; i++) { el("path", { d: `M${1398 + i * 30} 578 l22 6 l-22 6 z`, class: "vessel" }, g); }
    txt(1440, 606, "J-201/202/203", "lbl-s", g, "middle");
    B.ejTxt = txt(1490, 588, "", "val", g, "start");
  }
  stream("vac_ovhd", [[VAC.x + 40, VAC.top], [VAC.x + 40, 584], [1398, 584]], () => 70, (o, s) => 6 * (s.sp.motive / 100), { vapour: true });
  stream("lvgo", [[VAC.x + VAC.w, PROW.LVGO], [PX, PROW.LVGO]], () => 55, (o, s) => s.lag.yields.LVGO * s.act.feed * 6);
  stream("hvgo", [[VAC.x + VAC.w, PROW.HVGO], [PX, PROW.HVGO]], () => 90, (o, s) => s.lag.yields.HVGO * s.act.feed * 6);
  stream("slop", [[VAC.x + VAC.w, PROW.SLOP], [PX, PROW.SLOP]], () => 300, (o, s) => s.lag.yields.SLOP * s.act.feed * 6);
  stream("vr", [[VAC.x + 40, VAC.bot], [VAC.x + 40, 902], [1470, 902], [1470, PROW.VR], [PX, PROW.VR]], () => 175, (o, s) => s.lag.yields.VR * s.act.feed * 6);

  // ---------------------------------------------------------------- product rundown panel
  {
    const g = hitGroup("products");
    B.prod = {};
    for (const p of PRODUCTS) {
      const y = PROW[p.key];
      const r = el("rect", { x: PX, y: y - 26, width: 228, height: 52, rx: 6, class: "chip" }, g);
      el("rect", { x: PX, y: y - 26, width: 5, height: 52, rx: 2, fill: p.color }, g);
      txt(PX + 14, y - 8, p.name.toUpperCase(), "lbl", g);
      const flow = txt(PX + 14, y + 10, "", "val", g);
      const sub = txt(PX + 14, y + 22, "", "lbl-s", g);
      const pill = el("rect", { x: PX + 168, y: y - 20, width: 52, height: 16, rx: 8, fill: "rgba(88,196,135,.14)" }, g);
      const pillT = txt(PX + 194, y - 8, "ON SPEC", "val", g, "middle"); pillT.setAttribute("style", "font-size:9.5px;font-weight:600");
      const usd = txt(PX + 220, y + 10, "", "val", g, "end");
      B.prod[p.key] = { r, flow, sub, pill, pillT, usd, y };
    }
  }

  // ---------------------------------------------------------------- status boards (upper left)
  function board(id, x, y, w, h, title, rows) {
    const g = hitGroup(id); g.setAttribute("data-board", "1");
    el("rect", { x, y, width: w, height: h, rx: 7, class: "box" }, g);
    txt(x + 12, y + 20, title, "lbl", g);
    const out = {};
    rows.forEach((r, i) => {
      const ry = y + 42 + i * 22;
      txt(x + 12, ry, r[1], "lbl-s", g);
      if (r[2]) { // bar
        el("rect", { x: x + 84, y: ry - 8, width: w - 172, height: 8, rx: 4, fill: "#1d2a30" }, g);
        const bar = el("rect", { x: x + 84, y: ry - 8, width: 0, height: 8, rx: 4, fill: "#62c6e3" }, g);
        for (const m of r[2].marks || []) { const mx = x + 84 + (w - 172) * (m - r[2].min) / (r[2].max - r[2].min); el("line", { x1: mx, x2: mx, y1: ry - 11, y2: ry + 3, stroke: m === r[2].marks[r[2].marks.length - 1] ? "#ff5b4e" : "#f2c94c", "stroke-width": 1.5 }, g); }
        out[r[0] + "Bar"] = { bar, x: x + 84, w: w - 172, min: r[2].min, max: r[2].max, marks: r[2].marks || [] };
      }
      out[r[0]] = txt(x + w - 12, ry, "", "val", g, "end");
    });
    return out;
  }
  B.bHeat = board("h101", 172, 32, 206, 168, "H-101 FIREBOX", [["fired", "Fired", { min: 0, max: 80, marks: [78.2] }], ["tmt", "Tube metal °C", { min: 380, max: 580, marks: [520, 545] }], ["o2", "Excess O₂"], ["co", "Flue CO"], ["eff", "Efficiency"], ["coke", "Coke layer"]]);
  B.bHyd = board("c101", 388, 32, 206, 168, "C-101 TRAY LOADING", [["top", "Top", { min: 40, max: 110, marks: [90, 100] }], ["mpa", "MPA zone", { min: 40, max: 110, marks: [90, 100] }], ["bpa", "BPA zone", { min: 40, max: 110, marks: [90, 100] }], ["fz", "Flash zone", { min: 40, max: 110, marks: [90, 100] }], ["of", "Overflash"], ["dp", "Column ΔP"]]);
  B.bOH = board("overhead", 604, 32, 206, 168, "OVERHEAD INTEGRITY", [["corr", "Corrosion", { min: 0, max: 30, marks: [10, 20] }], ["ph", "Sour water pH"], ["dew", "Dew margin"], ["hcl", "HCl in OH"], ["qc", "Condenser"], ["drum", "Drum P"]]);
  B.bDes = board("desalter", 172, 214, 206, 146, "DESALTER", [["salt", "Salt out", { min: 0, max: 8, marks: [3] }], ["eff", "Efficiency"], ["bsw", "BS&W out"], ["t", "Temperature"], ["em", "Emulsion"]]);
  B.bVac = board("c201", 388, 214, 206, 146, "VACUUM SYSTEM", [["p", "Top P", { min: 0, max: 120, marks: [30, 60] }], ["pfz", "Flash zone P"], ["ej", "Ejector load"], ["gas", "Cracked gas"], ["cut", "HVGO cut"]]);
  B.bCrude = board("tanks", 604, 214, 206, 146, "CRUDE TO UNIT", [["api", "Gravity"], ["s", "Sulfur"], ["salt", "Salt"], ["met", "Ni + V"], ["px", "Crude price"]]);

  // ---------------------------------------------------------------- selection & tour focus
  let onSelect = () => {};
  let selectedId = null;
  function select(id) {
    svg.querySelectorAll(".hit.sel").forEach((n) => n.classList.remove("sel"));
    selectedId = id;
    if (id) svg.querySelectorAll(`.hit[data-eq="${id}"]`).forEach((n) => n.classList.add("sel"));
    onSelect(id);
  }
  let ring = null;
  function focus(id) {
    if (ring) { ring.remove(); ring = null; }
    if (!id) return null;
    let groups = [...svg.querySelectorAll(`.hit[data-eq="${id}"]:not([data-board])`)];
    if (!groups.length) groups = [...svg.querySelectorAll(`.hit[data-eq="${id}"]`)];
    if (!groups.length) return null;
    let bb = groups.map((gg) => gg.getBBox()).reduce((a, b) => ({ x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), x2: Math.max(a.x2, b.x + b.width), y2: Math.max(a.y2, b.y + b.height) }), { x: 1e9, y: 1e9, x2: -1e9, y2: -1e9 });
    if (id === "pa") bb = { x: 840, y: 70, x2: 940, y2: 420 };
    ring = el("rect", { x: bb.x - 8, y: bb.y - 8, width: bb.x2 - bb.x + 16, height: bb.y2 - bb.y + 16, rx: 10, class: "tour-ring" }, layerTop);
    return ring;
  }

  // ---------------------------------------------------------------- update
  function setBar(o, v, good) {
    const t = Math.max(0, Math.min(1, (v - o.min) / (o.max - o.min)));
    o.bar.setAttribute("width", (o.w * t).toFixed(1));
    const m = o.marks;
    o.bar.setAttribute("fill", m.length && v >= m[m.length - 1] ? "#ff5b4e" : m.length && v >= m[0] ? "#f2c94c" : good || "#62c6e3");
  }
  function cls(t, c) { t.setAttribute("class", "val" + (c ? " " + c : "")); }
  let frame = 0;
  function update(s) {
    const o = s.out, a = s.act, q = s.q;
    frame++;
    // flows
    for (const st of STREAMS) {
      let F = 0, T = 30;
      try { F = Math.max(0, st.flow(o, s)); T = st.temp(o, s); } catch (e) { /* stream not defined in this state */ }
      st.fl.setAttribute("stroke", tcol(T));
      const vis = F > 0.3;
      st.fl.style.visibility = vis ? "visible" : "hidden";
      const dur = vis ? Math.max(0.25, Math.min(6, 60 / F)) : 0;
      if (Math.abs(dur - st.last) > 0.05) { st.fl.style.animationDuration = dur.toFixed(2) + "s"; st.last = dur; }
      st.base.setAttribute("stroke", vis ? "#55666e" : "#3a474d");
    }
    // tanks
    const C = window.CDU.CRUDES, sp = s.sp;
    [[sp.crudeA, 100 - s.blendAct, 100 - sp.blend], [sp.crudeB, s.blendAct, sp.blend]].forEach(([k, pa, ps], i) => {
      const c = C[k];
      B["tankName" + i].textContent = c.short + " " + c.api.toFixed(1) + "°API";
      B["tankPct" + i].textContent = `${f0(pa)} % to unit`;
      B["tankSub" + i].textContent = c.S.toFixed(1) + "% S · " + c.metals + " ppm Ni+V";
      const shade = Math.max(0, Math.min(1, (40 - c.api) / 20));
      B["tankFill" + i].setAttribute("fill", `rgb(${Math.round(70 - shade * 40)},${Math.round(52 - shade * 30)},${Math.round(30 - shade * 18)})`);
    });
    B.p101.setAttribute("fill", s.ev.p101A || s.ev.p101B ? "#58c487" : "#ff5b4e");
    B.tdesIn.textContent = `→ ${f1(o.Tdes)} °C`;
    B.salt.textContent = `salt ${f1(o.saltIn)} → ${f2(s.lag.saltOut)} PTB`;
    B.cit.textContent = `CIT ${f1(a.CIT)} °C`;
    const iface = Math.min(1, 0.4 + o.emulsion * 0.25);
    [0, 1].forEach((i) => { B["dsWater" + i].setAttribute("height", (8 + 8 * iface).toFixed(1)); B["dsWater" + i].setAttribute("y", (430 - 8 * iface).toFixed(1)); B["dsWater" + i].setAttribute("fill", o.emulsion > 1.2 ? "#6b7f5a" : "#2d6e93"); });

    // heaters
    const r1 = s.ev.h1trip ? 0 : a.fired1 / 78;
    B.glow1.setAttribute("opacity", (0.15 + 0.85 * r1).toFixed(2));
    B.flames1.forEach((fl, i) => { const k = r1 * (0.82 + 0.18 * Math.sin(frame * 0.35 + i * 1.7) + 0.08 * Math.random()); fl.setAttribute("transform", `scale(1 ${Math.max(0.02, k).toFixed(2)})`); fl.style.visibility = r1 > 0.02 ? "visible" : "hidden"; });
    B.smoke.style.opacity = (0.3 + r1).toFixed(2);
    B.smoke.setAttribute("transform", `translate(${(Math.sin(frame * 0.05) * 3).toFixed(1)} ${(-(frame % 40) / 8).toFixed(1)})`);
    B.h1trip.textContent = s.ev.h1trip ? "TRIPPED" : "";
    const r2 = s.ev.h2trip ? 0 : a.fired2 / 20.6;
    B.glow2.setAttribute("opacity", (0.15 + 0.85 * r2).toFixed(2));
    B.flames2.forEach((fl, i) => { const k = r2 * (0.82 + 0.18 * Math.sin(frame * 0.4 + i * 2.1) + 0.08 * Math.random()); fl.setAttribute("transform", `scale(1 ${Math.max(0.02, k).toFixed(2)})`); fl.style.visibility = r2 > 0.02 ? "visible" : "hidden"; });
    B.h2trip.textContent = s.ev.h2trip ? "TRIPPED" : "";
    B.cot1.textContent = `${f1(a.COT1)} °C`; B.cot1sp.textContent = `SP ${f1(sp.cot1)}`;
    cls(B.cot1, Math.abs(a.COT1 - sp.cot1) > 3 ? "warn" : "");
    B.cot2.textContent = `${f1(a.COT2)} °C`; B.cot2sp.textContent = `SP ${f1(sp.cot2)}`;
    cls(B.cot2, a.COT2 > 408 ? "warn" : "");

    // column gradient
    const grad = document.getElementById("colGrad");
    if (grad.childNodes.length !== 9) { grad.innerHTML = ""; for (let i = 0; i < 9; i++) el("stop", {}, grad); }
    const prof = o.profile;
    [...grad.childNodes].forEach((st, i) => { const n = Math.round(i * 40 / 8); st.setAttribute("offset", (i / 8).toFixed(3)); st.setAttribute("stop-color", tcol(prof[n])); });
    B.colT.top.textContent = f0(prof[0]) + "°"; B.colT.kero.textContent = f0(prof[9]) + "°"; B.colT.dsl.textContent = f0(prof[21]) + "°";
    B.colT.ago.textContent = f0(prof[31]) + "°"; B.colT.fz.textContent = f0(prof[35]) + "°"; B.colT.bot.textContent = f0(prof[40]) + "°";
    B.floodRing.setAttribute("visibility", o.floodMax > 95 ? "visible" : "hidden");
    const vg = document.getElementById("vacGrad");
    if (vg.childNodes.length !== 3) { vg.innerHTML = ""; for (let i = 0; i < 3; i++) el("stop", {}, vg); }
    [[0, 70], [0.5, 285], [1, o.Tfz2 - 18]].forEach(([off, T], i) => { vg.childNodes[i].setAttribute("offset", off); vg.childNodes[i].setAttribute("stop-color", tcol(T)); });
    B.vacP.textContent = `${f0(o.Pfz2)} mbar`;

    for (const k of ["tpa", "mpa", "bpa"]) B["pa_" + k].textContent = f1(sp[k]) + " MW";
    B.ttop.textContent = `${f1(o.Ttop)} °C`; B.ttopSp.textContent = `SP ${f1(sp.ttop)}`;
    B.fans.forEach((b, i) => b.setAttribute("transform", `rotate(${(frame * (6 + i) * (o.Qcond / 40)) % 360})`));
    B.drumLvl.setAttribute("opacity", "0.45");
    B.stripKERO.textContent = `flash ${f0(q.keroFlash)}°C`;
    B.stripDIESEL.textContent = `T95 ${f0(q.dieselT95)}°C`;
    B.stripAGO.textContent = `colour ${f1(q.agoColor)}`;
    cls(B.stripKERO, q.keroFlash < 38 ? "bad" : ""); cls(B.stripDIESEL, q.dieselT95 > 360 ? "bad" : ""); cls(B.stripAGO, q.agoColor > 4 ? "bad" : "");
    B.ejTxt.textContent = o.ejBroken ? "BROKEN" : `load ${f0(o.ejLoad * 100)} %`;
    cls(B.ejTxt, o.ejBroken ? "bad" : o.ejLoad > 1.1 ? "warn" : "");

    // products
    const V = o.econ.value;
    for (const p of PRODUCTS) {
      const P = B.prod[p.key], v = V[p.key];
      P.flow.textContent = `${f1(v.bpd / 1000)} kBPD  ${f1(s.lag.yields[p.key] * 100)} %`;
      P.sub.textContent = `→ ${v.dest}`;
      const off = v.off;
      const hasSpec = o.specLag[p.key] !== undefined;
      P.pill.style.visibility = hasSpec ? "visible" : "hidden"; P.pillT.style.visibility = hasSpec ? "visible" : "hidden";
      P.pill.setAttribute("fill", off ? "rgba(255,91,78,.2)" : "rgba(88,196,135,.14)");
      P.pillT.textContent = off ? "OFF SPEC" : "ON SPEC"; P.pillT.setAttribute("fill", off ? "#ff5b4e" : "#58c487");
      P.r.setAttribute("class", "chip" + (off ? " off" : ""));
      P.usd.textContent = `$${f0(v.price)}/bbl`;
    }

    // boards
    const bh = B.bHeat;
    bh.fired.textContent = `${f1(a.fired1)} MW`; setBar(bh.firedBar, a.fired1);
    bh.tmt.textContent = `${f0(o.TMT1)} °C`; setBar(bh.tmtBar, o.TMT1); cls(bh.tmt, o.TMT1 > 545 ? "bad" : o.TMT1 > 520 ? "warn" : "");
    bh.o2.textContent = `${f1(sp.o2)} %`; bh.co.textContent = `${f0(o.co)} ppm`; cls(bh.co, o.co > 400 ? "bad" : "");
    bh.eff.textContent = `${f1(o.eff1 * 100)} %`; bh.coke.textContent = `${f2(o.coke1)} mm`;
    const hy = B.bHyd;
    for (const k of ["top", "mpa", "bpa", "fz"]) { hy[k].textContent = `${f0(o.flood[k])} %`; setBar(hy[k + "Bar"], o.flood[k]); cls(hy[k], o.flood[k] > 100 ? "bad" : o.flood[k] > 90 ? "warn" : ""); }
    hy.of.textContent = `${f1(o.overflash)} % LV`; cls(hy.of, o.overflash < 1 ? "bad" : o.overflash < 1.8 ? "warn" : "");
    hy.dp.textContent = `${f2(o.dPcol)} bar`;
    const oh = B.bOH;
    oh.corr.textContent = `${f1(s.lag.corr)} mpy`; setBar(oh.corrBar, s.lag.corr, "#58c487"); cls(oh.corr, s.lag.corr > 20 ? "bad" : s.lag.corr > 10 ? "warn" : "");
    oh.ph.textContent = f1(o.ohpH); cls(oh.ph, o.ohpH < 5.5 || o.ohpH > 7 ? "warn" : "");
    oh.dew.textContent = `${f1(o.dewMargin)} °C`; cls(oh.dew, o.dewMargin < 14 ? "bad" : "");
    oh.hcl.textContent = `${f1(o.hcl)} ppm`; oh.qc.textContent = `${f1(o.Qcond)} / ${f1(o.QcondMax)} MW`; oh.drum.textContent = `${f2(o.drumP)} barg`;
    const ds = B.bDes;
    ds.salt.textContent = `${f2(s.lag.saltOut)} PTB`; setBar(ds.saltBar, s.lag.saltOut, "#58c487"); cls(ds.salt, s.lag.saltOut > 3 ? "bad" : "");
    ds.eff.textContent = `${f1(o.desaltEff * 100)} %`; ds.bsw.textContent = `${f2(o.bsw)} vol%`; cls(ds.bsw, o.bsw > 0.3 ? "bad" : "");
    ds.t.textContent = `${f1(o.Tdes)} °C`; cls(ds.t, o.Tdes < 125 || o.Tdes > 145 ? "warn" : "");
    ds.em.textContent = o.emulsion < 0.9 ? "loose" : o.emulsion < 1.3 ? "normal" : o.emulsion < 1.8 ? "tight" : "very tight"; cls(ds.em, o.emulsion > 1.3 ? "warn" : "");
    const vb = B.bVac;
    vb.p.textContent = `${f1(a.Ptop2)} mbar`; setBar(vb.pBar, a.Ptop2, "#58c487"); cls(vb.p, a.Ptop2 > 60 ? "bad" : a.Ptop2 > 30 ? "warn" : "");
    vb.pfz.textContent = `${f0(o.Pfz2)} mbar`; vb.ej.textContent = `${f0(o.ejLoad * 100)} %`; cls(vb.ej, o.ejBroken ? "bad" : "");
    vb.gas.textContent = `${f0(o.crackGas)} kg/h`; cls(vb.gas, o.crackGas > 250 ? "warn" : "");
    vb.cut.textContent = `${f0(a.cutsV.cHvgo)} °C TBP`;
    const cb = B.bCrude, sl = o.sl;
    cb.api.textContent = `${f1(sl.api)} °API`; cb.s.textContent = `${f2(sl.sulfur)} wt%`; cb.salt.textContent = `${f1(o.saltIn)} PTB`;
    cb.met.textContent = `${f0(sl.metals)} ppm`; cb.px.textContent = `$${f1(sl.price)}/bbl`;
  }

  // board header ids are shared with equipment ids so clicking a board opens that equipment
  window.Mimic = { update, select, focus, onSelect: (fn) => { onSelect = fn; }, get selected() { return selectedId; }, tcol };
})();
