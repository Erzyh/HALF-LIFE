# Tier B triage, group 13 (49 papers)

Counts: eligible 17, maybe 9, ineligible 23.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md`. Order follows `data/tierb_triage/group_13.csv` (rank).

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W7160514285 | eligible | gpt-4.1-nano | S | partial | classification | forced-choice accuracy=0.935 (108) | low | - | Large Language Models Show Metacognitive Sensitivity in Med… |
| W7163878229 | eligible | gpt-4.1-nano | S | full | classification | BM (LLM TENSE vs human)=-0.006 (100) | low | - | The quantified immune-aging dysregulation index: a large-la… |
| W7130349016 | ineligible | gpt-4.1-nano | A | partial | agentic | none (aux./judge role only) | low | no_number | ED-Triage-Agent: A Framework for Human-AI Collaborative Eme… |
| W4416034996 | eligible | gpt-4.1-nano-2025-04-14 | S | partial | generation | Pass@1, full-file gen (All)=2.1 (1888) | low | - | Turning the Tide: Repository-based Code Reflection |
| W7130482099 | maybe | gpt-4.1-nano | S | partial | classification | overtake count, Role+R+ToT=11 (30) | low | - | CARE-Drive: A Framework for Evaluating Reason-Responsivenes… |
| W4414820685 | ineligible | gpt-4.1-nano-2025-04-14 | A | none | other | none (aux./judge role only) | low | no_number | Differential Information Distribution: A Bayesian Perspecti… |
| W4416036485 | maybe | o3-mini-2025-01-31 | S | partial | generation | pass@1, SEED math problems=99 (200) | high | - | From A and B to A+B: Can Large Language Models Solve Compos… |
| W4416036063 | eligible | o1-2024-12-17 | S | full | mcq | OQ MMLU accuracy=89.2 (500) | high | - | sudoLLM: On Multi-role Alignment of Language Models |
| W4417170236 | maybe | o1-2024-12-17 | S | full | classification | EMR, official SemEval test=0.345 (n/a) | mid | - | Fane at SemEval-2025 Task 10: Zero-Shot Entity Framing with… |
| W4415332749 | eligible | o1-2024-12-17 | B | full | classification | judging acc., ReasoningJudgeBench=73.1 (1483) | high | - | J4R: Learning to Judge with Equivalent Initial State Group… |
| W7165065231 | ineligible | o1-2024-12-17 | A | none | other | none (aux./judge role only) | low | no_number | Intelligent Multimodal Retrieval and Reasoning for Geospati… |
| W4416036262 | ineligible | o4-mini-2025-04-16 | A | partial | mcq | none (aux./judge role only) | low | no_number | Benchmark Profiling: Mechanistic Diagnosis of LLM Benchmarks |
| W7126280993 | eligible | o3-2025-04-16 | S | full | other | Semantic Gap (explicit sep.)=0.4 (120) | mid | - | Semantic Content Determines Algorithmic Performance |
| W7166823216 | eligible | o3-2025-04-16 | S | full | other | Belief Score, multimodal=35.2 (200) | high | - | Probing Multimodal Large Language Models on Cognitive Biase… |
| W7170225355 | ineligible | gpt-5-nano-2025-08-07 | A | full | classification | none (aux./judge role only) | low | no_number | LLM Detection as an Intervention: Downstream Impact under S… |
| W4401727214 | ineligible | unresolved | C | none | other | none (mention only) | low | no_number | Generative Artificial Intelligence in Education: Advancing… |
| W4409369309 | eligible | gpt-4-turbo-2024-04-09 | S | partial | generation | Verilog pass-rate=94.2 (156) | mid | - | VerilogCoder: Autonomous Verilog Coding Agents with Graph-b… |
| W4406960022 | ineligible | unresolved | C | none | mcq | none (mention only) | low | no_number | Accuracy of latest large language models in answering multi… |
| W4407719631 | ineligible | unresolved | C | none | mcq | none (mention only) | low | webui, no_number | Artificial intelligence in healthcare education: evaluating… |
| W4405764234 | ineligible | unresolved | C | none | other | none (mention only) | low | no_number | Large language models facilitating modern molecular biology… |
| W4410617211 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | IQC accuracy, five-shot=95 (40) | low | data_closed | Large language model-based multimodal system for detecting… |
| W4404396586 | eligible | gpt-4o-2024-05-13 | S | partial | agentic | WebArena completion (test)=30.5 (390) | high | - | Magentic-One: A Generalist Multi-Agent System for Solving C… |
| W4411120021 | eligible | gpt-4o-2024-05-13 | B | partial | agentic | Success Rate, ToolQuery-Unified=0.366 (60) | low | - | xLAM: A Family of Large Action Models to Empower AI Agent S… |
| W4415048600 | ineligible | unresolved | C | none | other | none (mention only) | low | no_number | Edge intelligence unleashed: a survey on deploying large la… |
| W4410187609 | ineligible | unresolved | S | none | mcq | correct-answer rate, GPT-4V=71 (n/a) | low | webui | Image Recognition Performance of GPT-4V(ision) and GPT-4o i… |
| W4402670978 | maybe | gpt-4-turbo-2024-04-09 | S | full | extraction | Avg Acc (PoT), testmini=62.9 (n/a) | mid | - | DocMath-Eval: Evaluating Math Reasoning Capabilities of LLM… |
| W4404782900 | eligible | gpt-4o-2024-05-13 | S | full | extraction | Recall@20 reranking, Avg Specific=79.2 (597) | mid | - | LitSearch: A Retrieval Benchmark for Scientific Literature… |
| W4414296875 | maybe | gpt-4o-2024-05-13 | S | partial | extraction | extraction accuracy, chat-5-RCT=73.4 (n/a) | mid | - | Automating the data extraction process for systematic revie… |
| W4403694843 | ineligible | unresolved | C | none | classification | none (mention only) | low | webui, no_number | The Role of Artificial Intelligence in Diagnostic Radiology |
| W4411120188 | eligible | gpt-4o-2024-05-13 | S | full | classification | hate-speech accuracy (en/US)=75.8 (300) | mid | - | Multi3Hate: Multimodal, Multilingual, and Multicultural Hat… |
| W4411119711 | eligible | gpt-4-turbo-2024-04-09 | B | partial | classification | Balanced Accuracy, zero-shot=55.96 (750) | high | - | FaithBench: A Diverse Hallucination Benchmark for Summariza… |
| W4399836654 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | other | none (aux./judge role only) | low | no_number | From Crowdsourced Data to High-Quality Benchmarks: Arena-Ha… |
| W4403045779 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | comprehensiveness score=3.72 (100) | low | data_closed | Physician- and Large Language Model-Generated Hospital Disc… |
| W4404781378 | eligible | gpt-4o-2024-05-13 | S | full | other | R-squared vs. citations, 2024=0.178 (171) | low | - | Learning the Bitter Lesson: Empirical Evidence from 20 Year… |
| W4400375223 | maybe | gpt-4-turbo-2024-04-09 | B | partial | extraction | Avg score, 9 QA/dialogue sets=38.6 (n/a) | mid | - | RankRAG: Unifying Context Ranking with Retrieval-Augmented… |
| W4408069345 | ineligible | gpt-4-turbo-2024-04-09 | S | none | extraction | Answer Relevance (RAGAS)=0.971 (n/a) | low | data_closed | Accurate AI Assistance in Contract Law Using Retrieval-Augm… |
| W4407230212 | ineligible | unresolved | C | none | classification | none (mention only) | low | no_number | Leveraging on large language model to classify sentences: a… |
| W4415130052 | ineligible | unresolved | C | none | mcq | none (mention only) | low | webui, no_number | Evaluating AI performance in infectious disease education:… |
| W4411119343 | eligible | gpt-4-turbo-2024-04-09 | B | full | classification | QAS accuracy, GPT-4-turbo judge=83.8 (450) | high | - | Are LLM-Judges Robust to Expressions of Uncertainty? Invest… |
| W4411613311 | ineligible | unresolved | C | none | other | none (mention only) | low | no_number | Large Language Models in Traditional Chinese Medicine: A Sh… |
| W4403369842 | ineligible | unresolved | C | full | classification | none (mention only) | low | no_number | Evaluating the Performance of Large Language Models for SDG… |
| W4412889516 | maybe | gpt-4-turbo-2024-04-09 | S | partial | extraction | Avg QA accuracy (with docs)=88.99 (n/a) | mid | - | KnowShiftQA: How Robust are RAG Systems when Textbook Knowl… |
| W4411120829 | ineligible | dead-preview | S | partial | classification | precision/recall/F1=0.79 (n/a) | low | dead_alias | Algorithmic Behaviors Across Regions: A Geolocation Audit o… |
| W4416034537 | ineligible | unresolved | C | none | extraction | none (mention only) | low | no_number | Enhancing Financial RAG with Agentic AI and Multi-HyDE: A N… |
| W4403569908 | eligible | gpt-4-turbo-2024-04-09 | S | partial | generation | BLEU-1, scene understanding=54.01 (12200) | high | - | EmbodiedCity: A Benchmark Platform for Embodied Agent in Re… |
| W4400487307 | maybe | gpt-4-turbo-2024-04-09 | B | partial | generation | avg score, baseline (no PAS)=59.25 (n/a) | mid | - | PAS: Data-Efficient Plug-and-Play Prompt Augmentation System |
| W4416529366 | ineligible | gpt-4-turbo-2024-04-09 | S | none | extraction | none (no usable number) | low | no_number | Automated Archival Descriptions with Federated Intelligence… |
| W4396820880 | eligible | gpt-4-turbo-2024-04-09 | S | partial | extraction | MSE, 1-day volatility=2.198 (500) | mid | - | ECC Analyzer: Extract Trading Signal from Earnings Conferen… |
| W4412889115 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | F1, Simple Benchmark=0.32 (n/a) | mid | - | Virtual CRISPR: Can LLMs Predict CRISPR Screen Results? |

## Observations

- Alias resolution: this group is dominated by bare `gpt-4-turbo` mentions (rows 16-49 of the CSV). Of the 34 such papers, only a handful (VerilogCoder, DocMath-Eval, Arena-Hard/BenchBuilder, FaithBench, EMBER, RankRAG, PAS, ECC Analyzer, Virtual CRISPR, EmbodiedCity, Archival Descriptions) actually run gpt-4-turbo themselves with a resolvable date; most of the rest use 'GPT-4 Turbo' only to name a consumer product's undisclosed backend (Microsoft Copilot, in five separate papers) or in a citation/survey aside, which the alias screen cannot distinguish from a genuine experiment.
- Mention-only and role C/A dominate ineligibility: 13 papers cite gpt-4-turbo only in prose, a reference list, a release-notes aside, or as a data-generation/judge auxiliary (PolyGuard-style), with no number tied to the authors' own run of that model.
- Webui is a recurring, easily-missed blocker: five clinical/education comparison papers (dentistry MCQs, cardiovascular pharmacology, infectious disease, X-ray diagnosis, ophthalmology quiz) run ChatGPT/Copilot/Gemini through consumer chat interfaces rather than a pinned API snapshot; one of these was caught only by checking for 'https://chat.openai.com/' in the text.
- A single explicit preview string overturned a 'post-GA alias' assumption: the YouTube COVID-19 geolocation audit names 'GPT-4 Turbo (v1106)' outright, so it resolves to dead-preview (`dead_alias`) despite a 2025 publication date and an otherwise clean, well-documented classification result.
- Judge/detector-benchmarking papers (J4R, FaithBench, EMBER) are the strongest eligible cluster: the still-callable model's own judging accuracy against a benchmark's gold labels is treated as role B, analogous to the CoT-detector precedent in group 1, and all three print their judge prompt in full.
- Data closure blocks several otherwise-clean role-S candidates: private clinical images/records (MOSAIC ocular-surface images, UCSF discharge summaries) and an unreleased legal question set each have a real API-based experiment and a clean metric but no public data.
- Cost skews high whenever the live model is o-series or the task is agentic/multimodal: J4R (o1, pairwise judging with order-swap), EMBER (GPT-4-turbo judge), Magentic-One and EmbodiedCity (agentic/vision-language multi-step tasks), and the compositional-math paper (o3-mini with 16k-token reasoning) all land in the high tier; gpt-4.1-nano and gpt-4o classification tasks with small n stay low.
