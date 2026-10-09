"""Project portal: single self-contained HTML index of every deliverable (deliverables/06-wrapup/portal/)."""
from __future__ import annotations

import base64
import html
import io
import json
from collections import OrderedDict
from pathlib import Path

from .. import basis

ROOT = Path(__file__).resolve().parents[2]
DLV = ROOT / "deliverables"
OUT = DLV / "06-wrapup" / "portal"
GH = "https://github.com/thowd223/crude-fractionator/blob/main/"

DISC_ORDER = ["Process", "Mechanical", "Plant layout", "Piping", "Instrumentation & control", "Electrical",
              "Project management"]
DISC_NOTE = {
    "Process": "Basis of design, heat & material balance, BFD, PFDs, P&IDs, process design report, HAZOP.",
    "Mechanical": "Equipment list, datasheets, ASME VIII / API 530 calculations, general arrangement drawings.",
    "Plant layout": "Plot plan, sections, rack section, 3D model.",
    "Piping": "Line list, piping classes, routing, isometrics, stress-critical lines, MTO.",
    "Instrumentation & control": "Control philosophy and proposed control scheme, ICS architecture, C&E, SIL, I/O, loop diagrams.",
    "Electrical": "Load list, single-line diagrams, sizing calcs, cable schedule, hazardous area classification.",
    "Project management": "Cost estimate and document register.",
}
# (svg path relative to deliverables, caption) for the drawing gallery
GALLERY = [
    ("01-process/bfd/CFU-000-PR-BFD-001.svg", "Block flow diagram"),
    ("01-process/pfd/CFU-100-PR-PFD-003.svg", "PFD - C-101 atmospheric column"),
    ("01-process/pid/CFU-100-PR-PID-004.svg", "P&ID - H-101 process coils"),
    ("02-equipment/ga/CFU-100-ME-GA-001.svg", "GA - C-101 column"),
    ("03-layout-piping/layout/CFU-000-PL-PLT-001_Plot-Plan.svg", "Plot plan 1:500"),
    ("PNG:03-layout-piping/3d/CFU-000-PL-3DM-001_render-iso-SE.png", "3D model - iso SE"),
    ("ISO", "Piping isometric"),
    ("04-instrumentation/control-scheme/CFU-100-IC-CSD-001.svg", "Control scheme - H-101 combustion"),
    ("04-instrumentation/CFU-000-IC-BLK-001_ICS-Architecture.svg", "ICS architecture"),
    ("05-electrical/sld/CFU-000-EL-SLD-001.svg", "Key single-line diagram"),
    ("05-electrical/hac/CFU-000-EL-HAC-001.svg", "Hazardous area classification"),
]


def _thumb(path: Path, width=1100) -> str | None:
    from PIL import Image
    try:
        if path.suffix == ".svg":
            import cairosvg
            png = cairosvg.svg2png(url=str(path), output_width=width)
            im = Image.open(io.BytesIO(png))
        else:
            im = Image.open(path)
            im.thumbnail((width, width * 2))
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=72, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def _find(pattern: str):
    hits = sorted(DLV.glob(pattern))
    return hits[0] if hits else None


def _primary(files: list[str]) -> str:
    for ext in (".pdf", ".xlsx", ".html", ".glb", ".svg", ".md"):
        for f in files:
            if f.endswith(ext) and "-ALL" not in f:
                return f
    return files[0]


def build():
    from . import register
    rows = register()
    reg = {}
    from . import DOCNO  # noqa
    for p in sorted(DLV.rglob("*")):
        if p.is_file():
            m = DOCNO.search(p.name)
            if m:
                reg.setdefault(m.group(1), []).append(str(p.relative_to(ROOT)))
    J = lambda n: json.loads((ROOT / "data" / n).read_text()) if (ROOT / "data" / n).exists() else {}
    R, E, IO, EL = J("process_results.json"), J("equipment.json"), J("io_list.json"), J("electrical.json")
    S = {s["no"]: s for s in J("streams.json")}
    eqd = {e["tag"]: e for e in E}
    lines, inst = J("lines.json"), J("instruments.json")
    routing = J("routing.json")
    est_md = (DLV / "06-wrapup" / "CFU-000-PM-EST-001_Cost-Estimate.md")
    tic = ""
    if est_md.exists():
        for ln in est_md.read_text().splitlines():
            if ln.startswith("| Total installed cost"):
                tic = ln.split("|")[2].strip()
    unit_kw = ""
    md = EL.get("max_demand", {}).get("total_13_8kV", {})
    if isinstance(md, dict):
        unit_kw = md.get("kW") or md.get("P_kW") or ""
    grand = IO.get("totals", {}).get("grand", {})
    io_used, io_inst = grand.get("used", ""), grand.get("installed", "")
    figures = [
        ("Capacity", f"{basis.CAPACITY_BPSD:,}", "BPSD Arab Light, 33.4 API"),
        ("H-101 fired", f"{R['heaters']['H-101']['Q_fired_kw'] / 1000:.1f}", f"MW; COT {R['atm']['cot']:.0f} C, CIT {R['preheat']['CIT']:.0f} C"),
        ("C-101", f"{eqd['C-101']['D']:.1f} m", f"x {eqd['C-101']['H']:.0f} m T/T, 41 trays, FZ {R['atm']['T_fz']:.0f} C"),
        ("C-201", f"{eqd['C-201']['D']:.1f} m", f"{R['vac']['P_fz_mbar']:.0f} mbar(a) flash zone, {R['vac']['T_fz']:.0f} C"),
        ("Lines / instruments", f"{len(lines)} / {len(inst)}", "on 17 P&ID sheets"),
        ("Installed cost", f"${tic}M" if tic else "-", "ISBL, AACE Class 4, 2026 USGC"),
    ]
    if unit_kw:
        figures.insert(5, ("Max demand", f"{float(unit_kw) / 1000:.2f} MW", "at 13.8 kV, two-bus scheme"))
    if io_used:
        figures.insert(5, ("Control system I/O", f"{io_used:,}", f"used of {io_inst:,} installed (DCS, SIS, BMS, F&G)"))
    yields = [("LPG", "30"), ("Light naphtha", "32"), ("Heavy naphtha", "33"), ("Kerosene", "16"), ("Diesel", "17"),
              ("AGO", "18"), ("LVGO", "23"), ("HVGO", "24"), ("Slop wax", "25"), ("Vacuum residue", "26")]
    ymax = max(S[n]["bpsd"] for _, n in yields)

    # gallery
    gal = []
    for rel, cap in GALLERY:
        if rel == "ISO":
            p = _find("03-layout-piping/piping/**/CFU-*-PI-ISO-001*.svg") or _find("03-layout-piping/piping/**/*ISO*.svg")
        elif rel.startswith("PNG:"):
            p = DLV / rel[4:]
        else:
            p = DLV / rel
        if not p or not p.exists():
            continue
        src = _thumb(p)
        if not src:
            continue
        pdf = p.with_suffix(".pdf")
        link = GH + str((pdf if pdf.exists() else p).relative_to(ROOT))
        gal.append((src, cap, link, p.stem.split("_")[0]))

    by_disc = OrderedDict((d, []) for d in DISC_ORDER)
    for r in rows:
        by_disc.setdefault(r["disc"], []).append(r)

    esc = html.escape
    out = []
    out.append(f"""<title>CDU/VDU FEED Package</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: drawing-register page - title-block header, figure strip, drawing gallery, register by discipline */
:root {{
  --paper: #f6f7f5; --sheet: #ffffff; --ink: #1d2b36; --muted: #5b6b77; --rule: #d3dade;
  --line: #2f5d7c; --flame: #c8501e; --chip: #e8eef2;
  --f-display: "Barlow Condensed", "Arial Narrow", sans-serif;
  --f-body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #121a20; --sheet: #182229; --ink: #e3e9ed; --muted: #95a6b2; --rule: #2c3a44;
  --line: #7fb2d6; --flame: #f08a52; --chip: #22313b; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --paper: #121a20; --sheet: #182229; --ink: #e3e9ed; --muted: #95a6b2; --rule: #2c3a44;
  --line: #7fb2d6; --flame: #f08a52; --chip: #22313b; color-scheme: dark }}
* {{ box-sizing: border-box }}
body {{ background: var(--paper); color: var(--ink); font-family: var(--f-body); font-size: 15px; line-height: 1.55;
  padding-inline: 16px; padding-block: 0 48px }}
.wrap {{ max-width: 1180px; margin: 0 auto }}
a {{ color: var(--line) }}
a:focus-visible {{ outline: 2px solid var(--flame); outline-offset: 2px }}
header.tb {{ margin-top: 24px; border: 1.5px solid var(--ink); background: var(--sheet); display: grid;
  grid-template-columns: 1fr auto; }}
.tb .main {{ padding: 18px 22px; min-width: 0 }}
.tb .eyebrow {{ font-family: var(--f-mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted) }}
.tb h1 {{ font-family: var(--f-display); font-weight: 700; font-size: clamp(32px, 5vw, 52px); line-height: 1.02;
  margin: 6px 0 8px; text-wrap: balance; letter-spacing: .01em }}
.tb p {{ margin: 0; max-width: 68ch; color: var(--muted) }}
.tb .cells {{ border-left: 1.5px solid var(--ink); display: grid; grid-template-rows: repeat(4, auto); min-width: 220px }}
.tb .cell {{ padding: 8px 14px; border-bottom: 1px solid var(--rule) }}
.tb .cell:last-child {{ border-bottom: 0 }}
.tb .cell b {{ display: block; font-family: var(--f-mono); font-size: 10.5px; letter-spacing: .08em; color: var(--muted); font-weight: 500 }}
.tb .cell span {{ font-family: var(--f-display); font-size: 22px; font-weight: 600 }}
.tb .rev span {{ color: var(--flame) }}
@media (max-width: 720px) {{ header.tb {{ grid-template-columns: 1fr }} .tb .cells {{ border-left: 0; border-top: 1.5px solid var(--ink);
  grid-template-columns: 1fr 1fr; grid-template-rows: none }} }}
.figs {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; margin-top: 18px;
  border-top: 1px solid var(--rule); border-left: 1px solid var(--rule) }}
.fig {{ padding: 12px 14px; border-right: 1px solid var(--rule); border-bottom: 1px solid var(--rule); background: var(--sheet) }}
.fig b {{ font-family: var(--f-mono); font-size: 10.5px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 500 }}
.fig .v {{ font-family: var(--f-display); font-size: 30px; font-weight: 600; font-variant-numeric: tabular-nums; line-height: 1.1 }}
.fig .u {{ font-size: 12.5px; color: var(--muted) }}
h2 {{ font-family: var(--f-display); font-weight: 600; font-size: 26px; letter-spacing: .02em; margin: 40px 0 6px;
  text-transform: uppercase }}
h2 + .lede {{ margin: 0 0 16px; color: var(--muted); max-width: 70ch }}
.split {{ display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr); gap: 28px; align-items: start }}
@media (max-width: 860px) {{ .split {{ grid-template-columns: 1fr }} .figs {{ grid-template-columns: repeat(2, minmax(0, 1fr)) }} }}
.yield {{ background: var(--sheet); border: 1px solid var(--rule); padding: 14px 16px }}
.yrow {{ display: grid; grid-template-columns: 120px 1fr 92px; gap: 10px; align-items: center; font-size: 13.5px; padding: 3px 0 }}
.ybar {{ height: 10px; background: var(--chip) }}
.ybar i {{ display: block; height: 100%; background: var(--line) }}
.yrow .n {{ font-family: var(--f-mono); font-size: 12.5px; text-align: right; font-variant-numeric: tabular-nums }}
.flow {{ background: var(--sheet); border: 1px solid var(--rule); padding: 14px 16px; font-size: 14px }}
.flow ol {{ margin: 0; padding-left: 20px }}
.flow li {{ padding: 3px 0 }}
.gal {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px }}
.gal a {{ display: block; text-decoration: none; color: inherit; background: var(--sheet); border: 1px solid var(--rule) }}
.gal a:hover {{ border-color: var(--line) }}
.gal img {{ display: block; width: 100%; aspect-ratio: 1.41; object-fit: cover; object-position: top left; background: #fff;
  border-bottom: 1px solid var(--rule) }}
.gal .c {{ padding: 8px 10px; font-size: 13.5px }}
.gal .c small {{ display: block; font-family: var(--f-mono); font-size: 11px; color: var(--muted) }}
.disc {{ margin-top: 26px }}
.disc h3 {{ font-family: var(--f-display); font-size: 21px; font-weight: 600; margin: 0 }}
.disc .note {{ color: var(--muted); font-size: 13.5px; margin: 2px 0 8px }}
.tw {{ overflow-x: auto; border: 1px solid var(--rule); background: var(--sheet) }}
table {{ border-collapse: collapse; width: 100%; font-size: 13.5px; min-width: 620px }}
th, td {{ text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--rule); vertical-align: top }}
th {{ font-family: var(--f-mono); font-size: 11px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); font-weight: 500 }}
td.no {{ font-family: var(--f-mono); font-size: 12.5px; white-space: nowrap }}
.fmt {{ display: inline-block; font-family: var(--f-mono); font-size: 11px; padding: 1px 6px; margin: 0 4px 2px 0; background: var(--chip); color: var(--ink);
  text-decoration: none }}
.fmt:hover {{ background: var(--line); color: var(--sheet) }}
.cta {{ display: inline-flex; gap: 8px; align-items: center; margin-top: 12px; padding: 9px 14px; border: 1.5px solid var(--ink);
  background: var(--sheet); color: var(--ink); font-weight: 600; text-decoration: none }}
.ctas {{ display: flex; flex-wrap: wrap; gap: 10px }}
.cta:hover {{ background: var(--ink); color: var(--sheet) }}
.issues {{ background: var(--sheet); border: 1px solid var(--rule); padding: 6px 16px }}
.issues li {{ padding: 4px 0 }}
.mono {{ font-family: var(--f-mono); font-size: 13px; background: var(--chip); padding: 10px 12px; overflow-x: auto; white-space: pre }}
footer {{ margin-top: 40px; color: var(--muted); font-size: 12.5px; border-top: 1px solid var(--rule); padding-top: 12px }}
</style>
<div class="wrap">
<header class="tb">
  <div class="main">
    <div class="eyebrow">{esc(basis.PROJECT['client'])} · FEED deliverable package</div>
    <h1>100 kBPSD Crude &amp; Vacuum Distillation Unit</h1>
    <p>Concept-to-FEED engineering for an Arab Light crude unit: desalting and preheat, atmospheric fractionation with three
    pumparounds, naphtha stabilisation and splitting, wet vacuum distillation and ejectors. Every document below is generated
    from one calculation model, so the drawings, lists and reports agree with each other.</p>
    <div class="ctas"><a class="cta" href="viewer.html">Open the 3D model &rarr;</a>
    <a class="cta" href="dependencies.html">Design dependency map &rarr;</a>
    <a class="cta" href="phases.html">Phase maturity plan &rarr;</a></div>
  </div>
  <div class="cells">
    <div class="cell"><b>DOCUMENT SET</b><span>{len(rows)} documents</span></div>
    <div class="cell"><b>STAGE</b><span>FEED</span></div>
    <div class="cell rev"><b>REVISION</b><span>Rev {basis.PROJECT['rev']} · IFR</span></div>
    <div class="cell"><b>DATE</b><span>2026-10-02</span></div>
  </div>
</header>
<section class="figs">""")
    for b, v, u in figures:
        out.append(f'<div class="fig"><b>{esc(b)}</b><div class="v">{esc(str(v))}</div><div class="u">{esc(u)}</div></div>')
    out.append("</section>")

    out.append('<h2>Products and process route</h2><p class="lede">Design-case yields from the heat and material balance '
               '(stream table CFU-000-PR-HMB-001).</p><div class="split"><div class="yield">')
    for n, no in yields:
        s = S[no]
        out.append(f'<div class="yrow"><span>{esc(n)}</span><span class="ybar"><i style="width:{s["bpsd"] / ymax * 100:.1f}%"></i></span>'
                   f'<span class="n">{s["bpsd"]:,.0f} BPSD</span></div>')
    a, v = R["atm"], R["vac"]
    out.append(f"""</div><div class="flow"><ol>
<li>Crude charge P-101, cold train E-101..105 to {R['preheat']['T_desalter']:.0f} C</li>
<li>Two-stage electrostatic desalting D-101A/B, wash water 5 LV%</li>
<li>Hot train E-106..111, CIT {R['preheat']['CIT']:.0f} C</li>
<li>H-101, 8 passes, COT {a['cot']:.0f} C</li>
<li>C-101 flash zone {a['T_fz']:.0f} C / {a['P_fz_barg']:.2f} barg; TPA, MPA, BPA; strippers C-102/103/104</li>
<li>Overhead to D-102; stabiliser C-105 and splitter C-106</li>
<li>Residue via P-112 to H-201, COT {v['cot']:.0f} C</li>
<li>C-201 at {v['P_fz_mbar']:.0f} mbar(a): LVGO, HVGO, slop wax, VR; ejectors J-201..203</li>
</ol></div></div>""")

    if gal:
        out.append('<h2>Drawing set</h2><p class="lede">Key sheets. Select one to open its PDF in the repository.</p><div class="gal">')
        for src, cap, link, no in gal:
            out.append(f'<a href="{esc(link)}" target="_blank" rel="noopener"><img src="{src}" alt="{esc(cap)}" loading="lazy">'
                       f'<div class="c">{esc(cap)}<small>{esc(no)}</small></div></a>')
        out.append("</div>")

    out.append('<h2>Document register</h2><p class="lede">All documents at Rev A, issued for review. The links open the files '
               'on GitHub (main branch).</p>')
    for d, items in by_disc.items():
        if not items:
            continue
        out.append(f'<div class="disc" id="{esc(d.split()[0].lower())}"><h3>{esc(d)}</h3><div class="note">{esc(DISC_NOTE.get(d, ""))}</div>'
                   '<div class="tw"><table><thead><tr><th>Document no.</th><th>Title</th><th>Files</th></tr></thead><tbody>')
        for r in items:
            files = reg.get(r["no"], [])
            chips = "".join(f'<a class="fmt" href="{esc(GH + f)}" target="_blank" rel="noopener">{esc(Path(f).suffix[1:])}</a>'
                            for f in sorted(files, key=lambda f: (Path(f).suffix != ".pdf", f)))
            title = r["title"] if r["title"] != "(drawing)" else Path(_primary(files)).stem
            out.append(f'<tr><td class="no">{esc(r["no"])}</td><td>{esc(title)}</td><td>{chips}</td></tr>')
        out.append("</tbody></table></div></div>")

    out.append(f"""<h2>Basis and limits</h2>
<ul class="issues">
<li>The process model is a pseudo-component cut-point model with ideal VLE. Expect temperatures within about 5-10 C of a rigorous
simulation. Confirm them in HYSYS/Petro-SIM on a full assay before detailed design.</li>
<li>Vendor-dependent items are marked TBD on the datasheets: heater burners, desalter internals, ejectors and packing.</li>
<li>Open items for detailed design: the global flare load study, a stack dispersion study, a satellite substation for the VDU
(480 V cable runs of about 255 m), the C-101 overhead relief (4 T orifices), and full-vacuum design or a steam-out procedure for
the vessels other than C-201.</li>
<li>LOPA frequencies and protection-layer credits are FEED judgements for the SIL workshop. The cost estimate is AACE Class 4.</li>
</ul>
<h2>Regenerate</h2>
<div class="mono">pip install -r requirements.txt
python build.py            # all stages
python build.py process    # heat &amp; material balance + sizing only</div>
<footer>Prepared by Claude Code. Every number is computed by the cfu package; see CONVENTIONS.md for the data ownership rules.</footer>
</div>""")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text("\n".join(out))
    # 3D viewer alongside (prefer combined piping viewer)
    for cand in ("viewer-piping.html", "viewer.html"):
        vp = DLV / "03-layout-piping" / "3d" / cand
        if vp.exists():
            (OUT / "viewer.html").write_text(vp.read_text())
            break
    return OUT / "index.html"
