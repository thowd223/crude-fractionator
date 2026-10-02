"""Proposed control scheme diagrams CFU-x00-IC-CSD-001..006 (A1, ISA-5.1 symbols).

Simplified process sketches showing the regulatory strategy: cascades, ratio stations, split range,
selectors, feed-forward and the APC (MPC) layer. Tags come from cfu.control_loops (data/control_loops.json).
"""
from __future__ import annotations

from ..drawing.sheet import Sheet
from .common import APC_GRN, GREY, OUT, SIS_RED, Pen, loops, pr, streams

DIR = OUT / "control-scheme"
SHEETS = [
    ("CFU-100-IC-CSD-001", "H-101 COMBUSTION, COT & PASS BALANCING CONTROL"),
    ("CFU-100-IC-CSD-002", "C-101 OVERHEAD, REFLUX, PUMPAROUND & SIDE-DRAW CONTROL"),
    ("CFU-100-IC-CSD-003", "CRUDE CHARGE, DESALTERS & PREHEAT TEMPERATURE CONTROL"),
    ("CFU-100-IC-CSD-004", "STABILISER C-105 & SPLITTER C-106 CONTROL"),
    ("CFU-200-IC-CSD-005", "VACUUM HEATER & COLUMN: PRESSURE, WASH OIL & QUENCH"),
    ("CFU-000-IC-CSD-006", "APC / MPC STRUCTURE (MV / CV / DV)"),
]
RX = 650          # right information column x
RW = 176


def _sheet(i):
    no, t2 = SHEETS[i]
    sh = Sheet("A1", "PROPOSED CONTROL SCHEME", t2, no, sheet=f"{i + 1} OF {len(SHEETS)}",
               discipline="INSTRUMENTATION")
    return sh, Pen(sh), no


def _check_tags(tags):
    L = loops()
    missing = [t for t in tags if t not in L]
    if missing:
        raise ValueError(f"control scheme uses tags not in control_loops: {missing}")


def _apc(p, x, y, label="MPC", r=4.0):
    """Small APC hexagon flag (MPC setpoint handle)."""
    return p.bubble(x, y, f"{label}-", "apc", r=r)


# =============================================================================== CSD-001  H-101
def csd_001():
    sh, p, no = _sheet(0)
    R = pr()
    H = R["heaters"]["H-101"]
    S = streams()
    _check_tags(["FIC-1001", "FIC-1011", "FIC-1018", "TDIC-1019", "TIC-1020", "PIC-1021", "AIC-1022", "PIC-1023",
                 "TIC-1024", "FIC-1025"])
    npass = H["passes"]
    fpp = H["flow"] / npass / 1000

    # ---- heater
    hx0, hy0, hw, hh = 290, 200, 160, 120
    ht = p.heater(hx0, hy0, hw, hh, "H-101", [f"{H['Q_abs_kw'] / 1000:.1f} MW ABS. / {H['Q_fired_kw'] / 1000:.1f} MW FIRED",
                                              f"{npass} PASSES, {H['burners']} BURNERS, {H['cells']} CELLS",
                                              f"CIT {H['T_in']:.0f} °C  ->  COT {H['T_out']:.0f} °C"], conv_h=44)
    cx, cy, cw, ch = ht["conv"]
    p.text("CONVECTION", cx + cw / 2, cy + ch / 2 + 1, 2.2, "middle", color=GREY)
    p.text("RADIANT (2 CELLS)", hx0 + hw / 2, hy0 + 8, 2.2, "middle", color=GREY)
    # plenum & burners
    p.box(hx0, 323, hw, 8, None, fill="none")
    p.text("COMBUSTION AIR PLENUM", hx0 + hw / 2, 328.4, 2.0, "middle")

    # ---- pass inlet manifold
    p.offpage(60, 125, "CRUDE FROM E-111A/B", "CSD-003", "r", w=44)
    p.proc([(60, 125), (150, 125)], arrow=False)
    ypass = [75, 175]
    p.proc([(150, ypass[0]), (150, ypass[1])], arrow=False, w=0.6)
    p.text(f"CIT {S['6']['T_C']:.0f} °C / {S['6']['P_barg']:.1f} barg", 64, 121, 2.0, color=GREY)
    p.text(f"{H['flow'] / 1000:.0f} t/h", 64, 131, 2.0, color=GREY)
    # bias bus (from TDIC) and base bus (from FY-1011A)
    p.offpage(60, 45, "FIC-1001 CRUDE CHARGE SP", "CSD-003", "r", w=50)
    fyA = p.fy(265, 45, "×", "FY-1011A", tag_pos="r")
    p.soft([(60, 45), (fyA["w"][0], 45)])
    p.text(f"K = 1/{npass}  (base SP per pass, {fpp:.1f} t/h)", 272, 56, 1.9, color=GREY)
    for k, y in enumerate(ypass):
        n = 1 if k == 0 else npass
        tag = f"FIC-{1010 + n}"
        p.proc([(150, y), (300 if k == 0 else 322, y)], arrow=False)
        p.line([(170, y), (170, y - 12)], w=0.3)
        p.line([(167.5, y - 1.5), (167.5, y + 1.5)], w=0.45)
        p.line([(172.5, y - 1.5), (172.5, y + 1.5)], w=0.45)
        ft = p.bubble(170, y - 16, f"FT-{1010 + n}", "field", r=4)
        fv = p.cv(205, y, "h", f"FV-{1010 + n}", "FO", tag_pos="b")
        fic = p.bubble(205, y - 16, tag, "dcs")
        p.sig([ft["e"], fic["w"]])
        p.sig([fic["s"], fv["a"]])
        sm = p.fy(235, y - 16, "Σ", f"FY-{1010 + n}B", tag_pos="b")
        p.soft([sm["w"], fic["e"]])
        p.soft([(265, y - 16), sm["e"]])
        p.soft([(224, y - 26), (235, y - 26), sm["n"]])
        # SIS pass flow transmitters
        p.bubble(185, y + 12, f"FT-{1010 + n}", "sis", r=4.6)
        p.text("A/B/C 2oo3", 190.5, y + 12.6, 1.9, color=SIS_RED)
        p.text(f"-> SIF-101", 190.5, y + 15.2, 1.9, color=SIS_RED)
        p.line([(185, y), (185, y + 8)], w=0.3, color=SIS_RED)
        p.text(f"PASS {n}", 153, y - 2, 2.2, bold=True)
    p.soft([(265, fyA["s"][1]), (265, ypass[1] - 16)], arrow=False)
    p.dot(265, ypass[0] - 16)
    p.proc([(300, ypass[0]), (300, 160), (cx, 160)], arrow=True)
    p.proc([(322, ypass[1]), (cx, ypass[1])], arrow=True)
    p.proc([(150, 125), (150, 125)], arrow=False)
    for yy in (110, 125, 140):
        p.line([(150, yy), (215, yy)], w=0.3, dash="2,1.5")
    p.text(f"PASSES 2 TO {npass - 1} TYPICAL (FIC-1012 ... FIC-{1010 + npass - 1})", 155, 104, 2.0, italic=True,
           color=GREY)

    # ---- outlet / COT
    yo = 300
    p.proc([(hx0 + hw, yo), (640, yo)], arrow=True)
    p.text(f"COT {H['T_out']:.0f} °C, {S['7']['P_barg']:.1f} barg, VF {H['vf_out']:.2f}", 545, yo + 4.5, 2.0, color=GREY)
    p.text("TRANSFER LINE TO C-101 (CSD-002)", 545, yo + 8, 2.0)
    ti = p.bubble(475, yo - 14, "TI-1011", "field", r=4.0)
    p.line([(475, yo), (475, yo - 10)], w=0.3)
    p.text("TI-1011 ... 1018", 480, yo - 20, 1.9, color=GREY)
    p.text("(PASS OUTLETS)", 480, yo - 17.5, 1.9, color=GREY)
    td = p.bubble(475, 245, "TDIC-1019", "dcs", note=["PASS", "BALANCING", "Σ BIAS = 0"],
                  note_pos="r")
    p.sig([ti["n"], td["s"]])
    p.soft([td["n"], (475, 30), (224, 30), (224, ypass[1] - 26)], arrow=False)
    p.soft([(224, ypass[0] - 26), (224, ypass[0] - 26)], arrow=False)
    p.dot(224, ypass[0] - 26)
    tt = p.bubble(535, yo - 14, "TT-1020", "field", r=4.0)
    p.line([(535, yo), (535, yo - 10)], w=0.3)
    tic = p.bubble(535, 262, "TIC-1020", "dcs", note=["COT", "MASTER"], note_pos="r")
    p.sig([tt["n"], tic["s"]])
    mpc = _apc(p, 535, 240)
    p.sig([mpc["s"], tic["n"]], color=APC_GRN)
    p.text("COT SP FROM MPC", 541, 239, 1.9, color=APC_GRN)
    p.bubble(590, yo - 14, "TT-1020", "sis", r=4.6)
    p.line([(590, yo), (590, yo - 9.4)], w=0.3, color=SIS_RED)
    p.text("A/B/C 2oo3", 596, yo - 15.5, 1.9, color=SIS_RED)
    p.text("TZHH->SIF-106", 596, yo - 12.9, 1.9, color=SIS_RED)

    # ---- flue gas / air system
    e120 = (545, 130, 25, 50)
    p.box(*e120, None)
    p.line([(e120[0], e120[1] + e120[3]), (e120[0] + e120[2], e120[1])], w=0.3)
    p.text("E-120", e120[0] + e120[2] / 2, e120[1] - 2, 2.4, "middle", bold=True)
    p.text("AIR PREHEATER", e120[0] + e120[2] / 2, e120[1] + e120[3] + 3.2, 1.9, "middle", color=GREY)
    p.line([(cx + cw, 160), (545, 160)], w=0.45, dash="4,1.2", arrow=True)
    p.text("FLUE GAS", 470, 157.5, 2.0, color=GREY)
    # ID fan
    p.line([(570, 140), (596, 140)], w=0.45, dash="4,1.2", arrow=True)
    p.gs.add(p.d.circle((600, 140), 4.0, fill="white", stroke="black", stroke_width=0.45))
    p.text("×", 600, 141.4, 4, "middle")
    p.text("K-102A/B", 600, 150.5, 2.2, "middle", bold=True)
    p.text("ID FAN (VSD)", 600, 153.3, 1.8, "middle", color=GREY)
    p.line([(604, 140), (625, 140), (625, 100)], w=0.45, dash="4,1.2", arrow=True)
    p.text("TO STACK", 627, 104, 2.0)
    # FD fan + hot air
    p.gs.add(p.d.circle((615, 372), 4.0, fill="white", stroke="black", stroke_width=0.45))
    p.text("×", 615, 373.4, 4, "middle")
    p.text("K-101A/B FD FAN", 610, 381.5, 2.2, "end", bold=True)
    p.line([(640, 372), (619, 372)], w=0.45, dash="4,1.2", arrow=True)
    p.text("AIR", 632, 370, 2.0)
    p.box(620.5, 368, 4, 8, None)  # inlet vanes
    p.text("FV-1025", 627, 365, 1.9)
    p.text("INLET VANES", 627, 362.5, 1.6, color=GREY)
    p.line([(615, 368), (615, 170), (570, 170)], w=0.45, dash="4,1.2", arrow=True)
    p.line([(545, 172), (520, 172), (520, 327), (hx0 + hw, 327)], w=0.45, dash="4,1.2", arrow=True)
    p.text("HOT AIR", 522, 210, 2.0, color=GREY)
    ft25 = p.bubble(548, 225, "FT-1025", "field", r=4.0)
    p.line([(520, 225), (544, 225)], w=0.3)
    # stack damper + draft
    sx, sy = ht["stack_top"]
    p.line([(sx - 3, 141), (sx + 3, 138)], w=0.5)
    p.dot(sx, 139.5, 0.7)
    p.text("STACK DAMPER", sx - 8, 128, 1.9, "end", color=GREY)
    pt23 = p.bubble(440, 183, "PT-1023", "field", r=4.0)
    p.line([(440, 187), (440, 197)], w=0.3)
    pic23 = p.bubble(440, 118, "PIC-1023", "dcs", note=["ARCH DRAFT", "-2.5 mmH2O"], note_pos="l")
    p.sig([pt23["n"], pic23["s"]])
    py23 = p.fy(500, 118, "SPLIT", "PY-1023", tag_pos="t")
    p.soft([pic23["e"], py23["w"]])
    p.sig([(503.5, 118), (600, 118), (600, 136)])
    p.text("SC: ID FAN SPEED (0-50 %)", 506, 115.5, 1.9, color=GREY)
    p.sig([(500, 114.5), (500, 104), (sx + 8, 104), (sx + 8, 139), (sx + 3, 139)])
    p.text("STACK DAMPER (50-100 %)", sx + 10, 101.5, 1.9, color=GREY)
    # O2 analyser
    at = p.bubble(458, 212, "AT-1022", "field", r=4.0, note=["O2 / CO"], note_pos="b")
    p.line([(hx0 + hw, 212), (454, 212)], w=0.3)

    # ---- fuel gas header
    yf = 345
    p.offpage(60, yf, "FUEL GAS FROM D-103", "PIC-9001", "r", w=46)
    xv1 = p.cv(90, yf, "h", "XV-1021", "FC", tag_pos="b", act="s", sis=True)
    xv2 = p.cv(125, yf, "h", "XV-1022", "FC", tag_pos="b", act="s", sis=True)
    pv = p.cv(220, yf, "h", "PV-1021", "FC", tag_pos="b")
    p.proc([(60, yf), (430, yf)], arrow=False, w=0.45)
    for bx in (310, 350, 390, 430):
        p.proc([(bx, yf), (bx, hy0 + hh)], arrow=True, w=0.4)
    p.text("BURNERS (16)", 352, yf + 4, 2.0, color=GREY)
    p.line([(107.5, yf), (107.5, yf + 7)], w=0.3)
    p.cv(107.5, yf + 10, "v", None, act="s", size=2.2, sis=True)
    p.text("VENT XV (FO)", 111, yf + 17, 1.7, color=SIS_RED)
    ft21 = p.bubble(260, 362, "FT-1021", "field", r=4.0, note=["FG FLOW", "(+ WOBBE AT)"], note_pos="l")
    p.line([(260, yf), (260, 358)], w=0.3)
    pt21 = p.bubble(300, 362, "PT-1021", "field", r=4.0)
    p.line([(300, yf), (300, 358)], w=0.3)
    p.bubble(335, 362, "PT-1027", "sis", r=4.0)
    p.line([(335, yf), (335, 358)], w=0.3, color=SIS_RED)
    p.text("A/B/C 2oo3", 340.5, 369, 1.8, color=SIS_RED)
    p.text("SIF-102/103", 340.5, 371.5, 1.8, color=SIS_RED)

    # ---- combustion logic (cross-limiting)
    p.box(232, 386, 408, 150, None, dash="3,1.5", stroke=GREY, sw=0.3, fill="none")
    p.text("FUEL / AIR CROSS-LIMITING (LEAD-LAG) COMBUSTION CONTROL - DCS", 236, 391.5, 2.4, bold=True, color=GREY)
    fx = p.fy(490, 405, "f(x)", "FY-1020A", tag_pos="b")
    p.text("FF: CHARGE x (COT-CIT)", 470, 420, 1.8, color=GREY)
    p.text("+ LEAD-LAG", 470, 422.5, 1.8, color=GREY)
    p.soft([(452, 405), fx["w"]])
    p.text("FIC-1001 PV", 437, 403, 1.8, color=GREY)
    p.text("TI CIT", 437, 407.8, 1.8, color=GREY)
    sm = p.fy(535, 405, "Σ", "FY-1020B", tag_pos="r")
    p.soft([fx["e"], sm["w"]])
    p.sig([tic["s"], (535, 296)], arrow=False)
    p.soft([(535, 310), sm["n"]])
    p.text("FIRING DEMAND", 539, 424, 1.9, bold=True)
    lo = p.fy(440, 445, "<", "FY-1021A", tag_pos="b")
    hi = p.fy(600, 445, ">", "FY-1025A", tag_pos="r")
    p.soft([sm["s"], (535, 428), (440, 428), lo["n"]])
    p.soft([(535, 428), (600, 428), hi["n"]])
    p.dot(535, 428)
    # fuel chain
    fx2 = p.fy(400, 445, "f(x)", "PY-1021A", tag_pos="b")
    hs = p.fy(360, 445, ">", "PY-1021B", tag_pos="b")
    pic = p.bubble(300, 445, "PIC-1021", "dcs", note=["FG PRESSURE", "(SLAVE)"], note_pos="b")
    p.soft([lo["w"], fx2["e"]])
    p.soft([fx2["w"], hs["e"]])
    p.soft([hs["w"], pic["e"]])
    p.text("HEAT -> BURNER P", 384, 456, 1.8, color=GREY)
    p.soft([(360, 430), hs["n"]])
    p.text("MIN-FIRE STOP", 362, 429, 1.8, color=GREY)
    p.sig([pt21["s"], pic["n"]])
    p.sig([pic["w"], (228, 445), (228, 337), (223, 337)])
    # measured fuel heat release
    fhr = p.fy(480, 485, "f(x)", "FY-1021C", tag_pos="b")
    p.sig([ft21["s"], (260, 485), fhr["w"]])
    p.soft([fhr["e"], (565, 485), (565, 445), hi["w"]])
    p.text("FUEL HEAT RELEASE", 487, 482.5, 1.8, color=GREY)
    # air chain
    aa = p.fy(545, 505, "÷", "FY-1025C", tag_pos="b")
    p.sig([ft25["s"], (548, 490), (545, 490), aa["n"]])
    p.soft([aa["w"], (460, 505), (460, 445), lo["e"]])
    p.text("AIR AVAILABLE", 500, 502.5, 1.8, color=GREY)
    mul = p.fy(600, 470, "×", "FY-1025B", tag_pos="l")
    p.soft([hi["s"], mul["n"]])
    aic = p.bubble(628, 470, "AIC-1022", "dcs", note=["O2 TRIM", "±10 %"], note_pos="b")
    p.sig([at["e"], (628, 212), (628, 465)])
    p.soft([aic["w"], mul["e"]])
    fic25 = p.bubble(600, 515, "FIC-1025", "dcs", note=["AIR FLOW"], note_pos="l")
    p.soft([mul["s"], fic25["n"]])
    p.sig([(548, 490), (580, 490), (580, 515), fic25["w"]], arrow=True)
    p.dot(548, 490)
    p.sig([fic25["e"], (612, 515), (612, 395), (622.5, 395), (622.5, 376)])
    p.text("FUEL SP = MIN(DEMAND, AIR AVAILABLE) ; AIR SP = MAX(DEMAND, FUEL ACTUAL) x RATIO x O2 TRIM", 236, 532,
           2.0, color=GREY)

    # ---- BMS/SIS box
    bx = p.box(25, 392, 140, 50, None, stroke=SIS_RED, sw=0.5, fill="none")
    p.text("H-101 BMS / SIS (SIL 2 LOGIC SOLVER)", 29, 398, 2.4, bold=True, color=SIS_RED)
    rows = ["SIF-101 Low-low pass flow (2oo3 per pass)",
            "SIF-102 Low-low FG pressure PT-1027 (2oo3)",
            "SIF-103 High-high FG pressure PT-1027 (2oo3)",
            "SIF-104 Loss of flame BS-1028 (scanners)",
            "SIF-105 High-high arch press. PT-1029 / ID fan",
            "SIF-106 High-high COT TT-1020A/B/C (2oo3)",
            "SIF-901 Unit ESD HS-9000",
            "Actions: close XV-1021/1022 (DB&B, vent opens),",
            "XV-1026 pilot; FD/ID fans to purge position;",
            "PIC-1021/TIC-1020 to manual (tracking);",
            "purge permissive & burner light-off sequence",
            "per NFPA 85/86 / API 556."]
    for i, s in enumerate(rows):
        p.text(s, 29, 405 + i * 3.1, 1.95, color="black" if i < 7 else GREY)
    p.sig([(90, 392), (90, 341)], color=SIS_RED)
    p.sig([(125, 392), (125, 341)], color=SIS_RED)
    p.sig([(107.5, 392), (107.5, 366), (104.5, 366)], color=SIS_RED, arrow=False)

    # ---- stripping steam superheat
    p.bubble(395, 118, "TIC-1024", "dcs", note=["SS COIL", "350 °C"], note_pos="l")

    # ---- right column
    yb = p.legend_isa(RX, 20, RW)
    p.narrative(RX, yb + 4, RW, "CONTROL DESCRIPTION", [
        f"Crude charge master FIC-1001 (CSD-003) sets the base SP of the {npass} pass flow controllers "
        f"FIC-1011..10{10 + npass} through FY-1011A (K = 1/{npass}, {fpp:.1f} t/h per pass).",
        "Pass balancing TDIC-1019 compares pass outlet temperatures TI-1011..1018 and computes biases "
        "FY-1011B..1018B whose sum is forced to zero, so total charge is unchanged; bias clamped ±10 % of "
        "pass flow and frozen when any pass FIC is not in CAS.",
        "COT TIC-1020 (SP from MPC) adds to a feed-forward f(x) of charge x (COT-CIT) with lead-lag "
        "(FY-1020A/B) to form the firing demand.",
        "Cross-limiting: fuel SP = low select of demand and air available (FY-1021A); air SP = high select "
        "of demand and actual fuel heat release (FY-1025A). On load increase air leads fuel; on decrease "
        "fuel leads air - no sub-stoichiometric firing.",
        "Fuel heat demand converted to burner pressure SP (burner curve, Wobbe-corrected, PY-1021A); "
        "min-fire stop PY-1021B; PIC-1021 manipulates PV-1021.",
        "O2 trim AIC-1022 (arch O2 with CO override) multiplies the air/fuel ratio, limited ±10 %. "
        "FIC-1025 positions the FD fan inlet vanes.",
        "Arch draft PIC-1023 (-2.5 mmH2O) split range: ID fan speed 0-50 %, stack damper 50-100 % "
        "(natural-draft fall-back on ID fan trip).",
        "All SIS/BMS functions are independent of the DCS (separate sensors, logic solver and SSOVs).",
    ])
    sh.save(DIR / f"{no}_H-101-Combustion-Control")
    return no




# =============================================================================== CSD-002  C-101
def _pa(p, X1, yr, yd, name, fic, tic, tv, fv, pump, hx, duty_mw, flow_th):
    """Pumparound module right of column (column right wall X1)."""
    xp, xf, xh, xo = X1 + 15, X1 + 40, X1 + 75, X1 + 105
    p.proc([(X1, yd), (X1 + 8, yd), (X1 + 8, yd + 16), (xp - 3.2, yd + 16)], arrow=False)
    pp = p.pump(xp, yd + 16, pump, label_pos="b")
    yq = yd + 12.8
    p.proc([pp["dis"], (xo, yq), (xo, yr), (xh + 4, yr)], arrow=False)
    h = p.hx(xh, yr, None)
    p.text(hx, xh, yr + 7.5, 2.1, "middle", bold=True)
    p.proc([(xh - 4, yr), (X1, yr)], arrow=True)
    # bypass
    p.proc([(xh + 20, yr), (xh + 20, yr - 10), (xh - 20, yr - 10), (xh - 20, yr)], arrow=False, w=0.45)
    t = p.cv(xh, yr - 10, "h", tv, "FO", tag_pos="r")
    p.dot(xh + 20, yr), p.dot(xh - 20, yr)
    ti = p.bubble(X1 + 30, yr - 12, tic, "dcs", r=4.6)
    p.line([(X1 + 30, yr - 7.4), (X1 + 30, yr)], w=0.3)
    p.sig([ti["e"], (X1 + 45, yr - 12), (X1 + 45, yr - 21), (xh, yr - 21), t["a"]])
    m = p.bubble(X1 + 17, yr - 12, "MPC-", "apc", r=3.6)
    p.sig([m["e"], ti["w"]], color=APC_GRN)
    f = p.cv(xf, yq, "h", fv, "FO", tag_pos="b")
    fi = p.bubble(xf, yd - 1, fic, "dcs", r=4.6)
    p.sig([fi["s"], f["a"]])
    p.line([(xf - 8, yq - 1.5), (xf - 8, yq + 1.5)], w=0.45)
    p.sig([(xf - 8, yq), (xf - 8, yd - 1), fi["w"]])
    p.text(f"{name}", xo + 2, yd + 3, 2.3, bold=True)
    p.text(f"{duty_mw:.1f} MW", xo + 2, yd + 6, 1.9, color=GREY)
    p.text(f"{flow_th:.0f} t/h", xo + 2, yd + 8.6, 1.9, color=GREY)


def _stripper(p, X1, yd, tag, ficd, fvd, lic, ficp, fvp, ficst, fvst, fy, pump, prod, flow, steam, an, an_note,
              tray):
    xs = X1 + 155
    p.proc([(X1, yd), (xs, yd)], arrow=True)
    p.text(f"TRAY {tray} DRAW", X1 + 2, yd - 1.5, 1.9, color=GREY)
    fv = p.cv(X1 + 125, yd, "h", fvd, "FO", tag_pos="b")
    fi = p.bubble(X1 + 125, yd - 13, ficd, "dcs", r=4.6)
    p.sig([fi["s"], fv["a"]])
    m = p.bubble(X1 + 111, yd - 13, "MPC-", "apc", r=3.6)
    p.sig([m["e"], fi["w"]], color=APC_GRN)
    p.column(xs, yd - 6, 18, 52, None)
    p.text(tag, xs + 9, yd + 22, 2.4, "middle", bold=True)
    p.proc([(xs + 9, yd - 6), (xs + 9, yd - 15)], arrow=True, w=0.45)
    p.text("VAPOUR TO C-101", xs + 11, yd - 12, 1.8, color=GREY)
    # steam
    ys = yd + 34
    p.util([(X1 + 300, ys), (xs + 18, ys)])
    p.text(f"LP STEAM {steam:.0f} kg/h", X1 + 300, ys - 1.5, 1.8, "end", color=GREY)
    sv = p.cv(X1 + 205, ys, "h", fvst, "FC", tag_pos="b", size=2.8)
    sf = p.bubble(X1 + 205, ys - 13, ficst, "dcs", r=4.6)
    p.sig([sf["s"], sv["a"]])
    y = p.fy(X1 + 250, ys - 13, "×", fy, tag_pos="r")
    p.soft([y["w"], sf["e"]])
    m2 = p.bubble(X1 + 250, ys - 26, "MPC-", "apc", r=3.6)
    p.sig([m2["s"], y["n"]], color=APC_GRN)
    # bottoms
    yb = yd + 58
    p.proc([(xs + 9, yd + 46), (xs + 9, yb), (xs + 11.8, yb)], arrow=False)
    pp = p.pump(xs + 15, yb, pump, label_pos="b")
    yq = yb - 3.2
    p.proc([pp["dis"], (X1 + 320, yq)], arrow=True)
    p.text(f"{prod} {flow:.1f} t/h", X1 + 320, yq - 1.5, 2.0, "end", bold=True)
    pv = p.cv(X1 + 230, yq, "h", fvp, "FC", tag_pos="b")
    pf = p.bubble(X1 + 230, yq - 13, ficp, "dcs", r=4.6)
    p.sig([pf["s"], pv["a"]])
    li = p.bubble(xs - 14, yd + 38, lic, "dcs", r=4.6)
    p.line([(xs - 9.4, yd + 38), (xs, yd + 38)], w=0.3)
    p.soft([li["s"], (xs - 14, yb + 12), (X1 + 222, yb + 12), (X1 + 222, yq - 13), pf["w"]])
    p.soft([pf["e"], (X1 + 250, yq - 13), y["s"]])
    a = p.bubble(X1 + 275, yq + 9, an, "field", r=4.2)
    p.line([(X1 + 275, yq), (X1 + 275, yq + 4.8)], w=0.3)
    p.text(an_note, X1 + 280, yq + 10, 1.8, color=GREY)
    p.text("-> MPC CV", X1 + 280, yq + 12.4, 1.8, color=APC_GRN)


def csd_002():
    sh, p, no = _sheet(1)
    R = pr()
    A = R["atm"]
    S = streams()
    _check_tags(["TIC-1030", "FIC-1031", "PIC-1032", "LIC-1033", "FIC-1034", "LIC-1035", "FFIC-1036", "AIC-1037",
                 "FIC-1040", "TIC-1041", "FIC-1042", "TIC-1043", "FIC-1044", "TIC-1045", "FIC-1050", "LIC-1051",
                 "FIC-1052", "FIC-1054", "FIC-1060", "LIC-1061", "FIC-1062", "FIC-1064", "FIC-1070", "LIC-1071",
                 "FIC-1072", "FIC-1074", "FI-1080", "FIC-1081", "LIC-1082", "FIC-1083"])
    X0, W = 275, 40
    X1 = X0 + W
    xc = X0 + W / 2
    p.column(X0, 60, W, 410, None, None)
    p.text("C-101", X0 - 3, 57, 2.8, "end", bold=True)
    p.text(f"ATM. COLUMN, {A['tray']['bottom']} TRAYS", xc, 474.5, 2.0, "middle", color=GREY)
    p.text(f"TOP {A['T_top']:.0f} °C / {A['P_top_barg']:.2f} barg", xc, 477.5, 2.0, "middle", color=GREY)
    # ------------------------------------------------ overhead
    p.proc([(xc, 60), (xc, 30), (260, 30)], arrow=True)
    p.text(f"OH VAPOUR {S['8']['total_kg_h'] / 1000:.0f} t/h", xc + 2, 26, 2.0, color=GREY)
    p.aircooler(245, 30, 30, "A-101")
    p.proc([(230, 30), (195, 30), (195, 51)], arrow=False)
    p.hx(195, 55, "E-115", label_pos="l")
    p.proc([(195, 59), (195, 95)], arrow=True)
    p.drum(85, 95, 120, 20, "D-102", f"OH DRUM {A['drum_P_barg']:.2f} barg", boot=(100, 12, 10))
    pk = p.box(264, 38, 22, 9, None)
    p.text("X-103", 275, 42, 2.0, "middle", bold=True)
    p.text("NEUTRALISER", 275, 45.4, 1.5, "middle", color=GREY)
    p.util([(275, 38), (275, 30)])
    p.text("FFIC-1036", 275, 50.5, 1.8, "middle", color=GREY)
    # TIC-1030 -> FIC-1031
    p.line([(X0, 66), (260, 66)], w=0.3)
    tic = p.bubble(255, 66, "TIC-1030", "dcs", note=["TOP T", "(NAPHTHA EP)"], note_pos="l")
    m = p.bubble(255, 50, "MPC-", "apc", r=3.6)
    p.sig([m["s"], tic["n"]], color=APC_GRN)
    # reflux
    pp = p.pump(135, 140, "P-103A/B")
    p.proc([(125, 115), (125, 140), (131.8, 140)], arrow=False)
    p.proc([pp["dis"], (265, 136.8), (265, 78), (X0, 78)], arrow=True)
    p.text(f"REFLUX {A['reflux_kg_h'] / 1000:.0f} t/h", 150, 134.5, 2.0, color=GREY)
    fv = p.cv(225, 136.8, "h", "FV-1031", "FO", tag_pos="b")
    fic = p.bubble(225, 121, "FIC-1031", "dcs", r=4.6)
    p.sig([fic["s"], fv["a"]])
    p.soft([tic["s"], (255, 112), (225, 112), fic["n"]])
    # naphtha
    pp4 = p.pump(175, 185, "P-104A/B")
    p.proc([(165, 115), (165, 185), (171.8, 185)], arrow=False)
    p.proc([pp4["dis"], (240, 181.8), (240, 245), (82, 245)], arrow=True)
    p.offpage(22, 245, "UNSTAB. NAPHTHA TO C-105", "CSD-004", "l", w=60)
    fv4 = p.cv(215, 181.8, "h", "FV-1034", "FC", tag_pos="b")
    f4 = p.bubble(215, 166, "FIC-1034", "dcs", r=4.6)
    p.sig([f4["s"], fv4["a"]])
    p.line([(205, 105), (215, 105)], w=0.3)
    l3 = p.bubble(220, 100, "LIC-1033", "dcs", r=4.6, note=["AVERAGING"], note_pos="t")
    p.soft([l3["e"], (245, 100), (245, 166), f4["e"]])
    an = p.bubble(205, 210, "AT-1038", "field", r=4.2)
    p.line([(205, 205.8), (205, 196), (240, 196)], w=0.3)
    p.text("D86 EP / RVP", 199, 216, 1.8, "end", color=GREY)
    p.text("-> MPC CV", 199, 218.4, 1.8, "end", color=APC_GRN)
    # sour water
    p.proc([(106, 127), (106, 165), (88.2, 165)], arrow=False)
    p5 = p.pump(85, 165, "P-105A/B", flip=True, label_pos="r")
    p.proc([p5["dis"], (75, 161.8), (75, 228), (67, 228)], arrow=True)
    p.offpage(22, 228, "SOUR WATER", "TO SWS", "l", w=45)
    lv = p.cv(75, 195, "v", "LV-1035", "FC", tag_pos="r")
    p.line([(100, 121), (60, 121)], w=0.3)
    l5 = p.bubble(55, 121, "LIC-1035", "dcs", r=4.6, note=["BOOT", "INTERFACE"], note_pos="t")
    p.sig([l5["s"], (55, 195), lv["a"]])
    ph = p.bubble(52, 212, "AIC-1037", "dcs", r=4.6, note=["pH 5.5-6.5", "-> FFIC-1036"], note_pos="b")
    p.line([(56.6, 212), (75, 212)], w=0.3)
    # pressure split range
    p.line([(125, 95), (125, 82)], w=0.3)
    pic = p.bubble(125, 77, "PIC-1032", "dcs", r=4.6)
    py = p.fy(105, 62, "SPLIT", "PY-1032", tag_pos="t")
    p.soft([pic["w"], (105, 77), py["s"]])
    p.proc([(112, 95), (112, 48), (62, 48)], arrow=True, w=0.45)
    p.offpage(22, 48, "OFF-GAS TO FG / FLARE", None, "l", w=40)
    pa = p.cv(80, 48, "h", "PV-1032A", "FC", tag_pos="b")
    p.offpage(22, 68, "FG MAKE-UP", None, "l", w=32)
    p.proc([(54, 68), (100, 68), (100, 95)], arrow=True, w=0.45)
    pb = p.cv(64, 68, "h", "PV-1032B", "FC", tag_pos="b")
    p.sig([(101.5, 62), (90, 62), (90, 36), (80, 36), (80, pa["a"][1])])
    p.sig([(105, 58.5), (105, 55), (64, 55), (64, pb["a"][1])])
    # split range graph
    gx, gy, gw, gh = 135, 20, 34, 22
    p.line([(gx, gy), (gx, gy + gh), (gx + gw, gy + gh)], w=0.3)
    p.line([(gx, gy + 2), (gx + gw / 2, gy + gh)], w=0.45)
    p.line([(gx + gw / 2, gy + gh), (gx + gw, gy + 2)], w=0.45)
    p.text("B", gx + 3, gy + 6, 2.0, bold=True)
    p.text("A", gx + gw - 4, gy + 6, 2.0, bold=True)
    p.text("0      50     100 % PIC OUT", gx, gy + gh + 2.6, 1.7, color=GREY)
    p.text("% OPEN", gx - 1, gy + 1, 1.7, "end", color=GREY)
    # ------------------------------------------------ pumparounds
    pa_ = A["pa"]
    _pa(p, X1, 75, 97, "TPA", "FIC-1040", "TIC-1041", "TV-1041", "FV-1040", "P-106A/B", "E-101",
        pa_["TPA"]["duty_kw"] / 1000, pa_["TPA"]["flow"] / 1000)
    _pa(p, X1, 152, 174, "MPA", "FIC-1042", "TIC-1043", "TV-1043", "FV-1042", "P-107A/B", "E-106A/B",
        pa_["MPA"]["duty_kw"] / 1000, pa_["MPA"]["flow"] / 1000)
    _pa(p, X1, 247, 269, "BPA", "FIC-1044", "TIC-1045", "TV-1045", "FV-1044", "P-108A/B", "E-110/E-113",
        pa_["BPA"]["duty_kw"] / 1000, pa_["BPA"]["flow"] / 1000)
    # ------------------------------------------------ side strippers
    st = A["steam"]
    _stripper(p, X1, 125, "C-102", "FIC-1050", "FV-1050", "LIC-1051", "FIC-1052", "FV-1052", "FIC-1054", "FV-1054",
              "FFY-1054", "P-109A/B", "KEROSENE", S["16"]["total_kg_h"] / 1000, st["KERO"], "AT-1055",
              "FLASH / FREEZE", A["tray"]["KERO"])
    _stripper(p, X1, 215, "C-103", "FIC-1060", "FV-1060", "LIC-1061", "FIC-1062", "FV-1062", "FIC-1064", "FV-1064",
              "FFY-1064", "P-110A/B", "DIESEL", S["17"]["total_kg_h"] / 1000, st["DIESEL"], "AT-1065",
              "D86 T95 / CLOUD", A["tray"]["DIESEL"])
    _stripper(p, X1, 305, "C-104", "FIC-1070", "FV-1070", "LIC-1071", "FIC-1072", "FV-1072", "FIC-1074", "FV-1074",
              "FFY-1074", "P-111A/B", "AGO", S["18"]["total_kg_h"] / 1000, st["AGO"], "AT-1075",
              "D86 T95 / COLOUR", A["tray"]["AGO"])
    # ------------------------------------------------ flash zone, overflash, bottoms
    p.offpage(110, 390, "TRANSFER LINE FROM H-101", "CSD-001", "r", w=62)
    p.proc([(110, 390), (X0, 390)], arrow=True)
    p.text(f"FLASH ZONE {A['T_fz']:.0f} °C / {A['P_fz_barg']:.2f} barg", 115, 387.5, 2.0, color=GREY)
    p.line([(X0, 352), (260, 352)], w=0.3)
    of = p.bubble(255, 352, "FI-1080", "dcs", r=4.6,
                  note=["OVERFLASH (WASH-ZONE LIQUID)", "FAL; MPC CONSTRAINT >= 3 vol %", "OF CHARGE"], note_pos="l")
    p.line([(X0, 300), (262, 300)], w=0.3)
    p.line([(X0, 200), (262, 200), (262, 296)], w=0.3)
    p.bubble(255, 300, "PDI-1084", "dcs", r=4.6, note=["SECTION dP", "(FLOODING CV)"], note_pos="l")
    # steam
    p.offpage(110, 440, "MP STEAM (SUPERHEATED)", "H-101 SS COIL", "r", w=62)
    p.util([(110, 440), (X0, 440)])
    p.text(f"{st['bottom']:.0f} kg/h", 232, 438, 1.8, color=GREY)
    sv = p.cv(200, 440, "h", "FV-1081", "FC", tag_pos="b", size=2.8)
    sf = p.bubble(200, 426, "FIC-1081", "dcs", r=4.6)
    p.sig([sf["s"], sv["a"]])
    fy = p.fy(160, 426, "×", "FFY-1081", tag_pos="t")
    p.soft([fy["e"], sf["w"]])
    m3 = p.bubble(140, 426, "MPC-", "apc", r=3.6)
    p.sig([m3["e"], fy["w"]], color=APC_GRN)
    p.text("10 lb/bbl AR", 152, 434, 1.8, color=GREY)
    # bottoms
    p.proc([(xc, 470), (xc, 495), (253.2, 495)], arrow=False)
    p12 = p.pump(250, 495, "P-112A/B", flip=True, label_pos="b")
    p.proc([p12["dis"], (95, 491.8)], arrow=True)
    p.offpage(35, 491.8, "ATM. RESIDUE TO H-201", "CSD-005", "l", w=60)
    p.text(f"{S['19']['total_kg_h'] / 1000:.0f} t/h, {S['19']['T_C']:.0f} °C", 150, 489.5, 2.0, color=GREY)
    fv3 = p.cv(200, 491.8, "h", "FV-1083", "FC", tag_pos="b")
    f3 = p.bubble(200, 478, "FIC-1083", "dcs", r=4.6)
    p.sig([f3["s"], fv3["a"]])
    p.line([(X0, 455), (260, 455)], w=0.3)
    l2 = p.bubble(255, 455, "LIC-1082", "dcs", r=4.6)
    p.soft([l2["s"], (255, 478), f3["e"]])
    p.soft([f3["w"], (160, 478), fy["s"]])
    p.bubble(230, 462, "LT-1082", "sis", r=4.6)
    p.line([(234.6, 462), (240, 462), (240, 458), (X0, 458)], w=0.3, color=SIS_RED)
    p.text("B: LZHH -> SIF-108", 224, 470, 1.8, "end", color=SIS_RED)
    p.text("(TRIP P-101 / XV-1001)", 224, 472.4, 1.8, "end", color=SIS_RED)
    # ------------------------------------------------ quality CV table
    tx, ty = 345, 405
    rows = [("CV (PRODUCT QUALITY)", "MEASUREMENT", "MPC HANDLE (MV)"),
            ("Naphtha D86 EP", "AT-1038 + inferential (TIC-1030, P)", "TIC-1030 SP"),
            ("Kerosene flash / freeze", "AT-1055 + inferential", "FIC-1050, FFY-1054"),
            ("Diesel D86 T95 / cloud", "AT-1065 + inferential", "FIC-1060"),
            ("AGO D86 T95 / colour", "AT-1075 + inferential", "FIC-1070, COT"),
            ("Overflash", "FI-1080", "COT, BPA duty"),
            ("Flooding", "PDI-1084", "PA duties, charge")]
    cw = [72, 72, 56]
    p.box(tx, ty, sum(cw), 6 * len(rows), None, fill="none")
    for i, r in enumerate(rows):
        yy = ty + 6 * i
        if i:
            p.line([(tx, yy), (tx + sum(cw), yy)], w=0.2)
        xx = tx
        for j, c in enumerate(r):
            p.text(c, xx + 1.5, yy + 4.2, 2.0, bold=(i == 0), color=APC_GRN if j == 2 and i else "black")
            xx += cw[j]
    xx = tx
    for c in cw[:-1]:
        xx += c
        p.line([(xx, ty), (xx, ty + 6 * len(rows))], w=0.2)
    p.text("CUT-POINT CONTROL - QUALITY CVs AND MPC HANDLES", tx, ty - 2, 2.4, bold=True)
    # ------------------------------------------------ notes
    yb = p.legend_isa(RX, 20, RW)
    p.narrative(RX, yb + 4, RW, "CONTROL DESCRIPTION", [
        f"Column pressure: PIC-1032 on D-102 ({A['drum_P_barg']:.2f} barg) split range - PV-1032B fuel-gas make-up "
        "0-50 % (closing), PV-1032A off-gas 50-100 % (opening); normally no off-gas, condenser A-101 runs at full "
        "duty (fans auto-variable pitch on TIC trim).",
        "Top temperature TIC-1030 (naphtha end point) cascades to reflux FIC-1031; SP from MPC on the "
        "inferred/analysed naphtha D86 EP (AT-1038). Reflux FIC tracks on loss of TIC.",
        "D-102 HC level LIC-1033 averaging control cascaded to naphtha FIC-1034 (smooth feed to C-105). Boot "
        "interface LIC-1035 tight to LV-1035; pH AIC-1037 trims neutraliser ratio FFIC-1036.",
        "Pumparounds: circulation FIC held (operator/MPC), duty set by return temperature TIC-1041/1043/1045 "
        "via exchanger bypass (crude side kept at full flow); MPC shifts duty TPA <-> MPA <-> BPA for heat "
        "recovery vs. fractionation (gap/overlap).",
        "Side draws are the cut-point handles: draw FIC-1050/1060/1070 SP from MPC on kero flash/freeze, "
        "diesel T95 and AGO quality. Stripper level LIC-10x1 cascades to product FIC-10x2. Stripping "
        "steam ratio FFY-10x4 to product (lb/bbl) - MPC adjusts the ratio for flash point.",
        f"Bottoms: LIC-1082 cascades to AR FIC-1083 (also H-201 charge). Stripping steam FIC-1081 ratioed to AR "
        f"({st['bottom']:.0f} kg/h design).",
        "Overflash FI-1080 (wash-zone liquid) is a hard MPC constraint (>= 3 vol % of charge) and has a low "
        "alarm; COT is raised / BPA duty reduced to restore it. Section dP PDI-1084 = flooding CV.",
        "SIS: LZHH-1082 (SIF-108) stops crude charge (XV-1001, P-101) on column high-high level.",
    ])
    sh.save(DIR / f"{no}_C-101-Column-Control")
    return no




# =============================================================================== CSD-003  desalting / preheat
def csd_003():
    sh, p, no = _sheet(2)
    R = pr()
    P = R["preheat"]
    S = streams()
    _check_tags(["FIC-1001", "FFIC-1002", "FFIC-1003", "TIC-1004", "PDIC-1005", "PDIC-1006", "LIC-1007", "LIC-1008",
                 "PIC-1009", "FFIC-1010", "TIC-1043", "TIC-2017", "TIC-1045"])
    ex = {e["tag"]: e for e in P["exch"]}
    y1 = 80.8
    # ---- row 1: charge + cold train
    p.offpage(55, 80, "CRUDE FROM TANKAGE", "OSBL", "r", w=45)
    p.proc([(55, 80), (60, 80), (60, 84), (66.8, 84)], arrow=False)
    pp = p.pump(70, 84, "P-101A/B")
    p.proc([pp["dis"], (375, y1), (375, 201), (380, 201)], arrow=True)
    p.text(f"{S['1']['std_m3h']:.0f} m3/h ({S['1']['bpsd'] / 1000:.0f} kBPSD), {S['1']['T_C']:.0f} °C", 20, 74, 2.0,
           color=GREY)
    a = p.bubble(84, 96, "AT-1048", "field", r=4.2, note=["API / SALT / BS&W", "(CRUDE SWITCH DV)"], note_pos="b")
    p.line([(84, y1), (84, 91.8)], w=0.3)
    p.line([(94, y1 - 1.5), (94, y1 + 1.5)], w=0.45)
    fv = p.cv(108, y1, "h", "FV-1001", "FC", tag_pos="b")
    fic = p.bubble(108, 64, "FIC-1001", "dcs", note=["CHARGE", "MASTER"], note_pos="l")
    p.sig([(94, y1), (94, 64), (103, 64)], arrow=True) if False else p.sig([(94, y1), (94, 70), (103, 70), (103, 66)])
    p.sig([fic["s"], fv["a"]])
    m = p.bubble(108, 49, "MPC-", "apc", r=3.6)
    p.sig([m["s"], fic["n"]], color=APC_GRN)
    p.cv(128, y1, "h", "XV-1001", "FC", tag_pos="b", act="s", sis=True)
    p.text("SIF-108", 132, y1 - 6.5, 1.8, color=SIS_RED)
    # ratio / FF bus
    p.soft([fic["e"], (120, 64), (120, 40), (585, 40)], arrow=True)
    p.offpage(640, 40, "TO FY-1011A / FY-1020A, MPC", "CSD-001 / 006", "r", w=55)
    p.text("FIC-1001 CHARGE RATE  -  RATIO / FEED-FORWARD BUS", 160, 37.5, 2.1, bold=True)
    # demulsifier
    p.box(140, 92, 22, 9, None)
    p.text("X-101", 151, 96.3, 2.0, "middle", bold=True)
    p.text("DEMULSIFIER", 151, 99.6, 1.5, "middle", color=GREY)
    p.util([(151, 92), (151, y1)])
    r2 = p.bubble(172, 58, "FFIC-1002", "dcs", r=4.6)
    p.soft([(172, 40), r2["n"]])
    p.dot(172, 40)
    p.sig([r2["s"], (172, 96), (162, 96)])
    # cold exchangers
    xs = [("E-101", 195), ("E-102", 222), ("E-103", 249), ("E-104", 276)]
    for t, x in xs:
        p.hx(x, y1, t, label_pos="b", duty=f"{ex[t]['hot']} {ex[t]['Q_kw'] / 1000:.1f} MW")
    p.text(f"{ex['E-101']['Tc_in']:.0f} °C", 180, y1 - 2, 1.9, color=GREY)
    # E-105 with crude bypass
    h5 = p.hx(315, y1, "E-105", label_pos="b", duty=f"VR {ex['E-105']['Q_kw'] / 1000:.1f} MW")
    p.proc([(298, y1), (298, y1 - 13), (332, y1 - 13), (332, y1)], arrow=False, w=0.45)
    p.dot(298, y1), p.dot(332, y1)
    tv = p.cv(315, y1 - 13, "h", "TV-1004", "FO", tag_pos="l")
    tic = p.bubble(352, y1 - 16, "TIC-1004", "dcs", note=["DESALTER T", "125-145 °C"], note_pos="r")
    p.line([(352, y1), (352, y1 - 11)], w=0.3)
    p.sig([tic["n"], (352, 56), (315, 56), tv["a"]])
    p.text(f"{P['T_desalter']:.0f} °C", 360, y1 + 4, 1.9, color=GREY)
    # ---- row 2: desalters
    pdv = p.cv(375, 150, "v", "PDV-1005", None, tag_pos="r")
    pd = p.bubble(350, 150, "PDIC-1005", "dcs", r=4.6, note=["MIX VALVE dP", "0.5-1.5 bar"], note_pos="b")
    p.sig([pd["e"], pdv["a"]])
    tx = p.desalter(380, 190, 100, 22, "D-101A", "1ST STAGE DESALTER")
    p.proc([(450, 190), (450, 165), (495, 165), (495, 201), (500, 201)], arrow=True)
    pdv2 = p.cv(495, 183, "v", "PDV-1006", None, tag_pos="r")
    pd2 = p.bubble(470, 183, "PDIC-1006", "dcs", r=4.6)
    p.sig([pd2["e"], pdv2["a"]])
    tx2 = p.desalter(500, 190, 100, 22, "D-101B", "2ND STAGE DESALTER")
    # wash water
    p.proc([(640, 144), (618.2, 144)], arrow=False, w=0.45)
    p.text("STRIPPED SW", 625, 141.5, 1.7, color=GREY)
    p14 = p.pump(615, 144, None, flip=True)
    p.text("P-114A/B", 615, 153, 2.0, "middle", bold=True)
    p.proc([p14["dis"], (495, 140.8), (495, 165)], arrow=True, w=0.45)
    p.hx(590, 140.8, "E-118", label_pos="t")
    p.text(f"WASH WATER {S['3']['total_kg_h'] / 1000:.0f} t/h (5 vol %)", 500, 138.5, 1.9, color=GREY)
    fv3 = p.cv(555, 140.8, "h", "FV-1003", "FC", tag_pos="b", size=2.8)
    f3 = p.bubble(555, 124, "FFIC-1003", "dcs", r=4.6)
    p.sig([f3["s"], fv3["a"]])
    p.soft([(555, 40), f3["n"]])
    p.dot(555, 40)
    # D-101B brine recycle to D-101A
    p.proc([(580, 212), (580, 235), (365, 235), (365, 130), (375, 130)], arrow=True, w=0.45)
    lv8 = p.cv(540, 235, "h", "LV-1008", "FC", tag_pos="b", size=2.8)
    l8 = p.bubble(520, 222, "LIC-1008", "dcs", r=4.6)
    p.line([(520, 212), (520, 217.4)], w=0.3)
    p.sig([l8["e"], (540, 222), lv8["a"]])
    p.text("2ND STAGE BRINE RECYCLE (COUNTER-CURRENT WASH)", 420, 232.5, 1.8, color=GREY)
    # D-101A brine
    p.proc([(400, 212), (400, 262), (80, 262)], arrow=True, w=0.45)
    p.offpage(20, 262, "BRINE TO E-118 / ETP", None, "l", w=60)
    lv7 = p.cv(360, 262, "h", "LV-1007", "FC", tag_pos="b", size=2.8)
    l7 = p.bubble(440, 240, "LIC-1007", "dcs", r=4.6, note=["INTERFACE", "(GWR + PROFILER)"], note_pos="r")
    p.line([(440, 212), (440, 235.4)], w=0.3)
    p.sig([l7["w"], (360, 240), lv7["a"]])
    p.text(f"{S['4']['total_kg_h'] / 1000:.0f} t/h", 300, 260, 1.9, color=GREY)
    an = p.bubble(250, 275, "AT-1049", "field", r=4.2, note=["OIL-IN-WATER"], note_pos="r")
    p.line([(250, 262), (250, 270.8)], w=0.3)
    # SIS transformer trips
    for (xx, yy), lt, xy in ((tx, "LT-1007", "XY-1007"), (tx2, "LT-1008", "XY-1008")):
        b = p.bubble(xx - 25, yy - 4, lt, "sis", r=4.6)
        p.text("B: LZLL -> SIF-107", xx - 20, yy - 13, 1.8, color=SIS_RED)
        p.text(f"TRIP TRANSFORMER {xy}", xx - 20, yy - 10.6, 1.8, color=SIS_RED)
        p.sig([b["e"], (xx - 3.3, yy - 4)], color=SIS_RED)
    # PIC-1009
    p.proc([(580, 190), (580, 170), (625, 170), (625, 334), (618.2, 334)], arrow=False)
    pv9 = p.cv(625, 200, "v", "PV-1009", "FO", tag_pos="r", size=2.8)
    p9 = p.bubble(605, 200, "PIC-1009", "dcs", r=4.6)
    p.sig([p9["e"], pv9["a"]])
    p.line([(625, 183), (605, 183), (605, 195.4)], w=0.3)
    for k, (t, nt) in enumerate((("AT-1046", "SALT-IN-CRUDE"), ("AT-1047", "BS&W"))):
        yy = 255 + 22 * k
        p.bubble(634, yy, t, "field", r=4.2)
        p.line([(625, yy), (629.8, yy)], w=0.3)
        p.text(nt, 628, yy + 7.8, 1.8, "end", color=GREY)
    p.text("DESALTED CRUDE", 623, 300, 1.8, "end", color=GREY)
    p.text(f"{S['5']['total_kg_h'] / 1000:.0f} t/h", 623, 302.6, 1.8, "end", color=GREY)
    # ---- row 3: hot train (right to left)
    y3 = 330.8
    p102 = p.pump(615, 334, None, flip=True)
    p.text("P-102A/B", 615, 343, 2.0, "middle", bold=True)
    p.proc([p102["dis"], (85, y3)], arrow=True)
    p.offpage(20, y3, "CRUDE TO H-101 PASSES", "CSD-001", "l", w=65)
    p.box(578, 343, 22, 9, None)
    p.text("X-102", 589, 347.3, 2.0, "middle", bold=True)
    p.text("CAUSTIC (FFIC-1010)", 589, 350.6, 1.4, "middle", color=GREY)
    p.util([(589, 343), (589, y3)])
    hot = [("E-106", 545, "MPA", "TIC-1043"), ("E-107", 505, "DIESEL", None), ("E-108", 465, "HVGO", "TIC-2017"),
           ("E-109", 425, "AGO", None), ("E-110", 385, "BPA", "TIC-1045"), ("E-111", 345, "VR", None)]
    for t, x, hs, tc in hot:
        p.hx(x, y3, t, label_pos="t", duty=None)
        p.text(f"{hs} {ex[t]['Q_kw'] / 1000:.1f} MW", x, y3 + 7, 1.8, "middle", color=GREY)
        if tc:
            p.text(f"{tc} (PA DUTY)", x, y3 + 9.6, 1.7, "middle", color=APC_GRN)
        p.text(f"{ex[t]['Tc_out']:.0f} °C", x - 20, y3 - 1.5, 1.7, "middle", color=GREY)
    ti = p.bubble(300, y3 - 14, "TI-1019", "field", r=4.2, note=[f"CIT {P['CIT']:.0f} °C"], note_pos="r") \
        if False else p.bubble(300, y3 - 14, "TT-1050", "field", r=4.2)
    p.line([(300, y3), (300, y3 - 9.8)], w=0.3)
    p.text(f"CIT {P['CIT']:.0f} °C -> MPC (FF TO COT)", 306, y3 - 13, 1.9, color=APC_GRN)
    # ---- inset table: preheat temperature controls
    tx0, ty0 = 30, 390
    rows = [("LOOP", "SERVICE / ACTION", "LIMITS"),
            ("TIC-1004", "Desalter inlet T via E-105 crude bypass TV-1004", "125-145 °C"),
            ("PDIC-1005/1006", "Mixing-valve dP (emulsion / salt removal)", "0.5-1.5 bar"),
            ("LIC-1007/1008", "Interface level, brine LV (tight, ±5 %)", "LZLL SIF-107"),
            ("PIC-1009", "Desalter pressure > crude bubble point + 1.5 bar", f"{S['5']['P_barg']:.1f} barg"),
            ("FFIC-1003", "Wash water ratio to FIC-1001", "4-6 vol %"),
            ("FFIC-1002/1010", "Demulsifier / caustic ratio to FIC-1001", "ppm"),
            ("TIC-1043/1045/2017", "PA return T via exchanger PA-side bypass", "MPC duty"),
            ("FIC-1001", "Unit throughput (MPC MV, max-feed push)", "50-110 %")]
    cw = [42, 110, 34]
    for i, r in enumerate(rows):
        yy = ty0 + 6 * i
        xx = tx0
        for j, c in enumerate(r):
            p.text(c, xx + 1.5, yy + 4.2, 2.0, bold=(i == 0))
            xx += cw[j]
        p.line([(tx0, yy), (tx0 + sum(cw), yy)], w=0.2)
    p.line([(tx0, ty0 + 6 * len(rows)), (tx0 + sum(cw), ty0 + 6 * len(rows))], w=0.2)
    xx = tx0
    for c in [0] + cw:
        xx += c
        p.line([(xx, ty0), (xx, ty0 + 6 * len(rows))], w=0.2)
    p.text("PREHEAT & DESALTING - REGULATORY LOOPS", tx0, ty0 - 2, 2.4, bold=True)
    yb = p.legend_isa(RX, 20, RW)
    p.narrative(RX, yb + 4, RW, "CONTROL DESCRIPTION", [
        "FIC-1001 is the unit throughput master (operator or MPC SP). Its PV/SP is broadcast as ratio/feed-forward "
        "bus to demulsifier, wash water, caustic, heater passes (CSD-001) and the COT feed-forward.",
        "Desalter temperature TIC-1004 (125-145 °C) positions the crude-side bypass of E-105; the VR side always "
        "flows. High temperature increases conductivity and grid current, low temperature impairs separation.",
        "Mix-valve dP PDIC-1005/1006 set by operator 0.5-1.5 bar; optimised against salt-in-crude AT-1046 and "
        "oil-in-brine AT-1049 (no closed loop on analysers).",
        "Interface LIC-1007/1008 (guided-wave radar with density profiler backup) - tight control; 2nd stage brine "
        "recycled counter-currently to 1st stage. Low-low interface (SIF-107) trips the transformers.",
        "PIC-1009 holds the desalter pressure above crude vapour pressure at P-102 suction.",
        "Hot-train exchanger bypasses are on the pumparound (hot) side and belong to PA duty control "
        "(CSD-002/005). CIT is a disturbance to the H-101 COT loop (feed-forward).",
        "Crude switch: AT-1048 (density / salt) or tank-change signal triggers the MPC crude-switch "
        "feed-forward and the desalter chemical ratio presets.",
    ])
    sh.save(DIR / f"{no}_Desalting-Preheat-Control")
    return no


# =============================================================================== CSD-004  C-105 / C-106
def _table(p, x, y, rows, cw, title=None, size=2.0, rh=6.0, hl_col=None):
    for i, r in enumerate(rows):
        yy = y + rh * i
        xx = x
        for j, c in enumerate(r):
            col = APC_GRN if (hl_col is not None and j == hl_col and i) else "black"
            p.text(c, xx + 1.5, yy + rh * 0.7, size, bold=(i == 0), color=col)
            xx += cw[j]
        p.line([(x, yy), (x + sum(cw), yy)], w=0.2)
    p.line([(x, y + rh * len(rows)), (x + sum(cw), y + rh * len(rows))], w=0.2)
    xx = x
    for c in [0] + list(cw):
        xx += c
        p.line([(xx, y), (xx, y + rh * len(rows))], w=0.2)
    if title:
        p.text(title, x, y - 2, 2.4, bold=True)
    return y + rh * len(rows)


def csd_004():
    sh, p, no = _sheet(3)
    R = pr()
    st, sp = R["stab"], R["split"]
    S = streams()
    _check_tags(["PIC-1091", "LIC-1092", "FIC-1093", "FIC-1094", "TIC-1095", "FIC-1096", "LIC-1097", "LIC-1098",
                 "PIC-1100", "LIC-1101", "FIC-1102", "FIC-1103", "TIC-1104", "FIC-1105", "LIC-1106", "FIC-1107"])
    # ------------------------------------------------ C-105
    X0, W, yt, yb = 70, 22, 80, 330
    cx = X0 + W / 2
    p.column(X0, yt, W, yb - yt, None)
    p.text("C-105", X0 - 2, 76, 2.8, "end", bold=True)
    p.text(f"STABILISER {st['N_actual']} TRAYS", X0 + W + 2, yb + 4, 1.9, color=GREY)
    p.text(f"{st['P_top']:.1f} bar(a) TOP", X0 + W + 2, yb + 6.6, 1.9, color=GREY)
    p.offpage(66, 230, "UNSTAB. NAPHTHA", "FIC-1034 (CSD-002)", "r", w=44)
    p.proc([(66, 230), (X0, 230)], arrow=True)
    p.text(f"{S['11']['total_kg_h'] / 1000:.0f} t/h", 24, 224, 1.9, color=GREY)
    # overhead + hot vapour bypass
    p.proc([(cx, yt), (cx, 40), (125, 40)], arrow=False)
    p.aircooler(140, 40, 30, "A-106")
    p.proc([(155, 40), (165, 40), (165, 70)], arrow=True)
    p.drum(150, 70, 65, 18, "D-105", None, label_pos="t")
    p.proc([(100, 40), (100, 62), (190, 62), (190, 70)], arrow=True, w=0.45)
    p.dot(100, 40)
    pv = p.cv(122, 62, "h", "PV-1091", "FO", tag_pos="b", size=2.8)
    pic = p.bubble(122, 49, "PIC-1091", "dcs", r=4.6, note=["HOT-VAPOUR", "BYPASS"], note_pos="l")
    p.sig([pic["s"], pv["a"]])
    p.line([(205, 70), (205, 49), (126.6, 49)], w=0.3)
    p.text("FLOODED A-106", 160, 33, 1.8, color=GREY)
    p.bubble(55, 92, "PT-1091", "sis", r=4.6)
    p.line([(59.6, 92), (X0, 92)], w=0.3, color=SIS_RED)
    p.text("B: PZHH -> SIF-110", 49, 100, 1.8, color=SIS_RED)
    p.text("CLOSE XV-1096", 49, 102.4, 1.8, color=SIS_RED)
    # reflux / LPG
    p.proc([(175, 88), (175, 105), (181.8, 105)], arrow=False)
    pp = p.pump(185, 105, "P-115A/B")
    p.proc([pp["dis"], (285, 101.8)], arrow=True)
    p.offpage(320, 101.8, "LPG TO OSBL", None, "r", w=35)
    p.text(f"LPG {S['30']['total_kg_h'] / 1000:.1f} t/h", 240, 99.5, 1.9, color=GREY)
    fv = p.cv(262, 101.8, "h", "FV-1093", "FC", tag_pos="b", size=2.8)
    f = p.bubble(262, 88, "FIC-1093", "dcs", r=4.6)
    p.sig([f["s"], fv["a"]])
    p.line([(215, 79), (227.4, 79)], w=0.3)
    l = p.bubble(232, 79, "LIC-1092", "dcs", r=4.6)
    p.soft([l["e"], (250, 79), (250, 88), f["w"]])
    a = p.bubble(300, 116, "AT-1099", "field", r=4.2, note=["LPG C5+ (GC)"], note_pos="r")
    p.line([(300, 101.8), (300, 111.8)], w=0.3)
    p.proc([(228, 101.8), (228, 118), (104, 118), (104, 88), (X0 + W, 88)], arrow=True)
    p.dot(228, 101.8)
    p.text(f"REFLUX {st['reflux'] / 1000:.1f} t/h", 160, 116, 1.9, color=GREY)
    fv = p.cv(150, 118, "h", "FV-1094", "FO", tag_pos="b", size=2.8)
    f = p.bubble(150, 104, "FIC-1094", "dcs", r=4.6)
    p.sig([f["s"], fv["a"]])
    fy = p.fy(125, 104, "×", "FFY-1094", tag_pos="l")
    p.soft([fy["e"], f["w"]])
    p.soft([(125, 130), fy["s"]])
    p.text("FEED (FIC-1034 PV)", 127, 133, 1.8, color=GREY)
    m = p.bubble(125, 90, "MPC-", "apc", r=3.4)
    p.sig([m["s"], fy["n"]], color=APC_GRN)
    # sensitive tray TIC-1095 -> FIC-1096 reboiler steam
    yT = yt + 5 + (st['N_actual'] - 4) * (yb - yt - 10) / st['N_actual']
    p.line([(X0 + W, yT), (112, yT)], w=0.3)
    tic = p.bubble(117, yT, "TIC-1095", "dcs", r=4.6, note=["SENSITIVE TRAY", "(RVP CONTROL)"], note_pos="r")
    m = p.bubble(117, yT - 14, "MPC-", "apc", r=3.4)
    p.sig([m["s"], tic["n"]], color=APC_GRN)
    p.proc([(X0 + W, 318), (110, 318), (110, 309)], arrow=False, w=0.45)
    p.hx(110, 305, "E-116", label_pos="l")
    p.proc([(110, 301), (110, 292), (X0 + W, 292)], arrow=True, w=0.45)
    p.util([(230, 305), (114, 305)])
    p.text("HP STEAM", 232, 306, 1.9)
    sv = p.cv(170, 305, "h", "FV-1096", "FC", tag_pos="b", size=2.8)
    sf = p.bubble(170, 291, "FIC-1096", "dcs", r=4.6)
    p.sig([sf["s"], sv["a"]])
    p.soft([tic["s"], (117, 278), (170, 278), sf["n"]])
    p.cv(200, 305, "h", "XV-1096", "FC", tag_pos="b", act="s", sis=True, size=2.8)
    p.text("COND. POT LIC-1098", 140, 318, 1.8, color=GREY)
    # bottoms -> C-106
    p.line([(X0, 322), (54.6, 322)], w=0.3)
    lb = p.bubble(50, 322, "LIC-1097", "dcs", r=4.6)
    p.proc([(cx, yb), (cx, 350), (300, 350), (300, 240), (345, 240)], arrow=True)
    p.hx(120, 350, "E-114", label_pos="t")
    p.text("FEED / BOTTOMS", 120, 357, 1.8, "middle", color=GREY)
    lv = p.cv(170, 350, "h", "LV-1097", "FC", tag_pos="b", size=2.8)
    p.sig([lb["s"], (50, 340), (170, 340), lv["a"]])
    p.text(f"STAB. NAPHTHA {S['31']['total_kg_h'] / 1000:.0f} t/h, {S['31']['T_C']:.0f} °C", 200, 348, 1.9, color=GREY)
    # ------------------------------------------------ C-106
    X0, W, yt, yb = 345, 28, 70, 400
    cx = X0 + W / 2
    p.column(X0, yt, W, yb - yt, None)
    p.text("C-106", X0 - 2, 66, 2.8, "end", bold=True)
    p.text(f"SPLITTER {sp['N_actual']} TRAYS", X0 - 2, yb + 4, 1.9, "end", color=GREY)
    p.text(f"{sp['P_top']:.1f} bar(a) TOP", X0 - 2, yb + 6.6, 1.9, "end", color=GREY)
    p.proc([(cx, yt), (cx, 40), (405, 40)], arrow=False)
    p.aircooler(420, 40, 30, "A-107")
    p.proc([(435, 40), (465, 40), (465, 70)], arrow=True)
    p.drum(445, 70, 65, 18, "D-106", None, label_pos="t")
    pv = p.cv(465, 55, "v", "PV-1100", "FO", tag_pos="r", size=2.8)
    pic = p.bubble(445, 55, "PIC-1100", "dcs", r=4.6, note=["FLOODED", "CONDENSER"], note_pos="l")
    p.sig([pic["e"], pv["a"]])
    p.line([(cx, 50), (445, 50), (445, 50.4)], w=0.3)
    p.proc([(470, 88), (470, 105), (476.8, 105)], arrow=False)
    pp = p.pump(480, 105, "P-116A/B")
    p.proc([pp["dis"], (600, 101.8)], arrow=True)
    p.offpage(640, 101.8, "LIGHT NAPHTHA", "OSBL", "r", w=40)
    p.text(f"LN {S['32']['total_kg_h'] / 1000:.1f} t/h", 548, 99.5, 1.9, color=GREY)
    fv = p.cv(570, 101.8, "h", "FV-1102", "FC", tag_pos="b", size=2.8)
    f = p.bubble(570, 88, "FIC-1102", "dcs", r=4.6)
    p.sig([f["s"], fv["a"]])
    p.line([(510, 79), (522.4, 79)], w=0.3)
    l = p.bubble(527, 79, "LIC-1101", "dcs", r=4.6)
    p.soft([l["e"], (550, 79), (550, 88), f["w"]])
    p.bubble(590, 118, "AT-1108", "field", r=4.2, note=["LN C6+ / RVP"], note_pos="b")
    p.line([(590, 101.8), (590, 113.8)], w=0.3)
    p.proc([(520, 101.8), (520, 120), (381, 120), (381, 85), (X0 + W, 85)], arrow=True)
    p.dot(520, 101.8)
    p.text(f"REFLUX {sp['reflux'] / 1000:.0f} t/h", 470, 118, 1.9, color=GREY)
    fv = p.cv(430, 120, "h", "FV-1103", "FO", tag_pos="b", size=2.8)
    f = p.bubble(430, 106, "FIC-1103", "dcs", r=4.6)
    p.sig([f["s"], fv["a"]])
    m = p.bubble(414, 106, "MPC-", "apc", r=3.4)
    p.sig([m["e"], f["w"]], color=APC_GRN)
    # sensitive tray / reboiler
    yT = yt + 5 + 29 * (yb - yt - 10) / sp['N_actual']
    p.line([(X0 + W, yT), (388.4, yT)], w=0.3)
    tic = p.bubble(393, yT, "TIC-1104", "dcs", r=4.6, note=["SENSITIVE", "TRAY 30"], note_pos="t")
    m = p.bubble(410, yT - 14, "MPC-", "apc", r=3.4)
    p.sig([m["s"], (410, yT), tic["e"]], color=APC_GRN)
    p.proc([(X0 + W, 392), (395, 392), (395, 384)], arrow=False, w=0.45)
    p.hx(395, 380, "E-117", label_pos="r")
    p.proc([(395, 376), (395, 366), (X0 + W, 366)], arrow=True, w=0.45)
    p.util([(500, 380), (399, 380)])
    p.text("MP STEAM", 502, 381, 1.9)
    sv = p.cv(460, 380, "h", "FV-1105", "FC", tag_pos="b", size=2.8)
    sf = p.bubble(460, 366, "FIC-1105", "dcs", r=4.6)
    p.sig([sf["s"], sv["a"]])
    p.soft([tic["s"], (393, 345), (460, 345), sf["n"]])
    p.proc([(cx, yb), (cx, 425), (476.8, 425)], arrow=False)
    pp = p.pump(480, 425, "P-117A/B")
    p.proc([pp["dis"], (600, 421.8)], arrow=True)
    p.offpage(640, 421.8, "HEAVY NAPHTHA", "A-108 / OSBL", "r", w=40)
    p.text(f"HN {S['33']['total_kg_h'] / 1000:.1f} t/h", 548, 419.5, 1.9, color=GREY)
    fv = p.cv(530, 421.8, "h", "FV-1107", "FC", tag_pos="b", size=2.8)
    f = p.bubble(530, 408, "FIC-1107", "dcs", r=4.6)
    p.sig([f["s"], fv["a"]])
    p.line([(X0, 390), (329.6, 390)], w=0.3)
    l = p.bubble(325, 390, "LIC-1106", "dcs", r=4.6)
    p.soft([l["s"], (325, 440), (515, 440), (515, 408), f["w"]])
    p.bubble(590, 436, "AT-1109", "field", r=4.2, note=["HN IBP / C5-"], note_pos="b")
    p.line([(590, 421.8), (590, 431.8)], w=0.3)
    # ------------------------------------------------ dual composition table
    rows = [("COLUMN", "CV (TOP)", "CV (BOTTOM)", "MV (TOP)", "MV (BOTTOM)", "PRESSURE"),
            ("C-105", "LPG C5+ (AT-1099)", "Naphtha RVP (TIC-1095 / infer.)", "FFY-1094 L/F", "TIC-1095 SP",
             "PIC-1091 (min P)"),
            ("C-106", "LN C6+ (AT-1108)", "HN C5- / IBP (AT-1109)", "FIC-1103", "TIC-1104 SP", "PIC-1100 (float)")]
    _table(p, 30, 470, rows, [20, 34, 52, 30, 30, 30], "DUAL-COMPOSITION STRATEGY (MPC 2x2 WITH DECOUPLING)",
           hl_col=None)
    yb_ = p.legend_isa(RX, 20, RW)
    p.narrative(RX, yb_ + 4, RW, "CONTROL DESCRIPTION", [
        "C-105 pressure PIC-1091 by hot-vapour bypass PV-1091 around the flooded condenser A-106; normally "
        "no off-gas (total condenser). C-106 pressure PIC-1100 on the flooded-condenser outlet PV-1100, "
        "set as low as A-107 allows (floating pressure under MPC).",
        "Material balance: reflux-drum levels LIC-1092/1101 cascade to distillate product FIC-1093/1102 "
        "(averaging); bottoms levels LIC-1097 (to C-106, averaging - surge for C-106 feed) and LIC-1106 to HN.",
        "Energy balance (bottom): sensitive-tray temperatures TIC-1095 (stage ~15) and TIC-1104 (tray 30), "
        "pressure-compensated, cascade to reboiler steam FIC-1096/1105.",
        "Top quality: reflux on ratio to feed (C-105, FFY-1094) or flow (C-106, FIC-1103).",
        "Dual-composition: MPC moves reflux/(L/F) and tray-temperature SPs on GC analysers (AT-1099, AT-1108, "
        "AT-1109) and inferentials; interaction handled by the MPC model (RGA ~ 2-4 for L-V).",
        "Without MPC: single-ended composition control (tray T) with reflux on ratio - operator trims.",
        "SIF-110: C-105 high-high pressure PZHH-1091 closes reboiler steam XV-1096 (PSV relief load reduction).",
    ])
    sh.save(DIR / f"{no}_Stabiliser-Splitter-Control")
    return no


# =============================================================================== CSD-005  VDU
def _ejector(p, x, y, tag):
    p.gs.add(p.d.polygon([(x - 7, y - 2.5), (x + 7, y - 0.8), (x + 7, y + 0.8), (x - 7, y + 2.5)], fill="white",
                         stroke="black", stroke_width=0.4))
    p.util([(x - 4, y - 9), (x - 4, y - 2)], arrow=True)
    p.text(tag, x, y + 6, 2.1, "middle", bold=True)


def csd_005():
    sh, p, no = _sheet(4)
    R = pr()
    V, H = R["vac"], R["heaters"]["H-201"]
    S = streams()
    _check_tags(["FIC-2001", "FIC-2004", "TIC-2005", "PIC-2006", "FIC-2007", "AIC-2008", "PIC-2010", "FIC-2011",
                 "TIC-2012", "TIC-2013", "LIC-2014", "FIC-2015", "FIC-2016", "TIC-2017", "LIC-2018", "FIC-2019",
                 "FIC-2020", "LIC-2021", "FIC-2022", "FIC-2023", "LIC-2024", "FIC-2025", "TIC-2026", "FIC-2027",
                 "LIC-2028", "LIC-2029", "PIC-2031"])
    X0, W = 270, 36
    X1 = X0 + W
    xc = X0 + W / 2
    p.column(X0, 70, W, 350, None)
    p.gs.add(p.d.rect((xc - 9, 419.5), (18, 50), rx=3, ry=3, fill="white", stroke="black", stroke_width=0.5))
    p.text("C-201", X0 - 2, 67, 2.8, "end", bold=True)
    p.text("VACUUM COLUMN", X0 - 2, 70, 1.9, "end", color=GREY)
    p.text(f"{V['P_top_mbar']:.0f} mbar(a) TOP / {V['P_fz_mbar']:.0f} FZ", X0 - 2, 72.6, 1.9, "end", color=GREY)
    for y0, y1, lbl in ((92, 122, "BED 1 LVGO PA"), (178, 215, "BED 3 HVGO PA"), (140, 165, "BED 2 FRACT."),
                        (266, 288, "BED 4 WASH")):
        p.gs.add(p.d.rect((X0 + 3, y0), (W - 6, y1 - y0), fill="none", stroke=GREY, stroke_width=0.25,
                          stroke_dasharray="1,1"))
        p.text(lbl, xc, (y0 + y1) / 2 + 0.8, 1.7, "middle", color=GREY)
    # ------------------------------------------------ overhead / ejectors
    p.proc([(xc, 70), (xc, 50), (413, 50)], arrow=False)
    p.text(f"OH {V['T_top']:.0f} °C, {S['22']['total_kg_h'] / 1000:.1f} t/h", xc + 2, 47.5, 1.9, color=GREY)
    for xj, xe, tj, te in ((420, 450, "J-201", "E-202"), (480, 510, "J-202", "E-203"), (540, 570, "J-203", "E-204")):
        _ejector(p, xj, 50, tj)
        p.proc([(xj + 7, 50), (xe - 4, 50)], arrow=False, w=0.45)
        p.hx(xe, 50, te, label_pos="t")
        if xe < 570:
            p.proc([(xe + 4, 50), (xj + 53, 50)], arrow=False, w=0.45)
        p.proc([(xe, 54), (xe, 70)], arrow=True, w=0.35)
    p.text("MOTIVE STEAM", 418, 39, 1.8, "end", color=GREY)
    p.drum(440, 70, 160, 16, "D-201", "HOTWELL / SOUR WATER SEPARATOR", label_pos="b")
    p.proc([(574, 50), (604, 50)], arrow=True, w=0.45)
    p.offpage(640, 50, "NCG TO D-202 / H-201", "PIC-2031", "r", w=36)
    # recycle pressure control
    p.proc([(586, 50), (586, 34), (350, 34), (350, 50)], arrow=True, w=0.45)
    p.dot(586, 50)
    pv = p.cv(460, 34, "h", "PV-2010", "FC", tag_pos="b", size=2.8)
    p.text("NCG / STEAM SPILL-BACK", 500, 32, 1.8, color=GREY)
    pic = p.bubble(330, 26, "PIC-2010", "dcs", r=4.6, note=["VACUUM", f"{V['P_top_mbar']:.0f} mbar(a)"], note_pos="l")
    p.line([(xc, 60), (330, 60), (330, 30.6)], w=0.3)
    p.sig([pic["e"], (345, 26), (345, 20), (460, 20), (460, pv["a"][1])])
    for k, (t, s_) in enumerate((("LIC-2028", "SW: LV-2028"), ("LIC-2029", "SLOP OIL: LV-2029"))):
        xx = 520 + 50 * k
        p.line([(xx, 86), (xx, 95.4)], w=0.3)
        p.bubble(xx, 100, t, "dcs", r=4.6)
        p.text(s_, xx + 5.5, 101, 1.7, color=GREY)
    # ------------------------------------------------ LVGO PA + product
    p.proc([(X1, 130), (X1 + 8, 130), (X1 + 8, 148), (X1 + 15.8, 148)], arrow=False)
    p.text("LVGO PAN", X1 + 2, 128.5, 1.8, color=GREY)
    pp = p.pump(X1 + 19, 148, "P-201A/B")
    p.proc([pp["dis"], (600, 144.8)], arrow=True)
    p.text(f"LVGO {S['23']['total_kg_h'] / 1000:.0f} t/h -> E-103 / A-201", 598, 142.5, 1.9, "end", bold=True)
    p.proc([(420, 144.8), (420, 95), (X1, 95)], arrow=True)
    p.dot(420, 144.8)
    p.hx(395, 95, "E-103", label_pos="t")
    p.aircooler(365, 95, 22, None)
    p.text("A-201", 352, 92, 2.1, "end", bold=True)
    fv = p.cv(420, 110, "v", "FV-2011", "FO", tag_pos="r")
    fi = p.bubble(400, 110, "FIC-2011", "dcs", r=4.6)
    p.sig([fi["e"], fv["a"]])
    t12 = p.bubble(345, 72, "TIC-2012", "dcs", r=4.6, note=["TOP T"], note_pos="r")
    p.line([(X1, 72), (340.4, 72)], w=0.3)
    m = p.bubble(360, 72, "MPC-", "apc", r=3.4) if False else None
    t13 = p.bubble(325, 82, "TIC-2013", "dcs", r=4.6)
    p.line([(325, 86.6), (325, 95)], w=0.3)
    p.soft([t12["s"], (345, 82), t13["e"]])
    p.sig([t13["w"], (316, 82), (316, 106), (365, 106), (365, 101.8)])
    p.text("FAN PITCH / BYPASS", 367, 108, 1.8, color=GREY)
    li = p.bubble(318, 120, "LIC-2014", "dcs", r=4.2)
    f15 = p.bubble(480, 131, "FIC-2015", "dcs", r=4.6)
    fv15 = p.cv(480, 144.8, "h", "FV-2015", "FC", tag_pos="b", size=2.8)
    p.sig([f15["s"], fv15["a"]])
    p.soft([li["e"], (470, 120), (470, 131), f15["w"]])
    # ------------------------------------------------ HVGO PA, wash, product
    p.proc([(X1, 230), (X1 + 8, 230), (X1 + 8, 248), (X1 + 15.8, 248)], arrow=False)
    p.text("HVGO PAN", X1 + 2, 228.5, 1.8, color=GREY)
    pp = p.pump(X1 + 19, 248, "P-202A/B")
    p.proc([pp["dis"], (600, 244.8)], arrow=True)
    p.text(f"HVGO {S['24']['total_kg_h'] / 1000:.0f} t/h -> E-108 / A-202", 598, 242.5, 1.9, "end", bold=True)
    p.proc([(420, 244.8), (420, 175), (384, 175)], arrow=False)
    p.dot(420, 244.8)
    p.hx(380, 175, "E-108A-D", label_pos="b")
    p.proc([(376, 175), (X1, 175)], arrow=True)
    p.proc([(400, 175), (400, 165), (360, 165), (360, 175)], arrow=False, w=0.45)
    tv = p.cv(380, 165, "h", "TV-2017", "FO", tag_pos="r", size=2.8)
    t17 = p.bubble(335, 160, "TIC-2017", "dcs", r=4.6)
    p.line([(335, 164.6), (335, 175)], w=0.3)
    p.sig([t17["e"], (350, 160), (350, 154), (380, 154), tv["a"]])
    fv = p.cv(420, 205, "v", "FV-2016", "FO", tag_pos="r")
    fi = p.bubble(400, 205, "FIC-2016", "dcs", r=4.6)
    p.sig([fi["e"], fv["a"]])
    li = p.bubble(318, 217, "LIC-2018", "dcs", r=4.2)
    f19 = p.bubble(500, 231, "FIC-2019", "dcs", r=4.6)
    fv19 = p.cv(500, 244.8, "h", "FV-2019", "FC", tag_pos="b", size=2.8)
    p.sig([f19["s"], fv19["a"]])
    p.soft([li["e"], (490, 217), (490, 231), f19["w"]])
    # wash oil
    p.proc([(360, 244.8), (360, 262), (X1, 262)], arrow=True)
    p.dot(360, 244.8)
    p.text("WASH OIL", 345, 260, 1.8, "middle", color=GREY)
    fv = p.cv(360, 253, "v", "FV-2020", "FC", tag_pos="r", size=2.8)
    f20 = p.bubble(335, 282, "FIC-2020", "dcs", r=4.6, note=["MIN-FLOW"], note_pos="l")
    p.sig([f20["n"], (335, 253), fv["a"]])
    hs = p.fy(375, 282, ">", "FY-2020", tag_pos="b")
    p.soft([hs["w"], f20["e"]])
    m = p.bubble(395, 282, "MPC-", "apc", r=3.4)
    p.sig([m["w"], hs["e"]], color=APC_GRN)
    p.soft([(375, 270), hs["n"]])
    p.text("MIN WETTING f(CHARGE)", 377, 272, 1.8, color=GREY)
    # slop wax
    p.proc([(X1, 300), (X1 + 8, 300), (X1 + 8, 318), (X1 + 15.8, 318)], arrow=False)
    p.text("SLOP WAX PAN", X1 + 2, 298.5, 1.8, color=GREY)
    pp = p.pump(X1 + 19, 318, "P-203A/B")
    p.proc([pp["dis"], (600, 314.8)], arrow=True)
    p.text(f"SLOP WAX {S['25']['total_kg_h'] / 1000:.1f} t/h", 598, 312.5, 1.9, "end", bold=True)
    li = p.bubble(318, 290, "LIC-2021", "dcs", r=4.2)
    f22 = p.bubble(480, 301, "FIC-2022", "dcs", r=4.6)
    fv22 = p.cv(480, 314.8, "h", "FV-2022", "FC", tag_pos="b", size=2.8)
    p.sig([f22["s"], fv22["a"]])
    p.soft([li["e"], (470, 290), (470, 301), f22["w"]])
    # stripping steam + bottoms
    p.offpage(246, 405, "MP STEAM", None, "r", w=24)
    p.util([(246, 405), (X0, 405)])
    sv = p.cv(257, 405, "h", "FV-2023", "FC", tag_pos="b", size=2.6)
    p.bubble(257, 392, "FIC-2023", "dcs", r=4.4, note=["RATIO TO", "CHARGE"], note_pos="l")
    p.sig([(257, 396.4), sv["a"]])
    p.proc([(xc, 469.5), (xc, 490), (X1 + 15.8, 490)], arrow=False)
    pp = p.pump(X1 + 19, 490, "P-204A/B")
    p.proc([pp["dis"], (600, 486.8)], arrow=True)
    p.text(f"VAC. RESIDUE {S['26']['total_kg_h'] / 1000:.0f} t/h -> E-111/E-105", 598, 484.5, 1.9, "end", bold=True)
    f25 = p.bubble(480, 473, "FIC-2025", "dcs", r=4.6)
    fv25 = p.cv(480, 486.8, "h", "FV-2025", "FC", tag_pos="b", size=2.8)
    p.sig([f25["s"], fv25["a"]])
    p.line([(xc - 9, 455), (259.6, 455)], w=0.3)
    l24 = p.bubble(255, 455, "LIC-2024", "dcs", r=4.6)
    p.soft([l24["s"], (255, 505), (470, 505), (470, 473), f25["w"]])
    p.bubble(238, 437, "LT-2024", "sis", r=4.4)
    p.line([(242.4, 437), (xc - 9, 437)], w=0.3, color=SIS_RED)
    p.text("B: LZHH -> SIF-203", 232, 444.5, 1.8, "end", color=SIS_RED)
    p.text("(CLOSE XV-1083)", 232, 446.9, 1.8, "end", color=SIS_RED)
    # quench
    p.proc([(600, 445), (xc + 9, 445)], arrow=True, w=0.45)
    p.text("QUENCH: COOLED VR (E-105 OUTLET)", 598, 443, 1.8, "end", color=GREY)
    fv27 = p.cv(420, 445, "h", "FV-2027", "FC", tag_pos="b", size=2.8)
    f27 = p.bubble(420, 431, "FIC-2027", "dcs", r=4.6)
    p.sig([f27["s"], fv27["a"]])
    p.line([(xc + 9, 460), (330.4, 460)], w=0.3)
    t26 = p.bubble(335, 460, "TIC-2026", "dcs", r=4.6, note=[f"MAX 365 °C"], note_pos="b")
    p.soft([t26["e"], (405, 460), (405, 431), f27["w"]])
    # ------------------------------------------------ H-201
    hx0, hy0, hw, hh = 60, 300, 110, 80
    ht = p.heater(hx0, hy0, hw, hh, "H-201", [f"{H['Q_abs_kw'] / 1000:.1f} MW ABS.",
                                              f"{H['passes']} PASSES, {H['burners']} BURNERS"], conv_h=30)
    cx_, cy_, cw_, ch_ = ht["conv"]
    p.offpage(57, 280, "AR FROM FIC-1083", "CSD-002", "r", w=40)
    p.proc([(57, 280), (cx_, 280)], arrow=True)
    p.text(f"PASS 1 OF {H['passes']} SHOWN (FIC-2001..200{H['passes']})", 20, 290, 1.8, color=GREY)
    fv = p.cv(64, 280, "h", None, None, size=2.4)
    p.text("FV-2001", 64, 286.5, 1.8, "middle")
    p.bubble(64, 267, "FIC-2001", "dcs", r=4.4)
    p.sig([(64, 271.4), fv["a"]])
    p.util([(76, 235), (76, 280)])
    p.text("MP STEAM", 76, 233, 1.8, "middle")
    sv = p.cv(76, 250, "v", None, None, size=2.4)
    p.bubble(55, 250, "FIC-2007", "dcs", r=4.4, note=["COIL STEAM"], note_pos="t")
    p.sig([(59.4, 250), sv["a"]])
    p.proc([(hx0 + hw, 370), (240, 370), (240, 340), (X0, 340)], arrow=True)
    p.text(f"COT {H['T_out']:.0f} °C", 245, 337.5, 1.9, color=GREY)
    p.text(f"VF {H['vf_out']:.2f}", 245, 351, 1.9, color=GREY)
    tt = p.bubble(195, 358, "TT-2005", "field", r=4.0)
    p.line([(195, 370), (195, 362)], w=0.3)
    tic = p.bubble(215, 345, "TIC-2005", "dcs", r=4.6)
    p.sig([tt["n"], (195, 345), tic["w"]])
    m = p.bubble(215, 331, "MPC-", "apc", r=3.4)
    p.sig([m["s"], tic["n"]], color=APC_GRN)
    yf = 400
    p.offpage(57, yf, "FUEL GAS", None, "r", w=26)
    p.proc([(57, yf), (160, yf)], arrow=False, w=0.45)
    for bx in (128.1, 156.0):
        p.proc([(bx, yf), (bx, hy0 + hh)], arrow=True, w=0.4)
    p.cv(72, yf, "h", None, None, act="s", sis=True, size=2.6)
    p.cv(88, yf, "h", None, None, act="s", sis=True, size=2.6)
    p.text("XV-2006A/B", 80, yf + 5.5, 1.8, "middle", color=SIS_RED)
    pv = p.cv(110, yf, "h", "PV-2006", "FC", tag_pos="b", size=3.0)
    pic = p.bubble(140, 420, "PIC-2006", "dcs", r=4.6)
    p.soft([tic["s"], (215, 420), pic["e"]])
    p.sig([pic["w"], (118, 420), (118, 390), (110, 390), (110, pv["a"][1])])
    sx, sy = ht["stack_top"]
    p.line([(sx - 3, 256), (sx + 3, 253)], w=0.5)
    at = p.bubble(190, 305, "AIC-2008", "dcs", r=4.6, note=["O2 -> STACK", "DAMPER"], note_pos="r")
    p.line([(hx0 + hw, 305), (185.4, 305)], w=0.3)
    p.sig([at["n"], (190, 254.5), (sx + 4, 254.5)])
    # SIS box
    p.box(20, 440, 150, 27, None, stroke=SIS_RED, sw=0.5, fill="none")
    p.text("H-201 BMS / SIS", 24, 446, 2.4, bold=True, color=SIS_RED)
    for i, s_ in enumerate(["SIF-201 Low-low pass flow FT-2001..2004 (2oo3)",
                            "SIF-202 Low-low FG press. PT-2009 / flame failure BS-2008",
                            "SIF-203 C-201 high-high level LT-2024B -> XV-1083",
                            "SIF-901 Unit ESD.  Actions: XV-2006A/B close, coil steam",
                            "to max (FV-2007 FO), PIC-2006/TIC-2005 track."]):
        p.text(s_, 24, 451 + 3.2 * i, 1.9)
    p.sig([(80, 440), (80, yf + 7)], color=SIS_RED)
    yb_ = p.legend_isa(RX, 20, RW)
    p.narrative(RX, yb_ + 4, RW, "CONTROL DESCRIPTION", [
        f"Vacuum: PIC-2010 ({V['P_top_mbar']:.0f} mbar(a)) spills non-condensables/steam from the after-condenser "
        "back to the J-201 suction (PV-2010); ejector motive steam on manual (fixed, at design pressure). "
        "Lower pressure is the main lift handle - MPC pushes PIC-2010 SP to its low limit.",
        "H-201: COT TIC-2005 cascades to FG pressure PIC-2006 (same cross-limiting philosophy as H-101); pass "
        "flows FIC-2001..2004 (ratio of FIC-1083) and coil-steam FIC-2007 set velocity / limit cracking.",
        "LVGO: top temperature TIC-2012 cascades to PA return temperature TIC-2013 (A-201 fan pitch / bypass); "
        "PA circulation FIC-2011; pan level LIC-2014 -> product FIC-2015.",
        "HVGO: PA return TIC-2017 by E-108 PA-side bypass (heat recovery to crude); FIC-2016 circulation; pan "
        "level LIC-2018 -> product FIC-2019.",
        "Wash oil FIC-2020 is safety-critical for bed coking: SP = high select of MPC SP and minimum wetting rate "
        "f(charge) (FY-2020); low-flow alarm (high priority).",
        "Bottoms: LIC-2024 -> VR FIC-2025; boot temperature TIC-2026 (<= 365 °C, coking) cascades to cooled-VR "
        "quench FIC-2027. Stripping steam FIC-2023 ratio to charge.",
        "Slop wax LIC-2021 -> FIC-2022 (recycled to H-201 or OSBL).",
    ])
    sh.save(DIR / f"{no}_VDU-Control")
    return no


# =============================================================================== CSD-006  APC / MPC structure
def mpc_tables():
    """MV / CV / DV definitions (shared with the control philosophy report)."""
    R = pr()
    A, V, H1, H2 = R["atm"], R["vac"], R["heaters"]["H-101"], R["heaters"]["H-201"]
    S = streams()
    m3h = S["1"]["std_m3h"]
    mv = [
        ("MV-01", "FIC-1001", "Crude charge", f"{0.5 * m3h:.0f}-{1.1 * m3h:.0f} m3/h", "CDU"),
        ("MV-02", "TIC-1020", "H-101 COT", f"{H1['T_out'] - 10:.0f}-{H1['T_out'] + 6:.0f} °C", "CDU"),
        ("MV-03", "TIC-1030", "C-101 top temperature (naphtha EP)", f"{A['T_top'] - 10:.0f}-{A['T_top'] + 10:.0f} °C", "CDU"),
        ("MV-04", "FIC-1050", "Kerosene draw", "±15 % of design", "CDU"),
        ("MV-05", "FIC-1060", "Diesel draw", "±15 % of design", "CDU"),
        ("MV-06", "FIC-1070", "AGO draw", "±20 % of design", "CDU"),
        ("MV-07", "TIC-1041", "TPA duty (return T)", f"{A['pa']['TPA']['T_ret'] - 10:.0f}-{A['pa']['TPA']['T_ret'] + 25:.0f} °C", "CDU"),
        ("MV-08", "TIC-1043", "MPA duty (return T)", f"{A['pa']['MPA']['T_ret'] - 10:.0f}-{A['pa']['MPA']['T_ret'] + 25:.0f} °C", "CDU"),
        ("MV-09", "TIC-1045", "BPA duty (return T)", f"{A['pa']['BPA']['T_ret'] - 10:.0f}-{A['pa']['BPA']['T_ret'] + 25:.0f} °C", "CDU"),
        ("MV-10", "FFY-1081", "C-101 stripping steam ratio", "6-12 lb/bbl AR", "CDU"),
        ("MV-11", "FFY-1054/1064/1074", "Side-stripper steam ratios", "2-8 lb/bbl", "CDU"),
        ("MV-12", "PIC-1032", "C-101 OH drum pressure", "0.4-1.0 barg", "CDU"),
        ("MV-13", "TIC-2005", "H-201 COT", f"{H2['T_out'] - 12:.0f}-{H2['T_out'] + 4:.0f} °C", "VDU"),
        ("MV-14", "PIC-2010", "C-201 top pressure", f"{V['P_top_mbar'] - 5:.0f}-{V['P_top_mbar'] + 20:.0f} mbar(a)", "VDU"),
        ("MV-15", "TIC-2012", "C-201 top temperature", "55-90 °C", "VDU"),
        ("MV-16", "TIC-2017", "HVGO PA duty (return T)", "±20 °C", "VDU"),
        ("MV-17", "FIC-2020", "Wash oil (>= min wetting)", "min-design x 1.3", "VDU"),
        ("MV-18", "FIC-2023", "C-201 stripping steam", "0-1.5 x design", "VDU"),
        ("MV-19", "FFY-1094 / TIC-1095", "C-105 L/F, sensitive tray T", "±10 % / ±8 °C", "LE"),
        ("MV-20", "FIC-1103 / TIC-1104", "C-106 reflux, sensitive tray T", "±15 % / ±8 °C", "LE"),
    ]
    cv = [
        ("CV-01", "Naphtha D86 EP", "AT-1038 + inferential", "range", "CDU"),
        ("CV-02", "Kerosene flash point", "AT-1055 + inferential", "min limit", "CDU"),
        ("CV-03", "Kerosene freeze point", "inferential (lab bias)", "max limit", "CDU"),
        ("CV-04", "Diesel D86 T95", "AT-1065 + inferential", "max / target", "CDU"),
        ("CV-05", "Diesel cloud point / flash", "inferential (lab bias)", "range", "CDU"),
        ("CV-06", "AGO D86 T95 / colour", "AT-1075 + inferential", "max", "CDU"),
        ("CV-07", "Kero-diesel / diesel-AGO gap", "inferential (5-95 gap)", "min", "CDU"),
        ("CV-08", "Overflash", "FI-1080 / charge", ">= 3 vol %", "CDU"),
        ("CV-09", "Section dP (flooding)", "PDI-1084", "max", "CDU"),
        ("CV-10", "H-101 firing / tube metal T", "FY-1020B OP, TI skin", "max", "CDU"),
        ("CV-11", "H-101 arch O2 / draft", "AIC-1022, PIC-1023", "range", "CDU"),
        ("CV-12", "Valve positions", "FV-1001/1031, TV bypass, PV-1032A", "5-90 %", "ALL"),
        ("CV-13", "A-101 duty / OH temperature", "TI A-101 outlet", "max", "CDU"),
        ("CV-14", "Desalter inlet T", "TIC-1004 OP / PV", "125-145 °C", "CDU"),
        ("CV-15", "LVGO D86 T95 / HVGO CCR, Ni+V", "inferential + lab", "max", "VDU"),
        ("CV-16", "Wash-bed wetting rate", "FIC-2020 / bed area", ">= min", "VDU"),
        ("CV-17", "C-201 flash zone T / bottoms T", "TI flash zone, TIC-2026", "max", "VDU"),
        ("CV-18", "Ejector load / PV-2010 OP", "PIC-2010 OP", "max", "VDU"),
        ("CV-19", "H-201 firing, coil outlet P", "PIC-2006 OP, PI", "max", "VDU"),
        ("CV-20", "LPG C5+ / naphtha RVP", "AT-1099 / TIC-1095 infer.", "max", "LE"),
        ("CV-21", "LN C6+ / HN C5- (IBP)", "AT-1108 / AT-1109", "max", "LE"),
    ]
    dv = [
        ("DV-01", "Crude switch / tank change", "Tank-farm signal (OSBL)"),
        ("DV-02", "Crude API / density, salt, BS&W", "AT-1048"),
        ("DV-03", "Crude inlet T to heater (CIT)", "TT-1050"),
        ("DV-04", "Ambient air temperature", "TT-9005 (air coolers)"),
        ("DV-05", "Fuel-gas Wobbe / LHV", "AT-1021 (FG analyser)"),
        ("DV-06", "MP/LP steam header pressure", "PIC-9004"),
        ("DV-07", "AR rate to VDU", "FIC-1083 PV (feed-forward)"),
    ]
    inf = [
        ("Naphtha D86 EP", "TIC-1030, PIC-1032, reflux/draw ratio", "AT-1038, lab"),
        ("Kerosene flash point", "Draw T, stripper steam ratio, C-101 P", "AT-1055, lab"),
        ("Kerosene freeze point", "Kero draw T, MPA return T, P", "lab"),
        ("Diesel D86 T95", "Diesel draw T (PCT), HC partial pressure", "AT-1065, lab"),
        ("Diesel cloud point", "D86 T95 infer., crude API", "lab"),
        ("AGO D86 T95", "AGO draw T, overflash, steam ratio", "AT-1075, lab"),
        ("Overflash vol %", "Wash-zone liquid FI-1080 / charge", "-"),
        ("LVGO D86 T95", "C-201 top P, TIC-2012, LVGO PA", "lab"),
        ("HVGO CCR / Ni+V", "Wash rate, flash zone T, HVGO cut", "lab"),
        ("Naphtha RVP (C-105)", "TIC-1095, P, feed rate", "lab"),
        ("Atm. residue 370 °C-", "Flash zone T/P, steam ratio", "lab"),
    ]
    return dict(mv=mv, cv=cv, dv=dv, inf=inf)


def csd_006():
    sh, p, no = _sheet(5)
    T = mpc_tables()
    # ---------------- structure
    p.box(230, 20, 180, 14, ["L4  REFINERY PLANNING & SCHEDULING (LP)"], ["crude slate, product prices, unit targets"],
          tsize=2.5, lsize=2.0, fill="#F2F2F2")
    p.box(30, 44, 590, 84, None, fill="none", stroke=APC_GRN, sw=0.6)
    p.text("L3  APC SERVER (REDUNDANT) - MULTIVARIABLE PREDICTIVE CONTROL (DMC-TYPE), CYCLE 1 min", 34, 50, 2.6,
           bold=True, color=APC_GRN)
    p.box(40, 56, 140, 26, ["STEADY-STATE OPTIMISER (LP/QP)"], ["economic targets for MVs/CVs every cycle",
                                                                   "objective: max value (products - energy)"],
          tsize=2.3, lsize=1.9, fill="#EAF4EA")
    p.box(200, 56, 130, 26, ["INFERENTIAL ENGINE"], ["soft sensors (11 models), lab bias update",
                                                       "(LIMS), analyser validation"], tsize=2.3, lsize=1.9,
          fill="#EAF4EA")
    p.box(350, 56, 120, 26, ["CRUDE-SWITCH LOGIC"], ["model gain scheduling, FF presets",
                                                      "triggered by DV-01/DV-02"], tsize=2.3, lsize=1.9, fill="#EAF4EA")
    p.box(490, 56, 120, 26, ["APC HISTORIAN / KPI"], ["service factor, CV limit violations,",
                                                      "benefits tracking"], tsize=2.3, lsize=1.9, fill="#EAF4EA")
    ctl = [("CDU MPC", "MV-01..MV-12 / CV-01..CV-14", "H-101, C-101, strippers, preheat"),
           ("VDU MPC", "MV-13..MV-18 / CV-15..CV-19", "H-201, C-201, ejectors"),
           ("LIGHT-ENDS MPC", "MV-19..MV-20 / CV-20..CV-21", "C-105 stabiliser, C-106 splitter")]
    xs = [40, 245, 450]
    for (t, a, b), x in zip(ctl, xs):
        p.box(x, 90, 160, 30, [t], [a, b], tsize=2.6, lsize=2.0, fill="white", stroke=APC_GRN, sw=0.5)
        p.line([(x + 80, 82), (x + 80, 90)], w=0.3, arrow=True, color=APC_GRN)
    p.line([(320, 34), (320, 44)], w=0.35, arrow=True)
    # firewall
    p.line([(30, 133), (620, 133)], w=0.8, dash="5,2", color=SIS_RED)
    p.text("L3 / L2 FIREWALL - OPC UA (read: PV/OP/mode/limits; write: SP in 'MPC' cascade mode only) - WATCHDOG "
           "HEARTBEAT, SP RATE & MAGNITUDE CLAMPS IN DCS, SHED TO LAST SP ON COMM FAILURE", 34, 131, 1.9, color=SIS_RED)
    # DCS
    p.box(30, 140, 590, 62, None, fill="none", sw=0.6)
    p.text("L2  DCS REGULATORY LAYER (BPCS) - PID CASCADES RECEIVE MPC SETPOINTS ('MPC' MODE / OPERATOR CAN DROP "
           "ANY MV OUT OF MPC)", 34, 146, 2.5, bold=True)
    dcs = [("CDU-1 CONTROLLER PAIR", ["FIC-1001  TIC-1020  FIC-1011..1018", "TIC-1004  PIC-1032  TIC-1030",
                                      "FIC-1031  FFY-1081"]),
           ("CDU-2 CONTROLLER PAIR", ["FIC-1050/1060/1070  FFY-1054/1064/1074", "TIC-1041/1043/1045",
                                      "FFY-1094 TIC-1095 FIC-1103 TIC-1104"]),
           ("VDU CONTROLLER PAIR", ["TIC-2005  PIC-2010  TIC-2012", "TIC-2017  FIC-2020  FIC-2023",
                                    "FIC-2001..2004  TIC-2026"])]
    for (t, ls), x in zip(dcs, xs):
        p.box(x, 152, 160, 44, [t], ls, tsize=2.4, lsize=2.0, fill="white")
    for x in xs:
        p.line([(x + 60, 120), (x + 60, 152)], w=0.45, color=APC_GRN, arrow=True, dash="2,1")
        p.text("MV SPs", x + 62, 127, 1.9, color=APC_GRN)
        p.line([(x + 110, 152), (x + 110, 120)], w=0.45, arrow=True)
        p.text("PV / CV / limits", x + 112, 127, 1.9)
    # field
    p.box(30, 210, 290, 18, ["L0/L1 FIELD: TRANSMITTERS, CONTROL VALVES"], ["4-20 mA / HART via FAR-100 marshalling"],
          tsize=2.3, lsize=1.9, fill="#F2F2F2")
    p.box(330, 210, 290, 18, ["ONLINE ANALYSERS (AH-101) & LAB (LIMS)"],
          ["D86, flash, freeze, GC, RVP, salt, BS&W, O2/CO -> inferential bias"], tsize=2.3, lsize=1.9,
          fill="#F2F2F2")
    p.line([(175, 202), (175, 210)], w=0.35, start_arrow=True, arrow=True)
    p.line([(475, 202), (475, 210)], w=0.35, start_arrow=True, arrow=True)
    p.line([(620, 219), (628, 219), (628, 69), (610, 69)], w=0.35, arrow=True, dash="2,1")
    p.text("LIMS", 629, 150, 1.9, rotate=-90)
    # ---------------- tables
    y0 = 246
    _table(p, 15, y0, [("MV", "DCS TAG (SP)", "DESCRIPTION", "RANGE", "MPC")] + [tuple(r) for r in T["mv"]],
           [12, 34, 54, 34, 12], "MANIPULATED VARIABLES (MV)", size=1.85, rh=5.3, hl_col=1)
    _table(p, 170, y0, [("CV", "CONTROLLED VARIABLE", "MEASUREMENT", "TYPE", "MPC")] + [tuple(r) for r in T["cv"]],
           [12, 52, 56, 22, 12], "CONTROLLED / CONSTRAINT VARIABLES (CV)", size=1.85, rh=5.3)
    yy = _table(p, 333, y0 + 140, [("DV", "DISTURBANCE", "SOURCE")] + [tuple(r) for r in T["dv"]],
                [12, 56, 48], "DISTURBANCE VARIABLES (DV)", size=1.85, rh=5.3)
    _table(p, 333, y0, [("INFERENTIAL (SOFT SENSOR)", "MAIN INPUTS", "BIAS / VALIDATION")] +
           [tuple(r) for r in T["inf"]], [52, 64, 30][:2] + [30], "INFERENTIAL MODELS", size=1.85, rh=5.3)
    p.narrative(RX, 20, RW, "APC DESIGN BASIS", [
        "Three DMC-type MPC applications on a redundant L3 APC server (CDU, VDU, light ends) with a common "
        "steady-state LP optimiser; 1-minute execution, prediction horizon ~ 2 x longest settling time "
        "(CDU ~ 180 min).",
        "Models identified by step testing (2-3 weeks per application) after regulatory tuning audit; "
        "crude-type gain scheduling (light / heavy blends).",
        "Priority of CV ranks: (1) safety / equipment limits (heater, flooding, wash-oil wetting, valve "
        "saturation), (2) product specifications, (3) economic optimisation (maximise diesel / HVGO recovery, "
        "minimise energy, maximise throughput).",
        "Inferentials run in the APC server (pressure-compensated temperatures, PCT), validated by analysers "
        "and lab with slow bias update; analyser fault -> inferential with frozen bias -> CV dropped after "
        "time-out.",
        "DCS keeps full authority: MPC writes SPs only to loops in 'MPC' mode, with SP clamps and rate limits; "
        "on watchdog failure all loops shed to AUTO at last good SP and an alarm is raised.",
        "Expected benefits (industry typical): 1-3 % throughput, 2-5 % energy, 0.5-1 vol % higher-value "
        "product recovery.",
        "MV/CV/DV lists are FEED-level; final list fixed in the APC functional specification after the "
        "pre-test.",
    ])
    sh.save(DIR / f"{no}_APC-MPC-Structure")
    return no


def build():
    DIR.mkdir(parents=True, exist_ok=True)
    return [csd_001(), csd_002(), csd_003(), csd_004(), csd_005(), csd_006()]
