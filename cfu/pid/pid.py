"""Piping & Instrumentation Diagrams (FEED) - CFU-xxx-PR-PID-000..016.

build() draws all P&ID sheets (A1) and writes:
  deliverables/01-process/pid/CFU-<area>-PR-PID-0NN.{svg,pdf} + CFU-000-PR-PID-ALL.pdf
  data/lines.json, data/instruments.json
  deliverables/03-layout-piping/CFU-000-PI-LL-001_Line-List.xlsx
  deliverables/03-layout-piping/CFU-000-PI-SPC-001_Piping-Class-Summary.xlsx (+ .md)
  deliverables/04-instrumentation/CFU-000-IC-IDX-001_Instrument-Index.xlsx

Topology (lines, conditions, sizes, classes) lives in pid_data.py; this module only places it.
"""
from __future__ import annotations

import json
import re

from ..drawing.sheet import Sheet, merge_pdfs
from . import pid_data as PD
from .pid_symbols import Canvas

ROOT = PD.ROOT
OUT = ROOT / "deliverables" / "01-process" / "pid"
C_ = None          # Ctx
REG = None         # Registry
NSHEETS = len(PD.SHEETS)

GEN_NOTES = [
    "Line numbers: <NPS>-<fluid>-<area>-<seq>-<class>-<insulation> per CONVENTIONS; see line list CFU-000-PI-LL-001.",
    "All vents / drains 3/4\" min. with blind or cap; HPV/LPD to piping specification. Valve sizes = line size UNO.",
    "Instrument tags per ISA-5.1; index CFU-000-IC-IDX-001. SIS functions per SRS (SIF tags shown in interlocks).",
]


# Instruments required by the I&C control philosophy (cfu/ic) - services aligned with the I&C package
IC_AN = {
    "AT-1021": "Fuel gas Wobbe index / LHV analyser (calorimeter), FG header",
    "AT-1038": "Unstabilised naphtha D86 end point / RVP (online analyser)",
    "AT-1046": "Salt-in-crude analyser, desalted crude",
    "AT-1047": "BS&W analyser (microwave water-cut), desalted crude",
    "AT-1048": "Crude API / density, salt, BS&W at charge (crude-switch DV)",
    "AT-1049": "Oil-in-water analyser, desalter brine",
    "AT-1055": "Kerosene flash / freeze point (online analyser)",
    "AT-1065": "Diesel D86 T95 / cloud point (online analyser)",
    "AT-1075": "AGO D86 T95 / colour (online analyser)",
    "AT-1099": "LPG C5+ (process GC)",
    "AT-1108": "Light naphtha C6+ / RVP (process GC)",
    "AT-1109": "Heavy naphtha IBP / C5- (process GC)",
    "AT-2032": "Vacuum off-gas H2S analyser (D-202 outlet, H-201 firing / SO2)",
    "FT-1021": "H-101 fuel gas flow (fuel/air cross-limiting)",
    "FT-2006": "H-201 fuel gas flow (cross-limiting fuel measurement)",
    "TT-9005": "Ambient air temperature (APC DV, air coolers)",
    "XA-9101": "Analyser house AH-101 common trouble / HVAC alarm",
}
IC_RNG = {"AT-1021": ("40-55", "MJ/Sm3 (Wobbe)"), "AT-1038": ("100-250", "C (D86 EP)"), "AT-1046": ("0-50", "PTB"),
          "AT-1047": ("0-2", "vol% BS&W"), "AT-1048": ("20-45", "API"), "AT-1049": ("0-500", "ppmw oil"),
          "AT-1055": ("0-100", "C (flash)"), "AT-1065": ("250-400", "C (D86 T95)"), "AT-1075": ("300-450", "C (D86 T95)"),
          "AT-1099": ("0-5", "LV% C5+"), "AT-1108": ("0-10", "LV% C6+"), "AT-1109": ("0-5", "LV% C5-"),
          "AT-2032": ("0-10", "mol% H2S"), "TT-9005": ("-20-60", "C")}
# DCS computing blocks used by the control schemes (cfu/ic/csd.py): tag -> (P&ID seq, function)
IC_SOFT = {
    "FY-1011A": (4, "Pass flow SP distribution (total / n passes)"), "FY-1011B": (4, "Pass bias summation (TDIC-1019)"),
    "FY-1020A": (5, "COT demand feed-forward f(x) from charge"), "FY-1020B": (5, "Firing demand summation"),
    "FY-1021A": (5, "Fuel SP low select (air available)"), "FY-1021C": (5, "Fuel heat release f(x) (Wobbe)"),
    "FY-1025A": (5, "Air SP high select (fuel heat release)"), "FY-1025B": (5, "Air demand multiplier"),
    "FY-1025C": (5, "Air/fuel ratio (O2 trim) divider"), "PY-1021A": (5, "Fuel heat demand to burner pressure f(x)"),
    "PY-1021B": (5, "Minimum-fire high select"), "PY-1032": (9, "D-102 pressure split-range"),
    "FFY-1054": (8, "C-102 steam / kero ratio"), "FFY-1064": (8, "C-103 steam / diesel ratio"),
    "FFY-1074": (8, "C-104 steam / AGO ratio"), "FFY-1081": (6, "C-101 steam / AR ratio"),
    "FFY-1094": (10, "C-105 reflux / feed (L/F) ratio"), "FY-2020": (13, "Wash-oil minimum f(charge) high select"),
}


def add_ic_soft():
    for t, (sq, fn) in IC_SOFT.items():
        REG.inst(t, dref(sq), kind="dcs", sys="DCS", svc=fn, note="DCS soft (computing block, not on P&ID)")


def add_fg_devices():
    """Basic F&G device set (index only; F&G layout drawing by others). Locations from data/layout.json."""
    lay = json.loads((ROOT / "data" / "layout.json").read_text())
    pos = {e["tag"]: (e["x"], e["y"]) for e in lay["equipment"]}

    def loc(tag):
        for k in (tag, tag + "A", tag.replace("A/B", "A"), tag.split("/")[0]):
            if k in pos:
                return pos[k]
        return pos.get("D-104", (0, 0)) if tag.startswith("P-119") else (0.0, 0.0)

    ctr = {"1": 1501, "2": 2501, "9": 9501}

    def dev(letters, area, near, svc, dx=0.0, dy=-3.0):
        n = ctr[area]
        ctr[area] += 1
        x, y = loc(near)
        tag = f"{letters}-{n}"
        REG.inst(tag, "F&G LAYOUT (BY OTHERS)", kind="field", sys="F&G", svc=svc,
                 note=f"Loc. x={x + dx:.1f} m, y={y + dy:.1f} m (near {near})")
        REG.inst_[tag]["sheets"] = ["F&G LAYOUT (BY OTHERS)"]

    pumps = sorted({e["tag"][:5] for e in lay["equipment"] if e["tag"].startswith("P-")}) + ["P-119"]
    for p in pumps:
        a = p[2]
        dev("GD", a if a in "12" else "1", p, f"Flammable gas detector (IR point), pump row {p}A/B")
    for h in ("H-101", "H-201"):
        a = h[2]
        for i, (dx, txt) in enumerate(((-8, "FG train"), (8, "burner manifold"))):
            dev("GD", a, h, f"Flammable gas detector (catalytic), {h} {txt}", dx=dx, dy=-12)
    for t in ("C-105", "D-105", "C-106", "D-106", "E-116"):
        dev("GD", "1", t, f"Flammable gas detector (IR point), LPG / light-ends area at {t}")
    for i in range(2):
        dev("GD", "1", "D-102", f"Flammable gas detector (IR point), D-102 overhead drum ({i + 1})", dx=-4 + 8 * i)
    for t, a, n in (("D-102", "1", 2), ("P-105", "1", 1), ("D-201", "2", 2), ("D-202", "2", 1), ("P-205", "2", 1)):
        for i in range(n):
            dev("GD", a, t, f"H2S toxic gas detector (electrochemical), {t}" + (f" ({i + 1})" if n > 1 else ""),
                dx=-4 + 8 * i)
    for h, a, n in (("H-101", "1", 4), ("H-201", "2", 2)):
        for i in range(n):
            dev("BE", a, h, f"Flame detector (IR3), {h} burner front / FG train ({i + 1})", dx=-10 + 20 * (i % 2),
                dy=-6 - 6 * (i // 2))
    for p in ("P-112", "P-204", "P-108", "P-111", "P-202", "P-203", "P-110"):
        dev("BE", p[2], p, f"Flame detector (IR3), hot pump {p}A/B")
    for t, a, txt in (("D-101A", "1", "desalting"), ("E-106", "1", "preheat bank"), ("C-101", "1", "C-101 / OH"),
                      ("H-101", "1", "H-101"), ("C-105", "1", "light ends"), ("P-112", "1", "CDU pump row"),
                      ("C-201", "2", "VDU"), ("H-201", "2", "H-201"), ("D-201", "2", "ejector / hotwell"),
                      ("D-104", "9", "flare KO / utilities"), ("D-103", "9", "fuel gas KO")):
        dev("HS", a, t, f"Manual call point (MCP), {txt} area", dy=4.0)


def dref(seq):
    return PD.dwg(seq)


def new_sheet(seq, notes=()):
    sid = PD.dwg(seq)
    title2 = [t for s, a, t in PD.SHEETS if s == seq][0]
    sh = Sheet("A1", "PIPING & INSTRUMENT DIAGRAM", title2, sid, sheet=f"{seq + 1} OF {NSHEETS}",
               discipline="PROCESS", notes=list(notes) + GEN_NOTES if seq else list(notes))
    return Canvas(sh, REG, sid)


def save(C):
    C.sh.save(OUT / C.sid)
    return OUT / (C.sid + ".pdf")


# ----------------------------------------------------------------------------- helpers
def fnum(x, d=1):
    return f"{x:,.{d}f}"


def eq_lines(tag):
    e = C_.eq(tag)
    out = [e.get("service", "")]
    if e.get("type") == "Pump":
        out.append(f"RATED {e['flow_m3h']:.0f} m3/h @ {e['head_m']:.0f} m, dP {e['dP_bar']:g} bar")
        out.append(f"MOTOR {e['motor_kw']:g} kW; {e.get('seal', '')}")
        out.append(f"DES. T {e['des_T']} C; MAT'L {e.get('moc', '')}")
        return out
    out.append(e.get("size", ""))
    dp, dt = e.get("des_P"), e.get("des_T")
    if dp is not None or dt:
        out.append(f"DESIGN {dp} barg / {dt} C" + (f"; CA {e['ca_mm']} mm" if e.get("ca_mm") else ""))
    if e.get("duty_kw"):
        out.append(f"DUTY {e['duty_kw'] / 1000:.2f} MW" + (f"; {e['fans']} x {e['motor_kw']:g} kW fans"
                                                        if e.get("fans") else ""))
    elif e.get("motor_kw"):
        out.append(f"MOTOR {e['motor_kw']:g} kW")
    if e.get("shellside"):
        out.append(f"SHELL: {e['shellside']} / TUBE: {e['tubeside']}")
    if e.get("internals"):
        out.append(e["internals"])
    if e.get("moc"):
        out.append(f"MAT'L {e['moc']}")
    return out


def eq_boxes(C, tags, x0=18, y0=17, w=63, gap=2.5):
    x = x0
    hmax = 0
    for t in tags:
        h = C.eqbox(x, y0, w, eq_lines(t), t)
        hmax = max(hmax, h)
        x += w + gap
    return y0 + hmax


def lt(key, field="op_T_C"):
    return REG.lines[key][field]


def ti(C, x, y, tap_pts=None, kind="dcs", svc=None, line=None, letters="TI"):
    tag = f"{letters}-{REG.free('1' if C.sid[4] == '1' else ('2' if C.sid[4] == '2' else '9'))}"
    C.bub(x, y, tag, kind, svc=svc, line=line)
    if tap_pts:
        C.tap(tap_pts)
    return tag


def free_tag(C, letters):
    a = C.sid[4]
    return f"{letters}-{REG.free(a if a in '129' else '1')}"


def pump_pair(C, x, y, tag, suct_key, disch_key, dx=34, ydisch=30, pi=True, labels=True, single=False):
    """Two 2x100 % pumps A/B.  Suction header at y+14 (starts x-18), discharge header at y-ydisch.
    Returns dict(s=(x-18, y+14), dl=(x, y-ydisch), dr=(x+dx, y-ydisch))."""
    ys, yd = y + 14, y - ydisch
    pumps = [(x, tag + ("" if single else "A"))] + ([] if single else [(x + dx, tag + "B")])
    sk = REG.lines[suct_key]
    dk = REG.lines[disch_key]
    REG.use_line(suct_key, C.sid)
    REG.use_line(disch_key, C.sid)
    xe = pumps[-1][0]
    if not single:
        C.pipe([(x - 18, ys), (xe - 18, ys)], arrow=False, util=sk["util"])
    for xp, t in pumps:
        C.pump(xp, y, t)
        C.pipe([(xp - 18, ys), (xp - 18, y), (xp - 4.2, y)], arrow=False, util=sk["util"])
        C.gate(xp - 18, ys - 7, "v")
        C.strainer(xp - 10.5, y, "h")
        C.vent(xp - 10.5, y + 1.5, "d", 4.5)
        C.pipe([(xp, y - 4.2), (xp, yd)], arrow=False, util=dk["util"])
        C.check(xp, y - 11.5, "u")
        C.gate(xp, y - 19.5, "v")
        if pi:
            ptag = free_tag(C, "PI")
            C.bub(xp + 8.5, y - 15.5, ptag, "field", svc=f"{t} discharge pressure", line=disch_key, r=4.0)
            C.tap([(xp, y - 15.5), (xp + 4.5, y - 15.5)])
    if not single:
        C.pipe([(x, yd), (xe, yd)], arrow=False, util=dk["util"])
        C.dot(x, yd)
        C.dot(xe, yd)
    return dict(s=(x - 18, ys), dl=(x, yd), dr=(xe, yd))


def loop_tags(loop):
    """Return (transmitter tag, controller tag, valve tag or None) for a principal loop."""
    lp = C_.LOOPS[loop]
    letters, num = loop.split("-")
    first = letters[:-2] if letters.endswith("IC") else letters[0]
    if letters.startswith("PDI"):
        first = "PD"
    tt = f"{first}T-{num}"
    fv = lp["final"].split()[0] if re.match(r"^[A-Z]+V-\d+", lp["final"]) else None
    return tt, loop, fv


def ctrl(C, loop, xt, yt, xc, yc, tap=None, sig=None, vsig=None, fail=None, tkind="field", rng=None, line=None,
         t_tag=None, tag_only=False):
    """Draw a principal control loop: transmitter bubble (field) + controller (DCS) + signal lines.
    tap: process connection points to transmitter; sig: points transmitter->controller (default straight);
    vsig: points controller->valve actuator."""
    tt, ct, fv = loop_tags(loop)
    tt = t_tag or tt
    if xt is not None:
        C.bub(xt, yt, tt, tkind, svc=C_.LOOPS[loop]["service"], line=line, loop=loop)
        if tap:
            C.tap(tap)
        C.sig(sig or [(xt, yt), (xc, yc)], "e")
    C.bub(xc, yc, ct, "dcs", svc=C_.LOOPS[loop]["service"], line=line, loop=loop)
    if vsig:
        C.sig(vsig, "e")
    if fv:
        REG.inst(fv, C.sid, svc=C_.LOOPS[loop]["service"], fail=fail, line=line, loop=loop)
    return tt, ct, fv


def sis_initiator(C, tags, x, y, fn_tag, sif, xs, ys, xi, yi, tap=None, txt_side="r", vote=None):
    """SIS initiator(s): field transmitter bubble(s) -> SIS trip function (diamond-in-square) -> interlock."""
    sil = C_.SIFS[sif]["sil"]
    for i, t in enumerate(tags):
        REG.inst(t, C.sid, kind="field", sys="SIS", sif=sif, svc=C_.SIFS[sif]["function"])
    label = tags[0] if len(tags) == 1 else tags[0][:-1] + "-".join(t[-1] for t in tags[::len(tags) - 1])
    lt_, num = label.split("-", 1)
    C.bub(x, y, f"{lt_}-{num}", "field", reg=False)
    if tap:
        C.tap(tap)
    C.bub(xs, ys, fn_tag, "sis", sys="SIS", sif=sif, svc=C_.SIFS[sif]["function"] + (f" ({vote})" if vote else ""))
    C.sig([(x, y), (xs, ys)] if (x == xs or y == ys) else [(x, y), (xs, y), (xs, ys)], "e")
    if vote:
        C.t(vote, xs + 5.5, ys - 3.5, 2.0)
    return sil


def interlock(C, x, y, sif, below=True):
    C.ilk(x, y, sif, below=below)


# ============================================================================= SHEET 001
def sheet_001():
    C = new_sheet(1, [
        "Cold-train crude-side design 35 barg (E-101..E-105) >= P-101 shut-off; PSV-1010 (30 barg) thermal / blocked-in.",
        "Exchanger hot-side connections shown at channel / shell nozzles; TEMA type & shells per data sheets.",
        "TV-1041 / TV-1004 bypass control valves have block valves only (exchanger provides bypass path).",
        "Demulsifier dosed at P-101 suction, ratio to FIC-1001 (FFIC-1002) - X-101 vendor package.",
    ])
    eq_boxes(C, ["P-101A/B", "E-101", "E-102", "E-103", "E-104", "E-105", "X-101"], w=72)
    ye, yh = 215.0, 245.0
    yu, yl = 143.0, 165.0
    cells = [
        ("E-101", 300, "crude_c1", "tpa_d", "tpa_r", ("FROM P-106A/B", 7), ("TO C-101 TRAY 1", 7), "shell", "TV-1041"),
        ("E-102", 395, "crude_c2", "kero_pd", "kero_c1", ("FROM P-109A/B", 8), ("TO A-103", 8), "shell", None),
        ("E-103", 490, "crude_c3", "lvgo_pd", "lvgo_c1", ("FROM P-201A/B", 14), ("TO A-201", 14), "shell", None),
        ("E-104", 585, "crude_c4", "dsl_c1", "dsl_c2", ("FROM E-107", 3), ("TO A-104", 8), "shell", None),
        ("E-105", 680, "crude_c5", "vr_c2", "vr_prod", ("FROM E-201", 14), ("TO VR RUNDOWN", 14), "tube", None),
    ]
    # ---- crude charge pumps
    xa, yp = 110.0, 430.0
    pp = pump_pair(C, xa, yp, "P-101", "crude_in", "p101_d")
    C.opc(50, pp["s"][1], "l", "FROM CRUDE TANKS", "OSBL")
    C.line("crude_in", [(50, pp["s"][1]), pp["s"]], arrow=False, at=0.25)
    C.reducer(86, pp["s"][1], "h", note='24"x20"', note_side=1)
    # demulsifier
    C.package(30, 345, 46, 22, "X-101", ["DEMULSIFIER", "INJECTION PKG"])
    C.line("ch_demul", [(53, 367), (53, 395), (76, 395), (76, pp["s"][1])], lab=1, at=0.4)
    C.check(76, 420, "d")
    C.gate(76, 432, "v")
    ffic = "FFIC-1002"
    C.bub(95, 352, ffic, "dcs", svc=C_.LOOPS[ffic]["service"], loop=ffic)
    C.sig([(90.4, 352), (76, 352)], "e")
    C.t("SP RATIO", 100, 345.5, 2.0)
    C.bub(95, 330, "FY-1002", "field", svc="Demulsifier pump stroke positioner", r=4.0)
    C.sig([(95, 347.4), (95, 334)], "e")
    # discharge
    yd = pp["dr"][1]
    xd = 300 + 10                       # E-101 shell inlet x
    pts = [pp["dr"], (258, yd), (258, yh), (xd, yh), (xd, ye + 6)]
    C.line("p101_d", pts, lab=2, at=0.5, side=-1)
    C.bub(272, 330, "AT-1048", "field", svc=IC_AN["AT-1048"], line='p101_d')
    C.tap([(258, 330), (267.4, 330)])
    C.pipe([pp["dl"], pp["dr"]], arrow=False)
    # PSV-1010 on discharge header
    p = C_.PSV["PSV-1010"]
    C.psv(127, yd, "PSV-1010", p["set_barg"], f"1{p['orifice']}", up=16, out="r", outlen=14,
          dest="CLOSED DRAIN", text_side=-1)
    REG.use_line("psv1010_out", C.sid)
    C.lab(REG.no("psv1010_out"), xy=(150, yd - 21.5))
    # FE/FT/FIC-1001 + FV-1001
    C.orifice(166, yd, "h")
    tt, ct, fv = ctrl(C, "FIC-1001", 166, yd - 17, 205, yd - 32, tap=[(166, yd - 2.4), (166, yd - 12.6)],
                      sig=[(170.6, yd - 17), (190, yd - 17), (190, yd - 32), (200.4, yd - 32)],
                      vsig=[(205, yd - 27.4), (205, yd - 10.4)], fail="FC", line="p101_d")
    REG.inst("FE-1001", C.sid, svc="Crude charge orifice", line="p101_d")
    C.t("FE-1001", 166, yd + 7, 2.0, "middle")
    C.station(183, yd, 227, yd, "FV-1001", "FC", byp=1, tag_pos=(209.5, yd - 6))
    C.xv(241, yd, "h", "XV-1001", "FC", tag_pos=(244.5, yd - 6))
    REG.inst("XV-1001", C.sid, kind="field", sys="SIS", sif="SIF-108", fail="FC", svc=C_.SIFS["SIF-108"]["function"])
    C.ilk(241, yd - 30, "SIF-108")
    C.sig([(241, yd - 26), (241, yd - 9.8)], "e")
    C.t("FROM LZHH-1082", 236, yd - 44, 2.0, "end")
    C.t(f"({dref(6)})", 236, yd - 41.4, 2.0, "end")
    C.sig([(237, yd - 43), (241, yd - 43), (241, yd - 34)], "e")
    C.t("TRIP P-101A/B", 236, yd - 31, 2.0, "end")
    C.t("(MCC)", 236, yd - 28.4, 2.0, "end")
    C.sig([(70, 352), (90.4, 352)], "e") if False else None
    C.sig([(166 + 0, yd - 21.6), (166, yd - 36), (95, yd - 36), (95, 356.6)], "d")
    C.t("FF", 160, yd - 37.5, 2.0)
    # minimum flow
    REG.use_line("p101_mf", C.sid)
    C.line("p101_mf", [(150, yd), (150, 468), (115, 468)], lab=0, at=0.55, side=1, arrow=False)
    C.dot(150, yd)
    C.orifice(132, 468, "h", ro=True)
    C.gate(142, 468, "h")
    C.spec_break(124, 468, "h", "B1", "A1")
    C.line("p101_mf2", [(115, 468), (50, 468)], lab=0, at=0.5)
    C.opc(50, 468, "l", "TO CRUDE TANKS", "OSBL", flow="out")
    C.t("MIN. FLOW", 132, 476, 2.0, "middle")

    # ---- exchanger cells
    cells = [c[:8] + ((c[8], "TIC-1041", "tpa_byp", True) if c[8] else (None, None, None, False),) for c in cells]
    prev_out, _ = train(C, cells, ye, yh, yu, yl)
    # E-105 crude bypass (TIC-1004) and outlet to desalters
    xe5 = 680
    xbl, xbr = 625, 722
    REG.use_line("crude_e105_byp", C.sid)
    C.pipe([(xbl, yh), (xbl, yh + 30), (xbr, yh + 30), (xbr, yh)], arrow=False)
    C.dot(xbl, yh)
    C.dot(xbr, yh)
    C.lab(REG.no("crude_e105_byp"), xy=(xbl + 22, yh + 28.5))
    C.station(xbl + 30, yh + 30, xbr - 8, yh + 30, "TV-1004", "FO", byp=1, bypass=False, side=-1,
              tag_pos=(674, yh + 22))
    C.line("crude_c5", [prev_out, (790, yh)], lab=0, at=0.6)
    C.opc(790, yh, "r", "TO D-101A", dref(2))
    tt, ct, fv = ctrl(C, "TIC-1004", 760, yh - 18, 760, yh - 38, tap=[(760, yh), (760, yh - 13.4)],
                      vsig=[(755.4, yh - 38), (745, yh - 38), (745, yh + 50), (673.5, yh + 50), (673.5, yh + 38.6)],
                      fail="FO", line="crude_c5")
    C.t("LIMITS 125-145 C", 766, yh - 37, 2.0)
    return save(C)


def train(C, cells, ye, yh, yu, yl, prev_out=None, prev_key=None):
    """Row of exchangers with crude header at yh, hot-side connectors above (rows yu / yl).
    cell = (tag, xe, crude_out_key, hot_in_key, hot_out_key, (from txt, sheet), (to txt, sheet) | None,
            'shell'|'tube', (tv_tag, tic_loop|None, bypass_key, draw_ctrl) )"""
    info = {}
    for i, (tag, xe, ck, hin, hout, fr, to, side, tvd) in enumerate(cells):
        rev = side == "tube"
        n = C.hx(xe, ye, rev=rev)
        C.t(tag, xe + (3 if not rev else -3), ye + 16.5, 2.6, "middle", bold=True)
        if not rev:
            c_in, c_out = n["sb_far"], n["st_near"]
            h_in, h_out = n["ct"], n["cb"]
        else:
            c_in, c_out = n["cb"], n["ct"]
            h_in, h_out = n["st_far"], n["sb_far"]
        key = cells[i - 1][2] if i else prev_key
        if prev_out is not None and key:
            C.line(key, [prev_out, (c_in[0], yh), c_in], lab=0, at=0.45)
        xo = xe + 30
        C.pipe([c_out, (c_out[0], ye - 14), (xo, ye - 14), (xo, yh)], arrow=False)
        prev_out = (xo, yh)
        ti(C, xo + 10, ye - 26, [(xo, ye - 14), (xo, ye - 26), (xo + 5.4, ye - 26)], svc=f"Crude {tag} outlet",
           line=ck)
        C.vent(xe + 3, ye - 6, "u", 4.5)
        C.vent(xe + 3, ye + 6, "d", 4.5)
        xin = h_in[0]
        xout = xe - 36
        if fr:
            C.line(hin, [(xin, yl), h_in], lab=0, at=0.5, side=1 if not rev else -1)
            C.opcv(xin, yl, "u", fr[0], dref(fr[1]))
        C.gate(xin, ye - 14, "v")
        if to:
            C.line(hout, [h_out, (h_out[0], ye + 16), (xout, ye + 16), (xout, yu)], lab=2, at=0.55, side=-1)
            C.opcv(xout, yu, "u", to[0], dref(to[1]), flow="out")
            C.gate(xout, ye + 2, "v")
        info[tag] = dict(h_in=h_in, h_out=h_out, xin=xin, xout=xout, c_in=c_in)
        tv, tloop, bkey, dctrl = tvd
        if tv:
            xb = xe - 25
            REG.use_line(bkey, C.sid)
            C.pipe([(xin, ye - 32), (xb, ye - 32), (xb, ye + 16)], arrow=False)
            C.dot(xin, ye - 32)
            C.dot(xb, ye + 16)
            C.station(xb, ye - 30, xb, ye + 12, tv, "FO", bypass=False, red=False, side=-1,
                      tag_pos=(xout - 2, ye - 3))
            C.lab(REG.no(bkey), xy=(xb + 3.2, ye - 35))
            vs = [(xout - 14, ye - 70), (xb, ye - 70), (xb, ye - 45), (xb - 8, ye - 45), (xb - 8, ye - 9)]
            if dctrl:
                ctrl(C, tloop, xout - 14, ye - 40, xout - 14, ye - 60, tap=[(xout, ye - 40), (xout - 9.4, ye - 40)],
                     vsig=[(xout - 14, ye - 64.6)] + vs, fail="FO", line=hout)
            else:
                REG.inst(tv, C.sid, svc=C_.LOOPS[tloop]["service"], fail="FO", line=hout, loop=tloop)
                C.sig([(xout - 18, ye - 58), (xb, ye - 58)] + vs[2:], "e")
                C.t(f"FROM {tloop}", xout - 19, ye - 61, 2.0, "end")
                C.t(f"({dref(14)})", xout - 19, ye - 57.4, 2.0, "end")
    return prev_out, info


def tsv(C, x, y):
    """Thermal relief valve on a cooling-water side (data from psv.json TSV-typ)."""
    pv = C_.PSV["TSV-typ"]
    tag = free_tag(C, "TSV")
    C.dot(x, y)
    C.psv(x, y, tag, pv["set_barg"], "", up=7, out="r", outlen=5, dest="", blocks=False, compact=True)
    REG.inst(tag, C.sid, svc=f"Thermal relief, {pv['protects']} (TSV-typ, {pv['orifice']} orifice, 3/4\" x 1\")",
             note="TSV-typ")
    return tag


# ============================================================================= SHEET 002
def transformer(C, x, y, label):
    C.g_eq.add(C.d.circle((x - 2, y), 3.0, stroke_width=0.35))
    C.g_eq.add(C.d.circle((x + 2, y), 3.0, stroke_width=0.35))
    C.t(label, x, y - 4.5, 2.0, "middle")


def sheet_002():
    C = new_sheet(2, [
        "Two-stage counter-current desalting: fresh wash water to 2nd stage, 2nd-stage effluent water to 1st stage.",
        "Desalter pressure held above crude bubble point by PV-1009 (backpressure on D-101B outlet).",
        "Wash water / brine lines class B1 (300#) where design P exceeds A2 (150#) rating - see line list remarks.",
        "Transformer trip on low-low interface (SIF-107) by Electrical (XY-1007 / XY-1008 to feeder CB).",
    ])
    eq_boxes(C, ["D-101A", "D-101B", "E-118", "P-102A/B", "P-114A/B", "P-118", "X-102"], w=70)
    # desalters
    yt, D = 160.0, 32.0
    for x0, tag in ((120, "D-101A"), (420, "D-101B")):
        C.hdrum(x0, yt, 150, D)
        C.t(tag, x0 + 75, yt + D / 2 + 1, 3.0, "middle", bold=True)
        C.g_eq.add(C.d.line((x0 + 8, yt + 11), (x0 + 142, yt + 11), stroke_width=0.3, stroke_dasharray="3,1.2"))
        C.g_eq.add(C.d.line((x0 + 8, yt + 15), (x0 + 142, yt + 15), stroke_width=0.3, stroke_dasharray="3,1.2"))
        C.t("ELECTRODE GRIDS", x0 + 75, yt + 9.5, 2.0, "middle")
        C.g_eq.add(C.d.line((x0 + 8, yt + 26), (x0 + 142, yt + 26), stroke_width=0.3))
        C.t("MUD-WASH HEADER", x0 + 75, yt + 29.5, 2.0, "middle")
        transformer(C, x0 + 95, yt - 9, "XFMR (ELEC.)")
        C.g_eq.add(C.d.line((x0 + 95, yt - 6), (x0 + 95, yt), stroke_width=0.35))
    yc = 115.0
    # crude in -> PDV-1005 -> D-101A
    C.opc(50, yc, "l", "FROM E-105", dref(1))
    C.line("crude_c5", [(50, yc), (140, yc), (140, yt)], lab=0, at=0.32)
    C.cv(108, yc, "h", "PDV-1005", "FO", tag_pos=(111.5, yc - 6))
    C.t("MIX VALVE", 108, yc + 5, 2.0, "middle")
    ctrl(C, "PDIC-1005", 108, yc - 22, 125, yc - 36, tap=[(100, yc), (100, yc - 22), (103.4, yc - 22)],
         sig=[(112.6, yc - 22), (125, yc - 22), (125, yc - 31.4)],
         vsig=[(120.4, yc - 36), (108, yc - 36), (108, yc - 26.6)], fail="FO", line="crude_c5")
    C.tap([(116, yc), (116, yc - 17), (112, yc - 19)])
    # crude D-101A -> PDV-1006 -> D-101B
    C.line("crude_d12", [(255, yt), (255, yc), (440, yc), (440, yt)], lab=1, at=0.3)
    C.cv(408, yc, "h", "PDV-1006", "FO", tag_pos=(411.5, yc - 6))
    C.t("MIX VALVE", 408, yc + 5, 2.0, "middle")
    ctrl(C, "PDIC-1006", 408, yc - 22, 425, yc - 36, tap=[(400, yc), (400, yc - 22), (403.4, yc - 22)],
         sig=[(412.6, yc - 22), (425, yc - 22), (425, yc - 31.4)],
         vsig=[(420.4, yc - 36), (408, yc - 36), (408, yc - 26.6)], fail="FO", line="crude_d12")
    C.tap([(416, yc), (416, yc - 17), (412, yc - 19)])
    # D-101B -> PV-1009 -> P-102
    xs = 700.0
    pp = pump_pair(C, 722, 432, "P-102", "crude_d2", "p102_d")
    C.line("crude_d2", [(555, yt), (555, yc), (xs, yc), (xs, pp["s"][1]), pp["s"]], lab=1, at=0.22, arrow=False)
    C.hop(636, yc, "h")
    C.station(648, yc, 694, yc, "PV-1009", "FO", byp=1, tag_pos=(675.5, yc - 6))
    tt, ct, fv = ctrl(C, "PIC-1009", 582, yc - 20, 610, yc - 20, tap=[(582, yc), (582, yc - 15.4)],
                      vsig=[(614.6, yc - 20), (672, yc - 20), (672, yc - 9.8)], fail="FO", line="crude_d2")
    C.t("FROM PDIC / D-101B", 0, 0, 0.1) if False else None
    ti(C, 582, yc + 22, [(582, yc), (582, yc + 17.4)], svc="Desalted crude temperature", line="crude_d2")
    C.bub(597, yc + 22, "AT-1046", "field", svc=IC_AN["AT-1046"], line='crude_d2')
    C.tap([(597, yc), (597, yc + 17.4)])
    C.bub(611, yc + 22, "AT-1047", "field", svc=IC_AN["AT-1047"], line='crude_d2')
    C.tap([(611, yc), (611, yc + 17.4)])
    # P-102 discharge
    yd = pp["dr"][1]
    C.line("p102_d", [pp["dr"], (795, yd)], lab=None, arrow=False)
    C.t(REG.no("p102_d"), 760, yd - 1.2, 2.0, "middle")
    C.opc(795, yd, "r", "TO E-106", dref(3))
    # min flow
    REG.use_line("p102_mf", C.sid)
    C.line("p102_mf", [(768, yd), (768, 372), (xs, 372)], lab=1, at=0.6, side=-1)
    C.dot(768, yd)
    C.dot(xs, 372)
    C.orifice(745, 372, "h", ro=True)
    C.gate(758, 372, "h")
    C.t("MIN. FLOW", 745, 365, 2.0, "middle")
    # caustic X-102
    C.package(745, 300, 46, 20, "X-102", ["CAUSTIC INJECTION", "PACKAGE"])
    C.line("ch_caustic", [(783, 320), (783, yd)], lab=0, at=0.55, side=1)
    C.check(783, yd - 12, "d")
    C.gate(783, yd - 20, "v")
    C.bub(730, 285, "FFIC-1010", "dcs", svc=C_.LOOPS["FFIC-1010"]["service"], loop="FFIC-1010")
    C.sig([(734.6, 285), (768, 285), (768, 300)], "e")
    C.t("RATIO TO FIC-1001", 724, 278, 2.0, "end")
    # PSVs
    for x0, t, k in ((120, "PSV-1002", "psv1002_out"), (420, "PSV-1003", "psv1003_out")):
        pv = C_.PSV[t]
        C.psv(x0 + 60, yt, t, pv["set_barg"], f"1{pv['orifice']}", up=18, out="r", outlen=16, dest="FLARE",
              text_side=-1)
        REG.use_line(k, C.sid)
        C.lab(REG.no(k), xy=(x0 + 76, yt - 25))
    # PI / TI on drums
    for x0, n in ((120, "D-101A"), (420, "D-101B")):
        ptag = free_tag(C, "PI")
        C.bub(x0 + 120, yt - 16, ptag, "dcs", svc=f"{n} pressure")
        C.tap([(x0 + 120, yt), (x0 + 120, yt - 11.4)])
    # level instrumentation D-101A (left), D-101B (right)
    lx = 98.0
    C.tap([(116, yt + 20), (lx + 4.6, yt + 20)])
    ctrl(C, "LIC-1007", lx, yt + 20, lx, yt + 42, line="brine_1",
         vsig=[(lx + 4.6, yt + 42), (lx + 20, yt + 42), (lx + 20, 268), (226, 268)], fail="FC")
    sis_initiator(C, ["LT-1007B"], lx, yt + 5, "LZLL-1007", "SIF-107", lx - 22, yt + 5, 0, 0,
                  tap=[(117, yt + 8), (117, yt + 5), (lx + 4.6, yt + 5)])
    C.ilk(lx - 22, yt + 24, "SIF-107")
    C.sig([(lx - 22, yt + 9.6), (lx - 22, yt + 20)], "e")
    C.t("TRIP XFMR", lx - 22, yt + 34.5, 2.0, "middle")
    C.t("XY-1007", lx - 22, yt + 37, 2.0, "middle")
    REG.inst("XY-1007", C.sid, sys="SIS", sif="SIF-107", svc="D-101A transformer feeder trip")
    rx = 598.0
    C.tap([(574, yt + 20), (rx - 4.6, yt + 20)])
    ctrl(C, "LIC-1008", rx, yt + 20, rx + 24, yt + 20, line="ww_recy",
         vsig=[(rx + 24, yt + 15.4), (rx + 24, 100), (493, 100), (493, 92)], fail="FC")
    sis_initiator(C, ["LT-1008B"], rx, yt + 40, "LZLL-1008", "SIF-107", rx + 24, yt + 40, 0, 0,
                  tap=[(573, yt + 24), (573, yt + 40), (rx - 4.6, yt + 40)])
    C.ilk(rx + 24, yt + 58, "SIF-107")
    C.sig([(rx + 24, yt + 44.6), (rx + 24, yt + 54)], "e")
    C.t("TRIP XFMR XY-1008", rx + 30, yt + 59, 2.0)
    REG.inst("XY-1008", C.sid, sys="SIS", sif="SIF-107", svc="D-101B transformer feeder trip")
    # 2nd-stage water -> LV-1008 -> 1st stage mix point (over the top)
    yw = 85.0
    C.line("ww_recy", [(560, yt + D), (560, 238), (636, 238), (636, yw), (80, yw), (80, yc)],
           lab=3, at=0.7)
    C.station(470, yw, 516, yw, "LV-1008", "FC", byp=-1, side=1, tag_pos=(496, yw + 9.5))
    # brine D-101A -> LV-1007 -> E-118 -> WWT
    xb = 230.0
    C.line("brine_1", [(xb, yt + D), (xb, 290)], arrow=False, lab=0, at=0.18, side=1)
    C.station(xb, 247, xb, 287, "LV-1007", "FC", byp=1, side=-1, tag_pos=(xb - 8, 262))
    C.spec_break(xb, 293, "v", "B1", "")
    hx = C.hx(330, 345)
    C.t("E-118", 330, 362, 2.6, "middle", bold=True)
    C.line("brine_2", [(xb, 290), (xb, 312), (hx["ct"][0], 312), hx["ct"]], lab=1, at=0.5)
    C.line("brine_3", [hx["cb"], (hx["cb"][0], 385), (50, 385)], lab=1, at=0.5)
    C.opc(50, 385, "l", "TO WWT", "OSBL", flow="out")
    ti(C, 260, 400, [(260, 385), (260, 395.4)], svc="Brine to WWT temperature", line="brine_3")
    C.bub(225, 400, "AT-1049", "field", svc=IC_AN["AT-1049"], line='brine_3')
    C.tap([(225, 385), (225, 395.4)])
    # wash water P-114 -> E-118 shell -> FV-1003 -> D-101B mix point
    wp = pump_pair(C, 110, 470, "P-114", "ww_s", "ww_d")
    C.opc(50, wp["s"][1], "l", "WASH WATER (SSW)", "OSBL")
    C.line("ww_s", [(50, wp["s"][1]), wp["s"]], arrow=False, at=0.5)
    C.line("ww_d", [wp["dr"], (hx["sb_far"][0], wp["dr"][1]), hx["sb_far"]], lab=0, at=0.6)
    xw = 385.0
    C.line("ww_inj", [hx["st_near"], (hx["st_near"][0], 325), (xw, 325), (xw, yc)], lab=2, at=0.75, side=1)
    C.station(xw, 255, xw, 300, "FV-1003", "FC", byp=1, side=-1, tag_pos=(xw - 8, 270))
    C.orifice(xw, 312, "v")
    ctrl(C, "FFIC-1003", 360, 312, 360, 290, tap=[(xw, 312), (364.6, 312)],
         vsig=[(360, 285.4), (360, 277.5), (xw - 7.6, 277.5)], fail="FC", line="ww_inj", t_tag="FT-1003")
    C.t("RATIO TO FIC-1001", 355, 283, 2.0, "end")
    ti(C, 360, 340, [(360, 325), (360, 335.4)], svc="Wash water to desalter temperature",
       line="ww_inj")
    # hops where wash water crosses brine
    # mud-wash pump P-118
    mp = pump_pair(C, 520, 300, "P-118", "mud_s", "mud_d", single=True, ydisch=40)
    C.line("mud_s", [(mp["s"][0], yt + D), mp["s"]], arrow=False, lab=0, at=0.5, side=1)
    C.line("mud_d", [mp["dl"], (520, 245), (170, 245), (170, yt + D)], lab=1, at=0.62)
    C.pipe([(520, 245), (535, 245), (535, yt + D)])
    C.dot(520, 245)
    C.hop(xb, 245, "v")
    C.hop(xw, 245, "h")
    C.t("TO MUD-WASH HEADERS", 300, 251.5, 2.0, "middle")
    return save(C)

# ============================================================================= SHEET 003
def sheet_003():
    C = new_sheet(3, [
        "Hot-train crude-side design 45 barg (E-106..E-111) >= P-102 shut-off (D-101B design + 1.2 x dP).",
        "E-113 kettle MP steam generator: 3-element level control simplified to LIC-1110 at FEED.",
        "TV-2017 controlled from TIC-2017 (HVGO pumparound return temperature) on " + dref(14) + ".",
    ])
    eq_boxes(C, ["E-106", "E-107", "E-108", "E-109", "E-110", "E-111", "E-113"], w=70)
    ye, yh, yu, yl = 215.0, 245.0, 143.0, 165.0
    N4 = (None, None, None, False)
    cells = [
        ("E-106", 150, "crude_h1", "mpa_d", "mpa_r", ("FROM P-107A/B", 7), ("TO C-101 TRAY 11", 7), "shell",
         ("TV-1043", "TIC-1043", "mpa_byp", True)),
        ("E-107", 245, "crude_h2", "dsl_pd", "dsl_c1", ("FROM P-110A/B", 8), ("TO E-104", 1), "shell", N4),
        ("E-108", 340, "crude_h3", "hvgo_pd", "hvgo_c1", ("FROM P-202A/B", 14), ("TO HVGO SPLIT", 14), "shell",
         ("TV-2017", "TIC-2017", "hvgo_byp", False)),
        ("E-109", 435, "crude_h4", "ago_pd", "ago_c1", ("FROM P-111A/B", 8), ("TO A-105", 8), "shell", N4),
        ("E-110", 530, "crude_h5", "bpa_d", "bpa_c1", ("FROM P-108A/B", 7), None, "shell", N4),
        ("E-111", 625, "crude_h6", "vr_pd", "vr_c1", ("FROM P-204A/B", 13), ("TO E-201", 14), "tube", N4),
    ]
    C.opc(50, yh, "l", "FROM P-102A/B", dref(2))
    out, info = train(C, cells, ye, yh, yu, yl, prev_out=(50, yh), prev_key="p102_d")
    C.hop(info["E-110"]["h_out"][0], yh, "h")
    C.line("crude_h6", [out, (790, yh)], lab=0, at=0.55)
    C.opc(790, yh, "r", "TO H-101", dref(4))
    REG.free("1")      # CIT indication is TI-1226 on H-101 inlet (PID-004); number kept unused
    ptag = free_tag(C, "PI")
    C.bub(740, yh - 20, ptag, "dcs", svc="Crude to H-101 pressure", line="crude_h6")
    C.tap([(740, yh), (740, yh - 15.4)])
    # E-110 -> E-113 kettle -> C-101
    k = C.kettle(560, 380)
    C.t("E-113", 560, 398, 2.6, "middle", bold=True)
    hb = info["E-110"]["h_out"]
    C.line("bpa_c1", [hb, (hb[0], 345), (k["ct"][0], 345), k["ct"]], lab=1, at=0.5, side=-1)
    C.gate(hb[0], ye + 14, "v")
    C.line("bpa_r", [k["cb"], (k["cb"][0], 415), (440, 415)], lab=1, at=0.55)
    C.opc(440, 415, "l", "TO C-101 TRAY 23", dref(7), flow="out")
    xb = 500.0
    REG.use_line("bpa_byp", C.sid)
    C.pipe([(hb[0], 335), (xb, 335), (xb, 415)], arrow=False)
    C.dot(hb[0], 335)
    C.dot(xb, 415)
    C.station(xb, 345, xb, 400, "TV-1045", "FO", bypass=False, red=False, side=-1, tag_pos=(xb - 8, 360))
    C.lab(REG.no("bpa_byp"), xy=(xb - 14, 331))
    ctrl(C, "TIC-1045", 465, 432, 465, 452, tap=[(465, 415), (465, 427.4)],
         vsig=[(460.4, 452), (450, 452), (450, 372.5), (xb - 8, 372.5)], fail="FO", line="bpa_r")
    # steam side
    sv, sb = k["sv"], k["sb"]
    C.opc(640, 455, "r", "FROM BFW HEADER", dref(16), flow="in")
    C.line("bfw_e113", [(640, 455), (sb[0], 455), sb], lab=0, at=0.55)
    C.station(sb[0], 400, sb[0], 445, "LV-1110", "FC", byp=-1, side=1, red=False, tag_pos=(sb[0] + 8, 412))
    C.line("ms_e113", [sv, (sv[0], 330), (650, 330)], lab=0, at=0.5, side=-1)
    pv = C_.PSV["PSV-1011"]
    C.psv(580, 330, "PSV-1011", pv["set_barg"], f"1{pv['orifice']}", up=20, out="l", outlen=14,
          dest="ATM (SAFE LOC.)", text_side=1)
    REG.use_line("psv1011_out", C.sid)
    C.t(REG.no("psv1011_out"), 565, 314, 2.0, "end")
    C.opc(650, 330, "r", "TO MP STEAM HDR", dref(16))
    C.station(588, 330, 632, 330, "PV-1111", "FO", byp=1, side=-1, tag_pos=(613.5, 324))
    ctrl(C, "PIC-1111", 645, 312, 620, 300, tap=[(645, 330), (645, 316.6)],
         sig=[(640.4, 312), (630, 312), (630, 300), (624.6, 300)],
         vsig=[(620, 304.6), (620, 315), (610, 315), (610, 320.2)],
         fail="FO", line="ms_e113")
    lv = k["lvl"]
    C.tap([lv, (lv[0] + 7, lv[1])])
    ctrl(C, "LIC-1110", lv[0] + 11.6, lv[1], lv[0] + 36, lv[1], line="bfw_e113",
         vsig=[(lv[0] + 36, lv[1] + 4.6), (lv[0] + 36, 422.5), (sb[0] + 7.6, 422.5)], fail="FC")
    C.bub(lv[0] + 11.6, lv[1] + 16, "LG-" + str(REG.free("1")), "field", svc="E-113 level gauge")
    C.tap([(lv[0], lv[1] + 2), (lv[0] + 3, lv[1] + 2), (lv[0] + 3, lv[1] + 16), (lv[0] + 7, lv[1] + 16)])
    C.line("bd_e113", [(552, k["sb"][1]), (552, 470), (500, 470)], lab=1, at=0.55)
    C.globe(552, 440, "v")
    C.opc(500, 470, "l", "TO BLOWDOWN", "OSBL", flow="out")
    return save(C)

# ============================================================================= heaters
def coil(C, x0, x1, y, amp=2.5, n=12):
    pts = [(x0, y)]
    for i in range(1, n):
        pts.append((x0 + (x1 - x0) * i / n, y + (amp if i % 2 else -amp)))
    pts.append((x1, y))
    C.g_eq.add(C.d.polyline(pts, stroke_width=0.45))


def heater_box(C, x0, y0, x1, y1, tag, cells=2, conv=None, stack=None, burners=8):
    C.g_eq.add(C.d.rect((x0, y0), (x1 - x0, y1 - y0), stroke_width=0.7))
    if cells == 2:
        C.g_eq.add(C.d.line(((x0 + x1) / 2, y0 + 25), ((x0 + x1) / 2, y1), stroke_width=0.3,
                            stroke_dasharray="3,1.5"))
    if conv:
        cx0, cy0, cx1, cy1 = conv
        C.g_eq.add(C.d.rect((cx0, cy0), (cx1 - cx0, cy1 - cy0), stroke_width=0.6))
        C.t("CONVECTION", (cx0 + cx1) / 2, cy0 + 4.0, 2.2, "middle")
    if stack:
        sx0, sy0, sx1, sy1 = stack
        C.g_eq.add(C.d.polyline([(sx0, sy1), (sx0, sy0), (sx1, sy0), (sx1, sy1)], stroke_width=0.6))
    for i in range(burners):
        bx = x0 + (x1 - x0) * (i + 0.5) / burners
        C.g_eq.add(C.d.polygon([(bx - 2.2, y1), (bx + 2.2, y1), (bx, y1 - 5)], stroke_width=0.35))
    C.t(tag, x0 + 4, y1 - 8, 3.2, "start", bold=True)


def duct(C, pts, w=3.0):
    C.g_ln.add(C.d.polyline(pts, stroke_width=w, stroke="#000"))
    C.g_ln.add(C.d.polyline(pts, stroke_width=w - 0.9, stroke="#fff"))
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    from .pid_symbols import _dir
    C.arrow(x2, y2, _dir(x1, y1, x2, y2), L=3.0, Wd=1.6)


def damper(C, x, y, o="h", tag=None):
    C.butterfly(x, y, "h" if o == "h" else "v")
    if tag:
        C.t(tag, x + 3, y - 3, 2.0)


# ============================================================================= SHEET 004
def sheet_004():
    C = new_sheet(4, [
        "Passes shown schematically (convection + radiant in series per pass); 8 identical passes.",
        "Tube-skin thermocouples: 4 per pass (TI-1101..1132) - shown on heater vendor P&ID, alarmed in DCS.",
        "Pass flow SIS transmitters FT-10xxA/B/C (2oo3 per pass) independent from BPCS FT-10xx (SIF-101).",
        "Decoking (steam-air) connections and spool pieces at inlet / outlet manifolds by heater vendor.",
    ])
    eq_boxes(C, ["H-101"], w=90)
    H1 = C_.R["heaters"]["H-101"]
    n = H1["passes"]
    X0, X1, Y0, Y1 = 380.0, 600.0, 140.0, 345.0
    heater_box(C, X0, Y0, X1, Y1, "H-101", cells=2, stack=(560, 70, 580, Y0), burners=8)
    C.g_eq.add(C.d.line((450, Y0), (450, Y1 - 10), stroke_width=0.3, stroke_dasharray="3,1.5"))
    C.t("CONV.", 415, Y0 + 6, 2.2, "middle")
    C.t("RADIANT (2 CELLS)", 525, Y0 + 6, 2.2, "middle")
    C.t(f"{H1['burners']} BURNERS (FLOOR-FIRED, 2 CELLS) - SEE {dref(5)}", (X0 + X1) / 2, Y1 + 6, 2.1, "middle")
    ys = [176 + 22 * i for i in range(n)]
    xm, xo = 82.0, 660.0
    # inlet manifold (crude_h6)
    C.opc(50, 120, "l", "FROM E-111 (CIT)", dref(3))
    C.line("crude_h6", [(50, 120), (xm, 120), (xm, ys[-1])], lab=1, at=0.75, side=-1, arrow=False)
    ti(C, 76, 100, [(76, 120), (76, 104.6)], svc="H-101 inlet temperature (CIT)", line="crude_h6")
    # outlet manifold + transfer line
    C.pipe([(xo, ys[-1]), (xo, ys[0])], arrow=False)
    C.line("transfer", [(xo, ys[0]), (xo, 125), (790, 125)], lab=1, at=0.62)
    C.reducer(xo, 140, "v", True, note='24"x28"', note_side=1)
    C.opc(790, 125, "r", "TO C-101 FLASH ZONE", dref(6))
    for i, y in enumerate(ys):
        k = i + 1
        lp = f"FIC-{1010 + k}"
        C.dot(xm, y)
        C.line(f"h101_in{k}", [(xm, y), (X0, y)], lab=0, at=0.79, arrow=False)
        coil(C, X0 + 6, X1 - 6, y, n=22)
        C.pipe([(X0, y), (X0 + 6, y)], arrow=False)
        C.pipe([(X1 - 6, y), (X1, y)], arrow=False)
        C.line(f"h101_out{k}", [(X1, y), (xo, y)], lab=0, at=0.3, arrow=False)
        C.dot(xo, y)
        C.t(f"PASS {k}", X0 + 37, y - 4.2, 2.1, "middle", bold=True)
        # BPCS pass flow control
        C.orifice(100, y, "h")
        REG.inst(f"FE-{1010 + k}", C.sid, svc=f"H-101 pass {k} flow element", line=f"h101_in{k}")
        ctrl(C, lp, 100, y - 11, 122, y - 11, tap=[(100, y - 2.4), (100, y - 6.4)], line=f"h101_in{k}",
             vsig=[(126.6, y - 11), (153, y - 11), (153, y - 7)], fail="FO")
        C.station(137, y, 169, y, f"FV-{1010 + k}", "FO", bypass=False, red=False, drain=False,
                  tag_pos=(157, y - 5.5))
        # SIS pass flow 2oo3
        tags = [f"FT-{1010 + k}{c}" for c in "ABC"]
        sis_initiator(C, tags, 190, y - 11, f"FZLL-{1010 + k}", "SIF-101", 212, y - 11, 0, 0,
                      tap=[(184, y), (184, y - 11), (185.4, y - 11)])
        C.orifice(184, y, "h")
        C.sig([(216.6, y - 11), (240, y - 11)], "e")
        # pass outlet TI (feeds TDIC-1019)
        C.bub(630, y - 11, f"TI-{1010 + k}", "dcs", svc=f"H-101 pass {k} outlet temperature", line=f"h101_out{k}")
        C.tap([(622, y), (622, y - 11), (625.4, y - 11)])
        C.sig([(634.6, y - 11), (642, y - 11)], "d")
    C.sig([(240, ys[0] - 11), (240, ys[-1] + 14)], "e")
    C.ilk(240, ys[-1] + 18, "SIF-101")
    C.t("2oo3 PER PASS", 203, ys[0] - 24, 2.0, "middle")
    C.t("LOW-LOW PASS FLOW", 203, ys[0] - 21.4, 2.0, "middle")
    C.t(f"TO XV-1021/1022, XV-1026 ({dref(5)})", 246, ys[-1] + 19, 2.0)
    # TDIC-1019 pass balancing
    C.sig([(642, ys[0] - 11), (642, ys[-1] - 11)], "d")
    C.bub(700, 260, "TDIC-1019", "dcs", svc=C_.LOOPS["TDIC-1019"]["service"], loop="TDIC-1019")
    C.sig([(642, 260), (695.4, 260)], "d")
    C.t("BIAS TO FIC-1011..1018", 706, 260, 2.0)
    C.t("(TOTAL FLOW HELD)", 706, 263, 2.0)
    # COT control & SIS
    ctrl(C, "TIC-1020", 700, 145, 720, 145, tap=[(700, 125), (700, 140.4)], line="transfer")
    C.t("SP CASCADE TO PIC-1021", 726, 144, 2.0)
    C.t(f"({dref(5)}); FF FROM FIC-1001", 726, 147, 2.0)
    sis_initiator(C, ["TT-1020A", "TT-1020B", "TT-1020C"], 745, 105, "TZHH-1020", "SIF-106", 770, 105, 0, 0,
                  tap=[(745, 125), (745, 109.6)], vote="2oo3")
    C.ilk(795, 105, "SIF-106", below=True)
    C.sig([(774.6, 105), (791, 105)], "e")
    # stripping steam superheat coil
    C.opc(50, 92, "l", "LP STEAM HEADER", dref(16))
    C.line("ls_ss_in", [(50, 92), (400, 92), (400, Y0)], lab=0, at=0.5)
    C.g_eq.add(C.d.rect((394, Y0 + 9), (52, 6), stroke_width=0.3))
    C.t("SS SUPERHEAT COIL", 420, Y0 + 19, 2.0, "middle")
    C.line("ls_ss_out", [(440, Y0), (440, 112), (540, 112), (540, 70), (790, 70)], lab=3, at=0.55)
    C.opc(790, 70, "r", "STRIPPING STEAM HDR", dref(6))
    C.opcv(650, 46, "u", "BFW HEADER", dref(16))
    C.line("bfw_desup", [(650, 46), (650, 70)], lab=None)
    C.lab(REG.no("bfw_desup"), xy=(656, 44), size=2.0)
    C.cv(650, 60, "v", "TV-1024", "FC", side=-1, tag_pos=(643, 55))
    C.check(650, 66, "d")
    ctrl(C, "TIC-1024", 700, 55, 680, 50, tap=[(700, 70), (700, 59.6)], line="ls_ss_out",
         sig=[(695.4, 55), (684.6, 55), (684.6, 50)], vsig=[(675.4, 50), (660, 50), (660, 60), (657, 60)], fail="FC")
    C.t("350 C", 686, 45, 2.0)
    ptag = free_tag(C, "PI")
    C.bub(740, 55, ptag, "dcs", svc="Stripping steam pressure", line="ls_ss_out")
    C.tap([(740, 70), (740, 59.6)])
    return save(C)


# ============================================================================= SHEET 005
def sif_block(C, x0, y0, w, sifs, title="H-101 BMS / SIS (SIL-RATED PLC)"):
    h = 10 + 14 * len(sifs)
    C.g_eq.add(C.d.rect((x0, y0), (w, h), stroke_width=0.5))
    C.t(title, x0 + w / 2, y0 + 5, 2.3, "middle", bold=True)
    pos = {}
    for i, sf in enumerate(sifs):
        y = y0 + 15 + i * 14
        C.ilk(x0 + 10, y, "", r=3.6)
        f = C_.SIFS[sf]
        C.t(f"{sf} ({f['sil']})", x0 + 16, y - 1.0, 2.1, bold=True)
        C.t(f["function"][:46], x0 + 16, y + 2.0, 2.0)
        pos[sf] = (x0 + 10, y)
    return pos, h


def sheet_005():
    C = new_sheet(5, [
        "Burner management per API 556 / NFPA 85: purge, light-off and trip sequences in BMS (SIS logic).",
        "Main fuel SSOVs XV-1021/1022 with vent XV (double block & bleed); all fail closed (vent fails open).",
        "Fuel / air cross-limiting: AIC-1022 trims FIC-1025 set point; PIC-1021 low-select vs. minimum fire.",
        "Snuffing steam manifold valves located >= 15 m from heater (API 560); one per cell + header boxes.",
        "Ducts shown double-line; K-101A/B and K-102A/B are 2 x 100 % (one fan symbol shown per pair).",
    ])
    eq_boxes(C, ["H-101", "E-120", "K-101A/B", "K-102A/B"], w=80)
    X0, X1, Y0, Y1 = 470.0, 640.0, 160.0, 330.0
    heater_box(C, X0, Y0, X1, Y1, "H-101", cells=2, conv=(510, 115, 600, Y0), burners=8)
    C.t("RADIANT", 555, 200, 2.4, "middle")
    C.g_eq.add(C.d.rect((X0, Y1), (X1 - X0, 15), stroke_width=0.4))
    C.t("WINDBOX / AIR PLENUM", (X0 + X1) / 2, Y1 + 10, 2.1, "middle")
    # E-120 APH
    C.g_eq.add(C.d.rect((370, 65), (60, 35), stroke_width=0.5))
    C.g_eq.add(C.d.line((370, 65), (430, 100), stroke_width=0.3))
    C.t("E-120 (APH)", 400, 61, 2.6, "middle", bold=True)
    # flue gas path
    duct(C, [(555, 115), (555, 78), (430, 78)])
    C.t("FLUE GAS", 495, 75, 2.1, "middle")
    C.fan(330, 78, None)
    duct(C, [(370, 78), (335, 78)])
    duct(C, [(325, 78), (290, 78), (290, 38)])
    C.t("K-102A/B (ID)", 330, 89, 2.2, "middle", bold=True)
    C.t("TO STACK", 300, 40, 2.2, "start", bold=True)
    damper(C, 290, 55, "v")
    C.t("STACK DAMPER", 287, 56, 2.0, "end")
    # combustion air path
    C.fan(330, 140, None)
    C.t("K-101A/B (FD)", 330, 151, 2.2, "middle", bold=True)
    duct(C, [(270, 140), (325, 140)])
    C.t("AIR", 266, 141, 2.1, "end")
    damper(C, 305, 140, "h")
    C.t("INLET VANES", 305, 135, 2.0, "middle")
    duct(C, [(335, 140), (390, 140), (390, 100)])
    duct(C, [(415, 100), (415, 338), (X0, 338)])
    C.t("PREHEATED AIR", 421, 250, 2.1, "start", rot=-90)
    C.orifice(360, 140, "h")
    REG.inst("FE-1025", C.sid, svc="H-101 combustion air flow element (venturi)")
    ctrl(C, "FIC-1025", 360, 160, 335, 175, tap=[(360, 142.4), (360, 155.4)],
         sig=[(355.4, 160), (345, 160), (345, 175), (339.6, 175)],
         vsig=[(330.4, 175), (305, 175), (305, 141.8)], fail="FO")
    REG.inst("FV-1025", C.sid, svc="H-101 FD fan inlet vanes (FIC-1025)", fail="FO")
    C.t("SP FROM AIC-1022", 330, 183, 2.0, "middle")
    # arch analyser / draft
    C.bub(660, 140, "AT-1022", "field", svc="H-101 arch O2 / CO analyser")
    C.tap([(X1, 168), (650, 168), (650, 140), (655.4, 140)])
    C.bub(685, 140, "AIC-1022", "dcs", svc=C_.LOOPS["AIC-1022"]["service"], loop="AIC-1022")
    C.sig([(664.6, 140), (680.4, 140)], "e")
    C.t("SP TRIM TO FIC-1025", 691, 136, 2.0)
    ctrl(C, "PIC-1023", 660, 190, 685, 190, tap=[(X1, 190), (655.4, 190)])
    C.t("-2.5 mmH2O", 691, 186, 2.0)
    C.bub(710, 190, "PY-1023", "field", svc="ID fan VSD speed signal / stack damper", r=4.0)
    C.sig([(689.6, 190), (706, 190)], "e")
    C.t("TO K-102A/B VSD", 716, 189, 2.0)
    C.t("& PV-1023 STACK DAMPER", 716, 192, 2.0)
    REG.inst("PV-1023", C.sid, svc="H-101 stack damper actuator", fail="FO")
    sis_initiator(C, ["PT-1029A", "PT-1029B", "PT-1029C"], 660, 225, "PZHH-1029", "SIF-105", 685, 225, 0, 0,
                  tap=[(X1, 225), (655.4, 225)], vote="2oo3")
    C.t("TO SIF-105", 691, 232, 2.0)
    ti(C, 660, 105, [(600, 125), (650, 125), (650, 105), (655.4, 105)], svc="H-101 flue gas temperature (bridgewall)")
    C.bub(560, 368, "BS-1028", "field", sys="BMS", svc="H-101 flame scanners (1 per burner, 16 off)")
    C.tap([(560, Y1 + 15), (560, 363.4)])
    C.bub(585, 368, "BZLL-1028", "sis", sys="SIS", sif="SIF-104", svc="Loss of flame (all burners)")
    C.sig([(564.6, 368), (580.4, 368)], "e")
    C.t("TO SIF-104", 591, 369, 2.0)
    # snuffing steam
    C.opc(790, 290, "r", "LP STEAM HEADER", dref(16), flow="in")
    C.line("ls_snuff_h101", [(790, 290), (700, 290), (700, 250), (X1, 250)], lab=0, at=0.5)
    C.pipe([(700, 290), (X1, 290)], util=True)
    C.xv(760, 290, "h", "HV-1290", "FC", tag_pos=(763, 284))
    REG.inst("HV-1290", C.sid, sys="F&G", fail="FC", svc="H-101 snuffing steam valve (remote open from CCR / F&G)")
    C.t("SNUFFING STEAM (CELLS / HEADER BOXES)", 698, 246, 2.0, "end")
    # ---- fuel gas train
    yf = 430.0
    C.opc(50, yf, "l", "FUEL GAS FROM D-103", dref(16))
    C.line("fg_h101", [(50, yf), (275, yf)], lab=0, at=0.13, arrow=False)
    C.strainer(78, yf)
    ptag = free_tag(C, "PI")
    C.bub(92, yf - 14, ptag, "field", svc="H-101 fuel gas supply pressure", line="fg_h101", r=4.0)
    C.tap([(92, yf), (92, yf - 10)])
    C.gate(104, yf, "h")
    C.xv(120, yf, "h", "XV-1021", "FC", tag_pos=(123, yf - 6))
    C.xv(160, yf, "h", "XV-1022", "FC", tag_pos=(163, yf - 6))
    for t in ("XV-1021", "XV-1022"):
        REG.inst(t, C.sid, sys="SIS", sif="SIF-101", fail="FC", svc="H-101 main fuel gas SSOV")
    vtag = free_tag(C, "XV")
    C.line("fl_h101_vent", [(140, yf), (140, yf + 24), (110, yf + 24)], lab=1, at=0.5, side=1)
    C.dot(140, yf)
    C.xv(140, yf + 12, "v", vtag, "FO", side=1, tag_pos=(146, yf + 12))
    REG.inst(vtag, C.sid, sys="SIS", sif="SIF-101", fail="FO", svc="H-101 FG double block & bleed vent")
    C.t("TO FLARE", 108, yf + 25, 2.0, "end")
    for xx in (1021, 1022):
        free_tag(C, "ZSC")   # limit switches are part of XV-1021/1022 (ZSO/ZSC in XV signal); number unused
    C.station(185, yf, 230, yf, "PV-1021", "FC", byp=1, tag_pos=(211, yf - 6))
    ctrl(C, "PIC-1021", 255, yf - 18, 230, yf - 30, tap=[(255, yf), (255, yf - 13.4)], line="fg_h101_b",
         sig=[(250.4, yf - 18), (240, yf - 18), (240, yf - 30), (234.6, yf - 30)],
         vsig=[(225.4, yf - 30), (207.5, yf - 30), (207.5, yf - 10.8)], fail="FC")
    C.t("SP FROM TIC-1020", 225, yf - 40, 2.0, "end")
    C.t(f"({dref(4)})", 225, yf - 37.4, 2.0, "end")
    C.line("fg_h101_b", [(275, yf), (455, yf), (455, 360), (X1 - 4, 360)], lab=0, at=0.55, arrow=False)
    C.orifice(385, yf, "h")
    REG.inst("FE-1021", C.sid, svc="H-101 fuel gas flow element", line="fg_h101_b")
    C.bub(385, yf - 16, "FT-1021", "field", svc=IC_AN["FT-1021"], line='fg_h101_b')
    C.tap([(385, yf - 2.4), (385, yf - 11.4)])
    C.t("TO FUEL/AIR CROSS-LIMIT", 391, yf - 15, 2.0)
    sis_initiator(C, ["PT-1027A", "PT-1027B", "PT-1027C"], 300, yf + 18, "PZLL-1027", "SIF-102", 325, yf + 18, 0, 0,
                  tap=[(300, yf), (300, yf + 13.4)], vote="2oo3")
    C.bub(350, yf + 18, "PZHH-1027", "sis", sys="SIS", sif="SIF-103", svc=C_.SIFS["SIF-103"]["function"])
    C.sig([(329.6, yf + 18), (345.4, yf + 18)], "e")
    C.t("TO SIF-102 / SIF-103", 356, yf + 28, 2.0)
    ybn = Y1 + 15
    for i in range(8):
        bx = X0 + (X1 - X0) * (i + 0.5) / 8
        C.pipe([(bx, 360), (bx, ybn)], arrow=False)
        C.pipe([(bx + 3, 352), (bx + 3, ybn)], arrow=False, util=True)
    yp = 470.0
    C.opc(50, yp, "l", "PILOT GAS FROM D-103", dref(16))
    C.line("fg_h101_pil", [(50, yp), (445, yp), (445, 352), (X1 - 1, 352)], lab=0, at=0.5, arrow=False)
    C.gate(80, yp, "h")
    pcv = free_tag(C, "PCV")
    C.cv(100, yp, "h", pcv, "", act="dia", tag_pos=(103, yp - 6))
    REG.inst(pcv, C.sid, svc="H-101 pilot gas self-acting regulator")
    C.xv(125, yp, "h", "XV-1026", "FC", tag_pos=(128, yp - 6))
    REG.inst("XV-1026", C.sid, sys="SIS", sif="SIF-101", fail="FC", svc="H-101 pilot gas SSOV")
    C.t("MAIN GAS", X1 + 2, 361, 2.0)
    C.t("PILOT GAS", X1 + 2, 353, 2.0)
    # SIS logic block feeding final elements
    pos, h = sif_block(C, 40, 270, 140, ["SIF-101", "SIF-102", "SIF-103", "SIF-104", "SIF-105", "SIF-106"])
    yb = 270 + h
    C.t(f"INPUTS: FZLL-1011..1018, TZHH-1020 ({dref(4)}); PZLL/PZHH-1027, BZLL-1028, PZHH-1029 (THIS SHEET)",
        40, 266, 2.0)
    C.sig([(120, yb), (120, yf - 9.8)], "e")
    C.sig([(160, yb), (160, yf - 9.8)], "e")
    C.sig([(146, yb), (146, 412), (152, 412), (152, yf + 4)], "e")
    C.sig([(60, yb), (60, 458), (125, 458), (125, yp - 9.8)], "e")
    C.t("TRIP: XV-1021/1022 + XV-1026 CLOSE, VENT XV OPEN", 185, yb + 5, 2.0)
    return save(C)


# ============================================================================= columns
def col_trays(C, x, w, ymap, num_side="r"):
    for n, y in ymap.items():
        C.tray(x, w, y, n, "l" if n % 2 else "r", num_side)


def swage(C, x, w1, w2, y0, y1):
    C.g_eq.add(C.d.line((x - w1 / 2, y0), (x - w2 / 2, y1)))
    C.g_eq.add(C.d.line((x + w1 / 2, y0), (x + w2 / 2, y1)))


# ============================================================================= SHEET 006
def sheet_006():
    C = new_sheet(6, [
        "Trays 1-25 and overhead on " + dref(7) + ". Stripping section trays 36-41 (6 trays, 4.1 m ID).",
        "Overflash measured on external loop FI-1080 (minimum overflash alarm, APC constraint).",
        "EIV-1121 remotely operated isolation valve (ROSOV), fire-safe, actuated from CCR / field (SIF-204).",
        "P-112 minimum flow returns to C-101 sump via RO.",
    ])
    eq_boxes(C, ["C-101", "P-112A/B"], w=95)
    x, w, w2 = 300.0, 60.0, 36.0
    ytop = 70.0
    ym = {n: 85 + (n - 26) * 19 for n in range(26, 36)}
    C.column(x, ytop, 300, w, top=False, bot=False, brk_top=True)
    swage(C, x, w, w2, 300, 318)
    C.column(x, 318, 470, w2, top=False, bot=True)
    col_trays(C, x, w, {n: y for n, y in ym.items() if n != 35})
    C.pan(x, w, ym[35], None)
    C.t("35 (WASH / OVERFLASH PAN)", x + w / 2 - 1.2, ym[35] - 6.5, 2.0, "end")
    C.t("TRAYS 1-25: SEE " + dref(7), x, ytop - 5, 2.1, "middle", bold=True)
    ys = {n: 335 + (n - 36) * 22 for n in range(36, 42)}
    col_trays(C, x, w2, ys)
    C.t("FLASH ZONE", x, 290, 2.2, "middle", bold=True)
    C.t("C-101", x - w / 2 - 4, 120, 3.4, "end", bold=True)
    C.t("WASH ZONE", x - w / 2 - 4, ym[33] + 3, 2.1, "end")
    C.t("STRIPPING", x - w2 / 2 - 4, 380, 2.1, "end")
    xl, xr = x - w / 2, x + w / 2
    # transfer line -> flash zone (N1)
    C.opc(50, 280, "l", "FROM H-101", dref(4))
    C.line("transfer", [(50, 280), (xl - 2.5, 280)], lab=0, at=0.45)
    C.noz(xl, 280, "l", "N1")
    C.t("VAPOUR HORN", x, 280, 2.0, "middle")
    ti(C, 230, 262, [(230, 280), (230, 266.6)], svc="C-101 flash zone feed temperature (COT)", line="transfer")
    # AGO draw tray 32 (N6) and vapour return tray 31 (N7) -> left side
    yd, yv = ym[32] + 3.5, ym[31] - 4
    C.noz(xl, yd, "l", "N6")
    C.line("ago_draw", [(xl - 2.5, yd), (50, yd)], lab=0, at=0.4)
    C.opc(50, yd, "l", "TO C-104 (FV-1070)", dref(8), flow="out")
    C.noz(xl, yv, "l", "N7")
    C.opc(50, yv, "l", "FROM C-104 OVHD", dref(8))
    C.line("ago_vret", [(50, yv), (xl - 2.5, yv)], lab=0, at=0.4)
    ti(C, 200, yd + 14, [(200, yd), (200, yd + 9.4)], svc="AGO draw temperature", line="ago_draw")
    # overflash external loop (N4 -> FI-1080 -> N5)
    yo1, yo2 = ym[35] + 2.5, 300
    C.noz(xr, yo1, "r", "N4")
    C.line("ovfl", [(xr + 2.5, yo1), (360, yo1), (360, yo2), (xr + 2.5, yo2)], lab=1, at=0.5, side=1)
    C.noz(xr, yo2, "r", "N5")
    C.orifice(360, 282, "v")
    REG.inst("FE-1080", C.sid, svc="Overflash flow element", line="ovfl")
    C.bub(380, 282, "FT-1080", "field", svc=C_.LOOPS["FI-1080"]["service"], line="ovfl", loop="FI-1080")
    C.tap([(362.4, 282), (375.4, 282)])
    C.bub(405, 282, "FI-1080", "dcs", svc=C_.LOOPS["FI-1080"]["service"], loop="FI-1080")
    C.sig([(384.6, 282), (400.4, 282)], "e")
    C.t("FAL (MIN. OVERFLASH)", 411, 283, 2.0)
    C.gate(360, yo1 + 12, "v")
    # pressure / temperature
    ptag = free_tag(C, "PT")
    C.bub(390, 240, ptag, "dcs", svc="C-101 flash zone pressure")
    C.tap([(xr, 240), (385.4, 240)])
    pd = free_tag(C, "PDI")
    C.bub(390, 215, pd, "dcs", svc="C-101 column dP (top - flash zone)")
    C.tap([(xr, 215), (385.4, 215)])
    C.t("FROM TOP (" + dref(7) + ")", 396, 216, 2.0)
    # stripping steam (N3) + SS header to strippers
    yss = 400.0
    C.opc(790, yss, "r", "STRIPPING STEAM", dref(4), flow="in")
    C.line("ls_c101", [(790, yss), (380, yss), (380, ys[41] + 8), (x + w2 / 2 + 2.5, ys[41] + 8)], lab=0, at=0.18)
    C.noz(x + w2 / 2, ys[41] + 8, "r", "N3")
    C.orifice(560, yss, "h")
    REG.inst("FE-1081", C.sid, svc="C-101 stripping steam flow element", line="ls_c101")
    C.station(470, yss, 520, yss, "FV-1081", "FC", byp=-1, tag_pos=(498, yss - 6))
    ctrl(C, "FIC-1081", 560, yss + 18, 530, yss + 18, tap=[(560, yss + 2.4), (560, yss + 13.4)],
         sig=[(555.4, yss + 18), (534.6, yss + 18)], vsig=[(525.4, yss + 18), (495, yss + 18), (495, yss - 9.8)],
         fail="FC", line="ls_c101")
    C.t("RATIO TO AR (10 lb/bbl)", 536, yss + 26, 2.0, "middle")
    C.dot(650, yss)
    C.line("ls_ss_hdr", [(650, yss), (650, 370), (790, 370)], lab=1, at=0.5)
    C.opc(790, 370, "r", "SS TO C-102/103/104", dref(8))
    # bottoms -> EIV-1121 -> P-112
    yb = 470 + 9
    pp = pump_pair(C, 440, 540, "P-112", "ar_s", "ar_d")
    C.line("ar_s", [(x, yb), (x, pp["s"][1]), pp["s"]], lab=1, at=0.5, arrow=False)
    C.noz(x, 474, "d", "N2") if False else None
    C.xv(x, 505, "v", "EIV-1121", "FC", side=1, tag_pos=(x + 9, 503), kind="ball")
    REG.inst("EIV-1121", C.sid, sys="SIS", sif="SIF-204", fail="FC", svc=C_.SIFS["SIF-204"]["function"])
    C.bub(345, 520, "HS-1121", "panel", sys="SIS", sif="SIF-204", svc="EIV-1121 manual close (CCR + field)")
    C.ilk(345, 500, "SIF-204", below=False)
    C.sig([(345, 515.4), (345, 504)], "e")
    C.sig([(341, 500), (x + 7, 500), (x + 7, 505)], "e")
    REG.inst("BY-1121", C.sid, sys="F&G", sif="SIF-204", svc="Fire confirmation from F&G (P-112 area)")
    C.t("+ F&G FIRE CONFIRM. (BY-1121)", 350, 497, 2.0)
    # min flow return
    yd2 = pp["dr"][1]
    C.line("p112_mf", [(460, yd2), (460, 464), (x + w2 / 2 + 2.5, 464)], lab=1, at=0.62)
    C.dot(460, yd2)
    C.noz(x + w2 / 2, 464, "r", "N21")
    C.orifice(430, 464, "h", ro=True)
    C.gate(445, 464, "h")
    # discharge -> FV-1083 -> XV-1083 -> H-201
    C.line("ar_d", [pp["dr"], (630, yd2), (630, 455), (790, 455)], lab=2, at=0.55)
    C.opc(790, 455, "r", "TO H-201", dref(12))
    C.orifice(500, yd2, "h")
    REG.inst("FE-1083", C.sid, svc="AR flow element", line="ar_d")
    C.station(520, yd2, 565, yd2, "FV-1083", "FC", byp=1, tag_pos=(546, yd2 - 6))
    ctrl(C, "FIC-1083", 500, yd2 - 16, 520, yd2 - 30, tap=[(500, yd2 - 2.4), (500, yd2 - 11.4)],
         sig=[(504.6, yd2 - 16), (510, yd2 - 16), (510, yd2 - 30), (515.4, yd2 - 30)],
         vsig=[(524.6, yd2 - 30), (542.5, yd2 - 30), (542.5, yd2 - 10.4)], fail="FC", line="ar_d")
    C.t("SP FROM LIC-1082; RATIO-SPLITS H-201 PASSES", 527, yd2 - 37, 2.0)
    C.xv(595, yd2, "h", "XV-1083", "FC", tag_pos=(598, yd2 - 6))
    REG.inst("XV-1083", C.sid, sys="SIS", sif="SIF-203", fail="FC", svc=C_.SIFS["SIF-203"]["function"])
    C.ilk(595, yd2 - 26, "SIF-203", below=False)
    C.sig([(595, yd2 - 22), (595, yd2 - 9.8)], "e")
    C.t("FROM LZHH-2024 (" + dref(13) + ")", 590, yd2 - 34, 2.0, "middle")
    ti(C, 655, 440, [(655, 455), (655, 444.6)], svc="AR to H-201 temperature", line="ar_d")
    # level control + SIS high-high
    yl = 440.0
    C.tap([(x - w2 / 2, yl), (255.4, yl)])
    ctrl(C, "LIC-1082", 250, yl, 225, yl, line="ar_s", sig=[(245.4, yl), (229.6, yl)])
    C.t("SP TO FIC-1083", 225, yl + 8, 2.0, "middle")
    sis_initiator(C, ["LT-1082B"], 250, yl - 25, "LZHH-1082", "SIF-108", 225, yl - 25, 0, 0,
                  tap=[(x - w2 / 2, yl - 25), (254.6, yl - 25)])
    C.ilk(200, yl - 25, "SIF-108")
    C.sig([(220.4, yl - 25), (204, yl - 25)], "e")
    C.t("TO XV-1001 / P-101 TRIP", 195, yl - 12, 2.0, "end")
    C.t("(" + dref(1) + ")", 195, yl - 9.4, 2.0, "end")
    lg = free_tag(C, "LG")
    C.bub(250, yl + 22, lg, "field", svc="C-101 bottom level gauge")
    C.tap([(x - w2 / 2, yl + 14), (250, yl + 14), (250, yl + 17.4)])
    ti(C, 275, 545, [(x, 545), (279.6, 545)], svc="C-101 bottoms temperature", line="ar_s")
    C.line("bd_c101", [(x - 6, yb - 1), (x - 6, 520), (260, 520)], lab=None)
    C.gate(x - 6, 512, "v")
    C.t("TO CLOSED DRAIN", 258, 521, 2.0, "end")
    C.t(REG.no("bd_c101"), 258, 517.5, 2.0, "end")
    return save(C)


# ============================================================================= SHEET 007
def sheet_007():
    C = new_sheet(7, [
        "Trays 26-41, flash zone and bottoms on " + dref(6) + ". Trays 1-5 Monel-lined; 410S trays below.",
        "Pumparound return temperatures controlled by exchanger bypass (TIC-1041/1043/1045 on PID-001/003).",
        "PSV-1001: 4 x T orifice on C-101 top head, CSO inlet/outlet blocks; discharge to closed flare header.",
        "Side-stripper draws / vapour returns: control on " + dref(8) + ".",
    ])
    eq_boxes(C, ["C-101", "P-106A/B", "P-107A/B", "P-108A/B"], w=88)
    x, w = 300.0, 60.0
    ytop = 92.0
    ym = {n: 112 + (n - 1) * 14.6 for n in range(1, 26)}
    C.column(x, ytop, 478, w, top=True, bot=False, brk_bot=True)
    col_trays(C, x, w, ym)
    C.t("C-101", x - w / 2 - 4, 300, 3.4, "end", bold=True)
    C.t("TRAYS 26-41: SEE " + dref(6), x, 486, 2.1, "middle", bold=True)
    xl, xr = x - w / 2, x + w / 2
    # overhead vapour (N19) + PSV-1001
    yapex = ytop - 9
    C.noz(x, yapex, "u", "N19")
    C.line("oh_vap", [(x, yapex - 2.5), (x, 64), (790, 64)], lab=1, at=0.5)
    C.opc(790, 64, "r", "TO A-101", dref(9))
    pv = C_.PSV["PSV-1001"]
    C.psv(x - 18, ytop - 5, "PSV-1001", pv["set_barg"], f"{pv['count']} x {pv['orifice']}", up=16, out="l",
          outlen=18, dest="FLARE", text_side=1)
    REG.use_line("1001_out", C.sid)
    C.lab(REG.no("1001_out"), xy=(x - 46, ytop - 25))
    ptag = free_tag(C, "PT")
    C.bub(345, 80, ptag, "dcs", svc="C-101 top pressure")
    C.tap([(x + 12, ytop - 6), (x + 12, 80), (340.4, 80)])
    # TIC-1030 top temperature
    ctrl(C, "TIC-1030", 360, ym[1] - 2, 385, ym[1] - 2, tap=[(xr, ym[1] - 2), (355.4, ym[1] - 2)], line="oh_vap")
    C.t("SP CASCADE TO FIC-1031 (" + dref(9) + ")", 391, ym[1] - 1, 2.0)
    # left side returns
    lefts = [("reflux", ytop + 3, "FROM P-103A/B (FV-1031)", 9, "N18"),
             ("tpa_r", ym[1] - 5, "FROM E-101 (TPA RETURN)", 1, "N16"),
             ("mpa_r", ym[11] - 5, "FROM E-106 (MPA RETURN)", 3, "N12"),
             ("bpa_r", ym[23] - 5, "FROM E-113 (BPA RETURN)", 3, "N8")]
    for key, y, txt, sh, nz in lefts:
        C.opc(50, y, "l", txt, dref(sh))
        C.line(key, [(50, y), (xl - 2.5, y)], lab=0, at=0.5)
        C.noz(xl, y, "l", nz)
    # stripper draws (right side) and vapour returns
    rights = [("kero_vret", ym[9] - 5, "FROM C-102 OVHD", "N14", "in"),
              ("kero_draw", ym[10] + 4, "TO C-102 (FV-1050)", "N15", "out"),
              ("dsl_vret", ym[21] - 5, "FROM C-103 OVHD", "N10", "in"),
              ("dsl_draw", ym[22] + 4, "TO C-103 (FV-1060)", "N11", "out")]
    for key, y, txt, nz, fl in rights:
        C.noz(xr, y, "r", nz)
        if fl == "in":
            C.line(key, [(790, y), (xr + 2.5, y)], lab=0, at=0.5)
            C.opc(790, y, "r", txt, dref(8), flow="in")
        else:
            C.line(key, [(xr + 2.5, y), (790, y)], lab=0, at=0.5)
            C.opc(790, y, "r", txt, dref(8))
            ti(C, 360, y + 13, [(360, y), (360, y + 8.4)], svc=f"{key.split('_')[0].title()} draw temperature",
               line=key)
    # pumparound draws -> pumps -> exchangers
    pas = [("TPA", 3, "tpa_s", "tpa_d", "P-106", 175, "FIC-1040", "TO E-101", 1, "N17"),
           ("MPA", 13, "mpa_s", "mpa_d", "P-107", 320, "FIC-1042", "TO E-106", 3, "N13"),
           ("BPA", 25, "bpa_s", "bpa_d", "P-108", 490, "FIC-1044", "TO E-110", 3, "N9")]
    for nm, tray, sk, dk, pt, yp, lp, to, sh, nz in pas:
        yd = ym[tray] + 4
        xp = 470.0
        pp = pump_pair(C, xp, yp, pt, sk, dk)
        C.noz(xr, yd, "r", nz)
        C.line(sk, [(xr + 2.5, yd), (400, yd), (400, pp["s"][1]), pp["s"]], lab=1, at=0.5, arrow=False)
        C.gate(345, yd, "h")
        ydd = pp["dr"][1]
        C.line(dk, [pp["dr"], (790, ydd)], lab=0, at=0.82)
        C.opc(790, ydd, "r", to, dref(sh))
        C.orifice(580, ydd, "h")
        REG.inst(f"FE-{lp[4:]}", C.sid, svc=f"{nm} flow element", line=dk)
        C.station(600, ydd, 645, ydd, f"FV-{lp[4:]}", "FC" if nm != "BPA" else "FO", byp=1,
                  tag_pos=(626, ydd - 6))
        ctrl(C, lp, 580, ydd - 16, 600, ydd - 28, tap=[(580, ydd - 2.4), (580, ydd - 11.4)],
             sig=[(584.6, ydd - 16), (590, ydd - 16), (590, ydd - 28), (595.4, ydd - 28)],
             vsig=[(604.6, ydd - 28), (622.5, ydd - 28), (622.5, ydd - 10.4)], fail="FO", line=dk)
        ti(C, 360, yd + 13, [(360, yd), (360, yd + 8.4)], svc=f"{nm} draw temperature", line=sk)
        C.t(f"{nm} DRAW (TRAY {tray})", 405, yd - 2, 2.0)
    return save(C)

# ============================================================================= SHEET 008
def sheet_008():
    C = new_sheet(8, [
        "Side-stripper vapours return to C-101 one tray above draw; strippers protected by PSV-1009 (fire case).",
        "Stripping steam ratio to product rate (6 lb/bbl) via FIC-1054/1064/1074.",
        "Product rundown temperatures: kerosene 45 C, diesel 55 C, AGO 60 C (air coolers with VFD on one fan).",
    ])
    eq_boxes(C, ["C-102", "C-103", "C-104", "P-109A/B", "P-110A/B", "P-111A/B", "A-103", "A-104", "A-105"], w=86,
             gap=2.0) if False else eq_boxes(C, ["C-102", "C-103", "C-104", "P-109A/B", "P-110A/B", "P-111A/B"], w=88)
    units = [
        ("C-102", 20, "kero", "ls_102", "P-109", "A-103", 1050, ("C-101 TRAY 10", 7), ("C-101 TRAY 9", 7),
         ("TO E-102", 1), ("FROM E-102", 1), "KEROSENE TO KHT", "16"),
        ("C-103", 240, "dsl", "ls_103", "P-110", "A-104", 1060, ("C-101 TRAY 22", 7), ("C-101 TRAY 21", 7),
         ("TO E-107", 3), ("FROM E-104", 1), "DIESEL TO DHT", "17"),
        ("C-104", 460, "ago", "ls_104", "P-111", "A-105", 1070, ("C-101 TRAY 32", 6), ("C-101 TRAY 31", 6),
         ("TO E-109", 3), ("FROM E-109", 3), "AGO TO DHT / FCC", "18"),
    ]
    ysh = 290.0
    C.opc(50, ysh, "l", "STRIPPING STEAM", dref(6))
    C.line("ls_ss_hdr", [(50, ysh), (650, ysh)], lab=0, at=0.06, arrow=False)
    for tag, x0, k, lsk, pump, ac, lp, dfrom, vto, pto, rfrom, rdtxt, strm in units:
        xc = x0 + 120.0
        y0, y1, w = 120.0, 260.0, 30.0
        C.column(xc, y0, y1, w)
        col_trays(C, xc, w, {i: 135 + 20 * (i - 1) for i in range(1, 7)})
        C.t(tag, xc - w / 2 - 3, 200, 3.0, "end", bold=True)
        # draw from C-101 -> FV -> top tray
        yd = 100.0
        C.opc(x0 + 36, yd, "l", "FROM " + dfrom[0], dref(dfrom[1]))
        C.line(f"{k}_draw", [(x0 + 36, yd), (x0 + 97, yd), (x0 + 97, 128), (xc - w / 2 - 2.5, 128)], lab=1, at=0.5,
               side=-1)
        C.noz(xc - w / 2, 128, "l")
        C.orifice(x0 + 42, yd, "h")
        REG.inst(f"FE-{lp}", C.sid, svc=f"{tag} feed (draw) flow element", line=f"{k}_draw")
        C.station(x0 + 50, yd, x0 + 92, yd, f"FV-{lp}", "FC", byp=1, tag_pos=(x0 + 74.5, yd - 6))
        ctrl(C, f"FIC-{lp}", x0 + 42, yd - 16, x0 + 60, yd - 22, tap=[(x0 + 42, yd - 2.4), (x0 + 42, yd - 11.4)],
             sig=[(x0 + 46.6, yd - 16), (x0 + 50, yd - 16), (x0 + 50, yd - 22), (x0 + 55.4, yd - 22)],
             vsig=[(x0 + 64.6, yd - 22), (x0 + 71, yd - 22), (x0 + 71, yd - 10.4)], fail="FC", line=f"{k}_draw")
        # vapour return
        C.noz(xc, y0 - 7.5, "u")
        C.line(f"{k}_vret", [(xc, y0 - 10), (xc, 70), (xc + 40, 70)], lab=0, at=0.35, side=1)
        C.opc(xc + 40, 70, "r", "TO " + vto[0], dref(vto[1]))
        if tag == "C-103":
            pv = C_.PSV["PSV-1009"]
            C.psv(xc + 12, y0 - 5, "PSV-1009", pv["set_barg"], f"1{pv['orifice']}", up=16, out="r", outlen=26,
                  dest="FLARE", text_side=1)
            REG.use_line("psv1009_out", C.sid)
            C.t(REG.no("psv1009_out"), xc + 40, y0 - 26, 2.0, "start")
        ptag = free_tag(C, "PI")
        C.bub(xc - 28, y0 + 5, ptag, "field", svc=f"{tag} pressure", r=4.0)
        C.tap([(xc - w / 2, y0 + 5), (xc - 24, y0 + 5)])
        # stripping steam
        xs = xc + 60
        C.dot(xs, ysh)
        C.line(lsk, [(xs, ysh), (xs, 250), (xc + w / 2 + 2.5, 250)], lab=0, at=0.5, side=-1)
        C.noz(xc + w / 2, 250, "r")
        C.station(xc + 20, 250, xc + 56, 250, f"FV-{lp + 4}", "FC", bypass=False, red=False, drain=False,
                  tag_pos=(xc + 41.5, 244))
        C.orifice(xs, 270, "v")
        REG.inst(f"FE-{lp + 4}", C.sid, svc=f"{tag} stripping steam flow element", line=lsk)
        ctrl(C, f"FIC-{lp + 4}", xc + 80, 270, xc + 80, 252, tap=[(xs + 2.4, 270), (xc + 75.4, 270)],
             vsig=[(xc + 80, 247.4), (xc + 80, 234), (xc + 38, 234), (xc + 38, 243)], fail="FC", line=lsk)
        # bottoms -> pumps
        pp = pump_pair(C, xc + 20, 350, pump, f"{k}_ps", f"{k}_pd")
        C.noz(xc, y1 + 7.5, "d")
        C.line(f"{k}_ps", [(xc, y1 + 10), (xc, pp["s"][1]), pp["s"]], lab=None, arrow=False)
        C.lab(REG.no(f"{k}_ps"), [(xc, y1 + 10), (xc, pp["s"][1])], 0, 0.62, -1)
        C.hop(xc, ysh, "h")
        C.line(f"{k}_pd", [pp["dr"], (xc + 62, pp["dr"][1])], lab=None, arrow=False)
        C.opc(xc + 62, pp["dr"][1], "r", pto[0], dref(pto[1]))
        C.t(REG.no(f"{k}_pd"), xc + 37, pp["dr"][1] - 1.2, 2.0, "middle")
        # level
        lt_, lic = f"LT-{lp + 1}", f"LIC-{lp + 1}"
        C.tap([(xc - w / 2, 252), (xc - 30.4, 252)])
        ctrl(C, lic, xc - 35, 252, xc - 35, 232, line=f"{k}_ps")
        C.t(f"SP TO FIC-{lp + 2}", xc - 35, 224.5, 2.0, "middle")
        lg = free_tag(C, "LG")
        C.bub(xc - 35, 272, lg, "field", svc=f"{tag} level gauge", r=4.0)
        C.tap([(xc - w / 2, 258), (xc - 22, 258), (xc - 22, 272), (xc - 31, 272)])
        # return from exchanger -> air cooler -> FV -> rundown
        yr = 430.0
        C.opc(x0 + 36, yr, "l", rfrom[0], dref(rfrom[1]))
        a = C.aircooler(x0 + 60, yr - 4, 34, 8, 2)
        C.t(ac, x0 + 77, yr - 7, 2.6, "middle", bold=True)
        C.line({"kero": "kero_c1", "dsl": "dsl_c2", "ago": "ago_c1"}[k], [(x0 + 36, yr), a["i"]], lab=None)
        C.t(REG.no({"kero": "kero_c1", "dsl": "dsl_c2", "ago": "ago_c1"}[k]), x0 + 47, yr + 4.5, 2.0, "middle")
        rk = f"{k}_rd"
        C.line(rk, [a["o"], (x0 + 178, yr)], lab=0, at=0.15, side=1, arrow=False)
        C.opc(x0 + 178, yr, "r", rdtxt, "OSBL")
        C.station(x0 + 104, yr, x0 + 148, yr, f"FV-{lp + 2}", "FC", byp=1, tag_pos=(x0 + 130, yr - 6))
        C.orifice(x0 + 160, yr, "h")
        REG.inst(f"FE-{lp + 2}", C.sid, svc=f"{tag} product flow element", line=rk)
        ctrl(C, f"FIC-{lp + 2}", x0 + 160, yr - 16, x0 + 140, yr - 26, tap=[(x0 + 160, yr - 2.4), (x0 + 160, yr - 11.4)],
             sig=[(x0 + 155.4, yr - 16), (x0 + 150, yr - 16), (x0 + 150, yr - 26), (x0 + 144.6, yr - 26)],
             vsig=[(x0 + 135.4, yr - 26), (x0 + 126, yr - 26), (x0 + 126, yr - 10.4)], fail="FC", line=rk)
        C.t(f"SP FROM LIC-{lp + 1}", x0 + 140, yr - 33, 2.0, "middle")
        ti(C, x0 + 170, yr + 14, [(x0 + 170, yr), (x0 + 170, yr + 9.4)], svc=f"{tag} product rundown temperature",
           line=rk)
        C.t(f"STREAM {strm}", x0 + 194, yr + 22, 2.0, "middle")
        an = {"16": "AT-1055", "17": "AT-1065", "18": "AT-1075"}[strm]
        C.bub(x0 + 186, yr + 14, an, "field", svc=IC_AN[an], line=rk)
        C.tap([(x0 + 176, yr), (x0 + 176, yr + 14), (x0 + 181.4, yr + 14)])
    return save(C)


# ============================================================================= SHEET 009
def sheet_009():
    C = new_sheet(9, [
        "Neutraliser and filming amine injected upstream of A-101; pH control AIC-1037 trims FFIC-1036.",
        "PIC-1032 split range: 0-50 % PV-1032B (FG make-up) closing, 50-100 % PV-1032A (off-gas) opening.",
        "D-102 high-high level is a DCS alarm only (LAHH-1033); TSV on E-115 CW side, set per TSV-typ.",
    ])
    eq_boxes(C, ["A-101", "E-115", "D-102", "P-103A/B", "P-104A/B", "P-105A/B", "X-103"], w=72)
    # OH vapour -> A-101
    C.opc(50, 80, "l", "FROM C-101 TOP", dref(7))
    a = C.aircooler(180, 100, 80, 10, 4)
    C.t("A-101", 220, 97, 2.8, "middle", bold=True)
    C.line("oh_vap", [(50, 80), (170, 80), (170, a["i"][1]), a["i"]], lab=0, at=0.32)
    C.package(88, 125, 60, 22, "X-103", ["NEUTRALISER / FILMING", "AMINE PACKAGE"])
    for k, xx in (("ch_neut", 105), ("ch_film", 132)):
        C.line(k, [(xx, 125), (xx, 80)], lab=None)
        C.check(xx, 112, "u")
        C.gate(xx, 103, "v")
        C.t(REG.no(k), xx + (-2 if xx < 120 else 2), 92, 2.0, "end" if xx < 120 else "start", rot=None)
    C.bub(70, 160, "FFIC-1036", "dcs", svc=C_.LOOPS["FFIC-1036"]["service"], loop="FFIC-1036")
    C.sig([(74.6, 160), (88, 160), (88, 147)], "e")
    # A-101 -> E-115
    hx = C.hx(330, 150)
    C.t("E-115", 336, 167, 2.6, "middle", bold=True)
    C.line("a101_out", [a["o"], (hx["st_far"][0], a["o"][1]), hx["st_far"]], lab=0, at=0.5)
    ti(C, 285, 88, [(285, 105), (285, 92.6)], svc="A-101 outlet temperature", line="a101_out")
    C.opc(240, 182, "l", "CWS HEADER", dref(16))
    C.line("cws_e115", [(240, 182), (hx["cb"][0], 182), hx["cb"]], lab=0, at=0.55)
    C.line("cwr_e115", [hx["ct"], (hx["ct"][0], 125), (240, 125)], lab=1, at=0.5)
    tsv(C, 290, 125)
    C.opc(240, 125, "l", "CWR HEADER", dref(16), flow="out")
    # E-115 -> D-102
    dx0, dy0, L, D = 380.0, 195.0, 150.0, 30.0
    bx = 400.0
    C.hdrum(dx0, dy0, L, D, boot=(bx, 14, 20))
    C.t("D-102", dx0 + 75, dy0 + 17, 3.0, "middle", bold=True)
    C.line("e115_out", [hx["sb_near"], (hx["sb_near"][0], 180), (420, 180), (420, dy0)], lab=1, at=0.6)
    # off-gas / FG make-up
    C.line("d102_og", [(470, dy0), (470, 160), (790, 160)], lab=1, at=0.75)
    C.opc(790, 160, "r", "TO FG RECOVERY / FLARE", "OSBL")
    C.station(560, 160, 605, 160, "PV-1032A", "FC", byp=-1, side=1, tag_pos=(588, 172))
    C.opc(790, 138, "r", "FUEL GAS HEADER", dref(16), flow="in")
    C.line("fg_d102", [(790, 138), (455, 138), (455, dy0)], lab=0, at=0.15)
    C.station(625, 138, 670, 138, "PV-1032B", "FO", byp=-1, side=1, tag_pos=(651, 151))
    ctrl(C, "PIC-1032", 545, 185, 570, 185, tap=[(530, dy0), (530, 185), (540.4, 185)],
         vsig=[(570, 180.4), (570, 175), (582.5, 175), (582.5, 167)], line="d102_og")
    C.sig([(574.6, 185), (620, 185), (620, 150), (647.5, 150), (647.5, 145)], "e")
    C.t("SPLIT RANGE", 576, 192, 2.0)
    pv = C_.PSV["PSV-1004"]
    C.psv(500, dy0, "PSV-1004", pv["set_barg"], f"1{pv['orifice']}", up=16, out="l", outlen=14, dest="",
          text_side=1)
    REG.use_line("1004_out", C.sid)
    C.t("FLARE", 485, dy0 - 15, 2.0, "end")
    C.t(REG.no("1004_out"), 503, dy0 - 29, 2.0, "start")
    # level instruments
    xr = dx0 + L + 6
    C.tap([(xr - 3, dy0 + 10), (xr + 10.4, dy0 + 10)])
    ctrl(C, "LIC-1033", xr + 15, dy0 + 10, xr + 40, dy0 + 10, line="naph_s")
    C.t("SP TO FIC-1034 (AVERAGING)", xr + 46, dy0 + 11, 2.0)
    C.bub(560, 236, "AT-1038", "field", svc=IC_AN["AT-1038"], line="naph_s")
    C.tap([(560, 250), (560, 240.6)])
    C.bub(xr + 40, dy0 + 32, "LAHH-1033", "dcs", svc="D-102 hydrocarbon level high-high alarm (DCS only)",
          line="naph_s")
    C.sig([(xr + 40, dy0 + 14.6), (xr + 40, dy0 + 26.6)], "d")
    C.t("ALARM ONLY", xr + 47, dy0 + 33, 2.0)
    lg = free_tag(C, "LG")
    C.bub(dx0 - 12, dy0 + 15, lg, "field", svc="D-102 hydrocarbon level gauge", r=4.0)
    C.tap([(dx0 - 5, dy0 + 15), (dx0 - 8, dy0 + 15)])
    ptag = free_tag(C, "PI")
    C.bub(dx0 + 58, dy0 - 14, ptag, "field", svc="D-102 pressure", r=4.0)
    C.tap([(dx0 + 58, dy0), (dx0 + 58, dy0 - 10)])
    ti(C, dx0 + 100, dy0 + 45, [(dx0 + 100, dy0 + D), (dx0 + 100, dy0 + 40.4)], svc="D-102 temperature")
    # boot interface LIC-1035 + pH
    C.tap([(bx - 7, dy0 + D + 12), (bx - 20.4, dy0 + D + 12)])
    ctrl(C, "LIC-1035", bx - 25, dy0 + D + 12, bx - 50, dy0 + D + 12, line="sw_d",
         vsig=[(bx - 54.6, dy0 + D + 12), (272.5, dy0 + D + 12), (272.5, 383.2)], fail="FC")
    # pumps
    yp = 330.0
    p5 = pump_pair(C, 420, yp, "P-105", "sw_s", "sw_d")
    p3 = pump_pair(C, 540, yp, "P-103", "refl_s", "reflux")
    p4 = pump_pair(C, 660, yp, "P-104", "naph_s", "naph_d")
    C.line("sw_s", [(bx, dy0 + D + 22), (bx, p5["s"][1]), p5["s"]], lab=0, at=0.55, side=-1, arrow=False)
    C.line("refl_s", [(445, dy0 + D), (445, 262), (520, 262), (520, p3["s"][1]), p3["s"]], lab=1, at=0.5,
           arrow=False)
    C.line("naph_s", [(495, dy0 + D), (495, 250), (640, 250), (640, p4["s"][1]), p4["s"]], lab=1, at=0.55,
           arrow=False)
    # sour water -> LV-1035 -> SWS
    ysw = 390.0
    C.line("sw_d", [p5["dl"], (370, p5["dl"][1]), (370, ysw), (50, ysw)], lab=2, at=0.2)
    C.opc(50, ysw, "l", "SOUR WATER TO SWS", "OSBL", flow="out")
    C.station(250, ysw, 295, ysw, "LV-1035", "FC", byp=1, tag_pos=(276, ysw - 6))
    C.bub(330, ysw - 18, "AT-1037", "field", svc="OH sour water pH analyser")
    C.tap([(330, ysw), (330, ysw - 13.4)])
    C.bub(330, ysw - 40, "AIC-1037", "dcs", svc=C_.LOOPS["AIC-1037"]["service"], loop="AIC-1037")
    C.sig([(330, ysw - 22.6), (330, ysw - 35.4)], "e")
    C.t("TRIM SP FFIC-1036", 336, ysw - 44, 2.0)
    # reflux -> FV-1031 -> C-101
    yrf = 420.0
    C.line("reflux", [p3["dr"], (600, p3["dr"][1]), (600, yrf), (50, yrf)], lab=2, at=0.75)
    C.opc(50, yrf, "l", "TO C-101 TRAY 1", dref(7), flow="out")
    C.orifice(540, yrf, "h")
    REG.inst("FE-1031", C.sid, svc="Reflux flow element", line="reflux")
    C.station(470, yrf, 515, yrf, "FV-1031", "FC", byp=1, tag_pos=(496, yrf - 6))
    ctrl(C, "FIC-1031", 540, yrf - 16, 520, yrf - 28, tap=[(540, yrf - 2.4), (540, yrf - 11.4)],
         sig=[(535.4, yrf - 16), (530, yrf - 16), (530, yrf - 28), (524.6, yrf - 28)],
         vsig=[(515.4, yrf - 28), (492.5, yrf - 28), (492.5, yrf - 10.4)], fail="FC", line="reflux")
    C.t("SP FROM TIC-1030", 520, yrf - 36, 2.0, "middle")
    C.hop(520, yrf, "h") if False else None
    # naphtha -> FV-1034 -> E-114
    ynp = 270.0
    C.line("naph_d", [p4["dr"], (705, p4["dr"][1]), (705, ynp), (795, ynp)], lab=2, at=0.5)
    C.opc(795, ynp, "r", "TO E-114 / C-105", dref(10))
    C.orifice(705, 285, "v")
    REG.inst("FE-1034", C.sid, svc="Unstabilised naphtha flow element", line="naph_d")
    C.station(712, ynp, 756, ynp, "FV-1034", "FC", byp=-1, side=1, tag_pos=(738, ynp + 9))
    ctrl(C, "FIC-1034", 722, 292, 745, 292, tap=[(707, 285), (722, 285), (722, 287.4)], line="naph_d",
         vsig=[(745, 287.4), (745, 280), (734, 280), (734, 277)], fail="FC")
    C.bub(686, 395, "FIC-1090", "dcs", svc=C_.LOOPS["FIC-1090"]["service"] + " (shares FT/FV-1034)",
          loop="FIC-1090")
    C.t("= FIC-1034 (SHARED)", 692, 396, 2.0)
    return save(C)

# ============================================================================= SHEET 010
def sheet_010():
    C = new_sheet(10, [
        "Stabiliser C-105 is in LPG service: class C1 (600#), fire-safe valves, area gas detection (F&G).",
        "Column pressure by hot-vapour bypass PV-1091; reboiler HP steam cut by SIF-110 (XV-1096).",
        "E-116 kettle: stabilised naphtha overflows weir to E-114; HP condensate pot level LIC-1098.",
        "SIF-109: D-105 low-low level (LT-1092B) closes XV-1093 to prevent gas blow-by to LPG treating.",
    ])
    eq_boxes(C, ["C-105", "E-114", "E-116", "A-106", "D-105", "P-115A/B"], w=82)
    x, w = 300.0, 34.0
    y0, y1 = 100.0, 400.0
    ym = {n: 115 + 15 * (n - 1) for n in range(1, 20)}
    C.column(x, y0, y1, w)
    col_trays(C, x, w, ym)
    C.t("C-105", x + w / 2 + 4, 250, 3.2, "start", bold=True)
    xl, xr = x - w / 2, x + w / 2
    # feed: P-104 -> E-114 shell -> tray 13
    hx = C.hx(170, 300)
    C.t("E-114", 170, 317, 2.6, "middle", bold=True)
    C.opc(50, 320, "l", "FROM P-104A/B", dref(9))
    C.line("naph_d", [(50, 320), (hx["sb_far"][0], 320), hx["sb_far"]], lab=0, at=0.4)
    C.line("stab_feed", [hx["st_near"], (hx["st_near"][0], 270), (250, 270), (250, ym[13] - 4), (xl - 2.5, ym[13] - 4)],
           lab=1, at=0.45)
    C.noz(xl, ym[13] - 4, "l", "FEED")
    ti(C, 230, 255, [(230, 270), (230, 259.6)], svc="Stabiliser feed temperature", line="stab_feed")
    # overhead -> A-106 -> D-105
    C.noz(x, y0 - 8.5, "u")
    a = C.aircooler(400, 68, 34, 8, 2)
    C.t("A-106", 417, 65, 2.6, "middle", bold=True)
    C.line("c105_ov", [(x, y0 - 11), (x, 72), a["i"]], lab=1, at=0.5)
    dx0, dy0 = 480.0, 120.0
    C.hdrum(dx0, dy0, 80, 25, boot=(545, 10, 14))
    C.t("D-105", dx0 + 30, dy0 + 14, 2.8, "middle", bold=True)
    C.line("a106_out", [a["o"], (490, 72), (490, dy0)], lab=0, at=0.5)
    C.line("c105_hvb", [(360, 72), (360, 100), (505, 100), (505, dy0)], lab=1, at=0.75, side=1)
    C.dot(360, 72)
    C.station(380, 100, 425, 100, "PV-1091", "FO", byp=1, tag_pos=(406, 94))
    ctrl(C, "PIC-1091", 470, 160, 445, 160, tap=[(dx0, 135), (470, 135), (470, 155.4)] if False else
         [(dx0 + 2, dy0 + 20), (474.6, dy0 + 20), (474.6, 160)], sig=[(465.4, 160), (449.6, 160)],
         vsig=[(445, 155.4), (445, 85), (402.5, 85), (402.5, 93.2)], fail="FO", line="c105_ov")
    sis_initiator(C, ["PT-1091B"], 470, 185, "PZHH-1091", "SIF-110", 445, 185, 0, 0,
                  tap=[(dx0 + 4, dy0 + 23), (dx0 + 4, 185), (474.6, 185)])
    C.ilk(445, 205, "SIF-110", below=False)
    C.sig([(445, 190.4), (445, 201)], "e")
    C.t("TO XV-1096", 451, 210, 2.0)
    pv = C_.PSV["PSV-1006"]
    C.psv(530, dy0, "PSV-1006", pv["set_barg"], f"1{pv['orifice']}", up=14, out="r", outlen=14, dest="FLARE",
          text_side=1)
    REG.use_line("1006_out", C.sid)
    C.t(REG.no("1006_out"), 558, dy0 - 10, 2.0)
    C.line("d105_og", [(555, dy0), (555, 84), (790, 84)], lab=1, at=0.6)
    C.opc(790, 84, "r", "OFF-GAS TO FG (NNF)", "OSBL")
    C.gate(555, 95, "v")
    C.line("d105_sw", [(545, dy0 + 39), (545, 168), (790, 168)], lab=1, at=0.6)
    C.opc(790, 168, "r", "BOOT WATER TO SWS", "OSBL")
    C.gate(600, 168, "h", note="NC")
    lg = free_tag(C, "LG")
    C.bub(575, 152, lg, "field", svc="D-105 level gauge", r=4.0)
    C.tap([(559, 140), (566, 140), (566, 152), (571, 152)])
    # pumps P-115 -> reflux / LPG
    pp = pump_pair(C, 530, 240, "P-115", "lpg_s", "stab_refl")
    REG.use_line("lpg_prod", C.sid)
    C.line("lpg_s", [(497, dy0 + 25), (497, pp["s"][1]), pp["s"]], lab=0, at=0.55, side=-1, arrow=False)
    yr = 178.0
    C.pipe([pp["dr"], (590, pp["dr"][1])], arrow=False)
    C.line("stab_refl", [(590, pp["dr"][1]), (590, yr), (335, yr), (335, ym[1] - 4), (xr + 2.5, ym[1] - 4)],
           lab=2, at=0.75)
    C.hop(497, yr, "h")
    C.noz(xr, ym[1] - 4, "r", "REFLUX")
    C.orifice(420, yr, "h")
    REG.inst("FE-1094", C.sid, svc="Stabiliser reflux flow element", line="stab_refl")
    C.station(355, yr, 400, yr, "FV-1094", "FC", byp=1, tag_pos=(381, yr - 6))
    ctrl(C, "FIC-1094", 420, yr - 16, 400, yr - 28, tap=[(420, yr - 2.4), (420, yr - 11.4)],
         sig=[(415.4, yr - 16), (410, yr - 16), (410, yr - 28), (404.6, yr - 28)],
         vsig=[(395.4, yr - 28), (377.5, yr - 28), (377.5, yr - 10.4)], fail="FC", line="stab_refl")
    C.t("RATIO TO FEED", 400, yr - 36, 2.0, "middle")
    C.dot(590, pp["dr"][1])
    C.line("lpg_prod", [(590, pp["dr"][1]), (790, pp["dr"][1])], lab=0, at=0.85)
    C.opc(790, pp["dr"][1], "r", "LPG TO TREATING", "OSBL")
    yl = pp["dr"][1]
    C.bub(755, yl + 16, "AT-1099", "field", svc=IC_AN["AT-1099"], line='lpg_prod')
    C.tap([(755, yl), (755, yl + 11.4)])
    C.orifice(620, yl, "h")
    REG.inst("FE-1093", C.sid, svc="LPG product flow element", line="lpg_prod")
    C.station(640, yl, 685, yl, "FV-1093", "FC", byp=1, tag_pos=(666, yl - 6))
    ctrl(C, "FIC-1093", 620, yl - 16, 640, yl - 28, tap=[(620, yl - 2.4), (620, yl - 11.4)],
         sig=[(624.6, yl - 16), (630, yl - 16), (630, yl - 28), (635.4, yl - 28)],
         vsig=[(644.6, yl - 28), (662.5, yl - 28), (662.5, yl - 10.4)], fail="FC", line="lpg_prod")
    C.tap([(dx0 + 80, dy0 + 12), (dx0 + 100, dy0 + 12), (dx0 + 100, 145.4)] if False else [(dx0 + 82, dy0 + 15), (612, dy0 + 15)])
    ctrl(C, "LIC-1092", 617, dy0 + 15, 640, dy0 + 15, line="lpg_s")
    C.t("SP TO FIC-1093", 646, dy0 + 16, 2.0)
    # SIF-109: D-105 low-low level -> XV-1093 (gas blow-by to LPG treating)
    sis_initiator(C, ["LT-1092B"], 617, 112, "LZLL-1092", "SIF-109", 640, 112, 0, 0,
                  tap=[(561, dy0 + 8), (600, dy0 + 8), (600, 112), (611.6, 112)])
    C.ilk(663, 112, "SIF-109", below=True)
    C.sig([(645.4, 112), (659, 112)], "e")
    C.xv(712, yl, "h", "XV-1093", "FC", tag_pos=(715, yl - 6))
    REG.inst("XV-1093", C.sid, sys="SIS", sif="SIF-109", fail="FC", svc=C_.SIFS["SIF-109"]["function"])
    C.sig([(667, 112), (712, 112), (712, yl - 9.8)], "e")
    for i, xg in enumerate((700, 730)):
        gd = free_tag(C, "GD")
        C.bub(xg, 300, gd, "field", sys="F&G", svc=f"Flammable gas detector, LPG pump area P-115 ({i + 1})")
    C.t("F&G (LPG AREA)", 715, 312, 2.0, "middle")
    pv = C_.PSV["PSV-1005"]
    C.psv(x + 10, y0 - 6, "PSV-1005", pv["set_barg"], f"1{pv['orifice']}", up=14, out="r", outlen=14,
          dest="FLARE", text_side=1)
    REG.use_line("1005_out", C.sid)
    C.t(REG.no("1005_out"), x + 14, y0 - 32, 2.0)
    # TIC-1095 tray 15
    ctrl(C, "TIC-1095", 350, ym[15], 375, ym[15], tap=[(xr, ym[15]), (345.4, ym[15])], line="stab_btm")
    C.t("SP CASCADE TO FIC-1096 (RVP)", 381, ym[15] + 1, 2.0)
    ptag = free_tag(C, "PDI")
    C.bub(350, ym[8], ptag, "dcs", svc="C-105 column dP")
    C.tap([(xr, ym[8]), (345.4, ym[8])])
    # bottoms -> E-116 kettle (left of column)
    k = C.kettle(220, 455)
    C.t("E-116", 205, 475, 2.6, "middle", bold=True)
    C.line("c105_reb_l", [(x, y1 + 8.5), (x, 478), (k["sb"][0], 478), k["sb"]], lab=1, at=0.5, side=1)
    C.line("c105_reb_v", [k["sv"], (k["sv"][0], ym[19] + 8), (xl - 2.5, ym[19] + 8)], lab=0, at=0.5)
    C.noz(xl, ym[19] + 8, "l")
    C.line("stab_btm", [(225, k["sb"][1]), (225, 495), (hx["cb"][0], 495), hx["cb"]], lab=1, at=0.5)
    C.line("stab_btm2", [hx["ct"], (hx["ct"][0], 245), (50, 245)], lab=0, at=0.5, side=1)
    C.opc(50, 245, "l", "TO C-106 FEED", dref(11), flow="out")
    C.station(70, 245, 115, 245, "LV-1097", "FC", byp=-1, tag_pos=(96, 239))
    lt_y = 372.0
    C.tap([(xl, lt_y), (264.6, lt_y)])
    ctrl(C, "LIC-1097", 260, lt_y, 235, lt_y, line="stab_btm2", sig=[(255.4, lt_y), (239.6, lt_y)],
         vsig=[(230.4, lt_y), (130, lt_y), (130, 232), (92.5, 232), (92.5, 238.2)], fail="FC")
    # HP steam -> FV-1096 -> XV-1096 -> E-116 channel; condensate pot -> LV-1098
    ys_ = 432.0
    C.opc(50, ys_, "l", "HP STEAM HEADER", dref(16))
    C.line("hs_e116", [(50, ys_), (k["ct"][0], ys_), k["ct"]], lab=0, at=0.13)
    C.hop(hx["cb"][0], ys_, "h")
    C.orifice(68, ys_, "h")
    REG.inst("FE-1096", C.sid, svc="HP steam to E-116 flow element", line="hs_e116")
    C.xv(80, ys_, "h", "XV-1096", "FC", tag_pos=(74, ys_ - 9))
    REG.inst("XV-1096", C.sid, sys="SIS", sif="SIF-110", fail="FC", svc=C_.SIFS["SIF-110"]["function"])
    C.station(165, ys_, 200, ys_, "FV-1096", "FC", bypass=False, tag_pos=(186, ys_ - 6))
    ctrl(C, "FIC-1096", 68, ys_ - 22, 100, ys_ - 22, tap=[(68, ys_ - 2.4), (68, ys_ - 17.4)],
         vsig=[(104.6, ys_ - 22), (182.5, ys_ - 22), (182.5, ys_ - 10.4)], fail="FC", line="hs_e116")
    C.t("SP FROM TIC-1095", 100, ys_ - 30, 2.0, "middle")
    C.line("hc_e116", [k["cb"], (k["cb"][0], 520)], lab=None, arrow=False)
    C.vdrum(k["cb"][0], 520, 10, 16)
    C.t("COND. POT", k["cb"][0] + 7, 528, 2.0)
    C.line("cd_e116", [(k["cb"][0], 545), (k["cb"][0], 552), (50, 552)], lab=1, at=0.35)
    C.hop(hx["cb"][0], 552, "h") if False else None
    C.opc(50, 552, "l", "TO CONDENSATE HDR", dref(16), flow="out")
    C.station(95, 552, 140, 552, "LV-1098", "FC", byp=-1, tag_pos=(121, 546))
    C.t(REG.no("hc_e116"), k["cb"][0] - 3, 505, 2.0, "end")
    C.tap([(k["cb"][0] + 5, 528), (k["cb"][0] + 18, 528), (k["cb"][0] + 18, 538)])
    ctrl(C, "LIC-1098", k["cb"][0] + 18, 538 + 4.6 if False else 542.6, k["cb"][0] + 40, 542.6, line="cd_e116",
         vsig=[(k["cb"][0] + 40, 547.2), (k["cb"][0] + 40, 541), (117.5, 541), (117.5, 545)], fail="FC")
    pv = C_.PSV["PSV-1008"]
    C.psv(239, k["sv"][1], "PSV-1008", pv["set_barg"], f"1{pv['orifice']}", up=30, out="r", outlen=16,
          dest="FLARE", text_side=1)
    REG.use_line("1008_out", C.sid)
    C.t(REG.no("1008_out"), 243, k["sv"][1] - 41, 2.0)
    return save(C)


# ============================================================================= SHEET 011
def sheet_011():
    C = new_sheet(11, [
        "C-106 pressure controlled by flooded condenser (PV-1100 on A-107 outlet) with D-106 balance line.",
        "E-117 vertical thermosyphon reboiler, MP steam; condensate via steam trap set to condensate header.",
        "Light naphtha to isomerisation, heavy naphtha to NHT/reformer (A-108 product cooler).",
    ])
    eq_boxes(C, ["C-106", "E-117", "A-107", "D-106", "P-116A/B", "P-117A/B", "A-108"], w=72)
    x, w = 260.0, 46.0
    y0, y1 = 95.0, 445.0
    ym = {n: 105 + (n - 1) * 8.9 for n in range(1, 39)}
    C.column(x, y0, y1, w)
    col_trays(C, x, w, ym)
    C.t("C-106", x - w / 2 - 4, 200, 3.2, "end", bold=True)
    xl, xr = x - w / 2, x + w / 2
    C.opc(50, ym[21] - 3, "l", "FROM C-105 (LV-1097)", dref(10))
    C.line("stab_btm2", [(50, ym[21] - 3), (xl - 2.5, ym[21] - 3)], lab=0, at=0.5)
    C.noz(xl, ym[21] - 3, "l", "FEED")
    # overhead -> A-107 -> PV-1100 -> D-106
    C.noz(x, y0 - 11.5, "u")
    a = C.aircooler(380, 68, 34, 8, 2)
    C.t("A-107", 397, 65, 2.6, "middle", bold=True)
    C.line("c106_ov", [(x, y0 - 14), (x, 72), a["i"]], lab=1, at=0.5)
    dx0, dy0 = 490.0, 125.0
    C.hdrum(dx0, dy0, 90, 28)
    C.t("D-106", dx0 + 45, dy0 + 16, 2.8, "middle", bold=True)
    C.line("a107_out", [a["o"], (505, 72), (505, dy0)], lab=0, at=0.8)
    C.station(430, 72, 475, 72, "PV-1100", "FO", byp=-1, side=1, tag_pos=(456, 85))
    C.line("c106_eq", [(330, 72), (330, 105), (560, 105), (560, dy0)], lab=1, at=0.82)
    C.dot(330, 72)
    C.gate(540, 105, "h")
    ctrl(C, "PIC-1100", 610, 112, 610, 92, tap=[(575, dy0), (575, 112), (605.4, 112)], line="c106_ov",
         vsig=[(605.4, 92), (452.5, 92), (452.5, 78.8)], fail="FO")
    pv = C_.PSV["PSV-1007"]
    C.psv(x + 12, y0 - 7, "PSV-1007", pv["set_barg"], f"1{pv['orifice']}", up=14, out="r", outlen=14,
          dest="FLARE", text_side=1)
    REG.use_line("1007_out", C.sid)
    C.t(REG.no("1007_out"), x + 16, y0 - 34, 2.0)
    # D-106 -> P-116 -> reflux / LN
    pp = pump_pair(C, 530, 245, "P-116", "ln_s", "split_refl")
    REG.use_line("ln_prod", C.sid)
    C.line("ln_s", [(500, dy0 + 28), (500, pp["s"][1]), pp["s"]], lab=0, at=0.55, side=-1, arrow=False)
    yr = 185.0
    C.pipe([pp["dr"], (590, pp["dr"][1])], arrow=False)
    C.line("split_refl", [(590, pp["dr"][1]), (590, yr), (300, yr), (300, ym[1] - 4), (xr + 2.5, ym[1] - 4)],
           lab=2, at=0.8)
    C.hop(500, yr, "h")
    C.noz(xr, ym[1] - 4, "r", "REFLUX")
    C.orifice(440, yr, "h")
    REG.inst("FE-1103", C.sid, svc="Splitter reflux flow element", line="split_refl")
    C.station(370, yr, 415, yr, "FV-1103", "FC", byp=1, tag_pos=(396, yr - 6))
    ctrl(C, "FIC-1103", 440, yr - 16, 420, yr - 28, tap=[(440, yr - 2.4), (440, yr - 11.4)],
         sig=[(435.4, yr - 16), (430, yr - 16), (430, yr - 28), (424.6, yr - 28)],
         vsig=[(415.4, yr - 28), (392.5, yr - 28), (392.5, yr - 10.4)], fail="FC", line="split_refl")
    C.dot(590, pp["dr"][1])
    yl = pp["dr"][1]
    C.line("ln_prod", [(590, yl), (790, yl)], lab=0, at=0.85)
    C.opc(790, yl, "r", "LT. NAPHTHA TO ISOM", "OSBL")
    C.bub(720, yl + 16, "AT-1108", "field", svc=IC_AN["AT-1108"], line='ln_prod')
    C.tap([(720, yl), (720, yl + 11.4)])
    C.orifice(620, yl, "h")
    REG.inst("FE-1102", C.sid, svc="Light naphtha flow element", line="ln_prod")
    C.station(640, yl, 685, yl, "FV-1102", "FC", byp=1, tag_pos=(666, yl - 6))
    ctrl(C, "FIC-1102", 620, yl - 16, 640, yl - 28, tap=[(620, yl - 2.4), (620, yl - 11.4)],
         sig=[(624.6, yl - 16), (630, yl - 16), (630, yl - 28), (635.4, yl - 28)],
         vsig=[(644.6, yl - 28), (662.5, yl - 28), (662.5, yl - 10.4)], fail="FC", line="ln_prod")
    C.tap([(dx0 + 96, dy0 + 14), (615.4, dy0 + 14)])
    ctrl(C, "LIC-1101", 620, dy0 + 14, 645, dy0 + 14, line="ln_s")
    C.t("SP TO FIC-1102", 651, dy0 + 15, 2.0)
    # TIC-1104 tray 30
    ctrl(C, "TIC-1104", 320, ym[30], 345, ym[30], tap=[(xr, ym[30]), (315.4, ym[30])], line="c106_reb_r")
    C.t("SP CASCADE TO FIC-1105", 351, ym[30] + 1, 2.0)
    # thermosyphon E-117 (vertical) left of column
    ex, ey0, ey1 = 170.0, 330.0, 400.0
    C.g_eq.add(C.d.rect((ex - 8, ey0), (16, ey1 - ey0)))
    C.g_eq.add(C.d.rect((ex - 8, ey0 - 7), (16, 7)))
    C.g_eq.add(C.d.rect((ex - 8, ey1), (16, 7)))
    C.t("E-117", ex - 11, 365, 2.6, "end", bold=True)
    C.line("c106_reb_l", [(x, y1 + 11.5), (x, 470), (ex, 470), (ex, ey1 + 7)], lab=1, at=0.5)
    C.line("c106_reb_r", [(ex, ey0 - 7), (ex, 318), (205, 318), (205, ym[38] + 4), (xl - 2.5, ym[38] + 4)],
           lab=2, at=0.5, side=1)
    C.noz(xl, ym[38] + 4, "l")
    C.opc(50, 340, "l", "MP STEAM HEADER", dref(16))
    C.line("ms_e117", [(50, 340), (ex - 8, 340)], lab=0, at=0.2)
    C.orifice(126, 340, "h")
    REG.inst("FE-1105", C.sid, svc="MP steam to E-117 flow element", line="ms_e117")
    C.station(80, 340, 118, 340, "FV-1105", "FC", bypass=False, tag_pos=(102, 334))
    ctrl(C, "FIC-1105", 126, 322, 100, 310, tap=[(126, 337.6), (126, 326.6)],
         sig=[(121.4, 322), (110, 322), (110, 310), (104.6, 310)],
         vsig=[(95.4, 310), (99, 310), (99, 330)] if False else [(95.4, 310), (99, 310), (99, 333.2)], fail="FC",
         line="ms_e117")
    C.t("SP FROM TIC-1104", 100, 302, 2.0, "middle")
    C.line("cd_e117", [(ex - 8, 392), (50, 392)], lab=0, at=0.3)
    C.opc(50, 392, "l", "TO CONDENSATE HDR", dref(16), flow="out")
    stt = free_tag(C, "ST")
    C.g_sy.add(C.d.rect((112, 388), (8, 8), fill="white"))
    C.t("T", 116, 394, 2.2, "middle", bold=True)
    C.t("STEAM TRAP", 116, 401, 2.0, "middle")
    # bottoms -> P-117 -> A-108 -> FV-1107
    pp2 = pump_pair(C, 340, 520, "P-117", "hn_s", "hn_d")
    C.line("hn_s", [(x + 12, y1 + 8), (x + 12, pp2["s"][1]), pp2["s"]], lab=0, at=0.4, side=1, arrow=False)
    C.noz(x + 12, y1 + 6, "d")
    a2 = C.aircooler(420, 486, 34, 8, 2)
    C.t("A-108", 437, 483, 2.6, "middle", bold=True)
    C.line("hn_d", [pp2["dr"], (400, pp2["dr"][1]), (400, 490), a2["i"]], lab=None)
    C.t(REG.no("hn_d"), 397, 500, 2.0, "end")
    C.line("hn_prod", [a2["o"], (600, 490)], lab=0, at=0.85)
    C.opc(600, 490, "r", "HVY NAPHTHA TO NHT", "OSBL")
    C.bub(588, 506, "AT-1109", "field", svc=IC_AN["AT-1109"], line='hn_prod')
    C.tap([(588, 490), (588, 501.4)])
    C.orifice(565, 490, "h")
    REG.inst("FE-1107", C.sid, svc="Heavy naphtha flow element", line="hn_prod")
    C.station(470, 490, 515, 490, "FV-1107", "FC", byp=1, tag_pos=(496, 484))
    ctrl(C, "FIC-1107", 565, 474, 545, 462, tap=[(565, 487.6), (565, 478.6)],
         sig=[(560.4, 474), (555, 474), (555, 462), (549.6, 462)],
         vsig=[(540.4, 462), (492.5, 462), (492.5, 479.6)], fail="FC", line="hn_prod")
    lt_y = y1 - 8
    C.tap([(xr, lt_y), (315.4, lt_y)])
    ctrl(C, "LIC-1106", 320, lt_y, 345, lt_y, line="hn_s")
    C.t("SP TO FIC-1107", 351, lt_y + 1, 2.0)
    ti(C, 300, 474, [(x + 12, 474), (295.4, 474)], svc="C-106 bottoms temperature", line="hn_s")
    return save(C)

# ============================================================================= SHEET 012
def fg_train(C, y, x0, opc_txt, xvs, vent_key, pv, pic, pic_line, main_key, pilot_key, yp, pil_xv=None):
    """Fuel gas train: strainer, PI, SSOVs with DBB vent, PV station.  Returns x at end of PV station."""
    C.opc(50, y, "l", opc_txt, dref(16))
    C.strainer(x0, y)
    pt = free_tag(C, "PI")
    C.bub(x0 + 14, y - 14, pt, "field", svc="Fuel gas supply pressure", line=main_key, r=4.0)
    C.tap([(x0 + 14, y), (x0 + 14, y - 10)])
    C.gate(x0 + 26, y, "h")
    xa, xb = x0 + 42, x0 + 82
    C.xv(xa, y, "h", xvs[0], "FC", tag_pos=(xa + 3, y - 6))
    C.xv(xb, y, "h", xvs[1], "FC", tag_pos=(xb + 3, y - 6))
    vt = free_tag(C, "XV")
    xm = (xa + xb) / 2
    C.line(vent_key, [(xm, y), (xm, y + 24), (xm - 30, y + 24)], lab=1, at=0.5, side=1)
    C.dot(xm, y)
    C.xv(xm, y + 12, "v", vt, "FO", side=1, tag_pos=(xm + 6, y + 12))
    C.t("TO FLARE", xm - 32, y + 25, 2.0, "end")
    C.station(x0 + 105, y, x0 + 150, y, pv, "FC", byp=1, tag_pos=(x0 + 131, y - 6))
    return vt, xm


def sheet_012():
    C = new_sheet(12, [
        "Passes shown schematically (convection + radiant in series); 4 identical passes, coil steam per pass.",
        "Pass flow SIS transmitters FT-200xA/B/C (2oo3) independent of BPCS FT-200x (SIF-201).",
        "Vacuum off-gas burned in dedicated H-201 burners via flame arrestor (from D-202 / PV-2031).",
        "Natural draft heater: O2 trim AIC-2008 on stack damper.",
    ])
    eq_boxes(C, ["H-201"], w=95)
    H2 = C_.R["heaters"]["H-201"]
    n = H2["passes"]
    X0, X1, Y0, Y1 = 380.0, 580.0, 130.0, 300.0
    heater_box(C, X0, Y0, X1, Y1, "H-201", cells=1, stack=(530, 70, 550, Y0), burners=H2["burners"])
    C.g_eq.add(C.d.line((440, Y0), (440, Y1 - 10), stroke_width=0.3, stroke_dasharray="3,1.5"))
    C.t("CONV.", 410, Y0 + 6, 2.2, "middle")
    C.t("RADIANT", 510, Y0 + 6, 2.2, "middle")
    damper(C, 540, 85, "h")
    C.t("STACK DAMPER", 555, 86, 2.0)
    ys = [165 + 32 * i for i in range(n)]
    xm, xo = 82.0, 630.0
    C.opc(50, 120, "l", "FROM P-112A/B (FV-1083)", dref(6))
    C.line("ar_d", [(50, 120), (xm, 120), (xm, ys[-1])], lab=0, at=0.5, arrow=False)
    C.pipe([(xo, ys[-1]), (xo, ys[0])], arrow=False)
    C.line("vac_transfer", [(xo, ys[0]), (xo, 110), (790, 110)], lab=1, at=0.6)
    C.reducer(xo, 135, "v", True, note="EXPANDING", note_side=1)
    C.opc(790, 110, "r", "TO C-201 FLASH ZONE", dref(13))
    yc = 145.0
    C.opc(50, yc - 50, "l", "MP STEAM HEADER", dref(16))
    C.line("ms_coil", [(50, yc - 50), (330, yc - 50), (330, ys[-1] - 6)], lab=0, at=0.15, arrow=False)
    C.orifice(200, yc - 50, "h")
    REG.inst("FE-2007", C.sid, svc="H-201 coil steam flow element", line="ms_coil")
    C.station(220, yc - 50, 265, yc - 50, "FV-2007", "FC", byp=1, tag_pos=(246, yc - 56))
    ctrl(C, "FIC-2007", 200, yc - 66, 220, yc - 76, tap=[(200, yc - 52.4), (200, yc - 61.4)],
         sig=[(204.6, yc - 66), (210, yc - 66), (210, yc - 76), (215.4, yc - 76)],
         vsig=[(224.6, yc - 76), (242.5, yc - 76), (242.5, yc - 60.4)], fail="FC", line="ms_coil")
    for i, y in enumerate(ys):
        k = i + 1
        lp = f"FIC-{2000 + k}"
        C.dot(xm, y)
        C.line(f"h201_in{k}", [(xm, y), (X0, y)], lab=0, at=0.84, arrow=False)
        coil(C, X0 + 6, X1 - 6, y, n=18)
        C.pipe([(X0, y), (X0 + 6, y)], arrow=False)
        C.pipe([(X1 - 6, y), (X1, y)], arrow=False)
        C.line(f"h201_out{k}", [(X1, y), (xo, y)], lab=0, at=0.45, arrow=False)
        C.dot(xo, y)
        C.t(f"PASS {k}", X0 + 30, y - 4.2, 2.1, "middle", bold=True)
        C.orifice(100, y, "h")
        REG.inst(f"FE-{2000 + k}", C.sid, svc=f"H-201 pass {k} flow element", line=f"h201_in{k}")
        ctrl(C, lp, 100, y - 13, 122, y - 13, tap=[(100, y - 2.4), (100, y - 8.4)], line=f"h201_in{k}",
             vsig=[(126.6, y - 13), (153, y - 13), (153, y - 7)], fail="FO")
        C.station(137, y, 169, y, f"FV-{2000 + k}", "FO", bypass=False, red=False, drain=False,
                  tag_pos=(157, y - 5.5))
        tags = [f"FT-{2000 + k}{c}" for c in "ABC"]
        sis_initiator(C, tags, 192, y - 13, f"FZLL-{2000 + k}", "SIF-201", 216, y - 13, 0, 0,
                      tap=[(186, y), (186, y - 13), (186.6, y - 13)])
        C.orifice(186, y, "h")
        C.sig([(221.4, y - 13), (250, y - 13)], "e")
        # coil steam injection
        C.dot(330, y - 6) if k < n else None
        C.pipe([(330, y - 6), (345, y - 6), (345, y)], util=True)
        C.check(338, y - 6, "r")
        C.dot(345, y)
        ti(C, 600, y - 14, [(600, y), (600, y - 8.6)], svc=f"H-201 pass {k} outlet temperature", line=f"h201_out{k}")
    C.t("COIL STEAM (EACH PASS, RO + CHECK)", 335, ys[0] - 22, 2.0, "middle")
    C.sig([(250, ys[0] - 13), (250, ys[-1] + 10)], "e")
    ctrl(C, "TIC-2005", 670, 130, 695, 130, tap=[(670, 110), (670, 124.6)], line="vac_transfer")
    C.t("SP CASCADE TO PIC-2006", 701, 131, 2.0)
    # stack O2
    C.bub(600, 70, "AT-2008", "field", svc="H-201 flue gas O2 analyser")
    C.tap([(550, 75), (594.6, 75), (594.6, 70)] if False else [(550, 70), (594.6, 70)])
    C.bub(625, 70, "AIC-2008", "dcs", svc=C_.LOOPS["AIC-2008"]["service"], loop="AIC-2008")
    C.sig([(605.4, 70), (619.6, 70)], "e")
    C.sig([(625, 75.4), (625, 92), (560, 92), (560, 85), (541.8, 85)], "e")
    REG.inst("AV-2008", C.sid, svc="H-201 stack damper actuator (AIC-2008)", fail="FO")
    # fuel gas train + pilot + off-gas
    yf = 400.0
    vt, xmv = fg_train(C, yf, 80, "FUEL GAS FROM D-103", ("XV-2006A", "XV-2006B"), "fl_h201_vent", "PV-2006",
                       "PIC-2006", "fg_h201", "fg_h201", None, 0)
    for t in ("XV-2006A", "XV-2006B"):
        REG.inst(t, C.sid, sys="SIS", sif="SIF-201", fail="FC", svc="H-201 fuel gas SSOV")
    REG.inst(vt, C.sid, sys="SIS", sif="SIF-201", fail="FO", svc="H-201 FG double block & bleed vent")
    C.line("fg_h201", [(50, yf), (420, yf), (420, 335), (X1 - 4, 335)], lab=0, at=0.55, arrow=False)
    C.orifice(345, yf, "h")
    REG.inst("FE-2006", C.sid, svc="H-201 fuel gas flow element", line="fg_h201")
    C.bub(345, yf - 16, "FT-2006", "field", svc=IC_AN["FT-2006"], line='fg_h201')
    C.tap([(345, yf - 2.4), (345, yf - 11.4)])
    ctrl(C, "PIC-2006", 260, yf - 18, 235, yf - 30, tap=[(260, yf), (260, yf - 13.4)], line="fg_h201",
         sig=[(255.4, yf - 18), (245, yf - 18), (245, yf - 30), (239.6, yf - 30)],
         vsig=[(230.4, yf - 30), (207.5, yf - 30), (207.5, yf - 10.8)], fail="FC")
    C.t("SP FROM TIC-2005", 230, yf - 40, 2.0, "end")
    sis_initiator(C, ["PT-2009A", "PT-2009B", "PT-2009C"], 300, yf + 18, "PZLL-2009", "SIF-202", 325, yf + 18,
                  0, 0, tap=[(300, yf), (300, yf + 12.6)], vote="2oo3")
    C.t("TO SIF-202", 331, yf + 29, 2.0)
    for i in range(H2["burners"]):
        bx = X0 + (X1 - X0) * (i + 0.5) / H2["burners"]
        C.pipe([(bx, 335), (bx, Y1)], arrow=False)
        C.pipe([(bx + 3, 327), (bx + 3, Y1)], arrow=False, util=True)
    ypl = 450.0
    C.opc(50, ypl, "l", "PILOT GAS FROM D-103", dref(16))
    C.line("fg_h201_pil", [(50, ypl), (405, ypl), (405, 327), (X1 - 1, 327)], lab=0, at=0.5, arrow=False)
    C.gate(80, ypl, "h")
    pcv = free_tag(C, "PCV")
    C.cv(100, ypl, "h", pcv, "", tag_pos=(103, ypl - 6))
    REG.inst(pcv, C.sid, svc="H-201 pilot gas self-acting regulator")
    C.t("MAIN GAS", X1 + 2, 336, 2.0)
    C.t("PILOT GAS", X1 + 2, 328, 2.0)
    C.bub(500, 355, "BS-2008", "field", sys="BMS", svc="H-201 flame scanners (1 per burner)")
    C.tap([(500, Y1), (500, 350.4)])
    C.bub(525, 355, "BZLL-2008", "sis", sys="SIS", sif="SIF-202", svc="H-201 flame failure")
    C.sig([(504.6, 355), (519.6, 355)], "e")
    C.t("TO SIF-202", 531, 356, 2.0)
    # off-gas burners
    C.opc(790, 280, "r", "VAC. OFF-GAS FROM D-202", dref(15), flow="in")
    C.line("vog", [(790, 280), (X1, 280)], lab=0, at=0.4)
    C.g_sy.add(C.d.rect((640, 276), (8, 8), fill="white"))
    C.t("FA", 644, 281.5, 2.0, "middle", bold=True)
    C.t("FLAME ARRESTOR", 644, 290, 2.0, "middle")
    C.gate(620, 280, "h")
    # snuffing
    C.opc(790, 220, "r", "LP STEAM HEADER", dref(16), flow="in")
    C.line("ls_snuff_h201", [(790, 220), (X1, 220)], lab=0, at=0.35)
    C.xv(700, 220, "h", "HV-2190", "FC", tag_pos=(703, 214))
    REG.inst("HV-2190", C.sid, sys="F&G", fail="FC", svc="H-201 snuffing steam valve (remote open from CCR / F&G)")
    # SIS block
    pos, h = sif_block(C, 40, 300, 150, ["SIF-201", "SIF-202"], title="H-201 BMS / SIS (SIL-RATED PLC)")
    yb = 300 + h
    C.sig([(250, ys[-1] + 10), (250, 290), (115, 290), (115, 300)], "e")
    C.sig([(80 + 42, yb), (80 + 42, yf - 9.8)], "e")
    C.sig([(80 + 82, yb), (80 + 82, yf - 9.8)], "e")
    C.sig([(140, yb), (140, yb + 8), (xmv + 6, yb + 8), (xmv + 6, yf + 4)], "e")
    return save(C)


# ============================================================================= SHEET 013
def sheet_013():
    C = new_sheet(13, [
        "C-201 wet vacuum column: 4 packed beds + 4 stripping trays; flash zone 60 mbar(a), top 20 mbar(a).",
        "Wash-bed wetting is critical: FIC-2020 minimum-flow alarm and APC constraint (coke prevention).",
        "Boot temperature limited to 365 C by cooled VR quench (TIC-2026 cascade to FIC-2027).",
        "Draw-off pumps P-201/202/203 and product routing on " + dref(14) + ".",
    ])
    eq_boxes(C, ["C-201", "P-204A/B", "X-104"], w=110)
    x = 330.0
    wt, wm, wb = 44.0, 84.0, 48.0
    C.column(x, 95, 175, wt, top=True, bot=False)
    swage(C, x, wt, wm, 175, 190)
    C.column(x, 190, 380, wm, top=False, bot=False)
    swage(C, x, wm, wb, 380, 395)
    C.column(x, 395, 470, wb, top=False, bot=True)
    C.t("C-201", x - wm / 2 - 4, 250, 3.4, "end", bold=True)
    C.distributor(x, wt, 112)
    C.bed(x, wt, 117, 160, "BED 1 (LVGO PA)")
    C.pan(x, wt, 170, None)
    C.t("LVGO PAN", x + wt / 2 + 3, 167, 2.0)
    C.distributor(x, wm, 198)
    C.bed(x, wm, 203, 235, "BED 2 (FRACT.)")
    C.pan(x, wm, 247, None)
    C.t("HVGO PAN", x - wm / 2 + 2, 243, 2.0)
    C.distributor(x, wm, 256)
    C.bed(x, wm, 261, 295, "BED 3 (HVGO PA)")
    C.distributor(x, wm, 305)
    C.bed(x, wm, 310, 330, "BED 4 (WASH)")
    C.pan(x, wm, 340, None)
    C.t("SLOP WAX PAN", x - wm / 2 + 2, 336, 2.0)
    C.t("FLASH ZONE", x, 370, 2.2, "middle", bold=True)
    col_trays(C, x, wb, {1: 405, 2: 420, 3: 435, 4: 450})
    xl, xr = x - wm / 2, x + wm / 2
    xtl, xtr = x - wt / 2, x + wt / 2
    # transfer line / vapour horn
    C.opc(50, 360, "l", "FROM H-201", dref(12))
    C.line("vac_transfer", [(50, 360), (xl - 2.5, 360)], lab=0, at=0.45)
    C.noz(xl, 360, "l", "N1")
    C.t("VAPOUR HORN", x, 362, 2.0, "middle")
    ti(C, 250, 345, [(250, 360), (250, 349.6)], svc="C-201 flash zone temperature", line="vac_transfer")
    # left side returns
    for key, y, txt, xx in (("lvgo_ret", 108, "LVGO PA RETURN (FV-2011)", xtl), ("hvgo_ret", 252, "HVGO PA RETURN (FV-2016)", xl),
                            ("wash_oil", 301, "WASH OIL FROM P-202", xl)):
        C.opc(50, y, "l", txt, dref(14))
        C.line(key, [(50, y), (xx - 2.5, y)], lab=0, at=0.5 if key != "wash_oil" else 0.25)
        C.noz(xx, y, "l")
    # wash oil FIC-2020 (on this sheet)
    yw = 301.0
    C.orifice(200, yw, "h")
    REG.inst("FE-2020", C.sid, svc="Wash oil flow element", line="wash_oil")
    C.station(215, yw, 260, yw, "FV-2020", "FC", byp=1, tag_pos=(241, yw - 6))
    ctrl(C, "FIC-2020", 200, yw - 16, 220, yw - 26, tap=[(200, yw - 2.4), (200, yw - 11.4)],
         sig=[(204.6, yw - 16), (210, yw - 16), (210, yw - 26), (215.4, yw - 26)],
         vsig=[(224.6, yw - 26), (237.5, yw - 26), (237.5, yw - 10.4)], fail="FC", line="wash_oil")
    C.t("FAL (MIN. WETTING)", 226, yw - 33, 2.0)
    # overhead to ejectors + PSV + PIC + X-104
    C.noz(x, 86, "u", "N2")
    C.line("vac_ov", [(x, 83.5), (x, 64), (790, 64)], lab=1, at=0.5)
    C.opc(790, 64, "r", "TO J-201A/B", dref(15))
    pv = C_.PSV["PSV-2001"]
    C.psv(x - 14, 92, "PSV-2001", pv["set_barg"], f"1{pv['orifice']}", up=14, out="l", outlen=16, dest="FLARE",
          text_side=1)
    REG.use_line("2001_out", C.sid)
    C.t(REG.no("2001_out"), x - 30, 70, 2.0, "end")
    ctrl(C, "PIC-2010", 400, 80, 425, 80, tap=[(x + 12, 90), (x + 12, 80), (395.4, 80)], line="vac_ov")
    C.t("TO PV-2010 (NCG RECYCLE, " + dref(15) + ")", 431, 81, 2.0)
    ctrl(C, "TIC-2012", 400, 120, 425, 120, tap=[(xtr, 120), (395.4, 120)], line="vac_ov")
    C.t("SP CASCADE TO TIC-2013", 431, 121, 2.0)
    C.package(560, 80, 50, 18, "X-104", ["CORROSION INHIBITOR"])
    C.line("ch_ci", [(585, 80), (585, 64)], lab=None)
    C.check(585, 73, "u")
    C.t(REG.no("ch_ci"), 589, 75, 2.0)
    pd = free_tag(C, "PDI")
    C.bub(460, 140, pd, "dcs", svc="C-201 dP top - flash zone")
    C.tap([(xtr, 140), (455.4, 140)])
    # draws -> P-201/202/203 (sheet 014)
    draws = [("lvgo_s", 172, xtr, "LVGO TO P-201A/B", "LIC-2014", "FIC-2015"),
             ("hvgo_s", 249, xr, "HVGO TO P-202A/B", "LIC-2018", "FIC-2019"),
             ("slop_s", 342, xr, "SLOP WAX TO P-203A/B", "LIC-2021", "FIC-2022")]
    for key, y, xx, txt, lic, fic in draws:
        C.noz(xx, y, "r")
        C.line(key, [(xx + 2.5, y), (790, y)], lab=0, at=0.75)
        C.opc(790, y, "r", txt, dref(14))
        lt_ = "LT-" + lic.split("-")[1]
        C.tap([(xx, y - 4), (xx + 18, y - 4), (xx + 18, y - 13), (xx + 25.4, y - 13)])
        ctrl(C, lic, xx + 30, y - 13, xx + 55, y - 13, line=key)
        C.t(f"SP TO {fic} ({dref(14).split('-')[-1]})", xx + 61, y - 12, 2.0)
        ti(C, xx + 30, y + 15, [(xx + 30, y), (xx + 30, y + 10.4)], svc=f"{txt.split()[0]} draw temperature",
           line=key)
    # stripping steam
    ys_ = 446.0
    C.opc(50, ys_, "l", "MP STEAM HEADER", dref(16))
    C.line("ms_c201", [(50, ys_), (x - wb / 2 - 2.5, ys_)], lab=0, at=0.15)
    C.noz(x - wb / 2, ys_, "l")
    C.orifice(140, ys_, "h")
    REG.inst("FE-2023", C.sid, svc="C-201 stripping steam flow element", line="ms_c201")
    C.station(160, ys_, 205, ys_, "FV-2023", "FC", byp=1, tag_pos=(186, ys_ - 6))
    ctrl(C, "FIC-2023", 140, ys_ - 16, 160, ys_ - 26, tap=[(140, ys_ - 2.4), (140, ys_ - 11.4)],
         sig=[(144.6, ys_ - 16), (150, ys_ - 16), (150, ys_ - 26), (155.4, ys_ - 26)],
         vsig=[(164.6, ys_ - 26), (182.5, ys_ - 26), (182.5, ys_ - 10.4)], fail="FC", line="ms_c201")
    # quench
    yq = 465.0
    C.opc(50, yq, "l", "COOLED VR QUENCH", dref(14))
    C.line("vr_quench", [(50, yq), (x - wb / 2 - 2.5, yq)], lab=0, at=0.15)
    C.noz(x - wb / 2, yq, "l")
    C.orifice(140, yq, "h")
    REG.inst("FE-2027", C.sid, svc="VR quench flow element", line="vr_quench")
    C.station(160, yq, 205, yq, "FV-2027", "FC", byp=1, tag_pos=(186, yq + 15))
    ctrl(C, "FIC-2027", 140, yq + 16, 230, yq + 22, tap=[(140, yq + 2.4), (140, yq + 11.4)],
         sig=[(144.6, yq + 16), (230, yq + 16), (230, yq + 17.4)],
         vsig=[(225.4, yq + 22), (215, yq + 22), (215, 455), (182.5, 455), (182.5, yq - 10.4)], fail="FC",
         line="vr_quench")
    ctrl(C, "TIC-2026", 250, 480, 275, 480, tap=[(x - wb / 2 + 4, 476), (254.6, 476), (254.6, 480)] if False else
         [(x - 10, 482), (x - 10, 488), (250, 488), (250, 484.6)], line="vr_s", sig=[(254.6, 480), (270.4, 480)])
    C.t("MAX 365 C; SP TO FIC-2027", 281, 481, 2.0)
    # bottoms -> EIV-2041 -> P-204
    pp = pump_pair(C, 470, 540, "P-204", "vr_s", "vr_pd")
    C.line("vr_s", [(x, 479), (x, pp["s"][1]), pp["s"]], lab=1, at=0.5, arrow=False)
    C.xv(x, 505, "v", "EIV-2041", "FC", side=1, tag_pos=(x + 9, 503), kind="ball")
    REG.inst("EIV-2041", C.sid, sys="SIS", sif="SIF-204", fail="FC", svc=C_.SIFS["SIF-204"]["function"])
    C.bub(375, 522, "HS-2041", "panel", sys="SIS", sif="SIF-204", svc="EIV-2041 manual close (CCR + field)")
    C.ilk(375, 502, "SIF-204", below=False)
    C.sig([(375, 516.6), (375, 506)], "e")
    C.sig([(371, 502), (x + 7, 502), (x + 7, 505)], "e")
    REG.inst("BY-2041", C.sid, sys="F&G", sif="SIF-204", svc="Fire confirmation from F&G (P-204 area)")
    yd = pp["dr"][1]
    C.line("vr_pd", [pp["dr"], (600, yd), (600, 455), (790, 455)], lab=2, at=0.6)
    C.opc(790, 455, "r", "VR TO E-111", dref(3))
    C.line("p204_mf", [(520, yd), (520, 476), (x + wb / 2 + 2.5, 476)] if False else
           [(530, yd), (530, 474), (x + 18, 474), (x + 18, 471)], lab=1, at=0.6)
    C.dot(530, yd)
    C.orifice(470, 474, "h", ro=True)
    C.gate(490, 474, "h")
    # level / SIS
    yl = 425.0
    C.tap([(x + wb / 2, yl), (x + wb / 2 + 26, yl)] if False else [(x + wb / 2, yl), (395.4, yl)])
    ctrl(C, "LIC-2024", 400, yl, 425, yl, line="vr_s")
    C.t("SP TO FIC-2025 (" + dref(14).split('-')[-1] + ")", 431, yl + 1, 2.0)
    sis_initiator(C, ["LT-2024B"], 400, yl - 25, "LZHH-2024", "SIF-203", 425, yl - 25, 0, 0,
                  tap=[(x + wb / 2, yl - 20), (390, yl - 20), (390, yl - 25), (394.6, yl - 25)])
    C.ilk(450, yl - 25, "SIF-203", below=False)
    C.sig([(430.4, yl - 25), (446, yl - 25)], "e")
    C.t("TO XV-1083 (" + dref(6) + ")", 445, yl - 34, 2.0)
    return save(C)

# ============================================================================= SHEET 014
def flow_loop(C, key, y, x_fe, xs0, xs1, loop, fail="FC", fv=None, up=True):
    """FE + FT + FIC + FV station on a horizontal line at y (FE at x_fe, station xs0..xs1)."""
    num = loop.split("-")[1]
    C.orifice(x_fe, y, "h")
    REG.inst(f"FE-{num}", C.sid, svc=C_.LOOPS[loop]["service"] + " flow element", line=key)
    xm = (xs0 + xs1) / 2
    C.station(xs0, y, xs1, y, fv or f"FV-{num}", fail, byp=1, tag_pos=(xm + 3.5, y - 6))
    ctrl(C, loop, x_fe, y - 16, x_fe + (20 if x_fe < xm else -20), y - 28,
         tap=[(x_fe, y - 2.4), (x_fe, y - 11.4)],
         sig=[(x_fe, y - 20.6), (x_fe, y - 28), (x_fe + (15.4 if x_fe < xm else -15.4), y - 28)],
         vsig=[(x_fe + (24.6 if x_fe < xm else -24.6), y - 28), (xm, y - 28), (xm, y - 10.4)], fail=fail, line=key)


def sheet_014():
    C = new_sheet(14, [
        "LVGO / HVGO pumps serve pumparound + product; pumparound return temperatures control column heat removal.",
        "VR, HVGO product and slop wax lines steam traced (ST) - high pour point.",
        "Slop wax routed hot (steam traced, no cooler) to delayed coker feed at slop-draw temperature.",
        "E-201 LP steam generator: VR on tube side; steam side protected by PSV-2003 to safe location.",
    ])
    eq_boxes(C, ["P-201A/B", "P-202A/B", "P-203A/B", "A-201", "A-202", "E-201"], w=85)
    # ---- LVGO
    p1 = pump_pair(C, 120, 140, "P-201", "lvgo_s", "lvgo_pd")
    C.opc(50, p1["s"][1], "l", "LVGO FROM C-201", dref(13))
    C.line("lvgo_s", [(50, p1["s"][1]), p1["s"]], arrow=False, at=0.45)
    y = p1["dr"][1]
    C.line("lvgo_pd", [p1["dr"], (230, y)], lab=0, at=0.5, arrow=False)
    C.opc(230, y, "r", "TO E-103", dref(1))
    C.opc(330, y, "l", "FROM E-103", dref(1))
    a1 = C.aircooler(350, y - 4, 34, 8, 2)
    C.t("A-201", 367, y - 7, 2.6, "middle", bold=True)
    C.line("lvgo_c1", [(330, y), a1["i"]], lab=None)
    C.line("lvgo_c2", [a1["o"], (420, y)], lab=0, at=0.5, arrow=False)
    C.dot(420, y)
    C.line("lvgo_ret", [(420, y), (790, y)], lab=0, at=0.88)
    C.opc(790, y, "r", "LVGO PA TO C-201 TOP", dref(13))
    flow_loop(C, "lvgo_ret", y, 560, 580, 625, "FIC-2011")
    ctrl(C, "TIC-2013", 680, y - 16, 700, y - 28, tap=[(680, y), (680, y - 11.4)],
         sig=[(684.6, y - 16), (700, y - 16), (700, y - 23.4)], line="lvgo_ret",
         vsig=[(695.4, y - 28), (660, y - 28), (660, y - 40), (367, y - 40), (367, y - 30)])
    C.bub(367, y - 25, "TY-2013", "field", svc="A-201 fan auto-variable pitch signal", r=4.0)
    C.t("FAN PITCH", 373, y - 25, 2.0)
    C.t("SP FROM TIC-2012", 706, y - 30, 2.0)
    C.line("lvgo_prod", [(420, y), (420, 165), (790, 165)], lab=1, at=0.88)
    C.opc(790, 165, "r", "LVGO TO HCU", "OSBL")
    flow_loop(C, "lvgo_prod", 165, 560, 580, 625, "FIC-2015")
    C.t("SP FROM LIC-2014", 600, 132, 2.0) if False else None
    ti(C, 440, 180, [(440, 165), (440, 175.4)], svc="LVGO product temperature", line="lvgo_prod")
    # ---- HVGO
    p2 = pump_pair(C, 120, 290, "P-202", "hvgo_s", "hvgo_pd")
    C.opc(50, p2["s"][1], "l", "HVGO FROM C-201", dref(13))
    C.line("hvgo_s", [(50, p2["s"][1]), p2["s"]], arrow=False, at=0.45)
    y = p2["dr"][1]
    C.line("hvgo_pd", [p2["dr"], (230, y)], lab=0, at=0.5, arrow=False)
    C.opc(230, y, "r", "TO E-108", dref(3))
    C.dot(175, y)
    C.line("wash_oil", [(175, y), (175, 222), (230, 222)], lab=None, arrow=False)
    C.t(REG.no("wash_oil"), 180, 219, 2.0)
    C.opc(230, 222, "r", "WASH OIL TO C-201", dref(13))
    C.opc(330, y, "l", "FROM E-108", dref(3))
    C.line("hvgo_c1", [(330, y), (380, y)], lab=0, at=0.3, arrow=False)
    C.dot(380, y)
    C.line("hvgo_ret", [(380, y), (790, y)], lab=0, at=0.88)
    C.opc(790, y, "r", "HVGO PA TO C-201", dref(13))
    flow_loop(C, "hvgo_ret", y, 560, 580, 625, "FIC-2016")
    ctrl(C, "TIC-2017", 680, y - 16, 700, y - 28, tap=[(680, y), (680, y - 11.4)],
         sig=[(684.6, y - 16), (700, y - 16), (700, y - 23.4)], line="hvgo_ret")
    C.t("TO TV-2017 (E-108 BYPASS, " + dref(3) + ")", 706, y - 36, 2.0)
    a2 = C.aircooler(420, 306, 34, 8, 2)
    C.t("A-202", 437, 303, 2.6, "middle", bold=True)
    C.line("hvgo_p1", [(380, y), (380, 310), a2["i"]], lab=0, at=0.5, side=-1)
    C.line("hvgo_prod", [a2["o"], (790, 310)], lab=0, at=0.88)
    C.opc(790, 310, "r", "HVGO TO FCC / HCU", "OSBL")
    flow_loop(C, "hvgo_prod", 310, 560, 580, 625, "FIC-2019")
    # ---- slop wax
    p3 = pump_pair(C, 120, 420, "P-203", "slop_s", "slop_d")
    C.opc(50, p3["s"][1], "l", "SLOP WAX FROM C-201", dref(13))
    C.line("slop_s", [(50, p3["s"][1]), p3["s"]], arrow=False, at=0.45)
    y = p3["dr"][1]
    C.line("slop_d", [p3["dr"], (330, y)], lab=0, at=0.2, arrow=False)
    C.opc(330, y, "r", "SLOP WAX TO COKER (HOT)", "OSBL")
    flow_loop(C, "slop_d", y, 190, 210, 255, "FIC-2022")
    # ---- VR through E-201
    k = C.kettle(470, 455)
    C.t("E-201", 470, 475, 2.6, "middle", bold=True)
    C.opc(390, 420, "l", "VR FROM E-111", dref(3))
    C.line("vr_c1", [(390, 420), (k["ct"][0], 420), k["ct"]], lab=None)
    C.t(REG.no("vr_c1"), 405, 417, 2.0)
    C.line("vr_c2", [k["cb"], (k["cb"][0], 490), (390, 490)], lab=None)
    C.opc(390, 490, "l", "VR TO E-105", dref(1), flow="out")
    C.t(REG.no("vr_c2"), 405, 488, 2.0)
    yv = 522.0
    C.opc(390, yv, "l", "VR FROM E-105", dref(1))
    C.line("vr_prod", [(390, yv), (620, yv)], lab=0, at=0.88)
    C.opc(620, yv, "r", "VR TO COKER", "OSBL")
    C.hop(k["sb"][0], yv, "h")
    flow_loop(C, "vr_prod", yv, 500, 520, 565, "FIC-2025")
    C.dot(425, yv)
    C.line("vr_quench", [(425, yv), (425, 548), (390, 548)], lab=None)
    C.t(REG.no("vr_quench"), 428, 540, 2.0)
    C.opc(390, 548, "l", "VR QUENCH TO C-201", dref(13), flow="out")
    C.line("ls_e201", [k["sv"], (k["sv"][0], 400), (620, 400)], lab=1, at=0.35)
    pv = C_.PSV["PSV-2003"]
    C.psv(560, 400, "PSV-2003", pv["set_barg"], f"1{pv['orifice']}", up=16, out="r", outlen=14, dest="ATM (SAFE LOC.)",
          text_side=-1)
    REG.use_line("psv2003_out", C.sid)
    C.t(REG.no("psv2003_out"), 563, 378, 2.0)
    C.opc(620, 400, "r", "TO LP STEAM HDR", dref(16))
    C.opcv(k["sb"][0], 562, "d", "BFW HEADER", dref(16), flow="in")
    C.line("bfw_e201", [(k["sb"][0], 562), k["sb"]], lab=None)
    C.t(REG.no("bfw_e201"), k["sb"][0] + 3, 478, 2.0)
    C.cv(k["sb"][0], 540, "v", "LV-2030", "FC", side=1, tag_pos=(k["sb"][0] + 9, 538))
    C.gate(k["sb"][0], 553, "v")
    C.gate(k["sb"][0], 508, "v")
    lv = k["lvl"]
    C.tap([lv, (lv[0] + 10, lv[1])])
    ctrl(C, "LIC-2030", lv[0] + 15, lv[1], lv[0] + 40, lv[1], line="bfw_e201",
         vsig=[(lv[0] + 40, lv[1] + 5.4), (lv[0] + 40, 540), (k["sb"][0] + 7, 540)], fail="FC")
    C.line("bd_e201", [(k["sb"][0] - 6, k["sb"][1]), (k["sb"][0] - 6, 478)], lab=None)
    C.t("BLOWDOWN (OSBL)", 452, 483, 2.0, "end")
    C.t(REG.no("bd_e201"), 452, 486.5, 2.0, "end")
    return save(C)


# ============================================================================= SHEET 015
def sheet_015():
    C = new_sheet(15, [
        "Three-stage steam ejector set, each stage 2 x 50 % in parallel (J-20xA/B); MP motive steam.",
        "Barometric legs from E-202/203/204 sealed in hotwell D-201 (min. 10.5 m leg height).",
        "C-201 pressure control by off-gas recycle to J-201 (1st stage) suction via PV-2010; TSVs on CW sides.",
        "Vacuum off-gas to H-201 burners via D-202 and PV-2031 (backpressure).",
    ])
    eq_boxes(C, ["J-201", "J-202", "J-203", "E-202", "E-203", "E-204", "D-201", "D-202", "P-205A/B", "P-206A/B"],
             w=66, gap=1.5) if False else eq_boxes(C, ["J-201", "J-202", "J-203", "E-202", "E-203", "E-204", "D-201"],
                                                   w=74)
    ymh = 66.0
    C.opc(50, ymh, "l", "MP STEAM HEADER", dref(16))
    stages = [("J-201", 100, "vac_ov", "201_d", "ms_201", "E-202", "202_v", "leg_202"),
              ("J-202", 270, "202_v", "202_d", "ms_202", "E-203", "203_v", "leg_203"),
              ("J-203", 440, "203_v", "203_d", "ms_203", "E-204", "204_v", "leg_204")]
    C.line("ms_201", [(50, ymh), (480, ymh)], lab=0, at=0.13, arrow=False)
    yin = 110.0
    for i, (jt, xs, ink, dk, mk, et, vk, lk) in enumerate(stages):
        xe = xs + 100
        if i == 0:
            C.opc(50, yin, "l", "FROM C-201 TOP", dref(13))
            C.line(ink, [(50, yin), (xs, yin)], lab=0, at=0.5, arrow=False)
        # parallel ejectors
        C.pipe([(xs, yin - 12), (xs, yin + 12)], arrow=False)
        for j, yy in enumerate((yin - 12, yin + 12)):
            C.pipe([(xs, yy), (xs + 8, yy)], arrow=False)
            C.gate(xs + 4, yy, "h")
            e = C.ejector(xs + 8, yy, L=26)
            C.pipe([e["d"], (xs + 42, yy)], arrow=False)
            C.t(jt + "AB"[j], xs + 21, yy + 6.5, 2.2, "middle", bold=True)
            C.pipe([(e["m"][0], ymh), e["m"]], util=True)
            C.gate(e["m"][0], ymh + 8, "v")
        if i:
            C.dot(xs - 0, yin)
        C.pipe([(xs + 42, yin - 12), (xs + 42, yin + 12)], arrow=False)
        C.dot(xs, yin)
        C.dot(xs + 42, yin)
        if mk != "ms_201":
            C.dot(xs + 13, ymh)
            REG.use_line(mk, C.sid)
            C.t(REG.no(mk), xs + 15, ymh - 1.2, 2.0)
        # condenser (vertical)
        cx, cy0, cy1 = xe, 85.0, 175.0
        C.g_eq.add(C.d.rect((cx - 8, cy0), (16, cy1 - cy0)))
        C.g_eq.add(C.d.line((cx - 8, cy1 - 12), (cx + 8, cy1 - 12), stroke_width=0.3))
        C.t(et, cx, cy0 - 3, 2.6, "middle", bold=True)
        C.line(dk, [(xs + 42, yin), (cx - 8, yin)], lab=0, at=0.5)
        # CW stubs
        k = et[2:].replace("-", "").lower()
        C.line(f"cws_{k}", [(cx + 28, cy1 - 18), (cx + 8, cy1 - 18)], lab=None)
        C.line(f"cwr_{k}", [(cx + 8, cy0 + 8), (cx + 28, cy0 + 8)], lab=None)
        C.t("CWS", cx + 29, cy1 - 17, 2.0)
        C.t("CWR", cx + 29, cy0 + 9, 2.0)
        tsv(C, cx + 20, cy0 + 8)
        C.t(REG.no(f"cws_{k}"), cx + 10, cy1 - 13, 2.0, "start", rot=None) if False else None
        # vapour to next stage
        yv = 150.0
        if i < 2:
            nx = stages[i + 1][1]
            C.line(vk, [(cx + 8, yv), (nx - 12, yv), (nx - 12, yin), (nx, yin)], lab=0, at=0.5, side=1, arrow=False)
        # barometric leg
        C.line(lk, [(cx, cy1), (cx, 352)], lab=0, at=0.35, side=-1)
        ti(C, cx + 18, 125, [(cx + 8, 125), (cx + 13.4, 125)], svc=f"{et} vapour outlet temperature")
    # CW line numbers (table)
    rows = [f"{et}: CWS {REG.no('cws_' + et[2:].replace('-', '').lower())}  /  CWR "
            f"{REG.no('cwr_' + et[2:].replace('-', '').lower())}" for et in ("E-202", "E-203", "E-204")]
    C.box_note(25, 528, ["COOLING WATER CONNECTIONS (HEADERS ON " + dref(16) + "):"] + rows, size=2.0)
    # E-204 vapour -> D-202 -> PV-2031 -> H-201
    dx = 680.0
    C.vdrum(dx, 115, 20, 40)
    C.t("D-202", dx + 13, 140, 2.6, "start", bold=True)
    C.line("204_v", [(548, 150), (dx - 10, 150)], lab=0, at=0.5)
    C.line("vog", [(dx, 106), (dx, 95), (790, 95)], lab=1, at=0.75)
    C.opc(790, 95, "r", "OFF-GAS TO H-201", dref(12))
    C.bub(772, 112, "AT-2032", "field", svc=IC_AN["AT-2032"], line='vog')
    C.tap([(772, 95), (772, 107.4)])
    C.station(705, 95, 750, 95, "PV-2031", "FO", byp=1, side=-1, tag_pos=(731, 89))
    ctrl(C, "PIC-2031", 712, 125, 735, 125, tap=[(dx + 10, 125), (707.4, 125)], line="vog",
         vsig=[(735, 120.4), (735, 112), (727.5, 112), (727.5, 101)], fail="FO")
    # NCG recycle to J-203 suction (PV-2010)
    C.line("ncg_recy", [(dx, 95), (dx, 74), (90, 74), (90, yin)], lab=1, at=0.85)
    C.dot(dx, 95)
    C.dot(90, yin)
    for st_ in stages:
        C.hop(st_[1] + 13.2, 74, "h")
    C.station(580, 74, 625, 74, "PV-2010", "FO", bypass=False, side=-1, tag_pos=(606, 69))
    C.t("FROM PIC-2010 (" + dref(13) + ")", 640, 60, 2.0)
    C.sig([(638, 59), (602.5, 59), (602.5, 66.8)], "e")
    REG.inst("PV-2010", C.sid, svc=C_.LOOPS["PIC-2010"]["service"], fail="FO", loop="PIC-2010")
    # hotwell D-201
    hx0, hy0, L, D = 150.0, 352.0, 440.0, 30.0
    C.hdrum(hx0, hy0, L, D)
    C.g_eq.add(C.d.line((hx0 + 360, hy0 + 8), (hx0 + 360, hy0 + D), stroke_width=0.45))
    C.t("D-201 HOTWELL", hx0 + 150, hy0 + 18, 2.8, "middle", bold=True)
    C.t("OIL COMPT.", hx0 + 400, hy0 + 18, 2.1, "middle")
    pv = C_.PSV["PSV-2002"]
    C.psv(hx0 + 60, hy0, "PSV-2002", pv["set_barg"], f"1{pv['orifice']}", up=14, out="r", outlen=14,
          dest="FLARE", text_side=1)
    REG.use_line("2002_out", C.sid)
    C.t(REG.no("2002_out"), hx0 + 64, hy0 - 30, 2.0)
    C.line("d201_v", [(hx0 + 420, hy0), (hx0 + 420, 230), (dx, 230), (dx, 159)], lab=1, at=0.6)
    # pumps
    p5 = pump_pair(C, 230, 450, "P-205", "hw_sw_s", "hw_sw_d")
    C.line("hw_sw_s", [(200, hy0 + D), (200, p5["s"][1]), p5["s"]], arrow=False, lab=0, at=0.5, side=-1)
    C.line("hw_sw_d", [p5["dr"], (790, p5["dr"][1])], lab=0, at=0.15)
    C.opc(790, p5["dr"][1], "r", "SOUR WATER TO SWS", "OSBL")
    C.station(600, p5["dr"][1], 645, p5["dr"][1], "LV-2028", "FC", byp=1, tag_pos=(626, p5["dr"][1] - 6))
    p6 = pump_pair(C, 400, 470, "P-206", "hw_oil_s", "hw_oil_d", ydisch=22)
    C.line("hw_oil_s", [(hx0 + 400, hy0 + D), (hx0 + 400, 440), (350, 440), (350, p6["s"][1]), p6["s"]],
           arrow=False, lab=1, at=0.5)
    C.hop(350, p5["dr"][1], "v")
    C.line("hw_oil_d", [p6["dr"], (460, p6["dr"][1]), (460, 500), (540, 500)], lab=2, at=0.5)
    C.opc(540, 500, "r", "SLOP OIL TO SLOP", "OSBL")
    C.station(475, 500, 520, 500, "LV-2029", "FC", byp=1, tag_pos=(501, 494))
    C.tap([(hx0 - 4, hy0 + 20), (125.4, hy0 + 20)])
    ctrl(C, "LIC-2028", 120, hy0 + 20, 120, hy0 + 45, line="hw_sw_d",
         vsig=[(124.6, hy0 + 45), (130, hy0 + 45), (130, 405), (622.5, 405), (622.5, p5["dr"][1] - 10.4)],
         fail="FC")
    C.tap([(hx0 + 430, hy0 + 15), (hx0 + 450, hy0 + 15)])
    ctrl(C, "LIC-2029", hx0 + 455, hy0 + 15, hx0 + 455, hy0 + 37, line="hw_oil_d",
         vsig=[(hx0 + 455, hy0 + 41.6), (hx0 + 455, 486), (497.5, 486), (497.5, 489.6)], fail="FC")
    return save(C)


# ============================================================================= SHEET 016
def header(C, key, y, x0, x1, txt_in, src, branches, opc_out=None):
    C.opc(x0, y, "l", txt_in, src)
    C.line(key, [(x0, y), (x1, y)], lab=0, at=0.08, arrow=opc_out is not None)
    for xb, txt in branches:
        C.dot(xb, y)
        C.pipe([(xb, y), (xb, y + 11)], util=True)
        C.t(txt, xb + 1.5, y + 14.5, 2.0, "middle")
    if opc_out:
        C.opc(x1, y, "r", opc_out[0], opc_out[1])


def sheet_016():
    C = new_sheet(16, [
        "Branch destinations shown at header take-offs; individual consumer lines on referenced P&IDs.",
        "Flare header slopes to D-104 (no pockets); all PSV discharges enter top of header.",
        "D-104 pump-out by P-119A/B to OSBL slop; LIC-9003 starts / stops the duty pump.",
        "Steam / BFW / CW / IA / N2 flows are unit totals (H&MB + allowances stated in line list).",
    ])
    eq_boxes(C, ["D-103", "D-104", "P-119A/B"], w=90)
    # fuel gas
    C.opc(50, 110, "l", "REFINERY FUEL GAS", "OSBL")
    C.line("fg_osbl", [(50, 110), (210, 110)], lab=0, at=0.55)
    C.station(140, 110, 185, 110, "PV-9001", "FC", byp=1, tag_pos=(166, 104))
    ctrl(C, "PIC-9001", 195, 88, 162.5, 88, tap=[(209, 97), (203, 97), (203, 88), (199.6, 88)],
         sig=[(190.4, 88), (167.1, 88)], vsig=[(162.5, 92.6), (162.5, 102.2)], fail="FC", line="fg_hdr")
    C.vdrum(220, 95, 22, 40)
    C.t("D-103", 233, 125, 2.6, "start", bold=True)
    C.line("fg_hdr", [(220, 86), (220, 70), (500, 70)], lab=1, at=0.35, arrow=False)
    C.bub(270, 52, "AT-1021", "field", svc=IC_AN["AT-1021"], line='fg_hdr')
    C.tap([(270, 70), (270, 56.6)])
    C.bub(640, 165, "TT-9005", "field", svc=IC_AN["TT-9005"])
    C.bub(665, 165, "XA-9101", "panel", svc=IC_AN["XA-9101"])
    C.t("AMBIENT (AIR COOLERS) / ANALYSER HOUSE AH-101 ALARM", 640, 175, 2.0)
    for xb, t, sh in ((300, "H-101 MAIN + PILOTS", 5), (380, "H-201 MAIN + PILOTS", 12), (460, "D-102 MAKE-UP", 9)):
        C.dot(xb, 70)
        C.pipe([(xb, 70), (xb, 85)], util=True)
        C.opcv(xb, 85, "d", t, dref(sh))
    C.line("d103_liq", [(220, 144), (220, 200), (330, 200), (330, 250)], lab=1, at=0.35)
    C.station(240, 200, 285, 200, "LV-9002", "FC", bypass=False, tag_pos=(266, 194))
    C.tap([(231, 130), (245, 130)])
    ctrl(C, "LIC-9002", 250, 130, 275, 130, line="d103_liq",
         vsig=[(275, 134.6), (275, 185), (262.5, 185), (262.5, 189.6)], fail="FC")
    # flare KO drum
    C.opc(50, 240, "l", "FROM UNIT PSVs / VENTS", "ALL SHEETS")
    C.line("fl_hdr", [(50, 240), (300, 240), (300, 250)], lab=0, at=0.5)
    C.hdrum(300, 250, 140, 32)
    C.t("D-104 FLARE KO DRUM", 370, 268, 2.6, "middle", bold=True)
    C.line("fl_osbl", [(420, 250), (420, 240), (790, 240)], lab=1, at=0.5)
    C.opc(790, 240, "r", "TO REFINERY FLARE", "OSBL")
    pp = pump_pair(C, 470, 315, "P-119", "d104_po", "p119_d", ydisch=26)
    C.line("d104_po", [(400, 282), (400, pp["s"][1]), pp["s"]], lab=1, at=0.5, arrow=False)
    C.line("p119_d", [pp["dr"], (560, pp["dr"][1])], lab=0, at=0.5)
    C.opc(560, pp["dr"][1], "r", "PUMP-OUT TO SLOP", "OSBL")
    C.tap([(440, 265), (545.4, 265)])
    ctrl(C, "LIC-9003", 550, 265, 575, 265, line="d104_po")
    C.bub(600, 265, "LY-9003", "field", svc="P-119A/B start/stop (high / low level) via MCC", r=4.0)
    C.sig([(579.6, 265), (596, 265)], "e")
    C.t("START / STOP P-119A/B (MCC)", 606, 266, 2.0)
    srcs = ", ".join(sorted(p["tag"] for p in C_.PSV.values() if p["dest"] == "Flare"))
    C.t("RELIEF SOURCES: " + srcs, 50, 228, 2.0)
    C.t("+ H-101 / H-201 FG DBB VENTS, D-102 / D-105 OFF-GAS (UPSET)", 50, 231.5, 2.0)
    # steam / water / air headers
    hdrs = [
        ("hs_hdr", 335, "HP STEAM 41.4 barg", [(300, "E-116 (010)")]),
        ("ms_hdr", 362, "MP STEAM 10.3 barg", [(200, "E-117 (011)"), (260, "H-201 COIL (012)"), (320, "C-201 (013)"),
                                               (380, "EJECTORS (015)"), (440, "E-113 EXPORT (003)")]),
        ("ls_hdr", 392, "LP STEAM 3.5 barg", [(200, "H-101 SS COIL (004)"), (270, "SNUFFING (005/012)"),
                                              (340, "E-201 EXPORT (014)")]),
        ("bfw_hdr", 420, "BFW 50 barg", [(200, "E-113 (003)"), (260, "E-201 (014)"), (320, "DESUP. (004)")]),
        ("cws_hdr", 448, "COOLING WATER SUPPLY", [(200, "E-115 (009)"), (260, "E-202/203/204 (015)")]),
        ("ia_hdr", 476, "INSTRUMENT AIR", [(200, "UNIT IA DISTRIBUTION")]),
        ("n2_hdr", 500, "NITROGEN", [(200, "PURGE / BLANKETING")]),
    ]
    for key, y, txt, br in hdrs:
        header(C, key, y, 50, 520, txt, "OSBL", br)
    C.station(560, 375, 605, 375, "PV-9004", "FO", byp=1, tag_pos=(586, 369)) if False else None
    C.line("ms_ls_ld", [(520, 362), (560, 362), (560, 392), (520, 392)], lab=1, at=0.5, side=1)
    C.cv(560, 377, "v", "PV-9004", "FO", side=1, tag_pos=(567, 372))
    ctrl(C, "PIC-9004", 600, 392, 600, 377, tap=[(560, 392), (595.4, 392)], line="ls_hdr",
         sig=[(600, 387.4), (600, 381.6)], vsig=[(595.4, 377), (567, 377)], fail="FO")
    # returns
    for key, y, txt, src in (("cd_hdr", 525, "CONDENSATE RETURN", "FROM E-116 / E-117"),
                             ("cwr_hdr", 545, "CW RETURN", "FROM E-115 / E-202..204"),
                             ("bd_hdr", 565, "CLOSED DRAIN TO SLOP", "FROM UNIT CLOSED DRAINS")):
        C.line(key, [(520, y), (50, y)], lab=0, at=0.75)
        C.opc(50, y, "l", txt, "OSBL", flow="out")
        C.t(src, 525, y + 1, 2.0)
    # unit ESD
    sf = C_.SIFS["SIF-901"]
    C.bub(640, 130, "HS-9000", "panel", sys="SIS", sif="SIF-901", svc="Unit ESD push-button (CCR + field)")
    C.ilk(670, 130, "SIF-901", below=True)
    C.sig([(644.6, 130), (666, 130)], "e")
    C.t(f"{sf['function']} ({sf['sil']})", 676, 128, 2.0)
    C.t("TRIPS: ALL UNIT XV / EIV, H-101 & H-201 BMS", 676, 131.5, 2.0)
    REG.inst("UZ-9000", C.sid, sys="SIS", sif="SIF-901", svc="Unit ESD-1 logic (SIS)")
    return save(C)


# ============================================================================= SHEET 000 (legend)
def sheet_000():
    C = new_sheet(0, ["Legend applies to all P&IDs CFU-xxx-PR-PID-001 to -016.",
                      "F&G devices (GD gas / H2S, BE flame, HS manual call points) are listed in instrument index "
                      "CFU-000-IC-IDX-001; F&G layout drawing by others.",
                      "DCS computing blocks (FY / PY / FFY) per control scheme drawings CFU-xxx-IC-CSD; listed in index."])
    t = C.t
    # column 1: lines & valves
    x, y = 25.0, 30.0
    t("LINE SYMBOLS", x, y, 3.0, bold=True)
    items = [("pipe", "MAIN PROCESS LINE"), ("util", "UTILITY / SECONDARY LINE"), ("e", "ELECTRICAL SIGNAL (4-20 mA / DI / DO)"),
             ("d", "SOFTWARE / DATA LINK (DCS / SIS)"), ("c", "PROCESS IMPULSE / CAPILLARY"),
             ("duct", "DUCT (AIR / FLUE GAS)")]
    for i, (k, lbl) in enumerate(items):
        yy = y + 9 + i * 8
        if k == "pipe":
            C.pipe([(x, yy), (x + 30, yy)])
        elif k == "util":
            C.pipe([(x, yy), (x + 30, yy)], util=True)
        elif k == "duct":
            duct(C, [(x, yy), (x + 30, yy)])
        else:
            C.sig([(x, yy), (x + 30, yy)], k)
        t(lbl, x + 36, yy + 0.8, 2.2)
    y = 95.0
    t("VALVES & PIPING COMPONENTS", x, y, 3.0, bold=True)
    vitems = [("gate", "GATE VALVE"), ("gate_nc", "GATE VALVE NORMALLY CLOSED (NC)"), ("globe", "GLOBE VALVE"),
              ("ball", "BALL VALVE"), ("butterfly", "BUTTERFLY VALVE / DAMPER"), ("check", "CHECK VALVE (FLOW ->)"),
              ("cv", "CONTROL VALVE, DIAPHRAGM ACTUATOR, FAIL POSITION"), ("xv", "ON/OFF SHUTDOWN VALVE (SOLENOID)"),
              ("reducer", "REDUCER"), ("strainer", "STRAINER"), ("fe", "FLOW ELEMENT (ORIFICE PLATE)"),
              ("ro", "RESTRICTION ORIFICE"), ("blind", "SPECTACLE BLIND"), ("spec", "PIPING CLASS (SPEC) BREAK"),
              ("vent", "VENT / DRAIN WITH CAP"), ("hop", "LINES CROSSING, NOT CONNECTED"), ("dot", "LINES CONNECTED")]
    for i, (k, lbl) in enumerate(vitems):
        yy = y + 10 + i * 10.5
        C.pipe([(x, yy), (x + 30, yy)], arrow=False)
        xm = x + 15
        if k == "gate":
            C.gate(xm, yy)
        elif k == "gate_nc":
            C.gate(xm, yy, nc=True)
        elif k == "globe":
            C.globe(xm, yy)
        elif k == "ball":
            C.ball(xm, yy)
        elif k == "butterfly":
            C.butterfly(xm, yy)
        elif k == "check":
            C.check(xm, yy, "r")
        elif k == "cv":
            C.cv(xm, yy, "h", "", "FC")
        elif k == "xv":
            C.xv(xm, yy, "h", "", "FC")
        elif k == "reducer":
            C.reducer(xm, yy)
        elif k == "strainer":
            C.strainer(xm, yy)
        elif k == "fe":
            C.orifice(xm, yy)
        elif k == "ro":
            C.orifice(xm, yy, ro=True)
        elif k == "blind":
            C.blind(xm, yy)
        elif k == "spec":
            C.spec_break(xm, yy, "h", "A1", "B1")
        elif k == "vent":
            C.vent(xm, yy, "u", 6)
        elif k == "hop":
            C.pipe([(xm, yy - 5), (xm, yy + 5)], arrow=False)
            C.hop(xm, yy, "h")
        elif k == "dot":
            C.pipe([(xm, yy), (xm, yy + 5)], arrow=False)
            C.dot(xm, yy)
        t(lbl, x + 36, yy + 0.8, 2.2)
    yy = y + 10 + len(vitems) * 10.5 + 6
    C.psv(x + 15, yy + 22, "PSV-xxxx", 0.0, "ORIFICE", up=14, out="r", outlen=14, dest="FLARE", text_side=-1) if False else None
    C.g_ln.add(C.d.line((x + 15, yy + 24), (x + 15, yy + 18), stroke_width=0.4))
    C.psv(x + 15, yy + 24, "PSV-NNNN", 3.5, "1 x P", up=14, out="r", outlen=12, dest="FLARE", blocks=False,
          text_side=-1) if False else None
    t("PRESSURE SAFETY VALVE: SET PRESSURE, ORIFICE, CSO BLOCKS", x + 36, yy + 14, 2.2)
    # simple PSV drawing without registry
    reg, C.reg = C.reg, None
    C.psv(x + 15, yy + 24, "PSV-NNNN", 3.5, "1 x P", up=14, out="r", outlen=14, dest="", text_side=-1)
    C.opc(x + 30, yy + 40, "r", "TO / FROM ITEM", "CFU-AAA-PR-PID-NNN")
    t("OFF-PAGE CONNECTOR (FLOW DIRECTION, DRAWING No.)", x + 66, yy + 41, 2.2)
    C.reg = reg
    # column 2: instruments
    x2, y = 300.0, 30.0
    t("INSTRUMENT SYMBOLS (ISA-5.1)", x2, y, 3.0, bold=True)
    reg, C.reg = C.reg, None
    syms = [("field", "TT-1234", "FIELD-MOUNTED INSTRUMENT"), ("panel", "HS-1234", "LOCAL PANEL / CCR HARDWIRED (DISCRETE)"),
            ("dcs", "FIC-1234", "DCS SHARED DISPLAY / CONTROL (BPCS)"), ("sis", "LZHH-1234", "SIS FUNCTION (SAFETY PLC)"),
            ("plc", "UZ-1234", "PLC / PACKAGE CONTROL")]
    for i, (k, tg, lbl) in enumerate(syms):
        yy = y + 14 + i * 15
        C.bub(x2 + 8, yy, tg, k)
        t(lbl, x2 + 20, yy + 0.8, 2.2)
    yy = y + 14 + len(syms) * 15
    C.ilk(x2 + 8, yy, "")
    t("INTERLOCK / SIF (TAG SIF-NNN SHOWN ADJACENT)", x2 + 20, yy + 0.8, 2.2)
    C.reg = reg
    y = yy + 16
    t("INSTRUMENT IDENTIFICATION LETTERS", x2, y, 3.0, bold=True)
    letters = ["A  ANALYSIS (O2, pH)        B  BURNER / FLAME", "F  FLOW                     H  HAND",
               "L  LEVEL                    P  PRESSURE", "T  TEMPERATURE              X/Z  ON-OFF / POSITION",
               "PD / TD  DIFFERENTIAL       FF  FLOW RATIO", "Succeeding: E element, G glass, I indicate, C control,",
               "T transmit, V valve, Y relay/compute, S switch, Z (2nd) SIS,", "AH/AL/AHH/ALL alarms; A/B/C suffix = redundant SIS"]
    for i, s_ in enumerate(letters):
        t(s_, x2, y + 6 + i * 3.6, 2.2)
    y = y + 6 + len(letters) * 3.6 + 8
    t("ABBREVIATIONS", x2, y, 3.0, bold=True)
    abbr = ["FC / FO / FL  FAIL CLOSED / OPEN / LAST", "CSO / CSC  CAR-SEALED OPEN / CLOSED", "NC / NO  NORMALLY CLOSED / OPEN",
            "NNF  NORMALLY NO FLOW", "TPA / MPA / BPA  TOP / MID / BOTTOM PUMPAROUND", "SS  STRIPPING STEAM",
            "DBB  DOUBLE BLOCK & BLEED", "ROSOV / EIV  REMOTE OPERATED SHUT-OFF VALVE", "COT / CIT  COIL OUTLET / INLET TEMP.",
            "RO  RESTRICTION ORIFICE", "FA  FLAME ARRESTOR", "OSBL  OUTSIDE BATTERY LIMITS", "BMS  BURNER MANAGEMENT SYSTEM",
            "2oo3  TWO-OUT-OF-THREE VOTING"]
    for i, s_ in enumerate(abbr):
        t(s_, x2, y + 6 + i * 3.6, 2.2)
    # column 3: line numbering, fluids, insulation, classes
    x3, y = 520.0, 30.0
    t("LINE NUMBER", x3, y, 3.0, bold=True)
    t('12"-P-100-002-B1-H', x3, y + 9, 3.0, bold=True)
    expl = ['NPS (in)  -  FLUID  -  AREA  -  SEQUENCE  -  PIPING CLASS  -  INSULATION',
            "AREA: 100 CDU, 200 VDU, 900 UNIT UTILITIES"]
    for i, s_ in enumerate(expl):
        t(s_, x3, y + 15 + i * 3.6, 2.2)
    y = 62.0
    t("FLUID CODES", x3, y, 3.0, bold=True)
    for i, (k, v) in enumerate(PD.SHORT_FLUID.items()):
        t(f"{k:4s} {v}", x3 + (0 if i < 9 else 80), y + 6 + (i % 9) * 3.6, 2.2)
    y = 105.0
    t("INSULATION CODES", x3, y, 3.0, bold=True)
    for i, s_ in enumerate(["H  HEAT CONSERVATION", "P  PERSONNEL PROTECTION", "ST STEAM TRACED + INSULATED",
                            "C  COLD", "N  NONE"]):
        t(s_, x3, y + 6 + i * 3.6, 2.2)
    y = 132.0
    t("PIPING CLASSES (SUMMARY, SEE CFU-000-PI-SPC-001)", x3, y, 3.0, bold=True)
    for i, (k, c) in enumerate(PD.CLASSES.items()):
        t(f"{k}  {c['rating']}#  {c['mat'][:40]}", x3, y + 6 + i * 3.6, 2.1)
        t(c["svc"][:62], x3 + 105, y + 6 + i * 3.6, 2.1)
    y = 185.0
    t("DRAWING INDEX", x3, y, 3.0, bold=True)
    for i, (sq, ar, ttl) in enumerate(PD.SHEETS):
        t(PD.dwg(sq), x3, y + 6 + i * 3.6, 2.2, bold=True)
        t(ttl, x3 + 44, y + 6 + i * 3.6, 2.2)
    y = 260.0
    t("EQUIPMENT DATA BOX", x3, y, 3.0, bold=True)
    C.eqbox(x3, y + 4, 70, ["Service", "Size / rating", "DESIGN P barg / T C; CA", "DUTY / MOTOR", "MAT'L"], "TAG")
    # equipment symbols
    x4, y4 = 300.0, 330.0
    t("EQUIPMENT SYMBOLS", x4, y4, 3.0, bold=True)
    C.pump(x4 + 10, y4 + 20, None)
    t("CENTRIFUGAL PUMP (A/B 2x100 %)", x4 + 22, y4 + 21, 2.2)
    C.hx(x4 + 20, y4 + 42)
    t("SHELL & TUBE EXCHANGER", x4 + 42, y4 + 43, 2.2)
    C.kettle(x4 + 20, y4 + 68)
    t("KETTLE REBOILER / STEAM GENERATOR", x4 + 45, y4 + 66, 2.2)
    C.aircooler(x4 + 3, y4 + 84, 34, 8, 2)
    t("AIR COOLER (FANS, MOTORS)", x4 + 45, y4 + 89, 2.2)
    C.ejector(x4 + 5, y4 + 118, 26)
    t("STEAM EJECTOR", x4 + 45, y4 + 119, 2.2)
    C.fan(x4 + 15, y4 + 134)
    t("FAN (FD / ID)", x4 + 45, y4 + 135, 2.2)
    C.package(x4 + 3, y4 + 145, 30, 12, "X-NNN")
    t("VENDOR PACKAGE", x4 + 45, y4 + 152, 2.2)
    x5 = 540.0
    C.column(x5, y4 + 15, y4 + 75, 22)
    col_trays(C, x5, 22, {1: y4 + 25, 2: y4 + 37, 3: y4 + 49})
    C.bed(x5, 22, y4 + 55, y4 + 70)
    t("COLUMN: TRAYS (NUMBERED, DOWNCOMER), PACKED BED", x5 + 16, y4 + 40, 2.2)
    C.hdrum(x5 - 15, y4 + 95, 40, 14, boot=(x5 + 15, 6, 8))
    t("HORIZONTAL DRUM WITH BOOT", x5 + 32, y4 + 102, 2.2)
    heater_box(C, x5 - 15, y4 + 125, x5 + 25, y4 + 155, "", cells=1, burners=4)
    coil(C, x5 - 10, x5 + 20, y4 + 138, n=8)
    t("FIRED HEATER (COIL, FLOOR BURNERS)", x5 + 32, y4 + 140, 2.2)
    return save(C)

# ============================================================================= exports
def _nice(x):
    if x <= 0:
        return 1
    import math
    e = 10 ** math.floor(math.log10(x))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * e >= x:
            return round(m * e, 6)
    return 10 * e


VALVE_LET = re.compile(r"^(FV|TV|PV|LV|PDV|AV|KV|HV)$")


def inst_record(tag, d):
    letters, num = tag.split("-", 1)
    base = re.sub(r"[A-Z]$", "", num)
    loopnum = base.split("-")[0]
    loop = None if letters in ("PSV", "TSV", "GD", "BE") or d.get("sys") == "F&G" and letters == "HS" else next((l for l in C_.LOOPS if l.split("-")[1] == loopnum), None)
    kind = d["kind"]
    if not d.get("line") and loop and REG.inst_.get(loop, {}).get("line"):
        d = dict(d, line=REG.inst_[loop]["line"])
    sys = d.get("sys")
    if not sys:
        if letters in ("PSV", "TSV", "PCV", "LG", "FE", "FO", "ST") or (kind == "field" and letters in ("PI", "TI")):
            sys = "Local"
        elif letters == "GD":
            sys = "F&G"
        else:
            sys = "DCS"
    # signal
    if letters in ("PSV", "TSV", "PCV", "LG", "FE", "ST") or (sys == "Local"):
        sig = "- (local / mechanical)"
    elif letters in ("UZ",) or d.get("note", "") and "DCS soft" in (d.get("note") or ""):
        sig = "-" if letters == "UZ" else "Soft (DCS function block)"
    elif letters in ("XV", "EIV", "HV"):
        sig = "DO 24 VDC (SOV) + 2 x DI (ZSO/ZSC)"
    elif letters in ("HS", "BS", "ZSC", "ZSO", "BY", "XA"):
        sig = "DI 24 VDC"
    elif letters in ("XY", "LY"):
        sig = "DO 24 VDC (interposing relay)"
    elif letters in ("FY", "TY", "PY") or VALVE_LET.match(letters):
        sig = "4-20 mA HART AO (smart positioner)" if VALVE_LET.match(letters) else "4-20 mA AO"
    elif letters in ("GD", "BE"):
        sig = "4-20 mA (F&G)"
    elif kind in ("dcs", "sis") and not letters.endswith("T") and letters not in ("TI", "PI", "PDI", "FI", "AI"):
        sig = "Soft (DCS function block)" if sys == "DCS" else "Soft (SIS logic)"
    elif sys == "SIS":
        sig = "4-20 mA HART (SIS AI)"
    else:
        sig = "4-20 mA HART"
    # range
    rng, units = "", ""
    ln = REG.lines.get(d.get("line")) if d.get("line") else None
    m = letters[0] if letters[:2] not in ("PD", "TD", "FF") else letters[:2]
    if VALVE_LET.match(letters) or letters in ("XV", "EIV", "HS", "XY", "LY", "FY", "TY", "PY", "ZSC", "BY",
                                                 "PCV", "FE", "ST", "UZ", "FFY", "HV"):
        pass
    elif letters in ("PSV", "TSV"):
        pv = C_.PSV.get(tag) or (C_.PSV.get("TSV-typ") if letters == "TSV" else None)
        rng, units = (f"Set {pv['set_barg']} ", "barg") if pv else ("", "")
    elif m == "F":
        if ln:
            if ln["phase"] in ("L",) and ln["rho_kg_m3"] > 300:
                rng, units = f"0-{_nice(1.3 * ln['flow_kg_h'] / ln['rho_kg_m3']):g}", "m3/h"
            else:
                rng, units = f"0-{_nice(1.3 * ln['flow_kg_h']):g}", "kg/h"
        else:
            rng, units = "0-100", "%"
    elif m == "FF":
        rng, units = "0-2", "ratio"
    elif m == "T" or m == "TD":
        T = ln["op_T_C"] if ln else 300
        rng, units = (f"0-{_nice(max(T * 1.3, T + 50)):g}", "C") if m == "T" else ("-50-50", "C")
    elif m == "PD":
        rng, units = "0-2.5", "bar"
    elif m == "P":
        P = ln["op_P_barg"] if ln else 3.0
        if ln and P < 0:
            rng, units = "0-1100", "mbar(a)"
        else:
            rng, units = f"0-{_nice(max(P * 1.5, P + 2, 1)):g}", "barg"
        if "SIF-105" == d.get("sif") or tag.startswith(("PT-1023", "PIC-1023", "PZHH-1029")):
            rng, units = "-25-25", "mmH2O"
    elif m == "L":
        rng, units = "0-100", "%"
    elif m == "A":
        rng, units = ("0-14", "pH") if "pH" in (d.get("svc") or "") or tag.endswith("1037") else ("0-10", "vol% O2")
        if letters == "GD":
            rng, units = "0-100", "% LEL"
    elif letters == "GD":
        rng, units = ("0-50", "ppm H2S") if "H2S" in (d.get("svc") or "") else ("0-100", "% LEL")
    elif letters == "BE":
        rng, units = "Fire / no fire", "-"
    elif letters == "XA":
        rng, units = "Alarm", "-"
    elif m == "B":
        rng, units = "Flame ON/OFF", "-"
    if tag in IC_RNG:
        rng, units = IC_RNG[tag]
    sif = d.get("sif")
    svc = d.get("svc") or (C_.LOOPS[loop]["service"] if loop else "")
    return dict(tag=tag, type=PD.inst_type(tag), loop=loop or f"{letters}-{num}", service=svc,
                pid_sheet=", ".join(d["sheets"]), system=sys, signal=sig, range=rng, units=units,
                fail_position=d.get("fail") or "", sif=sif or "", sil_ref=C_.SIFS[sif]["sil"] if sif else "",
                line_no=ln["line_no"] if ln else "", note=d.get("note") or "",
                location=(d.get("note") or "")[5:] if (d.get("note") or "").startswith("Loc. ") else "")


def checks():
    msgs = []
    for k, ln in REG.lines.items():
        if not ln["sheets"]:
            msgs.append(f"line {k} ({ln['line_no']}) not drawn on any P&ID")
    for lp, l in C_.LOOPS.items():
        if lp not in REG.inst_:
            msgs.append(f"principal loop {lp} not shown")
            continue
        tt, ct, fv = loop_tags(lp)
        num = lp.split("-")[1]
        has_t = any(t.split("-")[1] == num and t.split("-")[0].endswith("T") for t in REG.inst_)
        if not has_t and not lp.startswith(("FFIC", "TDIC")) and lp != "FIC-1090":
            msgs.append(f"loop {lp}: no transmitter")
        if fv and fv not in REG.inst_:
            msgs.append(f"loop {lp}: final element {fv} missing")
    for sf, d in C_.SIFS.items():
        if not any(i.get("sif") == sf for i in REG.inst_.values()):
            msgs.append(f"{sf}: no instruments")
    for t in ("XV-1021", "XV-1022", "XV-1026", "XV-1001", "XV-1093", "XV-1096", "XV-2006A", "XV-2006B", "XV-1083",
              "EIV-1121", "EIV-2041", "LT-1007B", "LT-1008B", "LT-1082B", "LT-1092B", "PT-1091B", "LT-2024B",
              "BS-1028", "BS-2008", "HS-9000", "PT-1027A", "PT-1029A", "TT-1020A", "PT-2009A", "FT-1011A", "FT-2001A"):
        if t not in REG.inst_:
            msgs.append(f"SIF element {t} missing")
    return msgs


def _xl_sheet(ws, title, docno, headers, rows, widths):
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"{docno}   Rev A - Issued for review (FEED)   2026-10-02   100 kBPSD CDU/VDU"
    hdr_row = 4
    thin = Side(style="thin", color="999999")
    for j, h in enumerate(headers, 1):
        c = ws.cell(row=hdr_row, column=j, value=h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3864")
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
    for i, r in enumerate(rows, hdr_row + 1):
        for j, v in enumerate(r, 1):
            ws.cell(row=i, column=j, value=v)
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=hdr_row, column=j).column_letter].width = w
    ws.freeze_panes = ws.cell(row=hdr_row + 1, column=3)
    ws.auto_filter.ref = f"A{hdr_row}:{ws.cell(row=hdr_row, column=len(headers)).column_letter}{hdr_row + len(rows)}"


def export():
    from openpyxl import Workbook
    # ---- lines
    lines = []
    for k, l in REG.lines.items():
        if not l["sheets"]:
            continue
        issues = [m.split(": ", 1)[1] for m in REG.issues if m.startswith(l["line_no"] + ":")]
        lines.append(dict(line_no=l["line_no"], size_in=l["size_in"], fluid=l["fluid"], area=l["area"],
                          seq=l["seq"], cls=l["cls"], insul=l["insul"], **{"from": l["frm"]}, to=l["to"],
                          service=l["service"], phase=l["phase"], design_P_barg=l["design_P_barg"],
                          design_T_C=l["design_T_C"], op_P_barg=l["op_P_barg"], op_T_C=l["op_T_C"],
                          flow_kg_h=l["flow_kg_h"], density_kg_m3=l["rho_kg_m3"], velocity_m_s=l["velocity_m_s"],
                          sizing_basis=l["kind"], pid_sheet=", ".join(l["sheets"]), stream_no=l["stream_no"],
                          remarks="; ".join([x for x in [l["note"]] + issues if x])))
    lines.sort(key=lambda r: (r["area"], r["seq"]))
    (ROOT / "data" / "lines.json").write_text(json.dumps(lines, indent=1))
    wb = Workbook()
    ws = wb.active
    ws.title = "Line List"
    hd = ["Line No.", "NPS (in)", "Fluid", "Area", "Seq", "Class", "Insul.", "From", "To", "Service", "Phase",
          "Des. P (barg)", "Des. T (C)", "Op. P (barg)", "Op. T (C)", "Flow (kg/h)", "Density (kg/m3)",
          "Velocity (m/s)", "Sizing basis", "P&ID", "H&MB stream", "Remarks"]
    rows = [[r["line_no"], r["size_in"], r["fluid"], r["area"], r["seq"], r["cls"], r["insul"], r["from"], r["to"],
             r["service"], r["phase"], r["design_P_barg"], r["design_T_C"], r["op_P_barg"], r["op_T_C"],
             r["flow_kg_h"], r["density_kg_m3"], r["velocity_m_s"], r["sizing_basis"], r["pid_sheet"],
             r["stream_no"], r["remarks"]] for r in lines]
    _xl_sheet(ws, "LINE LIST", "CFU-000-PI-LL-001", hd, rows,
              [24, 7, 6, 6, 5, 6, 6, 22, 22, 44, 6, 9, 9, 9, 9, 11, 10, 9, 10, 22, 8, 50])
    ws2 = wb.create_sheet("Sizing Criteria")
    crit = [[k, v, "m/s max"] for k, v in PD.VMAX.items()] + \
           [["vapour", "min(25, sqrt(15000/rho))", "rho.v2 <= 15 kPa"], ["steam", "min(30, sqrt(30000/rho))", ""]]
    _xl_sheet(ws2, "LINE SIZING CRITERIA", "CFU-000-PI-LL-001", ["Basis", "Velocity limit", "Note"], crit, [14, 28, 30])
    out = ROOT / "deliverables" / "03-layout-piping"
    out.mkdir(parents=True, exist_ok=True)
    wb.save(out / "CFU-000-PI-LL-001_Line-List.xlsx")
    # ---- instruments
    recs = sorted((inst_record(t, d) for t, d in REG.inst_.items()),
                  key=lambda r: (re.sub(r"\D", "", r["tag"].split("-")[1])[:4], r["tag"]))
    (ROOT / "data" / "instruments.json").write_text(json.dumps(recs, indent=1))
    wb = Workbook()
    ws = wb.active
    ws.title = "Instrument Index"
    hd = ["Tag", "Type", "Loop", "Service", "P&ID", "System", "Signal", "Range", "Units", "Fail pos.", "SIF",
          "SIL", "Line No.", "Location (plot plan)", "Note"]
    rows = [[r["tag"], r["type"], r["loop"], r["service"], r["pid_sheet"], r["system"], r["signal"], r["range"],
             r["units"], r["fail_position"], r["sif"], r["sil_ref"], r["line_no"], r["location"], r["note"]]
            for r in recs]
    _xl_sheet(ws, "INSTRUMENT INDEX", "CFU-000-IC-IDX-001", hd, rows,
              [13, 30, 11, 46, 20, 8, 30, 12, 9, 7, 8, 6, 24, 34, 30])
    ws2 = wb.create_sheet("SIF List")
    srows = []
    for sf, d in C_.SIFS.items():
        ins = sorted(r["tag"] for r in recs if r["sif"] == sf)
        srows.append([sf, d["function"], d["sil"], d["initiators"], d["final_elements"], ", ".join(ins)])
    _xl_sheet(ws2, "SAFETY INSTRUMENTED FUNCTIONS", "CFU-000-IC-IDX-001",
              ["SIF", "Function", "SIL", "Initiators", "Final elements", "Instrument tags on P&IDs"], srows,
              [9, 50, 6, 30, 32, 70])
    ws3 = wb.create_sheet("Summary")
    from collections import Counter
    cnt = Counter(r["system"] for r in recs)
    _xl_sheet(ws3, "SUMMARY", "CFU-000-IC-IDX-001", ["System", "Count"], [[k, v] for k, v in sorted(cnt.items())] +
              [["TOTAL", len(recs)]], [14, 10])
    out = ROOT / "deliverables" / "04-instrumentation"
    out.mkdir(parents=True, exist_ok=True)
    wb.save(out / "CFU-000-IC-IDX-001_Instrument-Index.xlsx")
    # ---- piping class summary
    used = {}
    for r in lines:
        used.setdefault(r["cls"], []).append(r)
    wb = Workbook()
    ws = wb.active
    ws.title = "Classes"
    hd = ["Class", "Rating", "Material", "B16.5 group", "CA (mm)", "Service", "Max service T (C)", "Flanges",
          "Valves", "Gaskets", "Bolting", "Branch", "Pipe schedule", "Lines on P&IDs", "Max des. P (barg)",
          "Max des. T (C)"]
    rows = []
    for k, c in PD.CLASSES.items():
        u = used.get(k, [])
        rows.append([k, f"{c['rating']}#", c["mat"], c["grp"], c["ca"], c["svc"], c["tmax"], c["flange"], c["valves"],
                     c["gasket"], c["bolting"], c["branch"], c["sch"], len(u),
                     max((x["design_P_barg"] for x in u), default=""), max((x["design_T_C"] for x in u), default="")])
    _xl_sheet(ws, "PIPING CLASS SUMMARY", "CFU-000-PI-SPC-001", hd, rows,
              [6, 7, 34, 8, 7, 42, 10, 18, 40, 34, 22, 26, 24, 9, 10, 10])
    ws2 = wb.create_sheet("P-T Ratings")
    hd2 = ["Class", "Rating", "Group"] + [f"{t} C" for t in PD._T]
    rows2 = [[k, f"{c['rating']}#", c["grp"]] + PD.RATINGS[(c["grp"], c["rating"])] for k, c in PD.CLASSES.items()]
    _xl_sheet(ws2, "PRESSURE-TEMPERATURE RATINGS, barg (ASME B16.5-2020 Table 2, FEED transcription - verify)",
              "CFU-000-PI-SPC-001", hd2, rows2, [7, 7, 7] + [7] * len(PD._T))
    ws3 = wb.create_sheet("Rating Exceptions")
    _xl_sheet(ws3, "LINES WHOSE DESIGN CONDITIONS EXCEED CLASS RATING (FOR RESOLUTION)", "CFU-000-PI-SPC-001",
              ["Line / issue"], [[m] for m in REG.issues], [120])
    out = ROOT / "deliverables" / "03-layout-piping"
    wb.save(out / "CFU-000-PI-SPC-001_Piping-Class-Summary.xlsx")
    md = ["# CFU-000-PI-SPC-001 Piping Class Summary (Rev A, FEED)", "",
          "100 kBPSD Crude & Vacuum Distillation Unit. Classes per CONVENTIONS.md; P-T ratings per ASME B16.5-2020 "
          "Table 2 (FEED transcription, verify at detailed design). Workbook: `CFU-000-PI-SPC-001_Piping-Class-Summary.xlsx`.",
          "", "| Class | Rating | Material | CA mm | Service | Valves | Gaskets / bolting | Lines | Max des. P/T |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[4]} | {r[5]} | {r[8]} | {r[9]}; {r[10]} | {r[13]} | "
                  f"{r[14]} barg / {r[15]} C |")
    md += ["", "## Pressure-temperature ratings (barg)", "",
           "| Class | " + " | ".join(f"{t} C" for t in PD._T) + " |", "|---" * (len(PD._T) + 1) + "|"]
    for r in rows2:
        md.append(f"| {r[0]} ({r[1]}) | " + " | ".join(f"{v:g}" for v in r[3:]) + " |")
    md += ["", "## Rating exceptions flagged by the line list", ""] + [f"- {m}" for m in REG.issues] + \
          ["", "Branch connections per ASME B31.3 branch table; vents/drains 3/4\" min. (1\" in B2/B3); "
               "PWHT for A2, B2, B3, S2 per class; spec breaks shown on P&IDs at class changes."]
    (out / "CFU-000-PI-SPC-001_Piping-Class-Summary.md").write_text("\n".join(md) + "\n")
    return lines, recs

# ============================================================================= build
def build():
    global C_, REG
    C_ = PD.Ctx()
    REG = PD.Registry(C_)
    PD.build_lines(REG)
    pdfs = []
    for fn in SHEET_FUNCS:
        pdfs.append(fn())
    merge_pdfs(pdfs, OUT / "CFU-000-PR-PID-ALL.pdf")
    add_ic_soft()
    add_fg_devices()
    for m in checks():
        print("  P&ID CHECK:", m)
    lines, recs = export()
    print(f"  P&IDs: {len(pdfs)} sheets, {len(lines)} lines, {len(recs)} instruments, "
          f"{len(REG.issues)} class-rating exceptions")
    return pdfs


SHEET_FUNCS = [sheet_000, sheet_001, sheet_002, sheet_003, sheet_004, sheet_005, sheet_006, sheet_007, sheet_008, sheet_009, sheet_010, sheet_011, sheet_012, sheet_013, sheet_014, sheet_015, sheet_016]

if __name__ == "__main__":
    build()
