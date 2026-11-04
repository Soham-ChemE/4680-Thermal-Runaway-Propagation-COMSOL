/* Hero scene for the 4680 page: the 20-cell 5s4p pack in 3D with the cascade played from the reduced-order surrogate's
   per-cell traces (window.TR4680.lumped.traces), a conductivity slider, a cooling toggle, and a scroll-scrubbed camera.
   The traces are the SURROGATE's, labelled as such in the page; the COMSOL outcome for the selected matrix cell is shown beside them. */
import { THREE, createStage, cameraPath } from './three-kit.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const D = window.TR4680, S = window.SITE, reduced = S.reduced, phone = S.phone;
const M = D.matrix.model, L = D.lumped; const NX = 5, NY = 4, PITCH = .48, R = .23, H = .8; // 1 unit = 100 mm

(function () {
  const canvas = document.getElementById('heroCanvas'); if (!canvas) return;
  const st = createStage(canvas, { fov: 38, bloom: { strength: .28, radius: .4, threshold: .9 }, dof: { aperture: .0004, maxblur: .003 }, exposure: .9, envIntensity: .45 });
  if (st.failed) return;
  const { scene, camera } = st;
  const ctr = new OrbitControls(camera, canvas); ctr.enableDamping = true; ctr.dampingFactor = .08; ctr.enableZoom = false; ctr.enablePan = false; ctr.maxPolarAngle = Math.PI / 2 - .05; ctr.autoRotate = !reduced; ctr.autoRotateSpeed = .35;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x1b2436, .8)); const dl = new THREE.DirectionalLight(0xffffff, 1.4); dl.position.set(4, 6, 3); scene.add(dl);
  const pack = new THREE.Group(); scene.add(pack);
  const cx = (NX - 1) * PITCH / 2, cz = (NY - 1) * PITCH / 2;
  const cylGeo = new THREE.CylinderGeometry(R, R, H, phone ? 28 : 48, 1, false); const capGeo = new THREE.CylinderGeometry(.075, .075, .03, 24);
  const cool = new THREE.Color('#5b7fb5'), warm = new THREE.Color('#f59e0b'), hot = new THREE.Color('#f97316'), white = new THREE.Color('#fde68a');
  const cells = [];
  for (let iy = 0; iy < NY; iy++) for (let ix = 0; ix < NX; ix++) {
    const mat = new THREE.MeshStandardMaterial({ color: cool.clone(), roughness: .32, metalness: .55, emissive: 0xff7a1a, emissiveIntensity: 0 });
    const m = new THREE.Mesh(cylGeo, mat); m.position.set(ix * PITCH - cx, 0, iy * PITCH - cz); pack.add(m);
    const cap = new THREE.Mesh(capGeo, new THREE.MeshStandardMaterial({ color: 0xb8c2cc, roughness: .3, metalness: .9 })); cap.position.set(m.position.x, H / 2 + .015, m.position.z); pack.add(cap);
    cells.push({ mesh: m, mat, id: iy * NX + ix });
  }
  // acrylic holder frames: lattice of bars at the top and bottom, translucent
  const acr = new THREE.MeshStandardMaterial({ color: 0xcfe3ff, roughness: .25, metalness: .05, transparent: true, opacity: .5 });
  for (const y of [H / 2 - .04, -H / 2 + .04]) {
    for (let ix = 0; ix <= NX; ix++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.03, .06, NY * PITCH), acr); b.position.set(ix * PITCH - cx - PITCH / 2, y, 0); pack.add(b); }
    for (let iy = 0; iy <= NY; iy++) { const b = new THREE.Mesh(new THREE.BoxGeometry(NX * PITCH, .06, .03), acr); b.position.set(0, y, iy * PITCH - cz - PITCH / 2); pack.add(b); }
  }
  // steel connectors: series strips along x on top, parallel strips across z midway between cylinders
  const steel = new THREE.MeshStandardMaterial({ color: 0x9aa4b1, roughness: .35, metalness: .95 });
  for (let iy = 0; iy < NY; iy++) for (let ix = 0; ix < NX - 1; ix++) { const s = new THREE.Mesh(new THREE.BoxGeometry(PITCH, .012, .07), steel); s.position.set(ix * PITCH - cx + PITCH / 2, H / 2 + .036, iy * PITCH - cz); pack.add(s); }
  for (let iy = 0; iy < NY - 1; iy++) for (let ix = 0; ix < NX; ix++) { const s = new THREE.Mesh(new THREE.BoxGeometry(.05, .012, PITCH), steel); s.position.set(ix * PITCH - cx, H / 2 + .03, iy * PITCH - cz + PITCH / 2); pack.add(s); }
  // cooled base plate and the wrapped air compartment
  const plateMat = new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: .5, metalness: .4, emissive: 0x3b82f6, emissiveIntensity: .25 });
  const plate = new THREE.Mesh(new THREE.BoxGeometry(NX * PITCH + .3, .06, NY * PITCH + .3), plateMat); plate.position.y = -H / 2 - .09; pack.add(plate);
  const wrap = new THREE.Mesh(new THREE.BoxGeometry(NX * PITCH + .12, H + .2, NY * PITCH + .12), new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: .05, roughness: .1, side: THREE.DoubleSide, depthWrite: false })); pack.add(wrap);
  const grid = new THREE.GridHelper(10, 20, 0x1f2a3c, 0x1f2a3c); grid.position.y = -H / 2 - .13; grid.material.transparent = true; grid.material.opacity = .35; scene.add(grid);
  st.onTheme = dark => { grid.material.color.set(dark ? 0x1f2a3c : 0xcbd5e1); st.dirty = true; };
  st.onTheme(S.isDark());

  // ---------- state: which surrogate trace plays, and the simulated clock ----------
  const kVals = L.k_values; const state = { h: 2000, kIdx: kVals.indexOf(1.0), tMin: 0, playing: !reduced, speed: 2.5 /* simulated minutes per real second */ };
  const traceKey = () => `h${state.h}_k${+kVals[state.kIdx]}`;
  const trace = () => L.traces[traceKey()];
  const clockEl = document.getElementById('heroClock'), outEl = document.getElementById('heroOutcome'), kEl = document.getElementById('kVal'), slider = document.getElementById('kSlider'), comsolEl = document.getElementById('heroComsol'), countEl = document.getElementById('heroCount');
  function comsolCell() { const r = D.matrix.runs.find(x => x.h_plate === state.h && x.k_tl === kVals[state.kIdx]); if (!r) return 'not in the COMSOL matrix'; if (r.status === 'inferred') return 'COMSOL: inferred cascade (not run)'; return r.outcome === 'cascade' ? `COMSOL: cascade, 2nd ignition ${r.second_ignition_min} min` : 'COMSOL: arrested at cell 1'; }
  function describe() {
    const tr = trace(), n = tr.ignition_min.filter(v => v !== null).length;
    kEl.textContent = (+kVals[state.kIdx]).toFixed(2); outEl.textContent = n > 1 ? `Surrogate: cascade, ${n} of 20 cells` : 'Surrogate: arrested at cell 1'; outEl.className = 'pill ' + (n > 1 ? 'bad' : 'good'); comsolEl.textContent = comsolCell();
    document.dispatchEvent(new CustomEvent('tr-state', { detail: { ...state, key: traceKey() } }));
  }
  if (slider) { slider.max = kVals.length - 1; slider.value = state.kIdx; slider.addEventListener('input', () => { state.kIdx = +slider.value; state.tMin = 0; describe(); }); }
  document.querySelectorAll('[data-h]').forEach(b => b.addEventListener('click', () => { document.querySelectorAll('[data-h]').forEach(x => x.classList.toggle('on', x === b)); state.h = +b.dataset.h; state.tMin = 0; plateMat.emissiveIntensity = state.h > 0 ? .25 : 0; plateMat.color.set(state.h > 0 ? 0x3b82f6 : 0x475569); describe(); }));
  const playBtn = document.getElementById('playBtn'); if (playBtn) playBtn.addEventListener('click', () => { state.playing = !state.playing; playBtn.textContent = state.playing ? 'Pause' : 'Play'; });
  describe();
  function tempAt(cell, tMin) { const tr = trace(), t = tr.t_min; let i = Math.min(t.length - 1, Math.max(0, Math.floor(tMin / (t[1] - t[0])))); const j = Math.min(t.length - 1, i + 1), f = Math.min(1, Math.max(0, (tMin - t[i]) / ((t[j] - t[i]) || 1))); return tr.cell_max_C[i][cell] * (1 - f) + tr.cell_max_C[j][cell] * f; }
  const tmp = new THREE.Color();
  function paint() {
    const tr = trace(); let n = 0;
    for (const c of cells) {
      const T = tempAt(c.id, state.tMin), ign = tr.ignition_min[c.id]; const u = Math.min(1, Math.max(0, (T - 30) / 330));
      tmp.copy(cool).lerp(warm, Math.min(1, u * 2.2)); if (u > .45) tmp.lerp(hot, Math.min(1, (u - .45) / .3)); if (u > .85) tmp.lerp(white, .5 * (u - .85) / .15);
      c.mat.color.copy(tmp); let e = u * .45;
      if (ign !== null && state.tMin >= ign) { n++; e += 1.0 * Math.exp(-(state.tMin - ign) / 1.2); }
      c.mat.emissiveIntensity = e;
    }
    if (clockEl) clockEl.textContent = `${Math.floor(state.tMin)} min`; if (countEl) countEl.textContent = `${n} / 20 ignited`;
  }
  // ---------- camera ----------
  pack.position.x = (st.wide !== false) ? 1.0 : 0; // keep the pack right of the headline on wide screens
  const pathWide = cameraPath([[4.4, 2.9, 4.6], [-2.6, 1.3, 3.4], [-1.6, 2.9, -2.6]], [[1.0, 0, 0], [1.0, -.1, 0], [1.0 - cx, .2, -cz]]);
  const pathNarrow = cameraPath([[3.9, 3.6, 5.4], [-3.4, 1.6, 3.8], [-2.6, 3.2, -3.0]], [[0, .3, 0], [0, 0, 0], [-cx, .3, -cz]]);
  const pos = new THREE.Vector3(), tgt = new THREE.Vector3(); let dragging = false, lastT = -1, lastClock = -1;
  // start the camera on the path instead of flying in from the origin
  (st.wide !== false ? pathWide : pathNarrow).at(reduced ? 1 : 0, pos, tgt); camera.position.copy(pos); ctr.target.copy(tgt); ctr.update();
  canvas.addEventListener('pointerdown', () => dragging = true); addEventListener('pointerup', () => setTimeout(() => dragging = false, 2500)); ctr.addEventListener('change', () => st.dirty = true);
  st.loop((t, dt) => {
    const T = S.hero.t; let changed = false;
    if (state.playing && !reduced) { state.tMin += (dt / 1000) * state.speed; if (state.tMin > 60) state.tMin = 0; changed = true; }
    else if (reduced) state.tMin = 60;
    if (Math.abs(state.tMin - lastClock) > .02) { paint(); lastClock = state.tMin; changed = true; }
    (st.wide !== false ? pathWide : pathNarrow).at(reduced ? 1 : T, pos, tgt);
    if (!dragging && camera.position.distanceToSquared(pos) > 1e-6) { camera.position.lerp(pos, reduced ? 1 : .1); changed = true; }
    ctr.target.lerp(tgt, .1); ctr.autoRotate = !reduced && T < .2 && !dragging; if (ctr.autoRotate || dragging) changed = true; ctr.update();
    if (st.bloom) st.bloom.strength = .22 + .2 * S.hero.glow; if (st.bokeh) st.bokeh.uniforms.focus.value = camera.position.distanceTo(ctr.target);
    if (Math.abs(T - lastT) > 1e-4) { lastT = T; changed = true; }
    return changed;
  });
})();
