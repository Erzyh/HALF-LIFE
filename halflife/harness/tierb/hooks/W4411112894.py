"""Hook W4411112894 (BABE media-bias annotation, gpt-4-turbo '0-shot + sys prompt', Table 1 MCC).

parse -> the LAST 'The answer is <LABEL>' in the reply (Table 8 template); fallback: the last standalone
         'BIASED' / 'NOT BIASED'; None when neither occurs.
score -> Matthews correlation coefficient with BIASED (gold 1) as the positive class; an unparsable reply is
         scored as NOT BIASED (no bias asserted). Set-level statistic, no per-item list.
"""
import math, re

TAIL = r"(?i)the answer is\s*:?\s*\**\s*\[?\s*(not\s+biased|biased)"
ANY = r"(?i)(?<![a-z])(not\s+biased|biased)(?![a-z])"


def parse(text, cfg):
    t = text or ""
    hits = re.findall(TAIL, t) or re.findall(ANY, t)
    if not hits:
        return None
    return "NOT BIASED" if hits[-1].lower().startswith("not") else "BIASED"


def mcc(tp, tn, fp, fn):
    d = math.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return (tp * tn - fp * fn) / d if d > 0 else 0.0


def score(preds, golds, cfg):
    tp = tn = fp = fn = 0
    for p, g in zip(preds, golds):
        y = 1 if str(g).strip().upper() == "BIASED" else 0
        yh = 1 if p == "BIASED" else 0
        if y and yh:
            tp += 1
        elif y:
            fn += 1
        elif yh:
            fp += 1
        else:
            tn += 1
    return mcc(tp, tn, fp, fn), None


if __name__ == "__main__":
    tests = [("Let's think step by step. The sentence uses loaded words. The answer is BIASED.", "BIASED"),
             ("... The answer is NOT BIASED", "NOT BIASED"), ("The answer is: **Not Biased**.", "NOT BIASED"),
             ("This is biased, however overall it is not biased.", "NOT BIASED"),
             ("The answer is BIASED. Wait, The answer is NOT BIASED.", "NOT BIASED"), ("Unbiased reporting.", None),
             ("", None)]
    for reply, want in tests:
        assert parse(reply, {}) == want, (reply, parse(reply, {}), want)
    assert abs(mcc(6, 3, 1, 2) - 16 / math.sqrt(7 * 8 * 4 * 5)) < 1e-12
    v, _ = score(["BIASED", "NOT BIASED", "BIASED", None], ["BIASED", "NOT BIASED", "BIASED", "NOT BIASED"], {})
    assert v == 1.0
    v, _ = score(["NOT BIASED", "BIASED"], ["BIASED", "NOT BIASED"], {})
    assert v == -1.0
    print("W4411112894 hook self-test ok")
