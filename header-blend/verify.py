"""Independent check of the header blending engine (model.js).

Written separately in Python from the data file, not translated from the JS.
Run:  python3 verify.py        (needs Node on PATH to run model.js for comparison)

Operating range of each running unit: any flow from min to max, and any blend of its lean,
normal and rich analyses. Header: heat short of demand is made up with NG; heat above demand
is flared and does not change the composition.

Checks
 1. Single case: normal operation computed here matches model.js.
 2. Closure, inside every evaluation: mol fractions sum to 1, component flows sum to total.
 3. Exhaustive: for test scenarios with 5 running units, evaluate every candidate extreme:
    all 6^5 corners (flow min/max x lean/normal/rich) and every balance point (one unit
    blending two of its corners so header heat equals demand exactly, the others at corners).
    Linear-programming theory says the extremes of every property except Wobbe are among
    these points. Compare the true min/max with model.js. Test sets are chosen so that the
    header crosses from short to long within the range, so balance points are exercised.
 4. Sampled, no theory assumed: for every scenario, random corners, random points anywhere
    inside the range, and random points forced onto the heat-balance boundary must all lie
    within the model.js envelope. This is the main check on Wobbe, which is searched.
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
    """Analysis for blend weights w = (lean, normal, rich)."""
    t = sum(w)
    return [(w[0] * Y[u]["lean"][j] + w[1] * Y[u]["normal"][j] + w[2] * Y[u]["rich"][j]) / t for j in range(NC)]

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
    return dict(F=F, h2=s("H2"), c1=s("CH4"), c2=g("c2"), olef=s("C2H4", "C3H6"), c3=g("c3"),
                c4p=s("C4", "C5+"), inert=g("inert"), h2s=x[IDS.index("H2S")] * 1e6, mw=mw,
                lhv=sum(x[j] * QN[j] for j in range(NC)) / VM, hhv=hhv,
                wobbe=hhv / (mw / AIR) ** 0.5, ng=ng, flare=flare)

PURE = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
def corners(u):
    fl = UNITS[u]["flow_kmol_h"]
    return [(fl[fk], blend(u, w)) for fk in ("min", "max") for w in PURE]

def run_js(extra):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(extra, f); path = f.name
    out = subprocess.run(["node", os.path.join(HERE, "search_cli.js"), os.path.join(HERE, "example_units.json"), path],
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

print("1. Normal operation, single case")
py = header([(UNITS[u]["flow_kmol_h"]["normal"], Y[u]["normal"]) for u in ALL], demand([]))
for k in ["F", "mw", "lhv", "hhv", "wobbe", "ng"]:
    report(f"{k:6} python {py[k]:10.4f}   model.js {JS['normal'][k]:10.4f}",
           abs(py[k] - JS["normal"][k]) < 1e-6 * max(1, abs(py[k])))

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

print("\n4. Sampled per scenario: 2,000 corners + 2,000 interior + up to 1,000 on the heat-balance boundary")
def random_setting(u):
    fl = UNITS[u]["flow_kmol_h"]; w = [rnd.random() for _ in range(3)]
    return [fl["min"] + rnd.random() * (fl["max"] - fl["min"]), blend(u, w)]
for s in D["scenarios"]:
    down = set(s["down"]); keep = [u for u in ALL if u not in down]; dem = demand(down)
    js = jsS[s["id"]]; worst, wk = 0.0, ""
    samples = [header([rnd.choice(corners(u)) for u in keep], dem) for _ in range(2000)]
    samples += [header([random_setting(u) for u in keep], dem) for _ in range(2000)]
    nb = tries = 0
    while nb < 1000 and tries < 50000:
        tries += 1
        st = [random_setting(u) for u in keep]; i = rnd.randrange(len(st)); u = keep[i]
        need = dem - sum(heat(f, y) for j, (f, y) in enumerate(st) if j != i)
        f = need * 1000 / sum(st[i][1][j] * QN[j] for j in range(NC))
        fl = UNITS[u]["flow_kmol_h"]
        if fl["min"] <= f <= fl["max"]:
            st[i][0] = f; samples.append(header(st, dem)); nb += 1
    for r in samples:
        for k in KEYS:
            over = max(js[k]["min"] - r[k], r[k] - js[k]["max"], 0) / max(1.0, abs(r[k]))
            if over > worst: worst, wk = over, k
    report(f"{s['name']} ({len(samples):,} samples, {nb:,} on boundary)", worst < 1e-6,
           "all inside envelope" if worst < 1e-6 else f"sample outside by {worst:.1e} on {wk}")

print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
