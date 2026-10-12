# Tier B triage, group 7 (50 papers)

Counts: eligible 3, maybe 10, ineligible 37.

Records: one JSON per paper in this directory (harness/tierb/<wid>.json). Blocker vocabulary as in SCHEMA.md plus no_prompt.

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost tier | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W7171738920 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | Kendall W vs human majority vote (stance, ...=0.81 (n=160) | low | no_prompt | GPT outperforms BERT and LIWC for stance and anger detect... |
| W7106340049 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | MCC / balanced accuracy (SLR screening)=- (n=-) | mid | no_number | Automatic screening of articles for systematic reviews us... |
| W7119058023 | ineligible | unresolved | B | partial | other | none (qualitative)=- (n=3) | low | webui, no_number | Artificial Intelligence and Consciousness: Limits and Mod... |
| W4416034199 | ineligible | o1-2024-12-17 | S | full | generation | BLEU (Gold Set, zero-shot profiling)=5.82 (n=4189) | high | data_closed | Guess What I am Thinking: A Benchmark for Inner Thought R... |
| W7144391352 | maybe | gpt-5-2025-08-07 | S | partial | mcq | accuracy (Type-ISR, average over Sufficien...=0.754 (n=279) | mid | - | CALRK-Bench: Evaluating Context-Aware Legal Reasoning in ... |
| W4400141942 | ineligible | gpt-4-turbo-2024-04-09 | A | full | generation | none tied to the live model (reported numb...=- (n=-) | high | no_number | HuatuoGPT-Vision, Towards Injecting Medical Visual Knowle... |
| W4402942065 | ineligible | unresolved | C | none | other | none=- (n=-) | low | no_number | Artificial Reason and Artificial Intelligence: the Legal ... |
| W4403823684 | ineligible | unresolved | S | partial | classification | Cohen's kappa vs gold relevance labels (CH...=0.729 (n=-) | mid | dead_alias | Can we trust LLMs as relevance judges? |
| W4416035248 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | accuracy (zero-shot w/o CoT, contamination...=72.2 (n=20435) | high | - | CANDY: Benchmarking LLMs' Limitations and Assistive Poten... |
| W4403900083 | maybe | gpt-4o-2024-05-13 | S | full | classification | unweighted accuracy (training set, CW=0, A...=0.449 (n=2577) | mid | - | Context and System Fusion in Post-ASR Emotion Recognition... |
| W4415062531 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | accuracy vs manual relevance labels=0.903 (n=897) | mid | data_closed | Using large language models to produce literature reviews... |
| W4405783870 | ineligible | gpt-4-turbo-2024-04-09 | S | none | agentic | vulnerability detection on real-world case...=- (n=13) | mid | no_prompt, data_closed | Combining GPT and Code-Based Similarity Checking for Effe... |
| W7125877182 | ineligible | unresolved | C | full | generation | human rating overall (1-5)=4.7 (n=500) | low | no_number, human_outcome | Assessing the Quality of Mental Health Support in LLM Res... |
| W7155654736 | ineligible | unresolved | C | partial | mcq | accuracy (disambiguated context)=95.48 (n=8952) | high | no_number | Intersectional Fairness in Large Language Models |
| W7166885218 | ineligible | gpt-4.1-nano | A | full | agentic | Task Success Rate (PGGA-2B with expert plans)=54.39 (n=57) | low | no_number | PGGA: A Plan-Grounded GUI Agent for Automated Device Support |
| W7204134240 | ineligible | o3-mini-2025-01-31 | A | full | other | accuracy of humor-rating classifier (JokeJ...=57.1 (n=-) | low | no_number | Jokes Aside: Measuring the Semantic Distance of Double Me... |
| W7154427322 | ineligible | gpt-5-mini-2025-08-07 | A | full | classification | detection rate (IR condition)=10.44 (n=-) | mid | no_number | Many Ways to Be Fake: Benchmarking Fake News Detection Un... |
| W4404970691 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | accuracy (zero-shot, OCR text input, RVL-C...=61.8 (n=800) | mid | - | Zero-Shot Prompting and Few-Shot Fine-Tuning: Revisiting ... |
| W4411119226 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | mean cosine similarity between specified a...=0.53 (n=120) | low | - | AI with Emotions: Exploring Emotional Expressions in Larg... |
| W4404187894 | ineligible | unresolved | C | partial | generation | precision of generated competency questions=- (n=-) | low | no_number, dead_alias | Investigating Open Source LLMs to Retrofit Competency Que... |
| W4399598180 | maybe | gpt-4o-2024-05-13 | B | full | classification | accuracy (dialogue-level hallucination det...=80.64 (n=-) | high | - | HalluDial: A Large-Scale Benchmark for Automatic Dialogue... |
| W4402618820 | ineligible | gpt-4o-2024-05-13 | S | full | classification | AUC (N2 lymph node metastasis prediction, ...=0.714 (n=-) | mid | data_closed | The Power of Combining Data and Knowledge: GPT-4o is an E... |
| W4411120358 | eligible | gpt-4-turbo-2024-04-09 | S | full | mcq | accuracy (answer-only, 0-shot, Average ove...=57.43 (n=79280) | high | - | CFinBench: A Comprehensive Chinese Financial Benchmark fo... |
| W4403786591 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | agentic | success rate (human-robot perception align...=61.9 (n=-) | mid | human_outcome | SYNERGAI: Perception Alignment for Human-Robot Collaboration |
| W7131248021 | ineligible | gpt-5-2025-08-07 | S | full | generation | diagnostic correction rate=0.38 (n=200) | mid | data_closed, human_outcome | Evaluating the AI Potential as a Safety Net for Diagnosis... |
| W7161421448 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | odds ratio of paternalistic tone, ID Prese...=136.59 (n=5000) | high | - | Identifying implicit bias in LLM-based chat AI toward peo... |
| W4416281425 | ineligible | gpt-4-turbo-2024-04-09 | B | none | agentic | ROUGE-1 / LLaMA-3-Eval on InsightBench (Ag...=0.3 (n=-) | high | no_prompt | Strategic Business Management in the Banking Sector: Enha... |
| W7130393701 | ineligible | unresolved | C | partial | generation | faithfulness score=1.0 (n=-) | low | no_number | Enhancing RAG with Agentic AI and Multi-HyDE for Knowledg... |
| W7140134498 | ineligible | unresolved | C | full | classification | average F1 (test set)=73.0 (n=150) | low | no_number | Measuring Social Integration Through Participation: Categ... |
| W7169863738 | ineligible | unresolved | C | partial | extraction | strict per-entity F1 (ECM extraction)=- (n=399) | low | no_number, data_closed | Recovering Engineering-Change Traceability from Legacy CN... |
| W7172172215 | maybe | gpt-4.1-nano | S | full | generation | test-selection rate (MBPP documentation-vs...=17.4 (n=268) | low | - | When Specifications Conflict: A Symmetry-Based Framework ... |
| W7152331263 | ineligible | gpt-4.1-nano | B | full | classification | weighted F1 (direct classification, GPT-4....=- (n=500) | low | no_number | Classifying Problem and Solution Framing in Congressional... |
| W4412887941 | ineligible | o1-2024-12-17 | S | none | generation | number of literature-attested Russenorsk p...=17 (n=27) | low | no_prompt | Smotrom tvoja pa ander drogoj verden! Resurrecting Dead P... |
| W7139077229 | ineligible | gpt-5-2025-08-07 | S | none | generation | proportion of SAP items scored accurate (s...=0.72 (n=414) | low | no_prompt, human_outcome | From Protocol to Analysis Plan: Development and Validatio... |
| W4401545735 | maybe | gpt-4o-2024-05-13 | B | partial | classification | accuracy (naive prompting, Financial Phras...=74.57 (n=2264) | mid | - | Designing Heterogeneous LLM Agents for Financial Sentimen... |
| W4412888523 | ineligible | unresolved | S | partial | other | Hits@1 (WebQSP, LLM-only CoT prompting)=72.11 (n=1639) | mid | dead_alias | FiDeLiS: Faithful Reasoning in Large Language Models for ... |
| W4411119861 | ineligible | unresolved | A | partial | generation | AlpacaEval 2.0 win rate (Llama2-7B-Chat wi...=- (n=805) | low | no_number | Alleviating Hallucinations of Large Language Models throu... |
| W4404782629 | maybe | gpt-4-turbo-2024-04-09 | S | full | mcq | exact-match accuracy (Top-View Recognition...=69.52 (n=11384) | high | - | TopViewRS: Vision-Language Models as Top-View Spatial Rea... |
| W4416415653 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | accuracy (full-text screening vs expert re...=0.87 (n=-) | mid | no_prompt, webui | Analysis of article screening and data extraction perform... |
| W4405627542 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | agentic | safety score, Total (%)=41.9 (n=2000) | high | no_prompt | Agent-SafetyBench: Evaluating the Safety of LLM Agents |
| W4406840430 | maybe | gpt-4o-2024-05-13 | B | partial | mcq | accuracy (MedMCQA ophthalmology subset)=0.82 (n=6990) | high | - | Can OpenAI o1 Reason Well in Ophthalmology? A 6,990-Quest... |
| W4404792825 | maybe | gpt-4o-2024-05-13 | S | full | other | General Self-Efficacy scale score (baselin...=31.36 (n=-) | low | - | Will LLMs Sink or Swim? Exploring Decision-Making Under P... |
| W4405254823 | ineligible | unresolved | C | full | generation | pass@1 (VerilogEval, fine-tuned code models)=- (n=-) | low | no_number | PyraNet: A Multi-Layered Hierarchical Dataset for Verilog |
| W4405767381 | ineligible | gpt-4o-2024-05-13 | A | full | classification | labeling accuracy vs human labels=97.81 (n=274) | low | no_number | The HalluRAG Dataset: Detecting Closed-Domain Hallucinati... |
| W4415312658 | ineligible | gpt-4o-2024-05-13 | A | partial | generation | pairwise win rate vs baseline (GPT-4o judge)=- (n=-) | high | no_number | Treasure Hunt: Real-time Targeting of the Long Tail using... |
| W4414476094 | ineligible | gpt-4-turbo-2024-04-09 | S | none | generation | human similarity rating (1-7)=4.2 (n=-) | low | human_outcome, data_closed, no_prompt | AI-DRIVEN AUTOMATED SLIDE GENERATION AND TRANSCRIPT-BASED... |
| W4406840425 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | accuracy (PHQ-8 >= 10 classification, DAIC...=0.77 (n=-) | low | data_closed | A Layered Multi-Expert Framework for Long-Context Mental ... |
| W4414249912 | ineligible | gpt-4-turbo-2024-04-09 | A | full | other | forecast error of MGDF (crude oil price)=- (n=-) | low | no_number, data_closed | MGDF: an embedded multi-graph deep learning method for cr... |
| W4417292655 | ineligible | unresolved | B | none | generation | none (qualitative comparison of translations)=- (n=-) | low | webui, no_number | An Exploration of Current Affairs Translation based on Ar... |
| W4410839161 | ineligible | unresolved | C | none | generation | similarity score (expert evaluation, English)=0.9444 (n=-) | low | no_number | LuminaURO: A comprehensive Artificial Intelligence Driven... |

## Observations

- Eight of the 50 live-model hits are citation-only (role C): W7125877182, W7155654736, W7130393701, W7140134498, W7169863738, W4404187894, W4405254823, W4410839161, plus W4402942065 whose text is the wrong document. The body-scan alias resolution of 'GPT-4 Turbo' therefore over-counts by roughly a fifth of the group.
- Eight papers use the live model only as an annotator, generator, reformatter or judge (role A): W4400141942, W7166885218, W7204134240, W7154427322, W4411119861, W4405767381, W4415312658, W4414249912. Their reported numbers belong to fine-tuned or downstream models.
- Prompts are frequently printed outside the paper body: online supplementary files or GitHub only (W7171738920, W4403823684, W4412887941, W7139077229, W4416415653), or as figure images whose text is not in the extraction (W4415062531, W4406840430, W4406840425; W4411119226's Figure 1 is font-shifted but decodable).
- Unversioned model names remain a problem after 2024: 'GPT-4o' without a snapshot is the subject in W4403823684, W7125877182 and W7155654736, and 'GPT-4.0' via a router in W7152331263; the schema's date rule only covers GPT-4 Turbo, so these stay unresolved.
- The three eligible papers differ widely in cost: W4411119226 needs ~720 calls, while W4411120358 (~79k MCQs per seed) and W7161421448 (5k generations plus 5k analysis calls per seed) are high-tier; several maybes (CANDY, HalluDial, TopViewRS, MedMCQA-ophthalmology) are also 20k-60k items.
- Two text files are unusable for triage: W4402942065 is the Gemini 1.5 report, and W7106340049 (M.Sc. thesis) is truncated at page 40 before its results chapter; W4416281425's body reproduces the InsightBench agent study under a banking-management title.
