"""Line properties (wall thickness, test pressure, weights), simplified flexibility checks (B31.3 eq.16,
guided cantilever), stress-critical line classification, pipe-rack loading and clash check."""
from __future__ import annotations

import json
import math
import re

import numpy as np

from . import specs
from .router import ROOT

EQ16_LIMIT = 208.3      # SI: D (mm) * y (mm) / (L - U)^2 (m^2) <= 208.3
BENT = 6.0


def line_props(l):
    w = specs.wall_calc(l["size_in"], l["design_P_barg"], l["design_T_C"], l["cls"])
    k = specs.cls(l["cls"])
    vac = is_vacuum(l)
    ext = None
    if vac and l["size_in"] >= 6:
        wall = w["wall"]
        pa, ok = specs.ext_pressure_ok(l["size_in"], wall, k["ca"], l["design_T_C"], k["mat"])
        while not ok and wall < 40:
            nxt = [t for t in specs.PLATE_WT + [specs.PIPE[specs._snap(l["size_in"])][1].get("XS", 0)] if t > wall]
            if not nxt:
                break
            wall = min(nxt)
            pa, ok = specs.ext_pressure_ok(l["size_in"], wall, k["ca"], l["design_T_C"], k["mat"])
        ext = dict(P_allow_bar=round(pa, 2), ok=ok, wall=wall)
        if wall > w["wall"]:
            names = {v: n for n, v in specs.PIPE[specs._snap(l["size_in"])][1].items()}
            w = dict(w, wall=wall, sch=("SCH " + names[wall]) if names.get(wall, "").isdigit() else
                     (names.get(wall) or f"WT {wall:.2f}"), governs="external pressure (full vacuum)")
    PT, ratio = specs.test_pressure(l["design_P_barg"], l["design_T_C"], l["cls"])
    rho = l.get("density_kg_m3") or 0.0
    wts = specs.line_weights(l["size_in"], w["wall"], l["insul"], l["design_T_C"], rho if l["phase"] != "V" else min(rho, 30))
    return dict(wall=w, sch=w["sch"], t_mm=w["wall"], PT=round(PT, 1), ST_S=round(ratio, 2), vac=vac, ext=ext,
                insul_mm=specs.insul_thk(l["insul"], l["design_T_C"]), w=wts,
                w_op=wts["steel"] + wts["content"] + wts["insul"], w_hydro=wts["steel"] + wts["water"] + wts["insul"],
                pwht=specs.pwht_text(l["cls"], w["wall"]), nde=specs.nde_text(l["cls"]), rating=k["rating"],
                mat=k["desc"])


def is_vacuum(l):
    f, t = l["from"], l["to"]
    if l["area"] != "200" or l["design_P_barg"] > 3.5:
        return False
    return bool(re.search(r"(C-201 top|H-201 outlet|H-201 pass|J-20\d)", f + " " + t)) and l["fluid"] in ("P", "PG")


# ----------------------------------------------------------------------------------------------
def terminal_move(P, conn, mech):
    """Thermal displacement (mm) of an equipment nozzle relative to its foundation."""
    if conn.get("kind") != "nozzle":
        return np.zeros(3)
    tag = conn.get("tag", "")
    e = P.eq.get(tag)
    if not e:
        return np.zeros(3)
    m = mech.get(tag) or mech.get(e.get("parent_tag", "")) or {}
    T = m.get("design_T_C") or 0
    if e["type"] in ("Column", "Drum", "Desalter") and T:
        g = specs.expansion_mm_per_m("CS", T)
        p = np.array(conn["p"])
        dz = (p[2] - e["z_base"]) * g
        r = np.array([p[0] - e["x"], p[1] - e["y"], 0.0]) * g
        return np.array([r[0], r[1], dz])
    return np.zeros(3)


def flex_check(route, P, mech):
    l = route.line
    def score(c):
        k = (c.start.get("kind") in ("nozzle", "bl", "header")) + (c.end.get("kind") in ("nozzle", "bl", "header"))
        return (k, c.length)
    b = max(route.branches, key=score)
    p0, p1 = b.pts[0], b.pts[-1]
    mat = specs.cls(l["cls"])["mat"]
    e = specs.expansion_mm_per_m(mat, l["design_T_C"])
    Lm = b.length
    U = float(np.linalg.norm(p1 - p0))
    m0 = terminal_move(P, b.start, mech)
    m1 = terminal_move(P, b.end, mech)
    yv = e * (p1 - p0) - (m1 - m0)
    y = float(np.linalg.norm(yv))
    D = specs.od(l["size_in"])
    if Lm - U < 0.05:
        ratio = float("inf") if y > 1 else 0.0
    else:
        ratio = D * y / (Lm - U) ** 2
    anchors = sum(1 for s in route.supports if s["type"] == "A")
    return dict(branch=b.id, L=round(Lm, 1), U=round(U, 1), y=round(y, 1), D=D, ratio=round(ratio, 1),
                ok=ratio <= EQ16_LIMIT, anchors=anchors,
                term=dict(start=[round(v, 1) for v in m0], end=[round(v, 1) for v in m1]),
                note="between terminal nozzles; rack anchors/loops reduce actual strain" if anchors else "")


# ----------------------------------------------------------------------------------------------
def stress_category(l, routed=None, flex=None):
    """Company practice (B31.3 319.4.1 + common refinery criteria)."""
    T, n, f, t = l["design_T_C"], l["size_in"], l["from"], l["to"]
    rot = bool(re.search(r"\bP-\d{3}|\bK-\d{3}|\bJ-\d{3}", f + " " + t))
    reasons = []
    if T > 300 and n >= 6:
        reasons.append("T > 300 C & NPS >= 6")
    if T > 200 and n >= 12:
        reasons.append("T > 200 C & NPS >= 12")
    if rot and ((n >= 4 and T >= 150) or n >= 12):
        reasons.append("rotating equipment (API 610 nozzle loads)")
    if re.search(r"H-\d{3} (outlet|inlet)", f + " " + t) or re.search(r"H-\d{3} pass", f + " " + t):
        reasons.append("fired heater terminal (API 560)")
    if is_vacuum(l) and n >= 6:
        reasons.append("vacuum / external pressure")
    if re.search(r"A-\d{3}", f + " " + t) and T > 120 and n >= 6:
        reasons.append("air cooler header (API 661 nozzle loads)")
    if n >= 24:
        reasons.append("NPS >= 24")
    if l["fluid"] == "FL" and n >= 12:
        reasons.append("flare / relief header (reaction forces)")
    if l["cls"] in ("C1", "S2") and n >= 4 and T > 200:
        reasons.append("600# class & T > 200 C")
    if flex is not None and not flex["ok"] and T > 150:
        reasons.append("fails simplified eq.(16)")
    if reasons:
        return 1, reasons
    if T > 150 or (n >= 4 and rot):
        return 2, ["T > 150 C or equipment-connected"]
    return 3, ["visual / no analysis"]


# ----------------------------------------------------------------------------------------------
def rack_loads(routes, P, props):
    bents = P.bents
    out = {t: {b: dict(op=0.0, hydro_max=0.0, lines=0, friction=0.0) for b in bents} for t in (1, 2, 3)}
    for r in routes:
        pr = props[r.line_no]
        for rr in r.rack_runs:
            nps = r.br(rr["branch"]).nps
            if nps != r.nps:
                pass
            w_op = pr["w_op"] * 9.81 / 1000.0          # kN/m
            w_hy = pr["w_hydro"] * 9.81 / 1000.0
            for i, b in enumerate(bents):
                left = bents[i - 1] if i > 0 else b
                right = bents[i + 1] if i + 1 < len(bents) else b
                a0, a1 = (left + b) / 2, (b + right) / 2
                ov = max(0.0, min(a1, rr["x1"]) - max(a0, rr["x0"]))
                if ov <= 0:
                    continue
                d = out[rr["tier"]][b]
                d["op"] += w_op * ov
                d["hydro_max"] = max(d["hydro_max"], (w_hy - w_op) * ov)
                d["lines"] += 1
                d["friction"] += 0.3 * w_op * ov
        for lp in r.loops:
            if not lp.get("legs"):
                continue
            w_op = pr["w_op"] * 9.81 / 1000.0
            extra = (2 * lp["H"] + 6.0) * w_op / 2
            for x in lp["legs"]:
                bb = min(bents, key=lambda b: abs(b - x))
                out[lp["tier"]][bb]["op"] += extra
    return out


# ----------------------------------------------------------------------------------------------
def _seg_seg_dist(p1, q1, p2, q2):
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    if a < 1e-12 and e < 1e-12:
        return float(np.linalg.norm(r))
    if a < 1e-12:
        s, t = 0.0, min(max(f / e, 0), 1)
    else:
        c = d1 @ r
        if e < 1e-12:
            t, s = 0.0, min(max(-c / a, 0), 1)
        else:
            b = d1 @ d2
            den = a * e - b * b
            s = min(max((b * f - c * e) / den, 0), 1) if den > 1e-12 else 0.0
            t = (b * s + f) / e
            if t < 0:
                t, s = 0.0, min(max(-c / a, 0), 1)
            elif t > 1:
                t, s = 1.0, min(max((b - c) / a, 0), 1)
    return float(np.linalg.norm((p1 + d1 * s) - (p2 + d2 * t)))


def _seg_box(p, q, lo, hi):
    d = q - p
    t0, t1 = 0.0, 1.0
    for i in range(3):
        if abs(d[i]) < 1e-12:
            if p[i] < lo[i] or p[i] > hi[i]:
                return False
        else:
            a, b = (lo[i] - p[i]) / d[i], (hi[i] - p[i]) / d[i]
            a, b = min(a, b), max(a, b)
            t0, t1 = max(t0, a), min(t1, b)
            if t0 > t1:
                return False
    return True


def equipment_solids(P):
    sol = []
    for e in P.L["equipment"]:
        tag = e["tag"]
        if e["shape"] == "vcyl":
            body = e.get("body") or [[e.get("bottom_tl", e["z_base"]), e.get("top_tl", e["top_el"]), e["D"]]]
            sol.append(("cyl", tag, e["x"], e["y"], e["z_base"], body[0][0], body[0][2] / 2))
            for z0, z1, D in body:
                sol.append(("cyl", tag, e["x"], e["y"], z0, z1, D / 2))
        elif e["shape"] == "heater":
            bb = e["bbox"]
            rz1 = e.get("radiant", {}).get("z1", e["z_base"] + 15)
            sol.append(("box", tag, (bb[0], bb[1], e["z_base"]), (bb[2], bb[3], rz1)))
        else:
            bb = e["bbox"]
            h = e.get("height") or e.get("H") or 2.0
            sol.append(("box", tag, (bb[0], bb[1], e["z_base"]), (bb[2], bb[3], e["z_base"] + h)))
    return sol


def clash_check(routes, P):
    sol = equipment_solids(P)
    segs = []
    for r in routes:
        for b in r.branches:
            ends = {b.start.get("tag"), b.end.get("tag")}
            hdr = {c.get("ref") for c in (b.start, b.end) if c.get("kind") == "header"}
            for i in range(len(b.pts) - 1):
                p, q = b.pts[i], b.pts[i + 1]
                rad = specs.od(r._nps_at(b, (b.cum[i] + b.cum[i + 1]) / 2)) / 2000.0
                near_end = i <= 1 or i >= len(b.pts) - 3
                segs.append((r, b, i, p, q, rad, ends if near_end else set(), hdr if near_end else set()))
    eq_cl = []
    for (r, b, i, p, q, rad, ends, _h) in segs:
        for s in sol:
            if s[1] in ends or s[1].split("-B")[0] in {str(t).split("-B")[0] for t in ends if t}:
                continue
            if s[0] == "box":
                lo = np.array(s[2]) - rad - 0.02
                hi = np.array(s[3]) + rad + 0.02
                if _seg_box(p, q, lo, hi):
                    eq_cl.append((r.line_no, r.level, s[1]))
            else:
                _, tag, x, y, z0, z1, R = s
                d = _seg_seg_dist(p, q, np.array([x, y, z0]), np.array([x, y, z1]))
                if d < R + rad + 0.02:
                    eq_cl.append((r.line_no, r.level, tag))
    eq_cl = sorted(set(eq_cl))
    # pipe-pipe via grid hash
    cell = 6.0
    grid = {}
    for k, (r, b, i, p, q, rad, _, _h) in enumerate(segs):
        lo = np.minimum(p, q) - rad
        hi = np.maximum(p, q) + rad
        for gx in range(int(lo[0] // cell), int(hi[0] // cell) + 1):
            for gy in range(int(lo[1] // cell), int(hi[1] // cell) + 1):
                grid.setdefault((gx, gy), []).append(k)
    pp = set()
    for ks in grid.values():
        for a in range(len(ks)):
            for c in range(a + 1, len(ks)):
                i1, i2 = ks[a], ks[c]
                s1, s2 = segs[i1], segs[i2]
                if s1[0] is s2[0] or s2[0].line_no in s1[7] or s1[0].line_no in s2[7]:
                    continue
                lo1, hi1 = np.minimum(s1[3], s1[4]) - s1[5], np.maximum(s1[3], s1[4]) + s1[5]
                lo2, hi2 = np.minimum(s2[3], s2[4]) - s2[5], np.maximum(s2[3], s2[4]) + s2[5]
                if np.any(hi1 < lo2) or np.any(hi2 < lo1):
                    continue
                d = _seg_seg_dist(s1[3], s1[4], s2[3], s2[4])
                if d < s1[5] + s2[5] + 0.025:
                    a_, b_ = sorted((s1[0].line_no, s2[0].line_no))
                    lv = "critical" if "critical" in (s1[0].level, s2[0].level) else "study"
                    pp.add((a_, b_, lv))
    return eq_cl, sorted(pp)


def mech_items():
    try:
        return json.loads((ROOT / "data" / "mech.json").read_text())["items"]
    except Exception:
        return {}
