# Tier B triage, group 6 (50 papers)

Counts: eligible 3, maybe 15, ineligible 32.

Blocker vocabulary: the SCHEMA.md list plus `no_prompt` (prompt not printed and no other listed blocker applies). Role A/C records carry `no_number` because no reported number is produced by the live model as a subject.

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost tier | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4412887918 | ineligible | gpt-4o-2024-05-13 | S | partial | other | attack success rate (text baseline)=0.1 (n=500) | mid | tos | The Structural Safety Generalization Problem |
| W4416035547 | eligible | o4-mini-2025-04-16 | S | full | classification | identification accuracy (identifier o4-mini, target o4-mini, Math)=0.93 (n=100) | mid | - | Agent-to-Agent Theory of Mind: Testing Interlocutor Awarenes |
| W7197053618 | maybe | gpt-5-2025-08-07 | S | partial | generation | LLM-as-a-judge overall score (1-7), ICLR 2026=6.7 (n=50) | high | - | AI-Assisted Peer Review Across Research Communities: From Re |
| W4414789220 | maybe | o4-mini-2025-04-16 | S | full | classification | Cohen's kappa, causal substance=0.662 (n=2619) | mid | - | Application of Large Language Models (LLM) for Automatic Cla |
| W4400222256 | ineligible | gpt-4o-2024-05-13 | B | none | other | accuracy on synthetic math test set=91.2 (n=11600) | high | data_closed,no_prompt | Scaling Synthetic Data Creation with 1,000,000,000 Personas |
| W4402671726 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | RAGAS context relevance (judge output)=93.4 (n=150) | low | no_number | To Generate or to Retrieve? On the Effectiveness of Artifici |
| W4404792844 | ineligible | gpt-4-turbo-2024-04-09 | A | full | agentic | none | low | no_number | Ask-before-Plan: Proactive Language Agents for Real-World Pl |
| W7125352730 | ineligible | unresolved | C | none | other | none | low | no_number | LLMOrbit: A Circular Taxonomy of Large Language Models -From |
| W4415332119 | maybe | gpt-4.1-nano-2025-04-14 | B | full | agentic | success rate, MultiWOZ, collaborative user=23.6 (n=356) | mid | - | Non-Collaborative User Simulators for Tool Agents |
| W4402698999 | ineligible | dead-preview | B | full | other | R@5 with fallacy+passage judge, MISSCI=0.308 (n=84) | low | dead_alias | Grounding Fallacies Misrepresenting Scientific Publications  |
| W4417210220 | maybe | gpt-5-2025-08-07 | S | partial | other | accuracy, FinanceBench oracle context, baseline prompt=0.94 (n=150) | mid | - | PRISM: Prompt-Refined In-Context System Modelling for Financ |
| W4414971412 | ineligible | gpt-4.1-nano-2025-04-14 | A | none | agentic | none | low | no_number | Doctor-R1: Mastering Clinical Inquiry with Experiential Agen |
| W4404990976 | maybe | gpt-4-turbo-2024-04-09 | B | full | mcq | accuracy, IC practice exam P1=72 (n=50) | low | - | Thai Financial Domain Adaptation of THaLLE -- Technical Repo |
| W4403006832 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | Bradley-Terry coefficient, human preference=0.558 (n=150) | mid | human_outcome | AI-Driven Review Systems: Evaluating LLMs in Scalable and Bi |
| W4404342653 | maybe | gpt-4o-2024-05-13 | B | partial | generation | Heron-Bench LLM-judge score (% of GPT-4 reference)=87.6 (n=102) | mid | - | Constructing Multimodal Datasets from Scratch for Rapid Deve |
| W4403795293 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | agentic | LitQA2 accuracy (old 147 questions)=64.4 (n=147) | high | data_closed | Language agents achieve superhuman synthesis of scientific k |
| W4404987838 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | other | none | low | no_number | Tulu 3: Pushing Frontiers in Open Language Model Post-Traini |
| W4406548626 | ineligible | gpt-4-turbo-2024-04-09 | C | full | generation | none | low | no_number | Solving the Unsolvable: Translating Case Law in Hong Kong |
| W4416033592 | ineligible | gpt-4.1-nano-2025-04-14 | A | partial | classification | none | low | no_number | It Depends: Resolving Referential Ambiguity in Minimal Conte |
| W4403570177 | eligible | gpt-4o-2024-05-13 | B | full | classification | pairwise accuracy, helpfulness set=0.815 (n=10067) | high | - | RMB: Comprehensively Benchmarking Reward Models in LLM Align |
| W4396244027 | ineligible | gpt-4.1-nano-2025-04-14 | C | partial | agentic | none | low | no_number | Large Language Model Agent as a Mechanical Designer |
| W4403159820 | ineligible | gpt-4-turbo-2024-04-09 | S | full | classification | accuracy, zero-shot mortality classification=0.57 (n=590) | low | data_closed | Large Language Models versus Classical Machine Learning: Per |
| W4403345634 | ineligible | gpt-4o-2024-05-13 | S | partial | generation | factor-level alignment tau (generation, summarization)=0.156 (n=?) | mid | no_number | Uncovering Factor Level Preferences to Improve Human-Model A |
| W7135428876 | maybe | gpt-4.1-nano-2025-04-14 | B | partial | classification | macro-averaged AUPRC over 15 DCR datasets=0.439 (n=16483) | mid | - | Large Language Models for Biomedical Article Classification |
| W4400434332 | ineligible | gpt-4-turbo-2024-04-09 | A | full | other | none | low | no_number | DotaMath: Decomposition of Thought with Code Assistance and  |
| W7104384491 | eligible | o3-2025-04-16 | B | full | classification | Micro-F1, Issue Type classification (Split base)=0.7968 (n=15481) | high | - | PILOT-Bench: A Benchmark for Legal Reasoning in the Patent D |
| W7167933623 | ineligible | gpt-4-turbo-2024-04-09 | S | full | classification | accuracy vs human adjudication, trial eligibility=85.5 (n=207) | low | data_closed | Assessment of Zero-Shot Large Language Model (LLM) Assisted  |
| W4406458936 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | classification | weighted F1, FakeNewsNet, zero-shot=81.7 (n=214) | low | data_closed | Large Language Models For Text Classification: Case Study An |
| W4405090298 | maybe | gpt-4o-2024-05-13 | S | partial | agentic | mean travel time on route 1, Scenario 1=22.29 (n=300) | mid | - | AI-Driven Day-to-Day Route Choice |
| W4416546105 | ineligible | unresolved | C | full | generation | none | low | no_number | Debunking with Dialogue? Exploring AI-Generated Counterspeec |
| W4404986534 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | alignment with human judgments, LLMEval2=61.54 (n=5106) | high | - | A Survey on LLM-as-a-Judge |
| W4404354758 | ineligible | dead-preview | B | partial | mcq | MedQA (US 4-option) accuracy, 5-shot=81.4 (n=1273) | mid | dead_alias | From Medprompt to o1: Exploration of Run-Time Strategies for |
| W4402712721 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | diagnosis accuracy, sequential prompt with rules and CoT=98.4 (n=250) | mid | - | Prompting Large Language Models for Supporting the Different |
| W4416036205 | ineligible | gpt-4-turbo-2024-04-09 | B | none | agentic | Final Pass Rate, travel plan evaluation=0.2 (n=500) | mid | no_prompt | RETAIL: Towards Real-world Travel Planning for Large Languag |
| W4403783611 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | attack detection rate=84.48 (n=3300) | high | - | Enhancing LLM-based Autonomous Driving Agents to Mitigate Pe |
| W4402387500 | ineligible | dead-preview | B | full | agentic | feedback-generator ratios (uplift/flat/downgrade)=n/a (n=100) | mid | dead_alias | Can We Rely on LLM Agents to Draft Long-Horizon Plans? Let's |
| W7172473576 | ineligible | gpt-4.1-nano-2025-04-14 | B | full | classification | quadratic weighted kappa, zero-shot difficulty prediction=0.123 (n=217) | low | data_closed | Can LLMs Really Understand Item Difficulty Levels? Implicati |
| W4409362526 | ineligible | gpt-4-turbo-2024-04-09 | B | none | other | overall score, TCoT=51.32 (n=886) | mid | no_prompt | TableBench: A Comprehensive and Complex Benchmark for Table  |
| W4404470015 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | anatomical region identification accuracy, ROCOv2 subset=78.0 (n=100) | low | - | Comparative Performance of Claude and GPT Models in Basic Ra |
| W7135028473 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | mcq | accuracy, ACCSAP cardiology MCQs (no RAG)=73.7 (n=449) | low | data_closed | Cardiology knowledge assessment of retrieval-augmented open  |
| W4403347060 | maybe | gpt-4-turbo-2024-04-09 | B | partial | classification | accuracy, SCL-90 symptom assessment=0.7561 (n=800) | mid | - | Multi-Session Client-Centered Treatment Outcome Evaluation i |
| W7104183057 | ineligible | unresolved | C | full | generation | none | low | no_number | LLMs as Judges: Toward The Automatic Review of GSN-compliant |
| W7160969382 | ineligible | o3-mini | S | partial | mcq | AIQ subtest accuracy=n/a (n=?) | low | data_closed,no_number | Uneven Evolution of Cognition Across Generations of Generati |
| W7131246555 | ineligible | gpt-5-2025-08-07 | S | full | mcq | accuracy, IOE entrance exam MCQs=83.13 (n=492) | mid | data_closed | A Study on the Performance of SOTA LLMs on Nepalese IOE Entr |
| W4405253355 | ineligible | unresolved | C | none | other | none | low | no_number | LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluati |
| W4403052068 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | accuracy of abstract inclusion, review 1=98 (n=492) | low | - | Large language models for abstract screening in systematic-  |
| W4412887717 | ineligible | unresolved | C | none | agentic | none | low | no_number | Aria-UI: Visual Grounding for GUI Instructions |
| W4405715387 | ineligible | gpt-4o-2024-05-13 | B | none | generation | mean volunteer rating (1-4), map description=3.68 (n=330) | low | human_outcome,data_closed | AutoLife: Automatic Life Journaling with Smartphones and LLM |
| W4410417118 | maybe | gpt-4.1-nano-2025-04-14 | S | full | classification | triage accuracy (45 vignettes x 10 trials)=44 (n=450) | low | - | ChatGPT Is Still Not Good Enough at Giving Care-Seeking Advi |
| W4404990196 | ineligible | gpt-4o-2024-05-13 | A | partial | other | none | low | no_number | Engineering AI Judge Systems |

Observations

- Role is the main filter: 14 of 50 papers use the live model only as a judge, annotator or data synthesizer (role A: W4402671726, W4404792844, W4414971412, W4404987838, W4416033592, W4400434332, W4404990196) or cite it without running it (role C: W7125352730, W4406548626, W4396244027, W4416546105, W7104183057, W4405253355, W4412887717). Two of the C cases are surveys (W7125352730, W4405253355); a third survey (W4404986534) contains its own meta-evaluation and is recorded as role S.
- Alias resolution: 'GPT-4 Turbo' without a snapshot appears in eight papers dated after 2024-07-01 and was resolved to gpt-4-turbo-2024-04-09 by the SCHEMA rule; two papers name the 1106-preview explicitly and one names 'GPT-4 Turbo (Nov 2023)' (dead_alias: W4402698999, W4402387500, W4404354758). Papers whose experiments may predate April 2024 (TableBench, HUDSON, anemia) could have used a preview snapshot; the resolution is a rule, not a verified fact.
- Catalog gaps: GPT-4.1 and GPT-4.1-mini (gpt-4.1-2025-04-14, gpt-4.1-mini-2025-04-14), gpt-4o-2024-08-06 and gpt-4o-mini-2024-07-18 are run as subjects in W4396244027, W7104183057, W4414971412, W4415332119, W4416033592 and W7172473576 but are not in the live_ids column, so those papers were judged only on the listed id (usually gpt-4.1-nano in an auxiliary role).
- Data closure is the most common hard blocker among role-S papers: clinical or proprietary inputs (W4403159820, W7167933623, W7135028473, W7172473576, W7131246555, W4405715387, W7160969382), a private retrieval corpus (W4403795293) and an unreleased synthetic test set (W4400222256). Partial availability (unlisted subsets, labels from prior work, vignettes in other papers) drives most 'maybe' verdicts (W4414789220, W4404470015, W4403052068, W4410417118, W4402712721).
- Judge models: where an LLM judge is needed it is usually the subject model itself (W7197053618 GPT-5, W4404342653 GPT-4o) or a still-callable mini model (gpt-4o-mini, gpt-4.1-nano/mini); no eligible or maybe record depends on a retired judge.
- Cost: two of the three eligible records are large benchmarks (RMB 10k pairs, PILOT-Bench 15k cases with long inputs) in the high tier, as is the LLMEval2 meta-evaluation (maybe); the low-tier candidates are small exam or vignette sets (THaLLE 100 items, radiology 100 images, care-seeking 450 calls) that carry a data-availability soft gap.
- Prompts: 'full' verbatim prompts are more common in medical and social-science preprints (tables of prompts) than in NLP benchmark papers, which often point to a GitHub repo (TableBench, RETAIL) or print only templates with dynamic placeholders (few-shot retrieval in W7135428876, schema injection in W7197053618).
