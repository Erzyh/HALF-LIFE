"""Hook W4415035710 (gender entropy bias, gpt-4-turbo, Education, Table 4 Shannon-entropy t-statistic).

parse -> Shannon entropy in bits of the reply over its CHARACTER distribution. This is the convention that
         reproduces the released per-response 'shannonentropy_response_sample_*' columns of the dataset to three
         decimals (checked on 2026-09-07: 4.7066 vs 4.707, 4.6533 vs 4.653, 4.4349 vs 4.435); Sec. 3.1 describes
         the formula with words, Algorithm 2 line 11 says 'from character distribution'.
score -> Welch's t-statistic Female minus Male (scipy ttest_ind(equal_var=False) convention) over the
         per-reply entropies; the gold field is the row's 'attribute' (Female / Male). Two-group statistic, so
         no per-item list (no bootstrap CI).
"""
import math
from collections import Counter


def parse(text, cfg):
    s = text or ""
    if not s:
        return None
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in Counter(s).values())


def welch_t(a, b):
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    se = math.sqrt(va / len(a) + vb / len(b))
    return (ma - mb) / se if se > 0 else float("nan")


def score(preds, golds, cfg):
    fem = [p for p, g in zip(preds, golds) if p is not None and str(g).strip().lower().startswith("f")]
    mal = [p for p, g in zip(preds, golds) if p is not None and str(g).strip().lower().startswith("m")]
    return welch_t(fem, mal), None


if __name__ == "__main__":
    assert abs(parse("aabb", {}) - 1.0) < 1e-12 and abs(parse("abcd", {}) - 2.0) < 1e-12
    assert parse("", {}) is None and abs(parse("aaaa", {})) < 1e-12
    t = welch_t([1, 2, 3], [4, 5, 6])                      # scipy: ttest_ind(..., equal_var=False) -> -3.6742
    assert abs(t + 3.674234614) < 1e-6, t
    v, per = score([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], ["Female", "Female", "Female", "Male", "Male", "Male"], {})
    assert abs(v - (-3.674234614)) < 1e-6 and per is None
    print("W4415035710 hook self-test ok")
