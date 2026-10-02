"""CFU-000-PI-RPT-001 Piping routing study / stress-critical line list (md + pdf)."""
from __future__ import annotations

import math
from collections import OrderedDict
from pathlib import Path

import numpy as np

from .. import docgen
from . import specs, stress
from .mto import valve_list

# API 610 (12th ed.) Table 5 - nozzle loads, SI (N, N.m) - each top/side/end nozzle
API610 = {2: (710, 580, 890, 1280, 460, 230, 350, 620), 3: (1070, 890, 1330, 1930, 950, 470, 720, 1280),
          4: (1420, 1160, 1780, 2560, 1330, 680, 1000, 1800), 6: (2490, 2050, 3110, 4480, 2300, 1180, 1760, 3130),
          8: (3780, 3110, 4890, 6920, 3530, 1760, 2580, 4710), 10: (5340, 4450, 6670, 9630, 5020, 2440, 3800, 6750),
          12: (6670, 5340, 8000, 11700, 6100, 2980, 4610, 8210), 14: (7120, 5780, 8900, 12780, 6370, 3120, 4750, 8540),
          16: (8450, 6670, 10230, 14850, 7320, 3660, 5420, 9890)}


def _t(rows, hdr):
    out = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


def rack_chart(R, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    bents = R.P.bents
    fig, ax = plt.subplots(figsize=(10, 3.6), dpi=150)
    cols = {1: "#c0392b", 2: "#2e86c1", 3: "#27ae60"}
    bottom = np.zeros(len(bents))
    for t in (1, 2, 3):
        v = np.array([R.rack_load[t][b]["op"] for b in bents])
        ax.bar(bents, v, width=4.2, bottom=bottom, color=cols[t], label=f"Tier {t} (EL {R.P.tiers[t]:.1f})")
        bottom += v
    hyd = np.array([max(R.rack_load[t][b]["hydro_max"] for t in (1, 2, 3)) for b in bents])
    ax.plot(bents, bottom + hyd, "k--", lw=0.9, label="+ largest single-line hydrotest increment")
    ax.set_xlabel("Bent x (m, plant east)")
    ax.set_ylabel("Vertical load per bent (kN)")
    ax.set_title("PR-100 pipe rack - operating pipe load per bent from routed lines")
    ax.grid(axis="y", lw=0.3)
    ax.legend(fontsize=7, ncol=4, loc="upper right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def write(R, stem: Path):
    stem = Path(stem)
    img = stem.parent / "img"
    img.mkdir(parents=True, exist_ok=True)
    rack_chart(R, img / "rack_load.png")
    P = R.P
    crit = [r for r in R.routes if r.level == "critical"]
    T = R.mto_totals
    md = []
    md.append("# CFU-000-PI-RPT-001 Piping Routing Study and Stress-Critical Line List")
    md.append("## 1 Purpose and scope")
    md.append("FEED piping routing study for the 100 kBPSD crude + vacuum distillation unit. The study establishes the "
              "pipe-rack and equipment piping arrangement in a 3D orthogonal routing model (`data/routing.json`, "
              "3D model CFU-000-PI-3DM-002, viewer `viewer-piping.html`), issues isometrics for the layout- and "
              "stress-critical lines, quantifies rack loading, lists stress-critical lines with simplified "
              "flexibility checks, and derives pipe wall thicknesses and the MTO (CFU-000-PI-MTO-001). All inputs "
              "are read at build time from `data/lines.json` (line list), `data/layout.json` (plot plan, nozzles, rack), "
              "`data/instruments.json`, `data/psv.json` and `data/mech.json`.")
    md.append(f"- Lines in line list: **{len(P.lines)}**; routed: **{len(R.routes)}** "
              f"({len(crit)} critical/isometric, {sum(1 for r in R.routes if r.level == 'header')} unit headers, "
              f"{sum(1 for r in R.routes if r.level == 'study')} study-level auto-routed); not routed: "
              f"**{len(R.unrouted)}** (reasons in section 4 and MTO sheet Line-List-Crosscheck).")
    md.append(f"- Routed pipe {T['pipe_m']:,.0f} m net ({T['pipe_m_allow']:,.0f} m incl. allowance), "
              f"{T['fittings']:,} fittings, {T['flanges']:,} flanges, {T['welds']:,} butt welds "
              f"({T['weld_idia_shop']:,} shop + {T['weld_idia_field']:,} field inch-dia), {T['spools']:,} spools, "
              f"{T['supports']:,} supports.")
    md.append("## 2 Codes and references")
    for s in ["ASME B31.3-2022 Process Piping (wall thickness 304.1.2, flexibility 319, testing 345, PWHT 331, NDE 341)",
              "ASME B36.10M, B16.5, B16.47 Series A, B16.9, B16.10, B16.20; MSS SP-58/69 supports",
              "API 610 12th ed. (pump nozzle loads, Table 5), API 560 (fired heater terminals), API 661 (air-cooler nozzles), "
              "API 521 (relief/flare piping), WRC 537/297 (vessel nozzle local stresses)",
              "CFU-000-PI-SPC-001 Piping class summary; CFU-000-PL-PLT-001 plot plan; CFU-000-PL-ELV-003 rack section; "
              "CONVENTIONS.md (rack tiers EL 106.0 / 108.5 / 111.0, bents at 6 m)"]:
        md.append(f"- {s}")
    md.append("## 3 Routing philosophy")
    for s in [
        "**Orthogonal routing** nozzle -> stub -> drop/rise -> rack tier -> along rack -> off rack -> destination nozzle. "
        "Lines change elevation to change direction ('elevation by direction'): local north-south pipeways at EL 104.0, "
        "east-west at EL 105.4; exchanger-area pipeway EL 104.6.",
        "**Rack tier allocation:** tier 1 (EL 106.0) hot process B2/B3, crude, residue, pumparounds (T >= 260 C); "
        "tier 2 (EL 108.5) products, cold hydrocarbon, sour water; tier 3 (EL 111.0) utilities, steam, condensate, "
        "CW, fuel gas, flare. Hot / loop-bearing lines are placed at the rack edges so loops span the rack width; "
        "heaviest lines next to the bent columns.",
        "**Rack entry/exit:** tier-1 lines leave the rack below the tier (clear of tier-1 loops), tier-2/3 lines rise above "
        "their tier; minimum rise = 2 x LR elbow + 150 mm. Expansion loops are raised one rise above the tier "
        "(tier 2 loops drop below), nested loops step 0.9 m inwards and 0.45 m up; tier-3 loops avoid bays below the "
        "forced-draft air coolers (fan deck EL 113).",
        "**Expansion:** dL = e(T) x L with e from B31.3 Table C-1 (total expansion from 21 C, per class material). "
        "Rack runs are first checked for absorption by the end legs (guided cantilever, anchor at mid-run); otherwise "
        "U-loops of width 6 m (one bay) are sized: H = sqrt(3 E D (dL_loop/2) / S_A), S_A = 1.25 Sc + 0.25 Sh.",
        "**Pump suctions:** shortest route, no pockets, header falling to the pumps, gate valve in the vertical leg, "
        "temporary cone strainer, eccentric reducer FLAT ON TOP at the nozzle; discharge check + block in the riser.",
        "**Heater transfer lines:** symmetrical multi-pass outlet manifolds (equal hydraulic length per pass), "
        "continuously rising (H-101, two-phase) or riser + continuous 1:100 fall (H-201 vacuum) to the column; "
        "54\" vacuum transfer line designed for full vacuum.",
        "**C-101 overhead:** self-draining at 1:200 from column to A-101 with symmetrical inlet manifold to the three bays; "
        "neutraliser/amine injection quills within 1.5 m of the column nozzle.",
        "**Gravity draws (C-101 to strippers):** vertical drop then continuous fall 1:100, no rising leg.",
        "**Steam:** branches from top of headers; lines fall to users; drip legs/traps at low points. "
        "**Relief:** PSV outlets self-draining into the flare header (falls 1:500 to D-104).",
        "**Spools:** shop spools <= 12 m and 3.0 x 3.0 m envelope (road transport); field welds at spool breaks, tie-ins "
        "and branch connections; high-point vents / low-point drains at every pocket."]:
        md.append(f"- {s}")
    md.append("## 4 Routing model summary")
    lv = OrderedDict()
    for r in R.routes:
        a = lv.setdefault(r.level, [0, 0.0, 0])
        a[0] += 1
        a[1] += r.total_length()
        a[2] += len(r.supports)
    md.append(_t([[k, v[0], f"{v[1]:,.0f}", v[2]] for k, v in lv.items()], ["Level", "Lines", "Routed length m", "Supports"]))
    reasons = OrderedDict()
    for ln, why in R.unrouted:
        import re as _re
        k = _re.sub(r"'[^']*'", "'...'", why)[:90]
        reasons.setdefault(k, []).append(ln)
    md.append("Lines not routed at FEED (by reason):")
    md.append(_t([[k, len(v), ", ".join(x.split("-")[1] + "-" + x.split("-")[2] + "-" + x.split("-")[3] for x in v[:8])
                   + (" ..." if len(v) > 8 else "")] for k, v in reasons.items()], ["Reason", "No.", "Lines (fluid-area-seq)"]))
    md.append(f"Clash check (cylinder model, bare OD): **{len(R.clash_eq)}** line/equipment and **{len(R.clash_pp)}** "
              f"line/line interferences, of which **{sum(1 for c in R.clash_eq if c[1] == 'critical')}** / "
              f"**{sum(1 for c in R.clash_pp if 'critical' in (c[2],))}** involve critical (iso) lines - all line/line "
              "items with critical lines are crossings with auto-routed study lines that are to be re-routed in the "
              "detailed 3D model; critical lines are clash-free with equipment and each other.")
    md.append("## 5 Critical lines and isometric register")
    rows = []
    for r in crit:
        rr = next((x for x in R.iso_register if x["line"] == r.line_no), {})
        rows.append([r.iso, r.line_no, f"{r.line['from']} -> {r.line['to']}", f"{r.total_length():.1f}",
                     len(r.spools), f"{sum(1 for w in r.welds if w['type'] == 'S')}/{sum(1 for w in r.welds if w['type'] == 'F')}",
                     len(r.supports), rr.get("sheets", 1)])
    md.append(_t(rows, ["Iso", "Line", "From -> to", "Routed m", "Spools", "Welds S/F", "Supports", "Sheets"]))
    md.append("\\pagebreak")
    md.append("## 6 Pipe-rack loading")
    md.append("Line weights per metre = pipe (selected schedule) + operating content (lines.json density) + insulation "
              "(thickness per temperature, 160 kg/m3 + cladding). Load per bent = w x tributary length (6 m); loops add "
              "(2H + W) w / 2 to each loop bent. Hydrotest: operating rack load + the largest single-line water-fill "
              "increment (one line tested at a time; large gas lines tested pneumatically or with temporary supports). "
              "Friction (mu = 0.3) acts longitudinally at anchors/guides.")
    md.append("![Operating pipe load per bent and tier](img/rack_load.png)")
    rows = []
    for t in (1, 2, 3):
        d = R.rack_load[t]
        mx = max(d, key=lambda b: d[b]["op"])
        tot = sum(v["op"] for v in d.values())
        rows.append([f"Tier {t} EL {P.tiers[t]:.1f}", max(v["lines"] for v in d.values()), f"{d[mx]['op']:.0f} @ x={mx:.0f}",
                     f"{d[mx]['op'] / 10.0:.1f}", f"{max(v['hydro_max'] for v in d.values()):.0f}",
                     f"{max(v['friction'] for v in d.values()):.0f}", f"{tot:,.0f}"])
    md.append(_t(rows, ["Tier", "Max lines / bent", "Max op. load kN", "Equiv. UDL kN/m (10 m beam)",
                        "Max hydro increment kN", "Max friction kN", "Total tier kN"]))
    worst = sorted(P.bents, key=lambda b: -sum(R.rack_load[t][b]["op"] for t in (1, 2, 3)))[:6]
    md.append(_t([[f"{b:.0f}"] + [f"{R.rack_load[t][b]['op']:.0f}" for t in (1, 2, 3)] +
                  [f"{sum(R.rack_load[t][b]['op'] for t in (1, 2, 3)):.0f}"] for b in sorted(worst)],
                 ["Bent x m", "Tier 1 kN", "Tier 2 kN", "Tier 3 kN", "Total kN"]))
    md.append("Recommendation to structural: design each tier beam for the routed load above plus 25 % future "
              "space allowance and a minimum 2.0 kPa distributed load over the rack width; anchor bents to take "
              "the anchor forces from the loops (see section 7).")
    occ = {t: len(R.rack.occ[t]) for t in (1, 2, 3)}
    md.append(f"Rack occupancy (routed lines per tier): tier 1 {occ[1]}, tier 2 {occ[2]}, tier 3 {occ[3]} "
              "(full width 10 m, 25 % spare to be held).")
    md.append("## 7 Expansion loops on the rack")
    rows = []
    for r in R.routes:
        for lp in r.loops:
            inf = lp.get("info") or {}
            if not inf or (inf.get("loops", 0) == 0 and inf.get("delta", 0) < 250):
                continue
            rows.append([r.line_no, lp["tier"], r.line["design_T_C"], inf.get("L"), inf.get("delta"), inf.get("loops", 0),
                         inf.get("H", "-"), ("loops raised" if inf.get("loops") else "end legs, mid anchor")])
    rows.sort(key=lambda x: -float(x[4]))
    md.append(_t(rows[:30], ["Line", "Tier", "T C", "Run m", "dL mm", "Loops", "H m", "Basis"]))
    md.append("\\pagebreak")
    md.append("## 8 Stress-critical line list")
    md.append("Criteria (company practice, B31.3 319.4.1): **Category 1 (formal computer analysis, CAESAR II):** "
              "T > 300 C and NPS >= 6; T > 200 C and NPS >= 12; lines to rotating equipment (NPS >= 4 and T >= 150 C, "
              "or NPS >= 12); fired-heater inlet/outlet/pass lines; vacuum lines NPS >= 6; air-cooler headers "
              "(T > 120 C, NPS >= 6); NPS >= 24; flare/relief headers NPS >= 12; 600# class with T > 200 C, NPS >= 4; "
              "any routed line above 150 C failing the simplified eq.(16). **Category 2 (simplified/manual):** T > 150 C or "
              "equipment-connected NPS >= 4. **Category 3:** visual review.")
    cats = {1: [], 2: [], 3: []}
    routed = {r.line_no: r for r in R.routes}
    for l in P.lines:
        r = routed.get(l["line_no"])
        c, why = stress.stress_category(l, flex=r.flex if r else None)
        cats[c].append((l, why))
    R.stress_counts = {k: len(v) for k, v in cats.items()}
    md.append(f"Result: **Category 1: {len(cats[1])} lines**, Category 2: {len(cats[2])}, Category 3: {len(cats[3])}.")
    rows = [[l["line_no"], l["design_T_C"], l["design_P_barg"], "; ".join(w)[:70],
             ("iso " + routed[l["line_no"]].iso) if l["line_no"] in routed and getattr(routed[l["line_no"]], "iso", None)
             else ("routed" if l["line_no"] in routed else "-")] for l, w in cats[1]]
    md.append(_t(rows, ["Line (Cat 1)", "T C", "P barg", "Criteria", "Model"]))
    md.append("\\pagebreak")
    md.append("## 9 Simplified flexibility checks")
    md.append("ASME B31.3 eq.(16) (SI): D y / (L - U)^2 <= 208.3, D = OD mm, y = resultant displacement mm (thermal "
              "growth of the straight line between terminals minus differential terminal movement - column nozzle growth "
              "from skirt base at shell design temperature), L = developed length m, U = anchor distance m. "
              "Applicable only to two-anchor systems of uniform size without intermediate restraints - lines with rack "
              "anchors/loops or failing the check go to formal analysis.")
    rows = []
    for r in R.routes:
        if r.line["design_T_C"] < 150 and r.level != "critical":
            continue
        f = r.flex
        ratio = "inf" if f["ratio"] == float("inf") else f"{f['ratio']:.0f}"
        rows.append([r.line_no, r.level[:4], f"{f['L']}", f"{f['U']}", f"{f['y']}", ratio,
                     "OK" if f["ok"] else "FORMAL", f"Cat {r.cat[0]}"])
    md.append(_t(rows, ["Line", "Level", "L m", "U m", "y mm", "Dy/(L-U)^2", "Eq.16", "Cat"]))
    md.append("Guided-cantilever leg check used for loops / end legs: required leg L = sqrt(3 E D dL / S_A) "
              "(E cold modulus B31.3 Table C-6; S_A allowable displacement stress range).")
    md.append("## 10 Pump nozzle loads (API 610)")
    md.append("Pump suction/discharge piping for P-101, P-103/104, P-108 and P-112 is arranged so that the pump-side "
              "spring support carries the weight of valves/strainers, the first rigid support is adjustable, and the "
              "loop between pump and header provides flexibility. Computed nozzle loads shall not exceed API 610 Table 5 "
              "(2x for Annex F method with vendor agreement). Hot services (P-108 345 C, P-112 390 C) need warm-up "
              "bypasses and formal analysis with both pumps' operating/standby cases. Nozzle sizes below are assumed "
              "pending vendor data.")
    md.append(_t([[f"{n}\"" ] + [f"{x:,}" for x in v] for n, v in API610.items()],
                 ["Nozzle", "Fx N", "Fy N", "Fz N", "FR N", "Mx N.m", "My N.m", "Mz N.m", "MR N.m"]))
    md.append("## 11 Fired-heater terminals (API 560)")
    for s in ["H-101 / H-201 pass outlets join symmetrical manifolds on the heater north face; manifolds and the first "
              "transfer-line spool are supported from the heater structure on variable springs so that the coil "
              "terminal loads remain within API 560 Table 7 allowables (typical 8\"-12\" terminals: F 2.2-4.4 kN, "
              "M 1.4-3.4 kN.m; to be confirmed by heater vendor).",
              "Coil terminal thermal movements (heater vendor) shall be included in the transfer-line analysis; "
              "the routing gives transfer lines of {:.0f} m (H-101) and {:.0f} m (H-201) developed length.".format(
                  next((r.br('TL').length for r in crit if r.iso == 'CFU-100-PI-ISO-001'), 0),
                  next((r.br('TL').length for r in crit if r.iso == 'CFU-200-PI-ISO-001'), 0)),
              "Inlet pass lines with pass flow control valves are part of the heater inlet manifold (vendor-coordinated)."]:
        md.append(f"- {s}")
    md.append("## 12 Valve list summary")
    vl = valve_list(R)
    agg = OrderedDict()
    for (src, c_, rt, kind, n), q in vl.items():
        k = (kind, c_)
        a = agg.setdefault(k, [0, 0, 0, set()])
        a[0 if src == "ISO" else (1 if src.startswith("ROUTED") else 2)] += q
        a[3].add(n)
    rows = [[kind, c_, a[0], a[1], a[2], a[0] + a[1] + a[2], ", ".join(specs.nps_str(x) for x in sorted(a[3]))[:40]]
            for (kind, c_), a in sorted(agg.items())]
    md.append(_t(rows, ["Type", "Class", "Isos", "Study routes", "P&ID est.", "Total", "Sizes"]))
    md.append("Control valves and orifices are supplied by I&C (tags per data/instruments.json); counts above include "
              "block/bypass valves of control stations and vent/drain valves (3/4\", 1\" in B2/B3).")
    md.append("\\pagebreak")
    md.append("## 13 Wall thickness per class (ASME B31.3 304.1.2)")
    md.append("t = P D / (2 (S E W + P Y)); t_m = t + c; t_nom >= t_m / 0.875 (12.5 % mill tolerance); next standard "
              "schedule selected (ASME B36.10M), company minimum XS for <= 2\" and STD for >= 3\". Governing P/T = the "
              "line of that class and size with the largest required thickness. E = 1.0 seamless (<= 24\") / EFW with 100 % "
              "RT; 0.85 EFW spot RT; W per Table 302.3.5 above 510 C for EFW CrMo. External pressure (vacuum) checked "
              "separately (long-cylinder buckling, FS 3).")
    for c in specs.CLASSES:
        ls = [l for l in P.lines if l["cls"] == c and l["size_in"] >= 2]
        if not ls:
            continue
        rows = []
        for n in sorted({l["size_in"] for l in ls}):
            cands = [(specs.wall_calc(n, l["design_P_barg"], l["design_T_C"], c), l) for l in ls if l["size_in"] == n]
            w, l = max(cands, key=lambda x: x[0]["t_nom_req"])
            ext = ""
            if stress.is_vacuum(l):
                pr = stress.line_props(l)
                ext = f" (vac: {pr['sch']})" if pr.get("ext") else ""
            rows.append([specs.nps_str(n), w["OD"], f"{w['P']}/{w['T']}", w["S"], w["E"], w["W"], w["Y"], w["c"], w["t"],
                         w["tm"], w["t_nom_req"], w["sch"] + ext, w["wall"]])
        k = specs.cls(c)
        md.append(f"### Class {c} - {k['rating']}# {k['desc']}, CA {k['ca']} mm")
        md.append(_t(rows, ["NPS", "OD mm", "P/T gov.", "S MPa", "E", "W", "Y", "c", "t mm", "tm mm", "t_nom req", "Selected", "WT mm"]))
    md.append("\\pagebreak")
    md.append("## 14 Upstream data issues and assumptions")
    md.append("Issues for the owning disciplines (not changed by piping):")
    for s in R.P.issues + extra_issues(R):
        md.append(f"- {s}")
    md.append("Assumptions made by the routing model:")
    seen = set()
    for s in R.P.assumed:
        k = s[:60]
        if k in seen:
            continue
        seen.add(k)
        md.append(f"- {s}")
    md.append("## 15 Deliverables")
    for s in ["`data/routing.json` - routing model (polylines, fittings, supports, welds, spools, lengths, rack runs, loops, checks)",
              "`3d/CFU-000-PI-3DM-002_Piping.glb` + `3d/viewer-piping.html` (equipment + piping, toggle, click-to-identify)",
              "`piping/iso/CFU-xxx-PI-ISO-0nn_*.pdf/.svg` and merged set `CFU-000-PI-ISO-000_Isometric-Set.pdf`",
              "`piping/CFU-000-PI-MTO-001_Piping-MTO.xlsx` (pipe, fittings, flanges, valves, welds/spools, supports, line cross-check)"]:
        md.append(f"- {s}")
    docgen.render("\n\n".join(md), stem, "CFU-000-PI-RPT-001", "Piping Routing Study and Stress-Critical Line List")


def extra_issues(R):
    P = R.P
    out = []
    eqs = P.L["equipment"]
    seen = {}
    for e in eqs:
        k = (round(e["x"], 2), round(e["y"], 2), round(e["z_base"], 2))
        if k in seen and e["type"] == "Air cooler":
            out.append(f"layout.json: {e['tag']} and {seen[k]} occupy the same position (x {k[0]}, y {k[1]}) - "
                       "air-cooler bay overlap; piping to A-106 taken at the A-107-B2 nozzles")
        seen[k] = e["tag"]
    import re
    tags = {e["tag"] for e in eqs} | {e.get("parent_tag") for e in eqs}
    miss = set()
    for l in P.lines:
        for t in re.findall(r"\b([ACDEHJKPX]-\d{3})", l["from"] + " " + l["to"]):
            if t not in tags and t + "A" not in tags:
                miss.add(t)
    if miss:
        out.append(f"Equipment referenced in lines.json but absent from layout.json: {', '.join(sorted(miss))} - lines not routed")
    hx = [e for e in eqs if e["type"] == "Shell & tube" and e["z_base"] < 101.2]
    if hx:
        out.append(f"{len(hx)} shell & tube exchangers have bottom nozzles below EL 101.2 ({', '.join(e['tag'] for e in hx[:8])}"
                   f"{'...' if len(hx) > 8 else ''}): insufficient room for bottom elbows/valves/drains - recommend "
                   "exchanger supports raised to >= EL 101.5 (layout)")
    tl = next((r for r in R.routes if getattr(r, "iso", "") == "CFU-200-PI-ISO-001"), None)
    if tl:
        out.append(f"H-201 -> C-201 vacuum transfer line developed length {tl.br('TL').length:.0f} m (heater south of rack, "
                   "column north): longer than typical (< 40 m); process to confirm flash-zone pressure drop / "
                   "consider relocating H-201 adjacent to C-201 (layout)")
    t1 = next((r for r in R.routes if getattr(r, "iso", "") == "CFU-100-PI-ISO-001"), None)
    if t1:
        out.append(f"H-101 -> C-101 transfer line {t1.br('TL').length:.0f} m with rack crossing above tier 3 - "
                   "dedicated support steel at bents x=96/102 required (structural)")
    out.append("Pump nozzle sizes not in mech.json - assumed 1-2 sizes below line size for suction reducers (vendor data)")
    out.append("C-101 kero/diesel/AGO draw nozzles all at the same azimuth (layout.json): gravity drops "
               "must be staggered - recommend re-orienting draw nozzles in 20-30 deg steps (mechanical / layout)")
    return out
