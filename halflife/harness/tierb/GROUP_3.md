# Tier B triage, group 3 (50 papers)

Source frame: `halflife/data/tierb_triage/group_3.csv`. One record per paper in `harness/tierb/<wid>.json`, keys as in `SCHEMA.md`. Text files read from `halflife/external/papers_tierb/`; all 50 were readable (one needed `grep -a` because of a stray binary byte: W4416233038).

Counts: eligible 7, maybe 16, ineligible 27.

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W7155245470 | eligible | gpt-5-mini-2025-08-07 | S | full | classification | F1 for the Incomplete class vs clinic...=0.76 (1281) | mid | - | Same Verdict, Different Reasons: LLM-as-a-Judge and Clini... |
| W7140084705 | eligible | gpt-4.1-nano-2025-04-14 | S | full | classification | item-dimension mapping F1 (mean over ...=0.92 (141) | low | - | Quantifying Data Contamination in Psychometric Evaluation... |
| W4404782941 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | Main Response Accuracy (MACC) on SCiP...=0.646 (510) | low | - | Can LLMs replace Neil deGrasse Tyson? Evaluating the Reli... |
| W4411119490 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | F1 for detecting erroneous questions ...=22.7 (3000) | high | - | Are We Done with MMLU? |
| W4411119333 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | ADR detection accuracy (%), zero-shot=72.03 (239) | low | - | Lived Experience Not Found: LLMs Struggle to Align with E... |
| W4410280647 | eligible | o3-mini-2025-01-31 | S | full | other | accuracy (%) on the text-only subset ...=13.4 (2500) | high | - | Humanity's Last Exam |
| W4404782525 | eligible | gpt-4o-2024-05-13 | S | full | classification | zero-shot task accuracy with gold con...=61.2 (500) | low | - | Characterizing LLM Abstention Behavior in Science QA with... |
| W4403345251 | maybe | gpt-4-turbo-2024-04-09 | S | full | other | accuracy (%), text-only one-step with...=2.3 (300) | low | - | ING-VP: MLLMs cannot Play Easy Vision-based Games Yet |
| W4404781124 | maybe | gpt-4o-2024-05-13 | B | full | classification | pairwise label accuracy vs human gold...=0.8 (100) | low | - | ValueScope: Unveiling Implicit Norms and Values via Retur... |
| W7150802891 | maybe | gpt-4o-2024-05-13 | S | full | generation | CIDEr-D (image captioning, 5-shot)=169.9 (3004) | high | - | Are large pre-trained vision language models effective co... |
| W4416034538 | maybe | o3-mini-2025-01-31 | S | full | generation | reasoning accuracy (Acc), mean of 3 runs=0.8207 (?) | high | - | FinEval-KR: A Financial Domain Evaluation Framework for L... |
| W4411119839 | maybe | gpt-4-turbo-2024-04-09 | S | full | mcq | AfriMMLU option-prediction accuracy, ...=59.5 (7500) | high | dead_alias | IrokoBench: A New Benchmark for African Languages in the ... |
| W4403663202 | maybe | gpt-4-turbo-2024-04-09 | S | full | other | task-level accuracy (%), model-only d...=25.97 (466) | high | - | DSBench: How Far Are Data Science Agents from Becoming Da... |
| W4400023054 | maybe | gpt-4-turbo-2024-04-09 | S | full | generation | calibrated Pass@1, greedy, BigCodeBen...=0.582 (1140) | high | - | BigCodeBench: Benchmarking Code Generation with Diverse F... |
| W4410274161 | maybe | gpt-4o-2024-05-13 | B | full | extraction | partial-match accuracy (%) of FDA-app...=n/a (234) | low | - | Implementing a context-augmented large language model to ... |
| W4403786592 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | balanced accuracy (%) / MAE on depres...=39.6 (1000) | mid | - | A Comprehensive Evaluation of Large Language Models on Me... |
| W4416033907 | maybe | gpt-4.1-nano-2025-04-14 | S | full | mcq | persuasion percentage F under Full Re...=74.6 (594) | low | - | Challenging the Evaluator: LLM Sycophancy Under User Rebu... |
| W7170989516 | maybe | unresolved | B | partial | extraction | R@P=0.9 (recall at 90% precision), me...=0.56 (?) | high | - | Auto-Fill: Learning to Predict Missing Values Accurately ... |
| W4404783604 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | overall accuracy on first-iteration L...=0.98 (5200) | high | - | LogicAsker: Evaluating and Improving the Logical Reasonin... |
| W4404783148 | maybe | gpt-4-turbo-2024-04-09 | S | partial | mcq | Level-1 action selection accuracy (%)=88.39 (1240) | mid | - | VIVA: A Benchmark for Vision-Grounded Decision-Making wit... |
| W7167625526 | maybe | gpt-4.1-nano-2025-04-14 | S | partial | extraction | extraction accuracy of compound menti...=0.971 (350) | low | - | Mapping the otoactive landscape: an LLM-aided extraction ... |
| W7203709730 | maybe | gpt-5-mini-2025-08-07 | S | none | classification | recall / F2 for study inclusion, indi...=0.369 (1527) | low | - | Class Imbalance and Batch Effects in LLM-Based Screening ... |
| W4403882351 | maybe | gpt-4o-2024-05-13 | B | full | generation | 1@3 solve rate (%) on CodeContests te...=25.3 (165) | high | - | RLEF: Grounding Code LLMs in Execution Feedback with Rein... |
| W4416074906 | ineligible | o4-mini-2025-04-16 | S | partial | agentic | raw CMS score (Moral Flexibility task...=0.67 (?) | mid | data_closed | AgentMisalignment: Measuring the Propensity for Misaligne... |
| W4415017642 | ineligible | gpt-5-mini-2025-08-07 | B | full | classification | Kendall tau between judge scores and ...=0.95 (100) | low | data_closed | RAGXplain: From Explainable Evaluation to Actionable Guid... |
| W7171902645 | ineligible | unresolved | C | full | generation | none=n/a (?) | low | no_number | CARE-MH: Towards Unified, Reproducible, and Comparable Ev... |
| W4407719176 | ineligible | unresolved | B | full | generation | human detection accuracy on GPT-4o-ge...=n/a (?) | low | human_outcome | Is Human-Like Text Liked by Humans? Multilingual Human De... |
| W4416233038 | ineligible | gpt-4o-2024-05-13 | B | full | generation | AUROC of the HLPD detector on GPT-4o ...=n/a (?) | low | no_number | HLPD: Aligning LLMs to Human Language Preference for Mach... |
| W7134291344 | ineligible | o4-mini-2025-04-16 | S | partial | other | CoT controllability score (%), Suppre...=1.1 (14076) | high | data_closed | Reasoning Models Struggle to Control their Chains of Thought |
| W4416036401 | ineligible | unresolved | C | partial | extraction | none=n/a (?) | low | no_number | SciEvent: Benchmarking Multi-domain Scientific Event Extr... |
| W7161915612 | ineligible | gpt-4.1-nano-2025-04-14 | S | none | generation | within-model configuration agreement ...=0.618 (3150) | high | tos | Why Do Safety Guardrails Degrade Across Languages? |
| W4404341509 | ineligible | dead-preview | S | full | generation | failure rate (%) averaged over test t...=8.78 (?) | low | dead_alias, tos | SG-Bench: Evaluating LLM Safety Generalization Across Div... |
| W4399837631 | ineligible | gpt-4-turbo-2024-04-09 | S | full | classification | Scott's pi alignment with human judge...=n/a (3600) | high | data_closed | Judging the Judges: Evaluating Alignment and Vulnerabilit... |
| W7162700493 | ineligible | gpt-5-mini-2025-08-07 | B | partial | generation | none tied to gpt-5-mini; Table 4 span...=n/a (1050) | low | no_number | JuICE: A Benchmark for Evaluating LLM-Judge in Identifyin... |
| W4404652849 | ineligible | gpt-4o-2024-05-13 | S | none | classification | SciFact correctness (accuracy), no re...=77.8 (?) | low | - | OpenScholar: Synthesizing Scientific Literature with Retr... |
| W7196942148 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | extraction | count of LLM-resolved LOINC matches (...=67 (262) | low | no_number | LabAlignAgent: A LOINC-Enriched Ontology-Guided Agent for... |
| W4417228525 | ineligible | gpt-4-turbo-2024-04-09 | S | none | generation | ROUGE-L between generated and ground-...=0.4118 (?) | low | human_outcome | LLMs4SchemaDiscovery: A Human-in-the-Loop Workflow for Sc... |
| W4415947839 | ineligible | unresolved | S | partial | agentic | total return (%) in the volatile regi...=-1.3 (?) | high | data_closed | ATLAS: Adaptive Trading with LLM AgentS Through Dynamic P... |
| W4405426167 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | correctness on benchmark items (figur...=n/a (?) | low | no_number | Migrating Existing Container Workload to Kubernetes -- LL... |
| W4413452230 | ineligible | dead-preview | S | none | generation | model rank on exam metrics (ROUGE, em...=n/a (?) | low | dead_alias, data_closed | Impact of retrieval augmented generation and large langua... |
| W4405033740 | ineligible | gpt-4-turbo-2024-04-09 | A | full | classification | disagreement rate between GPT-4 Turbo...=n/a (?) | low | no_number | Linear Probe Penalties Reduce LLM Sycophancy |
| W7161067791 | ineligible | gpt-4-turbo-2024-04-09 | A | none | generation | mean EGS scores of student models (Qw...=n/a (?) | low | no_number | EIPO: A Framework for Emotionally Intelligent Conversatio... |
| W4417002225 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | mean emotion scores per report group ...=n/a (11056) | high | no_number | What emotions reveal about patient safety: GPT-4-based se... |
| W7131319364 | ineligible | gpt-5-2025-08-07 | S | partial | generation | participant feedback on the conversat...=n/a (?) | low | human_outcome | Conversational AI for Automated Patient Questionnaire Com... |
| W4415625458 | ineligible | unresolved | S | full | classification | label identification accuracy (%), to...=25.0 (260) | low | webui, data_closed | Benchmarking large-language-model vision capabilities in ... |
| W4412888515 | ineligible | dead-preview | S | partial | mcq | test-set accuracy by profession=n/a (?) | low | dead_alias | EMPEC: A Comprehensive Benchmark for Evaluating Large Lan... |
| W7166856799 | ineligible | dead-preview | A | partial | generation | none tied to a run of the live model ...=n/a (?) | low | dead_alias, aux_model_dead | MetaScale: Test-Time Scaling with Evolving Meta-Thoughts |
| W7163595596 | ineligible | unresolved | C | full | generation | none=n/a (?) | low | no_number | Building Reliable Long-Form Generation via Hallucination ... |
| W4404783588 | ineligible | gpt-4-turbo-2024-04-09 | S | full | extraction | F1 on the Company concept task (short...=0.79 (?) | high | data_closed | Systematic Evaluation of Long-Context LLMs on Financial C... |
| W4412889970 | ineligible | unresolved | S | full | classification | error rate (%) when recommending gest...=82.8 (?) | mid | data_closed | Mind the Gesture: Evaluating AI Sensitivity to Culturally... |

Notes on the table: `n` is the item count behind the chosen claim (`?` when the paper does not state it); `cost` is the tier at three seeds per SCHEMA.md; W4404652849 has no listed blocker because its failing criterion (baseline prompt not printed) has no entry in the blocker vocabulary.

## Observations

- Alias hits from the screening step are unreliable for `gpt-4-turbo`. In seven papers the string comes from something other than a model run: an OpenAI docs URL (W4412889970), a citation of prior work (W7155245470, W7163595596), an example extraction triple (W4416036401), a comparative sentence about GPT-4o pricing (W4415625458), a leaderboard row (W7166856799), or a false match on GPT-3.5-turbo/Qwen-turbo (W4407719176). The post-GA date rule also failed four times: EMPEC states the 0125 version outright, SG-Bench used `gpt-4-turbo-preview`, the RAG-exam study ran in March 2024 through the Assistants API, and IrokoBench names 4-Turbo-0125 in the text but gpt-4-turbo-2024-04-09 in its appendix tables.
- Role matters more than presence. Ten papers use the live model only as judge, teacher, labeler or test-data generator (RAGXplain, HLPD, human-like text, JuICE, Linear Probe, EIPO, MetaScale, LabAlignAgent, ValueScope, RLEF); only where the judge itself is the object of study (W7155245470, W4399837631) or the labeler accuracy is tabulated (ValueScope) does a number attach to the model.
- Data closure is the dominant hard blocker among papers that otherwise qualify: unreleased human reference labels (Judging the Judges, RAGXplain), proprietary corpora (financial news haystacks, a textbook, atlas plates, hospital CIRS reports), raw reasoning traces obtained through a lab collaboration (CoT-Control), and sandboxed agent environments (AgentMisalignment, ATLAS).
- Several "maybe" verdicts have printed prompts and public inputs but need an execution or simulation harness to turn model output into the reported number: game simulators (ING-VP), unit-test sandboxes (BigCodeBench, RLEF), workbook serialization plus an LLM judge (DSBench). These are reproducible from public code but not from the prompt alone.
- Headline numbers are often not tabulated: figures only (Kubernetes migration, Judging the Judges, precision oncology, LogicAsker), prose ranges (54-69% across five models), or item counts given only as a pie chart (FinEval-KR). Where the per-model value is in a figure the record carries `value: null` and points to the figure.
- Cost tiers are driven by test-set size rather than model price: MMLU-Redux (3,000), HLE (2,500 with o3-mini high effort), IrokoBench (7,500), LogicAsker (5,200) land in the high tier at three seeds even though four of them use temperature 0, where a single seed would cost a third. The cheapest eligible runs are Psych-ADR (239 posts), the psychometric inventories (141 items), PubMedQA (500) and SCiPS-QA (510).
