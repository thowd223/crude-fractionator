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
    label = tags[0] if len(tags) == 1 else tags[0][:-1] + "/".join(t[-1] for t in tags)
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


SHEET_FUNCS = [sheet_001, sheet_002, sheet_003]

if __name__ == "__main__":
    build()
