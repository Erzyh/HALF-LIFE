# Tier B triage, group 1 (50 papers)

Counts: eligible 10, maybe 13, ineligible 27.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md`. Order follows `data/tierb_triage/group_1.csv` (rank).

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4403851744 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | MedExamLLM score=59.89 (1667) | high | - | MedQA-CS: Objective Structured Clinical Examination (OSCE)-… |
| W7164615251 | ineligible | unresolved | C | full | other | none (cited rows) | low | no_number | MoCA-Agent: A Market-of-Claims Code Agent for Financial and… |
| W4415164185 | ineligible | o4-mini-2025-04-16 | A | full | classification | none (data generator) | low | tos, no_number | PolyGuard: Massive Multi-Domain Safety Policy-Grounded Guar… |
| W4412944944 | ineligible | unresolved | C | full | other | none (citation) | low | no_number | BIG5-CHAT: Shaping LLM Personalities Through Training on Hu… |
| W4399442646 | ineligible | gpt-4o-2024-05-13 | S | full | mcq | accuracy (figure only) | high | no_number | ACCORD: Closing the Commonsense Measurability Gap |
| W4412888091 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | EC (GPT-4 eval)=0.81 (250) | mid | - | LoFTI: Localization and Factuality Transfer to Indian Local… |
| W4403784010 | ineligible | gpt-4o-2024-05-13 | B | full | extraction | micro-F1=0.93 (100) | low | data_closed | Enhancing disease detection in radiology reports through fi… |
| W4406880877 | eligible | o1-2024-12-17 | B | full | classification | TPR (CoT detector)=54.0 (300) | high | - | People who frequently use ChatGPT for writing tasks are acc… |
| W7166873827 | eligible | o3-mini-2025-01-31 | B | full | classification | accuracy RW=0.79 (1857) | high | - | Reward Modeling for Scientific Writing Evaluation |
| W4405627013 | ineligible | gpt-4-turbo-2024-04-09 | B | full | generation | alignment-faking rate (text only) | mid | tos, no_number | Alignment faking in large language models |
| W4404407955 | ineligible | unresolved | C | full | extraction | none (reference URL) | low | no_number | Sharingan: Extract User Action Sequence from Desktop Record… |
| W4403882451 | maybe | gpt-4-turbo-2024-04-09 | B | full | other | plan accuracy=40.1 (600) | mid | - | Planning in Strawberry Fields: Evaluating and Improving the… |
| W7128554909 | ineligible | gpt-5-2025-08-07 | S | full | other | spatial-grounding success=94.28 (n/a) | high | data_closed | ST-BiBench: Benchmarking Multi-Stream Multimodal Coordinati… |
| W7202244013 | ineligible | unresolved | C | none | other | none (cited) | low | no_number | The Application Landscape Analysis of Multi-agent Collabora… |
| W4404792940 | ineligible | gpt-4o-2024-05-13 | B | full | extraction | F1 of trained SLM=74.61 (n/a) | mid | no_number | Grasping the Essentials: Tailoring Large Language Models fo… |
| W4404649382 | ineligible | gpt-4o-2024-05-13 | S | full | generation | VideoAutoBench avg=82.55 (n/a) | high | aux_model_dead | VideoAutoArena: An Automated Arena for Evaluating Large Mul… |
| W4405766390 | ineligible | unresolved | B | partial | agentic | pass@10 (Twist order)=100 (1) | mid | data_closed | OpenAI o1 System Card |
| W4402302940 | ineligible | unresolved | C | full | generation | none (citation) | low | no_number | Performance of Open-Source LLMs in Challenging Radiological… |
| W4416017844 | ineligible | unresolved | C | partial | other | accuracy (ChatGPT-5 UI)=49.4 (500) | low | webui, no_number | The ORCA Benchmark: Evaluating Real-World Calculation Accur… |
| W7162893299 | ineligible | unresolved | S | partial | classification | refusal rate (figure only) | low | no_number, tos | SciIntBench: Measuring LLM Compliance with Research Integri… |
| W4415161353 | maybe | o3-mini-2025-01-31 | S | partial | mcq | accuracy=0.857 (5888) | high | - | Benchmarking Next-Generation Reasoning-Focused Large Langua… |
| W4412944996 | maybe | gpt-4-turbo-2024-04-09 | S | partial | other | F-score=49.1 (3000) | high | - | Chinese SimpleQA: A Chinese Factuality Evaluation for Large… |
| W4400103831 | maybe | gpt-4-turbo-2024-04-09 | S | partial | generation | GPT-4-eval avg score=8.825 (10) | low | - | BADGE: BADminton report Generation and Evaluation with LLM |
| W7159577685 | eligible | gpt-4-turbo-2024-04-09 | S | full | other | mean T+I+F=1.36 (25) | low | - | Breaking the Chains of Probability: Neutrosophic Logic as a… |
| W7169688936 | ineligible | o4-mini-2025-04-16 | S | full | other | accuracy (GPT-5 graded)=0.9 (6015) | high | data_closed | Assessing AI in Introductory Physics Problem Solving |
| W4402954433 | maybe | gpt-4o-2024-05-13 | S | full | extraction | faults at Top-1=221 (324) | mid | - | Beyond ChatGPT: Enhancing Software Quality Assurance Tasks… |
| W4411119341 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | other | accuracy (figure only) | mid | no_number | Reverse Question Answering: Can an LLM Write a Question so… |
| W7166852552 | eligible | gpt-4.1-nano | S | full | mcq | accuracy (Naive)=46.51 (8385) | low | - | LexGenius: An Expert-Level Benchmark for Large Language Mod… |
| W4416026742 | ineligible | gpt-4o-2024-05-13 | B | full | generation | cosine sim. to baseline=0.969 (n/a) | low | data_closed, aux_model_dead | Using language models to label clusters of scientific docum… |
| W7140124165 | maybe | gpt-4-turbo-2024-04-09 | S | full | mcq | accuracy zero-shot EN=0.44 (n/a) | high | - | MEENA (PersianMMMU): Multimodal-Multilingual Educational Ex… |
| W7133241402 | ineligible | gpt-4.1-nano | S | full | classification | Macro F1=0.731 (n/a) | low | data_closed | The Brittle Compass: Navigating LLM Prompt Sensitivity in S… |
| W4400141990 | maybe | gpt-4o-2024-05-13 | S | partial | other | LiveBench score=52.6 (n/a) | mid | - | AI Benchmark Half-Life in Recursive Corpora: A Theory of Va… |
| W4399317891 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | rejection rate Hard-1K=12.7 (n/a) | mid | - | OR-Bench: An Over-Refusal Benchmark for Large Language Mode… |
| W4404783055 | ineligible | gpt-4o-2024-05-13 | B | partial | classification | none (demo only) | low | no_number | PsyGUARD: An Automated System for Suicide Detection and Ris… |
| W4403443823 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | precision (metaphorical)=74.8 (3736) | high | - | Science is Exploration: Computational Frontiers for Concept… |
| W4416034223 | eligible | gpt-4o-2024-05-13 | S | partial | other | prompt-level acc, n=5=0.57 (216) | mid | - | When Instructions Multiply: Measuring and Estimating LLM Ca… |
| W4405762666 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | other | accuracy APBench-gamma=49.2 (n/a) | mid | aux_model_dead | APBench: Benchmarking Large Language Model Performance in F… |
| W4416339332 | maybe | o3-mini-2025-01-31 | B | full | classification | weighted F1 U.S.=65 (n/a) | high | - | "As Eastern Powers, I will veto." : An Investigation of Nat… |
| W4405172832 | ineligible | unresolved | A | partial | other | none (cited/scorer) | low | no_number | Expanding Performance Boundaries of Open-Source Multimodal… |
| W4405562150 | ineligible | unresolved | C | none | other | none (survey) | low | no_number | LLMs are Also Effective Embedding Models: An In-depth Overv… |
| W4411119617 | maybe | gpt-4-turbo-2024-04-09 | S | partial | mcq | accuracy Knowledge=0.72 (629) | low | - | MedEthicEval: Evaluating Large Language Models Based on Chi… |
| W4414633513 | ineligible | gpt-4o-2024-05-13 | B | none | classification | accuracy zero-shot=46.87 (1037) | mid | - | Exploring Cognitive and Aesthetic Causality for Multimodal… |
| W4404985489 | eligible | gpt-4-turbo-2024-04-09 | S | full | extraction | F1 (pureGPT4T)=0.491 (556) | high | - | Variable Extraction for Model Recovery in Scientific Litera… |
| W4404352371 | maybe | gpt-4-turbo-2024-04-09 | S | partial | mcq | accuracy ALL=40.21 (2860) | high | - | EEE-Bench: A Comprehensive Multimodal Electrical And Electr… |
| W7172172323 | ineligible | gpt-5-2025-08-07 | S | partial | agentic | total electricity kWh=273.84 (1) | high | data_closed | Exact Action Values Are Not Enough: Rollout-Verified Reinfo… |
| W4411113098 | maybe | gpt-4-turbo-2024-04-09 | S | full | generation | line coverage %=96.08 (210) | low | - | TESTEVAL: Benchmarking Large Language Models for Test Case… |
| W4404781158 | maybe | gpt-4-turbo-2024-04-09 | S | full | other | score EN avg=75.28 (300) | low | - | MultiPragEval: Multilingual Pragmatic Evaluation of Large L… |
| W4412008396 | ineligible | unresolved | C | none | generation | none (ChatGPT UI) | low | webui, no_number | DİN EĞİTİMİNDE CHATGPT’NİN ROLÜ: TEFSİR VE KELAM ÇERÇEVESİN… |
| W4406058598 | eligible | gpt-4o-2024-05-13 | B | full | classification | accuracy ME-FEVER=0.83 (1238) | mid | - | Halu-J: Critique-Based Hallucination Judge |
| W4404307057 | ineligible | unresolved | B | full | classification | total F1 (Copilot)=0.76 (n/a) | low | webui | Smart ETL and LLM-based contents classification: the Europe… |

## Observations

- Alias resolution: 30 of the 50 rows carry a bare `gpt-4-turbo` in `live_ids`. Only 8 papers pin `gpt-4-turbo-2024-04-09` in the text (W4400103831, W4399317891, W4403443823, W4404781158, W4405762666, W4406058598, W4411119341, W4400141990); the other eligible/maybe cases (W4403851744, W4412888091, W4403882451, W4412944996, W7140124165, W4411119617, W4411113098, W4404985489, W4404352371, W7159577685) were resolved by the date rule alone. W4403882451 (PlanBench numbers presented in a 2024-10 paper) is the case most likely to hide a 2023 preview behind the alias.
- Mention-only is the largest single reason for ineligibility: 8 papers use the live id only in a citation, reference URL or related-work sentence (role C), and 2 more use it only as a data generator or scorer (role A). In several of these the model actually run is an undated `GPT-4o` / `GPT-4o-mini` (W4412944944, W4404407955, W4415164185), which the live list does not count as a pinned snapshot.
- Judge and parser dependencies decide many verdicts. When the judge is the same live model (W4403851744, W4412888091, W4400103831, W4404985489) the claim stays re-runnable, at 2-3x the call count. Undated judges/parsers (`GPT-4o` in W4412944996, `GPT-4` in W4399317891, `GPT-4o-mini` in W4404352371 and W7140124165) were treated as soft gaps (maybe). Judges pinned to snapshots outside the live list (`gpt-4o-2024-08-06` in W4404649382 and W4405762666, `gpt-4o-2024-11-20` baseline in W4416026742) were treated as aux_model_dead.
- Data closure and interfaces: 7 papers are blocked by data_closed (institutional radiology reports, a robotics simulator, Dimensions bibliographic clusters, a Slovak media corpus, copyrighted textbook problems, an HVAC emulator, OpenAI-internal agentic tasks) and 3 by webui (ChatGPT/OpenAI UI, Microsoft Copilot). All 10 eligible papers point to a public GitHub/HF release of their inputs.
- No usable number: 3 papers report the live model only in figures (W4399442646, W4411119341, W7162893299), and 3 report a number that is not an output of the live model (an SLM trained on GPT-4o synthetic data in W4404792940, a demo-only use in W4404783055, a qualitative statement in W4405627013).
- Cost: 5 of the 10 eligible claims fall in the high tier because n is in the thousands (TroFi 3,736; MedQA-CS 1,667 x 2 with judge) or the model is o-series (o1 detector on 300 long articles, o3-mini on 1,857 rubric items) or the judge is called pairwise (W4404985489). The cheap eligible cases are W7159577685 (75 calls, but n=25 at temperature 0.7) and W7166852552 (8,385 MCQs on gpt-4.1-nano). W4400141990's text is LiveBench (matching its DOI), not the title listed in the CSV.
