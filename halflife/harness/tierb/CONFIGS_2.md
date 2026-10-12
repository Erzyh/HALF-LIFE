# Tier B run configs, group 2 (32 papers)

Written from `halflife/data/tierb_triage/config_2.csv` into `halflife/harness/tierb/configs/<wid>.json` following `CONFIG_SCHEMA.md`.

## Counts by status

- ready: 17
- needs_download_check: 4
- needs_human: 11
- total estimated cost: $1,501.2 (seeds included; CFinBench alone is $800 for one full-test-split seed)

## Configs

| wid | status | model | task | n_items | seeds | est_usd | items source | title |
|---|---|---|---|---:|---:|---:|---|---|
| W4397048985 | needs_human | gpt-4o-2024-05-13 | classification | 210 | 1 | 8.0 | URL: HAM10000 | Many-Shot In-Context Learning in Multimodal Founda |
| W4399911213 | ready | gpt-4-turbo-2024-04-09 | classification | 240 | 3 | 15.0 | HF: ibm-research/Wikipedia_contradict_benchmark | WikiContradict: A Benchmark for Evaluating LLMs on |
| W4400434899 | ready | gpt-4-turbo-2024-04-09 | other | 800 | 3 | 12.0 | in paper: Technical Appendix B: BASE PROMPT | Are Large Language Models Strategic Decision Maker |
| W4402952718 | needs_human | gpt-4-turbo-2024-04-09 | other | 900 | 3 | 54.0 | URL: figshare private share link https://figshare.... | Evaluating Large Language Models on Spatial Tasks: |
| W4403443823 | needs_download_check | gpt-4-turbo-2024-04-09 | classification | 3736 | 1 | 45.0 | GitHub: github.com/rmatouschekh/science-is-exploration | Science is Exploration: Computational Frontiers fo |
| W4403758464 | ready | gpt-4-turbo-2024-04-09 | other | 600 | 3 | 22.0 | GitHub: karthikv792/LLMs-Planning | LLMs Still Can't Plan; Can LRMs? A Preliminary Eva |
| W4403882451 | ready | gpt-4-turbo-2024-04-09 | other | 600 | 3 | 22.0 | GitHub: karthikv792/LLMs-Planning | Planning in Strawberry Fields: Evaluating and Impr |
| W4404342216 | needs_human | o3-mini-2025-01-31 | classification | 4196 | 1 | 80.0 | HF: Reza8848/AAAR-1.0 | AAAR-1.0: Assessing AI's Potential to Assist Resea |
| W4404781158 | ready | gpt-4-turbo-2024-04-09 | mcq | 300 | 3 | 9.0 | GitHub: DojunPark/MultiPragEval | MultiPragEval: Multilingual Pragmatic Evaluation o |
| W4404782525 | ready | gpt-4o-2024-05-13 | classification | 500 | 3 | 7.5 | HF: bigbio/pubmed_qa | Characterizing LLM Abstention Behavior in Science  |
| W4404792825 | needs_download_check | gpt-4o-2024-05-13 | other | 10 | 3 | 0.2 | URL: General Self-Efficacy Scale | Will LLMs Sink or Swim? Exploring Decision-Making  |
| W4404990976 | needs_download_check | gpt-4-turbo-2024-04-09 | mcq | 50 | 3 | 3.0 | URL: https://media.set.or.th/set/Documents/2022/Ap... | Thai Financial Domain Adaptation of THaLLE -- Tech |
| W4405768494 | needs_human | gpt-4-turbo-2024-04-09 | classification | 3339 | 1 | 35.0 | HF: MichiganNLP/Chumor | Chumor 2.0: Towards Benchmarking Chinese Humor Und |
| W4406880877 | ready | o1-2024-12-17 | classification | 300 | 1 | 45.0 | GitHub: jenna-russell/human_detectors | People who frequently use ChatGPT for writing task |
| W4410110677 | ready | o1-2024-12-17 | classification | 250 | 1 | 38.0 | GitHub: windisch-paul/positive_negative | Large Language Models for Supporting Clear Writing |
| W4411112894 | ready | gpt-4-turbo-2024-04-09 | classification | 3121 | 3 | 94.0 | HF: mediabiasgroup/BABE | The Promises and Pitfalls of LLM Annotations in Da |
| W4411119490 | ready | gpt-4-turbo-2024-04-09 | classification | 3000 | 1 | 30.0 | HF: edinburgh-dawg/mmlu-redux | Are We Done with MMLU? |
| W4411120358 | needs_download_check | gpt-4-turbo-2024-04-09 | mcq | 79280 | 1 | 800.0 | GitHub: yanbinwei/CFinBench-Eval | CFinBench: A Comprehensive Chinese Financial Bench |
| W4412888118 | ready | gpt-4o-2024-05-13 | mcq | 31 | 3 | 0.5 | HF: koreankiwi99/Nunchi-Bench | Nunchi-Bench: Benchmarking Language Models on Cult |
| W4412944528 | needs_human | gpt-4o-2024-05-13 | mcq | 1650 | 3 | 25.0 | GitHub: chenjux/AFCE | Do Language Models Mirror Human Confidence? Explor |
| W4414758400 | ready | gpt-4-turbo-2024-04-09 | generation | 600 | 3 | 8.0 | in paper: Appendix A.1 Table 4: the 25 BLS Occupational... | Mitigation of Gender and Ethnicity Bias in AI-Gene |
| W4416033907 | needs_human | gpt-4.1-nano-2025-04-14 | mcq | 594 | 3 | 4.0 | HF: tau/commonsense_qa | Challenging the Evaluator: LLM Sycophancy Under Us |
| W4416034777 | ready | gpt-4-turbo-2024-04-09 | other | 100 | 3 | 3.0 | in paper: Sec. 4.2 prompt box | The Illusion of Randomness: How LLMs Fail to Emula |
| W4416037849 | needs_human | o3-mini-2025-01-31 | classification | 2800 | 3 | 24.0 | HF: zhm0/CRAB | CRAB: A Benchmark for Evaluating Curation of Retri |
| W4417438236 | needs_human | gpt-5-2025-08-07 | classification | 100 | 3 | 20.0 | URL: MRNet | Evaluating Multimodal Large Language Model (LLM) ( |
| W7134094238 | ready | gpt-4o-2024-05-13 | generation | 30 | 3 | 0.5 | in paper: Appendix A.1 Neutral Prior Prompt | BioLLMAgent: A Hybrid Framework with Enhanced Stru |
| W7139147531 | ready | gpt-4.1-nano-2025-04-14 | classification | 120 | 3 | 0.3 | GitHub: FutureTech-OB/ai-taste | LLMs learn scientific taste from institutional tra |
| W7140138327 | ready | gpt-5-mini-2025-08-07 | mcq | 1259 | 3 | 19.0 | HF: disi-unibo-nlp/ReMedQA | ReMedQA: Are We Done With Medical Multiple-Choice  |
| W7155245470 | needs_human | gpt-5-mini-2025-08-07 | classification | 1281 | 3 | 60.0 | URL: HealthBench | Same Verdict, Different Reasons: LLM-as-a-Judge an |
| W7164447651 | needs_human | o3-mini-2025-01-31 | classification | 295 | 1 | 15.0 | URL: tau2-bench leaderboard runs published by Sierra | From Confident Closing to Silent Failure: Characte |
| W7166808309 | ready | gpt-4.1-nano-2025-04-14 | classification | 381 | 3 | 2.0 | HF: yuriilaba/ukrainian-visual-wsd-benchmark | From Sparse to Sense-Grounded: Wikipedia Training  |
| W7167154566 | needs_human | gpt-4.1-nano-2025-04-14 | classification | 151 | 3 | 0.2 | GitHub: bodenmoraski/Illusion-Project-Home-Repo | Anthropomorphism in AI Companion Communities: Age, |

## needs_human, first open point each

- W4397048985: The demo-set size behind 'Best' (53.59) for HAM10000/GPT-4o is only in Figure 7 (image); read it from the PDF or the authors' code release before the run.
- W4402952718: Choose and fix the LLM judge model for the subjective and code items (the run is only defined once the judge is fixed; gpt-4.1-2025-04-14 is a placeholder).
- W4404342216: Transcribe the EQINFER model-prediction prompt from Figure 11 of the PDF (the extraction holds only the caption).
- W4405768494: The Hugging Face dataset MichiganNLP/Chumor is gated: a human must request and obtain access, then confirm the test.tsv column names and the label encoding.
- W4412944528: The Vanilla prompt is not printed in the paper (only a quoted phrase); decide whether to run the code-release template given above (deviates from the 'printed prompt only' rule) or to switch the claim to the AFCE row (AvE 13.8, prompts printed in Table 7: 10 questions per call plus a separate 0-10 estimate call).
- W4416033907: Choose the challenger model(s) used to rebuild the disagreement pairs (paper: random challenger among seven other models of Table 9; proposal: gpt-4.1-2025-04-14, gpt-4.1-mini-2025-04-14, gpt-4o-mini-2024-07-18 with the same turn-1 template, drawn from correct responders when the target is wrong).
- W4416037849: The resolution plan speaks of '400 English queries' but en_data.jsonl holds 100 queries (100 per language, 400 in total, Table 1); decide whether Table 7 is compared on all 400 queries (as C.1.2 states) or on the 100 English ones.
- W4417438236: A human must register for MRNet (Stanford AIMI) and accept its research-use agreement before the validation set can be downloaded (~5.8 GB).
- W7155245470: The 1,281-conversation subset is not released: decide whether to reproduce the App. B.2 pipeline (langid, heuristic HCP tags, Llama-3.1-8B-Instruct few-shot HCP classifier of Table 3) or to approximate it with the metadata-only filters; the count will differ.
- W7164447651: Rebuild the corpus: locate the public leaderboard trajectory files for the 8 model families, confirm their message format, apply the Appendix A regexes and check that the FS/HF/ambiguous proportions are close to the paper's 616/753/361.
- W7167154566: Fix the kappa definition: the paper attaches kappa 0.58 to the within-one agreement sentence; an unweighted 5-class kappa at 64% exact agreement would be lower, so a weighted (linear) or within-one-collapsed kappa is likely - resolve from the repository's validation script (scripts/validate_paper_statistics.py does not compute kappa) or choose and state the weighting.

## Recurring difficulties

- Prompts that live in figures or code, not in the text: AAAR-1.0's EQINFER prompt is an image (nothing to copy), MMLU-Redux and AFCE print only the instruction block while the input layout or the whole Vanilla template sits in the code release, CRAB and the tau2-bench judge print the instruction but not how references or trajectories are rendered.
- Item sets that are the authors' own draws or need a pipeline: ManyICL's 805/210 HAM10000 split, the sycophancy disagreement pairs, the 295 tau2-bench judge trajectories, the 1,281 HealthBench conversations (langid + Llama HCP classifier + GPT-4.1 ground truth), the 100 MRNet cases; these are configured as seeded re-draws with set-level comparison and flagged.
- Access barriers: MichiganNLP/Chumor is gated, MRNet needs registration, the spatial-task benchmark is a private figshare link, TroFi's home page blocks automated requests, and the GitHub API rate limit blocked directory listings (worked around with raw files and HTML listings).
- Claims whose numbers do not line up with the released data: the CRAB plan speaks of 400 English queries but the English file has 100 (400 = all four languages); the AFCE 'AvE' 33.2 is not the mean of the nine printed ECEs; Table 1 of the game-theory paper pools 800 runs behind an n=100 claim.
- Human scoring replaced by rules or an LLM judge (spatial tasks WA, MultiPragEval option extraction, story gender coding) and stochastic statistics at temperature 1 (game-theory label frequency, RPS TVD, GSE totals) where 'seeds' are repeated draws rather than replicates of a deterministic run.
