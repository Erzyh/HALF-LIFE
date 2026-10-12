# Tier B triage, group 18 (49 papers)

Counts: eligible 5, maybe 6, ineligible 38.

Records: one JSON per paper in this directory (`<wid>.json`), schema in `SCHEMA.md`. Order follows `data/tierb_triage/group_18.csv` (rank). Two blocker tags outside the SCHEMA list are used, following GROUP_2's convention: `prompt_none` (the prompt is not printed in the paper, only in an external repository) and `alias_unpinned` (an undated `gpt-4o`/`GPT-4.1` mention that the SCHEMA's date rule leaves unresolved).

| wid | verdict | resolved live model | role | prompt | task_type | metric=value (n) | cost | blockers | title |
|---|---|---|---|---|---|---|---|---|---|
| W4412888662 | ineligible | unresolved | C | none | other | none (cited) | low | no_number | A Survey of Large Language Models in Psychotherapy: Current… |
| W4407230179 | ineligible | unresolved | C | none | other | none (disclosure) | low | no_number | The data scientist as a mainstay of the tumor board: global… |
| W4414137518 | ineligible | unresolved | C | none | other | none (disclosure) | low | no_number | Sudden cardiac death in the young: single-center study of Ba… |
| W4402711364 | ineligible | unresolved | C | none | other | none (cites EffiBench) | low | no_number | A Survey on Evaluating Large Language Models in Code Generat… |
| W4404782618 | eligible | gpt-4o-2024-05-13 | S | full | classification | Total acc (SoV)=50.10 (459) | mid | - | Visual Prompting in LLMs for Enhancing Emotion Recognition |
| W4412945194 | ineligible | unresolved | C | none | other | none (cited) | low | no_number | From Selection to Generation: A Survey of LLM-based Active L… |
| W4403083371 | ineligible | unresolved | C | none | other | none | low | no_number | The Impact of ChatGPT on Higher Education |
| W4411120238 | maybe | gpt-4-turbo-2024-04-09 | S | partial | generation | spBLEU en->xx=37.01 (27324) | high | - | Multilingual Machine Translation with Open Large Language Mo… |
| W4411113222 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | Mamo overall acc=66.34 (1209) | high | - | LLMs for Mathematical Modeling: Towards Bridging the Gap bet… |
| W4402671037 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | other | none (judge only) | low | no_number | Synthetic Arabic Medical Dialogues Using Advanced Multi-Agen… |
| W4405560434 | ineligible | unresolved | S | partial | classification | sensitivity=70 (87) | low | webui, alias_unpinned, data_closed | Feasibility of large language models for CEUS LI-RADS catego… |
| W4412886885 | ineligible | o3-mini-2025-01-31 | S | none | generation | Rubrics score=60.6 (100) | mid | aux_model_dead | Ai2 Scholar QA: Organized Literature Synthesis with Attribut… |
| W4416036264 | ineligible | unresolved | C | none | other | none (cited) | low | no_number | Position: LLMs Can be Good Tutors in English Education |
| W4413808555 | ineligible | gpt-4-turbo-2024-04-09 | S | full | extraction | U-value overest.=40 (4) | low | webui | LARGE LANGUAGE MODELS AS TOOLS FOR PUBLIC BUILDING ENERGY MA… |
| W4411119599 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | classification | none (figure only) | low | no_number | Evaluating Bias in LLMs for Job-Resume Matching: Gender, Rac… |
| W4409362832 | ineligible | gpt-4o-2024-05-13 | S | none | classification | Micro-F1 (MABSA)=25.7 (n/a) | low | prompt_none | DEQA: Descriptions Enhanced Question-Answering Framework for… |
| W4403689071 | ineligible | gpt-4-turbo-2024-04-09 | S | none | extraction | F1 (Kazakh QA)=73.33 (n/a) | low | prompt_none | COMPARATIVE ANALYSIS OF MULTILINGUAL QA MODELS AND THEIR ADA… |
| W4411119926 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | rho (AlpacaEval)=0.9112 (14490) | high | - | Re-evaluating Automatic LLM System Ranking for Alignment wit… |
| W4409362465 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | Relevance acc=79.8 (200) | low | prompt_none | Measuring Human and AI Values Based on Generative Psychometr… |
| W4403754117 | maybe | gpt-4-turbo-2024-04-09 | S | full | agentic | mean reward=-636.4 (5) | mid | - | InvAgent: A Large Language Model based Multi-Agent System fo… |
| W4407209197 | ineligible | unresolved | C | none | other | none (cited) | low | no_number | RAG for Personalized Medicine: A Framework for Integrating P… |
| W4403808762 | ineligible | unresolved | C | none | other | none (background) | low | no_number | GP-GPT: Large Language Model for Gene-Phenotype Mapping |
| W4403730209 | ineligible | gpt-4o-2024-05-13 | S | full | generation | quality score n/a (5) | low | webui | Assessing the Performance of ChatGPT in Answering Patients’… |
| W4402855388 | ineligible | gpt-4-turbo-2024-04-09 | S | none | agentic | Unmasked Wolf=75.0 (n/a) | mid | prompt_none | Werewolf Arena: A Case Study in LLM Evaluation via Social De… |
| W4407176798 | ineligible | gpt-4o-2024-11-20 (dead) | S | partial | classification | PLS=28.7% (805) | high | aux_model_dead | Preference Leakage: A Contamination Problem in LLM-as-a-judg… |
| W7124309492 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | exec time=69.77s (n/a) | low | webui | Code Generation by Large Language Models: A Comparative Anal… |
| W4403580619 | eligible | gpt-4-turbo-2024-04-09 | S | full | classification | PMR (CoT)=0.1773 (1003) | mid | - | Evaluating Gender Bias of LLMs in Making Morality Judgements |
| W4403780340 | ineligible | unresolved | C | none | other | none (cited) | low | no_number | Advancing Depression Detection on Social Media Platforms Thr… |
| W4416034273 | ineligible | gpt-4.1-nano-2025-04-14 | B | none | generation | none (figure only) | low | no_number | FigEx: Aligned Extraction of Scientific Figures and Captions |
| W4404310794 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | none (pooled range only) | low | no_number | Good Parenting is all you need -- Multi-agentic LLM Hallucin… |
| W4403586339 | ineligible | gpt-4o-2024-05-13 | S | none | generation | Pass@1 (HumanEval)=90.62 (164) | low | prompt_none | Multi-Programming Language Ensemble for Code Generation in L… |
| W4414672437 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | none (rating scale) (5) | low | webui | Artificial Intelligence in Pediatric Urology: Accuracy and C… |
| W4411113107 | maybe | gpt-4-turbo-2024-04-09 | S | full | generation | BERTScore F1=88.00 (n/a) | mid | - | GraPPI: A Retrieve-Divide-Solve GraphRAG Framework for Large… |
| W4402345581 | ineligible | unresolved | C | none | extraction | none (cited) | low | no_number | NinjaLLM: Fast, Scalable and Cost-effective RAG using Amazon… |
| W4407569651 | eligible | gpt-4-turbo-2024-04-09 | S | full | generation | Glob. acc (0-shot)=38.4 (510) | mid | - | CIRCUIT: A Benchmark for Circuit Interpretation and Reasonin… |
| W7124283595 | ineligible | o1-2024-12-17 | S | full | classification | T-factor acc n/a (100) | high | webui, data_closed | TNM Classification of Pancreatic Cancer From Unstructured Ra… |
| W4412889612 | maybe | gpt-4-turbo-2024-04-09 | S | partial | classification | Pearson r=0.459 (n/a) | mid | - | CiteEval: Principle-Driven Citation Evaluation for Source At… |
| W4416034827 | ineligible | gpt-4-turbo-2024-04-09 | A | partial | classification | none (cost only) | low | no_number | Summarize-Exemplify-Reflect: Data-driven Insight Distillatio… |
| W4414855056 | maybe | gpt-4-turbo-2024-04-09 | B | partial | agentic | ROUGE-L=0.35 (n/a) | mid | - | Agent-UniRAG: A Trainable Open-Source LLM Agent Framework fo… |
| W4413544481 | ineligible | unresolved | C | none | other | none (disclosure) | low | no_number | Differential impact of biologically effective dose in distal… |
| W4403853622 | ineligible | gpt-4-turbo-2024-04-09 | S | none | classification | % positive=9.24 (2998) | mid | prompt_none | Hierarchical Narrative Analysis: Unraveling Perceptions of G… |
| W4414359799 | ineligible | gpt-4-turbo-2024-04-09 | S | partial | generation | none (figure only) | low | no_number | Are Large Language Models Fluent in Declarative Process Mini… |
| W4404393581 | maybe | gpt-4-turbo-2024-04-09 | S | partial | generation | robustness R=0.3076 (100) | low | - | AutoRNet: Automatically Optimizing Heuristics for Robust Net… |
| W4415230395 | ineligible | gpt-4-turbo-2024-04-09 | A | full | classification | none (validation only) (200) | low | no_number | What Comes After Harm? Mapping Reparative Actions in AI Thro… |
| W4403571127 | ineligible | gpt-4-turbo-2024-04-09 | S | none | mcq | avg acc (High)=79.4 (3180) | mid | prompt_none | Efficiently Democratizing Medical LLMs for 50 Languages via… |
| W4416959427 | ineligible | gpt-5-2025-08-07 | S | partial | mcq | MedQA acc=96.2 (500) | high | aux_model_dead | Generalist Large Language Models Outperform Clinical Tools o… |
| W4416346128 | ineligible | gpt-5-2025-08-07 | B | partial | agentic | none (physical outcome) | low | no_number | Human-AI collaborative autonomous synthesis with pulsed lase… |
| W4414880467 | ineligible | gpt-4o-2024-05-13 | B | none | generation | none (1km acc) (3000) | mid | prompt_none | VLM-Guided Visual Place Recognition for Planet-Scale Geo-Loc… |
| W7165065521 | ineligible | unresolved | S | partial | agentic | TGC=60.3 (115) | mid | alias_unpinned | Not All Skills Help: Measuring and Repairing Agent Knowledge |

## Observations

- Mention-only and disclosure-only citations are the largest ineligible category (12 role-C papers): surveys or position papers citing a third party's GPT-4-Turbo result (W4412888662, W4402711364, W4412945194, W4416036264), a benchmark number copied from another paper for comparison in the authors' own table (W4402345581), pure reference-list/background-prose citations with no experiment at all (W4407209197, W4403808762, W4403780340, W4403083371), and mandatory Generative-AI-use disclosures where the model only polished the manuscript's prose (W4407230179, W4414137518, W4413544481). A further 3 role-A papers (auxiliary annotator/judge/cost-tool for someone else's pipeline, not the paper's own benchmarked subject) are ineligible despite real numbers existing in the text -- see below.
- `prompt_none` is the single largest blocker among papers that otherwise look eligible (8 of 49): several point to a GitHub repository for the actual prompt text (W4402855388 Werewolf Arena, W4403586339, W4414880467), one references an Appendix A/C prompt that never made it into this document's extraction (W4403853622), and others simply never print the query template despite dated models and clean numbers (W4409362832, W4403689071, W4409362465, W4403571127).
- `webui` recurs in small medical case-report-style studies that manually pasted questions into ChatGPT's consumer interface rather than the API (W4403730209, W4414672437, W7124283595, W4405560434, W7124309492, W4413808555) -- a consistent pattern across MED-tagged papers with 0 OpenAlex links.
- `aux_model_dead` catches three papers whose live model or judge is precisely dated but sits just outside the still-callable list: a judge/data-generator pinned to gpt-4o-2024-11-20 (W4407176798), a HealthBench/MedQA grader pinned to the mainline gpt-4.1-2025-04-14 rather than gpt-4.1-nano (W4416959427), and a ScholarQA-CS judge split across gpt-4o-2024-08-06/2024-11-20 (W4412886885).
- Role A (annotator/labeler/judge for someone else's pipeline, not the paper's own benchmarked subject) explains 3 more ineligible verdicts despite real validation numbers existing in the text: citation-quality judging in a dialogue pipeline (W4402671037), incident coding validated at 87%/79% against human labels (W4415230395), and a rule-summarization cost figure with no task-accuracy attached (W4416034827).
- Only 2 papers (W4416959427, W4416346128) use GPT-5 (gpt-5-2025-08-07), and one very recent 2026 arXiv paper (W7165065521) evaluates GPT-5.1/GPT-5.4/mainline GPT-4.1, none of which are on the still-callable list, plus an undated GPT-4o that falls well past the 2024-10-02 cutoff.
- The 5 eligible papers span circuit-reasoning (W4407569651's CIRCUIT benchmark), math modeling (W4411113222's Mamo benchmark), vision-language emotion recognition (W4404782618), meta-evaluation of automatic judges (W4411119926), and gender-bias psycholinguistics (W4403580619); all have dated gpt-4-turbo-2024-04-09 or gpt-4o-2024-05-13, a fully-printed prompt, and public benchmark data. A related paper on multilingual MT (W4411120238) narrowly misses eligible and lands at maybe only because its in-context template, while clear, doesn't pin down the exact few-shot exemplars used. Costs skew high because the eligible claims tend to be full-benchmark averages (459-14,490 items) rather than single-cell results.
