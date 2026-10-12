"""BF16 check of the open-weight condition: the FP8 serverless build against a BF16 dedicated deployment on identical requests.

For the 12 papers in data/p3_bf16_wids.json (seeded random draw among the scorable open-weight results whose FP8 pass cost
at most 1.50 USD): the open-weight condition's value (runs/tierb_p3/open70b/, Together serverless
meta-llama/Llama-3.3-70B-Instruct-Turbo, FP8) and the BF16 re-run (runs/tierb_p3/open70b_bf16/, Together dedicated
endpoint serving meta-llama/Llama-3.3-70B-Instruct in bfloat16 on 4x H100, same items and request bodies, one call per
item). Reported per paper: both values on the paper's scale, their difference, unparsed replies under each build, the class
of each value against the reported value under the prompt-level rule as applied in scripts/p3_summary.py (reproduced: reported
value inside the 95% interval or within 2 points; close: within 5; deviated otherwise; fractions read as percentages) and whether the class changes. Summary: median, upper quartile and
maximum of |difference|, papers over 2 and over 5 points, class changes in each direction, unparsed replies under each build,
and the call-to-call range of the same condition from the repeat (data/p3_repeat_spread.csv) as the noise reference.
Writes data/p3_bf16_compare.csv and data/p3_bf16_summary.csv. No API calls.
"""
import json
import statistics as st
import sys
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "scripts"))
from p3_summary import NOT_TRANSFERABLE, classify, scaled, unit_of   # noqa: E402  (the condition summary's own rules)

FP8, BF16 = "open70b", "open70b_bf16"


def load(path):
    p = Path(path)
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def first_call(res):
    """(value, ci_lo, ci_hi, n, unparsed) on the paper's scale, as scripts/p3_summary.py reads a one-call condition."""
    if not res:
        return None, None, None, None, None
    rx = res.get("reexecution") or {}
    s0 = (rx.get("per_seed") or {}).get("0") or {}
    v, lo, hi = scaled(res) or (None, None, None)
    return v, lo, hi, s0.get("n"), rx.get("unparsed")


def cls(wid, orig, v, lo, hi, n, unparsed):
    if v is None or orig is None:
        return None
    if wid in NOT_TRANSFERABLE:
        return "해당없음"
    if n and (unparsed or 0) > 0.5 * n:
        return "확인 필요"
    return classify(orig, v, lo, hi)


def main():
    wids = json.load(open(HALF / "data" / "p3_bf16_wids.json"))
    p3 = pd.read_csv(HALF / "data" / "p3_summary.csv")
    titles = dict(zip(p3.loc[p3.arm == FP8, "wid"], p3.loc[p3.arm == FP8, "title"]))
    rows = []
    for wid in wids:
        a = load(HALF / "runs" / "tierb_p3" / FP8 / wid / "result.json")
        b = load(HALF / "runs" / "tierb_p3" / BF16 / wid / "result.json")
        orig = (a or {}).get("original_value")
        va, loa, hia, na, ua = first_call(a)
        vb, lob, hib, nb, ub = first_call(b)
        ca, cb = cls(wid, orig, va, loa, hia, na, ua), cls(wid, orig, vb, lob, hib, nb, ub)
        unit = unit_of(orig, va) if (orig is not None and va is not None) else 1
        rows.append({"wid": wid, "title": str(titles.get(wid, (a or {}).get("title", "")))[:60], "metric": (a or {}).get("metric"),
                     "original": orig, "n_items": na, "fp8_value": None if va is None else round(va, 3), "bf16_value": None if vb is None else round(vb, 3),
                     "bf16_minus_fp8_pts": None if (va is None or vb is None) else round((vb - va) * unit, 2),
                     "fp8_unparsed": ua, "bf16_unparsed": ub, "fp8_class": ca, "bf16_class": cb,
                     "class_changed": None if (ca is None or cb is None) else (ca != cb),
                     "bf16_served": ";".join(((b or {}).get("served") or {}).get("models") or []) if b else "pending"})
    df = pd.DataFrame(rows)
    df.to_csv(HALF / "data" / "p3_bf16_compare.csv", index=False, encoding="utf-8-sig")
    done = df[df.bf16_value.notna() & df.fp8_value.notna()]
    diffs = done.bf16_minus_fp8_pts.abs().tolist()
    ref = None
    sp = HALF / "data" / "p3_repeat_spread.csv"
    if sp.exists():
        s = pd.read_csv(sp)
        col = "arm" if "arm" in s.columns else ("condition" if "condition" in s.columns else None)
        rcol = next((c for c in s.columns if c.startswith("range")), None)
        if col and rcol:
            sub = s[s[col].astype(str).str.contains("open", case=False)]
            ref = round(float(sub[rcol].median()), 2) if len(sub) else None
    summ = {"papers_drawn": len(df), "papers_compared": len(done),
            "abs_diff_median_pts": round(st.median(diffs), 2) if diffs else None,
            "abs_diff_p75_pts": round(float(pd.Series(diffs).quantile(0.75)), 2) if diffs else None,
            "abs_diff_max_pts": round(max(diffs), 2) if diffs else None,
            "papers_diff_over_2": int(sum(d > 2 for d in diffs)), "papers_diff_over_5": int(sum(d > 5 for d in diffs)),
            "class_changes": int(done.class_changed.sum()) if len(done) else 0,
            "fp8_deviated": int((done.fp8_class == "편차").sum()), "bf16_deviated": int((done.bf16_class == "편차").sum()),
            "deviated_fp8_only": int(((done.fp8_class == "편차") & (done.bf16_class != "편차")).sum()),
            "deviated_bf16_only": int(((done.fp8_class != "편차") & (done.bf16_class == "편차")).sum()),
            "fp8_unparsed_total": int(pd.to_numeric(done.fp8_unparsed, errors="coerce").fillna(0).sum()),
            "bf16_unparsed_total": int(pd.to_numeric(done.bf16_unparsed, errors="coerce").fillna(0).sum()),
            "items_total": int(pd.to_numeric(done.n_items, errors="coerce").fillna(0).sum()),
            "repeat_call_to_call_range_median_pts_open_weight": ref}
    pd.DataFrame([summ]).to_csv(HALF / "data" / "p3_bf16_summary.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 220, "display.max_columns", 20):
        print(df.drop(columns=["title", "bf16_served"]).to_string(index=False))
        print(json.dumps(summ, ensure_ascii=False))


if __name__ == "__main__":
    main()
