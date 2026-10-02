"""Pseudo-component thermodynamics for petroleum fractions.

Correlations (all public-domain, API Technical Data Book family):
  * MW, Tc, Pc            : Riazi-Daubert (1987), API TDB 2B2.1 / 4D3.1
  * Acentric factor       : Lee-Kesler (from Tb, Tc, Pc)
  * Vapour pressure       : Lee-Kesler corresponding states
  * Liquid Cp             : Watson-Nelson (K-factor corrected)
  * Ideal-gas vapour Cp   : Fallon-Watson
  * Latent heat at Tb     : Kistiakowsky; Watson temperature correction
  * Liquid density vs T   : API MPMS 11.1 thermal expansion (K0 = 613.97)
  * VLE                   : Raoult (ideal K = Psat/P), steam treated as non-condensing

Enthalpy reference state: liquid at 15 degC = 0 kJ/kg.
Units: T in degC at the interface (K internally), P in bar(a), mass in kg.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq

R = 8.314462618  # J/mol/K
T_REF = 15.0     # degC
STEAM = dict(MW=18.015, cp_l=4.19, cp_v=2.05, lam_b=2257.0, Tb=100.0)


@dataclass
class Component:
    name: str
    Tb: float          # K
    SG: float          # 15/15 degC
    MW: float = 0.0
    Tc: float = 0.0    # K
    Pc: float = 0.0    # bar
    omega: float = 0.0
    lv_frac: float = 0.0   # liquid-volume fraction in whole crude
    sulfur: float = 0.0    # wt fraction
    defined: bool = False

    def __post_init__(self):
        Tb, SG = self.Tb, self.SG
        if not self.defined:
            self.MW = 42.965 * math.exp(2.097e-4 * Tb - 7.78712 * SG + 2.08476e-3 * Tb * SG) \
                * Tb ** 1.26007 * SG ** 4.98308
            self.Tc = 9.5233 * math.exp(-9.314e-4 * Tb - 0.544442 * SG + 6.4791e-4 * Tb * SG) \
                * Tb ** 0.81067 * SG ** 0.53691
            self.Pc = 3.1958e5 * math.exp(-8.505e-3 * Tb - 4.8014 * SG + 5.749e-3 * Tb * SG) \
                * Tb ** -0.4844 * SG ** 4.0846
            th = Tb / self.Tc
            pr = self.Pc / 1.01325
            self.omega = (-math.log(pr) - 5.92714 + 6.09648 / th + 1.28862 * math.log(th)
                          - 0.169347 * th ** 6) / (15.2518 - 15.6875 / th - 13.4721 * math.log(th)
                                                     + 0.43577 * th ** 6)

    # ---- derived ---------------------------------------------------------
    @property
    def K(self) -> float:          # Watson characterisation factor
        return (self.Tb * 1.8) ** (1 / 3) / self.SG

    @property
    def rho15(self) -> float:      # kg/m3
        return self.SG * 999.0

    @property
    def Tb_C(self) -> float:
        return self.Tb - 273.15

    def psat(self, T_C: float) -> float:
        """Vapour pressure, bar(a)."""
        Tr = max((T_C + 273.15) / self.Tc, 0.05)
        if Tr <= 1.0:
            return self.Pc * math.exp(self._lnpr(Tr))
        # supercritical: Clausius-Clapeyron extrapolation of the Tr=1 slope
        slope = (self._lnpr(1.0) - self._lnpr(0.95)) / (1 / 0.95 - 1)
        return self.Pc * math.exp(self._lnpr(1.0) + slope * (1 - 1 / Tr))

    def _lnpr(self, Tr: float) -> float:
        f0 = 5.92714 - 6.09648 / Tr - 1.28862 * math.log(Tr) + 0.169347 * Tr ** 6
        f1 = 15.2518 - 15.6875 / Tr - 13.4721 * math.log(Tr) + 0.43577 * Tr ** 6
        return f0 + self.omega * f1

    def rho_liq(self, T_C: float) -> float:
        a = 613.97 / self.rho15 ** 2
        return self.rho15 * max(1.0 - a * (T_C - 15.0) * (1 + 0.8 * a * (T_C - 15.0)), 0.35)

    # enthalpies, kJ/kg -----------------------------------------------------
    def _hl(self, T_C: float) -> float:
        SG, K = self.SG, min(self.K, 13.0)
        f = 4.1868 * (0.055 * K + 0.35) * 5.0 / 9.0
        a = 0.6811 - 0.308 * SG
        b = 0.000815 - 0.000306 * SG
        TF, T0 = T_C * 1.8 + 32, T_REF * 1.8 + 32
        return f * (a * (TF - T0) + b / 2 * (TF ** 2 - T0 ** 2))

    def lam_b(self) -> float:
        return (36.1 + 8.31 * math.log(self.Tb)) * self.Tb / self.MW

    def lam(self, T_C: float) -> float:
        Tr, Trb = (T_C + 273.15) / self.Tc, self.Tb / self.Tc
        if Tr >= 1:
            return 0.0
        return self.lam_b() * ((1 - Tr) / (1 - Trb)) ** 0.38

    def _cpv_int(self, T1: float, T2: float) -> float:
        K = min(self.K, 13.0)
        a = 0.0450 * K - 0.233
        b = (0.440 + 0.0177 * K) * 1e-3
        c = -0.1520e-6
        t1, t2 = T1 * 1.8 + 32, T2 * 1.8 + 32
        return 4.1868 * 5 / 9 * (a * (t2 - t1) + b / 2 * (t2 ** 2 - t1 ** 2) + c / 3 * (t2 ** 3 - t1 ** 3))

    def h_liq(self, T_C: float) -> float:
        return self._hl(T_C)

    def h_vap(self, T_C: float) -> float:
        Tb = self.Tb_C
        return self._hl(Tb) + self.lam_b() + self._cpv_int(Tb, T_C)


# ---------------------------------------------------------------------------
class Slate:
    """Component slate (ordered list) with vectorised helpers."""

    def __init__(self, comps: list[Component]):
        self.c = comps
        self.n = len(comps)
        self.MW = np.array([c.MW for c in comps])
        self.SG = np.array([c.SG for c in comps])
        self.Tb = np.array([c.Tb_C for c in comps])
        self.S = np.array([c.sulfur for c in comps])

    def names(self):
        return [c.name for c in self.c]

    def psat(self, T):
        return np.array([c.psat(T) for c in self.c])

    def hl(self, T):
        return np.array([c.h_liq(T) for c in self.c])

    def hv(self, T):
        return np.array([c.h_vap(T) for c in self.c])

    def lam(self, T):
        return np.array([c.lam(T) for c in self.c])

    def rho_l(self, T):
        return np.array([c.rho_liq(T) for c in self.c])


@dataclass
class FlashResult:
    T: float
    P: float
    liq: np.ndarray          # kg/h each component
    vap: np.ndarray          # kg/h each component
    steam: float = 0.0       # kg/h (all in vapour)

    @property
    def vf_mass(self):
        tot = self.liq.sum() + self.vap.sum()
        return self.vap.sum() / tot if tot else 0.0


def flash_TP(sl: Slate, m: np.ndarray, T: float, P: float, steam_kg: float = 0.0) -> FlashResult:
    """Isothermal flash of hydrocarbon mass vector m (kg/h) with inert steam (kg/h)."""
    n = m / sl.MW                       # kmol/h
    F = n.sum()
    S = steam_kg / STEAM["MW"]
    k = sl.psat(T) / P                  # y/x on total-pressure basis

    def v_of(Vhc):
        L = max(F - Vhc, 1e-12)
        r = (Vhc + S) / L
        return n * k * r / (1 + k * r)

    def g(Vhc):
        return v_of(Vhc).sum() - Vhc

    lo, hi = 1e-12 * F, F * (1 - 1e-12)
    if g(lo) <= 0 and S == 0:
        v = np.zeros_like(n)
    elif g(hi) >= 0:
        v = n.copy()
    else:
        Vhc = brentq(g, lo, hi, xtol=1e-10 * F)
        v = v_of(Vhc)
    vm = v * sl.MW
    return FlashResult(T, P, m - vm, vm, steam_kg)


def bubble_T(sl: Slate, m: np.ndarray, P_hc: float, lo=-50.0, hi=650.0) -> float:
    x = (m / sl.MW) / (m / sl.MW).sum()
    return brentq(lambda T: (x * sl.psat(T)).sum() - P_hc, lo, hi)


def dew_T(sl: Slate, m: np.ndarray, P_hc: float, lo=-50.0, hi=700.0) -> float:
    y = (m / sl.MW) / (m / sl.MW).sum()
    return brentq(lambda T: (y * P_hc / sl.psat(T)).sum() - 1.0, lo, hi)


def enthalpy(sl: Slate, liq: np.ndarray, vap: np.ndarray, T: float, steam_v: float = 0.0,
             water_l: float = 0.0) -> float:
    """Total enthalpy flow, kW (inputs kg/h)."""
    h = (liq * sl.hl(T)).sum() + (vap * sl.hv(T)).sum()
    h += steam_v * steam_h(T) + water_l * STEAM["cp_l"] * (T - T_REF)
    return h / 3600.0


def steam_h(T: float) -> float:
    """Approx. low-pressure superheated steam enthalpy, kJ/kg, ref liquid water 15 degC."""
    return STEAM["cp_l"] * (100 - T_REF) + STEAM["lam_b"] + STEAM["cp_v"] * (T - 100)


def water_psat(T: float) -> float:
    """Antoine, bar."""
    return 10 ** (5.40221 - 1838.675 / (T + 273.15 - 31.737))
