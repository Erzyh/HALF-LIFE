"""Successor comparison without paper names: differences from the reported value grouped by task type (panel a) and by
field group (panel b), one point per paper and arm, with the median and its bootstrap 95% interval per category and arm.

Main-text alternative to scripts/p3_figure.py, whose rows name the papers. The per-paper detail stays in the
supplementary table (data/p3_summary.csv, identified by OpenAlex id) where it is needed for verification; the main
figure shows only the distribution. Inputs: data/p3_figure.csv (per-paper differences, points scale, panel a only),
data/tierb_triage/config_*.csv (task type) and group_*.csv (field group) through tierb_selection.load().
Output: figures/p3_successor_by_category.png, data/p3_figure_by_category.csv. No API calls.
"""
import csv, sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from tierb_selection import load                            # noqa: E402
from p3_figure import ARMS                                   # noqa: E402  (arm, label, colour, marker)

XMIN, XMAX = -60, 65
OFF = {"baseline": 0.30, "vendor": 0.15, "gpt41": 0.0, "open70b": -0.15, "gemini_flash": -0.30}
TASK_LABEL = {"classification": "classification", "mcq": "multiple choice", "generation": "generation",
              "extraction": "extraction", "other": "other / agentic", "agentic": "other / agentic"}
FIELD_LABEL = {"SOC": "social science", "LIFE": "life science", "MED": "medicine", "ENG": "engineering", "CS": "computer science"}
FIELD_ORDER = ["social science", "life science", "medicine", "engineering", "computer science", "unknown"]


def boot_median(vals, n=1000, seed=0):
    vals = np.asarray(vals, dtype=float)
    if len(vals) < 4:
        return None, None
    rng = np.random.default_rng(seed)
    meds = [np.median(rng.choice(vals, len(vals))) for _ in range(n)]
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def main():
    recs, grp, cfg, cen, summ = load()
    rows = [r for r in csv.DictReader(open(ROOT / "data" / "p3_figure.csv", encoding="utf-8-sig")) if r["panel"] == "a"]
    diffs = defaultdict(list)                                 # (dimension, category, arm) -> [difference]
    papers = defaultdict(set)
    for r in rows:
        w = r["wid"]
        t = TASK_LABEL.get((cfg.get(w, {}).get("task_type") or "other").lower(), "other / agentic")
        f = FIELD_LABEL.get(grp.get(w, {}).get("group") or "", grp.get(w, {}).get("group") or "unknown")
        for dim, cat in (("task type", t), ("field group", f)):
            diffs[(dim, cat, r["arm"])].append(float(r["difference"]))
            papers[(dim, cat)].add(w)
    cats = {"task type": sorted({c for (d, c) in papers if d == "task type"}, key=lambda c: -len(papers[("task type", c)])),
            "field group": sorted({c for (d, c) in papers if d == "field group"},
                                  key=lambda c: (FIELD_ORDER.index(c) if c in FIELD_ORDER else 99, -len(papers[("field group", c)])))}
    with open(ROOT / "data" / "p3_figure_by_category.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["dimension", "category", "arm", "n", "median_difference", "ci_lo", "ci_hi", "share_beyond_5", "unit"])
        for dim, cl in cats.items():
            for c in cl:
                for arm, _, _, _ in ARMS:
                    v = diffs.get((dim, c, arm), [])
                    if not v:
                        continue
                    lo, hi = boot_median(v)
                    w.writerow([dim, c, arm, len(v), round(float(np.median(v)), 2), "" if lo is None else round(lo, 2),
                                "" if hi is None else round(hi, 2), round(sum(abs(x) > 5 for x in v) / len(v), 3), "points"])

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    n_a, n_b = len(cats["task type"]), len(cats["field group"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 0.9 * max(n_a, n_b) + 2.2), dpi=300,
                             gridspec_kw={"width_ratios": [1, 1]}, sharex=True)
    rng = np.random.default_rng(1)
    from figstyle import panel
    for ax, dim, letter, title in ((axes[0], "task type", "a", "by task type"), (axes[1], "field group", "b", "by field group")):
        cl = cats[dim]
        for band, col in ((5, "#F2E6C8"), (2, "#CFE4D3")):
            ax.axvspan(-band, band, color=col, alpha=0.6, lw=0)
        ax.axvline(0, color="#1D2321", lw=0.8)
        for i, c in enumerate(cl):
            for arm, _, col, mk in ARMS:
                v = diffs.get((dim, c, arm), [])
                if not v:
                    continue
                y0 = i + OFF[arm]
                ys = y0 + rng.uniform(-0.05, 0.05, len(v))
                xs = np.clip(v, XMIN + 1.0, XMAX - 1.0)
                ax.plot(xs, ys, marker=mk, color=col, ms=2.6, lw=0, alpha=0.45, mec="none")
                lo, hi = boot_median(v)
                if lo is not None:
                    ax.plot([max(lo, XMIN), min(hi, XMAX)], [y0, y0], color=col, lw=3.2, alpha=0.85, solid_capstyle="butt")
                ax.plot(float(np.median(v)), y0, marker=mk, color=col, ms=6.0, lw=0, mec="#1D2321", mew=0.6)
            ax.axhline(i + 0.5, color="#DDDDDD", lw=0.5)
        ax.set_yticks(range(len(cl)))
        ax.set_yticklabels([f"{c} (n = {len(papers[(dim, c)])})" for c in cl], fontsize=8)
        ax.set_ylim(-0.6, len(cl) - 0.4)
        ax.invert_yaxis()
        ax.set_xlim(XMIN, XMAX)
        ax.set_title(title, fontsize=9.5, loc="left")
        panel(ax, letter, x=-0.3)
        ax.tick_params(axis="x", labelsize=7.5)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.supxlabel("difference from the reported value (points on the paper's 0-100 scale); faint marks are papers, "
                  "large marks the median, bars its bootstrap 95% interval (n >= 4)", fontsize=7.8, y=0.01)
    handles = [Line2D([0], [0], marker=mk, color=col, lw=0, ms=5.5, mec="#1D2321", mew=0.5, label=lab) for arm, lab, col, mk in ARMS]
    fig.legend(handles=handles, loc="upper center", ncol=3, fontsize=7.2, frameon=False, bbox_to_anchor=(0.5, 0.995))
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "p3_successor_by_category.png", bbox_inches="tight", pad_inches=0.05)
    print(f"task types {n_a}, field groups {n_b} -> figures/p3_successor_by_category.png, data/p3_figure_by_category.csv")


if __name__ == "__main__":
    main()
