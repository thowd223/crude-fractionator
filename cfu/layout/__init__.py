"""Plant layout discipline: plot plan, sections/elevations, 3D model (CFU-000-PL-*).

build() writes data/layout.json and deliverables/03-layout-piping/{layout,3d}/.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "deliverables" / "03-layout-piping"


def build():
    from . import elevations, model, model3d, plotplan
    L = model.build_layout()
    (ROOT / "data" / "layout.json").write_text(json.dumps(L.to_json(), indent=1))
    plotplan.build(L, OUT / "layout")
    elevations.build(L, OUT / "layout")
    model3d.build(L, OUT / "3d")
    fails = [c for c in L.checks if c["status"] != "OK"]
    for c in fails:
        print("  SPACING FAIL:", c["rule"], c["item_a"], c["item_b"], c["actual_m"])
    return L
