"""Lockout / tagout training: interactive isolation of hot pump P-112A (CFU-000-PM-TRN-001).

The page (loto_page.html) is a template; every number shown in it is read here from data/*.json so the
training follows the design. The scenario is the standby atmospheric-residue pump: medium-voltage motor,
auto-start from the DCS, residue above its auto-ignition temperature and a pressurised seal barrier.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import basis

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "deliverables" / "07-training"
DOCNO = "CFU-000-PM-TRN-001"
PUMP, TWIN, PARENT = "P-112A", "P-112B", "P-112A/B"
SAFE_TOUCH_C = 60          # casing temperature below which the pump may be opened (training criterion)


def _load(name):
    return json.loads((DATA / name).read_text())


def _one(rows, **match):
    for r in rows:
        if all(r.get(k) == v for k, v in match.items()):
            return r
    raise KeyError(f"no record matching {match}")


def _line(r):
    return dict(no=r["line_no"], nps=r["size_in"], cls=r["cls"], service=r["service"], opP=round(r["op_P_barg"], 1),
                opT=round(r["op_T_C"]), desP=r["design_P_barg"], desT=round(r["design_T_C"]), pid=r["pid_sheet"])


def scenario():
    eq = _one(_load("equipment.json"), tag=PARENT)
    el = _load("electrical.json")
    load = _one(el["loads"], tag=PUMP)
    twin = _one(el["loads"], tag=TWIN)
    cable = _one(el["cables"], tag=load["cable_tag"])
    lines = _load("lines.json")
    suction = next(r for r in lines if r["to"] == PARENT)
    discharge = next(r for r in lines if r["from"] == PARENT and r["stream_no"])
    spill = next(r for r in lines if r["from"] == PARENT and "spillback" in r["service"])
    inst = _load("instruments.json")
    gauge = next(r for r in inst if r["service"] == f"{PUMP} discharge pressure")
    eiv = next(r for r in inst if r["type"].startswith("Emergency isolation valve") and r["line_no"] == ""
               and r["pid_sheet"] == suction["pid_sheet"])
    stream = _one(_load("streams.json"), no=discharge["stream_no"])
    sif = _one(_load("control_loops.json")["sifs"], tag=eiv["sif"])
    return dict(
        doc=dict(no=DOCNO, rev=basis.PROJECT["rev"], project=basis.PROJECT["name"], client=basis.PROJECT["client"],
                 stage=basis.PROJECT["stage"], pid=suction["pid_sheet"], loadlist=el["doc"]["load_list"]),
        pump=dict(tag=PUMP, twin=TWIN, service=eq["service"], api610=eq["api610"], seal=eq["seal"], moc=eq["moc"],
                  flow=round(eq["flow_m3h"]), head=round(eq["head_m"]), opT=round(eq["T"]), desT=eq["des_T"],
                  duty="standby" if load["duty"] == "S" else "duty",
                  twin_duty="standby" if twin["duty"] == "S" else "duty"),
        motor=dict(kW=round(load["rated_kW"]), V=round(load["voltage_V"]), kV=load["voltage_V"] / 1000,
                   bus=load["bus"], twin_bus=twin["bus"], starter=load["starter"], flc=load["FLC_A"],
                   relays=load["relays"], cable=cable["tag"], cable_m=round(cable["L_m"]), device=cable["device"],
                   remote=sorted(load["dcs_signals"]["DO"]), zone=load["area_class"]["zone"]),
        suction=_line(suction), discharge=_line(discharge), spill=_line(spill),
        gauge=dict(tag=gauge["tag"], range=gauge["range"], units=gauge["units"]),
        eiv=dict(tag=eiv["tag"], sif=sif["tag"], sil=sif["sil"], function=sif["function"]),
        fluid=dict(no=stream["no"], name=stream["name"], sulfur=round(stream["sulfur_wt"], 1), T=round(stream["T_C"]),
                   kgph=round(stream["total_kg_h"] / 1000), dest=stream["to"]),
        limits=dict(touch=SAFE_TOUCH_C, ambient=round(basis.SITE["amb_design_C"])),
    )


def build():
    tpl = Path(__file__).with_name("loto_page.html").read_text()
    data = json.dumps(scenario(), separators=(",", ":")).replace("</", "<\\/")
    assert "/*DATA*/null" in tpl
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{DOCNO}_Hot-Pump-Lockout.html"
    out.write_text(tpl.replace("/*DATA*/null", data))
    print(f"  {out.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
