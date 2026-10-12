"""Merge the coders' workbooks and compute agreement (coding/CODEBOOK.md §5). Works for 2..N coders.

python scripts/coding_merge.py --set pilot [--files a.xlsx b.xlsx ...]
  -> coding/merge_<set>.json (Krippendorff's alpha, pairwise Cohen's kappa, coverage)
     coding/disagreements_<set>.csv (units where coders differ, with the suggested tie-breaker:
     the assigned third coder from data/coding/assignment_<set>.csv when there is one)

Units: (paper, matched ID) for the role code; paper for Q1-Q6. Blank cells mean "not yet coded" and
are left out; a unit enters the agreement statistics only when at least two coders coded it.
Krippendorff's alpha (nominal) handles any number of coders and missing codes, so it is the headline
figure with rotating pairs; pairwise kappa is reported for the pairs that share units.
"""
import argparse, csv, itertools, json
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "coding"
MAX_IDS = 6
QCOLS = ["Q1 접근경로", "Q2 버전표기", "Q3 실행시점", "Q5 열람", "Q6 확신도"]
DEP = {"실행": "의존", "인용·언급": "비의존", "못찾음": "비의존"}
# workbooks made before codebook v1.2 used letter codes; map them so old and new files merge alike
OLD_ROLE = {"S": "실행", "B": "실행", "A": "실행", "C": "인용·언급", "X": "못찾음", "U": "판단불가"}
OLD_Q2 = {"D": "날짜 스냅숏", "A": "별칭·계열명", "P": "제품명", "N": "해당없음"}


def norm_code(code):
    if code in (None, ""):
        return None
    c = str(code).strip()
    return OLD_ROLE.get(c.upper(), c)


def read(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb["코딩"]
    rows = ws.iter_rows(values_only=True)
    header = [str(h) if h is not None else "" for h in next(rows)]
    col = {h: i for i, h in enumerate(header)}
    out = {}
    for r in rows:
        if r[col["openalex_id"]] is None:
            continue
        wid = str(r[col["openalex_id"]])
        rec = {"num": r[col["번호"]], "title": r[col["제목"]], "roles": {}, "memo": r[col["메모"]]}
        for k in range(1, MAX_IDS + 1):
            mid, code = r[col[f"ID{k}"]], r[col[f"ID{k} 역할"]]
            if mid:
                rec["roles"][str(mid)] = norm_code(code)
        for q in QCOLS:
            v = r[col[q]] if q in col else None
            v = str(v).strip() if v not in (None, "") else None
            if q == "Q2 버전표기" and v in OLD_Q2:
                v = OLD_Q2[v]
            if q == "Q3 실행시점" and v == "N":
                v = "해당없음"
            rec[q] = v
        m = r[col["실행한 모델(전체)"]] if "실행한 모델(전체)" in col else None
        rec["models"] = str(m).strip() if m not in (None, "") else None
        out[wid] = rec
    return out


def kripp_alpha(units):
    """Krippendorff's alpha, nominal metric. units: iterable of lists of codes (only lists with >= 2 codes count)."""
    o = Counter()
    for u in units:
        m = len(u)
        if m < 2:
            continue
        for i in range(m):
            for j in range(m):
                if i != j:
                    o[(u[i], u[j])] += 1.0 / (m - 1)
    if not o:
        return None
    n_c = Counter()
    for (c, k), v in o.items():
        n_c[c] += v
    n = sum(n_c.values())
    if n <= 1:
        return None
    d_o = sum(v for (c, k), v in o.items() if c != k)
    d_e = sum(n_c[c] * n_c[k] for c in n_c for k in n_c if c != k) / (n - 1)
    return None if d_e == 0 else round(1 - d_o / d_e, 3)


def kappa(pairs):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    n = len(pairs)
    if n == 0:
        return {"n": 0}
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return {"n": n, "percent_agreement": round(po, 3), "kappa": round(k, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="pilot")
    ap.add_argument("--files", nargs="+")
    ap.add_argument("--dir", default=None, help="folder holding the returned workbooks (default coding/coders<k>/ with the most files)")
    a = ap.parse_args()
    if a.files:
        files = a.files
    else:
        folder = Path(a.dir) if a.dir else max(OUTDIR.glob("coders*"), key=lambda d: len(list(d.glob(f"halflife_coding_{a.set}_coder*.xlsx"))), default=OUTDIR)
        files = sorted(str(p) for p in folder.glob(f"halflife_coding_{a.set}_coder*.xlsx"))
    if len(files) < 2:
        raise SystemExit(f"need at least two workbooks, found {files}")
    coders = {}
    for f in files:
        name = Path(f).stem.split("coder")[-1]
        coders[name] = read(f)
    names = sorted(coders)
    third = {}
    ap_path = ROOT / "data" / "coding" / f"assignment_{a.set}_k{len(names)}.csv"
    if ap_path.exists():
        for r in csv.DictReader(open(ap_path, encoding="utf-8-sig")):
            third[r["openalex_id"].rsplit("/", 1)[-1]] = r.get("third_coder", "")

    # collect codes per unit
    role_units = defaultdict(dict)      # (wid, mid) -> {coder: code}
    q_units = {q: defaultdict(dict) for q in QCOLS}
    titles = {}
    for name, data in coders.items():
        for wid, rec in data.items():
            titles[wid] = (rec["num"], rec["title"])
            for mid, code in rec["roles"].items():
                if code:
                    role_units[(wid, mid)][name] = code
            for q in QCOLS:
                if rec[q]:
                    q_units[q][wid][name] = rec[q]

    def stats(units):
        multi = [list(v.values()) for v in units.values() if len(v) >= 2]
        return {"units_coded_by_2plus": len(multi), "alpha": kripp_alpha(multi),
                "percent_agreement": (round(sum(1 for u in multi if len(set(u)) == 1) / len(multi), 3) if multi else None)}
    res = {"set": a.set, "coders": names, "files": files,
           "coded_papers": {n: sum(1 for r in d.values() if any(r["roles"].values())) for n, d in coders.items()},
           "role": stats(role_units),
           "dependence_collapsed": stats({k: {c: DEP[v] for c, v in d.items() if v in DEP} for k, d in role_units.items()}),
           "pairwise_role_kappa": {}, "questions": {q: stats(q_units[q]) for q in QCOLS}}
    for x, y in itertools.combinations(names, 2):
        pairs = [(d.get(x), d.get(y)) for d in role_units.values() if x in d and y in d]
        res["pairwise_role_kappa"][f"{x}-{y}"] = kappa(pairs)
    res["role_distribution"] = {n: dict(Counter(c for r in d.values() for c in r["roles"].values() if c)) for n, d in coders.items()}

    dis = []
    for (wid, mid), d in role_units.items():
        if len(d) >= 2 and len(set(d.values())) > 1:
            dis.append({"num": titles[wid][0], "openalex_id": wid, "item": f"역할:{mid}", **{f"code_{n}": d.get(n, "") for n in names},
                        "tie_breaker": third.get(wid, ""), "title": titles[wid][1]})
    for q in QCOLS:
        for wid, d in q_units[q].items():
            if len(d) >= 2 and len(set(d.values())) > 1:
                dis.append({"num": titles[wid][0], "openalex_id": wid, "item": q, **{f"code_{n}": d.get(n, "") for n in names},
                            "tie_breaker": third.get(wid, ""), "title": titles[wid][1]})
    dis.sort(key=lambda r: (r["num"] or 0, r["item"]))
    (OUTDIR / f"merge_{a.set}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(OUTDIR / f"disagreements_{a.set}.csv", "w", newline="", encoding="utf-8-sig") as f:
        fields = ["num", "openalex_id", "item"] + [f"code_{n}" for n in names] + ["tie_breaker", "title"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(dis)
    # models the authors ran, as the coders wrote them (raw strings; the vocabulary extension starts here)
    strings = Counter()
    with open(OUTDIR / f"models_{a.set}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["num", "openalex_id", "coder", "models_run"])
        for name, data in coders.items():
            for wid, rec in data.items():
                if rec.get("models"):
                    w.writerow([rec["num"], wid, name, rec["models"]])
                    for s in rec["models"].split(","):
                        if s.strip():
                            strings[s.strip()] += 1
    with open(OUTDIR / f"models_{a.set}_strings.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["model_string", "count"])
        w.writerows(strings.most_common())
    print(json.dumps({k: v for k, v in res.items() if k != "files"}, ensure_ascii=False, indent=1))
    print(f"disagreements: {len(dis)} -> coding/disagreements_{a.set}.csv; model strings: {len(strings)} -> coding/models_{a.set}_strings.csv")


if __name__ == "__main__":
    # tiny self-check of alpha: perfect agreement -> 1.0; independent codes -> about 0
    assert kripp_alpha([["a", "a"], ["b", "b"], ["a", "a", "a"]]) == 1.0
    main()
