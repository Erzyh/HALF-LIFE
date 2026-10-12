"""Queues and launcher for the format-adaptation case studies on the designated replacement (approved 2026-10-02, US$100 cap).

python scripts/format_case_queues.py

Selection rule, fixed before any run: the vendor-arm results left unscorable by format non-compliance (class 'needs
review' in data/p3_summary.csv), every scorable vendor-arm result whose share of unparsable replies exceeds 5%
(data/p3_format_bound.csv, Table S24's per-paper rows), and the paper with the next-highest share as a contrast case. Two adaptations per paper (harness/tierb/paraphrase/format_adapt.json): f1 adds
one sentence stating the output format the paper's parser expects; f2 is f1 plus the successor's lowest reasoning
setting. Each adaptation is one pass with the baseline's items and seed-0 request bodies on the same successor model
as the vendor arm. Per-paper caps are 1.5 times the vendor-arm spend (at least US$2); the launcher runs queue_format_f1
then queue_format_f2 under a US$50 total cap each and logs to runs/format_cases.log. No API calls here.
"""
import json
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
THRESHOLD = 0.05

fb = pd.read_csv(HALF / "data" / "p3_format_bound.csv", encoding="utf-8-sig")
v = fb[fb.arm.str.startswith("designated replacement")].sort_values("unparsed_share", ascending=False).reset_index(drop=True)
# Table S24 lists scorable results only; a vendor-arm result left unscorable by format non-compliance ("needs review")
# is the clearest format case of all and is selected first.
p3 = pd.read_csv(HALF / "data" / "p3_summary.csv", encoding="utf-8-sig")
unsc = p3[(p3.arm == "vendor") & (p3.class_vs_original == "확인 필요")]
rows = [{"wid": r.wid, "title": r.title, "unparsed_share": float(r.n_unparsed) / float(r.n_items) if "n_unparsed" in p3.columns and r.n_items else None,
         "why": "unscorable on the vendor arm (format non-compliance)"} for r in unsc.itertuples(index=False)]
over = v[v.unparsed_share > THRESHOLD]
rows += [{"wid": r.wid, "title": r.title, "unparsed_share": float(r.unparsed_share), "why": f"unparsable share > {THRESHOLD:.0%}"} for r in over.itertuples(index=False)]
nxt = v[v.unparsed_share <= THRESHOLD].head(1)
rows += [{"wid": r.wid, "title": r.title, "unparsed_share": float(r.unparsed_share), "why": "next-highest share (contrast case)"} for r in nxt.itertuples(index=False)]
sel = pd.DataFrame(rows)
print(f"rule: unscorable vendor results ({len(unsc)}) + unparsable share > {THRESHOLD:.0%} ({len(over)}) + next-highest share (1) -> {len(sel)} papers")
adapt = json.load(open(HALF / "harness" / "tierb" / "paraphrase" / "format_adapt.json", encoding="utf-8"))
lines = ["@echo off", f"cd /d {HALF}", "set PYTHONIOENCODING=utf-8"]
for variant in ("f1", "f2"):
    jobs = []
    for r in sel.itertuples(index=False):
        wid = r.wid
        assert wid in adapt and variant in adapt[wid], f"no {variant} adaptation written for {wid}"
        res = json.load(open(HALF / "runs" / "tierb_p3" / "vendor" / wid / "result.json", encoding="utf-8"))
        model = res["arm"]["model"]
        cost = json.load(open(HALF / "runs" / "tierb_p3" / "vendor" / wid / "budget.json", encoding="utf-8"))["cost_usd"]
        jobs.append({"wid": wid, "cap": round(max(2.0, 1.5 * cost), 2), "seeds": 1, "arm": f"format_{variant}", "arm_model": model, "model": model,
                     "paraphrase": variant, "vendor_arm_cost_usd": round(cost, 2), "unparsed_share_vendor": r.unparsed_share, "selected_because": r.why,
                     "title": str(r.title)[:50],
                     "note": f"format adaptation {variant}: baseline items and seed-0 bodies on the successor with one added format sentence"
                             + (" and reasoning_effort none" if variant == "f2" else "") + "; one pass"})
        print(f"  {variant} {wid} {model} cap {jobs[-1]['cap']} (vendor arm {cost:.2f} USD, unparsed {'n/a' if pd.isna(r.unparsed_share) else format(r.unparsed_share, '.1%')}; {r.why}) {str(r.title)[:45]}")
    out = HALF / "harness" / "tierb" / f"queue_format_{variant}.json"
    json.dump(jobs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{variant}: {len(jobs)} papers, caps sum {sum(j['cap'] for j in jobs):.2f} USD -> {out.name}")
    lines += [f"echo START format adaptation {variant} ({len(jobs)} papers) %date% %time% >> runs\\format_cases.log",
              f"python harness\\run_queue.py --queue harness\\tierb\\queue_format_{variant}.json --total-cap 50 --workers 4 >> runs\\format_cases.log 2>&1",
              f"echo FORMAT {variant} DONE %date% %time% >> runs\\format_cases.log"]
lines.append("echo FORMAT CASES DONE %date% %time% >> runs\\format_cases.log")
(HALF / "runs" / "format_cases_launch.cmd").write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
print("launcher runs/format_cases_launch.cmd")
