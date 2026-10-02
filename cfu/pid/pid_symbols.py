"""ISA-5.1 style P&ID symbol library drawn on a cfu.drawing.sheet.Sheet (mm units).

All coordinates are drawing mm (origin top-left).  The Canvas keeps separate layers so that
valve / instrument symbols (white filled) always sit on top of pipes and signal lines:

    lines  -> signals -> equipment -> symbols -> text

Orientation codes: 'h' horizontal, 'v' vertical; directions 'r', 'l', 'u', 'd'.
"""
from __future__ import annotations

import math
import textwrap

from ..drawing.sheet import FONT, INK

LW_MAIN = 0.55      # main process line
LW_UTIL = 0.38      # utility / secondary line
LW_SIG = 0.25       # instrument signal
LW_EQ = 0.5         # equipment outline
CW = 0.60           # average glyph width / font size (DejaVu Sans)

DIRV = {"r": (1, 0), "l": (-1, 0), "u": (0, -1), "d": (0, 1)}


def text_w(s, size):
    return len(s) * size * CW


class Canvas:
    def __init__(self, sheet, reg=None, sheet_id=None):
        self.sh = sheet
        self.reg = reg                  # pid_data.Registry (lines + instruments) or None
        self.sid = sheet_id             # e.g. "CFU-100-PR-PID-001"
        d = self.d = sheet.dwg
        self.g_ln = d.g(fill="none", stroke=INK, stroke_width=LW_MAIN, stroke_linejoin="miter")
        self.g_sg = d.g(fill="none", stroke=INK, stroke_width=LW_SIG)
        self.g_eq = d.g(fill="none", stroke=INK, stroke_width=LW_EQ)
        self.g_sy = d.g(fill="white", stroke=INK, stroke_width=0.35)
        self.g_tx = d.g(font_family=FONT, fill=INK, stroke="none")
        for g in (self.g_ln, self.g_sg, self.g_eq, self.g_sy, self.g_tx):
            sheet.g.add(g)

    # ------------------------------------------------------------------ text
    def t(self, s, x, y, size=2.3, anchor="start", bold=False, rot=None, italic=False, g=None):
        el = self.d.text(s, insert=(x, y), font_size=size, text_anchor=anchor,
                         font_weight="bold" if bold else "normal", font_style="italic" if italic else "normal")
        if rot:
            el.rotate(rot, center=(x, y))
        (g or self.g_tx).add(el)
        return el

    def tlines(self, lines, x, y, size=2.3, anchor="start", lh=None, bold_first=False):
        lh = lh or size * 1.3
        for i, s in enumerate(lines):
            self.t(s, x, y + i * lh, size, anchor, bold=bold_first and i == 0)

    # ------------------------------------------------------------------ pipes
    def pipe(self, pts, arrow=True, util=False, dash=None, w=None, mid_arrow=None):
        kw = dict(stroke_width=w or (LW_UTIL if util else LW_MAIN))
        if dash:
            kw["stroke_dasharray"] = dash
        self.g_ln.add(self.d.polyline(pts, **kw))
        if arrow:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            self.arrow(x2, y2, _dir(x1, y1, x2, y2))
        if mid_arrow is not None:
            (x1, y1), (x2, y2) = pts[mid_arrow], pts[mid_arrow + 1]
            self.arrow((x1 + x2) / 2, (y1 + y2) / 2, _dir(x1, y1, x2, y2), L=2.2)

    def arrow(self, x, y, d, L=2.6, Wd=1.0):
        dx, dy = DIRV[d]
        px, py = -dy, dx
        pts = [(x, y), (x - dx * L + px * Wd, y - dy * L + py * Wd), (x - dx * L - px * Wd, y - dy * L - py * Wd)]
        self.g_sy.add(self.d.polygon(pts, fill=INK, stroke=INK, stroke_width=0.2))

    def dot(self, x, y, r=0.6):
        self.g_sy.add(self.d.circle((x, y), r, fill=INK, stroke="none"))

    def hop(self, x, y, o="h", r=1.4):
        """Line crossing: white gap on the crossed line (call on the line that is broken)."""
        if o == "h":
            self.g_sy.add(self.d.rect((x - r, y - 0.6), (2 * r, 1.2), fill="white", stroke="none"))
        else:
            self.g_sy.add(self.d.rect((x - 0.6, y - r), (1.2, 2 * r), fill="white", stroke="none"))

    def line(self, key, pts, lab=0, at=0.5, side=-1, arrow=True, util=None, dash=None, mid_arrow=None,
             lab_xy=None, lab_rot=None, size=2.0):
        """Draw a registered line (key in registry) and label it with its line number."""
        ln = self.reg.use_line(key, self.sid) if self.reg else {"line_no": key, "util": False}
        if util is None:
            util = ln.get("util", False)
        self.pipe(pts, arrow=arrow, util=util, dash=dash, mid_arrow=mid_arrow)
        if lab is not None or lab_xy:
            self.lab(ln["line_no"], pts, lab or 0, at, side, lab_xy, lab_rot, size)
        return ln

    def lab(self, s, pts=None, seg=0, at=0.5, side=-1, xy=None, rot=None, size=2.0):
        if xy:
            x, y = xy
            self.t(s, x, y, size, "middle", rot=rot)
            return
        (x1, y1), (x2, y2) = pts[seg], pts[seg + 1]
        x, y = x1 + (x2 - x1) * at, y1 + (y2 - y1) * at
        if abs(y2 - y1) < 1e-6:  # horizontal
            self.t(s, x, y - 1.1 if side < 0 else y + size + 0.9, size, "middle")
        else:
            xx = x - 1.1 if side < 0 else x + size + 0.6
            self.t(s, xx, y, size, "middle", rot=-90)

    def key_no(self, key):
        return self.reg.lines[key]["line_no"] if self.reg else key

    # ------------------------------------------------------------------ in-line valves
    def _bowtie(self, x, y, o, a=2.6, b=1.6, fill="white"):
        if o == "h":
            t1 = [(x - a, y - b), (x - a, y + b), (x, y)]
            t2 = [(x + a, y - b), (x + a, y + b), (x, y)]
        else:
            t1 = [(x - b, y - a), (x + b, y - a), (x, y)]
            t2 = [(x - b, y + a), (x + b, y + a), (x, y)]
        for t in (t1, t2):
            self.g_sy.add(self.d.polygon(t, fill=fill))

    def gate(self, x, y, o="h", nc=False, note=None, note_side=1):
        self._bowtie(x, y, o, fill=INK if nc else "white")
        if note:
            self._vnote(x, y, o, note, note_side)

    def globe(self, x, y, o="h", note=None, note_side=1):
        self._bowtie(x, y, o)
        self.dot(x, y, 0.75)
        if note:
            self._vnote(x, y, o, note, note_side)

    def ball(self, x, y, o="h", note=None, note_side=1):
        self._bowtie(x, y, o)
        self.g_sy.add(self.d.circle((x, y), 0.95, fill="white"))
        if note:
            self._vnote(x, y, o, note, note_side)

    def butterfly(self, x, y, o="h"):
        self.g_sy.add(self.d.circle((x, y), 1.8, fill="white"))
        if o == "h":
            self.g_sy.add(self.d.line((x - 1.3, y + 1.3), (x + 1.3, y - 1.3)))
        else:
            self.g_sy.add(self.d.line((x - 1.3, y - 1.3), (x + 1.3, y + 1.3)))

    def check(self, x, y, d="r"):
        dx, dy = DIRV[d]
        px, py = -dy, dx
        a, b = 2.4, 1.7
        tri = [(x + dx * a, y + dy * a), (x - dx * a + px * b, y - dy * a + py * b),
               (x - dx * a - px * b, y - dy * a - py * b)]
        self.g_sy.add(self.d.polygon(tri, fill="white"))
        self.g_sy.add(self.d.line((x + dx * a + px * b, y + dy * a + py * b),
                                  (x + dx * a - px * b, y + dy * a - py * b), stroke_width=0.5))

    def _vnote(self, x, y, o, s, side=1):
        if o == "h":
            self.t(s, x, y - 2.6 if side < 0 else y + 4.6, 2.0, "middle")
        else:
            self.t(s, x + 2.6 if side > 0 else x - 2.6, y + 0.8, 2.0, "start" if side > 0 else "end")

    def reducer(self, x, y, o="h", big_first=True, note=None, note_side=1):
        a, b1, b2 = 1.6, 1.8, 1.0
        if not big_first:
            b1, b2 = b2, b1
        if o == "h":
            pts = [(x - a, y - b1), (x + a, y - b2), (x + a, y + b2), (x - a, y + b1)]
        else:
            pts = [(x - b1, y - a), (x + b1, y - a), (x + b2, y + a), (x - b2, y + a)]
        self.g_sy.add(self.d.polygon(pts, fill="white"))
        if note:
            self._vnote(x, y, o, note, note_side)

    def strainer(self, x, y, o="h"):
        if o == "h":
            self.g_sy.add(self.d.rect((x - 2.2, y - 1.5), (4.4, 3.0), fill="white"))
            self.g_sy.add(self.d.line((x - 2.2, y + 1.5), (x + 2.2, y - 1.5), stroke_dasharray="0.8,0.5"))
        else:
            self.g_sy.add(self.d.rect((x - 1.5, y - 2.2), (3.0, 4.4), fill="white"))
            self.g_sy.add(self.d.line((x - 1.5, y + 2.2), (x + 1.5, y - 2.2), stroke_dasharray="0.8,0.5"))

    def orifice(self, x, y, o="h", ro=False):
        """Flow element (orifice plate) or restriction orifice (ro=True, labelled RO)."""
        if o == "h":
            self.g_sy.add(self.d.line((x - 0.6, y - 2.4), (x - 0.6, y + 2.4), stroke_width=0.45))
            self.g_sy.add(self.d.line((x + 0.6, y - 2.4), (x + 0.6, y + 2.4), stroke_width=0.45))
        else:
            self.g_sy.add(self.d.line((x - 2.4, y - 0.6), (x + 2.4, y - 0.6), stroke_width=0.45))
            self.g_sy.add(self.d.line((x - 2.4, y + 0.6), (x + 2.4, y + 0.6), stroke_width=0.45))
        if ro:
            if o == "h":
                self.t("RO", x, y + 5.0, 2.0, "middle")
            else:
                self.t("RO", x + 3.2, y + 0.8, 2.0)

    def blind(self, x, y, o="h", closed=False):
        """Spectacle blind (figure-8)."""
        r = 1.2
        if o == "h":
            c1, c2 = (x, y - r), (x, y + r)
        else:
            c1, c2 = (x - r, y), (x + r, y)
        self.g_sy.add(self.d.circle(c1, r, fill=INK if closed else "white"))
        self.g_sy.add(self.d.circle(c2, r, fill="white" if closed else INK))

    def spec_break(self, x, y, o="h", c1="", c2=""):
        """Piping class break: perpendicular bar with the two class codes."""
        if o == "h":
            self.g_sy.add(self.d.line((x, y - 3.2), (x, y + 3.2), stroke_width=0.4))
            self.t(c1, x - 0.8, y - 3.8, 2.0, "end")
            self.t(c2, x + 0.8, y - 3.8, 2.0, "start")
        else:
            self.g_sy.add(self.d.line((x - 3.2, y), (x + 3.2, y), stroke_width=0.4))
            self.t(c1, x + 3.6, y - 0.8, 2.0)
            self.t(c2, x + 3.6, y + 2.6, 2.0)

    def vent(self, x, y, d="u", L=5.5, drain=False):
        """Vent / drain stub with gate valve and blind flange/cap."""
        dx, dy = DIRV[d]
        x2, y2 = x + dx * L, y + dy * L
        self.g_ln.add(self.d.line((x, y), (x2, y2), stroke_width=LW_UTIL))
        o = "v" if dx == 0 else "h"
        self._bowtie(x + dx * L * 0.55, y + dy * L * 0.55, o, a=1.5, b=1.0)
        px, py = -dy, dx
        self.g_sy.add(self.d.line((x2 + px * 1.3, y2 + py * 1.3), (x2 - px * 1.3, y2 - py * 1.3), stroke_width=0.6))

    # ------------------------------------------------------------------ actuated valves
    def cv(self, x, y, o="h", tag="", fail="FC", act="dia", side=-1, tag_pos=None, kind="globe"):
        """Control valve: globe body + diaphragm actuator.  side=-1 actuator above (h) / left (v)."""
        if kind == "ball":
            self.ball(x, y, o)
        elif kind == "butterfly":
            self.butterfly(x, y, o)
        else:
            self._bowtie(x, y, o)
            self.dot(x, y, 0.75)
        L = 4.2
        if o == "h":
            sx, sy, ex, ey = x, y - 1.0 * (1 if side < 0 else -1), x, y + side * L
        else:
            sx, sy, ex, ey = x + side * 1.0, y, x + side * L, y
        self.g_sy.add(self.d.line((sx, sy), (ex, ey), stroke_width=0.35))
        self.actuator(ex, ey, o, side, act)
        # tag + fail action
        if o == "h":
            ax, ay = ex, ey + side * 3.0
            tx, ty = tag_pos or (x + 3.6, ay + (1.0 if side < 0 else 2.0))
            if tag:
                self.t(tag, tx, ty - 0.6, 2.2, "start", bold=True)
            if fail:
                self.t(fail, tx, ty + 2.2, 2.0, "start")
        else:
            ax = ex + side * 3.0
            tx, ty = tag_pos or ((ax + side * 1.5), y - 3.6)
            anc = "start" if side > 0 else "end"
            if tag:
                self.t(tag, tx, ty, 2.2, anc, bold=True)
            if fail:
                self.t(fail, tx, ty + 2.4, 2.0, anc)

    def actuator(self, x, y, o, side, act="dia"):
        r = 2.6
        if act == "dia":
            if o == "h":
                sweep = 1 if side < 0 else 0
                p = self.d.path(d=f"M {x - r},{y} A {r},{r} 0 0 {sweep} {x + r},{y} Z", fill="white")
            else:
                sweep = 1 if side > 0 else 0
                p = self.d.path(d=f"M {x},{y - r} A {r},{r} 0 0 {sweep} {x},{y + r} Z", fill="white")
            self.g_sy.add(p)
        elif act == "onoff":   # on/off actuator with solenoid (S)
            if o == "h":
                yy = y - 3.2 if side < 0 else y
                self.g_sy.add(self.d.rect((x - 2.4, yy), (4.8, 3.2), fill="white"))
                self.t("S", x, yy + 2.5, 2.0, "middle", bold=True)
            else:
                xx = x - 4.8 if side < 0 else x
                self.g_sy.add(self.d.rect((xx, y - 1.6), (4.8, 3.2), fill="white"))
                self.t("S", xx + 2.4, y + 0.8, 2.0, "middle", bold=True)
        elif act == "motor":
            if o == "h":
                yy = y - 3.6 if side < 0 else y
                self.g_sy.add(self.d.rect((x - 2.4, yy), (4.8, 3.6), fill="white"))
                self.t("M", x, yy + 2.7, 2.2, "middle", bold=True)
            else:
                xx = x - 4.8 if side < 0 else x
                self.g_sy.add(self.d.rect((xx, y - 1.8), (4.8, 3.6), fill="white"))
                self.t("M", xx + 2.4, y + 0.8, 2.2, "middle", bold=True)

    def station(self, x0, y0, x1, y1, tag, fail="FC", byp=1, bypass=True, red=True, side=-1, tag_pos=None,
                kind="globe", act="dia", drain=True):
        """Control valve station on a straight run (x0,y0)-(x1,y1) (pipe drawn by caller).
        Block valves both sides, bypass globe valve (offset byp*8 mm), drain between block and CV."""
        if abs(y1 - y0) < 1e-6:     # horizontal
            o, y = "h", y0
            xa, xb = min(x0, x1), max(x0, x1)
            xm = (xa + xb) / 2
            self.gate(xa + 4.5, y, "h")
            self.gate(xb - 4.5, y, "h")
            if red:
                self.reducer(xm - 5.2, y, "h", True)
                self.reducer(xm + 5.2, y, "h", False)
            self.cv(xm, y, "h", tag, fail, act, side, tag_pos, kind)
            if drain:
                self.vent(xa + 8.2, y, "d" if byp < 0 else "u", 4.0)
            if bypass:
                yb = y + byp * 8.5
                self.g_ln.add(self.d.polyline([(xa + 1.2, y), (xa + 1.2, yb), (xb - 1.2, yb), (xb - 1.2, y)],
                                              stroke_width=LW_UTIL))
                self.dot(xa + 1.2, y)
                self.dot(xb - 1.2, y)
                self.globe(xm, yb, "h")
        else:
            o, x = "v", x0
            ya, yb_ = min(y0, y1), max(y0, y1)
            ym = (ya + yb_) / 2
            self.gate(x, ya + 4.5, "v")
            self.gate(x, yb_ - 4.5, "v")
            if red:
                self.reducer(x, ym - 5.2, "v", True)
                self.reducer(x, ym + 5.2, "v", False)
            self.cv(x, ym, "v", tag, fail, act, side, tag_pos, kind)
            if drain:
                self.vent(x, ya + 8.2, "r" if byp < 0 else "l", 4.0)
            if bypass:
                xb2 = x + byp * 8.5
                self.g_ln.add(self.d.polyline([(x, ya + 1.2), (xb2, ya + 1.2), (xb2, yb_ - 1.2), (x, yb_ - 1.2)],
                                              stroke_width=LW_UTIL))
                self.dot(x, ya + 1.2)
                self.dot(x, yb_ - 1.2)
                self.globe(xb2, ym, "v")

    def xv(self, x, y, o="h", tag="", fail="FC", side=-1, tag_pos=None, kind="ball"):
        """On/off (SIS / ESD) valve with solenoid actuator and limit switches note."""
        self.cv(x, y, o, tag, fail, "onoff", side, tag_pos, kind)

    # ------------------------------------------------------------------ relief valve
    def psv(self, x, y, tag, set_barg, orifice="", up=14, out="r", outlen=12, dest="FLARE", blocks=True,
            text_side=None):
        """Pressure safety valve.  (x,y) = inlet connection on protected item (inlet rises 'up' mm).
        Body at (x, y-up); outlet horizontal (out='r'/'l') to destination arrow."""
        bx, by = x, y - up
        self.g_ln.add(self.d.line((x, y), (bx, by + 2.6), stroke_width=LW_UTIL))
        sgn = 1 if out == "r" else -1
        ox = bx + sgn * outlen
        self.g_ln.add(self.d.line((bx + sgn * 2.6, by), (ox, by), stroke_width=LW_UTIL))
        self.arrow(ox, by, out, L=2.2)
        # angle body
        a, b = 2.6, 1.6
        self.g_sy.add(self.d.polygon([(bx - b, by + a), (bx + b, by + a), (bx, by)], fill="white"))
        self.g_sy.add(self.d.polygon([(bx + sgn * a, by - b), (bx + sgn * a, by + b), (bx, by)], fill="white"))
        # spring bonnet
        pts = [(bx, by), (bx, by - 1.2)]
        for i in range(4):
            pts.append((bx + (1.2 if i % 2 == 0 else -1.2), by - 1.8 - i * 0.9))
        pts.append((bx, by - 5.6))
        self.g_sy.add(self.d.polyline(pts, fill="none", stroke_width=0.35))
        if blocks:
            self.gate(x, y - up * 0.42, "v", note="CSO", note_side=-sgn if text_side is None else -text_side)
            self.gate(bx + sgn * outlen * 0.6, by, "h", note="CSO", note_side=1)
        ts = text_side if text_side is not None else -sgn
        tx = bx + ts * 3.2
        anc = "start" if ts > 0 else "end"
        self.t(tag, tx, by - 7.0, 2.2, anc, bold=True)
        self.t(f"SET {set_barg:g} barg", tx, by - 4.5, 2.0, anc)
        if orifice:
            self.t(orifice, tx, by - 2.1, 2.0, anc)
        self.t(dest, ox + sgn * 1.2, by + 0.8, 2.0, "start" if sgn > 0 else "end")
        if self.reg:
            self.reg.inst(tag, self.sid)

    # ------------------------------------------------------------------ instruments
    def bub(self, x, y, tag, kind="field", r=4.6, reg=True, svc=None, **kw):
        """Instrument bubble.  kind: field | dcs | sis | panel | plc."""
        letters, num = tag.split("-", 1)
        if len(letters) >= 4 or len(num) > 4:
            r = max(r, 5.4)
        if kind in ("dcs", "sis", "plc"):
            self.g_sy.add(self.d.rect((x - r, y - r), (2 * r, 2 * r), fill="white"))
        if kind == "sis":
            self.g_sy.add(self.d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill="white"))
        elif kind == "plc":
            self.g_sy.add(self.d.polygon([(x - r * 0.6, y - r), (x + r * 0.6, y - r), (x + r, y),
                                          (x + r * 0.6, y + r), (x - r * 0.6, y + r), (x - r, y)], fill="white"))
        else:
            self.g_sy.add(self.d.circle((x, y), r, fill="white"))
        if kind in ("dcs", "sis", "panel", "plc"):
            lx = r * (0.62 if kind == "sis" else 1.0)
            self.g_sy.add(self.d.line((x - lx, y), (x + lx, y), stroke_width=0.3))
        fs = 2.2 if len(letters) <= 3 else 2.0
        fn = 2.0
        self.t(letters, x, y - 0.75, fs, "middle", bold=True)
        self.t(num, x, y + 2.75, fn, "middle")
        if reg and self.reg:
            self.reg.inst(tag, self.sid, kind=kind, svc=svc, **kw)
        return (x, y)

    def sig(self, pts, kind="e"):
        """Signal line: e = electrical (dashed), d = data/software link (line with circles), p = pneumatic."""
        if kind == "e":
            self.g_sg.add(self.d.polyline(pts, stroke_dasharray="1.6,0.9"))
        elif kind == "d":
            self.g_sg.add(self.d.polyline(pts))
            for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
                L = math.hypot(x2 - x1, y2 - y1)
                n = int(L // 4.5)
                for i in range(1, n):
                    f = i / n
                    self.g_sg.add(self.d.circle((x1 + (x2 - x1) * f, y1 + (y2 - y1) * f), 0.5, fill="white"))
        elif kind == "p":
            self.g_sg.add(self.d.polyline(pts))
        elif kind == "c":    # process impulse / capillary connection (thin solid)
            self.g_sg.add(self.d.polyline(pts, stroke_width=0.3))

    def tap(self, pts):
        self.sig(pts, "c")

    def ilk(self, x, y, text, r=4.0, below=True):
        self.g_sy.add(self.d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill="white"))
        self.t("I", x, y + 0.9, 2.4, "middle", bold=True)
        if text:
            if below:
                self.t(text, x, y + r + 2.4, 2.0, "middle", bold=True)
            else:
                self.t(text, x + r + 0.8, y + 0.8, 2.0, "start", bold=True)

    # ------------------------------------------------------------------ off-page connector
    def opc(self, x, y, ext="l", l1="", l2="", flow=None, w=31, h=9.5):
        """Off-page connector attached at line end (x,y), box extending to side ext ('l'/'r').
        flow 'in' (default when ext='l'): arrow tip at (x,y); 'out' (default when ext='r'): tip at far end."""
        flow = flow or ("in" if ext == "l" else "out")
        sgn = -1 if ext == "l" else 1
        xf = x + sgn * w
        tip = 3.5
        near_tip = flow == "in"
        xa, xb = (x, xf) if not near_tip else (xf, x)     # xa = flat end, xb = tip end
        s2 = 1 if xb > xa else -1
        pts = [(xa, y - h / 2), (xb - s2 * tip, y - h / 2), (xb, y), (xb - s2 * tip, y + h / 2), (xa, y + h / 2)]
        self.g_sy.add(self.d.polygon(pts, fill="white", stroke_width=0.45))
        cx = (xa + xb - s2 * tip) / 2
        self.t(l1, cx, y - 0.6, 2.1, "middle", bold=True)
        self.t(l2, cx, y + 3.1, 2.0, "middle")

    def opcv(self, x, y, ext="u", l1="", l2="", flow=None, w=31, h=9.5):
        """Off-page connector for a vertical line end (x,y); box above (ext='u') or below (ext='d')."""
        flow = flow or ("in" if ext == "u" else "out")
        sgn = -1 if ext == "u" else 1
        yf = y + sgn * (h + 3.5)
        tip = 3.5
        if flow == "in":     # tip at the line end
            ya, yb = yf, y
        else:
            ya, yb = y, yf
        s2 = 1 if yb > ya else -1
        pts = [(x - w / 2, ya), (x + w / 2, ya), (x + w / 2, yb - s2 * tip), (x, yb), (x - w / 2, yb - s2 * tip)]
        self.g_sy.add(self.d.polygon(pts, fill="white", stroke_width=0.45))
        top = min(ya, yb - s2 * tip)
        self.t(l1, x, top + 4.0, 2.1, "middle", bold=True)
        self.t(l2, x, top + 7.6, 2.0, "middle")

    # ------------------------------------------------------------------ equipment
    def eqbox(self, x, y, w, lines, tag):
        """Equipment data box (top band)."""
        wrapped = []
        for s in lines:
            wrapped += textwrap.wrap(s, int(w / (2.1 * CW))) or [""]
        h = 6.0 + 2.8 * len(wrapped) + 1.5
        self.g_eq.add(self.d.rect((x, y), (w, h), stroke_width=0.35))
        self.t(tag, x + w / 2, y + 4.4, 3.0, "middle", bold=True)
        for i, s in enumerate(wrapped):
            self.t(s, x + 1.5, y + 8.6 + i * 2.8, 2.1)
        return h

    def head(self, x0, x1, y, up=True, depth=None):
        """Semi-elliptical head between x0..x1 at y (up = dome above y)."""
        r = (x1 - x0) / 2
        dpt = depth or min(r * 0.5, 9)
        sweep = 1 if up else 0
        self.g_eq.add(self.d.path(d=f"M {x0},{y} A {r},{dpt} 0 0 {sweep} {x1},{y}"))

    def brk(self, x0, x1, y):
        """Break line across a vessel (zig-zag)."""
        m = (x0 + x1) / 2
        pts = [(x0 - 3, y), (m - 2, y), (m - 0.5, y - 2.2), (m + 0.5, y + 2.2), (m + 2, y), (x1 + 3, y)]
        self.g_eq.add(self.d.polyline(pts, stroke_width=0.35))

    def column(self, x, y0, y1, w, tag=None, top=True, bot=True, brk_top=False, brk_bot=False):
        x0, x1 = x - w / 2, x + w / 2
        self.g_eq.add(self.d.line((x0, y0), (x0, y1)))
        self.g_eq.add(self.d.line((x1, y0), (x1, y1)))
        if top:
            self.head(x0, x1, y0, True)
        if bot:
            self.head(x0, x1, y1, False)
        if brk_top:
            self.brk(x0, x1, y0)
        if brk_bot:
            self.brk(x0, x1, y1)

    def tray(self, x, w, y, n, dc="l", num_side="r", label=True):
        """Single tray with downcomer on side dc ('l'/'r')."""
        x0, x1 = x - w / 2, x + w / 2
        gap = w * 0.18
        if dc == "l":
            self.g_eq.add(self.d.line((x0 + gap, y), (x1, y), stroke_width=0.35))
            self.g_eq.add(self.d.line((x0 + gap, y), (x0 + gap, y + 3.0), stroke_width=0.3))
        else:
            self.g_eq.add(self.d.line((x0, y), (x1 - gap, y), stroke_width=0.35))
            self.g_eq.add(self.d.line((x1 - gap, y), (x1 - gap, y + 3.0), stroke_width=0.3))
        if label:
            if num_side == "r":
                self.t(str(n), x1 - 1.2, y - 0.6, 2.0, "end")
            else:
                self.t(str(n), x0 + 1.2, y - 0.6, 2.0, "start")

    def trays(self, x, w, ys, nums, num_side="r"):
        for i, (y, n) in enumerate(zip(ys, nums)):
            self.tray(x, w, y, n, "l" if n % 2 else "r", num_side if n % 2 == 0 else ("l" if num_side == "r" else "r"))

    def pan(self, x, w, y, label=None):
        """Chimney tray / total draw-off pan."""
        x0, x1 = x - w / 2, x + w / 2
        self.g_eq.add(self.d.line((x0, y), (x1, y), stroke_width=0.6))
        for f in (0.3, 0.7):
            cx = x0 + w * f
            self.g_eq.add(self.d.rect((cx - 1.5, y - 4), (3, 4), stroke_width=0.3))
            self.g_eq.add(self.d.line((cx - 2.5, y - 5), (cx + 2.5, y - 5), stroke_width=0.3))
        if label:
            self.t(label, x, y + 3.0, 2.0, "middle")

    def bed(self, x, w, y0, y1, label=None):
        x0 = x - w / 2 + 1.2
        ww = w - 2.4
        self.g_eq.add(self.d.rect((x0, y0), (ww, y1 - y0), stroke_width=0.35))
        self.g_eq.add(self.d.line((x0, y0), (x0 + ww, y1), stroke_width=0.25))
        self.g_eq.add(self.d.line((x0 + ww, y0), (x0, y1), stroke_width=0.25))
        if label:
            self.g_sy.add(self.d.rect((x - text_w(label, 2.1) / 2 - 1, (y0 + y1) / 2 - 2.6),
                                      (text_w(label, 2.1) + 2, 3.8), fill="white", stroke="none"))
            self.t(label, x, (y0 + y1) / 2 + 0.6, 2.1, "middle")

    def distributor(self, x, w, y):
        x0, x1 = x - w / 2 + 2, x + w / 2 - 2
        self.g_eq.add(self.d.line((x0, y), (x1, y), stroke_width=0.35))
        n = int((x1 - x0) // 4)
        for i in range(n + 1):
            xx = x0 + i * (x1 - x0) / max(n, 1)
            self.g_eq.add(self.d.polygon([(xx - 0.8, y), (xx + 0.8, y), (xx, y + 1.4)], fill=INK, stroke="none"))

    def noz(self, x, y, d, label=None, L=2.5):
        dx, dy = DIRV[d]
        self.g_eq.add(self.d.line((x, y), (x + dx * L, y + dy * L), stroke_width=0.5))
        px, py = -dy, dx
        xe, ye = x + dx * L, y + dy * L
        self.g_eq.add(self.d.line((xe + px * 1.3, ye + py * 1.3), (xe - px * 1.3, ye - py * 1.3), stroke_width=0.5))
        if label:
            if d in ("l", "r"):
                self.t(label, x + dx * 1.0, y - 1.6, 1.9, "end" if d == "l" else "start", italic=True)
            else:
                self.t(label, x + 1.4, y + dy * 1.6 + (1.5 if d == "d" else 0), 1.9, "start", italic=True)
        return (xe, ye)

    def hdrum(self, x, y, L, D, boot=None):
        """Horizontal drum: (x,y) = left tangent line top; boot = (x_center, width, depth)."""
        self.g_eq.add(self.d.line((x, y), (x + L, y)))
        self.g_eq.add(self.d.line((x, y + D), (x + L, y + D)))
        dpt = min(D * 0.35, 6)
        self.g_eq.add(self.d.path(d=f"M {x},{y} A {dpt},{D / 2} 0 0 0 {x},{y + D}"))
        self.g_eq.add(self.d.path(d=f"M {x + L},{y} A {dpt},{D / 2} 0 0 1 {x + L},{y + D}"))
        if boot:
            bx, bw, bd = boot
            self.g_eq.add(self.d.polyline([(bx - bw / 2, y + D), (bx - bw / 2, y + D + bd)]))
            self.g_eq.add(self.d.polyline([(bx + bw / 2, y + D), (bx + bw / 2, y + D + bd)]))
            self.head(bx - bw / 2, bx + bw / 2, y + D + bd, False, depth=2.0)

    def vdrum(self, x, y0, D, H):
        self.column(x, y0, y0 + H, D)

    def hx(self, x, y, L=34, H=11, kind="tema", label=None, rev=False):
        """Shell & tube exchanger, horizontal.  (x,y) = centre.  Channel at left (rev=True: right).
        Returns nozzle dict: ct (channel top), cb (channel bottom), st_* shell top at near/far end,
        sb_* shell bottom."""
        s = -1 if rev else 1
        xl, xr = x - L / 2, x + L / 2
        ch = 6.5
        if not rev:
            self.g_eq.add(self.d.rect((xl, y - H / 2), (ch, H)))
            self.g_eq.add(self.d.path(d=f"M {xl + ch},{y - H / 2} L {xr - H / 2},{y - H / 2} "
                                        f"A {H / 2},{H / 2} 0 0 1 {xr - H / 2},{y + H / 2} L {xl + ch},{y + H / 2}"))
            self.g_eq.add(self.d.line((xl + ch + 1.0, y - H / 2 + 1.0), (xr - 3, y - H / 2 + 1.0), stroke_width=0.25,
                                      stroke_dasharray="1,1"))
            cx = xl + ch / 2
            near, far = xl + ch + 5, xr - H / 2 - 2
        else:
            self.g_eq.add(self.d.rect((xr - ch, y - H / 2), (ch, H)))
            self.g_eq.add(self.d.path(d=f"M {xr - ch},{y - H / 2} L {xl + H / 2},{y - H / 2} "
                                        f"A {H / 2},{H / 2} 0 0 0 {xl + H / 2},{y + H / 2} L {xr - ch},{y + H / 2}"))
            cx = xr - ch / 2
            near, far = xr - ch - 5, xl + H / 2 + 2
        n = dict(ct=(cx, y - H / 2), cb=(cx, y + H / 2), st_near=(near, y - H / 2), st_far=(far, y - H / 2),
                 sb_near=(near, y + H / 2), sb_far=(far, y + H / 2), end=(xr if not rev else xl, y))
        return n

    def kettle(self, x, y, L=40, H=11, Hk=18):
        """Kettle reboiler/steam generator: tube bundle (channel left) in enlarged shell."""
        xl, xr = x - L / 2, x + L / 2
        ch = 6.5
        self.g_eq.add(self.d.rect((xl, y - H / 2), (ch, H)))
        k0 = xl + ch + 4
        self.g_eq.add(self.d.path(d=f"M {xl + ch},{y - H / 2} L {k0},{y - H / 2} L {k0 + 3},{y + H / 2 - Hk} "
                                    f"L {xr},{y + H / 2 - Hk} L {xr},{y + H / 2} L {xl + ch},{y + H / 2}"))
        self.g_eq.add(self.d.polyline([(xl + ch, y - 2), (xr - 4, y - 2), (xr - 4, y + 2), (xl + ch, y + 2)],
                                      stroke_width=0.3))
        cx = xl + ch / 2
        return dict(ct=(cx, y - H / 2), cb=(cx, y + H / 2), sv=(xr - 8, y + H / 2 - Hk), sb=(xr - 8, y + H / 2),
                    lvl=(xr, y + H / 2 - Hk * 0.45))

    def aircooler(self, x, y, w=34, h=8, fans=2, label=None):
        """Air cooler: tube bundle box with zig-zag; fans below.  (x,y) top-left.  Returns in/out."""
        self.g_eq.add(self.d.rect((x, y), (w, h)))
        n = 8
        pts = [(x + 1.5 + i * (w - 3) / n, y + (1.5 if i % 2 == 0 else h - 1.5)) for i in range(n + 1)]
        self.g_eq.add(self.d.polyline(pts, stroke_width=0.3))
        for i in range(fans):
            fx = x + w * (i + 0.5) / fans
            fy = y + h + 5
            self.g_eq.add(self.d.circle((fx, fy), 3.0, stroke_width=0.35))
            self.g_eq.add(self.d.line((fx - 2.1, fy - 2.1), (fx + 2.1, fy + 2.1), stroke_width=0.3))
            self.g_eq.add(self.d.line((fx - 2.1, fy + 2.1), (fx + 2.1, fy - 2.1), stroke_width=0.3))
            self.g_eq.add(self.d.line((fx, fy + 3), (fx, fy + 5), stroke_width=0.35))
            self.g_eq.add(self.d.circle((fx, fy + 7), 2.0, stroke_width=0.35))
            self.t("M", fx, fy + 7.8, 2.0, "middle")
        return dict(i=(x, y + h / 2), o=(x + w, y + h / 2), it=(x + 3, y), ib=(x + w - 3, y + h))

    def pump(self, x, y, tag=None, r=4.2, disch="u", tag_dy=None):
        """Centrifugal pump (centre x,y).  Suction from left; discharge up from top-centre."""
        self.g_eq.add(self.d.circle((x, y), r))
        self.g_eq.add(self.d.polygon([(x - r * 0.8, y + r * 0.6), (x + r * 0.8, y + r * 0.6),
                                      (x + r * 1.15, y + r + 1.6), (x - r * 1.15, y + r + 1.6)], fill="none",
                                     stroke_width=0.4))
        self.g_eq.add(self.d.circle((x, y), r))
        if tag:
            self.t(tag, x, y + r + (tag_dy or 4.6), 2.3, "middle", bold=True)
        return dict(s=(x - r, y), d=(x, y - r))

    def fan(self, x, y, tag=None, r=5):
        self.g_eq.add(self.d.circle((x, y), r))
        for a in range(0, 360, 90):
            ra = math.radians(a)
            self.g_eq.add(self.d.line((x, y), (x + r * 0.85 * math.cos(ra), y + r * 0.85 * math.sin(ra)),
                                      stroke_width=0.3))
        if tag:
            self.t(tag, x, y + r + 3.5, 2.3, "middle", bold=True)

    def ejector(self, x, y, L=22, tag=None):
        """Steam ejector, horizontal, suction at left (x,y), discharge at right.  Motive from top."""
        pts = [(x, y - 2.5), (x + L * 0.35, y - 2.5), (x + L * 0.5, y - 1.2), (x + L, y - 3.2), (x + L, y + 3.2),
               (x + L * 0.5, y + 1.2), (x + L * 0.35, y + 2.5), (x, y + 2.5)]
        self.g_eq.add(self.d.polygon(pts))
        if tag:
            self.t(tag, x + L / 2, y + 7.0, 2.3, "middle", bold=True)
        return dict(s=(x, y), d=(x + L, y), m=(x + L * 0.2, y - 2.5))

    def package(self, x, y, w, h, tag, lines=()):
        self.g_eq.add(self.d.rect((x, y), (w, h), stroke_dasharray="2.5,1.2", stroke_width=0.4))
        self.t(tag, x + w / 2, y + 4.2, 2.4, "middle", bold=True)
        for i, s in enumerate(lines):
            self.t(s, x + w / 2, y + 7.2 + i * 2.6, 2.0, "middle")

    def eq_label(self, x, y, tag, svc=None, anchor="middle"):
        self.t(tag, x, y, 2.6, anchor, bold=True)
        if svc:
            self.t(svc, x, y + 3.0, 2.1, anchor)

    def box_note(self, x, y, lines, size=2.1, w=None):
        w = w or max(text_w(s, size) for s in lines) + 3
        h = len(lines) * size * 1.35 + 2
        self.g_eq.add(self.d.rect((x, y), (w, h), stroke_width=0.3))
        for i, s in enumerate(lines):
            self.t(s, x + 1.5, y + size + 1.0 + i * size * 1.35, size)
        return w, h


def _dir(x1, y1, x2, y2):
    if abs(x2 - x1) >= abs(y2 - y1):
        return "r" if x2 > x1 else "l"
    return "d" if y2 > y1 else "u"
