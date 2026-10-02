"""Single-line diagrams CFU-000-EL-SLD-001..004 (A1, IEC 60617 / IEEE 315 symbols, ANSI C37.2 device numbers)."""
from __future__ import annotations

from pathlib import Path

from ..drawing.sheet import Sheet, merge_pdfs
from . import common as C
from .loads import B4, B13, BLV, BUPS
from .symbols import Pen

DISC = "ELECTRICAL"


def put_notes(sh, notes, width=100):
    """Like Sheet.notes but wraps long notes; continuation lines (and entries starting with two spaces)
    are not numbered."""
    lines = []
    n = 0
    for t in notes:
        cont = t.startswith("  ")
        if not cont:
            n += 1
        words, cur, first = t.strip().split(), "", True
        for w in words:
            if len(cur) + len(w) + 1 > width - 4:
                lines.append((None if (cont or not first) else n, cur))
                cur, first = "", False
            cur = (cur + " " + w).strip()
        lines.append((None if (cont or not first) else n, cur))
    d = sh.dwg
    x0 = sh._tb[0]
    lh = 3.6
    y = sh._notes_bottom - lh * (len(lines) + 1)
    from ..drawing.sheet import FONT
    g = d.g(font_family=FONT, font_size=2.5, fill="black")
    g.add(d.text("NOTES", insert=(x0, y), font_weight="bold", font_size=3.0))
    for i, (num, t) in enumerate(lines):
        g.add(d.text((f"{num}. " if num else "    ") + t, insert=(x0, y + lh * (i + 1))))
    d.add(g)
    sh._notes_bottom = y - 3


def _f(x, n=0):
    return f"{x:,.{n}f}"


# --------------------------------------------------------------------------------------------- legend
def legend(p: Pen, x, y, w=330, rows=2):
    p.rect(x, y, w, 62 if rows == 2 else 34, lw=0.3, fill="white")
    p.text("LEGEND (IEC 60617 / IEEE 315; device numbers ANSI/IEEE C37.2)", x + 2, y + 4.2, 2.3, bold=True)
    items = [
        ("cb", "Circuit breaker, drawout (VCB / ACB)"),
        ("mccb", "MCCB (fixed, in MCC bucket)"),
        ("cont", "Contactor"),
        ("ol", "Thermal overload relay"),
        ("tx", "Two-winding transformer (D / Y)"),
        ("m", "Induction motor"),
        ("vfd", "Variable frequency drive"),
        ("ct", "Current transformer / ZSCT"),
        ("vt", "Voltage transformer (fused)"),
        ("rel", "Protective relay function (MPR)"),
        ("fuse", "Fuse"),
        ("gnd", "Ground / NGR"),
    ]
    per = 6
    cw = w / per
    for i, (k, t) in enumerate(items):
        cx = x + 8 + (i % per) * cw
        cy = y + 9 + (i // per) * 27
        if k == "cb":
            p.breaker(cx, cy)
        elif k == "mccb":
            p.breaker(cx, cy, drawout=False, s=0.8)
        elif k == "cont":
            p.breaker(cx, cy, drawout=False, kind="contactor", s=0.8)
        elif k == "ol":
            p.overload(cx, cy + 2)
        elif k == "tx":
            p.transformer(cx, cy, r=3.2, h_lead=1.0)
        elif k == "m":
            p.motor(cx, cy + 2)
        elif k == "vfd":
            p.vfd(cx, cy, w=7, h=7, lead=1.5)
        elif k == "ct":
            p.line(cx, cy, cx, cy + 12)
            p.ct(cx, cy + 4)
            p.g.add(p.d.ellipse((cx, cy + 8.5), (2.4, 0.9), fill="none", stroke="black", stroke_width=0.3))
        elif k == "vt":
            p.vt(cx, cy, label="")
        elif k == "rel":
            p.relays(cx - 2.8, cy + 3, ["50/51"], cols=1)
        elif k == "fuse":
            p.fuse(cx, cy + 2)
        elif k == "gnd":
            p.line(cx, cy + 2, cx, cy + 4)
            p.rect(cx - 1, cy + 4, 2, 5)
            p.line(cx, cy + 9, cx, cy + 10)
            p.ground(cx, cy + 10)
        words = t.split(" ")
        ln, cur = [], ""
        for wd in words:
            if len(cur) + len(wd) > 17:
                ln.append(cur.strip())
                cur = ""
            cur += wd + " "
        ln.append(cur.strip())
        p.lines(ln, cx + 5.5, cy + 4.5, 1.9)


def table(p: Pen, x, y, cols, rows, title=None, size=2.3, rh=5.0, bold_last=False):
    """Simple ruled table; cols = [(header, width, align)]."""
    W = sum(c[1] for c in cols)
    if title:
        p.text(title, x, y - 1.5, 2.4, bold=True)
    n = len(rows) + 1
    p.rect(x, y, W, rh * n, lw=0.35, fill="white")
    p.rect(x, y, W, rh, lw=0.35, fill="#E8EDF5")
    for i in range(1, n):
        p.line(x, y + rh * i, x + W, y + rh * i, w=0.2)
    cx = x
    for j, (h, w, al) in enumerate(cols):
        if j:
            p.line(cx, y, cx, y + rh * n, w=0.2)
        tx = cx + 1 if al == "l" else cx + w - 1 if al == "r" else cx + w / 2
        anc = "start" if al == "l" else "end" if al == "r" else "middle"
        p.text(h, tx, y + rh - 1.2, size, anc, bold=True)
        for i, r in enumerate(rows):
            p.text(str(r[j]), tx, y + rh * (i + 2) - 1.2, size, anc, bold=bold_last and i == len(rows) - 1)
        cx += w
    return y + rh * n


# --------------------------------------------------------------------------------------------- SLD-001
def sld_001(ctx, out: Path):
    rows, R, cab = ctx["rows"], ctx["R"], ctx["cab"]
    trm, trl, sw = R["tr_mv"], R["tr_lv"], R["swgr"]
    notes = [
        "Normal operation: both incomers closed, bus ties NORMALLY OPEN (N.O.) at 13.8 kV, 4.16 kV and 480 V.",
        "Each transformer sized for the total unit maximum demand (one out of service, tie closed): "
        "ONAN >= MD, ONAF >= 1.25 x MD (25 % future). See CFU-000-EL-CAL-001.",
        "Tie breakers: 2-out-of-3 electrical/key interlock per board (no paralleling of transformers); "
        "auto-transfer (open transition) on loss of incomer, with residual-voltage supervision (27R).",
        "4.16 kV system low-resistance grounded (400 A); 480 V high-resistance grounded (5 A, alarm).",
        "Pump A/B (2 x 100 %) are always fed from opposite bus sections; the normally running unit of each "
        "pair is selected to balance the buses (load list CFU-000-EL-LDL-001).",
        "No emergency diesel generator: essential loads (DCS/SIS/F&G/telecom) on 2 x 100 % UPS, 30 min "
        "autonomy; unit fails safe on total power loss. See SLD-004 note 1.",
        "Detailed MV / LV / UPS SLDs: CFU-000-EL-SLD-002 / -003 (2 sheets) / -004.",
        "Short-circuit ratings: symmetrical interrupting kA; utility 31.5 kA at 13.8 kV (basis).",
    ]
    sh = Sheet("A1", "OVERALL KEY SINGLE LINE DIAGRAM", "13.8 / 4.16 / 0.48 kV DISTRIBUTION - SUBSTATION SS-100",
               "CFU-000-EL-SLD-001", discipline=DISC)
    put_notes(sh, notes)
    p = Pen(sh)

    def mirror(x):
        return 850 - x

    y13, y4, ylv = 118.0, 238.0, 352.0
    md = R["md"]
    for s in (0, 1):
        ab = "AB"[s]
        X = (lambda x: x) if s == 0 else mirror
        L = s == 0
        side = "left" if L else "right"
        oside = "right" if L else "left"
        bx1, bx2 = (24, 405) if L else (445, 826)
        lx, anc = (bx1, "start") if L else (bx2, "end")
        # ---------------- 13.8 kV
        p.bus(bx1, bx2, y13)
        p.bus_label(lx, y13, [f"SWG-101{ab}", "13.8 kV SWITCHGEAR",
                              f"3-ph, 60 Hz, {sw['SWG-101']['bus_A']} A",
                              f"{sw['SWG-101']['kA']:g} kA sym., 95 kV BIL"], anc)
        xi = X(95)
        p.lines(["FROM REFINERY MAIN", f"SUBSTATION - FEEDER {s + 1}"], xi, 30, 2.1, anchor="middle", bold_first=True)
        p.arrow_down(xi, 35, 6)
        p.line(xi, 41, xi, 62)
        c = cab[f"CBL-INC-{ab}"]
        p.cable_tag(xi, 50, c["cable"].split(" Cu")[0], side=oside, size=1.8)
        p.ct(xi, 66, "1200/5", side=side)
        p.line(xi, 62, xi, 64.7)
        p.line(xi, 67.3, xi, 76)
        _rel(p, xi, 66, ["50/51", "50N/51N", "67", "87L", "27", "86"], s, cols=3)
        p.breaker(xi, 76)
        p.text("52-I" + ab, xi + (3 if L else -3), 84, 2.0, "start" if L else "end")
        p.line(xi, 89, xi, y13)
        p.dot(xi, y13)
        # TR feeder
        xt = X(175)
        p.dot(xt, y13)
        p.breaker(xt, y13)
        p.line(xt, y13 + 13, xt, y13 + 32)
        p.ct(xt, y13 + 18, "400/5", side=side)
        p.cable_tag(xt, y13 + 27, cab[f"CBL-TR-10{s + 1}-P"]["cable"].split(" Cu")[0], side=side, size=1.8)
        _rel(p, xt, y13 + 18, ["50/51", "50N/51N", "87T", "63", "49T", "86T"], s, cols=3, dx=4)
        lbl = [f"TR-10{s + 1}", f"{trm['onan_kVA'] / 1000:g}/{trm['onaf_kVA'] / 1000:g} MVA ONAN/ONAF",
               "13.8/4.16 kV, Dyn1", f"Z = {trm['z_pct']:g} %, OCTC +/-2x2.5 %", "Oil-immersed, outdoor"]
        _, yb = p.transformer(xt, y13 + 32, r=7.0, ngr="NGR 400 A / 10 s", label=lbl,
                              label_x=xt - 10 if L else xt + 10)
        p.line(xt, yb, xt, y4 - 34)
        p.cable_tag(xt, y4 - 38, cab[f"CBL-TR-10{s + 1}-S"]["cable"].split(" Cu")[0], side=side, size=1.8)
        p.ct(xt, y4 - 29, "2000/5", side=side)
        p.line(xt, y4 - 34, xt, y4 - 30.3)
        p.line(xt, y4 - 27.7, xt, y4 - 22)
        _rel(p, xt, y4 - 29, ["51", "51G", "87T", "27", "86"], s, cols=3, dx=4)
        p.breaker(xt, y4 - 22)
        p.text("52-M" + ab, xt + (3 if L else -3), y4 - 14, 2.0, "start" if L else "end")
        p.line(xt, y4 - 9, xt, y4)
        p.dot(xt, y4)
        # spare + VT on 13.8
        xs = X(270)
        p.dot(xs, y13)
        p.breaker(xs, y13)
        p.line(xs, y13 + 13, xs, y13 + 18)
        p.text("SPARE (EQUIPPED)", xs, y13 + 21.5, 2.0, "middle")
        xv = X(350)
        p.dot(xv, y13)
        p.vt(xv, y13, "VT 14400-120 V")
        _rel(p, xv, y13 + 24, ["27", "59", "81"], 0, cols=3, dx=-8, link=False)
        # ---------------- 4.16 kV
        p.bus(bx1, bx2, y4)
        p.bus_label(lx, y4, [f"SWG-102{ab}", "4.16 kV SWITCHGEAR",
                             f"3-ph, 60 Hz, {sw['SWG-102']['bus_A']} A",
                             f"{sw['SWG-102']['kA']:g} kA sym., 60 kV BIL"], anc)
        mv = [r for r in rows if r["bus"] == B4[s]]
        mv.sort(key=lambda r: -r["rated_kw"])
        for i, r in enumerate(mv):
            xm = X(215 + 38 * i)
            p.dot(xm, y4)
            p.breaker(xm, y4)
            yy = y4 + 13
            if r["vfd"]:
                p.line(xm, yy, xm, yy + 6)
                _, yy = p.vfd(xm, yy + 6, w=8, h=8, lead=1.5)
                p.text(f"VFD-{r['tag']}", xm + (5 if L else -5), yy - 6, 1.8, "start" if L else "end")
            p.line(xm, yy, xm, y4 + 38)
            _, ym = p.motor(xm, y4 + 38, r=4.0)
            duty = {"C": "RUNNING", "S": "STANDBY", "I": "INTERMITTENT"}[r["duty"]]
            p.lines([r["tag"], f"{r['rated_kw']:g} kW", "VFD" if r["vfd"] else "DOL", duty], xm, ym + 4.5, 2.1,
                    anchor="middle", bold_first=True)
        # LV transformer feeder
        xl = X(95)
        p.dot(xl, y4)
        p.breaker(xl, y4)
        p.line(xl, y4 + 13, xl, y4 + 30)
        p.ct(xl, y4 + 18, "600/5", side=side)
        p.cable_tag(xl, y4 + 25, cab[f"CBL-TR-10{s + 3}-P"]["cable"].split(" Cu")[0], side=side, size=1.8)
        lbl = [f"TR-10{s + 3}", f"{trl['onan_kVA']:g}/{trl['onaf_kVA']:g} kVA ONAN/ONAF", "4.16/0.48 kV, Dyn1",
               f"Z = {trl['z_pct']:g} %"]
        _, yb = p.transformer(xl, y4 + 30, r=6.0, ngr="HRG 5 A", label=lbl, label_x=xl - 9 if L else xl + 9)
        p.line(xl, yb, xl, ylv - 24)
        p.text(f"BUS DUCT {C.std_up(trl['I_sec_onaf_A'], C.BUS_A)} A", xl + (2 if L else -2), ylv - 26,
               1.8, "start" if L else "end")
        p.breaker(xl, ylv - 22)
        p.text("52-L" + ab + " (ACB)", xl + (3 if L else -3), ylv - 14, 2.0, "start" if L else "end")
        p.line(xl, ylv - 9, xl, ylv)
        p.dot(xl, ylv)
        # spare + VT on 4.16
        xs = X(140)
        p.dot(xs, y4)
        p.breaker(xs, y4)
        p.line(xs, y4 + 13, xs, y4 + 18)
        p.text("SPARE", xs, y4 + 21.5, 2.0, "middle")
        xv = X(398)
        p.dot(xv, y4)
        p.vt(xv, y4, "")
        p.lines(["VT", "4200-120 V"], xv, y4 + 22, 1.8, anchor="middle")
        # ---------------- 480 V
        p.bus(bx1, bx2, ylv)
        p.bus_label(lx, ylv, [f"MCC-101{ab}", "480 V SWITCHGEAR / MCC",
                              f"3-ph, 60 Hz, {sw['MCC-101']['bus_A']} A", f"{sw['MCC-101']['kA']:g} kA sym."], anc)
        lv = [r for r in rows if r["bus"] == BLV[s]]
        dol = [r for r in lv if r["kind"] == "motor" and not r["vfd"]]
        vfd = [r for r in lv if r["vfd"]]
        dts = [r for r in lv if r["tag"].startswith("DT-")]
        misc = [r for r in lv if r["kind"] != "motor" and not r["tag"].startswith(("DT-", "UPS-", "BC-"))
                and r["volt"] != 208]
        groups = [
            ("mot", [f"{len(dol)} x LV MOTORS", f"DOL, {_f(sum(r['rated_kw'] for r in dol))} kW", "(connected)",
                     "SEE SLD-003"]),
            ("vfd", [f"{len(vfd)} x A-101 FANS", f"{vfd[0]['rated_kw']:g} kW each", "VFD"] if vfd else ["-"]),
            ("dt", [f"{len(dts)} x DESALTER TX", "150 kVA, 480 V /", "13-23 kV", " / ".join(r["tag"] for r in dts)]),
            ("ltr", [f"LTR-101{ab}", f"{R['ltr'][ab]['kva']:g} kVA", "480-208Y/120 V", f"to LDB-101{ab}"]),
            ("ups", [f"UPS-101{ab}", f"{ctx['ud']['ups']['rating_kVA']:g} kVA", "SEE SLD-004"]),
            ("dc", [f"BC-101{ab}", "125 V DC", "SEE SLD-004"]),
            ("misc", [f"{len(misc)} x FEEDERS", "HVAC, HT, MOV,", "WELDING, CP", "SEE SLD-003"]),
            ("spare", ["SPARE"]),
        ]
        for i, (k, lab) in enumerate(groups):
            xf = X(140 + 34 * i)
            p.dot(xf, ylv)
            yy = p.breaker(xf, ylv, drawout=False, s=0.85)[1]
            if k == "mot":
                yy = p.breaker(xf, yy, drawout=False, kind="contactor", s=0.7)[1]
                yy = p.overload(xf, yy, s=0.8)[1]
                yy = p.motor(xf, yy)[1]
            elif k == "vfd":
                yy = p.vfd(xf, yy, w=7, h=7, lead=1.5)[1]
                yy = p.motor(xf, yy)[1]
            elif k in ("dt", "ltr"):
                yy = p.transformer(xf, yy, r=3.4, h_lead=1.5)[1]
            elif k in ("ups", "dc"):
                p.line(xf, yy, xf, yy + 2)
                yy = p.converter(xf, yy + 2, "~", "=" if k == "dc" else "~", w=8, h=8)[1]
            elif k == "misc":
                yy = p.arrow_down(xf, yy, 6)[1]
            else:
                yy = yy + 1
            p.lines([t for t in lab if t], xf, yy + 4.5, 2.0, anchor="middle", bold_first=True)
    # ---------------- tie breakers (horizontal, N.O.)
    for y, nm in ((y13, "52-T1"), (y4, "52-T2"), (ylv, "52-T3")):
        p.line(405, y, 418.5, y, w=1.6)
        p.breaker(418.5, y, rot=-90)
        p.line(431.5, y, 445, y, w=1.6)
        p.text(nm + " N.O.", 425, y - 6.0, 2.0, "middle", bold=True)
        p.relays(419.0, y + 4.5, ["50/51", "86"], cols=2)
    # ---------------- legend
    legend(p, 215, 16, w=420)
    # ---------------- maximum demand + ratings tables
    tot = R["total"]
    rws = []
    for b in BLV:
        d = md[b]
        rws.append([b, _f(d["C_kW"]), _f(d["I_kW"]), _f(d["S_kW"]), _f(d["kW"]), _f(d["kvar"]), _f(d["kVA"]),
                    f"{d['pf']:.2f}"])
    for b in B4:
        d = md[b]
        bb = R["bus4"][b]
        rws.append([b + " (MV motors)", _f(d["C_kW"]), _f(d["I_kW"]), _f(d["S_kW"]), _f(d["kW"]), _f(d["kvar"]),
                    _f(d["kVA"]), f"{d['pf']:.2f}"])
        rws.append([b + " (incl. LV)", "", "", "", _f(bb["kW"]), _f(bb["kvar"]), _f(bb["kVA"]),
                    f"{bb['kW'] / bb['kVA']:.2f}"])
    rws.append(["UNIT TOTAL at 13.8 kV", "", "", "", _f(tot["kW"]), _f(tot["kvar"]), _f(tot["kVA"]),
                f"{tot['pf']:.2f}"])
    y0 = 440
    table(p, 20, y0, [("BUS", 50, "l"), ("C kW", 18, "r"), ("I kW", 16, "r"), ("S kW", 18, "r"),
                      ("MD kW", 20, "r"), ("MD kvar", 21, "r"), ("MD kVA", 20, "r"), ("PF", 12, "r")], rws,
          "MAXIMUM DEMAND SUMMARY  (MD = C + 0.3 I + 0.1 S)", bold_last=True)
    rat = [["SWG-101A/B", "13.8 kV metal-clad, VCB", f"{sw['SWG-101']['bus_A']} A", f"{sw['SWG-101']['kA']:g} kA"],
           ["TR-101/102", f"{trm['onan_kVA'] / 1000:g}/{trm['onaf_kVA'] / 1000:g} MVA 13.8/4.16 kV",
            f"Z {trm['z_pct']:g} %", f"{trm['load_onan_pct']:.0f} % MD"],
           ["SWG-102A/B", "4.16 kV metal-clad, VCB, AR", f"{sw['SWG-102']['bus_A']} A", f"{sw['SWG-102']['kA']:g} kA"],
           ["TR-103/104", f"{trl['onan_kVA']:g}/{trl['onaf_kVA']:g} kVA 4.16/0.48 kV",
            f"Z {trl['z_pct']:g} %", f"{trl['load_onan_pct']:.0f} % MD"],
           ["MCC-101A/B", "480 V LV swgr + MCC", f"{sw['MCC-101']['bus_A']} A", f"{sw['MCC-101']['kA']:g} kA"],
           ["UPS-101A/B", f"2 x {ctx['ud']['ups']['rating_kVA']:g} kVA, 30 min", "VRLA",
            f"{ctx['ud']['ups']['ah_sel']} Ah"]]
    table(p, 205, y0, [("TAG", 25, "l"), ("DESCRIPTION", 62, "l"), ("RATING", 20, "r"), ("SC / LOAD", 22, "r")],
          rat, "MAIN EQUIPMENT RATINGS")
    sc = R["sc"]
    scr = [[k, f"{sc['worst_kA'][k]:.1f}", f"{sc['worst_ip_kA'][k]:.1f}", f"{sc['rating_kA'][k]:g}"]
           for k in ("13.8 kV", "4.16 kV", "0.48 kV")]
    table(p, 365, y0, [("BUS", 20, "l"), ("Ik\" kA", 18, "r"), ("ip kA", 18, "r"), ("RATED kA", 22, "r")], scr,
          "FAULT LEVELS (max. case)")
    st = R["start"][0]
    p.lines(["MOTOR STARTING (largest DOL motor):",
             f"{st['motor']} {st['kW']:g} kW DOL at 4.16 kV:",
             f"bus dip {st['bus_dip_pct']:.1f} % (limit 10 %),",
             f"terminal dip {st['term_dip_pct']:.1f} % (limit 15 %)"], 365, y0 + 30, 2.3, bold_first=True)
    sh.save(out / "CFU-000-EL-SLD-001")
    return out / "CFU-000-EL-SLD-001.svg"


def _rel(p, x, y, devs, side, cols=2, dx=4.0, link=True):
    w = cols * 5.2 + (cols + 1) * 0.6
    if side == 0:
        bx = x + dx
    else:
        bx = x - dx - w
    p.relays(bx, y - 3.2, devs, cols=cols)
    if link:
        if side == 0:
            p.line(x + 1.3, y + 0.0, bx, y + 0.0, w=0.25, dash="1,0.7")
        else:
            p.line(x - 1.3, y + 0.0, bx + w, y + 0.0, w=0.25, dash="1,0.7")


# --------------------------------------------------------------------------------------------- SLD-002
ANSI = [("25", "Synchronism check"), ("27", "Undervoltage"), ("27R", "Residual voltage (transfer)"),
        ("46", "Negative-sequence / phase unbalance"), ("47", "Phase-sequence voltage"),
        ("49", "Thermal overload (motor, RTD)"), ("49T", "Transformer winding temperature"),
        ("50/51", "Instantaneous / time overcurrent"), ("50G", "Ground fault via ZSCT"),
        ("50N/51N", "Residual ground overcurrent"), ("51G", "Neutral (NGR) ground overcurrent"),
        ("59", "Overvoltage"), ("63", "Sudden pressure / Buchholz"), ("66", "Starts per hour"),
        ("67", "Directional overcurrent"), ("81", "Under/over frequency"), ("86", "Lockout relay"),
        ("87L/M/T", "Line / motor / transformer differential")]


def _wrap(t, n=20):
    out, cur = [], ""
    for w in t.replace("/", "/ ").split():
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur)
            cur = ""
        cur = (cur + " " + w).strip() if not cur.endswith("/") else cur + w
    if cur:
        out.append(cur)
    return out


def sld_002(ctx, out: Path):
    rows, R, cab = ctx["rows"], ctx["R"], ctx["cab"]
    trm, trl, sw = R["tr_mv"], R["tr_lv"], R["swgr"]
    notes = [
        "Switchgear: 4.16 kV metal-clad, arc-resistant (IEEE C37.20.7 Type 2B), drawout vacuum breakers,",
        f"  {sw['SWG-102']['bus_A']} A main bus, {sw['SWG-102']['kA']:g} kA sym. interrupting, 125 V DC control.",
        "Motor feeders: VCB + microprocessor motor protection relay (MPR) with RTD module (49).",
        "  87M (self-balancing CTs at motor terminal box) for motors >= 500 kW.",
        "VFD feeders: MV drive (18-pulse / AFE, IEEE 519 compliant) incl. motor protection (49/46/37).",
        "Auto-transfer: on loss of incomer (27 + 27R), incomer trips and tie closes (open transition);",
        "  manual return. Incomer/tie 2-out-of-3 interlock. MV motors restart by DCS sequence (no auto-restart).",
        "CT secondaries 5 A, C200/C400 relaying class; metering 0.3 class. All relays IEC 61850 to ECS.",
        "Motor space heaters 120 V fed from MCC-101A/B lighting panels; interlocked with VCB.",
        "Cable sizes per CFU-000-EL-CBL-001; lengths are route estimates (layout not final).",
    ]
    sh = Sheet("A1", "SINGLE LINE DIAGRAM", "4.16 kV SWITCHGEAR SWG-102A / SWG-102B", "CFU-000-EL-SLD-002",
               discipline=DISC)
    put_notes(sh, notes)
    p = Pen(sh)
    yb = 168.0
    sp = 41.0
    K = 1.25           # symbol scale on this sheet
    for s in (0, 1):
        ab = "AB"[s]
        L = s == 0
        X = (lambda x: x) if L else (lambda x: 850 - x)
        side, oside = ("left", "right") if L else ("right", "left")
        sg = 1 if L else -1
        bx1, bx2 = (24, 405) if L else (445, 826)
        p.bus(bx1, bx2, yb)
        p.bus_label(bx1 if L else bx2, yb, [f"SWG-102{ab}", f"4.16 kV, 3-ph, 3-W, 60 Hz, {sw['SWG-102']['bus_A']} A",
                                           f"{sw['SWG-102']['kA']:g} kA sym. / {R['sc']['worst_ip_kA']['4.16 kV']:.0f} kA peak calc.",
                                           "Arc-resistant Type 2B"],
                    "start" if L else "end")
        # incomer from TR-101 / TR-102
        xi = X(70)
        p.lines([f"FROM SWG-101{ab}", "(SLD-001)"], xi, 22, 2.3, anchor="middle", bold_first=True)
        p.line(xi, 26, xi, 32)
        lbl = [f"TR-10{s + 1}", f"{trm['onan_kVA'] / 1000:g}/{trm['onaf_kVA'] / 1000:g} MVA ONAN/ONAF",
               "13.8/4.16 kV Dyn1", f"Z {trm['z_pct']:g} %"]
        r_t = 8.0
        _, y = p.transformer(xi, 32, r=r_t, ngr=None, label=lbl, label_x=xi - 11 if L else xi + 11)
        # neutral: CT + NGR, drawn on the outer side away from the relay box
        yn = 32 + 2 + r_t + 1.25 * r_t + 0.2 * r_t
        xn = xi - sg * 14
        p.line(xi - sg * r_t * 0.95, yn, xn, yn)
        p.line(xn, yn, xn, yn + 3)
        p.circle(xn, yn + 4.3, 1.3, fill="none")
        p.line(xn, yn + 5.6, xn, yn + 7)
        p.rect(xn - 1.1, yn + 7, 2.2, 6)
        p.line(xn, yn + 13, xn, yn + 14)
        p.ground(xn, yn + 14)
        p.lines(["NGR 400 A, 10 s", "CT 400/5 -> 51G"], xn - sg * 2.5, yn + 6, 1.9, anchor="end" if L else "start")
        p.line(xi, y, xi, y + 10)
        c = cab[f"CBL-TR-10{s + 1}-S"]
        p.cable_tag(xi, y + 4, c["cable"].split(" Cu")[0], side=oside, size=1.9)
        p.ct(xi, y + 14, "2000/5", side=side, n=2)
        p.line(xi, y + 10, xi, y + 12.7)
        p.line(xi, y + 17.5, xi, y + 26)
        dv = ["87T", "51", "51G", "27", "27R", "59", "81", "86"]
        w = 3 * 5.8 + 4 * 0.6
        p.relays(xi + 5 if L else xi - 5 - w, y + 9, dv, cols=3, r=2.9)
        p.line(xi + sg * 1.3, y + 14, xi + sg * 5, y + 14, w=0.25, dash="1,0.7")
        p.breaker(xi, y + 26, s=K)
        p.lines([f"52-M{ab}", "VCB 2000 A"], xi + sg * 4, y + 36, 2.0, anchor="start" if L else "end")
        p.line(xi, y + 26 + 13 * K, xi, yb)
        p.dot(xi, yb)
        # feeders
        mv = sorted([r for r in rows if r["bus"] == B4[s]], key=lambda r: -r["rated_kw"])
        feeders = [("tx", None)] + [("m", r) for r in mv] + [("spare", None)]
        h = 13 * K
        for i, (k, r) in enumerate(feeders):
            xf = X(112 + sp * i)
            p.dot(xf, yb)
            p.breaker(xf, yb, s=K)
            p.line(xf, yb + h, xf, yb + 24)
            if k == "spare":
                p.lines(["SPARE", "(EQUIPPED)", "VCB 1200 A"], xf, yb + 30, 2.1, anchor="middle", bold_first=True)
                continue
            if k == "tx":
                ct = "600/5"
                devs = ["50/51", "50N/51N", "63", "49T", "86T"]
            else:
                ct = r["ct"].replace(" A", "")
                if r["vfd"]:
                    devs = ["50/51", "50G", "27", "86"]
                else:
                    devs = ["50/51", "50G", "46", "49", "27", "66", "86"]
                    if r["rated_kw"] >= 500:
                        devs.insert(4, "87M")
            p.ct(xf, yb + 25.3, ct, side="left")
            p.line(xf, yb + 26.6, xf, yb + 40)
            if k == "m" and not r["vfd"]:
                p.g.add(p.d.ellipse((xf, yb + 32.5), (2.6, 1.0), fill="none", stroke="black", stroke_width=0.3))
                p.text("ZSCT 50/5", xf - 3.4, yb + 33.2, 1.8, "end")
            p.relays(xf + 4, yb + 20, devs, cols=2, r=2.9)
            p.line(xf + 1.3, yb + 25.3, xf + 4, yb + 25.3, w=0.25, dash="1,0.7")
            p.lines([f"52-{(r['tag'] if r else 'TR-10' + str(s + 3))}", "VCB 1200 A"], xf - 3.5, yb + 7.5, 1.8,
                    anchor="end")
            y = yb + 40
            if k == "tx":
                c = cab[f"CBL-TR-10{s + 3}-P"]
                p.line(xf, y, xf, y + 30)
                p.cable_tag(xf, y + 14, c["cable"].split(" Cu")[0].replace(" mm2", ""), side="left", size=1.8)
                p.text(f"{c['L_m']:.0f} m", xf - 2, y + 18.5, 1.8, "end")
                _, y2 = p.transformer(xf, y + 30, r=6.5)
                p.line(xf, y2, xf, y2 + 3)
                p.arrow_down(xf, y2 + 3, 5)
                p.lines([f"TR-10{s + 3}", f"{trl['onan_kVA']:g}/{trl['onaf_kVA']:g} kVA", "4.16/0.48 kV Dyn1",
                         f"Z {trl['z_pct']:g} %, HRG 5 A", f"TO MCC-101{ab}", "(SLD-003)"], xf, y2 + 14, 2.1,
                        anchor="middle", bold_first=True)
                continue
            c = cab[f"CBL-{r['tag']}"]
            if r["vfd"]:
                p.line(xf, y, xf, y + 6)
                _, y = p.vfd(xf, y + 6, w=11, h=11, lead=2)
                p.lines([f"VFD-{r['tag']}", "4.16 kV MV drive", "18-pulse / AFE"], xf - 7.5, y - 12, 1.8,
                        anchor="end")
            p.line(xf, y, xf, yb + 104)
            p.cable_tag(xf, yb + 92, c["cable"].split(" Cu")[0].replace(" mm2", ""), side="left", size=1.8)
            p.text(f"{c['L_m']:.0f} m", xf - 2, yb + 96.5, 1.8, "end")
            _, ym = p.motor(xf, yb + 104, r=5.5)
            if not r["vfd"] and r["rated_kw"] >= 500:
                p.lines(["87M CTs at", "star point"], xf + 7, yb + 112, 1.7)
            duty = {"C": "NORMALLY RUNNING", "S": "STANDBY", "I": "INTERMITTENT"}[r["duty"]]
            info = [r["tag"]] + _wrap(r["desc"].replace(" pump A", "").replace(" pump B", "")
                                      .replace(" fan A", " fan").replace(" fan B", " fan"), 22) + \
                [f"{r['rated_kw']:g} kW, FLC {r['I_fl']:.0f} A", f"absorbed {r['absorbed_kw']:.0f} kW",
                 ("VFD" if r["vfd"] else f"DOL, LRC {C.LRC:g} x FLC"), duty]
            p.lines(info, xf, ym + 5, 2.1, anchor="middle", bold_first=True)
        # bus VT
        xv = X(393)
        p.dot(xv, yb)
        p.vt(xv, yb, "")
        p.lines(["VT", "4200/120 V"], xv, yb + 22, 1.9, anchor="middle")
        p.relays(xv - 6.6, yb + 27, ["27", "59", "47", "81"], cols=2, r=2.9)
    # tie
    p.line(405, yb, 418.5, yb, w=1.6)
    p.breaker(418.5, yb, rot=-90)
    p.line(431.5, yb, 445, yb, w=1.6)
    p.lines(["52-T2  N.O.", "VCB 2000 A"], 425, yb - 9, 2.2, anchor="middle", bold_first=True)
    p.relays(419.0, yb + 4.5, ["50/51", "25", "86"], cols=2)
    # ANSI legend and MV motor table
    y0 = 375
    half = (len(ANSI) + 1) // 2
    table(p, 20, y0, [("DEVICE", 18, "l"), ("FUNCTION (ANSI/IEEE C37.2)", 58, "l")], [list(a) for a in ANSI[:half]],
          "PROTECTIVE DEVICE FUNCTIONS", size=2.4, rh=5.6)
    table(p, 104, y0, [("DEVICE", 18, "l"), ("FUNCTION", 62, "l")], [list(a) for a in ANSI[half:]], size=2.4, rh=5.6)
    mvr = []
    for r in sorted([r for r in rows if r["volt"] > 1000], key=lambda r: r["tag"]):
        c = cab[f"CBL-{r['tag']}"]
        mvr.append([r["tag"], r["bus"], f"{r['rated_kw']:g}", f"{r['I_fl']:.0f}", "VFD" if r["vfd"] else "DOL",
                    r["ct"].replace(" A", ""), c["cable"].split(" Cu")[0], f"{c['L_m']:.0f}", f"{c['vd_run']:.2f}",
                    "-" if c.get("term_dip") is None else f"{c['term_dip']:.1f}"])
    table(p, 200, y0, [("TAG", 19, "l"), ("BUS", 22, "l"), ("kW", 12, "r"), ("FLC A", 14, "r"), ("START", 15, "c"),
                       ("CT", 16, "c"), ("CABLE", 40, "l"), ("L m", 12, "r"), ("VD run %", 18, "r"),
                       ("Vdip start %", 22, "r")], mvr, "MV MOTOR FEEDER SCHEDULE (term. dip = bus dip + cable)",
          size=2.4, rh=5.6)
    sh.save(out / "CFU-000-EL-SLD-002")
    return out / "CFU-000-EL-SLD-002.svg"


# --------------------------------------------------------------------------------------------- SLD-003
def _short_cable(c):
    t = c["cable"].split(" Cu")[0].replace(" mm2", "").replace(" ", "")
    return t


def mcc_feeders(ctx, s):
    rows, R, cab = ctx["rows"], ctx["R"], ctx["cab"]
    lv = [r for r in rows if r["bus"] == BLV[s] and r["volt"] != 208]
    order = {"Pumps": 0, "Fired-heater fans": 1, "Air-cooler fans": 2, "Chemical packages": 3}
    lv.sort(key=lambda r: (1 if r["vfd"] else 0, 0 if r["kind"] == "motor" else 2, order.get(r["group"], 9),
                           r["tag"]))
    fd = []
    for r in lv:
        fd.append(("vfd" if r["vfd"] else "mot" if r["kind"] == "motor" else
                   "tx" if r["tag"].startswith("DT-") else "conv" if r["tag"].startswith(("UPS-", "BC-")) else
                   "fdr", r, cab[f"CBL-{r['tag']}"]))
    ab = "AB"[s]
    fd.append(("ltr", dict(tag=f"LTR-101{ab}", rated_kw=None, duty="C", mccb=R["ltr"][ab]["mccb"],
                           desc="Lighting/small power"), cab[f"CBL-LTR-101{ab}"]))
    fd += [("spare", None, None), ("spare", None, None)]
    return fd


def sld_003(ctx, out: Path, s: int):
    rows, R, cab = ctx["rows"], ctx["R"], ctx["cab"]
    trl, sw = R["tr_lv"], R["swgr"]
    ab = "AB"[s]
    other = "AB"[1 - s]
    notes = [
        f"MCC-101{ab}: 480 V, 3-ph 3-W, {sw['MCC-101']['bus_A']} A Cu bus, {sw['MCC-101']['kA']:g} kA sym.; ACB incomer/tie",
        "  in LV switchgear section (IEEE C37.20.1), MCC sections UL 845, withdrawable buckets.",
        "Motor buckets: MCCB (thermal-magnetic, <= 250 % FLC per NEC 430.52) + contactor + electronic OL,",
        "  IEC 60947-4-1 Type 2 coordination; 120 V control transformer; DCS hardwired start/stop/run/trip.",
        "Motors >= 30 kW: 4-20 mA motor current to DCS. VFDs: 6-pulse + passive filter (THDi <= 8 %).",
        "Cable: Cu/XLPE/SWA/PVC 0.6/1 kV (IEC mm2). Sizes per CFU-000-EL-CBL-001 (ampacity x 1.25 FLC,",
        "  VD <= 5 % running, <= 15 % at motor terminals during start, SC withstand via MCCB let-through).",
        "Pump A/B pairs on opposite MCC sections; RUN/STBY = normally running unit for demand calculation.",
    ]
    sh = Sheet("A1", "SINGLE LINE DIAGRAM", f"480 V SWITCHGEAR / MCC-101{ab}", "CFU-000-EL-SLD-003",
               sheet=f"{s + 1} OF 2", discipline=DISC)
    put_notes(sh, notes)
    p = Pen(sh)
    fd = mcc_feeders(ctx, s)
    n1 = (len(fd) + 1) // 2
    tiers = [fd[:n1], fd[n1:]]
    ybs = [96.0, 284.0]
    x0, x1 = 64.0, 790.0
    for t, (yb, items) in enumerate(zip(ybs, tiers)):
        sp = (x1 - x0) / max(len(items), 1)
        bstart = 24 if t == 0 else 30
        bend = x0 + sp * (len(items) - 0.5) + 6
        p.bus(bstart, bend, yb)
        if t == 0:
            p.bus_label(24, yb, [f"MCC-101{ab}", f"480 V, 3-ph, 60 Hz, {sw['MCC-101']['bus_A']} A",
                                 f"{sw['MCC-101']['kA']:g} kA sym. (calc. {R['sc']['worst_kA']['0.48 kV']:.1f} kA)"])
            # incomer
            xi = 44.0
            p.lines([f"FROM TR-10{s + 3}", "(SLD-002)"], xi + 1, 22, 2.2, anchor="start", bold_first=True)
            p.line(xi, 25, xi, 34)
            p.text(f"BUS DUCT {C.std_up(trl['I_sec_onaf_A'], C.BUS_A)} A", xi + 2.5, 31, 1.9)
            p.ct(xi, 37.3, "5000/5", side="left")
            p.line(xi, 38.6, xi, 46)
            p.relays(xi + 4.5, 33.5, ["50/51", "64", "59N", "27", "86"], cols=3, r=2.7)
            p.line(xi + 1.3, 37.3, xi + 4.5, 37.3, w=0.25, dash="1,0.7")
            p.breaker(xi, 46, s=1.1)
            p.lines([f"52-L{ab}", f"ACB {C.std_up(trl['I_sec_onaf_A'], C.BUS_A)} A"], xi + 4, 70, 1.9)
            p.line(xi, 46 + 14.3, xi, yb)
            p.dot(xi, yb)
            # tie at right end
            p.line(bend, yb, bend + 4, yb, w=1.6)
            p.breaker(bend + 4, yb, rot=-90)
            p.line(bend + 17, yb, bend + 20, yb)
            p.lines([f"52-T3 N.O.", "ACB 5000 A", f"TO MCC-101{other}", f"(SHEET {2 - s} OF 2)"], bend + 10, yb - 15,
                    1.9, anchor="middle", bold_first=True)
            p.text("BUS CONTINUED ON TIER 2  >>", bend - 2, yb + 4.2, 1.9, "end", italic=True)
        else:
            p.text("<<  BUS CONTINUED FROM TIER 1", bstart, yb - 2.2, 2.0, italic=True)
        for i, (k, r, c) in enumerate(items):
            xf = x0 + sp * i + (8 if t == 1 else 0)
            p.dot(xf, yb)
            y = p.breaker(xf, yb, drawout=False, s=1.0)[1]
            if k == "spare":
                p.lines(["SPARE", "BUCKET", "MCCB 100 A"], xf, y + 5, 1.9, anchor="middle", bold_first=True)
                continue
            mccb = r.get("mccb")
            if k == "mot":
                y = p.breaker(xf, y, drawout=False, kind="contactor", s=0.9)[1]
                y = p.overload(xf, y, s=1.0)[1]
            elif k == "vfd":
                y = p.vfd(xf, y, w=9, h=9, lead=2)[1]
            p.line(xf, y, xf, yb + 58)
            p.cable_tag(xf, yb + 52, "", size=1.6)
            yy = yb + 58
            if k in ("mot", "vfd"):
                yy = p.motor(xf, yy, r=4.4, lead=1.0)[1]
            elif k in ("tx", "ltr"):
                yy = p.transformer(xf, yy, r=3.9, h_lead=1.0)[1]
            elif k == "conv":
                p.line(xf, yy, xf, yy + 1)
                yy = p.converter(xf, yy + 1, "~", "=" if r["tag"].startswith("BC") else "~", w=8.5, h=8.5)[1]
            else:
                yy = p.arrow_down(xf, yy - 1, 6)[1]
            duty = {"C": "RUN", "S": "STBY", "I": "INTERM."}[r["duty"]]
            if k in ("mot", "vfd"):
                info = [r["tag"], f"{r['rated_kw']:g} kW  {duty}", f"FLC {r['I_fl']:.0f} A",
                        f"MCCB {mccb} A", "VFD" if k == "vfd" else f"NEMA {_nema_size(r['rated_kw'])}"]
            elif k == "ltr":
                info = [r["tag"], f"{R['ltr'][ab]['kva']:g} kVA", "480-208Y/120", f"MCCB {mccb} A",
                        f"-> LDB-101{ab}"]
            else:
                kv = r.get("kva_rated")
                rating = f"{kv:g} kVA" if kv else f"{r['rated_kw']:g} kW"
                info = [r["tag"], f"{rating}  {duty}", _short_desc(r), f"MCCB {mccb} A", ""]
            info += [_short_cable(c), f"{c['L_m']:.0f} m, VD {c['vd_run']:.1f} %"]
            p.lines([x for x in info if x], xf, yy + 4.6, 2.0, lh=2.65, anchor="middle", bold_first=True)
    # section summary
    d = R["md"][BLV[s]]
    lv = [r for r in rows if r["bus"] == BLV[s]]
    nm = sum(1 for r in lv if r["kind"] == "motor")
    rws = [["Feeders / buckets", f"{len(fd)} ({nm} motor, {sum(1 for f in fd if f[0] == 'spare')} spare)"],
           ["Connected load", f"{_f(d['connected_kW'])} kW"],
           ["Continuous / Interm. / Standby", f"{_f(d['C_kW'])} / {_f(d['I_kW'])} / {_f(d['S_kW'])} kW"],
           ["Maximum demand (C+0.3I+0.1S)", f"{_f(d['kW'])} kW / {_f(d['kVA'])} kVA, PF {d['pf']:.2f}"],
           ["Both sections on one TR (tie closed)", f"{_f(R['md_lv_total']['kVA'])} kVA vs TR "
                                                    f"{trl['onan_kVA']:g}/{trl['onaf_kVA']:g} kVA ONAN/ONAF"],
           ["Largest DOL motor start - bus dip", f"{max((c['bus_dip'] or 0) for k, r, c in fd if c and c.get('bus_dip') is not None):.1f} % (limit 10 %)"]]
    table(p, 24, 432, [("MCC-101" + ab + " SUMMARY", 62, "l"), ("VALUE", 88, "l")], rws, size=2.3, rh=5.2)
    stem = out / f"CFU-000-EL-SLD-003-SH{s + 1}"
    sh.save(stem)
    return stem.with_suffix(".svg")


def _short_desc(r):
    t = r["tag"]
    if t.startswith("DT-"):
        return f"{r['eq']} grid TX"
    return {"Valve actuators": "MOV supply", "Heat tracing": "Heat tracing", "Welding outlets": "Welding outlets",
            "Cathodic protection": "Cathodic prot.", "Miscellaneous": "Hoists" if t.startswith("HST") else
            "Sootblowers"}.get(r["group"]) or (
        "UPS rectifier" if t.startswith("UPS") else "125 V DC charger" if t.startswith("BC") else
        "Batt. room fan" if t.startswith("BEF") else "Analyser house" if t.startswith("AH") else
        "SS-100 HVAC" if t.startswith("HVAC-101") else "FAR-100 HVAC" if t.startswith("HVAC-102") else r["group"])


def _nema_size(kw):
    from .cables import _nema
    return _nema(kw)


# --------------------------------------------------------------------------------------------- SLD-004
def sld_004(ctx, out: Path):
    R, ud, urows, cab = ctx["R"], ctx["ud"], ctx["ups_rows"], ctx["cab"]
    U, D = ud["ups"], ud["dc"]
    notes = [
        "Emergency diesel generator NOT provided. Basis: two independent 13.8 kV feeders from refinery main",
        "  substation; unit is designed to fail safe on total power loss (SIS de-energise-to-trip, fail-safe",
        "  valves, heater BMS trip); no machinery needs post-trip power (no lube-oil / seal-oil pumps,",
        "  API 682 seals, steam ejectors). Essential loads (DCS, SIS/BMS, F&G, PAGA/telecom) on UPS 30 min;",
        "  escape lighting self-contained 90 min. To be confirmed in HAZOP / refinery power study.",
        f"UPS: {U['config']}; {U['rating_kVA']:g} kVA each; input {U['input']}; output {U['output']}.",
        "Consumers with redundant PSUs fed from both UDBs; single-fed loads via static transfer switch STS-101.",
        f"UPS battery: {U['battery_type']}; {U['cells']} cells, {U['ah_sel']} Ah, {U['autonomy_min']} min at design load.",
        f"125 V DC: {D['config']}; batteries {D['ah_sel']} Ah VRLA 60 cells, {D['autonomy_h']:g} h duty cycle (IEEE 485).",
        "Battery rooms ventilated per IEEE 1635 / NFPA 70E; DC system ungrounded with ground-fault detection.",
    ]
    sh = Sheet("A1", "SINGLE LINE DIAGRAM", "UPS & 125 V DC SYSTEMS", "CFU-000-EL-SLD-004", discipline=DISC)
    put_notes(sh, notes)
    SC = 1.42
    gs = sh.dwg.g(transform=f"translate(6,4) scale({SC})", font_family="DejaVu Sans, Arial, sans-serif",
                  fill="none", stroke="black", stroke_width=0.3)
    sh.dwg.add(gs)
    p = Pen(sh, gs)
    pt = Pen(sh)
    share = {}
    for r in urows:
        share.setdefault(r["tag"].rsplit("-", 1)[0], r)
    for s in (0, 1):
        ab = "AB"[s]
        other = "AB"[1 - s]
        x0 = 60 + s * 280
        # rectifier input from MCC
        xr = x0 + 40
        xb = x0 + 110        # bypass line
        p.lines([f"FROM MCC-101{ab}", "(SLD-003)", f"MCCB {cab['CBL-UPS-101' + ab]['device'].split()[1]} A"], xr, 22,
                2.1, anchor="middle", bold_first=True)
        p.line(xr, 31, xr, 34)
        y = p.breaker(xr, 34, drawout=False, s=1.0)[1]
        p.line(xr, y, xr, y + 4)
        _, y = p.converter(xr, y + 4, "~", "=", w=13, h=13, label=["RECTIFIER /", "CHARGER", "IGBT, 480 V"],
                           label_side="left")
        yd = y + 10
        p.line(xr, y, xr, yd + 22)
        # battery branch
        p.dot(xr, yd)
        p.line(xr, yd, xr + 22, yd)
        yb2 = p.breaker(xr + 22, yd, drawout=False, s=0.8, kind="switch")[1]
        p.text("DC CB", xr + 25, yd + 6, 1.9)
        p.battery(xr + 22, yb2, [f"BAT-UPS-{ab}", f"{U['cells']} x 2 V VRLA", f"{U['ah_sel']} Ah",
                                 f"{U['autonomy_min']} min", f"{U['v_nom']:.0f} V DC nom."], s=1.3)
        _, y = p.converter(xr, yd + 22, "=", "~", w=13, h=13, label=["INVERTER", f"{U['rating_kVA']:g} kVA"],
                           label_side="left")
        p.line(xr, y, xr, y + 6)
        yss = y + 6
        # static switch
        p.rect(xr - 7, yss, 34 + (xb - xr - 27), 10)
        p.text(f"STATIC SWITCH SS-{ab}", (xr + xb) / 2, yss + 6.2, 2.0, "middle", bold=True)
        # bypass from other MCC through bypass transformer
        p.lines([f"BYPASS FROM", f"MCC-101{other}"], xb, 22, 2.1, anchor="middle", bold_first=True)
        p.line(xb, 28, xb, 34)
        y = p.breaker(xb, 34, drawout=False, s=1.0)[1]
        _, y = p.transformer(xb, y, r=4.5, h_lead=2, label=[f"BTR-101{ab}", "112.5 kVA", "480-208Y/120 V",
                                                              "shielded"], label_x=xb + 7)
        p.line(xb, y, xb, yss)
        # maintenance bypass
        xm = xb + 26
        p.line(xb, 52 + 0, xm, 52)
        p.dot(xb, 52)
        p.line(xm, 52, xm, yss + 24)
        p.breaker(xm, yss + 24, drawout=False, s=0.9, kind="switch")
        p.lines(["MAINT.", "BYPASS", "(interlocked)"], xm + 3, yss + 18, 1.8)
        yo = yss + 10
        p.line(xr + 10, yo, xr + 10, yo + 10)
        y = p.breaker(xr + 10, yo + 10, drawout=False, s=0.9)[1]
        yu = y + 14
        p.line(xr + 10, y, xr + 10, yu)
        p.line(xm, yss + 24 + 11.7, xm, yu)
        p.dot(xm, yu)
        p.dot(xr + 10, yu)
        # UDB
        ux1, ux2 = x0 - 12, x0 + 205
        p.bus(ux1, ux2, yu)
        p.bus_label(ux1, yu, [f"UDB-101{ab}", "208Y/120 V, 60 Hz, 400 A, 10 kA"])
        feeders = [(k, r) for k, r in share.items()]
        feeders = [("UPS-" + c, None) for c in ("DCS", "SIS", "FGS", "TEL", "ANZ", "MISC")]
        for i, (code, _) in enumerate(feeders + [("STS-101", None), ("SPARE", None)]):
            xf = x0 + 2 + i * 26
            p.dot(xf, yu)
            y = p.breaker(xf, yu, drawout=False, s=0.8)[1]
            p.arrow_down(xf, y, 6)
            if code.startswith("UPS-"):
                rr = next(r for r in urows if r["tag"] == f"{code}-{ab}")
                kva = rr["kva_rated"]
                amp = kva * 1000 / (1.732 * 208)
                mcb = C.std_up(amp * 1.25, C.NEC_A)
                txt = [code[4:] + "-" + ab, f"{kva:g} kVA", f"MCB {mcb} A 3P", "(dual-fed)"]
            elif code == "STS-101":
                txt = ["STS-101", "single-fed", "loads", f"(A/B)"]
            else:
                txt = ["SPARE", "MCB 60 A"]
            p.lines(txt, xf, y + 10, 1.85, anchor="middle", bold_first=True)
    # ---- DC system
    x0 = 640
    p.text("125 V DC SWITCHGEAR CONTROL SUPPLY", x0 + 50, 22, 2.4, "middle", bold=True)
    yd = 160
    for s in (0, 1):
        ab = "AB"[s]
        xc = x0 + 10 + s * 85
        p.lines([f"FROM MCC-101{ab}"], xc, 30, 2.0, anchor="middle", bold_first=True)
        p.line(xc, 31.5, xc, 36)
        y = p.breaker(xc, 36, drawout=False, s=0.9)[1]
        p.line(xc, y, xc, y + 4)
        _, y = p.converter(xc, y + 4, "~", "=", w=12, h=12, label=[f"BC-101{ab}", "125 V DC, 30 A"],
                           label_side="right" if s == 0 else "left")
        p.line(xc, y, xc, yd)
        yj = y + 18
        p.dot(xc, yj)
        p.line(xc, yj, xc + (18 if s == 0 else -18), yj)
        xbat = xc + (18 if s == 0 else -18)
        y2 = p.breaker(xbat, yj, drawout=False, s=0.75, kind="switch")[1]
        p.battery(xbat, y2, [f"BAT-DC-{ab}", f"60 x 2 V, {D['ah_sel']} Ah"] if s == 0 else None, s=1.2)
        if s == 1:
            p.lines([f"BAT-DC-{ab}", f"60 x 2 V, {D['ah_sel']} Ah"], xbat - 5, y2 + 4, 1.9, anchor="end")
        p.dot(xc, yd)
    p.bus(x0 - 5, x0 + 42, yd)
    p.bus(x0 + 58, x0 + 105, yd)
    p.line(x0 + 42, yd, x0 + 44, yd, w=1.6)
    p.breaker(x0 + 44, yd, rot=-90, drawout=False, s=0.9, kind="switch")
    p.line(x0 + 55.7, yd, x0 + 58, yd, w=1.6)
    p.text("N.O.", x0 + 50, yd - 3.5, 1.9, "middle", bold=True)
    p.bus_label(x0 - 5, yd + 26, [])
    p.text("DCDB-101  125 V DC, 200 A, 10 kA, ungrounded + GF detection", x0 - 5, yd - 7.5, 2.0, bold=True)
    dcf = ["SWG-101A", "SWG-102A", "MCC-101A", "SPARE", "SWG-101B", "SWG-102B", "MCC-101B", "SPARE"]
    for i, t in enumerate(dcf):
        xf = x0 + 2 + i * 13 + (12 if i >= 4 else 0)
        p.dot(xf, yd)
        y = p.breaker(xf, yd, drawout=False, s=0.7)[1]
        p.arrow_down(xf, y, 5)
        p.text(t, xf + 0.7, y + 7, 1.8, rotate=90)
    # ---- sizing tables
    y0 = 300
    urws = [["Connected UPS load (DCS 22, SIS/BMS 14, F&G 6, telecom 8, analysers 6, misc 4)", f"{U['load_kVA']:.0f} kVA"],
            ["Design load incl. 20 % future", f"{U['design_kVA']:.0f} kVA"],
            ["UPS rating (design load <= 80 % of rating)", f"2 x {U['rating_kVA']:g} kVA"],
            ["Battery power at design load (PF 0.9, inverter 94 %)", f"{U['battery_kW']:.1f} kW"],
            [f"Max. discharge current at end voltage {U['v_end']:.0f} V ({U['cells']} x 1.75 V)", f"{U['I_max_A']:.0f} A"],
            [f"Capacity = I x Kt({U['autonomy_min']} min)={U['Kt']} x aging {U['aging']} x margin {U['margin']}",
             f"{U['ah_req']:.0f} Ah -> {U['ah_sel']} Ah"],
            [f"125 V DC duty: {D['duty']}", f"F = {D['F']:.1f} Ah"],
            ["125 V DC battery incl. aging 1.25, margin 1.10", f"{D['ah_req']:.0f} Ah -> {D['ah_sel']} Ah"]]
    table(p, 24, y0, [("UPS / DC SIZING (detail in CFU-000-EL-CAL-001)", 150, "l"), ("RESULT", 40, "r")], urws,
          size=2.3, rh=5.4)
    crws = []
    for code, desc, kva in [(r["tag"].rsplit("-", 1)[0][4:], r["desc"].split(" - feed")[0], r["kva_rated"])
                            for r in urows if r["tag"].endswith("-A")]:
        crws.append([code, desc, f"{kva:g}", f"{kva / 2:g} + {kva / 2:g}"])
    crws.append(["TOTAL", "", f"{U['load_kVA']:g}", ""])
    table(p, 230, y0, [("CODE", 16, "l"), ("UPS CONSUMER", 112, "l"), ("kVA", 14, "r"), ("A + B share", 26, "r")],
          crws, size=2.3, rh=5.4, bold_last=True)
    sh.save(out / "CFU-000-EL-SLD-004")
    return out / "CFU-000-EL-SLD-004.svg"


def build_all(ctx, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    files = [sld_001(ctx, out), sld_002(ctx, out), sld_003(ctx, out, 0), sld_003(ctx, out, 1), sld_004(ctx, out)]
    merge_pdfs([out / "CFU-000-EL-SLD-003-SH1.pdf", out / "CFU-000-EL-SLD-003-SH2.pdf"],
               out / "CFU-000-EL-SLD-003.pdf")
    return files
