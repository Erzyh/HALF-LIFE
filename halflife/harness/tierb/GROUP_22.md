# Tier B triage, group 22 (49 papers)

Counts: eligible 8, maybe 8, ineligible 33.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md` (plus the `no_prompt` blocker). Order follows `data/tierb_triage/group_22.csv` (rank).

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4396945319 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | Cliff's delta (Wikipedia, GPT-4 row)=-0.828 (1200) | mid | tos | Many-Shot Regurgitation (MSR) Prompting |
| W4415697109 | ineligible | unresolved | C | none | other | none | low | webui, no_number, alias_unpinned | Context of collaborative human-machine systems architecture… |
| W7172391418 | ineligible | unresolved | C | none | other | none | low | no_number | Unlocking Government Open Data: Harnessing Open-Source LLMs… |
| W7128096469 | ineligible | gpt-4-turbo-2024-04-09 | B | none | agentic | proxy fidelity (AVG)=0.421 (n/a) | high | no_prompt, no_number | AgentXRay: White-Boxing Agentic Systems via Workflow Recons… |
| W7171806693 | ineligible | unresolved | C | none | other | none | low | no_number | Tendencias en la evaluación automática de accesibilidad en… |
| W4416433961 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | generation | none (1) | low | webui, no_number | O DESAFIO ÉTICO DA IA NA FORMAÇÃO HUMANA: DIRETRIZES PARA U… |
| W7166737382 | ineligible | gpt-4.1-nano-2025-04-14 | S | none | other | none | low | no_prompt, no_number | Why Trust Your Agent? Empirical Security Gains from TRiSM-G… |
| W7171748934 | maybe | o3-mini-2025-01-31 | S | partial | classification | Spearman rho (Openness)=0.269 (226) | mid | - | LEX-EC: A Lexical Evidence-Channel Audit Framework for Zero… |
| W7154539854 | maybe | o3-2025-04-16 | S | partial | agentic | mean gap at merge (m)=9.28 (109) | high | - | General-purpose LLMs as Models of Human Driver Behavior: Th… |
| W4395474395 | maybe | gpt-4o-2024-05-13 | B | partial | extraction | RepoQA avg=90.6 (n/a) | low | - | Phi-3 Technical Report: A Highly Capable Language Model Loc… |
| W4403906127 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | none (40) | low | data_closed | Performance of a large language model for identifying centr… |
| W4413737580 | maybe | gpt-4-turbo-2024-04-09 | B | partial | generation | solution-quality score (UAV, 1-trial)=9.6 (10) | mid | - | Large language models for combinatorial optimization of des… |
| W4408065649 | ineligible | unresolved | S | partial | generation | none (10) | low | alias_unpinned, no_number, webui | How does ChatGPT 4omni perform in consenting for common ort… |
| W4411119568 | ineligible | gpt-4-turbo-2024-04-09 | A | none | generation | none (figure only) | low | no_number | Navigating the Path of Writing: Outline-guided Text Generat… |
| W7127623381 | ineligible | gpt-4-turbo-2024-04-09 | B | none | other | none | low | webui, no_number | Generative AI and digital neocolonialism in global educatio… |
| W4412714694 | eligible | gpt-4-turbo-2024-04-09 | B | partial | agentic | success rate (Human Surrogate)=45 (20) | low | - | LA-RCS: LLM-agent-based Robot Control System |
| W4403322117 | ineligible | gpt-4o-2024-05-13 | S | partial | generation | none (200) | low | human_outcome | Human Bias in the Face of AI: Examining Human Judgment Agai… |
| W4399911093 | eligible | gpt-4-turbo-2024-04-09 | S | partial | classification | F-score (Spanish)=90.24 (100) | low | - | Leveraging Large Language Models to Measure Gender Represen… |
| W4415673480 | ineligible | unresolved | C | none | other | none | low | no_number, data_closed | Artificial Intelligence Powered Research Automation (AIPRA)… |
| W4413735524 | eligible | gpt-4-turbo-2024-04-09 | S | full | agentic | success rate (stepPlanning, Total)=43 (60) | low | - | From text to design: a framework to leverage LLM agents for… |
| W4409362592 | maybe | gpt-4-turbo-2024-04-09 | S | partial | agentic | success rate (Vanilla, L1)=72.0 (n/a) | mid | - | Infer Human's Intentions Before Following Natural Language… |
| W4415907988 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | none (figure only) | low | no_number | Cancer-Myth: Evaluating Large Language Models on Patient Qu… |
| W4404352845 | eligible | gpt-4-turbo-2024-04-09 | S | partial | agentic | pass rate (Avg, ReAct)=16.0 (632) | high | - | EcoAct: Economic Agent Determines When to Register What Act… |
| W4405033318 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | other | none (ref. only) (1000) | low | no_number | Evaluating the Consistency of LLM Evaluators |
| W4410873020 | ineligible | unresolved | S | partial | other | Likert score=3.82 (n/a) | low | alias_unpinned, human_outcome, webui | Exploring the medical ethical limitations of GPT-4 in clini… |
| W4412886848 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | none | low | no_number | Model Extrapolation Expedites Alignment |
| W4411120992 | ineligible | gpt-4-turbo-2024-04-09 | A | full | classification | none (unvalidated) | low | no_number | Does Content Moderation Lead Users Away from Fringe Movemen… |
| W4405096592 | ineligible | unresolved | S | partial | generation | valid test cases %=87 (n/a) | low | alias_unpinned, webui | System Test Case Design from Requirements Specifications: I… |
| W4403809255 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | agentic | none (figure only) | low | no_number | CurricuLLM: Automatic Task Curricula Design for Learning Co… |
| W4404650190 | ineligible | gpt-4-turbo-2024-04-09 | A | full | classification | none (unvalidated) (100) | low | no_number | The Value of Information from Sell-side Analysts |
| W7124513032 | maybe | gpt-4o-2024-05-13 | S | partial | generation | norm. total error=0.285 (n/a) | low | - | M^4olGen: Multi-Agent, Multi-Stage Molecular Generation und… |
| W4406192716 | eligible | gpt-4o-2024-05-13 | S | full | classification | alignment score=0.33 (36) | low | - | Vision Language Models as Values Detectors |
| W4415316668 | ineligible | dead-preview | B | none | other | none | low | dead_alias, no_number | PIKA: Expert-Level Synthetic Datasets for Post-Training Ali… |
| W7138965013 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | none (140) | low | human_outcome | From Prompt to Practice: Evaluating Unedited AI-Generated P… |
| W4405935604 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | Jailbreak Success Rate (EN)=38.1 (21) | low | tos | Generative Models Ethical Evaluation Approach: Industry Cas… |
| W7138349985 | ineligible | gpt-4-turbo-2024-04-09 | S | full | generation | none (categorical) (5) | low | webui, no_number | Evalvacija napredka generativne umetne inteligence pri snov… |
| W4403663239 | ineligible | dead-preview | S | partial | other | none | low | dead_alias | Experimenting with Legal AI Solutions: The Case of Question… |
| W4415594898 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | other | none | low | data_closed, webui | The AI-Base NDA Catalog |
| W7164974000 | eligible | gpt-4-turbo-2024-04-09 | S | partial | agentic | task completion=61.3 (690) | high | - | WorkBench Revisited: Workplace Agents Two Years On |
| W7104377898 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | Overton window area=53.5 (n/a) | mid | - | POW: Political Overton Windows of Large Language Models |
| W4405767487 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | AlpacaEval2 LC win rate=55.0 (n/a) | mid | aux_model_dead | Multi-Agent Sampling: Scaling Inference Compute for Data Sy… |
| W4406735499 | ineligible | unresolved | C | none | other | none | low | no_number | Resilience of LTE-A/5G-NR links Against Transient Electroma… |
| W7202319871 | maybe | unresolved | S | partial | generation | chi-sq (domain imbalance)=584.7 (890) | low | alias_unpinned | Automated Generation of Complexity-Validated Decision Scena… |
| W4416034022 | eligible | gpt-4o-2024-05-13 | B | none | generation | AlpacaEval2 LC win rate=57.5 (805) | mid | - | CoTD-PO: Chain-of-Thought Distillation with Preference Opti… |
| W4416054129 | ineligible | unresolved | C | none | other | none | low | no_number | Moving Beyond Next-Token Prediction: Transformers are Conte… |
| W7168987768 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none | low | webui, no_number | Associations between multidimensional fatigue and wearable-… |
| W4403785627 | ineligible | gpt-4-turbo-2024-04-09 | A | none | generation | none (805) | low | no_number | Orthogonal Finetuning for Direct Preference Optimization |
| W7134093983 | eligible | gpt-4.1-nano-2025-04-14 | S | partial | extraction | MAE (multimodal)=0.224 (154) | low | - | Using Vision + Language Models to Predict Item Difficulty |
| W7167017195 | ineligible | gpt-4.1-nano-2025-04-14 | S | none | agentic | none | low | no_prompt, no_number | Bayesian Uncertainty Propagation for Agentic RAG Pipelines:… |

## Observations

- Judge/annotator-only use (role A) is the single largest ineligibility driver in this group: six papers (W4411119568, W4405033318, W4412886848, W4411120992, W4404650190, W4403785627) point gpt-4-turbo at scoring or labeling someone else's output with no validated capability number for the model itself, versus W4399911093, where the annotator's own F-score against 100 hand-labeled sentences made the record eligible. W4405767487 shows the mirror case: a clean, dated subject score (GPT-4 Turbo 04/09 on AlpacaEval) is blocked anyway because the fixed judge/baseline for the whole table is the retired GPT-4-Preview-1106 (aux_model_dead).
- Alias resolution mostly favors the live snapshot: of the ~34 rows carrying a bare `gpt-4-turbo`/`GPT-4 Turbo`, the great majority resolve to gpt-4-turbo-2024-04-09 by the post-2024-07-01 date rule (many flagged "post-GA alias" by the automated screen and confirmed by an arXiv/DOI date in the 2024-2026 range). Two papers instead pin the retired 1106 preview explicitly (W4415316668, W4403663239, both dead_alias).
- Consumer web interfaces (ChatGPT, Copilot, ChatGPT Enterprise) rather than the API account for 9 of the 33 ineligible records (W4415697109, W4416433961, W4408065649, W7127623381, W4405096592, W7138349985, W4415594898, W4410873020, W7168987768), concentrated in education, medicine and qualitative case-study papers; several combine webui with an undated model, adding alias_unpinned as well.
- Mention-only citations, background-table entries and AI-assisted-writing disclosures (role C) rule out 8 more papers (W7172391418, W7171806693, W4415673480, W4406735499, W4416054129, W7168987768, plus the "gpt-4-turbo" half of W4415697109 and W7127623381's related-work citation) where the live id never corresponds to an experiment these authors ran.
- Two records (W7166737382, W7167017195) are abstract-landing-page captures only: the abstract itself names a live model (GPT-4.1-nano in both cases) with a real role, but no body text, tables or prompts were retrieved into papers_tierb, so no reproducible number could be extracted despite an otherwise promising setup.
- Real-world sensitive or controlled data blocks two otherwise clean setups (W4403906127: identifiable protected health information behind a Stanford-hosted secure LLM; W4415594898: export-controlled Los Alamos nuclear-materials technical reports), and two papers hit the `tos` rule despite clean models and metrics (W4396945319's many-shot-jailbreak-style regurgitation attack; W4405935604's TAP jailbreak benchmark with quoted harmful outputs).
- The 8 eligible records are short, cheap classification/agentic tasks with n in the tens to low hundreds (LA-RCS n=20, gender-bias annotation n=100, CAD agent n=60, VLM alignment n=36, item-difficulty n=154), except two larger agentic benchmarks that push into the high cost tier from repeated multi-step tool-use calls (WorkBench Revisited, 690 tasks; EcoAct's ToolBench runs, 632 queries).
