"""Census survival analysis: time from publication to the retirement of the first model a paper names.

Reads data/census_v2.csv (papers with a persistent identifier) and target_models.json. Two estimands:

  known-date (primary since 2026-10-12): the event is the vendor's published retirement date of the identifier that
    retires first. Every identifier in this census has such a date, so no paper is censored; the curve is the empirical
    distribution of (retirement - origin) and its median is the median time to loss.
  as-of (secondary): Kaplan-Meier with censoring at TODAY, i.e. what had been lost by the analysis date.

Origin: the publication date, with two corrections.
  (a) OpenAlex prints a year-only date as 1 January; those origins are set to 1 July of the year ('date_yearonly').
      Sensitivity: keep 1 January, or use 31 December.
  (b) A paper dated before the release of the identifier that retires first starts its time at risk at that release
      ('truncated'): the indexed date then belongs to a version that predates the model. Sensitivity: no truncation,
      or dropping those papers.
Dateless aliases: gpt-3.5-turbo, gpt-4o and gpt-4-turbo are resolved here by the paper's date (the snapshot the alias
pointed to then; gpt-4-turbo before the 2024-04-09 GA means the retired previews); the aliases added on 2026-10-12
(gpt-5 family, Claude 4 family, claude-instant, gpt-4-turbo-preview, gemini-pro-vision) were resolved at fold-in by
scripts/census_refresh3.py and carry their own retirement date. `alias_lag_months` reads the alias as of some months
before publication (runs precede publication; Table S43), for the sensitivity analysis.
Papers whose first-retiring model was already gone at the origin ("born dead") are counted and left out of the curves.

build() and analyse() are imported by sensitivity.py, cox_model.py, cox_checks.py, km_median_ci.py, release_lag.py
and supp_tables.py.

Outputs: data/census_survival_summary.csv (one row per group: known-date and as-of statistics side by side),
data/census_survival_curves.csv, figures/census_survival.png. No API calls.
"""
import json, re, sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
TODAY = date(2026, 10, 12)   # analysis date: the third vocabulary refresh (harvest of 2026-10-12); earlier runs used 2026-09-15 and 2026-10-11
END_2026 = date(2026, 12, 31)
GA, LAG = date(2024, 4, 9), date(2024, 7, 1)
GPT35_0613, GPT35_1106, GPT35_0125, GPT4O_MOVED = date(2023, 6, 13), date(2023, 12, 11), date(2024, 2, 16), date(2024, 10, 2)   # alias switch dates (0301 and 0613 retired together on 2024-09-13)
PREVIEW_SHUTDOWN = date(2026, 3, 26)
MONTH = 30.4375


def parse_date(s):
    """Date of a YYYY[-MM[-DD]] string as printed: a missing month gives 1 July, a missing day the 15th (used by the
    other scripts for retirement and release dates)."""
    m = re.match(r"([0-9]{4})(?:-([0-9]{2}))?(?:-([0-9]{2}))?", str(s))
    if not m:
        return None
    y, mo, d = int(m.group(1)), m.group(2), m.group(3)
    if mo is None:
        return date(y, 7, 1)
    return date(y, int(mo), int(d) if d else 15)


def parse_origin(s, yearonly="mid"):
    """(date, year_only) for a publication date. A year-only record (OpenAlex prints 1 January) is placed at 1 July
    ('mid'), kept at 1 January ('jan1') or set to 31 December ('dec31'); a month-only record at the 15th."""
    m = re.match(r"([0-9]{4})(?:-([0-9]{2}))?(?:-([0-9]{2}))?", str(s))
    if not m:
        return None, False
    y, mo, d = int(m.group(1)), m.group(2), m.group(3)
    if mo is None or (mo == "01" and d == "01"):
        return {"mid": date(y, 7, 1), "jan1": date(y, 1, 1), "dec31": date(y, 12, 31)}[yearonly], True
    return date(y, int(mo), int(d) if d else 15), False


def release_dates(tm):
    """Release date per identifier: the 'release' field of target_models.json, else the date embedded in the identifier,
    else the announcement table of lifecycle_figure.py."""
    from lifecycle_figure import RELEASE, embedded_date
    out = {}
    for m in tm:
        r = m.get("release")
        if r:
            out[m["id"]] = date.fromisoformat(r[:10])
            continue
        d = embedded_date(m["id"])
        if d is None and m["id"] in RELEASE:
            d = date.fromisoformat(RELEASE[m["id"]])
        out[m["id"]] = d
    return out


def km(durations, events, weights=None):
    """Kaplan-Meier step function: (times, survival). With every event observed it is the empirical survival function.
    Optional weights give a weighted estimator."""
    order = np.argsort(durations, kind="stable")
    t, e = np.asarray(durations, float)[order], np.asarray(events, int)[order]
    w = np.ones(len(t)) if weights is None else np.asarray(weights, float)[order]
    n = len(t)
    s, i = 1.0, 0
    at_risk = float(w.sum())
    times, surv = [0.0], [1.0]
    while i < n:
        j = i
        while j < n and t[j] == t[i]:
            j += 1
        d = float((e[i:j] * w[i:j]).sum())
        if d > 0 and at_risk > 0:
            s *= 1 - d / at_risk
            times.append(float(t[i]))
            surv.append(s)
        at_risk -= float(w[i:j].sum())
        i = j
    return np.array(times), np.array(surv)


def quantile(times, surv, q):
    idx = np.where(surv <= 1 - q)[0]
    return round(float(times[idx[0]]), 1) if len(idx) else None


def build(lag=LAG, unresolved="alive", alias_rule=True, exclude_ids=None, yearonly="mid", truncate="release",
          alias_lag_months=0, census_path=None, models_path=None):
    """One row per census paper with the first retirement among its matched identifiers.

    lag / unresolved / alias_rule: the gpt-4-turbo alias rule (see module docstring); exclude_ids: identifiers ignored
    in every paper; yearonly: where a year-only date is placed; truncate: 'release' (origin no earlier than the release
    of the first-retiring identifier), 'none', or 'drop' (such papers leave the census); alias_lag_months: the dateless
    aliases are read as of this many months before the publication date; census_path / models_path: other files (the
    archived censuses of earlier vocabularies, for the sensitivity analysis).
    Returns (DataFrame, alias Counter, unknown-id Counter, papers without an exact date)."""
    tm = json.load(open(models_path or ROOT / "target_models.json", encoding="utf-8"))["models"]
    shut = {m["id"]: parse_date(m["shutdown"]) for m in tm}
    vendor = {m["id"]: m["vendor"] for m in tm}
    rel = release_dates(tm)
    df = pd.read_csv(census_path or ROOT / "data" / "census_v2.csv", low_memory=False)
    alias, unknown = Counter(), Counter()
    missing_date = 0
    rows = []
    for r in df.itertuples(index=False):
        pub, yo = parse_origin(r.date, yearonly) if isinstance(r.date, str) else (None, False)
        if pub is None:
            missing_date += 1
            pub, yo = parse_origin(str(int(r.year)), yearonly)
        pub_alias = pub - timedelta(days=round(alias_lag_months * MONTH)) if alias_lag_months else pub
        models = [m for m in str(r.matched_models).split("|") if m and m != "nan"]
        ev = []
        for m in models:
            if m not in shut:
                unknown[m] += 1
                continue
            if exclude_ids and m in exclude_ids:
                continue
            sd, rl = shut[m], rel.get(m)
            if m == "gpt-3.5-turbo":            # dateless alias: a dated 3.5 snapshot in the paper decides
                if any(x.startswith("gpt-3.5-turbo-") for x in models):
                    continue
                if pub_alias < GPT35_0613:
                    sd, rl = shut["gpt-3.5-turbo-0301"], rel["gpt-3.5-turbo-0301"]; alias["gpt-3.5-turbo -> 0301 (before 13 Jun 2023)"] += 1
                elif pub_alias < GPT35_1106:
                    sd, rl = shut["gpt-3.5-turbo-0613"], rel["gpt-3.5-turbo-0613"]; alias["gpt-3.5-turbo -> 0613 (13 Jun to 10 Dec 2023)"] += 1
                elif pub_alias < GPT35_0125:
                    sd, rl = shut["gpt-3.5-turbo-1106"], rel["gpt-3.5-turbo-1106"]; alias["gpt-3.5-turbo -> 1106 (11 Dec 2023 to 15 Feb 2024)"] += 1
                else:
                    sd, rl = shut["gpt-3.5-turbo-0125"], rel["gpt-3.5-turbo-0125"]; alias["gpt-3.5-turbo -> 0125 (from 16 Feb 2024)"] += 1
            elif m == "gpt-4o":                 # dateless alias: a dated gpt-4o snapshot decides; the alias moved on 2 Oct 2024
                if any(x.startswith("gpt-4o-2024-") for x in models):
                    continue
                if pub_alias < GPT4O_MOVED:
                    sd, rl = shut["gpt-4o-2024-05-13"], rel["gpt-4o-2024-05-13"]; alias["gpt-4o -> 2024-05-13 (before 2 Oct 2024)"] += 1
                else:
                    alias["gpt-4o -> still-served snapshot, dropped"] += 1
                    continue
            if m == "gpt-4-turbo" and alias_rule:
                if "gpt-4-turbo-2024-04-09" in models:
                    alias["dated snapshot named"] += 1
                elif pub_alias < GA:
                    sd, rl = PREVIEW_SHUTDOWN, rel["gpt-4-1106-preview"]
                    alias["dead preview (paper dated before GA)"] += 1
                elif pub_alias < lag:
                    alias["unresolved (within the lag window)"] += 1
                    if unresolved == "dead":
                        sd, rl = PREVIEW_SHUTDOWN, rel["gpt-4-1106-preview"]
                else:
                    alias["post-GA alias"] += 1
            ev.append((sd, m, rl))
        if not ev:
            continue
        first_sd, first_m, first_rl = min(ev, key=lambda x: (x[0], x[1]))
        truncated = bool(first_rl and pub < first_rl)
        if truncated and truncate == "drop":
            continue
        origin = max(pub, first_rl) if (truncated and truncate == "release") else pub
        by_vendor = {}
        for sd, m, rl in ev:
            v = vendor[m]
            if v not in by_vendor or (sd, m) < (by_vendor[v][0], by_vendor[v][2]):
                by_vendor[v] = (sd, rl, m)
        row = {"openalex_id": r.openalex_id, "pub": origin, "pub_raw": pub, "date_yearonly": yo, "truncated": truncated,
               "year": int(r.year), "field": r.field if isinstance(r.field, str) else "Unknown",
               "type": r.type, "citations": r.citations, "n_models": len(ev), "first_model": first_m, "release_first": first_rl,
               "vendors": "|".join(sorted(by_vendor)), "first_shutdown": first_sd, "last_shutdown": max(sd for sd, _, _ in ev),
               "events": "|".join(f"{m}:{sd.isoformat()}" for sd, m, _ in sorted(ev, key=lambda x: (x[0], x[1])))}
        for v in ("openai", "anthropic", "google"):
            sd_rl = by_vendor.get(v)
            row[f"sd_{v}"] = sd_rl[0] if sd_rl else None
            row[f"fm_{v}"] = sd_rl[2] if sd_rl else None
            o = pub
            if sd_rl and sd_rl[1] and pub < sd_rl[1] and truncate == "release":
                o = sd_rl[1]
            row[f"org_{v}"] = o if sd_rl else None
        rows.append(row)
    return pd.DataFrame(rows), alias, unknown, missing_date


def origin_col(col):
    return f"org_{col[3:]}" if col.startswith("sd_") else "pub"


def analyse(sub, col="first_shutdown", today=TODAY, include_born_dead=False, weights=None, known=True):
    """Summary for one group. Born-dead papers (retirement on or before the origin) are excluded unless include_born_dead,
    in which case they enter as events at 0 months. known=True: the published retirement date is the event for every
    paper (no censoring); known=False: Kaplan-Meier censored at `today`. `weights` names a column."""
    oc = origin_col(col)
    if oc not in sub.columns:          # rows built elsewhere (census_extension.py) carry the publication date only
        oc = "pub"
    sub = sub[sub[col].notna()]
    org = sub[oc]
    born_dead = sub[sub[col] <= org]
    live = sub if include_born_dead else sub[sub[col] > org]
    org_l = live[oc]
    if known:
        dur = np.array([max(0.0, (sd - p).days / MONTH) for sd, p in zip(live[col], org_l)])
        evt = np.ones(len(dur), int)
    else:
        dur = np.array([max(0.0, (min(sd, today) - p).days / MONTH) for sd, p in zip(live[col], org_l)])
        evt = np.array([sd <= today for sd in live[col]], int)
    w = None if weights is None else np.asarray(live[weights], float)
    t, s = km(dur, evt, w)
    lost_today = np.array([sd <= today for sd in live[col]])
    lost_2026 = np.array([sd <= END_2026 for sd in live[col]])
    stats = {"n_named": len(sub), "born_dead": len(born_dead), "n_curve": len(live),
             "dead_by_today": int(lost_today.sum()), "pct_dead_today": round(100 * lost_today.mean(), 1) if len(live) else None,
             "pct_lost_by_2026_end": round(100 * lost_2026.mean(), 1) if len(live) else None,
             "median_months": quantile(t, s, 0.5), "q25_months": quantile(t, s, 0.25), "q75_months": quantile(t, s, 0.75),
             "all_gone_by": max(sub[col]).isoformat() if len(sub) else None,
             "n_date_yearonly": int(live["date_yearonly"].sum()) if "date_yearonly" in live else None,
             "n_truncated": int(live["truncated"].sum()) if "truncated" in live else None,
             "estimand": "published retirement dates" if known else f"Kaplan-Meier censored at {today.isoformat()}"}
    return stats, (t, s)


def both(sub, col, **kw):
    """Known-date statistics with the as-of Kaplan-Meier median beside them."""
    stats, curve = analyse(sub, col, known=True, **kw)
    asof, curve_asof = analyse(sub, col, known=False, **kw)
    stats = {k: v for k, v in stats.items() if k != "estimand"}
    stats.update({"km_median_months": asof["median_months"], "km_q25_months": asof["q25_months"], "km_q75_months": asof["q75_months"]})
    return stats, curve, curve_asof


def main():
    d, alias, unknown, missing_date = build()
    print(f"papers with a known model {len(d)}, missing exact date {missing_date}, year-only dates {int(d.date_yearonly.sum())}, "
          f"origins moved to the release date {int(d.truncated.sum())}")
    print("unknown ids:", dict(unknown))
    print("dateless alias rules:", dict(alias))

    groups = [("all", d, "first_shutdown")]
    for v in ("openai", "anthropic", "google"):
        groups.append((f"vendor:{v}", d, f"sd_{v}"))
    for f, _ in d["field"].value_counts().head(8).items():
        groups.append((f"field:{f}", d[d["field"] == f], "first_shutdown"))
    for y in sorted(d["year"].unique()):
        groups.append((f"year:{y}", d[d["year"] == y], "first_shutdown"))
    for ty in ("article", "preprint", "conference-paper"):
        groups.append((f"type:{ty}", d[d["type"] == ty], "first_shutdown"))
    summary, curves = [], []
    for name, sub, col in groups:
        stats, (t, s), (ta, sa) = both(sub, col)
        summary.append({"group": name, **stats})
        curves.extend({"group": name, "months": round(float(a), 2), "surviving": round(float(b), 5)} for a, b in zip(t, s))
        curves.extend({"group": f"asof:{name}", "months": round(float(a), 2), "surviving": round(float(b), 5)} for a, b in zip(ta, sa))
    summ = pd.DataFrame(summary)
    summ.to_csv(ROOT / "data" / "census_survival_summary.csv", index=False, encoding="utf-8-sig")
    cur = pd.DataFrame(curves)
    cur.to_csv(ROOT / "data" / "census_survival_curves.csv", index=False, encoding="utf-8-sig")
    print(summ.drop(columns=["all_gone_by"]).to_string(index=False))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from figstyle import apply, panel, VENDOR, SERIES, BLUE, BLUE_LIGHT, ORANGE, GREY, DARK  # noqa: F401
    apply()
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3), dpi=200, sharey=True)
    n_of = {x["group"]: x["n_curve"] for x in summary}

    def draw(ax, names, labels, colors=None):
        for k, (nm, lb) in enumerate(zip(names, labels)):
            c = cur[cur["group"] == nm]
            ax.step(c["months"], c["surviving"], where="post", lw=1.0, label=lb,
                    color=None if colors is None else colors[k])
        ax.set_xlim(0, 48)
        ax.set_ylim(0, 1.02)
        ax.set_xlabel("months since publication")
        ax.legend(loc="upper right", fontsize=6.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    vend = ["vendor:openai", "vendor:anthropic", "vendor:google"]
    names = {"openai": "OpenAI", "anthropic": "Anthropic", "google": "Google"}
    draw(axes[0], vend, [f"{names[v.split(':')[1]]} (n={n_of[v]:,})" for v in vend], [VENDOR["openai"], VENDOR["anthropic"], VENDOR["google"]])
    axes[0].set_ylabel("share of papers whose named model\nis still callable (published dates)")
    axes[0].set_title("by vendor of the named model")
    panel(axes[0], "a", x=-0.2)
    flds = [g for g in cur["group"].unique() if g.startswith("field:")][:6]
    draw(axes[1], flds, [f"{g.split(':')[1]} (n={n_of[g]:,})" for g in flds])
    axes[1].set_title("by field (six largest)")
    panel(axes[1], "b")
    yrs = [g for g in cur["group"].unique() if g.startswith("year:") and g.split(":")[1] in ("2022", "2023", "2024", "2025", "2026")]
    draw(axes[2], yrs, [f"published {g.split(':')[1]} (n={n_of[g]:,})" for g in yrs])
    axes[2].set_title("by publication year")
    panel(axes[2], "c")
    fig.tight_layout()
    (ROOT / "figures").mkdir(exist_ok=True)
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "census_survival.png", bbox_inches="tight")
    print("->", ROOT / "figures" / "census_survival.png")


if __name__ == "__main__":
    main()
