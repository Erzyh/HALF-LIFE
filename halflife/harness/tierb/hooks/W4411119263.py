"""Hook for W4411119263 (ReIFE base protocol, gpt-4o-2024-05-13, Table 2 Avg.).

load_items: Hub config 'src', splits llmbar_natural / llmbar_adversarial / mtbench / instrusum (1,030 pairs), each
            pair expanded to two rows: 'ab' (Output (a) = output_1) and 'ba' (swapped). gold = '<letter>|<dataset>'
            with the human winner mapped to the presented order (winner 1 = output_1).
render:     Figure 6 prompt (config system + user_template) with INSTRUCTION / OUTPUT_1 / OUTPUT_2 of the row.
parse:      'Output (a)' / 'Output (b)' (case-insensitive); a reply naming both or neither -> None (incorrect).
score:      accuracy per dataset over both orders, then the unweighted mean over the four datasets (Table 2 Avg.).
            per-item values are reweighted so that their mean equals the macro average (approximate bootstrap CI).
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tierb_runner import load_hf  # noqa: E402

SPLITS = ["llmbar_natural", "llmbar_adversarial", "mtbench", "instrusum"]


def load_items(cfg):
    rows = []
    for split in SPLITS:
        part = load_hf("yale-nlp/ReIFE", f"src/{split}")
        for i, r in enumerate(part):
            win = int(r["winner"])                       # 1 = output_1, 2 = output_2
            for order in ("ab", "ba"):
                o1, o2 = (r["output_1"], r["output_2"]) if order == "ab" else (r["output_2"], r["output_1"])
                letter = ("a" if win == 1 else "b") if order == "ab" else ("b" if win == 1 else "a")
                rows.append({"id": f"{split}_{i}_{order}", "instruction": r["instruction"], "o1": o1, "o2": o2,
                             "dataset": split, "gold": f"{letter}|{split}"})
    return rows


def render(cfg, row):
    p = cfg["prompt"]
    u = p["user_template"].replace("{INSTRUCTION}", str(row["instruction"])).replace("{OUTPUT_1}", str(row["o1"])).replace("{OUTPUT_2}", str(row["o2"]))
    msgs = [{"role": "system", "content": p["system"]}] if p.get("system") else []
    msgs.append({"role": "user", "content": u})
    return msgs


def parse(text, cfg):
    if not text:
        return None
    hits = {m.lower() for m in re.findall(r"(?i)Output\s*\(([ab])\)", text)}
    return hits.pop() if len(hits) == 1 else None


def score(preds, golds, cfg):
    by = {}
    for p, g in zip(preds, golds):
        letter, ds = str(g).split("|")
        by.setdefault(ds, []).append(1.0 if p == letter else 0.0)
    accs = {ds: sum(v) / len(v) for ds, v in by.items()}
    value = sum(accs.values()) / len(accs)
    n_total, k = sum(len(v) for v in by.values()), len(by)
    per = []
    for p, g in zip(preds, golds):                      # weight so that mean(per) == macro average
        letter, ds = str(g).split("|")
        per.append((1.0 if p == letter else 0.0) * n_total / (k * len(by[ds])))
    return value, per


if __name__ == "__main__":
    ts = ["Output (a)", "output (B)", "Both Output (a) and Output (b) are fine", "neither", "Output (b) is better than (a)"]
    print([parse(t, {}) for t in ts])
    assert [parse(t, {}) for t in ts] == ["a", "b", None, None, "b"]
    v, per = score(["a", "b", "a", "a"], ["a|x", "a|x", "a|y", "b|y"], {})
    assert abs(v - 0.5) < 1e-9 and abs(sum(per) / len(per) - v) < 1e-9, (v, per)
    print("ok", v, per)
