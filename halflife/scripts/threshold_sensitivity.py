"""Sensitivity of the successor 'moved' shares to the five-point threshold, the scale and the paper's own noise
(Supplementary Table 48).

From data/p3_summary.csv (one row per scorable result, paper x condition): the share of results that moved by more
than 5 points against the reported value (the paper's rule) and against the pre-retirement baseline; relative
thresholds (10% and 20% of the reported value); the share by metric family (accuracy-like metrics on a 0-100 scale,
F1 and overlap metrics, error metrics, custom metrics); the share when results whose metric is not a percentage-type
score are left out; and, for the papers with a measured noise floor (seed-to-seed range of the baseline, the
same-snapshot control, the wording check), the share of results whose move against the baseline exceeds both 5 points
and the paper's own floor. No API calls. Output: data/threshold_sensitivity.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARMS = [("vendor", "designated replacement"), ("gpt41", "non-reasoning successor"), ("open70b", "open-weight model"), ("gemini_flash", "other vendor")]
FAMILY = {"accuracy": "accuracy-type (0-100)", "exact_match": "accuracy-type (0-100)", "macro_f1": "F1 / overlap", "micro_f1": "F1 / overlap",
          "rouge_l": "F1 / overlap", "mean_abs_error": "error metric", "custom": "custom (paper-specific)"}


def share(mask, n):
    return round(100 * float(mask.sum()) / n, 1) if n else None


def main():
    p = pd.read_csv(ROOT / "data" / "p3_summary.csv", encoding="utf-8-sig")
    p = p[p["arm"].isin([a for a, _ in ARMS]) & p["delta_vs_original_pts"].notna() & p["delta_vs_baseline_pts"].notna()
          & p["class_vs_original"].isin(["재현", "근접", "편차"])].copy()      # the judged scorable results, as in Table 1
    p["family"] = p["metric"].map(FAMILY).fillna("custom (paper-specific)")
    # the runner's scale guess: proportions reported in 0-1 were scored x100
    p["scale"] = np.where((p["original"].abs() <= 1.5) & (p["arm_value"].abs() <= 1.5), 100.0, 1.0)
    p["original_pts"] = p["original"] * p["scale"]
    p["rel_vs_original"] = (p["delta_vs_original_pts"].abs() / p["original_pts"].abs().replace(0, np.nan))
    # noise floors per paper
    seed = pd.read_csv(ROOT / "data" / "baseline_seed_spread.csv", encoding="utf-8-sig").groupby("wid")["range_pts"].max()
    drift = pd.read_csv(ROOT / "data" / "drift_control.csv", encoding="utf-8-sig").groupby("wid")["delta_vs_baseline_mean_pts"].apply(lambda s: s.abs().max())
    word = pd.read_csv(ROOT / "data" / "p3_paraphrase_spread.csv", encoding="utf-8-sig").groupby("wid")["wording_range_pts"].max()
    floor = pd.concat([seed.rename("seed"), drift.rename("drift"), word.rename("wording")], axis=1)
    floor["floor"] = floor.max(axis=1)
    p["floor"] = p["wid"].map(floor["floor"])

    rows = []
    for arm, label in ARMS:
        a = p[p["arm"] == arm]
        n = len(a)
        row = {"condition": label, "scorable_results": n,
               "moved_gt5_vs_reported_pct": share(a["delta_vs_original_pts"].abs() > 5, n),
               "moved_gt5_vs_baseline_pct": share(a["delta_vs_baseline_pts"].abs() > 5, n),
               "moved_gt10_vs_reported_pct": share(a["delta_vs_original_pts"].abs() > 10, n),
               "moved_rel10_vs_reported_pct": share(a["rel_vs_original"] > 0.10, n),
               "moved_rel20_vs_reported_pct": share(a["rel_vs_original"] > 0.20, n)}
        for fam in ("accuracy-type (0-100)", "F1 / overlap", "error metric", "custom (paper-specific)"):
            s = a[a["family"] == fam]
            row[f"{fam}: n"] = len(s)
            row[f"{fam}: moved_gt5_vs_reported_pct"] = share(s["delta_vs_original_pts"].abs() > 5, len(s))
        pct = a[a["family"] == "accuracy-type (0-100)"]
        row["percentage_metrics_only: n"] = len(pct)
        row["percentage_metrics_only: moved_gt5_vs_reported_pct"] = share(pct["delta_vs_original_pts"].abs() > 5, len(pct))
        fl = a[a["floor"].notna()]
        row["papers_with_noise_floor: n"] = len(fl)
        row["papers_with_noise_floor: moved_gt5_vs_baseline_pct"] = share(fl["delta_vs_baseline_pts"].abs() > 5, len(fl))
        row["papers_with_noise_floor: moved_beyond_max(5, floor)_pct"] = share(fl["delta_vs_baseline_pts"].abs() > np.maximum(5, fl["floor"]), len(fl))
        row["papers_with_noise_floor: median_floor_pts"] = round(float(fl["floor"].median()), 1) if len(fl) else None
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "data" / "threshold_sensitivity.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 300, "display.max_columns", 40):
        print(out.T.to_string())
    print("-> data/threshold_sensitivity.csv")


if __name__ == "__main__":
    main()
