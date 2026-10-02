"""Shared data access, material properties and standard sizes for the mechanical package.

All process numbers are read from data/*.json (never re-typed).  Material allowable stresses are
ASME II-D Table 1A values (customary units converted to MPa and interpolated) - FEED accuracy,
to be re-verified against the edition of record at detailed design.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "deliverables" / "02-equipment"
G = 9.81
RHO_STEEL = 7850.0


@lru_cache(None)
def load(name):
    return json.loads((DATA / name).read_text())


def equipment():
    return load("equipment.json")


def eq(tag):
    for e in equipment():
        if e["tag"] == tag:
            return e
    raise KeyError(tag)


def streams():
    return {s["no"]: s for s in load("streams.json")}


def results():
    return load("process_results.json")


def psvs():
    return load("psv.json")


# ---------------------------------------------------------------------------
# Allowable stress S (MPa) vs design temperature (C) - ASME II-D Table 1A
F2C = lambda f: (f - 32) / 1.8
KSI = 6.894757
_SA516 = [(100, 20.0), (200, 20.0), (300, 20.0), (400, 20.0), (500, 20.0), (600, 19.4), (650, 18.8), (700, 18.1),
          (750, 14.8), (800, 12.0), (850, 9.3), (900, 6.7), (950, 4.0)]
_SA387_11 = [(100, 21.4), (500, 21.4), (600, 21.4), (650, 21.4), (700, 21.4), (750, 21.0), (800, 20.6), (850, 20.0),
             (900, 18.7), (950, 13.7), (1000, 9.3), (1050, 6.3)]
_SA387_5 = [(100, 21.4), (600, 21.4), (650, 21.4), (700, 21.2), (750, 20.9), (800, 20.2), (850, 18.2), (900, 13.1),
            (950, 10.6), (1000, 7.4), (1050, 5.0)]


def _tab(t):
    return [(round(F2C(f), 1), round(k * KSI, 1)) for f, k in t]


MATERIALS = {
    "SA-516-70": dict(name="SA-516 Gr.70 (CS plate, normalised)", S=_tab(_SA516), Sy20=260.0, Su=485.0,
                      chart="CS-2", E_mod=[(20, 202), (100, 198), (200, 192), (300, 185), (400, 176), (450, 171)]),
    "SA-387-11-2": dict(name="SA-387 Gr.11 Cl.2 (1.25Cr-0.5Mo)", S=_tab(_SA387_11), Sy20=310.0, Su=515.0,
                        chart="CS-2", E_mod=[(20, 206), (100, 202), (200, 196), (300, 190), (400, 183), (500, 175)]),
    "SA-387-5-2": dict(name="SA-387 Gr.5 Cl.2 (5Cr-0.5Mo)", S=_tab(_SA387_5), Sy20=310.0, Su=515.0,
                       chart="CS-2", E_mod=[(20, 213), (100, 209), (200, 203), (300, 197), (400, 189), (500, 180)]),
}


def interp(tab, x):
    if x <= tab[0][0]:
        return tab[0][1]
    for (x0, y0), (x1, y1) in zip(tab, tab[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return tab[-1][1]


def S_allow(mat, T):
    return interp(MATERIALS[mat]["S"], T)


def E_mod(mat, T):
    """Young's modulus, MPa."""
    return interp(MATERIALS[mat]["E_mod"], T) * 1000.0


def Sy(mat, T):
    """Yield strength (approx. II-D Table Y-1 trend), MPa."""
    s20 = MATERIALS[mat]["Sy20"]
    return s20 * interp([(20, 1.0), (100, 0.92), (200, 0.85), (300, 0.76), (400, 0.68), (450, 0.65), (500, 0.62)], T)


def B_factor(mat, T, A):
    """External-pressure factor B (MPa) from strain A: elastic line B = AE/2 blended into a plateau of
    ~0.5*Sy(T) (represents chart CS-2 knee).  Exact in the elastic region that governs thin columns."""
    E = E_mod(mat, T)
    Be = A * E / 2.0
    Bmax = 0.5 * Sy(mat, T) * 0.95
    n = 4.0
    return Be / (1 + (Be / Bmax) ** n) ** (1 / n)


def material_for(moc: str, des_T: float) -> str:
    m = (moc or "").lower()
    if "1.25cr" in m and "shell" in m:
        return "SA-387-11-2"
    if m.startswith("5cr") or "sa-387 gr5" in m:
        return "SA-387-5-2"
    return "SA-516-70"


# ---------------------------------------------------------------------------
PLATES = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 30, 32, 36, 38, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100]


def plate(t_mm):
    for p in PLATES:
        if p >= t_mm - 1e-6:
            return p
    return math.ceil(t_mm / 5) * 5


NPS = [1, 1.5, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 30, 32, 36, 42, 48, 54, 60, 66, 72]
_ID_SMALL = {1: 26.6, 1.5: 40.9, 2: 52.5, 3: 77.9, 4: 102.3, 6: 154.1, 8: 202.7, 10: 254.5}
NPS_OD = {12: 323.9, 14: 355.6, 16: 406.4, 18: 457.0, 20: 508.0, 24: 610.0}


def nps_id(n):
    if n in _ID_SMALL:
        return _ID_SMALL[n]
    od = NPS_OD.get(n, n * 25.4)
    return od - 2 * 9.53


def nps_for_area(A_m2, minimum=2):
    for n in NPS:
        if n < minimum:
            continue
        if math.pi / 4 * (nps_id(n) / 1000) ** 2 >= A_m2:
            return n
    return NPS[-1]


def nps_str(n):
    return f'{n:g}"'


# ASME B16.5 Group 1.1 (A105/A516) P-T ratings, barg
B165 = {150: [(38, 19.6), (50, 19.2), (100, 17.7), (150, 15.8), (200, 13.8), (250, 12.1), (300, 10.2), (325, 9.3),
              (350, 8.4), (375, 7.4), (400, 6.5), (425, 5.5), (450, 4.6), (475, 3.7)],
        300: [(38, 51.1), (50, 50.1), (100, 46.6), (150, 45.1), (200, 43.8), (250, 41.9), (300, 39.8), (325, 38.7),
              (350, 37.6), (375, 36.4), (400, 34.7), (425, 28.8), (450, 23.0), (475, 17.4)],
        600: [(38, 102.1), (50, 100.2), (100, 93.2), (150, 90.2), (200, 87.6), (250, 83.9), (300, 79.6), (325, 77.4),
              (350, 75.1), (375, 72.7), (400, 69.4), (425, 57.5), (450, 46.0), (475, 34.9)],
        900: [(38, 153.2), (100, 139.8), (200, 131.4), (300, 119.5), (400, 104.2), (450, 69.0)]}


def flange_class(P_barg, T_C):
    for c in (150, 300, 600, 900):
        if interp(B165[c], T_C) >= P_barg:
            return c
    return 1500


def num(x, default=None):
    """Parse '3.5', 'FV / 3.5', 3.5 -> internal design pressure (barg)."""
    if x is None:
        return default
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).replace("FV", "").replace("-", " ").replace("/", " ").split()
    vals = []
    for t in s:
        try:
            vals.append(float(t))
        except ValueError:
            pass
    return max(vals) if vals else default


def is_fv(x):
    return isinstance(x, str) and "FV" in x


def round_up(x, step):
    return math.ceil(x / step - 1e-9) * step


def ins_thk(T):
    """Heat-conservation insulation thickness (mm) by operating temperature."""
    if T is None or T < 60:
        return 0
    if T < 150:
        return 50
    if T < 250:
        return 75
    if T < 350:
        return 100
    return 125
