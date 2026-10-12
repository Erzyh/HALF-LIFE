"""Claim-level reading of the largest successor moves (provisional; the three-coder judgement replaces it).

A deviated class says that the reported number did not carry over to the successor; it does not say whether the paper's
claim built on that number still stands. This table reads the claim for a rule-selected set of cases: the five
repository-based papers run on the designated replacement (Table S32) and, among the scorable prompt-level results on the
designated replacement (Table S9), the three largest upward and the three largest downward moves from the reported value.
For each case: the quantity, the reported value, the pre-retirement baseline, the successor value, the move in points on
the paper's scale, the kind of claim the paper builds on the number, and a one-sentence reading of what the successor
value does to that claim. The reading is the first author's provisional one and is replaced by the blinded three-coder
judgement of direction, significance and magnitude (Methods, Judgement of survival). Writes data/claim_level_cases.csv.
No API calls.
"""
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]

READINGS = {
    # repository-based (Table S32)
    "W7171749161": ("effect", "Tag questions shift the model's agreement (reported effect -0.075; pre-retirement -0.102). On the successor the effect is -0.181: same direction, twice the size. The claim holds and is larger.", "holds, larger"),
    "W4404781910": ("phenomenon", "A judge model falls for six evaluation biases (EvalBiasBench accuracy 86.9%, chance-level 50% on empty references). The successor scores 100% on five of six bias types and 98.1% overall: the biases the paper documents are no longer measurable on it.", "vanishes (ceiling)"),
    "W7144391134": ("effect", "In-context examples lift a weak zero-shot property predictor (r 0.41 zero-shot to 75.6 with 1,000 examples). The successor predicts at r 0.95 with no examples and 97.5 with them: the premise of a weak zero-shot predictor and the in-context gain both disappear.", "vanishes"),
    "W4416074906": ("effect", "Persona prompts change the misalignment score (0.21 to 0.25 across personas, row mean 0.222). The successor gives 0.208 to 0.250 and a row mean of 0.222, every cell inside the interval. The claim holds.", "holds"),
    "W4412887943": ("comparison", "The model detects clinical errors less accurately than two doctors (flag accuracy 0.658). The successor reaches 0.752: still below the first doctor, now above the second. The ranking the paper reports partly reverses.", "partly reverses"),
    # prompt-level, largest moves (Table S9, designated replacement)
    "W4403882451": ("limitation", "GPT-4 Turbo solves 40% of Blocksworld planning instances, used to argue that language models cannot plan. The successor solves 100%. The limitation the paper diagnoses does not apply to the successor.", "reverses"),
    "W4403758464": ("limitation", "The same Blocksworld result (40%) frames the question whether reasoning models can plan where language models cannot. The successor solves 100%: the contrast the paper draws is gone.", "reverses"),
    "W4415270561": ("limitation", "A small model applies unified diffs correctly in 38% of cases, a benchmark the paper presents as hard. The successor applies 89% correctly; the benchmark's difficulty, as measured on the named model, does not carry over.", "largely reverses"),
    "W4416683695": ("effect", "The model prefers its own resume summaries over human-written ones in 93% of comparisons (self-preference bias). The pre-retirement re-run already gave 14.8 and the successor 13.2: the reported effect was not reproduced on the pinned model, and the successor adds nothing to that.", "not reproduced before retirement; unchanged"),
    "W4404573318": ("phenomenon", "A trading agent misappropriates customer funds in 41% of runs (35% on the pinned model). The successor never does (0 of 500). The misconduct the paper measures vanishes on the replacement.", "vanishes"),
    "W7166799942": ("level", "Text-only emotion recognition accuracy of 42.45% on MELD. The pre-retirement re-run gave 13.2 and the successor 5.7, because the successor answers with emotion words outside the label set; the number was not reproduced before retirement and the successor's replies do not fit the paper's label scheme (Table S33).", "not reproduced before retirement; format"),
}


def main():
    rows = []
    ta = pd.read_csv(HALF / "data" / "tiera_successor_claims.csv", encoding="utf-8-sig")
    for wid in ("W7171749161", "W4404781910", "W7144391134", "W4416074906", "W4412887943"):
        sub = ta[ta.wid == wid]
        head = sub.iloc[0]
        kind, reading, status = READINGS[wid]
        rows.append({"wid": wid, "design": "repository-based", "selection": "all five successor runs", "quantity": head.claim.split(":")[1].strip() if ":" in head.claim else head.claim,
                     "n_claims": len(sub), "reported": head.original, "pre_retirement": head.pre_retirement_rerun, "successor": head.successor,
                     "move_pts": head.successor_minus_original_pts, "classes": ", ".join(f"{k} {v}" for k, v in sub.class_vs_original.value_counts().items()),
                     "claim_kind": kind, "provisional_reading": reading, "status": status})
    p3 = pd.read_csv(HALF / "data" / "p3_summary.csv", encoding="utf-8-sig")
    v = p3[(p3.arm == "vendor") & (p3.class_vs_original.isin(["재현", "근접", "편차"]))].copy()
    up = v.sort_values("delta_vs_original_pts", ascending=False).head(3)
    down = v.sort_values("delta_vs_original_pts").head(3)
    for lab, part in (("three largest upward moves", up), ("three largest downward moves", down)):
        for r in part.itertuples(index=False):
            kind, reading, status = READINGS[r.wid]
            rows.append({"wid": r.wid, "design": "prompt-level", "selection": lab, "quantity": r.metric, "n_claims": 1, "reported": r.original,
                         "pre_retirement": round(float(r.baseline), 3), "successor": round(float(r.arm_value), 3), "move_pts": round(float(r.delta_vs_original_pts), 1),
                         "classes": r.class_vs_original, "claim_kind": kind, "provisional_reading": reading, "status": status})
    df = pd.DataFrame(rows)
    df.to_csv(HALF / "data" / "claim_level_cases.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 230, "display.max_columns", 20, "display.max_colwidth", 40):
        print(df.drop(columns=["provisional_reading"]).to_string(index=False))
    print(df.status.value_counts().to_dict())


if __name__ == "__main__":
    main()
