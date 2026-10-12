"""Time to loss counted on the identifiers the coders marked as executed (Supplementary Table 46).

The census event is the first retirement among every identifier a paper names, including identifiers mentioned only
in related work. For the 500 manually coded papers the coders recorded a role per identifier (executed / cited or
mentioned / string not found / cannot judge; codebook v1.3, third-coder adjudication), so the event can be recomputed
on the executed identifiers alone. This script compares, for the coded papers judged dependent, the published-date
time to loss under the census rule with the time to loss counted on executed identifiers only, unweighted and
post-stratified to the sampling frame (the 2 September 2026 census, 18 strata, as in Table S8). No API calls.
Output: data/coding_executed_halflife.csv.
"""
import csv
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from census_survival import MONTH, TODAY, build, km, quantile  # noqa: E402
from coding_adjudicate import load, read_decisions, resolve  # noqa: E402
from coding_main_report import frame_sizes  # noqa: E402


def summarise(times, weights=None):
    t = np.asarray(times, float)
    if not len(t):
        return {"median_months": None, "q25_months": None, "q75_months": None}
    ts, s = km(t, np.ones(len(t), int), None if weights is None else np.asarray(weights, float))
    return {"median_months": quantile(ts, s, 0.5), "q25_months": quantile(ts, s, 0.25), "q75_months": quantile(ts, s, 0.75)}


def main():
    data, sample, _ = load(ROOT / "coding" / "results_main")
    recs = resolve(data, sample, read_decisions())
    census = build()[0]
    census["openalex_id"] = census["openalex_id"].astype(str).str.rsplit("/", n=1).str[-1]
    census = census.set_index("openalex_id")
    sizes = frame_sizes()
    sample_n = Counter(sample[w]["stratum"] for w in sample)
    weight = {st: sizes[st] / sample_n[st] for st in sample_n if sample_n[st]}

    rows_out, per_paper = [], []
    n_dep = n_missing = 0
    for wid, rec in recs.items():
        if rec.get("dependence") != "의존":
            continue
        n_dep += 1
        if wid not in census.index:
            n_missing += 1
            continue
        c = census.loc[wid]
        events = {}
        for tok in str(c["events"]).split("|"):
            if ":" in tok:
                m, d = tok.split(":", 1)
                events[m] = date.fromisoformat(d)
        executed = [m for m, code in rec["roles"].items() if code == "실행"]
        ex_dates = [events[m] for m in executed if m in events]
        origin = c["pub"]
        per_paper.append({"openalex_id": wid, "stratum": sample[wid]["stratum"], "w": weight.get(sample[wid]["stratum"], 1.0),
                          "origin": origin, "census_event": c["first_shutdown"], "executed_ids": "|".join(executed),
                          "executed_event": min(ex_dates) if ex_dates else None,
                          "executed_without_date": "|".join(m for m in executed if m not in events)})
    pp = pd.DataFrame(per_paper)
    pp.to_csv(ROOT / "data" / "coding" / "executed_events.csv", index=False, encoding="utf-8-sig")

    for rule, col in (("first retirement among every named identifier (census rule)", "census_event"),
                      ("first retirement among the identifiers coded as executed", "executed_event")):
        d = pp[pp[col].notna()].copy()
        no_event = int(pp[col].isna().sum())
        d["t"] = [(e - o).days / MONTH for e, o in zip(d[col], d["origin"])]
        bd = d[d["t"] <= 0]
        live = d[d["t"] > 0]
        base = {"rule": rule, "dependent_papers": len(pp), "no_dated_event": no_event, "born_dead": len(bd), "in_curve": len(live),
                "pct_lost_by_today": round(100 * float((live[col] <= TODAY).mean()), 1) if len(live) else None}
        rows_out.append({**base, "weighting": "unweighted", **summarise(live["t"])})
        rows_out.append({**base, "weighting": "post-stratified to the sampling frame", **summarise(live["t"], live["w"])})
    both = pp[pp["executed_event"].notna()]
    later = int((both["executed_event"] > both["census_event"]).sum())
    same = int((both["executed_event"] == both["census_event"]).sum())
    rows_out.append({"rule": "comparison on papers with both events", "dependent_papers": len(both), "no_dated_event": None, "born_dead": None,
                     "in_curve": None, "pct_lost_by_today": None, "weighting": f"executed-only event later than the census event in {later} papers, identical in {same}",
                     "median_months": None, "q25_months": None, "q75_months": None})
    out = pd.DataFrame(rows_out)
    out.to_csv(ROOT / "data" / "coding_executed_halflife.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 250, "display.max_colwidth", 80):
        print(out.to_string(index=False))
    print(f"dependent papers {n_dep}, not in the current census {n_missing}, executed identifiers without a dated event: "
          f"{int((pp['executed_without_date'] != '').sum())} papers")
    print("-> data/coding_executed_halflife.csv")


if __name__ == "__main__":
    main()
