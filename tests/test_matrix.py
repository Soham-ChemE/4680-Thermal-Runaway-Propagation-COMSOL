from analysis import matrix as mx


def test_matrix_is_consistent():
    m = mx.load(); assert mx.validate(m) == []


def test_threshold_and_stress_test_are_in_the_data():
    m = mx.load(); g = mx.grid(m)
    # threshold between 1.0 and 1.25 at every cooling value where both were run (section A §2, Phases 2-3)
    for h in (500, 2000):
        assert g[h][1.0]["outcome"] == "cascade" and g[h][1.25]["outcome"] == "arrested"
    # adiabatic stress test: 1.25 cascades at h = 0 and arrests at h = 100 (Phase 4)
    assert g[0][1.25]["outcome"] == "cascade" and g[0][1.25]["second_ignition_min"] == 26.9
    assert g[100][1.25]["outcome"] == "arrested"
    # the one inferred cell is h = 0, k = 1.0 (section A §0.5)
    inf = [r for r in m["runs"] if r["status"] == "inferred"]; assert (inf[0]["h_plate"], inf[0]["k_tl"]) == (0, 1.0)
    # second-ignition times quoted in the notes
    assert g[2000][1.0]["second_ignition_min"] == 22.9 and g[500][1.0]["second_ignition_min"] == 22.4


def test_contact_resistance_null_result():
    m = mx.load(); runs = {r["label"]: r for r in m["contact_resistance_runs"]["runs"]}
    assert runs["tabbed"]["R_cap_m2K_W"] / runs["tabless"]["R_cap_m2K_W"] == 100
    shift = runs["tabless"]["second_ignition_min"] - runs["tabbed"]["second_ignition_min"]
    assert abs(shift - 0.3) < 1e-9 and shift / runs["tabbed"]["second_ignition_min"] < 0.02   # "<2% shift" (section A §0.6)
