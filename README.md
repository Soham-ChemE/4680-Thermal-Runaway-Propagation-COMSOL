<p align="center"><a href="https://soham-cheme.github.io/4680-Thermal-Runaway-Propagation-COMSOL/"><img src="docs/assets/hero.svg" alt="Thermal runaway propagation in a 20-cell 4680 pack: top view of the pack with a cascade playing, next to the headline numbers" width="100%"></a></p>

<p align="center"><b><a href="https://soham-cheme.github.io/4680-Thermal-Runaway-Propagation-COMSOL/">Open the live page</a></b> · the 20-cell pack in 3D with the cascade playing, a conductivity slider that flips it from cascade to arrest, and the run-matrix phase map</p>

<div align="center">

[![COMSOL](https://img.shields.io/badge/COMSOL-6.4%20%C2%B7%20Battery%20Design%20Module-0b1220?style=flat-square)](https://www.comsol.com/model/thermal-runaway-propagation-in-a-battery-pack-107571)
[![Studies](https://img.shields.io/badge/transient%20studies-12%20%C3%97%2060%20min-0b1220?style=flat-square)](#the-run-matrix)
[![Threshold](https://img.shields.io/badge/cascade%20threshold-1.0%E2%80%931.25%20W%2Fm%C2%B7K-0b1220?style=flat-square)](#the-threshold)
[![Tests](https://img.shields.io/badge/analysis-pytest%20passing-0b1220?style=flat-square)](#reproduce-what-is-reproducible)
[![Audit](https://img.shields.io/badge/claims-traced%20in%20docs%2FCLAIMS.md-0b1220?style=flat-square)](docs/CLAIMS.md)

**Soham Kavathekar** · independent project · COMSOL Multiphysics 6.4, Battery Design Module, transient FEA

</div>

---

## The one-paragraph version

**A 20-cell pack of 4680-format cells was built in COMSOL by adapting the Application Library model *Thermal Runaway Propagation in a Battery Pack* to 46 × 80 mm cells, 25 Ah and about 110 kJ of runaway energy per cell. One cell is forced into runaway at one minute; any other cell triggers when its maximum temperature crosses 80 °C. Twelve transient one-hour studies across the cell's through-layer (radial) thermal conductivity and the base cooling coefficient found a sharp cascade threshold between 1.0 and 1.25 W/m·K: below it, about 13 of the 20 cells failed within the hour; above it, propagation stopped at the initiating cell. The threshold did not move for any base cooling from 100 to 2,000 W/m²·K, but with no cooling at all the 1.25 W/m·K case cascaded again. A 100× change in the cap contact resistance moved the onset of propagation by about 20 s out of 23 min, which is what redirected the study to internal conduction.**

> **What is and is not in this repository**
>
> **In:** the written record of the study (what was asked, built, run and not run), the full run matrix as data (`results/matrix.json`), a Python package that reproduces the scaling arguments behind the numbers and generates every figure, a reduced-order lumped network surrogate of the pack built here, the claim-by-claim source audit (`docs/CLAIMS.md`), and the live page.
>
> **Not in:** the COMSOL `.mph` file, the mesh, the solver logs or any field data. The work was done on a university machine and only the written record survives. Nothing in this repository re-runs the finite-element model; the COMSOL numbers below are transcribed from the project notes and are marked as such. The surrogate in `analysis/lumped.py` is a separate, simpler model and is labelled that way wherever it appears.

---

## What was asked

The tabless 4680 is usually discussed electrically: lower internal resistance, better fast charging. The question here was whether anything about the format changes **thermal runaway propagation** between cells in a pack, and, more usefully, which thermal resistance actually controls whether failure spreads.

## What was built

Base model: COMSOL Application Library, *Thermal Runaway Propagation in a Battery Pack* (Application ID 107571, Battery Design Module), which couples a lumped Battery Pack interface, Heat Transfer in Solids and Electrochemical Heating and is built on the simplified propagation model of Coman, Darcy and White, *J. Electrochem. Soc.* 169, 040516 (2022). That model was adapted, not rebuilt:

| Item | Value | Note |
|---|---|---|
| Pack | 20 cells, 5s4p, 2 mm gaps, acrylic holders, steel AISI 4340 connectors, air compartment, plastic wrap | stock layout |
| Cell | 46 × 80 mm homogenised cylinder | volume 1.33 × 10⁻⁴ m³, mass ≈ 0.27 kg at 2,000 kg/m³ (a real 4680 is about 0.35 kg) |
| Thermal properties | ρ = 2,000 kg/m³, c<sub>p</sub> = 1,400 J/kg·K, in-layer k = 30 W/m·K, through-layer k = 1 W/m·K (stock) | spirally wound Battery Layers node |
| Electrical | 25 Ah per cell (100 A at 1C for the four parallel strings), 2C charge from 25 % SOC, 21 V pack cut-off, η<sub>1C</sub> = 4.5 mV | lumped battery model |
| Runaway | Thermal Event: triangular pulse, peak 36,667 W at t = 1 s, ends at 6 s, total 110 kJ; ohmic resistance up about 100× after the event | energy mass-scaled from the small stock cell (see below) |
| Trigger | cell 1 forced at t = 1 min; any other cell triggers when its **maximum** temperature exceeds 80 °C | step function, no reaction kinetics |
| Cooling | ambient 10 W/m²·K at 30 °C on all boundaries; a cooled base (pack floor) with h<sub>eff</sub> = 1 / (1/h<sub>plate</sub> + R<sub>cap</sub>) | bottom-cooled boundary as a simplified case |
| Mesh | 291,236 domain elements, 231 domains, 1,588 boundaries, about 2.7 GB | swept mesh through the cylinders |
| Study | time-dependent, 60 min, output every 5 min, first step 0.1 s | no mesh- or time-step-convergence study |

**Swept parameter, stated precisely.** In COMSOL's spirally wound Battery Layers node, `kT_batt_tl` is the *through-layer* conductivity: across the windings, the **radial** direction in a cylindrical cell (stock 1 W/m·K). `kT_batt_il`, the *in-layer* conductivity along the foils (azimuthal and axial, stock 30 W/m·K), was never changed. The sweep below varied the through-layer value. It is not a direct "tabless" knob: tabless construction changes how the foil edges connect to the cap, not the bulk conductivity across the layers.

## The run matrix

Rows are base cooling h<sub>plate</sub> (W/m²·K), columns are through-layer conductivity k<sub>tl</sub> (W/m·K). All cases: R<sub>cap</sub> = 10⁻⁵ m²·K/W, 110 kJ per cell, 25 Ah. **Bold** cells cascaded; the italic cell was **inferred and never run**. Generated from `results/matrix.json` by `python -m analysis.matrix`.

| Base cooling h (W/m²·K) | k_tl = 1 | k_tl = 1.25 | k_tl = 1.5 | k_tl = 2 |
|---|---|---|---|---|
| 0 | *Cascade (inferred, not run)* | **Cascade (2nd ignition ≈ 26.9 min)** | — | — |
| 100 | — | Arrested at cell 1 | — | — |
| 500 | **Cascade (2nd ignition ≈ 22.4 min)** | Arrested at cell 1 | Arrested at cell 1 | — |
| 2000 | **Cascade (2nd ignition ≈ 22.9 min)** | Arrested at cell 1 | Arrested at cell 1 | Arrested at cell 1 |
| 5000 | — | — | — | Arrested at cell 1 |

<p align="center"><img src="docs/assets/fig_phase_map_dark.svg" alt="Phase map of the COMSOL run matrix: cascade below 1.0 to 1.25 W/m·K, arrested above, inferred cell hatched" width="80%"></p>

The resume and the notes count 12 transient one-hour studies. The matrix identifies 10 run cells plus the tabbed contact-resistance run described below; the notes do not individually identify the twelfth.

## The threshold

- At h<sub>plate</sub> = 2,000: k<sub>tl</sub> = 1.0 cascaded (second ignition at 22.9 min); 1.25, 1.5 and 2.0 stopped at cell 1.
- At h<sub>plate</sub> = 500: the same threshold (1.0 cascaded at 22.4 min; 1.25 and 1.5 stopped). The threshold is not a cooling artefact.
- **Cascade pace** (k<sub>tl</sub> = 1.0, h = 2,000): about 13 further ignitions between about 23 and 52 min, roughly 0.45 cells per minute after onset. The count was read from kinks in the pack-maximum and pack-average temperature probes, not from per-cell probes, so it is approximate.
- **Mechanism in this model.** A neighbour triggers when its *maximum* temperature crosses 80 °C, and that maximum sits on the skin facing the burning cell. With low through-layer conductivity the arriving heat piles up at that skin; with higher conductivity it spreads into the interior and down to the cooled base, and the local maximum stays below 80 °C. The transition is sharp because the trigger is a step: the threshold comes from the trigger crossing. It is *analogous* to a thermal-explosion tipping point, but the model has no Arrhenius kinetics, so real self-heating would make the transition softer and probably shift it.

## The adiabatic stress test

At the threshold value k<sub>tl</sub> = 1.25: **h<sub>plate</sub> = 0 cascaded** (second ignition at about 26.9 min, pack average about 260 °C at 61 min) and **h<sub>plate</sub> = 100 arrested**. So near the threshold a cell needs both an internal conduction path and a heat sink, and above about 100 W/m²·K more cooling does not move the threshold. The Biot number explains why: with L = 23 mm and k = 1 W/m·K, h = 100 gives Bi ≈ 2.3, h = 500 gives 11.5 and h = 2,000 gives 46. Internal conduction is the bottleneck well before the plate is.

## The null result on contact resistance

The first representation of tabless was a lower thermal contact resistance at the cell base, R<sub>cap</sub> = 10⁻³ (tabbed) against 10⁻⁵ m²·K/W (tabless), in h<sub>eff</sub> = 1/(1/h<sub>plate</sub> + R<sub>cap</sub>) on the pack floor with h<sub>plate</sub> = 2,000 (h<sub>eff</sub> = 667 against 1,961 W/m²·K). The second ignition moved from 22.6 to 22.9 min: a **100× change produced about 20 s out of 23 min**. Diagnosis: the cooled boundary is the pack enclosure floor, behind a few millimetres of acrylic holder (k ≈ 0.19 W/m·K, roughly 5 × 10⁻³ to 10⁻² m²·K/W), which is larger than the tabbed contact resistance and swamps the difference; h<sub>eff</sub> was also capped by h<sub>plate</sub>. The correct tabless test, applying cooling and contact resistance directly on each cell's own base face, was not run. An earlier sweep of the stock pack's ohmic overpotential (9.0 → 1.0 mV) moved the second-ignition delay only from 6.7 to 7.2 min, small and saturating, so neither electrical nor base-contact representations of tabless were first-order in this setup. **This study did not show that tabless stops propagation.**

## Scaling arguments (reproduced in `analysis/scaling.py`)

| Check | Result | Test |
|---|---|---|
| Adiabatic temperature rise, 110 kJ into 0.266 kg at 1,400 J/kg·K | ΔT ≈ 295 K, about 325 °C, matching the 280 to 340 °C peaks in the runs. Real cells reach 600 °C and more because heat is released locally and gas burns; total energy is right, peak temperature is under-predicted. | `test_adiabatic_rise_about_295_K` |
| Radial diffusion time R²/α with k = 1 (α ≈ 3.6 × 10⁻⁷ m²/s) | 4680 (R = 23 mm) ≈ 1,470 s, about 25 min; 21700 (R = 10.5 mm) ≈ 306 s, about 5 min: about 5× slower radial heat removal | `test_diffusion_times_match_note` |
| Axial diffusion time with k = 30 over the 40 mm half-height | ≈ 150 s, about 10× faster than radial | same |
| Biot number, L = 23 mm, k = 1 | h = 100 → 2.3; 500 → 11.5; 2,000 → 46 | `test_biot_numbers` |
| Mass scaling of runaway energy | the 46 × 80 mm cell has 5.5× the volume of the 21 × 70 mm stock cell; 20 to 30 kJ × 5.5 brackets 110 to 165 kJ; the study used 110 kJ, an estimate at the low end, and the energy sensitivity was not run | `test_mass_scaling_bracket` |

<p align="center"><img src="docs/assets/fig_energy_balance_dark.svg" alt="Left: adiabatic peak temperature against runaway energy with the 110 kJ point at about 325 °C; right: diffusion times for 4680 radial, 2170 radial and 4680 axial" width="92%"></p>

## Reduced-order surrogate (built here; not the COMSOL model)

`analysis/lumped.py` is a transparent thermal network of the same pack: each cell is a core plus five radial shells split into 16 azimuthal sectors (radial links use k<sub>tl</sub>, azimuthal links use k<sub>il</sub>), neighbours are coupled through still air (two-cylinder conduction shape factor), acrylic holder bridges and steel connector strips, the cells sit in a wrapped air compartment that loses heat to ambient at 10 W/m²·K, and the base cooling acts on each cell's footprint through the half-height axial path, a 3 mm acrylic floor and 1/h<sub>eff</sub>. Same 110 kJ six-second pulse, same 80 °C maximum-temperature trigger, cell 1 forced at 1 min, explicit time stepping at 0.1 s for 60 min (about one second per run).

With the inter-cell conductances taken at face value the neighbour of the burning cell peaks at about 58 °C and nothing propagates. One parameter was therefore calibrated: the inter-cell coupling multiplied by 3.0, chosen so that at h = 2,000 the surrogate cascades at 1.0 W/m·K and arrests at 1.25 W/m·K, i.e. so that it matches the COMSOL threshold at one cooling value. Everything else is a prediction:

| Question | COMSOL (notes) | Surrogate, calibrated coupling | Agreement |
|---|---|---|---|
| Threshold at h = 500 | between 1.0 and 1.25 | between 1.0 and 1.25 | yes |
| k = 1.25 with no cooling (h = 0) | cascade | cascade | yes |
| k = 1.25 at h = 100 | arrested | cascade (the surrogate's threshold at h = 100 sits between 1.5 and 2.0) | no |
| Second ignition at k = 1.0, h = 2,000 | 22.9 min | about 5 min | no: the surrogate neighbour crosses 80 °C on a plateau, so its timing is knife-edge |
| Cells failed within the hour below threshold | about 13 of 20 | 20 of 20 | no |
| Neighbour peak temperature against k<sub>tl</sub> | falls as k<sub>tl</sub> rises (the mechanism above) | falls monotonically (58.4 → 56.8 °C from 1.0 to 2.0 at face-value coupling) | yes |
| 100× change in R<sub>cap</sub> at h = 2,000 | about 20 s out of 23 min | neighbour peak moves by under 0.5 K | yes |

What the surrogate supports: that a maximum-temperature trigger on a neighbour's skin produces a sharp threshold in through-layer conductivity, that the threshold is insensitive to base cooling between 500 and 2,000 W/m²·K, that removing the heat sink flips the threshold case back to cascade, and that base contact resistance is second-order behind the acrylic floor. What it does not support: the absolute threshold position (it depends on inter-cell conductances the surrogate cannot pin down from first principles), the cascade timing or the cell count. Treat it as a reading aid for the COMSOL result, not as evidence of it.

<p align="center"><img src="docs/assets/fig_lumped_phase_dark.svg" alt="Phase map of the surrogate sweep over cooling and conductivity" width="48%"> <img src="docs/assets/fig_lumped_traces_dark.svg" alt="Per-cell maximum temperature traces from the surrogate for the cascade and arrested cases" width="48%"></p>

## Limitations, stated plainly

- **Homogenised cells.** Each cell is a uniform anisotropic solid; no windings, hot spots or internal shorts. A fully resolved 4680 jelly roll was attempted: the swept mesh inverted on the inner turns and a free tetrahedral mesh exceeded 25 GB.
- **Fixed trigger, no chemistry.** Heat is a prescribed 110 kJ pulse released when a cell's maximum temperature crosses 80 °C. No SEI, anode or cathode Arrhenius kinetics. The sharp transition partly reflects this choice.
- **No venting, no radiation, no convection** in the air gap. Heat crosses between cells by conduction through air, the acrylic holders and the steel connectors. Real packs also move heat by radiation and hot vent gas, which make propagation easier.
- **Bottom cooling only**, on the pack floor, as a simplified case. It is not a replica of any production pack's cooling architecture.
- **No experimental validation** of the 4680 parameters. The model is built on a validated base (Coman et al., 2022); the 4680 energy, trigger and geometry are uncalibrated. No mesh- or time-step-convergence study. No per-cell probes, so ignition counts are approximate. One matrix cell (h = 0, k = 1.0) was inferred, not run. Untested sensitivities: trigger temperature, runaway energy, pulse duration, gap size, holder material.
- **Not a novel finding.** That internal conduction dominates propagation in large cells is known. What this study did was build the model, locate the threshold quantitatively for this setup, and separate the cooling-limited regime from the conduction-limited one.

## Reproduce what is reproducible

```bash
git clone https://github.com/Soham-ChemE/4680-Thermal-Runaway-Propagation-COMSOL.git
cd 4680-Thermal-Runaway-Propagation-COMSOL
pip install -r requirements.txt
./reproduce.sh        # surrogate sweep, page data, every figure, README hero, tests
python -m analysis.scaling   # prints the scaling checks
python -m analysis.matrix    # validates results/matrix.json and prints the table above
```

The COMSOL studies themselves cannot be re-run from this repository. The live page (`docs/index.html`) has no build step; it loads three.js 0.186.1, GSAP 3.15.0 and Lenis 1.3.27 from pinned CDN URLs. Design rationale is in [`docs/DESIGN.md`](docs/DESIGN.md); screenshots and the Lighthouse report are in [`docs/qa/`](docs/qa/).

## Sources

- COMSOL Application Library, *Thermal Runaway Propagation in a Battery Pack*, Application ID 107571: https://www.comsol.com/model/thermal-runaway-propagation-in-a-battery-pack-107571 (Battery Design Module). COMSOL 6.4 documentation page: https://doc.comsol.com/6.4/doc/com.comsol.help.models.battery.thermal_runaway_propagation/thermal_runaway_propagation.html. COMSOL blog, J. Carew, *Simulating Thermal Propagation in a Battery Pack* (June 2024): https://www.comsol.com/blogs/simulating-thermal-propagation-in-a-battery-pack.
- P. T. Coman, E. C. Darcy and R. E. White, "Simplified Thermal Runaway Model for Assisting the Design of a Novel Safe Li-Ion Battery Pack", *J. Electrochem. Soc.* 169, 040516 (2022).
- The author's project notes and the SHPE deep-dive write-up, transcribed claim by claim in [`docs/CLAIMS.md`](docs/CLAIMS.md).

## Contact

Soham Kavathekar · MS Chemical & Biomolecular Engineering, University of Pennsylvania · [stg3719@seas.upenn.edu](mailto:stg3719@seas.upenn.edu) · [linkedin.com/in/soham-kavathekar-cheme](https://www.linkedin.com/in/soham-kavathekar-cheme)

MIT License.
