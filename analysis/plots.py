"""Figures for the README and the live page, every one generated from results/matrix.json, analysis.scaling and the lumped
surrogate's saved sweep (results/lumped_sweep.json). Writes docs/assets/fig_*_{dark,light}.svg."""
from __future__ import annotations
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from . import ASSETS, ROOT
from . import matrix as mx, scaling as sc

THEMES = {"dark": ("#e6edf3", "#8b98a9", "#0b1220"), "light": ("#0b1220", "#5b6676", "#ffffff")}
CASCADE, ARREST, INFER = "#f97316", "#22d3ee", "#a78bfa"


def _style(ax, ink, muted):
    ax.set_facecolor("none")
    for s in ax.spines.values(): s.set_color(muted); s.set_linewidth(.8)
    ax.tick_params(colors=ink, labelsize=9); ax.xaxis.label.set_color(ink); ax.yaxis.label.set_color(ink); ax.title.set_color(ink)


def _save(fig, name, theme):
    os.makedirs(ASSETS, exist_ok=True); path = ASSETS / f"{name}_{theme}.svg"
    fig.savefig(path, transparent=True, bbox_inches="tight"); plt.close(fig); return path


def phase_map(m, theme, lumped=None):
    ink, muted, bg = THEMES[theme]; ks = m["k_tl_values_W_mK"]; hs = m["h_plate_values_W_m2K"]; g = mx.grid(m)
    fig, ax = plt.subplots(figsize=(6.6, 4.2)); _style(ax, ink, muted)
    for i, h in enumerate(hs):
        for j, k in enumerate(ks):
            r = g[h][k]
            if r is None:
                ax.add_patch(Rectangle((j, i), 1, 1, facecolor="none", edgecolor=muted, lw=.6, ls=":")); ax.text(j + .5, i + .5, "not run", ha="center", va="center", fontsize=7.5, color=muted); continue
            col = INFER if r["status"] == "inferred" else (CASCADE if r["outcome"] == "cascade" else ARREST)
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=col, alpha=.85 if r["status"] == "run" else .45, edgecolor=bg, lw=2, hatch="//" if r["status"] == "inferred" else None))
            lab = "cascade\n(inferred)" if r["status"] == "inferred" else ("cascade\n2nd @ %g min" % r["second_ignition_min"] if r["outcome"] == "cascade" else "arrested\nat cell 1")
            ax.text(j + .5, i + .5, lab, ha="center", va="center", fontsize=8, color="#0b1220" if r["status"] == "run" else ink, fontweight="bold")
    ax.set_xlim(0, len(ks)); ax.set_ylim(0, len(hs)); ax.set_xticks(np.arange(len(ks)) + .5); ax.set_xticklabels([f"{k:g}" for k in ks]); ax.set_yticks(np.arange(len(hs)) + .5); ax.set_yticklabels([str(h) for h in hs])
    ax.set_xlabel("Through-layer (radial) conductivity k_tl, W/m·K"); ax.set_ylabel("Base cooling h_plate, W/m²·K")
    ax.axvline(1, color=ink, lw=1.2, ls="--"); ax.text(1.02, len(hs) - .08, "threshold 1.0–1.25", fontsize=8, color=ink, va="top")
    ax.set_title("COMSOL run matrix: 20-cell 4680 pack, 110 kJ per cell, 80 °C trigger, 60 min", fontsize=9)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(length=0); return _save(fig, "fig_phase_map", theme)


def energy_balance(theme):
    ink, muted, bg = THEMES[theme]
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.6)); [_style(a, ink, muted) for a in axs]
    ax = axs[0]; W = np.linspace(20e3, 200e3, 50); m = sc.cell_mass()
    ax.plot(W / 1e3, sc.T_AMBIENT_C + W / (m * sc.CP), color=CASCADE, lw=2, label=f"adiabatic peak, m = {m:.3f} kg, cp = {sc.CP:.0f}")
    ax.axhspan(280, 340, color=muted, alpha=.18, lw=0); ax.text(22, 342, "280–340 °C peaks seen in the runs", fontsize=8, color=muted)
    ax.axvline(110, color=ink, lw=1, ls="--"); ax.plot([110], [sc.T_AMBIENT_C + sc.adiabatic_temperature_rise()], "o", color=ink, ms=5)
    ax.annotate(f"110 kJ → {sc.T_AMBIENT_C + sc.adiabatic_temperature_rise():.0f} °C", (110, sc.T_AMBIENT_C + sc.adiabatic_temperature_rise()), (118, 220), fontsize=8.5, color=ink, arrowprops=dict(arrowstyle="-", color=ink, lw=.7))
    ax.set_xlabel("Runaway energy per cell W_tr, kJ"); ax.set_ylabel("Uniform-cell peak temperature, °C"); ax.legend(fontsize=7.5, frameon=False, labelcolor=ink, loc="lower right"); ax.set_title("ΔT = W / (m·cp): energy spread over the whole homogenised cell", fontsize=8.5)
    ax = axs[1]
    labels = ["4680 radial\nR = 23 mm, k = 1", "2170 radial\nR = 10.5 mm, k = 1", "4680 axial\nH/2 = 40 mm, k = 30"]
    taus = [sc.diffusion_time(sc.R_4680, 1.0), sc.diffusion_time(sc.R_2170, 1.0), sc.diffusion_time(sc.H_4680 / 2, 30.0)]
    bars = ax.bar(labels, [t / 60 for t in taus], color=[CASCADE, ARREST, INFER], width=.6)
    for b, t in zip(bars, taus): ax.text(b.get_x() + b.get_width() / 2, b.get_height() + .4, f"{t:,.0f} s\n≈ {t/60:.1f} min", ha="center", fontsize=8, color=ink)
    ax.set_ylabel("Diffusion time L² / α, min"); ax.set_ylim(0, 31); ax.set_title("Radius squared: a 4680 sheds heat radially ~5× slower than a 2170", fontsize=8.5); ax.tick_params(axis="x", labelsize=8)
    fig.tight_layout(); return _save(fig, "fig_energy_balance", theme)


def lumped_figs(theme, sweep_path=ROOT / "results" / "lumped_sweep.json"):
    if not os.path.exists(sweep_path): return []
    ink, muted, bg = THEMES[theme]; S = json.load(open(sweep_path)); out = []
    ks = S["k_values"]; hs = S["h_values"]
    fig, ax = plt.subplots(figsize=(6.6, 4.0)); _style(ax, ink, muted)
    for i, h in enumerate(hs):
        for j, k in enumerate(ks):
            r = next(x for x in S["sweep"] if x["h_plate"] == h and x["k_tl"] == k)
            col = CASCADE if r["cascade"] else ARREST
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=col, alpha=.85, edgecolor=bg, lw=2))
            lab = f"{r['n_ignited']}/20 cells\n2nd @ {r['second_ignition_min']:g} min" if r["cascade"] else "arrested"
            ax.text(j + .5, i + .5, lab, ha="center", va="center", fontsize=7.5, color="#0b1220", fontweight="bold")
    ax.set_xlim(0, len(ks)); ax.set_ylim(0, len(hs)); ax.set_xticks(np.arange(len(ks)) + .5); ax.set_xticklabels([f"{k:g}" for k in ks]); ax.set_yticks(np.arange(len(hs)) + .5); ax.set_yticklabels([str(h) for h in hs])
    ax.set_xlabel("Through-layer conductivity k_tl, W/m·K"); ax.set_ylabel("Base cooling h_plate, W/m²·K")
    ax.set_title(f"Reduced-order model (built here): coupling scale {S['coupling_scale']:g}", fontsize=9)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(length=0); out.append(_save(fig, "fig_lumped_phase", theme))
    fig, ax = plt.subplots(figsize=(6.6, 3.8)); _style(ax, ink, muted)
    for key, col, lab in ((S["trace_cascade"], CASCADE, "cascade case"), (S["trace_arrest"], ARREST, "arrested case")):
        tr = S["traces"][key]; t = np.array(tr["t_min"]); T = np.array(tr["cell_max_C"])
        for c in range(T.shape[1]): ax.plot(t, T[:, c], color=col, lw=.9, alpha=.75, label=f"{lab}: {key.replace('_', ' ')}" if c == 0 else None)
    ax.axhline(80, color=ink, lw=1, ls="--"); ax.text(1, 84, "80 °C trigger", fontsize=8, color=ink)
    ax.set_xlabel("Time, min"); ax.set_ylabel("Cell maximum temperature, °C"); ax.legend(fontsize=8, frameon=False, labelcolor=ink); ax.set_title("Reduced-order model: per-cell maximum temperature, 20 cells", fontsize=9)
    out.append(_save(fig, "fig_lumped_traces", theme)); return out


def main():
    m = mx.load()
    for theme in THEMES:
        print(phase_map(m, theme)); print(energy_balance(theme)); [print(p) for p in lumped_figs(theme)]


if __name__ == "__main__":
    main()
