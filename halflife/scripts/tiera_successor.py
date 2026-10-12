"""Run a repository-based (Tier A) adapter on a successor model (approved 2026-10-01).

python scripts/tiera_successor.py <adapter file> --model gpt-5.6-sol --arm vendor [--cap 10] -- --dry-run | --run | --analyze [adapter args]

The adapter module is loaded as is; before its main() runs, every module-level Path under runs/<Wid>/ is redirected
from baseline_alive/ to successor_<arm>/ (run directory, run_meta.json, environment_check.json, items.jsonl and the
like), MODEL is replaced by the successor, CAP by --cap, and run_battery is wrapped so that each request body is made
legal for the successor as in harness/tierb_runner.py (reasoning successors: max_tokens -> max_completion_tokens with a
floor of 8,192, temperature/top_p/logprobs/penalties/seed dropped). The baseline archive is never touched. Spend is
written to budget.json of the successor run directory; scripts/tiera_successor_summary.py --log-budget copies it to
budget_log.csv (arm tierA_successor).
"""
import argparse
import importlib.util
import sys
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "harness"))
import battery  # noqa: E402


def successor_body(body, model):
    b = dict(body)
    b["model"] = model
    if model.startswith(("o1", "o3", "o4", "gpt-5")):
        if "max_tokens" in b:
            mt = b.pop("max_tokens")
            if mt is not None:
                b["max_completion_tokens"] = max(int(mt), 8192)
        for k in ("temperature", "top_p", "logprobs", "top_logprobs", "frequency_penalty", "presence_penalty", "seed"):
            b.pop(k, None)
        if b.get("reasoning_effort") == "minimal" and model.startswith("gpt-5.6"):
            b["reasoning_effort"] = "none"
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("adapter")
    ap.add_argument("--model", required=True)
    ap.add_argument("--arm", default="vendor")
    ap.add_argument("--cap", type=float, default=10.0)
    ap.add_argument("--nest", action="store_true", help="map baseline_alive/ to successor_<arm>/run/ for adapters that write next to RUN (RUN.parent)")
    a, rest = ap.parse_known_args()
    a.rest = rest
    path = Path(a.adapter)
    if not path.is_absolute():
        path = (HALF / "harness" / path).resolve() if not path.exists() else path.resolve()
    wid = next((p for p in path.stem.split("_") if p.startswith("W")), None)
    if not wid:
        sys.exit("adapter file name must carry the Wid")
    root = HALF / "runs" / wid
    new_root = root / f"successor_{a.arm}"
    new_root.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)
    moved = []
    for name, val in list(vars(mod).items()):
        if isinstance(val, Path):
            try:
                rel = val.resolve().relative_to(root.resolve())
            except ValueError:
                continue
            parts = rel.parts
            if parts and parts[0] == "baseline_alive":
                newp = (new_root / "run").joinpath(*parts[1:]) if a.nest else new_root.joinpath(*parts[1:])
            else:
                newp = new_root.joinpath(*parts)
            setattr(mod, name, newp)
            moved.append((name, str(newp.relative_to(HALF))))
    if not hasattr(mod, "MODEL"):
        sys.exit("adapter has no MODEL global")
    base_model = mod.MODEL
    mod.MODEL = a.model
    if hasattr(mod, "CAP"):
        mod.CAP = a.cap
    real_run = battery.run_battery

    def run_battery(requests, run_dir, cap_usd, *args, **kw):
        reqs = [dict(r, body=successor_body(r["body"], a.model)) for r in requests]
        return real_run(reqs, run_dir, min(float(cap_usd), a.cap), *args, **kw)

    mod.run_battery = run_battery
    (new_root / "successor_meta.json").write_text(__import__("json").dumps(
        {"wid": wid, "baseline_model": base_model, "successor_model": a.model, "arm": a.arm, "cap_usd": a.cap,
         "adapter_args": [x for x in a.rest if x != "--"], "paths_redirected": moved,
         "body_rule": "successor_body in scripts/tiera_successor.py"}, indent=2), encoding="utf-8")
    print(f"[tiera_successor] {wid}: {base_model} -> {a.model}; outputs under {new_root.relative_to(HALF)}; redirected {[m[0] for m in moved]}")
    rest = a.rest[1:] if a.rest[:1] == ["--"] else a.rest
    sys.argv = [str(path)] + rest
    rc = mod.main()
    return rc or 0


if __name__ == "__main__":
    sys.exit(main())
