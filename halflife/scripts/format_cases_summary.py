"""Format-adaptation case studies (approved 2026-10-02): does a minimal, pre-specified adaptation of the paper's prompt to the
designated replacement bring the reported value back?

For each selected paper (harness/tierb/paraphrase/format_adapt.json; rule in scripts/format_case_queues.py) the table gives,
on the paper's scale: the reported value, the pre-retirement baseline, the vendor-arm result scored with the paper's own
parser (Table S9), three adaptations and the class of each against the reported value under the prompt-level rule:
  L1  the archived vendor-arm replies re-scored after stripping markdown emphasis (** and __) before the paper's parser;
      no new calls (shows how much of the loss was decoration of an answer that is present);
  f1  one pass on the successor with one added sentence stating the output format the parser expects;
  f2  f1 plus the successor's lowest reasoning setting.
Writes data/format_cases.csv. No API calls. The L1 column re-scores the archived item replies (runs/tierb_p3/vendor/<Wid>/items.jsonl
and the call archive), which live in the Zenodo deposit; where they are absent (the public repository) the script prints a
note and leaves the committed data/format_cases.csv unchanged.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "harness"))
sys.path.insert(0, str(HALF / "scripts"))
import tierb_runner as tr  # noqa: E402
from p3_summary import classify, scaled  # noqa: E402

STRIP = re.compile(r"(\*\*|__)")


def load(p):
    p = Path(p)
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def rescore(wid, arm, transform=None):
    """Score an arm's archived seed-0 replies with the paper's parser and metric, optionally transforming the text first."""
    tr.RUNS = HALF / "runs" / "tierb_p3" / arm
    cfg = tr.load_cfg(wid)
    out = tr.RUNS / wid
    items = [json.loads(l) for l in open(out / "items.jsonl", encoding="utf-8") if l.strip()]
    res = tr.load_results(out)
    hook = tr.load_hook(wid)
    preds, golds, unparsed = [], [], 0
    for it in items:
        r = res.get((it["id"], 0))
        if not r:
            continue
        text = r["response"]["choices"][0]["message"].get("content") or ""
        if transform:
            text = transform(text)
        p = hook.parse(text, cfg) if hook and hasattr(hook, "parse") else tr.parse_output(text, cfg["output"].get("parse"))
        if p is None:
            unparsed += 1
        preds.append(p)
        golds.append(it["gold"])
    if hook and hasattr(hook, "score"):
        val, _ = hook.score(preds, golds, cfg)
    else:
        val, _ = tr.score_items(preds, golds, cfg["metric"]["name"])
    return float(val), unparsed, len(preds)


def main():
    table = load(HALF / "harness" / "tierb" / "paraphrase" / "format_adapt.json")
    wids = [w for w in table if w.startswith("W")]
    missing = [w for w in wids if not (HALF / "runs" / "tierb_p3" / "vendor" / w / "items.jsonl").exists()]
    if missing:
        print(f"format_cases_summary: the item archives of {len(missing)} of {len(wids)} papers are not present (they are in the "
              "Zenodo deposit, not in the repository); data/format_cases.csv is left as committed.")
        return
    rows = []
    for wid in wids:
        vend = load(HALF / "runs" / "tierb_p3" / "vendor" / wid / "result.json")
        base = load(HALF / "runs" / "tierb" / wid / "result.json")
        orig = vend["original_value"]
        scale = (vend.get("comparison") or {}).get("scale_applied") or 1.0
        v_val, v_lo, v_hi = scaled(vend)
        b_mean = ((base or {}).get("reexecution") or {}).get("mean_over_seeds")
        v_unp = vend["reexecution"].get("unparsed")
        n = vend["reexecution"]["per_seed"]["0"]["n"] if "0" in vend["reexecution"].get("per_seed", {}) else None
        # sanity: re-scoring the untouched replies must give the vendor value back
        chk, chk_unp, n_chk = rescore(wid, "vendor")
        l1, l1_unp, _ = rescore(wid, "vendor", lambda t: STRIP.sub("", t))
        row = {"wid": wid, "title": str(vend.get("title", ""))[:60], "metric": vend.get("metric"), "config_model": (vend.get("arm") or {}).get("config_model"),
               "successor": (vend.get("arm") or {}).get("model"), "n_items": n or n_chk, "original": orig,
               "baseline_pre_retirement": None if b_mean is None else round(b_mean * scale, 3),
               "vendor_value": None if v_val is None else round(v_val, 3), "vendor_unparsed": v_unp,
               "vendor_class": (pd.read_csv(HALF / "data" / "p3_summary.csv", encoding="utf-8-sig").query("arm == 'vendor' and wid == @wid").class_vs_original.iloc[0]),
               "rescore_check_value": round(chk * scale, 3), "rescore_check_unparsed": chk_unp,
               "L1_value": round(l1 * scale, 3), "L1_unparsed": l1_unp, "L1_class": classify(orig, l1 * scale, None, None)}
        for var in ("f1", "f2"):
            r = load(HALF / "runs" / "tierb_p3" / f"format_{var}" / wid / "result.json")
            b = load(HALF / "runs" / "tierb_p3" / f"format_{var}" / wid / "budget.json")
            if r:
                val, lo, hi = scaled(r)
                row.update({f"{var}_value": None if val is None else round(val, 3), f"{var}_ci_lo": lo, f"{var}_ci_hi": hi,
                            f"{var}_unparsed": r["reexecution"].get("unparsed"), f"{var}_class": classify(orig, val, lo, hi) if val is not None else None,
                            f"{var}_cost_usd": None if not b else round(b["cost_usd"], 2)})
            else:
                row.update({f"{var}_value": None, f"{var}_ci_lo": None, f"{var}_ci_hi": None, f"{var}_unparsed": None, f"{var}_class": None, f"{var}_cost_usd": None})
        e = table[wid]["f1"]
        old, new = e["pairs"][0]
        row["adaptation_sentence"] = new[len(old) - 1:] if new.startswith(old[:-1]) else new
        row["selected_because"] = None
        rows.append(row)
    q = load(HALF / "harness" / "tierb" / "queue_format_f1.json") or []
    why = {j["wid"]: j.get("selected_because") for j in q}
    for row in rows:
        row["selected_because"] = why.get(row["wid"])
    df = pd.DataFrame(rows)
    df.to_csv(HALF / "data" / "format_cases.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 30):
        print(df.drop(columns=["adaptation_sentence", "selected_because"]).to_string(index=False))
    for row in rows:
        print(row["wid"], "|", row["selected_because"], "| adaptation:", row["adaptation_sentence"][:140])


if __name__ == "__main__":
    main()
