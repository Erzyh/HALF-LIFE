# NORMALIZE_3: machine fields for the 27 configs of normalize_3.csv (2026-09-07)

Runner: `python harness/tierb_runner.py <wid> --prepare --dry-run --cap 100000` (no API calls; cap raised so the full item set is prepared).
Every config keeps its prose fields; machine fields were added next to them (`items.hf | file_url | inline`, `items.fields`, `items.label_map`, `items.filter`, strict `prompt.placeholders`, `output.parse`, `metric.name`, `metric.scale`). Replaced prose values are kept under `*_paper` keys (`fields_paper`, `placeholders_paper`, `parse_paper`, `name_paper`, `user_template_paper`, `filter_paper`). The prepare numbers are recorded in `task.n_items_prepare` / `cost.est_usd_prepare`.

## Counts by final status

- ready: 8
- needs_human: 15
- needs_download_check: 4

Total est_usd of the ready set (runner estimate, all seeds): $141.08

## Per-config table

| wid | status | n_items after prepare | est_usd (prepare) | items source | note |
|---|---|---|---|---|---|
| W4412888118 | ready | 31 | 0.13 | hf-file:koreankiwi99/Nunchi-Bench/resolve/main/nunchi_mcq.csv | Nunchi-Bench: Benchmarking Language Models on: HF CSV read directly (no parquet conversion); options block verbatim from eng_choices; gold letters |
| W7159577685 | needs_human | 25 | 0.40 | inline (25 rows) | Breaking the Chains of Probability: Neutrosop: 25 inline rows render; needs parse 'json sum of fields' + mean-without-gold metric |
| W4412889033 | needs_human | 1559 | 97.27 | gh:stefanolocci/Character-Role-Narrative-Framework-LLMs/main/tweets_dataset.json | Applying the Character-Role Narrative Framewo: public release anonymises every tweet/entity text ('ANONYM'); entity-level F1 unsupported |
| W4400375186 | ready | 200 | 9.91 | hf-file:Song-SW/CEB/resolve/main/CEB-Recognition-S/gender.json | CEB: Compositional Evaluation Benchmark for F: gender.json has 200 rows (not 100); released 'prompt' field = paper template; gold target 1/2, regex parse |
| W4416034777 | needs_human | 100 | 9.41 | inline (100 rows) | The Illusion of Randomness: How LLMs Fail to : 100 inline rows render; TVD is a distribution-level metric; last-mention parse needed |
| W4412888351 | needs_human | 164 | 31.63 | hf CodeEval-Pro/humaneval-pro default/train | HumanEval Pro and MBPP Pro: Evaluating Large : prompts render; pass@1 needs code execution |
| W4416036577 | needs_download_check | - | - | gh:DanielLin97/ACLR4RUMOR-NAACL2022/main/data/Twitter/COVID-19/Twitter-COVID19.7z | Cross-domain Rumor Detection via Test-Time Ad: only a .7z archive in the repository; runner reads json/jsonl/csv/tsv/parquet |
| W4404782525 | ready | 500 | 8.93 | hf qiaojin/PubMedQA pqa_labeled/train | Characterizing LLM Abstention Behavior in Sci: qiaojin/PubMedQA pqa_labeled/train filtered to the 500 official test pubids; maybe -> unanswerable |
| W4404781158 | ready | 300 | 15.00 | gh:DojunPark/MultiPragEval/main/test_suite.csv | MultiPragEval: Multilingual Pragmatic Evaluat: test_suite.csv (300); parse = first '(X)'; gold A-E |
| W4415035710 | needs_human | 122 | 11.79 | hf SonalPrabhune/RealWorldQuestioning default/train | Do LLMs have a Gender (Entropy) Bias?: train split only (122 of 158; 3 splits needed); system-prompt slot not rendered; t-statistic metric |
| W4407571428 | needs_human | - | - | hf ShunchiZhang/PhysiCo core/test | The Stochastic Parrot on LLM's Shoulder: A Su: core/test has no labels (remote scoring endpoint only; dev has); numpy grids crash json.dumps (TypeError, not NeedsHuman) |
| W4406058824 | needs_human | - | - | hf-file:SciCode1/SciCode/resolve/main/problems_test.jsonl | SciCode: A Research Coding Benchmark Curated : stateful sub-step prompts (model's own earlier code) + execution; HF file has 65 problems / 291 sub-steps |
| W7164614711 | ready | 12780 | 0.73 | gh:zihaurpang/Multilingual-Emotional-Validation/main/M-EDESConv/test.csv | I Understand How You Feel: Enhancing Deeper E: test.csv 12,780 rows; gold 1/0 -> validate/non-validate; macro_f1 |
| W4403758464 | needs_human | - | - | gh:karthikv792/LLMs-Planning/main/plan-bench/prompts/blocksworld/task_1_plan_generation.json | LLMs Still Can't Plan; Can LRMs? A Preliminar: one-shot query must be cut to zero-shot; JSON 'instances' key not read by _parse_table; VAL validation; file has 500 not 600 |
| W4412888091 | needs_human | 250 | 13.24 | gh:csalt-research/LoFTI/main/dataset/LoFTI.jsonl | LoFTI: Localization and Factuality Transfer t: LoFTI.jsonl snake_case fields render; seeded 250 subset applied; LLM-judge EC metric |
| W7144391352 | ready | 279 | 17.52 | gh:jhCOR/CALRKBench/main/dataset/calrk_type2.jsonl | CALRK-Bench: Evaluating Context-Aware Legal R: calrk_type2.jsonl 279 rows; item-weighted accuracy reproduces the Table 1 Avg (0.754); gold letters |
| W4412887844 | needs_download_check | - | - | hf MichiganNLP/Chumor default/test | Chumor 2.0: Towards Better Benchmarking Chine: gated (HTTP 401 without token); columns unverified; CJK word-boundary caveat for label parse |
| W4411119490 | needs_human | - | - | hf edinburgh-dawg/mmlu-redux college_chemistry/test | Are We Done with MMLU?: verbaliser layout confirmed from code; needs option_at(choices, answer), 30-config concat, positive-class F1 |
| W4401545735 | ready | 2264 | 3.55 | hf mteb/FinancialPhrasebankClassification default/train | Designing Heterogeneous LLM Agents for Financ: mteb/FinancialPhrasebankClassification train = all 2,264 all-agree sentences (class counts identical); label 0/1/2 remapped |
| W4403443823 | needs_human | - | - | (github) none resolvable | Science is Exploration: Computational Frontie: repository holds only the MWLB data (544); TroFi (3,736) not public (SFU 403); per-target-word parse + precision metric |
| W4412944996 | needs_human | 3000 | 92.58 | hf OpenStellarTeam/Chinese-SimpleQA default/train | Chinese SimpleQA: A Chinese Factuality Evalua: prompts render (question = whole message); GPT-4o judge + F-score needed |
| W4404352371 | needs_human | - | - | hf afdsafas/EEE-Bench default/test | EEE-Bench: A Comprehensive Multimodal Electri: images required (text-only runner); ~133 MB parquet not downloaded; judge extraction |
| W4404985489 | needs_human | 589 | 20.19 | gh:mitdbg/scivar/main/benchmark/chunkset/askem_variable_dataset.json | Variable Extraction for Model Recovery in Sci: prompts render (589 chunks); ~30K judge pairs + pooled F1; multi-group line regex |
| W7166873827 | needs_download_check | - | - | (url) none resolvable | Reward Modeling for Scientific Writing Evalua: TUdatalib unreachable (TLS failure), ~100 MB; three aspect templates in one config |
| W4416035248 | ready | 10342 | 85.31 | gh:SCUNLP/CANDY/main/Candyset/candyset_v1.jsonl | CANDY: Benchmarking LLMs' Limitations and Ass: candyset_v1.jsonl filtered to 10,342 rows (string filter verified against a real date parse); gold 0/1 -> 非谣言/谣言 |
| W4414992335 | needs_download_check | - | - | hf anvo25/vmmu default/full_vqa | VMMU: A Vietnamese Multitask Multimodal Under: ~1.26 GB image parquet not downloaded; images required; per-subject macro mean |
| W4399404161 | needs_human | - | - | hf TIGER-Lab/MMLU-Pro default/test | MMLU-Pro: A More Robust and Challenging Multi: test parquet loads; per-category 5-shot CoT block from the validation split not expressible |

## Runner gaps hit (most important first)

- Metrics beyond item-level scoring: LLM-judge metrics (W4412888091 LoFTI EC, W4412944996 Chinese SimpleQA F-score, W4404985489 SciVar pairwise F1, W4404352371 EEE-Bench extraction), code execution (W4412888351 HumanEval Pro, W4406058824 SciCode), plan validation (W4403758464 VAL), distribution/group statistics (W4416034777 TVD, W4415035710 Welch t), grouped means (W4414992335 per-subject macro mean, W4411119490 positive-class binary F1). None fits `metric.name`; these stay `custom` and `needs_human`.
- Placeholder mini-language: no way to select an option by an integer index with its letter (`option_at(choices, answer)`, W4411119490), no matrix rendering of 2-D arrays (W4407571428; `items.<field>` json-dumps non-strings and crashes with `TypeError` on numpy arrays instead of raising NeedsHuman), no list indexing (`sub_steps[k]`, W4406058824), no per-category few-shot block from a second split (W4399404161), no pattern-based substring extraction from a field (W4403758464 zero-shot cut).
- Placeholders are substituted in the user template only; a slot in `prompt.system` is sent unfilled and is not detected by the leftover check (W4415035710 `{category}`).
- One (config, split) per config: no concatenation of several HF configs (W4411119490, 30 subject configs) or splits (W4415035710, 3 splits; FPB solved by switching to a single-split mirror).
- `output.parse`: `json field` returns one field (no sum of fields, W7159577685); `regex` returns group 1 of the first match only (multi-line/multi-group extraction, W4404985489, W4412889033); `label from set` returns the first label in list order that occurs anywhere (not the last/final mention, W4416034777) and relies on `\w` word boundaries, which fail for CJK labels embedded in running text (W4412887844, W4416035248 - the CANDY prompt's fixed output format makes this safe in practice); the generic `letter` parser also matches a standalone 'A'/'I' used as a word, so W4404781158 uses `regex \(([A-E])\)`.
- Sources: `_parse_table` picks list values only under data/items/examples/test/questions/rows (PlanBench uses `instances`); archives (.7z, .zip) are not readable (W4416036577, takala/financial_phrasebank); `source_type: hf` requires a Hub parquet conversion (CSV/JSON repos without one - Nunchi-Bench, CEB - were switched to `source_type: url` with the resolve URL); gated datasets need a token (W4412887844).
- Cost estimate counts `max_tokens` as the output length of every call, so configs with large max_tokens (CEB 512, RPS/HumanEval 1-2K, gpt-5 2048 minimum) are over-estimated; MEV at gpt-4.1-nano is $0.73 for 38,340 calls.

## Not prepared (no run directory)

- W4416036577 (7z archive only), W4412887844 (gated, HTTP 401), W7166873827 (TUdatalib TLS failure, ~100 MB), W4414992335 (~1.26 GB images), W4404352371 (~133 MB images), W4403443823 (TroFi not public). The prepare attempts of W4407571428, W4406058824, W4403758464, W4411119490 and W4399404161 fail for the documented gaps (their `runs/tierb/<wid>/needs_human.txt` holds the runner's reason; W4407571428 crashes with a TypeError before that).
