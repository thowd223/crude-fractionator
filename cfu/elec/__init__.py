"""Electrical discipline generator (FEED): load list, SLDs, sizing calculations, cable schedule,
data/electrical.json.   Entry point: build()."""
from __future__ import annotations


def compute():
    from . import cables, common, loads, study
    rows, ups_rows, issues = loads.build_loads()
    R = study.run(rows, ups_rows)
    loc = common.Locator()
    cbl, ci = cables.build(rows, R, loc)
    R["start"] = study.motor_start_cases(rows, R)      # repeat with actual P-101 cable impedance
    ud = study.ups_dc(ups_rows)
    cab = {c["tag"]: c for c in cbl}
    return dict(rows=rows, ups_rows=ups_rows, R=R, cbl=cbl, cab=cab, ud=ud, loc=loc, issues=issues + ci)


def build():
    from . import common, reports, sld
    ctx = compute()
    out = common.OUT
    out.mkdir(parents=True, exist_ok=True)
    sld.build_all(ctx, out / "sld")
    reports.build_all(ctx, out)
    for w in ctx["issues"]:
        print("  ELEC NOTE:", w)
    return ctx
