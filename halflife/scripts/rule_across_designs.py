"""One classification rule applied to both re-execution designs (Supplementary Table 47).

The paper classes the repository-based re-executions with a claim-level rule (a claim survives within 2 points or
inside the re-run interval, survives in part when it moves with the same sign, dies only when its direction reverses;
a paper takes the worst class of its claims) and the prompt-level ones with the four-class rule (reproduced within 2
points or inside the interval, close within 5 points, deviated beyond). The two headlines, "no repository-based
re-execution died" and "20 of 86 prompt-level results deviated", therefore rest on different rules. Here each rule is
applied to both designs, on the points scale of data/reexec_forest.csv (claims whose unit is not a points scale are
left out and counted). No API calls. Output: data/rule_across_designs.csv.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def prompt_rule(d, inside):
    if inside or abs(d) <= 2:
        return "reproduced"
    return "close" if abs(d) <= 5 else "deviated"


def repo_rule(d, inside, reversed_direction=False):
    if reversed_direction:
        return "died"
    if inside or abs(d) <= 2:
        return "survived"
    return "partial"


WORST = {"reproduced": 0, "close": 1, "deviated": 2, "survived": 0, "partial": 1, "died": 2}


def main():
    f = pd.read_csv(ROOT / "data" / "reexec_forest.csv", encoding="utf-8-sig")
    f["tier"] = f["tier"].astype(str).str.upper()
    f["on_points"] = f["unit"].astype(str).str.startswith("points")
    f["inside"] = (f["original"] >= f["ci_lo"]) & (f["original"] <= f["ci_hi"])
    rows = []
    for tier, design in (("A", "repository-based (claims)"), ("B", "prompt-level (results)")):
        sub = f[f["tier"] == tier]
        pts = sub[sub["on_points"] & sub["difference"].notna()]
        off = len(sub) - len(pts)
        for rule_name, fn in (("prompt-level rule (2 / 5 points, interval clause)", prompt_rule), ("repository rule (same sign = partial, reversal = died)", repo_rule)):
            cls = [fn(d, i) for d, i in zip(pts["difference"], pts["inside"])]
            unit_counts = pd.Series(cls).value_counts().to_dict()
            # paper level: worst class among the paper's claims
            tmp = pts.assign(cls=cls)
            worst = tmp.groupby("id")["cls"].agg(lambda s: max(s, key=lambda c: WORST[c]))
            paper_counts = worst.value_counts().to_dict()
            last = "deviated" if fn is prompt_rule else "died"
            mid = "close" if fn is prompt_rule else "partial"
            first = "reproduced" if fn is prompt_rule else "survived"
            rows.append({"design": design, "rule": rule_name, "classes": f"{first} / {mid} / {last}", "units_on_points_scale": len(pts), "units_left_out": off,
                         "units_class_1": unit_counts.get(first, 0), "units_class_2": unit_counts.get(mid, 0), "units_class_3": unit_counts.get(last, 0),
                         "papers": int(worst.shape[0]), "papers_class_1": paper_counts.get(first, 0), "papers_class_2": paper_counts.get(mid, 0),
                         "papers_class_3": paper_counts.get(last, 0), "papers_in_worst_class_pct": round(100 * paper_counts.get(last, 0) / max(worst.shape[0], 1), 1),
                         "note": ("a single number per result: a reversed direction is not defined, so 'died' cannot occur" if (tier == "B" and fn is repo_rule)
                                  else "a paper takes the worst class among its claims" if tier == "A" else "")})
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "data" / "rule_across_designs.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(out.to_string(index=False))
    print("-> data/rule_across_designs.csv")


if __name__ == "__main__":
    main()
