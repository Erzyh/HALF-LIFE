# Hooks group 4: per-paper hooks for 25 needs_human configs (2026-09-07)

Input: `data/tierb_triage/hooks_4.csv` (25 configs, all `needs_human`). Hooks live in `harness/tierb/hooks/<wid>.py`; every hook carries an inline self-test (`python <wid>.py`) and every ready config passed `python tierb_runner.py <wid> --prepare --dry-run` with the first rendered prompt checked against the paper. No model API was called.

## Counts

- ready: **11** (hooks written, prepare succeeds, prompt renders, scoring implemented)
- still needs_human: **14**, by reason:
  - gated data: 3 (W4411120327, W4417438236, W4410280647)
  - execution sandbox: 2 (W4403885480, W4412888351)
  - image inputs: 2 (W4404470015, W4404352371)
  - data never released: 1 (W4416157016)
  - PDF-only items with a damaged text layer: 1 (W4404990976)
  - self-hosted Qwen-72B-Chat judge, three judge prompts per item: 1 (W4402426686)
  - embedding-based few-shot selection: 1 (W7135428876)
  - data anonymised: 1 (W4412889033)
  - prompt parts not printed: 1 (W4403347060)
  - prompt not printed: 1 (W7104384491)
- est_usd of the ready set: **$284.73** by the triage CSV figures; **$190.49** by the runner's prepare.json (3 seeds where staged, default --cap 40 applied: W4411112894 and W4403370432 are cost-capped to seeded subsets, raise --cap for the full item sets).

## Table

| wid | status | hook functions | n_items (prepare) | est_usd csv / prepare | note |
|---|---|---|---|---|---|
| W7159577685 | ready | parse, score | 25 (25) | 0.40 / 0.44 | T+I+F sum per reply, mean over valid replies; 25 prompts render verbatim (Appendix A.1) |
| W4416157016 | needs_human | - | 15 | 1.00 / - | data never released (primary-study sets) + metric needs torch (BERTScore) |
| W4403885480 | needs_human | - | 70 | 2.00 / - | execution sandbox + human grading (0/0.5/1.0), six skeletons unprinted |
| W4404990976 | needs_human | - | 50 | 3.00 / - | PDF-only items with a damaged text layer (OCR / manual transcription) |
| W4404470015 | needs_human | - | 100 | 5.00 / - | image inputs (861 MB) + human sample screening + synonym table |
| W7131319772 | ready | load_items, parse | 1000 (1000) | 6.29 / 3.98 | core.jsonl + hard-sarcasm.jsonl concatenated (items.file_urls); label parse tolerant to spaces/hyphens |
| W4411120327 | needs_human | - | 175 | 8.00 / - | gated data (Civ. Pro. items on request only) |
| W4417257719 | ready | parse, score | 451 (451) | 9.26 / 9.26 | JSON 'prob' (fallback 'prediction'); rank-based ROC-AUC; 451 test reports, up to ~87k chars each |
| W4415035710 | ready | parse, score | 158 (158) | 11.79 / 6.40 | character-level Shannon entropy (bits; reproduces the released entropy columns to 3 decimals), Welch t Female-Male; items.hf.splits loads all three splits, gold = attribute |
| W4399911213 | ready | load_items, parse | 240 (240) | 15.00 / 18.62 | dict-of-lists flattened (modelName, uid = model:question_ID); LAST 'evaluation:' label with the 'partically' remap; accuracy = runner |
| W4402426686 | needs_human | - | 299 | 18.00 / - | self-hosted Qwen-72B-Chat judge, three judge prompts per item (multi-call) |
| W4417438236 | needs_human | - | 100 | 20.00 / - | gated data (MRNet agreement, 5.8 GB) + image inputs |
| W4404314294 | ready | render, parse, score | 707 (707) | 21.00 / 27.24 | 'Answer Choices' column (name with a space) rendered, literal '{letter}' kept; Sec. IV phrase regex; accuracy over answered questions |
| W4406058562 | ready | load_items | 100 (100) | 23.00 / 20.12 | Zenodo dataset.zip (97.8 MB, cached) -> 100 UK-Abs test judgements, YY = reference word count (mean 1095.49 = paper Table 2); render + ROUGE-L = runner |
| W7135428876 | needs_human | - | 16483 | 25.00 / - | embedding-based few-shot selection (torch), 16.5k PubMed fetches, logprob scoring, AUPRC |
| W4411119490 | ready | render, parse, score | 3000 (3000) | 30.00 / 8.01 | verbaliser block with Ground Truth Answer from the index; 30 subject configs via items.hf.configs; positive-class ('not ok') F1 |
| W4412888351 | needs_human | - | 164 | 31.63 / - | execution sandbox (pass@1 on generated code) |
| W4411112894 | ready | parse, score | 3121 (1027) | 39.99 / 40.00 | LAST 'The answer is <LABEL>'; Matthews correlation coefficient (BIASED positive); default cap keeps 1,027 of 3,121 sentences, raise --cap for the full set |
| W7197053912 | ready | load_items, parse, score | 3211 (3211) | 48.00 / 16.43 | headerless test.out with the release's columns; candidate block = labels in schema order + 'none' + '- label: definition' lines from utils/text.py SemRep_LABEL2DEF; micro-F1 over positive types |
| W4404352371 | needs_human | - | 2860 | 59.00 / - | image inputs (133 MB parquet) + unpinned gpt-4o-mini judge |
| W4403370432 | ready | load_items, render, parse, score | 2633 (1383) | 80.00 / 39.99 | dead anonymous link replaced by the public mirror publicsubmission/CPSBench: authors' 10 folds, SimCSE shots (first 3) and prompt/ner.txt assembled as gpt_inference.py; entity-level micro-F1 (src/eval.py); default cap keeps 1,383 of 2,633 sentences |
| W4412889033 | needs_human | - | 50 | 97.27 / - | data anonymised ('ANONYM' texts), test set not reconstructible |
| W4410280647 | needs_human | load_items, render, parse, judge_requests, score_with_judge | 2150 | 108.00 / - | hook complete (system prompt by answer_type, o3-mini-2025-01-31 judge with structured decoding, accuracy); blocked only by the gated 274 MB parquet - place a local copy under external/data/tierb_items/W4410280647/ |
| W4403347060 | needs_human | - | 800 | 290.00 / - | prompt parts not printed (<Format Instructions>, <Psychometric Test>) + two dependent calls |
| W7104384491 | needs_human | - | 15481 | 929.00 / - | prompt not printed (Figure 8 image; prompt files absent from the repo) + function-calling body unsupported + cost decision |

## Decisions worth knowing

- W4403370432 (CPSBench): the paper's anonymous.4open.science link is dead, but `github.com/publicsubmission/CPSBench` holds the full package (10-fold split with KFold seed 42, per-fold `shot.json` with the SimCSE-retrieved training ids, `prompt/ner.txt` with all six type definitions, `src/llm/gpt_inference.py`, `src/eval.py`). The hook reproduces the authors' prompts byte-for-byte from those files, so the earlier approximation (own fold seed, own retriever) is gone; the config's user_template now carries the release template.
- W4415035710 (gender entropy): the released dataset stores a per-response entropy; character-level base-2 entropy reproduces it to three decimals (word-level does not), so the hook uses characters, as Algorithm 2 line 11 says, and the config records the deviation from the Sec. 3.1 wording.
- W7197053912 (ANCHOR-RE): the relation definitions come from `utils/text.py` `SemRep_LABEL2DEF` of the code release (the dict the release feeds to the model), not from SRDEF.RRF as the config guessed; the layout of the candidate slot inside the paper's Appendix A prompt (labels in the release's schema order + 'none', then '- label: definition' lines) is our choice and is recorded in task.approximation.
- W4399911213 (WikiContradict): Appendix C labels the instruction+examples 'System prompt' while Appendix D says the API calls used an empty system message with the prompt in the user turn; the config keeps the Appendix C split (noted in the config).
- W4410280647 (HLE): the full hook exists (per-type system prompt, o3-mini-2025-01-31 judge with the verbatim Appendix C.1.1 prompt and a json_schema response_format, accuracy = judged 'yes'); the judge model is live (dying 2026-10-23). The only blocker is the gated dataset; `--prepare` stops with a message naming the local path to fill.
- W7104384491 (PILOT-Bench): the GitHub release reads its prompts from `data/prompt/`, which is not in the repo (possibly inside the 55 MB HF tarball, unverified), and the paper's calls used OpenAI function calling to force the JSON list - the runner's request body cannot carry `functions`.
- Unparsable replies: W4404314294 removes them from the denominator (paper rule); W4411119490 scores them as 'ok', W4411112894 as NOT BIASED, W4417257719 as probability 0.5, W7197053912 and W4403370432 as an empty / 'none' prediction; the runner still reports the unparsed count.

## Runner defects and quirks hit

1. `NeedsHuman` identity: a hook that does `from tierb_runner import NeedsHuman` gets a second copy of the class (the runner runs as `__main__`), so `main()`'s `except NeedsHuman` would not catch it and the run would crash with a traceback instead of writing needs_human.txt. Work-around used in W4410280647: raise `sys.modules['__main__'].NeedsHuman`. Fix: inject `NeedsHuman` into the hook module namespace in `load_hook()` or move it to a small shared module.
2. A stale `runs/tierb/<wid>/needs_human.txt` survives a later successful `--prepare` (W7197053912 after the placeholder fix); `prepare()` should delete it on success.
3. Cost estimates disagree: `prepare()` counts 16 output tokens for letter/label parses and 120 for JSON, while the battery dry-run counts the body's `max_tokens` / `max_completion_tokens` (raised to at least 2048 for gpt-5/o-series even when the config asks for 64, W7131319772). Examples: W4411119490 $8.01 vs $60.57, W7131319772 $3.98 vs $12.57, W7197053912 $16.43 vs $42.01. The cap subset is decided on the smaller number.
4. Placeholder grammar: `items.<field>` must be the bare spec; any trailing annotation makes `render_placeholder` raise (my own W7197053912 first attempt). Prose belongs in `placeholders_prose`.
5. Set-level metrics (ROC-AUC, MCC, Welch t, micro-F1, positive-class F1) return `per_item=None`, so `result.json` has no `ci95` and no `original_inside_ci95` for those configs; a set-level bootstrap in `analyze()` (resample items, recompute via `hook.score`) would fill that.
6. `field()` in tierb_runner.py has a dead loop (`for k in row: pass`) - cosmetic.
7. Not a defect: the runner already fills placeholders in `prompt.system` (W4415035710's open point was stale) and already accepts `items.hf.configs` / `items.hf.splits` lists (used for W4411119490 and W4415035710 without a loader hook).
