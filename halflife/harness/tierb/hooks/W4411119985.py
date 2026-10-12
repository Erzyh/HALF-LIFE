"""Hook W4411119985 (How Inclusively do LMs Perceive Social and Moral Norms?, GPT-4 Turbo zero-shot, CONF ADA-Met 0.92).

load_items -> the 100 r/confessions rules-of-thumb of the Social Chemistry 101 "analysis" split. In
              social-chem-101.v1.0.tsv these are exactly the rows with m == 50 and area == "confessions":
              400 RoTs in total across the four sources (amitheasshole / confessions / dearabby /
              rocstories), 100 each, 50 annotations each - the subset Sec. 2 describes ("only the 400
              RoTs that have been labeled by 50 human annotators each ... 100 RoTs from each of the
              following data sources").
              gold = the human consensus s_Hi of Eq. 1: the mode of the 50 annotators' `rot-agree`
              values (0-4, the same five buckets as options A-E), and, when the mode is tied, the
              arithmetic mean of the tied values (Appendix B.2 works exactly that example).
parse      -> the answer letter A-E mapped to the 0-4 score s_li of Sec. 4 so that the runner's
              mean_abs_error is ADA-Met_i = |mode(s_Hi) - s_li| averaged over the 100 RoTs (Eq. 1-2).
              An unparsable answer becomes None and the runner's nanmean drops it (the paper reports
              only 2 irrelevant responses across all LMs, Appendix F).
Data file: external/data/tierb_items/W4411119985/social-chem-101/social-chem-101.v1.0.tsv, unzipped once
from https://storage.googleapis.com/ai2-mosaic-public/projects/social-chemistry/data/social-chem-101.zip
(27.6 MB zip, 147 MB tsv). No API calls; deterministic (rows are ordered by rot-id, no shuffle).
"""
from collections import Counter
from pathlib import Path

DATA = (Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4411119985"
        / "social-chem-101" / "social-chem-101.v1.0.tsv")
AREA = "confessions"          # r/confessions (CONF), the Table 1 column re-executed here
N_ANNOTATORS = 50


def load_items(cfg):
    if not DATA.exists():
        raise NeedsHuman(  # noqa: F821 (injected by the runner)
            f"unzip social-chem-101.zip into {DATA.parent.parent} before --prepare "
            "(https://storage.googleapis.com/ai2-mosaic-public/projects/social-chemistry/data/social-chem-101.zip)")
    import pandas as pd
    df = pd.read_csv(DATA, sep="\t", usecols=["area", "m", "split", "rot-agree", "rot", "rot-id"])
    sub = df[(df["m"] == 50) & (df["area"] == AREA) & (df["split"] == "analysis")]
    rows = []
    for rid, g in sub.groupby("rot-id", sort=True):
        vals = [int(v) for v in g["rot-agree"].dropna()]
        if len(vals) != N_ANNOTATORS:
            raise NeedsHuman(f"{rid} has {len(vals)} annotations, expected {N_ANNOTATORS}")  # noqa: F821
        c = Counter(vals)
        top = max(c.values())
        modes = sorted(k for k, v in c.items() if v == top)
        rows.append({"rot_id": rid, "rot": sorted(set(g["rot"]))[0],
                     "gold": sum(modes) / len(modes), "n_modes": len(modes)})
    if len(rows) != 100:
        raise NeedsHuman(f"expected 100 {AREA} RoTs, got {len(rows)}")  # noqa: F821
    return rows


def parse(text, cfg):
    """First standalone option letter A-E -> 0-4 ('Provide the answer in the first line')."""
    import re
    if text is None:
        return None
    t = text.strip()
    for pat in (r"(?i)answer\s*(?:is|:)?\s*\(?([A-E])\)?(?![A-Za-z])", r"\(([A-E])\)",
                r"^\W*([A-E])(?:[\.\):]|\s*$)", r"(?<![A-Za-z])([A-E])(?![A-Za-z])"):
        m = re.search(pat, t, re.M)
        if m:
            return ord(m.group(1).upper()) - 65
    return None


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    print(len(rows), "RoTs;", sum(r["n_modes"] > 1 for r in rows), "with a tied mode")
    print(Counter(r["gold"] for r in rows))
    print(rows[0])
    for text, want in [("A", 0), ("B) 5%-25%", 1), ("The answer is C", 2), ("(D)", 3),
                       ("E\nMost people agree.", 4), ("I cannot answer that.", None)]:
        assert parse(text, {}) == want, (text, parse(text, {}), want)
    # sanity: a constant answer C reproduces the order of magnitude of the paper's 0.92
    for k in range(5):
        print("constant", chr(65 + k), round(sum(abs(r["gold"] - k) for r in rows) / len(rows), 3))
