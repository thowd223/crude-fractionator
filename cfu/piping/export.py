"""data/routing.json + viewer metadata."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from . import specs

ROOT = Path(__file__).resolve().parents[2]


def _f(v):
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (float, np.floating)) and not np.isfinite(v):
        return None
    if isinstance(v, (np.floating,)):
        return round(float(v), 3)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, np.ndarray):
        return [round(float(x), 3) for x in v.tolist()]
    if isinstance(v, float):
        return round(v, 3)
    if isinstance(v, dict):
        return {k: _f(x) for k, x in v.items() if k not in ("item",)}
    if isinstance(v, (list, tuple)):
        return [_f(x) for x in v]
    return v


def route_dict(R, r):
    pr = R.props[r.line_no]
    lens = r.pipe_length_by_nps()
    return dict(
        line_no=r.line_no, level=r.level, iso=getattr(r, "iso", None), cls=r.cls, nps=r.nps,
        service=r.line["service"], frm=r.line["from"], to=r.line["to"],
        sch=pr["sch"], wall_mm=pr["t_mm"], test_P_barg=pr["PT"], insul_mm=pr["insul_mm"],
        branches=[dict(id=b.id, nps=b.nps, parent=b.parent, line_ref=getattr(b, "line_ref", None),
                       start={k: v for k, v in b.start.items()}, end={k: v for k, v in b.end.items()},
                       points=[[round(float(c), 3) for c in p] for p in b.pts], length_m=round(b.length, 3))
                  for b in r.branches],
        fittings=r.fittings,
        supports=r.supports,
        welds=dict(shop=sum(1 for w in r.welds if w["type"] == "S"), field=sum(1 for w in r.welds if w["type"] == "F"),
                   inch_dia=round(r.weld_inch_dia(), 1), list=r.welds if r.level == "critical" else []),
        spools=r.spools,
        cut_lengths=r.pieces if r.level == "critical" else [],
        lengths=dict(total_m=round(r.total_length(), 2), pipe_by_nps={str(k): round(v, 2) for k, v in lens.items()}),
        rack_runs=r.rack_runs, loops=[{k: v for k, v in lp.items()} for lp in r.loops],
        slope=r.slope, notes=r.notes, flex=r.flex, stress_cat=r.cat[0], stress_reasons=r.cat[1],
        fit_conflicts=r.conflicts, study_valves=getattr(r, "study_valves", []),
    )


def write_routing_json(R):
    out = dict(
        doc="CFU-000-PI-RPT-001 (routing model)", rev="A", generated_by="cfu/piping",
        units="m, plant grid (x east, y north, z = EL; grade EL 100.000)",
        sources=["data/lines.json", "data/layout.json", "data/instruments.json", "data/psv.json", "data/mech.json"],
        rack=dict(tiers=R.P.tiers, y=[R.P.ry0, R.P.ry1], bents=R.P.bents,
                  occupancy={str(t): [dict(x0=o[0], x1=o[1], y=o[2], half_width=o[3], line=o[4]) for o in occ]
                             for t, occ in R.rack.occ.items()}),
        iso_register=getattr(R, "iso_register", []),
        routes=[route_dict(R, r) for r in R.routes],
        unrouted=[dict(line_no=a, reason=b) for a, b in R.unrouted],
        clashes=dict(equipment=[dict(line=a, level=b, equipment=c) for a, b, c in R.clash_eq],
                     pipe_pipe=[dict(a=a, b=b, level=c) for a, b, c in R.clash_pp]),
        rack_load_kN={str(t): {str(b): v for b, v in d.items()} for t, d in R.rack_load.items()},
        issues=R.P.issues, assumptions=R.P.assumed,
    )
    (ROOT / "data" / "routing.json").write_text(json.dumps(_f(out), indent=1))


def viewer_meta(R):
    meta = {}
    for r in R.routes:
        pr = R.props[r.line_no]
        allp = np.array([p for b in r.branches for p in b.pts])
        c = (allp.min(0) + allp.max(0)) / 2
        span = float(np.max(allp.max(0) - allp.min(0)))
        k = specs.cls(r.cls)
        meta[r.line_no] = dict(service=r.line["service"], **{"from": r.line["from"]}, to=r.line["to"], cls=r.cls,
                               rating=k["rating"], mat=specs.MAT_NAME[k["mat"]], sch=pr["sch"],
                               P=r.line["design_P_barg"], T=r.line["design_T_C"], PT=pr["PT"],
                               length=round(r.total_length(), 1), level=r.level, supports=len(r.supports),
                               iso=getattr(r, "iso", None), stress=f"Cat {r.cat[0]}",
                               c=[round(float(x), 2) for x in c], span=round(span, 1))
    return meta
