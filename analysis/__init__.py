"""Analysis package for the 4680 thermal runaway propagation study.

Nothing in this package runs COMSOL or reproduces the finite-element results. It (a) holds the run matrix as data
(results/matrix.json), (b) reproduces the back-of-envelope scaling arguments in the project notes (analysis.scaling),
(c) draws the phase map and energy-balance figures (analysis.plots), and (d) provides a reduced-order lumped network
surrogate of the pack built here, clearly not the COMSOL model (analysis.lumped).
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "results" / "matrix.json"
ASSETS = ROOT / "docs" / "assets"
