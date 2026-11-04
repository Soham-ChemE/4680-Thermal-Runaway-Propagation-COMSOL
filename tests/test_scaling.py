import math
from analysis import scaling as s


def test_cell_mass_matches_note():
    assert math.isclose(s.cell_mass(), 0.266, rel_tol=0.01)          # section A §3: mass ≈ 0.27 kg (0.266)


def test_adiabatic_rise_about_295_K():
    assert abs(s.adiabatic_temperature_rise() - 295) < 2              # section A §3 sanity check, section B §2.7
    assert 320 < s.T_AMBIENT_C + s.adiabatic_temperature_rise() < 330  # "about 325 °C"


def test_diffusion_times_match_note():
    assert math.isclose(s.thermal_diffusivity(1.0), 3.6e-7, rel_tol=0.02)
    assert abs(s.diffusion_time(s.R_4680, 1.0) - 1470) < 15            # ~1,470 s
    assert abs(s.diffusion_time(s.R_2170, 1.0) - 306) < 4              # ~306 s
    assert abs(s.diffusion_time(s.H_4680 / 2, 30.0) - 150) < 2         # ~150 s axial
    assert 4.5 < s.summary()["radial_ratio_4680_over_2170"] < 5.0      # "about 5x slower"


def test_biot_numbers():
    assert math.isclose(s.biot(100), 2.3, rel_tol=0.01)
    assert math.isclose(s.biot(500), 11.5, rel_tol=0.01)
    assert math.isclose(s.biot(2000), 46, rel_tol=0.01)


def test_h_eff_series():
    assert round(s.h_eff(2000, 1e-3)) == 667
    assert round(s.h_eff(2000, 1e-5)) == 1961
    assert s.h_eff(0, 1e-5) == 0


def test_mass_scaling_bracket():
    r = s.summary()["volume_ratio_4680_over_stock"]
    assert 5.3 < r < 5.7                                               # 46x80 over 21x70 ≈ 5.5
    lo, hi = s.mass_scaled_energy(20e3), s.mass_scaled_energy(30e3)    # "about 20-30 kJ ... roughly 5x"
    assert lo < 110e3 < hi * 1.0 or lo <= 110e3 <= hi                  # 110 kJ sits inside the 20-30 kJ x 5.5 bracket
