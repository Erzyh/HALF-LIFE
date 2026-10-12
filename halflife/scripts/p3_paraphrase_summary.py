"""Wording check: how far a paper's result moves when the fixed instruction text is reworded on the pinned model.

For every control paper with rewordings (harness/tierb/paraphrase/paraphrases.json) the values on the paper's scale of
the pre-retirement baseline (seed 0), the same-snapshot control (same wording, later date), and the two rewordings
p1 and p2 (runs/tierb_p3/para_p1, para_p2). Reported per paper: the four values, the wording range (max minus min
over baseline, p1, p2), the dating range (|control minus baseline|), the class of each run against the reported value
under the prompt-level rule as applied in scripts/p3_summary.py, and whether the class is the same for all wordings.
The summary compares the wording range with the call-to-call range of the seed-variance repeat (data/p3_repeat_spread.csv)
and with the successor shift of the same papers in the designated-replacement condition (data/p3_summary.csv).
Writes data/p3_paraphrase_spread.csv and data/p3_paraphrase_summary.csv. No API calls.
"""
import json
import statistics as st
import sys
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "scripts"))
from p3_summary import NOT_TRANSFERABLE, classify, scaled, unit_of  # noqa: E402


def load(p):
    p = Path(p)
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def val(res):
    if not res:
        return None, None, None
    s = scaled(res)
    return s if s else (None, None, None)


def main():
    table = json.load(open(HALF / "harness" / "tierb" / "paraphrase" / "paraphrases.json", encoding="utf-8"))
    wids = [w for w in table if w.startswith("W")]
    p3 = pd.read_csv(HALF / "data" / "p3_summary.csv", encoding="utf-8-sig")
    vend = p3[p3.arm == "vendor"].set_index("wid")
    rows = []
    for wid in wids:
        base = load(HALF / "runs" / "tierb" / wid / "result.json")
        drift = load(HALF / "runs" / "tierb_p3" / "drift_ctrl" / wid / "result.json")
        r1 = load(HALF / "runs" / "tierb_p3" / "para_p1" / wid / "result.json")
        r2 = load(HALF / "runs" / "tierb_p3" / "para_p2" / wid / "result.json")
        orig = (base or {}).get("original_value")
        # baseline seed 0 on the paper's scale (scaled() gives the mean over seeds; take seed 0 for comparability with the control)
        b0 = None
        if base:
            sc = (base.get("comparison") or {}).get("scale_applied") or 1.0
            s0 = ((base.get("reexecution") or {}).get("per_seed") or {}).get("0") or {}
            b0 = float(s0["value"]) * sc if s0.get("value") is not None else None
        vd, ld, hd = val(drift)
        v1, l1, h1 = val(r1)
        v2, l2, h2 = val(r2)
        unit = unit_of(orig, b0) if (orig is not None and b0 is not None) else 1.0
        have = [v for v in (b0, v1, v2) if v is not None]
        wording_range = round((max(have) - min(have)) * unit, 2) if len(have) == 3 else None
        dating_range = round(abs(vd - b0) * unit, 2) if (vd is not None and b0 is not None) else None
        cls = {}
        for name, v, lo, hi in (("baseline", b0, None, None), ("control", vd, ld, hd), ("p1", v1, l1, h1), ("p2", v2, l2, h2)):
            cls[name] = (None if v is None or orig is None else "not transferable" if wid in NOT_TRANSFERABLE else classify(orig, v, lo, hi))
        succ = vend.loc[wid] if wid in vend.index else None
        rows.append({"wid": wid, "title": str((base or {}).get("title", ""))[:60], "metric": (base or {}).get("metric"), "model": (base or {}).get("model"),
                     "original": orig, "baseline_seed0": None if b0 is None else round(b0, 3), "control": None if vd is None else round(vd, 3),
                     "p1": None if v1 is None else round(v1, 3), "p2": None if v2 is None else round(v2, 3),
                     "wording_range_pts": wording_range, "dating_range_pts": dating_range,
                     "class_baseline": cls["baseline"], "class_control": cls["control"], "class_p1": cls["p1"], "class_p2": cls["p2"],
                     "class_stable_over_wordings": None if None in (cls["baseline"], cls["p1"], cls["p2"]) else (cls["baseline"] == cls["p1"] == cls["p2"]),
                     "successor_shift_pts": None if succ is None or pd.isna(succ.get("delta_vs_baseline_pts")) else round(float(succ["delta_vs_baseline_pts"]), 2),
                     "successor_class": None if succ is None else succ.get("class_vs_original"),
                     "n_items": ((base or {}).get("reexecution") or {}).get("per_seed", {}).get("0", {}).get("n")})
    df = pd.DataFrame(rows)
    df.to_csv(HALF / "data" / "p3_paraphrase_spread.csv", index=False, encoding="utf-8-sig")
    done = df[df.wording_range_pts.notna()]
    wr = done.wording_range_pts.tolist()
    ss = done.successor_shift_pts.dropna().abs().tolist()
    rep = HALF / "data" / "p3_repeat_spread.csv"
    rep_med = None
    if rep.exists():
        r = pd.read_csv(rep, encoding="utf-8-sig")
        rep_med = round(float(r.range_pts.median()), 2) if "range_pts" in r.columns else None
    # one rewording against the baseline is a single pairwise difference, like the successor shift; the wording range is the spread of three
    single = []
    for _, r in done.iterrows():
        u = unit_of(r.original, r.baseline_seed0) if pd.notna(r.original) else 1.0
        single += [abs(r.p1 - r.baseline_seed0) * u, abs(r.p2 - r.baseline_seed0) * u]
    dev = lambda c: c == "편차"
    status_changes = int(sum(len({dev(r.class_baseline), dev(r.class_p1), dev(r.class_p2)}) > 1 for _, r in done.iterrows()
                             if None not in (r.class_baseline, r.class_p1, r.class_p2)))
    summ = {"papers_with_rewordings": len(df), "papers_complete": len(done),
            "single_rewording_abs_shift_median_pts": round(st.median(single), 2) if single else None,
            "single_rewording_abs_shift_p75_pts": round(float(pd.Series(single).quantile(0.75)), 2) if single else None,
            "single_rewording_abs_shift_max_pts": round(max(single), 2) if single else None,
            "rewordings_over_2": int(sum(x > 2 for x in single)), "rewordings_over_5": int(sum(x > 5 for x in single)), "rewordings": len(single),
            "papers_deviated_status_changes_with_wording": status_changes,
            "wording_range_median_pts": round(st.median(wr), 2) if wr else None,
            "wording_range_p75_pts": round(float(pd.Series(wr).quantile(0.75)), 2) if wr else None,
            "wording_range_max_pts": round(max(wr), 2) if wr else None,
            "papers_wording_over_2": int(sum(w > 2 for w in wr)), "papers_wording_over_5": int(sum(w > 5 for w in wr)),
            "class_stable_share_pct": round(100 * done.class_stable_over_wordings.mean(), 1) if len(done) else None,
            "dating_range_median_pts": round(float(done.dating_range_pts.median()), 2) if done.dating_range_pts.notna().any() else None,
            "successor_abs_shift_median_pts_same_papers": round(st.median(ss), 2) if ss else None,
            "successor_abs_shift_over_5_same_papers": int(sum(s > 5 for s in ss)),
            "repeat_call_to_call_range_median_pts": rep_med}
    pd.DataFrame([summ]).to_csv(HALF / "data" / "p3_paraphrase_summary.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 230, "display.max_columns", 30):
        print(df.drop(columns=["title", "model"]).to_string(index=False))
        print(json.dumps(summ, ensure_ascii=False))


if __name__ == "__main__":
    main()
