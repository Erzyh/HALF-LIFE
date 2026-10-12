"""Hook W4404314294 (DisasterQA, gpt-4-turbo, No Prompting, Table II 1st Index).

render -> the paper's prompt: question, the 'Answer Choices' cell verbatim (a field name with a space, which the
          placeholder grammar rejects) and the closing phrase with its literal '{letter}'.
parse  -> the paper's Section IV rule: the first letter A-F after one of the listed phrases; None = unanswered.
score  -> accuracy with unanswered questions removed from the denominator (Section IV); gold letters compared
          case-insensitively (the CSV mixes a-d and A-D).
"""
import re

PAT = re.compile(r"(?i)(?:answer(?: choice)?(?: here)? is|choices provided is|options provided is|from the list is|"
                 r"choices is|one out is):?\s*\**\s*\(?([A-Fa-f])\b")


def render(cfg, row):
    p = cfg["prompt"]
    msg = p["user_template"].replace("{question}", str(row["Question"])).replace("{answer_choices}", str(row["Answer Choices"]))
    msgs = [{"role": "system", "content": p["system"]}] if p.get("system") else []
    msgs.append({"role": "user", "content": msg})
    return msgs


def parse(text, cfg):
    m = PAT.search(text or "")
    return m.group(1).upper() if m else None


def score(preds, golds, cfg):
    per = [None if p is None else (1.0 if p == str(g).strip().upper() else 0.0) for p, g in zip(preds, golds)]
    answered = [x for x in per if x is not None]
    return (sum(answered) / len(answered) if answered else float("nan")), per


if __name__ == "__main__":
    tests = [("Shelters are ... The answer is C.", "C"), ("The answer choice here is: b", "B"),
             ("Therefore, the correct answer is: c.", "C"), ("The answer is: **D**", "D"),
             ("The best one out is A", "A"), ("The answer is Chicago", None), ("I cannot say.", None)]
    for reply, want in tests:
        assert parse(reply, {}) == want, (reply, parse(reply, {}), want)
    v, per = score(["C", None, "A"], ["c", "b", "b"], {})
    assert v == 0.5 and per == [1.0, None, 0.0]
    cfg = {"prompt": {"system": None, "user_template": "{question}\n{answer_choices}\nEnd with 'The answer is {letter}'."}}
    msgs = render(cfg, {"Question": "Q?", "Answer Choices": "a. x\nb. y"})
    assert msgs == [{"role": "user", "content": "Q?\na. x\nb. y\nEnd with 'The answer is {letter}'."}]
    print("W4404314294 hook self-test ok")
