# P0 셔틀리스트 v1 — 초록 전수 검토 기반 (2026-09-01)

triage v1의 155편 초록을 전량 검토한 결과. 의존 유형과 Tier 적합성 기준으로 분류했다.
분포: **A급(P0 유력) 28편 / B급(경량 재실행 후보) ~85편 / C급(코딩만·복원 곤란) ~30편 / X(제외: 모델 리포트·서베이 잔존·무관) ~12편.**

판정 기준 — A급: 죽는 모델의 결과가 핵심 주장 + LLM 단계 분리 가능 + 프롬프트/데이터 공개 정황.
표기: [유형] 주석자/심사자/모의피험자/대상/구성요소.

## A급 후보 28편 (도메인 층화 순)

### 의학·생의학 (7)
1. **Durably reducing conspiracy beliefs through dialogues with AI** (Science 2024) — [대상/개입] GPT-4 Turbo(10/23 사망). 모델 측 재실행 = 반박 대화 재생성·논증 품질 대조. OSF 아티팩트 공개. **P0 플래그십 후보**
2. **MEDEC: Medical Error Detection and Correction** — [대상] o1-preview 포함 평가 + 의사 2인 인간 기준선. 3,848 임상 텍스트
3. **DeepSeek-R1 vs OpenAI o1 in Ophthalmology** — [대상] o1(10/23 사망) API + R1 오픈 대조. 300 케이스, 비용 분석 포함
4. **Collaborative LLMs for automated data extraction in living systematic reviews** — [주석자] GPT-4-turbo + Claude-3-Opus 2-리뷰어 워크플로
5. **The Impact of Temperature on Extracting Information From Clinical Trial Publications** — [주석자/방법론] GPT-4o 온도 민감도 — 재현성 방법론 주제와 공명
6. **Assessing DxGPT: Diagnosing Rare Diseases** — [대상] GPT-4/Claude 3/Gemini 1.5 Pro, RAMEDIS 공개 데이터
7. **Human vs AI: Clinical Chemistry MCQ (GPT-4/3.5/Bing/Bard)** — [대상] 사망 모델 다수 + 학생 기준선 (문항 저작권 확인 필요)

### 심리·인지과학 (5)
8. **When ELIZA meets therapists: A Turing test for the heart and mind** — [대상] 사전등록, N=830 인간 평가. 모델 측 응답 재생성 가능
9. **Validating the use of LLMs for psychological text classification** — [주석자] GPT-4o, 과제 3종 × N=1,500 수기 라벨 — 타당성 방법론
10. **Divergent Creativity in Humans and LLMs** — [대상] 10만 명 인간 대조군, 확산적 사고 과제
11. **Do LMs Exhibit the Same Cognitive Biases in Problem Solving as Human Learners?** — [대상] 아동 인지편향 대조
12. **PATIENT-ψ: LLMs Simulate Patients for Training Mental Health Professionals** — [모의피험자] 유형 다양성 확보용

### 사회과학·거버넌스 (6)
13. **Questioning the Survey Responses of LLMs** — [대상/방법론 비판] 43개 모델, 실리콘 샘플링 비판 — 순서·라벨 편향
14. **Accuracy and Political Bias of News Source Credibility Ratings by LLMs** — [주석자/대상] 9개 모델 vs 인간 전문가
15. **LLM Voting: Human Choices and AI Collective Decision-Making** — [모의피험자] GPT-4·LLaMA-2 vs 인간 투표 실험
16. **Cultural Bias and Cultural Alignment of LLMs** — [대상] OpenAI 5세대 모델 vs 세계가치조사
17. **AI Conversational Interviewing** — [구성요소/모의] LLM 설문 인터뷰어
18. **GenAI and Power Imbalances in Global Education** — [대상] GPT-4 Turbo·Gemini 1.5 제로샷 산출 비교 (질적 — 재생성 가능)

### NLP·평가과학 (7)
19. **Humans or LLMs as the Judge? A Study on Judgement Bias** — [심사자 검증] 심사자 타당성 주제와 직결
20. **Encouraging Divergent Thinking through Multi-Agent Debate** — [구성요소/대상] MAD 프레임워크, 코드 공개
21. **Let Me Speak Freely? Format Restrictions on LLM Performance** — [대상] 구조화 출력이 추론 저하 — 행동 발견
22. **Does Prompt Formatting Have Any Impact on LLM Performance?** — [대상] 템플릿 민감도 최대 40% — 방법론 취약성
23. **The Good, The Bad, and The Greedy: Evaluation Should Not Ignore Non-Determinism** — [대상/메타평가] 비결정성 — 우리 주제와 공명
24. **Examining the robustness of LLM evaluation to distributional assumptions** — [메타평가]
25. **Length-Controlled AlpacaEval / Replacing Judges with Juries (PoLL)** — [심사자 방법론] 둘 중 택1
26. **TopicGPT** — [주석자/구성요소] 전산사회과학 도구
27. **Evaluating Very Long-Term Conversational Memory of LLM Agents (LoCoMo)** — [대상]

### SE·에이전트 (3)
28. **Agentless** — [구성요소] GPT-4o, 단순 3단계 파이프라인, 편당 재실행 비용 $0.70 — 저비용 재실행의 이상적 사례
29. **TravelPlanner** — [대상] GPT-4 성공률 0.6% — 유명 부정 결과의 세대 간 생존 검정
30. **LLMs Assist NLP Researchers: Critique Paper (Meta-)Reviewing** — [심사자] 메타사이언스 접점

## 검토 중 발견한 데이터 품질 신호

- **중복 3쌍 잔존**: MAD, 문화 MT, LLM-AMT의 arXiv/출판본 쌍 — 셔틀리스트 확정 시 출판본 유지
- **메타데이터 오염 2건**: W4401306886(제목-초록 불일치), W4392616695(Chatbot Arena 제목에 다른 초록) — OpenAlex 병합 오류, 의존 분류 파이프라인에 제목-초록 일치성 검사 추가할 것
- **명백한 FP 1건**: W4407261874 "Playful brains"(노화 신경과학) — 전문 매칭 오염의 실물 표본, 논문에 예시로 인용 가치
- **W4400141990**: 제목 "AI Benchmark Half-Life in Recursive Corpora"인데 초록은 LiveBench — 제목 진위 확인 필요 (용어 충돌 점검)

## 다음 단계

1. 사용자 트리아지: 위 30편 중 P0 최종 20–30 확정 (탈락 사유 메모)
2. 확장 스캔(진행 중) 완료 후 Tier B 풀 재구성
3. 확정본에 핵심 주장 카드 작성 → 재실행 하네스 개발
