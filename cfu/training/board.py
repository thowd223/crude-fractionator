"""Board operator simulator: the unit running live in the browser (CFU-000-PM-TRN-002).

The page (board_page.html) holds a simplified dynamic model of the CDU/VDU. Its steady state, controller
tags, alarm and trip settings, pump duties and relief pressure are read here from data/*.json and from the
cause-and-effect generator, so the board trips where the design says it trips. The dynamics (lags, holdups,
controller tuning) are training approximations and are set in the page.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .. import basis
from ..ic import ce

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "deliverables" / "07-training"
DOCNO = "CFU-000-PM-TRN-002"
ALARM_COT = (8, 6)         # high alarm above design COT, H-101 / H-201 (ce.SETPOINT_BASIS)
ALARM_LEVEL = (25, 75)     # low / high level alarms, % of span (ce.SETPOINT_BASIS)
LOOPS = ["FIC-1001", "TIC-1020", "PIC-1021", "TIC-1030", "FIC-1031", "PIC-1032", "LIC-1033", "FIC-1034", "LIC-1082",
         "FIC-1083", "TIC-2005", "PIC-2006", "PIC-2010", "LIC-2024", "FIC-2025"]
SIFS = ["SIF-101", "SIF-102", "SIF-103", "SIF-106", "SIF-108", "SIF-201", "SIF-203", "SIF-901"]
PUMPS = ["P-101", "P-103", "P-112"]


def _load(name):
    return json.loads((DATA / name).read_text())


def _num(s):
    return float(re.search(r"-?\d+(\.\d+)?", s).group())


def scenario():
    pr = _load("process_results.json")
    st = {s["no"]: s for s in _load("streams.json")}
    t = lambda no: round(st[no]["total_kg_h"] / 1000, 1)
    cl = _load("control_loops.json")
    loops = {l["tag"]: l for l in cl["loops"]}
    sifs = {s["tag"]: s for s in cl["sifs"]}
    psv = {p["protects"]: p for p in _load("psv.json")}
    loads = {l["tag"]: l for l in _load("electrical.json")["loads"]}
    init = {r["tag"]: r for r in ce.initiators()}
    sp = ce.setpoints()
    H1, H2, atm, vac = pr["heaters"]["H-101"], pr["heaters"]["H-201"], pr["atm"], pr["vac"]
    acts = {a[0]: f"{a[1]}: {a[2]}" for a in ce.ACTIONS}
    first = {}
    for r in ce.initiators():
        first.setdefault(r["sif"], r)
    pumps = {}
    for p in PUMPS:
        a, b = loads[p + "A"], loads[p + "B"]
        pumps[p] = dict(duty="A" if a["duty"] == "C" else "B", kW=round(a["rated_kW"]), busA=a["bus"], busB=b["bus"],
                        relays=a["relays"] or "", service=a["description"].rsplit(" pump", 1)[0])
    return dict(
        doc=dict(no=DOCNO, rev=basis.PROJECT["rev"], project=basis.PROJECT["name"], stage=basis.PROJECT["stage"],
                 ce="CFU-000-IC-CE-001"),
        bpsd=basis.CAPACITY_BPSD, turndown=basis.TURNDOWN,
        F=t("1"), CIT=round(H1["T_in"], 1), COT=round(H1["T_out"], 1), passes1=H1["passes"], fired1=round(H1["Q_fired_kw"] / 1000, 1),
        AR=t("19"), Tbot=round(atm["T_bot"], 1), Ttop=round(atm["T_top"], 1), Ptop=round(atm["P_top_barg"], 2),
        Pdrum=round(atm["drum_P_barg"], 2), reflux=t("10"), naph=t("11"), kero=t("16"), diesel=t("17"), ago=t("18"),
        psv=psv["C-101"]["set_barg"], psvTag=psv["C-101"]["tag"],
        COT2=round(H2["T_out"], 1), passes2=H2["passes"], fired2=round(H2["Q_fired_kw"] / 1000, 1),
        Pvac=vac["P_top_mbar"], Pfz=vac["P_fz_mbar"], lvgo=t("23"), hvgo=t("24"), vr=t("26"), fgHdr=st["34"]["P_barg"],
        trip=dict(pass1=round(sp["pass1"][1], 1), pass2=round(sp["pass2"][1], 1), cot1=round(sp["cot1"][1], 1),
                  cot2=round(sp["cot2"][1], 1), fgLL=_num(init["PZLL-1027"]["sp"]), fgHH=_num(init["PZHH-1027"]["sp"]),
                  lvlHH=_num(init["LZHH-1082"]["sp"]), lvl2HH=_num(init["LZHH-2024"]["sp"])),
        alarm=dict(cot1=round(H1["T_out"] + ALARM_COT[0], 1), cot2=round(H2["T_out"] + ALARM_COT[1], 1),
                   lvlL=ALARM_LEVEL[0], lvlH=ALARM_LEVEL[1], fgH=_num(init["PZHH-1027"]["normal"].split("-")[1])),
        loops={k: dict(service=loops[k]["service"], final=loops[k]["final"]) for k in LOOPS},
        sifs={k: dict(fn=sifs[k]["function"], sil=sifs[k]["sil"], init=sifs[k]["initiators"], vote=first[k]["vote"],
                      acts=[acts[a] for a in first[k]["act"] if a != "A23"][:4]) for k in SIFS},
        pumps=pumps,
    )


def build():
    tpl = Path(__file__).with_name("board_page.html").read_text()
    data = json.dumps(scenario(), separators=(",", ":")).replace("</", "<\\/")
    assert "/*DATA*/null" in tpl
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{DOCNO}_Board-Operator-Simulator.html"
    out.write_text(tpl.replace("/*DATA*/null", data))
    print(f"  {out.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
