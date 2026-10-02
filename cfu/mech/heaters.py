"""Fired heaters: API 530 tube thickness, TMT estimate, cabin geometry for the GA, weights.

API 530 9Cr-1Mo (A335 P9 / A213 T9) allowable stresses below are digitised (approx.) from the
API 530 7th ed. material curves: elastic allowable sigma_el and 100,000 h minimum rupture
allowable sigma_r.  FEED accuracy - vendor to confirm with the code curves.
"""
from __future__ import annotations

import math

from .common import eq, interp, results, round_up, streams

P9 = dict(
    el=[(350, 133), (400, 127), (425, 123), (450, 118), (475, 112), (500, 105), (525, 97), (550, 88), (575, 78),
        (600, 67), (625, 55), (650, 43)],
    rup=[(400, 300), (425, 205), (450, 160), (475, 123), (500, 93), (525, 68), (550, 49), (575, 35), (600, 25),
         (625, 17.5), (650, 12)],
    k=27.0)
SCHED = [("Sch 40", 7.11), ("Sch 80", 10.97), ("Sch 120", 14.27), ("Sch 160", 18.26)]
F_CORR = 0.60           # API 530 corrosion fraction (Fig. 1, B ~ 0.6, n ~ 6)
LIFE_H = 100_000
OD = 168.3
ID_PROC = 146.3          # inside diameter assumed in process sizing (mass flux)
CP_FG = 1.25             # kJ/kg K flue gas


def tube_design(tag):
    e = eq(tag)
    h = results()["heaters"][tag]
    S = streams()
    hot = tag == "H-101"
    q_avg = h["radiant_kw"] / h["rad_area"]                  # kW/m2 on OD
    F_peak = 1.8 * 1.10                                       # circumferential (single row on wall) x longitudinal
    q_max = q_avg * F_peak
    q_in = q_max * OD / ID_PROC
    h_i = 1100.0 if hot else 650.0                             # W/m2K inside film (EOR)
    R_coke = 0.0005 if hot else 0.0009                         # m2K/W coke/fouling at EOR
    dT_film = q_in * 1000 / h_i
    dT_coke = q_in * 1000 * R_coke
    dT_wall = q_max * 1000 * (OD / 2000) * math.log(OD / ID_PROC) / P9["k"]
    T_fluid = h["T_out"]
    TMT = T_fluid + dT_film + dT_coke + dT_wall
    Tdm = round_up(TMT + 15, 5)
    P_el = float(e["des_P"]) / 10                              # MPa
    P_r = (S["6"]["P_barg"] if hot else S["19"]["P_barg"]) / 10
    s_el = interp(P9["el"], Tdm)
    s_r = interp(P9["rup"], Tdm)
    CA = float(e.get("ca_mm") or 3)
    d_el = P_el * OD / (2 * s_el + P_el)
    d_r = P_r * OD / (2 * s_r + P_r)
    t_el = d_el + CA
    t_r = d_r + F_CORR * CA
    t_min = max(t_el, t_r)
    gov = "elastic" if t_el >= t_r else "rupture"
    sched_min = next(s for s in SCHED if s[1] >= t_min)
    sel = ("Sch 80", 10.97)
    return dict(tag=tag, q_avg=q_avg, q_max=q_max, q_in=q_in, h_i=h_i, R_coke=R_coke, dT_film=dT_film,
                dT_coke=dT_coke, dT_wall=dT_wall, T_fluid=T_fluid, TMT=TMT, Tdm=Tdm, des_T_eq=e["des_T"], P_el=P_el,
                P_r=P_r, s_el=s_el, s_r=s_r, CA=CA, d_el=d_el, d_r=d_r, t_el=t_el, t_r=t_r, t_min=t_min, gov=gov,
                sched_min=sched_min, sched=sel, OD=OD, life=LIFE_H, f_corr=F_CORR)


def heater_geometry(tag):
    """Cabin geometry consistent with tube count/length in equipment.json and process_results."""
    e = eq(tag)
    h = results()["heaters"][tag]
    hot = tag == "H-101"
    cells = h["cells"]
    L_tube = 18.3
    pitch = 2 * OD / 1000
    tubes_cell = h["rad_tubes"] // cells
    per_wall = tubes_cell // 2
    coil_h = per_wall * pitch
    W_cl = 5.35 if hot else 4.4                     # between tube centre-lines (burner to tube CL >= 2.2 m)
    cell_in = W_cl + 2 * 0.25
    cell_out = cell_in + 2 * 0.25
    box_h = round(coil_h + 2.2, 1)
    floor = 2.0
    hdr = 1.5                                        # header box each end
    L_box = L_tube + 0.6
    L_out = L_box + 2 * hdr
    fg = results()["heaters"][tag]["fuel_kg_h"] * 18.5 / 3600          # kg/s flue gas
    aph = 0.0
    if hot:
        aph = fg * 1.1 * (380 - 160)                 # kW to combustion air (E-120)
    Q_in = h["Q_fired_kw"] + aph
    loss = 0.015 * h["Q_fired_kw"]
    BWT = 15 + (Q_in - h["radiant_kw"] - loss) / (fg * CP_FG)
    Q_ss = h.get("Q_ss_kw", 0.0)
    Q_conv_proc = h["conv_kw"] - Q_ss
    T_x = h["T_in"] + (h["T_out"] - h["T_in"]) * Q_conv_proc / h["Q_proc_kw"]
    T_fg_out_req = BWT - h["conv_kw"] / (fg * CP_FG)
    T_fg_min = h["T_in"] + 50                          # 50 C approach to process inlet
    Q_conv_max = fg * CP_FG * (BWT - T_fg_min)
    T_fg_out = max(T_fg_out_req, T_fg_min)
    Q_conv_proc_ach = min(Q_conv_proc, fg * CP_FG * (BWT - T_fg_min) - Q_ss)
    utility = max(0.0, h["conv_kw"] - Q_ss - Q_conv_proc_ach)
    d1 = BWT - T_x
    d2 = T_fg_out - h["T_in"]
    lm = (d1 - d2) / math.log(d1 / d2) if abs(d1 - d2) > 1 else d1
    U_bare = 105.0
    A_conv = Q_conv_proc_ach * 1000 / (U_bare * lm)
    A_tube = math.pi * OD / 1000 * L_tube
    per_row = h["passes"] if hot else max(4, h["passes"])
    n_conv = math.ceil(A_conv / A_tube / per_row) * per_row
    shock_rows = 2
    rows = max(n_conv // per_row, shock_rows + 2)
    ss_rows = 2 if Q_ss > 0 else 0
    util_rows = 2 if utility > 100 else 0
    conv_w = per_row * pitch + 0.4
    conv_h = (rows + ss_rows + util_rows) * 0.30 + 1.2
    rad_top = floor + box_h
    hip = 1.8 if hot else 1.2
    conv_bot = rad_top + hip
    conv_top = conv_bot + conv_h
    brch_top = conv_top + 2.0
    H_top = float(e["H"])
    stack_D = round(math.sqrt(4 * (fg / 0.55 / 10.0) / math.pi), 1)
    burners = h["burners"]
    W_out = cells * cell_out
    return dict(tag=tag, cells=cells, L_tube=L_tube, pitch=pitch, tubes_cell=tubes_cell, per_wall=per_wall,
                coil_h=coil_h, W_cl=W_cl, cell_in=cell_in, cell_out=cell_out, W_out=W_out, box_h=box_h, floor=floor,
                hdr=hdr, L_box=L_box, L_out=L_out, rad_top=rad_top, hip=hip, conv_bot=conv_bot, conv_top=conv_top,
                conv_w=conv_w, conv_h=conv_h, brch_top=brch_top, H_top=H_top, stack_D=stack_D,
                stack_h=H_top - brch_top, fg_kg_s=fg, BWT=BWT, aph_kw=aph, T_x=T_x, T_fg_out=T_fg_out,
                T_fg_out_req=T_fg_out_req, lmtd=lm, U_bare=U_bare, A_conv=A_conv, per_row=per_row, conv_rows=rows,
                shock_rows=shock_rows, ss_rows=ss_rows, util_rows=util_rows, util_kw=utility, Q_ss=Q_ss,
                Q_conv_proc=Q_conv_proc, Q_conv_max=Q_conv_max, burners=burners, burners_cell=burners // cells,
                burner_mw=h["Q_fired_kw"] / burners / 1000, burner_pitch=L_tube / (burners // cells),
                passes=h["passes"], rad_tubes=h["rad_tubes"], eq_L=e["L"], eq_W=e["W"], h=h)


def heater_weight(geo, td):
    L = geo["L_tube"]
    n_rad = geo["rad_tubes"]
    kgm80 = 42.56
    rad_coil = n_rad * L * kgm80 + n_rad * 45 + n_rad * 3 * 55
    n_conv = geo["conv_rows"] * geo["per_row"]
    conv_coil = n_conv * L * (kgm80 + 18) + n_conv * 45 + (geo["ss_rows"] + geo["util_rows"]) * geo["per_row"] * L * 30
    cells = geo["cells"]
    Lb = geo["L_box"]
    walls = cells * (2 * Lb * geo["box_h"] + 2 * geo["cell_in"] * geo["box_h"] + Lb * geo["cell_in"] * 1.1)
    floor = cells * Lb * geo["cell_in"]
    conv_area = 2 * (Lb + geo["conv_w"]) * geo["conv_h"]
    refr = walls * 75 + floor * 480 + conv_area * 165
    casing = (walls + floor + conv_area + 2 * Lb * geo["hip"] * cells) * 160
    stack = math.pi * geo["stack_D"] * geo["stack_h"] * (0.010 * 7850 + 0.05 * 1100)
    platforms = 25000 if geo["tag"] == "H-101" else 15000
    burners = geo["burners"] * 800
    aph = 0
    fans = 0
    ducts = 0
    if geo["tag"] == "H-101":
        aph = 110000
        fans = 2 * 6000 + 2 * 10000
        ducts = 45000
    empty = rad_coil + conv_coil + refr + casing + stack + platforms + burners + aph + fans + ducts
    coil_vol = (n_rad + n_conv) * L * math.pi / 4 * (ID_PROC / 1000) ** 2
    operating = empty + coil_vol * 450
    return dict(rad_coil=rad_coil, conv_coil=conv_coil, refractory=refr, casing_structure=casing, stack=stack,
                platforms=platforms, burners=burners, aph=aph, fans=fans, ducts=ducts, empty=empty,
                operating=operating, hydrotest=empty - aph - fans - ducts + coil_vol * 1000, coil_vol=coil_vol)
