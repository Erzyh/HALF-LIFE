"""Hook for W4416037849 (CRAB, Table 7 row o3-mini, SRC Relevance Precision 71.22).

load_items() reads the four CRAB language files (100 queries each; positive = relevant references,
negative = irrelevant, each prefixed '[n] ') and draws, per query with one RNG seeded 20260907, a
40%/60% relevant/irrelevant reference set (n_rel = min(#positive, floor(2/3 #negative)),
n_irr = min(#negative, round-half-up(1.5 n_rel))); queries without a positive or negative reference are
skipped. The draw is shuffled and renumbered [1]..[n]. One call per query; the gold is the list of 0/1
labels in that order. parse() reads per-reference labels ('[k] 1', 'k: 0', 'Reference k - 1') or a bare
0/1 sequence. score() pools all references: RP = F1 of the relevant class (returned), IS = F1 of the
irrelevant class and CE = macro F1 (printed); an unparsable reply predicts 0 for all its references.
"""
import json, math, re, urllib.request
from pathlib import Path
import numpy as np

WID = "W4416037849"
SEED = 20260907
FILES = ["en_data.jsonl", "french_data.jsonl", "german_data.jsonl", "zh_data.jsonl"]
BASE = "https://huggingface.co/datasets/zhm0/CRAB/resolve/main/"
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / WID
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}


def _strip_num(ref):
    return re.sub(r"^\s*\[\d+\]\s*", "", str(ref)).strip()


def load_items(cfg):
    CACHE.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    rows = []
    for fn in FILES:
        p = CACHE / fn
        if not p.exists():
            p.write_bytes(urllib.request.urlopen(urllib.request.Request(BASE + fn, headers=UA), timeout=300).read())
        lang = fn.split("_")[0]
        for qi, line in enumerate(l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()):
            q = json.loads(line)
            pos, neg = list(q["positive"]), list(q["negative"])
            if not pos or not neg:
                continue
            n_rel = min(len(pos), int(math.floor(2 * len(neg) / 3)))
            n_irr = min(len(neg), int(math.floor(1.5 * n_rel + 0.5)))
            drawn = [(_strip_num(pos[i]), 1) for i in rng.choice(len(pos), n_rel, replace=False)] + \
                    [(_strip_num(neg[i]), 0) for i in rng.choice(len(neg), n_irr, replace=False)]
            drawn = [drawn[i] for i in rng.permutation(len(drawn))]
            rows.append({"id": f"{lang}-{qi}", "language": lang, "question": q["question"],
                         "references": "\n".join(f"[{k + 1}] {t}" for k, (t, _) in enumerate(drawn)),
                         "gold": [lab for _, lab in drawn], "n_references": len(drawn)})
    return rows


def parse(text, cfg):
    if not text:
        return None
    by_index = {}
    for pat in (r"\[(\d{1,3})\]\s*[:\-=.)]?\s*\**\s*([01])(?!\d)",                       # '[k] 1' / '[k]: 1'
                r"(?:^|[,;])\s*(?:reference|ref\.?)?\s*#?(\d{1,3})\s*[:\-=.)]\s*\**\s*([01])(?!\d)"):   # 'k: 1', 'Reference k - 1'
        for m in re.finditer(pat, text, re.I | re.M):
            by_index.setdefault(int(m.group(1)), int(m.group(2)))
    seq = [int(x) for x in re.findall(r"(?<![\d.])([01])(?![\d.])", text)]
    return {"by_index": by_index, "seq": seq}


def _labels(pred, n):
    if pred and all(i in pred["by_index"] for i in range(1, n + 1)):
        return [pred["by_index"][i] for i in range(1, n + 1)], True
    if pred and len(pred["seq"]) == n:
        return pred["seq"], True
    if pred and len(pred["by_index"]) >= 1 and len(pred["seq"]) > n:
        return [pred["by_index"].get(i, 0) for i in range(1, n + 1)], True
    return [0] * n, False


def _f1(y_true, y_pred, cls):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
    return 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)


def score(preds, golds, cfg):
    y_true, y_pred, unparsed = [], [], 0
    for p, g in zip(preds, golds):
        labs, ok = _labels(p, len(g))
        unparsed += 0 if ok else 1
        y_true += list(g); y_pred += labs
    rp, is_ = _f1(y_true, y_pred, 1), _f1(y_true, y_pred, 0)
    print(f"[{WID}] {len(y_true)} references from {len(golds)} queries ({unparsed} unparsable replies); "
          f"RP {100 * rp:.2f} IS {100 * is_:.2f} CE {100 * (rp + is_) / 2:.2f}")
    return rp, None


if __name__ == "__main__":
    assert _labels(parse("[1] 1\n[2] 0\n[3] 1", {}), 3) == ([1, 0, 1], True)
    assert _labels(parse("1: 0, 2: 1, 3: 1", {}), 3) == ([0, 1, 1], True)
    assert _labels(parse("Reference 1 - 1\nReference 2 - 0", {}), 2) == ([1, 0], True)
    assert _labels(parse("[1, 0, 1, 1]", {}), 4) == ([1, 0, 1, 1], True)
    assert _labels(parse("I cannot classify these.", {}), 3) == ([0, 0, 0], False)
    v, _ = score([parse("[1] 1\n[2] 0\n[3] 1", {}), parse("1 1", {})], [[1, 0, 0], [1, 0]], {})
    assert abs(v - 2 * 2 / (2 * 2 + 2 + 0)) < 1e-9, v
    print("ok")
