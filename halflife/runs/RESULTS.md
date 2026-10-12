# 재실행 결과 현황 (지출 기록 2026-10-04 기준, 자동 생성)

`python scripts/results_report.py`가 데이터 파일에서 다시 만든다. 분류는 공저자 3인 판정의 다수결(data/judgment_final.csv, 2026-10-11)이고 자동 가안은 class_provisional 열에 남아 있다. 그림·표의 출처와 해석은 `PAPER_OUTLINE.md`와 `SUPPLEMENTARY.md`, 편차 원인은 `SUPPLEMENTARY_TABLES.md` 표 S4에 있다.

## 한눈에

| 항목 | 결과 | 비용 |
|---|---|---|
| Tier A (저장소 기반 전체 절차, 25편) | 생존 12, 부분 12, 판정 1 | $371.59 |
| Tier B (프롬프트 수준, 논문당 사전 지정 수치 1개, 86편) | 재현 54, 근접 10, 편차 20, 확인 필요 2 | $1,097.11 |
| 후속 전환, 벤더 지정 대체 모델 (실행 74, 채점 가능 72편) | 재현 25, 근접 9, 편차 38, 확인 필요 1 | $298.91 (gpt-4.1 포함, OpenAI) |
| 후속 전환, gpt-4.1 (실행 49, 채점 가능 48편) | 재현 21, 근접 4, 편차 23, 확인 필요 1 | 위에 포함 |
| 후속 전환, 공개 가중치 Llama 3.3 70B (실행 67, 채점 가능 64편) | 재현 19, 근접 2, 편차 43, 확인 필요 2 | $40.47 (Together) |
| 후속 전환, 타사 폐쇄형 API Gemini 3.8 Flash (실행 67, 채점 가능 66편) | 재현 17, 근접 6, 편차 43 | $92.80 (Google) |
| 프롬프트 변형 2건 | 아래 절 | $10.49 |
| 강건성 실행 (네 조건 반복 20편씩, BF16 점검 12편, 문구 점검 18편×2, 저장소 기반 후속 5편, 형식 맞춤 3편×2, 온도 점검 4편; 표 S27~S33, S38; 임계값 스윕 표 S39; 트리아지 교차 판정 60건 표 S40~S41, US$2.57) | 호출 간 범위 중앙값 0.16~0.48점, BF16에서 편차 6건 유지; 바꿔 쓴 지시문 하나당 이동 중앙값 0.96점(36건 중 5점 초과 7건), 저장소 기반 20개 주장 중 편차 11건(이동 중앙값 8.3점); 형식 맞춤 뒤에도 보고값 복원 0/3; temperature 1.0에서 분류 변화 1/4 | $336.34 |
| 같은 스냅숏 대조군 (20편, 4~15일 뒤 같은 모델) | 표 S20 | $53.48 |
| 지출 누계 | | $2,303.76 |

단위는 논문이다. 사망 전 재실행은 고유 논문 107편이고, 그중 4편은 두 절차로 모두 돌렸다(같은 주장을 저장소 기반과 프롬프트 수준으로 각각 재실행한 타당성 점검: W4403885225, W4406880877, W4411119263, W4416035547). Tier A의 주장 단위 95건은 그림 3(forest plot)의 점 개수이며 아래 주장별 표에 있다.

## 분석 집합 장부 (후속 전환)

각 조건의 분모가 어떻게 줄어드는지와 그 이유. 본문과 그림 5, 표 S9는 이 이름(후보·실행·전환 가능·채점 가능)을 그대로 쓴다.

| 분석 집합 | 벤더 지정 대체 모델 | gpt-4.1 | 공개 가중치 Llama 3.3 70B | Gemini 3.8 Flash | 빠진 이유 |
|---|---|---|---|---|---|
| 후보 | 86 | 57 | 86 | 86 | gpt-4.1 조건은 원 모델이 GPT-4급(gpt-4-turbo, gpt-4o)인 논문만 대상 |
| 실행 | 74 | 49 | 67 | 67 | 벤더: 1차 61편 중 호출 수가 적은 49편과 2차 25편 전부, 12편은 후속 모델 가격이 편당 $25~125라 미실행. gpt-4.1: 벤더 조건과 짝을 이룬 논문 우선, 채용 논문 1편은 계정 정지로 중단. 공개 가중치: 제3자 계정 정책 위험으로 편향 감사 6편과 OR-Bench 제외; OpenAI 2단계 판정이 필요한 2편은 계정 복구 뒤(9/21) 판정 단계를 돌려 채움. Gemini: 공개 가중치 조건과 같은 67편 |
| 전환 가능 | 73 | 49 | 66 | 66 | 자기 식별 과제 1편은 어느 후속 모델에도 정답 보기가 없어 전환이 성립하지 않음 |
| 채점 가능 | 72 | 48 | 64 | 66 | 응답의 절반 넘게 논문 파서가 요구한 형식이 아님(벤더 1, gpt-4.1 1, 공개 2, Gemini 0) |
| 5점 넘게 이동 | 38 (53%) | 23 (48%) | 43 (67%) | 43 (65%) | 분모는 채점 가능 |

## Tier A: 저장소 기반 프로토콜 전체 재실행

| 논문 | 모델 | 호출 | 비용 | 판정 |
|---|---|---|---|---|
| Knowing When to Abstain: Medical LLMs Under Clinical Uncerta | gpt-4.1-nano-2025-04-14 | 7,049 | $0.18 | 부분 생존 |
| Accuracy and Political Bias of News Source Credibility Ratin | gpt-4-turbo-2024-04-09 | 7,523 | $27.47 | 부분 생존 |
| Cultural bias and cultural alignment of large language model | gpt-4-turbo-2024-04-09 | 10,800 | $13.20 | 부분 생존 |
| MEDEC: A Benchmark for Medical Error Detection and Correctio | gpt-4o-2024-05-13 | 1,791 | $3.87 | 부분 생존 |
| The Impact of Temperature on Extracting Information From Cli | gpt-4o-2024-05-13 + gpt-4o-mini-2024-07-18 | 38,978 | $58.02 | 부분 생존 |
| Me, Myself, and AI: The Situational Awareness Dataset (SAD)  | gpt-4o-2024-05-13 | 8,715 | $8.16 | 부분 생존 |
| Humans or LLMs as the Judge? A Study on Judgement Bias | gpt-4o-2024-05-13 | 4,260 | $15.62 | 부분 생존 |
| The Good, The Bad, and The Greedy: Evaluation of LLMs Should | gpt-4-turbo-2024-04-09 | 5,740 | $30.13 | 부분 생존 |
| Agent-to-Agent Theory of Mind: Testing Interlocutor Awarenes | gemini-3.8-flash, gpt-5.6-terra, meta-llama/Llama-3.3-70B-In | 600 | $7.00 | 부분 생존 |
| Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge | gemini-3.8-flash, gpt-4-turbo-2024-04-09, gpt-4.1-2025-04-14 | 1,500 | $46.41 | 부분 생존 |
| Rethinking Table Instruction Tuning | gpt-4-turbo-2024-04-09 | 2,445 | $16.50 | 부분 생존 |
| AIRepr: An Analyst-Inspector Framework for Evaluating Reprod | o3-mini-2025-01-31 | 8,611 | $24.49 | 부분 생존 |
| Benchmarking Large Language Models for Bio-Image Analysis Co | gpt-4-turbo-2024-04-09 | 570 | $5.93 | 생존 |
| Tag Questions and the Generational Reversal of Sycophancy Ac | gpt-4-turbo-2024-04-09 | 960 | $0.35 | 생존 |
| In-Context Molecular Property Prediction with LLMs: A Blindi | gpt-4.1-nano-2025-04-14 | 6,252 | $1.92 | 생존 |
| Pattern Recognition or Medical Knowledge? The Problem with M | ['gpt-4o-2024-05-13', 'gpt-4-turbo-2024-04-09'] | 5,856 | $14.16 | 생존 |
| Assessing DxGPT: Diagnosing Rare Diseases with Various Large | gpt-4-turbo-2024-04-09 | 1,400 | $12.24 | 생존 |
| AgentMisalignment: Measuring the Propensity for Misaligned B | o4-mini-2025-04-16 | 216 | $0.79 | 생존 |
| OffsetBias: Leveraging Debiased Data for Tuning Evaluators | gpt-4o-2024-05-13 | 480 | $1.07 | 생존 |
| TURTLEAI: Benchmarking Multimodal Models for Visual Programm | o3-2025-04-16 | 306 | $5.17 | 생존 |
| ReIFE: Re-evaluating Instruction-Following Evaluation | gpt-4.1-2025-04-14, gpt-4o-2024-05-13 | 2,060 | $48.61 | 생존 |
| People who frequently use ChatGPT for writing tasks are accu | gemini-3.8-flash, gpt-5.6-sol, meta-llama/Llama-3.3-70B-Inst | 300 | $46.14 | 생존 |
| MedXpertQA: Benchmarking Expert-Level Medical Reasoning and  | o1-2024-12-17 + o3-mini-2025-01-31 | 1,928 | $42.24 | 생존 |
| ACCORD: Closing the Commonsense Measurability Gap | gpt-4o-2024-05-13 | 8,592 | $19.89 | 생존 |
| BADGE: BADminton report Generation and Evaluation with LLM | gpt-4-turbo-2024-04-09 | 510 | $5.80 | 판정 불능 |

주장별 값 (원 논문 → 재실행 [95% 구간]; 규칙 x100은 비율을 백분율로 읽음):

| 논문 ID | 주장 | 원 논문 | 재실행 | 메모 |
|---|---|---|---|---|
| T1 | Bio-image code generation: pass@1 | 0.4737 | 0.4807 [0.374, 0.581] |  |
| W7171749161 | Tag Questions: tag effect on agreement | -0.075 | -0.1021 [-0.165, -0.052] | 90% interval as in the paper |
| W7140135941 | MedAbstain: accuracy, no abstain option | 0.5404 | 0.5418 [0.502, 0.58] |  |
| W7140135941 | MedAbstain: accuracy, abstain option | 0.4099 | 0.4113 [0.376, 0.445] |  |
| W7140135941 | MedAbstain: accuracy, distractor + abstain | 0.3688 | 0.3603 [0.325, 0.396] |  |
| W7140135941 | MedAbstain: abstention rate (abstain option) | 0 | 0.025  |  |
| W4362598103 | News credibility: Spearman rho x100 vs expert ratings | 0.6242 | 0.6294 [0.61, 0.648] |  |
| W4362598103 | News credibility: refusal share | 0.4122 | 0.3543  |  |
| W7144391134 | BlindingLLMs: Pearson r x100, 1000-shot | 75.6 | 76.6 [69.2, 82.8] |  |
| W7144391134 | BlindingLLMs: Pearson r x100, 60-shot | 42.9 | 37.6 [21.7, 52.2] |  |
| W7144391134 | BlindingLLMs: Pearson r, 0-shot | 0.407 | 0.406  |  |
| W4402565126 | Cultural bias: distance reduction (107 countries) | 0.9341 | 0.9331 [0.711, 1.14] |  |
| W4402565126 | Cultural bias: share of countries improved | 0.8131 | 0.785  |  |
| W4412887943 | MEDEC: error flag accuracy (vs Table 2 GPT-4o) | 0.6584 | 0.5611 [0.521, 0.6] | MS subset 597/925; GPT-4o-mini row 0.6086 |
| W4412887943 | MEDEC: error sentence accuracy (vs Table 2 GPT-4o) | 0.5665 | 0.4606 [0.42, 0.5] | MS subset 597/925; GPT-4o-mini row 0.4757 |
| W4412945732 | Glianorex gpt-4o: accuracy, en gpt | 0.74 | 0.7576 [0.706, 0.807] |  |
| W4412945732 | Glianorex gpt-4o: accuracy, en claude | 0.72 | 0.7232 [0.664, 0.781] |  |
| W4412945732 | Glianorex gpt-4o: accuracy, fr gpt | 0.69 | 0.7083 [0.649, 0.755] |  |
| W4412945732 | Glianorex gpt-4o: accuracy, fr claude | 0.71 | 0.7188 [0.659, 0.777] |  |
| W4412945732 | Glianorex gpt-4-turbo: accuracy, en gpt | 0.65 | 0.6591 [0.605, 0.717] |  |
| W4412945732 | Glianorex gpt-4-turbo: accuracy, en claude | 0.69 | 0.692 [0.628, 0.749] |  |
| W4412945732 | Glianorex gpt-4-turbo: accuracy, fr gpt | 0.68 | 0.6591 [0.596, 0.712] |  |
| W4412945732 | Glianorex gpt-4-turbo: accuracy, fr claude | 0.68 | 0.6741 [0.613, 0.734] |  |
| W4396768794 | DxGPT: strict top-1 (new vs archived diagnoses, same judge) | 58.5 | 57 [51, 64] | judge-matched comparison; Table 3 with the original judge 54.0 |
| W4396768794 | DxGPT: top-5 (new vs archived diagnoses, same judge) | 69 | 69.5 [63.487, 76] |  |
| W4405408496 | Temperature study gpt-4o: formatted numeric answers, T=0.00 | 98.7 | 98.3936 [97.289, 98.996] | median over 3 pass(es) |
| W4405408496 | Temperature study gpt-4o: formatted numeric answers, T=1.50 | 98.7 | 97.8916 [96.985, 98.695] | median over 1 pass(es) |
| W4405408496 | Temperature study gpt-4o: formatted numeric answers, T=1.75 | 95.6 | 96.2851 [95.08, 97.39] | median over 1 pass(es) |
| W4405408496 | Temperature study gpt-4o: formatted numeric answers, T=2.00 | 89.2 | 86.8474 [84.739, 88.855] | median over 3 pass(es) |
| W4405408496 | Temperature study gpt-4o: MAPE of formatted answers, T=0.00 | 1.7 | 1.4012 [0.844, 2.101] |  |
| W4405408496 | Temperature study gpt-4o: MAPE of formatted answers, T=2.00 | 1 | 1.8047 [0.898, 4.221] |  |
| W4405408496 | Temperature study gpt-4o-mini: formatted numeric answers, T=2.00 | 90.2 | 90.1606 [88.253, 91.87] |  |
| W4400435289 | SAD-mini facts_human_defaults: accuracy | 0.75 | 0.7975 [0.774, 0.82] | substitute snapshot gpt-4o-2024-05-13 |
| W4400435289 | SAD-mini facts_llms: accuracy | 0.8916 | 0.8755 [0.835, 0.916] | substitute snapshot gpt-4o-2024-05-13 |
| W4400435289 | SAD-mini influence: accuracy | 0.6781 | 0.7031 [0.65, 0.756] | substitute snapshot gpt-4o-2024-05-13 |
| W4400435289 | SAD-mini stages_full: accuracy | 0.3375 | 0.3387 [0.305, 0.37] | substitute snapshot gpt-4o-2024-05-13 |
| W4400435289 | SAD-mini stages_oversight: accuracy | 0.4575 | 0.4575 [0.407, 0.498] | substitute snapshot gpt-4o-2024-05-13 |
| W4400435289 | SAD-mini SAD-mini/paper_unweighted: accuracy | 0.623 | 0.632 [0.614, 0.651] | substitute snapshot gpt-4o-2024-05-13 |
| W4400435289 | SAD-mini SAD-mini/repo_weighted: accuracy | 0.5944 | 0.6053 [0.58, 0.633] | substitute snapshot gpt-4o-2024-05-13 |
| W4404782878 | Judgement bias: attack success rate, factual error | 0.06 | 0.0816 [0.031, 0.139] | substitute snapshot; 6-vote composition assumed |
| W4404782878 | Judgement bias: attack success rate, gender | 0.16 | 0.0947 [0.04, 0.16] | substitute snapshot; 6-vote composition assumed |
| W4404782878 | Judgement bias: attack success rate, reference | 0.32 | 0.3298 [0.234, 0.429] | substitute snapshot; 6-vote composition assumed |
| W4404782878 | Judgement bias: attack success rate, rich content | 0.07 | 0.2421 [0.161, 0.33] | substitute snapshot; 6-vote composition assumed |
| W4411120389 | Greedy vs sampling (HumanEval): greedy pass@1, median of 3 repeats | 89.6 | 88.4146 [82.927, 92.683] |  |
| W4411120389 | Greedy vs sampling (HumanEval): sampled pass@1, mean of 32 runs | 84.1 | 86.9284 [83.078, 90.454] | paper states N=128; the released archive holds 32 runs |
| W4411120389 | Greedy vs sampling (HumanEval): greedy minus sampled gap | 5.5 | 1.4863 [-1.543, 4.212] |  |
| W4416074906 | AgentMisalignment: misalignment score, persona None | 0.208 | 0.2083 [0.042, 0.417] | 6 scenarios per persona |
| W4416074906 | AgentMisalignment: misalignment score, persona Analyst | 0.208 | 0.2083 [0.042, 0.375] | 6 scenarios per persona |
| W4416074906 | AgentMisalignment: misalignment score, persona Executor | 0.25 | 0.25 [0.083, 0.417] | 6 scenarios per persona |
| W4416074906 | AgentMisalignment: misalignment score, persona Inventor | 0.208 | 0.25 [0.083, 0.417] | 6 scenarios per persona |
| W4416074906 | AgentMisalignment: misalignment score, persona Custodian | 0.208 | 0.25 [0.083, 0.417] | 6 scenarios per persona |
| W4416074906 | AgentMisalignment: misalignment score, persona Pragmatist | 0.25 | 0.2083 [0.083, 0.333] | 6 scenarios per persona |
| W4416074906 | AgentMisalignment: misalignment score, persona row_mean | 0.222 | 0.2292 [0.167, 0.299] | 6 scenarios per persona |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, length | 91.2 | 91.2 [76.471, 100] | n=34 pairs x 2 orders |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, concreteness | 92.9 | 92.9 [82.143, 100] | n=28 pairs x 2 orders |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, empty reference | 50 | 61.5 [37.179, 82.051] | n=26 pairs x 2 orders |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, content continuation | 100 | 100 [100, 100] | n=24 pairs x 2 orders |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, nested instruction | 91.7 | 91.7 [79.167, 100] | n=24 pairs x 2 orders |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, familiar knowledge | 95.8 | 95.8 [87.5, 100] | n=24 pairs x 2 orders |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, total | 86.9 | 88.8 [82.292, 93.958] | n=160 pairs x 2 orders |
| W4400103831 | BADGE: GPT-4 judge score of GPT-4 reports (1-10) | 8.825 | 8.75  | GPT-4 reports regenerated; other writers' released reports re-judged |
| W4400103831 | BADGE: GPT-4 judge score of GPT-3.5 reports (1-10) | 8.625 | 8.2667  | GPT-4 reports regenerated; other writers' released reports re-judged |
| W4400103831 | BADGE: GPT-4 judge score of human reports (1-10) | 7.925 | 7.9083  | GPT-4 reports regenerated; other writers' released reports re-judged |
| W7166808082 | TURTLEAI: symbolic success rate, DSReal (o3) | 40.2 | 34.31 [27.45, 43.14] | 102 tasks x 3 seeds; 30 replies without code |
| W4411119263 | ReIFE: evaluator accuracy vs human preference, macro mean of 4 datasets | 84 | 84.155 [82.157, 86.083] | repository run; prompt-level Tier B run 84.39 |
| W4411119263 | ReIFE: accuracy, llmbar_natural | 95.5 | 95.5  |  |
| W4411119263 | ReIFE: accuracy, llmbar_adversarial | 80.7 | 80.564  |  |
| W4411119263 | ReIFE: accuracy, mtbench | 79.5 | 80.75  |  |
| W4411119263 | ReIFE: accuracy, instrusum | 80.3 | 79.805  |  |
| W4416035547 | Interlocutor awareness: self-identification accuracy, MATH-500 (o4-mini) | 0.64 | 0.94 [0.903, 0.957] | card reads Figure 11 as 0.64; the Tier B config carried 0.93 (open) |
| W4403885225 | Judge bias: verbosity robustness rate (500 fact items) | 0.915 | 0.9495 [0.929, 0.968] | unparsable verdicts dropped (1%) |
| W4403885225 | Judge bias: unperturbed consistency rate (noise floor) | 0.99 | 0.9737 [0.958, 0.986] |  |
| W4406880877 | AI-text detection (o1 zero-shot CoT): true positive rate, 150 AI articles | 54 | 55.3333 [47.343, 63.057] |  |
| W4406880877 | AI-text detection (o1 zero-shot CoT): false positive rate, 150 human articles | 4 | 4 [1.846, 8.451] |  |
| W4412887747 | TAMA: GPT-4-turbo exact-match accuracy, AIT-QA (repository scorer) | 88.57 | 87.9365 [84.233, 91.429] | repository scorer counts containment; strict scorer 0.0 (verbose replies) |
| W4412887747 | TAMA: GPT-4-turbo exact-match accuracy, InfoTabs (repository scorer) | 58.6 | 73 [69.133, 76.667] | repository scorer counts containment; strict scorer 0.0 (verbose replies) |
| W4407012395 | MedXpertQA Text: accuracy, Reasoning (o1-2024-12-17) | 46.24 | 48.0226 [40.113, 55.367] | n=177 |
| W4407012395 | MedXpertQA Text: accuracy, Understanding (o1-2024-12-17) | 39.66 | 40 [27.273, 52.727] | n=55 |
| W4407012395 | MedXpertQA Text: accuracy, Avg (o1-2024-12-17) | 44.67 | 46.1207 [40.086, 52.586] | n=232 |
| W4407012395 | MedXpertQA Text: accuracy, Reasoning (o3-mini-2025-01-31) | 37.63 | 40.3226 [33.32, 47.312] | n=186 |
| W4407012395 | MedXpertQA Text: accuracy, Understanding (o3-mini-2025-01-31) | 36.21 | 32.7586 [20.69, 44.828] | n=58 |
| W4407012395 | MedXpertQA Text: accuracy, Avg (o3-mini-2025-01-31) | 37.3 | 38.5246 [32.377, 44.672] | n=244 |
| W4416034576 | AIRepr: o3-mini overall reproducibility on DiscoveryBench, CoT prompt | 55.23 | 39.75 [33.89, 46.03] | n=239 tasks x 3 seeds; o3-mini as inspector |
| W4416034576 | AIRepr: o3-mini overall reproducibility on DiscoveryBench, RoT prompt | 60.25 | 48.12 [41.42, 54.81] | n=239 tasks x 3 seeds; o3-mini as inspector |
| W4416034576 | AIRepr: RoT minus CoT reproducibility difference (pp) | 5.02 | 8.37 [1.67, 15.06] | paired task-level bootstrap; the card's primary quantity |
| W4399442646 | ACCORD: gpt-4o anti-factual accuracy at 1 reasoning hops (Figure 3 series) | 0.8946 | 0.886 [0.843, 0.926] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |
| W4399442646 | ACCORD: gpt-4o anti-factual accuracy at 2 reasoning hops (Figure 3 series) | 0.5968 | 0.5833 [0.521, 0.648] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |
| W4399442646 | ACCORD: gpt-4o anti-factual accuracy at 3 reasoning hops (Figure 3 series) | 0.2832 | 0.2796 [0.227, 0.334] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |
| W4399442646 | ACCORD: gpt-4o anti-factual accuracy at 4 reasoning hops (Figure 3 series) | 0.1452 | 0.1774 [0.126, 0.238] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |
| W4399442646 | ACCORD: gpt-4o anti-factual accuracy at 5 reasoning hops (Figure 3 series) | 0.1505 | 0.1935 [0.114, 0.258] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |
| W4399442646 | ACCORD: gpt-4o factual accuracy at 1 reasoning hops (Figure 3 series) | 0.9849 | 0.9892 [0.977, 0.999] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |
| W4399442646 | ACCORD: gpt-4o factual accuracy at 2 reasoning hops (Figure 3 series) | 0.8817 | 0.871 [0.833, 0.915] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |
| W4399442646 | ACCORD: gpt-4o factual accuracy at 3 reasoning hops (Figure 3 series) | 0.6846 | 0.6667 [0.599, 0.729] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |
| W4399442646 | ACCORD: gpt-4o factual accuracy at 4 reasoning hops (Figure 3 series) | 0.543 | 0.4731 [0.391, 0.55] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |
| W4399442646 | ACCORD: gpt-4o factual accuracy at 5 reasoning hops (Figure 3 series) | 0.5054 | 0.5054 [0.402, 0.599] | reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap |

## Tier B: 프롬프트 수준 재실행

자동 가안의 분류 규칙: 재현 = 원 값이 재실행 95% 구간 안이거나 차이 2점 이내, 근접 = 5점 이내, 편차 = 그 이상, 확인 필요 = 채점 규칙 미보고. 비율 지표는 백분율 점수로 읽는다.

| 논문 ID | 논문 | 모델 | 지표 | 원 값 | 재실행 | Δ점 | 문항 | 분류 | 메모 |
|---|---|---|---|---|---|---|---|---|---|
| W4416683695 | AI Self-preferencing in Algorithmic Hiring:  | gpt-4-turbo-2024-04-09 | custom | 93 | 14.783 [6.087, 23.478] | -78.2 | 460 | 편차 | A/B order: the paper does not report whether the two resumes were counterbalanced or alway |
| W4411080278 | Temperature-Driven Variability in Emergency  | gpt-4o-2024-05-13 | custom | 100 | 25 [22.4, 27.6] | -75 | 1000 | 편차 | [triage 2026-09-09 g1] Leading diagnoses are the broader parents of the gold labels (hypot |
| W7166872685 | Machine Behavior in Relational Moral Dilemma | o3-mini-2025-01-31 | accuracy | 0.53 | 0.998 [1, 1] | 46.8 | 432 | 편차 | The 27 instances per cell are reconstructed as 3 crime types x 3 closeness paraphrases x 3 |
| W4411119985 | How Inclusively do LMs Perceive Social and M | gpt-4-turbo-2024-04-09 | mean_abs_error | 0.92 | 0.587 [0.455, 0.7] | -33.3 | 100 | 편차 |  |
| W4416035547 | Agent-to-Agent Theory of Mind: Testing Inter | o4-mini-2025-04-16 | accuracy | 0.64 | 0.947 [0.9, 0.99] | 30.7 | 100 | 편차 | the exact reproduction of the repository's 100 MATH-500 indices assumes promptfoo/CCP-sens |
| W7162149911 | Refining and Reusing Annotation Guidelines f | gpt-5-2025-08-07 | custom | 0.46 | 0.268 [0.173, 0.359] | -19.2 | 49 | 편차 | The paper prints the template but not the slot fillers; the values above are the released  |
| W4401545735 | Designing Heterogeneous LLM Agents for Finan | gpt-4o-2024-05-13 | accuracy | 74.57 | 91.593 [90.504, 92.757] | 17 | 2264 | 편차 | [triage 2026-09-09 g1] max_tokens=16 (assumed) truncates 1,404 of 6,792 replies (finish_re |
| W7160514285 | Large Language Models Show Metacognitive Sen | gpt-4.1-nano | accuracy | 0.935 | 0.812 [0.722, 0.88] | -12.3 | 108 | 편차 | The paper reports 0.935 in Table 2 but 0.944 in the cross-model comparison (Sec. 3.7) and  |
| W4416036577 | Cross-domain Rumor Detection via Test-Time A | gpt-4o-2024-05-13 | accuracy | 0.643 | 0.522 [0.477, 0.575] | -12.1 | 400 | 편차 | [triage 2026-09-18] The paper's LLM-baseline protocol is unreported (source-dependent numb |
| W4416034248 | Can LLMs Truly Plan? A Comprehensive Evaluat | gpt-4-turbo-2024-04-09 | custom | 17.65 | 28.758 [22.549, 34.804] | 11.1 | 204 | 편차 | The 1-shot demonstration is our seeded draw; the paper only says the examples were randoml |
| W7166821175 | From Regulatory Approvals to Patents: Cross- | gpt-4-turbo-2024-04-09 | accuracy | 60.1 | 70.655 [67.521, 74.872] | 10.6 | 585 | 편차 | Entity-slot filling is unreported: the released prompt has {device_entities_str} / {patent |
| W7164614711 | I Understand How You Feel: Enhancing Deeper  | gpt-4.1-nano-2025-04-14 | macro_f1 | 51.68 | 41.561 [40.784, 42.426] | -10.1 | 12780 | 편차 |  |
| W4399912745 | ALiiCE: Evaluating Positional Fine-grained C | gpt-4-turbo-2024-04-09 | custom | 47 | 37.598 [35.518, 39.554] | -9.4 | 907 | 편차 | [triage 2026-09-18] A run with the released code's prompt format ('Document [k] Title: T:  |
| W7197053912 | ANCHOR-RE: An Agentic Neuro-Symbolic Framewo | gpt-5-mini-2025-08-07 | custom | 0.654 | 0.575 [0.547, 0.593] | -7.9 | 3211 | 편차 |  |
| W4403556032 | Enhancing Healthcare LLM Trust with Atypical | gpt-4-turbo-2024-04-09 | accuracy | 0.751 | 0.811 [0.795, 0.836] | 6 | 1272 | 편차 |  |
| W4407571428 | The Stochastic Parrot on LLM's Shoulder: A S | gpt-4-turbo-2024-04-09 | accuracy | 41.3 | 35.667 [27, 40] | -5.6 | 200 | 편차 |  |
| W4399911213 | WikiContradict: A Benchmark for Evaluating L | gpt-4-turbo-2024-04-09 | accuracy | 86.7 | 81.111 [76.25, 86.25] | -5.6 | 240 | 편차 |  |
| W4406058598 | Halu-J: Critique-Based Hallucination Judge | gpt-4o-2024-05-13 | accuracy | 0.83 | 0.885 [0.868, 0.904] | 5.5 | 1238 | 편차 |  |
| W4403882451 | Planning in Strawberry Fields: Evaluating an | gpt-4-turbo-2024-04-09 | accuracy | 40.1 | 34.889 [30.5, 38] | -5.2 | 600 | 편차 |  |
| W4415035710 | Do LLMs have a Gender (Entropy) Bias? | gpt-4-turbo-2024-04-09 | custom | 2 | -0.229 [-2.168, 1.878] | -2.2 | 158 | 편차 |  |
| W7161421448 | Identifying implicit bias in LLM-based chat  | gpt-4-turbo-2024-04-09 | custom | 136.59 | 247.032  | 110.4 | 2348 | 확인 필요 | budget: approve the full 250-replicate design (~$180 for both stages) or set task.replicat |
| W7166799942 | CMTD: Cognitive Modeling with Traits and Dis | gpt-4.1-nano-2025-04-14 | accuracy | 42.45 | 13.218 [12.146, 14.828] | -29.2 | 280 | 확인 필요 | [triage 2026-09-09 g1] Scoring of free-text emotion phrases is unreported by the paper: ch |
| W4406975432 | Actions Speak Louder than Words: Agent Decis | gpt-4-turbo-2024-04-09 | custom | 0.513 | 0.561  | 4.8 | 1174 | 근접 | Two-stage run: the action-generation calls go through the runner's --judge stage, so the r |
| W4399404161 | MMLU-Pro: A More Robust and Challenging Mult | gpt-4-turbo-2024-04-09 | accuracy | 63.7 | 67.978 [65.738, 70.218] | 4.3 | 1652 | 근접 |  |
| W4403758464 | LLMs Still Can't Plan; Can LRMs? A Prelimina | gpt-4-turbo-2024-04-09 | accuracy | 40.1 | 35.889 [32, 39.504] | -4.2 | 600 | 근접 |  |
| W4400065264 | Following Length Constraints in Instructions | gpt-4-turbo-2024-04-09 | custom | 49.3 | 53.367 [49.875, 56.858] | 4.1 | 802 | 근접 |  |
| W4404985489 | Variable Extraction for Model Recovery in Sc | gpt-4-turbo-2024-04-09 | custom | 0.491 | 0.452  | -3.9 | 589 | 근접 |  |
| W4403443823 | Science is Exploration: Computational Fronti | gpt-4-turbo-2024-04-09 | custom | 74.8 | 71.482 [69.859, 73.192] | -3.3 | 3737 | 근접 |  |
| W4416035248 | CANDY: Benchmarking LLMs' Limitations and As | gpt-4-turbo-2024-04-09 | accuracy | 72.2 | 75.276 [74.454, 76.097] | 3.1 | 10342 | 근접 |  |
| W4411120580 | QSpell 250K: A Large-Scale, Practical Datase | gpt-4-turbo-2024-04-09 | custom | 0.442 | 0.468 [0.453, 0.483] | 2.7 | 7658 | 근접 | Cost: the full test set is about $131 at the dry-run's estimate (nearer $65 at realistic o |
| W4404792825 | Will LLMs Sink or Swim? Exploring Decision-M | gpt-4o-2024-05-13 | custom | 31.36 | 29 [29, 29] | -2.4 | 10 | 근접 |  |
| W4403570177 | RMB: Comprehensively Benchmarking Reward Mod | gpt-4o-2024-05-13 | accuracy | 0.815 | 0.792 [0.778, 0.807] | -2.3 | 2989 | 근접 |  |
| W7126280993 | Semantic Content Determines Algorithmic Perf | o3-2025-04-16 | custom | 0.4 | 0.537 [0.315, 0.846] | 13.7 | 133 | 재현 | Cost: the 950-1050 and 550-650 ranges send very long lists and o3 answers them with hidden |
| W4415332749 | J4R: Learning to Judge with Equivalent Initi | o1-2024-12-17 | custom | 73.1 | 66 [52, 78] | -7.1 | 100 | 재현 |  |
| W4403574994 | Measuring Spiritual Values and Bias of Large | gpt-4-turbo-2024-04-09 | custom | 52.97 | 46.268 [33.705, 64.882] | -6.7 | 133 | 재현 | Direction of Table 4: the table's column names match the left-hand bars of the test's resu |
| W4404573318 | Chat Bankman-Fried: an Exploration of LLM Al | gpt-4-turbo-2024-04-09 | accuracy | 0.41 | 0.352 [0.305, 0.414] | -5.8 | 295 | 재현 | Turn structure is inferred, not stated: Appendix A.1 narrates three prompts in sequence wh |
| W4416034777 | The Illusion of Randomness: How LLMs Fail to | gpt-4-turbo-2024-04-09 | custom | 0.107 | 0.052 [0.017, 0.159] | -5.5 | 100 | 재현 |  |
| W4411112894 | The Promises and Pitfalls of LLM Annotations | gpt-4-turbo-2024-04-09 | custom | 0.683 | 0.632 [0.598, 0.685] | -5.1 | 1027 | 재현 |  |
| W4414979614 | Overcoming Language Barriers: Multilingual A | gpt-5-2025-08-07 | custom | 0.93 | 0.889 [0.8, 1] | -4.1 | 30 | 재현 |  |
| W4417257719 | EDINET-Bench: Evaluating LLMs on Complex Fin | gpt-5-2025-08-07 | custom | 0.65 | 0.681 [0.632, 0.728] | 3.1 | 451 | 재현 |  |
| W7117377764 | Benchmarking large language models for geolo | o3-2025-04-16 | custom | 23.4 | 20.297 [14.542, 26.655] | -3.1 | 43 | 재현 |  |
| W7134885605 | More Signal vs. More Noise - Comparing Full  | gpt-5-2025-08-07 | accuracy | 0.86 | 0.89 [0.85, 0.93] | 3 | 200 | 재현 |  |
| W4411119490 | Are We Done with MMLU? | gpt-4-turbo-2024-04-09 | custom | 22.7 | 25.627 [22.418, 28.635] | 2.9 | 3000 | 재현 |  |
| W4416034223 | When Instructions Multiply: Measuring and Es | gpt-4o-2024-05-13 | custom | 0.57 | 0.542 [0.472, 0.602] | -2.8 | 216 | 재현 |  |
| W4416036063 | sudoLLM: On Multi-role Alignment of Language | o1-2024-12-17 | accuracy | 89.2 | 91.667 [89.167, 94.167] | 2.5 | 480 | 재현 | The exact 1,500 MMLU test questions of Section 4.1 are not published: DATA.md of github.co |
| W4414494504 | PGxRAG: A Retrieval Augmented Generation sup | gpt-4-turbo-2024-04-09 | accuracy | 80.889 | 78.815 [72.889, 83.556] | -2.1 | 225 | 재현 | [triage 2026-09-09 g1] 22 of 675 replies name no option letter (free-text explanation, or  |
| W4414758400 | Mitigation of Gender and Ethnicity Bias in A | gpt-4-turbo-2024-04-09 | custom | 51.5 | 49.604 [47.667, 50.697] | -1.9 | 25 | 재현 |  |
| W4404781158 | MultiPragEval: Multilingual Pragmatic Evalua | gpt-4-turbo-2024-04-09 | accuracy | 75.28 | 76.944 [70.833, 82.083] | 1.7 | 240 | 재현 |  |
| W4399317891 | OR-Bench: An Over-Refusal Benchmark for Larg | gpt-4-turbo-2024-04-09 | custom | 12.7 | 14.25 [10.781, 19.331] | 1.6 | 269 | 재현 | judge stand-in: the paper's judge is the undated 'GPT-4' (Appendix L/S); metric.judge name |
| W7166852552 | LexGenius: An Expert-Level Benchmark for Lar | gpt-4.1-nano | accuracy | 46.51 | 48.053 [46.998, 49.191] | 1.5 | 8345 | 재현 |  |
| W4400375186 | CEB: Compositional Evaluation Benchmark for  | gpt-4-turbo-2024-04-09 | micro_f1 | 69.5 | 68 [61, 74.5] | -1.5 | 200 | 재현 |  |
| W4403786592 | A Comprehensive Evaluation of Large Language | gpt-4-turbo-2024-04-09 | custom | 39.6 | 38.167 [35.4, 41.6] | -1.4 | 1000 | 재현 |  |
| W7169474262 | The One-Word Census: Answer-Choice Conformit | gpt-4-turbo-2024-04-09 | custom | 40 | 41.398 [38.231, 49.636] | 1.4 | 124 | 재현 | The headline metric of the paper (answer-choice surprisal) is leave-one-out against the ot |
| W4416339332 | "As Eastern Powers, I will veto." : An Inves | o3-mini-2025-01-31 | custom | 65 | 66.326 [54.854, 78.959] | 1.3 | 66 | 재현 |  |
| W4416037849 | CRAB: A Benchmark for Evaluating Curation of | o3-mini-2025-01-31 | custom | 71.22 | 69.905 [68.045, 72.035] | -1.3 | 389 | 재현 |  |
| W4400611869 | Lynx: An Open Source Hallucination Evaluatio | gpt-4-turbo-2024-04-09 | accuracy | 82.2 | 83.435 [79.268, 87.195] | 1.2 | 328 | 재현 |  |
| W7139147531 | LLMs learn scientific taste from institution | gpt-4.1-nano-2025-04-14 | accuracy | 25 | 23.889 [15.833, 30.833] | -1.1 | 120 | 재현 |  |
| W4403885225 | Justice or Prejudice? Quantifying Biases in  | gpt-4-turbo-2024-04-09 | custom | 0.915 | 0.926 [0.902, 0.948] | 1.1 | 1000 | 재현 |  |
| W7135428702 | SommBench: Assessing Sommelier Expertise of  | gpt-4.1-nano-2025-04-14 | accuracy | 0.73 | 0.741 [0.714, 0.767] | 1.1 | 1024 | 재현 |  |
| W4402345509 | LAB-Bench: Measuring Capabilities of Languag | gpt-4-turbo-2024-04-09 | accuracy | 0.12 | 0.131 [0.09, 0.186] | 1.1 | 199 | 재현 |  |
| W4411119343 | Are LLM-Judges Robust to Expressions of Unce | gpt-4-turbo-2024-04-09 | accuracy | 83.8 | 82.741 [78.934, 86.294] | -1.1 | 394 | 재현 | [triage correction 2026-09-19] The triage record names "450 Correct samples"; that is the  |
| W7106207151 | Syn-STARTS: Synthesized START Triage Scenari | gpt-4-turbo-2024-04-09 | accuracy | 0.72 | 0.71 [0.574, 0.815] | -1 | 54 | 재현 | One of the 54 cases has an empty narrative (row index 1). The authors skip it and score it |
| W7166837475 | Large Language Models Require Curated Contex | o3-mini-2025-01-31 | macro_f1 | 0.27 | 0.26 [0.246, 0.273] | -1 | 4412 | 재현 |  |
| W7144391352 | CALRK-Bench: Evaluating Context-Aware Legal  | gpt-5-2025-08-07 | accuracy | 0.754 | 0.763 [0.717, 0.817] | 0.9 | 279 | 재현 |  |
| W7140084705 | Quantifying Data Contamination in Psychometr | gpt-4.1-nano-2025-04-14 | macro_f1 | 0.92 | 0.913 [0.85, 0.962] | -0.7 | 138 | 재현 |  |
| W4400434899 | Are Large Language Models Strategic Decision | gpt-4-turbo-2024-04-09 | accuracy | 25.5 | 26.208 [23.5, 29.375] | 0.7 | 800 | 재현 |  |
| W4403580619 | Evaluating Gender Bias of LLMs in Making Mor | gpt-4-turbo-2024-04-09 | custom | 0.177 | 0.17 [0.15, 0.197] | -0.7 | 1816 | 재현 | The two calls of a pair must both survive the runner's cost cap or the pair drops out of t |
| W4415270561 | Diff-XYZ: A Benchmark for Evaluating Diff Un | gpt-4.1-nano-2025-04-14 | exact_match | 0.38 | 0.373 [0.343, 0.402] | -0.7 | 1000 | 재현 |  |
| W4406880877 | People who frequently use ChatGPT for writin | o1-2024-12-17 | accuracy | 54 | 54.667 [46.667, 62.667] | 0.7 | 150 | 재현 | 2026-09-09: duplicate item ids mis-paired replies; runner now forces unique ids and pairs  |
| W7131319772 | Can Large Language Models Replace Human Code | gpt-5-mini-2025-08-07 | accuracy | 99 | 98.333 [97.5, 99] | -0.7 | 1000 | 재현 |  |
| W7140138327 | ReMedQA: Are We Done With Medical Multiple-C | gpt-5-mini-2025-08-07 | accuracy | 94.4 | 93.752 [92.693, 95.393] | -0.6 | 1259 | 재현 |  |
| W4399911093 | Leveraging Large Language Models to Measure  | gpt-4-turbo-2024-04-09 | custom | 90.24 | 90.873 [89.131, 92.928] | 0.6 | 100 | 재현 | The paper averages five runs at the API default temperature; the harness runs three seeds, |
| W4410110677 | Large Language Models for Supporting Clear W | o1-2024-12-17 | accuracy | 0.97 | 0.964 [0.94, 0.984] | -0.6 | 249 | 재현 |  |
| W4403370432 | An Evaluation of Requirements Modeling for C | gpt-4-turbo-2024-04-09 | custom | 48 | 48.588 [46.42, 50.402] | 0.6 | 1383 | 재현 |  |
| W4399911276 | Whiteboard-of-Thought: Thinking Step-by-Step | gpt-4o-2024-05-13 | accuracy | 19.6 | 20 [14.8, 24.4] | 0.4 | 250 | 재현 |  |
| W4411119263 | ReIFE: Re-evaluating Instruction-Following E | gpt-4o-2024-05-13 | custom | 84 | 84.393 [81.208, 87.232] | 0.4 | 2060 | 재현 |  |
| W4407374917 | Large language models possess some ecologica | gpt-4o-2024-05-13 | custom | 78 | 77.63 [71.837, 79.388] | -0.4 | 100 | 재현 |  |
| W4416034345 | Unlocking Legal Knowledge: A Multilingual Da | o3-mini-2025-01-31 | rouge_l | 18.21 | 18.507 [18.057, 18.698] | 0.3 | 852 | 재현 |  |
| W4406058562 | Applicability of Large Language Models and G | gpt-4-turbo-2024-04-09 | rouge_l | 0.198 | 0.201 [0.195, 0.207] | 0.3 | 100 | 재현 |  |
| W4404314294 | DisasterQA: A Benchmark for Assessing the pe | gpt-4-turbo-2024-04-09 | accuracy | 0.817 | 0.819 [0.796, 0.852] | 0.2 | 707 | 재현 |  |
| W7134094238 | BioLLMAgent: A Hybrid Framework with Enhance | gpt-4o-2024-05-13 | custom | 0.002 | 0 [0, 0] | -0.2 | 30 | 재현 |  |
| W4404782525 | Characterizing LLM Abstention Behavior in Sc | gpt-4o-2024-05-13 | accuracy | 61.2 | 61.333 [56.6, 65.2] | 0.1 | 500 | 재현 |  |
| W4411119711 | FaithBench: A Diverse Hallucination Benchmar | gpt-4-turbo-2024-04-09 | custom | 55.96 | 56.09 [53.409, 58.36] | 0.1 | 750 | 재현 | The prompt is external to the paper. It is taken from the FaithBench authors' own released |
| W7140953907 | How Utilitarian Are OpenAI's Models Really?  | o3-mini-2025-01-31 | accuracy | 100 | 99.9 [99.7, 100] | -0.1 | 1000 | 재현 |  |
| W4412888118 | Nunchi-Bench: Benchmarking Language Models o | gpt-4o-2024-05-13 | accuracy | 96.7 | 96.774 [90.323, 100] | 0.1 | 31 | 재현 |  |
| W7159577685 | Breaking the Chains of Probability: Neutroso | gpt-4-turbo-2024-04-09 | custom | 1.36 | 1.416 [1.312, 1.596] | 0.1 | 25 | 재현 |  |

## 후속 모델 전환

같은 문항·프롬프트·채점으로 모델만 바꿨다. 벤더 지정 대체 모델은 OpenAI 단종 페이지의 대체 모델(gpt-5.6-sol/terra/luna, 기본 설정), gpt-4.1은 GPT-4 계열의 비추론 후속. 문항당 1회 실행. 분류는 원 보고값 기준이고 괄호는 사망 전 베이스라인 기준.

| 논문 ID | 논문 | 원 값 | 베이스라인 | 벤더 지정 대체 모델 | gpt-4.1 | 공개 가중치 Llama 3.3 70B | Gemini 3.8 Flash |
|---|---|---|---|---|---|---|---|
| W4399911276 | Whiteboard-of-Thought: Thinking Step-by- | 19.6 | 20 | 69.942 [63.006, 76.879] 편차 (편차) | 15.2 [10.8, 19.6] 재현 (근접) | 0 [0, 0] 확인 필요 (확인 필요) · format non-compliance: 250 of 250 replies lack the | 80 [75.2, 84.8] 편차 (편차) |
| W4400065264 | Following Length Constraints in Instruct | 49.3 | 53.367 | 12.968 [10.599, 15.337] 편차 (편차) | 8.105 [6.234, 10.1] 편차 (편차) | 0.623 [0.125, 1.247] 편차 (편차) | 13.092 [10.723, 15.461] 편차 (편차) |
| W4400375186 | CEB: Compositional Evaluation Benchmark  | 69.5 | 68 | 94.118 [90.441, 97.794] 편차 (편차) | 83 [77.5, 88.5] 편차 (편차) | - | - |
| W4400434899 | Are Large Language Models Strategic Deci | 25.5 | 26.208 | 50.552 [46.958, 54.282] 편차 (편차) | 37.856 [34.328, 41.52] 편차 (편차) | 50 [46.5, 53.625] 편차 (편차) | 50 [46.625, 53.25] 편차 (편차) |
| W4400611869 | Lynx: An Open Source Hallucination Evalu | 82.2 | 83.435 | 90.784 [88.431, 93.333] 편차 (편차) | 83.212 [79.562, 86.861] 재현 (재현) | 72.324 [69.297, 75.243] 편차 (편차) | 88.283 [86.361, 90.303] 편차 (근접) |
| W4401545735 | Designing Heterogeneous LLM Agents for F | 74.57 | 91.593 | 91.418 [90.114, 92.613] 편차 (재현) | 91.299 [90.15, 92.447] 편차 (재현) | 79.638 [77.871, 81.272] 편차 (편차) | 95.671 [94.832, 96.511] 편차 (근접) |
| W4402345509 | LAB-Bench: Measuring Capabilities of Lan | 0.12 | 0.131 | 0.538 [0.455, 0.615] 편차 (편차) | 0.392 [0.322, 0.462] 편차 (편차) | 0.322 [0.256, 0.387] 편차 (편차) | 0.492 [0.422, 0.558] 편차 (편차) |
| W4403758464 | LLMs Still Can't Plan; Can LRMs? A Preli | 40.1 | 35.889 | 100 [100, 100] 편차 (편차) | 36.333 [32.667, 40.171] 재현 (재현) | 60.333 [56.5, 64.337] 편차 (편차) | 99.5 [98.833, 100] 편차 (편차) |
| W4403882451 | Planning in Strawberry Fields: Evaluatin | 40.1 | 34.889 | 100 [100, 100] 편차 (편차) | 36.333 [32.5, 40.167] 재현 (재현) | 61.5 [57.5, 65.004] 편차 (편차) | 99.667 [99.167, 100] 편차 (편차) |
| W4403885225 | Justice or Prejudice? Quantifying Biases | 0.915 | 0.926 | 0.987 [0.974, 0.997] 편차 (편차) | 0.99 [0.982, 0.998] 편차 (편차) | 0.97 [0.954, 0.984] 편차 (근접) | 0.978 [0.964, 0.99] 편차 (편차) |
| W4404314294 | DisasterQA: A Benchmark for Assessing th | 0.817 | 0.819 | 0.919 [0.895, 0.942] 편차 (편차) | 0.873 [0.837, 0.907] 편차 (편차) | 0.84 [0.812, 0.868] 재현 (재현) | 0.901 [0.878, 0.922] 편차 (편차) |
| W4404573318 | Chat Bankman-Fried: an Exploration of LL | 0.41 | 0.352 | 0 [0, 0] 편차 (편차) | 0.008 [0, 0.019] 확인 필요 (확인 필요) · format non-compliance: 246 of 369 replies lack the | 0.138 [0.108, 0.168] 편차 (편차) | 0 [0, 0] 편차 (편차) |
| W4404781158 | MultiPragEval: Multilingual Pragmatic Ev | 75.28 | 76.944 | 87.124 [82.403, 91.416] 편차 (편차) | 67.083 [61.25, 72.917] 편차 (편차) | 77.083 [71.667, 82.083] 재현 (재현) | 88.75 [85, 92.5] 편차 (편차) |
| W4404782525 | Characterizing LLM Abstention Behavior i | 61.2 | 61.333 | 78.2 [74.6, 81.8] 편차 (편차) | 75.2 [71.395, 79] 편차 (편차) | 75.6 [71.8, 79.4] 편차 (편차) | 68 [63.995, 72] 편차 (편차) |
| W4406058598 | Halu-J: Critique-Based Hallucination Jud | 0.83 | 0.885 | 0.901 [0.881, 0.922] 편차 (재현) | 0.884 [0.865, 0.903] 편차 (재현) | 0.887 [0.869, 0.905] 편차 (재현) | 0.897 [0.88, 0.914] 편차 (재현) |
| W4406880877 | People who frequently use ChatGPT for wr | 54 | 54.667 | 100 [100, 100] 편차 (편차) | - | 8 [4, 12.667] 편차 (편차) | 100 [100, 100] 편차 (편차) |
| W4406975432 | Actions Speak Louder than Words: Agent D | 0.513 | 0.561 | 0.216  편차 (편차) | 0.215  편차 (편차) | - | - |
| W4407571428 | The Stochastic Parrot on LLM's Shoulder: | 41.3 | 35.667 | 80.5 [75, 86] 편차 (편차) | 47.5 [41, 54.5] 재현 (편차) | 34 [27.5, 40] 편차 (재현) | 82.5 [77, 87.5] 편차 (편차) |
| W4411119985 | How Inclusively do LMs Perceive Social a | 0.92 | 0.587 | 0.6 [0.495, 0.71] 편차 (재현) | 0.94 [0.82, 1.065] 재현 (편차) | 0.538 [0.385, 0.692] 편차 (재현) | 0.73 [0.625, 0.82] 편차 (편차) |
| W4411120580 | QSpell 250K: A Large-Scale, Practical Da | 0.442 | 0.468 | 0.729 [0.709, 0.751] 편차 (편차) | 0.605 [0.587, 0.623] 편차 (편차) | 0.29 [0.278, 0.302] 편차 (편차) | 0.757 [0.75, 0.765] 편차 (편차) |
| W4414494504 | PGxRAG: A Retrieval Augmented Generation | 80.889 | 78.815 | 92.523 [88.785, 95.794] 편차 (편차) | 84 [79.111, 88.444] 재현 (편차) | 72.889 [66.667, 78.667] 편차 (편차) | 64 [57.778, 70.222] 편차 (편차) |
| W4415035710 | Do LLMs have a Gender (Entropy) Bias? | 2 | -0.229 | -0.482 [-2.542, 1.543] 편차 (재현) | -0.081 [-2.165, 1.974] 편차 (재현) | - | - |
| W4415270561 | Diff-XYZ: A Benchmark for Evaluating Dif | 0.38 | 0.373 | 0.894 [0.875, 0.913] 편차 (편차) | - | 0.623 [0.592, 0.652] 편차 (편차) | 0.98 [0.971, 0.988] 편차 (편차) |
| W4416034223 | When Instructions Multiply: Measuring an | 0.57 | 0.542 | 0.898 [0.856, 0.935] 편차 (편차) | 0.699 [0.639, 0.759] 편차 (편차) | 0.731 [0.671, 0.787] 편차 (편차) | 0.838 [0.792, 0.884] 편차 (편차) |
| W4416034248 | Can LLMs Truly Plan? A Comprehensive Eva | 17.65 | 28.758 | 67.157 [60.294, 73.039] 편차 (편차) | 28.922 [23.039, 34.816] 편차 (재현) | 14.216 [9.804, 19.118] 재현 (편차) | 69.118 [62.255, 75.012] 편차 (편차) |
| W4416036577 | Cross-domain Rumor Detection via Test-Ti | 0.643 | 0.522 | 0.453 [0.4, 0.502] 편차 (편차) | 0.51 [0.463, 0.558] 편차 (재현) | 0.557 [0.51, 0.605] 편차 (재현) | 0.487 [0.438, 0.537] 편차 (재현) |
| W4416339332 | "As Eastern Powers, I will veto." : An I | 65 | 66.326 | 93.808 [87.424, 98.504] 편차 (편차) | - | 56.587 [42.675, 69.43] 재현 (재현) | 93.721 [87.049, 100] 편차 (편차) |
| W4416683695 | AI Self-preferencing in Algorithmic Hiri | 93 | 14.783 | 13.214 [5, 21.786] 편차 (재현) | - | - | - |
| W7126280993 | Semantic Content Determines Algorithmic  | 0.4 | 0.537 | 0.254 [0.195, 0.369] 편차 (편차) | - | 0.337 [0.236, 0.463] 재현 (편차) | 0.25 [0.174, 0.373] 편차 (편차) |
| W7134885605 | More Signal vs. More Noise - Comparing F | 0.86 | 0.89 | 0.935 [0.9, 0.97] 편차 (근접) | - | 0.64 [0.57, 0.705] 편차 (편차) | 0.975 [0.95, 0.995] 편차 (편차) |
| W7135428702 | SommBench: Assessing Sommelier Expertise | 0.73 | 0.741 | 0.913 [0.896, 0.931] 편차 (편차) | - | 0.805 [0.78, 0.828] 편차 (편차) | 0.979 [0.97, 0.987] 편차 (편차) |
| W7140084705 | Quantifying Data Contamination in Psycho | 0.92 | 0.913 | 0.986 [0.961, 1] 편차 (편차) | - | 0.931 [0.88, 0.973] 재현 (재현) | 1 [1, 1] 편차 (편차) |
| W7159577685 | Breaking the Chains of Probability: Neut | 1.36 | 1.416 | 2.028 [1.842, 2.23] 편차 (재현) | 1.372 [1.216, 1.536] 재현 (재현) | 1.612 [1.472, 1.76] 편차 (재현) | 1.818 [1.742, 1.896] 편차 (재현) |
| W7160514285 | Large Language Models Show Metacognitive | 0.935 | 0.812 | 0.657 [0.565, 0.741] 편차 (편차) | - | 0.778 [0.694, 0.852] 편차 (재현) | 0.991 [0.972, 1] 편차 (편차) |
| W7166799942 | CMTD: Cognitive Modeling with Traits and | 42.45 | 13.218 | 5.67 [4.828, 6.552] 편차 (편차) | - | 7.586 [6.59, 8.621] 편차 (편차) | 13.831 [12.529, 15.134] 편차 (재현) |
| W7166821175 | From Regulatory Approvals to Patents: Cr | 60.1 | 70.655 | 75.214 [71.624, 78.632] 편차 (근접) | 60.342 [56.239, 64.274] 재현 (편차) | 75.043 [71.624, 78.462] 편차 (근접) | 90.94 [88.547, 93.167] 편차 (편차) |
| W7166852552 | LexGenius: An Expert-Level Benchmark for | 46.51 | 48.053 | 63.571 [62.552, 64.566] 편차 (편차) | - | 55.53 [54.451, 56.633] 편차 (편차) | 64.685 [63.738, 65.68] 편차 (편차) |
| W7166872685 | Machine Behavior in Relational Moral Dil | 0.53 | 0.998 | 1 [1, 1] 편차 (재현) | - | 0.988 [0.977, 0.998] 편차 (재현) | 0.78 [0.741, 0.817] 편차 (편차) |
| W4411119490 | Are We Done with MMLU? | 22.7 | 25.627 | - | 35.963 [30.797, 40.897] 편차 (편차) | - | - |
| W4403556032 | Enhancing Healthcare LLM Trust with Atyp | 0.751 | 0.811 | 0.35 [0.324, 0.377] 확인 필요 (확인 필요) · format non-compliance: 774 of 1213 replies lack th | - | 0.423 [0.395, 0.45] 확인 필요 (확인 필요) · format non-compliance: 704 of 1272 replies lack th | 0.949 [0.936, 0.961] 편차 (편차) |
| W4416035547 | Agent-to-Agent Theory of Mind: Testing I | 0.93 | 0.947 | 0 [0, 0] 해당없음 (해당없음) · self-identification task: the model must pick itse | - | nan [nan, nan] 해당없음 (해당없음) · self-identification task: the model must pick itse | 0.89 [0.83, 0.95] 해당없음 (해당없음) · self-identification task: the model must pick itse |
| W4399911093 | Leveraging Large Language Models to Meas | 90.24 | 90.873 | 94.509 [93.157, 95.85] 근접 (근접) | 84.16 [80.749, 87.219] 편차 (편차) | 80.309 [75.78, 84.589] 편차 (편차) | 95.259 [93.907, 96.563] 편차 (근접) |
| W4403370432 | An Evaluation of Requirements Modeling f | 48 | 48.588 | 50.793 [48.796, 52.917] 근접 (근접) | 47.736 [45.725, 49.896] 재현 (재현) | 47.45 [45.507, 49.421] 재현 (재현) | 50.468 [48.354, 52.478] 근접 (재현) |
| W4403580619 | Evaluating Gender Bias of LLMs in Making | 0.177 | 0.17 | 0.224 [0.197, 0.25] 근접 (편차) | 0.215 [0.189, 0.24] 근접 (근접) | - | - |
| W4406058562 | Applicability of Large Language Models a | 0.198 | 0.201 | 0.162 [0.145, 0.176] 근접 (근접) | 0.222 [0.217, 0.228] 근접 (근접) | 0.236 [0.229, 0.243] 근접 (근접) | 0.215 [0.209, 0.22] 재현 (재현) |
| W4407374917 | Large language models possess some ecolo | 78 | 77.63 | 81.6 [79.1, 84] 근접 (근접) | 78.367 [76.122, 80.717] 재현 (재현) | 71.351 [67.973, 74.595] 편차 (편차) | 83.838 [81.715, 85.758] 편차 (편차) |
| W4411119711 | FaithBench: A Diverse Hallucination Benc | 55.96 | 56.09 | 60.048 [57.362, 62.75] 근접 (근접) | 55.415 [53.199, 57.491] 재현 (재현) | 57.348 [55.002, 59.979] 재현 (재현) | 60.405 [57.146, 63.44] 근접 (근접) |
| W4412888118 | Nunchi-Bench: Benchmarking Language Mode | 96.7 | 96.774 | 100 [100, 100] 근접 (근접) | 100 [100, 100] 근접 (근접) | 83.871 [70.968, 96.774] 재현 (재현) | 100 [100, 100] 근접 (근접) |
| W4416036063 | sudoLLM: On Multi-role Alignment of Lang | 89.2 | 91.667 | 93.638 [92.242, 94.957] 근접 (재현) | - | 81.667 [79.667, 83.467] 편차 (편차) | 93.595 [92.213, 94.978] 근접 (재현) |
| W7164614711 | I Understand How You Feel: Enhancing Dee | 51.68 | 41.561 | 47.671 [46.813, 48.564] 근접 (편차) | - | 46.354 [45.402, 47.179] 편차 (근접) | 44.908 [43.977, 45.777] 편차 (근접) |
| W4411119263 | ReIFE: Re-evaluating Instruction-Followi | 84 | 84.393 | - | 86.87 [84.097, 89.582] 근접 (재현) | - | - |
| W4399317891 | OR-Bench: An Over-Refusal Benchmark for  | 12.7 | 14.25 | 15.986 [11.905, 20.408] 재현 (재현) | 26.478 [22.108, 30.848] 편차 (편차) | - | - |
| W4399911213 | WikiContradict: A Benchmark for Evaluati | 86.7 | 81.111 | 85.47 [80.769, 89.744] 재현 (재현) | 84.583 [80, 89.167] 재현 (재현) | 85 [80.833, 89.583] 재현 (재현) | 86.667 [82.5, 90.833] 재현 (편차) |
| W4399912745 | ALiiCE: Evaluating Positional Fine-grain | 47 | 37.598 | 46.716 [44.406, 49.173] 재현 (편차) | 45.583 [42.88, 48.202] 재현 (편차) | 49.033 [46.858, 51.231] 재현 (편차) | 47.138 [45.012, 49.406] 재현 (편차) |
| W4403574994 | Measuring Spiritual Values and Bias of L | 52.97 | 46.268 | 55.72 [40.597, 70.651] 재현 (재현) | 52.542 [38.151, 68.988] 재현 (재현) | 57.301 [32.731, 76.638] 재현 (재현) | 50.212 [50, 50.774] 근접 (근접) |
| W4403786592 | A Comprehensive Evaluation of Large Lang | 39.6 | 38.167 | 37.8 [34.8, 40.9] 재현 (재현) | 32.4 [29.4, 35.4] 편차 (편차) | 33.9 [30.898, 36.702] 편차 (근접) | 38.6 [35.697, 41.7] 재현 (재현) |
| W4404792825 | Will LLMs Sink or Swim? Exploring Decisi | 31.36 | 29 | 31.7 [30.4, 32.7] 재현 (근접) | 37.3 [36.5, 38] 편차 (편차) | 10 [10, 10] 편차 (편차) | 30.6 [30.3, 30.9] 재현 (재현) |
| W4404985489 | Variable Extraction for Model Recovery i | 0.491 | 0.452 | 0.479  재현 (근접) | - | 0.42  편차 (근접) | 0.489  재현 (근접) |
| W4410110677 | Large Language Models for Supporting Cle | 0.97 | 0.964 | 0.972 [0.948, 0.992] 재현 (재현) | - | 0.96 [0.936, 0.984] 재현 (재현) | 0.976 [0.956, 0.992] 재현 (재현) |
| W4411080278 | Temperature-Driven Variability in Emerge | 100 | 25 | 99.5 [99, 99.9] 재현 (편차) | 92.7 [91.097, 94.2] 편차 (편차) | 31.3 [28.4, 34.1] 편차 (편차) | 50.3 [47, 53.5] 편차 (편차) |
| W4411112894 | The Promises and Pitfalls of LLM Annotat | 0.683 | 0.632 | 0.712 [0.663, 0.755] 재현 (편차) | 0.72 [0.679, 0.757] 재현 (편차) | 0.667 [0.637, 0.697] 재현 (근접) | 0.777 [0.748, 0.809] 편차 (편차) |
| W4411119343 | Are LLM-Judges Robust to Expressions of  | 83.8 | 82.741 | 81.98 [78.173, 85.533] 재현 (재현) | 82.487 [78.68, 86.041] 재현 (재현) | 85.787 [82.487, 89.086] 재현 (재현) | 85.279 [81.726, 88.832] 재현 (재현) |
| W4414758400 | Mitigation of Gender and Ethnicity Bias  | 51.5 | 49.604 | 53.061 [51.405, 54.277] 재현 (근접) | 51.813 [50.768, 52.775] 재현 (근접) | - | - |
| W4414979614 | Overcoming Language Barriers: Multilingu | 0.93 | 0.889 | 0.897 [0.73, 1] 재현 (재현) | - | 0.788 [0.593, 0.912] 편차 (재현) | 0.929 [0.8, 1] 재현 (재현) |
| W4415332749 | J4R: Learning to Judge with Equivalent I | 73.1 | 66 | 80 [68, 90] 재현 (편차) | - | 52 [38, 66] 편차 (재현) | 92 [84, 98] 편차 (편차) |
| W4416034777 | The Illusion of Randomness: How LLMs Fai | 0.107 | 0.052 | 0.057 [0.017, 0.162] 재현 (재현) | 0.527 [0.457, 0.587] 편차 (편차) | 0.615 [0.569, 0.656] 편차 (편차) | 0.487 [0.407, 0.557] 편차 (편차) |
| W4416037849 | CRAB: A Benchmark for Evaluating Curatio | 71.22 | 69.905 | 69.397 [67.514, 71.355] 재현 (재현) | - | 67.005 [65.431, 68.723] 근접 (근접) | 70.897 [68.84, 73.092] 재현 (재현) |
| W7106207151 | Syn-STARTS: Synthesized START Triage Sce | 0.72 | 0.71 | 0.759 [0.63, 0.87] 재현 (재현) | 0.722 [0.593, 0.833] 재현 (재현) | 0.741 [0.629, 0.852] 재현 (재현) | 0.759 [0.63, 0.87] 재현 (재현) |
| W7117377764 | Benchmarking large language models for g | 23.4 | 20.297 | 19.658 [14.652, 25.086] 재현 (재현) | - | 250.331 [40.563, 473.956] 편차 (편차) | 17.579 [12.045, 23.891] 재현 (재현) |
| W7131319772 | Can Large Language Models Replace Human  | 99 | 98.333 | 99.8 [99.5, 100] 재현 (재현) | - | 93 [91.4, 94.5] 편차 (편차) | 99.8 [99.5, 100] 재현 (재현) |
| W7134094238 | BioLLMAgent: A Hybrid Framework with Enh | 0.002 | 0 | 0 [0, 0] 재현 (재현) | 0 [0, 0] 재현 (재현) | 0 [0, 0] 재현 (재현) | 0 [0, 0] 재현 (재현) |
| W7140138327 | ReMedQA: Are We Done With Medical Multip | 94.4 | 93.752 | 93.309 [91.729, 94.796] 재현 (재현) | - | 85.226 [83.241, 87.212] 편차 (편차) | 97.061 [96.108, 98.014] 근접 (근접) |
| W7140953907 | How Utilitarian Are OpenAI's Models Real | 100 | 99.9 | 100 [100, 100] 재현 (재현) | - | 100 [100, 100] 재현 (재현) | 100 [100, 100] 재현 (재현) |
| W7144391352 | CALRK-Bench: Evaluating Context-Aware Le | 0.754 | 0.763 | 0.76 [0.71, 0.81] 재현 (재현) | - | 0.659 [0.599, 0.713] 편차 (편차) | 0.717 [0.663, 0.767] 재현 (재현) |
| W7162149911 | Refining and Reusing Annotation Guidelin | 0.46 | 0.268 | 0.428 [0.385, 0.469] 재현 (편차) | - | 0.165 [0.137, 0.195] 편차 (편차) | 0.621 [0.584, 0.659] 편차 (편차) |
| W7169474262 | The One-Word Census: Answer-Choice Confo | 40 | 41.398 | 41.129 [37.308, 48.295] 재현 (재현) | 37.903 [35.735, 47.134] 재현 (재현) | 41.935 [37.568, 48.806] 재현 (재현) | 34.677 [34.14, 44.788] 재현 (재현) |

## 프롬프트 변형 (트리아지 가설 검증, 사망 전 모델)

| 변형 | 원 값 | 원 프롬프트 재실행 | 변형 재실행 [95% 구간] | 문항 × 시드 |
|---|---|---|---|---|
| 루머 탐지: base 프롬프트 + 소스 도메인 예시 4개 | 0.643 | 0.522 | 0.575 [0.5, 0.6] | 400 × 3 |
| ALiiCE: 코드 공개본의 프롬프트 형식 | 47 | 37.598 | 37.129 [35.2, 39.1] | 948 × 1 |

## 강건성 점검

후속 비교의 잡음 바닥과 경계를 재는 다섯 가지 점검. 값은 모두 논문 척도의 점수이고 분류는 프롬프트 수준 규칙이다. 자세한 표는 S20, S26~S32.

- **같은 스냅숏 대조군 (표 S20)**: 20편을 생전 문항·요청 본문 그대로 같은 고정 모델에 4~15일 뒤 1회 재실행. 생전 시드 0 값 대비 편차 0/20, |Δ| 중앙값 0.70점, 최대 4.03점.
- **씨앗 분산 반복 (표 S27·S28)**: 조건마다 씨앗 고정 무작위 20편에 같은 요청 본문으로 두 번 더 호출. 호출 간 범위 중앙값 designated replacement 0.31점(5점 초과 1편, 분류 안정 100%), gpt-4.1 0.30점(5점 초과 0편, 분류 안정 95%), open-weight Llama 3.3 70B 0.16점(5점 초과 0편, 분류 안정 95%), Gemini 3.8 Flash 0.48점(5점 초과 0편, 분류 안정 80%).
- **BF16 점검 (표 S29)**: 공개 가중치 조건 11편을 전용 bfloat16 배포에 같은 요청으로 재실행. FP8 대비 |차이| 중앙값 1.25점, 편차 6건 모두 유지(분류 변화 1건), 파싱 실패 84→77/4762.
- **문구 점검 (표 S30·S31)**: 같은 스냅숏 대조군 중 고정 지시문이 있는 18편의 지시문을 두 가지로 바꿔 써서 같은 고정 모델에 1회씩. 바꿔 쓴 지시문 하나당 |Δ| 중앙값 0.96점(상위 사분위 3.33, 최대 15.80; 36건 중 5점 초과 7건), 세 문구의 범위 중앙값 1.75점(5점 초과 6편, 분류 안정 50%), 편차 여부가 문구에 따라 바뀐 논문 3편. 같은 논문의 날짜 차이 중앙값 0.53점, 벤더 지정 대체 모델 이동 중앙값 4.50점(5점 초과 7편).
- **저장소 기반 논문의 후속 조건 (표 S32)**: 어댑터가 OpenAI 모델 하나를 부르는 5편을 벤더 지정 대체 모델에 그대로 실행. 주장 20개 중 deviated 11, reproduced 9; 편차 가운데 보고값 위로 10건. |이동| 중앙값 8.30점.

| 논문 ID | 주장 | 보고값 | 생전 재실행 | 대체 모델 | 95% 구간 | 차이(점) | 분류 | 비고 |
|---|---|---|---|---|---|---|---|---|
| W7171749161 | Tag Questions: tag effect on agreement | -0.075 | -0.102 | -0.181 (gpt-5.6-sol) | [-0.258, -0.108] | -10.63 | deviated | interval is the 90% band as in the paper |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, length | 91.2 | 91.2 | 100 (gpt-5.6-sol) | [100, 100] | 8.80 | deviated | n=34 |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, concreteness | 92.9 | 92.9 | 100 (gpt-5.6-sol) | [100, 100] | 7.10 | deviated | n=28 |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, empty reference | 50 | 61.5 | 100 (gpt-5.6-sol) | [100, 100] | 50.00 | deviated | n=26 |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, content continuation | 100 | 100 | 100 (gpt-5.6-sol) | [100, 100] | 0.00 | reproduced | n=24 |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, nested instruction | 91.7 | 91.7 | 100 (gpt-5.6-sol) | [100, 100] | 8.30 | deviated | n=24 |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, familiar knowledge | 95.8 | 95.8 | 87.5 (gpt-5.6-sol) | [66.667, 100] | -8.30 | reproduced | n=24 |
| W4404781910 | OffsetBias: EvalBiasBench accuracy, total | 86.9 | 88.8 | 98.1 (gpt-5.6-sol) | [95, 100] | 11.20 | deviated | n=160 |
| W7144391134 | BlindingLLMs: Pearson r x100, 1000-shot | 75.6 | 76.6 | 97.5 (gpt-5.6-luna) | [96.3, 98.4] | 21.90 | deviated | n=150 test molecules, 2 runs |
| W7144391134 | BlindingLLMs: Pearson r x100, 60-shot | 42.9 | 37.6 | 94.2 (gpt-5.6-luna) | [91.5, 96.5] | 51.30 | deviated | n=150 test molecules, 2 runs |
| W7144391134 | BlindingLLMs: Pearson r, 0-shot | 0.407 | 0.406 | 0.952 (gpt-5.6-luna) | - | 54.50 | deviated | n=517 molecules: seeded random subset of 500 under the cost cap plus 1 |
| W4416074906 | AgentMisalignment: misalignment score, persona None | 0.208 | 0.208 | 0.208 (gpt-5.6-terra) | [0.042, 0.417] | 0.03 | reproduced |  |
| W4416074906 | AgentMisalignment: misalignment score, persona Analyst | 0.208 | 0.208 | 0.208 (gpt-5.6-terra) | [0.042, 0.375] | 0.03 | reproduced |  |
| W4416074906 | AgentMisalignment: misalignment score, persona Executor | 0.25 | 0.25 | 0.208 (gpt-5.6-terra) | [0.042, 0.375] | -4.17 | reproduced |  |
| W4416074906 | AgentMisalignment: misalignment score, persona Inventor | 0.208 | 0.25 | 0.25 (gpt-5.6-terra) | [0.083, 0.417] | 4.20 | reproduced |  |
| W4416074906 | AgentMisalignment: misalignment score, persona Custodian | 0.208 | 0.25 | 0.25 (gpt-5.6-terra) | [0.083, 0.417] | 4.20 | reproduced |  |
| W4416074906 | AgentMisalignment: misalignment score, persona Pragmatist | 0.25 | 0.208 | 0.208 (gpt-5.6-terra) | [0.042, 0.375] | -4.17 | reproduced |  |
| W4416074906 | AgentMisalignment: misalignment score, persona row_mean | 0.222 | 0.229 | 0.222 (gpt-5.6-terra) | [0.153, 0.292] | 0.02 | reproduced |  |
| W4412887943 | MEDEC: error flag accuracy (vs Table 2 GPT-4o) | 0.658 | 0.561 | 0.752 (gpt-5.6-sol) | [0.722, 0.784] | 9.37 | deviated | MS 597/925 |
| W4412887943 | MEDEC: error sentence accuracy (vs Table 2 GPT-4o) | 0.567 | 0.461 | 0.734 (gpt-5.6-sol) | [0.701, 0.765] | 16.72 | deviated | MS 597/925 |

## 파일

- Tier A: `runs/<논문 ID>/run_meta.json`, 주장 표 `data/tiera_claims.csv`, 어댑터 `harness/adapters/`.
- Tier B: `runs/tierb/<논문 ID>/result.json`, 요약 `runs/tierb/batch1_tierb_summary.json`, 설정 `harness/tierb/configs/`.
- 후속 전환: `runs/tierb_p3/<조건>/<논문 ID>/result.json`, 요약 `data/p3_summary.csv`, 그림 `figures/p3_successor.png`.
- 그림: `figures/reexec_forest.png` (Fig 3), `figures/p3_successor.png` (Fig 5 후보), `figures/drift_case_study.png` (Fig 4).
- 강건성 점검: `data/drift_control.csv`, `data/p3_repeat_spread.csv`·`p3_repeat_summary.csv`, `data/p3_bf16_compare.csv`·`p3_bf16_summary.csv`, `data/p3_paraphrase_spread.csv`·`p3_paraphrase_summary.csv`, `data/tiera_successor_claims.csv`; 아카이브 `runs/tierb_p3/<조건>/`, `runs/<논문 ID>/successor_vendor/`.
- 지출: `budget_log.csv`.
