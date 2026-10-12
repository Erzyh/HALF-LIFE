"""Extended Data tables as images (Nature submits Extended Data tables as image files, not editable tables).

Renders the four tables from their data files at 300 dpi with wrapped cells: Extended Data Table 1 (census summary,
data/table1_census_summary.csv), 2 (modes of loss, data/loss_typology.csv), 3 (effort accounting,
data/effort_accounting.csv) and 4 (predictors of a successor deviation: a, data/p3_predictors_univariate.csv;
b, data/p3_predictors_model.csv, stacked into one image). No API calls.
Output: figures/ed_tables/ed_table{1..4}.png. Usage: python scripts/ed_tables.py
"""
import textwrap
from pathlib import Path

import matplotlib
import pandas as pd
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "ed_tables"
FONT, MIN_WIDTH_IN, CHAR_IN = 6.0, 7.2, 0.068   # inches per wrapped character at 6 pt (DejaVu Sans), with slack so nothing clips


def fmt(v):
    if pd.isna(v):
        return ""
    if isinstance(v, float):
        return f"{v:,.1f}" if abs(v) >= 1000 else (f"{v:g}" if v == int(v) else f"{v:.3g}" if abs(v) < 1 else f"{v:.1f}")
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def render(df, path, wrap=None, default=14):
    wrap = wrap or {}
    cols = list(df.columns)
    w = [wrap.get(c, default) for c in cols]
    cells = [["\n".join(textwrap.wrap(fmt(v), w[j])) or "" for j, v in enumerate(row)] for row in df.itertuples(index=False)]
    header = ["\n".join(textwrap.wrap(str(c).replace("_", " "), max(4, int(w[j] * 0.85)))) for j, c in enumerate(cols)]
    nl = [max(s.count("\n") + 1 for s in r) for r in cells]
    hl = max(s.count("\n") + 1 for s in header)
    line_h = FONT * 1.45 / 72
    height = (sum(nl) + hl) * line_h + 0.3
    width_in = max(MIN_WIDTH_IN, sum(w) * CHAR_IN)        # landscape when the wrapped columns need it; no text clips at a cell border
    fig, ax = plt.subplots(figsize=(width_in, height))
    ax.axis("off")
    tab = ax.table(cellText=cells, colLabels=header, loc="upper left", cellLoc="left", colLoc="left", bbox=[0, 0, 1, 1])
    tab.auto_set_font_size(False)
    tab.set_fontsize(FONT)
    tot = sum(w)
    for (r, c), cell in tab.get_celld().items():
        cell.set_width(w[c] / tot)
        cell.set_height((hl if r == 0 else nl[r - 1]) * line_h / height)
        cell.set_linewidth(0.3)
        cell.set_edgecolor("#999999")
        cell.PAD = 0.02
        if r == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#EFEFEF")
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t1 = pd.read_csv(ROOT / "data" / "table1_census_summary.csv", encoding="utf-8-sig")
    render(t1, OUT / "ed_table1.png", {"grouping": 22, "group": 22}, default=9)
    t2 = pd.read_csv(ROOT / "data" / "loss_typology.csv", encoding="utf-8-sig")
    render(t2, OUT / "ed_table2.png", {"mode": 24, "stage": 22, "note": 46, "item": 26, "count": 7, "denominator": 9, "share_pct": 7})
    t3 = pd.read_csv(ROOT / "data" / "effort_accounting.csv", encoding="utf-8-sig")
    render(t3, OUT / "ed_table3.png", {"stage": 28, "provider": 48}, default=9)
    ua = pd.read_csv(ROOT / "data" / "p3_predictors_univariate.csv", encoding="utf-8-sig")
    ub = pd.read_csv(ROOT / "data" / "p3_predictors_model.csv", encoding="utf-8-sig")
    pa = render(ua, OUT / "ed_table4a.png", {"covariate": 20, "level": 30}, default=10)
    pb = render(ub, OUT / "ed_table4b.png", {c: 30 for c in ub.columns[:1]}, default=12)
    a, b = Image.open(pa), Image.open(pb)
    wmax = max(a.width, b.width)
    im = Image.new("RGB", (wmax, a.height + b.height + 80), "white")
    im.paste(a, (0, 40))
    im.paste(b, (0, a.height + 80))
    im.save(OUT / "ed_table4.png", dpi=(300, 300))
    for p in sorted(OUT.glob("ed_table*.png")):
        print(p.relative_to(ROOT), Image.open(p).size)


if __name__ == "__main__":
    main()
