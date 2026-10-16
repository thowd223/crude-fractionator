// Prints the range envelope for every scenario as JSON (used by verify.py).
// Usage: node search_cli.js [data.json] [extra-scenarios.json]
const fs = require("fs"), HB = require("./model.js");
const data = JSON.parse(fs.readFileSync(process.argv[2] || __dirname + "/example_units.json", "utf8"));
const extra = process.argv[3] ? JSON.parse(fs.readFileSync(process.argv[3], "utf8")) : [];
const M = HB.build(data), P = HB.props(M);
const out = [...data.scenarios, ...extra].map(s => {
  const r = HB.scenarioRange(M, s);
  const w = P.findIndex(p => p.key === "wobbe");
  return { id: s.id, solves: r.solves, props: Object.fromEntries(P.map((p, i) => [p.key, { min: r.min[i].v, typical: r.typical[i], max: r.max[i].v }])),
    wobbe: { bound: r.wobbeBound, certified: [r.min[w].exact, r.max[w].exact], min_case: r.min[w].case, max_case: r.max[w].case } };
});
const normal = HB.evaluate(M, { down: [] });
console.log(JSON.stringify({ normal: { h2s: normal.x[M.idx.H2S] * 1e6, F: normal.F, mw: normal.mw, lhv: normal.lhv, hhv: normal.hhv, wobbe: normal.wobbe, ng: normal.ng, flare: normal.flare, x: normal.x }, scenarios: out }));
