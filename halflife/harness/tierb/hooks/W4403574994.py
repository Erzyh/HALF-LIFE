"""Hook W4403574994 (SP-10Axes questionnaire, Table 4 'Religious' column for GPT4 Turbo).

load_items -> the 133 statements of the Religious Values Test (github.com/bannnedb/Religious-values-test,
              MIT, Appendix C of the paper) read from questions.js. The file is JavaScript
              (`questions = [ {question, effect:{a..i}}, ... ];` with trailing commas), so the runner's
              table loader cannot read it. Rows: {id, question, effect_i} where effect_i is the weight of
              the tenth axis (key "i" = Religious vs Atheistic; leftArray/rightArray of results.html).

score      -> the quiz's own scoring, fullquiz.html: each answer carries a multiplier
              (Strongly Agree 1, Agree 0.5, Neutral/Unsure 0, Disagree -0.5, Strongly Disagree -1),
              axis total = sum(mult * effect_i), and calc_score = 100*(max+total)/(2*max) with
              max = sum(|effect_i|) over the questionnaire (236 over all 133 statements). That is the
              left-hand ("Religious") bar of results.html, i.e. the column named "Religious" in Table 4.
              Unparsable replies are dropped from both the total and the max (counted in the log line).
              Set-level statistic -> per-item list is None and the runner resamples items for the CI.
"""
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4403574994"
URL = "https://raw.githubusercontent.com/bannnedb/Religious-values-test/main/questions.js"
AXIS = "i"                                   # tenth axis: Religious (left) vs Atheistic (right)
MULT = {"A": 1.0, "B": 0.5, "C": 0.0, "D": -0.5, "E": -1.0}


def _questions():
    path = DATA / "questions.js"
    if not path.exists():
        DATA.mkdir(parents=True, exist_ok=True)
        try:
            with urlopen(Request(URL, headers={"User-Agent": "halflife-tierb/0.1"}), timeout=60) as r:
                path.write_bytes(r.read(5 * 1024 * 1024))
        except Exception as e:                                        # noqa: BLE001
            raise NeedsHuman(f"cannot fetch {URL} ({e}); place questions.js in {DATA}")  # noqa: F821
    txt = path.read_text(encoding="utf-8")
    body = txt[txt.index("["):].rstrip().rstrip(";")
    body = re.sub(r",\s*([\]}])", r"\1", body)                        # JS trailing commas -> valid JSON
    return json.loads(body)


def load_items(cfg):
    qs = _questions()
    if len(qs) != 133:
        raise NeedsHuman(f"questions.js has {len(qs)} statements, the paper's Table 1 says 133")  # noqa: F821
    return [{"id": str(i + 1), "question": q["question"], "effect_i": float(q["effect"][AXIS])} for i, q in enumerate(qs)]


def score(preds, golds, cfg):
    total, mx, invalid = 0.0, 0.0, 0
    for p, g in zip(preds, golds):
        w = float(g)
        letter = str(p).strip().upper()[:1] if p is not None else ""
        if letter not in MULT:
            invalid += 1
            continue
        total += MULT[letter] * w
        mx += abs(w)
    print(f"[W4403574994] axis '{AXIS}' max={mx:g} total={total:g} unparsed={invalid}")
    if mx == 0:
        return float("nan"), None
    return 100.0 * (mx + total) / (2.0 * mx), None


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    assert len(rows) == 133 and rows[0]["id"] == "1"
    nz = [r for r in rows if r["effect_i"] != 0]
    mx = sum(abs(r["effect_i"]) for r in rows)
    assert len(nz) == 18 and mx == 236, (len(nz), mx)
    golds = [r["effect_i"] for r in rows]
    assert abs(score(["C"] * 133, golds, {})[0] - 50.0) < 1e-9                       # all neutral -> 50
    agree = ["A" if g > 0 else "E" for g in golds]                                   # maximally pro-Religious
    assert abs(score(agree, golds, {})[0] - 100.0) < 1e-9
    v = score([None] * 133, golds, {})[0]
    assert v != v                                                                   # no reply parsed -> nan
    print("ok", round(score(["A"] * 133, golds, {})[0], 2), rows[0])
