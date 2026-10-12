"""Hook W4417257719 (EDINET-Bench earnings forecasting, gpt-5, Table 6 ROC-AUC).

parse -> P(increase) = the JSON field 'prob' of the reply (code fences and surrounding text tolerated);
         fallback: the JSON field 'prediction' (0/1) as a hard probability; None when neither is readable.
score -> ROC-AUC of the parsed probability against the binary label (1 = increase); unparsable replies enter
         as 0.5 (config output.postprocess). Rank-based (Mann-Whitney) computation with ties averaged.
"""
import json, re
import numpy as np


def _obj(text):
    t = (text or "").strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.S)
    cands = [m.group(1)] if m else []
    m2 = re.search(r"\{.*\}", t, re.S)
    if m2:
        cands.append(m2.group(0))
    for c in cands:
        try:
            return json.loads(c)
        except Exception:
            continue
    return None


def parse(text, cfg):
    obj = _obj(text)
    if not isinstance(obj, dict):
        return None
    try:
        p = float(obj.get("prob"))
        if 0.0 <= p <= 1.0:
            return p
    except (TypeError, ValueError):
        pass
    try:
        return 1.0 if int(obj.get("prediction")) == 1 else 0.0
    except (TypeError, ValueError):
        return None


def roc_auc(scores, labels):
    s, y = np.asarray(scores, float), np.asarray(labels, int)
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), float)
    ss, i = s[order], 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1          # average rank, 1-based
        i = j + 1
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def score(preds, golds, cfg):
    scores = [0.5 if p is None else float(p) for p in preds]
    labels = [1 if str(g).strip().lower() in ("1", "1.0", "true") else 0 for g in golds]
    return roc_auc(scores, labels), None


if __name__ == "__main__":
    tests = [('JSON:\n```json\n{"reasoning": "x", "prob": 0.72, "prediction": 1}\n```', 0.72),
             ('{"reasoning": "y", "prob": 0.3, "prediction": 0}', 0.3),
             ('{"reasoning": "z", "prob": "n/a", "prediction": 1}', 1.0), ("no json here", None),
             ('{"reasoning": "w", "prob": 1.4}', None)]
    for reply, want in tests:
        got = parse(reply, {})
        assert (got is None and want is None) or abs(got - want) < 1e-9, (reply, got, want)
    rng = np.random.default_rng(20260907)
    s = rng.random(60); y = (rng.random(60) < 0.5).astype(int)
    brute = np.mean([(1.0 if a > b else 0.5 if a == b else 0.0) for a in s[y == 1] for b in s[y == 0]])
    assert abs(roc_auc(s, y) - brute) < 1e-12
    assert roc_auc([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) == 1.0 and roc_auc([0.5, 0.5, 0.5], [1, 0, 1]) == 0.5
    v, _ = score([0.9, None, 0.1], [1, 0, 0], {})
    assert v == 1.0
    print("W4417257719 hook self-test ok")
