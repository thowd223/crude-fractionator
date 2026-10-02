"""Cable schedule: main feeders + every motor / consumer cable, with protective device, CT and relays."""
from __future__ import annotations

import math

from . import common as C
from .loads import B4, B13, BLV
from .study import lv_start_dip, mv_start_dip, size_cable

SS_LOCAL = 20.0           # m, consumer inside SS-100 (incl. allowance)
MSS_FEEDER_M = 600.0      # m, assumed route from refinery main substation to SS-100 (OSBL, to be confirmed)

LOC = {  # non-equipment consumers -> location key (fallback point) or 'SS'/'FAR'
    "HVAC-101": "SS", "BEF-101": "SS", "UPS-101": "SS", "BC-101": "SS", "LTR-101": "SS",
    "HVAC-102": "FAR", "HTP-101": "CDU_P", "HTP-102": "VDU_P", "CP-101": "DESALT", "AH-101": "CDU",
    "HST-101": "DESALT_P", "SB-101": "H101", "MOV-A": "PLOT", "MOV-B": "PLOT", "WR-A": "PLOT", "WR-B": "PLOT",
}


def _fmt(sz):
    return f"{sz:g}"


def designation(kind, size, runs, vfd=False):
    if kind == "HV":
        return f"{runs} x (3 x 1C x {_fmt(size)} mm2) Cu/XLPE/CWS/PVC 8.7/15 kV, trefoil"
    if kind == "MV1":
        return f"{runs} x (3 x 1C x {_fmt(size)} mm2) Cu/XLPE/CWS/PVC 3.6/6 kV, trefoil"
    if kind == "MV":
        return (f"{runs} x " if runs > 1 else "") + f"3C x {_fmt(size)} mm2 Cu/XLPE/CWS/SWA/PVC 3.6/6 kV"
    e = C.earth_size(size)
    if vfd:
        return (f"{runs} x " if runs > 1 else "") + f"3C x {_fmt(size)} + 3E x {_fmt(C.earth_size(size / 3) if size > 16 else max(size / 3, 2.5))} mm2 " \
            "Cu/XLPE/CWS/SWA/PVC 0.6/1 kV, symmetrical VFD cable"
    return (f"{runs} x " if runs > 1 else "") + f"3C x {_fmt(size)} + E{_fmt(e)} mm2 Cu/XLPE/SWA/PVC 0.6/1 kV"


def mv_relays(r):
    if r["vfd"]:
        return "50/51, 50N/51N, 27, 86 (motor protection in VFD: 49, 46, 37)"
    devs = ["50/51", "50G", "46", "49", "27", "66", "86"]
    if r["rated_kw"] >= 500:
        devs.insert(4, "87M")
    return ", ".join(devs)


def build(rows, R, loc):
    sc4 = R["sc"]["worst_kA"]["4.16 kV"]
    sc13 = R["sc"]["worst_kA"]["13.8 kV"]
    sc48 = R["sc"]["worst_kA"]["0.48 kV"]
    trm, trl = R["tr_mv"], R["tr_lv"]
    out = []
    issues = []

    def add(**k):
        k.setdefault("notes", "")
        out.append(k)

    # ------------------------------------------------------------------ main feeders
    for s, ab in enumerate("AB"):
        I = trm["I_pri_onaf_A"]
        c = size_cable(kv=C.KV_UT, I_des=I * 1.0, I_run=I, pf=0.9, L=MSS_FEEDER_M, kind="HV", sc_kA=C.UT_FAULT_KA,
                       t_s=0.5, single_core=True)
        add(tag=f"CBL-INC-{ab}", frm="Refinery main substation (OSBL)", to=f"{B13[s]} incomer", kV=C.KV_UT,
            service="13.8 kV incomer", I_A=I, L_m=MSS_FEEDER_M, cable=designation("HV", c["size"], c["runs"]), **_c(c),
            device="VCB 1200 A (both ends)", notes="Length assumed (OSBL route TBC); sized for full unit load "
            "on one incomer (ONAF rating of one transformer)", length_src="assumed")
        c = size_cable(kv=C.KV_UT, I_des=I, I_run=I, pf=0.9, L=30, kind="HV", sc_kA=sc13, t_s=0.5, single_core=True)
        add(tag=f"CBL-TR-10{s + 1}-P", frm=B13[s], to=f"TR-10{s + 1} primary", kV=C.KV_UT, service="Transformer feeder",
            I_A=I, L_m=30.0, cable=designation("HV", c["size"], c["runs"]), **_c(c), device="VCB 1200 A",
            length_src="SS-100 yard")
        I2 = trm["I_sec_onaf_A"]
        c = size_cable(kv=C.KV_MV, I_des=I2, I_run=I2, pf=0.9, L=25, kind="HV", sc_kA=sc4, t_s=0.5, single_core=True)
        add(tag=f"CBL-TR-10{s + 1}-S", frm=f"TR-10{s + 1} secondary", to=f"{B4[s]} incomer", kV=C.KV_MV,
            service="Transformer secondary", I_A=I2, L_m=25.0, cable=designation("MV1", c["size"], c["runs"]), **_c(c),
            device=f"VCB {C.std_up(I2 * 1.0, [1200, 2000, 3000])} A", length_src="SS-100 yard",
            notes="Alternative: 5 kV cable bus / non-segregated bus duct")
        I3 = trl["I_pri_onaf_A"]
        c = size_cable(kv=C.KV_MV, I_des=I3, I_run=I3, pf=0.9, L=30, kind="MV", sc_kA=sc4, t_s=0.5)
        add(tag=f"CBL-TR-10{s + 3}-P", frm=B4[s], to=f"TR-10{s + 3} primary", kV=C.KV_MV, service="Transformer feeder",
            I_A=I3, L_m=30.0, cable=designation("MV", c["size"], c["runs"]), **_c(c), device="VCB 1200 A",
            length_src="SS-100 yard")
        I4 = trl["I_sec_onaf_A"]
        add(tag=f"BD-TR-10{s + 3}-S", frm=f"TR-10{s + 3} secondary", to=f"{BLV[s]} incomer", kV=C.V_LV / 1000,
            service="Transformer secondary", I_A=I4, L_m=15.0,
            cable=f"Non-segregated phase bus duct {C.std_up(I4, C.BUS_A)} A, Cu, {R['swgr']['MCC-101']['kA']:g} kA",
            size=None, runs=1, ampacity=C.std_up(I4, C.BUS_A), vd_run=0.1, vd_start=None, term_dip=None,
            s_sc_min=None, device=f"ACB {C.std_up(I4, C.BUS_A)} A", length_src="SS-100 yard", R_ohm=0, X_ohm=0)

    # ------------------------------------------------------------------ consumers
    groups_208 = {}
    for r in rows:
        if r["volt"] == 208:
            groups_208.setdefault(r["bus"], []).append(r)
    for r in rows:
        if r["volt"] == 208:
            continue
        mv = r["volt"] > 1000
        V = r["volt"]
        if r["kind"] == "motor":
            eff, pf = C.motor_eff_pf(r["rated_kw"], mv)
            I = r["rated_kw"] * 1000 / (math.sqrt(3) * V * eff * pf)
            if r["vfd"]:
                I_in = r["rated_kw"] * 1000 / (math.sqrt(3) * V * eff * C.VFD_EFF * C.VFD_PF)
        else:
            kva = r["kva_rated"] or (r["rated_kw"] / r["eff"] / r["pf"])
            I = kva * 1000 / (math.sqrt(3) * V)
            pf = r["pf"]
        key = r["eq"] or r["tag"]
        k2 = next((k for k in LOC if r["tag"].startswith(k)), None)
        extra = C.RACK_TOP_EXTRA_M if r["group"] == "Air-cooler fans" else 0.0
        if k2:
            where = LOC[k2]
            if where == "SS":
                L, src = SS_LOCAL, "inside SS-100"
            elif where == "FAR":
                L = abs(loc.far[0] - loc.ss[0]) + abs(loc.far[1] - loc.ss[1]) + C.RISER_M
                L, src = round(L / 5 + 0.4999) * 5.0, "FAR-100"
            else:
                (x, y) = C.AREA_PTS[where]
                L = abs(x - loc.ss[0]) + abs(y - loc.ss[1]) + C.RISER_M
                L, src = round(L / 5 + 0.4999) * 5.0, "area:" + where
        else:
            L, src = loc.route(r["tag"] if r["kind"] == "motor" else key, extra)
            if src.startswith("area:") and loc.xy:
                issues.append(f"{r['tag']}: not found in data/layout.json - area-block location used")
        dol = r["kind"] == "motor" and not r["vfd"]
        if mv:
            dip = mv_start_dip(R, r["bus"], r["rated_kw"], eff, pf, r["kva"] if r["duty"] == "C" else 0) if dol else 0
            c = size_cable(kv=C.KV_MV, I_des=1.25 * I, I_run=I, pf=pf, L=L, kind="MV", sc_kA=sc4, t_s=0.25,
                           start_mult=C.LRC if dol else None, start_pf=C.LR_PF, bus_dip=dip)
            ct = C.std_up(I * 1.25, C.CT_PRI)
            dev = (f"VCB 1200 A + VFD-{r['tag']} (MV drive, 18-pulse/AFE)" if r["vfd"] else "VCB 1200 A, DOL")
            add(tag=f"CBL-{r['tag']}", frm=r["bus"] if not r["vfd"] else f"VFD-{r['tag']}", to=r["tag"], kV=C.KV_MV,
                service=r["desc"], I_A=I, L_m=L, cable=designation("MV", c["size"], c["runs"]), **_c(c), device=dev,
                ct=f"{ct}/5 A", relays=mv_relays(r), bus_dip=dip if dol else None, length_src=src, load=r["tag"])
            r.update(cable_R=c["R_ohm"], cable_X=c["X_ohm"], ct=f"{ct}/5 A", relays=mv_relays(r), I_fl=I)
        else:
            dip = lv_start_dip(R, r["bus"], r["rated_kw"], eff, pf) if dol else 0.0
            if r["kind"] == "motor":
                mccb = C.std_up(1.75 * I if dol else 1.25 * I_in, C.NEC_A)
                mccb = max(mccb, 15)
                if dol and mccb > 2.5 * I and C.std_up(2.5 * I, C.NEC_A) < mccb:
                    mccb = C.std_up(2.5 * I, C.NEC_A)
            else:
                mccb = max(C.std_up(1.25 * I, C.NEC_A), 15)
            frame = C.std_up(mccb, C.MCCB_FRAMES)
            i2t = C.LET_THROUGH and next((e for lim, e in C.LET_THROUGH if mccb <= lim), None)
            if i2t is None:
                i2t = (sc48 * 1e3) ** 2 * 0.05
            Ides = 1.25 * (I_in if r["vfd"] else I)
            c = size_cable(kv=C.V_LV / 1000, I_des=Ides, I_run=I, pf=pf, L=L, kind="LV", sc_kA=sc48, i2t=i2t,
                           start_mult=C.LRC if dol else None, start_pf=C.LR_PF_LV, bus_dip=dip)
            if c is None:
                issues.append(f"{r['tag']}: no LV cable meets criteria at {L} m")
                continue
            if r["kind"] == "motor":
                st = "VFD (6-pulse + harmonic filter)" if r["vfd"] else ("DOL, NEMA size " + _nema(r["rated_kw"]))
                dev = f"MCCB {mccb} A ({frame} AF) + {st}"
            elif r["tag"].startswith("DT-"):
                dev = f"MCCB {mccb} A ({frame} AF) - desalter transformer feeder"
            else:
                dev = f"MCCB {mccb} A ({frame} AF)"
            add(tag=f"CBL-{r['tag']}", frm=r["bus"] if not r["vfd"] else f"VFD-{r['tag']}", to=r["tag"],
                kV=C.V_LV / 1000, service=r["desc"], I_A=I, L_m=L,
                cable=designation("LV", c["size"], c["runs"], r["vfd"]), **_c(c), device=dev,
                bus_dip=dip if dol else None, length_src=src, load=r["tag"])
            r.update(mccb=mccb, frame=frame, I_fl=I, cable_size=c["size"], cable_runs=c["runs"])
    # lighting transformers (208 V consumers grouped)
    for s, ab in enumerate("AB"):
        lt = R["ltr"][ab]
        I = lt["kva"] * 1000 / (math.sqrt(3) * C.V_LV)
        mccb = C.std_up(1.25 * I, C.NEC_A)
        c = size_cable(kv=0.48, I_des=1.25 * I, I_run=I, pf=0.95, L=SS_LOCAL, kind="LV", sc_kA=sc48,
                       i2t=next(e for lim, e in C.LET_THROUGH if mccb <= lim))
        add(tag=f"CBL-LTR-101{ab}", frm=BLV[s], to=f"LTR-101{ab} ({lt['kva']:g} kVA 480-208Y/120 V)", kV=0.48,
            service="Lighting & small-power transformer -> LDB-101" + ab, I_A=I, L_m=SS_LOCAL,
            cable=designation("LV", c["size"], c["runs"]), **_c(c), device=f"MCCB {mccb} A (125 AF)",
            length_src="inside SS-100", load=f"LTR-101{ab}")
        lt["mccb"] = mccb
    for i, k in enumerate(out, 1):
        k["no"] = i
    return out, issues


def _nema(kw):
    hp = kw / 0.746
    for sz, lim in (("0", 10), ("1", 15), ("2", 25), ("3", 50), ("4", 100), ("5", 200), ("6", 400)):
        if hp <= lim:
            return sz
    return "7"


def _c(c):
    return {k: c[k] for k in ("size", "runs", "ampacity", "vd_run", "vd_start", "term_dip", "s_sc_min", "R_ohm",
                              "X_ohm")}
