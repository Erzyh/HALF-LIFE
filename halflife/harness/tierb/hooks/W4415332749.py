"""Hook W4415332749 (J4R / ReasoningJudgeBench, o1 pairwise judging accuracy, Table 6 Avg. = 73.10).

The benchmark is 1,483 pairwise samples spread over 13 Hugging Face splits (Salesforce/ReasoningJudgeBench,
config 'default'). Two runner facilities are missing, hence this hook:

load_items  each sample is judged twice, with the two responses swapped (Sec. 5 / App. C.2), so one dataset
            row becomes two rendered items: order AB (A = positive_response, gold [[A>B]]) and order BA
            (A = negative_response, gold [[B>A]]). gold carries the sample id ("A>B|<problem_id>") because
            the runner hands score() only (preds, golds).
parse       the verdict is the LAST [[A>B]] / [[B>A]] marker in the reply (the explanation above it may
            quote the labels).
score       "consistent accuracy": a sample counts as correct only when BOTH orders were judged correctly
            (App. C.2). Value = micro-average over the samples for which both orders are archived, which is
            the paper's Avg. column ("a microaverage across benchmark splits", Table 1 caption); the per-item
            list is per sample, so the runner's bootstrap CI is over samples, not over calls.
Deterministic: splits are read in the fixed order below, rows keep their file order, no shuffling here
(the runner permutes with seed 20260907).
"""
import io
import json
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
SPLIT_GROUP = {                     # App. C (per-split data source breakdown), 1483 = 598 + 260 + 325 + 300
    "arc_challenge_pairwise": "multi_hop", "bbeh_be_pairwise": "multi_hop", "folio_pairwise": "multi_hop",
    "reclor_pairwise": "multi_hop",
    "aime_4o_pairwise": "math", "aime_pairwise": "math", "bbeh_ma_pairwise": "math",
    "olympiadbench_pairwise": "math",
    "bbeh_cu_pairwise": "everyday", "bbeh_dq_pairwise": "everyday", "bbeh_hyper_pairwise": "everyday",
    "strategy_qa_pairwise": "everyday",
    "supergpqa_pairwise": "domain",
}
VERDICT = re.compile(r"\[\[\s*([AB])\s*>\s*([AB])\s*\]\]")


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()


def load_items(cfg):
    import pandas as pd
    hf = cfg["items"]["hf"]
    listing = json.loads(_get(f"https://huggingface.co/api/datasets/{hf['dataset']}/parquet").decode("utf-8"))
    files = listing[hf.get("config", "default")]
    rows = []
    for split in hf["splits"]:
        if split not in files:
            raise NeedsHuman(f"split {split} missing from the parquet listing: {sorted(files)}")  # noqa: F821
        df = pd.concat([pd.read_parquet(io.BytesIO(_get(u))) for u in files[split]], ignore_index=True)
        recs = df.to_dict("records")
        for r in recs:
            pid, pos, neg = str(r["problem_id"]), r["positive_response"], r["negative_response"]
            common = {"question": r["instruction"], "split": split, "group": SPLIT_GROUP[split]}
            rows.append({"id": pid + "|AB", "response_a": pos, "response_b": neg,
                         "gold": "A>B|" + pid, **common})
            rows.append({"id": pid + "|BA", "response_a": neg, "response_b": pos,
                         "gold": "B>A|" + pid, **common})
    k = cfg["items"].get("max_samples")
    if k and 2 * k < len(rows):
        # Draw the cost subset by SAMPLE, keeping both orders of each, so that the consistent-accuracy metric has
        # complete pairs; the runner's own cap subset is item-level and left 1 complete pair out of 127 samples.
        import numpy as np
        pids = sorted({r["gold"].partition("|")[2] for r in rows})
        keep = set(np.array(pids)[np.random.default_rng(20260907).choice(len(pids), k, replace=False)].tolist())
        rows = [r for r in rows if r["gold"].partition("|")[2] in keep]
    return rows


def parse(text, cfg):
    if not text:
        return None
    hits = VERDICT.findall(text)
    if not hits:
        return None
    a, b = hits[-1]
    return f"{a}>{b}" if a != b else None


def score(preds, golds, cfg):
    pairs = {}
    for p, g in zip(preds, golds):
        want, _, pid = str(g).partition("|")
        pairs.setdefault(pid, []).append(1 if (p is not None and p == want) else 0)
    complete = [v for v in pairs.values() if len(v) == 2]
    if not complete:
        raise NeedsHuman("no sample has both orders archived; consistent accuracy is undefined")  # noqa: F821
    per = [1.0 if sum(v) == 2 else 0.0 for v in complete]
    dropped = len(pairs) - len(complete)
    if dropped:
        print(f"[W4415332749] {dropped} samples had only one of the two orders archived and were dropped")
    return sum(per) / len(per), per


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    cfg = {"items": {"hf": {"dataset": "Salesforce/ReasoningJudgeBench", "config": "default",
                            "splits": list(SPLIT_GROUP)}}}
    rows = load_items(cfg)
    from collections import Counter
    print(len(rows), "rendered items;", len(rows) // 2, "samples")
    print(Counter(r["group"] for r in rows))          # each group counted twice (2 orders per sample)
    print({k: rows[0][k] for k in ("id", "gold", "split", "group")})
    print(parse("Explanation: A uses [[A>B]] style.\nVerdict: [[B>A]].", cfg))      # -> B>A
    print(score(["A>B", "B>A", "A>B", "A>B"],
                ["A>B|x", "B>A|x", "A>B|y", "B>A|y"], cfg))                          # -> (0.5, [1.0, 0.0])
