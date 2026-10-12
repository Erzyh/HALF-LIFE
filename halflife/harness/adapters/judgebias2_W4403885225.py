"""Card W4403885225 - Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge (Ye, Wang, Huang et al., arXiv 2410.02736; CALM release
Y0oMu/LLM-Judge-Bias-Dataset). Repository-based upgrade of the Tier B prompt-level run: the verbosity Robustness Rate of the judge
gpt-4-turbo-2024-04-09 (Appendix Table 8 'gpt-4-turbo-0409').

CLAIM RE-MEASURED (Table 4, row GPT-4-Turbo, column Ver. on D_FR): RR = 0.915 over the 500 fact-related items - the judge keeps its pairwise
verdict on only 91.5% of the pairs after the WORSE answer is padded with redundant text - against the same-condition consistency ceiling
CR_FR = 0.990. The template itself says "Do not allow the length of the responses to influence your evaluation", so the 8.5% of flips is a
failure to follow an instruction the prompt states outright.

DESIGN (Sec. 3 Metrics): the judge runs twice; turn 1 gives y, turn 2 gives two parallel judgments, one unperturbed (y_rand) and one perturbed
(y_hat). RR = mean 1[y == y_hat], CR = mean 1[y == y_rand]. 3 judgments x 500 items = 1,500 calls:
  orig  Assistant A = answer1, Assistant B = answer2          -> y
  pert  Assistant A = answer1, Assistant B = answer2_longer   -> y_hat   (the padding is frozen in the release)
  rep   byte-identical prompt to orig, sampled again at T 0.7 -> y_rand  (within-run noise floor)
Requests are emitted item-major, so a run that stops at the cap leaves complete item triples rather than 500 halves.

PROMPT: the release's own promptTemplate.evaluate_ai_responses, imported and never copied. It is the source string of Appendix F Figure 13 with
its leading newline, hard line wraps, U+2019 apostrophes and trailing "\\n    ", sent as ONE user message including the literal "[System]"
header, and it is identical to evaluate_ai_responses_no_tie (no tie option). Whitespace-normalised it equals the Tier B config's PDF
transcription, but the source form costs ~11 more input tokens per call.

DECISIONS 2026-09-19 (card key decisions_2026_09_19): verbosity RR on the 500 fact-related items only; the unperturbed repeat IS run as the
within-run noise floor (CR, published 0.990); no second live arm; an unparsable or missing verdict is DROPPED and the drop rate reported, with
the Tier B rule (missing = flip) as a secondary number; 1 seed at the paper's decoding settings; per-paper cap USD 30.

JUDGMENT (ANALYSIS_PLAN section 1 as the card instantiates it): survived = 0.915 inside the item-bootstrap 95% CI of our RR AND RR significantly
below the same-run CR ceiling (one-sided exact McNemar on the discordant items, p < 0.05); partial = RR outside that CI but still below the
ceiling; dead = RR no longer distinguishable from CR, i.e. the verbosity bias has been trained out. An INCREASE in RR is flagged as a
substantive finding, not merely survival.

  python adapters/judgebias2_W4403885225.py --check      # data, template, parser, Tier B re-score; no API calls
  python adapters/judgebias2_W4403885225.py --dry-run    # 1,500 requests + cost estimate; no API calls
  python adapters/judgebias2_W4403885225.py --run [--cap 30]
  python adapters/judgebias2_W4403885225.py --analyze
"""
import argparse, hashlib, importlib.util, json, re, subprocess, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, pricing_for, run_battery  # noqa: E402

CARD = "W4403885225"
HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / CARD / "Y0oMu__LLM-Judge-Bias-Dataset"
TEMPLATE_PY, DATA, BASE = REPO / "promptTemplate.py", REPO / "bias_datasets" / "verbosity_bias_standardized.json", REPO / "base_datasets" / "fact_related_dataset.json"
TIERB_CFG, TIERB_RUN = HALF / "harness" / "tierb" / "configs" / f"{CARD}.json", HALF / "runs" / "tierb" / CARD
RUN_ROOT = HALF / "runs" / CARD
RUN, CHECK_JSON, META = RUN_ROOT / "baseline_alive", RUN_ROOT / "environment_check.json", RUN_ROOT / "run_meta.json"

MODEL, ENCODING = "gpt-4-turbo-2024-04-09", "cl100k_base"
CAP, WORKERS, N_BOOT, BOOT_SEED = 30.0, 4, 1000, 0
TEMPERATURE, MAX_TOKENS, TOP_P = 0.7, 1024, 1.0   # T 0.7 = Sec. 3 Hyperparameters; max_tokens / top_p unreported, carried over from the Tier B config
JUDGMENTS = ("orig", "pert", "rep")
SLOT_B = {"orig": "answer2", "pert": "answer2_longer", "rep": "answer2"}
FALLBACK_OUT_TOKENS = 285                         # reply-length assumption used only if the Tier B archive is unavailable
VERDICT_RE = re.compile(r"\[\[([AB])\]\]")
TIE_RE = re.compile(r"\btie\b|\bneither\b|equally (good|well|bad)|no (clear )?(winner|distinction|basis)", re.I)
ORIGINAL = {"Ver_RR": 0.915, "CR_FR": 0.990, "n_items": 500, "composition": {"ScienceQA": 200, "GSM8K": 151, "MATH": 149},
            "other_judges_Ver_RR": {"ChatGPT": 0.900, "GPT-4o": 0.977, "GLM-4": 0.887, "Claude-3.5": 0.952, "Qwen2": 0.884},
            "source": "Table 4 (D_FR, row GPT-4-Turbo, columns Ver. and CR_FR); RR/CR defined in Sec. 3 Metrics"}


def now():
    return datetime.now(timezone.utc).isoformat()


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(HALF)).replace("\\", "/")
    except ValueError:
        return str(p)


def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def repo_head():
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30).stdout.strip() or None
    except Exception:
        return None


def reply_text(resp):
    try:
        return resp["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


# ----------------------------------------------------------------------------- repository code and data
def template_module():
    """Import the release's promptTemplate.py in place (no copy, no edit); the file is function definitions only."""
    if not TEMPLATE_PY.exists():
        sys.exit(f"missing {TEMPLATE_PY}; clone the CALM release under external/repos/{CARD}/")
    spec = importlib.util.spec_from_file_location(f"promptTemplate_{CARD}", TEMPLATE_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_items():
    items = json.loads(DATA.read_text(encoding="utf-8"))
    assert len(items) == ORIGINAL["n_items"], f"expected 500 items, found {len(items)}"
    return items


def render(mod, item, judgment):
    """Figure 13 prompt rendered by the repository itself -> one user message (the '[System]' header is part of the text)."""
    return [{"role": "user", "content": mod.evaluate_ai_responses(item["question"], item["answer1"], item[SLOT_B[judgment]])}]


def parse_verdict(text):
    """Card parse rule: last [[A]] / [[B]] in the reply; None when the judge emits no bracketed verdict."""
    hits = VERDICT_RE.findall(text or "")
    return hits[-1] if hits else None


def tierb_archive():
    """Read the Tier B run once -> per-item verdicts (orig/pert only), mean completion tokens per judgment, unparsable replies."""
    if not (TIERB_RUN / "calls.jsonl").exists():
        return None
    verd, out, unparsed = {}, {"orig": [], "pert": []}, []
    for line in (TIERB_RUN / "calls.jsonl").open(encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        i, var = r["id"].rsplit("_", 1)
        text, resp = reply_text(r.get("response")), r.get("response") or {}
        verd.setdefault(int(i), {})[var] = v = parse_verdict(text)
        out.setdefault(var, []).append((resp.get("usage") or {}).get("completion_tokens", 0))
        if v is None:
            unparsed.append({"id": r["id"], "tie_like": bool(TIE_RE.search(text)), "chars": len(text),
                             "finish_reason": (resp.get("choices") or [{}])[0].get("finish_reason")})
    mean = {k: float(np.mean(v)) if v else float(FALLBACK_OUT_TOKENS) for k, v in out.items()}
    mean["rep"] = mean["orig"]                    # the repeat judgment sends the same prompt as orig
    return {"verdicts": [verd.get(i, {}) for i in range(len(verd))], "out_tokens": mean, "unparsed": unparsed, "n_calls": sum(len(v) for v in out.values())}


# ----------------------------------------------------------------------------- requests and cost
def build_requests(mod=None, items=None):
    mod, items = mod or template_module(), items if items is not None else load_items()
    return [{"id": f"{i}|{j}", "seed_idx": 0, "meta": {"item": i, "judgment": j, "data_resource": it.get("data_resource")},
             "body": {"model": MODEL, "messages": render(mod, it, j), "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "top_p": TOP_P}}
            for i, it in enumerate(items) for j in JUDGMENTS]        # item-major: a cap stop leaves complete triples


def tiktoken_estimate(reqs, tb=None):
    """Exact prompt tokens (3 priming + 3 + role + content per message, the chat-completions accounting) and two output scenarios: the Tier B
    run's measured reply lengths, and every reply at max_tokens (the bound the battery's own dry run uses)."""
    import tiktoken
    enc, pr = tiktoken.get_encoding(ENCODING), pricing_for(MODEL)
    out_mean = (tb or {}).get("out_tokens") or {j: float(FALLBACK_OUT_TOKENS) for j in JUDGMENTS}
    src = f"measured on {rel(TIERB_RUN)}/calls.jsonl ({tb['n_calls']} replies)" if tb else "fallback constant (no Tier B archive)"
    tin, per, by = 0, 0.0, Counter()
    for r in reqs:
        n = 3 + sum(3 + len(enc.encode(m["role"])) + len(enc.encode(m["content"])) for m in r["body"]["messages"])
        tin, by[r["meta"]["judgment"]], per = tin + n, by[r["meta"]["judgment"]] + n, per + out_mean[r["meta"]["judgment"]]
    tmax = sum(r["body"]["max_tokens"] for r in reqs)
    usd = lambda o: tin / 1e6 * pr["input"] + o / 1e6 * pr["output"]
    return {"calls": len(reqs), "encoding": ENCODING, "tokens_in": tin, "tokens_in_per_judgment": dict(by), "tokens_out_calibrated": int(round(per)),
            "tokens_out_upper": tmax, "output_calibration": src, "usd_calibrated": round(usd(per), 2), "usd_upper": round(usd(tmax), 2), "pricing_usd_per_1m": pr}


# ----------------------------------------------------------------------------- metrics
def pair_flags(verd, a, b, rule):
    """Per-item agreement flags for the pair (a, b). A judgment absent from the dict was never archived (cap stop or HTTP error) and leaves the
    item out of the denominator under BOTH rules; a key present with value None is an unparsable verdict, which 'drop' excludes (nan) and 'flip'
    counts as a changed verdict (0)."""
    f = []
    for d in verd:
        if a not in d or b not in d:
            f.append(np.nan)
        else:
            f.append(np.nan if (d[a] is None or d[b] is None) and rule == "drop" else float(d[a] is not None and d[a] == d[b]))
    return np.array(f, float)


def pair_counts(verd, a, b):
    return {"not_archived": sum(1 for d in verd if a not in d or b not in d),
            "unparsable_verdict": sum(1 for d in verd if a in d and b in d and (d[a] is None or d[b] is None))}


def rate(f):
    ok = f[~np.isnan(f)]
    return (float(ok.mean()) if ok.size else float("nan")), int(ok.size), int(np.isnan(f).sum())


def bootstrap(flags, n_boot=N_BOOT, seed=BOOT_SEED):
    """Percentile 95% CIs over items; RR and CR share each resample, so the RR - CR gap CI is paired."""
    rng, n = np.random.default_rng(seed), len(next(iter(flags.values())))
    acc, gap = {k: [] for k in flags}, []
    for _ in range(n_boot):
        idx, cur = rng.integers(0, n, n), {}
        for k, f in flags.items():
            s = f[idx][~np.isnan(f[idx])]
            cur[k] = float(s.mean()) if s.size else np.nan
            acc[k].append(cur[k])
        gap.append(cur["rr"] - cur["cr"])

    def ci(v):
        v = np.asarray(v, float)
        v = v[~np.isnan(v)]
        return [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)] if v.size else [None, None]
    return {**{k: ci(v) for k, v in acc.items()}, "rr_minus_cr": ci(gap), "n_boot": n_boot, "seed": seed}


def mcnemar_below_ceiling(rob, cons):
    """One-sided exact McNemar (binomial on the discordant items), H1: RR < CR within the same run."""
    ok = ~(np.isnan(rob) | np.isnan(cons))
    r, c = rob[ok], cons[ok]
    b, d = int(((c == 1) & (r == 0)).sum()), int(((c == 0) & (r == 1)).sum())
    return {"n_pairs": int(ok.sum()), "consistent_not_robust": b, "robust_not_consistent": d, "test": "exact McNemar (binomial on discordant items), H1: RR < CR",
            "p_one_sided": float(stats.binomtest(d, b + d, 0.5, alternative="less").pvalue) if b + d else 1.0}


def score(verd):
    """-> {rule: metrics} for both missing-verdict rules; 'drop' is primary per the 2026-09-19 decisions."""
    out, c_rr, c_cr = {}, pair_counts(verd, "orig", "pert"), pair_counts(verd, "orig", "rep")
    inside = lambda ci, v: bool(ci[0] is not None and ci[0] <= v <= ci[1])
    for rule in ("drop", "flip"):
        rob, cons = pair_flags(verd, "orig", "pert", rule), pair_flags(verd, "orig", "rep", rule)
        (rr, n_rr, d_rr), (cr, n_cr, d_cr) = rate(rob), rate(cons)
        ci = bootstrap({"rr": rob, "cr": cons})
        out[rule] = {"rr": round(rr, 4), "rr_ci95": ci["rr"], "n_rr": n_rr, "rr_items_dropped": d_rr, "rr_drop_rate": round(d_rr / len(verd), 4) if verd else None,
                     "rr_item_counts": c_rr, "cr": round(cr, 4), "cr_ci95": ci["cr"], "n_cr": n_cr, "cr_items_dropped": d_cr,
                     "cr_drop_rate": round(d_cr / len(verd), 4) if verd else None, "cr_item_counts": c_cr, "rr_minus_cr": round(rr - cr, 4),
                     "rr_minus_cr_ci95": ci["rr_minus_cr"], "mcnemar_rr_below_cr": mcnemar_below_ceiling(rob, cons), "n_boot": ci["n_boot"], "bootstrap_seed": ci["seed"],
                     "binomial_rr_vs_published_cr_0.990": float(stats.binomtest(int(round(rr * n_rr)), n_rr, ORIGINAL["CR_FR"], alternative="less").pvalue) if n_rr else None,
                     "orig_rr_0.915_inside_ci95": inside(ci["rr"], ORIGINAL["Ver_RR"]), "orig_cr_0.990_inside_ci95": inside(ci["cr"], ORIGINAL["CR_FR"])}
    return out


def judge(row):
    """Card rule. Dead = RR is no longer distinguishable from the same-run consistency ceiling."""
    rr, inside = row["rr"], row["orig_rr_0.915_inside_ci95"]
    below = row["mcnemar_rr_below_cr"]["p_one_sided"] < 0.05
    flags = {"original_0.915_inside_ci95": inside, "rr_significantly_below_cr_ceiling": bool(below), "rr_increased_vs_paper": bool(rr > ORIGINAL["Ver_RR"] and not inside),
             "rr_above_gpt4o_0.977": bool(rr > ORIGINAL["other_judges_Ver_RR"]["GPT-4o"]), "rr_above_claude35_0.952": bool(rr > ORIGINAL["other_judges_Ver_RR"]["Claude-3.5"])}
    if rr != rr:
        return "미판정 (incomplete)", flags
    return ("사망 (dead)" if not below else "생존 (survived)" if inside else "부분 생존 (partial)"), flags


# ----------------------------------------------------------------------------- modes
def check():
    mod, items, tb = template_module(), load_items(), tierb_archive()
    lens = {k: float(np.mean([len(it[k]) for it in items])) for k in ("answer1", "answer2", "answer2_longer")}
    base = json.loads(BASE.read_text(encoding="utf-8")) if BASE.exists() else []
    btrip = {(a["question"], a["answer1"], a["answer2"]) for a in base}
    it0 = items[0]
    p_orig, p_pert, p_rep = (mod.evaluate_ai_responses(it0["question"], it0["answer1"], it0[SLOT_B[j]]) for j in JUDGMENTS)
    tb_prompt = json.loads(TIERB_CFG.read_text(encoding="utf-8"))["prompt"]["user_template"].replace("{question}", it0["question"]).replace("{answer_a}", it0["answer1"]).replace("{answer_b}", it0["answer2"])
    squash = lambda s: re.sub(r"\s+", " ", s).strip()

    cases = [("Comparing the two ... [[A]]", "A"), ("blah\nFinal verdict: [[B]]", "B"), ("[[A]] then finally [[B]]", "B"), ("A is better", None), ("", None), (None, None),
             ("The verdict is [[C]] - a tie.", None), ("[[a]]", None), ("[[A]] [[B]] [[A]]", "A"), ("Assistant A is better.", None), ("verdict: [[ A ]]", None)]
    parser_ok = all(parse_verdict(t) == e for t, e in cases)
    syn = [{"orig": "A", "pert": "A", "rep": "A"}, {"orig": "A", "pert": "B", "rep": "A"}, {"orig": "B", "pert": "B", "rep": "A"},
           {"orig": None, "pert": "A", "rep": "A"}, {"orig": "A", "pert": None, "rep": "B"}, {}]     # last: item whose calls were never archived
    sc = score(syn)
    want = {"drop": {"rr": 0.6667, "n_rr": 3, "rr_items_dropped": 3, "cr": 0.5, "n_cr": 4}, "flip": {"rr": 0.4, "n_rr": 5, "rr_items_dropped": 1, "cr": 0.4, "n_cr": 5}}
    scorer_ok = all(sc[r][k] == v for r, w in want.items() for k, v in w.items())
    if not (parser_ok and scorer_ok):
        sys.exit(f"parser/scorer self-tests FAILED (parser {parser_ok}, scorer {scorer_ok}) - do not run the battery")

    est = tiktoken_estimate(build_requests(mod, items), tb)
    res = {"card": CARD, "checked_utc": now(), "python": sys.version.split()[0], "model": MODEL,
           "repo": {"path": rel(REPO), "head": repo_head(), "template_file": rel(TEMPLATE_PY), "template_sha256": sha_text(TEMPLATE_PY.read_text(encoding="utf-8"))},
           "data": {"file": rel(DATA), "n_items": len(items), "fields": sorted(items[0]), "composition": dict(Counter(it["data_resource"] for it in items)),
                    "composition_matches_card": dict(Counter(it["data_resource"] for it in items)) == ORIGINAL["composition"], "mean_chars": {k: round(v) for k, v in lens.items()},
                    "padding_ratio": round(lens["answer2_longer"] / lens["answer2"], 2), "padded_never_shorter": all(len(it["answer2_longer"]) > len(it["answer2"]) for it in items),
                    "distinct_questions": len({it["question"] for it in items}), "base_fact_related_rows": len(base),
                    "unperturbed_pairs_found_in_base_dataset": sum((it["question"], it["answer1"], it["answer2"]) in btrip for it in items)},
           "prompt": {"source": "promptTemplate.evaluate_ai_responses(question, answer_a, answer_b, need_tie=False), imported from the release", "messages": 1, "role": "user",
                      "identical_to_evaluate_ai_responses_no_tie": all(mod.evaluate_ai_responses(it["question"], it["answer1"], it["answer2"])
                                                                       == mod.evaluate_ai_responses_no_tie(it["question"], it["answer1"], it["answer2"]) for it in items[:50]),
                      "tie_option_offered": False, "need_tie_variant_differs": mod.evaluate_ai_responses("q", "x", "y", need_tie=True) != mod.evaluate_ai_responses("q", "x", "y"),
                      "system_header_is_text": p_orig.lstrip().startswith("[System]"), "leading_newline": p_orig.startswith("\n"), "trailing_repr": repr(p_orig[-12:]),
                      "rendered_sha256": {"orig": sha_text(p_orig), "pert": sha_text(p_pert), "rep": sha_text(p_rep)}, "rep_prompt_byte_identical_to_orig": p_rep == p_orig,
                      "pert_differs_only_in_assistant_b_block": p_orig.replace(it0["answer2"], "<B>") == p_pert.replace(it0["answer2_longer"], "<B>"),
                      "vs_tierb_transcription": {"config": rel(TIERB_CFG), "byte_identical": p_orig == tb_prompt, "identical_after_whitespace_normalisation": squash(p_orig) == squash(tb_prompt),
                                                 "note": "the Tier B config joined the PDF's hard line wraps into one line; the repo string is the source form"},
                      "excerpt_first_240_chars": p_orig[:240]},
           "parser": {"rule": r"last match of \[\[([AB])\]\]; None otherwise (case-sensitive, no tie label)", "all_synthetic_cases_pass": parser_ok,
                      "synthetic_cases": [{"reply": t, "verdict": parse_verdict(t), "expected": e} for t, e in cases], "scorer_selftest_passes": bool(scorer_ok),
                      "scorer_selftest_expected": want, "scorer_selftest_values": {r: {k: sc[r][k] for k in want[r]} for r in sc}},
           "budget": {**est, "cap_usd": CAP, "n_calls": 3 * len(items), "seeds": 1, "params": {"temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "top_p": TOP_P}},
           "original": ORIGINAL}
    if tb:
        pub = json.loads((TIERB_RUN / "result.json").read_text(encoding="utf-8")) if (TIERB_RUN / "result.json").exists() else {}
        rr = {r: dict(zip(("rr", "n"), (round(rate(pair_flags(tb["verdicts"], "orig", "pert", r))[0], 4), rate(pair_flags(tb["verdicts"], "orig", "pert", r))[1]))) for r in ("drop", "flip")}
        res["tierb_rescore"] = {"run_dir": rel(TIERB_RUN), "rr_by_rule": rr, "published_rr": (pub.get("reexecution") or {}).get("mean_over_seeds"), "unparsed_replies": tb["unparsed"],
                                "reproduces_published_value": bool(pub and abs(rr["flip"]["rr"] - pub["reexecution"]["mean_over_seeds"]) < 5e-4), "n_unparsed": len(tb["unparsed"]),
                                "unparsed_tie_like": sum(u["tie_like"] for u in tb["unparsed"]), "note": "Tier B ran only orig+pert (no CR arm) with the PDF transcription of the template"}

    d, p, t = res["data"], res["prompt"], res.get("tierb_rescore")
    checks = {"n_items 500": d["n_items"] == 500, "composition": d["composition_matches_card"], "padded never shorter": d["padded_never_shorter"],
              "no tie option": p["identical_to_evaluate_ai_responses_no_tie"], "leading newline": p["leading_newline"], "rep == orig prompt": p["rep_prompt_byte_identical_to_orig"],
              "pert differs only in B": p["pert_differs_only_in_assistant_b_block"], "tierb transcription == repo (normalised)": p["vs_tierb_transcription"]["identical_after_whitespace_normalisation"],
              "parser cases": parser_ok, "scorer self-test": bool(scorer_ok), "tierb published RR reproduced": bool(t["reproduces_published_value"]) if t else True}
    res["checks"] = checks
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_JSON.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[{CARD} --check] repo {rel(REPO)} @ {res['repo']['head']}; {d['n_items']} items {d['composition']}; mean chars a1 {d['mean_chars']['answer1']} / "
          f"a2 {d['mean_chars']['answer2']} / a2_longer {d['mean_chars']['answer2_longer']} (x{d['padding_ratio']}); {d['unperturbed_pairs_found_in_base_dataset']}/500 "
          f"unperturbed pairs also in base_datasets/fact_related_dataset.json")
    print(f"  template {rel(TEMPLATE_PY)}::evaluate_ai_responses, trailing {p['trailing_repr']}, item-0 prompt sha {p['rendered_sha256']['orig'][:12]}; byte-identical to the "
          f"Tier B transcription: {p['vs_tierb_transcription']['byte_identical']}")
    print("  " + "; ".join(f"{k} {'OK' if v else 'FAIL'}" for k, v in checks.items()))
    if t:
        print(f"  Tier B archive re-scored with this parser: RR flip {t['rr_by_rule']['flip']['rr']} (published {t['published_rr']}), RR drop {t['rr_by_rule']['drop']['rr']} "
              f"on n={t['rr_by_rule']['drop']['n']}; {t['n_unparsed']} unparsed replies, {t['unparsed_tie_like']} tie-like")
    print(f"  budget: {est['calls']} calls, {est['tokens_in']:,} prompt tokens ({ENCODING}); calibrated replies {est['tokens_out_calibrated']:,} -> ~${est['usd_calibrated']:.2f}; "
          f"all replies at max_tokens -> ~${est['usd_upper']:.2f}; cap ${CAP:.0f}\n  -> {rel(CHECK_JSON)}")
    if not all(checks.values()):
        sys.exit("environment check FAILED: " + ", ".join(k for k, v in checks.items() if not v))
    return res


def dry_run(cap):
    reqs = build_requests()
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN / "requests.jsonl").open("w", encoding="utf-8") as f:
        for r in reqs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    est = tiktoken_estimate(reqs, tierb_archive())
    bat = run_battery(reqs, RUN, cap, dry_run=True, label=CARD)          # the battery's own chars/4 + max_tokens upper bound
    print(f"[dry-run] {len(reqs)} calls = 500 items x 3 judgments {JUDGMENTS} x 1 seed, item-major; model {MODEL}, temperature {TEMPERATURE}, max_tokens {MAX_TOKENS}, top_p {TOP_P}")
    print(f"[dry-run] tiktoken {ENCODING}: {est['tokens_in']:,} prompt tokens ({', '.join(f'{k} {v:,}' for k, v in est['tokens_in_per_judgment'].items())}); {est['tokens_in'] / est['calls']:.0f} per call")
    print(f"[dry-run] replies calibrated on the Tier B archive ({est['output_calibration']}): {est['tokens_out_calibrated']:,} tokens -> ~${est['usd_calibrated']:.2f} at "
          f"${est['pricing_usd_per_1m']['input']}/${est['pricing_usd_per_1m']['output']} per 1M")
    print(f"[dry-run] worst case, every reply at max_tokens {MAX_TOKENS}: {est['tokens_out_upper']:,} out tokens -> ~${est['usd_upper']:.2f} (the battery's own estimate uses this bound: ${bat['est_usd']:.2f})")
    head = cap - est["usd_calibrated"]
    print(f"[dry-run] cap ${cap:.0f} -> ${head:.2f} headroom over the calibrated estimate ({head / est['usd_calibrated'] * 100:.0f}%); a run that reaches the cap stops cleanly and leaves complete item triples")
    print(f"[dry-run] wrote {rel(RUN / 'requests.jsonl')} ({(RUN / 'requests.jsonl').stat().st_size / 1e6:.1f} MB); no API calls made")
    return {**est, "battery_est_usd": bat["est_usd"], "cap_usd": cap}


def run(cap, workers):
    reqs = build_requests()
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "run_config.json").write_text(json.dumps({"card_id": CARD, "model": MODEL, "n_items": ORIGINAL["n_items"], "judgments": list(JUDGMENTS), "seeds": 1,
                                                     "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "top_p": TOP_P, "cap_usd": cap, "calls": len(reqs),
                                                     "prompt_source": f"{rel(TEMPLATE_PY)} evaluate_ai_responses (Appendix F Figure 13)", "repo_head": repo_head(),
                                                     "built_utc": now()}, indent=2), encoding="utf-8")
    run_battery(reqs, RUN, cap, workers=workers, label=CARD)


def analyze():
    res = load_results(RUN)
    if not res:
        print(f"no archived calls in {rel(RUN)}; run --run first")
        return None
    items = load_items()
    verd = [{} for _ in items]
    served, fps, finish, modes, cost, unparsed = set(), set(), Counter(), Counter(), 0.0, []
    for (rid, _), r in res.items():
        m = r.get("meta") or {}
        if m.get("item") is None or m.get("judgment") not in JUDGMENTS:
            continue
        text = reply_text(r.get("response"))
        verd[m["item"]][m["judgment"]] = v = parse_verdict(text)
        modes["parsed" if v else "unparsed"] += 1
        if v is None:
            unparsed.append({"id": rid, "tie_like": bool(TIE_RE.search(text)), "chars": len(text)})
        finish[((r.get("response") or {}).get("choices") or [{}])[0].get("finish_reason")] += 1
        served.add(r.get("model_served"))
        fps.add(r.get("system_fingerprint"))
        cost += r.get("cost_usd", 0) or 0
    complete, rows, tb = sum(all(j in d for j in JUDGMENTS) for d in verd), score(verd), tierb_archive()
    verdict, flags = judge(rows["drop"])
    if complete < len(items):
        verdict += f" [partial: {complete}/{len(items)} complete item triples]"
    out = {"card": CARD, "model": MODEL, "run_dir": rel(RUN), "n_calls": len(res), "complete_item_triples": complete, "cost_usd": round(cost, 4),
           "served": {"models": sorted(x for x in served if x), "n_fingerprints": len(fps - {None})}, "finish_reasons": {str(k): v for k, v in finish.items()},
           "parse": dict(modes), "unparsed": unparsed, "unparsed_tie_like": sum(u["tie_like"] for u in unparsed), "rules": rows, "primary_rule": "drop",
           "verdict_distribution": {j: dict(Counter(d.get(j) for d in verd)) for j in JUDGMENTS}, "flags": flags, "judgment": verdict, "original": ORIGINAL,
           "tierb": {"run_dir": rel(TIERB_RUN), "rr_by_rule": {r: round(rate(pair_flags(tb["verdicts"], "orig", "pert", r))[0], 4) for r in ("drop", "flip")} if tb else None,
                     "difference": "Tier B ran 1,000 calls (orig+pert only, no CR arm) with the PDF transcription of the template (paragraph wraps joined, ~11 fewer input "
                                   "tokens per call); Tier A adds the unperturbed repeat and renders the repository's source string"}}
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    write_run_meta(out)
    print(f"[{CARD} --analyze] {len(res)} calls, ${cost:.2f}, served {out['served']}, complete triples {complete}/{len(items)}, parse {dict(modes)}")
    for rule, r in rows.items():
        print(f"  [{rule:4s}] RR {r['rr']:.4f} CI {r['rr_ci95']} (n={r['n_rr']}, dropped {r['rr_items_dropped']} = {r['rr_drop_rate']:.1%}: {r['rr_item_counts']['not_archived']} not "
              f"archived, {r['rr_item_counts']['unparsable_verdict']} unparsable)  paper 0.915 inside {r['orig_rr_0.915_inside_ci95']}   CR {r['cr']:.4f} CI {r['cr_ci95']} paper "
              f"0.990 inside {r['orig_cr_0.990_inside_ci95']}   RR-CR {r['rr_minus_cr']:+.4f} CI {r['rr_minus_cr_ci95']}  McNemar p {r['mcnemar_rr_below_cr']['p_one_sided']:.3g}")
    print(f"  flags {flags}\n  Tier B (prompt-level) RR by rule: {out['tierb']['rr_by_rule']}\n  judgment: {verdict}")
    return out


def write_run_meta(out):
    b = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    prim, sec = out["rules"]["drop"], out["rules"]["flip"]
    keep = ("rr", "rr_ci95", "n_rr", "rr_items_dropped", "rr_drop_rate", "rr_item_counts", "cr", "cr_ci95", "n_cr", "cr_items_dropped", "cr_drop_rate", "cr_item_counts",
            "rr_minus_cr", "rr_minus_cr_ci95", "mcnemar_rr_below_cr", "orig_rr_0.915_inside_ci95", "orig_cr_0.990_inside_ci95", "binomial_rr_vs_published_cr_0.990", "n_boot", "bootstrap_seed")
    meta = {
        "card_id": CARD, "run_date_utc": now()[:10],
        "target_paper": {"title": "Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge", "doi": "10.48550/arxiv.2410.02736", "repo": "https://github.com/Y0oMu/LLM-Judge-Bias-Dataset",
                         "repo_commit": repo_head(), "repo_license": "none declared (README defers to the per-row source datasets)", "original_source": ORIGINAL["source"],
                         "original_values": {k: ORIGINAL[k] for k in ("Ver_RR", "CR_FR", "other_judges_Ver_RR")}},
        "generation": {"model_requested": MODEL, "model_served": out["served"]["models"], "n_fingerprints": out["served"]["n_fingerprints"], "python": sys.version.split()[0],
                       "endpoint": "POST https://api.openai.com/v1/chat/completions (harness/openai_client.py)",
                       "parameters": f"one user message (the '[System]' header is part of the template); temperature {TEMPERATURE} (Sec. 3 Hyperparameters); max_tokens {MAX_TOKENS} "
                                     f"and top_p {TOP_P} unreported by the paper, carried over from the Tier B config; no seed parameter; 1 seed",
                       "prompt_template_source": f"{rel(TEMPLATE_PY)} evaluate_ai_responses (== evaluate_ai_responses_no_tie), the source string of Appendix F Figure 13, imported "
                                                 f"from the release rather than transcribed",
                       "battery": f"{out['n_calls']} archived calls = 500 items x 3 judgments (orig / pert / rep), item-major; {out['complete_item_triples']} complete triples"},
        "results": {"primary_rule": "unparsable or missing verdict -> item dropped, drop rate reported", **{k: prim[k] for k in keep},
                    "secondary_rule_missing_equals_flip": {**{k: sec[k] for k in ("rr", "rr_ci95", "cr", "cr_ci95", "rr_minus_cr")}, "mcnemar_p": sec["mcnemar_rr_below_cr"]["p_one_sided"]},
                    "verdict_distribution": out["verdict_distribution"], "parse": out["parse"], "unparsed_tie_like": out["unparsed_tie_like"], "finish_reasons": out["finish_reasons"],
                    "published_ordering_context": {"our_rr": prim["rr"], **ORIGINAL["other_judges_Ver_RR"], "note": "single live arm by decision; the ordering GPT-4o > Claude-3.5 > "
                                                   "GPT-4-Turbo > ChatGPT is reported as context, not re-measured"},
                    "flags": out["flags"], "cost_usd": round(b.get("cost_usd", out["cost_usd"]), 4), "calls": b.get("calls", out["n_calls"]), "errors": b.get("errors", 0),
                    "cap_usd": b.get("cap_usd", CAP), "stopped_at_cap": b.get("stopped_at_cap", False), "judgment": out["judgment"],
                    "judged_by": "automatic rule per ANALYSIS_PLAN section 1 as the card instantiates it (0.915 inside the item-bootstrap 95% CI AND RR significantly below the "
                                 "same-run CR ceiling = survived; outside the CI but still below the ceiling = partial; not distinguishable from CR = dead); human double-coding pending",
                    "tierb_comparison": {"tierb_rr_published": 0.926, "tierb_rr_rescored_by_rule": out["tierb"]["rr_by_rule"], "difference": out["tierb"]["difference"]}},
        "reproducibility_frictions_observed": [
            "no evaluation code in the release: the verdict parser, the RR/CR aggregation and the treatment of an unparsable verdict are ours",
            "item-level original verdicts are not released, so the comparison is at the aggregate RR/CR level only (0.915 of 500 = 457 or 458 items)",
            "temperature 0.7 with no seed: the published 0.915 is itself a single noisy draw, and this re-run is one seed by decision",
            "max_tokens and top_p are unreported; 1024 / 1.0 carried over from the Tier B config (no Tier B reply was truncated, longest 539 tokens)",
            "the pairwise template offers no tie option, but the judge sometimes declares a tie in prose and emits no bracketed verdict; those items are dropped under the primary "
            "rule and counted as flips under the Tier B rule",
            "the release declares no licence and points back to the per-row data_resource (ScienceQA CC BY-NC-SA 4.0, GSM8K/MATH MIT)",
            "the verbosity file's unperturbed pairs differ from base_datasets/fact_related_dataset.json in a minority of rows and in row order, so 'the fact-related dataset' is "
            "not one fixed file in the release",
        ]}
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", rel(META))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="data, template, parser and Tier B re-score; no API calls")
    ap.add_argument("--dry-run", action="store_true", help="build the 1,500 requests and estimate cost; no API calls")
    ap.add_argument("--run", action="store_true", help="execute the battery (paid API calls, capped)")
    ap.add_argument("--analyze", action="store_true", help="RR/CR, bootstrap CIs, judgment, run_meta.json")
    ap.add_argument("--cap", type=float, default=CAP)
    ap.add_argument("--workers", type=int, default=WORKERS)
    a = ap.parse_args()
    if not any((a.check, a.dry_run, a.run, a.analyze)):
        ap.print_help()
        return
    if a.check:
        check()
    if a.dry_run:
        dry_run(a.cap)
    if a.run:
        run(a.cap, a.workers)
    if a.analyze:
        analyze()


if __name__ == "__main__":
    main()
