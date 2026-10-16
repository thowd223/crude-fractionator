// Fuel gas header blending engine. No DOM; runs in the browser and in Node.
// Data shape: see example_units.json. Flows kmol/h, heat GJ/h (net), analyses mol%.
(function (root) {
  "use strict";

  function build(data) {
    const b = data.basis, VM = b.molar_volume_nm3_kmol, LAT = b.latent_heat_water_kj_mol;
    const comps = data.components.map(c => ({ ...c, q_net_kj_mol: c.q_gross_kj_mol - c.n_h2o * LAT }));
    const nc = comps.length, idx = Object.fromEntries(comps.map((c, j) => [c.id, j]));
    const norm = a => { const t = a.reduce((s, v) => s + v, 0); return a.map(v => v / t); };
    const qn = comps.map(c => c.q_net_kj_mol), qg = comps.map(c => c.q_gross_kj_mol), mw = comps.map(c => c.mw);
    const qOf = y => y.reduce((s, v, j) => s + v * qn[j], 0); // net kJ/mol
    // Each unit has any number of named analyses ("normal" required), e.g. lean / normal / rich,
    // or engineer-selected samples such as "max_h2s". Its analysis range is every blend of them.
    const ids = new Set(data.units.map(u => u.id)), problems = [];
    const num = v => typeof v === "number" && isFinite(v);
    // an analysis must have one finite, non-negative value per component and a positive total
    const checkY = (y, what) => {
      if (!Array.isArray(y) || y.length !== nc) return problems.push(`${what} has ${Array.isArray(y) ? y.length : "no"} values, expected ${nc}`);
      if (!y.every(v => num(v) && v >= 0)) return problems.push(`${what} has a missing, negative or non-numeric value`);
      if (!(y.reduce((s, v) => s + v, 0) > 0)) problems.push(`${what} is all zero`);
    };
    for (const c of comps) if (!(num(c.mw) && c.mw > 0 && num(c.q_gross_kj_mol) && c.q_gross_kj_mol >= 0 && num(c.n_h2o) && c.n_h2o >= 0))
      problems.push(`component ${c.id} needs mw > 0, q_gross_kj_mol >= 0 and n_h2o >= 0`);
    for (const u of data.units) {
      if (!u.analysis_mol_pct.normal) problems.push(`unit ${u.id} has no "normal" analysis`);
      for (const [a, y] of Object.entries(u.analysis_mol_pct)) checkY(y, `unit ${u.id} analysis ${a}`);
      const f = u.flow_kmol_h; if (!([f.min, f.normal, f.max].every(num) && f.min >= 0 && f.min <= f.normal && f.normal <= f.max)) problems.push(`unit ${u.id} flow min/normal/max must be numbers with 0 <= min <= normal <= max`);
      if (!(num(u.fuel_use_gj_h) && u.fuel_use_gj_h >= 0)) problems.push(`unit ${u.id} fuel_use_gj_h must be a number >= 0`);
    }
    checkY(data.makeup.analysis_mol_pct, "make-up gas analysis");
    if (!(num(data.makeup.max_kmol_h) && data.makeup.max_kmol_h >= 0)) problems.push("make-up max_kmol_h must be a number >= 0");
    // A positive base demand keeps the header from ever being empty: when no unit gas flows,
    // make-up gas fills it. With zero base demand and every unit down there would be no gas at all.
    if (!(num(data.other_consumers.fuel_use_gj_h) && data.other_consumers.fuel_use_gj_h > 0))
      problems.push("other_consumers fuel_use_gj_h must be a number > 0");
    for (const sc of data.scenarios) for (const d of sc.down)
      if (!ids.has(d)) problems.push(`scenario "${sc.name}" names unknown unit "${d}"`);
    if (problems.length) throw new Error("Data problems: " + problems.join("; "));
    const units = data.units.map(u => ({ ...u, keys: Object.keys(u.analysis_mol_pct),
      Y: Object.fromEntries(Object.entries(u.analysis_mol_pct).map(([a, y]) => [a, norm(y)])) }));
    // analysis from blend weights {lean, normal, rich}
    const yOf = (u, mix) => { const y = new Array(nc).fill(0); let t = 0;
      for (const a of u.keys) { const w = mix[a] || 0; t += w; for (let j = 0; j < nc; j++) y[j] += w * u.Y[a][j]; }
      return t > 0 ? y.map(v => v / t) : u.Y.normal.slice(); };
    // a packet is one unit at one flow and analysis: component kmol/h, total kmol/h, net heat GJ/h
    const packet = (u, f, mix) => { const y = yOf(u, mix); return { n: y.map(v => f * v), F: f, heat: f * qOf(y) / 1000, f, mix }; };
    // corners of a unit's operating range: flow min/max x each named analysis
    for (const u of units) u.corners = [].concat(...["min", "max"].map(fk => u.keys.map(a => packet(u, u.flow_kmol_h[fk], { [a]: 1 }))));
    const ngY = norm(data.makeup.analysis_mol_pct), ngQ = qOf(ngY);
    if (!(ngQ > 0)) throw new Error("Data problems: make-up gas analysis has no net heating value, so it cannot make up a fuel shortfall");
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
    // An empty header (no flow at all) has no composition: report NaN, never zeros that read as a gas.
    // build() rules this out for loaded data by requiring a positive base demand.
    const x = Ft > 0 ? tot.map(v => v / Ft) : tot.map(() => NaN);
    let mwm = 0, lhv = 0, hhv = 0;
    for (let j = 0; j < M.nc; j++) { mwm += x[j] * M.mw[j]; lhv += x[j] * M.qn[j]; hhv += x[j] * M.qg[j]; }
    lhv /= M.VM; hhv /= M.VM;
    const sg = mwm / M.AIR;
    return { x, F: Ft, empty: !(Ft > 0), mw: mwm, sg, lhv, hhv, wobbe: hhv / Math.sqrt(sg),
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

  function scenarioRange(M, scen) {
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
    // maximise dir * sum_j w_j x_j on one side of the heat balance; unit weights, or null if infeasible
    const ratioOpt = (w, dir, side) => {
      const [a0, b0] = const_(w, side);
      const A = PK.map(ps => ps.map(p => dir * lin(w, side, p))), B = PK.map(ps => ps.map(p => tot(side, p)));
      const ratioOf = tt => { let a = dir * a0, b = b0; tt.forEach((ws, u) => ws.forEach(([m, x]) => { a += x * A[u][m]; b += x * B[u][m]; })); return a / b; };
      let t = solveSide(side, () => 0); if (!t) return null; t = t.t;
      let lam = ratioOf(t);
      for (let it = 0; it < 60; it++) {        // Dinkelbach: max a - lam*b until it reaches 0
        const r = lp1(A.map((au, u) => au.map((a, m) => a - lam * B[u][m])), PK.map(ps => ps.map(p => side.s * p.heat)), side.s * D); solves++;
        const nl = ratioOf(r.t);
        if (nl <= lam + 1e-13 * Math.max(1, Math.abs(lam))) { if (nl > lam) t = r.t; break; }
        t = r.t; lam = nl;
      }
      return t;
    };
    const extreme = (prop, dir) => {           // dir +1 max, -1 min
      let best = null;
      for (const side of sides) {
        let t;
        if (prop.kind === "ratio") { t = ratioOpt(prop.w, dir, side); if (!t) continue; }
        else if (prop.kind === "ng" || prop.kind === "flare") {
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
        if (f > 0) for (const a in mix) mix[a] /= f; else { for (const a in mix) delete mix[a]; mix.normal = 1; }
        c.flow[run[u].id] = f; c.mix[run[u].id] = mix; });
      return c; };
    const typical = P.map(p => p.f(evaluate(M, { down: [...down] })));
    const lo = [], hi = [];
    P.forEach((p, i) => {
      if (p.kind === "search") return;
      for (const dir of [-1, 1]) { const e = extreme(p, dir); if (!e) continue;
        (dir < 0 ? lo : hi)[i] = { v: e.v, t: e.t, exact: true }; }
    });
    // Wobbe (gross) = HHV/sqrt(SG) is not linear-fractional, and its extreme can sit inside an
    // edge of the operating range (an H2/CH4 blend has a lower Wobbe than either gas alone), so
    // it is bounded from both sides instead. On each side of the heat balance the reachable
    // (HHV, MW) pairs form a convex set: a linear-fractional image of a polytope. For a direction
    // c, the exact optimiser above gives the point of that set maximising c1*HHV + c2*MW. Those
    // support points span an inner polygon whose every point is a feasible case (the two
    // settings blended); their support lines enclose an outer polygon that contains the whole
    // set. Wobbe = HHV*sqrt(AIR/MW) is quasiconvex in (HHV, MW), so over a polygon its maximum is
    // at a vertex and its minimum on an edge (unimodal along it). Directions are added where
    // inner and outer values differ until they agree within tol/2, tol = 1e-9 x max(1, typical
    // Wobbe), i.e. scaled to the typical value, not to each extreme (tol after the rounding margin
    // below). The reported min/max are feasible cases in the input envelope; the outer values are
    // a numerically certified bound (wobbeBound): the construction is a bound, but it is computed
    // in floating point with a fixed margin, not interval arithmetic.
    const wi = P.findIndex(p => p.kind === "search"), iH = P.findIndex(p => p.key === "hhv"), iM = P.findIndex(p => p.key === "mw");
    const golden = fn => { const g = (Math.sqrt(5) - 1) / 2; let a = 0, b = 1, x1 = b - g, x2 = g, f1 = fn(x1), f2 = fn(x2);
      for (let it = 0; it < 90; it++) {
        if (f1 < f2) { b = x2; x2 = x1; f2 = f1; x1 = b - g * (b - a); f1 = fn(x1); }
        else { a = x1; x1 = x2; f1 = f2; x2 = a + g * (b - a); f2 = fn(x2); } }
      return [[0, fn(0)], [1, fn(1)], [x1, f1], [x2, f2]].reduce((p, q) => q[1] < p[1] ? q : p); };
    const wob = (h, m) => h * Math.sqrt(M.AIR / m);
    const blendT = (ta, tb, mu) => ta.map((ws, u) => [...ws.map(([m, x]) => [m, (1 - mu) * x]), ...tb[u].map(([m, x]) => [m, mu * x])]);
    let wobbeBound = null;
    if (lo[iH]) {
      const sH = Math.max(hi[iH].v - lo[iH].v, 1e-6 * Math.abs(hi[iH].v), 1e-9);
      const sM = Math.max(hi[iM].v - lo[iM].v, 1e-6 * Math.abs(hi[iM].v), 1e-9);
      const tol = 1e-9 * Math.max(1, typical[wi]);
      const support = (side, th) => {
        const c1 = Math.cos(th) / sH, c2 = Math.sin(th) / sM;   // direction in scaled (HHV, MW)
        const t = ratioOpt(M.qg.map((q, j) => c1 * q / M.VM + c2 * M.mw[j]), 1, side); if (!t) return null;
        const r = evalT(t);
        return { th, t, h: r.hhv, m: r.mw, x: r.hhv / sH, y: r.mw / sM, W: r.wobbe };
      };
      const span = (A, B) => {                 // the boundary between neighbouring support points
        // outer vertex v: walk along A's support line until B's is reached. Written as
        // n_B.(B - A) / sin(angle) so nearly parallel lines (fine angles near a flat face) stay
        // accurate; a plain 2x2 solve loses digits as the angle shrinks.
        const bx = B.x - A.x, by = B.y - A.y, same = Math.hypot(bx, by) < 1e-12;
        const sn = Math.sin((B.th - A.th + 2 * Math.PI) % (2 * Math.PI));
        const tau = same || !(sn > 0) ? 0 : (Math.cos(B.th) * bx + Math.sin(B.th) * by) / sn;
        const v = { h: (A.x - tau * Math.sin(A.th)) * sH, m: (A.y + tau * Math.cos(A.th)) * sM };
        const iv = { A, B, v };
        if (!(v.m > 0 && v.h >= 0)) { iv.outMax = Infinity; iv.outMin = -Infinity; }
        else { const seg = (p, q) => golden(s => wob(p.h + s * (q.h - p.h), p.m + s * (q.m - p.m)))[1];
          iv.outMax = Math.max(A.W, B.W, wob(v.h, v.m)); iv.outMin = same ? Math.min(A.W, B.W) : Math.min(seg(A, v), seg(v, B)); }
        const r = same ? (A.W <= B.W ? [0, A.W] : [1, B.W]) : golden(mu => evalT(blendT(A.t, B.t, mu)).wobbe);
        iv.inMin = { v: r[1], t: blendT(A.t, B.t, r[0]) };
        return iv;
      };
      const solveSideW = side => {
        const pts = [0, 1, 2, 3, 4, 5, 6, 7].map(i => support(side, i * Math.PI / 4));
        if (pts.some(p => !p)) return null;
        let ivs = pts.map((A, i) => span(A, pts[(i + 1) % 8])), dirs = 8;
        for (;;) {
          let iMax = 0, iMin = 0;
          ivs.forEach((iv, i) => { if (iv.outMax > ivs[iMax].outMax) iMax = i; if (iv.outMin < ivs[iMin].outMin) iMin = i; });
          const inMax = ivs.reduce((b, iv) => [iv.A, iv.B].reduce((p, q) => q.W > p.W ? q : p, b), ivs[0].A);
          const inMin = ivs.reduce((b, iv) => iv.inMin.v < b.v ? iv.inMin : b, ivs[0].inMin);
          const res = { max: { v: inMax.W, t: inMax.t }, min: inMin, bound: [ivs[iMin].outMin, ivs[iMax].outMax], dirs };
          const split = [...new Set([res.bound[1] - inMax.W > tol / 2 ? iMax : -1, inMin.v - res.bound[0] > tol / 2 ? iMin : -1])]
            .filter(i => i >= 0 && ((ivs[i].B.th - ivs[i].A.th + 2 * Math.PI) % (2 * Math.PI)) > 1e-10).sort((a, b) => b - a);
          if (!split.length || dirs >= 600) return res;
          for (const i of split) { const { A, B } = ivs[i];
            const C = support(side, A.th + ((B.th - A.th + 2 * Math.PI) % (2 * Math.PI)) / 2); dirs++;
            ivs.splice(i, 1, span(A, C), span(C, B)); }
        }
      };
      for (const side of sides) { const r = solveSideW(side); if (!r) continue;
        if (!lo[wi] || r.min.v < lo[wi].v) lo[wi] = { v: r.min.v, t: r.min.t };
        if (!hi[wi] || r.max.v > hi[wi].v) hi[wi] = { v: r.max.v, t: r.max.t };
        wobbeBound = wobbeBound ? [Math.min(wobbeBound[0], r.bound[0]), Math.max(wobbeBound[1], r.bound[1])] : r.bound; }
      wobbeBound = [wobbeBound[0] * (1 - 1e-11), wobbeBound[1] * (1 + 1e-11)];   // floating-point margin
      lo[wi].exact = lo[wi].v - wobbeBound[0] <= tol; hi[wi].exact = wobbeBound[1] - hi[wi].v <= tol;
    }
    return { scenario: scen, typical, solves, wobbeBound,
      min: lo.map(o => ({ v: o.v, exact: o.exact, case: caseOf(o.t) })),
      max: hi.map(o => ({ v: o.v, exact: o.exact, case: caseOf(o.t) })) };
  }

  const api = { build, evaluate, props, scenarioRange };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.HeaderBlend = api;
})(typeof window !== "undefined" ? window : globalThis);
