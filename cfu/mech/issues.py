"""Process-data issues found by the mechanical discipline (reported, not fixed upstream)."""
from __future__ import annotations

import math

from .common import eq, equipment, psvs, results, streams


def find(calc) -> list[tuple[str, str]]:
    out = []
    R = results()
    S = streams()
    E = {e["tag"]: e for e in equipment()}

    # C-201 top section diameter
    c201 = E["C-201"]
    secs = c201["sections"]
    b2 = secs[1]
    if b2["V_kg_h"] > 3 * secs[0]["V_kg_h"]:
        rv = b2["rho_v"] * 1.1
        Q = b2["V_kg_h"] / 3600 / rv
        u = 0.11 / math.sqrt(rv / (b2["rho_l"] - rv))
        D = math.sqrt(4 * Q / u / math.pi)
        out.append(("C-201", f"Top section ID {c201['D3']} m is sized on vapour leaving the top of bed 1 "
                             f"({secs[0]['V_kg_h'] / 1000:.0f} t/h). Vapour entering the bottom of bed 1 is ~ vapour "
                             f"leaving bed 2 ({b2['V_kg_h'] / 1000:.0f} t/h), which needs ID ~{D:.1f} m at Cs 0.11. "
                             f"Recommend process re-rate bed 1 at its bottom; GA drawn per equipment.json (hold)."))
    # heater tube length vs heater length
    for t in ("H-101", "H-201"):
        g = calc["heaters"][t]["geo"]
        if g["L_out"] > E[t]["L"] + 0.1:
            out.append((t, f"equipment.json L = {E[t]['L']} m cannot house {g['L_tube']} m horizontal radiant tubes; "
                           f"cabin incl. header boxes is {g['L_out']:.1f} m long. Plot reservation must be >= "
                           f"{g['L_out'] + 2:.0f} m (incl. tube-pulling at one end handled by crane)."))
        td = calc["heaters"][t]["tube"]
        if td["Tdm"] > E[t]["des_T"]:
            out.append((t, f"des_T {E[t]['des_T']} C in equipment.json is below the API 530 design metal temperature "
                           f"{td['Tdm']} C (estimated EOR TMT {td['TMT']:.0f} C + 15 C). Use {td['Tdm']} C for coil "
                           f"design / datasheet."))
    g1 = calc["heaters"]["H-101"]["geo"]
    if g1["BWT"] > 950:
        out.append(("H-101", f"Radiant fraction 0.65 (basis.DESIGN) gives an estimated bridgewall temperature of "
                             f"{g1['BWT']:.0f} C with APH; API 560 practice <= ~900-950 C. Suggest radiant fraction ~0.70 "
                             f"(more radiant surface) - vendor to optimise."))
    g2 = calc["heaters"]["H-201"]["geo"]
    if g2["util_kw"] > 100:
        out.append(("H-201", f"88 % efficiency is not achievable with process convection alone: charge enters at "
                             f"{g2['h']['T_in']:.0f} C, so flue gas cannot be cooled below ~{g2['h']['T_in'] + 50:.0f} C "
                             f"(max. process convection {g2['Q_conv_max'] / 1000:.1f} MW vs {g2['Q_conv_proc'] / 1000:.1f} MW "
                             f"assumed). ~{g2['util_kw'] / 1000:.1f} MW must go to a utility coil (steam superheat / BFW) "
                             f"or an APH - none exists in equipment.json. Also vacuum-heater outlet tubes normally step up "
                             f"in size (6\"->8\"->10\") - all tubes are 6\" in the data."))
    # pumps
    for p in calc["pumps"]:
        if p["tag"].startswith("P-112"):
            s19 = S["19"]["P_barg"]
            if s19 - p["Pd_barg"] > 2:
                out.append(("P-112A/B", f"Rated dP {p['dP']:.0f} bar gives discharge ~{p['Pd_barg']:.1f} barg but "
                                        f"H&MB stream 19 (P-112 -> H-201) is at {s19:.1f} barg: dP should be "
                                        f"~{s19 - p['Ps_barg']:.0f} bar (head ~{(s19 - p['Ps_barg']) * 1e5 / (p['rho'] * 9.81):.0f} m)."))
        if p["q_rated"] < 2:
            out.append((p["tag"], f"Rated flow {p['q_rated']:.2f} m3/h at {p['head']:.0f} m is outside the centrifugal "
                                  f"(API 610) range - use a positive-displacement / metering pump (API 674/675)."))
    if not E.get("P-118A/B") and E.get("P-118"):
        out.append(("P-118", "Single pump without spare (desalter mud-wash/recycle) - confirm intermittent duty."))
    # stream 24 source
    if S["24"]["frm"] == "E-202":
        out.append(("Stream 24", "HVGO product 'frm' is E-202 (ejector intercondenser); should be A-202 (HVGO product "
                                 "cooler)."))
    if "C-102A-C" in S["20"]["to"]:
        out.append(("Stream 20", "Destination 'C-102A-C' - strippers are tagged C-102/C-103/C-104."))
    # air coolers
    for a in calc["ac"]:
        if a["rows"] > 8:
            out.append((a["tag"], f"{a['area']:.0f} m2 bare in {a['bays']} bay(s) of 6 x 12 m needs {a['rows']} tube rows "
                                  f"(>8, not practical); {a['bays_req_6rows']} bays at 6 rows required. Plot space "
                                  f"/ fan count to be revised."))
        if a["Tao"] - a["Tai"] > 35:
            out.append((a["tag"], f"Air temperature rise {a['Tai']:.0f}->{a['Tao']:.0f} C is unrealistically high "
                                  f"(typ. 15-25 C); air flow and bundle size will increase."))
    # X-104 area
    x = E.get("X-104")
    if x and x["area"] == "CDU" and "VDU" in x["service"]:
        out.append(("X-104", "Area 'CDU' but service is VDU overhead (area 200) - sizing.py tests '\"10\" in tag'."))
    d102 = E["D-102"]
    if "6 mm CA" in d102["moc"] and d102["ca_mm"] != 6:
        out.append(("D-102", f"moc states 6 mm CA but ca_mm = {d102['ca_mm']}; mechanical design uses 6 mm."))
    # steam reboiler design temperatures
    for t, stm in (("E-116", ("HP steam", 400)), ("E-117", ("MP steam", 250))):
        if E[t]["des_T"] < stm[1]:
            out.append((t, f"Tube-side {stm[0]} header is superheated ({stm[1]} C) but des_T = {E[t]['des_T']} C - "
                           f"design temperature must cover the steam supply ({stm[1]} C) unless a desuperheater is added."))
    # PSV
    for p in psvs():
        if p["count"] > 1:
            out.append((p["tag"], f"{p['count']} x {p['orifice']} orifices for '{p['case']}' ({p['load_kg_h'] / 1000:.0f} t/h, "
                                  f"set {p['set_barg']} barg vs MAWP {eq('C-101')['des_P']} barg). Raising set to MAWP and "
                                  f"crediting unaffected pumparound duty (API 521 4.4.3) should reduce this."))
        if "/" in p["protects"]:
            out.append((p["tag"], f"One PSV protects {p['protects']}: requires no isolation between the vessels "
                                  f"(locked-open valves) - confirm in P&ID."))
    # exchanger shell D vs bundle
    big = [d for d in calc["st"] if d["D_eq"] and d["Ds"] / 1000 > d["D_eq"] + 0.15]
    if big:
        out.append(("E-1xx/2xx", "Shell IDs from tube-count/bundle correlation exceed equipment.json 'D' for: " +
                    ", ".join(f"{d['tag']} {d['Ds'] / 1000:.2f} vs {d['D_eq']}" for d in big) +
                    " m (kettles include the enlarged shell)."))
    # weight estimates
    for t in ("C-101", "C-201"):
        w = calc["columns"][t]["W"]["empty"] / 1000
        if E[t].get("weight_t") and abs(E[t]["weight_t"] - w) / w > 0.3:
            out.append((t, f"equipment.json weight_t {E[t]['weight_t']:.0f} t (rule of thumb) vs calculated empty "
                           f"{w:.0f} t / operating {calc['columns'][t]['W']['operating'] / 1000:.0f} t - use data/mech.json."))
    # vacuum design of other vessels
    nfv = [t for t, d in calc["drums"].items() if d["Pa_ext"] < 0.1034]
    out.append(("Design P", "Only C-201 (and ejector condensers) carry FV. Columns C-101..C-106 and drums " +
                ", ".join(nfv) + " are not full-vacuum capable as designed; refinery practice is FV for steam-out "
                "(or written steam-out procedure + vacuum breakers). Process to confirm."))
    # process_results vs equipment consistency
    pr = R["preheat"]["exch"][0]["Q_kw"]
    if abs(pr - E["E-101"]["duty_kw"]) > 1:
        out.append(("Data sync", f"process_results.json (E-101 Q {pr:.0f} kW, CIT {R['preheat']['CIT']:.1f} C) differs "
                                 f"slightly from equipment.json (E-101 {E['E-101']['duty_kw']:.0f} kW) - files written "
                                 f"from different iterations; regenerate together."))
    if E["C-101"]["D2"] != round(E["C-101"]["D2"], 1):
        out.append(("C-101", f"Stripping-section ID {E['C-101']['D2']} m (= 0.6 x main ID) is not rounded; size string "
                             f"says 4.1 m. Hydraulically {next(s for s in E['C-101']['sections'] if s['name'] == 'Stripping')['D_calc']:.1f} m "
                             f"suffices; mechanical uses {E['C-101']['D2']} m as given."))
    return out
