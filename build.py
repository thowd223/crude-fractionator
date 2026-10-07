"""Regenerate the complete deliverable set:  python build.py [stage ...]

Stages run in order; each stage reads data written by the previous ones.
"""
from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def stage_process():
    from cfu import control_loops, export, hmb, sizing
    m = hmb.run()
    sz = sizing.build(m)
    export.export_all(m, sz)
    export.write_json("control_loops.json", dict(loops=control_loops.as_dicts(), sifs=control_loops.sif_dicts()))
    for w in m.warn:
        print("  WARNING:", w)


# (stage name, callable or "module:function"); modules missing in a partial checkout are skipped
STAGES = [
    ("process", stage_process),
    ("reports", "cfu.reports:build"),
    ("bfd", "cfu.drawing.bfd:build"),
    ("pfd", "cfu.pid.pfd:build"),
    ("layout", "cfu.layout:build"),     # before pid: P&IDs read F&G locations from data/layout.json
    ("pid", "cfu.pid.pid:build"),
    ("mech", "cfu.mech:build"),
    ("piping", "cfu.piping:build"),
    ("elec", "cfu.elec:build"),
    ("ic", "cfu.ic:build"),
    ("wrapup", "cfu.wrapup:build"),
]


def main(argv):
    want = set(argv[1:])
    for name, fn in STAGES:
        if want and name not in want:
            continue
        t = time.time()
        if isinstance(fn, str):
            mod, func = fn.split(":")
            try:
                fn = getattr(importlib.import_module(mod), func)
            except ModuleNotFoundError as e:
                if e.name and (e.name == mod or mod.startswith(e.name)):
                    print(f"[skip] {name}: {mod} not present")
                    continue
                raise
        print(f"[run ] {name}")
        fn()
        print(f"[done] {name} ({time.time() - t:.1f} s)")


if __name__ == "__main__":
    main(sys.argv)
