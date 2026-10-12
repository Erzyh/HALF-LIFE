"""Card W4404781910 - OffsetBias: Leveraging Debiased Data for Tuning Evaluators (Park, Jwa, Ren, Kim, Choi;
Findings of EMNLP 2024 1043-1067; arXiv 2407.06551). Repository ncsoft/offsetbias at 0bd16e4
(external/repos/W4404781910/ncsoft__offsetbias). Live arm gpt-4o-2024-05-13, the exact snapshot the paper judged with
(config/gpt-4o.yaml); OpenAI shutdown 2026-10-23.

CLAIM (card): as a pairwise judge with the LLMBar prompt, gpt-4o-2024-05-13 scores 86.9% micro-average accuracy on the
160 EvalBiasBench samples (80 hand-written pairs x 2 response orders), cells 91.2 / 92.9 / 50.0 / 100.0 / 91.7 / 95.8
(length / concreteness / empty reference / content continuation / nested instruction / familiar knowledge), Table 4.
Each one-decimal cell has a unique integer pre-image (31/34, 26/28, 13/26, 24/24, 22/24, 23/24 = 139/160 = 86.875),
which --check re-derives and re-scores; item-level original outputs were never released, so the comparison with the
2024 run is at the accuracy level only.

DECISIONS 2026-09-19 (also written into the card under decisions_2026_09_19): EvalBiasBench only (no Table 1/2
LLMBar-HHH-MTBench extension); 3 seeds at the repository's own decoding settings (config/gpt-4o.yaml: temperature 0,
max_tokens 20, prompt llmbar); the repository's own scorer semantics (regex parse, unparsed = label 4 = incorrect,
exactly as run_bench.py); per-paper cost cap USD 3. Inference only - nothing is trained or distilled.

THE REPOSITORY'S OWN CODE IS CALLED, NOT COPIED. data: run_bench.get_benchmark_data("biasbench") ->
data/evalbiasbench/biasbench.json, 6 subsets / 80 pairs; these rows bypass make_data_row, so they are not stripped and
carry no id - identity here is positional (subset + index), in the order add_inference would have sent them. prompt:
module.InferenceModule(config={"prompt": "llmbar"}).make_conversation(instruction, r1, r2, swap) -> the [system, user]
pair from prompt/llmbar.py, swap exchanging Output (a) / Output (b). parse: run_bench.add_parse_result ->
module.get_prediction (output_pattern; no match = 4) and module.is_correct (swap flips the expected label; the label is
1 for all 80 pairs). score: run_bench.get_model_statistics over a result/<run>/biasbench.json written in our run tree -
single_accuracy is the Table 4 cell, the total is the micro-average of the 6 subsets' counts, pair_agreement_rate is
the Table 2 positional-agreement statistic. Two shims, both reported as frictions: module.py imports
torch/transformers/vllm/fastchat/openai at module level although this path needs none of them (vllm and fastchat are
not installed here), and the repository opens its JSON with the platform default encoding, which is cp949 on this
machine (UnicodeDecodeError on its own data file).

  python adapters/offsetbias_W4404781910.py --check      # offline: data, prompts, scorer on synthetic replies
  python adapters/offsetbias_W4404781910.py --dry-run    # request list + cost estimate, no API calls
  python adapters/offsetbias_W4404781910.py --run        # spends money, cap $3 -> runs/W4404781910/baseline_alive/
  python adapters/offsetbias_W4404781910.py --analyze    # Table 4 cells from the archive, CI, judgment, run_meta.json
"""
import argparse, builtins, contextlib, hashlib, io, json, os, subprocess, sys, types
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, pricing_for, run_battery  # noqa: E402

CARD, HALF = "W4404781910", HERE.parent.parent
REPO = HALF / "external" / "repos" / CARD / "ncsoft__offsetbias"
REPO_COMMIT = "0bd16e4ac935315999ed23480c69673b675884b0"
RUN_ROOT = HALF / "runs" / CARD
RUN = RUN_ROOT / "baseline_alive"
CHECK_JSON, META = RUN_ROOT / "environment_check.json", RUN_ROOT / "run_meta.json"
SCORE_DIR = RUN_ROOT / "repo_score"        # cwd for the repository's own scorer: <here>/result/<run_name>/biasbench.json

MODEL = "gpt-4o-2024-05-13"
PROMPT, TEMPERATURE, MAX_TOKENS = "llmbar", 0, 20                 # config/gpt-4o.yaml
CAP, SEEDS, WORKERS, N_BOOT, ENCODING = 3.0, 3, 4, 10000, "o200k_base"
HEAVY = ("torch", "transformers", "vllm", "fastchat", "fastchat.conversation", "openai", "datasets")
CELL = {"length bias": "length", "concreteness": "concreteness", "empty reference": "empty_reference",
        "content_continuation": "content_continuation", "nested_instruction": "nested_instruction",
        "familiar knowledge preference bias": "familiar_knowledge"}
ORIGINAL = {"total": 86.9, "cells": {"length": 91.2, "concreteness": 92.9, "empty_reference": 50.0, "content_continuation": 100.0,
                                     "nested_instruction": 91.7, "familiar_knowledge": 95.8},
            "counts": {"length": (31, 34), "concreteness": (26, 28), "empty_reference": (13, 26), "content_continuation": (24, 24),
                       "nested_instruction": (22, 24), "familiar_knowledge": (23, 24)},
            "source": "paper Table 4 (= appendix Table 6), row GPT-4o-0513, n=160"}
COMP = {"offsetbias_8b": 85.0, "llama3_8b_base_data": 66.3, "gpt_3_5_turbo_0613": 45.0, "chance": 50.0}

now = lambda: datetime.now(timezone.utc).isoformat()
rel = lambda p: str(Path(p)).replace(str(HALF) + os.sep, "")
sha_text = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
med = lambda xs: float(np.median(xs))


def _json_default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(type(o))


def orig_band():
    """Binomial reference band around the original 86.9 over the 80 pairs (card judgment rule: about +/- 7 pp)."""
    hw = 1.96 * (0.869 * (1 - 0.869) / 80) ** 0.5 * 100
    return [round(86.9 - hw, 2), round(86.9 + hw, 2)]


# --------------------------------------------------------------------------------- the repository's own code
class _Stub(types.ModuleType):
    """Placeholder for a dependency imported at the top of module.py that the biasbench / OpenAI path never calls."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        sys.modules.setdefault(f"{self.__name__}.{name}", _Stub(f"{self.__name__}.{name}"))
        return sys.modules[f"{self.__name__}.{name}"]


@contextlib.contextmanager
def _utf8_open():
    """run_bench.py opens its JSON with the platform default encoding (lines 77, 129, 160); cp949 here -> force utf-8."""
    real = builtins.open

    def patched(file, mode="r", *a, **kw):
        if "b" not in mode and not a and kw.get("encoding") is None:
            kw["encoding"] = "utf-8"
        return real(file, mode, *a, **kw)
    builtins.open = patched
    try:
        yield
    finally:
        builtins.open = real


@contextlib.contextmanager
def _cwd(path):
    old = os.getcwd()
    Path(path).mkdir(parents=True, exist_ok=True)
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(old)


def repo():
    """(module, run_bench, InferenceModule) imported from external/repos/...; the unused heavy deps are stubbed."""
    if not (REPO / "run_bench.py").exists():
        sys.exit(f"repository copy not found at {REPO}")
    for n in HEAVY:
        sys.modules.setdefault(n, _Stub(n))
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    import module, run_bench  # noqa: E402  (the repository's own files)
    return module, run_bench, module.InferenceModule(config={"prompt": PROMPT})


def load_benchmark():
    """The repository's own loader, run with cwd = the repository (it opens a relative path)."""
    run_bench = repo()[1]
    with _cwd(REPO), _utf8_open(), contextlib.redirect_stdout(io.StringIO()):
        return run_bench.get_benchmark_data("biasbench")


def samples(data):
    """(subset, row index, row, swap) in exactly the order run_bench.add_inference builds its conversation list."""
    for subset, rows in data.items():
        for i, row in enumerate(rows):
            for swap in (False, True):
                yield subset, i, row, swap


def rid(subset, i, swap):
    return f"{CELL[subset]}|{i:02d}|{'swap' if swap else 'orig'}"


def score_with_repo(data, run_name, completions):
    """Parse and score `completions` {(subset, i, swap): text} with run_bench.add_parse_result + get_model_statistics.
    Writes the repository-format result/<run_name>/biasbench.json under runs/<card>/repo_score (never into external/)."""
    run_bench, im = repo()[1:]
    scored = json.loads(json.dumps(data, ensure_ascii=False))          # the repo mutates its input; keep ours clean
    for subset, i, row, swap in samples(scored):
        txt = completions.get((subset, i, swap))
        row.setdefault("result", {})["swap" if swap else "orig"] = {"completion": "" if txt is None else txt}
    run_bench.add_parse_result(scored, im)
    out = SCORE_DIR / "result" / run_name
    out.mkdir(parents=True, exist_ok=True)
    (out / "biasbench.json").write_text(json.dumps(scored, ensure_ascii=False, indent=2), encoding="utf-8")
    with _cwd(SCORE_DIR), _utf8_open(), contextlib.redirect_stdout(io.StringIO()):
        return run_bench.get_model_statistics(run_name)["biasbench"], scored


def table4(stats):
    """A Table 4 row: per-subset single_accuracy (the repository's own rounding) plus the micro-average total."""
    counts = {CELL[s]: (st["single_correct"], st["single_total"]) for s, st in stats.items()}
    c, n = sum(x[0] for x in counts.values()), sum(x[1] for x in counts.values())
    ag, pr = sum(st["pair_agree"] for st in stats.values()), sum(st["pair_total"] for st in stats.values())
    return {"cells": {CELL[s]: st["single_accuracy"] for s, st in stats.items()}, "counts": counts, "correct": c, "n": n,
            "total": round(c / n * 100, 1), "positional_agreement": round(ag / pr * 100, 1), "pair_agree": ag, "pairs": pr}


def pair_credits(scored):
    """Per-pair credit in [0, 1] = mean of the two orders' is_correct. Bootstrap unit = the 80 pairs (card)."""
    cred = [(int(r["result"]["orig"]["is_correct"]) + int(r["result"]["swap"]["is_correct"])) / 2
            for rows in scored.values() for r in rows]
    cells = [CELL[s] for s, rows in scored.items() for _ in rows]
    return np.array(cred, float), np.array(cells)


def bootstrap(cred, cells, n_boot=N_BOOT, seed=0):
    rng = np.random.default_rng(seed)
    tot = cred[rng.integers(0, len(cred), (n_boot, len(cred)))].mean(axis=1) * 100
    pct = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]
    out = {"total_ci95": pct(tot), "n_boot": n_boot, "seed": seed, "unit": "pair (80 pairs, both orders resampled together)",
           "cells_ci95": {}}
    for c in dict.fromkeys(cells):
        sub = cred[cells == c]
        out["cells_ci95"][c] = pct(sub[rng.integers(0, len(sub), (n_boot, len(sub)))].mean(axis=1) * 100)
    return out


# --------------------------------------------------------------------------------- requests and cost
def build_requests(seeds=SEEDS, data=None, im=None):
    data, im = (load_benchmark() if data is None else data), (repo()[2] if im is None else im)
    reqs = []
    for s in range(seeds):                                   # seed-major: a stop at the cap leaves earlier seeds complete
        for subset, i, row, swap in samples(data):
            msgs = im.make_conversation(row["instruction"], row["response1"], row["response2"], swap)
            reqs.append({"id": rid(subset, i, swap), "seed_idx": s,
                         "meta": {"subset": subset, "cell": CELL[subset], "row": i, "swap": swap, "label": row["label"],
                                  "bias": row.get("bias"), "prompt_sha256": sha_text(json.dumps(msgs, ensure_ascii=False))},
                         "body": {"model": MODEL, "messages": msgs, "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS}})
    return reqs


def tiktoken_estimate(reqs):
    try:
        import tiktoken
    except ImportError:
        return None
    enc = tiktoken.get_encoding(ENCODING)
    n_ans = max(len(enc.encode("Output (a)")), len(enc.encode("Output (b)")))        # the only compliant replies
    tin = sum(3 + sum(3 + len(enc.encode(m["role"])) + len(enc.encode(m["content"])) for m in r["body"]["messages"]) for r in reqs)
    pr, exp, mx = pricing_for(MODEL), n_ans * len(reqs), MAX_TOKENS * len(reqs)
    return {"calls": len(reqs), "tokens_in": tin, "tokens_out_expected": exp, "tokens_out_max": mx, "encoding": ENCODING,
            "usd_expected": tin / 1e6 * pr["input"] + exp / 1e6 * pr["output"], "answer_tokens": n_ans, "pricing": pr,
            "usd_max_tokens_bound": tin / 1e6 * pr["input"] + mx / 1e6 * pr["output"], "mean_tokens_in": tin / len(reqs)}


def write_requests(reqs, run_dir):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "requests.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs), encoding="utf-8")
    return run_dir / "requests.jsonl"


# --------------------------------------------------------------------------------- --check
SYNTHETIC = {  # kind -> (what the synthetic judge replies, expected total accuracy under the repository's scorer)
    "oracle": ("the preference-labelled option, named for the order shown", 100.0),
    "oracle_verbose": ("the same choice plus an explanation (the regex anchors at line start, so it still parses)", 100.0),
    "always_a": ("always 'Output (a)': pure position bias, correct on orig and wrong on swap", 50.0),
    "always_b": ("always 'Output (b)'", 50.0),
    "bracketed": ("'[Output (a)]', the format the card's protocol paraphrase quotes; the repo regex does NOT match it", 0.0),
    "refusal": ("'I cannot decide.': no match, prediction 4, counted incorrect", 0.0),
    "table4_pattern": ("the reconstructed original counts 31/34, 26/28, 13/26, 24/24, 22/24, 23/24", 86.9),
}


def synthetic(data, kind):
    """Synthetic judge replies for --check. Every label is 1, so the correct answer is (a) on orig and (b) on swap."""
    out, seen = {}, {}
    for subset, i, row, swap in samples(data):
        right = "Output (a)" if (row["label"] == 1) != swap else "Output (b)"
        if kind == "table4_pattern":
            seen[subset] = k = seen.get(subset, 0) + 1
            t = right if k <= ORIGINAL["counts"][CELL[subset]][0] else "I cannot decide."
        else:
            t = {"oracle": right, "oracle_verbose": f"{right} is better because it follows the instruction more precisely.",
                 "always_a": "Output (a)", "always_b": "Output (b)", "bracketed": f"[{right}]",
                 "refusal": "I cannot decide."}[kind]
        out[(subset, i, swap)] = t
    return out


def repo_head():
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def check(seeds=SEEDS):
    im, data, head = repo()[2], load_benchmark(), repo_head()
    sizes = {CELL[s]: {"pairs": len(rows), "samples": 2 * len(rows)} for s, rows in data.items()}
    labels = sorted({row["label"] for rows in data.values() for row in rows})
    print(f"[{CARD} --check] repository {rel(REPO)} HEAD {head} ({'matches' if head == REPO_COMMIT else 'DIFFERS FROM'} the card)")
    print(f"  imported from the repository: module.py, run_bench.py, prompt/{PROMPT}.py (stubbed, unused here: {', '.join(HEAVY)})")
    print(f"  data via run_bench.get_benchmark_data('biasbench'): {sum(len(r) for r in data.values())} pairs in {len(data)} subsets "
          f"= {2*sum(len(r) for r in data.values())} samples; labels present {labels} (response1 is always the preferred output)")
    for c, v in sizes.items():
        n = ORIGINAL["counts"][c][1]
        print(f"    {c:22s} {v['pairs']:3d} pairs -> n={v['samples']:3d} samples (Table 4 n={n}) {'OK' if v['samples'] == n else 'MISMATCH'}")

    tpl = {"system_sha256": sha_text(im.system_message), "user_template_sha256": sha_text(im.user_message_template),
           "output_pattern": im.output_pattern, "system": im.system_message,
           "user_template_head": im.user_message_template[:120], "user_template_tail": im.user_message_template[-80:]}
    shas, bad = set(), []
    for subset, i, row, swap in samples(data):
        msgs = im.make_conversation(row["instruction"], row["response1"], row["response2"], swap)
        shas.add(sha_text(json.dumps(msgs, ensure_ascii=False)))
        a, b = (row["response2"], row["response1"]) if swap else (row["response1"], row["response2"])
        u = msgs[1]["content"]
        if not ([m["role"] for m in msgs] == ["system", "user"] and msgs[0]["content"] == im.system_message
                and f"# Instruction:\n{row['instruction']}\n" in u and f"# Output (a):\n{a}\n" in u and f"# Output (b):\n{b}\n" in u):
            bad.append(rid(subset, i, swap))
    print(f"  prompts rendered by module.InferenceModule.make_conversation: 160 (both orders), distinct {len(shas)}, malformed "
          f"{len(bad)}; system+user, system sha256 {tpl['system_sha256'][:12]}, parameters temperature {TEMPERATURE} max_tokens {MAX_TOKENS}")
    print(f"  DEVIATION: the card's protocol.messages paraphrase quotes '[Output (a)]'; prompt/{PROMPT}.py asks for '\"Output (a)\"' and the "
          f"parser regex is {im.output_pattern[1]!r}, so a bracketed reply is label 4 = incorrect. The repository text is used.")

    parser = {t: im.get_prediction(t) for t in ["Output (a)", "Output (b)", "\nOutput (a)", " Output (b)", "[Output (a)]", "output (a)",
                                                "Both are equally good.", "", "The winner is Output (b)", "Output (a) is better."]}
    correctness = {f"pred{p}_label1_{'swap' if sw else 'orig'}": im.is_correct(p, 1, sw) for p in (1, 2, 3, 4) for sw in (False, True)}
    print(f"  module.get_prediction on hand-made strings: {json.dumps(parser, ensure_ascii=False)}")
    print(f"  module.is_correct (label 1): orig needs prediction 1, swap needs prediction 2; tie (3) and unparsed (4) are always incorrect")
    print(f"  run_bench.add_parse_result + get_model_statistics on synthetic replies:")
    runs, sane = {}, {}
    for kind, (_, expected) in SYNTHETIC.items():
        runs[kind] = t = table4(score_with_repo(data, f"check_{kind}", synthetic(data, kind))[0])
        sane[kind] = {"observed": t["total"], "expected": expected, "ok": abs(t["total"] - expected) < 0.05}
        print(f"    {kind:16s} total {t['total']:5.1f} ({t['correct']:3d}/{t['n']})  agreement {t['positional_agreement']:5.1f}  "
              f"cells {[t['cells'][c] for c in ORIGINAL['cells']]}  expected total {expected}{'' if sane[kind]['ok'] else '  <-- MISMATCH'}")
    t4 = runs["table4_pattern"]
    cells_ok = all(abs(t4["cells"][c] - ORIGINAL["cells"][c]) < 0.05 for c in ORIGINAL["cells"]) and sane["table4_pattern"]["ok"]
    print(f"  Table 4 arithmetic reproduced from the reconstructed counts: {'YES' if cells_ok else 'NO'} (paper cells "
          f"{list(ORIGINAL['cells'].values())} total {ORIGINAL['total']}); original binomial band over 80 pairs {orig_band()}")

    est = tiktoken_estimate(build_requests(seeds, data, im))
    if est:
        print(f"  cost at {seeds} seeds: {est['calls']} calls, {est['tokens_in']:,} prompt tokens ({est['mean_tokens_in']:.0f}/call), "
              f"{est['tokens_out_expected']:,} expected output tokens -> ${est['usd_expected']:.2f} (max_tokens bound ${est['usd_max_tokens_bound']:.2f})")
    try:
        import openai
        sdk = getattr(openai, "__version__", "unknown")
    except Exception:
        sdk = "not installed"
    out = {
        "card_id": CARD, "checked_utc": now(), "python": sys.version.split()[0], "model": MODEL, "seeds": seeds,
        "repo": {"path": rel(REPO), "head": head, "card_commit": REPO_COMMIT, "head_matches_card": head == REPO_COMMIT,
                 "imported": ["module.py", "run_bench.py", f"prompt/{PROMPT}.py"], "stubbed_dependencies": list(HEAVY),
                 "openai_sdk_installed": sdk, "utf8_shim": "builtins.open forced to utf-8 around the repository's own file reads (cp949 locale)",
                 "note": "the repository's openai SDK path is not used; --run posts the same body over raw HTTPS (harness/openai_client.py)"},
        "data": {"loader": "run_bench.get_benchmark_data('biasbench')", "file": "data/evalbiasbench/biasbench.json", "subsets": sizes,
                 "pairs": sum(len(r) for r in data.values()), "samples": 2 * sum(len(r) for r in data.values()), "labels_present": labels,
                 "sizes_match_table4": all(sizes[c]["samples"] == ORIGINAL["counts"][c][1] for c in sizes)},
        "prompt": {"source": f"prompt/{PROMPT}.py via module.InferenceModule.make_conversation", **tpl, "rendered": 2 * sum(len(r) for r in data.values()),
                   "distinct_prompt_sha256": len(shas), "malformed": bad,
                   "parameters": {"temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "prompt": PROMPT, "source": "config/gpt-4o.yaml"},
                   "card_paraphrase_deviation": "card protocol.messages quotes '[Output (a)]'; the repository template and regex use 'Output (a)'"},
        "parser": {"get_prediction_examples": parser, "is_correct_matrix": correctness, "unparsed_label": 4,
                   "unparsed_counts_as": "incorrect (repository semantics, decision 2026-09-19)"},
        "scorer_on_synthetic_replies": {"definitions": {k: v[0] for k, v in SYNTHETIC.items()}, "runs": runs, "sanity": sane,
                                        "table4_arithmetic_reproduced": cells_ok},
        "original": {**ORIGINAL, "binomial_reference_band_80_pairs": orig_band(), "comparators": COMP},
        "estimate": est, "decisions": "card key decisions_2026_09_19", "repo_format_results_written_to": rel(SCORE_DIR / "result"),
    }
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    print(f"  -> {rel(CHECK_JSON)}")
    return out


# --------------------------------------------------------------------------------- --dry-run / --run
def dry_run(seeds=SEEDS, cap=CAP):
    reqs = build_requests(seeds)
    path, est = write_requests(reqs, RUN), tiktoken_estimate(reqs)
    battery = run_battery(reqs, RUN, cap, dry_run=True, label=f"{CARD} baseline_alive")
    print(f"[dry-run] {len(reqs)//seeds} samples (80 pairs x 2 orders) x {seeds} seeds = {len(reqs)} calls; model {MODEL}; "
          f"temperature {TEMPERATURE}, max_tokens {MAX_TOKENS}, prompt {PROMPT} (config/gpt-4o.yaml)")
    if est:
        print(f"[dry-run] tiktoken {ENCODING}: {est['tokens_in']:,} prompt tokens ({est['mean_tokens_in']:.0f}/call), "
              f"{est['tokens_out_expected']:,} output tokens expected ({est['answer_tokens']}/call, a compliant reply) -> "
              f"${est['usd_expected']:.2f}; worst case at max_tokens {MAX_TOKENS}: ${est['usd_max_tokens_bound']:.2f} "
              f"(pricing ${est['pricing']['input']}/${est['pricing']['output']} per 1M)")
    print(f"[dry-run] battery's own chars/4 estimate: ${battery['est_usd']:.2f}; cap ${cap:.2f}; card budget $1.2")
    print(f"[dry-run] requests -> {rel(path)} (no API calls made)")
    return {"calls": len(reqs), "estimate": est, "battery_est_usd": battery["est_usd"], "requests": rel(path)}


def run(seeds=SEEDS, cap=CAP, workers=WORKERS):
    reqs = build_requests(seeds)
    write_requests(reqs, RUN)
    (RUN / "run_config.json").write_text(json.dumps(
        {"card_id": CARD, "model": MODEL, "prompt": PROMPT, "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "seeds": seeds,
         "calls": len(reqs), "cap_usd": cap, "benchmark": "EvalBiasBench (biasbench.json, 80 pairs x 2 orders)", "repo_commit": REPO_COMMIT,
         "estimate": tiktoken_estimate(reqs), "built_utc": now(), "decisions": "card key decisions_2026_09_19"},
        indent=2, default=_json_default), encoding="utf-8")
    return run_battery(reqs, RUN, cap, workers=workers, label=f"{CARD} baseline_alive")


# --------------------------------------------------------------------------------- --analyze
def judge(total, ci):
    """ANALYSIS_PLAN section 1 as the card instantiates it."""
    hw, band = (ci[1] - ci[0]) / 2, orig_band()
    if total <= COMP["chance"] + 5 or ci[0] <= COMP["chance"] or (COMP["offsetbias_8b"] - total) > hw:
        return "사망 (dead)", "at or near chance, or the ordering against the tuned OffsetBias-8B (85.0) inverts by more than the CI"
    if band[0] <= total <= band[1] and total >= COMP["offsetbias_8b"]:
        return "생존 (survived)", f"median inside the original band {band} and at or above OffsetBias-8B (85.0), far above chance"
    return "부분 생존 (partial)", f"clearly above chance and above the 8B baselines, but outside the original band {band} or below 85.0"


def analyze(seeds=SEEDS):
    res = load_results(RUN)
    if not res:
        print(f"no archived calls in {rel(RUN)}; run --run first")
        return None
    data = load_benchmark()
    env = json.loads(CHECK_JSON.read_text(encoding="utf-8")) if CHECK_JSON.exists() else {}
    budget = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    n_samples = sum(2 * len(r) for r in data.values())
    by_seed, served, fps, finish, empty = {}, set(), set(), {}, 0
    for (_, sidx), rec in res.items():
        ch = ((rec.get("response") or {}).get("choices") or [{}])[0]
        txt, m = (ch.get("message") or {}).get("content"), rec["meta"]
        by_seed.setdefault(sidx, {})[(m["subset"], m["row"], m["swap"])] = "" if txt is None else txt
        served.add(rec.get("model_served")); fps.add(rec.get("system_fingerprint"))
        finish[ch.get("finish_reason")] = finish.get(ch.get("finish_reason"), 0) + 1
        empty += not txt
    complete = sorted(s for s, d in by_seed.items() if len(d) == n_samples)
    partial = {s: len(d) for s, d in by_seed.items() if s not in complete}
    if not complete:
        print(f"no complete seed (archived per seed: {partial}); cannot judge")
        return None
    per_seed, creds, cells = {}, [], None
    for s in complete:
        stats, scored = score_with_repo(data, f"seed{s}", by_seed[s])
        per_seed[s] = table4(stats)
        cred, cells = pair_credits(scored)
        creds.append(cred)
    boot = bootstrap(np.mean(creds, axis=0), cells)
    total = med([per_seed[s]["total"] for s in complete])
    agree = med([per_seed[s]["positional_agreement"] for s in complete])
    label, why = judge(total, boot["total_ci95"])
    rows = {c: {"acc": med([per_seed[s]["cells"][c] for s in complete]), "per_seed": [per_seed[s]["cells"][c] for s in complete],
                "ci95": boot["cells_ci95"][c], "orig": ORIGINAL["cells"][c], "orig_counts": list(ORIGINAL["counts"][c]),
                "n": ORIGINAL["counts"][c][1]} for c in ORIGINAL["cells"]}
    for c, r in rows.items():
        r["delta"] = round(r["acc"] - r["orig"], 1)
    rows["total"] = {"acc": total, "per_seed": [per_seed[s]["total"] for s in complete], "ci95": boot["total_ci95"], "orig": ORIGINAL["total"],
                     "delta": round(total - ORIGINAL["total"], 1), "n": n_samples, "orig_band_binomial_80_pairs": orig_band(),
                     "orig_inside_ci": boot["total_ci95"][0] <= ORIGINAL["total"] <= boot["total_ci95"][1],
                     "rerun_inside_orig_band": orig_band()[0] <= total <= orig_band()[1], "positional_agreement": agree,
                     "orig_positional_agreement": "not reported for EvalBiasBench (Table 2 covers LLMBar / HHH / MT-Bench)"}
    er = rows["empty_reference"]
    frictions = [
        "item-level original judge outputs were never released (only Table 4 percentages at one decimal), so agreement with the 2024 run can be compared only at the accuracy level; the original per-cell counts used here are reconstructed from the printed percentages, each of which has a unique integer pre-image",
        "module.py imports torch, transformers, vllm, fastchat and openai at module level although the OpenAI / biasbench path uses none of them; vllm and fastchat are not installable on this machine, so the adapter stubs them to reach InferenceModule's renderer and parser",
        "run_bench.py opens its JSON files with the platform default encoding; on this Windows locale (cp949) the repository's own data loader raises UnicodeDecodeError, so text mode is forced to UTF-8 around the repository's calls",
        "requirements.txt is unpinned (the openai SDK version of the original run is unknown); the re-run posts the same chat-completions body over raw HTTPS and logs the served model and system fingerprint",
        "biasbench rows bypass run_bench.make_data_row, so they carry no id and are not stripped: item identity is positional (subset + index)",
        "the card's protocol.messages paraphrase quotes '[Output (a)]'; the repository template asks for '\"Output (a)\"' and the parser regex requires 'Output (a)' at the start of a line, so a bracketed reply is label 4 = incorrect",
        f"the empty-reference cell rests on 13 pairs, so one flipped pair moves it by 7.7 pp (observed {er['acc']} vs 50.0, CI {[round(x, 1) for x in er['ci95']]}); it is not judged on its own",
        f"temperature 0 over the API is not deterministic; {len(complete)} complete seeds were run and the median is judged (per-seed totals {rows['total']['per_seed']})",
    ]
    if empty:
        frictions.append(f"{empty} archived replies had empty content and were scored as unparsed (label 4 = incorrect), exactly as run_bench.py does")
    if budget.get("stopped_at_cap"):
        frictions.append(f"the run stopped at the ${budget.get('cap_usd')} cap; incomplete seeds dropped: {partial}")
    note = (f"total {total:.1f} vs paper {ORIGINAL['total']} (delta {total - ORIGINAL['total']:+.1f}), 95% CI [{boot['total_ci95'][0]:.1f}, "
            f"{boot['total_ci95'][1]:.1f}] over the 80 pairs; original binomial band {orig_band()}; comparators OffsetBias-8B 85.0, "
            f"GPT-3.5-0613 45.0, chance 50.0; positional agreement {agree:.1f}. Empty-reference cell {er['acc']:.1f} (paper 50.0): "
            f"{'still at chance level, the paper qualitative point holds' if er['ci95'][0] <= 60 else 'clearly above chance, a reportable change'}. {why}")
    meta = {
        "card_id": CARD, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
        "target_paper": {"title": "OffsetBias: Leveraging Debiased Data for Tuning Evaluators", "repo": "https://github.com/ncsoft/offsetbias",
                         "repo_commit": REPO_COMMIT, "original_source": ORIGINAL["source"]},
        "generation": {"model_requested": MODEL, "model_served": sorted(x for x in served if x), "n_fingerprints": len(fps - {None}),
                       "substitute_snapshot": "none - gpt-4o-2024-05-13 is the snapshot the paper itself judged with (config/gpt-4o.yaml, Sec. 5.3)",
                       "parameters": f"system + user message from prompt/{PROMPT}.py via module.InferenceModule.make_conversation; temperature "
                                     f"{TEMPERATURE}; max_tokens {MAX_TOKENS}; no top_p and no seed (config/gpt-4o.yaml); endpoint POST "
                                     f"https://api.openai.com/v1/chat/completions (harness/openai_client.py, raw HTTPS)",
                       "battery": f"EvalBiasBench {n_samples} samples (80 pairs x 2 orders) x {len(complete)} complete seeds = {len(res)} archived "
                                  f"calls in {rel(RUN)}/calls.jsonl; scored by the repository's own run_bench.add_parse_result / "
                                  f"get_model_statistics; median over seeds; 95% CI = pair-level bootstrap ({N_BOOT} resamples, rng 0)"},
        "results": {"rows": rows, "per_seed": {str(s): per_seed[s] for s in complete}, "incomplete_seeds_dropped": partial,
                    "comparators": COMP, "bootstrap": boot,
                    "cost_usd": round(budget.get("cost_usd", sum(r.get("cost_usd", 0) for r in res.values())), 4),
                    "calls": budget.get("calls", len(res)), "errors": budget.get("errors", 0),
                    "call_log_stats": {"finish_reasons": finish, "empty_replies": empty, "distinct_fingerprints": len(fps - {None}),
                                       "tokens_in": budget.get("tokens_in"), "tokens_out": budget.get("tokens_out")},
                    "judgment": label,
                    "judged_by": "automatic rule per ANALYSIS_PLAN section 1 as the card instantiates it: survived = median total (3 seeds) inside the "
                                 "binomial band around the original 86.9 over 80 pairs AND far above chance AND at or above OffsetBias-8B 85.0; partial "
                                 "= outside the band but clearly above chance and above the 8B baselines; dead = at or near chance, or the ordering "
                                 "against OffsetBias-8B inverts by more than the CI. The six cells are secondary evidence. Human double-coding pending",
                    "note": note},
        "environment_check": {"file": rel(CHECK_JSON), "repo_head_matches_card": env.get("repo", {}).get("head_matches_card"),
                              "table4_arithmetic_reproduced": env.get("scorer_on_synthetic_replies", {}).get("table4_arithmetic_reproduced")},
        "reproducibility_frictions_observed": frictions,
    }
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    (RUN / "result.json").write_text(json.dumps({"rows": rows, "per_seed": {str(s): per_seed[s] for s in complete}, "judgment": label},
                                                indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    print(f"\n[{CARD} --analyze] {len(res)} calls, complete seeds {complete}, served {sorted(x for x in served if x)}, "
          f"{len(fps - {None})} fingerprints, ${meta['results']['cost_usd']}")
    print(f"  {'cell':24s}{'rerun':>8s}{'paper':>8s}{'delta':>8s}   95% CI")
    for c in list(ORIGINAL["cells"]) + ["total"]:
        r = rows[c]
        print(f"  {c:24s}{r['acc']:8.1f}{r['orig']:8.1f}{r['delta']:+8.1f}   [{r['ci95'][0]:.1f}, {r['ci95'][1]:.1f}]  n={r['n']}")
    print(f"  positional agreement {agree:.1f}; judgment: {label} - {why}\n  -> {rel(META)}")
    return meta


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="offline validation of data, prompts and scorer (no API calls)")
    ap.add_argument("--dry-run", action="store_true", help="build the request list and estimate cost (no API calls)")
    ap.add_argument("--run", action="store_true", help="execute the battery (paid API calls, capped)")
    ap.add_argument("--analyze", action="store_true", help="score the archived replies and write run_meta.json")
    ap.add_argument("--seeds", type=int, default=SEEDS)
    ap.add_argument("--cap", type=float, default=CAP)
    ap.add_argument("--workers", type=int, default=WORKERS)
    a = ap.parse_args()
    if not any((a.check, a.dry_run, a.run, a.analyze)):
        ap.print_help()
        return
    if a.check:
        check(a.seeds)
    if a.dry_run:
        dry_run(a.seeds, a.cap)
    if a.run:
        run(a.seeds, a.cap, a.workers)
    if a.analyze:
        analyze(a.seeds)


if __name__ == "__main__":
    main()
