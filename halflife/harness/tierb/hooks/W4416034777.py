"""Hook for W4416034777 (Illusion of Randomness, Table 1 row GPT-4-turbo, TVD 0.107).

parse() returns the final chosen action: the last sentence/line that names exactly one of Rock, Paper,
Scissors (the reasoning part lists all three, a final pick names one); replies with no such segment are
invalid. score() normalises the action counts over valid replies (Eq. 3) and returns the total variation
distance from the uniform 1/3 distribution (Eq. 4); the per-action shares are printed (Figure 2).
"""
import re

ACTIONS = ("rock", "paper", "scissors")
ACT_RE = re.compile(r"(?<![a-z])(rock|paper|scissors)(?![a-z])")


def parse(text, cfg):
    if not text:
        return None
    segments = [s for line in text.lower().splitlines() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]
    pick = None
    for seg in segments:
        found = set(ACT_RE.findall(seg))
        if len(found) == 1:
            pick = found.pop()                                      # the last single-action segment wins
    return pick


def score(preds, golds, cfg):
    valid = [p for p in preds if p in ACTIONS]
    n = len(valid)
    shares = {a: (sum(1 for p in valid if p == a) / n if n else 0.0) for a in ACTIONS}
    tvd = 0.5 * sum(abs(1 / 3 - shares[a]) for a in ACTIONS)
    print(f"[W4416034777] {n} valid of {len(preds)} games; shares {shares}; TVD {tvd:.4f}")
    return (tvd if n else float("nan")), None


if __name__ == "__main__":
    a = "The Nash equilibrium of Rock-Paper-Scissors is to play Rock, Paper, and Scissors with probability 1/3 each. Since no action is better, I choose Rock."
    b = "In equilibrium each of rock, paper and scissors is equally likely.\n\n**Action: Paper**"
    c = "Reasoning: mixed strategy over {Rock, Paper, Scissors}.\nMy choice: Scissors!"
    d = "The equilibrium mixes Rock, Paper and Scissors uniformly."            # no single pick -> invalid
    assert parse(a, {}) == "rock" and parse(b, {}) == "paper" and parse(c, {}) == "scissors" and parse(d, {}) is None
    v, _ = score(["rock", "rock", "paper", None, "scissors", "rock"], [None] * 6, {})
    assert abs(v - 0.5 * (abs(1 / 3 - 0.6) + abs(1 / 3 - 0.2) + abs(1 / 3 - 0.2))) < 1e-9
    print("ok")
