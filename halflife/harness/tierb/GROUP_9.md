# Tier B triage, group 9 (50 papers)

Counts: eligible 5, maybe 11, ineligible 34.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md`. Order follows `data/tierb_triage/group_9.csv` (rank). `no_prompt` is used when the only defect is that the prompt is not printed in the paper.

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4400518691 | maybe | gpt-4-turbo-2024-04-09 | S | full | agentic | LLaMA-3-Eval insight score=0.56 (100) | high | - | InsightBench: Evaluating Business Analytics Agents Through… |
| W4407310178 | ineligible | gpt-4-turbo-2024-04-09 | S | none | generation | max-similarity>0.7 rate=3.35% (6917) | high | no_prompt | On the Possibility of Breaking Copyleft Licenses When Reusi… |
| W7165423539 | ineligible | gpt-5-2025-08-07 | S | none | extraction | 1st-pass rate~0.85 (30, figure) | low | no_prompt, data_closed | Dual-Agent Framework for Cross-Model Verified Translation o… |
| W4414823918 | maybe | gpt-5-2025-08-07 | S | partial | generation | IntegratedScore=27.33 (214) | high | - | Dr. Bench: A Multidimensional Evaluation for Deep Research… |
| W4405903187 | ineligible | dead-preview | A | none | generation | none (dead 1106 judge; baseline rows) | low | dead_alias, no_prompt, no_number | DeepSeek-V3 Technical Report |
| W4398865217 | maybe | gpt-4-turbo-2024-04-09 | B | partial | extraction | micro-F1 NCBI=0.83 (475) | low | - | Evaluating Large Language Models for Public Health Classifi… |
| W7125649495 | maybe | gpt-4.1-nano-2025-04-14 | S | full | extraction | passage-level F1=0.566 (200 policies) | low | - | Word-level Annotation of GDPR Transparency Compliance in Pr… |
| W4403578009 | ineligible | gpt-4o-2024-05-13 | A | full | other | none (data conversion) | low | no_number | Understanding the Role of LLMs in Multimodal Evaluation Ben… |
| W4414586724 | ineligible | gpt-4-turbo-2024-04-09 | B | none | mcq | accuracy MMLU-Pro=0.68 (n/a) | low | no_prompt | Multi-Agent Collaboration via Evolving Orchestration |
| W7168433496 | ineligible | gpt-4o-2024-05-13 | S | none | agentic | breach rate=2.1% (1000 runs) | mid | no_prompt | Heterogeneous Agent Cohorts for Safe Open-Ended Exploration… |
| W4406490347 | ineligible | gpt-4-turbo-2024-04-09 | S | full | other | none (DBMS benchmark outcomes) | low | no_number | Is Large Language Model Good at Database Knob Tuning? A Com… |
| W7127041604 | ineligible | gpt-4-turbo-2024-04-09 | B | none | generation | Pass@1 EW-Fin=68.2 (400) | mid | no_prompt, data_closed | Exploration of AI Software Generation Methods Based on Work… |
| W4399554416 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | classification | accuracy (figure only) | high | no_number | How Far Can Transformers Reason? The Globality Barrier and… |
| W4416184585 | ineligible | unresolved | C | full | classification | none (citation) | low | no_number | A High-Scale Assessment of Social Media and Mainstream Medi… |
| W4416264796 | ineligible | gpt-4.1-nano-2025-04-14 | C | partial | generation | none (excluded model) | low | no_number, human_outcome | Seeing History Unseen: Evaluating Vision-Language Models fo… |
| W7165816542 | ineligible | o4-mini-2025-04-16 | S | none | agentic | solve rate=78.15% (2622 violations) | high | no_prompt | A11YRepair: Bridging Web Accessibility Barriers via Knowled… |
| W4400480600 | maybe | gpt-4-turbo-2024-04-09 | S | partial | generation | pass rate lc100 base=98% (100) | low | - | Enhancing Computer Programming Education with LLMs: A Study… |
| W4404370652 | maybe | gpt-4o-2024-05-13 | S | full | generation | nDCG@10 Core17 P-2=0.522 (50 topics) | low | - | Data Fusion of Synthetic Query Variants With Generative Lar… |
| W4404782508 | eligible | gpt-4o-2024-05-13 | S | full | other | overall score=37.0 (700) | high | - | ToolBeHonest: A Multi-level Hallucination Diagnostic Benchm… |
| W4403577181 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | extraction | type accuracy=93.88 (n/a) | mid | no_prompt, data_closed | ChatHouseDiffusion: Prompt-Guided Generation and Editing of… |
| W4414865824 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | top-1 accuracy=0.2222 (9) | low | no_prompt, data_closed | LLM-based multi-agent system for neuro-ophthalmic diagnosis… |
| W7166799387 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | L1 overall accuracy=100.0 (100) | low | - | Diagnosing and Mitigating Sycophancy and Skepticism in LLM… |
| W4403344681 | ineligible | gpt-4-turbo-2024-04-09 | S | none | mcq | static cognition acc=69.7 (n/a) | mid | no_prompt | EgoSocialArena: Benchmarking the Social Intelligence of Lar… |
| W4405693128 | ineligible | unresolved | C | none | other | none (review) | low | no_number | Exploring LLMS, A Systematic Review with SWOT Analysis |
| W7133182881 | ineligible | gpt-4o-2024-05-13 | S | partial | generation | rubric score (human) (79) | low | human_outcome, data_closed | Automating crash diagram generation using vision-language m… |
| W4414758400 | maybe | gpt-4-turbo-2024-04-09 | S | full | generation | female share vanilla=51.5% (600) | low | - | Mitigation of Gender and Ethnicity Bias in AI-Generated Sto… |
| W4416037849 | maybe | o3-mini-2025-01-31 | S | partial | classification | SRC RP F1=71.22 (400) | mid | - | CRAB: A Benchmark for Evaluating Curation of Retrieval-Augm… |
| W4404569958 | ineligible | unresolved | C | full | agentic | none (comparison table) | low | no_number | A Novel MLLM-based Approach for Autonomous Driving in Diffe… |
| W7203504196 | ineligible | unresolved | C | partial | other | none (related work) | low | no_number | LLMs in Process Diagram Engineering: From Optimal PFDs to V… |
| W4406055323 | ineligible | unresolved | A | full | generation | none (judge) | low | no_number | Data-Centric Human Preference with Rationales for Direct Pr… |
| W7125760104 | maybe | gpt-4.1-nano-2025-04-14 | S | partial | agentic | acquiescence=9.3% (75) | low | - | SycoEval-EM: Sycophancy Evaluation of Large Language Models… |
| W7166808309 | eligible | gpt-4.1-nano-2025-04-14 | S | full | classification | HIT@1 HIGH=19.9 (381) | low | - | From Sparse to Sense-Grounded: Wikipedia Training for Ukrai… |
| W4417409739 | maybe | gpt-5-2025-08-07 | S | partial | generation | judge score All=58.0 (646) | mid | - | ProMQA-Assembly: Multimodal Procedural QA Dataset on Assemb… |
| W4414787361 | ineligible | gpt-5-2025-08-07 | S | none | classification | diagnostic accuracy=86.6 (n/a) | high | no_prompt, data_closed, tos | MACD: Multi-Agent Clinical Diagnosis with Self-Learned Know… |
| W4404783788 | eligible | gpt-4o-2024-05-13 | S | full | generation | LC avg score=48.67 (1930) | high | - | Retrieval Augmented Generation or Long-Context LLMs? A Comp… |
| W4412889963 | ineligible | gpt-4-turbo-2024-04-09 | B | full | extraction | none (human-annotated outputs) | mid | human_outcome, no_number | Improving Automatic Evaluation of Large Language Models (LL… |
| W4414156829 | ineligible | gpt-5-2025-08-07 | C | partial | agentic | none (leaderboard table) | low | no_number | AI Agents for Economic Research |
| W4397048985 | eligible | gpt-4o-2024-05-13 | S | full | classification | HAM10000 many-shot acc=53.59 (210) | high | - | Many-Shot In-Context Learning in Multimodal Foundation Mode… |
| W4399992121 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | generation | none (query generator) | low | data_closed, no_number | Evaluating RAG-Fusion with RAGElo: an Automated Elo-based F… |
| W4404342216 | eligible | o3-mini-2025-01-31 | S | full | classification | EQINFER F1=47.98 (4196) | high | - | AAAR-1.0: Assessing AI's Potential to Assist Research |
| W4405767534 | ineligible | unresolved | C | full | classification | none (related work) | low | no_number | Assessing UML Diagrams by GPT: Implications for Education |
| W4416033599 | ineligible | unresolved | A | full | classification | none (QA-pair derivation) | low | no_number | Investigating Factuality in Long-Form Text Generation: The… |
| W4416036562 | ineligible | unresolved | C | full | generation | none (related work) | low | no_number | Are Checklists Really Useful for Automatic Evaluation of Ge… |
| W7142558072 | ineligible | o4-mini-2025-04-16 | S | none | generation | ECE Primary=71.8 (n/a) | mid | no_prompt | Can MLLMs Read Students' Minds? Unpacking Multimodal Error… |
| W4393253309 | ineligible | gpt-4-turbo-2024-04-09 | B | none | extraction | mean accuracy synthetic=0.939 (n/a) | low | no_prompt | Assessing the Feasibility of Processing a Paper-based Multi… |
| W7203975634 | ineligible | gpt-4-turbo-2024-04-09 | S | none | generation | checklist coverage (human) (10) | low | webui, no_prompt, human_outcome | Large Language Models as Simulated Candidates in Objective… |
| W4412888445 | ineligible | gpt-4-turbo-2024-04-09 | S | none | generation | accuracy (figure/appendix) | mid | no_prompt | Reasoning Does Not Necessarily Improve Role-Playing Ability |
| W4416036421 | ineligible | gpt-4-turbo-2024-04-09 | A | full | other | none (data construction) | low | no_number | IL-PCSR: Legal Corpus for Prior Case and Statute Retrieval |
| W7128069593 | ineligible | unresolved | C | partial | agentic | none (demo) | low | no_number | Employing GPT and NeRF for Intelligent Robotic-Controlled B… |
| W4402702436 | ineligible | unresolved | S | partial | generation | trace quality (figure) | low | webui | Towards Synthetic Trace Generation of Modeling Operations u… |

## Observations

- Alias resolution: 33 of the 50 rows carry a bare `gpt-4-turbo` in `live_ids`, but only 7 papers pin `gpt-4-turbo-2024-04-09` in the text (W4400518691, W4399554416, W4404782508, W4397048985, W4399992121, W4393253309, W7203975634). Seven of the bare mentions are citations, comparison tables or related-work sentences (role C: W4416184585, W4405693128, W4404569958, W7203504196, W4405767534, W4416036562, W7128069593) and one is the dead 1106 judge (W4405903187); the remaining post-2024-07 papers were resolved to 2024-04-09 by the alias rule, and two web-interface studies stay unresolved (W4402702436) or webui-blocked (W7203975634).
- Role is the largest single reason for ineligibility: 9 papers use the live id only in a citation, comparison table or leaderboard reproduction (C) and 6 use it only as a data generator, query generator or judge (A). In four of these the model actually run is an undated or off-list `GPT-4o`, `GPT-4o-mini` or `GPT-4.1` (W4405767534, W4416036562, W4416184585, W4416036421).
- Missing prompts block most of the papers that did run the live model: 15 records carry `no_prompt`, typically because the templates were moved to a supplement or repository (W4414865824, W4414787361, W7203975634, W4393253309, W7165816542, W4412888445, W4403344681) or only described in prose (W4407310178, W7165423539, W7142558072). Three further papers print their prompts only as image figures whose text is not in the extraction (W4398865217, W4400480600, W4404342216); these need a PDF check.
- Agentic and multi-agent systems are common in this group (InsightBench, Dr. Bench, Puppeteer, SESS-Lab cohorts, A11YRepair, MACD, the dual-agent lab-protocol parser, SycoEval-EM, the CARLA driving agent). Even when prompts are printed, the scaffold (code execution, validator loops, co-agent models) is only described, so these land at maybe (W4400518691, W4414823918, W7125760104) or ineligible. Judges in this group are mostly still callable (gpt-4o-2024-11-20, Claude Sonnet 4.6, Llama-3-70B, o3-mini); the only dead judge is gpt-4-1106-preview in W4405903187 and W4406055323.
- Data: 7 records are `data_closed` (unreleased ELISA protocols, EW-Bench, floor-plan texts, ophthalmology cases, police crash reports, MIMIC-IV with its API-use restriction, Infineon documents) and 6 more are `partial` because of licensing or unconfirmed release (TREC collections in W4404370652, Assembly101 in W4417409739, the GDPR-Transparency-200 corpus in W7125649495, CausalT3-Seed in W7166799387, ScratchMath in W7142558072, the SDoH questionnaires in W4393253309).
- Numbers only in figures or from human raters: W4399554416 (plot), W4412888445 (bars/appendix), W7133182881 and W7203975634 (human rubric scoring of images/transcripts), W4412889963 (human-annotated outputs) are marked `no_number` or `human_outcome`. Cost: 4 of the 5 eligible claims are high-tier (ToolBeHonest 2,100 calls per run, RAG-vs-LC 1,930 long-context calls, AAAR EQINFER 4,196 o3-mini calls, image-heavy many-shot ICL); the cheap eligible run is the gpt-4.1-nano Visual-WSD baseline (381 calls). Cheap maybe checks: W7166799387 L1 (100 calls), W4400480600 (100), W4404370652 (50), W4414758400 (25 batches).
