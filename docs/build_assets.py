#!/usr/bin/env python3
"""Build every derived asset of the live page and run its QA.

  python docs/build_assets.py            # data export, static fallbacks for every 3D body scene, both-theme screenshots, Lighthouse
  python docs/build_assets.py --snap     # only the static PNG fallbacks (assets/viz_<scene>_<theme>.png, quantised)
  python docs/build_assets.py --qa       # only the screenshots and console check (docs/qa/light, docs/qa/dark)
  python docs/build_assets.py --lighthouse

The 3D body scenes render in the browser; their static fallbacks (shown under prefers-reduced-motion and without WebGL)
are the same scenes at full progress, captured headlessly in both themes by docs/tools/page-qa.mjs and quantised here to
keep the page under its size budget. Needs: pip install -r requirements.txt; a global playwright (npm i -g playwright &&
npx playwright install chromium) and, for the Lighthouse step, npm i -g lighthouse."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
EXPORT_CMDS: list[list[str]] = [["python", "-m", "analysis.export", "--no-sweep"], ["python", "-m", "analysis.plots"], ["python", "-m", "analysis.hero"]]   # repo-specific data export commands, run from ROOT
PAGES = ["index.html"]


def run(cmd, cwd=ROOT):
    print("$", " ".join(cmd)); subprocess.run(cmd, cwd=cwd, check=True)


def quantise(paths, colors=256, max_w=1400):
    from PIL import Image
    for p in paths:
        im = Image.open(p).convert("RGBA")
        if im.width > max_w: im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        bg = Image.new("RGBA", im.size, (0, 0, 0, 0)); bg.alpha_composite(im)
        q = bg.convert("RGB").quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
        q.save(p, optimize=True); print("quantised", p.name, p.stat().st_size, "bytes")


def qa_readme(report):
    lines = ["# QA for the live page", "", "Served from docs/ by docs/tools/page-qa.mjs, loaded in headless Chromium (software WebGL, so frame timing is not representative). Screenshots in both themes: the hero, the first two body scenes, the 375 px hero.", ""]
    for page, pr in report.get("pages", {}).items():
        lines += [f"## {page}", ""]
        if "lighthouse" in pr:
            lh = pr["lighthouse"]; lines += [f"Lighthouse (desktop preset): performance {lh['performance']}, accessibility {lh['accessibility']}, best practices {lh['bestPractices']}, SEO {lh['seo']}", "", "| Metric | Value |", "|---|---|", f"| First Contentful Paint | {lh['fcp']} |", f"| Largest Contentful Paint | {lh['lcp']} |", f"| Speed Index | {lh['si']} |", f"| Total Blocking Time | {lh['tbt']} |", f"| Cumulative Layout Shift | {lh['cls']} |", f"| Total byte weight | {lh['bytes']} |", ""]
        lines += ["| Theme | Console errors | Failed requests | Images loaded | Transfer (bytes) | Body scenes captured |", "|---|---|---|---|---|---|"]
        for theme in ("dark", "light"):
            t = pr.get(theme)
            if t: lines.append(f"| {theme} | {len(t['errors']) + len(t.get('mobileErrors', []))} | {len(t['failed'])} | {t['imagesLoaded']} | {t['transferBytes']:,} | {', '.join(t['scenes'])} |")
        lines.append("")
    lines += ["Files: `light/` and `dark/` hold `<page>-hero.png`, `<page>-scene1-*.png`, `<page>-scene2-*.png` and `<page>-mobile-375-hero.png`; `lighthouse.report.html` and `.json` are the Lighthouse run; `qa.json` is the machine-readable summary."]
    (DOCS / "qa" / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv):
    only = [a for a in argv if a.startswith("--")]
    do_all = not only
    if do_all:
        for c in EXPORT_CMDS: run(c)
    tool = [str(DOCS / "tools" / "page-qa.mjs"), "--docs", str(DOCS), "--pages", ",".join(PAGES)]
    if do_all or "--snap" in only:
        run(["node", *tool, "--snap"]); quantise(sorted((DOCS / "assets").glob("viz_*_*.png")))
    flags = [f for f in ("--qa", "--lighthouse") if do_all or f in only]
    if flags:
        run(["node", *tool, *flags])
        qa_readme(json.loads((DOCS / "qa" / "qa.json").read_text()))


if __name__ == "__main__":
    main(sys.argv[1:])
