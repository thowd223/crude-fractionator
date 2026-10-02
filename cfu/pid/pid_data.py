"""P&ID data layer: context (JSON inputs), line sizing, piping classes, line & instrument registries,
and the line topology table (every line drawn on the P&IDs is defined here once).

Numbers come from data/*.json (H&MB streams, process_results, equipment, psv, control loops) and
cfu.basis; the only hand-set values are engineering rules (velocity criteria, density-temperature
slope, latent heats, allowances) which are stated next to where they are used.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from .. import basis
from ..sizing import design_P, design_T

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# ----------------------------------------------------------------------------- sheets
SHEETS = [
    # (seq, area, title2)
    (0, "000", "LEGEND, SYMBOLS & ABBREVIATIONS"),
    (1, "100", "CRUDE CHARGE PUMPS & COLD PREHEAT TRAIN"),
    (2, "100", "ELECTROSTATIC DESALTERS D-101A/B & BOOSTER PUMPS"),
    (3, "100", "HOT PREHEAT TRAIN E-106 TO E-111 & E-113"),
    (4, "100", "ATMOSPHERIC HEATER H-101 - PROCESS COILS"),
    (5, "100", "ATMOSPHERIC HEATER H-101 - FIRING & AIR SYSTEM"),
    (6, "100", "ATMOSPHERIC COLUMN C-101 - FLASH ZONE & BOTTOMS"),
    (7, "100", "ATMOSPHERIC COLUMN C-101 - UPPER SECTION & PUMPAROUNDS"),
    (8, "100", "SIDE STRIPPERS C-102/103/104 & PRODUCT RUNDOWN"),
    (9, "100", "C-101 OVERHEAD SYSTEM & REFLUX DRUM D-102"),
    (10, "100", "NAPHTHA STABILISER C-105"),
    (11, "100", "NAPHTHA SPLITTER C-106"),
    (12, "200", "VACUUM HEATER H-201"),
    (13, "200", "VACUUM COLUMN C-201"),
    (14, "200", "VACUUM PUMPAROUNDS & PRODUCTS"),
    (15, "200", "VACUUM EJECTOR SYSTEM & HOTWELL D-201"),
    (16, "900", "FUEL GAS, FLARE KO & UTILITY HEADERS"),
]


def dwg(seq):
    for s, a, _ in SHEETS:
        if s == seq:
            return f"CFU-{a}-PR-PID-{seq:03d}"
    raise KeyError(seq)


# ----------------------------------------------------------------------------- pipe data
NPS = [0.75, 1, 1.5, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 30, 32, 36, 42, 48, 54, 60]
OD_IN = {0.75: 1.050, 1: 1.315, 1.5: 1.900, 2: 2.375, 3: 3.5, 4: 4.5, 6: 6.625, 8: 8.625, 10: 10.75, 12: 12.75}
WALL_IN = {0.75: 0.154, 1: 0.179, 1.5: 0.200, 2: 0.218, 3: 0.216, 4: 0.237, 6: 0.280, 8: 0.322, 10: 0.365}


def pipe_id_m(nps):
    od = OD_IN.get(nps, float(nps))
    t = WALL_IN.get(nps, 0.375)          # Sch 80 <=2", Sch 40 3-10", STD (0.375") >= 12"
    return (od - 2 * t) * 0.0254


def fmt_nps(n):
    return {0.75: "3/4", 1.5: "1-1/2"}.get(n, f"{n:g}")


# velocity criteria (m/s) - FEED line sizing rules
VMAX = dict(suction=1.2, gravity=1.0, liquid=3.0, water=2.5, cw=2.5, chem=1.5, twophase=15.0, transfer=40.0,
            vtransfer=55.0, steam=30.0, fg=20.0, vacuum=60.0, flare=60.0, air=20.0)


def vmax_for(kind, rho):
    if kind == "vapour":
        return min(25.0, math.sqrt(15000.0 / max(rho, 0.1)))   # rho.v2 <= 15 000 Pa
    if kind == "steam":
        return min(30.0, math.sqrt(30000.0 / max(rho, 0.1)))
    return VMAX[kind]


def size_line(Q_m3h, vmax, min_nps=2.0):
    best = None
    for n in NPS:
        if n < min_nps:
            continue
        A = math.pi / 4 * pipe_id_m(n) ** 2
        v = Q_m3h / 3600 / A
        best = (n, v)
        if v <= vmax:
            return best
    return best


# ----------------------------------------------------------------------------- piping classes
# ASME B16.5-2020 Table 2 pressure-temperature ratings (bar g), FEED transcription (verify at detail design)
_T = [38, 50, 100, 150, 200, 250, 300, 325, 350, 375, 400, 425, 450, 475, 500]
RATINGS = {
    ("1.1", 150): [19.6, 19.2, 17.7, 15.8, 13.8, 12.1, 10.2, 9.3, 8.4, 7.4, 6.5, 5.5, 4.6, 3.7, 2.8],
    ("1.1", 300): [51.1, 50.1, 46.6, 45.1, 43.8, 41.9, 39.8, 38.7, 37.6, 36.4, 34.7, 28.8, 23.0, 17.4, 11.8],
    ("1.1", 600): [102.1, 100.2, 93.2, 90.2, 87.6, 83.9, 79.6, 77.4, 75.1, 72.7, 69.4, 57.5, 46.0, 34.9, 23.5],
    ("1.13", 150): [20.0, 19.5, 17.7, 15.8, 13.8, 12.1, 10.2, 9.3, 8.4, 7.4, 6.5, 5.5, 4.6, 3.7, 2.8],
    ("1.13", 300): [51.7, 51.7, 51.5, 50.3, 48.6, 46.3, 42.9, 41.4, 40.3, 38.9, 36.5, 35.2, 33.7, 31.7, 28.2],
    ("1.14", 300): [51.7, 51.7, 51.5, 50.3, 48.6, 46.3, 42.9, 41.4, 40.3, 38.9, 36.5, 35.2, 33.7, 31.7, 28.2],
    ("1.9", 600): [103.4, 103.4, 103.0, 99.5, 97.2, 92.7, 85.7, 82.6, 80.4, 77.6, 72.9, 70.0, 67.7, 63.4, 46.8],
    ("2.1", 150): [19.0, 18.3, 15.7, 14.2, 13.2, 12.1, 10.2, 9.3, 8.4, 7.4, 6.5, 5.5, 4.6, 3.7, 2.8],
}
CLASSES = {
    # cls: rating, material, B16.5 group, CA mm, service, max service T (C), pipe spec, valve trim, gasket, bolting
    "A1": dict(rating=150, mat="Carbon steel ASTM A106 Gr.B", grp="1.1", ca=3.0, svc="Hydrocarbon <= 230 C, general",
               tmax=230, flange="A105 RF", valves="Gate/globe A216 WCB, trim 8 (13Cr/stellite); ball fire-safe API 607",
               gasket="SPW 304/graphite, CS outer ring (ASME B16.20)", bolting="A193 B7 / A194 2H",
               branch="ASME B31.3 table; weldolet <= 1/2 run size", sch="Sch 40 / STD (min. Sch 80 <= 1-1/2\")"),
    "A2": dict(rating=150, mat="Carbon steel, HIC-resistant (NACE MR0103), PWHT", grp="1.1", ca=6.0,
               svc="Sour water, OH vapour/condensate, wash water/brine", tmax=200, flange="A105N RF, HB <= 200",
               valves="Gate/globe A216 WCB NACE, trim 316/stellite", gasket="SPW 316L/graphite, inner ring",
               bolting="A193 B7M / A194 2HM", branch="Full-encirclement / weldolet, PWHT",
               sch="Sch 80 <= 2\", Sch 40 / XS >= 3\""),
    "B1": dict(rating=300, mat="Carbon steel ASTM A106 Gr.B", grp="1.1", ca=3.0, svc="Hydrocarbon <= 260 C, pump discharges",
               tmax=260, flange="A105 RF", valves="Gate/globe A216 WCB, trim 8; check swing/dual-plate",
               gasket="SPW 304/graphite, inner + outer ring", bolting="A193 B7 / A194 2H",
               branch="Weldolet / reinforced tee", sch="Sch 40 / STD, Sch 80 <= 1-1/2\""),
    "B2": dict(rating=300, mat="5Cr-1/2Mo ASTM A335 P5", grp="1.13", ca=3.0,
               svc="Sulfidic hydrocarbon 260-400 C (hot crude, AR, BPA, HVGO, VR)", tmax=400,
               flange="A182 F5 RF", valves="Gate/globe A217 C5, trim 5 (stellite)",
               gasket="SPW 321/graphite (oxidation-inhibited), inner ring", bolting="A193 B7 / A194 4 (high temp)",
               branch="Sweepolet / reinforced, PWHT", sch="Sch 40 / STD, Sch 80 <= 1-1/2\""),
    "B3": dict(rating=300, mat="9Cr-1Mo ASTM A335 P9", grp="1.14", ca=3.0,
               svc="Heater outlets / transfer lines (H-101, H-201) and > 400 C", tmax=455,
               flange="A182 F9 RF", valves="Gate A217 C12, trim 5 (stellite); limit use",
               gasket="SPW 321/graphite (oxidation-inhibited)", bolting="A193 B16 / A194 4",
               branch="Forged tee / sweepolet, PWHT", sch="STD (0.375\") / per stress"),
    "C1": dict(rating=600, mat="Carbon steel, killed ASTM A106 Gr.B", grp="1.1", ca=3.0,
               svc="LPG / stabiliser, BFW > 300#", tmax=230, flange="A105 RTJ/RF", valves="Gate/globe A216 WCB, trim 8; ball fire-safe",
               gasket="SPW 316/graphite inner + outer ring", bolting="A193 B7 / A194 2H",
               branch="Weldolet / forged tee", sch="Sch 80 <= 2\", Sch 40 / XS >= 3\""),
    "A3": dict(rating=300, mat="Carbon steel, HIC-resistant (NACE MR0103), PWHT", grp="1.1", ca=6.0,
               svc="Wash water / brine / sour water above 150# rating (desalter pressure)", tmax=200,
               flange="A105N RF, HB <= 200", valves="Gate/globe A216 WCB NACE, trim 316/stellite",
               gasket="SPW 316L/graphite, inner + outer ring", bolting="A193 B7M / A194 2HM",
               branch="Weldolet / reinforced tee, PWHT", sch="Sch 80 <= 2\", Sch 40 / XS >= 3\""),
    "S1": dict(rating=150, mat="Carbon steel ASTM A106 Gr.B", grp="1.1", ca=1.5, svc="LP / MP steam, condensate",
               tmax=400, flange="A105 RF", valves="Gate/globe A216 WCB, trim 8", gasket="SPW 304/graphite",
               bolting="A193 B7 / A194 2H", branch="Weldolet / tee", sch="Sch 40 / STD"),
    "S2": dict(rating=600, mat="1.25Cr-1/2Mo ASTM A335 P11", grp="1.9", ca=1.5, svc="HP steam 41 barg / 400 C",
               tmax=450, flange="A182 F11 Cl.2 RF", valves="Gate/globe A217 WC6, trim 8", gasket="SPW 304/graphite",
               bolting="A193 B7 / A194 2H", branch="Weldolet, PWHT", sch="Sch 80"),
    "S3": dict(rating=300, mat="Carbon steel ASTM A106 Gr.B", grp="1.1", ca=1.5,
               svc="MP steam 10.3 barg / 250-290 C design (exceeds S1)", tmax=400, flange="A105 RF",
               valves="Gate/globe A216 WCB, trim 8 (stellite seats)", gasket="SPW 304/graphite, inner ring",
               bolting="A193 B7 / A194 2H", branch="Weldolet / tee", sch="Sch 40 / STD, Sch 80 <= 1-1/2\""),
    "F1": dict(rating=150, mat="Carbon steel, killed, impact-tested (A333 Gr.6)", grp="1.1", ca=3.0,
               svc="Flare / relief headers, -29 to 350 C", tmax=350, flange="A350 LF2 RF",
               valves="Gate A352 LCC (CSO/CSC per relief philosophy)", gasket="SPW 304/graphite, inner ring",
               bolting="A320 L7 / A194 4", branch="Lateral 45 deg into header top; reinforced",
               sch="STD, min. Sch 40 (acoustic fatigue check for large laterals)"),
    "U1": dict(rating=150, mat="Carbon steel (cement-lined for CW >= 12\")", grp="1.1", ca=1.5,
               svc="Cooling water, utility water, LP BFW", tmax=120, flange="A105 RF",
               valves="Butterfly (>= 6\"), gate (<= 4\")", gasket="Non-asbestos fibre", bolting="A193 B7 / A194 2H",
               branch="Tee / weldolet", sch="STD"),
    "U2": dict(rating=150, mat="SS304 (IA) / galvanised CS (N2)", grp="2.1", ca=0.0, svc="Instrument air, nitrogen",
               tmax=100, flange="A182 F304 RF / screwed <= 1-1/2\"", valves="Ball SS316", gasket="PTFE / SPW 304",
               bolting="A193 B8 / A194 8", branch="Tee", sch="Sch 10S / 40S"),
    "V1": dict(rating=150, mat="5Cr-1/2Mo ASTM A335 P5", grp="1.13", ca=3.0,
               svc="Vacuum vapour lines (C-201 OH); transfer line > 400 C -> B3", tmax=400, flange="A182 F5 RF",
               valves="Gate A217 C5 (vacuum service, bellows/stem purge)", gasket="SPW 321/graphite",
               bolting="A193 B7 / A194 4", branch="Reinforced, full vacuum design", sch="STD / per vacuum collapse"),
}


def rating(cls, T):
    c = CLASSES[cls]
    tab = RATINGS[(c["grp"], c["rating"])]
    if T <= _T[0]:
        return tab[0]
    for i in range(1, len(_T)):
        if T <= _T[i]:
            f = (T - _T[i - 1]) / (_T[i] - _T[i - 1])
            return tab[i - 1] + f * (tab[i] - tab[i - 1])
    return tab[-1]


# ----------------------------------------------------------------------------- property helpers
def rho_hc(rho_ref, T_ref, T):
    """Liquid hydrocarbon density at T from a reference point (slope -0.75 kg/m3/K, FEED estimate)."""
    return rho_ref - 0.75 * (T - T_ref)


def rho_w(T):
    return 1000.0 - 0.0035 * (T - 4) ** 2


def rho_gas(Pg, T, MW, Z=1.0):
    return (Pg + 1.013) * 1e5 * MW / (8314.0 * Z * (T + 273.15))


def rho_steam(Pg, T):
    return rho_gas(Pg, T, 18.015, Z=0.95 if Pg > 20 else 0.98)


def rho_mix(x_v, rho_l, rho_v):
    return 1.0 / ((1 - x_v) / rho_l + x_v / rho_v)


# latent heats (kJ/kg) of saturated steam at header pressures (steam tables)
HFG = {3.5: 2120.0, 10.3: 2000.0, 11.0: 1995.0, 41.4: 1690.0}
CP_W = 4.19


# ----------------------------------------------------------------------------- context
class Ctx:
    def __init__(self):
        rd = lambda n: json.loads((DATA / n).read_text())
        self.S = {s["no"]: s for s in rd("streams.json")}
        self.R = rd("process_results.json")
        self.E = {e["tag"]: e for e in rd("equipment.json")}
        self.PSV = {p["tag"]: p for p in rd("psv.json")}
        cl = rd("control_loops.json")
        self.LOOPS = {l["tag"]: l for l in cl["loops"]}
        self.SIFS = {s["tag"]: s for s in cl["sifs"]}
        self.U = basis.UTILITIES

    def eq(self, tag):
        if tag in self.E:
            return self.E[tag]
        return self.E[tag + "A/B"] if tag + "A/B" in self.E else self.E[tag]

    def desP(self, tag, side=0):
        v = self.eq(tag).get("des_P")
        if isinstance(v, (int, float)):
            return float(v)
        nums = [float(x) for x in re.findall(r"\d+\.?\d*", str(v))]
        return nums[min(side, len(nums) - 1)] if nums else 3.5

    def desT(self, tag):
        return float(self.eq(tag).get("des_T") or 0)

    def pump(self, tag):
        return self.eq(tag)

    def pump_desP(self, tag, suction_des):
        """Discharge design pressure = max suction (suction-vessel design P) + 1.2 x rated dP (shut-off)."""
        p = self.pump(tag)
        return math.ceil((suction_des + 1.2 * p["dP_bar"]) * 2) / 2

    def steam_rate(self, Q_kw, P, T_bfw=None):
        h = HFG.get(P, 2000.0)
        if T_bfw is not None:          # generator: sensible heating of BFW to saturation added
            Tsat = {3.5: 148, 10.3: 186, 11.0: 188}.get(P, 186)
            h += CP_W * (Tsat - T_bfw)
        return Q_kw / h * 3600.0

    def cw_rate(self, Q_kw):
        cw = self.U["cooling_water"]
        return Q_kw / (CP_W * (cw["return_C"] - cw["supply_C"])) * 3600.0


# ----------------------------------------------------------------------------- registry
SHORT_FLUID = {"P": "Process hydrocarbon", "PG": "Process gas / vapour", "SW": "Sour water", "WW": "Wash water / brine",
               "LS": "LP steam", "MS": "MP steam", "HS": "HP steam", "CD": "Condensate", "BFW": "Boiler feed water",
               "CWS": "Cooling water supply", "CWR": "Cooling water return", "FG": "Fuel gas", "FL": "Flare",
               "BD": "Blowdown / drain", "IA": "Instrument air", "N": "Nitrogen", "CH": "Chemical"}
UTIL_FLUIDS = {"LS", "MS", "HS", "CD", "BFW", "CWS", "CWR", "FG", "FL", "BD", "IA", "N", "CH"}


def select_class(fluid, kind, desP, desT, opT, hint=None):
    if hint:
        return hint
    if fluid in ("SW", "WW"):
        return "A2" if rating("A2", desT) >= desP else "A3"
    if fluid == "MS":
        return "S1" if rating("S1", desT) >= desP else "S3"
    if fluid in ("LS", "CD"):
        return "S1" if rating("S1", desT) >= desP else "S3"
    if fluid == "FL":
        return "F1"
    if fluid == "HS":
        return "S2"
    if fluid in ("CWS", "CWR"):
        return "U1"
    if fluid == "BFW":
        return "U1" if rating("U1", desT) >= desP and desT <= 120 else ("B1" if rating("B1", desT) >= desP else "C1")
    if fluid in ("IA", "N"):
        return "U2"
    if fluid in ("FG", "BD"):
        if opT > 260:
            return "B2"
        return "A1" if rating("A1", desT) >= desP else "B1"
    if kind in ("transfer", "vtransfer"):
        return "B3"
    if kind == "vacuum":
        return "V1" if desT <= 400 else "B3"
    # hydrocarbon (P / PG / CH)
    if opT > 400:
        return "B3"
    if opT > 260:
        return "B2"
    if desT <= 230 and rating("A1", desT) >= desP:
        return "A1"
    if rating("B1", desT) >= desP:
        return "B1"
    return "C1"


def select_insul(fluid, opT, kind, hint=None):
    if hint:
        return hint
    if fluid in ("CWS", "CWR", "IA", "N", "FL", "BD"):
        return "N"
    if fluid in ("LS", "MS", "HS", "BFW"):
        return "H"
    if fluid == "CD":
        return "P"
    if fluid in ("SW", "WW", "CH"):
        return "P" if opT >= 60 else "N"
    if opT >= 60:
        return "H"
    return "N"


class Registry:
    def __init__(self, ctx):
        self.c = ctx
        self.lines = {}
        self._seq = {}
        self.inst_ = {}
        self._free = {"1": 1200, "2": 2100, "9": 9100}
        self.issues = []

    # ------------------------------------------------------------------ lines
    def add(self, key, fluid, area, frm, to, svc, W, rho, P, T, kind, desP=None, desT=None, cls=None,
            insul=None, size=None, stream=None, phase=None, min_nps=None, note=""):
        if key in self.lines:
            raise KeyError(f"duplicate line key {key}")
        Q = W / rho if rho else 0.0
        if min_nps is None:
            min_nps = 1.0 if kind == "chem" or fluid in ("IA", "N", "CH") else 2.0
        if size is None:
            n, v = size_line(max(Q, 1e-6), vmax_for(kind, rho), min_nps)
        else:
            n = size
            v = Q / 3600 / (math.pi / 4 * pipe_id_m(n) ** 2)
        dP_ = desP if desP is not None else (design_P(P) if isinstance(design_P(P), (int, float)) else 3.5)
        dT_ = desT if desT is not None else design_T(T)
        c = select_class(fluid, kind, dP_, dT_, T, cls)
        ins = select_insul(fluid, T, kind, insul)
        self._seq[area] = self._seq.get(area, 0) + 1
        seq = self._seq[area]
        ln = f'{fmt_nps(n)}"-{fluid}-{area}-{seq:03d}-{c}-{ins}'
        if phase is None:
            phase = {"suction": "L", "gravity": "L", "liquid": "L", "water": "L", "cw": "L", "chem": "L",
                     "twophase": "M", "transfer": "M", "vtransfer": "M"}.get(kind, "V")
        if c in CLASSES and rating(c, dT_) < dP_ and P >= 0:
            self.issues.append(f"{ln}: design {dP_} barg @ {dT_} C exceeds class {c} rating "
                               f"{rating(c, dT_):.1f} barg")
        self.lines[key] = dict(key=key, line_no=ln, size_in=n, fluid=fluid, area=area, seq=seq, cls=c, insul=ins,
                               frm=frm, to=to, service=svc, phase=phase, design_P_barg=dP_, design_T_C=dT_,
                               op_P_barg=round(P, 2), op_T_C=round(T, 1), flow_kg_h=round(W, 0),
                               rho_kg_m3=round(rho, 3), velocity_m_s=round(v, 2), kind=kind, stream_no=stream,
                               sheets=[], util=fluid in UTIL_FLUIDS, note=note)
        return self.lines[key]

    def use_line(self, key, sid):
        ln = self.lines[key]
        if sid and sid not in ln["sheets"]:
            ln["sheets"].append(sid)
        return ln

    def no(self, key):
        return self.lines[key]["line_no"]

    # ------------------------------------------------------------------ instruments
    def free(self, area_digit):
        n = self._free[area_digit]
        used = {re.sub(r"[A-Z]$", "", t.split("-", 1)[1]) for t in self.inst_} | \
               {t.split("-", 1)[1] for t in self.c.LOOPS}
        while str(n) in used:
            n += 1
        self._free[area_digit] = n + 1
        return n

    def inst(self, tag, sid, kind="field", svc=None, fail=None, sif=None, line=None, rng=None, sys=None,
             sig=None, note=None, **kw):
        d = self.inst_.get(tag)
        if d is None:
            d = self.inst_[tag] = dict(tag=tag, sheets=[], kind=kind, svc=svc, fail=fail, sif=sif, line=line,
                                       rng=rng, sys=sys, sig=sig, note=note)
        else:
            for k, v in dict(svc=svc, fail=fail, sif=sif, line=line, rng=rng, sys=sys, sig=sig, note=note).items():
                if v is not None and d.get(k) is None:
                    d[k] = v
        if sid and sid not in d["sheets"]:
            d["sheets"].append(sid)
        return d


# ----------------------------------------------------------------------------- line topology table
def build_lines(reg: Registry):
    c = reg.c
    S, R, E = c.S, c.R, c.E
    U = c.U
    a, v, st, sp = R["atm"], R["vac"], R["stab"], R["split"]
    ph = {e["tag"]: e for e in R["preheat"]["exch"]}
    tr = {t["tag"]: t for t in R["preheat"]["trims"]}
    hs, ms, ls = U["hp_steam"], U["mp_steam"], U["lp_steam"]
    cw = U["cooling_water"]
    bfw = U["bfw"]
    fg = U["fuel_gas"]

    def L(key, fl, area, frm, to, svc, W, rho, P, T, kind, **kw):
        return reg.add(key, fl, area, frm, to, svc, W, rho, P, T, kind, **kw)

    s = lambda n: S[n]
    W = lambda n: S[n]["total_kg_h"]
    crude = W("1")
    rc30 = s("1")["rho_liq"]
    rc136 = s("5")["rho_liq"]
    rcr = lambda T: rc30 + (rc136 - rc30) * (T - 30) / (136.06 - 30) if T <= 140 else rho_hc(rc136, 136.06, T)
    p101, p102 = c.pump("P-101"), c.pump("P-102")
    P101d = s("1")["P_barg"] + p101["dP_bar"]
    des_p101 = c.desP("E-101")        # 30 barg crude side, = PSV-1010 set
    des_p102 = c.pump_desP("P-102", c.desP("D-101B"))
    # crude pressure profile, cold train: FV-1001 outlet -> stream 2 (desalter inlet)
    P2 = s("2")["P_barg"]
    Pcold = [P101d - 1.5 - i * (P101d - 1.5 - P2 - 1.0) / 5 for i in range(6)]
    P6 = s("6")["P_barg"]
    P102d = s("5")["P_barg"] + p102["dP_bar"]
    Phot = [P102d - 1.0 - i * (P102d - 1.0 - P6) / 6 for i in range(7)]

    # ===================== AREA 100 ===========================================================
    A = "100"
    # ---- sheet 001: crude charge & cold train
    L("crude_in", "P", A, "TK (OSBL)", "P-101A/B", "Crude from tankage to charge pumps", crude, rc30, s("1")["P_barg"],
      30, "suction", stream="1", desT=c.desT("P-101"))
    L("p101_d", "P", A, "P-101A/B", "E-101", "Crude charge pump discharge (FV-1001)", crude, rc30, P101d, 30,
      "liquid", desP=des_p101, desT=c.desT("P-101"))
    L("p101_mf", "P", A, "P-101A/B", "TK (OSBL)", "P-101 minimum-flow spillback (RO)", 0.3 * p101["flow_m3h"] * rc30,
      rc30, P101d, 30, "liquid", desP=des_p101, desT=c.desT("P-101"))
    L("p101_mf2", "P", A, "RO-P-101", "TK (OSBL)", "P-101 minimum flow, downstream RO", 0.3 * p101["flow_m3h"] * rc30,
      rc30, s("1")["P_barg"] + 1, 30, "liquid", desP=c.desP("P-101") if False else 10.0, desT=c.desT("P-101"), cls="A1")
    seq = ["E-101", "E-102", "E-103", "E-104", "E-105"]
    for i, t in enumerate(seq):
        To = ph[t]["Tc_out"]
        nxt = seq[i + 1] if i + 1 < len(seq) else "D-101A"
        key = f"crude_c{i + 1}"
        L(key, "P", A, t, nxt, f"Crude {t} outlet", crude, rcr(To), Pcold[i + 1], To, "liquid",
          desP=des_p101, stream="2" if t == "E-105" else None)
    L("crude_e105_byp", "P", A, "E-104", "E-105 outlet", "Crude bypass of E-105 (TV-1004)", 0.35 * crude,
      rcr(ph["E-104"]["Tc_out"]), Pcold[4], ph["E-104"]["Tc_out"], "liquid", desP=des_p101)
    L("ch_demul", "CH", A, "X-101", "P-101 suction", "Demulsifier injection", crude * 15e-6, 950, 6.0, 30, "chem",
      desP=10.0, cls="A1")
    psv = c.PSV["PSV-1010"]
    L("psv1010_out", "BD", A, "PSV-1010", "Closed drain", "PSV-1010 outlet (thermal / blocked)", psv["load_kg_h"],
      rc30, 0.5, 30, "liquid", desP=3.5, desT=60)
    # hot sides on 001
    tpa = a["pa"]["TPA"]
    rT = s("13")["rho_liq"]
    p106 = c.pump("P-106")
    dP106 = c.pump_desP("P-106", c.desP("C-101"))
    L("tpa_s", "P", A, "C-101 tray 3", "P-106A/B", "TPA draw to pumps", tpa["flow"], rT, a["P_top_barg"] + 0.3,
      tpa["T_draw"], "suction", desP=c.desP("C-101"), stream="13")
    L("tpa_d", "P", A, "P-106A/B", "E-101", "TPA pump discharge (FV-1040)", tpa["flow"], rT,
      a["P_top_barg"] + p106["dP_bar"], tpa["T_draw"], "liquid", desP=dP106)
    L("tpa_r", "P", A, "E-101", "C-101 tray 1", "TPA return to column", tpa["flow"], rho_hc(rT, tpa["T_draw"], tpa["T_ret"]),
      a["P_top_barg"] + 2.0, tpa["T_ret"], "liquid", desP=dP106, desT=design_T(tpa["T_draw"]))
    L("tpa_byp", "P", A, "P-106 disch.", "TPA return", "TPA bypass of E-101 (TV-1041)", 0.35 * tpa["flow"], rT,
      a["P_top_barg"] + 3.0, tpa["T_draw"], "liquid", desP=dP106)
    kero = W("16")
    p109 = c.pump("P-109")
    dP109 = c.pump_desP("P-109", c.desP("C-102"))
    L("kero_pd", "P", A, "P-109A/B", "E-102", "Kerosene product to E-102", kero, p109["rho"], 1.26 + p109["dP_bar"],
      a["T_strip_out"]["KERO"], "liquid", desP=dP109)
    L("kero_c1", "P", A, "E-102", "A-103", "Kerosene E-102 outlet to A-103", kero,
      rho_hc(p109["rho"], p109["T"], ph["E-102"]["Th_out"]), 1.26 + p109["dP_bar"] - 1.0, ph["E-102"]["Th_out"],
      "liquid", desP=dP109, desT=design_T(a["T_strip_out"]["KERO"]))
    lv = ph["E-103"]
    p201 = c.pump("P-201")
    dP201 = c.pump_desP("P-201", 3.5)
    L("lvgo_pd", "P", "200", "P-201A/B", "E-103", "LVGO PA + product to E-103", lv["hot_flow"], p201["rho"],
      p201["dP_bar"] - 0.5, lv["Th_in"], "liquid", desP=dP201)
    L("lvgo_c1", "P", "200", "E-103", "A-201", "LVGO E-103 outlet to A-201", lv["hot_flow"],
      rho_hc(p201["rho"], p201["T"], lv["Th_out"]), p201["dP_bar"] - 1.5, lv["Th_out"], "liquid", desP=dP201,
      desT=design_T(lv["Th_in"]))
    p110 = c.pump("P-110")
    dP110 = c.pump_desP("P-110", c.desP("C-103"))
    dsl = W("17")
    L("dsl_c1", "P", A, "E-107", "E-104", "Diesel E-107 outlet to E-104", dsl,
      rho_hc(p110["rho"], p110["T"], ph["E-104"]["Th_in"]), 1.36 + p110["dP_bar"] - 1.5, ph["E-104"]["Th_in"],
      "liquid", desP=dP110, desT=design_T(ph["E-107"]["Th_in"]))
    L("dsl_c2", "P", A, "E-104", "A-104", "Diesel E-104 outlet to A-104", dsl,
      rho_hc(p110["rho"], p110["T"], ph["E-104"]["Th_out"]), 1.36 + p110["dP_bar"] - 2.5, ph["E-104"]["Th_out"],
      "liquid", desP=dP110, desT=design_T(ph["E-107"]["Th_in"]))
    p204 = c.pump("P-204")
    dP204 = c.pump_desP("P-204", 3.5)
    vr = W("26")
    e201t = tr["E-201"]
    L("vr_c1", "P", "200", "E-111", "E-201", "Vacuum residue E-111 outlet to E-201", vr,
      rho_hc(p204["rho"], p204["T"], ph["E-111"]["Th_out"]), p204["dP_bar"] - 2.0, ph["E-111"]["Th_out"], "liquid",
      desP=dP204, insul="ST", desT=design_T(ph["E-111"]["Th_in"]))
    L("vr_c2", "P", "200", "E-201", "E-105", "Vacuum residue E-201 outlet to E-105", vr,
      rho_hc(p204["rho"], p204["T"], e201t["T_out"]), p204["dP_bar"] - 3.0, e201t["T_out"], "liquid",
      desP=dP204, insul="ST", desT=design_T(ph["E-111"]["Th_out"]))

    # ---- sheet 002: desalters
    L("crude_d12", "P", A, "D-101A", "D-101B", "1st-stage desalted crude to 2nd stage (PDV-1006)", crude, rc136,
      float(E["D-101A"]["op_P"]) + 0.3, R["preheat"]["T_desalter"], "liquid", desP=c.desP("D-101A"))
    L("crude_d2", "P", A, "D-101B", "P-102A/B", "Desalted crude to booster pumps (PV-1009)", W("5"), rc136,
      s("5")["P_barg"], s("5")["T_C"], "suction", desP=c.desP("D-101B"), stream="5")
    L("p102_d", "P", A, "P-102A/B", "E-106", "Desalted crude booster discharge", W("5"), rc136, P102d,
      s("5")["T_C"], "liquid", desP=des_p102, desT=c.desT("P-102"))
    L("p102_mf", "P", A, "P-102A/B", "D-101B outlet", "P-102 minimum-flow spillback (RO)",
      0.3 * p102["flow_m3h"] * rc136, rc136, P102d, s("5")["T_C"], "liquid", desP=des_p102, desT=c.desT("P-102"))
    L("ch_caustic", "CH", A, "X-102", "P-102 discharge", "Caustic injection (desalted crude)", W("5") * 10e-6, 1050,
      P102d + 2, 40, "chem", desP=des_p102, cls="B1")
    ww = W("3")
    p114 = c.pump("P-114")
    L("ww_s", "WW", A, "Stripped sour water (OSBL)", "P-114A/B", "Desalter wash water supply", ww, rho_w(50),
      3.0, 50, "suction", desP=7.0)
    L("ww_d", "WW", A, "P-114A/B", "E-118", "Wash water pump discharge", ww, rho_w(50), s("3")["P_barg"] + 1.0,
      50, "water", desP=c.desP("E-118"))
    L("ww_inj", "WW", A, "E-118", "D-101B mix valve", "Fresh wash water to 2nd stage (FV-1003)", ww,
      rho_w(s("3")["T_C"]), s("3")["P_barg"], s("3")["T_C"], "water", desP=c.desP("E-118"), stream="3")
    L("ww_recy", "WW", A, "D-101B", "D-101A mix valve", "2nd-stage effluent water to 1st stage wash (LV-1008)",
      ww, rho_w(136), float(E["D-101B"]["op_P"]), R["preheat"]["T_desalter"], "water", desP=c.desP("D-101B"))
    L("brine_1", "WW", A, "D-101A", "LV-1007", "1st-stage brine to level valve", W("4"), rho_w(136),
      float(E["D-101A"]["op_P"]), R["preheat"]["T_desalter"], "water", desP=c.desP("D-101A"))
    e118 = E["E-118"]
    L("brine_2", "WW", A, "LV-1007", "E-118", "Brine to wash water / brine exchanger", W("4"), rho_w(131),
      s("4")["P_barg"] + 1.0, e118["Th_in"], "water", desP=c.desP("E-118", 1))
    L("brine_3", "WW", A, "E-118", "WWT (OSBL)", "Desalter brine to WWT", W("4"), rho_w(s("4")["T_C"]),
      s("4")["P_barg"], s("4")["T_C"], "water", desP=c.desP("E-118", 1), stream="4")
    p118 = c.pump("P-118")
    L("mud_s", "WW", A, "D-101A/B bottoms", "P-118", "Mud-wash recycle pump suction", p118["flow_m3h"] * p118["rho"],
      p118["rho"], float(E["D-101A"]["op_P"]), p118["T"], "suction", desP=c.desP("D-101A"))
    L("mud_d", "WW", A, "P-118", "D-101A/B mud-wash headers", "Mud-wash header supply",
      p118["flow_m3h"] * p118["rho"], p118["rho"], float(E["D-101A"]["op_P"]) + p118["dP_bar"], p118["T"], "water",
      desP=c.pump_desP("P-118", c.desP("D-101A")))
    for t, k in (("PSV-1002", "psv1002_out"), ("PSV-1003", "psv1003_out")):
        p = c.PSV[t]
        L(k, "FL", A, t, "Flare header", f"{t} outlet ({p['case']})", p["load_kg_h"],
          rho_gas(0.5, p["T"], p["MW"]), 0.5, p["T"], "flare", desP=3.5, desT=design_T(p["T"]))

    # ---- sheet 003: hot train
    hot = ["E-106", "E-107", "E-108", "E-109", "E-110", "E-111"]
    for i, t in enumerate(hot):
        To = ph[t]["Tc_out"]
        nxt = hot[i + 1] if i + 1 < len(hot) else "H-101"
        if t == "E-111":
            x6 = s("6")["vf_mass"]
            r6 = rho_mix(x6, s("6")["rho_liq"], s("6")["rho_vap"])
            L("crude_h6", "P", A, "E-111", "H-101 inlet manifold", "Crude to H-101 (CIT)", W("6"), r6, P6, To,
              "liquid", desP=des_p102, stream="6", phase="M")
        else:
            L(f"crude_h{i + 1}", "P", A, t, nxt, f"Crude {t} outlet", W("5"), rho_hc(rc136, 136.06, To), Phot[i + 1],
              To, "liquid", desP=des_p102)
    mpa = a["pa"]["MPA"]
    rM = s("14")["rho_liq"]
    p107 = c.pump("P-107")
    dP107 = c.pump_desP("P-107", c.desP("C-101"))
    L("mpa_s", "P", A, "C-101 tray 13", "P-107A/B", "MPA draw to pumps", mpa["flow"], rM, a["P_top_barg"] + 0.4,
      mpa["T_draw"], "suction", desP=c.desP("C-101"), stream="14")
    L("mpa_d", "P", A, "P-107A/B", "E-106", "MPA pump discharge (FV-1042)", mpa["flow"], rM,
      a["P_top_barg"] + p107["dP_bar"], mpa["T_draw"], "liquid", desP=dP107)
    L("mpa_r", "P", A, "E-106", "C-101 tray 11", "MPA return to column", mpa["flow"], rho_hc(rM, mpa["T_draw"], mpa["T_ret"]),
      a["P_top_barg"] + 2.5, mpa["T_ret"], "liquid", desP=dP107, desT=design_T(mpa["T_draw"]))
    L("mpa_byp", "P", A, "MPA supply", "MPA return", "MPA bypass of E-106 (TV-1043)", 0.35 * mpa["flow"], rM,
      a["P_top_barg"] + 3.0, mpa["T_draw"], "liquid", desP=dP107)
    L("dsl_pd", "P", A, "P-110A/B", "E-107", "Diesel product to E-107", dsl, p110["rho"], 1.36 + p110["dP_bar"],
      a["T_strip_out"]["DIESEL"], "liquid", desP=dP110)
    hv = ph["E-108"]
    p202 = c.pump("P-202")
    dP202 = c.pump_desP("P-202", 3.5)
    L("hvgo_pd", "P", "200", "P-202A/B", "E-108", "HVGO PA + product to E-108", hv["hot_flow"], p202["rho"],
      p202["dP_bar"] - 0.5, hv["Th_in"], "liquid", desP=dP202)
    L("hvgo_c1", "P", "200", "E-108", "HVGO PA / product split", "HVGO E-108 outlet", hv["hot_flow"],
      rho_hc(p202["rho"], p202["T"], hv["Th_out"]), p202["dP_bar"] - 1.5, hv["Th_out"], "liquid", desP=dP202,
      desT=design_T(hv["Th_in"]))
    L("hvgo_byp", "P", "200", "HVGO supply", "E-108 outlet", "HVGO bypass of E-108 (TV-2017)", 0.35 * hv["hot_flow"],
      p202["rho"], p202["dP_bar"] - 1.0, hv["Th_in"], "liquid", desP=dP202)
    p111 = c.pump("P-111")
    dP111 = c.pump_desP("P-111", c.desP("C-104"))
    ago = W("18")
    L("ago_pd", "P", A, "P-111A/B", "E-109", "AGO product to E-109", ago, p111["rho"], 1.44 + p111["dP_bar"],
      a["T_strip_out"]["AGO"], "liquid", desP=dP111)
    L("ago_c1", "P", A, "E-109", "A-105", "AGO E-109 outlet to A-105", ago,
      rho_hc(p111["rho"], p111["T"], ph["E-109"]["Th_out"]), 1.44 + p111["dP_bar"] - 1.0, ph["E-109"]["Th_out"],
      "liquid", desP=dP111, desT=design_T(a["T_strip_out"]["AGO"]))
    bpa = a["pa"]["BPA"]
    rB = s("15")["rho_liq"]
    p108 = c.pump("P-108")
    dP108 = c.pump_desP("P-108", c.desP("C-101"))
    L("bpa_s", "P", A, "C-101 tray 25", "P-108A/B", "BPA draw to pumps", bpa["flow"], rB, a["P_top_barg"] + 0.5,
      bpa["T_draw"], "suction", desP=c.desP("C-101"), stream="15")
    L("bpa_d", "P", A, "P-108A/B", "E-110", "BPA pump discharge (FV-1044)", bpa["flow"], rB,
      a["P_top_barg"] + p108["dP_bar"], bpa["T_draw"], "liquid", desP=dP108)
    L("bpa_c1", "P", A, "E-110", "E-113", "BPA E-110 outlet to E-113", bpa["flow"],
      rho_hc(rB, bpa["T_draw"], ph["E-110"]["Th_out"]), a["P_top_barg"] + p108["dP_bar"] - 1.0,
      ph["E-110"]["Th_out"], "liquid", desP=dP108)
    L("bpa_r", "P", A, "E-113", "C-101 tray 23", "BPA return to column", bpa["flow"],
      rho_hc(rB, bpa["T_draw"], bpa["T_ret"]), a["P_top_barg"] + 2.5, bpa["T_ret"], "liquid", desP=dP108,
      desT=design_T(ph["E-110"]["Th_out"]))
    L("bpa_byp", "P", A, "E-110 outlet", "BPA return", "BPA bypass of E-113 (TV-1045)", 0.35 * bpa["flow"],
      rho_hc(rB, bpa["T_draw"], ph["E-110"]["Th_out"]), a["P_top_barg"] + 3.0, ph["E-110"]["Th_out"], "liquid",
      desP=dP108)
    L("vr_pd", "P", "200", "P-204A/B", "E-111", "Vacuum residue to E-111", vr, p204["rho"], p204["dP_bar"] - 0.5,
      p204["T"], "liquid", desP=dP204, insul="ST")
    e113 = tr["E-113"]
    W113 = c.steam_rate(e113["Q_kw"], ms["P_barg"], bfw["T_C"])
    L("bfw_e113", "BFW", A, "BFW header", "E-113", "BFW to E-113 (LV-1110)", W113 * 1.02, rho_w(bfw["T_C"]),
      bfw["P_barg"], bfw["T_C"], "water", desP=design_P(bfw["P_barg"]))
    L("ms_e113", "MS", A, "E-113", "MP steam header", "MP steam generated in E-113 (PV-1111)", W113,
      rho_steam(ms["P_barg"] + 0.7, 188), ms["P_barg"] + 0.7, 188, "steam", desP=c.desP("E-113"),
      desT=c.desT("E-113"))
    L("bd_e113", "BD", A, "E-113", "Blowdown drum (OSBL)", "E-113 continuous blowdown", W113 * 0.02, rho_w(186),
      ms["P_barg"], 186, "water", desP=c.desP("E-113"), desT=c.desT("E-113"), min_nps=1.0)

    p = c.PSV["PSV-1011"]
    L("psv1011_out", "MS", A, "PSV-1011", "Atmosphere (safe location)", "PSV-1011 discharge (E-113 steam side)",
      p["load_kg_h"], rho_steam(0.3, p["T"]), 0.3, p["T"], "flare", desP=3.5, desT=design_T(p["T"]))

    # ---- sheet 004: H-101 process coils
    H1 = R["heaters"]["H-101"]
    npass = H1["passes"]
    x6 = s("6")["vf_mass"]
    r6 = rho_mix(x6, s("6")["rho_liq"], s("6")["rho_vap"])
    x7 = s("7")["vf_mass"]
    r7 = rho_mix(x7, s("7")["rho_liq"], s("7")["rho_vap"])
    for i in range(1, npass + 1):
        L(f"h101_in{i}", "P", A, "H-101 inlet manifold", f"H-101 pass {i}", f"H-101 pass {i} inlet (FV-{1010 + i})",
          W("6") / npass, r6, P6 - 1.0, s("6")["T_C"], "liquid", desP=c.desP("H-101"), phase="M")
    for i in range(1, npass + 1):
        L(f"h101_out{i}", "P", A, f"H-101 pass {i}", "H-101 outlet manifold", f"H-101 pass {i} outlet",
          W("7") / npass, r7, s("7")["P_barg"], s("7")["T_C"], "transfer", desP=design_P(P6), desT=c.desT("H-101"))
    # transfer line sized at flash-zone conditions (vapour expands as pressure falls)
    rv_fz = s("7")["rho_vap"] * (a["P_fz_barg"] + 1.013) / (s("7")["P_barg"] + 1.013)
    L("transfer", "P", A, "H-101 outlet manifold", "C-101 flash zone", "Atmospheric transfer line", W("7"),
      rho_mix(x7, s("7")["rho_liq"], rv_fz), s("7")["P_barg"], s("7")["T_C"], "transfer", desP=design_P(P6),
      desT=c.desT("H-101"), stream="7")
    st_tot = W("20")
    L("ls_ss_in", "LS", A, "LP steam header", "H-101 SS coil", "LP steam to stripping-steam superheat coil", st_tot,
      rho_steam(ls["P_barg"], ls["T_C"]), ls["P_barg"], ls["T_C"], "steam", desP=design_P(ls["P_barg"]) + 1)
    L("ls_ss_out", "LS", A, "H-101 SS coil", "Stripping steam header", "Superheated stripping steam (TIC-1024)", st_tot,
      rho_steam(s("20")["P_barg"], s("20")["T_C"]), s("20")["P_barg"], s("20")["T_C"], "steam", stream="20",
      desP=design_P(ls["P_barg"]) + 1, desT=design_T(s("20")["T_C"]))
    L("bfw_desup", "BFW", A, "BFW header", "SS desuperheater", "BFW to desuperheater (TV-1024)", st_tot * 0.03,
      rho_w(bfw["T_C"]), bfw["P_barg"], bfw["T_C"], "water", desP=design_P(bfw["P_barg"]), min_nps=1.0)

    # ---- sheet 005: H-101 firing
    fgW = H1["fuel_kg_h"]
    rfg = s("34")["rho_vap"]
    L("fg_h101", "FG", A, "FG header (D-103)", "H-101 burners", "Fuel gas to H-101 (XV-1021/1022, PV-1021)", fgW,
      rfg, fg["P_barg"], 30, "fg", desP=c.desP("D-103"), desT=design_T(60))
    L("fg_h101_b", "FG", A, "PV-1021", "H-101 burner manifolds", "H-101 main burner gas manifold", fgW,
      rho_gas(1.5, 30, fg["MW"]), 1.5, 30, "fg", desP=c.desP("D-103"), desT=design_T(60))
    L("fg_h101_pil", "FG", A, "FG header (D-103)", "H-101 pilots", "H-101 pilot gas (XV-1026)", fgW * 0.03, rfg,
      fg["P_barg"], 30, "fg", desP=c.desP("D-103"), desT=design_T(60), min_nps=1.0)
    L("fl_h101_vent", "FL", A, "H-101 FG DBB", "Flare header", "H-101 fuel-gas double block & bleed vent",
      fgW * 0.1, rho_gas(0.5, 30, fg["MW"]), 0.5, 30, "flare", desP=3.5, desT=design_T(60), min_nps=1.0)
    snuff = 9.0 * H1["firebox_m3"]            # API 560: ~9 kg/h steam per m3 firebox volume
    L("ls_snuff_h101", "LS", A, "LP steam header", "H-101 firebox / header boxes", "H-101 snuffing steam",
      snuff, rho_steam(ls["P_barg"], ls["T_C"]), ls["P_barg"], ls["T_C"], "steam", desP=design_P(ls["P_barg"]) + 1)

    # ---- sheet 006: C-101 bottom
    ar = W("19")
    p112 = c.pump("P-112")
    dP112 = c.pump_desP("P-112", c.desP("C-101"))
    L("ar_s", "P", A, "C-101 bottom", "P-112A/B", "Atmospheric residue to P-112 (EIV-1121)", ar, s("19")["rho_liq"],
      a["P_fz_barg"] + 0.2, a["T_bot"], "suction", desP=c.desP("C-101"), desT=c.desT("C-101"))
    L("ar_d", "P", A, "P-112A/B", "H-201 inlet manifold", "Atmospheric residue to H-201 (FV-1083, XV-1083)", ar,
      s("19")["rho_liq"], s("19")["P_barg"], s("19")["T_C"], "liquid", desP=dP112, stream="19", desT=c.desT("P-112"))
    L("p112_mf", "P", A, "P-112A/B", "C-101 bottom", "P-112 minimum-flow spillback (RO)", 0.3 * p112["flow_m3h"] *
      p112["rho"], p112["rho"], s("19")["P_barg"], a["T_bot"], "liquid", desP=dP112, desT=c.desT("P-112"))
    stm = a["steam"]
    rss = rho_steam(s("20")["P_barg"], s("20")["T_C"])
    L("ls_c101", "LS", A, "Stripping steam header", "C-101 below tray 41", "C-101 bottom stripping steam (FV-1081)",
      stm["bottom"], rss, s("20")["P_barg"], s("20")["T_C"], "steam", desP=design_P(ls["P_barg"]) + 1,
      desT=design_T(s("20")["T_C"]))
    L("ls_ss_hdr", "LS", A, "Stripping steam header", "C-102/103/104", "Stripping steam to side strippers",
      stm["KERO"] + stm["DIESEL"] + stm["AGO"], rss, s("20")["P_barg"], s("20")["T_C"], "steam",
      desP=design_P(ls["P_barg"]) + 1, desT=design_T(s("20")["T_C"]))
    ago_draw = ago * basis.DESIGN_MARGIN + stm["AGO"]
    L("ago_draw", "P", A, "C-101 tray 32", "C-104", "AGO draw to stripper (FV-1070)", ago_draw,
      rho_hc(p111["rho"], p111["T"], a["T_draw"]["AGO"]), a["P_fz_barg"], a["T_draw"]["AGO"], "gravity",
      desP=c.desP("C-101"))
    ovf = basis.DESIGN["atm_overflash_lv"] * R["crude"]["m3h"] * s("18")["rho_liq"]
    L("ovfl", "P", A, "C-101 tray 35 pan", "C-101 flash zone", "Overflash (wash-zone liquid) to flash zone (FI-1080)",
      ovf, rho_hc(s("18")["rho_liq"], 60, a["T_fz"]), a["P_fz_barg"], a["T_fz"] - 3, "gravity", desP=c.desP("C-101"),
      desT=c.desT("C-101"))
    L("bd_c101", "BD", A, "C-101 bottom", "Closed drain", "C-101 bottom drain (pump-out to slops)", 20000,
      s("19")["rho_liq"], a["P_fz_barg"], a["T_bot"], "liquid", desP=c.desP("C-101"), desT=c.desT("C-101"), size=4)

    # ---- sheet 007: C-101 upper + PAs (draws)
    kero_draw = kero * basis.DESIGN_MARGIN + stm["KERO"]
    dsl_draw = dsl * basis.DESIGN_MARGIN + stm["DIESEL"]
    L("kero_draw", "P", A, "C-101 tray 10", "C-102", "Kerosene draw to stripper (FV-1050)", kero_draw,
      rho_hc(p109["rho"], p109["T"], a["T_draw"]["KERO"]), a["P_top_barg"] + 0.1, a["T_draw"]["KERO"], "gravity",
      desP=c.desP("C-101"))
    L("dsl_draw", "P", A, "C-101 tray 22", "C-103", "Diesel draw to stripper (FV-1060)", dsl_draw,
      rho_hc(p110["rho"], p110["T"], a["T_draw"]["DIESEL"]), a["P_top_barg"] + 0.2, a["T_draw"]["DIESEL"],
      "gravity", desP=c.desP("C-101"))
    for k, p, tray, P_ in (("kero", "KERO", 9, 1.26), ("dsl", "DIESEL", 21, 1.36), ("ago", "AGO", 31, 1.44)):
        Wv = stm[p] + 0.1 * W({"KERO": "16", "DIESEL": "17", "AGO": "18"}[p])
        mw = 1 / ((stm[p] / 18.0 + 0.1 * W({"KERO": "16", "DIESEL": "17", "AGO": "18"}[p]) /
                   {"KERO": 158.5, "DIESEL": 216.2, "AGO": 280.7}[p]) / Wv)
        tag = {"KERO": "C-102", "DIESEL": "C-103", "AGO": "C-104"}[p]
        L(f"{k}_vret", "PG", A, tag, f"C-101 tray {tray}", f"{tag} overhead vapour return to C-101", Wv,
          rho_gas(P_, a["T_draw"][p], mw), P_, a["T_draw"][p], "vapour", desP=c.desP(tag), desT=c.desT(tag))

    # ---- sheet 008: side strippers
    for k, p, tag, pump_, strm in (("kero", "KERO", "C-102", "P-109", "16"), ("dsl", "DIESEL", "C-103", "P-110", "17"),
                                   ("ago", "AGO", "C-104", "P-111", "18")):
        pp = c.pump(pump_)
        L(f"{k}_ps", "P", A, f"{tag} bottom", f"{pump_}A/B", f"{tag} bottoms to product pumps", W(strm), pp["rho"],
          float(E[tag]["op_P"]) + 0.3, a["T_strip_out"][p], "suction", desP=c.desP(tag), desT=c.desT(tag))
        L(f"ls_{tag[2:].lower().replace('-', '')}", "LS", A, "Stripping steam header", tag,
          f"{tag} stripping steam (FIC-{ {'C-102': 1054, 'C-103': 1064, 'C-104': 1074}[tag]})", stm[p], rss,
          s("20")["P_barg"], s("20")["T_C"], "steam", desP=design_P(ls["P_barg"]) + 1,
          desT=design_T(s("20")["T_C"]))
    L("kero_rd", "P", A, "A-103", "Storage / KHT (OSBL)", "Kerosene product rundown (FV-1052)", kero,
      s("16")["rho_liq"], s("16")["P_barg"], s("16")["T_C"], "liquid", desP=dP109, desT=c.desT("A-103"), stream="16")
    L("dsl_rd", "P", A, "A-104", "Storage / DHT (OSBL)", "Diesel product rundown (FV-1062)", dsl, s("17")["rho_liq"],
      s("17")["P_barg"], s("17")["T_C"], "liquid", desP=dP110, desT=c.desT("A-104"), stream="17")
    L("ago_rd", "P", A, "A-105", "DHT / FCC (OSBL)", "AGO product rundown (FV-1072)", ago, s("18")["rho_liq"],
      s("18")["P_barg"], s("18")["T_C"], "liquid", desP=dP111, desT=c.desT("A-105"), stream="18", insul="ST")
    p = c.PSV["PSV-1009"]
    L("psv1009_out", "FL", A, "PSV-1009", "Flare header", "PSV-1009 outlet (side strippers fire)", p["load_kg_h"],
      rho_gas(0.5, p["T"], p["MW"]), 0.5, p["T"], "flare", desP=3.5, desT=design_T(p["T"]))

    # ---- sheet 009: overhead
    r8 = s("8")["rho_vap"]
    L("oh_vap", "PG", A, "C-101 top", "A-101", "C-101 overhead vapour", W("8"), r8, s("8")["P_barg"], s("8")["T_C"],
      "vapour", desP=c.desP("C-101"), desT=c.desT("A-101"), stream="8", cls="A2", insul="H")
    xv = 1 - 0.85                                  # A-101 removes 85 % of condenser duty (sizing basis)
    L("a101_out", "PG", A, "A-101", "E-115", "A-101 outlet (partially condensed)", W("8"),
      rho_mix(xv, s("10")["rho_liq"], r8 * (s("8")["T_C"] + 273.15) / (60 + 273.15)), s("8")["P_barg"] - 0.3, 60,
      "twophase", desP=c.desP("A-101"), desT=c.desT("A-101"), cls="A2", insul="N")
    L("e115_out", "P", A, "E-115", "D-102", "E-115 outlet to reflux drum", W("8"), s("10")["rho_liq"],
      a["drum_P_barg"] + 0.1, basis.DESIGN["atm_drum_T"], "gravity", desP=c.desP("E-115"), desT=c.desT("E-115"),
      cls="A2", phase="M")
    p103, p104, p105 = c.pump("P-103"), c.pump("P-104"), c.pump("P-105")
    L("refl_s", "P", A, "D-102", "P-103A/B", "Reflux pump suction", W("10"), s("10")["rho_liq"], a["drum_P_barg"],
      basis.DESIGN["atm_drum_T"], "suction", desP=c.desP("D-102"), cls="A2")
    L("reflux", "P", A, "P-103A/B", "C-101 tray 1", "Reflux to C-101 (FV-1031)", W("10"), s("10")["rho_liq"],
      s("10")["P_barg"], s("10")["T_C"], "liquid", desP=c.pump_desP("P-103", c.desP("D-102")), stream="10")
    L("naph_s", "P", A, "D-102", "P-104A/B", "Unstabilised naphtha pump suction", W("11"), s("11")["rho_liq"],
      a["drum_P_barg"], basis.DESIGN["atm_drum_T"], "suction", desP=c.desP("D-102"), cls="A2")
    L("naph_d", "P", A, "P-104A/B", "E-114", "Unstabilised naphtha to C-105 (FV-1034)", W("11"),
      s("11")["rho_liq"], s("11")["P_barg"], s("11")["T_C"], "liquid",
      desP=c.pump_desP("P-104", c.desP("D-102")), stream="11")
    L("sw_s", "SW", A, "D-102 boot", "P-105A/B", "OH sour water pump suction", W("12"), rho_w(45), a["drum_P_barg"],
      45, "suction", desP=c.desP("D-102"))
    L("sw_d", "SW", A, "P-105A/B", "SWS (OSBL)", "OH sour water to SWS (LV-1035)", W("12"), rho_w(45),
      s("12")["P_barg"], 45, "water", desP=c.pump_desP("P-105", c.desP("D-102")), stream="12")
    og = 0.01 * W("8")                                # upset allowance, normally no flow
    L("d102_og", "PG", A, "D-102", "FG recovery / flare (OSBL)", "D-102 off-gas (PV-1032A), normally no flow", og,
      rho_gas(a["drum_P_barg"], 45, 40), a["drum_P_barg"], 45, "vapour", desP=c.desP("D-102"), stream="9", cls="A2")
    L("fg_d102", "FG", A, "FG header", "D-102", "Fuel-gas make-up / blanketing (PV-1032B)", og * 0.3,
      rfg, fg["P_barg"], 30, "fg", desP=c.desP("D-103"), min_nps=1.0)
    for k, n_ in (("ch_neut", "Neutraliser"), ("ch_film", "Filming amine")):
        L(k, "CH", A, "X-103", "C-101 OH vapour line", f"{n_} injection (X-103)", W("8") * 10e-6, 1000,
          s("8")["P_barg"] + 3, 40, "chem", desP=10.0, cls="A2")
    for t in ("PSV-1001", "PSV-1004"):
        p = c.PSV[t]
        L(f"{t[4:].replace('-', '').lower()}_out", "FL", A, t, "Flare header", f"{t} outlet ({p['case']})",
          p["load_kg_h"], rho_gas(0.5, p["T"], p["MW"]), 0.5, p["T"], "flare", desP=3.5, desT=design_T(p["T"]))

    # ---- sheet 010: stabiliser
    P105 = st["P_top"] - 1.013
    L("stab_feed", "P", A, "E-114", "C-105 tray 13", "Stabiliser feed (preheated)", W("11"),
      rho_hc(s("11")["rho_liq"], 45, st["T_feed"]), s("11")["P_barg"] - 1.0, st["T_feed"], "liquid",
      desP=c.desP("E-114"), cls="C1")
    Wov = st["reflux"] + W("30")
    rov = rho_gas(P105, st["T_top"], s("30")["mw"])
    L("c105_ov", "PG", A, "C-105 top", "A-106", "Stabiliser overhead vapour", Wov, rov, P105, st["T_top"], "vapour",
      desP=c.desP("C-105"), desT=c.desT("C-105"), cls="C1")
    L("c105_hvb", "PG", A, "C-105 overhead", "D-105", "Hot-vapour bypass (PV-1091)", 0.15 * Wov, rov, P105,
      st["T_top"], "vapour", desP=c.desP("C-105"), desT=c.desT("C-105"), cls="C1")
    L("a106_out", "P", A, "A-106", "D-105", "A-106 outlet (condensed LPG)", Wov * 0.85, s("30")["rho_liq"],
      P105 - 0.3, basis.DESIGN["stab_drum_T"], "gravity", desP=c.desP("A-106"), desT=c.desT("A-106"), cls="C1")
    p115 = c.pump("P-115")
    dP115 = c.pump_desP("P-115", c.desP("D-105"))
    L("lpg_s", "P", A, "D-105", "P-115A/B", "Stabiliser reflux / LPG pump suction", Wov, s("30")["rho_liq"],
      basis.DESIGN["stab_drum_P"] - 1.013, basis.DESIGN["stab_drum_T"], "suction", desP=c.desP("D-105"), cls="C1")
    L("stab_refl", "P", A, "P-115A/B", "C-105 tray 1", "Stabiliser reflux (FV-1094)", st["reflux"],
      s("30")["rho_liq"], P105 + 4, basis.DESIGN["stab_drum_T"], "liquid", desP=dP115, cls="C1")
    L("lpg_prod", "P", A, "P-115A/B", "LPG treating (OSBL)", "LPG product (FV-1093, XV-1093)", W("30"), s("30")["rho_liq"],
      s("30")["P_barg"], s("30")["T_C"], "liquid", desP=dP115, cls="C1", stream="30")
    L("d105_og", "PG", A, "D-105", "Fuel gas (OSBL)", "Stabiliser off-gas, normally no flow", 0.02 * Wov,
      rho_gas(P105 - 0.3, 45, 30), P105 - 0.3, 45, "vapour", desP=c.desP("D-105"), cls="C1", stream="29", min_nps=2)
    L("d105_sw", "SW", A, "D-105 boot", "Sour water (OSBL)", "D-105 boot water (intermittent)", 200, rho_w(45),
      P105 - 0.3, 45, "water", desP=c.desP("D-105"), cls="C1", min_nps=1.0)
    rb = s("31")["rho_liq"]
    L("c105_reb_l", "P", A, "C-105 bottom", "E-116", "Stabiliser bottoms to kettle reboiler", W("31") * 1.6, rb,
      st["P_bot"] - 1.013, st["T_bot"] - 10, "suction", desP=c.desP("C-105"), desT=c.desT("E-116"), cls="C1")
    Wreb = st["Q_reb"] * 3600 / 300.0
    L("c105_reb_v", "PG", A, "E-116", "C-105 below tray 19", "Kettle reboiler vapour return", Wreb,
      rho_gas(st["P_bot"] - 1.013, st["T_bot"], s("31")["mw"]), st["P_bot"] - 1.013, st["T_bot"], "vapour",
      desP=c.desP("C-105"), desT=c.desT("E-116"), cls="C1")
    L("stab_btm", "P", A, "E-116", "E-114", "Stabilised naphtha to E-114", W("31"), rb, s("31")["P_barg"],
      s("31")["T_C"], "liquid", desP=c.desP("C-105"), desT=c.desT("E-116"), stream="31", cls="C1")
    L("stab_btm2", "P", A, "E-114", "C-106 tray 21", "Stabilised naphtha to splitter (LV-1097)", W("31"),
      rho_hc(rb, s("31")["T_C"], sp["T_feed"]), s("31")["P_barg"] - 1.0, sp["T_feed"], "liquid",
      desP=c.desP("C-105"), desT=c.desT("E-114"), cls="C1")
    Whs = c.steam_rate(st["Q_reb"], hs["P_barg"])
    L("hs_e116", "HS", A, "HP steam header", "E-116", "HP steam to stabiliser reboiler (FV-1096, XV-1096)", Whs,
      rho_steam(hs["P_barg"], hs["T_C"]), hs["P_barg"], hs["T_C"], "steam", desP=c.desP("E-116", 1) + 1.0,
      desT=design_T(hs["T_C"]))
    L("hc_e116", "CD", A, "E-116", "LV-1098", "HP condensate to condensate pot", Whs, rho_w(253), hs["P_barg"] - 1,
      253, "gravity", desP=c.desP("E-116", 1), desT=c.desT("E-116"), cls="S2")
    L("cd_e116", "CD", A, "LV-1098", "Condensate header", "Condensate from E-116 pot (LV-1098)", Whs,
      rho_mix(0.15, rho_w(150), rho_steam(3.5, 150)), 3.5, 150, "twophase", desP=design_P(5.0), desT=design_T(150))
    for t in ("PSV-1005", "PSV-1006", "PSV-1008"):
        p = c.PSV[t]
        L(f"{t[4:].replace('-', '').lower()}_out", "FL", A, t, "Flare header", f"{t} outlet ({p['case']})",
          p["load_kg_h"], rho_gas(0.5, p["T"], p["MW"]), 0.5, p["T"], "flare", desP=3.5, desT=design_T(p["T"]))

    # ---- sheet 011: splitter
    P106 = sp["P_top"] - 1.013
    Wov6 = sp["reflux"] + W("32")
    rov6 = rho_gas(P106, sp["T_top"], s("32")["mw"])
    L("c106_ov", "PG", A, "C-106 top", "A-107", "Splitter overhead vapour", Wov6, rov6, P106, sp["T_top"], "vapour",
      desP=c.desP("C-106"), desT=c.desT("C-106"))
    L("a107_out", "P", A, "A-107", "D-106", "Splitter condensate (PV-1100 flooded condenser)", Wov6, s("32")["rho_liq"],
      P106 - 0.2, basis.DESIGN["split_drum_T"], "gravity", desP=c.desP("A-107"), desT=c.desT("A-107"))
    L("c106_eq", "PG", A, "C-106 overhead", "D-106", "D-106 pressure balance line", 0.05 * Wov6, rov6, P106,
      sp["T_top"], "vapour", desP=c.desP("C-106"), desT=c.desT("C-106"))
    p116, p117 = c.pump("P-116"), c.pump("P-117")
    dP116 = c.pump_desP("P-116", c.desP("D-106"))
    L("ln_s", "P", A, "D-106", "P-116A/B", "Splitter reflux / LN pump suction", Wov6, s("32")["rho_liq"],
      basis.DESIGN["split_drum_P"] - 1.013, basis.DESIGN["split_drum_T"], "suction", desP=c.desP("D-106"))
    L("split_refl", "P", A, "P-116A/B", "C-106 tray 1", "Splitter reflux (FV-1103)", sp["reflux"], s("32")["rho_liq"],
      P106 + 4, basis.DESIGN["split_drum_T"], "liquid", desP=dP116)
    L("ln_prod", "P", A, "P-116A/B", "Isomerisation (OSBL)", "Light naphtha product (FV-1102)", W("32"),
      s("32")["rho_liq"], s("32")["P_barg"], s("32")["T_C"], "liquid", desP=dP116, stream="32")
    rhn = rho_hc(s("33")["rho_liq"], 45, sp["T_bot"])
    L("c106_reb_l", "P", A, "C-106 bottom", "E-117", "Splitter thermosyphon reboiler feed", W("33") * 3, rhn,
      sp["P_bot"] - 1.013, sp["T_bot"] - 8, "gravity", desP=c.desP("C-106"), desT=c.desT("E-117"))
    Wreb6 = sp["Q_reb"] * 3600 / 320.0
    L("c106_reb_r", "P", A, "E-117", "C-106 below tray 38", "Thermosyphon reboiler return (two-phase)", W("33") * 3,
      rho_mix(Wreb6 / (W("33") * 3), rhn, rho_gas(sp["P_bot"] - 1.013, sp["T_bot"], s("33")["mw"])),
      sp["P_bot"] - 1.013, sp["T_bot"], "twophase", desP=c.desP("C-106"), desT=c.desT("E-117"))
    L("hn_s", "P", A, "C-106 bottom", "P-117A/B", "Heavy naphtha pump suction", W("33"), rhn, sp["P_bot"] - 1.013,
      sp["T_bot"], "suction", desP=c.desP("C-106"), desT=c.desT("C-106"))
    L("hn_d", "P", A, "P-117A/B", "A-108", "Heavy naphtha to A-108", W("33"), rhn, sp["P_bot"] - 1.013 + p117["dP_bar"],
      sp["T_bot"], "liquid", desP=c.pump_desP("P-117", c.desP("C-106")), desT=c.desT("P-117"))
    L("hn_prod", "P", A, "A-108", "NHT / reformer (OSBL)", "Heavy naphtha product (FV-1107)", W("33"),
      s("33")["rho_liq"], s("33")["P_barg"], s("33")["T_C"], "liquid", desP=c.pump_desP("P-117", c.desP("C-106")),
      desT=c.desT("A-108"), stream="33")
    Wms = c.steam_rate(sp["Q_reb"], ms["P_barg"])
    L("ms_e117", "MS", A, "MP steam header", "E-117", "MP steam to splitter reboiler (FV-1105)", Wms,
      rho_steam(ms["P_barg"], ms["T_C"]), ms["P_barg"], ms["T_C"], "steam", desP=c.desP("E-117", 1),
      desT=design_T(ms["T_C"]))
    L("cd_e117", "CD", A, "E-117", "Condensate header", "MP condensate from E-117 (steam trap / pot)", Wms,
      rho_mix(0.1, rho_w(150), rho_steam(3.5, 150)), 3.5, 150, "twophase", desP=c.desP("E-117", 1),
      desT=design_T(186))
    p = c.PSV["PSV-1007"]
    L("1007_out", "FL", A, "PSV-1007", "Flare header", f"PSV-1007 outlet ({p['case']})", p["load_kg_h"],
      rho_gas(0.5, p["T"], p["MW"]), 0.5, p["T"], "flare", desP=3.5, desT=design_T(p["T"]))

    # ===================== AREA 200 ===========================================================
    A = "200"
    H2 = R["heaters"]["H-201"]
    n2 = H2["passes"]
    for i in range(1, n2 + 1):
        L(f"h201_in{i}", "P", A, "H-201 inlet manifold", f"H-201 pass {i}", f"H-201 pass {i} inlet (FV-{2000 + i})",
          ar / n2, s("19")["rho_liq"], s("19")["P_barg"] - 2.0, s("19")["T_C"], "liquid", desP=dP112,
          desT=c.desT("H-201"))
    x21 = s("21")["vf_mass"]
    r21 = rho_mix(x21, s("21")["rho_liq"], s("21")["rho_vap"])
    for i in range(1, n2 + 1):
        L(f"h201_out{i}", "P", A, f"H-201 pass {i}", "H-201 outlet manifold", f"H-201 pass {i} outlet",
          W("21") / n2, r21, s("21")["P_barg"], s("21")["T_C"], "vtransfer", desP=3.5, desT=c.desT("H-201"))
    rv_vfz = s("21")["rho_vap"] * (v["P_fz_mbar"] / 1000) / (s("21")["P_barg"] + 1.013)
    L("vac_transfer", "P", A, "H-201 outlet manifold", "C-201 flash zone", "Vacuum transfer line", W("21"),
      rho_mix(x21, s("21")["rho_liq"], rv_vfz), s("21")["P_barg"], s("21")["T_C"], "vtransfer", desP=3.5,
      desT=c.desT("H-201"), stream="21", note="Sized at flash-zone pressure; FV design")
    coil = W("21") - W("19")
    L("ms_coil", "MS", A, "MP steam header", "H-201 passes", "H-201 coil (velocity) steam (FV-2007)", max(coil, 1.0),
      rho_steam(ms["P_barg"], ms["T_C"]), ms["P_barg"], ms["T_C"], "steam", desP=design_P(ms["P_barg"]),
      desT=design_T(ms["T_C"]), min_nps=1.5)
    fg2 = H2["fuel_kg_h"]
    L("fg_h201", "FG", A, "FG header (D-103)", "H-201 burners", "Fuel gas to H-201 (XV-2006A/B, PV-2006)", fg2, rfg,
      fg["P_barg"], 30, "fg", desP=c.desP("D-103"), desT=design_T(60))
    L("fg_h201_pil", "FG", A, "FG header (D-103)", "H-201 pilots", "H-201 pilot gas", fg2 * 0.04, rfg, fg["P_barg"],
      30, "fg", desP=c.desP("D-103"), desT=design_T(60), min_nps=1.0)
    L("fl_h201_vent", "FL", A, "H-201 FG DBB", "Flare header", "H-201 fuel-gas double block & bleed vent", fg2 * 0.1,
      rho_gas(0.5, 30, fg["MW"]), 0.5, 30, "flare", desP=3.5, desT=design_T(60), min_nps=1.0)
    L("ls_snuff_h201", "LS", A, "LP steam header", "H-201 firebox", "H-201 snuffing steam", 9.0 * H2["firebox_m3"],
      rho_steam(ls["P_barg"], ls["T_C"]), ls["P_barg"], ls["T_C"], "steam", desP=design_P(ls["P_barg"]) + 1)
    L("vog", "PG", A, "D-202", "H-201 off-gas burners", "Vacuum off-gas to H-201 (PV-2031)", W("28"),
      s("28")["rho_vap"], s("28")["P_barg"], s("28")["T_C"], "fg", desP=c.desP("D-202"), desT=c.desT("D-202"),
      stream="28", cls="A2")

    # ---- sheet 013: C-201
    L("vac_ov", "PG", A, "C-201 top", "J-201A/B", "Vacuum column overhead to 1st-stage ejectors", W("22"),
      s("22")["rho_vap"], s("22")["P_barg"], s("22")["T_C"], "vacuum", desP=3.5, desT=design_T(150), stream="22",
      insul="H")
    lv_pa = v["pa"]["LVGO"]
    hv_pa = v["pa"]["HVGO"]
    L("lvgo_s", "P", A, "C-201 LVGO pan", "P-201A/B", "LVGO draw to pumps", lv["hot_flow"], p201["rho"], -0.95,
      v["T_lvgo"], "suction", desP=3.5, desT=c.desT("P-201"))
    L("lvgo_ret", "P", A, "LVGO split", "C-201 top spray", "LVGO pumparound return (FV-2011)", lv_pa["flow"],
      s("23")["rho_liq"], p201["dP_bar"] - 3.0, lv_pa["T_ret"], "liquid", desP=dP201, desT=design_T(lv["Th_in"]))
    L("hvgo_s", "P", A, "C-201 HVGO pan", "P-202A/B", "HVGO draw to pumps", hv["hot_flow"], p202["rho"], -0.95,
      v["T_hvgo"], "suction", desP=3.5, desT=c.desT("P-202"))
    L("hvgo_ret", "P", A, "HVGO split", "C-201 bed 3 distributor", "HVGO pumparound return (FV-2016)", hv_pa["flow"],
      rho_hc(p202["rho"], p202["T"], hv_pa["T_ret"]), p202["dP_bar"] - 3.0, hv_pa["T_ret"], "liquid", desP=dP202,
      desT=design_T(hv["Th_in"]))
    wash = [x for x in v["sections"] if x["name"].startswith("Bed 4")][0]["L_kg_h"]
    L("wash_oil", "P", A, "P-202 discharge", "C-201 wash bed spray", "Wash oil to wash bed (FV-2020)", wash,
      p202["rho"], p202["dP_bar"] - 1.0, v["T_hvgo"], "liquid", desP=dP202, desT=c.desT("P-202"))
    p203 = c.pump("P-203")
    L("slop_s", "P", A, "C-201 slop-wax pan", "P-203A/B", "Slop wax draw to pumps", W("25"), p203["rho"], -0.94,
      v["T_slop"], "suction", desP=3.5, desT=c.desT("P-203"), size=None)
    L("slop_d", "P", A, "P-203A/B", s("25")["to"] + " (OSBL)", "Slop wax product, hot traced (FV-2022)",
      W("25"), p203["rho"], s("25")["P_barg"], s("25")["T_C"], "liquid", desP=c.pump_desP("P-203", 3.5), desT=c.desT("P-203"), stream="25",
      insul="ST")
    L("ms_c201", "MS", A, "MP steam header", "C-201 below stripping trays", "C-201 bottom stripping steam (FV-2023)",
      v["steam"], rho_steam(ms["P_barg"], ms["T_C"]), ms["P_barg"], ms["T_C"], "steam", desP=design_P(ms["P_barg"]),
      desT=design_T(ms["T_C"]))
    Wvr = p204["flow_m3h"] / 1.10 * p204["rho"]
    L("vr_s", "P", A, "C-201 boot", "P-204A/B", "Vacuum residue to P-204 (EIV-2041)", Wvr, p204["rho"], -0.93,
      v["T_bot"], "suction", desP=3.5, desT=c.desT("P-204"), insul="ST")
    L("vr_quench", "P", A, "VR rundown (E-105 outlet)", "C-201 boot", "Cooled VR quench to boot (FV-2027)", Wvr - vr,
      s("26")["rho_liq"], s("26")["P_barg"], s("26")["T_C"], "liquid", desP=dP204, desT=c.desT("P-204"), insul="ST")
    L("p204_mf", "P", A, "P-204A/B", "C-201 boot", "P-204 minimum-flow spillback (RO)", 0.3 * p204["flow_m3h"] *
      p204["rho"], p204["rho"], p204["dP_bar"] - 1, v["T_bot"], "liquid", desP=dP204, desT=c.desT("P-204"), insul="ST")
    p = c.PSV["PSV-2001"]
    L("2001_out", "FL", A, "PSV-2001", "Flare header", f"PSV-2001 outlet ({p['case']})", p["load_kg_h"],
      rho_gas(0.5, p["T"], p["MW"]), 0.5, p["T"], "flare", desP=3.5, desT=design_T(p["T"]))
    L("ch_ci", "CH", A, "X-104", "C-201 OH line", "Corrosion inhibitor injection (X-104)", W("22") * 50e-6, 950,
      2.0, 40, "chem", desP=10.0, cls="A1")

    # ---- sheet 014: VDU PAs & products
    L("lvgo_c2", "P", A, "A-201", "LVGO PA / product split", "LVGO A-201 outlet", lv["hot_flow"], s("23")["rho_liq"],
      p201["dP_bar"] - 2.5, tr["A-201"]["T_out"], "liquid", desP=dP201, desT=design_T(lv["Th_in"]))
    L("lvgo_prod", "P", A, "LVGO split", "Hydrocracker (OSBL)", "LVGO product (FV-2015)", W("23"), s("23")["rho_liq"],
      s("23")["P_barg"], s("23")["T_C"], "liquid", desP=dP201, desT=design_T(lv["Th_in"]), stream="23")
    L("hvgo_p1", "P", A, "HVGO split", "A-202", "HVGO product to A-202", W("24"),
      rho_hc(p202["rho"], p202["T"], hv["Th_out"]), p202["dP_bar"] - 2.0, hv["Th_out"], "liquid", desP=dP202,
      desT=design_T(hv["Th_in"]))
    L("hvgo_prod", "P", A, "A-202", "FCC / hydrocracker (OSBL)", "HVGO product (FV-2019)", W("24"),
      s("24")["rho_liq"], s("24")["P_barg"], s("24")["T_C"], "liquid", desP=dP202, desT=c.desT("A-202"),
      stream="24", insul="ST")
    L("vr_prod", "P", A, "E-105", "Delayed coker / storage (OSBL)", "Vacuum residue product (FV-2025)", vr,
      s("26")["rho_liq"], s("26")["P_barg"], s("26")["T_C"], "liquid", desP=dP204, desT=design_T(ph["E-105"]["Th_in"]),
      stream="26", insul="ST")
    e201 = tr["E-201"]
    W201 = c.steam_rate(e201["Q_kw"], ls["P_barg"], bfw["T_C"])
    L("bfw_e201", "BFW", A, "BFW header", "E-201", "BFW to E-201 (LV-2030)", W201 * 1.02, rho_w(bfw["T_C"]),
      bfw["P_barg"], bfw["T_C"], "water", desP=design_P(bfw["P_barg"]))
    L("ls_e201", "LS", A, "E-201", "LP steam header", "LP steam generated in E-201", W201,
      rho_steam(ls["P_barg"] + 0.5, 150), ls["P_barg"] + 0.5, 150, "steam", desP=c.desP("E-201"),
      desT=design_T(150 + 20))
    L("bd_e201", "BD", A, "E-201", "Blowdown drum (OSBL)", "E-201 continuous blowdown", W201 * 0.02, rho_w(148),
      ls["P_barg"], 148, "water", desP=c.desP("E-201"), desT=design_T(148), min_nps=1.0)

    p = c.PSV["PSV-2003"]
    L("psv2003_out", "LS", A, "PSV-2003", "Atmosphere (safe location)", "PSV-2003 discharge (E-201 steam side)",
      p["load_kg_h"], rho_steam(0.2, p["T"]), 0.2, p["T"], "flare", desP=3.5, desT=design_T(p["T"]))

    # ---- sheet 015: ejectors
    ej = R["ejector"]
    stg = {x["tag"]: x for x in ej["stages"]}
    Pm = ms["P_barg"]
    for t in ("J-201", "J-202", "J-203"):
        L(f"ms_{t[2:].replace('-', '').lower()}", "MS", A, "MP steam header", f"{t}A/B", f"Motive steam to {t}A/B",
          stg[t]["motive_kg_h"], rho_steam(Pm, ms["T_C"]), Pm, ms["T_C"], "steam", desP=design_P(Pm),
          desT=design_T(ms["T_C"]))
    seqE = [("J-201", "E-202"), ("J-202", "E-203"), ("J-203", "E-204")]
    for t, e in seqE:
        Wd = stg[t]["load_kg_h"] + stg[t]["motive_kg_h"]
        Pd = stg[t]["discharge_mbar"] / 1000 - 1.013
        L(f"{t[2:].replace('-', '').lower()}_d", "PG", A, f"{t}A/B", e, f"{t} discharge to {e}", Wd,
          rho_gas(Pd, 120, 18.5), Pd, 120, "vacuum", desP=3.5, desT=c.desT(t), cls="A2", insul="P")
    for e, nxt, t in (("E-202", "J-202A/B", "J-202"), ("E-203", "J-203A/B", "J-203"), ("E-204", "D-202", None)):
        if t:
            Wv = stg[t]["load_kg_h"]
            Pv = stg[t]["suction_mbar"] / 1000 - 1.013
        else:
            Wv = ej["offgas"] * 1.5
            Pv = s("28")["P_barg"] + 0.03
        L(f"{e[2:].replace('-', '').lower()}_v", "PG", A, e, nxt, f"{e} vapour outlet to {nxt}", Wv,
          rho_gas(Pv, 40, 30), Pv, 40, "vacuum" if Pv < 0 else "fg", desP=3.5, desT=c.desT(e), cls="A2")
    for e, d in (("E-202", 0.70), ("E-203", 0.15), ("E-204", 0.15)):
        L(f"leg_{e[2:].replace('-', '').lower()}", "SW", A, e, "D-201 (seal leg)", f"{e} condensate barometric leg",
          ej["sour_water"] * d, rho_w(45), 0.0, 45, "gravity", desP=3.5, desT=c.desT(e))
    L("d201_v", "PG", A, "D-201", "D-202", "Hotwell vent to off-gas KO drum", ej["offgas"] * 0.5, rho_gas(0.05, 45, 30),
      0.05, 45, "fg", desP=c.desP("D-201"), desT=c.desT("D-201"), cls="A2")
    p205, p206 = c.pump("P-205"), c.pump("P-206")
    L("hw_sw_s", "SW", A, "D-201", "P-205A/B", "Hotwell sour water pump suction", W("27"), rho_w(45), 0.05, 45,
      "suction", desP=c.desP("D-201"))
    L("hw_sw_d", "SW", A, "P-205A/B", "SWS (OSBL)", "Hotwell sour water to SWS (LV-2028)", W("27"), rho_w(45),
      0.05 + p205["dP_bar"], 45, "water", desP=c.pump_desP("P-205", c.desP("D-201")), stream="27")
    L("hw_oil_s", "P", A, "D-201 oil compartment", "P-206A/B", "Hotwell slop oil pump suction", max(ej["slop_oil"], 1),
      p206["rho"], 0.05, 45, "suction", desP=c.desP("D-201"))
    L("hw_oil_d", "P", A, "P-206A/B", "Slop (OSBL)", "Hotwell slop oil (LV-2029)", max(ej["slop_oil"], 1), p206["rho"],
      0.05 + p206["dP_bar"], 45, "liquid", desP=c.pump_desP("P-206", c.desP("D-201")))
    L("ncg_recy", "PG", A, "D-202 outlet", "J-201 suction", "NCG recycle for C-201 pressure control (PV-2010)",
      ej["offgas"] * 0.5, rho_gas(0.03, 40, 30), 0.03, 40, "fg", desP=3.5, desT=c.desT("D-202"), cls="A2")
    for e in ("E-202", "E-203", "E-204"):
        Wc = c.cw_rate(E[e]["duty_kw"])
        k = e[2:].replace("-", "").lower()
        L(f"cws_{k}", "CWS", A, "CWS header", e, f"Cooling water supply to {e}", Wc, rho_w(cw["supply_C"]),
          cw["P_barg"], cw["supply_C"], "cw", desP=design_P(cw["P_barg"]) + 2)
        L(f"cwr_{k}", "CWR", A, e, "CWR header", f"Cooling water return from {e}", Wc, rho_w(cw["return_C"]),
          cw["P_barg"] - 1.0, cw["return_C"], "cw", desP=design_P(cw["P_barg"]) + 2)
    p = c.PSV["PSV-2002"]
    L("2002_out", "FL", A, "PSV-2002", "Flare header", f"PSV-2002 outlet ({p['case']})", p["load_kg_h"],
      rho_gas(0.5, p["T"], p["MW"]), 0.5, p["T"], "flare", desP=3.5, desT=design_T(p["T"]))

    # ===================== AREA 900 (unit utilities) ==========================================
    A = "900"
    fgt = W("34")
    L("fg_osbl", "FG", A, "Refinery FG (OSBL)", "D-103", "Fuel gas import to KO drum (PV-9001)", fgt * 1.1,
      rho_gas(fg["P_barg"] + 1.5, 30, fg["MW"]), fg["P_barg"] + 1.5, 30, "fg", desP=c.desP("D-103"))
    L("fg_hdr", "FG", A, "D-103", "H-101 / H-201 / D-102", "Unit fuel gas header", fgt, s("34")["rho_vap"],
      s("34")["P_barg"], s("34")["T_C"], "fg", desP=c.desP("D-103"), desT=c.desT("D-103"), stream="34")
    L("d103_liq", "BD", A, "D-103", "D-104", "D-103 condensate to flare KO drum (LV-9002)", 500, 650, fg["P_barg"], 30,
      "liquid", desP=c.desP("D-103"), desT=c.desT("D-103"), min_nps=1.0)
    relief = max(p["load_kg_h"] for p in c.PSV.values() if p["dest"] == "Flare")
    pf = max(c.PSV.values(), key=lambda q: q["load_kg_h"] if q["dest"] == "Flare" else 0)
    L("fl_hdr", "FL", A, "Unit relief valves", "D-104", "Unit flare header (governing PSV-1001)", relief,
      rho_gas(0.3, pf["T"], pf["MW"]), 0.3, pf["T"], "flare", desP=c.desP("D-104"), desT=c.desT("D-104"))
    L("fl_osbl", "FL", A, "D-104", "Flare (OSBL)", "Unit flare KO drum outlet to main flare", relief,
      rho_gas(0.2, 120, pf["MW"]), 0.2, 120, "flare", desP=c.desP("D-104"), desT=c.desT("D-104"))
    p119 = c.pump("P-119")
    W119 = p119["flow_m3h"] / 1.10 * p119["rho"]
    L("d104_po", "BD", A, "D-104", "P-119A/B", "Flare KO drum liquid to pump-out pumps", W119, p119["rho"],
      0.2, p119["T"], "suction", desP=c.desP("D-104"), desT=c.desT("D-104"))
    L("p119_d", "BD", A, "P-119A/B", "Slop (OSBL)", "Flare KO drum pump-out to slop (LIC-9003 start/stop)", W119,
      p119["rho"], 0.2 + p119["dP_bar"], p119["T"], "liquid", desP=c.pump_desP("P-119", c.desP("D-104")),
      desT=c.desT("P-119"))
    Whs_tot = Whs
    L("hs_hdr", "HS", A, "HP steam (OSBL)", "Unit HP steam header", "HP steam import", Whs_tot,
      rho_steam(hs["P_barg"], hs["T_C"]), hs["P_barg"], hs["T_C"], "steam", desP=design_P(hs["P_barg"]),
      desT=design_T(hs["T_C"]))
    Wms_tot = Wms + coil + v["steam"] + ej["motive_total"] - W113
    L("ms_hdr", "MS", A, "MP steam (OSBL)", "Unit MP steam header", "MP steam import (net of E-113)", max(Wms_tot, 1000),
      rho_steam(ms["P_barg"], ms["T_C"]), ms["P_barg"], ms["T_C"], "steam", desP=design_P(ms["P_barg"]),
      desT=design_T(ms["T_C"]))
    Wls_tot = st_tot + 9.0 * H1["firebox_m3"] * 0
    L("ls_hdr", "LS", A, "LP steam (OSBL)", "Unit LP steam header", "LP steam import (stripping steam + E-201 export)",
      max(Wls_tot, W201), rho_steam(ls["P_barg"], ls["T_C"]), ls["P_barg"], ls["T_C"], "steam",
      desP=design_P(ls["P_barg"]) + 1)
    L("ms_ls_ld", "MS", A, "MP header", "LP header", "MP to LP let-down (PV-9004)", 0.5 * st_tot,
      rho_steam(ms["P_barg"], ms["T_C"]), ms["P_barg"], ms["T_C"], "steam", desP=design_P(ms["P_barg"]),
      desT=design_T(ms["T_C"]))
    L("cd_hdr", "CD", A, "Unit condensate header", "Condensate recovery (OSBL)", "Condensate return",
      Whs + Wms, rho_mix(0.1, rho_w(150), rho_steam(3.5, 150)), 3.5, 150, "twophase", desP=design_P(5.0),
      desT=design_T(186))
    L("bfw_hdr", "BFW", A, "BFW (OSBL)", "Unit BFW header", "BFW import", W113 + W201 + st_tot * 0.03,
      rho_w(bfw["T_C"]), bfw["P_barg"], bfw["T_C"], "water", desP=design_P(bfw["P_barg"]))
    Wcw = sum(c.cw_rate(E[e]["duty_kw"]) for e in ("E-115", "E-202", "E-203", "E-204"))
    L("cws_hdr", "CWS", A, "CW supply (OSBL)", "Unit CWS header", "Cooling water supply", Wcw, rho_w(cw["supply_C"]),
      cw["P_barg"], cw["supply_C"], "cw", desP=design_P(cw["P_barg"]) + 2)
    L("cwr_hdr", "CWR", A, "Unit CWR header", "CW return (OSBL)", "Cooling water return", Wcw, rho_w(cw["return_C"]),
      cw["P_barg"] - 1.5, cw["return_C"], "cw", desP=design_P(cw["P_barg"]) + 2)
    Wc115 = c.cw_rate(E["E-115"]["duty_kw"])
    L("cws_e115", "CWS", "100", "CWS header", "E-115", "Cooling water supply to E-115", Wc115, rho_w(cw["supply_C"]),
      cw["P_barg"], cw["supply_C"], "cw", desP=design_P(cw["P_barg"]) + 2)
    L("cwr_e115", "CWR", "100", "E-115", "CWR header", "Cooling water return from E-115", Wc115, rho_w(cw["return_C"]),
      cw["P_barg"] - 1.0, cw["return_C"], "cw", desP=design_P(cw["P_barg"]) + 2)
    nvalves = len([l for l in c.LOOPS.values() if re.match(r"[A-Z]+V-", l["final"] or "")]) + 40
    L("ia_hdr", "IA", A, "Instrument air (OSBL)", "Unit IA header", "Instrument air (1.5 Nm3/h per valve + 25 %)",
      nvalves * 1.5 * 1.25 * 1.29, rho_gas(U["instrument_air"]["P_barg"], 40, 29), U["instrument_air"]["P_barg"], 40,
      "air", desP=10.0, desT=65)
    L("n2_hdr", "N", A, "Nitrogen (OSBL)", "Unit N2 header", "Nitrogen (purge / blanketing allowance 300 Nm3/h)",
      300 * 1.25, rho_gas(U["nitrogen"]["P_barg"], 40, 28), U["nitrogen"]["P_barg"], 40, "air", desP=10.0, desT=65)
    L("bd_hdr", "BD", A, "Unit closed drains", "Slop (OSBL)", "Closed drain header", 30000, 750, 1.0, 150, "liquid",
      desP=10.0, desT=design_T(366), size=6)
    return reg


# ----------------------------------------------------------------------------- instrument descriptions
FIRST = {"A": "Analysis", "B": "Burner / flame", "E": "Voltage", "F": "Flow", "H": "Hand", "I": "Current",
         "K": "Time", "L": "Level", "M": "Moisture", "P": "Pressure", "S": "Speed", "T": "Temperature",
         "W": "Weight", "X": "On/off (unclassified)", "Z": "Position"}
TYPES = {
    "FT": "Flow transmitter", "FE": "Flow element (orifice)", "FIC": "Flow indicating controller", "FI": "Flow indicator",
    "FV": "Flow control valve", "FFIC": "Flow ratio controller", "FFY": "Flow ratio relay", "FY": "Flow relay / stroke positioner",
    "FZLL": "Flow low-low trip function (SIS)", "FO": "Restriction orifice", "FG": "Sight flow glass",
    "PT": "Pressure transmitter", "PI": "Pressure gauge", "PIC": "Pressure indicating controller",
    "PV": "Pressure control valve", "PCV": "Self-acting pressure regulator", "PDT": "Differential pressure transmitter",
    "PDI": "Differential pressure indicator", "PDIC": "Differential pressure indicating controller",
    "PDV": "Differential pressure control (mix) valve", "PZLL": "Pressure low-low trip function (SIS)",
    "PZHH": "Pressure high-high trip function (SIS)", "PSV": "Pressure safety valve", "PY": "Pressure relay / VSD signal",
    "TT": "Temperature transmitter", "TE": "Temperature element", "TI": "Temperature indicator", "TW": "Thermowell",
    "TIC": "Temperature indicating controller", "TV": "Temperature control valve", "TDIC": "Temperature differential controller",
    "TZHH": "Temperature high-high trip function (SIS)", "TY": "Temperature relay / output signal",
    "LT": "Level transmitter", "LG": "Level gauge", "LIC": "Level indicating controller", "LV": "Level control valve",
    "LZHH": "Level high-high trip function (SIS)", "LZLL": "Level low-low trip function (SIS)", "LY": "Level relay / output",
    "LSH": "Level switch high", "LAH": "Level alarm high",
    "AT": "Analyser transmitter", "AIC": "Analyser indicating controller", "AV": "Analyser control element (damper/vane)",
    "AI": "Analyser indicator", "BS": "Flame scanner", "BZLL": "Flame failure trip function (SIS)",
    "XV": "On/off shutdown valve", "LAHH": "Level alarm high-high (DCS)", "TSV": "Thermal safety valve", "EIV": "Emergency isolation valve (ROSOV)", "HS": "Hand switch",
    "XY": "Trip relay output", "ZSO": "Limit switch open", "ZSC": "Limit switch closed", "KV": "Damper actuator",
    "SC": "Speed controller (VSD)", "UZ": "Unit ESD logic (SIS)", "GD": "Gas detector", "AZ": "Analyser trip",
}


def inst_type(tag):
    letters = tag.split("-")[0]
    if letters in TYPES:
        return TYPES[letters]
    return FIRST.get(letters[0], "Instrument") + " " + letters
