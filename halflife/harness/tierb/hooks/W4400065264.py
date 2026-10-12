"""Hook W4400065264 (Following Length Constraints in Instructions, AlpacaEval-LI violation rate Vlt%).

Only score() is needed: items and prompt come from the config (items.file_url is the released
AlpacaEval-LI file, whose `instruction` field already carries the Figure-1 length template, and whose
`max_len` field is the per-prompt word limit used as the gold value).

Vlt% (Sec. 3.1.3) = share of responses whose word count exceeds the prompt's max_len, where the word
count is the paper's Appendix A function: nltk.word_tokenize minus pure-punctuation tokens.
per-item 0/1 is returned so the runner's item bootstrap gives the CI.
"""
import string

_PUNCT = set(string.punctuation)


def count_words(text) -> int:
    """Appendix A of the paper, verbatim:
        from nltk.tokenize import word_tokenize
        import string
        def count_words(text) -> int:
            return len([word for word in word_tokenize(text) if word not in string.punctuation])
    """
    from nltk.tokenize import word_tokenize          # needs the punkt/punkt_tab data (nltk.download)
    return len([w for w in word_tokenize(text or "") if w not in _PUNCT])


def score(preds, golds, cfg):
    per = []
    for p, g in zip(preds, golds):
        try:
            limit = int(g)
        except (TypeError, ValueError):
            raise NeedsHuman(f"item gold (max_len) is not an integer: {g!r}")  # noqa: F821 (injected by the runner)
        if p is None:                                 # no reply archived -> not counted as a violation
            per.append(0.0)
            continue
        per.append(1.0 if count_words(p) > limit else 0.0)
    if not per:
        return 0.0, []
    return sum(per) / len(per), per


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    demo = ["one two three four five six", "short answer", None]
    golds = [5, 5, 5]
    print(count_words("Hello, world! This is a test-case: 3.5 words, isn't it?"))   # -> 11
    print(score(demo, golds, {}))                                                   # -> (0.333..., [1.0, 0.0, 0.0])
