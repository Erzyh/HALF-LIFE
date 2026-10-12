"""Hook for W4416034345 (SLDS, Table 2 row 'o3-mini one-shot', ROUGE-L 18.21).

load_items() reads the test split of all nine decision/headnote language pairs of ipst/slds plus each
pair's one_shot_examples row (the shortest validation sample, Appendix F.2). render() builds the
lighteval-style one-shot chat (Appendix H.2): system = Prompt 2; user = Prompt 3 with the example
decision; assistant = the example's gold headnote; user = Prompt 3 with the target decision. The language
word is the written-out headnote language. score() is rouge_score's default rougeL F1 (lowercase,
non-[a-z0-9] characters become separators, no stemming) x1 per item, macro-averaged over the nine pairs.
"""
import io, json, re, urllib.request
from collections import defaultdict
from pathlib import Path

WID = "W4416034345"
PAIRS = ["de_de", "de_fr", "de_it", "fr_de", "fr_fr", "fr_it", "it_de", "it_fr", "it_it"]
LANG = {"de": "German", "fr": "French", "it": "Italian"}
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / WID
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()


def _parquet(dataset, config, split):
    import pandas as pd
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{config}.{split}.parquet"
    if not p.exists():
        listing = json.loads(_get(f"https://huggingface.co/api/datasets/{dataset}/parquet").decode("utf-8"))
        urls = listing[config][split]
        if len(urls) != 1:
            raise RuntimeError(f"{config}/{split}: expected one parquet shard, got {len(urls)}")
        p.write_bytes(_get(urls[0]))
    return pd.read_parquet(io.BytesIO(p.read_bytes())).to_dict("records")


def load_items(cfg):
    dataset = cfg["items"]["hf"]["dataset"]
    rows = []
    for pair in PAIRS:
        ex = _parquet(dataset, pair, "one_shot_examples")
        if len(ex) != 1:
            raise RuntimeError(f"{pair}: expected one one-shot example, got {len(ex)}")
        ex = ex[0]
        for r in _parquet(dataset, pair, "test"):
            rows.append({"sample_id": str(r["sample_id"]), "pair": pair, "decision": r["decision"],
                         "language": LANG[str(r["headnote_language"]).strip().lower()],
                         "example_decision": ex["decision"], "example_headnote": ex["headnote"],
                         "gold": {"pair": pair, "headnote": r["headnote"]}})
    return rows


def _user(cfg, decision, language):
    return cfg["prompt"]["user_template"].replace("{decision}", str(decision)).replace("{language}", language)


def render(cfg, row):
    return [{"role": "system", "content": cfg["prompt"]["system"]},
            {"role": "user", "content": _user(cfg, row["example_decision"], row["language"])},
            {"role": "assistant", "content": row["example_headnote"]},
            {"role": "user", "content": _user(cfg, row["decision"], row["language"])}]


def _tokens(s):
    return [t for t in re.sub(r"[^a-z0-9]+", " ", str(s).lower()).split() if t]


def rouge_l(pred, gold):
    x, y = _tokens(pred), _tokens(gold)
    if not x or not y:
        return 0.0
    prev = [0] * (len(y) + 1)
    for xi in x:
        cur = [0] * (len(y) + 1)
        for j, yj in enumerate(y):
            cur[j + 1] = prev[j] + 1 if xi == yj else max(prev[j + 1], cur[j])
        prev = cur
    lcs = prev[-1]
    if lcs == 0:
        return 0.0
    p, r = lcs / len(x), lcs / len(y)
    return 2 * p * r / (p + r)


def score(preds, golds, cfg):
    per, by_pair = [], defaultdict(list)
    for p, g in zip(preds, golds):
        v = rouge_l(p or "", g["headnote"])
        per.append(v)
        by_pair[g["pair"]].append(v)
    means = {k: sum(v) / len(v) for k, v in by_pair.items()}
    print(f"[{WID}] per-pair ROUGE-L x100: " + ", ".join(f"{k} {100 * v:.2f} (n={len(by_pair[k])})" for k, v in sorted(means.items())))
    return sum(means.values()) / len(means), per


if __name__ == "__main__":
    assert abs(rouge_l("Art. 8 EMRK; Prüfung der Verhältnismässigkeit.", "Art. 8 EMRK; Prüfung der Verhältnismässigkeit.") - 1.0) < 1e-9
    assert rouge_l("", "abc") == 0.0 and rouge_l("x y z", "a b c") == 0.0
    assert abs(rouge_l("the cat sat", "the cat sat on the mat") - 2 * 1.0 * 0.5 / 1.5) < 1e-9
    v, per = score(["a b c", "a b c", "x"], [{"pair": "de_de", "headnote": "a b c"}, {"pair": "fr_fr", "headnote": "a b"},
                                              {"pair": "fr_fr", "headnote": "x y"}], {})
    assert abs(v - (1.0 + (0.8 + 2 / 3) / 2) / 2) < 1e-9 and len(per) == 3
    cfg = {"prompt": {"system": "S", "user_template": "Leading decision:\n```{decision}```\n\nGenerate a headnote in {language} for the leading decision above."}}
    m = render(cfg, {"decision": "D {x}", "language": "German", "example_decision": "E", "example_headnote": "H"})
    assert [x["role"] for x in m] == ["system", "user", "assistant", "user"] and "D {x}" in m[3]["content"] and m[2]["content"] == "H"
    print("ok")
