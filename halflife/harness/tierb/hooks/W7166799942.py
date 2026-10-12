"""Hook for W7166799942 (CMTD, Table 2 MELD Text-only baseline): one call per dialogue, k labels per reply.

load_items() groups the MELD test CSV by Dialogue_ID (ordered by Utterance_ID) into 280 dialogues rendered
as numbered 'Speaker: utterance' lines; the gold is the list of the k Emotion labels. parse() reads one
label per numbered line (synonyms mapped), falling back to the order of appearance. score() is the
per-utterance accuracy over all 2,610 utterances (weighted F1 printed as the second Table 2 column).
"""
import csv, io, re, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

WID = "W7166799942"
URL = "https://raw.githubusercontent.com/declare-lab/MELD/master/data/MELD/test_sent_emo.csv"
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / WID
LABELS = ["neutral", "joy", "surprise", "anger", "sadness", "disgust", "fear"]
SYN = {"happy": "joy", "happiness": "joy", "joyful": "joy", "sad": "sadness", "angry": "anger", "surprised": "surprise",
       "disgusted": "disgust", "scared": "fear", "afraid": "fear", "fearful": "fear", "frustrated": "anger", "frustration": "anger"}
WORD_RE = re.compile(r"(?<![a-z])(" + "|".join(LABELS + list(SYN)) + r")(?![a-z])")


def _fetch():
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / "test_sent_emo.csv"
    if not p.exists():
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"})
        p.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return p.read_text(encoding="utf-8", errors="replace")


def load_items(cfg):
    rows = list(csv.DictReader(io.StringIO(_fetch())))
    groups = defaultdict(list)
    for r in rows:
        groups[int(r["Dialogue_ID"])].append(r)
    items = []
    for did in sorted(groups):
        utts = sorted(groups[did], key=lambda r: int(r["Utterance_ID"]))
        conv = "\n".join(f"{i + 1}. {u['Speaker']}: {u['Utterance']}" for i, u in enumerate(utts))
        items.append({"id": str(did), "conversation": conv, "gold": [u["Emotion"].strip().lower() for u in utts],
                      "n_utterances": len(utts)})
    return items


def _label_in(segment):
    hits = [SYN.get(w, w) for w in WORD_RE.findall(segment.lower())]
    if not hits:
        return None
    tail = re.split(r"[:\-–→=]", segment)[-1]           # the label usually follows the last separator
    tail_hits = [SYN.get(w, w) for w in WORD_RE.findall(tail.lower())]
    return tail_hits[0] if tail_hits else hits[-1]


def parse(text, cfg):
    if not text:
        return None
    by_index, seq = {}, []
    for line in text.splitlines():
        m = re.match(r"^\W*(\d{1,3})[\.\):\]]", line.strip())
        if m:                                                # numbered line: one label
            lab = _label_in(line.strip()[m.end():])
            if lab is not None:
                seq.append(lab)
                by_index.setdefault(int(m.group(1)), lab)
        else:                                                # free-form line: labels in order of appearance
            seq += [SYN.get(w, w) for w in WORD_RE.findall(line.lower())]
    return {"by_index": by_index, "seq": seq} if (by_index or seq) else None


def _align(pred, n):
    if pred and all(i in pred["by_index"] for i in range(1, n + 1)):
        return [pred["by_index"][i] for i in range(1, n + 1)]
    if pred and len(pred["seq"]) >= n:
        return pred["seq"][:n]
    return (pred["seq"] if pred else []) + [None] * (n - len(pred["seq"] if pred else []))


def score(preds, golds, cfg):
    per, y_true, y_pred = [], [], []
    for p, g in zip(preds, golds):
        for pl, gl in zip(_align(p, len(g)), g):
            per.append(1.0 if pl == gl else 0.0)
            y_true.append(gl); y_pred.append(pl)
    acc = sum(per) / max(1, len(per))
    wf1, n = 0.0, len(y_true)
    for lab in LABELS:
        tp = sum(1 for t, q in zip(y_true, y_pred) if t == lab and q == lab)
        fp = sum(1 for t, q in zip(y_true, y_pred) if t != lab and q == lab)
        fn = sum(1 for t, q in zip(y_true, y_pred) if t == lab and q != lab)
        f1 = 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)
        wf1 += f1 * (tp + fn) / max(1, n)
    print(f"[{WID}] {len(per)} utterances, accuracy {acc:.4f}, weighted F1 {wf1:.4f}, unlabelled {sum(1 for q in y_pred if q is None)}")
    return acc, per


if __name__ == "__main__":
    a = "1. Mark: surprise\n2. Chandler: Neutral\n3. Monica: Joy"
    b = "1. Surprise\n2. Neutral\n3. Happy"
    c = "The emotions are: surprise, neutral, and sadness."
    d = "1. **Surprise** - Mark is puzzled about the numbers.\n2. **Neutral**: plain answer.\n3. Anger: he is frustrated."
    assert _align(parse(a, {}), 3) == ["surprise", "neutral", "joy"]
    assert _align(parse(b, {}), 3) == ["surprise", "neutral", "joy"]
    assert _align(parse(c, {}), 3) == ["surprise", "neutral", "sadness"]
    assert _align(parse(d, {}), 3) == ["surprise", "neutral", "anger"], _align(parse(d, {}), 3)
    v, per = score([parse(a, {}), parse(c, {})], [["surprise", "neutral", "joy"], ["surprise", "joy", "sadness"]], {})
    assert abs(v - 5 / 6) < 1e-9 and len(per) == 6
    print("ok")
