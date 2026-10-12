# 수기 검증 (의존 분류) 작업 폴더

센서스 자동 분류의 정확도를 재기 위한 사람 코딩. 규칙은 `CODEBOOK.md`, 통계 계획은 `../ANALYSIS_PLAN.md` 5절.

## 파일

| 파일 | 내용 |
|---|---|
| `CODEBOOK.md` | 코드 정의, 판단 순서, 자주 나오는 경우, 절차. 개정 이력 포함 |
| `coders3/halflife_coding_{pilot,main}_coder{A,B,C}.xlsx` | 코더 3인 체제. 파일럿은 전원 같은 30편, 본표본은 순환 배정 333~334편 |
| `coders4/halflife_coding_{pilot,main}_coder{A,B,C,D}.xlsx` | 코더 4인 체제. 본표본 각 250편 |
| `../data/coding/assignment_main_k{3,4}.csv` | 본표본 배정표 (coder1, coder2, 불일치 결정자) |
| `results_v12/` | 파일럿 v1.2 회신 4개(2026-09-22~27). 검토는 `PILOT_REVIEW_v12.md` |
| `results_main/` | 본표본 회신을 여기에 모은다(파일명 유지). 배포 안내는 `MAIN_DISTRIBUTION.md` |
| `judgment_sheet_v1.xlsx`, `judgment_key_v1.csv` | 재실행 결과 3인 판정 마스터 시트와 조건 열쇠(판정자에게 보내지 않음). `scripts/judgment_sheet.py` |
| `judgment/halflife_judgment_v1_judge{A,B,C}.xlsx` | 판정자별 사본(입력 열 한 벌). 배포 안내는 `JUDGMENT_DISTRIBUTION.md` |
| `results_judgment/` | 판정 회신을 여기에 모은다. 병합은 `scripts/judgment_merge.py` |
| `merge_<set>.json`, `disagreements_<set>.csv` | 회신 파일을 합친 결과(Krippendorff α, 짝별 κ, 불일치 목록과 결정자). 병합 스크립트가 생성 |
| `../data/coding/sample_v1.csv` | 표본 추출 결과 (set, stratum 포함). 시드 고정 |
| `../data/coding/evidence_v1.jsonl` | 논문별 근거 문장 추출 결과. 짧은 발췌이며 재배포하지 않음 |

## 스크립트 (`../scripts/`)

```bash
python scripts/coding_sample.py                       # 표본 재추출 (동일 시드 -> 동일 결과)
python scripts/coding_evidence.py --set all           # 전문 수집 + 근거 추출 (재개 가능)
python scripts/coding_evidence.py --set all --arxiv-fallback   # 실패분을 arXiv 제목 검색으로 보완
python scripts/coding_workbook.py --set pilot --coders A B C --assign all      # 파일럿: 전원 같은 30편 -> coding/coders3/
python scripts/coding_workbook.py --set main --coders A B C --assign rotate    # 본표본: 논문당 2인 순환 배정
python scripts/coding_merge.py --set pilot            # 회신 파일 병합 (2인 이상), α·κ 계산; --dir로 폴더 지정
```

회신 파일은 파일명을 유지한 채 해당 폴더(coders3 또는 coders4)에 덮어쓴다. 병합 스크립트는 그 폴더의 `halflife_coding_<set>_coder*.xlsx`를 모두 읽고, 코더 수에 맞는 배정표로 불일치 결정자를 붙인다.

## 표본 설계 요약

주의(9/28 정정): 층의 모델 상태(dead / dying)는 표본을 뽑은 9월 2일의 식별자 목록 기준이다. 9월 28일에 gpt-4-0613(→ 2026-10-23 종료 예정, dying)과 gpt-4-0314(→ 2026-03-26 종료)의 날짜를 정정했지만 이미 배포된 표본은 다시 뽑지 않는다. 분석에서는 정정된 상태를 공변량으로 쓴다.

프레임은 `census_v2.csv` 27,044편에서 비영어 395편을 뺀 26,649편. 층은 모델 상태(dead / dying / dead|dying) × 분야군 6개(CS, MED, SOC, ENG, LIFE, UNK). 본표본 500은 층 크기에 비례하되 셀당 최소 8편, 셀 안에서는 연도순 계통추출. 파일럿 30과 예비 60은 같은 방식의 별도 추출이며 서로 겹치지 않는다. 예비는 본표본 논문이 열리지 않을 때만 사유를 기록하고 쓴다.

## 코딩 결과의 용도

- ID별 역할(S/B/A = 의존, C/X = 비의존)을 자동 분류와 대조해 층별 정밀도·재현율과 코더 간 α(및 짝별 κ)를 보고
- Q2 버전 표기 수준은 H3(표기율), Q1 웹UI 비율은 스냅숏 부재 층, Q3·Q4는 L0~L3 등급의 원료
