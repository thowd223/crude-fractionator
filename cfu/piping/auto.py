"""Automatic study-level routing of all other resolvable lines (>= 2") + unit headers on the rack."""
from __future__ import annotations

import json
import re

import numpy as np

from . import specs
from .model import Route, key_of
from .router import ROOT, V, AX

TAG_RE = re.compile(r"\b([ACDEHJKPX]-\d{3})([A-D])?(?:/([A-D]))?(?:-B\d)?")
OSBL_WORDS = ("OSBL", "TK ", "Storage", "Slop", "WWT", "SWS", "FCC", "Hydrocracker", "Isomerisation", "NHT",
              "LPG treating", "Fuel gas", "Condensate recovery", "coker", "KHT", "DHT", "Blowdown drum", "Flare (OSBL)")
LOCAL_Z = {"NS": 104.0, "EW": 105.4}
VAR = dict(dzx=0.0, dzl=0.0, stub=0.0, jog=0.0, up=False)
VARIANTS = [dict(dzx=0.0, dzl=0.0, stub=0.0, jog=0.0), dict(dzx=0.0, dzl=0.0, stub=0.9, jog=0.0),
            dict(dzx=0.0, dzl=0.0, stub=0.0, jog=1.3), dict(dzx=0.0, dzl=0.0, stub=0.0, jog=-1.3),
            dict(dzx=0.5, dzl=1.0, stub=0.0, jog=0.0), dict(dzx=0.0, dzl=-0.9, stub=0.5, jog=2.4),
            dict(dzx=0.9, dzl=2.0, stub=1.5, jog=-2.4), dict(dzx=0.3, dzl=2.8, stub=2.2, jog=0.0),
            dict(dzx=0.6, dzl=1.4, stub=0.5, jog=3.5), dict(dzx=0.0, dzl=0.0, stub=0.0, jog=0.0, up=True),
            dict(dzx=0.0, dzl=0.7, stub=0.6, jog=1.3, up=True), dict(dzx=0.4, dzl=-0.6, stub=0.0, jog=-1.3, up=True)]
for _v in VARIANTS:
    _v.setdefault("up", False)


def header_code(text):
    t = text.lower()
    if "closed drain" in t or "drains" in t:
        return "BD"
    if "header" not in t:
        return None
    for k, c in (("hp steam", "HS"), ("mp steam", "MS"), ("mp header", "MS"), ("lp steam", "LS"), ("lp header", "LS"),
                 ("stripping steam", "LS"), ("condensate", "CD"), ("bfw", "BFW"), ("cws", "CWS"), ("cwr", "CWR"),
                 ("fg header", "FG"), ("flare", "FL"), ("ia header", "IA"), ("n2", "N")):
        if k in t:
            return c
    return None


def is_header_line(l):
    f, t = l["from"], l["to"]
    if l["area"] != "900":
        return None
    if "OSBL" in f and "header" in t.lower():
        return l["fluid"]
    if "header" in f.lower() and "OSBL" in t:
        return l["fluid"]
    if f.startswith("Unit relief"):
        return "FL"
    if l["fluid"] == "FG" and f.startswith("D-103"):
        return "FG"
    return None


class Resolver:
    def __init__(self, R):
        self.R = R
        self.P = R.P
        self.psv = {p["tag"]: p for p in json.loads((ROOT / "data" / "psv.json").read_text())}
        self.steam_heated = set()
        for l in self.P.lines:
            if l["fluid"] in ("LS", "MS", "HS") and "header" in l["from"].lower():
                m = TAG_RE.search(l["to"])
                if m and m.group(1).startswith("E-"):
                    self.steam_heated.add(m.group(1))
        self.used = {}

    def eq_tags(self, base, sfx, sfx2):
        P = self.P
        if base + (sfx or "") in P.eq:
            tags = [base + (sfx or "")]
            if sfx2 and base + sfx2 in P.eq:
                tags.append(base + sfx2)
            return tags
        kids = sorted(P.children.get(base, []))
        if kids:
            return [kids[0]]
        if base + "A" in P.eq:
            return [base + "A"]
        return []

    def port(self, tag, name, label=None, nps=None):
        p, d = self.P.noz(tag, name)
        key = (tag, name)
        if key in self.used and self.used[key] != getattr(self, "_cur", None):
            # nozzle already taken by another (critical) line: assume a separate nozzle offset 1.2 m
            off = V(1.2, 0, 0) if abs(d[0]) < 0.5 else V(0, 1.2, 0)
            p = p + off
            name = name + "_2"
            msg = f"{tag} nozzle '{key[1]}' shared by {self.used[key]} and {getattr(self, '_cur', '?')} - separate nozzle assumed"
            if msg not in self.P.assumed:
                self.P.assumed.append(msg)
        return dict(kind="nozzle", tag=tag, nozzle=name, p=p, dir=d, label=label or f"{tag} {name}", nps=nps)

    def resolve(self, text, role, line):
        P = self.P
        t = text.strip()
        if t.startswith("PSV-"):
            return self.psv_port(t.split()[0], line)
        hc = header_code(t)
        if hc:
            return [dict(kind="header", code=hc, label=t)]
        if any(w in t for w in OSBL_WORDS) and not TAG_RE.search(t):
            return [dict(kind="bl", label=t)]
        m = TAG_RE.search(t)
        if not m:
            return None
        base, s1, s2 = m.group(1), m.group(2), m.group(3)
        tags = self.eq_tags(base, s1, s2)
        if not tags:
            return None
        e = P.eq[tags[0]]
        typ = e["type"]
        low = t.lower()
        try:
            if typ == "Pump":
                return [self.port(tg, "discharge" if role == "from" else "suction", f"{tg} "
                                  f"{'DISCHARGE' if role == 'from' else 'SUCTION'}") for tg in tags]
            if typ == "Column":
                return [self.port(tags[0], self.col_nozzle(e, low, role, line))]
            if typ in ("Drum", "Desalter"):
                return [self.port(tags[0], self.drum_nozzle(e, low, role, line))]
            if typ == "Shell & tube":
                return [self.port(tags[0], self.hx_nozzle(e, low, role, line))]
            if typ == "Air cooler":
                return [self.port(tags[0], "inlet" if role == "to" else "outlet")]
            if typ == "Fired heater":
                if "pass" in low or "coil" in low or "header box" in low or "firebox" in low:
                    return None
                if "inlet" in low:
                    return [self.port(tags[0], "inlet")]
                if "outlet" in low:
                    return [self.port(tags[0], "outlet")]
                if "burner" in low or "pilot" in low or "dbb" in low or "off-gas" in low:
                    return [self.port(tags[0], "fuel_gas")]
                return None
            if typ == "Ejector":
                nm = "motive_steam" if line["fluid"] in ("MS", "LS", "HS") else ("suction" if role == "to" else "discharge")
                return [self.port(tg, nm) for tg in tags]
            if typ == "Package":
                return [self.port(tags[0], "discharge")]
        except KeyError:
            return None
        return None

    def col_nozzle(self, e, low, role, line):
        nz = e["nozzles"]
        if "top" in low or "overhead" in low:
            if "spray" in low and "lvgo_pa_return" in nz:
                return "lvgo_pa_return"
            return "overhead"
        if "flash zone" in low:
            return "feed"
        for k, n in (("lvgo", "lvgo_draw"), ("hvgo pan", "hvgo_draw"), ("slop-wax", "slop_wax_draw"),
                     ("bed 3", "hvgo_pa_return"), ("wash bed", "wash_oil_return"),
                     ("below stripping", "stripping_steam")):
            if k in low and n in nz:
                return n
        if "boot" in low:
            return "quench_return" if role == "to" and "quench_return" in nz else "bottoms"
        if "bottom" in low:
            if role == "from" and line["to"].startswith("E-") and "reboiler_draw" in nz:
                return "reboiler_draw"
            if role == "to" and "reboiler_return" in nz and "below" in low:
                return "reboiler_return"
            return "bottoms" if role == "from" or "stripping_steam" not in nz else "stripping_steam"
        m = re.search(r"tray (\d+)", low)
        if m and "tray_el" in e:
            z = e["tray_el"].get(m.group(1))
            if "below" in low:
                for n in ("reboiler_return", "stripping_steam"):
                    if n in nz:
                        return n
            if z is not None:
                cands = {k: v for k, v in nz.items() if k not in ("overhead", "bottoms")}
                pref = [k for k in cands if (("draw" in k) if role == "from" else ("return" in k or "feed" in k))]
                pool = pref or list(cands)
                return min(pool, key=lambda k: abs(cands[k][2] - z))
        if m:
            for n in ("feed", "reflux_return"):
                if n in nz:
                    return "reflux_return" if m.group(1) == "1" and "reflux_return" in nz else n
        if "steam" in line["fluid"].lower() or line["fluid"] in ("LS", "MS"):
            return "stripping_steam"
        if role == "to":
            return "feed" if "feed" in nz else "vapour_return"
        return "vapour_return" if line["phase"] == "V" and "vapour_return" in nz else "bottoms"

    def drum_nozzle(self, e, low, role, line):
        nz = e["nozzles"]
        if role == "to":
            if "mud" in low and "mud_wash" in nz:
                return "mud_wash"
            return "inlet"
        if "boot" in low or line["fluid"] in ("SW", "WW"):
            return "water_outlet" if "water_outlet" in nz else ("brine_outlet" if "brine_outlet" in nz else "liquid_outlet")
        if "bottoms" in low and "brine_outlet" in nz:
            return "brine_outlet"
        if line["phase"] == "V" or line["fluid"] in ("PG", "FG"):
            return "vapour_outlet" if "vapour_outlet" in nz else "outlet"
        return "liquid_outlet" if "liquid_outlet" in nz else "outlet"

    def hx_nozzle(self, e, low, role, line):
        f = line["fluid"]
        tube = f in ("CWS", "CWR") or line.get("flow_kg_h", 0) > 4.0e5
        if f in ("LS", "MS", "HS", "BFW"):
            tube = False
        elif e.get("parent_tag", e["tag"]) in self.steam_heated:
            tube = True            # process side of a steam-heated reboiler / heater on the tube side
        if f == "CD":
            return "shell_outlet"
        if role == "from" and line["phase"] == "V":
            return "tube_outlet" if tube else "shell_inlet"
        if tube:
            return "tube_inlet" if role == "to" else "tube_outlet"
        return "shell_inlet" if role == "to" else "shell_outlet"

    def psv_port(self, tag, line):
        P = self.P
        ps = self.psv.get(tag)
        if not ps:
            return None
        eqt = ps["protects"].split("/")[0].strip()
        tags = self.eq_tags(*TAG_RE.search(eqt).groups()) if TAG_RE.search(eqt) else []
        if not tags:
            return None
        e = P.eq[tags[0]]
        sgn = -1.0 if e["y"] > 75 else 1.0
        if e["shape"] == "vcyl":
            R = max(b[2] for b in e.get("body", [[0, 0, e.get("D", 2)]])) / 2
            p = V(e["x"] + 0.5 * R + 1.5, e["y"] + sgn * (R + 1.2), e.get("top_tl", e["top_el"]) - 0.3)
        else:
            p = V(e["x"] + 1.0, e["y"] + sgn * (e.get("W", 2) / 2 + 1.0), e["z_base"] + e.get("height", e.get("H", 2)) + 1.0)
        P.assumed.append(f"{tag} outlet assumed at {tags[0]} ({p[0]:.1f}, {p[1]:.1f}, EL {p[2]:.2f}) - relief line "
                         f"routed self-draining to flare header")
        return [dict(kind="nozzle", tag=tag, nozzle="outlet", p=p, dir=V(0, sgn, 0), label=f"{tag} OUTLET ({tags[0]})",
                     nps=line["size_in"])]


# ==============================================================================================
def route_headers(R):
    res = Resolver(R)
    R.resolver = res
    P = R.P
    heads = [(l, is_header_line(l)) for l in P.lines]
    heads = [(l, c) for l, c in heads if c]
    # consumer extents
    ext = {}
    for l in P.lines:
        for role in ("from", "to"):
            hc = header_code(l[role])
            if hc:
                other = l["to" if role == "from" else "from"]
                ps = res.resolve(other, "to" if role == "from" else "from", l)
                if ps and ps[0]["kind"] == "nozzle":
                    ext.setdefault(hc, []).append(ps[0]["p"][0])
    order = sorted(heads, key=lambda lc: -lc[0]["size_in"])
    pref = ["south", "north"]
    for k, (l, code) in enumerate(order):
        xs = ext.get(code, [])
        if code == "BD":
            R.unrouted.append((l["line_no"], "closed drain header - underground (by civil/UG piping)"))
            continue
        r = Route(l, "header")
        nps = l["size_in"]
        tier = 3
        zc = P.zc(tier, nps, l["insul"])
        zx = P.zx(tier, nps, l["insul"])
        if code == "FG":
            src = res.port("D-103", "vapour_outlet", "D-103 FG KO DRUM OUTLET")
            xs2 = xs + [src["p"][0]]
            x_lo, x_hi = min(xs2) - 2, max(xs2) + 2
            y = R.rack.alloc(tier, x_lo, x_hi, nps, l["insul"], l["design_T_C"], l["line_no"], pref[k % 2])
            s = src["p"]
            pts = [s, V(s[0], s[1], zx), V(s[0], y, zx), V(s[0], y, zc), V(x_lo, y, zc)]
            r.add_branch("MAIN", nps, pts, dict(kind="nozzle", tag="D-103", nozzle="vapour_outlet", nps=nps,
                                                label=src["label"], p=s.tolist(), dir=[0, 0, 1]),
                         dict(kind="cap", label="END CAP"))
            if x_hi > s[0] + 1:
                r.add_branch("EAST", nps, [V(s[0], y, zc), V(x_hi, y, zc)], dict(kind="tee"), dict(kind="cap"),
                             parent="MAIN")
            R.rack_run(r, "MAIN", tier, y, zc, x_lo, x_hi)
        elif code == "FL":
            d104 = res.port("D-104", "inlet", "D-104 FLARE KO DRUM INLET")
            xin = d104["p"][0]
            fl_x = [x for x in xs] or [xin]
            x_hi = min(max(fl_x + [xin]) + 3, 214)
            x_lo = max(min(fl_x + [xin]) - 3, 1.0)
            y = R.rack.alloc(tier, x_lo, x_hi, nps, l["insul"], l["design_T_C"], l["line_no"], pref[k % 2])
            zfl = zx + 0.6
            p = d104["p"]
            r.add_branch("MAIN", nps, [V(x_lo, y, zc), V(x_hi, y, zc)], dict(kind="cap", label="WEST END CAP"),
                         dict(kind="cap", label="EAST END CAP"))
            r.add_branch("KO", nps, [V(xin, y, zc), V(xin, y, zfl), V(xin, p[1], zfl), V(*p)], dict(kind="tee"),
                         dict(kind="nozzle", tag="D-104", nozzle="inlet", nps=nps, label=d104["label"], p=p.tolist(),
                              dir=[0, 0, 1]), parent="MAIN")
            r.slope.append(dict(branch="MAIN", ratio="1:500", note="FLARE HEADER FALLS TO D-104 TEE"))
            R.rack_run(r, "MAIN", tier, y, zc, x_lo, x_hi)
        else:
            x_hi = min(max(xs) + 3, 214) if xs else 200.0
            y = R.rack.alloc(tier, 0.0, x_hi, nps, l["insul"], l["design_T_C"], l["line_no"], pref[k % 2])
            hot = l["design_T_C"] > 120
            lp, anchors, info = ([], [], {})
            if hot:
                lp, anchors, info = R.loops_for_run(r, l, nps, y, zc, 0.0, x_hi, [30.0, 30.0], tier)
            pts = R.rack_points(0.0, x_hi, y, zc, lp, nps, tier)
            out = "OSBL" in l["to"]
            if out:
                pts = pts[::-1]
            st = dict(kind="bl", label=f"BATTERY LIMIT ({l['from'] if not out else l['to']})")
            en = dict(kind="cap", label="END CAP")
            r.add_branch("MAIN", nps, pts, en if out else st, st if out else en)
            R.rack_run(r, "MAIN", tier, y, zc, 0.0, x_hi)
            r.loops.append(dict(branch="MAIN", tier=tier, y=y, legs=[x for q in lp for x in q[:2]],
                                H=(lp[0][2] if lp else 0.0), anchors=anchors, info=info))
            x_lo = 0.0
        R.headers[code] = dict(y=y, zc=round(zc, 3), tier=tier, line_no=l["line_no"], route=r, x0=x_lo, x1=x_hi)
        R.routes.append(r)


# ==============================================================================================
def _segs(routes):
    out = []
    for r in routes:
        for b in r.branches:
            for i in range(len(b.pts) - 1):
                out.append((r.line_no, b.pts[i], b.pts[i + 1], specs.od(b.nps) / 2000.0 + specs.insul_thk(r.line["insul"], r.line["design_T_C"]) / 1000.0))
    return out


def _undo_olets(r):
    hr = getattr(r, "_hdr_route", None)
    if hr is not None:
        hr.items = [it for it in hr.items if it.get("note") != f"branch {r.line_no}"]


def n_clash(r, protect):
    from .stress import _seg_seg_dist
    n = 0
    hdr = getattr(r, "_hdr_line", None)
    for b in r.branches:
        for i in range(len(b.pts) - 1):
            p, q = b.pts[i], b.pts[i + 1]
            rad = specs.od(b.nps) / 2000.0
            lo, hi = np.minimum(p, q) - rad - 1.5, np.maximum(p, q) + rad + 1.5
            for (ln, a, c, ra) in protect:
                if ln == hdr:
                    continue
                if np.any(np.maximum(a, c) < lo) or np.any(np.minimum(a, c) > hi):
                    continue
                if _seg_seg_dist(p, q, a, c) < rad + ra + 0.05:
                    n += 1
    return n


def build_all(R):
    res = getattr(R, "resolver", None) or Resolver(R)
    P = R.P
    protect = _segs([r for r in R.routes if r.level == "critical"])
    for r in R.routes:
        for b in r.branches:
            for c in (b.start, b.end):
                if c.get("kind") == "nozzle" and c.get("tag") in P.eq:
                    res.used[(c["tag"], c["nozzle"])] = r.line_no
    done = set(R.critical_keys) | {key_of(r.line_no) for r in R.routes}
    for l in P.lines:
        k = key_of(l["line_no"])
        if k in done:
            continue
        if l["size_in"] < 2:
            R.unrouted.append((l["line_no"], "small bore (< 2\") - field routed"))
            continue
        res._cur = l["line_no"]
        a = res.resolve(l["from"], "from", l)
        b = res.resolve(l["to"], "to", l)
        if not a or not b:
            what = l["from"] if not a else l["to"]
            R.unrouted.append((l["line_no"], f"endpoint '{what}' not a located nozzle/header (P&ID tie-in to another "
                                             f"line or heater coil) - detailed design"))
            continue
        if any(p["kind"] == "header" and p["code"] not in R.headers for p in a + b):
            R.unrouted.append((l["line_no"], "header not routed (underground / virtual)"))
            continue
        best = None
        for var in VARIANTS:
            VAR.update(var)
            R.rack.release(l["line_no"])
            try:
                r = auto_route(R, l, a, b)
            except Exception as ex:  # robust study routing - report and continue
                best = best or ex
                continue
            n = n_clash(r, protect)
            if best is None or isinstance(best, Exception) or n < best[0]:
                if best is not None and not isinstance(best, Exception):
                    _undo_olets(best[1])
                best = (n, r, dict(var))
            else:
                _undo_olets(r)
            if n == 0:
                break
        VAR.update(VARIANTS[0])
        if best is None or isinstance(best, Exception):
            R.unrouted.append((l["line_no"], f"auto-route failed: {best}"))
            continue
        n, r, var = best
        if var != VARIANTS[-1] or n == 0:
            # re-run chosen variant so rack allocation matches the kept geometry
            R.rack.release(l["line_no"])
            _undo_olets(r)
            VAR.update(var)
            r = auto_route(R, l, a, b)
            VAR.update(VARIANTS[0])
        r.clash_variant = var
        R.routes.append(r)


def _stub_chain(R, port, nps, toward):
    p = V(*port["p"])
    d = V(*port["dir"])
    s = R.stub(p, d, nps, max(0.5, 2.5 * specs.od(nps) / 1000.0) + VAR["stub"])
    pts = [p, s]
    pts += R.escape(port["tag"], s, d, toward, nps) if port["tag"] in R.P.eq else []
    if VAR["jog"]:
        q = pts[-1]
        ax = 0 if abs(d[0]) < 0.5 else 1
        j = q.copy()
        j[ax] += VAR["jog"]
        pts.append(j)
    return pts


def _path(R, route, line, bid, a, b, nps, a_rack=None, b_rack=None):
    """a, b free points; returns list a..b via local pipeway or rack."""
    P = R.P

    def side(y):
        return "N" if y > P.ry1 else ("S" if y < P.ry0 else "R")

    tier = P.tier_for(line)
    if a_rack is None and b_rack is None and side(a[1]) == side(b[1]) and side(a[1]) != "R" and abs(a[0] - b[0]) <= 30:
        zNS, zEW = LOCAL_Z["NS"] + VAR["dzl"], LOCAL_Z["EW"] + VAR["dzl"]
        if max(a[2], b[2]) > 110 and min(a[2], b[2]) > 108:
            zNS = zEW = max(a[2], b[2])
        return [a, V(a[0], a[1], zNS), V(a[0], b[1], zNS), V(a[0], b[1], zEW), V(b[0], b[1], zEW), V(b[0], b[1], b[2]), b]
    zc = P.zc(tier, nps, line["insul"])
    zx = P.zx(tier, nps, line["insul"], above=VAR["up"]) + VAR["dzx"] * (-1 if (tier == 1 and not VAR["up"]) else 1)
    xa = 0.0 if a_rack == "bl" else a[0]
    xb = 0.0 if b_rack == "bl" else b[0]
    hot = line["design_T_C"] > 150
    R._edge = getattr(R, "_edge", 0) + (1 if hot else 0)
    y = R.rack.alloc(tier, xa, xb, nps, line["insul"], line["design_T_C"], line["line_no"],
                     ("south" if R._edge % 2 else "north") if hot else "centre")
    legs = [abs(y - a[1]) + 1 if a_rack != "bl" else 30.0, abs(y - b[1]) + 1 if b_rack != "bl" else 30.0]
    lp, anchors, info = R.loops_for_run(route, line, nps, y, zc, xa, xb, legs, tier)
    rk = R.rack_points(xa, xb, y, zc, lp, nps, tier)
    R.rack_run(route, bid, tier, y, zc, xa, xb)
    route.loops.append(dict(branch=bid, tier=tier, y=y, legs=[x for q in lp for x in q[:2]],
                            H=(lp[0][2] if lp else 0.0), anchors=anchors, info=info))
    pre = [] if a_rack == "bl" else [a, V(a[0], a[1], zx), V(a[0], y, zx), V(a[0], y, zc)]
    post = [] if b_rack == "bl" else [V(b[0], y, zc), V(b[0], y, zx), V(b[0], b[1], zx), b]
    return pre + rk + post


def auto_route(R, l, A, B):
    P = R.P
    nps = l["size_in"]
    r = Route(l, "study")
    r.study_valves = []
    # header -> nozzle / nozzle -> header (branch connections on rack header)
    ha = A[0] if A[0]["kind"] == "header" else None
    hb = B[0] if B[0]["kind"] == "header" else None
    if ha and hb:
        H1, H2 = R.headers[ha["code"]], R.headers[hb["code"]]
        x = 12.0
        z = max(H1["zc"], H2["zc"]) + 1.0
        pts = [V(x, H1["y"], H1["zc"]), V(x, H1["y"], z), V(x, H2["y"], z), V(x, H2["y"], H2["zc"])]
        r.add_branch("MAIN", nps, pts, dict(kind="header", ref=H1["line_no"], label=ha["label"]),
                     dict(kind="header", ref=H2["line_no"], label=hb["label"]))
        r.study_valves += [("gate", nps, 2), ("globe", nps, 1)]
        return r
    if ha or hb:
        H = R.headers[(ha or hb)["code"]]
        ports = B if ha else A
        port = ports[0]
        far = V(port["p"][0], H["y"], H["zc"])
        chain = _stub_chain(R, port, nps, far)
        q = chain[-1]
        zh = H["zc"] + (1.0 if l["fluid"] in ("LS", "MS", "HS", "FG", "IA", "N") else -1.0 if l["fluid"] == "CD" else 1.0)
        if (ha or hb)["code"] == "FL":
            zh = max(q[2], H["zc"] + 1.2)
        hp = V(q[0], H["y"], H["zc"])
        if not (H["x0"] - 0.1 <= q[0] <= H["x1"] + 0.1):
            hp = V(min(max(q[0], H["x0"] + 0.5), H["x1"] - 0.5), H["y"], H["zc"])
        mid = [V(hp[0], H["y"], zh), V(hp[0], q[1], zh), V(q[0], q[1], zh)]
        pts = [hp] + mid + chain[::-1] if ha else chain + mid[::-1] + [hp]
        hc = dict(kind="header", ref=H["line_no"], label=(ha or hb)["label"])
        nc = dict(kind="nozzle", tag=port["tag"], nozzle=port["nozzle"], nps=nps, label=port["label"],
                  p=V(*port["p"]).tolist(), dir=V(*port["dir"]).tolist())
        r.add_branch("MAIN", nps, pts, hc if ha else nc, nc if ha else hc)
        hr = H["route"]
        r._hdr_route = hr
        r._hdr_line = H["line_no"]
        d = hr.br("MAIN").d_of_point(hp, tol=0.05) if hr.branches else None
        if d is not None:
            hr.add("olet_branch", "MAIN", d=d, nps_b=nps, tag="BR", note=f"branch {l['line_no']}")
        r.study_valves += [("gate", nps, 1)]
        return r
    # nozzle(s) / BL
    a_bl = A[0]["kind"] == "bl"
    b_bl = B[0]["kind"] == "bl"
    if a_bl and b_bl:
        raise ValueError("both ends battery limit")
    tgtB = V(*B[0]["p"]) if not b_bl else V(0, 75, 105)
    tgtA = V(*A[0]["p"]) if not a_bl else V(0, 75, 105)
    # start
    branchB = None
    if a_bl:
        start_pts = []
        a = None
        st = dict(kind="bl", label=f"BATTERY LIMIT ({l['from']})")
    elif len(A) == 2 and A[0]["tag"].startswith("P-"):
        p0, p1 = V(*A[0]["p"]), V(*A[1]["p"])
        zd = p0[2] + 2.4
        sg = 1.0 if tgtB[0] >= p1[0] else -1.0
        if (p1[0] - p0[0]) * sg < 0:
            p0, p1 = p1, p0
            A = A[::-1]
        a = V(p1[0] + sg * 1.2, p0[1], zd)
        start_pts = [p0, V(p0[0], p0[1], zd)]
        branchB = ("disch", A[1], [p1, V(p1[0], p1[1], zd)])
        st = dict(kind="nozzle", tag=A[0]["tag"], nozzle=A[0]["nozzle"], nps=nps, label=A[0]["label"],
                  p=p0.tolist(), dir=[0, 0, 1])
        r.study_valves += [("check", nps, 2), ("gate", nps, 2)]
    else:
        ch = _stub_chain(R, A[0], nps, tgtB)
        start_pts = ch[:-1]
        a = ch[-1]
        st = dict(kind="nozzle", tag=A[0]["tag"], nozzle=A[0]["nozzle"], nps=nps, label=A[0]["label"],
                  p=V(*A[0]["p"]).tolist(), dir=V(*A[0]["dir"]).tolist())
    # end
    if b_bl:
        end_pts = []
        b = None
        en = dict(kind="bl", label=f"BATTERY LIMIT ({l['to']})")
    elif len(B) == 2 and B[0]["tag"].startswith("P-"):
        q0, q1 = V(*B[0]["p"]), V(*B[1]["p"])
        src_x = a[0] if a is not None else 0.0
        near, far = (q0, q1) if abs(src_x - q0[0]) < abs(src_x - q1[0]) else (q1, q0)
        Bn = B[0] if near is q0 else B[1]
        Bf = B[1] if near is q0 else B[0]
        yh = near[1] + 2.4 * np.sign(V(*Bn["dir"])[1] or 1)
        zh = near[2] + 2.2
        b = V(near[0], yh, zh)
        end_pts = [V(far[0], yh, zh), V(far[0], yh, far[2]), far]
        branchB = ("suct", Bn, [V(near[0], yh, zh), V(near[0], yh, near[2]), near])
        en = dict(kind="nozzle", tag=Bf["tag"], nozzle=Bf["nozzle"], nps=nps, label=Bf["label"], p=far.tolist(),
                  dir=V(*Bf["dir"]).tolist())
        r.study_valves += [("gate", nps, 2), ("strainer", nps, 2)]
    else:
        ch = _stub_chain(R, B[0], nps, tgtA)
        end_pts = ch[:-1][::-1]
        b = ch[-1]
        en = dict(kind="nozzle", tag=B[0]["tag"], nozzle=B[0]["nozzle"], nps=nps, label=B[0]["label"],
                  p=V(*B[0]["p"]).tolist(), dir=V(*B[0]["dir"]).tolist())
    if a is None:
        pts = _path(R, r, l, "MAIN", None, b, nps, a_rack="bl")
    elif b is None:
        pts = _path(R, r, l, "MAIN", a, None, nps, b_rack="bl")
    else:
        pts = _path(R, r, l, "MAIN", a, b, nps)
    allp = start_pts + pts + end_pts
    r.add_branch("MAIN", nps, allp, st, en)
    if branchB:
        kind, port, bp = branchB
        conn = dict(kind="nozzle", tag=port["tag"], nozzle=port["nozzle"], nps=nps, label=port["label"],
                    p=V(*port["p"]).tolist(), dir=V(*port["dir"]).tolist())
        if kind == "disch":
            r.add_branch("BR", nps, bp, conn, dict(kind="tee"), parent="MAIN")
        else:
            r.add_branch("BR", nps, bp, dict(kind="tee"), conn, parent="MAIN")
    if r.br("MAIN").length < 0.3:
        raise ValueError("degenerate route")
    return r
