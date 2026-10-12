"""Card W4407012395 - MedXpertQA: Benchmarking Expert-Level Medical Reasoning and Understanding
(Zuo, Qu, Li, Chen, Zhu, Hua, Zhang, Ding, Zhou; ICML 2025, PMLR 267; arXiv 2501.18362v3). Artifact:
TsinghuaC3I/MedXpertQA at f53877b (external/repos/W4407012395/TsinghuaC3I__MedXpertQA, MIT). The authors'
own eval/ code is imported, never copied: config.PromptTemplates (prompt + answer trigger), utils.answer_cleansing
(parser) and main.set_correctness (scorer).

CLAIM (card, paper Table 5): on the seed-42 10% sample of MedXpertQA Text (244 items = 186 Reasoning + 58
Understanding, 10 options each) o1-2024-12-17 with zero-shot CoT reaches 44.67% (R 46.24 / U 39.66), the best of
the 18 evaluated models and above the pre-licensed expert baseline 42.60, while o3-mini-2025-01-31 reaches 37.30%
(37.63 / 36.21). Printed values are exact integer counts on those n (--check recovers 86/23/109 and 70/21/91).

DECISIONS 2026-09-19 (card block decisions_2026_09_19, decided_by "project default, user delegated"):
  scope Text only; the MM subset (199 items, Table 4's 56.28) is NOT run (user_check 2). seeds o1 x1 (~$42) and
  o3-mini x3 (~$9), the card's own cheaper alternative to 3x3 (user_check 1). rows the o3-mini row is a SECOND
  CLAIM ROW IN THIS CARD, judged separately, not a separate card (user_check 4). params the paper's own prompt and
  decoding settings, unchanged. logs item ids + model reply only (user_check 3). cap per-paper USD 60.

LOG POLICY / HOW THE REDACTION WORKS (Appendix A: "do not share any example of MedXpertQA online"). The question
text is needed on the wire and nowhere else, so it exists only in memory: --run builds every request from the local
dataset at call time (requests.jsonl is never an input to --run); after each battery pass, in a finally so an
interrupt is covered, redact_calls() rewrites baseline_alive/calls.jsonl in place (tmp + os.replace) - the stage-1
user text becomes REDACTED and the record gains prompt_sha256 / prompt_chars, while the battery's own sha_request
(hash of the TRUE wire body) is left untouched, so anyone holding the MIT dataset can rebuild and verify it. The
assistant turn is the MODEL's text and is KEPT: it is what the claim is about. --dry-run writes requests.jsonl
already redacted and --check writes only redacted prompts, so no file this adapter writes holds a question.

PROTOCOL (eval/main.py zero_shot_cot + eval/config/prompt_templates.py; paper Appendix G.3 prints this exact
rendering for item Text-20 = row 0 of the sampled file, which --check matches verbatim):
  stage 1  user {"content": [{"type":"text","text":"Q: <question, incl. 'Answer Choices: (A) ... (J) ...'>\\n
           A: Let's think step by step."}]}  <- content-parts list even for text-only items, as the repo sends it
  stage 2  same user turn + assistant <stage-1 reply, stripped> + user "Therefore, among A through J, the answer is"
  system   "You are a helpful medical assistant." is DROPPED for o1/o3-mini (api_agent.py filters role=system,
           paper C.2), so neither arm sends a system message
  params   max_completion_tokens 8192; seed = seed_idx (0 = the original's seed=0); NO temperature (C.2:
           unsupported for these two), no top_p, no logprobs. 2 calls x 244 items x seeds per arm.
  parsing  utils.answer_cleansing("zero_shot", trigger, reply, "medxpertqa_sampled", "text", item) -> first
           \\b[A-J]\\b after the trigger (fallback " answer is ", else the whole reply), then main.set_correctness
           against the single-letter label.

JUDGMENT (ANALYSIS_PLAN section 1 as the card instantiates it; the paper reports no significance test for these
rows, so that clause is vacuous). Per item: median over seeds. Band = binomial 95% CI of the PRINTED value at that
n (normal approx; +/-6.24 pp for 44.67 at n=244); the re-run bootstrap CI (2,000 draws, rng 20260907, item-level)
is reported alongside and both directions are recorded.
  o1 row       생존 acc in band AND o1 > o3-mini AND o1 > 42.60 | 부분 생존 in band and above o3-mini but no longer
               above the expert baseline | 사망 outside the band, or o1 <= o3-mini
  o3-mini row  생존 in band AND o3-mini < o1 | 부분 생존 in band, ordering broken | 사망 outside the band
  secondary    o1 Reasoning > Understanding (46.24 vs 39.66); per-seed spread is always printed.

  python adapters/medxpert_W4407012395.py --check      # offline, no API calls
  python adapters/medxpert_W4407012395.py --dry-run    # offline, writes the redacted request list
  python adapters/medxpert_W4407012395.py --run [--cap 60]     # SPENDS MONEY - not executed yet
  python adapters/medxpert_W4407012395.py --analyze
"""
import argparse, hashlib, json, math, os, sys, types
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import estimate, load_results, pricing_for, run_battery  # noqa: E402

CARD = "W4407012395"
HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / CARD / "TsinghuaC3I__MedXpertQA"
EVAL = REPO / "eval"
SAMPLED = EVAL / "data" / "medxpertqa_sampled" / "input" / "medxpertqa_sampled_text_input.jsonl"
SAMPLED_MM = EVAL / "data" / "medxpertqa_sampled" / "input" / "medxpertqa_sampled_mm_input.jsonl"
FULL = EVAL / "data" / "medxpertqa" / "input" / "medxpertqa_text_input.jsonl"
PAPER = HALF / "external" / "papers_tierb" / f"{CARD}.txt"
RUN_ROOT = HALF / "runs" / CARD
RUN = RUN_ROOT / "baseline_alive"
CHECK_PATH, META, ITEMS = RUN_ROOT / "environment_check.json", RUN_ROOT / "run_meta.json", RUN_ROOT / "items.jsonl"

REPO_COMMIT = "f53877b0d35b3c5526dfc0f899a2e902e0910c1d"
DATASET, TASK = "medxpertqa_sampled", "text"          # the repo's own dataset key / task name
MCT, CAP, WORKERS = 8192, 60.0, 4                     # max_completion_tokens as api_agent.py sets it for o-series
RNG_SEED, N_BOOT = 20260907, 2000
ARMS = [{"tag": "o1", "model": "o1-2024-12-17", "seeds": 1, "cap_share": 0.80},     # 48 / 12 of the 60 cap;
        {"tag": "o3mini", "model": "o3-mini-2025-01-31", "seeds": 3, "cap_share": 0.20}]  # estimates 39.5 / 8.7
ORIGINAL = {"o1-2024-12-17": {"Reasoning": 46.24, "Understanding": 39.66, "Avg": 44.67},
            "o3-mini-2025-01-31": {"Reasoning": 37.63, "Understanding": 36.21, "Avg": 37.30}}
EXPERT = {"Reasoning": 41.74, "Understanding": 45.44, "Avg": 42.60}   # Table 5, full Text set (not the sample)
N_SPLIT = {"Reasoning": 186, "Understanding": 58, "Avg": 244}
EXPECTED_OUT = {1: 2000, 2: 500}   # reasoning+visible tokens budgeted per stage; o-series bill reasoning as output
PLACEHOLDER_CHARS = 1600           # assumed visible stage-1 CoT, re-sent as the assistant turn of stage 2
PLACEHOLDER = ("The patient's presentation is consistent with the mechanism described in option B. "
               * 40)[:PLACEHOLDER_CHARS]   # written for this adapter; no MedXpertQA text is reproduced
REDACTED = ("[REDACTED MedXpertQA question text - the authors ask that no example be shared online "
            "(paper Appendix A); prompt_sha256 is kept and the text is rebuildable from the MIT dataset]")
PARSER_CASES = [   # (synthetic stage-2 reply, letter the AUTHORS' parser returns) - one per branch, plus quirks.
    ("The correct answer is (B), the second listed option.", "B"),      # No option or question text is reproduced:
    ("B", "B"),                                                         # these replies are written for this test.
    ("Therefore, among A through J, the answer is (D).", "D"),          # trigger echoed -> split on the trigger
    ("Answer: D. as explained above", "D"),                             # no trigger, no ' answer is '
    ("**(J)**", "J"),
    ("(F) is the best choice here", "F"),
    ("the answer is b", None),                                          # lowercase: \\b[A-J]\\b is case-sensitive
    ("No answer provided.", None),
    ("A patient with this presentation would most likely have (C).", "A"),   # quirk: the article 'A'
    ("I cannot determine the answer from the information given.", "I")]      # quirk: the pronoun 'I'
QUIRKS = ["utils.answer_cleansing extracts the FIRST case-sensitive \\b[A-J]\\b of the stage-2 reply, so the "
          "English words 'A' and 'I' are read as options A and I (a first-person refusal scores as I), while a "
          "lower-case letter yields no prediction at all (scored incorrect). Kept as released - it is the parser "
          "that produced Tables 4 and 5."]
FRICTIONS = [
    "per-question original outputs are not published (only leaderboard aggregates), so only aggregate accuracy is comparable; no item-level agreement with the original run can be computed",
    "paper Appendix A asks that no example be shared online, so this card's L1 archive stores item ids, hashes and model replies but not the question text (see LOG POLICY)",
    "the Expert (Pre-Licensed) row of Table 5 (42.60) is computed on the FULL Text set from aggregated examinee response distributions - it is not an integer item count and not the 244-item sample - yet the card's judgment compares o1's sampled accuracy against it directly",
    "eval/model/api_agent.py hard-codes an OpenAI-compatible proxy (api_key '[API_KEY]', base_url '[BASE_URL]'), so the published numbers were produced through a proxy of unknown routing; this re-run posts to api.openai.com directly",
    "the original run is a single pass (seed=0) and o-series ignore temperature, so the paper's own run-to-run spread is unknown; the seed parameter is sent as the original did, but OpenAI documents it as best-effort and reasoning models are not deterministic",
    "main.py's --temperature default of 0 is silently dropped for o1/o3-mini by api_agent.py; 'greedy decoding' in section 4.1 therefore does not apply to these two rows",
    "the repo sends the stage-1 user turn as a content-parts list even for text-only items; replicated here verbatim, but it cannot be exercised offline",
    "the sampled subsets ship in the repo without the seed-42 sampling script, so the 10% draw itself is not reproducible - it is taken as given (186/1861 and 58/589 of the full Text set)"] + QUIRKS

_API = None


def repo_api():
    """Import the authors' prompt builder, parser and scorer from external/ (unmodified, never copied).

    eval/main.py pulls in eval/model/api_agent.py -> `openai`, which this offline path never calls; if the SDK is
    absent it is stubbed so --check/--dry-run/--analyze keep working without it.
    """
    global _API
    if _API is not None:
        return _API
    try:
        import openai  # noqa: F401
        stubbed = False
    except ImportError:
        sys.modules["openai"] = m = types.ModuleType("openai")
        m.OpenAI = type("OpenAI", (), {"__init__": lambda s, **kw: None})
        stubbed = True
    sys.path.insert(0, str(EVAL))
    from config import PromptTemplates
    from main import set_correctness
    from utils import answer_cleansing
    tpl = PromptTemplates().load_templates(DATASET, ARMS[0]["model"])
    _API = types.SimpleNamespace(tpl=tpl, cleanse=answer_cleansing, correct=set_correctness,
                                 openai_stubbed=stubbed)
    return _API


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def load_items(path=SAMPLED):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def stage1_text(item):
    """eval/main.py zero_shot_cot stage 1: "Q: {question}\\nA: Let's think step by step."."""
    return repo_api().tpl.zero_shot_cot_prompt.format(question=item["question"].strip())


def trigger(item):
    """Stage-2 user turn; main.py formats the trigger with the item's own option range (A..J here)."""
    tpl = repo_api().tpl
    if len(item.get("options", [])) > 0 and "{start}" in tpl.zero_shot_ao_prompt:
        return tpl.zero_shot_cot_trigger.format(start=chr(65), end=chr(65 + len(item["options"]) - 1))
    return tpl.zero_shot_cot_trigger


def body(model, item, seed_idx, reply=None):
    """Stage-1 body when reply is None, else the stage-2 body. No system message (filtered for o1/o3-mini),
    no temperature (unsupported), seed as the original sent it."""
    msgs = [{"role": "user", "content": [{"type": "text", "text": stage1_text(item)}]}]
    if reply is not None:
        msgs += [{"role": "assistant", "content": (reply or "").strip()},
                 {"role": "user", "content": trigger(item)}]
    return {"model": model, "messages": msgs, "max_completion_tokens": MCT, "seed": seed_idx}


def request(arm, item, seed_idx, stage, reply=None):
    return {"id": f"{arm['tag']}|{item['id']}#s{stage}", "seed_idx": seed_idx,
            "meta": {"card": CARD, "arm": arm["tag"], "model": arm["model"], "item_id": item["id"], "stage": stage,
                     "question_type": item["question_type"], "medical_task": item["medical_task"],
                     "body_system": item["body_system"], "n_options": len(item["options"]),
                     "prompt_sha256": sha(stage1_text(item))},
            "body": body(arm["model"], item, seed_idx, reply)}


# ------------------------------------------------------------------ archive redaction (see LOG POLICY above)
def redact_body(b):
    """Replace the question-bearing text of message 0 in place; returns (sha256, chars) or None if already done."""
    c = b.get("messages", [{}])[0].get("content")
    part = c[0] if isinstance(c, list) and c else None
    txt = part.get("text", "") if part else (c if isinstance(c, str) else "")
    if not txt or txt.startswith("[REDACTED"):
        return None
    if part is not None:
        part["text"] = REDACTED
    else:
        b["messages"][0]["content"] = REDACTED
    return sha(txt), len(txt)


def redact_calls(run_dir=RUN):
    """Rewrite calls.jsonl without any question text (atomic tmp + os.replace). Idempotent; safe to re-run."""
    p = Path(run_dir) / "calls.jsonl"
    if not p.exists():
        return 0
    lines, n = [], 0
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        got = redact_body(rec.get("request", {}))
        if got:
            rec["prompt_sha256"], rec["prompt_chars"] = got
            rec["redacted"] = "stage-1 user text (MedXpertQA Appendix A); sha_request still hashes the true body"
            n += 1
        lines.append(json.dumps(rec, ensure_ascii=False))
    tmp = p.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, p)
    return n


def redacted_request(r):
    out = json.loads(json.dumps(r))
    got = redact_body(out["body"])
    if got:
        out["meta"]["prompt_sha256"], out["meta"]["prompt_chars"] = got
    return out


# ------------------------------------------------------------------ scoring
def score(item, reply):
    """The authors' own parser + scorer. Returns (letter or None, correct)."""
    api = repo_api()
    pred = api.cleanse("zero_shot", api.tpl.zero_shot_cot_trigger, reply or "", DATASET, TASK, item)
    label = item["label"] if isinstance(item["label"], list) else [item["label"]]
    return (pred[0] if pred else None), bool(api.correct(label, pred, DATASET, item))


def reply_text(rec):
    msg = ((rec.get("response") or {}).get("choices") or [{}])[0].get("message") or {}
    return "".join(x for x in (msg.get("content"), msg.get("reasoning_content")) if x)


def boot_ci(vals, rng):
    a = np.asarray(vals, float)
    if not len(a):
        return [float("nan"), float("nan")]
    d = a[rng.integers(0, len(a), (N_BOOT, len(a)))].mean(axis=1)
    return [round(float(np.percentile(d, 2.5)) * 100, 4), round(float(np.percentile(d, 97.5)) * 100, 4)]


def binom_band(pct, n):
    """Binomial 95% band of a PRINTED percentage at n items (normal approximation, as the card states)."""
    se = math.sqrt((pct / 100) * (1 - pct / 100) / n)
    return [round(pct - 1.96 * se * 100, 4), round(pct + 1.96 * se * 100, 4)]


def implied_counts():
    """Every printed Table 5 cell this card runs is an integer count on 186 / 58 / 244 items."""
    out = {}
    for model, vals in ORIGINAL.items():
        row = {s: {"printed": a, "n": N_SPLIT[s], "implied_correct": round(a / 100 * N_SPLIT[s]),
                   "recomputed": round(100 * round(a / 100 * N_SPLIT[s]) / N_SPLIT[s], 2)} for s, a in vals.items()}
        for s, c in row.items():
            c["exact"] = abs(c["recomputed"] - c["printed"]) < 0.005
        row["splits_sum_to_avg"] = (row["Reasoning"]["implied_correct"] + row["Understanding"]["implied_correct"]
                                    == row["Avg"]["implied_correct"])
        out[model] = row
    return out


def flatten(reqs):
    """battery.estimate() measures len(content), but our stage-1 content is the repo's parts LIST, so it is
    flattened to the equivalent plain string first: same messages, same formula, correct character count."""
    out = []
    for r in reqs:
        b = json.loads(json.dumps(r["body"]))
        for m in b["messages"]:
            m["content"] = "".join(p.get("text", "") for p in m["content"]) if isinstance(m["content"], list) else m["content"]
        out.append({"body": b})
    return out


def tiktoken_in(reqs):
    """Measured input tokens (o200k_base, 3 per message + 3 priming), or None if tiktoken is absent."""
    try:
        import tiktoken
    except ImportError:
        return None
    enc = tiktoken.get_encoding("o200k_base")
    return sum(3 + sum(3 + len(enc.encode(m["content"])) for m in r["body"]["messages"]) for r in flatten(reqs))


def token_estimate(arms=ARMS, items=None):
    """Input tokens measured with tiktoken (falling back to the battery's chars/4 estimator); output from the
    stated reasoning budget - the bodies carry max_completion_tokens 8192, which the estimator would otherwise
    take as the output figure and which is reported separately as the worst case."""
    items = items or load_items()
    out = {}
    for arm in arms:
        rows, tin, t4, tout, ceil_out = {}, 0, 0.0, 0.0, 0.0
        for stage in (1, 2):
            reqs = [request(arm, it, s, stage, PLACEHOLDER if stage == 2 else None)
                    for it in items for s in range(arm["seeds"])]
            c4, c = estimate(flatten(reqs))  # c = the max_completion_tokens ceiling, kept for the worst case
            tk = tiktoken_in(reqs)
            o = len(reqs) * EXPECTED_OUT[stage]
            rows[f"stage{stage}"] = {"calls": len(reqs), "tokens_in": int(tk if tk is not None else c4),
                                     "tokens_in_chars_over_4": int(c4), "tokens_out_expected": int(o),
                                     "tokens_out_budget_per_call": EXPECTED_OUT[stage]}
            tin, t4, tout, ceil_out = tin + rows[f"stage{stage}"]["tokens_in"], t4 + c4, tout + o, ceil_out + c
        p = pricing_for(arm["model"])
        out[arm["model"]] = {
            "arm": arm["tag"], "seeds": arm["seeds"], "calls": sum(r["calls"] for r in rows.values()),
            "tokens_in": int(tin), "tokens_in_method": "tiktoken o200k_base" if tiktoken_in([]) is not None
            else "battery chars/4", "tokens_in_chars_over_4": int(t4), "tokens_out_expected": int(tout),
            "by_stage": rows, "usd_per_1m": p,
            "usd_expected": round(tin / 1e6 * p["input"] + tout / 1e6 * p["output"], 2),
            "usd_ceiling_at_max_completion_tokens": round(tin / 1e6 * p["input"] + ceil_out / 1e6 * p["output"], 2)}
    return out


# ------------------------------------------------------------------ commands
def scorer_replay(items, rng):
    """End-to-end replay: seed each printed cell's implied number of correct items, synthesize the corresponding
    stage-2 replies, and push them through the AUTHORS' parser+scorer. Must return the printed Table 5 rows."""
    out = {}
    for model, vals in ORIGINAL.items():
        hits, acc = set(), {}
        for t in ("Reasoning", "Understanding"):
            ids = [i["id"] for i in items if i["question_type"] == t]
            hits |= set(rng.choice(ids, round(vals[t] / 100 * len(ids)), replace=False))
        for it in items:
            good = it["label"][0]
            bad = next(chr(65 + k) for k in range(10) if chr(65 + k) != good)
            _letter, ok = score(it, f"The correct answer is ({good if it['id'] in hits else bad}).")
            acc.setdefault(it["question_type"], []).append(ok)
            acc.setdefault("Avg", []).append(ok)
        scored = {k: round(100 * sum(v) / len(v), 2) for k, v in acc.items()}
        out[model] = {"seeded_correct": len(hits), "scored": scored, "printed": vals,
                      "matches_printed": all(abs(scored[k] - v) < 0.005 for k, v in vals.items())}
    return out


def cmd_check(args):
    api, items, full = repo_api(), load_items(), load_items(FULL)
    head = (REPO / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    if head.startswith("ref:"):
        head = (REPO / ".git" / head.split()[1]).read_text(encoding="utf-8").strip()
    typ = {t: sum(1 for i in items if i["question_type"] == t) for t in ("Reasoning", "Understanding")}
    ftyp = {t: sum(1 for i in full if i["question_type"] == t) for t in ("Reasoning", "Understanding")}
    letters = [chr(65 + k) for k in range(10)]
    data = {"path": str(SAMPLED.relative_to(HALF)), "n_items": len(items), "by_question_type": typ,
            "expected_by_question_type": {"Reasoning": 186, "Understanding": 58}, "unique_ids": len({i["id"] for i in items}),
            "all_ids_Text_prefixed": all(i["id"].startswith("Text-") for i in items),
            "all_10_options": all(len(i["options"]) == 10 for i in items),
            "labels_single_letter_A_J": all(len(i["label"]) == 1 and i["label"][0] in letters for i in items),
            "subset_of_full_text": all(i["id"] in {f["id"] for f in full} for i in items),
            "full_text_n": len(full), "full_by_question_type": ftyp, "mm_run": False,
            "sample_fraction": {t: round(typ[t] / ftyp[t], 4) for t in typ},
            "mm_sampled_n": len(load_items(SAMPLED_MM)) if SAMPLED_MM.exists() else None,
            "question_chars": {"min": min(len(i["question"]) for i in items), "max": max(len(i["question"]) for i in items),
                               "mean": round(sum(len(i["question"]) for i in items) / len(items), 1)}}

    g3 = next((i for i in items if i["id"] == "Text-20"), items[0])   # the item Appendix G.3 walks through
    rendered = {a["model"]: {"stage1": redacted_request(request(a, g3, 0, 1))["body"],
                             "stage2_with_placeholder_reply": redacted_request(request(a, g3, 0, 2, PLACEHOLDER))["body"]}
                for a in ARMS}
    env = {"item_id": g3["id"], "prompt_template": api.tpl.zero_shot_cot_prompt, "trigger_rendered": trigger(g3),
           "trigger_template": api.tpl.zero_shot_cot_trigger, "prompt_sha256": sha(stage1_text(g3)),
           "system_role_defined_but_dropped": api.tpl.zero_shot_system_role, "prompt_chars": len(stage1_text(g3)),
           "params": {"max_completion_tokens": MCT, "temperature": "not sent (paper C.2)", "system_message": "none",
                      "seed": "seed_idx (0 = the original's seed=0)"},
           "appendix_g3_prompt_found_verbatim": None}
    if PAPER.exists():                       # Appendix G.3 prints this item's rendered stage-1 prompt verbatim
        def norm(s):
            return " ".join(s.replace("’", "'").replace("‘", "'").split())
        ptxt = norm(PAPER.read_text(encoding="utf-8", errors="replace"))
        env["appendix_g3_prompt_found_verbatim"] = norm(stage1_text(g3))[2:] in ptxt   # the appendix reflows "Q: "
        env["appendix_g3_trigger_found_verbatim"] = norm(trigger(g3)) in ptxt

    cases = [dict(reply=r, expected=e, got=g, **{"pass": g == e}) for r, e in PARSER_CASES for g, _ in [score(g3, r)]]
    replay = scorer_replay(items, np.random.default_rng(RNG_SEED))
    counts = implied_counts()
    ok = {"repo_commit": head == REPO_COMMIT, "n_items": data["n_items"] == 244 and data["unique_ids"] == 244,
          "splits": typ == data["expected_by_question_type"], "options_and_labels": data["all_10_options"] and data["labels_single_letter_A_J"],
          "subset_of_full": data["subset_of_full_text"], "parser": sum(c["pass"] for c in cases) == len(cases),
          "printed_are_counts": all(c["exact"] for m in counts.values() for c in m.values() if isinstance(c, dict)),
          "scorer_replay": all(r["matches_printed"] for r in replay.values()),
          "appendix_g3": env["appendix_g3_prompt_found_verbatim"] is not False}
    out = {"card_id": CARD, "checked_utc": now(), "repo": str(REPO), "repo_commit_expected": REPO_COMMIT,
           "repo_commit_found": head, "repo_commit_matches_card": ok["repo_commit"],
           "repo_code_imported": ["eval/config/prompt_templates.py PromptTemplates.load_templates",
                                  "eval/utils.py answer_cleansing", "eval/main.py set_correctness"],
           "openai_sdk_stubbed": api.openai_stubbed, "dataset": data, "rendered_request": env,
           "rendered_bodies_redacted": rendered, "printed_values_are_integer_counts": counts,
           "parser_selftest": {"n": len(cases), "n_pass": sum(c["pass"] for c in cases), "cases": cases,
                               "known_quirks": QUIRKS},
           "scorer_replay_vs_table5": replay, "checks": ok,
           "expert_baseline_row": {**EXPERT, "n": len(full), "note": "aggregated examinee response distributions on "
                                   "the FULL Text set; not an integer count (41.74% of 1861 = 776.8) and not "
                                   "restricted to the 244-item sample the o1/o3-mini rows use"},
           "token_estimate": token_estimate(items=items), "log_policy": REDACTED, "frictions": FRICTIONS}
    out["ok"] = all(ok.values())
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[check] repo {head[:10]} matches card: {ok['repo_commit']}; openai SDK stubbed: {api.openai_stubbed}\n"
          f"[check] Text sampled {data['n_items']} items = {typ['Reasoning']} Reasoning + {typ['Understanding']} "
          f"Understanding, 10 options each, subset of the full {data['full_text_n']} "
          f"({data['sample_fraction']['Reasoning']:.3f} / {data['sample_fraction']['Understanding']:.3f} of each split)\n"
          f"[check] Table 5 cells are integer counts (o1 86/23/109, o3-mini 70/21/91): {ok['printed_are_counts']}; "
          f"scorer replay reproduces both printed rows: {ok['scorer_replay']}\n"
          f"[check] Appendix G.3 prompt rendered verbatim from the dataset: {env['appendix_g3_prompt_found_verbatim']}\n"
          f"[check] parser self-test {out['parser_selftest']['n_pass']}/{len(cases)} ({len(QUIRKS)} quirk(s) recorded)\n"
          f"[check] {'OK' if out['ok'] else 'FAILED ' + str([k for k, v in ok.items() if not v])} -> {CHECK_PATH} "
          f"(no question text written)")
    return 0 if out["ok"] else 1


def cmd_dry_run(args):
    items = load_items()
    reqs = []
    for arm in ARMS:
        for stage in (1, 2):                # stage 2 is provisional: the real one carries the live stage-1 reply
            reqs += [request(arm, it, s, stage, PLACEHOLDER if stage == 2 else None)
                     for it in items for s in range(arm["seeds"])]
    est = token_estimate(items=items)
    total = round(sum(v["usd_expected"] for v in est.values()), 2)
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN / "requests.jsonl").open("w", encoding="utf-8") as f:
        for r in reqs:
            f.write(json.dumps(redacted_request(r), ensure_ascii=False) + "\n")
    for m, v in est.items():
        print(f"[dry-run] {m}: {v['seeds']} seed(s) x 244 items x 2 stages = {v['calls']} calls; "
              f"~{v['tokens_in']/1e3:.0f}k in ({v['tokens_in_method']}) / ~{v['tokens_out_expected']/1e3:.0f}k out "
              f"(budget {EXPECTED_OUT[1]}+{EXPECTED_OUT[2]} reasoning+visible tokens per item) -> "
              f"~${v['usd_expected']:.2f} (ceiling at max_completion_tokens {MCT}: ${v['usd_ceiling_at_max_completion_tokens']:.2f})")
    print(f"[dry-run] total ~${total:.2f} of cap ${args.cap}; {len(reqs)} requests written to "
          f"{RUN / 'requests.jsonl'} with the question text redacted (sha256 kept); no API calls made")
    return 0


def cmd_run(args):
    """Four battery passes (o1 stage 1/2, o3-mini stage 1/2) into one run dir. The battery's cap is cumulative over
    the dir, so each arm gets its own ceiling (share of the cap) and a runaway o1 cannot starve the o3-mini row."""
    items = load_items()
    idx = {it["id"]: it for it in items}
    redact_calls(RUN)                        # clean anything an earlier interrupt left behind
    for arm in ARMS:
        bp = RUN / "budget.json"
        spent = float(json.loads(bp.read_text(encoding="utf-8")).get("cost_usd", 0.0)) if bp.exists() else 0.0
        arm_cap = round(min(args.cap, spent + args.cap * arm["cap_share"]), 2)
        for stage in (1, 2):
            if stage == 1:
                reqs = [request(arm, it, k, 1) for it in items for k in range(arm["seeds"])]
            else:
                done = load_results(RUN)
                reqs = [request(arm, idx[rid.split("|")[1].split("#")[0]], s, 2, reply_text(rec))
                        for (rid, s), rec in sorted(done.items())
                        if rid.startswith(arm["tag"] + "|") and rid.endswith("#s1")]
            try:
                b = run_battery(reqs, RUN, arm_cap, workers=args.workers, label=f"{CARD}/{arm['tag']}/s{stage}")
            finally:
                n = redact_calls(RUN)        # never leave question text on disk, even after an interrupt
            print(f"[run] {arm['tag']} stage {stage}: cumulative ${float(b.get('cost_usd', 0.0)):.2f} of arm ceiling "
                  f"${arm_cap} (paper cap ${args.cap}); {n} archived calls redacted")
            if b.get("stopped_at_cap") or b.get("stopped_on_errors"):
                print("[run] stopped early (cap or errors); rerun to resume")
                return 1
    return 0


def cmd_analyze(args):
    items, done = load_items(), load_results(RUN)
    if not done:
        print(f"[analyze] no archived calls under {RUN}; run --run first")
        return 1
    redact_calls(RUN)
    rng, rows, per_item = np.random.default_rng(RNG_SEED), {}, []
    st = {"missing_stage2": 0, "truncated_replies": 0, "reasoning_tokens": []}
    for arm in ARMS:
        seeds = sorted({s for (rid, s) in done if rid.startswith(arm["tag"] + "|")})
        credit = {}                          # {item_id: [0/1 per seed]}
        for s in seeds:
            for it in items:
                r1, r2 = (done.get((f"{arm['tag']}|{it['id']}#s{k}", s)) for k in (1, 2))
                if r2 is None:
                    st["missing_stage2"] += 1
                    continue
                for resp in [(r or {}).get("response") or {} for r in (r1, r2)]:
                    st["truncated_replies"] += (resp.get("choices") or [{}])[0].get("finish_reason") == "length"
                    rt = (resp.get("usage") or {}).get("completion_tokens_details") or {}
                    st["reasoning_tokens"] += [rt["reasoning_tokens"]] if rt.get("reasoning_tokens") is not None else []
                letter, ok = score(it, reply_text(r2))
                credit.setdefault(it["id"], []).append(int(ok))
                per_item.append({"arm": arm["tag"], "model": arm["model"], "item_id": it["id"], "seed_idx": s,
                                 "question_type": it["question_type"], "medical_task": it["medical_task"],
                                 "body_system": it["body_system"], "parsed_letter": letter, "correct": bool(ok),
                                 "prompt_sha256": sha(stage1_text(it)), "chars_reply_s2": len(reply_text(r2)),
                                 "chars_reply_s1": len(reply_text(r1)) if r1 else None})
        med = {k: float(np.median(v)) for k, v in credit.items()}
        rows[arm["model"]] = ar = {}
        for split in ("Reasoning", "Understanding", "Avg"):
            got = [i for i in items if i["id"] in med and (split == "Avg" or i["question_type"] == split)]
            vals, orig = [med[i["id"]] for i in got], ORIGINAL[arm["model"]][split]
            a, ci, band = round(100 * float(np.mean(vals)), 4), boot_ci(vals, rng), binom_band(orig, N_SPLIT[split])
            ar[split] = {"acc_pct": a, "acc_ci95": ci, "orig_pct": orig, "orig_band_binom95": band, "n": len(vals),
                         "rerun_inside_orig_band": bool(band[0] <= a <= band[1]),
                         "orig_inside_rerun_ci": bool(ci[0] <= orig <= ci[1]),
                         "per_seed": [round(100 * float(np.mean([credit[i["id"]][k] for i in got
                                                                 if len(credit[i["id"]]) > k])), 4) for k in range(len(seeds))],
                         "n_unparsed": sum(1 for r in per_item if r["arm"] == arm["tag"] and r["parsed_letter"] is None
                                           and (split == "Avg" or r["question_type"] == split))}
        ar["Reasoning"]["secondary_reasoning_above_understanding"] = bool(ar["Reasoning"]["acc_pct"] > ar["Understanding"]["acc_pct"])
        ar["descriptive"] = {k: {v: round(100 * float(np.mean([med[i["id"]] for i in items if i[k] == v and i["id"] in med])), 2)
                                 for v in sorted({i[k] for i in items})} for k in ("medical_task", "body_system")}

    o1, o3 = ARMS[0]["model"], ARMS[1]["model"]
    ordering = rows[o1]["Avg"]["acc_pct"] > rows[o3]["Avg"]["acc_pct"]      # the claim's own direction
    above_expert = rows[o1]["Avg"]["acc_pct"] > EXPERT["Avg"]
    for m, inside in ((o1, rows[o1]["Avg"]["rerun_inside_orig_band"]), (o3, rows[o3]["Avg"]["rerun_inside_orig_band"])):
        r = rows[m]["Avg"]
        r["ordering_o1_above_o3mini"] = bool(ordering)
        if m == o1:
            r["above_expert_baseline_42_60"] = bool(above_expert)
            r["verdict"] = ("사망 (dead)" if not inside or not ordering else
                            "생존 (survived)" if above_expert else "부분 생존 (partial)")
        else:
            r["verdict"] = ("사망 (dead)" if not inside else
                            "생존 (survived)" if ordering else "부분 생존 (partial)")

    with ITEMS.open("w", encoding="utf-8") as f:
        for r in per_item:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    budget = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    meta = {
        "card_id": CARD, "run_date_utc": now()[:10],
        "target_paper": {"title": "MedXpertQA: Benchmarking Expert-Level Medical Reasoning and Understanding",
                         "repo": "https://github.com/TsinghuaC3I/MedXpertQA", "repo_commit": REPO_COMMIT,
                         "original_source": "Table 5 (LLMs on MedXpertQA Text), the two rows marked as a sampled "
                         "subset: o1 46.24/39.66/44.67 and o3-mini 37.63/36.21/37.30 on the 244-item seed-42 10% "
                         "sample; Expert (Pre-Licensed) 41.74/45.44/42.60 on the full Text set"},
        "generation": {
            "model_requested": [a["model"] for a in ARMS], "substitute_snapshot": None,
            "model_served": sorted({r.get("model_served") for r in done.values() if r.get("model_served")}),
            "n_fingerprints": len({r.get("system_fingerprint") for r in done.values()}),
            "parameters": f"zero-shot CoT, 2 stages per item; no system message and no temperature for o1/o3-mini "
                          f"(paper C.2, api_agent.py); max_completion_tokens {MCT}; seed = seed_idx (0 = the original)",
            "battery": f"Text sampled subset, 244 items x 2 stages x {ARMS[0]['seeds']} seed (o1) / "
                       f"{ARMS[1]['seeds']} seeds (o3-mini) = {len(done)} archived calls; median over seeds per item; "
                       f"item-level bootstrap {N_BOOT} draws (rng {RNG_SEED}); parser/scorer imported from the repo",
            "mean_reasoning_tokens": round(float(np.mean(st["reasoning_tokens"])), 1) if st["reasoning_tokens"] else None},
        "results": {
            "rows": rows, "cost_usd": round(float(budget.get("cost_usd", 0.0)), 4), "calls": len(done),
            "errors": int(budget.get("errors", 0)), "missing_stage2": st["missing_stage2"],
            "truncated_replies": int(st["truncated_replies"]),
            "judgment": rows[o1]["Avg"]["verdict"], "judgment_o3mini_row": rows[o3]["Avg"]["verdict"],
            "judged_by": "automatic rule per ANALYSIS_PLAN section 1 as the card instantiates it (median over seeds "
                         "inside the binomial 95% band of the printed value; o1 > o3-mini; o1 > the 42.60 expert "
                         "baseline); the paper reports no significance test for these rows, so that clause is vacuous; "
                         "human double-coding pending",
            "note": f"Text subset only (MM not run). Per-item file {ITEMS.name} carries ids, hashes and parsed letters; "
                    f"calls.jsonl carries the model replies with the question text redacted (prompt_sha256 kept) under "
                    f"the authors' Appendix A request."},
        "deviations_from_card": [
            "o1 runs 1 seed instead of the card's 3 (the card's own cheaper alternative; ANALYSIS_PLAN section 3 asks for 3) - the o1 row therefore has no run-to-run spread",
            "no prompt-paraphrase arm (ANALYSIS_PLAN section 3): the claim is a benchmark level under the paper's exact prompt",
            "MM subset not run, so Table 4's o1 56.28 is not checked",
            "per-paper cap USD 60 instead of the card's est_cost_usd 134 (which assumed 3 seeds for both arms)",
            "the o3-mini row is judged as a second claim row inside this card rather than as a separate card"],
        "reproducibility_frictions_observed": FRICTIONS}
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    for m in (o1, o3):
        for split in ("Reasoning", "Understanding", "Avg"):
            r = rows[m][split]
            print(f"  {m:<20} {split:<14} {r['acc_pct']:6.2f} CI{r['acc_ci95']} orig {r['orig_pct']:.2f} "
                  f"band{r['orig_band_binom95']} {'in' if r['rerun_inside_orig_band'] else 'OUT'}"
                  f"{'  -> ' + r['verdict'] if split == 'Avg' else ''}")
    print(f"[analyze] wrote {META}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=f"Tier A re-execution adapter for card {CARD} (MedXpertQA Text)")
    g = ap.add_mutually_exclusive_group(required=True)
    for f in ("check", "dry-run", "run", "analyze"):
        g.add_argument("--" + f, action="store_true")
    ap.add_argument("--cap", type=float, default=CAP)
    ap.add_argument("--workers", type=int, default=WORKERS)
    a = ap.parse_args()
    return cmd_check(a) if a.check else cmd_dry_run(a) if a.dry_run else cmd_run(a) if a.run else cmd_analyze(a)


if __name__ == "__main__":
    sys.exit(main())
