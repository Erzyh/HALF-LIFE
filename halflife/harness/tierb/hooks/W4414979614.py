"""Hook W4414979614 (Swiss privacy law, GPT-5 controller-disclosure F1, English = 0.93).

load_items -> the 30 English policies of the 120-policy validation set, from the files pulled out of the Zenodo
              artifact (external/data/tierb_items/W4414979614/): policies/a_policy_{1..30}.txt plus the gold
              column `contr` of Phase_3_Ground_Truth.csv. Language blocks: 1-30 en, 31-60 de, 61-90 fr, 91-120 it.
render     -> the three messages of Validation_GPT_Swiss_GDPR_class.py: system = validation_system.txt,
              user = validation_user.txt (the codebook), user = the policy text. The runner's own render emits
              only one user message, hence this hook.
score      -> binary F1 with 'true' as the positive class (the artifact's Validation_metrics.py); the runner's
              macro_f1 would average the true and false classes and give a different number.
No parse: the config's "json field contr" is a runner facility.
"""
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4414979614"
LANG_OF = lambda n: "en" if n <= 30 else "de" if n <= 60 else "fr" if n <= 90 else "it"
TRUE = {"true", "1", "yes", "1.0"}


def _read(name):
    p = DATA / name
    if not p.exists():
        raise NeedsHuman(f"missing {p}; re-extract it from the Zenodo artifact (record 20794417, Artifacts.zip)")  # noqa: F821
    return p.read_text(encoding="utf-8")


def load_items(cfg):
    lang = (cfg.get("items", {}).get("filter") or "lang == 'en'").split("'")[1]
    gold = {}
    for r in csv.DictReader((DATA / "Phase_3_Ground_Truth.csv").open(encoding="utf-8")):
        gold[int(r["policy_name"])] = r
    rows = []
    for n in sorted(gold):
        if LANG_OF(n) != lang:
            continue
        if gold[n]["lang"] != lang:
            raise NeedsHuman(f"policy {n}: ground truth says lang={gold[n]['lang']}, block mapping says {lang}")  # noqa: F821
        rows.append({"id": str(n), "lang": lang, "policy_text": _read(f"policies/a_policy_{n}.txt"),
                     "contr": int(gold[n]["contr"])})
    if not rows:
        raise NeedsHuman(f"no policies for lang {lang!r}")  # noqa: F821
    return rows


def render(cfg, row):
    return [{"role": "system", "content": _read("validation_system.txt")},
            {"role": "user", "content": _read("validation_user.txt")},
            {"role": "user", "content": row["policy_text"]}]


def _is_true(v):
    return v is True or (v is not None and str(v).strip().lower() in TRUE)


def score(preds, golds, cfg=None):
    tp = fp = fn = 0
    for p, g in zip(preds, golds):
        pp, gg = _is_true(p), _is_true(g)
        tp += pp and gg
        fp += pp and not gg
        fn += (not pp) and gg
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return f1, None            # set-level metric: the runner resamples items to get the CI


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({"items": {"filter": "lang == 'en'"}})
    print(len(rows), "English policies |", sum(r["contr"] for r in rows), "with contr=1 |",
          sum(len(r["policy_text"]) for r in rows), "chars")
    msgs = render({}, rows[1])
    print("roles:", [m["role"] for m in msgs], "| sys", len(msgs[0]["content"]), "| codebook", len(msgs[1]["content"]),
          "| policy", len(msgs[2]["content"]))
    # the paper's own numbers: precision 0.8667, recall 1.0, F1 0.9285714... -> 13 gold positives, 15 predicted
    g = [r["contr"] for r in rows]
    preds = [True] * 0
    preds = [True if r["contr"] else False for r in rows]
    assert abs(score(preds, g)[0] - 1.0) < 1e-9
    extra = 0
    preds = []
    for r in rows:                       # reproduce precision 13/15, recall 13/13
        if r["contr"]:
            preds.append(True)
        elif extra < 2:
            preds.append(True); extra += 1
        else:
            preds.append(False)
    f1, _ = score(preds, g)
    assert abs(f1 - 0.9285714285714286) < 1e-9, f1
    assert score([None, "false", 0], [0, 0, 1])[0] == 0.0
    print("ok: perfect F1 1.0; 13/15 precision case ->", round(f1, 6), "(paper 0.9285714285714286)")
