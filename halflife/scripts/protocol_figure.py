"""Preservation protocol as a matrix: the loss modes observed in this study (rows, with the share observed at the
stage named in data/loss_typology.csv) against the protocol items that answer them (columns, grouped by the actor
who carries the item). A filled dot marks an item that addresses a mode; the bar on the right is the observed share.

Output: figures/protocol_map.png, data/protocol_map.csv. No API calls.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# mode number -> (row label, stage whose row of loss_typology.csv gives the headline number, denominator label)
MODES = [
    (1, "Identifier retired", "census", "papers in the survival curve"),
    (2, "Web interface only, no API snapshot", "Tier B triage, ineligible reasons", "ineligible papers"),
    (3, "Procedure under-reported", "Tier B triage, ineligible reasons", "ineligible papers"),
    (4, "Data gated or licence unclear", "Tier B triage, ineligible reasons", "ineligible papers"),
    (5, "Auxiliary model (judge) dependency", "Tier B executed papers", "executed papers"),
    (6, "Multi-stage or multimodal protocol", "Tier B configurations needing a human", "configurations needing a human"),
    (7, "Outcome measured on people", "Tier B triage, ineligible reasons", "ineligible papers"),
    (8, "Terms of service, account policy", "successor arms", "successor papers"),
    (9, "Change under a pinned identifier", "Tier B executed papers", "papers with a fingerprint"),
    (10, "Interface change on the successor", "third-party and open-weight arms", "third-party papers"),
    (11, "Hidden reasoning inside the output cap", "Gemini arm", "Gemini calls"),
    (12, "Format non-compliance, safety filter", "successor arms", "successor results"),
    (13, "Capability shift: the number moves", "successor arms", "successor results"),
]
# columns in display order, grouped by actor: (code, short header, actor, full description for the legend)
ITEMS = [
    ("P1", "Dated snapshot,\nfingerprint\ndistribution", "author", "the dated snapshot identifier and the distribution of served fingerprints reported with every result"),
    ("P3", "Prompts,\nparameters,\nitem identifiers", "author", "verbatim prompts, decoding parameters and item identifiers deposited"),
    ("P4", "Data or hashes;\nlicence stated", "author", "the items or their hashes deposited, with the data licence"),
    ("P6", "Three passes;\nsame-snapshot\nre-run", "author", "three or more passes per item; a same-snapshot re-run before the announced retirement"),
    ("P7", "Pipeline\ncontainer\nor trace", "author", "a container or execution trace for multi-stage and multimodal protocols"),
    ("P2", "Request and\nresponse logs\n(incl. judge)", "author + journal", "request and response logs deposited with the paper, including judge and auxiliary-model outputs"),
    ("P5", "Output cap,\nreasoning\ntokens recorded", "author + vendor", "the output allowance and the consumed reasoning tokens recorded per call, which needs the vendor to report them"),
    ("P8", "Dated\nmeasurements;\nweight escrow", "journal + vendor", "numbers treated as dated measurements; weight escrow or archival access after retirement"),
]
EDGES = {1: ["P1", "P2", "P8"], 2: ["P1", "P2"], 3: ["P3"], 4: ["P4"], 5: ["P2", "P1"], 6: ["P7"], 7: ["P2"], 8: ["P8"],
         9: ["P1", "P6"], 10: ["P2", "P3"], 11: ["P5"], 12: ["P2"], 13: ["P8", "P6"]}


def headline(rows, num, stage):
    for r in rows:
        if r["mode"].startswith(f"{num} ") and r["stage"] == stage:
            try:
                return int(float(r["count"])), int(float(r["denominator"])), float(r["share_pct"]) if r["share_pct"] != "" else None
            except ValueError:
                return None, None, None
    return None, None, None


def main():
    rows = list(csv.DictReader(open(ROOT / "data" / "loss_typology.csv", encoding="utf-8-sig")))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    import matplotlib.pyplot as plt
    INK, GREY, RULE = "#111111", "#6B6B6B", "#C9CDCB"
    ACTOR_COL = {"author": "#2D6FA3", "author + journal": "#3C8D5A", "author + vendor": "#8E5DAE", "journal + vendor": "#C8412B"}
    n_m, n_i = len(MODES), len(ITEMS)
    fig, ax = plt.subplots(figsize=(12.0, 8.4), dpi=300)
    ax.set_xlim(0, 108)
    ax.set_ylim(-14, 100)
    ax.axis("off")
    x_label, x0, dx = 1.0, 28.5, 7.0            # row labels; first dot column; column pitch
    x_bar0, bar_w = 82.5, 11.0                   # observed-share bar
    y_top, y_bot = 74.0, 6.0
    dy = (y_top - y_bot) / (n_m - 1)
    ys = {m[0]: y_top - k * dy for k, m in enumerate(MODES)}
    xcol = {it[0]: x0 + k * dx for k, it in enumerate(ITEMS)}
    # actor bands and column headers
    k = 0
    while k < n_i:
        actor = ITEMS[k][2]
        j = k
        while j + 1 < n_i and ITEMS[j + 1][2] == actor:
            j += 1
        xl, xr = xcol[ITEMS[k][0]] - dx / 2 + 0.4, xcol[ITEMS[j][0]] + dx / 2 - 0.4
        ax.plot([xl, xr], [95.0, 95.0], color=ACTOR_COL[actor], lw=1.6, solid_capstyle="butt")
        ax.text((xl + xr) / 2, 97.2, actor.replace(" + ", " +\n") if j == k else actor, ha="center", va="center", fontsize=6.3,
                color=ACTOR_COL[actor], linespacing=1.1)
        k = j + 1
    for code, text, actor, _ in ITEMS:
        ax.text(xcol[code], 92.6, code, ha="center", va="top", fontsize=7.4, fontweight="bold", color=INK)
        ax.text(xcol[code], 89.6, text, ha="center", va="top", fontsize=5.5, color=INK, linespacing=1.18)
    ax.text(x_bar0, 92.6, "Observed in this study", ha="left", va="top", fontsize=7.2, fontweight="bold", color=INK)
    ax.text(x_bar0, 89.6, "count / denominator (share);\ndenominators differ by row", ha="left", va="top", fontsize=5.7, color=GREY, linespacing=1.18)
    # rows
    out = []
    for num, label, stage, denom_label in MODES:
        y = ys[num]
        ax.plot([x_label, 107.0], [y - dy / 2, y - dy / 2], color=RULE, lw=0.4, zorder=1)
        ax.text(x_label, y + 0.9, f"{num}. {label}", ha="left", va="center", fontsize=7.0, color=INK)
        ax.text(x_label + 2.6, y - 1.5, denom_label, ha="left", va="center", fontsize=5.5, color=GREY)
        for code, _, actor, _ in ITEMS:
            if code in EDGES[num]:
                ax.plot(xcol[code], y, marker="o", ms=6.0, color=ACTOR_COL[actor], mec=ACTOR_COL[actor], lw=0, zorder=3)
            else:
                ax.plot(xcol[code], y, marker="o", ms=1.9, color="#DADEDC", lw=0, zorder=2)
        n, d, s = headline(rows, num, stage)
        if s is not None:
            ax.barh(y, bar_w * s / 100.0, left=x_bar0, height=dy * 0.42, color="#B8C4CE", ec="none", zorder=2)
            ax.text(x_bar0 + bar_w + 0.6, y, f"{n:,} / {d:,}  ({s:.0f}%)", ha="left", va="center", fontsize=5.8, color=INK)
        out.append({"mode": f"{num} {label}", "items": " ".join(EDGES[num]), "stage": stage, "count": n, "denominator": d, "share_pct": s})
    ax.plot([x_bar0, x_bar0], [y_bot - dy / 2, y_top + dy / 2], color=RULE, lw=0.5)
    ax.plot([x_bar0 + bar_w, x_bar0 + bar_w], [y_bot - dy / 2, y_top + dy / 2], color=RULE, lw=0.4, ls=(0, (2, 2)))
    ax.text(x_bar0 + bar_w, y_bot - dy / 2 - 1.4, "100%", ha="center", va="top", fontsize=5.5, color=GREY)
    ax.text(x_bar0, y_bot - dy / 2 - 1.4, "0", ha="center", va="top", fontsize=5.5, color=GREY)
    # legend: full item wording, two columns
    ax.text(x_label, -3.0, "Filled dot: the item addresses the mode. Items in full:", ha="left", va="top", fontsize=5.9, color=INK)
    half = (n_i + 1) // 2
    for idx, (code, _, actor, full) in enumerate(ITEMS):
        col, row = divmod(idx, half)
        ax.text(x_label + col * 54, -5.8 - row * 2.1, f"{code}  {full}", ha="left", va="top", fontsize=5.5, color=GREY)
    with open(ROOT / "data" / "protocol_map.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "protocol_map.png", bbox_inches="tight", pad_inches=0.08)
    print("-> figures/protocol_map.png, data/protocol_map.csv")


if __name__ == "__main__":
    main()
