"""Hook W4403370432 (CPSBench entity recognition, gpt-4 = gpt-4-turbo-0409, 3-shot, TABLE III Entity Ave).

load_items -> rebuilds the authors' prompts from the public mirror github.com/publicsubmission/CPSBench of the
              replication package: prompt/ner.txt (task description + all six type definitions), the released
              10-fold sentence-level split data/dataset/10-fold/fold_k/{train,test}_data.json and the
              SimCSE-retrieved shots input/fold_k/shot.json (the first three ids, as src/llm/gpt_inference.py
              does with --shot_num 3). Every test sentence of every fold is one item; the gold is its entity dict.
              Files are cached under external/data/tierb_items/W4403370432/.
render     -> the rebuilt prompt as the single user message (gpt_inference.py sends only a user turn).
parse      -> the first {...} dict of the reply (ast.literal_eval, then json), as src/eval.py; None if unreadable.
score      -> micro P/R/F1 over entity mentions of all six types with exact string match, TP/FP/FN summed over
              all sentences (src/eval.py compute_f1, the paper's Eq. 5 'Entity Ave'); an unreadable reply is an
              empty prediction. No per-item list.
"""
import ast, json, re, urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
RAW = "https://raw.githubusercontent.com/publicsubmission/CPSBench/main/"
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4403370432"
TYPES = ["Machine Domain", "Physical Device", "Environment Entity", "Design Domain", "Requirements", "Shared Phenomena"]
SHOTS = 3


def _fetch(rel):
    p = CACHE / rel
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(RAW + rel, headers=UA), timeout=120).read())
    return p.read_text(encoding="utf-8")


def load_items(cfg):
    tpl = _fetch("prompt/ner.txt")
    rows = []
    for k in range(10):
        train = json.loads(_fetch(f"data/dataset/10-fold/fold_{k}/train_data.json"))
        test = json.loads(_fetch(f"data/dataset/10-fold/fold_{k}/test_data.json"))
        shots = json.loads(_fetch(f"input/fold_{k}/shot.json"))
        if len(shots) != len(test):
            raise RuntimeError(f"fold {k}: {len(shots)} shot records for {len(test)} test sentences")
        for i, item in enumerate(test):
            if shots[i].get("text") != item["text"]:
                raise RuntimeError(f"fold {k} item {i}: shot.json is not aligned with test_data.json")
            ex = "\n## Examples\n"
            for sid in shots[i]["id"][:SHOTS]:
                ex += f"Input:{train[sid]['text']}\nAnswer:{train[sid]['entity']}\n"
            rows.append({"id": f"fold{k}_{i}", "fold": k, "text": item["text"], "entity": item["entity"],
                         "prompt": tpl.format(examples=ex, input_req=item["text"])})
    return rows


def render(cfg, row):
    return [{"role": "user", "content": row["prompt"]}]


def parse(text, cfg):
    m = re.search(r"\{[^}]*\}", text or "")
    if not m:
        return None
    s = m.group(0)
    for loader in (ast.literal_eval, json.loads):
        try:
            d = loader(s)
            return d if isinstance(d, dict) else None
        except Exception:
            continue
    return None


def _mentions(v):
    if isinstance(v, str):
        return {v}
    return {x for x in (v or []) if isinstance(x, str)}


def score(preds, golds, cfg):
    tp = fp = fn = 0
    for p, g in zip(preds, golds):
        p = p if isinstance(p, dict) else {}
        for k in TYPES:
            pk, gk = _mentions(p.get(k)), _mentions((g or {}).get(k))
            tp += len(pk & gk)
            fp += len(pk - gk)
            fn += len(gk - pk)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return (2 * prec * rec / (prec + rec) if prec + rec else 0.0), None


if __name__ == "__main__":
    reply = "Answer: {'Machine Domain': ['The system'], 'Physical Device': [], 'Environment Entity': ['users'], " \
            "'Design Domain': [], 'Requirements': ['log in'], 'Shared Phenomena': []}"
    p = parse(reply, {})
    assert p["Machine Domain"] == ["The system"] and parse("no dict here", {}) is None
    assert parse('{"Machine Domain": ["A"], "Physical Device": []}', {})["Machine Domain"] == ["A"]
    gold = {"Machine Domain": ["The system"], "Physical Device": ["a sensor"], "Environment Entity": ["users"],
            "Design Domain": [], "Requirements": [], "Shared Phenomena": []}
    v, _ = score([p, None], [gold, gold], {})
    # item 1: tp 2 (system, users), fp 1 (log in), fn 1 (sensor); item 2: fn 3 -> P 2/3, R 2/6, F1 4/9
    assert abs(v - 4 / 9) < 1e-12, v
    print("W4403370432 hook self-test ok")
