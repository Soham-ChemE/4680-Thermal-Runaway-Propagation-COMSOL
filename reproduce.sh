#!/usr/bin/env bash
# Rebuilds everything derived in this repository: the surrogate sweep (results/lumped_sweep.json), the page data
# (docs/assets/data.js), every figure (docs/assets/fig_*.svg) and the README hero (docs/assets/hero.svg), then runs the tests.
# It does not and cannot re-run the COMSOL studies; those results are transcribed in results/matrix.json.
# Needs: pip install -r requirements.txt
set -euo pipefail
cd "$(dirname "$0")"
python -m analysis.export
python -m analysis.plots
python -m analysis.hero
python -m pytest -q
# python docs/build_assets.py   # static fallbacks for the 3D body scenes, both-theme screenshots and Lighthouse (needs playwright + lighthouse)
