"""Main-sample coding: paper-level dependence, by-stratum shares, post-stratified census correction, Q items (P1).

python scripts/coding_main_report.py [--dir coding/results_main] [--decisions coding/adjudication_main_decisions.csv]
  reads  the four coders' workbooks, data/coding/sample_v1.csv (strata), data/census_v2_2026-09-02.csv (the sampling frame,
         English-metadata papers of the 2 September census, for the stratum weights), coding/merge_main.json (agreement, from coding_merge.py)
         and, when present, the third-coder decisions
  applies the codebook's merge rules (coding_adjudicate.resolve) and the decisions
  writes data/coding/main_summary.json, data/coding/main_papers.csv (one row per paper),
         data/coding_main_summary.csv (Supplementary Table 8: item, value; includes the by-stratum shares)
Papers still pending a third coder are reported as such and excluded from the shares (bounds are given).
No API calls.
"""
import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from coding_adjudicate import QS, load, read_decisions, resolve  # noqa: E402
from coding_sample import GROUP  # noqa: E402

def _census_denominators():
    """Census papers and papers in the survival curve, from data/census_survival_summary.csv (group 'all', written by
    scripts/census_survival.py, which runs before this script in check_regeneration.py)."""
    import pandas as _pd
    t = _pd.read_csv(ROOT / "data" / "census_survival_summary.csv", encoding="utf-8-sig")
    row = t[t["group"] == "all"].iloc[0]
    return int(row["n_named"]), int(row["n_curve"])


CENSUS_ALL, CURVE_N = _census_denominators()  # denominators used in the manuscript (census; papers in the survival curve)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


FRAME = ROOT / "data" / "census_v2_2026-09-02.csv"  # the census the sample was drawn from (coding_sample.py, 5 September)


def frame_sizes(path=FRAME):
    rows = csv.DictReader(open(path, encoding="utf-8-sig"))
    sizes = Counter()
    for r in rows:
        if r["language"] in ("en", ""):
            sizes[f"{r['statuses']}|{GROUP.get(r['field'], 'ENG' if r['field'] else 'UNK')}"] += 1
    return sizes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "coding" / "results_main"))
    ap.add_argument("--decisions", default=str(ROOT / "coding" / "adjudication_main_decisions.csv"))
    a = ap.parse_args()
    data, sample, third = load(a.dir)
    decisions = read_decisions(a.decisions)
    recs = resolve(data, sample, decisions)
    target = json.load(open(ROOT / "target_models.json", encoding="utf-8"))["models"]
    listed = {m["id"].lower() for m in target}

    # ---- paper table
    rows = []
    for wid, rec in recs.items():
        s = sample[wid]
        models = {}
        for c, m in rec["models"].items():
            names = [x.strip() for x in re.split(r"[,\n;]+", m) if x.strip()]
            if names:
                models[c] = names
        rows.append({"num": rec["num"], "openalex_id": wid, "stratum": s["stratum"], "statuses": s["statuses"], "group": s["group"], "year": s["year"],
                     "coders": "".join(rec["coders"]), **{f"verdict_{c}": rec["verdicts"].get(c, "") or "" for c in "ABCD"},
                     "dependence": rec["dependence"] or "", "how": rec["how"], "pending_units": len(rec["pending"]),
                     "Q1": rec["q"].get(QS[0]) or "", "Q2": rec["q"].get(QS[1]) or "", "Q3": rec["q"].get(QS[2]) or "",
                     "Q2_snapshot_any": int(any(data[c][wid][QS[1]] == "날짜 스냅숏" for c in rec["coders"])),
                     "Q3_date_any": int(any(data[c][wid][QS[2]] in ("연월", "연도만") for c in rec["coders"])),
                     "Q1_webui_any": int(any(data[c][wid][QS[0]] in ("웹UI", "혼합") for c in rec["coders"])),
                     "models_named": round(sum(len(v) for v in models.values()) / len(models), 1) if models else "",
                     "outside_list": int(any(n.lower() not in listed for v in models.values() for n in v)) if models else ""})
    (ROOT / "data" / "coding").mkdir(parents=True, exist_ok=True)
    with open(ROOT / "data" / "coding" / "main_papers.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["num"] or 0))

    # ---- dependence overall, bounds, by stratum
    decided = [r for r in rows if r["dependence"] in ("의존", "비의존")]
    pend = [r for r in rows if r["how"] == "pending"]
    unopened = [r for r in rows if r["how"] == "both_unopened"]
    k, n = sum(1 for r in decided if r["dependence"] == "의존"), len(decided)
    share = {"dependent": k, "decided": n, "share_pct": round(100 * k / n, 1) if n else None, "wilson95": wilson(k, n),
             "pending_third_coder": len(pend), "both_unopened": len(unopened), "uncoded": sum(1 for r in rows if r["how"] == "uncoded"),
             "bounds_if_pending_all_dependent_pct": round(100 * (k + len(pend)) / (n + len(pend)), 1) if n else None,
             "bounds_if_pending_all_nondependent_pct": round(100 * k / (n + len(pend)), 1) if n else None}
    by_how = Counter(r["how"] for r in rows)
    sizes = frame_sizes()
    N = sum(sizes.values())
    strata = []
    est, var = 0.0, 0.0
    for st in sorted(sizes):
        sub = [r for r in decided if r["stratum"] == st]
        ks, ns = sum(1 for r in sub if r["dependence"] == "의존"), len(sub)
        p = ks / ns if ns else None
        all_sub = [r for r in rows if r["stratum"] == st]
        strata.append({"stratum": st, "frame_n": sizes[st], "weight_pct": round(100 * sizes[st] / N, 2), "sample_n": len(all_sub), "decided": ns, "dependent": ks,
                       "share_pct": round(100 * p, 1) if p is not None else None, "wilson95": wilson(ks, ns), "pending": sum(1 for r in all_sub if r["how"] == "pending")})
        if p is not None:
            est += sizes[st] / N * p
            var += (sizes[st] / N) ** 2 * p * (1 - p) / ns
    se = math.sqrt(var)
    post = {"frame_n": N, "share_pct": round(100 * est, 1), "ci95_pct": (round(100 * (est - 1.96 * se), 1), round(100 * (est + 1.96 * se), 1)),
            "census_dependent": round(CENSUS_ALL * est), "census_dependent_range": (round(CENSUS_ALL * (est - 1.96 * se)), round(CENSUS_ALL * (est + 1.96 * se))),
            "curve_dependent": round(CURVE_N * est), "curve_dependent_range": (round(CURVE_N * (est - 1.96 * se)), round(CURVE_N * (est + 1.96 * se)))}
    # the same stratum rates post-stratified to the current census (strata that the frame did not have keep the pooled rate)
    cur = frame_sizes(ROOT / "data" / "census_v2.csv")
    Nc = sum(cur.values())
    rate = {s["stratum"]: s["share_pct"] / 100 for s in strata if s["share_pct"] is not None}
    pooled = k / n if n else 0.0
    est_c = sum(cur[st] / Nc * rate.get(st, pooled) for st in cur)
    var_c = sum((cur[st] / Nc) ** 2 * rate.get(st, pooled) * (1 - rate.get(st, pooled)) / max(next((s["decided"] for s in strata if s["stratum"] == st), n), 1) for st in cur)
    se_c = math.sqrt(var_c)
    post["current_census"] = {"frame_n": Nc, "strata_not_in_sampling_frame": sorted(st for st in cur if st not in rate),
                              "papers_in_those_strata": int(sum(cur[st] for st in cur if st not in rate)),
                              "share_pct": round(100 * est_c, 1), "ci95_pct": (round(100 * (est_c - 1.96 * se_c), 1), round(100 * (est_c + 1.96 * se_c), 1)),
                              "census_dependent": round(CENSUS_ALL * est_c), "curve_dependent": round(CURVE_N * est_c)}
    by_status = {}
    for st in sorted({r["statuses"] for r in rows}):
        sub = [r for r in decided if r["statuses"] == st]
        ks, ns = sum(1 for r in sub if r["dependence"] == "의존"), len(sub)
        by_status[st] = {"dependent": ks, "decided": ns, "share_pct": round(100 * ks / ns, 1) if ns else None, "wilson95": wilson(ks, ns)}
    by_group = {}
    for g in sorted({r["group"] for r in rows}):
        sub = [r for r in decided if r["group"] == g]
        ks, ns = sum(1 for r in sub if r["dependence"] == "의존"), len(sub)
        by_group[g] = {"dependent": ks, "decided": ns, "share_pct": round(100 * ks / ns, 1) if ns else None, "wilson95": wilson(ks, ns)}

    # ---- per coder and questions
    per_coder = {}
    for c in "ABCD":
        vs = [r[f"verdict_{c}"] for r in rows if r[f"verdict_{c}"]]
        dec = [v for v in vs if v in ("의존", "비의존")]
        per_coder[c] = {"papers": len(vs), "의존": dec.count("의존"), "decided": len(dec), "판단불가": vs.count("판단불가"),
                        "share_pct": round(100 * dec.count("의존") / len(dec), 1) if dec else None}
    dep_rows = [r for r in decided if r["dependence"] == "의존"]
    q = {"dependent_papers": len(dep_rows),
         "Q1_final": dict(Counter(r["Q1"] for r in dep_rows)), "Q2_final": dict(Counter(r["Q2"] for r in dep_rows)), "Q3_final": dict(Counter(r["Q3"] for r in dep_rows)),
         "snapshot_any_coder": sum(r["Q2_snapshot_any"] for r in dep_rows), "snapshot_final": sum(1 for r in dep_rows if r["Q2"] == "날짜 스냅숏"),
         "run_date_any_coder": sum(r["Q3_date_any"] for r in dep_rows), "run_month_final": sum(1 for r in dep_rows if r["Q3"] == "연월"),
         "webui_or_mixed_any_coder": sum(r["Q1_webui_any"] for r in dep_rows), "webui_final": sum(1 for r in dep_rows if r["Q1"] == "웹UI"),
         "outside_list_named": sum(1 for r in rows if r["outside_list"] == 1),
         "median_models_named": sorted(r["models_named"] for r in rows if r["models_named"] != "")[len([r for r in rows if r["models_named"] != ""]) // 2]}
    merge = json.load(open(ROOT / "coding" / "merge_main.json", encoding="utf-8")) if (ROOT / "coding" / "merge_main.json").exists() else {}
    summary = {"papers": len(rows), "codebook": "v1.3", "coders": 4, "decisions_applied": len(decisions), "papers_by_resolution": dict(by_how),
               "dependence": share, "post_stratified": post, "by_status": by_status, "by_group": by_group, "by_stratum": strata, "per_coder": per_coder,
               "questions": q, "agreement": {k: merge.get(k) for k in ("role", "dependence_collapsed", "pairwise_role_kappa", "questions")}}
    json.dump(summary, open(ROOT / "data" / "coding" / "main_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---- Supplementary Table 8 (item, value)
    ag = summary["agreement"]
    items = [("papers coded (main sample, two coders per paper)", len(rows)), ("codebook", "v1.3"),
             ("papers settled by agreement / full-text rule / third coder / single coder", f"{by_how.get('agree', 0)} / {by_how.get('fulltext', 0)} / {by_how.get('third', 0)} / {by_how.get('single', 0)}"),
             ("papers pending a third coder / neither coder could open", f"{len(pend)} / {len(unopened)}"),
             ("papers dependent (ran at least one matched identifier)", f"{k} of {n}"),
             ("dependence share, % (Wilson 95% CI)", f"{share['share_pct']} ({share['wilson95'][0]}-{share['wilson95'][1]})"),
             ("dependence share, post-stratified to the sampling frame, % (95% CI)", f"{post['share_pct']} ({post['ci95_pct'][0]}-{post['ci95_pct'][1]})"),
             (f"census papers that depend on a named model (of {CENSUS_ALL:,}), estimate (95% CI)", f"{post['census_dependent']:,} ({post['census_dependent_range'][0]:,}-{post['census_dependent_range'][1]:,})"),
             (f"papers in the survival curve that depend on a named model (of {CURVE_N:,})", f"{post['curve_dependent']:,} ({post['curve_dependent_range'][0]:,}-{post['curve_dependent_range'][1]:,})"),
             (f"dependence share post-stratified to the current census of {post['current_census']['frame_n']:,} English-metadata papers, % (95% CI); strata absent from the sampling frame take the pooled rate",
              f"{post['current_census']['share_pct']} ({post['current_census']['ci95_pct'][0]}-{post['current_census']['ci95_pct'][1]}); {post['current_census']['papers_in_those_strata']:,} papers in {len(post['current_census']['strata_not_in_sampling_frame'])} such strata"),
             (f"census papers that depend on a named model under that weighting (of {CENSUS_ALL:,})", f"{post['current_census']['census_dependent']:,}")]
    for st, v in by_status.items():
        items.append((f"dependence share by model status, {st}, % (n)", f"{v['share_pct']} ({v['wilson95'][0]}-{v['wilson95'][1]}; n = {v['decided']})"))
    for g, v in by_group.items():
        items.append((f"dependence share by field group, {g}, % (n)", f"{v['share_pct']} ({v['wilson95'][0]}-{v['wilson95'][1]}; n = {v['decided']})"))
    for s in strata:
        items.append((f"stratum {s['stratum']}: frame n, sample n, dependent share %", f"{s['frame_n']:,}, {s['sample_n']}, {s['share_pct']} ({s['wilson95'][0]}-{s['wilson95'][1]})"))
    if ag.get("role"):
        items += [("Krippendorff's alpha, role code (identifier level)", f"{ag['role']['alpha']} ({ag['role']['units_coded_by_2plus']} units)"),
                  ("Krippendorff's alpha, dependence dichotomy", f"{ag['dependence_collapsed']['alpha']} ({ag['dependence_collapsed']['units_coded_by_2plus']} units)"),
                  ("pairwise Cohen's kappa, role code", "; ".join(f"{p} {v['kappa']} (n = {v['n']})" for p, v in ag["pairwise_role_kappa"].items() if v.get("n")))]
        for qq, v in ag["questions"].items():
            items.append((f"Krippendorff's alpha, {qq}", f"{v['alpha']} ({v['units_coded_by_2plus']} units)"))
    for c, v in per_coder.items():
        items.append((f"coder {c}: dependent share of decided papers, %", f"{v['share_pct']} ({v['의존']} of {v['decided']}; cannot judge {v['판단불가']})"))
    items += [("dependent papers naming a dated snapshot anywhere (any coder / final)", f"{q['snapshot_any_coder']} / {q['snapshot_final']} of {q['dependent_papers']}"),
              ("dependent papers stating a run date (any coder) / the month (final)", f"{q['run_date_any_coder']} / {q['run_month_final']} of {q['dependent_papers']}"),
              ("dependent papers run through a web interface (final 웹UI / any coder 웹UI or 혼합)", f"{q['webui_final']} / {q['webui_or_mixed_any_coder']} of {q['dependent_papers']}"),
              ("papers naming a model outside the census list", q["outside_list_named"]), ("median number of model names per paper", q["median_models_named"])]
    with open(ROOT / "data" / "coding_main_summary.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "value"])
        w.writerows(items)
    print(json.dumps({k: summary[k] for k in ("papers_by_resolution", "dependence", "post_stratified", "by_status", "by_group", "per_coder", "questions")}, ensure_ascii=False, indent=1))
    print("-> data/coding/main_summary.json, data/coding/main_papers.csv, data/coding_main_summary.csv")


if __name__ == "__main__":
    main()
