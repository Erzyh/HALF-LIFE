"""Run a queue of Tier B configs without supervision, in order, under a total spending cap.

  python harness/run_queue.py --queue harness/tierb/queue_ready.json --total-cap 300
  python harness/run_queue.py --queue ... --dry-run            # estimates only, no API calls

Each job is {"wid": "W...", "cap": 40} (per-paper cap; default 40). The cap covers the paper as a
whole. When the paper's hook has an LLM-judge stage, the main stage is prepared and run with half
of the cap and the judge stage gets whatever is left; if less than $1 is left the judge is skipped
and the queue.log line says so (the earlier version gave each stage the full cap, so one paper
could cost twice its cap). For every job the script runs
  tierb_runner.py <wid> --prepare --cap <main cap>   only when prepare.json is missing or was made
                                                      for another cap, and no calls are archived yet
  tierb_runner.py <wid> --run --cap <main cap>       resumable; archived calls are never repeated
  tierb_runner.py <wid> --judge --cap <cap - main>   only if the hook defines judge_requests
  tierb_runner.py <wid> --analyze
then appends the job's spend to budget_log.csv and to runs/tierb/queue.log. It stops when the money
spent by this invocation reaches --total-cap, or when a job fails twice. Safe to re-run: finished
jobs (result.json present) are skipped unless the job carries "force": true.
A job with "arm_model": "<model id>" (and optionally "arm": "<label>") runs the paper on that model instead
of its own (successor comparison); its archive lives under runs/tierb_p3/<label>/<wid>/ and the budget row
is tagged tierb_p3.
"""
import argparse, csv, json, subprocess, sys, time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
HALF = HERE.parent
RUNS = HALF / "runs" / "tierb"
LOG = RUNS / "queue.log"
PY = sys.executable
MAIN_SHARE = 0.5     # share of the per-paper cap given to the main stage when a judge stage exists
JUDGE_MIN = 1.0      # dollars; below this the judge stage is skipped rather than started


def stage_cost(wid, stage=""):
    b = (RUNS / wid / stage / "budget.json") if stage else (RUNS / wid / "budget.json")
    return json.loads(b.read_text(encoding="utf-8")).get("cost_usd", 0.0) if b.exists() else 0.0


def spent(wid):
    return stage_cost(wid) + stage_cost(wid, "judge")


def has_judge(wid):
    p = HERE / "tierb" / "hooks" / f"{wid}.py"
    return p.exists() and "def judge_requests" in p.read_text(encoding="utf-8")


def prepared_cap(wid):
    p = RUNS / wid / "prepare.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("cap_usd")


def run(args, dry):
    cmd = [PY, str(HERE / "tierb_runner.py")] + args
    print("$", " ".join(args), flush=True)
    if dry and "--run" in args:
        cmd[cmd.index("--run")] = "--dry-run"
    if dry and "--judge" in args:
        return 0
    return subprocess.call(cmd, cwd=str(HERE))


def main():
    global RUNS
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--total-cap", type=float, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=None, help="parallel calls per run (the runner's default is 6; use 1-2 on third-party accounts)")
    a = ap.parse_args()
    jobs = json.loads(Path(a.queue).read_text(encoding="utf-8"))
    RUNS.mkdir(parents=True, exist_ok=True)
    log = open(LOG, "a", encoding="utf-8")
    session_spend = 0.0
    for job in jobs:
        wid, cap = job["wid"], float(job.get("cap", 40))
        arm_model = job.get("arm_model")
        arm = (job.get("arm") or arm_model) if arm_model else None
        extra = ["--model", arm_model, "--arm", arm] if arm_model else []
        if a.workers:
            extra += ["--workers", str(a.workers)]
        if job.get("seeds"):
            extra += ["--seeds", str(job["seeds"])]
        if job.get("max_items"):
            extra += ["--max-items", str(job["max_items"])]
        if job.get("copy_from"):
            extra += ["--copy-from", job["copy_from"]]
        if job.get("paraphrase"):
            extra += ["--paraphrase", job["paraphrase"]]
        armtxt = (" arm=" + arm) if arm_model else ""
        RUNS = (HALF / "runs" / "tierb_p3" / arm) if arm_model else (HALF / "runs" / "tierb")
        RUNS.mkdir(parents=True, exist_ok=True)
        if (RUNS / wid / "result.json").exists() and not job.get("force"):
            print(f"skip {wid}: result.json present", flush=True)
            continue
        if session_spend >= a.total_cap:
            print(f"stop: session spend ${session_spend:.2f} reached the total cap ${a.total_cap}", flush=True)
            break
        judge = has_judge(wid)
        main_cap = round(cap * MAIN_SHARE, 2) if judge else cap
        before = spent(wid)
        t0 = time.time()
        note = ""
        rc = 0
        if prepared_cap(wid) != main_cap and not (RUNS / wid / "calls.jsonl").exists():
            rc = run([wid, "--prepare", "--cap", str(main_cap)] + extra, a.dry_run)
        if rc == 0:
            rc = run([wid, "--run", "--cap", str(main_cap)] + extra, a.dry_run)
            if rc != 0:
                time.sleep(30)
                rc = run([wid, "--run", "--cap", str(main_cap)] + extra, a.dry_run)
        if rc == 0 and judge:
            left = round(cap - stage_cost(wid), 2)
            if left < JUDGE_MIN:
                note = f" judge skipped: main stage used ${stage_cost(wid):.2f} of the ${cap:.0f} cap"
                print(wid + ":" + note, flush=True)
            else:
                rc = run([wid, "--judge", "--cap", str(left)] + extra, a.dry_run)
        if rc == 0 and not a.dry_run:
            rc = run([wid, "--analyze"] + extra, a.dry_run)
        cost = spent(wid) - before
        session_spend += cost
        line = f"{date.today()} {wid}{armtxt} rc={rc} cost=${cost:.2f} session=${session_spend:.2f} {time.time()-t0:.0f}s{note}"
        print(line, flush=True)
        log.write(line + "\n"); log.flush()
        if cost > 0:
            bl = HALF / "budget_log.csv"
            rows = list(csv.reader(open(bl, encoding="utf-8"))) if bl.exists() else []
            prev = float(rows[-1][6]) if len(rows) > 1 else 0.0
            with open(bl, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([str(date.today()), wid, "tierb_p3" if arm_model else "tierb", arm_model or job.get("model", ""), "", round(cost, 2), round(prev + cost, 2), "queue run" + armtxt])
    print(f"queue done: session spend ${session_spend:.2f}", flush=True)


if __name__ == "__main__":
    main()
