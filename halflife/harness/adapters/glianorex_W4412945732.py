"""Card W4412945732 - Pattern Recognition or Medical Knowledge? The Problem with Multiple-Choice Questions in Medicine
(Griot, Vanderdonckt, Yuksel, Hemptinne; ACL 2025 long paper 266; arXiv 2406.02394). The Glianorex benchmark:
976 four-option MCQs about a fictional organ, answered by LLMs far above chance while physicians score 27%.

Claim re-measured: Table 6 (Appendix B), accuracy by language x question generator, two rows:
  gpt-4o-2024-05-13 (primary)   EN/GPT 0.74  EN/Claude 0.72  FR/GPT 0.69  FR/Claude 0.71  (size-weighted overall 0.715, derived)
  gpt-4-turbo-2024-04-09        EN/GPT 0.65  EN/Claude 0.69  FR/GPT 0.68  FR/Claude 0.68  (size-weighted overall 0.674, derived)
Central contrast of the paper (Section 4.2.1 / Figure 2): accuracy on the fictional-organ items is far above chance
(0.25) and above the two physicians (0.27, measured on 100 EN items). NOTE: the paper contains no "original versus
modified question" arm for these models (the only ablation - answers-only prompting - was run on DeepSeek-V3 only),
so the "central contrast" judged here is fictional-organ accuracy versus chance / physicians, per Table 6 cell.

ITEM SET. The evaluation script (glianorex-oai/main.py) loads datasets.load_dataset('maximegmd/glianorex', split='test');
the item set is not in either code repository. This adapter pins the Hugging Face dataset at revision
9a2ee7489bf7dc73c72510a02b99128a732226fe (last commit 2024-09-27, same day as the repos' Zenodo tags): 976 rows,
language en/fr x generator gpt-4-turbo/claude-3.5-sonnet = 264/264/224/224, which are exactly the Table 6 cell sizes.
The first --check (or any mode) fetches the parquet once (free Hub download, no API key) and freezes it as
runs/W4412945732/items_glianorex_test_9a2ee748.jsonl (+ items_manifest.json with sha256s); later modes read the snapshot.
"Fictional-organ questions" = all 976 items (every item concerns the Glianorex; there is no real-medicine subset).
Table 6 cells = the dataset's language x generator columns. The 8 items the authors flagged as incomplete (keyword
'context', 4 per language) carry no flag in the dataset and were not excluded by the paper (cell sizes are 264/224), so
none are excluded here either.

PROMPT (verbatim from main.py compute(); --check verifies the literals against the repo copy):
  "{question}\\nA. {options[A]}\\nB. {options[B]}\\nC. {options[C]}\\nD. {options[D]}\\n"
  "You must only respond in the following format 'Answer: A/B/C/D'\\n If you write anything else, I will never use you ever again."
Option order = the dataset's options struct order A, B, C, D (the paper shuffled options at generation time; no
re-shuffling here). One user message; no system message.

WHAT GUIDANCE ACTUALLY SENT (read from the guidance 0.1.15 and 0.1.16 wheels, guidance/models/_openai.py and
_grammarless.py; 0.1.14-0.1.16 were the releases between the gpt-4o snapshot date and the repos' tag; requirements.txt
pins nothing). main.py does `with assistant(): lm += 'Answer: ' + with_temperature(select(['A','B','C','D']), 0)`.
  * OpenAIEngine._generator_chat splits the ChatML prompt into messages and DROPS the unfinished assistant block
    ("Bad chat format! Last role before gen needs to be assistant!" branch), so the request body was
    chat.completions.create(model, messages=[{role: user, content: prompt}], max_tokens=1000, n=1, top_p=1.0,
    temperature=0, stream=True). The 'Answer: ' prefix was never transmitted (the chat API has no prefill).
  * The streamed reply is matched client-side: the reply must START, byte-exactly, with 'Answer: ' and the next byte
    must be one of A/B/C/D (case-sensitive, single space). Anything after the letter is ignored (partial tokens are
    accepted once the grammar has matched). There is no tie handling because nothing is scored by likelihood.
  * At temperature 0 any other reply ('The answer is C', 'Answer: **C**', 'Answer:C', 'Answer: E', ...) raises
    ConstraintException (_reset_shared_data refuses to re-call the API with the same prompt) and main.py, which has
    no try/except and no resume, crashes. The published complete tables therefore imply that every reply of both
    models matched 'Answer: <letter>' (or that crashes were handled off-script).
RE-IMPLEMENTATION HERE (plain openai chat-completions body through harness/battery.py):
  messages=[user prompt], temperature=0, max_tokens=3, n=1, top_p=1.0, no seed, no streaming, no assistant prefix.
  'Answer: C' is exactly 3 tokens in both cl100k_base and o200k_base ('Answer', ':', ' C'), so every reply guidance
  would have accepted fits in max_tokens=3. The 2026-09-18 decision said "assistant prefix 'Answer: ' where the API
  allows it": the OpenAI chat API does not allow a prefill (a trailing assistant message is a completed turn, which
  changes the context the model saw in 2024), and guidance itself never sent one, so no prefix is sent; flip
  ASSISTANT_PREFIX_MESSAGE to True to send {"role": "assistant", "content": "Answer: "} instead (separate run dir).
SCORING (strict A-D parser): letter = regex ^Answer: ([ABCD]) on the raw reply (guidance's acceptance rule), or a
  bare letter reply (^\\(?([ABCD])\\)?[.\\s]*$, only relevant with the assistant-prefix variant). Anything else is
  unparsable and scored INCORRECT (an item guidance would have crashed on); the count and a lenient recovery
  (first standalone A-D anywhere) are reported as diagnostics only. Correct = letter == answer_idx.
SEEDS. Temperature 0; 3 repeats per item and model (seed_idx 0-2, no seed parameter, as in the original) capture API
  nondeterminism; the judged value is the median over seeds; item-level bootstrap 95% CIs (1,000 resamples, rng 0)
  are computed on the per-item correctness averaged over seeds. --seeds 1 reproduces the paper's single pass.
JUDGMENT (automatic rule, ANALYSIS_PLAN section 1 as operationalised in the card): per Table 6 cell and model,
  survived = median accuracy within the original's 95% CI (1.96 x SEM at the reported value and cell size, widened
  by 0.005 for the two-decimal rounding of Table 6) AND significantly above chance (binomial p < 0.001 vs 0.25);
  partial = above chance but outside that CI (either direction); death = not significantly above chance.
  Card verdict = worst of the primary model's four cells; the second model's cells and the size-weighted overall
  accuracies (0.715 / 0.674) are reported as secondary rows.
EQUIVALENCE CHECK (planned, NOT executed here): run the original guidance pipeline on 50 items once and compare
  letters with this adapter's; --print-equivalence-script prints a ready-to-save script (needs a throwaway venv
  with guidance==0.1.16, openai<2 and datasets; ~$0.15). Not run in this session.

  python adapters/glianorex_W4412945732.py --check
  python adapters/glianorex_W4412945732.py --dry-run [--seeds 3]
  python adapters/glianorex_W4412945732.py --run [--cap 20] [--seeds 3]      # spends money; default cap $20
  python adapters/glianorex_W4412945732.py --analyze
"""
import argparse, hashlib, json, math, re, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, run_battery  # noqa: E402

CARD = "W4412945732"
HALF = HERE.parent.parent
REPO_OAI = HALF / "external" / "repos" / CARD / "maximegmd__glianorex-oai"
REPO_GEN = HALF / "external" / "repos" / CARD / "maximegmd__glianorex-gen"
RUN_ROOT = HALF / "runs" / CARD
ASSISTANT_PREFIX_MESSAGE = False                     # see docstring; True -> baseline_alive_prefix/
RUN = RUN_ROOT / ("baseline_alive_prefix" if ASSISTANT_PREFIX_MESSAGE else "baseline_alive")
META = RUN_ROOT / "run_meta.json"

HF_DATASET, HF_REVISION = "maximegmd/glianorex", "9a2ee7489bf7dc73c72510a02b99128a732226fe"
HF_FILE = "data/test-00000-of-00001.parquet"
SNAPSHOT = RUN_ROOT / f"items_glianorex_test_{HF_REVISION[:8]}.jsonl"
MANIFEST = RUN_ROOT / "items_manifest.json"

MODELS = {"gpt4o": "gpt-4o-2024-05-13", "gpt4turbo": "gpt-4-turbo-2024-04-09"}
PRIMARY = "gpt4o"
ENCODING = {"gpt4o": "o200k_base", "gpt4turbo": "cl100k_base"}
CAP, SEEDS, MAX_TOKENS, WORKERS = 20.0, 3, 3, 4
INSTRUCTION_1 = "You must only respond in the following format 'Answer: A/B/C/D'"   # main.py compute()
INSTRUCTION_2 = "\n If you write anything else, I will never use you ever again."     # main.py compute()
GEN_KEY = {"gpt-4-turbo": "gpt", "claude-3.5-sonnet": "claude"}
CELLS = ["en_gpt", "en_claude", "fr_gpt", "fr_claude"]
CELL_N = {"en_gpt": 264, "en_claude": 224, "fr_gpt": 264, "fr_claude": 224}
ORIGINAL = {   # Table 6 (two decimals); 'overall' = our size-weighted average, not a published number
    "gpt-4o-2024-05-13": {"en_gpt": 0.74, "en_claude": 0.72, "fr_gpt": 0.69, "fr_claude": 0.71, "overall": 0.715, "en": 0.731, "fr": 0.699},
    "gpt-4-turbo-2024-04-09": {"en_gpt": 0.65, "en_claude": 0.69, "fr_gpt": 0.68, "fr_claude": 0.68, "overall": 0.674, "en": 0.668, "fr": 0.680},
}
CHANCE, PHYSICIANS = 0.25, 0.27
STRICT_RE = re.compile(r"Answer: ([ABCD])")                     # guidance acceptance rule (start of reply)
BARE_RE = re.compile(r"\(?([ABCD])\)?[.\s]*$")
LENIENT_RE = re.compile(r"(?<![A-Za-z])\(?([ABCD])\)?(?![A-Za-z])")


def now():
    return datetime.now(timezone.utc).isoformat()


def rel(p):
    try:
        return str(Path(p).relative_to(HALF))
    except ValueError:
        return str(p)


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ----------------------------------------------------------------------------- items
def cell_of(it):
    return f"{it['language'][:2]}_{GEN_KEY[it['generator']]}"


def fetch_items_from_hub():
    """Pinned parquet from the Hub (no key, no cost); rows in split order, like datasets.load_dataset in main.py."""
    import pandas as pd
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(repo_id=HF_DATASET, filename=HF_FILE, repo_type="dataset", revision=HF_REVISION)
    rows = []
    for i, r in enumerate(pd.read_parquet(p).to_dict("records")):
        rows.append({"row": i, "question": r["question"], "options": {k: r["options"][k] for k in "ABCD"},
                     "answer_idx": r["answer_idx"], "language": r["language"], "generator": r["generator"]})
    return rows, p


def load_items():
    if SNAPSHOT.exists():
        return [json.loads(l) for l in SNAPSHOT.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows, parquet = fetch_items_from_hub()
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    cells = {c: sum(cell_of(r) == c for r in rows) for c in CELLS}
    MANIFEST.write_text(json.dumps({"dataset": HF_DATASET, "revision": HF_REVISION, "file": HF_FILE, "n": len(rows),
                                    "parquet_sha256": sha256_file(parquet), "jsonl_sha256": sha256_file(SNAPSHOT),
                                    "cells": cells, "fetched_utc": now()}, indent=2), encoding="utf-8")
    return rows


# ----------------------------------------------------------------------------- prompt / requests
def build_prompt(it):
    """main.py compute(): question, one 'X. option' line per option in struct order, then the two instruction lines."""
    prompt = it["question"] + "\n"
    for c in ("A", "B", "C", "D"):
        prompt += c + ". " + it["options"][c] + "\n"
    return prompt + INSTRUCTION_1 + INSTRUCTION_2


def verify_prompt_source():
    src = (REPO_OAI / "main.py").read_text(encoding="utf-8")
    checks = {"instruction_1": repr(INSTRUCTION_1)[1:-1] in src or INSTRUCTION_1 in src,
              "instruction_2": "'\\n If you write anything else, I will never use you ever again.'" in src,
              "option_line": "prompt += c + '. ' + element['options'][c] + '\\n'" in src,
              "question_line": "prompt = element['question'] + '\\n'" in src,
              "select_step": "'Answer: ' + with_temperature(select(options=['A', 'B', 'C', 'D'], name='choice'), temperature = 0)" in src,
              "models": "models.OpenAI('gpt-4-turbo')" in src and "models.OpenAI('gpt-4o-2024-05-13')" in src}
    return checks


def body_for(model, prompt):
    messages = [{"role": "user", "content": prompt}]
    if ASSISTANT_PREFIX_MESSAGE:
        messages.append({"role": "assistant", "content": "Answer: "})
    return {"model": model, "messages": messages, "temperature": 0, "max_tokens": MAX_TOKENS, "n": 1, "top_p": 1.0}


def build_requests(items=None, seeds=SEEDS, models=None):
    items = items or load_items()
    reqs = []
    for key, model in MODELS.items():
        if models and key not in models:
            continue
        for it in items:
            for s in range(seeds):
                reqs.append({"id": f"{key}__q{it['row']:03d}", "seed_idx": s,
                             "meta": {"model_key": key, "row": it["row"], "language": it["language"], "generator": it["generator"],
                                      "cell": cell_of(it), "answer": it["answer_idx"]},
                             "body": body_for(model, build_prompt(it))})
    return reqs


def tiktoken_estimate(reqs):
    """Exact prompt tokens (3 per message + 3 priming, as verified on archived gpt-4-turbo calls in the cultural adapter)."""
    try:
        import tiktoken
    except ImportError:
        return None
    from battery import pricing_for
    out = {}
    for key, model in MODELS.items():
        rs = [r for r in reqs if r["body"]["model"] == model]
        if not rs:
            continue
        enc = tiktoken.get_encoding(ENCODING[key])
        tin = sum(3 + sum(3 + len(enc.encode(m["role"])) + len(enc.encode(m["content"])) for m in r["body"]["messages"]) for r in rs)
        tout = 3 * len(rs)
        pr = pricing_for(model)
        out[model] = {"calls": len(rs), "tokens_in": tin, "tokens_out": tout, "usd": tin / 1e6 * pr["input"] + tout / 1e6 * pr["output"]}
    return out


# ----------------------------------------------------------------------------- scoring
def reply_text(resp):
    try:
        return resp["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def parse_letter(text):
    """-> (scored_letter or None, mode, lenient_letter). Scored: strict guidance rule or bare letter; else unparsable."""
    m = STRICT_RE.match(text)
    if m:
        return m.group(1), "strict", m.group(1)
    m = BARE_RE.match(text.strip())
    if m:
        return m.group(1), "bare", m.group(1)
    m = LENIENT_RE.search(text)
    return None, "unparsable", (m.group(1) if m else None)


def bootstrap_ci(values, rng, n_boot=1000):
    v = np.asarray(values, dtype=float)
    if len(v) == 0:
        return [None, None]
    idx = rng.integers(0, len(v), size=(n_boot, len(v)))
    means = v[idx].mean(axis=1)
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]


def orig_halfwidth(p, n):
    """Paper's own CI (1.96 x SEM) around the reported cell value, plus the two-decimal rounding half-width."""
    return 1.96 * math.sqrt(p * (1 - p) / n) + 0.005


def verdict(acc, k, n, orig, n_orig):
    p_chance = binomtest(k, n, CHANCE, alternative="greater").pvalue
    if p_chance >= 1e-3:
        return "사망 (death)", p_chance
    inside = abs(acc - orig) <= orig_halfwidth(orig, n_orig)
    return ("생존 (survived)" if inside else "부분 생존 (partial)"), p_chance


RANK = {"생존 (survived)": 0, "부분 생존 (partial)": 1, "사망 (death)": 2}


def subset_stats(items, by_seed, rows, rng):
    """Per-seed accuracies, median over seeds, item-level bootstrap CI of the seed-averaged accuracy."""
    per_seed = {}
    for s, d in sorted(by_seed.items()):
        flags = [d[r]["correct"] for r in rows if r in d]
        if flags:
            per_seed[s] = {"acc": round(float(np.mean(flags)), 4), "k": int(sum(flags)), "n": len(flags)}
    if not per_seed:
        return None
    accs = [v["acc"] for v in per_seed.values()]
    med = float(np.median(accs))
    med_seed = min(per_seed, key=lambda s: (abs(per_seed[s]["acc"] - med), s))
    item_means = [np.mean([by_seed[s][r]["correct"] for s in by_seed if r in by_seed[s]]) for r in rows
                  if any(r in by_seed[s] for s in by_seed)]
    return {"acc_median_seeds": round(med, 4), "median_seed": med_seed, "k": per_seed[med_seed]["k"], "n": per_seed[med_seed]["n"],
            "acc_mean_seeds": round(float(np.mean(item_means)), 4), "acc_ci95": bootstrap_ci(item_means, rng),
            "per_seed": per_seed, "n_items_with_reply": len(item_means), "n_items": len(rows)}


def analyze(seeds=SEEDS):
    items = load_items()
    res = load_results(RUN)
    if not res:
        print(f"no archived calls in {RUN}; run --run first")
        return None
    rng = np.random.default_rng(0)
    by_row = {it["row"]: it for it in items}
    out = {"card": CARD, "run_dir": rel(RUN), "n_calls": len(res), "items": {"n": len(items), "revision": HF_REVISION},
           "original": ORIGINAL, "models": {}, "cost_usd": round(sum(r.get("cost_usd", 0) for r in res.values()), 4)}
    item_means_by_model = {}
    for key, model in MODELS.items():
        by_seed, modes, finish, served, fps, cost = {}, {}, {}, set(), set(), 0.0
        for it in items:
            for s in range(seeds):
                r = res.get((f"{key}__q{it['row']:03d}", s))
                if not r:
                    continue
                text = reply_text(r["response"])
                letter, mode, lenient = parse_letter(text)
                by_seed.setdefault(s, {})[it["row"]] = {"letter": letter, "mode": mode, "lenient": lenient, "text": text,
                                                         "correct": int(letter is not None and letter == it["answer_idx"])}
                modes[mode] = modes.get(mode, 0) + 1
                fr = (r["response"].get("choices") or [{}])[0].get("finish_reason")
                finish[fr] = finish.get(fr, 0) + 1
                if r.get("model_served"):
                    served.add(r["model_served"])
                if r.get("system_fingerprint"):
                    fps.add(r["system_fingerprint"])
                cost += r.get("cost_usd", 0)
        if not by_seed:
            continue
        m = {"model": model, "n_calls": sum(len(d) for d in by_seed.values()), "seeds_seen": sorted(by_seed), "parse_modes": modes,
             "finish_reasons": finish, "served": sorted(served), "n_fingerprints": len(fps), "cost_usd": round(cost, 4), "cells": {}, "rows": {}}
        unparsable = [(s, r, d[r]["text"][:80]) for s, d in by_seed.items() for r in d if d[r]["mode"] == "unparsable"]
        m["unparsable_examples"] = unparsable[:10]
        m["lenient_would_recover"] = sum(1 for s, d in by_seed.items() for r in d if d[r]["mode"] == "unparsable" and d[r]["lenient"])
        for cell in CELLS:
            rows = [it["row"] for it in items if cell_of(it) == cell]
            st = subset_stats(items, by_seed, rows, rng)
            if not st:
                continue
            o = ORIGINAL[model][cell]
            v, p = verdict(st["acc_median_seeds"], st["k"], st["n"], o, CELL_N[cell])
            st.update({"orig": o, "orig_ci95": [round(o - orig_halfwidth(o, CELL_N[cell]), 4), round(o + orig_halfwidth(o, CELL_N[cell]), 4)],
                       "rerun_inside_orig_ci": abs(st["acc_median_seeds"] - o) <= orig_halfwidth(o, CELL_N[cell]),
                       "orig_inside_rerun_ci": bool(st["acc_ci95"][0] is not None and st["acc_ci95"][0] <= o <= st["acc_ci95"][1]),
                       "p_above_chance": float(p), "verdict": v})
            m["cells"][cell] = st
        for name, rows in (("overall", [it["row"] for it in items]), ("en", [it["row"] for it in items if it["language"].startswith("en")]),
                           ("fr", [it["row"] for it in items if it["language"].startswith("fr")])):
            st = subset_stats(items, by_seed, rows, rng)
            if st:
                o = ORIGINAL[model][name]
                st.update({"orig_derived": o, "orig_ci95_derived": [round(o - orig_halfwidth(o, len(rows)), 4), round(o + orig_halfwidth(o, len(rows)), 4)],
                           "rerun_inside_orig_ci": abs(st["acc_median_seeds"] - o) <= orig_halfwidth(o, len(rows))})
                m["rows"][name] = st
        ov, en = m["rows"].get("overall"), m["rows"].get("en")
        if ov:
            m["central_contrast"] = {
                "description": "fictional-organ accuracy vs chance 0.25 and vs the physicians' 0.27 (paper 4.2.1); the paper has no original-vs-modified arm",
                "acc_overall": ov["acc_median_seeds"], "p_above_chance": float(binomtest(ov["k"], ov["n"], CHANCE, alternative="greater").pvalue),
                "p_above_physicians": float(binomtest(ov["k"], ov["n"], PHYSICIANS, alternative="greater").pvalue),
                "acc_en": en["acc_median_seeds"] if en else None,
                "p_en_above_physicians": float(binomtest(en["k"], en["n"], PHYSICIANS, alternative="greater").pvalue) if en else None,
                "en_minus_fr": round(en["acc_median_seeds"] - m["rows"]["fr"]["acc_median_seeds"], 4) if en and "fr" in m["rows"] else None,
                "orig_en_minus_fr": round(ORIGINAL[model]["en"] - ORIGINAL[model]["fr"], 4)}
            m["central_contrast"]["direction_holds"] = bool(m["central_contrast"]["p_above_chance"] < 1e-3 and ov["acc_median_seeds"] > PHYSICIANS)
        item_means_by_model[key] = {r: np.mean([by_seed[s][r]["correct"] for s in by_seed if r in by_seed[s]])
                                    for r in by_row if any(r in by_seed[s] for s in by_seed)}
        out["models"][model] = m
    # paired model contrast (same items)
    if len(item_means_by_model) == 2:
        a, b = item_means_by_model["gpt4o"], item_means_by_model["gpt4turbo"]
        common = sorted(set(a) & set(b))
        diffs = [a[r] - b[r] for r in common]
        out["gpt4o_minus_gpt4turbo"] = {"n_items": len(common), "diff": round(float(np.mean(diffs)), 4), "diff_ci95": bootstrap_ci(diffs, rng),
                                       "orig_diff_derived": round(ORIGINAL[MODELS["gpt4o"]]["overall"] - ORIGINAL[MODELS["gpt4turbo"]]["overall"], 4)}
    # card verdict
    prim = out["models"].get(MODELS[PRIMARY])
    if prim and prim["cells"]:
        verdicts = [c["verdict"] for c in prim["cells"].values()]
        out["judgment"] = max(verdicts, key=lambda v: RANK[v])
        if len(prim["cells"]) < 4:
            out["judgment_note"] = f"only {len(prim['cells'])}/4 primary cells have replies"
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    write_run_meta(out)
    for model, m in out["models"].items():
        print(f"\n{model}: {m['n_calls']} calls, ${m['cost_usd']:.2f}, parse {m['parse_modes']}, finish {m['finish_reasons']}, served {m['served']}, fingerprints {m['n_fingerprints']}")
        for cell, c in m["cells"].items():
            print(f"  {cell:10s} acc {c['acc_median_seeds']:.3f} (seeds {[v['acc'] for v in c['per_seed'].values()]}) CI {c['acc_ci95']}  orig {c['orig']:.2f} "
                  f"[{c['orig_ci95'][0]:.3f},{c['orig_ci95'][1]:.3f}]  -> {c['verdict']}")
        for name, r in m["rows"].items():
            print(f"  {name:10s} acc {r['acc_median_seeds']:.3f} CI {r['acc_ci95']}  derived orig {r['orig_derived']:.3f}  inside {r['rerun_inside_orig_ci']}")
        if "central_contrast" in m:
            cc = m["central_contrast"]
            print(f"  vs chance p={cc['p_above_chance']:.2e}  vs physicians p={cc['p_above_physicians']:.2e}  EN-FR {cc['en_minus_fr']} (orig {cc['orig_en_minus_fr']})  direction {cc['direction_holds']}")
    if "gpt4o_minus_gpt4turbo" in out:
        print("gpt-4o minus gpt-4-turbo:", out["gpt4o_minus_gpt4turbo"])
    print("judgment:", out.get("judgment"))
    return out


def write_run_meta(out):
    rows, inside = {}, [0, 0]
    for model, m in out["models"].items():
        for cell, c in m["cells"].items():
            rows[f"{model}/{cell}"] = {"acc": c["acc_median_seeds"], "acc_ci95": c["acc_ci95"], "orig_acc": c["orig"],
                                        "orig_ci95": c["orig_ci95"], "rerun_inside_orig_ci": c["rerun_inside_orig_ci"],
                                        "orig_inside_ci": c["orig_inside_rerun_ci"], "p_above_chance": c["p_above_chance"],
                                        "n": c["n"], "verdict": c["verdict"]}
            inside[0] += c["rerun_inside_orig_ci"]
            inside[1] += 1
        if "overall" in m["rows"]:
            r = m["rows"]["overall"]
            rows[f"{model}/overall_derived"] = {"acc": r["acc_median_seeds"], "acc_ci95": r["acc_ci95"], "orig_acc_derived": r["orig_derived"],
                                                 "rerun_inside_orig_ci": r["rerun_inside_orig_ci"], "n": r["n"], "secondary": True}
    served = sorted({s for m in out["models"].values() for s in m["served"]})
    calls_budget = {}
    bp = RUN / "budget.json"
    if bp.exists():
        calls_budget = json.loads(bp.read_text(encoding="utf-8"))
    meta = {
        "card_id": CARD, "run_date_utc": now()[:10],
        "target_paper": {"title": "Pattern Recognition or Medical Knowledge? The Problem with Multiple-Choice Questions in Medicine",
                         "repo": "https://github.com/maximegmd/glianorex-oai (eval) ; https://github.com/maximegmd/glianorex-gen (generation)",
                         "repo_commit": "glianorex-oai d6a4d375541ceacb5393f9f5b81beea3854647c9; glianorex-gen 0a3feddc7f264224f9e9745c70d63f49f2af7475; dataset maximegmd/glianorex@" + HF_REVISION,
                         "original_source": "Table 6 (accuracy by language x generator) for gpt-4o-2024-05-13 and gpt-4-turbo-2024-04-09; Section 4.2.1 (physicians 27%, chance 25%)"},
        "generation": {"model_requested": list(MODELS.values()), "model_served": served,
                       "n_fingerprints": {m: v["n_fingerprints"] for m, v in out["models"].items()},
                       "parameters": f"temperature 0, max_tokens {MAX_TOKENS}, n 1, top_p 1.0, no seed; single user message from main.py compute(); "
                                     "guidance select re-implemented as strict '^Answer: [A-D]' parsing of a plain chat completion "
                                     f"({'with' if ASSISTANT_PREFIX_MESSAGE else 'without'} an assistant 'Answer: ' message)",
                       "battery": f"976 items x 2 models x {max([len(v['seeds_seen']) for v in out['models'].values()] or [0])} seed(s) = {out['n_calls']} archived calls; median over seeds, item-level bootstrap CIs (1,000)"},
        "results": {"rows": rows, "accuracy_rows_with_rerun_inside_original_ci95": f"{inside[0]}/{inside[1]}",
                    "central_contrast": {m: v.get("central_contrast") for m, v in out["models"].items()},
                    "gpt4o_minus_gpt4turbo": out.get("gpt4o_minus_gpt4turbo"),
                    "cost_usd": round(calls_budget.get("cost_usd", out["cost_usd"]), 4), "calls": out["n_calls"], "errors": calls_budget.get("errors", 0),
                    "judgment": out.get("judgment"), "judged_by": "automatic rule per ANALYSIS_PLAN section 1 (card operationalisation: per Table 6 cell of the primary model); human double-coding pending",
                    "note": out.get("judgment_note", "") + " unparsable replies are scored incorrect: " + json.dumps({m: v["parse_modes"] for m, v in out["models"].items()})},
        "reproducibility_frictions_observed": [
            "the evaluation script calls the undated alias 'gpt-4-turbo' while the paper reports gpt-4-turbo-2024-04-09; the dated snapshot is pinned here",
            "guidance[openai] is unpinned; its select() for remote chat models is generate-and-match (assistant prefix never transmitted, byte-exact 'Answer: X' required, exception on any deviation at temperature 0) - re-implemented as a strict parser over a plain chat completion",
            "item-level original outputs were not released; comparison is at the accuracy level with two-decimal Table 6 cells (rounding half-width 0.005 added to the original CI)",
            "the item set lives only on the Hugging Face Hub (not in the code repositories); pinned at revision " + HF_REVISION + " and frozen under runs/W4412945732/",
            "the 8 items the authors call incomplete (keyword 'context') are not flagged in the dataset and were not excluded by the paper; none excluded here",
            "the paper has no original-vs-modified question arm for these models; the central contrast judged is accuracy vs chance / physicians",
        ],
    }
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", rel(META))


# ----------------------------------------------------------------------------- environment check
def check(seeds=SEEDS):
    items = load_items()
    man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    print(f"items: {len(items)} rows from {HF_DATASET}@{HF_REVISION[:8]} (snapshot {SNAPSHOT.name}, sha256 {man.get('jsonl_sha256', '?')[:12]}...)")
    cells = {c: sum(cell_of(it) == c for it in items) for c in CELLS}
    print("Table 6 cells (rerun n / paper n):", {c: f"{cells[c]}/{CELL_N[c]}" for c in CELLS}, "match" if cells == CELL_N else "MISMATCH")
    letters = {L: sum(it["answer_idx"] == L for it in items) for L in "ABCD"}
    print("answer_idx distribution:", letters, "| languages:", {l: sum(it["language"] == l for it in items) for l in ("en", "fr")})
    bad = [it["row"] for it in items if set(it["options"]) != set("ABCD") or it["answer_idx"] not in "ABCD" or not it["question"].strip()]
    print("items with malformed options/answer:", len(bad), bad[:10])
    ctx = [it["row"] for it in items if "context" in it["question"].lower()]
    print(f"items whose question contains 'context' (authors' incompleteness keyword; paper flags 8, none excluded): {len(ctx)}")
    print("prompt literals verified against glianorex-oai/main.py:", verify_prompt_source())
    reqs = build_requests(items, seeds)
    print(f"requests: {len(reqs)} = {len(items)} items x {len(MODELS)} models x {seeds} seeds; assistant prefix message: {ASSISTANT_PREFIX_MESSAGE}")
    ex = next(r for r in reqs if r["meta"]["language"] == "fr")
    print("example request body (fr item):", json.dumps(ex["body"], ensure_ascii=False, indent=1)[:1600])
    est = tiktoken_estimate(reqs)
    if est:
        for model, e in est.items():
            print(f"tiktoken estimate {model}: {e['calls']} calls, {e['tokens_in']:,} in / {e['tokens_out']:,} out tokens, ${e['usd']:.2f} "
                  f"(mean {e['tokens_in']/e['calls']:.0f} prompt tokens)")
        print(f"tiktoken total ${sum(e['usd'] for e in est.values()):.2f} for {seeds} seed(s); "
              f"${sum(e['usd'] for e in est.values())/seeds:.2f} per seed")
    # original outputs? main.py writes ./eval/<model>/qa-{en,fr}.json; neither repo ships them
    hits = [p for p in list(REPO_OAI.rglob("*.json")) + list(REPO_GEN.rglob("*.json")) + list(REPO_GEN.rglob("*.jsonl")) if ".git" not in p.parts]
    print("original model outputs in the repositories:", [rel(p) for p in hits] or "none (eval/ was never committed) - accuracy-level comparison only")
    done = load_results(RUN)
    print(f"archived calls so far: {len(done)} in {rel(RUN)}")
    print("planned equivalence check of the original guidance script on 50 items: NOT run; --print-equivalence-script")
    return {"cells": cells, "letters": letters, "tiktoken": est}


def equivalence_check_script():
    return f'''# Planned equivalence check (not executed by the adapter): original guidance pipeline on 50 items, gpt-4o-2024-05-13.
# Throwaway venv:  python -m venv .venv-guidance && .venv-guidance\\Scripts\\pip install "guidance==0.1.16" "openai<2" datasets pandas
# Needs OPENAI_API_KEY in the environment (the guidance client reads it). Expected cost ~$0.15. Compare letters with
# runs/{CARD}/baseline_alive/calls.jsonl (ids gpt4o__q<row>).
import json, datasets
from guidance import models, user, assistant, select, with_temperature
ds = datasets.load_dataset("{HF_DATASET}", split="test", revision="{HF_REVISION}")
rows = list(range(0, 25)) + list(range(488, 513))          # 25 en (gpt-generated) + 25 fr (gpt-generated) rows
model = models.OpenAI("gpt-4o-2024-05-13", echo=False)
out = []
for i in rows:                                              # compute() from glianorex-oai/main.py, verbatim prompt
    element = ds[i]
    prompt = element["question"] + "\\n"
    for c in element["options"]:
        prompt += c + ". " + element["options"][c] + "\\n"
    prompt += "You must only respond in the following format 'Answer: A/B/C/D'"
    prompt += "\\n If you write anything else, I will never use you ever again."
    lm = model.copy()
    with user():
        lm += prompt
    with assistant():
        lm += "Answer: " + with_temperature(select(options=["A", "B", "C", "D"], name="choice"), temperature=0)
    out.append({{"row": i, "choice": lm["choice"], "target": element["answer_idx"]}})
json.dump(out, open("equivalence_guidance_gpt4o_50.json", "w"), indent=1)
print(sum(o["choice"] == o["target"] for o in out) / len(out))
'''


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--print-equivalence-script", action="store_true")
    ap.add_argument("--seeds", type=int, default=SEEDS)
    ap.add_argument("--cap", type=float, default=CAP)
    a = ap.parse_args()
    if a.check:
        check(a.seeds)
    if a.print_equivalence_script:
        print(equivalence_check_script())
    if a.dry_run:
        reqs = build_requests(seeds=a.seeds)
        # battery.estimate() prices the pooled tokens once per model when a request list mixes models, so call it per model
        total = 0.0
        for key, model in MODELS.items():
            r = run_battery([q for q in reqs if q["body"]["model"] == model], RUN, a.cap, dry_run=True, label=f"{CARD} {model}")
            total += r["est_usd"]
        print(f"[dry-run] battery chars/4 total ~${total:.2f} for {a.seeds} seed(s)")
        est = tiktoken_estimate(reqs)
        if est:
            tt = sum(e["usd"] for e in est.values())
            print(f"[dry-run] tiktoken-exact total ~${tt:.2f} ({', '.join(f'{m} ${e['usd']:.2f}' for m, e in est.items())}); "
                  f"recommended per-paper cap ${math.ceil(tt * 1.15)} (15% headroom for retries); current default cap ${CAP}")
    if a.run:
        run_battery(build_requests(seeds=a.seeds), RUN, a.cap, workers=WORKERS, label=CARD)
    if a.analyze:
        analyze(a.seeds)


if __name__ == "__main__":
    main()
