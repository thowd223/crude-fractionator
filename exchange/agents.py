"""Rank AI agent opportunities from the register.

    python exchange/agents.py --check [CODE]   # validate ai/*.json (one discipline or all), writes nothing

agents.json is the agent catalog; ai/<CODE>.json assigns every task of a discipline to the agents that could take
part of its work (see SPEC.md, "AI agent assignments"). Scoring:

Task weight      phases the task works in x (1 + 0.1 x (inputs + items produced))   recurring effort proxy
Share            1 small (about 10% of the task), 2 moderate (about 30%), 3 large (about 55%)
Agent value      60 x work relieved / largest       sum of task weight x share over its tasks
(0-100)        + 25 x hand-offs touched / largest  manual, review and meeting inputs of its tasks
               + 15 x disciplines served / all
Priority         value x readiness (ready now 1.0, needs a prerequisite 0.75, needs write access 0.5)
Waves            ranks 1-5, 6-12, the rest
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARE = {1: 0.10, 2: 0.30, 3: 0.55}
READY = {3: ("ready now", 1.0), 2: ("needs a prerequisite", 0.75), 1: ("needs write access", 0.5)}
RISKS = ("normal", "safety", "sealed", "commercial")
WAVES = ((5, 1), (12, 2), (10 ** 6, 3))
TOUCH = ("manual", "review", "meeting")
BEYOND = ("extract", "review", "answer", "check")   # patterns that act on documents a person would only read


def catalog():
    return json.loads((HERE / "agents.json").read_text())


def load():
    out, errs = {}, []
    for p in sorted((HERE / "ai").glob("*.json")):
        try:
            d = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            errs.append(f"{p.name}: {e}")
            continue
        for a in d.get("tasks", []):
            if a.get("task") in out:
                errs.append(f"{p.name}: {a.get('task')} assigned twice")
            out[a.get("task")] = dict(a, file=p.stem)
    return out, errs


def check(tasks, only=None):
    cat = catalog()
    ag = {a["id"]: a for a in cat["agents"]}
    asg, errs = load()
    for code in sorted({t["disc"] for t in tasks.values()}):
        if only and code != only:
            continue
        mine = [t for t in tasks.values() if t["disc"] == code]
        if not (HERE / "ai" / f"{code}.json").exists():
            errs.append(f"{code}: ai/{code}.json missing")
            continue
        for t in mine:
            if t["id"] not in asg:
                errs.append(f"{code}: task {t['id']} not in ai/{code}.json")
    for tid, a in asg.items():
        if only and not tid.startswith(only + "-"):
            continue
        if tid not in tasks:
            errs.append(f"{a['file']}: unknown task {tid}")
            continue
        if a.get("risk") not in RISKS:
            errs.append(f"{tid}: risk must be one of {RISKS}")
        if a.get("agents") and not a.get("keeps"):
            errs.append(f"{tid}: 'keeps' (what the person keeps) is required when agents are assigned")
        if len(a.get("agents", [])) > 3:
            errs.append(f"{tid}: at most 3 agents")
        seen = set()
        for x in a.get("agents", []):
            g = ag.get(x.get("agent"))
            if not g:
                errs.append(f"{tid}: unknown agent {x.get('agent')}")
                continue
            if x["agent"] in seen:
                errs.append(f"{tid}: {x['agent']} listed twice")
            seen.add(x["agent"])
            if x.get("pattern") not in g["patterns"]:
                errs.append(f"{tid}: {x['agent']} pattern must be one of {g['patterns']}")
            if x.get("share") not in SHARE:
                errs.append(f"{tid}: {x['agent']} share must be 1, 2 or 3")
            if x.get("autonomy") not in (1, 2, 3) or x.get("autonomy", 9) > g["autonomy_max"]:
                errs.append(f"{tid}: {x['agent']} autonomy must be 1..{g['autonomy_max']}")
            if a.get("risk") == "safety" and x.get("autonomy", 0) > 2:
                errs.append(f"{tid}: safety task, autonomy must be 2 or less")
            if not x.get("does"):
                errs.append(f"{tid}: {x['agent']} needs 'does'")
    return errs


def weight(t, produced):
    return len(t["phases"]) * (1 + 0.1 * (len(t.get("consumes", [])) + produced))


def rank(tasks, items, ex, man=()):
    cat = catalog()
    asg, _ = load()
    made = Counter(i["owner_task"] for i in items.values())
    W = {t: weight(tasks[t], made[t]) for t in tasks}
    ins = defaultdict(list)
    for e in ex:
        ins[e["to_task"]].append(e)
    rows, total_relief = [], 0
    for g in cat["agents"]:
        uses = [(tid, x) for tid, a in asg.items() if tid in tasks for x in a.get("agents", []) if x["agent"] == g["id"]]
        relief = sum(W[tid] * SHARE[x["share"]] for tid, x in uses)
        touched = {(e["item"], e["to_task"]) for tid, _ in uses for e in ins[tid] if e["method"] in TOUCH}
        beyond = {(m["item"], m["to_task"]) for m in man if m["remedy"] in ("read", "extract")
                  for tid, x in uses if m["to_task"] == tid and x["pattern"] in BEYOND}
        discs = sorted({tasks[tid]["disc"] for tid, _ in uses})
        rows.append(dict(g, tasks=[dict(task=tid, name=tasks[tid]["name"], disc=tasks[tid]["disc"], **x,
                                        risk=asg[tid].get("risk", ""), keeps=asg[tid].get("keeps", ""))
                                   for tid, x in sorted(uses)],
                         n=len(uses), relief=round(relief, 1), touched=len(touched), beyond=len(beyond), discs=discs,
                         autonomy=dict(Counter(x["autonomy"] for _, x in uses)),
                         safety=sum(1 for tid, _ in uses if asg[tid].get("risk") in ("safety", "sealed"))))
        total_relief += relief
    mr = max(r["relief"] for r in rows) or 1
    mt = max(r["touched"] for r in rows) or 1
    nd = len({t["disc"] for t in tasks.values()})
    for r in rows:
        r["value"] = round(60 * r["relief"] / mr + 25 * r["touched"] / mt + 15 * len(r["discs"]) / nd)
        r["ready_word"], f = READY[r["readiness"]]
        r["priority"] = round(r["value"] * f)
    rows.sort(key=lambda r: (-r["priority"], -r["value"], r["id"]))
    for k, r in enumerate(rows, 1):
        r["rank"] = k
        r["wave"] = next(w for lim, w in WAVES if k <= lim)
    # share of each discipline's task weight agents could take (an agent's shares on one task are capped at 80%)
    disc = defaultdict(lambda: [0.0, 0.0, 0, 0])
    for tid, t in tasks.items():
        a = asg.get(tid, {})
        s = min(0.8, sum(SHARE[x["share"]] for x in a.get("agents", [])))
        d = disc[t["disc"]]
        d[0] += W[tid]
        d[1] += W[tid] * s
        d[2] += 1
        d[3] += 1 if a.get("agents") else 0
    by_disc = {c: dict(weight=round(v[0], 1), relief=round(v[1], 1), share=round(v[1] / v[0], 2), tasks=v[2],
                       with_agent=v[3]) for c, v in disc.items()}
    return rows, by_disc


def summary(rows, by_disc, disc_names):
    tw = sum(v["weight"] for v in by_disc.values())
    tr = sum(v["relief"] for v in by_disc.values())
    nt = sum(v["tasks"] for v in by_disc.values())
    na = sum(v["with_agent"] for v in by_disc.values())
    md = ["# AI agent opportunities\n\n",
          f"{na} of {nt} tasks have work an agent could take on. Weighted by recurring effort, agents could take about "
          f"{round(100 * tr / tw)}% of the task work, with people keeping every judgement, approval and signature. "
          "Scoring is described in `exchange/agents.py`; readiness and shares are assumptions to confirm.\n\n",
          "| Rank | Wave | ID | Agent | Does | Tasks | Disciplines | Value | Readiness | Priority | Prerequisite |\n",
          "|---|---|---|---|---|---|---|---|---|---|---|\n"]
    for r in rows:
        md.append(f"| {r['rank']} | {r['wave']} | {r['id']} | {r['name']} | {', '.join(r['patterns'])} | {r['n']} | "
                  f"{len(r['discs'])} | {r['value']} | {r['ready_word']} | {r['priority']} | {r['prerequisite']} |\n")
    md.append("\n## By discipline\n\n| Discipline | Tasks | With an agent | Share of work agents could take |\n"
              "|---|---|---|---|\n")
    for c, v in by_disc.items():
        md.append(f"| {c} {disc_names[c]} | {v['tasks']} | {v['with_agent']} | {round(100 * v['share'])}% |\n")
    md.append("\n## Agents\n")
    for r in rows:
        md.append(f"\n### {r['rank']}. {r['id']} {r['name']} (wave {r['wave']})\n\n{r['what']}\n\n"
                  f"- **Reads:** {', '.join(r['reads'])}. **Writes:** {', '.join(r['writes'])}\n"
                  f"- **Highest autonomy:** {r['autonomy_max']}. **Person:** {r['human']}\n"
                  f"- **Guardrails:** {r['guardrails']}\n- **Readiness:** {r['ready_word']}. {r['readiness_note']}\n"
                  f"- **Prerequisite:** {r['prerequisite']}\n"
                  f"- **Work:** {r['n']} tasks in {', '.join(r['discs'])}; {r['touched']} manual, review or meeting "
                  f"hand-offs touched; {r['beyond']} hand-offs no integration removes\n")
        for x in r["tasks"]:
            md.append(f"  - {x['task']} {x['name']}: {x['does']} ({x['pattern']}, share {x['share']}, "
                      f"autonomy {x['autonomy']})\n")
    (HERE / "out" / "ai-agent-opportunities.md").write_text("".join(md))


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    import build
    args = [a for a in sys.argv[1:] if a != "--check"]
    if "--check" not in sys.argv or any(a not in build.DISC for a in args):
        print(__doc__)
        sys.exit(2)
    tasks, items, _ = build.load()
    errs = check(tasks, args[0] if args else None)
    print(f"{len(errs)} errors")
    for s in errs:
        print("  ERROR", s)
    sys.exit(1 if errs else 0)
