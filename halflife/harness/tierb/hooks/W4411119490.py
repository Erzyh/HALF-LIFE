"""Hook W4411119490 (MMLU-Redux error detection, gpt-4-turbo zero-shot, Table 3 F1).

render -> the Appendix G task text followed by the code release's verbaliser block (QUESTION_VERBALISER in
          src/taxonomy/data_utils.py): choices as 'A. ...' lines and Ground Truth Answer = '<letter>. <text>'
          selected by the integer 'answer' index.
parse  -> 'not ok' if the reply contains 'not ok', else 'ok' if it contains a standalone 'ok', else None.
score  -> F1 of the positive class 'not ok' (any error_type other than ok; Sec. 4: 'not ok' is the positive
          class); unparsable replies are scored as 'ok' (config output.postprocess). No per-item list.
"""
import json, re


def _choices(v):
    if isinstance(v, str):
        try:
            return [str(c) for c in json.loads(v)]
        except Exception:
            return [c.strip(" '\"") for c in re.split(r"'\s+'|\n", v.strip("[]")) if c.strip()]
    return [str(c) for c in list(v)]


def render(cfg, row):
    choices = _choices(row["choices"])
    ans = int(row["answer"])
    verbalised = "\n".join(f"{chr(65 + i)}. {c}" for i, c in enumerate(choices))
    gt = f"{chr(65 + ans)}. {choices[ans]}"
    msg = (cfg["prompt"]["user_template"].replace("{question}", str(row["question"]))
           .replace("{choices}", verbalised).replace("{answer}", gt))
    return [{"role": "user", "content": msg}]


def parse(text, cfg):
    low = (text or "").lower()
    if re.search(r"not\s+ok", low):
        return "not ok"
    if re.search(r"(?<![a-z])ok(?![a-z])", low):
        return "ok"
    return None


def score(preds, golds, cfg):
    tp = fp = fn = 0
    for p, g in zip(preds, golds):
        p = p or "ok"
        g = "ok" if str(g).strip().lower() == "ok" else "not ok"
        if p == "not ok" and g == "not ok":
            tp += 1
        elif p == "not ok":
            fp += 1
        elif g == "not ok":
            fn += 1
    return 2 * tp / max(1, 2 * tp + fp + fn), None


if __name__ == "__main__":
    tests = [("not ok", "not ok"), ("'ok'", "ok"), ("The question is Not OK.", "not ok"), ("OK", "ok"),
             ("I think it is fine.", None), ("okay", None)]
    for reply, want in tests:
        assert parse(reply, {}) == want, (reply, parse(reply, {}), want)
    v, _ = score(["not ok", "ok", None, "not ok"], ["wrong_groundtruth", "ok", "not ok", "ok"], {})
    assert abs(v - 2 * 1 / (2 * 1 + 1 + 1)) < 1e-12, v
    cfg = {"prompt": {"user_template": "Question: {question}\nChoices:\n{choices}\nGround Truth Answer: {answer}\nYour Response: "}}
    msg = render(cfg, {"question": "1+1?", "choices": ["1", "2", "3", "4"], "answer": 1})[0]["content"]
    assert msg == "Question: 1+1?\nChoices:\nA. 1\nB. 2\nC. 3\nD. 4\nGround Truth Answer: B. 2\nYour Response: ", msg
    print("W4411119490 hook self-test ok")
