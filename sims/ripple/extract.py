"""Regenerate the embedded data block of sims/ripple/ripple.html from the FEED package.

    python sims/ripple/extract.py

Reads the activity network (cfu/wrapup/activities.py), the document register, the cost estimate and the master
data files (data/*.json), and rewrites the JS constant between /*DATA:BEGIN*/ and /*DATA:END*/ in ripple.html.
Nothing here is hand-typed process data: every number traces to a file in the package. Engineering rules and
assumptions (scaling exponents, hours per document, unit rates) live in ripple.html, where they are shown.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = Path(__file__).resolve().parent / "ripple.html"
sys.path.insert(0, str(ROOT))

from cfu import basis  # noqa: E402
from cfu.wrapup.activities import ACTIVITIES, DISCIPLINES, FEEDBACK  # noqa: E402

DATA = ROOT / "data"
WRAP = ROOT / "deliverables" / "06-wrapup"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def r(x, n=3):
    return None if x is None else round(float(x), n)


# ------------------------------------------------------------------------------------------- activity network
def network():
    A = {a["id"]: a for a in ACTIVITIES}
    wave = {}

    def w(i):
        if i not in wave:
            wave[i] = 1 + max((w(p) for p, _ in A[i]["after"]), default=0)
        return wave[i]

    acts = []
    for a in ACTIVITIES:
        acts.append(dict(id=a["id"], n=a["name"], d=a["disc"], s=a["status"], w=w(a["id"]),
                         a=[[p, f] for p, f in a["after"]], ext=a["ext"], docs=a["docs"], note=a["note"],
                         wr=a["writes"]))
    return acts, [[f, t, x] for f, t, x in FEEDBACK]


# ------------------------------------------------------------------------------------------- document register
def register(acts, lines, routing):
    rows = []
    for ln in (WRAP / "CFU-000-PM-REG-001_Document-Register.md").read_text(encoding="utf-8").splitlines():
        if ln.startswith("| CFU"):
            c = [x.strip() for x in ln.strip("|").split("|")]
            rows.append(dict(no=c[0], disc=c[1], title=c[2]))
    # owning activity: longest matching docs prefix
    owner = {}
    for d in rows:
        best = None
        for a in acts:
            for p in a["docs"]:
                if d["no"].startswith(p) and (best is None or len(p) > len(best[1])):
                    best = (a["id"], p)
        owner[d["no"]] = best[0] if best else None
    # equipment on each P&ID sheet (from line end points) and lines on each sheet
    tagre = re.compile(r"\b([A-Z])-(\d{3})([A-Z]?)")
    sheet_tags, sheet_lines = {}, {}
    for i, l in enumerate(lines):
        for sh in [s.strip() for s in (l["pid_sheet"] or "").split(",") if s.strip()]:
            sheet_lines.setdefault(sh, []).append(i)
            for side in (l["from"], l["to"]):
                for m in tagre.finditer(side or ""):
                    sheet_tags.setdefault(sh, set()).add(f"{m.group(1)}-{m.group(2)}")
    iso_line = {x["iso"]: x["line"] for x in routing["iso_register"]}
    line_ix = {l["line_no"]: i for i, l in enumerate(lines)}
    ds_type = {"001": ["Column"], "002": ["Drum", "Desalter"], "003": ["Fired heater"], "004": ["Shell & tube"],
               "005": ["Air cooler"], "006": ["Pump"], "007": ["PSV"]}
    out = []
    for d in rows:
        no, t = d["no"], d["title"]
        typ = no.split("-")[3]
        e = dict(no=no, disc=d["disc"], t=t, a=owner[no], typ=typ)
        seq = no.split("-")[4]
        if seq in ("ALL",) or (typ in ("ISO", "DS") and seq == "000"):
            e["k"] = "set"                       # compiled set: re-issued if any sheet in it is
        elif typ == "PID" and seq == "000":
            e["k"] = "legend"
        elif typ == "PID":
            e["k"] = "pid"
            e["tags"] = sorted(sheet_tags.get(no, []))
            e["ln"] = sheet_lines.get(no, [])
        elif typ == "ISO":
            e["k"] = "iso"
            e["ln"] = [line_ix[iso_line[no]]] if iso_line.get(no) in line_ix else []
        elif typ == "DS" and seq in ds_type:
            e["k"] = "ds"
            e["types"] = ds_type[seq]
        elif typ in ("GA", "ELV"):
            e["k"] = "ga"
            tags = {f"{m.group(1)}-{m.group(2)}" for m in re.finditer(r"\b([A-Z]) ?(\d{3})", t)}
            if "Side Strippers" in t:
                tags |= {"C-102", "C-103", "C-104"}
            if "Exchanger" in t:
                tags |= {"E-1xx"}
            if "Pipe Rack" in t:
                tags |= {"RACK"}
            e["tags"] = sorted(tags)
        out.append(e)
    return out


# ------------------------------------------------------------------------------------------- equipment & mech
def equipment(proc):
    eq = load("equipment.json")
    hot = {e["tag"]: e["hot"] for e in proc["preheat"]["exch"]}
    keep = ["tag", "type", "service", "area", "D", "D2", "D3", "H", "L", "duty_kw", "area_m2", "shells", "series",
            "parallel", "area_per_shell", "bays", "fans", "fan_kw", "motor_kw", "absorbed_kw", "flow_m3h", "head_m",
            "residence_min", "holdup_min", "size", "internals"]
    out = []
    for e in eq:
        d = {k: (r(e[k], 4) if isinstance(e.get(k), float) else e.get(k)) for k in keep if e.get(k) is not None}
        if e.get("sections"):
            d["sec"] = [[s["name"], r(s["D_calc"], 4), r(s["V_kg_h"], 0)] for s in e["sections"]]
        if e["tag"] in hot:
            d["hot"] = hot[e["tag"]]
        out.append(d)
    return out


def mech():
    m = load("mech.json")["items"]
    out = {}
    for tag, x in m.items():
        d = dict(we=x.get("weight_empty_t") or x.get("weight_empty_t_per_shell"),
                 wo=x.get("weight_operating_t"))
        if x.get("shell_courses"):
            d["co"] = [[c["section"], c["ID_mm"], round(c["z_to_m"] - c["z_from_m"], 2), c["t_req_mm"], c["t_nom_mm"]]
                       for c in x["shell_courses"]]
            d["ca"] = x["CA_mm"]
            d["sw"] = x["shell_weight_kg"]
        if x.get("weight_breakdown_t") and x["type"] == "Column":
            d["wb"] = x["weight_breakdown_t"]
        if x.get("anchor_bolts"):
            a = x["anchor_bolts"]
            d["wind"] = dict(V=x["wind_base_shear_kN"], M=x["wind_base_moment_kNm"], basis=x["wind_basis"],
                             n=a["n"], size=a["size"], bcd=a["bcd_m"], F=a["F_kN"], fab=x["weight_fabricated_t"],
                             plat=(x.get("weight_breakdown_t") or {}).get("platforms", 0), skirt_h=x["skirt_height_m"],
                             skirt_t=x["skirt_t_mm"], top=x["top_elevation_m"], fn=x.get("natural_freq_Hz"))
        if x["type"] == "Shell & tube" and x.get("shells"):
            d["shells"] = x["shells"]
        out[tag] = d
    return out


# ------------------------------------------------------------------------------------------- cost estimate
def cost():
    txt = (WRAP / "CFU-000-PM-EST-001_Cost-Estimate.md").read_text(encoding="utf-8")
    summ = {}
    for k, pat in [("pce", r"Purchased equipment \(2026 USGC\) \| ([\d.]+)"), ("inst", r"Installed ISBL[^|]*\| ([\d.]+)"),
                   ("eng", r"Design & engineering[^|]*\| ([\d.]+)"), ("cont", r"Contingency[^|]*\| ([\d.]+)"),
                   ("total", r"Total installed cost, ISBL \| ([\d.]+)")]:
        summ[k] = float(re.search(pat, txt).group(1))
    items = {}
    sec = txt.split("# 4 Equipment detail")[1].split("# 5")[0]
    for ln in sec.splitlines():
        if ln.startswith("| ") and not ln.startswith("| Tag") and not ln.startswith("|---"):
            c = [x.strip() for x in ln.strip("|").split("|")]
            items[c[0]] = [float(c[3].replace(",", "")), c[2]]
    summ["items"] = items
    return summ


# ------------------------------------------------------------------------------------------- lines
GROUP_RULES = [  # (regex on service/from/to, group) - first match wins; groups map to product cuts in ripple.html
    (r"PSV-(\d{4})", None), (r"Vacuum residue|\bVR\b", "VR"), (r"Slop wax", "SLOP"), (r"slop oil", "FIX"),
    (r"LVGO", "LVGO"), (r"HVGO|Wash oil", "HVGO"),
    (r"Atmospheric residue|P-112|H-201 pass|Vacuum transfer|H-201 coil|C-201 bottom stripping|Overflash", "AR"),
    (r"Stripping steam|stripping steam|SS coil|steam import|MP to LP|OH sour water", "STRIP"),
    (r"TPA", "TPA"), (r"MPA", "MPA"), (r"BPA|E-113", "BPA"),
    (r"Kerosene|C-102", "KERO"), (r"Diesel|C-103", "DIESEL"), (r"AGO|C-104", "AGO"),
    (r"[Cc]rude|H-101 pass|Atmospheric transfer|[Ww]ash water|brine|[Mm]ud-wash|effluent water", "CRUDE"),
    (r"C-101 overhead|A-101 outlet|E-115|Reflux pump|Reflux to C-101|Unstabilised naphtha|D-102", "OVHD"),
    (r"Stabilis|LPG|C-105|D-105|Kettle reboiler|E-116|HP steam", "OVHD"),
    (r"Light naphtha|Splitter reflux|Splitter overhead|Splitter condensate|D-106", "LN"),
    (r"Heavy naphtha|Splitter thermosyphon|Thermosyphon|E-117", "HN"),
    (r"J-20|E-20[234]|ejector|Ejector|[Vv]acuum column overhead|Hotwell|hotwell|NCG|off-gas|Motive steam|E-202", "VACOH"),
    (r"[Ff]uel gas|FG|pilot|burner", "FUEL"),
    (r"[Cc]ooling water", "CW"),
]


def line_group(l):
    if l["fluid"] in ("FL", "BD", "CH", "IA", "N") or "snuffing" in l["service"] or "spillback" in l["service"] \
            or "minimum flow" in l["service"] or "drain" in l["service"]:
        m = re.search(r"PSV-(\d{4})", l["service"] + " " + l["from"])
        if m:
            return "PSV-" + m.group(1)
        if "governing PSV-1001" in l["service"] or l["service"].startswith("Unit flare KO drum outlet"):
            return "PSV-1001"
        return "FIX"
    if l["fluid"] in ("BFW", "CD") and "E-201" not in l["service"] and "E-113" not in l["service"]:
        txt = l["service"] + " " + l["from"] + " " + l["to"]
        if "E-116" in txt:
            return "OVHD"
        if "E-117" in txt:
            return "HN"
        return "FIX"
    txt = f"{l['service']} | {l['from']} | {l['to']}"
    if l["fluid"] == "FG":
        return "FIX" if "make-up" in l["service"] else "FUEL"
    if "import" in l["service"]:
        return "STRIP"
    if "E-201" in txt:
        return "VR"
    for pat, g in GROUP_RULES:
        if g and re.search(pat, txt):
            return g
    return "FIX"


def lines_data(routing):
    lines = load("lines.json")
    length = {x["line_no"]: x["lengths"]["total_m"] for x in routing["routes"] if x.get("lengths")}
    out = []
    for l in lines:
        out.append([l["line_no"], l["size_in"], l["sizing_basis"], r(l["flow_kg_h"], 0), r(l["density_kg_m3"], 3),
                    r(l["velocity_m_s"], 2), line_group(l), r(length.get(l["line_no"]), 1), l["cls"], l["op_T_C"],
                    l["fluid"], l["service"], l["from"], l["to"]])
    return lines, out


# ------------------------------------------------------------------------------------------- electrical
def electrical():
    el = load("electrical.json")
    md = el["max_demand"]
    loads = [[x["tag"], x["equipment"], x["rated_kW"], r(x["absorbed_kW"], 2), r(x["input_kW"], 2), x["duty"], x["bus"],
              x["voltage_V"]]
             for x in el["loads"] if x["category"] in ("Pumps", "Fired-heater fans", "Air-cooler fans")]
    tr = [dict(tag=t["tag"], kv=f"{t['pri_kV']}/{t['sec_kV']}", onan=t["onan_kVA"], onaf=t["onaf_kVA"],
               md=t["md_contingency_kVA"], pct=t["loading_onan_pct"]) for t in el["transformers"] if "onan_kVA" in t]
    return dict(md_kW=md["total_13_8kV"]["kW"], md_kVA=md["total_13_8kV"]["kVA"], lv_kW=md["lv_total"]["kW"],
                lv_kVA=md["lv_total"]["kVA"], mv_kW=md["mv_motors_total"]["kW"], mv_kVA=md["mv_motors_total"]["kVA"],
                div=el["basis"]["diversity"], mv_thr=el["basis"]["mv_motor_threshold_kW"], tr=tr, loads=loads)


def main():
    proc = load("process_results.json")
    streams = load("streams.json")
    routing = load("routing.json")
    acts, fb = network()
    lines_raw, lines = lines_data(routing)
    docs = register(acts, lines_raw, routing)
    io = load("io_list.json")["totals"]
    cl = load("control_loops.json")
    psv = [[p["tag"], p["protects"], p["case"], r(p["load_kg_h"], 0), r(p["area_mm2"], 0), p["orifice"], p["count"]]
           for p in load("psv.json")]
    cut_stream = dict(LPG="30", LN="32", HN="33", KERO="16", DIESEL="17", AGO="18", LVGO="23", HVGO="24", SLOP="25",
                      VR="26")
    S = {s["no"]: s for s in streams}
    data = dict(
        meta=dict(project=basis.PROJECT["name"], rev=basis.PROJECT["rev"], stage=basis.PROJECT["stage"],
                  bpsd=basis.CAPACITY_BPSD, margin=basis.DESIGN_MARGIN, crude=basis.CRUDE["name"],
                  api=basis.CRUDE["api"], s_wt=basis.CRUDE["sulfur_wt"], check=basis.CHECK_CRUDE,
                  tbp=basis.CRUDE["tbp"], cuts=basis.CUTS_ATM + basis.CUTS_VAC, site=basis.SITE,
                  diesel_spec=basis.PRODUCT_SPECS["DIESEL"], flux=basis.DESIGN["rad_flux_kW_m2"],
                  rad_frac=basis.DESIGN["rad_fraction"]),
        disc=DISCIPLINES, act=acts, fb=fb, docs=docs,
        cuts={k: dict(kg_h=S[v]["total_kg_h"], api=S[v]["api"], tbp5=S[v]["tbp5"], tbp95=S[v]["tbp95"], s=S[v]["sulfur_wt"],
                      stream=v, name=S[v]["name"]) for k, v in cut_stream.items()},
        crude=dict(kg_h=proc["crude"]["kg_h"], m3h=proc["crude"]["m3h"], api=proc["crude"]["api"],
                   std_m3h=S["1"]["std_m3h"], ar_kg_h=S["19"]["total_kg_h"]),
        heaters={k: {x: r(v[x], 3) for x in ("Q_abs_kw", "Q_fired_kw", "Q_proc_kw", "eff", "rad_area", "rad_tubes", "passes",
                                             "burners", "cells", "T_in", "T_out", "fuel_kg_h", "radiant_kw")}
                 for k, v in proc["heaters"].items()},
        stab=dict(top=proc["stab"]["sec_top"]["D_calc"], bot=proc["stab"]["sec_bot"]["D_calc"]),
        split=dict(top=proc["split"]["sec_top"]["D_calc"], bot=proc["split"]["sec_bot"]["D_calc"]),
        eq=equipment(proc), mech=mech(), cost=cost(), el=electrical(), lines=lines, psv=psv,
        io={k: dict(sys=v["system"], **{t: [v[t]["used"], v[t]["installed"]] for t in ("AI", "AO", "DI", "DO")})
            for k, v in io["by_controller"].items()},
        io_used=io["grand"]["used"], n_inst=len(load("instruments.json")),
        sifs=[[s["tag"], s["function"], s["sil"]] for s in cl["sifs"]],
    )
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    html = HTML.read_text(encoding="utf-8")
    new = re.sub(r"/\*DATA:BEGIN\*/.*?/\*DATA:END\*/", lambda m: "/*DATA:BEGIN*/" + blob + "/*DATA:END*/", html,
                 count=1, flags=re.S)
    if new == html and "/*DATA:BEGIN*/" + blob + "/*DATA:END*/" not in html:
        raise SystemExit("DATA markers not found in ripple.html")
    HTML.write_text(new, encoding="utf-8")
    print(f"ripple.html data block: {len(blob) / 1024:.1f} KB, {len(acts)} activities, {len(docs)} documents, "
          f"{len(lines)} lines, {len(data['eq'])} equipment items")


if __name__ == "__main__":
    main()
