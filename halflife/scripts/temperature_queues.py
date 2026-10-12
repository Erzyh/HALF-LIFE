"""Queue and launcher for the temperature sensitivity check (proposed 2026-10-02; runs only after the user's go).

python scripts/temperature_queues.py

Question: the configurations assumed temperature 0 where a paper is silent on decoding. For single-answer tasks the
assumption can only help the reproduction, but for generation and free-text tasks the paper may have sampled at the
API default. Selection rule, fixed before any run: executed prompt-level papers whose model parameters were assumed
because the paper is silent on temperature (params_source says so and the configuration carries temperature 0) and
whose task type is generation or other free text. Each selected paper is re-run on its own pinned model with
temperature 1.0 (the API default) and as many independent calls per item as the baseline had seeds, with the
baseline's items and request bodies otherwise unchanged (variant t1 in harness/tierb/paraphrase/temperature.json).
Per-paper caps are 1.3 times the baseline spend (at least US$2); the launcher runs under a US$70 total cap and logs to
runs/temperature_check.log. No API calls here.
"""
import json
import os
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
STATED = ("temperature 0", "temperature = 0", "temperature=0", "temperature 0.", "temperature=1", "temperature 1", "sampling temperature")

summ = {r["wid"]: r for r in json.load(open(HALF / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8"))}
budget = pd.read_csv(HALF / "budget_log.csv", encoding="utf-8-sig")
base_cost = budget[budget.arm == "tierb"].groupby("card").cost_usd.sum()
table = json.load(open(HALF / "harness" / "tierb" / "paraphrase" / "temperature.json", encoding="utf-8"))
jobs, skipped = [], []
for wid in sorted(summ):
    p = HALF / "harness" / "tierb" / "configs" / f"{wid}.json"
    if not p.exists():
        continue
    c = json.load(open(p, encoding="utf-8"))
    m = c["model"]; params = m.get("params") or {}; src = str(m.get("params_source") or "")
    silent = params.get("temperature") == 0.0 and ("silent" in src.lower() or src.lower().startswith("assumed")) and not any(k in src for k in STATED)
    task = (c.get("task") or {}).get("type")
    if not silent:
        continue
    if task not in ("generation", "other"):
        skipped.append((wid, task))
        continue
    assert wid in table and "t1" in table[wid], f"temperature.json lacks {wid}"
    seeds = int(m.get("seeds") or 1)
    cost = float(base_cost.get(wid, 0))
    jobs.append({"wid": wid, "cap": round(max(2.0, 1.3 * cost), 2), "seeds": seeds, "arm": "temp1", "arm_model": m["id"], "model": m["id"],
                 "paraphrase": "t1", "baseline_cost_usd": round(cost, 2), "baseline_class": summ[wid].get("class"), "task_type": task,
                 "title": str(c.get("title", ""))[:50],
                 "note": "temperature check: baseline items and seed-0 bodies on the pinned model at temperature 1.0 (API default), "
                         f"{seeds} independent call(s) per item as in the baseline"})
    print(f"  {wid} {m['id']} seeds {seeds} cap {jobs[-1]['cap']} (baseline {cost:.2f} USD, class {summ[wid].get('class')}) {str(c.get('title',''))[:45]}")
print(f"selected {len(jobs)} papers; silent-temperature papers with single-answer tasks left out: {len(skipped)} ({sorted({t for _, t in skipped})})")
out = HALF / "harness" / "tierb" / "queue_temp1.json"
json.dump(jobs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"caps sum {sum(j['cap'] for j in jobs):.2f} USD -> {out.name}")
lines = ["@echo off", f"cd /d {HALF}", "set PYTHONIOENCODING=utf-8",
         f"echo START temperature check ({len(jobs)} papers, temperature 1.0) %date% %time% >> runs\\temperature_check.log",
         "python harness\\run_queue.py --queue harness\\tierb\\queue_temp1.json --total-cap 70 --workers 4 >> runs\\temperature_check.log 2>&1",
         "echo TEMP CHECK DONE %date% %time% >> runs\\temperature_check.log"]
(HALF / "runs" / "temperature_check_launch.cmd").write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
print("launcher runs/temperature_check_launch.cmd (not launched)")
