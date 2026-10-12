"""Card W4412887943 - MEDEC: A Benchmark for Medical Error Detection and Correction in Clinical Notes (abachaa/MEDEC).

Claim re-measured for gpt-4o-2024-05-13 with the zero-shot prompt P#1 (paper Section 4) on the public MEDEC-MS
test subset (597 of the 925 test notes; the 328 UW notes need a UW DUA - card decisions_2026_09_18):
  Table 2 row 'GPT-4o'       error-flag accuracy 0.6584   error-sentence accuracy 0.5665   (primary cell)
  Table 2 row 'GPT-4o-mini'  error-flag accuracy 0.6086   error-sentence accuracy 0.4757   (alternative cell: Section 5.1
                             attaches the snapshot name to "GPT-4o-mini (gpt-4o-2024-05-13)")
The judgment is flagged 'subset': Table 2 is on all 925 notes and no MS-only GPT-4o cell exists (Table 3 gives MS/UW
splits for Claude 3.5 Sonnet, o1-preview and the two doctors only). The unpinned 'GPT-4' arm is not run.

Protocol (paper Sections 4-5; the repositories hold data and the shared-task scorer, no prompting or post-processing code):
  * one user message, no system prompt: P#1 verbatim (Section 4, reflowed from the PDF), a blank line, then the note as the
    dataset's 'Sentences' column - one sentence per line, "<id> <sentence>" (CRLF normalised to LF, trailing blank line
    dropped, nothing else changed; 7 MS test notes carry lab-value lines with a non-numeric prefix and one skips an id -
    formatting issues the README acknowledges, kept as in the original data).
    ASSUMPTION: P#1 says each line has "a pipe character" after the sentence ID, but the P#2 example printed in the paper
    shows the 'Sentences' column format with a space, and the shared task fed that column to participants; the space format
    is therefore the default (LINE_FORMAT = "space"). LINE_FORMAT = "pipe" rewrites "<id> <sentence>" -> "<id>|<sentence>".
  * temperature 0 (not reported -> deterministic default, ANALYSIS_PLAN section 3), max_tokens 300 (not reported; the
    longest reference correction is 296 characters, so the cap only trims explanations), no seed parameter, no top_p.
  * 3 replicate passes (seed_idx 0-2) over the 597 notes = 1,791 calls; the judgment uses the median over passes.
  * reply parsing per P#1: 'CORRECT' -> flag 0 / sentence -1; a leading integer -> flag 1 / that sentence id, remainder =
    correction. Anything else is 'unparsed' and counted as a missing prediction (wrong on both subtasks), which is how the
    shared-task scorer treats invalid submission lines. A lenient re-parse (CORRECT anywhere, 'sentence N', first integer)
    is reported as a sensitivity number only. The paper applied "minimal automatic post-processing" to Phi-3 and Claude,
    none to the GPT models.
Scoring re-implements compute_accuracy() of MEDIQA-CORR-2024/evaluation/mediqa-corr-2024-eval-script-1-acc-rouge.ipynb.py
(the script cannot be imported: it runs its own driver at import time and needs the 'rouge' package):
  error-flag accuracy     = share of the 597 notes whose predicted flag equals the reference flag
  error-sentence accuracy = share whose predicted sentence id equals the reference id; notes WITHOUT error have reference
                            id -1, so a 'CORRECT' reply on a correct note is a hit on both subtasks (that is how the paper
                            counts the 'no error' notes); a wrong flag is a miss on both.
  --check exec's the original parse/accuracy functions from that file and confirms they give the same numbers as this
  scorer on the released baseline run (evaluation/data/baseline-run-1.txt vs the MS validation set). Neither repository
  nor the paper release contains GPT-4o (or any LLM) outputs, so Table 2 cannot be re-scored from originals.
  Correction metrics (ROUGE-1, BERTScore, BLEURT, AggregateScore, MIST) are out of scope (card: direction only).
Data quirk: the test CSV holds 597 MS rows plus 328 all-blank rows (UW placeholders), which makes pandas read the flag
and sentence-id columns as floats; the original scorer compares str() values, so ids are normalised to int here.

Judgment (automatic rule, ANALYSIS_PLAN section 1 as instantiated in the card): with the median over the three passes,
  survived  both accuracies within +/- 0.05 of the Table 2 'GPT-4o' cell (bootstrap 95% CI over notes reported alongside)
            and GPT-4o still below the stronger doctor on the same subset (Table 3, Doctor #1 MS: 0.8125 / 0.7670)
  partial   still below that doctor, but at least one accuracy off by more than 0.05
  dead      GPT-4o at or above Doctor #1's MS accuracies (the 'outperformed by medical doctors' direction fails)
  every label carries the suffix '[subset: MS 597/925]'.

  python adapters/medec_W4412887943.py --check
  python adapters/medec_W4412887943.py --dry-run
  python adapters/medec_W4412887943.py --run        # cap $12
  python adapters/medec_W4412887943.py --analyze
"""
import argparse, contextlib, io, json, re, sys, warnings
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, run_battery  # noqa: E402

HALF = HERE.parent.parent
EXT = HALF / "external" / "repos" / "W4412887943"
DATA = EXT / "abachaa__MEDEC" / "MEDEC-MS"
TEST_CSV = DATA / "MEDEC-MS-TestSet-with-GroundTruth-and-ErrorType.csv"
VAL_CSV = DATA / "MEDEC-MS-ValidationSet-with-GroundTruth-and-ErrorType.csv"
EVAL_PY = EXT / "abachaa__MEDIQA-CORR-2024" / "evaluation" / "mediqa-corr-2024-eval-script-1-acc-rouge.ipynb.py"
BASELINE_RUN = EXT / "abachaa__MEDIQA-CORR-2024" / "evaluation" / "data" / "baseline-run-1.txt"
CARD = "W4412887943"
RUN = HALF / "runs" / CARD / "baseline_alive"
MODEL, CAP, N_SEEDS = "gpt-4o-2024-05-13", 12.0, 3
PARAMS = {"temperature": 0.0, "max_tokens": 300}
LINE_FORMAT = "space"      # "space": dataset lines "<id> <sentence>" verbatim | "pipe": "<id>|<sentence>" as P#1 describes
N_BOOT, TOL, N_TEST_FULL = 1000, 0.05, 925
EXPECTED_OUT_TOKENS = 40   # sentence id + one corrected sentence (~25 tokens) with some slack; used for the calibrated estimate

P1 = ("The following is a medical narrative about a patient. You are a skilled medical doctor reviewing the clinical text. "
      "The text is either correct or contains one error. The text has one sentence per line. Each line starts with the "
      "sentence ID, followed by a pipe character then the sentence to check. Check every sentence of the text. If the text "
      "is correct return the following output: CORRECT. If the text has a medical error related to treatment, management, "
      "cause, or diagnosis, return the sentence id of the sentence containing the error, followed by a space, and then a "
      "corrected version of the sentence. Finding and correcting the error requires medical knowledge and reasoning.")

ORIGINAL = {  # paper Table 2 (all 925 test notes) and Table 3 (MS / UW subsets)
    "gpt4o_P1": {"err_flag_acc": 0.6584, "err_sentence_acc": 0.5665},        # primary cell
    "gpt4o_mini_P1": {"err_flag_acc": 0.6086, "err_sentence_acc": 0.4757},   # alternative cell
    "doctor1": {"err_flag_acc": 0.7961, "err_sentence_acc": 0.6588, "ms_err_flag_acc": 0.8125, "ms_err_sentence_acc": 0.7670},
    "doctor2": {"err_flag_acc": 0.7161, "err_sentence_acc": 0.6677, "ms_err_flag_acc": 0.6890, "ms_err_sentence_acc": 0.6459},
}
ERROR_TYPES = ["diagnosis", "management", "treatment", "pharmacotherapy", "causalOrganism"]


# ----------------------------------------------------------------------------- data + prompts
def load_notes(csv=TEST_CSV):
    """MS notes from a MEDEC ground-truth CSV. The test CSV carries 328 all-blank rows (UW placeholders): dropped."""
    df = pd.read_csv(csv).dropna(how="all")
    notes = []
    for _, r in df.iterrows():
        notes.append({"id": str(r["Text ID"]), "flag": int(r["Error Flag"]), "sent_id": int(r["Error Sentence ID"]),
                      "error_type": (r["Error Type"] if isinstance(r["Error Type"], str) else None),
                      "corrected": (r["Corrected Sentence"] if isinstance(r["Corrected Sentence"], str) else None),
                      "sentences": str(r["Sentences"]).replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")})
    return notes


def note_lines(note):
    lines = [l for l in note["sentences"].split("\n") if l.strip()]
    if LINE_FORMAT == "pipe":
        lines = [re.sub(r"^(\d+) ", r"\1|", l) for l in lines]
    return lines


def build_prompt(note):
    return P1 + "\n\n" + "\n".join(note_lines(note))


def build_requests(notes=None):
    notes = notes or load_notes()
    return [{"id": n["id"], "seed_idx": s,
             "meta": {"flag": n["flag"], "sent_id": n["sent_id"], "error_type": n["error_type"], "line_format": LINE_FORMAT},
             "body": {"model": MODEL, "messages": [{"role": "user", "content": build_prompt(n)}], **PARAMS}}
            for s in range(N_SEEDS) for n in notes]


# ----------------------------------------------------------------------------- parsing + scoring
def parse_reply(text, lenient=False):
    """-> (flag, sentence_id, correction, status); status in {'correct', 'error', 'unparsed'} (+ '-lenient')."""
    if not isinstance(text, str) or not text.strip():
        return None, None, None, "unparsed"
    first = next(l for l in text.strip().splitlines() if l.strip()).strip()
    if re.fullmatch(r"(?i)[\W_]*correct[\W_]*", first) or re.match(r"^-1(\s|$)", first):   # '-1' = shared-task 'no error' code
        return 0, -1, "NA", "correct"
    m = re.match(r"^[\W_]*?(\d+)\s*(.*)$", first, re.S)
    if m:
        corr = re.sub(r"^[\s:|.)\-]+", "", m.group(2)).strip()
        return 1, int(m.group(1)), corr, "error"
    if lenient:
        if re.search(r"(?i)\bcorrect\b", text) and not re.search(r"(?i)\b(error|incorrect)\b", text):
            return 0, -1, "NA", "correct-lenient"
        m = re.search(r"(?i)sentence\s*(?:id|number|#)?\s*[:#]?\s*(\d+)", text) or re.search(r"(\d+)", text)
        if m:
            return 1, int(m.group(1)), text.strip(), "error-lenient"
    return None, None, None, "unparsed"


def score(notes, preds):
    """Re-implementation of compute_accuracy() in MEDIQA-CORR-2024/evaluation/mediqa-corr-2024-eval-script-1-acc-rouge.ipynb.py:
    preds = {note id: (flag, sentence id)}; a missing prediction is a miss on both subtasks. Returns per-note 0/1 arrays."""
    flag_ok = np.array([int(n["id"] in preds and preds[n["id"]][0] == n["flag"]) for n in notes])
    sent_ok = np.array([int(n["id"] in preds and preds[n["id"]][1] == n["sent_id"]) for n in notes])
    return flag_ok, sent_ok


def boot_ci(x, rng, n_boot=N_BOOT):
    x = np.asarray(x, dtype=float)
    boots = [rng.choice(x, len(x), replace=True).mean() for _ in range(n_boot)]
    return [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]


def original_scorer():
    """The authors' parse_reference_file / parse_run_submission_file / compute_accuracy, exec'd from the repository file
    (its module level runs a driver on a relative path and imports 'rouge', so it cannot be imported)."""
    src = EVAL_PY.read_text(encoding="utf-8")
    chunk = src[src.index("def parse_reference_file"):src.index("def increment_counter")]
    ns = {"re": re, "pd": pd, "math": __import__("math"), "open": partial(open, encoding="utf-8")}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")            # '\s' in plain strings -> SyntaxWarning on 3.12+
        exec(compile(chunk, str(EVAL_PY), "exec"), ns)
    return ns


def token_counter():
    try:
        import tiktoken
        try:
            enc = tiktoken.get_encoding("o200k_base")       # gpt-4o tokenizer
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        return lambda s: len(enc.encode(s)), enc.name
    except Exception:
        return lambda s: len(s) / 4, "chars/4"


# ----------------------------------------------------------------------------- --check
def check():
    notes = load_notes()
    n = len(notes)
    flags = sum(x["flag"] for x in notes)
    print(f"MS test notes: {n} (expected 597; card test_ms 597) | with error {flags} ({flags/n:.1%}), without {n-flags}")
    types = {t: sum(x["error_type"] == t for x in notes) for t in ERROR_TYPES}
    print(f"error types: {types}")
    lens = [len(note_lines(x)) for x in notes]
    odd = [x["id"] for x in notes if [l.split(" ", 1)[0] for l in note_lines(x)] != [str(i) for i in range(len(note_lines(x)))]]
    print(f"sentences per note: mean {np.mean(lens):.1f}, max {max(lens)} | notes with irregular line ids (kept verbatim): {len(odd)} {odd}")
    ok = sum(1 for x in notes if x["flag"] == 0 or any(l.split(" ", 1)[0] == str(x["sent_id"]) for l in note_lines(x)))
    print(f"reference sentence id present in the note lines: {ok}/{n}")
    reqs = build_requests(notes)
    count, enc_name = token_counter()
    ptoks = [count(r["body"]["messages"][0]["content"]) + 8 for r in reqs[:n]]
    print(f"requests: {len(reqs)} = {n} notes x {N_SEEDS} passes | model {MODEL} | params {PARAMS} | line format '{LINE_FORMAT}'")
    print(f"prompt tokens ({enc_name}): P#1 {count(P1)}, per request mean {np.mean(ptoks):.0f}, max {max(ptoks)}")
    print("\n--- example request body (first note) ---")
    print(json.dumps(reqs[0]["body"], indent=1, ensure_ascii=False))
    print("--- end example ---\n")
    # reply parser self-test
    cases = [("CORRECT", (0, -1)), ("CORRECT.", (0, -1)), ("**CORRECT**", (0, -1)), ("10 Prednisone is given.", (1, 10)),
             ("10: Prednisone is given.", (1, 10)), ("3 | The patient has ...", (1, 3)), ("The text is correct.", (None, None)),
             ("Sentence 5 contains an error: ...", (None, None))]
    for txt, exp in cases:
        f, s, _, st = parse_reply(txt)
        assert (f, s) == exp, (txt, f, s, st)
    print(f"reply parser self-test: {len(cases)} cases ok (strict); lenient fallback exists for sensitivity only")
    # chance references on this subset
    always_correct = (n - flags) / n
    print(f"chance references (MS subset): always 'CORRECT' -> flag acc {always_correct:.4f}, sentence acc {always_correct:.4f}; "
          f"always flag=1 -> flag acc {flags/n:.4f}")
    # scorer cross-check on the released baseline run (MS validation set)
    print("\nOriginal GPT-4o outputs/predictions: NONE in abachaa/MEDEC, abachaa/MEDIQA-CORR-2024 or the paper release "
          "(Table 5 quotes three example corrections only) -> Table 2 cannot be re-scored from originals.")
    print("Scorer cross-check on the only released run, evaluation/data/baseline-run-1.txt vs the MS validation set:")
    ns = original_scorer()
    ref_corr, ref_flags, ref_sid = ns["parse_reference_file"](str(VAL_CSV))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cand_corr, cand_flags, cand_sid = ns["parse_run_submission_file"](str(BASELINE_RUN))
    invalid = buf.getvalue().count("Invalid line")
    orig = ns["compute_accuracy"](ref_flags, ref_sid, cand_flags, cand_sid)
    val = load_notes(VAL_CSV)
    preds = {t: (int(cand_flags[t]), int(cand_sid[t])) for t in cand_flags}
    f_ok, s_ok = score(val, preds)
    # the same predictions pushed through the reply parser (synthetic P#1-style replies) must give identical numbers
    replies = {t: ("CORRECT" if preds[t][0] == 0 else f"{preds[t][1]} {cand_corr[t]}") for t in preds}
    preds2 = {t: parse_reply(r)[:2] for t, r in replies.items()}
    f_ok2, s_ok2 = score(val, preds2)
    print(f"  validation notes {len(val)}, baseline lines parsed {len(preds)} (invalid lines skipped by the original parser: {invalid})")
    print(f"  original functions : flag acc {orig['Error Flags Accuracy']:.4f}  sentence acc {orig['Error Sentence Detection Accuracy']:.4f}")
    print(f"  this scorer        : flag acc {f_ok.mean():.4f}  sentence acc {s_ok.mean():.4f}")
    print(f"  via parse_reply    : flag acc {f_ok2.mean():.4f}  sentence acc {s_ok2.mean():.4f}")
    match = (abs(orig["Error Flags Accuracy"] - f_ok.mean()) < 1e-12 and abs(orig["Error Sentence Detection Accuracy"] - s_ok.mean()) < 1e-12
             and abs(f_ok2.mean() - f_ok.mean()) < 1e-12 and abs(s_ok2.mean() - s_ok.mean()) < 1e-12)
    print(f"  match: {match}")
    print("\nTable 2 cells (925 notes): GPT-4o 0.6584 / 0.5665 (primary) | GPT-4o-mini 0.6086 / 0.4757 (alternative) | "
          "doctors 0.7961 / 0.6588 and 0.7161 / 0.6677; Table 3 MS-only doctors 0.8125 / 0.7670 and 0.6890 / 0.6459")
    return match


# ----------------------------------------------------------------------------- --dry-run
def dry_run():
    reqs = build_requests()
    est = run_battery(reqs, RUN, CAP, dry_run=True, label=CARD)
    count, enc_name = token_counter()
    ptok = sum(count(r["body"]["messages"][0]["content"]) + 8 for r in reqs)
    from battery import pricing_for
    p = pricing_for(MODEL)
    cal = ptok / 1e6 * p["input"] + len(reqs) * EXPECTED_OUT_TOKENS / 1e6 * p["output"]
    worst = ptok / 1e6 * p["input"] + len(reqs) * PARAMS["max_tokens"] / 1e6 * p["output"]
    print(f"[calibrated] {len(reqs)} calls; prompt tokens {ptok/1e3:.0f}k ({enc_name}) + ~{EXPECTED_OUT_TOKENS} completion tokens/call "
          f"-> ~${cal:.2f}; worst case at max_tokens={PARAMS['max_tokens']} ~${worst:.2f}; recommended cap ${CAP:.0f}")
    return est, cal


# ----------------------------------------------------------------------------- --analyze
def judge(med_flag, med_sent):
    o, d1, d2 = ORIGINAL["gpt4o_P1"], ORIGINAL["doctor1"], ORIGINAL["doctor2"]
    within = abs(med_flag - o["err_flag_acc"]) <= TOL and abs(med_sent - o["err_sentence_acc"]) <= TOL
    below_d1 = med_flag < d1["ms_err_flag_acc"] and med_sent < d1["ms_err_sentence_acc"]
    below_d2 = med_flag < d2["ms_err_flag_acc"] and med_sent < d2["ms_err_sentence_acc"]
    label = "사망 (dead)" if not below_d1 else ("생존 (survived)" if within else "부분 생존 (partial)")
    return label + " [subset: MS 597/925]", {"within_0.05_of_table2_gpt4o": within, "below_doctor1_ms": below_d1,
                                             "below_doctor2_ms": below_d2}


def analyze():
    notes = load_notes()
    res = load_results(RUN)
    if not res:
        print(f"no archived calls in {RUN / 'calls.jsonl'}")
        return None
    rng = np.random.default_rng(0)
    per_seed, rows_pred, status_counts = {}, [], {}
    flag_mat, sent_mat = [], []
    for s in range(N_SEEDS):
        preds, preds_len, missing = {}, {}, 0
        for n in notes:
            r = res.get((n["id"], s))
            if not r:
                missing += 1
                continue
            try:
                choice = r["response"]["choices"][0]
                text, finish_reason = choice["message"]["content"], choice.get("finish_reason")
            except (KeyError, IndexError, TypeError):
                text, finish_reason = None, None
            f, sid, corr, st = parse_reply(text)
            fl, sl, _, stl = parse_reply(text, lenient=True)
            status_counts[st] = status_counts.get(st, 0) + 1
            if st != "unparsed":
                preds[n["id"]] = (f, sid)
            if stl != "unparsed":
                preds_len[n["id"]] = (fl, sl)
            rows_pred.append({"id": n["id"], "seed_idx": s, "ref_flag": n["flag"], "ref_sent_id": n["sent_id"], "pred_flag": f,
                              "pred_sent_id": sid, "status": st, "reply": (text or "")[:300].replace("\n", " "), "finish_reason": finish_reason})
        if len(preds) + missing == 0:
            continue
        f_ok, s_ok = score(notes, preds)
        fl_ok, sl_ok = score(notes, preds_len)
        flag_mat.append(f_ok)
        sent_mat.append(s_ok)
        errs = [n for n in notes if n["flag"] == 1]
        recall = {t: {"flag": float(np.mean([preds.get(n["id"], (0, -1))[0] == 1 for n in errs if n["error_type"] == t])),
                      "sentence": float(np.mean([preds.get(n["id"], (0, -1))[1] == n["sent_id"] for n in errs if n["error_type"] == t]))}
                  for t in ERROR_TYPES}
        per_seed[s] = {"n_answered": len(notes) - missing, "n_missing_calls": missing, "n_unparsed": len(notes) - missing - len(preds),
                       "err_flag_acc": float(f_ok.mean()), "err_flag_acc_ci95": boot_ci(f_ok, rng),
                       "err_sentence_acc": float(s_ok.mean()), "err_sentence_acc_ci95": boot_ci(s_ok, rng),
                       "lenient_err_flag_acc": float(fl_ok.mean()), "lenient_err_sentence_acc": float(sl_ok.mean()),
                       "predicted_error_rate": float(np.mean([preds.get(n["id"], (None, None))[0] == 1 for n in notes])),
                       "recall_by_error_type": recall}
    if not per_seed:
        print("no complete pass found")
        return None
    F, S = np.array(flag_mat), np.array(sent_mat)                 # passes x notes
    med_flag, med_sent = float(np.median(F.mean(axis=1))), float(np.median(S.mean(axis=1)))
    pooled_flag, pooled_sent = F.mean(axis=0), S.mean(axis=0)       # per-note mean over passes
    ci_flag, ci_sent = boot_ci(pooled_flag, rng), boot_ci(pooled_sent, rng)
    o, alt = ORIGINAL["gpt4o_P1"], ORIGINAL["gpt4o_mini_P1"]
    rows = {}
    for key, med, ci, mat in (("err_flag_acc", med_flag, ci_flag, F), ("err_sentence_acc", med_sent, ci_sent, S)):
        rows[key] = {"value": round(med, 4), "per_pass": [round(float(v), 4) for v in mat.mean(axis=1)], "pooled_mean": round(float(mat.mean()), 4),
                     "ci95_pooled": [round(v, 4) for v in ci], "orig": o[key], "delta": round(med - o[key], 4),
                     "within_0.05": bool(abs(med - o[key]) <= TOL), "orig_inside_ci": bool(ci[0] <= o[key] <= ci[1]),
                     "alt_orig_gpt4o_mini": alt[key], "alt_delta": round(med - alt[key], 4), "alt_within_0.05": bool(abs(med - alt[key]) <= TOL),
                     "alt_orig_inside_ci": bool(ci[0] <= alt[key] <= ci[1])}
    pass_agreement = float(np.mean([len({(r["pred_flag"], r["pred_sent_id"]) for r in rows_pred if r["id"] == n["id"]}) == 1 for n in notes]))
    label, flags = judge(med_flag, med_sent)
    budget = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    served = sorted({r.get("model_served") for r in res.values() if r.get("model_served")})
    n_fp = len({r.get("system_fingerprint") for r in res.values() if r.get("system_fingerprint")})
    n_unparsed = sum(v["n_unparsed"] for v in per_seed.values())
    finish = {}
    for r in rows_pred:
        finish[r["finish_reason"]] = finish.get(r["finish_reason"], 0) + 1
    note = (f"MS subset only (597/925 notes; Table 2 is on all 925 and has no MS-only GPT-4o cell). Median over {len(per_seed)} passes: "
            f"flag {med_flag:.4f} (Table 2 GPT-4o {o['err_flag_acc']}, delta {med_flag - o['err_flag_acc']:+.4f}), sentence {med_sent:.4f} "
            f"(Table 2 {o['err_sentence_acc']}, delta {med_sent - o['err_sentence_acc']:+.4f}); alternative GPT-4o-mini cell "
            f"{alt['err_flag_acc']} / {alt['err_sentence_acc']}. Doctors on the MS subset (Table 3): 0.8125 / 0.7670 and 0.6890 / 0.6459. "
            f"Unparsed replies {n_unparsed}/{len(rows_pred)}; identical (flag, sentence) prediction across passes for {pass_agreement:.1%} of notes.")
    meta = {"card_id": CARD, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
            "target_paper": {"title": "MEDEC: A Benchmark for Medical Error Detection and Correction in Clinical Notes",
                             "repo": "https://github.com/abachaa/MEDEC (data) + https://github.com/abachaa/MEDIQA-CORR-2024 (scorer)",
                             "repo_commit": "MEDEC e9173f861b39706946b6a127394992c00535b1e3; MEDIQA-CORR-2024 4b87cb01c34d22bdef2423206305b2bedb1fe893",
                             "original_source": "Table 2 row 'GPT-4o' (P#1, 925 notes): error-flag accuracy 0.6584, error-sentence accuracy 0.5665; "
                                                "row 'GPT-4o-mini' 0.6086 / 0.4757 kept as the alternative cell (Section 5.1 snapshot ambiguity)"},
            "generation": {"model_requested": MODEL, "model_served": served, "n_fingerprints": n_fp,
                           "parameters": f"temperature 0, max_tokens {PARAMS['max_tokens']} (both unreported in the paper), no system prompt, "
                                         f"user = P#1 verbatim (Section 4) + blank line + the note's 'Sentences' column ('{LINE_FORMAT}' line format)",
                           "battery": f"597 MS test notes x {N_SEEDS} passes = {len(notes) * N_SEEDS} calls; scorer = compute_accuracy() of "
                                      "MEDIQA-CORR-2024/evaluation (re-implemented, cross-checked on the released baseline run)"},
            "results": {"rows": rows, "per_pass": {str(k): v for k, v in per_seed.items()}, "judgment_flags": flags,
                        "reply_status_counts": status_counts, "finish_reasons": finish, "subset": "MS 597/925",
                        "chance_always_correct": round(sum(1 for n in notes if n["flag"] == 0) / len(notes), 4),
                        "cost_usd": round(budget.get("cost_usd", 0.0), 3), "calls": budget.get("calls", len(res)), "errors": budget.get("errors", 0),
                        "judgment": label,
                        "judged_by": "automatic rule per ANALYSIS_PLAN §1 as instantiated in the card (both accuracies within +/-0.05 of Table 2 "
                                     "'GPT-4o' and still below Doctor #1 on the MS subset); human double-coding pending",
                        "note": note},
            "reproducibility_frictions_observed": [
                "the repositories hold the data and the shared-task scorer only; the prompting/post-processing code is not released, the prompt is verbatim in the paper",
                "the paper's only dated OpenAI snapshot, gpt-4o-2024-05-13, is attached to 'GPT-4o-mini' in Section 5.1; which Table 2 row it produced is ambiguous (primary cell 'GPT-4o' by decision)",
                "generation parameters (temperature, max tokens, seed) are not reported; temperature 0 and max_tokens 300 assumed",
                "328 of the 925 test notes (UW) are under a Data Use Agreement; only the 597 MS notes were run and Table 2 has no MS-only GPT-4o cell",
                "P#1 describes pipe-delimited lines but the dataset (and the paper's P#2 example) use '<id> <sentence>'; the dataset format was sent",
                "the public test CSV pads the 328 UW notes with blank rows, which turns the flag/sentence-id columns into floats; the original scorer compares str() values and needs int normalisation",
                "seven MS test notes contain lab-value lines with a non-numeric prefix and one skips a sentence id (formatting issues acknowledged in the README); sent verbatim",
                f"{n_unparsed} of {len(rows_pred)} replies did not follow the 'CORRECT' / '<id> <sentence>' format and were scored as missing predictions, as the shared-task scorer does",
            ]}
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "result.json").write_text(json.dumps({"per_pass": per_seed, "rows": rows, "status_counts": status_counts}, indent=2), encoding="utf-8")
    pd.DataFrame(rows_pred).to_csv(RUN / "predictions.tsv", sep="\t", index=False)
    (RUN.parent / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    for s, v in per_seed.items():
        print(f"pass {s}: flag {v['err_flag_acc']:.4f} {v['err_flag_acc_ci95']}  sentence {v['err_sentence_acc']:.4f} {v['err_sentence_acc_ci95']}  "
              f"unparsed {v['n_unparsed']}  missing {v['n_missing_calls']}  predicted-error rate {v['predicted_error_rate']:.3f}")
    for k, r in rows.items():
        print(f"{k}: median {r['value']} (Table 2 GPT-4o {r['orig']}, delta {r['delta']:+.4f}, within 0.05 {r['within_0.05']}, inside CI {r['orig_inside_ci']}; "
              f"GPT-4o-mini {r['alt_orig_gpt4o_mini']} within 0.05 {r['alt_within_0.05']})  pooled CI {r['ci95_pooled']}")
    print(f"judgment: {label} | flags {flags} | served {served} fingerprints {n_fp} | cost ${meta['results']['cost_usd']}")
    return meta


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
    ap.add_argument("--cap", type=float, default=CAP)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.check:
        check()
    if a.dry_run:
        dry_run()
    if a.run:
        run_battery(build_requests(), RUN, a.cap, workers=a.workers, label=CARD)
    if a.analyze:
        analyze()


if __name__ == "__main__":
    main()
