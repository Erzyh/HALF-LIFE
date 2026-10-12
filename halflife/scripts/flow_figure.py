"""Flow of papers through the study (PRISMA-style), drawn from the counts recorded in SPRINT.md and the data files.

Three columns: census and manual coding; Tier B prompt-level re-execution; Tier A repository-based re-execution.
Counts are typed here on purpose so that the figure states exactly what the text states; each is traceable:
  census_raw.jsonl (48,077 records), census_v0_summary.json (32,982 unique), census_v1.csv (27,929),
  census_v2.csv (27,044 on 2 Sept, 39,447 after the refresh of 2 Oct, 42,727 after the second refresh of 11 Oct: data/census_refresh_summary.json, census_refresh2_summary.json), coding/sample_v1.csv (30/500/60), tierb_screen.csv (3,644), SPRINT.md 9/5 and 9/7
  (2,885 / 2,052 / 1,198 / 600 / 70-139-389 / 57-66-9-7 / 127 / 58-60-9), the second pass on 9/19-20 (585 read: 88-126-371;
  88 configs: ready 25 / needs a human 63), batch1_tierb_summary.json (86 results), p0_candidates_raw.csv (1,964),
  harness/cards (70: done 25 / needs-user-check 10 / draft 2 / blocked 33), runs/<Wid>/run_meta.json (calls and cost of the 25 executed),
  data/p3_summary.csv (successor arms).
Style: journal flowchart - Arial, square boxes with a hairline border, a bold headline count per box, one accent tint
for the boxes that hold results, exclusions as grey side notes on the arrows. Output: figures/flow_diagram_matplotlib.png, the
fallback rendering; the figure used in the manuscript is figures/flow_diagram.png, exported from the editable
figures/flow_diagram.pptx (scripts/flow_figure_pptx.py builds it from COLS below, scripts/pptx_export.py renders it). No API calls.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (headline, detail lines, side note on the arrow leaving this box, accent)
COLS = {
    "Census and manual coding": [
        ("117 model identifiers", "retired or with a published retirement date\n55 on 2 Sept + 20 on 2 Oct + 6 on 11 Oct + 36 on 12 Oct 2026\nOpenAI 57, Anthropic 32, Google 28", None, False),
        ("48,077 + 159,102 + 3,275 + 41,140 identifier–work records", "OpenAlex full-text search, four harvests", None, False),
        ("32,982 + 16,771 + 7,561 + 19,548 works considered", "", "5,053 + 3,704 + 3,632 + 2,407 year false positives,\nduplicate titles and undated works removed", False),
        ("27,929 + 13,067 + 3,929 + 17,141 works", "", "885 + 664 + 649 + 1,248 without a DOI or arXiv\nidentifier removed", False),
        ("58,620 works = census", "time to loss (Fig. 2)", "coding sample drawn from the\n27,044 of 2 Sept; 395 without\nEnglish metadata excluded", False),
        ("26,649 with English metadata", "", None, False),
        ("590 sampled for manual coding", "pilot 30, main 500, reserve 60\nfour coders, two per paper, a third on disagreement", None, True),
    ],
    "Prompt-level re-execution (Tier B)": [
        ("3,644 papers", "artefact links or open-access text", None, False),
        ("2,885 full texts obtained", "", "833 name no still-callable\nidentifier in the body", False),
        ("1,198 prompt-complete, unflagged", "2,052 name a still-callable identifier", None, False),
        ("1,185 read by triage agents", "600 first pass, 585 second pass\neligible 158, conditional 265, ineligible 760", "conditionals resolved: 57 eligible, 66 need\nthe repository, 9 a figure read, 7 ineligible", False),
        ("216 eligible papers", "215 run configurations written", "127 need a human decision;\n2 gated data sets excluded", False),
        ("86 configurations ready", "58 + 3 after a data check + 25 second pass", None, False),
        ("86 executed", "judged: reproduced 54 · close 10 · deviated 20 · could not judge 2\n4 cap-stopped finished · 3 subsets extended · 2 repaired", "12 too costly at successor prices;\n7 bias audits kept off third-party accounts", True),
        ("Successor comparison", "one pass per item, same items and scoring\nreplacement 74 · gpt-4.1 49 · Llama 70B 67 · Gemini 67", "1 self-identification task not transferable;\nformat failures 1 · 1 · 2 · 0", False),
        ("Scorable 72 · 48 · 64 · 66", "judged: moved more than 5 points from the reported value\n38 (53%) · 23 (48%) · 43 (67%) · 43 (65%)", None, True),
    ],
    "Repository-based re-execution (Tier A)": [
        ("1,964 candidates", "papers naming a model on the 2026-10-23\nshutdown list, with artefacts", None, False),
        ("70 claim cards", "two shortlists, 46 + 24", "33 blocked: alias to a retired snapshot 18,\nweb interface 4, human outcome 3, data 3, other 5", False),
        ("37 runnable", "25 executed, 2 drafts, 10 await a decision", None, False),
        ("25 executed", "judged: survived 12 · partial 12 · could not judge 1 · died 0\n118,321 calls, $372\n4 also run at prompt level as a validity check", None, True),
    ],
}


def main():
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    INK, GREY, ACCENT = "#111111", "#6B6B6B", "#E8EEF4"
    fig, ax = plt.subplots(figsize=(13.2, 12.0), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    xs = [14.5, 49.0, 83.5]
    w = 25.0
    for (title, boxes), x in zip(COLS.items(), xs):
        ax.text(x - w / 2, 98.4, title, ha="left", va="center", fontsize=9.2, fontweight="bold", color=INK)
        ax.plot([x - w / 2, x + w / 2 + 8], [97.0, 97.0], color=INK, lw=0.6)
        n = len(boxes)
        step = 93.5 / max(n, 7)
        for i, (head, detail, note, accent) in enumerate(boxes):
            lines = 1 + (detail.count("\n") + 1 if detail else 0)
            gap = 3.6 if note else 2.2
            h = min(2.3 + 1.75 * lines, step - gap)
            top = 95.0 - i * step
            yc = top - h / 2
            ax.add_patch(Rectangle((x - w / 2, top - h), w, h, fc=ACCENT if accent else "white", ec=INK, lw=0.6, zorder=2))
            if detail:
                ax.text(x - w / 2 + 1.0, top - 1.4, head, ha="left", va="top", fontsize=7.6, fontweight="bold", color=INK, zorder=3)
                ax.text(x - w / 2 + 1.0, top - 1.4 - 2.0, detail, ha="left", va="top", fontsize=6.5, color=INK, zorder=3, linespacing=1.25)
            else:
                ax.text(x - w / 2 + 1.0, yc, head, ha="left", va="center", fontsize=7.6, fontweight="bold", color=INK, zorder=3)
            if i < n - 1:
                y_next_top = 95.0 - (i + 1) * step
                ax.annotate("", xy=(x, y_next_top + 0.15), xytext=(x, top - h - 0.15),
                            arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.7, shrinkA=0, shrinkB=0, mutation_scale=7))
                if note:
                    ym = (top - h + y_next_top) / 2
                    ax.plot([x, x + 1.6], [ym, ym], color=GREY, lw=0.6)
                    ax.text(x + 2.1, ym, note, ha="left", va="center", fontsize=6.0, color=GREY, linespacing=1.22)
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "flow_diagram_matplotlib.png", bbox_inches="tight", pad_inches=0.1)
    print("->", ROOT / "figures" / "flow_diagram_matplotlib.png")


if __name__ == "__main__":
    main()
