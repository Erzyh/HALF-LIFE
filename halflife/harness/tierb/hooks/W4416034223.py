"""W4416034223 (ManyIFEval, five instructions per prompt, GPT-4o): load_items keeps the 216 rows with
exactly five instructions and stores [instruction id, kwargs] pairs as the gold; score re-implements the
15 IFEval checkers that occur in these rows (repository instruction_following_eval, strict mode: the raw
reply must satisfy all five checkers; prompt-level accuracy, Eq. 1). Approximations vs the repository:
sentence counting uses a regex splitter instead of nltk punkt, capital-word tokenization uses a regex
instead of nltk word_tokenize, and the langdetect English check of the all-capital / all-lowercase
instructions is skipped (replies to these English prompts are English)."""
import json
import re
import urllib.request
from collections import Counter

import numpy as np

UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}


def load_items(cfg):
    with urllib.request.urlopen(urllib.request.Request(cfg["items"]["file_url"], headers=UA), timeout=120) as r:
        rows = [json.loads(l) for l in r.read().decode("utf-8").splitlines() if l.strip()]
    out = []
    for row in rows:
        if len(row["instruction_id_list"]) != 5:
            continue
        row["instruction_id_list"] = [[i, kw or {}] for i, kw in zip(row["instruction_id_list"], row["kwargs"])]
        out.append(row)
    return out


def parse(text, cfg):
    return text                                   # IFEval checks the raw (unstripped) reply


def _rel(x, n, relation):
    return x < n if relation == "less than" else x >= n


def _n_sentences(v):
    return len([s for s in re.split(r"(?<=[.!?])[\"')\]]*\s+", v.strip()) if s.strip()])


def _tokens(v):
    return re.findall(r"\w+(?:[-']\w+)*|[^\w\s]", v)


def check(iid, kw, v):
    if iid == "keywords:existence":
        return all(re.search(k, v, re.I) for k in kw["keywords"])
    if iid == "keywords:frequency":
        return _rel(len(re.findall(kw["keyword"], v, re.I)), kw["frequency"], kw["relation"])
    if iid == "keywords:forbidden_words":
        return not any(re.search(r"\b" + w + r"\b", v, re.I) for w in kw["forbidden_words"])
    if iid == "keywords:letter_frequency":
        return _rel(Counter(v.lower())[kw["letter"]], kw["let_frequency"], kw["let_relation"])
    if iid == "length_constraints:number_sentences":
        return _rel(_n_sentences(v), kw["num_sentences"], kw["relation"])
    if iid == "length_constraints:number_paragraphs":
        paras = re.split(r"\s?\*\*\*\s?", v)
        n = len(paras)
        for i, p in enumerate(paras):
            if not p.strip():
                if i in (0, len(paras) - 1):
                    n -= 1
                else:
                    return False
        return n == kw["num_paragraphs"]
    if iid == "length_constraints:number_words":
        return _rel(len(re.findall(r"\w+", v)), kw["num_words"], kw["relation"])
    if iid == "detectable_content:number_placeholders":
        return len(re.findall(r"\[.*?\]", v)) >= kw["num_placeholders"]
    if iid == "detectable_format:number_bullet_lists":
        return len(re.findall(r"^\s*\*[^\*].*$", v, re.M)) + len(re.findall(r"^\s*-.*$", v, re.M)) == kw["num_bullets"]
    if iid == "detectable_format:title":
        return any(t.lstrip("<").rstrip(">").strip() for t in re.findall(r"<<[^\n]+>>", v))
    if iid == "change_case:capital_word_frequency":
        return _rel(sum(1 for t in _tokens(v) if t.isupper()), kw["capital_frequency"], kw["capital_relation"])
    if iid == "change_case:english_capital":
        return v.isupper()
    if iid == "change_case:english_lowercase":
        return v.islower()
    if iid == "punctuation:no_comma":
        return not re.search(r"\,", v)
    if iid == "startend:quotation":
        s = v.strip()
        return len(s) > 1 and s[0] == '"' and s[-1] == '"'
    raise KeyError(f"no checker for instruction {iid}")


def score(preds, golds, cfg):
    per, failed = [], Counter()
    for p, g in zip(preds, golds):
        p = p or ""
        oks = [bool(p.strip()) and check(i, kw, p) for i, kw in g]
        for (i, _), ok in zip(g, oks):
            if not ok:
                failed[i] += 1
        per.append(1.0 if all(oks) else 0.0)
    print(f"[W4416034223] prompt-level accuracy {np.mean(per):.4f} over {len(per)}; failures by instruction: {dict(failed)}")
    return float(np.mean(per)), per


if __name__ == "__main__":
    g = [["keywords:forbidden_words", {"forbidden_words": ["cow", "speaker"]}], ["punctuation:no_comma", {}],
         ["startend:quotation", {}], ["length_constraints:number_words", {"num_words": 15, "relation": "less than"}],
         ["detectable_format:title", {}]]
    ok = '"<<Trip>> Fly to Tokyo and eat well; visit temples daily."'
    bad_comma = '"<<Trip>> Fly to Tokyo, eat well."'
    bad_word = '"<<Trip>> A cow greets you in Tokyo."'
    bad_long = '"<<Trip>> ' + " ".join(["word"] * 20) + '"'
    val, per = score([ok, bad_comma, bad_word, bad_long, ""], [g] * 5, {})
    assert per == [1.0, 0.0, 0.0, 0.0, 0.0] and abs(val - 0.2) < 1e-9, (val, per)
    assert check("detectable_format:number_bullet_lists", {"num_bullets": 2}, "Intro\n* one\n- two\n")
    assert check("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "A b. C d! E f?")
    assert not check("length_constraints:number_sentences", {"num_sentences": 3, "relation": "less than"}, "A b. C d! E f?")
    assert check("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "p1\n***\np2\n***\np3")
    assert check("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "at least"}, "I love NASA.")
    assert check("keywords:letter_frequency", {"letter": "y", "let_frequency": 2, "let_relation": "at least"}, "yay")
    assert check("change_case:english_lowercase", {}, "all lower here.") and not check("change_case:english_capital", {}, "Not All")
    assert check("detectable_content:number_placeholders", {"num_placeholders": 2}, "[name] at [address]")
    print("ok")
