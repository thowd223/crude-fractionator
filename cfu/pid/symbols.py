"""PFD symbol library and drawing canvas (svgwrite, millimetre units).

`Canvas` wraps a `cfu.drawing.sheet.Sheet` and provides
  * three z-ordered layers: process lines (bottom), symbols (middle), text (top)
  * orthogonal process / utility / signal lines with arrowheads and automatic line hops
  * a light-weight clash checker (text vs text, text vs line, text vs symbol) used during development
  * the symbol primitives used on Process Flow Diagrams (columns, vessels, exchangers, air coolers,
    fired heaters, pumps, fans, ejectors, control valves, ISA bubbles, stream diamonds, off-sheet
    connectors, temperature / pressure flags).

All symbol functions return a small dict of named connection points (ports) so the caller can route lines
to them without repeating geometry.
"""
from __future__ import annotations

import math

INK = "#000000"
FONT = "DejaVu Sans, Arial, sans-serif"
MIN_TXT = 2.2                     # mm - minimum lettering height on A1

# line styles: width, dash
LSTYLE = {
    "P": (0.60, None),            # main process
    "S": (0.42, None),            # secondary process
    "U": (0.32, None),            # utility
    "SIG": (0.25, "1.6,0.9"),     # instrument signal
    "FG": (0.42, "4,1.2"),        # flue gas / air duct
}


def _tw(s: str, size: float) -> float:
    """Approximate rendered width of a DejaVu Sans string (mm)."""
    w = 0.0
    for ch in s:
        if ch in "il.,:;'|!":
            w += 0.30
        elif ch in " -()/":
            w += 0.38
        elif ch.isupper() or ch in "MW%#@":
            w += 0.68
        elif ch.isdigit():
            w += 0.62
        else:
            w += 0.58
    return w * size


class Canvas:
    def __init__(self, sheet):
        self.sh = sheet
        self.d = d = sheet.dwg
        self.gl = d.g(fill="none", stroke=INK, stroke_linejoin="round")
        self.gs = d.g(fill="white", stroke=INK, stroke_width=0.35, stroke_linejoin="round")
        self.gt = d.g(font_family=FONT, fill=INK, stroke="none")
        for grp in (self.gl, self.gs, self.gt):
            sheet.g.add(grp)
        self.lines: list[dict] = []
        self.texts: list[tuple] = []          # (x0, y0, x1, y1, s)
        self.boxes: list[tuple] = []          # (x0, y0, x1, y1, name)

    # ------------------------------------------------------------------ text
    def text(self, s, x, y, size=2.5, anchor="start", bold=False, chk=True, italic=False, rotate=None,
             color=INK):
        size = max(size, MIN_TXT)
        t = self.d.text(s, insert=(x, y), font_size=size, text_anchor=anchor,
                        font_weight="bold" if bold else "normal", fill=color,
                        font_style="italic" if italic else "normal")
        if rotate:
            t.rotate(rotate, center=(x, y))
        self.gt.add(t)
        if chk and not rotate:
            w = _tw(s, size) * (1.06 if bold else 1.0)
            x0 = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
            self.texts.append((x0, y - 0.76 * size, x0 + w, y + 0.2 * size, s))
        return t

    def mtext(self, lines, x, y, size=2.4, anchor="start", lh=None, bold_first=False, chk=True):
        lh = lh or size * 1.25
        for i, s in enumerate(lines):
            self.text(s, x, y + i * lh, size, anchor, bold=bold_first and i == 0, chk=chk)
        return y + len(lines) * lh

    def reg(self, x0, y0, x1, y1, name=""):
        self.boxes.append((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), name))

    # ------------------------------------------------------------------ lines
    def line(self, pts, kind="P", arrow=True, start_arrow=False, hop=True, mid_arrow=False):
        pts = [tuple(map(float, p)) for p in pts]
        # drop zero-length segments
        clean = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - clean[-1][0]) > 1e-6 or abs(p[1] - clean[-1][1]) > 1e-6:
                clean.append(p)
        self.lines.append(dict(pts=clean, kind=kind, arrow=arrow, start_arrow=start_arrow,
                               hop=hop and kind != "SIG", mid_arrow=mid_arrow))
        return clean

    def sig(self, pts, arrow=False):
        return self.line(pts, kind="SIG", arrow=arrow, hop=False)

    def _arrowhead(self, p_from, p_to, kind):
        (x1, y1), (x2, y2) = p_from, p_to
        a = math.atan2(y2 - y1, x2 - x1)
        L = 2.6 if kind in ("P", "S") else 2.1
        wv = 0.36
        p1 = (x2 - L * math.cos(a - wv), y2 - L * math.sin(a - wv))
        p2 = (x2 - L * math.cos(a + wv), y2 - L * math.sin(a + wv))
        self.gl.add(self.d.polygon([(x2, y2), p1, p2], fill=INK, stroke=INK, stroke_width=0.15))

    def finish(self):
        """Render all lines in creation order; later lines hop over earlier ones where they cross."""
        R = 1.25
        drawn: list[tuple] = []           # segments of already drawn hop-able lines
        for ln in self.lines:
            w, dash = LSTYLE[ln["kind"]]
            pts = ln["pts"]
            segs = list(zip(pts[:-1], pts[1:]))
            path = [f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"]
            for (a, b) in segs:
                hops = []
                if ln["hop"]:
                    for (c, e) in drawn:
                        X = _cross(a, b, c, e)
                        if X is not None:
                            hops.append(X)
                horiz = abs(a[1] - b[1]) < 1e-6
                vert = abs(a[0] - b[0]) < 1e-6
                if hops and (horiz or vert):
                    if horiz:
                        sgn = 1 if b[0] > a[0] else -1
                        hops = sorted(set(round(h[0], 3) for h in hops), key=lambda v: sgn * v)
                        last = a[0] - sgn * 10
                        for hx in hops:
                            if abs(hx - a[0]) < R + 0.3 or abs(hx - b[0]) < R + 0.3:
                                continue
                            if sgn * (hx - last) < 2 * R + 0.2:
                                continue
                            path.append(f"L {hx - sgn * R:.2f} {a[1]:.2f}")
                            path.append(f"A {R} {R} 0 0 {1 if sgn > 0 else 0} {hx + sgn * R:.2f} {a[1]:.2f}")
                            last = hx
                        path.append(f"L {b[0]:.2f} {b[1]:.2f}")
                    else:
                        sgn = 1 if b[1] > a[1] else -1
                        hops = sorted(set(round(h[1], 3) for h in hops), key=lambda v: sgn * v)
                        last = a[1] - sgn * 10
                        for hy in hops:
                            if abs(hy - a[1]) < R + 0.3 or abs(hy - b[1]) < R + 0.3:
                                continue
                            if sgn * (hy - last) < 2 * R + 0.2:
                                continue
                            last = hy
                            path.append(f"L {a[0]:.2f} {hy - sgn * R:.2f}")
                            path.append(f"A {R} {R} 0 0 {0 if sgn > 0 else 1} {a[0]:.2f} {hy + sgn * R:.2f}")
                        path.append(f"L {b[0]:.2f} {b[1]:.2f}")
                else:
                    path.append(f"L {b[0]:.2f} {b[1]:.2f}")
            kw = dict(fill="none", stroke=INK, stroke_width=w)
            if dash:
                kw["stroke_dasharray"] = dash
            self.gl.add(self.d.path(" ".join(path), **kw))
            if ln["arrow"] and len(pts) >= 2:
                self._arrowhead(pts[-2], pts[-1], ln["kind"])
            if ln["start_arrow"]:
                self._arrowhead(pts[1], pts[0], ln["kind"])
            if ln["mid_arrow"]:
                # arrow at middle of the longest segment
                a, b = max(segs, key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                self._arrowhead(a, m, ln["kind"])
            if ln["hop"]:
                drawn.extend(segs)

    # ------------------------------------------------------------------ clash checker
    def check(self, verbose=True, area=None):
        issues = []

        def ov(a, b, pad=0.0):
            return a[0] < b[2] - pad and b[0] < a[2] - pad and a[1] < b[3] - pad and b[1] < a[3] - pad

        T = self.texts
        for i in range(len(T)):
            for j in range(i + 1, len(T)):
                if ov(T[i], T[j], 0.15):
                    issues.append(f"text/text  '{T[i][4]}' @({T[i][0]:.0f},{T[i][1]:.0f}) x '{T[j][4]}'")
        for t in T:
            for b in self.boxes:
                if ov(t, b, 0.2):
                    issues.append(f"text/sym   '{t[4]}' @({t[0]:.0f},{t[1]:.0f}) x box {b[4]}")
        for t in T:
            for ln in self.lines:
                for a, b in zip(ln["pts"][:-1], ln["pts"][1:]):
                    if _seg_box(a, b, (t[0] + 0.25, t[1] + 0.25, t[2] - 0.25, t[3] - 0.25)):
                        issues.append(f"text/line  '{t[4]}' @({t[0]:.0f},{t[1]:.0f}) x {ln['kind']} "
                                      f"{a[0]:.0f},{a[1]:.0f}->{b[0]:.0f},{b[1]:.0f}")
                        break
        if area:
            x0, y0, x1, y1 = area
            for t in T:
                if t[0] < x0 or t[2] > x1 or t[1] < y0 or t[3] > y1:
                    issues.append(f"out-of-area '{t[4]}'")
        if verbose:
            for s in issues:
                print("   ", s)
        return issues

    # ================================================================== SYMBOLS
    def _poly(self, pts, fill="white", w=0.35, close=True, g=None, dash=None):
        kw = dict(fill=fill, stroke=INK, stroke_width=w)
        if dash:
            kw["stroke_dasharray"] = dash
        el = self.d.polygon(pts, **kw) if close else self.d.polyline(pts, **kw)
        (g or self.gs).add(el)
        return el

    def _path(self, dstr, fill="white", w=0.35, g=None, dash=None):
        kw = dict(fill=fill, stroke=INK, stroke_width=w)
        if dash:
            kw["stroke_dasharray"] = dash
        (g or self.gs).add(self.d.path(dstr, **kw))

    def _circle(self, c, r, fill="white", w=0.35, g=None):
        (g or self.gs).add(self.d.circle(c, r, fill=fill, stroke=INK, stroke_width=w))

    def _ln(self, a, b, w=0.3, g=None, dash=None):
        kw = dict(stroke=INK, stroke_width=w)
        if dash:
            kw["stroke_dasharray"] = dash
        (g or self.gs).add(self.d.line(a, b, **kw))

    # ---------------------------------------------------------------- columns
    def column(self, cx, y_top, w, h, w_bot=None, y_swage=None, trays=(), packed=(), tag=None, tray_side=None,
               hd=None):
        """Vertical column with 2:1 heads. trays = [(y, side, label)], side 'L'/'R' tells which wall the
        downcomer weir starts from; packed = [(y0, y1, label)] drawn as cross-hatched beds."""
        hd = hd or w * 0.25
        x0, x1 = cx - w / 2, cx + w / 2
        yb = y_top + h
        if w_bot and y_swage:
            bx0, bx1 = cx - w_bot / 2, cx + w_bot / 2
            sw = 6.0
            hdb = w_bot * 0.25
            d = (f"M {x0} {y_top + hd} A {w / 2} {hd} 0 0 1 {x1} {y_top + hd} L {x1} {y_swage} "
                 f"L {bx1} {y_swage + sw} L {bx1} {yb - hdb} A {w_bot / 2} {hdb} 0 0 1 {bx0} {yb - hdb} "
                 f"L {bx0} {y_swage + sw} L {x0} {y_swage} Z")
        else:
            d = (f"M {x0} {y_top + hd} A {w / 2} {hd} 0 0 1 {x1} {y_top + hd} L {x1} {yb - hd} "
                 f"A {w / 2} {hd} 0 0 1 {x0} {yb - hd} Z")
        self._path(d, w=0.55)
        for (yy, side, lab) in trays:
            ww = w if not (w_bot and y_swage and yy > y_swage) else w_bot
            xa, xb = cx - ww / 2, cx + ww / 2
            if side == "L":
                self._ln((xa, yy), (xb - ww * 0.22, yy), 0.3)
                self._ln((xb - ww * 0.22, yy), (xb - ww * 0.22, yy + 2.2), 0.3)
            else:
                self._ln((xb, yy), (xa + ww * 0.22, yy), 0.3)
                self._ln((xa + ww * 0.22, yy), (xa + ww * 0.22, yy + 2.2), 0.3)
            if lab:
                tx = xb - 1.2 if side == "L" else xa + 1.2
                self.text(lab, tx, yy - 0.8, 2.2, "end" if side == "L" else "start", chk=False)
        for (ya, yb_, lab) in packed:
            ww = w
            xa, xb = cx - ww / 2, cx + ww / 2
            self.gs.add(self.d.rect((xa + 0.6, ya), (ww - 1.2, yb_ - ya), fill="white", stroke=INK,
                                    stroke_width=0.3))
            n = max(2, int(ww / 4))
            for i in range(n + 1):
                xx = xa + 0.6 + (ww - 1.2) * i / n
                xn = xa + 0.6 + (ww - 1.2) * (i + 1) / n
                if i < n:
                    self._ln((xx, ya), (xn, yb_), 0.18)
                    self._ln((xn, ya), (xx, yb_), 0.18)
            if lab:
                bw = _tw(lab, 2.2) + 2
                self.gs.add(self.d.rect((cx - bw / 2, (ya + yb_) / 2 - 2.1), (bw, 3.2), fill="white",
                                        stroke="none"))
                self.text(lab, cx, (ya + yb_) / 2 + 0.6, 2.2, "middle", chk=False)
        self.reg(x0, y_top, x1, yb, f"col {tag}")
        if tag:
            pass
        return dict(top=(cx, y_top), bot=(cx, yb), xl=x0, xr=x1, xbl=cx - (w_bot or w) / 2,
                    xbr=cx + (w_bot or w) / 2)

    # ---------------------------------------------------------------- vessels
    def hvessel(self, cx, cy, L, D, boot=None, internals=None, tag=None, weir=False):
        """Horizontal drum with elliptical heads. boot = (x_center, width, depth)."""
        hd = D * 0.28
        x0, x1 = cx - L / 2, cx + L / 2
        y0, y1 = cy - D / 2, cy + D / 2
        d = (f"M {x0 + hd} {y0} L {x1 - hd} {y0} A {hd} {D / 2} 0 0 1 {x1 - hd} {y1} L {x0 + hd} {y1} "
             f"A {hd} {D / 2} 0 0 1 {x0 + hd} {y0} Z")
        if boot:
            bx, bw, bd = boot
            self._path(f"M {bx - bw / 2} {y1 - 1} L {bx - bw / 2} {y1 + bd - bw * 0.25} "
                       f"A {bw / 2} {bw * 0.25} 0 0 0 {bx + bw / 2} {y1 + bd - bw * 0.25} L {bx + bw / 2} {y1 - 1} Z",
                       w=0.5)
        self._path(d, w=0.55)
        for a, b in [((x0 + hd, y0), (x0 + hd, y1)), ((x1 - hd, y0), (x1 - hd, y1))]:
            self._ln(a, b, 0.2, dash="1,0.8")
        if internals == "grid":           # desalter electrode grids
            for k in (0.38, 0.52):
                yy = y0 + D * k
                self._ln((x0 + hd + 2, yy), (x1 - hd - 2, yy), 0.3, dash="2.2,1")
            self.text("+", cx - L * 0.3, y0 + D * 0.38 - 0.6, 2.4, "middle", chk=False)
            self.text("−", cx - L * 0.3, y0 + D * 0.52 + 2.6, 2.4, "middle", chk=False)
            self._ln((x0 + hd + 1, y0 + D * 0.80), (x1 - hd - 1, y0 + D * 0.80), 0.2, dash="0.6,0.8")
        if weir:
            self._ln((cx + L * 0.25, y1), (cx + L * 0.25, y0 + D * 0.45), 0.35)
        self.reg(x0, y0, x1, y1 + (boot[2] if boot else 0), f"hv {tag}")
        return dict(l=(x0, cy), r=(x1, cy), top=lambda x: (x, y0), bot=lambda x: (x, y1), y0=y0, y1=y1,
                    x0=x0, x1=x1, boot=(boot[0], y1 + boot[2]) if boot else None)

    def vvessel(self, cx, cy, D, H, tag=None, mesh=False):
        hd = D * 0.25
        x0, x1 = cx - D / 2, cx + D / 2
        y0, y1 = cy - H / 2, cy + H / 2
        d = (f"M {x0} {y0 + hd} A {D / 2} {hd} 0 0 1 {x1} {y0 + hd} L {x1} {y1 - hd} "
             f"A {D / 2} {hd} 0 0 1 {x0} {y1 - hd} Z")
        self._path(d, w=0.55)
        if mesh:
            self.gs.add(self.d.rect((x0 + 0.5, y0 + hd + 1.5), (D - 1, 1.6), fill="white", stroke=INK,
                                    stroke_width=0.2))
            for i in range(int(D)):
                xx = x0 + 0.5 + i
                self._ln((xx, y0 + hd + 1.5), (xx + 1, y0 + hd + 3.1), 0.15)
        self.reg(x0, y0, x1, y1, f"vv {tag}")
        return dict(top=(cx, y0), bot=(cx, y1), l=(x0, cy), r=(x1, cy), x0=x0, x1=x1, y0=y0, y1=y1)

    # ---------------------------------------------------------------- heat exchangers
    def hx(self, cx, cy, r=5.5, tube="h", shells=1):
        """Shell & tube exchanger: circle with tube-side zig-zag. tube 'h' = tube side W->E, 'v' = N->S.
        shells > 1 draws stacked shell outlines behind (multiple shells)."""
        for k in range(min(shells, 4) - 1, 0, -1):
            self._circle((cx + 1.3 * k, cy - 1.3 * k), r, w=0.3)
        self._circle((cx, cy), r, w=0.5)
        z = 1.6
        if tube == "h":
            pts = [(cx - r, cy), (cx - r * 0.55, cy), (cx - r * 0.3, cy - z), (cx, cy + z), (cx + r * 0.3, cy - z),
                   (cx + r * 0.55, cy), (cx + r, cy)]
        else:
            pts = [(cx, cy - r), (cx, cy - r * 0.55), (cx - z, cy - r * 0.3), (cx + z, cy), (cx - z, cy + r * 0.3),
                   (cx, cy + r * 0.55), (cx, cy + r)]
        self._poly(pts, fill="none", w=0.4, close=False)
        self.reg(cx - r, cy - r - 1.3 * (shells - 1), cx + r + 1.3 * (shells - 1), cy + r, "hx")
        return dict(W=(cx - r, cy), E=(cx + r, cy), N=(cx, cy - r), S=(cx, cy + r), c=(cx, cy), r=r)

    def kettle(self, cx, cy, L=26, D=11):
        """Kettle reboiler / steam generator (enlarged shell, U-bundle). Ports: tin/tout at channel (left),
        vap at shell top, liq at shell bottom, ovf at right end bottom."""
        dc = D * 0.55
        x0 = cx - L / 2
        xc = x0 + L * 0.22                # channel / tubesheet
        xs = xc + L * 0.14                # end of cone
        x1 = cx + L / 2
        hd = D * 0.22
        d = (f"M {x0} {cy - dc / 2} L {xc} {cy - dc / 2} L {xs} {cy - D / 2} L {x1 - hd} {cy - D / 2} "
             f"A {hd} {D / 2} 0 0 1 {x1 - hd} {cy + D / 2} L {xs} {cy + D / 2} L {xc} {cy + dc / 2} "
             f"L {x0} {cy + dc / 2} Z")
        self._path(d, w=0.5)
        self._ln((xc, cy - dc / 2), (xc, cy + dc / 2), 0.35)
        self._ln((x0 + 0.3, cy), (xc, cy), 0.25)
        # U bundle
        ub = x1 - hd - 2
        self._path(f"M {xc} {cy - dc * 0.28} L {ub} {cy - dc * 0.28} A {dc * 0.28} {dc * 0.28} 0 0 1 {ub} "
                   f"{cy + dc * 0.28} L {xc} {cy + dc * 0.28}", fill="none", w=0.3)
        # weir
        self._ln((x1 - hd - 0.5, cy + D / 2), (x1 - hd - 0.5, cy - D * 0.05), 0.35)
        self.reg(x0, cy - D / 2, x1, cy + D / 2, "kettle")
        return dict(tin=(x0, cy - dc / 4), tout=(x0, cy + dc / 4), tin_top=((x0 + xc) / 2, cy - dc / 2),
                    tout_bot=((x0 + xc) / 2, cy + dc / 2), vap=((xs + x1) / 2, cy - D / 2),
                    liq=((xs + x1) / 2 - 3, cy + D / 2), ovf=(x1 - hd / 2 - 2, cy + D / 2 - 0.4), x1=x1, x0=x0,
                    xs=xs, top=cy - D / 2, bot=cy + D / 2)

    def aircooler(self, cx, cy, w=26, h=6, fans=2):
        """Air-cooled exchanger: bundle with tube pass hint and fans with motors below."""
        x0, y0 = cx - w / 2, cy - h / 2
        self.gs.add(self.d.rect((x0, y0), (w, h), fill="white", stroke=INK, stroke_width=0.5))
        n = 7
        pts = [(x0, cy)]
        for i in range(1, n):
            pts.append((x0 + w * i / n, cy + (h * 0.3 if i % 2 else -h * 0.3)))
        pts.append((x0 + w, cy))
        self._poly(pts, fill="none", w=0.3, close=False)
        nf = min(max(fans, 1), 4)
        for i in range(nf):
            fx = x0 + w * (i + 0.5) / nf
            fy = cy + h / 2 + 2.6
            bl = min(w / nf * 0.42, 5)
            self._path(f"M {fx - bl} {fy - 0.9} L {fx + bl} {fy + 0.9} L {fx + bl} {fy - 0.9} L {fx - bl} {fy + 0.9} Z",
                       fill=INK, w=0.2)
            self._ln((fx, fy), (fx, fy + 3.2), 0.3)
            self._circle((fx, fy + 4.6), 1.4, w=0.3)
            self.text("M", fx, fy + 5.4, 2.2, "middle", chk=False)
        self.reg(x0, y0, x0 + w, cy + h / 2 + 8, "ac")
        return dict(W=(x0, cy), E=(x0 + w, cy), N=(cx, y0), S=(cx, cy + h / 2), x0=x0, x1=x0 + w,
                    bot=cy + h / 2 + 7.5)

    def air_preheater(self, cx, cy, w=16, h=22):
        x0, y0 = cx - w / 2, cy - h / 2
        self.gs.add(self.d.rect((x0, y0), (w, h), fill="white", stroke=INK, stroke_width=0.5))
        for i in range(1, 6):
            yy = y0 + h * i / 6
            self._ln((x0, yy), (x0 + w, yy), 0.2, dash="0.8,0.6")
        self._ln((x0, y0), (x0 + w, y0 + h), 0.25)
        self.reg(x0, y0, x0 + w, y0 + h, "aph")
        return dict(N=(cx, y0), S=(cx, y0 + h), W=(x0, cy), E=(x0 + w, cy), x0=x0, x1=x0 + w, y0=y0, y1=y0 + h)

    # ---------------------------------------------------------------- machines
    def pump(self, cx, cy, r=3.6, face="R"):
        """Centrifugal pump: circle, tangential discharge at top, base. face 'R' discharges to the right."""
        s = 1 if face == "R" else -1
        self._path(f"M {cx - s * 0.6} {cy - r} L {cx + s * (r + 1.8)} {cy - r} L {cx + s * (r + 1.8)} "
                   f"{cy - r + 1.6} L {cx + s * r * 0.75} {cy - r + 1.6}", fill="white", w=0.45)
        self._circle((cx, cy), r, w=0.5)
        self._poly([(cx - r * 0.8, cy + r * 1.5), (cx + r * 0.8, cy + r * 1.5), (cx + r * 0.45, cy + r * 0.85),
                    (cx - r * 0.45, cy + r * 0.85)], fill="white", w=0.35)
        self.reg(cx - r - (1.8 if s < 0 else 0), cy - r, cx + r + (1.8 if s > 0 else 0), cy + r * 1.5, "pump")
        return dict(suc=(cx - s * r, cy), dis=(cx + s * (r + 1.8), cy - r + 0.8), top=(cx + s * (r + 1.8), cy - r),
                    c=(cx, cy), r=r)

    def fan(self, cx, cy, r=4.5, face="R", up=False):
        """Centrifugal fan / blower (FD/ID fan)."""
        s = 1 if face == "R" else -1
        if up:
            self._path(f"M {cx + s * r} {cy} L {cx + s * r} {cy - r - 3} L {cx + s * (r - 3)} {cy - r - 3} "
                       f"L {cx + s * (r - 3)} {cy - r + 0.8}", fill="white", w=0.45)
        else:
            self._path(f"M {cx} {cy - r} L {cx + s * (r + 3)} {cy - r} L {cx + s * (r + 3)} {cy - r + 3} "
                       f"L {cx + s * r * 0.9} {cy - r + 3}", fill="white", w=0.45)
        self._circle((cx, cy), r, w=0.5)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            self._ln((cx, cy), (cx + r * 0.75 * math.cos(a), cy + r * 0.75 * math.sin(a)), 0.3)
        self.reg(cx - r, cy - r - (3 if up else 0), cx + r + 3, cy + r, "fan")
        if up:
            return dict(suc=(cx - s * r, cy), dis=(cx + s * (r - 1.5), cy - r - 3), c=(cx, cy))
        return dict(suc=(cx - s * r, cy), dis=(cx + s * (r + 3), cy - r + 1.5), c=(cx, cy))

    def ejector(self, x0, cy, L=26, suction="bot"):
        """Steam jet ejector, motive steam enters at left end, discharge at right end."""
        hc = 7.0
        pts = [(x0, cy - 1.0), (x0 + 3, cy - 1.0), (x0 + 3, cy - hc / 2), (x0 + 9, cy - hc / 2),
               (x0 + 13, cy - 1.2), (x0 + 16, cy - 1.2), (x0 + L, cy - 2.8), (x0 + L, cy + 2.8),
               (x0 + 16, cy + 1.2), (x0 + 13, cy + 1.2), (x0 + 9, cy + hc / 2), (x0 + 3, cy + hc / 2),
               (x0 + 3, cy + 1.0), (x0, cy + 1.0)]
        self._poly(pts, w=0.5)
        # motive nozzle
        self._poly([(x0 + 3, cy - 0.8), (x0 + 9, cy - 0.3), (x0 + 9, cy + 0.3), (x0 + 3, cy + 0.8)], w=0.25)
        self.reg(x0, cy - hc / 2, x0 + L, cy + hc / 2, "ej")
        sy = cy + hc / 2 if suction == "bot" else cy - hc / 2
        return dict(motive=(x0, cy), suc=(x0 + 6, sy), dis=(x0 + L, cy))

    def heater_box(self, x0, y0, w, h, label_coils=True):
        """Radiant box rectangle with wall coils."""
        self.gs.add(self.d.rect((x0, y0), (w, h), fill="white", stroke=INK, stroke_width=0.6))
        self.reg(x0, y0, x0 + w, y0 + h, "heater")

    def coil_v(self, x, y0, y1, amp=1.6, n=None):
        """Vertical serpentine tube coil hint."""
        n = n or max(4, int((y1 - y0) / 4))
        pts = [(x, y0)]
        for i in range(1, n):
            pts.append((x + (amp if i % 2 else -amp), y0 + (y1 - y0) * i / n))
        pts.append((x, y1))
        self._poly(pts, fill="none", w=0.35, close=False)

    def coil_h(self, x0, x1, y, amp=1.6, n=None):
        n = n or max(4, int((x1 - x0) / 4))
        pts = [(x0, y)]
        for i in range(1, n):
            pts.append((x0 + (x1 - x0) * i / n, y + (amp if i % 2 else -amp)))
        pts.append((x1, y))
        self._poly(pts, fill="none", w=0.35, close=False)

    def burner(self, cx, yb, s=2.6):
        self._path(f"M {cx - s * 0.5} {yb} Q {cx - s * 0.6} {yb - s * 0.9} {cx} {yb - s * 1.6} "
                   f"Q {cx + s * 0.6} {yb - s * 0.9} {cx + s * 0.5} {yb} Z", fill="white", w=0.3)

    def stack(self, cx, y_base, y_top, wb=9, wt=6):
        self._poly([(cx - wb / 2, y_base), (cx - wt / 2, y_top), (cx + wt / 2, y_top), (cx + wb / 2, y_base)],
                   w=0.5)
        self.reg(cx - wb / 2, y_top, cx + wb / 2, y_base, "stack")

    def package(self, x0, y0, w, h, lines):
        self.gs.add(self.d.rect((x0, y0), (w, h), fill="white", stroke=INK, stroke_width=0.4,
                                stroke_dasharray="2,0.8"))
        for i, s in enumerate(lines):
            self.text(s, x0 + w / 2, y0 + 3.4 + i * 2.9, 2.2 if i else 2.5, "middle", bold=(i == 0), chk=False)
        self.reg(x0, y0, x0 + w, y0 + h, "pkg")
        return dict(W=(x0, y0 + h / 2), E=(x0 + w, y0 + h / 2), N=(x0 + w / 2, y0), S=(x0 + w / 2, y0 + h))

    # ---------------------------------------------------------------- valves / instruments
    def cv(self, x, y, orient="h", act="up", tag=None, tag_side=None):
        """Control valve (bow-tie body + diaphragm actuator). Returns actuator connection point."""
        a, b = 2.2, 1.45
        if orient == "h":
            self._poly([(x - a, y - b), (x + a, y + b), (x + a, y - b), (x - a, y + b)], w=0.4)
            s = -1 if act == "up" else 1
            self._ln((x, y), (x, y + s * 3.4), 0.35)
            ya = y + s * 3.4
            self._path(f"M {x - 1.9} {ya} A 1.9 1.9 0 0 {1 if s < 0 else 0} {x + 1.9} {ya} Z", w=0.35)
            pt = (x, ya + s * 1.9)
            self.reg(x - a, min(y - b, ya - 1.9), x + a, max(y + b, ya + 1.9), f"cv {tag}")
        else:
            self._poly([(x - b, y - a), (x + b, y + a), (x - b, y + a), (x + b, y - a)], w=0.4)
            s = 1 if act == "right" else -1
            self._ln((x, y), (x + s * 3.4, y), 0.35)
            xa = x + s * 3.4
            self._path(f"M {xa} {y - 1.9} A 1.9 1.9 0 0 {1 if s > 0 else 0} {xa} {y + 1.9} Z", w=0.35)
            pt = (xa + s * 1.9, y)
            self.reg(min(x - b, xa - 1.9), y - a, max(x + b, xa + 1.9), y + a, f"cv {tag}")
        if tag:
            side = tag_side or ("below" if orient == "h" else ("left" if act == "right" else "right"))
            if side == "below":
                self.text(tag, x, y + b + 3.0, 2.2, "middle")
            elif side == "above":
                self.text(tag, x, y - 6.8, 2.2, "middle")
            elif side == "left":
                self.text(tag, x - b - 0.8, y + 0.8, 2.2, "end")
            elif side == "right":
                self.text(tag, x + b + 0.8, y + 0.8, 2.2, "start")
            elif side == "belowright":
                self.text(tag, x + 2.6, y + b + 2.8, 2.2, "start")
            elif side == "belowleft":
                self.text(tag, x - 2.6, y + b + 2.8, 2.2, "end")
        return pt

    def hand_valve(self, x, y, orient="h"):
        a, b = 1.6, 1.1
        if orient == "h":
            self._poly([(x - a, y - b), (x + a, y + b), (x + a, y - b), (x - a, y + b)], w=0.35)
        else:
            self._poly([(x - b, y - a), (x + b, y + a), (x - b, y + a), (x + b, y - a)], w=0.35)

    def bubble(self, x, y, tag, r=4.7):
        """ISA-5.1 shared display / DCS function: circle in square omitted on PFD -> circle with bar."""
        letters, num = tag.split("-")
        self._circle((x, y), r, w=0.35)
        self._ln((x - r, y), (x + r, y), 0.25)
        fs = 2.3 if len(letters) <= 3 else 2.2
        self.text(letters, x, y - 1.0, fs, "middle", chk=False)
        self.text(num, x, y + 3.0, 2.2, "middle", chk=False)
        self.reg(x - r, y - r, x + r, y + r, f"bub {tag}")
        return dict(c=(x, y), N=(x, y - r), S=(x, y + r), W=(x - r, y), E=(x + r, y))

    def diamond(self, x, y, no, r=3.5):
        self._poly([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], w=0.4)
        self.text(str(no), x, y + 0.85, 2.4, "middle", bold=True, chk=False)
        self.reg(x - r, y - r, x + r, y + r, f"dia {no}")

    def flag(self, x, y, txt, kind="T", leader=None, anchor="middle"):
        """Operating-condition flag. kind 'T' rounded box, 'P' hexagon-ended box, 'F' plain box.
        (x, y) = box centre; leader = point the flag refers to (thin line)."""
        size = 2.2
        w = _tw(txt, size) + 2.4
        h = 3.6
        cx = x if anchor == "middle" else (x + w / 2 if anchor == "start" else x - w / 2)
        x0, y0 = cx - w / 2, y - h / 2
        if leader:
            self._ln((cx, y), leader, 0.2)
        if kind == "T":
            self.gs.add(self.d.rect((x0, y0), (w, h), rx=1.8, ry=1.8, fill="white", stroke=INK, stroke_width=0.3))
        elif kind == "P":
            self._poly([(x0, y), (x0 + 1.2, y0), (x0 + w - 1.2, y0), (x0 + w, y), (x0 + w - 1.2, y0 + h),
                        (x0 + 1.2, y0 + h)], w=0.3)
        else:
            self.gs.add(self.d.rect((x0, y0), (w, h), fill="white", stroke=INK, stroke_width=0.3))
        self.text(txt, cx, y + 0.8, size, "middle", chk=False)
        self.reg(x0, y0, x0 + w, y0 + h, f"flag {txt}")
        return w

    def offsheet(self, x, y, direction, l1, l2, w=None, h=8.4):
        """Off-sheet connector pentagon. (x, y) = the point where the process line attaches:
        for direction 'R' (flow to the right) a FROM connector has its tip at (x,y)... callers use
        `tip`/`base` returned. The connector is drawn with its base at x (direction R) or tip at x (L)."""
        size = 2.2
        w = w or max(_tw(l1, size), _tw(l2, size) * 1.07) + 7
        if direction == "R":
            x0 = x
            pts = [(x0, y - h / 2), (x0 + w - 4, y - h / 2), (x0 + w, y), (x0 + w - 4, y + h / 2), (x0, y + h / 2)]
            tx = x0 + (w - 4) / 2
            base, tip = (x0, y), (x0 + w, y)
        else:
            x0 = x
            pts = [(x0, y), (x0 + 4, y - h / 2), (x0 + w, y - h / 2), (x0 + w, y + h / 2), (x0 + 4, y + h / 2)]
            tx = x0 + 4 + (w - 4) / 2
            base, tip = (x0 + w, y), (x0, y)
        self._poly(pts, w=0.45)
        self.text(l1, tx, y - 0.7, size, "middle", chk=False)
        self.text(l2, tx, y + 2.9, size, "middle", bold=True, chk=False)
        self.reg(x0, y - h / 2, x0 + w, y + h / 2, f"off {l1}")
        return dict(base=base, tip=tip, w=w)


def _cross(a, b, c, e):
    """Intersection point of an axis-aligned segment a-b with perpendicular segment c-e (interiors only)."""
    ah = abs(a[1] - b[1]) < 1e-6
    av = abs(a[0] - b[0]) < 1e-6
    ch = abs(c[1] - e[1]) < 1e-6
    cvv = abs(c[0] - e[0]) < 1e-6
    eps = 0.4
    if ah and cvv:
        x, y = c[0], a[1]
        if min(a[0], b[0]) + eps < x < max(a[0], b[0]) - eps and min(c[1], e[1]) + eps < y < max(c[1], e[1]) - eps:
            return (x, y)
    if av and ch:
        x, y = a[0], c[1]
        if min(a[1], b[1]) + eps < y < max(a[1], b[1]) - eps and min(c[0], e[0]) + eps < x < max(c[0], e[0]) - eps:
            return (x, y)
    return None


def _seg_box(a, b, box):
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return False
    if abs(a[1] - b[1]) < 1e-6:
        return y0 < a[1] < y1 and min(a[0], b[0]) < x1 and max(a[0], b[0]) > x0
    if abs(a[0] - b[0]) < 1e-6:
        return x0 < a[0] < x1 and min(a[1], b[1]) < y1 and max(a[1], b[1]) > y0
    # diagonal: sample
    for k in range(21):
        x = a[0] + (b[0] - a[0]) * k / 20
        y = a[1] + (b[1] - a[1]) * k / 20
        if x0 < x < x1 and y0 < y < y1:
            return True
    return False
