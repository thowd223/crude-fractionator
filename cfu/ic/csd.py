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
    bx = p.box(25, 392, 140, 92, None, stroke=SIS_RED, sw=0.5, fill="none")
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


def build():
    DIR.mkdir(parents=True, exist_ok=True)
    out = [csd_001()]
    return out
