"""Card W7140135941 - Knowing When to Abstain: Medical LLMs Under Clinical Uncertainty (sravanthi6m/MedAbstain).

Claim re-measured for gpt-4.1-nano-2025-04-14 on MedQA (1,007 items; Table 6 zero-shot rows, no CoT):
  NA  (no abstention option)            acc 0.5404  LAC 3.80  APS 4.24
  A   (abstention option added)         acc 0.4099  LAC 4.21  APS 4.90  abstention rate 0.0
  NAP (perturbed question)              acc 0.4511  LAC 3.76  APS 4.23
  AP  (perturbed + abstention option)   acc 0.3688  LAC 4.51  APS 5.04  abstention rate 0.0
and Table 5 (CoT prompt with max_tokens=1): NA 0.2496 / LAC 5.0, A 0.227 / LAC 6.0, AP 0.227 / LAC 6.0.

Protocol copied from run_experiment.py + prompts/prompt_helpers.py (_shared) + models/openai_model.py:
single user message, temperature 0, max_tokens 1, logprobs with top_logprobs = number of options;
option logprobs read from the first token's top list, missing options imputed at (min - 5).
Accuracy and conformal set sizes are computed on the 70% test split after a 30% calibration split
(sklearn train_test_split, random_state 42 as in utils.load_and_split_jsonl); alpha = 0.1.
Few-shot (dynamic kNN with text-embedding-ada-002) conditions are out of scope for this run.

  python adapters/medabstain_W7140135941.py --dry-run
  python adapters/medabstain_W7140135941.py --run        # cap $5
  python adapters/medabstain_W7140135941.py --analyze
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, run_battery  # noqa: E402

HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / "W7140135941" / "sravanthi6m__MedAbstain"
RUN = HALF / "runs" / "W7140135941" / "baseline_alive"
MODEL, CAP, ALPHA, CAL_RATIO = "gpt-4.1-nano-2025-04-14", 5.0, 0.1, 0.3
VARIANTS = {"NA": "medqa_1_test_noabst.json", "A": "medqa_1_test_randabst.json",
            "NAP": "perturbed_medqa_1_test_noabst.json", "AP": "perturbed_medqa_1_test_randabst.json"}
ABSTENTION_STRING = "I am unable to answer this question for certain reasons."
SHARED_ZERO = ("The following is a multiple-choice question with {num_choices} potential answers. "
               "Only one of these options is correct. Please make your best effort and select the correct answer. "
               "You only need to output the option.\n\n")
SHARED_COT = ("The following is a multiple-choice question with {num_choices} potential answers. Only one of these options is correct. "
              "Please reason step-by-step and select the correct answer. You only need to output the option.\n\n")
ORIGINAL = {
    "noCoT": {"NA": {"acc": 0.5404, "lac": 3.8014, "aps": 4.2426}, "A": {"acc": 0.4099, "lac": 4.2057, "aps": 4.9021, "abstention": 0.0},
              "NAP": {"acc": 0.4511, "lac": 3.7603, "aps": 4.227}, "AP": {"acc": 0.3688, "lac": 4.5092, "aps": 5.0411, "abstention": 0.0}},
    "CoT": {"NA": {"acc": 0.2496, "lac": 5.0, "aps": 4.8014}, "A": {"acc": 0.227, "lac": 6.0, "aps": 5.5887, "abstention": 0.0},
            "AP": {"acc": 0.227, "lac": 6.0, "aps": 5.5887, "abstention": 0.0}},
}


def load(variant):
    return json.loads((REPO / "data" / VARIANTS[variant]).read_text(encoding="utf-8"))


def build_prompt(ex, cot):
    head = (SHARED_COT if cot else SHARED_ZERO).format(num_choices=len(ex["choices"]))
    body = "Question: " + ex["question"] + "\nChoices:\n" + "".join(f"{k}. {v}\n" for k, v in ex["choices"].items()) + "Answer:"
    return head + body


def build_requests():
    reqs = []
    for variant in VARIANTS:
        for cot in (False, True):
            if cot and variant == "NAP":
                continue        # Table 5 reports NA, A and AP only
            for ex in load(variant):
                choices = list(ex["choices"].keys())
                reqs.append({"id": f"{variant}_{'CoT' if cot else 'noCoT'}_{ex['id']}", "seed_idx": 0,
                             "meta": {"variant": variant, "cot": cot, "item": ex["id"]},
                             "body": {"model": MODEL, "messages": [{"role": "user", "content": build_prompt(ex, cot)}],
                                      "temperature": 0.0, "max_tokens": 1, "logprobs": True, "top_logprobs": len(choices)}})
    return reqs


def option_logprobs(resp, choices):
    try:
        top = resp["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    except (KeyError, IndexError, TypeError):
        top = []
    raw = {e["token"].strip(): e["logprob"] for e in top if e["token"].strip() in choices}
    floor = (min(raw.values()) - 5) if raw else -100.0
    return np.array([raw.get(c, floor) for c in choices], dtype=float)


def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()


def conformal_sizes(rows, seed):
    """rows: list of (id, choices, logits, answer) in dataset order. Returns (lac, aps, acc, abst, n_test, correct_flags)."""
    cal, test = train_test_split(rows, train_size=CAL_RATIO, random_state=seed)
    # LAC
    cal_scores = []
    for _, ch, lg, ans in cal:
        if ans in ch:
            cal_scores.append(1 - softmax(lg)[ch.index(ans)])
    n = len(cal)
    q_lac = np.quantile(cal_scores, np.ceil((n + 1) * (1 - ALPHA)) / n, method="higher")
    # APS
    cal_scores = []
    for _, ch, lg, ans in cal:
        p = softmax(lg)
        pi = np.argsort(p)[::-1]
        cum = np.take_along_axis(p, pi, axis=0).cumsum()
        cum_r = np.take_along_axis(cum, pi.argsort(), axis=0)
        if ans in ch:
            cal_scores.append(cum_r[ch.index(ans)])
    q_aps = np.quantile(cal_scores, np.ceil((n + 1) * (1 - ALPHA)) / n, method="higher")
    lac_sizes, aps_sizes, correct = [], [], []
    for _, ch, lg, ans in test:
        p = softmax(lg)
        ps = [o for o, pp in zip(ch, p) if pp >= 1 - q_lac] or [ch[int(np.argmax(p))]]
        lac_sizes.append(len(ps))
        pi = np.argsort(p)[::-1]
        cum = np.take_along_axis(p, pi, axis=0).cumsum()
        k = int(np.searchsorted(cum, q_aps, side="left")) + 1
        aps_sizes.append(min(k, len(ch)))
        pred = ch[int(np.argmax(p))]
        correct.append(int(pred == ans))
    return float(np.mean(lac_sizes)), float(np.mean(aps_sizes)), float(np.mean(correct)), len(test), correct


def analyze():
    res = load_results(RUN)
    out = {"card": "W7140135941", "model": MODEL, "n_calls": len(res), "original": ORIGINAL, "reexecution": {},
           "served": {"models": sorted({r.get("model_served") for r in res.values() if r.get("model_served")}),
                      "n_fingerprints": len({r.get("system_fingerprint") for r in res.values() if r.get("system_fingerprint")})}}
    rng = np.random.default_rng(0)
    for variant in VARIANTS:
        data = load(variant)
        for cot in (False, True):
            key = "CoT" if cot else "noCoT"
            rows, abst_flags, missing = [], [], 0
            for ex in data:
                r = res.get((f"{variant}_{key}_{ex['id']}", 0))
                if not r:
                    missing += 1
                    continue
                ch = list(ex["choices"].keys())
                lg = option_logprobs(r["response"], ch)
                pred = ch[int(np.argmax(lg))]
                abst_opt = next((k for k, v in ex["choices"].items() if ABSTENTION_STRING in v), None)
                abst_flags.append(int(abst_opt is not None and pred == abst_opt))
                rows.append((ex["id"], ch, lg, ex["answer"]))
            if not rows:
                continue
            per_seed = {}
            for seed in (42, 0, 1):
                lac, aps, acc, n_test, correct = conformal_sizes(rows, seed)
                boots = [np.mean(rng.choice(correct, len(correct), replace=True)) for _ in range(2000)]
                per_seed[seed] = {"acc": acc, "acc_ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                                  "lac": lac, "aps": aps, "n_test": n_test}
            all_acc = float(np.mean([int(ch[int(np.argmax(lg))] == ans) for _, ch, lg, ans in rows]))
            out["reexecution"].setdefault(key, {})[variant] = {
                "split42": per_seed[42], "other_splits": {str(s): per_seed[s] for s in (0, 1)},
                "acc_all_items": all_acc, "abstention_rate": float(np.mean(abst_flags)), "n_items": len(rows), "missing": missing}
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "result.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for key in ("noCoT", "CoT"):
        for variant, v in out["reexecution"].get(key, {}).items():
            o = ORIGINAL[key].get(variant, {})
            s = v["split42"]
            print(f"{key:5s} {variant:3s}  acc {s['acc']:.4f} [{s['acc_ci95'][0]:.3f},{s['acc_ci95'][1]:.3f}] (orig {o.get('acc')})  "
                  f"LAC {s['lac']:.2f} (orig {o.get('lac')})  APS {s['aps']:.2f} (orig {o.get('aps')})  abst {v['abstention_rate']:.3f} (orig {o.get('abstention', '-')})  n_test {s['n_test']}")
    print("served:", out["served"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        run_battery(build_requests(), RUN, CAP, dry_run=True, label="W7140135941")
    if a.run:
        run_battery(build_requests(), RUN, CAP, workers=6, label="W7140135941")
    if a.analyze:
        analyze()


if __name__ == "__main__":
    main()
