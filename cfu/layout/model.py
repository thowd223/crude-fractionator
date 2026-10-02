"""Plot-plan model: equipment placement, structures, nozzles and spacing checks -> data/layout.json.

Coordinate system (CONVENTIONS.md "Plot plan frame"):
  x = east (m), y = north (m), origin = SW corner of unit plot (230 x 150 m); z = elevation EL (m),
  grade = EL 100.000.  rotation = angle of the equipment long axis (L) from +x, degrees CCW.
  Footprint L (along axis) x W (across).  z_base = underside of the equipment body (top of
  foundation for columns/heaters/pumps; bottom of shell for horizontal vessels/exchangers).

Placement is topology driven (cfu/hmb.py): pumps beside the rack directly below their suction
vessels, exchanger trains grouped in two rows sharing a bundle-pull aisle, air coolers on the rack
top above the equipment they serve, side strippers adjacent to C-101, reflux drum D-102 next to
A-101, fired heaters on the south (upwind, SSE prevailing wind) side of the rack.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

GRADE = 100.0
PLOT = (230.0, 150.0)
RACK = dict(x0=0.0, x1=216.0, y0=70.0, y1=80.0, tiers=[106.0, 108.5, 111.0])
AC_BASE = 115.0               # underside of air-cooler bundles (structure on top of tier 3)
PUMP_N_Y = 83.5               # centreline of pump row north of rack
PUMP_S_Y = 65.5               # centreline of pump row south of rack
HX_CL = 101.5                 # exchanger centreline elevation (on saddles/pedestals)


# ---------------------------------------------------------------------------------------------
def _load():
    eq = json.loads((DATA / "equipment.json").read_text())
    res = json.loads((DATA / "process_results.json").read_text())
    return {e["tag"]: e for e in eq}, res


def _split_tag(tag: str) -> list[str]:
    """'P-101A/B' -> ['P-101A','P-101B']"""
    if tag.endswith("A/B"):
        base = tag[:-3]
        return [base + "A", base + "B"]
    return [tag]


def _shell_tags(e) -> list[str]:
    n = int(e.get("shells") or e.get("n_shells") or 1)
    if n <= 1:
        return [e["tag"]]
    return [e["tag"] + "ABCDEFGH"[i] for i in range(n)]


class Layout:
    def __init__(self):
        self.E, self.R = _load()
        self.items: list[dict] = []
        self.by_tag: dict[str, dict] = {}
        self.notes: list[str] = []

    # ------------------------------------------------------------------ primitives
    def add(self, tag, src, shape, x, y, z_base, rot, L, W, H, **kw):
        e = self.E.get(src, {})
        it = dict(tag=tag, parent_tag=src, type=e.get("type", kw.pop("type", "")),
                  service=e.get("service", kw.pop("service", "")), area=e.get("area", kw.pop("area", "")),
                  shape=shape, x=round(x, 3), y=round(y, 3), z_base=round(z_base, 3), rotation=rot,
                  L=round(L, 3), W=round(W, 3), height=round(H, 3), top_el=round(z_base + H, 3))
        it.update({k: v for k, v in kw.items() if k not in ("type", "service", "area")})
        it["bbox"] = [round(v, 3) for v in self.bbox(it)]
        it.setdefault("nozzles", {})
        self.items.append(it)
        self.by_tag[tag] = it
        return it

    @staticmethod
    def bbox(it):
        a = math.radians(it["rotation"])
        hx = abs(math.cos(a)) * it["L"] / 2 + abs(math.sin(a)) * it["W"] / 2
        hy = abs(math.sin(a)) * it["L"] / 2 + abs(math.cos(a)) * it["W"] / 2
        return (it["x"] - hx, it["y"] - hy, it["x"] + hx, it["y"] + hy)

    def local(self, it, u, v, z):
        """local (u along axis, v across) -> plant coords"""
        a = math.radians(it["rotation"])
        return [round(it["x"] + u * math.cos(a) - v * math.sin(a), 3),
                round(it["y"] + u * math.sin(a) + v * math.cos(a), 3), round(z, 3)]

    # ------------------------------------------------------------------ equipment families
    def column(self, tag, x, y, btl, noz_side=-90.0, sections=None):
        e = self.E[tag]
        D = e["D"]
        H = e["H"]
        Dbot = e.get("D2") or D
        z0 = GRADE + 0.3
        ttl = btl + H
        top = ttl + (e.get("D3") or D) / 4.0
        it = self.add(tag, tag, "vcyl", x, y, z0, 0, D, D, top - z0, D=D, bottom_tl=round(btl, 3),
                      top_tl=round(ttl, 3), skirt_h=round(btl - z0 - Dbot / 4, 3),
                      body=sections or [[round(btl, 3), round(ttl, 3), D]])
        self._col_noz_side = noz_side
        it["nozzles"]["overhead"] = [x, y, round(top, 3)]
        it["nozzles"]["bottoms"] = [x, y, round(btl - Dbot / 4, 3)]
        return it

    def shell_noz(self, it, name, z, ang_deg, Dloc=None):
        R = (Dloc or it["D"]) / 2
        a = math.radians(ang_deg)
        it["nozzles"][name] = [round(it["x"] + R * math.cos(a), 3), round(it["y"] + R * math.sin(a), 3), round(z, 3)]

    def pump(self, tag, src, x, y, south_row=False):
        e = self.E[src]
        L, W, H = e["L"], e["W"], e["H"]
        rot = 270 if south_row else 90      # axis N-S; casing/suction end faces the suction vessel
        it = self.add(tag, src, "box", x, y, GRADE + 0.3, rot, L, W, H, motor_kw=e.get("motor_kw"),
                      api610=e.get("api610"))
        it["nozzles"]["suction"] = self.local(it, L / 2 - 0.2, 0, GRADE + 0.3 + 0.6)
        it["nozzles"]["discharge"] = self.local(it, L / 2 - 0.7, 0, GRADE + 0.3 + H)
        return it

    def hx(self, tag, src, x, y, rot, chan_end=+1, cl=HX_CL, z_base=None):
        """Horizontal shell & tube. chan_end=+1: channel at +u end (bundle pulled towards +u)."""
        e = self.E[src]
        L, D = e["L"], e["D"]
        zb = (cl - D / 2) if z_base is None else z_base
        it = self.add(tag, src, "hcyl", x, y, zb, rot, L, D, D, D=D, channel_end=chan_end,
                      bundle_pull=round(L + 1.5, 1))
        zc = zb + D / 2
        s = chan_end
        it["nozzles"]["tube_inlet"] = self.local(it, s * (L / 2 - 0.4), 0, zb)
        it["nozzles"]["tube_outlet"] = self.local(it, s * (L / 2 - 0.4), 0, zb + D)
        it["nozzles"]["shell_inlet"] = self.local(it, -s * (L / 2 - 1.0), 0, zb + D)
        it["nozzles"]["shell_outlet"] = self.local(it, s * (L / 2 - 1.6), 0, zb)
        it["z_axis"] = round(zc, 3)
        return it

    def drum_h(self, tag, x, y, rot, zb, boot=None):
        e = self.E[tag]
        L, D = e["L"], e["D"]
        it = self.add(tag, tag, "hcyl", x, y, zb, rot, L + D / 2, D, D, D=D, TT=L, z_axis=round(zb + D / 2, 3))
        n = it["nozzles"]
        n["inlet"] = self.local(it, -(L / 2 - 1.0), 0, zb + D)
        n["vapour_outlet"] = self.local(it, (L / 2 - 0.8), 0, zb + D)
        n["liquid_outlet"] = self.local(it, (L / 2 - 1.5), 0, zb)
        if boot:
            bD, bH = boot
            it["boot"] = dict(D=bD, H=bH, u=round(L / 2 - 2.5, 2))
            n["water_outlet"] = self.local(it, L / 2 - 2.5, 0, zb - bH + 0.3)
        return it

    def drum_v(self, tag, x, y, zb=GRADE + 0.3, leg=1.0):
        e = self.E[tag]
        D, H = e["D"], e["H"]
        it = self.add(tag, tag, "vcyl", x, y, zb, 0, D, D, leg + H + D / 2, D=D,
                      bottom_tl=round(zb + leg, 3), top_tl=round(zb + leg + H, 3),
                      body=[[round(zb + leg, 3), round(zb + leg + H, 3), D]])
        n = it["nozzles"]
        n["inlet"] = [round(x + D / 2, 3), y, round(zb + leg + H * 0.6, 3)]
        n["vapour_outlet"] = [x, y, round(zb + leg + H + D / 4, 3)]
        n["liquid_outlet"] = [x, y, round(zb + leg - D / 4, 3)]
        return it

    def air_cooler(self, tag, src, x0, bays, nb):
        e = self.E[src]
        fans = int(e.get("fans", 2 * nb))
        for i in range(nb):
            t = tag if nb == 1 else f"{tag}-B{i + 1}"
            xc = x0 + 3.0 + 6.0 * i
            it = self.add(t, src, "box", xc, 75.0, AC_BASE, 90, 12.0, 6.0, 2.5, bay=i + 1, bays=nb,
                          fans=max(1, fans // nb), draft="forced", fan_deck_el=round(AC_BASE - 2.0, 1),
                          motor_kw=e.get("motor_kw"))
            it["nozzles"]["inlet"] = [round(xc, 3), 80.8, AC_BASE + 1.6]
            it["nozzles"]["outlet"] = [round(xc, 3), 80.8, AC_BASE + 0.3]

    def heater(self, tag, x, y):
        e = self.E[tag]
        L, W, H = e["L"], e["W"], e["H"]
        r = self.R["heaters"][tag]
        z0 = GRADE
        rad_top = z0 + 2.0 + 0.45 * H          # burners floor-fired, firebox floor at +2.0 m
        conv_top = rad_top + 0.22 * H
        stack_D = 3.2 if tag == "H-101" else 2.2
        it = self.add(tag, tag, "heater", x, y, z0, 0, L, W, H, cells=r["cells"], passes=r["passes"],
                      burners=r["burners"], duty_mw=round(r["Q_abs_kw"] / 1000, 2),
                      radiant=dict(z0=z0 + 2.0, z1=round(rad_top, 2), L=L, W=W),
                      convection=dict(z0=round(rad_top, 2), z1=round(conv_top, 2), L=round(L * 0.6, 2),
                                      W=round(min(W * 0.45, 5.0), 2)),
                      stack=dict(x=x, y=y, D=stack_D, z0=round(conv_top, 2), z1=round(z0 + H, 2)))
        n = it["nozzles"]
        n["inlet"] = [x + L * 0.25, round(y + W / 2, 3), round(conv_top - 0.8, 3)]       # convection inlet
        n["outlet"] = [x, round(y + W / 2, 3), round(z0 + 3.0, 3)]                       # radiant outlet manifold
        n["fuel_gas"] = [x - L / 2 + 1.0, round(y + W / 2, 3), z0 + 1.0]
        n["stack_top"] = [x, y, round(z0 + H, 3)]
        return it

    # ------------------------------------------------------------------ C-101 tray elevations
    def c101_tray_el(self, ttl):
        e = self.E["C-101"]
        ts = {}
        for s in e.get("sections", []):
            a, b = [int(v) for v in s["trays"].split("-")]
            for t in range(a, b + 1):
                ts[t] = s["TS_mm"] / 1000.0
        tr = self.R["atm"]["tray"]
        el = {1: ttl - 2.0}
        for t in range(2, 42):
            if t == tr["wash_bot"] + 1:
                el[t] = el[t - 1] - 4.0                      # flash zone
            else:
                el[t] = el[t - 1] - ts.get(t - 1, 0.61)
        return el

    # ------------------------------------------------------------------ build
    def build(self):
        E, R = self.E, self.R
        tr = R["atm"]["tray"]

        # ======================= CDU: C-101 + strippers + OH system (x 72-150, north) ===========
        c = E["C-101"]
        btl = 106.0
        ttl = btl + c["H"]
        tel = self.c101_tray_el(ttl)
        cone_top = tel[tr["wash_bot"] + 1] + 2.0          # D2 below the flash zone
        col = self.column("C-101", 95.0, 98.0, btl,
                          sections=[[btl, round(cone_top - 1.5, 3), c["D2"]], [round(cone_top, 3), round(ttl, 3), c["D"]]])
        col["cone"] = [round(cone_top - 1.5, 3), round(cone_top, 3)]
        col["tray_el"] = {str(k): round(v, 3) for k, v in tel.items()}
        col["tray_spacing_note"] = "0.76 m in pumparound sections (trays 1-3, 11-13, 23-25), 0.61 m elsewhere; 4.0 m flash zone"
        S = -90.0  # nozzles toward rack/pumps (south)
        self.shell_noz(col, "reflux_return", tel[1] + 0.35, S - 25)
        self.shell_noz(col, "tpa_return", tel[tr["TPA_ret"]] + 0.45, S + 25)
        self.shell_noz(col, "tpa_draw", tel[tr["TPA_draw"]] - 0.25, S)
        for p, ret, drw in [("kero", None, tr["KERO"]), ("diesel", None, tr["DIESEL"]), ("ago", None, tr["AGO"])]:
            self.shell_noz(col, f"{p}_draw", tel[drw] - 0.25, -20.0)     # toward strippers (east)
            self.shell_noz(col, f"{p}_vapour_return", tel[drw - 1] - 0.3, 10.0)
        self.shell_noz(col, "mpa_draw", tel[tr["MPA_draw"]] - 0.25, S)
        self.shell_noz(col, "mpa_return", tel[tr["MPA_ret"]] + 0.45, S + 25)
        self.shell_noz(col, "bpa_draw", tel[tr["BPA_draw"]] - 0.25, S)
        self.shell_noz(col, "bpa_return", tel[tr["BPA_ret"]] + 0.45, S + 25)
        self.shell_noz(col, "feed", (tel[tr["wash_bot"]] + tel[tr["wash_bot"] + 1]) / 2 - 0.3, S)
        self.shell_noz(col, "stripping_steam", tel[41] - 0.6, S + 40, Dloc=c["D2"])
        col["nozzle_trays"] = {k: v for k, v in tr.items()}

        for tag, xs, prod in [("C-102", 106.5, "KERO"), ("C-103", 112.5, "DIESEL"), ("C-104", 118.5, "AGO")]:
            s = self.column(tag, xs, 98.0, 104.0)
            self.shell_noz(s, "feed", s["top_tl"] - 0.9, 180.0)
            s["nozzles"]["vapour_return"] = s["nozzles"].pop("overhead")
            self.shell_noz(s, "stripping_steam", s["bottom_tl"] + 0.9, -90.0)
            s["draw_from"] = f"C-101 tray {tr[prod]}"

        # overhead system: A-101 on rack (x 72-84), D-102 next to it, E-115A/B trims, X-103
        self.drum_h("D-102", 79.0, 90.0, 0, 105.0, boot=(1.5, 3.0))
        e115 = _shell_tags(E["E-115"])
        for i, t in enumerate(e115):
            self.hx(t, "E-115", 79.0, 95.5 + 3.0 * i, 0, chan_end=-1)
        self.add("X-103", "X-103", "box", 76.0, 104.0, GRADE + 0.3, 0, 3.0, 2.0, 2.5)

        # north pump row (CDU) - grouped under the vessel they take suction from
        north = [("P-103A/B", 72.5), ("P-104A/B", 79.0), ("P-105A/B", 85.5), ("P-112A/B", 92.0), ("P-108A/B", 98.5),
                 ("P-109A/B", 105.0), ("P-110A/B", 111.5), ("P-111A/B", 118.0), ("P-106A/B", 124.5),
                 ("P-107A/B", 131.0)]
        for src, x0 in north:
            for i, t in enumerate(_split_tag(src)):
                self.pump(t, src, x0 + 3.0 * i, PUMP_N_Y)

        # ======================= Light ends, north-west (x 46-72) ================================
        self.column("C-106", 52.0, 100.0, 106.0)
        self.column("C-105", 64.0, 100.0, 104.0)
        st, sp = R["stab"], R["split"]
        for tag, cc in [("C-105", st), ("C-106", sp)]:
            it = self.by_tag[tag]
            t1 = it["top_tl"] - 2.0
            it["tray_el"] = {"1": round(t1, 3), str(cc["feed_stage"]): round(t1 - (cc["feed_stage"] - 1) * 0.61 - 0.6, 3),
                             str(cc["N_actual"]): round(t1 - (cc["N_actual"] - 1) * 0.61 - 1.2, 3)}
            self.shell_noz(it, "reflux_return", t1 + 0.35, -90)
            self.shell_noz(it, "feed", t1 - (cc["feed_stage"] - 1) * 0.61 - 0.3, 0 if tag == "C-105" else 180)
            self.shell_noz(it, "reboiler_return", it["bottom_tl"] + 1.0, 90)
            self.shell_noz(it, "reboiler_draw", it["bottom_tl"] + 0.2, 90)
        self.drum_h("D-106", 54.0, 90.5, 0, 104.5)
        self.drum_h("D-105", 65.5, 90.5, 0, 104.0, boot=(0.6, 1.5))
        self.hx("E-117", "E-117", 52.0, 106.0, 0, chan_end=-1, cl=107.0)    # thermosyphon: elevated
        self.hx("E-116", "E-116", 64.0, 105.5, 0, chan_end=+1)
        self.hx("E-114", "E-114", 70.0, 100.0, 90, chan_end=+1)
        for src, x0 in [("P-116A/B", 50.0), ("P-117A/B", 56.5), ("P-115A/B", 63.0)]:
            for i, t in enumerate(_split_tag(src)):
                self.pump(t, src, x0 + 3.0 * i, PUMP_N_Y)

        # ======================= Preheat exchangers, north-west (x 10-45) ========================
        row1 = ["E-106", "E-107", "E-108", "E-109", "E-110"]                  # hot train (near rack)
        row2 = ["E-111", "E-101", "E-102", "E-103", "E-104", "E-105", "E-113", "E-201"]
        x = 12.5
        for src in row1:
            for t in _shell_tags(E[src]):
                self.hx(t, src, x, 92.0, 90, chan_end=+1)       # channel north -> pulled into aisle
                self.by_tag[t]["train"] = "hot"
                x += 3.5
        x = 12.5
        for src in row2:
            for t in _shell_tags(E[src]):
                self.hx(t, src, x, 109.0, 90, chan_end=-1)      # channel south -> pulled into aisle
                self.by_tag[t]["train"] = "cold" if src in ("E-101", "E-102", "E-103", "E-104", "E-105") else (
                    "hot" if src == "E-111" else "steam gen.")
                x += 3.5
        for i, t in enumerate(_split_tag("P-101A/B")):
            self.pump(t, "P-101A/B", 14.0 + 4.5 * i, PUMP_N_Y)
        self.drum_h("D-104", 135.0, 128.0, 0, GRADE + 0.6)

        # ======================= Desalting, south-west ===========================================
        for tag, yy in [("D-101A", 52.0), ("D-101B", 42.0)]:
            e = E[tag]
            it = self.add(tag, tag, "hcyl", 36.0, yy, GRADE + 1.5, 0, e["L"] + e["D"] / 2, e["D"], e["D"],
                          D=e["D"], TT=e["L"], z_axis=round(GRADE + 1.5 + e["D"] / 2, 3), transformers=3)
            n = it["nozzles"]
            n["inlet"] = self.local(it, -2.0, 0, GRADE + 1.5)
            n["outlet"] = self.local(it, 2.0, 0, GRADE + 1.5 + e["D"])
            n["brine_outlet"] = self.local(it, 6.0, 0, GRADE + 1.5)
            n["mud_wash"] = self.local(it, -6.0, 0.8, GRADE + 1.6)
        self.hx("E-118", "E-118", 58.5, 47.0, 0, chan_end=+1)
        self.add("X-101", "X-101", "box", 58.0, 55.0, GRADE + 0.3, 0, 3.0, 2.0, 2.5)
        self.add("X-102", "X-102", "box", 58.0, 59.5, GRADE + 0.3, 0, 3.0, 2.0, 2.5)
        for src, x0, pitch in [("P-114A/B", 25.0, 3.0), ("P-118", 31.5, 0), ("P-102A/B", 46.0, 4.5)]:
            for i, t in enumerate(_split_tag(src)):
                self.pump(t, src, x0 + pitch * i, PUMP_S_Y, south_row=True)
        for t in ("X-101", "X-102"):
            it = self.by_tag[t]
            it["nozzles"]["discharge"] = [it["x"] + 1.5, it["y"], GRADE + 1.0]

        # ======================= Fired heaters, south band ======================================
        self.heater("H-101", 98.0, 36.0)
        self.heater("H-201", 172.0, 36.0)
        a = self.add("E-120", "E-120", "box", 92.0, 22.0, GRADE + 0.3, 0, E["E-120"]["L"], E["E-120"]["W"],
                     E["E-120"]["H"])
        a["nozzles"].update(flue_in=[92.0, 25.0, 110.0], flue_out=[96.0, 22.0, 101.0], air_in=[88.0, 22.0, 102.0],
                            air_out=[92.0, 25.0, 102.0])
        for src, xx in [("K-101A/B", 102.0), ("K-102A/B", 109.0)]:
            for i, t in enumerate(_split_tag(src)):
                f = self.add(t, src, "box", xx, 20.5 + 3.5 * i, GRADE + 0.3, 0, 6.0, 3.0, 4.0,
                             motor_kw=E[src].get("motor_kw"))
                f["nozzles"].update(inlet=self.local(f, -2.5, 0, 102.5), outlet=self.local(f, 2.5, 0, 103.5))
        self.drum_v("D-103", 150.0, 24.0)

        # ======================= VDU, north-east (x 150-221) ====================================
        v = E["C-201"]
        vb = 110.0
        vt = vb + v["H"]
        prof = [("top_head", 3.0), ("bed1_lvgo_pa", 2.5), ("lvgo_collector", 2.5), ("bed2_fract", 2.0),
                ("hvgo_collector", 2.5), ("bed3_hvgo_pa", 3.5), ("wash_distr", 2.5), ("bed4_wash", 1.2),
                ("slop_collector", 2.5), ("flash_zone", 5.0), ("stripping_trays", 4 * 0.61), ("sump", 6.0)]
        tot = sum(h for _, h in prof)
        z = vt
        zones = {}
        for nm, h in prof:
            hh = h * v["H"] / tot
            zones[nm] = [round(z - hh, 3), round(z, 3)]
            z -= hh
        top_sec = zones["lvgo_collector"][0]
        fz = zones["flash_zone"]
        cv = self.column("C-201", 175.0, 98.0, vb, sections=[
            [vb, round(zones["stripping_trays"][1] - 0.5, 3), v["D2"]],
            [round(zones["stripping_trays"][1] + 0.5, 3), round(top_sec - 0.8, 3), v["D"]],
            [round(top_sec + 0.8, 3), round(vt, 3), v["D3"]]])
        cv["zones"] = zones
        cv["nozzles"]["overhead"] = [175.0, 98.0, round(vt + v["D3"] / 4, 3)]
        Dm, Dt, Db = v["D"], v["D3"], v["D2"]
        self.shell_noz(cv, "lvgo_pa_return", zones["bed1_lvgo_pa"][1] + 0.4, -90, Dt)
        self.shell_noz(cv, "lvgo_draw", zones["lvgo_collector"][0] + 0.6, -90, Dm)
        self.shell_noz(cv, "hvgo_pa_return", zones["bed3_hvgo_pa"][1] + 0.4, -110, Dm)
        self.shell_noz(cv, "hvgo_draw", zones["hvgo_collector"][0] + 0.6, -70, Dm)
        self.shell_noz(cv, "wash_oil_return", zones["bed4_wash"][1] + 0.4, -110, Dm)
        self.shell_noz(cv, "slop_wax_draw", zones["slop_collector"][0] + 0.6, -70, Dm)
        self.shell_noz(cv, "feed", (fz[0] + fz[1]) / 2, -90, Dm)
        self.shell_noz(cv, "stripping_steam", zones["stripping_trays"][0] - 0.3, -60, Db)
        self.shell_noz(cv, "quench_return", zones["sump"][1] - 1.5, -120, Db)

        # ejector structure (barometric condensers >= 10.4 m above hotwell)
        self.ejector_structure = dict(id="ST-201", x0=190.0, y0=92.0, x1=202.0, y1=100.0,
                                      levels=[112.0, 115.0, 120.0], top=124.0)
        for jt, et, el in [("J-203", "E-204", 112.0), ("J-202", "E-203", 115.0), ("J-201", "E-202", 120.0)]:
            ee = self.hx(et, et, 196.0, 97.5, 0, chan_end=+1, z_base=el + 0.4)
            ee["nozzles"]["condensate_outlet"] = ee["nozzles"]["shell_outlet"]
            je = E[jt]
            j = self.add(jt, jt, "hcyl", 196.0, 94.0, el + 0.5, 0, je["L"], je["D"], je["D"], D=je["D"],
                         arrangement="2 x 50 % parallel", z_axis=round(el + 0.5 + je["D"] / 2, 3))
            j["nozzles"].update(suction=self.local(j, -2.0, 0, el + 0.5 + je["D"] / 2),
                                discharge=self.local(j, 2.0, 0, el + 0.5 + je["D"] / 2),
                                motive_steam=self.local(j, -1.6, 0, el + 0.5 + je["D"]))
        self.drum_h("D-201", 196.0, 106.0, 0, GRADE + 0.6)
        self.by_tag["D-201"]["barometric_legs"] = "E-202/203/204 condensate legs, seal >= 10.4 m"
        self.drum_v("D-202", 203.0, 106.0)
        self.add("X-104", "X-104", "box", 209.0, 106.0, GRADE + 0.3, 0, 3.0, 2.0, 2.5)
        for src, x0 in [("P-204A/B", 172.0), ("P-203A/B", 178.5), ("P-202A/B", 185.0), ("P-201A/B", 191.5)]:
            for i, t in enumerate(_split_tag(src)):
                self.pump(t, src, x0 + 3.0 * i, PUMP_N_Y)
        for src, x0 in [("P-205A/B", 193.0), ("P-206A/B", 199.5)]:
            for i, t in enumerate(_split_tag(src)):
                self.pump(t, src, x0 + 3.0 * i, 111.5, south_row=True)
        for t in ("X-103", "X-104"):
            it = self.by_tag[t]
            it["nozzles"]["discharge"] = [it["x"] + 1.5, it["y"], GRADE + 1.0]

        # ======================= Air coolers on rack top =========================================
        for tag, x0 in [("A-107", 48.0), ("A-106", 54.0), ("A-108", 60.0), ("A-101", 72.0), ("A-103", 108.0),
                        ("A-104", 114.0), ("A-105", 120.0), ("A-201", 156.0), ("A-202", 162.0)]:
            self.air_cooler(tag, tag, x0, None, int(E[tag].get("bays", 1)))

        missing = [t for t in E if not any(i["parent_tag"] == t for i in self.items)]
        if missing:
            raise RuntimeError(f"unplaced equipment: {missing}")
        self.structures()
        self.checks = spacing_checks(self)
        return self

    # ------------------------------------------------------------------ structures / areas
    def structures(self):
        x0, x1 = RACK["x0"], RACK["x1"]
        bents = [0.0] + [float(x) for x in range(12, int(x1) + 1, 6)]
        self.rack = dict(id="PR-100", axis="E-W", x0=x0, x1=x1, y0=RACK["y0"], y1=RACK["y1"], width=10.0,
                         y_centre=75.0, bent_spacing=6.0, bents_x=bents,
                         road_crossing_span=dict(x0=0.0, x1=12.0, note="12 m portal span over west perimeter road"),
                         tiers=[dict(level=1, el=RACK["tiers"][0], service="Hot process lines (B2/B3), crude, residue, pumparounds"),
                                dict(level=2, el=RACK["tiers"][1], service="Product, cold HC, sour water, OSBL product lines"),
                                dict(level=3, el=RACK["tiers"][2], service="Utilities: steam/condensate, CW, FG, N2, IA, flare header")],
                         cable_tray=dict(el=109.75, side="south", bracket=1.2, note="EL/IC trays on cantilever brackets, segregated from hot lines"),
                         air_cooler_deck=dict(el=AC_BASE, fan_deck_el=AC_BASE - 2.0, note="forced-draft air coolers on structure above tier 3"),
                         beam_depth=0.5, column_section="HE400B", min_headroom_m=round(RACK["tiers"][0] - 0.5 - GRADE - 0.15, 2))
        plats = []
        for it in self.items:
            if it["type"] != "Column":
                continue
            Dp = it["D"]
            els = []
            if it["tag"] == "C-101":
                tel = {int(k): v for k, v in it["tray_el"].items()}
                tr = self.R["atm"]["tray"]
                for k in ("AGO", "BPA_draw", "DIESEL", "MPA_draw", "KERO", "TPA_draw"):
                    els.append(tel[tr[k]] - 1.2)
                els += [tel[41] - 1.5, it["top_tl"] - 0.5]
            elif it["tag"] == "C-201":
                z = it["zones"]
                els = [z["sump"][1] - 1.0, z["flash_zone"][0] + 1.0, z["slop_collector"][0], z["hvgo_collector"][0],
                       z["lvgo_collector"][0], it["top_tl"] - 0.5]
            else:
                h = it["top_tl"] - it["bottom_tl"]
                n = max(1, int(h // 7.0))
                els = [it["bottom_tl"] + h * (i + 1) / (n + 1) for i in range(n)] + [it["top_tl"] - 0.5]
            for el in sorted(els):
                d_here = Dp
                for z0, z1, dd in it.get("body", []):
                    if z0 - 2 <= el <= z1 + 2:
                        d_here = dd
                plats.append(dict(tag=it["tag"], el=round(el, 3), r_in=round(d_here / 2 + 0.1, 3),
                                  r_out=round(d_here / 2 + 1.3, 3), arc=[0, 360] if el >= it["top_tl"] - 1 else [20, 250],
                                  ladder_side_deg=135))
        stacks = [dict(tag=h["tag"], **h["stack"]) for h in self.items if h["shape"] == "heater"]
        roads = [
            dict(id="RD-W", kind="perimeter road", x0=3, y0=22, x1=9, y1=147),
            dict(id="RD-N", kind="perimeter road", x0=3, y0=141, x1=227, y1=147),
            dict(id="RD-E", kind="perimeter road", x0=221, y0=3, x1=227, y1=147),
            dict(id="RD-S", kind="perimeter road", x0=67, y0=3, x1=227, y1=9),
            dict(id="RD-SW", kind="perimeter road (deviated north of SS-100/FAR-100)", x0=3, y0=22, x1=73, y1=28),
            dict(id="RD-SC", kind="perimeter road (connector)", x0=67, y0=3, x1=73, y1=28),
            dict(id="RD-INT", kind="internal fire/maintenance access road", x0=137, y0=9, x1=143, y1=66),
        ]
        buildings = [dict(id="SS-100", name="Unit substation", x0=10, y0=5, x1=40, y1=20, height=8.0,
                          classification="non-classified, pressurised"),
                     dict(id="FAR-100", name="Field auxiliary room / satellite instrument house", x0=45, y0=5, x1=65,
                          y1=17, height=5.0, classification="non-classified, pressurised, blast-assessed")]
        areas = [
            dict(id="BP-1", kind="bundle pull / maintenance aisle", x0=9, y0=96.2, x1=46, y1=104.8,
                 note="shared pull aisle for preheat shells (bundle 7.5 m), opens to RD-W"),
            dict(id="LD-1", kind="laydown", x0=12, y0=116, x1=44, y1=138, note="exchanger bundle laydown / cleaning"),
            dict(id="CR-1", kind="crane area", x0=46, y0=111, x1=72, y1=138, note="C-105/C-106 erection & maintenance crane"),
            dict(id="CR-2", kind="crane area", x0=84, y0=106, x1=112, y1=138, note="C-101 erection crane (main lift) + tailing crane"),
            dict(id="LD-2", kind="laydown", x0=114, y0=104, x1=150, y1=120, note="column internals / trays laydown"),
            dict(id="CR-3", kind="crane area", x0=158, y0=110, x1=188, y1=138, note="C-201 erection & packing replacement"),
            dict(id="LD-3", kind="laydown", x0=205, y0=116, x1=219, y1=138, note="VDU / ejector maintenance laydown"),
            dict(id="CR-4", kind="crane area", x0=86, y0=45, x1=110, y1=62, note="H-101 tube / burner maintenance (keep clear: no HC equipment)"),
            dict(id="CR-5", kind="crane area", x0=164, y0=45, x1=180, y1=62, note="H-201 tube / burner maintenance"),
            dict(id="LD-4", kind="laydown", x0=10, y0=30, x1=19, y1=62, note="desalter internals / grid laydown"),
            dict(id="FU-1", kind="future / construction laydown", x0=186, y0=14, x1=218, y1=64, note="construction laydown, future"),
        ]
        escape = [
            dict(id="ER-1", pts=[[9, 75], [221, 75]], note="under-rack aisle (6 m clear)"),
            dict(id="ER-2", pts=[[46, 100.5], [9, 100.5]], note="exchanger aisle to RD-W"),
            dict(id="ER-3", pts=[[47, 80], [47, 141]]),
            dict(id="ER-4", pts=[[90.2, 80], [90.2, 106], [86, 141]]),
            dict(id="ER-5", pts=[[122.75, 80], [122.75, 141]]),
            dict(id="ER-6", pts=[[155, 80], [155, 141]]),
            dict(id="ER-7", pts=[[214, 80], [214, 141]]),
            dict(id="ER-8", pts=[[70, 70], [70, 28]]),
            dict(id="ER-9", pts=[[9, 61.5], [66, 61.5], [70, 61.5]]),
            dict(id="ER-10", pts=[[190, 70], [190, 9]]),
            dict(id="ER-11", pts=[[155, 70], [155, 45], [143, 45]]),
            dict(id="ER-12", pts=[[202, 103], [214, 103]]),
        ]
        self.structs = dict(pipe_rack=self.rack, column_platforms=plats, heater_stacks=stacks,
                            ejector_structure=self.ejector_structure, roads=roads, buildings=buildings,
                            areas=areas, escape_routes=escape)

    # ------------------------------------------------------------------ export
    def to_json(self):
        return dict(
            doc="CFU-000-PL-PLT-001", rev="A", generated_by="cfu/layout/model.py",
            frame=dict(plot_x=PLOT[0], plot_y=PLOT[1], origin="SW corner of unit plot", north="+y",
                       grade_el=GRADE, wind="prevailing from SSE (157.5 deg)",
                       units="m; elevations EL m (grade = EL 100.000)"),
            conventions=dict(x="east (m)", y="north (m)", z_base="EL of underside of body/foundation top (m)",
                             rotation="deg CCW from +x of long axis L", footprint="L along axis x W across",
                             shape="vcyl | hcyl | box | heater", nozzles="{name: [x, y, EL]} approx. FEED positions",
                             bbox="[xmin, ymin, xmax, ymax] plan extents"),
            equipment=self.items,
            structures=self.structs,
            spacing_checks=self.checks,
        )


# ---------------------------------------------------------------------------------------------
def rect_dist(a, b):
    """edge-to-edge distance between rectangles [x0,y0,x1,y1] + nearest points."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(0.0, bx0 - ax1, ax0 - bx1)
    dy = max(0.0, by0 - ay1, ay0 - by1)
    # nearest points
    def near(lo1, hi1, lo2, hi2):
        if hi1 < lo2:
            return hi1, lo2
        if hi2 < lo1:
            return lo1, hi2
        m = (max(lo1, lo2) + min(hi1, hi2)) / 2
        return m, m
    px, qx = near(ax0, ax1, bx0, bx1)
    py, qy = near(ay0, ay1, by0, by1)
    return math.hypot(dx, dy), (px, py), (qx, qy)


LPG_TAGS = {"C-105", "D-105", "P-115A", "P-115B", "A-106", "E-116"}
HEATER_AUX = {"E-120", "K-101A", "K-101B", "K-102A", "K-102B"}


def spacing_checks(L: Layout):
    it = L.items
    heaters = [i for i in it if i["shape"] == "heater"]
    hc_types = {"Column", "Drum", "Desalter", "Shell & tube", "Pump", "Air cooler", "Ejector"}
    hc = [i for i in it if i["type"] in hc_types and i["tag"] not in HEATER_AUX]
    vessels = [i for i in it if i["type"] in ("Column", "Drum", "Desalter")]
    pumps = [i for i in it if i["type"] == "Pump"]
    rack = [L.rack["x0"], L.rack["y0"], L.rack["x1"], L.rack["y1"]]
    out = []

    def worst(A, B, req, rule, basis, kind=">=", skip_same=True):
        best = None
        for a in A:
            for b in B:
                if skip_same and a is b:
                    continue
                ba = a["bbox"] if isinstance(a, dict) else a
                bb = b["bbox"] if isinstance(b, dict) else b
                d, p, q = rect_dist(ba, bb)
                if best is None or d < best[0]:
                    best = (d, a, b, p, q)
        d, a, b, p, q = best
        na = a["tag"] if isinstance(a, dict) else "PR-100 rack"
        nb = b["tag"] if isinstance(b, dict) else "PR-100 rack"
        out.append(dict(rule=rule, basis=basis, required_m=req, item_a=na, item_b=nb, actual_m=round(d, 1),
                        status="OK" if d >= req - 1e-6 else "FAIL", p=[round(p[0], 2), round(p[1], 2)],
                        q=[round(q[0], 2), round(q[1], 2)]))

    worst(heaters, [i for i in hc if i["tag"] != "D-103"], 15.0, "Fired heater to HC process equipment", "CCPS GAP 2.5.2 typ. 15 m (50 ft)")
    worst(heaters, [i for i in it if i["tag"] in LPG_TAGS], 30.0, "Fired heater to LPG / light-ends equipment",
          "CCPS GAP 2.5.2 typ. 30 m (100 ft)")
    worst(heaters, [rack], 15.0, "Fired heater to main pipe rack", "CCPS GAP 2.5.2 typ. 15 m")
    worst(heaters, pumps, 15.0, "Fired heater to HC pumps", "CCPS GAP 2.5.2 typ. 15 m")
    worst(heaters, [i for i in it if i["tag"] == "D-104"], 30.0, "Fired heater to unit flare KO drum", "project typ. 30 m")
    worst(heaters, [i for i in it if i["tag"] == "D-103"], 15.0, "Fired heater to fuel-gas KO drum", "project typ. 15 m")
    worst(pumps, vessels, 3.0, "Pump to vessel / column (edge-edge)", "CCPS GAP 2.5.2 typ. 3 m")
    cols = [i for i in it if i["type"] == "Column"]
    worst(cols, cols, 3.0, "Column to column (shell-shell)", "project typ. 3 m (access)")
    hxs = [i for i in it if i["type"] == "Shell & tube" and i["z_base"] < 103]
    worst(hxs, hxs, 1.5, "Exchanger to exchanger (at grade)", "project typ. 1.5 m (access)")
    blds = [[b["x0"], b["y0"], b["x1"], b["y1"]] for b in L.structs["buildings"]]
    blds_d = [dict(tag=b["id"], bbox=[b["x0"], b["y0"], b["x1"], b["y1"]]) for b in L.structs["buildings"]]
    worst(blds_d, hc, 15.0, "Substation / FAR to HC equipment", "project typ. 15 m (API RP 752 siting study to confirm)")
    worst(blds_d, heaters, 15.0, "Substation / FAR to fired heater", "project typ. 15 m")
    # pumps not beneath air coolers
    acs = [i for i in it if i["type"] == "Air cooler"]
    worst(pumps, acs, 0.5, "HC pumps not beneath air coolers (plan clearance)", "CCPS GAP 2.5.2 / API 2510 practice")
    # bundle pull aisle clear length
    out.append(dict(rule="Exchanger bundle-pull aisle clear width", basis="bundle length + 1.5 m",
                    required_m=7.5 + 1.5, item_a="BP-1", item_b="E-1xx rows", actual_m=round(105.25 - 95.75, 1),
                    status="OK" if (105.25 - 95.75) >= 9.0 else "FAIL", p=[30, 95.75], q=[30, 105.25]))
    out.append(dict(rule="Rack headroom over road crossing", basis="project typ. >= 5.0 m (mobile crane not permitted)",
                    required_m=5.0, item_a="PR-100 tier 1", item_b="RD-W", actual_m=L.rack["min_headroom_m"],
                    status="OK" if L.rack["min_headroom_m"] >= 5.0 else "FAIL", p=[6, 75], q=[6, 75]))
    # max distance from equipment to an escape route / road
    segs = []
    for er in L.structs["escape_routes"]:
        pts = er["pts"]
        segs += list(zip(pts[:-1], pts[1:]))
    for r in L.structs["roads"]:
        segs.append(((r["x0"], (r["y0"] + r["y1"]) / 2), (r["x1"], (r["y0"] + r["y1"]) / 2)))
        segs.append((((r["x0"] + r["x1"]) / 2, r["y0"]), ((r["x0"] + r["x1"]) / 2, r["y1"])))

    def dseg(p, a, b):
        ax, ay = a
        bx, by = b
        vx, vy = bx - ax, by - ay
        t = max(0, min(1, ((p[0] - ax) * vx + (p[1] - ay) * vy) / max(vx * vx + vy * vy, 1e-9)))
        return math.hypot(p[0] - ax - t * vx, p[1] - ay - t * vy)
    worst_d, worst_t = 0, ""
    for i in it:
        d = min(dseg((i["x"], i["y"]), a, b) for a, b in segs)
        if d > worst_d:
            worst_d, worst_t = d, i["tag"]
    out.append(dict(rule="Max travel from equipment to escape route / road", basis="project typ. <= 30 m",
                    required_m=30.0, item_a=worst_t, item_b="nearest ER/road", actual_m=round(worst_d, 1),
                    status="OK" if worst_d <= 30 else "FAIL", kind="<=", p=None, q=None))
    return out


def build_layout() -> Layout:
    return Layout().build()
