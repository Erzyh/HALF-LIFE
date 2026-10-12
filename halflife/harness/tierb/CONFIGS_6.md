# Tier B run configs, group 6 (11 papers)

Source list: `halflife/data/tierb_triage/config_6.csv`. Configs: `halflife/harness/tierb/configs/<wid>.json` (schema in `CONFIG_SCHEMA.md`), hooks: `halflife/harness/tierb/hooks/<wid>.py`. Prompts were copied from the extracted texts in `halflife/external/papers_tierb/`; dataset pages were checked with small HTTP requests and one download (Social Chemistry 101, 27.6 MB). No model API was called and no dataset over 50 MB was downloaded. Date of the checks: 2026-09-19.

## Counts by status

| status | n |
|---|---|
| ready | 3 |
| needs_download_check | 0 |
| needs_human | 8 |
| **total** | **11** |

Estimated API cost of the ready set: **$33** (W4404573318 $29.79 + W7140953907 $2.75 + W4411119985 $0.46, seeds included). The blocked set sums to about **$3,269**, of which $3,000 is W4411119926 alone.

## Configs

| wid | status | model | seeds | task | n_items | est $ | hook | open points | title |
|---|---|---|---|---|---:|---:|---|---|---|
| W4404573318 | ready | gpt-4-turbo-2024-04-09 | 3 | agentic | 500 | 29.79 | yes | turn structure inferred from Figure 1 (system + one user message); "(50%)" gloss dropped when substituting the baseline loan amount | Chat Bankman-Fried: an Exploration of LLM Alignment in Finance |
| W7140953907 | ready | o3-mini-2025-01-31 | 1 | classification | 1000 | 2.75 | yes | none | How Utilitarian Are OpenAI's Models Really? Replicating and Reinterpreting Pfeffer, Krugel, and Uhl (2025) |
| W4411119985 | ready | gpt-4-turbo-2024-04-09 | 3 | classification | 100 | 0.46 | yes | none | How Inclusively do LMs Perceive Social and Moral Norms? |
| W4401246245 | needs_human | gpt-4o-2024-05-13 | 3 | generation | 20 | 0.42 | no | human expert judge: the 0/1/2 score comes from two radiologists with 20+ years' experience; the run itself prepares and renders correctly | Imaging protocol suggested by large language model depends on language: preliminary experiments using GPT-4 |
| W4416034780 | needs_human | gpt-4-turbo-2024-04-09 | 3 | mcq | 120 | 0.47 | no | context-dependent cell is a sequential dialogue carrying the model's own prior answers; TAR is cross-run agreement, not a per-item score | CAPE: Context-Aware Personality Evaluation Framework for Large Language Models |
| W7163878229 | needs_human | gpt-4.1-nano | 3 | classification | 38 | 1.00 | no | only the D-category prompt is printed (I/R/E/S in Supplementary File 1); the 38 TM1 pathway terms and their Enrichr scores are not listed | The quantified immune-aging dysregulation index: an LLM-powered method for annotating and quantifying systems-level dysregulation |
| W4409361695 | needs_human | gpt-4-turbo-2024-04-09 | 3 | agentic | 180 | 12.00 | no | the whole appendix is missing from the extracted camera-ready (agent prompt, 6 instructions, judge prompt); items are the authors' own simulation output | Multi-Agent Security Tax: Trading Off Security and Collaboration Capabilities in Multi-Agent Systems |
| W4416034996 | needs_human | gpt-4.1-nano-2025-04-14 | 3 | generation | 1888 | 25.00 | no | solve-time prompt not printed (only the data-generation prompts); Pass@1 needs unit-test execution in six languages | Turning the Tide: Repository-based Code Reflection |
| W4414981059 | needs_human | o3-2025-04-16 | 1 | other | 1725 | 80.00 | no | image input (runner is text-only); the 1,725-image sample and the six few-shot examples are not identified; images exceed the 50 MB limit | Benchmark It Yourself (BIY): Preparing a Dataset and Benchmarking AI Models for Scatterplot-Related Tasks |
| W4404352845 | needs_human | gpt-4-turbo-2024-04-09 | 1 | agentic | 632 | 150.00 | no | live RapidAPI tool calls over up to 24 steps; baseline ReAct prompt and ToolBench judge prompts both unprinted | EcoAct: Economic Agent Determines When to Register What Action |
| W4411119926 | needs_human | gpt-4-turbo-2024-04-09 | 1 | classification | 246330 | 3000.00 | no | 246,330 judge calls (~$3,000) for one cell; metric is a set-level Spearman of a Bradley-Terry ranking against a 2024-07-30 Chatbot Arena snapshot | Re-evaluating Automatic LLM System Ranking for Alignment with Human Preference |

## The three ready configs

All three were verified with `python tierb_runner.py <wid> --prepare --dry-run --cap 20` from `halflife/harness`, and the first rendered item in `runs/tierb/<wid>/items.jsonl` was read back against the paper.

- **W7140953907** (trolley dilemma). The single prompt of Sec. 2.1 is sent 1,000 times, exactly as the paper does; the hook emits the 1,000 items and implements the paper's four-way Pfeffer-matched classifier (Sec. 2.3, S4.2), with gold "Yes" on every item so that accuracy is the reported Yes% of 100.0 (Table S1). The paper is itself a drift measurement - it reports a 30.3% GPT-4o Yes rate against Pfeffer et al.'s 41.5% on the same snapshot and prompt, and a drop from 30% to 14% over nine days - so the o3-mini cell is a useful control at the ceiling.
- **W4411119985** (social and moral norms). The Social Chemistry 101 release was downloaded (27.6 MB zip, sha256 `ebaa5242...`) and the item set verified before any call: the `m == 50` / `split == analysis` rows are exactly 400 RoTs, 100 in each of the four sources, 50 annotations each, which is the subset Sec. 2 describes. The hook aggregates the 50 `rot-agree` values into the Eq. 1 consensus (mode, mean of tied values per Appendix B.2) and maps the answer letter to the 0-4 score, so `mean_abs_error` is ADA-Met. Worth knowing before reading the result: the CONF consensus is concentrated at "75-90%", so a model that always answers C scores 0.91 against the paper's 0.92, and D-everywhere would score 0.27.
- **W4404573318** (Chat Bankman-Fried). The Appendix A.1 prompts with every Table 3 pressure variable at its baseline value; the hook emits 500 identical runs (the paper's own N) and maps the required `Decision: (N)` marker to aligned/misaligned per Sec. 4.2, so accuracy is the misalignment rate of 0.41. Three seeds means three complete replications of the paper's 500-run baseline, directly comparable with its SE of 0.02. This is the one cell in the group where the original is a sampling distribution rather than a point estimate, because the paper's own default is temperature 1. At `--cap 20` the runner trims to 335 items, which would shrink each replication below N = 500; the recorded estimate is the uncapped $29.79 (the battery's own line prints $47.79 because it charges the full `max_tokens`).

## Recurring difficulties

- **Prompts that exist but are not in the paper text (4 papers).** W4409361695's entire appendix is absent from the extracted AAAI camera-ready (it is in arXiv:2502.19145); W7163878229 prints one of five category prompts and leaves the rest in Supplementary File 1; W4416034996 prints its data-generation prompts but never the solve-time prompt whose format compliance it scores; W4404352845 prints EcoAct's own prompt but the claim is the vanilla-ReAct baseline, whose prompt is ToolBench's. In every case the missing text is public somewhere, so these are retrievable rather than lost - but not copyable from what we hold.
- **Metrics that are not per-item scores (4 papers).** CAPE's TAR is agreement across three runs, W7163878229's Bias of the Mean compares a workflow-level aggregate with the author's own manual reference, W4411119926's Spearman rho needs a Bradley-Terry fit and a dated leaderboard snapshot, and W4401246245's 0/1/2 rubric is assigned by two radiologists. The runner scores each seed independently against per-item gold, which none of these four can be expressed as.
- **Protocols the batch runner cannot execute (4 papers).** Sequential dialogue carrying the model's own answers (CAPE), live third-party REST APIs over 24 steps (EcoAct), unit-test execution in six languages (LiveRepoReflection), and image inputs (BIY). The image case is the one worth treating as an infrastructure decision rather than a per-paper refusal: a hook that emits image content parts, like the Tier A TURTLEAI adapter, would unlock several cells here and probably other multimodal Tier B papers.
- **One cost blocker.** W4411119926's claim cell is base pairwise over the full data, which Appendix E prices at m*n*(n-1) = 805 x 18 x 17 = 246,330 judge calls, on the order of $3,000 for a single number. Cheaper cells exist in the same table (pairwise_base_ref 13,685 calls, rho 0.9071; pointwise 14,490 calls, rho 0.8611), but substituting one changes which claim is checked and is a scoping decision.
- **Data availability was rarely the problem.** Nine of the eleven item sources are public and were confirmed reachable: Social Chemistry 101 (downloaded), the MPI-120 inventory, the LiveRepoReflection benchmark (Apache-2.0, 1,888 tasks matching Table 3's language counts), the BIY dataset and pipeline (Apache-2.0, 18,921 images and metadata), and the self-contained prompt sets of the trolley, Bankman-Fried and imaging papers. Nothing in this group is gated. That is why the status split is 3 ready / 0 needs_download_check / 8 needs_human rather than the usual spread - the blockers here are protocol and scoring, not access.
- **Two near-ceiling cells.** o3-mini's trolley Yes% is 100.0 and o3's cluster-counting MAE is 0.03, so any deviation on re-execution can only go one way. Worth flagging when these are read alongside two-sided cells.
