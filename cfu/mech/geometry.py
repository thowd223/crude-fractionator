"""Vessel geometry used by both the mechanical calculations and the GA drawings.

Elevations z are metres above the bottom tangent line (BTL = 0).  Everything is derived from
data/equipment.json (diameters, T/T heights, tray counts) and data/streams.json /
process_results.json (nozzle flows).  Layout allowances (vapour spaces, collector spacers) are
mechanical assumptions chosen so that the T/T height equals the sized height in equipment.json.
"""
from __future__ import annotations

import math

from .common import (eq, flange_class, nps_for_area, nps_id, num, results, round_up, streams)

R_GAS = 8314.46
CONE_HALF_ANGLE = 30.0          # deg, conical transitions


def cone_len(D1, D2, alpha=CONE_HALF_ANGLE):
    return abs(D1 - D2) / 2 / math.tan(math.radians(alpha))


# ---------------------------------------------------------------------------
# nozzle sizing criteria
CRIT = {
    "liq_draw": (0.9, "gravity draw / pump suction <= 0.9 m/s (self-venting)"),
    "liq_strip": (0.6, "gravity draw to side stripper <= 0.6 m/s"),
    "liq_ret": (2.5, "pumped liquid return <= 2.5 m/s"),
    "liq_reflux": (2.0, "reflux / pumped liquid <= 2.0 m/s"),
    "suction": (1.0, "pump suction (bottoms) <= 1.0 m/s"),
    "vap_out": (None, "vapour outlet rho.v2 <= 3000 Pa"),
    "vap_ret": (None, "vapour return rho.v2 <= 4000 Pa"),
    "feed2ph": (None, "two-phase feed rho_m.v2 <= 6000 Pa"),
    "steam": (35.0, "stripping steam <= 35 m/s"),
    "vac_vap": (60.0, "vacuum vapour <= 60 m/s"),
    "vac_feed": (70.0, "vacuum transfer line <= 70 m/s (rho_m.v2 << 6000 Pa)"),
    "reb_vap": (None, "reboiler vapour return rho.v2 <= 4000 Pa"),
}


def size_nozzle(Q_m3s, rho, crit, minimum=2):
    v, _ = CRIT[crit]
    if v is None:
        lim = {"vap_out": 3000, "vap_ret": 4000, "feed2ph": 6000, "reb_vap": 4000}[crit]
        v = math.sqrt(lim / max(rho, 1e-6))
    A = Q_m3s / v
    n = nps_for_area(A, minimum)
    v_act = Q_m3s / (math.pi / 4 * (nps_id(n) / 1000) ** 2)
    return n, v_act


def N(mark, service, nps, z, side, angle, Q=None, rho=None, crit=None, v=None, kind="N", qty=1, note=""):
    return dict(mark=mark, service=service, nps=nps, z=round(z, 3), side=side, angle=angle, Q_m3s=Q, rho=rho,
                crit=CRIT[crit][1] if crit else "", v=v, kind=kind, qty=qty, note=note)


def flow_noz(mark, service, kg_h, rho, crit, z, side, angle, minimum=2, qty=1, note=""):
    Q = kg_h / 3600 / rho / qty
    n, v = size_nozzle(Q, rho, crit, minimum)
    return N(mark, service, n, z, side, angle, Q=Q, rho=rho, crit=crit, v=v, qty=qty, note=note)


def rho_gas(P_bara, T_C, MW):
    return P_bara * 1e5 * MW / (R_GAS * (T_C + 273.15))


# ---------------------------------------------------------------------------
def _common(tag):
    e = eq(tag)
    return e, num(e.get("des_P")), float(e.get("des_T") or 100)


def c101():
    e, Pd, Td = _common("C-101")
    R = results()["atm"]
    S = streams()
    H, D1, D2 = e["H"], e["D"], e["D2"]
    secs = e["sections"]
    TS = {}
    passes = {}
    for s in secs:
        a, b = (int(x) for x in s["trays"].split("-"))
        for i in range(a, b + 1):
            TS[i] = s["TS_mm"] / 1000
            passes[i] = s["passes"]
    ntray = 41
    # stack (top-down): top space, trays 1-35, flash zone (contains 30 deg swage), trays 36-41, bottom sump.
    # Sizing basis (sizing.py): 2.0 + 40 spacings + FZ 4.0 - 0.61 + 1.5 + sump + 1.0 -> fits by
    # trimming top space and widening the FZ so the swage clears tray 36 by >= 0.3 m.
    sp_rect = sum(TS.get(i, 0.61) for i in range(1, 35))
    sp_strip = sum(TS.get(i, 0.61) for i in range(36, ntray))
    Lc = cone_len(D1, D2)
    top, fz = 1.7, max(4.0, 1.6 + Lc + 0.3)
    bottom = H - top - sp_rect - fz - sp_strip
    if bottom < 4.4:
        top = 1.5
        bottom = H - top - sp_rect - fz - sp_strip
    z = {1: H - top}
    for i in range(1, 35):
        z[i + 1] = z[i] - TS.get(i, 0.61)
    cone_top = z[35] - 1.6
    cone_bot = cone_top - Lc
    z[36] = z[35] - fz
    for i in range(36, ntray):
        z[i + 1] = z[i] - TS.get(i, 0.61)
    # fill passes for draw trays (inherit tray above)
    for i in range(1, ntray + 1):
        if i not in passes:
            passes[i] = passes.get(i - 1, 2)
        if i >= 36:
            passes[i] = 2
    trays = [dict(no=i, z=z[i], D=D1 if i <= 35 else D2, passes=passes[i], TS=TS.get(i, 0.61)) for i in
             range(1, ntray + 1)]
    segs = [dict(kind="cyl", D=D2, z0=0.0, z1=cone_bot, name="Stripping section"),
            dict(kind="cone", D0=D2, D1=D1, z0=cone_bot, z1=cone_top, name="Swage 30 deg"),
            dict(kind="cyl", D=D1, z0=cone_top, z1=H, name="Flash zone / rectifying section")]
    z_steam = z[41] - 0.6
    z_mwb = z_steam - 0.65
    lahh = z_mwb - 0.5
    hll = lahh - 0.4
    levels = dict(LLL=0.5, NLL=round((0.5 + hll) / 2, 2), HLL=round(hll, 2), LAHH=round(lahh, 2))
    tr = R["tray"]
    pa = R["pa"]
    noz = []
    # feed (transfer line) two-phase at flash zone
    s7 = S["7"]
    Qv = s7["vap_act_m3h"] / 3600
    Ql = s7["liq_act_m3h"] / 3600
    rho_m = s7["total_kg_h"] / 3600 / (Qv + Ql)
    n, v = size_nozzle(Qv + Ql, rho_m, "feed2ph")
    noz.append(N("N1", "Feed - transfer line from H-101 (tangential, vapour horn)", n, z[35] - 0.95, "R", 90,
                 Q=Qv + Ql, rho=rho_m, crit="feed2ph", v=v))
    s8 = S["8"]
    n, v = size_nozzle(s8["vap_act_m3h"] / 3600, s8["rho_vap"], "vap_out")
    noz.append(N("N2", "Overhead vapour to A-101", n, H, "T", 0, Q=s8["vap_act_m3h"] / 3600, rho=s8["rho_vap"],
                 crit="vap_out", v=v))
    s10 = S["10"]
    noz.append(flow_noz("N3", "Reflux from P-103", s10["total_kg_h"], s10["rho_liq"], "liq_reflux", z[1] + 0.35, "R", 45))
    rho_ret = lambda k: S[{"TPA": "13", "MPA": "14", "BPA": "15"}[k]]["rho_liq"] * 1.10   # cooler return
    for k, mk_r, mk_d, sd in [("TPA", "N4", "N5", "L"), ("MPA", "N8", "N9", "L"), ("BPA", "N12", "N13", "L")]:
        x = pa[k]
        rho_d = S[{"TPA": "13", "MPA": "14", "BPA": "15"}[k]]["rho_liq"]
        noz.append(flow_noz(mk_r, f"{k} return", x["flow"], rho_ret(k), "liq_ret", z[x["ret_tray"]] + 0.30, sd, 270))
        noz.append(flow_noz(mk_d, f"{k} draw to P-{ {'TPA': 106, 'MPA': 107, 'BPA': 108}[k]} (draw sump)", x["flow"],
                            rho_d, "liq_draw", z[x["draw_tray"]] - 0.15, sd, 225))
    # side draws and vapour returns
    prod_rho = {"KERO": S["14"]["rho_liq"], "DIESEL": S["15"]["rho_liq"], "AGO": 636.0}
    prod_mw = {"KERO": S["16"]["mw"], "DIESEL": S["17"]["mw"], "AGO": S["18"]["mw"]}
    prod_kg = {"KERO": S["16"]["total_kg_h"], "DIESEL": S["17"]["total_kg_h"], "AGO": S["18"]["total_kg_h"]}
    marks = {"KERO": ("N6", "N7", "C-102"), "DIESEL": ("N10", "N11", "C-103"), "AGO": ("N14", "N15", "C-104")}
    side_vap = {}
    for k, (md, mv, st) in marks.items():
        t = tr[k]
        draw = prod_kg[k] * 1.10
        noz.append(flow_noz(md, f"{k.title()} draw to {st}", draw, prod_rho[k], "liq_strip", z[t] - 0.15, "R", 135))
        steam = R["steam"][k]
        Vm = steam + 0.10 * prod_kg[k]
        mwv = Vm / (steam / 18 + 0.10 * prod_kg[k] / prod_mw[k])
        P = 2.2 + R["P_fz_barg"] * 0 + 0.008 * t      # bar(a) at tray (top 2.2 bar(a) + 8 mbar/tray)
        rv = rho_gas(P, R["T_draw"][k], mwv)
        side_vap[k] = (Vm, rv)
        q = Vm / 3600 / rv
        n, v = size_nozzle(q, rv, "vap_ret")
        noz.append(N(mv, f"Vapour return from {st}", n, z[t - 1] - 0.25, "R", 150, Q=q, rho=rv, crit="vap_ret", v=v))
    # stripping steam
    st_kg = R["steam"]["bottom"]
    rs = rho_gas(4.5, 350, 18)
    n, v = size_nozzle(st_kg / 3600 / rs, rs, "steam")
    noz.append(N("N16", "Stripping steam (from H-101 SS coil)", n, z_steam, "R", 60, Q=st_kg / 3600 / rs, rho=rs,
                 crit="steam", v=v))
    s19 = S["19"]
    noz.append(flow_noz("N17", "Atm. residue to P-112", s19["total_kg_h"], s19["rho_liq"], "suction", -D2 / 4, "B", 0))
    noz.append(N("N18", "Vent / steam-out", 3, H, "T", 0, note="top head"))
    psv = [p for p in _psv() if p["protects"] == "C-101"]
    if psv:
        p = psv[0]
        noz.append(N("N19", f"{p['tag']} relief ({p['count']} x {p['orifice']} orifice)", _psv_inlet(p["orifice"]), H,
                     "T", 0, qty=p["count"], note="top head"))
    noz.append(N("N20A/B", "LT / LG bridle (bottom sump)", 3, levels["LLL"] - 0.3, "L", 300, qty=2,
                 note=f"bridle {levels['LLL'] - 0.3:.1f} / {levels['LAHH'] + 0.3:.1f}"))
    noz.append(N("N21", "Wash-zone overflash / slop connection (spare)", 4, z[35] - 0.15, "L", 200))
    # manways
    mw = []
    for i, zz in enumerate([z[1] + min(1.0, top - 0.6), (z[8] + z[9]) / 2, (z[17] + z[18]) / 2, (z[28] + z[29]) / 2,
                            z[35] - 1.1, (z[38] + z[39]) / 2, z_mwb]):
        mw.append(N(f"M{i + 1}", "Manway 24\" (davit)", 24, zz, "F", 0, kind="MW"))
    noz += mw
    platforms = [round(m["z"] - 1.0, 2) for m in mw] + [H + D1 / 4 + 0.2]
    for n_ in noz:
        n_["rating"] = flange_class(Pd + 0.1 * max(0, levels["HLL"] - n_["z"]), Td)
    internals = [dict(kind="draw", z=z[t] - 0.15, D=D1, label=f"Draw sump tray {t}") for t in
                 (tr["TPA_draw"], tr["KERO"], tr["MPA_draw"], tr["DIESEL"], tr["BPA_draw"], tr["AGO"])]
    internals.append(dict(kind="horn", z0=z[35] - 1.55, z1=z[35] - 0.35, D=D1, label="Feed vapour horn"))
    internals.append(dict(kind="steam", z=z_steam, D=D2, label="Steam sparger"))
    internals.append(dict(kind="vortex", z=0.0, D=D2, label="Vortex breaker"))
    clad = [dict(z0=-D2 / 4, z1=z[10], mat="410S", t=3.0), dict(z0=z[5] - 0.3, z1=H + D1 / 4, mat="Monel 400", t=2.0)]
    return dict(tag="C-101", e=e, H=H, Ds=[D1, D2], D_top=D1, D_bot=D2, segs=segs, trays=trays, levels=levels,
                nozzles=noz, platforms=platforms, internals=internals, clad=clad, rho_liq=706.0, rho_tray=630.0,
                Pd=Pd, Td=Td, fv=False, sections=secs, side_vap=side_vap, min_skirt=5.0, bottoms_pump="P-112A/B",
                top_space=top, fz=fz, cone=(cone_bot, cone_top))


def _psv():
    from .common import psvs
    return psvs()


def _psv_inlet(orifice):
    return {"D": 1, "E": 1, "F": 1.5, "G": 1.5, "H": 1.5, "J": 2, "K": 3, "L": 3, "M": 4, "N": 4, "P": 4,
            "Q": 6, "R": 6, "T": 8}[orifice]


def stripper(tag):
    e, Pd, Td = _common(tag)
    R = results()["atm"]
    S = streams()
    k = {"C-102": "KERO", "C-103": "DIESEL", "C-104": "AGO"}[tag]
    H, D = e["H"], e["D"]
    z = {1: H - 1.5}
    for i in range(1, 6):
        z[i + 1] = z[i] - 0.61
    trays = [dict(no=i, z=z[i], D=D, passes=1, TS=0.61) for i in range(1, 7)]
    segs = [dict(kind="cyl", D=D, z0=0.0, z1=H, name="Stripping section")]
    levels = dict(LLL=0.5, NLL=1.5, HLL=2.6, LAHH=3.0)
    prod = {"KERO": "16", "DIESEL": "17", "AGO": "18"}[k]
    prod_kg = S[prod]["total_kg_h"]
    rho_hot = {"KERO": S["14"]["rho_liq"], "DIESEL": S["15"]["rho_liq"], "AGO": 636.0}[k]
    noz = [flow_noz("N1", f"{k.title()} feed from C-101 tray {R['tray'][k]}", prod_kg * 1.10, rho_hot, "liq_strip",
                    z[1] + 0.3, "L", 270)]
    steam = R["steam"][k]
    Vm = steam + 0.10 * prod_kg
    mwv = Vm / (steam / 18 + 0.10 * prod_kg / S[prod]["mw"])
    rv = rho_gas(2.2 + 0.008 * R["tray"][k], R["T_draw"][k], mwv)
    n, v = size_nozzle(Vm / 3600 / rv, rv, "vap_ret")
    noz.append(N("N2", "Vapour return to C-101", n, H, "T", 0, Q=Vm / 3600 / rv, rho=rv, crit="vap_ret", v=v))
    rs = rho_gas(4.5, 350, 18)
    n, v = size_nozzle(steam / 3600 / rs, rs, "steam")
    noz.append(N("N3", "Stripping steam", n, z[6] - 0.6, "R", 90, Q=steam / 3600 / rs, rho=rs, crit="steam", v=v))
    pump = {"KERO": "P-109", "DIESEL": "P-110", "AGO": "P-111"}[k]
    noz.append(flow_noz("N4", f"Bottoms to {pump}", prod_kg, rho_hot * 1.02, "suction", -D / 4, "B", 0))
    noz.append(N("N5A/B", "LT / LG bridle", 2, levels["LLL"] - 0.3, "R", 120, qty=2))
    noz.append(N("N6", "Vent / steam-out / PSV-1009 (common)", 3, H, "T", 0, note="see PSV-1009"))
    noz.append(N("M1", "Manway 24\"", 24, z[1] + 0.75, "F", 0, kind="MW"))
    noz.append(N("M2", "Manway 24\"", 24, 3.3, "F", 0, kind="MW"))
    for n_ in noz:
        n_["rating"] = flange_class(Pd, Td)
    return dict(tag=tag, e=e, H=H, Ds=[D], D_top=D, D_bot=D, segs=segs, trays=trays, levels=levels, nozzles=noz,
                platforms=[2.3, H + D / 4 + 0.2], internals=[dict(kind="steam", z=z[6] - 0.6, D=D, label="Steam sparger")],
                clad=[dict(z0=-D / 4, z1=H + D / 4, mat="410S", t=3.0)] if "410S" in e["moc"] else [],
                rho_liq=rho_hot, rho_tray=rho_hot, Pd=Pd, Td=Td, fv=False, min_skirt=3.0, bottoms_pump=pump + "A/B",
                product=k)


def lightends(tag):
    e, Pd, Td = _common(tag)
    R = results()
    S = streams()
    col = R["stab"] if tag == "C-105" else R["split"]
    H, D = e["H"], e["D"]
    nt, ft = col["N_actual"], col["feed_stage"]
    z = {1: H - 2.0}
    for i in range(1, nt):
        z[i + 1] = z[i] - 0.61
    passes_top, passes_bot = col["sec_top"]["passes"], col["sec_bot"]["passes"]
    trays = [dict(no=i, z=z[i], D=D, passes=(passes_top if i < ft else passes_bot), TS=0.61) for i in range(1, nt + 1)]
    segs = [dict(kind="cyl", D=D, z0=0.0, z1=H, name="Shell")]
    levels = dict(LLL=0.5, NLL=1.4, HLL=2.4, LAHH=2.8)
    noz = []
    if tag == "C-105":
        feed = S["11"]
        rho_f = feed["rho_liq"] * 0.88       # at 120 C
        Vt = (S["30"]["total_kg_h"] + col["reflux"])
        bott = S["31"]
        reflux_rho = 530.0
        reb = "E-116 (kettle)"
        Vreb = col["Q_reb"] / 300 * 3600
        rho_b = bott["rho_liq"]
        bott_kg = bott["total_kg_h"]
        reb_liq = bott_kg + Vreb
        pump = None
    else:
        feed = S["31"]
        rho_f = feed["rho_liq"]
        Vt = S["32"]["total_kg_h"] + col["reflux"]
        reflux_rho = 640.0
        reb = "E-117 (thermosyphon)"
        Vreb = col["Q_reb"] / 320 * 3600
        rho_b = 624.0
        bott_kg = S["33"]["total_kg_h"]
        reb_liq = 3 * Vreb
        pump = "P-117A/B"
    noz.append(flow_noz("N1", f"Feed (tray {ft})", feed["total_kg_h"], rho_f, "liq_ret", z[ft] + 0.3, "R", 90))
    qv = col["sec_top"]["Q_v_m3s"]
    rv = Vt / 3600 / qv
    n, v = size_nozzle(qv, rv, "vap_out")
    noz.append(N("N2", "Overhead vapour to " + ("A-106" if tag == "C-105" else "A-107"), n, H, "T", 0, Q=qv, rho=rv,
                 crit="vap_out", v=v))
    noz.append(flow_noz("N3", "Reflux", col["reflux"], reflux_rho, "liq_reflux", z[1] + 0.35, "L", 270))
    noz.append(flow_noz("N4", f"Reboiler feed to {reb}", reb_liq, rho_b, "liq_draw", -D / 4, "B", 0))
    qb = col["sec_bot"]["Q_v_m3s"]
    rvb = Vreb / 3600 / qb
    n, v = size_nozzle(qb * (1.0 if tag == "C-105" else 1.3), rvb, "reb_vap")
    noz.append(N("N5", f"Reboiler return from {reb}", n, z[nt] - 0.8, "R", 120, Q=qb, rho=rvb, crit="reb_vap", v=v))
    if pump:
        noz.append(flow_noz("N6", f"Bottoms to {pump}", bott_kg, rho_b, "suction", 0.3, "L", 200))
    else:
        noz.append(flow_noz("N6", "Stabilised naphtha (bottoms) to E-114/C-106", bott_kg, rho_b, "suction", 0.3, "L", 200))
    psv = [p for p in _psv() if p["protects"] == tag]
    if psv:
        p = psv[0]
        noz.append(N("N7", f"{p['tag']} relief ({p['orifice']})", _psv_inlet(p["orifice"]), H, "T", 0))
    noz.append(N("N8A/B", "LT / LG bridle", 2, levels["LLL"] - 0.3, "L", 300, qty=2))
    noz.append(N("N9", "Vent / steam-out", 2, H, "T", 0))
    mws = [z[1] + 1.0, (z[ft - 1] + z[ft]) / 2 + 0.0, z[nt] - 1.5]
    if nt > 25:
        mws.insert(1, (z[10] + z[11]) / 2)
        mws.insert(3, (z[30] + z[31]) / 2)
    for i, zz in enumerate(mws):
        noz.append(N(f"M{i + 1}", "Manway 24\"", 24, zz, "F", 0, kind="MW"))
    for n_ in noz:
        n_["rating"] = flange_class(Pd + 0.1 * max(0, levels["HLL"] - n_["z"]), Td)
    plats = [round(n_["z"] - 1.0, 2) for n_ in noz if n_["kind"] == "MW"] + [H + D / 4 + 0.2]
    return dict(tag=tag, e=e, H=H, Ds=[D], D_top=D, D_bot=D, segs=segs, trays=trays, levels=levels, nozzles=noz,
                platforms=plats, internals=[dict(kind="feed", z=z[ft] + 0.3, D=D, label="Feed distributor")],
                clad=[], rho_liq=rho_b, rho_tray=rho_b, Pd=Pd, Td=Td, fv=False,
                min_skirt=4.0 if tag == "C-105" else 4.5, bottoms_pump=pump, col=col)


def c201():
    e, Pd, Td = _common("C-201")
    R = results()["vac"]
    S = streams()
    H, Dm, Db, Dt = e["H"], e["D"], e["D2"], e["D3"]
    secs = e["sections"]
    # top-down stack (name, length, kind, D)
    Lc1, Lc2 = cone_len(Dt, Dm), cone_len(Dm, Db)
    stack = [("Top space", 0.40, "space"), ("Demister (wire mesh)", 0.15, "demister"), ("", 0.35, "space"),
             ("LVGO PA spray distributor", 0.30, "dist"), ("", 0.30, "space"),
             ("Bed 1 - LVGO PA (struct. 250Y)", 2.50, "bed"), ("M", 0.90, "mw"), ("LVGO total-draw collector", 0.60, "coll"),
             ("Cone", Lc1, "cone1"),
             ("", 0.30, "space"), ("Bed 2 distributor (LVGO int. reflux)", 0.30, "dist"), ("", 0.20, "space"),
             ("Bed 2 - LVGO/HVGO fract. (struct. 250Y)", 2.50, "bed"), ("M", 0.90, "mw"),
             ("HVGO total-draw collector", 0.60, "coll"), ("", 0.30, "space"), ("HVGO PA distributor", 0.30, "dist"),
             ("", 0.20, "space"), ("Bed 3 - HVGO PA (struct. 125Y)", 3.50, "bed"), ("M", 0.90, "mw"),
             ("Wash oil distributor (spray)", 0.30, "dist"), ("", 0.15, "space"), ("Bed 4 - Wash (grid)", 1.20, "bed"),
             ("", 0.30, "space"), ("Slop wax collector", 0.60, "coll"), ("Flash zone / vapour horn", 3.60, "flash"),
             ("Cone", Lc2, "cone2"), ("", 0.60, "space")]
    zc = H
    items = []
    for name, L, kind in stack:
        items.append(dict(name=name, kind=kind, z1=zc, z0=zc - L))
        zc -= L
    cone1 = next(i for i in items if i["kind"] == "cone1")
    cone2 = next(i for i in items if i["kind"] == "cone2")
    tray_z = [zc - 0.61 * i for i in range(4)]
    trays = [dict(no=i + 1, z=tz, D=Db, passes=2, TS=0.61) for i, tz in enumerate(tray_z)]
    z_steam = tray_z[-1] - 0.6
    levels = dict(LLL=0.6, NLL=2.0, HLL=3.4, LAHH=3.6)
    segs = [dict(kind="cyl", D=Db, z0=0.0, z1=cone2["z0"], name="Boot (stripping / quench)"),
            dict(kind="cone", D0=Db, D1=Dm, z0=cone2["z0"], z1=cone2["z1"], name="Lower cone 30 deg"),
            dict(kind="cyl", D=Dm, z0=cone2["z1"], z1=cone1["z0"], name="Main shell (beds 2-4, flash zone)"),
            dict(kind="cone", D0=Dm, D1=Dt, z0=cone1["z0"], z1=cone1["z1"], name="Upper cone 30 deg"),
            dict(kind="cyl", D=Dt, z0=cone1["z1"], z1=H, name="Top section (bed 1)")]

    def Dat(z):
        for s in segs:
            if s["z0"] <= z <= s["z1"]:
                if s["kind"] == "cyl":
                    return s["D"]
                f = (z - s["z0"]) / (s["z1"] - s["z0"])
                return s["D0"] + f * (s["D1"] - s["D0"])
        return Dt

    internals = []
    for it in items:
        if it["kind"] in ("bed", "dist", "coll", "demister", "flash"):
            zz = (it["z0"] + it["z1"]) / 2
            internals.append(dict(kind=it["kind"], z0=it["z0"], z1=it["z1"], z=zz, D=Dat(zz), label=it["name"]))
    internals.append(dict(kind="steam", z=z_steam, D=Db, label="Steam sparger"))
    internals.append(dict(kind="quench", z=3.75, D=Db, label="VR quench distributor"))
    internals.append(dict(kind="vortex", z=0.0, D=Db, label="Vortex breaker"))
    find = lambda s: next(i for i in items if i["name"].startswith(s))
    flash = find("Flash zone")
    noz = []
    fz = next(s for s in secs if s["name"] == "Flash zone")
    s21 = S["21"]
    Qm = fz["Q_v_m3s"] + fz["L_kg_h"] / 3600 / fz["rho_l"]
    rho_m = (fz["V_kg_h"] + fz["L_kg_h"]) / 3600 / Qm
    n, v = size_nozzle(Qm, rho_m, "vac_feed")
    noz.append(N("N1", "Feed - transfer line from H-201 (tangential to vapour horn)", n, flash["z1"] - 1.6, "R", 90,
                 Q=Qm, rho=rho_m, crit="vac_feed", v=v))
    s22 = S["22"]
    n, v = size_nozzle(s22["vap_act_m3h"] / 3600, s22["rho_vap"], "vac_vap")
    noz.append(N("N2", "Overhead vapour to J-201 / E-202", n, H, "T", 0, Q=s22["vap_act_m3h"] / 3600, rho=s22["rho_vap"],
                 crit="vac_vap", v=v))
    pa = R["pa"]
    noz.append(flow_noz("N3", "LVGO PA return (+ LVGO reflux)", pa["LVGO"]["flow"], 860.0, "liq_ret",
                        find("LVGO PA spray")["z1"] + 0.2, "L", 270))
    lv_tot = pa["LVGO"]["flow"] + S["23"]["total_kg_h"] + secs[1]["L_kg_h"]
    noz.append(flow_noz("N4", "LVGO total draw to P-201", lv_tot, 739.0, "liq_draw", find("LVGO total")["z0"] - 0.15,
                        "L", 225))
    noz.append(flow_noz("N5", "LVGO internal reflux to bed 2", secs[1]["L_kg_h"], 760.0, "liq_ret",
                        find("Bed 2 distributor")["z1"] + 0.15, "R", 120))
    hv_tot = pa["HVGO"]["flow"] + S["24"]["total_kg_h"] + secs[3]["L_kg_h"]
    noz.append(flow_noz("N6", "HVGO total draw to P-202", hv_tot, 708.0, "liq_draw", find("HVGO total")["z0"] - 0.15,
                        "L", 225))
    noz.append(flow_noz("N7", "HVGO PA return", pa["HVGO"]["flow"], 790.0, "liq_ret", find("HVGO PA dist")["z1"] + 0.15,
                        "L", 300))
    noz.append(flow_noz("N8", "Wash oil (HVGO) to bed 4", secs[3]["L_kg_h"], 790.0, "liq_ret",
                        find("Wash oil")["z1"] + 0.15, "R", 60))
    noz.append(flow_noz("N9", "Slop wax draw to P-203", S["25"]["total_kg_h"], 714.0, "liq_draw",
                        find("Slop wax")["z0"] - 0.15, "R", 135, minimum=3))
    st = R["steam"]
    rs = rho_gas(4.5, 250, 18)
    n, v = size_nozzle(st / 3600 / rs, rs, "steam")
    noz.append(N("N10", "Stripping steam", n, z_steam, "R", 45, Q=st / 3600 / rs, rho=rs, crit="steam", v=v))
    noz.append(flow_noz("N11", "VR quench return (from E-201 outlet)", S["26"]["total_kg_h"] * 0.25, 905.0, "liq_ret",
                        3.75, "L", 300))
    noz.append(flow_noz("N12", "Vacuum residue to P-204", S["26"]["total_kg_h"] * 1.25, 757.0, "suction", -Db / 4, "B", 0))
    psv = [p for p in _psv() if p["protects"] == "C-201"]
    if psv:
        p = psv[0]
        noz.append(N("N13", f"{p['tag']} relief ({p['orifice']})", _psv_inlet(p["orifice"]), H, "T", 0))
    noz.append(N("N14A/B", "LT / LG bridle (boot)", 3, levels["LLL"] - 0.3, "L", 330, qty=2))
    noz.append(N("N15", "Vent / steam-out / N2 purge", 4, H, "T", 0))
    mws = [find("M")["z0"] + 0.45]
    mz = [i for i in items if i["kind"] == "mw"]
    mws = [m["z0"] + 0.45 for m in mz] + [flash["z0"] + 0.8, 4.4]
    for i, zz in enumerate(mws):
        noz.append(N(f"M{i + 1}", "Manway 24\" (36\" in flash zone)" if i == 3 else "Manway 24\"",
                     36 if i == 3 else 24, zz, "F", 0, kind="MW"))
    for n_ in noz:
        n_["rating"] = flange_class(Pd + 0.1 * max(0, levels["HLL"] - n_["z"]), Td)
    plats = [round(n_["z"] - 1.0, 2) for n_ in noz if n_["kind"] == "MW"] + [H + Dt / 4 + 0.2]
    clad = [dict(z0=-Db / 4, z1=H + Dt / 4, mat="410S / 317L", t=3.0)]
    return dict(tag="C-201", e=e, H=H, Ds=[Dm, Db, Dt], D_top=Dt, D_bot=Db, segs=segs, trays=trays, levels=levels,
                nozzles=noz, platforms=plats, internals=internals, items=items, clad=clad, rho_liq=757.0,
                rho_tray=757.0, Pd=Pd, Td=Td, fv=True, sections=secs, min_skirt=6.0, bottoms_pump="P-204A/B")


def columns():
    return [c101(), stripper("C-102"), stripper("C-103"), stripper("C-104"), lightends("C-105"), lightends("C-106"),
            c201()]


# ---------------------------------------------------------------------------
def horizontal(tag):
    e, Pd, Td = _common(tag)
    D, L = e["D"], e["L"]
    boot = None
    if "boot ID" in e.get("size", ""):
        s = e["size"].split("boot ID")[1].replace("m", "").split("x")
        boot = dict(D=float(s[0]), L=float(s[1]))
    return dict(tag=tag, e=e, D=D, L=L, orient="H", boot=boot, Pd=Pd, Td=Td, fv=False,
                rho_liq=780.0 if e["type"] == "Desalter" else (990.0 if "water" in e["service"].lower() else 700.0))


def vertical_drum(tag):
    e, Pd, Td = _common(tag)
    return dict(tag=tag, e=e, D=e["D"], L=e["H"], orient="V", boot=None, Pd=Pd, Td=Td, fv=False, rho_liq=700.0)


def drums():
    out = []
    for e in sorted(_eqs(), key=lambda x: x["tag"]):
        if e["type"] in ("Drum", "Desalter"):
            out.append(horizontal(e["tag"]) if e["orient"] == "H" else vertical_drum(e["tag"]))
    return out


def _eqs():
    from .common import equipment
    return equipment()


def desalter():
    """D-101A/B geometry & nozzles; x = m from left tangent line, z = m above shell bottom."""
    e, Pd, Td = _common("D-101A")
    S = streams()
    D, L = e["D"], e["L"]
    s2, s5, s4, s3 = S["2"], S["5"], S["4"], S["3"]
    noz = [
        flow_noz("N1", "Crude + wash water inlet (to distributor header)", s2["total_kg_h"] + s3["total_kg_h"],
                 s2["rho_liq"], "liq_ret", L / 2, "B", 270),
        flow_noz("N2", "Desalted crude outlet (collector header)", s5["total_kg_h"], s5["rho_liq"], "liq_reflux", L / 2,
                 "T", 0),
        flow_noz("N3A/B", "Brine outlet (to E-118 / WWT)", s4["total_kg_h"], 960.0, "liq_draw", L * 0.25, "B", 180,
                 qty=2, minimum=4),
        N("N4A/B", "Mud-wash inlet (from P-118)", 3, 0.0, "B", 200, qty=2, note="each half"),
        N("N5A-D", "Sludge drain / mud-wash outlet", 4, 0.0, "B", 160, qty=4),
        N("N6", "PSV (PSV-1002/1003, 4M6)", 4, D, "T", 0),
        N("N7", "Vent / N2 purge", 2, D, "T", 0),
        N("N8A-C", "Transformer entrance bushing", 8, D, "T", 0, qty=3),
        N("N9A/B", "Interface level (LT / LDT) - capacitance / RF", 2, D * 0.45, "S", 90, qty=2),
        N("N10A-E", "Try-cocks / interface sample", 1, D * 0.3, "S", 90, qty=5),
        N("N11", "Drain", 3, 0.0, "B", 180),
        N("N12", "Steam-out", 2, D * 0.2, "S", 270),
        N("N13", "Low-level / low-low level switch (LSLL - transformer trip)", 2, D * 0.82, "S", 90),
        N("M1/M2", "Manway 24\" (one per head)", 24, D / 2, "H", 0, kind="MW", qty=2),
    ]
    for n in noz:
        n["rating"] = flange_class(Pd, Td)
    xpos = {"N1": L / 2, "N2": L / 2, "N3A/B": L * 0.25, "N4A/B": L * 0.15, "N5A-D": L * 0.1, "N6": L * 0.85,
            "N7": L * 0.92, "N8A-C": L * 0.33, "N9A/B": L * 0.6, "N10A-E": L * 0.68, "N11": L * 0.75,
            "N12": L * 0.08, "N13": L * 0.55, "M1/M2": 0.0}
    for n in noz:
        n["x"] = xpos[n["mark"]]
    return dict(tag="D-101A/B", e=e, D=D, L=L, nozzles=noz, Pd=Pd, Td=Td,
                saddles=[0.2 * L, 0.8 * L], levels=dict(interface_NLL=0.30 * D, interface_HLL=0.40 * D,
                                                       interface_LLL=0.20 * D, grids=[0.55 * D, 0.62 * D, 0.69 * D]))
