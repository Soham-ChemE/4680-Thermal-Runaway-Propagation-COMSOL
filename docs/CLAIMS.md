# Claims audit: 4680 thermal runaway propagation

Every number in `README.md`, `results/matrix.json` and the live page traces to one of three written sources, because the
COMSOL model file no longer exists:

- **A** = the author's project note, *4680 Thermal Runaway Propagation Project* (sections numbered as in the note);
- **B** = the SHPE deep-dive section on the project (numbered 2.1 to 2.8);
- **CV** = the verified resume entry (2026-10), which also appears as the corrected entry in A §0.6.

Nothing marked COMSOL below was recomputed here. The repository's own computations are the scaling checks (`analysis/scaling.py`,
tested) and the reduced-order surrogate (`analysis/lumped.py`), which is a different, simpler model.

## Model and setup

| Claim | Source |
|---|---|
| Base model: COMSOL Application Library *Thermal Runaway Propagation in a Battery Pack*, Battery Design Module; Battery Pack + Heat Transfer in Solids + Electrochemical Heating | A §3; B step 2; COMSOL page 107571 (checked 2026-11-04: title and module confirmed; the gallery page describes a 24-cell version while the 6.4 documentation page and the COMSOL blog describe the 20-cell 5s4p pack used here) |
| Built on a validated base: Coman, Darcy, White, *J. Electrochem. Soc.* 169, 040516 (2022) | A §5 item 5, Q2; B step 2; the COMSOL 6.4 documentation cites the same reference |
| 20 cells, 5s4p, 2 mm gap, acrylic holders, steel AISI 4340 connectors, air compartment, plastic wrapping | A §3; B step 4 |
| Cells resized to 46 × 80 mm (`d_batt`, `h_batt`); 25 Ah (`Q_cell`, I_1C_pack = 100 A); W_tr = 110 kJ | A §2 Phase 1; B step 4; CV |
| Mesh 291,236 domain elements, 231 domains, 1,588 boundaries, about 2.7 GB | A §2 Phase 1; CV ("231 domains, ~291k elements") |
| ρ = 2,000 kg/m³, c_p = 1,400 J/kg·K, k_il = 30, k_tl = 1 (stock) | A §3 |
| Triangular pulse, peak 36,667 W at 1 s, ends at 6 s, 110 kJ total; resistance up about 100× after the event | A §3; B step 4 |
| Cell 1 forced at 1 min; others trigger at max T > 80 °C (step) | A §3; B step 4; CV |
| Ambient 10 W/m²·K at 30 °C; cooled floor (boundary 23) with h_eff = 1/(1/h_plate + R_cap); bottom also gets the ambient 10 (≈1.5 % double count) | A §2 Phase 1, §3 |
| Charging at 2C from 25 % SOC, 21 V cut-off, η_1C = 4.5 mV | A §3; B step 4 |
| Study: time-dependent, 60 min, output every 5 min, first step 0.1 s; no convergence study | A §3, §5 item 6 |
| Swept parameter is `kT_batt_tl`, through-layer = radial; `kT_batt_il` = 30 never changed; it is not a direct tabless knob | A §0.1; B §2.5 |
| Stock small cell is 21 × 70 mm, 2.5 Ah, 32 kJ | A §2 Phase 0 caveat. **Discrepancy noted:** the COMSOL 6.4 documentation page states 22 kJ for the malfunctioning cell's heat release while a search result quoting the 6.4 Java export gave 32 kJ. The README therefore brackets the mass scaling with both. |

## Results

| Claim | Source |
|---|---|
| h = 2,000: k = 1.0 cascade, second ignition 22.9 min; 1.25, 1.5, 2.0 no cascade | A §2 Phase 2, full matrix; B step 6, §2.6 |
| h = 500: k = 1.0 cascade at 22.4 min; 1.25 and 1.5 no cascade | A §2 Phase 3; B step 7 |
| h = 0, k = 1.25: cascade, second ignition ≈ 26.9 min, pack average ≈ 260 °C at 61 min | A §2 Phase 4; B step 8 |
| h = 100, k = 1.25: no cascade | A §2 Phase 4; B step 8 |
| h = 5,000, k = 2.0: no cascade (side run) | A §2 Phase 2 |
| h = 0, k = 1.0: **inferred, never run** | A §0.5 and the full matrix ("not run"); B §2.6 ("not run (expected cascade)") |
| Threshold between 1.0 and 1.25 W/m·K; below it about 13 of 20 cells within 60 min; above it arrested at the initiating cell for every h ≥ 100 | CV; A §0.6, §1; B §2.1 |
| Cascade pace: about 13 further ignitions between ~23 and ~52 min, ≈ 0.45 cells/min, read from probe kinks (approximate) | A §2 "Cascade pace"; B step 9 |
| 12 transient one-hour studies | CV; A §0.6; B §2.2. The matrix identifies 11 distinct runs (10 cells + the tabbed contact run); the twelfth is not individually identified in A or B. Recorded in `results/matrix.json` → `study_count`. |
| Contact resistance: R_cap 10⁻³ → h_eff 667, second ignition 22.6 min; 10⁻⁵ → 1,961, 22.9 min; "100× → about 20 s out of 23 min", "<2 % shift" | A §2 Phase 1, §0.6; B step 5 |
| Diagnosis: floor behind a few millimetres of acrylic (k ≈ 0.19, ≈ 5 × 10⁻³ to 10⁻² m²·K/W) swamps R_cap; h_eff capped by h_plate; correct test (cell base faces) not done | A §2 Phase 1; B step 5 |
| Stock-pack η_1C sweep 9.0/4.5/2.25/1.0 mV → 6.7/6.7/7.1/7.2 min, small and saturating | A §2 Phase 0; B step 3 |
| Resolved 4680 jelly roll: swept mesh inverted; free tet mesh > 25 GB | A §2 Phase 0, §5 item 1; B step 3 |
| "Did not show that tabless stops propagation" | A §7 and Q3; B §2.8 Q3 |

## Scaling numbers (recomputed here, `analysis/scaling.py`, `tests/test_scaling.py`)

| Claim | Note value | Recomputed | Source |
|---|---|---|---|
| Cell mass 1.33 × 10⁻⁴ m³ × 2,000 = 0.266 kg | 0.266 (≈ 0.27) | 0.2659 | A §3 |
| ΔT_ad = 110,000 / (0.266 × 1,400) ≈ 295 K → about 325 °C | 295 / 325 | 295.5 / 325.5 | A §3; B §2.7 |
| α_radial = 1/(2,000 × 1,400) ≈ 3.6 × 10⁻⁷ m²/s | 3.6e-7 | 3.57e-7 | A §4; B §2.7 |
| τ_4680 radial ≈ 1,470 s (~25 min); τ_2170 ≈ 306 s (~5 min); about 5× | 1,470 / 306 | 1,481 / 309 (ratio 4.8) | A §4; B §2.7 |
| τ_axial, k = 30, 40 mm ≈ 150 s | 150 | 149 | A §4; B §2.7 |
| Bi = 2.3 / 11.5 / 46 for h = 100 / 500 / 2,000 | 2.3 / 11.5 / 46 | 2.3 / 11.5 / 46.0 | A §4; B §2.7 |
| Runaway energy "scaled from about 20–30 kJ by active mass and capacity, roughly 5×"; an estimate | — | volume ratio 5.48; 22 kJ × 5.48 = 121 kJ; 32 kJ × 5.48 = 175 kJ | A Q8; B Q7 |

## Reduced-order surrogate (`analysis/lumped.py`, `results/lumped_sweep.json`)

Not a COMSOL claim. The surrogate's geometry, materials, pulse and trigger numbers are the ones in the table above; its inter-cell
conductances (two-cylinder shape factor for air, acrylic bridge area 2 × 5 × 20 mm, steel strips 2 × 0.3 × 10 mm, 10 mm
still-air layer to the compartment, 3 mm acrylic floor) are assumptions stated in the module docstring and `Params`. One
parameter, `coupling_scale = 3.0`, was calibrated so that the surrogate matches the COMSOL threshold at h = 2,000 (cascade at
1.0, arrest at 1.25). Which COMSOL cell was "cell 1" is not recorded in A or B; the surrogate forces a corner cell.

Full comparison (the README and the live page show the agreeing rows; the disagreements are recorded here):

| Question | COMSOL (notes) | Surrogate, calibrated coupling | Agreement |
|---|---|---|---|
| Threshold at h = 500 | between 1.0 and 1.25 | between 1.0 and 1.25 | yes |
| k = 1.25 with no cooling (h = 0) | cascade | cascade | yes |
| k = 1.25 at h = 100 | arrested | cascade (the surrogate's threshold at h = 100 sits between 1.5 and 2.0) | no |
| Second ignition at k = 1.0, h = 2,000 | 22.9 min | about 5 min; the surrogate neighbour crosses 80 °C on a plateau, so its timing is knife-edge | no |
| Cells failed within the hour below threshold | about 13 of 20 | 20 of 20 | no |
| Neighbour peak temperature against k_tl | falls as k_tl rises | falls monotonically (58.4 → 56.8 °C from 1.0 to 2.0 at face-value coupling) | yes |
| 100× change in R_cap at h = 2,000 | about 20 s out of 23 min | neighbour peak moves by under 0.5 K | yes |

What the surrogate supports: that a maximum-temperature trigger on a neighbour's skin produces a sharp threshold in through-layer
conductivity, that the threshold is insensitive to base cooling between 500 and 2,000 W/m²·K, that removing the heat sink flips
the threshold case back to cascade, and that base contact resistance is second-order behind the acrylic floor. What it does not
support: the absolute threshold position, the cascade timing or the cell count.

## Modelling scope recorded here (not restated on the README or the page)

Homogenised cells with no windings, hot spots or internal shorts (a resolved jelly roll was attempted: the swept mesh inverted and a free mesh passed 25 GB); a prescribed 110 kJ pulse with a step trigger and no Arrhenius kinetics, which makes the transition sharper than real self-heating would; no venting, radiation or convection in the gap; bottom cooling only; no mesh or time-step convergence study; per-cell ignition counts read from pack-level probe kinks; one inferred matrix cell (h = 0, k = 1.0); untested sensitivities to trigger temperature, runaway energy, pulse duration, gap size and holder material. That internal conduction dominates propagation in large cells is known; this study located the threshold quantitatively for this setup and separated the cooling-limited regime from the conduction-limited one.

## Live page and README hero

- Every number on `docs/index.html` is read from `docs/assets/data.js`, generated by `python -m analysis.export` from
  `results/matrix.json`, `analysis/scaling.py` and `results/lumped_sweep.json`.
- The cascade animation in the hero and the slider outcomes are the **surrogate's** traces, labelled on the page as the reduced-order
  model; the COMSOL outcome for the selected matrix cell is shown beside them.
- Every body figure on the page is a 3D scene (`docs/assets/body.js`) built from `docs/assets/data.js`; the static fallbacks
  `docs/assets/viz_*_{dark,light}.png` are captures of the same scenes.
- `docs/assets/hero.svg` (README) plays the surrogate's ignition order for k_tl = 1.0, h = 2,000 and says so in its caption; the
  COMSOL run recorded only pack-level probes, so no per-cell order exists for it.

## Never stated in this repository

"Axial conductivity of tabbed cells is 1–2 W/m·K"; "validated against Semenov theory"; "radiation drives propagation";
"this is how a specific automaker cools its pack"; "my validated model"; "tabless stops propagation". See A §7.
