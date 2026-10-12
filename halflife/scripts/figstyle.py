"""One matplotlib style for every figure of the paper: Arial, small type, hairline axes, a muted palette, no frames.

Import and call apply() before creating a figure. Widths follow the journal's columns: 3.5 in (one column) or
7.2 in (two columns); heights are chosen per figure.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from cycler import cycler  # noqa: E402

DARK = "#1D2321"
GREY = "#8a8f8d"
LIGHT = "#dfe6ee"
BLUE = "#1f5fa6"
BLUE_LIGHT = "#9fbbdc"
ORANGE = "#c2571a"
GREEN = "#2b7a4b"
PURPLE = "#7b4fa3"
RED = "#b5432e"
GOLD = "#a67c00"
VENDOR = {"openai": BLUE, "anthropic": ORANGE, "google": GREEN}
SERIES = [BLUE, ORANGE, GREEN, PURPLE, GOLD, "#5a6b7b"]


def apply():
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.8, "legend.frameon": False,
        "legend.handlelength": 1.6, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "axes.spines.top": False, "axes.spines.right": False,
        "lines.linewidth": 1.0, "axes.titlelocation": "left", "axes.titleweight": "normal",
        "figure.dpi": 200, "savefig.dpi": 300, "axes.prop_cycle": cycler(color=SERIES),   # 300 dpi: Nature's minimum for raster figures (raised from 200 on 4 October 2026)
    })


def panel(ax, letter, x=-0.02, y=1.04):
    """Bold panel letter at the top-left corner of the axes, outside the plotting area."""
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=9, fontweight="bold", ha="right", va="bottom", color=DARK)
