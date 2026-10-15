// Fuel gas header blending engine. No DOM; runs in the browser and in Node.
// Data shape: see example_units.json. Flows kmol/h, heat GJ/h (net), analyses mol%.
(function (root) {
  "use strict";
  const ANALYSES = ["lean", "normal", "rich"];

  function build(data) {
    const b = data.basis, VM = b.molar_volume_nm3_kmol, LAT = b.latent_heat_water_kj_mol;
    const comps = data.components.map(c => ({ ...c, q_net_kj_mol: c.q_gross_kj_mol - c.n_h2o * LAT }));
    const nc = comps.length, idx = Object.fromEntries(comps.map((c, j) => [c.id, j]));
    const norm = a => { const t = a.reduce((s, v) => s + v, 0); return a.map(v => v / t); };
    const qn = comps.map(c => c.q_net_kj_mol), qg = comps.map(c => c.q_gross_kj_mol), mw = comps.map(c => c.mw);
    const qOf = y => y.reduce((s, v, j) => s + v * qn[j], 0); // net kJ/mol
    const units = data.units.map(u => ({ ...u, Y: Object.fromEntries(ANALYSES.map(a => [a, norm(u.analysis_mol_pct[a])])) }));
    // analysis from blend weights {lean, normal, rich}
    const yOf = (u, mix) => { const y = new Array(nc).fill(0); let t = 0;
      for (const a of ANALYSES) { const w = mix[a] || 0; t += w; for (let j = 0; j < nc; j++) y[j] += w * u.Y[a][j]; }
      return y.map(v => v / t); };
    // a packet is one unit at one flow and analysis: component kmol/h, total kmol/h, net heat GJ/h
    const packet = (u, f, mix) => { const y = yOf(u, mix); return { n: y.map(v => f * v), F: f, heat: f * qOf(y) / 1000, f, mix }; };
    // the six corners of a unit's operating range: flow min/max x lean/normal/rich analysis
    for (const u of units) u.corners = [].concat(...["min", "max"].map(fk => ANALYSES.map(a => packet(u, u.flow_kmol_h[fk], { [a]: 1 }))));
    const ngY = norm(data.makeup.analysis_mol_pct), ngQ = qOf(ngY);
    return { data, VM, AIR: b.air_mw, comps, nc, idx, units, ngY, ngQ, qn, qg, mw, packet };
  }

  // Header balance: units that are down produce and consume nothing. If heat from running units
  // is below demand, NG import makes up the difference; if above, the excess is flared and the
  // header composition is unchanged. NG above the import limit is reported, not capped.
  function finish(M, n, F, heat, demand, extra) {
    let ng = 0, flare = 0;
    if (heat < demand) ng = (demand - heat) * 1000 / M.ngQ; else flare = heat - demand;
    const tot = n.slice(); for (let j = 0; j < M.nc; j++) tot[j] += ng * M.ngY[j];
    const Ft = F + ng;
    const x = Ft > 0 ? tot.map(v => v / Ft) : tot.map(() => 0);
    let mwm = 0, lhv = 0, hhv = 0;
    for (let j = 0; j < M.nc; j++) { mwm += x[j] * M.mw[j]; lhv += x[j] * M.qn[j]; hhv += x[j] * M.qg[j]; }
    lhv /= M.VM; hhv /= M.VM;
    const sg = mwm / M.AIR;
    return { x, F: Ft, mw: mwm, sg, lhv, hhv, wobbe: sg > 0 ? hhv / Math.sqrt(sg) : 0,
      supply: heat, demand, ng, ngOverLimit: ng > M.data.makeup.max_kmol_h, flare, ...extra };
  }

  // Evaluate one case: c = { down: [ids], flow: {id: kmol/h}, mix: {id: {lean, normal, rich}} }
  function evaluate(M, c) {
    const down = new Set(c.down || []);
    const n = new Array(M.nc).fill(0); let F = 0, heat = 0, demand = M.data.other_consumers.fuel_use_gj_h;
    const flows = {};
    for (const u of M.units) {
      if (down.has(u.id)) { flows[u.id] = 0; continue; }
      demand += u.fuel_use_gj_h;
      const f = c.flow && c.flow[u.id] != null ? +c.flow[u.id] : u.flow_kmol_h.normal;
      const p = M.packet(u, f, (c.mix && c.mix[u.id]) || { normal: 1 });
      for (let j = 0; j < M.nc; j++) n[j] += p.n[j];
      F += p.F; heat += p.heat; flows[u.id] = f;
    }
    return finish(M, n, F, heat, demand, { flows });
  }

  // Reported properties. kind "ratio": a mole-fraction-weighted average sum_j w_j x_j, which is
  // a ratio of two quantities linear in the unit packets. "ng"/"flare" are linear. Wobbe is neither.
  function props(M) {
    const W = f => M.comps.map(f);
    const ids = (...l) => W(c => l.includes(c.id) ? 100 : 0), grp = g => W(c => c.group === g ? 100 : 0);
    const ratio = (key, label, unit, d, w) => ({ key, label, unit, d, kind: "ratio", w,
      f: r => r.x.reduce((s, v, j) => s + v * w[j], 0) });
    return [
      ratio("h2", "Hydrogen", "mol%", 1, ids("H2")),
      ratio("c1", "Methane", "mol%", 1, ids("CH4")),
      ratio("c2", "C2s (ethane + ethylene)", "mol%", 1, grp("c2")),
      ratio("olef", "Olefins (C2= + C3=)", "mol%", 2, ids("C2H4", "C3H6")),
      ratio("c3", "C3s", "mol%", 1, grp("c3")),
      ratio("c4p", "C4 and heavier", "mol%", 2, ids("C4", "C5+")),
      ratio("inert", "Inerts (N₂ + CO₂)", "mol%", 2, grp("inert")),
      ratio("h2s", "H₂S", "ppmv", 0, W(c => c.id === "H2S" ? 1e6 : 0)),
      ratio("mw", "Molecular weight", "kg/kmol", 2, M.mw),
      ratio("lhv", "LHV (net)", "MJ/Nm³", 2, M.qn.map(q => q / M.VM)),
      ratio("hhv", "HHV (gross)", "MJ/Nm³", 2, M.qg.map(q => q / M.VM)),
      { key: "wobbe", label: "Wobbe index (gross)", unit: "MJ/Nm³", d: 2, kind: "search", f: r => r.wobbe },
      { key: "ng", label: "NG make-up", unit: "kmol/h", d: 0, kind: "ng", f: r => r.ng },
      { key: "flare", label: "Excess gas to flare", unit: "GJ/h", d: 0, kind: "flare", f: r => r.flare },
    ];
  }

  // ---- Exact optimiser -------------------------------------------------------------------
  // Each running unit chooses a convex combination of its six corner packets (any flow in
  // min..max, any blend of lean/normal/rich analysis). Header heat either stays at or below
  // demand (short side: NG make-up, linear in heat) or at or above it (long side: flare, no NG).
  // On each side every "ratio" property is a/b with a and b linear in the packets, so its
  // extreme is a linear-fractional program, solved exactly by Dinkelbach's method. Each step is
  // an LP with one coupling constraint (header heat), solved through its one-variable dual.

  // maximise sum_u val[u][m] over one packet m per unit (convex combinations allowed)
  // subject to sum_u g[u][m] <= G. Returns { t: [[m, weight], ...] per unit } or null.
  function lp1(val, g, G) {
    const k = val.length;
    const pick = mu => val.map((v, u) => { let bm = 0, bv = -Infinity;
      for (let m = 0; m < v.length; m++) { const s = v[m] - mu * g[u][m];
        if (s > bv + 1e-12 || (Math.abs(s - bv) <= 1e-12 && g[u][m] < g[u][bm])) { bv = s; bm = m; } }
      return bm; });
    const load = ch => ch.reduce((s, m, u) => s + g[u][m], 0);
    const minLoad = g.reduce((s, gu) => s + Math.min(...gu), 0);
    if (minLoad > G + 1e-9) return null;                       // side infeasible
    let c0 = pick(0);
    if (load(c0) <= G + 1e-9) return { t: c0.map(m => [[m, 1]]) };
    let lo = 0, hi = 1;
    while (load(pick(hi)) > G + 1e-9) { hi *= 4; if (hi > 1e15) break; }
    for (let it = 0; it < 200 && hi - lo > 1e-14 * Math.max(1, hi); it++) {
      const mid = (lo + hi) / 2; if (load(pick(mid)) > G + 1e-9) lo = mid; else hi = mid;
    }
    const cLo = pick(lo), cHi = pick(hi);                      // cLo over the limit, cHi within it
    const t = cHi.map(m => [[m, 1]]); let L = load(cHi);
    for (let u = 0; u < k && L < G - 1e-12; u++) {             // move toward cLo until heat hits G
      if (cLo[u] === cHi[u]) continue;
      const d = g[u][cLo[u]] - g[u][cHi[u]];
      if (L + d <= G) { t[u] = [[cLo[u], 1]]; L += d; }
      else { const w = (G - L) / d; t[u] = [[cLo[u], w], [cHi[u], 1 - w]]; L = G; }
    }
    return { t };
  }

  function scenarioRange(M, scen, opt = {}) {
    const P = props(M), nc = M.nc;
    const down = new Set(scen.down);
    const run = M.units.filter(u => !down.has(u.id));
    const D = M.data.other_consumers.fuel_use_gj_h + run.reduce((s, u) => s + u.fuel_use_gj_h, 0);
    const PK = run.map(u => u.corners), K = 1000 / M.ngQ;     // kmol NG per GJ shortfall
    let solves = 0;
    const evalT = t => { const n = new Array(nc).fill(0); let F = 0, H = 0;
      t.forEach((ws, u) => ws.forEach(([m, w]) => { const p = PK[u][m];
        for (let j = 0; j < nc; j++) n[j] += w * p.n[j]; F += w * p.F; H += w * p.heat; }));
      return finish(M, n, F, H, D, {}); };
    const sides = [{ s: 1, short: true }, { s: -1, short: false }];  // heat <= D, heat >= D
    // per-packet linear parts on a side: value of sum_j w_j * (component flow incl. NG)
    const lin = (w, side, p) => { let v = 0; for (let j = 0; j < nc; j++) v += w[j] * p.n[j];
      if (side.short) { let wy = 0; for (let j = 0; j < nc; j++) wy += w[j] * M.ngY[j]; v -= p.heat * K * wy; } return v; };
    const tot = (side, p) => p.F - (side.short ? p.heat * K : 0);
    const const_ = (w, side) => { if (!side.short) return [0, 0];
      let wy = 0; for (let j = 0; j < nc; j++) wy += w[j] * M.ngY[j]; return [D * K * wy, D * K]; };
    const solveSide = (side, valFn) => { solves++;
      return lp1(PK.map(ps => ps.map(valFn)), PK.map(ps => ps.map(p => side.s * p.heat)), side.s * D); };
    const extreme = (prop, dir) => {           // dir +1 max, -1 min
      let best = null;
      for (const side of sides) {
        let t;
        if (prop.kind === "ratio") {
          const w = prop.w, [a0, b0] = const_(w, side);
          const A = PK.map(ps => ps.map(p => dir * lin(w, side, p))), B = PK.map(ps => ps.map(p => tot(side, p)));
          const ratioOf = tt => { let a = dir * a0, b = b0; tt.forEach((ws, u) => ws.forEach(([m, x]) => { a += x * A[u][m]; b += x * B[u][m]; })); return a / b; };
          t = solveSide(side, () => 0); if (!t) continue; t = t.t;
          let lam = ratioOf(t);
          for (let it = 0; it < 60; it++) {    // Dinkelbach: max a - lam*b until it reaches 0
            const r = lp1(A.map((au, u) => au.map((a, m) => a - lam * B[u][m])), PK.map(ps => ps.map(p => side.s * p.heat)), side.s * D); solves++;
            const nl = ratioOf(r.t); t = r.t;
            if (nl <= lam + 1e-13 * Math.max(1, Math.abs(lam))) break;
            lam = nl;
          }
        } else if (prop.kind === "ng" || prop.kind === "flare") {
          if ((prop.kind === "ng") !== side.short) { const r = solveSide(side, () => 0); if (!r) continue; t = r.t; }
          else { const r = solveSide(side, p => dir * (prop.kind === "ng" ? -p.heat : p.heat)); if (!r) continue; t = r.t; }
        } else continue;
        const v = prop.f(evalT(t));
        if (!best || dir * v > dir * best.v) best = { v, t };
      }
      return best;
    };
    const caseOf = t => { const c = { down: [...down], flow: {}, mix: {} };
      t.forEach((ws, u) => { let f = 0; const mix = {};
        ws.forEach(([m, w]) => { const p = PK[u][m]; f += w * p.f; for (const a in p.mix) mix[a] = (mix[a] || 0) + w * p.f; });
        for (const a in mix) mix[a] /= f;
        c.flow[run[u].id] = f; c.mix[run[u].id] = mix; });
      return c; };
    const typical = P.map(p => p.f(evaluate(M, { down: [...down] })));
    const lo = [], hi = [];
    const found = [];                          // every optimum found, used to seed the Wobbe search
    P.forEach((p, i) => {
      if (p.kind === "search") return;
      for (const dir of [-1, 1]) { const e = extreme(p, dir); if (!e) continue;
        (dir < 0 ? lo : hi)[i] = { v: e.v, t: e.t, exact: true }; found.push(e.t); }
    });
    // Wobbe: not a linear-fractional property, so search. Start from every optimum found above
    // plus random corners; move one unit at a time to any corner or any balance point (a blend
    // of two of its corners that puts header heat exactly at demand) while Wobbe improves.
    const wi = P.findIndex(p => p.kind === "search"), rand = mulberry32(opt.seed || 12345);
    const k = run.length;
    for (const dir of [-1, 1]) {
      let best = null;
      const starts = found.slice();
      for (let r = 0; r < (opt.random ?? 40); r++) starts.push(run.map((_, u) => [[(rand() * 6) | 0, 1]]));
      for (const s0 of starts) {
        let t = s0.map(ws => ws.map(x => x.slice())), cur = dir * P[wi].f(evalT(t)), improved = true, pass = 0;
        while (improved && pass++ < 30) { improved = false;
          for (let u = 0; u < k; u++) {
            const Hothers = t.reduce((s, ws, v) => v === u ? s : s + ws.reduce((q, [m, w]) => q + w * PK[v][m].heat, 0), 0);
            const opts = [];
            for (let m = 0; m < 6; m++) opts.push([[m, 1]]);
            for (let m1 = 0; m1 < 6; m1++) for (let m2 = m1 + 1; m2 < 6; m2++) {
              const h1 = PK[u][m1].heat, h2 = PK[u][m2].heat, need = D - Hothers;
              if (h1 === h2) continue; const w = (need - h2) / (h1 - h2);
              if (w > 0 && w < 1) opts.push([[m1, w], [m2, 1 - w]]);
            }
            const keep = t[u]; let pick = null;
            for (const o of opts) { t[u] = o; const v = dir * P[wi].f(evalT(t)); if (v > cur + 1e-12) { cur = v; pick = o; } }
            t[u] = pick || keep; if (pick) improved = true;
          }
        }
        if (!best || cur > best.cur) best = { cur, t };
      }
      if (best) (dir < 0 ? lo : hi)[wi] = { v: dir * best.cur, t: best.t, exact: false };
    }
    return { scenario: scen, typical, solves,
      min: lo.map(o => ({ v: o.v, exact: o.exact, case: caseOf(o.t) })),
      max: hi.map(o => ({ v: o.v, exact: o.exact, case: caseOf(o.t) })) };
  }

  function mulberry32(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  const api = { build, evaluate, props, scenarioRange, ANALYSES };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.HeaderBlend = api;
})(typeof window !== "undefined" ? window : globalThis);
