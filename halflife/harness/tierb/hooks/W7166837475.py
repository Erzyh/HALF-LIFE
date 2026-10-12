"""Hook W7166837475 (curated-context political fact-checking, o3-mini zero-shot k = 0, Table A2 macro-F1).

load_items -> reads the paper's '6k' claim sample 2024-10-10_factchecks_cleaned_sampled_0.25_per_year.parquet (written by
              code/data_cleaning/002_subsample_claims.py, read by generate_classification_reports.py for the ~6k results)
              found under external/data/tierb_items/W7166837475/ after extracting it from the Zenodo data.tar.gz
              (10.5281/zenodo.17693220; files served from version record 19709981). Columns used: statement (the claim),
              statement_originator, verdict (gold PolitiFact label), factcheck_analysis_link (unique id). The hook adds
              claim = statement and claim_id = factcheck_analysis_link so the config's field names apply; rows whose
              verdict is not one of the six Truth-Scale labels are dropped.
parse      -> the JSON field 'label' (the paper used a structured output with keys label / justification, a facility the
              runner does not pass to reasoning models); fallback for prose replies: the Truth-Scale label mentioned first
              in the text (longest match wins), then a difflib close match, mirroring the edit-distance repair of malformed
              labels in code/data_cleaning/004_clean_fc_results_pt1.py.
score      -> macro-F1 as generate_performance_results() in generate_classification_reports.py, 'all' variant: unparsable
              (missing) predictions are dropped, NEI predictions stay and count against their gold label, a binary F1 is
              computed per label present in gold or predictions (zero_division = 1) and averaged over the labels except
              'Not enough information'. The released tables (data/cleaned/classification_reports/
              multi_class_{all,attempted}_summary_0.25.parquet) give o3-mini k = 0: all 0.2653 (accuracy 0.318, n 6,137),
              attempted 0.2874 (n 5,313) - so Table A2's 0.27 is the 'all' variant. No per-item list: the runner's
              set-level resample gives the CI.
"""
import difflib
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W7166837475"
FILE = "2024-10-10_factchecks_cleaned_sampled_0.25_per_year.parquet"
LABELS = ["True", "Mostly true", "Half true", "Mostly false", "False", "Pants on fire"]
NEI = "Not enough information"
CANON = {l.lower(): l for l in LABELS + [NEI]}


def load_items(cfg):
    hits = list(DATA.rglob(FILE))
    if not hits:
        raise NeedsHuman(f"extract {FILE} from data.tar.gz into {DATA}")  # noqa: F821 (injected by the runner)
    import pandas as pd
    df = pd.read_parquet(hits[0])
    rows = []
    for r in df.to_dict("records"):
        verdict = CANON.get(str(r.get("verdict") or "").strip().lower())
        if verdict not in LABELS:
            continue
        rows.append({"claim_id": str(r.get("factcheck_analysis_link") or len(rows)), "claim": str(r.get("statement") or ""),
                     "statement_originator": str(r.get("statement_originator") or ""), "verdict": verdict,
                     "factcheck_date": str(r.get("factcheck_date") or "")})
    return rows


def _canon(s):
    s = re.sub(r"\s+", " ", str(s or "")).strip().strip("'\".`").lower().replace("-", " ")
    if s in CANON:
        return CANON[s]
    found = [(m.start(), -len(l), CANON[l]) for l in CANON for m in [re.search(r"(?<!\w)" + re.escape(l) + r"(?!\w)", s)] if m]
    if found:
        return min(found)[2]
    close = difflib.get_close_matches(s, list(CANON), n=1, cutoff=0.6)
    return CANON[close[0]] if close else None


def parse(text, cfg):
    t = (text or "").strip()
    obj = None
    try:
        obj = json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
    if isinstance(obj, dict) and obj.get("label") is not None:
        return _canon(obj["label"])
    m = re.search(r"(?i)label\W{0,5}([A-Za-z ]{4,25})", t)          # 'Label: Mostly false' style prose
    lab = _canon(m.group(1)) if m else None
    return lab if lab else _canon(t)


def _binary_f1(y_true, y_pred, label, zero_division=1.0):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
    prec = tp / (tp + fp) if tp + fp else zero_division
    rec = tp / (tp + fn) if tp + fn else zero_division
    return 0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec)


def score(preds, golds, cfg):
    pairs = [(g, p) for p, g in zip(preds, golds) if p is not None]       # 'all' variant: NEI predictions stay as errors
    if not pairs:
        return 0.0, None
    y_true, y_pred = [g for g, _ in pairs], [p for _, p in pairs]
    labels = sorted(set(y_true) | set(y_pred))
    f1s = [_binary_f1(y_true, y_pred, l) for l in labels if l.lower() != NEI.lower()]
    return (sum(f1s) / len(f1s) if f1s else 0.0), None


if __name__ == "__main__":
    assert parse('{"label": "Mostly false", "justification": "..."}', {}) == "Mostly false"
    assert parse('```json\n{"label": "pants on fire"}\n```', {}) == "Pants on fire"
    assert parse("Label: Half true\nJustification: the figure is right but ...", {}) == "Half true"
    assert parse("This claim is Mostly True; note that it is not entirely False.", {}) == "Mostly true"
    assert parse("Not enough information to judge.", {}) == NEI
    assert parse("no idea", {}) is None
    v, _ = score(["True", "False", NEI, None, "Half true"], ["True", "True", "False", "False", "Half true"], {})
    # kept rows (None dropped): (True,True) (True,False) (False,NEI) (Half true,Half true); labels False, Half true, NEI, True
    # F1 True = 2*1*0.5/1.5 = 0.6667; F1 False: tp0 fp1 fn1 -> 0; F1 Half true = 1; NEI excluded from the mean
    assert abs(v - (2 / 3 + 0 + 1) / 3) < 1e-9, v
    v2, _ = score([NEI, "True"], ["True", "True"], {})          # 'all' keeps the NEI row: F1 True = 2/3 (attempted would give 1)
    assert abs(v2 - 2 / 3) < 1e-9, v2
    print("W7166837475 hook self-test ok")
