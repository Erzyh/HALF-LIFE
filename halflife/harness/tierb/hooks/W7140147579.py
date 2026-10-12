r"""Hook for W7140147579 (PLAT-MC, o3, F1 with a 'don't know' option).

load_items: Hub sma1-rmarud/plat-eng-mc default/test (100 precedents; the authors' GPT-4o English translation of the
            Korean originals) - precedent = facts + claims (Table 10 columns; case_info / reasoning / decision withheld);
            gold = 'Legitimate' if lawfulness else 'Not legitimate'.
render:     runner default (Figure 3 system + user template, {precedent} = items.precedent).
parse:      earliest occurrence among 'Not legitimate' / 'Legitimate' / "don't know" (case-insensitive) -> label; None = no answer.
score:      Eqs. 1-2: P = n_o/(n_o+n_x), R = (n_o+n_x)/N, F1 = 2PR/(P+R); no per-item CI (F1 is not an item mean).
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tierb_runner import load_hf  # noqa: E402

DATASET = "sma1-rmarud/plat-eng-mc"


def load_items(cfg):
    rows = []
    for r in load_hf(DATASET, "default/test"):
        law = str(r["lawfulness"]).strip().lower() in ("true", "1")
        rows.append({"id": str(r["case_no"]), "precedent": f"{str(r['facts']).strip()}\n\n{str(r['claims']).strip()}",
                     "gold": "Legitimate" if law else "Not legitimate"})
    if len(rows) != 100:
        raise RuntimeError(f"expected 100 precedents, got {len(rows)}")
    return rows


_PATS = [("Not legitimate", r"(?i)\bnot\s+legitimate\b"), ("don't know", r"(?i)\bdon[’']?t\s+know\b"), ("Legitimate", r"(?i)\blegitimate\b")]


def parse(text, cfg):
    if not text:
        return None
    hits = []
    for label, pat in _PATS:
        m = re.search(pat, text)
        if m:
            hits.append((m.start(), 0 if label != "Legitimate" else 1, label))
    if not hits:
        return None
    hits.sort()
    first = hits[0]
    if first[2] == "Legitimate":                      # 'Legitimate' matched inside 'Not legitimate' at the same spot?
        for pos, _, label in hits:
            if label == "Not legitimate" and pos <= first[0] + 4:
                return "Not legitimate"
    return first[2]


def score(preds, golds, cfg):
    n = len(golds)
    n_o = sum(1 for p, g in zip(preds, golds) if p == g)
    n_x = sum(1 for p, g in zip(preds, golds) if p is not None and p != "don't know" and p != g)
    answered = n_o + n_x
    precision = n_o / answered if answered else 0.0
    recall = answered / n if n else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    print(f"[W7140147579] P {precision:.3f} R {recall:.3f} F1 {f1:.3f} (n_o {n_o}, n_x {n_x}, n_u {n - answered})")
    return f1, None


if __name__ == "__main__":
    ts = ["The penalty tax is Legitimate because ...", "Answer: Not legitimate. The taxpayer ...", "I don't know - the facts are unclear",
          "Legitimate? No. Not legitimate.", "The imposition is not legitimate, since ...", "No conclusion."]
    print([parse(t, {}) for t in ts])
    assert [parse(t, {}) for t in ts] == ["Legitimate", "Not legitimate", "don't know", "Legitimate", "Not legitimate", None]
    f1, _ = score(["Legitimate", "Not legitimate", "don't know", None], ["Legitimate", "Legitimate", "Legitimate", "Not legitimate"], {})
    assert abs(f1 - 2 * 0.5 * 0.5 / 1.0) < 1e-9, f1
