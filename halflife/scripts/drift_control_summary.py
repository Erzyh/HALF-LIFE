"""Same-snapshot drift control: the pre-retirement baseline of 20 Tier B papers re-run weeks later on the same pinned
model with the same items and request bodies (arm directory runs/tierb_p3/drift_ctrl/, prepared by
tierb_runner.prepare_from_baseline). Two comparisons per paper:

  paper level - the metric of the re-run against the baseline's seed-0 value and its three-seed mean, classed with the
                Tier B rule (reproduced: inside the re-run's 95% interval or within 2 points; close: within 5; deviated),
                and against the paper's reported value;
  item level  - the share of items whose parsed answer is identical between the baseline's seed-0 reply and the re-run,
                and the share whose raw reply text is identical.

Writes data/drift_control.csv and prints the summary. No API calls.
"""
import csv, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "scripts"))
import tierb_runner as tr                                       # noqa: E402
from battery import load_results                                # noqa: E402
from p3_summary import classify, unit_of                        # noqa: E402

ARM = ROOT / "runs" / "tierb_p3" / "drift_ctrl"


def parsed(text, cfg, hook):
    if hook and hasattr(hook, "parse"):
        return hook.parse(text, cfg)
    return tr.parse_output(text, (cfg.get("output") or {}).get("parse"))


def content(rec):
    ch = (rec.get("response") or {}).get("choices") or [{}]
    return ((ch[0].get("message") or {}).get("content")) if ch else None


def main():
    rows = []
    for d in sorted(ARM.glob("W*")):
        wid = d.name
        rp = d / "result.json"
        base_dir = ROOT / "runs" / "tierb" / wid
        if not rp.exists() or not (base_dir / "result.json").exists():
            continue
        res = json.load(open(rp, encoding="utf-8"))
        base = json.load(open(base_dir / "result.json", encoding="utf-8"))
        cfg = tr.load_cfg(wid)
        hook = tr.load_hook(wid)
        orig = cfg["metric"].get("original_value")
        # bring re-run values onto the paper's scale the way the runner does (fractions reported as percentages)
        scale = float((res.get("comparison") or {}).get("scale_applied") or (base.get("comparison") or {}).get("scale_applied") or 1.0)
        drift_val = res["reexecution"]["mean_over_seeds"] * scale
        ci0 = (res["reexecution"]["per_seed"].get("0") or {}).get("ci95") or [None, None]
        drift_ci = [None if c is None else c * scale for c in ci0]
        b0 = base["reexecution"]["per_seed"].get("0") or {}
        b_seed0 = None if b0.get("value") is None else b0["value"] * scale
        b_mean = base["reexecution"]["mean_over_seeds"] * scale
        u = unit_of(orig, drift_val)
        # item-level agreement between the baseline's seed-0 replies and the re-run
        bres = load_results(base_dir)
        dres = load_results(d)
        same_parsed = same_raw = n_pair = 0
        for (iid, s), drec in dres.items():
            brec = bres.get((iid, 0))
            if not brec:
                continue
            n_pair += 1
            bt, dt = content(brec), content(drec)
            if bt == dt:
                same_raw += 1
            if parsed(bt, cfg, hook) == parsed(dt, cfg, hook):
                same_parsed += 1
        rows.append({
            "wid": wid, "title": (cfg.get("title") or "")[:60], "model": cfg["model"]["id"], "metric": cfg["metric"]["name"],
            "original": orig, "baseline_seed0": round(b_seed0, 4) if b_seed0 is not None else "", "baseline_mean": round(b_mean, 4),
            "drift_value": round(drift_val, 4), "drift_ci_lo": drift_ci[0], "drift_ci_hi": drift_ci[1],
            "delta_vs_baseline_seed0_pts": round((drift_val - b_seed0) * u, 2) if b_seed0 is not None else "",
            "delta_vs_baseline_mean_pts": round((drift_val - b_mean) * u, 2),
            "delta_vs_original_pts": round((drift_val - float(orig)) * u, 2) if orig is not None else "",
            "class_vs_baseline_seed0": classify(b_seed0, drift_val, drift_ci[0], drift_ci[1]) if b_seed0 is not None else "",
            "class_vs_original": classify(orig, drift_val, drift_ci[0], drift_ci[1]),
            "baseline_class_vs_original": next((r.get("class") for r in json.load(open(ROOT / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8")) if r.get("wid") == wid), ""),
            "items_paired": n_pair, "share_same_parsed": round(same_parsed / n_pair, 3) if n_pair else "", "share_same_raw": round(same_raw / n_pair, 3) if n_pair else "",
            "n_fingerprints_baseline": (base.get("served") or {}).get("n_fingerprints"), "n_fingerprints_drift": (res.get("served") or {}).get("n_fingerprints"),
            "baseline_date": json.load(open(base_dir / "budget.json"))["started"][:10] if (base_dir / "budget.json").exists() else "",
            "drift_date": json.load(open(d / "budget.json"))["started"][:10] if (d / "budget.json").exists() else "",
        })
    if not rows:
        print("no drift-control results yet")
        return
    with open(ROOT / "data" / "drift_control.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    d0 = [abs(float(r["delta_vs_baseline_seed0_pts"])) for r in rows if r["delta_vs_baseline_seed0_pts"] != ""]
    cls = {c: sum(1 for r in rows if r["class_vs_baseline_seed0"] == c) for c in ("재현", "근접", "편차")}
    moved = sum(1 for r in rows if r["class_vs_baseline_seed0"] == "편차")
    sp = [float(r["share_same_parsed"]) for r in rows if r["share_same_parsed"] != ""]
    sr = [float(r["share_same_raw"]) for r in rows if r["share_same_raw"] != ""]
    med = lambda v: sorted(v)[len(v) // 2] if v else float("nan")
    print(f"papers {n} | vs baseline seed 0: {cls}, deviated {moved} ({100 * moved / n:.0f}%), median |delta| {med(d0):.1f} pts, max {max(d0):.1f}")
    print(f"item level: median share of identical parsed answers {med(sp):.2f} (min {min(sp):.2f}), identical raw text {med(sr):.2f}")
    print(f"vs original: {dict((c, sum(1 for r in rows if r['class_vs_original'] == c)) for c in ('재현', '근접', '편차'))}; baseline classes vs original: {dict((c, sum(1 for r in rows if r['baseline_class_vs_original'] == c)) for c in ('재현', '근접', '편차'))}")
    print("-> data/drift_control.csv")


if __name__ == "__main__":
    main()
