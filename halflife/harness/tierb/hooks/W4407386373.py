"""Hook W4407386373 (CCPT, PROPERTY INDUCTION - EMERGENT, GPT-4o Base, Table 3 E = 40.8).

load_items        -> ccpt_emergent.csv rows whose positional index is in test_index.json['pi_emergent'] (200).
parse             -> the "property" value of the dictionary the model returns (Table 13 answer format).
judge_requests    -> 3 LLM-as-a-judge calls per (item, seed): the generated property scored against the
                     combination, the head noun (root) and the modifier, with Table 17's prompt.
score_with_judge  -> R = (rating - 1) / 9; E = max(R_combination - max(R_root, R_modifier), 0); mean over items.
score             -> refuses: E is undefined without the judge stage (run tierb_runner.py <wid> --judge first).

Verified against the authors' released results/pi_emergent_gpt-4o_naive.csv, which reproduces Table 3 exactly
(per-seed E 39.9 / 41.7 / 40.7, mean 40.8; R_N,P 83.3; R_H,M,P 44.1).
"""
import ast
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4407386373"
PARTS = ("combination", "root", "modifier")

JUDGE_MODEL = "gpt-4o-2024-05-13"
JUDGE_PROMPT = (
    'Concepts are characterized by properties. For example, the concept "a chicken in front of a fox" strongly '
    'exhibits the property "in danger." When given a concept and a property, your task is to evaluate how much the '
    'concept has the property on a scale from 1 to 10. You should follow the format: {"relevance": your_relevance_score}\n'
    "\nUse the following scoring criteria to assign a relevance score:\n"
    '- {"relevance": 1}: The concept does not have the property at all.\n'
    '- {"relevance": 2-3}: The concept rarely has the property.\n'
    '- {"relevance": 4-6}: The concept sometimes has the property.\n'
    '- {"relevance": 7-8}: The concept usually has the property, but not always.\n'
    '- {"relevance": 9}: The concept almost always has the property.\n'
    '- {"relevance": 10}: The concept always has the property.\n'
    "\n---\n\nExamples:\n\n---\n\nConcept: Rusty\nProperty: Useless\nRelevance: {\"relevance\": 7}\n"
    "\n---\n\nConcept: A chicken in the cage\nProperty: In danger\nRelevance: {\"relevance\": 2}\n"
    "\n---\n\nConcept: A chicken in front of a fox\nProperty: In danger\nRelevance: {\"relevance\": 9}\n"
    "\n---\n\nConcept: {concept}\nProperty: {property}\nRelevance:\n"
)


def load_items(cfg):
    import pandas as pd
    df = pd.read_csv(DATA / "ccpt_emergent.csv")
    idx = json.load(open(DATA / "test_index.json", encoding="utf-8"))["pi_emergent"]
    df = df[df.index.isin(idx)]
    if len(df) != 200:
        raise NeedsHuman(f"pi_emergent test split has {len(df)} rows, expected 200")  # noqa: F821
    return [{"id": str(i), "combination": r["combination"], "root": r["root"], "modifier": r["modifier"]}
            for i, r in df.iterrows()]


def parse(text, cfg=None):
    if not text:
        return None
    m = re.search(r"\{[^{}]*['\"]property['\"]\s*:.*?\}", text, re.S)
    if m:
        try:
            v = ast.literal_eval(m.group(0)).get("property")
            if isinstance(v, str) and v.strip():
                return v.strip().lower()
        except Exception:
            pass
    m = re.search(r"['\"]property['\"]\s*:\s*['\"]([^'\"]+)['\"]", text)
    return m.group(1).strip().lower() if m else None


def score(preds, golds, cfg=None):
    raise NeedsHuman("E needs the LLM-judge stage: run `python tierb_runner.py W4407386373 --judge` first")  # noqa: F821


def _text(rec):
    return rec["response"]["choices"][0]["message"].get("content")


def judge_requests(cfg, items, responses):
    by_id = {it["id"]: it for it in items}
    seeds = int(cfg["model"].get("seeds") or 1)
    reqs = []
    for (iid, s), rec in sorted(responses.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if s >= seeds or iid not in by_id:
            continue
        prop = parse(_text(rec))
        if not prop:
            continue                                   # unparsable generation: no judge call, dropped from the mean
        row = by_id[iid]
        for part in PARTS:
            concept = str(row[part])
            content = JUDGE_PROMPT.replace("{concept}", concept[:1].upper() + concept[1:]).replace("{property}", prop)
            reqs.append({"id": f"{iid}|{part}", "seed_idx": s, "meta": {"item": iid, "part": part, "property": prop},
                         "body": {"model": JUDGE_MODEL, "messages": [{"role": "user", "content": content}],
                                  "temperature": 0.0, "max_tokens": 32}})
    return reqs


def _relevance(rec):
    """(rating - 1) / 9 for a rating in 1..10 (experiment/utils.py get_relevance_score)."""
    t = _text(rec) or ""
    m = re.search(r"['\"]relevance['\"]\s*:\s*(\d+)", t) or re.search(r"\b(10|[1-9])\b", t)
    if not m:
        return None
    r = max(1, min(10, int(m.group(1))))
    return (r - 1) / 9


def score_with_judge(cfg, items, responses, judge_responses):
    per = []
    for it in items:
        vals = {}
        for part in PARTS:
            hits = [v for (jid, _), v in judge_responses.items() if jid == f"{it['id']}|{part}"]
            vals[part] = _relevance(hits[0]) if hits else None
        if any(v is None for v in vals.values()):
            continue
        per.append(max(vals["combination"] - max(vals["root"], vals["modifier"]), 0.0))
    return (sum(per) / len(per) if per else 0.0), per


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    print(len(rows), rows[0])
    for t, want in [('{"property": "stranded"}', "stranded"), ('Answer: {"property": "Fatal Attraction"}', "fatal attraction"),
                    ("{'property': 'wilted'}", "wilted"), ("no dict here", None)]:
        assert parse(t) == want, (t, parse(t))
    mk = lambda c: {"response": {"choices": [{"message": {"content": c}}]}}
    assert abs(_relevance(mk('{"relevance": 10}')) - 1.0) < 1e-9 and _relevance(mk('{"relevance": 1}')) == 0.0
    cfg = {"model": {"seeds": 1}}
    items = [{"id": "0", "combination": "a boat on the rocks", "root": "boat", "modifier": "rock"}]
    jr = {("0|combination", 0): mk('{"relevance": 8}'), ("0|root", 0): mk('{"relevance": 4}'),
          ("0|modifier", 0): mk('{"relevance": 1}')}
    v, p = score_with_judge(cfg, items, {}, jr)
    assert abs(v - (7 / 9 - 3 / 9)) < 1e-9, v
    reqs = judge_requests(cfg, items, {("0", 0): mk('{"property": "stranded"}')})
    assert len(reqs) == 3 and reqs[0]["id"] == "0|combination"
    print("judge req 0 tail:", repr(reqs[0]["body"]["messages"][0]["content"][-60:]))
    print("ok: E(example) =", round(v, 4), "| items", len(rows), "| judge reqs/item/seed", len(reqs))
