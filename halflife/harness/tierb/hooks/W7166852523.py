"""Hook W7166852523 (Dark & Stormy, GPT-5 synthetic Bulwer-Lytton sentences, Table 1 avg. token length 73.7).

load_items  there is no input dataset: the run is 1,000 one-shot generations whose only varying part is the
            genre, with the quotas printed in Appendix B ("Adventure, Science Fiction (100 each), Purple Prose,
            Romance, Crime & Detective, Vile Puns (150 each), Western, Historical Fiction, Children's
            Literature, and Fantasy & Horror (50 each)"). Rows are emitted in the fixed order below (the
            runner permutes them with seed 20260907), so the item set is deterministic.
score       Table 1 reports the mean number of tokens per generated sentence, "Sentences tokenized with
            gemma-3-1b-pt". That tokenizer is a gated Hugging Face repo (google/gemma-3-1b-pt, gated:manual),
            so this hook does not download it: it loads a tokenizer from the local directory named by the
            config (metric.tokenizer_dir) or by the HALFLIFE_GEMMA_TOKENIZER environment variable and raises
            NeedsHuman when neither is present. per-item token counts give the runner's bootstrap CI.
No render/parse: the config's user_template and "free text" parse are runner facilities; the whole reply is
the generated sentence ("Your final output should contain only the sentence").
"""
import os

GENRES = [                       # Appendix B, quotas as printed; 2*100 + 4*150 + 4*50 = 1000
    ("Adventure", 100),
    ("Science Fiction", 100),
    ("Purple Prose", 150),
    ("Romance", 150),
    ("Crime & Detective", 150),
    ("Vile Puns", 150),
    ("Western", 50),
    ("Historical Fiction", 50),
    ("Children's Literature", 50),
    ("Fantasy & Horror", 50),
]


def load_items(cfg):
    rows = []
    for genre, n in GENRES:
        slug = "".join(ch if ch.isalnum() else "_" for ch in genre.lower())
        for i in range(n):
            rows.append({"id": f"{slug}-{i:03d}", "genre": genre})
    return rows


def _tokenizer(cfg):
    path = (cfg.get("metric") or {}).get("tokenizer_dir") or os.environ.get("HALFLIFE_GEMMA_TOKENIZER")
    if not path or not os.path.isdir(path):
        raise NeedsHuman(                                        # noqa: F821 (injected by the runner)
            "Table 1 counts tokens with gemma-3-1b-pt, a gated Hugging Face repo (gated:manual). Accept the "
            "Gemma licence and place the tokenizer files locally, then set metric.tokenizer_dir (or "
            "HALFLIFE_GEMMA_TOKENIZER); an ungated mirror of the same tokenizer is a substitution a human must approve.")
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(path)


def score(preds, golds, cfg):
    tok = _tokenizer(cfg)
    per = [float(len(tok.encode(p, add_special_tokens=False))) for p in preds if p is not None]
    if not per:
        return 0.0, []
    return sum(per) / len(per), per


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    from collections import Counter
    print(len(rows), Counter(r["genre"] for r in rows))
    print(rows[0], rows[-1])
    try:
        score(["a sentence"], [None], {})
    except NeedsHuman as e:
        print("NeedsHuman as expected:", str(e)[:60], "...")
