r"""Hook for W4403786592 (mental-illness evaluation, GPT-4-Turbo zero-shot SEV-4 on DepSeverity).

load_items: Reddit_depression_dataset.csv (3,553 rows: text, label in minimum/mild/moderate/severe -> 0-3) with
            the paper's fair (class-balanced) sampling of 1,000 posts: 250 per class, seeded (20260907).
render:     runner default (SEV-4 prompt transcribed from Figure 1 of the PDF, post appended).
parse:      Sec. 3.7: the integers found in the reply; exactly one integer inside 0-3 -> that level, else invalid (None).
score:      BA = mean per-class recall over the four levels (invalid = wrong); per-item values reweighted so their
            mean equals BA; MAE over valid replies printed for the secondary cell.
"""
import csv, io, re, urllib.request

import numpy as np

URL = "https://raw.githubusercontent.com/usmaann/Depression_Severity_Dataset/main/Reddit_depression_dataset.csv"
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
LEVELS = {"minimum": 0, "minimal": 0, "mild": 1, "moderate": 2, "severe": 3}
SEED, PER_CLASS = 20260907, 250


def load_items(cfg):
    with urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=120) as r:
        data = list(csv.DictReader(io.StringIO(r.read().decode("utf-8", "replace"))))
    rows = [{"id": str(i), "post": d["text"], "gold": LEVELS[d["label"].strip().lower()]} for i, d in enumerate(data)]
    rng = np.random.default_rng(SEED)
    out = []
    for lvl in range(4):
        pool = [r for r in rows if r["gold"] == lvl]
        idx = sorted(rng.choice(len(pool), min(PER_CLASS, len(pool)), replace=False))
        out += [pool[i] for i in idx]
    return out


def parse(text, cfg):
    if not text:
        return None
    nums = re.findall(r"-?\d+", text)
    if len(nums) != 1:
        return None
    v = int(nums[0])
    return v if 0 <= v <= 3 else None


def score(preds, golds, cfg):
    golds = [int(g) for g in golds]
    recall, n_cls = {}, {}
    for lvl in range(4):
        idx = [i for i, g in enumerate(golds) if g == lvl]
        n_cls[lvl] = len(idx)
        recall[lvl] = (sum(1 for i in idx if preds[i] == lvl) / len(idx)) if idx else float("nan")
    ba = float(np.nanmean(list(recall.values())))
    k, n = sum(1 for v in n_cls.values() if v), len(golds)
    per = [(1.0 if p == g else 0.0) * n / (k * n_cls[g]) for p, g in zip(preds, golds)]
    valid = [(p, g) for p, g in zip(preds, golds) if p is not None]
    mae = float(np.mean([abs(p - g) for p, g in valid])) if valid else float("nan")
    print(f"[W4403786592] BA {ba:.4f} per-class recall {recall} | MAE over {len(valid)} valid replies {mae:.3f} | invalid {n - len(valid)}")
    return ba, per


if __name__ == "__main__":
    ts = ["2", " 3\n", "0.", "1 or 2", "The post suggests level 4", "I cannot assess this.", "Label: 1"]
    print([parse(t, {}) for t in ts])
    assert [parse(t, {}) for t in ts] == [2, 3, 0, None, None, None, 1]
    v, per = score([0, 1, 2, 3, None, 0], [0, 1, 2, 3, 3, 0], {})
    assert abs(v - (1 + 1 + 1 + 0.5) / 4) < 1e-9 and abs(sum(per) / len(per) - v) < 1e-9, (v, per)
    print("ok", v)
