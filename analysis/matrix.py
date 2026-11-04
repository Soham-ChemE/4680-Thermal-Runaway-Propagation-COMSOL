"""Load, validate and render the run matrix (results/matrix.json). The JSON is the single source of the COMSOL results in
this repository; the README table and the live page are generated from it."""
from __future__ import annotations
import json
from . import MATRIX_PATH

OUTCOMES = {"cascade", "arrested"}


def load(path=MATRIX_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(m: dict) -> list[str]:
    problems = []
    seen = set()
    for r in m["runs"]:
        key = (r["h_plate"], r["k_tl"])
        if key in seen: problems.append(f"duplicate cell {key}")
        seen.add(key)
        if r["outcome"] not in OUTCOMES: problems.append(f"bad outcome {r['outcome']} at {key}")
        if r["status"] not in ("run", "inferred"): problems.append(f"bad status {r['status']} at {key}")
        if r["outcome"] == "arrested" and r["second_ignition_min"] is not None: problems.append(f"arrested run with a second ignition at {key}")
        if r["status"] == "run" and r["outcome"] == "cascade" and r["second_ignition_min"] is None: problems.append(f"cascade run without a second-ignition time at {key}")
        if r["h_plate"] not in m["h_plate_values_W_m2K"] or r["k_tl"] not in m["k_tl_values_W_mK"]: problems.append(f"cell {key} outside the declared axes")
    if sum(r["status"] == "inferred" for r in m["runs"]) != 1: problems.append("exactly one cell must be marked inferred (section A §0.5)")
    return problems


def grid(m: dict) -> dict:
    """{h: {k: run}} for the declared axes; missing cells are None."""
    g = {h: {k: None for k in m["k_tl_values_W_mK"]} for h in m["h_plate_values_W_m2K"]}
    for r in m["runs"]: g[r["h_plate"]][r["k_tl"]] = r
    return g


def cell_label(r) -> str:
    if r is None: return "—"
    if r["status"] == "inferred": return "Cascade (inferred, not run)"
    if r["outcome"] == "cascade": return f"Cascade (2nd ignition ≈ {r['second_ignition_min']:g} min)"
    return "Arrested at cell 1"


def markdown_table(m: dict) -> str:
    ks = m["k_tl_values_W_mK"]; g = grid(m)
    lines = ["| Base cooling h (W/m²·K) | " + " | ".join(f"k_tl = {k:g}" for k in ks) + " |", "|---|" + "---|" * len(ks)]
    for h in m["h_plate_values_W_m2K"]:
        cells = []
        for k in ks:
            r = g[h][k]; lab = cell_label(r)
            if r is not None and r["status"] == "inferred": lab = f"*{lab}*"
            elif r is not None and r["outcome"] == "cascade": lab = f"**{lab}**"
            cells.append(lab)
        lines.append(f"| {h} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    m = load(); p = validate(m)
    print("problems:", p or "none"); print(markdown_table(m))
