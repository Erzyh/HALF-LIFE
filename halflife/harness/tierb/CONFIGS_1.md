# Tier B run configs, group 1 (32 papers)

Configs written to `halflife/harness/tierb/configs/<wid>.json` following `CONFIG_SCHEMA.md`. Prompts were copied from the extracted texts in `halflife/external/papers_tierb/`; dataset pages were checked with small HTTP requests only (no dataset over 50 MB downloaded, no model API called). Date of the checks: 2026-09-07.

## Counts by status

- ready: 8
- needs_download_check: 9
- needs_human: 15
- total estimated cost: USD 1786 (per-call prices of the task brief; long inputs scaled up)

## Table

| wid | status | model | task | n_items | seeds | est_usd | items source | title |
|---|---|---|---|---|---|---|---|---|
| W4386395478 | needs_human | gpt-4o-2024-05-13 | extraction | 86 | 3 | 1.0 | url: fm-data-tasks.s3.us-west-1.amazonaws.com/data... | Large Language Models as Data Preprocessors |
| W4399598180 | needs_download_check | gpt-4o-2024-05-13 | classification | 3200 | 1 | 16.0 | hf: FlagEval/HalluDial | HalluDial: A Large-Scale Benchmark for Automati... |
| W4400375186 | ready | gpt-4-turbo-2024-04-09 | classification | 100 | 3 | 3.0 | hf: Song-SW/CEB | CEB: Compositional Evaluation Benchmark for Fai... |
| W4402426686 | needs_human | gpt-4-turbo-2024-04-09 | classification | 299 | 3 | 18.0 | github: github.com/GAIR-NLP/Safety-J | SAFETY-J: Evaluating Safety with Critique |
| W4403370432 | needs_human | gpt-4-turbo-2024-04-09 | extraction | 2633 | 3 | 80.0 | url: anonymous.4open.science/r/CPSBench-BED7 | An Evaluation of Requirements Modeling for Cybe... |
| W4403584145 | ready | gpt-4-turbo-2024-04-09 | other | 20 | 1 | 100.0 | in_paper: Synthetic: Methods 'Opinion dynamics simulati... | AI agents can coordinate beyond human scale |
| W4403882351 | needs_human | gpt-4o-2024-05-13 | generation | 165 | 1 | 50.0 | hf: deepmind/code_contests | RLEF: Grounding Code LLMs in Execution Feedback... |
| W4404314294 | ready | gpt-4-turbo-2024-04-09 | mcq | 707 | 3 | 21.0 | hf: Rajat1212/DisasterQA | DisasterQA: A Benchmark for Assessing the perfo... |
| W4404518515 | needs_human | gpt-4-turbo-2024-04-09 | extraction | 50 | 1 | 150.0 | url: APM Reports 'In the Dark' season two source n... | Automating Transparency Mechanisms in the Judic... |
| W4404782508 | needs_download_check | gpt-4o-2024-05-13 | other | 700 | 1 | 10.5 | hf: Joelzhang/ToolBeHonest | ToolBeHonest: A Multi-level Hallucination Diagn... |
| W4404783788 | ready | gpt-4o-2024-05-13 | generation | 1930 | 1 | 500.0 | hf: zai-org/LongBench | Retrieval Augmented Generation or Long-Context ... |
| W4404986534 | needs_human | gpt-4-turbo-2024-04-09 | classification | 5106 | 1 | 51.0 | url: LLMEval2 benchmark | A Survey on LLM-as-a-Judge |
| W4405432557 | needs_human | gpt-4-turbo-2024-04-09 | generation | 40 | 1 | 20.0 | url: GAN Face Database | Vision-Language Models Generate More Homogeneou... |
| W4406058824 | needs_download_check | gpt-4-turbo-2024-04-09 | generation | 338 | 1 | 15.0 | hf: SciCode1/SciCode | SciCode: A Research Coding Benchmark Curated by... |
| W4409361799 | needs_human | gpt-4o-2024-05-13 | classification | 2400 | 1 | 60.0 | url: MathKnowCT | Knowledge Tagging with Large Language Model Bas... |
| W4411080278 | needs_human | gpt-4o-2024-05-13 | generation | 4 | 3 | 15.0 | in_paper: Table 1 of the paper | Temperature-Driven Variability in Emergency Dia... |
| W4411119333 | needs_human | gpt-4-turbo-2024-04-09 | classification | 239 | 3 | 7.0 | github: github.com/mohit3011/Lived-Experience-Not-Found | Lived Experience Not Found: LLMs Struggle to Al... |
| W4411120335 | ready | gpt-4-turbo-2024-04-09 | generation | 109 | 3 | 130.0 | url: gonenhila.github.io/files/semantic_leakage_pr... | Does Liking Yellow Imply Driving a School Bus? ... |
| W4412888091 | needs_download_check | gpt-4-turbo-2024-04-09 | generation | 250 | 3 | 23.0 | github: github.com/csalt-research/LoFTI | LoFTI: Localization and Factuality Transfer to ... |
| W4412889855 | needs_human | gpt-4-turbo-2024-04-09 | extraction | 1000 | 1 | 20.0 | url: RUIE-Bench subset on Google Drive | Towards Robust Universal Information Extraction... |
| W4414580657 | needs_human | o4-mini-2025-04-16 | classification | 6000 | 1 | 90.0 | hf: jiayingwu19/DeceptionDecoded | Seeing Through Deception: Uncovering Misleading... |
| W4415196225 | needs_download_check | gpt-4-turbo-2024-04-09 | classification | 286 | 3 | 9.0 | github: github.com/xiaoyuisrain/humorous-multimodal-m... | Hummus: A Dataset of Humorous Multimodal Metaph... |
| W4416034538 | needs_human | o3-mini-2025-01-31 | generation | 625 | 1 | 30.0 | github: github.com/SUFE-AIFLM-Lab/FinEval-KR | FinEval-KR: A Financial Domain Evaluation Frame... |
| W4416036577 | needs_download_check | gpt-4o-2024-05-13 | classification | 400 | 3 | 6.0 | github: github.com/DanielLin97/ACLR4RUMOR-NAACL2022 | Cross-domain Rumor Detection via Test-Time Adap... |
| W4417257719 | ready | gpt-5-2025-08-07 | classification | 451 | 1 | 85.0 | hf: SakanaAI/EDINET-Bench | EDINET-Bench: Evaluating LLMs on Complex Financ... |
| W7131319772 | ready | gpt-5-mini-2025-08-07 | classification | 1000 | 3 | 5.0 | github: github.com/contentbench/contentbench.github.io | Can Large Language Models Replace Human Coders?... |
| W7135428876 | needs_download_check | gpt-4.1-nano-2025-04-14 | classification | 16483 | 3 | 25.0 | url: DCR systematic drug-class review data | Large Language Models for Biomedical Article Cl... |
| W7140124165 | needs_human | gpt-4-turbo-2024-04-09 | mcq | 3067 | 1 | 46.0 | hf: raia-center/meena | MEENA (PersianMMMU): Multimodal-Multilingual Ed... |
| W7150802891 | needs_human | gpt-4o-2024-05-13 | generation | 3004 | 1 | 60.0 | hf: LouisChen15/ConstructionSite | Are large pre-trained vision language models ef... |
| W7164447524 | needs_download_check | gpt-5-2025-08-07 | generation | 339 | 1 | 30.0 | github: github.com/naver-ai/KCSAT-ML | KCSAT-ML: Probing Reasoning Models with Nationw... |
| W7166808082 | ready | o3-2025-04-16 | generation | 102 | 3 | 25.0 | github: github.com/machine-teaching-group/acl2026-tur... | TURTLEAI: Benchmarking Multimodal Models for Vi... |
| W7166873827 | needs_download_check | o3-mini-2025-01-31 | classification | 1857 | 1 | 85.0 | url: final_reward_data.json on TUdatalib | Reward Modeling for Scientific Writing Evaluation |

## Recurring difficulties

- Gated or unreachable data: three Hugging Face datasets are gated (raia-center/meena manual approval; jiayingwu19/DeceptionDecoded and LouisChen15/ConstructionSite auto-approval that still needs a human to accept terms), the CPSBench anonymous.4open.science link is dead, MathKnowCT has no public release, the Psych-ADR file is not in its repository, and FinEval-KR only released 625 of 9,782 questions. Each of these is a needs_human open point.
- Unlisted few-shot material: five papers print the template but not the demonstrations (data preprocessors, CPS requirements, MathKnowCT agents, RUIE-Bench 10-shot, ConstructionSite 5-shot); the configs use seeded draws or hand-written examples as the binding resolution plans prescribe, so these comparisons are set-level only.
- Execution- or judge-based scoring: RLEF/CodeContests and SciCode need local code execution, ToolBeHonest and TURTLEAI need the benchmarks' released scorers, Safety-J and FinEval-KR need a self-hosted 72B judge, LoFTI/KCSAT-ML/MEENA use the commercial model itself as judge or extractor. The metric definitions are written out, but the judge infrastructure is a human decision.
- Reasoning-model parameters: the o3/o3-mini/o4-mini/GPT-5 papers report temperature 0 or 1 that the API ignores and mostly omit reasoning_effort; configs record the paper value and the assumed API default in params_source.
- Extraction damage was limited and repaired where unambiguous (curly quotes for code fences, a dropped {input} brace in a LongBench prompt, hyphenated line breaks inside XML tags, lost code indentation in the TURTLEAI prompt, Chinese/Japanese prompts kept in the original script).
