"""CFU-100-ME-3DM-001: interactive 3D model of C-101 (anatomy, exploded view, process animation,
assembly sequence, tray close-up).

One self-contained HTML page. All dimensions, nozzles, tray elevations and process numbers are injected
from the same data the GA drawing and datasheets use (geometry.c101(), data/*.json); the page template
(explorer_page.html) holds no process numbers of its own.

    python -m cfu.mech.explorer [--fragment out.html]   # --fragment also writes the body-only page
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from . import geometry

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "deliverables" / "02-equipment" / "3d"
DOCNO = "CFU-100-ME-3DM-001"
NAME = f"{DOCNO}_C-101-Interactive-Model.html"
STREAMS = {"7": "feed", "8": "ovhd", "10": "reflux", "13": "TPA", "14": "MPA", "15": "BPA", "16": "KERO",
           "17": "DIESEL", "18": "AGO", "19": "AR"}


def _load(name):
    return json.loads((DATA / name).read_text())


def _r(o, n=3):
    """Round every float in a nested structure (keeps the page small and diff-stable)."""
    if isinstance(o, float):
        return round(o, n)
    if isinstance(o, dict):
        return {k: _r(v, n) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_r(v, n) for v in o]
    return o


def payload(g=None):
    g = g or geometry.c101()
    pr = _load("process_results.json")
    atm = pr["atm"]
    mech = _load("mech.json")["items"]["C-101"]
    eq = {e["tag"]: e for e in _load("equipment.json")}
    streams = {STREAMS[s["no"]]: dict(no=s["no"], name=s["name"], kg_h=s["total_kg_h"], bpsd=s.get("bpsd"),
                                      frm=s["frm"], to=s["to"])
               for s in _load("streams.json") if s["no"] in STREAMS}

    # tray temperature profile: same breakpoints the heat & material balance uses for pumparound draws
    tn = atm["tray"]
    prof_n = [tn["top"], tn["KERO"], tn["DIESEL"], tn["AGO"], tn["wash_bot"], tn["bottom"]]
    prof_T = [atm["T_top"], atm["T_draw"]["KERO"], atm["T_draw"]["DIESEL"], atm["T_draw"]["AGO"],
              atm["T_fz"] - 3, atm["T_bot"]]
    sec_of = {}
    for i, s in enumerate(g["sections"]):
        a, b = (int(x) for x in s["trays"].split("-"))
        for n in range(a, b + 1):
            sec_of[n] = i
    trays = [dict(no=t["no"], z=t["z"], D=t["D"], passes=t["passes"], TS=t["TS"],
                  T=float(np.interp(t["no"], prof_n, prof_T)), sec=sec_of.get(t["no"])) for t in g["trays"]]
    nozzles = [dict(mark=n["mark"], service=n["service"], nps=n["nps"], z=n["z"], side=n["side"], angle=n["angle"],
                    kind=n["kind"], qty=n["qty"], v=n.get("v") or 0, crit=n.get("crit") or "", rating=n.get("rating"))
               for n in g["nozzles"]]
    keep = ("material design_P_barg design_T_C CA_mm shell_courses head_top_t_mm head_bottom_t_mm skirt_height_m "
            "skirt_t_mm skirt_OD_mm BTL_elevation_m insulation_mm weight_fabricated_t weight_empty_t "
            "weight_operating_t weight_hydrotest_t weight_breakdown_t hydrotest_P_top_barg hydrotest_P_bottom_barg "
            "wind_base_shear_kN wind_base_moment_kNm wind_basis natural_freq_Hz anchor_bolts volume_m3").split()
    strippers = [dict(tag=t, service=eq[t]["service"], D=eq[t]["D"], H=eq[t]["H"], key=k)
                 for t, k in (("C-102", "KERO"), ("C-103", "DIESEL"), ("C-104", "AGO")) if t in eq]
    c = eq["C-101"]
    return _r(dict(
        docno=DOCNO, tag="C-101", service=c["service"], D=c["D"], D2=c["D2"], H=c["H"], internals=c["internals"],
        moc=c["moc"], op_P=c["op_P"], op_T=c["op_T"],
        crude=pr["crude"], mech={k: mech[k] for k in keep if k in mech},
        segs=g["segs"], cone=g["cone"], trays=trays, sections=g["sections"], nozzles=nozzles,
        platforms=sorted(g["platforms"]), parts=g["internals"], levels=g["levels"], clad=g["clad"],
        atm={k: atm[k] for k in ("T_fz", "cot", "T_top", "T_bot", "P_fz_barg", "P_top_barg", "T_draw", "T_strip_out",
                                 "reflux_kg_h", "Q_cond_kw", "steam", "tray", "pa")},
        vf_feed=pr["heaters"]["H-101"]["vf_out"], streams=streams, strippers=strippers))


def render(g=None):
    """Body-only page (the form the template is written in)."""
    tpl = Path(__file__).with_name("explorer_page.html").read_text()
    data = json.dumps(payload(g), separators=(",", ":")).replace("</", "<\\/")
    assert "/*__DATA__*/null" in tpl
    return tpl.replace("/*__DATA__*/null", data)


def build(c=None, fragment=None):
    body = render(c["geoms"]["C-101"] if c else None)
    OUT.mkdir(parents=True, exist_ok=True)
    page = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            "<style>html,body{margin:0}[hidden]{display:none!important}</style></head><body>\n"
            + body + "\n</body></html>\n")
    (OUT / NAME).write_text(page)
    if fragment:
        Path(fragment).write_text(body)
    return [OUT / NAME]


if __name__ == "__main__":
    frag = sys.argv[sys.argv.index("--fragment") + 1] if "--fragment" in sys.argv else None
    for p in build(fragment=frag):
        print(p.relative_to(ROOT))
