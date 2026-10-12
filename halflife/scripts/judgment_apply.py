"""Apply the three-judge majority to the re-execution results (manuscript placeholder P2).

python scripts/judgment_apply.py
  reads  data/judgment_merged.csv (scripts/judgment_merge.py: the three judges' answers, conditions unblinded, majorities)
         coding/judgment_query_rounds.csv (the query rounds per judge, kept by hand from the review logs)
  writes data/judgment_final.csv          one row per judged result: condition, the majority in the manuscript's class
                                          vocabulary, the conclusion level, agreement, the automatic class and whether
                                          the majority overturned it
         data/judgment_tiera_papers.csv   the repository-based papers: claim-level majorities aggregated to the paper
         data/judgment_by_condition.csv   Supplementary Table 44: majority classes and conclusion levels by condition
         data/judgment_agreement.csv      Supplementary Table 45: agreement per sheet, rows where the judges overturned
                                          the rule, unresolved rows, query rounds per judge
Prompt-level classes keep the summaries' vocabulary (재현/근접/편차/확인 필요) so that scripts/tierb_summary.py and
scripts/p3_summary.py, and through them every figure and table, pick the judged classes up; the Tier A claim
majorities (생존/부분 생존/사망/판정 불능) go into data/tiera_claims.csv through scripts/tiera_claims.py.
No API calls.
"""
import csv
import itertools
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from coding_merge import kappa, kripp_alpha  # noqa: E402

JUDGES = ["A", "B", "C"]
TO_CLASS = {"생존": "재현", "부분 생존": "근접", "사망": "편차", "판정 불능": "확인 필요"}
AUTO_TO_JUDGE = {"재현": "생존", "근접": "부분 생존", "편차": "사망", "확인 필요": "판정 불능", "해당없음": "판정 불능"}
COND_LABEL = {"baseline": "Pre-retirement baseline (prompt-level)", "vendor": "Designated replacement gpt-5.6", "gpt41": "gpt-4.1",
              "open70b": "Open-weight Llama 3.3 70B", "gemini_flash": "Gemini 3.8 Flash"}
COND_ORDER = ["baseline", "vendor", "gpt41", "open70b", "gemini_flash"]
CONCL_EN = {"핵심 주장 성립": "claim holds", "부분 성립": "holds in part", "불성립": "claim fails", "판단 불가": "cannot judge", "불일치": "unresolved"}


def aggregate(values, order):
    """Paper-level verdict from claim-level values: the worst class present, ignoring 'cannot judge' unless it is all there is."""
    vals = [v for v in values if v]
    if not vals:
        return ""
    decided = [v for v in vals if v != order[-1]]
    if not decided:
        return order[-1]
    for v in order[:-1][::-1]:
        if v in decided:
            return v
    return decided[0]


def main():
    merged = list(csv.DictReader(open(ROOT / "data" / "judgment_merged.csv", encoding="utf-8-sig")))
    rounds = list(csv.DictReader(open(ROOT / "coding" / "judgment_query_rounds.csv", encoding="utf-8-sig")))
    final = []
    for m in merged:
        tiera = m["sheet"] == "TierA_claims"
        maj = m["majority"]
        auto = m["auto"] or ""
        auto_j = AUTO_TO_JUDGE.get(auto.split(" (")[0], auto.split(" (")[0])
        final.append({"sheet": m["sheet"], "row": m["row"], "wid": m["wid"], "condition": m["condition"], "label": m["label"],
                      "original": m["original"], "rerun": m["rerun"], "auto": auto.split(" (")[0], "majority": maj,
                      "class": maj if tiera else TO_CLASS.get(maj, maj), "conclusion_majority": m["conclusion_majority"],
                      "agreement": m["agreement"], "overturned": "" if tiera else ("yes" if maj and auto_j != maj else "no"),
                      **{f"judgment_{j}": m[f"judgment_{j}"] for j in JUDGES}, **{f"conclusion_{j}": m[f"conclusion_{j}"] for j in JUDGES}})
    with open(ROOT / "data" / "judgment_final.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(final[0].keys()))
        w.writeheader()
        w.writerows(final)

    # ---- Tier A papers
    by_paper = defaultdict(list)
    for r in final:
        if r["sheet"] == "TierA_claims":
            by_paper[r["wid"]].append(r)
    papers = []
    for wid, rs in by_paper.items():
        judged = aggregate([r["majority"] for r in rs], ["생존", "부분 생존", "사망", "판정 불능"])
        concl = aggregate([r["conclusion_majority"] for r in rs], ["핵심 주장 성립", "부분 성립", "불성립", "판단 불가"])
        auto = rs[0]["auto"]
        papers.append({"wid": wid, "title": next((m["paper"] for m in merged if m["wid"] == wid and m["sheet"] == "TierA_claims"), ""),
                       "claims": len(rs), "judged": judged, "automatic": auto, "changed": "yes" if auto != judged else "no", "conclusion": concl,
                       "claims_survived": sum(1 for r in rs if r["majority"] == "생존"), "claims_partial": sum(1 for r in rs if r["majority"] == "부분 생존"),
                       "claims_died": sum(1 for r in rs if r["majority"] == "사망"), "claims_cannot_judge": sum(1 for r in rs if r["majority"] == "판정 불능")})
    with open(ROOT / "data" / "judgment_tiera_papers.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(papers[0].keys()))
        w.writeheader()
        w.writerows(papers)

    # ---- Supplementary Table 44: by condition
    def block(rows, label, unit):
        c = Counter(r["majority"] for r in rows)
        k = Counter(r["conclusion_majority"] for r in rows)
        return {"condition": label, "unit": unit, "results": len(rows),
                "reproduced or survived": c.get("생존", 0), "close or partial": c.get("부분 생존", 0), "deviated or died": c.get("사망", 0),
                "could not be judged": c.get("판정 불능", 0), "rule overturned by the judges": sum(1 for r in rows if r["overturned"] == "yes"),
                "claim holds": k.get("핵심 주장 성립", 0), "holds in part": k.get("부분 성립", 0), "claim fails": k.get("불성립", 0),
                "cannot judge": k.get("판단 불가", 0), "conclusion unresolved": k.get("불일치", 0),
                "deviated but claim holds": sum(1 for r in rows if r["majority"] == "사망" and r["conclusion_majority"] == "핵심 주장 성립")}
    table = []
    for cond in COND_ORDER:
        table.append(block([r for r in final if r["condition"] == cond], COND_LABEL[cond], "paper"))
    table.append(block([r for r in final if r["sheet"] == "TierA_claims"], "Repository-based re-execution, claims", "claim"))
    pc = Counter(p["judged"] for p in papers)
    pk = Counter(p["conclusion"] for p in papers)
    table.append({"condition": "Repository-based re-execution, papers", "unit": "paper", "results": len(papers),
                  "reproduced or survived": pc.get("생존", 0), "close or partial": pc.get("부분 생존", 0), "deviated or died": pc.get("사망", 0),
                  "could not be judged": pc.get("판정 불능", 0), "rule overturned by the judges": sum(1 for p in papers if p["changed"] == "yes"),
                  "claim holds": pk.get("핵심 주장 성립", 0), "holds in part": pk.get("부분 성립", 0), "claim fails": pk.get("불성립", 0),
                  "cannot judge": pk.get("판단 불가", 0), "conclusion unresolved": 0,
                  "deviated but claim holds": 0})
    with open(ROOT / "data" / "judgment_by_condition.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys()))
        w.writeheader()
        w.writerows(table)

    # ---- Supplementary Table 45: agreement, overturned rows, query rounds
    items = []
    for sheet, name in (("PromptLevel_blind", "prompt-level results (343 rows: 86 baselines and 257 successor results)"), ("TierA_claims", "repository-based claims (95 rows)")):
        rows = [m for m in merged if m["sheet"] == sheet]
        ju = [[m[f"judgment_{j}"] for j in JUDGES if m[f"judgment_{j}"]] for m in rows]
        co = [[m[f"conclusion_{j}"] for j in JUDGES if m[f"conclusion_{j}"]] for m in rows]
        items.append((f"{name}: Krippendorff's alpha, survival class", kripp_alpha(ju)))
        items.append((f"{name}: Krippendorff's alpha, conclusion level", kripp_alpha(co)))
        for x, y in itertools.combinations(JUDGES, 2):
            kp = kappa([(m[f"judgment_{x}"], m[f"judgment_{y}"]) for m in rows])
            kc = kappa([(m[f"conclusion_{x}"], m[f"conclusion_{y}"]) for m in rows])
            items.append((f"{name}: Cohen's kappa {x}-{y}, survival class / conclusion level", f"{kp['kappa']} / {kc['kappa']}"))
        items.append((f"{name}: rows with three identical survival classes / with a majority / without a majority",
                      f"{sum(1 for m in rows if m['agreement'] == '3/3')} / {sum(1 for m in rows if m['majority'] not in ('', '불일치'))} / {sum(1 for m in rows if m['majority'] == '불일치')}"))
        items.append((f"{name}: conclusion level rows with three identical answers / without a majority",
                      f"{sum(1 for m in rows if len({m[f'conclusion_{j}'] for j in JUDGES}) == 1)} / {sum(1 for m in rows if m['conclusion_majority'] == '불일치')}"))
    over = [r for r in final if r["overturned"] == "yes"]
    items.append(("prompt-level rows where the majority overturned the written rule's class", f"{len(over)}: " + "; ".join(f"row {r['row']} {r['wid']} {r['condition']} ({r['auto']} -> {r['majority']})" for r in over)))
    items.append(("repository-based papers whose paper-level class differs from the automatic verdict",
                  f"{sum(1 for p in papers if p['changed'] == 'yes')}: " + "; ".join(f"{p['wid']} ({p['automatic']} -> {p['judged']})" for p in papers if p["changed"] == "yes")))
    items.append(("rule the judges applied", "a result reproduced when the reported value lies inside the re-run's 95% interval or within two points on the paper's scale, close within five points, deviated otherwise; results that are not scores (t statistic, odds ratio, kilometre error) judged by the interval alone and cannot be judged without one; results with more than half of the replies unparsed, or a task that does not transfer, cannot be judged; repository-based claims over five points with the same sign are partial (died only when the direction reverses)"))
    items.append(("conclusion level", "whether the sentence the paper builds on the number still holds at the re-run value: holds, holds in part, fails, cannot judge; for a limitation the paper points out, a larger problem keeps the claim and a vanished problem fails it"))
    for r in rounds:
        items.append((f"query round: judge {r['judge']}, return {r['round']} ({r['received']})", f"{r['rows_departing_from_written_rule']} of {r['of_rows']} rows departed from the written rule; {r['notes']}"))
    items.append(("procedure of the query rounds", "each return was compared with the written rule; rows that departed from it without a stated reason were returned to the judge with the rule restated; answers with a stated reason were kept; judges never saw each other's answers; the first return of each judge is archived"))
    with open(ROOT / "data" / "judgment_agreement.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "value"])
        w.writerows(items)

    cnt = Counter((r["condition"], r["majority"]) for r in final if r["sheet"] == "PromptLevel_blind")
    print("prompt-level majorities:", {c: {k: v for (cc, k), v in cnt.items() if cc == c} for c in COND_ORDER})
    print("Tier A papers:", dict(pc), "| changed:", [(p["wid"], p["automatic"], p["judged"]) for p in papers if p["changed"] == "yes"])
    print("overturned prompt-level rows:", [(r["row"], r["auto"], r["majority"]) for r in over])
    print("-> data/judgment_final.csv, data/judgment_tiera_papers.csv, data/judgment_by_condition.csv, data/judgment_agreement.csv")


if __name__ == "__main__":
    main()
