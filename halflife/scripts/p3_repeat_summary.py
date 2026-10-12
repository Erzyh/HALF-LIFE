"""Seed-variance check of the successor conditions: spread over three identical calls per item set.

For each of the 20 papers in data/p3_repeat_wids.json and each condition, the original run (runs/tierb_p3/<arm>/,
one call per item) and the two fresh calls of the repeat (runs/tierb_p3/<arm>_rep/, seeds 0 and 1 with the same
request bodies) give three values of the paper's metric on its 0-100 scale. Reported per paper: the three values,
their range and standard deviation, the class of every call against the reported value under the prompt-level rule
(reproduced: reported value inside the call's 95% interval or within 2 points; close: within 5; deviated otherwise)
and whether the class is the same for all three calls. Per condition: median and upper quantiles of the range,
papers over 2 and over 5 points, share with a stable class, compared with the three-seed baselines and the
same-snapshot control. Writes data/p3_repeat_spread.csv and data/p3_repeat_summary.csv. No API calls.
"""
import json
import statistics as st
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
ARMS = {"vendor": "designated replacement", "gpt41": "gpt-4.1", "open70b": "open-weight Llama 3.3 70B", "gemini_flash": "Gemini 3.8 Flash"}


def load(path):
    p = Path(path)
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def classify(value, ci, original):
    if value is None or original is None:
        return None
    d = abs(value - original)
    inside = bool(ci and ci[0] is not None and ci[0] <= original <= ci[1])
    if inside or d <= 2:
        return "재현"
    if d <= 5:
        return "근접"
    return "편차"


def calls(res):
    """(value, ci) per call on the paper's scale, in seed order."""
    if not res:
        return []
    scale = (res.get("comparison") or {}).get("scale_applied") or 1
    out = []
    for s, v in sorted((res.get("reexecution") or {}).get("per_seed", {}).items(), key=lambda kv: int(kv[0])):
        if v.get("value") is None:
            continue
        ci = v.get("ci95")
        out.append((float(v["value"]) * scale, [c * scale for c in ci] if ci and ci[0] is not None else None))
    return out


def main():
    wids = json.load(open(HALF / "data" / "p3_repeat_wids.json"))
    rows = []
    for arm in ARMS:
        for wid in wids:
            base = load(HALF / "runs" / "tierb_p3" / arm / wid / "result.json")
            rep = load(HALF / "runs" / "tierb_p3" / f"{arm}_rep" / wid / "result.json")
            if not base:
                continue
            original = base.get("original_value")
            try:
                original = float(original)
            except (TypeError, ValueError):
                original = None
            cs = calls(base)[:1] + calls(rep)
            vals = [v for v, _ in cs]
            classes = [classify(v, ci, original) for v, ci in cs]
            rows.append({"condition": ARMS[arm], "arm": arm, "wid": wid, "title": (base.get("title") or "")[:70], "metric": base.get("metric"), "original": original,
                         "calls": len(vals), "values_pts": "; ".join(f"{v:.2f}" for v in vals), "range_pts": round(max(vals) - min(vals), 2) if len(vals) >= 2 else None,
                         "sd_pts": round(st.pstdev(vals), 2) if len(vals) >= 2 else None, "classes": "; ".join(c or "-" for c in classes),
                         "class_stable": (len(set(classes)) == 1) if len(vals) >= 3 else None, "repeat_done": rep is not None})
    d = pd.DataFrame(rows)
    d.to_csv(HALF / "data" / "p3_repeat_spread.csv", index=False, encoding="utf-8-sig")
    summ = []
    for arm, g in d[d["calls"] >= 3].groupby("arm", sort=False):
        r = g["range_pts"]
        summ.append({"condition": ARMS[arm], "papers": len(g), "range_median_pts": round(r.median(), 2), "range_p75_pts": round(r.quantile(0.75), 2),
                     "range_max_pts": round(r.max(), 2), "papers_range_over_2": int((r > 2).sum()), "papers_range_over_5": int((r > 5).sum()),
                     "class_stable_share_pct": round(100 * g["class_stable"].mean(), 1)})
    s = pd.DataFrame(summ)
    s.to_csv(HALF / "data" / "p3_repeat_summary.csv", index=False, encoding="utf-8-sig")
    print(f"repeat rows: {len(d)} | complete (3 calls): {(d['calls'] >= 3).sum()}")
    print(s.to_string(index=False) if len(s) else "no complete repeats yet")


if __name__ == "__main__":
    main()
