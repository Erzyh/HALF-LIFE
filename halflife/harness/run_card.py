"""Execute the generation arm of a claim card and archive every call.

Usage: python run_card.py T1 [--arm baseline_alive] [--samples 10] [--workers 4]

Outputs under halflife/runs/<card>/<arm>/:
  calls.jsonl      one line per API call: full request body, full response JSON,
                   latency, timestamps, sha256 of both (the L1 archive)
  samples.jsonl    HumanEval-format samples (task_id, completion, full_response)
                   consumable by the paper's own evaluator
  budget.json      running cost; the run aborts cleanly at the card's cap
Resumable: (task_id, sample_idx) pairs already in calls.jsonl are skipped.
"""
import argparse, json, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from openai_client import OpenAIClient, cost_usd, sha256  # noqa: E402

HALF = HERE.parent
EXTERNAL = HALF / "external" / "human-eval-bia"
sys.path.insert(0, str(EXTERNAL))
from human_eval.data import read_problems, extract_python  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card")
    ap.add_argument("--arm", default="baseline_alive")
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true", help="build prompts, print token-free estimate, no API calls")
    a = ap.parse_args()

    card = json.loads((HERE / "cards" / f"{a.card}_bia_codegen.json").read_text(encoding="utf-8"))
    arm = next(x for x in card["arms"] if x["arm"] == a.arm)
    model = arm["model"]
    pricing = card["budget"]["pricing_usd_per_1m"][model]
    cap = float(card["budget"]["cap_usd"])
    n_samples = a.samples or int(card["protocol"]["samples_per_task"])
    template = card["protocol"]["prompt_template"]

    problems = read_problems(str(EXTERNAL / "data" / "human-eval-bia.jsonl"))
    out = HALF / "runs" / a.card / a.arm
    out.mkdir(parents=True, exist_ok=True)
    calls_path, samples_path, budget_path = out / "calls.jsonl", out / "samples.jsonl", out / "budget.json"

    done = set()
    if calls_path.exists():
        for line in open(calls_path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                done.add((r["task_id"], r["sample_idx"]))

    jobs = [(tid, i) for i in range(n_samples) for tid in problems if (tid, i) not in done]
    print(f"[{a.card}/{a.arm}] model={model} tasks={len(problems)} samples/task={n_samples} "
          f"pending={len(jobs)} done={len(done)} cap=${cap}", flush=True)
    if a.dry_run:
        return

    spent = json.loads(budget_path.read_text())["spent_usd"] if budget_path.exists() else 0.0
    lock = threading.Lock()
    client = OpenAIClient()
    stop = threading.Event()
    calls_f = open(calls_path, "a", encoding="utf-8")
    samples_f = open(samples_path, "a", encoding="utf-8")

    def one(tid, idx):
        if stop.is_set():
            return None
        prompt = template.replace("{input_code}", problems[tid]["prompt"])
        body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        ts = now()
        resp, latency, status = client.chat(body)
        return tid, idx, body, resp, latency, status, ts

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(one, tid, idx) for tid, idx in jobs]
        n_ok = 0
        for f in as_completed(futs):
            r = f.result()
            if r is None:
                continue
            tid, idx, body, resp, latency, status, ts = r
            text = resp["choices"][0]["message"]["content"].strip()
            code = extract_python(text)
            c = cost_usd(resp.get("usage", {}), pricing)
            with lock:
                spent += c
                calls_f.write(json.dumps({
                    "card": a.card, "arm": a.arm, "task_id": tid, "sample_idx": idx,
                    "ts_utc": ts, "latency_ms": latency, "http_status": status,
                    "request": body, "response": resp,
                    "model_served": resp.get("model"), "system_fingerprint": resp.get("system_fingerprint"),
                    "usage": resp.get("usage"), "cost_usd": round(c, 6),
                    "sha256_request": sha256(body), "sha256_response": sha256(resp),
                }, ensure_ascii=False) + "\n")
                samples_f.write(json.dumps({"task_id": tid, "completion": code, "full_response": text,
                                            "sample_idx": idx}) + "\n")
                calls_f.flush(); samples_f.flush()
                budget_path.write_text(json.dumps({"spent_usd": round(spent, 4), "cap_usd": cap,
                                                   "updated": now()}, indent=2))
                n_ok += 1
                if n_ok % 25 == 0:
                    print(f"  {n_ok}/{len(jobs)} done, spent ${spent:.2f}", flush=True)
                if spent >= cap:
                    print(f"[budget] cap ${cap} reached at ${spent:.2f} — stopping", flush=True)
                    stop.set()
    calls_f.close(); samples_f.close()
    print(f"[{a.card}/{a.arm}] finished. calls={n_ok} spent=${spent:.2f}", flush=True)


if __name__ == "__main__":
    main()
