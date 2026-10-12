"""Card W4406880877 - People who frequently use ChatGPT for writing tasks are accurate and robust detectors
of AI-generated text (Russell, Karpinska, Iyyer; arXiv 2501.15654). Live arm: o1-2024-12-17 as the ZERO-SHOT + COT
prompt-based detector, Table 2 section (C).

CLAIM (card): overall TPR 54.0 (FPR 4.0) over 150 AI-generated / 150 human-written articles, far below the expert
majority vote 99.3 (0.0), with a collapse on the evasion blocks: 83.3 / 53.3 / 96.7 / 20.0 / 16.7 for GPT-4o,
Claude-3.5-Sonnet, GPT-4o-paraphrased, o1-pro and humanized o1-pro (30 AI + 30 human articles per block).

RE-EXECUTION PATH: the authors' own code, not a transcription. external/repos/W4406880877/jenna-russell__human_detectors
(MIT, afcf03d1) ships the dataset (human_detectors.json, 300 records keyed '0'-'299'), the prompt file and the detector
class. This adapter imports models.py and drives models.Detector with a stub LLM, so prompt rendering (.format(text))
and answer parsing (re.search(r'<answer>(.*?)</answer>', re.DOTALL) plus the <description> twin) are the authors' code
verbatim. Request body per models.ChatGPT.obtain_response, o1 branch: {model, messages:[user], seed:42} - no
temperature, max_tokens or reasoning_effort (API default 'medium' = footnote 22 "reasoning efforts to 'medium' for O1").

DECISIONS 2026-09-19 (card key decisions_2026_09_19): repo prompt file verbatim; repo seed 42; reasoning_effort unset;
all 300 articles (Tier B covered the 150 AI ones only); 1 seed (o1 pricing, the paper ran once); per-paper cap USD 45.
Tier B (runs/tierb/W4406880877/) ran the same row from a Table 20 transcription over the AI half: TPR 54.67 (82/150),
USD 16.50 / 150 calls. --check re-parses those replies with the repository parser and must reproduce 82/150; their
measured token usage calibrates the --dry-run estimate.

  python adapters/detect_W4406880877.py --check      # offline: data, prompt, one exact request, Tier B re-parse
  python adapters/detect_W4406880877.py --dry-run    # 300 requests + calibrated cost estimate (no API calls)
  python adapters/detect_W4406880877.py --run        # run_battery, cap $45 -> runs/W4406880877/baseline_alive/
  python adapters/detect_W4406880877.py --analyze    # TPR/FPR overall and per block, Wilson CIs, judgment, run_meta.json
"""
import argparse, builtins, contextlib, hashlib, json, math, os, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, run_battery  # noqa: E402

HALF = HERE.parent.parent
CARD_ID = "W4406880877"
MODEL = "o1-2024-12-17"
REPO = HALF / "external" / "repos" / CARD_ID / "jenna-russell__human_detectors"
DATA = REPO / "human_detectors.json"
PROMPT_FILE = REPO / "prompts" / "detector_prompts" / "classify_zero_shot_cot.txt"
REPO_COMMIT = "afcf03d14d2da4a038d8d0fafa5ec779dd858181"
RUNS = HALF / "runs" / CARD_ID
RUN = RUNS / "baseline_alive"
CHECK_JSON = RUNS / "environment_check.json"
TIERB = HALF / "runs" / "tierb" / CARD_ID

CAP = 45.0                      # decision 2026-09-19, per-paper cap
SEED = 42                       # models.ChatGPT.obtain_response(seed=42)
N_SEEDS = 1                     # decision 2026-09-19 (o1 pricing; the paper ran once)
PRICE = {"input": 15.0, "output": 60.0}                  # harness/pricing.json, o1-2024-12-17
GOLD_AI, GOLD_HUMAN = "AI-generated", "Human-written"    # release strings (README says 'Machine-generated')
LABEL_AI = "AI-GENERATED"
# Table 2 column order (paper) vs release order of generation_model
BLOCKS = [("gpt-4o", "GPT-4O"), ("claude", "CLAUDE"), ("paraphrased_gpt-4o", "GPT-4O PARAPHRASED"),
          ("o1-pro", "O1-PRO"), ("humanized_o1-pro", "O1-PRO HUMANIZED")]
ORIGINAL = {"tpr": {"gpt-4o": 83.3, "claude": 53.3, "paraphrased_gpt-4o": 96.7, "o1-pro": 20.0, "humanized_o1-pro": 16.7},
            "fpr": {"gpt-4o": 6.7, "claude": 3.3, "paraphrased_gpt-4o": 3.3, "o1-pro": 3.3, "humanized_o1-pro": 3.3},
            "overall": {"tpr": 54.0, "fpr": 4.0}, "counts": {"tpr_k": 81, "fpr_k": 6, "n": 150, "n_block": 30},
            "expert_majority_vote": {"tpr": 99.3, "fpr": 0.0},
            "source": "Table 2, section (C), Detector LLM O1-2024-12-17, row ZERO-SHOT + COT"}
GRADIENT_MIN_PP = 20.0          # 'well below': paper gap is 83.3 - 20.0 = 63.3 points
EXPERT_MARGIN_PP = 20.0         # 'far below the expert majority vote 99.3'
FPR_BLOWOUT = 20.0              # an FPR above this means the TPR was bought by over-calling AI
TIERB_TPR = 54.666666666666664  # runs/tierb/W4406880877/result_sha_matched.json (82/150)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------------- the authors' code, imported
@contextlib.contextmanager
def repo_context():
    """models.Detector.__init__ opens 'prompts/...' by RELATIVE path and without an encoding. chdir into the repo and
    default open() to UTF-8: on a non-UTF-8 locale (this machine: cp949) prompts/detection_guide.txt otherwise raises
    UnicodeDecodeError. UTF-8 is what the authors' Linux default gave them; no repository file is modified."""
    cwd, _open = os.getcwd(), builtins.open

    def uopen(file, mode="r", *a, **kw):
        if "b" not in mode and "encoding" not in kw:
            kw["encoding"] = "utf-8"
        return _open(file, mode, *a, **kw)
    sys.path.insert(0, str(REPO))
    os.chdir(str(REPO))
    builtins.open = uopen
    try:
        yield
    finally:
        builtins.open = _open
        os.chdir(cwd)
        if sys.path and sys.path[0] == str(REPO):
            sys.path.pop(0)


class _StubLLM:
    """Stands in for models.LLM so Detector.detect runs the authors' prompt rendering and parsing with NO API call."""

    def __init__(self, *a, **kw):
        self.reply, self.prompt = "", None

    def generate(self, prompt, **kw):
        self.prompt = prompt
        return self.reply


_DET = None


def detector():
    """models.Detector(explain=True, guide=False) -> the ZERO-SHOT + COT path (detect.py --no_guide)."""
    global _DET
    if _DET is None:
        if not PROMPT_FILE.exists():
            sys.exit(f"missing {PROMPT_FILE} (clone jenna-russell/human_detectors at {REPO_COMMIT[:8]})")
        with repo_context():
            import models                                           # torch/transformers/anthropic per requirements.txt
            models.LLM = _StubLLM
            _DET = models.Detector(llm=MODEL, explain=True, api_key="offline-stub", guide=False)
    return _DET


def render_and_parse(article, reply=""):
    """Authors' Detector.detect: renders classify_zero_shot_cot.format(article), 'calls' the stub, parses the reply."""
    det = detector()
    det.llm.reply = reply
    answer, explanation = det.detect(article)
    return det.llm.prompt, answer, explanation


def body_for(prompt):
    """models.ChatGPT.obtain_response, o1 branch: seed only; no temperature, max_tokens or reasoning_effort."""
    return {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "seed": SEED}


# -------------------------------------------------------------------------------------------------- data
def load_articles():
    if not DATA.exists():
        sys.exit(f"missing {DATA}")
    d = json.loads(DATA.read_text(encoding="utf-8"))
    items = []
    for k in sorted(d, key=int):                                    # release order; the dict key is the unique id
        r = d[k]
        items.append({"key": k, "article": r["article"], "gold": r["ground_truth"], "block": r["generation_model"],
                      "prompt_id": r["prompt_id"], "source": r.get("source"), "expert_majority": r.get("expert_majority_vote")})
    assert len(items) == 300, len(items)
    cnt = Counter((i["block"], i["gold"]) for i in items)
    for b, _ in BLOCKS:
        assert cnt[(b, GOLD_AI)] == 30 and cnt[(b, GOLD_HUMAN)] == 30, (b, cnt[(b, GOLD_AI)], cnt[(b, GOLD_HUMAN)])
    assert len({i["article"] for i in items}) == 300
    return items


# --------------------------------------------------------------------------------------------- statistics
def wilson(k, n, z=1.959963984540054):
    """Wilson score 95% interval in percent (deterministic; for n=150 it matches an item bootstrap to <1 pp)."""
    if n == 0:
        return [float("nan"), float("nan")]
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * max(0.0, c - h), 4), round(100 * min(1.0, c + h), 4)]


def rate(k, n):
    return {"k": k, "n": n, "pct": round(100 * k / n, 4) if n else None, "ci95": wilson(k, n)}


def judge(tpr, fpr, tpr_block):
    """Card judgment (ANALYSIS_PLAN Sec. 1 as instantiated): survival = overall TPR inside the original's 95% CI AND
    the behaviour holds (far below the expert majority vote; evasion blocks well below the clean blocks) AND no FPR
    blow-out. Partial = level or FPR moves but the evasion gradient survives. Death = the gradient disappears."""
    clean = [tpr_block["gpt-4o"]["pct"], tpr_block["paraphrased_gpt-4o"]["pct"]]
    evade = [tpr_block["o1-pro"]["pct"], tpr_block["humanized_o1-pro"]["pct"]]
    gradient = (min(clean) - max(evade)) >= GRADIENT_MIN_PP
    below_experts = tpr["pct"] <= ORIGINAL["expert_majority_vote"]["tpr"] - EXPERT_MARGIN_PP
    orig_ci = wilson(ORIGINAL["counts"]["tpr_k"], ORIGINAL["counts"]["n"])
    inside = orig_ci[0] <= tpr["pct"] <= orig_ci[1]
    fpr_ok = fpr["pct"] <= FPR_BLOWOUT
    why = {"evasion_gradient_pp": round(min(clean) - max(evade), 2), "gradient_holds": gradient,
           "far_below_expert_majority_vote": below_experts, "original_tpr_ci95": orig_ci,
           "tpr_inside_original_ci": inside, "fpr_no_blowout": fpr_ok,
           "original_fpr_ci95": wilson(ORIGINAL["counts"]["fpr_k"], ORIGINAL["counts"]["n"])}
    if not gradient or not below_experts:
        return "사망 (dead)", why
    return ("생존 (survived)" if (inside and fpr_ok) else "부분 생존 (partial)"), why


# ------------------------------------------------------------------------------------------------ --check
def tierb_replies():
    """Archived Tier B calls -> {dict key: reply}. The Tier B items carried duplicate ids (triage 2026-09-09), so each
    call is re-paired with its own article by the candidate text carried inside the request body."""
    p = TIERB / "calls.jsonl"
    if not p.exists():
        return {}, "missing"
    by_article = {i["article"]: i["key"] for i in load_articles()}
    out, unmatched = {}, 0
    for line in p.open(encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") != 200:
            continue
        content = r["request"]["messages"][0]["content"]
        start, end = content.find("<start of candidate text>"), content.find("</end of candidate text>")
        art = content[start + len("<start of candidate text>"):end] if start >= 0 and end > start else None
        key = by_article.get(art)
        if key is None:
            unmatched += 1
            continue
        out[key] = {"reply": (r["response"]["choices"][0]["message"].get("content") or ""), "usage": r["response"]["usage"],
                    "chars": len(content), "cost_usd": r.get("cost_usd", 0.0)}
    return out, unmatched


def token_fit(replies):
    """Least-squares prompt_tokens ~ a + b * len(prompt chars) over the Tier B calls, plus the mean completion length."""
    xs = [v["chars"] for v in replies.values()]
    ys = [v["usage"]["prompt_tokens"] for v in replies.values()]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    outs = [v["usage"]["completion_tokens"] for v in replies.values()]
    outs_sorted = sorted(outs)
    return {"in_per_char": b, "in_intercept": my - b * mx, "out_mean": sum(outs) / n, "out_max": max(outs),
            "out_p95": outs_sorted[int(0.95 * (n - 1))], "n_calls": n,
            "measured_cost_per_call": sum(v["cost_usd"] for v in replies.values()) / n}


def check(verbose=True):
    items = load_articles()
    raw = PROMPT_FILE.read_bytes()
    det = detector()
    prompt_tpl = det.classify_zero_shot_cot
    sample = next(i for i in items if i["gold"] == GOLD_AI)
    prompt, _, _ = render_and_parse(sample["article"])
    body = body_for(prompt)

    replies, unmatched = tierb_replies()
    by_key = {i["key"]: i for i in items}
    per_block, answers, unparsed, no_desc, hits = {b: [0, 0] for b, _ in BLOCKS}, Counter(), 0, 0, 0
    for key, rec in replies.items():
        it = by_key[key]
        _, ans, expl = render_and_parse(it["article"], rec["reply"])
        answers[str(ans)] += 1
        unparsed, no_desc = unparsed + (ans is None), no_desc + (expl is None)
        ai = (ans or "").strip().upper() == LABEL_AI
        hits += ai
        per_block[it["block"]][0] += ai
        per_block[it["block"]][1] += 1
    tpr_b = {b: rate(*per_block[b]) for b, _ in BLOCKS}
    overall = rate(hits, sum(v[1] for v in per_block.values())) if replies else rate(0, 0)
    fit = token_fit(replies) if replies else None
    reproduced = bool(replies) and abs(overall["pct"] - TIERB_TPR) < 0.01     # overall['pct'] is rounded to 4 dp

    summary = {
        "card_id": CARD_ID, "checked_utc": now(), "model": MODEL, "python": sys.version.split()[0],
        "repository": {"path": str(REPO), "commit": REPO_COMMIT, "license": "MIT (Copyright 2025 Jenna Russell)",
                       "code_used": "models.Detector (prompt rendering + <answer>/<description> parsing) imported, driven by a stub LLM; no API call"},
        "dataset": {"file": str(DATA), "n": len(items), "n_ai": sum(i["gold"] == GOLD_AI for i in items),
                    "n_human": sum(i["gold"] == GOLD_HUMAN for i in items), "gold_strings": sorted({i["gold"] for i in items}),
                    "block_counts": {b: {"ai": 30, "human": 30, "paper_column": lbl} for b, lbl in BLOCKS},
                    "release_block_order": list(dict.fromkeys(i["block"] for i in items)),
                    "paper_column_order": [b for b, _ in BLOCKS],
                    "keyed_by": "dict key '0'-'299' (unique); the record's own 'id' field is NOT unique",
                    "article_chars": {"ai_mean": round(sum(len(i["article"]) for i in items if i["gold"] == GOLD_AI) / 150, 1),
                                      "human_mean": round(sum(len(i["article"]) for i in items if i["gold"] == GOLD_HUMAN) / 150, 1)}},
        "prompt": {"file": str(PROMPT_FILE), "sha256_working_tree_bytes": hashlib.sha256(raw).hexdigest(),
                   "sha256_as_loaded_lf": sha(prompt_tpl), "bytes_on_disk": len(raw), "chars_as_loaded": len(prompt_tpl),
                   "working_tree_eol": "CRLF (git checkout; index is LF)", "loaded_contains_cr": "\r" in prompt_tpl,
                   "placeholders": prompt_tpl.count("{}"), "template": prompt_tpl},
        "example_request": {"item_key": sample["key"], "gold": sample["gold"], "block": sample["block"],
                            "body": body, "sha256_body": hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
                            "prompt_chars": len(prompt)},
        "tierb_reparse": {"run_dir": str(TIERB), "calls_matched": len(replies), "calls_unmatched": unmatched,
                          "matched_by": "candidate text carried in the archived request body (the Tier B item ids were not unique)",
                          "parser": "repository models.Detector.detect (strict <answer>(.*?)</answer>, re.DOTALL, .strip())",
                          "answers": dict(answers), "unparsed": unparsed, "replies_without_description": no_desc,
                          "tpr_overall": overall, "tpr_by_block": tpr_b, "tierb_reported_tpr": TIERB_TPR,
                          "reproduces_tierb": reproduced,
                          "paper_tpr_by_block": ORIGINAL["tpr"], "paper_tpr_overall": ORIGINAL["overall"]["tpr"],
                          "note": "Tier B sent a Table 20 transcription with reasoning_effort medium, max_completion_tokens 4096 and no seed; "
                                  "this re-parse only re-reads those replies with the repository's parser"},
        "cost_calibration": fit, "paper": ORIGINAL,
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    CHECK_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    if verbose:
        d = summary["dataset"]
        print(f"\n[{CARD_ID} --check] dataset {DATA.name}: {d['n']} articles, {d['n_ai']} AI / {d['n_human']} human, "
              f"gold strings {d['gold_strings']}; 5 blocks x (30 AI + 30 human)\n"
              f"  release block order {d['release_block_order']}\n"
              f"  Table 2 column order {d['paper_column_order']}  (the two middle columns are swapped w.r.t. the release)\n"
              f"  prompt {PROMPT_FILE.name}: {len(raw)} bytes on disk (CRLF checkout), {len(prompt_tpl)} chars as loaded "
              f"(LF, CR present: {summary['prompt']['loaded_contains_cr']}), one '{{}}' slot; sha256(loaded) {sha(prompt_tpl)[:16]}\n"
              f"  one exact request (item {sample['key']}, {sample['block']}, {sample['gold']}): "
              f"{json.dumps({k: v for k, v in body.items() if k != 'messages'})}, 1 user message, {len(prompt)} chars, "
              f"sha256(body) {summary['example_request']['sha256_body'][:16]}\n"
              f"    prompt head: {prompt[:96]!r}\n    prompt tail: {prompt[-88:]!r}\n"
              f"  Tier B re-parse with the repository parser: {len(replies)} calls matched ({unmatched} unmatched), "
              f"answers {dict(answers)}, unparsed {unparsed}, replies without <description> {no_desc}")
        print(f"  {'block':22s}{'TPR ours':>10s}{'paper':>8s}   n")
        for b, lbl in BLOCKS:
            print(f"  {lbl:22s}{tpr_b[b]['pct']:10.1f}{ORIGINAL['tpr'][b]:8.1f}   {tpr_b[b]['n']}")
        print(f"  {'OVERALL':22s}{overall['pct']:10.2f}{ORIGINAL['overall']['tpr']:8.1f}   {overall['n']}   "
              f"-> Tier B reported {TIERB_TPR:.2f}: {'reproduced' if reproduced else 'MISMATCH'}")
        if fit:
            print(f"  calibration from {fit['n_calls']} Tier B calls: prompt_tokens ~ {fit['in_per_char']:.5f}*chars + {fit['in_intercept']:.1f}; "
                  f"completion mean {fit['out_mean']:.0f} (p95 {fit['out_p95']}, max {fit['out_max']}); ${fit['measured_cost_per_call']:.4f}/call")
        print(f"  -> {CHECK_JSON}")
    return summary


# --------------------------------------------------------------------------------------------- requests
def build_requests(items=None, n_seeds=N_SEEDS):
    items = items or load_articles()
    reqs = []
    for s in range(n_seeds):
        for it in items:
            prompt, _, _ = render_and_parse(it["article"])
            reqs.append({"id": it["key"], "seed_idx": s,
                         "meta": {"key": it["key"], "gold": it["gold"], "block": it["block"], "prompt_id": it["prompt_id"],
                                  "arm": "baseline_alive", "prompt_chars": len(prompt)},
                         "body": body_for(prompt)})
    return reqs


def calibrated(reqs, fit):
    tin = sum(fit["in_per_char"] * len(r["body"]["messages"][0]["content"]) + fit["in_intercept"] for r in reqs)
    tout = fit["out_mean"] * len(reqs)
    return {"calls": len(reqs), "tokens_in": int(round(tin)), "tokens_out": int(round(tout)),
            "usd": tin / 1e6 * PRICE["input"] + tout / 1e6 * PRICE["output"],
            "usd_p95_out": tin / 1e6 * PRICE["input"] + fit["out_p95"] * len(reqs) / 1e6 * PRICE["output"]}


def dry_run(cap, n_seeds):
    reqs = build_requests(n_seeds=n_seeds)
    RUN.mkdir(parents=True, exist_ok=True)
    path = RUN / "requests.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for r in reqs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    replies, _ = tierb_replies()
    fit = token_fit(replies) if replies else None
    est = run_battery(reqs, RUN, cap, dry_run=True, label=CARD_ID)
    c = calibrated(reqs, fit) if fit else None
    print(f"[dry-run] {len(reqs)} requests ({len(reqs) // n_seeds} articles x {n_seeds} seed(s)); "
          f"body = model/messages/seed {SEED} only (no temperature, max_tokens or reasoning_effort)\n"
          f"[dry-run] battery's generic estimate (chars/4 in, 60 out): ~${est['est_usd']:.2f} - far too low for a reasoning model")
    if c:
        print(f"[dry-run] calibrated on {fit['n_calls']} archived Tier B o1 calls: {c['tokens_in']:,} in + {c['tokens_out']:,} out tokens "
              f"-> ~${c['usd']:.2f} (${PRICE['input']}/{PRICE['output']} per 1M); p95-output worst case ~${c['usd_p95_out']:.2f}; cap ${cap:.0f}\n"
              f"[dry-run] cross-check, measured Tier B ${fit['measured_cost_per_call']:.4f}/call x {len(reqs)} = ~${fit['measured_cost_per_call'] * len(reqs):.2f}")
    print(f"[dry-run] -> {path}")
    return {"calls": len(reqs), "battery_est_usd": est["est_usd"], "calibrated": c}


def run(cap, n_seeds, workers):
    reqs = build_requests(n_seeds=n_seeds)
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "run_config.json").write_text(json.dumps({
        "card_id": CARD_ID, "model": MODEL, "n_items": len(reqs) // n_seeds, "n_seeds": n_seeds, "calls": len(reqs),
        "api_seed": SEED, "temperature": None, "max_tokens": None, "reasoning_effort": None,
        "params_source": "models.ChatGPT.obtain_response o1 branch; reasoning_effort unset -> API default 'medium' (footnote 22)",
        "prompt_source": f"{PROMPT_FILE.relative_to(HALF).as_posix()} @ {REPO_COMMIT[:8]}", "cap_usd": cap, "built_utc": now(),
        "decisions": "decisions_2026_09_19 in harness/cards/W4406880877.json"}, indent=2), encoding="utf-8")
    run_battery(reqs, RUN, cap, workers=workers, label=CARD_ID)


# -------------------------------------------------------------------------------------------- --analyze
def analyze():
    res = load_results(RUN)
    if not res:
        print(f"no archived calls in {RUN}; run --run first")
        return None
    items = {i["key"]: i for i in load_articles()}
    budget = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    cfg = json.loads((RUN / "run_config.json").read_text(encoding="utf-8")) if (RUN / "run_config.json").exists() else {}

    per_seed, answers, served, fps, finish = {}, Counter(), set(), set(), Counter()
    unparsed, prompt_mismatch, tok_in, tok_out = 0, 0, 0, 0
    for (rid, sidx), rec in res.items():
        it = items.get(rid)
        if it is None:
            continue
        reply = ((rec["response"] or {}).get("choices") or [{}])[0].get("message", {}).get("content") or ""
        prompt, ans, _ = render_and_parse(it["article"], reply)
        prompt_mismatch += prompt != rec["request"]["messages"][0]["content"]
        answers[str(ans)] += 1
        unparsed += ans is None
        served.add(rec.get("model_served"))
        fps.add(rec.get("system_fingerprint"))
        finish[((rec["response"] or {}).get("choices") or [{}])[0].get("finish_reason")] += 1
        u = (rec["response"] or {}).get("usage") or {}
        tok_in += u.get("prompt_tokens", 0)
        tok_out += u.get("completion_tokens", 0)
        per_seed.setdefault(sidx, {}).setdefault(it["block"], {}).setdefault(it["gold"], []).append(
            (ans or "").strip().upper() == LABEL_AI)

    def aggregate(seed_rows):
        tpr_b = {b: rate(sum(seed_rows.get(b, {}).get(GOLD_AI, [])), len(seed_rows.get(b, {}).get(GOLD_AI, []))) for b, _ in BLOCKS}
        fpr_b = {b: rate(sum(seed_rows.get(b, {}).get(GOLD_HUMAN, [])), len(seed_rows.get(b, {}).get(GOLD_HUMAN, []))) for b, _ in BLOCKS}
        tpr = rate(sum(v["k"] for v in tpr_b.values()), sum(v["n"] for v in tpr_b.values()))
        fpr = rate(sum(v["k"] for v in fpr_b.values()), sum(v["n"] for v in fpr_b.values()))
        return {"tpr": tpr, "fpr": fpr, "tpr_by_block": tpr_b, "fpr_by_block": fpr_b}

    seeds = {s: aggregate(rows) for s, rows in sorted(per_seed.items())}
    primary = seeds[sorted(seeds)[len(seeds) // 2]]                 # median seed (1 seed by decision)
    complete = primary["tpr"]["n"] == 150 and primary["fpr"]["n"] == 150
    label, why = judge(primary["tpr"], primary["fpr"], primary["tpr_by_block"]) if complete else ("미판정 (incomplete)", {})
    if not complete:
        label += f" [{primary['tpr']['n']}/150 AI, {primary['fpr']['n']}/150 human replies archived]"

    frictions = [
        "the released record's own 'id' field is not unique (61 distinct values for 150 articles); items are keyed on the dict index '0'-'299' instead - "
        "the Tier B run mis-paired 89 replies before the responses were re-matched by request hash",
        "models.Detector.__init__ opens the prompt files by relative path and without an encoding: the adapter chdirs into the repository and defaults "
        "open() to UTF-8, without which prompts/detection_guide.txt raises UnicodeDecodeError on a non-UTF-8 locale",
        "models.py imports torch, transformers and anthropic at module level although the OpenAI detector path uses none of them (~25 s import)",
        "the repository ships no scoring script: TPR/FPR aggregation per Table 2 block is ours",
        "the release gold strings are 'AI-generated' / 'Human-written'; the README example and the Tier B config say 'Machine-generated'",
        "helpers.model_call in the same repository hard-codes reasoning_effort='high' for o1, contradicting footnote 22; that path is not the detector path "
        "and models.py sends no reasoning_effort at all (API default 'medium')",
        "a reply without an <answer> tag yields None in the authors' parser; such a reply is not a label and is reported separately, not folded into "
        "HUMAN-WRITTEN (the Tier B runner folded it)",
    ]
    if prompt_mismatch:
        frictions.append(f"{prompt_mismatch} archived requests do not re-render byte-identically from the repository prompt")
    if budget.get("stopped_at_cap"):
        frictions.append(f"the run stopped at the ${budget.get('cap_usd')} cap")
    if budget.get("errors"):
        frictions.append(f"{budget['errors']} calls failed at the HTTP level and are not in the archive")

    meta = {
        "card_id": CARD_ID, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
        "target_paper": {"title": "People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text",
                         "doi": "10.48550/arxiv.2501.15654", "repo": "https://github.com/jenna-russell/human_detectors",
                         "repo_commit": REPO_COMMIT, "repo_license": "MIT",
                         "original_source": ORIGINAL["source"], "original_values": ORIGINAL},
        "generation": {"model_requested": MODEL, "model_served": sorted(x for x in served if x), "n_fingerprints": len(fps),
                       "endpoint": "POST https://api.openai.com/v1/chat/completions (raw HTTPS, harness/openai_client.py)",
                       "parameters": f"one user message; seed {SEED}; no temperature, no max_tokens, no reasoning_effort "
                                     f"(models.ChatGPT.obtain_response o1 branch; API default reasoning effort 'medium' = footnote 22)",
                       "prompt_template_source": f"{PROMPT_FILE.relative_to(HALF).as_posix()} @ {REPO_COMMIT[:8]}, loaded and formatted by models.Detector",
                       "parser": "models.Detector.detect: re.search(r'<answer>(.*?)</answer>', re.DOTALL).strip(); None when the tag is missing",
                       "battery": f"{len(res)} archived calls in {RUN.name}/calls.jsonl; {len(seeds)} seed(s) x 300 articles",
                       "run_config": cfg, "budget_cap_usd": budget.get("cap_usd", cfg.get("cap_usd", CAP))},
        "results": {"reexecution": {"primary_seed": sorted(seeds)[len(seeds) // 2], "per_seed": seeds,
                                    "answers": dict(answers), "unparsed": unparsed,
                                    "prompt_rerender_mismatches": prompt_mismatch,
                                    "ci_method": "Wilson score 95% (n=150 overall, n=30 per block)"},
                    "original": ORIGINAL,
                    "comparison": {"tpr_delta_pp": round(primary["tpr"]["pct"] - ORIGINAL["overall"]["tpr"], 3) if complete else None,
                                   "fpr_delta_pp": round(primary["fpr"]["pct"] - ORIGINAL["overall"]["fpr"], 3) if complete else None,
                                   "tpr_by_block_delta_pp": {b: round(primary["tpr_by_block"][b]["pct"] - ORIGINAL["tpr"][b], 2) for b, _ in BLOCKS} if complete else None,
                                   "fpr_by_block_delta_pp": {b: round(primary["fpr_by_block"][b]["pct"] - ORIGINAL["fpr"][b], 2) for b, _ in BLOCKS} if complete else None,
                                   "tierb_tpr_ai_half": TIERB_TPR, **why},
                    "cost_usd": round(budget.get("cost_usd", tok_in / 1e6 * PRICE["input"] + tok_out / 1e6 * PRICE["output"]), 3),
                    "calls": budget.get("calls", len(res)), "errors": budget.get("errors", 0),
                    "call_log_stats": {"http_200": len(res), "finish_reasons": dict(finish), "tokens_in": budget.get("tokens_in", tok_in),
                                       "tokens_out": budget.get("tokens_out", tok_out)},
                    "judgment": label,
                    "judged_by": "automatic rule per ANALYSIS_PLAN Sec. 1 as the card instantiates it: survived = overall TPR inside the original's "
                                 f"95% CI AND at least {EXPERT_MARGIN_PP:.0f} pp below the expert majority vote ({ORIGINAL['expert_majority_vote']['tpr']}) "
                                 f"AND the evasion blocks at least {GRADIENT_MIN_PP:.0f} pp below the clean blocks AND FPR <= {FPR_BLOWOUT:.0f}; "
                                 "partial = level or FPR moves while the gradient holds; dead = the gradient disappears; human double-coding pending",
                    "note": (f"TPR {primary['tpr']['pct']:.2f} [{primary['tpr']['ci95'][0]:.1f}, {primary['tpr']['ci95'][1]:.1f}] "
                             f"({primary['tpr']['k']}/150) vs paper {ORIGINAL['overall']['tpr']}; FPR {primary['fpr']['pct']:.2f} "
                             f"[{primary['fpr']['ci95'][0]:.1f}, {primary['fpr']['ci95'][1]:.1f}] ({primary['fpr']['k']}/150) vs paper "
                             f"{ORIGINAL['overall']['fpr']}; evasion gradient {why.get('evasion_gradient_pp')} pp; unparsed {unparsed}"
                             if complete else "incomplete run")},
        "reproducibility_frictions_observed": frictions,
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUN / "result.json").write_text(json.dumps({"per_seed": seeds, "judgment": label, "comparison": meta["results"]["comparison"]},
                                                indent=2, ensure_ascii=False), encoding="utf-8")
    (RUNS / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[{CARD_ID} --analyze] {len(res)} calls; served {sorted(x for x in served if x)}; ${meta['results']['cost_usd']}; unparsed {unparsed}")
    print(f"  {'block':22s}{'TPR':>8s}{'(paper)':>9s}{'FPR':>8s}{'(paper)':>9s}")
    for b, lbl in BLOCKS:
        print(f"  {lbl:22s}{primary['tpr_by_block'][b]['pct']:8.1f}{ORIGINAL['tpr'][b]:9.1f}"
              f"{primary['fpr_by_block'][b]['pct']:8.1f}{ORIGINAL['fpr'][b]:9.1f}")
    print(f"  {'OVERALL':22s}{primary['tpr']['pct']:8.2f}{ORIGINAL['overall']['tpr']:9.1f}{primary['fpr']['pct']:8.2f}{ORIGINAL['overall']['fpr']:9.1f}")
    print(f"  judgment: {label}\n  -> {RUNS / 'run_meta.json'}")
    return meta


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="offline: data, prompt, one exact request, Tier B re-parse")
    ap.add_argument("--dry-run", action="store_true", help="build the 300 requests and estimate cost (no API calls)")
    ap.add_argument("--run", action="store_true", help="execute the battery (paid API calls, capped)")
    ap.add_argument("--analyze", action="store_true", help="TPR/FPR, judgment, run_meta.json")
    ap.add_argument("--cap", type=float, default=CAP, help=f"USD cap for --run (default {CAP:g})")
    ap.add_argument("--seeds", type=int, default=N_SEEDS, help=f"repeats per article (default {N_SEEDS})")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if not any((a.check, a.dry_run, a.run, a.analyze)):
        ap.print_help()
        return
    if a.check:
        check()
    if a.dry_run:
        dry_run(a.cap, a.seeds)
    if a.run:
        run(a.cap, a.seeds, a.workers)
    if a.analyze:
        analyze()


if __name__ == "__main__":
    main()
