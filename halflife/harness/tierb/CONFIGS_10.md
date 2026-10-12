# Tier B run configs, group 10 (11 papers)

Configs written to `halflife/harness/tierb/configs/<wid>.json` following `CONFIG_SCHEMA.md`, with per-paper hooks in `halflife/harness/tierb/hooks/<wid>.py` where the mini-language was not enough. Prompts were copied from the extracted texts in `halflife/external/papers_tierb/`, except where the paper prints none and the authors released one (W4414979614 Zenodo artifact, W4410627635 Google Drive script) — each such case is marked in `prompt.source_location` and `prompt.verbatim`. No model API was called. No dataset over 50 MB was downloaded: where a release exceeds the ceiling the schema was read through the Hugging Face datasets-server API (W4414580759) or the needed members were pulled out of the archive with HTTP Range requests (W4414979614, 27 KB + 0.59 MB out of a 2.1 GB zip). Date of the checks: 2026-09-19.

## Counts by status

- ready: 3
- needs_download_check: 0
- needs_human: 8
- total estimated cost: USD 350 (ready configs USD 86; the eight blocked ones USD 264 if their open points are all resolved in favour of running)

## Table

| wid | status | model | seeds | task | n_items | est $ | hook | open points | title |
|---|---|---|---|---|---|---|---|---|---|
| W4404781378 | needs_human | gpt-4o-2024-05-13 | 3 | other | 171 | 4 | no | no released sample; citation snapshot of 20 Jul 2024 unrecoverable; Magentic serialisation unknown; R² is set-level | Learning the Bitter Lesson: Empirical Evidence from 20 Years of CVPR Proceedings |
| W4399511962 | needs_human | gpt-4-turbo-2024-04-09 | 1 | generation | 1335 | 20 | no | judge prompt deliberately not released; judges gpt-3.5-turbo-0125 (not callable) + llama-3-70B; data file 739 MB | CRAG -- Comprehensive RAG Benchmark |
| W4400611869 | **ready** | gpt-4-turbo-2024-04-09 | 3 | classification | 1000 | 78.84 | no | — | Lynx: An Open Source Hallucination Evaluation Model |
| W4407386373 | needs_human | gpt-4o-2024-05-13 | 3 | generation | 200 | 9.50 | yes | claim cell: 36.3 is Table 4 (human judges, N=30), the LLM-judge cell is Table 3 E=40.8 (N=200) — substitution needs a go | Is a Peeled Apple Still Red? Evaluating LLMs' Ability for Conceptual Combination with Property Type |
| W4410627635 | needs_human | gpt-4-turbo-2024-04-09 | 1 | classification | 1136 | 73 | yes | released script pins gpt-4-1106-preview, not gpt-4-turbo-2024-04-09; batch size and CSV column layout ambiguous; no gold labels | Analysis of automation and retraining opportunities for the Brazilian federal public service |
| W4412945558 | needs_human | gpt-4o-2024-05-13 | 3 | generation | n/a | 45 | no | FAITHQA queries never released (no URL in the paper); evaluated subset size unstated; CONSTRAINT SCORE weights α_g not printed | Beyond Facts: Evaluating Intent Hallucination in Large Language Models |
| W4414580759 | needs_human | o4-mini-2025-04-16 | 1 | classification | 4519 | 60 | yes | prompt printed only as an English translation of a Chinese task; '## First-instance Documents' assembly elided; parquet 107 MB blocks --prepare | AppealCase: A Dataset and Benchmark for Civil Case Appeal Scenarios |
| W4414979614 | **ready** | gpt-5-2025-08-07 | 3 | extraction | 30 | 2.38 | yes | — | Overcoming Language Barriers: Multilingual Analysis of the 2023 Swiss Privacy Law's Impact |
| W4415270561 | **ready** | gpt-4.1-nano-2025-04-14 | 3 | extraction | 1000 | 5.08 | yes | — | Diff-XYZ: A Benchmark for Evaluating Diff Understanding |
| W7125460230 | needs_human | gpt-4.1-nano-2025-04-14 | 3 | classification | 1000 | 12 | no | agentic SQL tool-calling (20 tool calls/claim) the runner cannot express; ~110M-token evidence DBs; user turn not printed | ClaimDB: A Fact Verification Benchmark over Large Structured Data |
| W7166823216 | needs_human | o3-2025-04-16 | 1 | other | 200 | 40 | no | multimodal (≈22 video frames + transcript) unsupported by the runner; data_video.zip 13.5 GB; reasoning_effort unstated | Probing Multimodal Large Language Models on Cognitive Biases in Chinese Short-Video Misinformation |

## Verification of the ready configs

All three pass `python tierb_runner.py <wid> --prepare --dry-run --cap 200` with `dropped_unrenderable: 0`, and the first rendered item in `runs/tierb/<wid>/items.jsonl` was read back and compared with the paper.

- **W4415270561** — 1,000 items / 3,000 requests, $5.08. Rendered prompt is Figure 1 (system `You are a helpful assistant.`) plus Figure 3 with the instance's `udiff` and `old_code`; gold is `new_code`. Hook supplies the fenced-code parse and Sec. 3.1's Stripped Exact Match (the runner's own `exact_match` lower-cases and collapses whitespace, which would inflate the score).
- **W4400611869** — 1,000 items / 3,000 requests, $78.84. Rendered prompt is Appendix A.2 verbatim over HaluBench's `question` / `passage` / `answer`, `source_ds == 'FinanceBench'` giving exactly 1,000 rows at 500 PASS / 500 FAIL. No hook: `regex` parse on the SCORE key plus the runner's accuracy.
- **W4414979614** — 30 items / 90 requests, $2.38. Three messages exactly as the artifact's `Validation_GPT_Swiss_GDPR_class.py` builds them (system, codebook, policy text). Hook supplies the three-message render and binary F1; the released `Results_GPT5/eval_metrics.csv` reproduces the paper's 0.93 (0.9285714…) so the cell, split and metric are confirmed from the artifact.

## Hooks

| hook | functions | what the mini-language could not do |
|---|---|---|
| `W4415270561.py` | parse, score | strip the ``` fence; Stripped Exact Match (whitespace-only lines removed, case and indentation significant) |
| `W4407386373.py` | load_items, parse, score, judge_requests, score_with_judge | filter `ccpt_emergent.csv` by `test_index.json`; three LLM-judge calls per response (combination / head noun / modifier) with Table 17's prompt; E = max(R_N,P − max(R_H,P, R_M,P), 0) with R = (rating−1)/9 |
| `W4410627635.py` | load_items, render, parse, score | join two xlsx sheets into `<row>;<POSITION>;<duty>`; 18 KB system prompt from file; horizon = last bare 0–3 field of the returned CSV row; rate of horizon ∈ {0,1} with no gold |
| `W4414580759.py` | render, parse, score | concatenate six sub-fields of the nested `first-instance` struct; multi-label parse; multi-label F1-macro over three classes |
| `W4414979614.py` | load_items, render, score | a second user message carrying the policy text; binary F1 on the positive class |

Every hook is under 200 lines, makes no API call, is deterministic, and carries an inline self-test under `if __name__ == "__main__"` that runs clean.

## Two metrics verified against released material before the run

- **W4407386373** — the authors' `results/pi_emergent_gpt-4o_naive.csv` reproduces Table 3 exactly: per-seed E 39.9 / 41.7 / 40.7 (mean 40.8), R_N,P 82.8 / 83.7 / 83.4 (mean 83.3), R_H,M,P 44.6 / 43.2 / 44.5 (mean 44.1). `indiv_max == max(root, modifier)` and `E == max(combination − indiv_max, 0)` hold on every row, and relevance takes exactly the values k/9, k = 0..9, confirming (rating − 1)/9.
- **W4414979614** — `Results_GPT5/eval_metrics.csv` gives English `contr` F1 0.9285714285714286 (accuracy 0.9333, precision 0.8667, recall 1.0) against `Phase_3_Ground_Truth.csv`, in which 13 of the 30 English policies carry `contr = 1`.

## Recurring difficulties

- **Claim cell mis-identified once.** W4407386373's triage record cites "Table 3, GPT-4o/Base, E = 36.3, N = 200", but 36.3 is the GPT-4o/Base cell of **Table 4**, the *human* evaluation on a 30-item sub-sample. The Table 3 (LLM-judge, N = 200) value is 40.8. The config targets 40.8 and the substitution is the first open point; nothing else in the paper blocks it.
- **Prompt not in the paper, but in the artifact.** Two papers print no usable prompt: W4414979614 ("We release the prompts and the schema verbatim with our artifacts") and W4410627635 (Appendix 2 is absent from the extracted text). Both were resolved from the authors' own public releases — a Zenodo record and a public Google Drive folder — read byte-for-byte, which turned one of them into a ready config.
- **Releases far over the download ceiling.** Four papers ship data that cannot be fetched under 50 MB: CRAG 739 MB (every row embeds five full HTML pages), AppealCase 107 MB parquet / 252 MB LFS JSON, Fine-VDK 13.5 GB of video, the Swiss artifact 2.1 GB. Range requests on the zip and the datasets-server API replaced the download in two of these; the other two remain blocked.
- **Protocols the runner cannot express.** ClaimDB is an agent with a SQL tool and a 20-call budget; Fine-VDK sends ~22 video frames per item. Both would need harness changes, not config changes. The paper's own no-tool ablation for ClaimDB (macro-F1 0.253 vs 0.337) shows a tool-free substitute would not be comparable.
- **Judges.** Three papers score with an LLM judge. Two are admissible in principle — W4407386373 (gpt-4o-2024-05-13, Table 17 printed in full) and W4412945558 (gpt-4o-2024-05-13, Tables 5/6/7 printed) — and one is not: CRAG states outright that "We did not release the exact prompt used in the challenge to avoid prompt attack", and averages gpt-3.5-turbo-0125 (absent from `harness/pricing.json`, i.e. not callable) with a self-hosted llama-3-70B.
- **Metrics with no gold label.** W4410627635's 72% and W4404781378's R² are both properties of the model's own output distribution rather than agreement with a reference, so "reproducing" them is a rate-to-rate or fit-to-fit comparison, not a correctness test. Both configs say so in `metric.definition` and in the open points.
- **Unstated decoding parameters, again.** Only three papers state any: W4407386373 (T = 0.7, p = 0.95, three seeds), W7125460230 (a full per-model table) and W4412945558 (τ = 0.3). The rest are `assumed`. On the reasoning models the missing parameter that matters is `reasoning_effort` (W7166823216, W4414580759), which no paper in this group pins.
- **Structured output dropped by the harness.** W4414979614's released call uses a strict `json_schema` response format and `seed=123`; `tierb_runner.body_for` sends neither for a `gpt-5*` id, so the JSON now rests on the prompt's own `### OUTPUT ###` block. Recorded as the config's only approximation, and the unparsed count in `result.json` will show if it bites.
- **Extraction damage was minor and repaired where unambiguous.** Rejoined hard wraps in every prompt; doubled braces unescaped where the paper printed a Python format string (Lynx's `{{"REASONING"...}}`, CCPT's `{{"property"...}}`); the paper's own typos kept ("for you answer" in Diff-XYZ, "evalute" in the Bitter Lesson prompt, the numbering glitch in Fine-VDK's step 3). CCPT's literal `{generated_property}` had to be declared as a `literal:` placeholder so the runner would not treat it as an unfilled slot.
