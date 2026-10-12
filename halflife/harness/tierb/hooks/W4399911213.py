"""Hook W4399911213 (WikiContradict judge meta-evaluation, gpt-4-turbo, Table 3 Acc).

load_items -> flattens the adjudication JSON (a dict keyed by the judged model whose values are lists of 48
              records): the key is stored as 'modelName' and 'uid' = '<model>:<question_ID>' is a unique id.
parse      -> the judge's 3-way label, in this order:
              1. the LAST 'evaluation: <label>' line (the Appendix C format);
              2. else the LAST verdict sentence 'the response|it is|remains [considered] <label>' (the archived
                 gpt-4-turbo replies end the comment with 'Thus, the response is partially correct.' and omit the
                 'evaluation:' line in 341 of 720 cases);
              3. else the last standalone label that is not the phrase 'correct answer(s) / answer list / response'.
              The paper's own spellings 'partically / particially correct' map to 'partially correct'.
              [triage 2026-09-09: the earlier fallback took the last label anywhere, which in a comment such as
              '... is partially correct as it only matches one of the correct answers' returned 'correct'
              (72 of 720 replies); 76.7% -> 81.1%, see result_before_triage.json]
score      -> runner accuracy (case-insensitive) against the human label.
"""
import json, re, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
LAB = r"(partially correct|partically correct|particially correct|incorrect|correct)"
_EVAL = re.compile(r"(?i)evaluation\s*:\s*\**\s*" + LAB)
_VERDICT = re.compile(r"(?i)(?:response|evaluation|answer|it)\s+(?:is|remains|would be|should be|can be|could be)\s+"
                      r"(?:therefore\s+|thus\s+|only\s+|also\s+|still\s+)?"
                      r"(?:considered\s+|deemed\s+|classified as\s+|evaluated as\s+|rated as\s+|marked as\s+|judged\s+)?"
                      r"(?:as\s+)?\**" + LAB + r"(?![a-z])")
_ANY = re.compile(r"(?i)(?<![a-z])" + LAB + r"(?![a-z])(?!\s+(?:answers?|answer list|responses?))")


def load_items(cfg):
    url = cfg["items"]["file_url"]
    obj = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read().decode("utf-8"))
    rows = []
    for model, recs in obj.items():
        for r in recs:
            r = dict(r)
            r["modelName"] = model
            r["uid"] = f"{model}:{r.get('question_ID')}"
            rows.append(r)
    return rows


def parse(text, cfg):
    t = text or ""
    hits = _EVAL.findall(t) or _VERDICT.findall(t) or _ANY.findall(t)
    if not hits:
        return None
    lab = hits[-1].lower()
    return "partially correct" if lab.startswith("parti") else lab


if __name__ == "__main__":
    tests = [("comment: only one answer.\n evaluation: partically correct", "partially correct"),
             ("evaluation: incorrect", "incorrect"), ("evaluation: correct\n... evaluation: incorrect", "incorrect"),
             ("The response is correct.", "correct"), ("evaluation: **Correct**", "correct"),
             ("comment: the answer is wrong.\nevaluation: Incorrect.", "incorrect"), ("", None),
             ("Therefore, the response is partially correct as it only matches with one of the correct answers.", "partially correct"),
             ('The response is incorrect because it only provides one answer ("No") and does not acknowledge the correct answers.', "incorrect"),
             ("The primary answer matches one of the correct answers. Thus, the response is partially correct.", "partially correct"),
             ("Therefore, the evaluation remains partially correct.", "partially correct"),
             ("It matches one of the correct answers in the correct answer list.", None),
             ("incorrect", "incorrect")]
    for reply, want in tests:
        assert parse(reply, {}) == want, (reply, parse(reply, {}), want)
    print("W4399911213 hook self-test ok")
