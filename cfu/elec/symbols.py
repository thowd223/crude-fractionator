"""IEC 60617 / IEEE 315 style single-line-diagram symbols drawn with svgwrite (mm units).

Every symbol is drawn in a local frame whose origin is the upstream terminal, flowing +y (down);
`rot` rotates the whole symbol about that terminal (rot=-90 -> flows to +x).  Functions return the
downstream terminal coordinate in sheet space.
"""
from __future__ import annotations

import math

from ..drawing.sheet import FONT

LW = 0.35        # normal line
LW_BUS = 1.6     # busbar
INK = "#000000"
RED = "#C00000"


class Pen:
    def __init__(self, sheet, g=None):
        self.sh = sheet
        self.d = sheet.dwg
        self.g = g if g is not None else sheet.g

    # ---------------------------------------------------------------- primitives
    def grp(self, x, y, rot=0):
        t = f"translate({x:.2f},{y:.2f})" + (f" rotate({rot})" if rot else "")
        g = self.d.g(transform=t, fill="none", stroke=INK, stroke_width=LW)
        self.g.add(g)
        return g

    def line(self, x1, y1, x2, y2, w=LW, dash=None, color=INK, g=None):
        kw = dict(stroke=color, stroke_width=w)
        if dash:
            kw["stroke_dasharray"] = dash
        (g or self.g).add(self.d.line((x1, y1), (x2, y2), **kw))

    def poly(self, pts, w=LW, g=None, fill="none", close=False, dash=None):
        kw = dict(stroke=INK, stroke_width=w, fill=fill)
        if dash:
            kw["stroke_dasharray"] = dash
        el = self.d.polygon(pts, **kw) if close else self.d.polyline(pts, **kw)
        (g or self.g).add(el)

    def circle(self, x, y, r, w=LW, g=None, fill="white", dash=None):
        kw = dict(stroke=INK, stroke_width=w, fill=fill)
        if dash:
            kw["stroke_dasharray"] = dash
        (g or self.g).add(self.d.circle((x, y), r, **kw))

    def rect(self, x, y, w, h, lw=LW, g=None, fill="white", dash=None, rx=0):
        kw = dict(stroke=INK, stroke_width=lw, fill=fill)
        if dash:
            kw["stroke_dasharray"] = dash
        if rx:
            kw["rx"] = rx
        (g or self.g).add(self.d.rect((x, y), (w, h), **kw))

    def text(self, s, x, y, size=2.2, anchor="start", bold=False, color=INK, rotate=None, g=None, italic=False):
        t = self.d.text(s, insert=(x, y), font_size=size, text_anchor=anchor, fill=color, stroke="none",
                        font_family=FONT, font_weight="bold" if bold else "normal",
                        font_style="italic" if italic else "normal")
        if rotate:
            t.rotate(rotate, center=(x, y))
        (g or self.g).add(t)

    def lines(self, ls, x, y, size=2.0, lh=None, anchor="start", bold_first=False, color=INK):
        lh = lh or size * 1.3
        for i, s in enumerate(ls):
            if s:
                self.text(s, x, y + i * lh, size, anchor, bold=bold_first and i == 0, color=color)
        return y + len(ls) * lh

    @staticmethod
    def _rot(x, y, dx, dy, rot):
        a = math.radians(rot)
        return x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a)

    # ---------------------------------------------------------------- busbar
    def bus(self, x1, x2, y, name=None, rating=None, name_side="left"):
        self.line(x1, y, x2, y, LW_BUS)
        if name:
            if name_side == "left":
                self.text(name, x1, y - 2.2, 2.8, bold=True)
                if rating:
                    self.text(rating, x1, y + 4.0, 2.0)
            else:
                self.text(name, x2, y - 2.2, 2.8, "end", bold=True)
                if rating:
                    self.text(rating, x2, y + 4.0, 2.0, "end")

    def dot(self, x, y, r=0.7):
        self.g.add(self.d.circle((x, y), r, fill=INK, stroke="none"))

    # ---------------------------------------------------------------- switching devices
    def breaker(self, x, y, rot=0, s=1.0, drawout=True, h=13.0, kind="cb"):
        """kind: cb (X at fixed contact), contactor (semicircle), switch / disconnector (bar), fuse-switch."""
        g = self.grp(x, y, rot)
        h *= s
        fc, pv = 4.2 * s, 9.0 * s
        if drawout:
            self.poly([(-1.4 * s, 0.4 * s), (0, 1.8 * s), (1.4 * s, 0.4 * s)], g=g)
            self.poly([(-1.4 * s, h - 1.8 * s), (0, h - 0.4 * s), (1.4 * s, h - 1.8 * s)], g=g)
            self.line(0, 1.8 * s, 0, fc, g=g)
            self.line(0, pv, 0, h - 1.8 * s, g=g)
        else:
            self.line(0, 0, 0, fc, g=g)
            self.line(0, pv, 0, h, g=g)
        self.line(0, pv, -3.0 * s, fc + 0.5 * s, w=0.45, g=g)       # blade (drawn open per IEC convention)
        c = 1.0 * s
        if kind == "cb":
            self.line(-c, fc - c, c, fc + c, g=g)
            self.line(-c, fc + c, c, fc - c, g=g)
        elif kind == "contactor":
            g.add(self.d.path(d=f"M {-1.1 * s} {fc} A {1.1 * s} {1.1 * s} 0 0 0 {1.1 * s} {fc}", fill="none",
                              stroke=INK, stroke_width=LW))
        elif kind == "switch":
            self.line(-1.2 * s, fc, 1.2 * s, fc, g=g)
        return self._rot(x, y, 0, h, rot)

    def fuse(self, x, y, rot=0, s=1.0, h=8.0):
        g = self.grp(x, y, rot)
        h *= s
        self.line(0, 0, 0, h, g=g)
        self.rect(-1.0 * s, 1.5 * s, 2.0 * s, h - 3 * s, g=g, fill="white")
        self.line(0, 1.5 * s, 0, h - 1.5 * s, g=g)
        return self._rot(x, y, 0, h, rot)

    def overload(self, x, y, s=1.0, h=7.0):
        """Thermal overload relay (IEC: rectangle with thermal element)."""
        g = self.grp(x, y)
        h *= s
        self.line(0, 0, 0, 1.5 * s, g=g)
        self.rect(-1.8 * s, 1.5 * s, 3.6 * s, h - 3 * s, g=g)
        self.poly([(0, 1.5 * s), (0, 2.4 * s), (-0.9 * s, 2.4 * s), (-0.9 * s, h - 2.4 * s), (0, h - 2.4 * s),
                   (0, h - 1.5 * s)], g=g)
        self.line(0, h - 1.5 * s, 0, h, g=g)
        return x, y + h

    # ---------------------------------------------------------------- transformers / machines
    def transformer(self, x, y, r=5.0, prim="D", sec="Y", ngr=None, h_lead=2.0, label=None, label_x=None):
        """Two overlapping circles (IEC); winding marks; neutral to NGR/ground when ngr given."""
        c1 = y + h_lead + r
        c2 = c1 + 1.25 * r
        self.line(x, y, x, y + h_lead)
        self.circle(x, c1, r, fill="none")
        self.circle(x, c2, r, fill="none")
        self._winding(x, c1 - 0.25 * r, prim, r * 0.33)
        self._winding(x, c2 + 0.25 * r, sec, r * 0.33)
        yb = c2 + r
        self.line(x, yb, x, yb + h_lead)
        if ngr:
            xn = x + r + 3.5
            # neutral brought out to the right
            self.line(x + r * 0.95, c2 + 0.2 * r, xn, c2 + 0.2 * r)
            self.line(xn, c2 + 0.2 * r, xn, c2 + 0.2 * r + 1.5)
            self.rect(xn - 1.0, c2 + 0.2 * r + 1.5, 2.0, 5.0)
            self.line(xn, c2 + 0.2 * r + 6.5, xn, c2 + 0.2 * r + 8.0)
            self.ground(xn, c2 + 0.2 * r + 8.0)
            self.text(ngr, xn + 2.0, c2 + 0.2 * r + 5.0, 1.9)
        if label:
            lx = label_x if label_x is not None else x - r - 2.5
            self.lines(label, lx, c1 - 1.5, 2.0, anchor="end" if lx < x else "start", bold_first=True)
        return x, yb + h_lead

    def _winding(self, x, y, kind, a):
        if kind == "D":
            self.poly([(x, y - a), (x + a * 0.95, y + a * 0.6), (x - a * 0.95, y + a * 0.6)], close=True, w=0.3)
        else:
            self.line(x, y, x, y - a, w=0.3)
            self.line(x, y, x + a * 0.87, y + a * 0.5, w=0.3)
            self.line(x, y, x - a * 0.87, y + a * 0.5, w=0.3)

    def motor(self, x, y, r=3.6, lead=2.0, txt="M"):
        self.line(x, y, x, y + lead)
        self.circle(x, y + lead + r, r)
        self.text(txt, x, y + lead + r + 0.6, 2.6, "middle", bold=True)
        self.text("3~", x, y + lead + r + 2.6, 1.5, "middle")
        return x, y + lead + 2 * r

    def ground(self, x, y):
        for i, w in enumerate((2.4, 1.6, 0.8)):
            self.line(x - w, y + i * 0.8, x + w, y + i * 0.8)

    def ct(self, x, y, ratio=None, side="left", n=1, zsct=False):
        """IEC current transformer: circle(s) on the conductor."""
        for i in range(n):
            self.circle(x, y + i * 2.2, 1.3, fill="none")
        if zsct:
            self.g.add(self.d.ellipse((x, y + n * 2.2 + 0.6), (2.4, 0.9), fill="none", stroke=INK, stroke_width=0.3))
        if ratio:
            if side == "left":
                self.text(ratio, x - 2.2, y + 0.8, 1.8, "end")
            else:
                self.text(ratio, x + 2.2, y + 0.8, 1.8)

    def vt(self, x, y, label="VT", ratio=None, fused=True):
        """Bus VT: fuse + two small circles, drawn below the bus at (x, y)."""
        if fused:
            x2, y2 = self.fuse(x, y, s=0.8, h=7)
        else:
            x2, y2 = x, y
        self.line(x, y2, x, y2 + 1.0)
        self.circle(x, y2 + 3.0, 2.0, fill="none")
        self.circle(x, y2 + 5.6, 2.0, fill="none")
        self.lines([label] + ([ratio] if ratio else []), x + 3.0, y2 + 3.0, 1.8)
        return x, y2 + 7.6

    def relays(self, x, y, devs, cols=2, r=2.6, label=None, link_from=None):
        """Protective relay functions (ANSI/IEEE C37.2 device numbers) in circles, grouped in a dashed
        box (multifunction relay)."""
        rows = math.ceil(len(devs) / cols)
        w = cols * 2 * r + (cols + 1) * 0.6
        h = rows * 2 * r + (rows + 1) * 0.6 + (2.6 if label else 0)
        self.rect(x, y, w, h, lw=0.25, dash="1,0.7", fill="white")
        y0 = y + (2.6 if label else 0)
        if label:
            self.text(label, x + w / 2, y + 2.1, 1.7, "middle", bold=True)
        for i, dv in enumerate(devs):
            cx = x + 0.6 + r + (i % cols) * (2 * r + 0.6)
            cy = y0 + 0.6 + r + (i // cols) * (2 * r + 0.6)
            self.circle(cx, cy, r, w=0.3)
            if "/" in dv and len(dv) > 3:
                a, b = dv.split("/", 1)
                fs = 1.5 if max(len(a), len(b)) <= 3 else 1.3
                self.text(a + "/", cx, cy - 0.2, fs, "middle")
                self.text(b, cx, cy + fs + 0.05, fs, "middle")
            else:
                fs = 1.8 if len(dv) <= 3 else 1.5
                self.text(dv, cx, cy + fs * 0.36, fs, "middle")
        if link_from:
            self.line(link_from[0], link_from[1], x, link_from[1], w=0.25, dash="1,0.7")
        return w, h

    def bus_label(self, x, y, lines, anchor="start"):
        """Bus name/rating block stacked above the bus line at its outer end."""
        n = len(lines)
        for i, s in enumerate(lines):
            self.text(s, x, y - 2.0 - (n - 1 - i) * 3.4, 2.7 if i == 0 else 1.9, anchor, bold=i == 0)

    def vfd(self, x, y, w=8.0, h=8.0, label=None, lead=2.0):
        """AC/AC converter (IEC 60617-06-14-xx style): box with diagonal and ~ / ~."""
        self.line(x, y, x, y + lead)
        self.rect(x - w / 2, y + lead, w, h)
        self.line(x - w / 2, y + lead + h, x + w / 2, y + lead)
        self.text("~", x - w / 4, y + lead + h * 0.42, 2.8, "middle")
        self.text("~", x + w / 4, y + lead + h * 0.92, 2.8, "middle")
        self.line(x, y + lead + h, x, y + lead + h + lead)
        if label:
            self.text(label, x + w / 2 + 1.2, y + lead + h / 2 + 0.7, 1.9)
        return x, y + lead + h + lead

    def converter(self, x, y, a="~", b="=", w=10.0, h=10.0, label=None, lead=0.0, label_side="right"):
        self.rect(x - w / 2, y + lead, w, h)
        self.line(x - w / 2, y + lead + h, x + w / 2, y + lead)
        self.text(a, x - w / 4, y + lead + h * 0.42, 3.0 if a == "~" else 2.6, "middle")
        self.text(b, x + w / 4, y + lead + h * 0.9, 3.0 if b == "~" else 2.6, "middle")
        if label:
            if label_side == "right":
                self.lines(label, x + w / 2 + 1.5, y + lead + 3.0, 1.9)
            else:
                self.lines(label, x - w / 2 - 1.5, y + lead + 3.0, 1.9, anchor="end")
        return x, y + lead + h

    def battery(self, x, y, label=None, s=1.0):
        self.line(x, y, x, y + 2 * s)
        for i in range(2):
            yy = y + 2 * s + i * 2.4 * s
            self.line(x - 3.2 * s, yy, x + 3.2 * s, yy, w=0.5)
            self.line(x - 1.6 * s, yy + 1.1 * s, x + 1.6 * s, yy + 1.1 * s, w=1.0)
        self.line(x, y + 2 * s + 4.8 * s - 1.3 * s, x, y + 2 * s + 4.8 * s + 1.0 * s)
        if label:
            self.lines(label, x + 4.5 * s, y + 3.5 * s, 1.9)
        return x, y + 2 * s + 5.8 * s

    def arrow_down(self, x, y, L=5.0):
        self.line(x, y, x, y + L)
        self.poly([(x - 1.1, y + L - 2.2), (x, y + L), (x + 1.1, y + L - 2.2)], close=True, fill=INK)
        return x, y + L

    def cable_tag(self, x, y, txt, side="left", size=1.75):
        """Cable mark: short oblique tick through the conductor + designation."""
        self.line(x - 1.2, y + 1.0, x + 1.2, y - 1.0, w=0.3)
        if side == "left":
            self.text(txt, x - 2.0, y + 0.6, size, "end")
        else:
            self.text(txt, x + 2.0, y + 0.6, size)
