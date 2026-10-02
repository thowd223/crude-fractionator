"""Control valve sizing per ANSI/ISA-75.01.01 (IEC 60534-2-1) for key valves - FEED.

Liquids:  Cv = Q / N1 * sqrt(G / dP_s),  N1 = 0.865 (Q m3/h, dP bar), dP_s = min(dP, FL^2 (P1 - FF Pv))
Gases:    W  = N6 Fp Cv Y sqrt(x P1 rho1), N6 = 27.3 (W kg/h, P bar(a), rho kg/m3), Y = 1 - x/(3 Fk xT),
          x limited to Fk xT (choked).
Flows and densities from data/streams.json / process_results.json / equipment.json; valve dP allocations
are FEED engineering judgement (stated per valve). Sizing case = 1.2 x normal flow (max), check case =
0.5 x normal (turndown). Body = smallest standard size with travel at Cv_max <= 90 % (equal %, R = 50) /
85 % (linear) and travel at Cv_min >= 10 %.
"""
from __future__ import annotations

import math

from .common import load, pr, streams

N1, N6 = 0.865, 27.3
RATED = {  # globe valve rated Cv (full-port, typical) by NPS
    1: 14, 1.5: 32, 2: 55, 3: 120, 4: 200, 6: 430, 8: 750, 10: 1100, 12: 1500, 14: 2000, 16: 2600}
BALL = {6: 900, 8: 1700, 10: 2700, 12: 4000, 14: 5200, 16: 7000, 18: 9000, 20: 11500, 24: 17000}
R_EQ = 50.0


def _eq_travel(cv, cvr, char):
    f = cv / cvr
    if f <= 0:
        return 0
    if char == "Linear":
        return 100 * f
    return max(0.0, 100 * (1 + math.log(f) / math.log(R_EQ)))


def _select(cv_max, cv_min, char, large=False):
    lim = 90.0 if char != "Linear" else 85.0
    table = BALL if large else RATED
    for nps, cvr in sorted(table.items()):
        if _eq_travel(cv_max, cvr, char) <= lim:
            return nps, cvr, _eq_travel(cv_max, cvr, char), _eq_travel(cv_min, cvr, char)
    nps, cvr = max(table.items())
    return nps, cvr, _eq_travel(cv_max, cvr, char), _eq_travel(cv_min, cvr, char)


def valves():
    S = streams()
    R = pr()
    E = {e["tag"]: e for e in load("equipment.json")}
    pdp = lambda t: E[t]["dP_bar"]
    A, V = R["atm"], R["vac"]
    mpa = R["atm"]["pa"]
    hv = V["pa"]["HVGO"]
    rho_hvgo = next(s for s in V["sections"] if "HVGO PA" in s["name"])["rho_l"]
    vr_hot = S["26"]["rho_liq"] * (1 - 0.0007 * (V["T_bot"] - S["26"]["T_C"]))
    q_reb = R["stab"]["Q_reb"]
    fuel = R["heaters"]["H-101"]["fuel_kg_h"]
    L = []
    # liquid: tag, service, Q m3/h (normal), rho, P1 barg, dP bar, Pv bara, Pc bara, FL, char, basis
    L += [
        dict(tag="FV-1001", svc="Crude charge (P-101 disch.)", ph="L", q=S["1"]["liq_act_m3h"], rho=S["1"]["rho_liq"],
             p1=S["1"]["P_barg"] + pdp("P-101A/B"), dp=3.0, pv=1.0, pc=25, fl=0.85, char="Equal %",
             basis="dP = 3.0 bar (~14 % of P-101 dP); RVP-limited Pv", large=True),
        dict(tag="FV-1003", svc="Desalter wash water (P-114)", ph="L", q=S["3"]["total_kg_h"] / 943.0, rho=943.0,
             p1=S["3"]["P_barg"] + 1.0, dp=3.0, pv=2.1, pc=221, fl=0.90, char="Equal %",
             basis="water at 121 °C (Pv 2.1 bara)"),
        dict(tag="LV-1007", svc="D-101A brine to E-118", ph="L", q=S["4"]["total_kg_h"] / 950.0, rho=950.0,
             p1=11.5, dp=11.5 - S["4"]["P_barg"], pv=3.3, pc=221, fl=0.90, char="Linear",
             basis="desalter 11.5 barg -> brine header; check flashing"),
        dict(tag="FV-1031", svc="C-101 reflux (P-103)", ph="L", q=S["10"]["liq_act_m3h"], rho=S["10"]["rho_liq"],
             p1=A["drum_P_barg"] + pdp("P-103A/B"), dp=2.0, pv=A["drum_P_barg"] + 1.013, pc=30, fl=0.90,
             char="Equal %", basis="bubble-point liquid from D-102"),
        dict(tag="FV-1034", svc="Unstab. naphtha to C-105 (P-104)", ph="L", q=S["11"]["liq_act_m3h"],
             rho=S["11"]["rho_liq"], p1=A["drum_P_barg"] + pdp("P-104A/B"), dp=3.0, pv=A["drum_P_barg"] + 1.013,
             pc=30, fl=0.90, char="Equal %", basis="C-105 at 10.8 barg + E-114 + static"),
        dict(tag="FV-1040", svc="TPA circulation (P-106)", ph="L", q=S["13"]["liq_act_m3h"], rho=S["13"]["rho_liq"],
             p1=A["P_top_barg"] + pdp("P-106A/B"), dp=1.5, pv=A["P_top_barg"] + 1.013, pc=25, fl=0.90,
             char="Equal %", basis="tray-draw (bubble point) liquid"),
        dict(tag="FV-1042", svc="MPA circulation (P-107)", ph="L", q=S["14"]["liq_act_m3h"], rho=S["14"]["rho_liq"],
             p1=A["P_top_barg"] + pdp("P-107A/B"), dp=1.5, pv=A["P_top_barg"] + 1.1, pc=22, fl=0.90,
             char="Equal %", basis="tray-draw (bubble point) liquid"),
        dict(tag="FV-1044", svc="BPA circulation (P-108)", ph="L", q=S["15"]["liq_act_m3h"], rho=S["15"]["rho_liq"],
             p1=A["P_top_barg"] + pdp("P-108A/B"), dp=1.5, pv=A["P_top_barg"] + 1.2, pc=20, fl=0.90,
             char="Equal %", basis="tray-draw (bubble point) liquid"),
        dict(tag="FV-1052", svc="Kerosene product (P-109)", ph="L", q=S["16"]["liq_act_m3h"], rho=S["16"]["rho_liq"],
             p1=S["16"]["P_barg"] + 4.0, dp=2.0, pv=0.1, pc=20, fl=0.90, char="Equal %",
             basis="cooled product to OSBL rundown"),
        dict(tag="FV-1062", svc="Diesel product (P-110)", ph="L", q=S["17"]["liq_act_m3h"], rho=S["17"]["rho_liq"],
             p1=S["17"]["P_barg"] + 4.0, dp=2.0, pv=0.05, pc=18, fl=0.90, char="Equal %",
             basis="cooled product to OSBL rundown"),
        dict(tag="FV-1083", svc="Atm. residue to H-201 (P-112)", ph="L", q=S["19"]["liq_act_m3h"],
             rho=S["19"]["rho_liq"], p1=S["19"]["P_barg"], dp=2.5, pv=A["P_fz_barg"] + 1.013 + 1.0, pc=15, fl=0.85,
             char="Equal %", basis="H-201 4-pass coil dP + transfer line downstream"),
        dict(tag="FV-2016", svc="HVGO PA circulation (P-202)", ph="L", q=hv["flow"] / rho_hvgo, rho=rho_hvgo,
             p1=pdp("P-202A/B") - 1.0, dp=1.5, pv=0.06, pc=12, fl=0.90, char="Equal %",
             basis="vacuum draw: Pv ~ column pressure; static head provides subcooling"),
        dict(tag="FV-2025", svc="Vacuum residue (P-204)", ph="L", q=S["26"]["total_kg_h"] / vr_hot, rho=vr_hot,
             p1=pdp("P-204A/B") - 1.0, dp=3.0, pv=0.07, pc=10, fl=0.85, char="Equal %",
             basis=f"hot VR at {V['T_bot']:.0f} °C (rho corrected), before E-111/E-105"),
    ]
    # gases: tag, svc, W kg/h normal, MW, T C, P1 bara, P2 bara, k, xT
    G = [
        dict(tag="PV-1021", svc="H-101 fuel gas to burners", ph="G", w=fuel, mw=20.0, t=30.0,
             p1=S["34"]["P_barg"] + 1.013, p2=2.0 + 1.013, k=1.27, xt=0.70, char="Equal %",
             basis="burner max 2.0 barg at design firing; FG header 3.5 barg"),
        dict(tag="PV-1032A", svc="D-102 off-gas to FG / flare", ph="G", w=0.05 * S["8"]["total_kg_h"], mw=50.0,
             t=45.0, p1=A["drum_P_barg"] + 1.013, p2=0.2 + 1.013, k=1.12, xt=0.70, char="Equal %",
             basis="design: 5 % of OH vapour (light-crude / start-up non-condensables) - assumption"),
        dict(tag="PV-1032B", svc="FG make-up to D-102", ph="G", w=500.0, mw=20.0, t=30.0,
             p1=S["34"]["P_barg"] + 1.013, p2=A["drum_P_barg"] + 1.013, k=1.27, xt=0.70, char="Equal %",
             basis="blanketing make-up 500 kg/h - assumption"),
        dict(tag="PV-2010", svc="C-201 vacuum: NCG spill-back to J-201", ph="G",
             w=3 * R["ejector"]["offgas"] + 200.0, mw=25.0, t=45.0, p1=1.1, p2=V["P_top_mbar"] / 1000, k=1.3,
             xt=0.70, char="Equal %", basis="3 x NCG load + 200 kg/h steam; choked (x > Fk xT)"),
        dict(tag="FV-1096", svc="HP steam to E-116 (C-105 reboiler)", ph="G", w=q_reb * 3600 / 1700.0, mw=18.0,
             t=400.0, p1=41.4 + 1.013, p2=0.85 * (41.4 + 1.013), k=1.30, xt=0.70, char="Equal %",
             basis="latent ~1700 kJ/kg at shell P; dP 15 % of P1"),
    ]
    out = []
    for v in L:
        for case, f in (("max", 1.2), ("norm", 1.0), ("min", 0.5)):
            pass
        P1a = v["p1"] + 1.013
        FF = 0.96 - 0.28 * math.sqrt(min(v["pv"] / v["pc"], 1.0))
        dpmax = v["fl"] ** 2 * (P1a - FF * v["pv"])
        dps = min(v["dp"], dpmax)
        G_ = v["rho"] / 1000
        cvn = v["q"] / N1 * math.sqrt(G_ / dps)
        cvx, cvm = 1.2 * cvn, 0.5 * cvn
        P2a = P1a - v["dp"]
        regime = "choked" if v["dp"] > dpmax else "flashing" if P2a < v["pv"] else "normal"
        nps, cvr, tmax, tmin = _select(cvx, cvm, v["char"], v.get("large", False) and cvx > 1000)
        out.append(dict(tag=v["tag"], service=v["svc"], phase="Liquid", flow=f"{v['q']:.1f} m3/h",
                        dens=f"{v['rho']:.0f}", p1=round(P1a, 2), dp=round(v["dp"], 2), cv_norm=round(cvn, 1),
                        cv_max=round(cvx, 1), cv_min=round(cvm, 1), regime=regime, nps=nps, cv_rated=cvr,
                        travel_max=round(tmax), travel_min=round(tmin), char=v["char"],
                        body="Segmented ball" if v.get("large") and cvx > 1000 else "Globe", basis=v["basis"]))
    for v in G:
        T = v["t"] + 273.15
        rho1 = v["p1"] * 1e5 * v["mw"] / (8314.0 * T)
        Fk = v["k"] / 1.4
        x = (v["p1"] - v["p2"]) / v["p1"]
        xc = min(x, Fk * v["xt"])
        Y = 1 - xc / (3 * Fk * v["xt"])
        cvn = v["w"] / (N6 * Y * math.sqrt(xc * v["p1"] * rho1))
        cvx, cvm = 1.2 * cvn, 0.5 * cvn
        nps, cvr, tmax, tmin = _select(cvx, cvm, v["char"])
        out.append(dict(tag=v["tag"], service=v["svc"], phase="Gas/vapour", flow=f"{v['w']:.0f} kg/h",
                        dens=f"{rho1:.2f}", p1=round(v["p1"], 2), dp=round(v["p1"] - v["p2"], 2),
                        cv_norm=round(cvn, 1), cv_max=round(cvx, 1), cv_min=round(cvm, 1),
                        regime="choked" if x >= Fk * v["xt"] else f"Y={Y:.2f}", nps=nps, cv_rated=cvr,
                        travel_max=round(tmax), travel_min=round(tmin), char=v["char"], body="Globe",
                        basis=v["basis"]))
    return out


def write_xlsx(rows, path):
    from openpyxl import Workbook
    from openpyxl.styles import Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    ws = wb.active
    ws.title = "CV sizing"
    ws["A1"] = "CFU-000-IC-CAL-001  CONTROL VALVE SIZING (ISA-75.01.01) - FEED, Rev A"
    ws["A1"].font = Font(bold=True, size=13)
    for i, ln in enumerate(__doc__.strip().splitlines(), 2):
        ws.cell(i, 1, ln)
    heads = ["Tag", "Service", "Phase", "Normal flow", "Density kg/m3", "P1 bar(a)", "dP bar", "Cv normal",
             "Cv max (1.2x)", "Cv min (0.5x)", "Regime", "Body", "Size NPS", "Rated Cv", "Travel max %",
             "Travel min %", "Characteristic", "Basis / assumption"]
    keys = ["tag", "service", "phase", "flow", "dens", "p1", "dp", "cv_norm", "cv_max", "cv_min", "regime", "body",
            "nps", "cv_rated", "travel_max", "travel_min", "char", "basis"]
    r0 = 13
    thin = Side(style="thin", color="999999")
    bd = Border(left=thin, right=thin, top=thin, bottom=thin)
    for j, h in enumerate(heads, 1):
        c = ws.cell(r0, j, h)
        c.fill, c.font, c.border = PatternFill("solid", fgColor="1F3864"), Font(color="FFFFFF", bold=True), bd
    for i, r in enumerate(rows, r0 + 1):
        for j, k in enumerate(keys, 1):
            ws.cell(i, j, r[k]).border = bd
    for j, w in enumerate([10, 34, 10, 12, 9, 8, 7, 9, 9, 9, 9, 13, 8, 8, 8, 8, 11, 60], 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    wb.save(path)
