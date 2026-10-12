"""Temperature sensitivity check (approved 2026-10-02): does the temperature-0 assumption for papers silent on decoding change their class?

For each paper of harness/tierb/queue_temp1.json (rule in scripts/temperature_queues.py: paper silent on temperature, configuration
assumed 0, generation or free-text task) the table gives, on the paper's scale, the reported value, the pre-retirement baseline at
temperature 0 (the configuration's assumption) and the re-run at temperature 1.0 (the API default) with the baseline's seed count,
with intervals, unparsable counts, the class of each against the reported value under the prompt-level rule, and the spend.
Writes data/temperature_check.csv. No API calls.
"""
import json
import sys
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "scripts"))
from p3_summary import classify, scaled, unit_of  # noqa: E402


def load(p):
    p = Path(p)
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def main():
    jobs = load(HALF / "harness" / "tierb" / "queue_temp1.json") or []
    rows = []
    for j in jobs:
        wid = j["wid"]
        base = load(HALF / "runs" / "tierb" / wid / "result.json")
        t1 = load(HALF / "runs" / "tierb_p3" / "temp1" / wid / "result.json")
        bs = [load(q) for q in (HALF / "runs" / "tierb_p3" / "temp1" / wid).glob("**/budget.json")]   # main battery plus any judge stage
        b = {"cost_usd": sum(float(x.get("cost_usd") or 0) for x in bs if x)} if bs else None
        orig = (base or {}).get("original_value")
        bv, blo, bhi = scaled(base) if base else (None, None, None)
        tv, tlo, thi = scaled(t1) if t1 else (None, None, None)
        unit = unit_of(orig, bv) if (orig is not None and bv is not None) else 1.0
        rows.append({"wid": wid, "title": str((base or {}).get("title", ""))[:60], "model": j["model"], "task_type": j.get("task_type"), "metric": (base or {}).get("metric"),
                     "seeds": j["seeds"], "original": orig,
                     "baseline_t0": None if bv is None else round(bv, 3), "baseline_t0_ci_lo": blo, "baseline_t0_ci_hi": bhi,
                     "baseline_t0_unparsed": ((base or {}).get("reexecution") or {}).get("unparsed"),
                     "baseline_t0_class": classify(orig, bv, blo, bhi) if (orig is not None and bv is not None) else None,
                     "rerun_t1": None if tv is None else round(tv, 3), "rerun_t1_ci_lo": tlo, "rerun_t1_ci_hi": thi,
                     "rerun_t1_unparsed": ((t1 or {}).get("reexecution") or {}).get("unparsed"),
                     "rerun_t1_class": classify(orig, tv, tlo, thi) if (orig is not None and tv is not None) else None,
                     "t1_minus_t0_pts": None if (tv is None or bv is None) else round((tv - bv) * unit, 2),
                     "t1_minus_original_pts": None if (tv is None or orig is None) else round((tv - orig) * unit, 2),
                     "cost_usd": None if not b else round(b["cost_usd"], 2)})
    df = pd.DataFrame(rows)
    df.to_csv(HALF / "data" / "temperature_check.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 240, "display.max_columns", 30, "display.max_colwidth", 28):
        print(df.drop(columns=["title"]).to_string(index=False))
    done = df[df.rerun_t1.notna()]
    if len(done):
        print("papers done:", len(done), "| class changed:", int((done.baseline_t0_class != done.rerun_t1_class).sum()),
              "| median |t1 - t0|:", round(done.t1_minus_t0_pts.abs().median(), 2), "| spend:", round(done.cost_usd.fillna(0).sum(), 2))


if __name__ == "__main__":
    main()
