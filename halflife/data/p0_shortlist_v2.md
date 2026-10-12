# P0 셔틀리스트 v2 — 도메인 보충 반영 (2026-09-02)

v1(초기 풀 159편 검토, A급 30)에 확장 풀의 저대표 도메인 후보 76편 검토 결과를 더했다.
**살아있는 팔(live arm)** = 아직 호출 가능한 사망예고 모델. 생전 베이스라인은 이 팔에서만 가능하다.

v1 후보 중 어제 verify로 층이 바뀐 것: MEDEC(o1-preview), DxGPT(GPT-4 Turbo 1106), Clinical Chemistry MCQ(GPT-4/Bard), 문화 편향(GPT-3/3.5/4) 등은 **사망층 → P3 전환 비교 전용**. 살아있는 팔이 하나라도 있으면 P0 가능(부분 베이스라인).

## 보충 A급 후보 (신규, 도메인별)

### 생물정보학·생의학 (도메인 공백 해소)
| # | 논문 | 살아있는 팔 | 유형 | 재실행 메모 |
|---|---|---|---|---|
| T1 | **Benchmarking LLMs for Bio-Image Analysis Code Generation** (2024, 57 프롬프트 + 단위 테스트, 18개 모델) | gpt-4-turbo-2024-04-09 | 대상 | 단위 테스트 채점이라 판정 객관적. 비용 극소. **파일럿 1순위 후보** |
| T2 | **Pattern Recognition or Medical Knowledge? Glianorex 가상 장기 MCQ** (ACL 2025) | gpt-4-turbo, gpt-4o-2024-05-13 | 대상 | 벤치마크 생성물 공개, lm-eval-harness. 의사 27% vs 모델 64% |
| T3 | **MedXpertQA** (2025, 4,460문항, 18개 모델) | o1-2024-12-17, o3-mini | 대상 | 추론 모델 의학 벤치마크. o1 비용 → 추론 부분집합만 |
| T4 | **GPT for RCTs? 보고 지침 준수 판정** (BMJ Open 2025, 113편 × 9문항, OSF) | gpt-4-turbo | 주석자 | F1 0.89 재현. 프롬프트-완결형, 데이터 OSF 공개 |
| T5 | **Swedish Medical LLM Benchmark** (2025, 18개 모델) | gpt-4-turbo | 대상 | 비영어 의학 벤치마크 공개 |
| T6 | **Radiation Oncology Physics MCQ, 선택지 셔플** (2025, 100문항) | gpt-4o (스냅숏 확인) | 대상 | "None of the above" 추론 검정. 비용 극소 |
| T7 | **Diagnose and Treat Bias in LLMs for Clinical Decision-Making** (NAACL 2025) | gpt-4-turbo, gpt-4o-2024-05-13 | 대상/편향 | 코드 공개 |
| T8 | **Multi-model longitudinal assessment, 브라질 레지던트 시험** (2025, 1,041문항) | o4-mini, gpt-4-turbo | 대상 | 포르투갈어. 저자 자체가 "종단 평가"라 주제 공명 |
| T9 | **Knowing When to Abstain: Medical LLMs Under Clinical Uncertainty** (EACL 2026) | gpt-4.1-nano | 대상 | 4.1-nano 팔이 10/23 사망 |
| T10 | Lived Experience Not Found: ADR 전문가 정렬 (NAACL 2025) | gpt-4-turbo (부분) | 대상 | Claude 팔은 사망. 부분 베이스라인 |

### 재료·화학 (도메인 공백 해소)
| # | 논문 | 살아있는 팔 | 유형 | 재실행 메모 |
|---|---|---|---|---|
| T11 | **LLMs for nano synthesis mechanism explanation** (2024, 775 MCQ, c-score) | gpt-4-turbo | 대상 | 금 나노입자 합성 기제. logprob 필요 — gpt-4-turbo 지원 |
| T12 | **Unveiling the Potential of AI for Nanomaterial Morphology Prediction** (2024) | gpt-4-turbo | 대상 | 데이터셋 공개 |
| T13 | **MatDuck: Zero-Shot Materials Science Text Mining** (AAAI 2025, 8개 벤치마크) | gpt-4-turbo | 주석자/추출 | 코드 공개 |
| T14 | **In-Context Molecular Property Prediction: Blinding Study on Memorization** (2026, MoleculeNet) | gpt-4.1-nano, gpt-5 스냅숏 | 대상 | 오염·암기 주제 — 우리 논문과 공명 |
| T15 | AtomAgents 합금 설계 다중 에이전트 (2024) | gpt-4-turbo | 구성요소 | 물리 시뮬레이션 결합 — Tier B/C, 부분 과제만 |

### 행동·메타 (보너스, 주제 공명)
| # | 논문 | 살아있는 팔 | 유형 | 재실행 메모 |
|---|---|---|---|---|
| T16 | **Tag Questions and the Generational Reversal of Sycophancy Across 45 Models** (2026) | gpt-4-turbo | 대상 | "세대 간 역전" 주장 — 판정에 이상적, 비용 $1 수준 |
| T17 | **AIRepr: Reproducibility of LLMs in Data Science** (EMNLP 2025, 1,032 과제) | o3-mini | 대상 | 재현성 메타 주제 |
| T18 | **Situational Awareness Dataset (SAD)** (2024, 13k 문항) | gpt-4-turbo (부분) | 대상 | 안전-양성(benign). Claude 팔 사망 |
| T19 | Inductive Coding with ChatGPT (2024, 사전등록, OSF CC-BY) | gpt-4o (스냅숏 확인) | 주석자 | 온도×반복 설계 — 방법론 공명 |
| T20 | Decoy Dilemma 신뢰도 판단 (2025) | gpt-4o-2024-05-13 | 대상/인지편향 | 인간 실험 대조. 자료 공개 확인 필요 |

### 제외·주의
- 환자 데이터 의존(PDAC CT 보고서, SDoH 임상노트, CliBench/MIMIC): 데이터 비공개 → 재실행 불가, C
- 모델 리포트·서베이 잔존(DeepSeek-Coder-V2, Aya 23, UltraMedical, Reasoning4Sciences): X
- 무관 FP 3건(MEG 자폐, 메타분석 효과크기, 시각 작업기억) — 전문 매칭 오염 표본
- 탈옥·유해 프롬프트 계열은 상용 API 실행 제외 (이용약관)

## 도메인 배분 (v1 A급 + v2 보충, 살아있는 팔 기준)

| 도메인 | v1 생존 | v2 보충 | 합계 후보 |
|---|---|---|---|
| 의학·생의학 | 3–4 | 9 | 12–13 |
| 생물정보학 | 0 | 1 | 1 (T1 — 추가 탐색 필요) |
| 재료·화학 | 0 | 5 | 5 |
| 심리·인지 | 4 | 2 | 6 |
| 사회과학 | 5 | 1 | 6 |
| NLP·평가과학 | 6 | 3 | 9 |
| SE·에이전트 | 3 | 0 | 3 |

P0 최종 20–30편은 위에서 도메인당 2–5편씩 사용자가 선택. 재실행 비용은 대부분 논문당 $2–15 수준(MCQ·분류형 다수).
