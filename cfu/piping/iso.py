"""Piping isometric drawings (A3, true 30 deg isometric, single-line, not to scale).

Each sheet: iso view with fittings/valves/supports/welds/dimensions/elevations/coordinates, BOM, cut lengths,
line data strip, notes. Long lines are split over several sheets at a MAIN-branch vertex.
"""
from __future__ import annotations

import math
from collections import OrderedDict

import numpy as np

from ..drawing.sheet import Sheet, FONT
from . import specs

C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
AXV = {0: np.array([C30, S30]), 1: np.array([C30, -S30]), 2: np.array([0.0, -1.0])}   # E, N, Up in SVG coords
INK = "#000"
DIMC = "#1f3f8f"
SUPC = "#7a2e00"
WELDC = "#b00020"

MATS = {
    "CS": dict(pipe="ASTM A106 Gr.B SMLS", big="ASTM A672 C70 Cl.22 EFW", fit="ASTM A234 WPB", flg="ASTM A105",
               valve="A216 WCB, trim 8", bolt="A193 B7 / A194 2H"),
    "P5": dict(pipe="ASTM A335 P5 SMLS", big="ASTM A691 5CR Cl.42 EFW", fit="ASTM A234 WP5", flg="ASTM A182 F5",
               valve="A217 C5, trim 5", bolt="A193 B7 / A194 4"),
    "P9": dict(pipe="ASTM A335 P9 SMLS", big="ASTM A691 9CR Cl.42 EFW", fit="ASTM A234 WP9", flg="ASTM A182 F9",
               valve="A217 C12, trim 5", bolt="A193 B16 / A194 4"),
    "P11": dict(pipe="ASTM A335 P11 SMLS", big="ASTM A691 1-1/4CR Cl.42 EFW", fit="ASTM A234 WP11",
                flg="ASTM A182 F11", valve="A217 WC6, trim 8", bolt="A193 B7 / A194 2H"),
    "SS": dict(pipe="ASTM A312 TP304", big="ASTM A358 304 Cl.1", fit="ASTM A403 WP304", flg="ASTM A182 F304",
               valve="A351 CF8", bolt="A193 B8 / A194 8"),
}


def proj(v):
    return v[0] * AXV[0] + v[1] * AXV[1] + v[2] * AXV[2]


def draw_dir(v):
    v = np.array(v, float)
    L = np.linalg.norm(v)
    if L < 1e-9:
        return np.array([1.0, 0.0])
    v = v / L
    if abs(v[2]) < 0.06:
        v[2] = 0.0
    if abs(v[0]) < 0.03:
        v[0] = 0.0
    if abs(v[1]) < 0.03:
        v[1] = 0.0
    u = proj(v)
    n = np.linalg.norm(u)
    return u / n if n > 1e-9 else np.array([1.0, 0.0])


def fmt_el(z):
    return f"EL +{z:.3f}"


def fmt_c(p):
    return f"E {p[0]:.3f}  N {p[1]:.3f}"


# ==============================================================================================
class IsoLayout:
    """Schematic iso layout: segment lengths compressed (sqrt), fittings given room."""

    def __init__(self, route, view):
        self.r = route
        self.view = view            # {branch_id: (d0, d1)}
        self.bp = {}                # branch -> list[(d, Q)]
        self._layout()

    def _breaks(self, b, d0, d1):
        r = self.r
        ds = {d0, d1}
        kinds = {}
        for i in range(len(b.pts)):
            if d0 - 1e-6 <= b.cum[i] <= d1 + 1e-6:
                ds.add(b.cum[i])
        for e in r.elements[b.id]:
            if e["kind"] == "pipe":
                continue
            for d in (e["d0"], e["d1"]):
                if d0 - 1e-6 <= d <= d1 + 1e-6:
                    ds.add(d)
            kinds[(round(e["d0"], 4), round(e["d1"], 4))] = e["kind"]
        for s in r.supports:
            if s["branch"] == b.id and d0 <= s["d"] <= d1:
                ds.add(s["d"])
        for o in getattr(r, "_olets", {}).get(b.id, []):
            if d0 <= o["d0"] <= d1:
                ds.add(o["d0"])
        ds = sorted(ds)
        out = [ds[0]]
        for d in ds[1:]:
            if d - out[-1] > 0.004:
                out.append(d)
        if out[-1] < d1 - 1e-6:
            out.append(d1)
        return out, kinds

    def _g(self, b, a, c):
        L = c - a
        mid = (a + c) / 2
        for e in self.r.elements[b.id]:
            if e["kind"] != "pipe" and e["d0"] - 1e-6 <= a and c <= e["d1"] + 1e-6:
                if e["kind"] in ("gate", "globe", "check", "cv"):
                    return 6.0
                if e["kind"] in ("elbow", "tee"):
                    return 1.4 + 1.6 * math.sqrt(L)
                if e["kind"] in ("reducer",):
                    return 3.6
                return 1.6 + 2.0 * math.sqrt(L)
        return 2.6 + 5.2 * math.sqrt(L)

    def _branch_points(self, b, anchor, reverse=False):
        d0, d1 = self.view[b.id]
        ds, _ = self._breaks(b, d0, d1)
        pts = []
        if not reverse:
            Q = np.array(anchor, float)
            pts.append((ds[0], Q.copy()))
            for a, c in zip(ds, ds[1:]):
                v = b.dir_at((a + c) / 2)
                Q = Q + draw_dir(v) * self._g(b, a, c)
                pts.append((c, Q.copy()))
        else:
            Q = np.array(anchor, float)
            pts.append((ds[-1], Q.copy()))
            for a, c in zip(ds[::-1][1:], ds[::-1]):
                v = b.dir_at((a + c) / 2)
                Q = Q - draw_dir(v) * self._g(b, a, c)
                pts.append((a, Q.copy()))
            pts = pts[::-1]
        return pts

    def _layout(self):
        r = self.r
        order = [b for b in r.branches if b.id in self.view]
        roots = [b for b in order if b.parent is None or b.parent not in self.view]
        placed = set()
        for b in roots:
            self.bp[b.id] = self._branch_points(b, (0.0, 0.0) if not self.bp else self._free_anchor())
            placed.add(b.id)
        guard = 0
        while len(placed) < len(order) and guard < 20:
            guard += 1
            for b in order:
                if b.id in placed or b.parent not in placed:
                    continue
                par = r.br(b.parent)
                st_tee = b.start.get("kind") == "tee"
                en_tee = b.end.get("kind") == "tee"
                if st_tee:
                    da = par.d_of_point(b.pts[0], tol=0.05)
                    A = self.at(par.id, da)
                    pts = self._branch_points(b, A)
                    if en_tee:
                        db = par.d_of_point(b.pts[-1], tol=0.05)
                        B = self.at(par.id, db)
                        if len(pts) >= 3:
                            off = pts[1][1] - pts[0][1]
                            # bypass: keep offset legs, re-anchor end
                            k1 = [i for i, (d, _) in enumerate(pts) if d >= b.cum[1] - 1e-6][0]
                            k2 = [i for i, (d, _) in enumerate(pts) if d >= b.cum[-2] - 1e-6][0]
                            off = pts[k1][1] - pts[0][1]
                            newp = []
                            for i, (d, Q) in enumerate(pts):
                                if i <= k1:
                                    newp.append((d, A + (Q - A)))
                                elif i < k2:
                                    t = (d - b.cum[1]) / max(b.cum[-2] - b.cum[1], 1e-6)
                                    newp.append((d, A + off + (B - A) * t))
                                else:
                                    t = (d - b.cum[-2]) / max(b.length - b.cum[-2], 1e-6)
                                    newp.append((d, B + off * (1 - t)))
                            pts = newp
                else:
                    db = par.d_of_point(b.pts[-1], tol=0.05)
                    B = self.at(par.id, db)
                    pts = self._branch_points(b, B, reverse=True)
                self.bp[b.id] = pts
                placed.add(b.id)

    def _free_anchor(self):
        allp = np.array([q for v in self.bp.values() for _, q in v])
        return (allp[:, 0].max() + 30, allp[:, 1].mean())

    def at(self, bid, d):
        pts = self.bp[bid]
        if d <= pts[0][0]:
            return pts[0][1].copy()
        for (da, qa), (db, qb) in zip(pts, pts[1:]):
            if da - 1e-9 <= d <= db + 1e-9:
                t = 0 if db - da < 1e-9 else (d - da) / (db - da)
                return qa + (qb - qa) * t
        return pts[-1][1].copy()

    def bbox(self):
        allp = np.array([q for v in self.bp.values() for _, q in v])
        return allp.min(0), allp.max(0)


# ==============================================================================================
class IsoSheet:
    def __init__(self, route, props, stress, iso_no, title, sheet_no, n_sheets, view, cont_marks, catinfo):
        self.r = route
        self.pr = props
        self.st = stress
        self.iso_no = iso_no
        self.title = title
        self.view = view
        self.cont = cont_marks
        self.cat = catinfo
        self.sheet_txt = f"{sheet_no} OF {n_sheets}"
        l = route.line
        self.notes = self._notes()
        self.sh = Sheet("A3", f"PIPING ISOMETRIC  {l['line_no']}", title, iso_no, sheet=self.sheet_txt,
                        discipline="PIPING", notes=self.notes)
        self.d = self.sh.dwg
        self.lay = IsoLayout(route, view)
        route._sch_override = {route.nps: props["sch"]}
        self.labels = []

    # ------------------------------------------------------------------ helpers
    def T(self, s, x, y, size=1.9, anchor="start", bold=False, color=INK, rot=None, g=None):
        t = self.d.text(s, insert=(round(x, 2), round(y, 2)), font_size=size, text_anchor=anchor, fill=color,
                        stroke="none", font_family=FONT, font_weight="bold" if bold else "normal")
        if rot:
            t.rotate(round(rot, 2), center=(round(x, 2), round(y, 2)))
        (g or self.sh.g).add(t)
        return t

    def L(self, a, b, w=0.25, color=INK, dash=None, g=None):
        ln = self.d.line((round(a[0], 2), round(a[1], 2)), (round(b[0], 2), round(b[1], 2)), stroke=color,
                         stroke_width=w)
        if dash:
            ln["stroke-dasharray"] = dash
        (g or self.sh.g).add(ln)

    def P(self, pts, fill="none", color=INK, w=0.25, g=None):
        (g or self.sh.g).add(self.d.polygon([(round(p[0], 2), round(p[1], 2)) for p in pts], fill=fill, stroke=color,
                                            stroke_width=w))

    def X(self, d):
        return self.o + d * self.s

    def at(self, bid, d):
        return self.X(self.lay.at(bid, d))

    def sdir(self, bid, d):
        b = self.r.br(bid)
        return draw_dir(b.dir_at(d))

    # ------------------------------------------------------------------ main
    def render(self, stem):
        self.xr = self.sh._tb[0]
        x0, y0, x1, y1 = 15, 16, self.xr - 8, 248
        lo, hi = self.lay.bbox()
        w, h = hi - lo
        mx, my = 30, 26
        s = min((x1 - x0 - 2 * mx) / max(w, 1), (y1 - y0 - 2 * my) / max(h, 1), 2.3)
        self.s = s
        self.o = np.array([x0 + mx + ((x1 - x0 - 2 * mx) - w * s) / 2, y0 + my + ((y1 - y0 - 2 * my) - h * s) / 2]) - lo * s
        cen = self.lay.bbox()
        self.cen = self.X((cen[0] + cen[1]) / 2)
        self._frame_iso(x0, y0, x1, y1)
        self._pipes()
        self._components()
        self._welds()
        self._supports()
        self._dims()
        self._elevations()
        self._ends()
        self._labels()
        self._north(x0 + 13, y0 + 15)
        self._line_strip()
        self._right_tables()
        return self.sh.save(stem)

    def _frame_iso(self, x0, y0, x1, y1):
        self.L((x1 + 4, y0 - 4), (x1 + 4, 250), w=0.35)
        self.L((x0 - 6, 250), (x1 + 4, 250), w=0.35)
        self.T("ISOMETRIC VIEW - NOT TO SCALE - DIMENSIONS IN mm, ELEVATIONS / COORDINATES IN m (PLANT GRID)",
               x0, y0 - 2.5, 2.0, bold=True)

    def _pipes(self):
        g = self.d.g(stroke=INK, stroke_width=0.75, fill="none", stroke_linecap="round")
        for bid, pts in self.lay.bp.items():
            b = self.r.br(bid)
            n = b.nps
            w = 0.95 if n >= self.r.nps * 0.99 else 0.6
            q = [tuple(np.round(self.X(Q), 2)) for _, Q in pts]
            g.add(self.d.polyline(q, stroke_width=w))
        self.sh.g.add(g)
        # insulation indication: dashed offset on the longest segment of MAIN
        if self.r.line["insul"] != "N":
            bid, i0, L = self._longest()
            if bid:
                b = self.r.br(bid)
                da, db = b.cum[i0] + 0.25 * b.seg[i0], b.cum[i0] + 0.75 * b.seg[i0]
                A, B = self.at(bid, da), self.at(bid, db)
                u = B - A
                nrm = np.array([-u[1], u[0]]) / max(np.linalg.norm(u), 1e-9)
                for sg in (1, -1):
                    self.L(A + nrm * 1.2 * sg, B + nrm * 1.2 * sg, w=0.2, dash="1.2,0.8")
                ins = {"H": "HEAT CONS.", "P": "PERS. PROT.", "ST": "STEAM TRACED", "C": "COLD"}.get(self.r.line["insul"], "")
                m = (A + B) / 2 + nrm * 3.2
                self.T(f"INSUL. {self.pr['insul_mm']} mm {ins}", m[0], m[1], 1.6, "middle", color="#555",
                       rot=self._readable(u))

    def _longest(self):
        best = (None, 0, 0)
        for bid in self.lay.bp:
            b = self.r.br(bid)
            d0, d1 = self.view[bid]
            for i, s in enumerate(b.seg):
                a, c = max(b.cum[i], d0), min(b.cum[i + 1], d1)
                if c - a > best[2]:
                    best = (bid, i, c - a)
        return best

    @staticmethod
    def _readable(u):
        a = math.degrees(math.atan2(u[1], u[0]))
        if a > 90:
            a -= 180
        if a < -90:
            a += 180
        return a

    def _typ(self, bid):
        """Olet children (heater pass stubs etc.): only the first and last are annotated, rest 'typ.'"""
        kids = [b.id for b in self.r.branches if (b.start.get("olet") or b.end.get("olet")) and b.id in self.view]
        if bid not in kids:
            return 0
        return 0 if bid in (kids[0],) else (2 if bid == kids[-1] else 1)

    def _in_view(self, bid, d):
        if bid not in self.view:
            return False
        a, b = self.view[bid]
        return a - 1e-6 <= d <= b + 1e-6

    # ------------------------------------------------------------------ symbols
    def _components(self):
        r = self.r
        for bid in self.lay.bp:
            for e in r.elements[bid]:
                k = e["kind"]
                dm = (e["d0"] + e["d1"]) / 2
                if not self._in_view(bid, dm):
                    continue
                c = self.at(bid, dm)
                u = self.sdir(bid, dm)
                nrm = np.array([-u[1], u[0]])
                if k in ("gate", "globe", "check", "cv"):
                    self._valve(c, u, nrm, k, e.get("item") or {})
                elif k == "reducer":
                    it = e["item"]
                    big_first = it["nps"] > it["nps2"]
                    h1, h2 = (1.7, 1.0) if big_first else (1.0, 1.7)
                    A, B = c - u * 1.8, c + u * 1.8
                    if it.get("ecc"):
                        top = np.array([0, -1.0]) if abs(u[1]) < 0.95 else nrm
                        sgn = 1 if np.dot(top, nrm) > 0 else -1
                        pts = [A + nrm * sgn * h1, B + nrm * sgn * h1 if False else B + nrm * sgn * h2 - nrm * sgn * (h2 - h1) * 0,
                               B - nrm * sgn * h2 + nrm * sgn * (h2 - h1) * 0, A - nrm * sgn * h1]
                        # flat on top: keep top edge straight
                        hmax = max(h1, h2)
                        pts = [A + nrm * sgn * hmax, B + nrm * sgn * hmax, B + nrm * sgn * (hmax - 2 * h2),
                               A + nrm * sgn * (hmax - 2 * h1)]
                        self.P(pts, fill="white", w=0.3)
                        self._lab(c + nrm * sgn * 4.5, f"ECC RED {specs.nps_str(it['nps'])}x{specs.nps_str(it['nps2'])} "
                                                       f"{it.get('ecc', 'FOT')}", 1.6)
                    else:
                        self.P([A + nrm * h1, B + nrm * h2, B - nrm * h2, A - nrm * h1], fill="white", w=0.3)
                        self._lab(c + nrm * 4.0, f"CONC RED {specs.nps_str(it['nps'])}x{specs.nps_str(it['nps2'])}", 1.6)
                elif k == "fe":
                    for sg in (-0.5, 0.5):
                        self.L(c + u * sg + nrm * 1.9, c + u * sg - nrm * 1.9, w=0.45)
                    self._lab(c - nrm * 4.0, f"{e['item'].get('tag') or 'FE'} ORIFICE", 1.7, bold=True)
                elif k == "strainer":
                    for sg in (-0.45, 0.45):
                        self.L(c + u * sg + nrm * 1.8, c + u * sg - nrm * 1.8, w=0.4)
                    self.P([c + u * 0.0 + nrm * 1.2, c + u * 2.2, c - nrm * 1.2], w=0.2)
                    self._lab(c + nrm * 3.6, "TEMP. STRAINER", 1.5)
                elif k == "spec":
                    self.L(c + nrm * 2.0, c - nrm * 2.0, w=0.45)
                    circ = self.d.circle(center=tuple(np.round(c + nrm * 3.0, 2)), r=1.0, fill="none", stroke=INK,
                                         stroke_width=0.3)
                    self.sh.g.add(circ)
                    self._lab(c - nrm * 3.8, "SPEC. BLIND", 1.5)
                elif k == "cap":
                    end = self.at(bid, e["d1"] if e["d1"] >= self.r.br(bid).length - 0.01 else e["d0"])
                    self.L(end + nrm * 1.6, end - nrm * 1.6, w=0.8)
                elif k == "flange":
                    pass
        # bolted joints = flange pairs
        for j in r.joints:
            if not self._in_view(j["branch"], j["d"]):
                continue
            c = self.at(j["branch"], j["d"])
            u = self.sdir(j["branch"], min(j["d"], self.r.br(j["branch"]).length - 1e-3))
            nrm = np.array([-u[1], u[0]])
            for sg in (-0.35, 0.35):
                self.L(c + u * sg + nrm * 1.7, c + u * sg - nrm * 1.7, w=0.4)
        # olets
        for bid in self.lay.bp:
            for o in getattr(r, "_olets", {}).get(bid, []):
                if not self._in_view(bid, o["d0"]) or o.get("child"):
                    continue
                it = o.get("item") or {}
                c = self.at(bid, o["d0"])
                u = self.sdir(bid, o["d0"])
                nrm = np.array([-u[1], u[0]])
                side = nrm if np.dot(nrm, c - self.cen) >= 0 else -nrm
                e = c + side * 3.2
                self.L(c, e, w=0.4)
                self.L(e + u * 0.9, e - u * 0.9, w=0.5)
                circ = self.d.circle(center=tuple(np.round(c, 2)), r=0.55, fill="white", stroke=INK, stroke_width=0.3)
                self.sh.g.add(circ)
                t = f"{specs.nps_str(o.get('nps_b', 1))} {it.get('tag') or ''}".strip()
                self._lab(e + side * 2.2, t, 1.5)

    def _valve(self, c, u, nrm, k, it):
        L, H = 2.3, 1.45
        A, B = c - u * L, c + u * L
        t1 = [A + nrm * H, A - nrm * H, c]
        t2 = [B + nrm * H, B - nrm * H, c]
        self.P(t1, fill="white", w=0.35)
        self.P(t2, fill=INK if k == "check" else "white", w=0.35)
        side = np.array([0.0, -1.0]) if abs(u[1]) < 0.9 else (nrm if np.dot(nrm, c - self.cen) >= 0 else -nrm)
        if k == "globe":
            self.sh.g.add(self.d.circle(center=tuple(np.round(c, 2)), r=0.75, fill=INK, stroke="none"))
        if k in ("gate", "globe"):
            e = c + side * 3.0
            self.L(c, e, w=0.3)
            self.L(e - u * 1.3, e + u * 1.3, w=0.45)
        if k == "cv":
            e = c + side * 3.0
            self.L(c, e, w=0.3)
            arc = self.d.path(d=f"M {e[0] - u[0] * 2:.2f},{e[1] - u[1] * 2:.2f} A 2 2 0 0 1 {e[0] + u[0] * 2:.2f},{e[1] + u[1] * 2:.2f} Z",
                              fill="white", stroke=INK, stroke_width=0.35)
            self.sh.g.add(arc)
        lab = it.get("tag") or ""
        desc = {"gate": "GV", "globe": "GLV", "check": "CHV", "cv": ""}[k]
        if k == "cv":
            self._lab(c + side * 7.2, lab or "CV", 1.9, bold=True)
        elif lab:
            self._lab(c - side * 3.6, f"{desc} {lab}", 1.6, bold=True)

    def _lab(self, p, text, size=1.6, bold=False, color=INK):
        self.labels.append((p, text, size, bold, color))

    # ------------------------------------------------------------------ welds
    def _welds(self):
        n_s = 0
        for w in self.r.welds:
            if not self._in_view(w["branch"], w["d"]):
                continue
            c = self.at(w["branch"], w["d"])
            u = self.sdir(w["branch"], max(min(w["d"], self.r.br(w["branch"]).length - 1e-3), 0))
            nrm = np.array([-u[1], u[0]])
            if w["type"] == "F":
                self.sh.g.add(self.d.circle(center=tuple(np.round(c, 2)), r=0.85, fill="white", stroke=WELDC,
                                            stroke_width=0.35))
                self.L(c - (u + nrm) * 0.6, c + (u + nrm) * 0.6, w=0.3, color=WELDC)
                self.L(c - (u - nrm) * 0.6, c + (u - nrm) * 0.6, w=0.3, color=WELDC)
                side = -nrm if np.dot(nrm, c - self.cen) >= 0 else nrm
                p = c + side * 2.6
                self.T(f"FW{w['no']}", p[0], p[1] + 0.6, 1.45, "middle", color=WELDC, bold=True)
            else:
                n_s += 1
                self.sh.g.add(self.d.circle(center=tuple(np.round(c, 2)), r=0.42, fill=WELDC, stroke="none"))
                side = -nrm if np.dot(nrm, c - self.cen) >= 0 else nrm
                p = c + side * 1.9
                self.T(str(w["no"]), p[0], p[1] + 0.5, 1.15, "middle", color=WELDC)

    # ------------------------------------------------------------------ supports
    def _supports(self):
        for s in self.r.supports:
            if not self._in_view(s["branch"], s["d"]):
                continue
            c = self.at(s["branch"], s["d"])
            u = self.sdir(s["branch"], s["d"])
            nrm = np.array([-u[1], u[0]])
            down = np.array([0, 1.0])
            if abs(u[1]) > 0.9:
                down = nrm if np.dot(nrm, c - self.cen) < 0 else -nrm
            t = s["type"]
            g = self.d.g(stroke=SUPC, stroke_width=0.35, fill="none")
            if t == "R":
                self.P([c + down * 0.9, c + down * 2.6 + u * 1.2, c + down * 2.6 - u * 1.2], color=SUPC, w=0.3, g=g)
            elif t == "G":
                for sg in (1, -1):
                    self.L(c + nrm * sg * 1.2 - u * 1.2, c + nrm * sg * 1.2 + u * 1.2, w=0.45, color=SUPC, g=g)
                self.P([c + down * 0.9, c + down * 2.6 + u * 1.2, c + down * 2.6 - u * 1.2], color=SUPC, w=0.3, g=g)
            elif t == "A":
                q = [c + (u + nrm) * 1.5, c + (u - nrm) * 1.5, c - (u + nrm) * 1.5, c - (u - nrm) * 1.5]
                self.P(q, color=SUPC, w=0.4, g=g)
                self.L(q[0], q[2], w=0.35, color=SUPC, g=g)
                self.L(q[1], q[3], w=0.35, color=SUPC, g=g)
            elif t == "S":
                z = [c + down * 0.8]
                for k in range(5):
                    z.append(c + down * (1.2 + 0.45 * k) + u * (0.9 if k % 2 == 0 else -0.9))
                z.append(c + down * 3.6)
                g.add(self.d.polyline([tuple(np.round(p, 2)) for p in z]))
                self.L(c + down * 3.6 - u * 1.3, c + down * 3.6 + u * 1.3, w=0.45, color=SUPC, g=g)
            self.sh.g.add(g)
            code = {"R": "RS", "G": "GD", "A": "ANC", "S": "SPR"}[t]
            p = c + down * 4.6
            self.T(f"{s['tag'][-2:]}-{code}", p[0], p[1] + 0.5, 1.3, "middle", color=SUPC)

    # ------------------------------------------------------------------ dimensions
    def _dims(self):
        r = self.r
        for bid in self.lay.bp:
            b = r.br(bid)
            if self._typ(bid):
                continue
            d0v, d1v = self.view[bid]
            for i, sL in enumerate(b.seg):
                a, c = max(b.cum[i], d0v), min(b.cum[i + 1], d1v)
                if c - a < 0.05:
                    continue
                A, B = self.at(bid, a), self.at(bid, c)
                u = B - A
                ln = np.linalg.norm(u)
                if ln < 2.5:
                    continue
                u = u / ln
                v3 = b.pts[i + 1] - b.pts[i]
                vert = abs(v3[2]) > 0.5 * sL
                if vert:
                    cands = [AXV[0], -AXV[0]]
                else:
                    cands = [AXV[2], -AXV[2]] if abs(u[1]) < 0.97 else [AXV[0], -AXV[0]]
                mid = (A + B) / 2
                off = max(cands, key=lambda cv: np.dot(cv, mid - self.cen))
                # chain points: component centres in this segment
                chain = [a]
                for e in r.elements[bid]:
                    if e["kind"] in ("gate", "globe", "check", "cv", "reducer", "fe"):
                        dm = (e["d0"] + e["d1"]) / 2
                        if a + 0.05 < dm < c - 0.05:
                            chain.append(dm)
                for ch in r.branches:
                    if ch.parent == bid and ch.id in self.view:
                        for pt in (ch.pts[0], ch.pts[-1]):
                            dd = b.d_of_point(pt, tol=0.05)
                            if dd is not None and a + 0.05 < dd < c - 0.05:
                                chain.append(dd)
                chain = sorted(set(round(x, 4) for x in chain)) + [c]
                lvl = 1
                if len(chain) > 2:
                    for p0, p1 in zip(chain, chain[1:]):
                        self._dim(self.at(bid, p0), self.at(bid, p1), off, 4.2, (p1 - p0) * 1000)
                    lvl = 2
                self._dim(A, B, off, 4.2 if lvl == 1 else 8.2, (c - a) * 1000, bold=lvl == 2)

    def _dim(self, A, B, off, dist, val, bold=False):
        if np.linalg.norm(B - A) < 1.6:
            return
        a2, b2 = A + off * dist, B + off * dist
        self.L(A + off * 0.8, a2 + off * 0.8, w=0.15, color=DIMC)
        self.L(B + off * 0.8, b2 + off * 0.8, w=0.15, color=DIMC)
        self.L(a2, b2, w=0.18, color=DIMC)
        u = (b2 - a2) / np.linalg.norm(b2 - a2)
        nrm = np.array([-u[1], u[0]])
        for p, sg in ((a2, 1), (b2, -1)):
            self.L(p + (u * sg + nrm) * 0.55, p - (u * sg + nrm) * 0.55, w=0.3, color=DIMC)
        m = (a2 + b2) / 2 + off * 0.9
        txt = f"{val:.0f}"
        self.T(txt, m[0], m[1] + 0.55, 1.75, "middle", color=DIMC, rot=self._readable(u), bold=bold)

    # ------------------------------------------------------------------ elevations / coordinates
    def _elevations(self):
        r = self.r
        done = []
        for bid in self.lay.bp:
            b = r.br(bid)
            if self._typ(bid) or ((b.start.get("olet") or b.end.get("olet")) and len(b.pts) == 2):
                continue
            d0v, d1v = self.view[bid]
            for i in range(len(b.pts)):
                d = b.cum[i]
                if not (d0v - 1e-6 <= d <= d1v + 1e-6):
                    continue
                prev_v = i > 0 and abs((b.pts[i] - b.pts[i - 1])[2]) > 0.3
                next_v = i < len(b.pts) - 1 and abs((b.pts[i + 1] - b.pts[i])[2]) > 0.3
                if not (prev_v or next_v) and 0 < i < len(b.pts) - 1:
                    continue
                c = self.at(bid, d)
                if any(np.linalg.norm(c - q) < 9.0 for q in done):
                    continue
                done.append(c)
                z = b.pts[i][2]
                side = AXV[0] if np.dot(AXV[0], c - self.cen) >= 0 else -AXV[0]
                p = c + side * 3.0 + np.array([0, -2.2])
                self.L(c, p - np.array([0, -0.6]), w=0.15, color="#444")
                self.T(fmt_el(z), p[0] + (0.5 if side[0] > 0 else -0.5), p[1], 1.7, "start" if side[0] > 0 else "end",
                       color="#004d26", bold=True)

    def _ends(self):
        """Terminal boxes: nozzles / tie-ins / continuation, with coordinates."""
        r = self.r
        for bid in self.lay.bp:
            b = r.br(bid)
            d0v, d1v = self.view[bid]
            for side, conn, d in (("s", b.start, 0.0), ("e", b.end, b.length)):
                if not (d0v - 1e-6 <= d <= d1v + 1e-6):
                    continue
                k = conn.get("kind")
                if k in ("tee",) and not conn.get("olet"):
                    continue
                c = self.at(bid, d)
                u = self.sdir(bid, d if side == "s" else d - 1e-3)
                out = -u if side == "s" else u
                if k == "tee" and conn.get("olet"):
                    continue
                if k == "nozzle":
                    nrm = np.array([-out[1], out[0]])
                    self.L(c + nrm * 2.2, c - nrm * 2.2, w=1.1)
                    typ = self._typ(bid)
                    if typ in (1, 2):
                        continue
                    lab = [conn.get("label", "").upper()]
                    if typ in (0, 2) and (b.start.get("olet") or b.end.get("olet")) and typ == 0:
                        nk = sum(1 for x in self.r.branches if (x.start.get("olet") or x.end.get("olet")) and x.id in self.view)
                        lab[0] += f" (PASSES 1-{nk} TYP., SYMMETRICAL)"
                        lab.append(f"LINES {getattr(b, 'line_ref', '')} ...")
                    lab.append(f"{specs.nps_str(conn.get('nps') or b.nps)} NOZZLE")
                elif k == "bl":
                    lab = [conn.get("label", "").upper(), "TIE-IN / SPEC BREAK AT B.L."]
                    nrm = np.array([-out[1], out[0]])
                    self.L(c + nrm * 2.5, c - nrm * 2.5, w=0.5, dash="1.5,0.8")
                elif k == "header":
                    lab = [conn.get("label", "").upper(), f"ON {conn.get('ref', '')}"]
                elif k == "cont":
                    lab = ["CONT.: " + conn.get("label", "").upper()]
                elif k == "cap":
                    continue
                else:
                    continue
                p3 = b.pts[0] if side == "s" else b.pts[-1]
                lab.append(fmt_c(p3) + "  " + fmt_el(p3[2]))
                q = c + out * 6.0
                self._boxlabel(q, lab, out)
        for (where, bid, text) in getattr(self, "cont", []):
            pass
        for mark in self.cont:
            bid, d, text = mark
            c = self.at(bid, d)
            u = self.sdir(bid, max(d - 1e-3, 0))
            nrm = np.array([-u[1], u[0]])
            for k in range(3):
                self.L(c + nrm * 2.6 + u * (k - 1) * 0.0, c - nrm * 2.6, w=0.6 if k == 1 else 0.0)
            self.L(c + nrm * 2.4 - u * 0.6, c - nrm * 2.4 + u * 0.6, w=0.35)
            self.L(c + nrm * 2.4 + u * 0.6, c - nrm * 2.4 - u * 0.6, w=0.35)
            b = self.r.br(bid)
            p3 = b.point_at(d)
            self._boxlabel(c + nrm * 6.5, [text, fmt_c(p3) + "  " + fmt_el(p3[2])], nrm, bold=True)

    def _boxlabel(self, q, lines, out, bold=False):
        size = 1.65
        wmax = max(len(s) for s in lines) * size * 0.56 + 2.4
        h = len(lines) * (size + 0.7) + 1.4
        x = q[0] if out[0] >= -0.2 else q[0] - wmax
        y = q[1] - h / 2
        x = min(max(x, 16), self.xr - 9 - wmax)
        y = min(max(y, 16), 246 - h)
        boxes = getattr(self, "_boxes", [])
        for _ in range(12):
            hit = [bb for bb in boxes if x < bb[2] + 1 and x + wmax > bb[0] - 1 and y < bb[3] + 1 and y + h > bb[1] - 1]
            if not hit:
                break
            y = max(bb[3] for bb in hit) + 1.5
            if y + h > 246:
                y = min(bb[1] for bb in hit) - h - 1.5
        boxes.append((x, y, x + wmax, y + h))
        self._boxes = boxes
        self.sh.g.add(self.d.rect((round(x, 2), round(y, 2)), (round(wmax, 2), round(h, 2)), fill="#ffffff",
                                  stroke=INK, stroke_width=0.25))
        for i, s in enumerate(lines):
            self.T(s, x + 1.2, y + 1.0 + (i + 1) * (size + 0.7) - 0.6, size, bold=(i == 0) or bold)

    def _labels(self):
        r = self.r
        # line number along the longest MAIN segment
        bid, i, L = self._longest()
        if bid:
            b = r.br(bid)
            d0v, d1v = self.view[bid]
            a, c = max(b.cum[i], d0v), min(b.cum[i + 1], d1v)
            A, B = self.at(bid, a + (c - a) * 0.3), self.at(bid, a + (c - a) * 0.7)
            u = (B - A) / max(np.linalg.norm(B - A), 1e-9)
            nrm = np.array([-u[1], u[0]])
            side = nrm if np.dot(nrm, (A + B) / 2 - self.cen) >= 0 else -nrm
            m = (A + B) / 2 + side * 7.5
            self.T(r.line_no, m[0], m[1], 2.3, "middle", bold=True, rot=self._readable(u))
            # flow arrows
        for bid in self.lay.bp:
            b = r.br(bid)
            d0v, d1v = self.view[bid]
            for i, s in enumerate(b.seg):
                a, c = max(b.cum[i], d0v), min(b.cum[i + 1], d1v)
                if c - a < 0.3:
                    continue
                A, B = self.at(bid, a), self.at(bid, c)
                if np.linalg.norm(B - A) < 14:
                    continue
                # arrow in a free gap away from fittings
                dm = a + (c - a) * 0.5
                for e in r.elements[bid]:
                    if e["kind"] not in ("pipe",) and e["d0"] - 0.3 <= dm <= e["d1"] + 0.3:
                        dm = a + (c - a) * 0.38
                p = self.at(bid, dm)
                u = (B - A) / np.linalg.norm(B - A)
                nrm = np.array([-u[1], u[0]])
                self.P([p + u * 1.9, p - u * 1.0 + nrm * 1.0, p - u * 1.0 - nrm * 1.0], fill=INK, w=0.1)
        # spool tags
        for sp in r.spools:
            if not self._in_view(sp["branch"], (sp["d0"] + sp["d1"]) / 2):
                continue
            dm = (sp["d0"] + sp["d1"]) / 2
            c = self.at(sp["branch"], dm)
            u = self.sdir(sp["branch"], dm)
            nrm = np.array([-u[1], u[0]])
            side = nrm if np.dot(nrm, c - self.cen) < 0 else -nrm
            q = c + side * 5.0
            self.sh.g.add(self.d.rect((round(q[0] - 3.1, 2), round(q[1] - 1.5, 2)), (6.2, 2.6), rx=1.2, fill="#fff6d5",
                                      stroke="#8a6d00", stroke_width=0.25))
            self.T(sp["id"], q[0], q[1] + 0.6, 1.55, "middle", bold=True, color="#5a4600")
        # slope notes
        for sl in r.slope:
            bid = sl["branch"]
            if bid not in self.lay.bp:
                continue
            b = r.br(bid)
            i = max(range(len(b.seg)), key=lambda k: b.seg[k] if abs((b.pts[k + 1] - b.pts[k])[2]) < 0.3 * b.seg[k] else 0)
            dm = b.cum[i] + b.seg[i] * 0.62
            if not self._in_view(bid, dm):
                continue
            c = self.at(bid, dm)
            q = c + np.array([0, 6.5])
            self.T(f"SLOPE {sl['ratio']} - {sl['note']}", q[0], q[1], 1.7, "middle", bold=True, color="#8a0000")
        # deferred component labels
        for (p, text, size, bold, color) in self.labels:
            self.T(text, p[0], p[1], size, "middle", bold=bold, color=color)

    def _north(self, x, y):
        g = self.d.g(stroke=INK, stroke_width=0.35, fill="none")
        Nv = AXV[1] * 11
        Ev = AXV[0] * 8
        Uv = AXV[2] * 8
        c = np.array([x, y])
        for v, lab, w in ((Nv, "N", 0.6), (Ev, "E", 0.3), (Uv, "UP", 0.3)):
            e = c + v
            g.add(self.d.line(tuple(np.round(c, 2)), tuple(np.round(e, 2)), stroke_width=w))
            u = v / np.linalg.norm(v)
            n = np.array([-u[1], u[0]])
            self.P([e + u * 1.8, e + n * 0.9, e - n * 0.9], fill=INK, w=0.1, g=g)
            self.T(lab, e[0] + u[0] * 4 - 1.0, e[1] + u[1] * 4 + 0.8, 2.4 if lab == "N" else 1.8, bold=lab == "N", g=g)
        self.sh.g.add(g)
        self.T("PLANT NORTH", x - 6, y + 9.5, 1.6)

    # ------------------------------------------------------------------ tables
    def _line_strip(self):
        l, pr, r = self.r.line, self.pr, self.r
        x0, y0 = 15, 252
        cols = [("LINE NUMBER", l["line_no"]), ("FROM", l["from"]), ("TO", l["to"]),
                ("PIPING CLASS", f"{l['cls']} - {pr['rating']}# {specs.cls(l['cls'])['desc'][:30]}"),
                ("DESIGN P / T", f"{l['design_P_barg']} barg / {l['design_T_C']} C"),
                ("OPER. P / T", f"{l['op_P_barg']} barg / {l['op_T_C']} C"),
                ("TEST P (HYDRO)", f"{pr['PT']} barg (1.5xPxST/S={pr['ST_S']})"),
                ("PIPE WALL", f"{pr['sch']} ({pr['t_mm']} mm)" + (" ext.P" if pr.get("ext") else "")),
                ("INSULATION", f"{l['insul']} {pr['insul_mm']} mm" + (" + steam tracing" if l["insul"] == "ST" else "")),
                ("PWHT", pr["pwht"][:34]), ("NDE", pr["nde"][:40]),
                ("STRESS", f"CAT {self.cat[0]} - " + ("; ".join(self.cat[1]))[:42]),
                ("P&ID", l.get("pid_sheet") or "-"), ("FLUID / PHASE", f"{l['fluid']} / {l['phase']}  {l['service'][:24]}"),
                ("PAINT", "HT silicone/Al (insul.)" if l["design_T_C"] > 120 else "Epoxy/PU system"),
                ("SPOOLS / WELDS", f"{len(r.spools)} spools; {sum(1 for w in r.welds if w['type'] == 'S')} shop / "
                                   f"{sum(1 for w in r.welds if w['type'] == 'F')} field")]
        ncol = 4
        cw = (self.xr - 4 - x0) / ncol
        rh = 7.6
        for k, (lab, val) in enumerate(cols):
            cx = x0 + (k % ncol) * cw
            cy = y0 + (k // ncol) * rh
            self.sh.g.add(self.d.rect((round(cx, 2), round(cy, 2)), (round(cw, 2), rh), fill="none", stroke=INK,
                                      stroke_width=0.2))
            self.T(lab, cx + 0.8, cy + 2.2, 1.45, color="#444")
            fs = 1.75 if len(val) < 40 else 1.5
            self.T(val, cx + 0.8, cy + 5.8, fs, bold=(k == 0))

    def bom_rows(self):
        return bom(self.r, self.pr, self.view)

    def _right_tables(self):
        x0, y = self.xr + 1.0, 14.0
        W = self.sh.tb_w - 2.0
        rows = self.bom_rows()
        self.T("BILL OF MATERIALS (THIS SHEET)", x0, y + 2.4, 2.4, bold=True)
        y += 4.0
        hdr = [("PT", 7), ("DESCRIPTION", W - 55), ("NPS", 24), ("QTY", 24)]
        avail_bom = 112.0
        rh = min(3.15, max(2.45, avail_bom / (len(rows) + 3)))
        fs = 1.62 if rh >= 2.9 else 1.42
        self._table(x0, y, hdr, [[str(i + 1), r_[0], r_[1], r_[2]] for i, r_ in enumerate(rows)], rh, fs,
                    groups=[k for k, rr in enumerate(rows) if rr[3]])
        y += rh * (len(rows) + 1) + 4
        # cut lengths
        pcs = [p for p in self.r.pieces if self._in_view(p["branch"], self._piece_d(p))]
        self.T("CUT LENGTHS (mm, ex. weld gap) / SPOOLS", x0, y + 2.2, 2.2, bold=True)
        y += 3.5
        per = 3
        cells = [[p["no"], specs.nps_str(p["nps"]), str(p["L_mm"])] for p in pcs]
        rows2 = [sum(cells[i:i + per], []) for i in range(0, len(cells), per)]
        for rr in rows2:
            while len(rr) < 3 * per:
                rr += ["", "", ""]
        hdr2 = [("PIECE", 18), ("NPS", 13), ("L", 15)] * per
        hdr2 = [(h, w * W / (46 * per)) for h, w in hdr2]
        bottom_limit = self._notes_top() - 4
        rh2 = min(2.8, max(2.1, (bottom_limit - y - 14) / (len(rows2) + 1))) if rows2 else 2.6
        fs2 = 1.45 if rh2 >= 2.5 else 1.25
        self._table(x0, y, hdr2, rows2, rh2, fs2)
        y += rh2 * (len(rows2) + 1) + 3.5
        sps = [s for s in self.r.spools if self._in_view(s["branch"], (s["d0"] + s["d1"]) / 2)]
        txt = "  ".join(f"{s['id']}={s['length']:.1f}m" for s in sps)
        # wrap
        line, lines = "", []
        for tok in txt.split("  "):
            if len(line) + len(tok) > 118:
                lines.append(line)
                line = ""
            line += tok + "  "
        lines.append(line)
        self.T("SPOOL DEVELOPED LENGTHS (transport limit 12.0 x 3.0 x 3.0 m):", x0, y, 1.6, bold=True)
        for i, s in enumerate(lines[:4]):
            self.T(s, x0, y + 2.5 * (i + 1), 1.45)

    def _notes_top(self):
        return self.sh._notes_bottom

    def _piece_d(self, p):
        b = self.r.br(p["branch"])
        for e in self.r.elements[p["branch"]]:
            if e["kind"] == "pipe" and e.get("spool") == p["spool"]:
                return (e["d0"] + e["d1"]) / 2
        return 0.0

    def _table(self, x0, y0, hdr, rows, rh, fs, groups=()):
        xs = [x0]
        for _, w in hdr:
            xs.append(xs[-1] + w)
        n = len(rows) + 1
        g = self.d.g(stroke=INK, stroke_width=0.18, fill="none")
        g.add(self.d.rect((x0, round(y0, 2)), (round(xs[-1] - x0, 2), round(rh * n, 2))))
        for i in range(1, n):
            g.add(self.d.line((x0, round(y0 + rh * i, 2)), (round(xs[-1], 2), round(y0 + rh * i, 2)),
                              stroke_width=0.3 if (i - 1) in groups else 0.12))
        for xx in xs[1:-1]:
            g.add(self.d.line((round(xx, 2), round(y0, 2)), (round(xx, 2), round(y0 + rh * n, 2))))
        self.sh.g.add(g)
        self.sh.g.add(self.d.rect((x0, round(y0, 2)), (round(xs[-1] - x0, 2), rh), fill="#dde4ee", stroke="none"))
        for j, (h, w) in enumerate(hdr):
            self.T(h, xs[j] + 0.7, y0 + rh - 0.75, fs, bold=True)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                maxc = int(hdr[j][1] / (fs * 0.52))
                v = str(val)
                if len(v) > maxc:
                    v = v[: maxc - 1] + "."
                self.T(v, xs[j] + 0.7, y0 + rh * (i + 2) - 0.75, fs)

    def _notes(self):
        r = self.r
        l = r.line
        out = [f"Pipe/fittings/flanges per class {l['cls']} (CFU-000-PI-SPC-001); BW fittings ASME B16.9, flanges B16.5/B16.47A RF.",
               f"Hydrotest {self.pr['PT']} barg per ASME B31.3 345.4 (vents at high points, drains at low points).",
               f"PWHT: {self.pr['pwht'][:60]}. NDE: {self.pr['nde'][:60]}.",
               "Supports: RS rest/shoe, GD guide, ANC anchor, SPR variable spring - tags PS-<area><seq>-nn.",
               "Welds: dot = shop weld, crossed circle FW = field weld; spools <= 12 m for transport."]
        for n in r.notes[:4]:
            out.append(n[:105])
        return out


# ==============================================================================================
def material_desc(r, kind, nps, nps2=None, extra=""):
    k = specs.cls(r.cls)
    m = MATS[k["mat"]]
    hic = " HIC/SSC (NACE MR0103)" if r.cls in ("A2", "A3") else ""
    imp = " impact-tested -29 C" if r.cls == "F1" else ""
    rating = k["rating"]
    w = specs.wall_calc(nps, r.line["design_P_barg"], r.line["design_T_C"], r.cls)
    sch = getattr(r, "_sch_override", {}).get(nps, w["sch"])
    if kind == "pipe":
        base = m["pipe"] if nps <= 24 else m["big"]
        return f"PIPE {sch}, BE, {base}{hic}{imp}"
    if kind == "elbow":
        return f"ELBOW 90 {extra or 'LR'}, BW, {sch}, {m['fit']}"
    if kind == "elbow45":
        return f"ELBOW 45 LR, BW, {sch}, {m['fit']}"
    if kind == "tee":
        return f"TEE {'EQUAL' if nps2 == nps else 'RED.'}, BW, {sch}, {m['fit']}"
    if kind == "reducer":
        return f"REDUCER {extra}, BW, {sch}, {m['fit']}"
    if kind == "cap":
        return f"CAP, BW, {sch}, {m['fit']}"
    if kind == "flange":
        std = "B16.5" if nps <= 24 else "B16.47A"
        return f"FLANGE WN RF CL{rating} {std}, bore {sch}, {m['flg']}{extra}"
    if kind == "olet":
        return f"{'WELDOLET' if (nps2 or 1) >= 2 else 'SOCKOLET 3000#'} (branch), {m['flg']}"
    if kind == "gasket":
        gk = "SPW 321/graphite, inner+outer ring" if k["mat"] in ("P5", "P9") else "SPW 304/graphite, outer ring"
        return f"GASKET {gk}, CL{rating} B16.20"
    if kind == "bolt":
        return f"STUD BOLT SET (nuts) {m['bolt']}, CL{rating}"
    if kind in ("gate", "globe", "check"):
        nm = {"gate": "GATE VALVE OS&Y", "globe": "GLOBE VALVE", "check": "CHECK VALVE SWING"}[kind]
        return f"{nm} CL{rating} RF, {m['valve']}"
    if kind == "cv":
        return f"CONTROL VALVE {extra} CL{rating} RF (by I&C)"
    if kind == "fe":
        return f"ORIFICE PLATE + ORIFICE FLG PAIR {extra} (by I&C)"
    if kind == "strainer":
        return "TEMPORARY CONE STRAINER (commissioning)"
    if kind == "spec":
        return f"SPECTACLE BLIND CL{rating}, {m['flg']}"
    return kind


def bom(r, pr, view=None):
    """[(description, nps text, qty text, group_start)] for elements inside view."""
    def inv(bid, d):
        if view is None:
            return True
        if bid not in view:
            return False
        a, b = view[bid]
        return a - 1e-6 <= d <= b + 1e-6

    fab = OrderedDict()
    ere = OrderedDict()

    def add(tab, key, qty):
        tab[key] = tab.get(key, 0) + qty

    for bid, els in r.elements.items():
        for e in els:
            dm = (e["d0"] + e["d1"]) / 2
            if not inv(bid, dm):
                continue
            k, n = e["kind"], e.get("nps")
            if k == "pipe":
                add(fab, ("pipe", n, None, ""), e["d1"] - e["d0"])
            elif k == "elbow":
                add(fab, ("elbow45" if e.get("angle", 90) < 60 else "elbow", n, None, "SR" if e.get("SR") else "LR"), 1)
            elif k == "tee":
                add(fab, ("tee", n, e.get("nps_b"), ""), 1)
            elif k == "reducer":
                it = e["item"]
                add(fab, ("reducer", max(it["nps"], it["nps2"]), min(it["nps"], it["nps2"]),
                          "ECC" if it.get("ecc") else "CONC"), 1)
            elif k == "cap":
                add(fab, ("cap", n, None, ""), 1)
            elif k == "flange":
                add(fab, ("flange", n, None, " (orifice)" if e.get("orifice") else ""), 1)
            elif k in ("gate", "globe", "check", "strainer", "spec"):
                add(ere, (k, n, None, ""), 1)
            elif k in ("cv", "fe"):
                add(ere, (k, n, None, (e.get("item") or {}).get("tag") or ""), 1)
    for bid in r.elements:
        for o in getattr(r, "_olets", {}).get(bid, []):
            if inv(bid, o["d0"]) and not o.get("child"):
                add(fab, ("olet", o.get("nps_b", 1), o.get("nps_b", 1), ""), 1)
            elif inv(bid, o["d0"]) and o.get("child"):
                add(fab, ("olet", o.get("nps_b", 1), o.get("nps_b", 1), ""), 1)
    for j in r.joints:
        if inv(j["branch"], j["d"]):
            add(ere, ("gasket", j["nps"], None, ""), 1)
            add(ere, ("bolt", j["nps"], None, ""), 1)
    rows = []
    first = True
    for (k, n, n2, ex), q in fab.items():
        nps_t = specs.nps_str(n) + (f" x {specs.nps_str(n2)}" if n2 and k in ("tee", "reducer", "olet") and n2 != n else "")
        if k == "olet":
            nps_t = specs.nps_str(n2)
        qty = f"{q:.1f} m" if k == "pipe" else f"{int(q)}"
        rows.append((material_desc(r, k, n, n2, ex), nps_t, qty, first))
        first = False
    first = True
    for (k, n, n2, ex), q in ere.items():
        rows.append((("ERECTION: " if first else "") + material_desc(r, k, n, n2, ex), specs.nps_str(n), str(int(q)),
                     first))
        first = False
    sup = {}
    for s in r.supports:
        if inv(s["branch"], s["d"]):
            sup[s["type"]] = sup.get(s["type"], 0) + 1
    if sup:
        rows.append(("PIPE SUPPORTS (std. dwgs): " + ", ".join(f"{ {'R': 'rest', 'G': 'guide', 'A': 'anchor', 'S': 'spring'}[k]} x{v}"
                                                               for k, v in sorted(sup.items())), "-",
                     str(sum(sup.values())), True))
    return rows


# ==============================================================================================
def split_views(r, max_vertices=14):
    """Return list of (view, cont_marks). Split MAIN at a vertex if too complex."""
    main = r.branches[0]
    for b in r.branches:
        if b.parent is None:
            main = b
            break
    full = {b.id: (0.0, b.length) for b in r.branches}
    nv = sum(len(b.pts) for b in r.branches)
    if nv <= max_vertices + 6 or len(main.pts) < 10:
        return [(full, [])]
    nsh = 2 if nv <= 2 * max_vertices + 10 else 3
    cuts = []
    for k in range(1, nsh):
        target = main.length * k / nsh
        # cut in the middle of the longest segment near target
        i = min(range(len(main.seg)), key=lambda i: abs((main.cum[i] + main.cum[i + 1]) / 2 - target) - 0.3 * main.seg[i])
        cuts.append(main.cum[i] + main.seg[i] / 2)
    bounds = [0.0] + cuts + [main.length]
    out = []
    for k in range(nsh):
        a, b_ = bounds[k], bounds[k + 1]
        view = {main.id: (a, b_)}
        for c in r.branches:
            if c.id == main.id:
                continue
            anc = c
            ok = False
            while anc.parent:
                par = r.br(anc.parent)
                if par.id == main.id:
                    d = main.d_of_point(anc.pts[0] if anc.start.get("kind") == "tee" else anc.pts[-1], tol=0.05)
                    ok = d is not None and a - 1e-6 <= d <= b_ + 1e-6
                    break
                anc = par
            if ok:
                view[c.id] = (0.0, c.length)
        marks = []
        if k > 0:
            marks.append((main.id, a, f"CONT. FROM SHEET {k}"))
        if k < nsh - 1:
            marks.append((main.id, b_, f"CONT. ON SHEET {k + 2}"))
        out.append((view, marks))
    return out
