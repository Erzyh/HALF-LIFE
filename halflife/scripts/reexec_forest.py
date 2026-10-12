"""Forest plot of the re-executions: re-run minus reported value with 95% CI, Tier A claims and Tier B papers.

Panel (a): metrics on a 0-100 scale (accuracy, F1, ROUGE, rates, correlations x100): difference in points,
with bands at +-2 (class 재현) and +-5 (근접); classes are the three judges' majority. Panel (b): metrics on other scales (odds ratio,
t statistic, KL divergence, Likert sum, distance), shown as relative change so they share one axis; the raw
values are printed next to each point.
Inputs: runs/tierb/batch1_tierb_summary.json (Tier B) and data/tiera_claims.csv (Tier A, from scripts/tiera_claims.py).
Outputs: figures/reexec_forest.png, data/reexec_forest.csv. No API calls.
"""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLOR = {"재현": "#1baf7a", "근접": "#e0a500", "편차": "#d64541", "확인 필요": "#8a8f8c"}
EN = {"재현": "reproduced", "근접": "close", "편차": "deviated", "확인 필요": "could not be judged"}
OTHER_SCALE = {"W7161421448": "odds ratio", "W4415035710": "Welch t", "W7159577685": "Likert sum T+I+F",
               "W7134094238": "KL divergence", "W4404792825": "GSE total, 10-40",
               "W7117377764": "mean error, km"}
def tier_a_rows():
    """Tier A claims from data/tiera_claims.csv (written by scripts/tiera_claims.py from the run_meta files)."""
    rows = []
    for r in csv.DictReader(open(ROOT / "data" / "tiera_claims.csv", encoding="utf-8-sig")):
        ci = [float(r["ci_lo"]), float(r["ci_hi"])] if r["ci_lo"] else None
        j = r["judgment"]
        cls = "근접" if "부분" in j or "partial" in j else "재현" if ("생존" in j or "surviv" in j) else "편차" if ("사망" in j or "dead" in j) else "확인 필요"
        rows.append({"tier": "A", "id": r["wid"], "label": r["label"], "orig": float(r["original"]), "rerun": float(r["rerun"]),
                     "ci": ci, "class": cls, "rule": r["rule"]})
    return rows


def tier_b_rows():
    rows = []
    for r in json.load(open(ROOT / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8")):
        if r["orig"] is None or r["rerun"] is None:
            continue
        if r["wid"] in OTHER_SCALE:
            rule = "other:" + OTHER_SCALE[r["wid"]]
        else:
            rule = "x100" if abs(r["orig"]) <= 1.0 and -1.0 <= r["rerun"] <= 1.0 else "pts"
        metric = r["metric"] if r["metric"] != "custom" else "score"
        rows.append({"tier": "B", "id": r["wid"], "label": f"{r['title'][:38].rstrip()}: {metric}", "orig": r["orig"],
                     "rerun": r["rerun"], "ci": r["ci"] if r["ci"] and r["ci"][0] is not None else None,
                     "class": r["class"], "rule": rule})
    return rows


def main():
    rows = tier_a_rows() + tier_b_rows()
    pts, other = [], []
    for r in rows:
        if r["rule"].startswith("other:"):
            base = abs(r["orig"]) if r["orig"] else 1.0
            r["x"] = 100 * (r["rerun"] - r["orig"]) / base
            r["lo"], r["hi"] = ((100 * (r["ci"][0] - r["orig"]) / base, 100 * (r["ci"][1] - r["orig"]) / base) if r["ci"] else (None, None))
            r["unit"] = r["rule"].split(":", 1)[1]
            other.append(r)
        else:
            u = 100.0 if r["rule"] == "x100" else 1.0
            r["x"] = (r["rerun"] - r["orig"]) * u
            r["lo"], r["hi"] = (((r["ci"][0] - r["orig"]) * u, (r["ci"][1] - r["orig"]) * u) if r["ci"] else (None, None))
            r["unit"] = "points" if u == 1.0 else "points (x100)"
            pts.append(r)
    pts.sort(key=lambda r: r["x"])
    other.sort(key=lambda r: r["x"])
    with open(ROOT / "data" / "reexec_forest.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["panel", "tier", "id", "label", "original", "rerun", "ci_lo", "ci_hi", "unit", "difference", "diff_lo", "diff_hi", "class"])
        for panel, rs in (("a", pts), ("b", other)):
            for r in rs:
                w.writerow([panel, r["tier"], r["id"], r["label"], r["orig"], round(r["rerun"], 4),
                            r["ci"][0] if r["ci"] else "", r["ci"][1] if r["ci"] else "", r["unit"],
                            round(r["x"], 2), "" if r["lo"] is None else round(r["lo"], 2), "" if r["hi"] is None else round(r["hi"], 2), r["class"]])
    print(f"panel a {len(pts)} rows, panel b {len(other)} rows")
    print("panel a within +-2:", sum(abs(r["x"]) <= 2 for r in pts), " within +-5:", sum(abs(r["x"]) <= 5 for r in pts),
          " CI covers 0:", sum(r["lo"] is not None and r["lo"] <= 0 <= r["hi"] for r in pts), "of", sum(r["lo"] is not None for r in pts))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from figstyle import apply, panel, DARK
    apply()
    NCOL, ROW, FONT = 3, 0.085, 5.6                 # three columns of rows, so that the figure fits one page
    n, m = len(pts), len(other)
    per = -(-n // NCOL)
    chunks = [pts[i:i + per] for i in range(0, n, per)]
    LIM, LIM2 = 30.0, 150.0
    h_a, h_b = per * ROW + 0.5, max(m, 4) * 0.12 + 0.55
    fig = plt.figure(figsize=(7.2, h_a + h_b + 0.25), dpi=300)
    gs = fig.add_gridspec(2, NCOL, height_ratios=[h_a, h_b], left=0.155, right=0.995, top=0.99, bottom=0.05, wspace=0.78, hspace=0.16)
    axes = [fig.add_subplot(gs[0, j]) for j in range(NCOL)]

    def short(r):
        """Row label: 'A  claim' for Tier A, 'title: metric' for Tier B, cut to the column width."""
        if r["tier"] == "A":
            return "A  " + r["label"][:27].rstrip()
        title, _, metric = r["label"].rpartition(": ")
        return f"{title[:20].rstrip()}: {metric[:11]}"

    for ax, chunk in zip(axes, chunks):
        ax.axvspan(-5, 5, color="#e0a500", alpha=0.07, lw=0)
        ax.axvspan(-2, 2, color="#1baf7a", alpha=0.10, lw=0)
        ax.axvline(0, color=DARK, lw=0.7)
        for i, r in enumerate(chunk):
            y = per - i
            c = COLOR[r["class"]]
            x = max(-LIM, min(LIM, r["x"]))
            if r["lo"] is not None:
                ax.plot([max(-LIM, r["lo"]), min(LIM, r["hi"])], [y, y], color=c, lw=0.9, alpha=0.9)
            ax.plot([x], [y], marker="s" if r["tier"] == "A" else "o", ms=3.2 if r["tier"] == "A" else 2.8, color=c,
                    mec=DARK if r["tier"] == "A" else c, mew=0.5)
            if abs(r["x"]) > LIM:
                ax.annotate(f"{r['x']:+.0f}", (x, y), xytext=(-5 if r["x"] > 0 else 5, 0), textcoords="offset points",
                            ha="right" if r["x"] > 0 else "left", va="center", fontsize=5, color=c)
        ax.set_yticks([per - i for i in range(len(chunk))])
        ax.set_yticklabels([short(r) for r in chunk], fontsize=FONT)
        ax.tick_params(axis="y", length=0, pad=2)
        ax.set_ylim(0.4, per + 0.6)
        ax.set_xlim(-LIM, LIM)
        ax.set_xticks([-30, -15, 0, 15, 30])
        ax.tick_params(axis="x", labelsize=6.5)
    axes[1].set_xlabel("re-run minus reported value (points on the paper's 0-100 scale)", fontsize=7)
    handles = [Line2D([0], [0], marker="o", lw=0, color=COLOR[k], label=EN[k]) for k in ("재현", "근접", "편차", "확인 필요")]
    handles += [Line2D([0], [0], marker="s", lw=0, color="#ffffff", mec=DARK, label="Tier A claim"),
                Line2D([0], [0], marker="o", lw=0, color="#ffffff", mec=DARK, label="Tier B paper")]
    lax = fig.add_subplot(gs[1, 2])                     # legend in the empty bottom-right cell
    lax.axis("off")
    lax.legend(handles=handles, loc="center left", fontsize=6, frameon=False, handletextpad=0.5, borderaxespad=0)
    panel(axes[0], "a", x=-0.9)

    ax2 = fig.add_subplot(gs[1, 0:2])
    ax2.axvline(0, color=DARK, lw=0.7)
    for i, r in enumerate(other):
        y = m - i
        c = COLOR[r["class"]]
        x = max(-LIM2, min(LIM2, r["x"]))
        if r["lo"] is not None:
            ax2.plot([max(-LIM2, r["lo"]), min(LIM2, r["hi"])], [y, y], color=c, lw=0.9)
        ax2.plot([x], [y], marker="s" if r["tier"] == "A" else "o", ms=3.2, color=c, mec=DARK if r["tier"] == "A" else c, mew=0.5)
        txt = f"{r['orig']:g} -> {r['rerun']:.3g}" + (f"  [{r['ci'][0]:.3g}, {r['ci'][1]:.3g}]" if r["ci"] else "")
        ax2.text(LIM2 + 12, y, txt, ha="left", va="center", fontsize=5.2, color=DARK)
    ax2.text(LIM2 + 12, m + 0.75, "reported -> re-run [95% interval]", ha="left", va="bottom", fontsize=5.2, color=DARK)
    ax2.set_yticks([m - i for i in range(m)])
    ax2.set_yticklabels([("A  " if r["tier"] == "A" else "") + f"{r['label'][:24].rstrip()} ({r['unit']})" for r in other], fontsize=FONT)
    ax2.tick_params(axis="y", length=0, pad=2)
    ax2.set_ylim(0.4, m + 1.4)
    ax2.set_xlim(-LIM2, LIM2 + 240)
    ax2.set_xticks([-150, -100, -50, 0, 50, 100, 150])
    ax2.tick_params(axis="x", labelsize=6.5)
    ax2.set_xlabel("relative change (%)", fontsize=7)
    panel(ax2, "b", x=-0.36)
    (ROOT / "figures").mkdir(exist_ok=True)
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "reexec_forest.png", bbox_inches="tight", pad_inches=0.05)
    print("->", ROOT / "figures" / "reexec_forest.png")


if __name__ == "__main__":
    main()
