"""Hook W4411119711 (FaithBench, GPT-4-Turbo w/ simple zero-shot prompt, Table 2 balanced accuracy 55.96%).

load_items -> the 750 human-annotated samples of github.com/vectara/FaithBench (data_for_release/batch_{1..16}.json,
              batch 13 does not exist), mirrored into external/data/tierb_items/W4411119711/.
              Sample-level gold follows the released scripts/binarize.py with the paper's configuration
              (aggregation "worst", hallucinated classes = Questionable + Unwanted{,.Intrinsic,.Extrinsic}):
              take the most severe label over all span annotations of the sample; the sample is hallucinated
              (negative class) when that label is Questionable or Unwanted, and consistent (positive class) when it
              is Benign or when there is no annotation at all. Table 2's caption states the same split
              ("negative class is unwanted + questionable, positive class is benign + consistent").
              Gold is written as "yes" (consistent) / "no" (hallucinated) so it lines up with the prompt's answer
              space. Counts: 511 hallucinated, 239 consistent.
parse      -> the authors' own judge parser (data_collection_scripts/gpt_as_a_judge_pred.ipynb): drop every
              non-word, non-space character, lower-case, take the first token, map yes/accurate -> yes and
              no/inaccurate -> no; anything else is None.
score      -> balanced accuracy = mean of the two class recalls (x1 in 0-1; metric.scale 100 restores percent).
              per_item is None, so the runner resamples items and recomputes the statistic for the CI.
No render: the config's system prompt and user_template are runner facilities.
"""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4411119711"
SEVERITY = {"Benign": 1, "Questionable": 2, "Unwanted": 3,
            "Unwanted.Intrinsic": 3, "Unwanted.Extrinsic": 3, "Unwanted.Instrinsic": 3}
LABEL_MAP = {"yes": "yes", "accurate": "yes", "no": "no", "inaccurate": "no"}


def load_items(cfg):
    rows = []
    for b in list(range(1, 13)) + list(range(14, 17)):
        path = DATA / f"batch_{b}.json"
        if not path.exists():
            raise NeedsHuman(f"mirror FaithBench data_for_release/batch_{b}.json into {DATA}")  # noqa: F821
        for s in json.loads(path.read_text(encoding="utf-8"))["samples"]:
            labels = []
            for a in s.get("annotations") or []:
                labels.extend(a.get("label") or [])
            worst = max((SEVERITY[x] for x in set(labels)), default=1)
            rows.append({"id": f"b{b}_s{s['sample_id']}", "article": s["source"], "summary": s["summary"],
                         "gold": "no" if worst >= 2 else "yes",
                         "summarizer": (s.get("metadata") or {}).get("summarizer")})
    if len(rows) != 750:
        raise NeedsHuman(f"{len(rows)} samples, expected 750 (Sec. 2.3)")  # noqa: F821
    return rows


def parse(text, cfg):
    if not text:
        return None
    t = re.sub(r"[^\w\s]", "", text).strip().lower().split()
    if not t:
        return None
    if t[0] in LABEL_MAP:
        return LABEL_MAP[t[0]]
    joined = " ".join(t)
    if "inaccurate" in joined or "inaccurately" in joined:
        return "no"
    if "accurate" in joined or "accurately" in joined:
        return "yes"
    return None


def score(preds, golds, cfg):
    """Balanced accuracy: mean recall over the two classes; an unparsed reply counts as the wrong class."""
    rec = []
    for cls in ("yes", "no"):
        idx = [i for i, g in enumerate(golds) if g == cls]
        if not idx:
            continue
        rec.append(sum(1 for i in idx if preds[i] == cls) / len(idx))
    if not rec:
        return 0.0, None
    return sum(rec) / len(rec), None


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    from collections import Counter
    rows = load_items({})
    print(len(rows), "samples;", Counter(r["gold"] for r in rows))
    print("first id", rows[0]["id"], "| summary:", rows[0]["summary"][:90])
    for t, want in [("Yes", "yes"), ("no", "no"), ("Yes.", "yes"), ("No, the summary adds facts.", "no"),
                    ("Accurate", "yes"), ("", None)]:
        got = parse(t, {})
        print("parse", repr(t), "->", got, "OK" if got == want else "MISMATCH")
    golds = [r["gold"] for r in rows]
    print("all-yes BA", round(score(["yes"] * len(golds), golds, {})[0], 4))
    print("perfect BA", round(score(golds, golds, {})[0], 4))
    # cross-check against the detector predictions the benchmark ships in its own metadata
    stored = []
    for b in list(range(1, 13)) + list(range(14, 17)):
        for s in json.loads((DATA / f"batch_{b}.json").read_text(encoding="utf-8"))["samples"]:
            v = (s.get("metadata") or {}).get("gpt-4-turbo")
            stored.append("yes" if v == 1 else "no" if v == 0 else None)
    print("BA of the archived gpt-4-turbo column:", round(score(stored, golds, {})[0] * 100, 2), "(paper: 55.96)")
