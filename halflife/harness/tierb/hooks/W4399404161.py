r"""Hook for W4399404161 (MMLU-Pro, GPT-4-Turbo 5-shot CoT, Table 2 Overall).

load_items: Hub default/test (12,032) plus default/validation (70 = 5 exemplars per category, cot_content);
            each test row carries its category's exemplars; gold = {"answer": letter, "n_options": k}.
render:     Table 7 layout (config user_template): instruction line, five exemplars
            'Question: ..\nOptions: A. ..\nB. ..\nAnswer: Let's think step by step. .. The answer is (X).\n\n',
            then the test question with 'Answer: Let's think step by step.'
parse:      paper's extraction: 'answer is \(?([A-J])\)?', then '[aA]nswer:\s*([A-J])', else 'RANDOM'.
score:      accuracy; a 'RANDOM' prediction draws a seeded random option among the item's k options (paper fallback).
"""
import re, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tierb_runner import load_hf  # noqa: E402

SEED = 20260907


def _lettered(options):
    return "\n".join(f"{chr(65 + i)}. {o}" for i, o in enumerate(list(options)))


def load_items(cfg):
    val = load_hf("TIGER-Lab/MMLU-Pro", "default/validation")
    shots = {}
    for r in val:
        cot = str(r["cot_content"])
        cot = cot[3:] if cot.startswith("A: ") else cot
        shots.setdefault(r["category"], []).append(f"Question: {r['question']}\nOptions: {_lettered(r['options'])}\nAnswer: {cot}\n\n")
    rows = []
    for r in load_hf("TIGER-Lab/MMLU-Pro", "default/test"):
        ex = shots.get(r["category"])
        if not ex or len(ex) != 5:
            raise RuntimeError(f"category {r['category']!r} has {len(ex or [])} exemplars, expected 5")
        rows.append({"id": str(r["question_id"]), "question": r["question"], "options": list(r["options"]),
                     "category": r["category"], "few_shot_block": "".join(ex),
                     "gold": {"answer": str(r["answer"]).strip().upper(), "n_options": len(list(r["options"]))}})
    return rows


def render(cfg, row):
    t = cfg["prompt"]["user_template"]
    t = t.replace("{category}", row["category"]).replace("{few_shot_block}", row["few_shot_block"])
    t = t.replace("{question}", row["question"]).replace("{options}", _lettered(row["options"]))
    return [{"role": "user", "content": t}]


def parse(text, cfg):
    if not text:
        return "RANDOM"
    m = re.search(r"answer is \(?([A-J])\)?", text)
    if m:
        return m.group(1)
    m = re.search(r"[aA]nswer:\s*([A-J])", text)
    return m.group(1) if m else "RANDOM"


def score(preds, golds, cfg):
    rng = np.random.default_rng(SEED)
    per, n_random = [], 0
    for p, g in zip(preds, golds):
        if p == "RANDOM":
            n_random += 1
            p = chr(65 + int(rng.integers(int(g["n_options"]))))
        per.append(1.0 if p == g["answer"] else 0.0)
    print(f"[W4399404161] random fallback used for {n_random} of {len(per)} replies")
    return (sum(per) / len(per) if per else float("nan")), per


if __name__ == "__main__":
    ts = ["... The answer is (H).", "so the answer is B", "Answer: C", "I think it is D", ""]
    print([parse(t, {}) for t in ts])
    assert [parse(t, {}) for t in ts] == ["H", "B", "C", "RANDOM", "RANDOM"]
    v, per = score(["H", "B", "RANDOM"], [{"answer": "H", "n_options": 10}, {"answer": "A", "n_options": 4}, {"answer": "A", "n_options": 2}], {})
    assert per[:2] == [1.0, 0.0] and per[2] in (0.0, 1.0)
    print("ok", v, per)
