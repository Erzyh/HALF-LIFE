"""Queues and launcher for the wording check (approved 2026-10-01, cap US$140 in total).

python scripts/p3_paraphrase_queues.py

For every same-snapshot control paper that has rewordings in harness/tierb/paraphrase/paraphrases.json, two jobs
(variants p1 and p2) rerun the baseline's seed-0 request bodies with the fixed instruction text reworded, on the
paper's own pinned model, one call per item, judge stages as in the control. Per-paper caps are the control's caps
times 1.3 (at least US$1); the launcher runs queue_para_p1.json then queue_para_p2.json under a US$70 total cap each
and logs to runs/p3_para.log. No API calls here.
"""
import json
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
drift = json.load(open(HALF / "harness" / "tierb" / "queue_drift_control.json", encoding="utf-8"))
table = json.load(open(HALF / "harness" / "tierb" / "paraphrase" / "paraphrases.json", encoding="utf-8"))
lines = ["@echo off", f"cd /d {HALF}", "set PYTHONIOENCODING=utf-8"]
for v in ("p1", "p2"):
    jobs = []
    for j in drift:
        if j["wid"] not in table:
            continue
        jobs.append({"wid": j["wid"], "cap": round(max(1.0, float(j["cap"]) * 1.3), 2), "seeds": 1, "arm": f"para_{v}", "arm_model": j["model"],
                     "model": j["model"], "paraphrase": v, "est_usd": j.get("est_usd"), "n_calls": j.get("n_calls"), "title": j.get("title", "")[:50],
                     "note": f"wording check {v}: baseline items and seed-0 request bodies with the fixed instruction text reworded, same pinned model, one pass"})
    out = HALF / "harness" / "tierb" / f"queue_para_{v}.json"
    json.dump(jobs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    est = sum(float(j.get("est_usd") or 0) for j in jobs)
    print(f"{v}: {len(jobs)} papers, caps sum {sum(j['cap'] for j in jobs):.2f} USD, control estimate {est:.2f} USD -> {out.name}")
    lines += [f"echo START wording check {v} ({len(jobs)} papers) %date% %time% >> runs\\p3_para.log",
              f"python harness\\run_queue.py --queue harness\\tierb\\queue_para_{v}.json --total-cap 70 --workers 6 >> runs\\p3_para.log 2>&1",
              f"echo P3 PARA {v} DONE %date% %time% >> runs\\p3_para.log"]
(HALF / "runs" / "p3_para_launch.cmd").write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
print("launcher runs/p3_para_launch.cmd")
