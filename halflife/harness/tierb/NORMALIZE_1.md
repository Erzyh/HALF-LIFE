# NORMALIZE_1: machine fields for the 28 configs of data/tierb_triage/normalize_1.csv (2026-09-07)

Every config now carries the strict machine fields of CONFIG_SCHEMA.md ('Machine fields'): items.hf / items.file_url / items.inline,
items.fields with exact column names, items.label_map, items.filter (pandas query or null), prompt.placeholders in the mini-language,
output.parse in a supported form, metric.name / metric.scale. Prose fields were kept (moved to *_prose when replaced). Prompt texts are
unchanged; the three concatenated multi-block templates were split into per-key dicts (user_template_by_language / _by_level / _by_dataset)
with the first block left in user_template. Verification: `python tierb_runner.py <wid> --prepare --dry-run` (no API calls); the rendered
first item of every successful prepare was read from runs/tierb/<wid>/items.jsonl. Configs whose --prepare fails or renders an incomplete
prompt keep every machine field that is expressible and describe the missing piece in open_points / runner_gaps.

## Counts by final status

- ready: 2
- needs_download_check: 2
- needs_human: 24

Total est_usd of the ready set (runner dry-run estimate; output tokens counted at max_completion_tokens, so an upper bound): $58.52

## Per-config table

| wid | status | n_items after prepare | est_usd (prepare) | items source | note |
|---|---|---|---|---|---|
| W4404792825 | needs_human | 10 | 0.15 | in_paper (10 inline) | 10 inline administrations render; reply = 10 ratings whose sum is the score (parse + gold-free mean metric missing) |
| W7134094238 | needs_human | 30 | 0.42 | in_paper (30 inline) | 30 inline rows render; four-probability parse + KL metric missing |
| W7166799942 | needs_human | fails: placeholder spec not machine-readable: "group rows by Dialogue_ID orde | - | url:test_sent_emo.csv | CSV verified (2,610 rows); one call per dialogue with k gold labels needs a group-by placeholder |
| W7135428702 | needs_human | 128 | 0.00 | hf:sommify/sommbench wtqa/test | English block + filter language=='en' renders the paper prompt for 128 items; per-language template selection missing for the 8-language cell (alt. cell Table 2 EN 0.80) |
| W4404990976 | needs_human | fails: unknown table format for /set/documents/2022/apr/practice_plain_questi | - | url:Practice_Plain_Question_Answer.pdf | SET exam PDF text layer damaged (tone marks, answer digits); items must be transcribed into items.inline |
| W4416339332 | needs_human | 66 | 2.31 | url:not_adopted_resolutions_dataset.json | JSON list renders (persona literal); U.S. vote must be derived from vote.favour/against/abstention lists; weighted F1 missing |
| W7131319772 | needs_human | 500 | 6.29 | url:core.jsonl | core.jsonl renders; Agreement cell needs core + hard-sarcasm (list of file_url); alt. cell core macro-F1 0.990 |
| W4414494504 | needs_human | fails: unknown table format for /datasets/wellytics/pgxrag/resolve/main/pgxra | - | url:PGxRAG%20Supplementary%20tables_revised.xlsx | xlsx not supported; question/options/gold inside one JSON cell |
| W4414758400 | needs_human | 25 | 9.26 | in_paper (25 inline) | 25 inline occupations render; per-story gender count + gold-free ratio missing |
| W4415196225 | needs_human | fails: placeholder spec not machine-readable: 'attach images/<id>.jpg as an i | - | url:hummus_dataset.json | image input; test ids file not found at the expected path |
| W4404782508 | needs_human | 350 | 5.99 | url:test_en.json | test_en.json L1 block renders; 3 templates x 2 variants per record, progress-rate/embedding metrics missing |
| W4399911213 | needs_human | fails: item has no field 'question1'; fields: ['m', 'i', 'x', 't', 'r', 'a',  | - | url:WikiContradict_HumanEval_adjudication.json | JSON dict-of-lists (keyed by judged model) is not flattened by the runner |
| W4399598180 | needs_download_check | fails: not run (source gated/absent/>60 MB) | - | hf:FlagEval/HalluDial spontaneous/test | script-only HF dataset, files on Google Drive (~300 MB); not downloaded |
| W4416034345 | needs_human | 207 | 5.07 | hf:ipst/slds de_de/test | de_de/test renders (207); one-shot prior turns + nine configs missing |
| W4403882451 | needs_human | fails: placeholder spec not machine-readable: "regex on items.query: last 'As | - | url:task_1_plan_generation.json | top-level key 'instances' not recognised; instance text must be cut from the one-shot query; VAL scorer |
| W7134885605 | ready | 200 | 25.27 | url:metastatic_local_random200_noJCO.csv | prompt = system verbatim + abstract; gold from 'accept' via label_map; regex (LOCAL/$) reproduces the binary cell |
| W7166808082 | needs_human | 102 | 20.44 | url:metadata.jsonl | metadata.jsonl renders text part (102 dsreal); image input + emulator scorer missing |
| W7140099019 | needs_human | fails: not run (source gated/absent/>60 MB) | - | hf:hiyouga/geometry3k default/test | image input; literal '{your_answer}' rejected by the slot check; LLM judge |
| W7164447524 | needs_human | fails: not run (source gated/absent/>60 MB) | - | github: no direct URL | images generated locally from Google Drive/KICE PDFs; LLM judge |
| W4410110677 | ready | 249 | 33.25 | url:trials_with_predictions.csv | system {section} pre-filled 'title and abstract'; 249/250 rows (one abstract contains '{IQR}' and is dropped by the slot check); accuracy cell (= F1 0.97) |
| W4404783148 | needs_human | 1240 | 10.32 | url:VIVA_annotation.json | VIVA_annotation.json renders the text part (options joined); image input missing; image links external |
| W7197053912 | needs_human | fails: unknown table format for /combini-hub/multi_agent_relation_extraction/ | - | url:test.out | headerless .out TSV; definitions from a second file; micro-F1 excluding 'none' |
| W4403322813 | needs_download_check | fails: not run (source gated/absent/>60 MB) | - | hf:intronhealth/afrimedqa_v2 default/train | gated (401); columns/label format unverified; options rendered on their own line |
| W4399317891 | needs_human | 428 (cap subset) | 39.92 | hf:bench-llm/or-bench or-bench-hard-1k/train | 1,319 prompts render; LLM refusal judge + gold-free rate metric missing |
| W4411112894 | needs_human | 816 (cap subset) | 39.99 | hf:mediabiasgroup/BABE default/train | 3,121 rows render (816 under the $40 cap); MCC metric missing |
| W4410280647 | needs_human | fails: not run (source gated/absent/>60 MB) | - | hf:cais/hle default/test | gated + 274 MB; judge stage and answer_type-dependent system prompt missing |
| W4411120335 | needs_human | fails: unknown table format for /files/semantic_leakage_prompts.txt | - | url:semantic_leakage_prompts.txt | plain-text prompt file; temperature sweep; paired BERTScore leak rate |
| W4404783788 | needs_human | fails: not run (source gated/absent/>60 MB) | - | hf: no direct URL | 9 templates/sources (114 MB zip, >100 MB jsonl); list-of-references token-F1; truncation |

## Runner gaps hit (generic; the runner was not edited)

Blocking several configs:
- Image inputs: no placeholder that attaches an image (URL / file / parquet bytes) as an image content part - W4415196225, W7166808082, W7140099019, W7164447524, W4404783148 (5 configs).
- Template selected by an item field (per-language / per-dataset / per-answer_type / per-level templates): W7135428702, W4404783788, W4410280647, W4404782508.
- Judge stage (second model call over the reply) and gold-free rate metrics: W4399317891, W4410280647, W7164447524, W7140099019.
- Metrics not in the list: weighted_f1 (W4416339332), mcc (W4411112894), micro_f1 excluding a negative class (W7197053912), token-F1 with a list of references (W4404783788), KL / ratio / sum-of-ratings with no gold (W7134094238, W4414758400, W4404792825), external scorers (VAL for W4403882451, Turtle emulator for W7166808082, BERTScore leak rate for W4411120335).
- Several sources per config: list of file_url (W7131319772 core + hard-sarcasm, W4399598180 two splits), list of hf configs (W4416034345 nine pairs).

Small loader gaps (one config each, cheap to close):
- JSON dict whose values are lists of records (keyed by a group) is not flattened - W4399911213 (the loader returns the dict, rendering then fails).
- JSON top-level key 'instances' is not among the recognised list keys (data/items/examples/test/questions/rows) - W4403882451.
- Table formats: .xlsx (W4414494504), headerless TSV with a .out extension (W7197053912), plain-text one-prompt-per-line (W4411120335), PDF (W4404990976, text layer damaged anyway), zip archives (W4404783788).
- Parquet list columns arrive as numpy arrays; json.dumps of items.jsonl fails when such a column is the gold label - W4404782508 (raw JSON used instead).
- Derived gold labels: label_map remaps scalar values of one column only; membership of a literal in list-valued sub-fields (W4416339332) or a regex on the gold value (W4414494504 'A. text' -> 'A') is not expressible.
- Gated HF datasets: the loader sends anonymous requests (401 for W4403322813, W4410280647).

Rendering gaps:
- Placeholders are substituted in the user template only; a slot in the system prompt stays literal (W4410110677: pre-filled with 'title and abstract' as a workaround).
- The unfilled-slot check scans the rendered text, so an item whose own text contains '{word}' is silently dropped (W4410110677 row 176 with '{IQR}': 249 of 250 items; the drop is silent for every row except the first).
- Literal braces cannot survive in a rendered prompt (W7140099019 needs '\boxed{your_answer}').
- Group-by rendering (several rows -> one call with k gold labels) - W7166799942; regex/substring transforms of a field - W4403882451; lookups joined from a second file - W7197053912.
- Few-shot as prior user/assistant turns - W4416034345.
- Parameter sweeps (a list of temperatures) - W4411120335; for reasoning models only reasoning_effort is forwarded (seed dropped for W4416034345).

Parse notes: 'regex' keeps the first match (several papers take the last; W4411112894 uses a greedy pattern to get the last), 'label from set' returns the first label in set order rather than the first in the reply, 'json field' takes the last whitespace token of the spec (two-word keys such as 'Correct option' cannot be addressed).

## Decisions left to a human (recorded in each config's open_points)
- W7135428702 SommBench: accept the staged English-only run against Table 2 column EN (0.80, n=128) or wait for per-language templates (Table 1, 0.73 over 8 languages).
- W7131319772 ContentBench: accept the staged core-only run against 'Core macro-F1' 0.990 (metric macro_f1) or add list-of-file support for the combined Agreement cell (99.0).
- W4404990976 THaLLE: transcribe the 50 SET practice questions (the PDF's text layer loses Thai tone marks and garbles the answer-key digits).
- W4404783788 RAG-vs-LC: ~$500 at one seed even after the runner gaps are closed.
