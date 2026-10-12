"""Queues and launchers for the seed-variance check of the successor conditions (approved 2026-09-28).

Design: the 20 papers in data/p3_repeat_wids.json (seeded random draw among the 37 papers that ran on all four
successor conditions with a four-condition pass of at most US$12) are re-run on every condition with the same
request bodies and two fresh calls per item (arm '<arm>_rep', seeds 2). The spread over the three calls (the
original run plus the two repeats) is the call-to-call variance of each successor.

Writes harness/tierb/queue_p3_repeat_<arm>.json and runs/p3_repeat_<provider>.cmd (each with its own log,
runs/p3_repeat_<provider>.log: two processes cannot append to one redirected log on Windows). No API calls here.
"""
import json
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
ARMS = ["vendor", "gpt41", "open70b", "gemini_flash"]
TOTAL_CAPS = {"vendor": 80, "gpt41": 35, "open70b": 15, "gemini_flash": 35}
WORKERS = {"vendor": 6, "gpt41": 6, "open70b": 2, "gemini_flash": 12}
SEEDS = 2

wids = json.load(open(HALF / "data" / "p3_repeat_wids.json"))
p3 = pd.read_csv(HALF / "data" / "p3_summary.csv").set_index(["arm", "wid"])
for arm in ARMS:
    jobs = []
    for wid in wids:
        r = p3.loc[(arm, wid)]
        est = round(SEEDS * float(r["cost_usd"]), 2)
        jobs.append({"wid": wid, "cap": max(1.0, round(2 * est + 0.5, 2)), "seeds": SEEDS, "arm": f"{arm}_rep", "arm_model": r["arm_model"], "model": r["arm_model"],
                     "copy_from": arm, "est_usd": est, "title": str(r["title"])[:50],
                     "note": f"seed-variance check: same request bodies as the {arm} condition, {SEEDS} fresh calls per item"})
    out = HALF / "harness" / "tierb" / f"queue_p3_repeat_{arm}.json"
    json.dump(jobs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{arm}: {len(jobs)} papers, est ${sum(j['est_usd'] for j in jobs):.2f}, caps sum ${sum(j['cap'] for j in jobs):.2f}, total cap ${TOTAL_CAPS[arm]} -> {out.name}")

launchers = {
    "openai": ["vendor", "gpt41"], "gemini": ["gemini_flash"], "together": ["open70b"],
}
for prov, arms in launchers.items():
    lines = ["@echo off", f"cd /d {HALF}", "set PYTHONIOENCODING=utf-8"]
    for arm in arms:
        lines.append(f"echo START p3 repeat {arm} (20 papers, {SEEDS} calls per item, total cap {TOTAL_CAPS[arm]}, workers {WORKERS[arm]}) %date% %time% >> runs\\p3_repeat_{prov}.log")
        lines.append(f"python harness\\run_queue.py --queue harness\\tierb\\queue_p3_repeat_{arm}.json --total-cap {TOTAL_CAPS[arm]} --workers {WORKERS[arm]} >> runs\\p3_repeat_{prov}.log 2>&1")
        lines.append(f"echo P3 REPEAT {arm} DONE %date% %time% >> runs\\p3_repeat_{prov}.log")
    (HALF / "runs" / f"p3_repeat_{prov}.cmd").write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print("->", f"runs/p3_repeat_{prov}.cmd")
