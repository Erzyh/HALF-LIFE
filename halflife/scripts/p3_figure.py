"""Successor-model comparison figure (P3): for every Tier B paper run on a successor, the difference from the
paper's reported value for the pre-shutdown baseline (the paper's own model), the vendor-designated
replacement (gpt-5.6 family, default settings) and gpt-4.1 (GPT-4-class, non-reasoning).

Panel (a): metrics on a 0-100 scale, difference in points with bands at +-2 (재현) and +-5 (근접); differences
beyond the -60..+65 axis are drawn as arrowheads at the edge with the true value printed next to them.
Panel (b): metrics on other scales (odds ratio, divergence, Likert sums ...), relative change in percent.
Inputs: data/p3_summary.csv (scripts/p3_summary.py), runs/tierb/<wid>/result.json for the baseline interval,
the other-scale list of scripts/reexec_forest.py. Output: figures/p3_successor.png, data/p3_figure.csv. No API calls.
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from p3_summary import NOT_TRANSFERABLE, scaled, unit_of   # noqa: E402
from reexec_forest import OTHER_SCALE                        # noqa: E402

ARMS = [("baseline", "pre-shutdown baseline (paper's model)", "#7A847F", "s"),
        ("vendor", "vendor-designated replacement (gpt-5.6)", "#C8412B", "o"),
        ("gpt41", "gpt-4.1-2025-04-14", "#2D6FA3", "^"),
        ("open70b", "open-weight Llama 3.3 70B", "#3C8D5A", "s"),
        ("gemini_flash", "Gemini 3.8 Flash (other vendor)", "#8E5DAE", "D")]


def diff(orig, val, lo, hi, other):
    """Difference from the reported value: points (fractions x100) or, for other scales, percent of the original."""
    if val is None:
        return None, None, None
    if other:
        base = abs(orig) if orig else 1.0
        f = lambda v: 100.0 * (v - orig) / base
    else:
        u = unit_of(orig, val)
        f = lambda v: (v - orig) * u
    return f(val), (f(lo) if lo is not None else None), (f(hi) if hi is not None else None)


def main():
    rows = list(csv.DictReader(open(ROOT / "data" / "p3_summary.csv", encoding="utf-8-sig")))
    papers = {}
    for r in rows:
        if r["wid"] in NOT_TRANSFERABLE:
            continue
        p = papers.setdefault(r["wid"], {"title": r["title"], "metric": r["metric"], "orig": float(r["original"]), "arms": {}})
        if r["class_vs_original"] == "확인 필요":          # unscorable on this arm (format non-compliance): no point drawn
            continue
        val = float(r["arm_value"]) if r["arm_value"] else None
        lo = float(r["ci_lo"]) if r["ci_lo"] else None
        hi = float(r["ci_hi"]) if r["ci_hi"] else None
        p["arms"][r["arm"]] = (val, lo, hi)
    for wid, p in papers.items():
        bp = ROOT / "runs" / "tierb" / wid / "result.json"
        b = scaled(json.loads(bp.read_text(encoding="utf-8"))) if bp.exists() else None   # baseline being re-run: no baseline point yet
        p["arms"]["baseline"] = b if b else (None, None, None)
        p["other"] = wid in OTHER_SCALE
        p["unit"] = OTHER_SCALE.get(wid, "")
        for arm, (val, lo, hi) in p["arms"].items():
            p[arm] = diff(p["orig"], val, lo, hi, p["other"])
    pts = sorted([(w, p) for w, p in papers.items() if not p["other"]], key=lambda kv: kv[1]["vendor"][0] if kv[1].get("vendor") and kv[1]["vendor"][0] is not None else 0)
    other = sorted([(w, p) for w, p in papers.items() if p["other"]], key=lambda kv: kv[1]["vendor"][0] if kv[1].get("vendor") and kv[1]["vendor"][0] is not None else 0)
    with open(ROOT / "data" / "p3_figure.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["panel", "wid", "title", "metric", "original", "arm", "difference", "diff_lo", "diff_hi", "unit"])
        for panel, rs in (("a", pts), ("b", other)):
            for wid, p in rs:
                for arm, _, _, _ in ARMS:
                    if arm in p and p[arm][0] is not None:
                        w.writerow([panel, wid, p["title"], p["metric"], p["orig"], arm, round(p[arm][0], 3),
                                    "" if p[arm][1] is None else round(p[arm][1], 3), "" if p[arm][2] is None else round(p[arm][2], 3),
                                    "percent of original" if p["other"] else "points"])
    print(f"panel a {len(pts)} papers, panel b {len(other)} papers")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from figstyle import apply, panel, DARK
    apply()
    NCOL, ROW, FONT = 3, 0.2, 5.6                   # three columns of rows (five marks per row), so that the figure fits one page
    n, m = len(pts), max(len(other), 1)
    per = -(-n // NCOL)
    chunks = [pts[i:i + per] for i in range(0, n, per)]
    off = {"baseline": 0.28, "vendor": 0.14, "gpt41": 0.0, "open70b": -0.14, "gemini_flash": -0.28}
    XMIN, XMAX = -60, 65
    XMIN2, XMAX2 = -140, 160                        # relative change (%); the km-error outlier sits at +970
    h_a, h_b = per * ROW + 0.5, m * 0.24 + 0.6
    fig = plt.figure(figsize=(7.2, h_a + h_b + 0.25), dpi=300)
    gs = fig.add_gridspec(2, NCOL, height_ratios=[h_a, h_b], left=0.155, right=0.995, top=0.99, bottom=0.05, wspace=0.78, hspace=0.18)
    axes = [fig.add_subplot(gs[0, j]) for j in range(NCOL)]

    def draw(axis, rows, top, xmin, xmax, fmt):
        """Points with intervals, the first row at the top; a difference beyond [xmin, xmax] becomes an arrowhead at the edge with its value."""
        for i, (wid, p) in enumerate(rows):
            for arm, _, col, mk in ARMS:
                if arm not in p or p[arm][0] is None:
                    continue
                x, lo, hi = p[arm]
                y = top - 1 - i + off[arm]
                if lo is not None and hi is not None:
                    axis.plot([max(lo, xmin), min(hi, xmax)], [y, y], color=col, lw=0.7, alpha=0.8)
                if x < xmin or x > xmax:
                    left = x < xmin
                    edge = xmin + 0.01 * (xmax - xmin) if left else xmax - 0.01 * (xmax - xmin)
                    axis.plot(edge, y, marker="<" if left else ">", color=col, ms=4.0, lw=0, mec=DARK, mew=0.4)
                    axis.annotate(fmt(x), (edge, y), xytext=(4 if left else -4, 0), textcoords="offset points",
                                  ha="left" if left else "right", va="center", fontsize=4.8, color=DARK)
                    continue
                axis.plot(x, y, marker=mk, color=col, ms=3.2, lw=0, mec=DARK if arm != "baseline" else col, mew=0.4)

    def label(p, width=20):
        metric = p["metric"] if p["metric"] != "custom" else "score"
        return f"{p['title'][:width].rstrip()}: {metric[:11]}"

    for ax, chunk in zip(axes, chunks):
        for band, col in ((5, "#F2E6C8"), (2, "#CFE4D3")):
            ax.axvspan(-band, band, color=col, alpha=0.6, lw=0)
        ax.axvline(0, color=DARK, lw=0.7)
        draw(ax, chunk, per, XMIN, XMAX, lambda v: f"{v:+.0f}")
        ax.set_yticks([per - 1 - i for i in range(len(chunk))])
        ax.set_yticklabels([label(p) for _, p in chunk], fontsize=FONT)
        ax.tick_params(axis="y", length=0, pad=2)
        ax.set_ylim(-0.6, per - 0.4)
        ax.set_xlim(XMIN, XMAX)                     # the two planning papers sit at +59.9; points beyond are drawn at the edge
        ax.set_xticks([-60, -30, 0, 30, 60])
        ax.tick_params(axis="x", labelsize=6.5)
    axes[1].set_xlabel("difference from the reported value (points on the paper's 0-100 scale)", fontsize=7)
    panel(axes[0], "a", x=-0.9)

    ax2 = fig.add_subplot(gs[1, 0:2])
    ax2.axvline(0, color=DARK, lw=0.7)
    draw(ax2, other, len(other), XMIN2, XMAX2, lambda v: f"{v:+.0f}%")
    ax2.set_yticks([len(other) - 1 - i for i in range(len(other))])
    ax2.set_yticklabels([f"{p['title'][:24].rstrip()} ({p['unit']})" for _, p in other], fontsize=FONT)
    ax2.tick_params(axis="y", length=0, pad=2)
    ax2.set_ylim(-0.6, len(other) - 0.4)
    ax2.set_xlim(XMIN2, XMAX2)
    ax2.set_xlabel("relative change (%)", fontsize=7)
    ax2.tick_params(axis="x", labelsize=6.5)
    panel(ax2, "b", x=-0.36)
    present = {"baseline"} | {arm for p in papers.values() for arm in p if arm in {a for a, _, _, _ in ARMS} and p.get(arm)}
    handles = [Line2D([0], [0], marker=mk, color=col, lw=0, ms=5, label=lab) for arm, lab, col, mk in ARMS if arm in present]
    lax = fig.add_subplot(gs[1, 2])
    lax.axis("off")
    lax.legend(handles=handles, loc="center left", fontsize=6, frameon=False, handletextpad=0.5, borderaxespad=0)
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "p3_successor.png", bbox_inches="tight", pad_inches=0.05)
    print("->", ROOT / "figures" / "p3_successor.png")


if __name__ == "__main__":
    main()
