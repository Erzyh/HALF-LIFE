"""Hook W4415270561 (Diff-XYZ, Apply task, GPT 4.1 nano w/o format, Table 1 EM 0.38).

parse -> the reply is requested as ```lang ... ``` (Appendix A.2, Figure 3). Take the content of the LAST
         fenced block (models sometimes narrate first); when no fence is present, take the whole reply, so a
         bare-code answer is still scored rather than counted as unparsed.
score -> Stripped Exact Match of Sec. 3.1: drop every line that consists only of whitespace from BOTH the
         prediction and the reference new code, then require the remainders to be identical. The runner's own
         exact_match normalises with norm() (lower-case, whitespace collapsed), which would credit answers that
         differ in case or indentation, so the metric is computed here instead.
No load_items / render: items.hf + the config's placeholders are runner facilities.
"""
import re

FENCE = re.compile(r"```[ \t]*[\w+#.-]*[ \t]*\r?\n(.*?)```", re.S)


def _strip_blank_lines(text):
    """Sec. 3.1 'we remove all the lines that contain only whitespace characters'."""
    return "\n".join(l for l in str(text).replace("\r\n", "\n").split("\n") if l.strip())


def parse(text, cfg=None):
    if text is None:
        return None
    blocks = FENCE.findall(text)
    if blocks:
        return blocks[-1]
    # unterminated fence: keep everything after the opening marker
    m = re.search(r"```[ \t]*[\w+#.-]*[ \t]*\r?\n(.*)", text, re.S)
    if m:
        return m.group(1)
    return text


def score(preds, golds, cfg=None):
    per = [1.0 if p is not None and _strip_blank_lines(p) == _strip_blank_lines(g) else 0.0
           for p, g in zip(preds, golds)]
    return (sum(per) / len(per) if per else 0.0), per


if __name__ == "__main__":
    gold = "def f():\n\n    return 1\n"
    cases = [
        ("```python\ndef f():\n    return 1\n```", 1.0),                      # fenced, blank line dropped
        ("Here you go:\n```py\nwrong()\n```\n```python\ndef f():\n    return 1\n```", 1.0),  # last fence wins
        ("def f():\n    return 1", 1.0),                                      # no fence at all
        ("```python\nDEF F():\n    RETURN 1\n```", 0.0),                      # case must match (runner norm would pass)
        ("```python\ndef f():\n        return 1\n```", 0.0),                  # indentation must match
        ("```python\ndef f():\n    return 1\n", 1.0),                         # unterminated fence
    ]
    per_all = []
    for text, want in cases:
        v, per = score([parse(text)], [gold])
        per_all.append((v, want))
        assert v == want, (text, v, want)
    v, per = score([parse(t) for t, _ in cases], [gold] * len(cases))
    print("ok:", per, "mean", round(v, 4), "| parse(None) ->", parse(None))
