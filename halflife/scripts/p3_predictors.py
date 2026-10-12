"""Which results move when the model is replaced? Predictors of a successor deviation.

Unit: one scorable successor result (paper x arm) from data/p3_summary.csv; outcome: the class 편차 (more than 5 points
from the reported value and the reported value outside the re-execution interval), i.e. "moved" as used in the text.
Covariates per paper: task type and field group (triage tables, via tierb_selection.load()), metric family, the
pre-shutdown baseline's class against the reported value, the family of the paper's original model, the reported value
on its 0-100 scale, the number of items (log10), and the arm.

Two outputs:
  data/p3_predictors_univariate.csv - per covariate level: results, deviated, share with Wilson 95% interval.
  data/p3_predictors_model.csv      - pooled logistic regression with arm fixed effects and paper-clustered robust
                                      standard errors: odds ratio, 95% interval, p-value per term.
No API calls.
"""
import csv, math, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from tierb_selection import load                              # noqa: E402
from p3_summary import unit_of                                # noqa: E402

ARM_LABEL = {"vendor": "vendor-designated (gpt-5.6)", "gpt41": "gpt-4.1", "open70b": "open-weight Llama 70B", "gemini_flash": "Gemini 3.8 Flash"}
TASK = {"classification": "classification", "mcq": "multiple choice", "generation": "generation", "extraction": "extraction",
        "other": "other / agentic", "agentic": "other / agentic"}
FIELD = {"SOC": "social science", "LIFE": "life science", "MED": "medicine", "ENG": "engineering", "CS": "computer science"}


def family(mid):
    m = (mid or "").lower()
    if m.startswith(("o1", "o3", "o4", "gpt-5")):
        return "reasoning (o-series, gpt-5)"
    if m.startswith("gpt-4o"):
        return "gpt-4o"
    if m.startswith("gpt-4.1"):
        return "gpt-4.1-nano"
    return "gpt-4-turbo"


def metric_family(m):
    m = (m or "").lower()
    return "accuracy / exact match" if m in ("accuracy", "exact_match") else "other metric"


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


def main():
    recs, grp, cfg, cen, summ = load()
    rows = [r for r in csv.DictReader(open(ROOT / "data" / "p3_summary.csv", encoding="utf-8-sig"))
            if r["class_vs_original"] not in ("확인 필요", "해당없음")]
    data = []
    for r in rows:
        w = r["wid"]
        orig = float(r["original"])
        val = float(r["arm_value"]) if r["arm_value"] else None
        u = unit_of(orig, val if val is not None else orig)
        data.append({
            "wid": w, "arm": r["arm"],
            "deviated": int(r["class_vs_original"] == "편차"),
            "task": TASK.get((cfg.get(w, {}).get("task_type") or "other").lower(), "other / agentic"),
            "field": FIELD.get(grp.get(w, {}).get("group") or "", "unknown"),
            "metric": metric_family(r["metric"]),
            "baseline": {"재현": "reproduced", "근접": "close", "편차": "deviated"}.get(r["baseline_class_vs_original"], "other"),
            "family": family(r["config_model"]),
            "original_pts": orig * u,
            "log_items": math.log10(max(1.0, float(r["n_items"] or 1))),
        })
    df = pd.DataFrame(data)
    print(f"results {len(df)}, papers {df.wid.nunique()}, deviated {int(df.deviated.sum())} ({100 * df.deviated.mean():.0f}%)")

    # ---- univariate table
    uni = []
    for col, label in (("arm", "arm"), ("task", "task type"), ("field", "field group"), ("metric", "metric family"),
                       ("baseline", "pre-shutdown baseline vs reported"), ("family", "original model family")):
        for lvl, g in df.groupby(col):
            k, n = int(g.deviated.sum()), len(g)
            lo, hi = wilson(k, n)
            uni.append({"covariate": label, "level": ARM_LABEL.get(lvl, lvl), "results": n, "papers": g.wid.nunique(), "deviated": k,
                        "share_pct": round(100 * k / n, 1), "wilson_lo_pct": round(100 * lo, 1), "wilson_hi_pct": round(100 * hi, 1)})
    for col, label, cuts in (("original_pts", "reported value (0-100 scale)", [0, 50, 75, 90, 100.01]),
                             ("log_items", "items (log10)", [0, 2, 2.5, 3, 9])):
        binned = pd.cut(df[col], cuts, right=False)
        for lvl, g in df.groupby(binned, observed=True):
            k, n = int(g.deviated.sum()), len(g)
            lo, hi = wilson(k, n)
            uni.append({"covariate": label, "level": str(lvl), "results": n, "papers": g.wid.nunique(), "deviated": k,
                        "share_pct": round(100 * k / n, 1), "wilson_lo_pct": round(100 * lo, 1), "wilson_hi_pct": round(100 * hi, 1)})
    pd.DataFrame(uni).to_csv(ROOT / "data" / "p3_predictors_univariate.csv", index=False, encoding="utf-8-sig")

    # ---- pooled logistic regression, paper-clustered robust SE
    import statsmodels.formula.api as smf
    df["arm"] = pd.Categorical(df["arm"], ["vendor", "gpt41", "open70b", "gemini_flash"])
    df["task"] = pd.Categorical(df["task"], ["classification", "multiple choice", "generation", "extraction", "other / agentic"])
    df["field"] = pd.Categorical(df["field"], ["social science", "life science", "medicine", "engineering", "computer science"])
    df["metric"] = pd.Categorical(df["metric"], ["accuracy / exact match", "other metric"])
    n_other = int((~df["baseline"].isin(["reproduced", "close", "deviated"])).sum())
    if n_other:
        print(f"regression leaves out {n_other} results whose pre-shutdown baseline could not be judged")
    df = df[df["baseline"].isin(["reproduced", "close", "deviated"])].copy()
    df["baseline"] = pd.Categorical(df["baseline"], ["reproduced", "close", "deviated"])
    df["family"] = pd.Categorical(df["family"], ["gpt-4-turbo", "gpt-4o", "gpt-4.1-nano", "reasoning (o-series, gpt-5)"])
    df["original_10"] = df["original_pts"] / 10.0
    formula = "deviated ~ arm + task + field + metric + baseline + family + original_10 + log_items"
    model = smf.logit(formula, data=df).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": df["wid"].astype("category").cat.codes})
    ci = model.conf_int()
    out = []
    for term in model.params.index:
        out.append({"term": term, "odds_ratio": round(float(np.exp(model.params[term])), 2),
                    "ci_lo": round(float(np.exp(ci.loc[term, 0])), 2), "ci_hi": round(float(np.exp(ci.loc[term, 1])), 2),
                    "p": round(float(model.pvalues[term]), 3)})
    meta = {"term": "model", "odds_ratio": "", "ci_lo": "", "ci_hi": "",
            "p": f"n = {len(df)} results from {df.wid.nunique()} papers; logistic regression, robust SE clustered by paper; "
                 f"pseudo R2 {model.prsquared:.2f}; reference levels: vendor arm, classification, social science, accuracy, baseline reproduced, gpt-4-turbo"}
    pd.DataFrame(out + [meta]).to_csv(ROOT / "data" / "p3_predictors_model.csv", index=False, encoding="utf-8-sig")
    print(pd.DataFrame(out).to_string(index=False))
    print(meta["p"])
    print("-> data/p3_predictors_univariate.csv, data/p3_predictors_model.csv")


if __name__ == "__main__":
    main()
