"""Fired heater GA drawings: CFU-100-ME-GA-005 (H-101), CFU-200-ME-GA-006 (H-201)."""
from __future__ import annotations

import math

from ..drawing.sheet import Sheet
from .common import eq, results
from .draw import BLUE, DIM, GREY, MED, THIN, THK, Pen
from .ga_columns import GA_DIR

REFR = "#f1e3cf"
CASE = 0.25          # m casing + refractory


def _flame(P, x, y, h, w=1.6):
    P.path(f"M {x - w / 2} {y} Q {x - w} {y - h * 0.5} {x} {y - h} Q {x + w} {y - h * 0.5} {x + w / 2} {y} Z",
           lw=0.2, fill="#f6b26b", color="#c55a11")


def front_elevation(P, G, x0, yg, s):
    """Side view along the tubes (length direction)."""
    Lb, hdr = G["L_box"], G["hdr"]
    y = lambda z: yg - z * s
    xL = x0 + hdr * s
    xR = xL + Lb * s
    # grade
    P.line((x0 - 8, yg), (x0 + (Lb + 2 * hdr) * s + 8, yg), w=THK)
    P.hatch([(x0 - 8, yg), (x0 + (Lb + 2 * hdr) * s + 8, yg), (x0 + (Lb + 2 * hdr) * s + 8, yg + 2),
             (x0 - 8, yg + 2)], spacing=1.2, lw=0.1)
    # support columns
    for xc in (xL + 0.3 * s, (xL + xR) / 2, xR - 0.3 * s):
        P.rect(xc - 0.25 * s, y(G["floor"]), 0.5 * s, G["floor"] * s, lw=MED, fill="#dddddd")
    # radiant box
    P.rect(xL, y(G["rad_top"]), Lb * s, G["box_h"] * s, lw=THK, fill=REFR)
    P.rect(xL + CASE * s, y(G["rad_top"]) + CASE * s, (Lb - 2 * CASE) * s, (G["box_h"] - CASE) * s, lw=THIN, fill="white")
    # tubes (hidden, on far wall) + header boxes
    z0 = G["floor"] + 1.0
    for i in range(G["per_wall"]):
        zz = z0 + i * G["pitch"]
        P.line((xL + 0.3 * s, y(zz)), (xR - 0.3 * s, y(zz)), w=0.15, color="#555555", dash="2,0.8")
    for xh in (x0, xR):
        P.rect(xh, y(G["floor"] + G["coil_h"] + 1.8), hdr * s, (G["coil_h"] + 1.4) * s, lw=MED, fill="#e8e8e8")
        for i in range(0, G["per_wall"] - 1, 2):
            zz = z0 + i * G["pitch"]
            cxh = xh + (hdr * s * (0.35 if xh == x0 else 0.65))
            P.path(f"M {cxh} {y(zz)} A {G['pitch'] * s / 2} {G['pitch'] * s / 2} 0 0 {0 if xh == x0 else 1} {cxh} "
                   f"{y(zz + G['pitch'])}", lw=0.15, color="#555555")
    # hip (side view: rectangle) + convection
    P.rect(xL, y(G["conv_bot"]), Lb * s, G["hip"] * s, lw=MED, fill=REFR)
    P.rect(xL, y(G["conv_top"]), Lb * s, G["conv_h"] * s, lw=THK, fill=REFR)
    P.rect(xL + CASE * s, y(G["conv_top"]) + CASE * s, (Lb - 2 * CASE) * s, (G["conv_h"] - 2 * CASE) * s, lw=THIN,
           fill="white")
    nrows = G["conv_rows"] + G["ss_rows"] + G["util_rows"]
    for i in range(nrows):
        zz = G["conv_bot"] + 0.5 + i * 0.30
        P.line((xL + 0.3 * s, y(zz)), (xR - 0.3 * s, y(zz)), w=0.15, color="#555555", dash="2,0.8")
    for xh in (x0, xR):
        P.rect(xh, y(G["conv_top"]), hdr * s, G["conv_h"] * s, lw=MED, fill="#e8e8e8")
    # breeching + stack
    xc = (xL + xR) / 2
    bw = min(Lb * 0.35, 6.0) * s
    P.pline([(xL + Lb * s * 0.2, y(G["conv_top"])), (xc - G["stack_D"] / 2 * s, y(G["brch_top"])),
             (xc + G["stack_D"] / 2 * s, y(G["brch_top"])), (xR - Lb * s * 0.2, y(G["conv_top"]))], w=THK, fill=REFR,
            close=True)
    P.rect(xc - G["stack_D"] / 2 * s, y(G["H_top"]), G["stack_D"] * s, G["stack_h"] * s, lw=THK, fill="white")
    P.line((xc - G["stack_D"] / 2 * s, y(G["brch_top"] + 1.5)), (xc + G["stack_D"] / 2 * s, y(G["brch_top"] + 1.5)),
           w=0.5)
    P.ctr((xc, y(G["H_top"]) - 5), (xc, yg + 4))
    # burners under floor
    cnt = G["burners_cell"]
    for i in range(cnt):
        xb = xL + (i + 0.5) * Lb * s / cnt
        P.rect(xb - 0.35 * s, y(G["floor"]) , 0.7 * s, 1.2 * s, lw=MED, fill="#cccccc")
        _flame(P, xb, y(G["floor"]) - 0.2, 4.5 * s * 0.35)
    # platforms
    for zp in (G["floor"] + G["coil_h"] + 1.8, G["conv_bot"] + 0.2, G["conv_top"] + 0.3):
        for xa_, xb_ in ((x0 - 1.0 * s, x0), (xR + hdr * s, xR + hdr * s + 1.0 * s)):
            P.line((xa_, y(zp)), (xb_, y(zp)), w=0.8, color="#505050")
            P.line((xa_ if xa_ < x0 else xb_, y(zp)), (xa_ if xa_ < x0 else xb_, y(zp + 1.07)), w=0.15)
            P.line((xa_, y(zp + 1.07)), (xb_, y(zp + 1.07)), w=0.15)
    zp = G["H_top"] - 3.0
    for sx in (-1, 1):
        xs0 = xc + sx * G["stack_D"] / 2 * s
        P.line((xs0, y(zp)), (xs0 + sx * 1.0 * s, y(zp)), w=0.8, color="#505050")
        P.line((xs0 + sx * 1.0 * s, y(zp)), (xs0 + sx * 1.0 * s, y(zp + 1.07)), w=0.15)
        P.line((xs0, y(zp + 1.07)), (xs0 + sx * 1.0 * s, y(zp + 1.07)), w=0.15)
    P.leader([(xc + G["stack_D"] / 2 * s + 1.0 * s, y(zp)), (xc + 30, y(zp) + 6)], "STACK PLATFORM (SAMPLING)", 1.7)
    # dims
    xd = x0 + (Lb + 2 * hdr) * s + 8
    for z0_, z1_, t in ((0, G["floor"], f"{G['floor'] * 1000:.0f}"), (G["floor"], G["rad_top"], f"{G['box_h'] * 1000:.0f}"),
                        (G["rad_top"], G["conv_bot"], f"{G['hip'] * 1000:.0f}"),
                        (G["conv_bot"], G["conv_top"], f"{G['conv_h'] * 1000:.0f}"),
                        (G["conv_top"], G["brch_top"], "2000"), (G["brch_top"], G["H_top"], f"{G['stack_h'] * 1000:.0f}")):
        P.dim_v(xd, y(z0_), y(z1_), t, side="right", size=1.8)
    P.dim_v(xd + 9, yg, y(G["H_top"]), f"{G['H_top'] * 1000:.0f}", side="right", size=1.9)
    P.dim_h(yg + 9, x0, x0 + (Lb + 2 * hdr) * s, f"{G['L_out'] * 1000:.0f} OVERALL", size=1.9, ext_from=yg)
    P.dim_h(yg + 15, xL, xR, f"{Lb * 1000:.0f} RADIANT BOX (TUBES {G['L_tube'] * 1000:.0f} EFF.)", size=1.8)
    # elevations
    ex = x0 - 6
    for zz, lab in ((0, "GRADE"), (G["floor"], "FLOOR"), (G["rad_top"], "ARCH"), (G["conv_top"], "CONV. TOP"),
                    (G["H_top"], "STACK TOP")):
        P.elev(ex, y(zz), f"{lab} EL {100 + zz:.3f}", side="left", size=1.75, w=30)
    # callouts
    P.leader([(xL + Lb * s * 0.5, y(G["floor"] + G["coil_h"] * 0.5)), (xL + Lb * s * 0.5 + 25, y(G["floor"] + 2))],
             "RADIANT COIL (HIDDEN)\nA335 P9", 1.8)
    P.leader([(x0 + hdr * s * 0.5, y(G["floor"] + G["coil_h"] * 0.6)), (x0 - 4, y(G["floor"] + G["coil_h"] * 0.6) - 18)],
             "HEADER BOX\n(RETURN BENDS)", 1.8, "end")
    P.leader([(xc + G["stack_D"] / 2 * s, y(G["brch_top"] + 1.5)), (xc + 30, y(G["brch_top"] + 3))], "STACK DAMPER", 1.8)
    P.leader([(xL + Lb * s * 0.25, y(G["conv_bot"] + G["conv_h"] / 2)), (xL - 4, y(G["conv_bot"] + G["conv_h"] / 2) - 4)],
             "CONVECTION", 1.8, "end")
    P.leader([(xL + Lb * s / cnt * 0.5, y(G["floor"]) + 0.8 * s), (xL - 4, y(G["floor"]) + 9)],
             f"BURNERS ({cnt} PER CELL)", 1.8, "end")


def end_elevation(P, G, x0, yg, s):
    """Cross-section A-A across the cells: tubes, burners, hip, convection rows, stack."""
    y = lambda z: yg - z * s
    cells = G["cells"]
    co = G["cell_out"]
    W = G["W_out"] * s
    P.line((x0 - 8, yg), (x0 + W + 8, yg), w=THK)
    P.hatch([(x0 - 8, yg), (x0 + W + 8, yg), (x0 + W + 8, yg + 2), (x0 - 8, yg + 2)], spacing=1.2, lw=0.1)
    xm = x0 + W / 2
    cw = G["conv_w"] * s
    for k in range(cells):
        xa = x0 + k * co * s
        # columns
        for xc in (xa + 0.3 * s, xa + co * s - 0.3 * s):
            P.rect(xc - 0.25 * s, y(G["floor"]), 0.5 * s, G["floor"] * s, lw=MED, fill="#dddddd")
        # box with refractory
        P.rect(xa, y(G["rad_top"]), co * s, G["box_h"] * s, lw=THK, fill=REFR)
        xi = xa + CASE * s
        P.rect(xi, y(G["rad_top"]) + CASE * s, G["cell_in"] * s, (G["box_h"] - CASE) * s, lw=THIN, fill="white")
        # tubes on both side walls
        z0 = G["floor"] + 1.0
        r = 0.1683 / 2 * s
        for xw in (xi + 0.25 * s, xi + G["cell_in"] * s - 0.25 * s):
            for i in range(G["per_wall"]):
                P.circle((xw, y(z0 + i * G["pitch"])), r, lw=0.15, fill="#9ab")
        # burner
        xb = xi + G["cell_in"] * s / 2
        P.rect(xb - 0.35 * s, y(G["floor"]), 0.7 * s, 1.2 * s, lw=MED, fill="#cccccc")
        _flame(P, xb, y(G["floor"]) - 0.2, G["box_h"] * 0.38 * s, w=2.2)
        P.ctr((xb, y(G["floor"]) + 1.5 * s), (xb, y(G["rad_top"]) - 2))
        if k == 0:
            P.dim_h(y(G["floor"] + G["coil_h"] + 1.4), xi + 0.25 * s, xb, f"{G['W_cl'] / 2 * 1000:.0f}", size=1.6)
            P.dim_h(y(G["rad_top"]) - 0.5 * s - 3, xi + 0.25 * s, xi + G["cell_in"] * s - 0.25 * s,
                    f"{G['W_cl'] * 1000:.0f} TUBE CL", size=1.6)
    # hip (sloped roof) from radiant cells to convection
    P.pline([(x0, y(G["rad_top"])), (xm - cw / 2 - CASE * s, y(G["conv_bot"])), (xm + cw / 2 + CASE * s, y(G["conv_bot"])),
             (x0 + W, y(G["rad_top"]))], w=MED, fill=REFR, close=True)
    P.pline([(x0 + CASE * s * 1.5, y(G["rad_top"]) - 0.01), (xm - cw / 2, y(G["conv_bot"]) + CASE * s),
             (xm + cw / 2, y(G["conv_bot"]) + CASE * s), (x0 + W - CASE * s * 1.5, y(G["rad_top"]) - 0.01)], w=THIN,
            fill="white", close=True)
    # convection section
    P.rect(xm - cw / 2 - CASE * s, y(G["conv_top"]), cw + 2 * CASE * s, G["conv_h"] * s, lw=THK, fill=REFR)
    P.rect(xm - cw / 2, y(G["conv_top"]) + CASE * s, cw, (G["conv_h"] - 2 * CASE) * s, lw=THIN, fill="white")
    r = 0.1683 / 2 * s
    rows = [("shock", G["shock_rows"]), ("stud", G["conv_rows"] - G["shock_rows"]), ("ss", G["ss_rows"]),
            ("util", G["util_rows"])]
    zz = G["conv_bot"] + 0.45
    i = 0
    for kind, n in rows:
        for _ in range(n):
            off = (G["pitch"] / 2 if i % 2 else 0) - G["pitch"] / 4
            for j in range(G["per_row"]):
                xt = xm - (G["per_row"] - 1) / 2 * G["pitch"] * s + j * G["pitch"] * s + off * s
                fill = {"shock": "#9ab", "stud": "white", "ss": "#cfe2f3", "util": "#ffe599"}[kind]
                P.circle((xt, y(zz)), r * (0.75 if kind in ("ss", "util") else 1.0), lw=0.15, fill=fill)
                if kind == "stud":
                    P.circle((xt, y(zz)), r * 1.35, lw=0.08, color="#888888")
            zz += 0.30
            i += 1
    # breeching + stack
    P.pline([(xm - cw / 2 - CASE * s, y(G["conv_top"])), (xm - G["stack_D"] / 2 * s, y(G["brch_top"])),
             (xm + G["stack_D"] / 2 * s, y(G["brch_top"])), (xm + cw / 2 + CASE * s, y(G["conv_top"]))], w=THK,
            fill=REFR, close=True)
    P.rect(xm - G["stack_D"] / 2 * s, y(G["H_top"]), G["stack_D"] * s, G["stack_h"] * s, lw=THK, fill="white")
    P.ctr((xm, y(G["H_top"]) - 5), (xm, yg + 4))
    # dims & labels
    P.dim_h(yg + 9, x0, x0 + W, f"{G['W_out'] * 1000:.0f}", ext_from=yg, size=1.9)
    if cells > 1:
        P.dim_h(yg + 15, x0, x0 + co * s, f"{co * 1000:.0f} CELL", size=1.7)
    P.dim_h(y(G["H_top"]) - 3, xm - G["stack_D"] / 2 * s, xm + G["stack_D"] / 2 * s, f"ID {G['stack_D'] * 1000:.0f}",
            size=1.6)
    xr = x0 - 4
    xl = xm - cw / 2 + 1
    yl = y(G["conv_bot"] + 0.6)
    P.leader([(xl, yl), (xr, yl + 4)], f"SHOCK ROWS ({G['shock_rows']}), BARE P5", 1.7, "end")
    zs = G["conv_bot"] + 0.45 + 0.3 * (G["shock_rows"] + 1)
    P.leader([(xl, y(zs)), (xr, y(zs) - 2)], f"STUDDED ROWS ({G['conv_rows'] - G['shock_rows']})", 1.7, "end")
    if G["ss_rows"]:
        P.leader([(xl, y(G["conv_top"] - 0.7)), (xr, y(G["conv_top"] - 0.7) - 8)],
                 f"STEAM SUPERHEAT COIL ({G['ss_rows']} ROWS)", 1.7, "end")
    if G["util_rows"]:
        P.leader([(xl, y(G["conv_top"] - 0.7)), (xr, y(G["conv_top"] - 0.7) - 8)],
                 f"UTILITY COIL ({G['util_rows']} ROWS) - HOLD", 1.7, "end")
    P.leader([(x0 + CASE * s + 0.25 * s + 1, y(G["floor"] + G["coil_h"] * 0.7)), (x0 - 4, y(G["floor"] + G["coil_h"] * 0.7) - 6)],
             f"RADIANT TUBES 6\" ({G['per_wall']}/WALL)", 1.7, "end")
    P.leader([(x0 + 0.5, y(G["rad_top"] - 1.5)), (x0 - 4, y(G["rad_top"] - 1.5) - 10)], "CERAMIC FIBRE\nLINING", 1.7, "end")


def burner_plan(P, G, x0, y0, s):
    cells = G["cells"]
    Lb = G["L_box"]
    for k in range(cells):
        ya = y0 + k * G["cell_out"] * s
        P.rect(x0, ya, Lb * s, G["cell_out"] * s, lw=THK, fill=REFR)
        P.rect(x0 + CASE * s, ya + CASE * s, (Lb - 2 * CASE) * s, G["cell_in"] * s, lw=THIN, fill="white")
        for yt in (ya + (CASE + 0.25) * s, ya + (CASE + G["cell_in"] - 0.25) * s):
            P.line((x0 + 0.3 * s, yt), (x0 + (Lb - 0.3) * s, yt), w=0.6, color="#557")
        yc = ya + (CASE + G["cell_in"] / 2) * s
        P.ctr((x0 - 4, yc), (x0 + Lb * s + 4, yc))
        n = G["burners_cell"]
        for i in range(n):
            xb = x0 + (i + 0.5) * Lb * s / n
            P.circle((xb, yc), 0.55 * s, lw=0.35, fill="#f6b26b")
            P.text(f"B{k * n + i + 1}", xb, yc - 0.55 * s - 1.0, 1.5, "middle")
        P.text(f"CELL {'AB'[k]}", x0 + Lb * s + 6, yc + 0.8, 2.0, bold=True)
        if k == 0:
            P.dim_h(ya - 4, x0 + 0.5 * Lb * s / n, x0 + 1.5 * Lb * s / n, f"{G['burner_pitch'] * 1000:.0f}", size=1.6)
    P.dim_h(y0 + cells * G["cell_out"] * s + 6, x0, x0 + Lb * s, f"{Lb * 1000:.0f}", size=1.7)
    P.dim_v(x0 - 5, y0, y0 + cells * G["cell_out"] * s, f"{G['W_out'] * 1000:.0f}", size=1.7)


def pass_schematic(P, G, x0, y0, w, h, hot):
    """Pass arrangement (NTS): inlet manifold -> pass FCVs -> convection -> crossover -> radiant -> outlet."""
    n = G["passes"]
    cells = G["cells"]
    dy = h / (n + 1)
    xin, xfc, xcv0, xcv1, xr0, xr1, xout = (x0 + w * f for f in (0.02, 0.12, 0.22, 0.42, 0.52, 0.80, 0.92))
    P.line((xin, y0 + dy * 0.5), (xin, y0 + dy * (n + 0.5)), w=1.0)
    P.text("INLET", xin - 1, y0 + dy * 0.3, 1.8, "start", bold=True)
    P.line((xout, y0 + dy * 0.5), (xout, y0 + dy * (n + 0.5)), w=1.0)
    P.text("OUTLET", xout - 4, y0 + dy * 0.3, 1.8, "start", bold=True)
    P.rect(xcv0, y0 + dy * 0.4, xcv1 - xcv0, dy * n + 0.2 * dy, lw=MED, fill="#f6efe2")
    P.text("CONVECTION", (xcv0 + xcv1) / 2, y0 + dy * 0.3, 1.8, "middle", bold=True)
    per = n // cells
    for k in range(cells):
        ya = y0 + dy * (0.4 + k * per)
        P.rect(xr0, ya, xr1 - xr0, dy * per + (0.2 * dy if k == cells - 1 else 0), lw=MED, fill="#fde9d9")
        P.text(f"RADIANT CELL {'AB'[k]}" if cells > 1 else "RADIANT", (xr0 + xr1) / 2, ya + dy * per / 2 + 0.8, 2.0,
               "middle", bold=True, color="#c55a11")
    for i in range(n):
        yy = y0 + dy * (i + 1)
        P.line((xin, yy), (xcv0, yy), w=0.35)
        P.circle((xfc, yy), 1.5, lw=0.3, fill="white")
        P.text("FC", xfc, yy + 0.6, 1.3, "middle")
        P.pline([(xcv0 + 1, yy), (xcv1 - 3, yy - dy * 0.15), (xcv0 + 3, yy + dy * 0.15), (xcv1 - 1, yy)], w=0.25)
        P.line((xcv1, yy), (xr0, yy), w=0.35, dash="2,0.8")
        P.pline([(xr0 + 1, yy), (xr1 - 3, yy - dy * 0.15), (xr0 + 3, yy + dy * 0.15), (xr1 - 1, yy)], w=0.25,
                color="#c55a11")
        P.line((xr1, yy), (xout, yy), w=0.35)
        P.text(f"P{i + 1}", xin + 2, yy - 0.7, 1.5)
        P.circle((xr1 + (xout - xr1) * 0.45, yy), 1.3, lw=0.25, fill="white")
        P.text("TI", xr1 + (xout - xr1) * 0.45, yy + 0.5, 1.1, "middle")
    P.text("CROSSOVERS", (xcv1 + xr0) / 2, y0 + dy * (n + 0.9), 1.6, "middle")
    flow = G["h"]["flow"] / 1000 / n
    P.text(f"{n} passes x {flow:.1f} t/h; pass flow control + pass outlet TI (balancing), COT to "
           f"{'C-101' if hot else 'C-201'} transfer line", x0, y0 + h + 3, 1.8)


def aph_plan(P, x0, y0, s):
    """H-101 balanced-draft arrangement plan (1:300, schematic)."""
    e120 = eq("E-120")
    # heater footprint
    P.rect(x0, y0, 21.9 * s, 12.7 * s, lw=THK, fill=REFR)
    P.text("H-101", x0 + 21.9 * s / 2, y0 + 12.7 * s / 2 + 1, 2.4, "middle", bold=True)
    P.circle((x0 + 21.9 * s / 2, y0 + 12.7 * s / 2 - 5), 2.5 * s / 2, lw=0.4)
    xa = x0 + 21.9 * s + 6 * s
    ya = y0 + 1
    P.rect(xa, ya, e120["W"] * s, e120["L"] * s, lw=THK, fill="#dfe8f4")
    P.text("E-120", xa + e120["W"] * s / 2, ya + e120["L"] * s / 2, 2.0, "middle", bold=True)
    P.text("APH", xa + e120["W"] * s / 2, ya + e120["L"] * s / 2 + 3, 1.7, "middle")
    for i, (tag, yy) in enumerate((("K-101A", ya + e120["L"] * s + 6), ("K-101B", ya + e120["L"] * s + 14))):
        P.rect(xa - 2, yy, 6 * s * 0.5, 3 * s * 0.5, lw=MED, fill="#e8e8e8")
        P.text(tag, xa - 3, yy + 2, 1.6, "end")
    for i, (tag, yy) in enumerate((("K-102A", ya + e120["L"] * s + 6), ("K-102B", ya + e120["L"] * s + 14))):
        P.rect(xa + e120["W"] * s - 1, yy, 6 * s * 0.5, 3 * s * 0.5, lw=MED, fill="#e8e8e8")
        P.text(tag, xa + e120["W"] * s + 3 * s * 0.5 + 1, yy + 2, 1.6)
    # ducts
    P.pline([(x0 + 21.9 * s / 2 + 2.5 * s / 2, y0 + 12.7 * s / 2 - 5), (xa + 1, ya + 3)], w=1.2, color="#7f6000")
    P.text("FLUE GAS 380 C", (x0 + 21.9 * s + xa) / 2, ya - 1, 1.6, "middle", color="#7f6000")
    P.pline([(xa + e120["W"] * s + 1, ya + e120["L"] * s + 8), (xa + e120["W"] * s + 10, ya + e120["L"] * s + 8),
             (xa + e120["W"] * s + 10, y0 - 6), (x0 + 21.9 * s / 2, y0 - 6), (x0 + 21.9 * s / 2, y0 + 12.7 * s / 2 - 5 - 2.5 * s / 2)],
            w=1.2, color="#7f6000", dash="3,1")
    P.text("ID FAN DISCHARGE 160 C -> STACK", x0 + 21.9 * s / 2 + 2, y0 - 7.5, 1.6, color="#7f6000")
    P.pline([(xa + 2, ya + e120["L"] * s + 8), (xa - 8, ya + e120["L"] * s + 8), (xa - 8, y0 + 12.7 * s + 6),
             (x0 + 2, y0 + 12.7 * s + 6), (x0 + 2, y0 + 12.7 * s)], w=1.2, color="#1060c0")
    P.text("PREHEATED AIR TO BURNER PLENUM", x0 + 4, y0 + 12.7 * s + 9.5, 1.6, color="#1060c0")
    P.text("H-101 BALANCED DRAFT ARRANGEMENT - PLAN 1:300 (SCHEMATIC)", x0, y0 - 14, 2.3, bold=True)
    P.text("Stack bypass damper allows natural-draft operation on fan trip (reduced capacity).", x0, y0 - 10.5, 1.7)


def heater_tables(P, calc, tag, x0, y0, fs=2.05, rh=3.35):
    h = calc["heaters"][tag]
    G, td, W = h["geo"], h["tube"], h["W"]
    hh = G["h"]
    e = eq(tag)
    hot = tag == "H-101"
    rows = [("Service", e["service"]), ("Type", f"{G['cells']}-cell cabin, horizontal tubes, "
                                                 + ("balanced draft + APH" if hot else "natural draft")),
            ("Duty absorbed / fired", f"{hh['Q_abs_kw'] / 1000:.1f} / {hh['Q_fired_kw'] / 1000:.1f} MW (LHV)"),
            ("Radiant / convection duty", f"{hh['radiant_kw'] / 1000:.1f} / {hh['conv_kw'] / 1000:.1f} MW"),
            ("Efficiency (LHV)", f"{hh['eff'] * 100:.0f} %"), ("Flow / passes", f"{hh['flow'] / 1000:.0f} t/h / {hh['passes']}"),
            ("Inlet / outlet T", f"{hh['T_in']:.0f} / {hh['T_out']:.0f} C"), ("Outlet vaporisation", f"{hh['vf_out'] * 100:.0f} wt %"),
            ("Avg. radiant flux", f"{td['q_avg']:.1f} kW/m2"), ("Mass flux", f"{hh['mass_flux']:.0f} kg/m2s"),
            ("Bridgewall T (est.)", f"{G['BWT']:.0f} C"), ("Flue gas", f"{G['fg_kg_s'] * 3.6:.0f} t/h"),
            ("Overall L x W x H", f"{G['L_out']:.1f} x {G['W_out']:.1f} x {G['H_top']:.0f} m"),
            ("Weight empty / operating", f"{W['empty'] / 1e3:.0f} / {W['operating'] / 1e3:.0f} t")]
    y = P.kv_table(x0, y0, rows, [52, 123], title=f"{tag} DESIGN DATA", fs=fs, rh=rh) + 4
    rows = [("Radiant tubes", f"{G['rad_tubes']} x 168.3 OD, {td['sched'][0]} ({td['sched'][1]} mm), A335 P9"),
            ("Effective length", f"{G['L_tube']} m, {G['per_wall']} per wall per cell"),
            ("Design P elastic / rupture", f"{td['P_el'] * 10:.1f} / {td['P_r'] * 10:.1f} barg"),
            ("Design metal T (API 530)", f"{td['Tdm']:.0f} C (EOR TMT {td['TMT']:.0f} C)"),
            ("t min elastic / rupture", f"{td['t_el']:.2f} / {td['t_r']:.2f} mm ({td['gov']} governs)"),
            ("Corr. allow. / life", f"{td['CA']} mm / 100,000 h"),
            ("Convection", f"{G['conv_rows'] * G['per_row']} tubes: {G['shock_rows']} shock + "
                           f"{G['conv_rows'] - G['shock_rows']} studded rows x {G['per_row']}"),
            ("Extra coils", (f"SS superheat {G['ss_rows']} rows" if G["ss_rows"] else "") +
             (f"utility {G['util_rows']} rows (HOLD, {G['util_kw'] / 1000:.1f} MW)" if G["util_rows"] else "")),
            ("Tube supports", "HK40 radiant / 50Cr-50Ni-Nb shock")]
    y = P.kv_table(x0, y, rows, [52, 123], title="COIL DATA (API 530 - CFU-000-ME-CAL-001 S10)", fs=fs, rh=rh) + 4
    rows = [("Burners", f"{G['burners']} ULNB staged-fuel gas, up-fired"),
            ("Arrangement", f"single row per cell, pitch {G['burner_pitch']:.2f} m"),
            ("Heat release design / max", f"{G['burner_mw']:.2f} / {G['burner_mw'] * 1.25:.2f} MW"),
            ("Burner CL to tube CL", f"{G['W_cl'] / 2:.2f} m"), ("Pilots / scanners", "gas pilot, HEI, UV scanner each")]
    y = P.kv_table(x0, y, rows, [52, 123], title="BURNERS (API 535)", fs=fs, rh=rh)
    return y


def ga_heater(calc, tag):
    hot = tag == "H-101"
    G = calc["heaters"][tag]["geo"]
    dwg = "CFU-100-ME-GA-005" if hot else "CFU-200-ME-GA-006"
    notes = ["Dimensions in mm, elevations in m; grade EL 100.000.", "FEED arrangement - vendor to optimise (API 560).",
             "Radiant floor 2.0 m above grade for burner access.",
             "Tube pulling: removable header-box doors at both ends; crane access required.",
             "Datasheet CFU-000-ME-DS-003; coil design CFU-000-ME-CAL-001 S10."]
    if hot:
        notes += ["Balanced draft: FD fans K-101A/B, ID fans K-102A/B, APH E-120.",
                  f"Estimated BWT {G['BWT']:.0f} C - radiant surface to be reviewed (CAL-001 S13)."]
    else:
        notes += [f"HOLD: 88 % efficiency needs ~{G['util_kw'] / 1000:.1f} MW utility coil or APH (CAL-001 S13).",
                  f"HOLD: plot L {G['eq_L']} m in equipment.json < {G['L_out']:.1f} m required.",
                  "Outlet tube step-up (6\"->8\"->10\") for vacuum service by vendor."]
    sh = Sheet("A1", "FIRED HEATER GENERAL ARRANGEMENT", f"{tag} {eq(tag)['service'].upper()}", dwg, scale="1:100",
               discipline="MECHANICAL", notes=notes)
    P = Pen(sh)
    s = 10.0
    yg = 520
    scale_v = s if G["H_top"] * s < 420 else 8.0
    front_elevation(P, G, 62, yg, scale_v)
    P.text(f"SIDE ELEVATION (ALONG TUBES) 1:{1000 / scale_v:.0f}", 62 + G["L_out"] * scale_v / 2, yg + 24, 2.6,
           "middle", bold=True)
    xe = 62 + G["L_out"] * scale_v + 82
    end_elevation(P, G, xe, yg, scale_v)
    P.text(f"SECTION A-A (ACROSS CELLS) 1:{1000 / scale_v:.0f}", xe + G["W_out"] * scale_v / 2, yg + 24, 2.6, "middle",
           bold=True)
    sp = 1000 / 150
    bx = 470
    burner_plan(P, G, bx, 34, sp)
    P.text("BURNER LAYOUT - FLOOR PLAN 1:150", bx + G["L_box"] * sp / 2, 26, 2.4, "middle", bold=True)
    yps = 34 + G["W_out"] * sp + 22
    P.text("PASS ARRANGEMENT (NTS)", bx, yps - 4, 2.4, bold=True)
    pass_schematic(P, G, bx, yps, 165, 9 * G["passes"] + 12, hot)
    if hot:
        aph_plan(P, bx + 4, yps + 9 * G["passes"] + 50, 1000 / 300)
    else:
        P.rect(bx, yps + 9 * G["passes"] + 30, 165, 40, lw=0.5, dash="3,1.5")
        P.text("HOLD - HEAT RECOVERY", bx + 3, yps + 9 * G["passes"] + 36, 2.4, bold=True, color="#c00000")
        P.text(f"Process convection can recover only {G['Q_conv_max'] / 1000:.1f} MW (flue >= "
               f"{G['h']['T_in'] + 50:.0f} C).", bx + 3, yps + 9 * G["passes"] + 42, 1.9)
        P.text(f"{G['util_kw'] / 1000:.1f} MW utility coil shown dotted (steam superheat / BFW) - or add APH.",
               bx + 3, yps + 9 * G["passes"] + 46.5, 1.9)
        P.text("Off-gas (stream 28, from D-202) burned on dedicated burner tips.", bx + 3, yps + 9 * G["passes"] + 51, 1.9)
    heater_tables(P, calc, tag, 651, 20)
    coil_schedule(P, calc, tag, 20, 22)
    return sh


def coil_schedule(P, calc, tag, x0, y0):
    h = calc["heaters"][tag]
    G, td = h["geo"], h["tube"]
    hh = G["h"]
    pr = G["per_row"]
    rows = [["Radiant" + (" (cells A+B)" if G["cells"] > 1 else ""), f"{G['per_wall']}/wall", "-", str(G["rad_tubes"]),
             f"168.3 x {td['sched'][1]}", "A335 P9", "bare", f"{hh['radiant_kw'] / 1000:.1f}", f"{td['Tdm']:.0f}"],
            ["Convection - shock", str(G["shock_rows"]), str(pr), str(G["shock_rows"] * pr), "168.3 x 7.11", "A335 P5",
             "bare", "-", "-"],
            ["Convection - studded", str(G["conv_rows"] - G["shock_rows"]), str(pr),
             str((G["conv_rows"] - G["shock_rows"]) * pr), "168.3 x 7.11", "A106 B / P5", "studs 12.7x25",
             f"{(hh['conv_kw'] - G['Q_ss']) / 1000:.1f}", "-"]]
    if G["ss_rows"]:
        rows.append(["Steam superheat (SS)", str(G["ss_rows"]), str(pr), str(G["ss_rows"] * pr), "114.3 x 6.02",
                     "A335 P11", "bare", f"{G['Q_ss'] / 1000:.2f}", "-"])
    if G["util_rows"]:
        rows.append(["Utility coil (HOLD)", str(G["util_rows"]), str(pr), str(G["util_rows"] * pr), "114.3 x 6.02",
                     "TBD", "TBD", f"{G['util_kw'] / 1000:.2f}", "-"])
    P.table(x0, y0, ["COIL SECTION", "ROWS", "TUBES/ROW", "No. TUBES", "OD x WALL mm", "MATERIAL", "EXT. SURFACE",
                     "DUTY MW", "TDM C"], rows, [44, 16, 18, 18, 26, 26, 26, 16, 14], title=f"{tag} COIL SCHEDULE",
            fs=2.05, rh=3.4)


def build(calc):
    GA_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for tag, stem in (("H-101", "CFU-100-ME-GA-005_H-101-Heater-GA"), ("H-201", "CFU-200-ME-GA-006_H-201-Heater-GA")):
        out.append(ga_heater(calc, tag).save(GA_DIR / stem))
    return out
