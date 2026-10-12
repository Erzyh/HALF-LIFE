# Tier B triage, group 16 (49 papers)

Counts: eligible 7, maybe 18, ineligible 24.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md`. Order follows `data/tierb_triage/group_16.csv` (rank).

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4413969678 | ineligible | unresolved | C | none | other | none (writing aid only) | low | no_number | An integral vision of pain and its persistence: a whole-per… |
| W4404260739 | ineligible | gpt-4o-2024-05-13 | S | partial | agentic | TSP100 avg gap%=0.043 (1000) | high | no_number | In-the-loop Hyper-Parameter Optimization for LLM-Based Auto… |
| W4416184760 | ineligible | gpt-4-turbo-2024-04-09 | B | partial | extraction | RMSE (HAS-BLED)=0.26 (179) | high | data_closed | Development of an LLM Pipeline Surpassing Physicians in Car… |
| W4412889354 | ineligible | gpt-4-turbo-2024-04-09 | B | full | classification | none (chart only, n=3719) | high | data_closed | Beyond Metrics: Evaluating LLMs Effectiveness in Culturally… |
| W4400611869 | eligible | gpt-4-turbo-2024-04-09 | B | full | classification | accuracy=82.2 (1000) | mid | - | Lynx: An Open Source Hallucination Evaluation Model |
| W4404782507 | maybe | gpt-4o-2024-05-13 | S | full | classification | AVeriTeC score=0.50 (n/a) | high | - | AIC CTU system at AVeriTeC: Re-framing automated fact-check… |
| W4402466848 | ineligible | gpt-4-turbo-2024-04-09 | B | none | classification | none (n/a outcome, n=5200) | high | no_number | Trust or Escalate: LLM Judges with Provable Guarantees for… |
| W4405095511 | ineligible | unresolved | C | none | other | none (judge citation only) | low | no_number | Aya Expanse: Combining Research Breakthroughs for a New Mul… |
| W4406167407 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | none (annotator only) | low | no_number | LLM Content Moderation and User Satisfaction: Evidence from… |
| W4417146272 | ineligible | unresolved | C | none | other | none (writing aid only) | low | no_number | Variation in body weight and feed intake trajectories are p… |
| W4399447566 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | none (pairwise judge only) | low | no_number | Scaling Laws for Reward Model Overoptimization in Direct Al… |
| W7125599892 | ineligible | unresolved | C | none | other | none (survey citation only) | low | no_number | Deep Reinforcement Learning for Surgical Robotics with Stat… |
| W4403810065 | ineligible | gpt-4-turbo-2024-04-09 | B | none | classification | F1 (patent class.)=0.73 (n/a) | mid | no_number | Towards Automated Patent Workflows: AI-Orchestrated Multi-A… |
| W4405627345 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | other | none (annotation only) | low | no_number | Fake News Detection: Comparative Evaluation of BERT-like Mo… |
| W4410398015 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | F1 (2B)=0.72 (200) | mid | - | Analysis of Propaganda in Tweets From Politically Biased So… |
| W4405693132 | ineligible | unresolved | C | none | other | none (citation only) | low | no_number | Revolutionizing Healthcare Delivery: Evaluating the Impact… |
| W4415064567 | maybe | o1-2024-12-17 | S | partial | generation | Correctness=33.28 (n/a) | high | - | FinDER: Financial Dataset for Question Answering and Evalua… |
| W4405768066 | ineligible | unresolved | C | none | other | none (scoping review) | low | no_number | Large language models for conducting systematic reviews: on… |
| W4411119905 | maybe | gpt-4-turbo-2024-04-09 | S | full | classification | Micro F1 (ChemProt)=0.626 (n/a) | high | - | Entangled Relations: Leveraging NLI and Meta-analysis to En… |
| W4415363367 | maybe | gpt-4.1-nano-2025-04-14 | S | partial | agentic | UNKNOWN rate=4.4 (500) | mid | - | Clinical Agents Don’t Care |
| W7128827394 | maybe | o4-mini-2025-04-16 | S | full | generation | CER=6.87 (1029) | high | - | Evaluating LLMs for Historical Document OCR: A Methodologic… |
| W4407425826 | eligible | gpt-4o-2024-05-13 | S | full | generation | correct-rate=50.7 (140) | low | - | Verifying LLM-Generated Code in the Context of Software Ver… |
| W4403810020 | maybe | gpt-4-turbo-2024-04-09 | S | partial | other | NDCG@10=0.693 (50) | high | - | Controlled LLM-based Reasoning for Clinical Trial Retrieval |
| W4412888925 | ineligible | unresolved | C | none | other | none (background mention) | low | no_number | Exploring Semantic Filtering Heuristics For Efficient Claim… |
| W7125521524 | ineligible | unresolved | S | partial | generation | none (qualitative, n=1) | low | webui, no_number | O Serviço Social e a tomada de decisão algorítmica: A utili… |
| W4416037167 | ineligible | gpt-4-turbo-2024-04-09 | A | none | other | none (judge only) | low | no_number | Permutative Preference Alignment from Listwise Ranking of H… |
| W4412887969 | maybe | gpt-4-turbo-2024-04-09 | S | full | generation | gap%=0.18 (n/a) | high | - | Nested-Refinement Metamorphosis: Reflective Evolution for E… |
| W4410348348 | ineligible | unresolved | S | full | classification | kappa=0.78 (n/a) | low | dead_alias | Accuracy is Not Agreement: Expert-Aligned Evaluation of Cra… |
| W7129376919 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | recall=95.5 (11300) | high | - | Collaborative large language models (LLMs) are all you need… |
| W4414360395 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | F1=0.7381 (n/a) | high | - | Classifying and Tracking International Aid Contribution Tow… |
| W4403482870 | ineligible | gpt-4-turbo-2024-04-09 | S | full | other | none (demo only, n=1) | low | no_number | Selecting Countermeasures against Fake News using Large Lan… |
| W4409364614 | maybe | gpt-4-turbo-2024-04-09 | S | partial | agentic | %SR=40.1 (n/a) | high | - | GNN-Transformer Task Planning Enhanced with Semantic-Driven… |
| W4404781112 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | micro-F1 (RC)=65.5 (n/a) | mid | - | CERD: A Comprehensive Chinese Rhetoric Dataset for Rhetoric… |
| W4412889683 | ineligible | unresolved | C | none | other | none (mention only) | low | no_number | Assessing Reliability and Political Bias In LLMs’ Judgement… |
| W4417350538 | maybe | gpt-4.1-nano-2025-04-14 | S | partial | mcq | Flipped-To=18.8 (14042) | mid | - | "Check My Work?": Measuring Sycophancy in a Simulated Educa… |
| W7104423191 | maybe | gpt-5-nano-2025-08-07 | S | full | classification | F1=0.92 (1143) | low | - | Evaluating LLM-Generated Legal Explanations for Regulatory… |
| W4403038909 | maybe | gpt-4o-2024-05-13 | S | full | classification | score=0.686 (n/a) | low | - | Sarcasm Detection in a Less-Resourced Language |
| W4416034242 | maybe | o4-mini-2025-04-16 | S | partial | generation | pass@1=15.85 (235) | high | - | Humanity’s Last Code Exam: Can Advanced LLMs Conquer Human’… |
| W4416690282 | ineligible | gpt-4o-2024-05-13 | A | none | other | none (human-checked only) | low | no_number | Evaluating English-Korean Literary Machine Translations: A… |
| W4407571270 | eligible | gpt-4o-2024-05-13 | S | partial | classification | F1=0.762 (198) | low | - | Web Publication of Local Assembly Minutes in Tokachi, Hokka… |
| W7128864310 | eligible | gpt-4o-2024-05-13 | S | full | classification | %Agree=87.24 (243) | low | - | GPT-4o Lacks Core Features of Theory of Mind |
| W4407642372 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | MAE=0.254 (n/a) | low | - | GPT-4 y sus modelos sucesores en la predicción de la comple… |
| W4409141327 | maybe | gpt-4-turbo-2024-04-09 | S | partial | extraction | accuracy=86.1 (n/a) | low | - | impact of LLaMA fine tuning on hallucinations for name enti… |
| W7154538978 | ineligible | unresolved | C | none | other | none (survey) | low | no_number | From GPT-3 to GPT-5: Mapping their capabilities, scope, lim… |
| W4403928890 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | F1=0.82 (48) | low | - | Getting in the Door: Streamlining Intake in Civil Legal Ser… |
| W4404261107 | maybe | gpt-4-turbo-2024-04-09 | S | partial | generation | F-Measure=0.67 (n/a) | low | - | SmartGSN: an online tool to semi-automatically manage assur… |
| W4403996071 | ineligible | dead-preview | B | none | generation | Pass@1=86.6 (n/a, dead preview) | low | dead_alias | CELI: Controller-Embedded Language Model Interactions |
| W4403665748 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | agentic | none (figure only, n=20 trials) | low | no_number | Toward Automated Simulation Research Workflow through LLM P… |
| W4416683695 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | bias%=93.0 (2484) | mid | - | AI Self-preferencing in Algorithmic Hiring: Empirical Evide… |
