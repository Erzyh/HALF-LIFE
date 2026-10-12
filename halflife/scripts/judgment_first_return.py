"""Agreement before the query rounds, as far as it can be measured (Supplementary Table 45b).

The judges' returns were compared with the written rule and rows that departed from it without a stated reason were
returned (Table S45 records the rounds). Only judge A's first return survives as a file
(coding/results_judgment/versions/halflife_judgment_v2_judgeA_20261011_0006.xlsx); the earlier returns of judges B and
C were overwritten on receipt. This script compares the survival class and the conclusion level of judge A's first
return with the final majority and with the final returns of judges B and C (data/judgment_final.csv), per sheet:
rows compared, per-cent agreement, Cohen's kappa, and Krippendorff's alpha over (A first, B final, C final) beside the
alpha of the three final returns. No API calls. Output: data/judgment_first_return.csv.
"""
import sys
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "scripts"))
from coding_merge import kappa, kripp_alpha  # noqa: E402
from judgment_merge import auto_from_master, read_judge  # noqa: E402

FIRST = HALF / "coding" / "results_judgment" / "versions" / "halflife_judgment_v2_judgeA_20261011_0006.xlsx"


def main():
    first = read_judge(FIRST, "A", auto_from_master())
    final = pd.read_csv(HALF / "data" / "judgment_final.csv", encoding="utf-8-sig")
    rows = []
    for sheet, label in (("PromptLevel_blind", "prompt-level results (baseline and successor conditions)"), ("TierA_claims", "repository-based claims")):
        f = final[final["sheet"] == sheet]
        for level, fcol_major, fcol in (("survival class", "majority", "judgment"), ("conclusion level", "conclusion_majority", "conclusion")):
            a_first, maj, b_fin, c_fin, a_fin = [], [], [], [], []
            for r in f.itertuples(index=False):
                rec = first.get((sheet, int(r.row)))
                if rec is None:
                    continue
                v = rec["judgment"] if level == "survival class" else rec["conclusion"]
                if level == "conclusion level" and v in ("생존", "부분 생존", "사망", "판정 불능"):
                    v = None                    # the first return repeated the survival classes in the conclusion column: not comparable
                a_first.append(v)
                maj.append(getattr(r, fcol_major))
                b_fin.append(getattr(r, f"{fcol}_B")); c_fin.append(getattr(r, f"{fcol}_C")); a_fin.append(getattr(r, f"{fcol}_A"))
            pairs_maj = [(a, m) for a, m in zip(a_first, maj) if a and isinstance(m, str) and m not in ("불일치",)]
            pairs_b = [(a, b) for a, b in zip(a_first, b_fin) if a and isinstance(b, str)]
            pairs_c = [(a, c) for a, c in zip(a_first, c_fin) if a and isinstance(c, str)]
            pairs_af = [(a, x) for a, x in zip(a_first, a_fin) if a and isinstance(x, str)]
            alpha_first = kripp_alpha([[a, b, c] for a, b, c in zip(a_first, b_fin, c_fin) if a and isinstance(b, str) and isinstance(c, str)])
            alpha_final = kripp_alpha([[x, b, c] for x, b, c in zip(a_fin, b_fin, c_fin) if isinstance(x, str) and isinstance(b, str) and isinstance(c, str)])
            km, kb, kc, ka = kappa(pairs_maj), kappa(pairs_b), kappa(pairs_c), kappa(pairs_af)
            rows.append({"sheet": label, "level": level, "rows_in_first_return": len([a for a in a_first if a]),
                         "note": "" if level == "survival class" else "not comparable: the first return's conclusion column repeated the survival classes (the query round clarified the column)",
                         "agreement_with_final_majority_pct": round(100 * km["percent_agreement"], 1) if km.get("n") else None, "kappa_vs_final_majority": km.get("kappa"),
                         "agreement_with_final_B_pct": round(100 * kb["percent_agreement"], 1) if kb.get("n") else None, "kappa_vs_final_B": kb.get("kappa"),
                         "agreement_with_final_C_pct": round(100 * kc["percent_agreement"], 1) if kc.get("n") else None, "kappa_vs_final_C": kc.get("kappa"),
                         "rows_changed_by_A_between_first_and_final": sum(1 for a, x in pairs_af if a != x),
                         "alpha_A_first_B_final_C_final": alpha_first, "alpha_three_final_returns": alpha_final})
    out = pd.DataFrame(rows)
    out.to_csv(HALF / "data" / "judgment_first_return.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(out.to_string(index=False))
    print("-> data/judgment_first_return.csv")


if __name__ == "__main__":
    main()
