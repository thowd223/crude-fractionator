"""Piping 3D model CFU-000-PI-3DM-002 (GLB) + combined equipment/piping viewer (viewer-piping.html)."""
from __future__ import annotations

import base64
import json
import math
from pathlib import Path

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

from . import specs

GRADE = 100.0
TO_GLTF = np.array([[1, 0, 0, 0], [0, 0, 1, -GRADE], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)
VALVE_RGB = (35, 35, 40)
SUPPORT_RGB = (120, 125, 130)


def _cyl(p0, p1, r, sections=14):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    v = p1 - p0
    L = float(np.linalg.norm(v))
    if L < 1e-4:
        return None
    m = trimesh.creation.cylinder(radius=r, height=L, sections=sections)
    z = np.array([0, 0, 1.0])
    d = v / L
    ax = np.cross(z, d)
    if np.linalg.norm(ax) < 1e-9:
        R = np.eye(4) if d[2] > 0 else trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])
    else:
        R = trimesh.transformations.rotation_matrix(math.acos(max(-1, min(1, float(np.dot(z, d))))), ax)
    m.apply_transform(R)
    m.apply_translation((p0 + p1) / 2)
    return m


def route_mesh(r):
    parts, vparts = [], []
    for b in r.branches:
        for e in r.elements[b.id]:
            n = e.get("nps") or b.nps
            rad = specs.od(n) / 2000.0
            p0, p1 = b.point_at(e["d0"]), b.point_at(e["d1"])
            if e["kind"] in ("gate", "globe", "check", "cv"):
                c = _cyl(p0, p1, rad * 1.45)
                if c is not None:
                    vparts.append(c)
                mid = (p0 + p1) / 2
                up = np.array([0, 0, 1.0]) if abs(b.dir_at((e["d0"] + e["d1"]) / 2)[2]) < 0.7 else np.array([1.0, 0, 0])
                st = _cyl(mid, mid + up * (rad * 2.6 + 0.25), max(0.025, rad * 0.25), 8)
                if st is not None:
                    vparts.append(st)
                continue
            if e["kind"] == "flange":
                c = _cyl(p0, p1, rad * 1.5)
                if c is not None:
                    vparts.append(c)
                continue
        for i in range(len(b.pts) - 1):
            # pipe at the nps of the segment midpoint
            dm = (b.cum[i] + b.cum[i + 1]) / 2
            n = r._nps_at(b, dm)
            c = _cyl(b.pts[i], b.pts[i + 1], specs.od(n) / 2000.0)
            if c is not None:
                parts.append(c)
        for i in range(1, len(b.pts) - 1):
            n = r._nps_at(b, b.cum[i])
            s = trimesh.creation.icosphere(subdivisions=1, radius=specs.od(n) / 2000.0)
            s.apply_translation(b.pts[i])
            parts.append(s)
    sup = []
    for s in r.supports:
        p = np.array(s["pt"])
        h = 0.18
        bx = trimesh.creation.box(extents=[0.3, 0.3, h])
        n = r.br(s["branch"]).nps
        bx.apply_translation(p - [0, 0, specs.od(n) / 2000.0 + h / 2])
        sup.append(bx)
    return (trimesh.util.concatenate(parts) if parts else None,
            trimesh.util.concatenate(vparts) if vparts else None,
            trimesh.util.concatenate(sup) if sup else None)


def _mat(rgb):
    return PBRMaterial(baseColorFactor=[rgb[0], rgb[1], rgb[2], 255], metallicFactor=0.3, roughnessFactor=0.55,
                       doubleSided=True)


def export_glb(routes, path: Path):
    scene = trimesh.Scene()
    mats = {}
    for r in routes:
        pipe, valves, sup = route_mesh(r)
        rgb = specs.cls(r.cls)["rgb"]
        for suffix, m, col in (("pipe", pipe, rgb), ("valves", valves, VALVE_RGB), ("supports", sup, SUPPORT_RGB)):
            if m is None:
                continue
            m = m.copy()
            m.apply_transform(TO_GLTF)
            if col not in mats:
                mats[col] = _mat(col)
            m.visual = trimesh.visual.TextureVisuals(material=mats[col])
            nm = f"{r.line_no}__{suffix}"
            scene.add_geometry(m, node_name=nm, geom_name=nm)
    data = scene.export(file_type="glb")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def viewer(eq_glb: bytes, pipe_glb: bytes, meta: dict, path: Path):
    classes = {c: "#%02x%02x%02x" % v["rgb"] for c, v in specs.CLASSES.items()}
    html = TEMPLATE.replace("__EQ__", base64.b64encode(eq_glb).decode()) \
        .replace("__PI__", base64.b64encode(pipe_glb).decode()) \
        .replace("__META__", json.dumps(meta)).replace("__CLS__", json.dumps(classes))
    path.write_text(html)


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CDU/VDU Piping 3D</title>
<style>
:root{--bg:#eef1f4;--panel:#ffffffee;--ink:#1d232a;--mute:#5b6570;--acc:#1f4e9c;--line:#d5dbe1}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#15191d;--panel:#1f252bee;--ink:#e6eaee;--mute:#9aa5b1;--acc:#7fb0ff;--line:#3a434c}}
:root[data-theme="dark"]{--bg:#15191d;--panel:#1f252bee;--ink:#e6eaee;--mute:#9aa5b1;--acc:#7fb0ff;--line:#3a434c}
html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font:14px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;overflow:hidden}
#c{position:fixed;inset:0}
.panel{position:fixed;background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:0 4px 18px #0002}
#top{left:16px;top:16px;padding:10px 12px;max-width:min(440px,calc(100vw - 32px))}
#top h1{font-size:15px;margin:0 0 2px}#top .sub{color:var(--mute);font-size:12px;margin-bottom:8px}
#search{width:100%;box-sizing:border-box;padding:7px 9px;border:1px solid var(--line);border-radius:7px;background:transparent;color:var(--ink);font-size:14px}
.row{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;align-items:center}
button{border:1px solid var(--line);background:transparent;color:var(--ink);padding:5px 9px;border-radius:7px;cursor:pointer;font-size:12px}
button:hover,button.on{border-color:var(--acc);color:var(--acc)}
label{font-size:12px;color:var(--mute);display:flex;gap:4px;align-items:center}
#info{right:16px;top:16px;padding:12px 14px;width:min(320px,calc(100vw - 32px));display:none}
#info h2{margin:0 0 6px;font-size:15px;color:var(--acc);word-break:break-all}
#info table{border-collapse:collapse;width:100%;font-size:12.5px}#info td{padding:2px 0;vertical-align:top}
#info td:first-child{color:var(--mute);width:92px}
#legend{left:16px;bottom:16px;padding:8px 10px;font-size:12px;display:grid;grid-template-columns:repeat(3,auto);gap:3px 14px}
#legend span{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
#tip{position:fixed;pointer-events:none;background:#111c;color:#fff;font-size:12px;padding:3px 7px;border-radius:5px;display:none}
#msg{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);color:var(--mute)}
@media (max-width:640px){#legend{display:none}#info{top:auto;bottom:16px}}
</style></head><body>
<canvas id="c"></canvas><div id="msg">Loading models...</div>
<div id="top" class="panel"><h1>CFU-000-PI-3DM-002 &middot; Piping + Equipment</h1>
<div class="sub">Drag to orbit &middot; right-drag pan &middot; wheel zoom &middot; click a pipe to identify the line</div>
<input id="search" list="lns" placeholder="Search line no. (e.g. P-100-085) or tag" autocomplete="off"><datalist id="lns"></datalist>
<div class="row"><label><input type="checkbox" id="tEq" checked>Equipment</label><label><input type="checkbox" id="tPi" checked>Piping</label>
<label><input type="checkbox" id="tGh">Ghost equipment</label><label><input type="checkbox" id="tCr">Iso lines only</label></div>
<div class="row"><button id="bIso">Iso view</button><button id="bTop">Plan</button><button id="bS">South elev.</button><button id="bReset">Clear</button></div></div>
<div id="info" class="panel"></div><div id="legend" class="panel"></div><div id="tip"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const EQ_B64="__EQ__";
const PI_B64="__PI__";
const META=__META__;
const CLS=__CLS__;
const lg=document.getElementById('legend');for(const[k,v]of Object.entries(CLS)){lg.insertAdjacentHTML('beforeend',`<div><span style="background:${v}"></span>${k}</div>`)}
const dl=document.getElementById('lns');Object.keys(META).sort().forEach(t=>dl.insertAdjacentHTML('beforeend',`<option value="${t}">`));
const canvas=document.getElementById('c');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
const scene=new THREE.Scene();
function bg(){const d=getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();scene.background=new THREE.Color(d||'#eef1f4')}bg();
const camera=new THREE.PerspectiveCamera(40,1,0.5,3000);
const controls=new THREE.OrbitControls(camera,canvas);controls.enableDamping=true;controls.dampingFactor=0.12;
scene.add(new THREE.HemisphereLight(0xffffff,0x667788,0.9));
const sun=new THREE.DirectionalLight(0xffffff,0.7);sun.position.set(-150,220,180);scene.add(sun);
const W=(x,y,z)=>new THREE.Vector3(x,z-100,-y);
function resize(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}addEventListener('resize',resize);resize();
function view(kind){if(kind==='top'){camera.position.set(115,330,-74.9)}else if(kind==='s'){camera.position.set(115,25,140)}else{camera.position.set(-40,120,95)}controls.target.copy(W(110,80,108));controls.update()}
view('iso');
function b64ToBuf(b){const s=atob(b);const u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);return u.buffer}
const loader=new THREE.GLTFLoader();
let eqRoot=null,piRoot=null;const pipes=[];const byLine={};const eqMeshes=[];let selected=null;const orig=new Map();
let pending=2;function done(){if(--pending===0){document.getElementById('msg').remove()}}
loader.parse(b64ToBuf(EQ_B64),'',g=>{eqRoot=g.scene;scene.add(eqRoot);eqRoot.traverse(o=>{if(o.isMesh){o.userData.tag=o.name.split('__')[0];eqMeshes.push(o);if(o.material)o.material.side=THREE.DoubleSide}});done()},e=>{document.getElementById('msg').textContent='Equipment model failed: '+e});
loader.parse(b64ToBuf(PI_B64),'',g=>{piRoot=g.scene;scene.add(piRoot);piRoot.traverse(o=>{if(o.isMesh){const ln=o.name.split('__')[0];o.userData.line=ln;pipes.push(o);(byLine[ln]=byLine[ln]||[]).push(o)}});done()},e=>{document.getElementById('msg').textContent='Piping model failed: '+e});
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();const tip=document.getElementById('tip');
function pick(ev){const r=canvas.getBoundingClientRect();mouse.x=(ev.clientX-r.left)/r.width*2-1;mouse.y=-(ev.clientY-r.top)/r.height*2+1;ray.setFromCamera(mouse,camera);
  const objs=pipes.filter(o=>o.visible&&piRoot&&piRoot.visible);const h=ray.intersectObjects(objs,false)[0];if(h)return{line:h.object.userData.line};
  if(eqRoot&&eqRoot.visible){const he=ray.intersectObjects(eqMeshes,false).find(x=>x.object.userData.tag!=='ground'&&!/^RD-/.test(x.object.userData.tag));if(he)return{tag:he.object.userData.tag}}return null}
let down=null;canvas.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
canvas.addEventListener('pointerup',e=>{if(down&&Math.hypot(e.clientX-down[0],e.clientY-down[1])<5){const p=pick(e);select(p&&p.line,false,p&&p.tag)}down=null});
canvas.addEventListener('pointermove',e=>{if(e.buttons)return;const p=pick(e);if(p){tip.style.display='block';tip.textContent=p.line?(p.line+(META[p.line]?' - '+META[p.line].service:'')):p.tag;tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+10)+'px'}else tip.style.display='none'});
function hl(ln,on){(byLine[ln]||[]).forEach(o=>{if(on){orig.set(o,o.material);const m=o.material.clone();m.emissive=new THREE.Color(0xff5500);m.emissiveIntensity=0.7;o.material=m}else if(orig.has(o)){o.material=orig.get(o);orig.delete(o)}})}
function select(ln,fly,tag){if(selected)hl(selected,false);selected=null;const box=document.getElementById('info');
  if(tag&&!ln){box.innerHTML=`<h2>${tag}</h2><table><tr><td>Equipment</td><td>see CFU-000-PL-3DM-001</td></tr></table>`;box.style.display='block';return}
  if(!ln||!META[ln]){box.style.display='none';return}selected=ln;hl(ln,true);const m=META[ln];
  box.innerHTML=`<h2>${ln}</h2><table><tr><td>Service</td><td>${m.service}</td></tr><tr><td>From / to</td><td>${m.from} &rarr; ${m.to}</td></tr>
  <tr><td>Class</td><td>${m.cls} (${m.rating}#, ${m.mat})</td></tr><tr><td>Schedule</td><td>${m.sch}</td></tr><tr><td>Design</td><td>${m.P} barg / ${m.T} &deg;C</td></tr>
  <tr><td>Test (hydro)</td><td>${m.PT} barg</td></tr><tr><td>Routed</td><td>${m.length} m &middot; ${m.level}</td></tr><tr><td>Supports</td><td>${m.supports}</td></tr>
  ${m.iso?`<tr><td>Isometric</td><td>${m.iso}</td></tr>`:''}${m.stress?`<tr><td>Stress</td><td>${m.stress}</td></tr>`:''}</table>`;box.style.display='block';
  if(fly&&m.c){const c=W(m.c[0],m.c[1],m.c[2]);const d=Math.max(30,m.span*1.2);controls.target.copy(c);camera.position.set(c.x-d*0.6,c.y+d*0.6,c.z+d*0.8);controls.update()}}
const sb=document.getElementById('search');
sb.addEventListener('change',()=>{const v=sb.value.trim().toUpperCase();const k=Object.keys(META);const t=k.find(x=>x.toUpperCase()===v)||k.find(x=>x.toUpperCase().includes(v));if(t)select(t,true)});
sb.addEventListener('keydown',e=>{if(e.key==='Enter')sb.dispatchEvent(new Event('change'))});
const tEq=document.getElementById('tEq'),tPi=document.getElementById('tPi'),tGh=document.getElementById('tGh'),tCr=document.getElementById('tCr');
tEq.onchange=()=>{if(eqRoot)eqRoot.visible=tEq.checked};tPi.onchange=()=>{if(piRoot)piRoot.visible=tPi.checked};
tGh.onchange=()=>{eqMeshes.forEach(o=>{if(!o.material)return;o.material.transparent=tGh.checked;o.material.opacity=tGh.checked?0.18:1;o.material.depthWrite=!tGh.checked})};
tCr.onchange=()=>{pipes.forEach(o=>{const m=META[o.userData.line];o.visible=!tCr.checked||(m&&m.iso)})};
document.getElementById('bIso').onclick=()=>view('iso');document.getElementById('bTop').onclick=()=>view('top');document.getElementById('bS').onclick=()=>view('s');
document.getElementById('bReset').onclick=()=>{select(null);sb.value=''};
window.__select=select;window.__toggle=(eq,pi)=>{tEq.checked=eq;tPi.checked=pi;tEq.onchange();tPi.onchange()};window.__ghost=(g)=>{tGh.checked=g;tGh.onchange()};
(function loop(){requestAnimationFrame(loop);controls.update();renderer.render(scene,camera)})();
</script></body></html>
"""
