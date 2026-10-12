"""Hook for W4404792825 (Will LLMs Sink or Swim?): General Self-Efficacy scale, no-pressure baseline.

Each call is one administration of the 10-item GSE scale (Likert 1-4). parse() reads the ten per-line
ratings and returns their SUM (10-40); score() is the mean total over administrations (Table 2, GPT-4o
Base: 31.36). Administrations with fewer than 10 parsable ratings are discarded and counted.
"""
import re

N_ITEMS = 10


def parse(text, cfg):
    if not text:
        return None
    ratings = {}
    for line in text.splitlines():
        m = re.match(r"^\W*(?:item|statement|q)?\s*(\d{1,2})\b", line.strip(), re.I)
        if not m:
            continue
        item = int(m.group(1))
        if not 1 <= item <= N_ITEMS or item in ratings:
            continue
        rest = line.strip()[m.end():]
        r = re.search(r"(?<![\d.])([1-4])(?![\d.])", rest)      # first standalone 1-4 after the item number
        if r:
            ratings[item] = int(r.group(1))
    if len(ratings) < N_ITEMS:
        return None                                              # discarded administration
    return sum(ratings[i] for i in range(1, N_ITEMS + 1))


def score(preds, golds, cfg):
    vals = [float(p) for p in preds if p is not None]
    print(f"[W4404792825] {len(vals)} of {len(preds)} administrations parsable; totals {vals}")
    if not vals:
        return float("nan"), None
    return sum(vals) / len(vals), vals


if __name__ == "__main__":
    a = "1. 3\n2. 2\n3. 3\n4. 4\n5. 3\n6. 4\n7. 3\n8. 3\n9. 4\n10. 3"
    b = "Item 1: 4\nItem 2: 3\nItem 3: 4\nItem 4: 4\nItem 5: 4\nItem 6: 4\nItem 7: 3\nItem 8: 4\nItem 9: 4\nItem 10: 4"
    c = "1 - 3\n2 - 3\n3 - 3"                                    # incomplete -> discarded
    d = "1. I can always manage to solve difficult problems if I try hard enough. 4\n" + "\n".join(f"{i}. 3" for i in range(2, 11))
    assert parse(a, {}) == 32 and parse(b, {}) == 38 and parse(c, {}) is None and parse(d, {}) == 31
    assert abs(score([32, 38, None, 31], [None] * 4, {})[0] - 33.6667) < 1e-3
    print("ok")
