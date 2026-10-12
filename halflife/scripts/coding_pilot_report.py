"""Pilot coding analysis beyond the agreement statistics of coding_merge.py (codebook v1.2, four coders, 30 papers).

Reads the returned workbooks in coding/results_v12/ (or --dir), and reports
  - paper-level dependence per coder and by majority, with a Wilson 95% interval,
  - ID-level majority roles, per-coder deviation from the majority,
  - Q1-Q3, Q5, Q6 distributions per coder and by majority; the 'any coder found a dated snapshot' rule for Q2,
  - the units with role disagreements, the papers any coder could not open, the run-date reporting rate,
  - run-model lists: number of model names per paper and papers naming models outside the census list.
Writes data/coding/pilot_v12_summary.json and data/coding/pilot_v12_papers.csv; prints the numbers used in
coding/PILOT_REVIEW_v12.md. No API calls.
"""
import argparse
import csv
import glob
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from coding_merge import QCOLS, read  # noqa: E402

DEP = {"실행": "의존", "인용·언급": "비의존", "못찾음": "비의존", "판단불가": "판단불가"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def mode(values):
    """Modal value among the given codes; '동률' on a tie; None when empty."""
    values = [v for v in values if v]
    if not values:
        return None
    c = Counter(values).most_common()
    if len(c) > 1 and c[0][1] == c[1][1]:
        return "동률"
    return c[0][0]


def paper_verdict(roles):
    codes = [c for c in roles.values() if c]
    if not codes:
        return None
    if "실행" in codes:
        return "의존"
    if all(c in ("인용·언급", "못찾음") for c in codes):
        return "비의존"
    return "판단불가"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "coding" / "results_v12"))
    a = ap.parse_args()
    files = sorted(glob.glob(str(Path(a.dir) / "halflife_coding_pilot_coder*.xlsx")))
    data = {Path(f).stem.split("coder")[-1]: read(f) for f in files}
    coders = sorted(data)
    wids = sorted({w for d in data.values() for w in d}, key=lambda w: data[coders[0]][w]["num"] if w in data[coders[0]] else 999)
    target = json.load(open(ROOT / "target_models.json", encoding="utf-8"))["models"]
    listed = {m["id"].lower() for m in target}

    # ---- paper level
    rows = []
    for w in wids:
        rec = {"num": None, "title": None, "wid": w}
        verdicts = {}
        for c in coders:
            r = data[c].get(w)
            if r is None:
                continue
            rec["num"], rec["title"] = r["num"], r["title"]
            verdicts[c] = paper_verdict(r["roles"])
        rec["verdicts"] = verdicts
        decided = [v for v in verdicts.values() if v in ("의존", "비의존")]
        rec["majority"] = mode(decided) if decided else ("판단불가" if verdicts else None)
        rec["n_decided"] = len(decided)
        rec["unopened_by"] = [c for c, v in verdicts.items() if v == "판단불가"]
        for q in QCOLS:
            vals = {c: data[c][w][q] for c in coders if w in data[c] and data[c][w][q]}
            rec[q] = mode(vals.values())
            rec[q + " by coder"] = vals
        snap = [c for c in coders if w in data[c] and data[c][w]["Q2 버전표기"] == "날짜 스냅숏"]
        rec["snapshot_found_by_any"] = bool(snap)
        rec["snapshot_finders"] = snap
        models = {}
        for c in coders:
            r = data[c].get(w)
            if r and r["models"]:
                names = [x.strip() for x in re.split(r"[,\n;]+", r["models"]) if x.strip()]
                models[c] = names
        rec["models_per_coder"] = {c: len(v) for c, v in models.items()}
        rec["outside_list_named"] = any(any(n.lower() not in listed for n in v) for v in models.values())
        rows.append(rec)

    dep_counts = Counter(r["majority"] for r in rows)
    n_dec = sum(1 for r in rows if r["majority"] in ("의존", "비의존"))
    k_dep = dep_counts.get("의존", 0)
    per_coder_dep = {}
    for c in coders:
        vs = [paper_verdict(data[c][w]["roles"]) for w in wids if w in data[c]]
        dec = [v for v in vs if v in ("의존", "비의존")]
        per_coder_dep[c] = {"의존": dec.count("의존"), "decided": len(dec), "판단불가": vs.count("판단불가"), "blank": vs.count(None),
                            "share_pct": round(100 * dec.count("의존") / len(dec), 1) if dec else None}

    # ---- ID level
    units = defaultdict(dict)
    for c in coders:
        for w, r in data[c].items():
            for mid, code in r["roles"].items():
                if code:
                    units[(w, mid)][c] = code
    unit_major = {u: mode(v.values()) for u, v in units.items()}
    id_dist = Counter(unit_major.values())
    deviation = {c: 0 for c in coders}
    considered = {c: 0 for c in coders}
    for u, v in units.items():
        m = unit_major[u]
        if m in (None, "동률"):
            continue
        for c, code in v.items():
            considered[c] += 1
            if code != m:
                deviation[c] += 1
    role_disagreements = [(data[coders[1]][u[0]]["num"] if u[0] in data[coders[1]] else None, u[1], v) for u, v in units.items() if len(set(v.values())) > 1]

    # ---- questions
    q_major = {q: Counter(r[q] for r in rows) for q in QCOLS}
    q_by_coder = {q: {c: dict(Counter(data[c][w][q] for w in wids if w in data[c] and data[c][w][q])) for c in coders} for q in QCOLS}
    q_dev = {q: {c: sum(1 for r in rows if r[q] not in (None, "동률") and r[q + " by coder"].get(c) not in (None, r[q])) for c in coders} for q in QCOLS}
    snap_any = sum(1 for r in rows if r["snapshot_found_by_any"])
    snap_major = q_major["Q2 버전표기"].get("날짜 스냅숏", 0)
    date_any = sum(1 for r in rows if any(v == "연월" for v in r["Q3 실행시점 by coder"].values()))
    outside = sum(1 for r in rows if r["outside_list_named"])
    models_median = sorted(sum(r["models_per_coder"].values()) / max(1, len(r["models_per_coder"])) for r in rows)
    models_median = models_median[len(models_median) // 2]

    summary = {
        "coders": coders, "papers": len(rows),
        "paper_majority": dict(dep_counts), "dependence_share_pct": round(100 * k_dep / n_dec, 1) if n_dec else None,
        "dependence_wilson95": wilson(k_dep, n_dec), "n_decided_papers": n_dec,
        "per_coder_dependence": per_coder_dep,
        "id_units": len(units), "id_majority": dict(id_dist),
        "id_deviation_from_majority": {c: f"{deviation[c]}/{considered[c]}" for c in coders},
        "role_disagreements": [{"num": n, "id": mid, "codes": v} for n, mid, v in sorted(role_disagreements, key=lambda x: (x[0] or 0))],
        "unopened_papers": [{"num": r["num"], "by": r["unopened_by"], "majority": r["majority"]} for r in rows if r["unopened_by"]],
        "q_majority": {q: dict(v) for q, v in q_major.items()}, "q_by_coder": q_by_coder, "q_deviation_from_majority": q_dev,
        "snapshot_found_by_any_coder": snap_any, "snapshot_majority": snap_major,
        "run_date_reported_by_any_coder": date_any, "run_date_majority": q_major["Q3 실행시점"].get("연월", 0),
        "papers_naming_models_outside_list": outside, "median_models_named_per_paper": models_median,
    }
    (ROOT / "data" / "coding").mkdir(parents=True, exist_ok=True)
    json.dump(summary, open(ROOT / "data" / "coding" / "pilot_v12_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(ROOT / "data" / "coding" / "pilot_v12_papers.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["num", "openalex_id", "title", *[f"verdict_{c}" for c in coders], "majority", "unopened_by", "Q1", "Q2", "Q2_snapshot_any", "Q3", "models_named_median"])
        for r in rows:
            w.writerow([r["num"], r["wid"], r["title"], *[r["verdicts"].get(c) or "" for c in coders], r["majority"], "|".join(r["unopened_by"]),
                        r["Q1 접근경로"], r["Q2 버전표기"], int(r["snapshot_found_by_any"]), r["Q3 실행시점"],
                        round(sum(r["models_per_coder"].values()) / max(1, len(r["models_per_coder"])), 1)])
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
