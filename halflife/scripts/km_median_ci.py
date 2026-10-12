"""Confidence intervals for the median time to loss (Table S42), by cluster bootstrap over identifiers.

The retirement of a paper's first-retiring identifier happens on one of a few dozen vendor dates, so papers are not
independent observations: resampling papers gives degenerate intervals (the 2026-10-11 version of this table returned
20.4-20.4 months for the whole curve). Here the resampling unit is the identifier that retires first in a paper
(the 'cluster'): 1,000 resamples of the set of first-retiring identifiers with replacement (seed 20260907), every paper
following its identifier with the multiplicity drawn; the median of the published-date distribution (and, beside it,
of the as-of Kaplan-Meier curve censored at TODAY) is taken from the weighted estimator. For the vendor curves the
cluster is the vendor's first-retiring identifier. Point estimates come from census_survival.analyse, so they equal
the medians in Table S1. No API calls. Output: data/km_median_ci.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from census_survival import MONTH, TODAY, analyse, build, origin_col  # noqa: E402

B, SEED = 1000, 20260907
FIELDS = ["Computer Science", "Medicine", "Social Sciences", "Engineering", "Decision Sciences", "Psychology"]


def rows_for(sub, col):
    """Durations (known-date and as-of), events (as-of) and cluster labels of the papers in the curve of one group."""
    oc = origin_col(col)
    sub = sub[sub[col].notna()]
    live = sub[sub[col] > sub[oc]]
    org = live[oc]
    known = np.array([(sd - p).days / MONTH for sd, p in zip(live[col], org)], float)
    asof = np.array([max(0.0, (min(sd, TODAY) - p).days / MONTH) for sd, p in zip(live[col], org)], float)
    evt = np.array([sd <= TODAY for sd in live[col]], int)
    clus = (live["first_model"] if col == "first_shutdown" else live[f"fm_{col[3:]}"]).astype(str).values
    return known, asof, evt, clus


def km_median(t, e, w):
    """Median of the weighted Kaplan-Meier curve; t sorted ascending, e events, w weights (vectorised)."""
    ut, idx = np.unique(t, return_index=True)
    d = np.add.reduceat(e * w, idx)
    n_t = np.add.reduceat(w, idx)
    at_risk = w.sum() - np.concatenate(([0.0], np.cumsum(n_t)[:-1]))
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.cumprod(np.where(at_risk > 0, 1 - d / at_risk, 1.0))
    k = np.where(s <= 0.5)[0]
    return float(ut[k[0]]) if len(k) else np.nan


def cluster_ci(dur, evt, clus, rng):
    order = np.argsort(dur, kind="stable")
    t, e, c = dur[order], evt[order].astype(float), clus[order]
    labels, inv = np.unique(c, return_inverse=True)
    G = len(labels)
    meds = []
    for _ in range(B):
        draw = rng.multinomial(G, np.full(G, 1.0 / G)).astype(float)   # how often each identifier is drawn
        meds.append(km_median(t, e, draw[inv]))
    meds = np.array(meds)
    ok = meds[~np.isnan(meds)]
    if not len(ok):
        return None, None, B, G
    return round(float(np.percentile(ok, 2.5)), 1), round(float(np.percentile(ok, 97.5)), 1), int(len(meds) - len(ok)), G


def main():
    base = build()[0]
    rng = np.random.default_rng(SEED)
    groups = [("all papers", base, "first_shutdown"),
              ("vendor: OpenAI identifiers", base, "sd_openai"), ("vendor: Anthropic identifiers", base, "sd_anthropic"),
              ("vendor: Google identifiers", base, "sd_google"),
              ("type: article", base[base["type"] == "article"], "first_shutdown"),
              ("type: preprint", base[base["type"] == "preprint"], "first_shutdown"),
              ("type: conference paper", base[base["type"] == "conference-paper"], "first_shutdown")]
    groups += [(f"field: {f}", base[base["field"] == f], "first_shutdown") for f in FIELDS]
    rows = []
    for name, sub, col in groups:
        stats, _ = analyse(sub, col)
        asof, _ = analyse(sub, col, known=False)
        known, asof_d, evt, clus = rows_for(sub, col)
        lo, hi, undef, G = cluster_ci(known, np.ones(len(known)), clus, rng)
        klo, khi, kundef, _ = cluster_ci(asof_d, evt, clus, rng)
        rows.append({"group": name, "n_curve": stats["n_curve"], "identifiers_retiring_first": G,
                     "median_months": stats["median_months"], "ci95_lo_months": lo, "ci95_hi_months": hi,
                     "q25_months": stats["q25_months"], "q75_months": stats["q75_months"],
                     "km_median_months": asof["median_months"], "km_ci95_lo_months": klo, "km_ci95_hi_months": khi,
                     "bootstrap_resamples": B, "resamples_without_median": undef, "km_resamples_without_median": kundef})
        print(f"{name:34s} n {stats['n_curve']:6d} clusters {G:3d} median {stats['median_months']} CI {lo}-{hi} | as-of KM {asof['median_months']} CI {klo}-{khi}")
    pd.DataFrame(rows).to_csv(ROOT / "data" / "km_median_ci.csv", index=False, encoding="utf-8-sig")
    print("-> data/km_median_ci.csv")


if __name__ == "__main__":
    main()
