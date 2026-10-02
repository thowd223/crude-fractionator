"""Line-specific routing strategies for the stress-/layout-critical lines (isometric set).

Coordinates are taken from data/layout.json nozzles at build time; offsets below are piping design choices
(clearances, header elevations, valve access) and are documented in CFU-000-PI-RPT-001.
"""
from __future__ import annotations

import re

from . import specs
from .model import Route, key_of
from .router import V

# iso register: (iso number, line key, short title)
ISO_SET = [   # (iso number, (from regex, to regex), title) - lines found semantically in lines.json at build time
    ("CFU-100-PI-ISO-001", (r"^H-101 outlet manifold", r"^C-101"), "H-101 OUTLET TRANSFER LINE TO C-101"),
    ("CFU-100-PI-ISO-002", (r"^C-101 top", r"^A-101"), "C-101 OVERHEAD VAPOUR TO A-101"),
    ("CFU-100-PI-ISO-003", (r"^C-101 bottom", r"^P-112"), "C-101 BOTTOMS TO P-112A/B SUCTION"),
    ("CFU-100-PI-ISO-004", (r"^P-112", r"^H-201 inlet"), "P-112A/B DISCHARGE TO H-201 INLET"),
    ("CFU-200-PI-ISO-001", (r"^H-201 outlet manifold", r"^C-201"), "H-201 OUTLET VACUUM TRANSFER LINE TO C-201"),
    ("CFU-100-PI-ISO-005", (r"(TK|OSBL)", r"^P-101"), "CRUDE SUCTION TO P-101A/B"),
    ("CFU-100-PI-ISO-006", (r"^P-101", r"^E-101"), "P-101A/B DISCHARGE TO E-101"),
    ("CFU-100-PI-ISO-007", (r"^C-101 tray", r"^P-108"), "C-101 BPA DRAW TO P-108A/B"),
    ("CFU-100-PI-ISO-008", (r"^E-113", r"^C-101 tray"), "BPA RETURN E-113 TO C-101"),
    ("CFU-100-PI-ISO-009", (r"^C-101 tray", r"^C-102$"), "C-101 KERO DRAW TO C-102 (GRAVITY)"),
    ("CFU-100-PI-ISO-010", (r"^D-102", r"^P-103"), "D-102 TO P-103A/B SUCTION"),
    ("CFU-100-PI-ISO-011", (r"^D-102", r"^P-104"), "D-102 TO P-104A/B SUCTION"),
    ("CFU-100-PI-ISO-012", (r"^HP steam header", r"^E-116"), "HP STEAM HEADER TO E-116"),
]
ISO_FIND = {k: v for _, v, k in [(a, b, a) for a, b, c in ISO_SET]}


def find_line(lines, frm, to, fluid=None):
    c = [l for l in lines if re.search(frm, l["from"]) and re.search(to, l["to"])
         and (fluid is None or l["fluid"] == fluid)]
    if not c:
        return None
    return max(c, key=lambda l: l["size_in"])


def pump_nozzles(line_nps):
    """Assumed pump nozzle sizes (vendor data not yet available): suction 1-2 sizes below line."""
    s = specs.step(line_nps, -1 if line_nps <= 10 else -2)
    return s


def at(route, bid, pt):
    d = route.br(bid).d_of_point(V(*pt), tol=0.03)
    if d is None:
        raise ValueError(f"{route.line_no}: point {pt} not on branch {bid}")
    return d


def nozzle_conn(R, tag, name, nps, label=None):
    p, d = R.P.noz(tag, name)
    return dict(kind="nozzle", tag=tag, nozzle=name, nps=nps, label=label or f"{tag} {name.replace('_', ' ')}",
                p=p.tolist(), dir=d.tolist())


def match_instruments(R, line):
    """Instruments for this line - exact line_no, else same size/fluid/area/class with seq+1 (stale refs)."""
    exact = [i for i in R.P.instr if i.get("line_no") == line["line_no"]]
    if exact:
        return exact
    m = re.match(r'^([\d\-/.]+)"-([A-Z]+)-(\d{3})-(\d{3})-([A-Z0-9]+)-', line["line_no"])
    if not m:
        return []
    sz, fl, ar, sq, cl = m.groups()
    alt = f'{sz}"-{fl}-{ar}-{int(sq) + 1:03d}-{cl}-'
    out = [i for i in R.P.instr if (i.get("line_no") or "").startswith(alt)]
    if out:
        R.P.issues.append(f"instruments.json: {', '.join(sorted({i['tag'] for i in out if i['tag'][1:2] in 'VE' or i['tag'][:2] in ('FV', 'TV', 'LV', 'XV', 'FE')}))} "
                          f"reference '{out[0]['line_no']}' but service matches {line['line_no']} "
                          f"(line-number offset vs lines.json) - used for iso {line['line_no']}")
    return out


def tag_of(insts, prefix):
    for i in insts:
        if i["tag"].startswith(prefix):
            return i["tag"]
    return None


def vents_drains(route, skip=()):
    """High-point vents / low-point drains at pockets (D-H..-U low, U-H..-D high)."""
    for b in route.branches:
        if b.id in skip:
            continue
        kinds = []
        for i, s in enumerate(b.seg):
            v = b.pts[i + 1] - b.pts[i]
            kinds.append("U" if v[2] > 0.5 * s else ("D" if v[2] < -0.5 * s else "H"))
        i = 0
        while i < len(kinds):
            if kinds[i] == "H":
                j = i
                while j + 1 < len(kinds) and kinds[j + 1] == "H":
                    j += 1
                prev = kinds[i - 1] if i > 0 else None
                nxt = kinds[j + 1] if j + 1 < len(kinds) else None
                lo = min(range(i, j + 1), key=lambda k: min(b.pts[k][2], b.pts[k + 1][2]))
                d = b.cum[lo] + b.seg[lo] / 2
                if prev == "D" and nxt == "U":
                    route.add("olet_branch", b.id, d=d, nps_b=1 if route.cls not in ("B2", "B3") else 1.5,
                              tag="LPD", note="low-point drain")
                elif prev == "U" and nxt == "D":
                    route.add("olet_branch", b.id, d=d, nps_b=1, tag="HPV", note="high-point vent")
                i = j + 1
            else:
                i += 1


class Ctx:
    def __init__(self, R):
        self.R = R
        self.P = R.P

    def route(self, iso):
        frm, to = ISO_FIND[iso]
        line = find_line(self.P.lines, frm, to)
        if line is None:
            self.P.issues.append(f"{iso}: no line in lines.json with from~'{frm}' to~'{to}' - iso skipped")
            return None, None
        key = key_of(line["line_no"])
        r = Route(line, "critical")
        r.iso = iso
        r.instruments = match_instruments(self.R, line)
        self.R.routes.append(r)
        self.R.critical_keys.append(key)
        return r, line

    def rack(self, route, line, bid, tier, xa, xb, ya_off, yb_off, nps=None, prefer="south", loops=True, above=False):
        R = self.R
        nps = nps or line["size_in"]
        y = R.rack.alloc(tier, xa, xb, nps, line["insul"], line["design_T_C"], line["line_no"], prefer)
        zc = R.P.zc(tier, nps, line["insul"])
        zx = R.P.zx(tier, nps, line["insul"], above=above)
        legs = [abs(y - ya_off) + abs(zx - zc), abs(y - yb_off) + abs(zx - zc)]
        lp, anchors, info = R.loops_for_run(route, line, nps, y, zc, xa, xb, legs, tier) if loops else ([], [], {})
        pts = R.rack_points(xa, xb, y, zc, lp, nps, tier)
        R.rack_run(route, bid, tier, y, zc, xa, xb)
        route.loops.append(dict(branch=bid, tier=tier, y=y, legs=[x for l in lp for x in l[:2]],
                                H=(lp[0][2] if lp else 0.0), anchors=anchors, info=info))
        return y, zc, zx, pts


# ==============================================================================================
def heater_outlet_manifold(C, r, line, heater, npass, pitch, y_off, pass_nps):
    """Symmetrical outlet manifold: header along x on heater north face, pass outlets as branches."""
    P = C.P
    po, pdir = P.noz(heater, "outlet")
    x0, ym, zm = po[0], po[1] + y_off, po[2]
    xs = [x0 + (k - (npass - 1) / 2) * pitch for k in range(npass)]
    half = (npass - 1) / 2 * pitch + 0.75
    r.add_branch("HDR", line["size_in"], [V(x0 - half, ym, zm), V(x0 + half, ym, zm)],
                 dict(kind="cap", label="WELD CAP"), dict(kind="cap", label="WELD CAP"))
    for k, x in enumerate(xs):
        pl = find_line(P.lines, rf"^{heater} pass {k + 1}$", rf"^{heater} outlet manifold")
        lab = pl["line_no"] if pl else f"pass {k + 1}"
        if pl:
            C.R.critical_keys.append(key_of(pl["line_no"]))
        r.add_branch(f"PASS{k + 1}", pass_nps, [V(x, po[1], zm), V(x, ym, zm)],
                     dict(kind="nozzle", tag=heater, nozzle=f"pass {k + 1} outlet", nps=pass_nps,
                          label=f"{heater} PASS {k + 1} OUTLET", p=[x, po[1], zm], dir=[0, 1, 0]),
                     dict(kind="tee", olet=True), parent="HDR")
        r.branches[-1].line_ref = lab
    r.add("olet_branch", "HDR", d=1.4, nps_b=1.5, tag="LPD", note="manifold low-point drain (DBB)")
    P.assumed.append(f"{heater} pass-outlet stubs assumed on north face at {pitch:.1f} m pitch, EL {zm:.3f} "
                     f"(heater vendor to confirm terminal points)")
    return x0, ym, zm


def _pass_nps(P, heater):
    pl = find_line(P.lines, rf"^{heater} pass 1$", rf"^{heater} outlet manifold")
    return pl["size_in"] if pl else 8


def _pass_list(P, heater):
    out = [find_line(P.lines, rf"^{heater} pass {k}$", rf"^{heater} outlet manifold") for k in range(1, 13)]
    return [l["line_no"] for l in out if l]


def r_h101_transfer(C):
    r, line = C.route("CFU-100-PI-ISO-001")
    if not r:
        return
    P = C.P
    x0, ym, zm = heater_outlet_manifold(C, r, line, "H-101", P.eq["H-101"].get("passes", 8), 2.2, 1.5, _pass_nps(P, "H-101"))
    fz, fd = P.noz("C-101", "feed")
    nps = line["size_in"]
    zt = P.tiers[3] + 0.95 + specs.od(nps) / 2000.0           # crossing above tier 3
    y_s = P.ry0 - 4.0                                          # rise south of rack
    y_n = fz[1] - 5.5                                          # approach column from south
    pts = [V(x0, ym, zm), V(x0, y_s, zm), V(x0, y_s, zt), V(x0, y_n, zt), V(fz[0], y_n, zt), V(fz[0], y_n, fz[2]),
           V(*fz)]
    r.add_branch("TL", nps, pts, dict(kind="tee"), nozzle_conn(C.R, "C-101", "feed", nps, "C-101 FLASH ZONE FEED"),
                 parent="HDR")
    tw = tag_of(r.instruments, "TI") or tag_of(r.instruments, "TT")
    r.add("olet_branch", "TL", d=3.0, nps_b=1.5, tag=tw or "TW", note="thermowell (COT)")
    r.add("olet_branch", "TL", d=6.0, nps_b=1.0, tag="PI", note="pressure connection")
    r.notes += ["Transfer line rises continuously from manifold to C-101 - no pockets (2-phase flow).",
                "Manifold symmetrical about C/L of heater: equal hydraulic length per pass.",
                "Rack crossing above tier 3 on dedicated transfer-line support beams at bents x=96/102.",
                "Formal stress analysis mandatory (API 560 terminal loads, C-101 nozzle WRC 537)."]
    pl = _pass_list(P, "H-101")
    r.cont += [("start", "HDR", f"{len(pl)} PASS OUTLETS {pl[0] if pl else ''}..{pl[-1][-12:] if pl else ''} (THIS ISO)")]


def r_h201_transfer(C):
    r, line = C.route("CFU-200-PI-ISO-001")
    if not r:
        return
    P = C.P
    x0, ym, zm = heater_outlet_manifold(C, r, line, "H-201", P.eq["H-201"].get("passes", 4), 3.0, 2.0, _pass_nps(P, "H-201"))
    fz, fd = P.noz("C-201", "feed")
    nps = line["size_in"]
    slope = 1 / 100.0
    y_t = fz[1] - 6.7
    Lh = (y_t - ym) + (fz[1] - y_t) + 0.414 * abs(fz[0] - x0)
    ztop = fz[2] + slope * Lh
    z2 = fz[2] + slope * (fz[1] - y_t)
    dx = fz[0] - x0
    y_j = y_t - abs(dx)                    # 45 deg plan jog (54" elbows too long for a 90/90 offset)
    z0j = ztop - slope * (y_j - ym)
    pts = [V(x0, ym, zm), V(x0, ym, ztop), V(x0, y_j, z0j), V(fz[0], y_t, z2), V(*fz)]
    r.add_branch("TL", nps, pts, dict(kind="tee"), nozzle_conn(C.R, "C-201", "feed", nps, "C-201 FLASH ZONE FEED"),
                 parent="HDR")
    r.slope.append(dict(branch="TL", ratio="1:100", note="FALLS TOWARDS C-201"))
    tw = tag_of(r.instruments, "TT") or "TW"
    r.add("olet_branch", "TL", d=4.0, nps_b=1.5, tag=tw, note="thermowell (COT)")
    r.notes += ["Vacuum transfer line: riser at heater then continuous fall 1:100 to C-201 (no liquid hold-up).",
                "Large bore 54\" for low velocity / flash-zone pressure; external-pressure (full vacuum) design.",
                "Crosses rack at high level on transfer-line support structure TLS-201 (independent of rack).",
                "Formal stress analysis mandatory; spring hangers on riser (heater + column growth)."]
    pl = _pass_list(P, "H-201")
    r.cont += [("start", "HDR", f"{len(pl)} PASS OUTLETS {pl[0] if pl else ''}..{pl[-1][-12:] if pl else ''} (THIS ISO)")]


def r_c101_overhead(C):
    r, line = C.route("CFU-100-PI-ISO-002")
    if not r:
        return
    P = C.P
    nps = line["size_in"]
    o, _ = P.noz("C-101", "overhead")
    e = P.eq["C-101"]
    bays = sorted([t for t in P.children.get("A-101", []) if t.startswith("A-101")])
    ins = [P.noz(t, "inlet")[0] for t in bays]
    xc = ins[len(ins) // 2][0]
    yb = ins[0][1]
    zin = ins[0][2]
    plat_r = max([p["r_out"] for p in P.L["structures"]["column_platforms"] if p["tag"] == "C-101"] + [e["D"] / 2])
    y_drop = e["y"] - plat_r - specs.od(nps) / 2000.0 - 0.75
    s = 1 / 200.0
    zT1 = 120.2                                   # first tee (bay B2 / header take-off)
    zH = zT1 - 1.6                                # header EL
    yH = yb + 2.6
    z_top = o[2] + 2.0
    run1 = abs(e["x"] - xc)
    run2 = abs(y_drop - yH)
    zA = zT1 + s * (run1 + run2)
    pts = [V(*o), V(o[0], o[1], z_top), V(o[0], y_drop, z_top - s * abs(o[1] - y_drop)), V(o[0], y_drop, zA),
           V(xc, y_drop, zA - s * run1), V(xc, yH, zT1), V(xc, yb, zT1 - s * 2.6), V(xc, yb, zin)]
    r.add_branch("MAIN", nps, pts, nozzle_conn(C.R, "C-101", "overhead", nps, "C-101 OVERHEAD NOZZLE"),
                 dict(kind="nozzle", tag=bays[len(bays) // 2], nozzle="inlet", nps=24,
                      label=f"{bays[len(bays) // 2]} INLET", p=ins[len(ins) // 2].tolist(), dir=[0, 0, 1]))
    r.add("reducer", "MAIN", d=at(r, "MAIN", [xc, yH - 1.3, zT1 - s * 1.3]), nps=nps, nps2=24)
    # west / east halves
    xw, xe = ins[0][0], ins[-1][0]
    r.add_branch("HW", 30, [V(xc, yH, zT1), V(xc, yH, zH), V(xw, yH, zH - s * abs(xc - xw)),
                            V(xw, yb, zH - s * abs(xc - xw) - s * 2.6), V(xw, yb, zin)],
                 dict(kind="tee"), dict(kind="nozzle", tag=bays[0], nozzle="inlet", nps=24, label=f"{bays[0]} INLET",
                                        p=ins[0].tolist(), dir=[0, 0, 1]), parent="MAIN")
    r.add("reducer", "HW", d=at(r, "HW", [xc - 1.6, yH, zH - s * 1.6]), nps=30, nps2=24)
    r.add_branch("HE", 24, [V(xc, yH, zH), V(xe, yH, zH - s * abs(xe - xc)), V(xe, yb, zH - s * abs(xe - xc) - s * 2.6),
                            V(xe, yb, zin)],
                 dict(kind="tee"), dict(kind="nozzle", tag=bays[-1], nozzle="inlet", nps=24, label=f"{bays[-1]} INLET",
                                        p=ins[-1].tolist(), dir=[0, 0, 1]), parent="HW")
    r.slope.append(dict(branch="MAIN", ratio="1:200", note="SELF-DRAINING TO A-101"))
    inj = [l for l in P.lines if l["from"].startswith("X-103") and "OH" in l["to"]]
    for k, l2 in enumerate(inj[:2]):
        r.add("olet_branch", "MAIN", d=4.2 + 1.2 * k, nps_b=1.0, tag=f"X-103 INJ.{k + 1}",
              note=f"injection quill ({l2['line_no'] if l2 else 'CH'})")
    r.notes += ["Line self-draining: continuous fall 1:200 from C-101 to A-101 - no pockets.",
                "Inlet manifold to A-101 bays symmetrical about bay B2 (hydraulic balance, NH4Cl/HCl corrosion control).",
                "Neutraliser / filming amine injection quills within 1.5 m of column nozzle (X-103).",
                "Riser guided at C-101 platform clips; weight carried by column lugs (line & column grow together)."]


def pump_suction(C, r, line, key_pumps, src_pts, src_conn, y_off=2.4, z_h=None, valve_vertical=True,
                 strainer=True, reverse=False):
    """Main branch to pump B, branch from header tee to pump A; ecc. reducer FOT at each nozzle."""
    P = C.P
    nps = line["size_in"]
    pa, _ = P.noz(key_pumps[0], "suction")
    pb, _ = P.noz(key_pumps[1], "suction")
    nn = pump_nozzles(nps)
    yh = pa[1] + y_off
    last = src_pts[-1]
    order = [pa, pb] if abs(last[0] - pa[0]) < abs(last[0] - pb[0]) else [pb, pa]
    near, far = order
    tags = {tuple(pa): key_pumps[0], tuple(pb): key_pumps[1]}
    lo_x, hi_x = sorted((pa[0], pb[0]))
    xt = last[0] if lo_x + 0.5 < last[0] < hi_x - 0.5 else near[0]
    main = list(src_pts) + [V(xt, yh, z_h), V(far[0], yh, z_h), V(far[0], yh, far[2]), V(*far)]
    r.add_branch("MAIN", nps, main, src_conn,
                 dict(kind="nozzle", tag=tags[tuple(far)], nozzle="suction", nps=nn,
                      label=f"{tags[tuple(far)]} SUCTION", p=far.tolist(), dir=[0, 1, 0]))
    r.add_branch("BR", nps, [V(xt, yh, z_h), V(near[0], yh, z_h), V(near[0], yh, near[2]), V(*near)], dict(kind="tee"),
                 dict(kind="nozzle", tag=tags[tuple(near)], nozzle="suction", nps=nn,
                      label=f"{tags[tuple(near)]} SUCTION", p=near.tolist(), dir=[0, 1, 0]), parent="MAIN")
    for bid, pp in (("MAIN", far), ("BR", near)):
        r.add("reducer", bid, at="end", nps=nps, nps2=nn, ecc="FOT")
        zmid = (z_h + pp[2]) / 2
        r.add("gate", bid, d=at(r, bid, [pp[0], yh, zmid + 0.15]), tag=None, note="suction block valve")
        if strainer:
            r.add("strainer", bid, d=at(r, bid, [pp[0], yh, zmid - 0.55]), tag="TS", note="temporary cone strainer")
    r.notes += [f"Pump suction: no pockets, header falls to pumps; eccentric reducers {specs.nps_str(nps)}x"
                f"{specs.nps_str(nn)} FLAT ON TOP; temporary strainers for commissioning.",
                f"Pump nozzle {specs.nps_str(nn)} assumed (API 610 vendor data pending)."]
    return near, far, yh


def r_c101_bottoms(C):
    r, line = C.route("CFU-100-PI-ISO-003")
    if not r:
        return
    P = C.P
    b, _ = P.noz("C-101", "bottoms")
    zh = 103.6
    src = [V(*b), V(b[0], b[1], zh)]
    pump_suction(C, r, line, ("P-112A", "P-112B"), src, nozzle_conn(C.R, "C-101", "bottoms", line["size_in"],
                                                                     "C-101 BOTTOMS NOZZLE"), z_h=zh)
    r.notes += ["Line exits C-101 skirt through 1000 mm access sleeve; hot (390 C) - skirt opening insulated.",
                "NPSHa per mech. data sheet; suction line kept short (< 15 m developed per pump)."]


def r_p112_discharge(C):
    r, line = C.route("CFU-100-PI-ISO-004")
    if not r:
        return
    P = C.P
    nps = line["size_in"]
    pa, _ = P.noz("P-112A", "discharge")
    pb, _ = P.noz("P-112B", "discharge")
    hi, hd = P.noz("H-201", "inlet")
    suc = find_line(P.lines, r"^C-101 bottom", r"^P-112")
    nn = min(specs.step(pump_nozzles(suc["size_in"] if suc else nps), -1), nps)
    zd = 104.0
    xr = pb[0] + 1.6
    zg = 101.2                       # FV station at grade south of rack
    y_h = hi[1] + 2.95
    y_g = P.ry0 - 7.0
    y, zc, zx, rk = C.rack(r, line, "MAIN", 1, xr, hi[0], pa[1], y_g, prefer="south")
    pts = [V(*pa), V(pa[0], pa[1], zd), V(xr, pa[1], zd), V(xr, pa[1], zx), V(xr, y, zx)] + rk + \
          [V(hi[0], y, zx), V(hi[0], y_g, zx), V(hi[0], y_g, zg), V(hi[0], y_h, zg), V(hi[0], y_h, hi[2]), V(*hi)]
    r.add_branch("MAIN", nps, pts, nozzle_conn(C.R, "P-112A", "discharge", nn, "P-112A DISCHARGE"),
                 nozzle_conn(C.R, "H-201", "inlet", nps, "H-201 INLET MANIFOLD"))
    r.add_branch("BR", nps, [V(*pb), V(pb[0], pb[1], zd)],
                 nozzle_conn(C.R, "P-112B", "discharge", nn, "P-112B DISCHARGE"), dict(kind="tee"), parent="MAIN")
    for bid in ("MAIN", "BR"):
        if nn != nps:
            r.add("reducer", bid, at="start", nps=nn, nps2=nps)
        r.add("check", bid, at="start", note="disch. check (1in warm-up bypass)")
        r.add("gate", bid, at="start", note="disch. block valve")
    ins = r.instruments
    mf = find_line(P.lines, r"^P-112", r"^C-101 bottom")
    if mf:
        C.R.critical_keys.append(key_of(mf["line_no"]))
    xm = pb[0] + 0.75
    r.add_branch("MF", 6, [V(xm, pa[1], zd), V(xm, pa[1] + 1.0, zd)], dict(kind="tee"),
                 dict(kind="cont", label=f"{mf['line_no'] if mf else '6in min flow'} TO C-101 (MIN. FLOW)"),
                 parent="MAIN")
    fv = tag_of(ins, "FV") or "FV"
    xv = tag_of(ins, "XV")
    fe = tag_of(ins, "FE")
    rating = 300
    F = specs.valve_ftf("cv", nps, rating)
    W = specs.wn_len(nps, rating)
    G = specs.valve_ftf("gate", nps, rating) + 2 * W
    yc = (y_g + y_h) / 2 - 1.0
    dcv = at(r, "MAIN", [hi[0], yc, zg])
    r.add("cv", "MAIN", d=dcv, tag=fv, note="AR flow to H-201")
    r.add("gate", "MAIN", d=dcv - F / 2 - W - G / 2 - 0.02, note="CV block")
    r.add("gate", "MAIN", d=dcv + F / 2 + W + G / 2 + 0.02, note="CV block")
    off = F / 2 + W + G + 0.3 + specs.tee_C(nps)
    r.add_branch("BYP", 6, [V(hi[0], yc + off, zg), V(hi[0] + 0.9, yc + off, zg), V(hi[0] + 0.9, yc - off, zg),
                            V(hi[0], yc - off, zg)], dict(kind="tee"), dict(kind="tee"), parent="MAIN")
    r.add("globe", "BYP", d=r.br("BYP").length / 2, note="CV bypass")
    if fe:
        r.add("fe", "MAIN", d=at(r, "MAIN", [hi[0], yc + off + 1.6, zg]), tag=fe, note="orifice 20D/5D")
    if xv:
        r.add("gate", "MAIN", d=at(r, "MAIN", [hi[0], yc - off - 1.3, zg]), tag=xv, note="SDV (SIF)")
    r.notes += ["Discharge check + block valves in riser above each pump (accessible from grade).",
                "Rack run on tier 1 (hot B2) at rack south edge; expansion loops raised +1.0 m.",
                f"{fv} / FE / XV station at grade (EL {zg:.1f}) north of H-201 for operator access.",
                "Riser at H-201 supported from heater structure with variable spring hangers."]


def r_p101_suction(C):
    r, line = C.route("CFU-100-PI-ISO-005")
    if not r:
        return
    P = C.P
    nps = line["size_in"]
    pa, _ = P.noz("P-101A", "suction")
    pb, _ = P.noz("P-101B", "suction")
    xd = (pa[0] + pb[0]) / 2
    yh = pa[1] + 1.5
    tier = P.tier_for(line)
    y, zc, zx, rk = C.rack(r, line, "MAIN", tier, 0.0, xd, 0.0, yh, prefer="north", above=True)
    zh = 104.0
    src = rk + [V(xd, y, zx), V(xd, yh, zx), V(xd, yh, zh)]
    pump_suction(C, r, line, ("P-101A", "P-101B"), src,
                 dict(kind="bl", label="BATTERY LIMIT - FROM CRUDE TANKAGE (OSBL)", p=[0, y, zc]), y_off=1.5, z_h=zh)
    r.add("gate", "MAIN", d=0.9, tag="BL", note="battery-limit block valve (+ spectacle blind)")
    r.add("spec", "MAIN", d=1.9, tag="SB", note="spectacle blind")
    r.notes += ["Rack high point vented; tank static head gives NPSH margin (check at detailed design).",
                "Header at y = pump nozzle + 1.5 m limited by E-106A/B (layout) - see RPT-001 issues."]


def r_p101_discharge(C):
    r, line = C.route("CFU-100-PI-ISO-006")
    if not r:
        return
    P = C.P
    nps = line["size_in"]
    pa, _ = P.noz("P-101A", "discharge")
    pb, _ = P.noz("P-101B", "discharge")
    ti, _ = P.noz("E-101", "tube_inlet")
    suc = find_line(P.lines, r"(TK|OSBL)", r"^P-101")
    nn = min(specs.step(pump_nozzles(suc["size_in"] if suc else nps), -1), nps)
    zd = 104.0
    x1 = pb[0] + 3.5
    zcv = 101.0
    x2 = x1 + 6.75
    zp = 104.6
    y3 = ti[1] - 1.25
    pts = [V(*pa), V(pa[0], pa[1], zd), V(x1, pa[1], zd), V(x1, pa[1], zcv), V(x2, pa[1], zcv), V(x2, pa[1], zp),
           V(x2, y3, zp), V(ti[0], y3, zp), V(ti[0], y3, 100.35), V(ti[0], ti[1], 100.35), V(*ti)]
    r.add_branch("MAIN", nps, pts, nozzle_conn(C.R, "P-101A", "discharge", nn, "P-101A DISCHARGE"),
                 nozzle_conn(C.R, "E-101", "tube_inlet", nps, "E-101 TUBE INLET"))
    r.add_branch("BR", nps, [V(*pb), V(pb[0], pb[1], zd)], nozzle_conn(C.R, "P-101B", "discharge", nn, "P-101B DISCHARGE"),
                 dict(kind="tee"), parent="MAIN")
    for bid in ("MAIN", "BR"):
        if nn != nps:
            r.add("reducer", bid, at="start", nps=nn, nps2=nps)
        r.add("check", bid, at="start", note="disch. check")
        r.add("gate", bid, at="start", note="disch. block")
    ins = r.instruments
    fv, xv, fe = tag_of(ins, "FV") or "FV", tag_of(ins, "XV"), tag_of(ins, "FE")
    xc = (x1 + x2) / 2
    rating = specs.cls(line["cls"])["rating"]
    F = specs.valve_ftf("cv", nps, rating)
    G = specs.valve_ftf("gate", nps, rating) + 2 * specs.wn_len(nps, rating)
    dcv = at(r, "MAIN", [xc, pa[1], zcv])
    r.add("cv", "MAIN", d=dcv, tag=fv, note="unit charge flow control")
    r.add("gate", "MAIN", d=dcv - F / 2 - specs.wn_len(nps, rating) - G / 2 - 0.02, note="CV block")
    r.add("gate", "MAIN", d=dcv + F / 2 + specs.wn_len(nps, rating) + G / 2 + 0.02, note="CV block")
    off = F / 2 + G + 0.3 + specs.tee_C(nps)
    r.add_branch("BYP", 8, [V(xc - off, pa[1], zcv), V(xc - off, pa[1] - 0.9, zcv), V(xc + off, pa[1] - 0.9, zcv),
                            V(xc + off, pa[1], zcv)], dict(kind="tee"), dict(kind="tee"), parent="MAIN")
    r.add("globe", "BYP", d=r.br("BYP").length / 2, note="CV bypass")
    if xv:
        r.add("gate", "MAIN", d=at(r, "MAIN", [x1, pa[1], (zd + zcv) / 2]), tag=xv, note="SDV (SIF)")
    if fe:
        r.add("fe", "MAIN", d=at(r, "MAIN", [x2, pa[1] + 9.0, zp]), tag=fe, note="orifice, 20D/5D straight")
    for t in ("PI-1200", "PI-1201"):
        pass
    r.notes += ["Crude charge FV-1001 station at grade (EL 101.0) east of P-101B for operator access.",
                "Line passes between E-107 / E-108A and E-108B / E-108C at EL 104.6 (exchanger pipeway).",
                "E-101 bottom inlet only 0.95 m above grade - bottom connection run at EL 100.35 (see issues)."]


def r_bpa_draw(C):
    r, line = C.route("CFU-100-PI-ISO-007")
    if not r:
        return
    P = C.P
    n, _ = P.noz("C-101", "bpa_draw")
    nps = line["size_in"]
    zh = 104.6
    y1 = n[1] - 1.2
    x1 = n[0] - 1.4
    src = [V(*n), V(n[0], y1, n[2]), V(x1, y1, n[2]), V(x1, y1, zh)]
    pa, _ = P.noz("P-108A", "suction")
    yh = pa[1] + 2.4
    src.append(V(x1, yh, zh))
    pump_suction(C, r, line, ("P-108A", "P-108B"), src, nozzle_conn(C.R, "C-101", "bpa_draw", nps,
                                                                     "C-101 BPA DRAW (TRAY 25)"), z_h=zh)
    r.add("gate", "MAIN", at="start", note="column draw isolation")
    tw = tag_of(r.instruments, "TI")
    r.add("olet_branch", "MAIN", d=at(r, "MAIN", [x1, y1, zh + 2.0]), nps_b=1.5, tag=tw or "TW", note="thermowell")
    r.notes += ["Draw turns west to clear BPA return riser and C-101 OH line drop.",
                "Hot pump (345 C): spring support at first support off column; warm-up lines at pumps."]


def r_bpa_return(C):
    r, line = C.route("CFU-100-PI-ISO-008")
    if not r:
        return
    P = C.P
    nps = line["size_in"]
    s, _ = P.noz("E-113", "tube_outlet")
    n, _ = P.noz("C-101", "bpa_return")
    zg = 103.0
    yg = 97.0
    xr = n[0] + 0.95
    yn = n[1] - 1.2
    y, zc, zx, rk = C.rack(r, line, "MAIN", 1, s[0], xr, yg, yn, prefer="south")
    pts = [V(*s), V(s[0], s[1], zg), V(s[0], yg, zg), V(s[0], yg, zx), V(s[0], y, zx)] + rk + \
          [V(xr, y, zx), V(xr, yn, zx), V(xr, yn, n[2]), V(n[0], yn, n[2]), V(*n)]
    r.add_branch("MAIN", nps, pts, nozzle_conn(C.R, "E-113", "tube_outlet", nps, "E-113 TUBE OUTLET"),
                 nozzle_conn(C.R, "C-101", "bpa_return", nps, "C-101 BPA RETURN (TRAY 23)"))
    r.add("gate", "MAIN", at="end", note="column isolation")
    tv = tag_of(r.instruments, "TV") or "TV"
    rating = specs.cls(line["cls"])["rating"]
    F = specs.valve_ftf("cv", nps, rating)
    G = specs.valve_ftf("gate", nps, rating) + 2 * specs.wn_len(nps, rating)
    dcv = at(r, "MAIN", [s[0], (s[1] + yg) / 2, zg])
    r.add("cv", "MAIN", d=dcv, tag=tv, note="BPA return temperature")
    r.add("gate", "MAIN", d=dcv - F / 2 - specs.wn_len(nps, rating) - G / 2 - 0.02, note="CV block")
    r.add("gate", "MAIN", d=dcv + F / 2 + specs.wn_len(nps, rating) + G / 2 + 0.02, note="CV block")
    off = F / 2 + G + 0.3 + specs.tee_C(nps)
    yc = (s[1] + yg) / 2
    r.add_branch("BYP", 6, [V(s[0], yc + off, zg), V(s[0] + 0.85, yc + off, zg), V(s[0] + 0.85, yc - off, zg),
                            V(s[0], yc - off, zg)], dict(kind="tee"), dict(kind="tee"), parent="MAIN")
    r.add("globe", "BYP", d=r.br("BYP").length / 2, note="CV bypass")
    r.notes += ["TV-1045 station on platform at E-113 (EL 103.0) - access by stair from grade.",
                "Riser at C-101 offset 0.95 m east of nozzle to clear BPA draw and P-112 discharge crossings."]


def r_kero_draw(C):
    r, line = C.route("CFU-100-PI-ISO-009")
    if not r:
        return
    P = C.P
    nps = line["size_in"]
    n, _ = P.noz("C-101", "kero_draw")
    f, _ = P.noz("C-102", "feed")
    xd = n[0] + 2.15
    s = 1 / 100.0
    yv = n[1]
    Lh = abs(f[1] - yv) + abs(f[0] - xd)
    z1 = f[2] + s * Lh
    z2 = z1 - s * abs(f[1] - yv)
    pts = [V(*n), V(xd, yv, n[2]), V(xd, yv, z1), V(xd, f[1], z2), V(*f)]
    r.add_branch("MAIN", nps, pts, nozzle_conn(C.R, "C-101", "kero_draw", nps, "C-101 KERO DRAW (TRAY 10)"),
                 nozzle_conn(C.R, "C-102", "feed", nps, "C-102 FEED"))
    r.add("gate", "MAIN", at="start", note="draw isolation")
    r.add("gate", "MAIN", at="end", note="stripper isolation")
    r.slope.append(dict(branch="MAIN", ratio="1:100", note="FALLS TO C-102 (GRAVITY)"))
    r.notes += ["Gravity draw: vertical drop then continuous fall 1:100 to C-102 - no pockets, no rise.",
                "Drop leg 2.15 m east of draw nozzle clears diesel/AGO draw nozzles below (same orientation).",
                "Self-venting: line sized for <= 0.9 m/s; vapour vents back to C-101 via 8\"-PG-100-093."]


def r_d102_suction(C, key, nozzle, pumps, yoff, zh):
    r, line = C.route(key)
    if not r:
        return
    P = C.P
    nps = line["size_in"]
    if nozzle in P.eq["D-102"]["nozzles"]:
        n, _ = P.noz("D-102", nozzle)
        conn = nozzle_conn(C.R, "D-102", nozzle, nps, "D-102 LIQUID OUTLET")
    else:
        lo, _ = P.noz("D-102", "liquid_outlet")
        n = lo.copy()
        n[0] -= 3.0
        P.assumed.append("D-102 second hydrocarbon outlet nozzle assumed 3.0 m west of 'liquid_outlet' "
                         "(layout.json has one; P&ID has separate D-102 to P-103 and D-102 to P-104 lines)")
        conn = dict(kind="nozzle", tag="D-102", nozzle="liquid_outlet_2 (assumed)", nps=nps,
                    label="D-102 LIQUID OUTLET N2 (ASSUMED)", p=n.tolist(), dir=[0, 0, -1])
    pa, _ = P.noz(pumps[0], "suction")
    yh = pa[1] + yoff
    src = [V(*n), V(n[0], n[1], zh), V(n[0], yh, zh)]
    pump_suction(C, r, line, pumps, src, conn, y_off=yoff, z_h=zh)
    r.add("gate", "MAIN", at="start", note="drum isolation")
    r.notes += ["Vortex breaker in D-102 outlet nozzle (by vessel).", "Common header, equal branch to each pump."]


def r_hp_steam(C):
    r, line = C.route("CFU-100-PI-ISO-012")
    if not r:
        return
    P = C.P
    nps = line["size_in"]
    hdr = C.R.headers.get("HS")
    n, _ = P.noz("E-116", "shell_inlet")
    if not hdr:
        P.issues.append("HP steam header not routed - HS-100-134 starts at virtual header")
        hdr = dict(y=P.ry0 + 1.0, zc=P.tiers[3] + 0.2, line_no="HP header")
    xt = n[0] - 1.25
    zt = hdr["zc"] + 1.0
    yv = n[1]
    pts = [V(xt, hdr["y"], hdr["zc"]), V(xt, hdr["y"], zt), V(xt, yv, zt), V(n[0], yv, zt), V(*n)]
    r.add_branch("MAIN", nps, pts, dict(kind="header", ref=hdr["line_no"], label=f"TEE ON {hdr['line_no']} (TOP)"),
                 nozzle_conn(C.R, "E-116", "shell_inlet", nps, "E-116 SHELL INLET"))
    hr = hdr.get("route")
    if hr is not None:
        d = hr.br("MAIN").d_of_point(V(xt, hdr["y"], hdr["zc"]), tol=0.05)
        if d is not None:
            hr.add("olet_branch", "MAIN", d=d, nps_b=nps, tag="TEE", note=f"branch {line['line_no']}")
    r.add("gate", "MAIN", d=at(r, "MAIN", [xt, hdr["y"] + 1.6, zt]), note="header isolation (top take-off)")
    r.add("globe", "MAIN", d=at(r, "MAIN", [xt, yv - 2.0, zt]), note="warm-up / throttling")
    r.add("olet_branch", "MAIN", d=at(r, "MAIN", [xt, yv - 3.4, zt]), nps_b=1.0, tag="ST", note="drip leg + steam trap")
    r.notes += ["Branch taken from top of HP header; line falls to E-116 - drains into shell (no pocket).",
                "S2 (P11) - PWHT and 100 % RT; hot bolting check at 430 C."]


def build_all(R):
    from . import auto
    auto.route_headers(R)
    C = Ctx(R)
    r_h101_transfer(C)
    r_h201_transfer(C)
    r_c101_overhead(C)
    r_c101_bottoms(C)
    r_p112_discharge(C)
    r_p101_suction(C)
    r_p101_discharge(C)
    r_bpa_draw(C)
    r_bpa_return(C)
    r_kero_draw(C)
    r_d102_suction(C, "CFU-100-PI-ISO-010", "liquid_outlet_2", ("P-103A", "P-103B"), 2.8, 103.8)
    r_d102_suction(C, "CFU-100-PI-ISO-011", "liquid_outlet", ("P-104A", "P-104B"), 2.1, 103.0)
    r_hp_steam(C)
    for r in R.routes:
        if r.level == "critical":
            vents_drains(r, skip=("HDR", "BYP", "MF") + tuple(f"PASS{k}" for k in range(1, 10)))
