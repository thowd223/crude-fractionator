/* CDU LIVE - canvas charts: product distribution, TBP slicing, column profile, quality table, margin, trends. */
(function () {
  "use strict";
  const { PRODUCTS, NB, TB, EDGES } = window.CDU;
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const f0 = (x) => (isFinite(x) ? Math.round(x).toLocaleString("en-US") : "–");
  const f1 = (x) => (isFinite(x) ? x.toFixed(1) : "–");

  function fit(c, h) {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const w = c.clientWidth || 300; const H = h || c.clientHeight || 150;
    if (c.width !== Math.round(w * dpr) || c.height !== Math.round(H * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(H * dpr); }
    const g = c.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { g, w, h: H };
  }
  function axes(g, x0, y0, x1, y1, xt, yt, sx, sy, xl, yl) {
    g.strokeStyle = "rgba(255,255,255,.06)"; g.lineWidth = 1; g.fillStyle = css("--mute"); g.font = "11px " + css("--f-data");
    g.textAlign = "center"; g.textBaseline = "top";
    for (const t of xt) { const x = sx(t); g.beginPath(); g.moveTo(x, y0); g.lineTo(x, y1); g.stroke(); g.fillText(t, x, y0 + 5); }
    g.textAlign = "right"; g.textBaseline = "middle";
    for (const t of yt) { const y = sy(t); g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke(); g.fillText(t, x0 - 6, y); }
    g.strokeStyle = "rgba(255,255,255,.18)"; g.beginPath(); g.moveTo(x0, y1); g.lineTo(x0, y0); g.lineTo(x1, y0); g.stroke();
    g.fillStyle = css("--mute"); g.font = "11px " + css("--f-body");
    if (xl) { g.textAlign = "right"; g.textBaseline = "top"; g.fillText(xl, x1, y0 + 20); }
    if (yl) { g.save(); g.translate(x0 - 40, y1); g.rotate(-Math.PI / 2); g.textAlign = "right"; g.textBaseline = "top"; g.fillText(yl, 0, 0); g.restore(); }
  }

  // ---------------------------------------------------------------- the Cuts view
  let root, cDist, cTbp, cProf, tblQ, tblY, cMarg;
  function buildCuts(el) {
    root = el;
    el.innerHTML = `
      <div class="grid2">
        <div class="card"><h3>Where each barrel goes</h3><p class="sub">The crude's boiling range, coloured by the product each molecule ends up in. Overlaps are imperfect fractionation: the tails of neighbouring products share the same boiling range. Dashed lines are the live cut points.</p>
          <canvas class="chart" id="cDist" style="height:300px"></canvas><div class="legend" id="lgDist"></div></div>
        <div class="card"><h3>Product specifications</h3><p class="sub">Analyser values (lag about 15 min) against the limit each customer unit sets. The bar shows how much room is left: a long bar is giveaway.</p>
          <table class="q" id="tblQ"></table></div>
      </div>
      <div class="grid2" style="margin-top:14px">
        <div class="card"><h3>TBP curve, sliced</h3><p class="sub">True boiling point of the crude blend now feeding the unit, cut into products by volume. The faint curve is the design crude.</p>
          <canvas class="chart" id="cTbp" style="height:260px"></canvas></div>
        <div class="card"><h3>C-101 temperature profile</h3><p class="sub">Tray temperatures, live (solid) against the design case (dashed).</p>
          <canvas class="chart" id="cProf" style="height:260px"></canvas></div>
      </div>
      <div class="grid2" style="margin-top:14px">
        <div class="card"><h3>Yields against design</h3><p class="sub">Volume % of crude. Price is what the stream earns at its current destination.</p><table class="q" id="tblY"></table></div>
        <div class="card"><h3>Where the margin comes from</h3><p class="sub">Per day at the current rate. Prices are illustrative and can be changed in the Economics group of the operator panel.</p><canvas class="chart" id="cMarg" style="height:300px"></canvas></div>
      </div>`;
    cDist = el.querySelector("#cDist"); cTbp = el.querySelector("#cTbp"); cProf = el.querySelector("#cProf");
    tblQ = el.querySelector("#tblQ"); tblY = el.querySelector("#tblY"); cMarg = el.querySelector("#cMarg");
    el.querySelector("#lgDist").innerHTML = PRODUCTS.map((p) => `<span><i style="background:${p.color}"></i>${p.name}</span>`).join("");
  }

  function drawDist(s) {
    const { g, w, h } = fit(cDist, 300); g.clearRect(0, 0, w, h);
    const o = s.out, sl = o.sl, sh = o.shares;
    const x0 = 46, x1 = w - 10, y0 = h - 28, y1 = 12;
    const sx = (t) => x0 + (x1 - x0) * (t + 20) / 870;
    let ymax = 0; for (let i = 1; i < NB; i++) ymax = Math.max(ymax, sl.lv[i] * 100);
    ymax = Math.ceil(ymax * 1.15 * 2) / 2;
    const sy = (v) => y0 - (y0 - y1) * v / ymax;
    const yt = []; for (let v = 0; v <= ymax + 1e-6; v += ymax > 2 ? 0.5 : 0.25) yt.push(+v.toFixed(2));
    axes(g, x0, y0, x1, y1, [0, 100, 200, 300, 400, 500, 600, 700, 800], yt, sx, sy, "TBP °C", "vol % per 8 °C");
    // stacked bars per bin
    const bw = Math.max(1, sx(8) - sx(0));
    for (let i = 1; i < NB; i++) {
      let base = 0; const x = sx(EDGES[i - 1]);
      for (const p of PRODUCTS) {
        const v = sl.lv[i] * sh[p.key][i] * 100; if (v <= 1e-5) continue;
        g.fillStyle = p.color; g.globalAlpha = 0.9;
        g.fillRect(x + 0.5, sy(base + v), bw - 1, sy(base) - sy(base + v)); base += v;
      }
    }
    g.globalAlpha = 1;
    // light ends
    let base = 0; for (const p of PRODUCTS) { const v = sl.lv[0] * sh[p.key][0] * 100; if (v > 1e-5) { g.fillStyle = p.color; g.fillRect(sx(-16), sy(base + v / 6), sx(0) - sx(-16) - 1, sy(base) - sy(base + v / 6)); base += v / 6; } }
    // cut lines
    const c = s.act.cuts, cv = s.act.cutsV;
    const cuts = [["HN|KERO", c.c1], ["KERO|DSL", c.c2], ["DSL|AGO", c.c3], ["AGO|AR", c.c4], ["VGO|VR", cv.cHvgo]];
    g.setLineDash([4, 4]); g.strokeStyle = "rgba(255,255,255,.55)"; g.fillStyle = css("--ink"); g.font = "11px " + css("--f-data"); g.textAlign = "center";
    cuts.forEach(([lab, t], i) => { const x = sx(t); g.beginPath(); g.moveTo(x, y0); g.lineTo(x, y1 + 14); g.stroke(); g.fillText(f0(t) + "°", x, y1 + (i % 2 ? 12 : 0)); });
    g.setLineDash([]);
  }

  function drawTbp(s) {
    const { g, w, h } = fit(cTbp, 260); g.clearRect(0, 0, w, h);
    const o = s.out, sl = o.sl;
    const x0 = 46, x1 = w - 10, y0 = h - 28, y1 = 10;
    const sx = (v) => x0 + (x1 - x0) * v / 100, sy = (t) => y0 - (y0 - y1) * (t + 50) / 950;
    axes(g, x0, y0, x1, y1, [0, 20, 40, 60, 80, 100], [0, 200, 400, 600, 800], sx, sy, "cumulative vol % of crude", "TBP °C");
    // product bands
    let cum = 0;
    for (const p of PRODUCTS) {
      const y = s.lag.yields[p.key] * 100;
      g.fillStyle = p.color; g.globalAlpha = 0.18; g.fillRect(sx(cum), y1, sx(cum + y) - sx(cum), y0 - y1);
      g.globalAlpha = 0.95; g.fillRect(sx(cum), y0 - 6, sx(cum + y) - sx(cum) - 1, 6);
      if (y > 4) { g.fillStyle = css("--ink-2"); g.font = "10.5px " + css("--f-data"); g.textAlign = "center"; g.fillText(p.key, sx(cum + y / 2), y0 - 16); }
      cum += y;
    }
    g.globalAlpha = 1;
    const curve = (slate, style, wd) => {
      g.strokeStyle = style; g.lineWidth = wd; g.beginPath();
      for (let i = 0; i <= NB; i++) { const v = slate.cumLV[i] * 100, t = i === 0 ? -20 : (i === 1 ? 36 : EDGES[i - 1]); i ? g.lineTo(sx(v), sy(t)) : g.moveTo(sx(v), sy(t)); }
      g.stroke();
    };
    curve(s.design.sl, "rgba(255,255,255,.25)", 1.5);
    curve(sl, css("--ink"), 2.2);
  }

  function drawProf(s) {
    const { g, w, h } = fit(cProf, 260); g.clearRect(0, 0, w, h);
    const x0 = 46, x1 = w - 10, y0 = h - 28, y1 = 10;
    const sx = (t) => x0 + (x1 - x0) * (t - 100) / 300, sy = (n) => y1 + (y0 - y1) * (n - 1) / 40;
    axes(g, x0, y0, x1, y1, [100, 150, 200, 250, 300, 350, 400], [1, 10, 20, 30, 41], sx, sy, "°C", "tray (1 = top)");
    const line = (p, style, dash) => { g.strokeStyle = style; g.lineWidth = 2.2; g.setLineDash(dash || []); g.beginPath(); p.forEach((T, i) => { i ? g.lineTo(sx(T), sy(i + 1)) : g.moveTo(sx(T), sy(i + 1)); }); g.stroke(); g.setLineDash([]); };
    line(s.design.profile, "rgba(255,255,255,.35)", [5, 4]);
    const p = s.out.profile;
    for (let i = 1; i < p.length; i++) { g.strokeStyle = window.Mimic.tcol(p[i]); g.lineWidth = 3; g.beginPath(); g.moveTo(sx(p[i - 1]), sy(i)); g.lineTo(sx(p[i]), sy(i + 1)); g.stroke(); }
    g.fillStyle = css("--ink-2"); g.font = "11px " + css("--f-body"); g.textAlign = "left";
    for (const [lab, n] of [["kero draw", 10], ["diesel draw", 22], ["AGO draw", 32], ["flash zone", 36]]) { g.fillText(lab, sx(p[n - 1]) + 8, sy(n) + 4); g.beginPath(); g.arc(sx(p[n - 1]), sy(n), 3, 0, 7); g.fill(); }
  }

  const QROWS = [
    ["Heavy naphtha", "D86 end point", "hnEP", "°C", "max", 190, 130],
    ["Kerosene / jet", "Flash point", "keroFlash", "°C", "min", 38, 80],
    ["Kerosene / jet", "Freeze point", "keroFreeze", "°C", "max", -47, -70],
    ["Diesel", "D86 95 % point", "dieselT95", "°C", "max", 360, 280],
    ["Diesel", "Cloud point", "dieselCloud", "°C", "max", 0, -25],
    ["Diesel", "Flash point", "dieselFlash", "°C", "min", 55, 120],
    ["Atm. gas oil", "Colour (ASTM)", "agoColor", "", "max", 4, 0],
    ["Heavy VGO", "Ni + V", "hvgoMetals", "ppm", "max", 2.0, 0],
    ["Heavy VGO", "Conradson carbon", "hvgoCCR", "wt%", "max", 1.0, 0],
  ];
  function drawQ(s) {
    const q = s.q;
    let html = `<tr><th>Product</th><th>Property</th><th style="text-align:right">Now</th><th style="text-align:right">Limit</th><th>Room to limit</th></tr>`;
    for (const [p, prop, k, u, kind, lim, far] of QROWS) {
      const v = q[k];
      const ok = kind === "max" ? v <= lim : v >= lim;
      const room = Math.max(0, Math.min(1, kind === "max" ? (lim - v) / (lim - far) : (v - lim) / (far - lim)));
      const col = !ok ? "var(--alarm)" : room < 0.12 ? "var(--warn)" : "var(--ok)";
      html += `<tr><td>${p}</td><td>${prop}</td><td class="n" style="color:${ok ? "var(--ink)" : "var(--alarm)"}">${k === "hvgoMetals" || k === "hvgoCCR" ? v.toFixed(2) : f1(v)} ${u}</td><td class="n">${kind === "max" ? "≤" : "≥"} ${lim} ${u}</td>
        <td><div class="bar"><span style="width:${(room * 100).toFixed(0)}%;background:${col}"></span></div></td></tr>`;
    }
    tblQ.innerHTML = html;
  }
  function drawY(s) {
    const d = s.design, V = s.out.econ.value;
    let html = `<tr><th>Stream</th><th style="text-align:right">Now</th><th style="text-align:right">Design</th><th style="text-align:right">kBPD</th><th>Destination</th><th style="text-align:right">USD/bbl</th></tr>`;
    for (const p of PRODUCTS) {
      const y = s.lag.yields[p.key] * 100, yd = d.P[p.key].lv * 100, v = V[p.key];
      const dl = y - yd;
      html += `<tr><td><i style="display:inline-block;width:9px;height:9px;border-radius:2px;background:${p.color};margin-right:6px"></i>${p.name}</td>
        <td class="n">${f1(y)} %</td><td class="n" style="color:var(--mute)">${f1(yd)} <span style="color:${Math.abs(dl) < 0.3 ? "var(--mute)" : dl > 0 ? "var(--ok)" : "var(--warn)"}">${dl >= 0 ? "+" : ""}${f1(dl)}</span></td>
        <td class="n">${f1(v.bpd / 1000)}</td><td style="color:${v.off ? "var(--alarm)" : "var(--ink-2)"}">${v.dest}</td><td class="n">${f0(v.price)}</td></tr>`;
    }
    tblY.innerHTML = html;
  }
  function drawMargin(s) {
    const { g, w, h } = fit(cMarg, 300); g.clearRect(0, 0, w, h);
    const e = s.out.econ;
    const rows = PRODUCTS.map((p) => [p.name, e.value[p.key].usd, p.color]).concat([["Crude", -e.crude, "#8a6a52"], ["Fuel gas", -e.fuel, "#ff7a45"], ["Steam", -e.steam, "#9aa5ab"]]);
    const x0 = 120, x1 = w - 70, rowH = (h - 30) / (rows.length + 1);
    const max = Math.max(...rows.map((r) => Math.abs(r[1])));
    const sx = (v) => x0 + (x1 - x0) * Math.abs(v) / max;
    g.font = "11.5px " + css("--f-body"); g.textBaseline = "middle";
    rows.forEach(([n, v, c], i) => {
      const y = 8 + i * rowH;
      g.fillStyle = css("--ink-2"); g.textAlign = "right"; g.fillText(n, x0 - 8, y + rowH / 2);
      g.fillStyle = c; g.globalAlpha = v < 0 ? 0.55 : 0.9; g.fillRect(x0, y + 3, Math.max(1, sx(v) - x0), rowH - 6); g.globalAlpha = 1;
      g.fillStyle = css("--ink"); g.textAlign = "left"; g.font = "11px " + css("--f-data");
      g.fillText((v < 0 ? "−" : "") + "$" + f0(Math.abs(v) / 1000) + "k", sx(v) + 6, y + rowH / 2); g.font = "11.5px " + css("--f-body");
    });
    const y = 8 + rows.length * rowH;
    g.fillStyle = css("--ink"); g.textAlign = "right"; g.font = "600 13px " + css("--f-body"); g.fillText("Margin", x0 - 8, y + rowH / 2);
    g.textAlign = "left"; g.fillStyle = e.margin >= 0 ? css("--ok") : css("--alarm"); g.font = "600 15px " + css("--f-data");
    g.fillText("$" + f0(e.margin / 1000) + "k / day  ·  " + e.perBbl.toFixed(2) + " USD/bbl", x0, y + rowH / 2);
  }
  function updateCuts(s) {
    if (!root || root.hidden) return;
    drawDist(s); drawTbp(s); drawProf(s); drawQ(s); drawY(s); drawMargin(s);
  }

  // ---------------------------------------------------------------- trend strip
  function spark(c, data, key, opts) {
    const { g, w, h } = fit(c);
    g.clearRect(0, 0, w, h);
    if (data.length < 2) return;
    const vals = data.map((d) => d[key]);
    let lo = Math.min(...vals), hi = Math.max(...vals);
    if (opts.lo !== undefined) lo = Math.min(lo, opts.lo);
    if (opts.hi !== undefined) hi = Math.max(hi, opts.hi);
    if (opts.span && hi - lo < opts.span) { const m = (hi + lo) / 2; lo = m - opts.span / 2; hi = m + opts.span / 2; }
    const pad = (hi - lo) * 0.12 || Math.abs(hi) * 0.02 || 1; lo -= pad; hi += pad;
    const t0 = data[0].t, t1 = data[data.length - 1].t;
    const sx = (t) => 2 + (w - 6) * (t - t0) / Math.max(1, t1 - t0), sy = (v) => h - 3 - (h - 6) * (v - lo) / (hi - lo);
    if (opts.limit !== undefined && opts.limit >= lo && opts.limit <= hi) { g.strokeStyle = "rgba(255,91,78,.55)"; g.setLineDash([3, 3]); g.beginPath(); g.moveTo(0, sy(opts.limit)); g.lineTo(w, sy(opts.limit)); g.stroke(); g.setLineDash([]); }
    g.beginPath(); data.forEach((d, i) => { const x = sx(d.t), y = sy(d[key]); i ? g.lineTo(x, y) : g.moveTo(x, y); });
    const col = opts.color || css("--cyan");
    g.strokeStyle = col; g.lineWidth = 1.6; g.stroke();
    g.lineTo(sx(t1), h); g.lineTo(sx(t0), h); g.closePath(); g.globalAlpha = 0.12; g.fillStyle = col; g.fill(); g.globalAlpha = 1;
    const last = data[data.length - 1]; g.fillStyle = col; g.beginPath(); g.arc(sx(last.t), sy(last[key]), 2.6, 0, 7); g.fill();
  }

  window.Charts = { buildCuts, updateCuts, spark };
})();
