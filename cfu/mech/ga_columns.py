"""Column GA drawings: CFU-100-ME-GA-001 (C-101), -002 (C-102/103/104), -003 (C-105/C-106),
CFU-200-ME-GA-004 (C-201)."""
from __future__ import annotations

import math

from ..drawing.sheet import Sheet
from .common import OUT, nps_str
from .draw import BLUE, DIM, GREY, MED, THIN, THK, Pen

GA_DIR = OUT / "ga"


def _seg_R(g, z):
    for s in g["segs"]:
        if s["z0"] - 1e-6 <= z <= s["z1"] + 1e-6:
            if s["kind"] == "cyl":
                return s["D"] / 2
            f = (z - s["z0"]) / (s["z1"] - s["z0"])
            return (s["D0"] + f * (s["D1"] - s["D0"])) / 2
    return (g["D_top"] if z > g["H"] else g["D_bot"]) / 2


class ColumnView:
    """Elevation of a vertical column at scale s (mm per m), grade at y_grade, centre cx."""

    def __init__(self, P: Pen, g, r, cx, y_grade, s):
        self.P, self.g, self.r, self.cx, self.yg, self.s = P, g, r, cx, y_grade, s
        self.sk = r["skirt_h"]

    def y(self, z):            # z above BTL (m)
        return self.yg - (self.sk + z) * self.s

    def R(self, z):
        return _seg_R(self.g, z) * self.s

    def draw(self, tray_numbers=True, platforms=True, label_side_offset=16, show_levels=True, dims=True,
             nozzle_labels=True, elev_x=None, compact=False):
        P, g, r, cx, s = self.P, self.g, self.r, self.cx, self.s
        H = g["H"]
        Rb, Rt = g["D_bot"] / 2 * s, g["D_top"] / 2 * s
        yb, yt = self.y(0), self.y(H)
        # grade
        P.line((cx - Rb - 14, self.yg), (cx + Rb + 14, self.yg), w=THK)
        P.hatch([(cx - Rb - 14, self.yg), (cx + Rb + 14, self.yg), (cx + Rb + 14, self.yg + 2.2),
                 (cx - Rb - 14, self.yg + 2.2)], spacing=1.2, angle=45, lw=0.12)
        # skirt
        Rsk = r["skirt"]["D_mm"] / 2000 * s
        P.line((cx - Rsk, self.yg), (cx - Rsk, yb), w=THK)
        P.line((cx + Rsk, self.yg), (cx + Rsk, yb), w=THK)
        P.rect(cx - Rsk - 1.2, self.yg - 0.9, 2 * Rsk + 2.4, 0.9, lw=MED, fill="#bbbbbb")
        # fireproofing hatch strips
        for sx in (-1, 1):
            x0 = cx + sx * Rsk
            P.hatch([(x0, self.yg - 1), (x0 + sx * 0.9, self.yg - 1), (x0 + sx * 0.9, yb + 2), (x0, yb + 2)],
                    spacing=0.9, angle=60, lw=0.1)
        # access opening + vents
        ao = 0.6 * s
        ya = self.yg - min(1.5, self.sk * 0.35) * s
        P.rect(cx - ao / 2 - Rsk * 0.45, ya - ao * 1.6, ao, ao * 1.6, lw=THIN)
        if not compact:
            P.leader([(cx - Rsk * 0.45, ya - ao * 0.8), (cx - Rsk - 6, ya - ao * 2.2)], "ACCESS OPENING\n24\" (x2)",
                     1.7, "end")
        # bottom head
        hb = g["D_bot"] / 4 * s
        pts = [(cx + Rb * math.cos(t), yb + hb * math.sin(t)) for t in [math.pi * i / 40 for i in range(41)]]
        P.pline(pts, w=THK)
        # shell
        for sgm in g["segs"]:
            y0, y1 = self.y(sgm["z0"]), self.y(sgm["z1"])
            if sgm["kind"] == "cyl":
                R = sgm["D"] / 2 * s
                P.line((cx - R, y0), (cx - R, y1), w=THK)
                P.line((cx + R, y0), (cx + R, y1), w=THK)
            else:
                R0, R1 = sgm["D0"] / 2 * s, sgm["D1"] / 2 * s
                P.line((cx - R0, y0), (cx - R1, y1), w=THK)
                P.line((cx + R0, y0), (cx + R1, y1), w=THK)
            for yy, RR in ((y0, self.R(sgm["z0"])), (y1, self.R(sgm["z1"]))):
                P.line((cx - RR, yy), (cx + RR, yy), w=THIN, dash="2,1")
        # top head
        ht = g["D_top"] / 4 * s
        pts = [(cx + Rt * math.cos(t), yt - ht * math.sin(t)) for t in [math.pi * i / 40 for i in range(41)]]
        P.pline(pts, w=THK)
        # centre line
        P.ctr((cx, self.yg + 4), (cx, yt - ht - 5))
        # internals
        self._trays(tray_numbers)
        self._internals()
        if show_levels:
            self._levels()
        if platforms:
            self._platforms()
        self._nozzles(nozzle_labels, label_side_offset)
        if dims:
            self._dims(elev_x)
        return self

    # ------------------------------------------------------------------
    def _trays(self, numbers):
        P, g, cx, s = self.P, self.g, self.cx, self.s
        trays = g["trays"]
        for i, t in enumerate(trays):
            yy = self.y(t["z"])
            R = self.R(t["z"]) - 0.25
            P.line((cx - R, yy), (cx + R, yy), w=0.3)
            dc = 0.45 * t["TS"] * s
            if t["passes"] == 1:
                xs = [cx + (R * 0.78 if t["no"] % 2 else -R * 0.78)]
            elif t["passes"] == 2:
                xs = [cx - R * 0.8, cx + R * 0.8] if t["no"] % 2 else [cx - R * 0.12, cx + R * 0.12]
            else:
                xs = [cx - R * 0.85, cx - R * 0.05, cx + R * 0.85] if t["no"] % 2 else [cx - R * 0.45, cx + R * 0.45]
            for x in xs:
                P.line((x, yy), (x, yy + dc), w=0.18)
            if numbers:
                P.text(str(t["no"]), cx - R + 0.6, yy - 0.5, 1.45 if s <= 10 else 2.0, color=BLUE)

    def _internals(self):
        P, g, cx, s = self.P, self.g, self.cx, self.s
        for it in g.get("internals", []):
            k = it["kind"]
            if k == "bed":
                y0, y1 = self.y(it["z0"]), self.y(it["z1"])
                R0, R1 = self.R(it["z0"]) - 0.3, self.R(it["z1"]) - 0.3
                pts = [(cx - R1, y1), (cx + R1, y1), (cx + R0, y0), (cx - R0, y0)]
                P.pline(pts, w=0.3, close=True, fill="#f3f0e6")
                P.hatch(pts, spacing=1.4, angle=50, cross=True, lw=0.1)
                P.line((cx - R0, y0 + 0.6), (cx + R0, y0 + 0.6), w=0.5)      # support grid
            elif k == "dist":
                yy = self.y(it["z"])
                R = self.R(it["z"]) - 0.6
                P.line((cx - R, yy), (cx + R, yy), w=0.35, dash="1.5,0.8")
                n = max(4, int(2 * R / 3))
                for i in range(n):
                    x = cx - R + (i + 0.5) * 2 * R / n
                    P.pline([(x, yy), (x - 0.6, yy + 1.0), (x + 0.6, yy + 1.0)], w=0.15, close=True)
            elif k == "coll":
                yy = self.y(it["z"])
                R = self.R(it["z"]) - 0.25
                P.line((cx - R, yy), (cx + R, yy), w=0.5)
                P.line((cx - R, yy + 1.2), (cx - R + 2.5, yy + 1.2), w=0.3)
                n = 3
                for i in range(n):
                    x = cx - R + (i + 1) * 2 * R / (n + 1)
                    P.rect(x - 1.4, yy - 3.2, 2.8, 3.2, lw=0.25, fill="white")
                    P.line((x - 2.0, yy - 4.0), (x + 2.0, yy - 4.0), w=0.3)
            elif k == "demister":
                y0, y1 = self.y(it["z0"]), self.y(it["z1"])
                R = self.R(it["z"]) - 0.3
                pts = [(cx - R, y1), (cx + R, y1), (cx + R, y0), (cx - R, y0)]
                P.pline(pts, w=0.25, close=True)
                P.hatch(pts, spacing=0.7, angle=90, lw=0.1)
            elif k in ("horn", "flash"):
                if k == "flash":
                    z0, z1 = it["z1"] - 2.6, it["z1"] - 0.4
                else:
                    z0, z1 = it["z0"], it["z1"]
                y0, y1 = self.y(z0), self.y(z1)
                R = self.R((z0 + z1) / 2)
                w = max(0.12 * R, 2.5)
                for sx in (-1, 1):
                    P.rect(cx + sx * (R - 0.3) - (w if sx > 0 else 0), y1, w, y0 - y1, lw=0.3, dash="1.5,0.8")
            elif k == "steam":
                yy = self.y(it["z"])
                R = self.R(it["z"]) * 0.7
                P.line((cx - R, yy), (cx + R * 1.43, yy), w=0.45)
                for i in range(6):
                    x = cx - R + i * 2 * R / 5
                    P.circle((x, yy + 0.5), 0.3, lw=0.1, fill="black")
            elif k == "quench":
                yy = self.y(it["z"])
                R = self.R(it["z"]) * 0.7
                P.line((cx - R * 1.43, yy), (cx + R, yy), w=0.45, dash="2,0.6")
            elif k == "vortex":
                yy = self.y(0) + self.g["D_bot"] / 4 * self.s - 1.2
                P.rect(cx - 2.2, yy - 1.4, 4.4, 1.4, lw=0.25)
                P.line((cx - 2.2, yy - 1.4), (cx + 2.2, yy), w=0.15)
                P.line((cx + 2.2, yy - 1.4), (cx - 2.2, yy), w=0.15)
            elif k == "draw":
                yy = self.y(it["z"])
                R = self.R(it["z"])
                nz = [n for n in g["nozzles"] if n["side"] in ("L", "R") and abs(n["z"] - it["z"]) < 0.05]
                sx = -1 if (nz and nz[0]["side"] == "L") else 1
                x0 = cx + sx * (R - 0.3) - (4.2 if sx > 0 else 0)
                P.rect(x0, yy, 4.2, 1.6, lw=0.25, fill="#dfe8f4")

    def _levels(self):
        P, g, cx = self.P, self.g, self.cx
        lv = g["levels"]
        R = self.R(0)
        for k in ("LLL", "NLL", "HLL"):
            yy = self.y(lv[k])
            P.line((cx + R * 0.15, yy), (cx + R * 0.75, yy), w=0.2, color="#1060c0", dash="1.2,0.6")
            P.pline([(cx + R * 0.6, yy), (cx + R * 0.6 - 0.7, yy - 1.0), (cx + R * 0.6 + 0.7, yy - 1.0)], w=0.15,
                    close=True, color="#1060c0")
            P.text(k, cx + R * 0.62 + 1.0, yy - 0.3, 1.5, color="#1060c0")

    def _platforms(self):
        P, g, cx, s = self.P, self.g, self.cx, self.s
        ins = self.r["W"]["ins_mm"] / 1000
        plats = sorted(g["platforms"])
        for zp in plats:
            if zp > g["H"]:
                continue
            zc = min(max(zp, -0.5), g["H"])
            R = self.R(zc) + (ins + 0.15) * s
            yy = self.y(zp)
            for sx in (-1, 1):
                x0, x1 = cx + sx * R, cx + sx * (R + 1.2 * s)
                P.line((x0, yy), (x1, yy), w=0.8, color="#505050")
                P.line((x1, yy), (x1, yy - 1.07 * s), w=0.15, color="#505050")
                P.line((x0, yy - 1.07 * s), (x1, yy - 1.07 * s), w=0.15, color="#505050")
                P.line((x0, yy - 0.55 * s), (x1, yy - 0.55 * s), w=0.08, color="#505050")
        # ladder (left side) from grade to top platform with cages
        xl = cx - (self.R(0) + (ins + 1.5) * s)
        ytop = self.y(plats[-1]) if plats else self.y(g["H"])
        P.line((xl, self.yg), (xl, ytop), w=0.15, dash="0.8,0.8")
        P.line((xl - 0.45 * s, self.yg), (xl - 0.45 * s, ytop), w=0.15, dash="0.8,0.8")

    def _nozzles(self, labels, off):
        P, g, cx, s = self.P, self.g, self.cx, self.s
        ins = self.r["W"]["ins_mm"] / 1000
        top = [n for n in g["nozzles"] if n["side"] == "T"]
        topx = {}
        if top:
            Rt = g["D_top"] / 2 * s
            big = max(top, key=lambda n: n["nps"])
            others = [n for n in top if n is not big]
            topx[big["mark"]] = 0.0
            for i, n in enumerate(others):
                sgn = -1 if i % 2 == 0 else 1
                topx[n["mark"]] = sgn * Rt * (0.45 + 0.18 * (i // 2))
        mw_i = 0
        for n in g["nozzles"]:
            d = max(n["nps"] * 0.0254 * s, 0.7)
            if n["side"] in ("L", "R"):
                sx = -1 if n["side"] == "L" else 1
                yy = self.y(n["z"])
                R = self.R(n["z"])
                L = max(0.7 * s, (ins + 0.35) * s)
                x0, x1 = cx + sx * R, cx + sx * (R + L)
                P.line((x0, yy - d / 2), (x1, yy - d / 2), w=0.3)
                P.line((x0, yy + d / 2), (x1, yy + d / 2), w=0.3)
                P.line((x1, yy - d / 2 - 0.7), (x1, yy + d / 2 + 0.7), w=0.6)
                if labels:
                    xl = cx + sx * (R + (ins + 1.55) * s + 1.0)
                    P.line((x1, yy), (xl, yy), w=DIM)
                    r_ = P.bubble(xl + sx * 2.6, yy, n["mark"], size=1.6)
                    P.text(nps_str(n["nps"]) if n.get("qty", 1) == 1 else f"{n['qty']}x{nps_str(n['nps'])}",
                           xl + sx * (2.6 + r_ + 0.6), yy + 0.6, 1.6, "start" if sx > 0 else "end")
            elif n["side"] == "T":
                Rt = g["D_top"] / 2 * s
                ht = g["D_top"] / 4 * s
                xo = topx[n["mark"]]
                yh = self.y(g["H"]) - ht * math.sqrt(max(0, 1 - (xo / Rt) ** 2))
                L = 0.8 * s
                P.line((cx + xo - d / 2, yh), (cx + xo - d / 2, yh - L), w=0.3)
                P.line((cx + xo + d / 2, yh), (cx + xo + d / 2, yh - L), w=0.3)
                P.line((cx + xo - d / 2 - 0.7, yh - L), (cx + xo + d / 2 + 0.7, yh - L), w=0.6)
                if labels:
                    lab = n["mark"]
                    yl = yh - L - 3.2 - (abs(xo) > 0) * 0
                    P.bubble(cx + xo, yl, lab, size=1.5)
            elif n["side"] == "B":
                hb = g["D_bot"] / 4 * s
                yy = self.y(0) + hb
                L = min(1.6 * s, (self.sk - 0.6) * s)
                P.line((cx - d / 2, yy), (cx - d / 2, yy + L * 0.6), w=0.3)
                P.line((cx + d / 2, yy), (cx + d / 2, yy + L * 0.6), w=0.3)
                P.path(f"M {cx - d / 2} {yy + L * 0.6} Q {cx - d / 2} {yy + L * 0.6 + d * 1.5} {cx + 2 * d} "
                       f"{yy + L * 0.6 + d * 1.5}", lw=0.3)
                P.path(f"M {cx + d / 2} {yy + L * 0.6} Q {cx + d / 2} {yy + L * 0.6 + d * 0.5} {cx + 2 * d} "
                       f"{yy + L * 0.6 + d * 0.5}", lw=0.3)
                Rsk = self.r["skirt"]["D_mm"] / 2000 * s
                xe = cx + Rsk + 2.0
                P.line((cx + 2 * d, yy + L * 0.6 + d * 1.5), (xe, yy + L * 0.6 + d * 1.5), w=0.3)
                P.line((cx + 2 * d, yy + L * 0.6 + d * 0.5), (xe, yy + L * 0.6 + d * 0.5), w=0.3)
                P.line((xe, yy + L * 0.6 + d * 0.5 - 0.7), (xe, yy + L * 0.6 + d * 1.5 + 0.7), w=0.6)
                if labels:
                    P.bubble(xe + 3.6, yy + L * 0.6 + d, n["mark"], size=1.6)
            elif n["side"] == "F":
                yy = self.y(n["z"])
                R = self.R(n["z"])
                xo = cx + (R * 0.42 if mw_i % 2 == 0 else -R * 0.42)
                mw_i += 1
                P.circle((xo, yy), d / 2, lw=0.35, fill="white")
                P.circle((xo, yy), d / 2 * 0.72, lw=0.15)
                P.line((xo - d / 2 - 0.6, yy), (xo + d / 2 + 0.6, yy), w=0.1, color=GREY)
                if labels:
                    P.text(n["mark"], xo, yy - d / 2 - 0.6, 1.6, "middle", bold=True)

    def _dims(self, elev_x=None):
        P, g, r, cx, s = self.P, self.g, self.r, self.cx, self.s
        H = g["H"]
        Rmax = max(g["Ds"]) / 2 * s
        xd = cx - Rmax - 1.6 * s - 10
        yb, yt = self.y(0), self.y(H)
        P.dim_v(xd, self.yg, yb, f"SKIRT {r['skirt_h'] * 1000:.0f}", ext_from=cx - Rmax * 0.5)
        P.dim_v(xd, yb, yt, f"{H * 1000:.0f} T/T", ext_from=None)
        for yy in (yb, yt):
            P.line((xd - 1.2, yy), (cx - self.R(0 if yy == yb else H), yy), w=DIM)
        if len(g["segs"]) > 1:
            xd2 = xd + 6.5
            for sg in g["segs"]:
                y0, y1 = self.y(sg["z0"]), self.y(sg["z1"])
                P.dim_v(xd2, y0, y1, f"{(sg['z1'] - sg['z0']) * 1000:.0f}", size=1.7)
        # diameters
        done = set()
        for sg in g["segs"]:
            if sg["kind"] != "cyl" or sg["D"] in done:
                continue
            done.add(sg["D"])
            zm = sg["z0"] + (sg["z1"] - sg["z0"]) * (0.5 if len(g["segs"]) > 1 else 0.62)
            # avoid trays: shift to midway between two trays
            tz = sorted(t["z"] for t in g["trays"] if sg["z0"] < t["z"] < sg["z1"])
            mwz = [n["z"] for n in g["nozzles"] if n["kind"] == "MW"]
            if len(tz) > 2:
                gaps = [((a + b) / 2) for a, b in zip(tz, tz[1:]) if all(abs((a + b) / 2 - m) > 0.6 for m in mwz)]
                mid = (sg["z0"] + sg["z1"]) / 2
                if gaps:
                    zm = min(gaps, key=lambda q: abs(q - mid))
            yy = self.y(zm)
            R = sg["D"] / 2 * s
            P.rect(cx - 7.5, yy - 2.6, 15, 2.4, lw=0, fill="white")
            P.dim_h(yy, cx - R, cx + R, f"ID {sg['D'] * 1000:.0f}", size=1.8)
        # elevations
        ex = elev_x if elev_x is not None else cx + Rmax + 1.6 * s + 30
        for zz, lab in ((-r["skirt_h"], "GRADE"), (0, "BTL"), (H, "TTL")):
            yy = self.y(zz)
            P.line((cx + self.R(min(max(zz, 0), H)) + 1, yy), (ex - 1, yy), w=0.1, color=GREY, dash="1,1")
            P.elev(ex, yy, f"{lab} EL {100 + r['skirt_h'] + zz:.3f}", size=1.8, w=24)


def nozzle_rows(g, r):
    rows = []
    for n in g["nozzles"]:
        el = 100 + r["skirt_h"] + n["z"]
        loc = "TOP HEAD" if n["side"] == "T" else "BTM HEAD" if n["side"] == "B" else f"EL {el:.3f}"
        rows.append([n["mark"], str(n.get("qty", 1)), nps_str(n["nps"]), f"{n['rating']}# RF", loc,
                     f"{n['angle']}", n["service"]])
    return rows


def plan_orientation(P: Pen, g, cx, cy, Rmm, title):
    """Nozzle orientation plan (looking down), 0 deg = plant north."""
    P.circle((cx, cy), Rmm, lw=0.5)
    P.circle((cx, cy), Rmm * 0.97, lw=0.15)
    P.ctr((cx - Rmm - 6, cy), (cx + Rmm + 6, cy))
    P.ctr((cx, cy - Rmm - 6), (cx, cy + Rmm + 6))
    for a, lab in ((0, "0 (N)"), (90, "90"), (180, "180"), (270, "270")):
        x = cx + (Rmm - 6) * math.sin(math.radians(a))
        y = cy - (Rmm - 6) * math.cos(math.radians(a))
        P.text(lab, x, y + 0.8, 1.8, "middle", color=GREY)
    used = {}
    for n in g["nozzles"]:
        if n["side"] in ("T", "B"):
            continue
        a = n["angle"] if n["side"] != "F" else (315 if int(n["mark"][1:].split("/")[0] or 1) % 2 else 45)
        k = a
        used[k] = used.get(k, 0) + 1
        rr = Rmm + 2 + (used[k] - 1) * 6.5
        x0 = cx + Rmm * math.sin(math.radians(a))
        y0 = cy - Rmm * math.cos(math.radians(a))
        x1 = cx + rr * math.sin(math.radians(a))
        y1 = cy - rr * math.cos(math.radians(a))
        P.line((x0, y0), (x1, y1), w=0.3)
        P.bubble(x1 + 2.6 * math.sin(math.radians(a)), y1 - 2.6 * math.cos(math.radians(a)), n["mark"], size=1.35)
    # north arrow
    P.pline([(cx - Rmm - 14, cy - Rmm - 2), (cx - Rmm - 12, cy - Rmm - 8), (cx - Rmm - 10, cy - Rmm - 2)], w=0.3,
            close=True, fill="black")
    P.text("PN", cx - Rmm - 12, cy - Rmm - 9.5, 2.0, "middle", bold=True)
    P.text(title, cx, cy + Rmm + 15, 2.4, "middle", bold=True)
    P.text("(manways alternate 315 / 45 deg - platform side)", cx, cy + Rmm + 18.5, 1.8, "middle")


def design_rows(g, r):
    e = g["e"]
    W = r["W"]
    rows = [("Service", e["service"]), ("Design pressure", f"{r['Pd']} barg" + (" / FULL VACUUM" if r["fv"] else "")),
            ("Design temperature", f"{r['Td']:.0f} C"), ("Operating P / T", f"{e['op_P']} / {e['op_T']} C"),
            ("Shell material", r["mat"]), ("Cladding / lining", e["moc"][:60]), ("Corrosion allowance", f"{r['CA']} mm"),
            ("Joint efficiency", f"{r['E']} (full RT)"),
            ("Shell thickness", ", ".join(f"{s['t_nom']}" for s in r["segs"]) + " mm (by course, bottom up)"),
            ("Heads (2:1 SE) top / btm", f"{r['heads']['top']['t_nom']} / {r['heads']['bottom']['t_nom']} mm"),
            ("Skirt OD x t x height", f"{r['skirt']['D_mm']:.0f} x {r['skirt']['t_nom']} x {r['skirt_h'] * 1000:.0f} mm"),
            ("Anchor bolts", f"{r['anchor']['n']} x {r['anchor']['size']} on {r['anchor']['Dbc'] * 1000:.0f} BCD"),
            ("Hydrotest (top / btm)", f"{r['hydro']['Pt_top']:.2f} / {r['hydro']['Pt_bot']:.2f} barg"),
            ("Insulation", f"{W['ins_mm']} mm mineral wool" if W["ins_mm"] else "none"),
            ("Weight empty / oper.", f"{W['empty'] / 1e3:.0f} / {W['operating'] / 1e3:.0f} t"),
            ("Weight hydrotest", f"{W['hydrotest'] / 1e3:.0f} t"),
            ("Wind base V / M", f"{r['wind']['V_base'] / 1e3:.0f} kN / {r['wind']['M_base'] / 1e3:.0f} kNm"),
            ("Code", "ASME VIII Div.1, U-stamp; ASCE 7-16")]
    return rows


COMMON_NOTES = ["Dimensions in mm, elevations in m. Grade = EL 100.000.",
                "Thicknesses are FEED minimum nominal (CFU-000-ME-CAL-001); fabricator to verify.",
                "Nozzle orientations preliminary - to be confirmed by piping study.",
                "Platforms 1200 wide, 60 % wrap; caged ladders not shown in full.",
                "Datasheet CFU-000-ME-DS-001; weights in data/mech.json."]


# ---------------------------------------------------------------------------
def course_rows(g, r):
    rows = []
    sk = r["skirt_h"]
    rows.append(["Skirt", f"{r['skirt']['D_mm']:.0f} OD", f"{100:.3f}", f"{100 + sk:.3f}", f"{r['skirt']['t_nom']}",
                 "SA-516-70", "fireproofed"])
    rows.append(["Bottom head 2:1", f"{g['D_bot'] * 1000:.0f}", "-", f"{100 + sk:.3f}", f"{r['heads']['bottom']['t_nom']}",
                 r["mat"], ""])
    for sg in r["segs"]:
        rows.append([sg["name"][:26], f"{sg['D_mm']:.0f}" + (" cone" if sg["kind"] == "cone" else ""),
                     f"{100 + sk + sg['z0']:.3f}", f"{100 + sk + sg['z1']:.3f}", f"{sg['t_nom']}", r["mat"],
                     f"t req {sg['t_req']:.1f}" + (f" / ext {sg['t_ext']}" if sg.get("t_ext") else "")])
    rows.append(["Top head 2:1", f"{g['D_top'] * 1000:.0f}", f"{100 + sk + g['H']:.3f}", "-", f"{r['heads']['top']['t_nom']}",
                 r["mat"], ""])
    return rows


def platform_rows(g, r):
    mws = sorted([n for n in g["nozzles"] if n["kind"] == "MW"], key=lambda n: n["z"])
    rows = []
    for i, zp in enumerate(sorted(g["platforms"])):
        serv = [n["mark"] for n in mws if 0.3 < n["z"] - zp < 1.6]
        noz = [n["mark"] for n in g["nozzles"] if n["kind"] != "MW" and n["side"] in ("L", "R") and -0.5 < n["z"] - zp < 2.2]
        rows.append([f"P{i + 1}", f"EL {100 + r['skirt_h'] + zp:.3f}", ", ".join(serv) or ("top head / davit" if zp > g["H"] else "-"),
                     ", ".join(noz[:6])])
    return rows


def weight_rows(r):
    W = r["W"]
    c = W["cat"]
    return [("Shell + heads + nozzles + clad", f"{(c.get('shell', 0) + c.get('heads', 0) + c.get('nozzles', 0) + c.get('clad', 0)) / 1e3:.1f} t"),
            ("Skirt + base ring", f"{c.get('skirt', 0) / 1e3:.1f} t"), ("Internals", f"{c.get('internals', 0) / 1e3:.1f} t"),
            ("Platforms / ladders", f"{c.get('platforms', 0) / 1e3:.1f} t"),
            ("Insulation + fireproofing", f"{(c.get('insulation', 0) + c.get('fireproofing', 0)) / 1e3:.1f} t"),
            ("EMPTY (installed)", f"{W['empty'] / 1e3:.1f} t"), ("OPERATING", f"{W['operating'] / 1e3:.1f} t"),
            ("HYDROTEST (full of water)", f"{W['hydrotest'] / 1e3:.1f} t"),
            ("Wind base shear / moment (ASCE 7, strength)", f"{r['wind']['V_base'] / 1e3:.0f} kN / {r['wind']['M_base'] / 1e3:.0f} kNm"),
            ("Natural frequency / gust factor", f"{r['fn']:.2f} Hz / {r['wind']['G']:.2f}")]


def tray_plan(P, cx, cy, D, s, passes, title):
    R = D / 2 * s
    P.circle((cx, cy), R, lw=0.5)
    P.ctr((cx - R - 4, cy), (cx + R + 4, cy))
    P.ctr((cx, cy - R - 4), (cx, cy + R + 4))
    def chord(x, fill="#dfe8f4"):
        h = math.sqrt(max(R * R - x * x, 0))
        P.line((cx + x, cy - h), (cx + x, cy + h), w=0.4)
    if passes == 4:
        for x in (-0.86 * R, 0.86 * R):
            chord(x)
        P.rect(cx - 0.06 * R, cy - math.sqrt(R * R - (0.06 * R) ** 2), 0.12 * R, 2 * math.sqrt(R * R - (0.06 * R) ** 2),
               lw=0.4, fill="#dfe8f4")
        P.text("SIDE DC", cx - 0.93 * R, cy + 1, 1.5, "middle", rotate=-90)
        P.text("CENTRE DC", cx, cy + 1, 1.5, "middle", rotate=-90)
        P.text("ODD TRAYS", cx, cy + R + 8, 1.8, "middle")
        cx2 = cx + 2 * R + 14
        P.circle((cx2, cy), R, lw=0.5)
        P.ctr((cx2 - R - 4, cy), (cx2 + R + 4, cy))
        for x in (-0.45 * R, 0.45 * R):
            P.rect(cx2 + x - 0.06 * R, cy - math.sqrt(R * R - (abs(x) + 0.06 * R) ** 2), 0.12 * R,
                   2 * math.sqrt(R * R - (abs(x) + 0.06 * R) ** 2), lw=0.4, fill="#dfe8f4")
        P.text("OFF-CENTRE DC", cx2 + 0.45 * R + 2.5, cy + 1, 1.5, "middle", rotate=-90)
        P.text("EVEN TRAYS", cx2, cy + R + 8, 1.8, "middle")
        P.text(title, (cx + cx2) / 2, cy - R - 7, 2.3, "middle", bold=True)
    else:
        for x in (-0.8 * R, 0.8 * R):
            chord(x)
        P.text(title, cx, cy - R - 7, 2.3, "middle", bold=True)


def ga_c101(calc):
    g, r = calc["geoms"]["C-101"], calc["columns"]["C-101"]
    sh = Sheet("A1", "COLUMN GENERAL ARRANGEMENT", "C-101 ATMOSPHERIC CRUDE FRACTIONATOR", "CFU-100-ME-GA-001",
               scale="1:100", discipline="MECHANICAL", notes=COMMON_NOTES + [
                   "Trays 1-5 and top head Monel 400 lined; 410S clad below tray 10.",
                   f"Swage 30 deg half-angle in flash zone; tray 36 {((g['cone'][0] - g['trays'][35]['z']) * 1000):.0f} below junction.",
                   "Draw sumps (shaded) at trays 3, 10, 13, 22, 25, 32."])
    P = Pen(sh)
    s = 10.0                                   # 1:100 -> 10 mm per m
    y_grade = 530
    cx = 118
    cv = ColumnView(P, g, r, cx, y_grade, s).draw(elev_x=196)
    _callouts_c101(P, cv)
    P.text("ELEVATION (DEVELOPED) 1:100", cx, 548, 2.8, "middle", bold=True)
    x0, fs, rh = 250, 2.15, 3.6
    yb = P.table(x0, 20, ["MARK", "QTY", "SIZE", "RATING", "LOCATION", "ORIENT", "SERVICE"], nozzle_rows(g, r),
                 [13, 8, 11, 17, 23, 13, 125], title="NOZZLE SCHEDULE", fs=fs, rh=rh)
    rows = []
    trays_by = {t["no"]: t for t in g["trays"]}
    for sec in g["sections"]:
        a_, b_ = (int(x) for x in sec["trays"].split("-"))
        D = trays_by[a_]["D"]
        A = math.pi / 4 * D ** 2
        flood = sec["Q_v_m3s"] / (0.85 * A * sec["u_flood"]) * 100
        rows.append([sec["name"], sec["trays"], f"{sec['TS_mm']}", f"{sec['V_kg_h'] / 1000:.0f}", f"{sec['L_kg_h'] / 1000:.0f}",
                     f"{sec['FLV']:.3f}", f"{sec['u_flood']:.2f}", f"{sec['D_calc']:.2f}", f"{D:.2f}", f"{sec['passes']}",
                     f"{flood:.0f}"])
    yb = P.table(x0, yb + 5, ["SECTION", "TRAYS", "TS mm", "V t/h", "L t/h", "FLV", "u flood", "D calc", "D sel.",
                              "PASSES", "% FLOOD"], rows, [36, 15, 15, 16, 16, 16, 17, 17, 16, 15, 31],
                 title="TRAY HYDRAULIC SECTIONS (PROCESS SIZING; % FLOOD AT SELECTED ID, 85 % NET AREA)", fs=fs, rh=rh)
    yb = P.table(x0, yb + 5, ["COMPONENT", "ID mm", "FROM EL", "TO EL", "t mm", "MATERIAL", "REMARK"], course_rows(g, r),
                 [44, 22, 25, 25, 13, 30, 51], title="SHELL COURSE / THICKNESS SCHEDULE (CFU-000-ME-CAL-001)",
                 fs=fs, rh=rh)
    yb = P.table(x0, yb + 5, ["PLATF.", "ELEVATION", "SERVES MANWAY", "NOZZLES ACCESSED"], platform_rows(g, r),
                 [16, 30, 40, 124], title="PLATFORM SCHEDULE (1200 WIDE, 60 % WRAP)", fs=fs, rh=rh)
    plan_orientation(P, g, 555, 92, 34.5, "NOZZLE ORIENTATION PLAN 1:100")
    tray_plan(P, 503, 222, g["D_top"], 10.0, 4, "TYPICAL 4-PASS TRAY ARRANGEMENT (ID 6900) 1:100")
    legend(P, 651, 128, W=175)
    P.kv_table(651, 205, weight_rows(r), [95, 80], title="WEIGHTS & LOADS", fs=fs, rh=3.45)
    flash_section(P, g, 320, 400, s)
    base_plan(P, r, 425, 400, s)
    P.kv_table(651, 20, [("Trays 1-3, 11-13, 23-25 (PA)", "760"), ("Other rectifying trays", "610"),
                         ("Flash zone (tray 35-36)", f"{g['fz'] * 1000:.0f}"), ("Stripping trays 36-41", "610"),
                         ("Top TL to tray 1", f"{g['top_space'] * 1000:.0f}")], [60, 115], title="TRAY SPACING (mm)",
               fs=fs, rh=3.45)
    P.kv_table(651, 48, design_rows(g, r), [50, 125], title="DESIGN DATA", fs=fs, rh=3.45)
    return sh


def flash_section(P, g, cx, cy, s, D=None):
    """Plan section through the flash zone showing the tangential feed and vapour horn."""
    R = (D or g["D_top"]) / 2 * s
    P.circle((cx, cy), R, lw=0.5)
    P.circle((cx, cy), R + 0.6, lw=0.2)
    P.ctr((cx - R - 5, cy), (cx + R + 5, cy))
    P.ctr((cx, cy - R - 5), (cx, cy + R + 5))
    Ri = R * 0.80
    P.circle((cx, cy), Ri, lw=0.3, dash="1.5,0.8")
    feed = next(n for n in g["nozzles"] if n["mark"] == "N1")
    d = feed["nps"] * 0.0254 * s
    yy = cy - R + d / 2 + 0.5
    P.line((cx + 2, cy - R + 0.5), (cx + R + 12, cy - R + 0.5), w=0.35)
    P.line((cx + 2, cy - R + 0.5 + d), (cx + R + 12, cy - R + 0.5 + d), w=0.35)
    P.line((cx + R + 12, cy - R - 0.4), (cx + R + 12, cy - R + d + 1.4), w=0.7)
    for k in range(6):
        a = math.radians(200 + k * 30)
        P.arrow((cx + (Ri + R) / 2 * math.cos(a + 0.25), cy + (Ri + R) / 2 * math.sin(a + 0.25)),
                (cx + (Ri + R) / 2 * math.cos(a), cy + (Ri + R) / 2 * math.sin(a)), 1.4, color="#1060c0")
    P.bubble(cx + R + 16, cy - R + d / 2 + 0.5, "N1", size=1.6)
    P.leader([(cx - Ri + 1, cy + 4), (cx - R - 6, cy + R + 4)], "VAPOUR HORN\n(ANNULAR, OPEN AT TOP)", 1.8, "end")
    P.text("SECTION THROUGH FLASH ZONE 1:100", cx, cy + R + 12, 2.3, "middle", bold=True)
    P.text("tangential feed, 270 deg horn", cx, cy + R + 15.5, 1.8, "middle")


def base_plan(P, r, cx, cy, s):
    a = r["anchor"]
    Rs = r["skirt"]["D_mm"] / 2000 * s
    Rb = a["Dbc"] / 2 * s
    P.circle((cx, cy), Rs, lw=0.5)
    P.circle((cx, cy), Rb + 2.2, lw=0.3)
    P.circle((cx, cy), Rs - 2.0, lw=0.2)
    P.ctr((cx - Rb - 6, cy), (cx + Rb + 6, cy))
    P.ctr((cx, cy - Rb - 6), (cx, cy + Rb + 6))
    for i in range(a["n"]):
        t = 2 * math.pi * (i + 0.5) / a["n"]
        P.circle((cx + Rb * math.cos(t), cy + Rb * math.sin(t)), 0.6, lw=0.2, fill="black")
    P.dim_h(cy + Rb + 9, cx - Rb, cx + Rb, f"BCD {a['Dbc'] * 1000:.0f}", ext_from=cy, size=1.8)
    P.text("SKIRT BASE / ANCHOR BOLT PLAN 1:100", cx, cy - Rb - 12, 2.3, "middle", bold=True)
    P.text(f"{a['n']} x {a['size']} ASTM F1554 Gr.55", cx, cy + Rb + 15, 1.9, "middle")
    P.text(f"skirt OD {r['skirt']['D_mm']:.0f} x {r['skirt']['t_nom']} mm; base ring by vendor", cx, cy + Rb + 18.5, 1.8,
           "middle")


def legend(P, x, y, W=168):
    P.rect(x, y, W, 4.2, lw=0.35, fill=BLUE)
    P.text("LEGEND", x + 1.2, y + 3.1, 2.4, bold=True, color="white")
    y += 4.2
    P.rect(x, y, W, 62, lw=0.35)
    items = [("tray", "Valve tray with downcomer"), ("bed", "Packed bed (structured / grid)"),
             ("dist", "Liquid distributor"), ("coll", "Collector / chimney tray"), ("lvl", "Liquid level (LLL/NLL/HLL)"),
             ("mw", "Manway (shown on face)"), ("noz", "Nozzle - mark and size"), ("plat", "Platform with handrail"),
             ("sump", "Draw sump"), ("ring", "External stiffening ring")]
    for i, (k, t) in enumerate(items):
        cx = x + 4 + (i % 2) * W / 2
        cy = y + 5 + (i // 2) * 11.5
        if k == "tray":
            P.line((cx, cy), (cx + 14, cy), w=0.3)
            P.line((cx + 12, cy), (cx + 12, cy + 3), w=0.18)
        elif k == "bed":
            pts = [(cx, cy - 2), (cx + 14, cy - 2), (cx + 14, cy + 3), (cx, cy + 3)]
            P.pline(pts, w=0.3, close=True, fill="#f3f0e6")
            P.hatch(pts, spacing=1.4, angle=50, cross=True, lw=0.1)
        elif k == "dist":
            P.line((cx, cy), (cx + 14, cy), w=0.35, dash="1.5,0.8")
            for j in range(4):
                xx = cx + 1.5 + j * 3.6
                P.pline([(xx, cy), (xx - 0.6, cy + 1), (xx + 0.6, cy + 1)], w=0.15, close=True)
        elif k == "coll":
            P.line((cx, cy + 1), (cx + 14, cy + 1), w=0.5)
            P.rect(cx + 5.6, cy - 2.2, 2.8, 3.2, lw=0.25, fill="white")
            P.line((cx + 5, cy - 3), (cx + 9, cy - 3), w=0.3)
        elif k == "lvl":
            P.line((cx, cy), (cx + 14, cy), w=0.2, color="#1060c0", dash="1.2,0.6")
            P.pline([(cx + 7, cy), (cx + 6.3, cy - 1), (cx + 7.7, cy - 1)], w=0.15, close=True, color="#1060c0")
        elif k == "mw":
            P.circle((cx + 7, cy), 2.5, lw=0.35)
            P.circle((cx + 7, cy), 1.8, lw=0.15)
        elif k == "noz":
            P.line((cx, cy - 1), (cx + 5, cy - 1), w=0.3)
            P.line((cx, cy + 1), (cx + 5, cy + 1), w=0.3)
            P.line((cx + 5, cy - 1.7), (cx + 5, cy + 1.7), w=0.6)
            P.bubble(cx + 10, cy, "N1", size=1.6)
        elif k == "plat":
            P.line((cx, cy + 1.5), (cx + 14, cy + 1.5), w=0.8, color="#505050")
            P.line((cx, cy - 2), (cx + 14, cy - 2), w=0.15)
            P.line((cx + 14, cy + 1.5), (cx + 14, cy - 2), w=0.15)
        elif k == "sump":
            P.rect(cx + 2, cy - 0.8, 6, 1.6, lw=0.25, fill="#dfe8f4")
        elif k == "ring":
            P.line((cx, cy - 3), (cx, cy + 3), w=0.5)
            P.rect(cx, cy - 0.4, 5, 0.8, lw=0.2, fill="#606060")
        P.text(t, cx + 18, cy + 0.8, 2.0)


def _callouts_c101(P, cv):
    g = cv.g
    s, cx = cv.s, cv.cx
    zc0, zc1 = g["cone"]
    yy = cv.y((zc0 + zc1) / 2)
    P.leader([(cx - cv.R((zc0 + zc1) / 2) + 0.5, yy), (cx - 70, yy + 8)], "30 DEG SWAGE\n6900/4140", 1.8, "end")
    zf = g["trays"][34]["z"] - 0.95
    P.leader([(cx - cv.R(zf) + 2, cv.y(zf)), (cx - 70, cv.y(zf) - 6)], "FLASH ZONE /\nVAPOUR HORN", 1.8, "end")
    zst = next(i["z"] for i in g["internals"] if i["kind"] == "steam")
    P.leader([(cx - 10, cv.y(zst) + 0.4), (cx - 70, cv.y(zst) + 4)], "STEAM SPARGER", 1.8, "end")
    P.leader([(cx, cv.y(0) + g["D_bot"] / 4 * s - 2), (cx - 70, cv.y(0) + 7)], "VORTEX BREAKER", 1.8, "end")
    P.leader([(cx - 30, cv.y(g["trays"][2]["z"]) + 0.8), (cx - 70, cv.y(g["trays"][2]["z"]) + 8)],
             "MONEL LINED\nTRAYS 1-5 + HEAD", 1.8, "end")


# ---------------------------------------------------------------------------
def ga_strippers(calc):
    sh = Sheet("A1", "COLUMN GENERAL ARRANGEMENT", "C-102 / C-103 / C-104 SIDE STRIPPERS", "CFU-100-ME-GA-002",
               scale="1:50", discipline="MECHANICAL", notes=COMMON_NOTES + [
                   "Strippers fed by gravity from C-101 draw trays; vapour returns above draw trays.",
                   "PSV-1009 common to C-102/103/104 (locked-open valves) - HOLD.",
                   "Skirt heights set by NPSH of P-109/110/111 (CAL-001 S9)."])
    P = Pen(sh)
    s = 20.0
    y_grade = 512
    xs = [105, 300, 495]
    gC, rC = calc["geoms"]["C-101"], calc["columns"]["C-101"]
    feed_rows = []
    for (t, cx) in zip(("C-102", "C-103", "C-104"), xs):
        g, r = calc["geoms"][t], calc["columns"][t]
        cv = ColumnView(P, g, r, cx, y_grade, s).draw(elev_x=cx + 52, label_side_offset=10)
        ytop = cv.y(g["H"]) - g["D_top"] / 4 * s - 31
        P.text(f"{t} - {g['e']['service'].upper()}", cx, ytop, 3.0, "middle", bold=True)
        P.text(f"ID {g['D_top'] * 1000:.0f} x {g['H'] * 1000:.0f} T/T - ELEVATION 1:50", cx, ytop + 4.5, 2.2, "middle")
        t1, t2 = g["trays"][0], g["trays"][1]
        R = cv.R(t1["z"])
        P.dim_v(cx + R + 5, cv.y(t1["z"]), cv.y(t2["z"]), "610", side="right", size=1.8)
        # table above each column
        rows = [[n[0], n[2], n[3], n[4], n[6][:34]] for n in nozzle_rows(g, r)]
        x0 = cx - 88
        y = P.table(x0, 20, ["MARK", "SIZE", "RATING", "LOCATION", "SERVICE"], rows, [13, 10, 17, 24, 112],
                    title=f"{t} NOZZLE SCHEDULE", fs=2.0, rh=3.3) + 2
        W = r["W"]
        dr = [("Design P / T", f"{r['Pd']} barg / {r['Td']:.0f} C"),
              ("Material / CA", f"{r['mat']} / {r['CA']} mm ({g['e']['moc']})"),
              ("Shell / heads / skirt t", f"{r['segs'][0]['t_nom']} / {r['heads']['top']['t_nom']} / {r['skirt']['t_nom']} mm"),
              ("Skirt height / BTL", f"{r['skirt_h'] * 1000:.0f} mm / EL {100 + r['skirt_h']:.3f}"),
              ("Trays", "6 x 1-pass valve trays, 610 spacing, 410S"),
              ("Weights empty / op / test", f"{W['empty'] / 1e3:.1f} / {W['operating'] / 1e3:.1f} / {W['hydrotest'] / 1e3:.1f} t"),
              ("Hydrotest top / bottom", f"{r['hydro']['Pt_top']:.2f} / {r['hydro']['Pt_bot']:.2f} barg")]
        P.kv_table(x0, y, dr, [44, 132], fs=2.0, rh=3.2)
        plan_orientation(P, g, cx, 136, g["D_top"] / 2 * s, f"{t} NOZZLE ORIENTATION 1:50")
        # gravity feed check
        k = g["product"]
        draw = next(n for n in gC["nozzles"] if n["service"].startswith(f"{k.title()} draw"))
        el_draw = 100 + rC["skirt_h"] + draw["z"]
        inlet = next(n for n in g["nozzles"] if n["mark"] == "N1")
        el_in = 100 + r["skirt_h"] + inlet["z"]
        from .common import results as _res
        tr = _res()["atm"]["tray"][k]
        feed_rows.append([t, f"{draw['mark']} (tray {tr})", f"{el_draw:.3f}", f"{el_in:.3f}", f"{el_draw - el_in:.1f}"])
    P.table(651, 20, ["STRIPPER", "C-101 DRAW", "DRAW EL", "INLET EL", "HEAD m"], feed_rows, [24, 30, 42, 42, 37],
            title="GRAVITY FEED CHECK (C-101 DRAW -> STRIPPER N1)", fs=2.0, rh=3.4)
    legend(P, 651, 48, W=175)
    return sh


# ---------------------------------------------------------------------------
def ga_lightends(calc):
    sh = Sheet("A1", "COLUMN GENERAL ARRANGEMENT", "C-105 STABILISER & C-106 NAPHTHA SPLITTER", "CFU-100-ME-GA-003",
               scale="1:100", discipline="MECHANICAL", notes=COMMON_NOTES + [
                   "C-105: HIC-resistant plate, PWHT, NACE MR0103 (wet H2S).",
                   "C-105 reboiler E-116 (kettle), C-106 reboiler E-117 (thermosyphon)."])
    P = Pen(sh)
    s = 10.0
    y_grade = 515
    pos = {"C-105": 78, "C-106": 205}
    for t, cx in pos.items():
        g, r = calc["geoms"][t], calc["columns"][t]
        cv = ColumnView(P, g, r, cx, y_grade, s).draw(elev_x=cx + 38)
        P.text(t, cx, cv.y(g["H"]) - g["D_top"] / 4 * s - 20, 3.6, "middle", bold=True)
        P.text(g["e"]["service"].upper(), cx, cv.y(g["H"]) - g["D_top"] / 4 * s - 15.5, 2.2, "middle")
        ft = g["col"]["feed_stage"]
        zf = g["trays"][ft - 1]["z"]
        P.leader([(cx - cv.R(zf) + 1, cv.y(zf) - 2), (cx - 45, cv.y(zf) - 10)], f"FEED TRAY {ft}", 1.8, "end")
    x0 = 292
    y = 20
    fs, rh = 2.1, 3.45
    for t in ("C-105", "C-106"):
        g, r = calc["geoms"][t], calc["columns"][t]
        rows = [[n[0], n[1], n[2], n[3], n[4], n[5], n[6][:60]] for n in nozzle_rows(g, r)]
        y = P.table(x0, y, ["MARK", "QTY", "SIZE", "RATING", "LOCATION", "ORIENT", "SERVICE"], rows,
                    [13, 8, 11, 17, 23, 13, 115], title=f"{t} NOZZLE SCHEDULE", fs=fs, rh=rh) + 2
        col = g["col"]
        sec = [["Top (rectifying)", f"1-{col['feed_stage'] - 1}", f"{col['sec_top']['FLV']:.3f}",
                f"{col['sec_top']['u_flood']:.2f}", f"{col['sec_top']['D_calc']:.2f}", f"{g['D_top']:.2f}",
                str(col['sec_top']['passes'])],
               ["Bottom (stripping)", f"{col['feed_stage']}-{col['N_actual']}", f"{col['sec_bot']['FLV']:.3f}",
                f"{col['sec_bot']['u_flood']:.2f}", f"{col['sec_bot']['D_calc']:.2f}", f"{g['D_top']:.2f}",
                str(col['sec_bot']['passes'])]]
        y = P.table(x0, y, ["SECTION", "TRAYS", "FLV", "u flood m/s", "D calc m", "D sel. m", "PASSES"], sec,
                    [44, 22, 22, 26, 26, 26, 34], fs=fs, rh=rh) + 2
        y = P.kv_table(x0, y, design_rows(g, r), [48, 152], fs=fs, rh=3.25) + 8
    plan_orientation(P, calc["geoms"]["C-105"], 560, 72, 1.05 * 20, "C-105 NOZZLE ORIENTATION 1:50")
    plan_orientation(P, calc["geoms"]["C-106"], 560, 205, 1.55 * 20, "C-106 NOZZLE ORIENTATION 1:50")
    legend(P, 651, 20, W=175)
    return sh


# ---------------------------------------------------------------------------
def ring_positions(g, sg):
    """Evenly spaced ring elevations, shifted clear of side nozzles / manways."""
    n = sg["n_rings"]
    L = sg["z1"] - sg["z0"]
    out = []
    for i in range(1, n + 1):
        z = sg["z0"] + L * i / (n + 1)
        for _ in range(4):
            hit = [m for m in g["nozzles"] if m["side"] in ("L", "R", "F") and
                   abs(m["z"] - z) < m["nps"] * 0.0254 / 2 + 0.25]
            if not hit:
                break
            m = hit[0]
            z = m["z"] - (m["nps"] * 0.0254 / 2 + 0.3) if z <= m["z"] else m["z"] + m["nps"] * 0.0254 / 2 + 0.3
        out.append(z)
    return out


def ga_c201(calc):
    g, r = calc["geoms"]["C-201"], calc["columns"]["C-201"]
    sh = Sheet("A1", "COLUMN GENERAL ARRANGEMENT", "C-201 VACUUM COLUMN", "CFU-200-ME-GA-004", scale="1:100",
               discipline="MECHANICAL", notes=COMMON_NOTES + [
                   "Design full vacuum: external stiffening rings at max. 3.0 m spacing (see table).",
                   "Boot: VR quench distributor above HLL limits boot residence/coking.",
                   "HOLD: top section ID per equipment.json - see CAL-001 S13 (bed 1 rating)."])
    P = Pen(sh)
    s = 10.0
    y_grade = 532
    cx = 140
    cv = ColumnView(P, g, r, cx, y_grade, s).draw(elev_x=212, tray_numbers=True)
    ring_z = []
    for sg in r["segs"]:
        if not sg.get("ring"):
            continue
        for z in ring_positions(g, sg):
            ring_z.append((z, sg))
            R = cv.R(z)
            yy = cv.y(z)
            h = sg["ring"]["h"] / 1000 * s
            for sx in (-1, 1):
                P.rect(cx + sx * R - (0 if sx > 0 else h), yy - 0.4, h, 0.8, lw=0.2, fill="#606060")
    lab_x = cx - 72
    leftz = [n["z"] for n in g["nozzles"] if n["side"] == "L"]
    for it in g["internals"]:
        if it["kind"] in ("bed", "dist", "coll", "demister", "flash", "steam", "quench"):
            yy = cv.y(it["z"])
            R = cv.R(it["z"])
            if any(abs(it["z"] - zl) < 0.6 for zl in leftz):
                P.leader([(cx + R - 1.5, yy), (cx + 66, yy + 3)], it["label"].upper(), 1.75, "start", dot=True)
            else:
                P.leader([(cx - R + 1.5, yy), (lab_x + 2, yy)], it["label"].upper(), 1.75, "end", dot=True)
    zr, sgm = next((z, sg) for z, sg in ring_z if sg["D_mm"] > 5000 and
                   all(abs(z - n["z"]) > 1.5 for n in g["nozzles"] if n["side"] == "R"))
    P.leader([(cx + cv.R(zr) + 2.5, cv.y(zr)), (cx + 62, cv.y(zr) + 14)],
             f"STIFFENING RING\nFB {sgm['ring']['h']}x{sgm['ring']['b']} (TYP.)", 1.8, "start")
    P.text("ELEVATION (DEVELOPED) 1:100", cx, 550, 2.8, "middle", bold=True)
    x0, fs, rh = 252, 2.1, 3.5
    yb = P.table(x0, 20, ["MARK", "QTY", "SIZE", "RATING", "LOCATION", "ORIENT", "SERVICE"], nozzle_rows(g, r),
                 [13, 8, 11, 17, 23, 13, 125], title="NOZZLE SCHEDULE", fs=fs, rh=rh)
    rows = []
    for sec in g["sections"]:
        Dsel = {"Bed 1": g["Ds"][2], "Stripping": g["Ds"][1]}
        D = next((v for k, v in Dsel.items() if sec["name"].startswith(k)), g["Ds"][0])
        A = math.pi / 4 * D ** 2
        if "u_allow" in sec:
            load = sec["Q_v_m3s"] / A / sec["u_allow"] * 100
            rows.append([sec["name"], f"{sec['V_kg_h'] / 1000:.0f}", f"{sec['L_kg_h'] / 1000:.0f}", f"{sec['rho_v']:.3f}",
                         f"{sec['u_allow']:.2f}", f"{sec['D_calc']:.2f}", f"{D:.2f}", f"{load:.0f} % of Cs-limit"])
        else:
            fl = sec["Q_v_m3s"] / (0.85 * A * sec["u_flood"]) * 100
            rows.append([sec["name"], f"{sec['V_kg_h'] / 1000:.0f}", f"{sec['L_kg_h'] / 1000:.0f}", f"{sec['rho_v']:.3f}",
                         f"{sec['u_flood']:.2f}", f"{sec['D_calc']:.2f}", f"{D:.2f}", f"{fl:.0f} % flood"])
    yb = P.table(x0, yb + 4, ["SECTION", "V t/h", "L t/h", "rho V", "u allow/fl", "D calc", "D sel.", "LOADING"], rows,
                 [52, 17, 17, 19, 21, 18, 18, 48], title="HYDRAULIC SECTIONS (PROCESS SIZING)", fs=fs, rh=rh)
    rr = []
    for sg in r["segs"]:
        if sg.get("ext"):
            q = sg.get("ring")
            rr.append([sg["name"][:34], f"{sg['t_nom']}", f"{sg['ext']['t_ext'] if False else sg['t_ext']}",
                       f"{sg['ext']['Ls']:.0f}", f"{sg['ext']['Pa'] * 10:.3f}", f"{sg.get('n_rings') or '-'}",
                       f"{q['h']}x{q['b']}" if q else "-", f"{sg.get('t_ext_norings') or '-'}"])
    yb = P.table(x0, yb + 4, ["COURSE", "t nom", "t ext", "L / Le mm", "Pa bar", "RINGS", "FB h x b", "t no rings"], rr,
                 [56, 16, 16, 22, 20, 17, 23, 40], title="EXTERNAL PRESSURE UG-28/29 - FULL VACUUM (1.034 bar)",
                 fs=fs, rh=rh)
    yb = P.table(x0, yb + 4, ["COMPONENT", "ID mm", "FROM EL", "TO EL", "t mm", "MATERIAL", "REMARK"], course_rows(g, r),
                 [44, 22, 25, 25, 13, 30, 51], title="SHELL COURSE / THICKNESS SCHEDULE", fs=fs, rh=rh)
    yb = P.table(x0, yb + 4, ["PLATF.", "ELEVATION", "SERVES MANWAY", "NOZZLES ACCESSED"], platform_rows(g, r),
                 [16, 30, 40, 124], title="PLATFORM SCHEDULE", fs=fs, rh=rh)
    plan_orientation(P, g, 558, 92, g["D"] / 2 * s if "D" in g else g["Ds"][0] / 2 * s,
                     "NOZZLE ORIENTATION PLAN (MAIN SHELL) 1:100")
    flash_section(P, g, 528, 245, s, D=g["Ds"][0])
    base_plan(P, r, 575, 400, s)
    P.kv_table(651, 20, design_rows(g, r), [50, 125], title="DESIGN DATA", fs=fs, rh=3.4)
    legend(P, 651, 92, W=175)
    P.kv_table(651, 168, weight_rows(r), [95, 80], title="WEIGHTS & LOADS", fs=fs, rh=3.4)
    return sh


def build(calc):
    GA_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for fn, stem in ((ga_c101, "CFU-100-ME-GA-001_C-101-Column-GA"), (ga_strippers, "CFU-100-ME-GA-002_Side-Strippers-GA"),
                     (ga_lightends, "CFU-100-ME-GA-003_C-105-C-106-GA"), (ga_c201, "CFU-200-ME-GA-004_C-201-Vacuum-Column-GA")):
        sh = fn(calc)
        out.append(sh.save(GA_DIR / stem))
    return out
