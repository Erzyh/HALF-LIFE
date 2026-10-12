# Tier B triage, group 14 (49 papers)

Counts: eligible 5, maybe 18, ineligible 26.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md`. Order follows `data/tierb_triage/group_14.csv` (rank).

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4416035826 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (fixed AlpacaEval baseline) | low | no_number, aux_model_dead | Massive Supervised Fine-tuning Experiments Reveal How Data,… |
| W4411119690 | maybe | gpt-4-turbo-2024-04-09 | B | full | classification | accuracy%=86.91 (n/a) | mid | - | Privacy Checklist: Privacy Violation Detection Grounding on… |
| W4403364962 | maybe | gpt-4-turbo-2024-04-09 | B | partial | extraction | f1chain avg=67.32 (2146) | high | - | Benchmarking Agentic Workflow Generation |
| W4416036732 | maybe | o3-mini-2025-01-31 | S | full | other | tau-c=0.61 (631) | high | - | Debatable Intelligence: Benchmarking LLM Judges via Debate S… |
| W4414972314 | maybe | gpt-4o-2024-05-13 | S | partial | agentic | ARR%=58.68 (n/a) | mid | - | QuantAgents: Towards Multi-agent Financial System via Simula… |
| W4404988426 | maybe | gpt-4o-2024-05-13 | B | partial | extraction | F1=0.51 (n/a) | low | - | TabulaX: Leveraging Large Language Models for Multi-Class Ta… |
| W4404781797 | maybe | gpt-4o-2024-05-13 | S | full | classification | accuracy=79.0 (n/a) | low | - | Vector Poetics: Parallel Couplet Detection in Classical Chin… |
| W4415037596 | maybe | gpt-4.1-nano-2025-04-14 | S | partial | other | CDGAP=0.427 (640) | low | - | Are Language Models Consequentialist or Deontological Moral… |
| W4404659393 | maybe | gpt-4-turbo-2024-04-09 | S | partial | generation | accuracy=88.6 (79) | low | - | ChatGPT-4 Turbo and Meta’s LLaMA 3.1: A Relative Analysis of… |
| W4413114601 | maybe | gpt-4-turbo-2024-04-09 | B | partial | classification | sensitivity=0.43 (n/a) | low | - | Is Large Language Model-Assisted Citation Screening Feasible… |
| W4404782977 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | IH/IA score=0.70 (194) | mid | - | The Computational Anatomy of Humility: Modeling Intellectual… |
| W7128684877 | ineligible | unresolved | S | partial | mcq | none (ChatGPT value n/a) | low | webui, no_number | Comparative performance analysis of ChatGPT, Scholar GPT, an… |
| W4404313830 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | none (labeler only) | low | no_number | Enhancing Inflation Nowcasting with LLM: Sentiment Analysis… |
| W4400684338 | ineligible | dead-preview | S | partial | classification | hallucination rate=0.51 (12600) | mid | dead_alias | Self-Logical Consistency Assessment of Large Language Models… |
| W7135132372 | ineligible | unresolved | A | none | other | none (generator only) | low | no_number | Automating Quality Assessment of LLM-Generated Defeaters |
| W4417517434 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (survey) | low | no_number | Large Language Models for Computer-Aided Design: A Survey |
| W4406165121 | maybe | unresolved | B | full | generation | PDS entropy=98 (n/a) | mid | alias_unpinned | Toward Inclusive Educational AI: Auditing Frontier LLMs thro… |
| W4403564508 | ineligible | gpt-4o-2024-05-13 | A | partial | other | none (evaluator only) | low | no_number | Benchmark Inflation: Revealing LLM Performance Gaps Using Re… |
| W7138900817 | ineligible | o3-2025-04-16 | A | partial | generation | none (generator only) | low | no_number | CCD-Bench: Probing Cultural Conflict in Large Language Model… |
| W4415973405 | eligible | gpt-5-2025-08-07 | S | partial | classification | sensitivity(API)=87.3 (736) | high | - | Dual-Model LLM Ensemble via Web Chat Interfaces Reaches Near… |
| W4405904606 | maybe | gpt-4o-2024-05-13 | S | partial | generation | Atometric-F1=0.893 (n/a) | mid | - | MapExplorer: New Content Generation from Low-Dimensional Vis… |
| W4402702575 | maybe | gpt-4o-2024-05-13 | S | full | classification | accuracy=70.9 (n/a) | mid | - | From Bias to Balance: Detecting Facial Expression Recognitio… |
| W7159547386 | maybe | gpt-4o-2024-05-13 | B | partial | other | RMSTBE-F1=3.41 (n/a) | low | - | Assessing Y-Axis Influence: Bias in Multimodal Language Mode… |
| W4414852895 | maybe | gpt-4o-2024-05-13 | S | full | other | EWETC=0.871 (n/a) | low | - | The Topics of Depression on Social Networking Sites |
| W4403810015 | maybe | gpt-4-turbo-2024-04-09 | B | full | classification | F1=0.171 (n/a) | mid | - | PropaInsight: Toward Deeper Understanding of Propaganda in T… |
| W4409805074 | ineligible | gpt-4-turbo-2024-04-09 | S | none | extraction | recall%=100 (n/a) | low | data_closed | Leveraging Semantic Web Technologies in Healthcare: Developm… |
| W7166554439 | maybe | gpt-4-turbo-2024-04-09 | B | partial | classification | align. score=0.218 (174) | mid | - | InFACT: Benchmarking LLM Explanations Against Institutional… |
| W4404313648 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | F1=0.61 (100) | low | - | Architectural Flaw Detection in Civil Engineering Using GPT-… |
| W7166821175 | eligible | gpt-4-turbo-2024-04-09 | B | full | classification | R@Gold=60.1 (585) | mid | - | From Regulatory Approvals to Patents: Cross-Domain Linking f… |
| W7130936658 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | classification | none (number n/a) | low | data_closed | Clinical Evaluation of a PACS-Integrated Deep Learning Tool… |
| W4403818357 | ineligible | gpt-4-turbo-2024-04-09 | B | none | agentic | none (system metrics only) | mid | no_prompt | Interactive Speculative Planning: Enhance Agent Efficiency t… |
| W4403585697 | maybe | gpt-4-turbo-2024-04-09 | B | partial | mcq | accuracy=49.62 (n/a) | low | - | Diagram Formalization Enhanced Multi-Modal Geometry Problem… |
| W4416907954 | eligible | gpt-4-turbo-2024-04-09 | B | full | classification | balanced acc=0.542 (712) | low | - | ROLE OF ARTIFICIAL INTELLIGENCE IN PREDICTING OUTCOMES OF CL… |
| W4415270561 | eligible | gpt-4.1-nano-2025-04-14 | S | full | extraction | EM=0.38 (1000) | low | - | Diff-XYZ: A Benchmark for Evaluating Diff Understanding |
| W7164209790 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | classification | avg safety acc=43.4 (n/a) | high | aux_model_dead | Evaluating and Enhancing an AI Mental Health Guide in High-R… |
| W4411120012 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (fixed baseline) | low | no_number | Cross-lingual Transfer of Reward Models in Multilingual Alig… |
| W7171295101 | ineligible | unresolved | S | full | generation | accuracy (n/a, webui) | low | webui | Evaluating the impact of prompting styles on LLM accuracy fo… |
| W4416238481 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | other | none (qualitative) | low | webui, no_number | On the Military Applications of Large Language Models |
| W4414809055 | ineligible | o4-mini-2025-04-16 | B | partial | classification | verdict correct=22.9 (1329) | high | aux_model_dead | ALARB: An Arabic Legal Argument Reasoning Benchmark |
| W4405254208 | ineligible | o4-mini-2025-04-16 | S | partial | agentic | none (figure only) | high | no_number | Can foundation models actively gather information in interac… |
| W7163712085 | ineligible | unresolved | S | none | mcq | accuracy=85.8 (127) | low | data_closed | Comparative analysis of the performance of large language mo… |
| W7165626184 | ineligible | unresolved | C | none | other | none (survey) | low | no_number | Retrieval-Augmented Generation in Healthcare Systems: A Syst… |
| W4404395395 | ineligible | gpt-4-turbo-2024-04-09 | A | full | other | none (labeler only) | low | no_number | Evaluating Fine-Tuning Efficiency of Human-Inspired Learning… |
| W4405173954 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | none (figure only) | low | no_number | Verb Mirage: Unveiling and Assessing Verb Concept Hallucinat… |
| W7169689017 | ineligible | o4-mini-2025-04-16 | S | none | classification | refusal rate=72.4 (542) | high | tos | BioTIER: A Refusal Benchmark for Targeted Biological Risk Mi… |
| W4417172171 | ineligible | dead-preview | A | full | generation | none (dead judge) | low | dead_alias | JaccDiv: A Metric and Benchmark for Quantifying Diversity of… |
| W4412679812 | ineligible | gpt-4-turbo-2024-04-09 | B | none | generation | accuracy=89.1 (n/a) | low | no_prompt | Legal Document Summarization: Enhancing Judicial Efficiency… |
| W4402954235 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none (fixed baseline) | low | no_number | Self-Judge: Selective Instruction Following with Alignment S… |
| W4404261082 | ineligible | gpt-4-turbo-2024-04-09 | A | none | generation | none (rewriter only) | low | no_number | MotionGlot: A Multi-Embodied Motion Generation Model |

## Observations

- Alias resolution: 35 of the 49 rows mention `gpt-4-turbo` in `live_ids` (30 as a bare alias only, 5 already dated by the extraction pipeline). Only six papers pin `gpt-4-turbo-2024-04-09` verbatim in the text (the same 5 plus the CI-characteristics run in W4411119690, where the text gives the abbreviated "GPT-4-turbo-04-09"); the remaining bare mentions were resolved by the post-2024-07-01 alias rule alone. Two dead-preview catches came from reading past the CSV's alias_note hint: W4400684338 states its checkpoint was accessed on "March 05, 2024," which predates the 2024-04-09 GA despite the paper itself dating to mid-2024, and W4417172171 pins its G-Eval judge to the November-2023 preview gpt-4-turbo-1106.
- Role C (mention/citation only, never run by these authors) accounts for 5 of the 49 rows: three use GPT-4-Turbo purely as an AlpacaEval-style fixed win-rate reference that these authors never re-invoke (W4416035826, W4411120012, W4402954235), and two are pure literature surveys (W4417517434, W7165626184, detailed below).
- Role A (auxiliary tool, not the scored subject) is larger still at 7 of 49: GPT-4/GPT-4-Turbo is used only to label training data (W4404313830, W4404395395), generate a benchmark's own content (W7135132372's defeaters, W7138900817's CCD-Bench dilemmas, W4404261082's rewritten motion prompts), evaluate someone else's sub-study (W4403564508's human-indistinguishability survey), or serve as a dead-preview G-Eval judge (W4417172171). In each case the paper's headline metric belongs to a different system.
- Judge dependency downgraded two otherwise-clean maybe candidates to ineligible: W7164209790's mental-health safety accuracy and W4414809055's ALARB verdict-alignment score both require an undated/off-list judge (GPT-4.1, GPT-4o) to reproduce the exact reported number, even though the tested model itself (GPT-4-turbo, o4-mini) is live-listed.
- Data closure blocks three otherwise well-documented clinical/institutional studies: W7130936658 (institutional radiology reports), W4409805074 (real clinical prescriptions), and W7163712085 (a national Turkish dental licensing exam).
- Web-interface access blocks three papers outright (W7171295101 via chat.openai.com, W4416238481 via Microsoft Copilot's chat UI, W7128684877 via ChatGPT/Scholar GPT's web platforms), each otherwise using reasonably clean, public evaluation data (AIME 2024/2025 for W7171295101).
- One paper, W7169689017 (BioTIER), is flagged tos: it is a legitimate SecureBio biosecurity-safety benchmark, but its Catastrophe-Avoidance prompt tier is deliberately built from genuinely high-risk biological-uplift content, so re-executing it would mean sending those prompts to commercial APIs, which this project does not do regardless of the paper's own research legitimacy.
- Two papers are pure literature surveys with no original experiments at all (W4417517434, W7165626184); every GPT-4-family mention in them describes a different, cited paper's system.
- The 5 eligible records span clinical-trial outcome prediction from ClinicalTrials.gov (W4416907954), Reddit intellectual-humility classification (W4404782977), patent-to-regulatory-approval linking (W7166821175), a diff-understanding benchmark released on HuggingFace (W4415270561), and a systematic-review-screening study that deliberately runs a matched API condition alongside its web-chat condition (W4415973405); in each case the live model is dated in the text, the evaluation prompt is fully specified, the claim has a clear n_items, and the underlying data is public.
- Cost skews low/mid overall (most n_items are in the hundreds), but o-series/gpt-5 reasoning models push several maybe/eligible claims to the high tier purely on per-call price: W4415973405 (gpt-5, reasoning effort medium, 736 items), W4416036732 (o3-mini judge, 631 items), W4414809055 (o4-mini, 1,329 cases), and W7169689017 (o4-mini refusal benchmark, 542 prompts, ineligible on tos regardless of cost).
