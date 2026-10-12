"""Hook W7162149911 (LLM annotation guidelines, GPT-5 simple prompting on NCBI Disease, Table 1 S column F1).

load_items -> the 100 PubAnnotation JSON documents of the NCBI Disease development split, released with the paper at
              github.com/KonWooKim/llm-guideline-moderation (data/datasets/ncbi_disease/valid) and mirrored once into
              external/data/tierb_items/W7162149911/valid/. Each file: {text, sourcedb, sourceid,
              denotations: [{id, span:{begin,end}, obj}]}. Rows: {id, input_text, gold} where gold is the JSON dump
              of the gold (begin, end, label) triples. 100 documents, 791 gold entities (matches Table 1 / Table 5).
parse      -> json.loads of the reply (optional ``` fence stripped), key "annotations"; offsets are realigned to the
              document text the way the repo's align_annotations does in spirit: keep (start, end) when the slice
              already equals the returned span text, otherwise take the occurrence of that text nearest the claimed
              start. Returns a list of [begin, end, label].
score      -> strict-match micro P/R/F1 over all documents (exact begin, end and label, one-to-one), i.e. the
              PubAnnotation evaluator with soft_match_characters = soft_match_words = 0. per_item is None so the
              runner bootstraps by resampling documents and recomputing the micro F1.
No render: the config's user_template with {input_text} is a runner facility.
"""
import json
import re
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W7162149911" / "valid"
LABELS = {"SpecificDisease", "DiseaseClass", "Modifier", "CompositeMention"}


def load_items(cfg):
    files = sorted(DATA.glob("*.json"))
    if len(files) != 100:
        raise NeedsHuman(  # noqa: F821 (injected by the runner)
            f"expected the 100 NCBI Disease valid documents in {DATA}, found {len(files)}")
    rows = []
    for p in files:
        doc = json.loads(p.read_text(encoding="utf-8"))
        gold = [[d["span"]["begin"], d["span"]["end"], d["obj"]] for d in doc.get("denotations", [])]
        rows.append({"id": str(doc.get("sourceid") or p.stem), "input_text": doc["text"],
                     "gold": json.dumps(gold, ensure_ascii=False)})
    n = sum(len(json.loads(r["gold"])) for r in rows)
    if n != 791:
        raise NeedsHuman(f"gold entity count {n} != 791 (Table 1 'NCBI (791)')")  # noqa: F821
    return rows


def _realign(text, start, end, span):
    """Repo behaviour in spirit: trust the offsets when they already quote the span, else relocate the span text."""
    if not isinstance(span, str) or not span:
        return (start, end) if isinstance(start, int) and isinstance(end, int) else None
    if isinstance(start, int) and isinstance(end, int) and text[start:end] == span:
        return start, end
    hits = [m.start() for m in re.finditer(re.escape(span), text)]
    if not hits:
        return None
    anchor = start if isinstance(start, int) else 0
    b = min(hits, key=lambda h: abs(h - anchor))
    return b, b + len(span)


def parse(text, cfg):
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"```\s*$", "", t).strip()
    try:
        obj = json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, re.S)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
        except Exception:
            return None
    if not isinstance(obj, dict) or not isinstance(obj.get("annotations"), list):
        return None
    return obj["annotations"]


def _pred_triples(anns, text):
    out = []
    for a in anns or []:
        if not isinstance(a, dict):
            continue
        label = str(a.get("entity") or "").strip()
        if label not in LABELS:
            continue
        pos = _realign(text, a.get("start"), a.get("end"), a.get("text"))
        if pos:
            out.append((pos[0], pos[1], label))
    return out


def score(preds, golds, cfg):
    """preds: parsed annotation lists (or None); golds: JSON dumps of the gold triples, in items.jsonl order.

    The document text is recovered from the gold file so the offsets can be realigned; documents are matched by
    their gold triples, which are unique per document in this split."""
    by_gold = {}
    for p in sorted(DATA.glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        key = json.dumps([[d["span"]["begin"], d["span"]["end"], d["obj"]] for d in doc.get("denotations", [])],
                         ensure_ascii=False)
        by_gold.setdefault(key, doc["text"])
    tp = n_pred = n_gold = 0
    for pred, gold in zip(preds, golds):
        gold_triples = [tuple(x) for x in json.loads(gold)]
        text = by_gold.get(gold, "")
        pt = Counter(_pred_triples(pred, text))
        gt = Counter(gold_triples)
        tp += sum((pt & gt).values())
        n_pred += sum(pt.values())
        n_gold += sum(gt.values())
    prec = tp / n_pred if n_pred else 0.0
    rec = tp / n_gold if n_gold else 0.0
    f1 = 0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec)
    return f1, None


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    print(len(rows), "documents,", sum(len(json.loads(r["gold"])) for r in rows), "gold entities")
    print("first id", rows[0]["id"], "| text[:60]", rows[0]["input_text"][:60])
    # self-test: a perfect prediction must score 1.0, an empty one 0.0, a half prediction ~0.67
    perfect, half = [], []
    for r in rows:
        g = json.loads(r["gold"])
        text = r["input_text"]
        perfect.append([{"start": b, "end": e, "text": text[b:e], "entity": lab} for b, e, lab in g])
        half.append([{"start": b, "end": e, "text": text[b:e], "entity": lab} for b, e, lab in g[::2]])
    golds = [r["gold"] for r in rows]
    print("perfect F1", round(score(perfect, golds, {})[0], 4))
    print("empty   F1", round(score([[] for _ in rows], golds, {})[0], 4))
    print("half    F1", round(score(half, golds, {})[0], 4))
    print("parse   ", parse('```json\n{"annotations": [{"start": 1, "end": 4, "text": "abc", "entity": "Modifier"}]}\n```', {}))
