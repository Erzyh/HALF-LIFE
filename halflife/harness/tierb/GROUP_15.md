# Tier B triage, group 15 (49 papers)

Counts: eligible 10, maybe 12, ineligible 27.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md`. Order follows `data/tierb_triage/group_15.csv` (rank).

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4406735017 | ineligible | dead-preview | C | full | other | none (footnote only) | low | dead_alias, no_number | Multi-round, Chain-of-thought Post-editing for Unfaithful Su… |
| W4405561711 | maybe | gpt-4-turbo-2024-04-09 | B | partial | mcq | Avg MC=62.21 (5600) | mid | - | Rethinking Comprehensive Benchmark for Chart Understanding:… |
| W4415135175 | ineligible | unresolved | C | none | other | none (mention only) | low | no_number | The Pastor as Romantic Author: AI, Preaching, and the Unackn… |
| W4412889412 | maybe | gpt-4-turbo-2024-04-09 | B | partial | classification | accuracy=79.51 (300) | low | - | Making Sense of Korean Sentences: A Comprehensive Evaluation… |
| W4405311095 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | generation | none (data generator) | low | no_number | RoomTour3D: Geometry-Aware Video-Instruction Tuning for Embo… |
| W7159891030 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | none (decomposer only) | low | no_number | Unified Data Discovery across Query Modalities and User Inte… |
| W4410407371 | maybe | o3-mini-2025-01-31 | S | full | classification | F1=0.883 (6443) | high | - | Enhancing Substance Use Detection in Clinical Notes with Lar… |
| W4414979614 | eligible | gpt-5-2025-08-07 | S | full | extraction | F1 (contr, EN)=0.93 (30) | mid | - | Overcoming Language Barriers: Multilingual Analysis of the 2… |
| W4405355481 | ineligible | dead-preview | B | none | other | none (dead baseline) | low | dead_alias | Sail into the Headwind: Alignment via Robust Rewards and Dyn… |
| W4404570241 | ineligible | unresolved | C | none | other | none (forum theme) | low | no_number | Developer Challenges on Large Language Models: A Study of St… |
| W7162606056 | ineligible | unresolved | C | none | other | none (survey table) | low | no_number | LLM-as-a-Judge in Healthcare: A Scoping Analysis of Applicat… |
| W7163747669 | ineligible | gpt-4.1-nano-2025-04-14 | C | none | other | none (cited energy) | low | no_number | Green AI: A Framework for Energy-Efficient and Sustainable M… |
| W4412889012 | ineligible | gpt-4.1-nano-2025-04-14 | B | partial | classification | none (figure only) | low | no_number | EMULATE: A Multi-Agent Framework for Determining the Veracit… |
| W7203893220 | maybe | gpt-4.1-nano-2025-04-14 | B | partial | agentic | ADE=7.22 (n/a) | high | - | GAPL: Grounded Action-effect Policy Learning for LLM-Based T… |
| W7166871080 | eligible | gpt-4.1-nano-2025-04-14 | B | full | classification | accuracy=89.54 (100502) | mid | - | 100,000+ Movie Reviews from Kazakhstan: Russian, Kazakh, and… |
| W7165972458 | ineligible | gpt-4.1-nano-2025-04-14 | B | partial | mcq | none (figure only) | low | no_number | Legal Reasoning Is Not Lawyering: Rethinking Legal Benchmark… |
| W7169474253 | maybe | gpt-4.1-nano-2025-04-14 | B | partial | classification | F1=0.79 (62) | low | - | Beyond Binary Detection: A Multi-Dimensional Taxonomy of Can… |
| W7203692329 | ineligible | gpt-4.1-nano-2025-04-14 | B | none | classification | none (discarded) | low | no_number | Operationalising Large Language Models for Financial Sentime… |
| W7203633312 | ineligible | gpt-4.1-nano-2025-04-14 | C | none | other | none (prior work) | low | no_number, webui | Buddhist, Yogic, and Vedic Contemplative Principles in AI Mo… |
| W7125460230 | eligible | gpt-4.1-nano-2025-04-14 | B | full | classification | Macro-F1=0.337 (1000) | low | - | ClaimDB: A Fact Verification Benchmark over Large Structured… |
| W7203859208 | ineligible | gpt-4.1-nano-2025-04-14 | B | none | extraction | none (incomplete) | low | no_number | Automating scientific annotations for open transcriptomic pr… |
| W4410633563 | maybe | o3-mini-2025-01-31 | S | partial | mcq | accuracy=92.99 (n/a) | mid | - | Reasoning Over Pre-training: Evaluating LLM Performance and… |
| W7140953907 | eligible | o3-mini-2025-01-31 | S | full | classification | Yes%=100 (1000) | high | - | How Utilitarian Are OpenAI's Models Really? Replicating and… |
| W7125459680 | maybe | o3-mini-2025-01-31 | B | partial | generation | avg score=92.2 (100) | mid | - | AI for Mathematics: Progress, Challenges, and Prospects |
| W4412888017 | ineligible | o1-2024-12-17 | A | partial | generation | none (rationale gen) | low | no_number | DeRAGEC: Denoising Named Entity Candidates with Synthetic Ra… |
| W7135156771 | maybe | o4-mini-2025-04-16 | S | full | other | Crisis Detect=8.93 (70) | low | - | Empathy Is Not What Changed: Clinical Assessment of Psycholo… |
| W4416932034 | maybe | o3-2025-04-16 | B | partial | classification | kappa=0.59 (n/a) | mid | - | Development and Benchmarking of a Blended Human-AI Qualitati… |
| W7155245866 | ineligible | gpt-5-mini-2025-08-07 | B | partial | generation | S3(ISO)=3.95 (287) | high | data_closed | Evaluating Multimodal LLMs for Inpatient Diagnosis: Real-Wor… |
| W7124513739 | eligible | gpt-5-2025-08-07 | S | full | generation | Addressed%=88 (1100) | mid | - | MedRedFlag: Investigating how LLMs Redirect Misconceptions i… |
| W7108248001 | maybe | gpt-5-2025-08-07 | S | partial | generation | Win Rate=0.695 (300) | low | - | HUMORCHAIN: Theory-Guided Multi-Stage Reasoning for Interpre… |
| W7166864620 | maybe | unresolved | S | full | agentic | Win Rate=16.67 (12) | mid | alias_unpinned | Can AI Revise Research Papers with Human Review Feedback? An… |
| W7204104731 | eligible | gpt-5-mini-2025-08-07 | B | full | classification | accuracy=0.75 (38) | low | - | Using Human-LLM Disagreement to Improve Checklist-Based Qual… |
| W7203473845 | ineligible | gpt-5-nano-2025-08-07 | S | partial | extraction | none (in SI only) | low | no_number | Cascading Hazards, Contested Futures: Media Analysis of the… |
| W7161091627 | ineligible | gpt-5-mini-2025-08-07 | S | partial | other | none (figure only) | low | no_number | Political Plasticity: An Analysis of Ideological Adaptabilit… |
| W4401660192 | ineligible | gpt-4-turbo-2024-04-09 | B | none | generation | none (closed eval) | low | data_closed | Qwen2 Technical Report |
| W7124249593 | ineligible | unresolved | C | none | other | none (mention only) | low | no_number | A Survey on Small Language Models |
| W4402670901 | eligible | gpt-4o-2024-05-13 | B | partial | generation | Avg=79.0 (3709) | mid | - | MathBench: Evaluating the Theory and Application Proficiency… |
| W4412945594 | eligible | gpt-4o-2024-05-13 | B | partial | agentic | File Acc@1=57.30 (300) | high | - | LocAgent: Graph-Guided LLM Agents for Code Localization |
| W4403021429 | ineligible | gpt-4o-2024-05-13 | S | partial | generation | none (one example) | low | no_number | Real-world cooking robot system from recipes based on food s… |
| W4411569746 | ineligible | gpt-4-turbo-2024-04-09 | C | none | classification | none (prior study) | low | no_number | Optimal large language models to screen citations for system… |
| W4404459995 | ineligible | gpt-4-turbo-2024-04-09 | C | full | other | none (not selected) | low | no_number | AI Chatbots: Fast Tracking Sustainability Report Analysis fo… |
| W4409365705 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | other | none (KD teacher) | low | no_number | Active Large Language Model-Based Knowledge Distillation for… |
| W4406443929 | maybe | gpt-4o-2024-05-13 | S | partial | extraction | accuracy +26.71% (16) | low | - | Agentic LLM Workflows for Generating Patient-Friendly Medica… |
| W4412732787 | ineligible | gpt-4-turbo-2024-04-09 | S | full | generation | none (values n/a) | low | webui | Evaluating the accuracy of generative artificial intelligenc… |
| W4403719800 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | generation | none (data generator) | low | no_number | Harnessing LLMs for API Interactions: A Framework for Classi… |
| W4411120015 | eligible | gpt-4o-2024-05-13 | S | full | classification | accuracy=96.7 (n/a) | mid | - | Exploring Large Language Models for Effective Rumor Detectio… |
| W4399511962 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | accuracy=33.5 (1335) | high | - | CRAG -- Comprehensive RAG Benchmark |
| W4416034134 | ineligible | unresolved | C | none | other | none (survey table) | low | no_number | Large Language Model Agents in Finance: A Survey Bridging Re… |
| W4404313603 | ineligible | unresolved | C | none | other | none (mention only) | low | no_number | A Survey of Small Language Models |

## Observations

- Alias resolution: 18 rows carry a bare `gpt-4-turbo`. Two resolve to a dead preview instead of the GA snapshot: W4406735017's only hit is a footnote URL naming `gpt-4-0613`, and W4405355481's "GPT-4-Turbo" win-rate baseline turns out to be the fixed Arena-Hard/AlpacaEval `GPT-4-Preview-1106`. The rest post-date 2024-07-01 with no preview string and resolve to `gpt-4-turbo-2024-04-09` by the date rule alone. `gpt-4.1-nano` behaved differently: the task's alias dispensation let all 10 bare mentions resolve straight to `gpt-4.1-nano-2025-04-14` regardless of paper date. Bare o-series/GPT-5 mentions got no such dispensation; W7166864620's undated `O4-MINI` stayed "unresolved" (blocker `alias_unpinned`), capping an otherwise clean, publicly-released benchmark at maybe.
- Annotator-with-validation is the recurring judgment call. When a model is used to help build a dataset (fill gaps a second human annotator would have covered) but the paper reports its own accuracy against human/gold labels, it was scored role B and kept on the eligible track (W4412889412 Korean sentence endings, W7166871080 Kazakh movie reviews). When the model instead generates/parses/scores something with no gold-standard check on its own output, it stayed role A and ineligible with `no_number` (W4405311095 instruction generation, W7159891030 query decomposition, W4412888017 rationale synthesis, W4409365705 KD teacher, W4403719800 synthetic-data generation).
- Mention-only citation is the single largest ineligibility reason: 3 surveys (W7124249593, W4404313603, W4416034134), 1 scoping review (W7162606056), and several papers citing their own or others' prior work (W4404570241, W4411569746, W7203633312, W4404459995, W4404313603) never call the live model themselves.
- Figure-only claims recur across model families: W4412889012 (GPT-4.1 family ablation), W7165972458 and W7161091627 (bar-chart-only accuracy/shift results), and W7203473845 (extraction accuracy explicitly deferred to a supplementary file not in the provided text) all have a real experiment but no printed number to cite.
- Data closure blocked two otherwise strong cases: Qwen2's GPT-4-Turbo comparison lives only in a closed, self-designed multilingual human-eval set (W4401660192), and a ten-model LMIC inpatient-diagnosis benchmark uses real, non-public hospital cases (W7155245866). Two papers used a consumer chat product rather than a pinned API snapshot (`webui`: W4412732787, and W7203633312 alongside its citation problem).
- Cost skews high wherever the claim needs thousands of calls or many-turn agentic rollouts on an o-series/GPT-5 model: W4410407371 (o3-mini, n=6443), W7140953907 (o3-mini/o3, n=1000/dilemma), W4399511962 (GPT-4 Turbo, n=1335), W4412945594 and W7203893220 (agent rollouts). The cheapest eligible cases sit on gpt-4.1-nano, which is priced roughly 100x below gpt-4-turbo (W7125460230 at 1,000 calls, W7166871080 at over 100k calls, still "mid" tier only because of sheer volume).
