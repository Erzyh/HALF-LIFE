"""Successor-model comparison (P3): one row per paper and arm, next to the pre-shutdown baseline.

Reads runs/tierb/<wid>/result.json (baseline on the paper's own model) and runs/tierb_p3/<arm>/<wid>/result.json
(the same config on a successor). Classes use the Tier B rule: reproduced if the reference value lies inside the
arm's 95% CI or within 2 points, close within 5 points, deviated otherwise (the provisional columns); when
data/judgment_final.csv exists, class_vs_original and baseline_class_vs_original carry the three judges' majority; 'vs_original' takes the paper's
reported value as reference, 'vs_baseline' the pre-shutdown re-run. Writes data/p3_summary.csv and prints counts.
No API calls."""
import csv, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JUDGED = {}  # the three judges' majority (scripts/judgment_apply.py); when present it replaces the provisional class
if (ROOT / "data" / "judgment_final.csv").exists():
    for _r in csv.DictReader(open(ROOT / "data" / "judgment_final.csv", encoding="utf-8-sig")):
        if _r["sheet"] == "PromptLevel_blind":
            JUDGED[(_r["wid"], _r["condition"])] = _r
ARMS = {"vendor": "vendor-designated replacement (deprecations page, default settings)",
        "gpt41": "gpt-4.1-2025-04-14 (supported non-reasoning GPT-4-class model)",
        "open70b": "open-weight Llama 3.3 70B Instruct (Together, FP8 Turbo serving; permanent re-execution axis)",
        "gemini_flash": "other vendor's closed API: Gemini 3.8 Flash (Google AI Studio, OpenAI-compatible endpoint, lowest thinking level)"}


def scaled(res):
    """(value, ci_lo, ci_hi) on the paper's scale, or None."""
    rx = res.get("reexecution") or {}
    if rx.get("mean_over_seeds") is None:
        return None
    comp = res.get("comparison") or {}
    scale = comp.get("scale_applied") or 1.0
    ci = ((rx.get("per_seed") or {}).get("0") or {}).get("ci95") or [None, None]
    lo = ci[0] * scale if ci[0] is not None else None
    hi = ci[1] * scale if ci[1] is not None else None
    return rx["mean_over_seeds"] * scale, lo, hi


NOT_TRANSFERABLE = {
    # the paper's quantity is about the retired model itself, so no successor can stand in for it
    "W4416035547": "self-identification task: the model must pick itself among named options; the successor is not an option",
}
# arm-specific: a paper whose second stage (a fixed OpenAI judge or translator) could not be run for an arm is unscorable
# on that arm. The two open-weight cases (W4403882451 plan translation, W4404985489 similarity judge) were blocked by the
# OpenAI account deactivation of 2026-09-20 and were completed on 2026-09-21 after the account was restored, so the dict
# is empty; the mechanism stays for future arms.
JUDGE_UNAVAILABLE = {}


def unit_of(ref, val):
    """Points on the paper's scale, as in scripts/tierb_summary.py: fractions are read as percentages."""
    return 100.0 if (isinstance(ref, (int, float)) and abs(ref) <= 1.0 and val is not None and -1.0 <= val <= 1.0) else 1.0


def classify(ref, val, lo, hi):
    if ref is None or val is None:
        return "확인 필요"
    inside = lo is not None and hi is not None and lo <= float(ref) <= hi
    d = abs(val - float(ref)) * unit_of(ref, val)
    return "재현" if inside or d <= 2 else ("근접" if d <= 5 else "편차")


def cost_of(d):
    total = 0.0
    for b in (d / "budget.json", d / "judge" / "budget.json"):
        if b.exists():
            total += json.loads(b.read_text(encoding="utf-8")).get("cost_usd", 0.0)
    return total


def main():
    rows = []
    for arm in ARMS:
        base = ROOT / "runs" / "tierb_p3" / arm
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            f = d / "result.json"
            if not f.exists():
                continue
            res = json.loads(f.read_text(encoding="utf-8"))
            wid = res["wid"]
            bres = json.loads((ROOT / "runs" / "tierb" / wid / "result.json").read_text(encoding="utf-8"))
            s, b = scaled(res), scaled(bres)
            orig = res.get("original_value")
            val, lo, hi = s if s else (None, None, None)
            bval = b[0] if b else None
            rx = res.get("reexecution") or {}
            n = ((rx.get("per_seed") or {}).get("0") or {}).get("n")
            n_base = (((bres.get("reexecution") or {}).get("per_seed") or {}).get("0") or {}).get("n")
            # when most replies cannot be scored, the number measures format compliance, not the paper's quantity
            unscorable = n and (rx.get("unparsed") or 0) > 0.5 * n
            note = NOT_TRANSFERABLE.get(wid, "")
            if (arm, wid) in JUDGE_UNAVAILABLE:
                unscorable = True
                note = JUDGE_UNAVAILABLE[(arm, wid)]
            elif unscorable:
                note = f"format non-compliance: {rx.get('unparsed')} of {n} replies lack the answer field the paper's parser expects; value not comparable"
            rows.append({
                "arm": arm, "wid": wid, "title": (res.get("title") or "")[:60],
                "config_model": (res.get("arm") or {}).get("config_model"), "arm_model": res.get("model"),
                "metric": res.get("metric"), "original": orig,
                "baseline": None if bval is None else round(bval, 3),
                "arm_value": None if val is None else round(val, 3),
                "ci_lo": None if lo is None else round(lo, 3), "ci_hi": None if hi is None else round(hi, 3),
                "delta_vs_original_pts": None if (val is None or orig is None) else round((val - float(orig)) * unit_of(orig, val), 2),
                "delta_vs_baseline_pts": None if (val is None or bval is None) else round((val - bval) * unit_of(bval, val), 2),
                "class_vs_original": "해당없음" if wid in NOT_TRANSFERABLE else (JUDGED[(wid, arm)]["class"] if (wid, arm) in JUDGED else ("확인 필요" if unscorable else classify(orig, val, lo, hi))),
                "class_vs_baseline": "해당없음" if wid in NOT_TRANSFERABLE else "확인 필요" if unscorable else classify(bval, val, lo, hi),
                "baseline_class_vs_original": JUDGED[(wid, "baseline")]["class"] if (wid, "baseline") in JUDGED else (classify(orig, bval, b[1], b[2]) if b else "확인 필요"),
                "note": note,
                "n_items": n, "n_items_baseline": n_base, "unparsed": rx.get("unparsed"),
                "served": ";".join((res.get("served") or {}).get("models") or []),
                "fingerprints": (res.get("served") or {}).get("n_fingerprints"),
                "cost_usd": round(cost_of(d), 2),
                "subset_note": (res.get("prepare") or {}).get("subset_note") or "",
                "class_vs_original_provisional": "해당없음" if wid in NOT_TRANSFERABLE else "확인 필요" if unscorable else classify(orig, val, lo, hi),
                "baseline_class_vs_original_provisional": classify(orig, bval, b[1], b[2]) if b else "확인 필요",
                "conclusion_vs_original": JUDGED.get((wid, arm), {}).get("conclusion_majority", "")})
    out = ROOT / "data" / "p3_summary.csv"
    if not rows:
        print("no arm results yet")
        return
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        if not sub:
            continue
        excluded = [r["wid"] for r in sub if r["class_vs_original"] == "해당없음"]
        if excluded:
            print(f"{arm}: not transferable (excluded from the counts): {excluded}")
        sub = [r for r in sub if r["class_vs_original"] != "해당없음"]
        print(f"{arm}: {len(sub)} papers, ${sum(r['cost_usd'] for r in sub):.2f}; "
              f"vs original {dict(Counter(r['class_vs_original'] for r in sub))}; "
              f"vs baseline {dict(Counter(r['class_vs_baseline'] for r in sub))}; "
              f"baseline itself {dict(Counter(r['baseline_class_vs_original'] for r in sub))}")
        hi_unparsed = [(r["wid"], r["unparsed"], r["n_items"]) for r in sub
                       if (r["unparsed"] or 0) > 0.1 * max(1, r["n_items"] or 1)]
        if hi_unparsed:
            print("  unparsed > 10%:", hi_unparsed)
    print("->", out)


if __name__ == "__main__":
    main()
