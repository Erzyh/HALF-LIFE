"""Hook for W4402345509 (LAB-Bench, LitQA2 public split, Appendix D.1 prompt).

load_items() composes the answer options from ideal + distractors + the fixed 'Insufficient information'
option, permutes them per item with seed 20260907 + row index, letters them 'A) ...' and derives the gold
letter from the position of ideal. parse() reads the letter inside [ANSWER]...[/ANSWER] (a mangled closing
tag such as '[\\ANSWER]', seen in the paper's own examples, is accepted). score() is accuracy over all
questions (the 'Insufficient information' letter counts as incorrect); coverage and precision are printed.
"""
import io, json, re, urllib.request
from pathlib import Path
import numpy as np

WID = "W4402345509"
SEED = 20260907
EXTRA = "Insufficient information to answer the question."
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / WID
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()


def load_items(cfg):
    import pandas as pd
    hf = cfg["items"]["hf"]
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{hf['config']}.{hf['split']}.parquet"
    if not p.exists():
        listing = json.loads(_get(f"https://huggingface.co/api/datasets/{hf['dataset']}/parquet").decode("utf-8"))
        urls = listing[hf["config"]][hf["split"]]
        if len(urls) != 1:
            raise RuntimeError(f"expected one parquet shard, got {len(urls)}")
        p.write_bytes(_get(urls[0]))
    rows = pd.read_parquet(io.BytesIO(p.read_bytes())).to_dict("records")
    items = []
    for i, r in enumerate(rows):
        opts = [str(r["ideal"])] + [str(d) for d in list(r["distractors"])] + [EXTRA]
        order = np.random.default_rng(SEED + i).permutation(len(opts))
        letters = [chr(65 + k) for k in range(len(opts))]
        lines, gold, insufficient = [], None, None
        for k, j in enumerate(order):
            lines.append(f"{letters[k]}) {opts[j]}")
            if j == 0:
                gold = letters[k]
            if j == len(opts) - 1:
                insufficient = letters[k]
        items.append({"id": str(r["id"]), "question": str(r["question"]), "answers": "\n".join(lines),
                      "gold_letter": gold, "insufficient_letter": insufficient, "n_options": len(opts)})
    return items


def parse(text, cfg):
    if not text:
        return None
    m = re.search(r"\[ANSWER\]\s*\(?([A-Z])\)?\s*\[[/\\]?ANSWER\]", text) or re.search(r"\[ANSWER\]\s*\(?([A-Z])\)?", text)
    return m.group(1) if m else None


def score(preds, golds, cfg):
    per = [1.0 if p is not None and p == g else 0.0 for p, g in zip(preds, golds)]
    answered = sum(1 for p in preds if p is not None)
    acc = sum(per) / max(1, len(per))
    print(f"[{WID}] accuracy {acc:.4f} over {len(per)} questions; parsed {answered}; "
          f"precision over parsed {sum(per) / max(1, answered):.4f}")
    return acc, per


if __name__ == "__main__":
    assert parse("Reasoning... [ANSWER]D[/ANSWER]", {}) == "D"
    assert parse("Ans: [ANSWER]B[\\ANSWER]", {}) == "B"
    assert parse("[ANSWER] C [/ANSWER] because", {}) == "C"
    assert parse("The answer is B.", {}) is None
    v, per = score(["D", "B", None, "A"], ["D", "C", "A", "A"], {})
    assert abs(v - 0.5) < 1e-9 and per == [1.0, 0.0, 0.0, 1.0]
    o = np.random.default_rng(SEED + 3).permutation(5)
    assert sorted(o.tolist()) == [0, 1, 2, 3, 4]
    print("ok")
