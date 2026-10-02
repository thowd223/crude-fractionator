"""Shell & tube (TEMA R / API 660) and air-cooler (API 661) FEED geometry, thickness and weights;
PSV (API 526) selection data."""
from __future__ import annotations

import math

from .common import (RHO_STEEL, S_allow, equipment, flange_class, num, plate, psvs, results, round_up)
from .vessel import t_min, t_shell

# Tube count / bundle diameter correlation (Coulson & Richardson Vol.6 Table 12.4), Db = OD (Nt/K1)^(1/n1)
K1N1 = {("sq", 1): (0.215, 2.207), ("sq", 2): (0.156, 2.291), ("sq", 4): (0.158, 2.263),
        ("tri", 1): (0.319, 2.142), ("tri", 2): (0.249, 2.207), ("tri", 4): (0.175, 2.285)}
TEMA_MIN = [(610, 9.5), (762, 9.5), (1016, 11.1), (1524, 12.7), (2032, 14.3), (2540, 15.9)]


def tema_min(D):
    for d, t in TEMA_MIN:
        if D <= d:
            return t
    return 15.9


def _split(x, default=10.0):
    if x is None:
        return default, default
    if isinstance(x, (int, float)):
        return float(x), float(x)
    a = str(x).split("/")
    sh = num(a[0], default)
    tu = num(a[1], default) if len(a) > 1 else sh
    return sh, tu


def _hot_flow(tag):
    p = results()["preheat"]
    for e in p["exch"]:
        if e["tag"] == tag:
            return e["hot_flow"], e["cold_flow"]
    for t in p["trims"]:
        if t["tag"] == tag:
            return t["flow"], None
    return None, None


def shell_tube():
    out = []
    for e in equipment():
        if e["type"] != "Shell & tube":
            continue
        tema = e["tema"].split()[0]
        nsh = int(e.get("n_shells") or e.get("shells") or 1)
        A_sh = e["area_m2"] / nsh
        clean = any(s in e["service"].lower() for s in ("condenser", "reboiler", "steam"))
        OD = 19.05 if clean else 25.4
        bwg = "14 BWG (2.11 mm)" if clean else "12 BWG (2.77 mm)"
        wall = 2.11 if clean else 2.77
        pitch_type = "tri" if (clean and tema[1:] in ("EU", "EL", "XS")) else "sq"
        pitch = 1.25 * OD if pitch_type == "tri" else (25.4 if OD == 19.05 else 31.75)
        L = 6096 if A_sh > 60 else 4877
        passes = 1 if tema.startswith("AX") else (2 if tema[2] in ("U", "T") or "K" in tema else 4 if A_sh > 300 else 2)
        if tema.endswith("U"):
            passes = 2
        Nt = math.ceil(A_sh / (math.pi * OD / 1000 * (L - 150) / 1000))
        if tema.endswith("U"):
            Nt = math.ceil(Nt / 2) * 2
        K1, n1 = K1N1[(pitch_type, min(4, passes) if passes != 1 else 1)]
        Db = OD * (Nt / K1) ** (1 / n1)
        clr = 95 if tema.endswith("S") else (25 if tema[2] in ("L", "M", "U") else 60)
        port = round_up(Db + clr, 50)
        Ds = round_up(port * 1.6, 50) if "K" in tema else port
        Psh, Ptu = _split(e.get("des_P"))
        fv = "FV" in str(e.get("des_P"))
        Td = float(e["des_T"])
        moc = e.get("moc", "CS")
        shell_mat = "SA-387-11-2" if moc.lower().startswith("1.25cr") else "SA-516-70"
        S = S_allow(shell_mat, Td)
        CA = float(e.get("ca_mm") or 3)
        tc, tl = t_shell(Psh / 10, Ds, S, 0.85, CA)
        t_req = max(tc + CA, tema_min(Ds), t_min(Ds) + CA)
        if fv:
            t_req = max(t_req, 0.008 * Ds + CA)       # vacuum shell: FEED allowance (stiffened by baffles)
        t_sh = plate(t_req)
        tchan = plate(max(t_shell(Ptu / 10, port, S, 0.85, CA)[0] + CA, tema_min(port)))
        tube_kgm = math.pi * (OD - wall) * wall * 7.85e-3 * (0.57 if "Ti" in moc else 1.0)
        bundle = Nt * L / 1000 * tube_kgm * 1.35 + (math.pi / 4 * (port / 1000) ** 2 * 0.08 * RHO_STEEL * 2)
        shell_w = math.pi * (Ds + t_sh) / 1000 * (L / 1000 + 0.6) * t_sh / 1000 * RHO_STEEL
        chan_w = math.pi * (port + tchan) / 1000 * 1.2 * tchan / 1000 * RHO_STEEL * 2.2 + \
            math.pi / 4 * (port / 1000) ** 2 * 0.08 * RHO_STEEL
        empty = (bundle + shell_w + chan_w) * 1.12
        V = math.pi / 4 * (Ds / 1000) ** 2 * (L / 1000 + 1.5)
        V_metal = Nt * math.pi / 4 * (OD / 1000) ** 2 * L / 1000 * 0.15
        hydro = empty + (V - V_metal) * 1000
        operating = empty + (V - V_metal) * 0.85 * 800
        hf, cf = _hot_flow(e["tag"])
        out.append(dict(tag=e["tag"], service=e["service"], tema=e["tema"], size=f"{int(Ds)}-{L} {tema}",
                        n_shells=nsh, series=e.get("series", 1), parallel=e.get("parallel", 1), area_total=e["area_m2"],
                        area_shell=A_sh, duty_kw=e["duty_kw"], U=e["U"], LMTD=e.get("LMTD"), F=e.get("F"),
                        shellside=e["shellside"], tubeside=e["tubeside"], Th_in=e["Th_in"], Th_out=e["Th_out"],
                        Tc_in=e["Tc_in"], Tc_out=e["Tc_out"], hot_flow=hf, cold_flow=cf, P_shell=Psh, P_tube=Ptu,
                        fv=fv, des_T=Td, moc=moc, CA=CA, OD=OD, bwg=bwg, pitch=pitch, pitch_type=pitch_type, L=L,
                        passes=passes, Nt=Nt, Db=Db, port=port, Ds=Ds, t_shell=t_sh, t_chan=tchan,
                        shell_mat=shell_mat, empty=empty, operating=operating, hydrotest=hydro,
                        rating_shell=flange_class(Psh, Td), rating_tube=flange_class(Ptu, Td),
                        D_eq=e.get("D"), area=e["area"]))
    return out


def air_coolers():
    out = []
    for e in equipment():
        if e["type"] != "Air cooler":
            continue
        A = e["area_m2"]
        bays = e["bays"]
        L_t = 12.0
        tubes_row_bundle = 44            # 2.9 m bundle, 63.5 mm transverse pitch
        bundles = 2 * bays
        a_tube = math.pi * 0.0254 * L_t
        nt = math.ceil(A / a_tube)
        rows = math.ceil(nt / (bundles * tubes_row_bundle))
        bays_req = math.ceil(nt / (2 * tubes_row_bundle * 6))    # at 6 rows
        rows_sel = max(4, rows)
        Td = float(e["des_T"])
        Pd = float(e["des_P"])
        op = e["op_T"].split("(air")[1].replace(")", "").split("->")
        Tai, Tao = float(op[0]), float(op[1])
        air_kg_s = e["duty_kw"] / (1.006 * (Tao - Tai))
        fan_area = 0.40 * 6.0 * L_t / 2
        fan_D = round_up(math.sqrt(4 * fan_area / math.pi), 0.3)
        tubes_w = nt * L_t * 2.6
        empty = tubes_w * 1.3 + bays * 16000
        out.append(dict(tag=e["tag"], service=e["service"], duty_kw=e["duty_kw"], area=A, bays=bays, bundles=bundles,
                        fans=e["fans"], motor_kw=e["motor_kw"], fan_kw=e["fan_kw"], Nt=nt, rows=rows,
                        rows_sel=rows_sel, bays_req_6rows=bays_req, des_P=Pd, des_T=Td, op_T=e["op_T"], Tai=Tai,
                        Tao=Tao, air_kg_s=air_kg_s, fan_D=fan_D, moc=e["moc"], L_t=L_t, empty=empty,
                        operating=empty + nt * math.pi / 4 * 0.0206 ** 2 * L_t * 750,
                        rating=flange_class(Pd, Td), draft="Forced" if Td < 175 else "Induced",
                        header="Plug-type box" if Pd < 35 else "Cover-plate", eq_area=e["area"]))
    return out


API526 = {"D": (71, "1D2"), "E": (126, "1E2"), "F": (198, "1.5F2"), "G": (324, "1.5G3"), "H": (506, "1.5H3"),
          "J": (830, "2J3"), "K": (1186, "3K4"), "L": (1841, "3L4"), "M": (2323, "4M6"), "N": (2800, "4N6"),
          "P": (4116, "4P6"), "Q": (7129, "6Q8"), "R": (10323, "6R8"), "T": (16774, "8T10")}


def psv_data():
    out = []
    for p in psvs():
        A_eff, desig = API526[p["orifice"]]
        Tset = p["T"]
        inlet = flange_class(p["set_barg"] * 1.21, Tset)
        fire = "fire" in p["case"].lower()
        out.append(dict(**p, A_eff=A_eff, designation=desig, inlet_rating=max(150, inlet), outlet_rating=150,
                        overpressure="21 % (fire)" if fire else "10 %",
                        bonnet="Balanced bellows" if p["dest"] == "Flare" else "Conventional",
                        body="A217 WC6" if Tset > 425 else "A216 WCC", trim="316 SS (Stellited seats)",
                        backpressure="0.5 barg superimposed (var.) + 10 % built-up" if p["dest"] == "Flare" else "atm",
                        util=p["area_mm2"] / (p["count"] * A_eff),
                        Kd=0.975, Kb=1.0, phase="Vapour" if p["T"] > 0 else "-"))
    return out
