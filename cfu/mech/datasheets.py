"""Equipment datasheets CFU-000-ME-DS-001..007 (multi-page PDF per class) + combined xlsx."""
from __future__ import annotations

import math

from . import geometry
from .common import OUT, eq, equipment, flange_class, nps_for_area, nps_str, psvs, results, streams
from .dsrender import DSWriter, write_xlsx

TBD = "TBD"
VEN = "Vendor"


def fm(x, n=1, u=""):
    if x is None or x == "":
        return "-"
    if isinstance(x, str):
        return x
    return f"{x:,.{n}f}{(' ' + u) if u else ''}"


def _el(z):
    return f"EL {100 + z:.3f}"


# ---------------------------------------------------------------------------
def columns(calc):
    items = []
    for t, r in calc["columns"].items():
        g = calc["geoms"][t]
        e = g["e"]
        packed = t == "C-201"
        Ds = " / ".join(f"{x * 1000:.0f}" for x in g["Ds"])
        sec_names = ", ".join(f"{s['name']} {s['t_nom']}" for s in r["segs"])
        rings = [s for s in r["segs"] if s.get("ring")]
        a = r["anchor"]
        W = r["W"]
        S = [("Tag / quantity", f"{t} / 1"), ("Service", e["service"]), ("Type", "Packed + trayed" if packed else "Trayed"),
             ("Orientation", "Vertical, skirt supported"), ("Code", "ASME VIII Div.1 (U-stamp)"),
             ("Wind / seismic", "ASCE 7-16, 150 mph Exp. C / SDC B")]
        PR = [("Operating pressure top / bottom", f"{e['op_P']} {'barg' if 'mbar' not in e['op_P'] else ''}"),
              ("Operating temperature top / bottom", f"{e['op_T']} C"),
              ("Design pressure (internal)", f"{r['Pd']} barg"),
              ("Design pressure (external)", "Full vacuum" if r["fv"] else "None (see note)"),
              ("Design temperature", f"{r['Td']:.0f} C"), ("MDMT", "-5 C (site minimum)"),
              ("Corrosion allowance", f"{r['CA']} mm"), ("Joint efficiency / RT", f"{r['E']} / Full RT"),
              ("Hydrotest pressure (top / bottom)", f"{r['hydro']['Pt_top']:.2f} / {r['hydro']['Pt_bot']:.2f} barg"),
              ("Test position", "Vertical (field) - shop test of sections"),
              ("PWHT", "Yes (HIC / sour, NACE MR0103)" if "HIC" in e["moc"] or t == "C-105" else
                       ("Yes (thickness > 38 mm)" if max(s["t_nom"] for s in r["segs"]) > 38 else "Not required by code")),
              ("Service fluid", "Hydrocarbon + steam (sour)" if t != "C-105" else "LPG / naphtha (sour, H2S)")]
        MAT = [("Shell / heads", f"{r['mat']}"), ("Cladding / lining", e["moc"]),
               ("Skirt", "SA-516 Gr.70 (top 1 m same as shell)"), ("Nozzle necks / forgings", "SA-106 B / SA-105N"
                                                                                               if r["Td"] < 400 else "SA-335 P5 / SA-182 F5"),
               ("Internals (trays/packing)", "410S / 316L" if t != "C-105" else "410S"),
               ("Bolting (ext./int.)", "SA-193 B7 / SA-194 2H ; int. SS"), ("Gaskets", "Spiral-wound 316/graphite"),
               ("Insulation", f"{W['ins_mm']} mm mineral wool (heat cons.)" if W["ins_mm"] else "None")]
        MECH = [("Inside diameter(s)", f"{Ds} mm"), ("Tangent-tangent height", f"{e['H']:.2f} m"),
                ("Shell thickness by course", sec_names + " mm"),
                ("Top / bottom head (2:1 SE)", f"{r['heads']['top']['t_nom']} / {r['heads']['bottom']['t_nom']} mm"),
                ("Skirt height / thickness / OD", f"{r['skirt_h']:.1f} m / {r['skirt']['t_nom']} mm / {r['skirt']['D_mm']:.0f} mm"),
                ("BTL elevation", _el(r["skirt_h"])),
                ("Top of column", _el(W["H_total"])),
                ("Anchor bolts", f"{a['n']} x {a['size']} F1554 Gr.55 on {a['Dbc'] * 1000:.0f} BCD"),
                ("Stiffening rings", "; ".join(f"{s['name']}: {s['n_rings']} x {s['ring']['h']}x{s['ring']['b']} FB @ "
                                               f"{s['ext']['Ls'] / 1000:.1f} m" for s in rings) if rings else "None"),
                ("Platforms / davit", f"{len(g['platforms'])} platforms; davit on top head"),
                ("Fireproofing", "Skirt inside & outside, 50 mm (API 2218)"),
                ("Natural frequency / gust factor", f"{r['fn']:.2f} Hz / {r['wind']['G']:.2f}")]
        if packed:
            beds = [i for i in g["internals"] if i["kind"] == "bed"]
            INT = [(b["label"], f"{(b['z1'] - b['z0']):.2f} m, ID {b['D'] * 1000:.0f}") for b in beds]
            INT += [("Distributors", "4 (spray/trough), 316L"), ("Collector (chimney) trays", "3 total-draw, 316L, seal-welded"),
                    ("Flash zone", "Tangential vapour horn, 317L"), ("Stripping trays (boot)", f"4 x 2-pass valve trays @ 610"),
                    ("Demister", "Wire mesh 150 mm, 316L"), ("Manways", f"{sum(1 for n in g['nozzles'] if n['kind'] == 'MW')}")]
        else:
            nt = len(g["trays"])
            ps = sorted({tr["passes"] for tr in g["trays"]})
            INT = [("Number of trays", str(nt)), ("Tray type", "Valve trays (fixed/moving valves), 410S, 3 mm"),
                   ("Tray spacing", " / ".join(sorted({f'{tr["TS"] * 1000:.0f}' for tr in g["trays"]})) + " mm"),
                   ("Passes", " / ".join(str(p) for p in ps)),
                   ("Feed / draws", "See nozzle schedule"),
                   ("Manways", f"{sum(1 for n in g['nozzles'] if n['kind'] == 'MW')} x 24\"")]
        WT = [("Fabricated (shop) weight", f"{W['fabricated'] / 1e3:.1f} t"), ("Empty (installed)", f"{W['empty'] / 1e3:.1f} t"),
              ("Operating", f"{W['operating'] / 1e3:.1f} t"), ("Hydrotest (full of water)", f"{W['hydrotest'] / 1e3:.1f} t"),
              ("Wind base shear (strength)", f"{r['wind']['V_base'] / 1e3:.0f} kN"),
              ("Wind base moment (strength)", f"{r['wind']['M_base'] / 1e3:.0f} kNm")]
        noz = [[n["mark"], str(n.get("qty", 1)), nps_str(n["nps"]), f"{n['rating']}#",
                "RF" if n["rating"] < 600 else "RTJ", n["service"],
                ("Top head" if n["side"] == "T" else "Bottom head" if n["side"] == "B" else _el(r["skirt_h"] + n["z"])),
                f"{n['angle']} deg"] for n in g["nozzles"]]
        secs = [("kv", "General", S), ("kv", "Process & design conditions", PR), ("kv", "Materials", MAT),
                ("kv", "Mechanical design (CFU-000-ME-CAL-001)", MECH), ("kv", "Internals", INT), ("kv", "Weights & loads", WT),
                ("tbl", "Nozzle schedule", ["Mark", "Qty", "Size", "Rating", "Face", "Service", "Elevation", "Orient."],
                 noz, [6, 3, 5, 6, 4, 38, 13, 7])]
        if g.get("sections"):
            hs = []
            for s in g["sections"]:
                hs.append([s["name"], s.get("trays", "-"), fm(s["V_kg_h"] / 1000, 1), fm(s["L_kg_h"] / 1000, 1),
                           fm(s["rho_v"], 3), fm(s["rho_l"], 0), fm(s.get("FLV"), 3) if s.get("FLV") else "-",
                           fm(s.get("u_flood") or s.get("u_allow"), 2), fm(s["D_calc"], 2), str(s.get("passes", "-"))])
            secs.append(("tbl", "Hydraulic sections (process sizing)", ["Section", "Trays", "V (t/h)", "L (t/h)",
                                                                        "rho V", "rho L", "FLV", "u flood/allow", "D calc (m)", "Passes"],
                         hs, [20, 6, 6, 6, 6, 6, 6, 7, 7, 5]))
        secs.append(("note", "Notes", ["1. Thicknesses are FEED minimum nominal; fabricator to confirm by detailed calculation "
                                       "(cone junctions App. 1-5/1-8, nozzle reinforcement UG-37, local loads WRC 537).",
                                       "2. Orientation angles are preliminary - final by piping layout (CFU-PI).",
                                       "3. Steam-out vacuum: column not FV-rated unless noted - see CAL-001 S13."]))
        items.append(dict(tag=t, title=e["service"], area=e["area"], sections=secs))
    return items


def drums(calc):
    items = []
    dz = geometry.desalter()
    for t, r in calc["drums"].items():
        e = eq(t)
        W = r["W"]
        G = [("Tag / quantity", f"{t} / 1"), ("Service", e["service"]),
             ("Orientation / support", ("Horizontal, 2 saddles" if r["orient"] == "H" else "Vertical, legs")),
             ("Code", "ASME VIII Div.1 (U-stamp)"), ("Size (ID x T/T)", e["size"]),
             ("Volume", f"{r['Vol']:.1f} m3")]
        PR = [("Operating P / T", f"{e.get('op_P', '-')} barg / {e.get('op_T', '-')} C"),
              ("Design P / T", f"{r['Pd']} barg / {r['Td']:.0f} C"), ("External design P", "None (see note)"),
              ("MDMT", "-5 C"), ("Corrosion allowance", f"{r['CA']} mm"), ("Joint efficiency", f"{r['E']}"),
              ("Hydrotest pressure", f"{r['Pt']:.2f} barg"), ("Hold-up / residence",
                                                              f"{e.get('holdup_min') or e.get('residence_min')} min"),
              ("PWHT", "Yes (HIC-resistant / sour)" if "HIC" in e["moc"] else "No (code)"),
              ("Sour service", "NACE MR0103" if ("HIC" in e["moc"] or t in ("D-102", "D-201")) else "-")]
        MECH = [("Material shell / heads", r["mat"] + (" (HIC-tested)" if "HIC" in e["moc"] else "")),
                ("Shell t (req / nominal)", f"{r['t_req']:.1f} / {r['t_nom']} mm"),
                ("Head t 2:1 SE (req / nominal)", f"{r['t_head_req']:.1f} / {r['t_head_nom']} mm"),
                ("Boot", f"ID {r['boot']['D']} m x {r['boot']['L']} m" if r["boot"] else "-"),
                ("Bottom of shell elevation", _el(r["BOS_el"])), ("Insulation", f"{r['ins_mm']} mm" if r["ins_mm"] else "None"),
                ("Internals", "Electrostatic grids (AC/DC), inlet distributor, outlet collector, mud-wash" if
                 e["type"] == "Desalter" else "Inlet diverter, vortex breakers" + (", weir / boot" if r["boot"] else "")),
                ("Electrical (desalter)", "3 x transformers, 100 % reactance, 480 V / 16.5-23 kV" if e["type"] == "Desalter" else "-")]
        WT = [("Fabricated", f"{W['fabricated'] / 1e3:.1f} t"), ("Empty", f"{W['empty'] / 1e3:.1f} t"),
              ("Operating", f"{W['operating'] / 1e3:.1f} t"), ("Hydrotest", f"{W['hydrotest'] / 1e3:.1f} t")]
        secs = [("kv", "General", G), ("kv", "Design conditions", PR), ("kv", "Mechanical", MECH), ("kv", "Weights", WT)]
        if e["type"] == "Desalter":
            noz = [[n["mark"], str(n["qty"]), nps_str(n["nps"]), f"{n['rating']}#", "RF", n["service"],
                    f"{n['x']:.1f} m from LH TL"] for n in dz["nozzles"]]
            secs.append(("tbl", "Nozzle schedule (see GA CFU-100-ME-GA-007)",
                         ["Mark", "Qty", "Size", "Rating", "Face", "Service", "Location"], noz, [7, 3, 5, 6, 4, 45, 14]))
        else:
            secs.append(("note", "Nozzles", ["Nozzle sizes per P&ID line sizing (CFU-100/200-PR-PID); manway 24\" on "
                                             "head; PSV, vent 2\", drain 2\", steam-out 2\", LT/LG bridle 2\"."]))
        items.append(dict(tag=t, title=e["service"], area=e["area"], sections=secs))
    return items


def heaters(calc):
    items = []
    S = streams()
    R = results()
    for t, h in calc["heaters"].items():
        g, td, W = h["geo"], h["tube"], h["W"]
        hh = g["h"]
        e = eq(t)
        hot = t == "H-101"
        sin, sout = (S["6"], S["7"]) if hot else (S["19"], S["21"])
        PD = [("Heater type", f"{g['cells']}-cell cabin, horizontal tube" + (" (twin radiant cells, common convection)" if hot else "")),
              ("Service", e["service"]), ("Number required", "1"), ("Draft", "Balanced (FD + ID fans, APH E-120)" if hot
                                                                       else "Natural"),
              ("Total heat absorbed (process)", f"{hh['Q_proc_kw'] / 1000:.2f} MW"),
              ("Steam superheat coil", f"{hh.get('Q_ss_kw', 0) / 1000:.2f} MW" if hot else "-"),
              ("Total absorbed / fired (LHV)", f"{hh['Q_abs_kw'] / 1000:.2f} / {hh['Q_fired_kw'] / 1000:.2f} MW"),
              ("Efficiency (LHV, guaranteed)", f"{hh['eff'] * 100:.0f} %" + ("" if hot else " (see note 3)")),
              ("Fluid", "Desalted crude" if hot else "Atmospheric residue + coil steam"),
              ("Flow rate", f"{hh['flow'] / 1000:.1f} t/h"), ("Inlet T / outlet T", f"{hh['T_in']:.1f} / {hh['T_out']:.1f} C"),
              ("Inlet P / outlet P", f"{sin['P_barg']:.2f} / {sout['P_barg']:.2f} barg"),
              ("Outlet vaporisation (mass)", f"{hh['vf_out'] * 100:.1f} %"),
              ("Allowable / calc. pressure drop", f"{sin['P_barg'] - sout['P_barg']:.1f} bar / Vendor"),
              ("Mass velocity (radiant)", f"{hh['mass_flux']:.0f} kg/m2s"),
              ("Avg. radiant flux / max.", f"{td['q_avg']:.1f} / {td['q_max']:.1f} kW/m2"),
              ("Fouling factor", "0.0005 m2K/W" if hot else "0.0009 m2K/W"), ("Coking allowance / decoking",
                                                                              "Steam-air decoking + pigging connections")]
        CB = [("Fuel", "Refinery fuel gas, LHV 47 MJ/kg, MW 20, 3.5 barg"), ("Fuel consumption", f"{hh['fuel_kg_h']:.0f} kg/h"),
              ("Excess air (gas)", "15 %"), ("Flue gas flow", f"{g['fg_kg_s'] * 3.6:.0f} t/h"),
              ("Bridgewall temperature (est.)", f"{g['BWT']:.0f} C"),
              ("Flue gas leaving convection", f"{g['T_fg_out']:.0f} C"),
              ("Flue gas leaving APH / stack", "160 C" if hot else f"{g['T_fg_out']:.0f} C (see note 3)"),
              ("Combustion air preheat (APH E-120)", f"{g['aph_kw'] / 1000:.1f} MW" if hot else "-"),
              ("Ambient design", "35 C / -5 C min."), ("Emissions", "NOx <= 25 ppmv @ 3 % O2 (TBD by permit)"),
              ("Vac. off-gas burning", "-" if hot else "Dedicated off-gas tips (stream 28, 102 kg/h)")]
        n_conv = g["conv_rows"] * g["per_row"]
        CO = [("Section", "RADIANT  |  CONVECTION (shock / studded)"),
              ("Tube OD", f"168.3 mm (6\")  |  168.3 mm"), ("Tube wall (min. / selected)",
                                                          f"{td['t_min']:.2f} / {td['sched'][1]} mm ({td['sched'][0]})  |  Sch 40 min."),
              ("Tube material", "A335 P9 (9Cr-1Mo)  |  A335 P5 shock, A106 B studded"),
              ("Number of tubes", f"{g['rad_tubes']}  |  {n_conv} ({g['shock_rows']} shock rows)"),
              ("Effective length", f"{g['L_tube']} m  |  {g['L_tube']} m"), ("Passes", f"{g['passes']}"),
              ("Arrangement", f"Single row on side walls, {g['per_wall']} per wall per cell  |  {g['per_row']} per row, staggered"),
              ("Tube spacing", f"{g['pitch'] * 1000:.0f} mm (2 OD) / 1.5 OD from wall"),
              ("Radiant / convection surface", f"{hh['rad_area']:.0f} m2  |  {g['A_conv']:.0f} m2 bare-equiv."),
              ("Extended surface", "-  |  Studs 12.7 dia x 25 high, 11-13Cr (where TMT > 400 C), CS"),
              ("Elastic / rupture design pressure", f"{td['P_el'] * 10:.1f} / {td['P_r'] * 10:.1f} barg"),
              ("Design metal temperature", f"{td['Tdm']:.0f} C (API 530, EOR TMT {td['TMT']:.0f} C + 15 C)"),
              ("Corrosion allowance / design life", f"{td['CA']} mm / {td['life']:,} h"),
              ("Return bends", "Welded 180 deg LR, A234 WP9 (radiant) - plug headers on outlet for pigging: no"),
              ("Tube supports", "25Cr-20Ni (A297 HK40) radiant; 50Cr-50Ni-Nb shock / >870 C"),
              ("Hydrotest", f"{1.5 * td['P_el'] * 10:.1f} barg (1.5 x design)"),
              ("Coils", f"SS superheat {g['ss_rows']} rows" if hot else f"Utility coil {g['util_rows']} rows ({g['util_kw'] / 1000:.1f} MW, TBD)")]
        BU = [("Burner type", "Ultra-low-NOx, staged fuel gas, " + ("forced draft (preheated air)" if hot else "natural draft")),
              ("Number / arrangement", f"{g['burners']}, single row per cell, up-fired from floor ({g['burners_cell']} per cell)"),
              ("Spacing", f"{g['burner_pitch']:.2f} m"), ("Heat release design / max", f"{g['burner_mw']:.2f} / "
                                                                                      f"{g['burner_mw'] * 1.25:.2f} MW"),
              ("Burner CL to tube CL", f"{g['W_cl'] / 2:.2f} m (API 560 min.)"), ("Pilots / ignition", "Gas pilots, HEI"),
              ("Flame detection", "UV scanner per burner (BMS, NFPA 85 / API 556)"), ("Snuffing steam", "Firebox + header boxes")]
        ME = [("Overall dimensions L x W", f"{g['L_out']:.1f} x {g['W_out']:.1f} m (plot reservation {e['L']} x {e['W']} m)"),
              ("Radiant cell (inside) L x W x H", f"{g['L_box']:.1f} x {g['cell_in']:.2f} x {g['box_h']:.1f} m"),
              ("Floor elevation / clearance", f"{_el(g['floor'])} / 2.0 m below floor"),
              ("Convection section (inside) W x H", f"{g['conv_w']:.2f} x {g['conv_h']:.1f} m"),
              ("Stack ID / top elevation", f"{g['stack_D']:.1f} m / {_el(g['H_top'])}"),
              ("Refractory - radiant walls", "Ceramic fibre modules 200 mm (or IFB/castable 230 mm)"),
              ("Refractory - floor / arch", "IFB 65 mm + castable 150 mm / ceramic fibre 250 mm"),
              ("Refractory - convection", "Dual-layer castable 150 mm"), ("Casing temperature", "82 C max at 27 C, 0 m/s wind"),
              ("Structural / casing", "CS, ASCE 7 wind 150 mph"), ("Platforms", "Burner, header-box, convection, stack access"),
              ("APH / fans", "E-120 cast-iron/glass tube; K-101A/B FD 90 kW, K-102A/B ID 200 kW" if hot else "-"),
              ("Weight empty / operating", f"{W['empty'] / 1e3:.0f} / {W['operating'] / 1e3:.0f} t (+/-30 %)")]
        secs = [("kv", "Process design data", PD), ("kv", "Combustion data", CB), ("kv", "Coil design (API 530)", CO),
                ("kv", "Burners (API 535)", BU), ("kv", "Mechanical / casing / stack", ME),
                ("note", "Notes", ["1. Datasheet per API 560 5th ed. layout. Vendor to complete thermal rating and confirm TMTs.",
                                   "2. Tube design: API 530 elastic + rupture (100,000 h) - see CFU-000-ME-CAL-001 S10.",
                                   "3. " + ("BWT ~1040 C at 0.65 radiant fraction - vendor to optimise radiant surface."
                                            if hot else "88 % LHV needs ~1.4 MW utility coil or APH (not in equipment list) - HOLD."),
                                   "4. Plot dimensions in equipment.json are inconsistent with 18.3 m tubes for H-201 - see CAL-001 S13."])]
        items.append(dict(tag=t, title=e["service"], area=e["area"], sections=secs))
    return items


def _st_flows(x):
    """(shell flow, tube flow) kg/h and phase descriptions."""
    S = streams()
    R = results()
    hot, cold = x["hot_flow"], x["cold_flow"]
    t = x["tag"]
    Q = x["duty_kw"]
    cw = lambda: Q / (4.18 * 11) * 3600
    if t in ("E-101", "E-102", "E-103", "E-104", "E-106", "E-107", "E-108", "E-109", "E-110"):
        return cold, hot
    if t in ("E-105", "E-111"):
        return hot, cold
    if t == "E-113":
        return Q / 1990 * 3600, hot
    if t == "E-201":
        return Q / 2120 * 3600, hot
    if t == "E-114":
        return S["11"]["total_kg_h"], S["31"]["total_kg_h"]
    if t == "E-115":
        return S["8"]["total_kg_h"], cw()
    if t == "E-116":
        return R["stab"]["Q_reb"] / 300 * 3600, Q / 1700 * 3600
    if t == "E-117":
        return R["split"]["Q_reb"] / 320 * 3600 * 4, Q / 1990 * 3600
    if t == "E-118":
        return S["3"]["total_kg_h"], S["4"]["total_kg_h"]
    ej = {s["tag"]: s for s in R["ejector"]["stages"]}
    k = {"E-202": "J-201", "E-203": "J-202", "E-204": "J-203"}.get(t)
    if k:
        s = ej[k]
        return s["load_kg_h"] + s["motive_kg_h"], cw()
    return None, None


FOUL = {"Crude": 0.0005, "Vacuum residue": 0.0009, "Cooling water": 0.00035, "HP steam": 0.0001, "MP steam": 0.0001,
        "BFW / MP steam": 0.0002, "BFW / LP steam": 0.0002}


def shell_tube(calc):
    items = []
    for x in calc["st"]:
        e = eq(x["tag"])
        fs, ft = _st_flows(x)
        hot_shell = x["shellside"] in ("Vacuum residue", "OH vapour/condensate", "Steam / NCG", "Stabiliser bottoms") or \
            x["tag"] in ("E-105", "E-111")
        if x["tag"] in ("E-114",):
            hot_shell = False
        Ts_in, Ts_out = (x["Th_in"], x["Th_out"]) if hot_shell else (x["Tc_in"], x["Tc_out"])
        Tt_in, Tt_out = (x["Tc_in"], x["Tc_out"]) if hot_shell else (x["Th_in"], x["Th_out"])
        dn_s = nps_for_area((fs or 1) / 3600 / 750 / 2.0, 3)
        dn_t = nps_for_area((ft or 1) / 3600 / 750 / 2.0, 3)
        LM = x["LMTD"] * x["F"] if x.get("LMTD") and x.get("F") else None
        PF = [("Size / type (TEMA)", f"{x['size']}  (ID mm - tube length mm)"),
              ("Connected in", f"{x['parallel']} parallel x {x['series']} series"),
              ("Surface per unit (total) / per shell", f"{x['area_total']:.0f} / {x['area_shell']:.0f} m2"),
              ("Shells per unit", str(x["n_shells"])), ("Service", x["service"]), ("Heat exchanged", f"{x['duty_kw'] / 1000:.2f} MW"),
              ("MTD (corrected)", f"{LM:.1f} C" if LM else f"{(x['Th_in'] - x['Tc_out'] + x['Th_out'] - x['Tc_in']) / 2:.1f} C (approx.)"),
              ("Transfer rate, service (clean: vendor)", f"{x['U']:.0f} W/m2K")]
        SS = [("Fluid name (shell / tube)", f"{x['shellside']}  /  {x['tubeside']}"),
              ("Total flow (shell / tube)", f"{fm((fs or 0) / 1000, 1)} / {fm((ft or 0) / 1000, 1)} t/h"),
              ("Temperature in (shell / tube)", f"{Ts_in:.0f} / {Tt_in:.0f} C"),
              ("Temperature out (shell / tube)", f"{Ts_out:.0f} / {Tt_out:.0f} C"),
              ("Phase", "L / L" if "condenser" not in x["service"].lower() and "reboiler" not in x["service"].lower()
               and "generator" not in x["service"].lower() else "Two-phase (condensing / boiling)"),
              ("Physical properties", "Per H&MB / vendor simulation"),
              ("Allowable pressure drop (shell / tube)", "0.7 / 0.7 bar" if "Crude" in x["service"] else "0.35 / 0.7 bar"),
              ("Fouling resistance (shell / tube)", f"{FOUL.get(x['shellside'], 0.0004)} / {FOUL.get(x['tubeside'], 0.0004)} m2K/W")]
        CN = [("Design pressure (shell / tube)", f"{e['des_P']} barg"), ("Design temperature", f"{x['des_T']:.0f} C"),
              ("Test pressure (shell / tube)", f"{1.3 * x['P_shell']:.1f} / {1.3 * x['P_tube']:.1f} barg"),
              ("Passes per shell (shell / tube)", f"1 / {x['passes']}"), ("Corrosion allowance", f"{x['CA']} mm"),
              ("Connections in/out (shell)", f"{nps_str(dn_s)} {x['rating_shell']}#"),
              ("Connections in/out (tube)", f"{nps_str(dn_t)} {x['rating_tube']}#"),
              ("Tube no. / OD / thk / length", f"{x['Nt']} / {x['OD']} mm / {x['bwg']} / {x['L']} mm"),
              ("Tube pitch / layout", f"{x['pitch']:.2f} mm / {'30 deg' if x['pitch_type'] == 'tri' else '90 deg (square, cleanable)'}"),
              ("Tube material", x["moc"].split("/")[-1].strip()), ("Shell material / ID / thk",
                                                                   f"{x['shell_mat']} / {x['Ds']:.0f} mm / {x['t_shell']} mm"),
              ("Channel / bonnet thickness", f"{x['t_chan']} mm"), ("Tubesheet", "Vendor (TEMA R / ASME UHX)"),
              ("Floating head", "Split-ring (S)" if x["tema"].startswith(("AES",)) else ("U-tube" if "U" in x["tema"][:3] else "-")),
              ("Baffles", "Single segmental, cut 25 % (V) - spacing vendor"), ("Impingement protection", "Plate (rho.v2 > 2230)"),
              ("Expansion joint", "None"), ("Gaskets", "Double-jacketed / spiral-wound"),
              ("Code requirements", "ASME VIII-1 / TEMA R / API 660"), ("Bundle pull / removable", "Yes" if x["tema"][2] in "SUTX" else "Fixed TS"),
              ("Weight per shell empty / water filled", f"{x['empty'] / 1e3:.1f} / {x['hydrotest'] / 1e3:.1f} t"),
              ("Bundle weight (est.)", f"{x['Nt'] * x['L'] / 1000 * 1.55 * 1.35 / 1e3:.1f} t")]
        items.append(dict(tag=x["tag"], title=x["service"], area=x["area"],
                          sections=[("kv", "Performance of one unit", PF), ("kv", "Shell side / tube side", SS),
                                    ("kv", "Construction of one shell", CN),
                                    ("note", "Notes", ["1. TEMA datasheet layout. Thermal design (HTRI) by vendor - geometry here "
                                                       "is an estimate from area and the tube-count correlation.",
                                                       "2. Crude shell-side exchangers: square pitch, removable bundle, "
                                                       "1 m min. tube velocity (tube side) / no dead zones.",
                                                       "3. Stacking: max. 2 shells high; bundle-pull clearance = tube length + 1.5 m."])]))
    return items


def air_coolers(calc):
    items = []
    S = streams()
    R = results()
    trims = {t["tag"]: t for t in R["preheat"]["trims"]}
    flows = {"A-101": S["8"]["total_kg_h"], "A-106": S["30"]["total_kg_h"] + R["stab"]["reflux"],
             "A-107": S["32"]["total_kg_h"] + R["split"]["reflux"], "A-108": S["33"]["total_kg_h"]}
    for a in calc["ac"]:
        e = eq(a["tag"])
        fl = flows.get(a["tag"]) or trims.get(a["tag"], {}).get("flow")
        Ti, To = e["op_T"].split("(")[0].split("->")
        cond = "condenser" in a["service"].lower()
        PD = [("Service", a["service"]), ("Heat exchanged", f"{a['duty_kw'] / 1000:.2f} MW"),
              ("Fluid", "OH vapour + steam (sour)" if a["tag"] == "A-101" else a["service"].split(" ")[0]),
              ("Total flow", f"{fm((fl or 0) / 1000, 1)} t/h"), ("Phase", "Condensing" if cond else "Liquid"),
              ("Inlet / outlet temperature", f"{float(Ti):.0f} / {float(To):.0f} C"),
              ("Allowable pressure drop", "0.35 bar" if cond else "0.7 bar"), ("Fouling resistance", "0.00035 m2K/W"),
              ("Design air temperature in / out", f"{a['Tai']:.0f} / {a['Tao']:.0f} C"),
              ("Air flow (total)", f"{a['air_kg_s']:.0f} kg/s"), ("Elevation", "5 m ASL")]
        CO = [("Type / draft", f"{a['draft']} draft, pipe-rack mounted"), ("Bays (data) / bays required @ 6 rows",
                                                                           f"{a['bays']} / {a['bays_req_6rows']}"),
              ("Bay size", "6.0 m W x 12.0 m L"), ("Bundles per bay", "2"), ("Tube rows (calc. for data bays)", f"{a['rows']}"),
              ("Bare surface (total)", f"{a['area']:.0f} m2"), ("Extended surface (approx. x21)", f"{a['area'] * 21:,.0f} m2"),
              ("Tubes: OD / thk / length", "25.4 mm / 2.77 mm / 12.0 m"), ("Tube material", "A214 ERW CS" + (" + inlet ferrules" if a["tag"] == "A-101" else "")),
              ("Fins", "Al 1100, embedded (G-fin) 57.2 mm OD, 433 fins/m" if a["des_T"] > 230 else "Al 1100, L-footed / extruded, 57.2 mm OD"),
              ("Header type / plugs", f"{a['header']} / shoulder plugs, SS"), ("Design pressure / temperature",
                                                                               f"{a['des_P']} barg / {a['des_T']:.0f} C"),
              ("Test pressure", f"{a['des_P'] * 1.3:.1f} barg"), ("Corrosion allowance", "3 mm headers / 0 tubes"),
              ("Nozzle rating", f"{a['rating']}# RF"), ("Code", "ASME VIII-1 / API 661")]
        ME = [("Fans per bay / total", f"2 / {a['fans']}"), ("Fan diameter", f"{a['fan_D']:.1f} m (>= 40 % coverage)"),
              ("Blades / pitch", "FRP or Al; manual pitch, 1 auto-variable pitch fan per bay"),
              ("Motor rated / absorbed per fan", f"{a['motor_kw']} / {a['fan_kw']:.1f} kW"),
              ("Motor", "480 V, 3 ph, 60 Hz, TEFC, Ex nA / Class I Div 2" if a["motor_kw"] < 200 else "4.16 kV"),
              ("Drive", "HTD belt (<= 45 kW) / right-angle gear (> 45 kW)"), ("Speed control", "VFD on 1 fan per bay (TBD)"),
              ("Vibration switches", "Yes, each fan"), ("Louvres / winterisation", "None (Gulf Coast); A-101 inlet louvres optional"),
              ("Noise", "<= 85 dB(A) at 1 m below bundle"),
              ("Weight empty / operating (est.)", f"{a['empty'] / 1e3:.1f} / {a['operating'] / 1e3:.1f} t")]
        notes = ["1. API 661 datasheet layout. Thermal rating by vendor."]
        if a["rows"] > 8:
            notes.append(f"2. HOLD: {a['rows']} tube rows would be needed in {a['bays']} bay(s); {a['bays_req_6rows']} bays at "
                         f"6 rows recommended (see CAL-001 S13).")
        if a["Tao"] - a["Tai"] > 35:
            notes.append("3. HOLD: air outlet temperature in process data is too high - air flow to be re-optimised.")
        items.append(dict(tag=a["tag"], title=a["service"], area=a["eq_area"],
                          sections=[("kv", "Performance data", PD), ("kv", "Construction - tube bundle", CO),
                                    ("kv", "Mechanical equipment", ME), ("note", "Notes", notes)]))
    return items


def pumps(calc):
    items = []
    for p in calc["pumps"]:
        e = eq(p["tag"])
        qs = p["q_rated"] / 3600
        ns = nps_for_area(qs / 2.5)
        nd = nps_for_area(qs / 4.0)
        rating = max(300, flange_class(p["Pd_barg"] * 1.25, p["des_T"]))
        G = [("Applicable standard", "API 610 12th ed. / ISO 13709"), ("Pump type", f"{p['api610']}" +
                                                                          (" (double-suction 1st stage)" if p["double_suction"] else "")),
             ("Number of pumps", "2 (1 operating + 1 spare)" if p["spare"] else "1 (no spare - see note)"),
             ("Service", p["service"]), ("Driver", "Electric motor"), ("Suction source", p["source"])]
        OC = [("Liquid", p["service"]), ("Pumping temperature normal / design", f"{p['T']:.0f} / {p['des_T']} C"),
              ("Density at PT", f"{p['rho']:.0f} kg/m3"), ("Viscosity", "TBD (process)"),
              ("Vapour pressure", "Bubble point (= surface P)" if p["kind"] == "vessel" else ("Estimated" if p["Pv_est"] else "Water")),
              ("Rated / normal flow", f"{p['q_rated']:.1f} / {p['q_normal']:.1f} m3/h"),
              ("Suction pressure (rated)", f"{p['Ps_barg']:.2f} barg"), ("Discharge pressure", f"{p['Pd_barg']:.2f} barg"),
              ("Differential pressure / head", f"{p['dP']:.1f} bar / {p['head']:.0f} m"),
              ("NPSH available (est.)", f"{p['npsha']:.1f} m"), ("NPSH required (est., vendor)", f"{p['npshr_est']:.1f} m"),
              ("NPSH margin", f"{p['margin']:.1f} m"), ("Hydraulic power", f"{p['q_rated'] / 3600 * p['dP'] * 100:.1f} kW"),
              ("Corrosive / erosive", "Sour (H2S) / naphthenic" if p["T"] > 200 else "Sour" if "water" in p["service"].lower() else "-")]
        PERF = [("Speed (est.)", f"{p['speed']} rpm"), ("Stages", str(p["stages"])), ("Efficiency (est.)", f"{p['eta'] * 100:.0f} %"),
                ("Absorbed power (rated)", f"{p['bkw']:.1f} kW"), ("Motor rating", f"{p['motor']} kW"),
                ("Motor voltage", f"{p['voltage']}, 3 ph, 60 Hz"), ("Motor enclosure / area", "TEFC, Class I Div 2 Gr D / Zone 2 IIA T3"),
                ("Suction / discharge nozzle", f"{nps_str(ns)} / {nps_str(nd)} {rating}# RF (vendor)"),
                ("Casing MAWP", f"{max(p['Pd_barg'] * 1.25, 40):.0f} barg (incl. shut-off, TBD)"),
                ("Material class (API 610 Annex H)", p["moc"]), ("Mechanical seal", p["seal"] + ", API 682 Cat 2, Arr. 2"
                                                                 if "53B" in p["seal"] else p["seal"] + ", API 682 Cat 2, Arr. 1"),
                ("Bearings / lubrication", "Rolling / ring oil" if p["bkw"] < 300 else "Hydrodynamic / forced oil"),
                ("Coupling / baseplate", "Flexible disc spacer / API 610 grouted"),
                ("Minimum continuous flow", "Vendor (min. flow bypass if < 30 % rated)"),
                ("Weight pump+motor+base (est.)", f"{p['weight_t']:.1f} t each")]
        notes = ["1. Rated flow = 110 % normal (process). Heads per process sizing; hydraulic check by piping (CFU-PI).",
                 "2. NPSHr estimated with suction-specific speed 200 (metric, ~10,300 US); vendor to confirm NPSHr <= NPSHa - 1 m."]
        if p["q_rated"] < 2:
            notes.append("3. HOLD: flow below API 610 range - metering / PD pump recommended.")
        if p["tag"].startswith("P-112"):
            notes.append("3. HOLD: differential pressure inconsistent with H&MB stream 19 (see CAL-001 S13).")
        items.append(dict(tag=p["tag"], title=p["service"], area=p["area"],
                          sections=[("kv", "General", G), ("kv", "Operating conditions", OC), ("kv", "Performance / construction", PERF),
                                    ("note", "Notes", notes)]))
    return items


def psv(calc):
    items = []
    for p in calc["psv"]:
        GE = [("Tag / quantity", f"{p['tag']} / {p['count']}"), ("Protected equipment", p["protects"]),
              ("Governing case", p["case"]), ("Valve type", "Spring-loaded, full-nozzle, high-lift"),
              ("Bonnet", p["bonnet"]), ("Discharge to", p["dest"]),
              ("Size designation (API 526)", f"{p['designation']}  (inlet x orifice x outlet)"),
              ("Inlet flange / facing", f"{p['designation'].split(p['orifice'])[0]}\" {p['inlet_rating']}# RF"),
              ("Outlet flange / facing", f"{p['designation'].split(p['orifice'])[1]}\" {p['outlet_rating']}# RF")]
        SV = [("Fluid / state", "Hydrocarbon vapour" if p["MW"] > 20 else "Steam / vapour"),
              ("Required capacity (per valve)", f"{p['load_kg_h'] / p['count']:,.0f} kg/h"),
              ("Molecular weight", f"{p['MW']:.1f}"), ("Relieving temperature", f"{p['T']:.0f} C"),
              ("Cp/Cv (k) / Z", "1.10 / 1.0"), ("Set pressure", f"{p['set_barg']} barg"),
              ("Overpressure / accumulation", p["overpressure"]), ("Back pressure", p["backpressure"]),
              ("Kd / Kb / Kc", f"{p['Kd']} / {p['Kb']} / 1.0"),
              ("Required orifice area (total)", f"{p['area_mm2']:,.0f} mm2"),
              ("Selected orifice / effective area", f"{p['orifice']} / {p['A_eff']:,} mm2 each"),
              ("Utilisation", f"{p['util'] * 100:.0f} %"), ("Inlet loss limit", "< 3 % of set (API 520-II)")]
        MT = [("Body / bonnet", p["body"]), ("Nozzle / disc", "316 SS"), ("Spring", "CS, aluminised (W < 230 C) / tungsten (> 230 C)"),
              ("Bellows", "Inconel 625" if "bellows" in p["bonnet"].lower() else "-"), ("Trim", p["trim"]),
              ("Lifting lever / test gag", "No / Yes"), ("NACE", "MR0103 (sour)"), ("Code", "ASME VIII-1 UG-125..137, API 520/521/526/527")]
        items.append(dict(tag=p["tag"], title=f"Relief valve for {p['protects']}", area="CDU" if p["tag"][4] == "1" else "VDU",
                          sections=[("kv", "General", GE), ("kv", "Service conditions & sizing (API 520)", SV),
                                    ("kv", "Materials & accessories", MT),
                                    ("note", "Notes", ["1. API 526 datasheet layout. Sizing per process (data/psv.json); "
                                                       "vendor to confirm certified capacity (API 527 seat tightness).",
                                                       "2. Multiple valves: staggered set pressures (+5 %) where count > 1."])]))
    return items


CLASSES = [
    ("DS-001", "Columns", "ASME VIII Div.1 - columns & internals", columns),
    ("DS-002", "Drums & Desalters", "ASME VIII Div.1 - pressure vessels", drums),
    ("DS-003", "Fired Heaters", "API 560 / API 530 / API 535", heaters),
    ("DS-004", "Shell & Tube Exchangers", "TEMA R / API 660", shell_tube),
    ("DS-005", "Air Coolers", "API 661", air_coolers),
    ("DS-006", "Pumps", "API 610 12th ed. / API 682", pumps),
    ("DS-007", "Pressure Relief Valves", "API 526 / API 520", psv),
]


def build(calc):
    OUT.mkdir(parents=True, exist_ok=True)
    classes = []
    produced = []
    for code, name, std, fn in CLASSES:
        items = fn(calc)
        doc = f"CFU-000-ME-{code}"
        fname = OUT / f"{doc}_{name.replace(' & ', '-').replace(' ', '-')}-Datasheets.pdf"
        w = DSWriter(fname, doc, name.rstrip("s") if not name.endswith("ss") else name, std)
        for it in items:
            w.add(it)
        n = w.save()
        produced.append((fname, n))
        classes.append((name, doc, items))
    xl = OUT / "CFU-000-ME-DS-000_Equipment-Datasheets-Combined.xlsx"
    write_xlsx(xl, classes)
    produced.append((xl, len(classes)))
    return produced
