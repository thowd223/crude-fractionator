"""Loop diagrams CFU-100-IC-LD-001..003 (A3, ISA-5.4 style).

field device -> field cable -> JB (terminals) -> multicore (pair) -> FAR-100 marshalling (terminals, IS isolator /
SIL barrier) -> system cabinet I/O card / channel -> controller function. Terminal numbers, cable tags, JB,
cabinet and card assignments are read from data/io_list.json so they agree with the I/O list.
"""
from __future__ import annotations

from ..drawing.sheet import Sheet as _Sheet


class Sheet(_Sheet):
    """A3 sheet with the full-height (A1-style) title block: the stock A3 block (170 x 50) leaves only 4 mm
    for the drawing number row, which then overlaps the frame (reported upstream)."""

    def _title_block(self, *a):
        self.tb_w, self.tb_h = 180, 62
        super()._title_block(*a)
from .common import APC_GRN, BLUE, GREY, OUT, SIS_RED, Pen, load

COLS = [("FIELD", 12, 78), ("FIELD JB", 78, 128), ("MULTICORE", 128, 178), ("FAR-100 MARSHALLING", 178, 248),
        ("SYSTEM CABINET / I/O", 248, 318), ("CONTROLLER / HMI (CCR)", 318, 408)]


def _pts():
    io = load("io_list.json")
    return {p["tag"]: p for p in io["points"]} if io else {}


def _frame(p, y0, y1):
    for name, x0, x1 in COLS:
        p.gb.add(p.d.rect((x0, y0), (x1 - x0, 7), fill="#D9E1F2", stroke="black", stroke_width=0.3))
        p.text(name, (x0 + x1) / 2, y0 + 4.8, 2.4, "middle", bold=True)
        p.line([(x1, y0), (x1, y1)], w=0.25, dash="2,1.2", color=GREY)
    p.line([(COLS[0][1], y0), (COLS[0][1], y1)], w=0.25, dash="2,1.2", color=GREY)
    p.text("HAZARDOUS AREA (ZONE 1/2, IIA T3)", 45, y1 - 2, 1.9, "middle", color=GREY)
    p.text("SAFE AREA (FAR-100 / CCR)", 293, y1 - 2, 1.9, "middle", color=GREY)
    p.line([(178, y0 + 7), (178, y1)], w=0.6, color="black")


def _term(p, x, y, n):
    p.gs.add(p.d.rect((x - 2.2, y - 1.3), (4.4, 2.6), fill="white", stroke="black", stroke_width=0.25))
    p.text(str(n), x, y + 0.8, 1.6, "middle")


def _row(p, y, pt, dev, kind="tx", sis=False, power="24 VDC loop powered from I/O card (2-wire)"):
    """Draw one signal path. kind: tx (transmitter) | pos (valve positioner) | sov | ls (limit switch)."""
    col = SIS_RED if sis else "black"
    # device
    p.box(14, y - 8, 48, 16, None, stroke=col, fill="none")
    if kind == "sov":
        p.cv(21, y + 3, "h", None, None, act="s", sis=True, size=2.8)
    else:
        p.bubble(21, y, pt["tag"], "field", r=5.0, color=col)
    for i, s in enumerate(dev):
        p.text(s, 28, y - 4 + 3.0 * i, 1.7, color=col if i == 0 else "black", bold=i == 0)
    # wires
    t = pt["jb_terminals"].split("/")
    mt = pt["marsh_terminals"].split("-")[1].split("/")
    for k, dy in enumerate((-1.6, 1.6)):
        yy = y + dy
        p.line([(62, yy), (95, yy)], w=0.3, color=col)
        p.line([(99.4, yy), (136, yy)], w=0.3, color=col)
        p.line([(136, yy), (190, yy)], w=0.45, color=col)
        p.line([(194.4, yy), (212, yy)], w=0.3, color=col)
        p.line([(232, yy), (262, yy)], w=0.3, color=col)
        p.text("+" if k == 0 else "-", 64, yy - 0.4, 1.6)
    # JB
    p.box(88, y - 6, 18, 12, None, stroke=BLUE)
    _term(p, 97.2, y - 1.6, t[0])
    _term(p, 97.2, y + 1.6, t[1])
    p.text(pt["jb"], 97, y - 7.2, 1.8, "middle", bold=True, color=BLUE)
    p.text(f"FC-{pt['tag']}", 76, y - 3.3, 1.5, "middle", color=GREY)
    p.text("1pr 1.5 mm2", 76, y + 4.4, 1.5, "middle", color=GREY)
    # multicore
    p.text(f"{pt['multicore']}", 153, y - 3.0, 1.8, "middle", bold=True)
    p.text(f"pair {pt['mc_pair']}  ({pt['mc_length_m']} m)", 153, y + 5.0, 1.6, "middle", color=GREY)
    # marshalling
    cab = pt["far_cabinet"].split("/")[1]
    p.box(186, y - 6, 18, 12, None)
    _term(p, 192.2, y - 1.6, mt[0])
    _term(p, 192.2, y + 1.6, mt[1])
    p.text(cab, 195, y - 7.2, 1.7, "middle", bold=True)
    p.text(pt["marsh_terminals"].split("-")[0], 198.5, y + 0.8, 1.5)
    iso = "SIL 3 isolator" if sis or pt["system"] in ("SIS", "BMS") else "IS isolator"
    if pt["io_type"] in ("DI", "DO"):
        iso = "IS relay / NAMUR" if pt["io_type"] == "DI" else ("SIL relay" if sis else "interposing relay")
    p.box(212, y - 5, 20, 10, None, fill="#FFF7E6")
    p.text(iso.split()[0], 222, y - 0.5, 1.7, "middle", bold=True)
    p.text(" ".join(iso.split()[1:]), 222, y + 2.3, 1.5, "middle")
    # I/O card
    p.box(262, y - 7, 40, 14, None, stroke=col)
    p.text(f"{pt['io_card']}", 282, y - 3.2, 1.9, "middle", bold=True, color=col)
    p.text(f"{pt['io_type']} ch {pt['io_channel']:02d}", 282, y + 0.4, 1.8, "middle")
    p.text(pt["signal"], 282, y + 3.6, 1.25, "middle", color=GREY)
    p.line([(302, y), (318, y)], w=0.3, color=col, arrow=pt["io_type"] in ("AI", "DI"),
           start_arrow=pt["io_type"] in ("AO", "DO"))
    p.text(power, 14, y + 10.5, 1.5, color=GREY)
    return (318, y)


def _notes(p, x, y, items, w=230):
    p.text("NOTES", x, y, 2.4, bold=True)
    yy = y + 3.6
    for i, s in enumerate(items):
        for j, ln in enumerate(p.wrap(s, w, 1.9)):
            p.text((f"{i + 1}. " if j == 0 else "    ") + ln, x, yy, 1.9)
            yy += 2.8
    return yy


def ld_001(P):
    sh = Sheet("A3", "LOOP DIAGRAM", "FIC-1031 C-101 REFLUX FLOW (CASCADE FROM TIC-1030)", "CFU-100-IC-LD-001",
               sheet="1 OF 3", discipline="INSTRUMENTATION")
    p = Pen(sh)
    _frame(p, 14, 150)
    ft, fv = P["FT-1031"], P["FV-1031"]
    a = _row(p, 45, ft, ["FT-1031 DP flow transmitter", "on FE-1031 orifice (P-103 disch.)", f"{ft['range']} {ft['units']}"],
             "tx")
    b = _row(p, 100, fv, ["FV-1031 globe valve 4\" (CAL-001)", "smart HART positioner, FO", "IA 7 barg, filter-reg."],
             "pos", power="4-20 mA from AO card, HART; positioner loop-powered")
    # controller
    p.box(326, 30, 76, 90, None, stroke=BLUE, fill="none")
    p.text(f"DCS {ft['controller']} (redundant)", 364, 35, 2.2, "middle", bold=True, color=BLUE)
    ai = p.fy(340, 45, "AI", None, s=7)
    fic = p.bubble(364, 72, "FIC-1031", "dcs", r=5.5)
    ao = p.fy(340, 100, "AO", None, s=7)
    tic = p.bubble(390, 50, "TIC-1030", "dcs", r=5.0)
    p.soft([ai["e"], (364, 45), fic["n"]])
    p.soft([tic["s"], (390, 72), fic["e"]])
    p.text("CAS SP", 386, 70, 1.6, "end", color=GREY)
    p.soft([fic["s"], (364, 100), ao["e"]])
    p.line([a, ai["w"]], w=0.3, arrow=True)
    p.line([ao["w"], b], w=0.3, arrow=True)
    m = p.bubble(390, 32 + 6, "MPC-", "apc", r=3.2) if False else None
    p.text("SP of TIC-1030 from MPC (CDU)", 366, 115, 1.7, "middle", color=APC_GRN)
    p.text("HMI: faceplate, trend, alarms FAL/FAH", 366, 118, 1.6, "middle", color=GREY)
    _notes(p, 14, 160, [
        "Cable FC- = field (branch) cable 1 pair 1.5 mm2 screened, IS blue sheath; multicore 12/24 pair, armoured, "
        "overall + individual screens; screens earthed at FAR-100 IS earth bar only.",
        "Terminal numbers, JB, multicore, cabinet and card/channel assignments from CFU-000-IC-IOL-001 "
        "(data/io_list.json) - final at detailed design.",
        "Positioner fail action: air failure -> valve OPEN (FO, reflux to column top on air loss).",
        "FIC-1031 in CAS from TIC-1030; on TIC bad PV the FIC sheds to AUTO at last SP (bumpless).",
        "Power: AI/AO cards 24 VDC from redundant cabinet PSUs fed by UPS-101A/B (UDB-101A/B).",
    ])
    sh.save(OUT / "loop-diagrams" / "CFU-100-IC-LD-001_FIC-1031")


def ld_002(P):
    sh = Sheet("A3", "LOOP DIAGRAM", "TIC-1020 / PIC-1021 H-101 COT -> FUEL GAS PRESSURE CASCADE", "CFU-100-IC-LD-002",
               sheet="2 OF 3", discipline="INSTRUMENTATION")
    p = Pen(sh)
    _frame(p, 14, 150)
    tt, pt, pv = P["TT-1020"], P["PT-1021"], P["PV-1021"]
    a = _row(p, 36, tt, ["TT-1020 COT (duplex TC, head TX)", "H-101 combined outlet", f"{tt['range']} {tt['units']}"])
    b = _row(p, 76, pt, ["PT-1021 FG burner pressure", "downstream PV-1021", f"{pt['range']} {pt['units']}"])
    c = _row(p, 116, pv, ["PV-1021 FG control valve 4\"", "smart positioner, FC", "IA 7 barg"], "pos",
             power="4-20 mA from AO card, HART")
    p.box(326, 22, 76, 112, None, stroke=BLUE, fill="none")
    p.text(f"DCS {tt['controller']} (redundant)", 364, 27, 2.2, "middle", bold=True, color=BLUE)
    ai1 = p.fy(338, 36, "AI", None, s=6)
    ai2 = p.fy(338, 76, "AI", None, s=6)
    ao = p.fy(338, 116, "AO", None, s=6)
    tic = p.bubble(360, 44, "TIC-1020", "dcs", r=5.0)
    sm = p.fy(382, 44, "Σ", "FF", s=6, tag_pos="t")
    lo = p.fy(382, 64, "<", None, s=6)
    p.text("x-limit", 386, 66, 1.5, color=GREY)
    fx = p.fy(382, 82, "f(x)", None, s=6)
    pic = p.bubble(360, 96, "PIC-1021", "dcs", r=5.0)
    p.soft([ai1["e"], (360, 36), tic["n"]])
    p.soft([tic["e"], sm["w"]])
    p.soft([sm["s"], lo["n"]])
    p.soft([lo["s"], fx["n"]])
    p.soft([fx["s"], (382, 96), pic["e"]])
    p.soft([ai2["e"], (350, 76), (350, 96), pic["w"]])
    p.soft([pic["s"], (360, 116), ao["e"]])
    p.text("FIC-1001 / CIT", 396, 38, 1.5, "end", color=GREY)
    p.soft([(398, 44), sm["e"]])
    p.text("air avail.", 398, 62, 1.5, "end", color=GREY)
    p.soft([(398, 64), lo["e"]])
    p.line([a, ai1["w"]], w=0.3, arrow=True)
    p.line([b, ai2["w"]], w=0.3, arrow=True)
    p.line([ao["w"], c], w=0.3, arrow=True)
    p.text("BMS: PIC-1021 forced to min / track on trip", 364, 128, 1.6, "middle", color=SIS_RED)
    p.text("(XV-1021/1022 closed, see LD-003)", 364, 131, 1.6, "middle", color=SIS_RED)
    _notes(p, 14, 160, [
        "TT-1020 (BPCS) is independent of the SIS transmitters TT-1020A/B/C (SIF-106); separate thermowells.",
        "Cascade: TIC-1020 output + feed-forward (charge x dT, lead-lag) -> fuel demand -> low select with air "
        "available (cross-limiting) -> burner curve f(x) -> PIC-1021 SP. See CFU-100-IC-CSD-001.",
        "PV-1021 fail-closed (FC) on air failure; min-fire mechanical stop not used (min-fire in DCS logic).",
        "Terminal / cable data from CFU-000-IC-IOL-001 (data/io_list.json).",
    ])
    sh.save(OUT / "loop-diagrams" / "CFU-100-IC-LD-002_TIC-1020-PIC-1021")


def ld_003(P):
    sh = Sheet("A3", "LOOP DIAGRAM", "SIF-101 H-101 PASS 1 LOW-LOW FLOW (2oo3) -> FUEL SSOVs", "CFU-100-IC-LD-003",
               sheet="3 OF 3", discipline="INSTRUMENTATION")
    p = Pen(sh)
    _frame(p, 14, 196)
    ys = [33, 54, 75]
    rows = []
    for t, y in zip(("FT-1011A", "FT-1011B", "FT-1011C"), ys):
        q = P[t]
        rows.append(_row(p, y, q, [f"{t} DP flow TX (SIL 2 cert.)", "dedicated taps on FE-1011", f"{q['range']} {q['units']}"],
                         "tx", sis=True))
    rows.append(_row(p, 105, P["XV-1021"], ["XV-1021 FG SSOV (FC)", "SOV 24 VDC de-energise to trip",
                                              "+ ZSO/ZSC, partial stroke"], "sov", sis=True,
                     power="24 VDC SOV from SIS DO card (line-monitored)"))
    rows.append(_row(p, 126, P["XV-1022"], ["XV-1022 FG SSOV (FC)", "SOV 24 VDC de-energise to trip",
                                              "+ ZSO/ZSC"], "sov", sis=True,
                     power="24 VDC SOV from SIS DO card (line-monitored)"))
    rows.append(_row(p, 147, P["ZSC-1021"], ["ZSC-1021 closed limit switch", "proof of closure (BMS)", ""], "ls",
                     sis=True, power="NAMUR / dry contact to SIS DI"))
    rows.append(_row(p, 168, P["XV-1230"], ["XV-1230 FG vent valve (FO)", "DB&B vent - opens on trip", ""], "sov",
                     sis=True, power="24 VDC SOV from SIS DO card"))
    ctl = P["FT-1011A"]["controller"]
    p.box(326, 22, 76, 162, None, stroke=SIS_RED, fill="none")
    p.text(f"SIS LOGIC SOLVER - {ctl}", 364, 27, 2.1, "middle", bold=True, color=SIS_RED)
    p.text("(SIL 3 capable, TMR / 2oo4D)", 364, 30, 1.7, "middle", color=SIS_RED)
    fz = p.bubble(345, 54, "FZLL-1011", "sis", r=5.5)
    vote = p.fy(370, 54, "2oo3", None, s=8, color=SIS_RED)
    orb = p.fy(370, 90, "OR", None, s=8, color=SIS_RED)
    p.text("passes 1..8", 375, 84.5, 1.5, color=GREY)
    for x0, y in zip([r[0] for r in rows[:3]], ys):
        p.line([(318, y), (330, y), (338, 54)], w=0.3, color=SIS_RED, arrow=False)
    p.line([(fz["e"][0], 54), (vote["w"][0], 54)], w=0.3, color=SIS_RED, arrow=True)
    p.line([vote["s"], orb["n"]], w=0.3, color=SIS_RED, arrow=True)
    for x in (390, 394):
        p.line([(x, 50), (x, 90)], w=0.25, color=GREY, dash="1,1")
    p.text("FZLL-1012..1018, SIF-102..106, ESD", 398, 47, 1.4, "end", color=GREY)
    p.line([(392, 90), orb["e"]], w=0.3, color=SIS_RED, arrow=True)
    lat = p.fy(370, 116, "S/R", None, s=8, color=SIS_RED)
    p.text("latch, CCR reset", 375, 122, 1.5, color=GREY)
    p.line([orb["s"], lat["n"]], w=0.3, color=SIS_RED, arrow=True)
    for y in (105, 126, 168):
        p.line([(366, 120), (366, y), (318, y)], w=0.3, color=SIS_RED, arrow=True)
    p.line([(318, 147), (350, 147)], w=0.3, color=SIS_RED)
    p.text("proof of closure -> BMS", 352, 148, 1.5, color=GREY)
    p.text("-> SOE / first-out (1 ms)", 364, 176, 1.6, "middle", color=GREY)
    p.text("-> DCS via read-only gateway", 364, 179, 1.6, "middle", color=GREY)
    p.text("Trip SP: 40 % of design pass flow", 364, 36, 1.6, "middle", color=SIS_RED)
    _notes(p, 14, 202, [
        "SIL 2 per LOPA (CFU-000-IC-RPT-002). 2oo3 voting with 2oo2 on one transmitter in bypass / fault; deviation "
        "alarm between A/B/C (5 %).",
        "Final elements: XV-1021 and XV-1022 in series (1oo2) with vent XV-1230 (double block & bleed); also "
        "pilot XV-1026 (SIF-101 / BMS). Proof-test interval 12 months (partial stroke 3 months).",
        "Field cables and JBs for SIS are segregated (red sheath / labels); SIS multicores separate from DCS.",
        "Terminal / cable data from CFU-000-IC-IOL-001 (data/io_list.json).",
    ], w=300)
    sh.save(OUT / "loop-diagrams" / "CFU-100-IC-LD-003_SIF-101")


def build():
    P = _pts()
    if not P:
        print("  WARNING: io_list.json missing - loop diagrams skipped")
        return []
    (OUT / "loop-diagrams").mkdir(parents=True, exist_ok=True)
    ld_001(P)
    ld_002(P)
    ld_003(P)
    return ["CFU-100-IC-LD-001", "CFU-100-IC-LD-002", "CFU-100-IC-LD-003"]
