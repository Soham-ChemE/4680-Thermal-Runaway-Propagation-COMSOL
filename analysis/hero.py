"""Animated README hero: docs/assets/hero.svg. Top view of the 5 x 4 pack; the cells light up in the order and at the times
the reduced-order surrogate predicts for k_tl = 1.0, h = 2000 (its cascade case), compressed to a 16 s loop, next to the
COMSOL headline numbers. CSS keyframes only (GitHub renders them through <img>); no SMIL, no scripts, no fonts."""
from __future__ import annotations
import json
from . import ROOT, ASSETS
from . import matrix as mx

CASCADE, COOL, INK, MUTED, BG = "#f97316", "#334155", "#e6edf3", "#8b98a9", "#0b1220"


def main():
    m = mx.load(); S = json.load(open(ROOT / "results" / "lumped_sweep.json"))
    tr = S["traces"][S["trace_cascade"]]; ign = tr["ignition_min"]; nx, ny = 5, 4
    t_end = max(v for v in ign if v is not None); loop = 16.0; hold = 3.0  # seconds of real time per loop, and a hold at the end
    cells = []; css = []
    for c in range(nx * ny):
        ix, iy = c % nx, c // nx; cx, cy = 1000 + ix * 96, 108 + iy * 96
        cells.append(f'<g class="cell c{c}"><circle cx="{cx}" cy="{cy}" r="44" fill="{COOL}" stroke="#1f2a3c" stroke-width="2"/><circle cx="{cx}" cy="{cy}" r="44" class="hot" fill="{CASCADE}"/><circle cx="{cx}" cy="{cy}" r="10" fill="#0b1220" opacity=".6"/></g>')
        if ign[c] is not None:
            start = (ign[c] / t_end) * (loop - hold) / loop * 100  # percent of the loop at which this cell ignites
            css.append(f".c{c} .hot{{animation-delay:{start/100*loop:.2f}s}}")
    css_text = "\n".join(css)
    rows = [("1.0 → 1.25 W/m·K", "sharp cascade threshold in through-layer (radial) conductivity"),
            ("13 of 20 cells", "cascade within an hour below the threshold; above it, arrested at cell 1"),
            ("110 kJ per cell", "mass-scaled runaway energy, 80 °C trigger, 20-cell 5s4p 4680 pack"),
            ("12 studies", "transient one-hour COMSOL runs, cooling 0 to 2,000 W/m²·K")]
    stats = "".join(f'<g class="st s{i}"><text x="80" y="268" class="big">{a}</text><text x="80" y="300" class="small">{b}</text></g>' for i, (a, b) in enumerate(rows))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 500" width="1600" height="500" role="img" aria-label="Thermal runaway propagation in a 20-cell 4680 pack: top view of the pack with the cascade playing, next to the headline numbers">
<style>
.t{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
.h{{font-size:54px;font-weight:800;fill:{INK};letter-spacing:-1.5px}}.sub{{font-size:21px;fill:{MUTED}}}.big{{font-size:34px;font-weight:800;fill:#22d3ee}}.small{{font-size:16px;fill:{MUTED}}}.foot{{font-size:15px;fill:#5b6676}}.lab{{font-size:13px;fill:{MUTED}}}
.hot{{opacity:0;animation:ignite {loop}s linear infinite}}
@keyframes ignite{{0%{{opacity:0}}1%{{opacity:1}}{(loop-hold)/loop*100:.1f}%{{opacity:1}}{(loop-hold+0.01)/loop*100:.2f}%{{opacity:1}}99%{{opacity:1}}100%{{opacity:0}}}}
{css_text}
.st{{opacity:0;animation:cycle 16s infinite}}.s1{{animation-delay:4s}}.s2{{animation-delay:8s}}.s3{{animation-delay:12s}}
@keyframes cycle{{0%,22%{{opacity:1}}25%,97%{{opacity:0}}100%{{opacity:1}}}}
#clock{{transform-origin:960px 464px;transform:scaleX(0);animation:clock {loop}s linear infinite}}@keyframes clock{{0%{{transform:scaleX(0)}}{(loop-hold)/loop*100:.1f}%{{transform:scaleX(1)}}100%{{transform:scaleX(1)}}}}
@media (prefers-reduced-motion:reduce){{.hot,.st,#clock{{animation:none}}.hot{{opacity:1}}.s0{{opacity:1}}}}
</style>
<rect width="1600" height="500" fill="{BG}"/>
<g class="t">
<text x="80" y="120" class="h">Thermal runaway propagation</text><text x="80" y="178" class="h">in a 20-cell 4680 pack</text>
<text x="80" y="218" class="sub">COMSOL Multiphysics 6.4 · Battery Design Module · transient electro-thermal FEA</text>
{stats}
<text x="80" y="396" class="foot">Adapted from COMSOL's validated pack-propagation model · 46 × 80 mm cells · 25 Ah · 291,000 elements</text>
<text x="80" y="422" class="foot">Animation: ignition order from the reduced-order surrogate in this repository (k_tl = 1.0, h = 2,000),</text>
<text x="80" y="446" class="foot">not the COMSOL run · open the live page for the 3D pack and the COMSOL run matrix</text>
<text x="960" y="40" class="lab">Top view, 5s4p. Cell 1 (corner) forced at 1 min; neighbours trigger at 80 °C.</text>
</g>
<rect x="940" y="52" width="500" height="386" rx="18" fill="none" stroke="#1f2a3c"/>
{"".join(cells)}
<rect x="960" y="462" width="460" height="4" rx="2" fill="#1f2a3c"/><rect id="clock" x="960" y="462" width="460" height="4" rx="2" fill="#22d3ee"/>
<text x="960" y="452" class="t lab">simulated time, 0 to 60 min</text>
</svg>'''
    ASSETS.mkdir(parents=True, exist_ok=True)
    with open(ASSETS / "hero.svg", "w", encoding="utf-8") as f: f.write(svg)
    print("wrote", ASSETS / "hero.svg", (ASSETS / "hero.svg").stat().st_size, "bytes; surrogate ignition order (min):", [round(v, 1) if v is not None else None for v in ign])


if __name__ == "__main__":
    main()
