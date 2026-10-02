"""Block Flow Diagram (CFU-000-PR-BFD-001)."""
from __future__ import annotations

import json
from pathlib import Path

from .sheet import Sheet

ROOT = Path(__file__).resolve().parents[2]


def build():
    S = {s["no"]: s for s in json.loads((ROOT / "data" / "streams.json").read_text())}
    R = json.loads((ROOT / "data" / "process_results.json").read_text())
    sh = Sheet("A2", "BLOCK FLOW DIAGRAM", "CRUDE & VACUUM DISTILLATION UNIT - OVERALL", "CFU-000-PR-BFD-001",
               notes=["Flows are design case (Arab Light, 100,000 BPSD), normal operation.",
                      "kBPSD = thousand barrels per stream day at 15 C. t/h = tonne/hour.",
                      "Stream numbers in diamonds refer to H&MB CFU-000-PR-HMB-001.",
                      "Dashed blocks/lines are outside battery limits (OSBL)."])
    d, g = sh.dwg, sh.g

    def block(x, y, w, h, title, sub=(), osbl=False, fill="#EEF3FA"):
        g.add(d.rect((x, y), (w, h), fill=fill if not osbl else "white", stroke="black", stroke_width=0.6,
                     stroke_dasharray="3,1.5" if osbl else "none", rx=1.5))
        sh.text(title, x + w / 2, y + 7, 3.6, "middle", bold=True)
        for i, s in enumerate(sub):
            sh.text(s, x + w / 2, y + 13 + i * 4.2, 2.6, "middle")
        return (x, y, w, h)

    def arrow(pts, label=None, lpos=None, no=None, dashed=False, color="black"):
        g.add(d.polyline(pts, stroke=color, stroke_width=0.55, fill="none",
                         stroke_dasharray="3,1.5" if dashed else "none"))
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        import math
        a = math.atan2(y2 - y1, x2 - x1)
        L = 3.0
        p1 = (x2 - L * math.cos(a - 0.35), y2 - L * math.sin(a - 0.35))
        p2 = (x2 - L * math.cos(a + 0.35), y2 - L * math.sin(a + 0.35))
        g.add(d.polygon([(x2, y2), p1, p2], fill=color, stroke=color, stroke_width=0.2))
        if label:
            lx, ly = lpos or ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2 - 1.8)
            for i, ln in enumerate(label.split("\n")):
                sh.text(ln, lx, ly + i * 3.2, 2.4, "middle")
        if no:
            mx, my = (pts[-2][0] + pts[-1][0]) / 2, (pts[-2][1] + pts[-1][1]) / 2
            if lpos and len(pts) == 2:
                pass
            diamond(*(no_pos(pts)), no)

    def no_pos(pts):
        (x1, y1), (x2, y2) = pts[0], pts[1]
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def diamond(x, y, no):
        r = 3.2
        g.add(d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill="white", stroke="black",
                        stroke_width=0.35))
        sh.text(no, x, y + 1.0, 2.4, "middle", bold=True)

    def kbpsd(no):
        s = S[no]
        return f"{s.get('bpsd', 0) / 1000:.1f} kBPSD / {s['total_kg_h'] / 1000:.1f} t/h"

    def th(no):
        return f"{S[no]['total_kg_h'] / 1000:.1f} t/h"

    # ---- blocks ------------------------------------------------------------
    block(20, 120, 50, 30, "CRUDE TANKAGE", ["(OSBL)", "Arab Light 33.4 API"], osbl=True)
    block(95, 105, 70, 60, "DESALTING & PREHEAT", ["(AREA 100)", "Cold train E-101..105", "2-stage desalter D-101A/B",
                                          f"Hot train E-106..111", f"CIT {R['preheat']['CIT']:.0f} C"])
    block(190, 115, 52, 40, "ATM. HEATER", ["H-101", f"{R['heaters']['H-101']['Q_abs_kw'] / 1000:.1f} MW abs.",
                                            f"COT {R['atm']['cot']:.0f} C"])
    block(270, 70, 70, 130, "ATMOSPHERIC", ["FRACTIONATION", "C-101 + strippers", "C-102/103/104",
                                            f"Top {R['atm']['P_top_barg']:.1f} barg",
                                            f"FZ {R['atm']['T_fz']:.0f} C"])
    block(395, 25, 72, 46, "NAPHTHA", ["STABILISATION &", "SPLITTING", "C-105 Stabiliser", "C-106 Splitter"])
    block(270, 225, 52, 40, "VACUUM HEATER", ["H-201", f"{R['heaters']['H-201']['Q_abs_kw'] / 1000:.1f} MW abs.",
                                              f"COT {R['vac']['cot']:.0f} C"])
    block(350, 205, 72, 85, "VACUUM", ["DISTILLATION", "C-201 (packed)", f"FZ {R['vac']['P_fz_mbar']:.0f} mbar(a)",
                                       f"FZ {R['vac']['T_fz']:.0f} C"])
    block(300, 305, 72, 24, "EJECTOR SYSTEM", ["J-201/202/203, D-201"])
    block(25, 240, 85, 62, "UTILITIES", ["(OSBL supply)",
                                         "HP/MP/LP steam, BFW",
                                         "Cooling water 32/43 C",
                                         "Fuel gas, N2, inst. air",
                                         "Power 13.8 kV, 60 Hz", "Flare / SWS / WWT"], osbl=True)

    # ---- streams -----------------------------------------------------------
    arrow([(70, 135), (95, 135)], no="1")
    sh.text(kbpsd("1"), 82, 131, 2.2, "middle")
    arrow([(165, 135), (190, 135)], no="6")
    sh.text(f"{S['6']['T_C']:.0f} C", 177, 131, 2.2, "middle")
    arrow([(242, 135), (270, 135)], no="7")
    sh.text(f"{S['7']['T_C']:.0f} C, VF {S['7']['vf_mass']:.2f}", 256, 131, 2.2, "middle")
    # brine
    arrow([(130, 165), (130, 190), (160, 190)], no="4")
    sh.text(f"Brine to WWT {th('4')}", 163, 191, 2.4)
    arrow([(110, 190), (110, 165)], no="3")
    sh.text(f"Wash water {th('3')}", 107, 195, 2.4, "end")
    # naphtha to stab
    arrow([(305, 70), (305, 48), (395, 48)], no="11")
    sh.text(f"Unstab. naphtha {kbpsd('11')}", 350, 44, 2.4, "middle")
    arrow([(285, 70), (285, 40), (240, 40)], no="12")
    sh.text(f"Sour water to SWS {th('12')}", 238, 37, 2.4, "end")
    # stab products
    prods_n = [("30", "LPG to treating", 30), ("32", "Light naphtha to isom.", 45), ("33", "Heavy naphtha to NHT", 60)]
    for no, nm, y in prods_n:
        arrow([(467, y), (520, y)], no=no)
        sh.text(nm, 523, y - 1, 2.7, bold=True)
        sh.text(kbpsd(no), 523, y + 2.6, 2.3)
    arrow([(431, 25), (431, 15), (520, 15)], no="29", dashed=True)
    sh.text("Off-gas to FG (normally no flow)", 523, 16, 2.5)
    # side products
    for no, nm, y in [("16", "Kerosene to KHT", 100), ("17", "Diesel to DHT", 125), ("18", "AGO to DHT/FCC", 150)]:
        arrow([(340, y), (520, y)], no=no)
        sh.text(nm, 523, y - 1, 2.7, bold=True)
        sh.text(kbpsd(no), 523, y + 2.6, 2.3)
    # AR
    arrow([(305, 200), (305, 212), (296, 212), (296, 225)], no="19")
    sh.text(f"Atm. residue {kbpsd('19')}", 300, 207, 2.4, "end")
    arrow([(322, 245), (350, 245)], no="21")
    # vac products
    for no, nm, y in [("23", "LVGO to hydrocracker", 215), ("24", "HVGO to FCC/HCU", 235),
                      ("25", "Slop wax to FCC/slop", 255), ("26", "Vacuum residue to coker", 275)]:
        arrow([(422, y), (520, y)], no=no)
        sh.text(nm, 523, y - 1, 2.7, bold=True)
        sh.text(kbpsd(no), 523, y + 2.6, 2.3)
    arrow([(386, 290), (386, 317), (372, 317)])
    sh.text("22  Vac. OH (steam + NCG)", 389, 300, 2.2)
    arrow([(336, 329), (336, 345), (200, 345)], no="27")
    sh.text(f"Sour water to SWS {th('27')}", 198, 344, 2.5, "end")
    arrow([(310, 305), (310, 265)], no="28", dashed=True)
    sh.text("Vac. off-gas to H-201", 312, 290, 2.4)
    # utilities link
    arrow([(110, 270), (150, 270), (150, 165)], dashed=True)
    sh.text("Steam / FG / CW / power", 153, 262, 2.4)

    # yields table
    x0, y0 = 20, 30
    sh.text("PRODUCT YIELDS (DESIGN CASE)", x0, y0, 3.2, bold=True)
    rows = [("LPG", "30"), ("Light naphtha", "32"), ("Heavy naphtha", "33"), ("Kerosene", "16"), ("Diesel", "17"),
            ("AGO", "18"), ("LVGO", "23"), ("HVGO", "24"), ("Slop wax", "25"), ("Vacuum residue", "26")]
    hdr = ["Product", "kBPSD", "wt%", "t/h", "API"]
    xs = [x0, x0 + 32, x0 + 50, x0 + 65, x0 + 80]
    for x, h in zip(xs, hdr):
        sh.text(h, x, y0 + 6, 2.5, bold=True)
    for i, (nm, no) in enumerate(rows):
        s = S[no]
        y = y0 + 10 + i * 3.6
        for x, v in zip(xs, [nm, f"{s['bpsd'] / 1000:.1f}", f"{s['total_kg_h'] / R['crude']['kg_h'] * 100:.1f}", f"{s['total_kg_h'] / 1000:.1f}",
                             f"{s['api']:.1f}"]):
            sh.text(v, x, y, 2.4)
    sh.save(ROOT / "deliverables" / "01-process" / "bfd" / "CFU-000-PR-BFD-001")


if __name__ == "__main__":
    build()
