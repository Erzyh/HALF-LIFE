"""Hook W4399912745 (ALiiCE, GPT-4 Turbo with 5 passages on ALCE ASQA, Table 1 'Correct.' = ALCE str_em).

load_items -> reads asqa_eval_gtr_top100.json (948 items) extracted from ALCE-data.tar (princeton-nlp/ALCE-data) into
              external/data/tierb_items/W4399912745/ and adds documents_block: one line per passage of docs[0:5] in the
              format the config describes for the paper's Table 7, 'Documents [k] (Title: {title}) {text}' (DOC_LINE; the
              ALiiCE code release instead renders 'Document [k] Title: {title}: {text}' joined by blank lines - see the
              config notes). The gold field qa_pairs keeps question + short_answers per sub-question.
score      -> ALCE str_em exactly as in ALCE eval.py / utils.py (compute_str_em, exact_presence, normalize_answer) after
              utils.remove_citations on the response, as ALiiCE eval.py does (no truncation at the first newline: ALiiCE's
              eval.py has none). Per item: share of qa_pairs with a short answer present in the normalised response; the
              value is the mean over items in 0-1 (metric.scale 100 gives the paper's percent).
"""
import json
import re
import string
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4399912745" / "asqa_eval_gtr_top100.json"
DOC_LINE = "Documents [{k}] (Title: {title}) {text}"   # config prompt.placeholders_prose (paper Table 7)
N_DOCS = 5


def load_items(cfg):
    if not DATA.exists():
        raise NeedsHuman(f"extract asqa_eval_gtr_top100.json from ALCE-data.tar into {DATA.parent}")  # noqa: F821
    rows = []
    for x in json.loads(DATA.read_text(encoding="utf-8")):
        docs = x["docs"][:N_DOCS]
        rows.append({"sample_id": str(x["sample_id"]), "question": x["question"],
                     "documents_block": "\n".join(DOC_LINE.format(k=i + 1, title=d["title"], text=d["text"]) for i, d in enumerate(docs)),
                     "qa_pairs": [{"question": q.get("question"), "short_answers": list(q.get("short_answers") or [])}
                                  for q in x["qa_pairs"]]})
    return rows


def normalize_answer(s):                       # ALCE utils.normalize_answer
    s = "".join(ch for ch in str(s).lower() if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def remove_citations(sent):                    # ALCE utils.remove_citations
    return re.sub(r"\[\d+", "", re.sub(r" \[\d+", "", sent)).replace(" |", "").replace("]", "")


def exact_presence(short_answers, context):    # ALCE eval.exact_presence
    n_context = normalize_answer(context)
    return any(normalize_answer(sa) in n_context for sa in short_answers)


def score(preds, golds, cfg):
    per = []
    for p, qa in zip(preds, golds):
        out = remove_citations((p or "").strip())
        hits = [exact_presence(q.get("short_answers") or [], out) for q in (qa or [])]
        per.append(sum(hits) / len(hits) if hits else 0.0)
    return (sum(per) / len(per) if per else 0.0), per


if __name__ == "__main__":
    golds = [[{"short_answers": ["Daei", "Ali Daei"]}, {"short_answers": ["Bican", "Josef Bican"]}],
             [{"short_answers": ["1995"]}]]
    preds = ["Ali Daei[1] holds the record for men's international goals, while the all-time record belongs to others [2][3].",
             "It was in the year nineteen ninety-five apparently."]
    v, per = score(preds, golds, {})
    assert per == [0.5, 0.0] and abs(v - 0.25) < 1e-12, (v, per)
    assert score(["In 1,995."], [golds[1]], {})[1] == [1.0]          # punctuation is removed before matching (ALCE)
    # ALCE order: lower -> strip punctuation (hyphen vanishes, no space) -> drop articles -> collapse whitespace
    assert normalize_answer("The Ali-Daei!") == "alidaei" and normalize_answer("An answer, the End.") == "answer end"
    assert remove_citations("glass[1] or plastic[2][3].") == "glass or plastic."
    rows = load_items({})
    assert len(rows) == 948 and rows[0]["documents_block"].startswith("Documents [1] (Title: ") and rows[0]["documents_block"].count("\nDocuments [") == 4
    print("W4399912745 hook self-test ok;", rows[0]["question"], "|", rows[0]["documents_block"][:90].replace("\n", " / "))
