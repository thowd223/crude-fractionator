/* CDU LIVE - process model.
 *
 * A reduced-order, real-time model of the 100 kBPSD CDU/VDU. The crude is split into ~110 TBP pseudo-components;
 * every tick the model works out heater duty, flash-zone vaporisation, cut points, fractionation overlap, product
 * yields and qualities, vacuum-column lift, desalting, overhead corrosion, tray loading and the unit margin.
 * At start-up it is calibrated so the design inputs reproduce the FEED heat & material balance in data/*.json.
 * It is a training model: trends and trade-offs are right, absolute numbers are within FEED accuracy.
 */
(function () {
  "use strict";
  const D = window.PLANT.design;
  const BBL = 0.158987;
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const logistic = (x) => 1 / (1 + Math.exp(-x));

  // ---------------------------------------------------------------- crude library (TBP: cum LV %, deg C)
  // Arab Light is the project design assay; the others are representative public-domain style assays.
  const CRUDES = {
    AL: { name: "Arab Light", short: "AL", api: 33.4, S: 1.8, salt: 20, metals: 18, emul: 1.0, price: 72.5,
      note: "Design crude (FEED basis). Medium sour, well-behaved in the desalter.", tbp: D.crude.tbp },
    BR: { name: "North Sea light sweet", short: "NSL", api: 38.3, S: 0.4, salt: 12, metals: 7, emul: 0.8, price: 75.0,
      note: "Light, sweet, rich in naphtha and kero. Loads the top of the column and the overhead condensers.",
      tbp: [[2.3, 36], [5, 52], [10, 88], [20, 135], [30, 185], [40, 235], [50, 288], [60, 345], [70, 410], [80, 485], [85, 530], [90, 595], [95, 675], [100, 820]] },
    AH: { name: "Arab Heavy", short: "AH", api: 27.7, S: 2.8, salt: 30, metals: 75, emul: 1.4, price: 69.0,
      note: "Project check crude. More residue, more sulfur, harder to desalt.",
      tbp: [[1.3, 36], [5, 75], [10, 118], [20, 180], [30, 242], [40, 305], [50, 370], [60, 438], [70, 512], [80, 595], [85, 645], [90, 705], [95, 775], [100, 880]] },
    MY: { name: "Heavy sour (Maya-type)", short: "HSM", api: 21.8, S: 3.4, salt: 45, metals: 320, emul: 2.2, price: 63.0,
      note: "Cheap, heavy, high metals and a stubborn emulsion former. Loads the vacuum unit and the desalter.",
      tbp: [[1.0, 36], [5, 98], [10, 152], [20, 228], [30, 300], [40, 372], [50, 445], [60, 515], [70, 585], [80, 655], [85, 695], [90, 745], [95, 805], [100, 900]] },
  };

  // ---------------------------------------------------------------- product slate and illustrative prices (USD/bbl)
  const PRODUCTS = [
    { key: "LPG", name: "LPG", color: "#b9c7ff", price: 42, to: "LPG treating" },
    { key: "LN", name: "Light naphtha", color: "#8fd3ff", price: 68, to: "Isomerisation" },
    { key: "HN", name: "Heavy naphtha", color: "#5fb8e8", price: 74, to: "NHT / reformer" },
    { key: "KERO", name: "Kerosene / jet", color: "#7fe0b0", price: 103, to: "Kero hydrotreater" },
    { key: "DIESEL", name: "Diesel", color: "#e8d66a", price: 100, to: "Diesel hydrotreater" },
    { key: "AGO", name: "Atm. gas oil", color: "#f0b05a", price: 86, to: "DHT / FCC" },
    { key: "LVGO", name: "Light VGO", color: "#e98e4e", price: 84, to: "Hydrocracker" },
    { key: "HVGO", name: "Heavy VGO", color: "#d9714a", price: 82, to: "FCC / hydrocracker" },
    { key: "SLOP", name: "Slop wax", color: "#b65a44", price: 66, to: "Coker" },
    { key: "VR", name: "Vacuum residue", color: "#7d4a3f", price: 58, to: "Delayed coker" },
  ];
  const PRICES = { fuel_usd_mmbtu: 3.6, steam_usd_t: 18 };
  const OFFSPEC = { // where an off-spec product goes, and its value there
    HN: { to: "slop reprocessing", delta: -6 }, KERO: { to: "diesel pool", priceOf: "DIESEL", delta: -3 },
    DIESEL: { to: "AGO / FCC feed", priceOf: "AGO", delta: 0 }, AGO: { to: "slop reprocessing", delta: -8 },
    HVGO: { to: "coker feed", priceOf: "VR", delta: 5 },
  };

  // ---------------------------------------------------------------- pseudo-component grid
  const EDGES = [36];
  for (let t = 44; t <= 900; t += 8) EDGES.push(t);
  const NB = EDGES.length; // bin 0 is the light-ends lump (C3/C4); bins 1..NB-1 span EDGES
  const TB = new Float64Array(NB);
  TB[0] = -5;
  for (let i = 1; i < NB; i++) TB[i] = (EDGES[i - 1] + EDGES[i]) / 2;

  function monotoneInterp(xs, ys) { // Fritsch-Carlson monotone cubic
    const n = xs.length, dx = [], m = [], d = [];
    for (let i = 0; i < n - 1; i++) { dx[i] = xs[i + 1] - xs[i]; d[i] = (ys[i + 1] - ys[i]) / dx[i]; }
    m[0] = d[0]; m[n - 1] = d[n - 2];
    for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (3 * (dx[i - 1] + dx[i])) / ((2 * dx[i] + dx[i - 1]) / d[i - 1] + (dx[i] + 2 * dx[i - 1]) / d[i]);
    return (x) => {
      if (x <= xs[0]) return ys[0];
      if (x >= xs[n - 1]) return ys[n - 1];
      let i = 0; while (x > xs[i + 1]) i++;
      const h = dx[i], t = (x - xs[i]) / h, t2 = t * t, t3 = t2 * t;
      return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h * m[i + 1];
    };
  }

  function characterise(c) { // -> per-bin LV, SG, S, metals for one crude
    const lvOfT = monotoneInterp(c.tbp.map((p) => p[1]), c.tbp.map((p) => p[0] / 100));
    const lv = new Float64Array(NB);
    lv[0] = c.tbp[0][0] / 100;
    for (let i = 1; i < NB; i++) lv[i] = Math.max(0, lvOfT(EDGES[i]) - lvOfT(EDGES[i - 1]));
    const tot = lv.reduce((a, b) => a + b, 0);
    for (let i = 0; i < NB; i++) lv[i] /= tot;
    const sgT = 141.5 / (c.api + 131.5);
    const sgOf = (K0) => { const sg = new Float64Array(NB); sg[0] = 0.565;
      for (let i = 1; i < NB; i++) { const K = K0 - 0.00025 * (TB[i] - 100); sg[i] = Math.pow((TB[i] + 273.15) * 1.8, 1 / 3) / K; }
      return sg; };
    let lo = 10.5, hi = 13.5, sg;
    for (let k = 0; k < 40; k++) { const K0 = (lo + hi) / 2; sg = sgOf(K0); let s = 0; for (let i = 0; i < NB; i++) s += lv[i] * sg[i]; if (s > sgT) lo = K0; else hi = K0; }
    const K0 = (lo + hi) / 2;
    sg = sgOf(K0);
    const sProf = [[36, 0.01], [100, 0.03], [165, 0.08], [235, 0.35], [320, 1.4], [400, 2.2], [500, 2.7], [600, 3.6], [900, 4.3]];
    const S = new Float64Array(NB), MET = new Float64Array(NB);
    let ms = 0, mt = 0, mm = 0;
    for (let i = 0; i < NB; i++) {
      S[i] = i === 0 ? 0 : interpPairs(sProf, TB[i]);
      MET[i] = TB[i] < 430 ? 0 : Math.exp((TB[i] - 650) / 55);
      const m = lv[i] * sg[i]; ms += m * S[i]; mm += m * MET[i]; mt += m;
    }
    for (let i = 0; i < NB; i++) { S[i] *= c.S / (ms / mt); MET[i] *= c.metals / (mm / mt); }
    return { lv, sg, S, MET, K0 };
  }
  function interpPairs(p, x) {
    if (x <= p[0][0]) return p[0][1];
    for (let i = 1; i < p.length; i++) if (x <= p[i][0]) return lerp(p[i - 1][1], p[i][1], (x - p[i - 1][0]) / (p[i][0] - p[i - 1][0]));
    return p[p.length - 1][1];
  }
  const CHAR = {}; for (const k in CRUDES) CHAR[k] = characterise(CRUDES[k]);

  function blendSlate(a, b, fb) { // volume blend of two crudes
    const A = CHAR[a], B = CHAR[b], lv = new Float64Array(NB), sg = new Float64Array(NB), S = new Float64Array(NB), MET = new Float64Array(NB);
    for (let i = 0; i < NB; i++) {
      const va = A.lv[i] * (1 - fb), vb = B.lv[i] * fb, v = va + vb;
      lv[i] = v;
      const ma = va * A.sg[i], mb = vb * B.sg[i], m = ma + mb;
      sg[i] = v > 0 ? m / v : A.sg[i];
      S[i] = m > 0 ? (ma * A.S[i] + mb * B.S[i]) / m : 0;
      MET[i] = m > 0 ? (ma * A.MET[i] + mb * B.MET[i]) / m : 0;
    }
    const cumLV = new Float64Array(NB + 1), cumM = new Float64Array(NB + 1);
    let mt = 0; for (let i = 0; i < NB; i++) mt += lv[i] * sg[i];
    for (let i = 0; i < NB; i++) { cumLV[i + 1] = cumLV[i] + lv[i]; cumM[i + 1] = cumM[i] + (lv[i] * sg[i]) / mt; }
    const ca = CRUDES[a], cb = CRUDES[b];
    const sgBulk = mt;
    return { lv, sg, S, MET, cumLV, cumM, sgBulk, api: 141.5 / sgBulk - 131.5,
      K: lerp(CHAR[a].K0, CHAR[b].K0, fb), salt: lerp(ca.salt, cb.salt, fb), metals: lerp(ca.metals, cb.metals, fb),
      emul: lerp(ca.emul, cb.emul, fb), price: lerp(ca.price, cb.price, fb), sulfur: lerp(ca.S, cb.S, fb) };
  }
  // cumulative LV (or mass) fraction boiling below T; bin 0 counts as boiling below 36 C
  function cumAt(sl, T, mass) {
    const c = mass ? sl.cumM : sl.cumLV;
    if (T <= EDGES[0]) return c[1] * clamp((T + 45) / 81, 0, 1);
    if (T >= EDGES[NB - 1]) return 1;
    // EDGES[i] is the upper edge of bin i (i>=1); find bin containing T
    let i = 1; while (i < NB - 1 && EDGES[i] < T) i++;
    const lo = EDGES[i - 1], hi = EDGES[i];
    return c[i] + (c[i + 1] - c[i]) * (T - lo) / (hi - lo);
  }
  function tbpAt(sl, f) { // inverse of cumAt (LV basis)
    if (f <= sl.cumLV[1]) return 36;
    let i = 1; while (i < NB - 1 && sl.cumLV[i + 1] < f) i++;
    const c0 = sl.cumLV[i], c1 = sl.cumLV[i + 1];
    return EDGES[i - 1] + (EDGES[i] - EDGES[i - 1]) * (c1 > c0 ? (f - c0) / (c1 - c0) : 0);
  }

  // ---------------------------------------------------------------- correlations
  const D86 = { 10: [0.5564, 1.09], 50: [0.9013, 1.0176], 90: [0.9552, 1.011], 95: [0.9552, 1.011], 99.5: [0.8177, 1.0355] };
  const d86 = (tbp, p) => Math.pow((tbp + 273.15) / D86[p][0], 1 / D86[p][1]) - 273.15; // Riazi-Daubert
  function flashPoint(d86_10) { // API TDB 2B7.1, deg R
    const T = (d86_10 * 1.8 + 32) + 459.67;
    const inv = -0.014568 + 2.84947 / T + 1.903e-3 * Math.log(T);
    return ((1 / inv - 459.67) - 32) / 1.8;
  }
  function aet(Tc, Pmmhg) { // Maxwell-Bonnell: vacuum temperature -> atmospheric equivalent temperature
    const lp = Math.log10(Pmmhg);
    const A = (5.9991972 - 0.9774472 * lp) / (2663.129 - 95.76 * lp);
    const T = Tc + 273.15;
    return (748.1 * A) / (1 / T + 0.3861 * A - 0.00051606) - 273.15;
  }

  // ---------------------------------------------------------------- inputs
  const DES = {
    feed: 100, crudeA: "AL", crudeB: "MY", blend: 0,
    cot1: round1(D.atm.cot), o2: 2.5, ttop: round1(D.atm.T_top),
    kero: 13.0, diesel: 14.7, ago: 7.9,
    tpa: round1(D.atm.pa.TPA.duty_kw / 1000), mpa: round1(D.atm.pa.MPA.duty_kw / 1000), bpa: round1(D.atm.pa.BPA.duty_kw / 1000),
    sBot: 10, sKero: 6, sDiesel: 5.5,
    ww: 5, mixdp: 1.0, demul: 8, neut: 1.0,
    cot2: round1(D.vac.cot), motive: 100,
  };
  function round1(x) { return Math.round(x * 10) / 10; }
  const LIMITS = {
    feed: [55, 115, 0.5, "kBPSD"], blend: [0, 100, 1, "% crude B"], cot1: [330, 395, 0.5, "°C"], o2: [0.5, 6, 0.1, "% O₂"],
    ttop: [110, 160, 0.5, "°C"], kero: [6, 20, 0.1, "% crude"], diesel: [6, 24, 0.1, "% crude"], ago: [0, 14, 0.1, "% crude"],
    tpa: [2, 14, 0.1, "MW"], mpa: [4, 20, 0.1, "MW"], bpa: [4, 20, 0.1, "MW"],
    sBot: [0, 16, 0.5, "lb/bbl"], sKero: [0, 12, 0.5, "lb/bbl"], sDiesel: [0, 12, 0.5, "lb/bbl"],
    ww: [0, 10, 0.1, "% vol"], mixdp: [0.2, 2.2, 0.05, "bar"], demul: [0, 30, 0.5, "ppm"], neut: [0, 2.5, 0.05, "× ratio"],
    cot2: [370, 430, 0.5, "°C"], motive: [30, 110, 1, "% design"],
  };

  // design references (filled by calibrate())
  const REF = {};
  const H1 = D.heaters["H-101"], H2 = D.heaters["H-201"];

  // ---------------------------------------------------------------- the steady-state core
  function vaporTBP(Tfz, sBot) { return Tfz + 13 + 14 * (1 - Math.exp(-sBot / 6)); }

  function heaterQ(sl, m_kgs, CIT, COT, sBot) { // absorbed process duty, MW
    const vfOut = cumAt(sl, vaporTBP(COT - 5, sBot) - REF.vfShift, true);
    const vfIn = cumAt(sl, CIT - 175, true);
    return (m_kgs * (REF.cp1 * (COT - CIT) + REF.lam1 * Math.max(0, vfOut - vfIn))) / 1000;
  }
  function solveCOT(sl, m_kgs, CIT, Qmw, sBot) {
    let lo = CIT, hi = 460;
    if (heaterQ(sl, m_kgs, CIT, lo + 0.01, sBot) >= Qmw) return lo;
    for (let k = 0; k < 28; k++) { const mid = (lo + hi) / 2; if (heaterQ(sl, m_kgs, CIT, mid, sBot) > Qmw) hi = mid; else lo = mid; }
    return (lo + hi) / 2;
  }

  /* Product split. Each boundary has a cut point (TBP) and an overlap width on each side.
   * Share of bin i in product p = (1 - F_{p-1->p heavy}) ... built from cumulative logistic fractions. */
  function splitShares(cuts, sig) { // returns shares[p][i]
    const P = cuts.length + 1, sh = [];
    for (let p = 0; p < P; p++) sh.push(new Float64Array(NB));
    for (let i = 0; i < NB; i++) {
      let prevHeavy = 1; // fraction of bin heavier than boundary p-1
      for (let p = 0; p < P; p++) {
        let heavy = 0;
        if (p < cuts.length) { const s = TB[i] < cuts[p] ? sig[p][1] : sig[p][0]; heavy = logistic((TB[i] - cuts[p]) / Math.max(0.5, s)); heavy = Math.min(heavy, prevHeavy); }
        sh[p][i] = prevHeavy - heavy; prevHeavy = heavy;
      }
    }
    return sh;
  }

  function productProps(sl, share, crudeLVfrac) {
    let v = 0, m = 0, s = 0, met = 0;
    const vols = new Float64Array(NB);
    for (let i = 0; i < NB; i++) { const x = sl.lv[i] * share[i] * crudeLVfrac; vols[i] = x; v += x; const mm = x * sl.sg[i]; m += mm; s += mm * sl.S[i]; met += mm * sl.MET[i]; }
    const pct = (p) => { if (v <= 0) return NaN; let c = 0; const target = (p / 100) * v;
      for (let i = 0; i < NB; i++) { if (c + vols[i] >= target) { const lo = i === 0 ? -20 : EDGES[i - 1], hi = i === 0 ? 36 : EDGES[i]; return lo + (hi - lo) * (vols[i] > 0 ? (target - c) / vols[i] : 0); } c += vols[i]; }
      return EDGES[NB - 1]; };
    return { lv: v, sg: v > 0 ? m / v : 0, S: m > 0 ? s / m : 0, metals: m > 0 ? met / m : 0,
      t5: pct(5), t10: pct(10), t50: pct(50), t90: pct(90), t95: pct(95), t995: pct(99.5), vols };
  }

  function steady(inp, st) {
    // inp: effective (lagged) operating variables; st: persistent state (coke, fouling...). Returns all outputs.
    const sl = st.slate;
    const fr = inp.feedAct / 100;
    const bpsd = inp.feedAct * 1000;
    const m_kgh = (bpsd * BBL / 24) * sl.sgBulk * 999;
    const m_kgs = m_kgh / 3600;
    const o = { fr, bpsd, m_kgh, sl };

    // desalting
    o.Tdes = 30 + 106.4 * Math.pow(Math.max(fr, 0.3), -0.2) + (3.0 * (inp.tpa - REF.tpa)) / Math.max(fr, 0.3);
    const fT = logistic((o.Tdes - 115) / 7);
    const fww = 1 - Math.exp(-inp.ww / 1.6);
    const contact = 1 - Math.exp(-inp.mixdp / 0.3);
    const demulF = 10 / (inp.demul + 2);
    const E = sl.emul * Math.pow(inp.mixdp / 1.1, 3) * demulF * Math.exp(-(o.Tdes - 136) / 30) * (0.6 + 0.08 * inp.ww);
    o.emulsion = E;
    const sep = 1 / (1 + 0.25 * E * E);
    const stageEff = clamp(0.985 * fww * contact * sep * fT, 0, 0.995);
    o.desaltEff = 1 - Math.pow(1 - stageEff, 2);
    o.saltIn = sl.salt * st.saltSpike;
    o.saltOut = o.saltIn * (1 - o.desaltEff);
    o.bsw = 0.06 + 0.12 * E * E + (inp.ww > 8 ? (inp.ww - 8) * 0.05 : 0);

    // preheat: crude inlet temperature to H-101
    const hvgoDelta = (st.vacDutyHVGO || REF.hvgoDuty) - REF.hvgoDuty;
    o.CIT = o.Tdes + 137.6 * Math.pow(Math.max(fr, 0.3), -0.08)
      + (2.3 * ((inp.mpa - REF.mpa) + 0.85 * (inp.bpa - REF.bpa) + 0.6 * hvgoDelta)) / Math.max(fr, 0.3)
      + 18 * (REF.resFrac && st.resFrac ? (st.resFrac / REF.resFrac - 1) : 0) - 30 * st.fouling;

    // H-101: fired duty follows demand, limited by burners and trip state
    o.eff1 = clamp(0.905 - 0.011 * (inp.o2 - 2.5) - 0.06 * Math.exp(-(inp.o2 - 0.3) / 0.3), 0.6, 0.93);
    o.co = 25 + 1800 * Math.exp(-(inp.o2 - 0.3) / 0.28);
    o.Qreq1 = heaterQ(sl, m_kgs, inp.CITact, inp.cot1sp, inp.sBot);
    o.firedReq1 = o.Qreq1 / o.eff1 + REF.ssCoil;
    o.firedMax1 = H1.Q_fired_kw / 1000 * 1.16;

    // atmospheric flash
    o.COT1 = inp.COT1act;
    o.Tfz = o.COT1 - 5;
    o.TBPvap = vaporTBP(o.Tfz, inp.sBot) - REF.vfShift;
    o.vapLV = cumAt(sl, o.TBPvap, false);
    o.vapM = cumAt(sl, o.TBPvap, true);
    o.mVap = o.vapM * m_kgh;

    // heat removal and internal reflux
    o.Qtot = REF.Qtot * (o.mVap / REF.mVap) * (1 + (o.Tfz - REF.Tfz) / 260);
    o.Qpa = inp.tpa + inp.mpa + inp.bpa;
    o.QcondReq = o.Qtot - o.Qpa;
    o.QcondMax = REF.Qcond * 1.3;
    o.Qcond = clamp(o.QcondReq, 0.5, o.QcondMax);
    const IRnk = Math.max(0.05, (o.Qcond + inp.tpa) / (REF.Qcond + REF.tpa));
    const IRkd = Math.max(0.05, (o.Qcond + inp.tpa + inp.mpa) / (REF.Qcond + REF.tpa + REF.mpa));
    const IRda = Math.max(0.05, o.Qtot / REF.Qtot);
    o.IR = { nk: IRnk, kd: IRkd, da: IRda };
    o.Ttop = inp.ttopAct + (o.QcondReq > o.QcondMax ? (o.QcondReq - o.QcondMax) * 1.6 : 0) + (o.QcondReq < 0.5 ? (0.5 - o.QcondReq) * 2.5 : 0);
    o.refluxKgh = D.atm.reflux_kg_h * (o.Qcond / REF.Qcond) * (REF.Ttop > 0 ? 1 : 1);
    o.drumP = D.atm.drum_P_barg + (o.QcondReq > o.QcondMax ? (o.QcondReq - o.QcondMax) * 0.05 : 0);

    // cut points from draws (LV % of crude)
    const c1 = 165 + 1.3 * (o.Ttop - REF.Ttop);
    const f1 = cumAt(sl, c1, false);
    const keroLV = inp.kero / 100, dieselLV = inp.diesel / 100;
    let agoLV = inp.ago / 100;
    const f2 = Math.min(f1 + keroLV, 0.995), c2 = tbpAt(sl, f2);
    const f3 = Math.min(f2 + dieselLV, 0.995), c3 = tbpAt(sl, f3);
    o.overflash = (o.vapLV - (f3 + agoLV)) * 100;
    o.ofRaw = o.overflash; // before the draw-pan limit: what the requested draws leave
    if (o.overflash < 0.2) { agoLV = Math.max(0, o.vapLV - f3 - 0.002); o.agoLimited = true; } else o.agoLimited = false;
    if (f3 > o.vapLV - 0.002) o.dieselLimited = true; else o.dieselLimited = false;
    const f4 = Math.min(f3 + agoLV, 0.998), c4 = tbpAt(sl, f4);
    o.overflash = Math.max(0, (o.vapLV - f4) * 100);

    // tray loading (% of jet flood) for the four critical sections
    const prodAbove = (f) => f; // LV fraction distilled above a section
    const Vtop = 0.55 * (o.Qcond + inp.tpa) / (REF.Qcond + REF.tpa) + 0.45 * prodAbove(f1) / REF.f1;
    const Vmpa = 0.5 * IRkd + 0.5 * f2 / REF.f2;
    const Vbpa = 0.45 * IRda * (o.Qtot - 0.6 * inp.bpa) / (REF.Qtot - 0.6 * REF.bpa) + 0.55 * f3 / REF.f3;
    const Vfz = o.mVap / REF.mVap * (1 + 0.03 * (inp.sBot - 10));
    o.flood = { top: 74 * Vtop * fr / Math.max(fr, 1e-6) * fr / 1, mpa: 76 * Vmpa * fr, bpa: 78 * Vbpa * fr, fz: 70 * Vfz };
    o.flood.top = 74 * Vtop * fr;
    o.floodMax = Math.max(o.flood.top, o.flood.mpa, o.flood.bpa, o.flood.fz);
    const pen = (f) => 1 + Math.pow(Math.max(0, (f - 85) / 15), 2) * 2.2;
    o.dPcol = 0.28 * Math.pow(o.floodMax / 78, 2);

    // overlap widths: [light product's heavy tail, heavy product's light tail]
    const stripK = 0.45 + 0.75 * Math.exp(-inp.sKero / 3);
    const stripD = 0.45 + 0.75 * Math.exp(-inp.sDiesel / 3);
    const s1 = 4.2 * Math.pow(IRnk, -0.75) * pen(o.flood.top);
    const s2 = 5.0 * Math.pow(IRkd, -0.75) * pen(o.flood.mpa);
    const s3 = 6.5 * Math.pow(IRda, -0.75) * pen(o.flood.bpa);
    const s4 = 8 * Math.pow(3 / Math.max(o.overflash, 0.25), 0.45) * pen(o.flood.fz);
    o.sig = { s1, s2, s3, s4 };
    o.cuts = { c0: 80, c1, c2, c3, c4 };

    // vacuum unit
    const resLV = 1 - f4;
    o.resFrac = resLV;
    const arKgh = m_kgh * (1 - cumAt(sl, c4, true));
    o.arKgh = arKgh;
    o.Tbot1 = o.Tfz - 12 + 0.6 * (inp.sBot - 10) * -1;
    o.COT2 = inp.COT2act;
    const crack = Math.exp((o.COT2 - REF.cot2) / 9);
    o.crackGas = D.ejector.offgas * (arKgh / REF.arKgh) * crack;
    o.ejLoad = (D.ejector.stages[0].load_kg_h + (o.crackGas - D.ejector.offgas) * 3.2 + st.airLeak) / D.ejector.stages[0].load_kg_h;
    const cap = Math.max(0.05, inp.motive / 100);
    const x = o.ejLoad / cap;
    o.ejBroken = x > 1.18 || inp.motive < 72;
    o.Ptop2 = o.ejBroken ? 20 * (1.6 + 3.5 * (x - 1.0) + (inp.motive < 72 ? (72 - inp.motive) * 0.35 : 0)) : 20 * (0.82 + 0.18 * x);
    o.Ptop2 = clamp(o.Ptop2, 8, 400);
    // vapour up the column and the bed pressure drop
    const Tfz2 = o.COT2 - 12;
    o.Tfz2 = Tfz2;
    const dPbeds = 40 * Math.pow((arKgh / REF.arKgh) * Math.max(0.3, st.vapRatio2 || 1), 1.6);
    o.Pfz2 = o.Ptop2 + dPbeds;
    const Phc = o.Pfz2 * 0.77 * 0.750062; // mmHg, steam lowers HC partial pressure
    o.aet = aet(Tfz2, Phc);
    o.TBPvac = o.aet + REF.aetOffset;
    const cHvgo = Math.max(c4 + 5, Math.min(o.TBPvac, 640));
    const fV = cumAt(sl, cHvgo, false);
    const slopLV = Math.max(0.004, 0.012 * (arKgh / REF.arKgh) * (1 / Math.max(fr, 0.3)) * fr);
    const fS = Math.min(fV + slopLV, 0.999), cSlop = tbpAt(sl, fS);
    const cLV = Math.max(c4 + 8, 430);
    o.cutsV = { cLV, cHvgo, cSlop };
    const vapAR = Math.max(0, fV - f4) / Math.max(resLV, 1e-6);
    o.vapFracAR = vapAR;
    st.vapRatio2 = REF.vapFracAR ? vapAR / REF.vapFracAR : 1;
    o.vel2 = (arKgh / REF.arKgh) * (vapAR / (REF.vapFracAR || vapAR)) * (REF.Pfz2 / o.Pfz2);
    o.flood2 = 68 * o.vel2;
    o.ent2 = Math.pow(Math.max(o.vel2, 0.1), 3);

    // H-201
    const mAR = arKgh / 3600;
    o.Qreq2 = (mAR * (REF.cp2 * (inp.cot2sp - o.Tbot1) + REF.lam2 * vapAR)) / 1000;
    o.eff2 = H2.eff;
    o.firedReq2 = Math.max(0, o.Qreq2) / o.eff2;
    o.firedMax2 = H2.Q_fired_kw / 1000 * 1.18;

    // product split
    const cutsAll = [c1, c2, c3, c4, cLV, cHvgo, cSlop];
    const sigAll = [
      [s1, s1 * stripK], [s2, s2 * stripD], [s3, s3], [s4, s4],
      [7, 7], [9 * (0.6 + 0.4 * o.ent2), 12], [10, 10]];
    const sh = splitShares(cutsAll, sigAll);
    // naphtha (product 0) splits into LPG (light ends), LN (<80) and HN (>80) in the light-ends section
    const naph = sh[0];
    const shLPG = new Float64Array(NB), shLN = new Float64Array(NB), shHN = new Float64Array(NB);
    for (let i = 0; i < NB; i++) {
      if (i === 0) { shLPG[i] = naph[i] * 0.93; shLN[i] = naph[i] * 0.07; continue; }
      const h = logistic((TB[i] - 80) / 3.2); shLN[i] = naph[i] * (1 - h); shHN[i] = naph[i] * h;
    }
    const shares = { LPG: shLPG, LN: shLN, HN: shHN, KERO: sh[1], DIESEL: sh[2], AGO: sh[3], LVGO: sh[4], HVGO: sh[5], SLOP: sh[6], VR: sh[7] };
    o.shares = shares;
    const P = {};
    for (const pr of PRODUCTS) P[pr.key] = productProps(sl, shares[pr.key], 1);
    o.P = P;

    // qualities
    const q = {};
    const hn = P.HN, ke = P.KERO, di = P.DIESEL, ag = P.AGO, hv = P.HVGO;
    q.hnEP = d86(hn.t995, 99.5);
    q.keroFlash = flashPoint(d86(ke.t10, 10));
    q.keroFreeze = -50 + 0.5 * (ke.t95 - REF.keroT95) + 6 * (sl.K - 11.93);
    q.keroFBP = d86(ke.t995, 99.5);
    q.dieselT95 = d86(di.t95, 95);
    q.dieselFlash = flashPoint(d86(di.t10, 10));
    q.dieselCloud = -12 + 0.34 * (di.t95 - REF.dieselT95) + 7 * (sl.K - 11.93);
    q.agoColor = clamp(1.2 + 6 * Math.exp(-(o.overflash - 0.4) / 0.7) + 2 * Math.max(0, o.flood.fz - 95) / 10, 0.5, 8);
    q.hvgoMetals = P.VR.metals * (0.0015 * o.ent2 + 0.0035 * Math.exp((cHvgo - REF.cHvgo) / 16)) * (hv.lv > 0 ? 1 : 0);
    q.hvgoCCR = 0.25 + 0.25 * Math.exp((cHvgo - REF.cHvgo) / 26) + 0.35 * (o.ent2 - 1 > 0 ? o.ent2 - 1 : 0);
    q.dieselS = di.S;
    o.q = q;
    o.spec = {
      HN: q.hnEP <= 190, KERO: q.keroFlash >= 38 && q.keroFreeze <= -47, DIESEL: q.dieselT95 <= 360 && q.dieselFlash >= 55 && q.dieselCloud <= 0,
      AGO: q.agoColor <= 4, HVGO: q.hvgoMetals <= 2.0 && q.hvgoCCR <= 1.0,
    };

    // column temperature profile (41 trays)
    const T = D.atm.T_draw;
    o.Tkero = T.KERO + 0.85 * (ke.t50 - REF.keroT50);
    o.Tdiesel = T.DIESEL + 0.85 * (di.t50 - REF.dieselT50);
    o.Tago = T.AGO + 0.8 * (o.Tfz - REF.Tfz) + 0.3 * ((ag.t50 || REF.agoT50) - REF.agoT50);
    const pts = [[1, o.Ttop], [3, o.Ttop + 19], [10, o.Tkero], [13, o.Tkero + 20], [22, o.Tdiesel], [25, o.Tdiesel + 12], [32, o.Tago], [35, o.Tfz - 3], [36, o.Tfz], [41, o.Tbot1]];
    o.profile = []; for (let t = 1; t <= 41; t++) o.profile.push(interpPairs(pts, t));

    // overhead corrosion
    const steamTot = inp.sBot * resLV * bpsd / 2.2046 / 24 + inp.sKero * (P.KERO.lv * bpsd) / 2.2046 / 24 + inp.sDiesel * (P.DIESEL.lv * bpsd) / 2.2046 / 24;
    o.steamKgh = steamTot + D.atm.steam.AGO * fr + D.vac.steam * fr;
    o.Tdew = D.atm.T_water_dew + 9 * Math.log(Math.max(0.2, steamTot / REF.steamAtm)) + 4 * (o.drumP - D.atm.drum_P_barg);
    o.dewMargin = o.Ttop - o.Tdew;
    const dewF = o.dewMargin < 14 ? 1 + Math.pow(14 - o.dewMargin, 1.4) * 0.35 : 1;
    const neutF = 1 / (0.25 + 0.75 * Math.min(inp.neut, 1.6));
    o.hcl = 6 * o.saltOut;
    o.corr = 2.4 * Math.pow(Math.max(o.saltOut, 0.05) / REF.saltOut, 0.8) * neutF * dewF;
    o.ohpH = clamp(6.0 + 1.1 * Math.log(Math.max(inp.neut, 0.05)) - 0.4 * Math.log(Math.max(o.saltOut, 0.1) / REF.saltOut), 3.5, 8.5);
    o.saltFouling = inp.neut > 1.6 ? (inp.neut - 1.6) * 2 : 0;

    // economics (USD per day)
    let revenue = 0; const value = {};
    for (const pr of PRODUCTS) {
      const bpd = P[pr.key].lv * bpsd;
      let price = pr.price, dest = pr.to;
      if (o.spec[pr.key] === false && OFFSPEC[pr.key]) {
        const os = OFFSPEC[pr.key];
        price = (os.priceOf ? PRODUCTS.find((x) => x.key === os.priceOf).price : pr.price) + os.delta; dest = os.to;
      }
      value[pr.key] = { bpd, price, usd: bpd * price, dest, off: o.spec[pr.key] === false };
      revenue += bpd * price;
    }
    o.value = value;
    o.crudeCost = bpsd * sl.price;
    o.fuelUSD = 0; // filled after fired duty known (needs actual)
    o.revenue = revenue;
    return o;
  }

  // ---------------------------------------------------------------- dynamic simulator
  const TAU = { feed: 25, blend: 900, CIT: 700, fired: 40, cot: 35, ttop: 240, cuts: 420, qual: 900, salt: 1500, corr: 2400, vac: 90, cot2: 50 };

  class Sim {
    constructor() {
      this.sp = Object.assign({}, DES);
      this.t = 0; // plant seconds since start
      this.speed = 30;
      this.st = { saltSpike: 1, fouling: 0, airLeak: 0, coke1: 1.0, coke2: 0.6, vacDutyHVGO: null, resFrac: null };
      this.ev = { p101: "A", p101A: true, p101B: false, h1trip: false, h2trip: false, esd: false, lowFlowTimer: 0, fgLoss: false };
      this.hist = [];
      this.events = [];
      this.blendAct = this.sp.blend;
      this.slateKey = "";
      this.calibrate();
      this.reset();
    }
    slateFor(fb) {
      const key = this.sp.crudeA + this.sp.crudeB + Math.round(fb * 2) / 2;
      if (key !== this.slateKey) { this.slateKey = key; this.st.slate = blendSlate(this.sp.crudeA, this.sp.crudeB, Math.round(fb * 2) / 200); }
      return this.st.slate;
    }
    calibrate() {
      // Anchor every design ratio to the FEED H&MB at the design inputs on Arab Light.
      const sl = blendSlate("AL", "MY", 0);
      this.st.slate = sl;
      Object.assign(REF, { tpa: DES.tpa, mpa: DES.mpa, bpa: DES.bpa, Ttop: D.atm.T_top, Tfz: D.atm.T_fz, cot2: D.vac.cot,
        Qcond: D.atm.Q_cond_kw / 1000, ssCoil: H1.Q_ss_kw / 1000, hvgoDuty: D.vac.pa.HVGO.duty_kw / 1000 });
      REF.Qtot = REF.Qcond + REF.tpa + REF.mpa + REF.bpa;
      // pick the flash shift so the design flash reproduces design overflash (~2.5 LV%) at the AGO draw
      const fr = 1, m_kgh = (100000 * BBL / 24) * sl.sgBulk * 999;
      const f1 = cumAt(sl, 165, false), f2 = f1 + DES.kero / 100, f3 = f2 + DES.diesel / 100, f4 = f3 + DES.ago / 100;
      const targetVap = f4 + 0.025;
      let lo = -40, hi = 40;
      for (let k = 0; k < 40; k++) { const mid = (lo + hi) / 2; const v = cumAt(sl, vaporTBP(D.atm.T_fz, DES.sBot) - mid, false); if (v > targetVap) lo = mid; else hi = mid; }
      REF.vfShift = (lo + hi) / 2;
      REF.f1 = f1; REF.f2 = f2; REF.f3 = f3;
      REF.mVap = cumAt(sl, vaporTBP(D.atm.T_fz, DES.sBot) - REF.vfShift, true) * m_kgh;
      REF.arKgh = m_kgh * (1 - cumAt(sl, tbpAt(sl, f4), true));
      REF.resFrac = 1 - f4;
      // heater: split design absorbed duty between sensible heat and vaporisation
      const m_kgs = m_kgh / 3600, CIT = D.preheat.CIT, COT = D.atm.cot;
      const vfOut = cumAt(sl, vaporTBP(COT - 5, DES.sBot) - REF.vfShift, true), vfIn = cumAt(sl, CIT - 175, true);
      REF.cp1 = 2.95;
      REF.lam1 = ((H1.Q_proc_kw) - m_kgs * REF.cp1 * (COT - CIT)) / (m_kgs * Math.max(0.05, vfOut - vfIn));
      // vacuum: AET offset so the design flash lifts HVGO to the design cut
      const Phc = D.vac.P_fz_mbar * 0.77 * 0.750062;
      REF.aetOffset = 562 - aet(D.vac.T_fz, Phc);
      REF.Pfz2 = D.vac.P_fz_mbar;
      REF.cHvgo = 562;
      REF.vapFracAR = Math.max(0, cumAt(sl, 562, false) - f4) / (1 - f4);
      REF.cp2 = 2.75;
      const mAR = REF.arKgh / 3600, Tbot = D.atm.T_fz - 12;
      REF.lam2 = (H2.Q_proc_kw - mAR * REF.cp2 * (D.vac.cot - Tbot)) / (mAR * REF.vapFracAR);
      // product-quality anchors, from a first pass at design
      REF.keroT95 = 239; REF.dieselT95 = 326; REF.keroT50 = 201; REF.dieselT50 = 278; REF.agoT50 = 345;
      REF.saltOut = 1; REF.steamAtm = (D.atm.steam.bottom + D.atm.steam.KERO + D.atm.steam.DIESEL);
      const o = steady(this.effInputs(true), this.st);
      REF.keroT95 = o.P.KERO.t95; REF.dieselT95 = o.P.DIESEL.t95; REF.keroT50 = o.P.KERO.t50; REF.dieselT50 = o.P.DIESEL.t50; REF.agoT50 = o.P.AGO.t50;
      REF.saltOut = o.saltOut; REF.steamAtm = o.steamKgh - D.atm.steam.AGO - D.vac.steam;
      this.design = steady(this.effInputs(true), this.st);
    }
    effInputs(design) {
      const s = design ? DES : this.sp, a = this.act || {};
      const pick = (k, dflt) => (design || a[k] === undefined ? dflt : a[k]);
      return Object.assign({}, s, {
        feedAct: pick("feed", s.feed), CITact: pick("CIT", D.preheat.CIT), cot1sp: s.cot1, COT1act: pick("COT1", s.cot1),
        ttopAct: pick("ttop", s.ttop), COT2act: pick("COT2", s.cot2), cot2sp: s.cot2,
      });
    }
    reset() {
      this.sp = Object.assign({}, DES);
      this.t = 0; this.hist = []; this.events = []; this.slateKey = "";
      this.st = Object.assign(this.st, { saltSpike: 1, fouling: 0, airLeak: 0, coke1: 1.0, coke2: 0.6 });
      this.ev = { p101: "A", p101A: true, p101B: false, h1trip: false, h2trip: false, esd: false, lowFlowTimer: 0, fgLoss: false, p112: true };
      this.blendAct = 0;
      this.slateFor(0);
      const d = this.design;
      this.act = { feed: 100, CIT: d.CIT, fired1: d.firedReq1, COT1: D.atm.cot, ttop: D.atm.T_top, fired2: d.firedReq2, COT2: D.vac.cot,
        cuts: Object.assign({}, d.cuts), cutsV: Object.assign({}, d.cutsV), Ptop2: d.Ptop2 };
      this.out = d; this.q = Object.assign({}, d.q); this.lag = { saltOut: d.saltOut, corr: d.corr, yields: {}, margin: null };
      for (const p of PRODUCTS) this.lag.yields[p.key] = d.P[p.key].lv;
      this.cum = { profit: 0, crude: 0, hours: 0 };
      this.step(1);
    }
    flt(key, target, tau, dt, obj) { obj = obj || this.act; const x = obj[key]; obj[key] = x === undefined ? target : x + (target - x) * (1 - Math.exp(-dt / tau)); return obj[key]; }
    log(kind, msg) { this.events.push({ t: this.t, kind, msg }); if (this.events.length > 200) this.events.shift(); }

    step(dt) {
      const sp = this.sp, ev = this.ev, act = this.act;
      this.t += dt;
      // feed: pumps, ESD
      const pumpOK = (ev.p101A || ev.p101B) && !ev.esd;
      const feedTarget = pumpOK ? sp.feed : 0;
      this.flt("feed", feedTarget, pumpOK ? TAU.feed : 8, dt);
      // H-101 low-low pass flow trip (SIF-101): any pass below 40 % of normal for 20 s
      if (!ev.h1trip) {
        if (act.feed < 35) { ev.lowFlowTimer += dt; if (ev.lowFlowTimer > 15) this.trip("h1", "SIF-101 H-101 low-low pass flow: fuel gas SSOVs XV-1021/1022 closed"); }
        else ev.lowFlowTimer = 0;
      }
      if (ev.esd && !ev.h1trip) this.trip("h1", "SIF-901 ESD-1: all unit trip valves closed");
      if (ev.esd && !ev.h2trip) this.trip("h2", "SIF-901 ESD-1: H-201 tripped");
      // blend arrives at the unit with tankage/line lag
      this.blendAct += (sp.blend - this.blendAct) * (1 - Math.exp(-dt / TAU.blend));
      const sl = this.slateFor(this.blendAct);
      this.st.slate = sl;
      // persistent state for coupled terms
      this.st.vacDutyHVGO = this.out ? REF.hvgoDuty * (this.out.P.HVGO.lv / Math.max(this.design.P.HVGO.lv, 1e-6)) : REF.hvgoDuty;
      this.st.resFrac = this.out ? this.out.resFrac : REF.resFrac;
      const inp = this.effInputs(false);
      const o = steady(inp, this.st);
      // CIT
      this.flt("CIT", o.CIT, TAU.CIT, dt);
      // H-101 firing
      const fgOK = !ev.h1trip && !ev.esd;
      const fired1Target = fgOK ? Math.min(o.firedReq1, o.firedMax1 * (ev.fgLoss ? 0.55 : 1)) : 0;
      this.flt("fired1", fired1Target, fgOK ? TAU.fired : 8, dt);
      const Qabs1 = Math.max(0, act.fired1 - REF.ssCoil) * o.eff1;
      const m_kgs = o.m_kgh / 3600;
      const cotTarget = m_kgs > 1 ? solveCOT(sl, m_kgs, act.CIT, Qabs1, sp.sBot) : act.COT1 - 2;
      this.flt("COT1", Math.min(cotTarget, 470), ev.h1trip ? 200 : TAU.cot / Math.max(o.fr, 0.25), dt);
      if (!ev.h1trip && act.COT1 > 392) this.trip("h1", "SIF-106 H-101 high-high COT (TT-1020A/B/C 2oo3): fuel tripped");
      o.limited1 = fgOK && o.firedReq1 > o.firedMax1 * (ev.fgLoss ? 0.55 : 1) * 0.995;
      // H-101 tube metal temperature and coking
      const flux = (0.687 * Qabs1 * 1000) / H1.rad_area * 1.75; // peak kW/m2
      const Rfilm = 1.55 * Math.pow(Math.max(o.fr, 0.25), -0.8);
      o.flux1 = flux;
      o.TMT1 = act.COT1 + flux * (Rfilm + this.st.coke1 / 1.5);
      const Tfilm = (act.COT1 + o.TMT1) / 2;
      this.st.coke1 += dt * (1.0 / (3.15e7)) * Math.exp((Tfilm - 412) / 17) * (ev.h1trip ? 0 : 1);
      o.coke1 = this.st.coke1;
      // column top temperature (TIC-1030 via reflux)
      this.flt("ttop", sp.ttop, TAU.ttop, dt);
      // H-201
      const fg2OK = !ev.h2trip && !ev.esd && act.feed > 25;
      if (!ev.h2trip && act.feed < 25 && this.t > 5) this.trip("h2", "SIF-201 H-201 low-low pass flow: fuel tripped");
      const fired2Target = fg2OK ? Math.min(o.firedReq2, o.firedMax2) : 0;
      this.flt("fired2", fired2Target, fg2OK ? TAU.fired : 8, dt);
      const Qabs2 = act.fired2 * o.eff2;
      const mAR = o.arKgh / 3600;
      const cot2Target = mAR > 0.5 ? o.Tbot1 + (Qabs2 * 1000 - REF.lam2 * mAR * o.vapFracAR) / (mAR * REF.cp2) : o.Tbot1;
      this.flt("COT2", clamp(cot2Target, 200, 470), ev.h2trip ? 200 : TAU.cot2, dt);
      o.limited2 = fg2OK && o.firedReq2 > o.firedMax2 * 0.995;
      o.TMT2 = act.COT2 + 80 * (Qabs2 / (H2.Q_proc_kw / 1000)) * (1 + this.st.coke2 * 0.35) * Math.pow(Math.max(o.fr, 0.25), -0.5);
      this.st.coke2 += dt * (1.0 / (3.15e7)) * Math.exp((act.COT2 - 398) / 10);
      // vacuum pressure dynamics
      this.flt("Ptop2", o.Ptop2, TAU.vac, dt);
      // cut points and qualities with column / analyser lag
      for (const k in o.cuts) this.flt(k, o.cuts[k], TAU.cuts, dt, act.cuts);
      for (const k in o.cutsV) this.flt(k, o.cutsV[k], TAU.cuts, dt, act.cutsV);
      for (const k in o.q) this.flt(k, o.q[k], TAU.qual, dt, this.q);
      this.flt("saltOut", o.saltOut, TAU.salt, dt, this.lag);
      this.flt("corr", o.corr, TAU.corr, dt, this.lag);
      for (const p of PRODUCTS) this.flt(p.key, o.P[p.key].lv, TAU.cuts, dt, this.lag.yields);
      // economics on the lagged yields; off-spec judged on the analyser (lagged) values
      const q = this.q;
      o.specLag = {
        HN: q.hnEP <= 190, KERO: q.keroFlash >= 38 && q.keroFreeze <= -47, DIESEL: q.dieselT95 <= 360 && q.dieselFlash >= 55 && q.dieselCloud <= 0,
        AGO: q.agoColor <= 4, HVGO: q.hvgoMetals <= 2.0 && q.hvgoCCR <= 1.0,
      };
      const bpsd = act.feed * 1000;
      let rev = 0; const value = {};
      for (const pr of PRODUCTS) {
        const bpd = this.lag.yields[pr.key] * bpsd;
        let price = pr.price, dest = pr.to; const off = o.specLag[pr.key] === false;
        if (off && OFFSPEC[pr.key]) { const os = OFFSPEC[pr.key]; price = (os.priceOf ? PRODUCTS.find((x) => x.key === os.priceOf).price : pr.price) + os.delta; dest = os.to; }
        value[pr.key] = { bpd, price, usd: bpd * price, dest, off };
        rev += bpd * price;
      }
      const fuelMW = act.fired1 + act.fired2;
      const fuelUSD = fuelMW * 24 * 3.41214 * PRICES.fuel_usd_mmbtu;
      const steamUSD = (o.steamKgh / 1000) * 24 * PRICES.steam_usd_t + (sp.motive / 100) * (D.ejector.motive_total / 1000) * 24 * PRICES.steam_usd_t;
      const crudeUSD = bpsd * sl.price;
      o.econ = { revenue: rev, crude: crudeUSD, fuel: fuelUSD, steam: steamUSD, margin: rev - crudeUSD - fuelUSD - steamUSD, value };
      o.econ.perBbl = bpsd > 1000 ? o.econ.margin / bpsd : 0;
      this.cum.profit += (o.econ.margin * dt) / 86400;
      this.cum.hours += dt / 3600;
      o.act = act; o.fuelKgh = (act.fired1 + act.fired2) * 1000 * 3.6 / 47.1;
      this.out = o;
      return o;
    }
    trip(which, msg) {
      if (which === "h1") { if (this.ev.h1trip) return; this.ev.h1trip = true; }
      else { if (this.ev.h2trip) return; this.ev.h2trip = true; }
      this.log("trip", msg);
    }
    canReset(which) {
      const a = this.act;
      if (this.ev.esd) return false;
      return which === "h1" ? a.feed > 60 : a.feed > 50;
    }
    resetTrip(which) {
      if (!this.canReset(which)) return false;
      if (which === "h1") { this.ev.h1trip = false; this.ev.lowFlowTimer = 0; this.log("info", "H-101 SIS reset, burners relit (purge complete)"); }
      else { this.ev.h2trip = false; this.log("info", "H-201 SIS reset, burners relit"); }
      return true;
    }
    /* Steady-state prediction at a set of setpoints (current crude at the unit, current coke and fouling).
     * Used by the APC optimiser and the advisor's what-if tool. Does not touch the running simulation. */
    predict(spOverride) {
      const sp = Object.assign({}, this.sp, spOverride || {});
      const st = Object.assign({}, this.st);
      const pumpsOK = (this.ev.p101A || this.ev.p101B) && !this.ev.esd;
      const inp = Object.assign({}, sp, { feedAct: pumpsOK ? sp.feed : this.act.feed, CITact: this.act.CIT, cot1sp: sp.cot1,
        COT1act: sp.cot1, ttopAct: sp.ttop, COT2act: sp.cot2, cot2sp: sp.cot2 });
      let o = steady(inp, st);
      inp.CITact = o.CIT; o = steady(inp, st);
      const m_kgs = o.m_kgh / 3600;
      let fired1 = o.firedReq1, fired2 = o.firedReq2;
      if (o.firedReq1 > o.firedMax1 && m_kgs > 1) {
        fired1 = o.firedMax1;
        inp.COT1act = solveCOT(o.sl, m_kgs, inp.CITact, (fired1 - REF.ssCoil) * o.eff1, sp.sBot);
        o = steady(inp, st); o.limited1 = true;
      }
      if (o.firedReq2 > o.firedMax2) {
        fired2 = o.firedMax2;
        const mAR = o.arKgh / 3600;
        inp.COT2act = o.Tbot1 + (fired2 * o.eff2 * 1000 - REF.lam2 * mAR * o.vapFracAR) / (mAR * REF.cp2);
        o = steady(inp, st); o.limited2 = true;
      }
      const Qabs1 = Math.max(0, fired1 - REF.ssCoil) * o.eff1;
      const flux = (0.687 * Qabs1 * 1000) / H1.rad_area * 1.75;
      const TMT1 = inp.COT1act + flux * (1.55 * Math.pow(Math.max(o.fr, 0.25), -0.8) + this.st.coke1 / 1.5);
      const bpsd = o.bpsd;
      const fuel = (fired1 + fired2) * 24 * 3.41214 * PRICES.fuel_usd_mmbtu;
      const steamUSD = (o.steamKgh / 1000) * 24 * PRICES.steam_usd_t + (sp.motive / 100) * (D.ejector.motive_total / 1000) * 24 * PRICES.steam_usd_t;
      const chem = bpsd * (0.0025 * sp.demul + 0.012 * sp.neut);
      const margin = o.revenue - o.crudeCost - fuel - steamUSD - chem;
      return { o, q: o.q, sp, margin, fuel, steamUSD, fired1, fired2, TMT1, COT1: inp.COT1act, COT2: inp.COT2act, CIT: inp.CITact };
    }
    snapshot() { // for trends
      const o = this.out, a = this.act;
      return { t: this.t, feed: a.feed, cot1: a.COT1, cit: a.CIT, ttop: o.Ttop, fired1: a.fired1, tmt1: o.TMT1, cot2: a.COT2, p2: a.Ptop2 + (o.Pfz2 - o.Ptop2),
        margin: o.econ.margin, diesel: this.lag.yields.DIESEL * 100, kero: this.lag.yields.KERO * 100, flood: o.floodMax, corr: this.lag.corr, salt: this.lag.saltOut, of: o.overflash };
    }
  }

  window.CDU = { Sim, CRUDES, PRODUCTS, PRICES, LIMITS, DES, REF, EDGES, TB, NB, cumAt, tbpAt, d86, flashPoint, aet, blendSlate };
})();
