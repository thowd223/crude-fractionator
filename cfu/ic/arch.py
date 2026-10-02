"""ICS architecture block diagram CFU-000-IC-BLK-001 (A1): Purdue levels 0-4 + DMZ, DCS / SIS / BMS / F&G,
IEC 62443 zones & conduits, UPS feeds (data/electrical.json) and I/O counts (data/io_list.json)."""
from __future__ import annotations

from ..drawing.sheet import Sheet
from .common import APC_GRN, BLUE, GREY, OUT, SIS_RED, Pen, load

FG_COL = "#E65100"
ZONES = [
    # id, name, SL-T, colour
    ("Z1", "Enterprise (L4)", "SL 1", "#7F7F7F"),
    ("Z2", "Process DMZ (L3.5)", "SL 2", "#7030A0"),
    ("Z3", "Site operations (L3)", "SL 2", APC_GRN),
    ("Z4", "BPCS / DCS (L2-L1)", "SL 2", BLUE),
    ("Z5", "SIS / BMS (L2-L1)", "SL 3", SIS_RED),
    ("Z6", "F&G (L2-L1)", "SL 3", FG_COL),
    ("Z7", "Packages / MCC / analysers", "SL 2", "#00838F"),
]
CONDUITS = [
    ("C1", "Z1-Z2", "FW-01 (L4/DMZ)", "Historian replica read-only (PI-to-PI), patch/AV distribution, no inbound to L3"),
    ("C2", "Z2-Z3", "FW-02 (DMZ/L3)", "Historian push L3->DMZ only; remote access via jump host + MFA, session recorded"),
    ("C3", "Z3-Z4", "FW-03 (L3/L2)", "OPC UA (APC SP write, historian read), AMS HART pass-through, NTP; whitelisted"),
    ("C4", "Z4-Z5", "SIS gateway (L2/SIS)", "Read-only SIS -> DCS status/first-out via SIL-rated gateway; no DCS writes "
                                             "(bypass/reset by hardwired keyswitch)"),
    ("C5", "Z4-Z6", "F&G gateway", "Read-only F&G -> DCS mimic; F&G executive actions hardwired / SIS"),
    ("C6", "Z4-Z7", "Package gateway", "Modbus TCP / IEC 61850 (MCC IEDs, packages X-101..104, AH-101) via "
                                       "industrial firewall"),
]


def build():
    io = load("io_list.json")
    E = load("electrical.json")
    sh = Sheet("A1", "ICS ARCHITECTURE BLOCK DIAGRAM", "DCS / SIS / BMS / F&G - PURDUE LEVELS & IEC 62443 ZONES",
               "CFU-000-IC-BLK-001", discipline="INSTRUMENTATION")
    p = Pen(sh)
    tot = io["totals"]["by_controller"] if io else {}

    def iot(ctl):
        d = tot.get(ctl)
        if not d:
            return "I/O: TBA (I/O list)"
        return (f"AI {d['AI']['used']}  AO {d['AO']['used']}  DI {d['DI']['used']}  DO {d['DO']['used']}  "
                f"= {d['used']} (inst. {d['installed']})")

    # ---------------------------------------------------------------- level bands
    bands = [("L4", "ENTERPRISE", 18, 44), ("DMZ", "PROCESS DMZ (L3.5)", 48, 80), ("L3", "SITE OPERATIONS", 84, 152),
             ("L2", "SUPERVISORY - CCR (OSBL)", 156, 240), ("L1", "CONTROL - FAR-100 (UNIT)", 250, 390),
             ("L0", "FIELD", 396, 506)]
    for lv, nm, y0, y1 in bands:
        p.gb.add(p.d.rect((15, y0), (630, y1 - y0), fill="#F7F9FC" if lv in ("L4", "L3", "L1") else "white",
                          stroke=GREY, stroke_width=0.25))
        p.gb.add(p.d.rect((15, y0), (16, y1 - y0), fill="#D9E1F2", stroke=GREY, stroke_width=0.25))
        p.text(lv, 23, (y0 + y1) / 2 + 1.5, 4.0, "middle", bold=True, color=BLUE)
        p.text(nm, 23, y0 + 5, 1.7, "middle", color=BLUE) if False else None
        p.text(nm, 35, y0 + 4.2, 2.3, bold=True, color=BLUE)

    def blk(x, y, w, h, title, lines=(), col="black", fill="white", ts=2.6, ls=2.2):
        return p.box(x, y, w, h, title, list(lines), fill=fill, stroke=col, sw=0.45, tsize=ts, lsize=ls,
                     title_color=col)

    # L4
    for i, (t, l) in enumerate([("ERP / MAINTENANCE (CMMS)", "work orders"), ("LIMS", "lab results -> inferentials"),
                                ("PLANNING / LP", "crude slate, targets"), ("CORPORATE HISTORIAN", "PI replica users")]):
        blk(45 + 150 * i, 24, 120, 16, t, [l], col=ZONES[0][3])
    # DMZ
    p.line([(35, 46), (640, 46)], w=0.8, color=SIS_RED)
    p.text("FW-01", 600, 45, 2.2, bold=True, color=SIS_RED)
    for i, (t, l) in enumerate([("HISTORIAN REPLICA", "read-only mirror"), ("PATCH / AV SERVER", "WSUS, AV signatures"),
                                ("REMOTE ACCESS JUMP HOST", "MFA, session recording"), ("BACKUP / FILE TRANSFER",
                                                                                         "data diode option")]):
        blk(45 + 150 * i, 56, 120, 18, t, [l], col=ZONES[1][3])
    p.line([(35, 82), (640, 82)], w=0.8, color=SIS_RED)
    p.text("FW-02", 600, 81, 2.2, bold=True, color=SIS_RED)
    # L3
    l3 = [("PROCESS HISTORIAN (L3)", ["redundant, 1-s data, 5 yr", "SOE / alarm journal"]),
          ("APC SERVER (L3)", ["DMC-type MPC x 3 + LP", "inferential engine (redundant)"]),
          ("ALARM MANAGEMENT", ["ISA 18.2 / EEMUA 191 KPIs", "master alarm database"]),
          ("ASSET MANAGEMENT (AMS)", ["HART diagnostics, valve", "signatures (via HART mux)"]),
          ("OTS", ["operator training simulator", "dynamic model + DCS emulation"]),
          ("DOMAIN / TIME SERVER", ["AD, GPS master clock", "NTP / PTP to L2, L1, SIS"])]
    for i, (t, ls) in enumerate(l3):
        x = 40 + 100 * i
        blk(x, 94, 92, 24, t, ls, col=ZONES[2][3], ts=2.5, ls=2.1)
    p.line([(40, 126), (632, 126)], w=0.6)
    p.text("L3 OPERATIONS LAN (redundant, managed switches)", 42, 124.5, 1.9, color=GREY)
    for i in range(6):
        p.line([(86 + 100 * i, 118), (86 + 100 * i, 126)], w=0.35)
    p.line([(35, 154), (640, 154)], w=0.8, color=SIS_RED)
    p.text("FW-03  (L3 / L2)", 560, 153, 2.2, bold=True, color=SIS_RED)
    p.line([(86, 126), (86, 158)], w=0.35, arrow=True)
    p.line([(186, 126), (186, 158)], w=0.35, arrow=True, color=APC_GRN)
    p.text("OPC UA", 188, 140, 1.9, color=APC_GRN)
    # L2
    l2 = [("OPERATOR CONSOLES (CCR)", ["4 consoles x 4 screens: CDU, VDU,", "light ends/utilities, supervisor",
                                       "+ 2 large overview screens"], "black"),
          ("DCS SERVERS (A/B)", ["redundant HMI / data servers", "engineering station (EWS) x 2"], "black"),
          ("SIS / BMS ENG. STATION", ["separate, key-locked, SIS zone", "SOE + first-out display"], SIS_RED),
          ("F&G MIMIC & PANEL", ["F&G operator station,", "hardwired matrix panel in CCR"], FG_COL),
          ("ESD / HARDWIRED CONSOLE", ["HS-9000 ESD-1 push-button,", "bypass keyswitches, BMS reset"], SIS_RED)]
    xs = [40, 160, 270, 380, 490]
    ws = [112, 102, 102, 102, 140]
    for (t, ls, c), x, w in zip(l2, xs, ws):
        blk(x, 168, w, 26, t, ls, col=c, ts=2.5, ls=2.1)
    p.line([(40, 206), (632, 206)], w=0.7, color=BLUE)
    p.line([(40, 209), (632, 209)], w=0.7, color=BLUE, dash="3,1")
    p.text("DCS CONTROL NETWORK A / B (redundant, IEC 62439 ring) - CCR SWITCHES", 42, 204.5, 1.9, color=BLUE)
    for x, w, c in zip(xs, ws, [BLUE, BLUE, SIS_RED, FG_COL, SIS_RED]):
        p.line([(x + w / 2, 194), (x + w / 2, 206)], w=0.35, color=c)
    # fibre to FAR
    for k, (xx, lab) in enumerate(((110, "FO RING A"), (130, "FO RING B"))):
        p.line([(xx, 209), (xx, 262)], w=0.9, color=BLUE, dash="5,1.5" if k else None)
        p.text(lab, xx + 1.5, 232 + 6 * k, 2.0, bold=True, color=BLUE)
    p.text("2 x 24-core SM fibre, diverse routes CCR (OSBL) <-> FAR-100 (assumed ~ 800 m)", 140, 226, 2.0, color=BLUE)
    p.line([(300, 209), (300, 262)], w=0.9, color=SIS_RED)
    p.text("SIS SAFETY NETWORK (separate fibres)", 302, 232, 2.0, bold=True, color=SIS_RED)
    p.line([(470, 209), (470, 262)], w=0.9, color=FG_COL)
    p.text("F&G NETWORK", 472, 238, 2.0, bold=True, color=FG_COL)
    p.text("FAR-100: pressurised, blast-assessed, x 45-65 / y 5-17 m (layout.json)", 330, 248, 2.0, color=GREY)
    # L1 controllers
    p.line([(40, 262), (632, 262)], w=0.7, color=BLUE)
    p.text("FAR-100 NETWORK SWITCHES (A/B)", 42, 260.5, 1.9, color=BLUE)
    ctls = [("DCS CDU-1 (REDUNDANT PAIR)", "Charge, desalting, preheat, H-101, FG", "CDU-1", BLUE),
            ("DCS CDU-2 (REDUNDANT PAIR)", "C-101, strippers, OH, C-105, C-106", "CDU-2", BLUE),
            ("DCS VDU (REDUNDANT PAIR)", "H-201, C-201, ejectors, VDU products", "VDU", BLUE),
            ("SIS-1 LOGIC SOLVER", "SIL 3 capable (TMR / 2oo4D), ESD + SIFs", "SIS-1", SIS_RED),
            ("BMS H-101", "on SIS hardware, NFPA 85/86, API 556", "BMS-H101", SIS_RED),
            ("BMS H-201", "on SIS hardware, NFPA 85/86, API 556", "BMS-H201", SIS_RED),
            ("F&G SYSTEM FGS-1", "SIL 2 (IEC 61511 / EN 54), redundant", "FGS-1", FG_COL)]
    cx = [40, 125, 210, 300, 385, 470, 555]
    for (t, d, key, c), x in zip(ctls, cx):
        blk(x, 270, 80, 40, t, p.wrap(d, 74, 1.9), col=c, ts=2.1, ls=1.9)
        dd = tot.get(key)
        yy = 296
        if dd:
            for k2, io_ in enumerate(("AI", "AO", "DI", "DO")):
                p.text(f"{io_} {dd[io_]['used']:>3} / {dd[io_]['installed']}", x + 4 + 37 * (k2 % 2),
                       yy + 4 * (k2 // 2), 2.0, bold=True)
            p.text(f"USED {dd['used']} / INSTALLED {dd['installed']}", x + 4, yy + 10.5, 2.0, color=c, bold=True)
        else:
            p.text("I/O: see I/O list", x + 4, yy + 4, 2.0)
        p.line([(x + 40, 262), (x + 40, 270)], w=0.35, color=c)
    # packages & 3rd party
    blk(40, 318, 160, 22, "PACKAGES / 3RD PARTY (ZONE Z7)", ["X-101..X-104 chemical injection PLCs, AH-101 analysers,",
                                                             "K-102 VSD, MCC IEDs (SS-100) - Modbus TCP / IEC 61850"],
        col=ZONES[6][3], ts=2.5, ls=2.0)
    blk(210, 318, 140, 22, "SOE / FIRST-OUT", ["1 ms SOE on SIS / BMS trips,", "time-stamped via GPS/PTP"],
        col=SIS_RED, ts=2.5, ls=2.0)
    blk(360, 318, 130, 22, "HART MUX (AMS)", ["HART pass-through on DCS AI/AO cards", "+ SIS AI (read-only)"],
        col=ZONES[2][3], ts=2.5, ls=2.0)
    blk(500, 318, 132, 22, "HARDWIRED LINKS", ["SIS -> MCC trip relays (XY), F&G -> SIS", "fire confirm (BY), ESD PBs"],
        col=SIS_RED, ts=2.5, ls=2.0)
    # marshalling
    p.line([(40, 352), (632, 352)], w=0.3, color=GREY)
    io_txt = ""
    if io:
        g = io["totals"]["grand"]
        io_txt = f" - UNIT TOTAL {g['used']} I/O USED / {g['installed']} INSTALLED"
    p.text("SYSTEM CABINETS + MARSHALLING CABINETS (FAR-100): DCS MC-*, SIS SMC-*, F&G FMC-*; IS barriers / isolators"
           + io_txt, 42, 358, 2.1, bold=True)
    sysz = io["totals"]["by_system"] if io else {}
    for i, (s, d) in enumerate(sysz.items()):
        p.text(f"{s}: AI {d['AI']}  AO {d['AO']}  DI {d['DI']}  DO {d['DO']}  -> {d['used']} used / {d['installed']}"
               f" installed", 42 + 150 * (i % 4), 364 + 5 * (i // 4), 2.0)
    p.text("Spare: >= 20 % installed spare per card type (cards filled to <= 80 %) + 10 % space for future cards.",
           42, 382, 2.0, color=GREY)
    # L0 field
    for i, (t, ls, c) in enumerate([
        ("FIELD JBs (ZONED)", ["JB-D*/S*/B*/F* per 40 x 30 m zone", "segregated per system (IEC 61511)"], BLUE),
        ("MULTICORE CABLES", ["armoured, IS blue sheath (AI/AO)", "tray on rack EL 109.75 (south side)"], BLUE),
        ("TRANSMITTERS / VALVES", ["4-20 mA HART, Ex ia / Ex d", "smart positioners, SOVs (SIS)"], BLUE),
        ("SIS SENSORS / SSOVs", ["dedicated taps, 2oo3 voting", "partial-stroke testing on SSOVs"], SIS_RED),
        ("F&G DEVICES", ["IR gas, IR3 flame, H2S, MCPs,", "beacons / sounders (mapping study)"], FG_COL)]):
        blk(40 + 120 * i, 412, 110, 24, t, ls, col=c, ts=2.5, ls=2.0)
        p.line([(95 + 120 * i, 390), (95 + 120 * i, 412)], w=0.35, color=c, start_arrow=True, arrow=True)
    p.text("SS-100 SUBSTATION: MCC-101A/B, desalter transformer feeders (XY-1007/1008), UPS-101A/B, battery room",
           42, 448, 2.1, bold=True)
    # UPS feeds
    ups = E.get("ups", {})
    ul = E.get("ups_loads", [])
    p.text(f"UPS: {ups.get('config', '')}", 42, 455, 1.9)
    p.text(f"{ups.get('rating_kVA', '')} kVA each, {ups.get('autonomy_min', '')} min autonomy, output "
           f"{ups.get('output', '')}", 42, 459.5, 1.9)
    yy = 466
    for k, u in enumerate([x for x in ul if x["tag"].endswith("-A")]):
        b = next((x for x in ul if x["tag"] == u["tag"][:-2] + "-B"), None)
        p.text(f"{u['tag'][:-2]}: {u['kVA_total']:.0f} kVA (A {u['bus']} {u['kVA_feed']:.0f} kVA + B "
               f"{b['bus'] if b else '-'} {b['kVA_feed'] if b else 0:.0f} kVA) - {u['description'].split(' - ')[0][:58]}",
               42 + 300 * (k % 2), yy + 5 * (k // 2), 1.9)
    p.text("Each system cabinet / console has dual PSUs fed from UDB-101A and UDB-101B (no single point of failure).",
           42, 500, 2.0, color=GREY)
    # ---------------------------------------------------------------- zones (dashed outlines)
    zbox = {"Z1": (37, 21, 604, 22), "Z2": (37, 53, 604, 24), "Z3": (37, 90, 604, 38), "Z4": (36, 164, 236, 50),
            "Z5": (266, 164, 118, 3), "Z7": (37, 315, 166, 28)}
    for zid, (x, y, w, h) in zbox.items():
        z = next(z for z in ZONES if z[0] == zid)
        if h < 5:
            continue
        p.gs.add(p.d.rect((x, y), (w, h), fill="none", stroke=z[3], stroke_width=0.5, stroke_dasharray="3,1.5"))
        p.text(f"{zid} {z[2]}", x + w - 1, y + h - 1, 2.0, "end", bold=True, color=z[3])
    for zid, xs_, c in (("Z4", (36, 293), BLUE), ("Z5", (296, 553), SIS_RED), ("Z6", (551, 638), FG_COL)):
        p.gs.add(p.d.rect((xs_[0], 266), (xs_[1] - xs_[0], 48), fill="none", stroke=c, stroke_width=0.6,
                          stroke_dasharray="3,1.5"))
        z = next(z for z in ZONES if z[0] == zid)
        p.text(f"{zid} {z[2]}", xs_[1] - 2, 313, 2.0, "end", bold=True, color=c)
    # ---------------------------------------------------------------- right column: zone / conduit tables
    x0 = 652
    p.text("IEC 62443 ZONES", x0, 22, 2.8, bold=True)
    for i, (zid, nm, sl, c) in enumerate(ZONES):
        p.gs.add(p.d.rect((x0, 25 + 6 * i), (4, 4), fill="none", stroke=c, stroke_width=0.6, stroke_dasharray="1,0.6"))
        p.text(f"{zid}  {nm}  -  SL-T {sl[3:]}", x0 + 6, 28.6 + 6 * i, 2.2, color=c)
    y = 25 + 6 * len(ZONES) + 6
    p.text("CONDUITS", x0, y, 2.8, bold=True)
    y += 4
    for cid, zz, dev, desc in CONDUITS:
        p.text(f"{cid} {zz}: {dev}", x0, y + 1, 2.1, bold=True)
        for ln in p.wrap(desc, 170, 1.9):
            y += 3.0
            p.text(ln, x0 + 3, y + 1, 1.9)
        y += 5
    y += 2
    p.narrative(x0, y, 174, "ARCHITECTURE NOTES", [
        "DCS: 3 redundant controller pairs (CDU-1, CDU-2, VDU) with redundant I/O comms and power; "
        "controller load <= 60 % CPU at FEED.",
        "SIS: one SIL 3-capable logic solver (TMR or 2oo4D), physically and logically separate from the DCS "
        "(IEC 61511 cl. 11.2); BMS H-101/H-201 configured as separate applications on SIS hardware.",
        "F&G: dedicated SIL 2 system; confirmed fire / gas executive actions per C&E CFU-000-IC-CE-001.",
        "Time synchronisation: GPS master clock (L3) - NTP / PTP to servers, controllers, SIS SOE (1 ms).",
        "Cyber: IEC 62443-3-2 risk assessment at detailed design; zones / conduits as shown; no direct L4 "
        "to L2 traffic; USB lock-down; whitelisting on EWS.",
        "I/O counts from data/io_list.json (CFU-000-IC-IOL-001).",
    ], size=2.0)
    sh.save(OUT / "CFU-000-IC-BLK-001_ICS-Architecture")
    return sh.dwg_no
