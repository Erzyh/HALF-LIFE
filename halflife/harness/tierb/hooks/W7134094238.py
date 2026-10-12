"""Hook for W7134094238 (BioLLMAgent, Table V 'GPT-4o w/' row): Iowa Gambling Task neutral prior.

parse() reads the four deck probabilities {A: p, B: p, C: p, D: p} (braces, JSON or 'p_A = ...' forms)
and normalises them to sum 1. score() draws 100 deck choices from every valid distribution with a fixed
RNG (seed 20260907), pools them and reports KL(p_hat || uniform) (paper: 0.002), the chi-square
goodness-of-fit p-value against uniform (0.988) and the std of the four deck shares (0.017). The KL of
the mean returned distribution (no sampling) is printed as a second reading.
"""
import math, re
import numpy as np

SEED = 20260907
DECKS = "ABCD"


def parse(text, cfg):
    if not text:
        return None
    probs = []
    for d in DECKS:
        pat = r"(?<![A-Za-z])(?:p_?)?" + d + r"(?![A-Za-z])\s*[\"']?\s*[:=]\s*[\"']?\s*(\d*\.?\d+)\s*(%?)"
        ms = re.findall(pat, text)
        if not ms:
            return None
        v, pct = ms[-1]                                         # the last statement is the answer
        v = float(v) / (100.0 if pct or float(v) > 1.0 else 1.0)
        probs.append(v)
    s = sum(probs)
    if s <= 0 or any(p < 0 for p in probs):
        return None
    return [p / s for p in probs]


def chi2_sf_df3(x):
    """Survival function of chi-square with 3 degrees of freedom (closed form)."""
    return math.erfc(math.sqrt(x / 2.0)) + math.sqrt(2.0 * x / math.pi) * math.exp(-x / 2.0)


def stats(counts):
    n = counts.sum()
    p = counts / n
    kl = float(sum(pi * math.log(pi / 0.25) for pi in p if pi > 0))
    chi = float(((counts - n / 4.0) ** 2 / (n / 4.0)).sum())
    return kl, chi2_sf_df3(chi), float(np.std(p))


def score(preds, golds, cfg):
    valid = [np.array(p) for p in preds if p is not None]
    print(f"[W7134094238] {len(valid)} of {len(preds)} replies carry a valid distribution")
    if not valid:
        return float("nan"), None
    rng = np.random.default_rng(SEED)
    counts = np.zeros(4)
    for p in valid:
        counts += np.bincount(rng.choice(4, 100, p=p), minlength=4)
    kl, pval, std = stats(counts)
    mean_p = np.mean(valid, axis=0)
    kl_mean = float(sum(pi * math.log(pi / 0.25) for pi in mean_p if pi > 0))
    print(f"[W7134094238] pooled {int(counts.sum())} sampled choices: shares {np.round(counts / counts.sum(), 4).tolist()}, "
          f"KL {kl:.4f}, chi-square p {pval:.3f}, std {std:.4f}; KL of the mean distribution {kl_mean:.5f}")
    return kl, None


if __name__ == "__main__":
    assert parse("{A: 0.25, B: 0.25, C: 0.25, D: 0.25}", {}) == [0.25] * 4
    assert parse('{"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2}', {}) == [0.3, 0.3, 0.2, 0.2]
    p = parse("Sure. p_A = 25%, p_B = 25%, p_C = 25%, p_D = 25%", {})
    assert p and abs(sum(p) - 1) < 1e-9
    assert parse("I will choose deck A.", {}) is None
    assert abs(chi2_sf_df3(7.815) - 0.05) < 1e-3
    kl, _ = score([[0.25] * 4] * 30, [None] * 30, {})
    assert kl < 0.01
    print("ok")
