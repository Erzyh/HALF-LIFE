"""Current results overview, regenerated from the data files: runs/RESULTS.md.

Sections: headline counts; Tier A (13 papers, 46 claims) from data/tiera_claims.csv and runs/<wid>/run_meta.json;
Tier B (61 papers) from runs/tierb/batch1_tierb_summary.json; successor comparison from data/p3_summary.csv;
the two prompt variants from runs/tierb/<wid>v2/result.json; spend from budget_log.csv. No API calls.

  python scripts/results_report.py
"""
import csv, json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_FILE = {"T1": "T1_bia_codegen.json"}
CLASS_ORDER = {"편차": 0, "확인 필요": 1, "해당없음": 2, "근접": 3, "재현": 4}


def fmt(v, nd=3):
    if v is None or v == "":
        return "-"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    return f"{x:.{nd}f}".rstrip("0").rstrip(".") if abs(x) < 1000 else f"{x:,.0f}"


def ci(lo, hi, nd=3):
    return f"[{fmt(lo, nd)}, {fmt(hi, nd)}]" if lo not in (None, "") and hi not in (None, "") else ""


def is_robustness(r):
    """Budget rows of the robustness runs: the seed-variance repeat (arm=<condition>_rep) and the BF16 check (2026-09-28), the wording
    check (arm=para_p1/p2) and the successor condition for repository-based papers (arm tierA_successor) (2026-10-01)."""
    note = r.get("note") or ""
    return ("_rep" in note or "open70b_bf16" in note or "para_p" in note or "format_f" in note or "temp1" in note
            or r.get("arm") == "tierA_successor")


def budget():
    rows = list(csv.DictReader(open(ROOT / "budget_log.csv", encoding="utf-8")))
    per = defaultdict(lambda: {"cost": 0.0, "calls": 0, "models": set()})
    for r in rows:
        if is_robustness(r):          # the seed-variance repeat and the BF16 check are accounted separately
            continue
        k = r["card"]
        per[k]["cost"] += float(r["cost_usd"] or 0)
        per[k]["calls"] += int(r["calls"]) if (r["calls"] or "").strip().isdigit() else 0
        if r["model"]:
            per[k]["models"].add(r["model"])
    return rows, per


JUDGED_PAPERS = {}
if (ROOT / "data" / "judgment_tiera_papers.csv").exists():
    JUDGED_PAPERS = {r["wid"]: r for r in csv.DictReader(open(ROOT / "data" / "judgment_tiera_papers.csv", encoding="utf-8-sig"))}


def tier_a(per):
    claims = list(csv.DictReader(open(ROOT / "data" / "tiera_claims.csv", encoding="utf-8-sig")))
    by = defaultdict(list)
    for r in claims:
        by[r["wid"]].append(r)
    papers = []
    for wid, cl in by.items():
        meta = json.load(open(ROOT / "runs" / wid / "run_meta.json", encoding="utf-8"))
        card = json.load(open(ROOT / "harness" / "cards" / CARD_FILE.get(wid, f"{wid}.json"), encoding="utf-8"))
        judgment = JUDGED_PAPERS.get(wid, {}).get("judged") or meta["results"].get("judgment") or cl[0]["judgment"]
        models = sorted(per[wid]["models"]) if per[wid]["models"] else sorted({a.get("model") for a in (card.get("arms") or {}).values() if isinstance(a, dict) and a.get("model")})
        papers.append({"wid": wid, "title": card.get("title", "")[:60], "judgment": judgment, "models": ", ".join(models)[:60],
                       "calls": per[wid]["calls"], "cost": per[wid]["cost"], "claims": cl})
    return papers


def tier_b():
    rows = json.load(open(ROOT / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8"))
    rows.sort(key=lambda r: (CLASS_ORDER.get(r["class"], 9), -(abs(r["delta_pts"]) if isinstance(r.get("delta_pts"), (int, float)) else 0)))
    return rows


def successors():
    rows = list(csv.DictReader(open(ROOT / "data" / "p3_summary.csv", encoding="utf-8-sig")))
    by = defaultdict(dict)
    for r in rows:
        by[r["wid"]][r["arm"]] = r
    return rows, by


def variants():
    out = []
    for wid, label in (("W4416036577", "루머 탐지: base 프롬프트 + 소스 도메인 예시 4개"), ("W4399912745", "ALiiCE: 코드 공개본의 프롬프트 형식")):
        base = json.load(open(ROOT / "runs" / "tierb" / wid / "result.json", encoding="utf-8"))
        var = json.load(open(ROOT / "runs" / "tierb" / f"{wid}v2" / "result.json", encoding="utf-8"))
        def val(res):
            c = res.get("comparison") or {}
            return c.get("reexecution_scaled", (res["reexecution"] or {}).get("mean_over_seeds"))
        s0 = (var["reexecution"].get("per_seed") or {}).get("0") or {}
        scale = (var.get("comparison") or {}).get("scale_applied") or 1.0
        c95 = s0.get("ci95") or [None, None]
        out.append({"label": label, "orig": var["original_value"], "base": val(base), "var": val(var),
                    "ci": ci(c95[0] * scale if c95[0] is not None else None, c95[1] * scale if c95[1] is not None else None, 1),
                    "n": s0.get("n"), "seeds": len(var["reexecution"].get("per_seed") or {})})
    return out


def main():
    rows, per = budget()
    ta = tier_a(per)
    tb = tier_b()
    p3rows, p3 = successors()
    var = variants()
    L = []
    w = L.append
    data_date = max(r[next(iter(r))] for r in rows)            # first column of budget_log.csv: date of the last recorded spend
    w(f"# 재실행 결과 현황 (지출 기록 {data_date} 기준, 자동 생성)")
    w("")
    w("`python scripts/results_report.py`가 데이터 파일에서 다시 만든다. 분류는 공저자 3인 판정의 다수결(data/judgment_final.csv, 2026-10-11)이고 자동 가안은 class_provisional 열에 남아 있다. "
      "그림·표의 출처와 해석은 `PAPER_OUTLINE.md`와 `SUPPLEMENTARY.md`, 편차 원인은 `SUPPLEMENTARY_TABLES.md` 표 S4에 있다.")
    w("")
    # ---- headline
    ja = Counter(p["judgment"].split(" ")[0] for p in ta)
    jb = Counter(r["class"] for r in tb)
    vend = [r for r in p3rows if r["arm"] == "vendor" and r["class_vs_original"] != "해당없음"]
    g41 = [r for r in p3rows if r["arm"] == "gpt41"]
    op = [r for r in p3rows if r["arm"] == "open70b" and r["class_vs_original"] != "해당없음"]
    gf = [r for r in p3rows if r["arm"] == "gemini_flash" and r["class_vs_original"] != "해당없음"]
    cv, cg, co = Counter(r["class_vs_original"] for r in vend), Counter(r["class_vs_original"] for r in g41), Counter(r["class_vs_original"] for r in op)
    cf = Counter(r["class_vs_original"] for r in gf)
    cost_r = sum(float(r["cost_usd"]) for r in rows if is_robustness(r))
    total_spend = float(rows[-1]["cumulative_usd"])                      # last row of the full log
    cost_d = sum(float(r["cost_usd"]) for r in rows if "drift_ctrl" in (r.get("note") or ""))
    rows = [r for r in rows if not is_robustness(r) and "drift_ctrl" not in (r.get("note") or "")]
    cost_o = sum(float(r["cost_usd"]) for r in rows if r["model"].startswith(("meta-llama", "Qwen")))
    cost_f = sum(float(r["cost_usd"]) for r in rows if r["model"].startswith("gemini"))
    arm_rows_all = lambda arm: [r for r in p3rows if r["arm"] == arm]
    cost_a = sum(float(r["cost_usd"]) for r in rows if r["arm"] in ("tierA", "baseline_alive"))
    cost_b = sum(float(r["cost_usd"]) for r in rows if r["arm"] == "tierb" and not r["card"].endswith("v2"))
    cost_v = sum(float(r["cost_usd"]) for r in rows if r["card"].endswith("v2"))
    cost_p = sum(float(r["cost_usd"]) for r in rows if r["arm"] == "tierb_p3") - cost_o - cost_f   # OpenAI vendor + gpt-4.1 arms only
    w("## 한눈에")
    w("")
    w("| 항목 | 결과 | 비용 |")
    w("|---|---|---|")
    w(f"| Tier A (저장소 기반 전체 절차, {len(ta)}편) | " + ", ".join(f"{k} {v}" for k, v in ja.items()) + f" | ${cost_a:,.2f} |")
    w(f"| Tier B (프롬프트 수준, 논문당 사전 지정 수치 1개, {len(tb)}편) | " + ", ".join(f"{k} {jb[k]}" for k in ("재현", "근접", "편차", "확인 필요") if jb.get(k)) + f" | ${cost_b:,.2f} |")
    w(f"| 후속 전환, 벤더 지정 대체 모델 (실행 {len(arm_rows_all('vendor'))}, 채점 가능 {sum(1 for r in vend if r['class_vs_original'] != '확인 필요')}편) | " + ", ".join(f"{k} {cv[k]}" for k in ("재현", "근접", "편차", "확인 필요") if cv.get(k)) + f" | ${cost_p:,.2f} (gpt-4.1 포함, OpenAI) |")
    w(f"| 후속 전환, gpt-4.1 (실행 {len(g41)}, 채점 가능 {sum(1 for r in g41 if r['class_vs_original'] != '확인 필요')}편) | " + ", ".join(f"{k} {cg[k]}" for k in ("재현", "근접", "편차", "확인 필요") if cg.get(k)) + " | 위에 포함 |")
    if op:
        w(f"| 후속 전환, 공개 가중치 Llama 3.3 70B (실행 {len(arm_rows_all('open70b'))}, 채점 가능 {sum(1 for r in op if r['class_vs_original'] != '확인 필요')}편) | " + ", ".join(f"{k} {co[k]}" for k in ("재현", "근접", "편차", "확인 필요") if co.get(k)) + f" | ${cost_o:,.2f} (Together) |")
    if gf:
        w(f"| 후속 전환, 타사 폐쇄형 API Gemini 3.8 Flash (실행 {len(arm_rows_all('gemini_flash'))}, 채점 가능 {sum(1 for r in gf if r['class_vs_original'] != '확인 필요')}편) | " + ", ".join(f"{k} {cf[k]}" for k in ("재현", "근접", "편차", "확인 필요") if cf.get(k)) + f" | ${cost_f:,.2f} (Google) |")
    w(f"| 프롬프트 변형 2건 | 아래 절 | ${cost_v:,.2f} |")
    w(f"| 강건성 실행 (네 조건 반복 20편씩, BF16 점검 12편, 문구 점검 18편×2, 저장소 기반 후속 5편, 형식 맞춤 3편×2, 온도 점검 4편; 표 S27~S33, S38; 임계값 스윕 표 S39; 트리아지 교차 판정 60건 표 S40~S41, US$2.57) | 호출 간 범위 중앙값 0.16~0.48점, BF16에서 편차 6건 유지; 바꿔 쓴 지시문 하나당 이동 중앙값 0.96점(36건 중 5점 초과 7건), 저장소 기반 20개 주장 중 편차 11건(이동 중앙값 8.3점); 형식 맞춤 뒤에도 보고값 복원 0/3; temperature 1.0에서 분류 변화 1/4 | ${cost_r:,.2f} |")
    w(f"| 같은 스냅숏 대조군 (20편, 4~15일 뒤 같은 모델) | 표 S20 | ${cost_d:,.2f} |")
    w(f"| 지출 누계 | | ${total_spend:,.2f} |")
    w("")
    ta_ids = {p["wid"] for p in ta}
    tb_ids = {r["wid"] for r in tb}
    both = sorted(ta_ids & tb_ids)
    w(f"단위는 논문이다. 사망 전 재실행은 고유 논문 {len(ta_ids | tb_ids)}편이고, 그중 {len(both)}편은 두 절차로 모두 돌렸다(같은 주장을 저장소 기반과 프롬프트 수준으로 각각 재실행한 타당성 점검: "
      + ", ".join(both) + f"). Tier A의 주장 단위 {sum(len(p['claims']) for p in ta)}건은 그림 3(forest plot)의 점 개수이며 아래 주장별 표에 있다.")
    w("")
    # ---- analysis-set ledger for the successor comparison
    def arm_rows(arm):
        return [r for r in p3rows if r["arm"] == arm]
    def ledger(arm):
        rs = arm_rows(arm)
        run = len(rs)
        transferable = sum(1 for r in rs if r["class_vs_original"] != "해당없음")
        scorable = sum(1 for r in rs if r["class_vs_original"] not in ("해당없음", "확인 필요"))
        moved = sum(1 for r in rs if r["class_vs_original"] == "편차")
        return run, transferable, scorable, moved
    gpt4_class = sum(1 for r in tb if r["model"] in ("gpt-4-turbo-2024-04-09", "gpt-4o-2024-05-13"))
    V, G, O, F = ledger("vendor"), ledger("gpt41"), ledger("open70b"), ledger("gemini_flash")
    unsc = {arm: sum(1 for r in arm_rows(arm) if r["class_vs_original"] == "확인 필요") for arm in ("vendor", "gpt41", "open70b", "gemini_flash")}
    fcol = lambda k, pct=False: (f" {F[k]} ({100 * F[k] / F[2]:.0f}%) |" if pct else f" {F[k]} |") if F[0] else ""
    fhead = " Gemini 3.8 Flash |" if F[0] else ""
    w("## 분석 집합 장부 (후속 전환)")
    w("")
    w("각 조건의 분모가 어떻게 줄어드는지와 그 이유. 본문과 그림 5, 표 S9는 이 이름(후보·실행·전환 가능·채점 가능)을 그대로 쓴다.")
    w("")
    w("| 분석 집합 | 벤더 지정 대체 모델 | gpt-4.1 | 공개 가중치 Llama 3.3 70B |" + fhead + " 빠진 이유 |")
    w("|---|---|---|---|" + ("---|" if F[0] else "") + "---|")
    w(f"| 후보 | {len(tb)} | {gpt4_class} | {len(tb)} |" + (f" {len(tb)} |" if F[0] else "") + " gpt-4.1 조건은 원 모델이 GPT-4급(gpt-4-turbo, gpt-4o)인 논문만 대상 |")
    w(f"| 실행 | {V[0]} | {G[0]} | {O[0]} |" + fcol(0) + " 벤더: 1차 61편 중 호출 수가 적은 49편과 2차 25편 전부, 12편은 후속 모델 가격이 편당 $25~125라 미실행. gpt-4.1: 벤더 조건과 짝을 이룬 논문 우선, 채용 논문 1편은 계정 정지로 중단. 공개 가중치: 제3자 계정 정책 위험으로 편향 감사 6편과 OR-Bench 제외; OpenAI 2단계 판정이 필요한 2편은 계정 복구 뒤(9/21) 판정 단계를 돌려 채움. Gemini: 공개 가중치 조건과 같은 67편 |")
    w(f"| 전환 가능 | {V[1]} | {G[1]} | {O[1]} |" + fcol(1) + " 자기 식별 과제 1편은 어느 후속 모델에도 정답 보기가 없어 전환이 성립하지 않음 |")
    w(f"| 채점 가능 | {V[2]} | {G[2]} | {O[2]} |" + fcol(2) + f" 응답의 절반 넘게 논문 파서가 요구한 형식이 아님(벤더 {unsc['vendor']}, gpt-4.1 {unsc['gpt41']}, 공개 {unsc['open70b']}" + (f", Gemini {unsc['gemini_flash']}" if F[0] else "") + ") |")
    w(f"| 5점 넘게 이동 | {V[3]} ({100 * V[3] / V[2]:.0f}%) | {G[3]} ({100 * G[3] / G[2]:.0f}%) | {O[3]} ({100 * O[3] / O[2]:.0f}%) |" + fcol(3, True) + " 분모는 채점 가능 |")
    w("")
    # ---- Tier A
    w("## Tier A: 저장소 기반 프로토콜 전체 재실행")
    w("")
    w("| 논문 | 모델 | 호출 | 비용 | 판정 |")
    w("|---|---|---|---|---|")
    for p in sorted(ta, key=lambda p: p["judgment"]):
        w(f"| {p['title']} | {p['models']} | {p['calls']:,} | ${p['cost']:.2f} | {p['judgment']} |")
    w("")
    w("주장별 값 (원 논문 → 재실행 [95% 구간]; 규칙 x100은 비율을 백분율로 읽음):")
    w("")
    w("| 논문 ID | 주장 | 원 논문 | 재실행 | 메모 |")
    w("|---|---|---|---|---|")
    for p in ta:
        for c in p["claims"]:
            w(f"| {p['wid']} | {c['label']} | {fmt(c['original'], 4)} | {fmt(c['rerun'], 4)} {ci(c['ci_lo'], c['ci_hi'])} | {c.get('note', '')} |")
    w("")
    # ---- Tier B
    w("## Tier B: 프롬프트 수준 재실행")
    w("")
    w("자동 가안의 분류 규칙: 재현 = 원 값이 재실행 95% 구간 안이거나 차이 2점 이내, 근접 = 5점 이내, 편차 = 그 이상, 확인 필요 = 채점 규칙 미보고. 비율 지표는 백분율 점수로 읽는다.")
    w("")
    w("| 논문 ID | 논문 | 모델 | 지표 | 원 값 | 재실행 | Δ점 | 문항 | 분류 | 메모 |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for r in tb:
        c = r.get("ci")
        w(f"| {r['wid']} | {r['title'][:44]} | {r['model']} | {r['metric']} | {fmt(r['orig'])} | {fmt(r['rerun'])} {ci(c[0], c[1]) if c else ''} | "
          f"{fmt(r.get('delta_pts'), 1)} | {r.get('n') or '-'} | {r['class']} | {(r.get('note') or '')[:90]} |")
    w("")
    # ---- successors
    w("## 후속 모델 전환")
    w("")
    w("같은 문항·프롬프트·채점으로 모델만 바꿨다. 벤더 지정 대체 모델은 OpenAI 단종 페이지의 대체 모델(gpt-5.6-sol/terra/luna, 기본 설정), gpt-4.1은 GPT-4 계열의 비추론 후속. 문항당 1회 실행. 분류는 원 보고값 기준이고 괄호는 사망 전 베이스라인 기준.")
    w("")
    w("| 논문 ID | 논문 | 원 값 | 베이스라인 | 벤더 지정 대체 모델 | gpt-4.1 | 공개 가중치 Llama 3.3 70B |" + (" Gemini 3.8 Flash |" if F[0] else ""))
    w("|---|---|---|---|---|---|---|" + ("---|" if F[0] else ""))
    def cell(r):
        if not r:
            return "-"
        return f"{fmt(r['arm_value'])} {ci(r['ci_lo'], r['ci_hi'])} {r['class_vs_original']} ({r['class_vs_baseline']})" + (f" · {r['note'][:50]}" if r.get("note") else "")
    for wid, d in sorted(p3.items(), key=lambda kv: CLASS_ORDER.get((kv[1].get("vendor") or kv[1].get("gpt41") or kv[1].get("open70b") or kv[1].get("gemini_flash"))["class_vs_original"], 9)):
        r0 = d.get("vendor") or d.get("gpt41") or d.get("open70b") or d.get("gemini_flash")
        w(f"| {wid} | {r0['title'][:40]} | {fmt(r0['original'])} | {fmt(r0['baseline'])} | {cell(d.get('vendor'))} | {cell(d.get('gpt41'))} | {cell(d.get('open70b'))} |" + (f" {cell(d.get('gemini_flash'))} |" if F[0] else ""))
    w("")
    # ---- variants
    w("## 프롬프트 변형 (트리아지 가설 검증, 사망 전 모델)")
    w("")
    w("| 변형 | 원 값 | 원 프롬프트 재실행 | 변형 재실행 [95% 구간] | 문항 × 시드 |")
    w("|---|---|---|---|---|")
    for v in var:
        w(f"| {v['label']} | {fmt(v['orig'])} | {fmt(v['base'])} | {fmt(v['var'])} {v['ci']} | {v['n']} × {v['seeds']} |")
    w("")
    # ---- robustness checks (all from data/*.csv; no API calls)
    def read_csv(name):
        q = ROOT / "data" / name
        return list(csv.DictReader(open(q, encoding="utf-8-sig"))) if q.exists() else []
    def num(x, nd=2):
        try:
            return f"{float(x):.{nd}f}"
        except (TypeError, ValueError):
            return "-"
    w("## 강건성 점검")
    w("")
    w("후속 비교의 잡음 바닥과 경계를 재는 다섯 가지 점검. 값은 모두 논문 척도의 점수이고 분류는 프롬프트 수준 규칙이다. 자세한 표는 S20, S26~S32.")
    w("")
    dc = read_csv("drift_control.csv")
    if dc:
        d = sorted(abs(float(r["delta_vs_baseline_seed0_pts"])) for r in dc if r.get("delta_vs_baseline_seed0_pts") not in (None, ""))
        dev = sum(1 for r in dc if r.get("class_vs_baseline_seed0") == "편차")
        w(f"- **같은 스냅숏 대조군 (표 S20)**: {len(dc)}편을 생전 문항·요청 본문 그대로 같은 고정 모델에 4~15일 뒤 1회 재실행. 생전 시드 0 값 대비 편차 {dev}/{len(dc)}, "
          f"|Δ| 중앙값 {num(d[len(d) // 2]) if d else '-'}점, 최대 {num(max(d)) if d else '-'}점.")
    rep = read_csv("p3_repeat_summary.csv")
    if rep:
        w("- **씨앗 분산 반복 (표 S27·S28)**: 조건마다 씨앗 고정 무작위 20편에 같은 요청 본문으로 두 번 더 호출. 호출 간 범위 중앙값 "
          + ", ".join(f"{r['condition']} {num(r['range_median_pts'])}점(5점 초과 {r['papers_range_over_5']}편, 분류 안정 {num(r['class_stable_share_pct'], 0)}%)" for r in rep) + ".")
    bf = read_csv("p3_bf16_summary.csv")
    if bf:
        b = bf[0]
        w(f"- **BF16 점검 (표 S29)**: 공개 가중치 조건 {b['papers_compared']}편을 전용 bfloat16 배포에 같은 요청으로 재실행. FP8 대비 |차이| 중앙값 {num(b['abs_diff_median_pts'])}점, "
          f"편차 {b['fp8_deviated']}건 모두 유지(분류 변화 {b['class_changes']}건), 파싱 실패 {b['fp8_unparsed_total']}→{b['bf16_unparsed_total']}/{b['items_total']}.")
    pa = read_csv("p3_paraphrase_summary.csv")
    if pa:
        a = pa[0]
        w(f"- **문구 점검 (표 S30·S31)**: 같은 스냅숏 대조군 중 고정 지시문이 있는 {a['papers_complete']}편의 지시문을 두 가지로 바꿔 써서 같은 고정 모델에 1회씩. "
          f"바꿔 쓴 지시문 하나당 |Δ| 중앙값 {num(a['single_rewording_abs_shift_median_pts'])}점(상위 사분위 {num(a['single_rewording_abs_shift_p75_pts'])}, 최대 {num(a['single_rewording_abs_shift_max_pts'])}; "
          f"{a['rewordings']}건 중 5점 초과 {a['rewordings_over_5']}건), 세 문구의 범위 중앙값 {num(a['wording_range_median_pts'])}점(5점 초과 {a['papers_wording_over_5']}편, 분류 안정 {num(a['class_stable_share_pct'], 0)}%), "
          f"편차 여부가 문구에 따라 바뀐 논문 {a['papers_deviated_status_changes_with_wording']}편. 같은 논문의 날짜 차이 중앙값 {num(a.get('dating_range_median_pts'))}점, "
          f"벤더 지정 대체 모델 이동 중앙값 {num(a.get('successor_abs_shift_median_pts_same_papers'))}점(5점 초과 {a.get('successor_abs_shift_over_5_same_papers', '-')}편).")
    ts = read_csv("tiera_successor_claims.csv")
    if ts:
        cls = Counter(r["class_vs_original"] for r in ts)
        papers = sorted({r["wid"] for r in ts})
        up = sum(1 for r in ts if r["class_vs_original"] == "deviated" and float(r["successor_minus_original_pts"]) > 0)
        shifts = sorted(abs(float(r["successor_minus_original_pts"])) for r in ts)
        w(f"- **저장소 기반 논문의 후속 조건 (표 S32)**: 어댑터가 OpenAI 모델 하나를 부르는 {len(papers)}편을 벤더 지정 대체 모델에 그대로 실행. 주장 {len(ts)}개 중 "
          + ", ".join(f"{k} {v}" for k, v in sorted(cls.items())) + f"; 편차 가운데 보고값 위로 {up}건. |이동| 중앙값 {num(shifts[len(shifts) // 2])}점.")
        w("")
        w("| 논문 ID | 주장 | 보고값 | 생전 재실행 | 대체 모델 | 95% 구간 | 차이(점) | 분류 | 비고 |")
        w("|---|---|---|---|---|---|---|---|---|")
        for r in ts:
            w(f"| {r['wid']} | {r['claim']} | {fmt(r['original'])} | {fmt(r['pre_retirement_rerun'])} | {fmt(r['successor'])} ({r['successor_model']}) | "
              f"{ci(r['ci_lo'], r['ci_hi']) if r.get('ci_lo') not in (None, '') else '-'} | {num(r['successor_minus_original_pts'])} | {r['class_vs_original']} | {(r.get('note') or '')[:70]} |")
    w("")
    w("## 파일")
    w("")
    w("- Tier A: `runs/<논문 ID>/run_meta.json`, 주장 표 `data/tiera_claims.csv`, 어댑터 `harness/adapters/`.")
    w("- Tier B: `runs/tierb/<논문 ID>/result.json`, 요약 `runs/tierb/batch1_tierb_summary.json`, 설정 `harness/tierb/configs/`.")
    w("- 후속 전환: `runs/tierb_p3/<조건>/<논문 ID>/result.json`, 요약 `data/p3_summary.csv`, 그림 `figures/p3_successor.png`.")
    w("- 그림: `figures/reexec_forest.png` (Fig 3), `figures/p3_successor.png` (Fig 5 후보), `figures/drift_case_study.png` (Fig 4).")
    w("- 강건성 점검: `data/drift_control.csv`, `data/p3_repeat_spread.csv`·`p3_repeat_summary.csv`, `data/p3_bf16_compare.csv`·`p3_bf16_summary.csv`, "
      "`data/p3_paraphrase_spread.csv`·`p3_paraphrase_summary.csv`, `data/tiera_successor_claims.csv`; 아카이브 `runs/tierb_p3/<조건>/`, `runs/<논문 ID>/successor_vendor/`.")
    w("- 지출: `budget_log.csv`.")
    out = ROOT / "runs" / "RESULTS.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("->", out, f"({len(L)} lines)")


if __name__ == "__main__":
    main()
