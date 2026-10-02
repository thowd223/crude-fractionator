"""ASME VIII Div.1 FEED-level mechanical design of columns, drums and desalters.

* UG-27 cylindrical shells (circumferential + longitudinal), UG-32(d) 2:1 ellipsoidal heads,
  UG-32(g) conical sections, UG-16 / fabrication minimum thickness.
* UG-28 / UG-33 external pressure (factor A from the Div.2 4.4.5 closed-form that generates
  Fig. G; factor B elastic B = A.E/2 with plastic knee), UG-29 stiffening rings.
* UG-99(b) hydrotest, UG-23(b)/(d) longitudinal stress under wind + weight.
* ASCE 7-16 wind (Exposure C, V = 150 mph 3-s gust, Kd 0.95, G 0.85 / flexible check).
* Weights: shell, heads, cones, skirt, nozzles, internals, clad, platforms, insulation,
  operating liquid, hydrotest water.
"""
from __future__ import annotations

import math

from .common import (B_factor, E_mod, G, RHO_STEEL, S_allow, Sy, ins_thk, material_for, plate, round_up)

P_FV = 0.1034            # MPa external (15 psi) for full vacuum
WIND_V = 67.06           # m/s (150 mph)
KD, KZT, KE = 0.95, 1.0, 1.0
CF = 0.70                # round, moderately smooth, h/D ~ 7-25
ATTACH = 0.6             # m added to insulated OD for ladders / piping
E_JOINT = 1.0            # full RT (columns, desalters, large drums)
E_JOINT_SMALL = 0.85     # spot RT (small drums)
RING_SPACING = 3000.0     # mm, max. stiffening-ring spacing on vacuum shells (assumption)
MIN_T_RULE = "t_min (excl. CA) = max(UG-16(b) 1.5 mm, D/1000 + 2.5 mm)"


# ---------------------------------------------------------------------------
def t_shell(P, D_mm, S, E, CA):
    R = D_mm / 2 + CA
    tc = P * R / (S * E - 0.6 * P)
    tl = P * R / (2 * S * E + 0.4 * P)
    return tc, tl


def t_head(P, D_mm, S, E, CA):
    D = D_mm + 2 * CA
    return P * D / (2 * S * E - 0.2 * P)


def t_cone(P, D_mm, S, E, CA, alpha=30.0):
    D = D_mm + 2 * CA
    return P * D / (2 * math.cos(math.radians(alpha)) * (S * E - 0.6 * P))


def t_min(D_mm):
    return max(1.5, D_mm / 1000 + 2.5)


def ext_cyl(Do, t, L, mat, T):
    """UG-28(c) allowable external pressure (MPa) for cylinder; Do, t, L in mm (t corroded)."""
    Ro = Do / 2
    Mx = L / math.sqrt(Ro * t)
    dt = Do / t
    if Mx >= 2 * dt ** 0.94:
        Ch = 0.55 * t / Do
    elif Mx >= 13:
        Ch = 1.12 * Mx ** -1.058
    elif Mx > 1.5:
        Ch = 0.92 / (Mx - 0.579)
    else:
        Ch = 1.0
    A = 1.6 * Ch * t / Do
    A = min(A, 0.1)
    B = B_factor(mat, T, A)
    Pa = 4 * B / (3 * dt)
    return Pa, A, B


def ext_head(Do, t, mat, T):
    """UG-33(d) 2:1 ellipsoidal head, Ro = 0.9 Do."""
    Ro = 0.9 * Do
    A = 0.125 / (Ro / t)
    B = B_factor(mat, T, A)
    return B / (Ro / t), A, B


def ring_required(Do, ts, Ls, mat, T, P=P_FV):
    """UG-29: smallest external flat-bar ring (h x b mm) satisfying I_s (ring alone)."""
    E = E_mod(mat, T)
    best = None
    for b in (16, 20, 25, 30):
        for h in range(80, 410, 10):
            if h / b > 12:                      # flat-bar slenderness limit (local buckling)
                break
            As = h * b
            teff = ts + As / Ls
            B = 0.75 * P * Do / teff
            A = 2 * B / E
            Is_req = Do ** 2 * Ls * teff * A / 14.0
            I = b * h ** 3 / 12
            if I >= Is_req:
                if best is None or As < best["As"]:
                    best = dict(h=h, b=b, As=As, Is_req=Is_req, I=I, A=A, B=B)
                break
    return best


# ---------------------------------------------------------------------------
def qz(z):
    zz = max(z, 4.57)
    Kz = 2.01 * (zz / 274.32) ** (2 / 9.5)
    return 0.613 * Kz * KZT * KD * KE * WIND_V ** 2, Kz


def _seg_at(segs, z):
    for s in segs:
        if s["z0"] - 1e-9 <= z <= s["z1"] + 1e-9:
            return s
    return segs[-1] if z > segs[-1]["z1"] else segs[0]


def _D_at(g, z):
    s = _seg_at(g["segs"], z)
    if s["kind"] == "cyl":
        return s["D"]
    f = (z - s["z0"]) / (s["z1"] - s["z0"])
    return s["D0"] + f * (s["D1"] - s["D0"])


def vol_head(D):
    return math.pi * D ** 3 / 24


def area_head(D):
    return 1.084 * D ** 2


def nozzle_kg(nps, kind="N", qty=1):
    w = 1.6 * nps ** 1.75
    if kind == "MW":
        w = w * 1.4 + 150
    return w * qty


# ---------------------------------------------------------------------------
def design_column(g, skirt_h=None):
    """Full FEED design of a vertical column described by geometry dict g."""
    e = g["e"]
    tag = g["tag"]
    CA = float(e.get("ca_mm") or 3)
    Td = g["Td"]
    Pd = g["Pd"]               # barg
    P = Pd / 10.0              # MPa
    mat = material_for(e.get("moc", ""), Td)
    S = S_allow(mat, Td)
    S_amb = S_allow(mat, 40)
    E = E_JOINT
    H = g["H"]
    lv = g["levels"]
    rho_l = g["rho_liq"]
    ring = None
    res_segs = []
    # ---- pressure / minimum / external per segment
    for s in g["segs"]:
        Dm = (s["D"] if s["kind"] == "cyl" else max(s["D0"], s["D1"])) * 1000
        h_liq = max(0.0, lv["HLL"] - s["z0"])
        Pz = P + rho_l * G * h_liq / 1e6
        if s["kind"] == "cyl":
            tc, tl = t_shell(Pz, Dm, S, E, CA)
            t_p = max(tc, tl)
        else:
            t_p = t_cone(Pz, Dm, S, E, CA)
            tc, tl = t_p, 0
        tm = t_min(Dm)
        r = dict(name=s["name"], kind=s["kind"], D_mm=Dm, z0=s["z0"], z1=s["z1"], P_calc=Pz, t_circ=tc, t_long=tl,
                 t_press=t_p, t_minfab=tm, t_req=max(t_p, tm) + CA, t_ext=None, ring=None)
        if g["fv"]:
            # external pressure: cylinders with rings at spacing Ls; cones as equivalent cylinder
            if s["kind"] == "cyl":
                L_unst = (s["z1"] - s["z0"]) * 1000
                Ls = min(L_unst, RING_SPACING)
            else:
                Ls = (s["z1"] - s["z0"]) * 1000 / 2 * (1 + min(s["D0"], s["D1"]) / max(s["D0"], s["D1"]))
            for tn in [x for x in range(int(CA) + 4, 81)]:
                tcor = tn - CA
                te = tcor * (math.cos(math.radians(30)) if s["kind"] == "cone" else 1.0)
                Pa, A, B = ext_cyl(Dm + 2 * tn, te, Ls, mat, Td)
                if Pa >= P_FV:
                    break
            r["t_ext"] = tn
            r["ext"] = dict(Ls=Ls, Pa=Pa, A=A, B=B, Do=Dm + 2 * tn)
            # also no-ring case for information (cylinders)
            if s["kind"] == "cyl":
                L0 = (s["z1"] - s["z0"]) * 1000 + Dm / 4 / 3 * 2
                for tn0 in range(int(CA) + 4, 101):
                    if ext_cyl(Dm + 2 * tn0, tn0 - CA, L0, mat, Td)[0] >= P_FV:
                        break
                r["t_ext_norings"] = tn0
                if Ls < L_unst - 1:
                    r["ring"] = ring_required(Dm + 2 * tn, tn - CA, Ls, mat, Td)
                    r["n_rings"] = max(0, math.ceil(L_unst / Ls) - 1)
        r["t_nom"] = plate(max(r["t_req"], r["t_ext"] or 0))
        res_segs.append(r)
    # ---- heads
    heads = {}
    for pos, D in (("top", g["D_top"]), ("bottom", g["D_bot"])):
        Dm = D * 1000
        h_liq = lv["HLL"] + D / 4 if pos == "bottom" else 0
        Pz = P + rho_l * G * h_liq / 1e6
        th = t_head(Pz, Dm, S, E, CA)
        tr = max(th, t_min(Dm)) + CA
        te = None
        if g["fv"]:
            for tn in range(int(CA) + 4, 81):
                if ext_head(Dm + 2 * tn, tn - CA, mat, Td)[0] >= P_FV:
                    break
            te = tn
        adj = next(r for r in (res_segs if pos == "bottom" else res_segs[::-1]) if r["kind"] == "cyl")
        t_formed = max(tr, te or 0)                       # minimum thickness after forming
        heads[pos] = dict(D_mm=Dm, P_calc=Pz, t_press=th, t_req=tr, t_ext=te, t_min_formed=t_formed,
                          t_nom=max(plate(t_formed + 1.5), adj["t_nom"]))   # +1.5 mm forming thinning
    # ---- skirt height from NPSH of bottoms pump
    npshr = g.get("npshr", 4.0)
    if skirt_h is None:
        need = npshr + 1.0 + 0.6 + 0.8 - lv["LLL"]
        skirt_h = round_up(max(g.get("min_skirt", 3.0), need), 0.5)
    # ---- weights & wind (iterate wind thickness)
    Gf, gtype = 0.85, "rigid"
    for it in range(8):
        W = weights(g, res_segs, heads, skirt_h, CA, mat)
        if it:
            fn0 = natural_freq(g, W, res_segs, skirt_h, sk["t_nom"], mat)
            Gf, gtype = gust_factor(W["H_total"], g["D_top"] + 2 * W["ins_mm"] / 1000 + ATTACH, fn0)
        wind = wind_load(g, W, skirt_h, Gf)
        changed = False
        for r in res_segs:
            chk = long_stress(g, r, W, wind, P, S, mat, Td, CA, skirt_h)
            r["long"] = chk
            if not chk["ok"]:
                r["t_nom"] = plate(r["t_nom"] + 1)
                r["t_wind"] = r["t_nom"]
                changed = True
        sk = skirt_check(g, W, wind, skirt_h, mat)
        if not changed and it >= 2:
            break
    W = weights(g, res_segs, heads, skirt_h, CA, mat, skirt_t=sk["t_nom"])
    wind = wind_load(g, W, skirt_h, Gf)
    sk = skirt_check(g, W, wind, skirt_h, mat)
    wind["gtype"] = gtype
    # ---- hydrotest
    Pt = 1.3 * Pd * S_amb / S
    h_water = H + g["D_top"] / 4 + g["D_bot"] / 4
    Pt_bot = Pt + 1000 * G * h_water / 1e5
    bot = res_segs[0]
    tcor_new = bot["t_nom"]          # test in new condition
    sig_test = (Pt_bot / 10) * (bot["D_mm"] / 2 + 0.6 * tcor_new) / tcor_new
    hydro = dict(Pt_top=Pt, Pt_bot=Pt_bot, sigma_bot=sig_test, lim=0.9 * Sy(mat, 20), S_amb=S_amb, S_des=S,
                 position="vertical (field), water at 15 C min.")
    # natural frequency / vortex shedding
    fn = natural_freq(g, W, res_segs, skirt_h, sk["t_nom"], mat)
    D_top = g["D_top"]
    Vcr = fn * (D_top + 2 * W["ins_mm"] / 1000) / 0.2
    anchor = anchor_bolts(g, W, wind, sk)
    return dict(tag=tag, mat=mat, S=S, S_amb=S_amb, E=E, CA=CA, Pd=Pd, Td=Td, fv=g["fv"], segs=res_segs, heads=heads,
                skirt=sk, skirt_h=skirt_h, W=W, wind=wind, hydro=hydro, fn=fn, Vcr=Vcr, anchor=anchor,
                npshr=npshr)


def weights(g, segs, heads, skirt_h, CA, mat, skirt_t=None):
    """Point-mass model (z above grade, kg) + summary."""
    pts = []          # (z_grade, kg, cat)
    zb = skirt_h
    for r in segs:
        z0, z1 = r["z0"], r["z1"]
        nsl = max(1, int((z1 - z0) / 0.5))
        for i in range(nsl):
            za = z0 + (z1 - z0) * i / nsl
            zb_ = z0 + (z1 - z0) * (i + 1) / nsl
            Dm = _D_at(g, (za + zb_) / 2) * 1000 + r["t_nom"]
            L = (zb_ - za) / (math.cos(math.radians(30)) if r["kind"] == "cone" else 1)
            pts.append((zb + (za + zb_) / 2, math.pi * Dm / 1000 * L * r["t_nom"] / 1000 * RHO_STEEL * 1.02, "shell"))
    for pos in ("top", "bottom"):
        h = heads[pos]
        Dm = h["D_mm"] / 1000
        w = area_head(Dm + h["t_nom"] / 1000) * h["t_nom"] / 1000 * RHO_STEEL * 1.08
        z = zb + (g["H"] + Dm / 8 if pos == "top" else -Dm / 8)
        pts.append((z, w, "heads"))
    # skirt
    Dsk = g["D_bot"] + 2 * segs[0]["t_nom"] / 1000
    tsk = skirt_t or max(10, segs[0]["t_nom"])
    nsl = max(1, int(skirt_h / 0.5))
    for i in range(nsl):
        pts.append(((i + 0.5) * skirt_h / nsl, math.pi * Dsk * skirt_h / nsl * tsk / 1000 * RHO_STEEL, "skirt"))
    # base ring + access openings + fireproofing (50 mm, 2.2 t/m3 inside/outside skirt)
    pts.append((0.1, math.pi * Dsk * 0.4 * 0.04 * RHO_STEEL * 2.2, "skirt"))
    pts.append((skirt_h / 2, math.pi * Dsk * skirt_h * 2 * 0.05 * 2200, "fireproofing"))
    # nozzles / manways
    for n in g["nozzles"]:
        pts.append((zb + n["z"], nozzle_kg(n["nps"], n["kind"], n.get("qty", 1)), "nozzles"))
    # trays + support rings
    liq = []
    for t in g["trays"]:
        A = math.pi / 4 * t["D"] ** 2
        unit = 60 if t["D"] < 3 else 75
        pts.append((zb + t["z"], A * unit + math.pi * t["D"] * 0.08 * 0.012 * RHO_STEEL, "internals"))
        liq.append((zb + t["z"], A * (0.75 * 0.05 + 0.12 * 0.4 * t["TS"]) * g["rho_tray"]))
    for it in g.get("internals", []):
        D = it.get("D", g["D_top"])
        A = math.pi / 4 * D ** 2
        z = zb + it.get("z", (it.get("z0", 0) + it.get("z1", 0)) / 2)
        k = it["kind"]
        if k == "bed":
            V = A * (it["z1"] - it["z0"])
            dens = 380 if "grid" in it["label"] else (150 if "125Y" in it["label"] else 210)
            pts.append((z, V * dens + A * 60, "internals"))
            liq.append((z, V * 0.05 * 780))
        elif k == "dist":
            pts.append((z, A * 120, "internals"))
            liq.append((z, A * 0.05 * 780))
        elif k == "coll":
            pts.append((z, A * 220, "internals"))
            liq.append((z, A * 0.25 * 760))
        elif k == "demister":
            pts.append((z, A * 40, "internals"))
        elif k in ("horn", "flash"):
            Dh = D
            pts.append((z, math.pi * Dh * 2.4 * 0.012 * RHO_STEEL * 0.8, "internals"))
        elif k == "draw":
            pts.append((z, A * 0.15 * 90, "internals"))
        else:
            pts.append((z, 250 + 30 * D ** 2, "internals"))
    # clad / lining
    for c in g.get("clad", []):
        Dm = (g["Ds"][0] + g["Ds"][-1]) / 2 if len(g["Ds"]) > 1 else g["Ds"][0]
        Lc = c["z1"] - c["z0"]
        pts.append((zb + (c["z0"] + c["z1"]) / 2, math.pi * Dm * Lc * c["t"] / 1000 * 7900, "clad"))
    # platforms / ladders
    ins = ins_thk(_op_T(g))
    for zp in g["platforms"]:
        D = _D_at(g, min(max(zp, 0), g["H"])) + 2 * ins / 1000
        Ao = math.pi * ((D / 2 + 1.35) ** 2 - (D / 2 + 0.15) ** 2) * 0.6
        pts.append((zb + zp, Ao * 250 + 150, "platforms"))
    Htot = skirt_h + g["H"] + g["D_top"] / 4
    pts.append((Htot / 2, 35 * Htot, "platforms"))
    # insulation (shell + heads)
    if ins:
        for r in segs:
            Dm = _D_at(g, (r["z0"] + r["z1"]) / 2)
            Ash = math.pi * (Dm + 2 * ins / 1000) * (r["z1"] - r["z0"])
            pts.append((zb + (r["z0"] + r["z1"]) / 2, Ash * (ins / 1000 * 130 + 6), "insulation"))
        for D in (g["D_top"], g["D_bot"]):
            pts.append((zb + g["H"] / 2, area_head(D) * (ins / 1000 * 130 + 6), "insulation"))
    # operating liquid: trays/packing + sump to NLL
    for z, w in liq:
        pts.append((z, w, "op_liquid"))
    Db = g["D_bot"]
    nll = g["levels"]["NLL"]
    pts.append((zb + nll / 2, (vol_head(Db) + math.pi / 4 * Db ** 2 * nll) * g["rho_liq"], "op_liquid"))
    # hydrotest water: total internal volume
    Vtot = vol_head(g["D_top"]) + vol_head(Db)
    for s in g["segs"]:
        if s["kind"] == "cyl":
            Vtot += math.pi / 4 * s["D"] ** 2 * (s["z1"] - s["z0"])
        else:
            Ls = s["z1"] - s["z0"]
            Vtot += math.pi * Ls / 12 * (s["D0"] ** 2 + s["D0"] * s["D1"] + s["D1"] ** 2)
    cat = {}
    for z, w, c in pts:
        cat[c] = cat.get(c, 0) + w
    steel = sum(cat.get(k, 0) for k in ("shell", "heads", "skirt", "nozzles", "clad"))
    fabricated = steel + cat.get("internals", 0)
    empty = fabricated + cat.get("platforms", 0) + cat.get("insulation", 0) + cat.get("fireproofing", 0)
    operating = empty + cat.get("op_liquid", 0)
    hydro = fabricated + cat.get("platforms", 0) + cat.get("fireproofing", 0) + Vtot * 1000
    return dict(pts=pts, cat=cat, steel=steel, fabricated=fabricated, empty=empty, operating=operating,
                hydrotest=hydro, V_m3=Vtot, ins_mm=ins, H_total=Htot, skirt_t=tsk, D_skirt=Dsk)


def _op_T(g):
    t = str(g["e"].get("op_T", "100")).split("/")
    try:
        return max(float(x) for x in t)
    except ValueError:
        return 100.0


def gust_factor(h, B, n1, beta=0.01):
    """ASCE 7-16 26.11 - rigid (n1 >= 1 Hz): G = 0.85; flexible: Gf (Exposure C constants)."""
    c, l, eps, bb, ab = 0.20, 152.4, 1 / 5.0, 0.65, 1 / 6.5
    zb = max(0.6 * h, 4.57)
    Iz = c * (10 / zb) ** (1 / 6)
    Lz = l * (zb / 10) ** eps
    Q = math.sqrt(1 / (1 + 0.63 * ((B + h) / Lz) ** 0.63))
    G_rigid = 0.925 * (1 + 1.7 * 3.4 * Iz * Q) / (1 + 1.7 * 3.4 * Iz)
    if n1 >= 1.0:
        return max(0.85, G_rigid), "rigid"
    Vz = bb * (zb / 10) ** ab * WIND_V
    N1 = n1 * Lz / Vz
    Rn = 7.47 * N1 / (1 + 10.3 * N1) ** (5 / 3)

    def Rl(eta):
        return 1 / eta - 1 / (2 * eta ** 2) * (1 - math.exp(-2 * eta)) if eta > 0 else 1

    Rh, RB, RL = Rl(4.6 * n1 * h / Vz), Rl(4.6 * n1 * B / Vz), Rl(15.4 * n1 * B / Vz)
    R2 = 1 / beta * Rn * Rh * RB * (0.53 + 0.47 * RL)
    gR = math.sqrt(2 * math.log(3600 * n1)) + 0.577 / math.sqrt(2 * math.log(3600 * n1))
    Gf = 0.925 * (1 + 1.7 * Iz * math.sqrt(3.4 ** 2 * Q ** 2 + gR ** 2 * R2)) / (1 + 1.7 * 3.4 * Iz)
    return max(0.85, Gf), "flexible"


def wind_load(g, W, skirt_h, Gf=0.85):
    """ASCE 7-16 Ch.29 (other structures) strength-level wind; returns profile & base values."""
    ins = W["ins_mm"] / 1000
    zb = skirt_h
    Htot = W["H_total"]
    dz = 0.5
    prof = []
    z = 0.0
    while z < Htot - 1e-6:
        zc = z + dz / 2
        zv = zc - zb
        if zv < -g["D_bot"] / 4:
            D = W["D_skirt"] + 0.1                       # skirt + fireproofing
        elif zv > g["H"]:
            D = g["D_top"] * 0.8 + 2 * ins + ATTACH
        else:
            D = _D_at(g, min(max(zv, 0), g["H"])) + 2 * ins + ATTACH
        q, Kz = qz(zc)
        F = q * Gf * CF * D * dz                       # N
        prof.append((zc, F, D, q))
        z += dz
    for zp in g["platforms"]:
        q, _ = qz(zb + zp)
        prof.append((zb + zp, q * Gf * 2.0 * 1.2, 0, q))   # platform handrail/toe-plate 1.2 m2, Cf 2.0
    V = sum(F for _, F, _, _ in prof)
    M = sum(F * zc for zc, F, _, _ in prof)

    def M_at(zz):
        return sum(F * (zc - zz) for zc, F, _, _ in prof if zc > zz)

    return dict(prof=prof, V_base=V, M_base=M, M_at=M_at, qh=qz(Htot)[0], Kz_top=qz(Htot)[1], G=Gf)


def _W_above(W, zz, cats=None, exclude=()):
    return sum(w for z, w, c in W["pts"] if z > zz and (cats is None or c in cats) and c not in exclude) * G


def long_stress(g, r, W, wind, P, S, mat, Td, CA, skirt_h):
    """UG-23 longitudinal stress check at the bottom of segment r (corroded, ASD 0.6W)."""
    zz = skirt_h + r["z0"]
    D = (r["D_mm"] if r["kind"] == "cyl" else min(r["D_mm"], _D_at(g, r["z0"]) * 1000))
    t = r["t_nom"] - CA
    if r["kind"] == "cone":
        t *= math.cos(math.radians(30))
    Dm = D + t
    M = 0.6 * wind["M_at"](zz) * 1000           # N.mm
    Wop = _W_above(W, zz, exclude=("skirt", "fireproofing"))
    Wemp = _W_above(W, zz, exclude=("op_liquid", "skirt", "fireproofing"))
    sb = 4 * M / (math.pi * Dm ** 2 * t)
    sw_op = Wop / (math.pi * Dm * t)
    sw_em = Wemp / (math.pi * Dm * t)
    sp = P * D / (4 * t)
    tens = sp + sb - sw_em                      # windward, pressurised, minimum weight
    A = 0.125 / ((Dm / 2 + t) / t)
    Bc = min(B_factor(mat, Td, A), S)
    comp = sb + sw_op + (P_FV * D / (4 * t) if g["fv"] else 0)    # leeward, vacuum / unpressurised
    ok = tens <= S * E_JOINT and comp <= Bc
    return dict(z=zz, M=M / 1e6, sigma_p=sp, sigma_b=sb, sigma_w=sw_op, tension=tens, compression=comp, S=S, B=Bc,
                ok=ok)


def skirt_check(g, W, wind, skirt_h, mat):
    D = W["D_skirt"] * 1000
    M = 0.6 * wind["M_base"] * 1000
    Wop = _W_above(W, 0.0) - _W_above(W, 0.0, cats=("fireproofing",))
    Wem = Wop - _W_above(W, 0.0, cats=("op_liquid",))
    Wht = W["hydrotest"] * G
    S = S_allow(mat, 100)
    Ej = 0.7                                    # skirt-to-head weld
    CA = 1.5
    res = None
    for tn in [x for x in [8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 30, 32, 36, 38, 40, 45, 50]]:
        t = tn - CA
        Dm = D + t
        sb = 4 * M / (math.pi * Dm ** 2 * t)
        comp = sb + Wop / (math.pi * Dm * t)
        comp_ht = 4 * 0.6 * 0.25 * wind["M_base"] * 1000 / (math.pi * Dm ** 2 * t) + Wht / (math.pi * Dm * t)
        tens = sb - Wem / (math.pi * Dm * t)
        A = 0.125 / ((Dm / 2) / t)
        B = min(B_factor(mat, 100, A), S)
        res = dict(t_nom=tn, CA=CA, D_mm=D, M_asd=M / 1e6, W_op=Wop / 1e3, W_em=Wem / 1e3, sigma_b=sb, comp=comp,
                   comp_hydro=comp_ht, tens=tens, B=B, S_E=S * Ej, Ej=Ej, ok=False)
        if comp <= B and comp_ht <= B and tens <= S * Ej:
            res["ok"] = True
            break
    return res


def natural_freq(g, W, segs, skirt_h, tsk, mat):
    """Rayleigh estimate, cantilever with stepped EI (operating mass)."""
    E = E_mod(mat, 20) * 1e6
    Htot = W["H_total"]
    n = 60
    dz = Htot / n
    zs = [(i + 0.5) * dz for i in range(n)]
    m = [0.0] * n
    for z, w, c in W["pts"]:
        i = min(n - 1, max(0, int(z / dz)))
        m[i] += w
    EI = []
    for z in zs:
        zv = z - skirt_h
        if zv < 0:
            D, t = W["D_skirt"], tsk / 1000
        else:
            D = _D_at(g, min(zv, g["H"]))
            r = _seg_at(segs, min(max(zv, 0), g["H"]))
            t = r["t_nom"] / 1000
        EI.append(E * math.pi / 8 * D ** 3 * t)
    F = [mi * G for mi in m]
    # moment from lateral load = weight (static deflection shape)
    Mo = [sum(F[j] * (zs[j] - zs[i]) for j in range(i, n)) for i in range(n)]
    curv = [Mo[i] / EI[i] for i in range(n)]
    slope, y = [0.0] * n, [0.0] * n
    s = 0.0
    yy = 0.0
    for i in range(n):
        s += curv[i] * dz
        yy += s * dz
        slope[i], y[i] = s, yy
    num_ = sum(F[i] * y[i] for i in range(n))
    den = sum(m[i] * y[i] ** 2 for i in range(n))
    w = math.sqrt(num_ / den) if den > 0 else 0
    return w / (2 * math.pi)


def anchor_bolts(g, W, wind, sk):
    D = sk["D_mm"] / 1000
    Dbc = D + 0.25
    nb = max(8, int(round_up(math.pi * Dbc / 0.45, 4)))
    M = 0.6 * wind["M_base"]                 # N.m
    Wmin = (W["fabricated"] + W["cat"].get("platforms", 0)) * G * 0.6
    Fb = 4 * M / (nb * Dbc) - Wmin / nb
    Fb = max(Fb, 0)
    sa = 0.5 * 380e6                          # ASTM F1554 Gr55 Fy 380 MPa, 0.5Fy allowable tension (ASD)
    Ar = Fb / sa * 1e6                        # mm2
    sizes = [(24, 353), (30, 561), (36, 817), (42, 1120), (48, 1470), (56, 2030), (64, 2680), (72, 3460)]
    d = next((s for s, a in sizes if a >= Ar), 80)
    return dict(n=nb, Dbc=Dbc, F_bolt_kN=Fb / 1e3, Ar_mm2=Ar, size=f"M{max(d, 24)}")


# ---------------------------------------------------------------------------
def design_drum(g):
    e = g["e"]
    CA = float(e.get("ca_mm") or 3)
    if "6 mm CA" in (e.get("moc") or ""):
        CA = 6.0
    Td = float(e.get("des_T") or 100)
    Pd = float(g["Pd"])
    P = Pd / 10
    mat = material_for(e.get("moc", ""), Td)
    S = S_allow(mat, Td)
    S_amb = S_allow(mat, 40)
    big = g["D"] >= 2.0 or e["type"] == "Desalter"
    E = E_JOINT if big else E_JOINT_SMALL
    D = g["D"] * 1000
    h_liq = g["D"] if g["orient"] == "H" else g["L"]
    Pz = P + g["rho_liq"] * G * h_liq / 1e6
    tc, tl = t_shell(Pz, D, S, E, CA)
    tr = max(tc, tl, t_min(D)) + CA
    tn = plate(tr)
    th = t_head(Pz, D, S, E, CA)
    thr = max(th, t_min(D)) + CA
    thn = max(plate(thr), tn)
    Dm = (D + tn) / 1000
    L = g["L"]
    Wsh = math.pi * Dm * L * tn / 1000 * RHO_STEEL
    Wh = 2 * area_head(g["D"] + thn / 1000) * thn / 1000 * RHO_STEEL * 1.08
    Vol = math.pi / 4 * g["D"] ** 2 * L + 2 * vol_head(g["D"])
    boot = g.get("boot")
    Wboot = 0
    if boot:
        tb = plate(max(t_shell(Pz, boot["D"] * 1000, S, E, CA)[0], t_min(boot["D"] * 1000)) + CA)
        Wboot = math.pi * boot["D"] * boot["L"] * tb / 1000 * RHO_STEEL + area_head(boot["D"]) * tb / 1000 * RHO_STEEL
        Vol += math.pi / 4 * boot["D"] ** 2 * boot["L"]
    supports = 0.06 * (Wsh + Wh)
    noz = 0.10 * (Wsh + Wh) + 300
    if e["type"] == "Desalter":
        internals = 18000.0                     # electrode grids, distributor, collector, mud wash, bushings
        transformers = 3 * 4500.0
        liq_frac = 1.0
    else:
        internals = 0.04 * (Wsh + Wh) + 200
        transformers = 0
        liq_frac = 0.5
    ins = ins_thk(num_T(e.get("op_T")))
    A_out = math.pi * Dm * L + 2 * area_head(Dm)
    insul = A_out * (ins / 1000 * 130 + 6) if ins else 0
    fabricated = Wsh + Wh + Wboot + supports + noz + internals
    empty = fabricated + transformers + insul + (A_out * 0.0 if not big else 0)
    operating = empty + Vol * liq_frac * g["rho_liq"]
    hydro = fabricated + transformers + Vol * 1000
    Pt = 1.3 * Pd * S_amb / S
    ext = None
    if g["fv"]:
        ext = ext_cyl(D + 2 * tn, tn - CA, L * 1000 + D / 6, mat, Td)
    # FV capability (information): allowable external pressure without rings
    Pa_fv = ext_cyl(D + 2 * tn, tn - CA, L * 1000 + D / 6, mat, Td)[0]
    return dict(tag=g["tag"], mat=mat, S=S, S_amb=S_amb, E=E, CA=CA, Pd=Pd, Td=Td, P_calc=Pz, t_circ=tc, t_long=tl,
                t_req=tr, t_nom=tn, t_head_calc=th, t_head_req=thr, t_head_nom=thn, Vol=Vol, Pt=Pt,
                W=dict(shell=Wsh, heads=Wh, boot=Wboot, supports=supports, nozzles=noz, internals=internals,
                       transformers=transformers, insulation=insul, fabricated=fabricated, empty=empty,
                       operating=operating, hydrotest=hydro), ins_mm=ins, Pa_ext=Pa_fv, D=g["D"], L=L,
                orient=g["orient"], boot=boot)


def num_T(x):
    try:
        return max(float(v) for v in str(x).replace("/", " ").split())
    except (ValueError, TypeError):
        return 60.0
