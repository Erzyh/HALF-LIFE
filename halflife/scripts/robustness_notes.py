"""Three robustness notes that need no new API calls (2026-09-28).

1. Format bound for the successor conditions: can format non-compliance alone explain a deviation? For every
   scorable successor result, the share of replies the paper's parser could not read is compared with the
   deviation; a downward deviation no larger than that share (on the 0-100 scale, unparsed counted as wrong)
   is 'explainable by format failures alone'. -> data/p3_format_bound.csv (per result) and the per-condition
   summary printed here (Supplementary Table 24).
2. Born-dead papers: lag from the retirement of the first named model to the publication date, by document
   type. -> data/born_dead_lag.csv (Supplementary Table 25).
3. Seed-to-seed spread of the pre-retirement baselines: range and standard deviation over the three seeds,
   on the paper's scale. -> data/baseline_seed_spread.csv (Supplementary Table 26).
"""
import glob
import json
import statistics as st
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from census_survival import MONTH, build  # noqa: E402

ARMS = {"vendor": "designated replacement (gpt-5.6)", "gpt41": "gpt-4.1", "open70b": "open-weight Llama 3.3 70B (FP8)", "gemini_flash": "Gemini 3.8 Flash"}


def format_bound():
    p3 = pd.read_csv(ROOT / "data" / "p3_summary.csv")
    d = p3[p3["class_vs_original"].isin(["재현", "근접", "편차"])].copy()
    d["unparsed_share"] = d["unparsed"].astype(float) / d["n_items"].astype(float)
    d["delta_pts"] = d["delta_vs_original_pts"].astype(float)
    d["explainable_by_format"] = (d["class_vs_original"] == "편차") & (d["delta_pts"] < 0) & (d["delta_pts"].abs() <= 100 * d["unparsed_share"])
    out = d[["arm", "wid", "title", "metric", "original", "arm_value", "delta_pts", "class_vs_original", "n_items", "unparsed", "unparsed_share", "explainable_by_format"]].copy()
    out["arm"] = out["arm"].map(lambda a: ARMS.get(a, a))
    out["unparsed_share"] = out["unparsed_share"].round(3)
    out.to_csv(ROOT / "data" / "p3_format_bound.csv", index=False, encoding="utf-8-sig")
    rows = []
    for arm, g in d.groupby("arm"):
        dev = g[g["class_vs_original"] == "편차"]
        rows.append({"condition": ARMS.get(arm, arm), "scorable": len(g), "deviated": len(dev), "deviated_down": int((dev["delta_pts"] < 0).sum()),
                     "deviated_up": int((dev["delta_pts"] > 0).sum()), "median_unparsed_share_pct": round(100 * g["unparsed_share"].median(), 1),
                     "max_unparsed_share_pct": round(100 * g["unparsed_share"].max(), 1), "deviated_with_unparsed_over_5pct": int((dev["unparsed_share"] > 0.05).sum()),
                     "deviations_explainable_by_format_alone": int(dev["explainable_by_format"].sum())})
    summ = pd.DataFrame(rows)
    summ.to_csv(ROOT / "data" / "p3_format_bound_summary.csv", index=False, encoding="utf-8-sig")
    print(summ.to_string(index=False))
    return summ


def born_dead_lag():
    d, _, _, _ = build()
    bd = d[d["first_shutdown"] <= d["pub"]].copy()
    bd["lag_months"] = [(p - sd).days / MONTH for p, sd in zip(bd["pub"], bd["first_shutdown"])]
    bins = [-0.01, 3, 6, 12, 24, 10_000]
    labels = ["0-3 months", "3-6 months", "6-12 months", "12-24 months", "over 24 months"]
    bd["lag"] = pd.cut(bd["lag_months"], bins=bins, labels=labels)
    types = ["preprint", "article", "conference-paper"]
    bd["type_group"] = bd["type"].where(bd["type"].isin(types), "other")
    tab = bd.pivot_table(index="lag", columns="type_group", values="openalex_id", aggfunc="count", fill_value=0, observed=False)
    tab = tab[[c for c in types + ["other"] if c in tab.columns]]
    tab = tab.astype(int)
    tab["total"] = tab.sum(axis=1)
    tab["share_pct"] = (100 * tab["total"] / tab["total"].sum()).round(1)
    tab.loc["all born-dead"] = tab.sum(axis=0)
    tab.loc["all born-dead", "share_pct"] = 100.0
    for c in tab.columns:
        if c != "share_pct":
            tab[c] = tab[c].astype(int)
    tab = tab.reset_index().rename(columns={"lag": "retirement to publication"})
    tab.to_csv(ROOT / "data" / "born_dead_lag.csv", index=False, encoding="utf-8-sig")
    print(tab.to_string(index=False))
    within6 = int(bd["lag_months"].le(6).sum())
    over12 = int(bd["lag_months"].gt(12).sum())
    print(f"born-dead {len(bd):,} of {len(d):,} ({100 * len(bd) / len(d):.1f}%): within 6 months {within6:,} ({100 * within6 / len(bd):.0f}%), over 12 months {over12:,} ({100 * over12 / len(bd):.0f}%)")
    return bd


def seed_spread():
    rows = []
    for p in sorted(glob.glob(str(ROOT / "runs" / "tierb" / "W*" / "result.json"))):
        if "v2" in Path(p).parent.name:
            continue
        try:
            x = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        per = (x.get("reexecution") or {}).get("per_seed") or {}
        vals = [s.get("value") for s in per.values() if isinstance(s, dict) and s.get("value") is not None]
        if len(vals) < 2:
            continue
        scale = (x.get("comparison") or {}).get("scale_applied") or 1
        vals = [float(v) * scale for v in vals]
        rows.append({"wid": x["wid"], "title": (x.get("title") or "")[:80], "metric": x.get("metric"), "model": x.get("model"), "seeds": len(vals),
                     "values_pts": "; ".join(f"{v:.2f}" for v in vals), "range_pts": round(max(vals) - min(vals), 2), "sd_pts": round(st.pstdev(vals), 2)})
    out = pd.DataFrame(rows).sort_values("range_pts", ascending=False)
    out.to_csv(ROOT / "data" / "baseline_seed_spread.csv", index=False, encoding="utf-8-sig")
    r = out["range_pts"]
    print(f"baselines with per-seed values: {len(out)} | range median {r.median():.2f}, 75th {r.quantile(0.75):.2f}, 90th {r.quantile(0.9):.2f}, max {r.max():.2f} | "
          f"over 2 pts {(r > 2).sum()} ({100 * (r > 2).mean():.0f}%), over 5 pts {(r > 5).sum()} | sd median {out['sd_pts'].median():.2f}")
    return out


if __name__ == "__main__":
    format_bound()
    born_dead_lag()
    seed_spread()
