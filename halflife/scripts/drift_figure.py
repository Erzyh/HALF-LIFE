"""Drift inside a pinned snapshot: Tier A re-executions where item-level outputs reproduce but behavioural
quantities move.

(a) News credibility (gpt-4-turbo-2024-04-09): per-domain rating in the released original run versus our
    re-run, for domains rated in both; rating changes and refusal flips are counted.
(b) Behavioural quantities, original versus re-run, in percentage points, across the Tier A runs.
(c) Refusal share by backend fingerprint inside the single re-run of (a).
Inputs: runs/W4362598103/baseline_alive/calls.jsonl, the released llm_ratings.parquet (under halflife/external,
not redistributed), runs/<Wid>/run_meta.json. Outputs: figures/drift_case_study.png, data/drift_fingerprints.csv,
data/drift_quantities.csv. No API calls.
"""
import json, sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness" / "adapters"))
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "scripts"))
import newscred_W4362598103 as nc  # noqa: E402


def meta(wid):
    return json.load(open(ROOT / "runs" / wid / "run_meta.json", encoding="utf-8"))


def rerun_ratings():
    rows = []
    for line in open(ROOT / "runs" / "W4362598103" / "baseline_alive" / "calls.jsonl", encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") != 200:
            continue
        text = r["response"]["choices"][0]["message"].get("content")
        rating = nc.parse_rating(text)
        rows.append({"domain": r["id"], "rating": np.nan if rating is None else rating,
                     "fp": r.get("system_fingerprint") or "none"})
    return pd.DataFrame(rows)


def quantities():
    news, med, cul, tag, bl = meta("W4362598103"), meta("W7140135941"), meta("W4402565126"), meta("W7171749161"), meta("W7144391134")
    nr = news["results"]
    rows = [("News: domains refused", 100 * nr["original"]["unrated_share"], 100 * nr["reexecution"]["unrated_share"]),
            ("News: Spearman rho x100 vs experts", 100 * nr["original"]["rho_own"], 100 * nr["reexecution"]["rho_own"])]
    for key, label in (("noCoT/A", "MedAbstain: abstains, no CoT, abstain option"),
                       ("noCoT/AP", "MedAbstain: abstains, no CoT, + distractor"),
                       ("CoT/A", "MedAbstain: abstains, CoT, abstain option"),
                       ("CoT/AP", "MedAbstain: abstains, CoT, + distractor")):
        r = med["results"]["rows"][key]
        rows.append((label, 100 * (r.get("orig_abstention") or 0.0), 100 * r["abstention"]))
    co, cr = cul["results"]["original"], cul["results"]["reexecution"]
    rows.append(("Cultural bias: countries improved", 100 * co["share_improved"], 100 * cr["share_improved"]))
    rows.append(("Tag Questions: tag effect", 100 * tag["target_paper"]["original_values"]["tageff"], 100 * tag["results"]["reexecution"]["tageff"]))
    rows.append(("BlindingLLMs: r x100, 60-shot", bl["results"]["icl_60"]["orig_r"], bl["results"]["icl_60"]["r"]))
    rows.append(("BlindingLLMs: r x100, 1000-shot", bl["results"]["icl_1000"]["orig_r"], bl["results"]["icl_1000"]["r"]))
    return pd.DataFrame(rows, columns=["quantity", "original", "rerun"])


def main():
    o = nc.original_frame()
    o = o[o.model == nc.ORIG_CODE][["domain", "rating"]].groupby("domain", as_index=False).first()
    rr = rerun_ratings()
    m = o.merge(rr, on="domain", suffixes=("_orig", "_rerun"))
    both = m[(m.rating_orig >= 0) & (m.rating_rerun >= 0)]
    rho = spearmanr(both.rating_orig, both.rating_rerun).correlation
    flips = m[(m.rating_orig >= 0) != (m.rating_rerun >= 0)]
    to_refuse = int(((m.rating_orig >= 0) & (m.rating_rerun < 0)).sum())
    to_rate = int(((m.rating_orig < 0) & (m.rating_rerun >= 0)).sum())
    identical = float((np.isclose(both.rating_orig, both.rating_rerun)).mean())
    print(f"domains matched {len(m):,}; rated in both {len(both):,}; rho {rho:.3f}; identical rating {100*identical:.1f}%; "
          f"flips {len(flips):,} ({100*len(flips)/len(m):.1f}%): rated->refused {to_refuse:,}, refused->rated {to_rate:,}")
    fp = (rr.assign(refused=rr.rating < 0, parsed=rr.rating.notna())
            .groupby("fp").agg(n=("domain", "size"), refused=("refused", "sum"), parsed=("parsed", "sum")).reset_index())
    fp["refusal_share"] = fp["refused"] / fp["parsed"]
    fp = fp.sort_values("n", ascending=False)
    fp.to_csv(ROOT / "data" / "drift_fingerprints.csv", index=False, encoding="utf-8-sig")
    print(fp.to_string(index=False))
    q = quantities()
    q["delta_pts"] = q["rerun"] - q["original"]
    q.to_csv(ROOT / "data" / "drift_quantities.csv", index=False, encoding="utf-8-sig")
    print(q.round(1).to_string(index=False))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from figstyle import apply, panel, VENDOR, SERIES, BLUE, BLUE_LIGHT, ORANGE, GREY, DARK  # noqa: F401
    apply()
    fig = plt.figure(figsize=(7.2, 5.4), dpi=200)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.15], height_ratios=[1.0, 0.9], wspace=0.6, hspace=0.5)
    ax = fig.add_subplot(gs[0, 0])
    hb = ax.hexbin(both.rating_orig, both.rating_rerun, gridsize=22, bins="log", cmap="Blues", mincnt=1, extent=(0, 1, 0, 1))
    ax.plot([0, 1], [0, 1], color="#1D2321", lw=0.8, ls="--")
    ax.set_xlabel("original rating (released run)")
    ax.set_ylabel("re-run rating, same dated snapshot")
    ax.set_title("news credibility, per domain")
    panel(ax, "a", x=-0.25)
    ax.text(0.03, 0.97, f"n = {len(both):,} rated in both\nrho = {rho:.3f}\nidentical {100*identical:.0f}%\n"
                        f"refusal flipped: {100*len(flips)/len(m):.1f}% of {len(m):,}",
            transform=ax.transAxes, va="top", fontsize=5.8)
    cax = ax.inset_axes([0.86, 0.07, 0.035, 0.42])       # lower right of the panel is empty (high original, low re-run)
    cb = fig.colorbar(hb, cax=cax)
    cb.set_label("domains", fontsize=5.5)
    cb.ax.tick_params(labelsize=5, width=0.5, length=2)
    cb.outline.set_linewidth(0.5)

    ax2 = fig.add_subplot(gs[1, :])
    ys = np.arange(len(q))[::-1]
    for y, (_, r) in zip(ys, q.iterrows()):
        ax2.plot([r.original, r.rerun], [y, y], color=GREY, lw=0.9, zorder=1)
        ax2.plot([r.original], [y], "o", color=GREY, ms=3.6, zorder=2)
        ax2.plot([r.rerun], [y], "o", color=ORANGE, ms=3.6, zorder=3)
        ax2.annotate(f"{r.original:.1f} → {r.rerun:.1f}", (max(r.original, r.rerun), y), xytext=(5, 0), textcoords="offset points", va="center", fontsize=5.8)
    ax2.set_yticks(ys)
    ax2.set_yticklabels(q["quantity"], fontsize=6.6)
    ax2.set_xlabel("percentage points")
    ax2.set_xlim(-15, 100)
    ax2.set_title("behavioural quantities: original (grey), re-run (orange)")
    panel(ax2, "b", x=-0.3)

    ax3 = fig.add_subplot(gs[0, 1])
    ys = np.arange(len(fp))[::-1]
    ax3.barh(ys, 100 * fp["refusal_share"], color=BLUE, height=0.65)
    ax3.set_yticks(ys)
    ax3.set_yticklabels([f"{f[:14]} (n={n:,})" for f, n in zip(fp["fp"], fp["n"])], fontsize=6.2)
    ax3.axvline(100 * nc_original_unrated(), color=GREY, ls=(0, (3, 2)), lw=0.8)
    ax3.axvline(100 * float(rr.rating.lt(0).sum() / rr.rating.notna().sum()), color=ORANGE, ls="-", lw=0.8)
    ax3.set_xlabel("refusal share (%)")
    ax3.set_title("refusal by backend fingerprint")
    panel(ax3, "c", x=-0.42)
    ax3.text(0.98, 0.03, "dashed: original run\nsolid: re-run overall", transform=ax3.transAxes, ha="right", va="bottom", fontsize=5.8)
    for a in (ax, ax2, ax3):
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "drift_case_study.png", bbox_inches="tight")
    print("->", ROOT / "figures" / "drift_case_study.png")


def nc_original_unrated():
    return meta("W4362598103")["results"]["original"]["unrated_share"]


if __name__ == "__main__":
    main()
