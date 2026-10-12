"""Proportional-hazards checks for the census Cox model (no API calls).

Everything runs on the design of scripts/cox_model.py (born-dead papers excluded, Efron ties).

1. Schoenfeld residual test of proportional hazards (Grambsch and Therneau 1994), per covariate and
   globally, with the Kaplan-Meier, rank and identity transforms of time, as in R's cox.zph and
   lifelines' proportional_hazard_test. With s_k the Schoenfeld residual at event k, V the covariance
   of the estimate and d the number of events, the scaled residual is s*_k = d V s_k and
   beta_hat + s*_k estimates beta(t_k). Per covariate: [sum (g - gbar) s*_j]^2 / (d V_jj sum (g - gbar)^2)
   on 1 df; globally: a*' V^-1 a* / (d sum (g - gbar)^2) on p df, with a* = sum (g - gbar) s*.
2. Stratified Cox models: a baseline hazard per publication year (vendor, field, preprint and citation
   effects kept), per vendor group (field, year, preprint and citation effects kept), and per year x
   vendor group.
3. Period-specific hazard ratios by episode splitting at 6, 12 and 24 months (counting-process form
   with entry times): the two vendor terms and the citation term interact with the follow-up period,
   the other covariates stay constant.

Outputs: data/cox_schoenfeld.csv, data/cox_stratified.csv, data/cox_period_hr.csv,
figures/cox_ph_check.png.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from census_survival import km  # noqa: E402
from cox_model import design  # noqa: E402

CUTS = [0.0, 6.0, 12.0, 24.0, np.inf]
PERIODS = ["0-6 months", "6-12 months", "12-24 months", "over 24 months"]
INTERACT = ["any Anthropic model", "any Google model", "log(1 + citations)"]
VENDOR_COLS = ["any Anthropic model", "any Google model"]
N_BINS = 12


def fit(time, X, status, strata=None, entry=None, groups=None):
    """PHReg fit; with `groups` (the identifier that retires first) the standard errors are cluster-robust."""
    m = sm.PHReg(np.asarray(time, float), np.asarray(X, float), status=np.asarray(status, int),
                 ties="efron", strata=strata, entry=entry)
    return m.fit(groups=np.asarray(groups)) if groups is not None else m.fit()


def hr_table(res, names, front):
    p, se = res.params, res.bse
    out = pd.DataFrame({"covariate": names, "coef": p, "hazard_ratio": np.exp(p),
                        "hr_ci_lo": np.exp(p - 1.96 * se), "hr_ci_hi": np.exp(p + 1.96 * se), "p": res.pvalues})
    for k, v in reversed(list(front.items())):
        out.insert(0, k, v)
    return out


def schoenfeld(res, time, status, names):
    """Grambsch-Therneau tests on three time transforms; also returns the scaled residuals for plotting."""
    S = res.schoenfeld_residuals
    time = np.asarray(time, float)
    status = np.asarray(status, int)
    ev = np.flatnonzero((status == 1) & np.isfinite(S).all(axis=1))
    s = S[ev]
    t = time[ev]
    d = len(ev)
    V = np.asarray(res.cov_params())
    s_scaled = d * s @ V
    kt, ks = km(time, status)
    left = np.searchsorted(kt, t, side="left") - 1  # left-continuous KM, as in cox.zph
    g_km = 1.0 - np.where(left >= 0, ks[np.clip(left, 0, len(ks) - 1)], 1.0)
    transforms = (("km", g_km), ("rank", stats.rankdata(t)), ("identity", t))
    Vinv = np.linalg.inv(V)
    rows = []
    for tname, g in transforms:
        gc = g - g.mean()
        den = float((gc ** 2).sum())
        a_star = gc @ s_scaled
        T = a_star ** 2 / (d * np.diag(V) * den)
        for j, nm in enumerate(names):
            sd = s_scaled[:, j].std()
            corr = float(np.corrcoef(gc, s_scaled[:, j])[0, 1]) if sd > 0 else np.nan
            rows.append({"transform": tname, "covariate": nm, "chi2": float(T[j]), "df": 1,
                         "p": float(stats.chi2.sf(T[j], 1)), "correlation_with_time": f"{corr:.3f}" if np.isfinite(corr) else "",
                         "direction": "hazard ratio falls with time since publication" if a_star[j] < 0
                         else "hazard ratio rises with time since publication"})
        Tg = float(a_star @ Vinv @ a_star / (d * den))
        rows.append({"transform": tname, "covariate": "GLOBAL", "chi2": Tg, "df": len(names),
                     "p": float(stats.chi2.sf(Tg, len(names))), "correlation_with_time": "", "direction": ""})
    return pd.DataFrame(rows), t, s_scaled


def stratified(live, X):
    names = list(X.columns)
    year_cols = [c for c in names if c.startswith("published ")]
    anth, goog = X["any Anthropic model"].values == 1, X["any Google model"].values == 1
    group = np.where(anth & goog, "anthropic+google", np.where(anth, "anthropic", np.where(goog, "google", "openai only")))
    year = live["year"].astype(str).values
    out = []
    g = live["cluster"].values
    Xa = X.drop(columns=year_cols)
    res = fit(live["time"], Xa, live["event"], strata=year, groups=g)
    out.append(hr_table(res, list(Xa.columns), {"model": "baseline hazard per publication year", "strata": len(set(year))}))
    Xb = X.drop(columns=VENDOR_COLS)
    res = fit(live["time"], Xb, live["event"], strata=group, groups=g)
    out.append(hr_table(res, list(Xb.columns), {"model": "baseline hazard per vendor group", "strata": len(set(group))}))
    Xc = X.drop(columns=year_cols + VENDOR_COLS)
    both = np.array([f"{y}|{g_}" for y, g_ in zip(year, group)])
    res = fit(live["time"], Xc, live["event"], strata=both, groups=g)
    out.append(hr_table(res, list(Xc.columns), {"model": "baseline hazard per publication year x vendor group", "strata": len(set(both))}))
    return pd.concat(out, ignore_index=True), group


def episodes(live, X):
    """Counting-process rows: one per paper and follow-up period in which it is at risk."""
    T = live["time"].values.astype(float)
    E = live["event"].values.astype(int)
    C = live["cluster"].values
    parts = []
    for i in range(len(CUTS) - 1):
        lo, hi = CUTS[i], CUTS[i + 1]
        at = T > lo
        part = X[at].copy()
        part["_entry"] = lo
        part["_time"] = np.minimum(T[at], hi)
        part["_event"] = ((T[at] <= hi) & (E[at] == 1)).astype(int)
        part["_period"] = i
        part["_cluster"] = C[at]
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def period_model(live, X):
    long = episodes(live, X)
    cols = [c for c in X.columns if c not in INTERACT]
    Z = long[cols].copy()
    names = list(cols)
    meta = []
    for c in INTERACT:
        for i, lab in enumerate(PERIODS):
            nm = f"{c} | {lab}"
            Z[nm] = long[c].values * (long["_period"].values == i)
            names.append(nm)
            sub = long[long["_period"] == i]
            with_cov = sub[c] > 0 if c != "log(1 + citations)" else sub[c] >= 0
            meta.append({"covariate": nm, "period": lab, "papers_at_risk": int(len(sub)),
                         "events_in_period": int(sub["_event"].sum()),
                         "events_with_covariate": int(sub.loc[with_cov, "_event"].sum()),
                         "at_risk_with_covariate": int(with_cov.sum()) if c != "log(1 + citations)" else int(len(sub))})
    meta = pd.DataFrame(meta)
    # a period-specific term with no variation among the events of its period (no event with the covariate, or every
    # event with it) cannot be estimated and would make the information matrix singular: it is left out of the fit
    drop = []
    for r in meta.itertuples(index=False):
        c0 = r.covariate.split(" | ")[0]
        sep = (r.events_with_covariate == 0 or r.events_with_covariate >= 0.98 * max(r.at_risk_with_covariate, 1)) if c0 in VENDOR_COLS else False
        if Z[r.covariate].nunique() <= 1 or sep:          # (near-)complete separation: the coefficient diverges
            drop.append(r.covariate)
    Zf = Z.drop(columns=drop)
    res = fit(long["_time"], Zf, long["_event"], entry=long["_entry"].values, groups=long["_cluster"].values)
    out = hr_table(res, [n for n in names if n not in drop], {"model": "episode-split, period-specific terms"})
    if drop:
        out = pd.concat([out, pd.DataFrame([{"model": "episode-split, period-specific terms", "covariate": d} for d in drop])], ignore_index=True)
    out = out.merge(meta, on="covariate", how="left")
    for c in ("papers_at_risk", "events_in_period", "events_with_covariate", "at_risk_with_covariate"):
        out[c] = out[c].astype("Int64")
    out["estimable"] = np.where(out["period"].isna(), "", np.where(out["covariate"].isin(drop), "no (complete or near-complete separation: the papers at risk with the covariate almost all had the event in this period)", "yes"))
    return out


def figure(res_main, names, t_ev, s_scaled, period, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Arial", "font.size": 7.5, "axes.linewidth": 0.6,
                         "xtick.major.width": 0.6, "ytick.major.width": 0.6})
    beta = np.asarray(res_main.params)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5), dpi=300)
    edges = np.quantile(t_ev, np.linspace(0, 1, N_BINS + 1))
    which = np.clip(np.searchsorted(edges, t_ev, side="right") - 1, 0, N_BINS - 1)
    tmax = float(t_ev.max())
    titles = ["any Anthropic identifier", "any Google identifier", "log(1 + citations)"]
    for ax, cov, title in zip(axes, INTERACT, titles):
        j = names.index(cov)
        y = beta[j] + s_scaled[:, j]
        xs, ms, lo, hi = [], [], [], []
        for b in range(N_BINS):
            sel = which == b
            if sel.sum() < 20:
                continue
            v = y[sel]
            m, se = v.mean(), v.std(ddof=1) / np.sqrt(sel.sum())
            xs.append(t_ev[sel].mean()); ms.append(m); lo.append(m - 1.96 * se); hi.append(m + 1.96 * se)
        xs, ms, lo, hi = map(np.array, (xs, ms, lo, hi))
        ax.fill_between(xs, np.exp(lo), np.exp(hi), color="#c9d6e8", lw=0, alpha=0.9)
        ax.plot(xs, np.exp(ms), color="#1D2321", lw=0.9)
        ax.axhline(np.exp(beta[j]), color="#1D2321", lw=0.6, ls=(0, (3, 2)))
        sub = period[period["covariate"].str.startswith(cov + " | ")]
        for (_, r), lo_c, hi_c in zip(sub.iterrows(), CUTS[:-1], CUTS[1:]):
            if r["estimable"] != "yes":
                continue
            ax.hlines(r["hazard_ratio"], lo_c, min(hi_c, tmax), color="#b5432e", lw=1.4)
        ax.set_yscale("log")
        ax.axhline(1, color="#8a8f8d", lw=0.5)
        ax.set_title(title, loc="left", fontsize=8)
        ax.set_xlabel("months since publication")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=2.5)
        ticks = [0.5, 1, 2, 4, 8] if cov != "log(1 + citations)" else [0.8, 0.9, 1.0, 1.1, 1.2, 1.4]
        ax.set_yticks(ticks)
        ax.set_yticklabels([f"{v:g}" for v in ticks])
        ax.minorticks_off()
    axes[0].set_ylabel("hazard ratio")
    fig.text(0.01, 0.005, "grey band: binned means of the scaled Schoenfeld residuals (12 bins of equal event count, 95% intervals); "
             "dashed: proportional estimate; red steps: period-specific estimates at 0-6, 6-12, 12-24 and over 24 months",
             fontsize=6.2, color="#444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    from figutil import savefig
    savefig(fig, out_path, bbox_inches="tight")


def main():
    live, X = design()
    names = list(X.columns)
    res = fit(live["time"], X, live["event"], groups=live["cluster"].values)
    d = int(live["event"].sum())
    print(f"main model: n = {len(live):,}, events = {d:,}, clusters = {live['cluster'].nunique()}")

    sch, t_ev, s_scaled = schoenfeld(res, live["time"], live["event"], names)
    sch.to_csv(ROOT / "data" / "cox_schoenfeld.csv", index=False, encoding="utf-8-sig")
    print(sch[sch["transform"] == "km"].round(4).to_string(index=False))

    strat, group = stratified(live, X)
    strat.to_csv(ROOT / "data" / "cox_stratified.csv", index=False, encoding="utf-8-sig")
    print(strat.round(3).to_string(index=False))
    print("vendor groups:", pd.Series(group).value_counts().to_dict())

    period = period_model(live, X)
    period.to_csv(ROOT / "data" / "cox_period_hr.csv", index=False, encoding="utf-8-sig")
    print(period[period["period"].notna()].round(3).to_string(index=False))

    figure(res, names, t_ev, s_scaled, period, ROOT / "figures" / "cox_ph_check.png")
    print("->", ROOT / "figures" / "cox_ph_check.png")


if __name__ == "__main__":
    main()
