"""Process Flow Diagrams CFU-100/200-PR-PFD-001..006 (A1).

All process numbers (flows, temperatures, pressures, duties, sizes) are read from data/*.json
(streams, equipment, process_results, control_loops). Geometry is hand-laid per sheet.

    PYTHONPATH=. python -m cfu.pid.pfd
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

from .. import basis
from ..drawing.sheet import Sheet, merge_pdfs
from .symbols import Canvas, _tw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "deliverables" / "01-process" / "pfd"
DEG = "°C"


# ============================================================================ data
class Data:
    def __init__(self):
        dd = ROOT / "data"
        self.S = {s["no"]: s for s in json.loads((dd / "streams.json").read_text())}
        self.E = {e["tag"]: e for e in json.loads((dd / "equipment.json").read_text())}
        self.R = json.loads((dd / "process_results.json").read_text())
        cl = json.loads((dd / "control_loops.json").read_text())
        self.L = {l["tag"]: l for l in cl["loops"]}
        self.X = {x["tag"]: x for x in self.R["preheat"]["exch"]}
        self.TR = {x["tag"]: x for x in self.R["preheat"]["trims"]}
        self.used_loops: set[str] = set()
        self.used_streams: set[str] = set()

    def eq(self, tag):
        if tag in self.E:
            return self.E[tag]
        for k, v in self.E.items():
            if k.split("A/B")[0] == tag or k.startswith(tag + "A"):
                return v
        raise KeyError(tag)

    def T(self, no):
        return self.S[no]["T_C"]

    def loop(self, tag):
        if tag not in self.L:
            raise KeyError(f"control loop {tag} not in control_loops.json")
        self.used_loops.add(tag)
        return self.L[tag]


def fT(t):
    return f"{t:.0f} {DEG}"


def fP(p, unit="barg"):
    return f"{p:.2f} {unit}" if abs(p) < 10 else f"{p:.1f} {unit}"


def shell_suffix(e):
    n = e.get("n_shells") or e.get("shells") or 1
    return {1: "", 2: "A/B", 3: "A-C", 4: "A-D"}.get(int(n), "")


def disp_tag(D, tag):
    e = D.eq(tag)
    t = e["tag"]
    if e["type"] == "Shell & tube":
        sfx = shell_suffix(e)
        return f"{t}{sfx}" if sfx else t
    return t


def eq_lines(D, tag):
    """Equipment title strip text: (tag, [service lines], [data lines])."""
    e = D.eq(tag)
    typ = e["type"]
    svc = e["service"].upper().replace("MBAR(A)", "mbar(a)")
    data = []
    if typ == "Column":
        data.append(e["size"].replace(" (top/main)", "").replace(" (stripping)", " strip.")
                    .replace(" (main)", "").replace(" (top)", "").replace(" (boot)", " boot"))
        data.append(e["internals"].split(";")[0].split(",")[0])
    elif typ in ("Shell & tube",):
        arr = e["size"].split(";")[-1].strip()
        data.append(f"{e['duty_kw'] / 1000:.1f} MW, {e['area_m2']:.0f} m², TEMA {e['tema'].split()[0]}")
        if "shells" in arr and "x" in arr:
            data.append(arr.replace("shells", "shell arr."))
    elif typ == "Air cooler":
        data.append(f"{e['duty_kw'] / 1000:.1f} MW, {e['area_m2']:.0f} m² bare")
        data.append(f"{e['bays']} bay(s), {e['fans']} fans x {e['motor_kw']:g} kW")
    elif typ == "Fired heater":
        parts = [p.strip() for p in e["size"].replace(";", ",").split(",")]
        data.append(", ".join(parts[:2]))
        data.append(", ".join(parts[2:4]))
    elif typ == "Pump":
        data.append(f"{e['flow_m3h']:.0f} m³/h @ {e['head_m']:.0f} m")
        data.append(f"{e['motor_kw']:g} kW, API 610 {e['api610']}")
    elif typ == "Fan":
        data.append(f"{e['size']}, {e['motor_kw']:g} kW")
    elif typ == "Air preheater":
        data.append(e["size"].replace("->", "→"))
    elif typ == "Ejector":
        s = e["size"]
        data.append(s.split(",")[0])
        data.append(s.split(",")[1].strip().split("(")[0].strip())
        if "(" in s:
            data.append(s[s.index("(") + 1:s.index(")")])
    elif typ in ("Drum", "Desalter"):
        parts = [p.strip() for p in e["size"].replace(";", ",").split(",")]
        data.extend(parts[:2])
    else:
        data.append(e.get("size", ""))
    return disp_tag(D, tag), svc, data


# ============================================================================ sheet helpers
class PFD:
    BW = 50.0                    # title block width (mm)

    def __init__(self, D, docno, title2, notes, sheet_no):
        self.D = D
        self.docno = docno
        allnotes = notes + [
            "Stream numbers (diamonds) refer to H&MB CFU-000-PR-HMB-001; data from design case, normal operation.",
            "Pressures bar(g) unless noted. Pumps A/B are 2 x 100 %; only duty pump shown.",
        ]
        self.sh = Sheet("A1", "PROCESS FLOW DIAGRAM", title2, docno, sheet=f"{sheet_no} OF 6", notes=allnotes)
        self.c = Canvas(self.sh)
        self.titles = []
        self.streams = []

    # ------------------------------------------------------------- titles
    def title(self, tag, x):
        self.titles.append((tag, x))

    def _titles(self):
        c, D = self.c, self.D
        x_min, x_max = 17.0, 824.0
        rows = [[] for _ in range(3)]
        row_y = [19.5, 37.0, 54.5]
        items = sorted(self.titles, key=lambda t: t[1])
        place = []
        for tag, x in items:
            best = None
            for r in range(3):
                last = rows[r][-1] if rows[r] else x_min - 100
                xx = max(x - self.BW / 2, last + 2.0, x_min)
                shift = xx - (x - self.BW / 2)
                cost = shift + r * 40
                if xx + self.BW > x_max + 0.1:
                    cost += 1e4
                if best is None or cost < best[0]:
                    best = (cost, r, xx)
            _, r, xx = best
            rows[r].append(xx + self.BW)
            place.append((tag, r, xx))
        nrows = max(r for _, r, _ in place) + 1
        for tag, r, xx in place:
            t, svc, data = eq_lines(D, tag)
            y = row_y[r]
            cx = xx + self.BW / 2
            c.text(t, cx, y, 2.9, "middle", bold=True)
            w = _tw(t, 2.9) * 1.06
            c._ln((cx - w / 2, y + 0.7), (cx + w / 2, y + 0.7), 0.25)
            lines = textwrap.wrap(svc, 33)[:2]
            yy = y + 3.4
            for s in lines:
                c.text(s, cx, yy, 2.2, "middle")
                yy += 2.75
            for s in data:
                for s2 in textwrap.wrap(s, 36)[:2]:
                    c.text(s2, cx, yy, 2.2, "middle")
                    yy += 2.75
        self.title_bottom = row_y[nrows - 1] + 15

    # ------------------------------------------------------------- stream table
    def stream(self, no, x, y):
        self.c.diamond(x, y, no)
        if no not in self.streams:
            self.streams.append(no)
        self.D.used_streams.add(no)

    def _table(self):
        c, S = self.c, self.D.S
        nos = sorted(self.streams, key=lambda n: int(n))
        x0, x1 = 15.0, 645.0
        y0 = 521.0
        lab_w = 46.0
        cw = min(48.0, (x1 - x0 - lab_w) / max(len(nos), 1))
        rows = [("STREAM No.", 6.0), ("DESCRIPTION", 7.2), ("PHASE", 4.6), ("TOTAL FLOW  kg/h", 4.6),
                ("TEMPERATURE  " + DEG, 4.6), ("PRESSURE  barg", 4.6), ("STD LIQ. FLOW  BPSD", 4.6),
                ("VAPOUR FRACTION (mass)", 4.6), ("MOLECULAR WEIGHT", 4.6)]
        H = sum(h for _, h in rows)
        W = lab_w + cw * len(nos)
        g = c.gs
        g.add(c.d.rect((x0, y0), (W, H), fill="white", stroke="black", stroke_width=0.45))
        yy = y0
        phase = {"L": "LIQUID", "V": "VAPOUR", "M": "MIXED", "W": "WATER"}
        for i, (lab, h) in enumerate(rows):
            if i:
                c._ln((x0, yy), (x0 + W, yy), 0.2)
            c.text(lab, x0 + 1.5, yy + h / 2 + 0.85, 2.2, bold=(i == 0), chk=False)
            for j, no in enumerate(nos):
                s = S[no]
                cx = x0 + lab_w + cw * (j + 0.5)
                ty = yy + h / 2 + 0.85
                if i == 0:
                    c.diamond(cx, yy + h / 2, no, r=2.7)
                elif i == 1:
                    ln = textwrap.wrap(s["name"].replace(" (normally no flow)", " (NNF)"), int(cw / 1.38))[:2]
                    for k, t in enumerate(ln):
                        c.text(t, cx, yy + 3.0 + k * 2.7, 2.2, "middle", chk=False)
                elif i == 2:
                    c.text(phase.get(s["phase"], s["phase"]), cx, ty, 2.2, "middle", chk=False)
                elif i == 3:
                    c.text(f"{s['total_kg_h']:,.0f}", cx, ty, 2.2, "middle", chk=False)
                elif i == 4:
                    c.text(f"{s['T_C']:.0f}", cx, ty, 2.2, "middle", chk=False)
                elif i == 5:
                    p = s["P_barg"]
                    c.text(f"{p:.2f}" if p < 0 else f"{p:.1f}", cx, ty, 2.2, "middle", chk=False)
                elif i == 6:
                    c.text(f"{s['bpsd']:,.0f}" if s.get("bpsd") else "-", cx, ty, 2.2, "middle", chk=False)
                elif i == 7:
                    v = s.get("vf_mass")
                    c.text("-" if v is None else f"{v:.3f}" if 0 < v < 1 else f"{v:.0f}", cx, ty, 2.2,
                           "middle", chk=False)
                elif i == 8:
                    mw = s.get("mw")
                    c.text(f"{mw:.1f}" if mw else "-", cx, ty, 2.2, "middle", chk=False)
            yy += h
        for j in range(len(nos) + 1):
            xx = x0 + lab_w + cw * j
            c._ln((xx, y0), (xx, y0 + H), 0.2)
        c.reg(x0, y0, x0 + W, y0 + H, "table")

    # ------------------------------------------------------------- legend
    def _legend(self):
        c = self.c
        x0 = 651.0
        w = 175.0
        h = 30.0
        y1 = self.sh._notes_bottom - 1
        y0 = y1 - h
        c.gs.add(c.d.rect((x0, y0), (w, h), fill="white", stroke="black", stroke_width=0.3))
        c.text("LEGEND", x0 + 2, y0 + 4, 2.6, bold=True, chk=False)
        a, b2, b3 = x0 + 3, x0 + 62, x0 + 124
        r = [y0 + 9.5, y0 + 15.0, y0 + 20.5, y0 + 26.0]
        c.diamond(a + 3.5, r[0], "00", r=2.8)
        c.text("H&MB STREAM No.", a + 9, r[0] + 0.8, 2.2, chk=False)
        c.flag(a + 5, r[1], "000 " + DEG, "T")
        c.text("TEMPERATURE", a + 13, r[1] + 0.8, 2.2, chk=False)
        c.flag(a + 5, r[2], "0.0 barg", "P")
        c.text("PRESSURE", a + 13, r[2] + 0.8, 2.2, chk=False)
        c.bubble(a + 3.8, r[3] + 0.3, "FIC-000", r=3.8)
        c.text("DCS CONTROLLER", a + 9, r[3] + 1.0, 2.2, chk=False)
        c._ln((b2, r[0]), (b2 + 10, r[0]), 0.25, dash="1.6,0.9")
        c.text("INSTRUMENT SIGNAL", b2 + 13, r[0] + 0.8, 2.2, chk=False)
        c.cv(b2 + 5, r[1] + 1.2)
        c.text("CONTROL VALVE", b2 + 13, r[1] + 0.8, 2.2, chk=False)
        c.offsheet(b2, r[3] - 1.2, "R", "SERVICE", "TO PFD-00X", w=26, h=7.2)
        c.text("OFF-SHEET", b2 + 29, r[3] - 1.8, 2.2, chk=False)
        c.text("CONNECTOR", b2 + 29, r[3] + 0.9, 2.2, chk=False)
        for i, (wd, dash, t) in enumerate([(0.6, None, "MAIN PROCESS"), (0.42, None, "SECONDARY PROCESS"),
                                           (0.32, None, "UTILITY"), (0.42, "4,1.2", "FLUE GAS / AIR")]):
            kw = dict(stroke="black", stroke_width=wd)
            if dash:
                kw["stroke_dasharray"] = dash
            c.gs.add(c.d.line((b3, r[i]), (b3 + 10, r[i]), **kw))
            c.text(t, b3 + 13, r[i] + 0.8, 2.2, chk=False)
        c.reg(x0, y0, x0 + w, y1, "legend")
        self.legend_top = y0

    # ------------------------------------------------------------- loops
    def loop(self, tag, x, y):
        """Draw ISA bubble for a principal control loop (must exist in control_loops.json)."""
        self.D.loop(tag)
        return self.c.bubble(x, y, tag)

    def save(self, check=True):
        self._titles()
        self._table()
        self._legend()
        self.c.finish()
        if check:
            iss = self.c.check(verbose=False)
            if iss:
                print(f"  {self.docno}: {len(iss)} layout warnings")
                for s in iss:
                    print("    ", s)
        stem = OUT / self.docno
        self.sh.save(stem)
        return stem.with_suffix(".pdf")


# ============================================================================ common pieces
def preheat_exchanger(p: PFD, x, Y, tag, hot_in, hot_out, bypass=None, crude_tube=False, dy=70):
    """Preheat exchanger on the crude header at (x, Y). Crude passes W->E; hot medium enters N, leaves S.
    hot_in / hot_out = (connector line 1, connector line 2). bypass = (TIC tag, TV tag)."""
    c, D = p.c, p.D
    e = D.eq(tag)
    xr = D.X[tag]
    n = int(e.get("n_shells", 1))
    h = c.hx(x, Y, r=5.5, tube="h" if crude_tube else "v", shells=n)
    yin, yout = Y - dy, Y + dy
    # inlet connector (FROM) - tip at x-6
    from .symbols import _tw as tw
    w_in = max(tw(hot_in[0], 2.2), tw(hot_in[1], 2.2) * 1.07) + 7
    c.offsheet(x - 6 - w_in, yin, "R", *hot_in, w=w_in)
    c.line([(x - 6, yin), (x, yin), h["N"]], kind="S")
    w_out = max(tw(hot_out[0], 2.2), tw(hot_out[1], 2.2) * 1.07) + 7
    c.line([h["S"], (x, yout), (x + 6, yout)], kind="S")
    c.offsheet(x + 6, yout, "R", *hot_out, w=w_out)
    # flags
    c.flag(x - 8.5, Y - 30, fT(xr["Th_in"]), "T", anchor="middle")
    c.flag(x - 8.5, Y + 30, fT(xr["Th_out"]), "T")
    c.flag(x + 33, Y - 5, fT(xr["Tc_out"]), "T")
    # tag + duty label at exchanger
    c.text(disp_tag(D, tag), x - 6.5, Y - 9.0, 2.6, "end", bold=True)
    c.text(f"{xr['Q_kw'] / 1000:.1f} MW", x - 6.5, Y + 10.0, 2.2, "end")
    if bypass:
        tic, tv = bypass
        xb = x + 14
        yb1, yb2 = yin + 15, yout - 18
        c.line([(x, yb1), (xb, yb1), (xb, yb2), (x, yb2)], kind="S")
        act = c.cv(xb, Y - 30, orient="v", act="right", tag=tv, tag_side="left")
        b = p.loop(tic, x + 24, yb2 + 5)
        c.sig([b["W"], (x, yb2 + 5)])
        c.sig([b["N"], (x + 24, Y - 30), act])
    return h


def osbl(p, x, y, direction, l1, l2):
    """OSBL / off-sheet connector; returns attach point (base for FROM 'R', tip for TO)."""
    return p.c.offsheet(x, y, direction, l1, l2)


# ============================================================================ SHEET 1
def sheet1(D):
    p = PFD(D, "CFU-100-PR-PFD-001", "CRUDE CHARGE, COLD PREHEAT & DESALTING",
            ["Cold preheat train E-101..E-105 crude shell-side except E-105 (crude tube-side).",
             "Desalter mix valves PDV-1005/1006 set at 0.5-1.5 bar dP; 2-stage counter-current wash.",
             "Chemical packages X-101 (demulsifier) and X-102 (caustic) ratio-controlled to FIC-1001."], 1)
    c = p.c
    Y = 175.0
    # ---- crude in, P-101
    yin = Y + 2.8
    con = c.offsheet(15, yin, "R", "CRUDE FROM TANKAGE", "FROM OSBL")
    p.stream("1", con["tip"][0] + 7, yin)
    pm = c.pump(80, yin)
    c.line([con["tip"], pm["suc"]])
    c.text("P-101A/B", 80, yin + 9.5, 2.5, "middle", bold=True)
    c.flag(62, yin + 9, fT(D.T("1")), "T")
    # FV-1001 + FIC-1001
    act = c.cv(97, Y, tag="FV-1001")
    b = p.loop("FIC-1001", 97, Y - 19)
    c.sig([b["S"], act])
    # X-101 demulsifier
    pk = c.package(102, 123, 22, 11, ["X-101", "DEMULSIFIER"])
    c.line([pk["S"], (113, Y)], kind="U")
    # ---- cold train
    xs = [140, 205, 270, 335, 400]
    trains = [
        ("E-101", ("TPA FROM P-106", "FROM PFD-003"), ("TPA RETURN TO C-101", "TO PFD-003"), ("TIC-1041", "TV-1041")),
        ("E-102", ("KEROSENE FROM P-109", "FROM PFD-003"), ("KEROSENE TO A-103", "TO PFD-003"), None),
        ("E-103", ("LVGO FROM P-201", "FROM PFD-005"), ("LVGO TO A-201", "TO PFD-005"), None),
        ("E-104", ("DIESEL FROM E-107", "FROM PFD-002"), ("DIESEL TO A-104", "TO PFD-003"), None),
        ("E-105", ("VAC. RESIDUE FROM E-111", "FROM PFD-002"), ("VAC. RESIDUE TO E-201", "TO PFD-005"), None),
    ]
    hs = []
    for x, (tag, hi, ho, byp) in zip(xs, trains):
        hs.append(preheat_exchanger(p, x, Y, tag, hi, ho, byp, crude_tube=(tag == "E-105")))
    c.line([pm["dis"], hs[0]["W"]])
    for a, b2 in zip(hs[:-1], hs[1:]):
        c.line([a["E"], b2["W"]])
    # E-105 crude bypass TV-1004
    xa, xb = xs[4] - 17, xs[4] + 17
    c.line([(xa, Y), (xa, Y + 22), (xb, Y + 22), (xb, Y)], kind="S", arrow=False)
    act = c.cv(xs[4] + 7, Y + 22, act="down", tag="TV-1004", tag_side="belowright")
    # ---- to desalter D-101A
    xd = 452.0
    yd = 335.0
    D1 = c.hvessel(505, yd, 96, 20, internals="grid", tag="D-101A")
    D2 = c.hvessel(650, yd, 96, 20, internals="grid", tag="D-101B")
    c.text("D-101A", 505, yd - 13, 2.8, "middle", bold=True)
    c.text("D-101B", 650, yd - 13, 2.8, "middle", bold=True)
    ymix = yd + 22
    c.line([hs[4]["E"], (xd, Y), (xd, ymix), (D1["x0"] + 18, ymix), (D1["x0"] + 18, D1["y1"])])
    p.stream("2", xd - 14, Y)
    b = p.loop("TIC-1004", xd + 13, Y + 34)
    c.sig([b["W"], (xd, Y + 34)])
    c.sig([b["S"], (xd + 13, Y + 52), (xs[4] + 7, Y + 52), act])
    # mix valve PDV-1005 on vertical
    act = c.cv(xd, 300, orient="v", act="right", tag="PDV-1005", tag_side="left")
    b = p.loop("PDIC-1005", xd + 14, 300)
    c.sig([b["W"], act])
    c.text("MIX VALVE", xd - 3, 306.5, 2.2, "end")
    # D-101A -> D-101B
    xm2 = 578.0
    c.line([D1["top"](D1["x1"] - 16), (D1["x1"] - 16, 295), (xm2, 295), (xm2, ymix), (D2["x0"] + 18, ymix),
            (D2["x0"] + 18, D2["y1"])])
    c.cv(xm2, 318, orient="v", act="right", tag="PDV-1006", tag_side="left")
    c.text("MIX VALVE", xm2 - 3, 324.5, 2.2, "end")
    c.flag(D1["x0"] + 26, yd - 15, fP(float(D.eq("D-101A")["op_P"])), "P")
    c.flag(D1["x0"] + 26, yd - 20.5, fT(float(D.eq("D-101A")["op_T"])), "T")
    # ---- desalted crude -> PV-1009 -> P-102
    ydc = 295.0
    ys = ydc + 2.8
    act = c.cv(712, ys, act="down", tag="PV-1009", tag_side="above")
    b = p.loop("PIC-1009", 712, ys + 19)
    c.sig([b["N"], act])
    c.sig([b["W"], (D2["x1"] - 16, ys + 19)])
    p.stream("5", 730, ys)
    pk2 = c.package(733, 255, 22, 11, ["X-102", "CAUSTIC"])
    c.line([pk2["S"], (744, ys)], kind="U")
    pm2 = c.pump(762, ys)
    c.line([D2["top"](D2["x1"] - 16), (D2["x1"] - 16, ys), pm2["suc"]])
    c.text("P-102A/B", 762, ydc + 12.5, 2.5, "middle", bold=True)
    con = c.offsheet(pm2["dis"][0] + 4, ydc, "R", "DESALTED CRUDE TO E-106", "TO PFD-002", w=None)
    c.line([pm2["dis"], (pm2["dis"][0] + 4, ydc)], arrow=False)
    c.flag(728, ydc - 6, fP(D.S["5"]["P_barg"]), "P")
    # ---- brine: D-101A boot -> LV-1007 -> E-118 -> WWT
    yb = 470.0
    xbr = D1["x1"] - 20
    act = c.cv(xbr, 385, orient="v", act="right", tag="LV-1007", tag_side="left")
    b = p.loop("LIC-1007", xbr + 18, 368)
    c.sig([b["W"], (D1["x1"] - 9, 368), (D1["x1"] - 9, D1["y1"] - 3)])
    c.sig([b["S"], (xbr + 18, 385), act])
    hx = c.hx(250, yb, tube="h")
    c.text("E-118", 244, yb + 10.5, 2.6, "end", bold=True)
    c.line([D1["bot"](xbr), (xbr, yb), hx["E"]], kind="S")
    con = c.offsheet(15, yb, "L", "DESALTER BRINE TO WWT", "TO OSBL")
    c.line([hx["W"], con["base"]], kind="S")
    p.stream("4", con["base"][0] + 10, yb)
    c.flag(hx["W"][0] - 22, yb - 6, fT(D.S["4"]["T_C"]), "T")
    # ---- wash water: OSBL -> P-114 -> FV-1003 -> E-118 -> 2nd stage mix
    yw = 432.0
    con = c.offsheet(15, yw + 2.8, "R", "WASH WATER", "FROM OSBL")
    pw = c.pump(85, yw + 2.8)
    c.text("P-114A/B", 85, yw + 12.3, 2.5, "middle", bold=True)
    c.line([con["tip"], pw["suc"]], kind="S")
    act = c.cv(110, yw, tag="FV-1003")
    b = p.loop("FFIC-1003", 110, yw - 18)
    c.sig([b["S"], act])
    c.text("RATIO TO FIC-1001", 116, yw - 22, 2.2)
    p.stream("3", 128, yw)
    c.line([pw["dis"], (250, yw), hx["N"]], kind="S")
    c.line([hx["S"], (250, 492), (xm2 + 14, 492), (xm2 + 14, 306), (xm2, 306)], kind="S")
    c.flag(275, 492 - 5, fT(D.S["3"]["T_C"]), "T")
    # ---- D-101B brine -> LV-1008 -> P-118 -> 1st stage mix
    xr2 = D2["x1"] - 20
    c.cv(xr2, 372, orient="v", act="right", tag="LV-1008", tag_side="left")
    pr = c.pump(xr2 - 14, 400, face="L")
    c.line([D2["bot"](xr2), (xr2, 400), pr["suc"]], kind="S")
    c.text("P-118", xr2 - 14, 410, 2.5, "middle", bold=True)
    c.line([pr["dis"], (436, pr["dis"][1]), (436, 280), (xd, 280)], kind="S")
    # titles
    for tag, x in [("P-101A/B", 80), ("X-101", 113), ("E-101", 140), ("E-102", 205), ("E-103", 270),
                   ("E-104", 335), ("E-105", 400), ("D-101A", 505), ("D-101B", 650), ("P-102A/B", 762),
                   ("X-102", 744), ("P-114A/B", 85), ("E-118", 250), ("P-118", 690)]:
        p.title(tag, x)
    return p.save()


# ============================================================================ SHEET 2
def sheet2(D):
    p = PFD(D, "CFU-100-PR-PFD-002", "HOT PREHEAT TRAIN & ATMOSPHERIC HEATER H-101",
            ["H-101: 2-cell cabin, 8 parallel passes (convection then radiant); one pass shown typical "
             "(FIC-1011..1018).",
             "TDIC-1019 balances pass outlet temperatures by biasing pass flow set points, total flow held.",
             "COT TIC-1020 cascades to fuel gas pressure PIC-1021; O2 trim AIC-1022 on FD fan vanes."], 2)
    c = p.c
    Y = 175.0
    con = c.offsheet(15, Y, "R", "DESALTED CRUDE FROM P-102", "FROM PFD-001")
    xs = [100, 165, 230, 295, 360, 425]
    trains = [
        ("E-106", ("MPA FROM P-107", "FROM PFD-003"), ("MPA RETURN TO C-101", "TO PFD-003"), ("TIC-1043", "TV-1043")),
        ("E-107", ("DIESEL FROM P-110", "FROM PFD-003"), ("DIESEL TO E-104", "TO PFD-001"), None),
        ("E-108", ("HVGO FROM P-202", "FROM PFD-005"), ("HVGO TO C-201 / A-202", "TO PFD-005"), ("TIC-2017", "TV-2017")),
        ("E-109", ("AGO FROM P-111", "FROM PFD-003"), ("AGO TO A-105", "TO PFD-003"), None),
        ("E-110", ("BPA FROM P-108", "FROM PFD-003"), ("BPA TO E-113", "TO PFD-003"), None),
        ("E-111", ("VAC. RESIDUE FROM P-204", "FROM PFD-005"), ("VAC. RESIDUE TO E-105", "TO PFD-001"), None),
    ]
    hs = [preheat_exchanger(p, x, Y, *t, crude_tube=(t[0] == "E-111")) for x, t in zip(xs, trains)]
    c.line([con["tip"], hs[0]["W"]])
    c.flag(con["tip"][0] + 10, Y - 5, fT(D.X["E-106"]["Tc_in"]), "T")
    for a, b2 in zip(hs[:-1], hs[1:]):
        c.line([a["E"], b2["W"]])
    h1 = D.R["heaters"]["H-101"]
    npass = int(h1["passes"])
    # ---- heater geometry
    rx0, rx1, ry0, ry1 = 520.0, 640.0, 305.0, 420.0
    cvx0, cvx1, cvy0, cvy1 = 545.0, 615.0, 222.0, 300.0
    xm = (rx0 + rx1) / 2
    c.heater_box(rx0, ry0, (rx1 - rx0) / 2 - 2, ry1 - ry0)
    c.heater_box(xm + 2, ry0, (rx1 - rx0) / 2 - 2, ry1 - ry0)
    c._poly([(rx0, ry0), (cvx0, cvy1), (cvx1, cvy1), (rx1, ry0)], w=0.5)
    c.heater_box(cvx0, cvy0, cvx1 - cvx0, cvy1 - cvy0)
    c.reg(rx0, cvy1, rx1, ry0, "hood")
    for xx in (rx0 + 4, xm - 6, xm + 6, rx1 - 4):
        c.coil_v(xx, ry0 + 6, ry1 - 14, n=12)
    for yy in range(int(cvy0 + 18), int(cvy1 - 3), 7):
        c.coil_h(cvx0 + 4, cvx1 - 4, yy, amp=1.2, n=14)
    c.coil_h(cvx0 + 4, cvx1 - 4, cvy0 + 6, amp=1.2, n=14)
    c.text("SS COIL", xm, cvy0 + 13.0, 2.2, "middle", chk=False)
    c.text("CONVECTION", cvx0 - 2, cvy1 - 1.5, 2.2, "end")
    for k, x0c in enumerate((rx0, xm + 2)):
        cx = x0c + ((rx1 - rx0) / 2 - 2) / 2
        c.text(f"RADIANT CELL {'AB'[k]}", cx, ry0 + 60, 2.4, "middle", chk=False)
        for j in range(4):
            c.burner(x0c + 9 + j * 12.5, ry1)
    c.text("H-101", rx0 - 4, ry0 + 40, 3.4, "end", bold=True)
    c.text(f"{h1['Q_abs_kw'] / 1000:.1f} MW ABS.", rx0 - 4, ry0 + 45, 2.4, "end")
    c.text(f"{h1['Q_fired_kw'] / 1000:.1f} MW FIRED", rx0 - 4, ry0 + 49.5, 2.2, "end")
    c.text(f"{h1['burners']} BURNERS", rx0 - 4, ry0 + 54, 2.2, "end")
    c.text(f"{h1['passes']} PASSES", rx0 - 4, ry0 + 58.5, 2.2, "end")
    # stack + flue gas / air system
    sx, sy_top = 580.0, 88.0
    c.stack(sx, cvy0, sy_top, wb=14, wt=9)
    def sedge(y):
        return sx + 7 - 2.5 * (cvy0 - y) / (cvy0 - sy_top)
    c._ln((sx - 5, 160), (sx + 5, 160), 0.5)
    c._circle((sx, 160), 0.8, fill="black")
    c.text("STACK DAMPER", sx - 7, 161, 2.2, "end")
    aph = c.air_preheater(745, 200, w=16, h=26)
    c.text("E-120", 755, 220, 2.6, bold=True)
    yfg = 200.0
    c.line([(sedge(yfg), yfg), aph["W"]], kind="FG")
    idf = c.fan(795, yfg, face="R", up=True)
    c.text("K-102A/B", 800, yfg + 9, 2.5, "start", bold=True)
    c.line([aph["E"], idf["suc"]], kind="FG")
    c.line([idf["dis"], (idf["dis"][0], 110), (sedge(110), 110)], kind="FG")
    c.text("FLUE GAS", 680, yfg - 1.5, 2.2, "middle")
    fdf = c.fan(718, 150, face="R")
    c.text("K-101A/B", 718, 141, 2.5, "middle", bold=True)
    c.line([(698, 150), fdf["suc"]], kind="FG")
    c.text("AIR", 696, 151, 2.4, "end")
    c.line([fdf["dis"], (745, fdf["dis"][1]), aph["N"]], kind="FG")
    ypl = 432.0
    c.gs.add(c.d.rect((rx0, ry1 + 4), (rx1 - rx0, 8), fill="white", stroke="black", stroke_width=0.35))
    c.text("COMBUSTION AIR PLENUM", xm, ry1 + 9, 2.2, "middle", chk=False)
    c.reg(rx0, ry1 + 4, rx1, ry1 + 12, "plenum")
    c.line([aph["S"], (745, ry1 + 8), (rx1, ry1 + 8)], kind="FG")
    c.text("HOT AIR", 747, 300, 2.2)
    # ---- passes
    y_p = [cvy0 + 26 + 6.6 * i for i in range(npass)]
    y_p = [cvy0 + 22 + (cvy1 - cvy0 - 26) * i / (npass - 1) for i in range(npass)]
    xh = 485.0
    p.stream("6", 450, Y)
    c.flag(450, Y - 9, "CIT " + fT(D.R["preheat"]["CIT"]), "T")
    c.flag(450, Y + 9, fP(D.S["6"]["P_barg"]), "P")
    c.line([hs[-1]["E"], (xh, Y), (xh, y_p[-1])], arrow=False)
    for i, yy in enumerate(y_p):
        c.line([(xh, yy), (cvx0, yy)], kind="S")
        a = c.cv(510, yy, tag=None)
        if i == 0:
            b = p.loop("FIC-1011", 510, yy - 13)
            c.sig([b["S"], a])
    c.text(f"{npass} PASSES", xh - 3, y_p[-1] + 7, 2.2, "end")
    c.text("FV-1011...FV-1018", xh - 3, y_p[-1] + 10, 2.2, "end")
    # outlet manifold
    xo = 664.0
    y_o = [ry0 + 18 + 7 * i for i in range(npass)]
    for yy in y_o:
        c.line([(rx1, yy), (xo, yy)], kind="S", arrow=False)
    yt = 398.0
    c.line([(xo, y_o[0]), (xo, yt), (775, yt)])
    b = p.loop("TDIC-1019", 683, y_o[2])
    c.sig([b["W"], (xo, y_o[2])])
    c.text("TI-1011...1018 PASS OUTLETS", 690, y_o[2] - 6.5, 2.2)
    c.text("BIAS TO FIC-1011...1018", 690, y_o[2] + 8.5, 2.2)
    con = c.offsheet(775, yt, "R", "TRANSFER LINE TO C-101", "TO PFD-003")
    p.stream("7", 700, yt)
    c.flag(712, yt - 6, "COT " + fT(D.R["atm"]["cot"]), "T")
    c.flag(712, yt + 6, fP(D.S["7"]["P_barg"]), "P")
    b_tic = p.loop("TIC-1020", 728, yt + 15)
    c.sig([b_tic["N"], (728, yt)])
    # ---- SS coil
    lp = basis.UTILITIES["lp_steam"]
    con = c.offsheet(624, cvy0 + 4, "L", f"LP STEAM {lp['P_barg']:g} barg", "FROM UTILITIES")
    c.line([con["tip"], (cvx1, cvy0 + 4)], kind="U")
    c.line([(cvx1, cvy0 + 10), (632, cvy0 + 10), (632, 292), (662, 292)], kind="U")
    con = c.offsheet(662, 292, "R", "STRIPPING STEAM", "TO PFD-003")
    p.stream("20", 632, 281)
    c.flag(646, 281, fT(D.T("20")), "T")
    # ---- draft / O2
    b = p.loop("AIC-1022", 652, 258)
    c.sig([b["W"], (cvx1, 258)])
    c.sig([b["E"], (705, 258), (705, 165), (718, 165), (718, 154.5)])
    b = p.loop("PIC-1023", 652, 274)
    c.sig([b["W"], (cvx1, 274)])
    c.sig([b["E"], (795, 274), (795, 204.5)])
    c.text("TO VANES", 707, 170, 2.2)
    c.text("TO SPEED", 797, 240, 2.2)
    # ---- fuel gas
    fg = basis.UTILITIES["fuel_gas"]
    yfg2 = 488.0
    con = c.offsheet(300, yfg2, "R", "FUEL GAS", "FROM OSBL")
    a = c.cv(355, yfg2, tag="PV-9001")
    b = p.loop("PIC-9001", 355, yfg2 - 17)
    c.sig([b["S"], a])
    dk = c.vvessel(400, yfg2 - 10, 12, 28, tag="D-103", mesh=True)
    c.text("D-103", 392, yfg2 + 9, 2.6, "end", bold=True)
    c.line([con["tip"], (dk["x0"], yfg2)], kind="S")
    c.sig([b["E"], (400 - 10, yfg2 - 17)])
    yh = 450.0
    c.line([dk["top"], (400, yh), (rx0 - 6, yh)], kind="S", arrow=False)
    p.stream("34", 420, yh)
    c.flag(420, yh - 7, f"{fg['P_barg']:g} barg", "P")
    c.line([(440, yh), (440, 505), (455, 505)], kind="S")
    c.offsheet(455, 505, "R", "FUEL GAS TO H-201", "TO PFD-005")
    a = c.cv(475, yh, tag="PV-1021", tag_side="below")
    b = p.loop("PIC-1021", 475, yh - 17)
    c.sig([b["S"], a])
    c.sig([b_tic["S"], (728, 442), (485, 442), (485, yh - 17), b["E"]])
    c.line([(rx0 - 6, yh), (rx1 - 6, yh)], kind="S", arrow=False)
    for k, x0c in enumerate((rx0, xm + 2)):
        for j in range(4):
            bx = x0c + 9 + j * 12.5
            c.line([(bx, yh), (bx, ry1 + 12)], kind="U", hop=False)
    c.text("FUEL GAS HEADER", rx0 + 2, yh + 4.5, 2.2)
    for tag, x in [("E-106", 100), ("E-107", 165), ("E-108", 230), ("E-109", 295), ("E-110", 360),
                   ("E-111", 425), ("H-101", 580), ("D-103", 400), ("E-120", 745), ("K-101A/B", 700),
                   ("K-102A/B", 795)]:
        p.title(tag, x)
    return p.save()

# ============================================================================ SHEET 3
def sheet3(D):
    p = PFD(D, "CFU-100-PR-PFD-003", "ATMOSPHERIC COLUMN C-101, PUMPAROUNDS & SIDE STRIPPERS",
            ["C-101 trays numbered top-down. Pumparound heat recovered in preheat trains (PFD-001/002).",
             "Side-stripper draw rates (FIC-1050/1060/1070) set cut points; product rate on stripper level.",
             "Stripping steam is LP steam superheated in H-101 convection (stream 20)."], 3)
    c = p.c
    A = D.R["atm"]
    tr = A["tray"]
    cx, ytop, w, wb = 240.0, 86.0, 40.0, 26.0
    ybot = 478.0
    y35, ysw = 372.0, 394.0

    def ty(t):
        if t <= 35:
            return 104.0 + (t - 1) * (y35 - 104.0) / 34
        return 404.0 + (t - 36) * 9.5

    trays = []
    shown = sorted({1, tr["TPA_draw"], tr["KERO"], tr["MPA_ret"], tr["MPA_draw"], tr["DIESEL"], tr["BPA_ret"],
                    tr["BPA_draw"], tr["AGO"], tr["wash_bot"], 6, 18, 29, 36, 41})
    for k, t in enumerate(shown):
        trays.append((ty(t), "L" if k % 2 else "R", str(t)))
    col = c.column(cx, ytop, w, ybot - ytop, w_bot=wb, y_swage=ysw, trays=trays, tag="C-101")
    xl, xr = col["xl"], col["xr"]
    c.text("C-101", cx + 22, ytop + 3, 3.0, "start", bold=True)
    c.text("FLASH ZONE", cx, y35 + 14, 2.2, "middle", chk=False)
    # ---- overhead + reflux
    yoh = 74.0
    c.line([col["top"], (cx, yoh), (420, yoh)])
    c.offsheet(420, yoh, "R", "OVERHEAD VAPOUR TO A-101", "TO PFD-004")
    p.stream("8", 300, yoh)
    c.flag(330, yoh - 6, fT(A["T_top"]), "T")
    c.flag(330, yoh + 6, fP(A["P_top_barg"]), "P")
    yrf = ty(1) - 4
    con = c.offsheet(395, yrf, "L", "REFLUX FROM P-103", "FROM PFD-004")
    c.line([con["tip"], (xr, yrf)])
    p.stream("10", 372, yrf)
    a = c.cv(300, yrf, tag="FV-1031", tag_side="below")
    bf = p.loop("FIC-1031", 300, yrf - 13)
    c.sig([bf["S"], a])
    bt = p.loop("TIC-1030", 205, 96)
    c.sig([bt["E"], (xl, 96)])
    c.sig([bt["N"], (205, 68), (288, 68), (288, yrf - 13), bf["W"]])
    # ---- pumparounds (left)
    pa = A["pa"]
    xpv, xpp = 197.0, 182.0
    pas = [("TPA", "13", "P-106", "FIC-1040", ("TPA TO E-101", "TO PFD-001"), ("TPA RETURN FROM E-101", "FROM PFD-001")),
           ("MPA", "14", "P-107", "FIC-1042", ("MPA TO E-106", "TO PFD-002"), ("MPA RETURN FROM E-106", "FROM PFD-002")),
           ("BPA", "15", "P-108", "FIC-1044", ("BPA TO E-110", "TO PFD-002"), None)]
    for k, (nm, no, ptag, fic, cto, cfrom) in enumerate(pas):
        yd, yr = ty(pa[nm]["draw_tray"]), ty(pa[nm]["ret_tray"])
        if nm == "TPA":
            yr = ty(1) + 4
        yp = yd + 22
        pm = c.pump(xpp, yp, face="L")
        c.line([(xl, yd), (xpv, yd), (xpv, yp), pm["suc"]])
        p.stream(no, 208, yd)
        c.flag(208, yd - 6, fT(pa[nm]["T_draw"]), "T")
        c.text(ptag + "A/B", xpp, yp + 9.5, 2.5, "middle", bold=True)
        ydis = pm["dis"][1]
        a = c.cv(140, ydis, act="down", tag=None)
        c.text(fic.replace("FIC", "FV"), 140, ydis - 3, 2.2, "middle")
        b = p.loop(fic, 140, ydis + 17)
        c.sig([b["N"], a])
        con = c.offsheet(15, ydis, "L", *cto)
        c.line([pm["dis"], con["base"]])
        if cfrom:
            con = c.offsheet(15, yr, "R", *cfrom)
            c.line([con["tip"], (xl, yr)])
            c.flag(185, yr - 5.5, fT(pa[nm]["T_ret"]), "T")
        c.text(f"{nm}  {pa[nm]['duty_kw'] / 1000:.1f} MW", 120, yd + 1 if nm != "TPA" else yd + 2, 2.4, "middle",
               bold=True)
    # BPA return through E-113 (MP steam generator) with TV-1045 bypass
    yr = ty(pa["BPA"]["ret_tray"])
    yin = yr - 30
    k = c.kettle(115, yr - 13, L=28, D=11)
    con = c.offsheet(15, yin, "R", "BPA FROM E-110", "FROM PFD-002")
    xt = k["tin_top"][0]
    c.line([con["tip"], (xt, yin), k["tin_top"]], kind="S")
    c.line([k["tout_bot"], (xt, yr), (xl, yr)], kind="S")
    c.flag(185, yr - 5.5, fT(pa["BPA"]["T_ret"]), "T")
    c.line([(80, yin), (80, yr + 6), (xt + 9, yr + 6), (xt + 9, yr)], kind="S")
    a = c.cv(80, yr - 12, orient="v", act="right", tag="TV-1045", tag_side="left")
    b = p.loop("TIC-1045", 166, yr - 11)
    c.sig([b["S"], (166, yr)])
    c.sig([b["N"], (166, yin + 6), (90, yin + 6), (90, yr - 12), a])
    mp = basis.UTILITIES["mp_steam"]
    c.line([k["vap"], (k["vap"][0], yin - 8)], kind="U")
    c.text(f"MP STEAM {mp['P_barg']:g} barg", k["vap"][0] + 2, yin - 6, 2.2)
    c.line([(k["x1"] + 12, yr - 10), (k["x1"], yr - 10)], kind="U")
    c.text("BFW", k["x1"] + 13, yr - 9.2, 2.2)
    c.text("E-113", k["x0"] - 1, yr - 21, 2.6, "end", bold=True)
    tq = D.TR["E-113"]
    c.text(f"{tq['Q_kw'] / 1000:.1f} MW", k["x0"] - 1, yr - 2, 2.2, "end")
    # ---- feed (transfer line)
    yfz = y35 + 9
    con = c.offsheet(15, yfz, "R", "TRANSFER LINE FROM H-101", "FROM PFD-002")
    c.line([con["tip"], (xl, yfz)])
    p.stream("7", 120, yfz)
    c.flag(150, yfz - 6, "FZ " + fT(A["T_fz"]), "T")
    c.flag(150, yfz + 6, fP(A["P_fz_barg"]), "P")
    b = p.loop("FI-1080", 205, y35 - 7)
    c.sig([b["E"], (xl, y35 - 7)])
    c.text("OVERFLASH", 199, y35 - 13, 2.2, "end")
    # ---- stripping steam header (stream 20)
    yst = 500.0
    xhs = 286.0
    con = c.offsheet(15, yst, "R", "STRIPPING STEAM FROM H-101", "FROM PFD-002")
    c.line([con["tip"], (xhs, yst), (xhs, 205)], kind="U", arrow=False)
    p.stream("20", 95, yst)
    c.flag(120, yst - 6, fT(D.T("20")), "T")
    xsb = 205.0
    c.line([(xsb, yst), (xsb, ybot - 18), (col["xbl"], ybot - 18)], kind="U")
    a = c.cv(xsb, ybot - 2, orient="v", act="left", tag="FV-1081", tag_side="right")
    b = p.loop("FIC-1081", 186, ybot - 2)
    c.sig([b["E"], a])
    # bottoms / AR
    pm = c.pump(305, ybot + 9.6)
    c.text("P-112A/B", 305, ybot + 19, 2.5, "middle", bold=True)
    c.line([col["bot"], (cx, ybot + 9.6), pm["suc"]])
    c.flag(cx - 9, ybot + 6, fT(A["T_bot"]), "T")
    yar = pm["dis"][1]
    a = c.cv(335, yar, tag="FV-1083", tag_side="below")
    bfa = p.loop("FIC-1083", 335, yar - 15)
    c.sig([bfa["S"], a])
    bl = p.loop("LIC-1082", 268, ybot - 22)
    c.sig([bl["W"], (col["xbr"], ybot - 22)])
    c.sig([bl["E"], (335, ybot - 22), bfa["N"]])
    p.stream("19", 355, yar)
    c.offsheet(368, yar, "R", "ATM. RESIDUE TO H-201", "TO PFD-005")
    c.line([pm["dis"], (368, yar)])
    # ---- side strippers
    xs_ = 335.0
    strip = [("KERO", "C-102", "P-109", "1050", "16", ("KEROSENE TO E-102", "TO PFD-001"),
              ("KEROSENE FROM E-102", "FROM PFD-001"), "A-103", ("KEROSENE TO STORAGE / KHT", "TO OSBL")),
             ("DIESEL", "C-103", "P-110", "1060", "17", ("DIESEL TO E-107", "TO PFD-002"),
              ("DIESEL FROM E-104", "FROM PFD-001"), "A-104", ("DIESEL TO STORAGE / DHT", "TO OSBL")),
             ("AGO", "C-104", "P-111", "1070", "18", ("AGO TO E-109", "TO PFD-002"),
              ("AGO FROM E-109", "FROM PFD-002"), "A-105", ("AGO TO DHT / FCC", "TO OSBL"))]
    for nm, stag, ptag, ln, no, cto, cfrom, actag, cout in strip:
        yd = ty(tr[nm])
        e = D.eq(stag)
        h = 40.0
        y0 = yd - 8
        sv = c.vvessel(xs_, y0 + h / 2, 15, h, tag=stag)
        for j in range(3):
            c._ln((sv["x0"], y0 + 9 + j * 8), (sv["x1"] - 4, y0 + 9 + j * 8), 0.3)
        c.text(stag, sv["x1"] + 2, y0 + 1, 2.6, bold=True)
        # draw
        a = c.cv(304, yd, tag=f"FV-{ln}", tag_side="below")
        c.line([(xr, yd), (sv["x0"], yd)])
        b = p.loop(f"FIC-{ln}", 304, yd - 14)
        c.sig([b["S"], a])
        c.flag(272 + 0, yd - 5, fT(A["T_draw"][nm]), "T", anchor="start")
        # vapour return
        yv = y0 - 9
        c.line([sv["top"], (xs_, yv), (xr, yv)], kind="S")
        # steam
        ysn = y0 + h - 6
        c.line([(xhs, ysn), (sv["x0"], ysn)], kind="U")
        fl = str(int(ln) + 4)
        a = c.cv(296, ysn, act="down", tag=None)
        b = p.loop(f"FIC-{fl}", 296, ysn + 13)
        c.sig([b["N"], a])
        # bottoms -> pump
        yp = y0 + h + 8
        pm = c.pump(xs_ + 18, yp)
        c.line([sv["bot"], (xs_, yp), pm["suc"]])
        c.text(ptag + "A/B", xs_ + 18, yp + 9, 2.5, "middle", bold=True)
        ydis = pm["dis"][1]
        a = c.cv(385, ydis, tag=f"FV-{int(ln) + 2}", tag_side="below")
        bfp = p.loop(f"FIC-{int(ln) + 2}", 385, ydis - 15)
        c.sig([bfp["S"], a])
        blc = p.loop(f"LIC-{int(ln) + 1}", 360, y0 + 14)
        c.sig([blc["W"], (sv["x1"], y0 + 14)])
        c.sig([blc["E"], (385, y0 + 14), bfp["N"]])
        c.flag(372, ydis + 7, fT(A["T_strip_out"][nm]), "T")
        con = c.offsheet(402, ydis, "R", *cto)
        c.line([pm["dis"], (402, ydis)])
        # return from preheat -> air cooler -> product
        con = c.offsheet(500, ydis, "R", *cfrom)
        ac = D.eq(actag)
        acs = c.aircooler(590, ydis, fans=int(ac["fans"]))
        c.line([con["tip"], acs["W"]], kind="S")
        c.text(actag, 590, ydis - 5, 2.6, "middle", bold=True)
        c.text(f"{ac['duty_kw'] / 1000:.1f} MW", 606, ydis - 5, 2.2)
        trm = D.TR.get(actag)
        if trm:
            c.flag(565, ydis - 6, fT(trm["T_in"]), "T")
        p.stream(no, 630, ydis)
        c.flag(645, ydis - 6, fT(D.T(no)), "T")
        c.flag(645, ydis + 6, fP(D.S[no]["P_barg"]), "P")
        con = c.offsheet(665, ydis, "R", *cout)
        c.line([acs["E"], (665, ydis)], kind="S")
    for tag, x in [("C-101", 240), ("P-106A/B", 120), ("P-107A/B", 150), ("P-108A/B", 180), ("E-113", 90),
                   ("P-112A/B", 305), ("C-102", 300), ("C-103", 335), ("C-104", 370), ("P-109A/B", 410),
                   ("P-110A/B", 450), ("P-111A/B", 490), ("A-103", 560), ("A-104", 600), ("A-105", 640)]:
        p.title(tag, x)
    return p.save()

# ============================================================================ SHEET 4
def sheet4(D):
    p = PFD(D, "CFU-100-PR-PFD-004", "ATMOSPHERIC OVERHEAD SYSTEM, STABILISER & NAPHTHA SPLITTER",
            ["D-102 pressure by split range: PV-1032A off-gas to FG/FGR, PV-1032B fuel gas make-up.",
             "C-105 pressure by hot-vapour bypass PV-1091; C-106 by flooded condenser PV-1100.",
             "Reboiler duties set by sensitive-tray temperature cascades (TIC-1095, TIC-1104)."], 4)
    c = p.c
    A, ST, SP = D.R["atm"], D.R["stab"], D.R["split"]
    ut = basis.UTILITIES
    # ---------------- atmospheric overhead
    yoh = 95.0
    con = c.offsheet(15, yoh, "R", "OVERHEAD VAPOUR FROM C-101", "FROM PFD-003")
    p.stream("8", con["tip"][0] + 7, yoh)
    pk = c.package(64, 70, 22, 11, ["X-103", "NEUTRALISER"])
    c.line([pk["S"], (75, yoh)], kind="U")
    a101 = D.eq("A-101")
    ac = c.aircooler(108, yoh, w=34, fans=int(a101["fans"]))
    c.text("A-101", 108, yoh - 5, 2.6, "middle", bold=True)
    c.text(f"{a101['duty_kw'] / 1000:.1f} MW", 108, yoh + 15.5, 2.2, "middle")
    c.line([con["tip"], ac["W"]])
    e115 = D.eq("E-115")
    hx = c.hx(150, yoh, tube="v", shells=int(e115["n_shells"]))
    c.text(disp_tag(D, "E-115"), 157, yoh - 7, 2.6, bold=True)
    c.text(f"{e115['duty_kw'] / 1000:.1f} MW", 157, yoh + 9, 2.2)
    c.line([ac["E"], hx["W"]])
    c.flag(135, yoh - 6, fT(e115["Th_in"]), "T")
    c.line([(150, yoh - 16), hx["N"]], kind="U")
    c.text("CWS", 150, yoh - 17.5, 2.2, "middle")
    c.line([hx["S"], (150, yoh + 16)], kind="U")
    c.text("CWR", 150, yoh + 19, 2.2, "middle")
    d2 = c.hvessel(195, 162, 64, 18, boot=(212, 9, 11), tag="D-102", weir=True)
    c.text("D-102", 195, 162 + 1, 2.8, "middle", bold=True, chk=False)
    c.line([hx["E"], (186, yoh), (186, d2["y0"])])
    c.flag(200, d2["y0"] - 12, fT(D.T("10")), "T")
    c.flag(200, d2["y0"] - 6.5, fP(A["drum_P_barg"]), "P")
    # off-gas / FG make-up (split range)
    yog, ymk = 125.0, 138.0
    con = c.offsheet(15, yog, "L", "OFF-GAS TO FUEL GAS / FGR", "TO OSBL")
    c.line([d2["top"](167), (167, yog), con["base"]], kind="S")
    a1 = c.cv(118, yog, tag="PV-1032A", tag_side="belowleft")
    p.stream("9", 92, yog)
    con = c.offsheet(15, ymk, "R", "FUEL GAS MAKE-UP", "FROM OSBL")
    c.line([con["tip"], (176, ymk), (176, d2["y0"])], kind="U")
    a2 = c.cv(118, ymk, act="down", tag="PV-1032B", tag_side="belowright")
    b = p.loop("PIC-1032", 98, ymk + 14)
    c.sig([b["E"], (118, ymk + 14), a2])
    c.sig([b["W"], (84, ymk + 14), (84, yog - 9), (118, yog - 9), a1])
    c.sig([b["S"], (98, 158), (d2["x0"] + 1, 158)])
    c.text("SPLIT RANGE", 92, ymk + 22, 2.2, "middle")
    # HC to P-103 / P-104
    xh = 172.0
    yrf, ynp = 205.0, 333.0
    c.line([d2["bot"](xh), (xh, ynp)], arrow=False)
    p103 = c.pump(150, yrf, face="L")
    c.line([(xh, yrf), p103["suc"]])
    c.text("P-103A/B", 150, yrf + 9, 2.5, "middle", bold=True)
    con = c.offsheet(15, p103["dis"][1], "L", "REFLUX TO C-101", "TO PFD-003")
    c.line([p103["dis"], con["base"]])
    p.stream("10", 100, p103["dis"][1])
    c.flag(100, p103["dis"][1] + 7, fP(D.S["10"]["P_barg"]), "P")
    p104 = c.pump(200, ynp)
    c.line([(xh, ynp), p104["suc"]])
    c.text("P-104A/B", 200, ynp + 9, 2.5, "middle", bold=True)
    yn = p104["dis"][1]
    a = c.cv(230, yn, tag="FV-1034")
    bf = p.loop("FIC-1034", 230, yn - 17)
    c.sig([bf["S"], a])
    bl = p.loop("LIC-1033", 148, 168)
    c.sig([bl["E"], (d2["x0"] + 1, 168)])
    c.sig([bl["S"], (148, 180), (128, 180), (128, yn - 17), bf["W"]])
    p.stream("11", 255, yn)
    c.flag(270, yn + 7, fT(D.T("11")), "T")
    # sour water
    p105 = c.pump(236, 200)
    c.line([d2["boot"], (212, 200), p105["suc"]], kind="S")
    c.text("P-105A/B", 236, 209, 2.5, "middle", bold=True)
    ysw = p105["dis"][1]
    a = c.cv(256, ysw, tag="LV-1035", tag_side="below")
    b = p.loop("LIC-1035", 230, 182)
    c.sig([b["W"], (216.5, 182)])
    c.sig([b["E"], (256, 182), a])
    p.stream("12", 270, ysw)
    con = c.offsheet(282, ysw, "R", "SOUR WATER TO SWS", "TO OSBL")
    c.line([p105["dis"], (282, ysw)], kind="S")
    # ---------------- stabiliser C-105
    e105 = D.eq("C-105")
    cx5, top5, h5, w5 = 390.0, 100.0, 225.0, 22.0
    nt5 = int(ST["N_actual"])

    def t5(t):
        return top5 + 14 + (t - 1) * (h5 - 30) / (nt5 - 1)
    trays = [(t5(t), "L" if t % 2 else "R", str(t) if t in (1, int(ST["feed_stage"]), nt5, 15) else "")
             for t in (1, 4, 8, 12, int(ST["feed_stage"]), 15, nt5)]
    col5 = c.column(cx5, top5, w5, h5, trays=trays, tag="C-105")
    c.text("C-105", cx5 - 13, top5 + 4, 2.8, "end", bold=True)
    hx114 = c.hx(345, 300, tube="h")
    c.text("E-114", 337, 292, 2.6, "end", bold=True)
    e114 = D.eq("E-114")
    c.text(f"{e114['duty_kw'] / 1000:.1f} MW", 337, 309, 2.2, "end")
    yf = t5(int(ST["feed_stage"]))
    c.line([(255, yn), (345, yn), hx114["S"]])
    c.line([hx114["N"], (345, yf), (col5["xl"], yf)])
    c.flag(357, yf - 5, fT(ST["T_feed"]), "T")
    c.flag(cx5 + 18, top5 - 2, fT(ST["T_top"]), "T")
    c.flag(cx5 + 18, top5 + 4, fP(float(e105["op_P"])), "P")
    # overhead -> A-106 -> D-105
    yo5 = 82.0
    a106 = D.eq("A-106")
    ac6 = c.aircooler(450, yo5, w=26, fans=int(a106["fans"]))
    c.text("A-106", 450, yo5 - 5, 2.6, "middle", bold=True)
    c.line([col5["top"], (cx5, yo5), ac6["W"]], kind="P")
    d5 = c.hvessel(472, 140, 38, 13, boot=None, tag="D-105")
    c.text("D-105", 472, 141, 2.4, "middle", bold=True, chk=False)
    c.line([ac6["E"], (484, yo5), (484, d5["y0"])])
    c.line([(420, yo5), (420, 112), (458, 112), (458, d5["y0"])], kind="S")
    a = c.cv(438, 112, act="down", tag="PV-1091", tag_side="belowleft")
    b = p.loop("PIC-1091", 438, 126)
    c.sig([b["N"], a])
    c.sig([b["E"], (455, 126), (455, d5["y0"] + 1)])
    c.text("HOT VAPOUR BYPASS", 438, 109, 2.2, "middle")
    # off-gas 29
    c.line([d5["top"](480), (480, 122), (500, 122)], kind="S")
    con = c.offsheet(500, 122, "R", "OFF-GAS (NNF) TO FG", "TO OSBL")
    p.stream("29", 491, 122)
    # P-115 reflux + LPG
    p115 = c.pump(482, 168)
    c.line([d5["bot"](464), (464, 168), p115["suc"]])
    c.text("P-115A/B", 482, 177, 2.5, "middle", bold=True)
    yd5 = p115["dis"][1]
    c.line([p115["dis"], (500, yd5), (500, 190), (412, 190), (412, t5(1)), (col5["xr"], t5(1))])
    a = c.cv(450, 190, act="down", tag="FV-1094", tag_side="belowright")
    b = p.loop("FIC-1094", 450, 205)
    c.sig([b["N"], a])
    a = c.cv(515, yd5, tag="FV-1093", tag_side="below")
    bf = p.loop("FIC-1093", 515, yd5 - 16)
    c.sig([bf["S"], a])
    bl = p.loop("LIC-1092", 500, 140)
    c.sig([bl["W"], (d5["x1"], 140)])
    c.sig([bl["E"], (515, 140), bf["N"]])
    p.stream("30", 530, yd5)
    con = c.offsheet(540, yd5, "R", "LPG TO TREATING", "TO OSBL")
    c.line([(500, yd5), (540, yd5)])
    # E-116 reboiler
    kt = c.kettle(447, 352, L=32, D=12)
    c.text("E-116", kt["x1"] + 2, 343, 2.6, bold=True)
    e116 = D.eq("E-116")
    c.text(f"{e116['duty_kw'] / 1000:.1f} MW", kt["x1"] + 2, 347, 2.2)
    c.line([col5["bot"], (cx5, 366), (kt["liq"][0], 366), kt["liq"]])
    c.line([kt["vap"], (kt["vap"][0], 312), (col5["xr"], 312)])
    c.flag(cx5 - 2, 372, fT(ST["T_bot"]), "T", anchor="end")
    hp = ut["hp_steam"]
    xs6 = kt["tin_top"][0]
    c.line([(xs6, 318), kt["tin_top"]], kind="U")
    c.text(f"HP STEAM {hp['P_barg']:g} barg", xs6 + 1, 316, 2.2, "middle")
    c.line([kt["tout_bot"], (xs6, 372)], kind="U")
    c.text("COND.", xs6, 375, 2.2, "middle")
    a = c.cv(xs6, 332, orient="v", act="left", tag="FV-1096", tag_side="right")
    bf = p.loop("FIC-1096", 414, 332)
    c.sig([bf["E"], a])
    bt = p.loop("TIC-1095", 414, t5(15))
    c.sig([bt["W"], (col5["xr"], t5(15))])
    c.sig([bt["S"], bf["N"]])
    # bottoms -> LV-1097 -> E-114 -> C-106 (stream 31)
    yb5 = 395.0
    c.line([kt["ovf"], (470, kt["ovf"][1]), (470, yb5), (365, yb5), (365, 300), hx114["E"]])
    a = c.cv(420, yb5, act="down", tag="LV-1097", tag_side="above")
    b = p.loop("LIC-1097", 372, 340)
    c.sig([b["E"], (col5["xl"], 340)])
    c.sig([b["S"], (372, 410), (420, 410), a])
    p.stream("31", 445, yb5)
    yfeed6 = None
    # ---------------- splitter C-106
    e106 = D.eq("C-106")
    cx6, top6, h6, w6 = 612.0, 92.0, 300.0, 30.0
    nt6 = int(SP["N_actual"])

    def t6(t):
        return top6 + 16 + (t - 1) * (h6 - 36) / (nt6 - 1)
    trays = [(t6(t), "L" if t % 2 else "R", str(t) if t in (1, int(SP["feed_stage"]), 30, nt6) else "")
             for t in (1, 6, 12, 17, int(SP["feed_stage"]), 25, 30, 34, nt6)]
    col6 = c.column(cx6, top6, w6, h6, trays=trays, tag="C-106")
    c.text("C-106", cx6 - 17, top6 + 4, 2.8, "end", bold=True)
    yf6 = t6(int(SP["feed_stage"]))
    c.line([hx114["W"], (322, 300), (322, 432), (570, 432), (570, yf6), (col6["xl"], yf6)])
    c.flag(322 - 2, 420, fT(e114["Th_out"]), "T", anchor="end")
    c.flag(cx6 + 20, top6 - 2, fT(SP["T_top"]), "T")
    c.flag(cx6 + 20, top6 + 4, fP(float(e106["op_P"])), "P")
    yo6 = 78.0
    a107 = D.eq("A-107")
    ac7 = c.aircooler(682, yo6, w=26, fans=int(a107["fans"]))
    c.text("A-107", 682, yo6 - 5, 2.6, "middle", bold=True)
    c.line([col6["top"], (cx6, yo6), ac7["W"]])
    d6 = c.hvessel(705, 145, 46, 15, tag="D-106")
    c.text("D-106", 705, 146, 2.4, "middle", bold=True, chk=False)
    c.line([ac7["E"], (718, yo6), (718, d6["y0"])])
    a = c.cv(718, 112, orient="v", act="right", tag="PV-1100", tag_side="left")
    b = p.loop("PIC-1100", 738, 125)
    c.sig([b["N"], (738, 112), a])
    c.sig([b["S"], (738, 134), (d6["x1"] - 4, 134), (d6["x1"] - 4, d6["y0"] + 1)])
    c.text("FLOODED CONDENSER", 724, 100, 2.2)
    p116 = c.pump(712, 178)
    c.line([d6["bot"](694), (694, 178), p116["suc"]])
    c.text("P-116A/B", 712, 187, 2.5, "middle", bold=True)
    yd6 = p116["dis"][1]
    c.line([p116["dis"], (735, yd6), (735, 198), (645, 198), (645, t6(1)), (col6["xr"], t6(1))])
    a = c.cv(670, 198, act="down", tag="FV-1103", tag_side="belowright")
    b = p.loop("FIC-1103", 670, 213)
    c.sig([b["N"], a])
    a = c.cv(752, yd6, tag="FV-1102", tag_side="below")
    bf = p.loop("FIC-1102", 752, yd6 - 18)
    c.sig([bf["S"], a])
    bl = p.loop("LIC-1101", 752, 145)
    c.sig([bl["W"], (d6["x1"], 145)])
    c.sig([bl["S"], bf["N"]])
    p.stream("32", 768, yd6)
    con = c.offsheet(777, yd6, "R", "LN TO ISOM.", "TO OSBL")
    c.line([(735, yd6), (777, yd6)])
    c.flag(768, yd6 + 9, fT(D.T("32")), "T")
    # E-117 thermosyphon
    hx7 = c.hx(668, 350, tube="h")
    c.text("E-117", 676, 343, 2.6, bold=True)
    e117 = D.eq("E-117")
    c.text(f"{e117['duty_kw'] / 1000:.1f} MW", 676, 360, 2.2)
    c.line([(col6["xr"], 378), (668, 378), hx7["S"]])
    c.line([hx7["N"], (668, 325), (col6["xr"], 325)])
    mp = ut["mp_steam"]
    c.line([(712, 350), hx7["E"]], kind="U")
    c.text(f"MP STEAM {mp['P_barg']:g} barg", 714, 351, 2.2)
    c.line([hx7["W"], (652, 350), (652, 362)], kind="U")
    c.text("COND.", 652, 365, 2.2, "middle")
    a = c.cv(694, 350, tag="FV-1105", tag_side="below")
    bf = p.loop("FIC-1105", 694, 333)
    c.sig([bf["S"], a])
    bt = p.loop("TIC-1104", 645, t6(30) - 2)
    c.sig([bt["W"], (col6["xr"], t6(30) - 2)])
    c.sig([bt["E"], (694, t6(30) - 2), bf["N"]])
    # bottoms -> P-117 -> A-108 -> HN
    p117 = c.pump(645, 412)
    c.line([col6["bot"], (cx6, 412), p117["suc"]])
    c.text("P-117A/B", 645, 421, 2.5, "middle", bold=True)
    c.flag(cx6 - 10, 400, fT(SP["T_bot"]), "T", anchor="end")
    yhn = p117["dis"][1]
    a = c.cv(668, yhn, tag="FV-1107", tag_side="below")
    bf = p.loop("FIC-1107", 668, yhn - 16)
    c.sig([bf["S"], a])
    bl = p.loop("LIC-1106", 590, 385)
    c.sig([bl["E"], (col6["xl"], 385)])
    c.sig([bl["S"], (590, 400), (630, 400), (630, yhn - 16), bf["W"]])
    a108 = D.eq("A-108")
    ac8 = c.aircooler(715, yhn, w=26, fans=int(a108["fans"]))
    c.text("A-108", 715, yhn - 5, 2.6, "middle", bold=True)
    c.line([p117["dis"], ac8["W"]])
    p.stream("33", 745, yhn)
    con = c.offsheet(762, yhn, "R", "HN TO NHT / REFORMER", "TO OSBL")
    c.line([ac8["E"], (762, yhn)])
    c.flag(752, yhn + 9, fT(D.T("33")), "T")
    for tag, x in [("X-103", 75), ("A-101", 108), ("E-115", 150), ("D-102", 195), ("P-103A/B", 150),
                   ("P-104A/B", 200), ("P-105A/B", 236), ("E-114", 345), ("C-105", 390), ("A-106", 450),
                   ("D-105", 472), ("P-115A/B", 482), ("E-116", 447), ("C-106", 612), ("A-107", 682),
                   ("D-106", 705), ("P-116A/B", 712), ("E-117", 668), ("P-117A/B", 645), ("A-108", 715)]:
        p.title(tag, x)
    return p.save()

# ============================================================================ SHEET 5
def sheet5(D):
    p = PFD(D, "CFU-200-PR-PFD-005", "VACUUM HEATER H-201 & VACUUM COLUMN C-201",
            ["C-201 is a wet, packed column: 4 beds with chimney-tray draw pans.",
             "Wash-oil flow FIC-2020 is a critical minimum-flow constraint (wash bed coking).",
             "VR bottoms temperature limited by quench (TIC-2026 -> FIC-2027); coil steam per pass FI."], 5)
    c = p.c
    V = D.R["vac"]
    h2 = D.R["heaters"]["H-201"]
    ut = basis.UTILITIES
    # ---------------- H-201
    rx0, rx1, ry0, ry1 = 72.0, 172.0, 255.0, 368.0
    cvx0, cvx1, cvy0, cvy1 = 92.0, 152.0, 182.0, 248.0
    c.heater_box(rx0, ry0, rx1 - rx0, ry1 - ry0)
    c._poly([(rx0, ry0), (cvx0, cvy1), (cvx1, cvy1), (rx1, ry0)], w=0.5)
    c.heater_box(cvx0, cvy0, cvx1 - cvx0, cvy1 - cvy0)
    c.reg(rx0, cvy1, rx1, ry0, "hood")
    for xx in (rx0 + 4, rx1 - 4):
        c.coil_v(xx, ry0 + 6, ry1 - 12, n=12)
    for yy in range(int(cvy0 + 6), int(cvy1 - 2), 7):
        c.coil_h(cvx0 + 4, cvx1 - 4, yy, amp=1.2, n=12)
    c.stack(122, cvy0, 92, wb=12, wt=8)
    c.text("H-201", 122, ry0 + 28, 3.4, "middle", bold=True, chk=False)
    c.text(f"{h2['Q_abs_kw'] / 1000:.1f} MW ABS.", 122, ry0 + 34, 2.4, "middle", chk=False)
    c.text(f"{h2['Q_fired_kw'] / 1000:.1f} MW FIRED", 122, ry0 + 39, 2.2, "middle", chk=False)
    c.text(f"{h2['passes']} PASSES, {h2['burners']} BURNERS", 122, ry0 + 44, 2.2, "middle", chk=False)
    nb = int(h2["burners"])
    for j in range(nb):
        c.burner(rx0 + 12 + j * (rx1 - rx0 - 24) / (nb - 1), ry1)
    # AR in + coil steam + passes
    xh = 70.0
    yar = 175.0
    con = c.offsheet(15, yar - 22, "R", "ATM. RESIDUE FROM P-112", "FROM PFD-003")
    c.line([con["tip"], (xh, yar - 22), (xh, yar)], arrow=False)
    p.stream("19", con["tip"][0] + 6, yar - 22)
    npass = int(h2["passes"])
    yps = [cvy0 + 12 + (cvy1 - cvy0 - 22) * i / (npass - 1) for i in range(npass)]
    c.line([(xh, yar - 22), (xh, yps[-1])], arrow=False)
    for i, yy in enumerate(yps):
        c.line([(xh, yy), (cvx0, yy)], kind="S")
        a = c.cv(82, yy)
        if i == 0:
            b = p.loop("FIC-2001", 82, yy - 13)
            c.sig([b["S"], a])
    c.text("FV-2001...2004", xh - 2, yps[-1] + 6, 2.2, "end")
    mp = ut["mp_steam"]
    c.line([(xh, 118), (xh, yar - 23)], kind="U")
    c.text(f"COIL STEAM (MP {mp['P_barg']:g} barg)", xh, 115.5, 2.2, "middle")
    a = c.cv(xh, 134, orient="v", act="left", tag="FV-2007", tag_side="right")
    b = p.loop("FIC-2007", xh - 20, 134)
    c.sig([b["E"], a])
    # outlets
    xo = 190.0
    yo = [ry0 + 14 + 8 * i for i in range(npass)]
    for yy in yo:
        c.line([(rx1, yy), (xo, yy)], kind="S", arrow=False)
    ytl = 330.0
    col = c.column_sections(380, 86, [(24, 146), (54, 376), (26, 472)], tag="C-201")
    xl, xr = col["xl"], col["xr"]
    c.line([(xo, yo[0]), (xo, ytl), (xl(ytl), ytl)])
    p.stream("21", 225, ytl)
    c.flag(250, ytl - 6, "COT " + fT(V["cot"]), "T")
    c.flag(282, ytl - 6, fP(D.S["21"]["P_barg"]), "P")
    c.flag(320, ytl - 6, "FZ " + fT(V["T_fz"]), "T")
    c.flag(320, ytl + 6, f"{V['P_fz_mbar']:.0f} mbar(a)", "P")
    btc = p.loop("TIC-2005", 250, ytl + 15)
    c.sig([btc["N"], (250, ytl)])
    # fuel gas / off-gas
    yfg = 392.0
    con = c.offsheet(15, yfg, "R", "FUEL GAS FROM D-103", "FROM PFD-002")
    a = c.cv(70, yfg, tag="PV-2006", tag_side="below")
    bp = p.loop("PIC-2006", 70, yfg - 14)
    c.sig([bp["S"], a])
    c.sig([btc["S"], (250, yfg - 14), bp["E"]])
    c.line([con["tip"], (rx1 - 12, yfg)], kind="S", arrow=False)
    for j in range(nb):
        bx = rx0 + 12 + j * (rx1 - rx0 - 24) / (nb - 1)
        c.line([(bx, yfg), (bx, ry1)], kind="U", hop=False)
    p.stream("34", 94, yfg)
    yog = 408.0
    con = c.offsheet(15, yog, "R", "VAC. OFF-GAS FROM D-202", "FROM PFD-006")
    c.line([con["tip"], (rx1 - 4, yog), (rx1 - 4, ry1)], kind="U")
    p.stream("28", 120, yog)
    c.text("OFF-GAS BURNER", rx1 - 2, yog + 4.5, 2.2, "end")
    # ---------------- C-201 internals
    cx = 380.0
    c.text("C-201", cx - 30, 92, 3.0, "end", bold=True)
    c.spray(cx, 24, 96)
    c.bed(cx, 24, 101, 128, "BED 1")
    c.pan(cx, 24, 138)
    c.bed(cx, 54, 162, 192, "BED 2")
    c.spray(cx, 54, 205)
    c.bed(cx, 54, 210, 244, "BED 3")
    c.pan(cx, 54, 256)
    c.spray(cx, 54, 268)
    c.bed(cx, 54, 273, 298, "BED 4 (WASH)")
    c.pan(cx, 54, 310)
    c.text("FLASH ZONE", cx, 343, 2.2, "middle", chk=False)
    for k, yy in enumerate((396, 410, 424, 438, 452)):
        side = k % 2
        xa, xb = xl(yy), xr(yy)
        if side:
            c._ln((xa, yy), (xb - 6, yy), 0.3)
        else:
            c._ln((xb, yy), (xa + 6, yy), 0.3)
    # overhead
    yoh = 70.0
    c.line([col["top"], (cx, yoh), (742, yoh)])
    c.offsheet(742, yoh, "R", "VAC. OVERHEAD TO J-201", "TO PFD-006")
    p.stream("22", 420, yoh)
    c.flag(450, yoh - 5.5, fT(V["T_top"]), "T")
    c.flag(480, yoh - 5.5, f"{V['P_top_mbar']:.0f} mbar(a)", "P")
    # ---------------- LVGO circuit
    ypa1, yret1, ydis1, yprod1 = 92.0, 140.0, 162.0, 180.0
    pm = c.pump(431, 165)
    c.line([(xr(138), 138), (418, 138), (418, 165), pm["suc"]])
    c.text("P-201A/B", 431, 174, 2.5, "middle", bold=True)
    c.flag(408, 143, fT(V["T_lvgo"]), "T", anchor="start")
    con = c.offsheet(452, pm["dis"][1], "R", "LVGO TO E-103", "TO PFD-001")
    c.line([pm["dis"], (452, pm["dis"][1])])
    con = c.offsheet(760, yret1, "L", "LVGO FROM E-103", "FROM PFD-001")
    a201 = D.eq("A-201")
    ac = c.aircooler(700, yret1, w=26, fans=int(a201["fans"]))
    c.text("A-201", 682, yret1 - 5, 2.6, "end", bold=True)
    c.text(f"{a201['duty_kw'] / 1000:.1f} MW", 700, yret1 + 15.5, 2.2, "middle")
    c.line([con["tip"], ac["E"]], kind="S")
    c.line([ac["W"], (640, yret1), (640, ypa1), (xr(ypa1), ypa1)])
    c.flag(735, yret1 + 6.5, fT(D.TR["A-201"]["T_in"]), "T")
    c.flag(655, ypa1 - 5, fT(V["pa"]["LVGO"]["T_ret"]), "T")
    a = c.cv(560, ypa1, tag="FV-2011", tag_side="below")
    b = p.loop("FIC-2011", 560, ypa1 - 13)
    c.sig([b["S"], a])
    c.line([(640, yret1), (640, yprod1), (742, yprod1)])
    a = c.cv(690, yprod1, act="down", tag="FV-2015", tag_side="belowright")
    bf = p.loop("FIC-2015", 690, yprod1 + 16)
    c.sig([bf["N"], a])
    p.stream("23", 720, yprod1)
    c.offsheet(742, yprod1, "R", "LVGO TO HYDROCRACKER", "TO OSBL")
    c.flag(720, yprod1 - 6, fT(D.T("23")), "T")
    bl = p.loop("LIC-2014", 432, 126)
    c.sig([bl["W"], (xr(126), 126)])
    c.sig([bl["E"], (625, 126), (625, yprod1 + 16), bf["W"]])
    bt2 = p.loop("TIC-2012", 420, 106)
    c.sig([bt2["W"], (xr(106), 106)])
    bt3 = p.loop("TIC-2013", 470, 106)
    c.sig([bt2["E"], bt3["W"]])
    c.sig([bt3["E"], (722, 106), (722, 150), (ac["x1"] - 6.5 + 1.5, 150)])
    c.text("TO FAN PITCH", 724, 120, 2.2)
    # ---------------- HVGO circuit
    ypa2, yret2, yd2, ydis2, yprod2 = 205.0, 230.0, 256.0, 280.0, 300.0
    pm = c.pump(436, ydis2 + 2.8)
    c.line([(xr(yd2), yd2), (424, yd2), (424, ydis2 + 2.8), pm["suc"]])
    c.text("P-202A/B", 436, ydis2 + 12, 2.5, "middle", bold=True)
    con = c.offsheet(458, ydis2, "R", "HVGO TO E-108", "TO PFD-002")
    c.line([pm["dis"], (458, ydis2)])
    con = c.offsheet(705, yret2, "L", "HVGO FROM E-108", "FROM PFD-002")
    c.line([con["tip"], (600, yret2), (600, ypa2), (xr(ypa2), ypa2)])
    c.flag(655, yret2 - 5.5, fT(V["pa"]["HVGO"]["T_ret"]), "T")
    a = c.cv(540, ypa2, tag="FV-2016", tag_side="below")
    b = p.loop("FIC-2016", 540, ypa2 - 13)
    c.sig([b["S"], a])
    c.line([(600, yret2), (432, yret2), (432, 268), (xr(268), 268)], kind="S")
    a = c.cv(500, yret2, tag="FV-2020", tag_side="below")
    b = p.loop("FIC-2020", 500, yret2 - 13)
    c.sig([b["S"], a])
    c.text("WASH OIL", 470, yret2 - 2, 2.2, "middle")
    c.line([(600, yret2), (600, yprod2), (650, yprod2)])
    a = c.cv(625, yprod2, act="down", tag="FV-2019", tag_side="belowleft")
    bf = p.loop("FIC-2019", 625, yprod2 + 15)
    c.sig([bf["N"], a])
    a202 = D.eq("A-202")
    ac2 = c.aircooler(675, yprod2, w=26, fans=int(a202["fans"]))
    c.line([(650, yprod2), ac2["W"]])
    c.text("A-202", 675, yprod2 - 5, 2.6, "middle", bold=True)
    c.text(f"{a202['duty_kw'] / 1000:.1f} MW", 692, yprod2 - 5, 2.2)
    p.stream("24", 708, yprod2)
    c.flag(708, yprod2 - 6, fT(D.T("24")), "T")
    con = c.offsheet(720, yprod2, "R", "HVGO TO FCC / HCU", "TO OSBL")
    c.line([ac2["E"], (720, yprod2)])
    bl = p.loop("LIC-2018", 446, 244)
    c.sig([bl["W"], (xr(244), 244)])
    c.sig([bl["E"], (585, 244), (585, yprod2 + 15), bf["W"]])
    c.flag(408, yd2 + 6, fT(V["T_hvgo"]), "T", anchor="start")
    # ---------------- slop wax
    ysl = 335.0
    pm = c.pump(436, ysl + 2.8)
    c.line([(xr(310), 310), (424, 310), (424, ysl + 2.8), pm["suc"]])
    c.text("P-203A/B", 436, ysl + 12, 2.5, "middle", bold=True)
    a = c.cv(470, ysl, tag="FV-2022", tag_side="below")
    bf = p.loop("FIC-2022", 470, ysl - 15)
    c.sig([bf["S"], a])
    bl = p.loop("LIC-2021", 448, ysl - 15)
    c.sig([bl["W"], (xr(ysl - 15), ysl - 15)])
    c.sig([bl["E"], bf["W"]])
    p.stream("25", 492, ysl)
    con = c.offsheet(505, ysl, "R", "SLOP WAX TO SLOP / FCC", "TO OSBL")
    c.line([pm["dis"], (505, ysl)])
    c.flag(415, 304, fT(V["T_slop"]), "T", anchor="start")
    # ---------------- bottoms / VR
    xbl, xbr = xl(430), xr(430)
    ysb = 446.0
    c.line([(440, ysb), (xbr, ysb)], kind="U")
    c.text("STRIPPING STEAM", 442, ysb + 0.8, 2.2)
    a = c.cv(420, ysb, tag="FV-2023", tag_side="below")
    b = p.loop("FIC-2023", 420, ysb - 13)
    c.sig([b["S"], a])
    yvr = 497.0
    pm = c.pump(345, yvr + 2.8, face="L")
    c.line([col["bot"], (380, yvr + 2.8), pm["suc"]])
    c.text("P-204A/B", 345, yvr + 12, 2.5, "middle", bold=True)
    c.flag(392, 478, fT(V["T_bot"]), "T", anchor="start")
    a = c.cv(300, yvr, act="down", tag="FV-2025", tag_side="belowleft")
    bf = p.loop("FIC-2025", 300, yvr + 15)
    c.sig([bf["N"], a])
    con = c.offsheet(240, yvr, "L", "VAC. RESIDUE TO E-111", "TO PFD-002")
    c.line([pm["dis"], con["base"]])
    bl = p.loop("LIC-2024", 405, 466)
    c.sig([bl["W"], (xbr, 466)])
    c.sig([bl["S"], (405, yvr + 15), bf["E"]])
    # E-201 return / quench
    yre = 455.0
    con = c.offsheet(290, yre, "L", "VAC. RESIDUE FROM E-105", "FROM PFD-001")
    kt = c.kettle(232, yre + 15, L=30, D=12)
    c.text("E-201", kt["x1"] + 2, yre + 22, 2.6, bold=True)
    e201 = D.eq("E-201")
    c.text(f"{e201['duty_kw'] / 1000:.1f} MW", kt["x1"] + 2, yre + 26, 2.2)
    xt = kt["tin_top"][0]
    c.line([con["tip"], (xt, yre), kt["tin_top"]])
    yv = 485.0
    c.line([kt["tout_bot"], (xt, yv), (60, yv)])
    con = c.offsheet(15, yv, "L", "VR TO COKER / STORAGE", "TO OSBL")
    c.line([(60, yv), con["base"]])
    p.stream("26", 80, yv)
    c.flag(100, yv - 6, fT(D.T("26")), "T")
    lp = ut["lp_steam"]
    c.line([kt["vap"], (kt["vap"][0], yre - 8)], kind="U")
    c.text(f"LP STEAM {lp['P_barg']:g} barg", kt["vap"][0] + 2, yre - 6, 2.2)
    c.line([(kt["x1"] + 9, yre + 18), (kt["x1"], yre + 18)], kind="U")
    c.text("BFW", kt["x1"] + 10, yre + 18.8, 2.2)
    yq = 420.0
    c.line([(200, yv), (200, yq), (xl(yq), yq)])
    a = c.cv(290, yq, tag="FV-2027", tag_side="below")
    b = p.loop("FIC-2027", 290, yq - 14)
    c.sig([b["S"], a])
    c.text("VR QUENCH", 230, yq - 2, 2.2, "middle")
    bt = p.loop("TIC-2026", 340, yq + 16)
    c.sig([bt["E"], (xl(yq + 16), yq + 16)])
    c.sig([bt["N"], (340, yq - 14), b["E"]])
    for tag, x in [("H-201", 122), ("C-201", 380), ("P-201A/B", 431), ("A-201", 700), ("P-202A/B", 470),
                   ("A-202", 675), ("P-203A/B", 510), ("P-204A/B", 345), ("E-201", 232)]:
        p.title(tag, x)
    return p.save()

# ============================================================================ SHEET 6
def sheet6(D):
    p = PFD(D, "CFU-200-PR-PFD-006", "VACUUM EJECTOR SYSTEM & HOTWELL",
            ["Each ejector stage 2 x 50 % parallel units; one shown. Motive MP steam.",
             "Condensers E-202/203/204 drain via barometric legs (seal) to hotwell D-201.",
             "C-201 top pressure PIC-2010 (transmitter on C-201 top, PFD-005) recycles off-gas to J-203 suction."], 6)
    c = p.c
    EJ = {e["tag"]: e for e in D.R["ejector"]["stages"]}
    mp = basis.UTILITIES["mp_steam"]
    yh, yj, ye = 120.0, 150.0, 185.0
    xj = {"J-201": 140.0, "J-202": 290.0, "J-203": 440.0}
    xe = {"E-202": 230.0, "E-203": 380.0, "E-204": 530.0}
    L = 32.0
    con = c.offsheet(15, yh, "R", f"MP STEAM {mp['P_barg']:g} barg", "FROM UTILITIES")
    c.line([con["tip"], (xj["J-203"] - 10, yh)], kind="U", arrow=False)
    c.text("MOTIVE STEAM HEADER", 70, yh - 2, 2.2)
    js = {}
    for tag, x0 in xj.items():
        js[tag] = c.ejector(x0, yj, L=L)
        c.line([(x0 - 10, yh), (x0 - 10, yj), (x0, yj)], kind="U")
        e = EJ[tag]
        c.text(tag, x0 + L / 2, yj - 10, 2.8, "middle", bold=True)
        c.text(f"MOTIVE {e['motive_kg_h']:,.0f} kg/h", x0 + L / 2, yj - 5.2, 2.2, "middle")
        c.flag(x0 + L + 9, yj - 6, f"{e['discharge_mbar']:.0f} mbar(a)", "P")
    # vacuum overhead in
    con = c.offsheet(15, ye, "R", "VAC. OVERHEAD FROM C-201", "FROM PFD-005")
    p.stream("22", con["tip"][0] + 10, ye)
    pk = c.package(78, ye - 30, 22, 11, ["X-104", "CORR. INHIBITOR"])
    c.line([pk["S"], (89, ye)], kind="U")
    c.line([con["tip"], (js["J-201"]["suc"][0], ye), js["J-201"]["suc"]])
    c.flag(110, ye + 7, f"{EJ['J-201']['suction_mbar']:.0f} mbar(a)", "P")
    c.flag(110, ye + 13, fT(D.T("22")), "T")
    hxs = {}
    order = [("J-201", "E-202", "J-202"), ("J-202", "E-203", "J-203"), ("J-203", "E-204", None)]
    for jt, et, nxt in order:
        x = xe[et]
        h = c.hx(x, ye, r=9, tube="h")
        hxs[et] = h
        ee = D.eq(et)
        c.text(et, x + 11, ye - 9, 2.8, bold=True)
        c.text(f"{ee['duty_kw'] / 1000:.2f} MW", x + 11, ye + 13, 2.2)
        c.line([js[jt]["dis"], (x, yj), h["N"]])
        c.line([(x - 22, ye), h["W"]], kind="U")
        c.text("CW", x - 23, ye + 0.8, 2.2, "end")
        if nxt:
            c.line([h["E"], (js[nxt]["suc"][0], ye), js[nxt]["suc"]])
        c.flag(x + 22, ye + 6, fT(ee["Th_out"]), "T")
    # off-gas KO drum D-202
    d202 = c.vvessel(620, ye + 5, 14, 34, tag="D-202", mesh=True)
    c.text("D-202", 630, ye - 12, 2.8, bold=True)
    c.line([hxs["E-204"]["E"], (d202["x0"], ye)])
    yog = 100.0
    c.line([d202["top"], (620, yog), (690, yog)], kind="S")
    p.stream("28", 655, yog)
    c.offsheet(690, yog, "R", "VAC. OFF-GAS TO H-201 BURNERS", "TO PFD-005")
    c.flag(655, yog - 7, fP(D.S["28"]["P_barg"]), "P")
    # NCG recycle PV-2010
    yrc = 132.0
    xr_ = js["J-203"]["suc"][0]
    c.line([(620, yrc), (472 + 8, yrc), (480, ye - 10), (xr_, ye - 10)], kind="S")
    a = c.cv(560, yrc, tag="PV-2010", tag_side="below")
    b = p.loop("PIC-2010", 560, yrc - 15)
    c.sig([b["S"], a])
    c.sig([b["W"], (530, yrc - 15)])
    c.text("FROM PT ON C-201 TOP", 528, yrc - 15.8, 2.2, "end")
    c.text("(SEE PFD-005)", 528, yrc - 12.8, 2.2, "end")
    c.text("NCG RECYCLE", 520, yrc - 2, 2.2, "middle")
    # hotwell D-201
    yd = 285.0
    hw = c.hvessel(382, yd, 326, 22, tag="D-201", weir=True)
    c.text("D-201", 380, yd + 1, 3.0, "middle", bold=True, chk=False)
    c.text("HOTWELL", 380, yd + 5.5, 2.2, "middle", chk=False)
    for et, x in xe.items():
        c.line([hxs[et]["S"], (x, hw["y0"])], kind="S")
    c.text("BAROMETRIC LEGS (SEALED IN HOTWELL)", 305, 240, 2.4, "middle")
    c.line([d202["bot"], (620, yd), (hw["x1"], yd)], kind="S")
    # sour water
    yp = 360.0
    xsw = 300.0
    pm = c.pump(xsw + 20, yp)
    c.line([hw["bot"](xsw), (xsw, yp), pm["suc"]], kind="S")
    c.text("P-205A/B", xsw + 20, yp + 9, 2.5, "middle", bold=True)
    yd1 = pm["dis"][1]
    a = c.cv(355, yd1, tag="LV-2028", tag_side="below")
    b = p.loop("LIC-2028", 270, 318)
    c.sig([b["N"], (270, hw["y1"])])
    c.sig([b["E"], (355, 318), a])
    p.stream("27", 375, yd1)
    c.flag(375, yd1 - 7, fT(D.T("27")), "T")
    con = c.offsheet(390, yd1, "R", "EJECTOR SOUR WATER TO SWS", "TO OSBL")
    c.line([pm["dis"], (390, yd1)], kind="S")
    # slop oil
    xso = 490.0
    pm = c.pump(xso + 20, yp)
    c.line([hw["bot"](xso), (xso, yp), pm["suc"]], kind="S")
    c.text("P-206A/B", xso + 20, yp + 9, 2.5, "middle", bold=True)
    a = c.cv(540, pm["dis"][1], tag="LV-2029", tag_side="below")
    con = c.offsheet(560, pm["dis"][1], "R", f"SLOP OIL {D.R['ejector']['slop_oil']:.0f} kg/h", "TO OSBL SLOP")
    c.line([pm["dis"], (560, pm["dis"][1])], kind="S")
    for tag, x in [("X-104", 89), ("J-201", 156), ("E-202", 230), ("J-202", 306), ("E-203", 380),
                   ("J-203", 456), ("E-204", 530), ("D-202", 620), ("D-201", 380), ("P-205A/B", 320),
                   ("P-206A/B", 510)]:
        p.title(tag, x)
    return p.save()


# ============================================================================ build
SHEETS = [sheet1, sheet2, sheet3, sheet4, sheet5, sheet6]


def build():
    D = Data()
    pdfs = []
    for fn in SHEETS:
        pdfs.append(fn(D))
    merge_pdfs(pdfs, OUT / "CFU-000-PR-PFD-ALL.pdf")
    if len(SHEETS) == 6:
        miss_s = sorted(set(D.S) - D.used_streams, key=int)
        miss_l = sorted(t for t, l in D.L.items() if l.get("pfd") and t not in D.used_loops)
        if miss_s:
            print("  WARNING: H&MB streams not shown on any PFD:", ", ".join(miss_s))
        if miss_l:
            print("  WARNING: PFD control loops not shown:", ", ".join(miss_l))
    return pdfs


if __name__ == "__main__":
    build()
