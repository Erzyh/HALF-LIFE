"""Hook W7160514285 (medical metacognition pilot, gpt-4.1-nano forced-choice accuracy, Table 2 = 0.935).

load_items -> the frozen 135-trial manifest released with the paper
              (github.com/anazz-dev/medical-llm-metacognition-benchmark,
              medical_llm_colab_run_package_v0_1/medical_llm_trial_manifest_seed1to3_v0_1.jsonl), mirrored into
              external/data/tierb_items/W7160514285/. Only the 108 trials with forced_choice_accuracy_applicable
              are kept - the 27 equivocal trials have no forced-choice gold (Sec. 2.11/3.1).
              The manifest already carries the fully rendered prompt_text of the trial's variant (P01/P02/P03), so
              the runner's user_template is just {prompt_text}.
              gold: the letter the strict JSON schema forces the model to answer with. The released runner maps the
              model's A/B through the row's option_A/option_B to AT_NCD/DRCI and compares with ground_truth_label,
              so gold = "A" when option_A names the ground-truth condition, else "B". This also covers P03, whose
              manifest field expected_choice_value holds the full label although the response schema only allows
              A or B.
No render / parse / score: {prompt_text}, output.parse "json field diagnosis" and metric accuracy are runner
facilities.
"""
import json
from pathlib import Path

MANIFEST = (Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W7160514285"
            / "medical_llm_trial_manifest_seed1to3_v0_1.jsonl")


def _letter(row):
    truth = row["ground_truth_label"]                  # AT_NCD | DRCI (equivocal rows are filtered out)
    a = str(row["option_A"]).lower()
    a_is = "AT_NCD" if "alzheimer" in a else "DRCI" if "depression" in a else None
    if a_is is None:
        raise NeedsHuman(f"cannot read option_A of {row['trial_id']}")  # noqa: F821
    return "A" if a_is == truth else "B"


def load_items(cfg):
    if not MANIFEST.exists():
        raise NeedsHuman(f"mirror the trial manifest into {MANIFEST} before --prepare")  # noqa: F821
    rows = [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(rows) != 135:
        raise NeedsHuman(f"manifest has {len(rows)} trials, expected 135")  # noqa: F821
    out = [{"id": r["trial_id"], "prompt_text": r["prompt_text"], "gold_letter": _letter(r),
            "prompt_id": r["prompt_id"], "evidence_level": r["evidence_level"],
            "information_quality": r["information_quality"], "ground_truth_label": r["ground_truth_label"]}
           for r in rows if r.get("forced_choice_accuracy_applicable")]
    if len(out) != 108:
        raise NeedsHuman(f"{len(out)} forced-choice trials, expected 108 (Sec. 3.1)")  # noqa: F821
    return out


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    from collections import Counter
    print(len(rows), "forced-choice trials")
    print("gold letters:", Counter(r["gold_letter"] for r in rows))
    print("by variant  :", Counter((r["prompt_id"][:3], r["gold_letter"], r["ground_truth_label"]) for r in rows))
    print("first id", rows[0]["id"])
    print(rows[0]["prompt_text"][:400])
