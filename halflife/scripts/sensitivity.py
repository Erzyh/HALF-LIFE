"""Sensitivity of the census survival results and of the Tier B provisional classes to the analysis choices.

Survival variants (all from data/census_v2.csv through census_survival.build/analyse; the base is the published-date
estimand with the corrected origins):
  the as-of Kaplan-Meier curve censored at the analysis date (the estimand of the earlier versions) and one censored the
  day after the 23 October 2026 retirements; year-only dates kept at 1 January or set to 31 December; no origin
  correction at the release date, or those papers dropped; the dateless aliases read 4, 8 and 13 months before
  publication and at their earliest snapshot; the gpt-4-turbo alias rule off / unresolved window read as retired /
  lag windows 0 and 6 months; born-dead papers kept as events at 0 months; journal articles, preprints and conference
  papers only; citation-weighted; papers with at least 10 citations; one field left out at a time; single-vendor
  papers; preview identifiers removed; and the census as it stood under each earlier vocabulary (the archived files),
  analysed with the current rules and retirement dates.
Tier B variants (from runs/tierb/batch1_tierb_summary.json): class thresholds 1/3, 2/5 (base), 3/10 points,
  CI-only, points-only; and subset runs (cost cap) versus full runs.

Outputs: data/sensitivity_survival.csv, data/sensitivity_tierb.csv, figures/sensitivity.png. No API calls.
"""
import json, sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from census_survival import GA, LAG, TODAY, analyse, build  # noqa: E402

VOCABULARIES = [("census_v2_2026-09-02.csv", "vocabulary of 2 September 2026 (55 identifiers)"),
                ("census_v2_2026-10-11-pre.csv", "vocabulary of 2 October 2026 (75 identifiers)"),
                ("census_v2_2026-10-12-pre.csv", "vocabulary of 11 October 2026 (81 identifiers)")]


def survival_variants():
    base, alias, _, _ = build()
    rows, curves = [], {}

    def add(name, d, known=True, **kw):
        stats, (t, s) = analyse(d, "first_shutdown", known=known, **kw)
        row = {"variant": name, **{k: stats[k] for k in ("n_curve", "born_dead", "pct_dead_today", "pct_lost_by_2026_end", "median_months", "q25_months", "q75_months")}}
        for v in ("openai", "anthropic", "google"):
            row[f"median_{v}"] = analyse(d, f"sd_{v}", known=known, **kw)[0]["median_months"]
        rows.append(row)
        curves[name] = (t, s)

    add("base (published retirement dates; year-only dates at 1 July; origin no earlier than the release; aliases read at publication)", base)
    add("as-of Kaplan-Meier censored at 2026-10-12 (the estimand of the earlier versions)", base, known=False)
    add("as-of Kaplan-Meier censored at 2026-10-24, the day after the 23 October retirements", base, known=False, today=date(2026, 10, 24))
    add("year-only dates kept at 1 January (as OpenAlex prints them)", build(yearonly="jan1")[0])
    add("year-only dates set to 31 December", build(yearonly="dec31")[0])
    add("no origin correction (papers dated before the release keep their indexed date)", build(truncate="none")[0])
    add("papers dated before the release of the first-retiring identifier dropped", build(truncate="drop")[0])
    add("dateless aliases read 4 months before publication", build(alias_lag_months=4)[0])
    add("dateless aliases read 8 months before publication (the median lag from release to publication)", build(alias_lag_months=8)[0])
    add("dateless aliases read 13 months before publication", build(alias_lag_months=13)[0])
    add("dateless aliases read as their earliest snapshot (bound)", build(alias_lag_months=36)[0])
    add("gpt-4-turbo alias rule off (every gpt-4-turbo = live snapshot)", build(alias_rule=False)[0])
    add("gpt-4-turbo unresolved window read as retired previews", build(unresolved="dead")[0])
    add("gpt-4-turbo lag window 0 (every alias after GA = live snapshot)", build(lag=GA)[0])
    add("gpt-4-turbo lag window 6 months, unresolved read as retired previews", build(lag=date(2024, 10, 9), unresolved="dead")[0])
    add("born-dead papers kept as events at 0 months", base, include_born_dead=True)
    add("journal articles only", base[base["type"] == "article"])
    add("preprints only", base[base["type"] == "preprint"])
    add("conference papers only", base[base["type"] == "conference-paper"])
    base = base.assign(w=base["citations"].fillna(0).astype(float) + 1.0)
    add("citation-weighted (weight = citations + 1)", base, weights="w")
    add("papers with at least 10 citations", base[base["citations"].fillna(0) >= 10])
    for f in ("Computer Science", "Medicine", "Social Sciences"):
        add(f"field {f} left out", base[base["field"] != f])
    add("single-vendor papers only", base[~base["vendors"].str.contains("|", regex=False)])
    tm = json.load(open(ROOT / "target_models.json", encoding="utf-8"))["models"]
    preview = {m["id"] for m in tm if "preview" in m["id"] or "-exp" in m["id"] or m["id"].endswith("exp")}
    add(f"preview and experimental identifiers removed from every paper ({len(preview)} identifiers)", build(exclude_ids=preview)[0])
    cen = pd.read_csv(ROOT / "data" / "census_v2.csv", low_memory=False, usecols=["openalex_id", "matched_models"])
    any_prev = set(cen.loc[cen["matched_models"].astype(str).apply(lambda s: any(x in preview for x in s.split("|"))), "openalex_id"])
    add("papers naming any preview or experimental identifier left out", base[~base["openalex_id"].isin(any_prev)])
    for fn, label in VOCABULARIES:
        p = ROOT / "data" / fn
        if p.exists():
            add(f"census under the {label}, current rules and dates", build(census_path=p)[0])
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "data" / "sensitivity_survival.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 250, "display.max_colwidth", 70):
        print(out.to_string(index=False))
    return out, curves


def tierb_variants():
    rows = json.load(open(ROOT / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8"))
    subset = {}
    for r in rows:
        p = ROOT / "runs" / "tierb" / r["wid"] / "prepare.json"
        note = json.loads(p.read_text(encoding="utf-8")).get("subset_note") if p.exists() else None
        subset[r["wid"]] = bool(note)

    def classify(r, lo, hi, use_ci=True, use_pts=True, max_hw=None):
        if r.get("class_provisional", r["class"]) == "확인 필요":
            return "needs review"
        d = r["delta_pts"]
        inside = bool(r["inside"]) if use_ci else False
        if inside and max_hw is not None:          # the CI clause counts only when the interval is precise enough
            hw = r.get("ci_halfwidth_pts")
            inside = hw is not None and hw <= max_hw
        if inside or (use_pts and d is not None and abs(d) <= lo):
            return "reproduced"
        if use_pts and d is not None and abs(d) <= hi:
            return "close"
        if not use_pts:
            return "reproduced" if inside else "deviated"
        return "deviated"

    variants = [("base: |d| <= 2 or inside CI / <= 5", dict(lo=2, hi=5)),
                ("stricter: |d| <= 1 or inside CI / <= 3", dict(lo=1, hi=3)),
                ("looser: |d| <= 3 or inside CI / <= 10", dict(lo=3, hi=10)),
                ("CI only (inside CI = reproduced, else deviated)", dict(lo=0, hi=0, use_pts=False)),
                ("points only, CI ignored: <= 2 / <= 5", dict(lo=2, hi=5, use_ci=False)),
                ("base rule, CI clause only when CI half-width <= 10 points", dict(lo=2, hi=5, max_hw=10)),
                ("base rule, CI clause only when CI half-width <= 5 points", dict(lo=2, hi=5, max_hw=5))]
    out = []
    for name, kw in variants:
        c = {"reproduced": 0, "close": 0, "deviated": 0, "needs review": 0}
        for r in rows:
            c[classify(r, **kw)] += 1
        out.append({"variant": name, "n": len(rows), **c})
    for label, flag in (("cost-cap subset runs", True), ("full-set runs", False)):
        c = {"reproduced": 0, "close": 0, "deviated": 0, "needs review": 0}
        sel = [r for r in rows if subset[r["wid"]] == flag]
        for r in sel:
            c[classify(r, lo=2, hi=5)] += 1
        out.append({"variant": f"base rule, {label}", "n": len(sel), **c})
    for label, flag in (("low-precision runs (CI half-width > 10 points)", True), ("precise runs (CI half-width <= 10 points)", False)):
        c = {"reproduced": 0, "close": 0, "deviated": 0, "needs review": 0}
        sel = [r for r in rows if bool(r.get("low_precision")) == flag]
        for r in sel:
            c[classify(r, lo=2, hi=5)] += 1
        out.append({"variant": f"base rule, {label}", "n": len(sel), **c})
    df = pd.DataFrame(out)
    df.to_csv(ROOT / "data" / "sensitivity_tierb.csv", index=False, encoding="utf-8-sig")
    print(df.to_string(index=False))
    return df


def main():
    surv, curves = survival_variants()
    tierb_variants()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from figstyle import apply, panel, VENDOR, SERIES, BLUE, BLUE_LIGHT, ORANGE, GREY, DARK  # noqa: F401
    apply()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.2), dpi=200, gridspec_kw={"width_ratios": [1.0, 1.25], "wspace": 1.1})
    names = list(surv["variant"])
    show = [names[0], names[1], names[3], names[5], names[8], names[15]]
    short = ["base (published dates)", "as-of Kaplan-Meier, 12 Oct 2026", "year-only dates at 1 January", "no origin correction",
             "aliases read 8 months earlier", "born-dead kept as events at 0"]
    for nm, lb in zip(show, short):
        t, s = curves[nm]
        ax1.step(t, s, where="post", lw=1.0, label=lb)
    ax1.set_xlim(0, 48)
    ax1.set_ylim(0, 1.02)
    ax1.set_xlabel("months since publication")
    ax1.set_ylabel("share of papers whose named\nmodel is still callable")
    ax1.legend(loc="upper right", fontsize=5.8)
    panel(ax1, "a", x=-0.18)
    med = surv.set_index("variant")["median_months"]
    labels = {n: n for n in names}
    labels.update({names[0]: "base (published dates)", names[1]: "as-of KM, censored 12 Oct 2026", names[2]: "as-of KM, censored 24 Oct 2026",
                   names[3]: "year-only dates at 1 January", names[4]: "year-only dates at 31 December", names[5]: "no origin correction",
                   names[6]: "papers dated before the release dropped", names[7]: "aliases read 4 months earlier", names[8]: "aliases read 8 months earlier",
                   names[9]: "aliases read 13 months earlier", names[10]: "aliases at the earliest snapshot", names[11]: "gpt-4-turbo rule off",
                   names[12]: "gpt-4-turbo unresolved = retired", names[13]: "gpt-4-turbo lag window 0", names[14]: "gpt-4-turbo lag window 6 months",
                   names[15]: "born-dead kept as events at 0", names[19]: "citation-weighted", names[20]: "at least 10 citations", names[24]: "single-vendor papers only"})
    for n in names:
        if n.startswith("census under the"):
            labels[n] = n.split("under the ")[1].split(", current")[0]
        elif n.startswith("preview and experimental identifiers removed"):
            labels[n] = "preview identifiers removed"
        elif n.startswith("papers naming any preview"):
            labels[n] = "papers naming previews left out"
    ax2.barh(range(len(names))[::-1], [med[n] if med[n] is not None and not pd.isna(med[n]) else 0 for n in names], color=BLUE, height=0.65)
    panel(ax2, "b", x=-1.05)
    ax2.set_yticks(range(len(names))[::-1])
    ax2.set_yticklabels([labels.get(n, n) for n in names], fontsize=5.6)
    ax2.set_xlabel("median months to the first retirement")
    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.tight_layout()
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "sensitivity.png", bbox_inches="tight")
    print("->", ROOT / "figures" / "sensitivity.png")


if __name__ == "__main__":
    main()
