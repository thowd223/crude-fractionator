"""Pump FEED data: suction source, NPSHa estimate, speed selection and NPSHr estimate.

NPSHr estimate from suction-specific speed S = n.sqrt(Q)/NPSHr^0.75 = 200 (metric: rpm, m3/s, m;
~10,300 US units - refinery limit 11,000).  Double-suction first-stage impeller above 500 m3/h.
Vapour pressures marked (est.) are engineering estimates to be confirmed by process.
"""
from __future__ import annotations

import math

from .common import G, equipment, results, round_up, streams

S_SS = 200.0
PUMP_CL = 0.8          # m above grade (EL 100.800)
LOSS = 0.6             # m suction line + strainer losses


def npshr_est(q_m3h, n, double=False):
    q = q_m3h / 3600 / (2 if double else 1)
    return (n * math.sqrt(q) / S_SS) ** (4 / 3)


def _speed(p, boiling):
    hot = p["T"] > 200
    return 1780 if (hot and boiling and p["flow_m3h"] > 60) else 3560


# Suction sources: (source, kind, data)
#   kind 'vessel'  : boiling liquid in vessel, NPSHa = static - losses (z_src = LLL elevation above grade)
#   kind 'press'   : sub-cooled supply at known pressure (bar a) with vapour pressure Pv (bar a)
def sources(col_elev):
    S = streams()
    R = results()
    el = col_elev       # dict tag -> dict(BTL=..., draw z's) supplied by calc
    return {
        "P-101": ("Crude tank (OSBL) via suction header", "press", dict(P=S["1"]["P_bara"], Pv=0.70, est=True)),
        "P-102": ("D-101B desalted crude outlet", "press", dict(P=S["5"]["P_bara"], Pv=6.0, est=True)),
        "P-103": ("D-102 HC compartment (bubble point)", "vessel", dict(LLL=el["D-102"]["LLL"], P=R["atm"]["drum_P_barg"] + 1.013)),
        "P-104": ("D-102 HC compartment (bubble point)", "vessel", dict(LLL=el["D-102"]["LLL"], P=R["atm"]["drum_P_barg"] + 1.013)),
        "P-105": ("D-102 water boot", "press", dict(P=R["atm"]["drum_P_barg"] + 1.013 + 990 * G * (el["D-102"]["boot_LLL"] - PUMP_CL) / 1e5,
                                                    Pv=0.096, est=False)),
        "P-106": ("C-101 tray 3 draw sump", "vessel", dict(LLL=el["C-101"]["draw"][3], P=2.2)),
        "P-107": ("C-101 tray 13 draw sump", "vessel", dict(LLL=el["C-101"]["draw"][13], P=2.3)),
        "P-108": ("C-101 tray 25 draw sump", "vessel", dict(LLL=el["C-101"]["draw"][25], P=2.4)),
        "P-109": ("C-102 bottoms", "vessel", dict(LLL=el["C-102"]["LLL"], P=2.3)),
        "P-110": ("C-103 bottoms", "vessel", dict(LLL=el["C-103"]["LLL"], P=2.4)),
        "P-111": ("C-104 bottoms", "vessel", dict(LLL=el["C-104"]["LLL"], P=2.5)),
        "P-112": ("C-101 bottoms", "vessel", dict(LLL=el["C-101"]["LLL"], P=R["atm"]["P_fz_barg"] + 1.013)),
        "P-114": ("Stripped sour water / utility water (OSBL) at 1.0 barg (assumed)", "press", dict(P=2.0, Pv=0.12, est=True)),
        "P-115": ("D-105 (bubble point)", "vessel", dict(LLL=el["D-105"]["LLL"], P=11.5)),
        "P-116": ("D-106 (bubble point)", "vessel", dict(LLL=el["D-106"]["LLL"], P=1.8)),
        "P-117": ("C-106 bottoms", "vessel", dict(LLL=el["C-106"]["LLL"], P=R["split"]["P_bot"])),
        "P-118": ("D-101A/B brine (sub-cooled water at 11.5 barg)", "press", dict(P=12.5, Pv=2.0, est=True)),
        "P-119": ("D-104 flare KO drum (liquid at bubble point, 0.2 barg)", "press", dict(P=1.25, Pv=1.21, est=True)),
        "P-201": ("C-201 LVGO collector", "vessel", dict(LLL=el["C-201"]["draw"]["LVGO"], P=0.03)),
        "P-202": ("C-201 HVGO collector", "vessel", dict(LLL=el["C-201"]["draw"]["HVGO"], P=0.045)),
        "P-203": ("C-201 slop wax collector", "vessel", dict(LLL=el["C-201"]["draw"]["SLOP"], P=0.058)),
        "P-204": ("C-201 boot (quenched VR)", "vessel", dict(LLL=el["C-201"]["LLL"], P=0.07)),
        "P-205": ("D-201 hotwell water compartment", "press", dict(P=1.063 + 990 * G * (el["D-201"]["LLL"] - PUMP_CL) / 1e5,
                                                                   Pv=0.096, est=False)),
        "P-206": ("D-201 slop oil compartment", "press", dict(P=1.063 + 850 * G * (el["D-201"]["LLL"] - PUMP_CL) / 1e5,
                                                              Pv=0.05, est=True)),
    }


def column_bottom_npshr():
    """NPSHr of bottoms pumps used to set column skirt heights (speed fixed by service)."""
    out = {}
    for e in equipment():
        if e["type"] != "Pump":
            continue
        base = e["tag"][:5]
        p = dict(T=e["T"], flow_m3h=e["flow_m3h"])
        n = _speed(p, True)
        out[base] = (npshr_est(e["flow_m3h"], n, e["flow_m3h"] > 500), n)
    return out


def pump_data(col_elev):
    src = sources(col_elev)
    out = []
    for e in equipment():
        if e["type"] != "Pump":
            continue
        base = e["tag"][:5]
        name, kind, d = src[base]
        rho = e["rho"]
        q = e["flow_m3h"]
        boiling = kind == "vessel"
        n = _speed(e, boiling)
        double = q > 500
        if kind == "vessel":
            static = d["LLL"] - PUMP_CL
            npsha = static - LOSS
            Ps = d["P"] + rho * G * static / 1e5 - rho * G * LOSS / 1e5          # bar a
        else:
            npsha = (d["P"] - d["Pv"]) * 1e5 / (rho * G) - LOSS
            Ps = d["P"] - rho * G * LOSS / 1e5
        nr = npshr_est(q, n, double)
        if npsha < nr + 1.0 and n == 3560:
            n = 1780
            nr = npshr_est(q, n, double)
        Pd = Ps + e["dP_bar"]
        stages = 1 if e["head_m"] <= (250 if n == 3560 else 150) else 2
        out.append(dict(tag=e["tag"], service=e["service"], source=name, kind=kind, rho=rho, T=e["T"], q_rated=q,
                        q_normal=q / 1.10, head=e["head_m"], dP=e["dP_bar"], Ps_barg=Ps - 1.013, Pd_barg=Pd - 1.013,
                        npsha=npsha, npshr_est=nr, margin=npsha - nr, speed=n, double_suction=double, stages=stages,
                        eta=e["eta"], bkw=e["absorbed_kw"], motor=e["motor_kw"], api610=e["api610"],
                        seal=e["seal"], moc=e["moc"], des_T=e["des_T"], spare=e["tag"].endswith("A/B"),
                        Pv_est=d.get("est", False), area=e["area"],
                        voltage="4.16 kV" if e["motor_kw"] >= 200 else "480 V",
                        weight_t=round(((0.8 + 0.017 * e["motor_kw"]) if e["api610"].startswith("BB")
                                        else (0.3 + 0.012 * e["motor_kw"])), 1)))
    return out
