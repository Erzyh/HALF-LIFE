# Hooks pass, group 2 (25 configs from data/tierb_triage/hooks_2.csv), 2026-09-07

Per-paper hooks (harness/tierb/hooks/<wid>.py) were written where the only blocker was a runner facility gap;
configs that no code can fix keep status needs_human with a precise open point. No model API was called and no
money was spent. Every hook was verified with `python tierb_runner.py <wid> --prepare --dry-run`, the first
rendered prompt was compared with the paper's prompt, and parse/score carry an inline self-test
(`python tierb/hooks/<wid>.py`). The PlanBench judge stage was exercised offline with a fake archived response.

## Counts

- ready: 9 (W7117377764, W4414494504, W4403885225, W4407571428, W4411080278, W4411119263, W4403882451,
  W4403786592, W4399404161)
- still needs_human: 16
  - image inputs the runner cannot send (6): W7166808309 (10 images per call, ~400 MB), W4415196225 (cartoon +
    caption; test_set.json also missing), W7164447524 (problem images, locally generated dataset), W7150802891 and
    W4414580657 (both also gated Hugging Face archives of 1.5-2 GB), W4404970691 (37 GB RVL-CDIP tarball plus
    Amazon Textract OCR)
  - protocols beyond one main + one judge stage (4): W4416033907 (target turn-1, challenger models, turn-2
    rebuttal), W4404782330 (web-search agent loop + trafilatura + official scorer with METEOR), W4403584145
    (sequential 50-agent simulation), W4411120335 (4-temperature sweep, which a hook cannot put into the request
    body, plus BERTScore/roberta-large)
  - metric needs a model outside the hook rules (1): W4404782508 (Level-3 matching score with all-MiniLM-L6-v2
    embeddings; the 6-variant expansion and L1/L2/L3 progress rates would be hook-expressible)
  - data not released / not downloadable (2): W7167154566 (the expert consensus labels of the 100-comment
    validation sample are not in the repository - see below), W4386395478 (111 MB archive, over the 100 MB limit)
  - dead auxiliary model + external API at scoring (1): W4411120175 (GPT-4-0613 post-processing, Semantic Scholar
    matching, 1.16 GB archive)
  - hook complete, one human approval left (2): W7140147579 (English-translation run of a Korean experiment; the
    Korean prompt is not printed), W4404986534 (adapted pairwise template; the judge prompt is not printed)

Ready est_usd: 537.37 USD by the triage CSV figures, 177.39 USD by prepare.json (same 9 configs; the two capped
configs W4399404161 and W4411119263 are recorded at their post-cap subsets of 39.91 and 39.97 USD - raise --cap
for the full 12,032 / 2,060-row sets, roughly 290 USD and 41 USD). The two "one approval left" configs would add
2.88 (W7140147579) and 29.93 (W4404986534) USD. Battery dry-run figures are higher for large max_tokens (see
runner notes).

## Table

| wid | status | hook functions | n_items | est_usd (csv / prepare.json) | note |
|---|---|---|---|---|---|
| W7167154566 | needs_human | none | 151 | 0.2 / - | gold labels not public: validation_results.json (n = 100, kappa 0.579 unweighted, exact 0.64) matches the paper, but that sample's expert scores are absent (human_score empty, answer-key 'Human Score' empty; the three annotator sheets cover a different 100-item sample and give kappa 0.23); kappa weighting and n-gram default (use_ngrams=False) resolved |
| W4386395478 | needs_human | none | 86 | 1.0 / - | fm_data_tasks tarball is 111 MB (> 100 MB limit), no other public copy; extraction path for a human documented in open_points |
| W7117377764 | ready | load_items, parse, score | 43 | 1.11 / 1.06 | 43 verified grants pinned via results/full_results.csv is_locatable == 1 (released M-2 errors over these rows = 23.39 km = Table 4); DMS -> decimal, haversine mean |
| W7166808309 | needs_human | none | 381 | 2.0 / - | 10 image parts per call |
| W4416033907 | needs_human | none | 594 | 4.0 / - | three-stage protocol with challenger models |
| W4404782508 | needs_human | none | 700 | 5.99 / - | L3 matching score needs sentence embeddings |
| W4414494504 | ready | load_items, render, parse | 225 | 7.0 / 8.9 | xlsx sheet parsed with pandas/openpyxl, JSON cells -> question/options/answer letter; query rendered as the Table 1 JSON object |
| W4415196225 | needs_human | none | 286 | 9.0 / - | image + caption; test ids file not located |
| W4403885225 | ready | load_items, render, parse, score | 1000 | 9.97 / 19.11 | 500 items x {orig, pert} rows; RR = agreement of the two [[A]]/[[B]] verdicts per item |
| W4407571428 | ready | load_items, render, parse, score | 200 | 12.0 / 13.0 | switched to the CORE-Dev cell (41.3 +/- 1.3; test labels only via the authors' endpoint); grids as rows of digits, options 'A. text' (serialisation not printed); gold {letter, choices}, letter-or-option-text scoring |
| W4411080278 | ready | load_items, parse, score | 1000 | 15.0 / 18.57 | four Table 1 vignettes transcribed into items.inline, x250 iterations; leading diagnosis = first listed item; keyword scoring with whole-word 'co' |
| W4411120175 | needs_human | none | 166 | 20.0 / - | aux_model_dead (GPT-4-0613) + Semantic Scholar API at scoring |
| W4411119263 | ready | load_items, render, parse, score | 2060 (2030 at cap) | 20.29 / 39.97 | both presentation orders; per-dataset accuracy then macro mean (Table 2 Avg.); per-item weights keep mean(per) = macro |
| W4403882451 | ready | load_items, render, parse, score, judge_requests, score_with_judge | 600 | 22.0 / 29.4 | the paper's own zero-shot query files (blocksworld 500 + blocksworld_3 100 = the /600 of Table 1) used verbatim; Blocksworld simulator reproduces 600/600 released llm_correct flags (241 correct = Table 1); judge stage = the repository's gpt-4o translation prompt (side file W4403882451_translation_prompt.txt, model gpt-4o-2024-08-06 assumed for the alias); without --judge the rule-based text_to_plan replica is used (254 vs the paper's 241 correct on the released replies) |
| W7140147579 | needs_human (hook ready) | load_items, parse, score | 100 | 24.0 / 2.88 | precedent = facts + claims (Table 10), F1 of Eqs. 1-2, plat-eng-mc + printed English prompt; approval of the translation approximation pending |
| W4403786592 | ready | load_items, parse, score | 1000 | 30.0 / 7.47 | SEV-4 prompt transcribed from the Figure 1 image (arXiv 2409.15687v2 p. 13); balanced 250/class seeded sample (Sec. 3.6); max_tokens 2 (Sec. 3.8); single-integer parse; BA = mean per-class recall |
| W7164447524 | needs_human | none | 339 | 30.0 / - | image inputs + locally generated dataset |
| W4404970691 | needs_human | none | 800 | 36.0 / - | Textract OCR + 37 GB images |
| W4404782330 | needs_human | none | 200 | 45.0 / - | web-search agent loop |
| W4404986534 | needs_human (hook ready) | load_items, render, parse, score | 5106 | 51.0 / 29.93 | LLMEval2 zip fetched from Google Drive (fields verified: dataset, query, response1, response2, human); both orders; agreement over valid judgements; template approval pending |
| W7150802891 | needs_human | none | 3004 | 60.0 / - | gated 1.5 GB image data, 6 images per call |
| W4414580657 | needs_human | none | 6000 | 90.0 / - | gated 2 GB image data, image per call |
| W4403584145 | needs_human | none | 20 | 100.0 / - | sequential multi-agent simulation |
| W4411120335 | needs_human | none | 109 | 130.0 / - | temperature sweep + BERTScore |
| W4399404161 | ready | load_items, render, parse, score | 12032 (1652 at cap) | 420.0 / 39.91 | 5-shot CoT block from the validation split per category (cot_content 'A: ' prefix removed); two-regex extraction with the paper's seeded random fallback (count logged) |

## Runner notes and defects

- prepare() recomputed the post-cap cost with estimate(reqs) (max_tokens-based) instead of out_guess, so the
  recorded est_usd after subsetting was inflated (W4399404161 first showed 218 USD for 1,652 items); this was
  patched in tierb_runner.py during the pass (by another group) and the two capped configs were re-prepared.
- prepare.json and the battery dry-run disagree whenever max_tokens is large: the battery counts max_tokens (or
  max_completion_tokens) as output per call, prepare uses out_guess. W7117377764: 1.06 vs 16.94 USD (o3,
  max_completion_tokens 16384); W4403882451: 29.40 vs 63.09 USD. The cap check in prepare uses the low figure, so
  a long-output run can stop at the battery cap before all items are answered.
- items.label_map / label_transform are applied only inside the runner's own load_items; a hook load_items
  bypasses them, so hooks must map labels themselves (done in W4403786592, W4411119263, W4407571428).
- Placeholder specs in prompt.placeholders must be bare machine specs (`items.post`); any annotation makes the
  default render fail with "placeholder spec not machine-readable" - prose belongs in placeholders_prose.
- The pricing table lacked the PlanBench translation judge model; `gpt-4o-2024-08-06` (2.50 / 10.00 USD per 1M)
  was added to harness/pricing.json so `--judge` can run for W4403882451.
- analyze() hands score_with_judge the archived main-stage records positionally (`used`, `texts`) while
  judge_responses is keyed by (id, seed_idx); hooks have to re-key by it["id"] / rec["seed_idx"] (undocumented).
- field() has a dead `for k in row: pass` loop (harmless).
