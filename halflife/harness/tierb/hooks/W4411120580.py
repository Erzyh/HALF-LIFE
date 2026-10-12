"""W4411120580 (QSpell 250K, Table 3 row 'Prompt GPT4', QSpell 250K F1).

load_items -> the released test file corrector_datasets/qspell_250k_test.txt of github.com/dz1109/CQSpell
              (tab-separated 'query<TAB>corrected query', no header, so the runner's table loader cannot
              read it). gold packs both fields as "query\\tcorrection" because the score needs the source
              query to tell a correction apart from a false alarm.
parse      -> the reply is the corrected query: first non-empty line, quotes and an echoed
              'The output query is:' prefix removed.
score      -> the repository's own eval_corrector.py, transcribed: predictions and gold corrections are
              converted full-width -> half-width (strB2Q, the source query is left as it is, as in the
              original script), then
                 TP: query != gold and pred == gold      FN: query != gold and pred != gold
                 FP: query == gold and pred != gold      TN: query == gold and pred == gold
                 precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2PR/(P+R).
              Checked against the repository's own GPT-4 output file qspell_250k_gpt4.txt: this code gives
              P 0.7556 R 0.3181 F1 0.4477 on it, next to Table 3's P 0.7409 R 0.3146 F1 0.4416, which the
              paper reports as the average of five runs.
Set-level statistic -> per-item list is None and the runner resamples items for the CI.
"""
import re
from pathlib import Path
from urllib.request import Request, urlopen

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4411120580"
TEST = DATA / "qspell_250k_test.txt"
PREFIX = re.compile(r"^\s*(?:###\s*)?(?:out\s*query|output\s*query|the\s*output\s*query(?:\s*is)?)\s*[:：]\s*", re.I)


def strB2Q(s):
    """Full-width -> half-width, exactly as eval_corrector.py does (the function's name is the authors')."""
    out = []
    for ch in s:
        code = ord(ch)
        if code == 0x3000:
            code = 0x0020
        elif 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        out.append(chr(code))
    return "".join(out)


def load_items(cfg):
    if not TEST.exists():
        DATA.mkdir(parents=True, exist_ok=True)
        with urlopen(Request(cfg["items"]["file_url"], headers={"User-Agent": "halflife-tierb/0.1"}), timeout=300) as r:
            TEST.write_bytes(r.read(50 * 1024 * 1024))
    rows = []
    for i, line in enumerate(TEST.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2:
            raise NeedsHuman(f"line {i} of {TEST.name} has no tab: {line[:60]!r}")  # noqa: F821
        rows.append({"id": str(i), "query": parts[0], "target": parts[1], "gold": parts[0] + "\t" + parts[1]})
    return rows


def parse(text, cfg):
    if not text:
        return None
    line = next((l for l in text.strip().splitlines() if l.strip()), "")
    line = PREFIX.sub("", line.strip()).strip()
    return line.strip("\"'“”‘’ ") or None


def score(preds, golds, cfg):
    tp = fp = fn = tn = 0
    unparsed = 0
    for p, g in zip(preds, golds):
        src, tgt = str(g).split("\t", 1)
        tgt = strB2Q(tgt)
        if p is None:
            unparsed += 1
            pred = ""                                   # no reply: counts as an unchanged / wrong output
        else:
            pred = strB2Q(str(p))
        if src == tgt:
            tn += 1 if pred == tgt else 0
            fp += 0 if pred == tgt else 1
        else:
            tp += 1 if pred == tgt else 0
            fn += 0 if pred == tgt else 1
    n = tp + fp + fn + tn
    pr = tp / (tp + fp) if tp > 0 else 0.0
    rc = tp / (tp + fn) if tp > 0 else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    print(f"[W4411120580] n={n} acc={(tp + tn) / max(1, n):.4f} precision={pr:.4f} recall={rc:.4f} f1={f1:.4f} unparsed={unparsed}")
    return float(f1), None


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    assert strB2Q("ａＢ　") == "aB "
    assert parse("The output query is: name音标怎么写", {}) == "name音标怎么写"
    assert parse(' "赛音hitting" ', {}) == "赛音hitting"
    assert parse("", {}) is None
    golds = ["a\ta", "b\tB", "c\tc", "d\tD"]
    preds = ["a", "B", "x", "d"]                        # TN, TP, FP, FN
    v, per = score(preds, golds, {})
    assert per is None and abs(v - 2 * 0.5 * 0.5 / 1.0) < 1e-9, v
    if TEST.exists():                                   # replay of the repository's own GPT-4 outputs
        rows = load_items({"items": {"file_url": ""}})
        pred_file = DATA / "qspell_250k_gpt4.txt"
        if pred_file.exists():
            preds = [l.rstrip("\n").split("\t")[1] for l in pred_file.read_text(encoding="utf-8").splitlines() if l.strip()]
            v, _ = score(preds, [r["gold"] for r in rows][:len(preds)], {})
            print(f"repository GPT-4 file: f1={v:.4f} (Table 3: 0.4416, average of five runs)")
            assert 0.43 < v < 0.46
    print("ok")
