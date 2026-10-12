"""Queue for an additional successor arm (another vendor or an open-weight model) over the prompt-level papers.

Same design as the earlier successor arms: one pass per item on the papers that already have a vendor-arm result
(74 papers), minus a policy exclusion list (bias audits that combine demographic attributes with decisions about a
person, and benchmarks built from seemingly harmful prompts) that is kept out of third-party accounts. Projection =
archived baseline tokens / config seeds at the arm model's prices, plus --think-tokens hidden thinking tokens per
call billed as output for models that cannot switch thinking off (Gemini 3.1 Pro at its lowest level spends about
300; instruction models take 0). Per-paper cap = max($1, 1.5 x projection + $0.3); a paper whose projection alone
exceeds --paper-cap is not queued but listed in queue_p3_<arm>_over_cap.json (the vendor arm treated its costly
papers the same way: skipped, not truncated). The worst case of a launch is the --total-cap given to run_queue.py. Papers flagged sensitive-but-benign (medical vignettes, moral dilemmas, court judgments, alignment
scenarios) are placed last so that they run after the ordinary benchmarks. No API calls.

usage: python scripts/p3_extra_queues.py --arm open70b --model meta-llama/Llama-3.3-70B-Instruct-Turbo
"""
import argparse, json, os
from collections import Counter
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
EXCLUDE = {  # kept out of third-party and open-weight arms (see ANALYSIS_DEVIATIONS.md, 2026-09-20)
    "W4416683695": "hiring self-preferencing: demographic attributes + hiring decisions",
    "W4406975432": "agent decisions: demographic personas + decisions",
    "W4403580619": "gender bias in morality judgements",
    "W4415035710": "gender entropy bias",
    "W4414758400": "gender and ethnicity bias mitigation",
    "W4400375186": "CEB fairness benchmark: stereotype judgements over named groups",
    "W4399317891": "OR-Bench: prompts written to look harmful",
}
RUN_LAST = {"W7106207151", "W4411080278", "W7140138327", "W4403556032", "W4416339332", "W7140953907", "W7166872685",
            "W4404573318", "W4406058562"}   # sensitive but benign: medical, moral dilemmas, UN simulation, court texts, alignment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--paper-cap", type=float, default=20.0)
    ap.add_argument("--think-tokens", type=float, default=0.0, help="hidden thinking tokens per call, billed as output")
    ap.add_argument("--max-paper-calls", type=int, default=0, help="if > 0, queue only papers with at most this many calls per seed (daily request quotas)")
    a = ap.parse_args()
    price = json.load(open(HALF / "harness" / "pricing.json", encoding="utf-8"))["usd_per_1m"][a.model]
    titles = {}
    for q in ("queue_p3_vendor.json", "queue_p3_vendor2.json", "queue_p3_vendor3.json", "queue_p3_vendor4.json"):
        p = HALF / "harness" / "tierb" / q
        if p.exists():
            for j in json.load(open(p, encoding="utf-8")):
                titles[j["wid"]] = j.get("title", "")
    jobs, skipped, over_cap = [], [], []
    for d in sorted((HALF / "runs" / "tierb_p3" / "vendor").iterdir()):
        w = d.name
        if not (d / "result.json").exists():
            continue
        if w in EXCLUDE:
            skipped.append(w); continue
        b = json.load(open(HALF / "runs" / "tierb" / w / "budget.json", encoding="utf-8"))
        cfg = json.load(open(HALF / "harness" / "tierb" / "configs" / f"{w}.json", encoding="utf-8"))
        k = int(cfg["model"].get("seeds") or 1)
        proj = (b["tokens_in"] / k) / 1e6 * price["input"] + (b["tokens_out"] / k) / 1e6 * price["output"]
        jb = HALF / "runs" / "tierb" / w / "judge" / "budget.json"
        if jb.exists():                      # hook-driven second stage: same token volume per seed, billed at the arm's prices
            j = json.load(open(jb, encoding="utf-8"))
            proj += (j.get("tokens_in", 0) / k) / 1e6 * price["input"] + (j.get("tokens_out", 0) / k) / 1e6 * price["output"]
        proj += (b["calls"] / k) * a.think_tokens / 1e6 * price["output"]
        if proj > a.paper_cap or (a.max_paper_calls and round(b["calls"] / k) > a.max_paper_calls):
            reason = (f"projected ${proj:.2f} exceeds the per-paper cap ${a.paper_cap:.0f}" if proj > a.paper_cap
                      else f"{round(b['calls'] / k)} calls exceed the per-paper limit {a.max_paper_calls} set for the daily request quota")
            over_cap.append({"wid": w, "est_usd": round(proj, 2), "n_calls": round(b["calls"] / k),
                             "title": (cfg.get("title") or titles.get(w, ""))[:60], "reason": reason})
            continue
        jobs.append({"wid": w, "cap": round(min(a.paper_cap, max(1.0, 1.5 * proj + 0.3)), 2), "seeds": 1, "arm": a.arm, "arm_model": a.model,
                     "model": cfg["model"]["id"], "est_usd": round(proj, 3), "n_calls": round(b["calls"] / k), "config_seeds": k,
                     "title": (cfg.get("title") or titles.get(w, ""))[:60], "run_last": w in RUN_LAST})
    jobs.sort(key=lambda j: (j["run_last"], j["est_usd"]))
    out = HALF / "harness" / "tierb" / f"queue_p3_{a.arm}.json"
    json.dump(jobs, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if over_cap:
        json.dump(over_cap, open(out.with_name(f"queue_p3_{a.arm}_over_cap.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"arm {a.arm} ({a.model}, think {a.think_tokens:.0f} tok/call): {len(jobs)} papers, projected ${sum(j['est_usd'] for j in jobs):.2f}, "
          f"sum of caps ${sum(j['cap'] for j in jobs):.2f}, calls {sum(j['n_calls'] for j in jobs):,}; excluded {len(skipped)}: {skipped}; "
          f"over cap {len(over_cap)}: {[(o['wid'], o['est_usd'], o['n_calls']) for o in over_cap]}; run last: {sum(j['run_last'] for j in jobs)} -> {out.relative_to(HALF)}")


if __name__ == "__main__":
    main()
