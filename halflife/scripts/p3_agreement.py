"""Successor arms: agreement between arms and leniency of the "moved" definition.

Tables (written to data/):
  p3_agreement.csv  - for every pair of arms, on the papers scorable in both: n, both deviated, only the first, only
                      the second, neither, Cohen's kappa on the deviated/not-deviated dichotomy, and the exact McNemar
                      two-sided p-value of the discordant counts.
  p3_leniency.csv   - per arm: scorable papers, class 편차 ("moved" as used in the text), papers whose point estimate
                      is more than 5 points from the reported value regardless of the interval (raw |delta| > 5),
                      papers reproduced by the interval clause alone (|delta| > 2 but the reported value inside the
                      re-execution interval), of which |delta| > 5, and low-precision results (interval half-width
                      > 10 points).
  p3_threshold_sweep.csv - per arm (Table S39): scorable results, median absolute move from the reported value on the
                      paper's 0-100 scale, the class 편차 count for comparison, and the number and share of results that
                      move by more than 2, 3, 5, 10 and 20 points; the pre-retirement baseline (prompt-level papers on
                      the points scale, from data/reexec_forest.csv) is the first row.
Inputs: data/p3_summary.csv (scripts/p3_summary.py), data/reexec_forest.csv (scripts/reexec_forest.py). No API calls.
"""
import csv, math, statistics
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS = [("vendor", "vendor-designated replacement"), ("gpt41", "gpt-4.1"), ("open70b", "open-weight Llama 3.3 70B"),
        ("gemini_flash", "Gemini 3.8 Flash")]


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def kappa(a, b, c, d):
    n = a + b + c + d
    if n == 0:
        return None
    po = (a + d) / n
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def main():
    rows = list(csv.DictReader(open(ROOT / "data" / "p3_summary.csv", encoding="utf-8-sig")))
    sc = {arm: {r["wid"]: r for r in rows if r["arm"] == arm and r["class_vs_original"] not in ("확인 필요", "해당없음")}
          for arm, _ in ARMS}
    dev = {arm: {w for w, r in sc[arm].items() if r["class_vs_original"] == "편차"} for arm, _ in ARMS}
    with open(ROOT / "data" / "p3_agreement.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["arm_1", "arm_2", "papers_scorable_in_both", "both_deviated", "only_arm_1", "only_arm_2", "neither",
                    "agreement_pct", "cohen_kappa", "mcnemar_exact_p"])
        for (a1, l1), (a2, l2) in combinations(ARMS, 2):
            common = sorted(set(sc[a1]) & set(sc[a2]))
            both = sum(1 for x in common if x in dev[a1] and x in dev[a2])
            o1 = sum(1 for x in common if x in dev[a1] and x not in dev[a2])
            o2 = sum(1 for x in common if x not in dev[a1] and x in dev[a2])
            nei = len(common) - both - o1 - o2
            k = kappa(both, o1, o2, nei)
            w.writerow([l1, l2, len(common), both, o1, o2, nei, round(100 * (both + nei) / len(common), 1) if common else "",
                        "" if k is None else round(k, 2), round(mcnemar_exact(o1, o2), 3)])
    with open(ROOT / "data" / "p3_leniency.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["arm", "scorable", "deviated_class", "deviated_pct", "raw_abs_delta_gt_5", "raw_pct",
                    "reproduced_via_interval_only", "of_which_abs_delta_gt_5", "low_precision_halfwidth_gt_10"])
        for arm, label in ARMS:
            rs = sc[arm]
            n = len(rs)
            d = {x: abs(float(r["delta_vs_original_pts"])) for x, r in rs.items()}
            raw = sum(1 for v in d.values() if v > 5)
            via = [x for x, r in rs.items() if r["class_vs_original"] == "재현" and d[x] > 2]
            via5 = sum(1 for x in via if d[x] > 5)
            lowp = 0
            for x, r in rs.items():
                try:
                    lo, hi = float(r["ci_lo"]), float(r["ci_hi"])
                    unit = 100.0 if abs(float(r["original"])) <= 1.0 and abs(float(r["arm_value"])) <= 1.0 else 1.0
                    if (hi - lo) / 2 * unit > 10:
                        lowp += 1
                except (TypeError, ValueError):
                    pass
            w.writerow([label, n, len(dev[arm]), round(100 * len(dev[arm]) / n, 1), raw, round(100 * raw / n, 1), len(via), via5, lowp])
    # threshold sweep (Table S39): how the share of moved results depends on the point threshold; baseline row first
    TH = (2, 3, 5, 10, 20)
    base = [r for r in csv.DictReader(open(ROOT / "data" / "reexec_forest.csv", encoding="utf-8-sig"))
            if r["tier"] == "B" and r["panel"] == "a" and r["class"] in ("재현", "근접", "편차")]
    sweep = [("pre-retirement baseline (prompt-level papers on the points scale)", [abs(float(r["difference"])) for r in base],
              sum(1 for r in base if r["class"] == "편차"))]
    for arm, label in ARMS:
        sweep.append((label, [abs(float(r["delta_vs_original_pts"])) for r in sc[arm].values()], len(dev[arm])))
    with open(ROOT / "data" / "p3_threshold_sweep.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["condition", "scorable", "median_abs_move_pts", "class_deviated", "class_deviated_pct"]
                   + [x for k in TH for x in (f"moved_gt_{k}_pts", f"moved_gt_{k}_pct")])
        for label, d, ndev in sweep:
            n = len(d)
            w.writerow([label, n, round(statistics.median(d), 1), ndev, round(100 * ndev / n, 1)]
                       + [x for k in TH for x in (sum(v > k for v in d), round(100 * sum(v > k for v in d) / n, 1))])
    for p in ("p3_agreement.csv", "p3_leniency.csv", "p3_threshold_sweep.csv"):
        print("->", p)
        for r in csv.DictReader(open(ROOT / "data" / p, encoding="utf-8-sig")):
            print("  ", " | ".join(f"{k}={v}" for k, v in r.items()))


if __name__ == "__main__":
    main()
