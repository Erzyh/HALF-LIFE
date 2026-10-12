"""Successor-arm queues for the second-pass Tier B papers (the 25 papers of harness/tierb/queue_pass2.json).

Same design as the first successor batches (2026-09-18/19): arm "vendor" = the replacement named on the OpenAI
deprecations page, default settings, one pass per item; arm "gpt41" = gpt-4.1-2025-04-14 for the papers whose
original model was GPT-4-class, paired with the vendor arm. The projection uses the archived token usage of the
finished baseline run divided by its seeds, at the successor's prices, plus OVER extra output tokens per call for
the reasoning successor (the first batches used 1,500 and came in at about half the projection; 800 here).
Per-paper cap = min(1.5 x projection + $0.3, PAPER_CAP) with a $1 floor; the worst case of a launch is the
--total-cap given to run_queue.py, not the sum of caps. Papers whose baseline has not finished are skipped, so
the script can run again after the resume queue. No API calls.

usage: python scripts/p3_pass2_queues.py [--over 800] [--paper-cap 25]
writes harness/tierb/queue_p3_vendor4.json and harness/tierb/queue_p3_gpt41c.json
"""
import argparse, json, os
from collections import Counter
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
REPL = {"gpt-4-turbo-2024-04-09": "gpt-5.6-sol", "gpt-4o-2024-05-13": "gpt-5.6-sol", "o1-2024-12-17": "gpt-5.6-sol",
        "o3-mini-2025-01-31": "gpt-5.6-sol", "o3-2025-04-16": "gpt-5.6-sol", "gpt-5-2025-08-07": "gpt-5.6-sol",
        "o4-mini-2025-04-16": "gpt-5.6-terra", "gpt-5-mini-2025-08-07": "gpt-5.6-terra",
        "gpt-4.1-nano-2025-04-14": "gpt-5.6-luna", "gpt-4.1-nano": "gpt-5.6-luna"}
PRICE = {"gpt-5.6-sol": (4, 20), "gpt-5.6-terra": (2, 12), "gpt-5.6-luna": (0.2, 1.2), "gpt-4.1-2025-04-14": (2, 8)}
GPT4 = {"gpt-4-turbo-2024-04-09", "gpt-4o-2024-05-13"}
SKIP = {}   # both reasoning-model baselines were repaired on 2026-09-20 (J4R paired 16k run; annotation guidelines effort low)


def usage_of(wid, title):
    d = HALF / "runs" / "tierb" / wid
    if not (d / "budget.json").exists() or not (d / "result.json").exists():
        return None
    b = json.load(open(d / "budget.json", encoding="utf-8"))
    cfg = json.load(open(HALF / "harness" / "tierb" / "configs" / f"{wid}.json", encoding="utf-8"))
    jc = 0.0
    if (d / "judge" / "budget.json").exists():
        jc = float(json.load(open(d / "judge" / "budget.json", encoding="utf-8")).get("cost_usd") or 0)
    return {"model": cfg["model"]["id"], "seeds": int(cfg["model"].get("seeds") or 1), "n_calls": b["calls"],
            "tok_in": b["tokens_in"], "tok_out": b["tokens_out"], "judge_cost": jc, "title": title}


def proj(v, model, over):
    pi, po = PRICE[model]
    k = v["seeds"]
    return (v["tok_in"] / k) / 1e6 * pi + ((v["tok_out"] + over * v["n_calls"]) / k) / 1e6 * po + v["judge_cost"] / k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--over", type=float, default=800)
    ap.add_argument("--paper-cap", type=float, default=25)
    a = ap.parse_args()
    cap = lambda x: round(min(a.paper_cap, max(1.0, 1.5 * x + 0.3)), 1)
    queue = json.load(open(HALF / "harness" / "tierb" / "queue_pass2.json", encoding="utf-8"))
    summary = {r["wid"]: r for r in json.load(open(HALF / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8"))}
    qa, qb, skipped = [], [], []
    for j in queue:
        if j["wid"] in SKIP:
            skipped.append(j["wid"] + " (" + SKIP[j["wid"]].split(":")[0] + ", repair pending)"); continue
        v = usage_of(j["wid"], j.get("title", ""))
        if v is None:
            skipped.append(j["wid"]); continue
        cls = summary.get(j["wid"], {}).get("class", "?")
        m = REPL[v["model"]]
        pa = proj(v, m, a.over if m != "gpt-5.6-luna" else a.over)
        qa.append({"wid": j["wid"], "cap": cap(pa), "seeds": 1, "arm": "vendor", "arm_model": m, "model": v["model"],
                   "est_usd": round(pa, 2), "n_calls_baseline": v["n_calls"], "config_seeds": v["seeds"], "baseline_class": cls, "title": v["title"]})
        if v["model"] in GPT4:
            pb = proj(v, "gpt-4.1-2025-04-14", 0)
            qb.append({"wid": j["wid"], "cap": cap(pb), "seeds": 1, "arm": "gpt41", "arm_model": "gpt-4.1-2025-04-14", "model": v["model"],
                       "est_usd": round(pb, 2), "n_calls_baseline": v["n_calls"], "config_seeds": v["seeds"], "paired": True, "baseline_class": cls, "title": v["title"]})
    qa.sort(key=lambda j: j["est_usd"]); qb.sort(key=lambda j: j["est_usd"])
    json.dump(qa, open(HALF / "harness" / "tierb" / "queue_p3_vendor4.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump(qb, open(HALF / "harness" / "tierb" / "queue_p3_gpt41c.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"vendor arm: {len(qa)} papers, projected ${sum(j['est_usd'] for j in qa):.1f}, sum of caps ${sum(j['cap'] for j in qa):.1f}; "
          f"{dict(Counter(j['arm_model'] for j in qa))}; baseline classes {dict(Counter(j['baseline_class'] for j in qa))}")
    print(f"gpt41 arm : {len(qb)} papers (all paired), projected ${sum(j['est_usd'] for j in qb):.1f}, sum of caps ${sum(j['cap'] for j in qb):.1f}")
    print("skipped (baseline not finished):", skipped)
    for j in qa:
        print(f"{j['est_usd']:6.2f} {j['cap']:5.1f} {j['wid']} {j['model']}->{j['arm_model']} {j['n_calls_baseline']}/{j['config_seeds']} {j['baseline_class']} {j['title'][:40]}")


if __name__ == "__main__":
    main()
