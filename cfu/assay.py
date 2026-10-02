"""Crude assay -> pseudo-component slate (Arab Light design case)."""
from __future__ import annotations

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

from . import basis
from .thermo import Component, Slate

BBL_M3 = 0.158987
LIGHT_ENDS = {  # name: Tb K, SG, MW, Tc K, Pc bar, omega
    "C2": (184.6, 0.356, 30.07, 305.3, 48.72, 0.099),
    "C3": (231.1, 0.507, 44.10, 369.8, 42.48, 0.152),
    "iC4": (261.4, 0.563, 58.12, 408.1, 36.48, 0.181),
    "nC4": (272.7, 0.584, 58.12, 425.1, 37.96, 0.200),
}
EDGES = ([36] + list(range(50, 396, 15)) + list(range(420, 596, 25)) + [650, 700, 750, 800, 850])
S_PROFILE = [(36, .01), (100, .03), (165, .08), (235, .35), (320, 1.4), (400, 2.2), (500, 2.7),
             (600, 3.6), (850, 4.3)]


def _tbp():
    pts = basis.CRUDE["tbp"]
    lv = np.array([p[0] for p in pts]) / 100
    t = np.array([p[1] for p in pts], float)
    return PchipInterpolator(t, lv), PchipInterpolator(lv, t)


def build_slate(K0: float | None = None) -> Slate:
    lv_of_T, T_of_lv = _tbp()

    def make(K0):
        comps = []
        for n, (tb, sg, mw, tc, pc, w) in LIGHT_ENDS.items():
            comps.append(Component(n, tb, sg, mw, tc, pc, w, defined=True,
                                   lv_frac=basis.CRUDE["light_ends_lv"][n] / 100))
        for lo, hi in zip(EDGES[:-1], EDGES[1:]):
            lv_lo, lv_hi = float(lv_of_T(lo)), float(lv_of_T(hi))
            tb = float(T_of_lv((lv_lo + lv_hi) / 2))
            K = K0 - 0.00025 * (tb - 100)
            sg = ((tb + 273.15) * 1.8) ** (1 / 3) / K
            comps.append(Component(f"NBP{int(round(tb))}", tb + 273.15, sg, lv_frac=lv_hi - lv_lo))
        return comps

    target_sg = 141.5 / (basis.CRUDE["api"] + 131.5)

    def err(K0):
        comps = make(K0)
        v = np.array([c.lv_frac for c in comps])
        sg = np.array([c.SG for c in comps])
        return (v * sg).sum() / v.sum() - target_sg

    if K0 is None:
        K0 = brentq(err, 11.0, 13.0)
    comps = make(K0)
    # sulfur distribution scaled to bulk
    st, sv = zip(*S_PROFILE)
    m = np.array([c.lv_frac * c.SG for c in comps])
    s_raw = np.array([0.0 if c.defined else np.interp(c.Tb_C, st, sv) for c in comps])
    scale = basis.CRUDE["sulfur_wt"] / ((m * s_raw).sum() / m.sum())
    for c, s in zip(comps, s_raw):
        c.sulfur = s * scale / 100
    sl = Slate(comps)
    sl.K0 = K0
    return sl


def crude_mass_vector(sl: Slate, bpsd: float = basis.CAPACITY_BPSD) -> np.ndarray:
    m3h = bpsd * BBL_M3 / 24
    return np.array([c.lv_frac * m3h * c.rho15 for c in sl.c])


def bpsd(sl: Slate, m: np.ndarray) -> float:
    """Liquid volume at 15 degC expressed as BPSD."""
    return float((m / (sl.SG * 999.0)).sum() * 24 / BBL_M3)


def api(sl: Slate, m: np.ndarray) -> float:
    v = (m / (sl.SG * 999.0)).sum()
    sg = m.sum() / v / 999.0
    return 141.5 / sg - 131.5


def tbp_points(sl: Slate, m: np.ndarray, pcts=(0.5, 5, 10, 30, 50, 70, 90, 95, 99.5)):
    """TBP of a blend from its pseudo-component volumes (linear within cuts)."""
    v = m / (sl.SG * 999.0)
    order = np.argsort(sl.Tb)
    tb, v = sl.Tb[order], v[order]
    cum = np.cumsum(v) / v.sum() * 100
    mid = cum - v / v.sum() * 50
    return {p: float(np.interp(p, mid, tb)) for p in pcts}


def d86_from_tbp(tbp: dict) -> dict:
    """Riazi-Daubert (API TDB 3A1.1) inverse TBP->ASTM D86, T in K."""
    coef = {0.5: (0.9177, 1.0019), 10: (0.5564, 1.0900), 30: (0.7617, 1.0425), 50: (0.9013, 1.0176),
            70: (0.8821, 1.0226), 90: (0.9552, 1.0110), 99.5: (0.8177, 1.0355)}
    out = {}
    for p, (a, b) in coef.items():
        if p in tbp:
            T = tbp[p] + 273.15
            out[p] = (T / a) ** (1 / b) - 273.15
    return out
