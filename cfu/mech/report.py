"""CFU-000-ME-CAL-001 Mechanical design calculations (markdown + PDF)."""
from __future__ import annotations

import math

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

from .. import basis
from . import issues as ISS
from .common import MATERIALS, OUT, S_allow, nps_str
from .geometry import CRIT
from .heaters import F_CORR, P9
from .vessel import ATTACH, CF, KD, MIN_T_RULE, P_FV, RING_SPACING, WIND_V

DOC = "CFU-000-ME-CAL-001"
TITLE = "Mechanical Design Calculations"


def f(x, n=1):
    if x is None:
        return "-"
    if isinstance(x, str):
        return x
    return f"{x:,.{n}f}"


class Doc:
    def __init__(self):
        self.blocks = []

    def h1(self, t):
        self.blocks.append(("h1", t))

    def h2(self, t):
        self.blocks.append(("h2", t))

    def p(self, t):
        self.blocks.append(("p", t))

    def bullets(self, items):
        self.blocks.append(("ul", items))

    def table(self, hdr, rows, note=None, widths=None):
        self.blocks.append(("tbl", hdr, rows, note, widths))

    def pagebreak(self):
        self.blocks.append(("pb",))

    # ---------------- markdown
    def md(self):
        L = [f"# {DOC} - {TITLE}", "",
             f"**Project:** {basis.PROJECT['name']} | **Client:** {basis.PROJECT['client']} | "
             f"**Rev {basis.PROJECT['rev']}** - {basis.PROJECT['rev_desc']} | 2026-10-02 | Prepared: CLAUDE CODE", ""]
        for b in self.blocks:
            k = b[0]
            if k == "h1":
                L += [f"## {b[1]}", ""]
            elif k == "h2":
                L += [f"### {b[1]}", ""]
            elif k == "p":
                L += [b[1], ""]
            elif k == "ul":
                L += [f"* {x}" for x in b[1]] + [""]
            elif k == "tbl":
                hdr, rows, note = b[1], b[2], b[3]
                L.append("| " + " | ".join(hdr) + " |")
                L.append("|" + "|".join("---" for _ in hdr) + "|")
                for r in rows:
                    L.append("| " + " | ".join(str(x) for x in r) + " |")
                L.append("")
                if note:
                    L += [f"*{note}*", ""]
        return "\n".join(L)

    # ---------------- pdf
    def pdf(self, path):
        ss = getSampleStyleSheet()
        st = dict(
            h1=ParagraphStyle("h1", parent=ss["Heading1"], fontSize=12.5, spaceBefore=8, spaceAfter=4,
                              textColor=colors.HexColor("#1F3864")),
            h2=ParagraphStyle("h2", parent=ss["Heading2"], fontSize=10.5, spaceBefore=6, spaceAfter=3),
            p=ParagraphStyle("p", parent=ss["BodyText"], fontSize=8.6, leading=10.8, alignment=TA_LEFT),
            cell=ParagraphStyle("c", parent=ss["BodyText"], fontSize=6.9, leading=8.0),
            cellb=ParagraphStyle("cb", parent=ss["BodyText"], fontSize=6.9, leading=8.0, fontName="Helvetica-Bold",
                                 textColor=colors.white),
            note=ParagraphStyle("n", parent=ss["BodyText"], fontSize=7.2, leading=8.6, textColor=colors.HexColor("#333333"),
                                fontName="Helvetica-Oblique"),
        )
        W = landscape(A4)[0] - 30 * mm
        flow = []
        P = basis.PROJECT
        title_tbl = Table([[Paragraph(f"<b>{P['client'].upper()}</b><br/>{P['name']}", st["p"]),
                            Paragraph(f"<b>{TITLE.upper()}</b><br/>Columns, drums, desalters, fired-heater coils, "
                                      f"nozzles, wind/skirts, weights", st["p"]),
                            Paragraph(f"<b>{DOC}</b><br/>Rev {P['rev']} - {P['rev_desc']}<br/>2026-10-02 - "
                                      f"Prepared: CLAUDE CODE - Discipline: MECHANICAL", st["p"])]],
                          colWidths=[W * 0.3, W * 0.38, W * 0.32])
        title_tbl.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                                       ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.black),
                                       ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        flow += [title_tbl, Spacer(1, 6)]
        for b in self.blocks:
            k = b[0]
            if k in ("h1", "h2"):
                flow.append(Paragraph(b[1], st[k]))
            elif k == "p":
                flow.append(Paragraph(b[1], st["p"]))
            elif k == "ul":
                for x in b[1]:
                    flow.append(Paragraph("&bull; " + x, st["p"]))
            elif k == "pb":
                flow.append(PageBreak())
            elif k == "tbl":
                hdr, rows, note, widths = b[1:]
                data = [[Paragraph(str(h), st["cellb"]) for h in hdr]] + \
                       [[Paragraph(str(c), st["cell"]) for c in r] for r in rows]
                n = len(hdr)
                if widths:
                    tot = sum(widths)
                    cw = [W * w / tot for w in widths]
                else:
                    lens = [max(len(str(hdr[i])), *(len(str(r[i])) for r in rows)) if rows else len(hdr[i])
                            for i in range(n)]
                    lens = [min(max(l, 4), 60) for l in lens]
                    tot = sum(lens)
                    cw = [W * l / tot for l in lens]
                t = Table(data, colWidths=cw, repeatRows=1)
                t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
                                       ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#808080")),
                                       ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3FA")]),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                                       ("TOPPADDING", (0, 0), (-1, -1), 1.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2)]))
                flow.append(t)
                if note:
                    flow.append(Paragraph(note, st["note"]))
                flow.append(Spacer(1, 4))

        def deco(c, d):
            c.saveState()
            c.setFont("Helvetica", 7)
            c.drawString(15 * mm, 8 * mm, f"{DOC} Rev {P['rev']}  -  {TITLE}  -  {P['name']}")
            c.drawRightString(landscape(A4)[0] - 15 * mm, 8 * mm, f"Page {d.page}")
            c.restoreState()

        doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=15 * mm,
                                topMargin=12 * mm, bottomMargin=14 * mm, title=f"{DOC} {TITLE}", author="CLAUDE CODE")
        doc.build(flow, onFirstPage=deco, onLaterPages=deco)


# ---------------------------------------------------------------------------
def build(calc):
    d = Doc()
    C, G, D = calc["columns"], calc["geoms"], calc["drums"]
    d.h1("1. Purpose and scope")
    d.p("FEED-level mechanical design of the CDU/VDU pressure equipment: shell/head/cone thickness to ASME VIII "
        "Div.1, external pressure (C-201 full vacuum) with stiffening rings, hydrotest pressures, empty / operating / "
        "hydrotest weights, skirt heights, ASCE 7 wind loads with skirt and anchor-bolt checks, API 530 fired-heater "
        "tube thickness, and main-column nozzle sizing. Inputs are read from data/equipment.json, streams.json, "
        "process_results.json and psv.json (generator cfu/mech). Results are exported to data/mech.json for the "
        "layout, civil/foundation and cost-estimate work. Datasheets: CFU-000-ME-DS-001..007; GA drawings: "
        "CFU-100/200-ME-GA-001..008.")
    d.h1("2. Design basis and assumptions")
    d.bullets([
        "Code: ASME BPVC VIII Div.1 (2023) - UG-16, UG-23, UG-27, UG-28, UG-29, UG-32, UG-33, UG-99; ASME II-D Table 1A "
        "allowable stresses (Section 3). Flanges ASME B16.5 / B16.47 Group 1.1 ratings.",
        "Design pressure / temperature and corrosion allowance from equipment.json. Static liquid head to HLL added to "
        "the design pressure of bottom courses and bottom heads (operating liquid density from H&MB).",
        "Joint efficiency E = 1.0 (full RT) for columns, desalters and drums >= 2.0 m ID; E = 0.85 (spot RT) for smaller "
        "drums. Skirt-to-head weld efficiency 0.7.",
        f"Fabrication minimum: {MIN_T_RULE}; plus CA. Heads: 2:1 semi-ellipsoidal, nominal = max(min. after forming "
        f"+ 1.5 mm thinning, adjoining shell). Cones: 30 deg half-angle, UG-32(g); junction reinforcement per "
        f"App. 1-5/1-8 by fabricator.",
        f"Cladding / linings (410S, 317L, Monel 400) are corrosion barriers only - not credited for strength; "
        f"included in weights (3 mm clad, 2 mm Monel lining).",
        f"External pressure (C-201): {P_FV * 10:.3f} bar (15 psi) full vacuum at design temperature. Factor A from the "
        f"Div.2 4.4.5.1 closed form (the basis of Fig. G), factor B = A.E/2 in the elastic range with a plastic "
        f"knee at 0.5 Sy(T) representing chart CS-2. <b>Stiffening rings: external flat-bar rings at max. "
        f"{RING_SPACING / 1000:.1f} m spacing</b> on all C-201 cylindrical courses (rings double as insulation/"
        f"platform supports); cone-cylinder junctions taken as lines of support (to be confirmed by App. 1-8).",
        f"Wind: ASCE 7-16 Ch.26/29, V = 150 mph ({WIND_V:.1f} m/s, 3-s gust), Exposure C, Kd = {KD}, Kzt = 1.0, "
        f"Cf = {CF} (round, moderately smooth), effective diameter = insulated OD + {ATTACH} m (ladders, piping), "
        f"platforms 1.2 m2 x Cf 2.0 each. Gust factor G = 0.85 for rigid structures (n1 >= 1 Hz); Gf per 26.11.5 "
        f"(beta = 1 %) for flexible columns. Stress checks use ASD 0.6W (+ 0.6D for anchor uplift).",
        "Longitudinal stress (UG-23): tension (windward, design pressure, empty weight) <= S.E; compression (leeward, "
        "operating weight, + vacuum for C-201) <= B (UG-23(b), A = 0.125/(Ro/t)). No 1.2 wind increase taken.",
        "Skirt height set by NPSH of the bottoms pump: LLL >= pump CL (EL 100.800) + NPSHr(est.) + 1.0 m margin "
        "+ 0.6 m suction losses, with minimum 3.0 m (5.0 m C-101, 6.0 m C-201). NPSHr estimated from suction-specific "
        "speed 200 (metric) - see datasheet CFU-000-ME-DS-006.",
        "Weights: steel density 7850 kg/m3; nozzles 1.6 NPS^1.75 kg (manways x1.4 + 150 kg); valve trays 60-75 kg/m2 "
        "+ support ring; structured packing 150-210 kg/m3, grid 380 kg/m3; distributors 120 kg/m2; collector trays "
        "220 kg/m2; platforms 250 kg/m2 (60 % wrap, 1.2 m wide) + ladders 35 kg/m; insulation mineral wool "
        "130 kg/m3 + 6 kg/m2 cladding; skirt fireproofing 50 mm both faces. Operating liquid: tray clear liquid + "
        "downcomer backup, packing hold-up 5 %, sump to NLL. Hydrotest: vessel full of water (internals installed, "
        "no insulation).",
        "Accuracy: thickness to nominal plate; weights +/-15 % (vessels), +/-30 % (fired heaters, exchangers, air "
        "coolers). All values to be superseded by vendor/fabricator calculations.",
    ])
    # ---- materials
    d.h1("3. Material allowable stresses (ASME II-D Table 1A)")
    Ts = [40, 100, 150, 200, 250, 300, 325, 350, 375, 400, 425, 450, 475, 500]
    rows = []
    for k, m in MATERIALS.items():
        rows.append([k, m["name"]] + [f(S_allow(k, T), 0) for T in Ts])
    d.table(["Spec", "Material"] + [f"{T} C" for T in Ts], rows,
            note="S in MPa; customary-unit values converted and interpolated. SA-516-70 above 425 C is subject to "
                 "graphitisation limits (not used above 415 C here).", widths=[7, 18] + [3.2] * len(Ts))
    rows = []
    for t, r in C.items():
        rows.append([t, r["mat"], f(r["Td"], 0), f(r["S"], 1), f(r["S_amb"], 1), r["E"], f(r["CA"], 1)])
    for t, r in D.items():
        rows.append([t, r["mat"], f(r["Td"], 0), f(r["S"], 1), f(r["S_amb"], 1), r["E"], f(r["CA"], 1)])
    d.table(["Tag", "Base material", "Design T (C)", "S at design T (MPa)", "S at test T (MPa)", "E", "CA (mm)"], rows)
    d.h1("4. Formulae")
    d.bullets([
        "Shell, circumferential stress UG-27(c)(1): t = P.R / (S.E - 0.6 P); longitudinal UG-27(c)(2): t = P.R / "
        "(2 S.E + 0.4 P); R = inside radius in corroded condition.",
        "2:1 ellipsoidal head UG-32(d): t = P.D / (2 S.E - 0.2 P). Cone UG-32(g): t = P.D / (2 cos(a) (S.E - 0.6 P)).",
        "External pressure UG-28(c): Pa = 4B / (3 Do/t); UG-33(d) ellipsoidal head: Pa = B / (Ro/t), Ro = 0.9 Do; cone "
        "UG-33(f): equivalent cylinder Le = (L/2)(1 + Ds/DL), te = t cos(a).",
        "Stiffening ring UG-29: Is = Do^2 Ls (t + As/Ls) A / 14, A from B = 0.75 P Do / (t + As/Ls).",
        "Hydrotest UG-99(b): Pt = 1.3 MAWP (S_test / S_design), MAWP taken = design pressure (top); bottom adds "
        "water head. Membrane stress at test <= 0.9 Sy (vertical field test).",
        "API 530: elastic t_sigma = P_el.Do / (2 sigma_el + P_el), t = t_sigma + CA; rupture t_sigma = P_r.Do / "
        f"(2 sigma_r + P_r), t = t_sigma + f_corr.CA (f_corr = {F_CORR}).",
    ])
    # ---- column thickness
    d.h1("5. Columns - shell, cone and head thickness (internal pressure)")
    for t, r in C.items():
        g = G[t]
        rows = []
        for s in r["segs"]:
            rows.append([s["name"], f(s["D_mm"], 0), f"{s['z0']:.2f}-{s['z1']:.2f}", f(s["P_calc"] * 10, 2),
                         f(s["t_circ"], 2), f(s["t_long"], 2) if s["kind"] == "cyl" else "-", f(s["t_minfab"], 1),
                         f(r["CA"], 1), f(s["t_req"], 1), f(s["t_ext"], 0) if s["t_ext"] else "-",
                         f(s.get("t_wind"), 0) if s.get("t_wind") else "-", f"<b>{s['t_nom']}</b>"])
        for pos, h in r["heads"].items():
            rows.append([f"Head ({pos}) 2:1 SE", f(h["D_mm"], 0), "-", f(h["P_calc"] * 10, 2), f(h["t_press"], 2), "-",
                         "-", f(r["CA"], 1), f(h["t_req"], 1), f(h["t_ext"], 0) if h["t_ext"] else "-", "-",
                         f"<b>{h['t_nom']}</b> (min {h['t_min_formed']:.1f} formed)"])
        e = g["e"]
        d.h2(f"{t} - {e['service']} ({r['mat']}, P = {r['Pd']} barg{' + FV' if r['fv'] else ''}, "
             f"T = {r['Td']:.0f} C, S = {r['S']:.1f} MPa, E = {r['E']}, CA = {r['CA']} mm)")
        d.table(["Component", "ID (mm)", "z (m from BTL)", "P calc (barg)", "t circ", "t long", "t min fab", "CA",
                 "t req (int)", "t ext (FV)", "t wind", "t nominal (mm)"], rows,
                widths=[16, 6, 8, 6, 5, 5, 5, 4, 6, 6, 5, 11])
    # ---- external pressure
    d.h1("6. C-201 external pressure (full vacuum) and stiffening rings")
    r = C["C-201"]
    rows = []
    for s in r["segs"]:
        x = s.get("ext")
        if not x:
            continue
        t = s["t_ext"] - r["CA"]
        te = t * (math.cos(math.radians(30)) if s["kind"] == "cone" else 1)
        rows.append([s["name"], f(x["Do"], 0), f(s["t_ext"], 0), f(te, 1), f(x["Ls"], 0), f(x["Ls"] / x["Do"], 3),
                     f(x["Do"] / te, 0), f"{x['A']:.2e}", f(x["B"], 1), f(x["Pa"] * 10, 3), f(P_FV * 10, 3),
                     f(s.get("t_ext_norings"), 0) if s.get("t_ext_norings") else "-"])
    d.table(["Course", "Do (mm)", "t nom", "t corr/eff", "L (mm)", "L/Do", "Do/t", "A", "B (MPa)", "Pa (bar)",
             "Req. (bar)", "t if no rings"], rows,
            note=f"Design temperature {r['Td']:.0f} C, material {r['mat']}, CA {r['CA']} mm; cones use the "
                 f"equivalent-cylinder method. Without rings the main shell would need the thickness in the last "
                 f"column.", widths=[16, 6, 5, 6, 6, 5, 5, 7, 6, 6, 6, 6])
    rows = []
    for s in r["segs"]:
        if s.get("ring"):
            q = s["ring"]
            rows.append([s["name"], s.get("n_rings"), f(s["ext"]["Ls"], 0), f"{q['h']} x {q['b']}", f(q["As"], 0),
                         f"{q['A']:.2e}", f(q["B"], 1), f"{q['Is_req'] / 1e6:.2f}", f"{q['I'] / 1e6:.2f}"])
    d.table(["Course", "No. of rings", "Spacing Ls (mm)", "Flat bar h x b (mm)", "As (mm2)", "A", "B (MPa)",
             "Is req (10^6 mm4)", "I provided (10^6 mm4)"], rows,
            note="External rings, continuous fillet welds both sides (UG-30). Ring stiffeners also carry insulation "
                 "support. Internal bed-support / collector rings are not credited.")
    hd = r["heads"]
    d.p(f"Heads under external pressure (UG-33(d)): top head t = {hd['top']['t_ext']} mm, bottom head t = "
        f"{hd['bottom']['t_ext']} mm minimum (corroded {r['CA']} mm deducted); nominal {hd['top']['t_nom']} / "
        f"{hd['bottom']['t_nom']} mm.")
    # ---- hydrotest
    d.h1("7. Hydrotest")
    rows = []
    for t, r in C.items():
        h = r["hydro"]
        rows.append([t, f(r["Pd"], 1), f(h["S_amb"] / h["S_des"], 3), f(h["Pt_top"], 2), f(h["Pt_bot"], 2),
                     f(h["sigma_bot"], 0), f(h["lim"], 0), "OK" if h["sigma_bot"] <= h["lim"] else "CHECK",
                     "Vertical (field)"])
    for t, r in D.items():
        rows.append([t, f(r["Pd"], 1), f(r["S_amb"] / r["S"], 3), f(r["Pt"], 2), f(r["Pt"] + r["D"] * 0.0981, 2), "-",
                     "-", "OK", "Horizontal (shop)" if r["orient"] == "H" else "Vertical"])
    d.table(["Tag", "MAWP (barg)", "S_test/S_des", "Pt top (barg)", "Pt bottom (barg)", "sigma bottom (MPa)",
             "0.9 Sy (MPa)", "Check", "Test position"], rows,
            note="Foundations for C-101 / C-201 shall be checked for the full-of-water hydrotest weight (Section 8) "
                 "unless a pneumatic/hydro-pneumatic or horizontal shop test is specified.")
    # ---- weights
    d.h1("8. Weights")
    rows = []
    for t, r in C.items():
        W = r["W"]
        c = W["cat"]
        rows.append([t, f(c.get("shell", 0) / 1e3 + c.get("heads", 0) / 1e3), f(c.get("skirt", 0) / 1e3),
                     f(c.get("nozzles", 0) / 1e3), f(c.get("internals", 0) / 1e3), f(c.get("clad", 0) / 1e3),
                     f(c.get("platforms", 0) / 1e3), f(c.get("insulation", 0) / 1e3 + c.get("fireproofing", 0) / 1e3),
                     f"<b>{W['empty'] / 1e3:.1f}</b>", f(c.get("op_liquid", 0) / 1e3), f"<b>{W['operating'] / 1e3:.1f}</b>",
                     f(W["V_m3"], 0), f"<b>{W['hydrotest'] / 1e3:.1f}</b>"])
    d.table(["Tag", "Shell + heads", "Skirt + base", "Nozzles", "Internals", "Clad", "Platf./ladders",
             "Insul./fireproof.", "EMPTY", "Op. liquid", "OPERATING", "Volume (m3)", "HYDROTEST"], rows,
            note="Tonnes. EMPTY = installed, incl. internals, platforms, insulation and fireproofing (erection lift "
                 "excludes platforms/insulation if installed after setting).")
    rows = []
    for t, r in D.items():
        W = r["W"]
        rows.append([t, r["e"]["service"] if "e" in r else "", f"{r['D']:.1f} x {r['L']:.1f}", r["mat"], f(r["P_calc"] * 10, 2),
                     f(r["t_req"], 1), f"<b>{r['t_nom']}</b>", f(r["t_head_req"], 1), f"<b>{r['t_head_nom']}</b>",
                     f(W["fabricated"] / 1e3), f(W["empty"] / 1e3), f(W["operating"] / 1e3), f(W["hydrotest"] / 1e3)])
    d.h2("Drums and desalters - thickness and weights")
    d.table(["Tag", "Service", "ID x T/T (m)", "Material", "P calc (barg)", "Shell t req", "Shell t nom",
             "Head t req", "Head t nom", "Fabricated (t)", "Empty (t)", "Operating (t)", "Hydrotest (t)"],
            [[x[0], _svc(x[0]), *x[2:]] for x in rows], widths=[5, 15, 6, 6, 5, 5, 5, 5, 5, 6, 5, 6, 6],
            note="Desalters operate liquid-full (crude/water, 780 kg/m3); include 3 transformers (4.5 t each) and "
                 "18 t internals. Drums at 50 % liquid. Boots included (D-102, D-105).")
    # ---- skirts / wind
    d.h1("9. Skirt height, wind load and longitudinal stress")
    rows = []
    for t, r in C.items():
        g = G[t]
        rows.append([t, g.get("bottoms_pump") or "- (no pump)", f(r["npshr"], 1) if g.get("bottoms_pump") else "-",
                     f(g["levels"]["LLL"], 1), f(r["skirt_h"], 1), f(100 + r["skirt_h"], 3), f(r["skirt"]["t_nom"], 0),
                     f(r["skirt"]["D_mm"], 0)])
    d.table(["Tag", "Bottoms pump", "NPSHr est. (m)", "LLL above BTL (m)", "Skirt height (m)", "BTL elevation",
             "Skirt t (mm)", "Skirt OD (mm)"], rows,
            note="C-105 bottoms flow under pressure to C-106 / kettle E-116; skirt 6.0 m for kettle liquid head and "
                 "bottom piping.")
    rows = []
    for t, r in C.items():
        w = r["wind"]
        rows.append([t, f(r["W"]["H_total"], 1), f(r["fn"], 2), w.get("gtype", ""), f(w["G"], 3), f(w["Kz_top"], 3),
                     f(w["qh"] / 1000, 2), f(w["V_base"] / 1e3, 0), f(w["M_base"] / 1e3, 0),
                     f(0.6 * w["M_base"] / 1e3, 0), f(r["Vcr"], 1)])
    d.table(["Tag", "Height (m)", "n1 (Hz)", "Type", "G / Gf", "Kz top", "qh (kPa)", "Base shear (kN)",
             "Base moment (kNm)", "ASD moment (kNm)", "Vortex Vcr (m/s)"], rows,
            note="Strength-level wind. Vortex shedding: critical velocity Vcr = n1.D/0.2. Columns with Vcr < ~25 m/s "
                 "and D/t > 200 to be checked in detail (helical strakes not expected for insulated columns with "
                 "platforms).")
    for t in ("C-101", "C-201"):
        r = C[t]
        d.h2(f"{t} - wind / weight longitudinal stress check (corroded, ASD)")
        rows = []
        for s in r["segs"]:
            L = s["long"]
            rows.append([s["name"], f(L["z"], 2), f(s["t_nom"], 0), f(L["M"] / 1e3, 0), f(L["sigma_p"], 1), f(L["sigma_b"], 1),
                         f(L["sigma_w"], 1), f(L["tension"], 1), f(L["S"], 1), f(L["compression"], 1), f(L["B"], 1),
                         "OK" if L["ok"] else "FAIL"])
        sk = r["skirt"]
        rows.append(["Skirt (base, 1.5 mm CA, E = 0.7)", "0.00", f(sk["t_nom"], 0), f(sk["M_asd"] / 1e3, 0), "-",
                     f(sk["sigma_b"], 1), f(sk["comp"] - sk["sigma_b"], 1), f(sk["tens"], 1), f(sk["S_E"], 1),
                     f(sk["comp"], 1), f(sk["B"], 1), "OK" if sk["ok"] else "FAIL"])
        d.table(["Section (bottom of)", "Elev. above grade (m)", "t nom", "M ASD (MNm)", "sig P", "sig M", "sig W",
                 "Tension", "Allow. S.E", "Compression", "Allow. B", "Result"], rows,
                widths=[16, 6, 4, 6, 5, 5, 5, 6, 6, 7, 6, 5])
        a = r["anchor"]
        d.p(f"Anchor bolts {t}: {a['n']} x {a['size']} ASTM F1554 Gr.55 on {a['Dbc']:.2f} m BCD; max. tension "
            f"{a['F_bolt_kN']:.0f} kN/bolt (0.6D + 0.6W, empty), required root area {a['Ar_mm2']:.0f} mm2. Hydrotest "
            f"skirt compression {r['skirt']['comp_hydro']:.1f} MPa (25 % wind). Base shear {r['wind']['V_base'] / 1e3:.0f} kN, "
            f"base moment {r['wind']['M_base'] / 1e3:.0f} kNm (strength) for foundation design.")
    # ---- heaters
    d.h1("10. Fired heater tubes - API 530 (9Cr-1Mo, 100,000 h)")
    H = calc["heaters"]
    rows = []
    keys = [("Radiant average flux (kW/m2, OD)", "q_avg", 1), ("Peak flux (x1.8 circ. x1.1 long.) (kW/m2)", "q_max", 1),
            ("Inside peak flux (kW/m2)", "q_in", 1), ("Bulk fluid T at outlet (C)", "T_fluid", 1),
            ("Inside film coefficient (W/m2K, EOR)", "h_i", 0), ("Coke/fouling resistance EOR (m2K/W)", "R_coke", 4),
            ("dT film (C)", "dT_film", 1), ("dT coke (C)", "dT_coke", 1), ("dT wall (C)", "dT_wall", 1),
            ("Estimated max. TMT EOR (C)", "TMT", 0), ("<b>Design metal temperature (TMT + 15 C)</b>", "Tdm", 0),
            ("equipment.json des_T (C)", "des_T_eq", 0), ("Elastic design pressure (MPa)", "P_el", 2),
            ("Rupture design pressure (MPa, coil inlet op.)", "P_r", 2), ("sigma_el at Tdm (MPa)", "s_el", 1),
            ("sigma_r 100,000 h at Tdm (MPa)", "s_r", 1), ("Corrosion allowance (mm)", "CA", 1),
            ("Elastic t_sigma (mm)", "d_el", 2), ("Rupture t_sigma (mm)", "d_r", 2), ("Elastic t_min = t_sigma + CA", "t_el", 2),
            ("Rupture t_min = t_sigma + f_corr CA", "t_r", 2), ("<b>Minimum thickness (mm)</b>", "t_min", 2)]
    for lbl, k, n in keys:
        rows.append([lbl, f(H["H-101"]["tube"][k], n), f(H["H-201"]["tube"][k], n)])
    rows.append(["Governing", H["H-101"]["tube"]["gov"], H["H-201"]["tube"]["gov"]])
    rows.append(["Minimum schedule", *(f"{H[t]['tube']['sched_min'][0]} ({H[t]['tube']['sched_min'][1]} mm)" for t in H)])
    rows.append(["<b>Selected</b> (OD 168.3 mm, A335 P9)", *(f"<b>{H[t]['tube']['sched'][0]} ({H[t]['tube']['sched'][1]} mm)</b>"
                                                             for t in H)])
    d.table(["Item", "H-101 radiant", "H-201 radiant"], rows, widths=[30, 12, 12],
            note="Sch 80 is retained (process mass-flux basis ID 146.3 mm) - gives margin for coke spalling/erosion "
                 "and decoking. 9Cr-1Mo stresses digitised from API 530 curves: " +
                 ", ".join(f"{T} C: {s:.0f}/{r_:.0f}" for (T, s), (_, r_) in zip(P9['el'][2:10], P9['rup'][1:9])) +
                 " MPa (sigma_el/sigma_r).")
    rows = []
    for t in H:
        g = H[t]["geo"]
        hh = g["h"]
        rows.append([t, f(hh["Q_fired_kw"] / 1000, 1), f(g["aph_kw"] / 1000, 1), f(hh["radiant_kw"] / 1000, 1),
                     f(g["fg_kg_s"] * 3.6, 0), f(g["BWT"], 0), f(g["T_x"], 0), f(g["T_fg_out"], 0), f(g["lmtd"], 0),
                     f(g["A_conv"], 0), f"{g['shock_rows']} + {g['conv_rows'] - g['shock_rows']} + {g['ss_rows']} SS + "
                                          f"{g['util_rows']} util.", f(g["util_kw"] / 1000, 2)])
    d.table(["Heater", "Fired (MW)", "APH duty (MW)", "Radiant (MW)", "Flue gas (t/h)", "BWT (C)", "Crossover (C)",
             "Flue out conv. (C)", "LMTD (C)", "Conv. bare area (m2)", "Rows (shock+studded+coils)",
             "Utility coil req. (MW)"], rows,
            note="Convection estimate: U = 105 W/m2K on bare-tube area (studded), 50 C minimum approach to process "
                 "inlet. Vendor to optimise.")
    # ---- nozzles
    d.h1("11. Nozzle sizing summary (main columns)")
    for t in ("C-101", "C-201", "C-102", "C-103", "C-104", "C-105", "C-106"):
        g = G[t]
        rows = []
        for n in g["nozzles"]:
            rows.append([n["mark"], n["service"], (f"{n['qty']} x " if n.get("qty", 1) > 1 else "") + nps_str(n["nps"]),
                         f"{n['rating']}#", f(n["z"], 2), f(n["Q_m3s"] * 3600, 0) if n["Q_m3s"] else "-",
                         f(n["rho"], 2 if (n["rho"] or 99) < 10 else 0) if n["rho"] else "-",
                         f(n["v"], 1) if n["v"] else "-", n["crit"] or "-"])
        d.h2(f"{t} - {g['e']['service']}")
        d.table(["Mark", "Service", "Size", "Rating", "z from BTL (m)", "Flow (m3/h act.)", "rho (kg/m3)",
                 "v (m/s)", "Criterion"], rows, widths=[4, 22, 5, 4, 5, 6, 5, 4, 16])
    # ---- exchangers
    d.h1("12. Shell & tube exchangers and air coolers - mechanical summary")
    rows = []
    for x in calc["st"]:
        rows.append([x["tag"], x["size"], x["n_shells"], f(x["area_shell"], 0), x["Nt"], f"{x['OD']} / {x['L']}",
                     f"{x['P_shell']:g} / {x['P_tube']:g}{' (FV)' if x['fv'] else ''}", f(x["des_T"], 0), x["shell_mat"],
                     x["t_shell"], x["t_chan"], f(x["empty"] / 1e3), f(x["hydrotest"] / 1e3)])
    d.table(["Tag", "TEMA size", "Shells", "m2/shell", "Tubes/shell", "Tube OD/L (mm)", "Des. P sh/tu (barg)",
             "Des. T", "Shell matl.", "Shell t", "Channel t", "Empty t/shell", "Hydro t/shell"], rows,
            note="Shell t = max(UG-27 with E = 0.85 + CA, TEMA R minimum). Bundle diameter from tube-count "
                 "correlation (square pitch 1.25 OD for fouling crude; triangular for clean condensers).")
    rows = []
    for a in calc["ac"]:
        rows.append([a["tag"], a["service"], f(a["area"], 0), a["bays"], a["rows"], a["bays_req_6rows"], a["fans"],
                     f(a["fan_D"], 1), a["motor_kw"], f(a["empty"] / 1e3)])
    d.table(["Tag", "Service", "Bare area (m2)", "Bays (data)", "Rows req.", "Bays @ 6 rows", "Fans", "Fan D (m)",
             "Motor kW", "Empty (t)"], rows)
    # ---- issues
    d.h1("13. Process-data issues and holds")
    rows = [[i + 1, t, s] for i, (t, s) in enumerate(ISS.find(calc))]
    d.table(["#", "Item", "Issue / recommendation"], rows, widths=[2, 6, 60])
    d.h1("14. Summary of results")
    d.table(*summary_rows(calc), widths=[6, 16, 8, 8, 6, 6, 6, 7, 7, 7])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{DOC}_Mechanical-Design-Calculations.md").write_text(d.md())
    d.pdf(OUT / f"{DOC}_Mechanical-Design-Calculations.pdf")
    return d


def _svc(tag):
    from .common import eq
    return eq(tag)["service"]


def summary_rows(calc):
    hdr = ["Tag", "Service", "Size (m)", "Material", "Shell t (mm)", "Head t (mm)", "Skirt (m / mm)", "Empty (t)",
           "Operating (t)", "Hydrotest (t)"]
    rows = []
    for t, r in calc["columns"].items():
        e = calc["geoms"][t]["e"]
        ts = sorted({s["t_nom"] for s in r["segs"]})
        rows.append([t, e["service"], " / ".join(f"{x:g}" for x in calc["geoms"][t]["Ds"]) + f" x {e['H']:g}", r["mat"],
                     "-".join(str(x) for x in (ts if len(ts) < 3 else [ts[0], ts[-1]])),
                     f"{r['heads']['top']['t_nom']}/{r['heads']['bottom']['t_nom']}",
                     f"{r['skirt_h']:g} / {r['skirt']['t_nom']}", f(r["W"]["empty"] / 1e3, 0),
                     f(r["W"]["operating"] / 1e3, 0), f(r["W"]["hydrotest"] / 1e3, 0)])
    for t, r in calc["drums"].items():
        rows.append([t, _svc(t), f"{r['D']:g} x {r['L']:g}", r["mat"], str(r["t_nom"]), str(r["t_head_nom"]),
                     "saddles" if r["orient"] == "H" else "legs", f(r["W"]["empty"] / 1e3, 0),
                     f(r["W"]["operating"] / 1e3, 0), f(r["W"]["hydrotest"] / 1e3, 0)])
    for t, h in calc["heaters"].items():
        g = h["geo"]
        rows.append([t, _svc(t), f"{g['L_out']:.1f} x {g['W_out']:.1f} x {g['H_top']:.0f}", "A335 P9 tubes",
                     f"{h['tube']['sched'][1]} (tube)", "-", "-", f(h["W"]["empty"] / 1e3, 0),
                     f(h["W"]["operating"] / 1e3, 0), f(h["W"]["hydrotest"] / 1e3, 0)])
    return hdr, rows
