"""Back-of-envelope checks from the project notes (section A §3 sanity check, §4 physics; section B §2.7).

Every function is a one-line physical estimate; the numbers in the notes are reproduced by `summary()` and checked by
tests/test_scaling.py. Units are SI unless the name says otherwise.
"""
from __future__ import annotations
import math

# model constants (section A §3): homogenised 4680 cell
D_4680, H_4680 = 0.046, 0.080            # m
R_4680, R_2170 = 0.023, 0.0105           # m (4680 radius, 21700 radius)
RHO, CP = 2000.0, 1400.0                 # kg/m3, J/kg/K
K_TL, K_IL = 1.0, 30.0                   # W/m/K through-layer (radial) stock, in-layer (axial, azimuthal)
W_TR = 110e3                             # J runaway energy per cell used in the study
T_AMBIENT_C = 30.0
# stock cell of the base model, as described in section A §2 Phase 0 caveat ("21x70 mm with 2.5 Ah and 32 kJ")
D_STOCK, H_STOCK, W_STOCK_NOTE = 0.021, 0.070, 32e3
W_STOCK_DOC = 22e3                       # the COMSOL 6.4 documentation page states 22 kJ; see docs/CLAIMS.md


def cylinder_volume(d: float, h: float) -> float:
    return math.pi * (d / 2) ** 2 * h


def cell_mass(d: float = D_4680, h: float = H_4680, rho: float = RHO) -> float:
    """Homogenised cell mass. 4680: 1.33e-4 m3 x 2000 kg/m3 = 0.266 kg (a real 4680 is about 0.35 kg)."""
    return cylinder_volume(d, h) * rho


def adiabatic_temperature_rise(w: float = W_TR, m: float | None = None, cp: float = CP) -> float:
    """dT = W / (m cp). 110 kJ into 0.266 kg at 1400 J/kg/K gives about 295 K, so about 325 C from 30 C."""
    m = cell_mass() if m is None else m
    return w / (m * cp)


def thermal_diffusivity(k: float, rho: float = RHO, cp: float = CP) -> float:
    return k / (rho * cp)


def diffusion_time(length: float, k: float, rho: float = RHO, cp: float = CP) -> float:
    """tau = L^2 / alpha. Radial with k = 1: 4680 (23 mm) about 1,470 s, 21700 (10.5 mm) about 306 s. Axial with k = 30 and
    half-height 40 mm: about 150 s."""
    return length ** 2 / thermal_diffusivity(k, rho, cp)


def biot(h: float, length: float = R_4680, k: float = K_TL) -> float:
    """Bi = h L / k with L = 23 mm, k = 1: h = 100 -> 2.3, 500 -> 11.5, 2000 -> 46."""
    return h * length / k


def mass_scaled_energy(w_base: float, d_base: float = D_STOCK, h_base: float = H_STOCK, d_new: float = D_4680, h_new: float = H_4680) -> float:
    """Scale the base model's runaway energy by cell volume (same density, so by mass). The 4680/stock volume ratio is about
    5.5. From 22 kJ that gives about 120 kJ; from 32 kJ about 175 kJ. The study used 110 kJ, which the note describes as
    'scaled from about 20-30 kJ by active mass and capacity, roughly 5x' and calls an estimate (section A Q8)."""
    return w_base * cylinder_volume(d_new, h_new) / cylinder_volume(d_base, h_base)


def h_eff(h_plate: float, r_cap: float) -> float:
    """Series combination used in the model: h_eff = 1/(1/h_plate + R_cap). 2000 with 1e-3 -> 667; with 1e-5 -> 1961."""
    return 1.0 / (1.0 / h_plate + r_cap) if h_plate > 0 else 0.0


def summary() -> dict:
    m = cell_mass(); dT = adiabatic_temperature_rise()
    return {
        "cell_volume_m3": cylinder_volume(D_4680, H_4680), "cell_mass_kg": m,
        "adiabatic_dT_K": dT, "adiabatic_peak_C": T_AMBIENT_C + dT,
        "alpha_radial_m2_s": thermal_diffusivity(K_TL), "alpha_axial_m2_s": thermal_diffusivity(K_IL),
        "tau_radial_4680_s": diffusion_time(R_4680, K_TL), "tau_radial_2170_s": diffusion_time(R_2170, K_TL),
        "tau_axial_4680_s": diffusion_time(H_4680 / 2, K_IL),
        "radial_ratio_4680_over_2170": diffusion_time(R_4680, K_TL) / diffusion_time(R_2170, K_TL),
        "biot": {h: biot(h) for h in (100, 500, 2000)},
        "volume_ratio_4680_over_stock": cylinder_volume(D_4680, H_4680) / cylinder_volume(D_STOCK, H_STOCK),
        "mass_scaled_energy_from_22kJ_J": mass_scaled_energy(W_STOCK_DOC), "mass_scaled_energy_from_32kJ_J": mass_scaled_energy(W_STOCK_NOTE),
        "h_eff_tabbed": h_eff(2000, 1e-3), "h_eff_tabless": h_eff(2000, 1e-5),
    }


if __name__ == "__main__":
    for k, v in summary().items():
        print(f"{k:36s} {v}")
