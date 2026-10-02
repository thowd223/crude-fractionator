"""3D model CFU-000-PL-3DM-001 (GLB via trimesh) + self-contained three.js viewer + PNG renders."""
from __future__ import annotations

import base64
import json
import math
from pathlib import Path

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

from .model import GRADE

TYPE_RGB = {
    "Column": (70, 110, 190), "Drum": (60, 160, 120), "Desalter": (40, 140, 110), "Shell & tube": (205, 130, 60),
    "Air cooler": (80, 170, 215), "Fired heater": (200, 70, 55), "Air preheater": (170, 90, 80), "Fan": (150, 60, 60),
    "Pump": (140, 80, 175), "Ejector": (120, 120, 120), "Package": (215, 180, 40),
    "_rack": (150, 150, 145), "_ground": (205, 205, 195), "_road": (110, 110, 110), "_building": (225, 225, 230),
    "_platform": (230, 200, 60), "_steel": (120, 125, 130), "_stack": (90, 90, 90), "_area": (240, 170, 60),
}
SECTIONS = 28


def _mat(rgb, alpha=255, metal=0.15, rough=0.75):
    return PBRMaterial(baseColorFactor=[rgb[0], rgb[1], rgb[2], alpha], metallicFactor=metal, roughnessFactor=rough,
                       doubleSided=True, alphaMode="BLEND" if alpha < 255 else None)


def box(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box(extents=[abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)])
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def obox(cx, cy, z0, L, W, H, rot):
    m = trimesh.creation.box(extents=[L, W, H])
    m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(rot), [0, 0, 1]))
    m.apply_translation([cx, cy, z0 + H / 2])
    return m


def vcyl(cx, cy, z0, z1, D, sections=SECTIONS):
    m = trimesh.creation.cylinder(radius=D / 2, height=z1 - z0, sections=sections)
    m.apply_translation([cx, cy, (z0 + z1) / 2])
    return m


def frustum(cx, cy, z0, z1, D0, D1, sections=SECTIONS):
    m = trimesh.creation.cylinder(radius=1.0, height=1.0, sections=sections)
    v = m.vertices.copy()
    top = v[:, 2] > 0
    v[top, :2] *= D1 / 2
    v[~top, :2] *= D0 / 2
    v[:, 2] = np.where(top, z1, z0)
    v[:, 0] += cx
    v[:, 1] += cy
    m.vertices = v
    return m


def head(cx, cy, z, D, up=True):
    s = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
    v = s.vertices
    s = trimesh.Trimesh(v * [D / 2, D / 2, D / 4], s.faces)
    s.apply_translation([cx, cy, z])
    return s


def hcyl(cx, cy, zc, L, D, rot):
    m = trimesh.creation.cylinder(radius=D / 2, height=max(L - D / 2, 0.2), sections=SECTIONS)
    caps = []
    for sgn in (-1, 1):
        s = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
        s = trimesh.Trimesh(s.vertices * [D / 2, D / 2, D / 4], s.faces)
        s.apply_translation([0, 0, sgn * (L - D / 2) / 2])
        caps.append(s)
    m = trimesh.util.concatenate([m] + caps)
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))   # axis -> x
    m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(rot), [0, 0, 1]))
    m.apply_translation([cx, cy, zc])
    return m


def item_meshes(it, L):
    """returns dict part -> list of meshes (plant coords, z = EL)"""
    t = it["type"]
    parts = {"body": [], "platforms": [], "steel": []}
    B = parts["body"]
    x, y = it["x"], it["y"]
    if it["shape"] == "vcyl":
        body = it.get("body") or [[it["z_base"], it["top_el"], it["D"]]]
        Dbot, Dtop = body[0][2], body[-1][2]
        btl, ttl = body[0][0], body[-1][1]
        if btl - Dbot / 4 > it["z_base"] + 0.1:
            B.append(vcyl(x, y, it["z_base"], btl, Dbot * 1.0))
        B.append(head(x, y, btl, Dbot))
        B.append(head(x, y, ttl, Dtop))
        prev = None
        for z0, z1, D in body:
            if prev:
                B.append(frustum(x, y, prev[0], z0, prev[1], D))
            B.append(vcyl(x, y, z0, z1, D))
            prev = (z1, D)
        if t == "Column":
            for p in L.structs["column_platforms"]:
                if p["tag"] == it["tag"]:
                    a = trimesh.creation.annulus(r_min=p["r_in"], r_max=p["r_out"], height=0.12, sections=SECTIONS)
                    a.apply_translation([x, y, p["el"]])
                    parts["platforms"].append(a)
                    rail = trimesh.creation.annulus(r_min=p["r_out"] - 0.05, r_max=p["r_out"], height=1.1, sections=SECTIONS)
                    rail.apply_translation([x, y, p["el"] + 0.55])
                    parts["platforms"].append(rail)
            # ladder
            r = Dbot / 2 + 0.6
            a = math.radians(135)
            lx, ly = x + r * math.cos(a), y + r * math.sin(a)
            parts["steel"].append(box(lx - 0.25, ly - 0.05, GRADE, lx + 0.25, ly + 0.05, it["top_tl"] + 1.0))
        else:
            for dx in (-1, 1):
                parts["steel"].append(box(x + dx * it["D"] / 2 - 0.05, y - 0.05, GRADE, x + dx * it["D"] / 2 + 0.05,
                                          y + 0.05, it["bottom_tl"]) if it["z_base"] < it["bottom_tl"] - 0.6 else box(0, 0, 0, 0.01, 0.01, 0.01))
    elif it["shape"] == "hcyl":
        D = it["D"]
        zc = it["z_base"] + D / 2
        B.append(hcyl(x, y, zc, it["L"], D, it["rotation"]))
        if it.get("boot"):
            b = it["boot"]
            a = math.radians(it["rotation"])
            bx, by = x + b["u"] * math.cos(a), y + b["u"] * math.sin(a)
            B.append(vcyl(bx, by, it["z_base"] - b["H"], it["z_base"] + 0.3, b["D"]))
        if it["z_base"] > GRADE + 0.2 and it["z_base"] < 110:
            a = math.radians(it["rotation"])
            for u in (-it["L"] * 0.3, it["L"] * 0.3):
                sx, sy = x + u * math.cos(a), y + u * math.sin(a)
                parts["steel"].append(obox(sx, sy, GRADE, 0.5, D * 0.8, it["z_base"] - GRADE + D * 0.3, it["rotation"]))
    elif it["shape"] == "heater":
        r, c, s = it["radiant"], it["convection"], it["stack"]
        Lh, W = it["L"], it["W"]
        for dx in (-Lh / 2 + 0.5, 0, Lh / 2 - 0.5):
            for dy in (-W / 2 + 0.5, W / 2 - 0.5):
                parts["steel"].append(box(x + dx - 0.3, y + dy - 0.3, GRADE, x + dx + 0.3, y + dy + 0.3, r["z0"]))
        B.append(box(x - Lh / 2, y - W / 2, r["z0"], x + Lh / 2, y + W / 2, r["z1"]))
        pts = []
        for zz, ll, ww in ((r["z1"], Lh, W), (r["z1"] + 2.5, c["L"], c["W"])):
            for sx in (-1, 1):
                for sy in (-1, 1):
                    pts.append([x + sx * ll / 2, y + sy * ww / 2, zz])
        B.append(trimesh.convex.convex_hull(np.array(pts)))
        B.append(box(x - c["L"] / 2, y - c["W"] / 2, r["z1"] + 2.5, x + c["L"] / 2, y + c["W"] / 2, c["z1"]))
        parts["stack"] = [vcyl(s["x"], s["y"], c["z1"], s["z1"], s["D"])]
        # platforms around radiant box top & convection
        parts["platforms"].append(box(x - Lh / 2 - 1.0, y - W / 2 - 1.0, r["z1"] - 0.1, x + Lh / 2 + 1.0, y - W / 2, r["z1"]))
        parts["platforms"].append(box(x - Lh / 2 - 1.0, y + W / 2, r["z1"] - 0.1, x + Lh / 2 + 1.0, y + W / 2 + 1.0, r["z1"]))
    elif t == "Air cooler":
        z0 = it["z_base"]
        x0, y0, x1, y1 = it["bbox"]
        B.append(box(x0 + 0.05, y0, z0, x1 - 0.05, y1, z0 + 1.2))
        B.append(box(x0 + 0.05, y0 - 0.4, z0 + 0.1, x1 - 0.05, y0, z0 + 1.6))      # headers
        B.append(box(x0 + 0.05, y1, z0 + 0.1, x1 - 0.05, y1 + 0.4, z0 + 1.6))
        B.append(box(x0 + 0.5, y0 + 0.5, z0 - 1.2, x1 - 0.5, y1 - 0.5, z0))          # plenum
        nf = it.get("fans", 2)
        for k in range(nf):
            fy = y0 + (y1 - y0) * (k + 0.5) / nf
            B.append(vcyl(it["x"], fy, z0 - 1.8, z0 - 1.2, 3.6))
    elif t == "Pump":
        a = math.radians(it["rotation"])
        Lp, Wp, Hp = it["L"], it["W"], it["height"]
        parts["steel"].append(obox(x, y, it["z_base"], Lp, Wp, 0.3, it["rotation"]))
        cx, cy = x + 0.25 * Lp * math.cos(a), y + 0.25 * Lp * math.sin(a)
        B.append(obox(cx, cy, it["z_base"] + 0.3, Lp * 0.45, Wp * 0.8, Hp * 0.8, it["rotation"]))
        mx, my = x - 0.25 * Lp * math.cos(a), y - 0.25 * Lp * math.sin(a)
        m = trimesh.creation.cylinder(radius=min(Wp, Hp) * 0.38, height=Lp * 0.42, sections=20)
        m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        m.apply_transform(trimesh.transformations.rotation_matrix(a, [0, 0, 1]))
        m.apply_translation([mx, my, it["z_base"] + 0.3 + min(Wp, Hp) * 0.4])
        B.append(m)
    else:
        B.append(obox(x, y, it["z_base"], it["L"], it["W"], it["height"], it["rotation"]))
    return parts


def rack_meshes(L):
    rk = L.rack
    out = []
    top = rk["tiers"][-1]["el"]
    for bx in rk["bents_x"]:
        for by in (rk["y0"], rk["y1"]):
            out.append(box(bx - 0.2, by - 0.2, GRADE, bx + 0.2, by + 0.2, top))
        for t in rk["tiers"]:
            out.append(box(bx - 0.15, rk["y0"], t["el"] - 0.45, bx + 0.15, rk["y1"], t["el"]))
    bx = rk["bents_x"]
    for t in rk["tiers"]:
        for by in (rk["y0"], rk["y1"]):
            for xa, xb in zip(bx[:-1], bx[1:]):
                out.append(box(xa, by - 0.12, t["el"] - 0.35, xb, by + 0.12, t["el"] - 0.1))
    # AC support structure
    acs = [i for i in L.items if i["type"] == "Air cooler"]
    for a in acs:
        x0, y0, x1, y1 = a["bbox"]
        for xx in (x0 + 0.2, x1 - 0.2):
            for yy in (rk["y0"] + 0.5, rk["y1"] - 0.5):
                out.append(box(xx - 0.12, yy - 0.12, top, xx + 0.12, yy + 0.12, a["z_base"]))
    # cable tray
    ct = rk["cable_tray"]
    for xa, xb in zip(bx[:-1], bx[1:]):
        out.append(box(xa, rk["y0"] - ct["bracket"], ct["el"], xb, rk["y0"] - 0.25, ct["el"] + 0.12))
    return out


def ejector_structure(L):
    es = L.ejector_structure
    out = []
    for xx in (es["x0"], es["x1"]):
        for yy in (es["y0"], es["y1"]):
            out.append(box(xx - 0.2, yy - 0.2, GRADE, xx + 0.2, yy + 0.2, es["top"]))
    for z in es["levels"] + [es["top"]]:
        out.append(box(es["x0"], es["y0"], z - 0.15, es["x1"], es["y1"], z))
    return out


def build_scene(L):
    """returns list of (node_name, mesh, rgb, info) in plant coordinates."""
    nodes = []
    S = L.structs
    nodes.append(("ground", box(-5, -5, GRADE - 0.4, 235, 155, GRADE - 0.02), TYPE_RGB["_ground"], None))
    for r in S["roads"]:
        nodes.append((r["id"], box(r["x0"], r["y0"], GRADE - 0.02, r["x1"], r["y1"], GRADE + 0.03), TYPE_RGB["_road"], None))
    for b in S["buildings"]:
        nodes.append((b["id"], box(b["x0"], b["y0"], GRADE, b["x1"], b["y1"], GRADE + b["height"]), TYPE_RGB["_building"], None))
    nodes.append(("PR-100", trimesh.util.concatenate(rack_meshes(L)), TYPE_RGB["_rack"], None))
    nodes.append(("ST-201", trimesh.util.concatenate(ejector_structure(L)), TYPE_RGB["_steel"], None))
    for it in L.items:
        parts = item_meshes(it, L)
        rgb = TYPE_RGB.get(it["type"], (150, 150, 150))
        nodes.append((it["tag"], trimesh.util.concatenate(parts["body"]), rgb, it["tag"]))
        if parts["platforms"]:
            nodes.append((it["tag"] + "__platforms", trimesh.util.concatenate(parts["platforms"]), TYPE_RGB["_platform"], it["tag"]))
        if parts["steel"]:
            nodes.append((it["tag"] + "__supports", trimesh.util.concatenate(parts["steel"]), TYPE_RGB["_steel"], it["tag"]))
        if parts.get("stack"):
            nodes.append((it["tag"] + "__stack", trimesh.util.concatenate(parts["stack"]), TYPE_RGB["_stack"], it["tag"]))
    return nodes


# glTF is Y-up: X = east, Y = EL - 100, Z = -north
TO_GLTF = np.array([[1, 0, 0, 0], [0, 0, 1, -GRADE], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)


def export_glb(nodes, path: Path):
    scene = trimesh.Scene()
    mats = {}
    for name, mesh, rgb, _ in nodes:
        m = mesh.copy()
        m.apply_transform(TO_GLTF)
        key = tuple(rgb)
        if key not in mats:
            mats[key] = _mat(rgb)
        m.visual = trimesh.visual.TextureVisuals(material=mats[key])
        scene.add_geometry(m, node_name=name, geom_name=name)
    data = scene.export(file_type="glb")
    path.write_bytes(data)
    return data


def renders(nodes, outdir: Path, L):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris, cols = [], []
    light = np.array([-0.4, -0.6, 0.75])
    light /= np.linalg.norm(light)
    gt = []
    for gx in range(0, 230, 5):
        for gy in range(0, 150, 5):
            gt.append([[gx, gy, GRADE], [gx + 5, gy, GRADE], [gx + 5, gy + 5, GRADE]])
            gt.append([[gx, gy, GRADE], [gx + 5, gy + 5, GRADE], [gx, gy + 5, GRADE]])
    tris.append(np.array(gt, float))
    cols.append(np.tile(np.array(TYPE_RGB["_ground"]) / 255.0, (len(gt), 1)))
    rt = []
    for r in L.structs["roads"]:
        xs = np.arange(r["x0"], r["x1"], 6.0).tolist() + [r["x1"]]
        ys = np.arange(r["y0"], r["y1"], 6.0).tolist() + [r["y1"]]
        for xa, xb in zip(xs[:-1], xs[1:]):
            for ya, yb in zip(ys[:-1], ys[1:]):
                z = GRADE + 0.25
                rt.append([[xa, ya, z], [xb, ya, z], [xb, yb, z]])
                rt.append([[xa, ya, z], [xb, yb, z], [xa, yb, z]])
    tris.append(np.array(rt, float))
    cols.append(np.tile(np.array([0.62, 0.62, 0.62]), (len(rt), 1)))
    for name, mesh, rgb, _ in nodes:
        if name == "ground" or name.startswith("RD-"):
            continue
        m = mesh
        tri = m.vertices[m.faces]
        n = m.face_normals
        sh = 0.45 + 0.55 * np.clip(np.abs(n @ light), 0, 1)
        base = np.array(rgb) / 255.0
        tris.append(tri)
        cols.append(np.clip(base[None, :] * sh[:, None], 0, 1))
    tris = np.concatenate(tris)
    cols = np.concatenate(cols)
    views = [("iso-SE", -55, 28, None), ("iso-SW", -130, 25, None), ("iso-NE-C101", 40, 22, (60, 130, 60, 125))]
    files = []
    for nm, az, el, crop in views:
        fig = plt.figure(figsize=(16, 10), dpi=110)
        ax = fig.add_subplot(111, projection="3d")
        ax.set_proj_type("ortho")
        sel = np.ones(len(tris), bool)
        if crop:
            sel = ((tris[:, :, 0].min(1) > crop[0] - 1) & (tris[:, :, 0].max(1) < crop[1] + 1)
                   & (tris[:, :, 1].min(1) > crop[2] - 1) & (tris[:, :, 1].max(1) < crop[3] + 1))
        pc = Poly3DCollection(tris[sel], facecolors=cols[sel], edgecolors="none", linewidths=0)
        ax.add_collection3d(pc)
        g = Poly3DCollection([[[-3, -3, GRADE], [233, -3, GRADE], [233, 153, GRADE], [-3, 153, GRADE]]],
                             facecolors=[(0.86, 0.86, 0.82)], edgecolors="none")
        xr = (crop[0], crop[1]) if crop else (0, 230)
        yr = (crop[2], crop[3]) if crop else (0, 150)
        ax.set_xlim(*xr)
        ax.set_ylim(*yr)
        ax.set_zlim(GRADE, GRADE + 50)
        ax.set_box_aspect((xr[1] - xr[0], yr[1] - yr[0], 50), zoom=1.2 if crop else 1.4)
        ax.view_init(elev=el, azim=az)
        ax.set_axis_off()
        # labels for main items
        for t in ("C-101", "C-201", "H-101", "H-201", "C-105", "C-106", "D-101A", "D-102", "PR-100"):
            if t == "PR-100":
                px, py, pz = 30, 75, 112
            else:
                it = L.by_tag[t]
                px, py, pz = it["x"], it["y"], it["top_el"] + 2
            if crop and not (crop[0] < px < crop[1] and crop[2] < py < crop[3]):
                continue
            ax.text(px, py, pz, t, fontsize=10, fontweight="bold", color="black", zorder=10)
        ax.set_title(f"CFU-000-PL-3DM-001  -  100 kBPSD CDU/VDU  -  {nm.replace('-', ' ')} view", fontsize=13)
        fig.subplots_adjust(0, 0, 1, 0.95)
        f = outdir / f"CFU-000-PL-3DM-001_render-{nm}.png"
        fig.savefig(f, dpi=110)
        plt.close(fig)
        files.append(f)
    return files


def viewer_html(glb: bytes, L, path: Path):
    meta = {}
    for it in L.items:
        meta[it["tag"]] = dict(type=it["type"], service=it["service"], x=it["x"], y=it["y"], z=it["z_base"],
                               top=it["top_el"], L=it["L"], W=it["W"], area=it.get("area", ""),
                               nozzles=len(it.get("nozzles", {})))
    for b in L.structs["buildings"]:
        meta[b["id"]] = dict(type="Building", service=b["name"], x=(b["x0"] + b["x1"]) / 2, y=(b["y0"] + b["y1"]) / 2,
                             z=GRADE, top=GRADE + b["height"], L=b["x1"] - b["x0"], W=b["y1"] - b["y0"], area="", nozzles=0)
    meta["PR-100"] = dict(type="Pipe rack", service="Main pipe rack, 3 tiers EL 106.0/108.5/111.0, bents @ 6 m",
                          x=108, y=75, z=GRADE, top=111.0, L=216, W=10, area="", nozzles=0)
    meta["ST-201"] = dict(type="Structure", service="Ejector structure (J-201/202/203, E-202/203/204)",
                          x=196, y=96, z=GRADE, top=124.0, L=12, W=8, area="VDU", nozzles=0)
    b64 = base64.b64encode(glb).decode()
    html = TEMPLATE.replace("__GLB__", b64).replace("__META__", json.dumps(meta))
    path.write_text(html)


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CDU/VDU 3D Model</title>
<style>
:root{--bg:#eef1f4;--panel:#ffffffee;--ink:#1d232a;--mute:#5b6570;--acc:#1f4e9c;--line:#d5dbe1}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#15191d;--panel:#1f252bee;--ink:#e6eaee;--mute:#9aa5b1;--acc:#7fb0ff;--line:#3a434c}}
:root[data-theme="dark"]{--bg:#15191d;--panel:#1f252bee;--ink:#e6eaee;--mute:#9aa5b1;--acc:#7fb0ff;--line:#3a434c}
html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font:14px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;overflow:hidden}
#c{position:fixed;inset:0}
.panel{position:fixed;background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:0 4px 18px #0002;backdrop-filter:blur(4px)}
#top{left:16px;top:16px;padding:10px 12px;max-width:min(420px,calc(100vw - 32px))}
#top h1{font-size:15px;margin:0 0 2px}#top .sub{color:var(--mute);font-size:12px;margin-bottom:8px}
#search{width:100%;box-sizing:border-box;padding:7px 9px;border:1px solid var(--line);border-radius:7px;background:transparent;color:var(--ink);font-size:14px}
.row{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
button{border:1px solid var(--line);background:transparent;color:var(--ink);padding:5px 9px;border-radius:7px;cursor:pointer;font-size:12px}
button:hover{border-color:var(--acc);color:var(--acc)}
#info{right:16px;top:16px;padding:12px 14px;width:min(300px,calc(100vw - 32px));display:none}
#info h2{margin:0 0 4px;font-size:18px;color:var(--acc)}#info table{border-collapse:collapse;width:100%;font-size:12.5px}
#info td{padding:2px 0;vertical-align:top}#info td:first-child{color:var(--mute);width:84px}
#legend{left:16px;bottom:16px;padding:8px 10px;font-size:12px;display:grid;grid-template-columns:repeat(2,auto);gap:3px 14px}
#legend span{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.lbl{position:fixed;transform:translate(-50%,-100%);font:600 11px system-ui,sans-serif;color:#111;background:#ffffffd0;padding:1px 4px;border-radius:4px;pointer-events:none;white-space:nowrap}
#tip{position:fixed;pointer-events:none;background:#111c;color:#fff;font-size:12px;padding:3px 7px;border-radius:5px;display:none}
#msg{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);color:var(--mute)}
@media (max-width:640px){#legend{display:none}#info{top:auto;bottom:16px}}
</style></head><body>
<canvas id="c"></canvas><div id="msg">Loading model...</div>
<div id="top" class="panel"><h1>CFU-000-PL-3DM-001 &middot; 100 kBPSD CDU/VDU</h1>
<div class="sub">Drag to orbit &middot; right-drag to pan &middot; wheel to zoom &middot; click equipment to identify</div>
<input id="search" list="tags" placeholder="Search tag (e.g. C-101, P-112A, E-108C)..." autocomplete="off"><datalist id="tags"></datalist>
<div class="row"><button id="bIso">Iso view</button><button id="bTop">Plan</button><button id="bS">South elev.</button><button id="bLbl">Labels on/off</button><button id="bReset">Clear</button></div></div>
<div id="info" class="panel"></div><div id="legend" class="panel"></div><div id="tip"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const GLB_B64="__GLB__";
const META=__META__;
const TYPES={"Column":"#466ebe","Drum":"#3ca078","Desalter":"#288c6e","Shell & tube":"#cd823c","Air cooler":"#50aad7","Fired heater":"#c84637","Pump":"#8c50af","Ejector":"#787878","Package":"#d7b428","Platforms":"#e6c83c","Pipe rack / steel":"#96968f"};
const lg=document.getElementById('legend');for(const[k,v]of Object.entries(TYPES)){lg.insertAdjacentHTML('beforeend',`<div><span style="background:${v}"></span>${k}</div>`)}
const dl=document.getElementById('tags');Object.keys(META).sort().forEach(t=>dl.insertAdjacentHTML('beforeend',`<option value="${t}">`));
const canvas=document.getElementById('c');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
const scene=new THREE.Scene();
function bg(){const d=getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();scene.background=new THREE.Color(d||'#eef1f4')}bg();
const camera=new THREE.PerspectiveCamera(40,1,0.5,3000);
const controls=new THREE.OrbitControls(camera,canvas);controls.enableDamping=true;controls.dampingFactor=0.12;
scene.add(new THREE.HemisphereLight(0xffffff,0x667788,0.85));
const sun=new THREE.DirectionalLight(0xffffff,0.75);sun.position.set(-150,220,180);scene.add(sun);
// plant (E,N,EL) -> world
const W=(x,y,z)=>new THREE.Vector3(x,z-100,-y);
function resize(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}addEventListener('resize',resize);resize();
function view(kind){const c=W(115,75,110);if(kind==='top'){camera.position.set(115,330,-74.9)}else if(kind==='s'){camera.position.set(115,25,140)}else{camera.position.set(-60,150,120)}controls.target.copy(W(115,75,108));controls.update()}
view('iso');
const pickables=[];const byTag={};let selected=null;const origMat=new Map();
function b64ToBuf(b){const s=atob(b);const u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);return u.buffer}
const loader=new THREE.GLTFLoader();
loader.parse(b64ToBuf(GLB_B64),'',g=>{
  scene.add(g.scene);
  g.scene.traverse(o=>{if(o.isMesh){
    const tag=o.name.split('__')[0];o.userData.tag=tag;pickables.push(o);(byTag[tag]=byTag[tag]||[]).push(o);
    if(o.material){o.material.side=THREE.DoubleSide}}});
  document.getElementById('msg').remove();buildLabels();
},e=>{document.getElementById('msg').textContent='Model failed to load: '+e});
// labels
const MAIN=["C-101","C-102","C-103","C-104","C-105","C-106","C-201","H-101","H-201","D-101A","D-101B","D-102","D-105","D-106","D-104","D-201","A-101-B1","E-108A","E-111A","E-101","SS-100","FAR-100","PR-100","ST-201","P-112A","P-204A"];
let labels=[],showLbl=true;
function buildLabels(){MAIN.forEach(t=>{const m=META[t];if(!m)return;const d=document.createElement('div');d.className='lbl';d.textContent=t.replace('-B1','');document.body.appendChild(d);labels.push({d,p:W(m.x,m.y,m.top+2)})})}
function updLabels(){const w=innerWidth,h=innerHeight;labels.forEach(l=>{const v=l.p.clone().project(camera);const vis=showLbl&&v.z<1&&Math.abs(v.x)<1.05&&Math.abs(v.y)<1.05;l.d.style.display=vis?'block':'none';if(vis){l.d.style.left=((v.x+1)/2*w)+'px';l.d.style.top=((1-v.y)/2*h)+'px'}})}
// picking
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();const tip=document.getElementById('tip');
function pick(ev){const r=canvas.getBoundingClientRect();mouse.x=(ev.clientX-r.left)/r.width*2-1;mouse.y=-(ev.clientY-r.top)/r.height*2+1;ray.setFromCamera(mouse,camera);
  const hit=ray.intersectObjects(pickables,false).find(h=>!['ground'].includes(h.object.userData.tag)&&!/^RD-/.test(h.object.userData.tag));return hit?hit.object.userData.tag:null}
let down=null;canvas.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
canvas.addEventListener('pointerup',e=>{if(down&&Math.hypot(e.clientX-down[0],e.clientY-down[1])<5){const t=pick(e);select(t,false)}down=null});
canvas.addEventListener('pointermove',e=>{if(e.buttons)return;const t=pick(e);if(t&&META[t]){tip.style.display='block';tip.textContent=t+' - '+META[t].service;tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+10)+'px'}else tip.style.display='none'});
function highlight(tag,on){(byTag[tag]||[]).forEach(o=>{if(on){origMat.set(o,o.material);const m=o.material.clone();m.emissive=new THREE.Color(0xff5500);m.emissiveIntensity=0.55;o.material=m}else if(origMat.has(o)){o.material=origMat.get(o);origMat.delete(o)}})}
function select(tag,fly){if(selected)highlight(selected,false);selected=null;const box=document.getElementById('info');
  if(!tag||!META[tag]){box.style.display='none';return}selected=tag;highlight(tag,true);const m=META[tag];
  box.innerHTML=`<h2>${tag}</h2><table><tr><td>Service</td><td>${m.service}</td></tr><tr><td>Type</td><td>${m.type}</td></tr>
  <tr><td>Location</td><td>E ${m.x.toFixed(1)} / N ${m.y.toFixed(1)}</td></tr><tr><td>Base / top</td><td>EL ${m.z.toFixed(3)} / EL ${m.top.toFixed(1)}</td></tr>
  <tr><td>Footprint</td><td>${m.L.toFixed(1)} x ${m.W.toFixed(1)} m</td></tr>${m.nozzles?`<tr><td>Nozzles</td><td>${m.nozzles} in layout.json</td></tr>`:''}</table>`;box.style.display='block';
  if(fly){const c=W(m.x,m.y,(m.z+m.top)/2);const d=Math.max(25,Math.max(m.L,m.W,m.top-m.z)*2.2);controls.target.copy(c);camera.position.set(c.x-d*0.7,c.y+d*0.6,c.z+d*0.8);controls.update()}}
const sb=document.getElementById('search');
sb.addEventListener('change',()=>{const v=sb.value.trim().toUpperCase();const t=Object.keys(META).find(k=>k.toUpperCase()===v)||Object.keys(META).find(k=>k.toUpperCase().startsWith(v));if(t)select(t,true)});
sb.addEventListener('keydown',e=>{if(e.key==='Enter')sb.dispatchEvent(new Event('change'))});
document.getElementById('bIso').onclick=()=>view('iso');document.getElementById('bTop').onclick=()=>view('top');document.getElementById('bS').onclick=()=>view('s');
document.getElementById('bLbl').onclick=()=>{showLbl=!showLbl};document.getElementById('bReset').onclick=()=>{select(null);sb.value=''};
window.__select=select;
(function loop(){requestAnimationFrame(loop);controls.update();renderer.render(scene,camera);updLabels()})();
</script></body></html>
"""


def build(L, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    nodes = build_scene(L)
    glb = export_glb(nodes, outdir / "CFU-000-PL-3DM-001.glb")
    viewer_html(glb, L, outdir / "viewer.html")
    renders(nodes, outdir, L)
