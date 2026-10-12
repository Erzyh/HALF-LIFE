"""Audit of the eligibility triage (Table S40). No API calls.

Three blocks, one row per measure:
  completeness  - the agent-written triage records (harness/tierb/<Wid>.json): verdict counts; eligible records that
                  carry a quoted passage and a location for the resolved live model, a claim cell with metric, value
                  and item count, and a data source; ineligible records that name at least one blocker.
  outcome       - validation of the eligible class by what happened downstream: of the 86 configurations judged
                  executable without human input, how many produced a scorable number (data/reexec_forest.csv), and
                  how many of the 20 deviations traced to a procedure the triage had not flagged (data/deviation_causes.csv).
  cross-judge   - agreement of the second reader (scripts/triage_crossjudge.py -> data/triage_crossjudge.csv) with the
                  original verdict: three-class and eligible-versus-not agreement with Cohen's kappa, per original class,
                  and agreement on the resolved live model.
Output: data/triage_audit.csv.
"""
import csv, glob, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ("eligible", "maybe", "ineligible")


def kappa(a, b, labels):
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] * cb[l] for l in labels) / (n * n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def pct(k, n):
    return round(100 * k / n, 1) if n else ""


def main():
    recs = [json.load(open(f, encoding="utf-8")) for f in glob.glob(str(ROOT / "harness" / "tierb" / "W*.json"))]
    recs = [r for r in recs if r.get("verdict") in CLASSES]
    rows = []

    def add(block, measure, n, count, note=""):
        rows.append({"block": block, "measure": measure, "n": n, "count": count, "pct": pct(count, n) if isinstance(count, int) else "", "note": note})

    byv = Counter(r["verdict"] for r in recs)
    for c in CLASSES:
        add("completeness", f"records with verdict {c}", len(recs), byv[c], "1,185 records: 600 read on 5-7 September 2026, 585 on 19 September")
    el = [r for r in recs if r["verdict"] == "eligible"]
    lm = lambda r: r.get("live_model") or {}
    cl = lambda r: r.get("claim") or {}
    add("completeness", "eligible: resolved live model has a quoted passage", len(el), sum(1 for r in el if str(lm(r).get("evidence") or "").strip() != ""))
    add("completeness", "eligible: claim cell has a location", len(el), sum(1 for r in el if str(cl(r).get("location") or "").strip() != ""))
    add("completeness", "eligible: claim has a numeric value and an item count", len(el),
        sum(1 for r in el if isinstance(cl(r).get("value"), (int, float)) and isinstance(cl(r).get("n_items"), (int, float))))
    add("completeness", "eligible: data source named", len(el), sum(1 for r in el if str((r.get("data") or {}).get("source") or "").strip() != ""))
    inel = [r for r in recs if r["verdict"] == "ineligible"]
    add("completeness", "ineligible: at least one blocker named", len(inel), sum(1 for r in inel if r.get("blockers")))
    bl = Counter(b for r in inel for b in (r.get("blockers") or []))
    add("completeness", "ineligible: blockers named (counts)", len(inel), "", "; ".join(f"{k} {v}" for k, v in bl.most_common()))
    # outcome-based validation
    tb = [r for r in csv.DictReader(open(ROOT / "data" / "reexec_forest.csv", encoding="utf-8-sig")) if r["tier"] == "B"]
    scor = sum(1 for r in tb if r.get("class_provisional", r["class"]) in ("재현", "근접", "편차"))  # scorability is a harness outcome: the provisional class, not the judged one
    add("outcome", "configurations judged executable without human input that produced a number the judges could score", len(tb), scor,
        "the remaining two could not be judged: one with more than half of its replies unparsable, one a non-score quantity reported without an interval")
    lt = [r for r in csv.DictReader(open(ROOT / "data" / "loss_typology.csv", encoding="utf-8-sig"))
          if r["mode"].startswith("3 ") and r["stage"] == "Tier B deviations after triage"]
    if lt:
        add("outcome", "deviations traced to a step the paper did not report, which the triage had judged complete (prompt wording, label mapping)",
            int(lt[0]["denominator"]), int(lt[0]["count"]), "mode 3 of the loss typology at the stage 'Tier B deviations after triage' (Tables S4 and S15)")
    # cross-judgement
    p = ROOT / "data" / "triage_crossjudge.csv"
    if p.exists():
        cj = list(csv.DictReader(open(p, encoding="utf-8-sig")))
        a3 = [r["original_verdict"] for r in cj]
        b3 = [r["second_verdict"] for r in cj]
        add("cross-judge", "three-class verdict identical (eligible / maybe / ineligible)", len(cj), sum(x == y for x, y in zip(a3, b3)),
            f"Cohen's kappa {kappa(a3, b3, CLASSES + ('unparsable',))}; second reader gpt-4.1-2025-04-14, 20 records per original class, seed 20260907")
        a2 = ["eligible" if x == "eligible" else "not" for x in a3]
        b2 = ["eligible" if x == "eligible" else "not" for x in b3]
        add("cross-judge", "eligible versus not eligible identical", len(cj), sum(x == y for x, y in zip(a2, b2)), f"Cohen's kappa {kappa(a2, b2, ('eligible', 'not'))}")
        for c in CLASSES:
            sub = [r for r in cj if r["original_verdict"] == c]
            add("cross-judge", f"original verdict {c}: second reader gives the same verdict", len(sub), sum(1 for r in sub if r["second_verdict"] == c),
                "second verdicts: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(r["second_verdict"] for r in sub).items())))
        add("cross-judge", "resolved live model identical", len(cj), sum(1 for r in cj if r["original_resolved_model"] == r["second_resolved_model"]))
        add("cross-judge", "second reader cost (USD) and texts truncated at 120,000 characters", len(cj), sum(int(r["truncated"]) for r in cj),
            f"cost {sum(float(r['cost_usd']) for r in cj):.2f}")
    with open(ROOT / "data" / "triage_audit.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["block", "measure", "n", "count", "pct", "note"])
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['block']:12s} {r['measure'][:80]:80s} {r['count']}/{r['n']} {r['pct']}")
    print("-> data/triage_audit.csv")


if __name__ == "__main__":
    main()
