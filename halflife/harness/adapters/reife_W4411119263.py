"""Card W4411119263 - ReIFE: Re-evaluating Instruction-Following Evaluation (Liu, Shi, Fabbri, Zhao, Wang, Wu, Joty,
Cohan; NAACL 2025). Repository-based upgrade of the Tier B prompt-level replay runs/tierb/W4411119263.

CLAIM (card; Table 2, row gpt-4o-24-05-13, base protocol): as a pairwise LLM-evaluator gpt-4o-2024-05-13 agrees with
human preference at 95.5 (LLMBar-Natural) / 80.7 (LLMBar-Adversarial) / 79.5 (MTBench) / 80.3 (InstruSum), Avg. 84.0.
The Avg. column is the UNWEIGHTED (macro) mean over the four datasets: (95.5+80.7+79.5+80.3)/4 = 84.0 exactly.

THE AUTHORS' CODE IS IMPORTED, NOT COPIED (external/repos/W4411119263/yale-nlp__ReIFE @ cfcb8fc2):
  items    data/{llmbar_natural,llmbar_adversarial,mtbench,instrusum}.json = 100/319/200/411 = 1,030 pairs
           (instruction / output_1 / output_2 / winner) via ReIFE.utils.read_json + get_dataset_path. --check proves
           offline that they are identical to the Hugging Face mirror yale-nlp/ReIFE subset 'src' by rebuilding the
           archived Tier B requests (which were built from the Hub) from them; nothing is downloaded.
  prompts  prompts/pairwise_vanilla.txt (normal) and pairwise_vanilla_swap.txt (swapped display order), rendered by
           ReIFE.methods.base_pairwise.base_pairwise_eval through ReIFE.evaluator.PairwiseEvaluator - the path run.py
           takes - with a capture-only stand-in for the API client, so every request carries the authors' own
           str.format_map + prompt_to_chatml output (one system + one user message).
  params   configs/gpt/pairwise_base{,_swap}.yaml eval_kwargs, READ FROM THE REPOSITORY at runtime: max_tokens 64,
           n 1, temperature 0.0, top_p 1.0, logprobs 5 -> the body ReIFE/models/gpt.py sends has logprobs=true,
           top_logprobs=5 (decision 2026-09-19; supersedes the Tier B config's assumed max_tokens 16).
  parser   base_pairwise_parse, sys1_marker a / sys2_marker b / pattern 'Output \\((\\S+)\\)'. CASE SENSITIVE, takes the
           FIRST match, and resolves an unparsable reply with random.randint(1, 2); PairwiseEvaluator calls
           random.seed(42) once per (dataset, prompt file) pass, which --analyze mirrors exactly.
  metric   meta_eval.pairwise_meta_eval(human, model, model_swap): accuracy against the human winner computed per
           order and averaged, plus Krippendorff alpha self-agreement across the orders (local fallback if the
           repository's undeclared krippendorff/tabulate dependencies are missing).
  vllm is stubbed at import time (ReIFE/base_llm.py imports it unconditionally; the GPT arm never touches it).

DECISIONS 2026-09-19 (card key decisions_2026_09_19): all four datasets, macro mean = the judged quantity; the
repository's own eval_kwargs; 1 seed (the paper ran greedy decoding once, Sec. 3); both presentation orders as the
repository does (two passes, two prompt files); per-paper cap USD 20.

JUDGMENT (ANALYSIS_PLAN Sec. 1 as the card instantiates it): survived = the macro mean lies inside a band of
84.0 +/- our own bootstrap 95% half-width over the 1,030 pairs (the original has no item-level release - card blocker
1 - so its sampling error is proxied by ours) AND the ordering Nat > {Adv, MT, Ins} within a 5-point spread holds AND
the macro CI lower bound stays >= 10 points above the 50% random-oracle floor. Partial = outside the band but still
above gpt-4o-mini's 78.4 with Nat > Adv preserved. Dead = LLMBar-Adversarial no longer separates from chance (CI lower
bound <= 50), or a dataset is unscorable (parse-failure rate > 5%, or missing calls).

  python adapters/reife_W4411119263.py --check      # offline: data, prompts, parser, cost calibration; no API calls
  python adapters/reife_W4411119263.py --dry-run    # request list + token/cost estimate; no API calls
  python adapters/reife_W4411119263.py --run        # spends money; cap $20 -> runs/W4411119263/baseline_alive/
  python adapters/reife_W4411119263.py --analyze    # accuracies, bootstrap CI, judgment, run_meta.json
"""
import argparse, contextlib, hashlib, importlib.util, io, json, random, subprocess, sys, tempfile, types
from collections import Counter
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, pricing_for, run_battery  # noqa: E402

HALF = HERE.parent.parent
CARD_ID, MODEL = "W4411119263", "gpt-4o-2024-05-13"
REPO = HALF / "external" / "repos" / CARD_ID / "yale-nlp__ReIFE"
REPO_COMMIT = "cfcb8fc2cd078b91e1fe26d81ddbd03672b60175"
TIERB_CFG = HALF / "harness" / "tierb" / "configs" / f"{CARD_ID}.json"
TIERB_HOOK = HALF / "harness" / "tierb" / "hooks" / f"{CARD_ID}.py"
TIERB_RUN = HALF / "runs" / "tierb" / CARD_ID
RUNS = HALF / "runs" / CARD_ID
RUN = RUNS / "baseline_alive"
CHECK_JSON = RUNS / "environment_check.json"

DATASETS = ["llmbar_natural", "llmbar_adversarial", "mtbench", "instrusum"]   # paper Table 2 column order
ORDERS = {"normal": "pairwise_vanilla", "swap": "pairwise_vanilla_swap"}      # key -> repository prompt_method
CONFIGS = {"normal": "configs/gpt/pairwise_base.yaml", "swap": "configs/gpt/pairwise_base_swap.yaml"}
CAP, SEEDS = 20.0, 1             # decision 2026-09-19: the paper ran greedy decoding once
N_BOOT, BOOT_SEED = 1000, 0
FAIL_UNSCORABLE = 0.05           # parse-failure rate above which a dataset counts as unscorable
ORDER_SPREAD = 5.0               # max spread among {Adv, MT, Ins} for the paper's ordering to count as preserved
OUT_TOKENS = 4                   # every reply in the archived Tier B run is exactly 4 completion tokens
ORIGINAL = {"llmbar_natural": 95.5, "llmbar_adversarial": 80.7, "mtbench": 79.5, "instrusum": 80.3, "avg": 84.0,
            "gpt_4o_mini_avg": 78.4, "random_floor": 50.0,
            "source": "Table 2 (Sec. 4.1, Proprietary LLMs block), row gpt-4o-24-05-13; Avg. = macro mean over the four datasets"}
SYNTHETIC = ["Output (a)", "Output (b)", "Output (a) is better.", "The better output is Output (b).", "output (a)",
             "Output (A)", "Output (c)", "Both Output (a) and Output (b) are good.", "Neither output is acceptable.",
             "I'm sorry, I can't help with that.", "", "(a)", "Output (a)\n\nBecause it follows the instruction."]
_NS, _RENDER, _DATA = None, {}, {}


def now():
    return datetime.now(timezone.utc).isoformat()


def _default(o):
    if isinstance(o, (np.integer, np.floating)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


# -------------------------------------------------------------------------------------- repository code (imported)
def repo():
    """Import ReIFE from the checked-out repository. vllm is stubbed: ReIFE/base_llm.py imports it at module level
    for the open-weight arms, but the GPT arm never calls into it."""
    global _NS
    if _NS is not None:
        return _NS
    if not (REPO / "ReIFE").is_dir():
        sys.exit(f"repository not found at {REPO} (clone yale-nlp/ReIFE at {REPO_COMMIT}, code paths only)")
    if "vllm" not in sys.modules:
        stub = types.ModuleType("vllm")
        stub.__version__, stub.LLM, stub.SamplingParams = "0.0.0+stub-not-installed", object, object
        sys.modules["vllm"] = stub
    sys.path.insert(0, str(REPO))
    import yaml
    from ReIFE.base_llm import BaseLLMAPI
    from ReIFE.evaluator import PairwiseEvaluator
    from ReIFE.methods import get_method, get_parser
    from ReIFE.utils import get_dataset_path, read_json
    try:                                       # meta_eval.py needs krippendorff + tabulate, neither declared anywhere
        import meta_eval as me
        me_err = None
    except Exception as e:
        me, me_err = None, f"{type(e).__name__}: {e}"
    _NS = SimpleNamespace(yaml=yaml, BaseLLMAPI=BaseLLMAPI, PairwiseEvaluator=PairwiseEvaluator, get_method=get_method,
                          get_parser=get_parser, get_dataset_path=get_dataset_path, read_json=read_json,
                          meta_eval=me, meta_eval_error=me_err)
    return _NS


def config(order="normal"):
    """The repository's own config for the base protocol under the GPT arm."""
    return repo().yaml.safe_load((REPO / CONFIGS[order]).read_text(encoding="utf-8"))


def data(dataset):
    if dataset not in _DATA:
        R = repo()
        _DATA[dataset] = R.read_json(str(REPO / R.get_dataset_path(dataset)))
    return _DATA[dataset]


def parse_fn():
    c = config()
    return partial(repo().get_parser(c["parse_method"]), sys1_marker=c["sys1_marker"], sys2_marker=c["sys2_marker"],
                   pattern=c["pattern"], verbose=False)


def render(dataset, order):
    """Chat messages for one dataset and one presentation order, produced by the repository's own prompt code
    (base_pairwise_eval via PairwiseEvaluator) with a capture-only stand-in for the API client."""
    if (dataset, order) in _RENDER:
        return _RENDER[(dataset, order)]
    R, c = repo(), config(order)

    class Capture(R.BaseLLMAPI):
        def __init__(self):
            super().__init__(model_pt="capture-only", key_path=None, account_path=None, parallel_size=1,
                             max_retries=1, initial_wait_time=0, end_wait_time=0)
            self.seen = []

        def _get_response(self, prompt, n=1, max_tokens=1024, temperature=1.0, top_p=1.0, logprobs=None):
            self.seen.append(prompt)                       # no network: a canned reply stands in for the API
            return [{"text": "Output (a)", "logprobs": None, "tokens": None}]

    m = Capture()
    with tempfile.TemporaryDirectory(prefix="reife_") as td, contextlib.redirect_stdout(io.StringIO()):
        R.PairwiseEvaluator(m).pairwise_eval(
            eval_fn=partial(R.get_method(c["eval_method"]), instruction_marker=c["instruction_marker"],
                            output_marker=c["output_marker"]),
            input_dir=str(REPO / R.get_dataset_path(dataset)), output_dir=str(Path(td) / "out.jsonl"),
            prompt_dir=str(REPO / "prompts" / f"{c['prompt_method']}.txt"), batch_size=512, output_text_dir=None,
            parse_fn=parse_fn(), verbose=False, **c["eval_kwargs"])
    assert len(m.seen) == len(data(dataset)), (dataset, order, len(m.seen))
    _RENDER[(dataset, order)] = [[{"role": x["role"], "content": x["content"]} for x in p] for p in m.seen]
    return _RENDER[(dataset, order)]


def tierb_messages(row, order):
    """The Tier B config's prompt for the same pair (harness/tierb/hooks/W4411119263.py render). The hook swaps the
    two output CONTENTS and remaps the gold letter; the repository instead swaps the two display POSITIONS."""
    p = json.loads(TIERB_CFG.read_text(encoding="utf-8"))["prompt"]
    o1, o2 = (row["output_1"], row["output_2"]) if order == "normal" else (row["output_2"], row["output_1"])
    u = p["user_template"].replace("{INSTRUCTION}", str(row["instruction"])).replace("{OUTPUT_1}", str(o1)).replace("{OUTPUT_2}", str(o2))
    return [{"role": "system", "content": p["system"]}, {"role": "user", "content": u}]


# -------------------------------------------------------------------------------------------------- tokens / cost
def token_counter():
    """(fn, name). o200k_base with 4 tokens per message + 3 priming reproduces the API's prompt_tokens exactly on
    every archived Tier B call (--check re-verifies this)."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")
        return (lambda ms: sum(len(enc.encode(m["content"])) + 4 for m in ms) + 3), "tiktoken/o200k_base +4/msg +3"
    except Exception:
        return (lambda ms: int(sum(len(m["content"]) for m in ms) / 4 + 4 * len(ms) + 3)), "chars/4 fallback"


def estimate(seeds=SEEDS):
    """Per-dataset input tokens and USD for `seeds` passes over both presentation orders."""
    count, how = token_counter()
    price, per, tin, calls = pricing_for(MODEL), {}, 0, 0
    for ds in DATASETS:
        t = sum(count(p) for o in ORDERS for p in render(ds, o))
        n = len(data(ds)) * len(ORDERS)
        per[ds] = {"calls_per_seed": n, "tokens_in_per_seed": t, "mean_tokens_in": round(t / n, 1),
                   "usd_per_seed": round(t / 1e6 * price["input"] + n * OUT_TOKENS / 1e6 * price["output"], 4)}
        tin, calls = tin + t, calls + n
    usd = tin * seeds / 1e6 * price["input"] + calls * seeds * OUT_TOKENS / 1e6 * price["output"]
    worst = tin * seeds / 1e6 * price["input"] + calls * seeds * config()["eval_kwargs"]["max_tokens"] / 1e6 * price["output"]
    return {"tokenizer": how, "seeds": seeds, "calls": calls * seeds, "tokens_in": tin * seeds,
            "tokens_out_expected": calls * seeds * OUT_TOKENS, "usd_expected": round(usd, 2),
            "usd_if_every_reply_hit_max_tokens": round(worst, 2), "pricing_usd_per_1m": price, "per_dataset": per}


# ---------------------------------------------------------------------------------------------------------- check
def check(verbose=True):
    R, c, csw = repo(), config("normal"), config("swap")
    count, how = token_counter()
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    ds_info, prompts = {}, {}
    for ds in DATASETS:
        rows = data(ds)
        ds_info[ds] = {"n": len(rows), "file": f"data/{ds}.json", "fields": sorted(rows[0]),
                       "sha256": hashlib.sha256((REPO / R.get_dataset_path(ds)).read_bytes()).hexdigest(),
                       "winner_counts": dict(Counter(int(r["winner"]) for r in rows)),
                       "mean_tokens_in": {o: round(sum(count(p) for p in render(ds, o)) / len(rows), 1) for o in ORDERS}}
        prompts[ds] = {}
        for o in ORDERS:
            msgs, tb = render(ds, o)[0], tierb_messages(rows[0], o)
            prompts[ds][o] = {"prompt_file": f"prompts/{ORDERS[o]}.txt", "roles": [m["role"] for m in msgs],
                              "sha256": hashlib.sha256(json.dumps(msgs, sort_keys=True).encode("utf-8")).hexdigest(),
                              "tokens_in": count(msgs), "chars": sum(len(m["content"]) for m in msgs),
                              "system_identical_to_tierb": msgs[0]["content"] == tb[0]["content"],
                              "user_identical_to_tierb": msgs[1]["content"] == tb[1]["content"],
                              "user_identical_to_tierb_ignoring_blank_lines_and_bold":
                                  msgs[1]["content"].replace("\n\n", "\n").replace("**", "") == tb[1]["content"].replace("\n\n", "\n")}

    # The Tier B run was built from the Hugging Face mirror; rebuilding its requests from the repository's own data
    # files proves the two item copies agree, without downloading anything.
    hf_eq, tb_req = {}, TIERB_RUN / "requests.jsonl"
    if tb_req.exists():
        seen, match, mism = set(), 0, []
        for line in tb_req.open(encoding="utf-8"):
            r = json.loads(line)
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            ds, i, o = r["id"].rsplit("_", 2)
            built = tierb_messages(data(ds)[int(i)], "normal" if o == "ab" else "swap")
            if [m["content"] for m in built] == [m["content"] for m in r["body"]["messages"]]:
                match += 1
            elif len(mism) < 5:
                mism.append(r["id"])
        hf_eq = {"source": tb_req.relative_to(HALF).as_posix(), "rows_compared": len(seen), "identical": match, "mismatch_examples": mism,
                 "conclusion": "the Hugging Face mirror yale-nlp/ReIFE subset 'src' and the repository's data/*.json carry "
                               "identical instruction/output_1/output_2 for all 1,030 pairs" if match == len(seen)
                               else "MISMATCH - the two item copies differ"}

    pf = parse_fn()                                        # the repository's parser on synthetic replies, seeded as the evaluator seeds it
    random.seed(42)
    parsed = [dict(reply=t, **pf({"response": [{"text": t}]})[0]) for t in SYNTHETIC]
    random.seed(42)
    repeat = [pf({"response": [{"text": t}]})[0]["winner"] for t in SYNTHETIC]
    spec = importlib.util.spec_from_file_location("tierb_hook", TIERB_HOOK)
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    for p in parsed:
        p["tierb_parse"] = hook.parse(p["reply"], {})
        p["agree_with_tierb"] = p["tierb_parse"] == {1: "a", 2: "b"}[p["winner"]] and not p["fail"]

    tok, tb_calls = {"note": "tokenizer calibration against the archived Tier B calls (same model, same API)"}, TIERB_RUN / "calls.jsonl"
    if tb_calls.exists():
        d = [count(json.loads(l)["request"]["messages"]) - json.loads(l)["response"]["usage"]["prompt_tokens"]
             for i, l in enumerate(tb_calls.open(encoding="utf-8")) if i % 500 == 0 and json.loads(l).get("status") == 200]
        tok.update({"sampled_calls": len(d), "estimate_minus_api_prompt_tokens": dict(Counter(d))})
    tb_res = json.loads((TIERB_RUN / "result.json").read_text(encoding="utf-8")) if (TIERB_RUN / "result.json").exists() else None
    est = estimate(SEEDS)
    summary = {
        "card_id": CARD_ID, "checked_utc": now(), "model": MODEL, "python": sys.version.split()[0], "api_calls_made": 0,
        "repo": {"path": REPO.relative_to(HALF).as_posix(), "commit": commit, "commit_expected": REPO_COMMIT,
                 "commit_matches": commit == REPO_COMMIT, "vllm": "stubbed (imported unconditionally by ReIFE/base_llm.py, unused here)",
                 "license": "none (all rights reserved): the code is read and run, not redistributed",
                 "imported": ["ReIFE.evaluator.PairwiseEvaluator", "ReIFE.methods.base_pairwise (method + parser via the registry)",
                              "ReIFE.methods.utils.prompt_to_chatml (through base_pairwise_eval)",
                              "ReIFE.utils.read_json / get_dataset_path", "meta_eval.pairwise_meta_eval"],
                 "meta_eval_importable": R.meta_eval is not None, "meta_eval_error": R.meta_eval_error},
        "config": {"files": CONFIGS, "eval_kwargs": c["eval_kwargs"], "swap_eval_kwargs_identical": c["eval_kwargs"] == csw["eval_kwargs"],
                   "eval_method": c["eval_method"], "parse_method": c["parse_method"], "pattern": c["pattern"],
                   "markers": [c["sys1_marker"], c["sys2_marker"]], "prompt_methods": {o: config(o)["prompt_method"] for o in ORDERS},
                   "api_body": "ReIFE/models/gpt.py: logprobs=5 -> logprobs=true + top_logprobs=5; n, top_p, temperature, max_tokens verbatim"},
        "datasets": ds_info, "total_pairs": sum(v["n"] for v in ds_info.values()),
        "data_source": {"used": "repository data/*.json", "bytes_downloaded": 0, "equality_check_vs_hf": hf_eq,
                        "hf_mirror": "yale-nlp/ReIFE subset 'src' (apache-2.0) - fallback, not needed"},
        "prompt_check": prompts, "prompt_example_llmbar_natural_pair0": {o: render("llmbar_natural", o)[0] for o in ORDERS},
        "prompt_vs_tierb": {"verdict": "NOT verbatim: the Tier B config's user_template differs from prompts/pairwise_vanilla.txt",
                            "differences": [
                                "all 6 blank lines of the prompt file are collapsed to single newlines in the Tier B config (20 newlines vs 14)",
                                "the markdown emphasis '**equally likely**' is written 'equally likely' in the Tier B config",
                                "swapped order: the repository swaps the two DISPLAY POSITIONS and keeps Output (a) bound to output_1 "
                                "(prompts/pairwise_vanilla_swap.txt), while the Tier B hook keeps the a-then-b display order and swaps "
                                "the output CONTENTS, remapping the gold letter - the same pair, a different manipulation"],
                            "card_statement_corrected": "card tierb_relationship.protocol_differences says 'Prompt text is identical (the "
                                                        "Tier B config transcribes prompts/pairwise_vanilla.txt verbatim)'; it is not"},
        "parser_check": {"pattern": c["pattern"], "case_sensitive": True, "takes": "the first 'Output (x)' in the reply",
                         "failure_behaviour": "random.randint(1,2) after random.seed(42), once per (dataset, prompt file) pass",
                         "deterministic_under_seed_42": [p["winner"] for p in parsed] == repeat, "synthetic": parsed,
                         "disagreements_with_tierb_parser": [p["reply"] for p in parsed if not p["agree_with_tierb"]]},
        "cost_estimate": est,
        "tierb_reference": {"run": TIERB_RUN.relative_to(HALF).as_posix(), "reexecution": (tb_res or {}).get("reexecution"),
                            "macro_mean_pct": round((tb_res or {}).get("reexecution", {}).get("mean_over_seeds", 0) * 100, 3) if tb_res else None,
                            "tokenizer_calibration": tok},
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    CHECK_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=_default), encoding="utf-8")
    if verbose:
        print(f"\n[{CARD_ID} --check] repo {commit[:8]} ({'matches' if commit == REPO_COMMIT else 'DIFFERS FROM'} the card); "
              f"meta_eval importable: {R.meta_eval is not None}; API calls made: 0")
        print("  datasets: " + ", ".join(f"{d} {ds_info[d]['n']}" for d in DATASETS) +
              f" = {summary['total_pairs']} pairs, 0 bytes downloaded (repository copy)" +
              (f"; == HF mirror on {hf_eq['identical']}/{hf_eq['rows_compared']} archived Tier B prompts" if hf_eq else ""))
        print(f"  eval_kwargs {c['eval_kwargs']} (swap config identical: {c['eval_kwargs'] == csw['eval_kwargs']}); parser {c['pattern']!r}")
        for d in DATASETS:
            print(f"    {d:20s} prompt sha {prompts[d]['normal']['sha256'][:12]} / swap {prompts[d]['swap']['sha256'][:12]}; "
                  f"{ds_info[d]['mean_tokens_in']['normal']:7.1f} mean input tokens")
        print(f"  vs the Tier B config prompt: identical {prompts['llmbar_natural']['normal']['user_identical_to_tierb']}, identical after "
              f"collapsing blank lines and '**' {prompts['llmbar_natural']['normal']['user_identical_to_tierb_ignoring_blank_lines_and_bold']}")
        print(f"  parser on {len(SYNTHETIC)} synthetic replies: {sum(not p['fail'] for p in parsed)} parsed, "
              f"{sum(p['fail'] for p in parsed)} fail -> coin flip; deterministic under seed 42: "
              f"{summary['parser_check']['deterministic_under_seed_42']}")
        for p in parsed:
            if p["fail"] or not p["agree_with_tierb"]:
                print(f"    {p['reply']!r:52s} -> repo winner {p['winner']} fail={p['fail']}; Tier B -> {p['tierb_parse']}")
        print(f"  estimate ({how}): {est['calls']} calls, {est['tokens_in']/1e6:.2f}M in, {est['tokens_out_expected']} out -> "
              f"${est['usd_expected']:.2f} (cap ${CAP:.0f}); calibration on {tok.get('sampled_calls')} Tier B calls: "
              f"{tok.get('estimate_minus_api_prompt_tokens')} token error")
        print(f"  -> {CHECK_JSON}")
    return summary


# ------------------------------------------------------------------------------------------------------- requests
def build_requests(seeds=SEEDS):
    ek, reqs = config()["eval_kwargs"], []
    for ds in DATASETS:
        rows = data(ds)
        for order in ORDERS:
            for i, m in enumerate(render(ds, order)):
                body = {"model": MODEL, "messages": m, "temperature": ek["temperature"], "max_tokens": ek["max_tokens"],
                        "top_p": ek["top_p"], "n": ek["n"]}
                if ek.get("logprobs"):
                    body["logprobs"], body["top_logprobs"] = True, ek["logprobs"]
                for s in range(seeds):
                    reqs.append({"id": f"{ds}|{order}|{i}", "seed_idx": s, "body": body,
                                 "meta": {"dataset": ds, "order": order, "idx": i, "human_winner": int(rows[i]["winner"]),
                                          "prompt_method": ORDERS[order]}})
    return reqs


def dry_run(seeds, cap):
    reqs, est = build_requests(seeds), estimate(seeds)
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN / "requests.jsonl").open("w", encoding="utf-8") as f:
        for r in reqs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    bat = run_battery(reqs, RUN, cap, dry_run=True, label=f"{CARD_ID} baseline_alive")
    print(f"[dry-run] {sum(len(data(d)) for d in DATASETS)} pairs x {len(ORDERS)} presentation orders x {seeds} seed(s) = "
          f"{len(reqs)} calls; body {config()['eval_kwargs']} (logprobs 5 -> logprobs=true, top_logprobs=5)")
    for d in DATASETS:
        p = est["per_dataset"][d]
        print(f"  {d:20s} {p['calls_per_seed']:5d} calls/seed {p['mean_tokens_in']:8.1f} mean in tok  ${p['usd_per_seed']:6.2f}/seed")
    print(f"[dry-run] {est['tokenizer']}: {est['tokens_in']/1e6:.3f}M input + {est['tokens_out_expected']} output tokens -> "
          f"${est['usd_expected']:.2f} expected (${est['usd_if_every_reply_hit_max_tokens']:.2f} if every reply hit max_tokens="
          f"{config()['eval_kwargs']['max_tokens']}); battery chars/4 estimate ${bat['est_usd']:.2f}; cap ${cap:.0f}")
    print(f"[dry-run] wrote {RUN / 'requests.jsonl'} ({len(reqs)} lines); no API calls were made")
    return {"calls": len(reqs), "battery_est_usd": bat["est_usd"], **est}


def run(seeds, cap, workers):
    reqs = build_requests(seeds)
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "run_config.json").write_text(json.dumps(
        {"card_id": CARD_ID, "model": MODEL, "seeds": seeds, "calls": len(reqs), "cap_usd": cap, "repo_commit": REPO_COMMIT,
         "eval_kwargs": config()["eval_kwargs"], "prompt_methods": dict(ORDERS), "estimate": estimate(seeds),
         "built_utc": now()}, indent=2), encoding="utf-8")
    run_battery(reqs, RUN, cap, workers=workers, label=f"{CARD_ID} baseline_alive")


# -------------------------------------------------------------------------------------------------------- analyze
def meta_eval_one(human, model, swap):
    """The repository's own meta_eval.pairwise_meta_eval when importable, else the same two lines locally."""
    R = repo()
    if R.meta_eval is not None:
        return R.meta_eval.pairwise_meta_eval(human, model, swap, verbose=False), "repo meta_eval.pairwise_meta_eval"
    h = np.array([x["winner"] for x in human])
    a, b = np.array([x["winner"] for x in model]), np.array([x["winner"] for x in swap])
    return ({"acc": float(((h == a).mean() + (h == b).mean()) / 2), "agr": None, "models_acc": float((a == b).mean()),
             "models_agr": None}, "local fallback (krippendorff/tabulate unavailable)")


def bootstrap(credits):
    """Percentile 95% CIs, resampling PAIRS (both presentation orders together) within each dataset."""
    rng = np.random.default_rng(BOOT_SEED)
    draws, macro = {d: [] for d in credits}, []
    for _ in range(N_BOOT):
        vals = []
        for d, a in credits.items():
            v = float(a[rng.integers(0, a.size, a.size)].mean()) * 100
            draws[d].append(v)
            vals.append(v)
        macro.append(sum(vals) / len(vals))
    ci = lambda x: [round(float(np.percentile(x, 2.5)), 3), round(float(np.percentile(x, 97.5)), 3)]
    return {"per_dataset_ci95": {d: ci(v) for d, v in draws.items()}, "macro_ci95": ci(macro), "n_boot": N_BOOT,
            "seed": BOOT_SEED, "unit": "pair, stratified by dataset"}


def judge(per_ds, macro, boot, fail_rate, incomplete):
    lo, hi = boot["macro_ci95"]
    half = (hi - lo) / 2
    band = [round(ORIGINAL["avg"] - half, 3), round(ORIGINAL["avg"] + half, 3)]
    others = [per_ds[d] for d in ("llmbar_adversarial", "mtbench", "instrusum")]
    ok = {"inside_original_band": band[0] <= macro <= band[1], "original_inside_our_ci": lo <= ORIGINAL["avg"] <= hi,
          "ordering_kept": per_ds["llmbar_natural"] > max(others) and (max(others) - min(others)) <= ORDER_SPREAD,
          "far_above_random_floor": lo >= ORIGINAL["random_floor"] + 10,
          "adversarial_above_chance": boot["per_dataset_ci95"]["llmbar_adversarial"][0] > ORIGINAL["random_floor"],
          "above_gpt4o_mini_row": macro > ORIGINAL["gpt_4o_mini_avg"], "nat_above_adv": per_ds["llmbar_natural"] > per_ds["llmbar_adversarial"]}
    unscorable = sorted({d for d in DATASETS if fail_rate.get(d, 0) > FAIL_UNSCORABLE} | set(incomplete))
    if unscorable or not ok["adversarial_above_chance"]:
        label = "사망 (dead)"
    elif ok["inside_original_band"] and ok["ordering_kept"] and ok["far_above_random_floor"]:
        label = "생존 (survived)"
    elif ok["above_gpt4o_mini_row"] and ok["nat_above_adv"]:
        label = "부분 생존 (partial)"
    else:
        label = "사망 (dead)"
    return label, {"original_band": band, "band_half_width": round(half, 3), "criteria": ok, "unscorable_datasets": unscorable}


def analyze(seeds=SEEDS):
    res = load_results(RUN)
    if not res:
        print(f"no archived calls in {RUN}; run --run first")
        return None
    c, pf = config(), parse_fn()
    seed_ids = sorted({k[1] for k in res})
    budget = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    served, fps, finish, lat, incomplete = Counter(), set(), Counter(), [], set()
    per_seed, credits_by_seed, frate_by_seed = {}, {}, {}
    for s in seed_ids:
        winners, fails, missing = {}, {}, {}
        for ds in DATASETS:
            for order in ORDERS:
                rows, miss = [], 0
                for i in range(len(data(ds))):             # dataset order, as the repository writes its output file
                    rec = res.get((f"{ds}|{order}|{i}", s))
                    ch = ((rec or {}).get("response") or {}).get("choices") or [{}]
                    rows.append({"response": [{"text": ((ch[0].get("message") or {}).get("content") or "") if rec else ""}]})
                    if rec is None:
                        miss += 1
                        continue
                    served[rec.get("model_served")] += 1
                    finish[ch[0].get("finish_reason")] += 1
                    fps.add(rec.get("system_fingerprint"))
                    lat.append(rec.get("latency_ms"))
                random.seed(42)                            # PairwiseEvaluator.pairwise_eval, once per output file
                out = [pf(r) for r in rows]
                winners[(ds, order)] = [{"winner": o[0]["winner"]} for o in out]
                fails[(ds, order)], missing[(ds, order)] = sum(o[1] for o in out), miss
                if miss:
                    incomplete.add(ds)
        rows_out, credits, frate = {}, {}, {}
        for ds in DATASETS:
            human = [{"winner": int(r["winner"])} for r in data(ds)]
            m, sw = winners[(ds, "normal")], winners[(ds, "swap")]
            r, how = meta_eval_one(human, m, sw)
            n = len(human)
            credits[ds] = np.array([((m[i]["winner"] == human[i]["winner"]) + (sw[i]["winner"] == human[i]["winner"])) / 2
                                    for i in range(n)], float)
            frate[ds] = (fails[(ds, "normal")] + fails[(ds, "swap")]) / (2 * n)
            acc = lambda p: round(float(np.mean([x["winner"] == h["winner"] for x, h in zip(p, human)])) * 100, 3)
            rows_out[ds] = {"acc": round(r["acc"] * 100, 3), "acc_normal": acc(m), "acc_swap": acc(sw),
                            "self_agreement_acc": round((r.get("models_acc") or 0) * 100, 3),
                            "krippendorff_alpha_orders": r.get("models_agr"), "krippendorff_alpha_vs_human": r.get("agr"),
                            "n_pairs": n, "parse_fails": {o: fails[(ds, o)] for o in ORDERS}, "parse_fail_rate": round(frate[ds], 5),
                            "missing_calls": sum(missing[(ds, o)] for o in ORDERS), "original": ORIGINAL[ds],
                            "delta": round(r["acc"] * 100 - ORIGINAL[ds], 3), "metric_code": how}
        per_seed[s] = {"per_dataset": rows_out, "macro_mean": round(sum(rows_out[d]["acc"] for d in DATASETS) / len(DATASETS), 3)}
        credits_by_seed[s], frate_by_seed[s] = credits, frate
    judged = sorted(per_seed, key=lambda k: per_seed[k]["macro_mean"])[len(per_seed) // 2]        # median seed
    rows_out, macro = per_seed[judged]["per_dataset"], per_seed[judged]["macro_mean"]
    boot = bootstrap(credits_by_seed[judged])
    label, detail = judge({d: rows_out[d]["acc"] for d in DATASETS}, macro, boot, frate_by_seed[judged], incomplete)
    tb = json.loads((TIERB_RUN / "result.json").read_text(encoding="utf-8")) if (TIERB_RUN / "result.json").exists() else {}
    tb_macro = round(tb.get("reexecution", {}).get("mean_over_seeds", 0) * 100, 3) if tb else None
    env = json.loads(CHECK_JSON.read_text(encoding="utf-8")) if CHECK_JSON.exists() else check(verbose=False)
    lat = sorted(x for x in lat if x is not None)
    frictions = [
        "no item-level release exists for any proprietary evaluator (the repository's results/ and the Hugging Face 'predictions' "
        "subset cover only the 25 open-source base LLMs), so the comparison is at the accuracy level (one decimal) and the original's sampling error has to be proxied by ours",
        "the repository has no LICENSE (GitHub API license: null): the code may be run but not redistributed; only the Hugging Face data mirror is apache-2.0",
        "ReIFE/base_llm.py imports vllm unconditionally, so even the pure-API arm cannot be imported without a stub, and "
        "meta_eval.py needs krippendorff and tabulate, which the repository never declares",
        "the base_pairwise parser resolves an unparsable reply with random.randint(1,2) (a coin flip seeded 42 per output file) "
        "instead of recording a miss, so format failures pull accuracy toward 50% rather than showing up; it is also case "
        "sensitive ('output (a)' misses) and takes the first 'Output (x)' in the reply, so a 'both are good' answer scores as (a)",
        "the Tier B config's transcription of prompts/pairwise_vanilla.txt is not verbatim (blank lines collapsed, "
        "'**equally likely**' unbolded) and its swapped order swaps the output contents where the repository swaps the display positions",
    ]
    if budget.get("stopped_at_cap"):
        frictions.append(f"the run stopped at the ${budget.get('cap_usd')} cap; incomplete datasets: {sorted(incomplete)}")
    meta = {
        "card_id": CARD_ID, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
        "target_paper": {"title": "ReIFE: Re-evaluating Instruction-Following Evaluation", "doi": "10.18653/v1/2025.naacl-long.610",
                         "repo": "https://github.com/yale-nlp/ReIFE", "repo_commit": REPO_COMMIT,
                         "repo_license": "none in the code repo; the Hugging Face mirror yale-nlp/ReIFE is apache-2.0",
                         "original_values": {**{d: ORIGINAL[d] for d in DATASETS}, "avg": ORIGINAL["avg"]},
                         "original_source": ORIGINAL["source"]},
        "generation": {"model_requested": MODEL, "model_served_field": sorted(x for x in served if x), "n_fingerprints": len({x for x in fps if x}),
                       "endpoint": "POST https://api.openai.com/v1/chat/completions (raw HTTPS, harness/openai_client.py)",
                       "parameters": f"{c['eval_kwargs']} from {CONFIGS['normal']} -> logprobs=true, top_logprobs=5; system + user "
                                     f"message from prompts/{ORDERS['normal']}.txt and prompts/{ORDERS['swap']}.txt",
                       "prompt_template_source": "the repository's own base_pairwise_eval (str.format_map + prompt_to_chatml), rendered offline with a capture-only client",
                       "seeds": len(seed_ids), "judged_seed_idx": judged, "battery": f"{len(res)} archived calls in {RUN.name}/calls.jsonl"},
        "evaluation": {"metric_code": rows_out[DATASETS[0]]["metric_code"], "parser": "ReIFE base_pairwise_parse (random.seed(42) per output file)",
                       "bootstrap": boot,
                       "environment_check": {"repo_commit_matches": env["repo"]["commit_matches"],
                                             "items_identical_to_hf_mirror": env["data_source"]["equality_check_vs_hf"].get("identical"),
                                             "prompt_identical_to_tierb_config": env["prompt_check"]["llmbar_natural"]["normal"]["user_identical_to_tierb"]}},
        "results": {"per_dataset": rows_out, "macro_mean": macro, "macro_ci95": boot["macro_ci95"], "per_seed": per_seed,
                    "original_avg": ORIGINAL["avg"], "delta_vs_original": round(macro - ORIGINAL["avg"], 3),
                    "judgment_detail": detail, "judgment": label,
                    "judged_by": "automatic rule per ANALYSIS_PLAN Sec. 1 as the card instantiates it (macro mean inside 84.0 +/- the "
                                 "bootstrap half-width, Nat > {Adv, MT, Ins} within 5 points, CI lower bound >= 60, no unscorable dataset); human double-coding pending",
                    "cost_usd": round(budget.get("cost_usd", 0.0), 3), "calls": budget.get("calls", len(res)), "errors": budget.get("errors", 0),
                    "call_log_stats": {"finish_reasons": dict(finish), "distinct_system_fingerprints": len({x for x in fps if x}),
                                       "latency_ms_median": lat[len(lat) // 2] if lat else None,
                                       "tokens_in": budget.get("tokens_in"), "tokens_out": budget.get("tokens_out")},
                    "tierb_comparison": {"run": TIERB_RUN.relative_to(HALF).as_posix(), "macro_mean": tb_macro, "seeds": 3,
                                         "difference_repo_minus_tierb": round(macro - tb_macro, 3) if tb_macro else None},
                    "note": (f"macro mean {macro:.2f} [95% CI {boot['macro_ci95'][0]:.2f}, {boot['macro_ci95'][1]:.2f}] vs the paper's 84.0 "
                             f"(delta {macro - ORIGINAL['avg']:+.2f}); per dataset "
                             + ", ".join(f"{d} {rows_out[d]['acc']:.1f} (orig {ORIGINAL[d]})" for d in DATASETS)
                             + (f". The Tier B prompt-level replay of the same claim gave {tb_macro} over 3 seeds, {macro - tb_macro:+.2f} "
                                f"points from this repository-based run; the two differ in prompt whitespace, in max_tokens (16 vs 64), in "
                                f"how the swapped order is built (output contents vs display positions) and in the failure rule (Tier B "
                                f"scores an unparsable reply wrong, the repository coin-flips it)." if tb_macro else ""))},
        "reproducibility_frictions_observed": frictions,
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUN / "result.json").write_text(json.dumps({"per_dataset": rows_out, "macro_mean": macro, "bootstrap": boot, "judgment": label},
                                                indent=2, ensure_ascii=False, default=_default), encoding="utf-8")
    (RUNS / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_default), encoding="utf-8")
    print(f"\n[{CARD_ID} --analyze] {len(res)} calls, {len(seed_ids)} seed(s), cost ${meta['results']['cost_usd']}")
    for d in DATASETS:
        r = rows_out[d]
        print(f"  {d:20s} {r['acc']:6.2f} (orig {ORIGINAL[d]:.1f}, delta {r['delta']:+.2f}) CI {boot['per_dataset_ci95'][d]}; normal "
              f"{r['acc_normal']:.1f} / swap {r['acc_swap']:.1f}; self-agreement {r['self_agreement_acc']:.1f}; fails {r['parse_fail_rate']:.2%}")
    print(f"  macro mean {macro:.2f} [{boot['macro_ci95'][0]:.2f}, {boot['macro_ci95'][1]:.2f}] vs 84.0 (band {detail['original_band']}); "
          f"Tier B prompt-level {tb_macro}")
    print(f"  judgment: {label}\n  -> {RUNS / 'run_meta.json'}")
    return meta


def main():
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="offline environment check (no API calls)")
    ap.add_argument("--dry-run", action="store_true", help="build the request list and estimate cost (no API calls)")
    ap.add_argument("--run", action="store_true", help="execute the battery (paid API calls, capped)")
    ap.add_argument("--analyze", action="store_true", help="score the archived replies and write run_meta.json")
    ap.add_argument("--seeds", type=int, default=SEEDS, help="passes over the full item set (default 1)")
    ap.add_argument("--cap", type=float, default=CAP, help=f"USD cap for --run (default {CAP:.0f})")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if not any((a.check, a.dry_run, a.run, a.analyze)):
        ap.print_help()
        return
    if a.check:
        check()
    if a.dry_run:
        dry_run(a.seeds, a.cap)
    if a.run:
        run(a.seeds, a.cap, a.workers)
    if a.analyze:
        analyze(a.seeds)


if __name__ == "__main__":
    main()
