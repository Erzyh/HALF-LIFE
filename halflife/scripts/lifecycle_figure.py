"""Model lifecycle figure: release -> shutdown for the census model identifiers, by vendor (panel b of Fig. 1).

Release dates: taken from the date embedded in dated snapshot IDs where present; otherwise from the release field of
target_models.json (vendor page or launch announcement), or from RELEASE below for older entries. Shutdown dates come
from target_models.json. An undated alias that shares the shutdown date of a listed dated snapshot is not drawn twice.

Output: data/model_lifecycles.csv, figures/model_lifecycles.png (two columns: OpenAI; Anthropic and Google, one
identifier per row with the identifier as the row label) and a per-vendor lifespan summary. draw() is also used by
scripts/fig1_combine.py, which builds Fig. 1 with the trend panel above the lifespans.
"""
import csv, json, re, statistics
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 10, 12)
DEADLINES = {"2026-10-23": "OpenAI batch 1", "2026-11-30": "Anthropic", "2026-12-11": "OpenAI batch 2"}   # announced retirement dates marked; 2027-05-07 (gemini-3.1-flash-lite) lies beyond the axis
COLUMNS = (("openai",), ("anthropic", "google"))                                                       # left column, right column

# announcement dates for IDs without an embedded date (vendor release notes / model cards)
RELEASE = {
    "text-davinci-001": "2022-01-27", "text-curie-001": "2022-01-27", "text-davinci-002": "2022-03-15", "text-davinci-003": "2022-11-28",
    "gpt-3.5-turbo-0301": "2023-03-01", "gpt-3.5-turbo-0613": "2023-06-13", "gpt-3.5-turbo-16k": "2023-06-13",
    "gpt-4-0314": "2023-03-14", "gpt-4-0613": "2023-06-13", "gpt-4-32k": "2023-03-14",
    "gpt-4-1106-preview": "2023-11-06", "gpt-4-vision-preview": "2023-11-06", "gpt-4-1106-vision-preview": "2023-11-06",
    "gpt-4-0125-preview": "2024-01-25", "gpt-4-turbo": "2024-04-09", "gpt-4.5-preview": "2025-02-27", "chatgpt-4o-latest": "2024-08-14",
    "o1-preview": "2024-09-12", "o1-mini": "2024-09-12", "o1-pro": "2025-03-19", "o3-mini": "2025-01-31", "o4-mini": "2025-04-16",
    "o3-pro": "2025-06-10", "gpt-4.1-nano": "2025-04-14",
    "claude-1": "2023-03-14", "claude-instant-1.2": "2023-08-09", "claude-2": "2023-07-11", "claude-2.1": "2023-11-21",
    "claude-3-5-sonnet": "2024-06-20", "claude-3-haiku": "2024-03-13", "claude-3-5-haiku": "2024-10-22", "claude-3-7-sonnet": "2025-02-24",
    "text-bison": "2023-05-10", "gemini-1.0-pro": "2023-12-13", "gemini-1.5-pro": "2024-02-15", "gemini-1.5-flash": "2024-05-14",
    "gemini-1.5-flash-8b": "2024-10-03",
    # refresh of 2026-10-11
    "gpt-3.5-turbo-instruct": "2023-09-21", "gpt-3.5-turbo-1106": "2023-11-06",
    # refresh of 2026-10-02
    "gpt-3.5-turbo": "2023-03-01", "gpt-4o": "2024-05-13", "gpt-5-pro": "2025-10-06", "claude-sonnet-4-5": "2025-09-29",
    "gemini-2.0-flash": "2025-02-05", "gemini-2.0-flash-001": "2025-02-05", "gemini-2.0-flash-lite": "2025-02-25", "gemini-2.0-flash-lite-001": "2025-02-25",
    "gemini-2.5-pro-preview-03-25": "2025-03-25", "gemini-2.5-pro-preview-05-06": "2025-05-06", "gemini-2.5-pro-preview-06-05": "2025-06-05",
    "gemini-2.5-flash-preview-05-20": "2025-05-20", "gemini-2.5-flash-preview-09-25": "2025-09-25", "gemini-2.5-flash-lite-preview-09-2025": "2025-09-25",
    "gemini-3-pro-preview": "2025-11-18", "gemini-3.1-flash-lite-preview": "2026-03-03", "gemini-3.1-flash-lite": "2026-05-07",
}


def embedded_date(mid):
    m = re.search(r"(20\d\d)-?(\d\d)-?(\d\d)$", mid)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"-(\d\d)(\d\d)-preview$", mid) or re.search(r"-(\d\d)(\d\d)$", mid)   # 1106-preview, 0613
    if m and mid.startswith(("gpt-4", "gpt-3.5")):
        mm, dd = int(m.group(1)), int(m.group(2))
        yr = 2023 if not (mm == 1 and dd == 25) else 2024
        return date(yr, mm, dd)
    return None


def parse(d):
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?", str(d))
    if not m:
        return None
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 15))


def lifecycle_rows():
    """One row per drawn identifier; rewrites data/model_lifecycles.csv and prints the per-vendor lifespan summary."""
    models = json.load(open(ROOT / "target_models.json", encoding="utf-8"))["models"]
    ids = {m["id"] for m in models}
    rows = []
    for m in models:
        # undated alias of a listed dated snapshot with the same shutdown date: one bar is enough
        twins = [i for i in ids if i != m["id"] and i.startswith(m["id"] + "-") and embedded_date(i) is not None]
        if any(next(x for x in models if x["id"] == t).get("shutdown") == m.get("shutdown") for t in twins):
            continue
        rel = embedded_date(m["id"])
        src = "embedded in id"
        if rel is None and m.get("release"):
            rel, src = parse(m["release"]), "release field of target_models.json (vendor page or launch announcement)"
        elif rel is None and m["id"] in RELEASE:
            rel, src = parse(RELEASE[m["id"]]), "announcement (verify)"
        sd = parse(m.get("shutdown", ""))
        approx = "(" in str(m.get("shutdown", ""))
        if rel is None or sd is None:
            continue
        rows.append({"id": m["id"], "vendor": m["vendor"], "status": m["status"], "release": rel, "shutdown": sd,
                     "lifespan_days": (sd - rel).days, "release_source": src, "shutdown_approx": approx,
                     "dated_snapshot": src == "embedded in id"})
    with open(ROOT / "data" / "model_lifecycles.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("lifespan (days) by vendor, all ids:")
    for v in ("openai", "anthropic", "google"):
        ls = [r["lifespan_days"] for r in rows if r["vendor"] == v]
        print(f"  {v:10s} n={len(ls):2d} median {statistics.median(ls):5.0f} min {min(ls)} max {max(ls)}")
    print("dead only:")
    for v in ("openai", "anthropic", "google"):
        ls = [r["lifespan_days"] for r in rows if r["vendor"] == v and r["status"] == "dead"]
        if ls:
            print(f"  {v:10s} n={len(ls):2d} median {statistics.median(ls):5.0f}")
    return rows


def draw(axes, rows, font=5.8, date_labels=False):
    """Lifespan bars in the columns of COLUMNS (one axes each), one identifier per row with the identifier as the row
    label, rows aligned at the top of both columns. Returns the legend handles; the caller places the legend."""
    import matplotlib.dates as mdates
    from matplotlib.lines import Line2D
    from figstyle import VENDOR, GREY, DARK
    cols = []
    for vendors in COLUMNS:
        order = sorted([r for r in rows if r["vendor"] in vendors], key=lambda r: (vendors.index(r["vendor"]), r["release"]))
        ys, y, prev = [], 0, None
        for r in order:
            if prev is not None and r["vendor"] != prev:
                y += 1                                              # one empty row between vendors
            prev = r["vendor"]
            y += 1
            ys.append(y)
        cols.append((order, ys))
    nmax = max(ys[-1] for _, ys in cols)
    for ax, (order, ys) in zip(axes, cols):
        for r, y in zip(order, ys):
            yy = nmax - y + 1
            alive = r["status"] == "dying"
            c = VENDOR[r["vendor"]]
            ax.plot([r["release"], r["shutdown"]], [yy, yy], color=c, lw=1.8, alpha=0.95 if not alive else 0.5, solid_capstyle="butt")
            ax.plot([r["release"]], [yy], marker="|", color=c, ms=5, mew=1.0)
            ax.plot([r["shutdown"]], [yy], marker="x" if not alive else ">", color=c, ms=3.5 if not alive else 3.0, mew=0.9)
        ax.set_yticks([nmax - y + 1 for y in ys])
        ax.set_yticklabels([r["id"] + ("" if r["dated_snapshot"] else " *") for r in order], fontsize=font, color=DARK)
        ax.tick_params(axis="y", length=0, pad=2)
        ax.axvline(TODAY, color=GREY, lw=0.7, ls=(0, (3, 2)))
        for k, d in enumerate(DEADLINES):
            dd = parse(d)
            ax.axvline(dd, color="#A8781F", lw=0.7, ls=":")
            if date_labels:
                off = 0.6 if k % 2 == 0 else 3.6                     # neighbouring dates staggered so that their labels do not overlap
                ax.text(dd, nmax + off, d, ha="center", va="bottom", rotation=90, fontsize=font, color="#A8781F")
        if date_labels:
            ax.text(TODAY, nmax + 0.6, "today", ha="center", va="bottom", rotation=90, fontsize=font, color=GREY)
        ax.set_ylim(0.3, nmax + (7.5 if date_labels else 0.8))
        ax.set_xlim(date(2021, 9, 1), date(2027, 3, 1))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", labelsize=font + 0.6)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
    return ([Line2D([0], [0], color=VENDOR[v], lw=2.0, label=v) for v in VENDOR] +
            [Line2D([0], [0], color=GREY, marker="x", lw=0, label="shut down"),
             Line2D([0], [0], color=GREY, marker=">", lw=0, label="shutdown announced"),
             Line2D([0], [0], color="#A8781F", lw=0.8, ls=":", label="retirement dates: 23 Oct, 30 Nov, 11 Dec 2026"),
             Line2D([0], [0], color=GREY, lw=0.8, ls=(0, (3, 2)), label="12 Oct 2026, the analysis date"),
             Line2D([0], [0], color="white", lw=0, label="* release from the announcement (no dated snapshot)")])


def main():
    rows = lifecycle_rows()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from figstyle import apply
    apply()
    nmax = max(sum(r["vendor"] in v for r in rows) + len(v) - 1 for v in COLUMNS)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 0.1 * nmax + 1.3), dpi=300)
    handles = draw(axes, rows)
    fig.subplots_adjust(left=0.16, right=0.995, top=0.995, bottom=0.07, wspace=0.75)
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.17, 0.08), ncol=1, fontsize=5.6, frameon=False, handletextpad=0.5)
    (ROOT / "figures").mkdir(exist_ok=True)
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "model_lifecycles.png", bbox_inches="tight", pad_inches=0.05)
    print("->", ROOT / "figures" / "model_lifecycles.png")


if __name__ == "__main__":
    main()
