"""Hook W4414580759 (AppealCase, judgment reversal prediction, second-instance perspective, o4-mini F1 47.85).

render -> the runner's placeholder language cannot join the six sub-fields of the nested `first-instance`
          struct into one '## First-instance Documents' block, so the message is built here.
parse  -> the reply names any subset of {Non-Reversed, Factual determination errors, Legal application errors}
          (Appendix B.2: "There may be multiple answers"); returns a frozenset of canonical label strings,
          with the empty set standing for Non-Reversed.
score  -> F1-macro over the three classes, treating each as a one-vs-rest binary decision and averaging the
          three F1s (Table 3 lists Precision / Recall / F1-macro for this multi-label task). The runner's
          macro_f1 assumes exactly one label per item and cannot be used.
No load_items: items.hf + items.filter are runner facilities (default/train, new_information == True -> 4,519).

NOT verified against a live --prepare: the Hub parquet conversion is 106.9 MB, over this task's 50 MB
download ceiling. The field names used here come from the datasets-server /first-rows schema.
"""
NONE = "non-reversed"
FACT = "factual determination errors"
LAW = "legal application errors"
CLASSES = (NONE, FACT, LAW)
DOC_ORDER = ("header", "claim", "fact_description", "court_view", "judgment", "footer")

INSTRUCTION = (
    "Read the following first-instance judgment and determine whether the appellate court will reverse the "
    "judgment if an appeal is filed. If it will, specify whether the reason for changing the judgment is an "
    "error in fact-finding or an error in the application of the law."
)
TAIL = (
    '## Reason for reversal\nDirectly output the answer by selecting from ["Non-Reversed", '
    '"Factual determination errors", "Legal application errors"]. There may be multiple answers.\n'
    "Do not output anything else."
)


def _first_instance(row):
    fi = row.get("first-instance") or {}
    return "\n".join(str(fi.get(k) or "").strip() for k in DOC_ORDER if str(fi.get(k) or "").strip())


def render(cfg, row):
    si = row.get("second-instance") or {}
    user = (f"{INSTRUCTION}\n"
            f"## First-instance Documents\n{_first_instance(row)}\n"
            f"## Second-instance Claims\n{str(si.get('claim') or '').strip()}\n"
            f"## Second-instance Fact Description\n{str(si.get('fact_description') or '').strip()}\n"
            f"{TAIL}")
    return [{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": user}]


def parse(text, cfg=None):
    if text is None:
        return None
    low = str(text).lower()
    hits = {c for c in (FACT, LAW) if c in low}
    if hits:
        return frozenset(hits)
    return frozenset()                      # "Non-Reversed", or nothing recognisable: no reversal reason


def _as_set(v):
    """gold comes from items.jsonl as a list (possibly a numpy array serialised to list) or None."""
    if v is None:
        return frozenset()
    if isinstance(v, (frozenset, set)):
        return frozenset(str(x).strip().lower() for x in v)
    if isinstance(v, str):
        return frozenset([v.strip().lower()]) if v.strip() else frozenset()
    return frozenset(str(x).strip().lower() for x in v if str(x).strip())


def score(preds, golds, cfg=None):
    f1s = []
    for c in CLASSES:
        tp = fp = fn = 0
        for p, g in zip(preds, golds):
            ps, gs = _as_set(p), _as_set(g)
            pp = (not ps) if c == NONE else (c in ps)
            gg = (not gs) if c == NONE else (c in gs)
            tp += pp and gg
            fp += pp and not gg
            fn += (not pp) and gg
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * pr * rc / (pr + rc) if pr + rc else 0.0)
    return sum(f1s) / len(f1s), None        # set-level metric: the runner resamples items for the CI


if __name__ == "__main__":
    row = {"index": 7,
           "first-instance": {"header": "H", "claim": "C", "fact_description": "F", "court_view": "V",
                              "judgment": "J", "footer": ""},
           "second-instance": {"claim": "SC", "fact_description": "SF"}}
    msgs = render({}, row)
    assert msgs[0]["role"] == "system" and "## First-instance Documents\nH\nC\nF\nV\nJ\n" in msgs[1]["content"]
    assert msgs[1]["content"].endswith("Do not output anything else.")
    assert parse("Factual determination errors, Legal application errors") == frozenset([FACT, LAW])
    assert parse("Non-Reversed") == frozenset() and parse("") == frozenset() and parse(None) is None
    assert parse("Legal application errors") == frozenset([LAW])
    golds = [[], ["factual determination errors"], ["legal application errors"],
             ["factual determination errors", "legal application errors"]]
    perfect, _ = score([_as_set(g) for g in golds], golds)
    assert abs(perfect - 1.0) < 1e-9, perfect
    allnone, _ = score([frozenset()] * 4, golds)          # predict Non-Reversed everywhere
    print("ok | perfect macro-F1", perfect, "| always-Non-Reversed", round(allnone, 4))
    print("rendered user message:\n" + msgs[1]["content"])
