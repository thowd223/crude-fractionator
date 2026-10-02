"""Control Philosophy & Proposed Control Scheme CFU-000-IC-RPT-001 and SIF list / SIL determination
CFU-000-IC-RPT-002 (markdown + pdf via cfu.docgen)."""
from __future__ import annotations

import math
import re

from .. import basis, docgen
from . import ce, csd, cvsizing
from .common import OUT, load, loops, pr, render_png, sifs, streams

FIG = OUT / "figures"


def _figs():
    FIG.mkdir(parents=True, exist_ok=True)
    out = {}
    for no, _ in csd.SHEETS:
        svg = next(csd.DIR.glob(f"{no}_*.svg"))
        out[no] = render_png(svg, FIG / f"{no}.png", 2600).name
    for stem in ("CFU-000-IC-BLK-001_ICS-Architecture", "CFU-000-IC-CE-001_Cause-Effect-Matrix"):
        svg = OUT / f"{stem}.svg"
        if svg.exists():
            k = stem.split("_")[0]
            out[k] = render_png(svg, FIG / f"{k}.png", 2600).name
    for svg in sorted((OUT / "loop-diagrams").glob("*.svg")):
        k = svg.stem.split("_")[0]
        out[k] = render_png(svg, FIG / f"{k}.png", 2200).name
    return out


def _tbl(head, rows):
    s = "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n"
    for r in rows:
        s += "| " + " | ".join(str(c) for c in r) + " |\n"
    return s + "\n"


def _hcyl_frac(h):
    """Fraction of horizontal-cylinder cross-section filled at fractional height h."""
    th = 2 * math.acos(1 - 2 * h)
    return (th - math.sin(th)) / (2 * math.pi)


def level_table():
    E = {e["tag"]: e for e in load("equipment.json")}
    S = streams()
    R = pr()

    def L_of(t):
        m = re.search(r"x\s*([\d.]+)\s*m T/T", E[t]["size"])
        return float(m.group(1)) if m else 5.0

    def hdrum(t):
        D = E[t]["D"]
        return math.pi * D ** 2 / 4 * L_of(t) * (_hcyl_frac(0.75) - _hcyl_frac(0.25))

    def vcol(D, span):
        return math.pi * D ** 2 / 4 * span

    vac_q = S["26"]["total_kg_h"] / (S["26"]["rho_liq"] * (1 - 0.0007 * (R["vac"]["T_bot"] - S["26"]["T_C"])))
    rows = [
        ("LIC-1033", "D-102 HC level", hdrum("D-102"), S["11"]["liq_act_m3h"], "Averaging", "FIC-1034 (C-105 feed)"),
        ("LIC-1092", "D-105 level", hdrum("D-105"), S["30"]["liq_act_m3h"], "Averaging", "FIC-1093 (LPG)"),
        ("LIC-1101", "D-106 level", hdrum("D-106"), S["32"]["liq_act_m3h"], "Averaging", "FIC-1102 (LN)"),
        ("LIC-1082", "C-101 bottom (2.0 m span)", vcol(E["C-101"]["D2"], 2.0), S["19"]["liq_act_m3h"], "Averaging",
         "FIC-1083 (H-201 charge)"),
        ("LIC-1051", "C-102 bottom (1.5 m span)", vcol(E["C-102"]["D"], 1.5), S["16"]["liq_act_m3h"] * 1.25,
         "Averaging", "FIC-1052"),
        ("LIC-1061", "C-103 bottom (1.5 m span)", vcol(E["C-103"]["D"], 1.5), S["17"]["liq_act_m3h"] * 1.3,
         "Averaging", "FIC-1062"),
        ("LIC-1071", "C-104 bottom (1.5 m span)", vcol(E["C-104"]["D"], 1.5), S["18"]["liq_act_m3h"] * 1.35,
         "Averaging", "FIC-1072"),
        ("LIC-1097", "C-105 bottom (1.5 m span)", vcol(E["C-105"]["D"], 1.5), S["31"]["liq_act_m3h"], "Averaging",
         "LV-1097 (C-106 feed)"),
        ("LIC-1106", "C-106 bottom (1.5 m span)", vcol(E["C-106"]["D"], 1.5), S["33"]["liq_act_m3h"] * 1.25,
         "Averaging", "FIC-1107 (HN)"),
        ("LIC-2024", "C-201 boot (2.0 m span)", vcol(E["C-201"]["D2"], 2.0), vac_q, "Tight-ish (residence "
         "time limit, coking)", "FIC-2025 (VR)"),
    ]
    out = []
    for tag, d, V, Q, mode, mv in rows:
        tau = V / Q * 60 if Q else 0
        if mode.startswith("Averaging"):
            tune = f"PI: Kc 0.5-1.0 %/%, Ti ~ {max(4 * tau, 5):.0f} min"
        else:
            tune = "PI: Kc 1.5-2, Ti 5-8 min; TIC-2026 quench limits T"
        out.append((tag, d, f"{V:.1f}", f"{Q:.0f}", f"{tau:.1f}", mode, mv, tune))
    out += [
        ("LIC-1007 / 1008", "Desalter interface", "-", f"{S['4']['total_kg_h'] / 950:.0f}", "-", "Tight",
         "LV-1007 / LV-1008", "PI: Kc 2-3, Ti 3-5 min (grid protection)"),
        ("LIC-1035", "D-102 boot interface", "-", f"{S['12']['total_kg_h'] / 990:.0f}", "-", "Tight", "LV-1035",
         "PI: Kc 2-4, Ti 2-4 min"),
        ("LIC-2014 / 2018 / 2021", "C-201 draw-pan levels", "small", "-", "< 2", "Tight", "product FICs",
         "PI: Kc 2-4, Ti 1-3 min (pans run dry fast)"),
        ("LIC-1110 / 2030", "E-113 / E-201 steam drum", "-", "-", "-", "3-element", "LV BFW",
         "Level + steam flow FF + BFW flow cascade"),
        ("LIC-1098", "E-116 condensate pot", "small", "-", "-", "Tight", "LV-1098", "PI: Kc 2-3, Ti 2 min"),
        ("LIC-2028 / 2029", "D-201 hotwell water / slop", "-", "-", "-", "Tight (barometric seal)", "LV-2028/2029",
         "PI: Kc 2, Ti 3 min"),
    ]
    return out


def analysers():
    return [
        ("AT-1022 / AT-2008", "H-101 / H-201 flue gas O2 + CO", "In-situ zirconia O2 + TDL CO (arch)", "continuous",
         "O2 trim, CO override, CV"),
        ("AT-1037", "D-102 boot sour water pH", "pH probe (retractable)", "continuous", "Neutraliser trim"),
        ("AT-1038", "Unstab. naphtha D86 EP / RVP", "Online distillation (ASTM D86 equiv.), AH-101", "10-15 min",
         "MPC CV-01, inferential bias"),
        ("AT-1046", "Desalted crude salt content", "Online salt-in-crude (conductometric)", "15 min",
         "Desalter optimisation"),
        ("AT-1047", "Desalted crude BS&W", "Microwave water-cut", "continuous", "Desalter performance"),
        ("AT-1048", "Charge crude API / salt / BS&W", "Densitometer + salt + water-cut", "continuous",
         "Crude-switch DV (MPC)"),
        ("AT-1049", "Desalter brine oil-in-water", "UV fluorescence", "continuous", "Brine quality / ETP"),
        ("AT-1055", "Kerosene flash / freeze point", "Online flash (Pensky-Martens eq.) + freeze analyser",
         "10-20 min", "MPC CV-02/03"),
        ("AT-1065", "Diesel D86 T95 / cloud point", "Online distillation + cloud point", "15 min", "MPC CV-04/05"),
        ("AT-1075", "AGO D86 T95 / colour", "Online distillation + colorimeter", "15 min", "MPC CV-06"),
        ("AT-1099", "LPG C5+", "Process GC", "5 min", "C-105 MPC CV"),
        ("AT-1108 / AT-1109", "LN C6+ & RVP / HN IBP & C5-", "Process GC (shared, stream switching)", "6 min",
         "C-106 MPC CVs"),
        ("AT-1021", "Fuel gas Wobbe index / LHV", "Fast calorimeter", "< 30 s", "Combustion FF, DV-05"),
        ("AT-2032", "Vacuum off-gas H2S", "UV / lead-acetate tape analyser", "2 min", "H-201 firing / SO2"),
    ]


# =========================================================================== RPT-001
def rpt001(F, io):
    R = pr()
    S = streams()
    A, V, H1, H2 = R["atm"], R["vac"], R["heaters"]["H-101"], R["heaters"]["H-201"]
    L = loops()
    SF = sifs()
    T = csd.mpc_tables()
    cv = cvsizing.valves()
    lp = ce.lopa()
    md = []
    a = md.append
    a("# 1. Introduction and scope")
    a(f"This document defines the control philosophy and the proposed control scheme for the {basis.PROJECT['name']} "
      f"(design throughput {basis.CAPACITY_BPSD:,} BPSD of {basis.CRUDE['name']}, turndown "
      f"{int(basis.TURNDOWN * 100)} %). It covers the regulatory (BPCS / DCS) layer, the advanced process control "
      "(APC / MPC) layer, alarm management, the safety layer interfaces (SIS, BMS, F&G - detailed in "
      "CFU-000-IC-RPT-002 and CFU-000-IC-CE-001), the ICS architecture and the instrument design criteria, "
      "including control valve sizing for the key valves.")
    a("All tags follow ISA-5.1 and are taken from the master loop list `cfu/control_loops.py` "
      "(data/control_loops.json) and the instrument index CFU-000-IC-IDX-001 (data/instruments.json). Tags "
      "introduced by I&C (analysers, computing blocks) are listed in section 13 for inclusion in the index.")
    a("**Related deliverables**")
    a(_tbl(["Document", "Title"], [
        ("CFU-100-IC-CSD-001..005, CFU-000-IC-CSD-006", "Proposed control scheme diagrams (A1)"),
        ("CFU-000-IC-BLK-001", "ICS architecture block diagram (A1)"),
        ("CFU-000-IC-CE-001", "Cause & effect matrix (xlsx + A1 drawing)"),
        ("CFU-000-IC-RPT-002", "SIF list and SIL determination (LOPA)"),
        ("CFU-000-IC-IOL-001", "I/O list (xlsx), data/io_list.json"),
        ("CFU-000-IC-CAL-001", "Control valve sizing (xlsx, summarised in section 12)"),
        ("CFU-100-IC-LD-001..003", "Typical loop diagrams (A3)"),
        ("CFU-xxx-PR-PFD / PID", "Process flow diagrams / P&IDs (process discipline)"),
    ]))
    a("**Codes and standards:** ISA-5.1, ISA-5.4, ISA-18.2 / IEC 62682, EEMUA 191, ISA-75.01.01 / IEC 60534, "
      "IEC 61511 / ISA-84, IEC 62443, API 551, API 552, API 554, API 556, NFPA 85/86, IEC 60079.")
    a("# 2. Control objectives")
    for s in [
        "**Safety and environment** - keep the unit within its safe operating envelope; independent protection "
        "layers (SIS / BMS / F&G) separate from the BPCS; no single failure leads to an unsafe state.",
        "**Product quality** - hold naphtha end point, kerosene flash / freeze, diesel T95 / cloud, AGO and VGO "
        "quality and LPG / naphtha RVP within specification with minimum give-away.",
        "**Throughput** - maximise crude charge up to the active constraint (heater firing, flooding, overhead "
        "condenser, vacuum system, pump / valve limits).",
        "**Energy** - maximise preheat recovery (CIT), minimise excess O2, stripping steam and reflux.",
        "**Stability and operability** - smooth feed to downstream units (averaging level control), "
        "fast crude switches, robust start-up / shutdown and 50 % turndown.",
        "**Reliability** - redundant controllers, I/O isolation per area, dual-fed power, no common-mode with "
        "the SIS."]:
        a(f"- {s}")
    a("The control hierarchy is: L0/L1 field and regulatory PID (DCS), L2 operator HMI and supervisory "
      "logic, L3 multivariable predictive control with inferentials and an economic LP; the SIS / BMS / F&G act "
      "independently of all of these.")
    a("**Key operating values (design case, data/process_results.json)**")
    a(_tbl(["Item", "Value", "Item", "Value"], [
        ("Crude charge", f"{S['1']['std_m3h']:.0f} m3/h std ({S['1']['total_kg_h'] / 1000:.0f} t/h)",
         "Desalter temperature", f"{R['preheat']['T_desalter']:.0f} °C"),
        ("CIT (H-101 inlet)", f"{R['preheat']['CIT']:.0f} °C", "H-101 COT", f"{H1['T_out']:.0f} °C"),
        ("H-101 absorbed / fired", f"{H1['Q_abs_kw'] / 1000:.1f} / {H1['Q_fired_kw'] / 1000:.1f} MW",
         "H-101 passes / burners", f"{H1['passes']} / {H1['burners']}"),
        ("C-101 top T / P", f"{A['T_top']:.0f} °C / {A['P_top_barg']:.2f} barg", "D-102 pressure",
         f"{A['drum_P_barg']:.2f} barg"),
        ("Flash zone T / P", f"{A['T_fz']:.0f} °C / {A['P_fz_barg']:.2f} barg", "Reflux",
         f"{A['reflux_kg_h'] / 1000:.0f} t/h"),
        ("TPA / MPA / BPA duty", f"{A['pa']['TPA']['duty_kw'] / 1000:.1f} / {A['pa']['MPA']['duty_kw'] / 1000:.1f} / "
                                 f"{A['pa']['BPA']['duty_kw'] / 1000:.1f} MW",
         "Kero / diesel / AGO draw T", f"{A['T_draw']['KERO']:.0f} / {A['T_draw']['DIESEL']:.0f} / "
                                       f"{A['T_draw']['AGO']:.0f} °C"),
        ("H-201 COT", f"{H2['T_out']:.0f} °C", "C-201 top / flash zone", f"{V['P_top_mbar']:.0f} / "
                                                                         f"{V['P_fz_mbar']:.0f} mbar(a)"),
        ("LVGO / HVGO PA duty", f"{V['pa']['LVGO']['duty_kw'] / 1000:.1f} / {V['pa']['HVGO']['duty_kw'] / 1000:.1f} MW",
         "C-201 bottoms T", f"{V['T_bot']:.0f} °C (limit 365 °C)"),
        ("C-105 top P", f"{R['stab']['P_top']:.1f} bar(a)", "C-106 top P", f"{R['split']['P_top']:.1f} bar(a)"),
    ]))
    a("# 3. Regulatory control strategy")
    a("General rules applied to all sections:")
    for s in [
        "Flow loops are the innermost loops for all manipulated streams (cascade slaves); valves are never "
        "positioned directly by quality or temperature controllers.",
        "Product draws from towers are on flow control; accumulator / bottoms levels cascade to the downstream "
        "flow (material balance 'in the direction of flow' except where noted).",
        "Pumparound duties are controlled by return temperature via exchanger bypass on the pumparound side, "
        "with circulation rate on flow control.",
        "Ratio stations (FFIC / FFY) relate chemical injection, wash water and stripping steam to their master "
        "flows; ratios are operator / MPC set.",
        "Selectors and cross-limits are implemented in the DCS with anti-windup (external reset feedback).",
        "All cascades are bumpless; on slave failure or bad PV the master goes to tracking.",
    ]:
        a(f"- {s}")
    a("## 3.1 Crude charge and desalting (CFU-100-IC-CSD-003)")
    a(f"- **Throughput** - FIC-1001 on P-101 discharge (FV-1001) is the unit throughput master "
      f"({S['1']['std_m3h']:.0f} m3/h design). Its SP is set by the operator or the CDU MPC (max-feed push). "
      "The PV / SP is broadcast on a ratio / feed-forward bus to: demulsifier FFIC-1002 (X-101 stroke), wash "
      "water FFIC-1003 (5 vol %), caustic FFIC-1010 (X-102), the H-101 pass flow controllers and the COT "
      "feed-forward.")
    a(f"- **Desalter temperature** - TIC-1004 positions TV-1004 on the crude-side bypass of E-105 (VR side "
      f"always flowing) to hold {R['preheat']['T_desalter']:.0f} °C (limits 125-145 °C).")
    a("- **Mixing** - PDIC-1005 / 1006 hold the mix-valve dP (0.5-1.5 bar) for wash-water dispersion; the SP is "
      "optimised against salt-in-crude AT-1046 and oil-in-brine AT-1049 (operator, not closed loop).")
    a("- **Interface** - LIC-1007 / 1008 (guided-wave radar + density profiler) control the water/oil interface "
      "tightly via brine valves LV-1007 / LV-1008; second-stage brine is recycled counter-currently to stage 1. "
      "Low-low interface (SIF-107) trips the transformers.")
    a(f"- **Pressure** - PIC-1009 holds the desalter outlet pressure ({S['5']['P_barg']:.1f} barg) above crude "
      "vapour pressure at the booster pump P-102 suction.")
    a("![Figure 1 - Crude charge, desalting and preheat control (CFU-100-IC-CSD-003)](figures/"
      + F["CFU-100-IC-CSD-003"] + ")")
    a("## 3.2 Preheat train")
    a(f"The cold train (E-101..E-105) heats crude from {S['1']['T_C']:.0f} °C to the desalter; the hot train "
      f"(E-106..E-111) to a CIT of {R['preheat']['CIT']:.0f} °C. Exchanger bypasses that carry a control function "
      "are on the hot (pumparound) side and belong to the pumparound duty loops: TIC-1043 (MPA, E-106), "
      "TIC-1045 (BPA, E-110 / E-113) and TIC-2017 (HVGO, E-108). This keeps the crude flow path simple and makes "
      "CIT a measured disturbance (TI-1226) fed forward to the COT controller. The MPC trades heat recovery "
      "(higher CIT) against column fractionation through the PA duties.")
    a("## 3.3 Atmospheric heater H-101 (CFU-100-IC-CSD-001)")
    a(f"- **Pass flow** - each of the {H1['passes']} passes has a flow controller FIC-1011..1018. The base SP of "
      f"each pass = FIC-1001 / {H1['passes']} (FY-1011A, {H1['flow'] / H1['passes'] / 1000:.1f} t/h).")
    a("- **Pass balancing** - TDIC-1019 compares the pass outlet temperatures TI-1011..1018 with their average and "
      "computes biases FY-1011B..1018B; the biases are normalised so that their sum is zero, i.e. **total flow is "
      "held constant** and only the distribution changes. Biases are clamped to ±10 % of pass flow and frozen "
      "when any pass FIC is not in cascade or a pass flow is near its low-low trip.")
    a("- **COT** - TIC-1020 (SP from MPC) is the master. A feed-forward FY-1020A = f(charge x (COT - CIT)) with "
      "lead-lag dynamic compensation is added (FY-1020B) to give the firing demand.")
    a("- **Cross-limiting (lead-lag) combustion control** - fuel SP = MIN(firing demand, air available / "
      "stoichiometric ratio) (FY-1021A); air SP = MAX(firing demand, actual fuel heat release) x air/fuel ratio "
      "x O2 trim (FY-1025A / B). On a load increase the air leads and fuel follows; on a decrease the fuel leads "
      "and air follows, so the firebox never becomes sub-stoichiometric. Actual fuel heat release uses FG flow "
      "FT-1021 corrected by the Wobbe analyser AT-1021.")
    a("- **Fuel** - the fuel heat demand is characterised to a burner pressure SP (burner curve, FY / PY-1021A); a "
      "min-fire stop (high select PY-1021B) keeps burners above the stable minimum. PIC-1021 manipulates "
      "PV-1021. (The loop list describes this as 'low select vs min-fire'; the implementation is a high select "
      "against the minimum burner pressure combined with the cross-limit low select.)")
    a("- **O2 trim** - AIC-1022 (arch O2, typical SP 2-3 % wet, with CO override > 200 ppm) multiplies the air/fuel "
      "ratio, limited ±10 %. Combustion air FIC-1025 positions the FD fan inlet vanes (K-101A/B).")
    a("- **Draft** - PIC-1023 holds -2.5 mmH2O at the arch; split range via PY-1023: ID fan speed (K-102A/B VSD) "
      "0-50 %, stack damper 50-100 %. On ID fan trip the damper opens for natural-draft operation at reduced "
      "firing.")
    a("- **Stripping steam superheat** - TIC-1024 (350 °C) on the convection steam coil desuperheater.")
    a("![Figure 2 - H-101 combustion, COT and pass balancing (CFU-100-IC-CSD-001)](figures/"
      + F["CFU-100-IC-CSD-001"] + ")")
    a("## 3.4 Atmospheric column C-101 and side strippers (CFU-100-IC-CSD-002)")
    a(f"- **Column pressure (split range)** - PIC-1032 on D-102 ({A['drum_P_barg']:.2f} barg): 0-50 % output closes "
      "the fuel-gas make-up PV-1032B, 50-100 % opens the off-gas valve PV-1032A to FG / flare. Normally the "
      "overhead is a total condenser and neither valve passes significant flow. The MPC may lower the PIC SP to "
      "improve lift, constrained by A-101 duty and the reflux drum temperature.")
    a(f"- **Top temperature -> reflux cascade** - TIC-1030 (top {A['T_top']:.0f} °C, pressure-compensated) sets "
      f"the SP of reflux FIC-1031 ({A['reflux_kg_h'] / 1000:.0f} t/h). TIC-1030 is the naphtha end-point handle "
      "for the MPC (CV: AT-1038 / inferential).")
    a("- **Overhead accumulator** - LIC-1033 (averaging) -> naphtha FIC-1034 (feed to C-105); boot interface "
      "LIC-1035 tight to LV-1035; pH AIC-1037 trims the neutraliser ratio FFIC-1036 (X-103).")
    a("- **Pumparound duty** - FIC-1040 / 1042 / 1044 hold circulation; TIC-1041 / 1043 / 1045 set the return "
      "temperature, i.e. the duty, via PA-side exchanger bypass (TV-1041, TV-1043, TV-1045). Duty "
      "distribution TPA / MPA / BPA is an MPC degree of freedom (heat recovery vs. internal reflux in the "
      "fractionation zones).")
    a("- **Side-draw cut-point control** - draw flows FIC-1050 / 1060 / 1070 are the cut-point handles; their SPs "
      "come from the MPC (kero flash / freeze, diesel T95, AGO T95). The internal reflux below each draw must "
      "stay above a minimum (inferred from the column heat balance - MPC constraint).")
    a("- **Strippers** - bottoms level LIC-1051 / 1061 / 1071 cascades to product flow FIC-1052 / 1062 / 1072. "
      "Stripping steam FIC-1054 / 1064 / 1074 is ratioed to the product flow (FFY, lb/bbl) - the MPC adjusts the "
      "ratio for flash point.")
    a(f"- **Bottoms** - LIC-1082 cascades to the atmospheric residue flow FIC-1083 (also the H-201 charge). "
      f"Bottom stripping steam FIC-1081 is ratioed to AR ({A['steam']['bottom']:.0f} kg/h design, ~10 lb/bbl).")
    a("- **Overflash** - FI-1080 (wash-zone liquid) is monitored as % of charge with a low alarm; it is a hard "
      "MPC constraint (>= 3 vol %) raised by COT or by reducing BPA duty. Section dP PDI-1237 is the flooding "
      "indicator.")
    a("![Figure 3 - C-101 overhead, reflux, pumparound and side-draw control (CFU-100-IC-CSD-002)](figures/"
      + F["CFU-100-IC-CSD-002"] + ")")
    a("## 3.5 Stabiliser C-105 and splitter C-106 (CFU-100-IC-CSD-004)")
    a(f"- **Pressure** - C-105: PIC-1091 hot-vapour bypass PV-1091 around the flooded condenser A-106 "
      f"({R['stab']['P_top']:.1f} bar(a)). C-106: PIC-1100 on the flooded-condenser outlet PV-1100 "
      f"({R['split']['P_top']:.1f} bar(a)); floating-pressure operation under MPC.")
    a("- **Material balance** - D-105 / D-106 levels LIC-1092 / 1101 cascade to LPG FIC-1093 / LN FIC-1102; "
      "C-105 bottoms LIC-1097 to LV-1097 (C-106 feed, averaging); C-106 bottoms LIC-1106 to HN FIC-1107.")
    a("- **Energy balance** - sensitive-tray temperatures TIC-1095 (C-105) and TIC-1104 (C-106, tray 30), "
      "pressure-compensated, cascade to reboiler steam FIC-1096 (HP steam, E-116) and FIC-1105 (MP steam, "
      "E-117). Reflux: FIC-1094 on ratio to feed (FFY-1094) for C-105; FIC-1103 on flow for C-106.")
    a("- **Dual-composition strategy** - top composition (LPG C5+, LN C6+) is controlled with reflux "
      "(L/F), bottom composition (naphtha RVP, HN C5- / IBP) with the sensitive-tray temperature SP. The "
      "interaction (L-V configuration, RGA ~ 2-4) is handled by the light-ends MPC using GC analysers "
      "AT-1099, AT-1108 and AT-1109. Without MPC the columns run single-ended (tray temperature) with reflux on "
      "ratio and operator trim.")
    a("![Figure 4 - Stabiliser / splitter control (CFU-100-IC-CSD-004)](figures/" + F["CFU-100-IC-CSD-004"] + ")")
    a("## 3.6 Vacuum unit H-201 / C-201 (CFU-200-IC-CSD-005)")
    a(f"- **H-201** - pass flows FIC-2001..2004 (ratio of FIC-1083), coil (velocity) steam FIC-2007, COT "
      f"TIC-2005 ({H2['T_out']:.0f} °C) cascaded to FG pressure PIC-2006 with the same cross-limiting and FF "
      "philosophy as H-101; O2 AIC-2008 on the stack damper (natural draft).")
    a(f"- **Vacuum pressure** - PIC-2010 ({V['P_top_mbar']:.0f} mbar(a)) recycles off-gas / steam from the "
      "after-condenser to the 1st-stage ejector J-201 suction (PV-2010). Motive steam is not throttled. The MPC "
      "pushes the pressure SP to the lowest achievable value (max lift), constrained by PV-2010 output.")
    a("- **LVGO section** - top temperature TIC-2012 cascades to the LVGO PA return temperature TIC-2013 "
      "(A-201 fan pitch / bypass); PA circulation FIC-2011; pan level LIC-2014 -> product FIC-2015.")
    a("- **HVGO section** - FIC-2016 circulation, TIC-2017 PA return temperature by E-108 PA-side bypass; pan "
      "level LIC-2018 -> HVGO product FIC-2019.")
    a("- **Wash oil (minimum flow)** - FIC-2020 SP = high select (FY-2020) of the MPC SP and a minimum wetting "
      "rate f(charge), protecting the wash bed against coking. Low-flow alarm is high priority.")
    a("- **Bottoms and quench** - LIC-2024 -> VR FIC-2025; boot temperature TIC-2026 (max 365 °C) cascades to "
      "the cooled-VR quench FIC-2027. Stripping steam FIC-2023 is ratioed to charge. Slop wax LIC-2021 -> "
      "FIC-2022.")
    a("![Figure 5 - VDU control (CFU-200-IC-CSD-005)](figures/" + F["CFU-200-IC-CSD-005"] + ")")
    a("## 3.7 Unit utilities")
    a("Fuel-gas header pressure PIC-9001 (D-103) with KO drum level LIC-9002; flare KO drum D-104 level LIC-9003 "
      "(pump-out P-119A/B start/stop); LP steam header PIC-9004 (let-down). Steam generators E-113 / E-201 use "
      "three-element level control (LIC-1110 / 2030: level + steam flow FF + BFW flow) with steam pressure "
      "PIC-1111 / let-down.")
    a("\\pagebreak")
    a("# 4. Level control tuning philosophy")
    a("Levels are classified as **averaging** (use the vessel hold-up to filter flow disturbances to the downstream "
      "unit - level allowed to swing between 25 % and 75 %) or **tight** (level itself matters: interfaces, draw "
      "pans, steam drums, seals). Surge time is the volume between 25 % and 75 % of span divided by the outflow. "
      "Averaging PI tuning: Kc 0.5-1.0 %/% and integral time ~ 4 x surge time (critically damped response to a "
      "step in inflow, level stays within the band); tight control: Kc 2-4 %/%, short integral. Error-squared or "
      "gap action is not used (non-linear behaviour hinders MPC identification).")
    a(_tbl(["Loop", "Service", "Vol. 25-75 % m3", "Outflow m3/h", "Surge min", "Mode", "Manipulates", "Tuning guide"],
           level_table()))
    a("# 5. Alarm philosophy (ISA-18.2 / IEC 62682)")
    a("Alarm management follows the ISA-18.2 life cycle: philosophy -> identification -> rationalisation -> "
      "detailed design -> implementation -> operation -> maintenance -> monitoring & assessment -> MOC -> audit. "
      "Every alarm must indicate an abnormal condition requiring a timely operator action; status and "
      "information go to the journal, not the alarm list. Rationalisation is done in a workshop (process, "
      "operations, I&C) and recorded in the master alarm database (L3 alarm management server).")
    a(_tbl(["Priority", "Consequence if no action", "Time to respond", "Target share", "Annunciation"], [
        ("Emergency (1)", "Safety / environment / major damage (pre-trip)", "< 5 min", "~ 5 %",
         "Red, audible tone 1, cannot be shelved"),
        ("High (2)", "Off-spec, equipment damage, unit upset", "5-15 min", "~ 15 %", "Orange, tone 2"),
        ("Low (3)", "Minor efficiency / quality loss", "15-30 min", "~ 80 %", "Yellow, tone 3"),
        ("Journal", "Status, diagnostics, events", "-", "-", "Event journal only"),
    ]))
    for s in [
        "**Performance targets (EEMUA 191)**: average alarm rate <= 1 per 10 min per console in steady operation; "
        "peak <= 10 alarms in 10 min after an upset; < 1 % of time in flood; no stale alarms > 24 h; no chattering "
        "(> 3 per minute).",
        "**Design rules**: deadbands and on/off delays per signal type (flow 2 %, 5 s; level 2 %, 10 s; pressure "
        "1 %, 5 s; temperature 1 °C, 15 s); SIS pre-trip alarms 5-10 % ahead of trip set point; deviation alarms "
        "for cascades only where the slave can saturate.",
        "**State-based alarming**: alarm sets switch with operating mode (start-up, normal, turndown, crude "
        "switch, shutdown) and with equipment status (spare pump, heater out of service).",
        "**Suppression and shelving**: designed suppression for consequential alarms after a trip (first-out "
        "kept); shelving time-limited (max 8 h) with shift-log review; emergency priority cannot be shelved.",
        "**SIS alarms**: SIS trips and first-out are displayed via the read-only SIS-DCS gateway; SIS bypasses and "
        "transmitter deviations alarm in the CCR.",
        "**KPIs**: monthly report from the alarm management server (top-10 bad actors, standing, chattering, "
        "flood periods), reviewed by operations.",
    ]:
        a(f"- {s}")
    a("\\pagebreak")
    a("# 6. Advanced process control (APC / MPC)")
    a("Three DMC-type multivariable predictive controllers run on a redundant L3 APC server with a common "
      "steady-state LP / QP optimiser: CDU (H-101, C-101, strippers, preheat), VDU (H-201, C-201, ejectors) "
      "and light ends (C-105, C-106). Execution 1 min; models from plant step tests after a regulatory tuning "
      "audit; crude-type gain scheduling for light / heavy blends. The MPC writes setpoints only to DCS loops in "
      "'MPC' cascade mode with SP clamps and rate limits; a watchdog sheds all loops to AUTO at the last SP on "
      "loss of communication.")
    a("![Figure 6 - APC / MPC structure (CFU-000-IC-CSD-006)](figures/" + F["CFU-000-IC-CSD-006"] + ")")
    a("## 6.1 Manipulated variables")
    a(_tbl(["MV", "DCS tag (SP)", "Description", "Range", "MPC"], T["mv"]))
    a("## 6.2 Controlled and constraint variables")
    a(_tbl(["CV", "Variable", "Measurement", "Type", "MPC"], T["cv"]))
    a("## 6.3 Disturbance variables")
    a(_tbl(["DV", "Disturbance", "Source"], T["dv"]))
    a("## 6.4 Inferential models (soft sensors)")
    a("Inferentials are linear / PLS models on pressure-compensated temperatures (PCT), flows and heat-balance "
      "terms, executed in the APC server and validated by online analysers (fast bias) and laboratory results "
      "(slow bias via LIMS). On analyser failure the inferential continues with frozen bias; after a time-out the "
      "CV is dropped from the MPC.")
    a(_tbl(["Inferential", "Main inputs", "Bias / validation"], T["inf"]))
    a("## 6.5 Online analysers")
    a("Analysers are housed in the analyser house AH-101 (UPS-fed, HVAC, gas detection) close to the sample points; "
      "fast-loop sample systems with return to process; validation by automatic line sample and lab "
      "correlation.")
    a(_tbl(["Tag", "Service", "Type", "Cycle", "Use"], analysers()))
    a("# 7. Start-up, shutdown, crude switch and turndown")
    a("## 7.1 Start-up")
    for s in [
        "Cold circulation (crude through preheat, H-101 coils and C-101 bottoms back to slop) on flow control with "
        "level loops in AUTO; heater passes on FIC with SIF-101 armed (permissive: all pass flows > LL + margin).",
        "H-101 / H-201 light-off by BMS sequence: purge (5 volume changes, air flow >= 25 %), pilot ignition with "
        "proof, main burners one by one; FG pressure on PIC-1021 in AUTO at minimum fire, COT ramp limited to "
        "50 °C/h by TIC-1020 SP ramp.",
        "Column pressure on PIC-1032 using FG make-up (PV-1032B); reflux established on FIC-1031 manual flow, "
        "TIC-1030 into cascade when the top temperature is meaningful; PAs started top to bottom on FIC with TICs "
        "in manual until duties stabilise.",
        "Side draws opened on FIC at low rate once trays are wet; stripping steam on ratio after product flow "
        "established; VDU started when AR quality is stable (vacuum pulled on ejectors with steam, PIC-2010 into "
        "AUTO; wash oil FIC-2020 established before H-201 COT exceeds 370 °C).",
        "MPC applications switched on after > 4 h of stable regulatory operation.",
    ]:
        a(f"- {s}")
    a("## 7.2 Normal shutdown")
    a("Reverse sequence with ramped SPs: MPC off, COT reduced to 300 °C (50 °C/h), draws closed progressively, "
      "heaters to minimum fire then burners out by BMS, circulation maintained until heater outlet < 200 °C, "
      "coil steam-out. Emergency shutdown is by SIS (ESD-1, SIF-901) per the C&E matrix.")
    a("## 7.3 Crude switch strategy")
    for s in [
        "Tank change signal (DV-01) and charge density AT-1048 (DV-02) trigger the crude-switch logic in the APC "
        "server: model gain set selected for the new crude, cut-point SPs pre-moved by the feed-forward, "
        "desalter chemical / wash ratios preset.",
        "COT and side-draw rates are moved with feed-forward on the measured density change; inferential bias "
        "updates are frozen for 2 h (analysers and lab confirm the new steady state).",
        "Regulatory layer: blending of tanks over ~30 min (OSBL) is preferred to a step change; FIC-1001 rate cut "
        "of 5-10 % during the switch is an operator option.",
    ]:
        a(f"- {s}")
    tmins = [r for r in cv if r["phase"] == "Liquid"]
    a("## 7.4 Turndown to 50 %")
    a(f"- H-101 / H-201 pass flow LL trips are set at 40 % of design pass flow, below the 50 % turndown, so the "
      "heaters can operate at turndown with margin; burners operate at ~ 45-50 % fire (turndown 3:1 burners).")
    a(f"- Control valves at 0.5 x normal flow: travel {min(r['travel_min'] for r in cv)}-"
      f"{max(r['travel_min'] for r in cv)} % (all >= 10 %, section 12).")
    a("- Orifice flow meters: at 50 % flow the dP is 25 % of span (rangeability 3:1 acceptable); pass flow and "
      "SIS flow transmitters are ranged so that the LL trip is above 20 % of span.")
    a("- Column internals: tray weeping limits the vapour rate to ~ 50-60 % of design; at turndown the stripping "
      "steam and pumparound ratios are kept, and the MPC keeps overflash and internal reflux minima.")
    a("- Pumps: minimum continuous flow by recirculation (P&ID); pumparound flows are kept above 60 % of design to "
      "keep exchangers in turbulent flow.")
    a("\\pagebreak")
    a("# 8. Safety instrumented systems (summary)")
    a("The SIFs below are implemented in the SIS (SIL 3-capable logic solver, separate from the DCS). Heater BMS "
      "functions run as separate applications on SIS hardware. SIL determination by LOPA is in CFU-000-IC-RPT-002; "
      "the cause & effect matrix is CFU-000-IC-CE-001.")
    a(_tbl(["SIF", "Function", "Initiators", "Final elements", "SIL (SRS)", "LOPA RRF", "LOPA SIL"],
           [(s["tag"], s["function"], s["initiators"], s["final_elements"], s["sil"],
             next((f"{x['rrf']:.0f}" if x["rrf"] else "-" for x in lp if x["sif"] == s["tag"]), "-"),
             next((x["sil"] for x in lp if x["sif"] == s["tag"]), "-")) for s in SF.values()]))
    a("![Figure 7 - Cause & effect matrix (CFU-000-IC-CE-001)](figures/" + F["CFU-000-IC-CE-001"] + ")")
    a("# 9. ICS architecture")
    a("The ICS follows the Purdue / ISA-95 model with a process DMZ (CFU-000-IC-BLK-001). The DCS has three "
      "redundant controller pairs in the field auxiliary room FAR-100 (CDU-1: charge, desalting, preheat, H-101, "
      "fuel gas; CDU-2: C-101, strippers, overhead, C-105, C-106; VDU: H-201, C-201, ejectors). The SIS logic "
      "solver (SIL 3 capable), the BMS applications and the F&G system are physically separate. Marshalling and "
      "system cabinets are in FAR-100; a redundant single-mode fibre ring connects FAR-100 to the OSBL central "
      "control room (CCR), where operator consoles, engineering stations and L3 servers are located.")
    a("![Figure 8 - ICS architecture (CFU-000-IC-BLK-001)](figures/" + F["CFU-000-IC-BLK-001"] + ")")
    if io:
        a("## 9.1 I/O summary (CFU-000-IC-IOL-001)")
        rows = []
        for ctl, d in io["totals"]["by_controller"].items():
            rows.append((ctl, d["system"], d["AI"]["used"], d["AO"]["used"], d["DI"]["used"], d["DO"]["used"],
                         d["used"], d["installed"], f"{100 * (d['installed'] - d['used']) / d['used']:.0f} %"))
        g = io["totals"]["grand"]
        rows.append(("TOTAL", "", "", "", "", "", g["used"], g["installed"],
                     f"{100 * (g['installed'] - g['used']) / g['used']:.0f} %"))
        a(_tbl(["Controller", "System", "AI", "AO", "DI", "DO", "Used", "Installed", "Spare"], rows))
        a("Points by source: " + "; ".join(f"{k}: {v}" for k, v in io["totals"]["by_source"].items()) + ".")
    a("## 9.2 IEC 62443 zones and conduits")
    from .arch import CONDUITS, ZONES
    a(_tbl(["Zone", "Name", "Target security level"], [(z[0], z[1], z[2]) for z in ZONES]))
    a(_tbl(["Conduit", "Zones", "Device", "Permitted traffic / controls"], CONDUITS))
    a("Power: all ICS cabinets have dual PSUs fed from UPS-101A / UPS-101B (data/electrical.json, 30 min autonomy); "
      "time synchronisation from a GPS master clock (NTP / PTP), 1 ms SOE in the SIS.")
    a("\\pagebreak")
    a("# 10. Instrument design criteria")
    for s in [
        "**Signals** - 4-20 mA with HART 7 for all analogue I/O (FOUNDATION Fieldbus H1 is an alternative for the "
        "DCS-only loops, not selected for FEED: HART gives one I/O per signal, simpler segregation and full asset "
        "management via HART multiplexers). Discrete: 24 VDC, NAMUR for IS proximity switches.",
        "**Hazardous area** - unit classified Zone 1 / 2, IIA / IIB T3 (HAC deliverable); transmitters Ex ia "
        "(intrinsically safe, galvanic isolators in FAR-100), solenoids and limit switches Ex ia or Ex d; "
        "analyser house AH-101 pressurised.",
        "**Pressure / dP** - smart electronic transmitters, 316 SS wetted parts (Hastelloy C for sour / H2S "
        "service per NACE MR0103), remote seals with capillary for viscous / hot service (> 300 °C AR, VR, HVGO) "
        "and for vacuum service (absolute pressure transmitters, 0-100 mbar(a) for C-201).",
        "**Flow** - orifice plates (ISO 5167) with dP transmitters as default; Coriolis for chemical injection and "
        "wash water; wedge meters or venturi for viscous VR / AR / quench; vortex for steam; ultrasonic clamp-on "
        "not used for control. Pass flows: one orifice per pass with 1 BPCS + 3 SIS transmitters on separate taps.",
        "**Level** - guided-wave radar for drums and columns (two technologies for SIS: GWR / dP), displacer not "
        "used; desalter interface by GWR + multi-point density profiler; vacuum column boot by dP with "
        "remote seals and purge.",
        "**Temperature** - type K thermocouples (duplex) with head-mounted transmitters; RTD Pt100 for < 300 °C "
        "quality-critical points (sensitive trays, PCT inputs); heater tube-skin thermocouples (knife-edge) on each "
        "pass; flanged thermowells (ASME PTC 19.3 TW wake-frequency check).",
        "**Control valves** - globe, cage-guided, equal-percentage trim (linear for level / dP service where the "
        "valve dP is near-constant), class IV seat leakage (class V for tight shut-off duties), smart HART "
        "positioners with partial-stroke capability where also used as SIS final element (not adopted: SIS uses "
        "dedicated XVs). Noise <= 85 dBA at 1 m.",
        "**On-off / SIS valves** - fire-safe ball or gate valves, spring-return actuators, 24 VDC de-energise-to-"
        "trip SOVs, ZSO / ZSC limit switches; ROSOVs (EIV-1121 / 2041) fire-proofed for 30 min.",
        "**Analysers** - see section 6.5; sample systems with heated / insulated lines, fast loop and return.",
        "**Instrument air** - 7 barg, dew point -40 °C (basis); each valve with filter-regulator; air failure "
        "positions stated on P&IDs (FO / FC).",
    ]:
        a(f"- {s}")
    a("# 11. Control valve sizing (ISA-75.01.01)")
    a("Key control valves are sized for the maximum case (1.2 x normal flow) and checked at turndown (0.5 x "
      "normal). Liquid Cv = Q / N1 x sqrt(G / dP), with dP limited to the choked value FL^2 (P1 - FF Pv); gas / "
      "steam valves with the expansion factor Y = 1 - x / (3 Fk xT), x limited to Fk xT. Valve dP allocations are "
      "FEED engineering judgement (stated); flows and densities from the H&MB (data/streams.json) and pump data "
      "(data/equipment.json). Body size: smallest size with travel <= 90 % at max flow (equal %, R = 50) and "
      ">= 10 % at turndown. Full calculation: CFU-000-IC-CAL-001 (xlsx).")
    a(_tbl(["Tag", "Service", "Normal flow", "rho kg/m3", "P1 bar(a)", "dP bar", "Cv norm", "Cv max",
            "Regime", "Size", "Rated Cv", "Travel max / min %", "Char."],
           [(r["tag"], r["service"], r["flow"], r["dens"], r["p1"], r["dp"], r["cv_norm"], r["cv_max"], r["regime"],
             f"{r['nps']}\" {r['body'].lower()}", r["cv_rated"], f"{r['travel_max']} / {r['travel_min']}",
             r["char"]) for r in cv]))
    a("Notes: (1) no liquid valve is choked or flashing at the allocated dP (LV-1007 brine checked against "
      "Pv at 136 °C); (2) PV-2010 is choked (vacuum service) - noise / velocity check and possibly a 2-stage "
      "trim at detailed design; (3) PV-1032A / PV-1032B sizing cases are assumptions (no H&MB flow - "
      "normally closed); (4) viscosity correction (FR) to be checked for VR (FV-2025) with vendor data.")
    a("# 12. Typical loop diagrams")
    a("Three typical loop diagrams (A3, ISA-5.4) are issued to fix the wiring philosophy: CFU-100-IC-LD-001 "
      "(FIC-1031 reflux flow, FT + FV with smart positioner), CFU-100-IC-LD-002 (TIC-1020 / PIC-1021 COT "
      "cascade) and CFU-100-IC-LD-003 (SIF-101 pass 1 low-low flow, 2oo3 FT -> SIS -> SSOVs with solenoids). "
      "JB, multicore, marshalling terminals and I/O card / channel come from the I/O list.")
    a("![Figure 9 - Loop diagram SIF-101 (CFU-100-IC-LD-003)](figures/" + F["CFU-100-IC-LD-003"] + ")")
    a("# 13. Open items, holds and interface notes")
    for s in issues(io):
        a(f"- {s}")
    a("\\pagebreak")
    a("# Appendix A - Principal control loop list")
    a(_tbl(["Tag", "Service", "Measured", "Final element / output", "Notes"],
           [(l["tag"], l["service"], l["measured"], l["final"], l["notes"]) for l in L.values()]))
    return "\n\n".join(md)


def issues(io):
    out = [
        "I&C additions to be added to the instrument index (CFU-000-IC-IDX-001) by the P&ID discipline: "
        "analysers AT-1021, AT-1038, AT-1046..1049, AT-1055, AT-1065, AT-1075, AT-1099, AT-1108, AT-1109, AT-2032; "
        "fuel gas flow FT-1021 / FT-2006 (cross-limiting); ambient TT-9005; analyser house alarm XA-9101; computing "
        "blocks FY-1011A..1018B, FY-1020A/B, FY-1021A/C, PY-1021A/B, FY-1025A..C, FFY-1054/1064/1074/1081/1094, "
        "FY-2020, PY-1032; heater snuffing steam HV-1290 / HV-2190.",
        "Instrument index: flame scanners BS-1028 / BS-2008 are listed with system 'DCS' - they are BMS (SIS "
        "logic solver) inputs; UZ-9000 (ESD logic) carries signal '4-20 mA HART (SIS AI)' - it is a logic "
        "function with no field I/O; ZSC-1231 / ZSC-1232 duplicate the limit switches already included with "
        "XV-1021 / XV-1022 (signal 'DO + 2 x DI') - counted once in the I/O list.",
        "F&G field devices are not yet in the instrument index (only GD-1284 / 1285 and BY-1121 / 2041); the I/O "
        "list carries a per-fire-zone allowance until the F&G mapping study is done.",
        "Motor interfaces (run / fault DI, start / stop DO) are hardwired allowances derived from equipment.json; "
        "a serial / IEC 61850 MCC interface would remove ~ 250 hardwired points (decision at detailed design).",
        "Burner FG pressure trip settings (0.15 / 2.2 barg), the burner curve and minimum fire are FEED "
        "assumptions pending burner vendor data.",
        "PV-1032A / PV-1032B and PV-2010 sizing flows are assumptions (no H&MB case for normally-closed duties).",
        "CCR distance (fibre route ~ 800 m) is an assumption; CCR building, consoles and L3 servers are OSBL scope "
        "shared with the refinery.",
        "Drawing frame: the common A3 title block (cfu/drawing/sheet.py, 170 x 50 mm) leaves the drawing-number row "
        "only 4 mm high so the number overlaps the frame; the I&C loop diagrams use a local subclass with the "
        "A1-size block. Fix in sheet.py recommended (process / drawing owner).",
        "LOPA frequencies, consequence categories and IPL credits are FEED judgements; to be confirmed in the SIL "
        "workshop after HAZOP close-out.",
    ]
    return out


# =========================================================================== RPT-002
def rpt002():
    SF = sifs()
    lp = ce.lopa()
    rows = ce.initiators()
    md = []
    a = md.append
    a("# 1. Purpose")
    a("This report lists the safety instrumented functions (SIFs) of the CDU / VDU, summarises the SIL "
      "determination by layer of protection analysis (LOPA), and documents the trip set-point basis used in the "
      "cause & effect matrix CFU-000-IC-CE-001. It is the FEED input to the Safety Requirements Specification "
      "(SRS, IEC 61511-1 clause 10).")
    a("# 2. Method")
    for s in [
        "Scenarios from the preliminary HAZOP (CFU-000-PR-RPT-002) and the SIF list in `cfu/control_loops.py`.",
        "Tolerable / target mitigated event likelihood (TMEL) by consequence category: C5 multiple fatalities "
        "1e-6 /yr, C4 single fatality 1e-5 /yr, C3 serious injury / major environmental or asset 1e-4 /yr, "
        "C2 1e-3 /yr.",
        "Initiating event frequencies and IPL PFDs are CCPS typical values: BPCS loop failure 0.1 /yr; operator "
        "response to an independent alarm with >= 10 min available 0.1; PSV 0.01. Conditional modifiers "
        "(ignition, occupancy) are applied explicitly.",
        "Required risk reduction RRF = (IEF x prod(IPL PFD) x prod(CM)) / TMEL; SIL 1: 10 < RRF <= 100, SIL 2: "
        "100 < RRF <= 1000, SIL 3: 1000 < RRF <= 10000.",
        "Manual ESD (SIF-901) is assigned SIL 2 by company practice (no LOPA scenario).",
    ]:
        a(f"- {s}")
    a("# 3. SIF list")
    vote = {r["sif"]: r["vote"] for r in rows}
    rt = {r["sif"]: r["rt"] for r in rows}
    a(_tbl(["SIF", "Function", "Initiators", "Voting", "Final elements", "SIL", "Response", "Proof test"],
           [(s["tag"], s["function"], s["initiators"], vote.get(s["tag"], "-"), s["final_elements"], s["sil"],
             rt.get(s["tag"], "-"), "12 months" if s["sil"] == "SIL 2" else "24 months") for s in SF.values()]))
    a("# 4. LOPA / SIL determination")
    a("**4.1 Scenarios and initiating events**")
    a(_tbl(["SIF", "Hazard scenario", "Initiating event (IEF /yr)", "Consequence (TMEL /yr)"],
           [(L["sif"], L["scenario"], f"{L['ie']} ({L['ief'] if L['ief'] else '-'})",
             f"{L['cat']} ({L['tmel']:.0e})") for L in lp]))
    a("**4.2 Independent protection layers, conditional modifiers and required risk reduction**")
    a(_tbl(["SIF", "IPLs (PFD)", "Conditional modifiers", "MEL w/o SIF", "RRF", "SIL (LOPA)", "SIL (SRS)"],
           [(L["sif"], "; ".join(f"{n} ({p:g})" for n, p in L["ipls"]) or "-",
             "; ".join(f"{n} ({p:g})" for n, p in L["cms"]) or "-",
             f"{L['mel']:.1e}" if L["mel"] else "-", f"{L['rrf']:.0f}" if L["rrf"] else "-",
             L["sil"] + ("" if L["match"] else " (REVIEW)"), L["srs"]) for L in lp]))
    n_ok = sum(1 for L in lp if L["match"])
    cnt = {}
    for s in SF.values():
        cnt[s["sil"]] = cnt.get(s["sil"], 0) + 1
    a(f"**Result:** {len(lp)} SIFs assessed; {n_ok} LOPA results are consistent with the SIL in the SIF list. "
      f"SIL distribution: " + ", ".join(f"{k}: {v}" for k, v in sorted(cnt.items())) + ". No SIL 3 function is "
      "required; the logic solver is nevertheless SIL 3 capable to allow future changes without hardware "
      "replacement.")
    a("# 5. Trip set-point basis")
    for s in ce.SETPOINT_BASIS:
        a(f"- {s}")
    a(_tbl(["Initiator", "SIF", "Description", "Voting", "Normal", "Trip", "Response"],
           [(r["tag"], r["sif"], r["desc"], r["vote"], r["normal"], r["sp"], r["rt"]) for r in rows
            if r["sif"] != "F&G"]))
    a("# 6. SRS requirements (FEED)")
    for s in [
        "SIS sensors, logic solver and final elements independent of the BPCS (separate taps, transmitters, "
        "cables, JBs and cabinets); BPCS valves are not credited as SIS final elements.",
        "2oo3 voting for continuous analogue initiators on heaters (degrade to 2oo2 on fault, 1oo1 trip on "
        "two faults); 1oo1 for SIL 1 level / pressure functions with BPCS-transmitter comparison alarm.",
        "De-energise to trip for all SIFs; line monitoring on SOV outputs; fail-safe on loss of power or air.",
        "Bypasses for maintenance only via key-switch with time limit and CCR alarm; operational overrides "
        "(start-up) auto-reset.",
        "Proof-test intervals: SIL 2 12 months (partial-stroke tests of SSOVs every 3 months), SIL 1 24 months; "
        "PFDavg to be verified with vendor data (IEC 61508 certified devices or prior use).",
        "Response times per SIF (table above) include sensor, logic solver and final element closure; SSOV "
        "closure <= 2 s, ROSOV <= 30 s.",
        "BMS: NFPA 85 / 86 and API 556 sequences (purge, pilot proving, flame supervision, safety time 4 s).",
    ]:
        a(f"- {s}")
    a("# 7. F&G executive actions")
    a("Confirmed gas (2ooN at 50 % LEL) or confirmed fire per fire zone initiate the actions shown in the C&E "
      "matrix: beacons / PAGA, isolation of fuel to the heaters in the heater zone, ROSOV closure for the hot "
      "pumps P-112 / P-204 in their zones and the signal to the OSBL fire-water pumps. F&G is a SIL 2 system; "
      "performance targets (coverage, detector voting) from the F&G mapping study.")
    return "\n\n".join(md)


def build(io=None):
    F = _figs()
    docgen.render(rpt001(F, io), OUT / "CFU-000-IC-RPT-001_Control-Philosophy", "CFU-000-IC-RPT-001",
                  "Control Philosophy & Proposed Control Scheme")
    docgen.render(rpt002(), OUT / "CFU-000-IC-RPT-002_SIF-List-SIL-Determination", "CFU-000-IC-RPT-002",
                  "SIF List & SIL Determination (LOPA)")
