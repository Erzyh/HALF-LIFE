"""Hook for W4411080278 (GPT-4o emergency diagnoses, temperature 0.0, with physical exam).

load_items: the four Table 1 vignettes held in the config's items.inline, each replicated 250 times
            (id = <case>_<iteration>, gold = case key) = the paper's 1,000 outputs per condition.
render:     runner default (Supplement 1 template with the five case fields).
parse:      the leading diagnosis = the diagnosis named in the first listed item of the reply (numbered /
            bulleted / 'Leading diagnosis:' line). Only the diagnosis proper is kept: a leading bold segment
            ('**Hypothyroidism**: explanation ...') or the text before the first ': '. The paper's keyword
            search runs over the listed diagnosis, not over an appended explanation (a whole-line search
            would credit 'Hypothyroidism: ... potentially myxedema coma' for 'myxedema').
            [triage 2026-09-09: whole-line search replaced by the diagnosis-name rule; 50.1% -> 25.0%]
score:      keyword search (case-insensitive) of the leading diagnosis: myxedema | cholangitis |
            'carbon monoxide' or whole-word 'co' | cryptococcal meningitis / meningoencephalitis / encephalitis.
"""
import re

KEYWORDS = {
    "myxedema_coma": [r"myxedema"],
    "ascending_cholangitis": [r"cholangitis"],
    "carbon_monoxide_poisoning": [r"carbon monoxide", r"(?<![a-z])co(?![a-z])"],
    "cryptococcal_meningitis": [r"cryptococcal meningitis", r"cryptococcal meningoencephalitis", r"cryptococcal encephalitis"],
}
ITERATIONS = 250


def load_items(cfg):
    rows = []
    for case in cfg["items"]["inline"]:
        for k in range(ITERATIONS):
            r = dict(case)
            r["id"] = f"{case['case']}_{k + 1:03d}"
            r["gold"] = case["case"]
            rows.append(r)
    return rows


_MARK = re.compile(r"^\s*(?:(?:\d+|[a-c])[\.\):]\s*|[-*•]\s+)")
_LEAD = re.compile(r"(?i)^\s*\**\s*(?:leading|primary|most likely)\s+(?:differential\s+)?diagnosis\s*\**\s*[:\-]\s*")


def _name(l):
    """The diagnosis proper: a leading bold segment, else the text before the first ': ' (explanation separator).
    Dashes and parentheses are kept as part of the named diagnosis."""
    m = re.match(r"\s*\*\*(.+?)\*\*", l)
    core = m.group(1) if m else re.split(r":\s", l, maxsplit=1)[0]
    return core.strip(" *_\"'.").lower()


def parse(text, cfg):
    if not text:
        return None
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return None
    for l in lines:                                    # first list item or explicit leading-diagnosis line
        if _MARK.match(l) or _LEAD.match(l):
            l = _LEAD.sub("", _MARK.sub("", l))
            l = re.sub(r"(?i)^\**\s*(?:leading|primary)\s+diagnosis\s*\**\s*[:\-]\s*", "", l)
            return _name(l)
    return _name(lines[0])


def score(preds, golds, cfg):
    per = []
    for p, g in zip(preds, golds):
        pats = KEYWORDS[str(g)]
        per.append(1.0 if p and any(re.search(pat, p) for pat in pats) else 0.0)
    return (sum(per) / len(per) if per else float("nan")), per


if __name__ == "__main__":
    t1 = "1. Myxedema coma\n2. Sepsis\n3. Hypothermia"
    t2 = "**Leading Diagnosis:** Ascending cholangitis\n**Differential Diagnoses:**\n1. Urinary tract infection\n2. Pneumonia"
    t3 = "- CO poisoning\n- Viral syndrome\n- Migraine"
    t4 = "Cryptococcal meningitis, bacterial meningitis, viral meningitis"
    t5 = "1. Cocaine intoxication\n2. Carbon monoxide poisoning\n3. Tension headache"
    t6 = "1. **Hypothyroidism**: The patient's bradycardia ... are consistent with severe hypothyroidism, potentially myxedema coma.\n\n2. **Sepsis**: ..."
    t7 = "### Differential Diagnoses\n1. **Carbon Monoxide Poisoning**\n2. **Migraine**"
    t8 = "1. Hypothyroidism (myxedema coma)\n2. Sepsis"
    ps = [parse(t, {}) for t in (t1, t2, t3, t4, t5, t6, t7, t8)]
    print(ps)
    assert ps[5] == "hypothyroidism" and ps[6] == "carbon monoxide poisoning" and ps[7] == "hypothyroidism (myxedema coma)"
    v, per = score(ps, ["myxedema_coma", "ascending_cholangitis", "carbon_monoxide_poisoning", "cryptococcal_meningitis",
                        "carbon_monoxide_poisoning", "myxedema_coma", "carbon_monoxide_poisoning", "myxedema_coma"], {})
    print(v, per)
    assert per == [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0]
    print("W4411080278 hook self-test ok")
