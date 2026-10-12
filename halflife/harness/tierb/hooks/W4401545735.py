"""Hook W4401545735 (FPB, naive BloombergGPT prompt, gpt-4o-2024-05-13, Table 4 'GPT-4' FPB Acc.).

parse -> the FIRST occurrence in the reply of negative | neutral | positive (config output.postprocess:
         'lowercase, first occurrence'). The runner's generic 'label from set' parser returns the first label in
         list order among those present, so 'Neutral. ... does not convey any positive or negative sentiment'
         came back as 'negative' (21 of 6,792 replies; triage 2026-09-09). Items, prompt and metric: runner.
"""
import re

_RE = re.compile(r"(?<![a-z])(negative|neutral|positive)(?![a-z])")


def parse(text, cfg):
    if not text:
        return None
    m = _RE.search(text.lower())
    return m.group(1) if m else None


if __name__ == "__main__":
    tests = [("Neutral. The statement does not convey any positive or negative sentiment.", "neutral"),
             ("Positive.", "positive"), ("The sentiment is negative.", "negative"),
             ('The sentiment of the statement "The project is expected', None)]
    for t, want in tests:
        assert parse(t, {}) == want, (t, parse(t, {}))
    print("W4401545735 hook self-test ok")
