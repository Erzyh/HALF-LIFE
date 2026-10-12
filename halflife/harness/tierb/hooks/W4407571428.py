r"""Hook for W4407571428 (PhysiCo CORE, GPT-4 text-only matrix format).

load_items: Hub config core / split dev (200 rows with a 'label' column; the CORE-Test labels sit behind the
            authors' remote scoring endpoint, so the paper's CORE-Dev cell 41.3 is the target). Grids arrive as
            arrays of arrays; gold = {"letter": X, "choices": [...]} with X the position of 'label' in 'choices'.
render:     Figure 7 [SYSTEM] + [USER] template; each grid printed as rows of space-separated digits
            (matrix format; the exact serialisation is not printed); options lettered 'A. text' one per line.
parse:      the tail of the reply (the prompt asks that it end with the choice): last option letter, else option text.
score:      accuracy against the gold letter; per-item list.
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tierb_runner import load_hf  # noqa: E402

LETTERS = "ABCD"


def _grid(g):
    return "\n".join(" ".join(str(int(v)) for v in row) for row in g)


def load_items(cfg):
    rows = []
    for i, r in enumerate(load_hf("ShunchiZhang/PhysiCo", "core/dev")):
        choices = [str(c) for c in list(r["choices"])]
        label = str(r["label"])
        if label not in choices:
            raise RuntimeError(f"row {i}: label {label!r} not among choices {choices}")
        row = {"id": str(i), "choices": choices, "gold": {"letter": LETTERS[choices.index(label)], "choices": choices}}
        for k in ("input_1", "output_1", "input_2", "output_2", "input_3", "output_3"):
            row[k] = _grid(r[k])
        rows.append(row)
    return rows


def render(cfg, row):
    p = cfg["prompt"]
    u = p["user_template"]
    for k in (1, 2, 3):
        u = u.replace(f"{{input_grid_{k}}}", row[f"input_{k}"]).replace(f"{{output_grid_{k}}}", row[f"output_{k}"])
    u = u.replace("{candidate_answers}", "\n".join(f"{LETTERS[i]}. {c}" for i, c in enumerate(row["choices"])))
    return [{"role": "system", "content": p["system"]}, {"role": "user", "content": u}]


def parse(text, cfg):
    return text.strip()[-600:] if text and text.strip() else None


def _pick(tail, choices):
    pats = [r"(?i)answer\s*(?:is|:)?\s*\(?([A-D])\)?(?![A-Za-z])", r"\(([A-D])\)", r"\*\*([A-D])[\.\):]", r"(?<![A-Za-z])([A-D])[\.\):](?=\s|$)"]
    hits = [(m.end(), m.group(1).upper()) for pat in pats for m in re.finditer(pat, tail)]
    if hits:
        return max(hits)[1]                            # the last letter mention in the tail
    low = tail.lower()
    found = [(low.rfind(c.lower()), LETTERS[i]) for i, c in enumerate(choices) if c.lower() in low]
    return max(found)[1] if found else None


def score(preds, golds, cfg):
    per = []
    for p, g in zip(preds, golds):
        letter = _pick(p, g["choices"]) if p else None
        per.append(1.0 if letter == g["letter"] else 0.0)
    return (sum(per) / len(per) if per else float("nan")), per


if __name__ == "__main__":
    ch = ["spectrum of light and optical filters", "nuclear fission", "wave interference", "gravity"]
    ts = ["... Therefore my answer is (D) gravity.", "The pattern shows objects falling. Answer: D", "I choose B. nuclear fission",
          "The common pattern is gravity.", "No idea", "**D. gravity**"]
    print([_pick(t, ch) for t in ts])
    assert [_pick(t, ch) for t in ts] == ["D", "D", "B", "D", None, "D"]
    print(_grid([[0, 0, 9], [6, 6, 0]]))
