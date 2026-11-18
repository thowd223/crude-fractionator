"""Regenerate the embedded data block of sims/p80/p80.html from the FEED package.

Sources
  data/equipment.json, data/mech.json     equipment list and shell weights (via cfu.wrapup.estimate.ce_items)
  cfu/wrapup/estimate.py                  Class 4 factored estimate: Towler installation factors, 25 % D&E, 20 % contingency
  deliverables/06-wrapup/CFU-000-PM-EST-001_Cost-Estimate.md   issued summary, used as a cross-check
  cfu/wrapup/activities.py                45 design activities (status, links) that feed the schedule logic

Nothing here writes deliverables: ce_items() is called directly, so the estimate is recomputed exactly as issued.

    python sims/p80/extract.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cfu.wrapup import estimate as est          # noqa: E402
from cfu.wrapup.activities import ACTIVITIES   # noqa: E402

HTML = Path(__file__).with_name("p80.html")
M = 1e6

# Purchased-equipment groups used as cost lines (estimate types, smallest ones pooled)
GROUPS = [("heater", "Fired heaters", ["Fired heater"]),
          ("column", "Columns", ["Column"]),
          ("aircooler", "Air coolers", ["Air cooler"]),
          ("stx", "Shell & tube exchangers", ["Shell & tube"]),
          ("desalter", "Desalters", ["Desalter"]),
          ("pump", "Pumps", ["Pump"]),
          ("othereq", "Drums, ejectors, fans, packages", ["Drum", "Ejector", "Fan", "Package", "Air preheater"])]
# Towler installation factors, split out of the ISBL formula in estimate.build()
INSTALL = [("piping", "Piping (material + erection)", "fp"), ("erection", "Equipment erection", "fer"),
           ("elec", "Electrical", "fel"), ("instr", "Instrumentation", "fi"), ("civil", "Civil & foundations", "fc"),
           ("struct", "Structures & pipe rack", "fs"), ("lagging", "Insulation & paint", "fl")]
LONG_LEAD = ["H-101", "H-201", "C-101", "C-201", "D-101A", "D-101B", "E-108", "A-101", "A-107"]


def load_mech():
    mp = ROOT / "data" / "mech.json"
    if not mp.exists():
        return None
    raw = json.loads(mp.read_text())
    items = raw if isinstance(raw, list) else raw.get("items", raw)
    if isinstance(items, dict):
        return {k: v for k, v in items.items() if isinstance(v, dict)}
    return {x["tag"]: x for x in items if isinstance(x, dict) and "tag" in x}


def issued_summary():
    md = (ROOT / "deliverables" / "06-wrapup" / "CFU-000-PM-EST-001_Cost-Estimate.md").read_text()
    out = {}
    for k, pat in [("pec", r"Purchased equipment \(2026 USGC\) \| ([\d.,]+)"), ("isbl", r"Installed ISBL[^|]*\| ([\d.,]+)"),
                   ("eng", r"Design & engineering[^|]*\| ([\d.,]+)"), ("cont", r"Contingency[^|]*\| ([\d.,]+)"),
                   ("tic", r"Total installed cost, ISBL \| ([\d.,]+)")]:
        out[k] = float(re.search(pat, md).group(1).replace(",", ""))
    return out


def build():
    eq = json.loads((ROOT / "data" / "equipment.json").read_text())
    byt = {e["tag"]: e for e in eq}
    rows = est.ce_items(eq, load_mech())
    F = est.FACT
    ce = sum(r["ce_2026"] for r in rows)
    inst = {k: 0.0 for k, _, _ in INSTALL}
    for r in rows:   # same formula as estimate.build(): Ce[(1 + fp*1.15) + (fer+fel+fi+fc+fs+fl)/fm]
        c, fm = r["ce_2026"], max(r["fm"], 1)
        for k, _, f in INSTALL:
            inst[k] += c * F["fp"] * 1.15 if f == "fp" else c * F[f] / fm
    isbl = ce + sum(inst.values())
    de = 0.25 * isbl
    cont = 0.20 * (isbl + de)
    tic = isbl + de + cont

    lines = []
    for key, label, types in GROUPS:
        tags = [r for r in rows if r["type"] in types]
        lines.append(dict(k=key, n=label, kind="eq", b=round(sum(r["ce_2026"] for r in tags) / M, 3), cnt=len(tags)))
    for key, label, f in INSTALL:
        lines.append(dict(k=key, n=label, kind="inst", b=round(inst[key] / M, 3),
                          f=F[f] if f != "fp" else round(F[f] * 1.15, 3)))
    lines.append(dict(k="eng", n="Design & engineering (25 %)", kind="eng", b=round(de / M, 3)))

    ll = []
    for t in LONG_LEAD:
        r = next(x for x in rows if x["tag"] == t)
        e = byt[t]
        ll.append(dict(tag=t, svc=e["service"], ce=round(r["ce_2026"] / M, 3), size=e.get("size", ""),
                       moc=e.get("moc", "")))

    issued = issued_summary()
    calc = dict(pec=ce / M, isbl=isbl / M, eng=de / M, cont=cont / M, tic=tic / M)
    for k, v in issued.items():
        assert abs(calc[k] - v) < 0.06, f"{k}: recomputed {calc[k]:.2f} vs issued {v}"

    acts = [dict(id=a["id"], n=a["name"], d=a["disc"], s=a["status"], after=[x[0] for x in a["after"]],
                 note=a["note"]) for a in ACTIVITIES]
    counts = {s: sum(1 for a in ACTIVITIES if a["status"] == s) for s in ("done", "partial", "open")}
    return dict(
        doc="CFU-000-PM-EST-001", basis="AACE Class 4 (-30 % / +50 %), ISBL, USGC, 2026 USD, CEPCI 820",
        summary={k: round(v, 3) for k, v in calc.items()}, issued=issued, ce_items=len(rows),
        factors=F, lines=lines, longlead=ll, activities=acts, act_counts=counts)


def main():
    data = build()
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    src = HTML.read_text(encoding="utf-8")
    new, n = re.subn(r"/\*DATA:BEGIN\*/.*?/\*DATA:END\*/", lambda m: "/*DATA:BEGIN*/" + blob + "/*DATA:END*/",
                     src, flags=re.S)
    if n != 1:
        raise SystemExit("data markers not found in p80.html")
    HTML.write_text(new, encoding="utf-8")
    s = data["summary"]
    print(f"p80 data: PEC {s['pec']:.1f}, ISBL {s['isbl']:.1f}, D&E {s['eng']:.1f}, cont {s['cont']:.1f}, "
          f"TIC {s['tic']:.1f} USD M; {len(data['lines'])} cost lines, {len(data['activities'])} activities, "
          f"{len(blob) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
