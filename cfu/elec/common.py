"""Electrical design basis constants, rating tables and location helpers (FEED level).

All numbers here are electrical design assumptions (not process data). Process data (motor ratings,
absorbed power, equipment list) is read from data/equipment.json; locations from data/layout.json when it
exists, otherwise from the CONVENTIONS.md area blocks.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .. import basis

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "deliverables" / "05-electrical"

PWR = basis.UTILITIES["power"]
KV_UT = PWR["utility_kV"]          # 13.8
KV_MV = PWR["mv_kV"]               # 4.16
V_LV = PWR["lv_V"]                 # 480
HZ = PWR["ac_hz"]
V_UPS = PWR["ups_V"]               # 120

MV_MOTOR_KW = 200.0                # motors >= 200 kW at 4.16 kV
FUTURE = 1.25                      # 25 % future margin on transformers
DIV = dict(C=1.0, I=0.3, S=0.1)    # maximum-demand diversity (continuous / intermittent / standby)

# Utility source
UT_FAULT_KA = 31.5
UT_XR = 15.0

# Standard ratings
TX_STD_KVA = [500, 750, 1000, 1500, 2000, 2500, 3000, 3750, 5000, 7500, 10000, 12000, 15000, 20000]
ONAF_FACTOR = {True: 1.25, False: 1.333}       # <=10 MVA: +25 % fan rating (IEEE C57.12.10), above: +33 %
SWGR_KA = {KV_UT: [25.0, 31.5, 40.0, 50.0, 63.0], KV_MV: [31.5, 40.0, 50.0, 63.0],
           V_LV / 1000: [42.0, 50.0, 65.0, 85.0, 100.0]}
BUS_A = [600, 800, 1200, 1600, 2000, 2500, 3000, 3200, 4000, 5000]
NEC_A = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200, 225, 250, 300, 350,
         400, 450, 500, 600, 700, 800, 1000, 1200, 1600, 2000, 2500, 3000, 4000]
MCCB_FRAMES = [125, 250, 400, 600, 800, 1200]
CT_PRI = [50, 75, 100, 150, 200, 300, 400, 600, 800, 1000, 1200, 1500, 2000, 3000, 4000]


def std_up(x, table):
    for t in table:
        if t >= x - 1e-9:
            return t
    return table[-1]


def motor_eff_pf(kw: float, mv: bool = False):
    """Full-load efficiency and power factor by motor size (NEMA Premium / IEEE 841 typical values)."""
    if mv:
        return (0.965, 0.89) if kw >= 500 else (0.955, 0.87)
    for lim, eff, pf in [(1.5, 0.80, 0.76), (7.5, 0.875, 0.82), (30, 0.91, 0.85), (90, 0.935, 0.86),
                         (160, 0.95, 0.87), (1e9, 0.955, 0.87)]:
        if kw <= lim:
            return eff, pf


VFD_EFF = 0.97
VFD_PF = 0.95       # supply-side displacement/true PF of a 6-pulse/AFE drive (AFE for MV)
LRC = 6.5           # locked-rotor current multiple (DOL)
LR_PF = 0.20        # MV motor starting PF
LR_PF_LV = 0.35     # LV motor starting PF
XD2 = 0.17          # motor subtransient reactance (pu on motor kVA)

# -------------------------------------------------------------------- cables
# Copper conductors, XLPE 90 C. Base ampacities at 30 C in free air / on ladder tray (A).
# LV: IEC 60364-5-52 Table B.52.12 method E, multicore, 3 loaded conductors.
AMP_LV = {2.5: 32, 4: 42, 6: 54, 10: 75, 16: 100, 25: 127, 35: 158, 50: 192, 70: 246, 95: 298, 120: 346,
          150: 399, 185: 456, 240: 538, 300: 621}
# 3.6/6 kV 3-core screened Cu/XLPE in air (IEC 60502-2 Annex B, approx.) - used for 4.16 kV
AMP_MV = {35: 170, 50: 205, 70: 255, 95: 310, 120: 355, 150: 405, 185: 460, 240: 540, 300: 615}
# 8.7/15 kV single-core Cu/XLPE in trefoil, in air (IEC 60502-2 Annex B, approx.) - used for 13.8 kV
AMP_HV = {70: 300, 95: 360, 120: 410, 150: 460, 185: 520, 240: 610, 300: 690, 400: 790, 500: 900, 630: 1020}
# conductor AC resistance at 90 C (ohm/km) = IEC 60228 DC 20 C x 1.28
R20 = {2.5: 7.41, 4: 4.61, 6: 3.08, 10: 1.83, 16: 1.15, 25: 0.727, 35: 0.524, 50: 0.387, 70: 0.268, 95: 0.193,
       120: 0.153, 150: 0.124, 185: 0.0991, 240: 0.0754, 300: 0.0601, 400: 0.0470, 500: 0.0366, 630: 0.0283}
R90 = {s: r * 1.28 for s, r in R20.items()}


def X_km(size, kind):
    if kind == "LV":
        return 0.085 if size <= 50 else 0.078
    if kind == "MV":
        return 0.11 if size <= 70 else 0.10
    return 0.13


K_XLPE = 143.0          # adiabatic constant Cu/XLPE 90 -> 250 C (IEC 60364-5-54)
DERATE = dict(ambient=0.91, group=0.80)     # 40 C air (35 C design + solar), 6+ cables touching on tray
LV_MIN_MM2 = 4.0        # minimum LV power cable (mechanical strength, refinery practice)
MV_MIN_MM2 = 35.0
# Current-limiting MCCB / MCP let-through energy at prospective LV fault (A^2 s), by MCCB rating (A) -
# typical manufacturer data for 65-85 kA class devices; ACB feeders use t = 0.05 s instantaneous.
LET_THROUGH = [(30, 0.05e6), (60, 0.15e6), (125, 0.5e6), (250, 1.5e6), (400, 3.0e6), (630, 6.0e6)]


def earth_size(s):
    if s <= 16:
        return s
    if s <= 35:
        return 16
    return std_up(s / 2, sorted(R20))


# -------------------------------------------------------------------- locations
SS_REF = (25.0, 12.5)           # SS-100 centroid (x 10-40, y 5-20)
FAR_REF = (55.0, 11.0)          # FAR-100 centroid (x 45-65, y 5-17)
RISER_M = 15.0                  # riser / termination / routing allowance
RACK_TOP_EXTRA_M = 10.0         # extra for air-cooler fan motors on top of main rack

# Fallback equipment points (m) from CONVENTIONS.md area blocks
AREA_PTS = {
    "DESALT": (35.0, 47.0),     # x 0-70, south of main rack: desalters D-101A/B, preheat
    "DESALT_P": (35.0, 68.0),   # desalting/preheat pumps along south side of rack
    "CDU": (110.0, 100.0),      # x 70-150 north of rack: C-101, strippers, OH system
    "CDU_P": (110.0, 82.0),     # CDU pumps under/next to rack north side
    "CDU_AC": (115.0, 75.0),    # CDU air coolers on main rack
    "H101": (105.0, 35.0),      # H-101 in heater band y 20-50
    "H201": (165.0, 35.0),
    "LE": (40.0, 115.0),        # light ends NW
    "LE_P": (40.0, 95.0),
    "LE_AC": (45.0, 75.0),
    "VDU": (190.0, 100.0),      # x 150-230 north of rack
    "VDU_P": (190.0, 82.0),
    "VDU_AC": (190.0, 75.0),
    "PLOT": (115.0, 75.0),      # unit centroid (lighting / receptacle distribution)
}
TAG_AREA = {
    "P-101": "DESALT_P", "P-102": "DESALT_P", "P-114": "DESALT_P", "P-118": "DESALT_P", "X-101": "DESALT_P",
    "X-102": "DESALT_P", "D-101A": "DESALT", "D-101B": "DESALT",
    "P-103": "CDU_P", "P-104": "CDU_P", "P-105": "CDU_P", "P-106": "CDU_P", "P-107": "CDU_P", "P-108": "CDU_P",
    "P-109": "CDU_P", "P-110": "CDU_P", "P-111": "CDU_P", "P-112": "CDU_P", "X-103": "CDU_P",
    "A-101": "CDU_AC", "A-103": "CDU_AC", "A-104": "CDU_AC", "A-105": "CDU_AC",
    "K-101": "H101", "K-102": "H101", "H-101": "H101", "H-201": "H201",
    "P-115": "LE_P", "P-116": "LE_P", "P-117": "LE_P", "A-106": "LE_AC", "A-107": "LE_AC", "A-108": "LE_AC",
    "P-201": "VDU_P", "P-202": "VDU_P", "P-203": "VDU_P", "P-204": "VDU_P", "P-205": "VDU_P", "P-206": "VDU_P",
    "X-104": "VDU_P", "A-201": "VDU_AC", "A-202": "VDU_AC",
}


def _walk_xy(obj, out):
    """Collect {tag: (x, y)} from an arbitrary layout JSON structure."""
    if isinstance(obj, dict):
        tag = obj.get("tag") or obj.get("id") or obj.get("name")
        xy = None
        for kx, ky in (("x", "y"), ("X", "Y"), ("cx", "cy"), ("x_m", "y_m"), ("E", "N"), ("east", "north")):
            if isinstance(obj.get(kx), (int, float)) and isinstance(obj.get(ky), (int, float)):
                xy = (float(obj[kx]), float(obj[ky]))
                # a footprint given as SW corner + size: use centre
                for kw, kh in (("w", "h"), ("W", "L"), ("dx", "dy"), ("width", "depth")):
                    if isinstance(obj.get(kw), (int, float)) and isinstance(obj.get(kh), (int, float)) \
                            and obj.get("origin", "centre") in ("sw", "SW", "corner"):
                        xy = (xy[0] + obj[kw] / 2, xy[1] + obj[kh] / 2)
                break
        if xy is None:
            for k in ("xy", "pos", "position", "center", "centre", "coords"):
                v = obj.get(k)
                if isinstance(v, (list, tuple)) and len(v) >= 2 and all(isinstance(c, (int, float)) for c in v[:2]):
                    xy = (float(v[0]), float(v[1]))
                    break
                if isinstance(v, dict) and isinstance(v.get("x"), (int, float)):
                    xy = (float(v["x"]), float(v["y"]))
                    break
        if isinstance(tag, str) and xy:
            out.setdefault(tag, xy)
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                if isinstance(v, dict) and k not in out and isinstance(k, str) and "-" in k:
                    sub = {}
                    _walk_xy(dict(v, tag=v.get("tag", k)), sub)
                    for t, p in sub.items():
                        out.setdefault(t, p)
                else:
                    _walk_xy(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk_xy(v, out)


class Locator:
    """Equipment coordinates: data/layout.json when present, else CONVENTIONS area blocks."""

    def __init__(self):
        self.xy = {}
        p = DATA / "layout.json"
        self.source = "CONVENTIONS.md area blocks (data/layout.json not available)"
        if p.exists():
            try:
                _walk_xy(json.loads(p.read_text()), self.xy)
                if self.xy:
                    self.source = f"data/layout.json ({len(self.xy)} tagged items)"
            except Exception as e:     # noqa: BLE001 - layout is optional input
                self.source = f"CONVENTIONS.md area blocks (data/layout.json unreadable: {e})"
        self.ss = self.xy.get("SS-100", SS_REF)
        self.far = self.xy.get("FAR-100", FAR_REF)
        self.used_layout = set()

    def point(self, tag: str):
        """tag may be a unit tag ('P-101A'), a pair ('P-101A/B') or a fan ('A-101-M1')."""
        cands = [tag]
        base = tag.split("-M")[0] if tag.startswith(("A-", "K-")) and "-M" in tag else tag
        cands.append(base)
        if base[-1:] in "AB" and base[:-1].count("-") == 1 and base[:2] in ("P-", "K-", "X-"):
            cands += [base[:-1] + "A/B", base[:-1]]
        if "/" in base:
            cands += [base.split("/")[0], base.split("/")[0][:-1]]
        if base.startswith("X-") and base.count("-") == 2:      # X-101-PA
            cands.append("-".join(base.split("-")[:2]))
        for c in cands:
            if c in self.xy:
                self.used_layout.add(c)
                return self.xy[c], "layout"
        key = "-".join(base.split("-")[:2])
        k2 = key[:-1] if key[-1] in "AB" and key[:2] in ("P-", "K-") else key
        area = TAG_AREA.get(key) or TAG_AREA.get(k2)
        return AREA_PTS[area or "PLOT"], "area:" + (area or "PLOT")

    def route(self, tag: str, extra: float = 0.0):
        (x, y), src = self.point(tag)
        L = abs(x - self.ss[0]) + abs(y - self.ss[1]) + RISER_M + extra
        return round(L / 5.0 + 0.4999) * 5.0, src


def r1(x, n=1):
    return None if x is None else round(float(x), n)
