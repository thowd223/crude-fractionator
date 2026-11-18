"""Regenerate the embedded data block of sims/biglift/biglift.html from the FEED package.

    python sims/biglift/extract.py

Reads data/layout.json (plot plan model, CFU-000-PL-PLT-001), data/mech.json (mechanical calcs, CFU-000-ME-CAL-001)
and data/routing.json (piping routing model, CFU-000-PI-RPT-001) and rewrites the JS constant between the
/*DATA:BEGIN*/ and /*DATA:END*/ markers in biglift.html.

Derived here (so the numbers are traceable):
  * lift candidates (C-101, C-201, C-106): overall length from foundation top to top of head (layout),
    lift weights (mech fabricated weight; "dressed" adds platforms + insulation from the mech weight breakdown),
    centre of gravity along the axis from the shell-course masses (mech ID x t_nom x course length) plus skirt,
    heads, internals, nozzles and cladding, trunnion station (1.0 m below top tangent line) and wind sail area
    (projected body sections from the layout model, + insulation thickness when dressed).
  * per-item empty weight (mech) used to weight equipment-erection progress in the 4D S-curve.
Everything else (crane charts, sequence rules) is illustrative and lives in the page, labelled as such.
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = Path(__file__).resolve().parent / "biglift.html"
LIFT_TAGS = ["C-101", "C-201", "C-106"]
TRUNNION_BELOW_TTL = 1.0   # m, trunnions on the top shell course
TAIL_LUG_ABOVE_BASE = 0.3  # m, tailing lug / base ring


def r(v, n=2):
    return None if v is None else round(float(v), n)


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def cog_and_area(it, m, dressed):
    """Centre of gravity (m above base ring) and projected sail area (m2) for a vertical vessel."""
    zb = it["z_base"]
    btl, ttl = it["bottom_tl"], it["top_tl"]
    tt = ttl - btl
    bd = m["weight_breakdown_t"]
    parts = []  # (mass t, s from base)
    # shell courses: distribute mech shell mass by ID x t x length
    courses = m["shell_courses"]
    raw = [(c["ID_mm"] / 1000) * c["t_nom_mm"] * (c["z_to_m"] - c["z_from_m"]) for c in courses]
    tot = sum(raw) or 1.0
    scale = tt / max(courses[-1]["z_to_m"], 1e-6)
    for c, w in zip(courses, raw):
        s_mid = (btl - zb) + scale * 0.5 * (c["z_from_m"] + c["z_to_m"])
        parts.append((bd["shell"] * w / tot, s_mid))
    parts.append((bd["skirt"], 0.5 * (btl - zb)))
    parts.append((bd["heads"] * 0.5, btl - zb))
    parts.append((bd["heads"] * 0.5, ttl - zb))
    mid = (btl - zb) + 0.5 * tt
    for k in ("internals", "nozzles", "clad"):
        if bd.get(k):
            parts.append((bd[k], mid))
    if dressed:
        for k in ("platforms", "insulation"):
            if bd.get(k):
                parts.append((bd[k], mid + 0.1 * tt))  # platforms are concentrated in the upper half
    W = sum(p[0] for p in parts)
    s_cg = sum(p[0] * p[1] for p in parts) / W
    ins = (m.get("insulation_mm") or 0) / 1000 if dressed else 0.0
    area = (btl - zb) * (m["skirt_OD_mm"] / 1000)
    prev = None
    for z0, z1, D in it["body"]:
        area += (z1 - z0) * (D + 2 * ins)
        if prev:
            area += (z0 - prev[0]) * (0.5 * (prev[1] + D) + 2 * ins)
        prev = (z1, D)
    return W, s_cg, area


def main():
    L = load("layout.json")
    M = load("mech.json")["items"]
    R = load("routing.json")
    S = L["structures"]

    eq = []
    for it in L["equipment"]:
        e = {"t": it["tag"], "p": it.get("parent_tag", it["tag"]), "ty": it["type"], "sh": it["shape"],
             "x": r(it["x"]), "y": r(it["y"]), "z": r(it["z_base"]), "L": r(it["L"]), "W": r(it["W"]),
             "H": r(it["height"]), "top": r(it.get("top_el")), "r": it.get("rotation", 0),
             "bb": [r(v) for v in it["bbox"]], "svc": it.get("service", "")}
        if it.get("D"):
            e["D"] = r(it["D"])
        if it["shape"] == "vcyl":
            e["body"] = [[r(a), r(b), r(c)] for a, b, c in it.get("body") or [[it["z_base"], it["top_el"], it["D"]]]]
            e["btl"], e["ttl"] = r(it.get("bottom_tl", it["z_base"])), r(it.get("top_tl", it["top_el"]))
        if it["shape"] == "hcyl" and it.get("boot"):
            e["boot"] = {k: r(v) for k, v in it["boot"].items()}
        if it["shape"] == "heater":
            e["rad"] = {k: r(v) for k, v in it["radiant"].items()}
            e["conv"] = {k: r(v) for k, v in it["convection"].items()}
            e["stk"] = {k: r(v) for k, v in it["stack"].items()}
        if it["type"] == "Air cooler":
            e["fans"] = it.get("fans", 2)
        # empty weight for progress weighting (mech is keyed by parent tag; split per shell/bay/pump)
        m = M.get(it["tag"]) or M.get(it.get("parent_tag", ""))
        if m:
            if "weight_t_each" in m:
                w = m["weight_t_each"]
            elif "weight_empty_t_per_shell" in m:
                w = m["weight_empty_t_per_shell"]
            else:
                w = m.get("weight_empty_t", 0)
                if it["type"] == "Air cooler":
                    w = w / max(it.get("bays", 1), 1)
            e["wt"] = r(w, 1)
        eq.append(e)

    rk = S["pipe_rack"]
    rack = {"id": rk["id"], "x0": rk["x0"], "x1": rk["x1"], "y0": rk["y0"], "y1": rk["y1"], "bents": rk["bents_x"],
            "tiers": [t["el"] for t in rk["tiers"]], "ac_el": rk["air_cooler_deck"]["el"],
            "fan_el": rk["air_cooler_deck"]["fan_deck_el"], "ct_el": rk["cable_tray"]["el"],
            "ct_br": rk["cable_tray"]["bracket"], "headroom": rk["min_headroom_m"]}
    plat = [[p["tag"], r(p["el"]), r(p["r_in"]), r(p["r_out"]), p["arc"][0], p["arc"][1]] for p in S["column_platforms"]]

    mech = {}
    lifts = []
    byTag = {it["tag"]: it for it in L["equipment"]}
    for tag in LIFT_TAGS:
        it, m = byTag[tag], M[tag]
        bd = m["weight_breakdown_t"]
        Wf, cgf, Af = cog_and_area(it, m, False)
        Wd, cgd, Ad = cog_and_area(it, m, True)
        Lv = it["top_el"] - it["z_base"]
        lifts.append({
            "tag": tag, "svc": it["service"], "x": it["x"], "y": it["y"], "z": it["z_base"], "Lv": r(Lv),
            "Lt": r(it["top_tl"] - TRUNNION_BELOW_TTL - it["z_base"]), "tailLug": TAIL_LUG_ABOVE_BASE,
            "Dmax": max(b[2] for b in it["body"]), "fab": m["weight_fabricated_t"], "empty": m["weight_empty_t"],
            "oper": m["weight_operating_t"], "dress": {"platforms": bd.get("platforms", 0), "insulation": bd.get("insulation", 0)},
            "fabParts": {k: bd[k] for k in ("shell", "heads", "skirt", "nozzles", "clad", "internals") if bd.get(k)},
            "cgF": r(cgf), "cgD": r(cgd), "chkF": r(Wf, 1), "chkD": r(Wd, 1), "areaF": r(Af, 1), "areaD": r(Ad, 1),
            "skirtOD": m["skirt_OD_mm"] / 1000, "skirtH": r(it["bottom_tl"] - it["z_base"]), "ins_mm": m.get("insulation_mm", 0),
            "bolts": m["anchor_bolts"], "windV_kN": m["wind_base_shear_kN"], "windM_kNm": m["wind_base_moment_kNm"],
            "topEL": r(it["top_el"], 3), "mechTop": m["top_elevation_m"], "matl": m["material"],
        })
    for tag in ("H-101", "H-201"):
        m = M[tag]
        mech[tag] = {"empty": m["weight_empty_t"], "bd": {k: v for k, v in m["weight_breakdown_t"].items()
                                                         if k in ("rad_coil", "conv_coil", "refractory", "casing_structure", "stack")}}

    pipes = []
    for rt in R["routes"]:
        lev = {"header": 0, "critical": 1}.get(rt["level"], 2)
        for b in rt["branches"]:
            pts = b.get("points") or []
            if len(pts) < 2:
                continue
            flat = []
            for p in pts:
                flat += [round(p[0], 1), round(p[1], 1), round(p[2], 1)]
            pipes.append([b.get("nps") or rt["nps"], lev, flat])

    data = {
        "src": {"layout": f'{L["doc"]} rev {L["rev"]}', "mech": "CFU-000-ME-CAL-001 rev A", "routing": R["doc"]},
        "frame": {"px": L["frame"]["plot_x"], "py": L["frame"]["plot_y"], "grade": L["frame"]["grade_el"],
                  "wind": L["frame"]["wind"], "windFrom": 157.5},
        "eq": eq, "rack": rack, "plat": plat, "ejs": S["ejector_structure"], "roads": S["roads"],
        "bldg": S["buildings"], "areas": S["areas"], "lifts": lifts, "mech": mech, "pipes": pipes,
    }
    assert "157.5" in L["frame"]["wind"], "wind direction changed in layout.json - update windFrom"
    js = "const DATA=" + json.dumps(data, separators=(",", ":")) + ";"
    html = PAGE.read_text(encoding="utf-8")
    new, n = re.subn(r"/\*DATA:BEGIN\*/.*?/\*DATA:END\*/", lambda _m: "/*DATA:BEGIN*/" + js + "/*DATA:END*/", html, flags=re.S)
    if n != 1:
        raise SystemExit("DATA markers not found in biglift.html")
    PAGE.write_text(new, encoding="utf-8")
    for lf in lifts:
        print(f'{lf["tag"]}: L={lf["Lv"]} m, fab={lf["fab"]} t (chk {lf["chkF"]}), CoG {lf["cgF"]} m / dressed {lf["cgD"]} m, '
              f'trunnion {lf["Lt"]} m, area {lf["areaF"]}/{lf["areaD"]} m2')
    print(f"wrote {PAGE.relative_to(ROOT)}: {len(js) / 1024:.1f} KB data, {len(eq)} items, {len(pipes)} pipe branches")


if __name__ == "__main__":
    main()
