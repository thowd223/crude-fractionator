"""Rank integration candidates from the register's manual hand-offs.

Every manual exchange between two different systems is scored, classed by the kind of remedy it needs and, where
its item is listed in integrations.json, assigned to one integration candidate. Candidates are then ranked.

Exchange weight (re-entry effort per project):
    form weight (data 1.0, model 0.8, drawing 0.4, document 0.4, decision 0.3)
    x number of phases the receiving task works in (each phase re-issues the information)
    x level factor 1 + 0.25 x (level needed - 1)     (final data is re-entered more carefully, and more often)

Reads (a person reading a document or drawing to write their own) carry no weight: no integration removes them.

Candidate value (0-100):
    50 x effort / largest effort       sum of exchange weights x volume (records per issue: tens 1, hundreds 2,
                                       thousands 3)
  + 30 x reach / largest reach         tasks within two hand-offs downstream of the receiving tasks
                                       (how far a typing error travels before someone sees it)
  + 20 x late share                    share of weight landing in procurement, vendors, construction or
                                       completions, or needed at level 4 (where errors cost most)
Priority = value x ease factor (easy 1.0, medium 0.75, hard 0.5). Waves: ranks 1-5, 6-12, the rest.
"""
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORM_W = {"data": 1.0, "model": 0.8, "drawing": 0.4, "document": 0.4, "decision": 0.3}
EASE = {3: ("easy", 1.0), 2: ("medium", 0.75), 1: ("hard", 0.5)}
LATE = {"SCM", "VEND", "CONS", "COMM"}
WAVES = ((5, 1), (12, 2), (10 ** 6, 3))
REMEDY = {
    "link": "Link the two systems: structured data re-typed between tools",
    "record": "Give the data a system of record: it lives only in a workbook today",
    "extract": "Publish structured data with the document: values are read out of an issued document",
    "read": "Not an integration target: a person reads a document or drawing to do their own work",
}


def load():
    return json.loads((HERE / "integrations.json").read_text())["candidates"]


def check(cands, items):
    errs, seen = [], {}
    for c in cands:
        if c.get("ease") not in EASE:
            errs.append(f"{c['id']}: ease must be 1, 2 or 3")
        if c.get("volume") not in (1, 2, 3):
            errs.append(f"{c['id']}: volume must be 1, 2 or 3")
        for i in c["items"]:
            if i not in items:
                errs.append(f"{c['id']}: unknown item {i}")
            elif i in seen:
                errs.append(f"{c['id']}: item {i} already in {seen[i]}")
            seen[i] = c["id"]
    return errs


def remedy(e):
    if e["form"] in ("document", "drawing", "decision") and e["to_sys"] == "Excel / Word":
        return "read"
    if e["from_sys"] == "Excel / Word":
        return "record"
    if e["from_sys"] == "Document Locator":
        return "extract"
    return "link"


def downstream(ex, hops=2):
    nxt = defaultdict(set)
    for e in ex:
        nxt[e["from_task"]].add(e["to_task"])

    def reach(t):
        seen, front = {t}, {t}
        for _ in range(hops):
            front = set().union(*(nxt[f] for f in front)) - seen
            seen |= front
        return seen
    return reach


def rank(tasks, items, ex):
    cands = load()
    owner = {i: c["id"] for c in cands for i in c["items"]}
    reach = downstream(ex)
    man = []
    for e in ex:
        if e["method"] != "manual" or e["from_sys"] == e["to_sys"]:
            continue
        r = remedy(e)
        w = 0 if r == "read" else FORM_W[e["form"]] * len(e["phases"]) * (1 + 0.25 * (e["level"] - 1))
        late = e["to_disc"] in LATE or e["level"] == 4
        man.append(dict(e, weight=round(w, 2), late=late, remedy=r, cand=owner.get(e["item"], "")))
    rows = []
    for c in cands:
        mine = [m for m in man if m["cand"] == c["id"]]
        wsum = sum(m["weight"] for m in mine)
        eff = wsum * c["volume"]
        down = set().union(*(reach(m["to_task"]) for m in mine if m["weight"])) if wsum else set()
        rows.append(dict(c, n=len(mine), effort=round(eff, 1), reach=len(down),
                         late=round(sum(m["weight"] for m in mine if m["late"]) / wsum, 2) if wsum else 0,
                         systems=sorted({(m["from_sys"], m["to_sys"]) for m in mine}),
                         remedies={r: sum(1 for m in mine if m["remedy"] == r) for r in REMEDY},
                         discs=sorted({m["from_disc"] for m in mine} | {m["to_disc"] for m in mine})))
    me = max(r["effort"] for r in rows) or 1
    mr = max(r["reach"] for r in rows) or 1
    for r in rows:
        r["value"] = round(50 * r["effort"] / me + 30 * r["reach"] / mr + 20 * r["late"])
        r["ease_word"], f = EASE[r["ease"]]
        r["priority"] = round(r["value"] * f)
    rows.sort(key=lambda r: (-r["priority"], -r["value"], r["id"]))
    for k, r in enumerate(rows, 1):
        r["rank"] = k
        r["wave"] = next(w for lim, w in WAVES if k <= lim)
    return rows, man


def summary(rows, man):
    n, cov = len(man), sum(1 for m in man if m["cand"])
    read = sum(1 for m in man if m["remedy"] == "read")
    md = ["# Integration priorities\n\n",
          f"Ranked from the {n} manual hand-offs between systems in the interface register. "
          f"{cov} of them ({cov * 100 // n}%) fall in the {len(rows)} candidates below; {read} are a person reading "
          "a document to do their own work, which no integration removes. Scoring is described in "
          "`exchange/rank.py`. Ease ratings are assumptions to confirm with IT and the tool owners.\n\n",
          "| Rank | Wave | ID | Integration | Systems | Hand-offs | Value | Ease | Priority | Prerequisite |\n",
          "|---|---|---|---|---|---|---|---|---|---|\n"]
    for r in rows:
        md.append(f"| {r['rank']} | {r['wave']} | {r['id']} | {r['name']} | {r['path']} | {r['n']} | {r['value']} | "
                  f"{r['ease_word']} | {r['priority']} | {r['prerequisite']} |\n")
    md.append("\n## Candidates\n")
    for r in rows:
        md.append(f"\n### {r['rank']}. {r['id']} {r['name']} (wave {r['wave']})\n\n{r['flow']}\n\n"
                  f"- **Systems:** {r['path']}\n- **Manual hand-offs:** {r['n']} (effort {r['effort']}, "
                  f"{r['reach']} downstream tasks, {int(r['late'] * 100)}% late-stage)\n"
                  f"- **Ease:** {r['ease_word']}. {r['ease_note']}\n- **Approach:** {r['approach']}\n"
                  f"- **Prerequisite:** {r['prerequisite']}\n- **Items:** {', '.join(r['items'])}\n")
    (HERE / "out" / "integration-priorities.md").write_text("".join(md))
