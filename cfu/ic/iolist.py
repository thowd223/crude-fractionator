"""I/O list CFU-000-IC-IOL-001 (xlsx) and data/io_list.json, derived from data/instruments.json.

Rules (FEED):
  * every instrument with a field signal becomes one or more I/O points (AI/AO/DI/DO);
    'Local' instruments and soft function blocks have no physical I/O;
  * shutdown valves (DO SOV + 2 DI) expand to XV (DO), ZSO (DI), ZSC (DI);
  * BMS = heater burner-management functions (SIF-101..106, SIF-201/202, flame scanners) - hosted in the
    SIS logic solver hardware but configured as a separate application;
  * motor interfaces (run / available DI, start / stop DO) are derived from equipment.json drivers;
  * F&G field devices are a FEED allowance per fire zone (detector mapping study to follow);
  * I&C additions from the control philosophy (analysers, FG flow, ambient T) are flagged 'I&C addition';
  * DCS controller allocation by P&ID sheet / area; SIS split CDU / VDU;
  * installed spare: each I/O card filled to <= ~80 % (AI 13/16, AO 6/8, DI 26/32, DO 13/16) -> >= 20 % spare.
Junction boxes are zoned on a 40 m x 30 m grid of the plot (data/layout.json); one JB per system per zone
(split at 24 pairs); multicores run to the marshalling cabinets in FAR-100.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, OrderedDict, defaultdict

from .common import DATA, OUT, load

CARD = {"AI": (16, 13), "AO": (8, 6), "DI": (32, 26), "DO": (16, 13)}      # channels, max used
JB_PAIRS = 24
GRID = (40.0, 30.0)

SHEET_CTRL = {1: "CDU-1", 2: "CDU-1", 3: "CDU-1", 4: "CDU-1", 5: "CDU-1", 6: "CDU-2", 7: "CDU-2", 8: "CDU-2",
              9: "CDU-2", 10: "CDU-2", 11: "CDU-2", 12: "VDU", 13: "VDU", 14: "VDU", 15: "VDU", 16: "CDU-1"}
SHEET_EQ = {1: "P-101A", 2: "D-101A", 3: "E-108A", 4: "H-101", 5: "H-101", 6: "C-101", 7: "C-101", 8: "C-103",
            9: "D-102", 10: "C-105", 11: "C-106", 12: "H-201", 13: "C-201", 14: "C-201", 15: "D-201", 16: "D-103"}
BMS_SIFS = {"SIF-101", "SIF-102", "SIF-103", "SIF-104", "SIF-105", "SIF-106", "SIF-201", "SIF-202"}

# I&C additions (control philosophy) - not yet in the instrument index; reported upstream
IC_ADDITIONS = [
    ("AT-1038", "Analyser transmitter", "Unstabilised naphtha D86 end point / RVP (online)", "CDU-2", 9, "AI"),
    ("AT-1046", "Analyser transmitter", "Salt-in-crude, desalted crude", "CDU-1", 2, "AI"),
    ("AT-1047", "Analyser transmitter", "BS&W, desalted crude", "CDU-1", 2, "AI"),
    ("AT-1048", "Analyser transmitter", "Crude API / density, salt, BS&W at charge (crude switch DV)", "CDU-1", 1, "AI"),
    ("AT-1049", "Analyser transmitter", "Oil-in-water, desalter brine", "CDU-1", 2, "AI"),
    ("AT-1055", "Analyser transmitter", "Kerosene flash / freeze point (online)", "CDU-2", 8, "AI"),
    ("AT-1065", "Analyser transmitter", "Diesel D86 T95 / cloud point (online)", "CDU-2", 8, "AI"),
    ("AT-1075", "Analyser transmitter", "AGO D86 T95 / colour (online)", "CDU-2", 8, "AI"),
    ("AT-1099", "Analyser transmitter", "LPG C5+ (process GC)", "CDU-2", 10, "AI"),
    ("AT-1108", "Analyser transmitter", "Light naphtha C6+ / RVP (process GC)", "CDU-2", 11, "AI"),
    ("AT-1109", "Analyser transmitter", "Heavy naphtha IBP / C5- (process GC)", "CDU-2", 11, "AI"),
    ("AT-1021", "Analyser transmitter", "Fuel gas Wobbe index / LHV (calorimeter)", "CDU-1", 16, "AI"),
    ("FT-1021", "Flow transmitter", "H-101 fuel gas flow (cross-limiting fuel measurement)", "CDU-1", 5, "AI"),
    ("FT-2006", "Flow transmitter", "H-201 fuel gas flow (cross-limiting fuel measurement)", "VDU", 12, "AI"),
    ("TT-9005", "Temperature transmitter", "Ambient air temperature (APC DV)", "CDU-2", 16, "AI"),
    ("AT-2032", "Analyser transmitter", "Vacuum off-gas H2S (D-202, to H-201 firing / SO2 emissions)", "VDU", 15, "AI"),
    ("XA-9101", "Analyser house common alarm", "AH-101 analyser house common trouble / HVAC", "CDU-2", 16, "DI"),
]

# F&G allowance per fire zone: (zone, description, x, y, gas det, flame det, MCP, beacon/sounder, H2S det)
FG_ZONES = [
    ("FZ-01", "Desalting & crude charge", 35, 55, 6, 2, 3, 3, 0),
    ("FZ-02", "Preheat exchanger bank", 28, 100, 6, 3, 3, 3, 0),
    ("FZ-03", "C-101 / strippers / OH system & pumps", 100, 92, 10, 4, 4, 4, 4),
    ("FZ-04", "Light ends C-105/C-106 & LPG pumps", 58, 95, 10, 3, 3, 3, 2),
    ("FZ-05", "Fired heaters H-101/H-201 & FG KO", 130, 35, 8, 4, 4, 4, 0),
    ("FZ-06", "VDU C-201, ejectors & hotwell", 185, 98, 8, 3, 3, 3, 4),
]


def _sheet_no(s):
    m = re.search(r"PID-(\d{3})", s or "")
    return int(m.group(1)) if m else 0


def _layout_xy():
    L = load("layout.json")
    xy = {e["tag"]: (e["x"], e["y"]) for e in L["equipment"]}
    for b in L["structures"].get("buildings", []):
        xy[b["id"]] = ((b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2)
    return xy


def _equip_for(inst, XY, loops):
    txt = " ".join([inst.get("service", ""), inst.get("note", "")])
    L = loops.get(inst.get("loop", ""), {})
    txt += " " + L.get("measured", "") + " " + L.get("service", "")
    for m in re.finditer(r"\b([CDEHPAKJX])-(\d{3})([A-D])?", txt):
        base = f"{m.group(1)}-{m.group(2)}"
        for cand in (base + (m.group(3) or ""), base, base + "A", base + "-B1"):
            if cand in XY:
                return cand
    return SHEET_EQ.get(_sheet_no(inst.get("pid_sheet")), "C-101")


def _zone(x, y):
    cx = int(x // GRID[0])
    cy = int(y // GRID[1])
    return f"{'ABCDEF'[min(cx, 5)]}{cy + 1}"


def _points(inst):
    """Expand an index row into (io_type, tag, description) tuples."""
    sig = inst["signal"]
    t = inst["tag"]
    if inst["system"] == "Local" or sig.startswith("Soft") or sig.startswith("-"):
        return []
    if t.startswith("ZSC-") and "limit switch on xv" in inst["service"].lower():
        return []                                    # already counted with its XV (2 x DI)
    if t.startswith("UZ-"):
        return []                                    # logic function, no field I/O
    if "SOV" in sig:
        n = t.split("-", 1)[1]
        return [("DO", t, "SOV de-energise to trip"), ("DI", f"ZSO-{n}", "Open limit switch"),
                ("DI", f"ZSC-{n}", "Closed limit switch")]
    if t.startswith("BS-"):
        m = re.search(r"(\d+)\s*off", inst["service"])
        n = int(m.group(1)) if m else 6
        return [("DI", f"{t}-{k + 1:02d}", f"Flame scanner burner {k + 1} (flame on)") for k in range(n)]
    if "AO" in sig:
        return [("AO", t, "Valve positioner / output")]
    if sig.startswith("DI"):
        return [("DI", t, "")]
    if sig.startswith("DO"):
        return [("DO", t, "")]
    if "4-20" in sig:
        return [("AI", t, "")]
    return []


def _system(inst):
    s = inst["system"]
    if inst["tag"].startswith("BS-") or inst.get("sif") in BMS_SIFS:
        return "BMS"
    return {"F&G": "F&G"}.get(s, s)


def _controller(system, sheet, eq):
    if system == "DCS":
        return SHEET_CTRL.get(sheet, "CDU-1")
    if system == "BMS":
        return "BMS-H201" if eq.startswith("H-2") or sheet == 12 else "BMS-H101"
    if system == "SIS":
        return "SIS-1"
    return "FGS-1"


def build_io():
    inst = load("instruments.json")
    if not inst:
        return None
    loops = {l["tag"]: l for l in load("control_loops.json")["loops"]}
    sifs = {s["tag"]: s for s in load("control_loops.json")["sifs"]}
    XY = _layout_xy()
    rows = []
    for it in inst:
        pts = _points(it)
        if not pts:
            continue
        sh = _sheet_no(it["pid_sheet"])
        eq = _equip_for(it, XY, loops)
        sysm = _system(it)
        for io, tag, d in pts:
            rows.append(dict(tag=tag, parent=it["tag"], type=it["type"], service=it["service"] + (f" - {d}" if d else ""),
                             loop=it["loop"], pid_sheet=it["pid_sheet"], system=sysm, io_type=io,
                             signal=_sigtxt(io, sysm, it["signal"]), equipment=eq,
                             controller=_controller(sysm, sh, eq), sif=it.get("sif", ""),
                             sil=it.get("sil_ref", ""), range=it.get("range", ""), units=it.get("units", ""),
                             source="instrument index"))
    # I&C additions
    for tag, typ, svc, ctl, sh, io in IC_ADDITIONS:
        eq = SHEET_EQ.get(sh, "C-101")
        rows.append(dict(tag=tag, parent=tag, type=typ, service=svc, loop=tag, pid_sheet=f"(P&ID sheet {sh:03d})",
                         system="DCS", io_type=io, signal=_sigtxt(io, "DCS", "4-20 mA HART"), equipment=eq,
                         controller=ctl, sif="", sil="", range="", units="",
                         source="I&C addition (add to index)"))
    # motor interfaces
    E = load("equipment.json")
    for e in E:
        kw = e.get("motor_kw")
        if not kw or e["type"] not in ("Pump", "Fan", "Air cooler", "Package"):
            continue
        tags = _drivers(e["tag"])
        for t in tags:
            sh = _motor_sheet(t)
            ctl = "VDU" if re.match(r"[PAK]-2", t) else SHEET_CTRL.get(sh, "CDU-1")
            eqxy = t if t in XY else (t[:-1] if t[:-1] in XY else e["tag"].split("/")[0])
            for io, sfx, d in (("DI", "XL", "Motor running"), ("DI", "XA", "Motor fault / not available"),
                               ("DO", "HS-START", "Start command"), ("DO", "HS-STOP", "Stop command")):
                rows.append(dict(tag=f"{t} {sfx}", parent=t, type="Motor interface (MCC)",
                                 service=f"{e['service']} {t} - {d} ({kw} kW)", loop=t, pid_sheet="",
                                 system="DCS", io_type=io, signal=_sigtxt(io, "DCS", ""), equipment=eqxy,
                                 controller=ctl, sif="", sil="", range="", units="",
                                 source="equipment.json (MCC hardwired interface)"))
    # SIS motor trips (from C&E)
    from .ce import motor_trips
    for t, sif, why in motor_trips():
        sysm = "SIS"
        ctl = "SIS-1"
        rows.append(dict(tag=f"XY-{t}", parent=t, type="Motor trip relay (SIS)", service=f"{t} trip ({why})",
                         loop=sif, pid_sheet="", system=sysm, io_type="DO", signal=_sigtxt("DO", sysm, "relay"),
                         equipment=t if t in XY else t[:-1] if t[:-1] in XY else "C-101", controller=ctl,
                         sif=sif, sil=sifs.get(sif, {}).get("sil", ""), range="", units="",
                         source="C&E CFU-000-IC-CE-001"))
    # F&G allowance
    for z, d, x, y, g, f, mcp, bcn, h2s in FG_ZONES:
        for kind, n, io, typ in (("GD", g, "AI", "Flammable gas detector (IR point)"),
                                 ("BD", f, "AI", "Flame detector (IR3)"), ("HS", mcp, "DI", "Manual call point"),
                                 ("XL", bcn, "DO", "Beacon / sounder"), ("AT", h2s, "AI", "H2S detector")):
            for k in range(n):
                rows.append(dict(tag=f"{kind}-{z[3:]}{k + 1:02d}", parent=z, type=typ, service=f"{d} ({z})",
                                 loop=z, pid_sheet="", system="F&G", io_type=io, signal=_sigtxt(io, "F&G", ""),
                                 equipment=z, controller="FGS-1", sif="", sil="SIL 2 (F&G)", range="",
                                 units="", source="F&G allowance (mapping study)", x=x, y=y))
    # zoning, JB, cabinets, channels
    _assign(rows, XY)
    tot = _totals(rows)
    return dict(doc="CFU-000-IC-IOL-001", rev="A", generated_by="cfu.ic.iolist",
                basis=__doc__.strip(), points=rows, totals=tot)


def _drivers(tag):
    m = re.match(r"([A-Z]-\d{3})([A-D](?:/[A-D])*)?$", tag.replace("-B1", ""))
    if m and m.group(2):
        return [m.group(1) + s for s in m.group(2).split("/")]
    return [tag]


def _motor_sheet(t):
    n = int(re.search(r"\d{3}", t).group(0))
    table = {101: 1, 114: 2, 118: 2, 102: 2, 120: 5, 112: 6, 106: 7, 107: 7, 108: 7, 109: 8, 110: 8, 111: 8, 103: 9,
             104: 9, 105: 9, 115: 10, 116: 11, 117: 11}
    if t.startswith("K-1"):
        return 5
    if t.startswith("A-1"):
        return 9 if n in (101,) else 8 if n in (103, 104, 105) else 10 if n == 106 else 11
    if t.startswith("X-"):
        return 2
    return table.get(n, 16 if n < 200 else 14)


def _sigtxt(io, sysm, sig):
    if io == "AI":
        return "4-20 mA HART, 2-wire, IS (Ex ia)" if sysm != "F&G" else "4-20 mA, 3-wire (F&G)"
    if io == "AO":
        return "4-20 mA HART to smart positioner"
    if io == "DI":
        return "24 VDC dry contact / NAMUR"
    return "24 VDC, de-energise to trip" if sysm in ("SIS", "BMS") else "24 VDC interposing relay"


def _assign(rows, XY):
    far = XY.get("FAR-100", (55, 11))
    by_jb = defaultdict(list)
    for r in rows:
        if "x" in r:
            x, y = r.pop("x"), r.pop("y")
        else:
            x, y = XY.get(r["equipment"], (100, 90))
        r["zone"] = _zone(x, y)
        r["xy"] = (round(x, 1), round(y, 1))
        sysk = {"DCS": "D", "SIS": "S", "BMS": "B", "F&G": "F"}[r["system"]]
        sig = "A" if r["io_type"] in ("AI", "AO") else "D"
        by_jb[(sysk, sig, r["zone"])].append(r)
    for (sysk, sig, zone), rs in sorted(by_jb.items()):
        rs.sort(key=lambda r: r["tag"])
        for i, r in enumerate(rs):
            k = i // JB_PAIRS
            jb = f"JB-{sysk}{sig}-{zone}" + (f"-{k + 1}" if len(rs) > JB_PAIRS else "")
            pair = i % JB_PAIRS + 1
            r["jb"] = jb
            r["jb_terminals"] = f"{2 * pair - 1}/{2 * pair}"
            r["multicore"] = f"MC-{jb[3:]}"
            r["mc_pair"] = pair
            x, y = r["xy"]
            r["mc_length_m"] = int(round((abs(x - far[0]) + abs(y - far[1])) * 1.2 + 20, -1))
    # channels per controller / io type
    by_ctl = defaultdict(list)
    for r in rows:
        by_ctl[(r["controller"], r["io_type"])].append(r)
    for (ctl, io), rs in sorted(by_ctl.items()):
        rs.sort(key=lambda r: (r["zone"], r["tag"]))
        ch, used = CARD[io]
        for i, r in enumerate(rs):
            card = i // used + 1
            c = i % used + 1
            r["io_card"] = f"{ctl}-{io}{card:02d}"
            r["io_channel"] = c
            mc_no = (i // 120) + 1
            r["far_cabinet"] = f"FAR-100/{_cabpref(r['system'])}-{ctl}-{io[0]}{mc_no:02d}"
            r["marsh_terminals"] = f"TB{card:02d}-{2 * c - 1}/{2 * c}"


def _cabpref(s):
    return {"DCS": "MC", "SIS": "SMC", "BMS": "SMC", "F&G": "FMC"}[s]


def _totals(rows):
    tot = OrderedDict()
    for r in rows:
        t = tot.setdefault(r["controller"], dict(system=r["system"], AI=0, AO=0, DI=0, DO=0))
        t[r["io_type"]] += 1
    out = OrderedDict()
    order = ["CDU-1", "CDU-2", "VDU", "SIS-1", "BMS-H101", "BMS-H201", "FGS-1"]
    for ctl in order + [k for k in tot if k not in order]:
        if ctl not in tot:
            continue
        t = tot[ctl]
        d = dict(system=t["system"])
        for io in ("AI", "AO", "DI", "DO"):
            n = t[io]
            ch, used = CARD[io]
            cards = math.ceil(n / used) if n else 0
            inst = cards * ch
            d[io] = dict(used=n, cards=cards, installed=inst, spare=inst - n,
                         spare_pct=round(100 * (inst - n) / n, 1) if n else 0.0)
        d["used"] = sum(d[io]["used"] for io in ("AI", "AO", "DI", "DO"))
        d["installed"] = sum(d[io]["installed"] for io in ("AI", "AO", "DI", "DO"))
        out[ctl] = d
    sysz = OrderedDict()
    for ctl, d in out.items():
        s = sysz.setdefault(d["system"], dict(AI=0, AO=0, DI=0, DO=0, used=0, installed=0))
        for io in ("AI", "AO", "DI", "DO"):
            s[io] += d[io]["used"]
        s["used"] += d["used"]
        s["installed"] += d["installed"]
    grand = dict(used=sum(s["used"] for s in sysz.values()), installed=sum(s["installed"] for s in sysz.values()))
    src = Counter(r["source"] for r in rows)
    return dict(by_controller=out, by_system=sysz, grand=grand, by_source=dict(src))


def write_xlsx(io, path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    hdr = PatternFill("solid", fgColor="1F3864")
    hf = Font(color="FFFFFF", bold=True)
    thin = Side(style="thin", color="999999")
    bd = Border(left=thin, right=thin, top=thin, bottom=thin)
    ws = wb.active
    ws.title = "Summary"
    ws["A1"] = "CFU-000-IC-IOL-001  I/O LIST - SUMMARY (Rev A, FEED)"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = "100 kBPSD Crude & Vacuum Distillation Unit - derived from data/instruments.json; spare >= 20 % installed"
    cols = ["Controller", "System", "AI used", "AI inst.", "AO used", "AO inst.", "DI used", "DI inst.", "DO used",
            "DO inst.", "Total used", "Total installed", "Spare %", "Cards AI/AO/DI/DO"]
    for j, c in enumerate(cols, 1):
        cell = ws.cell(4, j, c)
        cell.fill, cell.font, cell.border = hdr, hf, bd
    r = 5
    for ctl, d in io["totals"]["by_controller"].items():
        vals = [ctl, d["system"]]
        for k in ("AI", "AO", "DI", "DO"):
            vals += [d[k]["used"], d[k]["installed"]]
        vals += [d["used"], d["installed"], round(100 * (d["installed"] - d["used"]) / d["used"], 1),
                 "/".join(str(d[k]["cards"]) for k in ("AI", "AO", "DI", "DO"))]
        for j, v in enumerate(vals, 1):
            ws.cell(r, j, v).border = bd
        r += 1
    r += 1
    ws.cell(r, 1, "Totals per system").font = Font(bold=True)
    r += 1
    for j, c in enumerate(["System", "AI", "AO", "DI", "DO", "Used", "Installed"], 1):
        cell = ws.cell(r, j, c)
        cell.fill, cell.font, cell.border = hdr, hf, bd
    r += 1
    for s, d in io["totals"]["by_system"].items():
        for j, v in enumerate([s, d["AI"], d["AO"], d["DI"], d["DO"], d["used"], d["installed"]], 1):
            ws.cell(r, j, v).border = bd
        r += 1
    ws.cell(r, 1, "GRAND TOTAL").font = Font(bold=True)
    ws.cell(r, 6, io["totals"]["grand"]["used"]).font = Font(bold=True)
    ws.cell(r, 7, io["totals"]["grand"]["installed"]).font = Font(bold=True)
    r += 2
    ws.cell(r, 1, "Points by source").font = Font(bold=True)
    for s, n in io["totals"]["by_source"].items():
        r += 1
        ws.cell(r, 1, s)
        ws.cell(r, 2, n)
    for j, w in enumerate([14, 8] + [9] * 10 + [9, 18], 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    # detail
    ws = wb.create_sheet("I-O List")
    keys = ["tag", "parent", "type", "service", "loop", "pid_sheet", "system", "controller", "io_type", "signal",
            "io_card", "io_channel", "far_cabinet", "marsh_terminals", "jb", "jb_terminals", "multicore", "mc_pair",
            "mc_length_m", "zone", "equipment", "sif", "sil", "range", "units", "source"]
    heads = ["Tag", "Parent tag", "Type", "Service", "Loop", "P&ID", "System", "Controller", "I/O", "Signal",
             "I/O card", "Ch.", "FAR-100 cabinet", "Marsh. terminals", "JB", "JB term.", "Multicore", "Pair",
             "MC length m", "Zone", "Equipment", "SIF", "SIL", "Range", "Units", "Source"]
    for j, h in enumerate(heads, 1):
        c = ws.cell(1, j, h)
        c.fill, c.font, c.border = hdr, hf, bd
        c.alignment = Alignment(wrap_text=True, vertical="top")
    order = {"CDU-1": 0, "CDU-2": 1, "VDU": 2, "SIS-1": 3, "BMS-H101": 4, "BMS-H201": 5, "FGS-1": 6}
    pts = sorted(io["points"], key=lambda p: (order.get(p["controller"], 9), p["io_type"], p["io_card"],
                                              p["io_channel"]))
    for i, p in enumerate(pts, 2):
        for j, k in enumerate(keys, 1):
            ws.cell(i, j, p.get(k, "")).border = bd
    widths = [16, 13, 26, 52, 12, 20, 7, 10, 5, 28, 14, 5, 26, 14, 16, 8, 16, 5, 8, 6, 10, 9, 8, 9, 7, 30]
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(keys))}{len(pts) + 1}"
    ws = wb.create_sheet("Basis")
    for i, ln in enumerate(io["basis"].splitlines(), 1):
        ws.cell(i, 1, ln)
    ws.column_dimensions["A"].width = 120
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def build():
    io = build_io()
    if io is None:
        print("  WARNING: data/instruments.json missing - I/O list skipped")
        return None
    (DATA / "io_list.json").write_text(json.dumps(io, indent=1, default=list))
    write_xlsx(io, OUT / "CFU-000-IC-IOL-001_IO-List.xlsx")
    return io
