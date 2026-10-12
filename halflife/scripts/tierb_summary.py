"""Aggregate runs/tierb/<Wid>/result.json into runs/tierb/batch1_tierb_summary.json with the class of each result.

Provisional class (automatic): 재현 = original inside the re-run 95% CI or |delta| <= 2 points on the paper's scale;
근접 = |delta| <= 5; 편차 = larger; 확인 필요 = config status needs_human. When data/judgment_final.csv exists
(scripts/judgment_apply.py, the three judges' majority of 11 October 2026), "class" is the judged class and the
automatic one stays in "class_provisional"; "conclusion" is the judges' conclusion level.
"""
import csv, json, glob, collections, re
from pathlib import Path
HALF = Path(__file__).resolve().parents[1]
JUDGED = {}
if (HALF / "data" / "judgment_final.csv").exists():
    for _r in csv.DictReader(open(HALF / "data" / "judgment_final.csv", encoding="utf-8-sig")):
        if _r["sheet"] == "PromptLevel_blind":
            JUDGED[(_r["wid"], _r["condition"])] = _r
rows = []
for f in sorted(glob.glob(str(HALF / "runs" / "tierb" / "W*" / "result.json"))):
    if not re.fullmatch(r"W\d+", Path(f).parent.name):   # prompt variants (…v2) and superseded archives (…_v1_*) are reported separately
        continue
    wid = Path(f).parent.name
    if "_" in wid:                      # archived earlier runs (e.g. W..._v1_maxtok16) are not current results
        continue
    r = json.load(open(f, encoding="utf-8"))
    cfg = json.load(open(HALF / "harness" / "tierb" / "configs" / f"{wid}.json", encoding="utf-8"))
    cost = 0.0
    for b in (Path(f).parent / "budget.json", Path(f).parent / "judge" / "budget.json"):
        if b.exists():
            cost += json.load(open(b, encoding="utf-8")).get("cost_usd", 0.0)
    rx = r.get("reexecution") or {}; cmp_ = r.get("comparison") or {}
    ps = rx.get("per_seed") or {}; s0 = ps.get("0") or ps.get(0) or {}
    scale = cmp_.get("scale_applied", 1.0)
    ci = s0.get("ci95"); ci_s = [c * scale for c in ci] if ci and ci[0] is not None else None
    orig = r.get("original_value"); rerun = cmp_.get("reexecution_scaled", (rx.get("mean_over_seeds") or 0) * scale)
    inside = cmp_.get("original_inside_ci95")
    # points on the paper's scale: fractions (|orig| <= 1 and 0 <= rerun <= 1) are read as percentages
    unit = 100.0 if (isinstance(orig, (int, float)) and abs(orig) <= 1.0 and -1.0 <= rerun <= 1.0) else 1.0
    delta = (rerun - orig) * unit if isinstance(orig, (int, float)) else None
    if cfg.get("status") == "needs_human":
        cls = "확인 필요"
    elif inside or (delta is not None and abs(delta) <= 2):
        cls = "재현"
    elif delta is not None and abs(delta) <= 5:
        cls = "근접"
    else:
        cls = "편차"
    # precision of the re-run interval on the paper's scale: half the CI width in points; wide intervals make the
    # "original inside the CI" clause easy to satisfy, so they are flagged and the CI-only reproductions are counted
    hw = (ci_s[1] - ci_s[0]) / 2 * unit if ci_s else None
    rows.append({"wid": wid, "title": (cfg.get("title") or "")[:52], "model": cfg["model"]["id"], "metric": cfg["metric"]["name"],
                 "orig": orig, "rerun": rerun, "ci": ci_s, "inside": inside, "delta_pts": delta, "n": s0.get("n"), "seeds": len(ps),
                 "unparsed": rx.get("unparsed"), "cost": round(cost, 2), "class": (JUDGED[(wid, "baseline")]["class"] if (wid, "baseline") in JUDGED else cls),
                 "class_provisional": cls, "conclusion": JUDGED.get((wid, "baseline"), {}).get("conclusion_majority"), "judged": (wid, "baseline") in JUDGED,
                 "ci_halfwidth_pts": None if hw is None else round(hw, 2), "low_precision": bool(hw is not None and hw > 10),
                 "class_via_ci_only": bool(cls == "재현" and delta is not None and abs(delta) > 2),
                 "note": (cfg.get("triage_note") or (cfg.get("open_points") or [""])[0] or "")[:160]})
json.dump(rows, open(HALF / "runs" / "tierb" / "batch1_tierb_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("results:", len(rows), "| class:", dict(collections.Counter(r["class"] for r in rows)), "| cost:", round(sum(r["cost"] for r in rows), 2),
      "| reproduced via the CI clause alone:", sum(r["class_via_ci_only"] for r in rows), "| low-precision (CI half-width > 10 pts):", sum(r["low_precision"] for r in rows))
