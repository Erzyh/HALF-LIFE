"""Hook W7169474262 (One-Word Census, Table 1 self-distinctness for gpt-4-turbo).

load_items -> the 31 frozen stimuli of items.inline, each repeated four times (the paper asks every
              prompt four times per model, Sec. 3.5); rows {id: "<category>#<run>", category, stimulus}.
parse      -> the authors' normalizer, transcribed from studies/consensus/analyze.py of
              github.com/tap2k/modelun (Sec. 3.3): junk guard (chat-template artifacts, >15 words,
              bare acknowledgments) -> failed cell (None); otherwise lowercase, strip punctuation and
              emoji, keep the last alphabetic word, single-letter tokens dropped.
score      -> self-distinctness: within each category, distinct valid answers / valid samples; the
              model's score is the mean over the categories (analyze.py: selfd.append(len(set(mine))
              / len(mine)); "self_distinct": mean(selfd)). Bare plurals are merged with their
              singulars when both occur in the category pool - here our own four answers, since the
              panel's other 43 models are not part of this re-execution.
Set-level statistic -> per-item list is None and the runner resamples items for the CI.
"""
import re
from collections import Counter

import numpy as np

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿]")
PUNCT = re.compile(r"[*_`#>\[\]().,!?\"':;]")
WORD = re.compile(r"^[a-z\-]+$|^\d+$")
JUNK = re.compile(r"\[/?INST\]|<[^>]*>|\bthinking\b", re.I)
ACK = re.compile(r"^\s*(okay|ok|sure|certainly|alright)[.!]?\s*$", re.I)
RUNS = 4


def load_items(cfg):
    rows = cfg["items"]["inline"]
    if len(rows) != 31:
        raise NeedsHuman(f"items.inline has {len(rows)} stimuli, Sec. 3.1 has 31")  # noqa: F821
    return [{"id": f"{r['id']}#{k + 1}", "category": r["id"], "stimulus": r["stimulus"]}
            for r in rows for k in range(RUNS)]


def parse(text, cfg):
    if not text:
        return None
    if JUNK.search(text) or ACK.match(text) or len(text.split()) > 15:
        return None
    a = EMOJI.sub(" ", PUNCT.sub(" ", text.strip().lower()))
    words = [w for w in a.split() if WORD.match(w) and (len(w) > 1 or w.isdigit())]
    return words[-1] if words else None


def score(preds, golds, cfg):
    by_cat = {}
    failed = 0
    for p, g in zip(preds, golds):
        if p is None:
            failed += 1
            continue
        by_cat.setdefault(str(g), []).append(p)
    selfd = []
    for cat in sorted(by_cat):
        mine = by_cat[cat]
        pool = Counter(mine)                       # plural merge inside the category pool
        stems = {w: w[:-1] for w in pool if w.endswith("s") and w[:-1] in pool}
        mine = [stems.get(a, a) for a in mine]
        selfd.append(len(set(mine)) / len(mine))
    print(f"[W7169474262] categories {len(selfd)}, failed cells {failed}")
    if not selfd:
        return float("nan"), None
    return float(np.mean(selfd)), None


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    assert parse("Blue", {}) == "blue"
    assert parse("A common color is blue.", {}) == "blue"
    assert parse("Okay.", {}) is None and parse("[/INST] blue", {}) is None
    assert parse(" ".join(["word"] * 16), {}) is None
    assert parse("(kroa:a)", {}) == "kroa"                   # single-letter tokens are never answers
    assert parse("...", {}) is None
    assert parse("**Mustard**", {}) == "mustard"
    rows = load_items({"items": {"inline": [{"id": f"c{i}", "stimulus": "s"} for i in range(31)]}})
    assert len(rows) == 124 and rows[0]["id"] == "c0#1"
    preds = ["oak", "oak", "oak", "oak", "rose", "rose", "lily", "tulip", "cat", "cats", "dog", None]
    golds = ["tree"] * 4 + ["flower"] * 4 + ["animal"] * 4
    v, per = score(preds, golds, {})
    assert per is None and abs(v - (1 / 4 + 3 / 4 + 2 / 3) / 3) < 1e-12, v   # cats->cat merged
    print("ok", round(v, 4))
