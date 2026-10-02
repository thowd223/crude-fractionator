"""Sections / elevations CFU-000-PL-ELV-001..003 generated from the layout model."""
from __future__ import annotations

import json
import math
from pathlib import Path

from ..drawing.sheet import Sheet
from .model import GRADE, ROOT

STD_NPS = [2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 30, 36, 42, 48]
GREY = "#8a8a8a"


def nps_for(q_m3h, v=2.0):
    d_in = math.sqrt(4 * q_m3h / 3600 / math.pi / v) / 0.0254
    for n in STD_NPS:
        if n >= d_in * 0.97:
            return n
    return STD_NPS[-1]


class Sec:
    """Section view helper: horizontal = plant y (looking west, north to the right), vertical = EL."""

    def __init__(self, sh, scale_mm_per_m, ox, oy, y0):
        self.sh, self.d, self.g = sh, sh.dwg, sh.g
        self.k, self.ox, self.oy, self.y0 = scale_mm_per_m, ox, oy, y0

    def P(self, y, z):
        return (self.ox + self.k * (y - self.y0), self.oy - self.k * (z - GRADE))

    def rect(self, y0, z0, y1, z1, **kw):
        a = self.P(min(y0, y1), max(z0, z1))
        return self.d.rect(a, (self.k * abs(y1 - y0), self.k * abs(z1 - z0)), **kw)

    def el(self, y, z, label=None, right=True, color="black", size=2.2):
        sx, sy = self.P(y, z)
        g, d = self.g, self.d
        g.add(d.polygon([(sx, sy), (sx - 1.4, sy - 2.2), (sx + 1.4, sy - 2.2)], fill="none", stroke=color, stroke_width=0.3))
        g.add(d.line((sx - 3, sy), (sx + 3, sy), stroke=color, stroke_width=0.25))
        t = label or f"EL {z:.3f}"
        self.sh.text(t, sx + (2.2 if right else -2.2), sy - 2.6, size=size, anchor="start" if right else "end", color=color)

    def hdim(self, ya, yb, z, label=None, off=0, color="#0050b0", size=2.2):
        (x1, s1), (x2, _) = self.P(ya, z), self.P(yb, z)
        s1 += off
        g, d = self.g, self.d
        g.add(d.line((x1, s1), (x2, s1), stroke=color, stroke_width=0.25))
        for xx, sg in ((x1, 1), (x2, -1)):
            g.add(d.polygon([(xx, s1), (xx + sg * 1.6, s1 - 0.5), (xx + sg * 1.6, s1 + 0.5)], fill=color))
            g.add(d.line((xx, s1 - 2), (xx, s1 + 2), stroke=color, stroke_width=0.2))
        self.sh.text(label or f"{abs(yb - ya):.1f} m", (x1 + x2) / 2, s1 - 1.0, size=size, anchor="middle", color=color)

    def vdim(self, y, za, zb, label=None, off=0, color="#0050b0", size=2.0):
        (x1, s1), (_, s2) = self.P(y, za), self.P(y, zb)
        x1 += off
        g, d = self.g, self.d
        g.add(d.line((x1, s1), (x1, s2), stroke=color, stroke_width=0.25))
        for ss, sg in ((s1, -1), (s2, 1)):
            g.add(d.polygon([(x1, ss), (x1 - 0.5, ss + sg * 1.6), (x1 + 0.5, ss + sg * 1.6)], fill=color))
        t = self.sh.text(label or f"{abs(zb - za):.1f} m", x1 - 1.0, (s1 + s2) / 2, size=size, anchor="middle", color=color)
        t.rotate(-90, center=(x1 - 1.0, (s1 + s2) / 2))

    def grade(self, ya, yb):
        g, d = self.g, self.d
        a, b = self.P(ya, GRADE), self.P(yb, GRADE)
        g.add(d.line(a, b, stroke="black", stroke_width=0.6))
        for i in range(int((b[0] - a[0]) / 3)):
            x = a[0] + i * 3
            g.add(d.line((x, a[1]), (x - 2, a[1] + 2), stroke="black", stroke_width=0.2))


# ------------------------------------------------------------------------------------------
def draw_item(S: Sec, it, faint=False, label=True, rack=None):
    d, g, sh = S.d, S.g, S.sh
    col = GREY if faint else "black"
    fill = "white"
    sw = 0.25 if faint else 0.4
    dash = "2,1" if faint else "none"
    kw = dict(fill=fill, stroke=col, stroke_width=sw, stroke_dasharray=dash)
    x0, y0, x1, y1 = it["bbox"]
    t = it["type"]
    if it["shape"] == "vcyl":
        y = it["y"]
        body = it.get("body") or [[it["z_base"], it["top_el"], it["D"]]]
        Dbot = body[0][2]
        Dtop = body[-1][2]
        btl = body[0][0]
        # skirt
        if btl - Dbot / 4 > it["z_base"] + 0.05:
            g.add(S.rect(y - Dbot / 2, it["z_base"], y + Dbot / 2, btl - Dbot / 4 + 0.05, **kw))
        # bottom head
        cx, cz = S.P(y, btl)
        g.add(d.ellipse((cx, cz), (Dbot / 2 * S.k, Dbot / 4 * S.k), **kw))
        ttl = body[-1][1]
        cx2, cz2 = S.P(y, ttl)
        g.add(d.ellipse((cx2, cz2), (Dtop / 2 * S.k, Dtop / 4 * S.k), **kw))
        prev = None
        for z0, z1, D in body:
            if prev:
                pz1, pD = prev
                a1, b1 = S.P(y - pD / 2, pz1)
                a2, b2 = S.P(y + pD / 2, pz1)
                a3, b3 = S.P(y + D / 2, z0)
                a4, b4 = S.P(y - D / 2, z0)
                g.add(d.polygon([(a1, b1), (a2, b2), (a3, b3), (a4, b4)], **kw))
            g.add(S.rect(y - D / 2, z0, y + D / 2, z1, **kw))
            prev = (z1, D)
        if label:
            tx, ty = S.P(y, it["top_el"])
            sh.text(it["tag"], tx, ty - 4 - (2 if faint else 0), size=3.0 if not faint else 2.2, anchor="middle", bold=True,
                    color=col)
        return
    if it["shape"] == "hcyl":
        D = it["D"]
        if abs(math.sin(math.radians(it["rotation"]))) < 0.5:     # axis E-W: seen end-on
            cx, cz = S.P(it["y"], it["z_base"] + D / 2)
            if it["z_base"] - GRADE > 0.4 and it["z_base"] < 110:
                g.add(S.rect(it["y"] - D * 0.35, GRADE, it["y"] + D * 0.35, it["z_base"] + D / 2, **kw))
            g.add(d.circle((cx, cz), D / 2 * S.k, **kw))
            if it.get("boot"):
                b = it["boot"]
                g.add(S.rect(it["y"] - b["D"] / 2, it["z_base"] - b["H"], it["y"] + b["D"] / 2, it["z_base"] + 0.1, **kw))
                g.add(d.circle((cx, cz), D / 2 * S.k - 0.01, **kw))
        else:
            zb = it["z_base"]
            if zb - GRADE > 0.4 and zb < 110:
                for yy in (y0 + 1.2, y1 - 1.2):
                    g.add(S.rect(yy - 0.3, GRADE, yy + 0.3, zb, **kw))
            a = S.P(y0, zb + D)
            g.add(d.rect(a, ((y1 - y0) * S.k, D * S.k), rx=D * S.k / 2.5, ry=D * S.k / 2.5, **kw))
        if label:
            tx, ty = S.P(it["y"], it["top_el"] + 0.3)
            sh.text(it["tag"], tx, ty - 1.0, size=2.2 if not faint else 1.8, anchor="middle", bold=not faint, color=col)
        return
    if it["shape"] == "heater":
        y, W = it["y"], it["W"]
        r, c, s = it["radiant"], it["convection"], it["stack"]
        for yy in (y - W / 2 + 0.5, y + W / 2 - 0.5, y):
            g.add(S.rect(yy - 0.25, GRADE, yy + 0.25, r["z0"], **kw))
        g.add(S.rect(y - W / 2, r["z0"], y + W / 2, r["z1"], **kw))
        cw = c["W"]
        a1, b1 = S.P(y - W / 2, r["z1"])
        a2, b2 = S.P(y + W / 2, r["z1"])
        a3, b3 = S.P(y + cw / 2, r["z1"] + 2.5)
        a4, b4 = S.P(y - cw / 2, r["z1"] + 2.5)
        g.add(d.polygon([(a1, b1), (a2, b2), (a3, b3), (a4, b4)], **kw))
        g.add(S.rect(y - cw / 2, r["z1"] + 2.5, y + cw / 2, c["z1"], **kw))
        g.add(S.rect(y - s["D"] / 2, c["z1"], y + s["D"] / 2, s["z1"], **kw))
        # burners
        for i in range(5):
            yy = y - W / 2 + W * (i + 0.5) / 5
            g.add(S.rect(yy - 0.3, r["z0"] - 0.9, yy + 0.3, r["z0"], fill="none", stroke=col, stroke_width=0.2))
        if label:
            tx, ty = S.P(y, s["z1"])
            sh.text(it["tag"], tx, ty - 4, size=3.0, anchor="middle", bold=True, color=col)
            S.el(y + s["D"] / 2 + 0.5, s["z1"], f"STACK TOP EL {s['z1']:.3f}", color=col)
            S.el(y + W / 2, r["z1"], f"EL {r['z1']:.3f}", color=col, size=2.1)
        return
    # boxes
    if t == "Air cooler":
        g.add(S.rect(y0, it["z_base"], y1, it["z_base"] + 1.2, **kw))
        g.add(S.rect(y0 + 0.5, it["z_base"] - 1.2, y1 - 0.5, it["z_base"], fill="white", stroke=col, stroke_width=0.2,
                     stroke_dasharray=dash))
        nf = it.get("fans", 2)
        for i in range(nf):
            yy = y0 + (y1 - y0) * (i + 0.5) / nf
            g.add(S.rect(yy - 1.8, it["z_base"] - 1.6, yy + 1.8, it["z_base"] - 1.35, fill=col, stroke="none"))
            g.add(S.rect(yy - 0.2, it["z_base"] - 2.0, yy + 0.2, it["z_base"] - 1.35, fill=col, stroke="none"))
        if label:
            tx, ty = S.P(it["y"], it["z_base"] + 1.2)
            sh.text(it["parent_tag"], tx, ty - 1.2, size=2.2, anchor="middle", bold=True, color=col)
        return
    g.add(S.rect(y0, it["z_base"], y1, it["top_el"], **kw))
    if t == "Pump":
        # motor + casing split
        ym = it["y"]
        g.add(d.line(S.P(ym, it["z_base"]), S.P(ym, it["top_el"]), stroke=col, stroke_width=0.2))
    if label:
        tx, ty = S.P(it["y"], it["top_el"])
        sh.text(it["tag"] if t != "Pump" else it["tag"][:-1] + "A/B", tx, ty - 1.0, size=1.9, anchor="middle",
                color=col)


def draw_rack(S: Sec, L, faint=False, detail=False):
    rk = L.rack
    d, g = S.d, S.g
    col = "#333"
    for y in (rk["y0"], rk["y1"]):
        g.add(S.rect(y - 0.2, GRADE, y + 0.2, rk["tiers"][-1]["el"], fill="#ddd", stroke=col, stroke_width=0.3))
        g.add(S.rect(y - 0.6, GRADE - 0.3, y + 0.6, GRADE, fill="#bbb", stroke=col, stroke_width=0.2))
    for t in rk["tiers"]:
        g.add(S.rect(rk["y0"] - 0.2, t["el"] - 0.5, rk["y1"] + 0.2, t["el"], fill="#ddd", stroke=col, stroke_width=0.3))
    # AC support posts
    for y in (rk["y0"] + 0.5, rk["y1"] - 0.5):
        g.add(S.rect(y - 0.12, rk["tiers"][-1]["el"], y + 0.12, rk["air_cooler_deck"]["el"], fill="#ddd", stroke=col, stroke_width=0.2))
    # knee braces
    for y, sgn in ((rk["y0"], 1), (rk["y1"], -1)):
        for t in rk["tiers"]:
            g.add(d.line(S.P(y + 0.2 * sgn, t["el"] - 1.6), S.P(y + 1.4 * sgn, t["el"] - 0.5), stroke=col, stroke_width=0.25))
    # cable tray bracket (south side)
    ct = rk["cable_tray"]
    ys = rk["y0"] - 0.2
    g.add(S.rect(ys - ct["bracket"], ct["el"] - 0.12, ys, ct["el"], fill="#aaa", stroke=col, stroke_width=0.2))
    g.add(S.rect(ys - ct["bracket"] + 0.1, ct["el"], ys - 0.15, ct["el"] + 0.12, fill="#f0c000", stroke=col, stroke_width=0.2))
    g.add(S.rect(ys - ct["bracket"], ct["el"] + 0.45, ys, ct["el"] + 0.57, fill="#aaa", stroke=col, stroke_width=0.2))
    g.add(S.rect(ys - ct["bracket"] + 0.1, ct["el"] + 0.57, ys - 0.15, ct["el"] + 0.69, fill="#30a0e0", stroke=col, stroke_width=0.2))


def section_sheet(L, docno, title2, xband, xplane, yr, extra_notes, nozzle_tags, outdir, name):
    sh = Sheet("A1", "SECTION / ELEVATION", title2, docno, scale="1:200", discipline="PLANT LAYOUT",
               notes=["Elevations in metres; grade (HPP) EL 100.000. Section looking WEST (north to the right).",
                      "Items in front of / at the section plane solid; items beyond shown dashed grey.",
                      "Nozzle elevations approximate (FEED) - from tray spacing 0.61 / 0.76 m per sizing.",
                      "Rack tiers TOS EL 106.0 / 108.5 / 111.0; air coolers on structure above tier 3.",
                      *extra_notes])
    k = 5.0  # 1:200
    S = Sec(sh, k, 35.0, 470.0, yr[0])
    # frame of section
    S.grade(yr[0], yr[1])
    # elevation scale on left
    for z in range(100, 156, 5):
        sx, sy = S.P(yr[0], z)
        S.g.add(S.d.line((sx - 4, sy), (sx - 2, sy), stroke="black", stroke_width=0.2))
        sh.text(f"{z}.0", sx - 5, sy + 0.7, size=1.8, anchor="end", color="#555")
    S.g.add(S.d.line(S.P(yr[0], 100), S.P(yr[0], 155), stroke="black", stroke_width=0.2))
    # N grid labels at bottom
    for y in range(int(math.ceil(yr[0] / 10) * 10), int(yr[1]) + 1, 10):
        sx, sy = S.P(y, GRADE)
        S.g.add(S.d.line((sx, sy + 3), (sx, sy + 6), stroke="#555", stroke_width=0.2))
        sh.text(f"N{y}", sx, sy + 9, size=2.0, anchor="middle", color="#555")
    sh.text(f"SECTION AT E {xplane:.1f} (LOOKING WEST)  -  SCALE 1:200", S.P(yr[0], 100)[0], 30, size=4.0, bold=True)
    sh.text(f"Equipment shown: E {xband[0]:.0f} to section plane E {xplane:.0f}; faint = more than {xband[2]:.0f} m beyond plane", S.P(yr[0], 100)[0], 36, size=2.6)
    sh.text("SOUTH", S.P(yr[0], 100)[0], S.P(yr[0], 100)[1] + 16, size=3.0, bold=True)
    sh.text("NORTH", S.P(yr[1], 100)[0], S.P(yr[1], 100)[1] + 16, size=3.0, bold=True, anchor="end")

    sel = [i for i in L.items if i["bbox"][2] >= xband[0] and i["bbox"][0] <= xplane + 0.5]
    # painter: far (small x) first; faint if centre farther than 6 m from plane
    sel.sort(key=lambda i: (i["x"]))
    done_pumps = set()
    for it in sel:
        if it["type"] == "Air cooler":
            continue
        faint = (xplane - it["x"]) > xband[2] and it["type"] not in ("Fired heater",)
        lab = True
        if it["type"] == "Pump":
            key = round(it["y"], 1)
            lab = key not in done_pumps
            done_pumps.add(key)
        if it["type"] == "Shell & tube" and it["z_base"] > 110:
            lab = it["tag"] in ("E-202",)
        draw_item(S, it, faint=faint, label=lab and not (faint and it["type"] in ("Pump",)))
    draw_rack(S, L)
    acs = [i for i in sel if i["type"] == "Air cooler"]
    if acs:
        a = min(acs, key=lambda i: abs(i["x"] - xplane))
        draw_item(S, a, faint=False, label=False)
        tx, ty = S.P(75, a["z_base"] + 1.2)
        sh.text("AIR COOLERS " + ", ".join(sorted({i["parent_tag"] for i in acs})), tx, ty - 1.5, size=2.1,
                anchor="middle", bold=True)
    # rack labels
    for t in L.rack["tiers"]:
        S.el(L.rack["y1"] + 0.3, t["el"], f"TOS EL {t['el']:.3f}", size=2.1)
    S.el(L.rack["y1"] + 0.3, L.rack["air_cooler_deck"]["el"], f"AC EL {L.rack['air_cooler_deck']['el']:.3f}", size=2.1)
    tx, ty = S.P(75, GRADE)
    sh.text("PR-100", tx, ty + 5, size=2.4, anchor="middle", bold=True)
    S.hdim(L.rack["y0"], L.rack["y1"], GRADE, "10.0 m", off=12)

    # nozzle elevations of columns in plane
    for tag in nozzle_tags:
        it = L.by_tag[tag]
        y = it["y"]
        D = it["D"]
        for nm, (nx, ny, nz) in sorted(it["nozzles"].items(), key=lambda kv: -kv[1][2]):
            if nm in ("bottoms", "overhead"):
                continue
            side = -1 if ny < y - 0.05 else 1
            Dl = abs(ny - y) * 2 if abs(ny - y) > 0.3 else D
            sx, sy = S.P(y + side * Dl / 2, nz)
            S.g.add(S.d.line((sx, sy), (sx + side * 2.0, sy), stroke="#b00000", stroke_width=0.35))
            S.g.add(S.d.circle((sx + side * 2.0, sy), 0.5, fill="#b00000", stroke="none"))
        # platforms
        for p in L.structs["column_platforms"]:
            if p["tag"] != tag:
                continue
            for sgn in (-1, 1):
                a = S.P(y + sgn * p["r_in"], p["el"])
                b = S.P(y + sgn * p["r_out"], p["el"])
                S.g.add(S.d.line(a, b, stroke="black", stroke_width=0.5))
                # handrail
                S.g.add(S.d.line(S.P(y + sgn * p["r_out"], p["el"]), S.P(y + sgn * p["r_out"], p["el"] + 1.1),
                                 stroke="black", stroke_width=0.2))
        S.el(y + D / 2 + 1.5, it["top_tl"], f"TOP T/L EL {it['top_tl']:.3f}", size=1.9)
        S.el(y + D / 2 + 1.5, it["bottom_tl"], f"BTM T/L EL {it['bottom_tl']:.3f}", size=1.9)
        # ladder
        ly = y - it["D"] / 2 - 0.8
        S.g.add(S.d.line(S.P(ly, GRADE), S.P(ly, it["top_tl"]), stroke="black", stroke_width=0.2, stroke_dasharray="0.8,0.5"))
    return sh, S


def nozzle_table(sh, L, tags, x, y, title="COLUMN NOZZLE ELEVATIONS (FEED, approx.)"):
    sh.text(title, x, y, size=2.8, bold=True)
    yy = y + 5
    for tag in tags:
        it = L.by_tag[tag]
        sh.text(tag, x, yy, size=2.2, bold=True)
        yy += 3.4
        rows = sorted(it["nozzles"].items(), key=lambda kv: -kv[1][2])
        for i, (nm, (nx, ny, nz)) in enumerate(rows):
            c = i % 2
            r = i // 2
            sh.text(f"{nm}", x + c * 82, yy + r * 3.0, size=2.1)
            sh.text(f"EL {nz:.2f}", x + c * 82 + 58, yy + r * 3.0, size=2.1)
        yy += (len(rows) + 1) // 2 * 3.0 + 3
    return yy


def key_plan(sh, L, x, y, xplane, w=150):
    d, g = sh.dwg, sh.g
    k = w / 230.0
    h = 150 * k
    g.add(d.rect((x, y), (w, h), fill="none", stroke="black", stroke_width=0.3))
    g.add(d.rect((x, y + (150 - 80) * k), (216 * k, 10 * k), fill="#ccc", stroke="none"))
    for it in L.items:
        x0, y0, x1, y1 = it["bbox"]
        g.add(d.rect((x + x0 * k, y + (150 - y1) * k), (max((x1 - x0) * k, 0.3), max((y1 - y0) * k, 0.3)),
                     fill="#666", stroke="none"))
    sx = x + xplane * k
    g.add(d.line((sx, y - 4), (sx, y + h + 4), stroke="#c00000", stroke_width=0.5, stroke_dasharray="4,1,1,1"))
    for yy, lab in ((y - 5, "A"), (y + h + 8, "A")):
        sh.text(lab, sx, yy, size=3.0, anchor="middle", bold=True, color="#c00000")
    g.add(d.polygon([(sx, y - 3), (sx - 3, y - 1.5), (sx, y)], fill="#c00000"))
    sh.text("KEY PLAN (NTS) - SECTION PLANE, LOOKING WEST", x, y + h + 13, size=2.4, bold=True)


# ------------------------------------------------------------------------------------------
def elv1(L, outdir):
    sh, S = section_sheet(L, "CFU-000-PL-ELV-001", "SECTION N-S THROUGH H-101 / PIPE RACK / C-101 (AREA 100)",
                          (70, 121, 7.5), 96.0, (14, 136),
                          ["C-101 skirt height set by P-112 / P-108 NPSH (hot bottoms, 350 C).",
                           "Side strippers C-102/3/4 (east of plane, not shown) fed by gravity from C-101 draws."],
                          ["C-101"], outdir, "elv1")
    c = L.by_tag["C-101"]
    h = L.by_tag["H-101"]
    rk = L.rack
    S.hdim(h["bbox"][3], rk["y0"], 104.0, f"{rk['y0'] - h['bbox'][3]:.1f} m (min 15)")
    S.hdim(rk["y1"], c["y"] - c["D"] / 2, 103.0, f"{c['y'] - c['D'] / 2 - rk['y1']:.1f} m")
    tel = c["tray_el"]
    tr = L.R["atm"]["tray"]
    for nm, t in [("KERO DRAW T10", tr["KERO"]), ("DIESEL DRAW T22", tr["DIESEL"]), ("AGO DRAW T32", tr["AGO"]),
                  ("TRAY 1", 1), ("TRAY 41", 41)]:
        S.el(c["y"] - c["D"] / 2 - 3.5, tel[str(t)], f"{nm} EL {tel[str(t)]:.2f}", right=False, size=2.1)
    f = c["nozzles"]["feed"]
    S.el(c["y"] - c["D"] / 2 - 3.5, f[2], f"FEED (TRANSFER LINE) EL {f[2]:.2f}", right=False, size=1.8, color="#b00000")
    S.el(c["y"], c["top_el"], f"OVHD EL {c['top_el']:.3f}", size=1.9)
    yy = nozzle_table(sh, L, ["C-101"], 651, 40)
    nozzle_table(sh, L, ["C-102", "C-103", "C-104"], 651, yy + 2, title="SIDE STRIPPER NOZZLES")
    key_plan(sh, L, 651, 290, 96.0, w=165)
    return sh.save(outdir / "CFU-000-PL-ELV-001_Section-C101-H101")


def elv2(L, outdir):
    sh, S = section_sheet(L, "CFU-000-PL-ELV-002", "SECTION N-S THROUGH H-201 / PIPE RACK / C-201 (AREA 200)",
                          (158, 212, 40.0), 204.0, (14, 136),
                          ["C-201 bottom T/L EL 110.0 for P-204 NPSH (VR 366 C, quench).",
                           "Ejector condensers on ST-201 >= 10.4 m above hotwell D-201 (barometric legs)."],
                          ["C-201"], outdir, "elv2")
    c = L.by_tag["C-201"]
    h = L.by_tag["H-201"]
    rk = L.rack
    S.hdim(h["bbox"][3], rk["y0"], 104.0, f"{rk['y0'] - h['bbox'][3]:.1f} m (min 15)")
    S.hdim(rk["y1"], c["y"] - c["D"] / 2, 103.0, f"{c['y'] - c['D'] / 2 - rk['y1']:.1f} m")
    es = L.ejector_structure
    # ejector structure outline (beyond)
    for z in es["levels"] + [es["top"]]:
        S.g.add(S.rect(es["y0"], z - 0.3, es["y1"], z, fill="#ddd", stroke="#333", stroke_width=0.25))
    for y in (es["y0"], es["y1"]):
        S.g.add(S.rect(y - 0.15, GRADE, y + 0.15, es["top"], fill="#ddd", stroke="#333", stroke_width=0.25))
        S.g.add(S.d.line(S.P(y, GRADE), S.P((es["y0"] + es["y1"]) / 2, es["levels"][0] - 0.3), stroke="#333", stroke_width=0.2))
    tx, ty = S.P((es["y0"] + es["y1"]) / 2, es["top"])
    S.sh.text("ST-201 EJECTOR STRUCTURE", tx, ty - 3, size=2.2, anchor="middle", color="#333", bold=True)
    for z in es["levels"]:
        S.el(es["y1"] + 0.3, z, f"EL {z:.3f}", size=2.0, color="#555")
    S.vdim(L.by_tag["D-201"]["y"] + 2.5, L.by_tag["D-201"]["top_el"], L.by_tag["E-204"]["z_base"],
           f"{L.by_tag['E-204']['z_base'] - L.by_tag['D-201']['top_el']:.1f} m BAROMETRIC LEG (min 10.4)", off=0)
    z = c["zones"]
    for nm, el in [("LVGO DRAW", c["nozzles"]["lvgo_draw"][2]), ("HVGO DRAW", c["nozzles"]["hvgo_draw"][2]),
                   ("SLOP WAX DRAW", c["nozzles"]["slop_wax_draw"][2])]:
        S.el(c["y"] - c["D"] / 2 - 3.5, el, f"{nm} EL {el:.2f}", right=False, size=2.1)
    f = c["nozzles"]["feed"]
    S.el(c["y"] - c["D"] / 2 - 3.5, f[2], f"FEED (VAPOUR HORN) EL {f[2]:.2f}", right=False, size=1.8, color="#b00000")
    S.el(c["y"], c["top_el"], f"OVHD EL {c['top_el']:.3f}", size=1.9)
    yy = nozzle_table(sh, L, ["C-201"], 651, 40)
    sh.text("C-201 ZONES (EL from / to)", 651, yy + 2, size=2.6, bold=True)
    for i, (k_, (a, b)) in enumerate(sorted(z.items(), key=lambda kv: -kv[1][1])):
        sh.text(f"{k_}", 651, yy + 7 + i * 3.0, size=1.9)
        sh.text(f"{a:.2f} - {b:.2f}", 720, yy + 7 + i * 3.0, size=1.9)
    key_plan(sh, L, 651, 290, 204.0, w=165)
    return sh.save(outdir / "CFU-000-PL-ELV-002_Section-C201-H201")


def elv3(L, outdir):
    E = {e["tag"]: e for e in json.loads((ROOT / "data" / "equipment.json").read_text())}
    sh = Sheet("A1", "PIPE RACK TYPICAL SECTION", "MAIN PIPE RACK PR-100 - TIER ALLOCATION", "CFU-000-PL-ELV-003",
               scale="1:50", discipline="PLANT LAYOUT",
               notes=["Typical bent; bents at 6.0 m centres (12 m portal over RD-W). Steel HE400B columns, HE300A beams.",
                      "Line sizes indicative: from pump rated flow at 2.0 m/s (liquid); final sizes per line list.",
                      "Hot lines (> 260 C) on tier 1 with expansion loops on tier 3 level; flare header",
                      "   on tier 3 free-draining to D-104 (1:500). CWS/CWR heavy lines tier 1 outer positions.",
                      "Cable trays (EL / IC) on south cantilever brackets, segregated from hot lines; fireproofed",
                      "   rack steel to EL 111.0 below air coolers per API 2218 (to be confirmed by fire study).",
                      "Pump CL 3.5 m (north) / 4.5 m (south) off rack edge; drivers accessible from under-rack aisle (ER-1).",
                      "Headroom under tier 1 = EL 106.0 - beam - road crown >= 5.0 m (no mobile crane under rack)."])
    k = 20.0
    S = Sec(sh, k, 40.0, 470.0, 62.0)
    S.grade(62.0, 88.0)
    rk = L.rack
    draw_rack(S, L, detail=True)
    ac = L.by_tag["A-104"]
    draw_item(S, ac, label=False)
    tx, ty = S.P(75, ac["z_base"] + 1.2)
    sh.text("AIR COOLER BAY (TYP. A-104, 6 m x 12 m, FORCED DRAFT)", tx, ty - 3, size=3.0, anchor="middle", bold=True)
    # pumps either side
    pn = L.by_tag["P-110A"]
    ps = L.by_tag["P-102A"]
    for p in (pn, ps):
        draw_item(S, p, label=False)
        tx, ty = S.P(p["y"], p["top_el"])
        sh.text(("TYP. PUMP ROW NORTH (" + pn["tag"][:-1] + "A/B)") if p is pn else "TYP. PUMP ROW SOUTH (P-102A/B)",
                tx, ty - 2, size=2.4, anchor="middle")
    # lines per tier
    pumps = {e["tag"]: e for e in E.values() if e["type"] == "Pump"}

    def ln(tag, svc, cls, hot=False):
        n = nps_for(pumps[tag]["flow_m3h"])
        return (n, svc, cls, hot)
    t1 = [("CWS", 14, "U1"), ln("P-102A/B", "Desalted crude to hot train", "B1"), ln("P-112A/B", "AR to H-201", "B2", True),
          ln("P-107A/B", "MPA", "B2", True), ln("P-108A/B", "BPA", "B2", True), ln("P-202A/B", "HVGO PA/prod.", "B2", True),
          ln("P-204A/B", "VR (to preheat)", "B2", True), ln("P-110A/B", "Diesel product", "B2", True), ("CWR", 14, "U1")]
    t1 = [(x[1], x[0], x[2]) if isinstance(x[1], int) else (x[0], x[1], x[2]) for x in t1]
    t2 = [ln("P-101A/B", "Crude charge", "B1"), ln("P-106A/B", "TPA", "B1"), ln("P-201A/B", "LVGO PA/prod.", "B1"),
          ln("P-104A/B", "Unstab. naphtha", "C1"), ln("P-109A/B", "Kerosene", "B1"), ln("P-116A/B", "Light naphtha", "B1"),
          ln("P-117A/B", "Heavy naphtha", "B1"), ln("P-115A/B", "LPG", "C1"), ln("P-111A/B", "AGO", "B2"),
          ln("P-105A/B", "Sour water", "A2"), ln("P-114A/B", "Wash water", "A2")]
    t2 = [(x[0], x[1], x[2]) for x in t2]
    t3 = [(24, "Flare header FL", "A1"), (12, "HP steam HS", "S2"), (14, "MP steam MS", "S1"), (16, "LP steam LS", "S1"),
          (6, "Condensate CD", "S1"), (8, "Fuel gas FG", "A1"), (4, "BFW", "B1"), (3, "Inst. air IA", "U2"),
          (2, "Nitrogen N", "U2"), (3, "Utility water", "U1")]
    alloc = [(rk["tiers"][0]["el"], t1), (rk["tiers"][1]["el"], t2), (rk["tiers"][2]["el"], t3)]
    for el, lines in alloc:
        # positions across 10 m (y 70.4 .. 79.6)
        ods = [(n * 0.0254 + (0.15 if n >= 6 else 0.08)) for n, _, _ in lines]
        tot = sum(ods)
        gap = max(0.1, (9.2 - tot) / max(1, len(lines) - 1))
        y = 70.4
        for (n, svc, cls), od in zip(lines, ods):
            cy = y + od / 2
            sx, sy = S.P(cy, el + od / 2)
            S.g.add(S.d.circle((sx, sy), od / 2 * k, fill="#fff3e0" if cls.startswith("B2") else "white",
                               stroke="black", stroke_width=0.35))
            S.g.add(S.d.circle((sx, sy), n * 0.0254 / 2 * k, fill="none", stroke="black", stroke_width=0.2))
            t = sh.text(f'{n}" {svc} ({cls})', sx, sy - od / 2 * k - 1.2, size=1.9)
            t.rotate(-90, center=(sx, sy - od / 2 * k - 1.2))
            y += od + gap
    # labels of tiers & allocation box
    for t in rk["tiers"]:
        S.el(rk["y1"] + 0.5, t["el"], f"TOS EL {t['el']:.3f}  TIER {t['level']}", size=2.2)
    S.el(rk["y1"] + 0.5, rk["air_cooler_deck"]["el"], f"AC BUNDLE EL {rk['air_cooler_deck']['el']:.3f}", size=2.2)
    S.el(rk["y1"] + 0.5, rk["air_cooler_deck"]["fan_deck_el"], f"FAN DECK EL {rk['air_cooler_deck']['fan_deck_el']:.3f}", size=2.0)
    ct = rk["cable_tray"]
    S.el(rk["y0"] - 1.6, ct["el"], f"CABLE TRAY EL {ct['el']:.3f} (POWER)", right=False, size=2.0)
    S.el(rk["y0"] - 1.6, ct["el"] + 0.57, f"EL {ct['el'] + 0.57:.3f} (INSTRUMENT)", right=False, size=2.0)
    S.hdim(rk["y0"], rk["y1"], GRADE, "10.0 m (RACK WIDTH)", off=14)
    S.hdim(rk["y1"], pn["y"], GRADE, f"{pn['y'] - rk['y1']:.1f} m", off=8)
    S.hdim(ps["y"], rk["y0"], GRADE, f"{rk['y0'] - ps['y']:.1f} m", off=8)
    S.hdim(ac["bbox"][1], ac["bbox"][3], 116.0, "12.0 m AIR-COOLER BUNDLE", off=0)
    S.vdim(rk["y0"] + 1.8, GRADE, rk["tiers"][0]["el"] - 0.5, f"{rk['tiers'][0]['el'] - 0.5 - GRADE:.1f} m CLEAR", off=0)
    S.vdim(rk["y1"] - 1.0, rk["tiers"][0]["el"], rk["tiers"][1]["el"], "2.5 m")
    S.vdim(rk["y1"] - 1.0, rk["tiers"][1]["el"], rk["tiers"][2]["el"], "2.5 m")
    S.el(62.5, GRADE, "GRADE EL 100.000", size=2.2)
    for z in range(100, 118):
        sx, sy = S.P(62.0, z)
        S.g.add(S.d.line((sx - 3, sy), (sx, sy), stroke="black", stroke_width=0.2))
        sh.text(f"{z}", sx - 4, sy + 0.7, size=1.8, anchor="end", color="#555")
    sh.text("TYPICAL BENT CROSS-SECTION (LOOKING WEST ALONG RACK)  -  SCALE 1:50", 40, 30, size=4.0, bold=True)
    sh.text("SOUTH", 40, 495, size=3.0, bold=True)
    sh.text("NORTH", 40 + 26 * k, 495, size=3.0, bold=True, anchor="end")
    # allocation table
    x0, y0 = 600, 40
    sh.text("TIER ALLOCATION", x0, y0, size=3.0, bold=True)
    rows = [("Tier", "TOS EL", "Allocation")] + [(str(t["level"]), f"{t['el']:.3f}", t["service"]) for t in rk["tiers"]] + [
        ("Brkt", f"{ct['el']:.3f}", "Cable trays EL power + IC (south brackets)"),
        ("AC", f"{rk['air_cooler_deck']['el']:.3f}", "Air-cooler bundles A-101..A-202 (10 bays)")]
    for i, r in enumerate(rows):
        yy = y0 + 6 + i * 6
        for j, (v, cx) in enumerate(zip(r, (0, 12, 32))):
            words = v.split(", ") if j == 2 else [v]
            txt = v if len(v) < 60 else v[:58] + "."
            sh.text(txt, x0 + cx, yy, size=2.0, bold=i == 0)
    sh.text("Utilities on tier 3 include steam headers with expansion loops;", x0, y0 + 50, size=1.9)
    sh.text("loops for tier-1 hot lines raised to tier 3 level at loop bays.", x0, y0 + 53.5, size=1.9)
    return sh.save(outdir / "CFU-000-PL-ELV-003_Pipe-Rack-Section")


def build(L, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    return [elv1(L, outdir), elv2(L, outdir), elv3(L, outdir)]
