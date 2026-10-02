"""Run all mechanical calculations and export data/mech.json."""
from __future__ import annotations

import json
import math

from . import geometry, heaters, hx, pumps, vessel
from .common import DATA

ELEV_DRUMS = {          # bottom-of-shell elevation above grade (m) - layout assumptions for NPSH
    "D-101A": 1.5, "D-101B": 1.5, "D-102": 7.0, "D-103": 1.0, "D-104": 1.0, "D-105": 5.0, "D-106": 6.0,
    "D-201": 0.5, "D-202": 1.0,
}


def run():
    npshr = pumps.column_bottom_npshr()
    cols = {}
    geoms = {}
    for g in geometry.columns():
        bp = g.get("bottoms_pump")
        if bp:
            g["npshr"] = npshr[bp[:5]][0]
            g["npshr_speed"] = npshr[bp[:5]][1]
        r = vessel.design_column(g)
        cols[g["tag"]] = r
        geoms[g["tag"]] = g
    drums = {}
    for g in geometry.drums():
        r = vessel.design_drum(g)
        r["BOS_el"] = ELEV_DRUMS.get(g["tag"], 1.0)
        drums[g["tag"]] = r
    # elevations for pump NPSH
    el = {}
    for t, g in geoms.items():
        sk = cols[t]["skirt_h"]
        el[t] = dict(BTL=sk, LLL=sk + g["levels"]["LLL"])
    gC = geoms["C-101"]
    tz = {tr["no"]: tr["z"] for tr in gC["trays"]}
    el["C-101"]["draw"] = {n: cols["C-101"]["skirt_h"] + tz[n] - 0.35 for n in (3, 13, 25)}
    g2 = geoms["C-201"]
    it = {i["name"]: i for i in g2["items"]}
    sk2 = cols["C-201"]["skirt_h"]
    el["C-201"]["draw"] = dict(LVGO=sk2 + it["LVGO total-draw collector"]["z0"] - 0.3,
                               HVGO=sk2 + it["HVGO total-draw collector"]["z0"] - 0.3,
                               SLOP=sk2 + it["Slop wax collector"]["z0"] - 0.3)
    for t, d in drums.items():
        b = d["BOS_el"]
        el[t] = dict(LLL=b + 0.15 * d["D"], boot_LLL=b - (d["boot"]["L"] if d["boot"] else 0) + 0.4)
    pdata = pumps.pump_data(el)
    hts = {}
    for t in ("H-101", "H-201"):
        td = heaters.tube_design(t)
        geo = heaters.heater_geometry(t)
        hts[t] = dict(tube=td, geo=geo, W=heaters.heater_weight(geo, td))
    st = hx.shell_tube()
    ac = hx.air_coolers()
    ps = hx.psv_data()
    calc = dict(columns=cols, geoms=geoms, drums=drums, pumps=pdata, heaters=hts, st=st, ac=ac, psv=ps, elev=el)
    export(calc)
    return calc


def _r(x, n=1):
    return None if x is None else round(float(x), n)


def export(c):
    out = dict(_meta=dict(doc="CFU-000-ME-CAL-001", rev="A", units="t = tonnes, thickness mm, elevations m above "
                                                                   "grade (grade = EL 100.000)",
                          note="FEED estimates; weights +/-15 % (vessels), +/-30 % (heaters/packages)"),
               items={})
    E = out["items"]
    for t, r in c["columns"].items():
        W = r["W"]
        E[t] = dict(type="Column", material=r["mat"], design_P_barg=r["Pd"], design_T_C=r["Td"], full_vacuum=r["fv"],
                    CA_mm=r["CA"], joint_eff=r["E"],
                    shell_courses=[dict(section=s["name"], ID_mm=s["D_mm"], z_from_m=_r(s["z0"], 2),
                                        z_to_m=_r(s["z1"], 2), t_req_mm=_r(s["t_req"]), t_ext_mm=s["t_ext"],
                                        t_nom_mm=s["t_nom"],
                                        stiffening_rings=(dict(spacing_mm=_r(s["ext"]["Ls"], 0), n=s.get("n_rings"),
                                                               size_mm=f"{s['ring']['h']}x{s['ring']['b']} flat bar")
                                                          if s.get("ring") else None)) for s in r["segs"]],
                    shell_t_max_mm=max(s["t_nom"] for s in r["segs"]),
                    shell_weight_kg=round(W["steel"]),
                    head_top_t_mm=r["heads"]["top"]["t_nom"], head_bottom_t_mm=r["heads"]["bottom"]["t_nom"],
                    skirt_height_m=r["skirt_h"], skirt_t_mm=r["skirt"]["t_nom"], skirt_OD_mm=_r(r["skirt"]["D_mm"], 0),
                    BTL_elevation_m=_r(100 + r["skirt_h"], 3),
                    top_elevation_m=_r(100 + W["H_total"], 3),
                    insulation_mm=W["ins_mm"],
                    weight_fabricated_t=_r(W["fabricated"] / 1e3), weight_empty_t=_r(W["empty"] / 1e3),
                    weight_operating_t=_r(W["operating"] / 1e3), weight_hydrotest_t=_r(W["hydrotest"] / 1e3),
                    weight_breakdown_t={k: _r(v / 1e3) for k, v in W["cat"].items()},
                    hydrotest_P_top_barg=_r(r["hydro"]["Pt_top"], 2), hydrotest_P_bottom_barg=_r(r["hydro"]["Pt_bot"], 2),
                    wind_base_shear_kN=_r(r["wind"]["V_base"] / 1e3, 0),
                    wind_base_moment_kNm=_r(r["wind"]["M_base"] / 1e3, 0),
                    wind_basis="ASCE 7-16, V=150 mph, Exp. C, strength level (ASD = 0.6 x)",
                    gust_factor=_r(r["wind"]["G"], 3), natural_freq_Hz=_r(r["fn"], 2),
                    anchor_bolts=dict(n=r["anchor"]["n"], size=r["anchor"]["size"], bcd_m=_r(r["anchor"]["Dbc"], 2),
                                      F_kN=_r(r["anchor"]["F_bolt_kN"], 0)),
                    volume_m3=_r(W["V_m3"]))
    for t, r in c["drums"].items():
        W = r["W"]
        E[t] = dict(type="Desalter" if "101" in t else "Drum", material=r["mat"], orient=r["orient"],
                    design_P_barg=r["Pd"], design_T_C=r["Td"], CA_mm=r["CA"], joint_eff=r["E"], ID_mm=r["D"] * 1000,
                    TT_m=r["L"], shell_t_mm=r["t_nom"],
                    shell_weight_kg=round(W["shell"] + W["heads"] + W["boot"] + W["supports"] + W["nozzles"]), head_t_mm=r["t_head_nom"], shell_t_req_mm=_r(r["t_req"]),
                    hydrotest_P_barg=_r(r["Pt"], 2), volume_m3=_r(r["Vol"]), insulation_mm=r["ins_mm"],
                    support="saddles" if r["orient"] == "H" else "legs / skirt",
                    bottom_elevation_m=_r(100 + r["BOS_el"], 3),
                    weight_fabricated_t=_r(W["fabricated"] / 1e3), weight_empty_t=_r(W["empty"] / 1e3),
                    weight_operating_t=_r(W["operating"] / 1e3), weight_hydrotest_t=_r(W["hydrotest"] / 1e3))
    for t, h in c["heaters"].items():
        W, td, g = h["W"], h["tube"], h["geo"]
        E[t] = dict(type="Fired heater", tube_OD_mm=td["OD"], tube_wall_min_mm=_r(td["t_min"], 2),
                    tube_schedule=td["sched"][0], tube_wall_mm=td["sched"][1], design_metal_T_C=td["Tdm"],
                    governing=td["gov"], overall_L_m=_r(g["L_out"]), overall_W_m=_r(g["W_out"]),
                    stack_top_elevation_m=_r(100 + g["H_top"]), stack_D_m=g["stack_D"],
                    weight_empty_t=_r(W["empty"] / 1e3), weight_operating_t=_r(W["operating"] / 1e3),
                    weight_hydrotest_t=_r(W["hydrotest"] / 1e3),
                    weight_breakdown_t={k: _r(v / 1e3) for k, v in W.items() if k not in ("coil_vol",)})
    for d in c["st"]:
        E[d["tag"]] = dict(type="Shell & tube", size=d["size"], shells=d["n_shells"], shell_ID_mm=d["Ds"],
                           shell_t_mm=d["t_shell"], tubes_per_shell=d["Nt"], tube_OD_mm=d["OD"], tube_L_mm=d["L"],
                           weight_empty_t_per_shell=_r(d["empty"] / 1e3),
                           weight_operating_t_per_shell=_r(d["operating"] / 1e3),
                           weight_hydrotest_t_per_shell=_r(d["hydrotest"] / 1e3),
                           weight_empty_t=_r(d["empty"] * d["n_shells"] / 1e3),
                           weight_operating_t=_r(d["operating"] * d["n_shells"] / 1e3))
    for d in c["ac"]:
        E[d["tag"]] = dict(type="Air cooler", bays=d["bays"], bays_required_6_rows=d["bays_req_6rows"],
                           rows=d["rows_sel"], weight_empty_t=_r(d["empty"] / 1e3),
                           weight_operating_t=_r(d["operating"] / 1e3))
    for p in c["pumps"]:
        E[p["tag"]] = dict(type="Pump", npsha_m=_r(p["npsha"]), npshr_est_m=_r(p["npshr_est"]), speed_rpm=p["speed"],
                           weight_t_each=p["weight_t"], weight_operating_t=p["weight_t"])
    (DATA / "mech.json").write_text(json.dumps(out, indent=1))
    return out
