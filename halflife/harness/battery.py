"""Generic request battery executor: run a list of chat-completion requests, archive every call.

Used by the per-card adapters (harness/adapters/*.py) and by the Tier B runner. Each request
is one line of JSONL: {"id": str, "seed_idx": int, "body": {...chat completion body...},
"meta": {...anything the adapter wants back...}}.

Outputs under <run_dir>/:
  calls.jsonl   one line per call: request body, full response JSON, latency, timestamps,
                sha256 of both, cost (the L1 archive)
  budget.json   running cost; the run stops cleanly at the cap (in-flight calls finish)
Resumable: (id, seed_idx) pairs already in calls.jsonl with a 200 response are skipped.

CLI:  python battery.py requests.jsonl run_dir --cap 5 [--workers 4] [--dry-run]
API:  from battery import run_battery, load_results
"""
import argparse, json, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from openai_client import OpenAIClient, cost_usd, sha256  # noqa: E402

PRICING = json.loads((HERE / "pricing.json").read_text(encoding="utf-8"))["usd_per_1m"]


def now():
    return datetime.now(timezone.utc).isoformat()


def pricing_for(model):
    if model in PRICING:
        return PRICING[model]
    for k, v in PRICING.items():          # alias -> dated snapshot prefix match
        if model.startswith(k) or k.startswith(model):
            return v
    raise KeyError(f"no pricing for model {model}; add it to harness/pricing.json")


def estimate(requests, default_out=60):
    """Rough token estimate (chars / 4) for a dry run."""
    tin = tout = 0.0
    for r in requests:
        body = r["body"]
        chars = sum(len(m.get("content") or "") for m in body.get("messages", []))
        tin += chars / 4 + 8 * len(body.get("messages", []))
        tout += body.get("max_tokens") or body.get("max_completion_tokens") or default_out
    return tin, tout


def load_results(run_dir):
    out = {}
    p = Path(run_dir) / "calls.jsonl"
    if p.exists():
        for line in open(p, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if r.get("status") == 200:
                    # Gemini's OpenAI-compatible endpoint returns a choice without a message when its safety filter
                    # blocks the reply (finish_reason "content_filter: ..."); give it an empty message so that the
                    # analysis and the hooks see an unparsable reply instead of crashing (the raw record is untouched)
                    for ch in (r.get("response") or {}).get("choices") or []:
                        if "message" not in ch:
                            ch["message"] = {"role": "assistant", "content": None}
                            ch["blocked"] = True
                    out[(r["id"], r.get("seed_idx", 0))] = r
    return out


def run_battery(requests, run_dir, cap_usd, workers=4, dry_run=False, label=""):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    calls_path, budget_path = run_dir / "calls.jsonl", run_dir / "budget.json"
    done = load_results(run_dir)
    todo = [r for r in requests if (r["id"], r.get("seed_idx", 0)) not in done]
    models = {r["body"]["model"] for r in todo}
    budget = {"label": label, "calls": len(done), "errors": 0, "cost_usd": 0.0, "tokens_in": 0, "tokens_out": 0,
              "cap_usd": cap_usd, "stopped_at_cap": False, "started": now(), "updated": now()}
    if budget_path.exists():
        old = json.loads(budget_path.read_text(encoding="utf-8"))
        for k in ("cost_usd", "tokens_in", "tokens_out", "errors"):
            budget[k] = old.get(k, 0)
        budget["started"] = old.get("started", budget["started"])
    if dry_run:
        tin, tout = estimate(todo)
        est = sum(tin / 1e6 * pricing_for(m)["input"] + tout / 1e6 * pricing_for(m)["output"] for m in models) if models else 0
        print(f"[dry-run] {label}: {len(todo)} calls pending ({len(done)} done); ~{tin/1e3:.0f}k in / ~{tout/1e3:.0f}k out tokens; "
              f"~${est:.2f} (cap ${cap_usd})", flush=True)
        return {"pending": len(todo), "done": len(done), "est_usd": est}
    if not todo:
        print(f"{label}: nothing to do ({len(done)} calls already archived)", flush=True)
        return budget

    client = OpenAIClient()
    lock = threading.Lock()
    stop = threading.Event()

    consecutive_errors = [0]

    def one(req):
        if stop.is_set():
            return None
        try:
            resp, latency, status = client.chat(req["body"])
        except Exception as e:                       # retries exhausted, quota gone, network down ...
            msg = str(e)
            with lock:
                budget["errors"] += 1
                consecutive_errors[0] += 1
                budget["last_error"] = msg[:300]
                budget["updated"] = now()
                if "insufficient_quota" in msg or "billing" in msg.lower() or consecutive_errors[0] >= 5:
                    budget["stopped_on_errors"] = True
                    stop.set()
                budget_path.write_text(json.dumps(budget, indent=2), encoding="utf-8")
            print(f"  {label}: call failed ({msg[:120]})", flush=True)
            return None
        consecutive_errors[0] = 0
        rec = {"id": req["id"], "seed_idx": req.get("seed_idx", 0), "meta": req.get("meta", {}), "ts": now(),
               "request": req["body"], "response": resp, "status": status, "latency_ms": latency,
               "sha_request": sha256(req["body"]), "sha_response": sha256(resp),
               "model_served": (resp or {}).get("model"), "system_fingerprint": (resp or {}).get("system_fingerprint")}
        c = 0.0
        if status == 200 and resp.get("usage"):
            c = cost_usd(resp["usage"], pricing_for(req["body"]["model"]))
        rec["cost_usd"] = round(c, 6)
        with lock:
            with open(calls_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if status == 200:
                budget["calls"] += 1
                budget["cost_usd"] += c
                u = resp.get("usage") or {}
                budget["tokens_in"] += u.get("prompt_tokens", 0)
                budget["tokens_out"] += u.get("completion_tokens", 0)
            else:
                budget["errors"] += 1
            budget["updated"] = now()
            if budget["cost_usd"] >= cap_usd:
                budget["stopped_at_cap"] = True
                stop.set()
            if budget["calls"] % 25 == 0 or stop.is_set():
                budget_path.write_text(json.dumps(budget, indent=2), encoding="utf-8")
        return status

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, r) for r in todo]
        n = 0
        for f in as_completed(futs):
            n += 1
            if n % 50 == 0:
                print(f"  {label}: {n}/{len(todo)} calls, ${budget['cost_usd']:.2f}, errors {budget['errors']}", flush=True)
            if stop.is_set():
                pass
    budget_path.write_text(json.dumps(budget, indent=2), encoding="utf-8")
    print(f"{label}: done {budget['calls']} calls, ${budget['cost_usd']:.2f}, errors {budget['errors']}, "
          f"{time.time()-t0:.0f}s{' (STOPPED AT CAP)' if budget['stopped_at_cap'] else ''}", flush=True)
    return budget


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("requests")
    ap.add_argument("run_dir")
    ap.add_argument("--cap", type=float, required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    reqs = [json.loads(l) for l in open(a.requests, encoding="utf-8") if l.strip()]
    run_battery(reqs, a.run_dir, a.cap, a.workers, a.dry_run, label=Path(a.run_dir).name)


if __name__ == "__main__":
    main()
