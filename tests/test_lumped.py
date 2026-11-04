import json, math
import numpy as np
import pytest
from analysis.lumped import Params, simulate, build, pulse_power
from analysis import scaling as sc


def test_pulse_integrates_to_110_kJ():
    p = Params(); t = np.linspace(0, p.t_end, 60001); P = np.array([pulse_power(x, p) for x in t])
    assert math.isclose(np.trapezoid(P, t), p.w_tr, rel_tol=1e-3)
    assert math.isclose(max(P), 36667, rel_tol=1e-3)          # peak 36,667 W (section A §3)


def test_single_cell_adiabatic_rise_matches_energy_balance():
    # isolate one cell: no base cooling, no ambient, no neighbours (nx = ny = 1), air film off -> uniform cell must reach 30 + 295 C
    p = Params(nx=1, ny=1, h_plate=0, h_amb=0, air_film=1e9, t_final=600, first_cell=0)
    r = simulate(p)
    assert abs(r.cell_mean[-1, 0] - (sc.T_AMBIENT_C + sc.adiabatic_temperature_rise())) < 2.0


def test_cell_capacity_matches_mass():
    net = build(Params()); C = net["C"][:net["per_cell"]].sum()
    assert math.isclose(C, sc.cell_mass() * sc.CP, rel_tol=1e-6)


@pytest.mark.slow
def test_threshold_between_1_and_1p25_at_calibrated_coupling():
    # with the single calibrated parameter (coupling_scale = 3.0) the surrogate cascades at k_tl = 1.0 and arrests at 1.25 for h = 2000
    a = simulate(Params(k_tl=1.0, h_plate=2000, coupling_scale=3.0)); b = simulate(Params(k_tl=1.25, h_plate=2000, coupling_scale=3.0))
    assert a.cascade and not b.cascade


def test_neighbour_peak_falls_with_through_layer_conductivity():
    peaks = [simulate(Params(k_tl=k, h_plate=2000, t_final=1800)).cell_max[:, 1].max() for k in (0.5, 1.0, 2.0)]
    assert peaks[0] > peaks[1] > peaks[2]


def test_contact_resistance_is_second_order():
    a = simulate(Params(k_tl=1.0, h_plate=2000, r_cap=1e-3, t_final=1800)); b = simulate(Params(k_tl=1.0, h_plate=2000, r_cap=1e-5, t_final=1800))
    assert abs(a.cell_max[:, 1].max() - b.cell_max[:, 1].max()) < 1.0   # a 100x change in R_cap moves the neighbour peak by < 1 K
