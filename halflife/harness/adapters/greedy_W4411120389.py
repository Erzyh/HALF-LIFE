"""Card W4411120389 - The Good, The Bad, and The Greedy: Evaluation of LLMs Should Not Ignore Non-Determinism
(Song, Wang, Li, Lin; NAACL 2025). Core re-executable arm: the HumanEval greedy-vs-sampling gap of gpt-4-turbo-2024-04-09.

Paper, Table 2 (header says N=128): greedy 89.6, sampling mean 84.1, std 2.65, best-worst 11.0; Table 8 one-sample t-test p 1.1e-48.
Released per-run outputs (HF goodbadgreedy/GoodBadGreedy, Apache-2.0; GoodBadGreedy.zip -> sampleeval/humaneval/gpt-4-turbo-2024-04-09_*):
ONE greedy run + 32 sampled runs, not 128. Their own metrics.json give greedy 89.63, mean 84.05, population std 2.645, best-worst 10.98,
i.e. the Table 2 row for GPT-4-Turbo rests on the 32 released runs. Each run is a separate API pass (n=1, 164 calls, 2024-06-14 UTC).

Protocol, from Open-Instruct commit 167a2b4b (eval/codex_humaneval/run_eval.py, OpenAI branch; a copy of the files sits in
external/data/W4411120389/open_instruct_167a2b4b/). The main-branch file in force on the generation date (b6737f62, 2024-04-27) differs
only by the vLLM-only --additional_stop_sequence flag.
  prompt      "Complete the following python function. Please only output the code for the completed function.\\n\\n\\n" + HumanEval prompt
              (run_eval.py:140; prompts = raw example["prompt"], :64) sent as ONE user message (eval/utils.py:363); verified verbatim
              against the 'prompt' field of all 5,412 released calls.
  parameters  top_p=0.95 (run_eval.py:147; the paper text says top-p 1.0), temperature=--temperature (:148; paper: 1.0 for sampling,
              0 for greedy), n=--unbiased_sampling_size_n (:149; released runs carry one choice each). NO max_tokens and NO stop
              sequences on this branch - the codex stop list (:30) feeds only the vLLM (:79-85) and HF (:112-130) branches. All 5,412
              released responses have finish_reason 'stop'.
  scoring     prompt + completion + "\\n" + test + "\\n" + check(entry_point), executed under a timeout
              (eval/codex_humaneval/execution.py:38-42; evaluation.py default timeout 3.0 s); pass@1 = mean over the 164 problems.
  post-proc.  run_eval.py:153-154 use the raw message content, but every released completion is the ```python block(s) of the reply
              (empty string when the reply has no such block). The rule below reproduces 5,412/5,412 released completions; the step
              itself is the authors' own and is not in the released repository.
Decisions 2026-09-18: HumanEval only; top_p 1.0 as the paper states (0.95 = unrun sensitivity, --top-p 0.95 writes a separate run dir);
greedy T=0 x 3 repeats + sampling T=1.0 x N (target 32); per-paper cap $85.

  python adapters/greedy_W4411120389.py --check      # re-score the released samples in our harness (no API calls)
  python adapters/greedy_W4411120389.py --dry-run    # request list + cost estimate, chooses N (no API calls)
  python adapters/greedy_W4411120389.py --run        # cap $85 by default -> runs/W4411120389/baseline_alive/
  python adapters/greedy_W4411120389.py --analyze    # execute archived completions, statistics, judgment, run_meta.json
Code execution happens only in a fresh isolated interpreter per sample (subprocess with a wall-clock timeout).
"""
import argparse, hashlib, json, os, re, subprocess, sys, tempfile, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, run_battery  # noqa: E402

HALF = HERE.parent.parent
sys.path.insert(0, str(HALF / "external" / "human-eval-bia"))
from human_eval.data import read_problems  # noqa: E402  (stdlib-only jsonl/.gz reader, same as harness/run_card.py)

CARD_ID = "W4411120389"
MODEL = "gpt-4-turbo-2024-04-09"
DATA = HALF / "external" / "data" / CARD_ID
PROBLEM_FILE = DATA / "HumanEval.jsonl.gz"            # openai/human-eval data/HumanEval.jsonl.gz (MIT), file commit 463c980b (2021-07-08)
RELEASE = DATA / "sampleeval" / "humaneval"            # members of GoodBadGreedy.zip (HF repo commit c4c9340b), fetched by HTTP range requests
MANIFEST = DATA / "sampleeval_humaneval_gpt4turbo_manifest.json"
OI_SRC = "allenai/open-instruct@167a2b4b eval/codex_humaneval/run_eval.py"
RUNS = HALF / "runs" / CARD_ID
RUN = RUNS / "baseline_alive"
CHECK_JSON = RUNS / "environment_check.json"
CHECK_CACHE = RUNS / "environment_check_executions.jsonl"

CAP = 85.0
N_GREEDY = 3
N_SAMPLE_TARGET = 32
TEMPERATURE_SAMPLE = 1.0        # paper Sec. 2 "Setup": "For sampling, we set the temperature to 1.0 and top-p to 1.0."
TEMPERATURE_GREEDY = 0.0
TOP_P = 1.0                     # paper; Open-Instruct's OpenAI branch hard-codes 0.95 (run_eval.py:147) -> sensitivity only
INSTRUCTION = "Complete the following python function. Please only output the code for the completed function.\n\n\n"  # run_eval.py:140
EXEC_TIMEOUT_S = 10.0           # Open-Instruct: 3 s of exec time inside a forked worker; here a fresh interpreter starts per sample, so allow start-up
EXEC_WORKERS = 8
SAFETY = 1.25                   # cost margin applied to the calibrated estimate when choosing N
ORIGINAL = {"greedy": 89.6, "sample_mean": 84.1, "std": 2.65, "delta_best_worst": 11.0, "gap": 5.5, "N_stated": 128, "N_released": 32,
            "t_test_p": 1.1e-48, "source": "Table 2 (HumanEval, GPT-4-Turbo row), Table 8 (App. A)"}
FENCE = re.compile(r"```python\n(.*?)```", re.S)


def now():
    return datetime.now(timezone.utc).isoformat()


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


# ----------------------------------------------------------------------------------------------------- data
def load_problems():
    if not PROBLEM_FILE.exists():
        sys.exit(f"missing {PROBLEM_FILE} (openai/human-eval data/HumanEval.jsonl.gz)")
    problems = read_problems(str(PROBLEM_FILE))
    assert len(problems) == 164, len(problems)
    return problems


def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def release_dirs():
    greedy = RELEASE / f"{MODEL}_greedy"
    samples = sorted(RELEASE.glob(f"{MODEL}_nochat_sample_*"), key=lambda d: int(d.name.rsplit("_", 1)[1]))
    if not greedy.exists() or not samples:
        sys.exit(f"released samples not found under {RELEASE} (extract sampleeval/humaneval/{MODEL}_* from GoodBadGreedy.zip)")
    return greedy, samples


def load_release_run(d):
    """One released run -> (rows, metrics). rows: 164 dicts with the sent prompt, raw reply, released completion and pass flag."""
    q = read_jsonl(d / "openai_query_results.jsonl")
    r = read_jsonl(d / "codex_eval_predictions.jsonl_results.jsonl")
    assert len(q) == len(r) == 164, (d, len(q), len(r))
    rows = []
    for a, b in zip(q, r):
        rm = a["response_metadata"]
        rm = json.loads(rm) if isinstance(rm, str) else rm
        assert a["id"] == b["task_id"], (d, a["id"], b["task_id"])
        rows.append({"task_id": a["id"], "prompt_sent": a["prompt"], "reply": a["output"], "completion_released": b["completion"],
                     "passed_released": bool(b["passed"]), "usage": rm.get("usage") or {}, "model": rm.get("model"),
                     "fingerprint": rm.get("system_fingerprint"), "created": rm.get("created"),
                     "finish": rm["choices"][0].get("finish_reason"), "n_choices": len(rm["choices"])})
    metrics = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    return rows, metrics


# ------------------------------------------------------------------------------------------- prompt / post-processing
def build_prompt(problem):
    return INSTRUCTION + problem["prompt"]                      # run_eval.py:140 with prompts = example["prompt"] (:64)


def extract_code(reply):
    """Authors' post-processing (inferred): concatenate the ```python fenced blocks and strip; empty when there is no such block.
    Not in Open-Instruct (run_eval.py:153-154 keep the raw content); reproduces 5,412/5,412 released completions (--check verifies)."""
    return "\n".join(FENCE.findall(reply)).strip()


def extract_code_lenient(reply):
    """Sensitivity variant: a reply without any ```python block is used as-is instead of becoming an empty completion."""
    code = extract_code(reply)
    return code if (code or "```python" in reply) else reply


# ------------------------------------------------------------------------------------------------- execution
def check_program(problem, completion):
    # Open-Instruct eval/codex_humaneval/execution.py:38-42 (identical to openai/human-eval)
    return problem["prompt"] + completion + "\n" + problem["test"] + "\n" + f"check({problem['entry_point']})"


def run_check(problem, completion, timeout=EXEC_TIMEOUT_S):
    """Run one check program in a fresh isolated interpreter (subprocess.run with a wall-clock timeout).
    Stands in for execution.py's fork + exec + signal.alarm design, which does not work on Windows."""
    with tempfile.TemporaryDirectory(prefix="he_", ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "prog.py")
        Path(path).write_text(check_program(problem, completion), encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, "-I", "-X", "utf8", path], cwd=td, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "timed out"
    if r.returncode == 0:
        return "passed"
    err = [l for l in r.stderr.decode("utf-8", "replace").splitlines() if l.strip()]
    return "failed: " + (err[-1][:200] if err else f"exit code {r.returncode}")


def execute_many(items, problems, cache_path, label=""):
    """items: dicts {key, task_id, completion}. Returns {key: result string}. Results are cached by sha256 of the check program."""
    cache = {}
    if cache_path.exists():
        for line in open(cache_path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                cache[r["sha"]] = r["result"]
    out, todo = {}, []
    for it in items:
        it["sha"] = hashlib.sha256(check_program(problems[it["task_id"]], it["completion"]).encode("utf-8")).hexdigest()
        if it["sha"] in cache:
            out[it["key"]] = cache[it["sha"]]
        else:
            todo.append(it)
    if todo:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        print(f"  executing {len(todo)} programs ({label}; {len(items) - len(todo)} cached) ...", flush=True)
        with ThreadPoolExecutor(EXEC_WORKERS) as ex, open(cache_path, "a", encoding="utf-8") as f:
            futs = {ex.submit(run_check, problems[it["task_id"]], it["completion"]): it for it in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                it, res = futs[fut], fut.result()
                out[it["key"]] = res
                cache[it["sha"]] = res
                f.write(json.dumps({"sha": it["sha"], "task_id": it["task_id"], "result": res}) + "\n")
                if i % 1000 == 0:
                    print(f"    {i}/{len(todo)} ({time.time() - t0:.0f}s)", flush=True)
        print(f"  done in {time.time() - t0:.0f}s", flush=True)
    return out


# ------------------------------------------------------------------------------------------------- statistics
def run_stats(scores):
    a = np.asarray(scores, float)
    return {"n_runs": int(a.size), "mean": float(a.mean()), "std_pop": float(a.std(ddof=0)),
            "std_sample": float(a.std(ddof=1)) if a.size > 1 else None, "max": float(a.max()), "min": float(a.min()),
            "delta_best_worst": float(a.max() - a.min()), "scores": [round(float(x), 3) for x in a]}


def t_test(scores, greedy):
    """One-sample t-test of the per-run scores against the greedy score (paper App. A)."""
    if len(scores) < 2:
        return {"t": None, "p": None, "df": len(scores) - 1}
    t = stats.ttest_1samp(np.asarray(scores, float), greedy)
    return {"t": float(t.statistic), "p": float(t.pvalue), "df": len(scores) - 1}


def per_problem_stats(S, G):
    """S: problems x sampled runs (0/1); G: problems x greedy repeats (0/1)."""
    rate = S.mean(axis=1)
    g = np.median(G, axis=1) if G.shape[1] else np.full(S.shape[0], np.nan)
    return {"always_solved": int((rate == 1).sum()), "never_solved": int((rate == 0).sum()),
            "unstable": int(((rate > 0) & (rate < 1)).sum()), "oracle_any_pass_pct": float((rate > 0).mean() * 100),
            "mean_per_problem_variance": float((rate * (1 - rate)).mean()),
            "per_problem_rate_quartiles": [float(x) for x in np.percentile(rate, [25, 50, 75])],
            "greedy_pass_sample_rate_below_half": int(((g == 1) & (rate < 0.5)).sum()),
            "greedy_fail_sample_rate_at_least_half": int(((g == 0) & (rate >= 0.5)).sum()),
            "greedy_fail_some_sample_pass": int(((g == 0) & (rate > 0)).sum())}


def bootstrap(S, G, n_boot=1000, seed=0):
    """Percentile 95% CIs over problems for the greedy median, the sampling mean and their gap (points)."""
    rng = np.random.default_rng(seed)
    n = S.shape[0]
    gm, sm, gap = [], [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        g = float(np.median(G[idx].mean(axis=0))) * 100
        s = float(S[idx].mean()) * 100
        gm.append(g); sm.append(s); gap.append(g - s)
    ci = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]
    return {"greedy_median_ci95": ci(gm), "sample_mean_ci95": ci(sm), "gap_ci95": ci(gap), "n_boot": n_boot, "seed": seed}


def judge(greedy_median, sample_mean, p):
    """Card judgment rule (ANALYSIS_PLAN Sec. 1, method_effect, as instantiated in the card)."""
    gap = greedy_median - sample_mean
    if sample_mean >= greedy_median:
        return "사망 (dead)", gap
    if p is not None and p < 0.05 and gap >= 2.0:
        return "생존 (survived)", gap
    return "부분 생존 (partial)", gap


# -------------------------------------------------------------------------------------------------------- --check
def check(verbose=True):
    problems = load_problems()
    greedy_dir, sample_dirs = release_dirs()
    runs = {"greedy": load_release_run(greedy_dir)}
    for d in sample_dirs:
        runs[d.name.rsplit("_", 1)[1]] = load_release_run(d)
    sample_keys = [k for k in runs if k != "greedy"]

    n_pairs = prompt_ok = data_ok = rule_ok = 0
    nofence, served, fps, finish, nch, created = Counter(), Counter(), Counter(), Counter(), Counter(), []
    usage = {"greedy": [], "sample": []}
    for name, (rows, _) in runs.items():
        arm = "greedy" if name == "greedy" else "sample"
        for r in rows:
            n_pairs += 1
            prompt_ok += r["prompt_sent"] == build_prompt(problems[r["task_id"]])
            data_ok += r["prompt_sent"].endswith(problems[r["task_id"]]["prompt"])
            rule_ok += extract_code(r["reply"]) == r["completion_released"]
            nofence[arm] += "```python" not in r["reply"]
            served[r["model"]] += 1; fps[r["fingerprint"]] += 1; finish[r["finish"]] += 1; nch[r["n_choices"]] += 1
            created.append(r["created"])
            usage[arm].append((r["usage"].get("prompt_tokens", 0), r["usage"].get("completion_tokens", 0)))

    canon = execute_many([{"key": t, "task_id": t, "completion": p["canonical_solution"]} for t, p in problems.items()],
                         problems, CHECK_CACHE, "canonical solutions")
    canon_pass = sum(v == "passed" for v in canon.values())

    items = []
    for name, (rows, _) in runs.items():
        for r in rows:
            items.append({"key": f"{name}|{r['task_id']}", "task_id": r["task_id"], "completion": r["completion_released"]})
            lenient = extract_code_lenient(r["reply"])
            if lenient != r["completion_released"]:
                items.append({"key": f"{name}|{r['task_id']}|lenient", "task_id": r["task_id"], "completion": lenient})
    results = execute_many(items, problems, CHECK_CACHE, "released completions")

    per_run, disagreements, agree = {}, [], 0
    flags_rescored, flags_released, flags_lenient = {}, {}, {}
    for name, (rows, metrics) in runs.items():
        ours, ours_len, theirs = [], [], []
        for r in rows:
            res = results[f"{name}|{r['task_id']}"]
            p = res == "passed"
            kl = f"{name}|{r['task_id']}|lenient"
            pl = results[kl] == "passed" if kl in results else p
            ours.append(p); ours_len.append(pl); theirs.append(r["passed_released"])
            if p == r["passed_released"]:
                agree += 1
            else:
                disagreements.append({"run": name, "task_id": r["task_id"], "released": r["passed_released"], "ours": res[:160]})
        per_run[name] = {"released_metrics_json": metrics["pass@1"] * 100, "released_flags": float(np.mean(theirs) * 100),
                         "rescored": float(np.mean(ours) * 100), "rescored_lenient": float(np.mean(ours_len) * 100)}
        flags_rescored[name], flags_released[name], flags_lenient[name] = ours, theirs, ours_len

    tids = [r["task_id"] for r in runs["greedy"][0]]
    S_re = np.array([flags_rescored[k] for k in sample_keys], int).T          # problems x runs
    S_rel = np.array([flags_released[k] for k in sample_keys], int).T
    S_len = np.array([flags_lenient[k] for k in sample_keys], int).T
    G_re = np.array(flags_rescored["greedy"], int)[:, None]
    G_len = np.array(flags_lenient["greedy"], int)[:, None]

    rel = run_stats([per_run[k]["released_metrics_json"] for k in sample_keys])
    ours_stats = run_stats([per_run[k]["rescored"] for k in sample_keys])
    len_stats = run_stats([per_run[k]["rescored_lenient"] for k in sample_keys])
    g_rel, g_ours, g_len = per_run["greedy"]["released_metrics_json"], per_run["greedy"]["rescored"], per_run["greedy"]["rescored_lenient"]
    tt_rel, tt_ours = t_test(rel["scores"], g_rel), t_test(ours_stats["scores"], g_ours)
    tt_flags = t_test(S_re.flatten() * 100.0, g_ours)      # alternative construction: every sample as an observation
    boot = bootstrap(S_re, G_re)
    boot_len = bootstrap(S_len, G_len)
    label, gap = judge(g_ours, ours_stats["mean"], tt_ours["p"])

    mean_in = {a: float(np.mean([u[0] for u in usage[a]])) for a in usage}
    mean_out = {a: float(np.mean([u[1] for u in usage[a]])) for a in usage}
    cs = [c for c in created if c]
    summary = {
        "card_id": CARD_ID, "checked_utc": now(), "model": MODEL, "python": sys.version.split()[0],
        "release": {"source": "HF goodbadgreedy/GoodBadGreedy GoodBadGreedy.zip (Apache-2.0), members sampleeval/humaneval/gpt-4-turbo-2024-04-09_*",
                    "n_sampled_runs": len(sample_keys), "n_greedy_runs": 1, "n_calls": n_pairs,
                    "served_models": dict(served), "n_fingerprints": len(fps), "finish_reasons": dict(finish), "choices_per_call": dict(nch),
                    "created_utc_range": [datetime.fromtimestamp(min(cs), timezone.utc).isoformat(), datetime.fromtimestamp(max(cs), timezone.utc).isoformat()] if cs else None,
                    "mean_prompt_tokens": mean_in, "mean_completion_tokens": mean_out,
                    "manifest_sha256": json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else None},
        "prompt_check": {"prompt_verbatim_matches": prompt_ok, "humaneval_prompt_matches_our_data_file": data_ok, "n": n_pairs,
                         "instruction": INSTRUCTION, "source": f"{OI_SRC}:140 (single user message, eval/utils.py:363)"},
        "postprocessing_check": {"rule": "'\\n'.join(re.findall(r'```python\\n(.*?)```', reply, re.S)).strip()", "matches": rule_ok, "n": n_pairs,
                                 "replies_without_python_fence": dict(nofence),
                                 "note": "not in Open-Instruct (run_eval.py:153-154 use the raw content); authors' own step, inferred"},
        "canonical_solutions": {"passed": canon_pass, "n": len(problems)},
        "per_run": per_run, "flag_agreement": {"agree": agree, "disagree": len(disagreements), "disagreements": disagreements},
        "released": {"greedy": g_rel, "sample": rel, "t_test_runs_vs_greedy": tt_rel},
        "rescored": {"greedy": g_ours, "sample": ours_stats, "t_test_runs_vs_greedy": tt_ours, "t_test_all_samples_vs_greedy": tt_flags,
                     "gap": g_ours - ours_stats["mean"], "bootstrap": boot, "per_problem": per_problem_stats(S_re, G_re),
                     "judgment_of_released_data": label},
        "rescored_lenient": {"greedy": g_len, "sample": len_stats, "gap": g_len - len_stats["mean"], "bootstrap": boot_len},
        "paper": ORIGINAL,
        "per_problem_flags": {"task_ids": tids, "greedy_rescored": flags_rescored["greedy"], "sample_rescored": S_re.tolist(),
                              "sample_released": S_rel.tolist()},
        "execution": {"timeout_s": EXEC_TIMEOUT_S, "workers": EXEC_WORKERS, "mode": "fresh isolated interpreter per sample (subprocess.run)"},
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    CHECK_JSON.write_text(json.dumps(summary, indent=2, default=_json_default), encoding="utf-8")
    if verbose:
        p = summary
        print(f"\n[{CARD_ID} --check] released runs: 1 greedy + {len(sample_keys)} sampled (paper header: N=128); {n_pairs} calls; "
              f"served {dict(served)}; {len(fps)} fingerprints; finish {dict(finish)}; choices/call {dict(nch)}")
        print(f"  created {p['release']['created_utc_range']}")
        print(f"  prompt verbatim (instruction + HumanEval prompt): {prompt_ok}/{n_pairs}; HumanEval prompt == our data file: {data_ok}/{n_pairs}")
        print(f"  post-processing rule reproduces released completions: {rule_ok}/{n_pairs}; replies without a ```python fence: {dict(nofence)} "
              f"(released completion empty -> scored failed)")
        print(f"  canonical solutions pass: {canon_pass}/{len(problems)}; released pass flags reproduced: {agree}/{n_pairs} "
              f"({len(disagreements)} disagreements)")
        print(f"\n  {'':28s}{'paper':>10s}{'released':>12s}{'re-scored':>12s}{'lenient':>10s}")
        print(f"  {'greedy pass@1':28s}{ORIGINAL['greedy']:10.1f}{g_rel:12.2f}{g_ours:12.2f}{g_len:10.2f}")
        print(f"  {'sampling mean pass@1':28s}{ORIGINAL['sample_mean']:10.1f}{rel['mean']:12.2f}{ours_stats['mean']:12.2f}{len_stats['mean']:10.2f}")
        print(f"  {'std over runs (pop.)':28s}{ORIGINAL['std']:10.2f}{rel['std_pop']:12.3f}{ours_stats['std_pop']:12.3f}{len_stats['std_pop']:10.3f}")
        print(f"  {'best - worst run':28s}{ORIGINAL['delta_best_worst']:10.1f}{rel['delta_best_worst']:12.2f}{ours_stats['delta_best_worst']:12.2f}{len_stats['delta_best_worst']:10.2f}")
        print(f"  {'gap greedy - mean':28s}{ORIGINAL['gap']:10.1f}{g_rel - rel['mean']:12.2f}{g_ours - ours_stats['mean']:12.2f}{g_len - len_stats['mean']:10.2f}")
        print(f"  {'t-test p (runs vs greedy)':28s}{ORIGINAL['t_test_p']:10.1e}{tt_rel['p']:12.1e}{tt_ours['p']:12.1e}")
        print(f"  t-test with every sample as an observation (n={S_re.size}): p={tt_flags['p']:.1e}")
        print(f"  bootstrap 95% CI over problems (re-scored): greedy {boot['greedy_median_ci95']}, mean {boot['sample_mean_ci95']}, gap {boot['gap_ci95']}")
        pp = p["rescored"]["per_problem"]
        print(f"  per problem: always solved {pp['always_solved']}, never {pp['never_solved']}, unstable {pp['unstable']}, oracle any-pass {pp['oracle_any_pass_pct']:.1f}%")
        print(f"  judgment rule applied to the released data: {label} (gap {gap:.2f})")
        print(f"  token usage per call: prompt {mean_in}, completion {mean_out}")
        print(f"  -> {CHECK_JSON}")
    return summary


# ------------------------------------------------------------------------------------------------- requests
def build_requests(n_sample, top_p=TOP_P, problems=None):
    problems = problems or load_problems()
    reqs = []
    for rep in range(N_GREEDY):                                    # greedy repeats first (cheap), then sampling run by run
        for tid, p in problems.items():
            reqs.append({"id": f"greedy|{tid}", "seed_idx": rep, "meta": {"arm": "greedy", "task_id": tid, "repeat": rep},
                         "body": {"model": MODEL, "messages": [{"role": "user", "content": build_prompt(p)}],
                                  "temperature": TEMPERATURE_GREEDY, "top_p": top_p, "n": 1}})
    for k in range(n_sample):
        for tid, p in problems.items():
            reqs.append({"id": f"sample|{tid}", "seed_idx": k, "meta": {"arm": "sample", "task_id": tid, "sample_idx": k},
                         "body": {"model": MODEL, "messages": [{"role": "user", "content": build_prompt(p)}],
                                  "temperature": TEMPERATURE_SAMPLE, "top_p": top_p, "n": 1}})
    return reqs


def calibrated_cost(n_sample, mean_in, mean_out, price=(10.0, 30.0)):
    """USD from the released runs' measured token usage (prompt/completion means per arm), n=1 per call."""
    g = 164 * N_GREEDY * (mean_in["greedy"] * price[0] + mean_out["greedy"] * price[1]) / 1e6
    s = 164 * n_sample * (mean_in["sample"] * price[0] + mean_out["sample"] * price[1]) / 1e6
    return g + s


def release_usage():
    if CHECK_JSON.exists():
        c = json.loads(CHECK_JSON.read_text(encoding="utf-8"))
        return c["release"]["mean_prompt_tokens"], c["release"]["mean_completion_tokens"]
    greedy_dir, sample_dirs = release_dirs()
    usage = {"greedy": [], "sample": []}
    for arm, dirs in (("greedy", [greedy_dir]), ("sample", sample_dirs)):
        for d in dirs:
            for r in load_release_run(d)[0]:
                usage[arm].append((r["usage"].get("prompt_tokens", 0), r["usage"].get("completion_tokens", 0)))
    return ({a: float(np.mean([u[0] for u in usage[a]])) for a in usage}, {a: float(np.mean([u[1] for u in usage[a]])) for a in usage})


def choose_n(cap, target, mean_in, mean_out):
    n_max = 0
    while calibrated_cost(n_max + 1, mean_in, mean_out) * SAFETY <= cap:
        n_max += 1
    return min(target, n_max), n_max


def run_dir_for(top_p):
    return RUN if abs(top_p - TOP_P) < 1e-9 else RUN.parent / f"baseline_alive_topp{str(top_p).replace('.', '')}"


def dry_run(n_target, cap, top_p):
    mean_in, mean_out = release_usage()
    n, n_max = choose_n(cap, n_target, mean_in, mean_out)
    reqs = build_requests(n, top_p)
    rd = run_dir_for(top_p)
    est = run_battery(reqs, rd, cap, dry_run=True, label=f"{CARD_ID} top_p={top_p}")
    cal = calibrated_cost(n, mean_in, mean_out)
    print(f"[dry-run] requests: {164 * N_GREEDY} greedy (3 repeats x 164, T=0) + {164 * n} sampling ({n} runs x 164, T={TEMPERATURE_SAMPLE}) "
          f"= {len(reqs)} calls; top_p {top_p}; no max_tokens, no stop (as the Open-Instruct OpenAI branch)")
    print(f"[dry-run] battery estimate (chars/4 in, 60 out tokens per call by default): ~${est['est_usd']:.2f}")
    print(f"[dry-run] calibrated on the released runs' usage (prompt {mean_in['sample']:.0f} / completion {mean_out['sample']:.0f} tokens per sampled call, "
          f"{mean_in['greedy']:.0f} / {mean_out['greedy']:.0f} greedy): ~${cal:.2f}; x{SAFETY} safety = ${cal * SAFETY:.2f}")
    rec_cap = min(cap, 5 * int(np.ceil(cal * 1.5 / 5)))
    print(f"[dry-run] chosen N = {n} (target {n_target}; up to N = {n_max} fits the ${cap:.0f} cap with the {SAFETY}x margin); "
          f"expected spend ~${cal:.0f}; recommended --cap {rec_cap:.0f} (1.5x expected; hard ceiling ${cap:.0f})")
    return {"n": n, "n_max": n_max, "calls": len(reqs), "battery_est_usd": est["est_usd"], "calibrated_usd": cal, "recommended_cap": rec_cap}


def run(n_target, cap, top_p, workers):
    mean_in, mean_out = release_usage()
    n, n_max = choose_n(cap, n_target, mean_in, mean_out)
    reqs = build_requests(n, top_p)
    rd = run_dir_for(top_p)
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "run_config.json").write_text(json.dumps({
        "card_id": CARD_ID, "model": MODEL, "n_greedy_repeats": N_GREEDY, "n_sample_runs": n, "n_max_affordable": n_max,
        "temperature_greedy": TEMPERATURE_GREEDY, "temperature_sample": TEMPERATURE_SAMPLE, "top_p": top_p, "n_per_call": 1,
        "max_tokens": None, "stop": None, "cap_usd": cap, "calls": len(reqs), "calibrated_cost_usd": calibrated_cost(n, mean_in, mean_out),
        "prompt_source": f"{OI_SRC}:140", "instruction": INSTRUCTION, "built_utc": now()}, indent=2), encoding="utf-8")
    run_battery(reqs, rd, cap, workers=workers, label=f"{CARD_ID} top_p={top_p}")


# -------------------------------------------------------------------------------------------------------- --analyze
def analyze(top_p):
    rd = run_dir_for(top_p)
    res = load_results(rd)
    if not res:
        print(f"no archived calls in {rd}; run --run first")
        return None
    problems = load_problems()
    tids = list(problems)
    budget = json.loads((rd / "budget.json").read_text(encoding="utf-8")) if (rd / "budget.json").exists() else {}
    cfg = json.loads((rd / "run_config.json").read_text(encoding="utf-8")) if (rd / "run_config.json").exists() else {}
    env = check(verbose=False)                     # cached executions -> cheap; fills the environment reference block

    recs = {}
    for (rid, sidx), rec in res.items():
        arm, tid = rid.split("|", 1)
        ch = (rec["response"] or {}).get("choices") or [{}]
        reply = (ch[0].get("message") or {}).get("content") or ""
        recs[(arm, tid, sidx)] = {"reply": reply, "completion": extract_code(reply), "lenient": extract_code_lenient(reply),
                                  "finish": ch[0].get("finish_reason"), "model": rec.get("model_served"), "fp": rec.get("system_fingerprint"),
                                  "latency": rec.get("latency_ms"), "usage": (rec["response"] or {}).get("usage") or {}}
    greedy_reps = sorted({k[2] for k in recs if k[0] == "greedy" and all((("greedy", t, k[2]) in recs) for t in tids)})
    sample_runs = sorted({k[2] for k in recs if k[0] == "sample" and all((("sample", t, k[2]) in recs) for t in tids)})
    partial = {"greedy": len({k[2] for k in recs if k[0] == "greedy"}) - len(greedy_reps),
               "sample": len({k[2] for k in recs if k[0] == "sample"}) - len(sample_runs)}
    if not greedy_reps or not sample_runs:
        print(f"incomplete run: complete greedy repeats {greedy_reps}, complete sampled runs {len(sample_runs)}; cannot judge yet")
    items = []
    for (arm, tid, sidx), r in recs.items():
        items.append({"key": f"{arm}|{tid}|{sidx}", "task_id": tid, "completion": r["completion"]})
        if r["lenient"] != r["completion"]:
            items.append({"key": f"{arm}|{tid}|{sidx}|lenient", "task_id": tid, "completion": r["lenient"]})
    results = execute_many(items, problems, rd / "executions.jsonl", "archived completions")

    def flag(arm, tid, sidx, lenient=False):
        k = f"{arm}|{tid}|{sidx}" + ("|lenient" if lenient and f"{arm}|{tid}|{sidx}|lenient" in results else "")
        return int(results[k] == "passed")

    G = np.array([[flag("greedy", t, rep) for rep in greedy_reps] for t in tids], int).reshape(len(tids), -1)
    S = np.array([[flag("sample", t, k) for k in sample_runs] for t in tids], int).reshape(len(tids), -1)
    G_len = np.array([[flag("greedy", t, rep, True) for rep in greedy_reps] for t in tids], int).reshape(len(tids), -1)
    S_len = np.array([[flag("sample", t, k, True) for k in sample_runs] for t in tids], int).reshape(len(tids), -1)
    greedy_scores = [float(x) for x in G.mean(axis=0) * 100] if G.size else []
    greedy_median = float(np.median(greedy_scores)) if greedy_scores else float("nan")
    sample_stats = run_stats(S.mean(axis=0) * 100) if S.size else None
    tt = t_test(sample_stats["scores"], greedy_median) if sample_stats else {"t": None, "p": None, "df": None}
    tt_flags = t_test(S.flatten() * 100.0, greedy_median) if S.size else None
    boot = bootstrap(S, G) if S.size and G.size else None
    len_greedy = [float(x) for x in G_len.mean(axis=0) * 100] if G_len.size else []
    len_stats = run_stats(S_len.mean(axis=0) * 100) if S_len.size else None
    complete = bool(sample_stats and greedy_scores)
    label, gap = judge(greedy_median, sample_stats["mean"], tt["p"]) if complete else ("미판정 (incomplete)", float("nan"))
    if complete and len(sample_runs) < cfg.get("n_sample_runs", len(sample_runs)):
        label += f" [subset: {len(sample_runs)}/{cfg.get('n_sample_runs')} sampled runs]"

    # paired comparison with the released runs (same problems, same prompt, 2024-06-14 vs now)
    rel_S = np.array(env["per_problem_flags"]["sample_rescored"], int)
    rel_G = np.array(env["per_problem_flags"]["greedy_rescored"], int)
    rel_tids = env["per_problem_flags"]["task_ids"]
    order = [rel_tids.index(t) for t in tids]
    rel_rate, our_rate = rel_S[order].mean(axis=1), (S.mean(axis=1) if S.size else np.full(len(tids), np.nan))
    paired = {"released_runs": int(rel_S.shape[1]), "our_runs": int(S.shape[1]) if S.size else 0,
              "per_problem_sample_rate_pearson_r": float(np.corrcoef(rel_rate, our_rate)[0, 1]) if S.size else None,
              "per_problem_sample_rate_mean_abs_diff": float(np.abs(rel_rate - our_rate).mean()) if S.size else None,
              "problems_majority_flipped": int(((rel_rate >= 0.5) != (our_rate >= 0.5)).sum()) if S.size else None,
              "greedy_flag_agreement_with_released_greedy": float((rel_G[order][:, None] == G).mean()) if G.size else None,
              "released_rescored_greedy": env["rescored"]["greedy"], "released_rescored_sample_mean": env["rescored"]["sample"]["mean"],
              "released_rescored_gap": env["rescored"]["gap"]}

    served = sorted({r["model"] for r in recs.values() if r["model"]})
    fps = {r["fp"] for r in recs.values() if r["fp"]}
    lat = sorted(r["latency"] for r in recs.values() if r["latency"] is not None)
    finish = Counter(r["finish"] for r in recs.values())
    nofence = {"greedy": int(sum("```python" not in r["reply"] for k, r in recs.items() if k[0] == "greedy")),
               "sample": int(sum("```python" not in r["reply"] for k, r in recs.items() if k[0] == "sample"))}
    reex = {"greedy_pass1_per_repeat": greedy_scores, "greedy_median": greedy_median, "n_greedy_repeats": len(greedy_reps),
            "sample": sample_stats, "n_sample_runs": len(sample_runs), "gap": gap, "t_test_runs_vs_greedy_median": tt,
            "t_test_all_samples_vs_greedy_median": tt_flags, "bootstrap95": boot,
            "per_problem": per_problem_stats(S, G) if S.size and G.size else None,
            "lenient_postprocessing": {"greedy_per_repeat": len_greedy, "sample": len_stats,
                                       "gap": (float(np.median(len_greedy)) - len_stats["mean"]) if len_greedy and len_stats else None},
            "replies_without_python_fence": nofence, "incomplete_runs_dropped": partial, "top_p": top_p}
    original = {"paper": ORIGINAL,
                "released_runs_rescored_in_our_harness": {"greedy": env["rescored"]["greedy"], "sample_mean": env["rescored"]["sample"]["mean"],
                                                          "std_pop": env["rescored"]["sample"]["std_pop"], "delta_best_worst": env["rescored"]["sample"]["delta_best_worst"],
                                                          "gap": env["rescored"]["gap"], "t_test_p": env["rescored"]["t_test_runs_vs_greedy"]["p"],
                                                          "bootstrap95": env["rescored"]["bootstrap"], "n_runs": env["release"]["n_sampled_runs"]}}
    frictions = [
        "Table 1/2 state N=128 sampled runs for HumanEval, but the released archive holds 32 sampled runs for gpt-4-turbo-2024-04-09 and their metrics reproduce Table 2 exactly (mean 84.05, std 2.645, best-worst 10.98): the reported row rests on N=32",
        "the paper says top-p 1.0; the Open-Instruct OpenAI branch that produced the released runs hard-codes top_p=0.95 (run_eval.py:147); re-run uses 1.0 as decided, 0.95 left as an unrun sensitivity",
        "the OpenAI branch passes no max_tokens and no stop sequences (the codex stop list feeds only the vLLM/HF branches); the card's stop/max_tokens fields describe the local-model path",
        "the released completions are the ```python block(s) of each reply (empty when a reply has no fence, then scored failed), a post-processing step that is neither in Open-Instruct nor in the released repository; the rule was inferred and reproduces all 5,412 released completions",
        f"generation via the OpenAI API, so 'greedy' (temperature 0) is itself non-deterministic; {N_GREEDY} repeats were run and the median used",
        "Open-Instruct's evaluator forks a worker and uses signal.alarm (POSIX only); scoring here runs each program in a fresh isolated interpreter with a wall-clock timeout",
        "the one-sample t-test p-value of Table 8 (1.1e-48) is not reproduced by a t-test over the 32 run scores (about 1e-12) nor by one over all 5,248 sample outcomes; the construction is not documented",
    ]
    if budget.get("stopped_at_cap"):
        frictions.append(f"the run stopped at the ${budget.get('cap_usd')} cap; incomplete runs dropped: {partial}")
    if budget.get("errors"):
        frictions.append(f"{budget['errors']} calls failed at the HTTP level and are not in the archive")
    meta = {
        "card_id": CARD_ID, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
        "target_paper": {"title": "The Good, The Bad, and The Greedy: Evaluation of LLMs Should Not Ignore Non-Determinism",
                         "doi": "10.18653/v1/2025.naacl-long.211", "repo": "https://github.com/Yifan-Song793/GoodBadGreedy",
                         "repo_commit": "eb9a5860ce7a94e800fed6aa04faf6e27bf6b04d",
                         "repo_license": "none in the code repo; released samples (HF goodbadgreedy/GoodBadGreedy) Apache-2.0",
                         "original_run_dates": (f"{env['release']['created_utc_range'][0][:10]} (created timestamps in the released openai_query_results.jsonl)"
                                                if env["release"]["created_utc_range"] else "2024-06 (released response timestamps)"),
                         "original_values": {"greedy": ORIGINAL["greedy"], "sample_mean": ORIGINAL["sample_mean"], "std": ORIGINAL["std"],
                                             "delta_best_worst": ORIGINAL["delta_best_worst"], "gap": ORIGINAL["gap"], "N_stated": 128, "N_released": 32,
                                             "t_test_p": ORIGINAL["t_test_p"]},
                         "original_source": ORIGINAL["source"]},
        "generation": {"model_requested": MODEL, "model_served_field": served, "n_fingerprints": len(fps),
                       "system_fingerprint_example": next(iter(fps), None),
                       "endpoint": "POST https://api.openai.com/v1/chat/completions (raw HTTPS, harness/openai_client.py)",
                       "parameters": f"single user message; temperature {TEMPERATURE_GREEDY} (greedy, {len(greedy_reps)} repeats) / {TEMPERATURE_SAMPLE} (sampling, "
                                     f"{len(sample_runs)} runs); top_p {top_p}; n 1; no max_tokens; no stop sequences - the Open-Instruct OpenAI branch "
                                     f"(run_eval.py:138-150) except top_p (code 0.95, paper 1.0)",
                       "prompt_template_source": f"{OI_SRC}:140 ('Complete the following python function. Please only output the code for the completed function.' + HumanEval prompt), verified verbatim against the released calls",
                       "postprocessing": "```python block(s) of the reply concatenated and stripped (authors' step, inferred; empty when no fence); lenient variant reported",
                       "samples_per_task": {"greedy": len(greedy_reps), "sample": len(sample_runs)}, "n_tasks": len(tids),
                       "python": sys.version.split()[0], "pricing_assumed_usd_per_1m": {"input": 10.0, "output": 30.0},
                       "budget_cap_usd": budget.get("cap_usd", cfg.get("cap_usd", CAP)), "run_config": cfg,
                       "battery": f"{len(res)} archived calls in {rd.name}/calls.jsonl"},
        "evaluation": {"python": sys.version.split()[0], "timeout_s": EXEC_TIMEOUT_S, "workers": EXEC_WORKERS,
                       "mode": "fresh isolated interpreter per sample (subprocess.run, cwd = temp dir); check program per Open-Instruct execution.py:38-42",
                       "k": [1], "problem_file": "openai/human-eval data/HumanEval.jsonl.gz (164 problems)",
                       "environment_reference_check": {"canonical_solutions_pass": env["canonical_solutions"],
                                                       "released_flags_reproduced": {"agree": env["flag_agreement"]["agree"], "disagree": env["flag_agreement"]["disagree"]},
                                                       "released_greedy_rescored": env["rescored"]["greedy"], "released_sample_mean_rescored": env["rescored"]["sample"]["mean"]}},
        "results": {"reexecution": reex, "original": original, "paired_with_released": paired,
                    "delta_gap_points_vs_paper": (gap - ORIGINAL["gap"]) if complete else None,
                    "delta_greedy_points_vs_paper": (greedy_median - ORIGINAL["greedy"]) if complete else None,
                    "delta_sample_mean_points_vs_paper": (sample_stats["mean"] - ORIGINAL["sample_mean"]) if complete else None,
                    "cost_usd": round(budget.get("cost_usd", sum(r["usage"].get("prompt_tokens", 0) * 10 / 1e6 + r["usage"].get("completion_tokens", 0) * 30 / 1e6 for r in recs.values())), 3),
                    "calls": budget.get("calls", len(res)), "errors": budget.get("errors", 0),
                    "call_log_stats": {"http_200": len(res), "distinct_system_fingerprints": len(fps), "finish_reasons": dict(finish),
                                       "latency_ms_median": lat[len(lat) // 2] if lat else None, "latency_ms_p95": lat[int(0.95 * (len(lat) - 1))] if lat else None,
                                       "tokens_in": budget.get("tokens_in"), "tokens_out": budget.get("tokens_out")},
                    "judgment": label,
                    "judged_by": "automatic rule per ANALYSIS_PLAN Sec. 1 as instantiated in the card: survived if median greedy (3 repeats) > sampling mean, "
                                 "one-sample t-test of run scores vs greedy p < 0.05 and gap >= 2 points; partial if greedy > mean but n.s. or gap < 2; "
                                 "dead if sampling mean >= greedy; human double-coding pending",
                    "subsidiary_claim_std_ordering": "not judged (HumanEval only; MMLU-Redux/GSM8K arms not run)",
                    "note": (f"greedy median {greedy_median:.2f} (repeats {[round(x, 2) for x in greedy_scores]}) vs sampling mean {sample_stats['mean']:.2f} "
                             f"(std {sample_stats['std_pop']:.2f}, best-worst {sample_stats['delta_best_worst']:.2f}, {len(sample_runs)} runs); gap {gap:.2f} "
                             f"[95% CI {boot['gap_ci95'][0]:.2f}, {boot['gap_ci95'][1]:.2f}] vs paper 5.5 (released runs re-scored: {env['rescored']['gap']:.2f}); "
                             f"t-test p {tt['p']:.1e}. Lenient post-processing gap {reex['lenient_postprocessing']['gap']:.2f}." if complete else "incomplete run")},
        "reproducibility_frictions_observed": frictions,
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    (rd / "result.json").write_text(json.dumps({"reexecution": reex, "paired_with_released": paired, "judgment": label}, indent=2, default=_json_default), encoding="utf-8")
    meta_path = RUNS / ("run_meta.json" if rd == RUN else f"run_meta_{rd.name}.json")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    print(f"\n[{CARD_ID} --analyze] {len(res)} calls; served {served}; {len(fps)} fingerprints; cost ${meta['results']['cost_usd']}")
    if complete:
        print(f"  greedy pass@1 per repeat {[round(x, 2) for x in greedy_scores]} -> median {greedy_median:.2f} (paper 89.6; released re-scored {env['rescored']['greedy']:.2f})")
        print(f"  sampling mean {sample_stats['mean']:.2f} std {sample_stats['std_pop']:.3f} best {sample_stats['max']:.2f} worst {sample_stats['min']:.2f} "
              f"delta {sample_stats['delta_best_worst']:.2f} over {len(sample_runs)} runs (paper 84.1 / 2.65 / 11.0)")
        print(f"  gap {gap:.2f} [CI {boot['gap_ci95'][0]:.2f}, {boot['gap_ci95'][1]:.2f}] (paper 5.5); t-test p {tt['p']:.1e}; lenient gap {reex['lenient_postprocessing']['gap']:.2f}")
        print(f"  paired with released: per-problem rate r={paired['per_problem_sample_rate_pearson_r']:.3f}, majority flipped {paired['problems_majority_flipped']}/164")
    print(f"  judgment: {label}\n  -> {meta_path}")
    return meta


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="re-score the released gpt-4-turbo samples (no API calls)")
    ap.add_argument("--dry-run", action="store_true", help="build requests and print the cost estimate (no API calls)")
    ap.add_argument("--run", action="store_true", help="execute the battery (paid API calls, capped)")
    ap.add_argument("--analyze", action="store_true", help="score the archived completions and write run_meta.json")
    ap.add_argument("--n-samples", type=int, default=N_SAMPLE_TARGET, help="target sampled runs per problem (default 32)")
    ap.add_argument("--cap", type=float, default=CAP, help="USD cap for --run (default 85)")
    ap.add_argument("--top-p", type=float, default=TOP_P, help="1.0 primary (paper); 0.95 = Open-Instruct code path, separate run dir")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if not any((a.check, a.dry_run, a.run, a.analyze)):
        ap.print_help()
        return
    if a.check:
        check()
    if a.dry_run:
        dry_run(a.n_samples, a.cap, a.top_p)
    if a.run:
        run(a.n_samples, a.cap, a.top_p, a.workers)
    if a.analyze:
        analyze(a.top_p)


if __name__ == "__main__":
    main()
