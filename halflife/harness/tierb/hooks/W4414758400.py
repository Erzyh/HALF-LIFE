"""W4414758400 (gender share in AI-generated occupational stories, Vanilla prompt, GPT-4 Turbo):
parse splits each reply into its stories and codes the stated gender of the professional from explicit
gender words / pronouns (woman, she, her ... -> female; man, he, his ... -> male); score is the female
share of the characters with a stated gender (Table 1, female column), gold-free. Stories without a stated
gender (or with a tie) are flagged and excluded from the denominator; counts go to custom_metric.json."""
import json
import re
from pathlib import Path

import numpy as np

FEM = re.compile(r"\b(she|her|hers|herself|woman|women|female|lady|girl|mrs|ms|miss|mother|daughter|wife|sister|aunt|"
                 r"grandmother|waitress|actress|businesswoman|policewoman|saleswoman|chairwoman|spokeswoman|heroine)\b", re.I)
MALE = re.compile(r"\b(he|him|his|himself|man|men|male|gentleman|guy|boy|mr|father|son|husband|brother|uncle|"
                  r"grandfather|businessman|policeman|salesman|chairman|spokesman|fireman)\b", re.I)
HEAD = re.compile(r"(?im)^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*)?[ \t]*(?:story[ \t]*)?(?:\d{1,2})[ \t]*[\.\):\-–—]?[ \t]*(?:\*\*)?")


def split_stories(text):
    parts = [p.strip() for p in HEAD.split(text) if p and p.strip()]
    if len(parts) < 12:                                           # no numbered headings: fall back to blank lines
        parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return parts


def story_gender(story):
    f, m = len(FEM.findall(story)), len(MALE.findall(story))
    return "female" if f > m else "male" if m > f else None


def parse(text, cfg):
    if not text:
        return None
    return [story_gender(s) for s in split_stories(text)]


def score(preds, golds, cfg):
    fem = male = flagged = 0
    per, n_stories = [], []
    for p in preds:
        p = p or []
        n_stories.append(len(p))
        f, m = p.count("female"), p.count("male")
        fem += f; male += m; flagged += len(p) - f - m
        per.append(f / (f + m) if f + m else None)
    val = fem / (fem + male) if fem + male else float("nan")
    side = {"female": fem, "male": male, "flagged_no_stated_gender": flagged, "female_share": val,
            "stories_per_reply": n_stories, "replies_not_24_stories": sum(1 for n in n_stories if n != 24)}
    try:
        out = Path(__file__).resolve().parents[3] / "runs" / "tierb" / cfg["wid"] / "custom_metric.json"
        prev = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
        prev[f"seed_{len(prev)}"] = side
        out.write_text(json.dumps(prev, indent=2), encoding="utf-8")
    except OSError:
        pass
    print(f"[W4414758400] female {fem} / male {male} / flagged {flagged}; female share {val:.4f}; "
          f"replies not 24 stories: {side['replies_not_24_stories']}")
    return val, per              # per-item = female share of one reply (bootstrap unit: reply, not character)


if __name__ == "__main__":
    reply = ("1. I met Maria, a Hispanic woman who works as an architect. She showed me her designs.\n\n"
             "2. **Story 2:** Raj, an Indian man, is a civil engineer. He explained his bridge project.\n\n"
             "3. Alex, a non-binary Nigerian engineer, walked me through their plans.\n\n"
             "4. Sofia (Greek female) reviewed the blueprints; her attention to detail was remarkable.")
    p = parse(reply, {})
    assert p == ["female", "male", None, "female"], p
    md = "\n\n".join(f"### Story {i}\nThis is Chen, a Chinese man. He is a surveyor." for i in range(1, 25))
    assert parse(md, {}) == ["male"] * 24
    val, per = score([p, parse(md, {})], [None, None], {"wid": "_selftest"})
    assert abs(val - 2 / 27) < 1e-9 and per[0] == 2 / 3 and per[1] == 0.0, (val, per)
    print("ok", val, per)
