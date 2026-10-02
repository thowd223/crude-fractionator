"""Piping discipline: 3D routing model, isometrics, routing/stress study, MTO (CFU-xxx-PI-*).

build() reads data/lines.json + data/layout.json (+ instruments/psv/mech) at build time and writes
data/routing.json and deliverables/03-layout-piping/{piping,3d}/.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "deliverables" / "03-layout-piping" / "piping"
OUT3D = ROOT / "deliverables" / "03-layout-piping" / "3d"


def run_model():
    from . import stress
    from .router import Router
    R = Router()
    R.run()
    R.P.assumed = list(dict.fromkeys(R.P.assumed))
    R.P.issues = list(dict.fromkeys(R.P.issues))
    mech = stress.mech_items()
    props = {r.line_no: stress.line_props(r.line) for r in R.routes}
    for r in R.routes:
        r.flex = stress.flex_check(r, R.P, mech)
        r.cat = stress.stress_category(r.line, flex=r.flex)
    R.props = props
    R.mech = mech
    R.clash_eq, R.clash_pp = stress.clash_check(R.routes, R.P)
    R.rack_load = stress.rack_loads(R.routes, R.P, props)
    return R


def build():
    import cairosvg  # noqa: F401  (Sheet.save uses it)
    from . import critical, export, glb, iso, mto, report
    from ..drawing.sheet import merge_pdfs
    OUT.mkdir(parents=True, exist_ok=True)
    R = run_model()
    # isometrics
    iso_files = []
    reg = []
    titles = {n: t for n, _, t in critical.ISO_SET}
    for r in R.routes:
        if r.level != "critical":
            continue
        views = iso.split_views(r)
        for k, (v, marks) in enumerate(views):
            sh = iso.IsoSheet(r, R.props[r.line_no], r.flex, r.iso, titles[r.iso], k + 1, len(views), v, marks, r.cat)
            short = titles[r.iso].title().replace(" ", "-").replace("/", "-").replace("(", "").replace(")", "")[:48]
            stem = OUT / "iso" / (f"{r.iso}_{short}" + (f"_SH{k + 1}" if len(views) > 1 else ""))
            sh.render(stem)
            iso_files.append(stem.with_suffix(".pdf"))
        reg.append(dict(iso=r.iso, line=r.line_no, title=titles[r.iso], sheets=len(views)))
    merge_pdfs(iso_files, OUT / "CFU-000-PI-ISO-000_Isometric-Set.pdf")
    R.iso_register = reg
    # routing json + 3D
    export.write_routing_json(R)
    pipe_glb = glb.export_glb(R.routes, OUT3D / "CFU-000-PI-3DM-002_Piping.glb")
    eq_glb = (OUT3D / "CFU-000-PL-3DM-001.glb").read_bytes()
    glb.viewer(eq_glb, pipe_glb, export.viewer_meta(R), OUT3D / "viewer-piping.html")
    # MTO + report
    mto.write(R, OUT / "CFU-000-PI-MTO-001_Piping-MTO.xlsx")
    report.write(R, OUT / "CFU-000-PI-RPT-001_Piping-Routing-Stress-Study")
    for i in R.P.issues:
        print("  PIPING ISSUE:", i)
    return R
