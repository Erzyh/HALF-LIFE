"""Hook W7159577685 (neutrosophic T+I+F elicitation, gpt-4-turbo, Table 2 'Sum').

parse  -> T + I + F of the JSON reply; None when the reply is not a JSON object with T, I, F all in [0, 1]
          (the paper counts only such replies as valid evaluations).
score  -> mean of the sums over the valid replies (no gold label); per-item values give the bootstrap CI.
"""
import json, math, re


def _obj(text):
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S)
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"\{.*?\}", t, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def parse(text, cfg):
    obj = _obj(text)
    if not isinstance(obj, dict):
        return None
    total = 0.0
    for k in ("T", "I", "F"):
        try:
            v = float(obj[k])
        except (KeyError, TypeError, ValueError):
            return None
        if math.isnan(v) or not (0.0 <= v <= 1.0):
            return None
        total += v
    return total


def score(preds, golds, cfg):
    valid = [float(p) for p in preds if p is not None]
    value = sum(valid) / len(valid) if valid else float("nan")
    return value, [None if p is None else float(p) for p in preds]


if __name__ == "__main__":
    tests = [('{"T": 0.3, "I": 0.9, "F": 0.7}', 1.9), ('```json\n{"T":0.5,"I":0.5,"F":0.5}\n```', 1.5),
             ('Sure: {"T": 1.0, "I": 0.0, "F": 0.0} done', 1.0), ('{"T": 1.2, "I": 0.1, "F": 0.1}', None),
             ("I cannot evaluate this.", None), ('{"T": 0.2, "I": 0.3}', None)]
    for reply, want in tests:
        got = parse(reply, {})
        assert (got is None and want is None) or abs(got - want) < 1e-9, (reply, got, want)
    v, per = score([1.9, 1.5, None, 1.0], [None] * 4, {})
    assert abs(v - (1.9 + 1.5 + 1.0) / 3) < 1e-9 and per[2] is None
    print("W7159577685 hook self-test ok")
