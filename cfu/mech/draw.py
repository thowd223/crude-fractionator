"""Drawing helpers for mechanical GA sheets (all coordinates in sheet mm, y downwards)."""
from __future__ import annotations

import math

from ..drawing.sheet import FONT

THK = 0.5
MED = 0.35
THIN = 0.2
DIM = 0.18
BLUE = "#1F3864"
GREY = "#808080"
HATCH = "#606060"


class Pen:
    def __init__(self, sh):
        self.sh = sh
        self.d = sh.dwg
        self.g = sh.g
        self._hatch_ids = {}

    # -------------------------------------------------------------- primitives
    def line(self, p1, p2, w=MED, color="black", dash=None):
        kw = dict(stroke=color, stroke_width=w)
        if dash:
            kw["stroke_dasharray"] = dash
        self.g.add(self.d.line(p1, p2, **kw))

    def pline(self, pts, w=MED, color="black", fill="none", dash=None, close=False):
        kw = dict(stroke=color, stroke_width=w, fill=fill)
        if dash:
            kw["stroke_dasharray"] = dash
        self.g.add((self.d.polygon if close else self.d.polyline)(pts, **kw))

    def rect(self, x, y, w, h, lw=MED, fill="none", color="black", dash=None):
        kw = dict(stroke=color, stroke_width=lw, fill=fill)
        if dash:
            kw["stroke_dasharray"] = dash
        self.g.add(self.d.rect((x, y), (w, h), **kw))

    def circle(self, c, r, lw=MED, fill="none", color="black", dash=None):
        kw = dict(stroke=color, stroke_width=lw, fill=fill)
        if dash:
            kw["stroke_dasharray"] = dash
        self.g.add(self.d.circle(c, r, **kw))

    def path(self, dstr, lw=MED, fill="none", color="black", dash=None):
        kw = dict(stroke=color, stroke_width=lw, fill=fill)
        if dash:
            kw["stroke_dasharray"] = dash
        self.g.add(self.d.path(d=dstr, **kw))

    def text(self, s, x, y, size=2.2, anchor="start", bold=False, color="black", rotate=None, italic=False):
        return self.sh.text(s, x, y, size, anchor, bold=bold, color=color, rotate=rotate, italic=italic)

    def ctr(self, p1, p2):
        self.line(p1, p2, w=DIM, color=GREY, dash="6,1.2,1,1.2")

    def arrow(self, tip, frm, size=1.6, color="black"):
        a = math.atan2(tip[1] - frm[1], tip[0] - frm[0])
        p1 = (tip[0] - size * math.cos(a - 0.3), tip[1] - size * math.sin(a - 0.3))
        p2 = (tip[0] - size * math.cos(a + 0.3), tip[1] - size * math.sin(a + 0.3))
        self.g.add(self.d.polygon([tip, p1, p2], fill=color, stroke=color, stroke_width=0.1))

    # -------------------------------------------------------------- dimensions
    def dim_v(self, x, y1, y2, text, side="left", ext_from=None, size=2.0):
        """Vertical dimension at x between y1, y2 (text rotated)."""
        if abs(y2 - y1) < 0.3:
            return
        self.line((x, y1), (x, y2), w=DIM)
        self.arrow((x, y1), (x, y2), 1.3)
        self.arrow((x, y2), (x, y1), 1.3)
        if ext_from is not None:
            for yy in (y1, y2):
                self.line((ext_from, yy), (x + (-1.2 if side == "left" else 1.2), yy), w=DIM)
        ym = (y1 + y2) / 2
        dx = -0.8 if side == "left" else 2.6
        self.text(text, x + dx, ym, size, "middle", rotate=-90)

    def dim_h(self, y, x1, x2, text, ext_from=None, size=2.0, above=True):
        if abs(x2 - x1) < 0.3:
            return
        self.line((x1, y), (x2, y), w=DIM)
        self.arrow((x1, y), (x2, y), 1.3)
        self.arrow((x2, y), (x1, y), 1.3)
        if ext_from is not None:
            for xx in (x1, x2):
                self.line((xx, ext_from), (xx, y + (1.2 if ext_from > y else -1.2)), w=DIM)
        self.text(text, (x1 + x2) / 2, y - 0.8 if above else y + 2.6, size, "middle")

    def elev(self, x, y, label, side="right", size=2.0, w=14):
        """Elevation marker: open triangle on a leader line + label."""
        s = 1.4
        self.pline([(x, y), (x - s * 0.8, y - s * 1.2), (x + s * 0.8, y - s * 1.2)], w=0.2, close=True, fill="white")
        if side == "right":
            self.line((x, y), (x + w, y), w=DIM)
            self.text(label, x + 1.5, y - 0.6, size)
        else:
            self.line((x - w, y), (x, y), w=DIM)
            self.text(label, x - 1.5, y - 0.6, size, "end")

    def leader(self, pts, text, size=2.0, anchor="start", bold=False, dot=True):
        self.pline(pts, w=DIM)
        if dot:
            self.arrow(pts[0], pts[1], 1.3)
        x, y = pts[-1]
        dx = 0.8 if anchor == "start" else -0.8 if anchor == "end" else 0
        for i, ln in enumerate(str(text).split("\n")):
            self.text(ln, x + dx, y + 0.7 + i * (size + 0.6), size, anchor, bold=bold)

    def bubble(self, x, y, label, r=None, size=1.9):
        r = r or max(2.2, 0.62 * len(label) * size / 2 + 0.9)
        self.circle((x, y), r, lw=0.25, fill="white")
        self.text(label, x, y + size * 0.36, size, "middle", bold=True)
        return r

    # -------------------------------------------------------------- tables
    def table(self, x, y, hdr, rows, widths, title=None, fs=2.0, rh=3.4, hdr_fs=None, bold_first=False,
              wrap=False):
        """Draw a ruled table; returns the y of the bottom edge."""
        W = sum(widths)
        hdr_fs = hdr_fs or fs
        if title:
            self.rect(x, y, W, rh + 0.6, lw=MED, fill=BLUE)
            self.text(title, x + 1.2, y + rh * 0.78, fs + 0.3, bold=True, color="white")
            y += rh + 0.6
        self.rect(x, y, W, rh, lw=MED, fill="#E4EAF4")
        xx = x
        for h, w in zip(hdr, widths):
            self.text(h, xx + 0.8, y + rh * 0.74, hdr_fs, bold=True)
            xx += w
        y += rh
        for i, r in enumerate(rows):
            self.line((x, y + rh), (x + W, y + rh), w=0.12, color=GREY)
            xx = x
            for j, (v, w) in enumerate(zip(r, widths)):
                s = str(v)
                maxc = int(w / (fs * 0.53)) if w > 0 else 99
                if len(s) > maxc:
                    s = s[:max(1, maxc - 1)] + "~"
                self.text(s, xx + 0.8, y + rh * 0.74, fs, bold=(bold_first and j == 0))
                xx += w
            y += rh
        top = y - rh * (len(rows) + 1)
        self.rect(x, top, W, rh * (len(rows) + 1), lw=MED)
        xx = x
        for w in widths[:-1]:
            xx += w
            self.line((xx, top), (xx, y), w=0.12, color=GREY)
        return y

    def kv_table(self, x, y, rows, widths, title=None, fs=2.0, rh=3.3):
        W = sum(widths)
        if title:
            self.rect(x, y, W, rh + 0.6, lw=MED, fill=BLUE)
            self.text(title, x + 1.2, y + rh * 0.78, fs + 0.3, bold=True, color="white")
            y += rh + 0.6
        top = y
        for k, v in rows:
            self.text(k, x + 0.8, y + rh * 0.74, fs)
            s = str(v)
            maxc = int(widths[1] / (fs * 0.55))
            if len(s) > maxc:
                s = s[:maxc - 1] + "~"
            self.text(s, x + widths[0] + 0.8, y + rh * 0.74, fs, bold=True)
            y += rh
            self.line((x, y), (x + W, y), w=0.12, color=GREY)
        self.rect(x, top, W, y - top, lw=MED)
        self.line((x + widths[0], top), (x + widths[0], y), w=0.12, color=GREY)
        return y

    # -------------------------------------------------------------- fills
    def hatch(self, pts, spacing=1.6, angle=45, color=HATCH, cross=False, lw=0.12):
        """Hatch a convex polygon with parallel lines (clipped analytically)."""
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        R = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 1
        for ang in ([angle, -angle] if cross else [angle]):
            a = math.radians(ang)
            dx, dy = math.cos(a), math.sin(a)
            nx, ny = -dy, dx
            k = -R
            while k <= R:
                ox, oy = cx + nx * k, cy + ny * k
                # clip infinite line through (ox,oy) dir (dx,dy) against polygon
                ts = []
                n = len(pts)
                for i in range(n):
                    (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
                    ex, ey = x2 - x1, y2 - y1
                    den = dx * ey - dy * ex
                    if abs(den) < 1e-12:
                        continue
                    t = ((x1 - ox) * ey - (y1 - oy) * ex) / den
                    u = ((x1 - ox) * dy - (y1 - oy) * dx) / den
                    if -1e-9 <= u <= 1 + 1e-9:
                        ts.append(t)
                if len(ts) >= 2:
                    t0, t1 = min(ts), max(ts)
                    self.line((ox + dx * t0, oy + dy * t0), (ox + dx * t1, oy + dy * t1), w=lw, color=color)
                k += spacing
