"""Hook W4410280647 (Humanity's Last Exam, o3-mini high, text-only accuracy, Table 1 / Appendix C.2).

The dataset cais/hle is gated (401 without an accepted-terms token) and 274 MB, so load_items reads a local copy
that a human places under external/data/tierb_items/W4410280647/ after accepting the terms: the Feb-2025 revision
of data/test-00000-of-00001.parquet, or a jsonl with id, question, answer, answer_type, image. Text-only rows
(empty image) are kept. Status stays needs_human until that file exists.

render            -> system prompt chosen by answer_type (exactMatch / multipleChoice, Appendix C.1.1) + question.
parse             -> the 'Exact Answer:' / 'Answer:' line (informational; the judge decides correctness).
judge_requests    -> one o3-mini-2025-01-31 call per archived response with the Appendix C.1.1 judge prompt and
                     structured decoding (json_schema: extracted_final_answer, reasoning, correct, confidence).
score_with_judge  -> accuracy = share of responses the judge marks correct == 'yes'; per-item 0/1.
"""
import json, re, sys
from pathlib import Path

CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4410280647"
JUDGE_MODEL = "o3-mini-2025-01-31"
JUDGE_PROMPT = ("Judge whether the following [response] to [question] is correct or not based on the precise and "
                "unambiguous [correct_answer] below.\n[question]: {question}\n[response]: {response}\n"
                "Your judgement must be in the format and criteria specified below:\n"
                "extracted_final_answer: The final exact answer extracted from the [response]. Put the extracted answer "
                "as 'None' if there is no exact, final answer to extract from the response.\n"
                "[correct_answer]: {correct_answer}\n"
                "reasoning: Explain why the extracted_final_answer is correct or incorrect based on [correct_answer], "
                "focusing only on if there are meaningful differences between [correct_answer] and the "
                "extracted_final_answer. Do not comment on any background to the problem, do not attempt to solve the "
                "problem, do not argue for any answer different than [correct_answer], focus only on whether the "
                "answers match.\n"
                "correct: Answer 'yes' if extracted_final_answer matches the [correct_answer] given above, or is within "
                "a small margin of error for numerical problems. Answer 'no' otherwise, i.e. if there if there is any "
                "inconsistency, ambiguity, non-equivalency, or if the extracted answer is incorrect.\n"
                "confidence: The extracted confidence score between 0% and 100% from [response]. Put 100 if there is "
                "no confidence score available.")
SCHEMA = {"type": "json_schema", "json_schema": {"name": "ExtractedAnswer", "strict": True, "schema": {
    "type": "object", "additionalProperties": False,
    "properties": {"extracted_final_answer": {"type": "string"}, "reasoning": {"type": "string"},
                   "correct": {"type": "string", "enum": ["yes", "no"]}, "confidence": {"type": "integer"},
                   "strict": {"type": "boolean"}},
    "required": ["extracted_final_answer", "reasoning", "correct", "confidence", "strict"]}}}


def _needs_human(msg):
    exc = getattr(sys.modules.get("__main__"), "NeedsHuman", RuntimeError)
    raise exc(msg)


def load_items(cfg):
    files = sorted(CACHE.glob("*.parquet")) + sorted(CACHE.glob("*.jsonl"))
    if not files:
        _needs_human("cais/hle is gated: accept the terms on huggingface.co, then place the Feb-2025 revision of "
                     "data/test-00000-of-00001.parquet (or a text-only jsonl with id, question, answer, answer_type, "
                     f"image) under {CACHE}")
    rows = []
    for f in files:
        if f.suffix == ".parquet":
            import pandas as pd
            rows += pd.read_parquet(f, columns=["id", "question", "answer", "answer_type", "image"]).to_dict("records")
        else:
            rows += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = []
    for r in rows:
        if r.get("image"):
            continue
        out.append({k: r.get(k) for k in ("id", "question", "answer", "answer_type")})
    return out


def render(cfg, row):
    by_type = cfg["prompt"].get("system_by_answer_type") or {}
    system = by_type.get(str(row.get("answer_type")), cfg["prompt"]["system"])
    return [{"role": "system", "content": system}, {"role": "user", "content": str(row["question"])}]


def parse(text, cfg):
    m = re.search(r"(?im)^\s*(?:Exact Answer|Answer)\s*:\s*(.+?)\s*$", text or "")
    return m.group(1) if m else None


def judge_requests(cfg, items, responses):
    by_id = {}
    for (iid, s), rec in responses.items():
        by_id.setdefault(str(iid), []).append((s, rec))
    reqs = []
    for it in items:
        for s, rec in sorted(by_id.get(str(it["id"]), [])):
            text = rec["response"]["choices"][0]["message"].get("content") or ""
            prompt = JUDGE_PROMPT.format(question=it["messages"][-1]["content"], response=text, correct_answer=it["gold"])
            reqs.append({"id": it["id"], "seed_idx": s, "meta": {},
                         "body": {"model": JUDGE_MODEL, "messages": [{"role": "user", "content": prompt}],
                                  "response_format": SCHEMA, "max_completion_tokens": 4096}})
    return reqs


def _correct(content):
    try:
        return str(json.loads(content).get("correct", "")).strip().lower() == "yes"
    except Exception:
        return bool(re.search(r"(?im)^\s*\"?correct\"?\s*:\s*\"?yes", content or ""))


def score_with_judge(cfg, items, responses, judge_responses):
    by_id = {str(iid): rec for (iid, s), rec in judge_responses.items()}
    per = []
    for it in items:
        rec = by_id.get(str(it["id"]))
        if not rec:
            per.append(None)
            continue
        per.append(1.0 if _correct(rec["response"]["choices"][0]["message"].get("content") or "") else 0.0)
    vals = [x for x in per if x is not None]
    return (sum(vals) / len(vals) if vals else float("nan")), per


if __name__ == "__main__":
    cfg = {"prompt": {"system": "EM {x}", "system_by_answer_type": {"exactMatch": "EM {x}", "multipleChoice": "MC {y}"}}}
    row = {"id": "q1", "question": "What is 2+2?", "answer": "4", "answer_type": "multipleChoice"}
    assert render(cfg, row)[0]["content"] == "MC {y}" and render(cfg, {**row, "answer_type": "exactMatch"})[0]["content"] == "EM {x}"
    assert parse("Explanation: ...\nExact Answer: 4\nConfidence: 90%", {}) == "4" and parse("nothing", {}) is None
    items = [{"id": "q1", "gold": "4", "messages": render(cfg, row)}]
    resp = {("q1", 0): {"response": {"choices": [{"message": {"content": "Explanation: x\nAnswer: 4\nConfidence: 80%"}}]}}}
    jr = judge_requests(cfg, items, resp)
    assert len(jr) == 1 and jr[0]["body"]["model"] == JUDGE_MODEL and "[correct_answer]: 4" in jr[0]["body"]["messages"][0]["content"]
    good = {("q1", 0): {"response": {"choices": [{"message": {"content": json.dumps({"correct": "yes", "confidence": 80})}}]}}}
    bad = {("q1", 0): {"response": {"choices": [{"message": {"content": "reasoning: no\ncorrect: no"}}]}}}
    assert score_with_judge(cfg, items, resp, good) == (1.0, [1.0]) and score_with_judge(cfg, items, resp, bad) == (0.0, [0.0])
    print("W4410280647 hook self-test ok (data must be provided by a human)")
