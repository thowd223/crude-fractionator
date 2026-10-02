"""Heat & material balance for the CDU/VDU (cut-point model with equilibrium flash zones).

Method summary (documented in deliverables/00-basis/process-design-basis):
  * Products are defined by TBP cut points with sigmoid overlap ("sloppy split").
  * Atmospheric / vacuum flash zones: equilibrium flash with stripping steam as inert;
    flash-zone temperature solved so vapour = distillates + specified overflash.
  * Draw temperatures: product bubble point at tray hydrocarbon partial pressure.
  * Column heat removal = overall enthalpy balance; distributed between reflux and
    pumparounds per basis split; internal reflux by envelope balances.
  * Stabiliser and naphtha splitter: Fenske-Underwood-Gilliland short-cut.
  * Preheat train: sequential counter-current exchangers with min. approach.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq

from . import assay, basis
from .thermo import STEAM, Slate, bubble_T, dew_T, enthalpy, flash_TP, steam_h, water_psat

D = basis.DESIGN
LB_BBL_TO_KG_M3 = 0.45359237 / assay.BBL_M3


# ---------------------------------------------------------------------------
@dataclass
class Stream:
    no: str
    name: str
    m: np.ndarray                 # hydrocarbon kg/h per component
    T: float                      # degC
    P: float                      # bar(a)
    water: float = 0.0            # liquid water kg/h
    steam: float = 0.0            # water vapour kg/h
    frm: str = ""
    to: str = ""
    phase: str = "L"              # L, V, M (mixed) or W
    vf: float | None = None       # HC vapour mass fraction (computed if None)
    q_kw: float | None = None     # for duty-only "streams"
    gas: float = 0.0              # non-hydrocarbon-slate gas (fuel gas, NCG/air), kg/h
    gas_mw: float = 20.0

    def total(self):
        return float(self.m.sum() + self.water + self.steam + self.gas)


class Model:
    def __init__(self):
        self.sl: Slate = assay.build_slate()
        self.crude = assay.crude_mass_vector(self.sl)
        self.S: dict[str, Stream] = {}
        self.res: dict = {}
        self.warn: list[str] = []

    # helpers ---------------------------------------------------------------
    def vol(self, m):  # m3/h at 15 degC
        return float((m / (self.sl.SG * 999.0)).sum())

    def mw(self, m):
        return float(m.sum() / (m / self.sl.MW).sum()) if m.sum() > 0 else 0.0

    def hl(self, m, T):
        return float((m * self.sl.hl(T)).sum()) / 3600

    def hv(self, m, T):
        return float((m * self.sl.hv(T)).sum()) / 3600

    def lam(self, m, T):
        """kJ/kg mixture latent heat (consistent with enthalpy model)."""
        return float((m * (self.sl.hv(T) - self.sl.hl(T))).sum() / m.sum())

    def T_from_hl(self, m, H_kw, water=0.0, lo=0.0, hi=500.0):
        return brentq(lambda T: self.hl(m, T) + water * 4.19 * (T - 15) / 3600 - H_kw, lo, hi)

    def add(self, s: Stream):
        self.S[s.no] = s
        return s

    @staticmethod
    def sigmoid_split(Tb, cuts, widths):
        s = [1 / (1 + np.exp(np.clip((Tb - c) / w, -60, 60))) for c, w in zip(cuts, widths)]
        fr = [s[0]] + [s[k] - s[k - 1] for k in range(1, len(s))] + [1 - s[-1]]
        return np.array(fr)

    # ======================================================================
    def run(self):
        self.atmospheric()
        self.vacuum()
        self.light_ends()
        self.preheat()
        self.heaters()
        self.number_streams()
        return self

    # ======================================================================
    def atmospheric(self):
        sl, crude = self.sl, self.crude
        crude_m3h = self.vol(crude)
        names = ["NAPH", "KERO", "DIESEL", "AGO", "AR"]
        cuts = [165, 235, 320, 370]
        fr = self.sigmoid_split(sl.Tb, cuts, [4.5, 6.5, 9, 12])
        prod = {n: crude * fr[i] for i, n in enumerate(names)}

        # column geometry: tray 1 = top
        tray = dict(top=1, TPA_ret=1, TPA_draw=3, KERO=10, MPA_ret=11, MPA_draw=13, DIESEL=22,
                    BPA_ret=23, BPA_draw=25, AGO=32, wash_bot=35, bottom=41)
        Ptray = lambda n: D["atm_top_P"] + (n - 1) * D["atm_tray_dP"]
        P_fz = Ptray(tray["wash_bot"]) + 0.01

        # steam
        st = {k: v * LB_BBL_TO_KG_M3 * self.vol(prod[k if k != "bottom" else "AR"])
              for k, v in D["steam_lb_per_bbl"].items()}
        desalted_water = 0.002 * crude_m3h * 999
        steam_total = sum(st.values()) + desalted_water

        # ---- flash zone temperature -------------------------------------
        distil = sum(self.vol(prod[n]) for n in names[:-1])
        target = distil + D["atm_overflash_lv"] * crude_m3h

        def fz_err(T):
            f = flash_TP(sl, crude, T, P_fz, st["bottom"] + desalted_water)
            return self.vol(f.vap) - target

        T_fz = brentq(fz_err, 250, 450)
        fz = flash_TP(sl, crude, T_fz, P_fz, st["bottom"] + desalted_water)
        cot = T_fz + D["tl_dT"]
        if cot > D["atm_cot_max"]:
            self.warn.append(f"Atm COT {cot:.1f} C exceeds {D['atm_cot_max']} C limit")
        overflash = np.clip(fz.vap - sum(prod[n] for n in names[:-1]), 0, None)

        # ---- iterate draw temperatures / reflux --------------------------
        T_draw = {"KERO": 200.0, "DIESEL": 280.0, "AGO": 330.0}
        T_top, R = 120.0, prod["NAPH"].sum() * 1.0
        L_int = {"KERO": 1e5, "DIESEL": 1e5, "AGO": 1e5}
        T_bot = T_fz - 12.0
        mw_w = STEAM["MW"]
        # drum flash for reflux composition
        drum = flash_TP(sl, prod["NAPH"], D["atm_drum_T"], D["atm_drum_P"])
        refl_unit = drum.liq / drum.liq.sum()
        for _ in range(8):
            # steam below each draw tray (stripper vapours return one tray above draw)
            steam_below = {"AGO": st["bottom"] + desalted_water,
                           "DIESEL": st["bottom"] + desalted_water + st["AGO"],
                           "KERO": st["bottom"] + desalted_water + st["AGO"] + st["DIESEL"]}
            lighter = {"KERO": ["NAPH"], "DIESEL": ["NAPH", "KERO"], "AGO": ["NAPH", "KERO", "DIESEL"]}
            for p in ["KERO", "DIESEL", "AGO"]:
                n_hc = sum((prod[q] / sl.MW).sum() for q in lighter[p]) + R / self.mw(refl_unit) * 0 \
                    + L_int[p] / self.mw(prod[p])
                n_st = steam_below[p] / mw_w
                p_hc = Ptray(tray[p]) * n_hc / (n_hc + n_st)
                # bounded by wash-zone profile (pseudo-component LK Psat over-predicts AGO bubble pt)
                T_draw[p] = min(bubble_T(sl, prod[p], p_hc), T_fz - 18.0)
            # top temperature: dew point of (D + R) at HC partial pressure
            top_vap = prod["NAPH"] + R * refl_unit
            n_hc = (top_vap / sl.MW).sum()
            n_st = steam_total / mw_w
            p_hc = D["atm_top_P"] * n_hc / (n_hc + n_st)
            T_top = dew_T(sl, top_vap, p_hc)
            # overall balance (column + side strippers, condenser excluded)
            T_out = {"KERO": T_draw["KERO"] - 8, "DIESEL": T_draw["DIESEL"] - 8, "AGO": T_draw["AGO"] - 8}
            H_in = enthalpy(sl, fz.liq, fz.vap, T_fz) + (sum(st.values())) * steam_h(350) / 3600 \
                + desalted_water * steam_h(T_fz) / 3600 - (st["bottom"] + desalted_water) * 0  # steam already
            H_in = enthalpy(sl, fz.liq, fz.vap, T_fz) + sum(st.values()) * steam_h(350) / 3600 \
                + desalted_water * steam_h(T_fz) / 3600
            H_out = self.hv(prod["NAPH"], T_top) + steam_total * steam_h(T_top) / 3600 \
                + sum(self.hl(prod[p], T_out[p]) for p in T_out) + self.hl(prod["AR"], T_bot)
            Q_tot = H_in - H_out
            pa = {k: v * Q_tot for k, v in D["pa_split"].items()}
            Q_refl = Q_tot - sum(pa.values())
            dh_refl = (self.hv(refl_unit, T_top) - self.hl(refl_unit, D["atm_drum_T"])) * 3600
            R = Q_refl * 3600 / dh_refl
            # internal reflux below each draw via envelope balance
            Q_above = {"KERO": Q_refl + pa["TPA"], "DIESEL": Q_refl + pa["TPA"] + pa["MPA"],
                       "AGO": Q_refl + pa["TPA"] + pa["MPA"] + pa["BPA"]}
            steam_above = {"KERO": steam_below["KERO"], "DIESEL": steam_below["DIESEL"],
                           "AGO": steam_below["AGO"]}
            for p in ["KERO", "DIESEL", "AGO"]:
                Tn = T_draw[p]
                sens = 0.0
                for q in lighter[p]:
                    h_out = self.hv(prod[q], T_top) if q == "NAPH" else self.hl(prod[q], T_out[q])
                    sens += self.hv(prod[q], Tn) - h_out
                sens += steam_above[p] * STEAM["cp_v"] * (Tn - T_top) / 3600
                L_int[p] = max((Q_above[p] - sens) * 3600 / self.lam(prod[p], Tn), 0.0)

        # PA draw/return temperatures from tray temperature profile
        prof_n = [1, 10, 22, 32, 35, 41]
        prof_T = [T_top, T_draw["KERO"], T_draw["DIESEL"], T_draw["AGO"], T_fz - 3, T_bot]
        T_tray = lambda n: float(np.interp(n, prof_n, prof_T))
        pa_info = {}
        for k, comp, dT in [("TPA", prod["KERO"] * 0.5 + prod["NAPH"] * 0.5, 70),
                            ("MPA", prod["KERO"], 80), ("BPA", prod["DIESEL"], 90)]:
            Td = T_tray(tray[f"{k}_draw"])
            unit = comp / comp.sum()
            dh = (self.hl(unit, Td) - self.hl(unit, Td - dT)) * 3600
            circ = pa[k] * 3600 / dh
            pa_info[k] = dict(duty_kw=pa[k], T_draw=Td, T_ret=Td - dT, flow=circ, comp=unit,
                              draw_tray=tray[f"{k}_draw"], ret_tray=tray[f"{k}_ret"])

        # water dew point at top
        y_st = (steam_total / mw_w) / ((prod["NAPH"] + R * refl_unit) / sl.MW).sum()
        y_st = y_st / (1 + y_st)
        p_w = D["atm_top_P"] * y_st
        T_wdew = brentq(lambda T: water_psat(T) - p_w, 0, 200)

        Q_cond = (self.hv(prod["NAPH"] + R * refl_unit, T_top) - self.hl(drum.liq + R * refl_unit, D["atm_drum_T"])
                  - self.hv(drum.vap, T_top) + self.hv(drum.vap, D["atm_drum_T"])) \
            + steam_total * (steam_h(T_top) - 4.19 * (D["atm_drum_T"] - 15)) / 3600

        # section loads for hydraulics -----------------------------------
        sections = []

        def sec(name, trays, V_hc, V_comp_mw, T, P, L, L_comp, steam, Lpa=0.0):
            V_tot = V_hc + steam
            mwv = (V_hc + steam) / (V_hc / V_comp_mw + steam / mw_w)
            rho_v = P * 1e5 * mwv / (8314.46 * (T + 273.15))
            rho_l = float((L_comp * self.sl.rho_l(T)).sum() / L_comp.sum()) if L_comp.sum() else 700
            sections.append(dict(name=name, trays=trays, V_kg_h=V_tot, L_kg_h=L + Lpa, T=T, P=P,
                                 rho_v=rho_v, rho_l=rho_l, mw_v=mwv))

        refl_mw = self.mw(refl_unit)
        naph_v = prod["NAPH"].sum()
        sec("Top / TPA", "1-3", naph_v + R + pa["TPA"] * 3600 / self.lam(prod["KERO"], T_top) * 0.0,
            self.mw(prod["NAPH"]), T_top + 5, D["atm_top_P"], R, refl_unit, steam_total, pa_info["TPA"]["flow"])
        # below TPA draw: vapour must also carry TPA condensing load
        V_tpa = naph_v + R + pa["TPA"] * 3600 / self.lam(prod["NAPH"] + prod["KERO"], T_tray(4))
        sec("Naphtha-kero fract.", "4-9", V_tpa, self.mw(prod["NAPH"] + prod["KERO"]), T_tray(6), Ptray(6),
            V_tpa - naph_v, prod["KERO"], steam_total)
        V_k = naph_v + prod["KERO"].sum() + L_int["KERO"]
        sec("MPA", "11-13", V_k + pa["MPA"] * 3600 / self.lam(prod["KERO"], T_tray(13)),
            self.mw(prod["KERO"]), T_tray(12), Ptray(12), L_int["KERO"], prod["KERO"],
            steam_below["KERO"] + st["KERO"] * 0, pa_info["MPA"]["flow"])
        V_d = naph_v + prod["KERO"].sum() + prod["DIESEL"].sum() + L_int["DIESEL"]
        sec("Kero-diesel fract.", "14-21", V_k + pa["MPA"] * 3600 / self.lam(prod["KERO"], T_tray(14)) * 0.7,
            self.mw(prod["KERO"] + prod["DIESEL"]), T_tray(17), Ptray(17), L_int["KERO"] + 0.5 * L_int["DIESEL"],
            prod["DIESEL"], steam_below["KERO"])
        sec("BPA", "23-25", V_d + pa["BPA"] * 3600 / self.lam(prod["DIESEL"], T_tray(25)),
            self.mw(prod["DIESEL"]), T_tray(24), Ptray(24), L_int["DIESEL"], prod["DIESEL"],
            steam_below["DIESEL"], pa_info["BPA"]["flow"])
        V_a = V_d - L_int["DIESEL"] + prod["AGO"].sum() + L_int["AGO"]
        sec("Diesel-AGO fract.", "26-31", max(V_a, V_d), self.mw(prod["DIESEL"] + prod["AGO"]), T_tray(28),
            Ptray(28), L_int["AGO"] + L_int["DIESEL"] * 0.3, prod["AGO"], steam_below["AGO"])
        sec("Wash zone", "33-35", fz.vap.sum(), self.mw(fz.vap), T_fz - 3, P_fz, max(overflash.sum(), 1.0),
            overflash if overflash.sum() > 0 else prod["AGO"], st["bottom"] + desalted_water)
        strip_hc = 0.03 * prod["AR"].sum()
        sec("Stripping", "36-41", strip_hc, self.mw(prod["AR"]) * 0.4, T_bot + 5, Ptray(38), prod["AR"].sum(),
            prod["AR"], st["bottom"])

        self.res["atm"] = dict(prod=prod, tray=tray, P_fz=P_fz, T_fz=T_fz, cot=cot, fz=fz, T_draw=T_draw,
                               T_out={"KERO": T_draw["KERO"] - 8, "DIESEL": T_draw["DIESEL"] - 8,
                                      "AGO": T_draw["AGO"] - 8},
                               T_top=T_top, T_bot=T_bot, R=R, drum=drum, refl_unit=refl_unit, Q_tot=Q_tot,
                               Q_refl=Q_refl, Q_cond=Q_cond, pa=pa_info, L_int=L_int, steam=st,
                               desalted_water=desalted_water, steam_total=steam_total, T_wdew=T_wdew,
                               overflash=overflash, sections=sections, Ptray=Ptray, T_tray=T_tray,
                               crude_m3h=crude_m3h)
        if T_top - T_wdew < 14:
            self.warn.append(f"Atm top {T_top:.0f} C within {T_top - T_wdew:.0f} C of water dew point")

    # ======================================================================
    def vacuum(self):
        sl, a = self.sl, self.res["atm"]
        ar = a["prod"]["AR"]
        ar_m3h = self.vol(ar)
        fr = self.sigmoid_split(sl.Tb, [430, 550], [12, 16])
        lvgo, hvgo, vr0 = ar * fr[0], ar * fr[1], ar * fr[2]
        st_bot = D["vac_steam_lb_per_bbl"]["bottom"] * LB_BBL_TO_KG_M3 * self.vol(vr0)
        st_coil = D["vac_steam_lb_per_bbl"]["coil"] * LB_BBL_TO_KG_M3 * ar_m3h
        P_fz = D["vac_fz_P"]
        target = self.vol(lvgo + hvgo) + D["vac_overflash_lv"] * ar_m3h

        def err(T):
            return self.vol(flash_TP(sl, ar, T, P_fz, st_bot + st_coil).vap) - target

        T_fz = brentq(err, 300, 480)
        fz = flash_TP(sl, ar, T_fz, P_fz, st_bot + st_coil)
        cot = T_fz + D["vac_tl_dT"]
        if cot > D["vac_cot_max"]:
            self.warn.append(f"Vac COT {cot:.1f} C exceeds {D['vac_cot_max']} C")
        slop = np.clip(fz.vap - lvgo - hvgo, 0, None)
        slop *= D["vac_overflash_lv"] * ar_m3h / self.vol(slop)
        vr = ar - lvgo - hvgo - slop
        T_bot = T_fz - 20  # quench + stripping
        steam = st_bot + st_coil
        ncg = 0.0003 * ar.sum()       # cracked gas, MW ~35
        air = 25.0
        # draw temperatures at HC partial pressure
        P_top = D["vac_top_P"]
        P_hv = P_top + 0.6 * (P_fz - P_top)
        P_lv = P_top + 0.1 * (P_fz - P_top)
        n_st = steam / STEAM["MW"]

        def T_bub(m, lighter_mol, P):
            n_hc = (m / sl.MW).sum() * 1.5 + lighter_mol
            return bubble_T(sl, m, P * n_hc / (n_hc + n_st), lo=0, hi=600)

        T_hvgo = T_bub(hvgo, (lvgo / sl.MW).sum(), P_hv)
        T_lvgo = T_bub(lvgo, 0.0, P_lv)
        T_top = 70.0
        T_slop = T_fz - 8
        H_in = enthalpy(sl, fz.liq, fz.vap, T_fz) + steam * steam_h(T_fz) / 3600
        H_out = steam * steam_h(T_top) / 3600 + self.hl(lvgo, T_lvgo) + self.hl(hvgo, T_hvgo) \
            + self.hl(slop, T_slop) + self.hl(vr, T_bot)
        Q_tot = H_in - H_out
        pa = {}
        for k, comp, Td, Tr in [("LVGO", lvgo, T_lvgo, 55.0), ("HVGO", hvgo, T_hvgo, T_hvgo - 110)]:
            q = D["vac_pa_split"][k] * Q_tot
            unit = comp / comp.sum()
            circ = q * 3600 / ((self.hl(unit, Td) - self.hl(unit, Tr)) * 3600)
            pa[k] = dict(duty_kw=q, T_draw=Td, T_ret=Tr, flow=circ, comp=unit)
        # internal reflux in LVGO/HVGO fractionation bed
        L_frac = max((pa["LVGO"]["duty_kw"] - (self.hv(lvgo, T_hvgo) - self.hl(lvgo, T_lvgo))
                      - steam * STEAM["cp_v"] * (T_hvgo - T_top) / 3600) * 3600 / self.lam(hvgo, T_hvgo), 0)
        # loads
        def sec(name, V_hc, mwhc, T, P, L, Lcomp):
            mwv = (V_hc + steam + ncg) / (V_hc / mwhc + steam / 18.015 + ncg / 35)
            rho_v = P * 1e5 * mwv / (8314.46 * (T + 273.15))
            rho_l = float((Lcomp * sl.rho_l(T)).sum() / Lcomp.sum())
            return dict(name=name, V_kg_h=V_hc + steam + ncg, L_kg_h=L, T=T, P=P, rho_v=rho_v, rho_l=rho_l,
                        mw_v=mwv)
        mwl = self.mw(lvgo)
        sections = [
            sec("Bed 1 - LVGO PA", lvgo.sum(), mwl,  # vapour entering bed 1 bottom (condensed in bed)
                (T_top + T_lvgo) / 2, P_top + 0.002,
                pa["LVGO"]["flow"], lvgo),
            sec("Bed 2 - LVGO/HVGO fract.", lvgo.sum() + L_frac, self.mw(lvgo + hvgo), T_hvgo - 30,
                P_top + 0.35 * (P_fz - P_top), L_frac, hvgo),
            sec("Bed 3 - HVGO PA", lvgo.sum() + hvgo.sum() + L_frac, self.mw(hvgo), (T_hvgo + T_slop) / 2,
                P_hv, pa["HVGO"]["flow"], hvgo),
            sec("Bed 4 - Wash", fz.vap.sum(), self.mw(fz.vap), T_fz - 4, P_fz - 0.004,
                slop.sum() * 1.6, slop),
            sec("Flash zone", fz.vap.sum(), self.mw(fz.vap), T_fz, P_fz, fz.liq.sum(), fz.liq),
            sec("Stripping", 0.02 * vr.sum(), self.mw(vr) * 0.5, T_bot + 5, P_fz + 0.01, vr.sum(), vr),
        ]
        self.res["vac"] = dict(ar=ar, lvgo=lvgo, hvgo=hvgo, slop=slop, vr=vr, T_fz=T_fz, P_fz=P_fz, cot=cot,
                               fz=fz, T_bot=T_bot, T_top=T_top, T_lvgo=T_lvgo, T_hvgo=T_hvgo, T_slop=T_slop,
                               st_bot=st_bot, st_coil=st_coil, steam=steam, ncg=ncg, air=air, Q_tot=Q_tot,
                               pa=pa, L_frac=L_frac, sections=sections, P_top=P_top, ar_m3h=ar_m3h)
        # ejector system (three stages, HEI-style rough entrainment ratios)
        oil_vap = 0.0005 * ar.sum()
        load1 = steam + ncg + air + oil_vap
        ms1 = 2.6 * load1
        cond1_load = (steam + ms1) * 0.97
        load2 = ncg + air + oil_vap * 0.5 + (steam + ms1) * 0.03
        ms2 = 1.8 * load2 + 200
        load3 = ncg + air + (load2 - ncg - air) * 0.1 + ms2 * 0.03
        ms3 = 1.6 * load3 + 150
        self.res["ejector"] = dict(stages=[
            dict(tag="J-201", suction_mbar=P_top * 1000, discharge_mbar=130, load_kg_h=load1, motive_kg_h=ms1),
            dict(tag="J-202", suction_mbar=120, discharge_mbar=350, load_kg_h=load2, motive_kg_h=ms2),
            dict(tag="J-203", suction_mbar=330, discharge_mbar=1100, load_kg_h=load3, motive_kg_h=ms3)],
            motive_total=ms1 + ms2 + ms3, sour_water=steam + ms1 + ms2 + ms3, offgas=ncg + air,
            slop_oil=oil_vap)

    # ======================================================================
    def _fug(self, feed, lk, hk, rec_lk, rec_hk, P_top, T_drum, P_bot, tag):
        sl = self.sl
        n = feed / sl.MW
        z = n / n.sum()
        # first estimate: keys only, others sharp
        d = np.where(np.arange(sl.n) < lk, n, 0.0)
        d[lk], d[hk] = rec_lk * n[lk], (1 - rec_hk) * n[hk]
        for _ in range(3):
            b = n - d
            Tt = dew_T(sl, d * sl.MW, P_top)
            Tb = bubble_T(sl, b * sl.MW, P_bot)
            Tavg = 0.5 * (Tt + Tb)
            ps = sl.psat(Tavg)
            alpha = ps / ps[hk]
            Nmin = math.log((d[lk] / b[lk]) * (b[hk] / d[hk])) / math.log(alpha[lk])
            ratio = (d[hk] / b[hk]) * alpha ** Nmin           # Fenske distribution of non-keys
            d = n * ratio / (1 + ratio)
            d[lk], d[hk] = rec_lk * n[lk], (1 - rec_hk) * n[hk]
        b = n - d
        theta = brentq(lambda th: (alpha * z / (alpha - th)).sum(), 1.0 + 1e-6, alpha[lk] - 1e-6)
        xd = d / d.sum()
        Rmin = (alpha * xd / (alpha - theta)).sum() - 1
        Rr = 1.3 * Rmin
        X = (Rr - Rmin) / (Rr + 1)
        Y = 0.75 * (1 - X ** 0.5668)
        N = (Nmin + Y) / (1 - Y)
        kirk = ((z[hk] / z[lk]) * ((b[lk] / b.sum()) / (d[hk] / d.sum())) ** 2 * b.sum() / d.sum()) ** 0.206
        Nr = N / (1 + kirk)
        actual = math.ceil((N - 1) / 0.75)
        dm, bm = d * sl.MW, b * sl.MW
        drum = flash_TP(sl, dm, T_drum, P_top - 0.3)
        refl = Rr * dm.sum()
        Q_cond = (self.hv(dm, Tt) - self.hl(dm, T_drum)) * (1 + Rr)
        return dict(tag=tag, d=dm, b=bm, T_top=Tt, T_bot=Tb, alpha_lk=alpha[lk], Nmin=Nmin, Rmin=Rmin, R=Rr,
                    N_theo=N, N_actual=actual, feed_stage=max(1, round(actual * Nr / N)), reflux=refl,
                    Q_cond=Q_cond, drum=drum, P_top=P_top, P_bot=P_bot)

    def light_ends(self):
        a = self.res["atm"]
        naph = a["drum"].liq.copy()
        names = self.sl.names()
        nc4, ip = names.index("nC4"), 4
        stab = self._fug(naph, nc4, ip, 0.98, 0.97, D["stab_drum_P"] + 0.3, D["stab_drum_T"],
                         D["stab_drum_P"] + 0.8, "C-105")
        # feed preheated against bottoms to 120 C
        # feed preheated against stabiliser bottoms (bottoms cooled to splitter feed T)
        T_sf = stab["T_bot"] - 40
        stab["Q_fb"] = self.hl(stab["b"], stab["T_bot"]) - self.hl(stab["b"], T_sf)
        H_f = self.hl(naph, D["atm_drum_T"]) + stab["Q_fb"]
        T_feed = self.T_from_hl(naph, H_f, lo=0, hi=300)
        stab["Q_reb"] = self.hl(stab["b"], stab["T_bot"]) + self.hl(stab["d"], D["stab_drum_T"]) + stab["Q_cond"] - H_f
        stab["T_feed"] = T_feed
        # LPG / off-gas split in stabiliser drum
        sd = flash_TP(self.sl, stab["d"], D["stab_drum_T"], D["stab_drum_P"])
        stab["lpg"], stab["offgas"] = sd.liq, sd.vap
        # naphtha splitter: LN / HN at 80 C
        Tb = self.sl.Tb
        lk = int(np.where(Tb < 80)[0].max())
        hk = lk + 1
        spl = self._fug(stab["b"], lk, hk, 0.95, 0.95, D["split_drum_P"] + 0.3, D["split_drum_T"],
                        D["split_drum_P"] + 0.7, "C-106")
        spl["T_feed"] = T_sf
        spl["Q_reb"] = self.hl(spl["b"], spl["T_bot"]) + self.hl(spl["d"], D["split_drum_T"]) + spl["Q_cond"] \
            - self.hl(stab["b"], T_sf)
        stab["T_feed_in"] = D["atm_drum_T"]
        self.res["stab"], self.res["split"] = stab, spl

    # ======================================================================
    def preheat(self):
        sl, a, v = self.sl, self.res["atm"], self.res["vac"]
        crude = self.crude
        water_in = 0.003 * a["crude_m3h"] * 999
        ww = D["wash_water_lv"] * a["crude_m3h"] * 999
        ds_water = a["desalted_water"]
        # hot streams: name -> (mass vector, T_in, T_out_target, fixed duty?)
        hot = {
            "TPA": (a["pa"]["TPA"]["comp"] * a["pa"]["TPA"]["flow"], a["pa"]["TPA"]["T_draw"], a["pa"]["TPA"]["T_ret"], True),
            "MPA": (a["pa"]["MPA"]["comp"] * a["pa"]["MPA"]["flow"], a["pa"]["MPA"]["T_draw"], a["pa"]["MPA"]["T_ret"], True),
            "BPA": (a["pa"]["BPA"]["comp"] * a["pa"]["BPA"]["flow"], a["pa"]["BPA"]["T_draw"], a["pa"]["BPA"]["T_ret"], True),
            "KERO": (a["prod"]["KERO"], a["T_out"]["KERO"], 45.0, False),
            "DIESEL": (a["prod"]["DIESEL"], a["T_out"]["DIESEL"], 55.0, False),
            "AGO": (a["prod"]["AGO"], a["T_out"]["AGO"], 60.0, False),
            "LVGO": (v["pa"]["LVGO"]["comp"] * v["pa"]["LVGO"]["flow"] + v["lvgo"], v["T_lvgo"], 55.0, False),
            "HVGO": (v["pa"]["HVGO"]["comp"] * v["pa"]["HVGO"]["flow"] + v["hvgo"], v["T_hvgo"],
                     v["pa"]["HVGO"]["T_ret"], False),
            "VR": (v["vr"], v["T_bot"], 175.0, False),
        }
        state = {k: h[1] for k, h in hot.items()}  # current hot temperature
        # split temperatures for streams used twice (hot-end exchanger outlet)
        split = {"DIESEL": 205.0, "VR": 255.0}
        seq_cold = [("E-101", "TPA"), ("E-102", "KERO"), ("E-103", "LVGO"), ("E-104", "DIESEL"), ("E-105", "VR")]
        seq_hot = [("E-106", "MPA"), ("E-107", "DIESEL"), ("E-108", "HVGO"), ("E-109", "AGO"), ("E-110", "BPA"),
                   ("E-111", "VR")]
        dTmin = D["min_approach"]
        exch = []
        hot_end_out = {}

        def run_train(seq, Tc, cold_m, cold_w, train):
            for tag, hname in seq:
                mh, Tin_nom, Tout_t, _ = hot[hname]
                if hname in split and train == "hot":
                    Th_in, Th_out_min = Tin_nom, split[hname]
                elif hname in split and train == "cold":
                    Th_in, Th_out_min = split[hname], Tout_t
                else:
                    Th_in, Th_out_min = state[hname], Tout_t
                Hc_in = self.hl(cold_m, Tc) + cold_w * 4.19 * (Tc - 15) / 3600
                # duty limited by cold-end approach
                Th_out = max(Th_out_min, Tc + dTmin)
                Q = max(self.hl(mh, Th_in) - self.hl(mh, Th_out), 0)
                # hot-end approach: cold outlet <= Th_in - dTmin
                Tc_out = self.T_from_hl(cold_m, Hc_in + Q, cold_w, lo=0, hi=450)
                if Tc_out > Th_in - dTmin:
                    Tc_out = Th_in - dTmin
                    Q = self.hl(cold_m, Tc_out) + cold_w * 4.19 * (Tc_out - 15) / 3600 - Hc_in
                    Th_out = self.T_from_hl(mh, self.hl(mh, Th_in) - Q, lo=0, hi=450)
                if Q <= 0:
                    Q, Tc_out, Th_out = 0.0, Tc, Th_in
                exch.append(dict(tag=tag, hot=hname, Q_kw=Q, Th_in=Th_in, Th_out=Th_out, Tc_in=Tc, Tc_out=Tc_out,
                                 hot_flow=mh.sum(), cold_flow=cold_m.sum() + cold_w, train=train))
                if hname in split and train == "hot":
                    hot_end_out[hname] = Th_out          # cold-end exchanger owns the final state
                else:
                    state[hname] = Th_out
                Tc = Tc_out
            return Tc

        T_des = run_train(seq_cold, 30.0, crude, water_in, "cold")
        if T_des > 150:
            self.warn.append(f"Desalter temperature {T_des:.0f} C high - bypass control required")
        # desalter: mix wash water (preheated vs brine to ~T_des-15)
        T_ww = T_des - 15
        T_dc = T_des  # desalted crude temp (mixing small effect)
        cit = run_train(seq_hot, T_dc, crude, ds_water, "hot")
        # trims: remainder duties to coolers/steam generators
        trims = []
        trim_map = {"TPA": ("E-101", "trim (none)"), "MPA": ("E-106", "trim (none)"),
                    "BPA": ("E-113", "MP steam generator"), "KERO": ("A-103", "air cooler"),
                    "DIESEL": ("A-104", "air cooler"), "AGO": ("A-105", "air cooler"),
                    "LVGO": ("A-201", "air cooler"), "HVGO": ("A-202", "air cooler"),
                    "VR": ("E-201", "LP steam generator")}
        for hname, (mh, Tin, Tt, fixed) in hot.items():
            Tcur = state[hname]
            # hot-end exchanger of a split stream may not reach the split temperature
            extra = 0.0
            if hname in hot_end_out and hot_end_out[hname] > split[hname]:
                extra = self.hl(mh, hot_end_out[hname]) - self.hl(mh, split[hname])
            if Tcur > Tt + 0.5 or extra > 1:
                Q = self.hl(mh, Tcur) - self.hl(mh, Tt) + extra
                tag, typ = trim_map[hname]
                T_in, T_out = (hot_end_out[hname], split[hname]) if extra > 1 and Tcur <= Tt + 0.5 else (Tcur, Tt)
                trims.append(dict(tag=tag, hot=hname, type=typ, Q_kw=Q, T_in=T_in, T_out=T_out, flow=mh.sum(),
                                  note="between hot-end and cold-end exchangers" if extra > 1 else ""))
        # HVGO net product continues from PA-return temperature to 90 C rundown
        hv = v["hvgo"]
        trims.append(dict(tag="A-202", hot="HVGO product", type="air cooler",
                          Q_kw=self.hl(hv, state["HVGO"]) - self.hl(hv, 90.0), T_in=state["HVGO"], T_out=90.0,
                          flow=hv.sum()))
        self.res["preheat"] = dict(exch=exch, trims=trims, T_desalter=T_des, CIT=cit, wash_water=ww,
                                   water_in=water_in, T_ww=T_ww, hot=hot,
                                   brine=ww + water_in - ds_water)

    # ======================================================================
    def heaters(self):
        sl, a, v, p = self.sl, self.res["atm"], self.res["vac"], self.res["preheat"]
        P_out = a["P_fz"] + D["tl_dP"]
        f_out = flash_TP(sl, self.crude, a["cot"], P_out, a["desalted_water"])
        H_out = enthalpy(sl, f_out.liq, f_out.vap, a["cot"], steam_v=a["desalted_water"])
        H_in = self.hl(self.crude, p["CIT"]) + a["desalted_water"] * 4.19 * (p["CIT"] - 15) / 3600
        Q = H_out - H_in
        # stripping-steam superheat coil (LP steam 180 -> 350 C)
        st_ss = sum(a["steam"].values())
        Q_ss = st_ss * STEAM["cp_v"] * (350 - 180) / 3600
        h101 = dict(tag="H-101", Q_proc_kw=Q, Q_ss_kw=Q_ss, Q_abs_kw=Q + Q_ss, eff=D["h101_eff"],
                    Q_fired_kw=(Q + Q_ss) / D["h101_eff"], T_in=p["CIT"], T_out=a["cot"], P_out=P_out,
                    vf_out=f_out.vf_mass, flow=self.crude.sum() + a["desalted_water"])
        P_out_v = v["P_fz"] + 0.25
        f_v = flash_TP(sl, v["ar"], v["cot"], P_out_v, v["st_coil"])
        Q_v = enthalpy(sl, f_v.liq, f_v.vap, v["cot"], steam_v=v["st_coil"]) - self.hl(v["ar"], a["T_bot"]) \
            - v["st_coil"] * steam_h(180) / 3600
        h201 = dict(tag="H-201", Q_proc_kw=Q_v, Q_abs_kw=Q_v, eff=D["h201_eff"], Q_fired_kw=Q_v / D["h201_eff"],
                    T_in=a["T_bot"], T_out=v["cot"], P_out=P_out_v, vf_out=f_v.vf_mass,
                    flow=v["ar"].sum() + v["st_coil"])
        lhv = basis.UTILITIES["fuel_gas"]["LHV_MJ_kg"] * 1000
        for h in (h101, h201):
            h["fuel_kg_h"] = h["Q_fired_kw"] / lhv * 3600
        self.res["H-101"], self.res["H-201"] = h101, h201

    # ======================================================================
    def number_streams(self):
        sl, a, v, p = self.sl, self.res["atm"], self.res["vac"], self.res["preheat"]
        st, sp = self.res["stab"], self.res["split"]
        e = self.res["ejector"]
        z = np.zeros(sl.n)
        ex = {e["tag"]: e for e in p["exch"]}
        A = self.add
        c = self.crude
        A(Stream("1", "Crude from tankage", c, 30, 3.0, water=p["water_in"], frm="TK (OSBL)", to="P-101"))
        A(Stream("2", "Crude to desalter", c, p["T_desalter"], 14.0, water=p["water_in"], frm="E-105", to="D-101"))
        A(Stream("3", "Desalter wash water", z, p["T_ww"], 16.0, water=p["wash_water"], frm="P-114", to="D-101", phase="W"))
        A(Stream("4", "Desalter brine", z, p["T_desalter"] - 30, 6.0, water=p["brine"], frm="D-101", to="WWT (OSBL)", phase="W"))
        A(Stream("5", "Desalted crude", c, p["T_desalter"], 11.0, water=a["desalted_water"], frm="D-101", to="P-102"))
        A(Stream("6", "Crude to heater (CIT)", c, p["CIT"], 18.0, water=a["desalted_water"], frm="E-111", to="H-101"))
        A(Stream("7", "Heater outlet / transfer line", c, a["cot"], a["P_fz"] + D["tl_dP"], steam=a["desalted_water"],
                 frm="H-101", to="C-101", phase="M"))
        A(Stream("8", "Column overhead vapour", a["prod"]["NAPH"] + a["R"] * a["refl_unit"], a["T_top"],
                 D["atm_top_P"], steam=a["steam_total"], frm="C-101", to="A-101", phase="V"))
        A(Stream("9", "Overhead drum off-gas (normally no flow)", a["drum"].vap, D["atm_drum_T"], D["atm_drum_P"], frm="D-102",
                 to="Fuel gas / FGR (OSBL)", phase="V"))
        A(Stream("10", "Reflux", a["R"] * a["refl_unit"], D["atm_drum_T"], 8.0, frm="P-103", to="C-101"))
        A(Stream("11", "Unstabilised naphtha", a["drum"].liq, D["atm_drum_T"], 15.0, frm="P-104", to="E-114"))
        A(Stream("12", "Overhead sour water", z, D["atm_drum_T"], 6.0, water=a["steam_total"], frm="P-105",
                 to="SWS (OSBL)", phase="W"))
        for no, k, tag in [("13", "TPA", "P-106"), ("14", "MPA", "P-107"), ("15", "BPA", "P-108")]:
            pa = a["pa"][k]
            A(Stream(no, f"{k} pumparound (draw)", pa["comp"] * pa["flow"], pa["T_draw"], 9.0, frm="C-101", to=tag))
        A(Stream("16", "Kerosene product", a["prod"]["KERO"], 45, 6.0, frm="A-103", to="Storage / KHT"))
        A(Stream("17", "Diesel product", a["prod"]["DIESEL"], 55, 6.0, frm="A-104", to="Storage / DHT"))
        A(Stream("18", "AGO product", a["prod"]["AGO"], 60, 6.0, frm="A-105", to="DHT / FCC"))
        A(Stream("19", "Atmospheric residue", a["prod"]["AR"], a["T_bot"], 20.0, frm="P-112", to="H-201"))
        A(Stream("20", "Atm stripping steam (total)", z, 350, 4.5, steam=sum(a["steam"].values()), frm="H-101 SS coil",
                 to="C-101/C-102/C-103/C-104", phase="V"))
        A(Stream("21", "Vacuum heater outlet", v["ar"], v["cot"], v["P_fz"] + 0.25, steam=v["st_coil"], frm="H-201",
                 to="C-201", phase="M"))
        A(Stream("22", "Vacuum column overhead", z, v["T_top"], v["P_top"], steam=v["steam"], frm="C-201", to="J-201",
                 phase="V", gas=v["ncg"] + v["air"] + e["slop_oil"], gas_mw=40.0))
        A(Stream("23", "LVGO product", v["lvgo"], 55, 8.0, frm="A-201", to="Hydrocracker"))
        A(Stream("24", "HVGO product", v["hvgo"], 90, 8.0, frm="A-202", to="FCC / Hydrocracker"))
        A(Stream("25", "Slop wax (hot, traced)", v["slop"], v["T_slop"], 8.0, frm="P-203", to="Delayed coker feed (hot)"))
        A(Stream("26", "Vacuum residue", v["vr"], 175, 10.0, frm="E-105", to="Delayed coker / storage"))
        A(Stream("27", "Ejector sour water", z, 45, 1.5, water=e["sour_water"], frm="D-201", to="SWS (OSBL)", phase="W"))
        A(Stream("28", "Vacuum off-gas (NCG + air)", z, 45, 1.05, frm="D-202", to="H-201 burners", phase="V",
                 gas=v["ncg"] + v["air"], gas_mw=30.0))
        A(Stream("29", "Stabiliser off-gas (normally no flow)", st["offgas"], D["stab_drum_T"], D["stab_drum_P"], frm="D-105",
                 to="Fuel gas (OSBL)", phase="V"))
        A(Stream("30", "LPG product", st["lpg"], D["stab_drum_T"], 18.0, frm="P-115", to="LPG treating"))
        A(Stream("31", "Stabilised naphtha", st["b"], st["T_bot"], st["P_bot"], frm="C-105", to="C-106"))
        A(Stream("32", "Light naphtha", sp["d"], D["split_drum_T"], 8.0, frm="P-116", to="Isomerisation"))
        A(Stream("33", "Heavy naphtha", sp["b"], 45, 8.0, frm="P-117", to="NHT / Reformer"))
        A(Stream("34", "Fuel gas to heaters", z, 30, 4.5, frm="D-103", to="H-101/H-201", phase="V",
                 gas=self.res["H-101"]["fuel_kg_h"] + self.res["H-201"]["fuel_kg_h"], gas_mw=20.0))

        # flash all streams for vapour fraction
        for s in self.S.values():
            if s.m.sum() > 0 and s.phase in ("M", "V", "L"):
                f = flash_TP(sl, s.m, s.T, s.P, s.steam)
                s.vf = f.vf_mass
                if s.phase == "L" and s.vf > 0.01:
                    s.phase = "M"
            else:
                s.vf = 1.0 if s.phase == "V" else 0.0


def run() -> Model:
    return Model().run()
