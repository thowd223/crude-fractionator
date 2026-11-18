"""Generate the simulator's data bundles from the project master data.

    python simulator/build_assets.py

Writes simulator/data/plant-data.js (design point + layout) and simulator/data/plant-model.js (3D model as
base64), so the simulator page works from file:// and as a hosted page without fetch().
"""
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "simulator" / "data"
GLB = ROOT / "deliverables" / "03-layout-piping" / "3d" / "CFU-000-PL-3DM-001.glb"


def load(name):
    return json.loads((ROOT / "data" / name).read_text())


def main():
    from cfu import basis

    pr = load("process_results.json")
    streams = {s["no"]: s for s in load("streams.json")}
    layout = load("layout.json")
    loops = load("control_loops.json")
    equipment = {e["tag"]: e for e in load("equipment.json")}

    def st(no, *keys):
        s = streams[str(no)]
        return {k: s.get(k) for k in keys}

    keep = ("no", "name", "frm", "to", "T_C", "P_barg", "hc_kg_h", "bpsd", "api", "tbp5", "tbp95", "sulfur_wt")
    design = dict(
        crude=dict(basis.CRUDE, tbp=[list(p) for p in basis.CRUDE["tbp"]], **pr["crude"]),
        cuts_atm=basis.CUTS_ATM, cuts_vac=basis.CUTS_VAC,
        atm={k: pr["atm"][k] for k in ("T_fz", "cot", "P_fz_barg", "T_top", "T_bot", "P_top_barg", "drum_P_barg",
                                       "T_draw", "reflux_kg_h", "Q_cond_kw", "T_water_dew", "steam", "pa", "sections")},
        vac={k: pr["vac"][k] for k in ("T_fz", "cot", "P_fz_mbar", "P_top_mbar", "T_top", "T_bot", "T_lvgo",
                                       "T_hvgo", "T_slop", "steam", "pa", "sections")},
        ejector=pr["ejector"], heaters=pr["heaters"],
        preheat=dict(CIT=pr["preheat"]["CIT"], T_desalter=pr["preheat"]["T_desalter"],
                     wash_water=pr["preheat"]["wash_water"]),
        streams=[{k: streams[n].get(k) for k in keep} for n in sorted(streams, key=int)],
    )
    eq = {}
    for e in layout["equipment"]:
        eq[e["tag"]] = dict(x=e["x"], y=e["y"], z=e["z_base"], top=e.get("top_el", e["z_base"] + e["height"]),
                            L=e["L"], W=e["W"], shape=e["shape"], service=e.get("service", ""),
                            type=e.get("type", ""))
    fields = ("size", "op_T", "op_P", "des_T", "des_P", "moc", "duty_kw", "motor_kw", "flow_m3h", "head_m")
    for tag in eq:
        e = equipment.get(tag)
        if e is None:  # spares and bays share one datasheet: P-101A -> P-101A/B, A-101-B1 -> A-101
            base = re.sub(r"(-B\d|[A-D])$", "", tag)
            e = next((v for k, v in equipment.items() if k == base or k.startswith(base + "A") or k.startswith(base + "/")
                      or k.split("/")[0] == base), None)
        if e:
            eq[tag]["datasheet"] = {k: e[k] for k in fields if k in e}
    bundle = dict(design=design, layout=eq, loops=loops["loops"], sifs=loops["sifs"],
                  source="Generated from data/*.json by simulator/build_assets.py")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "plant-data.js").write_text("window.PLANT=" + json.dumps(bundle, separators=(",", ":")) + ";\n")
    (OUT / "plant-model.js").write_text(
        "window.PLANT_GLB_B64=\"" + base64.b64encode(GLB.read_bytes()).decode() + "\";\n")
    print("wrote", OUT / "plant-data.js", "and", OUT / "plant-model.js")


if __name__ == "__main__":
    main()
