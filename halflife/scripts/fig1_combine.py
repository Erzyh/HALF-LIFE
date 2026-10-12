"""Fig. 1 of the manuscript as one matplotlib figure: the yearly trend (panel a: scripts/trend_counts.py,
data/trend_counts.csv) above the identifier lifespans in two columns (panel b: scripts/lifecycle_figure.py,
data/model_lifecycles.csv). The panel letters sit in the figure margin, outside the axes and their labels.
Replaces the PIL composition of 4 October 2026. No API calls.
Output: figures/fig1_combined.png. Usage: python scripts/fig1_combine.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from figstyle import apply, DARK  # noqa: E402
import lifecycle_figure  # noqa: E402
import trend_counts  # noqa: E402


def main():
    apply()
    counts = trend_counts.load()
    rows = lifecycle_figure.lifecycle_rows()
    nmax = max(sum(r["vendor"] in v for r in rows) + len(v) - 1 for v in lifecycle_figure.COLUMNS)
    h_a, h_b = 1.9, 0.1 * nmax + 0.9
    fig = plt.figure(figsize=(7.2, h_a + h_b + 0.5), dpi=300)
    gs = fig.add_gridspec(2, 2, height_ratios=[h_a, h_b], left=0.17, right=0.99, top=0.985, bottom=0.045, wspace=0.75, hspace=0.3)
    ax_a1, ax_a2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    ax_b = [fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
    trend_counts.draw(ax_a1, ax_a2, counts)
    handles = lifecycle_figure.draw(ax_b, rows)
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.18, 0.05), ncol=1, fontsize=5.6, frameon=False, handletextpad=0.5)
    for ax, letter in ((ax_a1, "a"), (ax_b[0], "b")):
        fig.text(0.01, ax.get_position().y1 + 0.004, letter, fontsize=9, fontweight="bold", ha="left", va="bottom", color=DARK)
    (ROOT / "figures").mkdir(exist_ok=True)
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "fig1_combined.png", bbox_inches="tight", pad_inches=0.05)
    print("figures/fig1_combined.png", tuple(round(v, 2) for v in fig.get_size_inches()), "in")


if __name__ == "__main__":
    main()
