"""W4407374917 (eco-LLM, Task 1a species presence): parse the Python list of 10 likelihood scores,
binarize at 0.5 and score each species as the share of its 10 locations that match correct_answers;
the metric is the mean over species (Table 1 'Mean Acc.', scores binarized at 0.5). Replies without a
parsable list of the right length are invalid: counted, excluded from the mean (paper's '# Invalid')."""
import json
import re

import numpy as np


def parse(text, cfg):
    """First bracketed list in the reply -> list of floats (None when there is none)."""
    if not text:
        return None
    m = re.search(r"\[([^\[\]]*)\]", text, re.S)
    if not m:
        return None
    nums = re.findall(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", m.group(1))
    return [float(x) for x in nums] if nums else None


def score(preds, golds, cfg):
    per, invalid = [], 0
    for p, g in zip(preds, golds):
        g = json.loads(g) if isinstance(g, str) else list(g)
        if p is None or len(p) != len(g):
            per.append(None)
            invalid += 1
            continue
        per.append(float(np.mean([(1 if x >= 0.5 else 0) == int(y) for x, y in zip(p, g)])))
    valid = [x for x in per if x is not None]
    print(f"[W4407374917] species scored {len(valid)}, invalid replies {invalid}")
    return (float(np.mean(valid)) if valid else float("nan")), per


if __name__ == "__main__":
    gold = [0, 1, 0, 1, 1, 0, 0, 1, 0, 1]
    r1 = "[0.1, 0.9, 0.2, 0.8, 0.7, 0.1, 0.3, 0.6, 0.05, 0.95]"            # all correct
    r2 = "Sure. Here is my answer:\n```python\n[0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]\n```"  # 5/10
    r3 = "I cannot say."                                                   # invalid
    r4 = "[0.5, 0.4]"                                                      # wrong length -> invalid
    preds = [parse(r, {}) for r in (r1, r2, r3, r4)]
    val, per = score(preds, [gold] * 4, {})
    assert per == [1.0, 0.5, None, None] and abs(val - 0.75) < 1e-9, (val, per)
    print("ok", val, per)
