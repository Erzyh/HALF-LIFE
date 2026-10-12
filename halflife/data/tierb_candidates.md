# Tier B 후보 순위 (자동 선별, 3644편 스캔 / 2885편 전문 확보 / 2028편 후보)

후보 = 전문 확보 + 본문에 사망 예고 모델 ID 등장. 점수 = 프롬프트 표시, 'You are', 인용 블록, 지표, 호출 설정 신호의 합에 MCQ·지표·API 가점.
플래그는 제외가 아니라 검토 표시: alias_dead(별칭이 죽은 preview를 가리킴), alias_unresolved(GA 3개월 내 출판), webui, human, tos, rolling_alias, in_pool.

gpt-4-turbo 언급 1560편의 별칭 해소: {'post-GA alias': 770, 'unresolved': 112, 'dead': 490, 'dated': 188}
플래그 없는 후보 1183편, 그중 저장소 링크 보유 700편

## 제안 1: Tier B 1차 배치 (40편, 점수 12 이상, 분야군 할당 SOC 12 / ENG 8 / MED 8 / CS 6 / LIFE 4 / UNK 2)

| 순위 | 군 | 점수 | 인용 | 살아있는 팔 | 별칭 메모 | 제목 |
|---|---|---|---|---|---|---|
| 10 | ENG | 35 | 0 | gpt-5-mini-2025-08-07 |  | RAGXplain: From Explainable Evaluation to Actionable Guidance of RAG Pipelines |
| 19 | SOC | 31 | 1 | o4-mini |  | VMMU: A Vietnamese Multitask Multimodal Understanding and Reasoning Benchmark |
| 22 | ENG | 31 | 0 | gpt-5-mini-2025-08-07 |  | EngTrace: A Symbolic Benchmark for Verifiable Process Supervision of Engineering |
| 23 | ENG | 31 | 0 | gpt-5-2025-08-07 |  | AI-Assisted Peer Review Across Research Communities: From Reviewer AI Policies t |
| 26 | SOC | 30 | 0 | gpt-4-turbo|o4-mini | post-GA alias (2026-05-26) | CARE-MH: Towards Unified, Reproducible, and Comparable Evaluation of Mental Heal |
| 28 | SOC | 30 | 0 | gpt-4.1-nano|gpt-5-2025-08-07|gpt-5-mini-2025-08-07 |  | COMPASS: A Framework for Evaluating Organization-Specific Policy Alignment in LL |
| 33 | MED | 29 | 1 | gpt-4-turbo|o4-mini | post-GA alias (2025-10-03) | Application of Large Language Models (LLM) for Automatic Classification of Work  |
| 41 | ENG | 28 | 22 | gpt-4o-2024-05-13 |  | AgentClinic: a multimodal agent benchmark to evaluate AI in simulated clinical e |
| 46 | ENG | 27 | 2 | gpt-4o-2024-05-13 |  | Enhancing TinyBERT for Financial Sentiment Analysis Using GPT-Augmented FinBERT  |
| 49 | MED | 27 | 0 | gpt-4-turbo|o4-mini | post-GA alias (2026-03-24) | Large language model scoring of medical student reflection essays: Accuracy and  |
| 54 | SOC | 26 | 4 | gpt-4o-2024-05-13 |  | Enhancing disease detection in radiology reports through fine-tuning lightweight |
| 71 | SOC | 25 | 0 | gpt-4o-2024-05-13|o3-mini |  | GAMEBoT: Transparent Assessment of LLM Reasoning in Games |
| 73 | ENG | 25 | 0 | gpt-4-turbo|o3-mini | post-GA alias (2026-01-20) | LLMOrbit: A Circular Taxonomy of Large Language Models -From Scaling Walls to Ag |
| 101 | SOC | 23 | 0 | gpt-4.1-nano |  | UNH @ Rag4Reports: A Broad Exploration of LLM-Judges for RAG |
| 105 | ENG | 23 | 0 | gpt-5-2025-08-07|gpt-5-mini-2025-08-07 |  | PRISM: Prompt-Refined In-Context System Modelling for Financial Retrieval |
| 112 | ENG | 22 | 3 | gpt-4-turbo | post-GA alias (2024-10-03) | Planning in Strawberry Fields: Evaluating and Improving the Planning and Schedul |
| 119 | ENG | 22 | 0 | gpt-4-turbo | post-GA alias (2024-08-13) | How Aligned are Human Chart Takeaways and LLM Predictions? A Case Study on Bar C |
| 122 | SOC | 22 | 0 | gpt-5-2025-08-07 |  | ST-BiBench: Benchmarking Multi-Stream Multimodal Coordination in Bimanual Embodi |
| 131 | CS | 21 | 5 | gpt-4o-2024-05-13 |  | Knowledge Tagging with Large Language Model Based Multi-Agent System |
| 137 | SOC | 21 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09 |  | Thai Financial Domain Adaptation of THaLLE -- Technical Report |
| 149 | ENG | 20 | 2 | gpt-4-turbo | post-GA alias (2025-01-01) | AGrail: A Lifelong Agent Guardrail with Effective and Adaptive Safety Detection |
| 182 | SOC | 19 | 1 | gpt-4-turbo|gpt-4-turbo-2024-04-09 |  | HAICOSYSTEM: An Ecosystem for Sandboxing Safety Risks in Human-AI Interactions |
| 199 | SOC | 18 | 0 | gpt-4o-2024-05-13 |  | SciIntBench: Measuring LLM Compliance with Research Integrity Norms Under Advers |
| 200 | LIFE | 18 | 0 | gpt-4o-2024-05-13 |  | VipAct: Visual-Perception Enhancement via Specialized VLM Agent Collaboration an |
| 201 | LIFE | 18 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09 |  | Can LLMs replace Neil deGrasse Tyson? Evaluating the Reliability of LLMs as Scie |
| 204 | SOC | 18 | 0 | gpt-4-turbo|o1-pro|o3-mini|o3-pro|o4-mini | post-GA alias (2026-06-04) | Three Years of r/ChatGPT: Societal Impact Evaluations from Social Media Data |
| 207 | MED | 18 | 0 | o3-mini|o3-mini-2025-01-31 |  | Benchmarking Next-Generation Reasoning-Focused Large Language Models in Ophthalm |
| 210 | SOC | 18 | 0 | gpt-5-mini-2025-08-07 |  | JuICE: A Benchmark for Evaluating LLM-Judge in Identifying Cultural Errors |
| 240 | MED | 17 | 0 | gpt-4-turbo|gpt-4.1-nano|o3-2025-04-16 | post-GA alias (2026-04-23) | ChatGPT as a Time Capsule: The Limits of Price Discovery |
| 257 | CS | 16 | 5 | gpt-4-turbo | post-GA alias (2025-01-01) | Adaptive Tool Use in Large Language Models with Meta-Cognition Trigger |
| 289 | CS | 15 | 8 | gpt-4-turbo | post-GA alias (2025-01-14) | Large Language Models For Text Classification: Case Study And Comprehensive Revi |
| 301 | MED | 15 | 1 | gpt-4o-2024-05-13 |  | Temperature-Driven Variability in Emergency Diagnostic Accuracy by a Leading Lan |
| 319 | LIFE | 15 | 0 | gpt-5-2025-08-07 |  | Visual LLM-guided consensus spatial domain detection with L-STAR |
| 331 | CS | 14 | 10 | gpt-4o-2024-05-13 |  | Large Language Models as Data Preprocessors |
| 347 | CS | 14 | 6 | gpt-4-turbo | post-GA alias (2024-11-26) | Prompting Large Language Models for Supporting the Differential Diagnosis of Ane |
| 380 | MED | 14 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09 |  | What emotions reveal about patient safety: GPT-4-based sentiment and emotion ana |
| 389 | MED | 14 | 0 | gpt-5-2025-08-07 |  | Conversational AI for Automated Patient Questionnaire Completion: Development In |
| 410 | MED | 13 | 8 | gpt-4-turbo|o3-mini | post-GA alias (2025-10-28) | Benchmarking large-language-model vision capabilities in oral and maxillofacial  |
| 415 | CS | 13 | 6 | gpt-4-turbo | post-GA alias (2024-09-20) | LLMs Still Can't Plan; Can LRMs? A Preliminary Evaluation of OpenAI's o1 on Plan |
| 563 | LIFE | 12 | 0 | gpt-4-turbo | post-GA alias (2025-12-01) | Artificial Intelligence and Consciousness: Limits and Modern Perspectives |

## 제안 2: Tier A 2차 카드 작성 후보 (30편, 링크 보유, 점수 10 이상, 분야군 할당 SOC 8 / ENG 6 / MED 6 / CS 5 / LIFE 4 / UNK 1)

| 순위 | 군 | 점수 | 인용 | 살아있는 팔 | 링크 | 제목 |
|---|---|---|---|---|---|---|
| 1 | MED | 41 | 2 | gpt-4-turbo | 10 | MedQA-CS: Objective Structured Clinical Examination (OSCE)-Style Benchmark for E |
| 2 | LIFE | 41 | 0 | gpt-4-turbo|o3-2025-04-16|o4-mini|o4-mini-2025-04-16 | 2 | IntrAgent: An LLM Agent for Content-Grounded Information Retrieval through Liter |
| 4 | MED | 39 | 0 | o4-mini|o4-mini-2025-04-16 | 1 | AgentMisalignment: Measuring the Propensity for Misaligned Behaviour in LLM-Base |
| 5 | SOC | 38 | 4 | gpt-4-turbo | 1 | Investigating the Shortcomings of LLMs in Step-by-Step Legal Reasoning |
| 6 | SOC | 37 | 8 | gpt-4-turbo | 11 | Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge |
| 7 | ENG | 37 | 1 | gpt-4o-2024-05-13|o3-mini | 4 | The Structural Safety Generalization Problem |
| 8 | ENG | 37 | 0 | gpt-4-turbo|o3-mini|o4-mini | 1 | MoCA-Agent: A Market-of-Claims Code Agent for Financial and Numerical Reasoning |
| 9 | CS | 35 | 5 | gpt-4o-2024-05-13 | 4 | AutoML-Agent: A Multi-Agent LLM Framework for Full-Pipeline AutoML |
| 11 | SOC | 33 | 1 | gpt-4-turbo | 6 | Rethinking Table Instruction Tuning |
| 12 | ENG | 33 | 0 | gpt-4o-2024-05-13 | 4 | Neptune: The Long Orbit to Benchmarking Long Video Understanding |
| 13 | SOC | 33 | 0 | o4-mini|o4-mini-2025-04-16 | 4 | Agent-to-Agent Theory of Mind: Testing Interlocutor Awareness among Large Langua |
| 15 | ENG | 32 | 0 | o4-mini|o4-mini-2025-04-16 | 6 | PolyGuard: Massive Multi-Domain Safety Policy-Grounded Guardrail Dataset |
| 20 | ENG | 31 | 0 | gpt-4-turbo | 18 | ING-VP: MLLMs cannot Play Easy Vision-based Games Yet |
| 21 | SOC | 31 | 0 | gpt-4.1-nano | 1 | Learning to Predict Future-Aligned Research Proposals with Language Models |
| 24 | SOC | 30 | 9 | gpt-4-turbo | 3 | BIG5-CHAT: Shaping LLM Personalities Through Training on Human-Grounded Data |
| 25 | SOC | 30 | 1 | gpt-4-turbo|gpt-4o-2024-05-13 | 4 | ReIFE: Re-evaluating Instruction-Following Evaluation |
| 27 | SOC | 30 | 0 | gpt-4-turbo | 1 | Judging with Many Minds: Do More Perspectives Mean Less Prejudice? On Bias Ampli |
| 34 | ENG | 29 | 0 | gpt-4o-2024-05-13 | 2 | ACCORD: Closing the Commonsense Measurability Gap |
| 38 | ENG | 29 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-5-2025-08-07|o3-2025-04-16|o4-mini|o4-mini-2025-04-16 | 3 | TURTLEAI: Benchmarking Multimodal Models for Visual Programming in Turtle Graphi |
| 39 | MED | 29 | 0 | gpt-4-turbo|gpt-5-mini-2025-08-07 | 2 | Same Verdict, Different Reasons: LLM-as-a-Judge and Clinician Disagreement on Me |
| 42 | CS | 28 | 12 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13 | 6 | Scaling Synthetic Data Creation with 1,000,000,000 Personas |
| 53 | CS | 26 | 9 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 8 | To Generate or to Retrieve? On the Effectiveness of Artificial Contexts for Medi |
| 59 | MED | 26 | 0 | gpt-4.1-nano | 4 | Qworld: Question-Specific Evaluation Criteria for LLMs |
| 62 | CS | 25 | 12 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 4 | Ask-before-Plan: Proactive Language Agents for Real-World Planning |
| 68 | MED | 25 | 3 | o1-2024-12-17|o1-pro | 2 | People who frequently use ChatGPT for writing tasks are accurate and robust dete |
| 77 | LIFE | 25 | 0 | gpt-5-mini-2025-08-07|o4-mini | 2 | Reasoning Models Struggle to Control their Chains of Thought |
| 79 | CS | 24 | 7 | gpt-4o-2024-05-13 | 5 | OffsetBias: Leveraging Debiased Data for Tuning Evaluators |
| 91 | MED | 23 | 5 | gpt-4o-2024-05-13 | 6 | Are large pre-trained vision language models effective construction safety inspe |
| 96 | LIFE | 23 | 1 | o1-2024-12-17 | 1 | The evolving landscape of neuroscience |
| 229 | LIFE | 17 | 2 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 2 | BADGE: BADminton report Generation and Evaluation with LLM |

## 분야군별 상위 후보 (플래그 없음)

### CS (129편 중 상위 25)

| 순위 | 점수 | 인용 | 살아있는 팔 | 링크 | 제목 |
|---|---|---|---|---|---|
| 9 | 35 | 5 | gpt-4o-2024-05-13 | 4 | AutoML-Agent: A Multi-Agent LLM Framework for Full-Pipeline AutoML |
| 42 | 28 | 12 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13 | 6 | Scaling Synthetic Data Creation with 1,000,000,000 Personas |
| 53 | 26 | 9 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 8 | To Generate or to Retrieve? On the Effectiveness of Artificial Contexts for Medical Open-D |
| 62 | 25 | 12 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 4 | Ask-before-Plan: Proactive Language Agents for Real-World Planning |
| 79 | 24 | 7 | gpt-4o-2024-05-13 | 5 | OffsetBias: Leveraging Debiased Data for Tuning Evaluators |
| 87 | 23 | 24 | gpt-4-turbo | 2 | Alignment faking in large language models |
| 129 | 21 | 7 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13 | 3 | One Thousand and One Pairs: A “novel” challenge for long-context language models |
| 130 | 21 | 7 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 4 | IrokoBench: A New Benchmark for African Languages in the Age of Large Language Models |
| 131 | 21 | 5 | gpt-4o-2024-05-13 | 0 | Knowledge Tagging with Large Language Model Based Multi-Agent System |
| 143 | 20 | 60 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13 | 13 | A Systematic Survey and Critical Review on Evaluating Large Language Models: Challenges, L |
| 147 | 20 | 7 | gpt-4o-2024-05-13 | 1 | Grasping the Essentials: Tailoring Large Language Models for Zero-Shot Relation Extraction |
| 163 | 19 | 44 | gpt-4-turbo | 2 | OpenAI o1 System Card |
| 164 | 19 | 21 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13 | 70 | BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instruc |
| 167 | 19 | 11 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13 | 13 | RewardBench: Evaluating Reward Models for Language Modeling |
| 170 | 19 | 8 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 16 | Tulu 3: Pushing Frontiers in Open Language Model Post-Training |
| 194 | 18 | 6 | gpt-4o-2024-05-13 | 6 | MMCode: Benchmarking Multimodal Large Language Models for Code Generation with Visually Ri |
| 214 | 17 | 34 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 6 | MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark |
| 216 | 17 | 13 | gpt-4-turbo | 5 | From News to Forecast: Integrating Event Analysis in LLM-Based Time Series Forecasting wit |
| 219 | 17 | 10 | gpt-4.1-nano | 2 | Large Language Model Agent as a Mechanical Designer |
| 223 | 17 | 6 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13 | 2 | Long Context RAG Performance of Large Language Models |
| 224 | 17 | 6 | gpt-4o-2024-05-13 | 10 | OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs |
| 252 | 16 | 6 | gpt-4-turbo | 8 | Are We Done with MMLU? |
| 256 | 16 | 6 | gpt-4-turbo | 2 | HTML: Hierarchical Topology Multi-task Learning for Semantic Parsing in Knowledge Base Que |
| 257 | 16 | 5 | gpt-4-turbo | 0 | Adaptive Tool Use in Large Language Models with Meta-Cognition Trigger |
| 289 | 15 | 8 | gpt-4-turbo | 0 | Large Language Models For Text Classification: Case Study And Comprehensive Review |

### MED (220편 중 상위 25)

| 순위 | 점수 | 인용 | 살아있는 팔 | 링크 | 제목 |
|---|---|---|---|---|---|
| 1 | 41 | 2 | gpt-4-turbo | 10 | MedQA-CS: Objective Structured Clinical Examination (OSCE)-Style Benchmark for Evaluating  |
| 4 | 39 | 0 | o4-mini|o4-mini-2025-04-16 | 1 | AgentMisalignment: Measuring the Propensity for Misaligned Behaviour in LLM-Based Agents |
| 33 | 29 | 1 | gpt-4-turbo|o4-mini | 0 | Application of Large Language Models (LLM) for Automatic Classification of Work Accident T |
| 39 | 29 | 0 | gpt-4-turbo|gpt-5-mini-2025-08-07 | 2 | Same Verdict, Different Reasons: LLM-as-a-Judge and Clinician Disagreement on Medical Chat |
| 49 | 27 | 0 | gpt-4-turbo|o4-mini | 0 | Large language model scoring of medical student reflection essays: Accuracy and reproducib |
| 59 | 26 | 0 | gpt-4.1-nano | 4 | Qworld: Question-Specific Evaluation Criteria for LLMs |
| 68 | 25 | 3 | o1-2024-12-17|o1-pro | 2 | People who frequently use ChatGPT for writing tasks are accurate and robust detectors of A |
| 91 | 23 | 5 | gpt-4o-2024-05-13 | 6 | Are large pre-trained vision language models effective construction safety inspectors |
| 97 | 23 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13 | 2 | SAFETY-J: Evaluating Safety with Critique |
| 116 | 22 | 0 | gpt-4o-2024-05-13 | 3 | Reinforcement Learning Improves LLM Accuracy and Reasoning in Disease Classification from  |
| 121 | 22 | 0 | gpt-4.1-nano|gpt-4.1-nano-2025-04-14 | 7 | Doctor-R1: Mastering Clinical Inquiry with Experiential Agentic Reinforcement Learning |
| 138 | 21 | 0 | gpt-4-turbo|gpt-5-mini-2025-08-07 | 2 | The Application Landscape Analysis of Multi-agent Collaboration Research in the Medical Fi |
| 140 | 21 | 0 | gpt-4.1-nano | 4 | Why Do Safety Guardrails Degrade Across Languages? |
| 189 | 19 | 0 | gpt-4-turbo|o3-mini | 1 | The ORCA Benchmark: Evaluating Real-World Calculation Accuracy in Large Language Models |
| 197 | 18 | 1 | gpt-4-turbo|gpt-4o-2024-05-13 | 1 | Comparative Analysis of Multimodal Large Language Models GPT-4o and o1 vs Clinicians in Cl |
| 207 | 18 | 0 | o3-mini|o3-mini-2025-01-31 | 0 | Benchmarking Next-Generation Reasoning-Focused Large Language Models in Ophthalmology: A H |
| 228 | 17 | 2 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13 | 2 | Large Language Models versus Classical Machine Learning: Performance in COVID-19 Mortality |
| 240 | 17 | 0 | gpt-4-turbo|gpt-4.1-nano|o3-2025-04-16 | 0 | ChatGPT as a Time Capsule: The Limits of Price Discovery |
| 241 | 17 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 3 | LabAlignAgent LabAlignAgent: A LOINC-Enriched Ontology-Guided Agent forCross-Hospital Sema |
| 259 | 16 | 3 | gpt-4o-2024-05-13 | 2 | Beyond ChatGPT: Enhancing Software Quality Assurance Tasks with Diverse LLMs and Validatio |
| 301 | 15 | 1 | gpt-4o-2024-05-13 | 0 | Temperature-Driven Variability in Emergency Diagnostic Accuracy by a Leading Language Mode |
| 341 | 14 | 8 | gpt-4-turbo | 2 | Lived Experience Not Found: LLMs Struggle to Align with Experts on Addressing Adverse Drug |
| 352 | 14 | 3 | gpt-4o-2024-05-13 | 8 | Alignment for Honesty |
| 353 | 14 | 3 | gpt-4-turbo | 2 | Impact of retrieval augmented generation and large language model complexity on undergradu |
| 380 | 14 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 0 | What emotions reveal about patient safety: GPT-4-based sentiment and emotion analysis of 1 |

### SOC (510편 중 상위 25)

| 순위 | 점수 | 인용 | 살아있는 팔 | 링크 | 제목 |
|---|---|---|---|---|---|
| 5 | 38 | 4 | gpt-4-turbo | 1 | Investigating the Shortcomings of LLMs in Step-by-Step Legal Reasoning |
| 6 | 37 | 8 | gpt-4-turbo | 11 | Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge |
| 11 | 33 | 1 | gpt-4-turbo | 6 | Rethinking Table Instruction Tuning |
| 13 | 33 | 0 | o4-mini|o4-mini-2025-04-16 | 4 | Agent-to-Agent Theory of Mind: Testing Interlocutor Awareness among Large Language Models |
| 19 | 31 | 1 | o4-mini | 0 | VMMU: A Vietnamese Multitask Multimodal Understanding and Reasoning Benchmark |
| 21 | 31 | 0 | gpt-4.1-nano | 1 | Learning to Predict Future-Aligned Research Proposals with Language Models |
| 24 | 30 | 9 | gpt-4-turbo | 3 | BIG5-CHAT: Shaping LLM Personalities Through Training on Human-Grounded Data |
| 25 | 30 | 1 | gpt-4-turbo|gpt-4o-2024-05-13 | 4 | ReIFE: Re-evaluating Instruction-Following Evaluation |
| 26 | 30 | 0 | gpt-4-turbo|o4-mini | 0 | CARE-MH: Towards Unified, Reproducible, and Comparable Evaluation of Mental Health LLMs |
| 27 | 30 | 0 | gpt-4-turbo | 1 | Judging with Many Minds: Do More Perspectives Mean Less Prejudice? On Bias Amplifications  |
| 28 | 30 | 0 | gpt-4.1-nano|gpt-5-2025-08-07|gpt-5-mini-2025-08-07 | 0 | COMPASS: A Framework for Evaluating Organization-Specific Policy Alignment in LLMs |
| 40 | 29 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 2 | CEB: Compositional Evaluation Benchmark for Fairness in Large Language Models |
| 45 | 28 | 0 | gpt-4-turbo | 2 | LoFTI: Localization and Factuality Transfer to Indian Locales |
| 47 | 27 | 1 | gpt-4-turbo|gpt-4o-2024-05-13 | 9 | Is Human-Like Text Liked by Humans? Multilingual Human Detection and Preference Against AI |
| 50 | 27 | 0 | gpt-4.1-nano | 3 | Training Alignment Auditors via Reinforcement Learning |
| 54 | 26 | 4 | gpt-4o-2024-05-13 | 0 | Enhancing disease detection in radiology reports through fine-tuning lightweight LLM on we |
| 55 | 26 | 1 | gpt-5-mini-2025-08-07 | 12 | ReMedQA: Are We Done With Medical Multiple-Choice Benchmarks? |
| 56 | 26 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-4o-2024-05-13|o3-2025-04-16 | 2 | HLPD: Aligning LLMs to Human Language Preference for Machine-Revised Text Detection |
| 58 | 26 | 0 | gpt-4.1-nano | 2 | LLMs learn scientific taste from institutional traces across the social sciences |
| 69 | 25 | 2 | gpt-4.1-nano|gpt-4.1-nano-2025-04-14|o4-mini|o4-mini-2025-04-16 | 5 | Are Vision-Language Models Safe in the Wild? A Meme-Based Benchmark Study |
| 70 | 25 | 0 | gpt-4o-2024-05-13 | 4 | ValueScope: Unveiling Implicit Norms and Values via Return Potential Model of Social Inter |
| 71 | 25 | 0 | gpt-4o-2024-05-13|o3-mini | 0 | GAMEBoT: Transparent Assessment of LLM Reasoning in Games |
| 74 | 25 | 0 | o3-mini | 2 | Reward Modeling for Scientific Writing Evaluation |
| 76 | 25 | 0 | o1-pro|o4-mini | 5 | Frankentext: Stitching random text fragments into long-form narratives |
| 81 | 24 | 1 | gpt-4-turbo | 2 | Distinct Profiles of Run-to-Run Score Reliability and Expert-Panel Alignment Across Four L |

### ENG (256편 중 상위 25)

| 순위 | 점수 | 인용 | 살아있는 팔 | 링크 | 제목 |
|---|---|---|---|---|---|
| 7 | 37 | 1 | gpt-4o-2024-05-13|o3-mini | 4 | The Structural Safety Generalization Problem |
| 8 | 37 | 0 | gpt-4-turbo|o3-mini|o4-mini | 1 | MoCA-Agent: A Market-of-Claims Code Agent for Financial and Numerical Reasoning |
| 10 | 35 | 0 | gpt-5-mini-2025-08-07 | 0 | RAGXplain: From Explainable Evaluation to Actionable Guidance of RAG Pipelines |
| 12 | 33 | 0 | gpt-4o-2024-05-13 | 4 | Neptune: The Long Orbit to Benchmarking Long Video Understanding |
| 15 | 32 | 0 | o4-mini|o4-mini-2025-04-16 | 6 | PolyGuard: Massive Multi-Domain Safety Policy-Grounded Guardrail Dataset |
| 20 | 31 | 0 | gpt-4-turbo | 18 | ING-VP: MLLMs cannot Play Easy Vision-based Games Yet |
| 22 | 31 | 0 | gpt-5-mini-2025-08-07 | 0 | EngTrace: A Symbolic Benchmark for Verifiable Process Supervision of Engineering Reasoning |
| 23 | 31 | 0 | gpt-5-2025-08-07 | 0 | AI-Assisted Peer Review Across Research Communities: From Reviewer AI Policies to LLM Revi |
| 34 | 29 | 0 | gpt-4o-2024-05-13 | 2 | ACCORD: Closing the Commonsense Measurability Gap |
| 38 | 29 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09|gpt-5-2025-08-07|o3-2025-04-16|o4-mini|o4-mini-2025-04-16 | 3 | TURTLEAI: Benchmarking Multimodal Models for Visual Programming in Turtle Graphics |
| 41 | 28 | 22 | gpt-4o-2024-05-13 | 0 | AgentClinic: a multimodal agent benchmark to evaluate AI in simulated clinical environment |
| 46 | 27 | 2 | gpt-4o-2024-05-13 | 0 | Enhancing TinyBERT for Financial Sentiment Analysis Using GPT-Augmented FinBERT Distillati |
| 72 | 25 | 0 | gpt-4-turbo | 2 | Beyond Sample-Level Feedback: Using Reference-Level Feedback to Guide Data Synthesis |
| 73 | 25 | 0 | gpt-4-turbo|o3-mini | 0 | LLMOrbit: A Circular Taxonomy of Large Language Models -From Scaling Walls to Agentic AI S |
| 100 | 23 | 0 | gpt-4-turbo | 1 | Sharingan: Extract User Action Sequence from Desktop Recordings |
| 102 | 23 | 0 | o3-mini|o3-mini-2025-01-31 | 2 | FinEval-KR: A Financial Domain Evaluation Framework for Large Language Models’ Knowledge a |
| 105 | 23 | 0 | gpt-5-2025-08-07|gpt-5-mini-2025-08-07 | 0 | PRISM: Prompt-Refined In-Context System Modelling for Financial Retrieval |
| 112 | 22 | 3 | gpt-4-turbo | 0 | Planning in Strawberry Fields: Evaluating and Improving the Planning and Scheduling Capabi |
| 117 | 22 | 0 | gpt-4-turbo | 2 | SciEvent: Benchmarking Multi-domain Scientific Event Extraction |
| 119 | 22 | 0 | gpt-4-turbo | 0 | How Aligned are Human Chart Takeaways and LLM Predictions? A Case Study on Bar Charts with |
| 120 | 22 | 0 | gpt-4-turbo | 1 | Seeker: Towards Exception Safety Code Generation with Intermediate Language Agents Framewo |
| 135 | 21 | 0 | gpt-4o-2024-05-13|o3-2025-04-16|o3-mini|o3-mini-2025-01-31 | 2 | ASPERA: A Simulated Environment to Evaluate Planning for Complex Action Execution |
| 141 | 21 | 0 | gpt-5-2025-08-07 | 10 | El Agente Gráfico: A Semantic Execution Runtime for Scientific Agents |
| 146 | 20 | 8 | gpt-4-turbo | 2 | AI-Driven Review Systems: Evaluating LLMs in Scalable and Bias-Aware Academic Reviews |
| 149 | 20 | 2 | gpt-4-turbo | 0 | AGrail: A Lifelong Agent Guardrail with Effective and Adaptive Safety Detection |

### LIFE (68편 중 상위 25)

| 순위 | 점수 | 인용 | 살아있는 팔 | 링크 | 제목 |
|---|---|---|---|---|---|
| 2 | 41 | 0 | gpt-4-turbo|o3-2025-04-16|o4-mini|o4-mini-2025-04-16 | 2 | IntrAgent: An LLM Agent for Content-Grounded Information Retrieval through Literature Revi |
| 77 | 25 | 0 | gpt-5-mini-2025-08-07|o4-mini | 2 | Reasoning Models Struggle to Control their Chains of Thought |
| 96 | 23 | 1 | o1-2024-12-17 | 1 | The evolving landscape of neuroscience |
| 200 | 18 | 0 | gpt-4o-2024-05-13 | 0 | VipAct: Visual-Perception Enhancement via Specialized VLM Agent Collaboration and Tool-use |
| 201 | 18 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 0 | Can LLMs replace Neil deGrasse Tyson? Evaluating the Reliability of LLMs as Science Commun |
| 229 | 17 | 2 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 2 | BADGE: BADminton report Generation and Evaluation with LLM |
| 231 | 17 | 1 | gpt-4o-2024-05-13 | 2 | Implementing a context-augmented large language model to guide precision cancer medicine |
| 246 | 17 | 0 | gpt-4-turbo|gpt-4.1-nano|gpt-4.1-nano-2025-04-14 | 4 | Large Language Models for Biomedical Article Classification |
| 249 | 16 | 17 | gpt-4-turbo | 3 | LAB-Bench: Measuring Capabilities of Language Models for Biology Research |
| 269 | 16 | 0 | gpt-4-turbo | 1 | PGxRAG: A Retrieval Augmented Generation supported Pharmacogenomics Assistant |
| 319 | 15 | 0 | gpt-5-2025-08-07 | 0 | Visual LLM-guided consensus spatial domain detection with L-STAR |
| 358 | 14 | 2 | gpt-4-turbo | 6 | TourSynbio: A Multi-Modal Large Model and Agent Framework to Bridge Text and Protein Seque |
| 375 | 14 | 0 | gpt-4-turbo | 4 | AskBeacon -- Performing genomic data exchange and analytics with natural language |
| 376 | 14 | 0 | gpt-4-turbo|gpt-4-turbo-2024-04-09 | 1 | Two Heads Are Better Than One: Dual-Model Verbal Reflection at Inference-Time |
| 464 | 13 | 0 | gpt-4.1-nano | 2 | Mapping the otoactive landscape: an LLM-aided extraction of compounds and their targets |
| 471 | 13 | 0 | gpt-5-mini-2025-08-07 | 2 | ANCHOR-RE: An Agentic Neuro-Symbolic Framework for Grounded Biomedical Relation Extraction |
| 501 | 12 | 7 | gpt-4-turbo|o3-mini | 2 | ProteinGPT: Multimodal LLM for Protein Property Prediction and Structure Understanding |
| 524 | 12 | 1 | gpt-4o-2024-05-13 | 4 | Give me Some Hard Questions: Synthetic Data Generation for Clinical QA |
| 563 | 12 | 0 | gpt-4-turbo | 0 | Artificial Intelligence and Consciousness: Limits and Modern Perspectives |
| 572 | 12 | 0 | gpt-4.1-nano | 2 | Identifying Implicit Research Data References in Paper Citations |
| 682 | 11 | 0 | gpt-4-turbo | 1 | Enhancing Healthcare LLM Trust with Atypical Presentations Recalibration |
| 717 | 11 | 0 | gpt-4.1-nano | 2 | SommBench: Assessing Sommelier Expertise of Language Models |
| 798 | 10 | 1 | gpt-4-turbo | 0 | Scaling Public Health Text Annotation: Zero-Shot Learning vs. Crowdsourcing for Improved E |
| 823 | 10 | 0 | gpt-4o-2024-05-13 | 0 | Analyzing the Multilingual Ability of Vision-Language Models to Generate Explanations for  |
| 826 | 10 | 0 | gpt-4-turbo | 2 | Integrating Semantic Web Technologies and Large Language Models: Ontologies and LLMs for M |
