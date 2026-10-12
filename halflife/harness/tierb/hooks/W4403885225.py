"""Hook for W4403885225 (CALM verbosity bias, Robustness Rate of GPT-4-Turbo as judge).

load_items: verbosity_bias_standardized.json (500 items) expanded to 1,000 rows: for each item an 'orig' row
            (Assistant A = answer1, Assistant B = answer2) and a 'pert' row (Assistant B = answer2_longer).
            gold = '<variant>|<item index>' so the scorer can pair the two verdicts.
render:     Figure 13 template (config user_template) filled with question / answer_a / answer_b.
parse:      last [[A]] / [[B]] verdict -> 'A' / 'B', None when absent.
score:      RR = share of items whose two verdicts agree (a missing verdict counts as changed); per-item = per pair.
"""
import json, re, urllib.request

URL = "https://raw.githubusercontent.com/Y0oMu/LLM-Judge-Bias-Dataset/main/bias_datasets/verbosity_bias_standardized.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}


def load_items(cfg):
    with urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    rows = []
    for i, it in enumerate(data):
        for variant, ans_b in (("orig", it["answer2"]), ("pert", it["answer2_longer"])):
            rows.append({"id": f"{i}_{variant}", "question": it["question"], "answer_a": it["answer1"], "answer_b": ans_b,
                         "data_resource": it.get("data_resource"), "pair_key": f"{variant}|{i}"})
    return rows


def render(cfg, row):
    t = cfg["prompt"]["user_template"]
    for k in ("question", "answer_a", "answer_b"):
        t = t.replace("{" + k + "}", str(row[k]))
    msgs = []
    if cfg["prompt"].get("system"):
        msgs.append({"role": "system", "content": cfg["prompt"]["system"]})
    msgs.append({"role": "user", "content": t})
    return msgs


def parse(text, cfg):
    if not text:
        return None
    hits = re.findall(r"\[\[([AB])\]\]", text)
    return hits[-1] if hits else None


def score(preds, golds, cfg):
    verdicts = {}
    for p, g in zip(preds, golds):
        variant, idx = str(g).split("|")
        verdicts.setdefault(idx, {})[variant] = p
    per = []
    for idx, v in verdicts.items():
        if "orig" not in v or "pert" not in v:
            continue                                   # one of the two calls missing: skip the pair
        per.append(1.0 if (v["orig"] is not None and v["orig"] == v["pert"]) else 0.0)
    return (sum(per) / len(per) if per else float("nan")), per


if __name__ == "__main__":
    print([parse(t, {}) for t in ("... [[A]] ...", "first [[B]] then [[A]]", "no verdict", "[[C]]")])
    assert [parse(t, {}) for t in ("... [[A]] ...", "first [[B]] then [[A]]", "no verdict", "[[C]]")] == ["A", "A", None, None]
    v, per = score(["A", "A", "B", "A", None, "A"], ["orig|0", "pert|0", "orig|1", "pert|1", "orig|2", "pert|2"], {})
    print(v, per)
    assert per == [1.0, 0.0, 0.0] and abs(v - 1 / 3) < 1e-9
