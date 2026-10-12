# Tier B run configs, group 4 (31 papers)

Source list: `halflife/data/tierb_triage/config_4.csv`. Configs: `halflife/harness/tierb/configs/<wid>.json` (schema in `CONFIG_SCHEMA.md`).

## Counts by status

| status | n |
|---|---|
| ready | 12 |
| needs_download_check | 12 |
| needs_human | 7 |
| **total** | **31** |

Total estimated API cost: **~$1,560** (sum of est_usd; seeds already included).

## Configs

| wid | status | model | task | n_items | seeds | est_usd | items source | title |
|---|---|---|---|---:|---:|---:|---|---|
| W4399404161 | ready | gpt-4-turbo-2024-04-09 | mcq | 12032 | 1 | 420 | hf:TIGER-Lab/MMLU-Pro | MMLU-Pro: A More Robust and Challenging Multi-Task |
| W4399912745 | needs_download_check | gpt-4-turbo-2024-04-09 | generation | 948 | 1 | 15 | hf:princeton-nlp/ALCE-data | ALiiCE: Evaluating Positional Fine-grained Citatio |
| W4402345509 | ready | gpt-4-turbo-2024-04-09 | mcq | 199 | 3 | 9 | hf:futurehouse/lab-bench | LAB-Bench: Measuring Capabilities of Language Mode |
| W4403347060 | needs_human | gpt-4-turbo-2024-04-09 | classification | 800 | 3 | 290 | hf:UTSNLPGroup/TheraPhase | Multi-Session Client-Centered Treatment Outcome Ev |
| W4403570177 | needs_download_check | gpt-4o-2024-05-13 | classification | 10067 | 1 | 120 | github:Zhou-Zoey/RMB-Reward-Model-Benchmark | RMB: Comprehensively Benchmarking Reward Models in |
| W4403851744 | needs_human | gpt-4-turbo-2024-04-09 | generation | 1667 | 1 | 100 | hf:bio-nlp-umass/MedQA-CS-Student | MedQA-CS: Objective Structured Clinical Examinatio |
| W4403885480 | needs_human | gpt-4o-2024-05-13 | other | 70 | 1 | 2 | Table 3 | AutoML-Agent: A Multi-Agent LLM Framework for Full |
| W4404470015 | needs_human | gpt-4-turbo-2024-04-09 | classification | 100 | 3 | 5 | ROCOv2 | Comparative Performance of Claude and GPT Models i |
| W4404782330 | needs_human | gpt-4o-2024-05-13 | other | 200 | 1 | 45 | hf:chenxwh/AVeriTeC | Multi-hop Evidence Pursuit Meets the Web: Team Pap |
| W4404783148 | needs_download_check | gpt-4-turbo-2024-04-09 | mcq | 1240 | 3 | 45 | hf:zhehuderek/VIVA_Benchmark_EMNLP24 | VIVA: A Benchmark for Vision-Grounded Decision-Mak |
| W4404985489 | needs_download_check | gpt-4-turbo-2024-04-09 | extraction | 556 | 1 | 75 | github:mitdbg/scivar | Variable Extraction for Model Recovery in Scientif |
| W4405425991 | needs_download_check | o3-mini-2025-01-31 | generation | 1025 | 3 | 31 | github:OviaLabs/ProteinGPT | ProteinGPT: Multimodal LLM for Protein Property Pr |
| W4406058598 | ready | gpt-4o-2024-05-13 | classification | 1238 | 3 | 30 | github:GAIR-NLP/factool | Halu-J: Critique-Based Hallucination Judge |
| W4407571428 | needs_download_check | gpt-4-turbo-2024-04-09 | mcq | 200 | 3 | 12 | hf:ShunchiZhang/PhysiCo | The Stochastic Parrot on LLM's Shoulder: A Summati |
| W4410417118 | needs_human | gpt-4.1-nano-2025-04-14 | classification | 450 | 1 | 1 | 45 validated case vignettes from Kopka et al. | ChatGPT Is Still Not Good Enough at Giving Care-Se |
| W4411119263 | needs_download_check | gpt-4o-2024-05-13 | classification | 1030 | 3 | 40 | hf:yale-nlp/ReIFE | ReIFE: Re-evaluating Instruction-Following Evaluat |
| W4411120327 | needs_human | gpt-4-turbo-2024-04-09 | mcq | 175 | 3 | 8 | github:VenkyMishra/Legal-Reasoning | Investigating the Shortcomings of LLMs in Step-by- |
| W4412887844 | needs_download_check | gpt-4-turbo-2024-04-09 | classification | 3339 | 1 | 27 | hf:MichiganNLP/Chumor | Chumor 2.0: Towards Better Benchmarking Chinese Hu |
| W4412889033 | needs_download_check | gpt-4-turbo-2024-04-09 | classification | 50 | 3 | 2 | github:stefanolocci/Character-Role-Narrative- | Applying the Character-Role Narrative Framework wi |
| W4414494504 | needs_download_check | gpt-4-turbo-2024-04-09 | mcq | 225 | 3 | 7 | hf:Wellytics/PGxRAG | PGxRAG: A Retrieval Augmented Generation supported |
| W4415035710 | ready | gpt-4-turbo-2024-04-09 | generation | 158 | 3 | 10 | hf:SonalPrabhune/RealWorldQuestioning | Do LLMs have a Gender (Entropy) Bias? |
| W4416034345 | ready | o3-mini-2025-01-31 | generation | 978 | 1 | 20 | hf:ipst/slds | Unlocking Legal Knowledge: A Multilingual Dataset  |
| W4416035547 | needs_download_check | o4-mini-2025-04-16 | classification | 100 | 3 | 6 | hf:EleutherAI/hendrycks_math | Agent-to-Agent Theory of Mind: Testing Interlocuto |
| W4416339332 | ready | o3-mini-2025-01-31 | classification | 66 | 3 | 3 | github:concistency/Nation-Level_Bias | "As Eastern Powers, I will veto." : An Investigati |
| W7117377764 | ready | o3-2025-04-16 | extraction | 43 | 3 | 7 | github:ryanmio/colonial-virginia-llm-geolocat | Benchmarking large language models for geolocating |
| W7135428702 | ready | gpt-4.1-nano-2025-04-14 | mcq | 1024 | 3 | 2 | hf:sommify/sommbench | SommBench: Assessing Sommelier Expertise of Langua |
| W7140099019 | ready | o4-mini-2025-04-16 | other | 601 | 3 | 27 | hf:hiyouga/geometry3k | When Does Auxiliary Modality Matter in Solving Geo |
| W7144391352 | needs_download_check | gpt-5-2025-08-07 | mcq | 279 | 3 | 25 | github:jhCOR/CALRKBench | CALRK-Bench: Evaluating Context-Aware Legal Reason |
| W7161421448 | ready | gpt-4-turbo-2024-04-09 | generation | 5000 | 1 | 150 | Methods: the ten situations and the two promp | Identifying implicit bias in LLM-based chat AI tow |
| W7166799942 | ready | gpt-4.1-nano-2025-04-14 | classification | 2610 | 3 | 1 | github:declare-lab/MELD | CMTD: Cognitive Modeling with Traits and Distortio |
| W7166852552 | ready | gpt-4.1-nano | mcq | 8385 | 3 | 25 | hf:QwenQKing/LexGenius | LexGenius: An Expert-Level Benchmark for Large Lan |

## needs_human, one line each

- W4403347060: <Format Instructions> and the SCL-90 item list of the two-step prompt must be authored; reference-score file identity to confirm
- W4403851744: Diagnosis-score denominator and the InfoGatherQA examiner configuration behind Table 3 are not printed; examiner snapshot to confirm
- W4403885480: execution-based success rate needs a runtime with 14 datasets (Kaggle), six unprinted skeleton scripts and manual 0/0.5/1 grading; decoding unstated
- W4404470015: 100 ROCOv2 images must be sampled and manually screened, CUIs mapped to Table 1 regions, and a region-synonym scoring rule fixed
- W4404782330: live Google search + trafilatura pipeline and the official AVeriTeC scorer must be provisioned; max questions per claim not printed
- W4410417118: the 45 vignettes and gold labels live in two other Kopka papers' supplements; free-text-to-urgency classifier prompt not printed; decoding unstated
- W4411120327: the Civ. Pro. dataset is released only on request (trusthlt terms); repository prompt adds a 'Task:' sentence the paper omits

## Recurring difficulties

- Decoding parameters are missing in 18 of 31 papers; the schema default (temperature 0) contradicts designs that rely on sampling (AutoML-Agent's five-run std, the care-seeking paper's ten trials), and o-series/GPT-5 models ignore the temperature/seed the authors requested (SLDS, UNSC, CALRK). These are flagged per config rather than silently defaulted.
- Prompts printed as tables or figures lose their slot syntax: placeholders had to be reconstructed for elided documents (ALiiCE), colour-coded template variants (scivar), schematic figure text (Agent ToM target prompt, legal reasoning), and two-step pipelines whose <...> slots are never instantiated (TheraPhase). Multi-block prompts (MedQA-CS sections, Papelo functions, SommBench languages) are stored under '###' headers in one user_template.
- Item files could rarely be inspected: parquet/JSON column names are unverified for 12 configs (needs_download_check), and four sources are gated, oversized or private (Chumor login, ALCE 451 MB tar, ROCOv2 861 MB, Civ. Pro. on request, Zenodo corpus restricted). GitHub's unauthenticated API quota (60/h) ran out midway; raw README and tree-page fetches were used instead.
- Several claimed numbers are set-level only: the paper's subset is unlisted or private (LAB-Bench 20% private split, ROCOv2 100-image sample, ProteinGPT 35-protein sample, Agent ToM 100 random MATH items) or depends on drifting resources (web search, image URLs on Pinterest), so item-level comparison is impossible and the configs say so in task.approximation.
- Metric definitions leave aggregation choices open (F1 micro vs macro for character categorization, pooled vs per-chunk F1 for scivar, how three repetitions become one weighted F1 for UNSC, order handling for pairwise judges in RMB/ReIFE); defaults are recorded in approximation/notes and only the blocking ones appear in open_points.
