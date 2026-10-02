"""Electrical load list: every consumer, duty, voltage level, bus assignment and maximum demand."""
from __future__ import annotations

import json
import math

from .common import (DATA, DIV, KV_MV, MV_MOTOR_KW, V_LV, VFD_EFF, VFD_PF, motor_eff_pf)

# buses
B13 = ("SWG-101A", "SWG-101B")
B4 = ("SWG-102A", "SWG-102B")
BLV = ("MCC-101A", "MCC-101B")
BUPS = ("UDB-101A", "UDB-101B")

VFD_TAGS = {"A-101", "K-102A/B"}       # A-101 fans (overhead condenser temperature control), H-101 ID fan


def _row(tag, desc, eq, *, rated_kw, absorbed_kw=None, duty="C", kind="motor", eff=None, pf=None, starter="DOL",
         vfd=False, kva_rated=None, lf=None, volt=None, group="", note="", pair=None):
    mv = kind == "motor" and rated_kw >= MV_MOTOR_KW
    if kind == "motor":
        e, p = motor_eff_pf(rated_kw, mv)
        eff, pf = eff or e, pf or p
        if absorbed_kw is None:
            absorbed_kw = rated_kw * (lf or 0.8)
        lf = min(absorbed_kw / rated_kw, 1.0)
        kw_in = absorbed_kw / eff
        if vfd:
            kw_in /= VFD_EFF
            pf = VFD_PF
            starter = "VFD"
        elif mv:
            starter = "VCB-DOL"
        volt = volt or (KV_MV * 1000 if mv else V_LV)
    else:
        eff = eff or 1.0
        pf = pf or 0.9
        if absorbed_kw is None:
            absorbed_kw = rated_kw * (lf if lf is not None else 1.0)
        lf = (absorbed_kw / rated_kw) if rated_kw else 0.0
        kw_in = absorbed_kw / eff
        volt = volt or V_LV
    kva = kw_in / pf if pf else 0.0
    kvar = math.sqrt(max(kva ** 2 - kw_in ** 2, 0.0))
    return dict(tag=tag, desc=desc, eq=eq, kind=kind, rated_kw=rated_kw, kva_rated=kva_rated,
                absorbed_kw=absorbed_kw, lf=lf, eff=eff, pf=pf, kw=kw_in, kvar=kvar, kva=kva, duty=duty,
                volt=volt, level="MV" if volt and volt > 1000 else ("UPS" if volt in (120, 208) and kind == "ups"
                                                                     else "LV"),
                starter=starter, vfd=vfd, bus=None, group=group, note=note, pair=pair)


def build_loads():
    eq = json.loads((DATA / "equipment.json").read_text())
    rows: list[dict] = []
    pairs: list[tuple[dict, dict]] = []     # (A unit, B unit): A on bus A, B on bus B, running chosen by balance
    singles: list[dict] = []
    fixed: list[tuple[dict, int]] = []
    issues: list[str] = []

    for e in eq:
        tag, typ = e["tag"], e["type"]
        mk = e.get("motor_kw")
        if typ in ("Pump", "Fan") and mk:
            absd = e.get("absorbed_kw")
            if absd is None:
                issues.append(f"{tag}: no absorbed_kw - 80 % load factor assumed")
            grp = "Pumps" if typ == "Pump" else "Fired-heater fans"
            if tag.endswith("A/B"):
                b = tag[:-3]
                vfd = tag in VFD_TAGS
                ra = _row(b + "A", f"{e['service']} pump A" if typ == "Pump" else f"{e['service']} A", tag,
                          rated_kw=mk, absorbed_kw=absd, vfd=vfd, group=grp)
                rb = _row(b + "B", ra["desc"][:-1] + "B", tag, rated_kw=mk, absorbed_kw=absd, vfd=vfd, group=grp)
                ra["pair"], rb["pair"] = rb["tag"], ra["tag"]
                pairs.append((ra, rb))
                rows += [ra, rb]
            else:
                r = _row(tag, e["service"] + (" (single, intermittent)" if tag == "P-118" else ""), tag,
                         rated_kw=mk, absorbed_kw=absd, duty="I" if tag == "P-118" else "C", group=grp)
                singles.append(r)
                rows.append(r)
            if absd and mk and absd > mk:
                issues.append(f"{tag}: absorbed {absd:.1f} kW exceeds motor rating {mk} kW")
        elif typ == "Air cooler" and mk:
            n = int(e.get("fans") or 0)
            fan_abs = e.get("fan_kw")
            vfd = tag in VFD_TAGS
            for i in range(1, n + 1):
                r = _row(f"{tag}-M{i}", f"{e['service']} - fan motor {i}/{n}" + (" (VFD)" if vfd else ""), tag,
                         rated_kw=mk, absorbed_kw=fan_abs, vfd=vfd, group="Air-cooler fans")
                fixed.append((r, (i - 1) % 2))
                rows.append(r)
            if fan_abs and fan_abs > mk:
                issues.append(f"{tag}: fan absorbed {fan_abs:.1f} kW exceeds motor {mk} kW")
        elif typ == "Package" and mk:
            ra = _row(f"{tag}-PA", f"{e['service']} - metering pump A", tag, rated_kw=mk,
                      absorbed_kw=0.6 * mk, group="Chemical packages", note="2 x 100 % pumps per package")
            rb = _row(f"{tag}-PB", f"{e['service']} - metering pump B", tag, rated_kw=mk,
                      absorbed_kw=0.6 * mk, group="Chemical packages")
            ra["pair"], rb["pair"] = rb["tag"], ra["tag"]
            pairs.append((ra, rb))
            rows += [ra, rb]
        elif typ == "Desalter":
            for i in (1, 2):
                r = _row(f"DT-{tag[2:]}{i}", f"{tag} {e['service'].split(',')[-1].strip()} - HV transformer {i}/2"
                         " (150 kVA, 480 V / 13-23 kV)", tag, rated_kw=150 * 0.85, kind="static", lf=0.35, pf=0.85,
                         kva_rated=150, group="Desalter transformers",
                         note="Load factor 0.35 typical for electrostatic grids (vendor to confirm)")
                fixed.append((r, i - 1))
                rows.append(r)
        elif typ == "Fired heater" and e["tag"] == "H-101":
            r = _row("SB-101", "H-101 convection sootblowers (8 x 0.75 kW, electric retract)", "H-101",
                     rated_kw=6.0, absorbed_kw=6.0, duty="I", kind="static", pf=0.8, group="Miscellaneous")
            singles.append(r)
            rows.append(r)

    # ---------------------------------------------------------------- non-process allowances
    def add(r, side):
        rows.append(r)
        fixed.append((r, side))

    def static(tag, desc, kw, duty="C", pf=0.9, lf=1.0, side=0, group="", volt=V_LV, note="", eff=1.0):
        r = _row(tag, desc, "", rated_kw=kw, duty=duty, kind="static", pf=pf, lf=lf, volt=volt, group=group,
                 note=note, eff=eff)
        add(r, side)
        return r

    for s, ab in ((0, "A"), (1, "B")):
        static(f"MOV-{ab}", f"MOV / electric valve actuators - allowance (18 x 1.5 kW), bus {ab}", 27.0, "I", 0.75,
               group="Valve actuators", side=s, note="ROSOVs on hot/LPG pump suctions, BL & heater isolation")
        static(f"HVAC-101{ab}", f"SS-100 HVAC package {ab} (2 x 100 %)", 60.0, "C" if ab == "A" else "S", 0.85,
               0.8, side=s, group="HVAC")
        static(f"HVAC-102{ab}", f"FAR-100 HVAC package {ab} (2 x 100 %)", 25.0, "C" if ab == "A" else "S", 0.85,
               0.8, side=s, group="HVAC")
        static(f"BEF-101{ab}", f"SS-100 battery-room exhaust fan {ab}", 1.1, "C" if ab == "A" else "S", 0.8,
               side=s, group="HVAC")
        static(f"LTG-{ab}", f"Area & structure lighting (LED), via LTR-101{ab} 480-208Y/120 V", 24.0, "C", 0.95,
               side=s, group="Lighting & small power", volt=208)
        static(f"LTG-B{ab}", f"Building lighting SS-100 / FAR-100, via LTR-101{ab}", 5.0, "C", 0.95, side=s,
               group="Lighting & small power", volt=208)
        static(f"SP-{ab}", f"Building small power & receptacles, via LTR-101{ab}", 10.0, "C", 0.9, 0.6, side=s,
               group="Lighting & small power", volt=208)
        static(f"CR-{ab}", f"Field convenience receptacles (120 V), via LTR-101{ab}", 10.0, "I", 0.9, side=s,
               group="Lighting & small power", volt=208)
        static(f"WR-{ab}", f"Welding receptacles 3 x 63 A, 480 V, bus {ab}", 75.0, "I", 0.7, side=s,
               group="Welding outlets")
        static(f"BC-101{ab}", f"125 V DC battery charger {ab} (switchgear control), 2 x 100 %", 6.0, "C", 0.85,
               0.5, side=s, group="UPS / DC", eff=0.9)
    static("HTP-101", "Electric heat tracing panel - CDU slop & HN lines (allowance)", 30.0, "C", 1.0, 0.7, 0,
           group="Heat tracing", note="Self-regulating; winter design -5 C; steam tracing elsewhere")
    static("HTP-102", "Electric heat tracing panel - VDU slop wax / slop oil lines (allowance)", 40.0, "C", 1.0,
           0.7, 1, group="Heat tracing")
    static("CP-101", "Cathodic protection transformer-rectifier (buried piping / tank bottoms in plot)", 8.0, "C",
           0.8, 0.8, 0, group="Cathodic protection")
    static("AH-101", "Analyser house AH-101 HVAC & utilities (analysers on UPS)", 15.0, "C", 0.85, 0.8, 1,
           group="HVAC")
    static("HST-101", "Monorail hoists P-101/P-102 maintenance (2 x 7.5 kW)", 15.0, "I", 0.8, side=0,
           group="Miscellaneous")

    # ---------------------------------------------------------------- UPS (rectifier input) + UPS consumers
    UPS_LOADS = [("DCS", "Distributed control system (controllers, I/O, servers, HMI in FAR)", 22.0),
                 ("SIS", "Safety instrumented system incl. H-101/H-201 BMS, ESD solenoids", 14.0),
                 ("FGS", "Fire & gas system incl. detectors/beacons", 6.0),
                 ("TEL", "Telecom: PAGA, CCTV, LAN/fibre, radio", 8.0),
                 ("ANZ", "Process analysers (AH-101)", 6.0),
                 ("MISC", "Misc. instrument panels, MCC/IED networking, metering", 4.0)]
    ups_kva = sum(k for _, _, k in UPS_LOADS)
    ups_rows = []
    for code, desc, kva in UPS_LOADS:
        for s, ab in ((0, "A"), (1, "B")):
            r = _row(f"UPS-{code}-{ab}", desc + f" - feed {ab} (dual redundant PSU, 50 % normal share)", "",
                     rated_kw=kva * 0.9 / 2, kind="ups", pf=0.9, volt=120, group="UPS consumers")
            r["kva_rated"] = kva
            r["bus"] = BUPS[s]
            ups_rows.append(r)
    for s, ab in ((0, "A"), (1, "B")):
        # each UPS shares 50 % of load in parallel-redundant operation; input = load / eff + recharge
        out_kw = ups_kva * 0.9 / 2
        r = _row(f"UPS-101{ab}", f"UPS-101{ab} rectifier input (2 x 100 % 100 kVA, 50 % share + battery recharge)",
                 "", rated_kw=out_kw / 0.93 + 5.0, kind="static", pf=0.95, group="UPS / DC")
        add(r, s)

    # ---------------------------------------------------------------- bus assignment
    run_kw = {0: 0.0, 1: 0.0}
    run_kw_mv = {0: 0.0, 1: 0.0}
    for r, s in fixed:
        lvl = r["volt"] > 1000
        r["bus"] = (B4 if lvl else BLV)[s]
        if r["duty"] == "C":
            (run_kw_mv if lvl else run_kw)[s] += r["kw"]
    for r in sorted(singles, key=lambda r: -r["kw"]):
        lvl = r["volt"] > 1000
        acc = run_kw_mv if lvl else run_kw
        s = 0 if acc[0] <= acc[1] else 1
        r["bus"] = (B4 if lvl else BLV)[s]
        acc[s] += r["kw"] if r["duty"] == "C" else 0.3 * r["kw"]
    for ra, rb in sorted(pairs, key=lambda p: -p[0]["kw"]):
        lvl = ra["volt"] > 1000
        acc = run_kw_mv if lvl else run_kw
        buses = B4 if lvl else BLV
        ra["bus"], rb["bus"] = buses[0], buses[1]
        if acc[0] <= acc[1]:
            ra["duty"], rb["duty"] = "C", "S"
            acc[0] += ra["kw"]
        else:
            ra["duty"], rb["duty"] = "S", "C"
            acc[1] += rb["kw"]

    order = {"Pumps": 0, "Fired-heater fans": 1, "Air-cooler fans": 2, "Chemical packages": 3,
             "Desalter transformers": 4, "Valve actuators": 5, "Heat tracing": 6, "HVAC": 7,
             "Lighting & small power": 8, "Welding outlets": 9, "Cathodic protection": 10, "UPS / DC": 11,
             "Miscellaneous": 12}
    rows.sort(key=lambda r: (0 if r["volt"] > 1000 else 1, order.get(r["group"], 99), r["tag"]))
    for i, r in enumerate(rows, 1):
        r["item"] = i
        r["c_kw"] = r["kw"] if r["duty"] == "C" else 0.0
        r["i_kw"] = r["kw"] if r["duty"] == "I" else 0.0
        r["s_kw"] = r["kw"] if r["duty"] == "S" else 0.0
        r["c_kvar"] = r["kvar"] if r["duty"] == "C" else 0.0
        r["i_kvar"] = r["kvar"] if r["duty"] == "I" else 0.0
        r["s_kvar"] = r["kvar"] if r["duty"] == "S" else 0.0
    return rows, ups_rows, issues


def demand(rows, bus=None):
    sel = [r for r in rows if bus is None or r["bus"] == bus]
    C = sum(r["c_kw"] for r in sel)
    I = sum(r["i_kw"] for r in sel)
    S = sum(r["s_kw"] for r in sel)
    Cq = sum(r["c_kvar"] for r in sel)
    Iq = sum(r["i_kvar"] for r in sel)
    Sq = sum(r["s_kvar"] for r in sel)
    kw = DIV["C"] * C + DIV["I"] * I + DIV["S"] * S
    kvar = DIV["C"] * Cq + DIV["I"] * Iq + DIV["S"] * Sq
    kva = math.hypot(kw, kvar)
    return dict(C_kW=C, I_kW=I, S_kW=S, C_kvar=Cq, I_kvar=Iq, S_kvar=Sq, kW=kw, kvar=kvar, kVA=kva,
                pf=kw / kva if kva else 1.0, connected_kW=C + I + S, n=len(sel))
