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
    p.column(X0, 60, W, 410, "C-101", None)
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


def build():
    DIR.mkdir(parents=True, exist_ok=True)
    return [csd_001(), csd_002()]
