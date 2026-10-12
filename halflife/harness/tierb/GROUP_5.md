# Tier B triage, group 5 (50 papers)

Counts: eligible 3, maybe 15, ineligible 32.

Records: one JSON per paper in this directory (harness/tierb/<wid>.json), schema in SCHEMA.md.

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost tier | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4403885225 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | robustness rate (verbosity bias)=0.915 (500) | high | - | Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge |
| W4412887844 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | accuracy (explanation evaluation, direct prompting)=52.32 (3339) | high | - | Chumor 2.0: Towards Better Benchmarking Chinese Humor Unders |
| W4412944528 | eligible | gpt-4o-2024-05-13 | S | full | mcq | average expected calibration error (Vanilla confidence elicitation, AvE)=33.2 (1650) | low | - | Do Language Models Mirror Human Confidence? Exploring Psycho |
| W4405355440 | maybe | gpt-4o-2024-05-13 | S | full | mcq | MCQ accuracy=80.23 (3268) | high | - | Neptune: The Long Orbit to Benchmarking Long Video Understan |
| W4416437629 | maybe | gpt-5-mini-2025-08-07 | S | full | other | final-answer accuracy=63.7 (1350) | mid | - | EngTrace: A Symbolic Benchmark for Verifiable Process Superv |
| W7166826703 | maybe | gpt-5-2025-08-07 | S | partial | generation | policy alignment score (Denied Base, average of 8 domains)=13.01 (516) | mid | - | COMPASS: A Framework for Evaluating Organization-Specific Po |
| W7141772025 | maybe | gpt-4.1-nano | B | partial | generation | HealthBench score (official rubrics)=33.9 (5000) | high | - | Qworld: Question-Specific Evaluation Criteria for LLMs |
| W4402426686 | maybe | gpt-4-turbo-2024-04-09 | B | full | classification | critique-level Meta-F1 (English meta-evaluation set)=67.3 (299) | low | - | SAFETY-J: Evaluating Safety with Critique |
| W7140134105 | maybe | o4-mini-2025-04-16 | S | partial | mcq | exact match=82.3 (131) | low | - | RoD-TAL: A Benchmark for Answering Questions in Romanian Dri |
| W4412889923 | maybe | gpt-4o-2024-05-13 | S | full | agentic | task success rate=45.33 (250) | high | - | ASPERA: A Simulated Environment to Evaluate Planning for Com |
| W4411120604 | maybe | gpt-4-turbo-2024-04-09 | S | full | mcq | TRAIT personality score, Conscientiousness, Type 1 template=93.9 (1000) | mid | - | Do LLMs Have Distinct and Consistent Personality? TRAIT: Per |
| W4411549654 | maybe | gpt-4-turbo-2024-04-09 | S | full | mcq | accuracy=82.1 (1426) | mid | - | Comparative Analysis of Multimodal Large Language Models GPT |
| W4403370432 | maybe | gpt-4-turbo-2024-04-09 | S | partial | extraction | F1 (entity recognition, average over entity types, 3-shot)=48 (n/a) | low | - | An Evaluation of Requirements Modeling for Cyber-Physical Sy |
| W4406604156 | maybe | gpt-4-turbo-2024-04-09 | S | partial | agentic | overall success rate=49.5 (1000) | high | - | ComplexFuncBench: Exploring Multi-Step and Constrained Funct |
| W4411120335 | maybe | gpt-4-turbo-2024-04-09 | S | partial | generation | semantic Leak-Rate (BERTScore)=70.8 (4360) | mid | - | Does Liking Yellow Imply Driving a School Bus? Semantic Leak |
| W4403758464 | maybe | gpt-4-turbo-2024-04-09 | S | full | other | plan validity accuracy (Blocksworld, zero-shot)=40.1 (600) | mid | - | LLMs Still Can't Plan; Can LRMs? A Preliminary Evaluation of |
| W7134290865 | maybe | gpt-4-turbo-2024-04-09 | S | partial | mcq | accuracy (zero-shot)=77 (169) | low | - | Agentic retrieval-augmented reasoning reshapes collective re |
| W4402952718 | maybe | gpt-4-turbo-2024-04-09 | S | full | other | weighted accuracy (WA)=69.7 (900) | mid | - | Evaluating Large Language Models on Spatial Tasks: A Multi-T |
| W4396914156 | ineligible | gpt-4o-2024-05-13 | S | partial | agentic | diagnostic accuracy=34.2 (215) | high | aux_model_dead | AgentClinic: a multimodal agent benchmark to evaluate AI in  |
| W7204463329 | ineligible | gpt-4.1-nano | B | partial | agentic | behavioral lift (judge score, behavior minus baseline)=2.86 (32) | high | aux_model_dead | Training Alignment Auditors via Reinforcement Learning |
| W4407308868 | ineligible | dead-preview | A | none | generation | none | low | dead_alias | Beyond Sample-Level Feedback: Using Reference-Level Feedback |
| W4415162359 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | generation | none | low | human_outcome, no_number | Distinct Profiles of Run-to-Run Score Reliability and Expert |
| W4405470316 | ineligible | unresolved | B | partial | agentic | exception-handling accuracy (ACC %)=77 (n/a) | mid | no_number | Seeker: Towards Exception Safety Code Generation with Interm |
| W4404782882 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none | low | no_number | A Systematic Survey and Critical Review on Evaluating Large  |
| W4416034648 | ineligible | gpt-4.1-nano | B | partial | generation | none | low | data_closed, no_number | Bringing Pedagogy into Focus: Evaluating Virtual Teaching As |
| W4416378724 | ineligible | gpt-5-2025-08-07 | B | none | mcq | VSI-Bench score (MRA/Acc)=55.0 (n/a) | high | - | Scaling Spatial Intelligence with Multimodal Foundation Mode |
| W4403578738 | ineligible | gpt-4-turbo-2024-04-09 | S | full | extraction | exact match accuracy (Q1, prompt P1)=0.55 (200) | low | data_closed | Answering Questions in Stages: Prompt Chaining for Contract  |
| W7163777928 | ineligible | gpt-4-turbo-2024-04-09 | C | partial | other | none | low | no_number | Three Years of r/ChatGPT: Societal Impact Evaluations from S |
| W4403362785 | ineligible | gpt-4-turbo-2024-04-09 | B | full | agentic | none | mid | no_number | From News to Forecast: Integrating Event Analysis in LLM-Bas |
| W4404313204 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | generation | none | high | data_closed, no_number | First-Person Fairness in Chatbots |
| W7115097999 | ineligible | gpt-4-turbo-2024-04-09 | B | none | classification | none | low | no_number | The Llama 3 herd of models |
| W4412945277 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | classification | decision accuracy (MetaTool, w/o ctx)=61.3 (n/a) | low | no_number | Adaptive Tool Use in Large Language Models with Meta-Cogniti |
| W4405025319 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | generation | none | mid | tos, no_number | ChemSafetyBench: Benchmarking LLM Safety on Chemistry Domain |
| W4414812774 | ineligible | dead-preview | A | none | generation | none | low | dead_alias | Adaptive Batch-Wise Sample Scheduling for Direct Preference  |
| W4400703072 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | agentic | none | mid | no_number | AtomAgents: Alloy design and discovery through physics-aware |
| W4402030489 | ineligible | gpt-4o-2024-05-13 | S | partial | classification | average F1 against expert labels=0.66 (147) | low | data_closed | Generative Multimodal Models for Social Science: An Applicat |
| W7204709953 | ineligible | gpt-5-2025-08-07 | S | none | other | recall of the highest-ARI method within the top-5 ranked methods=1.0 (6) | mid | - | Visual LLM-guided consensus spatial domain detection with L- |
| W4402670069 | ineligible | gpt-4o-2024-05-13 | B | partial | generation | none | low | human_outcome | Learning to Generate Instruction Tuning Datasets for Zero-Sh |
| W4402705653 | ineligible | gpt-4-turbo-2024-04-09 | C | none | agentic | none | low | no_number | TourSynbio: A Multi-Modal Large Model and Agent Framework to |
| W4402698368 | ineligible | unresolved | B | partial | mcq | MCQ accuracy (MainframeBench)=73.9 (n/a) | low | dead_alias | XMainframe: A Large Language Model for Mainframe Modernizati |
| W4416036943 | ineligible | gpt-4-turbo-2024-04-09 | B | full | classification | none | mid | data_closed, no_number | Two Heads Are Better Than One: Dual-Model Verbal Reflection  |
| W7163597399 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none | low | no_number | Reasoning4Sciences: Bridging Reasoning Language Models to Al |
| W4405355275 | ineligible | o3-mini-2025-01-31 | A | partial | agentic | none | mid | no_number | From intention to implementation: automating biomedical rese |
| W4408426017 | ineligible | gpt-4o-2024-05-13 | S | none | extraction | L1 weighted score (distance, lower is better)=0.1431 (156) | low | - | Wikimpacts 1.0: a new global climate impact database based o |
| W4416036974 | ineligible | gpt-4-turbo-2024-04-09 | A | full | generation | none | low | no_number | Glider: Global and Local Instruction-Driven Expert Router |
| W7164974068 | ineligible | gpt-5-2025-08-07 | C | none | other | none | low | no_number | Every Eval Ever: A Unifying Schema and Community Repository  |
| W7166525782 | ineligible | gpt-5-mini-2025-08-07 | B | none | generation | none | low | no_number | A Multilingual Linguistic Analysis of Human vs LLM-Generated |
| W4411120052 | ineligible | gpt-4-turbo-2024-04-09 | C | none | other | none | low | no_number | Causal Inference with Large Language Model: A Survey |
| W7128813364 | ineligible | o3-mini-2025-01-31 | S | partial | extraction | none | low | data_closed | Improving reliability and accuracy of structured data extrac |
| W4401202384 | ineligible | gpt-4-turbo-2024-04-09 | B | none | agentic | none | low | no_number | A Study on the Implementation Method of an Agent-Based Advan |

## Observations
- Alias resolution: 31 of the 50 papers carry a bare 'gpt-4-turbo' hit. Only 9 confirm gpt-4-turbo-2024-04-09 in the text (CALM and CPSBench write 'gpt-4-turbo-0409'; SAFETY-J, TRAIT, ComplexFuncBench, DARS, Semantic Leakage, the spatial benchmark and the radiology study give the full snapshot). 18 are resolved to that snapshot only by the post-2024-07 rule (Contract QA, Medscape, Chumor, PlanBench, MeCo and others), 2 are dead previews used as judges (REFED: 'GPT-4-Turbo (1106)'; SamS: AlpacaEval 2 annotator), and 2 stay unresolved (Seeker cites '(GPT-4, 2023)'; XMainframe's baseline is labelled only 'GPT 4').
- Judge and auxiliary models decide several verdicts: AgentClinic needs gpt-4-0613 patient/measurement agents, the alignment-auditor paper scores with Claude Sonnet 4/Opus 4.6, BioResearcher and REFED use the live model only as a judge (role A: 4 papers), and COMPASS, Qworld and ComplexFuncBench depend on a still-callable GPT judge (gpt-5-mini-2025-08-07, gpt-4.1, gpt-4o-2024-08-06) that is outside the tracked model list.
- Prompts: 15 papers print the full prompt, 22 print a template with a missing piece (label lists, retrieved shots, translations, random in-context samples), 13 print none. Four papers keep the exact prompt in a supplement or online resource that is absent from the extracted text (Wikimpacts, L-STAR, the radiology study, the Japanese counselling study). Three ineligible records (SenseNova-SI, L-STAR, Wikimpacts) have an empty blockers list because 'prompt not printed' is not one of the seven listed blockers; the reason is in notes.
- Blocker tally: no_number 20 (surveys, mentions, generators, pipeline-only numbers), data_closed 6 (Contract QA clauses to be released later; satellite/streetscape imagery with no site list; VTA forum data under FERPA; MS clinical records; First-Person Fairness private ChatGPT prompts; DARS proprietary answers), dead_alias 3, aux_model_dead 2, human_outcome 2, tos 1 (ChemSafetyBench jailbreak redrafts).
- Role C is common in the top-ranked list: 6 surveys/position/repository papers (EMNLP evaluation survey, Reasoning4Sciences, causal-inference survey, Every Eval Ever, r/ChatGPT, TourSynbio) carry live IDs only as citations, leaderboard rows or release-timeline entries. Role S 23, B 17, A 4.
- Cost at three seeds: low 26, mid 14, high 10. The three eligible papers are AFCE (low, ~500 calls of ten questions each), CALM (high: three judgments per item over 500 items) and Chumor (high: 3,339 Chinese items). Multimodal and agentic maybes (Neptune, ASPERA, ComplexFuncBench, Qworld) are high tier even where everything is printed.
