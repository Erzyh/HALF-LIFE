"""Queue and launcher for the BF16 check of the open-weight condition (approved 2026-09-28, cap US$45 for the endpoint hours).

python scripts/p3_bf16_queue.py <endpoint model name>

The 12 papers in data/p3_bf16_wids.json (seeded random draw among the scorable open-weight results with an FP8 pass
of at most US$1.50) are re-run with the same request bodies as the FP8 (Together serverless 'Turbo') run, one call
per item, on a Together dedicated endpoint that serves meta-llama/Llama-3.3-70B-Instruct in bfloat16. Token charges
are zero on a dedicated endpoint (it bills per minute), so harness/pricing.json gets a zero entry for the endpoint
name and the hourly cost is written to budget_log.csv by hand after the endpoint is stopped.
Writes harness/tierb/queue_p3_open70b_bf16.json and runs/p3_bf16_launch.cmd (log runs/p3_bf16.log). No API calls.
"""
import json
import sys
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
model = sys.argv[1]
wids = json.load(open(HALF / "data" / "p3_bf16_wids.json"))
p3 = pd.read_csv(HALF / "data" / "p3_summary.csv").set_index(["arm", "wid"])
jobs = []
for wid in wids:
    r = p3.loc[("open70b", wid)]
    jobs.append({"wid": wid, "cap": 5.0, "seeds": 1, "arm": "open70b_bf16", "arm_model": model, "model": model, "copy_from": "open70b",
                 "est_usd": 0.0, "fp8_cost_usd": round(float(r["cost_usd"]), 2), "title": str(r["title"])[:50],
                 "note": "BF16 check: same request bodies as the FP8 open-weight run, one call per item, Together dedicated endpoint (hourly billing, token price 0)"})
out = HALF / "harness" / "tierb" / "queue_p3_open70b_bf16.json"
json.dump(jobs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
pr = json.load(open(HALF / "harness" / "pricing.json", encoding="utf-8"))
pr["usd_per_1m"][model] = {"input": 0.0, "output": 0.0, "note": "Together dedicated endpoint for the BF16 check (2026-09-28): billed per minute (36 cents), not per token"}
json.dump(pr, open(HALF / "harness" / "pricing.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
lines = ["@echo off", f"cd /d {HALF}", "set PYTHONIOENCODING=utf-8",
         "echo START p3 bf16 check (12 papers, 1 call per item, workers 16) %date% %time% >> runs\\p3_bf16.log",
         "python harness\\run_queue.py --queue harness\\tierb\\queue_p3_open70b_bf16.json --total-cap 5 --workers 16 >> runs\\p3_bf16.log 2>&1",
         "echo P3 BF16 DONE %date% %time% >> runs\\p3_bf16.log"]
(HALF / "runs" / "p3_bf16_launch.cmd").write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
print(f"{len(jobs)} papers -> {out.name}; pricing entry added for {model}; launcher runs/p3_bf16_launch.cmd")
