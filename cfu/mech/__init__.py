"""Mechanical / equipment discipline (deliverables/02-equipment, data/mech.json).

build() runs: ASME VIII / API 530 / ASCE 7 calculations (calc), report CFU-000-ME-CAL-001 (md + pdf),
datasheets CFU-000-ME-DS-001..007 (+ combined xlsx) and GA drawings CFU-100/200-ME-GA-001..008.
"""
from __future__ import annotations


def build():
    from . import calc, datasheets, ga_columns, ga_heaters, ga_misc, report
    c = calc.run()                       # also writes data/mech.json
    report.build(c)
    ds = datasheets.build(c)
    ga = ga_columns.build(c) + ga_heaters.build(c) + ga_misc.build(c)
    print(f"  mech: {len(ds)} datasheet files, {len(ga)} GA drawings, data/mech.json")
    return c
