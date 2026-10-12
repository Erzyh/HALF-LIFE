"""Build the coder workbooks for the manual dependence coding (coding/CODEBOOK.md).

python scripts/coding_workbook.py --set pilot --coders A B
  -> coding/halflife_coding_pilot_coderA.xlsx, coding/halflife_coding_pilot_coderB.xlsx

Inputs: data/coding/sample_v1.csv (the draw) and data/coding/evidence_v1.jsonl (pre-extracted
snippets). Both coders get identical workbooks; only the coder label differs. No formulas:
agreement is computed by scripts/coding_merge.py after the files come back.
"""
import argparse, csv, json, re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "coding" / "sample_v1.csv"
EVID = ROOT / "data" / "coding" / "evidence_v1.jsonl"
VOCAB = ROOT / "target_models.json"
OUTDIR = ROOT / "coding"

FONT = "Arial"
MAX_IDS = 6
LISTS = {
    "role": "실행,인용·언급,못찾음,판단불가",
    "q1": "API,웹UI,혼합,클라우드배포,서드파티,로컬,해당없음,불명",
    "q2": "날짜 스냅숏,별칭·계열명,제품명,해당없음",
    "q3": "연월,연도만,없음,해당없음",
    "q5": "전문,초록만,불가",
    "q6": "높음,낮음",
}
FIXED = ["번호", "openalex_id", "제목", "연도", "분야", "유형", "DOI", "OA 링크", "매칭 ID", "추출 상태",
         "근거 요약", "힌트"]
QCOLS = ["실행한 모델(전체)", "Q1 접근경로", "Q2 버전표기", "Q3 실행시점", "Q5 열람", "Q6 확신도", "메모", "소요(분)"]
WIDTHS = {"번호": 6, "openalex_id": 14, "제목": 42, "연도": 6, "분야": 14, "유형": 10, "DOI": 10, "OA 링크": 10,
          "매칭 ID": 22, "추출 상태": 9, "근거 요약": 75, "힌트": 38, "실행한 모델(전체)": 34, "Q2 버전표기": 14,
          "메모": 30, "소요(분)": 8}

HEAD_FILL = PatternFill("solid", fgColor="1F4E78")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
NA_FILL = PatternFill("solid", fgColor="D9D9D9")
WRAP = Alignment(wrap_text=True, vertical="top")
TOP = Alignment(vertical="top")

ROLE_TABLE = [
    ("실행", "저자가 직접 실행", "저자가 이 모델을 직접 호출해 결과를 얻었다. 평가 대상, 비교 베이스라인, 제안 방법의 백본, 미세조정, 심사자·라벨러·데이터 생성 같은 보조 도구, 사람에게 준 개입 모두 포함. 실행 결과가 표·본문·부록에 있거나 실행했다는 서술이 있어야 함"),
    ("인용·언급", "실행하지 않음", "관련연구·서론·논의의 언급, 참고문헌 제목, 다른 논문에서 옮긴 수치를 넣은 비교표, 향후 연구, 예시로 든 이름, 논문 작성 보조 고지"),
    ("못찾음", "문자열이 없음", "본문·부록·표·각주·참고문헌 어디에도 이 ID(별칭 포함)가 없음. 검색 오탐. 참고문헌의 제목·URL·모델 카드 링크에만 있어도 '인용·언급'이지 '못찾음'이 아님 (v1.3)"),
    ("판단불가", "열 수 없음", "전문을 열 수 없음, 읽을 수 없는 언어, 깨진 PDF. 초록만으로 추정하지 않음. 메모에 출처(ACM DL, IOS Press 등)와 시도한 경로를 적음 (v1.3)"),
]
Q_TABLE = [
    ("실행한 모델(전체)", "저자가 직접 실행한 모델 전체를 논문에 적힌 가장 구체적인 표기 그대로, 쉼표로 구분해 한 줄에(줄바꿈 금지), 주 모델을 반드시 맨 앞에, 찾은 날짜 스냅숏은 그 문자열 그대로 (예: gpt-4o-mini-2024-07-18, claude-3-5-sonnet, Llama-3.1-70B-Instruct). 언급만 된 모델은 적지 않음. 실행이 없으면 비움"),
    ("Q1 접근경로", "매칭된 상용 모델의 경로만 답한다 (v1.3). API(SDK·호출 코드·temperature 같은 파라미터·코드 저장소가 있으면 API) / 웹UI(채팅 화면) / 혼합(같은 상용 모델을 웹UI와 API 두 경로로) / 클라우드배포(Azure·Bedrock·Vertex) / 서드파티(OpenRouter 등) / 로컬(드묾) / 해당없음(실행 없음) / 불명(실행했으나 경로 단서가 전혀 없음). 오픈 가중치 모델을 함께 로컬로 돌린 경우는 '혼합'이 아니라 상용 모델의 경로(보통 API)"),
    ("Q2 버전표기", "'실행한 모델' 목록의 첫 모델(주 모델)을 어떻게 표기했는가. 날짜 스냅숏(gpt-4-0613, gpt-4o-2024-05-13, claude-3-opus-20240229, text-davinci-003) / 별칭·계열명(gpt-4-turbo, gpt-4o, claude-3-5-sonnet, o1-preview) / 제품명(ChatGPT, GPT-4, Gemini) / 해당없음(실행 없음). 본문·표·각주·부록·저장소 어디든 날짜 스냅숏이 있으면 '날짜 스냅숏'. 찾았으면 그 문자열을 실행 모델 칸에 적는다. 한 명이라도 찾으면 병합에서 인정 (v1.3)"),
    ("Q3 실행시점", "모델을 호출한 시점이 적혀 있는가. 연월 / 연도만 / 없음 / 해당없음(실행 없음). 투고일·학회 일자는 해당 없음"),
    ("Q5 열람", "전문 / 초록만 / 불가"),
    ("Q6 확신도", "높음 / 낮음. 낮음이면 메모에 이유"),
    ("메모", "판단이 어려웠던 이유, 코드북에 없는 상황, 목록 외 모델에 대한 설명"),
    ("판단 순서", "1) ID가 나오는 자리를 모두 찾는다(Ctrl+F, 별칭까지). 2) 참고문헌·관련연구의 언급뿐이면 '인용·언급'. 3) 저자가 실행했으면 '실행'. 4) 어디에도 없으면 '못찾음', 열 수 없으면 '판단불가'. 5) 실행한 모델 전체를 적고 Q1~Q3, Q5, Q6을 채운다"),
]
EXAMPLES = [
    ("본문 'We evaluate GPT-4 Turbo (gpt-4-1106-preview) on our benchmark', 표 1에 점수. 매칭 ID gpt-4-1106-preview", "실행", "gpt-4-1106-preview, Llama-2-70b-chat", "API", "날짜 스냅숏", "연월", ""),
    ("관련연구에 'text-davinci-003 (Ouyang et al.) showed …', 참고문헌에도 등장. 실험은 Llama만 실행", "인용·언급", "Llama-2-7b", "로컬", "별칭·계열명", "없음", "매칭 ID는 언급만, 주 모델은 목록 외"),
    ("오픈 모델들을 평가하면서 채점자로 gpt-4-1106-preview 사용 (AlpacaEval 방식)", "실행", "Mistral-7B-Instruct, gpt-4-1106-preview", "API", "별칭·계열명", "없음", "gpt-4-1106-preview는 심사자로 실행"),
    ("매칭 ID gpt-4-turbo. 본문 표기 'GPT-4 Turbo', 부록 표에 'gpt-4-turbo-2024-04-09'. 제안 방법의 백본", "실행", "gpt-4-turbo-2024-04-09", "API", "날짜 스냅숏", "연도만", "부록의 실제 문자열로 적음"),
    ("말미 고지 'ChatGPT (gpt-4-0613) was used to improve readability'. 실험은 없음", "인용·언급", "", "해당없음", "해당없음", "해당없음", "작성 보조"),
    ("의대생 60명에게 ChatGPT 웹 화면(gpt-4-0613 시절)으로 답을 보여주고 학습 효과 측정", "실행", "ChatGPT", "웹UI", "제품명", "연월", "개입 = 모델 출력"),
    ("매칭 ID claude-2가 참고문헌 제목에만 있고 본문에는 없음. 실험은 GPT-4o로 수행", "인용·언급", "gpt-4o", "API", "별칭·계열명", "없음", "참고문헌 제목만이라 못찾음이 아님"),
    ("GPT-4o(temperature 0, 공식 API)와 Llama-3-8B(로컬 GPU)를 같은 벤치마크로 비교. 매칭 ID gpt-4o-2024-05-13", "실행", "gpt-4o-2024-05-13, Llama-3-8B-Instruct", "API", "날짜 스냅숏", "없음", "오픈 모델 로컬 병행은 혼합 아님 (v1.3)"),
    ("매칭 ID claude-3-5-sonnet이 참고문헌의 system card URL에만 있음. 실험은 o4-mini", "인용·언급", "o4-mini", "API", "별칭·계열명", "없음", "URL 문자열만 = 인용·언급 (v1.3)"),
    ("ACM DL 전문을 열 수 없고 초록에 'GPT-4 기반 baseline'만 있음. 매칭 ID gpt-4-0613", "판단불가", "", "", "", "", "메모에 'ACM DL 접근 불가'. 초록만으로 실행을 추정하지 않음 (v1.3)"),
]


def clean(v):
    """Strip control characters that PDF extraction leaves behind (openpyxl rejects them)."""
    return ILLEGAL_CHARACTERS_RE.sub("", v) if isinstance(v, str) else v


def load_evidence():
    ev = {}
    if EVID.exists():
        for line in open(EVID, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                ev[r["openalex_id"]] = r
    return ev


def id_kind(mid):
    if re.search(r"\d{4}-\d{2}-\d{2}|\d{8}|-(0301|0314|0613|1106|0125)\b|davinci|curie|bison", mid):
        return "스냅숏 (D)"
    return "별칭 (A)"


def hint_text(e):
    if not e or "ids" not in e:
        return "전문 추출 실패 - 링크로 논문을 여세요"
    parts = []
    counts = [f"{m}: 본문 {d['n_body']} / 참고문헌 이후 {d['n_refs']}" for m, d in e["ids"].items()]
    parts.append("등장 횟수 " + "; ".join(counts))
    h = e.get("hints", {})
    lab = {"api": "API", "webui": "웹UI", "azure": "Azure", "openrouter": "OpenRouter", "bedrock_vertex": "Bedrock/Vertex",
           "temperature": "temperature", "batch_or_playground": "Batch/Playground"}
    hs = [f"{lab[k]} {v}" for k, v in h.items() if v]
    parts.append("경로 단서: " + (", ".join(hs) if hs else "없음"))
    if e.get("dates_near_mentions"):
        parts.append("언급 근처 날짜: " + ", ".join(e["dates_near_mentions"]))
    if e.get("other_ids_in_text"):
        parts.append("본문의 다른 버전 ID: " + ", ".join(e["other_ids_in_text"]))
    if e.get("repo_links"):
        parts.append("저장소 링크: " + ", ".join(e["repo_links"]))
    if e.get("refs_start_frac") is None:
        parts.append("참고문헌 경계 미검출 (위치 구분 없음)")
    return "\n".join(parts)


def evidence_text(e, limit=1400):
    if not e or "ids" not in e:
        return ""
    out = []
    for m, d in e["ids"].items():
        sn = [s for s in d["snippets"] if s["where"] == "body"] or d["snippets"]
        if not sn:
            out.append(f"[{m}] 추출된 본문에서 못 찾음")
            continue
        s = sn[0]
        tag = "본문" if s["where"] == "body" else "참고문헌 이후"
        out.append(f"[{m}] ({tag}, {int(s['pos']*100)}%) {s['text'][:330]}")
    t = "\n".join(out)
    return t if len(t) <= limit else t[:limit] + " …"


def style_header(ws, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF")
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 32


def build(set_name, coder, rows, ev, vocab, total=None):
    wb = Workbook()
    # ---- 안내
    ws = wb.active
    ws.title = "안내"
    n = len(rows)
    assigned_note = (f"이 파일에는 전체 {total}편 중 배정된 {n}편만 들어 있습니다. '번호'는 전체 표본 번호이므로 다른 코더와 같은 번호는 같은 논문입니다."
                     if total and total != n else None)
    lines = [
        (f"HALF-LIFE 의존 분류 수기 코딩 - {'파일럿' if set_name == 'pilot' else '본표본'} ({n}편) - 코더 {coder} - 코드북 v1.3", True),
        ("", False),
        *([(assigned_note, False)] if assigned_note else []),
        ("이 파일은 논문을 '재현'하는 것이 아니라 읽고 분류하는 작업입니다. '코딩' 시트의 노란 칸만 채우면 됩니다.", False),
        ("", False),
        ("순서", True),
        ("1. '코드북' 시트를 한 번 읽습니다 (전체 규칙은 coding/CODEBOOK.md).", False),
        ("2. '예시' 시트에서 코딩된 예 10개를 봅니다.", False),
        ("3. '코딩' 시트에서 한 행(논문 한 편)씩: 근거 요약과 힌트를 보고, 확신이 없으면 DOI/OA 링크로 논문을 열어 Ctrl+F로 ID를 찾습니다.", False),
        ("4. ID1~ID6 역할(드롭다운: 실행 / 인용·언급 / 못찾음 / 판단불가), 실행한 모델(전체), Q1~Q3, Q5~Q6, 메모를 채웁니다. ID가 비어 있는 회색 칸은 건너뜁니다.", False),
        ("   코드북 v1.3에서 바뀐 규칙: Q1은 매칭된 상용 모델의 경로만 답합니다(오픈 모델을 로컬로 함께 돌려도 'API'; 호출 파라미터·SDK·코드가 있으면 'API'; 단서가 전혀 없을 때만 '불명').", False),
        ("   날짜 스냅숏을 찾으면 그 문자열을 '실행한 모델' 칸 맨 앞에 적습니다. 참고문헌의 URL·모델 카드 링크에만 있으면 '인용·언급'. 전문을 못 열면 '판단불가'로 두고 메모에 출처를 적습니다.", False),
        ("5. 다 하면 파일명을 바꾸지 말고 그대로 저장해서 보냅니다. 중간 회신도 됩니다.", False),
        ("", False),
        ("범례", True),
        ("노란 칸 = 입력 / 회색 칸 = 입력 없음 / 파란 글자 = 링크", False),
        ("'근거 요약'은 ID별 첫 문장만 보여줍니다. 전체 목록은 '근거 전체' 시트에서 번호로 찾습니다.", False),
        ("'참고문헌 이후'는 자동 검출한 참고문헌 시작점 뒤라는 뜻이며 부록이 섞일 수 있습니다. 위치 판단은 논문에서 직접 확인합니다.", False),
        ("", False),
        ("시간", True),
        ("편당 3~5분 목표, 10분을 넘기면 현재 판단을 적고 확신도 '낮음' + 메모.", False),
        ("다른 코더와 상의하지 않고 독립적으로 코딩합니다. 불일치는 회신 뒤에 같이 봅니다.", False),
        ("저자에게 문의하지 않습니다. 논문과 논문이 가리키는 공개 저장소만 봅니다.", False),
    ]
    for i, (t, bold) in enumerate(lines, 1):
        c = ws.cell(row=i, column=1, value=t)
        c.font = Font(name=FONT, bold=bold, size=12 if i == 1 else 10)
    ws.column_dimensions["A"].width = 120

    # ---- 코드북
    ws = wb.create_sheet("코드북")
    ws.append(["코드", "이름", "기준"])
    for r in ROLE_TABLE:
        ws.append(list(r))
    ws.append([])
    ws.append(["항목", "", "값과 뜻"])
    for k, v in Q_TABLE:
        ws.append([k, "", v])
    for row in ws.iter_rows():
        for c in row:
            c.font = Font(name=FONT, bold=(c.row in (1, len(ROLE_TABLE) + 3)))
            c.alignment = WRAP
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 120

    # ---- 예시
    ws = wb.create_sheet("예시")
    ws.append(["상황", "역할", "실행한 모델(전체)", "Q1", "Q2", "Q3", "메모"])
    for r in EXAMPLES:
        ws.append(list(r))
    style_header(ws, 7)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name=FONT)
            c.alignment = WRAP
    for col, w in zip("ABCDEFG", (60, 10, 30, 10, 12, 9, 30)):
        ws.column_dimensions[col].width = w

    # ---- 코딩
    ws = wb.create_sheet("코딩")
    header = list(FIXED)
    for k in range(1, MAX_IDS + 1):
        header += [f"ID{k}", f"ID{k} 역할"]
    header += QCOLS
    ws.append(header)
    style_header(ws, len(header))
    col = {h: i + 1 for i, h in enumerate(header)}
    dvs = {k: DataValidation(type="list", formula1=f'"{v}"', allow_blank=True, showErrorMessage=True,
                             errorTitle="목록에서 선택", error="드롭다운 값 중 하나를 고르세요")
           for k, v in LISTS.items()}
    for dv in dvs.values():
        ws.add_data_validation(dv)
    qmap = {"Q1 접근경로": "q1", "Q2 버전표기": "q2", "Q3 실행시점": "q3", "Q5 열람": "q5", "Q6 확신도": "q6"}
    for i, r in enumerate(rows, 1):
        e = ev.get(r["openalex_id"])
        ids = r["matched_models"].split("|")
        wid = r["openalex_id"].rsplit("/", 1)[-1]
        fetch = (e or {}).get("fetch", "none")
        fetch_kr = {"pdf": "PDF", "html": "HTML", "pdf_arxiv_fallback": "PDF (arXiv 판)", "pdf_unparsed": "PDF 파싱 실패", "none": "링크 없음"}.get(
            fetch, "실패" if fetch.startswith("error") else fetch)
        tm = (e or {}).get("title_match")
        if tm is not None and tm < 0.5:
            # the fetched document is probably not this paper (landing page or wrong OA link)
            fetch_kr = "제목 불일치"
            ev_txt = "자동 추출한 문서가 이 논문이 아닐 수 있습니다 (제목 일치도 낮음). 링크로 논문을 직접 여세요."
            hint_txt = "근거 문장 사용 금지. DOI/OA 링크 확인."
        else:
            ev_txt, hint_txt = evidence_text(e), hint_text(e)
        num = int(r.get("_num", i))
        vals = [num, wid, r["title"], r["year"], r["field"] or "(미상)", r["type"], r["doi"], r["oa_url"],
                "\n".join(ids), fetch_kr, ev_txt, hint_txt]
        for k in range(MAX_IDS):
            vals += [ids[k] if k < len(ids) else "", ""]
        vals += [""] * len(QCOLS)
        ws.append([clean(v) for v in vals])
        row = i + 1
        for c in range(1, len(header) + 1):
            cell = ws.cell(row=row, column=c)
            cell.font = Font(name=FONT, size=9)
            cell.alignment = WRAP if header[c - 1] in ("제목", "매칭 ID", "근거 요약", "힌트", "메모") else TOP
        for h in ("DOI", "OA 링크"):
            cell = ws.cell(row=row, column=col[h])
            if cell.value:
                url = cell.value
                cell.hyperlink = url
                cell.value = "열기"
                cell.font = Font(name=FONT, size=9, color="0563C1", underline="single")
        for k in range(MAX_IDS):
            idc = ws.cell(row=row, column=col[f"ID{k+1}"])
            rc = ws.cell(row=row, column=col[f"ID{k+1} 역할"])
            if k < len(ids):
                rc.fill = INPUT_FILL
                dvs["role"].add(rc)
            else:
                idc.fill = NA_FILL
                rc.fill = NA_FILL
        for h in QCOLS:
            cell = ws.cell(row=row, column=col[h])
            cell.fill = INPUT_FILL
            if h in qmap:
                dvs[qmap[h]].add(cell)
        ws.row_dimensions[row].height = 118
    for h, w in WIDTHS.items():
        ws.column_dimensions[get_column_letter(col[h])].width = w
    for k in range(1, MAX_IDS + 1):
        ws.column_dimensions[get_column_letter(col[f"ID{k}"])].width = 20
        ws.column_dimensions[get_column_letter(col[f"ID{k} 역할"])].width = 11
    for h in QCOLS:
        if h not in WIDTHS:
            ws.column_dimensions[get_column_letter(col[h])].width = 12
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(header))}{len(rows) + 1}"

    # ---- 근거 전체
    ws = wb.create_sheet("근거 전체")
    ws.append(["번호", "openalex_id", "ID", "위치", "위치(%)", "문장"])
    style_header(ws, 6)
    for i, r in enumerate(rows, 1):
        e = ev.get(r["openalex_id"])
        wid = r["openalex_id"].rsplit("/", 1)[-1]
        tm = (e or {}).get("title_match")
        if tm is not None and tm < 0.5:
            ws.append([int(r.get("_num", i)), wid, "", "제목 불일치", "", "자동 추출 문서가 이 논문이 아닐 수 있어 근거 문장을 싣지 않음"])
            continue
        for m, d in (e or {}).get("ids", {}).items():
            for s in d["snippets"]:
                ws.append([int(r.get("_num", i)), wid, m, "본문" if s["where"] == "body" else "참고문헌 이후", int(s["pos"] * 100), clean(s["text"])])
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name=FONT, size=9)
            c.alignment = WRAP if c.column == 6 else TOP
    for colL, w in zip("ABCDEF", (6, 14, 24, 12, 8, 120)):
        ws.column_dimensions[colL].width = w
    ws.freeze_panes = "A2"

    # ---- 모델ID참조
    ws = wb.create_sheet("모델ID참조")
    ws.append(["ID", "제조사", "상태", "종료일", "표기 유형"])
    style_header(ws, 5)
    st = {"dead": "사망", "dying": "사망 예고", "alive": "생존"}
    for m in vocab:
        ws.append([m["id"], m.get("vendor", ""), st.get(m.get("status", ""), m.get("status", "")),
                   m.get("shutdown", ""), id_kind(m["id"])])
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name=FONT, size=9)
    for colL, w in zip("ABCDE", (30, 10, 10, 12, 14)):
        ws.column_dimensions[colL].width = w
    ws.freeze_panes = "A2"

    wb.move_sheet("코딩", offset=-1)  # order: 안내, 코드북, 코딩, 예시, 근거 전체, 모델ID참조
    return wb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="pilot", choices=["pilot", "main", "reserve"])
    ap.add_argument("--coders", nargs="+", default=["A", "B"])
    ap.add_argument("--assign", choices=["all", "rotate"], default="all",
                    help="all: every coder gets every paper; rotate: each paper goes to two coders, rotating pairs")
    ap.add_argument("--outdir", default=None, help="output folder (default coding/coders<k>/)")
    a = ap.parse_args()
    OUTDIR = Path(a.outdir) if a.outdir else ROOT / "coding" / f"coders{len(a.coders)}"
    rows = [r for r in csv.DictReader(open(SAMPLE, encoding="utf-8-sig")) if r["set"] == a.set]
    for i, r in enumerate(rows, 1):
        r["_num"] = i                                   # global sample number, kept in every coder's file
    ev = load_evidence()
    vocab = json.load(open(VOCAB, encoding="utf-8"))["models"]
    missing = [r["openalex_id"] for r in rows if r["openalex_id"] not in ev]
    if missing:
        print(f"warning: {len(missing)} papers have no evidence record yet (run coding_evidence.py)")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    assignment = {}
    if a.assign == "rotate":
        import random
        k = len(a.coders)
        order = list(range(len(rows)))
        random.Random(20260907).shuffle(order)
        pairs = [(a.coders[j % k], a.coders[(j + 1) % k]) for j in range(k)]   # (A,B),(B,C),(C,A) ...
        for slot, idx in enumerate(order):
            assignment[rows[idx]["openalex_id"]] = pairs[slot % k]
        with open(ROOT / "data" / "coding" / f"assignment_{a.set}_k{k}.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["num", "openalex_id", "coder1", "coder2", "third_coder"])
            for r in rows:
                c1, c2 = assignment[r["openalex_id"]]
                third = [c for c in a.coders if c not in (c1, c2)]
                w.writerow([r["_num"], r["openalex_id"], c1, c2, "/".join(third)])
    for coder in a.coders:
        mine = rows if a.assign == "all" else [r for r in rows if coder in assignment[r["openalex_id"]]]
        wb = build(a.set, coder, mine, ev, vocab, total=len(rows))
        out = OUTDIR / f"halflife_coding_{a.set}_coder{coder}.xlsx"
        wb.save(out)
        print("->", out, f"({len(mine)} papers)")
    ok = sum(1 for r in rows if ev.get(r["openalex_id"], {}).get("ids"))
    print(f"{a.set}: {len(rows)} papers, evidence extracted for {ok}")


if __name__ == "__main__":
    main()
