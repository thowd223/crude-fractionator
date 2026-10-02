"""Route data model: branches (orthogonal polylines), inline components, derived fittings, welds, spools,
cut lengths, supports. All coordinates plant m (x east, y north, z = EL)."""
from __future__ import annotations

import math
import re

import numpy as np

from . import specs

SPOOL_MAX_L = 12.0     # m developed / longest envelope dimension (road transport)
SPOOL_MAX_W = 3.0      # m second / third envelope dimension
EPS = 1e-6

BOLTED = {"gate", "globe", "check", "cv", "strainer", "fe", "blind", "spec"}


def P(*a):
    return np.array(a if len(a) == 3 else a[0], dtype=float)


def key_of(line_no):
    """'12"-P-100-050-B2-H' -> 'P-100-050' (size/class independent key)."""
    m = re.match(r'^[\d\-/.]+"-([A-Z]+)-(\d{3})-(\d{3})-', line_no)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else line_no


def simplify(pts):
    out = []
    for p in pts:
        p = P(p)
        if out and np.linalg.norm(p - out[-1]) < 1e-4:
            continue
        out.append(p)
    i = 1
    while i < len(out) - 1:
        a, b, c = out[i - 1], out[i], out[i + 1]
        u, v = b - a, c - b
        if np.linalg.norm(np.cross(u, v)) < 1e-6 * max(np.linalg.norm(u) * np.linalg.norm(v), 1e-9) and np.dot(u, v) > 0:
            out.pop(i)
        else:
            i += 1
    return out


class Branch:
    def __init__(self, bid, nps, pts, start, end, parent=None):
        self.id = bid
        self.nps = nps
        self.pts = simplify(pts)
        self.start = start          # dict(kind=nozzle|tee|bl|header|cap|cont, ...)
        self.end = end
        self.parent = parent
        self._cum()

    def _cum(self):
        self.seg = [np.linalg.norm(self.pts[i + 1] - self.pts[i]) for i in range(len(self.pts) - 1)]
        self.cum = [0.0]
        for s in self.seg:
            self.cum.append(self.cum[-1] + s)

    @property
    def length(self):
        return self.cum[-1]

    def point_at(self, d):
        d = min(max(d, 0.0), self.length)
        for i, s in enumerate(self.seg):
            if d <= self.cum[i + 1] + EPS:
                t = (d - self.cum[i]) / s if s > 0 else 0
                return self.pts[i] + (self.pts[i + 1] - self.pts[i]) * t
        return self.pts[-1]

    def seg_index(self, d):
        for i in range(len(self.seg)):
            if d <= self.cum[i + 1] + EPS:
                return i
        return len(self.seg) - 1

    def dir_at(self, d):
        i = self.seg_index(d)
        v = self.pts[i + 1] - self.pts[i]
        return v / max(np.linalg.norm(v), 1e-9)

    def d_of_point(self, p, tol=0.02):
        p = P(p)
        best = None
        for i in range(len(self.seg)):
            a, b = self.pts[i], self.pts[i + 1]
            ab = b - a
            L2 = float(np.dot(ab, ab))
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, float(np.dot(p - a, ab)) / L2))
            q = a + ab * t
            dist = np.linalg.norm(q - p)
            if best is None or dist < best[0]:
                best = (dist, self.cum[i] + t * math.sqrt(L2))
        return best[1] if best and best[0] < tol else None


class Route:
    def __init__(self, line, level="critical"):
        self.line = line
        self.line_no = line["line_no"]
        self.cls = line["cls"]
        self.nps = line["size_in"]
        self.level = level
        self.branches: list[Branch] = []
        self.items = []          # inline components placed by router
        self.supports = []
        self.rack_runs = []      # dict(tier, el, y, x0, x1, zc, branch)
        self.loops = []
        self.notes = []
        self.cont = []           # continuation / tie-in references for iso
        self.slope = []          # dict(branch, seg, ratio, note)
        self.stress = {}
        self.vents = []

    def br(self, bid):
        return next(b for b in self.branches if b.id == bid)

    def add_branch(self, *a, **k):
        b = Branch(*a, **k)
        self.branches.append(b)
        return b

    def add(self, kind, branch, d=None, at=None, **attrs):
        """Inline component. d = centre distance from branch start (m); at='start'/'end' = bolted to nozzle."""
        it = dict(kind=kind, branch=branch, d=d, at=at, **attrs)
        self.items.append(it)
        return it

    # ------------------------------------------------------------------
    def finalize(self):
        rating = specs.cls(self.cls)["rating"]
        self.rating = rating
        self.elements = {}
        self.fittings = []
        self.welds = []
        self.joints = []
        self.spools = []
        self.pieces = []
        self.conflicts = []
        for b in self.branches:
            self.elements[b.id] = self._elements(b, rating)
        self._spools()
        self._number()

    def _nps_at(self, b, d):
        n = b.nps
        reds = sorted([it for it in self.items if it["kind"] == "reducer" and it["branch"] == b.id],
                      key=lambda r: r["_d"] if "_d" in r else (r["d"] or 0))
        for r in reds:
            rd = r.get("_d", r["d"])
            if rd is not None and rd < d:
                n = r["nps2"]
        return n

    def _elements(self, b, rating):
        E = []
        Lb = b.length

        def add(kind, d0, d1, left, right, **a):
            E.append(dict(kind=kind, d0=d0, d1=d1, left=left, right=right, **a))

        children = [c for c in self.branches if c.parent == b.id]
        tee_d = {}
        for c in children:
            pt = c.pts[0] if c.start.get("kind") == "tee" else c.pts[-1]
            d = b.d_of_point(pt)
            if d is None:
                self.conflicts.append(f"branch {c.id} tee point not on {b.id}")
                continue
            tee_d[c.id] = d
        # end stacks (nozzle-mounted components)
        stacks = {"start": [it for it in self.items if it["branch"] == b.id and it["at"] == "start"],
                  "end": [it for it in self.items if it["branch"] == b.id and it["at"] == "end"]}
        for side in ("start", "end"):
            conn = b.start if side == "start" else b.end
            pos = 0.0
            nps = b.nps if side == "start" else None
            if nps is None:
                nps = b.nps
                for r in self.items:
                    if r["kind"] == "reducer" and r["branch"] == b.id and r["at"] is None:
                        nps = r["nps2"]
            k = conn.get("kind")
            seq = []
            if k == "nozzle":
                seq = list(stacks[side])
                nn = conn.get("nps", nps)
                prev_bolted = True
                for it in seq:
                    it_n = it.get("nps", nn)
                    if it["kind"] in BOLTED:
                        L = specs.valve_ftf(it["kind"], it_n, rating) if it["kind"] in ("gate", "globe", "check", "cv") else 0.0
                        if not prev_bolted:
                            fl = specs.wn_len(it_n, rating)
                            self._place(E, side, Lb, pos, pos + fl, "flange", "W", "B", nps=it_n)
                            pos += fl
                        self._place(E, side, Lb, pos, pos + L, it["kind"], "B", "B", nps=it_n, item=it)
                        it["_d"] = pos + L / 2 if side == "start" else Lb - pos - L / 2
                        pos += L
                        prev_bolted = True
                    else:   # reducer at nozzle
                        if prev_bolted:
                            fl = specs.wn_len(nn, rating)
                            self._place(E, side, Lb, pos, pos + fl, "flange", "B", "W", nps=nn)
                            pos += fl
                        H = specs.red_H(max(it["nps"], it["nps2"]))
                        self._place(E, side, Lb, pos, pos + H, "reducer", "W", "W", nps=it["nps"], item=it)
                        it["_d"] = pos + H / 2 if side == "start" else Lb - pos - H / 2
                        pos += H
                        prev_bolted = False
                        nn = it["nps2"] if side == "start" else it["nps"]
                if prev_bolted:
                    fl = specs.wn_len(nn, rating)
                    self._place(E, side, Lb, pos, pos + fl, "flange", "B", "W", nps=nn, nozzle=True)
                    pos += fl
            elif k == "tee":
                C = specs.tee_C(self._parent_nps(b))
                self._place(E, side, Lb, 0.0, C, "tee_out", "W", "W", nps=b.nps, field=True)
            elif k == "header":
                self._place(E, side, Lb, 0.0, 0.0, "olet", "W", "W", nps=b.nps, field=True, header=conn.get("ref"))
            elif k == "bl":
                self._place(E, side, Lb, 0.0, 0.0, "tiein", "W", "W", nps=b.nps, field=True)
            elif k == "cap":
                self._place(E, side, Lb, 0.0, max(0.038, 0.011 * b.nps + 0.02), "cap", "W", "W", nps=b.nps)
            elif k == "cont":
                self._place(E, side, Lb, 0.0, 0.0, "cont", "W", "W", nps=b.nps, field=True)
        # elbows / tees at interior vertices
        vert_children = {}
        for cid, d in tee_d.items():
            vert_children.setdefault(round(d, 3), []).append(cid)
        for i in range(1, len(b.pts) - 1):
            dv = b.cum[i]
            nps = self._nps_at(b, dv)
            if any(abs(dv - d) < 0.02 for d in tee_d.values()):
                C = specs.tee_C(nps)
                cid = [c for c, d in tee_d.items() if abs(dv - d) < 0.02][0]
                add("tee", dv - C, dv + C, "W", "W", nps=nps, nps_b=self.br(cid).nps, child=cid, vertex=True)
            else:
                v1 = b.pts[i] - b.pts[i - 1]
                v2 = b.pts[i + 1] - b.pts[i]
                ang = math.degrees(math.acos(max(-1, min(1, np.dot(v1, v2) / np.linalg.norm(v1) / np.linalg.norm(v2)))))
                A = specs.elbow_A(nps) * (1.0 if ang > 60 else math.tan(math.radians(ang / 2)))
                add("elbow", dv - A, dv + A, "W", "W", nps=nps, angle=round(ang), at_pt=b.pts[i].tolist())
        for cid, d in tee_d.items():
            if any(abs(b.cum[i] - d) < 0.02 for i in range(1, len(b.pts) - 1)):
                continue
            nps = self._nps_at(b, d)
            C = specs.tee_C(nps)
            add("tee", d - C, d + C, "W", "W", nps=nps, nps_b=self.br(cid).nps, child=cid, vertex=False)
        # inline items
        for it in self.items:
            if it["branch"] != b.id or it["at"] is not None:
                continue
            d = it["d"]
            it["_d"] = d
            n = it.get("nps") or self._nps_at(b, d)
            if it["kind"] in ("gate", "globe", "check", "cv"):
                F = specs.valve_ftf(it["kind"], n, rating)
                Y = specs.wn_len(n, rating)
                add("flange", d - F / 2 - Y, d - F / 2, "W", "B", nps=n)
                add(it["kind"], d - F / 2, d + F / 2, "B", "B", nps=n, item=it)
                add("flange", d + F / 2, d + F / 2 + Y, "B", "W", nps=n)
            elif it["kind"] in ("fe", "strainer", "spec", "blind"):
                Y = specs.wn_len(n, rating)
                add("flange", d - Y, d, "W", "B", nps=n, orifice=it["kind"] == "fe")
                add(it["kind"], d, d, "B", "B", nps=n, item=it)
                add("flange", d, d + Y, "B", "W", nps=n, orifice=it["kind"] == "fe")
            elif it["kind"] == "reducer":
                H = specs.red_H(max(it["nps"], it["nps2"]))
                add("reducer", d - H / 2, d + H / 2, "W", "W", nps=it["nps"], item=it)
            elif it["kind"] in ("olet_branch",):
                add("olet_b", d, d, "W", "W", nps=n, item=it)
        E.sort(key=lambda e: (e["d0"], e["d1"]))
        # check overlaps
        for e1, e2 in zip(E, E[1:]):
            if e2["d0"] < e1["d1"] - 0.005:
                self.conflicts.append(f"{b.id}: {e1['kind']} / {e2['kind']} overlap {1000 * (e1['d1'] - e2['d0']):.0f} mm "
                                      f"at d={e2['d0']:.2f}")
                e2["d0"] = e1["d1"]
                if e2["d1"] < e2["d0"]:
                    e2["d1"] = e2["d0"]
        # pipe pieces in the gaps
        out = []
        cur = 0.0
        for e in E:
            if e["d0"] > cur + 0.005:
                out.append(dict(kind="pipe", d0=cur, d1=e["d0"], left="W", right="W", nps=self._nps_at(b, (cur + e["d0"]) / 2)))
            out.append(e)
            cur = max(cur, e["d1"])
        if Lb > cur + 0.005:
            out.append(dict(kind="pipe", d0=cur, d1=Lb, left="W", right="W", nps=self._nps_at(b, (cur + Lb) / 2)))
        for e in out:
            e["branch"] = b.id
        return out

    def _place(self, E, side, Lb, p0, p1, kind, left, right, **a):
        if side == "start":
            E.append(dict(kind=kind, d0=p0, d1=p1, left=left, right=right, **a))
        else:
            E.append(dict(kind=kind, d0=Lb - p1, d1=Lb - p0, left=right, right=left, **a))

    def _parent_nps(self, b):
        p = self.br(b.parent)
        pt = b.pts[0]
        d = p.d_of_point(pt)
        return self._nps_at(p, d or 0.0)

    # ------------------------------------------------------------------
    def _spools(self):
        sp_no = 0
        for b in self.branches:
            els = self.elements[b.id]
            groups, cur = [], []
            for i, e in enumerate(els):
                if e["kind"] in BOLTED:
                    if cur:
                        groups.append(cur)
                    cur = []
                    continue
                cur.append(e)
            if cur:
                groups.append(cur)
            for g in groups:
                g = [e for e in g if e["kind"] not in ("tee_out", "olet", "tiein", "cont")] or []
                if not g:
                    continue
                for part in self._split(b, g):
                    sp_no += 1
                    sid = f"SP{sp_no:02d}"
                    for e in part:
                        e["spool"] = sid
                    d0, d1 = part[0]["d0"], part[-1]["d1"]
                    self.spools.append(dict(id=sid, branch=b.id, d0=d0, d1=d1, length=round(d1 - d0, 3),
                                            env=[round(v, 2) for v in self._envelope(b, d0, d1)]))

    def _envelope(self, b, d0, d1):
        pts = [b.point_at(d0), b.point_at(d1)] + [b.pts[i] for i in range(len(b.pts)) if d0 < b.cum[i] < d1]
        a = np.array(pts)
        ext = a.max(0) - a.min(0)
        n = specs.od(b.nps) / 1000.0
        return sorted((ext + n).tolist(), reverse=True)

    def _ok(self, b, d0, d1):
        e = self._envelope(b, d0, d1)
        return (d1 - d0) <= SPOOL_MAX_L + 1e-6 and e[0] <= SPOOL_MAX_L and e[1] <= SPOOL_MAX_W

    def _split(self, b, g):
        els = self.elements[b.id]
        parts, cur = [], []
        start = g[0]["d0"]
        for e in g:
            if self._ok(b, start, e["d1"]):
                cur.append(e)
                continue
            if e["kind"] == "pipe":
                lo, hi = e["d0"] + 0.15, e["d1"] - 0.15
                best = None
                x = lo
                while x <= hi:
                    if self._ok(b, start, x):
                        best = x
                    x += 0.1
                if best is not None and best - e["d0"] >= 0.15:
                    left = dict(e, d1=best)
                    right = dict(e, d0=best, field_left=True)
                    left["right_fw"] = True
                    idx = els.index(e)
                    els[idx:idx + 1] = [left, right]
                    cur.append(left)
                    parts.append(cur)
                    cur, start = [right], best
                    # long straight pipe: keep splitting
                    while not self._ok(b, start, right["d1"]):
                        best = None
                        x = start + 0.3
                        while x <= right["d1"] - 0.15:
                            if self._ok(b, start, x):
                                best = x
                            x += 0.1
                        if best is None:
                            break
                        l2 = dict(right, d1=best, right_fw=True)
                        r2 = dict(right, d0=best, field_left=True)
                        idx = els.index(right)
                        els[idx:idx + 1] = [l2, r2]
                        cur[-1] = l2
                        parts.append(cur)
                        cur, start, right = [r2], best, r2
                    continue
            # split before this fitting (field weld at fitting end)
            if cur:
                cur[-1]["right_fw"] = True
                parts.append(cur)
            e["field_left"] = True
            cur, start = [e], e["d0"]
        if cur:
            parts.append(cur)
        return parts

    def _number(self):
        """Welds (shop/field), bolted joints and pipe pieces, numbered along each branch."""
        wn = 0
        pn = {}
        for b in self.branches:
            els = self.elements[b.id]
            for i in range(len(els) - 1):
                e1, e2 = els[i], els[i + 1]
                d = e1["d1"]
                if e1["right"] == "B" and e2["left"] == "B":
                    self.joints.append(dict(branch=b.id, d=d, nps=e1.get("nps") or b.nps,
                                            pt=b.point_at(d).tolist()))
                    continue
                field = bool(e1.get("right_fw") or e2.get("field_left") or e1["kind"] in ("tee_out", "olet", "tiein", "cont")
                             or e2["kind"] in ("tee_out", "olet", "tiein", "cont"))
                if e1["kind"] in ("tee_out",) and e1["d1"] - e1["d0"] > 0 and e2["kind"] == "pipe":
                    field = True
                wn += 1
                nps = min(e1.get("nps") or b.nps, e2.get("nps") or b.nps) if e1["kind"] != "reducer" and e2["kind"] != "reducer" else (e1.get("nps") if e2["kind"] == "reducer" else e2.get("nps"))
                if e1["kind"] == "reducer":
                    nps = e1["item"]["nps2"]
                if e2["kind"] == "reducer":
                    nps = e2["item"]["nps"]
                self.welds.append(dict(no=wn, type="F" if field else "S", branch=b.id, d=round(d, 3), nps=nps,
                                       pt=[round(v, 3) for v in b.point_at(d).tolist()],
                                       spool=e1.get("spool") or e2.get("spool")))
            # nozzle bolted joints at branch ends
            for e in (els[0], els[-1]):
                if e["kind"] in ("flange",) and e.get("nozzle"):
                    d = e["d0"] if e is els[0] else e["d1"]
                    self.joints.append(dict(branch=b.id, d=d, nps=e["nps"], pt=b.point_at(d).tolist(), nozzle=True))
                if e["kind"] in BOLTED and e is els[0] and e["d0"] < 0.001:
                    self.joints.append(dict(branch=b.id, d=0.0, nps=e["nps"], pt=b.point_at(0).tolist(), nozzle=True))
                if e["kind"] in BOLTED and e is els[-1] and e["d1"] > b.length - 0.001:
                    self.joints.append(dict(branch=b.id, d=b.length, nps=e["nps"], pt=b.point_at(b.length).tolist(),
                                            nozzle=True))
            # olet / tee-branch weld at branch start counted as field weld of branch size
            for e in els:
                if e["kind"] in ("olet",):
                    wn += 1
                    self.welds.append(dict(no=wn, type="F", branch=b.id, d=e["d0"], nps=e["nps"], olet=True,
                                           pt=[round(v, 3) for v in b.point_at(e["d0"]).tolist()], spool=None))
            for e in els:
                if e["kind"] == "pipe" and e["d1"] - e["d0"] > 0.003:
                    sp = e.get("spool", "-")
                    pn[sp] = pn.get(sp, 0) + 1
                    self.pieces.append(dict(spool=sp, no=f"{sp}-{pn[sp]}", branch=b.id, nps=e["nps"],
                                            L_mm=round((e["d1"] - e["d0"]) * 1000)))
        # fittings summary
        for b in self.branches:
            for e in self.elements[b.id]:
                k = e["kind"]
                if k in ("pipe", "tee_out", "tiein", "cont"):
                    continue
                f = dict(kind=k, nps=e.get("nps"), branch=b.id, d=round((e["d0"] + e["d1"]) / 2, 3),
                         spool=e.get("spool"))
                if k == "tee":
                    f["nps_b"] = e["nps_b"]
                if k == "reducer":
                    f.update(nps=e["item"]["nps"], nps2=e["item"]["nps2"], ecc=e["item"].get("ecc"))
                if k in BOLTED and e.get("item"):
                    f.update(tag=e["item"].get("tag"), note=e["item"].get("note"))
                if k == "elbow":
                    f["angle"] = e.get("angle", 90)
                self.fittings.append(f)

    # ------------------------------------------------------------------
    def total_length(self):
        return sum(b.length for b in self.branches)

    def pipe_length_by_nps(self):
        out = {}
        for b in self.branches:
            for e in self.elements[b.id]:
                if e["kind"] == "pipe":
                    out[e["nps"]] = out.get(e["nps"], 0.0) + (e["d1"] - e["d0"])
        return out

    def weld_inch_dia(self):
        return sum(w["nps"] for w in self.welds)
