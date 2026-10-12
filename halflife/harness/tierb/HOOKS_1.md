# Tier B hooks, group 1 (hooks_1.csv, 25 configs) - 2026-09-07

Per-paper Python hooks (harness/tierb/hooks/<Wid>.py) that close runner facility gaps. No model API was
called: every hook was verified with `python tierb_runner.py <Wid> --prepare --dry-run`, the first rendered
prompt was checked against the paper text, and parse/score run inline unit tests (`python hooks/<Wid>.py`).

## Counts

- ready: 12 (hook written, --prepare ok, prompt renders as printed, scoring implemented)
- still needs_human: 13
  - data not released / gated: 4 (W4411119333 Psych-ADR file not distributed, W4404781531 Google-Form request, W4405768494 gated HF dataset, W4409361799 MathKnowCT not found)
  - image or video input (text-only runner): 3 (W4405432557, W7140099019, W4405355440)
  - prompt exists only as a figure image: 1 (W4404342216)
  - execution sandbox / multi-call protocol: 2 (W4406058824 sequential sub-steps + code execution, W4403882351 sandbox for 3,300 programs)
  - auxiliary model not callable or outside the hook contract: 2 (W4416034538 self-hosted Qwen2.5-72B judge, W4411119226 HF transformer classifier + figure-only angles)
  - inputs must be assembled from six external datasets with unprinted slot wordings: 1 (W4411120447)

Ready est_usd as staged (runner --prepare estimate, <=400 output tokens per free-text call, $40 cap applied):
0.15 + 0.42 + 0.02 + 0.05 + 12.49 + 8.33 + 3.79 + 9.16 + 29.40 + 6.97 + 39.98 + 39.93 = **150.7 USD** for the
main stages. Two configs exceed the $40 cap and are subset by the runner at prepare time (W4403443823 -> 2,586 of
3,737 sentences, full set ~$58; W4403570177 -> 2,989 of 10,067 pairs, full set ~$135): uncapped total ~263 USD.
The dry-run lines that count the full max_tokens sum to ~290 USD as staged. W4404985489 adds a judge stage of
roughly 25-35K one-token gpt-4-turbo calls (~25-30 USD).

## Table

| wid | status | hook functions | n_items | est_usd | note |
|---|---|---|---|---|---|
| W4404792825 | ready | parse, score | 10 (x3 seeds) | 0.15 | sum of 10 Likert ratings per administration; mean over administrations, no gold (target 31.36) |
| W7134094238 | ready | parse, score | 30 (x3 seeds) | 0.42 | four deck probabilities; 100 sampled choices per reply (seed 20260907), KL vs uniform (+ chi-square p, std printed) |
| W7166799942 | ready | load_items, parse, score | 2,610 utterances / 280 calls | 0.02 | dialogue group-by, k labels per reply, per-utterance accuracy (weighted F1 printed) |
| W7135428702 | ready | render | 1,024 | 0.05 | per-language prompt block from user_template_by_language; all 8 languages vs Table 1 (0.73) |
| W4416034345 | ready | load_items, render, score | 978 | 12.49 | nine hf configs + one_shot_examples turn (user/assistant), rouge_score-default rougeL, macro over pairs |
| W4402345509 | ready | load_items, parse, score | 199 (x3 seeds) | 8.33 | options composed (ideal + distractors + 'Insufficient information'), seeded permutation, gold letter, [ANSWER] tag parse |
| W4416034777 | ready | parse, score | 100 (x3 seeds) | 3.79 | final single-action segment; TVD from uniform over valid replies |
| W4404985489 | ready | load_items, parse, judge_requests, score_with_judge | 589 chunks (2,083 annotations) | 9.16 (+ judge ~25-30) | 'name \| description \| value' parse; Figure 6 GPT-4 Turbo y/n judge on per-chunk Cartesian pairs; pooled P/R/F1 |
| W4403758464 | ready | load_items, parse, score | 600 (x3 seeds) | 29.40 | 500 + 100 PlanBench instances, zero-shot statement cut from the one-shot query, rule-based extractor mirrored, VAL replaced by an exact Blocksworld simulator (600/600 ground-truth plans validate) |
| W4416037849 | ready | load_items, parse, score | 2,371 references / 389 calls | 6.97 | seeded 40/60 reference draw per query, 0/1 sequence parse, RP = F1 of the relevant class (IS, CE printed) |
| W4403443823 | ready | load_items, parse, score | 3,737 (cap -> 2,586) | 39.98 (full set ~58) | TroFi Example Base fetched from the SFU page (human-tagged N/L), per-item target-word line, metaphorical precision, missing label = incorrect label |
| W4403570177 | ready | load_items, parse | 10,067 (cap -> 2,989) | 39.93 (full set ~135) | 37 subcategory files concatenated, dialog history rendered, seeded chosen/rejected -> A/B coin flip, last [[A]]/[[B]] |
| W4411119226 | needs_human | - | 120 | 4.00 | scorer needs a HF transformer classifier (outside stdlib+numpy/pandas) and Russell (1980) angles (Figure 2 is an image); Figure 1 prompt decoded from a font-shifted extraction |
| W4411119333 | needs_human | - | 239 | 7.00 | Psych-ADR file not distributed (README: 'You will need the dataset file') |
| W4404781531 | needs_human | - | 807 | 12.00 | dataset on request via Google Form; rationale format unknown |
| W4406058824 | needs_human | - | 338 | 15.00 | sequential stateful sub-step calls + code execution against test_data.h5 |
| W4405432557 | needs_human | - | 40 | 20.00 | image input (GANFD faces) + embedding model and mixed-model fit |
| W7140099019 | needs_human | - | 601 | 27.00 | image input (diagram); literal '\boxed{your_answer}' rejected by the runner's slot check; gemini judge not callable |
| W4416034538 | needs_human | - | 625 | 30.00 | judge = self-hosted Qwen2.5-72B-Instruct (not callable through the battery); 625 of 9,782 items public |
| W4405768494 | needs_human | - | 3,339 | 35.00 | MichiganNLP/Chumor is gated |
| W4403882351 | needs_human | - | 165 | 50.00 | execution sandbox for 3,300 programs; 20 samples per problem for 1@3 |
| W4409361799 | needs_human | - | 2,400 | 60.00 | MathKnowCT not public; five-call multi-agent protocol with code execution |
| W4404342216 | needs_human | - | 4,196 | 80.00 | EQINFER prompt is Figure 11 (image); protocol (one-by-one vs whole-list) unfixed |
| W4405355440 | needs_human | - | 3,268 | 98.00 | video frames + ASR input; annotation JSON behind a Google sign-in |
| W4411120447 | needs_human | - | 34,416 | 344.00 | 30 subsets must be assembled from six source datasets; aspect/slot wordings unprinted |

## Runner defects and observations

1. Cost-estimate inconsistency: `prepare()` decides the cap subset with `out_guess` (<= 400 output tokens per free-text call), while the battery's dry-run line counts the full `max_tokens`, so the two printed figures differ by 2-3x (W4403443823: prepare 39.98 vs dry-run 88.39 for the same 2,586 items). The committed runner also recorded the post-subset `est_usd` with the full `max_tokens` (88.39 above a $40 cap); the working-copy runner already applies the same output guess after subsetting (est_usd 39.98 / 39.93 on the final run). Hook configs record both figures (`cost.est_usd_prepare`, `cost.est_usd_dryrun_max_tokens`).
2. The bootstrap CI exists only for mean-of-per-item metrics. Hooks whose metric is set-level (F1, precision, KL, TVD) return `per_item = None`, so `ci95` and `original_inside_ci95` are absent; the runner's own `micro_f1` returns a per-item accuracy list, so its CI is an accuracy CI mislabelled as F1.
3. The unfilled-slot check (`render.fill`) rejects literal braces in a template (W7140099019 `\boxed{your_answer}`); a hook `render()` bypasses it but the mini-language has no escape.
4. When a hook needs the judge stage and `runs/<Wid>/judge/` does not exist, `analyze()` falls back to `hook.score()`; hooks cannot raise the runner's `NeedsHuman` (the runner runs as `__main__`, so importing `tierb_runner` would create a second class), so W4404985489 raises a plain RuntimeError with the instruction to run `--judge` first.
5. `prepare()` silently drops items whose `render()` raises after the first item (`continue` without a count); a hook bug on a later row would shrink the set unnoticed. A dropped-item counter in prepare.json would help.
6. GitHub API folder listings (api.github.com) hit "403 rate limit exceeded" during this session; hooks that need multi-file folders should carry the file list (W4403570177 does) and fetch raw.githubusercontent.com only.
7. The SFU TroFi page refuses the runner's user agent on the directory (403) but serves the file with a browser user agent; the hook sets one.
8. Reasoning bodies drop `seed` (W4416034345 asked for seed 2025) and pass only `reasoning_effort` / `max_completion_tokens`; documented in the config, not changed.
9. Cosmetic: `field()` in the runner contains a dead loop (`for k in row: pass`).

## Files

- hooks: harness/tierb/hooks/{W4404792825,W7134094238,W7166799942,W7135428702,W4416034345,W4402345509,W4416034777,W4404985489,W4403758464,W4416037849,W4403443823,W4403570177}.py
- cached data (downloaded once by load_items): external/data/tierb_items/<Wid>/ (SLDS 9x2 parquet, RMB 37 json, TroFi txt, PlanBench 2 json, CRAB 4 jsonl, MELD csv, LitQA2 parquet, SciVar json)
- prepared runs: runs/tierb/<Wid>/{items.jsonl,requests.jsonl,prepare.json}
