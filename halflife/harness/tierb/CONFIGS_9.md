# Tier B run configs, group 9 (11 papers)

Source list: `halflife/data/tierb_triage/config_9.csv`. Configs written to `halflife/harness/tierb/configs/<wid>.json` following `CONFIG_SCHEMA.md`. Prompts were copied from the extracted texts in `halflife/external/papers_tierb/`; dataset pages were checked with small HTTP requests and, where a file was small enough, a direct download into `halflife/external/data/tierb_items/<wid>/` (nothing over 50 MB was fetched, no model API was called, no author was contacted). Date of the checks: 2026-09-19.

## Counts by status

| status | n |
|---|---|
| ready | 1 |
| needs_download_check | 0 |
| needs_human | 10 |
| **total** | **11** |

Total estimated API cost if every config were unblocked and run as written: **~$1,232** (seeds included; dominated by the two agentic papers, W7164700917 ~$900 and W4412945594 ~$150). The one ready config costs **$1.64** at the runner's own `--prepare --dry-run` estimate.

## Configs

| wid | status | model | seeds | task | n_items | est $ | hook | open points | title |
|---|---|---|---:|---|---:|---:|:--:|---|---|
| W7106207151 | ready | gpt-4-turbo-2024-04-09 | 3 | classification | 54 | 1.6 | no | empty-narrative row scored differently from the authors (1/54) | Syn-STARTS: Synthesized START Triage Scenario Generation Framework |
| W4404261042 | needs_human | gpt-4-turbo-2024-04-09 | 3 | generation | 26 | 35 | no | proverb database not released; error rate is a human annotation | A Statistical Analysis of LLMs' Self-Evaluation Using Proverbs |
| W4413735524 | needs_human | gpt-4-turbo-2024-04-09 | 3 | other | 60 | 20 | no | no prompt printed (repo only); human visual scoring; CAD toolchain | From text to design: LLM agents for automated CAD generation |
| W4396820880 | needs_human | gpt-4-turbo-2024-04-09 | 3 | extraction | 115 | 25 | no | baseline prompt not printed; test split not enumerated; MSE not a runner metric | ECC Analyzer: Extract Trading Signal from Earnings Conference Calls |
| W4404782977 | needs_human | gpt-4-turbo-2024-04-09 | 3 | classification | 194 | 12 | no | released csv is the raw screening pool, not the 194-post gold; codebook rows lost in extraction | The Computational Anatomy of Humility |
| W4412945367 | needs_human | o4-mini-2025-04-16 | 3 | generation | 100 | 4 | no | claim cell is a human Likert average; judge prompts missing from Appendix B | AbGen: Evaluating LLMs in Ablation Study Design and Evaluation |
| W7166871080 | needs_human | gpt-4.1-nano-2025-04-14 | 3 | classification | 100502 | 7 | no | HF dataset gated (auto-approval): a human must accept the terms once | 100,000+ Movie Reviews from Kazakhstan |
| W4409363352 | needs_human | gpt-4-turbo-2024-04-09 | 1 | other | 1970 | 65 | no | appendix with Figures 6-7 absent from our text; epsilon-CAUSAL not located | Nuance Matters: Probing Epistemic Consistency in Causal Reasoning |
| W4412945594 | needs_human | gpt-4o-2024-05-13 | 1 | other | 300 | 150 | no | SWE-agent scaffold prompts not printed; container + multi-turn rollouts | LocAgent: Graph-Guided LLM Agents for Code Localization |
| W7204104731 | needs_human | gpt-5-mini-2025-08-07 | 3 | classification | 798 | 13 | no | human label file not released and the paper_id ordering is unrecoverable | Using Human-LLM Disagreement to Improve Checklist-Based Quality Appraisal |
| W7164700917 | needs_human | gpt-5-2025-08-07 | 1 | other | 199 | 900 | no | harness not released; 4.43 GB split; recursive multi-agent architecture | Recursive Agent Harnesses |

Items sources, for reference: W7106207151 github `seitalab/Syn-STARTS` (`datasets/TRIAGE/triage_questions_adult.csv`); W4404261042 in_paper (Table 2, illustrative only); W4413735524 github `R-SMP/text-to-design`; W4396820880 github `GeminiLn/EarningsCall_Dataset`; W4404782977 github `xiaobo-guo/The-Computational-Anatomy-of-Humility-...`; W4412945367 url `huggingface.co/datasets/yale-nlp/AbGen/resolve/main/validation.json`; W7166871080 hf `yeshpanovrustem/100k_movie_reviews_from_kz` (gated); W4409363352 unresolved (epsilon-CAUSAL); W4412945594 hf `princeton-nlp/SWE-bench_Lite`; W7204104731 url `osf.io/download/65vyt/` (43.3 MB prompt batch) plus `osf.io/vw3t7`; W7164700917 hf `oolongbench/oolong-synth` (deliberately not machine-readable, see below).

## The one ready config

**W7106207151 (Syn-STARTS)** verified end to end. The authors' repository carries the 54-row `triage_questions_adult.csv` with exactly the `{Green 18, Yellow 11, Red 22, Black 3}` distribution of Sec. 4.1, and the three prompt fragments printed as Figure 10 live in `run_tasks/prompts/{triage_context,triage_syntax_variations,formatting_prompts}.json`, which fixes the system/user split, the insertion point of the patient narrative and the decoding parameters (temperature 0.0, max_tokens 200) that the paper itself never states. Scoring the authors' own released per-item file with the label map Green=MINOR, Yellow=DELAYED, Red=IMMEDIATE, Black=EXPECTANT/DECEASED reproduces the published cell exactly: 39/54 = 0.7222 vs the reported 0.72. `--prepare --dry-run --cap 20` renders all 54 items (162 requests, $1.64) and the first rendered prompt matches Figure 10.

## Recurring difficulties in this group

- **Human-in-the-loop metrics (4 papers).** The claim cell is a human judgement in W4404261042 (two annotators decide whether a Siegal-Tukey rejection contains a real scoring failure), W4413735524 (binary visual inspection of generated CAD geometry), W4412945367 (expert Likert ratings) and, indirectly, W7204104731 (agreement against expert labels). Re-running the model produces new outputs that would need new raters; none of these can be closed by better engineering.
- **Prompt not printed (4 papers).** W4396820880 never gives the wording of its direct-volatility baseline; W4413735524's Appendix A is a bare repository link; W4412945594 relies on third-party agent scaffolds it does not reprint; W4409363352's AAAI text in `external/papers_tierb/` stops at the references, so Figures 6-7 are missing (they are in the extended arXiv version 2409.00103, and the released repository never got the generation/ranking scripts its README documents).
- **Released data is not the evaluated data (2 papers).** W4404782977 publishes the 1,412-post screening pool with in-progress annotator columns rather than the cleaned 350/194-post gold standard. W7204104731 publishes the rendered prompts (43.3 MB batch JSONL, retrieved context frozen), the model outputs and the result CSVs, but not `eval/human_labels/ptsd.csv`; its `paper_id` values are the bare file names `0..37`, so the mapping to the 38 PTSD studies is gone. The original human ratings do exist (OSF `vw3t7`, "Appendix C - screening papers with GRoLTS - final.xlsx", 38 rows x 21 items, and the item-to-column mapping was recovered) but scoring the authors' own gpt-5-mini answers against them in row order gives 0.665 instead of the reported 0.75, and matches their per-item values exactly only where the gold is near-constant - i.e. the columns are right and the row order is a permutation that only a human can supply.
- **Access and size limits (2 papers).** `yeshpanovrustem/100k_movie_reviews_from_kz` is gated with auto-approval (anonymous reads 401, token reads 403), so a human has to accept the terms once before W7166871080 can prepare. `oolongbench/oolong-synth`'s validation split is 4.43 GB; `items.hf` is left unset on purpose in W7164700917 so that `--prepare` cannot start a download above the 50 MB rule, with the hub id parked under `items.hf_paper`.
- **Architectures the runner cannot express (3 papers).** W4409363352 needs two dependent calls per item (generate ten intermediates, then rank them) plus a Kendall-tau scorer; W4412945594 needs a containerised repository checkout and tens of tool-calling turns per instance; W7164700917 spawns thousands of subagent harnesses per instance with filesystem and shell access. Each would need a hook at least, and the last two need a sandbox that does not exist here. No hook was written in this group: every candidate is blocked upstream by a missing prompt, missing gold or missing code, so a hook would encode guesses.
- **Reasoning-model parameters.** W4412945367 (o4-mini), W7204104731 (gpt-5-mini) and W7164700917 (gpt-5) report a temperature the API ignores; the configs record the paper's value in `params_source` and raise `max_tokens` (4096 / 4096 / 8192) so hidden reasoning tokens have room.
- **Claim-cell wording corrected once.** The triage row for W4396820880 reads 2.198 as a "1-day horizon" MSE; in Table 1 the first column is the overall average MSE and the horizon-specific values begin at MSE_3 = 3.187. The config records the Table 1 first column and notes the discrepancy.
- **Recovered links.** The dataset link of W4404782977, lost in the text extraction as the anchor "Dataset", was recovered from the PDF link annotations of `aclanthology.org/2024.emnlp-main.327.pdf`: `github.com/xiaobo-guo/The-Computational-Anatomy-of-Humility-Modeling-Intellectual-Humility-in-Online-Public-Discourse`.
