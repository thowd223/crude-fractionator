"""Phase-0 reports: Basis of Design and Process Design Report (calculation summary)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import assay, basis, docgen, hmb, sizing

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "00-basis"
FIG = OUT / "figures"
D = basis.DESIGN


def _j(name):
    return json.loads((ROOT / "data" / name).read_text())


def tbl(header, rows):
    s = "| " + " | ".join(header) + " |\n|" + "---|" * len(header) + "\n"
    for r in rows:
        s += "| " + " | ".join(str(x) for x in r) + " |\n"
    return s + "\n"


# ---------------------------------------------------------------------------
def figures(m):
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3})
    sl = m.sl
    # 1. TBP with cut points and product distributions
    pts = basis.CRUDE["tbp"]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot([p[0] for p in pts], [p[1] for p in pts], "o-", color="#1F3864", lw=2, label="Crude TBP (assay)")
    for nm, T in basis.CUTS_ATM + basis.CUTS_VAC:
        ax.axhline(T, color="#999", ls="--", lw=0.8)
        ax.text(101, T, f"{nm} | {T} C", va="center", fontsize=7.5)
    ax.set_xlabel("Cumulative liquid volume, %")
    ax.set_ylabel("TBP temperature, C")
    ax.set_xlim(0, 100)
    ax.set_title("Arab Light TBP curve and product cut points")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "tbp.png", dpi=160)
    plt.close(fig)
    # 2. product TBP distributions (overlap)
    a, v = m.res["atm"], m.res["vac"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    prods = [("Naphtha (OH)", a["prod"]["NAPH"]), ("Kerosene", a["prod"]["KERO"]), ("Diesel", a["prod"]["DIESEL"]),
             ("AGO", a["prod"]["AGO"]), ("LVGO", v["lvgo"]), ("HVGO", v["hvgo"]), ("Slop wax", v["slop"]),
             ("VR", v["vr"])]
    for nm, p in prods:
        frac = p / np.maximum(m.crude, 1e-9)
        ax.plot(sl.Tb, frac * 100, lw=1.6, label=nm)
    ax.set_xlim(0, 750)
    ax.set_xlabel("Pseudo-component NBP, C")
    ax.set_ylabel("% of component to product")
    ax.set_title("Product split by pseudo-component (sloppy-split model)")
    ax.legend(ncol=4, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(FIG / "splits.png", dpi=160)
    plt.close(fig)
    # 3. column temperature profile
    fig, ax = plt.subplots(figsize=(5.5, 6))
    n = np.arange(1, 42)
    T = [a["T_tray"](i) for i in n]
    ax.plot(T, n, "-", color="#C00000", lw=2)
    for k, t in a["tray"].items():
        if k in ("KERO", "DIESEL", "AGO", "TPA_draw", "MPA_draw", "BPA_draw", "wash_bot"):
            ax.annotate(k, (a["T_tray"](t), t), xytext=(8, 0), textcoords="offset points", fontsize=7.5, va="center")
    ax.invert_yaxis()
    ax.set_xlabel("Temperature, C")
    ax.set_ylabel("Tray (1 = top)")
    ax.set_title("C-101 temperature profile (design)")
    fig.tight_layout()
    fig.savefig(FIG / "c101_profile.png", dpi=160)
    plt.close(fig)
    # 4. preheat train composite
    ex = m.res["preheat"]["exch"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    q = 0.0
    for e in ex:
        q1 = q + e["Q_kw"] / 1000
        ax.plot([q, q1], [e["Tc_in"], e["Tc_out"]], "-", color="#1F3864", lw=2)
        ax.plot([q, q1], [e["Th_out"], e["Th_in"]], "-", color="#C00000", lw=1.2)
        ax.text((q + q1) / 2, e["Th_in"] + 6, e["tag"], fontsize=6.8, ha="center", rotation=90)
        q = q1
    ax.axhline(m.res["preheat"]["T_desalter"], ls=":", color="green")
    ax.text(1, m.res["preheat"]["T_desalter"] + 4, "Desalter", color="green", fontsize=8)
    ax.set_xlabel("Cumulative duty to crude, MW")
    ax.set_ylabel("Temperature, C")
    ax.set_title(f"Crude preheat train (blue = crude, red = hot side) - CIT {m.res['preheat']['CIT']:.0f} C")
    fig.tight_layout()
    fig.savefig(FIG / "preheat.png", dpi=160)
    plt.close(fig)
    # 5. column vapour/liquid loading
    fig, ax = plt.subplots(figsize=(8, 3.8))
    secs = a["sections"]
    x = np.arange(len(secs))
    ax.bar(x - 0.2, [s["V_kg_h"] / 1000 for s in secs], 0.4, label="Vapour t/h", color="#1F3864")
    ax.bar(x + 0.2, [s["L_kg_h"] / 1000 for s in secs], 0.4, label="Liquid t/h", color="#8EA9DB")
    ax.set_xticks(x, [s["name"] for s in secs], rotation=25, ha="right", fontsize=7.5)
    ax.set_title("C-101 section traffic")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "c101_loads.png", dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------
def bod():
    P, C, S, U = basis.PROJECT, basis.CRUDE, basis.SITE, basis.UTILITIES
    md = f"""# 1 Introduction
This Basis of Design (BoD) defines the design premises for the {P['name']} ({P['short']}). It is the governing
input for every deliverable in the FEED package; all numbers below are read by the calculation code in
`cfu/basis.py`, so this document and the calculations cannot diverge.

## 1.1 Scope
- Crude receipt from OSBL tankage, two-stage electrostatic desalting, crude preheat train (cold and hot trains).
- Atmospheric crude charge heater H-101 and atmospheric fractionator C-101 with three pumparounds and side strippers
  for kerosene, diesel and AGO.
- Overhead condensing system, naphtha stabiliser (debutaniser) C-105 and naphtha splitter C-106.
- Vacuum heater H-201, wet packed vacuum column C-201, three-stage steam ejector system and hotwell.
- Unit utility distribution (steam, BFW, CW, fuel gas, nitrogen, instrument air), unit flare knock-out, closed drains.
- Excluded (interfaces only): tankage, sour water stripper, LPG treating, flare stack, wastewater treatment,
  fuel gas production, central control room, main substation.

## 1.2 Capacity and operating envelope
{tbl(["Item", "Value"], [
        ["Design capacity", f"{basis.CAPACITY_BPSD:,} BPSD (stream day)"],
        ["On-stream factor", f"{basis.STREAM_FACTOR:.0%} (8,322 h/y)"],
        ["Turndown", f"{basis.TURNDOWN:.0%} of design"],
        ["Hydraulic design margin", f"{basis.DESIGN_MARGIN - 1:.0%} on normal flows (pumps, lines, control valves)"],
        ["Run length", "5 years between turnarounds"]])}

# 2 Feedstock
{tbl(["Property", "Design crude", "Check crude"], [
        ["Name", C['name'], basis.CHECK_CRUDE['name']],
        ["API gravity", C['api'], basis.CHECK_CRUDE['api']],
        ["Sulfur, wt%", C['sulfur_wt'], basis.CHECK_CRUDE['sulfur_wt']],
        ["Salt as received, PTB", C['salt_ptb'], "30"],
        ["BS&W, vol%", C['bsw_vol'], "0.5"],
        ["TAN, mg KOH/g", C['tan'], "0.1"],
        ["Pour point, C", C['pour_C'], "-27"]])}
Check case: {basis.CHECK_CRUDE['note']}.

## 2.1 TBP distillation (design crude)
{tbl(["LV %", *[f"{p[0]:g}" for p in C['tbp']]], [["TBP C", *[p[1] for p in C['tbp']]]])}
Light ends (LV% on crude): {', '.join(f'{k} {v}' for k, v in C['light_ends_lv'].items())}.

![Crude TBP and product cut points](figures/tbp.png)

# 3 Products and specifications
{tbl(["Product", "Specification / destination"], [[k, v] for k, v in basis.PRODUCT_SPECS.items()])}
Atmospheric cut points (TBP): {', '.join(f'{n} {t} C' for n, t in basis.CUTS_ATM)}.
Vacuum cut points (TBP): {', '.join(f'{n} {t} C' for n, t in basis.CUTS_VAC)}; VR = 550 C+.
Desalted crude: salt <= 1 PTB, BS&W <= 0.2 vol%. Brine oil content <= 100 ppmw.

# 4 Site and climatic data
{tbl(["Item", "Value"], [[k.replace('_', ' '), v] for k, v in S.items()])}

# 5 Utilities
{tbl(["Utility", "Conditions"], [[k.replace('_', ' '), ', '.join(f'{kk}={vv}' for kk, vv in v.items())] for k, v in U.items()])}

# 6 Key process design parameters
{tbl(["Parameter", "Value"], [[k.replace('_', ' '), v] for k, v in D.items()])}

# 7 Design criteria
- Design pressure: max(1.1 x max. operating, operating + 1.7 bar), minimum 3.5 barg; vacuum equipment full vacuum.
- Design temperature: maximum operating + 28 C (rounded up to 5 C).
- Corrosion allowance: 3 mm general, 6 mm for hot sulfidic (> 260 C) and overhead sour service.
- Materials: per API 939-C (McConomy curves) and API 571: 5Cr / 9Cr for sulfidic service above 260 C, 410S
  cladding for column shells above 260 C, Monel 400 for the C-101 top section (HCl/NH4Cl dew point), Ti tubes in
  the overhead trim condenser, NACE MR0103 / HIC-resistant plate in wet H2S service.
- Fired heaters: API 560; average radiant flux 31.5 kW/m2 (H-101), 25 kW/m2 (H-201); efficiency 90 % (LHV) with APH.
- Exchangers: TEMA R / API 660, max. 650 m2 per shell, 20 C minimum approach, F >= 0.80.
- Pumps: API 610, 2 x 100 % (A/B), 10 % flow margin; spares on opposite electrical buses.
- Relief: API 520/521; all relief to closed flare header (hydrocarbon) via unit KO drum D-104.
- Instrumentation: ISA 5.1; DCS for regulatory control; SIS per IEC 61511 (SIL by LOPA); F&G separate.
- Electrical: NEC Art. 505 (Zone system), API RP 505 classification, IEEE 141/399 studies.

# 8 Codes and standards
{tbl(["Code", "Application"], basis.CODES)}

# 9 Environmental limits (design targets)
- Heater stacks: NOx <= 25 ppmv @ 3 % O2 (ultra-low-NOx burners); SO2 governed by fuel gas H2S <= 160 ppmv.
- No continuous hydrocarbon venting to atmosphere; vacuum off-gas burned in H-201.
- Sour water to SWS; desalter brine to WWT via oil-recovery; noise <= 85 dB(A) at 1 m.
"""
    docgen.render(md, OUT / "CFU-000-PR-BOD-001_Basis-of-Design", "CFU-000-PR-BOD-001", "Basis of Design")


# ---------------------------------------------------------------------------
def pdr(m, sz):
    R = _j("process_results.json")
    S = {s["no"]: s for s in _j("streams.json")}
    a, v = m.res["atm"], m.res["vac"]
    st, sp = m.res["stab"], m.res["split"]
    eq = {e["tag"]: e for e in sz["equipment"]}
    c101 = eq["C-101"]
    c201 = eq["C-201"]
    yields = [["LPG", "30"], ["Light naphtha", "32"], ["Heavy naphtha", "33"], ["Kerosene", "16"], ["Diesel", "17"],
              ["AGO", "18"], ["LVGO", "23"], ["HVGO", "24"], ["Slop wax", "25"], ["Vacuum residue", "26"]]
    crude_kg = m.crude.sum()
    yrows = [[n, no, f"{S[no]['bpsd']:,.0f}", f"{S[no]['total_kg_h'] / 1000:.1f}",
              f"{S[no]['total_kg_h'] / crude_kg * 100:.2f}", S[no]["api"], S[no]["tbp5"], S[no]["tbp95"],
              S[no]["sulfur_wt"]] for n, no in yields]
    tot = sum(S[no]["total_kg_h"] for _, no in yields) + S["9"]["total_kg_h"] + S["29"]["total_kg_h"]
    D86 = {}
    for nm, p in [("Kerosene", a["prod"]["KERO"]), ("Diesel", a["prod"]["DIESEL"]), ("AGO", a["prod"]["AGO"]),
                  ("Heavy naphtha", sp["b"])]:
        tb = assay.tbp_points(m.sl, p, (0.5, 10, 30, 50, 70, 90, 99.5))
        D86[nm] = assay.d86_from_tbp(tb)
    gaps = []
    for lt, hv in [("Heavy naphtha", "Kerosene"), ("Kerosene", "Diesel"), ("Diesel", "AGO")]:
        gaps.append([f"{lt} / {hv}", f"{D86[lt][90]:.0f}", f"{D86[hv][10]:.0f}",
                     f"{D86[lt][99.5]:.0f}", f"{D86[hv][0.5]:.0f}", f"{D86[hv][0.5] - D86[lt][99.5]:+.0f}"])
    secs = [[s["name"], s["trays"] if "trays" in s else "", f"{s['V_kg_h'] / 1000:.0f}", f"{s['L_kg_h'] / 1000:.0f}",
             f"{s['T']:.0f}", f"{s['rho_v']:.2f}", f"{s['rho_l']:.0f}", f"{s['FLV']:.3f}", f"{s['TS_mm']}",
             f"{s['u_flood']:.2f}", f"{s['D_calc']:.2f}"] for s in c101["sections"]]
    vsecs = [[s["name"], f"{s['V_kg_h'] / 1000:.1f}", f"{s['L_kg_h'] / 1000:.0f}", f"{s['T']:.0f}",
              f"{s['P'] * 1000:.0f}", f"{s['rho_v']:.3f}", f"{s['Q_v_m3s']:.0f}", f"{s['D_calc']:.2f}"]
             for s in c201["sections"]]
    ex = [[e["tag"], e["hot"], f"{e['Q_kw'] / 1000:.2f}", f"{e['Th_in']:.0f} / {e['Th_out']:.0f}",
           f"{e['Tc_in']:.0f} / {e['Tc_out']:.0f}"] for e in m.res["preheat"]["exch"]]
    hx = {h["tag"]: h for h in sz["hx"]}
    exs = [[t, f"{hx[t]['area_m2']:.0f}", f"{hx[t]['U']}", f"{hx[t].get('F', 0.9):.2f}",
            f"{hx[t].get('series', 1)} x {hx[t].get('parallel', 1)}"] for t in [e["tag"] for e in m.res["preheat"]["exch"]]
           if t in hx]
    trims = [[t["tag"], t["hot"], t["type"], f"{t['Q_kw'] / 1000:.2f}", f"{t['T_in']:.0f} -> {t['T_out']:.0f}"]
             for t in m.res["preheat"]["trims"]]
    h1, h2 = sz["heaters"]["H-101"], sz["heaters"]["H-201"]
    hrows = [[k, f"{h1[k2] if not isinstance(h1[k2], float) else round(h1[k2] / f, f2)}",
              f"{h2.get(k2, '-') if not isinstance(h2.get(k2), float) else round(h2[k2] / f, f2)}"]
             for k, k2, f, f2 in [("Process duty, MW", "Q_proc_kw", 1000, 2), ("Absorbed duty, MW", "Q_abs_kw", 1000, 2),
                                  ("Fired duty (LHV), MW", "Q_fired_kw", 1000, 2), ("Efficiency", "eff", 1, 2),
                                  ("Inlet T, C", "T_in", 1, 0), ("Outlet T (COT), C", "T_out", 1, 1),
                                  ("Outlet P, bar(a)", "P_out", 1, 2), ("Outlet vapour fraction (mass)", "vf_out", 1, 3),
                                  ("Radiant duty, MW", "radiant_kw", 1000, 2), ("Radiant area, m2", "rad_area", 1, 0),
                                  ("Radiant tubes (6 in x 18.3 m)", "rad_tubes", 1, 0), ("Passes", "passes", 1, 0),
                                  ("Mass flux, kg/m2s", "mass_flux", 1, 0), ("Burners", "burners", 1, 0),
                                  ("Fuel gas, kg/h", "fuel_kg_h", 1, 0)]]
    pumps = [[p["tag"], p["service"], f"{p['flow_m3h']:.0f}", f"{p['head_m']:.0f}", f"{p['absorbed_kw']:.0f}",
              p["motor_kw"], p["api610"]] for p in sz["pumps"]]
    psv = [[p["tag"], p["protects"], p["case"], f"{p['load_kg_h']:,.0f}", p["set_barg"], f"{p['count']} x {p['orifice']}"]
           for p in sz["psv"]]
    warns = "\n".join(f"- {w}" for w in m.warn) or "- None"
    md = f"""# 1 Purpose
This report documents the process simulation and equipment sizing basis for the {basis.PROJECT['name']}
(FEED, Rev {basis.PROJECT['rev']}). It summarises the method, the heat and material balance (full stream table in
CFU-000-PR-HMB-001) and the hydraulic and thermal sizing of the main equipment. Every number is produced by the
calculation code in this repository (`python build.py`). That code is the calculation record.

# 2 Method
## 2.1 Crude characterisation
The design crude TBP curve is split into {m.sl.n - 4} pseudo-components (15 C cuts to 395 C, 25 C to 595 C,
then 50 C), plus discrete light ends C2-nC4. Specific gravity uses a Watson K that varies with boiling point,
K = K0 - 0.00025 (Tb - 100), with K0 = {m.sl.K0:.3f} fitted to the bulk {basis.CRUDE['api']} API. MW, Tc and Pc
come from Riazi-Daubert (1987) and the acentric factor from Lee-Kesler. Vapour pressure uses Lee-Kesler
corresponding states. Enthalpy: Watson-Nelson liquid Cp, Fallon-Watson vapour Cp, Kistiakowsky latent heat at
Tb (reference liquid at 15 C). Sulfur is distributed by boiling point and scaled to {basis.CRUDE['sulfur_wt']} wt%.

## 2.2 Column modelling (cut-point model)
- Products are defined by TBP cut points with a sigmoid overlap ("sloppy split"); the width increases down the
  column, matching typical crude-unit ASTM gaps and overlaps.
- Flash zones: equilibrium (Raoult) flash with stripping steam as an inert. The flash-zone temperature is solved
  so that vapour = all distillates + overflash ({D['atm_overflash_lv']:.0%} LV on crude; vacuum
  {D['vac_overflash_lv']:.0%} LV on feed). COT = FZ + transfer-line temperature drop.
- Draw temperatures are the product bubble point at the tray's hydrocarbon partial pressure; steam and internal
  reflux are iterated with the heat balance.
- Total heat removal comes from the overall column enthalpy balance. It is split between top reflux and
  pumparounds (TPA {D['pa_split']['TPA']:.0%}, MPA {D['pa_split']['MPA']:.0%}, BPA {D['pa_split']['BPA']:.0%});
  internal reflux below each draw comes from envelope balances, and gives the section vapour and liquid loads
  used for tray sizing.
- Stabiliser and splitter: Fenske-Underwood-Gilliland short-cut, Fenske distribution of non-keys, Kirkbride feed
  stage, R = 1.3 Rmin, tray efficiency 75 %.
- Preheat train: sequential counter-current exchangers, minimum approach {D['min_approach']:.0f} C; the
  remaining duty goes to trim coolers or steam generators.

## 2.3 Limitations (FEED accuracy)
The thermodynamics are ideal (Raoult), and the model does not do tray-to-tray rigorous rating. Expect the
flash-zone and draw temperatures to be within about 5-10 C of a rigorous simulation (HYSYS/Petro-SIM). Before
detailed engineering, these numbers must be confirmed with a rigorous simulation on a full crude assay.

Model warnings:
{warns}

\\pagebreak
# 3 Heat and material balance summary
## 3.1 Product yields
{tbl(["Product", "Stream", "BPSD", "t/h", "wt%", "API", "TBP5 C", "TBP95 C", "S wt%"], yrows)}
Overall hydrocarbon balance: products + off-gases = {tot / 1000:.2f} t/h vs crude {crude_kg / 1000:.2f} t/h
({(tot / crude_kg - 1) * 100:+.3f} %).

![Product split by pseudo-component](figures/splits.png)

## 3.2 Fractionation quality (ASTM D86 estimated via Riazi-Daubert TBP-D86)
{tbl(["Pair", "Light D86 90%", "Heavy D86 10%", "Light D86 EP", "Heavy D86 IBP", "5-95 gap (IBP-EP), C"], gaps)}
A negative IBP-EP gap means overlap; typical crude-unit targets are a gap of +10 C (naphtha/kero) and an
overlap of 0 to -20 C (kero/diesel, diesel/AGO).

# 4 Atmospheric section
{tbl(["Parameter", "Value"], [
        ["Crude inlet temperature (CIT)", f"{R['preheat']['CIT']:.1f} C"],
        ["Desalter temperature", f"{R['preheat']['T_desalter']:.1f} C"],
        ["H-101 COT", f"{a['cot']:.1f} C"],
        ["Flash zone T / P", f"{a['T_fz']:.1f} C / {a['P_fz'] - 1.013:.2f} barg"],
        ["Column top T / P", f"{a['T_top']:.1f} C / {D['atm_top_P'] - 1.013:.2f} barg"],
        ["Top water dew point (margin)", f"{a['T_wdew']:.1f} C ({a['T_top'] - a['T_wdew']:.0f} C)"],
        ["Bottom T", f"{a['T_bot']:.1f} C"],
        ["Reflux (to top tray)", f"{a['R'] / 1000:.1f} t/h (R/D = {a['R'] / a['prod']['NAPH'].sum():.2f})"],
        ["Draw temperatures K / D / AGO", " / ".join(f"{a['T_draw'][k]:.0f}" for k in ('KERO', 'DIESEL', 'AGO')) + " C"],
        ["Total heat removal", f"{a['Q_tot'] / 1000:.2f} MW"],
        ["Overhead condensing duty", f"{a['Q_cond'] / 1000:.2f} MW"],
        ["Stripping steam bottom/K/D/AGO, kg/h", " / ".join(f"{a['steam'][k]:.0f}" for k in ('bottom', 'KERO', 'DIESEL', 'AGO'))]])}

{tbl(["Pumparound", "Draw tray", "Return tray", "Duty MW", "Draw T C", "Return T C", "Circulation t/h"],
     [[k, x['draw_tray'], x['ret_tray'], f"{x['duty_kw'] / 1000:.2f}", f"{x['T_draw']:.0f}", f"{x['T_ret']:.0f}",
       f"{x['flow'] / 1000:.0f}"] for k, x in a['pa'].items()])}

![C-101 temperature profile](figures/c101_profile.png)

## 4.1 C-101 tray hydraulics (Fair flooding, 80 % flood, 85 % net area)
{tbl(["Section", "Trays", "V t/h", "L t/h", "T C", "rho V", "rho L", "FLV", "TS mm", "u flood m/s", "D calc m"], secs)}
Selected: {c101['size']}. Internals: {c101['internals']}.

![C-101 section traffic](figures/c101_loads.png)

\\pagebreak
# 5 Crude preheat train
{tbl(["Exchanger", "Hot stream", "Duty MW", "Hot in/out C", "Crude in/out C"], ex)}
{tbl(["Exchanger", "Area m2", "U W/m2K", "F", "Shells (series x parallel)"], exs)}
Trim duties (heat not recovered to crude):
{tbl(["Tag", "Stream", "Type", "Duty MW", "T C"], trims)}
![Preheat train temperature-duty diagram](figures/preheat.png)

# 6 Fired heaters
{tbl(["Item", "H-101", "H-201"], hrows)}

# 7 Vacuum section
{tbl(["Parameter", "Value"], [
        ["Feed (atmospheric residue)", f"{v['ar'].sum() / 1000:.1f} t/h, {v['ar_m3h']:.0f} m3/h"],
        ["H-201 COT", f"{v['cot']:.1f} C"],
        ["Flash zone T / P", f"{v['T_fz']:.1f} C / {v['P_fz'] * 1000:.0f} mbar(a)"],
        ["Top T / P", f"{v['T_top']:.0f} C / {v['P_top'] * 1000:.0f} mbar(a)"],
        ["LVGO / HVGO draw T", f"{v['T_lvgo']:.0f} / {v['T_hvgo']:.0f} C"],
        ["Bottom T (quenched)", f"{v['T_bot']:.0f} C"],
        ["Stripping + coil steam", f"{v['steam']:.0f} kg/h"],
        ["Total heat removal", f"{v['Q_tot'] / 1000:.2f} MW (LVGO PA {v['pa']['LVGO']['duty_kw'] / 1000:.1f}, "
                               f"HVGO PA {v['pa']['HVGO']['duty_kw'] / 1000:.1f})"],
        ["Ejector motive steam", f"{m.res['ejector']['motive_total']:.0f} kg/h MP steam"]])}
C-201 bed sizing (packing at Cs = 0.11 m/s, wash grid 0.12 m/s; stripping trays at 75 % flood):
{tbl(["Section", "V t/h", "L t/h", "T C", "P mbar", "rho V", "Q m3/s", "D calc m"], vsecs)}
Selected: {c201['size']}.

# 8 Light ends
{tbl(["Item", "C-105 stabiliser", "C-106 splitter"], [
        ["Light / heavy key", "nC4 / iC5-range pseudo", "NBP<80 / NBP>80 pseudo"],
        ["Top / bottom P, bar(a)", f"{st['P_top']:.2f} / {st['P_bot']:.2f}", f"{sp['P_top']:.2f} / {sp['P_bot']:.2f}"],
        ["Top / bottom T, C", f"{st['T_top']:.0f} / {st['T_bot']:.0f}", f"{sp['T_top']:.0f} / {sp['T_bot']:.0f}"],
        ["Nmin / Rmin / R", f"{st['Nmin']:.1f} / {st['Rmin']:.2f} / {st['R']:.2f}",
         f"{sp['Nmin']:.1f} / {sp['Rmin']:.2f} / {sp['R']:.2f}"],
        ["Theoretical / actual trays", f"{st['N_theo']:.1f} / {st['N_actual']}", f"{sp['N_theo']:.1f} / {sp['N_actual']}"],
        ["Feed tray (from top)", st['feed_stage'], sp['feed_stage']],
        ["Condenser / reboiler duty, MW", f"{st['Q_cond'] / 1000:.2f} / {st['Q_reb'] / 1000:.2f}",
         f"{sp['Q_cond'] / 1000:.2f} / {sp['Q_reb'] / 1000:.2f}"],
        ["Diameter x height", eq['C-105']['size'], eq['C-106']['size']]])}

# 9 Pumps
{tbl(["Tag", "Service", "Rated m3/h", "Head m", "Abs. kW", "Motor kW", "API 610"], pumps)}

# 10 Relief loads (preliminary governing cases)
{tbl(["Tag", "Protects", "Case", "Load kg/h", "Set barg", "Orifice"], psv)}
The global flare load (power failure, cooling failure) is assessed in the flare study. The largest single unit
contributor is the C-101 overhead (reflux failure).
"""
    docgen.render(md, OUT / "CFU-000-PR-RPT-001_Process-Design-Report", "CFU-000-PR-RPT-001",
                  "Process Design Report - Simulation & Equipment Sizing")


def build():
    m = hmb.run()
    sz = sizing.build(m)
    figures(m)
    bod()
    pdr(m, sz)
