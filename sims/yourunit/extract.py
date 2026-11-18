"""Regenerate the embedded data block of Your Unit (sims/yourunit/yourunit.html) from the FEED package.

    python sims/yourunit/extract.py

Reads data/layout.json (geometry), data/equipment.json, data/mech.json, data/streams.json,
data/process_results.json, data/instruments.json, data/io_list.json, data/control_loops.json, data/psv.json,
data/electrical.json and deliverables/06-wrapup/CFU-000-PM-EST-001_Cost-Estimate.md (CAPEX + purchased cost),
then rewrites the JS constant between /*DATA:BEGIN*/ and /*DATA:END*/ in place.

Nothing in the page's engineering numbers is typed by hand: product yields, temperatures, duties, weights and
counts all come from here. The only page-side inputs are the illustrative prices and the illustrative
alternative-crude yield vectors, which the page labels as such.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = Path(__file__).with_name("yourunit.html")
D = ROOT / "data"


def load(name):
    return json.loads((D / name).read_text(encoding="utf-8"))


def r(v, n=2):
    if isinstance(v, float):
        v = round(v, n)
        return int(v) if v == int(v) and abs(v) < 1e9 else v
    return v


def rr(o, n=2):
    if isinstance(o, dict):
        return {k: rr(v, n) for k, v in o.items()}
    if isinstance(o, list):
        return [rr(v, n) for v in o]
    return r(o, n)


lay = load("layout.json")
equip = load("equipment.json")
mech = load("mech.json")["items"]
streams = load("streams.json")
proc = load("process_results.json")
instr = load("instruments.json")
io = load("io_list.json")
loops = load("control_loops.json")
psv = load("psv.json")
elec = load("electrical.json")
est_md = (ROOT / "deliverables/06-wrapup/CFU-000-PM-EST-001_Cost-Estimate.md").read_text(encoding="utf-8")

# ---------------------------------------------------------------- cost estimate (markdown tables)
cost = {}
for m in re.finditer(r"^\| ([A-Z]-\d{3}[A-Z]?(?:/[A-Z])?) \| [^|]+ \| [^|]+ \| ([\d,\.]+) \|$", est_md, re.M):
    cost[m.group(1)] = float(m.group(2).replace(",", ""))
tic = float(re.search(r"Total installed cost, ISBL \| ([\d\.]+)", est_md).group(1))
pec = float(re.search(r"Purchased equipment \(2026 USGC\) \| ([\d\.]+)", est_md).group(1))
cls = re.search(r"AACE (Class \d) \(expected accuracy ([^)]+)\)", est_md)
per_bpsd = re.search(r"\*\*([\d,]+) USD per BPSD\*\*", est_md).group(1)

# ---------------------------------------------------------------- geometry
KEEP = ("tag", "parent_tag", "type", "shape", "x", "y", "z_base", "rotation", "L", "W", "height", "top_el", "D",
        "bottom_tl", "top_tl", "skirt_h", "body", "cone", "z_axis", "TT", "channel_end", "boot", "radiant",
        "convection", "stack", "cells", "fan_deck_el", "fans", "transformers", "service")
items = []
for e in lay["equipment"]:
    it = {k: e[k] for k in KEEP if k in e}
    if e["shape"] == "vcyl" or e["tag"] in ("H-101", "H-201", "D-102", "D-101A", "D-101B", "A-101-B1", "J-201"):
        it["noz"] = e.get("nozzles", {})
    items.append(rr(it, 3))

st = lay["structures"]
geo = rr({
    "frame": lay["frame"],
    "rack": {k: st["pipe_rack"][k] for k in ("id", "x0", "x1", "y0", "y1", "bents_x", "tiers", "air_cooler_deck")},
    "platforms": st["column_platforms"],
    "ejector": st["ejector_structure"],
    "roads": st["roads"],
    "buildings": st["buildings"],
    "areas": [a for a in st["areas"] if a["kind"].startswith(("laydown", "crane", "bundle"))],
    "items": items,
}, 3)

# ---------------------------------------------------------------- streams + equipment cards
S = []
for s in streams:
    S.append(rr({"no": s["no"], "name": s["name"], "frm": s["frm"], "to": s["to"], "T": s.get("T_C"),
                 "P": s.get("P_barg"), "ph": s.get("phase"), "kg": s.get("total_kg_h"), "bpsd": s.get("bpsd"),
                 "api": s.get("api")}, 1))


def base(tag):
    """'P-101A/B' -> 'P-101', 'D-101A' -> 'D-101'."""
    return re.match(r"[A-Z]-\d{3}", tag).group(0)


def ends(field, tag):
    toks = re.split(r"[ /]", field)
    return tag in toks or base(tag) in toks


cards = {}
for e in equip:
    t = e["tag"]
    m = mech.get(t, {})
    wt = m.get("weight_empty_t") or m.get("weight_t_each")
    c = {k: e[k] for k in ("type", "service", "size", "internals", "op_P", "op_T", "des_P", "des_T", "moc", "tema",
                           "shellside", "tubeside", "area_m2", "flow_m3h", "head_m", "motor_kw", "duty_kw",
                           "absorbed_kw", "api610", "residence_min") if e.get(k) not in (None, "")}
    c["wt_e"] = wt
    c["wt_o"] = m.get("weight_operating_t")
    if m.get("weight_t_each"):
        c["wt_each"] = True
    c["cost_k"] = cost.get(t)
    c["s_in"] = [s["no"] for s in streams if ends(s["to"], t)]
    c["s_out"] = [s["no"] for s in streams if ends(s["frm"], t)]
    c["psv"] = [f'{p["tag"]}: {p["case"]}, {p["count"]} x {p["orifice"]}, set {p["set_barg"]} barg'
                for p in psv if p["protects"] in (t, base(t))]
    cards[t] = rr(c, 1)

# column / heater key-duty lines (from the process model)
atm, vac, stab, split, H = proc["atm"], proc["vac"], proc["stab"], proc["split"], proc["heaters"]
key = {
    "C-101": f'Heat removal {atm["Q_tot_kw"]/1e3:.1f} MW: TPA {atm["pa"]["TPA"]["duty_kw"]/1e3:.1f}, '
             f'MPA {atm["pa"]["MPA"]["duty_kw"]/1e3:.1f}, BPA {atm["pa"]["BPA"]["duty_kw"]/1e3:.1f} MW; '
             f'flash zone {atm["T_fz"]:.0f} °C, top {atm["T_top"]:.0f} °C',
    "C-201": f'Heat removal {vac["Q_tot_kw"]/1e3:.1f} MW: LVGO PA {vac["pa"]["LVGO"]["duty_kw"]/1e3:.1f}, '
             f'HVGO PA {vac["pa"]["HVGO"]["duty_kw"]/1e3:.1f} MW; flash zone {vac["T_fz"]:.0f} °C at '
             f'{vac["P_fz_mbar"]:.0f} mbar(a)',
    "C-105": f'Reboiler {stab["Q_reb"]/1e3:.1f} MW, condenser {stab["Q_cond"]/1e3:.1f} MW; {stab["N_actual"]} trays, R = {stab["R"]:.2f}',
    "C-106": f'Reboiler {split["Q_reb"]/1e3:.1f} MW, condenser {split["Q_cond"]/1e3:.1f} MW; {split["N_actual"]} trays, R = {split["R"]:.2f}',
    "H-101": f'{H["H-101"]["Q_fired_kw"]/1e3:.1f} MW fired, {H["H-101"]["Q_abs_kw"]/1e3:.1f} MW absorbed, '
             f'eff. {H["H-101"]["eff"]*100:.0f} % (LHV); fuel gas {H["H-101"]["fuel_kg_h"]:,.0f} kg/h',
    "H-201": f'{H["H-201"]["Q_fired_kw"]/1e3:.1f} MW fired, {H["H-201"]["Q_abs_kw"]/1e3:.1f} MW absorbed, '
             f'eff. {H["H-201"]["eff"]*100:.0f} % (LHV); fuel gas {H["H-201"]["fuel_kg_h"]:,.0f} kg/h',
}
for t, v in key.items():
    cards[t]["key"] = v

# ---------------------------------------------------------------- products (stream numbers per the PDR table 3.1)
crude_kg = proc["crude"]["kg_h"]
PROD = [("LPG", "LPG", "30"), ("LN", "Light naphtha", "32"), ("HN", "Heavy naphtha", "33"), ("KERO", "Kerosene", "16"),
        ("DIESEL", "Diesel", "17"), ("AGO", "AGO", "18"), ("LVGO", "LVGO", "23"), ("HVGO", "HVGO", "24"),
        ("SLOP", "Slop wax", "25"), ("VR", "Vacuum residue", "26")]
byno = {s["no"]: s for s in streams}
products = []
for k, name, no in PROD:
    s = byno[no]
    products.append(rr({"k": k, "name": name, "no": no, "bpsd": s["bpsd"], "kg": s["hc_kg_h"],
                        "wt": 100 * s["hc_kg_h"] / crude_kg, "api": s["api"], "S": s["sulfur_wt"], "T": s["T_C"],
                        "dest": s["to"], "rho": s["hc_kg_h"] / s["std_m3h"]}, 3))

# ---------------------------------------------------------------- process headline numbers
ph = proc["preheat"]
cold = sum(x["Q_kw"] for x in ph["exch"] if x["train"] == "cold")
hot = sum(x["Q_kw"] for x in ph["exch"] if x["train"] == "hot")
trims = {x["tag"]: x for x in ph["trims"]}
eqd = {e["tag"]: e for e in equip}
P = rr({
    "crude": proc["crude"], "S": byno["1"]["sulfur_wt"], "T_in": byno["1"]["T_C"],
    "cit": ph["CIT"], "T_desalter": ph["T_desalter"], "wash": ph["wash_water"], "brine": byno["4"]["total_kg_h"],
    "Q_cold": cold, "Q_hot": hot, "n_cold": sum(1 for x in ph["exch"] if x["train"] == "cold"),
    "n_hot": sum(1 for x in ph["exch"] if x["train"] == "hot"),
    "atm": {k: atm[k] for k in ("T_fz", "cot", "P_fz_barg", "T_top", "T_bot", "T_draw", "reflux_kg_h", "Q_tot_kw", "Q_cond_kw")},
    "pa": {k: v["duty_kw"] for k, v in atm["pa"].items()},
    "strip_steam": byno["20"]["total_kg_h"],
    "vac": {k: vac[k] for k in ("T_fz", "cot", "P_fz_mbar", "P_top_mbar", "T_top", "T_bot", "T_lvgo", "T_hvgo", "steam", "Q_tot_kw")},
    "ejector_motive": proc["ejector"]["motive_total"],
    "H101": H["H-101"], "H201": H["H-201"],
    "ar_kg": byno["19"]["total_kg_h"], "ar_bpsd": byno["19"]["bpsd"], "ar_T": byno["19"]["T_C"],
    "oh_kg": byno["8"]["total_kg_h"], "A101_kw": eqd["A-101"]["duty_kw"],
    "stab_reb": stab["Q_reb"], "split_reb": split["Q_reb"],
    "E113_kw": trims["E-113"]["Q_kw"], "E201_kw": trims["E-201"]["Q_kw"],
    "C101": {"D": eqd["C-101"]["D"], "H": eqd["C-101"]["H"], "trays": 41},
    "C201": {"D": eqd["C-201"]["D"], "H": eqd["C-201"]["H"]},
    "P101": {"flow": eqd["P-101A/B"]["flow_m3h"], "head": eqd["P-101A/B"]["head_m"], "kw": eqd["P-101A/B"]["motor_kw"]},
    "D101_res": eqd["D-101A"]["residence_min"],
    "fuel_gas": byno["34"]["total_kg_h"],
}, 2)

# ---------------------------------------------------------------- energy (utilities)
# Steam rates for reboilers / steam generators are derived from duty with steam-table enthalpy differences:
#   HP 41.4 barg / 400 °C to condensate at 254 °C:   3205 - 1105 = 2100 kJ/kg
#   MP 10.3 barg / 250 °C to condensate at 186 °C:   2935 -  790 = 2145 kJ/kg
#   MP generated (sat. 11.3 bara) from BFW 120 °C:   2782 -  504 = 2278 kJ/kg
#   LP generated (sat.  4.5 bara) from BFW 120 °C:   2744 -  504 = 2240 kJ/kg
kgh = lambda kw, dh: kw * 3600 / dh
energy = rr({
    "fired_kw": H["H-101"]["Q_fired_kw"] + H["H-201"]["Q_fired_kw"],
    "fuel_kg_h": H["H-101"]["fuel_kg_h"] + H["H-201"]["fuel_kg_h"],
    "lhv": 47.0,
    "steam": [
        ["Atmospheric stripping steam (C-101..C-104)", "MP", byno["20"]["total_kg_h"], "H&MB stream 20"],
        ["Vacuum stripping + coil steam (C-201, H-201)", "MP", vac["steam"], "PDR §7"],
        ["Ejector motive steam (J-201..J-203)", "MP", proc["ejector"]["motive_total"], "PDR §7"],
        ["Stabiliser reboiler E-116", "HP", kgh(stab["Q_reb"], 2100), f'{stab["Q_reb"]/1e3:.2f} MW / 2,100 kJ/kg'],
        ["Splitter reboiler E-117", "MP", kgh(split["Q_reb"], 2145), f'{split["Q_reb"]/1e3:.2f} MW / 2,145 kJ/kg'],
        ["BPA steam generator E-113 (credit)", "MP", -kgh(trims["E-113"]["Q_kw"], 2278), f'{trims["E-113"]["Q_kw"]/1e3:.2f} MW / 2,278 kJ/kg'],
        ["VR steam generator E-201 (credit)", "LP", -kgh(trims["E-201"]["Q_kw"], 2240), f'{trims["E-201"]["Q_kw"]/1e3:.2f} MW / 2,240 kJ/kg'],
    ],
    "power_kw": elec["max_demand"]["total_13_8kV"]["kW"],
}, 1)

# ---------------------------------------------------------------- at a glance
glance = rr({
    "bpsd": proc["crude"]["bpsd"], "kg_h": proc["crude"]["kg_h"], "api": proc["crude"]["api"], "S": byno["1"]["sulfur_wt"],
    "crude": "Arab Light", "n_products": len(products),
    "fired_h101": H["H-101"]["Q_fired_kw"] / 1e3, "fired_h201": H["H-201"]["Q_fired_kw"] / 1e3,
    "n_equip": len(equip), "n_placed": len(lay["equipment"]),
    "n_instr": len(instr), "io_used": io["totals"]["grand"]["used"], "n_loops": len(loops["loops"]),
    "n_sif": len(loops["sifs"]), "n_psv": len(psv),
    "tic": tic, "pec": pec, "cls": cls.group(1), "acc": cls.group(2), "per_bpsd": per_bpsd,
    "plot": [lay["frame"]["plot_x"], lay["frame"]["plot_y"]],
}, 2)

DATA = {"src": "FEED Rev A: data/*.json + CFU-000-PM-EST-001", "glance": glance, "geo": geo, "cards": cards,
        "streams": S, "products": products, "P": P, "energy": energy}

blob = json.dumps(DATA, separators=(",", ":"), ensure_ascii=False)
html = HTML.read_text(encoding="utf-8")
new, n = re.subn(r"/\*DATA:BEGIN\*/.*?/\*DATA:END\*/", lambda _: f"/*DATA:BEGIN*/{blob}/*DATA:END*/", html, flags=re.S)
if n != 1:
    raise SystemExit("DATA markers not found exactly once in yourunit.html")
HTML.write_text(new, encoding="utf-8")
print(f"wrote {len(blob)/1024:.1f} KB of data into {HTML.relative_to(ROOT)}")
