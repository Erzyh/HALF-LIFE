"""Hook for W4403443823 (Science is Exploration, Table 1 row 4-turbo, TroFi metaphorical precision 74.80).

load_items() reads the TroFi Example Base (Birke & Sarkar 2006, SFU page) and keeps the sentences tagged
by humans (N = nonliteral, L = literal; U = labelled only by the clustering system, dropped): 3,737
sentences for 50 target verbs (the paper counts 3,736). The tokenised WSJ text is kept, with the trailing
'./.' marker removed and -LRB-/-RRB-/``/'' restored to ( ) ". The gold carries the label, the target lemma
and its surface form in the sentence. parse() reads the '- word: YES|NO' lines. score() takes the line of
the target form (a phrase containing it counts, Sec. 4); a missing label is treated as the incorrect label
(Sec. 4). YES = metaphorical; the metric is precision on the metaphorical class (recall and the literal
precision/recall are printed).
"""
import re, urllib.request
from pathlib import Path

WID = "W4403443823"
URL = "https://www.cs.sfu.ca/~anoop/students/jbirke/TroFiExampleBase.txt"
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / WID
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
IRREGULAR = {"drink": ["drank", "drunk"], "eat": ["ate", "eaten"], "fly": ["flew", "flown", "flies"], "ride": ["rode", "ridden"],
             "sleep": ["slept"], "strike": ["struck", "stricken"], "stick": ["stuck"], "lend": ["lent"], "die": ["dying"],
             "lie": ["lay", "lain"], "grasp": ["grasp"], "run": ["ran"]}


def _clean(s):
    s = re.sub(r"\s*\./\.\s*$", ".", s.strip())
    return s.replace("-LRB-", "(").replace("-RRB-", ")").replace("``", '"').replace("''", '"')


def _norm(w):
    return re.sub(r"[^a-z\-']", "", w.lower())


def _surface(lemma, sentence):
    stem = lemma[:-1] if lemma.endswith("e") else lemma
    forms = set(IRREGULAR.get(lemma, []))
    for tok in sentence.split():
        for part in _norm(tok).split("-"):
            if part == lemma or part in forms or (part.startswith(stem) and len(part) <= len(lemma) + 3):
                return _norm(tok)
    return lemma


def load_items(cfg):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / "TroFiExampleBase.txt"
    if not p.exists():
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=120).read())
    rows, lemma = [], None
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\*\*\*([a-z]+)\*\*\*\s*$", line)
        if m:
            lemma = m.group(1)
            continue
        parts = line.split("\t")
        if lemma and len(parts) >= 3 and parts[1].strip() in ("N", "L"):
            sent = _clean(parts[2])
            rows.append({"id": f"{lemma}:{parts[0].strip()}", "sentence": sent, "target": lemma,
                         "gold": {"label": "nonliteral" if parts[1].strip() == "N" else "literal", "target": lemma,
                                  "form": _surface(lemma, sent)}})
    return rows


def parse(text, cfg):
    if text is None:
        return None
    out = []
    for line in text.splitlines():
        m = re.match(r"^\s*[-•*]?\s*\**\s*[\"“”']?(.+?)[\"“”']?\s*\**\s*:\s*\**\s*(YES|NO)\b", line.strip(), re.I)
        if m:
            out.append((m.group(1).strip(), m.group(2).upper()))
    return out


def _label_for(pred, gold):
    form, stem = gold["form"], (gold["target"][:-1] if gold["target"].endswith("e") else gold["target"])
    words = [([_norm(x) for x in w.split()], lab) for w, lab in (pred or [])]
    for toks, lab in words:
        if len(toks) == 1 and toks[0] == form:
            return lab
    for toks, lab in words:
        if form in toks or any(form in t.split("-") for t in toks):
            return lab
    for toks, lab in words:
        if any(t.startswith(stem) and len(t) <= len(gold["target"]) + 3 for t in toks):
            return lab
    return None


def score(preds, golds, cfg):
    tp = fp = fn = tn = missing = 0
    for p, g in zip(preds, golds):
        lab = _label_for(p, g)
        if lab is None:                                   # "we act as if the incorrect label was given"
            missing += 1
            lab = "NO" if g["label"] == "nonliteral" else "YES"
        meta, pred_meta = g["label"] == "nonliteral", lab == "YES"
        tp += meta and pred_meta; fp += (not meta) and pred_meta; fn += meta and not pred_meta; tn += (not meta) and not pred_meta
    prec = tp / max(1, tp + fp)
    print(f"[{WID}] n {len(golds)}, missing labels {missing}; metaphorical P {100 * prec:.2f} R {100 * tp / max(1, tp + fn):.2f}; "
          f"literal P {100 * tn / max(1, tn + fn):.2f} R {100 * tn / max(1, tn + fp):.2f}")
    return prec, None


if __name__ == "__main__":
    s = _clean("But in the short-term it will absorb a lot of top management 's energy , '' says X -LRB- Y -RRB- ./.")
    assert s.endswith('says X ( Y ).') and _surface("absorb", s) == "absorb"
    assert _surface("drink", "They danced and drank until 10 p.m.") == "drank" and _surface("dance", "He tap-danced around") == "tap-danced"
    r = "- But: NO (conjunction)\n- absorb: YES (verb, more basic meaning is to soak up liquid)\n- **energy**: NO\n- top management 's: NO"
    p = parse(r, {})
    assert ("absorb", "YES") in p and ("energy", "NO") in p and len(p) == 4
    assert _label_for(p, {"form": "absorb", "target": "absorb", "label": "nonliteral"}) == "YES"
    assert _label_for(parse("- tap-danced around: NO", {}), {"form": "tap-danced", "target": "dance", "label": "literal"}) == "NO"
    assert _label_for(parse("- flew: YES", {}), {"form": "flew", "target": "fly", "label": "nonliteral"}) == "YES"
    v, _ = score([p, p, parse("- nothing: NO", {})],
                 [{"form": "absorb", "target": "absorb", "label": "nonliteral"}, {"form": "absorb", "target": "absorb", "label": "literal"},
                  {"form": "absorb", "target": "absorb", "label": "literal"}], {})
    assert abs(v - 1 / 3) < 1e-9, v                     # 1 TP, 1 FP, missing label on a literal -> counted as YES (FP)
    print("ok")
