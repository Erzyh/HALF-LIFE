"""Successor condition for repository-based papers: the same claims on the vendor's designated replacement.

Reads the successor outputs of the five adapters run through scripts/tiera_successor.py (runs/<Wid>/successor_vendor/)
and the pre-retirement values from data/tiera_claims.csv, and writes one row per claim: reported value, pre-retirement
re-run, successor value with its 95% interval, differences in points (the claims table's scale rule: 'pts' as is,
'x100' for fractions), whether the reported value lies inside the successor interval, and the provisional class under
the prompt-level rule (reproduced: inside the interval or within 2 points; close: within 5; deviated otherwise) so that
the rows are comparable with the prompt-level successor condition. Writes data/tiera_successor_claims.csv and prints
the table. No API calls.
"""
import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
ARM = "successor_vendor"
WIDS = ("W7171749161", "W4404781910", "W7144391134", "W4416074906", "W4412887943")


def load(p):
    p = Path(p)
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def first_existing(*paths):
    for p in paths:
        if Path(p).exists():
            return load(p)
    return None


def rows_for(wid):
    d = HALF / "runs" / wid / ARM
    out = []
    if wid == "W7171749161":
        r = first_existing(d / "result.json", d / "run" / "result.json")
        if r and r.get("pooled"):
            out.append(("Tag Questions: tag effect on agreement", r["pooled"]["tageff"], r["pooled"].get("ci90"), "pts", "interval is the 90% band as in the paper"))
    elif wid == "W4404781910":
        m = first_existing(d / "run_meta.json")
        if m:
            for bias, rr in m["results"]["rows"].items():
                out.append((f"OffsetBias: EvalBiasBench accuracy, {bias.replace('_', ' ')}", rr["acc"], rr.get("ci95"), "pts", f"n={rr.get('n', '')}"))
    elif wid == "W7144391134":
        r = first_existing(d / "result.json", d / "run" / "result.json")
        if r:
            if "1000-shot" in r:
                out.append(("BlindingLLMs: Pearson r x100, 1000-shot", r["1000-shot"]["r"], r["1000-shot"].get("ci"), "pts",
                            f"n={r['1000-shot'].get('n', '')} test molecules, {len(r['1000-shot'].get('per_run_r') or [])} runs"))
            if "60-shot" in r:
                out.append(("BlindingLLMs: Pearson r x100, 60-shot", r["60-shot"]["r"], r["60-shot"].get("ci"), "pts",
                            f"n={r['60-shot'].get('n', '')} test molecules, {len(r['60-shot'].get('per_run_r') or [])} runs"))
            if "zeroshot" in r:
                nz = r["zeroshot"].get("n")
                sub = ((load(d / "successor_meta.json") or {}).get("zero_shot_subset") or {}).get("molecules")
                note = f"n={nz} molecules" + ((f": seeded random subset of {sub} under the cost cap plus {nz - sub} answered before the restart; paper: 1,128"
                                               if sub and nz and nz > sub else f" (seeded random subset under the cost cap; paper: 1,128)") if nz and nz < 1128 else "")
                out.append(("BlindingLLMs: Pearson r, 0-shot", r["zeroshot"]["pearson_r"], None, "x100", note))
    elif wid == "W4416074906":
        m = first_existing(d / "run_meta.json")
        if m:
            for persona, rr in m["results"]["rows"].items():
                out.append((f"AgentMisalignment: misalignment score, persona {persona}", rr["cms"], rr.get("cms_ci95"), "x100", ""))
    elif wid == "W4412887943":
        m = first_existing(d / "run_meta.json")
        if m:
            rows = m["results"]["rows"]
            out.append(("MEDEC: error flag accuracy (vs Table 2 GPT-4o)", rows["err_flag_acc"]["value"], rows["err_flag_acc"].get("ci95_pooled"), "x100", m["results"].get("subset", "")))
            out.append(("MEDEC: error sentence accuracy (vs Table 2 GPT-4o)", rows["err_sentence_acc"]["value"], rows["err_sentence_acc"].get("ci95_pooled"), "x100", m["results"].get("subset", "")))
    return out


def unit(orig, val, scale):
    """Points on the paper's scale: fractions (both values within [-1, 1]) are read as percentages, as in scripts/p3_summary.py."""
    if scale == "x100":
        return 100.0
    return 100.0 if (orig is not None and val is not None and abs(orig) <= 1.0 and abs(val) <= 1.0) else 1.0


def classify(orig, val, lo, hi, scale):
    if orig is None or val is None:
        return None
    k = unit(orig, val, scale)
    d = abs(val - orig) * k
    inside = lo is not None and hi is not None and lo <= orig <= hi
    return "reproduced" if inside or d <= 2 else ("close" if d <= 5 else "deviated")


def log_budget():
    """Append one budget_log.csv row per finished successor run (arm tierA_successor) if none exists yet; spend from the run's budget.json."""
    bl = HALF / "budget_log.csv"
    rows = list(csv.reader(open(bl, encoding="utf-8")))
    have = {(r[1], r[2]) for r in rows[1:] if len(r) > 2}
    prev = float(rows[-1][6]) if len(rows) > 1 else 0.0
    for wid in WIDS:
        d = HALF / "runs" / wid / ARM
        b = first_existing(d / "budget.json", d / "run" / "budget.json")
        sm = load(d / "successor_meta.json") or {}
        done = (d / "result.json").exists() or (d / "run" / "result.json").exists() or (d / "run_meta.json").exists()
        if not b or not done or (wid, "tierA_successor") in have or float(b.get("cost_usd") or 0) <= 0:
            continue
        cost = round(float(b["cost_usd"]), 2)
        args = [x for x in sm.get("adapter_args", []) if x not in ("--run", "--analyze", "--dry-run")]
        note = (f"successor condition approved 2026-10-01: {sm.get('baseline_model')} -> {sm.get('successor_model')}, cap {sm.get('cap_usd')}"
                + (f", adapter args {' '.join(args)}" if args else "") + ("; stopped at cap" if b.get("stopped_at_cap") else ""))
        prev = round(prev + cost, 2)
        with open(bl, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([str(date.today()), wid, "tierA_successor", sm.get("successor_model", ""), b.get("calls", ""), cost, prev, note])
        print(f"budget_log.csv: + {wid} tierA_successor {cost} USD (cumulative {prev})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-budget", action="store_true", help="append the spend of finished successor runs to budget_log.csv (idempotent)")
    a = ap.parse_args()
    claims = pd.read_csv(HALF / "data" / "tiera_claims.csv", encoding="utf-8-sig")
    meta = {}
    for wid in WIDS:
        sm = load(HALF / "runs" / wid / ARM / "successor_meta.json")
        meta[wid] = sm or {}
    rows = []
    for wid in meta:
        base = claims[claims.wid == wid].set_index("label")
        for label, val, ci, scale, note in rows_for(wid):
            b = base.loc[label] if label in base.index else None
            orig = float(b["original"]) if b is not None else None
            rerun = float(b["rerun"]) if b is not None else None
            k = unit(orig, val, scale)
            lo, hi = (ci[0], ci[1]) if ci and ci[0] is not None else (None, None)
            rows.append({"wid": wid, "claim": label, "baseline_model": meta[wid].get("baseline_model"), "successor_model": meta[wid].get("successor_model"),
                         "original": orig, "pre_retirement_rerun": rerun, "successor": round(float(val), 4), "ci_lo": lo, "ci_hi": hi,
                         "successor_minus_original_pts": None if orig is None else round((val - orig) * k, 2),
                         "successor_minus_rerun_pts": None if rerun is None else round((val - rerun) * k, 2),
                         "original_inside_ci": (lo is not None and lo <= orig <= hi) if orig is not None and lo is not None else None,
                         "class_vs_original": classify(orig, val, lo, hi, scale), "class_vs_rerun": classify(rerun, val, lo, hi, scale),
                         "rerun_judgment": re.sub(r"\s*\((survived|partial|died)\)", "", str(b["judgment"])) if b is not None else None, "note": note})
    df = pd.DataFrame(rows)
    df.to_csv(HALF / "data" / "tiera_successor_claims.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 230, "display.max_columns", 20, "display.max_colwidth", 48):
        print(df.drop(columns=["baseline_model", "note"]).to_string(index=False))
    if len(df):
        print("papers:", df.wid.nunique(), "claims:", len(df), "| class vs original:", df.class_vs_original.value_counts().to_dict(),
              "| class vs pre-retirement re-run:", df.class_vs_rerun.value_counts().to_dict(),
              "| median |shift| vs original:", round(df.successor_minus_original_pts.abs().median(), 2))
    if a.log_budget:
        log_budget()


if __name__ == "__main__":
    main()
