"""How far the successor result generalises beyond the executed papers: joint re-weighting and transparent bounds.

The executed prompt-level papers are the most completely reported ones (printed prompts, public items, a single
model), so the shares measured on them describe the stratum where re-execution is possible. Two devices make that
explicit without a model that the data cannot support (Table S18: the available covariates barely predict a deviation):

1. Raking (iterative proportional fitting). The scorable results of the designated-replacement condition (one per paper)
   are re-weighted so that their joint margins over field group, year, document type, task type, model family and cost
   tier match the 216 eligible papers of the triage (the population of Table S10) at once, rather than one dimension at
   a time as in Table S11. The weighted share of deviated results is reported with a bootstrap 95% interval (papers
   resampled, raking repeated). The pre-retirement classes of the 86 executed papers are raked the same way.

2. Bounds. For the eligible papers without a scorable successor result the deviation share is unknown. The table gives
   the share among all eligible papers under stated assumptions for the unmeasured ones (0, half, three quarters, the
   same, 1.25 and 1.5 times the measured share, and 1: the Manski bounds are the first and last rows), and the share of
   triaged candidates whose result demonstrably carries over to the designated replacement, between "no unmeasured paper
   carries over" and "every unmeasured eligible paper carries over" (and, in a last column, every undecided 'maybe'
   candidate as well); candidates that failed triage cannot be re-executed at all and never carry over.

Writes data/p3_selection_raking.csv and data/p3_selection_bounds.csv. No API calls.
"""
import collections
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "scripts"))
from tierb_selection import cit_band, load, model_family  # noqa: E402

DIMS = ["field group", "year", "document type", "task type", "model family", "cost tier"]
RNG = np.random.default_rng(20260907)


def eligible_rows():
    recs, grp, cfg, cen, summ = load()
    rows, n_cand = [], 0
    verdicts = collections.Counter(r.get("verdict") for r in recs.values())
    for w, r in recs.items():
        n_cand += 1
        if r.get("verdict") != "eligible":
            continue
        g, c, ce = grp.get(w, {}), cfg.get(w, {}), cen.get(w, {})
        cost = r.get("cost") if isinstance(r.get("cost"), dict) else {}
        live = r.get("live_model") if isinstance(r.get("live_model"), dict) else {}
        rows.append({"wid": w, "executed": w in summ, "class_pre": summ.get(w, {}).get("class"),
                     "field group": g.get("group") or "unknown", "year": str(g.get("year") or ce.get("year") or "unknown"),
                     "document type": ce.get("type") or "unknown", "citations": cit_band(ce.get("citations")),
                     "cost tier": (c.get("cost_tier") or cost.get("tier") or "unknown"), "task type": c.get("task_type") or "no config",
                     "model family": model_family(c.get("resolved_model") or live.get("resolved"))})
    return pd.DataFrame(rows), n_cand, verdicts


def rake(sample, population, dims, iters=60):
    """IPF weights for `sample` so that its weighted margins match `population` on every dimension (strata absent from
    the sample are dropped from the target and the remaining target margins renormalised)."""
    w = np.ones(len(sample))
    targets = {}
    for d in dims:
        present = set(sample[d])
        pop = population[population[d].isin(present)][d].value_counts(normalize=True)
        targets[d] = pop
    for _ in range(iters):
        for d in dims:
            cur = pd.Series(w).groupby(sample[d].values).sum()
            cur = cur / cur.sum()
            factor = {k: (targets[d].get(k, 0) / cur[k]) if cur.get(k, 0) > 0 else 1.0 for k in cur.index}
            w = w * np.array([factor[k] for k in sample[d].values])
            w = w / w.mean()
    return w


def weighted_share(flags, w):
    return float(np.sum(w * flags) / np.sum(w))


def main():
    elig, n_cand, verdicts = eligible_rows()
    n_maybe = verdicts.get("maybe", 0)
    n_elig = len(elig)
    p3 = pd.read_csv(HALF / "data" / "p3_summary.csv", encoding="utf-8-sig")
    vend = p3[p3.arm == "vendor"].set_index("wid")
    elig["class_succ"] = elig.wid.map(vend.class_vs_original)
    scorable = elig[elig.class_succ.isin(["재현", "근접", "편차"])].reset_index(drop=True)
    executed = elig[elig.executed & elig.class_pre.isin(["재현", "근접", "편차", "확인 필요"])].reset_index(drop=True)

    out = []
    def block(name, sample, flag_col, flag_val, label):
        flags = (sample[flag_col] == flag_val).astype(float).values
        raw = flags.mean()
        w = rake(sample, elig, DIMS)
        est = weighted_share(flags, w)
        boots = []
        for _ in range(1000):
            idx = RNG.integers(0, len(sample), len(sample))
            s = sample.iloc[idx].reset_index(drop=True)
            boots.append(weighted_share((s[flag_col] == flag_val).astype(float).values, rake(s, elig, DIMS, iters=30)))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        one_dim = {d: weighted_share(flags, rake(sample, elig, [d])) for d in DIMS}
        cov = {d: round(100 * elig[elig[d].isin(set(sample[d]))].shape[0] / n_elig, 1) for d in DIMS}
        out.append({"quantity": name, "n": len(sample), "raw_share_pct": round(100 * raw, 1),
                    "raked_share_pct": round(100 * est, 1), "raked_ci95_lo": round(100 * lo, 1), "raked_ci95_hi": round(100 * hi, 1),
                    "weight_min": round(float(w.min()), 2), "weight_max": round(float(w.max()), 2), "design_effect": round(float(len(w) * np.sum(w ** 2) / np.sum(w) ** 2), 2),
                    **{f"one_dim_{d.replace(' ', '_')}_pct": round(100 * v, 1) for d, v in one_dim.items()},
                    "population_covered_pct_min_over_dims": min(cov.values()), "note": label})
    block("deviated on the designated replacement", scorable, "class_succ", "편차", "scorable vendor-arm results, one per paper; population: 216 eligible papers")
    block("reproduced before retirement", executed, "class_pre", "재현", "executed prompt-level papers; population: 216 eligible papers")
    block("deviated before retirement", executed, "class_pre", "편차", "executed prompt-level papers; population: 216 eligible papers")
    rk = pd.DataFrame(out)
    rk.to_csv(HALF / "data" / "p3_selection_raking.csv", index=False, encoding="utf-8-sig")

    # ---- bounds
    n_scor = len(scorable); n_dev = int((scorable.class_succ == "편차").sum()); n_carry = n_scor - n_dev
    n_unmeasured = n_elig - n_scor
    measured = n_dev / n_scor
    rows = []
    for k, lab in ((0.0, "no unmeasured eligible paper would deviate (Manski lower bound)"), (0.5, "half the measured share"), (0.75, "three quarters"),
                   (1.0, "the measured share"), (1.25, "1.25 times"), (1.5, "1.5 times"), (None, "every unmeasured eligible paper would deviate (Manski upper bound)")):
        share_un = 1.0 if k is None else min(1.0, k * measured)
        dev_total = n_dev + share_un * n_unmeasured
        rows.append({"assumption_for_unmeasured_eligible": lab, "assumed_deviation_share_pct": round(100 * share_un, 1),
                     "deviated_among_eligible_pct": round(100 * dev_total / n_elig, 1),
                     "carry_over_among_eligible_pct": round(100 * (n_elig - dev_total) / n_elig, 1),
                     "carry_over_among_candidates_pct": round(100 * (n_elig - dev_total) / n_cand, 1),
                     "carry_over_among_candidates_pct_if_undecided_all_carry": round(100 * (n_elig - dev_total + n_maybe) / n_cand, 1)})
    b = pd.DataFrame(rows)
    b.attrs = {}
    b.to_csv(HALF / "data" / "p3_selection_bounds.csv", index=False, encoding="utf-8-sig")
    summary = {"candidates_triaged": n_cand, "eligible": n_elig, "undecided_maybe": n_maybe, "ineligible_never_reexecutable": verdicts.get("ineligible", 0),
               "executed_pre_retirement": int(elig.executed.sum()), "scorable_on_designated_replacement": n_scor, "deviated": n_dev, "carry_over_measured": n_carry,
               "carry_over_among_candidates_pct_min": round(100 * n_carry / n_cand, 1),
               "carry_over_among_candidates_pct_max_undecided_excluded": round(100 * (n_carry + n_unmeasured) / n_cand, 1),
               "carry_over_among_candidates_pct_max_undecided_included": round(100 * (n_carry + n_unmeasured + n_maybe) / n_cand, 1)}
    pd.DataFrame([summary]).to_csv(HALF / "data" / "p3_selection_bounds_summary.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 220, "display.max_columns", 30):
        print(rk[["quantity", "n", "raw_share_pct", "raked_share_pct", "raked_ci95_lo", "raked_ci95_hi", "design_effect", "population_covered_pct_min_over_dims"]].to_string(index=False))
        print(b.to_string(index=False))
        print(summary)


if __name__ == "__main__":
    main()
