"""Independent check of the header blending engine (model.js).

Written separately in Python from the data file, not translated from the JS.
Run:  python3 verify.py        (needs Node on PATH to run model.js for comparison)

Operating range of each running unit: any flow from min to max, and any blend of its named
analyses (lean / normal / rich in the example data; any number is allowed). Header: heat short of demand is made up with NG; heat above demand
is flared and does not change the composition.

Checks
 1. Single case: normal operation computed here matches model.js (flow, MW, LHV, HHV, Wobbe,
    NG make-up, H2S and every component mole fraction).
 2. Closure, inside every evaluation made here (the Python evaluator, not model.js): mol
    fractions sum to 1, component flows sum to total.
 3. Exhaustive: for test scenarios with 5 running units, evaluate every candidate extreme:
    all 6^5 corners (flow min/max x each analysis) and every balance point (one unit
    blending two of its corners so header heat equals demand exactly, the others at corners).
    Linear-programming theory says the extremes of every property except Wobbe are among
    these points. Compare the true min/max with model.js (pass threshold 1e-6 relative).
    Test sets are chosen so the header crosses from short to long, so balance points exist.
    For Wobbe this only checks that model.js covers these points; its true extreme can lie
    elsewhere (see checks 5 and 6).
 4. Sampled, no theory assumed: for every scenario, random corners, random points anywhere
    inside the range, and random points on the heat-balance boundary (where reachable) must
    all lie within the model.js envelope.
 5. Wobbe interior extremes: two-unit tests where the Wobbe minimum lies inside an edge, not
    at a corner. (a) 95% H2 stream and pure CH4, 10 kmol/h grid refined at 0.25 kmol/h around
    its best point, at a demand that keeps the header long and two that make it cross
    short/long. (b) Pure H2 over a wide flow range with fixed CH4: the case an independent
    review found escaping the earlier Wobbe search. model.js must reach or beat the scan and
    its proven bound must contain it.
 6. Wobbe bound on random synthetic data: datasets of 2-4 units with random flows (some very
    wide or starting at zero) and random analyses (H2-rich, pure H2, mixed). For each,
    model.js's reported Wobbe min/max cases are re-evaluated here (they must be reachable and
    give the reported value), and random points plus fine line scans must stay inside
    model.js's proven Wobbe bound.

Same author, same equations, same property table and assumptions: these checks test that
model.js implements the stated model correctly. They do not test the model against a plant
or a simulator.
"""
import itertools, json, os, random, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "example_units.json")))
VM, AIR, LAT = D["basis"]["molar_volume_nm3_kmol"], D["basis"]["air_mw"], D["basis"]["latent_heat_water_kj_mol"]
C = D["components"]; NC = len(C); IDS = [c["id"] for c in C]
MW = [c["mw"] for c in C]
QG = [c["q_gross_kj_mol"] for c in C]
QN = [c["q_gross_kj_mol"] - c["n_h2o"] * LAT for c in C]
GROUP = [c["group"] for c in C]
UNITS = {u["id"]: u for u in D["units"]}
ALL = [u["id"] for u in D["units"]]
EXT = D["other_consumers"]["fuel_use_gj_h"]

def frac(a):
    t = sum(a); return [v / t for v in a]

Y = {u: {k: frac(v) for k, v in UNITS[u]["analysis_mol_pct"].items()} for u in UNITS}
YNG = frac(D["makeup"]["analysis_mol_pct"])
Q_NG = sum(YNG[j] * QN[j] for j in range(NC))                            # kJ/mol

def demand(down):
    return EXT + sum(UNITS[u]["fuel_use_gj_h"] for u in ALL if u not in down)

def blend(u, w):
    """Analysis for blend weights w = {analysis name: weight}."""
    t = sum(w.values())
    return [sum(x * Y[u][a][j] for a, x in w.items()) / t for j in range(NC)]

def heat(f, y):
    return f * sum(y[j] * QN[j] for j in range(NC)) / 1000              # GJ/h

def header(streams, dem):
    """streams: list of (kmol/h, mol fractions). Returns header properties."""
    n = [0.0] * NC; F = H = 0.0
    for f, y in streams:
        for j in range(NC): n[j] += f * y[j]
        F += f; H += heat(f, y)
    ng = (dem - H) * 1000 / Q_NG if H < dem else 0.0
    flare = H - dem if H >= dem else 0.0
    for j in range(NC): n[j] += ng * YNG[j]
    F += ng
    x = [v / F for v in n]
    assert abs(sum(x) - 1) < 1e-12 and abs(sum(n) - F) < 1e-9 * F, "closure failed"
    mw = sum(x[j] * MW[j] for j in range(NC))
    hhv = sum(x[j] * QG[j] for j in range(NC)) / VM
    s = lambda *ids: 100 * sum(x[IDS.index(i)] for i in ids)
    g = lambda grp: 100 * sum(x[j] for j in range(NC) if GROUP[j] == grp)
    return dict(F=F, x=x, h2=s("H2"), c1=s("CH4"), c2=g("c2"), olef=s("C2H4", "C3H6"), c3=g("c3"),
                c4p=s("C4", "C5+"), inert=g("inert"), h2s=x[IDS.index("H2S")] * 1e6, mw=mw,
                lhv=sum(x[j] * QN[j] for j in range(NC)) / VM, hhv=hhv,
                wobbe=hhv / (mw / AIR) ** 0.5, ng=ng, flare=flare)

def corners(u):
    fl = UNITS[u]["flow_kmol_h"]
    return [(fl[fk], blend(u, {a: 1})) for fk in ("min", "max") for a in Y[u]]

def run_js(extra, data_path=os.path.join(HERE, "example_units.json")):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(extra, f); path = f.name
    out = subprocess.run(["node", os.path.join(HERE, "search_cli.js"), data_path, path],
                         capture_output=True, text=True, check=True).stdout
    os.unlink(path); return json.loads(out)

ok = True
def report(name, passed, detail=""):
    global ok; ok &= passed
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}", flush=True)

# --- exhaustive test sets: 5 running units whose heat range straddles demand ---
rnd = random.Random(7); tests = []
while len(tests) < 3:
    keep = rnd.sample(ALL, 5); down = [u for u in ALL if u not in keep]; dem = demand(down)
    hmin = sum(min(heat(f, y) for f, y in corners(u)) for u in keep)
    hmax = sum(max(heat(f, y) for f, y in corners(u)) for u in keep)
    if hmin < dem < hmax: tests.append(dict(id=f"test{len(tests)}", name="test", down=down))
JS = run_js(tests)
jsS = {s["id"]: s["props"] for s in JS["scenarios"]}
KEYS = list(next(iter(jsS.values())).keys())
SCAL = [k for k in KEYS]

print("1. Normal operation, single case")
py = header([(UNITS[u]["flow_kmol_h"]["normal"], Y[u]["normal"]) for u in ALL], demand([]))
for k in ["F", "mw", "lhv", "hhv", "wobbe", "ng", "h2s"]:
    report(f"{k:6} python {py[k]:10.4f}   model.js {JS['normal'][k]:10.4f}",
           abs(py[k] - JS["normal"][k]) < 1e-6 * max(1, abs(py[k])))
dx = max(abs(a - b) for a, b in zip(py["x"], JS["normal"]["x"]))
report(f"all {NC} component mole fractions", dx < 1e-12, f"largest difference {dx:.1e}")

print("\n2. Closure (sum x = 1, sum n = F) is asserted inside every evaluation below")

print("\n3. Exhaustive candidate extremes vs model.js (5 running units, header crosses short/long)")
for t in tests:
    down = set(t["down"]); keep = [u for u in ALL if u not in down]; dem = demand(down)
    lo = {k: float("inf") for k in KEYS}; hi = {k: float("-inf") for k in KEYS}; count = [0, 0]
    def take(r, b):
        count[b] += 1
        for k in KEYS: lo[k] = min(lo[k], r[k]); hi[k] = max(hi[k], r[k])
    CK = {u: corners(u) for u in keep}
    for combo in itertools.product(*(CK[u] for u in keep)):
        take(header(list(combo), dem), 0)
    for i, ub in enumerate(keep):
        others = keep[:i] + keep[i + 1:]
        for combo in itertools.product(*(CK[u] for u in others)):
            need = dem - sum(heat(f, y) for f, y in combo)
            for (f1, y1), (f2, y2) in itertools.combinations(CK[ub], 2):
                h1, h2 = heat(f1, y1), heat(f2, y2)
                if h1 == h2: continue
                w = (need - h2) / (h1 - h2)
                if 0 < w < 1:
                    f = w * f1 + (1 - w) * f2
                    y = [(w * f1 * a + (1 - w) * f2 * b) / f for a, b in zip(y1, y2)]
                    take(header(list(combo) + [(f, y)], dem), 1)
    js = jsS[t["id"]]; worst, wk = 0.0, ""
    for k in KEYS:
        if k == "wobbe": continue
        for exact, found in ((lo[k], js[k]["min"]), (hi[k], js[k]["max"])):
            gap = abs(exact - found) / max(1.0, abs(exact))
            if gap > worst: worst, wk = gap, k
    report(f"{t['id']} running {','.join(keep)} ({count[0]:,} corners, {count[1]:,} balance points)",
           worst < 1e-6, f"largest gap {worst:.1e} (on {wk})" if wk else "exact match")
    covered = lo["wobbe"] >= js["wobbe"]["min"] - 1e-9 and hi["wobbe"] <= js["wobbe"]["max"] + 1e-9
    report(f"{t['id']} Wobbe: model.js range covers every candidate point", covered,
           f"exhaustive {lo['wobbe']:.4f}-{hi['wobbe']:.4f}, model.js {js['wobbe']['min']:.4f}-{js['wobbe']['max']:.4f}")

print("\n4. Sampled per scenario: 2,000 corners + 2,000 interior + 1,000 on the heat-balance boundary where reachable")
def random_setting(u):
    fl = UNITS[u]["flow_kmol_h"]
    return [fl["min"] + rnd.random() * (fl["max"] - fl["min"]), blend(u, {a: rnd.random() for a in Y[u]})]
def boundary_setting(keep, dem):
    """Random point inside the range, moved in a straight line (component flows interpolated
    unit by unit, which stays inside each unit's range) until header heat equals demand. The
    line goes first toward all-max (or all-min) flow with the same analyses; if that never
    reaches demand, toward each unit's highest-heat (or lowest-heat) corner. None if neither does."""
    for _ in range(50):
        st = [random_setting(u) for u in keep]
        h0 = sum(heat(f, y) for f, y in st); up = h0 < dem
        ends = [[(UNITS[u]["flow_kmol_h"]["max" if up else "min"], y) for u, (_, y) in zip(keep, st)],
                [(max if up else min)(corners(u), key=lambda c: heat(*c)) for u in keep]]
        for end in ends:
            h1 = sum(heat(f, y) for f, y in end)
            if (h1 - dem) * (h0 - dem) > 0 or h1 == h0: continue
            lam = (dem - h0) / (h1 - h0)                 # heat is linear along the line
            out = []
            for (f0, y0), (f1, y1) in zip(st, end):
                n = [(1 - lam) * f0 * a + lam * f1 * b for a, b in zip(y0, y1)]; F = sum(n)
                out.append((F, [v / F for v in n]) if F > 0 else (0.0, y0))
            return out
    return None
for s in D["scenarios"]:
    down = set(s["down"]); keep = [u for u in ALL if u not in down]; dem = demand(down)
    js = jsS[s["id"]]; worst, wk = 0.0, ""
    samples = [header([rnd.choice(corners(u)) for u in keep], dem) for _ in range(2000)]
    samples += [header([random_setting(u) for u in keep], dem) for _ in range(2000)]
    hmin = sum(min(heat(f, y) for f, y in corners(u)) for u in keep)
    hmax = sum(max(heat(f, y) for f, y in corners(u)) for u in keep)
    nb = 0
    if hmin <= dem <= hmax:
        for _ in range(1000):
            st = boundary_setting(keep, dem)
            if st: samples.append(header(st, dem)); nb += 1
        where = f"{nb:,} on boundary"
    else:
        where = "header always " + ("short" if hmax < dem else "long") + ", no boundary"
    for r in samples:
        for k in SCAL:
            if k == "x": continue
            over = max(js[k]["min"] - r[k], r[k] - js[k]["max"], 0) / max(1.0, abs(r[k]))
            if over > worst: worst, wk = over, k
    report(f"{s['name']} ({len(samples):,} samples, {where})", worst < 1e-6,
           "all inside envelope" if worst < 1e-6 else f"sample outside by {worst:.1e} on {wk}")

def synth_run(units, dem):
    """Run model.js on a copy of the data with these units, one all-running scenario and this base demand."""
    s = json.loads(json.dumps(D))
    s["units"] = units; s["scenarios"] = [dict(id="s", name="s", down=[])]; s["other_consumers"]["fuel_use_gj_h"] = dem
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(s, f); sp = f.name
    r = run_js([], sp)["scenarios"][0]; os.unlink(sp); return r

def wobbe_report(name, js, lo, hi):
    """model.js must reach the scanned extremes (lo, hi) and its proven bound must contain them."""
    w, (bl, bh) = js["props"]["wobbe"], js["wobbe"]["bound"]
    reach = w["min"] <= lo + 1e-9 * hi and w["max"] >= hi - 1e-9 * hi
    inside = bl <= lo and hi <= bh
    report(f"{name}: model.js {w['min']:.5f}-{w['max']:.5f}, scan {lo:.5f}-{hi:.5f}, bound {bl:.5f}-{bh:.5f}",
           reach and inside and all(js["wobbe"]["certified"]),
           "model.js reaches the scanned extremes; bound contains them" if reach and inside else
           ("scan beyond model.js" if not reach else "scan outside bound"))

print("\n5. Wobbe interior extremes vs scans")
z = lambda **kw: [kw.get(i.replace("+", "p"), 0) for i in IDS]
two = lambda ya, fa, yb, fb: [dict(id=i, name=i, short=i, fuel_use_gj_h=0, flow_kmol_h=dict(min=fl[0], normal=fl[0], max=fl[1]),
                                   analysis_mol_pct=dict(normal=y)) for i, y, fl in (("a", ya, fa), ("b", yb, fb))]
units = two(z(H2=95, N2=5), (100, 1000), z(CH4=100), (100, 1000))
ya, yb = frac(units[0]["analysis_mol_pct"]["normal"]), frac(units[1]["analysis_mol_pct"]["normal"])
for dem in (50, 400, 700):
    js = synth_run(units, dem)
    wob = lambda fa, fb: header([(fa, ya), (fb, yb)], dem)["wobbe"]
    grid = [(wob(a, b), a, b) for a in range(100, 1001, 10) for b in range(100, 1001, 10)]
    res = []
    for pick in (min, max):
        v, a0, b0 = pick(grid)
        fine = [wob(a0 + i / 4, b0 + j / 4) for i in range(-40, 41) for j in range(-40, 41)
                if 100 <= a0 + i / 4 <= 1000 and 100 <= b0 + j / 4 <= 1000]
        res.append(pick(fine))
    wobbe_report(f"(a) 95% H2 + CH4, demand {dem:>3} GJ/h", js, *res)
units = two(z(H2=100), (300, 10000), z(CH4=100), (100, 100))
ya, yb = frac(units[0]["analysis_mol_pct"]["normal"]), frac(units[1]["analysis_mol_pct"]["normal"])
js = synth_run(units, 100)
scan = [header([(f, ya), (100, yb)], 100)["wobbe"] for f in
        [300 + i * 0.01 for i in range(120001)] + [1500 + i for i in range(8501)]]
wobbe_report("(b) pure H2 300-10,000 + CH4 100 kmol/h, demand 100 (review case)", js, min(scan), max(scan))
w439 = header([(439.9, ya), (100, yb)], 100)["wobbe"]
report(f"(b) review point H2 = 439.9 kmol/h, Wobbe {w439:.5f}, is inside model.js range",
       js["props"]["wobbe"]["min"] <= w439 + 1e-12, f"model.js min {js['props']['wobbe']['min']:.5f}")

print("\n6. Wobbe bound on random synthetic data (40 datasets)")
srnd = random.Random(2024); worst_reach = 0.0; worst_out = -1.0; uncert = 0
def rand_y():
    k = srnd.random(); y = [0.0] * NC
    if k < 0.3: y[IDS.index("H2")] = 50 + 50 * srnd.random(); y[IDS.index("CH4")] = 100 - y[IDS.index("H2")]
    elif k < 0.5: y[IDS.index("H2")] = 100
    else:
        y = [srnd.random() * 30 if srnd.random() < 0.4 else 0.0 for _ in range(NC)]; y[IDS.index("CH4")] += 1
    return y
for case in range(40):
    units = []
    for i in range(srnd.randint(2, 4)):
        lo = 0 if srnd.random() < 0.3 else 10 + 200 * srnd.random()
        hi = lo + srnd.random() * (5000 if srnd.random() < 0.3 else 500)
        an = dict(normal=rand_y())
        if srnd.random() < 0.6: an["rich"] = rand_y()
        if srnd.random() < 0.4: an["lean"] = rand_y()
        units.append(dict(id=f"u{i}", name=f"u{i}", short=f"u{i}", fuel_use_gj_h=0,
                          flow_kmol_h=dict(min=lo, normal=lo, max=hi), analysis_mol_pct=an))
    dem = 1 + 600 * srnd.random()
    js = synth_run(units, dem); w = js["props"]["wobbe"]; bl, bh = js["wobbe"]["bound"]
    if not all(js["wobbe"]["certified"]): uncert += 1
    YS = {u["id"]: {a: frac(v) for a, v in u["analysis_mol_pct"].items()} for u in units}
    def setting(c):
        out = []
        for u in units:
            mix = c["mix"][u["id"]]; t = sum(mix.values())
            out.append((c["flow"][u["id"]], [sum(x * YS[u["id"]][a][j] for a, x in mix.items()) / t for j in range(NC)]))
        return out
    for key, c in (("min", js["wobbe"]["min_case"]), ("max", js["wobbe"]["max_case"])):
        worst_reach = max(worst_reach, abs(header(setting(c), dem)["wobbe"] - w[key]) / w[key])
    def rand_setting():
        out = []
        for u in units:
            fl = u["flow_kmol_h"]; f = fl["min"] + srnd.random() * (fl["max"] - fl["min"])
            if srnd.random() < 0.3: f = srnd.choice((fl["min"], fl["max"]))
            ws = {a: srnd.random() for a in YS[u["id"]]}; t = sum(ws.values())
            out.append((f, [sum(x * YS[u["id"]][a][j] for a, x in ws.items()) / t for j in range(NC)]))
        return out
    pts = [rand_setting() for _ in range(1000)]
    for _ in range(10):                                  # fine line scans between random settings
        a, b = rand_setting(), rand_setting()
        for k in range(201):
            lam = k / 200; st = []
            for (f0, y0), (f1, y1) in zip(a, b):
                n = [(1 - lam) * f0 * p + lam * f1 * q for p, q in zip(y0, y1)]; F = sum(n)
                st.append((F, [v / F for v in n]) if F > 0 else (0.0, y0))
            pts.append(st)
    for st in pts:
        if sum(f for f, _ in st) == 0 and dem == 0: continue
        v = header(st, dem)["wobbe"]
        worst_out = max(worst_out, (bl - v) / bh, (v - bh) / bh)
report("reported Wobbe min/max cases are reachable (re-evaluated here)", worst_reach < 1e-9, f"largest difference {worst_reach:.1e}")
report("no random point or line-scan point outside the proven bound (120,400 points)", worst_out <= 0,
       f"largest excursion {worst_out:.1e} (negative = inside)")
report("every dataset certified (inner and outer Wobbe agree within 1e-9)", uncert == 0, f"{uncert} not certified")

print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
