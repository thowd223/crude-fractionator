"""Draw the unit plot plan (from data/layout.json) as inline SVG into the suite landing page.

    python sims/suite/plotplan.py      # rewrites the block between PLOT markers in landing.html
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANDING = Path(__file__).with_name("landing.html")

TYPE_CLASS = {"Column": "col", "Fired heater": "htr", "Heater": "htr", "Drum": "drm", "Desalter": "drm",
              "Shell & tube": "hx", "Air cooler": "ac", "Pump": "pmp"}
LONG_LEAD = {"H-101", "H-201", "C-101", "C-201"}


def cls_for(e):
    t = e.get("type", "")
    for k, v in TYPE_CLASS.items():
        if k.lower() in t.lower():
            return v
    return "oth"


def svg():
    lay = json.loads((ROOT / "data/layout.json").read_text())
    W, H = lay["frame"]["plot_x"], lay["frame"]["plot_y"]
    y = lambda v: H - v  # north up
    out = [f'<svg class="plot" viewBox="-4 -4 {W + 8} {H + 8}" role="img" '
           f'aria-label="Plot plan of the CDU/VDU unit, {W:.0f} by {H:.0f} m, drawn from the layout data">']
    out.append(f'<rect class="frame" x="0" y="0" width="{W}" height="{H}"/>')
    for gx in range(0, int(W) + 1, 10):
        out.append(f'<line class="grid" x1="{gx}" y1="0" x2="{gx}" y2="{H}"/>')
    for gy in range(0, int(H) + 1, 10):
        out.append(f'<line class="grid" x1="0" y1="{gy}" x2="{W}" y2="{gy}"/>')
    st = lay["structures"]
    for r in (st.get("roads") or []) if isinstance(st.get("roads"), list) else []:
        if all(k in r for k in ("x0", "x1", "y0", "y1")):
            out.append(f'<rect class="road" x="{r["x0"]}" y="{y(r["y1"])}" width="{r["x1"] - r["x0"]}" height="{r["y1"] - r["y0"]}"/>')
    pr = st.get("pipe_rack")
    racks = pr if isinstance(pr, list) else [pr] if pr else []
    for r in racks:
        if r.get("axis", "E-W") == "E-W":
            out.append(f'<rect class="rack" x="{r["x0"]}" y="{y(r["y1"])}" width="{r["x1"] - r["x0"]}" height="{r["y1"] - r["y0"]}"/>')
            for bx in r.get("bents_x", []):
                out.append(f'<line class="bent" x1="{bx}" y1="{y(r["y1"])}" x2="{bx}" y2="{y(r["y0"])}"/>')
    for e in lay["equipment"]:
        c = cls_for(e)
        tag = e["parent_tag"]
        extra = " ll" if tag in LONG_LEAD else ""
        lift = " lift" if tag == "C-101" else ""
        if e["shape"] == "vcyl":
            r = max(e.get("D", 1) / 2, 0.6)
            out.append(f'<circle class="eq {c}{extra}{lift}" data-tag="{tag}" cx="{e["x"]}" cy="{y(e["y"])}" r="{r}"><title>{tag} · {e["service"]}</title></circle>')
        else:
            x0, y0, x1, y1 = e["bbox"]
            out.append(f'<rect class="eq {c}{extra}" data-tag="{tag}" x="{x0}" y="{y(y1)}" width="{x1 - x0}" height="{y1 - y0}"><title>{tag} · {e["service"]}</title></rect>')
    c101 = next(e for e in lay["equipment"] if e["tag"] == "C-101")
    cx, cy = c101["x"], y(c101["y"])
    out.append(f'<g class="liftmark"><circle cx="{cx - 22}" cy="{cy - 8}" r="3"/><circle class="rad" cx="{cx - 22}" cy="{cy - 8}" r="23.4"/>'
               f'<line x1="{cx - 22}" y1="{cy - 8}" x2="{cx}" y2="{cy}"/></g>')
    out.append(f'<text class="lbl" x="{c101["x"] + 5}" y="{cy - 5}">C-101</text>')
    for tag in ("H-101", "H-201", "C-201"):
        e = next((q for q in lay["equipment"] if q["parent_tag"] == tag), None)
        if e:
            out.append(f'<text class="lbl" x="{e["x"] + 5}" y="{y(e["y"]) + 2}">{tag}</text>')
    out.append(f'<text class="north" x="{W - 6}" y="10">N ↑</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    page = LANDING.read_text()
    block = "<!--PLOT:BEGIN-->\n" + svg() + "\n<!--PLOT:END-->"
    page = re.sub(r"<!--PLOT:BEGIN-->.*?<!--PLOT:END-->", lambda m: block, page, flags=re.S)
    LANDING.write_text(page)
    print("plot plan written into", LANDING.name)
