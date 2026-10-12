# Tier B machine-field normalization, group 2 (28 configs, 2026-09-07)

Input: `data/tierb_triage/normalize_2.csv`. Every config in `harness/tierb/configs/<wid>.json` now carries the strict
machine fields of CONFIG_SCHEMA.md ("Machine fields"): `items.hf | file_url | inline`, exact `items.fields`,
`items.label_map` where gold needs remapping, `items.filter` (pandas query or null), placeholders in the
mini-language, a supported `output.parse` form, `metric.name` + `metric.scale`. Prose that was overwritten is kept
under `<key>_prose` (and paper templates under `prompt.user_template_paper`); nothing was deleted. Each config has
`machine_fields_added`. Verification command (no API calls): `python tierb_runner.py <wid> --prepare --dry-run`
with the runner at commit 2983b7d (the runner changed mid-task; every executable config was re-prepared with it).

## Counts by final status

| status | n | wids |
|---|---|---|
| ready | 8 | W7139147531, W7140084705, W4399911276, W4400434899, W7140138327, W7166852552, W4406880877, W4403556032 |
| needs_human | 17 | W4407374917, W7166808309, W4416034223, W4416035547, W7117377764, W4402345509, W4403885225, W4404314294, W4406058562, W7135428876, W4406058598, W4405425991, W4411119263, W4417257719, W4403584145, W4403570177, W7161421448 |
| needs_download_check | 3 | W4399912745, W7166837475, W4411120358 |

Ready set: 8 configs, sum of `est_usd` from `runs/tierb/<wid>/prepare.json` = **$87.30** (default cap 40; one
config capped, see table). Ten configs that the triage had marked ready went to needs_human: their prompts or
metrics need a runner facility that does not exist yet (listed under "Runner gaps").

## Table

n_items / est_usd are the values in `prepare.json` after `--prepare --dry-run` ("-" = prepare cannot run).

| wid | status | n_items | est_usd | items source | note |
|---|---|---|---|---|---|
| W7139147531 | ready | 120 | 0.02 | github ai-taste management_benchmark_120.jsonl | level top/top-/good/fair mapped to Exceptional/Strong/Fair/Limited (mapping confirmed against the released prediction records); text argmax instead of first-token logprob rule (approximation), max_tokens 1 -> 4, logprobs still archived |
| W7140084705 | ready | 138 | 0.01 | inline (4 repo JSON files merged: bfi44, mfq, pvq40, sd3) | inventory display names and sorted dimension list follow the repo code; runner macro-F1 pooled over 23 labels vs paper's per-inventory mean (approximation) |
| W4407374917 | needs_human | 100 | 1.37 | inline (SPECIES.md x iucn names x task1_coordinates.json) | renders; reply is a list of 10 floats needing element-wise binarized accuracy (no list parse / metric) |
| W7166808309 | needs_human | - | - | hf yuriilaba/ukrainian-visual-wsd-benchmark (not downloaded, ~400 MB) | 10 image parts per prompt; runner is text-only |
| W4416034223 | needs_human | 216 | 4.35 | github manyifeval.jsonl, filter `instruction_id_list.str.len() == 5` | renders; metric needs IFEval checkers |
| W4416035547 | needs_human | - | - | hf EleutherAI/hendrycks_math, 7 configs, filter Level 5 | loads (configs concatenation); two-stage target/identifier pipeline, constant gold |
| W7117377764 | needs_human | 45 | 1.11 | github validation.csv, filter `has_ground_truth == '1'` | renders; DMS coordinates -> haversine km not a runner metric; CSV has 125 rows (40 test + 5 dev with ground truth, not 43) |
| W4402345509 | needs_human | - | - | hf futurehouse/lab-bench LitQA2/train | options = ideal + distractors + fixed extra, seeded permutation, gold letter per item |
| W4403885225 | needs_human | 500 | 9.97 | github verbosity_bias_standardized.json | perturbed judgment renders; RR needs the paired original judgment (agreement metric, no gold) |
| W4400434899 | ready | 800 | 13.39 | inline (8 Stag Hunt setups x 100 runs) | accuracy vs constant gold 'A' x 100 = share choosing A; invalid replies count as non-A |
| W4399912745 | needs_download_check | - | - | hf princeton-nlp/ALCE-data (451 MB tar) | archive, doc-list formatting, str_em |
| W7140138327 | ready | 1259 | 7.81 | hf disi-unibo-nlp/ReMedQA default/medqa_mcq | user message = released prompt_think (paper template kept in user_template_paper); boxed-letter regex (last match) |
| W4404314294 | needs_human | - | - | hf Rajat1212/DisasterQA default/train | column 'Answer Choices' has a space (placeholder grammar rejects it); literal {letter} now fine |
| W4406058562 | needs_human | - | - | zenodo dataset.zip (97.8 MB) | zip of per-document text files; {YY} is a computed word count |
| W7135428876 | needs_human | - | - | url epc-ir.clean.tsv (headerless) | PubMed fetch, kNN few-shot, CV folds, logprob AUPRC; TSV has no header row |
| W7166852552 | ready | 8345 | 0.48 | hf QwenQKing/LexGenius default/train | 20 files hold 8,345 MCQs (config said 8,385); options already lettered -> join with newlines; no option shuffle (approximation) |
| W4406058598 | needs_human | - | - | github halu-j test_data.jsonl | evidences list must be composed from prefix fields (1-3 misleading present) and shuffled; label ints 0/1/2 -> True/Neutral/False inferred |
| W4405425991 | needs_human | - | - | none | repository has no ProteinQA test file (src/data/DATASET.md is an acknowledgement); FASTA fetch |
| W4411119263 | needs_human | 1030 | 20.29 | hf yale-nlp/ReIFE src, 4 splits | renders all four datasets; human label key = winner (1/2 -> a/b); swapped-order pass and per-dataset averaging missing |
| W4406880877 | ready | 150 | 12.08 | github human_detectors.json (dict of records) | filter keeps the 150 AI articles so accuracy x 100 = TPR (paper cell 54); FPR half = inverted filter; max_tokens 4096 added for o1 |
| W4403556032 | ready | 823* | 48.28* | hf openlifescienceai/medqa default/dev (1,272 = bigbio validation) | *cap 40 subset of the 1,272 dev questions (full set ~$59 by the runner's pre-subset formula; the post-subset figure is recomputed with max_tokens, see gaps); template slot split into {question}\n{options} |
| W7166837475 | needs_download_check | - | - | zenodo data.tar.gz (1.24 GB) | not fetched; NEI exclusion from macro-F1 not a runner facility |
| W4417257719 | needs_human | 451 | 9.26 | hf SakanaAI/EDINET-Bench earnings_forecast/test | renders (template restored from the released yaml, '<sheet>: <json>' lines as in predict.py); metric ROC-AUC not implemented; 88 MB render files removed after inspection |
| W4403584145 | needs_human | - | - | none (simulation) | sequential multi-agent opinion dynamics |
| W4403570177 | needs_human | - | - | github RMB Pairwise_set/Helpfulness/Chat/Casual Conversation.json | field names verified (pair_uid, conversation_input, chosen.answer, rejected.answer); 37 files, dialog rendering, coin-flip A/B |
| W7161421448 | needs_human | 20 | 0.25 | inline (10 situations x 2 conditions) | story prompts render; judge stage + odds ratio missing; fixed params.seed would make replicates identical |
| W4411120358 | needs_download_check | - | - | Google Drive archive (not fetched) | three templates by question type, weighted custom metric |

## Runner gaps hit (things a human or the runner author must decide; the runner was not edited)

- Composed / derived placeholders are the biggest blocker (6 configs): numbered evidence lists built from prefix
  fields with a seeded shuffle (W4406058598), options assembled from several fields plus a fixed extra option with a
  per-item permutation and a derived gold letter (W4402345509), seeded option shuffles (W7166852552 runs in the released
  order instead), dialog turns rendered from a list plus a seeded chosen/rejected coin flip (W4403570177), computed
  values such as a word count (W4406058562), formatted slices of nested lists (W4399912745).
- Field names with spaces (`Answer Choices`, W4404314294) are rejected by the `items.<field>` grammar (`\w` only);
  this is the only blocker left for that config.
- Multi-call protocols: target-then-identifier (W4416035547), story-then-judge (W7161421448), paired judgments for
  a robustness rate (W4403885225), swapped-order judging (W4411119263), sequential simulation (W4403584145).
- Metrics not in the runner: ROC-AUC (W4417257719), haversine mean error from DMS coordinates (W7117377764),
  element-wise list accuracy (W4407374917), IFEval checkers (W4416034223), agreement rate (W4403885225), str_em
  (W4399912745), macro over datasets/inventories (W4411119263, W7140084705 approximated by pooled macro-F1),
  AUPRC from logprobs (W7135428876).
- Parse forms: regex returns group 1 only (six-group DMS pattern), no list-of-numbers parse, no first-token
  logprob scoring (W7139147531 uses a text fallback; logprobs are still requested and archived).
- Sources: tar/zip archives and folders (W4399912745, W4406058562, W7166837475), headerless TSV (W7135428876),
  images (W7166808309), multi-file GitHub folders (37 RMB files; the four psychometric files were merged into
  `items.inline` instead).
- Small runner defects noticed: `body_for` does `int(None)` when a reasoning model's `max_tokens` is null (W7117377764,
  W4416035547 now carry an explicit value); after a cost-cap subset the estimate is recomputed with `max_tokens`
  instead of `out_guess`, so `prepare.json` can report an est_usd above the cap (W4403556032: 48.28 vs cap 40);
  `frequency_penalty` is not forwarded (W4399911276); list/dict-valued gold needs `label_map` keyed by the Python
  string form (W4399911276 target_scores); `params.seed` is constant across `seed_idx` replicates (W7161421448);
  item ids fall back to subset positions when `fields.id` is null.
