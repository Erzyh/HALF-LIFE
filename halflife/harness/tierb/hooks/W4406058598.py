"""W4406058598 (Halu-J, ME-FEVER baseline GPT-4o): render builds the {evidences} slot from the non-empty
golden_evidence / completely_irrelevant_evidence_* / partial_irrelevant_evidence_* / misled_evidence_*
fields of the instance, shuffled with a per-instance seed derived from 20260907 and numbered '1. ...';
parse reads the 'factuality' value (True / False / Neutral) leniently from the dict-style reply. Gold
labels come from the runner (items.label_map 0/1/2 -> True/Neutral/False) and accuracy is the runner's."""
import hashlib
import json
import re

import numpy as np

SEED = 20260907
PREFIXES = ("completely_irrelevant_evidence_", "partial_irrelevant_evidence_", "misled_evidence_")


def evidences_for(row):
    keys = [k for k in row if k == "golden_evidence" or k.startswith(PREFIXES)]
    texts = [str(row[k]).strip() for k in keys if isinstance(row.get(k), str) and str(row[k]).strip()]
    h = int(hashlib.sha256(str(row.get("claim", "")).encode("utf-8")).hexdigest()[:8], 16)
    order = np.random.default_rng(SEED + h).permutation(len(texts))
    return "\n".join(f"{i + 1}. {texts[j]}" for i, j in enumerate(order))


def render(cfg, row):
    tpl = cfg["prompt"]["user_template"]
    content = tpl.replace("{claim}", str(row["claim"])).replace("{evidences}", evidences_for(row))
    msgs = []
    if cfg["prompt"].get("system"):
        msgs.append({"role": "system", "content": cfg["prompt"]["system"]})
    msgs.append({"role": "user", "content": content})
    return msgs


def parse(text, cfg):
    if not text:
        return None
    t = text.strip()
    m = re.search(r"\{.*\}", t, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            v = obj.get("factuality") if isinstance(obj, dict) else None
            if isinstance(v, bool):
                return "True" if v else "False"
            if isinstance(v, str) and v.strip().lower() in ("true", "false", "neutral"):
                return v.strip().capitalize()
        except Exception:
            pass
    m = re.search(r"[\"']?factuality[\"']?\s*:\s*[\"']?\s*(true|false|neutral)\b", t, re.I)
    return m.group(1).capitalize() if m else None


if __name__ == "__main__":
    row = {"claim": "Purple Haze is a Jimi Hendrix song.", "label": "True", "golden_evidence": "G", "completely_irrelevant_evidence_1": "C1",
           "completely_irrelevant_evidence_2": "C2", "partial_irrelevant_evidence_1": "P1", "misled_evidence_1": "M1", "misled_evidence_2": "",
           "explanation_1": "not evidence"}
    ev = evidences_for(row)
    assert ev == evidences_for(row) and sorted(l.split(". ", 1)[1] for l in ev.splitlines()) == ["C1", "C2", "G", "M1", "P1"], ev
    cfg = {"prompt": {"system": None, "user_template": "[claim]: {claim}\n[evidences]:\n{evidences}\nSTART WITH '{'.\n{\n\"reasoning\": ...}"}}
    msg = render(cfg, row)[0]["content"]
    assert "[claim]: Purple Haze" in msg and "1. " in msg and "START WITH '{'" in msg and "{\n\"reasoning\"" in msg, msg
    assert parse('{"reasoning": "x", "factuality": "True"}', {}) == "True"
    assert parse('```json\n{\n"reasoning": "y",\n"factuality": "Neutral"\n}\n```', {}) == "Neutral"
    assert parse("{'reasoning': 'z', 'factuality': 'False'}", {}) == "False"
    assert parse('{"reasoning": "unterminated', {}) is None and parse("", {}) is None
    print("ok\n" + msg)
