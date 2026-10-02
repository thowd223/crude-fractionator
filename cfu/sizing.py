"""Equipment sizing (FEED level) from the heat & material balance."""
from __future__ import annotations

import math

import numpy as np

from . import basis
from .hmb import Model

D = basis.DESIGN
STD_MOTORS = [0.75, 1.1, 1.5, 2.2, 3.7, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200,
              250, 315, 355, 400, 450, 500, 560, 630, 710, 800, 900, 1000, 1120, 1250, 1400, 1600, 1800, 2000]
API526 = [("D", 71), ("E", 126), ("F", 198), ("G", 324), ("H", 506), ("J", 830), ("K", 1186), ("L", 1841),
          ("M", 2323), ("N", 2800), ("P", 4116), ("Q", 7129), ("R", 10323), ("T", 16774)]


def motor(kw):
    for m in STD_MOTORS:
        if m >= kw * 1.15:
            return m
    return math.ceil(kw * 1.15 / 100) * 100


def design_P(op_barg):
    if op_barg < 0:
        return "FV / 3.5"
    return round(max(op_barg * 1.1, op_barg + 1.7, 3.5), 1)


def design_T(op_C):
    return int(math.ceil((op_C + 28) / 5) * 5)


def round_up(x, step):
    return math.ceil(x / step) * step


# ---------------------------------------------------------------------------
def tray_diameter(sec, TS_mm=610, flood=0.80, net_frac=0.85, sigma=15.0):
    V, L = sec["V_kg_h"], sec["L_kg_h"]
    rv, rl = sec["rho_v"], sec["rho_l"]
    flv = (L / V) * math.sqrt(rv / rl)
    C = (0.0105 + 8.127e-4 * TS_mm ** 0.755 * math.exp(-1.463 * flv ** 0.842)) * (sigma / 20) ** 0.2
    uf = C * math.sqrt((rl - rv) / rv)
    Q = V / 3600 / rv
    A_net = Q / (flood * uf)
    A = A_net / net_frac
    Dm = math.sqrt(4 * A / math.pi)
    return dict(FLV=flv, C_sb=C, u_flood=uf, Q_v_m3s=Q, D_calc=Dm, passes=1 if Dm < 2 else 2 if Dm < 5 else 4)


def packing_diameter(sec, Cs=0.11):
    rv, rl = sec["rho_v"], sec["rho_l"]
    u = Cs / math.sqrt(rv / (rl - rv))
    Q = sec["V_kg_h"] / 3600 / rv
    return dict(Q_v_m3s=Q, u_allow=u, D_calc=math.sqrt(4 * Q / u / math.pi))


def lmtd(Thi, Tho, Tci, Tco):
    d1, d2 = Thi - Tco, Tho - Tci
    if d1 <= 0 or d2 <= 0:
        return 1.0
    return (d1 - d2) / math.log(d1 / d2) if abs(d1 - d2) > 1e-6 else d1


def F_shells(Thi, Tho, Tci, Tco, N):
    """F-factor for N 1-2 shells in series (Bowman)."""
    R = (Thi - Tho) / max(Tco - Tci, 1e-6)
    P = (Tco - Tci) / max(Thi - Tci, 1e-6)
    if abs(R - 1) < 1e-4:
        R = 1.0001
    X = ((1 - R * P) / (1 - P)) ** (1 / N)
    Pn = (X - 1) / (X - R)
    s = math.sqrt(R * R + 1)
    try:
        num = s * math.log((1 - Pn) / (1 - R * Pn)) / (R - 1)
        den = math.log((2 - Pn * (R + 1 - s)) / (2 - Pn * (R + 1 + s)))
        return num / den
    except (ValueError, ZeroDivisionError):
        return 0.0


U_SERV = {"TPA": 330, "KERO": 300, "LVGO": 280, "DIESEL": 290, "VR": 170, "MPA": 320, "HVGO": 250, "AGO": 260,
          "BPA": 280}


def size_exchanger(e, U, max_area=650.0):
    for N in range(1, 7):
        F = F_shells(e["Th_in"], e["Th_out"], e["Tc_in"], e["Tc_out"], N)
        if F >= 0.80:
            break
    lm = lmtd(e["Th_in"], e["Th_out"], e["Tc_in"], e["Tc_out"])
    A = e["Q_kw"] * 1000 / (U * F * lm) if e["Q_kw"] > 0 else 0
    par = max(1, math.ceil(A / N / max_area))
    return dict(U=U, LMTD=lm, F=F, area_m2=A, series=N, parallel=par, shells=N * par,
                area_per_shell=A / (N * par) if A else 0)


# ---------------------------------------------------------------------------
def build(m: Model) -> dict:
    a, v = m.res["atm"], m.res["vac"]
    st, sp = m.res["stab"], m.res["split"]
    eq: list[dict] = []
    E = eq.append

    # ---------------- C-101 atmospheric column -------------------------------
    secs = []
    for s in a["sections"]:
        TS = 760 if "PA" in s["name"] else 610
        r = tray_diameter(s, TS_mm=TS)
        secs.append({**s, **r, "TS_mm": TS})
    top_D = round_up(max(r["D_calc"] for r in secs[:2]) * 1.0, 0.1)
    mid_D = round_up(max(r["D_calc"] for r in secs[2:7]), 0.1)
    bot_D = round_up(secs[7]["D_calc"], 0.1)
    D_main = max(top_D, mid_D)
    bot_D = max(bot_D, 0.6 * D_main)
    tray_h = 28 * 0.61 + 9 * 0.76 + 3 * 0.61
    sump = (a["prod"]["AR"].sum() / secs[7]["rho_l"] / 60 * 5) / (math.pi / 4 * bot_D ** 2)  # 5 min
    H101 = round_up(2.0 + tray_h + 4.0 + 6 * 0.61 + 1.5 + sump + 1.0, 0.5)
    E(dict(tag="C-101", type="Column", service="Atmospheric crude fractionator", area="CDU",
           size=f"ID {D_main:.1f} m (top/main) / {bot_D:.1f} m (stripping) x {H101:.1f} m T/T",
           D=D_main, D2=bot_D, H=H101, orient="V", internals="41 valve trays (2/4-pass), 410S; Monel-lined top 5 trays",
           op_P=f"{a['Ptray'](1) - 1.013:.2f} / {a['P_fz'] - 1.013:.2f}", op_T=f"{a['T_top']:.0f} / {a['T_fz']:.0f}",
           des_P=3.5, des_T=design_T(a["T_fz"]), moc="CS + 410S clad below tray 10; Monel 400 lined top head & trays 1-5",
           ca_mm=3, sections=secs, weight_t=round(D_main * H101 * 2.6, 0)))

    # side strippers (6 trays each, size on draw liquid)
    for tag, p in [("C-102", "KERO"), ("C-103", "DIESEL"), ("C-104", "AGO")]:
        draw = a["prod"][p].sum() * 1.10
        rl = float((a["prod"][p] * m.sl.rho_l(a["T_draw"][p])).sum() / a["prod"][p].sum())
        steam = a["steam"][p]
        Vm = steam + 0.10 * a["prod"][p].sum()
        mwv = Vm / (steam / 18 + 0.10 * a["prod"][p].sum() / m.mw(a["prod"][p]))
        P = a["Ptray"](a["tray"][p])
        rv = P * 1e5 * mwv / (8314 * (a["T_draw"][p] + 273))
        r = tray_diameter(dict(V_kg_h=Vm, L_kg_h=draw, rho_v=rv, rho_l=rl), TS_mm=610, flood=0.7, net_frac=0.75)
        # liquid-limited: downcomer velocity 0.10 m/s => min area
        A_dc = draw / 3600 / rl / 0.10
        Dm = round_up(max(r["D_calc"], math.sqrt(4 * A_dc / 0.25 / math.pi)), 0.1)
        E(dict(tag=tag, type="Column", service=f"{p.title()} side stripper", area="CDU",
               size=f"ID {Dm:.1f} m x {6 * 0.61 + 5.5:.1f} m T/T", D=Dm, H=round(6 * 0.61 + 5.5, 1), orient="V",
               internals="6 valve trays, 410S", op_P=f"{P - 1.013:.2f}", op_T=f"{a['T_draw'][p]:.0f}",
               des_P=3.5, des_T=design_T(a["T_draw"][p]), moc="CS + 410S clad" if a["T_draw"][p] > 260 else "CS",
               ca_mm=3 if a["T_draw"][p] < 260 else 6))

    # stabiliser / splitter
    for col, tag, name, P in [(st, "C-105", "Naphtha stabiliser (debutaniser)", st["P_top"]),
                              (sp, "C-106", "Naphtha splitter", sp["P_top"])]:
        Vt = col["d"].sum() * (1 + col["R"])
        mwv = m.mw(col["d"])
        rv = P * 1e5 * mwv / (8314 * (col["T_top"] + 273))
        rl = float((col["d"] * m.sl.rho_l(col["T_top"])).sum() / col["d"].sum())
        r1 = tray_diameter(dict(V_kg_h=Vt, L_kg_h=col["reflux"], rho_v=rv, rho_l=rl), sigma=8 if tag == "C-105" else 14)
        Lb = col["b"].sum() + col["reflux"] + col["d"].sum()
        rlb = float((col["b"] * m.sl.rho_l(col["T_bot"])).sum() / col["b"].sum())
        rvb = col["P_bot"] * 1e5 * m.mw(col["b"]) / (8314 * (col["T_bot"] + 273))
        r2 = tray_diameter(dict(V_kg_h=Vt * 1.05, L_kg_h=Lb, rho_v=rvb, rho_l=rlb), sigma=8 if tag == "C-105" else 12)
        Dm = round_up(max(r1["D_calc"], r2["D_calc"]), 0.1)
        H = round_up(col["N_actual"] * 0.61 + 2 + 1.2 + 3.0, 0.5)
        col.update(D=Dm, H=H, sec_top=r1, sec_bot=r2)
        E(dict(tag=tag, type="Column", service=name, area="CDU",
               size=f"ID {Dm:.1f} m x {H:.1f} m T/T", D=Dm, H=H, orient="V",
               internals=f"{col['N_actual']} valve trays, feed tray {col['feed_stage']}",
               op_P=f"{P - 1.013:.1f}", op_T=f"{col['T_top']:.0f} / {col['T_bot']:.0f}",
               des_P=design_P(col["P_bot"] - 1.013), des_T=design_T(col["T_bot"]),
               moc="CS (HIC-resistant plate, NACE MR0103)" if tag == "C-105" else "CS", ca_mm=3))

    # ---------------- C-201 vacuum column -----------------------------------
    vsecs = []
    for s in v["sections"]:
        if s["name"] == "Stripping":
            r = tray_diameter(s, TS_mm=610, flood=0.75)
        else:
            r = packing_diameter(s, Cs=0.12 if "Wash" in s["name"] else 0.11)
        vsecs.append({**s, **r})
    D_top = round_up(vsecs[0]["D_calc"], 0.2)
    D_mid = round_up(max(x["D_calc"] for x in vsecs[1:5]), 0.2)
    D_bot = round_up(max(vsecs[5]["D_calc"], 0.45 * D_mid), 0.2)
    Hvac = round_up(3 + 2.5 + 2.5 + 2.0 + 2.5 + 3.5 + 2.5 + 1.2 + 2.5 + 5.0 + 4 * 0.61 + 6.0, 0.5)
    E(dict(tag="C-201", type="Column", service="Vacuum column (wet, packed)", area="VDU",
           size=f"ID {D_top:.1f} m (top) / {D_mid:.1f} m (main) / {D_bot:.1f} m (boot) x {Hvac:.1f} m T/T",
           D=D_mid, D2=D_bot, D3=D_top, H=Hvac, orient="V",
           internals="4 packed beds (structured 250Y/grid), 4 stripping trays, vapour horn",
           op_P=f"{v['P_top'] * 1000:.0f} / {v['P_fz'] * 1000:.0f} mbar(a)", op_T=f"{v['T_top']:.0f} / {v['T_fz']:.0f}",
           des_P="FV / 3.5", des_T=design_T(v["T_fz"]), moc="CS + 410S clad (317L clad flash/wash zone)",
           ca_mm=6, sections=vsecs, weight_t=round(D_mid * Hvac * 2.8)))

    # ---------------- fired heaters ------------------------------------------
    heaters = {}
    for tag, h, flux, npass, OD, L, name in [
            ("H-101", m.res["H-101"], D["rad_flux_kW_m2"], 8, 0.1683, 18.3, "Atmospheric crude charge heater"),
            ("H-201", m.res["H-201"], 25.0, 4, 0.1683, 18.3, "Vacuum heater")]:
        Qr = h["Q_proc_kw"] * D["rad_fraction"]
        Arad = Qr / flux
        ntubes = round_up(Arad / (math.pi * OD * L), npass)
        G = h["flow"] / 3600 / npass / (math.pi / 4 * 0.1463 ** 2)
        burners = math.ceil(h["Q_fired_kw"] / 1000 / (4.5 if tag == "H-101" else 3.0))
        burners = round_up(burners, 2)
        vol = h["Q_fired_kw"] / 75.0
        cells = 2 if tag == "H-101" else 1
        W = round(math.sqrt(vol / cells / 14) * 1.0 + 1, 1)
        heaters[tag] = h
        h.update(radiant_kw=Qr, conv_kw=h["Q_abs_kw"] - Qr, rad_area=Arad, rad_tubes=ntubes, passes=npass,
                 mass_flux=G, burners=burners, cells=cells, firebox_m3=vol)
        E(dict(tag=tag, type="Fired heater", service=name, area="CDU" if tag == "H-101" else "VDU",
               size=f"{h['Q_abs_kw'] / 1000:.1f} MW abs. / {h['Q_fired_kw'] / 1000:.1f} MW fired; {cells}-cell cabin, "
                    f"{npass} passes, {ntubes} rad. tubes 6\" x {L} m",
               orient="V", D=None, L=12.0 * cells + 2, W=W + 6, H=38.0 if tag == "H-101" else 32.0,
               op_P=f"{h['P_out'] - 1.013:.2f} outlet", op_T=f"{h['T_in']:.0f} -> {h['T_out']:.0f}",
               des_P=design_P(35 if tag == "H-101" else 18), des_T=design_T(h["T_out"]) + 60,
               moc="Tubes A335 P9 (9Cr-1Mo); convection P5 / CS studded", ca_mm=3,
               duty_kw=h["Q_abs_kw"], motor_kw=None))
    # APH and draft fans for H-101 (balanced draft)
    fg_flow = m.res["H-101"]["fuel_kg_h"] * 18.5  # flue gas kg/h at 15 % excess air
    for tag, name, kw in [("K-101A/B", "H-101 forced-draft fan", fg_flow / 3600 / 1.2 * 2500 / 0.75 / 1000),
                          ("K-102A/B", "H-101 induced-draft fan", fg_flow / 3600 / 0.65 * 3000 / 0.72 / 1000)]:
        E(dict(tag=tag, type="Fan", service=name, area="CDU", size=f"{fg_flow / 1000:.0f} t/h flue gas",
               motor_kw=motor(kw), absorbed_kw=kw, orient="H", L=6, W=3, H=4))
    E(dict(tag="E-120", type="Air preheater", service="H-101 cast-iron/glass-tube air preheater", area="CDU",
           size="Flue gas 380 -> 160 C", orient="V", L=8, W=6, H=10, des_T=450, moc="Cast iron / borosilicate"))

    # ---------------- shell & tube -----------------------------------------
    p = m.res["preheat"]
    hx_list = []
    names = {"TPA": "Top pumparound", "KERO": "Kerosene product", "LVGO": "LVGO pumparound/product",
             "DIESEL": "Diesel product", "VR": "Vacuum residue", "MPA": "Middle (kero) pumparound",
             "HVGO": "HVGO pumparound/product", "AGO": "AGO product", "BPA": "Bottom (diesel) pumparound"}
    for e in p["exch"]:
        if e["Q_kw"] <= 1:
            continue
        r = size_exchanger(e, U_SERV[e["hot"]])
        hot_tube = e["hot"] in ("VR",)
        temax = max(e["Th_in"], e["Tc_out"])
        moc = "CS shell / CS tubes" if temax < 230 else ("CS shell / 5Cr-1/2Mo tubes" if temax < 300
                                                        else "1.25Cr shell / 9Cr-1Mo tubes")
        hx = dict(tag=e["tag"], type="Shell & tube", service=f"Crude / {names[e['hot']]}", area="CDU",
                  tema="AES" if not hot_tube else "AES (crude tubeside)", duty_kw=e["Q_kw"],
                  size=f"{r['area_m2']:.0f} m2 total; {r['series']}S x {r['parallel']}P shells",
                  op_T=f"H {e['Th_in']:.0f}->{e['Th_out']:.0f} / C {e['Tc_in']:.0f}->{e['Tc_out']:.0f}",
                  shellside="Crude" if not hot_tube else names[e["hot"]],
                  tubeside=names[e["hot"]] if not hot_tube else "Crude",
                  des_P="30 / 20", des_T=design_T(temax), moc=moc, ca_mm=3 if temax < 260 else 6,
                  orient="H", L=7.5, D=1.4 if r["area_per_shell"] > 400 else 1.1, n_shells=r["shells"], **r,
                  **{k: e[k] for k in ("Th_in", "Th_out", "Tc_in", "Tc_out")})
        hx_list.append(hx)
        E(hx)

    def simple_hx(tag, service, Q, U, Thi, Tho, Tci, Tco, tema, shell, tube, moc="CS", desP="15 / 10", typ="Shell & tube"):
        A = Q * 1000 / (U * 0.9 * lmtd(Thi, Tho, Tci, Tco))
        sh = max(1, math.ceil(A / 650))
        d = dict(tag=tag, type=typ, service=service, area="CDU" if tag[2] == "1" else "VDU", tema=tema, duty_kw=Q,
                 size=f"{A:.0f} m2; {sh} shell(s)", area_m2=A, n_shells=sh, U=U,
                 op_T=f"H {Thi:.0f}->{Tho:.0f} / C {Tci:.0f}->{Tco:.0f}", shellside=shell, tubeside=tube,
                 des_P=desP, des_T=design_T(max(Thi, Tco)), moc=moc, ca_mm=3, orient="H", L=6.5,
                 D=1.2 if A / sh > 300 else 0.9, Th_in=Thi, Th_out=Tho, Tc_in=Tci, Tc_out=Tco)
        hx_list.append(d)
        E(d)

    trims = {t["tag"]: t for t in p["trims"]}
    t = trims.get("E-113")
    if t:
        simple_hx("E-113", "BPA / MP steam generator (kettle)", t["Q_kw"], 450, t["T_in"], t["T_out"], 186, 186,
                  "AKT", "BFW / MP steam", "Bottom pumparound", desP="13 / 20")
    t = trims["E-201"]
    simple_hx("E-201", "VR / LP steam generator (kettle)", t["Q_kw"], 200, t["T_in"], t["T_out"], 148, 148, "AKT",
              "BFW / LP steam", "Vacuum residue", moc="CS shell / 5Cr tubes", desP="6 / 20")
    simple_hx("E-114", "Stabiliser feed / bottoms", st["Q_fb"], 380, st["T_bot"], sp["T_feed"], st["T_feed_in"],
              st["T_feed"], "AES", "Unstab. naphtha", "Stabiliser bottoms", desP="20 / 20")
    Qtrim = a["Q_cond"] * 0.15
    simple_hx("E-115", "Atm. overhead trim condenser", Qtrim, 600, 60, D["atm_drum_T"], 32, 43, "AEU",
              "OH vapour/condensate", "Cooling water", moc="CS shell / Ti tubes", desP="3.5 / 7")
    simple_hx("E-116", "Stabiliser reboiler (HP steam)", st["Q_reb"], 900, 253, 253, st["T_bot"] - 10, st["T_bot"],
              "BKT", "Naphtha", "HP steam", desP="15 / 45")
    simple_hx("E-117", "Splitter reboiler (MP steam)", sp["Q_reb"], 900, 186, 186, sp["T_bot"] - 8, sp["T_bot"],
              "BXM (thermosyphon)", "Naphtha", "MP steam", desP="5 / 13")
    simple_hx("E-118", "Desalter wash water / brine", 0.0 + p["wash_water"] * 4.19 * 70 / 3600 * 0.6, 800,
              p["T_desalter"] - 5, p["T_desalter"] - 30, 50, p["T_ww"], "AEL", "Wash water", "Brine",
              moc="CS shell / duplex 2205 tubes", desP="20 / 20")
    # ejector condensers
    ej = m.res["ejector"]
    for tag, nm, load in [("E-202", "1st-stage ejector intercondenser", ej["stages"][0]["load_kg_h"] +
                           ej["stages"][0]["motive_kg_h"]),
                          ("E-203", "2nd-stage ejector intercondenser", ej["stages"][1]["load_kg_h"] +
                           ej["stages"][1]["motive_kg_h"]),
                          ("E-204", "Ejector aftercondenser", ej["stages"][2]["load_kg_h"] +
                           ej["stages"][2]["motive_kg_h"])]:
        Q = load * 2300 / 3600
        simple_hx(tag, nm, Q, 900, 70, 40, 32, 43, "AXS (vacuum condenser)", "Steam / NCG", "Cooling water",
                  moc="CS shell / 304L tubes", desP="FV-3.5 / 7")

    # ---------------- air coolers -------------------------------------------
    ac = []
    U_ac = {"A-101": 480, "A-103": 380, "A-104": 320, "A-105": 280, "A-106": 520, "A-107": 480, "A-108": 380,
            "A-201": 280, "A-202": 220}
    duties = {"A-101": ("Atm. overhead condenser", a["Q_cond"] * 0.85, a["T_top"], 60.0),
              "A-106": ("Stabiliser overhead condenser", st["Q_cond"], st["T_top"], D["stab_drum_T"]),
              "A-107": ("Splitter overhead condenser", sp["Q_cond"], sp["T_top"], D["split_drum_T"]),
              "A-108": ("Heavy naphtha product cooler",
                        m.hl(sp["b"], sp["T_bot"]) - m.hl(sp["b"], 45.0), sp["T_bot"], 45.0)}
    for t in p["trims"]:
        if t["tag"].startswith("A-"):
            duties[t["tag"]] = (f"{t['hot'].title()} cooler", t["Q_kw"], t["T_in"], t["T_out"])
    for tag in sorted(duties):
        name, Q, Ti, To = duties[tag]
        if Q <= 1:
            continue
        Ta_in = basis.SITE["amb_design_C"]
        Ta_out = Ta_in + 0.45 * (To - Ta_in) + 0.25 * (Ti - To)
        Ta_out = min(Ta_out, To - 5)
        F = 0.9
        A_bare = Q * 1000 / (U_ac.get(tag, 350) * F * lmtd(Ti, To, Ta_in, Ta_out))
        bays = max(1, math.ceil(A_bare / 1100))
        fans = 2 * bays
        fan_kw = max(Q / 1000 * 8.0, 15) / fans
        d = dict(tag=tag, type="Air cooler", service=name, area="CDU" if tag[2] == "1" else "VDU", duty_kw=Q,
                 size=f"{A_bare:.0f} m2 bare; {bays} bay(s) 6 m x 12 m, {fans} fans",
                 area_m2=A_bare, bays=bays, fans=fans, fan_kw=fan_kw, motor_kw=motor(fan_kw),
                 op_T=f"{Ti:.0f}->{To:.0f} (air {Ta_in:.0f}->{Ta_out:.0f})",
                 des_P=design_P(15 if tag in ("A-106",) else 8), des_T=design_T(Ti),
                 moc="CS tubes, Al fins (A-101: CS + inlet ferrules, Ti optional)", orient="H",
                 L=12.0, W=6.0 * bays, H=2.5)
        ac.append(d)
        E(d)

    # ---------------- drums / vessels ---------------------------------------
    def drum(tag, name, liq_m3h, hold_min, LD=3.0, frac=0.5, P="", T="", desP=None, desT=None, moc="CS", vert=False,
             area="CDU", boot=None):
        V = liq_m3h * hold_min / 60 / frac
        Dm = round_up((4 * V / (math.pi * LD)) ** (1 / 3), 0.1)
        Lm = round_up(Dm * LD, 0.5)
        d = dict(tag=tag, type="Drum", service=name, area=area, size=f"ID {Dm:.1f} m x {Lm:.1f} m T/T"
                 + (f"; boot {boot}" if boot else ""), D=Dm, L=Lm if not vert else None,
                 H=Lm if vert else Dm, orient="V" if vert else "H", op_P=P, op_T=T, des_P=desP, des_T=desT,
                 moc=moc, ca_mm=3, holdup_min=hold_min, volume_m3=V)
        E(d)
        return d

    cm = a["crude_m3h"]
    for tag, stage in [("D-101A", "1st"), ("D-101B", "2nd")]:
        E(dict(tag=tag, type="Desalter", service=f"Electrostatic desalter, {stage} stage", area="CDU",
               size="ID 3.8 m x 30.0 m T/T, AC/DC dual-polarity grids", D=3.8, L=30.0, H=3.8, orient="H",
               op_P="11.5", op_T=f"{p['T_desalter']:.0f}", des_P=17.0, des_T=design_T(p["T_desalter"]),
               moc="CS", ca_mm=3, residence_min=round(math.pi / 4 * 3.8 ** 2 * 30 * 0.9 / cm * 60, 1)))
    hc_liq = (a["R"] + a["drum"].liq.sum()) / 680
    drum("D-102", "Atm. overhead reflux drum (3-phase)", hc_liq, 10, LD=3.5, P=f"{D['atm_drum_P'] - 1.013:.1f}",
         T=f"{D['atm_drum_T']:.0f}", desP=3.5, desT=design_T(130), moc="CS (HIC-resistant), 6 mm CA",
         boot="ID 1.5 m x 3.0 m")
    drum("D-103", "Fuel gas knock-out drum", 2.0, 20, LD=2.5, vert=True, P="3.5", T="30", desP=7.0, desT=design_T(60))
    drum("D-105", "Stabiliser reflux drum", (st["reflux"] + st["lpg"].sum()) / 540, 10, P=f"{D['stab_drum_P'] - 1.013:.1f}",
         T=f"{D['stab_drum_T']:.0f}", desP=design_P(D["stab_drum_P"] - 1.013 + 3), desT=design_T(65),
         moc="CS (HIC-resistant)", boot="ID 0.6 m x 1.5 m")
    drum("D-106", "Splitter reflux drum", (sp["reflux"] + sp["d"].sum()) / 640, 10, P=f"{D['split_drum_P'] - 1.013:.1f}",
         T=f"{D['split_drum_T']:.0f}", desP=3.5, desT=design_T(90))
    drum("D-201", "Ejector hotwell / sour water separator", ej["sour_water"] / 990 + 1, 15, LD=4, P="0.05", T="45",
         desP=3.5, desT=design_T(70), area="VDU", boot="slop oil compartment")
    drum("D-202", "Vacuum off-gas knock-out drum", 1.0, 10, LD=2.5, vert=True, P="0.05", T="45", desP=3.5,
         desT=design_T(70), area="VDU")
    drum("D-104", "Flare knock-out drum (unit)", 30.0, 20, LD=3.0, P="0.2", T="60", desP=3.5, desT=design_T(250))

    # ejectors
    for s in ej["stages"]:
        E(dict(tag=s["tag"], type="Ejector", service=f"Steam ejector ({s['suction_mbar']:.0f} -> "
                                                        f"{s['discharge_mbar']:.0f} mbar(a))",
               area="VDU", size=f"load {s['load_kg_h']:.0f} kg/h, motive MP steam {s['motive_kg_h']:.0f} kg/h "
                                f"(2 x 50 % parallel)", orient="H", L=4.0, D=0.6, H=1.0,
               des_P="FV / 3.5", des_T=250, moc="CS body / SS nozzle"))

    # ---------------- pumps ---------------------------------------------------
    pumps = []

    def pump(tag, svc, kg_h, T, rho, dP_bar, area="CDU", spare=True, NPSHa=None, vap_P=None):
        q = kg_h / rho * 1.10          # m3/h rated (10 % margin)
        H = dP_bar * 1e5 / (rho * 9.81)
        eta = 0.55 + 0.08 * math.log10(max(q, 5) / 5) if q < 2000 else 0.82
        eta = min(eta, 0.82)
        bkw = q / 3600 * dP_bar * 1e5 / eta / 1000
        d = dict(tag=tag + ("A/B" if spare else ""), type="Pump", service=svc, area=area,
                 size=f"{q:.0f} m3/h rated @ {H:.0f} m", flow_m3h=q, head_m=H, dP_bar=dP_bar, T=T, rho=rho, eta=eta,
                 absorbed_kw=bkw, motor_kw=motor(bkw), api610="OH2" if bkw < 150 and T < 200 else "BB2",
                 seal="API 682 Plan 53B" if T > 250 else "API 682 Plan 11/52", orient="H",
                 L=3.0 if bkw < 200 else 5.0, W=1.2 if bkw < 200 else 2.0, H=1.5, op_T=f"{T:.0f}",
                 des_T=design_T(T), moc="S-6 (CS/12Cr)" if T < 230 else "C-6 (12Cr)" if T < 300 else "A-8 (316)")
        pumps.append(d)
        E(d)
        return d

    rho = lambda mv, T: float((mv * m.sl.rho_l(T)).sum() / mv.sum())
    c = m.crude
    pump("P-101", "Crude charge", c.sum() + p["water_in"], 30, rho(c, 30), 22.0)
    pump("P-102", "Desalted crude booster", c.sum(), p["T_desalter"], rho(c, p["T_desalter"]), 20.0)
    pump("P-103", "Atm. reflux", a["R"], 45, rho(a["refl_unit"], 45), 7.0)
    pump("P-104", "Unstabilised naphtha", a["drum"].liq.sum(), 45, rho(a["drum"].liq, 45), 16.0)
    pump("P-105", "Overhead sour water", a["steam_total"], 45, 990, 5.0)
    for tag, k in [("P-106", "TPA"), ("P-107", "MPA"), ("P-108", "BPA")]:
        x = a["pa"][k]
        pump(tag, f"{k} pumparound", x["flow"], x["T_draw"], rho(x["comp"], x["T_draw"]), 8.0)
    for tag, k in [("P-109", "KERO"), ("P-110", "DIESEL"), ("P-111", "AGO")]:
        pump(tag, f"{k.title()} product", a["prod"][k].sum(), a["T_out"][k], rho(a["prod"][k], a["T_out"][k]), 9.0)
    pump("P-112", "Atm. residue / vacuum heater charge", a["prod"]["AR"].sum(), a["T_bot"],
         rho(a["prod"]["AR"], a["T_bot"]), 12.0)
    pump("P-114", "Desalter wash water", p["wash_water"], 50, 990, 8.0)
    pump("P-115", "Stabiliser reflux / LPG", st["reflux"] + st["lpg"].sum(), 45, 530, 8.0)
    pump("P-116", "Splitter reflux / LN", sp["reflux"] + sp["d"].sum(), 50, 640, 7.0)
    pump("P-117", "Heavy naphtha product", sp["b"].sum(), sp["T_bot"], rho(sp["b"], sp["T_bot"]), 6.0)
    pump("P-118", "Desalter mud-wash / recycle", p["wash_water"] * 0.5, 120, 950, 6.0, spare=False)
    for tag, k, nm in [("P-201", "LVGO", "LVGO pumparound / product"), ("P-202", "HVGO", "HVGO pumparound / product")]:
        x = v["pa"][k]
        mv = x["comp"] * x["flow"] + v[k.lower()]
        pump(tag, nm, mv.sum(), x["T_draw"], rho(mv, x["T_draw"]), 10.0, area="VDU")
    pump("P-203", "Slop wax", v["slop"].sum(), v["T_slop"], rho(v["slop"], v["T_slop"]), 8.0, area="VDU")
    pump("P-204", "Vacuum residue (incl. quench)", v["vr"].sum() * 1.25, v["T_bot"], rho(v["vr"], v["T_bot"]), 14.0,
         area="VDU")
    pump("P-205", "Hotwell sour water", ej["sour_water"], 45, 990, 5.0, area="VDU")
    pump("P-206", "Hotwell slop oil", max(ej["slop_oil"], 500), 45, 850, 5.0, area="VDU")

    # chemical injection packages
    for tag, nm in [("X-101", "Demulsifier injection package"), ("X-102", "Caustic injection package (desalted crude)"),
                    ("X-103", "Neutraliser / filming amine package (atm OH)"),
                    ("X-104", "Corrosion inhibitor package (VDU OH)")]:
        E(dict(tag=tag, type="Package", service=nm, area="CDU" if "10" in tag else "VDU",
               size="Tank 2 m3 + 2 x 100 % metering pumps", motor_kw=0.75, orient="H", L=3.0, W=2.0, H=2.5,
               moc="SS316"))

    # ---------------- relief valves ------------------------------------------
    psv = []

    def orifice(W, T_C, MW, Pset_barg, k=1.1, Z=1.0, over=0.10):
        P1 = (Pset_barg * (1 + over) + 1.013) * 100  # kPa(a)
        C = 0.03948 * math.sqrt(k * (2 / (k + 1)) ** ((k + 1) / (k - 1)))
        A = W / (C * 0.975 * P1) * math.sqrt((T_C + 273.15) * Z / MW)
        for L, a_ in API526:
            if a_ >= A:
                return A, 1, L
        n = math.ceil(A / 16774)
        return A, n, "T"

    def fire(Awet, lam):
        Q = 43200 * 1.0 * Awet ** 0.82  # W, adequate drainage, F=1
        return Q / 1000 / lam * 3600, Q / 1000

    reliefs = [
        ("PSV-1001", "C-101", "Reflux failure / blocked OH (total OH vapour)", (a["prod"]["NAPH"].sum() + a["R"]) * 1.0,
         a["T_top"] + 20, m.mw(a["prod"]["NAPH"]), 2.4, "Flare"),
        ("PSV-1002", "D-101A", "Fire (liquid full)", fire(math.pi * 3.8 * 30 * 0.8, 320)[0], 200, 120, 15.5, "Flare"),
        ("PSV-1003", "D-101B", "Fire (liquid full)", fire(math.pi * 3.8 * 30 * 0.8, 320)[0], 200, 120, 15.5, "Flare"),
        ("PSV-1004", "D-102", "Fire", fire(math.pi * 3.0 * 10 * 0.6, 330)[0], 120, 90, 2.4, "Flare"),
        ("PSV-1005", "C-105", "Reflux failure (reboiler duty)", st["Q_reb"] / 300 * 3600, st["T_top"] + 15,
         m.mw(st["d"]), design_P(st["P_bot"] - 1.013), "Flare"),
        ("PSV-1006", "D-105", "Fire", fire(math.pi * 2.0 * 6 * 0.6, 340)[0], 70, 50, design_P(D["stab_drum_P"] + 2), "Flare"),
        ("PSV-1007", "C-106", "Reflux failure (reboiler duty)", sp["Q_reb"] / 320 * 3600, sp["T_top"] + 15,
         m.mw(sp["d"]), 3.5, "Flare"),
        ("PSV-1008", "E-116", "Tube rupture (HP steam into naphtha)", 25000, 260, 18, design_P(st["P_bot"] - 1.013),
         "Flare"),
        ("PSV-1009", "C-102/103/104", "Fire (side strippers)", fire(60, 280)[0], 300, 180, 3.5, "Flare"),
        ("PSV-1010", "P-101 disch.", "Blocked outlet / thermal", 5000, 60, 150, 30.0, "Closed drain"),
        ("PSV-2001", "C-201", "Loss of vacuum / fire (blocked outlet to ejectors)", v["steam"] + 30000, 400, 60, 3.5,
         "Flare"),
        ("PSV-2002", "D-201", "Fire", fire(30, 400)[0], 120, 100, 3.5, "Flare"),
    ]
    for tagp, prot, case, W, T, MW, Pset, dest in reliefs:
        A, n, L = orifice(W, T, MW, Pset if isinstance(Pset, (int, float)) else 3.5)
        psv.append(dict(tag=tagp, protects=prot, case=case, load_kg_h=W, T=T, MW=MW, set_barg=Pset, area_mm2=A,
                        orifice=L, count=n, dest=dest))

    return dict(equipment=eq, pumps=pumps, aircoolers=ac, hx=hx_list, psv=psv, heaters=heaters, model=m)
