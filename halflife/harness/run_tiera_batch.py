"""Run a list of Tier A adapter commands one after another, unattended, with a log.

  python harness/run_tiera_batch.py --steps harness/tiera_batch2.json [--log runs/tierA_batch2.log]

The steps file is a JSON list of {"name": str, "args": [str, ...], "stop_group_on_error": true}. Each step runs
`python harness/adapters/<args...>` from the harness folder. Steps that share a "group" are skipped after one of
them fails (so --analyze never runs on a failed --run). Every step's start, return code and duration are appended
to the log and to runs/tierA_batch.log; nothing here calls the API itself.
"""
import argparse, json, subprocess, sys, time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
HALF = HERE.parent
PY = sys.executable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", required=True)
    ap.add_argument("--log", default=str(HALF / "runs" / "tierA_batch.log"))
    a = ap.parse_args()
    steps = json.loads(Path(a.steps).read_text(encoding="utf-8-sig"))
    log = open(a.log, "a", encoding="utf-8")
    failed_groups = set()
    for s in steps:
        group = s.get("group", s["name"])
        if group in failed_groups:
            line = f"{datetime.now():%Y-%m-%d %H:%M} SKIP {s['name']} (earlier step in group {group} failed)"
            print(line, flush=True); log.write(line + "\n"); log.flush()
            continue
        cmd = [PY, str(HERE / "adapters" / s["args"][0])] + s["args"][1:]
        line = f"{datetime.now():%Y-%m-%d %H:%M} START {s['name']}: {' '.join(s['args'])}"
        print(line, flush=True); log.write(line + "\n"); log.flush()
        t0 = time.time()
        rc = subprocess.call(cmd, cwd=str(HERE))
        line = f"{datetime.now():%Y-%m-%d %H:%M} END {s['name']} rc={rc} {time.time()-t0:.0f}s"
        print(line, flush=True); log.write(line + "\n"); log.flush()
        if rc != 0:
            failed_groups.add(group)
    line = f"{datetime.now():%Y-%m-%d %H:%M} batch done; failed groups: {sorted(failed_groups) or 'none'}"
    print(line, flush=True); log.write(line + "\n"); log.flush()


if __name__ == "__main__":
    main()
