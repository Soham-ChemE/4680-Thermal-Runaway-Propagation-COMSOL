"""Reduced-order lumped network surrogate of the 20-cell pack. BUILT HERE; NOT THE COMSOL MODEL.

Purpose: a transparent, fully inspectable thermal network that uses the same pulse (110 kJ, triangular, 1 s peak, 6 s end),
the same trigger (a cell ignites when its maximum temperature crosses 80 C; cell 1 is forced at 1 min), the same material
numbers (rho 2000, cp 1400, k_il 30, k_tl swept) and the same cooling idea (ambient 10 W/m2K at 30 C, a cooled base with
h_plate), to ask one question: does a threshold in through-layer conductivity also appear in a model simple enough to read
in one sitting? Everything below is an assumption stated in code; compare with docs/CLAIMS.md and the README caveats.

Discretisation (per cell, 2.5-D):
  * a central core node (r < r_core) plus radial shells, each split into NSEC azimuthal sectors, one axial layer;
  * radial conduction uses k_tl (through-layer), azimuthal conduction uses k_il (in-layer);
  * the base cooling acts on each node's footprint through a series resistance: half-height / k_il (axial, in-layer)
    + an acrylic floor layer R_FLOOR + 1/h_eff(h_plate, R_cap). This is why the surrogate also shows the R_cap null result.
  * the cells sit inside the wrapped air compartment of the base model, so they do not see ambient directly: every outer
    surface and top end exchanges heat with one shared air node through a still-air film (k_air over half the gap), and
    the air node loses heat to ambient (10 W/m2K, 30 C) over the pack's outer wrap area.
Inter-cell coupling between grid neighbours (5 x 4, pitch 48 mm):
  * still air between the two cylinders, as the conduction shape factor of two parallel cylinders in an infinite medium
    (S = 2 pi L / acosh((4D^2 - 2d^2)/(2 d^2)), k_air 0.026), split over the sectors that face the neighbour;
  * acrylic holder bridges (two frames) and steel connector strips as lumped conductances between the facing sectors.
Not included: electrical Joule heating before the event, radiation, convection in the air gap, venting, the plastic wrap,
the extra 100x resistance step after an event (no electrical model), any 3-D axial temperature structure.
"""
from __future__ import annotations
import math, json
from dataclasses import dataclass, field, asdict
import numpy as np
import scipy.sparse as sp

T_AMB = 30.0
@dataclass
class Params:
    d_cell: float = 0.046; h_cell: float = 0.080; gap: float = 0.002
    rho: float = 2000.0; cp: float = 1400.0; k_il: float = 30.0; k_tl: float = 1.0
    w_tr: float = 110e3; t_peak: float = 1.0; t_end: float = 6.0; t_force: float = 60.0; t_trigger_C: float = 80.0
    h_amb: float = 10.0; h_plate: float = 2000.0; r_cap: float = 1e-5; r_floor: float = 0.003 / 0.19  # 3 mm acrylic floor
    k_air: float = 0.026; k_acrylic: float = 0.19; k_steel: float = 44.0
    holder_area: float = 2 * 0.005 * 0.020   # two frames x 5 mm thick x 20 mm wide bridge between neighbours
    busbar_area: float = 2 * 0.0003 * 0.010  # two strips x 0.3 mm x 10 mm
    air_film: float = 0.010                  # still-air layer between a surface that faces open compartment air and the air node (the wrap clearance)
    coupling_scale: float = 1.0              # multiplier on the neighbour-to-neighbour conductance (air + holders + connectors); 1 = the estimates above
    wrap_clearance: float = 0.010            # air above/below the cells inside the wrap
    nx: int = 5; ny: int = 4
    shells: tuple = (0.008, 0.014, 0.018, 0.0205, 0.022, 0.023)  # outer radii; first entry is the core radius
    nsec: int = 16
    first_cell: int = 0                      # index of the forced cell (0 = corner); the COMSOL note does not say which cell is cell 1
    dt: float = 0.1; t_final: float = 3600.0

@dataclass
class Result:
    params: dict; t: np.ndarray; cell_max: np.ndarray; cell_mean: np.ndarray; ignition_s: list; n_ignited: int
    cascade: bool; second_ignition_min: float | None
    def to_json(self, every: int = 50):
        return {"params": self.params, "t_min": (self.t[::every] / 60).round(2).tolist(), "cell_max_C": self.cell_max[::every].round(1).tolist(),
                "ignition_min": [None if v is None else round(v / 60, 2) for v in self.ignition_s], "n_ignited": self.n_ignited, "cascade": self.cascade, "second_ignition_min": self.second_ignition_min}


def build(p: Params):
    """Assemble node capacities C (J/K), conductance matrix K (W/K, Laplacian form) and boundary conductances."""
    R = p.d_cell / 2; H = p.h_cell; ns = p.nsec; radii = [0.0] + list(p.shells); n_rad = len(p.shells)
    # node indexing within a cell: 0 = core, then (shell i >= 1, sector j) -> 1 + (i-1)*ns + j
    per_cell = 1 + (n_rad - 1) * ns; ncell = p.nx * p.ny; N = ncell * per_cell
    C = np.zeros(N); rows, cols, vals = [], [], []
    def add(a, b, g):
        rows.extend([a, b, a, b]); cols.extend([a, b, b, a]); vals.extend([g, g, -g, -g])
    side_area = np.zeros(N); top_area = np.zeros(N); foot_area = np.zeros(N)
    sector_angle = 2 * math.pi / ns
    for c in range(ncell):
        base = c * per_cell
        # core
        C[base] = p.rho * p.cp * math.pi * radii[1] ** 2 * H; top_area[base] = math.pi * radii[1] ** 2; foot_area[base] = top_area[base]
        for i in range(1, n_rad):
            r0, r1 = radii[i], radii[i + 1]; rm = 0.5 * (r0 + r1); area_sec = 0.5 * (r1 ** 2 - r0 ** 2) * sector_angle
            for j in range(ns):
                n = base + 1 + (i - 1) * ns + j
                C[n] = p.rho * p.cp * area_sec * H; top_area[n] = area_sec; foot_area[n] = area_sec
                # radial link inward (through-layer): conductance k_tl * (interface area) / (distance between node centres)
                if i == 1: inner = base; dr = rm - 0.5 * radii[1]
                else: inner = base + 1 + (i - 2) * ns + j; dr = rm - 0.5 * (radii[i - 1] + radii[i])
                add(n, inner, p.k_tl * (r0 * sector_angle * H) / dr)
                # azimuthal link to next sector (in-layer)
                nxt = base + 1 + (i - 1) * ns + (j + 1) % ns
                g_t = p.k_il * ((r1 - r0) * H) / (rm * sector_angle); add(n, nxt, g_t)
                if i == n_rad - 1: side_area[n] = r1 * sector_angle * H
    # inter-cell coupling on the 5 x 4 grid
    D = p.d_cell + p.gap; d = p.d_cell
    S = 2 * math.pi * H / math.acosh((4 * D ** 2 - 2 * d ** 2) / (2 * d ** 2))      # shape factor, two parallel cylinders
    g_air = p.k_air * S; g_holder = p.k_acrylic * p.holder_area / p.gap; g_bus = p.k_steel * p.busbar_area / D
    g_pair = (g_air + g_holder + g_bus) * p.coupling_scale
    outer = n_rad - 1; facing = 3  # sectors facing the neighbour: the nearest sector and one on each side
    def cell_id(ix, iy): return iy * p.nx + ix
    def sector_facing(angle):
        return int(round(angle / sector_angle)) % ns
    links = []
    for iy in range(p.ny):
        for ix in range(p.nx):
            for dx, dy, ang in ((1, 0, 0.0), (0, 1, math.pi / 2)):
                jx, jy = ix + dx, iy + dy
                if jx >= p.nx or jy >= p.ny: continue
                a, b = cell_id(ix, iy), cell_id(jx, jy); sa, sb = sector_facing(ang), sector_facing(ang + math.pi)
                w = np.array([0.25, 0.5, 0.25])
                for k, off in enumerate((-1, 0, 1)):
                    na = a * per_cell + 1 + (outer - 1) * ns + (sa + off) % ns; nb = b * per_cell + 1 + (outer - 1) * ns + (sb - off) % ns
                    add(na, nb, g_pair * w[k])
                links.append((a, b))
    # shared compartment-air node (index N). Only surfaces that face open air couple to it: every top end, and the outer-shell
    # sectors of a cell that do not face a neighbour (the 2 mm gaps between neighbours are already the pair conduction above).
    AIR = N; N += 1
    h_film = p.k_air / p.air_film
    faces_neighbour = np.zeros(AIR, bool)
    for iy in range(p.ny):
        for ix in range(p.nx):
            c = cell_id(ix, iy)
            for dx, dy, ang in ((1, 0, 0.0), (0, 1, math.pi / 2), (-1, 0, math.pi), (0, -1, 3 * math.pi / 2)):
                if 0 <= ix + dx < p.nx and 0 <= iy + dy < p.ny:
                    sa = sector_facing(ang)
                    for off in (-1, 0, 1): faces_neighbour[c * per_cell + 1 + (outer - 1) * ns + (sa + off) % ns] = True
    for n in range(AIR):
        g = h_film * (top_area[n] + (0.0 if faces_neighbour[n] else side_area[n]))
        if g > 0: add(n, AIR, g)
    Lx, Ly, Lz = p.nx * D, p.ny * D, H + 2 * p.wrap_clearance
    wrap_area = 2 * (Lx * Ly) + 2 * (Lx + Ly) * Lz
    air_volume = Lx * Ly * Lz - ncell * math.pi * R ** 2 * H
    C = np.append(C, 1.2 * 1005 * air_volume)
    K = sp.coo_matrix((vals, (rows, cols)), shape=(N, N)).tocsr()
    g_amb = np.zeros(N); g_amb[AIR] = p.h_amb * wrap_area
    foot_area = np.append(foot_area, 0.0)
    if p.h_plate > 0:
        r_series = (H / 2) / p.k_il + p.r_floor + (1.0 / p.h_plate + p.r_cap)
        g_base = foot_area / r_series
    else:
        g_base = np.zeros(N)
    return dict(N=N, per_cell=per_cell, ncell=ncell, AIR=AIR, C=C, K=K, g_amb=g_amb, g_base=g_base, g_pair=g_pair, g_air=g_air, g_holder=g_holder, g_bus=g_bus, g_wrap=g_amb[AIR], links=links)


def pulse_power(tau: float, p: Params) -> float:
    """Triangular pulse: 0 at tau=0, peak at t_peak, back to 0 at t_end; area = w_tr."""
    peak = 2 * p.w_tr / p.t_end
    if tau <= 0 or tau >= p.t_end: return 0.0
    return peak * (tau / p.t_peak if tau < p.t_peak else (p.t_end - tau) / (p.t_end - p.t_peak))


def simulate(p: Params = Params(), record_every: int = 10) -> Result:
    net = build(p); N, pc, nc = net["N"], net["per_cell"], net["ncell"]
    C, K, g_amb, g_base = net["C"], net["K"], net["g_amb"], net["g_base"]
    T = np.full(N, T_AMB); ignition = [None] * nc; ignition[p.first_cell] = p.t_force
    steps = int(round(p.t_final / p.dt)); nrec = steps // record_every + 1
    t_rec = np.zeros(nrec); cmax = np.zeros((nrec, nc)); cmean = np.zeros((nrec, nc)); r = 0
    Cinv = 1.0 / C; Cc = C[:nc * pc]
    mass_frac = Cc / Cc.reshape(nc, pc).sum(1).repeat(pc)  # pulse shared by node heat capacity (uniform volumetric release)
    cells = slice(0, nc * pc)
    # explicit Euler; dt is well inside the stability limit of the smallest node (see module docstring)
    for s in range(steps + 1):
        t = s * p.dt
        if s % record_every == 0:
            Tc = T[cells].reshape(nc, pc); t_rec[r] = t; cmax[r] = Tc.max(1); cmean[r] = (Tc * Cc.reshape(nc, pc)).sum(1) / Cc.reshape(nc, pc).sum(1); r += 1
        q = np.zeros(N)
        for c, t0 in enumerate(ignition):
            if t0 is not None and t0 <= t < t0 + p.t_end:
                P = pulse_power(t - t0, p); q[c * pc:(c + 1) * pc] = P * mass_frac[c * pc:(c + 1) * pc]
        dT = (-(K @ T) + q - g_amb * (T - T_AMB) - g_base * (T - T_AMB)) * Cinv
        T = T + p.dt * dT
        Tc = T[cells].reshape(nc, pc).max(1)
        for c in range(nc):
            if ignition[c] is None and Tc[c] >= p.t_trigger_C: ignition[c] = t + p.dt
    ign = [v for v in ignition if v is not None]; ign_sorted = sorted(ign)
    second = (ign_sorted[1] / 60) if len(ign_sorted) > 1 else None
    return Result(params={k: (list(v) if isinstance(v, tuple) else v) for k, v in asdict(p).items()}, t=t_rec[:r], cell_max=cmax[:r], cell_mean=cmean[:r], ignition_s=ignition, n_ignited=len(ign), cascade=len(ign) > 1, second_ignition_min=second)


def sweep(k_values=(0.5, 0.75, 1.0, 1.25, 1.5, 2.0), h_values=(0, 100, 500, 2000), **kw):
    out = []
    for h in h_values:
        for k in k_values:
            res = simulate(Params(k_tl=k, h_plate=h, **kw))
            out.append({"h_plate": h, "k_tl": k, "n_ignited": res.n_ignited, "cascade": res.cascade, "second_ignition_min": None if res.second_ignition_min is None else round(res.second_ignition_min, 2)})
    return out


if __name__ == "__main__":
    import time
    t0 = time.time(); res = simulate(Params()); print(f"k_tl=1.0 h=2000: ignited {res.n_ignited}/20, second at {res.second_ignition_min} min, pack max {res.cell_max.max():.0f} C  [{time.time()-t0:.1f} s]")
