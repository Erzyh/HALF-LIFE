"""Cox proportional-hazards model for the census: hazard of losing the first named model.

Time = months from the origin (publication date, corrected as in census_survival.build) to the published retirement
date of the first-retiring identifier: every paper has the event, nothing is censored. Born-dead papers are excluded
(as in the curves). Covariates: vendor mix of the named models (any Anthropic, any Google; baseline OpenAI only),
field (baseline Computer Science), publication year (baseline 2024), preprint versus other, and log(1 + citations).
Efron ties. Standard errors are cluster-robust by the identifier that retires first (statsmodels PHReg with groups):
the retirement dates come from a few dozen vendor decisions, not from 35,000 independent papers, and the naive
intervals of the earlier version were an order of magnitude too narrow.

Outputs: data/cox_hazard_ratios.csv, figures/cox_forest.png. No API calls. The proportional-hazards checks
(Schoenfeld residuals, stratified and period-specific models) live in scripts/cox_checks.py.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from census_survival import MONTH, build  # noqa: E402

FIELDS = ["Medicine", "Social Sciences", "Engineering", "Decision Sciences", "Psychology"]
YEARS = [2022, 2023, 2025, 2026]


def design():
    """Analysis rows (born-dead papers excluded, positive follow-up) and the covariate matrix of the main model.

    Shared with scripts/cox_checks.py so that the proportional-hazards checks use exactly this design."""
    d, _, _, _ = build()
    live = d[d["first_shutdown"] > d["pub"]].copy()
    live["time"] = [(sd - p).days / MONTH for sd, p in zip(live["first_shutdown"], live["pub"])]
    live["event"] = 1
    live["cluster"] = live["first_model"].astype(str)
    live = live[live["time"] > 0]
    X = pd.DataFrame(index=live.index)
    X["any Anthropic model"] = live["vendors"].str.contains("anthropic").astype(float)
    X["any Google model"] = live["vendors"].str.contains("google").astype(float)
    for f in FIELDS:
        X[f"field: {f}"] = (live["field"] == f).astype(float)
    X["field: other"] = (~live["field"].isin(FIELDS + ["Computer Science"])).astype(float)
    for y in YEARS:
        X[f"published {y}"] = (live["year"] == y).astype(float)
    X["preprint"] = (live["type"] == "preprint").astype(float)
    X["log(1 + citations)"] = np.log1p(live["citations"].fillna(0).astype(float))
    return live, X


def fit_clustered(time, X, status, groups, strata=None, entry=None):
    """PHReg fit with cluster-robust standard errors (groups = identifier that retires first)."""
    m = sm.PHReg(np.asarray(time, float), np.asarray(X, float), status=np.asarray(status, int), ties="efron", strata=strata, entry=entry)
    return m.fit(groups=np.asarray(groups))


def main():
    live, X = design()
    res = fit_clustered(live["time"], X, live["event"], live["cluster"])
    params, se = res.params, res.bse
    out = pd.DataFrame({"covariate": X.columns, "coef": params, "hazard_ratio": np.exp(params),
                        "hr_ci_lo": np.exp(params - 1.96 * se), "hr_ci_hi": np.exp(params + 1.96 * se),
                        "p": res.pvalues})
    out["n_with_covariate"] = [int((X[c] > 0).sum()) if c != "log(1 + citations)" else len(X) for c in X.columns]
    out["standard_errors"] = f"cluster-robust by first-retiring identifier ({live['cluster'].nunique()} clusters)"
    out.to_csv(ROOT / "data" / "cox_hazard_ratios.csv", index=False, encoding="utf-8-sig")
    print(f"n = {len(live):,}, events = {int(live['event'].sum()):,}, clusters = {live['cluster'].nunique()}")
    print(out.drop(columns=["standard_errors"]).round(3).to_string(index=False))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from figstyle import apply, panel, VENDOR, SERIES, BLUE, BLUE_LIGHT, ORANGE, GREY, DARK  # noqa: F401
    apply()
    fig, ax = plt.subplots(figsize=(5.2, 0.24 * len(out) + 1.1), dpi=200)
    y = np.arange(len(out))[::-1]
    ax.axvline(1, color=GREY, lw=0.7)
    ax.errorbar(out["hazard_ratio"], y, xerr=[out["hazard_ratio"] - out["hr_ci_lo"], out["hr_ci_hi"] - out["hazard_ratio"]],
                fmt="o", color=BLUE, ms=3, capsize=1.5, lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{c}  (n={n:,})" if c != "log(1 + citations)" else c for c, n in zip(out["covariate"], out["n_with_covariate"])], fontsize=6.8)
    ax.set_xscale("log")
    ticks = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t:g}" for t in ticks], fontsize=6.8)
    ax.minorticks_off()
    ax.set_xlabel("hazard ratio for losing the first named model (95% CI, cluster-robust by identifier)\nbaselines: OpenAI-only identifiers, computer science, 2024, not a preprint", fontsize=6.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "cox_forest.png", bbox_inches="tight")
    print("->", ROOT / "figures" / "cox_forest.png")


if __name__ == "__main__":
    main()
