"""I&C package common helpers: paths, data access and an ISA-5.1 drawing pen for control-scheme sketches,
architecture block diagrams and loop diagrams (svgwrite, mm units on a cfu.drawing.sheet.Sheet)."""
from __future__ import annotations

import json
import math
from pathlib import Path

from ..drawing.sheet import FONT, Sheet

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "deliverables" / "04-instrumentation"
INK = "#000000"
BLUE = "#1F3864"
GREY = "#666666"
SIS_RED = "#B00020"
APC_GRN = "#1B5E20"


def load(name, default=None):
    p = DATA / name
    if not p.exists():
        return default
    return json.loads(p.read_text())


def pr():
    return load("process_results.json")


def streams():
    return {s["no"]: s for s in load("streams.json")}


def equipment():
    return {e["tag"]: e for e in load("equipment.json")}


def loops():
    return {l["tag"]: l for l in load("control_loops.json")["loops"]}


def sifs():
    return {s["tag"]: s for s in load("control_loops.json")["sifs"]}


def tw(s: str, size: float) -> float:
    """Approximate DejaVu Sans text width (mm)."""
    w = 0.0
    for ch in str(s):
        if ch in "il.,:;'|!":
            w += 0.30
        elif ch in " -()/[]":
            w += 0.38
        elif ch.isupper() or ch in "MW%#@":
            w += 0.68
        elif ch.isdigit():
            w += 0.62
        else:
            w += 0.58
    return w * size


class Pen:
    """Drawing helper on a Sheet. Layers: lines (bottom), symbols, text (top)."""

    def __init__(self, sheet: Sheet):
        self.sh = sheet
        self.d = d = sheet.dwg
        self.gb = d.g()
        sheet.g.add(self.gb)
        self.gl = d.g(fill="none", stroke=INK, stroke_linejoin="round", stroke_linecap="round")
        self.gs = d.g(fill="white", stroke=INK, stroke_width=0.35, stroke_linejoin="round")
        self.gt = d.g(font_family=FONT, fill=INK, stroke="none")
        for grp in (self.gl, self.gs, self.gt):
            sheet.g.add(grp)

    # ------------------------------------------------------------------ text
    def text(self, s, x, y, size=2.5, anchor="start", bold=False, color=INK, italic=False, rotate=None, g=None):
        t = self.d.text(str(s), insert=(x, y), font_size=size, text_anchor=anchor, fill=color,
                        font_weight="bold" if bold else "normal", font_style="italic" if italic else "normal")
        if rotate:
            t.rotate(rotate, center=(x, y))
        (g or self.gt).add(t)
        return t

    def mtext(self, lines, x, y, size=2.4, anchor="start", lh=None, bold_first=False, color=INK):
        lh = lh or size * 1.3
        for i, s in enumerate(lines):
            self.text(s, x, y + i * lh, size, anchor, bold=bold_first and i == 0, color=color)
        return y + len(lines) * lh

    def wrap(self, s, width, size):
        words, out, cur = str(s).split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if tw(t, size) > width and cur:
                out.append(cur)
                cur = w
            else:
                cur = t
        if cur:
            out.append(cur)
        return out

    # ------------------------------------------------------------------ lines
    def line(self, pts, w=0.35, dash=None, color=INK, arrow=False, start_arrow=False, g=None, alen=2.2):
        pts = [(float(a), float(b)) for a, b in pts]
        kw = dict(fill="none", stroke=color, stroke_width=w)
        if dash:
            kw["stroke_dasharray"] = dash
        (g or self.gl).add(self.d.polyline(pts, **kw))
        if arrow:
            self.arrowhead(pts[-2], pts[-1], color, alen)
        if start_arrow:
            self.arrowhead(pts[1], pts[0], color, alen)
        return pts

    def arrowhead(self, a, b, color=INK, L=2.2):
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        wv = 0.38
        p1 = (b[0] - L * math.cos(ang - wv), b[1] - L * math.sin(ang - wv))
        p2 = (b[0] - L * math.cos(ang + wv), b[1] - L * math.sin(ang + wv))
        self.gl.add(self.d.polygon([b, p1, p2], fill=color, stroke=color, stroke_width=0.1))

    def proc(self, pts, arrow=True, w=0.6, mid=False):
        p = self.line(pts, w=w, arrow=arrow)
        if mid:
            a, b = max(zip(p[:-1], p[1:]), key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
            self.arrowhead(a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), INK, 2.6)
        return p

    def util(self, pts, arrow=True):
        return self.line(pts, w=0.35, arrow=arrow)

    def sig(self, pts, arrow=True, color=INK):
        """Electrical signal (ISA-5.1 dashed)."""
        return self.line(pts, w=0.25, dash="1.8,0.9", arrow=arrow, color=color, alen=1.9)

    def soft(self, pts, arrow=True, color=INK, step=5.0):
        """Software / data link (ISA-5.1 line with small circles)."""
        pts = self.line(pts, w=0.25, arrow=arrow, color=color, alen=1.9)
        for a, b in zip(pts[:-1], pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            n = int(L // step)
            for i in range(1, n):
                t = i / n
                self.gl.add(self.d.circle((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), 0.55,
                                          fill="white", stroke=color, stroke_width=0.22))
        return pts

    def dot(self, x, y, r=0.6):
        self.gl.add(self.d.circle((x, y), r, fill=INK, stroke="none"))

    # ------------------------------------------------------------------ ISA bubbles
    def bubble(self, x, y, tag, kind="dcs", r=5.0, note=None, note_pos="r", color=None):
        """ISA-5.1 instrument bubble. kind: field | dcs | sis | apc | plc | local.
        Returns ports n/s/e/w."""
        d, g = self.d, self.gs
        col = color or (SIS_RED if kind == "sis" else APC_GRN if kind == "apc" else INK)
        sw = 0.35
        if kind == "dcs":
            g.add(d.rect((x - r, y - r), (2 * r, 2 * r), fill="white", stroke=col, stroke_width=sw))
            g.add(d.circle((x, y), r, fill="white", stroke=col, stroke_width=sw))
            g.add(d.line((x - r, y), (x + r, y), stroke=col, stroke_width=sw))
        elif kind == "sis":
            g.add(d.rect((x - r, y - r), (2 * r, 2 * r), fill="white", stroke=col, stroke_width=sw))
            g.add(d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill="white", stroke=col,
                            stroke_width=sw))
            g.add(d.line((x - r, y), (x + r, y), stroke=col, stroke_width=sw))
        elif kind == "apc":
            h = r * 1.08
            pts = [(x - h, y), (x - h / 2, y - r), (x + h / 2, y - r), (x + h, y), (x + h / 2, y + r), (x - h / 2, y + r)]
            g.add(d.polygon(pts, fill="white", stroke=col, stroke_width=sw))
            g.add(d.line((x - h, y), (x + h, y), stroke=col, stroke_width=sw))
        elif kind == "plc":
            g.add(d.polygon([(x - r, y), (x, y - r), (x + r, y), (x, y + r)], fill="white", stroke=col, stroke_width=sw))
            g.add(d.rect((x - r * 0.72, y - r * 0.72), (1.44 * r, 1.44 * r), fill="none", stroke=col, stroke_width=sw))
            g.add(d.line((x - r * 0.72, y), (x + r * 0.72, y), stroke=col, stroke_width=sw))
        else:  # field / local
            g.add(d.circle((x, y), r, fill="white", stroke=col, stroke_width=sw))
        letters, _, num = tag.partition("-")
        fs = 2.2 if len(letters) <= 3 else 1.9 if len(letters) <= 4 else 1.65
        nfs = 2.0 if len(num) <= 4 else 1.75
        if kind in ("sis", "plc"):
            fs, nfs = fs * 0.8, nfs * 0.8
            self.text(letters, x, y - 0.9, fs, "middle", bold=True, color=col)
            self.text(num, x, y + 2.3, nfs, "middle", color=col)
        elif kind == "field":
            self.text(letters, x, y - 0.3, fs, "middle", bold=True, color=col)
            self.text(num, x, y + 2.6, nfs, "middle", color=col)
        else:
            self.text(letters, x, y - 1.0, fs, "middle", bold=True, color=col)
            self.text(num, x, y + 2.9, nfs, "middle", color=col)
        if note:
            lines = note if isinstance(note, (list, tuple)) else [note]
            if note_pos == "r":
                self.mtext(lines, x + r + 1.2, y - r + 2.3, 2.0, color=GREY)
            elif note_pos == "l":
                self.mtext(lines, x - r - 1.2, y - r + 2.3, 2.0, anchor="end", color=GREY)
            elif note_pos == "b":
                self.mtext(lines, x, y + r + 3.0, 2.0, anchor="middle", color=GREY)
            else:
                self.mtext(lines, x, y - r - 1.5 - 2.6 * (len(lines) - 1), 2.0, anchor="middle", color=GREY)
        k = r * 1.08 if kind == "apc" else r
        return dict(n=(x, y - r), s=(x, y + r), e=(x + k, y), w=(x - k, y), c=(x, y))

    def fy(self, x, y, sym, tag=None, s=7.0, tag_pos="b", color=INK):
        """Computing function block: ISA bubble-less square with function symbol (Σ, ×, <, >, f(x) ...)."""
        g = self.gs
        g.add(self.d.rect((x - s / 2, y - s / 2), (s, s), fill="white", stroke=color, stroke_width=0.35))
        fs = 3.4 if len(sym) <= 1 else 2.5 if len(sym) <= 4 else 2.0
        self.text(sym, x, y + fs * 0.36, fs, "middle", bold=True, color=color)
        if tag:
            if tag_pos == "b":
                self.text(tag, x, y + s / 2 + 2.6, 1.9, "middle", color=color)
            elif tag_pos == "t":
                self.text(tag, x, y - s / 2 - 1.0, 1.9, "middle", color=color)
            elif tag_pos == "r":
                self.text(tag, x + s / 2 + 1.0, y + 0.7, 1.9, color=color)
            else:
                self.text(tag, x - s / 2 - 1.0, y + 0.7, 1.9, "end", color=color)
        return dict(n=(x, y - s / 2), s=(x, y + s / 2), e=(x + s / 2, y), w=(x - s / 2, y), c=(x, y))

    # ------------------------------------------------------------------ final elements
    def cv(self, x, y, orient="h", tag=None, fail=None, tag_pos="t", act="d", size=3.2, sis=False):
        """Globe control valve (bow-tie) with diaphragm actuator. Returns port 'a' (actuator top)."""
        d, g = self.d, self.gs
        s = size
        col = SIS_RED if sis else INK
        if orient == "h":
            g.add(d.polygon([(x - s, y - s * 0.62), (x - s, y + s * 0.62), (x + s, y - s * 0.62), (x + s, y + s * 0.62)],
                            fill="white", stroke=INK, stroke_width=0.35))
            g.add(d.line((x, y), (x, y - s * 1.55), stroke=INK, stroke_width=0.35))
            ay = y - s * 1.55
            if act == "d":
                g.add(d.path(f"M {x - s * 0.85} {ay} A {s * 0.85} {s * 0.7} 0 0 1 {x + s * 0.85} {ay} Z",
                             fill="white", stroke=col, stroke_width=0.35))
                top = (x, ay - s * 0.7)
            else:  # solenoid / on-off (square)
                g.add(d.rect((x - s * 0.6, ay - s * 1.0), (s * 1.2, s * 1.0), fill="white", stroke=col, stroke_width=0.35))
                self.text("S", x, ay - s * 0.22, 2.0, "middle", bold=True, color=col)
                top = (x, ay - s * 1.0)
            if tag:
                if tag_pos == "t":
                    self.text(tag, x, top[1] - 1.2, 2.1, "middle", color=col)
                elif tag_pos == "b":
                    self.text(tag, x, y + s + 2.2, 2.1, "middle", color=col)
                elif tag_pos == "r":
                    self.text(tag, x + s + 0.8, y + s + 1.6, 2.1, color=col)
                else:
                    self.text(tag, x - s - 0.8, y + s + 1.6, 2.1, "end", color=col)
            if fail:
                self.text(fail, x + s + 0.6, y - s * 0.7, 1.7, color=GREY)
            return dict(a=top, w=(x - s, y), e=(x + s, y))
        # vertical valve, actuator to the left
        g.add(d.polygon([(x - s * 0.62, y - s), (x + s * 0.62, y - s), (x - s * 0.62, y + s), (x + s * 0.62, y + s)],
                        fill="white", stroke=INK, stroke_width=0.35))
        g.add(d.line((x, y), (x - s * 1.55, y), stroke=INK, stroke_width=0.35))
        ax = x - s * 1.55
        if act == "d":
            g.add(d.path(f"M {ax} {y - s * 0.85} A {s * 0.7} {s * 0.85} 0 0 0 {ax} {y + s * 0.85} Z",
                         fill="white", stroke=col, stroke_width=0.35))
            top = (ax - s * 0.7, y)
        else:
            g.add(d.rect((ax - s * 1.0, y - s * 0.6), (s * 1.0, s * 1.2), fill="white", stroke=col, stroke_width=0.35))
            self.text("S", ax - s * 0.5, y + 0.7, 2.0, "middle", bold=True, color=col)
            top = (ax - s * 1.0, y)
        if tag:
            if tag_pos in ("t", "l"):
                self.text(tag, top[0] - 1.0, y - s - 0.6, 2.1, "end", color=col)
            else:
                self.text(tag, x + s * 0.62 + 1.0, y + 0.8, 2.1, color=col)
        if fail:
            self.text(fail, x + s * 0.62 + 0.8, y + s + 1.5, 1.7, color=GREY)
        return dict(a=top, n=(x, y - s), s=(x, y + s))

    # ------------------------------------------------------------------ equipment
    def column(self, x, y, w, h, tag, desc=None, trays=None):
        g = self.gs
        g.add(self.d.rect((x, y), (w, h), rx=w / 2 if w < 14 else 6, ry=6, fill="white", stroke=INK, stroke_width=0.5))
        for t in trays or []:
            g.add(self.d.line((x, t), (x + w * 0.7, t), stroke=INK, stroke_width=0.25))
        if tag:
            self.text(tag, x + w / 2, y - 3.0 - (3.0 if desc else 0), 2.8, "middle", bold=True)
        if desc:
            self.text(desc, x + w / 2, y - 2.6, 2.0, "middle", color=GREY)

    def drum(self, x, y, w, h, tag, desc=None, label_pos="b", boot=None):
        r = h / 2
        self.gs.add(self.d.rect((x, y), (w, h), rx=r, ry=r, fill="white", stroke=INK, stroke_width=0.5))
        if boot:
            bx, bw, bh = boot
            self.gs.add(self.d.rect((bx, y + h - 0.5), (bw, bh), fill="white", stroke=INK, stroke_width=0.45))
        if label_pos == "b":
            yy = y + h + 3.5 + (boot[2] if boot else 0)
            self.text(tag, x + w / 2, yy, 2.8, "middle", bold=True)
            if desc:
                self.text(desc, x + w / 2, yy + 2.8, 2.0, "middle", color=GREY)
        else:
            self.text(tag, x + w / 2, y - 3.5 - (2.8 if desc else 0), 2.8, "middle", bold=True)
            if desc:
                self.text(desc, x + w / 2, y - 3.2, 2.0, "middle", color=GREY)

    def vvessel(self, x, y, w, h, tag, desc=None):
        self.gs.add(self.d.rect((x, y), (w, h), rx=w / 2, ry=3, fill="white", stroke=INK, stroke_width=0.5))
        self.text(tag, x + w / 2, y + h + 3.5, 2.6, "middle", bold=True)
        if desc:
            self.text(desc, x + w / 2, y + h + 6.2, 2.0, "middle", color=GREY)

    def pump(self, x, y, tag=None, r=3.2, label_pos="b", flip=False):
        g = self.gs
        g.add(self.d.circle((x, y), r, fill="white", stroke=INK, stroke_width=0.45))
        if flip:
            g.add(self.d.line((x, y - r), (x - r * 1.5, y - r), stroke=INK, stroke_width=0.45))
            out = (x - r * 1.5, y - r)
        else:
            g.add(self.d.line((x, y - r), (x + r * 1.5, y - r), stroke=INK, stroke_width=0.45))
            out = (x + r * 1.5, y - r)
        g.add(self.d.polygon([(x - r * 0.8, y + r * 1.4), (x + r * 0.8, y + r * 1.4), (x + r * 0.45, y + r * 0.75),
                              (x - r * 0.45, y + r * 0.75)], fill="white", stroke=INK, stroke_width=0.3))
        if tag:
            if label_pos == "b":
                self.text(tag, x, y + r * 1.4 + 3.0, 2.2, "middle", bold=True)
            elif label_pos == "l":
                self.text(tag, x - r - 1.2, y + r + 1.0, 2.2, "end", bold=True)
            else:
                self.text(tag, x + r + 1.2, y + r + 1.0, 2.2, bold=True)
        return dict(suc=(x - r, y) if not flip else (x + r, y), dis=out)

    def hx(self, x, y, tag=None, r=4.0, label_pos="t", duty=None):
        g = self.gs
        g.add(self.d.circle((x, y), r, fill="white", stroke=INK, stroke_width=0.45))
        pts = [(x - r, y), (x - r * 0.5, y - r * 0.5), (x, y + r * 0.5), (x + r * 0.5, y - r * 0.5), (x + r, y)]
        g.add(self.d.polyline(pts, fill="none", stroke=INK, stroke_width=0.35))
        if tag:
            if label_pos == "t":
                self.text(tag, x, y - r - 1.4, 2.2, "middle", bold=True)
            elif label_pos == "b":
                self.text(tag, x, y + r + 3.0, 2.2, "middle", bold=True)
            elif label_pos == "r":
                self.text(tag, x + r + 1.2, y - 1.0, 2.2, bold=True)
            else:
                self.text(tag, x - r - 1.2, y - 1.0, 2.2, "end", bold=True)
        if duty:
            self.text(duty, x, y + r + (5.6 if label_pos == "b" else 3.0), 1.8, "middle", color=GREY)
        return dict(w=(x - r, y), e=(x + r, y), n=(x, y - r), s=(x, y + r))

    def aircooler(self, x, y, w, tag=None, label_pos="t"):
        g = self.gs
        h = 5.0
        g.add(self.d.rect((x - w / 2, y - h / 2), (w, h), fill="white", stroke=INK, stroke_width=0.45))
        for k in range(5):
            xx = x - w / 2 + w * (k + 0.5) / 5
            g.add(self.d.line((xx - 1.0, y - h / 2 + 0.6), (xx + 1.0, y + h / 2 - 0.6), stroke=INK, stroke_width=0.25))
        g.add(self.d.circle((x, y + h / 2 + 2.4), 1.9, fill="white", stroke=INK, stroke_width=0.3))
        g.add(self.d.line((x - 1.9, y + h / 2 + 2.4), (x + 1.9, y + h / 2 + 2.4), stroke=INK, stroke_width=0.3))
        if tag:
            if label_pos == "t":
                self.text(tag, x, y - h / 2 - 1.4, 2.2, "middle", bold=True)
            else:
                self.text(tag, x + w / 2 + 1.2, y + 1.0, 2.2, bold=True)
        return dict(w=(x - w / 2, y), e=(x + w / 2, y), n=(x, y - h / 2), s=(x, y + h / 2))

    def heater(self, x, y, w, h, tag, desc=None, conv_h=None, stack=True):
        """Box-type fired heater: radiant box (x,y,w,h) with convection section and stack above."""
        g = self.gs
        ch = conv_h or h * 0.35
        cw = w * 0.6
        cx = x + (w - cw) / 2
        g.add(self.d.rect((x, y), (w, h), fill="white", stroke=INK, stroke_width=0.55))
        g.add(self.d.polygon([(x, y), (cx, y - 6), (cx + cw, y - 6), (x + w, y)], fill="white", stroke=INK,
                             stroke_width=0.45))
        g.add(self.d.rect((cx, y - 6 - ch), (cw, ch), fill="white", stroke=INK, stroke_width=0.5))
        if stack:
            sw = cw * 0.14
            g.add(self.d.rect((x + w / 2 - sw / 2, y - 6 - ch - 18), (sw, 18), fill="white", stroke=INK, stroke_width=0.45))
        # burner flames
        for k in range(4):
            bx = x + w * (k + 0.5) / 4
            g.add(self.d.path(f"M {bx - 1.4} {y + h} Q {bx} {y + h - 6} {bx + 1.4} {y + h}", fill="none",
                              stroke=INK, stroke_width=0.3))
        self.text(tag, x + w / 2, y + h * 0.42, 3.2, "middle", bold=True)
        if desc:
            self.mtext(desc if isinstance(desc, list) else [desc], x + w / 2, y + h * 0.42 + 4, 2.0, "middle",
                       color=GREY)
        return dict(conv=(cx, y - 6 - ch, cw, ch), stack_top=(x + w / 2, y - 6 - ch - 18))

    def desalter(self, x, y, w, h, tag, desc=None):
        self.drum(x, y, w, h, tag, desc)
        for k in range(3):
            yy = y + h * 0.3 + k * 1.2
            self.gs.add(self.d.line((x + w * 0.2, yy), (x + w * 0.8, yy), stroke=INK, stroke_width=0.25))
        # transformer symbol on top
        tx = x + w / 2
        self.gs.add(self.d.circle((tx - 1.3, y - 4), 2.0, fill="white", stroke=INK, stroke_width=0.3))
        self.gs.add(self.d.circle((tx + 1.3, y - 4), 2.0, fill="none", stroke=INK, stroke_width=0.3))
        self.gs.add(self.d.line((tx, y - 2), (tx, y), stroke=INK, stroke_width=0.3))
        return (tx, y - 6)

    def offpage(self, x, y, label, sub=None, direction="r", w=None):
        """Off-sheet connector (pentagon arrow). direction r: points right with tip at (x,y)."""
        w = w or max(tw(label, 2.0), tw(sub or "", 1.8)) + 7
        h = 6.4 if sub else 4.6
        if direction == "r":
            pts = [(x - w, y - h / 2), (x - 3, y - h / 2), (x, y), (x - 3, y + h / 2), (x - w, y + h / 2)]
            cx = x - w / 2 - 1.5
        else:
            pts = [(x + w, y - h / 2), (x + 3, y - h / 2), (x, y), (x + 3, y + h / 2), (x + w, y + h / 2)]
            cx = x + w / 2 + 1.5
        self.gs.add(self.d.polygon(pts, fill="white", stroke=INK, stroke_width=0.35))
        if sub:
            self.text(label, cx, y - 0.4, 2.0, "middle")
            self.text(sub, cx, y + 2.4, 1.7, "middle", bold=True)
        else:
            self.text(label, cx, y + 0.7, 2.0, "middle")
        return w

    def box(self, x, y, w, h, title=None, lines=(), fill="white", stroke=INK, sw=0.4, tsize=2.6, lsize=2.0,
            dash=None, rx=1.0, title_fill=None, title_color=INK, align="middle", g=None):
        kw = dict(fill=fill, stroke=stroke, stroke_width=sw)
        if dash:
            kw["stroke_dasharray"] = dash
        g = g or (self.gb if fill not in (None, "none") else self.gs)
        g.add(self.d.rect((x, y), (w, h), rx=rx, ry=rx, **kw))
        yy = y + tsize + 1.4
        if title:
            if title_fill:
                (g or self.gs).add(self.d.rect((x, y), (w, tsize + 2.6), rx=rx, ry=rx, fill=title_fill,
                                               stroke=stroke, stroke_width=sw))
            tl = title if isinstance(title, (list, tuple)) else [title]
            for i, t in enumerate(tl):
                self.text(t, x + w / 2 if align == "middle" else x + 2, yy + i * (tsize * 1.2), tsize, align,
                          bold=True, color=title_color)
            yy += tsize * 1.2 * (len(tl) - 1) + lsize + 2.0
        for i, s in enumerate(lines):
            self.text(s, x + w / 2 if align == "middle" else x + 2, yy + i * lsize * 1.3, lsize, align)
        return (x, y, w, h)

    def legend_isa(self, x, y, w=170):
        """Standard ISA symbol legend for control-scheme sketches. Returns bottom y."""
        self.box(x, y, w, 64, None, fill="none")
        self.text("LEGEND (ISA-5.1 / ISA-5.4)", x + 3, y + 5, 2.8, bold=True)
        yy = y + 13
        col2 = x + w / 2 + 2
        self.bubble(x + 8, yy, "FIC-0000", "dcs", r=4.2)
        self.text("DCS (BPCS) function, operator accessible", x + 15, yy + 0.8, 2.0)
        self.bubble(col2 + 6, yy, "PZ-0000", "sis", r=4.2)
        self.text("SIS / BMS function (SIL rated)", col2 + 13, yy + 0.8, 2.0)
        yy += 11
        self.bubble(x + 8, yy, "TC-0000", "apc", r=4.2)
        self.text("APC / MPC (L3 computer) function", x + 15, yy + 0.8, 2.0)
        self.bubble(col2 + 6, yy, "FT-0000", "field", r=4.2)
        self.text("Field-mounted instrument", col2 + 13, yy + 0.8, 2.0)
        yy += 11
        self.fy(x + 8, yy, "Σ", s=6)
        self.text("Computing block: Σ sum/bias, × ratio/mult,", x + 15, yy - 0.5, 2.0)
        self.text("< low select, > high select, f(x) characteriser", x + 15, yy + 2.3, 2.0)
        self.cv(col2 + 6, yy + 1, "h", size=2.6)
        self.text("Control valve (FO/FC = fail open/closed)", col2 + 13, yy + 0.8, 2.0)
        yy += 11
        self.sig([(x + 3, yy), (x + 14, yy)])
        self.text("Electrical signal (4-20 mA / HART)", x + 16, yy + 0.8, 2.0)
        self.soft([(col2 + 1, yy), (col2 + 12, yy)], step=3.5)
        self.text("Software / data link (DCS internal)", col2 + 14, yy + 0.8, 2.0)
        yy += 7
        self.line([(x + 3, yy), (x + 14, yy)], w=0.6, arrow=True)
        self.text("Process line", x + 16, yy + 0.8, 2.0)
        self.sig([(col2 + 1, yy), (col2 + 12, yy)], color=APC_GRN)
        self.text("APC setpoint / MPC move", col2 + 14, yy + 0.8, 2.0, color=APC_GRN)
        return y + 64

    def narrative(self, x, y, w, title, items, size=2.1):
        """Boxed numbered narrative. Returns bottom y."""
        lines = []
        for i, it in enumerate(items):
            wr = self.wrap(it, w - 9, size)
            lines.append((f"{i + 1}.", wr))
        n = sum(len(l[1]) for l in lines)
        lh = size * 1.32
        h = 9 + n * lh + 2 * len(items) * 0.25
        self.box(x, y, w, h, None, fill="none")
        self.text(title, x + 3, y + 5.2, 2.8, bold=True)
        yy = y + 10.5
        for num, wr in lines:
            self.text(num, x + 3, yy, size, bold=True)
            for s in wr:
                self.text(s, x + 7.5, yy, size)
                yy += lh
            yy += 0.5
        return y + h


def render_png(svg: Path, png: Path, width=2600):
    import cairosvg
    png.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=width)
    return png
