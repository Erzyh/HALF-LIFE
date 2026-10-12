"""Hook W4399911093 (gender representation bias, gpt-4-turbo noun/pronoun annotation, Table 4 F-score 90.24%).

load_items -> the 100 manually annotated Spanish Europarl sentences of data/validation/gt-es.txt in the authors'
              repository github.com/ellisalicante/grb-corpora, mirrored into
              external/data/tierb_items/W4399911093/. The file is a blank-line separated list of
              "<sentence>" "<word> - <P|N>, <M|F>\\n..." blocks; load_ground_truth() of the released
              code/validation/validation-gt-openai.ipynb upper-cases the annotation, splits it on ' - ', ', ' and
              newlines, regroups it in threes and drops groups whose word is in data/dataset-analysis/skiplist-es.txt.
              Rows: {id, sentence, gold} with gold the JSON dump of the filtered [WORD, P/N, M/F] groups.
parse      -> parse_response() of the same notebook, unchanged (upper-case, same split, same skip-list filter).
score      -> analyze_response() of the same notebook, pooled over the 100 sentences as the notebook's Total row
              does: nc identified (word and both attributes right), ni identified with a wrong attribute, nm missed,
              ne extra; P = nc/(nc+ni+ne), R = nc/(nc+nm), F = 2PR/(P+R) (Appendix C). per_item is None, so the
              runner resamples sentences and recomputes the pooled F-score for the CI.
No render: the config's user_template already carries the five priming examples and a {sentence} slot.
"""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4399911093"


def _skip_words():
    return {l.strip().upper() for l in (DATA / "skiplist-es.txt").read_text(encoding="utf-8").splitlines() if l.strip()}


def _groups(words_block, skip):
    words = re.split(r" - |, |\n", words_block.strip('"').upper())
    grouped = [words[i:i + 3] for i in range(0, len(words), 3)]
    return [g for g in grouped if g and g[0] not in skip]


def load_items(cfg):
    path = DATA / "gt-es.txt"
    if not path.exists():
        raise NeedsHuman(f"mirror gt-es.txt and skiplist-es.txt into {DATA} before --prepare")  # noqa: F821
    skip = _skip_words()
    rows = []
    for i, block in enumerate(path.read_text(encoding="utf-8").strip().split("\n\n")):
        sentence, words = block.strip().split(' "')
        rows.append({"id": str(i + 1), "sentence": sentence.strip('"'),
                     "gold": json.dumps(_groups(words, skip), ensure_ascii=False)})
    if len(rows) != 100:
        raise NeedsHuman(f"{len(rows)} validation sentences, expected 100 (Appendix C)")  # noqa: F821
    return rows


def parse(text, cfg):
    if not text:
        return None
    skip = _skip_words()
    cleaned = re.sub(r"\s+\n", "\n", text.strip().upper())
    words = re.split(r" - |, |\n", cleaned)
    groups = [words[i:i + 3] for i in range(0, len(words), 3)]
    return [g for g in groups if g and g[0] not in skip]


def _counts(model_words, gt_words):
    """analyze_response() of the released notebook -> (nc, nm, ni, ne)."""
    extra = [list(w) for w in model_words]
    nc = nm = ni = 0
    for item in gt_words:
        if item in extra:
            nc += 1
            extra.remove(item)
        elif item[0] not in [w[0] for w in extra]:
            nm += 1
        else:
            ni += 1
            for w in extra:
                if item[0] == w[0]:
                    extra.remove(w)
                    break
    return nc, nm, ni, len(extra)


def score(preds, golds, cfg):
    nc = nm = ni = ne = 0
    for p, g in zip(preds, golds):
        a, b, c, d = _counts(p or [], json.loads(g))
        nc += a; nm += b; ni += c; ne += d
    prec = nc / (nc + ni + ne) if (nc + ni + ne) else 0.0
    rec = nc / (nc + nm) if (nc + nm) else 0.0
    f = 0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec)
    return f, None


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    print(len(rows), "sentences;", sum(len(json.loads(r["gold"])) for r in rows), "annotated words")
    print("id1:", rows[0]["sentence"][:70])
    print("gold1:", json.loads(rows[0]["gold"]))
    reply = "Comisión - N, F\ndeclaración - N, F\nperíodo - N, M\nsesiones - N, F\nfin - N, M\nespaldas - N, F"
    print("parse:", parse(reply, {}))
    golds = [r["gold"] for r in rows]
    perfect = [json.loads(g) for g in golds]
    print("perfect F", round(score(perfect, golds, {})[0], 4))
    print("empty   F", round(score([[] for _ in golds], golds, {})[0], 4))
    flipped = [[[w[0], w[1], "F" if w[2] == "M" else "M"] for w in json.loads(g)] for g in golds]
    print("gender-flipped F (all attributes wrong):", round(score(flipped, golds, {})[0], 4))
