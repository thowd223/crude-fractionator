/* CDU LIVE - Field 3D: the project's plant model (CFU-000-PL-3DM-001) driven by the live simulator. */
(function () {
  "use strict";
  const view = document.getElementById("v-field");
  const canvas = document.getElementById("field-canvas");
  const labelsEl = document.getElementById("field-labels");
  const msg = document.getElementById("field-msg");
  const L = window.PLANT.layout;
  const W = (x, y, z) => new THREE.Vector3(x, z - 100, -y);
  let started = false, ready = false, renderer, scene, camera, controls, clock;
  const byTag = {}, pickables = [], heaters = {}, smoke = [];
  const labels = [];
  let onPick = () => {};
  let fly = null;

  // equipment tag -> console id
  const TAG2ID = (t) => {
    if (/^H-101|^E-120|^K-10/.test(t)) return "h101";
    if (/^H-201/.test(t)) return "h201";
    if (/^C-101/.test(t)) return "c101";
    if (/^C-10[234]/.test(t)) return "strippers";
    if (/^C-10[56]|^D-10[56]|^E-11[4-7]|^A-10[678]/.test(t)) return "lightends";
    if (/^D-101|^E-118|^X-10[12]|^P-114|^P-118/.test(t)) return "desalter";
    if (/^E-1(0\d|1[0-3])|^E-201$/.test(t)) return "preheat";
    if (/^C-201/.test(t)) return "c201";
    if (/^J-20|^E-20[234]|^D-20[12]/.test(t)) return "ejectors";
    if (/^A-101|^D-102|^E-115|^X-103|^P-10[345]/.test(t)) return "overhead";
    if (/^A-10[345]|^A-20/.test(t)) return "products";
    if (/^P-101|^P-102/.test(t)) return "tanks";
    return null;
  };

  function loadScript(src) { return new Promise((res, rej) => { const s = document.createElement("script"); s.src = src; s.onload = res; s.onerror = () => rej(new Error("could not load " + src)); document.head.appendChild(s); }); }

  async function start() {
    if (started) return; started = true;
    if (!window.THREE || !THREE.GLTFLoader) { msg.textContent = "3D libraries did not load. The console and all other views still work."; return; }
    try { if (!window.PLANT_GLB_B64) await loadScript("data/plant-model.js"); } catch (e) { msg.textContent = "Plant model file missing (data/plant-model.js)."; return; }
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 0.95;
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a1216);
    scene.fog = new THREE.Fog(0x0a1216, 260, 620);
    camera = new THREE.PerspectiveCamera(42, 1, 0.5, 2000);
    controls = new THREE.OrbitControls(camera, canvas);
    controls.enableDamping = true; controls.dampingFactor = 0.1; controls.maxPolarAngle = Math.PI * 0.49; controls.autoRotateSpeed = 0.35;
    scene.add(new THREE.HemisphereLight(0x9fb7c9, 0x20262a, 0.75));
    const moon = new THREE.DirectionalLight(0xc8d6ff, 0.55); moon.position.set(-160, 240, 120); scene.add(moon);
    const fill = new THREE.DirectionalLight(0xffc98a, 0.25); fill.position.set(200, 60, -150); scene.add(fill);
    clock = new THREE.Clock();
    // sodium lights along the rack
    for (const x of [30, 90, 150, 200]) { const l = new THREE.PointLight(0xffb15c, 0.7, 70, 2); l.position.copy(W(x, 75, 118)); scene.add(l); }
    const buf = Uint8Array.from(atob(window.PLANT_GLB_B64), (c) => c.charCodeAt(0)).buffer;
    new THREE.GLTFLoader().parse(buf, "", (g) => {
      scene.add(g.scene);
      g.scene.traverse((o) => {
        if (!o.isMesh) return;
        const tag = o.name.split("__")[0];
        o.userData.tag = tag;
        o.material = o.material.clone(); o.material.side = THREE.DoubleSide;
        if (o.material.emissive === undefined) o.material = new THREE.MeshStandardMaterial({ color: o.material.color || 0x888888 });
        if (/^ground/.test(tag)) o.material.color.set(0x1c2429);
        else if (/^RD-/.test(tag)) o.material.color.set(0x2c353a);
        else o.material.color.multiplyScalar(0.8);
        o.userData.baseEm = o.material.emissive.clone();
        (byTag[tag] = byTag[tag] || []).push(o);
        if (!/^RD-|^ground/.test(tag)) pickables.push(o);
      });
      for (const t of ["H-101", "H-201"]) {
        const m = L[t]; if (!m) continue;
        const light = new THREE.PointLight(0xff7a2a, 0, t === "H-101" ? 90 : 60, 2);
        light.position.copy(W(m.x, m.y - (t === "H-101" ? 14 : 8), 108)); scene.add(light);
        heaters[t] = { light, m };
        // stack smoke
        const tex = smokeTexture();
        for (let i = 0; i < 26; i++) {
          const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, opacity: 0 }));
          sp.userData = { t: Math.random(), heater: t, base: W(m.x, m.y, m.top + 1) };
          scene.add(sp); smoke.push(sp);
        }
      }
      buildLabels();
      msg.remove(); ready = true; camTo("overview", true); resize();
    }, (e) => { msg.textContent = "Plant model failed to load: " + e; });
    canvas.addEventListener("pointerdown", (e) => { canvas._down = [e.clientX, e.clientY]; controls.autoRotate = false; setOrbit(false); });
    canvas.addEventListener("pointerup", (e) => { const d = canvas._down; if (d && Math.hypot(e.clientX - d[0], e.clientY - d[1]) < 5) pick(e); });
    addEventListener("resize", resize);
    loop();
  }
  function smokeTexture() {
    const c = document.createElement("canvas"); c.width = c.height = 64; const g = c.getContext("2d");
    const r = g.createRadialGradient(32, 32, 2, 32, 32, 32); r.addColorStop(0, "rgba(200,205,210,.55)"); r.addColorStop(1, "rgba(200,205,210,0)");
    g.fillStyle = r; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c);
  }
  function resize() { if (!renderer) return; const w = view.clientWidth, h = view.clientHeight; if (!w || !h) return; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }

  const LBL = [
    { tag: "H-101", key: "h101" }, { tag: "C-101", key: "c101" }, { tag: "D-101A", key: "desalter" }, { tag: "C-201", key: "c201" },
    { tag: "H-201", key: "h201" }, { tag: "A-101-B2", key: "overhead" }, { tag: "J-201", key: "ejectors" }, { tag: "C-106", key: "lightends" }, { tag: "E-108B", key: "preheat" },
  ];
  function buildLabels() {
    for (const l of LBL) {
      const m = L[l.tag]; if (!m) continue;
      const d = document.createElement("div"); d.className = "flabel"; labelsEl.appendChild(d);
      d.addEventListener("click", () => onPick(l.key));
      labels.push({ ...l, d, p: W(m.x, m.y, m.top + 3) });
    }
  }
  let labelText = () => ({ lines: [] });
  function updLabels(sim) {
    const w = view.clientWidth, h = view.clientHeight;
    for (const l of labels) {
      const v = l.p.clone().project(camera);
      const vis = v.z < 1 && Math.abs(v.x) < 1.1 && Math.abs(v.y) < 1.1;
      l.d.hidden = !vis;
      if (!vis) continue;
      l.d.style.left = ((v.x + 1) / 2 * w).toFixed(0) + "px"; l.d.style.top = ((1 - v.y) / 2 * h).toFixed(0) + "px";
      const t = labelText(l.key, sim);
      const html = `<b>${l.tag.replace("-B2", "")} ${t.title || ""}</b>${t.lines.join("<br>")}`;
      if (l.d._h !== html) { l.d.innerHTML = html; l.d._h = html; }
      l.d.className = "flabel" + (t.alarm ? " alarm" : t.hot ? " hot" : "");
    }
  }

  const CAMS = {
    overview: { pos: [-60, 150, 125], t: [115, 75, 108] },
    "H-101": { tag: "H-101", d: 70 }, "C-101": { tag: "C-101", d: 85 }, "D-101A": { tag: "D-101A", d: 75 }, "C-201": { tag: "C-201", d: 90 },
  };
  function camTo(key, instant) {
    if (!camera) return;
    let pos, tgt;
    const c = CAMS[key] || { tag: key, d: 60 };
    if (c.tag) {
      const m = L[c.tag]; if (!m) return;
      tgt = W(m.x, m.y, (m.z + m.top) / 2);
      pos = tgt.clone().add(new THREE.Vector3(-c.d * 0.75, c.d * 0.55, c.d * 0.75));
    } else { tgt = W(...c.t); pos = new THREE.Vector3(...c.pos); }
    if (instant) { camera.position.copy(pos); controls.target.copy(tgt); controls.update(); return; }
    fly = { p0: camera.position.clone(), t0: controls.target.clone(), p1: pos, t1: tgt, k: 0 };
  }
  function focusId(id) {
    const map = { h101: "H-101", c101: "C-101", desalter: "D-101A", c201: "C-201", h201: "H-201", overhead: "D-102", ejectors: "J-201", lightends: "C-105", strippers: "C-103", preheat: "E-108B", hottrain: "E-108B", tanks: "P-101A", pa: "C-101", products: "A-104" };
    if (map[id]) camTo(map[id]);
  }
  function pick(e) {
    const r = canvas.getBoundingClientRect();
    const mouse = new THREE.Vector2((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1);
    const ray = new THREE.Raycaster(); ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(pickables, false)[0];
    if (!hit) return;
    const id = TAG2ID(hit.object.userData.tag);
    if (id) onPick(id, hit.object.userData.tag);
  }

  let alarmTags = new Set(), simRef = null;
  function setOrbit(on) { controls.autoRotate = on; const b = document.getElementById("orbitBtn"); if (b) b.setAttribute("aria-pressed", on ? "true" : "false"); }
  function loop() {
    requestAnimationFrame(loop);
    if (!ready || view.hidden) return;
    const dt = Math.min(0.05, clock.getDelta()), t = clock.elapsedTime;
    if (fly) { fly.k = Math.min(1, fly.k + dt * 0.9); const e = fly.k < 0.5 ? 2 * fly.k * fly.k : 1 - Math.pow(-2 * fly.k + 2, 2) / 2; camera.position.lerpVectors(fly.p0, fly.p1, e); controls.target.lerpVectors(fly.t0, fly.t1, e); if (fly.k >= 1) fly = null; }
    controls.update();
    const s = simRef;
    if (s) {
      // heater glow
      for (const [tag, hh] of Object.entries(heaters)) {
        const r = tag === "H-101" ? (s.ev.h1trip ? 0 : s.act.fired1 / 78) : (s.ev.h2trip ? 0 : s.act.fired2 / 20.6);
        const flick = 0.85 + 0.15 * Math.sin(t * 13 + (tag === "H-101" ? 0 : 2)) * (0.6 + 0.4 * Math.random());
        hh.light.intensity = 3.2 * r * flick;
        for (const o of byTag[tag] || []) o.material.emissive.setRGB(0.55 * r * flick, 0.16 * r * flick, 0.03 * r);
        hh.r = r;
      }
      for (const sp of smoke) {
        const hh = heaters[sp.userData.heater]; if (!hh) continue;
        sp.userData.t += dt * 0.12; if (sp.userData.t > 1) sp.userData.t -= 1;
        const k = sp.userData.t;
        sp.position.copy(sp.userData.base).add(new THREE.Vector3(Math.sin(k * 6 + sp.id) * 2 + k * 18, k * 45, -k * 10));
        const sc = 3 + k * 16; sp.scale.set(sc, sc, 1);
        sp.material.opacity = (1 - k) * 0.22 * (0.25 + hh.r);
      }
      // equipment in alarm pulses red; columns carry a faint heat tint
      const pulse = 0.5 + 0.5 * Math.sin(performance.now() / 180);
      for (const [tag, list] of Object.entries(byTag)) {
        if (tag === "H-101" || tag === "H-201") continue;
        const al = alarmTags.has(tag);
        for (const o of list) {
          if (al) o.material.emissive.setRGB(0.6 * pulse, 0.05, 0.03);
          else if (tag === "C-101") { const c = new THREE.Color(window.Mimic.tcol(s.out.profile[30])); o.material.emissive.copy(c).multiplyScalar(0.12); }
          else o.material.emissive.copy(o.userData.baseEm);
        }
      }
      updLabels(s);
    }
    renderer.render(scene, camera);
  }

  window.Field = {
    start, resize, camTo, focusId,
    setSim(s) { simRef = s; },
    setAlarmTags(set) { alarmTags = set; },
    onPick(fn) { onPick = fn; },
    setLabelText(fn) { labelText = fn; },
    orbit() { if (!controls) return; setOrbit(!controls.autoRotate); },
  };
})();
