"""Third-coder adjudication of the main-sample coding (CODEBOOK §6.5; MAIN_DISTRIBUTION '회신 처리' 3).

python scripts/coding_adjudicate.py build   [--dir coding/results_main] [--roles-only]
    Applies the written merge rules to the two coders' codes of every main-sample paper and writes
      coding/adjudication_main_resolved.csv      units settled by a rule (which rule)
      coding/adjudication_main_pending.csv       units that need a third coder, with the coder assigned
      coding/adjudication/halflife_adjudication_main_coder{A,B,C,D}.xlsx
            one workbook per third coder: tab '역할' (needed: role clashes, and papers neither coder could open)
            and tab 'Q1~Q3' (optional: access path and designation clashes on executed papers).
    Rules (codebook v1.3): a coder who opened the full text beats '판단불가'; found beats not found
    (인용·언급 over 못찾음, a dated snapshot decides Q2, a run date decides Q3); '해당없음' on Q1-Q3 follows the
    paper's dependence once that is settled. Everything else goes to the third coder named in
    data/coding/assignment_main_k4.csv (the two coders who did not code the paper; each paper goes to the less loaded one).
python scripts/coding_adjudicate.py collect [--dir coding/results_adjudication]
    Reads the returned workbooks and writes coding/adjudication_main_decisions.csv (one row per unit with the
    third coder's decision and memo). coding_main_report.py applies that file.
No API calls. The coders' own workbooks are never modified.
"""
import argparse
import csv
import glob
import sys
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from coding_merge import read  # noqa: E402

CODERS = "ABCD"
ROLE_CODES = ["실행", "인용·언급", "못찾음", "판단불가"]
Q_CODES = {"Q1 접근경로": ["API", "웹UI", "혼합", "클라우드배포", "서드파티", "로컬", "해당없음", "불명"],
           "Q2 버전표기": ["날짜 스냅숏", "별칭·계열명", "제품명", "해당없음"],
           "Q3 실행시점": ["연월", "연도만", "없음", "해당없음"]}
QS = list(Q_CODES)
FONT = "Malgun Gothic"
YELLOW = PatternFill("solid", fgColor="FFFF00")
GREY = PatternFill("solid", fgColor="EEEEEE")
ADJ_DIR = ROOT / "coding" / "adjudication"
DECISIONS = ROOT / "coding" / "adjudication_main_decisions.csv"


def verdict(roles):
    codes = [c for c in roles.values() if c]
    if not codes:
        return None
    if "실행" in codes:
        return "의존"
    if all(c in ("인용·언급", "못찾음") for c in codes):
        return "비의존"
    return "판단불가"


def load(dir_):
    data = {c: read(str(Path(dir_) / f"halflife_coding_main_coder{c}.xlsx")) for c in CODERS}
    sample = {r["openalex_id"].rsplit("/", 1)[-1]: r for r in csv.DictReader(open(ROOT / "data" / "coding" / "sample_v1.csv", encoding="utf-8-sig"))
              if r["set"] == "main"}
    third = {r["openalex_id"].rsplit("/", 1)[-1]: r["third_coder"] for r in csv.DictReader(open(ROOT / "data" / "coding" / "assignment_main_k4.csv", encoding="utf-8-sig"))}
    return data, sample, third


def read_decisions(path=DECISIONS):
    if not Path(path).exists():
        return {}
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        if r.get("decision"):
            out[(r["openalex_id"], r["item"], r.get("mid", ""))] = r
    return out


def resolve(data, sample, decisions=None):
    """One record per main-sample paper with the rule-resolved codes and the units still pending."""
    decisions = decisions or {}
    recs = {}
    for wid in sample:
        have = [c for c in CODERS if wid in data[c]]
        recs[wid] = rec = {"wid": wid, "num": None, "title": None, "coders": have, "verdicts": {}, "q5": {}, "models": {}, "memo": {},
                           "roles": {}, "role_how": {}, "q": {}, "q_how": {}, "pending": [], "note": ""}
        if not have:
            rec["dependence"], rec["how"] = None, "uncoded"
            continue
        for c in have:
            r = data[c][wid]
            rec["num"], rec["title"] = r["num"], r["title"]
            rec["verdicts"][c] = verdict(r["roles"])
            rec["q5"][c] = r["Q5 열람"]
            rec["models"][c] = r["models"] or ""
            rec["memo"][c] = r["memo"] or ""
        # ---- roles per identifier
        matched = set(sample[wid].get("matched_models", "").split("|"))
        mids = []
        for c in have:
            for m, code in data[c][wid]["roles"].items():
                if m not in mids and (m in matched or code):  # a stray string typed into an empty ID cell is ignored
                    mids.append(m)
        for mid in mids:
            codes = {c: data[c][wid]["roles"].get(mid) for c in have}
            vals = [v for v in codes.values() if v]
            dec = decisions.get((wid, f"역할:{mid}", mid))
            if dec:
                rec["roles"][mid], rec["role_how"][mid] = dec["decision"], "third"
            elif len(set(vals)) <= 1:
                rec["roles"][mid], rec["role_how"][mid] = (vals[0] if vals else None), ("agree" if len(vals) == 2 else "single")
            elif "판단불가" in vals:
                other = [(c, v) for c, v in codes.items() if v and v != "판단불가"]
                c, v = other[0]
                if rec["q5"].get(c) == "전문":
                    rec["roles"][mid], rec["role_how"][mid] = v, "fulltext"
                else:
                    rec["roles"][mid], rec["role_how"][mid] = None, "pending"
                    rec["pending"].append(("역할", mid, codes))
            elif set(vals) == {"못찾음", "인용·언급"}:
                rec["roles"][mid], rec["role_how"][mid] = "인용·언급", "found"
            else:
                rec["roles"][mid], rec["role_how"][mid] = None, "pending"
                rec["pending"].append(("역할", mid, codes))
        # ---- paper-level dependence with bounds over the pending units
        both_unopened = len(have) == 2 and all(v == "판단불가" for v in rec["verdicts"].values())
        if both_unopened and not any(h == "third" for h in rec["role_how"].values()):
            rec["dependence"], rec["how"] = None, "both_unopened"
            rec["note"] = "두 코더 모두 전문을 열지 못함"
            rec["pending"] = [("역할", m, {c: data[c][wid]["roles"].get(m) for c in have}) for m in mids]
        else:
            settled = {m: v for m, v in rec["roles"].items() if v}
            lo = dict(settled, **{m: "인용·언급" for m, v in rec["roles"].items() if v is None})
            hi = dict(settled, **{m: "실행" for m, v in rec["roles"].items() if v is None})
            vlo, vhi = verdict(lo), verdict(hi)
            if vlo == vhi:
                rec["dependence"] = vlo
                hows = set(rec["role_how"].values())
                rec["how"] = "third" if "third" in hows else ("fulltext" if "fulltext" in hows else ("single" if "single" in hows else "agree"))
            else:
                rec["dependence"], rec["how"] = None, "pending"
        # ---- questions
        for q in QS:
            codes = {}
            for c in have:
                v = data[c][wid][q]
                if v is None and rec["verdicts"][c] == "비의존":
                    v = "해당없음"  # a blank on a paper the coder judged non-executing means 해당없음 (codebook §5)
                codes[c] = v
            vals = [v for v in codes.values() if v]
            dec = decisions.get((wid, q, ""))
            if dec:
                rec["q"][q], rec["q_how"][q] = dec["decision"], "third"
            elif len(set(vals)) <= 1:
                rec["q"][q], rec["q_how"][q] = (vals[0] if vals else None), ("agree" if len(vals) == 2 else "single")
            elif q == "Q2 버전표기" and "날짜 스냅숏" in vals:
                rec["q"][q], rec["q_how"][q] = "날짜 스냅숏", "found"
            elif q == "Q3 실행시점" and ("연월" in vals or "연도만" in vals):
                rec["q"][q], rec["q_how"][q] = ("연월" if "연월" in vals else "연도만"), "found"
            elif "해당없음" in vals:
                other = [v for v in vals if v != "해당없음"][0]
                if rec["dependence"] == "의존":
                    rec["q"][q], rec["q_how"][q] = other, "dependence"
                elif rec["dependence"] == "비의존":
                    rec["q"][q], rec["q_how"][q] = "해당없음", "dependence"
                else:
                    rec["q"][q], rec["q_how"][q] = None, "follows_role"
            else:
                rec["q"][q], rec["q_how"][q] = None, "pending"
                rec["pending"].append((q, "", codes))
    return recs


def assign_third(recs, third):
    """Give each pending paper one of its two candidate third coders, alternating within each candidate pair."""
    load = Counter()
    out = {}
    for wid in sorted(recs, key=lambda w: recs[w]["num"] or 0):
        if not recs[wid]["pending"]:
            continue
        cands = [c for c in third.get(wid, "").split("/") if c]
        if not cands:
            cands = [c for c in CODERS if c not in recs[wid]["coders"]]
        pick = min(cands, key=lambda c: (load[c], c))  # the less loaded of the two candidates (units, then letter)
        out[wid] = pick
        load[pick] += len(recs[wid]["pending"])
    return out


def build(dir_, roles_only=False):
    data, sample, third = load(dir_)
    recs = resolve(data, sample)
    who = assign_third(recs, third)
    ADJ_DIR.mkdir(exist_ok=True)
    resolved, pending = [], []
    for wid, rec in recs.items():
        for mid, how in rec["role_how"].items():
            if how in ("fulltext", "found"):
                resolved.append({"num": rec["num"], "openalex_id": wid, "item": f"역할:{mid}", "rule": how, "final": rec["roles"][mid]})
        for q, how in rec["q_how"].items():
            if how in ("found", "dependence"):
                resolved.append({"num": rec["num"], "openalex_id": wid, "item": q, "rule": how, "final": rec["q"][q]})
        for item, mid, codes in rec["pending"]:
            a, b = rec["coders"][:2] if len(rec["coders"]) == 2 else (rec["coders"] + [None])[:2]
            pending.append({"num": rec["num"], "openalex_id": wid, "title": rec["title"], "item": item if item != "역할" else f"역할:{mid}", "mid": mid,
                            "code_1": codes.get(a) or "", "code_2": codes.get(b) or "", "coders": "".join(rec["coders"]), "third_coder": who.get(wid, ""),
                            "affects_dependence": "예" if (item == "역할" and rec["dependence"] is None) else "아니오", "note": rec["note"]})
    with open(ROOT / "coding" / "adjudication_main_resolved.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["num", "openalex_id", "item", "rule", "final"])
        w.writeheader()
        w.writerows(sorted(resolved, key=lambda r: (r["num"] or 0, r["item"])))
    with open(ROOT / "coding" / "adjudication_main_pending.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pending[0].keys()))
        w.writeheader()
        w.writerows(pending)
    # ---- workbooks
    for coder in CODERS:
        mine = [p for p in pending if p["third_coder"] == coder]
        if not mine:
            continue
        wb = Workbook()
        guide = wb.active
        guide.title = "안내"
        n_role = sum(1 for p in mine if p["item"].startswith("역할"))
        n_q = len(mine) - n_role
        lines = [f"본표본 코딩 제3코더 조정 - 코더 {coder} (코드북 v1.3 §6.5, 2026-10-10)", "",
                 "두 코더의 코드가 갈린 항목입니다. 조정자는 그 논문을 코딩하지 않은 사람입니다. 논문을 열어 보고 '결정' 열(노란 칸)에 두 코드 중 하나를 고르거나 다른 코드를 정하고, 근거를 '메모'에 한 줄 적어 주세요.",
                 "두 코더가 누구인지, 어느 쪽이 어떤 코드를 냈는지는 보이지 않습니다. 코드 ①·②의 순서에는 뜻이 없습니다.", "",
                 f"'역할' 탭 ({n_role}행): 매칭 ID를 저자들이 실행했는지(실행 / 인용·언급 / 못찾음 / 판단불가). '의존 여부에 영향'이 '예'인 행은 그 논문이 의존인지 비의존인지를 가르는 행입니다. "
                 "'비고'에 '두 코더 모두 전문을 열지 못함'이라고 적힌 논문은 원문을 다시 구해 코딩해 주시고, 구할 수 없으면 '판단불가'로 두어 주세요.",
                 ("" if roles_only else f"'Q1~Q3' 탭 ({n_q}행): 접근 경로(Q1)와 버전 표기(Q2). 코드북의 v1.3 규칙: temperature·max_tokens·SDK·호출 코드·코드 저장소가 있으면 '불명'이 아니라 'API'; "
                  "'혼합'은 같은 상용 모델을 웹UI와 API 두 경로로 부른 경우만(오픈 모델을 로컬로 함께 돌린 것은 '혼합'이 아니라 'API'); 날짜 스냅숏은 논문 어디에든 하나라도 있으면 '날짜 스냅숏'."), "",
                 "'모델 목록 ①·②'와 '메모 ①·②'는 두 코더가 적은 것으로, 참고용입니다. 다른 코더와 상의하지 않고, 저자에게 문의하지 않습니다. 파일명은 바꾸지 않습니다."]
        for l in lines:
            guide.append([l])
        for row in guide.iter_rows():
            for c in row:
                c.font = Font(name=FONT, bold=(c.row == 1))
                c.alignment = Alignment(wrap_text=True, vertical="top")
        guide.column_dimensions["A"].width = 120
        for tab, rows in (("역할", [p for p in mine if p["item"].startswith("역할")]), ("Q1~Q3", [p for p in mine if not p["item"].startswith("역할")])):
            if roles_only and tab != "역할":
                continue
            ws = wb.create_sheet(tab)
            head = ["번호", "openalex_id", "제목", "DOI", "OA 링크", "항목", "코드 ①", "코드 ②", "모델 목록 ①", "모델 목록 ②", "메모 ①", "메모 ②"]
            if tab == "역할":
                head.append("의존 여부에 영향")
            head += ["비고", "결정", "메모"]
            ws.append(head)
            dvs = {"역할": DataValidation(type="list", formula1='"' + ",".join(ROLE_CODES) + '"', allow_blank=True)}
            for q, codes in Q_CODES.items():
                dvs[q] = DataValidation(type="list", formula1='"' + ",".join(codes) + '"', allow_blank=True)
            for dv in dvs.values():
                ws.add_data_validation(dv)
            for p in rows:
                rec = recs[p["openalex_id"]]
                a, b = (rec["coders"] + [None, None])[:2]
                s = sample[p["openalex_id"]]
                row = [p["num"], p["openalex_id"], p["title"], s.get("doi", ""), s.get("oa_url", ""), p["item"], p["code_1"], p["code_2"],
                       rec["models"].get(a, ""), rec["models"].get(b, "") if b else "", rec["memo"].get(a, ""), rec["memo"].get(b, "") if b else ""]
                if tab == "역할":
                    row.append(p["affects_dependence"])
                row += [p["note"], None, None]
                ws.append(row)
                r = ws.max_row
                dec_col = head.index("결정") + 1
                dv = dvs["역할"] if p["item"].startswith("역할") else dvs[p["item"]]
                dv.add(ws.cell(r, dec_col))
            widths = {"번호": 6, "openalex_id": 13, "제목": 40, "DOI": 28, "OA 링크": 28, "항목": 20, "코드 ①": 11, "코드 ②": 11, "모델 목록 ①": 30, "모델 목록 ②": 30,
                      "메모 ①": 28, "메모 ②": 28, "의존 여부에 영향": 9, "비고": 22, "결정": 14, "메모": 30}
            for i, h in enumerate(head, 1):
                ws.column_dimensions[get_column_letter(i)].width = widths.get(h, 14)
                ws.cell(1, i).font = Font(name=FONT, bold=True)
                ws.cell(1, i).fill = GREY
            for row in ws.iter_rows(min_row=2):
                for c in row:
                    c.font = Font(name=FONT)
                    c.alignment = Alignment(wrap_text=True, vertical="top")
                    if head[c.column - 1] in ("결정", "메모"):
                        c.fill = YELLOW
            ws.freeze_panes = "D2"
        out = ADJ_DIR / f"halflife_adjudication_main_coder{coder}.xlsx"
        wb.save(out)
        print(f"coder {coder}: {len(mine)} units (역할 {n_role}, Q1~Q3 {n_q}{' not written' if roles_only else ''}) -> {out.relative_to(ROOT)}")
    hows = Counter(r["how"] for r in recs.values())
    print("papers by resolution:", dict(hows))
    print(f"resolved by rule: {len(resolved)} units -> coding/adjudication_main_resolved.csv; pending: {len(pending)} units "
          f"({sum(1 for p in pending if p['item'].startswith('역할'))} role, {sum(1 for p in pending if not p['item'].startswith('역할'))} Q) -> coding/adjudication_main_pending.csv")
    print("pending units by third coder:", dict(Counter(p["third_coder"] for p in pending)))


def collect(dir_):
    rows = []
    for f in sorted(glob.glob(str(Path(dir_) / "*adjudication*coder*.xlsx"))):
        coder = Path(f).stem.split("coder")[-1][:1]
        wb = load_workbook(f, read_only=True, data_only=True)
        for tab in ("역할", "Q1~Q3"):
            if tab not in wb.sheetnames:
                continue
            it = wb[tab].iter_rows(values_only=True)
            head = [str(h) if h is not None else "" for h in next(it)]
            col = {h: i for i, h in enumerate(head)}
            for r in it:
                if r[col["openalex_id"]] is None:
                    continue
                item = str(r[col["항목"]])
                decision = r[col["결정"]]
                rows.append({"num": r[col["번호"]], "openalex_id": str(r[col["openalex_id"]]), "item": item, "mid": item.split(":", 1)[1] if item.startswith("역할:") else "",
                             "decision": str(decision).strip() if decision not in (None, "") else "", "memo": r[col["메모"]] or "", "third_coder": coder})
    with open(DECISIONS, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["num", "openalex_id", "item", "mid", "decision", "memo", "third_coder"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} units read, {sum(1 for r in rows if r['decision'])} decided -> {DECISIONS.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "collect"])
    ap.add_argument("--dir", default=None)
    ap.add_argument("--roles-only", action="store_true", help="write only the 역할 tab (the Q1~Q3 clashes are resolved by the any-coder rules instead)")
    a = ap.parse_args()
    if a.mode == "build":
        build(a.dir or str(ROOT / "coding" / "results_main"), roles_only=a.roles_only)
    else:
        collect(a.dir or str(ROOT / "coding" / "results_adjudication"))


if __name__ == "__main__":
    main()
