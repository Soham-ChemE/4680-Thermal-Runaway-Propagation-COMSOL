/* Body scenes for the 4680 page, all drawn by the shared Viz renderer (assets/viz.js) from window.TR4680 (assets/data.js):
   1. the pack as an exploded assembly (base plate, holder frames, 20 cells, busbars, wrap) that assembles on scroll;
   2. the COMSOL run matrix as a 3D tile field, driven by the sticky steps;
   3. adiabatic peak temperature against runaway energy as a ribbon, with the 110 kJ point;
   4. diffusion-time and Biot-number bar fields;
   5. the mechanism: a burning cell, the air gap and the neighbour whose facing skin crosses 80 °C first;
   6. the surrogate's twenty per-cell temperature traces as ribbons, cascade or arrested;
   7. the surrogate sweep as a tile field. */
import { Viz } from './viz.js';
import { THREE } from './three-kit.js';
const D = window.TR4680, M = D.matrix.model, sc = D.scaling, L = D.lumped;
const f = (v, d = 0) => (+v).toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: d });
const NX = 5, NY = 4, PITCH = .48, R = .23, H = .8;

/* ---------- 1. exploded pack ---------- */
Viz.view('[data-viz="pack"]', v => {
  const cx = (NX - 1) * PITCH / 2, cz = (NY - 1) * PITCH / 2, parts = [];
  const plate = new THREE.Mesh(new THREE.BoxGeometry(NX * PITCH + .3, .06, NY * PITCH + .3), Viz.mat('blue', { roughness: .5, metalness: .4, emissive: 'blue', emissiveIntensity: .2 })); plate.position.y = -H / 2 - .09; parts.push({ mesh: plate, from: [0, -1.2, 0], delay: 0, span: .3 });
  const cellGeo = new THREE.CylinderGeometry(R, R, H, 40, 1), capGeo = new THREE.CylinderGeometry(.075, .075, .03, 20);
  const cells = new THREE.Group(); v.rig.add(cells);
  for (let iy = 0; iy < NY; iy++) for (let ix = 0; ix < NX; ix++) { const c = new THREE.Mesh(cellGeo, Viz.mat('cool', { roughness: .32, metalness: .55 })); c.position.set(ix * PITCH - cx, 0, iy * PITCH - cz); const cap = new THREE.Mesh(capGeo, Viz.mat('steel', { roughness: .3, metalness: .9 })); cap.position.y = H / 2 + .015; c.add(cap); cells.add(c); parts.push({ mesh: c, from: [0, 1.6 + (ix + iy) * .08, 0], delay: .18 + (ix + iy) * .03, span: .35 }); }
  const acr = () => Viz.mat('acrylic', { roughness: .25, metalness: .05, opacity: .55 });
  for (const [y, k] of [[-H / 2 + .04, 0], [H / 2 - .04, 1]]) { const fr = new THREE.Group(); for (let ix = 0; ix <= NX; ix++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.03, .06, NY * PITCH), acr()); b.position.set(ix * PITCH - cx - PITCH / 2, 0, 0); fr.add(b); } for (let iy = 0; iy <= NY; iy++) { const b = new THREE.Mesh(new THREE.BoxGeometry(NX * PITCH, .06, .03), acr()); b.position.set(0, 0, iy * PITCH - cz - PITCH / 2); fr.add(b); } fr.position.y = y; parts.push({ mesh: fr, from: [0, k ? 2.2 : -.9, 0], delay: k ? .5 : .08, span: .3, fade: false }); }
  const bus = new THREE.Group(); const steel = () => Viz.mat('steel', { roughness: .35, metalness: .95 });
  for (let iy = 0; iy < NY; iy++) for (let ix = 0; ix < NX - 1; ix++) { const s = new THREE.Mesh(new THREE.BoxGeometry(PITCH, .012, .07), steel()); s.position.set(ix * PITCH - cx + PITCH / 2, H / 2 + .036, iy * PITCH - cz); bus.add(s); }
  for (let iy = 0; iy < NY - 1; iy++) for (let ix = 0; ix < NX; ix++) { const s = new THREE.Mesh(new THREE.BoxGeometry(.05, .012, PITCH), steel()); s.position.set(ix * PITCH - cx, H / 2 + .03, iy * PITCH - cz + PITCH / 2); bus.add(s); }
  parts.push({ mesh: bus, from: [0, 2.6, 0], delay: .62, span: .3, fade: false });
  const wrap = new THREE.Mesh(new THREE.BoxGeometry(NX * PITCH + .12, H + .2, NY * PITCH + .12), Viz.mat('white', { opacity: .07, roughness: .1, side: THREE.DoubleSide, depthWrite: false })); parts.push({ mesh: wrap, from: [0, 0, 0], delay: .8, span: .2 });
  const ex = Viz.exploded(v, parts);
  const labels = [['Cooled base plate\nh_plate 100 to 2,000 W/m²·K', [0, -H / 2 - .32, cz + .55], .02], ['Acrylic holder frames, k ≈ 0.19 W/m·K', [-cx - .2, H / 2 + .25, -cz - .3], .5], ['Steel AISI 4340 busbars', [cx + .4, H / 2 + .35, 0], .62], ['20 × 46 × 80 mm cells, 2 mm gaps', [0, .15, cz + .75], .25]];
  const sprites = labels.map(([t, p, d]) => { const s = Viz.label(v, t, p, { px: 22, scale: .112 }); s.userData.delay = d; return s; });
  v.update = vv => { ex.draw(vv.p); sprites.forEach(s => { s.material.opacity = Math.min(1, Math.max(0, (vv.p - s.userData.delay - .15) / .2)); }); return false; };
  v.spin = .12; v.tilt = .1;
}, { camera: [3.6, 2.4, 4.4], target: [0, -.1, 0], fov: 34 });

/* ---------- 2. COMSOL run matrix as a tile field ---------- */
const matrixView = Viz.view('[data-viz="matrix"]', v => {
  const hs = D.matrix.h_plate_values_W_m2K, ks = D.matrix.k_tl_values_W_mK, runs = D.matrix.runs; const cells = [];
  const X = j => (j - (ks.length - 1) / 2) * 1.05, Zc = i => (i - (hs.length - 1) / 2) * 1.05;
  hs.forEach((h, i) => ks.forEach((k, j) => { const r = runs.find(x => x.h_plate === h && x.k_tl === k); cells.push({ x: X(j), z: Zc(i), h, k, r, color: !r ? 'line' : r.status === 'inferred' ? 'violet' : r.outcome === 'cascade' ? 'hot' : 'cyan', scale: !r ? .25 : 1, delay: (i + j) / (hs.length + ks.length) }); }));
  const T = Viz.tiles(v, cells, { width: .92, depth: .92, height: .22 });
  ks.forEach((k, j) => Viz.label(v, `k = ${k}`, [X(j), .02, Zc(hs.length - 1) + .95], { px: 24, scale: .12, bg: false }));
  hs.forEach((h, i) => Viz.label(v, `h = ${f(h)}`, [X(-1) - .1, .02, Zc(i)], { px: 24, scale: .12, bg: false }));
  Viz.label(v, 'through-layer conductivity k_tl, W/m·K', [0, .02, Zc(hs.length - 1) + 1.5], { px: 22, scale: .12, bg: false, color: 'ink', weight: 700 });
  Viz.label(v, 'base cooling h, W/m²·K', [X(-1) - .2, .9, Zc(-1.4)], { px: 22, scale: .12, bg: false, color: 'ink', weight: 700 });
  // threshold line between the k = 1.0 and 1.25 columns
  const thr = Viz.line(v, [[X(.5), .26, Zc(-.6)], [X(.5), .26, Zc(hs.length - .4)]], 'ink'); thr.material.transparent = true;
  const tag = Viz.label(v, 'threshold 1.0 → 1.25', [X(.5), .5, Zc(hs.length - .2)], { px: 22, scale: .112, color: 'ink', weight: 700 });
  cells.forEach(c => { if (c.r) { const t = c.r.status === 'inferred' ? 'inferred' : c.r.outcome === 'cascade' ? `2nd @ ${c.r.second_ignition_min} min` : 'arrested'; const s = Viz.label(v, t, [c.x, .36, c.z], { px: 19, scale: .096, bg: false, color: c.r.status === 'inferred' ? 'ink' : 'white' }); c.label = s; } });
  v.highlight = null; const M4 = new THREE.Matrix4();
  v.update = vv => { T.draw(vv.p); thr.material.opacity = Math.max(0, vv.p * 1.5 - .6); tag.material.opacity = thr.material.opacity; const hl = vv.highlight; cells.forEach((c, i) => { if (!c.r) return; const on = hl ? hl(c) : true; const sY = on ? 1 : .35; const m = new THREE.Matrix4(); T.mesh.getMatrixAt(i, M4); const pos = new THREE.Vector3().setFromMatrixPosition(M4); m.makeScale(1, Math.max(1e-3, vv.p >= .999 ? sY : M4.elements[5]), 1); m.setPosition(pos); T.mesh.setMatrixAt(i, m); if (c.label) c.label.material.opacity = (on ? 1 : .3) * Math.min(1, Math.max(0, vv.p * 2 - 1)); }); T.mesh.instanceMatrix.needsUpdate = true; return false; };
  v.hover = hit => { const c = cells[hit.instanceId]; if (!c || !c.r) return `<b>h = ${f(c.h)} W/m²·K, k_tl = ${c.k} W/m·K</b>not run`; return `<b>h = ${f(c.h)} W/m²·K, k_tl = ${c.k} W/m·K</b>${c.r.status === 'inferred' ? 'cascade, inferred from the neighbouring runs' : c.r.outcome === 'cascade' ? `cascade, second ignition ${c.r.second_ignition_min} min` : 'arrested at cell 1'}`; };
  v.rot = -.22; v.tilt = .1;
}, { camera: [0, 7.6, 6.2], target: [0, -.3, .4], fov: 36, spin: 0 });
const PHASES = { p1: c => c.h === 2000 && c.k === 1.0, p2: c => c.h === 2000, p3: c => c.h === 500, p4: c => c.k === 1.25 && (c.h === 0 || c.h === 100) };
document.addEventListener('tr-phase', e => { if (matrixView) { matrixView.highlight = PHASES[e.detail] || null; matrixView.dirty = true; } });

/* ---------- 3. adiabatic peak against runaway energy ---------- */
Viz.view('[data-viz="energy"]', v => {
  const m = sc.cell_mass_kg, cp = M.cp_J_kgK, T0 = M.ambient_T_C; const xs = [], ys = []; for (let W = 20; W <= 200; W += 2) { xs.push(W); ys.push(T0 + W * 1e3 / (m * cp)); }
  const A = Viz.axes(v, { size: [4.2, 2.2, 1.2], x: { lo: 20, hi: 200, ticks: [50, 100, 150, 200], label: 'runaway energy per cell, kJ' }, y: { lo: 0, hi: 600, ticks: [0, 200, 400, 600], label: 'peak °C' }, z: { lo: 0, hi: 1 } });
  const rb = Viz.ribbon(v, A, xs, ys, { color: 'hot', width: .22, z: .5, name: 'uniform-cell peak', unit: '°C' });
  // the 280 to 340 °C band seen in the runs, and the 110 kJ point
  const band = new THREE.Mesh(new THREE.BoxGeometry(4.2, A.map(0, 340).y - A.map(0, 280).y, 1.2), Viz.mat('muted', { opacity: .16, depthWrite: false })); band.position.y = (A.map(0, 340).y + A.map(0, 280).y) / 2; v.rig.add(band);
  Viz.label(v, '280–340 °C peaks seen in the runs', [-.6, A.map(0, 340).y + .16, .62], { px: 20, scale: .104, bg: false, color: 'muted' });
  const pk = T0 + 110e3 / (m * cp), P = A.map(110, pk, .5); const dot = new THREE.Mesh(new THREE.SphereGeometry(.07, 16, 16), Viz.mat('ink', { emissive: 'ink', emissiveIntensity: .5 })); dot.position.copy(P); v.rig.add(dot);
  const post = Viz.line(v, [[P.x, A.map(0, 0).y, P.z], [P.x, P.y, P.z]], 'ink'); const lab = Viz.label(v, `110 kJ → ${f(pk)} °C`, [P.x + .55, P.y + .25, .6], { px: 24, scale: .12, color: 'ink', weight: 700 });
  v.update = vv => { rb.draw(vv.p); const on = vv.p > .9; dot.visible = on; post.visible = on; lab.visible = on; return false; };
  v.hover = hit => { const i = Viz.ribbonIndex(hit, A); return `<b>${xs[i]} kJ per cell</b>uniform-cell peak ${f(ys[i])} °C (ΔT = W / m·cₚ, m = ${f(m, 3)} kg, cₚ = ${f(cp)} J/kg·K)`; };
  v.rot = -.25; v.tilt = .1;
}, { camera: [0, 2.0, 7.0], target: [0, -.1, 0], fov: 32 });

/* ---------- 4. diffusion times and Biot numbers ---------- */
Viz.view('[data-viz="diffusion"]', v => {
  const taus = [['4680 radial\nR = 23 mm, k = 1', sc.tau_radial_4680_s / 60, 'hot'], ['2170 radial\nR = 10.5 mm, k = 1', sc.tau_radial_2170_s / 60, 'cyan'], ['4680 axial\nH/2 = 40 mm, k = 30', sc.tau_axial_4680_s / 60, 'violet']];
  const bi = [['h = 100', sc.biot[100], 'cool'], ['h = 500', sc.biot[500], 'blue'], ['h = 2,000', sc.biot[2000], 'green']];
  const A = Viz.axes(v, { size: [3.2, 2.2, 2.6], x: { lo: -.5, hi: 2.5, ticks: [] }, y: { lo: 0, hi: 50, ticks: [0, 10, 20, 30, 40, 50], label: 'minutes · Biot' }, z: { lo: -.5, hi: 1.5, ticks: [] } });
  const items = [...taus.map(([n, y, c], i) => ({ x: i, y, z: 0, color: c, name: n, unit: 'min', text: `${f(y * 60)} s ≈ ${f(y, 1)} min` })), ...bi.map(([n, y, c], i) => ({ x: i, y, z: 1, color: c, name: n, unit: '', text: `Bi = ${f(y, 1)}` }))];
  const B = Viz.bars(v, A, items, { width: .5, depth: .5 });
  items.forEach(it => { const p = A.map(it.x, it.y, it.z); it.lab = Viz.label(v, it.text, [p.x, p.y + .22, p.z], { px: 20, scale: .096 }); it.name_ = Viz.label(v, it.name, [p.x, A.map(0, 0).y - .25, p.z + .28], { px: 18, scale: .088, bg: false }); });
  Viz.label(v, 'diffusion time L² / α', [-2.2, .7, A.map(0, 0, 0).z], { px: 22, scale: .112, color: 'ink', weight: 700 });
  Viz.label(v, 'Biot number h·L / k, L = 23 mm', [-2.2, .7, A.map(0, 0, 1).z], { px: 22, scale: .112, color: 'ink', weight: 700 });
  v.update = vv => { B.draw(vv.p); items.forEach(it => it.lab.material.opacity = Math.max(0, vv.p * 2 - 1)); return false; };
  v.hover = hit => { const it = items[hit.instanceId]; return it ? `<b>${it.name.replace('\n', ', ')}</b>${it.text}` : null; };
  v.rot = -.42; v.tilt = .1;
}, { camera: [0, 2.6, 7.4], target: [0, -.2, 0], fov: 32 });

/* ---------- 5. mechanism: facing skin of the neighbour crosses 80 °C ---------- */
Viz.view('[data-viz="mechanism"]', v => {
  const geo = new THREE.CylinderGeometry(R * 2.2, R * 2.2, H * 2.2, 64, 1), burn = new THREE.Mesh(geo, Viz.mat('hot', { roughness: .3, metalness: .4, emissive: 'hot', emissiveIntensity: .9 })); burn.position.x = -.62;
  // neighbour: vertex colours paint its temperature field; the facing skin heats first
  const ng = geo.clone(); const cols = new Float32Array(ng.attributes.position.count * 3); ng.setAttribute('color', new THREE.BufferAttribute(cols, 3));
  const nb = new THREE.Mesh(ng, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .32, metalness: .45 })); nb.position.x = .62;
  const gap = new THREE.Mesh(new THREE.BoxGeometry(.18, H * 2.2, .3), Viz.mat('acrylic', { opacity: .4 })); gap.position.set(0, 0, -.55);
  const strip = new THREE.Mesh(new THREE.BoxGeometry(1.3, .025, .14), Viz.mat('steel', { metalness: .95, roughness: .3 })); strip.position.y = H * 1.1 + .03;
  const plate = new THREE.Mesh(new THREE.BoxGeometry(2.8, .08, 1.6), Viz.mat('blue', { emissive: 'blue', emissiveIntensity: .2 })); plate.position.y = -H * 1.1 - .14;
  const ex = Viz.exploded(v, [{ mesh: plate, from: [0, -1, 0], delay: 0, span: .25 }, { mesh: burn, from: [-1.5, 0, 0], delay: .1, span: .3 }, { mesh: nb, from: [1.5, 0, 0], delay: .1, span: .3, fade: false }, { mesh: gap, from: [0, 1.5, 0], delay: .35, span: .25 }, { mesh: strip, from: [0, 1.2, 0], delay: .45, span: .25 }]);
  const mark = new THREE.Mesh(new THREE.SphereGeometry(.06, 16, 16), Viz.mat('white', { emissive: 'yellow', emissiveIntensity: 1.2 })); mark.position.set(.62 - R * 2.2, .1, 0); v.rig.add(mark);
  const lab1 = Viz.label(v, 'maximum T sits on the facing skin:\ncrosses 80 °C → neighbour ignites', [.9, H * 1.1 + .55, .3], { px: 22, scale: .112 });
  const lab2 = Viz.label(v, 'higher k_tl spreads the heat inward\nand down to the cooled base', [.9, -H * 1.1 - .45, .5], { px: 22, scale: .112 });
  const lab3 = Viz.label(v, 'burning cell, 110 kJ', [-.62, H * 1.1 + .3, 0], { px: 22, scale: .112 });
  const air = Viz.label(v, '2 mm air gap, acrylic bridge, steel strip', [0, -H * 1.1 + .25, .9], { px: 20, scale: .1 });
  const cool = new THREE.Color(), hot = new THREE.Color(), tmp = new THREE.Color(); const pos = ng.attributes.position;
  const paint = (p) => { cool.set(v.pal.cool); hot.set(v.pal.hot); for (let i = 0; i < pos.count; i++) { const x = pos.getX(i), y = pos.getY(i); const d = (x + R * 2.2) / (R * 4.4); const heat = Math.max(0, p * 1.3 - .3) * Math.exp(-d * 3.2) * (1 - .25 * Math.abs(y) / (H * 1.1)); tmp.copy(cool).lerp(hot, Math.min(1, heat)); cols[i * 3] = tmp.r; cols[i * 3 + 1] = tmp.g; cols[i * 3 + 2] = tmp.b; } ng.attributes.color.needsUpdate = true; };
  v.onTheme = () => paint(v.p);
  let lastP = -1; v.update = (vv, t) => { ex.draw(vv.p); if (Math.abs(vv.p - lastP) > 1e-3) { paint(vv.p); lastP = vv.p; } const s = 1 + .25 * Math.sin(t * 3) * (vv.p > .9 ? 1 : 0); mark.scale.setScalar(s); [lab1, lab2, lab3, air].forEach((l, i) => l.material.opacity = Math.max(0, (vv.p - .6 - i * .08) * 4)); return vv.p > .9; };
  v.rot = .35; v.tilt = .12;
}, { camera: [0, 1.4, 5.6], target: [0, 0, 0], fov: 34 });

/* ---------- 6. surrogate traces as twenty ribbons ---------- */
Viz.view('[data-viz="traces"]', v => {
  const keys = { cascade: L.trace_cascade, arrest: L.trace_arrest }; const sets = {};
  const A = Viz.axes(v, { size: [4.4, 2.0, 2.6], x: { lo: 0, hi: 60, ticks: [0, 15, 30, 45, 60], label: 'time, min' }, y: { lo: 20, hi: 360, ticks: [100, 200, 300], label: '°C' }, z: { lo: -1, hi: 20, ticks: [1, 10, 20], label: 'cell' } });
  for (const [name, key] of Object.entries(keys)) { const tr = L.traces[key]; const xs = tr.t_min; const rbs = []; for (let c = 0; c < 20; c++) { const ys = tr.cell_max_C.map(row => row[c]); const rb = Viz.ribbon(v, A, xs, ys, { color: name === 'cascade' ? (tr.ignition_min[c] !== null ? 'hot' : 'warm') : (c === 0 ? 'hot' : 'cyan'), width: .07, z: c, name: `cell ${c + 1}`, skirtOpacity: .05 }); rb.mesh.userData.cell = c; rb.mesh.userData.ign = tr.ignition_min[c]; rbs.push(rb); } sets[name] = rbs; }
  const plane = new THREE.Mesh(new THREE.PlaneGeometry(4.4, 2.6), Viz.mat('ink', { opacity: .1, side: THREE.DoubleSide, depthWrite: false })); plane.rotation.x = -Math.PI / 2; plane.position.y = A.map(0, 80).y; v.rig.add(plane);
  Viz.label(v, '80 °C trigger', [-1.7, A.map(0, 80).y + .12, -1.25], { px: 20, scale: .104, bg: false, color: 'ink', weight: 700 });
  v.mode = 'cascade'; const setMode = m => { v.mode = m; for (const n in sets) sets[n].forEach(rb => { rb.mesh.visible = n === m; if (rb.skirt) rb.skirt.visible = n === m; }); v.dirty = true; };
  document.querySelectorAll('[data-trace]').forEach(b => b.addEventListener('click', () => { document.querySelectorAll('[data-trace]').forEach(x => x.classList.toggle('on', x === b)); setMode(b.dataset.trace); })); setMode('cascade');
  v.update = vv => { for (const n in sets) sets[n].forEach(rb => rb.draw(vv.p)); return false; };
  v.hover = hit => { const u = hit.object.userData; if (!u.xs) return null; const i = Viz.ribbonIndex(hit, A); return `<b>${u.series}, ${f(u.xs[i], 1)} min</b>maximum ${f(u.ys[i])} °C${u.ign !== null && u.ign !== undefined ? `; ignites at ${u.ign} min` : '; never ignites'}`; };
  v.rot = -.55; v.tilt = .14;
}, { camera: [0, 3.0, 8.6], target: [0, -.3, 0], fov: 32 });

/* ---------- 7. surrogate sweep as a tile field ---------- */
Viz.view('[data-viz="sweep"]', v => {
  const hs = L.h_values, ks = L.k_values; const cells = []; const X = j => (j - (ks.length - 1) / 2) * 1.02, Zc = i => (i - (hs.length - 1) / 2) * 1.02;
  hs.forEach((h, i) => ks.forEach((k, j) => { const r = L.sweep.find(x => x.h_plate === h && x.k_tl === k); cells.push({ x: X(j), z: Zc(i), h, k, r, color: r.cascade ? 'hot' : 'cyan', delay: (i + j) / (hs.length + ks.length) }); }));
  const T = Viz.tiles(v, cells, { width: .9, depth: .9, height: .2 });
  ks.forEach((k, j) => Viz.label(v, `${k}`, [X(j), .02, Zc(hs.length - 1) + .9], { px: 24, scale: .12, bg: false })); hs.forEach((h, i) => Viz.label(v, `h = ${f(h)}`, [X(-1) - .1, .02, Zc(i)], { px: 24, scale: .12, bg: false }));
  Viz.label(v, 'k_tl, W/m·K', [0, .02, Zc(hs.length - 1) + 1.45], { px: 22, scale: .12, bg: false, color: 'ink', weight: 700 });
  cells.forEach(c => { c.label = Viz.label(v, c.r.cascade ? `${c.r.n_ignited}/20` : 'arrested', [c.x, .34, c.z], { px: 19, scale: .096, bg: false, color: '#f8fafc' }); });
  v.update = vv => { T.draw(vv.p); cells.forEach(c => c.label.material.opacity = Math.max(0, vv.p * 2 - 1)); return false; };
  v.hover = hit => { const c = cells[hit.instanceId]; return c ? `<b>surrogate: h = ${f(c.h)}, k_tl = ${c.k}</b>${c.r.cascade ? `cascade, ${c.r.n_ignited} of 20 cells, second ignition ${c.r.second_ignition_min} min` : 'arrested at cell 1'}; neighbour peak ${c.r.neighbour_peak_C} °C` : null; };
  v.rot = -.35; v.tilt = .12;
}, { camera: [0, 6.6, 5.6], target: [0, -.3, .3], fov: 36 });
