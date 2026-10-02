"""Orthogonal 3D router: nozzle -> drop/rise -> rack tier -> along rack -> destination nozzle.

Critical lines (isometrics) are routed with line-specific strategies (transfer lines, OH line, pump suctions,
gravity draws); all other resolvable >= 2" lines are routed automatically at 'study' level for rack loading,
3D model and MTO. Everything is read from data/lines.json and data/layout.json at build time.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np

from . import specs
from .model import Route, key_of

ROOT = Path(__file__).resolve().parents[2]
GRADE = 100.0
T_INSTALL = 21.0
X_MAX_RACK = 216.0


def load():
    lines = json.loads((ROOT / "data" / "lines.json").read_text())
    layout = json.loads((ROOT / "data" / "layout.json").read_text())
    try:
        instr = json.loads((ROOT / "data" / "instruments.json").read_text())
    except FileNotFoundError:
        instr = []
    return lines, layout, instr


def rise(nps):
    """Crossing / loop rise above the tier: room for two LR elbows (min 1.0 m)."""
    return max(1.0, 2 * specs.elbow_A(nps) + 0.15)


def V(x, y, z):
    return np.array([x, y, z], dtype=float)


AX = {"+x": V(1, 0, 0), "-x": V(-1, 0, 0), "+y": V(0, 1, 0), "-y": V(0, -1, 0), "+z": V(0, 0, 1), "-z": V(0, 0, -1)}


def axname(v):
    i = int(np.argmax(np.abs(v)))
    return ("+" if v[i] > 0 else "-") + "xyz"[i]


# ==============================================================================================
class Plant:
    def __init__(self, layout, lines, instr):
        self.L = layout
        self.lines = lines
        self.by_no = {l["line_no"]: l for l in lines}
        self.by_key = {key_of(l["line_no"]): l for l in lines}
        self.instr = instr
        self.eq = {e["tag"]: e for e in layout["equipment"]}
        self.children = {}
        for e in layout["equipment"]:
            self.children.setdefault(e.get("parent_tag", e["tag"]), []).append(e["tag"])
        pr = layout["structures"]["pipe_rack"]
        self.rack = pr
        self.tiers = {t["level"]: t["el"] for t in pr["tiers"]}
        self.bents = pr["bents_x"]
        self.ry0, self.ry1 = pr["y0"], pr["y1"]
        self.issues = []
        self.assumed = []

    # ---------------------------------------------------------------- nozzles
    def noz(self, tag, name):
        e = self.eq[tag]
        p = V(*e["nozzles"][name])
        return p, self.noz_dir(e, name, p)

    def noz_dir(self, e, name, p):
        sh = e["shape"]
        if name in ("overhead", "stack_top"):
            return AX["+z"]
        if name in ("bottoms",):
            return AX["-z"]
        if e["type"] == "Pump":
            if name == "discharge":
                return AX["+z"]
            v = p - V(e["x"], e["y"], p[2])
            return AX[axname(v)]
        if e["type"] == "Air cooler":
            return AX["+z"] if name == "inlet" else AX["-z"]
        if e["type"] == "Ejector":
            if name == "motive_steam":
                return AX["+z"]
            v = p - V(e["x"], e["y"], p[2])
            return AX[axname(v)]
        if sh == "vcyl":
            if name in ("vapour_outlet",):
                return AX["+z"]
            if name in ("liquid_outlet",):
                return AX["-z"]
            v = p - V(e["x"], e["y"], p[2])
            if np.linalg.norm(v[:2]) < 0.05:
                return AX["-z"]
            return AX[axname(v)]
        if sh == "hcyl":
            if name in ("tube_inlet", "shell_outlet", "liquid_outlet", "water_outlet", "condensate_outlet"):
                return AX["-z"]
            return AX["+z"]
        bb = e["bbox"]
        for ax, val, s in (("y", bb[3], "+y"), ("y", bb[1], "-y"), ("x", bb[2], "+x"), ("x", bb[0], "-x")):
            c = p[1] if ax == "y" else p[0]
            if abs(c - val) < 0.06:
                return AX[s]
        return AX["+z"]

    def box(self, tag):
        e = self.eq[tag]
        bb = e["bbox"]
        top = e.get("top_el") or (e["z_base"] + e.get("height", 2.0))
        if e["shape"] == "hcyl":
            top = e["z_base"] + e.get("H", e.get("W", 1.0))
        return (bb[0], bb[1], e["z_base"], bb[2], bb[3], top)

    # ---------------------------------------------------------------- rack
    def tier_for(self, line):
        c, f, T = line["cls"], line["fluid"], line["design_T_C"]
        if f in ("LS", "MS", "HS", "CD", "BFW", "CWS", "CWR", "FG", "FL", "IA", "N", "BD", "CH"):
            return 3
        if c in ("B2", "B3") or (f == "P" and T >= 260) or line.get("flow_kg_h", 0) > 4.0e5:
            return 1
        return 2

    def zc(self, tier, nps, insul):
        return self.tiers[tier] + specs.od(nps) / 2000.0 + (0.1 if insul != "N" else 0.0)

    def zx(self, tier, nps, insul="H", above=False):
        """Rack entry/exit elevation: tier 1 lines leave BELOW the tier (no conflict with tier-1 loops),
        tier 2/3 lines leave ABOVE their tier."""
        if tier == 1 and not above:
            zc = self.zc(tier, nps, insul)
            return zc - max(2 * specs.elbow_A(nps) + 0.15, specs.od(nps) / 1000.0 + 0.65)
        return self.tiers[tier] + rise(nps) + specs.od(nps) / 2000.0

    def loop_dz(self, tier, nps):
        if tier == 2:
            return -rise(nps)
        if tier == 3:
            return rise(nps) + 0.7
        return rise(nps)

    def under_air_cooler(self, x0, x1):
        for e in self.L["equipment"]:
            if e["type"] == "Air cooler":
                if x1 > e["bbox"][0] - 0.5 and x0 < e["bbox"][2] + 0.5:
                    return True
        return False


class RackAlloc:
    """First-fit lateral slot allocation per tier with x-interval occupancy."""

    def __init__(self, plant):
        self.p = plant
        self.occ = {1: [], 2: [], 3: []}
        self.loop_bays = {1: set(), 2: set(), 3: set()}
        self.owner = []          # (tier, bay, line_no)

    def release(self, line_no):
        for t in self.occ:
            self.occ[t] = [o for o in self.occ[t] if o[4] != line_no]
        for (t, bay, ln) in [o for o in self.owner if o[2] == line_no]:
            self.loop_bays[t].discard(bay)
            if t in (1, 2):
                self.loop_bays[3 - t].discard(bay)
        self.owner = [o for o in self.owner if o[2] != line_no]

    @staticmethod
    def half(nps, insul, T):
        return specs.od(nps) / 2000.0 + specs.insul_thk(insul, T) / 1000.0

    def alloc(self, tier, x0, x1, nps, insul, T, line_no, prefer="south", fixed=None):
        x0, x1 = min(x0, x1), max(x0, x1)
        h = self.half(nps, insul, T)
        y0, y1 = self.p.ry0 + 0.25, self.p.ry1 - 0.25

        def fits(y):
            if y - h < y0 - 1e-6 or y + h > y1 + 1e-6:
                return False
            for (a0, a1, yy, hh, _) in self.occ[tier]:
                if a1 < x0 - 0.5 or a0 > x1 + 0.5:
                    continue
                if abs(y - yy) < h + hh + 0.075:
                    return False
            return True

        if fixed is not None and fits(fixed):
            y = fixed
        else:
            cands = np.arange(y0 + h, y1 - h + 1e-6, 0.025)
            if prefer == "north":
                cands = cands[::-1]
            elif prefer == "centre":
                cands = sorted(cands, key=lambda v: abs(v - 75.0))
            y = next((float(c) for c in cands if fits(c)), None)
            if y is None:
                self.p.issues.append(f"Rack tier {tier} full between x {x0:.0f}-{x1:.0f} m for {line_no} - "
                                     f"placed on overflow slot (rack widening / 4th tier needed)")
                y = float(y1 - h)
        self.occ[tier].append((x0, x1, round(y, 3), h, line_no))
        return round(y, 3)

    def tier_fill(self):
        out = {}
        for t, occ in self.occ.items():
            out[t] = occ
        return out


# ==============================================================================================
# flexibility helpers
def leg_capacity_mm(line, nps, h_m):
    mat = specs.cls(line["cls"])["mat"]
    E = specs.E_COLD[mat] * 1000.0
    D = specs.od(nps)
    return specs.Sa(mat, line["design_T_C"]) * (h_m * 1000.0) ** 2 / (3 * E * D)


def leg_required_m(line, nps, delta_mm):
    mat = specs.cls(line["cls"])["mat"]
    E = specs.E_COLD[mat] * 1000.0
    D = specs.od(nps)
    return math.sqrt(max(3 * E * D * delta_mm / specs.Sa(mat, line["design_T_C"]), 0.0)) / 1000.0


def growth_mm_per_m(line):
    return specs.expansion_mm_per_m(specs.cls(line["cls"])["mat"], line["design_T_C"])


SPAN = {2: 3.0, 3: 3.7, 4: 4.3, 6: 5.2, 8: 5.8, 10: 6.4, 12: 7.0, 14: 7.6, 16: 8.2, 18: 8.5, 20: 9.1, 24: 9.8,
        28: 10.5, 36: 11.5, 42: 12.0, 48: 12.0, 54: 12.0}


def span_for(nps):
    ks = sorted(SPAN)
    return SPAN[min(ks, key=lambda k: abs(k - nps))]


# ==============================================================================================
class Router:
    def __init__(self):
        lines, layout, instr = load()
        self.P = Plant(layout, lines, instr)
        self.rack = RackAlloc(self.P)
        self.routes: list[Route] = []
        self.unrouted = []
        self.headers = {}       # key -> dict(tier, y, zc, x0, x1, line_no)
        self.critical_keys = []

    # ------------------------------------------------------------------ utils
    def line(self, key):
        l = self.P.by_key.get(key)
        if l is None:
            self.P.issues.append(f"Line {key} not found in lines.json - route skipped")
        return l

    def instruments(self, line):
        k = key_of(line["line_no"])
        return [i for i in self.P.instr if i.get("line_no") and key_of(i["line_no"]) == k]

    def inline_tag(self, line, prefix):
        for i in self.instruments(line):
            if i["tag"].startswith(prefix):
                return i["tag"]
        return None

    def rack_run(self, route, branch_id, tier, y, zc, x0, x1):
        route.rack_runs.append(dict(branch=branch_id, tier=tier, el=self.P.tiers[tier], y=y, zc=round(zc, 3),
                                    x0=round(min(x0, x1), 3), x1=round(max(x0, x1), 3)))

    # ------------------------------------------------------------------ loops
    def loops_for_run(self, route, line, nps, y, zc, xa, xb, end_legs, tier):
        """Return list of (xl0, xl1, H, sgn) loops for rack run xa->xb and anchors x; sizes via guided cantilever."""
        L = abs(xb - xa)
        e = growth_mm_per_m(line)
        dT = line["design_T_C"] - T_INSTALL
        if dT < 60 or L < 12:
            return [], [], dict(L=L, delta=round(e * L, 1), loops=0, note="no loop - low temperature / short run")
        delta = e * L
        cap = [leg_capacity_mm(line, nps, h) for h in end_legs]
        if min(cap) >= delta / 2:
            xm = self._near_bent((xa + xb) / 2)
            return [], [xm], dict(L=round(L, 1), delta=round(delta, 1), loops=0, anchor_mid=xm,
                                  end_leg_cap=[round(c) for c in cap],
                                  note="absorbed by end legs (anchor at mid-run)")
        hmax = min(8.5, (self.P.ry1 - 0.3 - y) if y < 75 else (y - self.P.ry0 - 0.3))
        sgn = 1 if y < 75 else -1
        for n in range(1, 12):
            dl = delta / n
            H = leg_required_m(line, nps, dl / 2)
            if H <= hmax and L / n >= 18:
                break
        H = max(2.0, math.ceil(H * 2) / 2)
        if H > hmax:
            self.P.issues.append(f"{line['line_no']}: loop leg {H:.1f} m exceeds rack width - rack extension "
                                 f"or bellows required")
        lo, hi = min(xa, xb), max(xa, xb)
        loops, anchors = [], []
        for k in range(n):
            xc = lo + (k + 0.5) * L / n
            bays = [(self.P.bents[i], self.P.bents[i + 1]) for i in range(len(self.P.bents) - 1)
                    if self.P.bents[i] >= lo + 5.9 and self.P.bents[i + 1] <= hi - 5.9]
            if tier == 3:
                bays = [b for b in bays if not self.P.under_air_cooler(*b)]
            if not bays:
                continue
            bays.sort(key=lambda b: abs((b[0] + b[1]) / 2 - xc))
            used = {x for bb in self.rack.loop_bays[tier] for x in bb}
            pick = next((b for b in bays if b[0] not in used and b[1] not in used), None)
            k = 0
            if pick is None:       # nest inside an existing loop bay: narrower and higher
                def cnt(b):
                    return sum(1 for (t, bb, _ln) in self.rack.owner
                               if t in ((1, 2) if tier in (1, 2) else (3,)) and (set(bb) & set(b)))
                pick = min(bays, key=lambda b: (cnt(b), abs((b[0] + b[1]) / 2 - xc)))
                k = min(cnt(pick), 2)
            self.rack.loop_bays[tier].add(pick)
            if tier in (1, 2):
                self.rack.loop_bays[3 - tier].add(pick)
            self.rack.owner.append((tier, pick, line["line_no"]))
            loops.append((pick[0] + 0.9 * k, pick[1] - 0.9 * k, H, sgn, 0.45 * k))
        loops.sort()
        a_pts = [lo] + [(loops[i][1] + loops[i + 1][0]) / 2 for i in range(len(loops) - 1)] + [hi]
        anchors = [self._near_bent(a, inside=(lo, hi)) for a in a_pts]
        info = dict(L=round(L, 1), delta=round(delta, 1), loops=len(loops), H=H, W=6.0,
                    per_loop_mm=round(delta / max(len(loops), 1), 1), end_leg_cap=[round(c) for c in cap],
                    note=f"{len(loops)} loop(s) H={H:.1f} m x W=6.0 m, raised +1.0 m")
        return loops, anchors, info

    def _near_bent(self, x, inside=None):
        bs = self.P.bents
        if inside:
            bs = [b for b in bs if inside[0] - 1e-6 <= b <= inside[1] + 1e-6] or bs
        return min(bs, key=lambda b: abs(b - x))

    def rack_points(self, xa, xb, y, zc, loops, nps=None, tier=1):
        """Points along a rack run xa->xb incl. raised loops."""
        self._nps = nps or 2
        self._tier = tier
        pts = [V(xa, y, zc)]
        rng = sorted(loops, key=lambda l: l[0], reverse=bool(xb < xa))
        for (l0, l1, H, s, kz) in rng:
            a, b = (l0, l1) if xb > xa else (l1, l0)
            dz = self.P.loop_dz(self._tier, self._nps)
            zl = zc + dz + (kz if dz > 0 else -kz)
            pts += [V(a, y, zc), V(a, y, zl), V(a, y + s * H, zl), V(b, y + s * H, zl), V(b, y, zl), V(b, y, zc)]
        pts.append(V(xb, y, zc))
        return pts

    # ------------------------------------------------------------------ supports
    def supports(self, route):
        line = route.line
        hot = line["design_T_C"] >= 200
        n = 0
        sup = []
        seq = route.line_no.split("-")[3] if route.line_no.count("-") >= 4 else "000"
        area = line["area"]
        rr = route.rack_runs
        anchors = set()
        for lp in route.loops:
            for a in lp.get("anchors", []):
                anchors.add(round(a, 2))
        for b in route.branches:
            for i, s in enumerate(b.seg):
                p0, p1 = b.pts[i], b.pts[i + 1]
                v = p1 - p0
                horiz = abs(v[2]) < 0.2 * s
                on_rack = [r for r in rr if r["branch"] == b.id and abs(p0[2] - r["zc"]) < 0.02 and abs(p1[2] - r["zc"]) < 0.02
                           and abs(p0[1] - r["y"]) < 0.02 and abs(p1[1] - r["y"]) < 0.02]
                if horiz and on_rack:
                    lo, hi = sorted((p0[0], p1[0]))
                    loop_x = sorted({x for lp in route.loops for x in lp.get("legs", [])})
                    for bx in self.P.bents:
                        if lo + 0.3 < bx < hi - 0.3:
                            near_loop = any(abs(bx - lx) <= 6.01 for lx in loop_x)
                            if any(abs(bx - a) < 0.01 for a in anchors):
                                t = "A"
                            elif near_loop or (hot and int(bx) % 24 == 0) or (not hot and int(bx) % 36 == 0):
                                t = "G"
                            else:
                                t = "R"
                            sup.append(dict(branch=b.id, d=round(b.cum[i] + abs(bx - p0[0]), 3), type=t,
                                            pt=[round(bx, 3), round(p0[1], 3), round(p0[2], 3)], on="rack bent"))
                    continue
                if horiz:
                    sp = span_for(b.nps)
                    if b.cum[i] < 0.5 and route.level == "study" and s < sp:
                        continue
                    k = max(1, int(s // sp))
                    for j in range(1, k + 1):
                        d = b.cum[i] + min(s - 0.6, j * s / (k + 1)) if s > 1.2 else b.cum[i] + s / 2
                        if s < 1.0 and j > 0:
                            continue
                        sup.append(dict(branch=b.id, d=round(d, 3), type="R",
                                        pt=[round(c, 3) for c in b.point_at(d)], on="steel / sleeper"))
                else:
                    if s > 6.0:
                        k = int(s // 6.0)
                        for j in range(1, k + 1):
                            d = b.cum[i] + j * s / (k + 1)
                            sup.append(dict(branch=b.id, d=round(d, 3), type="G",
                                            pt=[round(c, 3) for c in b.point_at(d)], on="clip / structure"))
                    if s > 2.5 and i + 1 < len(b.seg):
                        d = b.cum[i + 1] - 0.4 if v[2] > 0 else b.cum[i] + 0.4
                        sup.append(dict(branch=b.id, d=round(d, 3), type="S" if hot else "R",
                                        pt=[round(c, 3) for c in b.point_at(d)],
                                        on="trunnion / lug" + (" - variable spring" if hot else "")))
        # spring at the first support off hot equipment (column / heater / pump nozzles)
        for b in route.branches:
            for side in ("start", "end"):
                c = b.start if side == "start" else b.end
                if c.get("kind") == "nozzle" and hot and c.get("tag", "")[:1] in "CHP":
                    near = [s for s in sup if s["branch"] == b.id and s["type"] in ("R",)]
                    if near:
                        s = min(near, key=lambda s: s["d"] if side == "start" else b.length - s["d"])
                        s["type"] = "S"
                        s["on"] += " - variable spring (equipment growth)"
        sup.sort(key=lambda s: (s["branch"], s["d"]))
        # dedupe within 0.5 m
        out = []
        for s in sup:
            if out and out[-1]["branch"] == s["branch"] and abs(out[-1]["d"] - s["d"]) < 0.5:
                if s["type"] in ("A", "S") and out[-1]["type"] not in ("A",):
                    out[-1] = s
                continue
            out.append(s)
        for s in out:
            n += 1
            s["tag"] = f"PS-{area}{seq}-{n:02d}"
        route.supports = out

    # ------------------------------------------------------------------ generic path pieces
    def escape(self, tag, p, d, toward, nps):
        """From stub point p (after nozzle) move horizontally out of the equipment footprint if needed."""
        if tag not in self.P.eq:
            return []
        x0, y0, z0, x1, y1, z1 = self.P.box(tag)
        e = self.P.eq[tag]
        m = 0.4 + specs.od(nps) / 2000.0
        inside = x0 - m < p[0] < x1 + m and y0 - m < p[1] < y1 + m
        if not inside or abs(d[2]) < 0.5:
            return []
        if e["shape"] == "vcyl":
            r = max(b[2] for b in e.get("body", [[0, 0, e.get("D", 2)]])) / 2 if p[2] > e.get("bottom_tl", 0) else \
                e.get("body", [[0, 0, e.get("D", 2)]])[0][2] / 2
            cx, cy = e["x"], e["y"]
            dy = toward[1] - cy
            dx = toward[0] - cx
            if abs(dy) >= abs(dx):
                return [V(p[0], cy + math.copysign(r + m + 0.3, dy), p[2])]
            return [V(cx + math.copysign(r + m + 0.3, dx), p[1], p[2])]
        opts = []
        for ax, edge, sg in ((1, y0 - m, -1), (1, y1 + m, 1), (0, x0 - m, -1), (0, x1 + m, 1)):
            q = p.copy()
            q[ax] = edge
            cost = abs(edge - p[ax]) + 0.2 * np.linalg.norm((q - toward)[:2])
            opts.append((cost, q))
        return [min(opts, key=lambda o: o[0])[1]]

    def stub(self, p, d, nps, length=None):
        s = length if length is not None else max(0.5, 2.5 * specs.od(nps) / 1000.0)
        if d[2] < -0.5:      # bottom nozzles: keep the elbow above grade
            s = max(0.3, min(s, p[2] - (GRADE + 0.25 + specs.od(nps) / 2000.0)))
        return p + d * s

    # ==============================================================================================
    def run(self):
        from . import critical
        critical.build_all(self)
        from . import auto
        auto.build_all(self)
        for r in self.routes:
            if not r.supports:
                self.supports(r)
            r.finalize()
        return self.routes
