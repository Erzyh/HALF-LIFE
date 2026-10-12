"""Pre-shutdown re-execution without paper names: the difference between the re-run and the reported value grouped by
task type (Tier B papers; Tier A claims as one row) and by OpenAlex field (both tiers), one faint mark per claim or
paper coloured by its judged class, with the median and its bootstrap 95% interval per row.

Main-text alternative to scripts/reexec_forest.py, whose rows name the papers; the per-paper forest with identifiers
stays in the supplement. Inputs: data/reexec_forest.csv (panel a, points scale), the triage tables for Tier B task
types, data/census_v2.csv for the OpenAlex field of every paper. Output: figures/reexec_forest_by_category.png,
data/reexec_forest_by_category.csv. No API calls.
"""
import csv, sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from tierb_selection import load                              # noqa: E402
from reexec_forest import COLOR, EN                           # noqa: E402

XMIN, XMAX = -30, 30
TASK = {"classification": "classification", "mcq": "multiple choice", "generation": "generation", "extraction": "extraction",
        "other": "other / agentic", "agentic": "other / agentic"}
FIELD_MAP = {"Computer Science": "computer science", "Engineering": "engineering", "Mathematics": "engineering", "Physics and Astronomy": "engineering",
             "Materials Science": "engineering", "Medicine": "medicine", "Health Professions": "medicine", "Nursing": "medicine", "Dentistry": "medicine",
             "Social Sciences": "social science", "Psychology": "social science", "Economics, Econometrics and Finance": "social science",
             "Business, Management and Accounting": "social science", "Decision Sciences": "social science", "Arts and Humanities": "social science",
             "Biochemistry, Genetics and Molecular Biology": "life science", "Agricultural and Biological Sciences": "life science",
             "Neuroscience": "life science", "Immunology and Microbiology": "life science", "Environmental Science": "life science",
             "Pharmacology, Toxicology and Pharmaceutics": "life science", "Earth and Planetary Sciences": "life science", "Chemistry": "life science",
             "Chemical Engineering": "engineering", "Energy": "engineering", "Veterinary": "life science"}
FIELD_ORDER = ["computer science", "social science", "medicine", "life science", "engineering", "other"]


def boot_median(vals, n=1000, seed=0):
    vals = np.asarray(vals, dtype=float)
    if len(vals) < 4:
        return None, None
    rng = np.random.default_rng(seed)
    meds = [np.median(rng.choice(vals, len(vals))) for _ in range(n)]
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def main():
    recs, grp, cfg, cen, summ = load()
    rows = [r for r in csv.DictReader(open(ROOT / "data" / "reexec_forest.csv", encoding="utf-8-sig")) if r["panel"] == "a"]
    groups = defaultdict(list)          # (dimension, category) -> [(difference, class, tier)]
    seen_fields = defaultdict(int)
    for r in rows:
        w, tier, d, c = r["id"], r["tier"], float(r["difference"]), r["class"]
        if tier == "B":
            t = TASK.get((cfg.get(w, {}).get("task_type") or "other").lower(), "other / agentic")
            groups[("task type (Tier B papers)", t)].append((d, c, tier))
        else:
            groups[("task type (Tier B papers)", "Tier A claims, all repository-based re-runs")].append((d, c, tier))
        f_raw = (cen.get(w, {}) or {}).get("field") or ""
        f = FIELD_MAP.get(f_raw, "other")
        seen_fields[f_raw] += 1
        groups[("OpenAlex field (both tiers)", f)].append((d, c, tier))
    print("census fields seen:", dict(seen_fields))
    dims = ["task type (Tier B papers)", "OpenAlex field (both tiers)"]
    order = {dims[0]: sorted({c for (d, c) in groups if d == dims[0]},
                             key=lambda c: (c.startswith("Tier A"), -len(groups[(dims[0], c)]))),
             dims[1]: sorted({c for (d, c) in groups if d == dims[1]}, key=lambda c: FIELD_ORDER.index(c) if c in FIELD_ORDER else 99)}
    with open(ROOT / "data" / "reexec_forest_by_category.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["dimension", "category", "n", "reproduced", "close", "deviated", "needs_review", "median_difference", "ci_lo", "ci_hi", "share_within_5_pts"])
        for dim in dims:
            for c in order[dim]:
                v = groups[(dim, c)]
                diffs = [x[0] for x in v]
                lo, hi = boot_median(diffs)
                cls = [x[1] for x in v]
                w.writerow([dim, c, len(v), cls.count("재현"), cls.count("근접"), cls.count("편차"), cls.count("확인 필요"),
                            round(float(np.median(diffs)), 2), "" if lo is None else round(lo, 2), "" if hi is None else round(hi, 2),
                            round(sum(abs(x) <= 5 for x in diffs) / len(diffs), 3)])

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    n_rows = max(len(order[d]) for d in dims)
    fig, axes = plt.subplots(1, 2, figsize=(11, 0.75 * n_rows + 2.0), dpi=300, sharex=True)
    rng = np.random.default_rng(3)
    from figstyle import panel
    for ax, dim, letter, title in zip(axes, dims, "ab", ("by task type", "by OpenAlex field")):
        cl = order[dim]
        for band, col in ((5, "#F2E6C8"), (2, "#CFE4D3")):
            ax.axvspan(-band, band, color=col, alpha=0.6, lw=0)
        ax.axvline(0, color="#1D2321", lw=0.8)
        for i, c in enumerate(cl):
            v = groups[(dim, c)]
            diffs = np.array([x[0] for x in v])
            ys = i + rng.uniform(-0.22, 0.22, len(v))
            for (d, k, tier), y in zip(v, ys):
                x = min(max(d, XMIN + 0.8), XMAX - 0.8)
                mk = "^" if tier == "A" else "s"
                off = d < XMIN or d > XMAX
                ax.plot(x, y, marker=("<" if d < XMIN else ">") if off else mk, color=COLOR.get(k, "#8a8f8c"), ms=3.4 if off else 2.8,
                        lw=0, alpha=0.55, mec="none")
            lo, hi = boot_median(diffs)
            if lo is not None:
                ax.plot([max(lo, XMIN), min(hi, XMAX)], [i, i], color="#1D2321", lw=3.0, alpha=0.8, solid_capstyle="butt")
            ax.plot(float(np.median(diffs)), i, marker="o", color="white", ms=6.5, lw=0, mec="#1D2321", mew=1.2)
            ax.axhline(i + 0.5, color="#DDDDDD", lw=0.5)
        ax.set_yticks(range(len(cl)))
        ax.set_yticklabels([f"{c}\n(n = {len(groups[(dim, c)])}, reproduced {100 * sum(1 for x in groups[(dim, c)] if x[1] == '재현') / len(groups[(dim, c)]):.0f}%)" for c in cl], fontsize=7.6)
        ax.set_ylim(-0.6, len(cl) - 0.4)
        ax.invert_yaxis()
        ax.set_xlim(XMIN, XMAX)
        ax.set_title(title, fontsize=9.5, loc="left")
        panel(ax, letter, x=-0.36)
        ax.tick_params(axis="x", labelsize=7.5)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.supxlabel("re-run minus reported value (points on the paper's 0-100 scale); marks are claims (triangles, Tier A) or papers (squares, Tier B), "
                  "arrowheads sit beyond the axis; white dot = median, bar = bootstrap 95% interval", fontsize=7.4, y=0.01)
    handles = [Line2D([0], [0], marker="s", color=COLOR[k], lw=0, ms=5.5, label=EN[k]) for k in ("재현", "근접", "편차", "확인 필요")]
    handles += [Line2D([0], [0], marker="^", color="#7A847F", lw=0, ms=5.5, label="Tier A claim"), Line2D([0], [0], marker="s", color="#7A847F", lw=0, ms=5.5, label="Tier B paper")]
    fig.legend(handles=handles, loc="upper center", ncol=6, fontsize=7.2, frameon=False, bbox_to_anchor=(0.5, 0.995))
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "reexec_forest_by_category.png", bbox_inches="tight", pad_inches=0.05)
    print(f"rows: {len(order[dims[0]])} task-type rows, {len(order[dims[1]])} field rows -> figures/reexec_forest_by_category.png")


if __name__ == "__main__":
    main()
