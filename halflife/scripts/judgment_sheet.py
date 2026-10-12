"""Judgment workbook for the three-coder judgment of the re-execution results (ANALYSIS_PLAN section 1).

Sheets
  안내                 rule, how to fill, which cells to edit, an example row
  TierA_claims         one row per Tier A claim (data/tiera_claims.csv + cards): reported vs re-run value with its
                       interval, the automatic rule judgment, evidence path, human-check flag; judge columns
  PromptLevel_blind    one row per prompt-level result: the 86 pre-shutdown baselines and every successor run,
                       with the CONDITION HIDDEN behind a per-paper code (A..E in a seeded random order) so the
                       judge rates the value without knowing whether it came from the pinned model or a successor
  요약                 COUNTIF formulas over the judge columns (majority vote, agreement); master workbook only
The condition key is written separately to coding/judgment_key_v1.csv; judges must not open it.

python scripts/judgment_sheet.py                 -> coding/judgment_sheet_v1.xlsx (all three judge columns) + key
python scripts/judgment_sheet.py --judge A       -> coding/judgment/halflife_judgment_v1_judgeA.xlsx (one judge's
                                                    columns only; rows and codes identical to the master, checked
                                                    against the key)
No API calls.
"""
import argparse
import csv
import json
import random
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HALF = Path(__file__).resolve().parents[1]
OUT = HALF / "coding" / "judgment_sheet_v1.xlsx"
KEY = HALF / "coding" / "judgment_key_v1.csv"
JUDGE_DIR = HALF / "coding" / "judgment"
FONT = "Arial"
YELLOW = PatternFill("solid", fgColor="FFFF00")
GREY = PatternFill("solid", fgColor="EEEEEE")
JUDG = '"생존,부분 생존,사망,판정 불능"'
CONCL = '"핵심 주장 성립,부분 성립,불성립,판단 불가"'
VERSION = "v1.1, 2026-09-27"


def human_check_wids():
    p = HALF / "harness" / "cards" / "HUMAN_CHECKS.md"
    return set(re.findall(r"\| (W\d+)", p.read_text(encoding="utf-8"))) if p.exists() else set()


def style_header(ws, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(name=FONT, bold=True)
        cell.fill = GREY
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"


def finish(ws, widths, input_cols, nrows):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for r in range(2, nrows + 2):
        for c in range(1, len(widths) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(name=FONT)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        for c in input_cols:
            ws.cell(row=r, column=c).fill = YELLOW


def coder_head(coders):
    h = [f"판정 {c}" for c in coders] + [f"결론 수준 {c}" for c in coders] + [f"메모 {c}" for c in coders]
    return h + (["다수결", "일치"] if len(coders) == 3 else [])


def coder_widths(coders):
    k = len(coders)
    return [12] * k + [14] * k + [24] * k + ([12, 8] if k == 3 else [])


def add_coder_cols(ws, first_col, nrows, judg_list, concl_list, coders):
    """Judgment, conclusion and memo columns per judge; with three judges also majority and agreement formulas."""
    dv1 = DataValidation(type="list", formula1=judg_list, allow_blank=True)
    dv2 = DataValidation(type="list", formula1=concl_list, allow_blank=True)
    ws.add_data_validation(dv1)
    ws.add_data_validation(dv2)
    k = len(coders)
    j = [get_column_letter(first_col + i) for i in range(k)]
    kk = [get_column_letter(first_col + k + i) for i in range(k)]
    for r in range(2, nrows + 2):
        for col in j:
            dv1.add(f"{col}{r}")
        for col in kk:
            dv2.add(f"{col}{r}")
        if k == 3:
            a, b, c = (f"{j[0]}{r}", f"{j[1]}{r}", f"{j[2]}{r}")
            maj = ws.cell(row=r, column=first_col + 9)
            maj.value = (f'=IF(COUNTA({a}:{c})<3,"",IF(AND({a}={b},{b}={c}),{a},IF({a}={b},{a},IF({a}={c},{a},IF({b}={c},{b},"판정 불능")))))')
            agr = ws.cell(row=r, column=first_col + 10)
            agr.value = f'=IF(COUNTA({a}:{c})<3,"",IF(AND({a}={b},{b}={c}),"3/3",IF(OR({a}={b},{a}={c},{b}={c}),"2/3","0/3")))'
    return list(range(first_col, first_col + 3 * k))


def tier_a(wb, hc, coders):
    ws = wb.active
    ws.title = "TierA_claims"
    cards = {}
    for p in (HALF / "harness" / "cards").glob("*.json"):
        try:
            c = json.load(open(p, encoding="utf-8"))
            cards[c["card_id"]] = c
        except Exception:
            pass
    rows = list(csv.DictReader(open(HALF / "data" / "tiera_claims.csv", encoding="utf-8-sig")))
    head = ["번호", "카드", "논문", "주장(지표)", "원 논문 값", "재실행 값", "95% 구간 하한", "95% 구간 상한", "규칙(척도)",
            "자동 판정(논문 단위 가안)", "메모(자동)", "근거 파일", "사람 확인 항목"] + coder_head(coders)
    ws.append(head)
    for i, r in enumerate(rows, 1):
        card = cards.get(r["wid"], {})
        ws.append([i, r["wid"], (card.get("title") or "")[:90], r["label"],
                   float(r["original"]) if r["original"] not in ("", None) else None,
                   float(r["rerun"]) if r["rerun"] not in ("", None) else None,
                   float(r["ci_lo"]) if r["ci_lo"] else None, float(r["ci_hi"]) if r["ci_hi"] else None,
                   r["rule"], r["judgment"], r["note"], f"runs/{r['wid']}/run_meta.json",
                   "예 (harness/cards/HUMAN_CHECKS.md)" if r["wid"] in hc else ""])
    n = len(rows)
    inputs = add_coder_cols(ws, 14, n, JUDG, CONCL, coders)
    style_header(ws, len(head))
    finish(ws, [5, 13, 40, 44, 11, 11, 11, 11, 9, 20, 40, 30, 14] + coder_widths(coders), inputs, n)
    return n


def prompt_level(wb, coders, write_key):
    ws = wb.create_sheet("PromptLevel_blind")
    summ = json.load(open(HALF / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8"))
    p3 = list(csv.DictReader(open(HALF / "data" / "p3_summary.csv", encoding="utf-8-sig")))
    prep = {}
    for r in summ:
        p = HALF / "runs" / "tierb" / r["wid"] / "prepare.json"
        prep[r["wid"]] = bool(json.load(open(p, encoding="utf-8")).get("subset_note")) if p.exists() else False
    per = {}
    for r in summ:
        per.setdefault(r["wid"], {"title": r["title"], "orig": r["orig"], "metric": r["metric"], "conds": []})
        per[r["wid"]]["conds"].append({"arm": "baseline", "value": r["rerun"], "ci": r["ci"], "n": r["n"], "unparsed": r["unparsed"],
                                       "subset": prep[r["wid"]], "auto": r["class"], "seeds": r["seeds"], "low": r.get("low_precision")})
    for r in p3:
        if r["wid"] not in per:
            continue
        ci = [float(r["ci_lo"]), float(r["ci_hi"])] if r["ci_lo"] not in ("", None) else None
        per[r["wid"]]["conds"].append({"arm": r["arm"], "value": float(r["arm_value"]) if r["arm_value"] not in ("", None) else None, "ci": ci,
                                       "n": r["n_items"], "unparsed": r["unparsed"], "subset": bool(r["subset_note"]), "auto": r["class_vs_original"],
                                       "seeds": 1, "low": None})
    rng = random.Random(20260920)
    # no seed count in the sheet: baselines ran 3 seeds and successors 1, so the column would give the condition away
    head = ["번호", "논문 ID", "논문", "지표", "원 논문 값", "조건 부호", "재실행 값", "95% 구간 하한", "95% 구간 상한", "문항 수",
            "파싱 실패 수", "비용 상한 부분집합", "자동 가안(값 수준)", "저정밀(구간 반폭>10점)"] + coder_head(coders)
    ws.append(head)
    key_rows, i = [], 0
    for wid in sorted(per):
        d = per[wid]
        assert len(d["conds"]) <= 5, wid
        codes = list("ABCDE")[:len(d["conds"])]
        order = list(range(len(d["conds"])))
        rng.shuffle(order)
        for code, idx in zip(codes, order):
            c = d["conds"][idx]
            i += 1
            ci = c["ci"] if c["ci"] and c["ci"][0] is not None else [None, None]
            ws.append([i, wid, d["title"], d["metric"], d["orig"], code, c["value"], ci[0], ci[1], c["n"], c["unparsed"],
                       "예" if c["subset"] else "", c["auto"], "예" if c.get("low") else ""])
            key_rows.append({"row": str(i), "wid": wid, "code": code, "condition": c["arm"]})
    n = i
    inputs = add_coder_cols(ws, 15, n, JUDG, CONCL, coders)
    style_header(ws, len(head))
    finish(ws, [5, 13, 40, 14, 11, 8, 11, 11, 11, 8, 8, 8, 12, 10] + coder_widths(coders), inputs, n)
    if write_key:
        with open(KEY, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["row", "wid", "code", "condition"])
            w.writeheader()
            w.writerows(key_rows)
    else:
        existing = list(csv.DictReader(open(KEY, encoding="utf-8-sig")))
        assert existing == key_rows, "the judge copy would not match coding/judgment_key_v1.csv; regenerate the master first"
    return n


def summary(wb, n_a, n_b):
    ws = wb.create_sheet("요약")
    ws.append(["집계 (수식)", "TierA_claims", "PromptLevel_blind"])
    items = [("코딩된 행 수 (세 명 모두)", 'COUNTIF({s}!{c}2:{c}{n},"<>")'),
             ("다수결 생존", 'COUNTIF({s}!{c}2:{c}{n},"생존")'), ("다수결 부분 생존", 'COUNTIF({s}!{c}2:{c}{n},"부분 생존")'),
             ("다수결 사망", 'COUNTIF({s}!{c}2:{c}{n},"사망")'), ("다수결 판정 불능", 'COUNTIF({s}!{c}2:{c}{n},"판정 불능")'),
             ("3/3 일치", 'COUNTIF({s}!{d}2:{d}{n},"3/3")'), ("2/3 일치", 'COUNTIF({s}!{d}2:{d}{n},"2/3")'), ("0/3 일치", 'COUNTIF({s}!{d}2:{d}{n},"0/3")')]
    for label, f in items:
        ws.append([label, "=" + f.format(s="TierA_claims", c="W", d="X", n=n_a + 1), "=" + f.format(s="PromptLevel_blind", c="X", d="Y", n=n_b + 1)])
    ws.append([])
    ws.append(["세 판정자의 파일을 합치고 자동 가안과 교차표를 만드는 것은 scripts/judgment_merge.py다. 위 수식은 채워진 행만 센다."])
    for row in ws.iter_rows():
        for cell in row:
            cell.font = Font(name=FONT, bold=(cell.row == 1))
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 18


def guide(wb, n_a, n_b, judge):
    ws = wb.create_sheet("안내", 0)
    who = f"이 파일은 판정자 {judge}용입니다. " if judge else ""
    lines = [
        f"재실행 결과 3인 판정 시트 ({VERSION})" + (f" - 판정자 {judge}" if judge else ""),
        "",
        "규칙 (ANALYSIS_PLAN 1절, 2026-09-02 고정): 생존 = 효과 방향 동일, 원 논문이 검정을 보고했으면 유의성 유지, 효과크기의 부호와 크기급 유지. "
        "부분 생존 = 방향은 같으나 유의성 또는 크기급이 달라짐. 사망 = 방향이 뒤집히거나 핵심 주장이 성립하지 않음. 판정 불능 = 근거가 모자라 판단할 수 없음.",
        "결론 수준 = 그 값이 뒷받침하던 논문의 문장이 지금도 성립하는가 (핵심 주장 성립 / 부분 성립 / 불성립 / 판단 불가).",
        "",
        who + "채우는 칸은 노란색뿐입니다: 판정, 결론 수준, 메모. 다른 판정자와 상의하지 않고 채웁니다. 판정이 어려우면 메모에 이유를 적고 '판정 불능'을 고릅니다."
        + ("" if judge else " 다수결과 일치 열은 수식이라 손대지 않습니다."),
        "회색 열은 근거입니다. 원 논문 값, 재실행 값과 95% 구간, 문항 수, 파싱 실패 수, 비용 상한 부분집합 여부, 자동 가안. 자동 가안은 참고용이며 판정을 대신하지 않습니다. "
        "자동 가안과 다르게 판정해도 됩니다. 그것이 이 작업의 목적입니다.",
        "판단 기준은 값과 구간입니다. 원 논문 값이 재실행의 95% 구간 안이거나 차이가 2점 이내면 대체로 생존, 5점 이내면 부분 생존, 그 밖이면 사망으로 읽되, "
        "지표의 성격(비율, 상관, 점수)과 논문이 그 값으로 무엇을 주장했는지를 함께 봅니다.",
        "",
        f"TierA_claims: 저장소 기반 재실행 논문의 주장 {n_a}건. 근거 파일 열의 run_meta.json에 실행 조건과 관찰된 마찰이 있습니다. '사람 확인 항목'이 '예'인 논문은 harness/cards/HUMAN_CHECKS.md의 결정이 먼저 필요합니다.",
        f"PromptLevel_blind: 프롬프트 수준 결과 {n_b}행(86편). 같은 논문의 행들은 사망 전 고정 모델 실행과 후속 모델 실행이 섞여 있고, 어느 것이 어느 조건인지는 조건 부호(A~E)로 가려져 있습니다. "
        "조건을 추측하지 말고 행마다 값만 보고 판정합니다.",
        "열쇠는 coding/judgment_key_v1.csv에 있으며 판정이 끝나기 전에는 열지 않습니다 (계획의 조건 가림 코딩).",
        "",
        "예시 행 (형식만 보이기 위한 가상의 값입니다. 데이터 시트에는 들어 있지 않습니다):",
    ]
    for l in lines:
        ws.append([l])
    ex_judge = judge or "A"
    ws.append(["번호", "논문", "원 논문 값", "재실행 값", "95% 구간", f"판정 {ex_judge}", f"결론 수준 {ex_judge}", f"메모 {ex_judge}"])
    ws.append([0, "(예시) 어떤 벤치마크 논문", 62.0, 60.5, "[57.9, 63.1]", "생존", "핵심 주장 성립", "구간 안, 방향 동일"])
    for row in ws.iter_rows():
        for cell in row:
            cell.font = Font(name=FONT, bold=(cell.row in (1, len(lines) + 1)))
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for c in ("F", "G", "H"):
        ws[f"{c}{len(lines) + 2}"].fill = YELLOW
    ws.column_dimensions["A"].width = 120
    for c in "BCDEFGH":
        ws.column_dimensions[c].width = 16


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", choices=["A", "B", "C", "all"], default="all")
    a = ap.parse_args()
    OUT.parent.mkdir(exist_ok=True)
    coders = ("A", "B", "C") if a.judge == "all" else (a.judge,)
    wb = Workbook()
    hc = human_check_wids()
    n_a = tier_a(wb, hc, coders)
    n_b = prompt_level(wb, coders, write_key=(a.judge == "all"))
    if a.judge == "all":
        summary(wb, n_a, n_b)
        guide(wb, n_a, n_b, None)
        wb.save(OUT)
        print(f"TierA claims {n_a}, prompt-level rows {n_b} -> {OUT.relative_to(HALF)}; key -> {KEY.relative_to(HALF)}")
    else:
        guide(wb, n_a, n_b, a.judge)
        JUDGE_DIR.mkdir(exist_ok=True)
        out = JUDGE_DIR / f"halflife_judgment_v1_judge{a.judge}.xlsx"
        wb.save(out)
        print(f"TierA claims {n_a}, prompt-level rows {n_b} -> {out.relative_to(HALF)} (judge {a.judge}, key verified)")


if __name__ == "__main__":
    main()
