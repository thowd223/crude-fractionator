"""CFU-100-ME-GA-007 desalter D-101A/B GA and CFU-100-ME-GA-008 typical crude preheat exchanger (AES) setting plan."""
from __future__ import annotations

import math

from ..drawing.sheet import Sheet
from . import geometry
from .common import nps_for_area, nps_str
from .draw import BLUE, GREY, MED, THIN, THK, Pen
from .ga_columns import GA_DIR


def _hvessel(P, x0, yc, D, L, s, lw=THK, fill="white"):
    """Horizontal vessel outline (2:1 heads) centred on yc; x0 = left tangent line."""
    R = D / 2 * s
    h = D / 4 * s
    P.rect(x0, yc - R, L * s, 2 * R, lw=0, fill=fill)
    P.line((x0, yc - R), (x0 + L * s, yc - R), w=lw)
    P.line((x0, yc + R), (x0 + L * s, yc + R), w=lw)
    for xt, sg in ((x0, -1), (x0 + L * s, 1)):
        pts = [(xt + sg * h * math.sin(t), yc - R * math.cos(t)) for t in [math.pi * i / 40 for i in range(41)]]
        P.pline(pts, w=lw, fill=fill)
        P.line((xt, yc - R), (xt, yc + R), w=THIN, dash="2,1")
    P.ctr((x0 - h - 6, yc), (x0 + L * s + h + 6, yc))


def ga_desalter(calc):
    dz = geometry.desalter()
    r = calc["drums"]["D-101A"]
    D, L = dz["D"], dz["L"]
    sh = Sheet("A1", "DESALTER GENERAL ARRANGEMENT", "D-101A / D-101B ELECTROSTATIC DESALTERS (2-STAGE)",
               "CFU-100-ME-GA-007", scale="1:75 / 1:40", discipline="MECHANICAL",
               notes=["Dimensions in mm, elevations in m; grade EL 100.000.",
                      "D-101A (1st stage) and D-101B (2nd stage) identical; series flow, wash water to 2nd stage, "
                      "brine recycle to 1st stage.",
                      "Internals (distributor, electrode grids, collector, mud wash) by desalter licensor/vendor.",
                      "Transformers on top platform; vessel liquid-full - LSLL trips transformers.",
                      "Thicknesses per CFU-000-ME-CAL-001; datasheet CFU-000-ME-DS-002.",
                      "One saddle fixed, one sliding (slotted holes, PTFE slide plate)."])
    P = Pen(sh)
    s = 1000 / 75
    x0 = 45
    yc = 200
    R = D / 2 * s
    # ----- elevation
    P.text("ELEVATION 1:75", x0 + L * s / 2, yc + R + 50, 2.8, "middle", bold=True)
    _hvessel(P, x0, yc, D, L, s, fill="#fbfbf6")
    lv = dz["levels"]
    yb = yc + R
    yg = yb + r["BOS_el"] * s
    P.line((x0 - 25, yg), (x0 + L * s + 25, yg), w=THK)
    P.hatch([(x0 - 25, yg), (x0 + L * s + 25, yg), (x0 + L * s + 25, yg + 2), (x0 - 25, yg + 2)], spacing=1.2, lw=0.1)
    # water layer / interface + grids
    yi = yb - lv["interface_NLL"] * s
    P.rect(x0, yi, L * s, yb - yi, lw=0, fill="#d9e8f6")
    P.line((x0, yi), (x0 + L * s, yi), w=0.25, color="#1060c0", dash="2,1")
    P.text("INTERFACE NLL", x0 + 3, yi - 0.8, 1.7, color="#1060c0")
    for k, gz in enumerate(lv["grids"]):
        yy = yb - gz * s
        P.line((x0 + 1.0 * s, yy), (x0 + (L - 1.0) * s, yy), w=0.45, color="#c00000", dash="5,1.5")
    P.text("ELECTRODE GRIDS (3 LEVELS, AC/DC)", x0 + L * s * 0.62, yb - lv["grids"][-1] * s - 1.5, 1.8, color="#c00000")
    yd = yb - 0.42 * D * s
    P.line((x0 + 1.5 * s, yd), (x0 + (L - 1.5) * s, yd), w=0.5, color="#555555")
    P.text("INLET DISTRIBUTOR HEADER", x0 + 3 * s, yd + 2.6, 1.7)
    ycol = yc - R + 0.15 * D * s
    P.line((x0 + 1.5 * s, ycol), (x0 + (L - 1.5) * s, ycol), w=0.5, color="#555555")
    P.text("OUTLET COLLECTOR", x0 + 3 * s, ycol + 2.6, 1.7)
    P.line((x0 + 1 * s, yb - 0.08 * D * s), (x0 + (L - 1) * s, yb - 0.08 * D * s), w=0.3, dash="1,1")
    P.text("MUD-WASH HEADERS", x0 + L * s * 0.4, yb - 0.08 * D * s - 1, 1.6)
    # saddles
    for xs in dz["saddles"]:
        xx = x0 + xs * s
        P.pline([(xx - 1.2 * s, yg), (xx - 0.9 * s, yb + 0.2), (xx + 0.9 * s, yb + 0.2), (xx + 1.2 * s, yg)], w=MED,
                fill="#dddddd", close=True)
        P.rect(xx - 1.6 * s, yg, 3.2 * s, 1.5, lw=MED, fill="#bbbbbb")
    P.text("FIXED", x0 + dz["saddles"][0] * s, yg - 3, 1.8, "middle", bold=True)
    P.text("SLIDING", x0 + dz["saddles"][1] * s, yg - 3, 1.8, "middle", bold=True)
    # nozzles on elevation
    for n in dz["nozzles"]:
        xx = x0 + n["x"] * s
        d = max(n["nps"] * 0.0254 * s, 0.8)
        if n["side"] == "T":
            for j in range(n["qty"]):
                xj = xx + j * 1.6 * s
                P.rect(xj - d / 2, yc - R - 0.7 * s, d, 0.7 * s, lw=0.3, fill="white")
                P.line((xj - d / 2 - 0.6, yc - R - 0.7 * s), (xj + d / 2 + 0.6, yc - R - 0.7 * s), w=0.6)
            P.bubble(xx, yc - R - 0.7 * s - 4, n["mark"], size=1.5)
        elif n["side"] == "B":
            for j in range(n["qty"]):
                xj = xx + j * (L * s * 0.5 if n["qty"] == 2 else 2.5 * s)
                P.rect(xj - d / 2, yb, d, 0.6 * s, lw=0.3, fill="white")
                P.line((xj - d / 2 - 0.6, yb + 0.6 * s), (xj + d / 2 + 0.6, yb + 0.6 * s), w=0.6)
            P.bubble(xx - 4, yb + 0.6 * s + 3.5, n["mark"], size=1.4)
        elif n["kind"] == "MW":
            for xt, sg in ((x0, -1), (x0 + L * s, 1)):
                P.circle((xt + sg * D / 4 * s * 0.55, yc), 0.6 * s / 2, lw=0.35, fill="white")
            P.text("M1", x0 - D / 4 * s * 0.55, yc - 0.45 * s, 1.6, "middle", bold=True)
            P.text("M2", x0 + L * s + D / 4 * s * 0.55, yc - 0.45 * s, 1.6, "middle", bold=True)
        else:
            P.circle((xx, yb - n["z"] * s), max(d / 2, 0.6), lw=0.3, fill="white")
            P.text(n["mark"], xx + 2, yb - n["z"] * s - 1, 1.5, bold=True)
    # transformers + platform
    for j in range(3):
        xj = x0 + (dz["nozzles"][7]["x"] + j * 1.6) * s
        P.rect(xj - 0.6 * s, yc - R - 0.7 * s - 2.0 * s - 6, 1.2 * s, 2.0 * s, lw=MED, fill="#e8e8e8")
    P.text("TRANSFORMERS (3)", x0 + (dz["nozzles"][7]["x"] + 1.6) * s, yc - R - 0.7 * s - 2.0 * s - 8, 1.8, "middle")
    yp = yc - R - 0.5 * s
    P.line((x0 + 3 * s, yp), (x0 + 0.9 * L * s, yp), w=0.8, color="#505050")
    P.line((x0 + 3 * s, yp - 1.07 * s), (x0 + 0.9 * L * s, yp - 1.07 * s), w=0.15)
    P.text(f"TOP PLATFORM EL {100 + r['BOS_el'] + D + 0.2:.3f}", x0 + 3 * s, yp - 1.07 * s - 1, 1.7)
    # dims
    P.dim_h(yg + 9, x0, x0 + L * s, f"{L * 1000:.0f} T/T", ext_from=yc, size=2.0)
    P.dim_h(yg + 16, x0 - D / 4 * s, x0 + L * s + D / 4 * s, f"{(L + D / 2) * 1000:.0f} OVERALL", size=2.0)
    P.dim_h(yg + 23, x0 + dz["saddles"][0] * s, x0 + dz["saddles"][1] * s,
            f"{(dz['saddles'][1] - dz['saddles'][0]) * 1000:.0f} SADDLE CTRS", ext_from=yg, size=1.9)
    P.dim_v(x0 + L * s + D / 4 * s + 14, yc - R, yc + R, f"ID {D * 1000:.0f}", side="right", size=1.9)
    P.dim_v(x0 + L * s + D / 4 * s + 22, yb, yg, f"{r['BOS_el'] * 1000:.0f}", side="right", size=1.9)
    P.elev(x0 - 14, yg, "GRADE EL 100.000", side="left", w=30, size=1.8)
    P.elev(x0 - 14, yb, f"BOS EL {100 + r['BOS_el']:.3f}", side="left", w=30, size=1.8)
    P.elev(x0 - 14, yc - R, f"TOS EL {100 + r['BOS_el'] + D:.3f}", side="left", w=30, size=1.8)
    # ----- plan (top view)
    yp0 = 70
    P.text("PLAN 1:75", x0 + L * s / 2, yp0 - 34, 2.8, "middle", bold=True)
    P.rect(x0, yp0 - R, L * s, 2 * R, lw=THK)
    for xt, sg in ((x0, -1), (x0 + L * s, 1)):
        pts = [(xt + sg * D / 4 * s * math.sin(t), yp0 - R * math.cos(t)) for t in [math.pi * i / 40 for i in range(41)]]
        P.pline(pts, w=THK)
    P.ctr((x0 - 20, yp0), (x0 + L * s + 20, yp0))
    for n in dz["nozzles"]:
        if n["side"] != "T":
            continue
        for j in range(n["qty"]):
            P.circle((x0 + (n["x"] + j * 1.6) * s, yp0), max(n["nps"] * 0.0254 * s / 2, 0.8), lw=0.35, fill="white")
        P.bubble(x0 + n["x"] * s, yp0 - R - 5, n["mark"], size=1.4)
    for n in dz["nozzles"]:
        if n["side"] == "S":
            P.line((x0 + n["x"] * s, yp0 + R), (x0 + n["x"] * s, yp0 + R + 5), w=0.4)
            P.bubble(x0 + n["x"] * s, yp0 + R + 8, n["mark"], size=1.3)
    # ----- end section 1:40
    s2 = 25.0
    cx, cy = 560, 330
    R2 = D / 2 * s2
    P.text("SECTION A-A 1:40 (TYPICAL)", cx, cy - R2 - 26, 2.8, "middle", bold=True)
    P.circle((cx, cy), R2, lw=THK, fill="#fbfbf6")
    yb2 = cy + R2
    yi2 = yb2 - lv["interface_NLL"] * s2
    hw = math.sqrt(max(R2 ** 2 - (cy - yi2) ** 2, 0))
    P.path(f"M {cx - hw} {yi2} A {R2} {R2} 0 0 0 {cx + hw} {yi2} Z", lw=0, fill="#d9e8f6")
    P.line((cx - hw, yi2), (cx + hw, yi2), w=0.3, color="#1060c0", dash="2,1")
    for key, col, lab in (("interface_LLL", "#1060c0", "INTERFACE LLL"), ("interface_HLL", "#1060c0", "INTERFACE HLL")):
        yy = yb2 - lv[key] * s2
        w_ = math.sqrt(max(R2 ** 2 - (cy - yy) ** 2, 0))
        P.line((cx - w_, yy), (cx + w_, yy), w=0.2, color=col, dash="1,1")
        P.text(lab, cx + w_ + 2, yy + 0.6, 1.7, color=col)
    for gz in lv["grids"]:
        yy = yb2 - gz * s2
        w_ = math.sqrt(max(R2 ** 2 - (cy - yy) ** 2, 0)) - 4
        P.line((cx - w_, yy), (cx + w_, yy), w=0.6, color="#c00000", dash="5,1.5")
    P.leader([(cx + 15, yb2 - lv["grids"][1] * s2), (cx + R2 + 6, yb2 - lv["grids"][1] * s2 - 10)],
             "ELECTRODE GRIDS\n(3 LEVELS)", 1.8)
    yd2 = yb2 - 0.42 * D * s2
    P.circle((cx, yd2), 0.4 * s2 / 2, lw=0.4, fill="white")
    P.leader([(cx - 5, yd2), (cx - R2 - 6, yd2 + 8)], "INLET DISTRIBUTOR\n(EMULSION ZONE)", 1.8, "end")
    ycl = cy - R2 + 0.15 * D * s2
    P.circle((cx, ycl), 0.4 * s2 / 2, lw=0.4, fill="white")
    P.leader([(cx - 5, ycl), (cx - R2 - 6, ycl - 6)], "OUTLET COLLECTOR", 1.8, "end")
    for sx in (-1, 1):
        P.circle((cx + sx * R2 * 0.5, yb2 - 0.08 * D * s2), 1.2, lw=0.3, fill="white")
    P.leader([(cx + R2 * 0.5, yb2 - 0.08 * D * s2), (cx + R2 + 6, yb2 + 4)], "MUD-WASH HEADERS", 1.8)
    P.text("BRINE", cx, yb2 - 0.12 * D * s2, 1.8, "middle", color="#1060c0")
    P.text("CRUDE (DESALTING ZONE)", cx, cy - R2 * 0.45, 1.8, "middle")
    P.dim_h(cy + R2 + 8, cx - R2, cx + R2, f"ID {D * 1000:.0f}", size=1.9)
    # ----- tables
    rows = [[n["mark"], str(n["qty"]), nps_str(n["nps"]), f"{n['rating']}# RF",
             {"T": "TOP", "B": "BOTTOM", "S": "SIDE", "H": "HEADS"}[n["side"]], f"{n['x']:.1f}", n["service"]]
            for n in dz["nozzles"]]
    P.table(45, 330, ["MARK", "QTY", "SIZE", "RATING", "LOC.", "X FROM LH TL m", "SERVICE"], rows,
            [16, 9, 11, 18, 16, 24, 130], title="NOZZLE SCHEDULE (EACH VESSEL)", fs=2.1, rh=3.5)
    e = dz["e"]
    W = r["W"]
    dr = [("Service", "1st / 2nd stage electrostatic desalting"), ("Size", f"ID {D * 1000:.0f} x {L * 1000:.0f} T/T"),
          ("Design P / T", f"{r['Pd']} barg / {r['Td']:.0f} C"), ("Operating P / T", f"{e['op_P']} barg / {e['op_T']} C"),
          ("Material", f"{r['mat']}, CA {r['CA']} mm, E = {r['E']}"),
          ("Shell / head t", f"{r['t_nom']} / {r['t_head_nom']} mm (req. {r['t_req']:.1f})"),
          ("Hydrotest", f"{r['Pt']:.2f} barg (shop, horizontal)"), ("Residence time", f"{e['residence_min']} min"),
          ("Volume", f"{r['Vol']:.0f} m3"), ("Insulation", f"{r['ins_mm']} mm"),
          ("Weight empty / oper. / test", f"{W['empty'] / 1e3:.0f} / {W['operating'] / 1e3:.0f} / {W['hydrotest'] / 1e3:.0f} t"),
          ("Code", "ASME VIII Div.1, U-stamp")]
    P.kv_table(651, 20, dr, [58, 117], title="DESIGN DATA (EACH)", fs=2.1, rh=3.5)
    return sh


# ---------------------------------------------------------------------------
def ga_exchanger(calc):
    x = next(d for d in calc["st"] if d["tag"] == "E-106")
    Ds, Lt = x["Ds"] / 1000, x["L"] / 1000
    sh = Sheet("A1", "EXCHANGER SETTING PLAN", f"TYPICAL CRUDE PREHEAT EXCHANGER - TEMA AES ({x['tag']})",
               "CFU-100-ME-GA-008", scale="1:30", discipline="MECHANICAL",
               notes=["Dimensions in mm; elevations in m (grade EL 100.000).",
                      f"Typical for AES crude preheat shells E-101..E-111; {x['tag']} shown "
                      f"({x['series']} shells in series, stacked).",
                      "Crude shell side (square pitch, removable bundle); hot stream tube side.",
                      "Bundle-pull area = tube length + 1.5 m clear at channel end.",
                      "Lower shell saddle fixed, upper shells sliding; intermediate supports bolted.",
                      "Datasheet CFU-000-ME-DS-004; weights data/mech.json."])
    P = Pen(sh)
    s = 1000 / 30
    ch, fh = 0.9, 0.85            # channel length, floating-head cover length (m)
    x0 = 175
    yg = 300
    base = 0.9                    # bottom shell CL clearance above BOS
    gap = 0.45
    tsh = x["t_shell"] / 1000
    Do = Ds + 2 * tsh
    ys = [yg - (base + Do / 2) * s, yg - (base + Do + gap + Do / 2) * s]
    P.line((x0 - ch * s - 30, yg), (x0 + (Lt + fh) * s + 70, yg), w=THK)
    P.hatch([(x0 - ch * s - 30, yg), (x0 + (Lt + fh) * s + 70, yg), (x0 + (Lt + fh) * s + 70, yg + 2),
             (x0 - ch * s - 30, yg + 2)], spacing=1.2, lw=0.1)
    nz_s = nps_for_area(x["cold_flow"] / 3600 / 760 / 2 / 2.0, 6)
    nz_t = nps_for_area(x["hot_flow"] / 3600 / 700 / 2.5, 6)
    for k, yc in enumerate(ys):
        R = Do / 2 * s
        P.rect(x0, yc - R, Lt * s, 2 * R, lw=THK, fill="#fbfbf6")
        # channel (A) with flat cover
        P.rect(x0 - ch * s, yc - R - 0.04 * s, ch * s, 2 * R + 0.08 * s, lw=THK, fill="#eeeeee")
        P.rect(x0 - ch * s - 0.12 * s, yc - R - 0.12 * s, 0.12 * s, 2 * R + 0.24 * s, lw=MED, fill="#cccccc")
        P.line((x0 - ch * s / 2, yc - R), (x0 - ch * s / 2, yc + R), w=THIN, dash="2,1")
        # floating head cover (S) - shell cover
        Rf = (Do / 2 + 0.05) * s
        P.rect(x0 + Lt * s, yc - Rf, 0.15 * s, 2 * Rf, lw=MED, fill="#cccccc")
        pts = [(x0 + Lt * s + 0.15 * s + fh * s * 0.8 * math.sin(t), yc - Rf * math.cos(t)) for t in
               [math.pi * i / 30 for i in range(31)]]
        P.pline(pts, w=THK, fill="#eeeeee")
        P.ctr((x0 - ch * s - 10, yc), (x0 + (Lt + fh) * s + 15, yc))
        # tubes hidden
        for f in (-0.6, -0.3, 0, 0.3, 0.6):
            P.line((x0, yc + f * R), (x0 + Lt * s - 0.3 * s, yc + f * R), w=0.12, color=GREY, dash="2,1")
        # nozzles: shell in/out top & bottom, channel in/out
        dsn = nz_s * 0.0254 * s
        dtn = nz_t * 0.0254 * s
        for xn, top in ((x0 + 0.6 * s, k == 1), (x0 + (Lt - 0.7) * s, k == 0)):
            yy = yc - R if top else yc + R
            sg = -1 if top else 1
            P.rect(xn - dsn / 2, min(yy, yy + sg * 0.35 * s), dsn, 0.35 * s, lw=0.3, fill="white")
        for yy, sg in ((yc - R - 0.04 * s, -1), (yc + R + 0.04 * s, 1)):
            xn = x0 - ch * s / 2
            P.rect(xn - dtn / 2, min(yy, yy + sg * 0.35 * s), dtn, 0.35 * s, lw=0.3, fill="white")
        P.text(f"SHELL {'B (UPPER)' if k else 'A (LOWER)'}", x0 + Lt * s / 2, yc + 1, 2.2, "middle", bold=True)
    # interconnecting shell nozzles (upper shell bottom outlet to lower shell top inlet) shown at RH end
    P.text("SHELL-TO-SHELL\nSTACKED NOZZLES", x0 + (Lt - 0.7) * s + 6, (ys[0] + ys[1]) / 2, 1.8)
    # saddles
    for xs in (x0 + 1.0 * s, x0 + (Lt - 1.2) * s):
        R = Do / 2 * s
        P.pline([(xs - 0.5 * s, yg), (xs - 0.35 * s, ys[0] + R * 0.7), (xs + 0.35 * s, ys[0] + R * 0.7), (xs + 0.5 * s, yg)],
                w=MED, fill="#dddddd", close=True)
        P.rect(xs - 0.35 * s, ys[1] + R * 0.7, 0.7 * s, (ys[0] - R) - (ys[1] + R * 0.7), lw=MED, fill="#dddddd")
    P.text("FIXED", x0 + 1.0 * s, yg + 4, 1.8, "middle", bold=True)
    P.text("SLIDING", x0 + (Lt - 1.2) * s, yg + 4, 1.8, "middle", bold=True)
    # bundle pull zone (shown broken)
    xp0 = x0 - ch * s - 0.12 * s
    pull = Lt + 1.5
    xp1 = 28
    ytop, ybot = ys[1] - Do / 2 * s, ys[0] + Do / 2 * s
    P.rect(xp1, ytop, xp0 - 4 - xp1, ybot - ytop, lw=0.3, dash="3,1.5", color="#c00000")
    xm_ = (xp1 + xp0) / 2
    P.pline([(xm_ - 2, ytop - 3), (xm_ + 2, (ytop + ybot) / 2 - 3), (xm_ - 2, (ytop + ybot) / 2 + 3), (xm_ + 2, ybot + 3)],
            w=0.3, color="#c00000")
    P.text("BUNDLE PULL AREA", xm_, ytop + 12, 2.0, "middle", color="#c00000", bold=True)
    P.text(f"{pull * 1000:.0f} MIN. CLEAR", xm_, ytop + 16, 1.8, "middle", color="#c00000")
    P.text("(SHOWN BROKEN)", xm_, ytop + 19.5, 1.7, "middle", color="#c00000")
    # dims
    P.dim_h(yg + 10, x0, x0 + Lt * s, f"{Lt * 1000:.0f} TUBE LENGTH", ext_from=ys[0], size=1.9)
    P.dim_h(yg + 17, x0 - ch * s - 0.12 * s, x0 + (Lt + 0.15 + fh * 0.8) * s,
            f"{(ch + 0.12 + Lt + 0.15 + fh * 0.8) * 1000:.0f} OVERALL", size=1.9)
    P.dim_h(yg + 24, x0 + 1.0 * s, x0 + (Lt - 1.2) * s, f"{(Lt - 2.2) * 1000:.0f} SADDLES", size=1.9)
    xd = x0 + (Lt + fh) * s + 20
    P.dim_v(xd, yg, ys[0], f"{(base + Do / 2) * 1000:.0f}", side="right", size=1.8)
    P.dim_v(xd, ys[0], ys[1], f"{(Do + gap) * 1000:.0f}", side="right", size=1.8)
    P.dim_v(xd + 9, ys[1] - Do / 2 * s, ys[1] + Do / 2 * s, f"OD {Do * 1000:.0f}", side="right", size=1.8)
    P.elev(xd + 22, yg, "GRADE EL 100.000", w=28, size=1.8)
    P.elev(xd + 22, ys[0], f"CL EL {100 + base + Do / 2:.3f}", w=28, size=1.8)
    P.elev(xd + 22, ys[1], f"CL EL {100 + base + 1.5 * Do + gap:.3f}", w=28, size=1.8)
    P.text("ELEVATION 1:30", x0 + Lt * s / 2, yg + 34, 2.8, "middle", bold=True)
    # plan view
    yp = 420
    R = Do / 2 * s
    P.text("PLAN 1:30", x0 + Lt * s / 2, yp - R - 18, 2.8, "middle", bold=True)
    P.rect(x0, yp - R, Lt * s, 2 * R, lw=THK, fill="#fbfbf6")
    P.rect(x0 - ch * s, yp - R, ch * s, 2 * R, lw=THK, fill="#eeeeee")
    P.rect(x0 + Lt * s, yp - R - 0.05 * s, 0.15 * s, 2 * R + 0.1 * s, lw=MED, fill="#cccccc")
    P.ctr((x0 - ch * s - 10, yp), (x0 + (Lt + fh) * s + 15, yp))
    for xs in (x0 + 1.0 * s, x0 + (Lt - 1.2) * s):
        P.rect(xs - 0.5 * s, yp - R - 0.15 * s, 1.0 * s, 2 * R + 0.3 * s, lw=0.3, dash="2,1")
        for sx in (-1, 1):
            P.circle((xs, yp + sx * (R + 0.05 * s)), 0.8, lw=0.2, fill="black")
    P.dim_v(x0 + (Lt + fh) * s + 20, yp - R - 0.15 * s, yp + R + 0.15 * s, f"{(Do + 0.3) * 1000:.0f} BASEPLATE",
            side="right", size=1.8)
    P.text("ANCHOR BOLTS 4 x M24 PER SADDLE (SLOTTED AT SLIDING SADDLE)", x0, yp + R + 12, 1.8)
    # end view
    cx, cy = 585, 175
    P.text("END VIEW (CHANNEL END) 1:30", cx, cy - 2 * R - 45, 2.6, "middle", bold=True)
    yc0, yc1 = cy + 40, cy + 40 - (Do + gap) * s
    for yc in (yc0, yc1):
        P.circle((cx, yc), R, lw=THK, fill="#fbfbf6")
        P.circle((cx, yc), R + 0.12 * s, lw=MED)
        for i in range(-3, 4):
            for j in range(-3, 4):
                if (i * i + j * j) * (0.2 * s) ** 2 < (R * 0.85) ** 2:
                    P.circle((cx + i * 0.2 * s, yc + j * 0.2 * s), 0.7, lw=0.1)
        P.line((cx - R, yc), (cx + R, yc), w=0.3)
    ygE = yc0 + (base + Do / 2) * s
    P.line((cx - R - 20, ygE), (cx + R + 20, ygE), w=THK)
    P.hatch([(cx - R - 20, ygE), (cx + R + 20, ygE), (cx + R + 20, ygE + 2), (cx - R - 20, ygE + 2)], spacing=1.2, lw=0.1)
    P.pline([(cx - R * 0.9, ygE), (cx - R * 0.75, yc0 + R * 0.6), (cx + R * 0.75, yc0 + R * 0.6), (cx + R * 0.9, ygE)],
            w=MED, fill="#dddddd", close=True)
    P.rect(cx - R * 0.75, yc1 + R * 0.6, 1.5 * R, (yc0 - R) - (yc1 + R * 0.6), lw=MED, fill="#dddddd")
    P.text("PASS PARTITION (4-PASS)", cx + R + 3, yc0 + 1, 1.7)
    P.dim_h(yc1 - R - 8, cx - R, cx + R, f"OD {Do * 1000:.0f}", size=1.8)
    # tables
    rows = [["S1/S2", "2", nps_str(nz_s), f"{x['rating_shell']}# RF", "Shell in / out (crude)"],
            ["T1/T2", "2", nps_str(nz_t), f"{x['rating_tube']}# RF", "Channel in / out (MPA)"],
            ["V / D", "4", '1"', f"{x['rating_shell']}# RF", "Vents / drains (each shell)"],
            ["TI / PI", "4", '1"', f"{x['rating_shell']}# RF", "Thermowell / pressure connections"]]
    P.table(470, 300, ["MARK", "QTY", "SIZE", "RATING", "SERVICE"], rows, [18, 10, 12, 20, 95],
            title="NOZZLE SCHEDULE (EACH SHELL)", fs=2.1, rh=3.5)
    dr = [("Item", f"{x['tag']} - {x['service']}"), ("TEMA type / size", f"{x['size']} (Ds-L mm)"),
          ("Shells", f"{x['n_shells']} ({x['series']} series x {x['parallel']} parallel), stacked 2-high"),
          ("Surface", f"{x['area_shell']:.0f} m2/shell; {x['area_total']:.0f} m2 total"),
          ("Duty / U", f"{x['duty_kw'] / 1000:.1f} MW / {x['U']:.0f} W/m2K"),
          ("Tubes", f"{x['Nt']} x {x['OD']} OD {x['bwg']}, {x['L']} mm, {x['passes']} passes"),
          ("Pitch", f"{x['pitch']:.2f} mm square (cleanable)"),
          ("Design P shell / tube", f"{x['P_shell']:g} / {x['P_tube']:g} barg"), ("Design T", f"{x['des_T']:.0f} C"),
          ("Shell matl. / t", f"{x['shell_mat']} / {x['t_shell']} mm"), ("Tubes matl.", x["moc"]),
          ("Weight empty / filled", f"{x['empty'] / 1e3:.1f} / {x['hydrotest'] / 1e3:.1f} t per shell"),
          ("Code", "ASME VIII-1 / TEMA R / API 660")]
    P.kv_table(651, 20, dr, [50, 125], title="DESIGN DATA", fs=2.05, rh=3.45)
    # typical schedule of all AES preheat exchangers
    rows = []
    for d in calc["st"]:
        if not d["tema"].startswith("AES"):
            continue
        rows.append([d["tag"], d["size"], f"{d['series']}S x {d['parallel']}P", f"{d['area_shell']:.0f}",
                     f"{d['Ds']:.0f}", f"{d['t_shell']}", f"{d['empty'] / 1e3:.1f}", d["service"][:30]])
    P.table(470, 340, ["TAG", "SIZE", "ARRGT", "m2/SH", "Ds mm", "t mm", "t/SH", "SERVICE"], rows,
            [14, 30, 15, 12, 13, 10, 11, 50], title="AES SHELL SCHEDULE (TYPICAL ARRANGEMENT APPLIES)", fs=1.95, rh=3.3)
    return sh


def build(calc):
    GA_DIR.mkdir(parents=True, exist_ok=True)
    return [ga_desalter(calc).save(GA_DIR / "CFU-100-ME-GA-007_D-101AB-Desalter-GA"),
            ga_exchanger(calc).save(GA_DIR / "CFU-100-ME-GA-008_AES-Exchanger-Setting-Plan")]
