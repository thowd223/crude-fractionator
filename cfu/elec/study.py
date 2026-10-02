"""Power-system sizing studies (FEED level): demand roll-up, transformers, short circuit, motor starting,
cable sizing, UPS / battery.  Simplified IEEE 141/399 hand-calculation methods; per-unit on 100 MVA base."""
from __future__ import annotations

import cmath
import math

from . import common as C
from .loads import B4, B13, BLV, BUPS, demand

BASE_MVA = 100.0


def zpu(mag, xr):
    """Complex impedance of magnitude mag with X/R ratio."""
    ang = math.atan(xr)
    return cmath.rect(mag, ang)


def ibase(kv):
    return BASE_MVA * 1e3 / (math.sqrt(3) * kv)    # A


def zbase(kv):
    return kv ** 2 / BASE_MVA                      # ohm


def kappa(xr):
    return 1.02 + 0.98 * math.exp(-3.0 / xr)


def par(*zs):
    return 1.0 / sum(1.0 / z for z in zs if z)


# ---------------------------------------------------------------------------- transformers
def size_tx(md_kva, name, pri_kv, sec_kv, z_pct, xr, limit_kva=None):
    """ONAN rating >= contingency MD (both sections on one transformer); ONAF (fans, +25 %) >= MD x 1.25
    (25 % future margin); ONAN loading at MD kept <= 95 %."""
    for s in C.TX_STD_KVA:
        onaf = s * C.ONAF_FACTOR[s <= 10000]
        if s >= md_kva / 0.95 and onaf >= md_kva * C.FUTURE:
            break
    onaf = s * C.ONAF_FACTOR[s <= 10000]
    return dict(tag=name, pri_kV=pri_kv, sec_kV=sec_kv, onan_kVA=s, onaf_kVA=round(onaf), z_pct=z_pct, xr=xr,
                md_kVA=md_kva, req_onaf_kVA=md_kva * C.FUTURE, load_onan_pct=100 * md_kva / s,
                load_onaf_future_pct=100 * md_kva * C.FUTURE / onaf,
                I_sec_onaf_A=onaf / (math.sqrt(3) * sec_kv), I_pri_onaf_A=onaf / (math.sqrt(3) * pri_kv),
                vector="Dyn1" if sec_kv > 1 else "Dyn1",
                grounding=("Low-resistance grounded, NGR 400 A / 10 s" if sec_kv > 1
                           else "High-resistance grounded, NGR 5 A (continuous), ground-fault alarm"),
                cooling="ONAN/ONAF", type="Oil-immersed, outdoor, off-circuit tap changer +/-2 x 2.5 %")


def run(rows, ups_rows):
    R: dict = {"assumptions": [], "notes": []}
    md = {b: demand(rows, b) for b in BLV + B4}
    md_lv_total = demand([r for r in rows if r["bus"] in BLV])
    md_mv_total = demand([r for r in rows if r["bus"] in B4])

    # ---- LV transformers TR-103/104 (4.16/0.48 kV)
    tr_lv = size_tx(md_lv_total["kVA"], "TR-103 / TR-104", C.KV_MV, C.V_LV / 1000, 5.75, 6.0)
    # lighting transformers
    ltr = {}
    for s, ab in enumerate("AB"):
        kva = sum(r["kva"] * (1 if r["duty"] == "C" else 0.3) for r in rows
                  if r["bus"] == BLV[s] and r["volt"] == 208)
        ltr[ab] = dict(tag=f"LTR-101{ab}", kva_load=kva, kva=C.std_up(kva * C.FUTURE, [30, 45, 75, 112.5, 150]))

    # ---- 4.16 kV bus roll-up (MV loads + LV transformer through-load + 1 % LV transformer losses)
    def lvthrough(d):
        return complex(d["kW"] * 1.01, d["kvar"] * 1.04)

    bus4 = {}
    for s in (0, 1):
        mv = md[B4[s]]
        lv = lvthrough(md[BLV[s]])
        tot = complex(mv["kW"], mv["kvar"]) + lv
        bus4[B4[s]] = dict(mv_kW=mv["kW"], mv_kvar=mv["kvar"], lv_kW=lv.real, lv_kvar=lv.imag, kW=tot.real,
                           kvar=tot.imag, kVA=abs(tot))
    tot4 = complex(md_mv_total["kW"], md_mv_total["kvar"]) + lvthrough(md_lv_total)
    tr_mv = size_tx(abs(tot4), "TR-101 / TR-102", C.KV_UT, C.KV_MV, 7.0, 14.0)
    bus13 = {}
    for s in (0, 1):
        b = bus4[B4[s]]
        t = complex(b["kW"] * 1.008, b["kvar"] * 1.06)
        bus13[B13[s]] = dict(kW=t.real, kvar=t.imag, kVA=abs(t))
    t13 = complex(tot4.real * 1.008, tot4.imag * 1.06)
    R.update(md=md, md_lv_total=md_lv_total, md_mv_total=md_mv_total, bus4=bus4, bus13=bus13,
             total=dict(kW=t13.real, kvar=t13.imag, kVA=abs(t13), pf=t13.real / abs(t13)),
             tr_lv=tr_lv, tr_mv=tr_mv, ltr=ltr)

    # ---- network impedances (pu, 100 MVA)
    s_ut = math.sqrt(3) * C.KV_UT * C.UT_FAULT_KA            # MVA
    Zut = zpu(BASE_MVA / s_ut, C.UT_XR)
    Ztm = zpu(tr_mv["z_pct"] / 100 * BASE_MVA / (tr_mv["onan_kVA"] / 1000), tr_mv["xr"])
    Ztl = zpu(tr_lv["z_pct"] / 100 * BASE_MVA / (tr_lv["onan_kVA"] / 1000), tr_lv["xr"])
    R["net"] = dict(S_utility_MVA=s_ut, Zut=Zut, Ztm=Ztm, Ztl=Ztl)

    def motor_kva(rs):
        return sum(r["rated_kw"] / (r["eff"] * (C.motor_eff_pf(r["rated_kw"], r["volt"] > 1000)[1]))
                   for r in rs if r["kind"] == "motor" and r["duty"] == "C")

    sc = {}
    for case, secs in (("normal (tie open)", ((0,), (1,))), ("one transformer, tie closed", ((0, 1),))):
        for grp in secs:
            mvm = motor_kva([r for r in rows if r["bus"] in [B4[s] for s in grp] and not r["vfd"]])
            lvm = motor_kva([r for r in rows if r["bus"] in [BLV[s] for s in grp] and not r["vfd"]])
            Zm_mv = zpu(C.XD2 * BASE_MVA / (mvm / 1000), 20) if mvm else None
            Zm_lv = zpu(0.25 * BASE_MVA / (lvm / 1000), 6) if lvm else None   # 4 x FLA aggregate (IEEE 141)
            z_lvm = (Zm_lv + Ztl) if Zm_lv else None
            z13 = par(Zut, Ztm + par(Zm_mv, z_lvm))
            z4 = par(Zut + Ztm, Zm_mv, z_lvm)
            z48 = par(par(Zut + Ztm, Zm_mv) + Ztl, Zm_lv)
            key = case + ("" if len(grp) == 2 else f" - section {'AB'[grp[0]]}")
            sc[key] = {}
            for lbl, z, kv in (("13.8 kV", z13, C.KV_UT), ("4.16 kV", z4, C.KV_MV), ("0.48 kV", z48, C.V_LV / 1000)):
                ik = ibase(kv) / abs(z) / 1000
                xr = z.imag / z.real
                sc[key][lbl] = dict(Ik_kA=ik, XR=xr, ip_kA=kappa(xr) * math.sqrt(2) * ik)
            sc[key]["motor_kVA"] = dict(MV=mvm, LV=lvm)
    worst = {lv: max(v[lv]["Ik_kA"] for v in sc.values()) for lv in ("13.8 kV", "4.16 kV", "0.48 kV")}
    worst_ip = {lv: max(v[lv]["ip_kA"] for v in sc.values()) for lv in ("13.8 kV", "4.16 kV", "0.48 kV")}
    rating = {"13.8 kV": C.std_up(max(worst["13.8 kV"] * 1.1, C.UT_FAULT_KA * 1.1), C.SWGR_KA[C.KV_UT]),
              "4.16 kV": C.std_up(worst["4.16 kV"] * 1.1, C.SWGR_KA[C.KV_MV]),
              "0.48 kV": C.std_up(worst["0.48 kV"] * 1.1, C.SWGR_KA[C.V_LV / 1000])}
    R["sc"] = dict(cases=sc, worst_kA=worst, worst_ip_kA=worst_ip, rating_kA=rating)

    # ---- switchgear bus ratings
    R["swgr"] = {
        "SWG-101": dict(kV=C.KV_UT, bus_A=C.std_up(tr_mv["I_pri_onaf_A"] * 1.25, [1200, 2000, 3000]),
                        kA=rating["13.8 kV"], bil="95 kV", type="Metal-clad, drawout VCB (IEEE C37.20.2)"),
        "SWG-102": dict(kV=C.KV_MV, bus_A=C.std_up(tr_mv["I_sec_onaf_A"] * 1.1, [1200, 2000, 3000]),
                        kA=rating["4.16 kV"], bil="60 kV", type="Metal-clad, drawout VCB (IEEE C37.20.2), arc-resistant Type 2B"),
        "MCC-101": dict(kV=C.V_LV / 1000, bus_A=C.std_up(tr_lv["I_sec_onaf_A"] * 1.0, C.BUS_A),
                        kA=rating["0.48 kV"], type="LV switchgear (ACB incomers/tie, IEEE C37.20.1) + MCC sections "
                                                  "(UL 845), withdrawable buckets"),
    }

    # ---- motor starting (largest DOL MV motor)
    R["start"] = motor_start_cases(rows, R)
    return R


# ---------------------------------------------------------------------------- motor starting
def _start(Zs, pre_kva, pre_pf, mot_kw, eff, pf, kv, Zc_ohm, lrc=C.LRC, lr_pf=C.LR_PF):
    """Returns (bus_V, term_V) during locked rotor; pre-start bus voltage set to 1.0 pu (tap)."""
    S_fl = mot_kw / (eff * pf) / 1000                    # MVA
    S_lr = lrc * S_fl
    Zm = cmath.rect(BASE_MVA / S_lr, math.acos(lr_pf))
    Zc = Zc_ohm / zbase(kv)
    # pre-start load as constant impedance at 1.0 pu
    if pre_kva > 0:
        Sl = cmath.rect(pre_kva / 1000 / BASE_MVA, math.acos(pre_pf))
        Zl = 1.0 / Sl.conjugate()
    else:
        Zl = None
    zpar_pre = Zl if Zl else 1e9
    E = abs(1.0 * (Zs + zpar_pre) / zpar_pre)            # source emf giving 1.0 pu bus pre-start
    zload = par(Zl, Zc + Zm) if Zl else (Zc + Zm)
    Vb = E * abs(zload / (Zs + zload))
    Vt = Vb * abs(Zm / (Zc + Zm))
    return Vb, Vt, S_lr * 1000


def motor_start_cases(rows, R):
    net = R["net"]
    big = max((r for r in rows if r["volt"] > 1000 and not r["vfd"]), key=lambda r: r["rated_kw"])
    out = []
    for case, Zs, pre in (
            ("Normal: tie open, motor bus section on its own transformer", net["Zut"] + net["Ztm"],
             R["bus4"][big["bus"]]),
            ("Contingency: one 13.8/4.16 kV transformer feeding both sections, largest motor started last",
             net["Zut"] + net["Ztm"], dict(kVA=sum(b["kVA"] for b in R["bus4"].values()),
                                          kW=sum(b["kW"] for b in R["bus4"].values()))),
            ("Contingency + one 13.8 kV incomer (utility fault level reduced to 20 kA assumed)",
             zpu(BASE_MVA / (math.sqrt(3) * C.KV_UT * 20.0), C.UT_XR) + net["Ztm"],
             dict(kVA=sum(b["kVA"] for b in R["bus4"].values()), kW=sum(b["kW"] for b in R["bus4"].values())))):
        pre_kva = pre["kVA"]
        if case.startswith("Normal") and big["duty"] == "C":
            # running motor not part of the pre-start load
            pre_kva = max(pre_kva - big["kva"], 0)
        elif not case.startswith("Normal"):
            pre_kva = max(pre_kva - big["kva"], 0)
        pf = pre["kW"] / pre["kVA"]
        Zc = (big.get("cable_R", 0.0) + 1j * big.get("cable_X", 0.0))
        Vb, Vt, Slr = _start(Zs, pre_kva, pf, big["rated_kw"], big["eff"], C.motor_eff_pf(big["rated_kw"], True)[1],
                             C.KV_MV, Zc)
        out.append(dict(case=case, motor=big["tag"], kW=big["rated_kw"], LR_kVA=Slr, pre_kVA=pre_kva,
                        bus_dip_pct=100 * (1 - Vb), term_dip_pct=100 * (1 - Vt),
                        ok=(1 - Vb) <= 0.10 and (1 - Vt) <= 0.15))
    return out


# ---------------------------------------------------------------------------- cables
def let_through(a):
    for lim, e in C.LET_THROUGH:
        if a <= lim:
            return e
    return None


def size_cable(*, kv, I_des, I_run, pf, L, kind, sc_kA, t_s=None, i2t=None, start_mult=None, start_pf=None,
               bus_dip=0.0, single_core=False, vd_lim=5.0, st_lim=15.0, min_size=None):
    """Return dict with selected cores x size, runs, ampacity, VD running / starting, SC minimum."""
    if kind == "HV" or single_core:
        table = C.AMP_HV
    elif kind == "MV":
        table = C.AMP_MV
    else:
        table = C.AMP_LV
    der = C.DERATE["ambient"] * C.DERATE["group"]
    if i2t is None and t_s:
        i2t = (sc_kA * 1e3) ** 2 * t_s
    s_sc = math.sqrt(i2t) / C.K_XLPE if i2t else 0.0
    mn = max(min_size or (C.LV_MIN_MM2 if kind == "LV" else C.MV_MIN_MM2 if kind == "MV" else 70), 0)
    V = kv * 1000
    best = None
    for n in range(1, 13):
        for s, amp in sorted(table.items()):
            if s < mn or s < s_sc:
                continue
            cap = amp * der * n
            if cap < I_des:
                continue
            R = C.R90[s] * L / 1000 / n
            X = C.X_km(s, kind if not single_core else "HV") * L / 1000 / n
            sin = math.sqrt(1 - pf ** 2)
            vd = 100 * math.sqrt(3) * I_run * (R * pf + X * sin) / V
            vds = None
            if start_mult:
                ss = math.sqrt(1 - start_pf ** 2)
                vds = 100 * math.sqrt(3) * I_run * start_mult * (R * start_pf + X * ss) / V
            if vd > vd_lim or (vds is not None and bus_dip + vds > st_lim):
                continue
            best = dict(size=s, runs=n, ampacity=cap, vd_run=vd, vd_start=vds, term_dip=(bus_dip + vds) if vds
                        is not None else None, s_sc_min=s_sc, R_ohm=R, X_ohm=X, derate=der)
            break
        if best:
            break
        if kind == "LV" and n == 1:
            mn = max(mn, 95)          # parallel LV runs: minimum 95 mm2 per run
    return best


def lv_start_dip(R, bus, mot_kw, eff, pf):
    """Bus voltage dip on MCC section when starting an LV DOL motor (normal configuration)."""
    net = R["net"]
    pre = R["md"][bus]
    Vb, _, _ = _start(net["Zut"] + net["Ztm"] + net["Ztl"], pre["kVA"], pre["pf"], mot_kw, eff, pf, C.V_LV / 1000,
                      0, lr_pf=C.LR_PF_LV)
    return 100 * (1 - Vb)


def mv_start_dip(R, bus, mot_kw, eff, pf, kva_self):
    net = R["net"]
    pre = R["bus4"][bus]
    Vb, _, _ = _start(net["Zut"] + net["Ztm"], max(pre["kVA"] - kva_self, 0), pre["kW"] / pre["kVA"], mot_kw, eff,
                      pf, C.KV_MV, 0)
    return 100 * (1 - Vb)


# ---------------------------------------------------------------------------- UPS / battery
def ups_dc(ups_rows):
    load = sum(r["kva_rated"] for r in ups_rows) / 2          # each consumer listed for A and B feeds
    fut = load * 1.20
    rating = C.std_up(fut / 0.80, [40, 60, 80, 100, 120, 160, 200])
    p_dc = fut * 0.9 / 0.94                                   # kW at battery (PF 0.9, inverter eff 94 %)
    cells, v_end = 192, 1.75
    I_max = p_dc * 1000 / (cells * v_end)
    Kt = 1.10                                                 # Ah per A for 30 min to 1.75 V/cell (VRLA, 25 C)
    aging, margin, temp = 1.25, 1.10, 1.0
    ah = I_max * Kt * aging * margin * temp
    ah_sel = C.std_up(ah, [100, 150, 200, 250, 300, 350, 400, 500, 600, 800, 1000])
    ups = dict(load_kVA=load, design_kVA=fut, rating_kVA=rating, config="2 x 100 % parallel-redundant, each with "
               "own battery, static bypass and external maintenance bypass", input="480 V 3-ph 60 Hz (from MCC-101A/B)",
               output="208Y/120 V 3-ph, 120 V 1-ph distribution, 60 Hz", autonomy_min=30, battery_kW=p_dc,
               cells=cells, v_float=cells * 2.25, v_nom=cells * 2.0, v_end=cells * v_end, I_max_A=I_max, Kt=Kt,
               aging=aging, margin=margin, temp=temp, ah_req=ah, ah_sel=ah_sel,
               battery_type="VRLA, 2 V cells, 20-yr design life, in ventilated battery room in SS-100")
    # 125 V DC switchgear control (IEEE 485 duty cycle)
    L1, L2, L3 = 60.0, 15.0, 40.0          # A: 1-min trip of all breakers / standing / 1-min closing+spring
    Kt1, Kt120, Kt119, Kt121 = 0.55, 2.35, 2.34, 2.36
    s1 = L1 * Kt1
    s2 = L1 * Kt120 + (L2 - L1) * Kt119
    s3 = L1 * Kt121 + (L2 - L1) * Kt120 + (L3 - L2) * Kt1
    f = max(s1, s2, s3)
    ah_dc = f * 1.25 * 1.10
    dc = dict(V=125, cells=60, duty="L1 60 A 1 min (trip) / L2 15 A 120 min standing / L3 40 A 1 min (close)",
              sections=(s1, s2, s3), F=f, ah_req=ah_dc, ah_sel=C.std_up(ah_dc, [50, 75, 100, 150, 200, 300]),
              autonomy_h=2.0, chargers="2 x 100 %, 30 A each (standing load + recharge in 8 h)",
              config="2 x 100 % chargers, 2 x 100 % batteries, DCDB-101 with A/B sections")
    return dict(ups=ups, dc=dc)
