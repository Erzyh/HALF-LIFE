"""Merge the three judges' workbooks of the re-execution judgment and unblind the conditions.

python scripts/judgment_merge.py [--dir coding/results_judgment]
  reads  halflife_judgment_v2_judge{A,B,C}.xlsx (v1 returns are accepted; a v2 return supersedes a v1 return for the
         same judge; a judge's copy holds one set of columns, the master workbook with all three sets is accepted too).
         The v2 copies hide the automatic class, which is taken from coding/judgment_sheet_v1.xlsx by row.
  writes data/judgment_merged.csv          one row per judged result: sheet, row, paper, condition (unblinded from
                                           coding/judgment_key_v1.csv), values, automatic class, the three judgments,
                                           majority, agreement, conclusions, memos
         coding/judgment_disagreements.csv rows where the three judges do not agree, for the reconciliation meeting
  prints coverage per judge, Krippendorff's alpha and pairwise kappa per sheet (judgment and conclusion), majority
         tallies by condition and the cross-table of the automatic class against the majority.
Krippendorff's alpha and kappa come from scripts/coding_merge.py. No API calls.
"""
import argparse
import csv
import glob
import itertools
import sys
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import load_workbook

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "scripts"))
from coding_merge import kappa, kripp_alpha  # noqa: E402

JUDGES = ["A", "B", "C"]
SHEETS = {"TierA_claims": {"id": "카드", "label": "주장(지표)", "auto": "자동 판정(논문 단위 가안)"},
          "PromptLevel_blind": {"id": "논문 ID", "label": "지표", "auto": "자동 가안(값 수준)"}}
AUTO_MAP = {"재현": "생존", "근접": "부분 생존", "편차": "사망", "확인 필요": "판정 불능"}


def clean(v):
    return str(v).strip() if v not in (None, "") else None


def auto_from_master():
    """Automatic classes by (sheet, row) from the version-1 master; the version-2 judge copies hide that column."""
    out = {}
    p = HALF / "coding" / "judgment_sheet_v1.xlsx"
    if not p.exists():
        return out
    wb = load_workbook(p, read_only=True, data_only=True)
    for sheet, spec in SHEETS.items():
        rows = wb[sheet].iter_rows(values_only=True)
        header = [str(h) if h is not None else "" for h in next(rows)]
        col = {h: i for i, h in enumerate(header)}
        for r in rows:
            if r[0] is not None:
                out[(sheet, int(r[0]))] = clean(r[col[spec["auto"]]])
    return out


def read_judge(path, judge, auto_master=None):
    wb = load_workbook(path, read_only=True, data_only=True)
    out = {}
    for sheet, spec in SHEETS.items():
        ws = wb[sheet]
        rows = ws.iter_rows(values_only=True)
        header = [str(h) if h is not None else "" for h in next(rows)]
        col = {h: i for i, h in enumerate(header)}
        jc = col.get(f"판정 {judge}")
        cc = col.get(f"결론 수준 {judge}")
        mc = col.get(f"메모 {judge}")
        if jc is None:
            raise SystemExit(f"{path}: no column '판정 {judge}' in {sheet}")
        for r in rows:
            if r[0] is None:
                continue
            num = int(r[0])
            auto = clean(r[col[spec["auto"]]]) if spec["auto"] in col else (auto_master or {}).get((sheet, num))
            judgment = clean(r[jc])
            conclusion = clean(r[cc]) if cc is not None else None
            if judgment == "판정 불능" and conclusion is None:
                conclusion = "판단 불가"  # the guide maps 판정 불능 to 판단 불가; judges tend to leave the cell empty
            out[(sheet, num)] = {
                "judgment": judgment, "conclusion": conclusion, "memo": clean(r[mc]) if mc is not None else None,
                "meta": {"id": r[col[spec["id"]]], "paper": r[col["논문"]], "label": r[col[spec["label"]]], "original": r[col["원 논문 값"]],
                         "rerun": r[col["재실행 값"]], "ci_lo": r[col["95% 구간 하한"]], "ci_hi": r[col["95% 구간 상한"]], "auto": auto,
                         "code": r[col["조건 부호"]] if "조건 부호" in col else ""}}
    return out


def majority(vals):
    vals = [v for v in vals if v]
    if len(vals) < 2:
        return None, f"{len(vals)}/3 coded"
    c = Counter(vals).most_common()
    if len(c) == 1:
        return c[0][0], "3/3" if len(vals) == 3 else "2/2"
    if c[0][1] >= 2:
        return c[0][0], "2/3"
    return "불일치", "0/3"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(HALF / "coding" / "results_judgment"))
    a = ap.parse_args()
    files = {}
    for j in JUDGES:
        hits = sorted(glob.glob(str(Path(a.dir) / f"*judge{j}*.xlsx")))
        hits = [h for h in hits if "_v2_" in Path(h).name] or hits  # a v2 return supersedes a v1 return
        if hits:
            files[j] = hits[0]
    if len(files) < 2:
        raise SystemExit(f"need at least two judge files in {a.dir}, found {files}")
    auto_master = auto_from_master()
    data = {j: read_judge(f, j, auto_master) for j, f in files.items()}
    key = {int(r["row"]): r for r in csv.DictReader(open(HALF / "coding" / "judgment_key_v1.csv", encoding="utf-8-sig"))}
    units = sorted({u for d in data.values() for u in d}, key=lambda u: (u[0], u[1]))

    merged = []
    for sheet, num in units:
        meta = next(d[(sheet, num)]["meta"] for d in data.values() if (sheet, num) in d)
        js = {j: data.get(j, {}).get((sheet, num), {}).get("judgment") for j in JUDGES}
        cs = {j: data.get(j, {}).get((sheet, num), {}).get("conclusion") for j in JUDGES}
        ms = {j: data.get(j, {}).get((sheet, num), {}).get("memo") for j in JUDGES}
        maj, agr = majority(js.values())
        cmaj, _ = majority(cs.values())
        cond = key[num]["condition"] if sheet == "PromptLevel_blind" and num in key else ("tierA" if sheet == "TierA_claims" else "")
        wid = key[num]["wid"] if sheet == "PromptLevel_blind" and num in key else meta["id"]
        merged.append({"sheet": sheet, "row": num, "wid": wid, "condition": cond, "code": meta["code"], "paper": meta["paper"], "label": meta["label"],
                       "original": meta["original"], "rerun": meta["rerun"], "ci_lo": meta["ci_lo"], "ci_hi": meta["ci_hi"], "auto": meta["auto"],
                       **{f"judgment_{j}": js[j] or "" for j in JUDGES}, "majority": maj or "", "agreement": agr,
                       **{f"conclusion_{j}": cs[j] or "" for j in JUDGES}, "conclusion_majority": cmaj or "",
                       **{f"memo_{j}": ms[j] or "" for j in JUDGES}})
    (HALF / "data").mkdir(exist_ok=True)
    with open(HALF / "data" / "judgment_merged.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(merged[0].keys()))
        w.writeheader()
        w.writerows(merged)
    dis = [m for m in merged if m["agreement"] not in ("3/3",) and any(m[f"judgment_{j}"] for j in JUDGES)]
    with open(HALF / "coding" / "judgment_disagreements.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(merged[0].keys()))
        w.writeheader()
        w.writerows(dis)

    print("coverage:", {j: sum(1 for m in merged if m[f"judgment_{j}"]) for j in JUDGES}, "of", len(merged), "rows")
    for sheet in SHEETS:
        rows = [m for m in merged if m["sheet"] == sheet]
        ju = [[m[f"judgment_{j}"] for j in JUDGES if m[f"judgment_{j}"]] for m in rows]
        co = [[m[f"conclusion_{j}"] for j in JUDGES if m[f"conclusion_{j}"]] for m in rows]
        print(f"[{sheet}] rows {len(rows)} | judgment alpha {kripp_alpha(ju)} | conclusion alpha {kripp_alpha(co)} | full agreement "
              f"{sum(1 for m in rows if m['agreement'] == '3/3')}")
        for x, y in itertools.combinations(JUDGES, 2):
            pairs = [(m[f"judgment_{x}"], m[f"judgment_{y}"]) for m in rows if m[f"judgment_{x}"] and m[f"judgment_{y}"]]
            print(f"    kappa {x}-{y}: {kappa(pairs)}")
        by_cond = defaultdict(Counter)
        for m in rows:
            by_cond[m["condition"]][m["majority"] or "(none)"] += 1
        for cond, cnt in sorted(by_cond.items()):
            print(f"    {cond:12s} majority: {dict(cnt)}")
        cross = Counter((AUTO_MAP.get(m["auto"], str(m["auto"]).split(" (")[0]), m["majority"]) for m in rows if m["majority"])
        print("    automatic (mapped) vs majority:", dict(cross))
    print(f"-> data/judgment_merged.csv ({len(merged)} rows), coding/judgment_disagreements.csv ({len(dis)} rows)")


if __name__ == "__main__":
    main()
