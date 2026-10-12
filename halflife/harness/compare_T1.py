"""Compare our re-execution of T1 against the paper's archived results.

Inputs
  runs/T1/baseline_alive/samples.jsonl_passk.json   (from heb_eval.py)
  runs/T1/baseline_alive/samples.jsonl_results.jsonl
  external/human-eval-bia/data/samples_gpt-4-turbo-2024-04-09.jsonl_results.jsonl  (original)
  runs/reference/samples.jsonl_passk.json           (environment sanity, optional)
Outputs
  runs/T1/comparison.json  and a console summary.
Bootstrap CI: resample the 57 tasks with replacement (2,000 draws) for pass@1.
"""
import json, random, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
HALF = HERE.parent
RUN = HALF / "runs" / "T1" / "baseline_alive"
ORIG = HALF / "external" / "human-eval-bia" / "data" / "samples_gpt-4-turbo-2024-04-09.jsonl_results.jsonl"
REF = HALF / "runs" / "reference" / "samples.jsonl_passk.json"


def per_task(results_path):
    d = defaultdict(lambda: [0, 0])
    for line in open(results_path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            d[r["task_id"]][0] += 1
            d[r["task_id"]][1] += 1 if r["passed"] else 0
    return {t: (n, c) for t, (n, c) in d.items()}


def pass1(pt):
    return sum(c / n for n, c in pt.values()) / len(pt)


def bootstrap(pt, draws=2000, seed=0):
    rng = random.Random(seed)
    tasks = list(pt.values())
    vals = []
    for _ in range(draws):
        s = [rng.choice(tasks) for _ in tasks]
        vals.append(sum(c / n for n, c in s) / len(s))
    vals.sort()
    return vals[int(0.025 * draws)], vals[int(0.975 * draws)]


def main():
    ours = per_task(RUN / "samples.jsonl_results.jsonl")
    orig = per_task(ORIG)
    ours_p1, orig_p1 = pass1(ours), pass1(orig)
    lo, hi = bootstrap(ours)
    olo, ohi = bootstrap(orig, seed=1)
    ref = json.loads(REF.read_text())["passk"] if REF.exists() else None

    rows = []
    for t in sorted(orig):
        on, oc = orig[t]
        n, c = ours.get(t, (0, 0))
        rows.append({"task": Path(t).stem, "orig_n": on, "orig_c": oc, "orig_rate": oc / on,
                     "ours_n": n, "ours_c": c, "ours_rate": (c / n) if n else None})
    flipped = [r for r in rows if r["ours_n"] and ((r["orig_rate"] >= 0.5) != (r["ours_rate"] >= 0.5))]
    agree = sum(1 for r in rows if r["ours_n"] and abs(r["orig_rate"] - r["ours_rate"]) <= 0.2)

    out = {
        "original": {"pass@1": orig_p1, "ci95": [olo, ohi], "n_samples": sum(n for n, _ in orig.values())},
        "reexecution": {"pass@1": ours_p1, "ci95": [lo, hi], "n_samples": sum(n for n, _ in ours.values())},
        "environment_reference_passk": ref,
        "task_level": {"n_tasks": len(rows), "within_0.2_of_original": agree,
                       "majority_flipped": [r["task"] for r in flipped]},
        "rows": rows,
    }
    (HALF / "runs" / "T1" / "comparison.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"original     pass@1 = {orig_p1:.4f}  95% CI [{olo:.3f}, {ohi:.3f}]  (n={out['original']['n_samples']})")
    print(f"re-execution pass@1 = {ours_p1:.4f}  95% CI [{lo:.3f}, {hi:.3f}]  (n={out['reexecution']['n_samples']})")
    if ref:
        print(f"environment reference pass@1 = {ref.get('pass@1'):.3f}")
    print(f"tasks within ±0.2 of original: {agree}/{len(rows)}; majority-flipped: {len(flipped)}")
    for r in flipped:
        print(f"  flipped: {r['task']}  orig {r['orig_rate']:.1f} -> ours {r['ours_rate']:.1f}")


if __name__ == "__main__":
    main()
