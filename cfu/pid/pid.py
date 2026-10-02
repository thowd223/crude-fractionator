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
        "Crude-side design pressure 30 barg (= PSV-1010 set) for P-101 discharge system to D-101A inlet.",
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
        ("E-105", 680, "crude_c5", "vr_c1", "vr_c2", ("FROM E-111", 3), ("TO E-201", 14), "tube", None),
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
    # P-102 discharge
    yd = pp["dr"][1]
    C.line("p102_d", [pp["dr"], (795, yd)], lab=0, at=0.5, arrow=False)
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
        C.lab(REG.no(k), xy=(x0 + 77, yt - 13.5))
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
           lab=3, at=0.3)
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
        "Hot train crude-side design pressure per P-102 shut-off (see line list); exchanger rating to be confirmed.",
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
        ("E-111", 625, "crude_h6", "vr_pd", "vr_c1", ("FROM P-204A/B", 13), ("TO E-105", 1), "tube", N4),
    ]
    C.opc(50, yh, "l", "FROM P-102A/B", dref(2))
    out, info = train(C, cells, ye, yh, yu, yl, prev_out=(50, yh), prev_key="p102_d")
    C.hop(info["E-110"]["h_out"][0], yh, "h")
    C.line("crude_h6", [out, (790, yh)], lab=0, at=0.55)
    C.opc(790, yh, "r", "TO H-101", dref(4))
    ti(C, 760, yh - 20, [(760, yh), (760, yh - 15.4)], svc="CIT - crude to H-101", line="crude_h6")
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
    C.line("ms_e113", [sv, (sv[0], 330), (650, 330)], lab=1, at=0.25)
    C.opc(650, 330, "r", "TO MP STEAM HDR", dref(16))
    C.station(588, 330, 632, 330, "PV-1111", "FO", byp=1, side=-1, tag_pos=(613.5, 324))
    ctrl(C, "PIC-1111", 580, 312, 610, 300, tap=[(580, 330), (580, 316.6)],
         sig=[(584.6, 312), (595, 312), (595, 300), (605.4, 300)], vsig=[(610, 304.6), (610, 320.2)],
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
    C.line("crude_h6", [(50, 120), (xm, 120), (xm, ys[-1])], lab=0, at=0.5, arrow=False)
    ti(C, 70, 103, [(70, 120), (70, 107.6)], svc="H-101 inlet temperature (CIT)", line="crude_h6")
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
def sif_block(C, x0, y0, w, sifs):
    h = 10 + 14 * len(sifs)
    C.g_eq.add(C.d.rect((x0, y0), (w, h), stroke_width=0.5))
    C.t("H-101 BMS / SIS (SIL-RATED PLC)", x0 + w / 2, y0 + 5, 2.3, "middle", bold=True)
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
    C.bub(560, 368, "BS-1028", "field", svc="H-101 flame scanners (1 per burner, 16 off)")
    C.tap([(560, Y1 + 15), (560, 363.4)])
    C.bub(585, 368, "BZLL-1028", "sis", sys="SIS", sif="SIF-104", svc="Loss of flame (all burners)")
    C.sig([(564.6, 368), (580.4, 368)], "e")
    C.t("TO SIF-104", 591, 369, 2.0)
    # snuffing steam
    C.opc(790, 290, "r", "LP STEAM HEADER", dref(16), flow="in")
    C.line("ls_snuff_h101", [(790, 290), (700, 290), (700, 250), (X1, 250)], lab=0, at=0.5)
    C.pipe([(700, 290), (X1, 290)], util=True)
    C.gate(760, 290, "h", note="SNUFFING")
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
        REG.inst(free_tag(C, "ZSC"), C.sid, sys="SIS", svc=f"Closed limit switch on XV-{xx}")
    C.station(185, yf, 230, yf, "PV-1021", "FC", byp=1, tag_pos=(211, yf - 6))
    ctrl(C, "PIC-1021", 255, yf - 18, 230, yf - 30, tap=[(255, yf), (255, yf - 13.4)], line="fg_h101_b",
         sig=[(250.4, yf - 18), (240, yf - 18), (240, yf - 30), (234.6, yf - 30)],
         vsig=[(225.4, yf - 30), (207.5, yf - 30), (207.5, yf - 10.8)], fail="FC")
    C.t("SP FROM TIC-1020", 225, yf - 40, 2.0, "end")
    C.t(f"({dref(4)})", 225, yf - 37.4, 2.0, "end")
    C.line("fg_h101_b", [(275, yf), (455, yf), (455, 360), (X1 - 4, 360)], lab=0, at=0.55, arrow=False)
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
        C.t(f"STREAM {strm}", x0 + 194, yr + 9, 2.0, "middle")
    return save(C)


# ============================================================================= SHEET 009
def sheet_009():
    C = new_sheet(9, [
        "Neutraliser and filming amine injected upstream of A-101; pH control AIC-1037 trims FFIC-1036.",
        "PIC-1032 split range: 0-50 % PV-1032B (FG make-up) closing, 50-100 % PV-1032A (off-gas) opening.",
        "SIF-109 initiator / final element per SRS: LT-1033B high-high closes XV-1034 (see data issue log).",
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
    sis_initiator(C, ["LT-1033B"], xr + 15, dy0 + 30, "LZHH-1033", "SIF-109", xr + 40, dy0 + 30, 0, 0,
                  tap=[(xr - 3, dy0 + 22), (xr + 2, dy0 + 22), (xr + 2, dy0 + 30), (xr + 10.4, dy0 + 30)])
    C.ilk(xr + 62, dy0 + 30, "SIF-109")
    C.sig([(xr + 44.6, dy0 + 30), (xr + 58, dy0 + 30)], "e")
    C.t("TO XV-1034", xr + 67, dy0 + 31, 2.0)
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
    # naphtha -> FV-1034 -> XV-1034 -> E-114
    ynp = 270.0
    C.line("naph_d", [p4["dr"], (705, p4["dr"][1]), (705, ynp), (795, ynp)], lab=2, at=0.5)
    C.opc(795, ynp, "r", "TO E-114 / C-105", dref(10))
    C.orifice(705, 285, "v")
    REG.inst("FE-1034", C.sid, svc="Unstabilised naphtha flow element", line="naph_d")
    C.station(712, ynp, 756, ynp, "FV-1034", "FC", byp=-1, side=1, tag_pos=(738, ynp + 9))
    ctrl(C, "FIC-1034", 722, 292, 745, 292, tap=[(707, 285), (722, 285), (722, 287.4)], line="naph_d",
         vsig=[(745, 287.4), (745, 280), (734, 280), (734, 277)], fail="FC")
    C.xv(772, ynp, "h", "XV-1034", "FC", tag_pos=(766, ynp - 9))
    REG.inst("XV-1034", C.sid, sys="SIS", sif="SIF-109", fail="FC", svc=C_.SIFS["SIF-109"]["function"])
    C.sig([(xr + 62, dy0 + 34), (xr + 62, 255), (772, 255), (772, ynp - 9.8)], "e")
    C.bub(686, 395, "FIC-1090", "dcs", svc=C_.LOOPS["FIC-1090"]["service"] + " (shares FT/FV-1034)",
          loop="FIC-1090")
    C.t("= FIC-1034 (SHARED)", 692, 396, 2.0)
    return save(C)

# ============================================================================= build
def build():
    global C_, REG
    C_ = PD.Ctx()
    REG = PD.Registry(C_)
    PD.build_lines(REG)
    pdfs = []
    for fn in SHEET_FUNCS:
        pdfs.append(fn())
    return pdfs


SHEET_FUNCS = [sheet_001, sheet_002, sheet_003, sheet_004, sheet_005, sheet_006, sheet_007, sheet_008, sheet_009]

if __name__ == "__main__":
    build()
