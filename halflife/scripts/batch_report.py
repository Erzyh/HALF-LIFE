"""Build the batch-1 results page (HTML artifact) and a Markdown summary from the run records.

python scripts/batch_report.py <out_html> [--md runs/BATCH1_RESULTS.md]
Reads runs/<Wid>/run_meta.json and runs/<Wid>/baseline_alive/result.json for the six baselines.
"""
import argparse, html, json
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
R = HALF / "runs"


def load(wid):
    meta = json.loads((R / wid / "run_meta.json").read_text(encoding="utf-8"))
    res_p = R / wid / "baseline_alive" / "result.json"
    res = json.loads(res_p.read_text(encoding="utf-8")) if res_p.exists() else {}
    return meta, res


def rows():
    """Claim rows: (paper, metric label, orig, orig_ci, rerun, rerun_ci, note)."""
    out = []
    # T1
    m = json.loads((R / "T1" / "run_meta.json").read_text(encoding="utf-8"))
    o, x = m["results"]["original"], m["results"]["reexecution"]
    out.append(("T1 바이오이미지 코드생성", "pass@1 (57 과제)", o["pass@1"], o["bootstrap95_pass@1"], x["pass@1"], x["bootstrap95_pass@1"], "pass@10 0.737 양쪽 동일", "생존"))
    # Tag questions
    m, res = load("W7171749161")
    o, p = res["original"], res["pooled"]
    out.append(("Tag Questions 아첨 역전", "태그 효과 TAGeff (90% CI)", o["tageff"], o["ci90"], p["tageff"], p["ci90"], f"ask 팔 {o['affirm_ask']:.3f}→{p['affirm_ask']:.3f}", "생존"))
    # MedAbstain
    m, res = load("W7140135941")
    rx = res["reexecution"]["noCoT"]; orig = res["original"]["noCoT"]
    for v, label in (("NA", "정확도, 기권 옵션 없음"), ("A", "정확도, 기권 옵션 추가"), ("AP", "정확도, 교란 + 기권")):
        s = rx[v]["split42"]
        out.append(("MedAbstain 의학 기권", label, orig[v]["acc"], None, s["acc"], s["acc_ci95"], f"LAC {orig[v]['lac']:.2f}→{s['lac']:.2f}", "부분 생존"))
    out.append(("MedAbstain 의학 기권", "기권 선택률 (옵션 추가 조건)", 0.0, None, rx["A"]["abstention_rate"], None, "논문 '절대 기권 안 함' → 2.5%", "부분 생존"))
    # News
    m, res = load("W4362598103")
    o, x = res["original"], res["reexecution"]
    out.append(("뉴스 신뢰도 평가", "Spearman ρ, 전문가 평점 대비 (자체 평가 도메인)", o["rho_own"], o["rho_own_ci95"], x["rho_own"], x["rho_own_ci95"], f"n {o['n_rated_with_pc1']}→{x['n_rated_with_pc1']}", "부분 생존"))
    out.append(("뉴스 신뢰도 평가", "평가 거부(-1) 비율", o["unrated_share"], None, x["unrated_share"], None, "도메인 7.0%가 상태 변경", "부분 생존"))
    po, px = o["political"], x["political"]
    out.append(("뉴스 신뢰도 평가", "좌−우 매체 평점 편향 (Welch p)", po["mean_bias_left"] - po["mean_bias_right"], None, px["mean_bias_left"] - px["mean_bias_right"], None, f"p {po['p']:.3f}→{px['p']:.3f}", "부분 생존"))
    # Blinding
    m, res = load("W7144391134")
    out.append(("BlindingLLMs 분자 용해도", "Pearson r×100, 1000-shot (150 분자)", 75.6, [68.5, 81.5], res["1000-shot"]["r"], res["1000-shot"]["ci"], "2회 실행", "생존"))
    out.append(("BlindingLLMs 분자 용해도", "Pearson r×100, 60-shot", 42.9, [28.2, 56.1], res["60-shot"]["r"], res["60-shot"]["ci"], "실행 간 편차 큼 (T=0.7)", "생존"))
    out.append(("BlindingLLMs 분자 용해도", "Pearson r, 0-shot (1,128 분자)", res["original"]["zeroshot"]["pearson_r"], None, res["zeroshot"]["pearson_r"], None, f"암기 지표 {res['original']['zeroshot']['exact3']['pct']}%→{res['zeroshot']['exact3']['pct']}%", "생존"))
    # Cultural
    m, res = load("W4402565126")
    o, x = res["original"], res["reexecution"]
    out.append(("문화 편향 (PNAS Nexus)", "문화 프롬프팅에 의한 거리 감소 (107개국)", o["mean_reduction"], o["mean_reduction_ci95"], x["mean_reduction"], x["mean_reduction_ci95"], f"기본 거리 {o['mean_distance_default']:.2f}→{x['mean_distance_default']:.2f}", "생존"))
    out.append(("문화 편향 (PNAS Nexus)", "정렬 개선 국가 비율", o["share_improved"], None, x["share_improved"], None, f"{o['n_improved']}→{x['n_improved']}/107", "생존"))
    return out


def summary_rows():
    s = json.loads((R / "batch1_summary.json").read_text(encoding="utf-8"))
    t1 = json.loads((R / "T1" / "run_meta.json").read_text(encoding="utf-8"))
    s.insert(0, {"wid": "T1", "name": "바이오이미지 코드생성 (파일럿)", "model": "gpt-4-turbo-2024-04-09", "calls": t1["results"]["calls"], "cost_usd": t1["results"]["cost_usd"], "judgment": "생존 (survived)", "fingerprints": t1["results"]["call_log_stats"]["distinct_system_fingerprints"]})
    return s


EST = {"T1": 9.5, "W7171749161": 0.5, "W7140135941": 1.1, "W4362598103": 99.0, "W7144391134": 16.0, "W4402565126": 48.0}
WHY = {"T1": "상한 $9.5로 잡은 파일럿", "W7171749161": "출력이 Yes/No 두 토큰", "W7140135941": "출력 1토큰, 소형 모델",
       "W4362598103": "3시드 견적, 온도 0이라 1회 실행", "W7144391134": "3회→논문과 같은 2회, 긴 접두부 캐시", "W4402565126": "3시드 견적, 온도 0이라 1회 실행"}


def fmt(v, ci=None, nd=3):
    s = f"{v:.{nd}f}" if isinstance(v, float) and abs(v) < 10 else f"{v:.1f}" if isinstance(v, float) else str(v)
    if ci and ci[0] is not None:
        s += f" [{ci[0]:.{nd}f}, {ci[1]:.{nd}f}]" if abs(ci[1]) < 10 else f" [{ci[0]:.1f}, {ci[1]:.1f}]"
    return s


def dumbbell(o, oci, x, xci, w=260):
    vals = [o, x] + (list(oci) if oci else []) + (list(xci) if xci else [])
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.15 or abs(hi) * 0.1 or 0.05
    lo, hi = lo - pad, hi + pad
    sx = lambda v: 8 + (v - lo) / (hi - lo) * (w - 16)
    parts = [f'<svg class="db" viewBox="0 0 {w} 34" width="{w}" height="34" role="img" aria-label="원 논문 {fmt(o, oci)} 대 재실행 {fmt(x, xci)}">',
             f'<line x1="8" x2="{w-8}" y1="17" y2="17" class="axis"/>']
    if oci:
        parts.append(f'<line x1="{sx(oci[0]):.1f}" x2="{sx(oci[1]):.1f}" y1="11" y2="11" class="ci orig"/>')
    if xci:
        parts.append(f'<line x1="{sx(xci[0]):.1f}" x2="{sx(xci[1]):.1f}" y1="23" y2="23" class="ci rerun"/>')
    parts.append(f'<line x1="{sx(o):.1f}" x2="{sx(x):.1f}" y1="17" y2="17" class="link"/>')
    parts.append(f'<circle cx="{sx(o):.1f}" cy="11" r="5" class="pt orig"><title>원 논문 {fmt(o, oci)}</title></circle>')
    parts.append(f'<circle cx="{sx(x):.1f}" cy="23" r="5" class="pt rerun"><title>재실행 {fmt(x, xci)}</title></circle>')
    parts.append("</svg>")
    return "".join(parts)


def build_html():
    rs, ss = rows(), summary_rows()
    total_calls = sum(s["calls"] for s in ss); total_cost = sum(s["cost_usd"] for s in ss)
    n_surv = sum(1 for s in ss if s["judgment"].startswith("생존")); n_part = len(ss) - n_surv
    H = []
    H.append("""<title>HALF-LIFE 1차 배치 결과</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{--bg:#F6F7F4;--bg-2:#ECEFEA;--ink:#1D2321;--ink-2:#4F5955;--muted:#7A847F;--line:#D3D9D4;--accent:#23596A;--accent-soft:#DCE9EC;--ochre:#A8781F;--ochre-soft:#F3E7CC;--chip:#E4E8E3;--ok:#1E7B4D;--ok-soft:#DDEFE4;--warn:#A8781F;--warn-soft:#F3E7CC;--orig:#eb6834;--rerun:#2a78d6;--surface-1:#fcfcfb}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#151917;--bg-2:#1D2320;--ink:#E7EAE6;--ink-2:#B7BEB9;--muted:#838C87;--line:#2E3633;--accent:#7DB6C3;--accent-soft:#1E2F34;--ochre:#D9A84A;--ochre-soft:#34301F;--chip:#262D2A;--ok:#6CC495;--ok-soft:#1F332A;--warn:#D9A84A;--warn-soft:#34301F;--orig:#d95926;--rerun:#3987e5;--surface-1:#1a1a19}}
:root[data-theme="dark"]{--bg:#151917;--bg-2:#1D2320;--ink:#E7EAE6;--ink-2:#B7BEB9;--muted:#838C87;--line:#2E3633;--accent:#7DB6C3;--accent-soft:#1E2F34;--ochre:#D9A84A;--ochre-soft:#34301F;--chip:#262D2A;--ok:#6CC495;--ok-soft:#1F332A;--warn:#D9A84A;--warn-soft:#34301F;--orig:#d95926;--rerun:#3987e5;--surface-1:#1a1a19}
body{background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans KR","Noto Sans KR","Malgun Gothic",sans-serif;font-size:15px;line-height:1.6}
.wrap{max-width:1040px;margin:0 auto;padding:36px 24px 64px}
header{border-bottom:2px solid var(--accent);padding-bottom:18px;margin-bottom:24px}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
h1{font-size:28px;margin:6px 0 8px;font-weight:700;text-wrap:balance}
.lede{color:var(--ink-2);max-width:70ch;margin:0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0 0}
.tile{background:var(--bg-2);border:1px solid var(--line);border-radius:4px;padding:12px 14px}
.tile .k{font-size:12px;color:var(--muted);letter-spacing:.04em}.tile .v{font-size:22px;font-weight:600;font-variant-numeric:tabular-nums;margin-top:2px}
h2{font-size:19px;margin:36px 0 10px;font-weight:700}
.legend{display:flex;gap:18px;font-size:13px;color:var(--ink-2);margin:0 0 8px}.legend span::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}
.legend .o::before{background:var(--orig)}.legend .r::before{background:var(--rerun)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:4px}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:middle}
th{background:var(--bg-2);font-weight:600;color:var(--ink-2);font-size:12.5px;white-space:nowrap}tr:last-child td{border-bottom:none}
td.num{font-family:"IBM Plex Mono",monospace;font-size:12.5px;white-space:nowrap;font-variant-numeric:tabular-nums}
.paper{font-weight:600;white-space:nowrap}.metric{color:var(--ink-2)}
.chip{display:inline-block;font-size:12px;padding:1px 9px;border-radius:999px;font-weight:600;white-space:nowrap}
.chip.ok{background:var(--ok-soft);color:var(--ok)}.chip.part{background:var(--warn-soft);color:var(--warn)}
svg.db{display:block}svg.db .axis{stroke:var(--line);stroke-width:1}svg.db .link{stroke:var(--muted);stroke-width:1.5}
svg.db .ci{stroke-width:2;opacity:.6}svg.db .ci.orig{stroke:var(--orig)}svg.db .ci.rerun{stroke:var(--rerun)}
svg.db .pt{stroke:var(--surface-1);stroke-width:2}svg.db .pt.orig{fill:var(--orig)}svg.db .pt.rerun{fill:var(--rerun)}
ul{padding-left:20px;max-width:75ch}li{margin:4px 0}
.note{background:var(--accent-soft);border-left:3px solid var(--accent);padding:10px 14px;border-radius:0 4px 4px 0;max-width:75ch}
code{font-family:"IBM Plex Mono",monospace;font-size:12.5px;background:var(--chip);padding:1px 5px;border-radius:3px}
footer{margin-top:40px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:12px}
</style>
<div class="wrap">
<header>
<div class="eyebrow">HALF-LIFE · Tier A 1차 배치 · 2026-09-07</div>
<h1>생전 베이스라인 6편, 원 논문 대 재실행</h1>
<p class="lede">아직 호출되는 날짜 스냅숏(gpt-4-turbo-2024-04-09, gpt-4.1-nano-2025-04-14)에서 여섯 논문의 핵심 주장 하나씩을 원 프로토콜 그대로 다시 쟀습니다. 판정 규칙은 분석 계획 1절(방향 일치 + 신뢰구간 겹침)을 기계적으로 적용했습니다.</p>
<div class="tiles">""")
    for k, v in (("베이스라인", f"{len(ss)}편"), ("생존", f"{n_surv}"), ("부분 생존", f"{n_part}"), ("API 호출", f"{total_calls:,}"), ("지출", f"${total_cost:.2f}"), ("서빙 fingerprint", "논문당 9~10종")):
        H.append(f'<div class="tile"><div class="k">{k}</div><div class="v">{v}</div></div>')
    H.append("</div></header>")

    H.append('<h2>주장별 비교</h2><div class="legend"><span class="o">원 논문 (2024~2025 보고값)</span><span class="r">재실행 (2026-09, 같은 스냅숏)</span><span>가로선 = 95% CI (Tag Questions는 90%)</span></div>')
    H.append('<div class="tablewrap"><table><thead><tr><th>논문</th><th>지표</th><th>원 논문</th><th>재실행</th><th>비교</th><th>메모</th><th>판정</th></tr></thead><tbody>')
    for paper, metric, o, oci, x, xci, note, judg in rs:
        cls = "ok" if judg == "생존" else "part"
        H.append(f'<tr><td class="paper">{html.escape(paper)}</td><td class="metric">{html.escape(metric)}</td><td class="num">{fmt(o, oci)}</td><td class="num">{fmt(x, xci)}</td><td>{dumbbell(o, oci, x, xci)}</td><td>{html.escape(note)}</td><td><span class="chip {cls}">{judg}</span></td></tr>')
    H.append("</tbody></table></div>")

    H.append('<h2>편당 비용: 견적 대 실제</h2><div class="tablewrap"><table><thead><tr><th>논문</th><th>모델</th><th>호출</th><th>견적</th><th>실제</th><th>차이 이유</th><th>판정</th></tr></thead><tbody>')
    for s in ss:
        cls = "ok" if s["judgment"].startswith("생존") else "part"
        H.append(f'<tr><td class="paper">{html.escape(s["name"])}</td><td class="num">{s["model"]}</td><td class="num">{s["calls"]:,}</td><td class="num">${EST[s["wid"]]:.2f}</td><td class="num">${s["cost_usd"]:.2f}</td><td>{WHY[s["wid"]]}</td><td><span class="chip {cls}">{s["judgment"].split(" ")[0]}</span></td></tr>')
    H.append(f'<tr><td class="paper">합계</td><td></td><td class="num">{total_calls:,}</td><td class="num">${sum(EST.values()):.2f}</td><td class="num">${total_cost:.2f}</td><td>견적은 3시드·최대 출력 토큰 기준의 보수치</td><td></td></tr></tbody></table></div>')

    tb_path = R / "tierb" / "batch1_tierb_summary.json"
    if tb_path.exists():
        tb = json.load(open(tb_path, encoding="utf-8"))
        from collections import Counter
        cnt = Counter(t["class"] for t in tb)
        H.append(f'<h2>Tier B 1차 큐: 프롬프트 완결형 {len(tb)}편 (${sum(t["cost"] for t in tb):.2f})</h2>')
        H.append('<p>저장소 없이 논문에 인쇄된 프롬프트와 공개 문항만으로 보고 수치 하나를 다시 잰 결과입니다. 분류는 자동 가안이며(재현: 원 값이 재실행 95% CI 안이거나 차이 2점 이내, 근접: 5점 이내, 편차: 그 이상, 확인 필요: 채점 규칙이 미보고), 최종 판정은 공저자 3인 코딩으로 정합니다.</p>')
        H.append('<div class="tiles">' + "".join(f'<div class="tile"><div class="k">{k}</div><div class="v">{cnt.get(k, 0)}</div></div>' for k in ("재현", "근접", "편차", "확인 필요")) + "</div>")
        H.append('<div class="tablewrap" style="margin-top:12px"><table><thead><tr><th>논문</th><th>모델</th><th>지표</th><th>원 논문</th><th>재실행 (95% CI)</th><th>차이(점)</th><th>n</th><th>비용</th><th>분류</th></tr></thead><tbody>')
        order = {"편차": 0, "확인 필요": 1, "근접": 2, "재현": 3}
        for t in sorted(tb, key=lambda t: (order.get(t["class"], 9), t["wid"])):
            ci = f"[{t['ci'][0]:.2f}, {t['ci'][1]:.2f}]" if t.get("ci") else ""
            d = f"{t['delta_pts']:+.1f}" if isinstance(t.get("delta_pts"), (int, float)) else "-"
            cls = {"재현": "ok", "근접": "ok", "편차": "part", "확인 필요": "part"}[t["class"]]
            H.append(f'<tr><td class="paper">{html.escape(t["title"])}</td><td class="num">{t["model"]}</td><td class="metric">{t["metric"]}</td><td class="num">{t["orig"]}</td><td class="num">{t["rerun"]:.3f} {ci}</td><td class="num">{d}</td><td class="num">{t["n"]}</td><td class="num">${t["cost"]:.2f}</td><td><span class="chip {cls}">{t["class"]}</span></td></tr>')
        H.append("</tbody></table></div>")
    H.append("""<h2>여섯 편에서 공통으로 보인 것</h2>
<ul>
<li><b>문항 수준 출력은 거의 그대로입니다.</b> 뉴스 도메인별 평점의 원본 대 재실행 상관 0.974(평균 절대차 0.011), 문화 설문 10,200개 셀 중 87%가 2024년 응답과 동일, 용해도 0-shot 상관계수 0.407→0.406, 코드 생성 pass@10 동일.</li>
<li><b>행동 지표는 드리프트했습니다.</b> 같은 스냅숏인데 "모른다"며 평가를 거부한 도메인이 41%에서 35%로 줄었고(7%가 상태 변경), 기권 옵션 선택이 0%에서 2.5~3.2%로 늘었습니다. 뉴스 논문의 "유의한 진보 편향 없음"은 거부율 변화 때문에 p 0.16→0.045로 경계선에서 뒤집혔습니다.</li>
<li><b>날짜 스냅숏 하나가 백엔드 fingerprint 9~10종으로 서빙됩니다.</b> 여섯 편 모두 한 시간 안에 관찰. 모델 ID가 같아도 서빙 구성은 하나가 아닙니다.</li>
<li><b>원 논문 쪽 결함도 두 건.</b> 문화 편향 논문 본문의 최근접 국가 수치(네덜란드 0.21 등)는 그 논문의 보충 데이터셋 S5(뉴질랜드 0.125 등)와 맞지 않고, MedAbstain의 보정/시험 분할은 카드가 "시드 없음"으로 적었으나 코드에 시드 42가 있었습니다.</li>
</ul>
<h2>재현 마찰 (환경 부식)</h2>
<ul>
<li>T1: 저장소의 <code>execution.py</code>가 문법 오류 상태로 배포되고 <code>pip install -e .</code>가 실패해 채점기를 다시 구현해야 했습니다.</li>
<li>BlindingLLMs: 파이프라인이 Julia라 프롬프트·파서·분자 분할(MersenneTwister)을 파이썬으로 옮겨 보관된 대화 2,700건과 시험 분자 150개를 100% 재현한 뒤에야 실행할 수 있었습니다.</li>
<li>문화 편향: IVS 원자료는 등록제라 없지만, OSF의 공개 표로부터 지도 투영을 선형 복원(잔차 5e-14)해 논문의 보충 데이터셋을 그대로 재현했습니다.</li>
<li>뉴스 신뢰도: 그림 단위 분석 코드가 저장소에 없어 재구현했고, 편향 점수는 Dataverse가 기본 클라이언트를 403으로 막아 브라우저 헤더로 받았습니다.</li>
<li>Tag Questions: 원 호출은 OpenRouter 경유, 저장소에 라이선스 없음. MedAbstain: few-shot 조건은 임베딩 모델(text-embedding-ada-002) 의존이라 범위 밖.</li>
</ul>
<div class="note">모든 호출의 요청·응답 전문과 해시, 서빙 모델명, fingerprint는 <code>halflife/runs/&lt;Wid&gt;/baseline_alive/calls.jsonl</code>에, 편당 요약과 판정은 <code>run_meta.json</code>에 있습니다. 판정의 사람 이중 코딩은 11월에 합니다.</div>
<footer>HALF-LIFE · 재현성 반감기 프로젝트 · 1차 배치 보고</footer>
</div>""")
    return "\n".join(H)


def build_md():
    rs, ss = rows(), summary_rows()
    L = ["# Tier A 1차 배치 결과 (2026-09-07)", "", "| 논문 | 모델 | 호출 | 비용 | 판정 |", "|---|---|---|---|---|"]
    for s in ss:
        L.append(f"| {s['name']} | {s['model']} | {s['calls']:,} | ${s['cost_usd']:.2f} | {s['judgment']} |")
    L += ["", "| 논문 | 지표 | 원 논문 | 재실행 | 메모 | 판정 |", "|---|---|---|---|---|---|"]
    for paper, metric, o, oci, x, xci, note, judg in rs:
        L.append(f"| {paper} | {metric} | {fmt(o, oci)} | {fmt(x, xci)} | {note} | {judg} |")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_html")
    ap.add_argument("--md", default=str(R / "BATCH1_RESULTS.md"))
    a = ap.parse_args()
    Path(a.out_html).write_text(build_html(), encoding="utf-8")
    Path(a.md).write_text(build_md(), encoding="utf-8")
    print("->", a.out_html, "|", a.md)


if __name__ == "__main__":
    main()
