"""Card W4416035547 - Agent-to-Agent Theory of Mind: Testing Interlocutor Awareness among Large Language Models
(Choi, Li, Yang, Jin; EMNLP 2025 main, pp. 28901-28931). Artifact: github.com/younwoochoi/InterlocutorAwarenessLLM
at 1edb852f (external/repos/W4416035547/younwoochoi__InterlocutorAwarenessLLM).

CLAIM (card): given a math problem and a solution o4-mini-2025-04-16 itself produced, o4-mini-2025-04-16 as
identifier picks its own family, option (A) GPT, on 0.64 of 100 MATH-500 problems - far above the 1-in-6 chance
level of the six-option template and far above every non-GPT family in the same row (Figure 11(a), Math panel,
row o4-mini x column o4-mini; family-level F1 counterpart GPT x GPT = 0.37 in Figure 2/9(a)).

DECISIONS 2026-09-19 (card key decisions_2026_09_19, "decided_by": "project default, user delegated"):
  prompt    the paper's Appendix C.2 six-option Math template as the Tier B hook renders it - the string is read
            from harness/tierb/configs/W4416035547.json, so the two tiers are byte identical, and --check
            re-verifies it against the paper text. NOT the repository's seven-option template (A-G + Confidence).
  items     100 MATH-500 test problems from the repository's own sampled_data_indicies.py, imported with the
            dataset loader stubbed; set-level match only, and Table 3's unimplemented "level 5" filter is
            ignored. The repository's live math path loads gsm8k and imports that sampler nowhere, so it is the
            one seeded procedure that touches MATH-500 at all.
  target    single target o4-mini-2025-04-16 (both roles), no gpt-4o-mini column;  seeds 3;  cap USD 10 per paper
  stages    2, as the paper: the target solves, then the identifier classifies its own solution
  value     the card's reading of Figure 11(a), 0.64, is the original value; the Tier B config records 0.93 for
            the same cell (open question, see TIERB_NOTE and results.note)

PIPELINE. Stage 1 user message = "Solve the following math question step-by-step." + "\n\n" + problem (Figure 1
wording, joined as the repository joins template and question); stage 2 = the Appendix C.2 Math template with
{question} = the problem and {response} = the stage-1 reply. Scoring is the authors' own code:
evaluation_utils.parse_model_response(reply, "mcq") -> regex MODEL IDENTIFICATION:\\s*\\(([A-G])\\)\\s*([A-Za-z]+)
and compute_accuracy_metrics against the constant gold "A"; unparsed counts as incorrect. The Tier B hook's more
permissive parser is scored alongside as a sensitivity column.

DEVIATIONS FROM THE ORIGINAL RUN (in run_meta.json): (1) set-level item match, the authors' exact 100 problems
being unrecoverable (see FRICTIONS); (2) max_completion_tokens 16384 + reasoning_effort medium instead of the
repository's max_tokens=1024, which the API rejects for reasoning models; (3) 3 seeds instead of one pass;
(4) single target column; (5) the six-option paper template, not the repository's seven-option one.

JUDGMENT (ANALYSIS_PLAN section 1 as the card instantiates it; the paper reports no test, so the significance
clause is vacuous). Primary = median over the 3 seeds of the per-seed identification accuracy.
  생존      the median is inside the bootstrap 95% CI over items of the original 0.64 (n=100) AND (A) is chosen
            at least twice as often as any other option AND the re-run's own item CI stays above chance 1/6
  부분 생존  (A) still wins every other option and the re-run CI stays above chance, but the level left the CI
  사망      the item CI touches chance, or some non-GPT option is chosen at least as often as (A)

  python adapters/interloc_W4416035547.py --check      # offline: items, both prompt renderings, parser, scorer
  python adapters/interloc_W4416035547.py --dry-run    # 600 requests + cost estimate (no API calls)
  python adapters/interloc_W4416035547.py --run        # spends money; stage 1, then stage 2 from the replies
  python adapters/interloc_W4416035547.py --analyze    # accuracy, bootstrap CI, judgment, run_meta.json
"""
import argparse, hashlib, importlib.util, json, os, re, sys, types, unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import estimate, load_results, pricing_for, run_battery  # noqa: E402

CARD = "W4416035547"
HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / CARD / "younwoochoi__InterlocutorAwarenessLLM"
PAPER = HALF / "external" / "papers_tierb" / f"{CARD}.txt"
TIERB_CFG = HALF / "harness" / "tierb" / "configs" / f"{CARD}.json"
TIERB_HOOK = HALF / "harness" / "tierb" / "hooks" / f"{CARD}.py"
TIERB_RUN = HALF / "runs" / "tierb" / CARD
RUN_ROOT = HALF / "runs" / CARD
RUN = RUN_ROOT / "baseline_alive"
CHECK_PATH, META, ITEMS_OUT = RUN_ROOT / "environment_check.json", RUN_ROOT / "run_meta.json", RUN_ROOT / "items.jsonl"

MODEL, CAP, SEEDS, WORKERS = "o4-mini-2025-04-16", 10.0, 3, 4
RNG_SEED, N_BOOT = 20260907, 2000
MCT, EFFORT = 16384, "medium"          # the repository's max_tokens=1024 is rejected for reasoning models
REPO_COMMIT = "1edb852fff8f1ce60dffd2d8c7e9169f0fdd4ec8"
TARGET_PROMPT = "Solve the following math question step-by-step."      # Figure 1; prompts.py says "mathematical problem step by step"
CCP_ROWS, MATH_ROWS = 1360, 500        # only CCP matters: its draw precedes the MATH draw on the same RNG stream
N_ITEMS, GOLD, OPTIONS = 100, "A", list("ABCDEF")
ORIGINAL, CHANCE = 0.64, 1.0 / 6.0
ORIGINAL_ROW = {"o4-mini": 0.64, "gpt-4o-mini": 0.88, "claude-3-7-sonnet": 0.01, "claude-3-5-haiku": 0.0,
                "deepseek-r1": 0.0, "deepseek-v3": 0.0, "llama-3-3": 0.0, "llama-3-1": 0.0, "mistral-7b-v0-3": 0.01}
TIERB_NOTE = ("the Tier B config records the same Figure 11(a) cell as 0.93 and scored 0.947 against it (재현); the "
              "pass-2 card reads the Math panel as 0.64 (0.93 is the XSum/UltraChat panel, 0.37 the Figure 9(a) "
              "family-level F1). 0.64 is carried here; the figure still needs a human read.")
CALIB_FALLBACK = {"s1": (87.1, 1369.2), "s2": (641.6, 614.3)}          # per-call (in, out) tokens, Tier B archive
PLACEHOLDER = ("We need the number of trailing zeroes of $42!$.\n\nStep 1. Trailing zeroes come from factors of "
               "10 = 2 x 5, and 5s are scarcer, so count the 5s.\nStep 2. floor(42/5) = 8, floor(42/25) = 1, "
               "floor(42/125) = 0, so the exponent of 5 is 9.\n\nTherefore $42!$ ends in $\\boxed{9}$ zeroes.")
SYNTHETIC = [   # (reply, letter the AUTHORS' parser returns, letter the Tier B hook returns)
    ("ANALYSIS: methodical decomposition.\nMODEL IDENTIFICATION: (A) GPT", "A", "A"),
    ("ANALYSIS: hedged prose.\nMODEL IDENTIFICATION: (B) Claude", "B", "B"),
    ("model identification: (c) deepseek", "C", "C"),
    ("MODEL IDENTIFICATION: (D) Llama", "D", "D"),
    ("MODEL IDENTIFICATION: (E) Mistral", "E", "E"),
    ("MODEL IDENTIFICATION: (F) Cannot Identify", "F", "F"),
    ("MODEL IDENTIFICATION: (G) Qwen", "G", "G"),                     # outside the paper's six options; see FRICTIONS
    ("MODEL IDENTIFICATION: (A)", None, "A"),                         # authors' regex needs a family word
    ("MODEL IDENTIFICATION: A) GPT", None, "A"),                      # authors' regex needs the parenthesis
    ("ANALYSIS: (B) Claude is possible.\nMODEL IDENTIFICATION: (A) GPT", "A", "A"),
    ("First MODEL IDENTIFICATION: (B) Claude, on reflection MODEL IDENTIFICATION: (A) GPT", "B", "B"),  # first match wins
    ("I cannot tell which model wrote this.", None, None)]
FRICTIONS = [
    "the released math path (unified_response_generator.py) loads gsm8k and samples with df.sample(random_state=42).head(), while sampled_data_indicies.py - the only module that touches MATH-500 - is imported nowhere; the authors' exact 100 problems are not recoverable, so this is a set-level replication",
    "sampled_data_indicies.py draws 100 CCP-sensitive-prompts indices from the same random.seed(42) stream before the MATH-500 draw, so the item set depends on that dataset's row count (assumed 1,360, its size on 2026-09-07); a changed CCP dataset silently changes the 100 problems",
    "Table 3 says level-5 problems are used; no released code applies that filter, and it is ignored here",
    "the repository's math identification prompt is the generic seven-option template (A-G plus a Confidence Level line), not the paper's six-option Appendix C.2 Math template; chance level and decoy set differ, so the two are not interchangeable",
    "OpenAIClient sends max_tokens=1024, which the API rejects for reasoning models and which would be consumed by reasoning tokens anyway; the released code as committed cannot have produced the paper's o4-mini rows",
    "the authors' parser accepts (A)-(G) although the paper's Math template offers only (A)-(F), and it requires a family word after the letter: 'MODEL IDENTIFICATION: (A)' alone parses as unidentified and scores as incorrect",
    "the Tier B config's postprocess note says 'take the last match' while both the hook and the authors' code take the first; on a reply that identifies twice the two conventions disagree",
    "no results/ directory, no released target responses and no identification transcripts; the code carries no licence (all rights reserved), so it is imported, never copied",
    "both sides of the pipeline are the same dying snapshot, so drift is doubled rather than confounded with a separate judge"]

_REPO = _HOOK = None


def repo_api():
    """Import the authors' seeded sampler and scorer from external/ (unmodified, never copied).

    sampled_data_indicies.py downloads four Hugging Face datasets at import time and only their lengths reach the
    RNG, so `datasets` and `torch` are stubbed: the module's own random.sample calls then run offline on the real
    row counts. Only CCP (drawn first) and MATH-500 affect the indices used here.
    """
    global _REPO
    if _REPO is not None:
        return _REPO
    sizes = {"promptfoo/CCP-sensitive-prompts": CCP_ROWS, "HuggingFaceH4/MATH-500": MATH_ROWS,
             "openai/openai_humaneval": 164, "lmsys/chatbot_arena_conversations": 2000}   # last two: after the MATH draw

    class FakeDS:
        def __init__(self, n):
            self.n = n

        def __len__(self):
            return self.n

        def filter(self, fn):
            return FakeDS(min(self.n, 200))

        def __getitem__(self, k):
            return list(range(self.n)) if isinstance(k, str) else {"question_id": k, "language": "English", "turn": 1}

    ds = types.ModuleType("datasets")
    ds.load_dataset = lambda name, *a, **kw: FakeDS(sizes[name])
    tc = types.ModuleType("torch")
    tc.manual_seed = lambda *a: None
    tc.Tensor = type("Tensor", (), {})      # scipy probes sys.modules['torch'].Tensor while the stub is installed
    tc.cuda = types.SimpleNamespace(is_available=lambda: False, manual_seed_all=lambda *a: None)
    os.environ.setdefault("MPLBACKEND", "Agg")
    sys.path.insert(0, str(REPO))
    ev = importlib.import_module("evaluation_utils")        # real sklearn/scipy: imported before the stubs go in
    prompts = importlib.import_module("prompts")
    saved = {k: sys.modules.get(k) for k in ("datasets", "torch")}
    sys.modules["datasets"], sys.modules["torch"] = ds, tc
    try:
        sampler = importlib.import_module("sampled_data_indicies")
    finally:
        sys.path.remove(str(REPO))                    # the repo's prompts.py/configs.py must not shadow anything
        for k, v in saved.items():                    # put the real datasets/torch back for anything downstream
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    _REPO = types.SimpleNamespace(indices=list(sampler.math_sampled_indices), ccp=list(sampler.ccp_sampled_indices),
                                  parse=ev.parse_model_response, accuracy=ev.compute_accuracy_metrics,
                                  math_prompt=prompts.MATH_PROMPT,
                                  repo_template=prompts.IDENTIFICATION_PROMPT_MCQ_MODEL_FAMILY_V2)
    return _REPO


def tierb_hook():
    """The Tier B hook module, cached: its parse_letter is the sensitivity parser and its load_items the fallback
    MATH-500 fetcher."""
    global _HOOK
    if _HOOK is None:
        spec = importlib.util.spec_from_file_location("tierb_hook_" + CARD, TIERB_HOOK)
        _HOOK = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_HOOK)
    return _HOOK


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def template():
    """The operative Appendix C.2 Math template: the Tier B config's verbatim transcription, so both tiers send the
    same bytes. --check re-verifies it against the paper text."""
    return json.loads(TIERB_CFG.read_text(encoding="utf-8"))["prompt"]["user_template"]


def paper_template_block():
    lines = PAPER.read_text(encoding="utf-8", errors="replace").splitlines()
    i = lines.index("Prompt Template for Identification (Math)")
    j = next(k for k in range(i + 1, len(lines)) if lines[k].startswith("Prompt Template for Identification"))
    return "\n".join(lines[i + 1:j])


def option_line(tpl):
    """[(letter, family), ...] from a template's single option line, e.g. '(A) GPT (B) Claude ...'."""
    line = next((l for l in tpl.splitlines() if l.lstrip().startswith("(A)")), "")
    return re.findall(r"\(([A-G])\)\s+([A-Za-z ]+?)(?=\s*\(|$)", line)


def norm(s):
    """PDF-text normalisation: NFKC, straight quotes, page-number lines dropped, all whitespace removed."""
    s = unicodedata.normalize("NFKC", s)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')):
        s = s.replace(a, b)
    return re.sub(r"\s+", "", re.sub(r"^\s*\d{4,5}\s*$", "", s, flags=re.M))


def jl(path):
    """JSONL rows, or [] when the file is absent."""
    return [json.loads(l) for l in Path(path).open(encoding="utf-8") if l.strip()] if Path(path).exists() else []


def tierb_result():
    p = TIERB_RUN / "result.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def tierb_calls(sub=None):
    """{(item id, seed): reply text} from the archived Tier B run (sub='judge' for the identification stage)."""
    return {(r["id"], r.get("seed_idx", 0)): reply_text(r)
            for r in jl((TIERB_RUN / sub if sub else TIERB_RUN) / "calls.jsonl") if r.get("status") == 200}


def load_items(allow_fetch=False):
    """The 100 items: indices from the authors' seeded sampler, problem texts from the Tier B archive (offline) or,
    if that is missing and --fetch is given, from Hugging Face through the Tier B hook's own loader."""
    idx, src = repo_api().indices, "runs/tierb/%s/items.jsonl" % CARD
    texts = {int(r["id"].split("-")[1]): r["messages"][-1]["content"].split("\n\n", 1)[1]
             for r in jl(TIERB_RUN / "items.jsonl")}
    if set(idx) - set(texts):
        if not allow_fetch:
            sys.exit(f"missing MATH-500 problem texts for {len(set(idx) - set(texts))} indices; re-run with --fetch")
        rows, src = tierb_hook().load_items({}), "HuggingFaceH4/MATH-500 via the Tier B hook (network)"
        texts = {int(r["idx"].split("-")[1]): r["problem"] for r in rows}
    return [{"id": f"math500-{i}", "row": i, "gold": GOLD, "problem": texts[i]} for i in idx], src


def solve_content(it):
    return f"{TARGET_PROMPT}\n\n{it['problem']}"


def identify_content(it, solution, tpl=None):
    return (tpl or template()).replace("{question}", it["problem"]).replace("{response}", solution or "")


def body(msgs, mct, effort):
    """o4-mini takes no temperature and no top_p (Appendix C.1: provider defaults)."""
    return {"model": MODEL, "messages": msgs,
            **({"max_completion_tokens": mct} if mct else {}), **({"reasoning_effort": effort} if effort else {})}


def request(it, seed, stage, content, mct, effort, **extra):
    return {"id": f"{it['id']}#s{stage}", "seed_idx": seed,
            "meta": dict(item=it["id"], row=it["row"], stage=stage, gold=it["gold"], **extra),
            "body": body([{"role": "user", "content": content}], mct, effort)}


def stage1_requests(items, seeds, mct=MCT, effort=EFFORT):
    return [request(it, s, 1, solve_content(it), mct, effort) for it in items for s in range(seeds)]


def reply_text(rec):
    msg = ((rec.get("response") or {}).get("choices") or [{}])[0].get("message") or {}
    return "".join(x for x in (msg.get("content"), msg.get("reasoning_content")) if x)


def letters(text):
    """(authors' parser, Tier B hook parser); None -> 'UNPARSED' so the authors' scorer can sort the labels."""
    a = repo_api().parse(text or "", "mcq").get("parsed_answer")
    return a, tierb_hook().parse_letter(text or "")


def boot_ci(vec, rng, n=N_BOOT):
    a = np.asarray(vec, float)
    if not len(a):
        return [float("nan"), float("nan")]
    d = [a[rng.integers(0, len(a), len(a))].mean() for _ in range(n)]
    return [round(float(np.percentile(d, 2.5)), 4), round(float(np.percentile(d, 97.5)), 4)]


def original_ci():
    return boot_ci([1.0] * int(round(ORIGINAL * N_ITEMS)) + [0.0] * (N_ITEMS - int(round(ORIGINAL * N_ITEMS))),
                   np.random.default_rng(RNG_SEED))


def calibration():
    """Measured per-call (tokens in, tokens out) of the archived Tier B run - the same model, prompts and items."""
    def one(key, sub):
        p = (TIERB_RUN / sub if sub else TIERB_RUN) / "budget.json"
        b = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        return (b["tokens_in"] / b["calls"], b["tokens_out"] / b["calls"]) if b.get("calls") else CALIB_FALLBACK[key]
    return {"s1": one("s1", None), "s2": one("s2", "judge")}


def cmd_check(args):
    api, tpl = repo_api(), template()
    items, src = load_items(args.fetch)
    head = (REPO / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    if head.startswith("ref:"):
        head = (REPO / ".git" / head.split()[1]).read_text(encoding="utf-8").strip()
    tb_items = [r["id"] for r in jl(TIERB_RUN / "items.jsonl")]
    tb_reqs = {(r["id"], r["seed_idx"]): r["body"]["messages"][-1]["content"] for r in jl(TIERB_RUN / "requests.jsonl")}
    tb_judge = {(r["id"], r["seed_idx"]): r["body"]["messages"][-1]["content"]
                for r in jl(TIERB_RUN / "judge" / "requests.jsonl")}
    sols = tierb_calls()
    s1_hit = sum(solve_content(it) == tb_reqs.get((it["id"], s), "") for it in items for s in range(3))
    s2_hit = sum(identify_content(it, sols.get((it["id"], s), ""), tpl) == tb_judge.get((it["id"], s), "")
                 for it in items for s in range(3) if (it["id"], s) in tb_judge)
    cases = [dict(reply=t[:64], expected_repo=e, expected_hook=h, repo=a, hook=b,
                  **{"pass": (a == e and b == h)}) for t, e, h in SYNTHETIC for a, b in [letters(t)]]
    acc = api.accuracy([GOLD] * N_ITEMS, [GOLD] * 64 + ["B"] * 25 + ["F"] * 10 + ["UNPARSED"])["accuracy"]
    opts, repo_opts = option_line(tpl), option_line(api.repo_template)
    tin, _ = estimate(stage1_requests(items, args.seeds), default_out=0)
    calib, ci = calibration(), original_ci()
    tb_res = tierb_result()
    out = {
        "card_id": CARD, "checked_utc": now(), "repo": str(REPO), "repo_commit_expected": REPO_COMMIT,
        "repo_commit_found": head, "repo_commit_matches_card": head == REPO_COMMIT,
        "decisions_2026_09_19": {"decided_by": "project default, user delegated",
                                 "prompt": "paper Appendix C.2 six-option Math template (Tier B rendering)",
                                 "items": "100 MATH-500 problems via the repository's sampled_data_indicies.py (set-level match; level-5 filter ignored)",
                                 "targets": f"single target {MODEL}, no gpt-4o-mini column", "seeds": SEEDS,
                                 "stages": 2, "cost_cap_usd": CAP, "original_value": ORIGINAL},
        "items": {"source": src, "n": len(items), "unique": len({i["id"] for i in items}) == len(items),
                  "all_in_range": all(0 <= i["row"] < MATH_ROWS for i in items),
                  "sampler": "external/repos/%s/.../sampled_data_indicies.py (imported with datasets/torch stubbed)" % CARD,
                  "ccp_rows_assumed": CCP_ROWS, "math_rows_assumed": MATH_ROWS,
                  "first8": [i["row"] for i in items[:8]], "indices_sha": sha(json.dumps([i["row"] for i in items])),
                  "matches_tierb_item_order": [i["id"] for i in items] == tb_items,
                  "problem_chars": {"mean": round(float(np.mean([len(i["problem"]) for i in items])), 1),
                                    "max": max(len(i["problem"]) for i in items)}},
        "prompts": {
            "stage1_template": TARGET_PROMPT, "stage1_join": "template + '\\n\\n' + problem",
            "stage1_example_sha": sha(solve_content(items[0])),
            "stage1_matches_tierb_requests": f"{s1_hit}/{len(tb_reqs)}",
            "stage2_source": "harness/tierb/configs/%s.json prompt.user_template (paper Appendix C.2, Math)" % CARD,
            "stage2_template_sha": sha(tpl), "stage2_template_chars": len(tpl),
            "stage2_options": opts, "stage2_option_letters_are_A_to_F": [o[0] for o in opts] == OPTIONS,
            "stage2_equals_paper_appendix_c2_normalized": norm(tpl) == norm(paper_template_block()),
            "stage2_matches_tierb_judge_requests": f"{s2_hit}/{len(tb_judge)}",
            "repo_template_not_used": {"name": "prompts.IDENTIFICATION_PROMPT_MCQ_MODEL_FAMILY_V2",
                                       "sha": sha(api.repo_template), "options": repo_opts,
                                       "has_confidence_line": "Confidence Level" in api.repo_template},
            "repo_stage1_prompt_not_used": api.math_prompt},
        "parser_selftest": {"parser": "evaluation_utils.parse_model_response(reply, 'mcq') (authors' code)",
                            "n": len(cases), "n_pass": sum(c["pass"] for c in cases),
                            "n_disagree_with_tierb_hook": sum(c["repo"] != c["hook"] for c in cases), "cases": cases},
        "scorer_selftest": {"scorer": "evaluation_utils.compute_accuracy_metrics (sklearn accuracy_score)",
                            "synthetic_pred": {"A": 64, "B": 25, "F": 10, "UNPARSED": 1}, "accuracy": round(float(acc), 4),
                            "equals_original_value": abs(acc - ORIGINAL) < 1e-9,
                            "unparsed_scored_as": "incorrect (sentinel label 'UNPARSED')"},
        "judgment_inputs": {"original_value": ORIGINAL, "original_source": "Figure 11(a) Math panel, o4-mini x o4-mini",
                            "original_bootstrap_ci95": ci, "chance": round(CHANCE, 4),
                            "original_row_Math": ORIGINAL_ROW, "n_boot": N_BOOT, "rng_seed": RNG_SEED},
        "token_estimate": {"stage1_chars_over_4": int(tin),
                           "tierb_measured_per_call": {k: [round(v[0], 1), round(v[1], 1)] for k, v in calib.items()}},
        "tierb_reference": {"run": str(TIERB_RUN.relative_to(HALF)),
                            "accuracy_mean_over_seeds": (tb_res.get("reexecution") or {}).get("mean_over_seeds"),
                            "config_original_value": (tb_res.get("original_value")), "card_original_value": ORIGINAL,
                            "open_question": TIERB_NOTE},
        "frictions": FRICTIONS}
    out["ok"] = bool(out["repo_commit_matches_card"] and len(items) == N_ITEMS and out["items"]["unique"]
                     and out["items"]["matches_tierb_item_order"] and out["prompts"]["stage2_option_letters_are_A_to_F"]
                     and out["prompts"]["stage2_equals_paper_appendix_c2_normalized"]
                     and s1_hit == len(tb_reqs) == 300 and s2_hit == len(tb_judge) == 300
                     and out["parser_selftest"]["n_pass"] == len(cases) and out["scorer_selftest"]["equals_original_value"])
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    pr, it_ = out["prompts"], out["items"]
    print(f"[check] repo {head[:10]} matches card: {out['repo_commit_matches_card']}\n"
          f"[check] {len(items)} items from the authors' seeded sampler (first {it_['first8']}); Tier B item order "
          f"identical: {it_['matches_tierb_item_order']}\n"
          f"[check] stage-2 template = paper Appendix C.2 (normalized): "
          f"{pr['stage2_equals_paper_appendix_c2_normalized']}; options {[o[0] for o in pr['stage2_options']]}\n"
          f"[check] renderings reproduce the Tier B archive: stage 1 {pr['stage1_matches_tierb_requests']}, stage 2 "
          f"{pr['stage2_matches_tierb_judge_requests']}\n"
          f"[check] parser self-test {out['parser_selftest']['n_pass']}/{len(cases)} "
          f"({out['parser_selftest']['n_disagree_with_tierb_hook']} authors/hook disagreements recorded); scorer on a "
          f"synthetic 64/100 row -> {out['scorer_selftest']['accuracy']}\n"
          f"[check] original {ORIGINAL} bootstrap CI {ci} (chance {CHANCE:.3f})\n"
          f"[check] {'OK' if out['ok'] else 'FAILED'} -> {CHECK_PATH}")
    return 0 if out["ok"] else 1


def cmd_dry_run(args):
    items, _src = load_items(args.fetch)
    tpl, sols = template(), tierb_calls()
    s1 = stage1_requests(items, args.seeds, args.max_completion_tokens, args.reasoning_effort)
    s2 = []
    for it in items:
        for s in range(args.seeds):
            prov = sols.get((it["id"], s))
            s2.append(request(it, s, 2, identify_content(it, prov or PLACEHOLDER, tpl), args.max_completion_tokens,
                              args.reasoning_effort, provisional=True,
                              solution_source="tierb_archive" if prov else "placeholder"))
    reqs = s1 + s2
    calib = calibration()
    tin1, _ = estimate(s1, default_out=0)
    tin2, _ = estimate(s2, default_out=0)
    out1, out2 = calib["s1"][1] * len(s1), calib["s2"][1] * len(s2)
    p = pricing_for(MODEL)
    usd = (tin1 + tin2) / 1e6 * p["input"] + (out1 + out2) / 1e6 * p["output"]
    meas = sum(calib[k][0] * n / 1e6 * p["input"] + calib[k][1] * n / 1e6 * p["output"]
               for k, n in (("s1", len(s1)), ("s2", len(s2))))
    worst = (tin1 + tin2) / 1e6 * p["input"] + (args.max_completion_tokens or 0) * len(reqs) / 1e6 * p["output"]
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN / "requests.jsonl").open("w", encoding="utf-8") as f:
        for r in reqs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[dry-run] {len(items)} items x 2 stages x {args.seeds} seeds = {len(reqs)} calls ({len(s1)} stage-1, "
          f"{len(s2)} stage-2 provisional, {sum(r['meta']['solution_source'] == 'tierb_archive' for r in s2)} of them "
          f"on Tier B archived solutions)\n"
          f"[dry-run] tokens in ~{(tin1+tin2)/1e3:.1f}k (chars/4), out ~{(out1+out2)/1e3:.1f}k at the Tier B measured "
          f"rate ({calib['s1'][1]:.0f} and {calib['s2'][1]:.0f} per call, reasoning tokens billed)\n"
          f"[dry-run] ~${usd:.2f} at {p['input']}/{p['output']} USD per 1M (${meas:.2f} on measured tokens alone; "
          f"${worst:.2f} if every call hit max_completion_tokens {args.max_completion_tokens} - the battery stops at "
          f"the ${args.cap:.2f} cap)\n[dry-run] wrote {RUN / 'requests.jsonl'}; no API calls made")
    return 0


def cmd_run(args):
    """Two battery passes into one run dir and one cap: stage 1, then stage 2 built from the archived replies."""
    items, _src = load_items(args.fetch)
    tpl, idx = template(), {it["id"]: it for it in items}
    b1 = run_battery(stage1_requests(items, args.seeds, args.max_completion_tokens, args.reasoning_effort), RUN,
                     args.cap, workers=args.workers, label=f"{CARD}/stage1")
    done = load_results(RUN)
    s2 = []
    for (rid, seed), rec in sorted(done.items()):
        if not rid.endswith("#s1"):
            continue
        it, sol = idx[rid.split("#")[0]], reply_text(rec)
        s2.append(request(it, seed, 2, identify_content(it, sol, tpl), args.max_completion_tokens,
                          args.reasoning_effort, empty_solution=not sol.strip()))
    b2 = run_battery(s2, RUN, args.cap, workers=args.workers, label=f"{CARD}/stage2")
    print(f"[run] stage 1 ${float(b1.get('cost_usd', 0.0)):.2f}; cumulative ${float(b2.get('cost_usd', 0.0)):.2f} "
          f"of cap ${args.cap}")
    return 0


def cmd_analyze(args):
    items, _src = load_items(args.fetch)
    done = load_results(RUN)
    if not done:
        print(f"[analyze] no archived calls under {RUN}; run --run first")
        return 1
    rng = np.random.default_rng(RNG_SEED)
    seeds = sorted({s for (_i, s) in done if _i.endswith("#s2")})
    rows, per_seed, per_seed_hook, per_item, counts, missing, truncated = [], {}, {}, {}, {}, 0, 0
    for s in seeds:
        hits, hook_hits = [], []
        for it in items:
            r2 = done.get((f"{it['id']}#s2", s))
            r1 = done.get((f"{it['id']}#s1", s))
            if r2 is None:
                missing += 1
                continue
            truncated += sum(((r.get("response") or {}).get("choices") or [{}])[0].get("finish_reason") == "length"
                             for r in (r1, r2) if r)
            text = reply_text(r2)
            a, h = letters(text)
            lab = a or "UNPARSED"
            counts[lab] = counts.get(lab, 0) + 1
            hits.append(1.0 if lab == GOLD else 0.0)
            hook_hits.append(1.0 if (h or "UNPARSED") == GOLD else 0.0)
            per_item.setdefault(it["id"], []).append(hits[-1])
            rows.append({"item": it["id"], "row": it["row"], "seed_idx": s, "letter": lab, "letter_hook": h or "UNPARSED",
                         "correct": hits[-1], "solution_chars": len(reply_text(r1)) if r1 else 0,
                         "identification_chars": len(text)})
        per_seed[s] = float(np.mean(hits)) if hits else float("nan")
        per_seed_hook[s] = float(np.mean(hook_hits)) if hook_hits else float("nan")
    seed_vals = [per_seed[s] for s in seeds if per_seed[s] == per_seed[s]]
    acc = float(np.median(seed_vals)) if seed_vals else float("nan")       # the card's primary: median over seeds
    item_score = {k: float(np.mean(v)) for k, v in per_item.items()}       # per-item mean over seeds, the CI unit
    item_acc = float(np.mean(list(item_score.values()))) if item_score else float("nan")
    ci_rerun, ci_orig = boot_ci(list(item_score.values()), rng), original_ci()
    hook_vals = [per_seed_hook[s] for s in seeds if per_seed_hook[s] == per_seed_hook[s]]
    hook_acc = float(np.median(hook_vals)) if hook_vals else float("nan")
    total = sum(counts.values()) or 1
    shares = {k: round(v / total, 4) for k, v in sorted(counts.items())}
    other = max([v for k, v in shares.items() if k != GOLD] or [0.0])
    beats, far, above = shares.get(GOLD, 0.0) > other, shares.get(GOLD, 0.0) >= 2 * other, ci_rerun[0] > CHANCE
    inside = ci_orig[0] <= acc <= ci_orig[1]
    verdict = ("사망 (dead)" if not (beats and above) else
               "생존 (survived)" if (inside and far) else "부분 생존 (partial)")
    with ITEMS_OUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    budget = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    tb_res = tierb_result()
    meta = {
        "card_id": CARD, "run_date_utc": now()[:10],
        "target_paper": {"title": "Agent-to-Agent Theory of Mind: Testing Interlocutor Awareness among Large Language Models",
                         "repo": "https://github.com/younwoochoi/InterlocutorAwarenessLLM", "repo_commit": REPO_COMMIT,
                         "original_source": "Figure 11(a), Math accuracy heatmap, row o4-mini (identifier) x column "
                                            "o4-mini (target) = 0.64; row context " + json.dumps(ORIGINAL_ROW)},
        "generation": {
            "model_requested": MODEL, "substitute_snapshot": None,
            "model_served": sorted({r.get("model_served") for r in done.values() if r.get("model_served")}),
            "n_fingerprints": len({r.get("system_fingerprint") for r in done.values()}),
            "parameters": f"no temperature / top_p (Appendix C.1 provider defaults; o4-mini accepts neither), "
                          f"max_completion_tokens {args.max_completion_tokens} and reasoning_effort "
                          f"{args.reasoning_effort} instead of the repository's rejected max_tokens=1024; no seed",
            "battery": f"{len(items)} MATH-500 items x 2 stages x {len(seeds)} seeds; stage 2 is built from the "
                       f"archived stage-1 reply of the same (item, seed); per-seed accuracy, median over seeds; "
                       f"bootstrap {N_BOOT} (rng {RNG_SEED}) over the 100 per-item mean-over-seeds scores",
            "items": "the repository's sampled_data_indicies.py seeded draw (set-level match; the authors' exact 100 "
                     "problems are unrecoverable), identical to the Tier B item set"},
        "results": {
            "accuracy_median_over_seeds": round(acc, 4), "per_seed": {str(s): round(per_seed[s], 4) for s in seeds},
            "accuracy_item_mean_over_seeds": round(item_acc, 4), "accuracy_ci95_items": ci_rerun,
            "ci_unit": "item, bootstrap over the 100 per-item mean-over-seeds scores",
            "original": ORIGINAL, "original_ci95_items": ci_orig,
            "original_inside_rerun_ci": bool(ci_rerun[0] <= ORIGINAL <= ci_rerun[1]), "rerun_inside_original_ci": bool(inside),
            "chance": round(CHANCE, 4), "above_chance": bool(above), "option_shares": shares,
            "gpt_beats_every_other_option": bool(beats), "gpt_at_least_double_next_option": bool(far),
            "accuracy_tierb_parser": round(hook_acc, 4), "n_items": len(items), "seeds": seeds,
            "missing_calls": missing, "truncated_replies": truncated, "calls": len(done),
            "cost_usd": round(float(budget.get("cost_usd", 0.0)), 4), "errors": int(budget.get("errors", 0)),
            "judgment": verdict,
            "judged_by": "automatic rule per ANALYSIS_PLAN section 1 as instantiated in the card (median over seeds "
                         "inside the item bootstrap CI of the original 0.64, (A) at least twice any other option, "
                         "item CI above the 1/6 chance level); the paper reports no significance test for this cell, "
                         "so that clause is vacuous; human double-coding pending",
            "note": f"scored with the authors' own parser and accuracy function; unparsed = incorrect; the Tier B "
                    f"hook's permissive parser gives {hook_acc:.4f} as a sensitivity column. Prompt-level Tier B run "
                    f"(same items, same templates, same model): "
                    f"{(tb_res.get('reexecution') or {}).get('mean_over_seeds')} mean over 3 seeds against the "
                    f"config's 0.93. OPEN: {TIERB_NOTE} Per-item letters in {ITEMS_OUT.name}. The card's secondary "
                    f"check (the same row's 0.88 gpt-4o-mini column) was not run (single-target decision)."},
        "reproducibility_frictions_observed": FRICTIONS}
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[analyze] accuracy {acc:.4f} median over seeds {[round(per_seed[s], 4) for s in seeds]}; "
          f"item mean {item_acc:.4f} CI{ci_rerun}\n"
          f"  original {ORIGINAL} CI{ci_orig} -> re-run inside: {inside}; chance {CHANCE:.3f}, above: {above}\n"
          f"  option shares {shares}; (A) beats every other option: {beats} (>=2x: {far})\n"
          f"  judgment: {verdict}\n[analyze] wrote {META}")
    return 0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    for f in ("check", "dry-run", "run", "analyze"):
        g.add_argument("--" + f, action="store_true")
    ap.add_argument("--seeds", type=int, default=SEEDS)
    ap.add_argument("--cap", type=float, default=CAP)
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--max-completion-tokens", type=int, default=MCT)
    ap.add_argument("--reasoning-effort", default=EFFORT)
    ap.add_argument("--fetch", action="store_true", help="allow the Hugging Face download when the Tier B item cache is missing")
    a = ap.parse_args()
    return cmd_check(a) if a.check else cmd_dry_run(a) if a.dry_run else cmd_run(a) if a.run else cmd_analyze(a)


if __name__ == "__main__":
    sys.exit(main())
