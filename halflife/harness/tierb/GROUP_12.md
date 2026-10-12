# Tier B triage, group 12 (50 papers)

Counts: eligible 7, maybe 8, ineligible 35.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md` (plus the `no_prompt` blocker). Order follows `data/tierb_triage/group_12.csv` (rank).

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4402953190 | ineligible | gpt-4-turbo-2024-04-09 | B | none | classification | sentence-level hallucination classification weighted F1 (wF1)=73.16... | mid | no_prompt | Pre-Training Multimodal Hallucination Detectors with Corrup… |
| W4415035710 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | Welch t-statistic (p) male vs female Shannon entropy, Education cat... | mid | - | Do LLMs have a Gender (Entropy) Bias? |
| W4404311505 | maybe | o1-2024-12-17 | B | full | generation | Pass@1 overall (execution-output match on BCVPP)=67.78 (90) | high | - | MaCTG: Multi-Agent Collaborative Thought Graph for Automati… |
| W7204232084 | ineligible | gpt-5-mini-2025-08-07 | A | full | classification | judge vs arbitrated human labels: exact match (%)=76 (50) | low | no_number | Who is the Agent to Blame? Localizing Faithfulness and Cita… |
| W4411120175 | eligible | gpt-4o-2024-05-13 | B | full | generation | existing generated references in Semantic Scholar (% of all referen... | mid | - | Large Language Models Reflect Human Citation Patterns with … |
| W4412944691 | ineligible | gpt-4o-2024-05-13 | S | none | agentic | accuracy (% of tasks with correct reproducibility score)=21.4 (112) | high | no_prompt | REPRO-Bench: Can Agentic AI Systems Assess the Reproducibil… |
| W4404188613 | ineligible | unresolved | B | none | other | task-planning accuracy (%) on MathComp=84.67 (n/a) | mid | data_closed, no_prompt, dead_alias | Knowledge Graph Modeling-Driven Large Language Model Operat… |
| W4402385945 | maybe | gpt-4-turbo-2024-04-09 | S | partial | extraction | edges retrieval F1, Task 1 Graph Reconstruction, 0-shot=66.8 (125) | low | - | PLUGH: A Benchmark for Spatial Understanding and Reasoning … |
| W7134094238 | maybe | gpt-4o-2024-05-13 | S | full | generation | KL divergence of the LLM action distribution from uniform, with the... | low | - | BioLLMAgent: A Hybrid Framework with Enhanced Structural In… |
| W4416259485 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | mean accuracy across seven criteria (3 runs)=0.85 (35) | low | - | Benchmarking PDF Accessibility Evaluation A Dataset and Fra… |
| W4402510068 | ineligible | gpt-4-turbo-2024-04-09 | C | none | classification | accuracy (organizer baseline, bar chart only) (figure only) | low | no_number | Chinese Metaphor Recognition Using a Multi-stage Prompting … |
| W4416613039 | ineligible | unresolved | C | full | classification | none | low | no_number | Evaluating AI capabilities in detecting conspiracy theories… |
| W4417302310 | maybe | o3-mini-2025-01-31 | S | partial | generation | pass@1 (%) on AutoGEEval-Bench=56.98 (1325) | high | - | AutoGEEval: A Multimodal and Automated Framework for Geospa… |
| W4416934502 | ineligible | unresolved | C | none | other | none | low | no_number | From Red AI to Green AI: A Unified Survey of Lifecycle Cost… |
| W7166862368 | ineligible | o4-mini-2025-04-16 | S | full | mcq | accuracy (%) averaged over 11 specialties, ClinBenchText=45.4 (2000) | mid | data_closed | Benchmarking LLMs on Authentic Cases from Medical Journals |
| W7202288916 | ineligible | gpt-5-2025-08-07 | S | none | mcq | overall mean accuracy across 5 seeds, pooled question types=0.537 (... | mid | data_closed, no_prompt | Toward Human Rights Benchmarking for LLMs: A Pilot Methodol… |
| W4411113186 | ineligible | gpt-4-turbo-2024-04-09 | B | none | extraction | log-parsing grouping accuracy (GA, %) averaged over 16 Loghub datas... | mid | no_prompt | LogRules: Enhancing Log Analysis Capability of Large Langua… |
| W4407374917 | eligible | gpt-4o-2024-05-13 | S | full | classification | mean accuracy (%) species presence, Task 1a (coordinates), scores b... | low | - | Large language models possess some ecological knowledge, bu… |
| W4412699263 | ineligible | unresolved | S | none | mcq | accuracy (correct answers)=78.3 (120) | low | webui, no_prompt | Performance of the ChatGPT-4o Language Model in Solving the… |
| W4403322813 | maybe | gpt-4-turbo-2024-04-09 | B | full | mcq | accuracy (%) on AfriMed-QA expert-level multiple-choice questions, ... | mid | - | KGARevion: An AI Agent for Knowledge-Intensive Biomedical QA |
| W4410313682 | ineligible | o1-2024-12-17 | S | none | agentic | resolved rate (%) on Python, MagentLess=48.2 (500) | high | no_prompt | Multi-SWE-bench: A Multilingual Benchmark for Issue Resolvi… |
| W4404518640 | ineligible | gpt-4-turbo-2024-04-09 | S | none | generation | mean cosine distance between GPT-4 arguments and the State's argume... | low | aux_model_dead, no_prompt | Legal Minds, Algorithmic Decisions: How LLMs Apply Constitu… |
| W4416095533 | ineligible | gpt-4-turbo-2024-04-09 | S | full | classification | mean difference LLM minus human grade (10-point scale)=-1.34 (557) | mid | data_closed | ChatGPT for automated grading of short-answer questions in … |
| W7134885605 | eligible | gpt-5-2025-08-07 | S | full | classification | accuracy for the LOCAL (localized-disease eligibility) label, abstr... | mid | - | More Signal vs. More Noise - Comparing Full Text and Abstra… |
| W7164760565 | ineligible | gpt-4o-2024-05-13 | A | none | generation | none | low | no_number, webui | Analyzing the Multilingual Ability of Vision-Language Model… |
| W4412888200 | ineligible | gpt-4-turbo-2024-04-09 | B | none | generation | Arena-hard score with P3-optimized prompts=78.0 (500) | high | no_prompt, aux_model_dead | P3: Prompts Promote Prompting |
| W7126122929 | ineligible | gpt-4.1-nano-2025-04-14 | A | full | generation | none | low | no_number | Beyond Divergent Creativity: A Human-Based Evaluation of Cr… |
| W7165973413 | ineligible | unresolved | C | none | other | none | low | no_number | Transformer-Based Language Models Across Domain Verticals: … |
| W7131319772 | eligible | gpt-5-mini-2025-08-07 | S | full | classification | agreement (%) with jury labels on the combined evaluation set=99.0 ... | low | - | Can Large Language Models Replace Human Coders? Introducing… |
| W7167154566 | eligible | gpt-4.1-nano | S | full | classification | Cohen's kappa (within-one agreement) of AnthroIndex vs expert conse... | low | - | Anthropomorphism in AI Companion Communities: Age, Gender, … |
| W7155247005 | ineligible | gpt-4.1-nano | S | none | agentic | baseline task correctness (%) judged by the LLM ensemble=45.3 (450) | mid | no_prompt | Auditing Automated Evaluation, Error Propagation, and Runti… |
| W4410110677 | eligible | o1-2024-12-17 | S | full | classification | F1 score, positive-vs-negative trial classification, title-and-abst... | high | - | Large Language Models for Supporting Clear Writing and Dete… |
| W7118052377 | ineligible | o4-mini-2025-04-16 | S | none | mcq | KCL-MCQA score (%), vanilla (without supporting precedents)=37.7 (283) | mid | no_prompt | Korean Canonical Legal Benchmark: Toward Knowledge-Independ… |
| W4404330874 | ineligible | unresolved | C | none | other | none | low | no_number | GPT-4o System Card |
| W4411119597 | ineligible | gpt-4o-2024-05-13 | S | partial | agentic | Pass@1 (%) on SWE-bench Lite with CodexGraph=22.96 (300) | high | no_prompt | CodexGraph: Bridging Large Language Models and Code Reposit… |
| W4404839867 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | Cohen's kappa vs instructor scores, best prompt=0.704 (2242) | mid | data_closed | Prompt Engineering for Automatic Short Answer Grading in Br… |
| W4404784038 | ineligible | gpt-4-turbo-2024-04-09 | B | none | generation | d-BLEU, literary test set=47.8 (240) | high | no_prompt | TransAgents: Build Your Translation Company with Language A… |
| W4406482922 | ineligible | unresolved | C | none | other | none | low | no_number | LLM-based Human Simulations Have Not Yet Been Reliable |
| W4404313190 | maybe | gpt-4-turbo-2024-04-09 | B | full | agentic | Average Success Rate (ASR, %) for first-order stable systems, fast ... | mid | - | ControlAgent: Automating Control System Design via Novel In… |
| W4403759556 | ineligible | gpt-4o-2024-05-13 | S | full | generation | primary-diagnosis accuracy, Condition 2 (with quiz premise)=26.7 (150) | low | human_outcome | "This Is a Quiz" Premise Input: A Key to Unlocking Higher D… |
| W4411120249 | maybe | gpt-4o-2024-05-13 | B | partial | extraction | performance (%) on the Counting Characters task, 0-shot=77.4 (n/a) | mid | - | From Introspection to Best Practices: Principled Analysis o… |
| W4403345534 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | generation | none | low | no_number | MentalArena: Self-play Training of Language Models for Diag… |
| W7166812239 | ineligible | gpt-4-turbo-2024-04-09 | S | none | generation | execution accuracy (%) on JHD (h>=3), base (without SchemaScope)=42... | mid | data_closed, no_prompt | SchemaScope: How Join-Hop Depth Breaks Text-to-SQL in Large… |
| W4416036191 | ineligible | gpt-4o-2024-05-13 | B | partial | generation | win-rate vs Claude 3.5 Sonnet on MathOdyssey-Olympiad, no hint=40.2... | mid | aux_model_dead | Graders Should Cheat: Privileged Information Enables Expert… |
| W4402856762 | ineligible | gpt-4-turbo-2024-04-09 | B | none | mcq | InfiniteBench En.MC accuracy=77.73 (229) | high | no_prompt | ChatQA 2: Bridging the Gap to Proprietary LLMs in Long Cont… |
| W4414322202 | ineligible | gpt-4-turbo-2024-04-09 | B | none | mcq | accuracy (%) on the 2021 ACR TXIT exam, RAG with textbook + NCCN=77... | low | no_prompt, data_closed | Development of a RAG-based Expert LLM for Clinical Support … |
| W7166883518 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | mcq | average score (Avg.) across the performance-oriented metrics=63.6 (... | high | no_prompt | Pub-LawBench: Public-Oriented Benchmarking for LegalAI |
| W7169923556 | ineligible | gpt-4-turbo-2024-04-09 | B | none | generation | mean Standard (rubric-weighted partial-credit) score, %=63.9 (615) | high | data_closed | Frontier AI performance across the business disciplines: a … |
| W4411119648 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | Attack Success Rate (%) on SafetyQuizzer questions=13.4 (n/a) | mid | aux_model_dead | SafetyQuizzer: Timely and Dynamic Evaluation on the Safety … |
| W7133570722 | ineligible | unresolved | C | none | other | none | low | no_number | Sustainable Code Generation Using Large Language Models: A … |

Observations

- Agentic systems dominate the ineligible set with a live subject model: REPRO-Bench, Multi-SWE-bench, CodexGraph and AgentProp-Bench all pin a snapshot, but the prompts sent to the model are assembled at runtime by third-party scaffolds, so the record carries `no_prompt` even when the paper is otherwise careful. The deep-research paper pins gpt-5-mini-2025-08-07 only as the judge (role A).
- Execution-scored code benchmarks (MaCTG/BCVPP, AutoGEEval on Google Earth Engine, ControlAgent/ControlEval) print their prompts and publish their items, but re-execution needs a runner or simulator, so they land in `maybe` with a high or mid cost tier rather than eligible.
- Six of the seven eligible papers are single-call classification or short generation tasks with the system prompt printed in the Methods section (oncology trial labels with gpt-5, spin detection with o1, ecological presence with gpt-4o-2024-05-13, AnthroIndex with gpt-4.1-nano, ContentBench with GPT-5 Mini, citation suggestions with gpt-4o-2024-05-13); they are cheap except where o-series reasoning is involved.
- The alias screen produced several false positives: in ContentBench, the conspiracy-detection paper, the Chinese-metaphor paper, the two surveys, the position paper and the GPT-4o System Card, 'GPT-4 Turbo' is only a citation, a pricing remark or an organizer baseline. ContentBench nevertheless yields an eligible record through GPT-5 Mini, which the screen did not list.
- Two papers list 'GPT-4 Turbo' next to a separate 'GPT-4-1106' row (PEOA LLM OS, Graders Should Cheat), leaving the alias ambiguous even though the papers post-date the GA release; both are ineligible on other grounds as well.
- Auxiliary-model decay is a recurring blocker: AlpacaEval/Arena-hard judges (gpt-4-1106-preview), retired Claude 3.5 Sonnet and Gemini 1.5 graders, Chinese commercial evaluator LLMs, and an unreleased fine-tuned embedder all break otherwise well-specified numbers.
