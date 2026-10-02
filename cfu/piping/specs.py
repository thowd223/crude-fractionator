"""Piping class data for the routing / iso / stress / MTO generators.

Class letters, ratings, materials and corrosion allowances are those of CONVENTIONS.md and
CFU-000-PI-SPC-001. Material properties are FEED transcriptions of ASME B31.3-2022 Table A-1
(allowable stress), Table C-1 (total thermal expansion) and Table C-6 (modulus); dimensional data per
ASME B36.10M / B16.9 / B16.5 / B16.47 / B16.10. Verify against the latest editions at detailed design.
"""
from __future__ import annotations

import bisect
import math

# ----------------------------------------------------------------------------------------------
# Piping classes
# ----------------------------------------------------------------------------------------------
CLASSES = {
    #      rating, material key, description,                          CA mm, RT %, PWHT,  hardness, colour (GLB)
    "A1": dict(rating=150, mat="CS", desc="CS ASTM A106 Gr.B", ca=3.0, rt=10, pwht=False, hb=None,
               rgb=(150, 150, 150)),
    "A2": dict(rating=150, mat="CS", desc="CS ASTM A106 Gr.B HIC-resistant (NACE MR0103)", ca=6.0, rt=20,
               pwht=True, hb=200, rgb=(230, 200, 40)),
    "A3": dict(rating=300, mat="CS", desc="CS ASTM A106 Gr.B HIC-resistant (NACE MR0103)", ca=6.0, rt=20,
               pwht=True, hb=200, rgb=(210, 170, 30)),
    "B1": dict(rating=300, mat="CS", desc="CS ASTM A106 Gr.B", ca=3.0, rt=10, pwht=False, hb=None,
               rgb=(60, 120, 200)),
    "B2": dict(rating=300, mat="P5", desc="5Cr-1/2Mo ASTM A335 P5", ca=3.0, rt=100, pwht=True, hb=241,
               rgb=(220, 110, 40)),
    "B3": dict(rating=300, mat="P9", desc="9Cr-1Mo ASTM A335 P9", ca=3.0, rt=100, pwht=True, hb=241,
               rgb=(200, 40, 40)),
    "C1": dict(rating=600, mat="CS", desc="CS killed ASTM A106 Gr.B", ca=3.0, rt=20, pwht=False, hb=None,
               rgb=(120, 60, 170)),
    "S1": dict(rating=150, mat="CS", desc="CS ASTM A106 Gr.B", ca=1.5, rt=5, pwht=False, hb=None,
               rgb=(60, 170, 90)),
    "S2": dict(rating=600, mat="P11", desc="1.25Cr-1/2Mo ASTM A335 P11", ca=1.5, rt=100, pwht=True, hb=225,
               rgb=(20, 120, 60)),
    "S3": dict(rating=300, mat="CS", desc="CS ASTM A106 Gr.B", ca=1.5, rt=10, pwht=False, hb=None,
               rgb=(100, 200, 120)),
    "U1": dict(rating=150, mat="CS", desc="CS ASTM A106 Gr.B (cement-lined CW >= 12in)", ca=1.5, rt=5,
               pwht=False, hb=None, rgb=(40, 170, 200)),
    "U2": dict(rating=150, mat="SS", desc="SS ASTM A312 TP304 / galv. CS", ca=0.0, rt=5, pwht=False, hb=None,
               rgb=(170, 200, 220)),
    "V1": dict(rating=150, mat="P5", desc="5Cr-1/2Mo ASTM A335 P5 / A691 5CR", ca=3.0, rt=100, pwht=True,
               hb=241, rgb=(240, 130, 90)),
    "F1": dict(rating=150, mat="CS", desc="CS killed, impact-tested ASTM A333 Gr.6", ca=3.0, rt=10,
               pwht=False, hb=None, rgb=(110, 110, 110)),
}


def cls(c):
    return CLASSES.get(c, CLASSES["A1"])


def pwht_text(c, t_mm=None):
    k = cls(c)
    if k["pwht"]:
        if k["mat"] in ("P5", "P9"):
            return "YES - all thk (P-No.5B, B31.3 Tbl 331.1.1) 705-770 C"
        if k["mat"] == "P11":
            return "YES (P-No.4) 705-745 C"
        return "YES - service (sour/HIC) 595-650 C"
    if t_mm and t_mm > 19.0:
        return "YES - t > 19 mm (P-No.1)"
    return "NO"


def nde_text(c):
    k = cls(c)
    s = f"{k['rt']} % RT of BW"
    if k["rt"] >= 100:
        s += "; 100 % MT/PT of fillets"
    if k["hb"]:
        s += f"; HB <= {k['hb']}"
    if k["mat"] in ("P5", "P9", "P11"):
        s += "; 100 % PMI"
    return s


# ----------------------------------------------------------------------------------------------
# Materials (allowable stress MPa vs C, total expansion mm/m from 21 C, cold modulus GPa)
# ----------------------------------------------------------------------------------------------
_S = {
    "CS": [(38, 138), (204, 138), (260, 130), (316, 119), (343, 117), (371, 113), (399, 90), (427, 74), (454, 60),
           (482, 45), (510, 32), (538, 19)],
    "P5": [(38, 138), (93, 125), (149, 120), (204, 119), (260, 118), (316, 116), (343, 114), (371, 112), (399, 109),
           (427, 103), (454, 91), (482, 74), (510, 55), (538, 40), (566, 29), (593, 20)],
    "P9": [(38, 138), (93, 129), (149, 125), (204, 124), (260, 123), (316, 121), (343, 119), (371, 117), (399, 114),
           (427, 110), (454, 105), (482, 90), (510, 72), (538, 51), (566, 35), (593, 23)],
    "P11": [(38, 138), (93, 131), (149, 127), (204, 126), (260, 125), (316, 124), (371, 122), (427, 118), (454, 113),
            (482, 100), (510, 75), (538, 50), (566, 32)],
    "SS": [(38, 138), (93, 138), (149, 138), (204, 130), (260, 122), (316, 115), (371, 110), (427, 106)],
}
# B31.3 Table C-1 total linear expansion (in/100 ft from 70 F) converted to mm/m
_E_TOT = {
    "CS": [(21, 0.0), (93, 0.825), (149, 1.517), (204, 2.25), (260, 3.02), (316, 3.83), (371, 4.69), (427, 5.58),
           (482, 6.51), (538, 7.41), (593, 8.37)],
    "P5": [(21, 0.0), (93, 0.78), (149, 1.43), (204, 2.08), (260, 2.77), (316, 3.47), (371, 4.19), (427, 4.93),
           (482, 5.70), (538, 6.47), (593, 7.26)],
    "P11": [(21, 0.0), (93, 0.80), (149, 1.48), (204, 2.20), (260, 2.95), (316, 3.73), (371, 4.55), (427, 5.42),
            (482, 6.30), (538, 7.19), (593, 8.10)],
    "SS": [(21, 0.0), (93, 1.22), (149, 2.18), (204, 3.17), (260, 4.18), (316, 5.20), (371, 6.25), (427, 7.33)],
}
_E_TOT["P9"] = _E_TOT["P5"]
E_COLD = {"CS": 203.0, "P5": 213.0, "P9": 213.0, "P11": 204.0, "SS": 195.0}   # GPa
MAT_NAME = {"CS": "Carbon steel", "P5": "5Cr-1/2Mo", "P9": "9Cr-1Mo", "P11": "1.25Cr-1/2Mo", "SS": "SS304"}
RHO_STEEL = 7850.0


def _interp(tab, x):
    xs = [a for a, _ in tab]
    if x <= xs[0]:
        return tab[0][1]
    if x >= xs[-1]:
        return tab[-1][1]
    i = bisect.bisect_left(xs, x)
    (x0, y0), (x1, y1) = tab[i - 1], tab[i]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def allow_S(mat, T):
    return _interp(_S[mat], T)


def expansion_mm_per_m(mat, T):
    """Total thermal expansion from 21 C install temperature (mm/m), signed for cold service."""
    return _interp(_E_TOT[mat], max(T, 21.0)) if T >= 21 else -0.011 * (21 - T)


def Sa(mat, T):
    """B31.3 eq.(1a) allowable displacement stress range, f = 1.0 (< 7000 cycles)."""
    Sc = allow_S(mat, 21)
    Sh = allow_S(mat, T)
    return 1.25 * Sc + 0.25 * Sh


def Y_coef(mat, T):
    if mat == "SS":
        return 0.4
    if T <= 482:
        return 0.4
    if T <= 510:
        return 0.5
    return 0.7


def W_factor(mat, T, seamless):
    """B31.3 Table 302.3.5 weld joint strength reduction (CrMo, creep range) - seamless = 1.0."""
    if seamless or mat not in ("P5", "P9", "P11") or T <= 510:
        return 1.0
    return max(0.64, 1.0 - (T - 510) * 0.0022)


# ----------------------------------------------------------------------------------------------
# Dimensions - ASME B36.10M (OD mm, walls mm by schedule)
# ----------------------------------------------------------------------------------------------
PIPE = {
    0.75: (26.7, {"10": 2.11, "STD": 2.87, "40": 2.87, "XS": 3.91, "80": 3.91, "160": 5.56, "XXS": 7.82}),
    1: (33.4, {"10": 2.77, "STD": 3.38, "40": 3.38, "XS": 4.55, "80": 4.55, "160": 6.35, "XXS": 9.09}),
    1.5: (48.3, {"10": 2.77, "STD": 3.68, "40": 3.68, "XS": 5.08, "80": 5.08, "160": 7.14, "XXS": 10.15}),
    2: (60.3, {"10": 2.77, "STD": 3.91, "40": 3.91, "XS": 5.54, "80": 5.54, "160": 8.74, "XXS": 11.07}),
    3: (88.9, {"10": 3.05, "STD": 5.49, "40": 5.49, "XS": 7.62, "80": 7.62, "160": 11.13, "XXS": 15.24}),
    4: (114.3, {"10": 3.05, "STD": 6.02, "40": 6.02, "XS": 8.56, "80": 8.56, "120": 11.13, "160": 13.49,
                "XXS": 17.12}),
    6: (168.3, {"10": 3.40, "STD": 7.11, "40": 7.11, "XS": 10.97, "80": 10.97, "120": 14.27, "160": 18.26,
                "XXS": 21.95}),
    8: (219.1, {"10": 3.76, "20": 6.35, "30": 7.04, "STD": 8.18, "40": 8.18, "60": 10.31, "XS": 12.70, "80": 12.70,
                "100": 15.09, "120": 18.26, "140": 20.62, "160": 23.01}),
    10: (273.0, {"10": 4.19, "20": 6.35, "30": 7.80, "STD": 9.27, "40": 9.27, "60": 12.70, "XS": 12.70,
                 "80": 15.09, "100": 18.26, "120": 21.44, "140": 25.40, "160": 28.58}),
    12: (323.8, {"10": 4.57, "20": 6.35, "30": 8.38, "STD": 9.53, "40": 10.31, "XS": 12.70, "60": 14.27,
                 "80": 17.48, "100": 21.44, "120": 25.40, "140": 28.58, "160": 33.32}),
    14: (355.6, {"10": 6.35, "20": 7.92, "30": 9.53, "STD": 9.53, "40": 11.13, "XS": 12.70, "60": 15.09,
                 "80": 19.05, "100": 23.83, "120": 27.79, "140": 31.75, "160": 35.71}),
    16: (406.4, {"10": 6.35, "20": 7.92, "30": 9.53, "STD": 9.53, "40": 12.70, "XS": 12.70, "60": 16.66,
                 "80": 21.44, "100": 26.19, "120": 30.96, "140": 36.53, "160": 40.49}),
    18: (457.0, {"10": 6.35, "20": 7.92, "STD": 9.53, "30": 11.13, "XS": 12.70, "40": 14.27, "60": 19.05,
                 "80": 23.83, "100": 29.36, "120": 34.93, "140": 39.67, "160": 45.24}),
    20: (508.0, {"10": 6.35, "20": 9.53, "STD": 9.53, "30": 12.70, "XS": 12.70, "40": 15.09, "60": 20.62,
                 "80": 26.19, "100": 32.54, "120": 38.10, "140": 44.45, "160": 50.01}),
    24: (610.0, {"10": 6.35, "20": 9.53, "STD": 9.53, "XS": 12.70, "30": 14.27, "40": 17.48, "60": 24.61,
                 "80": 30.96, "100": 38.89, "120": 46.02, "140": 52.37, "160": 59.54}),
    28: (711.0, {"10": 7.92, "STD": 9.53, "20": 12.70, "XS": 12.70, "30": 15.88}),
    30: (762.0, {"10": 7.92, "STD": 9.53, "20": 12.70, "XS": 12.70, "30": 15.88, "40": 17.48}),
    36: (914.0, {"10": 7.92, "STD": 9.53, "20": 12.70, "XS": 12.70, "30": 15.88, "40": 19.05}),
    42: (1067.0, {"STD": 9.53, "20": 12.70, "XS": 12.70, "30": 15.88, "40": 19.05}),
    48: (1219.0, {"STD": 9.53, "XS": 12.70}),
    54: (1372.0, {"STD": 9.53, "XS": 12.70}),
}
SIZES = sorted(PIPE)
PLATE_WT = [14.27, 15.88, 17.48, 19.05, 20.62, 22.23, 23.83, 25.40, 28.58, 31.75, 34.93, 38.10]
_SCH_ORDER = ["10", "20", "30", "40", "60", "80", "100", "120", "140", "160", "STD", "XS", "XXS"]


def nps_str(n):
    if n == 0.75:
        return '3/4"'
    if n == 1.5:
        return '1-1/2"'
    return f'{int(n)}"' if float(n).is_integer() else f'{n}"'


def od(nps):
    return PIPE[_snap(nps)][0]


def _snap(nps):
    return min(SIZES, key=lambda s: abs(s - nps))


def step(nps, k):
    i = SIZES.index(_snap(nps))
    return SIZES[max(0, min(len(SIZES) - 1, i + k))]


def seamless(nps):
    return nps <= 24


def min_practice(nps, mat):
    """Company minimum wall for mechanical strength (stated in RPT-001)."""
    if mat == "SS":
        return "40" if nps <= 2 else "10"
    if nps <= 2:
        return "XS"
    return "STD"


def pick_schedule(nps, t_req_nom, mat="CS"):
    """Return (label, wall) - lightest standard schedule >= t_req_nom (and >= company minimum)."""
    n = _snap(nps)
    walls = PIPE[n][1]
    mp = min_practice(n, mat)
    tmin = walls.get(mp, 0.0) if isinstance(mp, str) else 0.0
    need = max(t_req_nom, tmin)
    cands = sorted(((w, name) for name, w in walls.items() if w >= need - 1e-6),
                   key=lambda a: (a[0], _SCH_ORDER.index(a[1]) if a[1] in _SCH_ORDER else 99))
    if cands:
        w = cands[0][0]
        names = [nm for ww, nm in cands if abs(ww - w) < 1e-6]
        num = [nm for nm in names if nm.isdigit()]
        lab = ("SCH " + num[0]) if num else names[0]
        if num and ("STD" in names or "XS" in names) and n >= 12:
            lab = [nm for nm in names if nm in ("STD", "XS")][0]
        return lab, w
    for w in PLATE_WT:
        if w >= need:
            return f"WT {w:.2f}", w
    return f"WT {need:.1f}", need


def wall_calc(nps, P_barg, T_C, c):
    """B31.3 304.1.2 eq.(3a): t = PD / (2(SEW + PY)); tm = t + c; t_nom >= tm / (1 - 0.125)."""
    k = cls(c)
    mat = k["mat"]
    D = od(nps)
    P = max(P_barg, 0.0) * 0.1  # MPa
    S = allow_S(mat, T_C)
    sm = seamless(nps)
    E = 1.0 if (sm or k["rt"] >= 100) else 0.85
    W = W_factor(mat, T_C, sm)
    Y = Y_coef(mat, T_C)
    t = P * D / (2 * (S * E * W + P * Y))
    tm = t + k["ca"]
    tn = tm / 0.875
    lab, w = pick_schedule(nps, tn, mat)
    return dict(nps=nps, OD=D, P=P_barg, T=T_C, S=round(S, 1), E=E, W=round(W, 3), Y=Y, c=k["ca"], t=round(t, 2),
                tm=round(tm, 2), t_nom_req=round(tn, 2), sch=lab, wall=w, mat=mat,
                form="SMLS" if sm else ("EFW 100% RT" if k["rt"] >= 100 else "EFW spot RT"))


def ext_pressure_ok(nps, wall, c, T_C, mat, L_unstiff_m=None):
    """Simplified long-cylinder elastic buckling check for full vacuum (1.013 bar external), FS = 3."""
    D = od(nps)
    t = wall * 0.875 - c
    E = E_COLD[mat] * 1000.0 * max(0.75, 1 - 0.00045 * max(T_C - 21, 0))   # MPa, hot modulus approx.
    Pc = 2 * E / (1 - 0.3 ** 2) * (t / D) ** 3      # MPa
    Pa = Pc / 3.0
    return Pa * 10.0, Pa * 10.0 >= 1.013             # bar


def test_pressure(P_barg, T_C, c):
    """B31.3 345.4.2 hydrostatic: PT = 1.5 P ST/S, ST/S <= 6.5."""
    mat = cls(c)["mat"]
    ratio = min(6.5, allow_S(mat, 21) / allow_S(mat, T_C))
    return 1.5 * P_barg * ratio, ratio


# ----------------------------------------------------------------------------------------------
# Fitting dimensions (mm) - interpolated by NPS
# ----------------------------------------------------------------------------------------------
def _dim(tab, nps):
    return _interp(sorted(tab.items()), nps)


TEE_C = {1: 38, 1.5: 57, 2: 64, 3: 86, 4: 105, 6: 143, 8: 178, 10: 216, 12: 254, 14: 279, 16: 305, 18: 343,
         20: 381, 24: 432, 28: 521, 30: 559, 36: 673, 42: 762, 48: 889, 54: 1000}
RED_H = {1: 51, 1.5: 64, 2: 76, 3: 89, 4: 102, 6: 140, 8: 152, 10: 178, 12: 203, 14: 330, 16: 356, 18: 381,
         20: 508, 24: 508, 28: 610, 36: 610, 54: 610}
WN_Y = {150: {1: 56, 2: 62, 3: 68, 4: 75, 6: 87, 8: 100, 10: 100, 12: 113, 14: 125, 16: 125, 18: 138, 20: 143,
              24: 151, 28: 140, 36: 156, 42: 168, 48: 183, 54: 200},
        300: {1: 62, 2: 68, 3: 79, 4: 84, 6: 97, 8: 110, 10: 116, 12: 129, 14: 141, 16: 144, 18: 157, 20: 160,
              24: 167, 28: 200, 36: 225, 42: 240, 48: 260, 54: 280},
        600: {1: 62, 2: 73, 3: 83, 4: 102, 6: 117, 8: 133, 10: 152, 12: 156, 14: 165, 16: 178, 18: 184, 20: 190,
              24: 203}}
GATE_FTF = {150: {1: 127, 2: 178, 3: 203, 4: 229, 6: 267, 8: 292, 10: 330, 12: 356, 14: 381, 16: 406, 18: 432,
                  20: 457, 24: 508, 28: 610, 36: 711, 42: 787, 48: 864, 54: 940},
            300: {1: 165, 2: 216, 3: 283, 4: 305, 6: 403, 8: 419, 10: 457, 12: 502, 14: 762, 16: 838, 18: 914,
                  20: 991, 24: 1143, 28: 1346, 36: 1651},
            600: {1: 216, 2: 292, 3: 356, 4: 432, 6: 559, 8: 660, 10: 787, 12: 838, 14: 889, 16: 991, 18: 1092,
                  20: 1194, 24: 1397}}
GLOBE_FTF = {150: {1: 165, 2: 203, 3: 241, 4: 292, 6: 406, 8: 495, 10: 622, 12: 698, 14: 787, 16: 914},
             300: {1: 216, 2: 267, 3: 318, 4: 356, 6: 445, 8: 559, 10: 622, 12: 711, 14: 838, 16: 864},
             600: {1: 254, 2: 292, 3: 356, 4: 432, 6: 559, 8: 660, 10: 787, 12: 838}}
CV_FTF = {150: {1: 184, 2: 267, 3: 318, 4: 368, 6: 473, 8: 568, 10: 708, 12: 775, 16: 900},
          300: {1: 197, 2: 282, 3: 337, 4: 394, 6: 508, 8: 610, 10: 752, 12: 819, 16: 950},
          600: {1: 210, 2: 286, 3: 337, 4: 394, 6: 508, 8: 610, 10: 752, 12: 819}}


def elbow_A(nps):
    return 1.5 * 25.4 * nps / 1000.0          # LR 90 deg centre-to-end (m)


def tee_C(nps):
    return _dim(TEE_C, nps) / 1000.0


def red_H(nps):
    return _dim(RED_H, nps) / 1000.0


def wn_len(nps, rating):
    return _dim(WN_Y[rating], nps) / 1000.0


def valve_ftf(kind, nps, rating):
    tab = {"gate": GATE_FTF, "check": GLOBE_FTF, "globe": GLOBE_FTF, "cv": CV_FTF}.get(kind, GATE_FTF)[rating]
    if nps > max(tab):
        tab = GATE_FTF[rating]
    return _dim(tab, nps) / 1000.0


def pipe_kg_m(nps, wall):
    D = od(nps)
    return math.pi * (D - wall) * wall * 1e-6 * RHO_STEEL


def insul_thk(insul, T):
    if insul == "H":
        for lim, t in ((100, 40), (200, 50), (300, 75), (400, 100), (500, 125)):
            if T <= lim:
                return t
        return 150
    if insul == "ST":
        return 50
    if insul == "P":
        return 40
    if insul == "C":
        return 50
    return 0


def line_weights(nps, wall, insul, T, rho_content):
    """kg/m: steel, content (operating), water (hydro), insulation incl. cladding."""
    D = od(nps) / 1000.0
    di = D - 2 * wall / 1000.0
    a_in = math.pi / 4 * di ** 2
    ti = insul_thk(insul, T) / 1000.0
    ins = math.pi / 4 * ((D + 2 * ti) ** 2 - D ** 2) * 160.0 + (math.pi * (D + 2 * ti) * 0.8 * 7.8 if ti else 0.0)
    return dict(steel=pipe_kg_m(nps, wall), content=a_in * rho_content, water=a_in * 1000.0, insul=ins)
