"""Plot plan CFU-000-PL-PLT-001 (A1, 1:500) generated from data/layout.json model."""
from __future__ import annotations

import math
from pathlib import Path

from ..drawing.sheet import Sheet

SC = 2.0                 # mm per m (1:500)
X0, Y0 = 36.0, 362.0      # sheet position of plot origin (x=0, y=0)

COL = dict(Column="#1f4e9c", Drum="#2a7f62", Desalter="#2a7f62", Pump="#7a3d9c", **{"Shell & tube": "#b5651d"},
           **{"Air cooler": "#2a8fbd", "Fired heater": "#c0392b", "Air preheater": "#c0392b", "Fan": "#c0392b"},
           Ejector="#555555", Package="#8a6d00")


def P(x, y):
    return (X0 + SC * x, Y0 - SC * y)


def build(L, outdir: Path):
    sh = Sheet("A1", "PLOT PLAN", "CRUDE & VACUUM DISTILLATION UNIT - OVERALL UNIT PLOT", "CFU-000-PL-PLT-001",
               scale="1:500", discipline="PLANT LAYOUT", notes=[
                   "Coordinates in metres from unit plot SW corner (E = x, N = y). Grade EL 100.000.",
                   "Equipment positions = centrelines; outlines to equipment list CFU-000-ME-LST-001.",
                   "Air coolers (dashed) on structure above rack tier 3, bundles at EL 115.0.",
                   "Spacing per CCPS 'Guidelines for Facility Siting & Layout' / GAP 2.5.2 typical values;",
                   "   distances edge-to-edge of plan bounding boxes (conservative), see table.",
                   "Final spacing subject to HAC, fire & explosion and API RP 752 siting study.",
                   "Fired heaters south of rack, upwind of HC equipment (prevailing wind SSE).",
                   "Rack bents at 6 m; 12 m portal span over west perimeter road RD-W.",
                   "SW perimeter road deviated north of SS-100 / FAR-100 (frame conflict, see report).",
               ])
    d, g = sh.dwg, sh.g
    defs = d.defs
    pat = d.pattern(id="hatch", size=(2.0, 2.0), patternUnits="userSpaceOnUse", patternTransform="rotate(45)")
    pat.add(d.line((0, 0), (0, 2.0), stroke="#999", stroke_width=0.25))
    defs.add(pat)
    pat2 = d.pattern(id="hatchb", size=(1.4, 1.4), patternUnits="userSpaceOnUse", patternTransform="rotate(-45)")
    pat2.add(d.line((0, 0), (0, 1.4), stroke="#555", stroke_width=0.25))
    defs.add(pat2)
    pat3 = d.pattern(id="dots", size=(2.5, 2.5), patternUnits="userSpaceOnUse")
    pat3.add(d.circle((1.25, 1.25), 0.25, fill="#999", stroke="none"))
    defs.add(pat3)

    S = L.structs

    def rect(x0, y0, x1, y1, **kw):
        a, b = P(x0, y1)
        return d.rect((a, b), (SC * (x1 - x0), SC * (y1 - y0)), **kw)

    # ---- grid -----------------------------------------------------------------------
    gg = d.g(stroke="#c8c8c8", stroke_width=0.12)
    for xx in range(0, 231, 10):
        gg.add(d.line(P(xx, -4), P(xx, 154)))
        sh.text(f"E{xx}", *P(xx, 156.5), size=2.0, anchor="middle", color="#555")
        sh.text(f"E{xx}", *P(xx, -8.0), size=2.0, anchor="middle", color="#555")
    for yy in range(0, 151, 10):
        gg.add(d.line(P(-4, yy), P(234, yy)))
        sh.text(f"N{yy}", *(P(-5.5, yy)[0], P(-5.5, yy)[1] + 0.7), size=2.0, anchor="end", color="#555")
        sh.text(f"N{yy}", *(P(235.5, yy)[0], P(235.5, yy)[1] + 0.7), size=2.0, anchor="start", color="#555")
    g.add(gg)

    # ---- plot limit / roads ----------------------------------------------------------
    g.add(rect(0, 0, 230, 150, fill="none", stroke="black", stroke_width=0.7, stroke_dasharray="6,1.5,1,1.5"))
    sh.text("UNIT PLOT LIMIT (230 x 150 m)", *P(115, 151.2), size=2.2, anchor="middle", bold=True)
    for r in S["roads"]:
        g.add(rect(r["x0"], r["y0"], r["x1"], r["y1"], fill="#e3e3e3", stroke="#888", stroke_width=0.2))
    for r, (lx, ly, rot) in zip(S["roads"], [(6, 60, -90), (180, 144, 0), (224, 50, -90), (160, 6, 0), (30, 25, 0),
                                              (70, 13, -90), (140, 30, -90)]):
        sh.text(f"{r['id']}  6 m ROAD", *P(lx, ly), size=1.8, anchor="middle", color="#444", rotate=rot)

    # ---- areas ------------------------------------------------------------------------
    for a in S["areas"]:
        k = a["kind"]
        if k.startswith("crane"):
            kw = dict(fill="url(#hatch)", stroke="#d08000", stroke_width=0.35, stroke_dasharray="2,1")
            col = "#a05a00"
        elif k.startswith("bundle"):
            kw = dict(fill="#fff6d8", stroke="#b5651d", stroke_width=0.3, stroke_dasharray="2,1")
            col = "#8a4a10"
        else:
            kw = dict(fill="url(#dots)", stroke="#777", stroke_width=0.3, stroke_dasharray="1,1")
            col = "#555"
        g.add(rect(a["x0"], a["y0"], a["x1"], a["y1"], **kw))
        cx, cy = (a["x0"] + a["x1"]) / 2, a["y1"] - 2.2
        lab = {"crane area": "CRANE AREA", "laydown": "LAYDOWN", "bundle pull / maintenance aisle": "BUNDLE PULL AISLE",
               "future / construction laydown": "CONSTRUCTION LAYDOWN / FUTURE"}[k]
        if a["id"] == "LD-4":
            sh.text(f"{a['id']} {lab}", *P(cx, (a["y0"] + a["y1"]) / 2), size=1.6, anchor="middle", color=col, rotate=-90)
        elif a["id"] == "BP-1":
            sh.text(f"{a['id']} {lab} (9.5 m clear, bundles 7.5 m)  ->  RD-W", *P(cx, a["y0"] + 3.4), size=1.7,
                    anchor="middle", color=col, bold=True)
        else:
            sh.text(f"{a['id']} {lab}", *P(cx, cy), size=1.7, anchor="middle", color=col, bold=True)

    # ---- buildings ---------------------------------------------------------------------
    for b in S["buildings"]:
        g.add(rect(b["x0"], b["y0"], b["x1"], b["y1"], fill="url(#hatchb)", stroke="black", stroke_width=0.5))
        cx, cy = (b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2
        g.add(rect(cx - 9, cy - 2.6, cx + 9, cy + 3.2, fill="white", stroke="none"))
        sh.text(b["id"], *P(cx, cy + 0.6), size=2.3, anchor="middle", bold=True)
        sh.text(b["name"].split("/")[0].upper(), *P(cx, cy - 1.7), size=1.4, anchor="middle")

    # ---- pipe rack ----------------------------------------------------------------------
    rk = L.rack
    g.add(rect(rk["x0"], rk["y0"], rk["x1"], rk["y1"], fill="#f4f4f4", stroke="black", stroke_width=0.45))
    g.add(d.line(P(rk["x0"] - 2, 75), P(rk["x1"] + 3, 75), stroke="black", stroke_width=0.2, stroke_dasharray="5,1,1,1"))
    for bx in rk["bents_x"]:
        for by in (rk["y0"], rk["y1"]):
            g.add(rect(bx - 0.3, by - 0.3, bx + 0.3, by + 0.3, fill="black", stroke="none"))
        g.add(d.line(P(bx, rk["y0"]), P(bx, rk["y1"]), stroke="#666", stroke_width=0.15))
    sh.text("MAIN PIPE RACK PR-100  (10 m wide, bents @ 6 m, TOS EL 106.0 / 108.5 / 111.0)", *P(28, 72.4),
            size=1.8, anchor="start", bold=True)
    sh.text("TIE-IN TO OSBL RACK", *P(1, 82.5), size=1.6, anchor="start")
    g.add(d.polygon([P(-3.5, 75), P(-0.5, 76.5), P(-0.5, 73.5)], fill="black", stroke="none"))

    # ---- ejector structure ---------------------------------------------------------------
    es = L.ejector_structure
    g.add(rect(es["x0"], es["y0"], es["x1"], es["y1"], fill="none", stroke="#555", stroke_width=0.4, stroke_dasharray="3,1"))
    g.add(d.line(P(es["x0"], es["y0"]), P(es["x1"], es["y1"]), stroke="#999", stroke_width=0.15))
    g.add(d.line(P(es["x0"], es["y1"]), P(es["x1"], es["y0"]), stroke="#999", stroke_width=0.15))
    sh.text("ST-201 EJECTOR STRUCTURE", *P(es["x0"], es["y0"] - 2.2), size=1.5, bold=True, color="#555")
    sh.text("J-201/202/203, E-202/203/204 (EL 112-124)", *P(es["x0"], es["y0"] - 4.0), size=1.3, color="#555")

    # ---- equipment ---------------------------------------------------------------------
    eqs = sorted(L.items, key=lambda i: (i["type"] == "Air cooler", i["z_base"]))
    for it in eqs:
        draw_item(sh, d, g, it)

    # ---- escape routes -----------------------------------------------------------------
    for er in S["escape_routes"]:
        pts = [P(*p) for p in er["pts"]]
        g.add(d.polyline(pts, stroke="#1a9a3a", stroke_width=0.5, stroke_dasharray="2.5,1.2", fill="none"))
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        a = math.atan2(y2 - y1, x2 - x1)
        Lh = 2.4
        g.add(d.polygon([(x2, y2), (x2 - Lh * math.cos(a - 0.4), y2 - Lh * math.sin(a - 0.4)),
                         (x2 - Lh * math.cos(a + 0.4), y2 - Lh * math.sin(a + 0.4))], fill="#1a9a3a", stroke="none"))
    for er_id, (x, y, rot) in {"ER-3": (47.8, 128, -90), "ER-5": (123.5, 128, -90), "ER-6": (155.8, 128, -90),
                               "ER-8": (70.8, 50, -90), "ER-10": (190.8, 40, -90), "ER-7": (214.8, 128, -90)}.items():
        sh.text(f"{er_id} ESCAPE", *P(x, y), size=1.4, color="#1a9a3a", rotate=rot, anchor="middle")
    sh.text("ER-1 ESCAPE / ACCESS UNDER RACK", *P(150, 76.0), size=1.4, color="#1a9a3a", anchor="middle")

    # assembly points
    for (x, y, t) in [(-1.5, 40, "AP-1 ASSEMBLY POINT (OSBL W)"), (231.5, 120, "AP-2 (OSBL E)")]:
        sx, sy = P(x, y)
        g.add(d.circle((sx, sy), 2.2, fill="#1a9a3a", stroke="none"))
        sh.text("AP", sx, sy + 0.7, size=1.8, anchor="middle", color="white", bold=True)
        sh.text(t, sx + (-3 if x < 0 else 3), sy + 4.6, size=1.5, anchor="end" if x < 0 else "start", color="#1a9a3a")

    # hydrants / monitors along roads (indicative, 50 m max)
    for (x, y) in [(10.5, 40), (10.5, 90), (10.5, 130), (60, 139.5), (110, 139.5), (160, 139.5), (210, 139.5),
                   (219.5, 110), (219.5, 60), (219.5, 20), (180, 10.5), (120, 10.5), (80, 29.5), (40, 29.5),
                   (144.5, 30), (135.5, 55)]:
        sx, sy = P(x, y)
        g.add(d.circle((sx, sy), 1.1, fill="#d62020", stroke="none"))
        g.add(d.line((sx - 1.6, sy), (sx + 1.6, sy), stroke="#d62020", stroke_width=0.35))

    # ---- spacing dimension callouts -------------------------------------------------------
    want = {"Fired heater to HC process equipment": (0, 3), "Fired heater to LPG / light-ends equipment": (2, 0),
            "Fired heater to main pipe rack": (0, 0),
            "Fired heater to fuel-gas KO drum": (0, 3), "Substation / FAR to HC equipment": (0, 0),
            "Substation / FAR to fired heater": (0, 0)}
    for c in L.checks:
        if c["rule"] in want and c.get("p"):
            dim(sh, d, g, c["p"], c["q"], f"{c['actual_m']:.1f} m (min {c['required_m']:.0f})", want[c["rule"]])
    # extra callouts computed from the model
    from .model import rect_dist
    B = {i["tag"]: i["bbox"] for i in L.items}
    rkb = [rk["x0"], rk["y0"], rk["x1"], rk["y1"]]
    for a, b, req, off in [("H-201", rkb, 15, (0, 0)), ("D-101A", "H-101", 15, (0, -2)), ("H-201", "C-201", 15, (5, 0))]:
        ba = B[a]
        bb = B[b] if isinstance(b, str) else b
        dd, p, q = rect_dist(ba, bb)
        dim(sh, d, g, p, q, f"{dd:.1f} m (min {req})", off)
    for a, b in [("P-103A", "D-102"), ("P-205A", "D-201")]:
        dd, p, q = rect_dist(B[a], B[b])
        dim(sh, d, g, p, q, f"{dd:.1f} m (min 3)", (0, 0), small=True)

    # ---- coordinates on key items ----------------------------------------------------
    for t in ("C-101", "C-201", "H-101", "H-201", "C-105", "C-106", "D-101A", "D-101B", "D-102"):
        it = L.by_tag[t]
        x, y = it["x"], it["y"]
        off = {"C-101": (-5, 8.5), "C-201": (-5, 7.5), "H-101": (-13, -9.3), "H-201": (-7, -8.0), "C-105": (-3.5, -4.5),
               "C-106": (-3.5, -4.5), "D-101A": (-16, 3.0), "D-101B": (-16, -4.0), "D-102": (-6, -1)}[t]
        sh.text(f"E {x:.1f}  N {y:.1f}", *P(x + off[0], y + off[1]), size=1.4, color="#333", italic=True)

    # ---- right-hand panel -------------------------------------------------------------
    north_arrow(sh, d, 545, 50)
    wind_rose(sh, d, 612, 50)
    scale_bar(sh, d, 665, 40)
    legend(sh, d, 520, 92)
    spacing_table(sh, d, L, 520, 146)
    schedule(sh, d, L, 15, 392)
    area_key(sh, d, 520, 252)

    outdir.mkdir(parents=True, exist_ok=True)
    return sh.save(outdir / "CFU-000-PL-PLT-001_Plot-Plan")


# ------------------------------------------------------------------------------------------
def draw_item(sh, d, g, it):
    t = it["type"]
    col = COL.get(t, "#333")
    x, y = it["x"], it["y"]
    sx, sy = P(x, y)
    tag = it["tag"]
    if it["shape"] == "vcyl":
        r = it["L"] / 2 * SC
        g.add(d.circle((sx, sy), r, fill="#eef2fb" if t == "Column" else "#eef7f2", stroke=col, stroke_width=0.45))
        if r > 4:
            g.add(d.circle((sx, sy), r + 1.3 * SC, fill="none", stroke=col, stroke_width=0.18, stroke_dasharray="1,0.8"))
        g.add(d.line((sx - r - 1, sy), (sx + r + 1, sy), stroke=col, stroke_width=0.12, stroke_dasharray="2,0.6,0.4,0.6"))
        g.add(d.line((sx, sy - r - 1), (sx, sy + r + 1), stroke=col, stroke_width=0.12, stroke_dasharray="2,0.6,0.4,0.6"))
        if r > 4:
            sh.text(tag, sx, sy + 1.0, size=2.6, anchor="middle", bold=True, color=col)
        elif t == "Column":
            sh.text(tag, sx, sy - r - 4.5, size=1.9, anchor="middle", bold=True, color=col, rotate=-90 if tag in
                    ("C-102", "C-103", "C-104") else None)
        else:
            sh.text(tag, sx + r + 0.8, sy + 0.6, size=1.5, color=col, bold=True)
        return
    x0, y0, x1, y1 = it["bbox"]
    a, b = P(x0, y1)
    w, h = (x1 - x0) * SC, (y1 - y0) * SC
    if it["shape"] == "hcyl":
        stacked = it["z_base"] > 110
        g.add(d.rect((a, b), (w, h), rx=min(w, h) / 2.2, ry=min(w, h) / 2.2,
                     fill="none" if stacked else "#fbf4ec" if t == "Shell & tube" else "#eef7f2",
                     stroke=col, stroke_width=0.4, stroke_dasharray="1.5,0.8" if stacked else "none"))
        if t == "Shell & tube" and not stacked:
            # channel end marker + pull direction arrow
            ce = it.get("channel_end", 1)
            ang = math.radians(it["rotation"])
            ux, uy = math.cos(ang) * ce, math.sin(ang) * ce
            cxp, cyp = P(x + ux * (it["L"] / 2 - 0.8), y + uy * (it["L"] / 2 - 0.8))
            if abs(ux) > 0.5:
                g.add(d.line((cxp, b), (cxp, b + h), stroke=col, stroke_width=0.3))
            else:
                g.add(d.line((a, cyp), (a + w, cyp), stroke=col, stroke_width=0.3))
        if stacked:
            return
        if t == "Shell & tube" and it["rotation"] == 90:
            sh.text(tag, sx + 0.6, sy, size=1.45, anchor="middle", color=col, rotate=-90, bold=True)
        elif t in ("Desalter", "Drum") and w > 15:
            sh.text(tag, sx, sy + 0.9, size=2.3 if w > 30 else 1.9, anchor="middle", bold=True, color=col)
        else:
            sh.text(tag, sx, b - 0.8, size=1.6, anchor="middle", bold=True, color=col)
        return
    if t == "Air cooler":
        g.add(d.rect((a, b), (w, h), fill="none", stroke=col, stroke_width=0.4, stroke_dasharray="2,1"))
        nf = it.get("fans", 2)
        for k in range(nf):
            fy = b + h * (k + 0.5) / nf
            g.add(d.circle((sx, fy), min(w, h / nf) * 0.36, fill="none", stroke=col, stroke_width=0.2))
        if it.get("bay", 1) == 1:
            nb = it.get("bays", 1)
            sh.text(it["parent_tag"], a + w * nb / 2, b - 0.9, size=1.8, anchor="middle", bold=True, color=col)
        return
    if it["shape"] == "heater":
        g.add(d.rect((a, b), (w, h), fill="#fdecea", stroke=col, stroke_width=0.6))
        cv = it["convection"]
        g.add(d.rect((sx - cv["L"] * SC / 2, sy - cv["W"] * SC / 2), (cv["L"] * SC, cv["W"] * SC), fill="none",
                     stroke=col, stroke_width=0.25, stroke_dasharray="1.5,0.8"))
        st = it["stack"]
        g.add(d.circle(P(st["x"], st["y"]), st["D"] / 2 * SC, fill="white", stroke=col, stroke_width=0.4))
        sh.text(tag, sx, b + 3.6, size=2.6, anchor="middle", bold=True, color=col)
        sh.text(f"{it['duty_mw']:.1f} MW abs., {it['cells']}-cell cabin, {it['burners']} burners", sx, b + h - 1.6,
                size=1.4, anchor="middle", color=col)
        return
    # boxes: pumps, packages, fans, APH
    if t == "Pump":
        g.add(d.rect((a, b), (w, h), fill="#f3ecf7", stroke=col, stroke_width=0.3))
        su = it["nozzles"]["suction"]
        g.add(d.circle(P(su[0], su[1]), 0.45 * SC, fill=col, stroke="none"))
        north = it["rotation"] == 90
        ty = b - 0.7 if north else b + h + 0.7
        sh.text(tag, sx + 0.5, ty, size=1.25, anchor="start", color=col, rotate=-90, bold=True)
        return
    g.add(d.rect((a, b), (w, h), fill="#fff8e0" if t == "Package" else "#fdecea", stroke=col, stroke_width=0.35))
    if t in ("Package", "Air preheater", "Fan"):
        sh.text(tag, sx, sy + 0.6, size=1.5, anchor="middle", bold=True, color=col)
    else:
        sh.text(tag, a + w + 0.6, sy + 0.6, size=1.4, anchor="start", bold=True, color=col)


def dim(sh, d, g, p, q, label, off=(0, 0), small=False):
    ox, oy = off
    (x1, y1), (x2, y2) = P(p[0] + ox, p[1] + oy), P(q[0] + ox, q[1] + oy)
    if math.hypot(x2 - x1, y2 - y1) < 1.0:
        return
    colr = "#0050b0"
    g.add(d.line((x1, y1), (x2, y2), stroke=colr, stroke_width=0.3))
    a = math.atan2(y2 - y1, x2 - x1)
    for (xx, yy), s in (((x1, y1), 1), ((x2, y2), -1)):
        Lh = 1.6
        g.add(d.polygon([(xx, yy), (xx + s * Lh * math.cos(a - 0.3), yy + s * Lh * math.sin(a - 0.3)),
                         (xx + s * Lh * math.cos(a + 0.3), yy + s * Lh * math.sin(a + 0.3))], fill=colr, stroke="none"))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ang = math.degrees(a)
    if ang > 90:
        ang -= 180
    if ang < -90:
        ang += 180
    tw = len(label) * (1.25 if small else 1.45) * 0.62
    t = sh.text(label, mx, my - 0.8, size=1.3 if small else 1.6, anchor="middle", color=colr, bold=True)
    if abs(ang) > 0.1:
        t.rotate(ang, center=(mx, my))
    if small:
        t["x"] = str(mx + 1.2)
        t["text-anchor"] = "start"


def north_arrow(sh, d, cx, cy):
    g = sh.g
    g.add(d.circle((cx, cy), 13, fill="none", stroke="black", stroke_width=0.35))
    g.add(d.polygon([(cx, cy - 16), (cx + 4.5, cy + 8), (cx, cy + 4)], fill="black", stroke="black", stroke_width=0.3))
    g.add(d.polygon([(cx, cy - 16), (cx - 4.5, cy + 8), (cx, cy + 4)], fill="white", stroke="black", stroke_width=0.3))
    sh.text("N", cx, cy - 18, size=5, anchor="middle", bold=True)
    sh.text("PLANT NORTH = TRUE NORTH", cx, cy + 19, size=1.9, anchor="middle")


def wind_rose(sh, d, cx, cy):
    g = sh.g
    # indicative frequency (%) by direction FROM, 16 points starting N, prevailing SSE
    freq = [4, 3, 3, 4, 6, 8, 11, 15, 10, 7, 5, 4, 4, 5, 6, 5]
    k = 1.25
    for r in (5, 10, 15):
        g.add(d.circle((cx, cy), r * k, fill="none", stroke="#aaa", stroke_width=0.15))
    for i, f in enumerate(freq):
        a = math.radians(i * 22.5)
        w = math.radians(7)
        r = f * k
        pts = [(cx, cy), (cx + r * math.sin(a - w), cy - r * math.cos(a - w)), (cx + r * math.sin(a + w), cy - r * math.cos(a + w))]
        g.add(d.polygon(pts, fill="#2a8fbd" if i != 7 else "#c0392b", stroke="#1a5f80", stroke_width=0.15))
    for i, lab in enumerate(["N", "E", "S", "W"]):
        a = math.radians(i * 90)
        sh.text(lab, cx + 21 * math.sin(a), cy - 21 * math.cos(a) + 1.0, size=2.4, anchor="middle", bold=True)
    sh.text("WIND ROSE (WIND FROM, % TIME, INDICATIVE)", cx, cy + 25.5, size=1.9, anchor="middle")
    sh.text("PREVAILING: SSE (RED)", cx, cy + 28.5, size=1.9, anchor="middle", color="#c0392b", bold=True)


def scale_bar(sh, d, x, y):
    g = sh.g
    sh.text("SCALE 1:500 (A1)", x, y - 6, size=2.6, bold=True)
    for i in range(5):
        g.add(d.rect((x + i * 10 * SC / 2 * 2, y), (10 * SC, 2.0), fill="black" if i % 2 == 0 else "white",
                     stroke="black", stroke_width=0.25))
        sh.text(f"{i * 10}", x + i * 10 * SC, y + 5.5, size=1.8, anchor="middle")
    sh.text("50 m", x + 50 * SC, y + 5.5, size=1.8, anchor="middle")
    sh.text("GRID 10 m. COORDINATES E/N IN m.", x, y + 10, size=1.9)
    sh.text("GRADE EL 100.000 (HPP)", x, y + 13.5, size=1.9)


def legend(sh, d, x, y):
    g = sh.g
    sh.text("LEGEND", x, y, size=3.0, bold=True)
    items = [
        ("circle", "#1f4e9c", "Column (platform outline dotted)"), ("hcyl", "#2a7f62", "Drum / desalter"),
        ("hcyl", "#b5651d", "Shell & tube exch. (bar = channel / pull end)"),
        ("ac", "#2a8fbd", "Air cooler bay on rack (EL 115.0), fans"),
        ("box", "#7a3d9c", "Pump (dot = suction end)"), ("heater", "#c0392b", "Fired heater / stack / APH / fans"),
        ("pkg", "#8a6d00", "Chemical injection package"), ("rack", "#000", "Pipe rack PR-100, bents @ 6 m"),
        ("road", "#888", "Road (6 m)"), ("bldg", "#000", "Building (non-classified)"),
        ("crane", "#d08000", "Crane / maintenance area (keep clear)"), ("lay", "#777", "Laydown area"),
        ("esc", "#1a9a3a", "Escape route (min. 2 directions) / AP"), ("dim", "#0050b0", "Spacing check dimension"),
        ("fh", "#d62020", "Fire hydrant / monitor (indicative)"), ("st", "#555", "Ejector structure ST-201 (stacked equip.)"),
    ]
    for i, (k, c, txt) in enumerate(items):
        col_ = i // 8
        row = i % 8
        xx = x + col_ * 150
        yy = y + 5 + row * 5.6
        if k == "circle":
            g.add(d.circle((xx + 4, yy), 2.0, fill="#eef2fb", stroke=c, stroke_width=0.4))
        elif k == "hcyl":
            g.add(d.rect((xx, yy - 1.4), (8, 2.8), rx=1.3, fill="#fbf4ec", stroke=c, stroke_width=0.4))
        elif k == "ac":
            g.add(d.rect((xx, yy - 1.8), (8, 3.6), fill="none", stroke=c, stroke_width=0.4, stroke_dasharray="2,1"))
            g.add(d.circle((xx + 2.2, yy), 1.2, fill="none", stroke=c, stroke_width=0.2))
            g.add(d.circle((xx + 5.8, yy), 1.2, fill="none", stroke=c, stroke_width=0.2))
        elif k == "box":
            g.add(d.rect((xx, yy - 1.0), (8, 2.0), fill="#f3ecf7", stroke=c, stroke_width=0.3))
            g.add(d.circle((xx + 7, yy), 0.7, fill=c))
        elif k == "heater":
            g.add(d.rect((xx, yy - 1.8), (8, 3.6), fill="#fdecea", stroke=c, stroke_width=0.5))
            g.add(d.circle((xx + 4, yy), 1.0, fill="white", stroke=c, stroke_width=0.3))
        elif k == "pkg":
            g.add(d.rect((xx, yy - 1.5), (8, 3.0), fill="#fff8e0", stroke=c, stroke_width=0.3))
        elif k == "rack":
            g.add(d.rect((xx, yy - 1.8), (8, 3.6), fill="#f4f4f4", stroke=c, stroke_width=0.4))
            for bx in (xx + 0.3, xx + 7.7):
                g.add(d.rect((bx - 0.3, yy - 2.1), (0.6, 0.6), fill="black"))
                g.add(d.rect((bx - 0.3, yy + 1.5), (0.6, 0.6), fill="black"))
        elif k == "road":
            g.add(d.rect((xx, yy - 1.8), (8, 3.6), fill="#e3e3e3", stroke=c, stroke_width=0.2))
        elif k == "bldg":
            g.add(d.rect((xx, yy - 1.8), (8, 3.6), fill="url(#hatchb)", stroke=c, stroke_width=0.4))
        elif k == "crane":
            g.add(d.rect((xx, yy - 1.8), (8, 3.6), fill="url(#hatch)", stroke=c, stroke_width=0.3, stroke_dasharray="2,1"))
        elif k == "lay":
            g.add(d.rect((xx, yy - 1.8), (8, 3.6), fill="url(#dots)", stroke=c, stroke_width=0.3, stroke_dasharray="1,1"))
        elif k == "esc":
            g.add(d.line((xx, yy), (xx + 7, yy), stroke=c, stroke_width=0.5, stroke_dasharray="2.5,1.2"))
            g.add(d.polygon([(xx + 8.5, yy), (xx + 6.5, yy - 1), (xx + 6.5, yy + 1)], fill=c))
        elif k == "dim":
            g.add(d.line((xx, yy), (xx + 8, yy), stroke=c, stroke_width=0.3))
            g.add(d.polygon([(xx, yy), (xx + 1.5, yy - 0.5), (xx + 1.5, yy + 0.5)], fill=c))
            g.add(d.polygon([(xx + 8, yy), (xx + 6.5, yy - 0.5), (xx + 6.5, yy + 0.5)], fill=c))
        elif k == "fh":
            g.add(d.circle((xx + 4, yy), 1.1, fill=c, stroke="none"))
            g.add(d.line((xx + 2.4, yy), (xx + 5.6, yy), stroke=c, stroke_width=0.35))
        elif k == "st":
            g.add(d.rect((xx, yy - 1.8), (8, 3.6), fill="none", stroke=c, stroke_width=0.4, stroke_dasharray="3,1"))
            g.add(d.line((xx, yy - 1.8), (xx + 8, yy + 1.8), stroke="#999", stroke_width=0.15))
        sh.text(txt, xx + 11, yy + 0.8, size=2.1)


def spacing_table(sh, d, L, x, y):
    g = sh.g
    sh.text("SPACING CHECK (COMPUTED FROM data/layout.json)", x, y, size=3.0, bold=True)
    cols = [("RULE", 0), ("BASIS", 72), ("ITEMS (GOVERNING PAIR)", 160), ("REQ'D", 230), ("ACTUAL", 250), ("STATUS", 272)]
    W = 300
    y0 = y + 3
    rh = 5.0
    n = len(L.checks)
    g.add(d.rect((x, y0), (W, rh * (n + 1)), fill="none", stroke="black", stroke_width=0.35))
    g.add(d.rect((x, y0), (W, rh), fill="#e8e8e8", stroke="black", stroke_width=0.35))
    for lab, cx in cols:
        sh.text(lab, x + cx + 1.2, y0 + 3.5, size=2.0, bold=True)
        if cx:
            g.add(d.line((x + cx, y0), (x + cx, y0 + rh * (n + 1)), stroke="black", stroke_width=0.2))
    for i, c in enumerate(L.checks):
        yy = y0 + rh * (i + 1)
        g.add(d.line((x, yy), (x + W, yy), stroke="black", stroke_width=0.15))
        op = "<=" if c.get("kind") == "<=" else ">="
        vals = [c["rule"], c["basis"], f"{c['item_a']} / {c['item_b']}", f"{op} {c['required_m']:.1f}",
                f"{c['actual_m']:.1f} m", c["status"]]
        for (lab, cx), v in zip(cols, vals):
            fs = 1.75 if cx in (0, 72) else 1.9
            ok = v == "OK"
            sh.text(_fit(v, {0: 58, 72: 66, 160: 46}.get(cx, 20)), x + cx + 1.2, yy + 3.4, size=fs,
                    bold=cx == 272, color=("#1a7a2a" if ok else "#c00000") if cx == 272 else "black")
    sh.text("All distances edge-to-edge (m) of plan bounding boxes; columns use circumscribed square (conservative).",
            x, y0 + rh * (n + 1) + 3.5, size=1.8, italic=True)


def _fit(s, n):
    return s if len(s) <= n else s[: n - 1] + "."


def schedule(sh, d, L, x, y):
    g = sh.g
    sh.text("EQUIPMENT LOCATION SCHEDULE (CENTRELINE COORDINATES, m; BASE / TOP EL)", x, y, size=3.0, bold=True)
    items = sorted(L.items, key=lambda i: (i["tag"][0], i["tag"]))
    ncol = 5
    per = math.ceil(len(items) / ncol)
    cw = 125
    rh = 2.95
    for c in range(ncol):
        xx = x + c * cw
        sh.text("TAG", xx, y + 5, size=1.9, bold=True)
        sh.text("E", xx + 27, y + 5, size=1.9, bold=True, anchor="end")
        sh.text("N", xx + 40, y + 5, size=1.9, bold=True, anchor="end")
        sh.text("BASE EL", xx + 56, y + 5, size=1.9, bold=True, anchor="end")
        sh.text("TOP EL", xx + 72, y + 5, size=1.9, bold=True, anchor="end")
        sh.text("SERVICE", xx + 75, y + 5, size=1.9, bold=True)
        g.add(d.line((xx, y + 6.2), (xx + cw - 4, y + 6.2), stroke="black", stroke_width=0.2))
        for r, it in enumerate(items[c * per:(c + 1) * per]):
            yy = y + 9 + r * rh
            sh.text(it["tag"], xx, yy, size=1.75)
            sh.text(f"{it['x']:.1f}", xx + 27, yy, size=1.75, anchor="end")
            sh.text(f"{it['y']:.1f}", xx + 40, yy, size=1.75, anchor="end")
            sh.text(f"{it['z_base']:.3f}", xx + 56, yy, size=1.75, anchor="end")
            sh.text(f"{it['top_el']:.1f}", xx + 72, yy, size=1.75, anchor="end")
            sh.text(_fit(it["service"], 30), xx + 75, yy, size=1.55)
        if c:
            g.add(d.line((xx - 3, y + 2), (xx - 3, y + 9 + per * rh), stroke="#999", stroke_width=0.15))


def area_key(sh, d, x, y):
    sh.text("AREA ALLOCATION", x, y, size=3.0, bold=True)
    rows = ["Area 100 west: desalting (south of rack), preheat exchangers (north, 2 rows + pull aisle)",
            "Light ends C-105/C-106 north-west, > 30 m from fired heaters (LPG spacing)",
            "Area 100 centre: C-101 + side strippers C-102/3/4, OH system D-102/E-115 under A-101",
            "Fired heaters H-101 / H-201 south band y 20-50 (upwind, SSE wind), FG KO D-103",
            "Area 200 east: C-201, ejector structure ST-201 + hotwell D-201 (barometric legs)",
            "Pump rows CL 3.5 m (N) / 4.5 m (S) off rack edge, grouped below their suction vessels",
            "Air coolers on rack top over the systems they serve (OH, products, light ends, VGO)"]
    for i, r in enumerate(rows):
        sh.text(f"- {r}", x, y + 5 + i * 3.6, size=2.0)
