"""Hook W4416034248 (Multi-Plan, GPT-4-turbo on the Math-structured format, Table 2 planning accuracy 17.65%).

load_items -> the 204 scenarios of huggingface.co/datasets/Bllossom/Multi-Plan (single parquet, mirrored into
              external/data/tierb_items/W4416034248/). Columns: id, category, num_cities, generation_type,
              question_ko/answer_ko, question_en/answer_en, question_math/answer_math. The Math column is used
              (question_math is the mathematically structured request, answer_math is the Korean gold plan and is
              identical to answer_ko for every row). Figure 1's prompt is 1-shot ("randomly selected examples");
              the paper does not print which example, so each item gets one demonstration drawn from the other 203
              scenarios with a fixed RNG (seed 20260907) - deterministic and independent of the item order.
parse      -> the visit / fly regular expressions of Appendix F.1 in both the printed English form and the Korean
              form the Math gold plans actually use; returns the ordered event list.
score      -> accuracy: an item is correct when the event sequence, its length and every field equal the gold's
              (Appendix F.1). per_item is returned so the runner bootstraps item-level.
No render: the config's user_template with {example_task}/{example_solution}/{task} is a runner facility.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

PARQUET = (Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4416034248"
           / "train-00000-of-00001.parquet")
SEED = 20260907

# Appendix F.1 prints the English patterns; the Korean ones are the same two sentence shapes in the gold plans
# ("1-5일차: 5일간 헬싱키 방문." / "5일차: 헬싱키에서 바르셀로나로 비행.").
VISIT_EN = re.compile(r"Days? (\d+)(?:\s*[-–—]\s*(\d+))?:\s*Visit ([^\s,\.]+)\s*for (\d+)\s*days?\.?",
                      re.IGNORECASE)
FLY_EN = re.compile(r"Day (\d+):\s*Fly from ([^\s,\.]+)\s*to ([^\s,\.]+)\.?", re.IGNORECASE)
VISIT_KO = re.compile(r"(\d+)(?:\s*[-–—]\s*(\d+))?일차:\s*(\d+)일간\s*(\S+?)\s*방문\.?")
FLY_KO = re.compile(r"(\d+)일차:\s*(\S+?)에서\s*(\S+?)(?:으로|로)\s*비행\.?")


def _events(text):
    """Ordered visit/fly events of one plan, in the order they appear in the text."""
    if not text:
        return []
    hits = []
    for m in VISIT_EN.finditer(text):
        hits.append((m.start(), ("visit", m.group(1), m.group(2) or m.group(1), m.group(3), m.group(4))))
    for m in FLY_EN.finditer(text):
        hits.append((m.start(), ("fly", m.group(1), m.group(2), m.group(3))))
    for m in VISIT_KO.finditer(text):
        hits.append((m.start(), ("visit", m.group(1), m.group(2) or m.group(1), m.group(4), m.group(3))))
    for m in FLY_KO.finditer(text):
        hits.append((m.start(), ("fly", m.group(1), m.group(2), m.group(3))))
    return [e for _, e in sorted(hits, key=lambda x: x[0])]


def load_items(cfg):
    if not PARQUET.exists():
        raise NeedsHuman(f"mirror the Multi-Plan parquet into {PARQUET} before --prepare")  # noqa: F821
    df = pd.read_parquet(PARQUET)
    if len(df) != 204:
        raise NeedsHuman(f"Multi-Plan has {len(df)} rows, expected 204")  # noqa: F821
    rng = np.random.default_rng(SEED)
    shots = [int(rng.integers(0, len(df) - 1)) for _ in range(len(df))]
    rows = []
    for i, (_, r) in enumerate(df.iterrows()):
        j = shots[i] + (1 if shots[i] >= i else 0)          # any scenario except the item itself
        ex = df.iloc[j]
        rows.append({"id": str(r["id"]), "task": r["question_math"], "answer": r["answer_math"],
                     "example_task": ex["question_math"], "example_solution": ex["answer_math"],
                     "example_id": str(ex["id"])})
    return rows


def parse(text, cfg):
    ev = _events(text)
    return ev or None


def score(preds, golds, cfg):
    per = [1.0 if (p is not None and p == _events(g)) else 0.0 for p, g in zip(preds, golds)]
    return float(np.mean(per)) if per else 0.0, per


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    print(len(rows), "items; first id", rows[0]["id"], "shot id", rows[0]["example_id"])
    print("gold events[0]:", _events(rows[0]["answer"]))
    print("gold events[1]:", _events(rows[1]["answer"]))
    en = ("Days 1-5: Visit Helsinki for 5 days.\nDay 5: Fly from Helsinki to Barcelona.\n"
          "Days 5-9: Visit Barcelona for 5 days.\nDay 9: Fly from Barcelona to Florence.\n"
          "Days 9-14: Visit Florence for 6 days.")
    print("english parse:", _events(en))
    n_parsed = sum(1 for r in rows if _events(r["answer"]))
    print("gold plans that parse:", n_parsed, "/", len(rows))
    golds = [r["answer"] for r in rows]
    print("self accuracy (gold vs gold):", score([_events(g) for g in golds], golds, {})[0])
    print("empty accuracy:", score([None] * len(golds), golds, {})[0])
    # the English rendering of the same plan must NOT be judged equal to the Korean gold (city names differ)
    print("mixed-language accuracy:", score([_events(en)] * len(golds), golds, {})[0])
