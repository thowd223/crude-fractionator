/* CDU LIVE - advanced process control (real-time optimiser).
 *
 * Every APC cycle (one plant minute) the controller asks the steady-state model what each handle would do if
 * moved one step up or down, and keeps the moves that raise margin without crossing a constraint. Constraints
 * carry a safety margin inside the product specs and equipment limits, as a real APC application does. Moves
 * are rate-limited, so the plant walks towards its constraints instead of jumping.
 */
(function () {
  "use strict";
  const f1 = (x) => (isFinite(x) ? x.toFixed(1) : "–");

  // Controlled / constraint variables: value from a prediction p, APC limit, the spec or hard limit behind it.
  const CONS = [
    { id: "freeze", name: "Kero freeze point", u: "°C", max: -48, hard: -47, sc: 1, v: (p) => p.q.keroFreeze },
    { id: "kflash", name: "Kero flash point", u: "°C", min: 40, hard: 38, sc: 1, v: (p) => p.q.keroFlash },
    { id: "t95", name: "Diesel D86 95 %", u: "°C", max: 357, hard: 360, sc: 1, v: (p) => p.q.dieselT95 },
    { id: "cloud", name: "Diesel cloud point", u: "°C", max: -1, hard: 0, sc: 0.5, v: (p) => p.q.dieselCloud },
    { id: "dflash", name: "Diesel flash point", u: "°C", min: 57, hard: 55, sc: 1, v: (p) => p.q.dieselFlash },
    { id: "hnep", name: "Heavy naphtha end point", u: "°C", max: 187, hard: 190, sc: 1, v: (p) => p.q.hnEP },
    { id: "ago", name: "AGO colour", u: "", max: 3.5, hard: 4, sc: 0.2, v: (p) => p.q.agoColor },
    { id: "metals", name: "HVGO Ni + V", u: "ppm", max: 1.8, hard: 2, sc: 0.1, v: (p) => p.q.hvgoMetals },
    { id: "ccr", name: "HVGO carbon", u: "wt%", max: 0.9, hard: 1, sc: 0.05, v: (p) => p.q.hvgoCCR },
    { id: "of", name: "Overflash", u: "% LV", min: 1.5, hard: 1, sc: 0.3, v: (p) => Math.min(p.o.overflash, p.o.ofRaw) },
    { id: "flood", name: "C-101 tray loading", u: "% flood", max: 92, hard: 100, sc: 2, v: (p) => p.o.floodMax },
    { id: "fired1", name: "H-101 firing", u: "% max", max: 97, hard: 100, sc: 1, v: (p) => (p.fired1 / p.o.firedMax1) * 100 },
    { id: "tmt", name: "H-101 tube metal", u: "°C", max: 515, hard: 545, sc: 4, v: (p) => p.TMT1 },
    { id: "fired2", name: "H-201 firing", u: "% max", max: 97, hard: 100, sc: 1, v: (p) => (p.fired2 / p.o.firedMax2) * 100 },
    { id: "cot2", name: "H-201 outlet (cracking)", u: "°C", max: 405, hard: 410, sc: 1, v: (p) => p.COT2 },
    { id: "ptop", name: "Vacuum top pressure", u: "mbar", max: 25, hard: 30, sc: 1, v: (p) => p.o.Ptop2 },
    { id: "cond", name: "Overhead condensers", u: "% max", max: 96, hard: 100, sc: 1, v: (p) => (p.o.QcondReq / p.o.QcondMax) * 100 },
    { id: "reflux", name: "Top reflux (condenser duty)", u: "MW", min: 10, hard: 6, sc: 1, v: (p) => p.o.QcondReq },
    { id: "dew", name: "Top dew-point margin", u: "°C", min: 16, hard: 14, sc: 1, v: (p) => p.o.dewMargin },
    { id: "corr", name: "Overhead corrosion", u: "mpy", max: 6, hard: 10, sc: 0.5, v: (p) => p.o.corr },
    { id: "salt", name: "Desalted salt", u: "PTB", max: 2, hard: 3, sc: 0.2, v: (p) => p.o.saltOut },
    { id: "bsw", name: "Desalter BS&W", u: "vol%", max: 0.25, hard: 0.3, sc: 0.03, v: (p) => p.o.bsw },
    { id: "tdesH", name: "Desalter temperature", u: "°C", max: 143, hard: 145, sc: 1, v: (p) => p.o.Tdes },
    { id: "tdesL", name: "Desalter temperature", u: "°C", min: 127, hard: 125, sc: 1, v: (p) => p.o.Tdes },
  ];

  // Manipulated variables: step per cycle (move limit) and APC operating range.
  const MVS = [
    { k: "diesel", step: 0.15, lo: 8, hi: 24 }, { k: "kero", step: 0.1, lo: 8, hi: 18 }, { k: "ago", step: 0.15, lo: 0.5, hi: 12 },
    { k: "cot1", step: 0.5, lo: 345, hi: 385 }, { k: "ttop", step: 0.5, lo: 118, hi: 150 },
    { k: "bpa", step: 0.3, lo: 6, hi: 18 }, { k: "mpa", step: 0.3, lo: 6, hi: 18 }, { k: "tpa", step: 0.2, lo: 4, hi: 12 },
    { k: "sBot", step: 0.3, lo: 4, hi: 14 }, { k: "sKero", step: 0.3, lo: 2, hi: 10 }, { k: "sDiesel", step: 0.3, lo: 2, hi: 10 },
    { k: "o2", step: 0.1, lo: 1.5, hi: 3.5 }, { k: "cot2", step: 0.5, lo: 380, hi: 405 },
    { k: "ww", step: 0.2, lo: 3, hi: 8 }, { k: "mixdp", step: 0.05, lo: 0.6, hi: 1.4 }, { k: "demul", step: 0.5, lo: 3, hi: 25 }, { k: "neut", step: 0.05, lo: 0.6, hi: 1.5 },
  ];
  const FEED_MV = { k: "feed", step: 0.3, lo: 70, hi: 112 };
  // Paired moves shift barrels between neighbouring products (one draw up, the next one down).
  const PAIRS = [["diesel", "ago", 0.15], ["kero", "diesel", 0.1], ["kero", "ago", 0.1]];

  function penalty(p) {
    let pen = 0;
    for (const c of CONS) {
      const v = c.v(p); if (!isFinite(v)) continue;
      const viol = c.max !== undefined ? v - c.max : c.min - v;
      if (viol > 0) { const x = viol / c.sc; pen += 60000 * x + 120000 * x * x; }
    }
    return pen;
  }
  const objective = (p) => p.margin - penalty(p);

  function status(p) { // constraint table for display: room to the APC limit as a share of a typical range
    return CONS.map((c) => {
      const v = c.v(p), lim = c.max !== undefined ? c.max : c.min;
      const room = c.max !== undefined ? c.max - v : v - c.min;
      return { id: c.id, name: c.name, u: c.u, v, lim, hard: c.hard, room, kind: c.max !== undefined ? "max" : "min", active: room < c.sc * 0.6, viol: room < 0 };
    });
  }

  class APC {
    constructor(sim) { this.sim = sim; this.on = false; this.pushFeed = false; this.feedMax = 108; this.next = 0; this.moves = []; this.base = null; this.shed = null; this.last = null; }
    enable(on) {
      const s = this.sim;
      this.on = on; this.shed = null;
      if (on) { this.base = s.out.econ.margin; this.baseT = s.t; this.next = s.t; s.log("info", "APC switched on: optimiser in control of 17 handles"); }
      else s.log("info", "APC switched off: handles back to the operator");
    }
    tick() {
      const s = this.sim;
      if (!this.on) return;
      if (s.ev.h1trip || s.ev.h2trip || s.ev.esd || s.act.feed < 60) {
        this.on = false; this.shed = "APC shed to manual: unit not in a normal operating state";
        s.log("trip", this.shed); return;
      }
      if (s.t < this.next) return;
      this.next = s.t + 60;
      this.cycle();
    }
    cycle() {
      const s = this.sim;
      const L = window.CDU.LIMITS;
      let sp = {}; for (const m of MVS) sp[m.k] = s.sp[m.k];
      sp.feed = s.sp.feed;
      let best = s.predict(sp), J = objective(best);
      const start = best.margin;
      const mvs = this.pushFeed ? MVS.concat([Object.assign({}, FEED_MV, { hi: this.feedMax })]) : MVS;
      const moved = [];
      for (const m of mvs) {
        const [hl, hh] = L[m.k];
        const lo = Math.max(m.lo, hl), hi = Math.min(m.hi, hh);
        let bestDir = 0, bestP = null, bestJ = J;
        for (const dir of [1, -1]) {
          const v = +(sp[m.k] + dir * m.step).toFixed(3);
          if (v < lo - 1e-9 || v > hi + 1e-9) continue;
          const trial = Object.assign({}, sp, { [m.k]: v });
          const p = s.predict(trial), j = objective(p);
          if (j > bestJ + 40) { bestJ = j; bestDir = dir; bestP = p; }
        }
        if (bestDir) { const old = sp[m.k]; sp[m.k] = +(sp[m.k] + bestDir * m.step).toFixed(3); best = bestP; J = bestJ; moved.push({ k: m.k, from: old, to: sp[m.k] }); }
      }
      for (const [a, b, st] of PAIRS) {
        let bestDir = 0, bestP = null, bestJ = J;
        for (const dir of [1, -1]) {
          const va = +(sp[a] + dir * st).toFixed(3), vb = +(sp[b] - dir * st).toFixed(3);
          if (va < L[a][0] || va > L[a][1] || vb < L[b][0] || vb > L[b][1]) continue;
          const p = s.predict(Object.assign({}, sp, { [a]: va, [b]: vb })), j = objective(p);
          if (j > bestJ + 40) { bestJ = j; bestDir = dir; bestP = p; }
        }
        if (bestDir) {
          moved.push({ k: a, from: sp[a], to: +(sp[a] + bestDir * st).toFixed(3) }, { k: b, from: sp[b], to: +(sp[b] - bestDir * st).toFixed(3) });
          sp[a] = +(sp[a] + bestDir * st).toFixed(3); sp[b] = +(sp[b] - bestDir * st).toFixed(3); best = bestP; J = bestJ;
        }
      }
      const fin = {}; for (const mv of moved) { if (!fin[mv.k]) fin[mv.k] = { k: mv.k, from: mv.from }; fin[mv.k].to = mv.to; }
      moved.length = 0; for (const k in fin) if (Math.abs(fin[k].to - fin[k].from) > 1e-9) moved.push(fin[k]);
      for (const mv of moved) s.sp[mv.k] = mv.to;
      this.last = { t: s.t, p: best, gain: best.margin - start, moved };
      if (moved.length) { this.moves.unshift({ t: s.t, moved, gain: best.margin - start }); this.moves.length = Math.min(this.moves.length, 12); }
      this.cons = status(best);
    }
    constraints() { return this.cons || status(this.sim.predict()); }
  }

  window.APCmod = { APC, CONS, MVS, status, objective, f1 };
})();
