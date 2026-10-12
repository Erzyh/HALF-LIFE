# Tier B batch-1 triage, group 2 (8 papers, 7 cells)

Date 2026-09-09. No model API calls were made; all re-analyses run on the archived replies (`runs/tierb/<wid>/calls.jsonl`).
Network use was limited to public data files (MultiPragEval `test_suite.csv`, the PlanBench `blocksworld_3` results file, the
RealWorldQuestioning and PhysiCo parquet files, the MMLU-Pro dataset card). Audit scripts live in the session scratchpad
(`pb_audit*.py`, `mpe_audit.py`, `haluj_audit.py`, `mmlu_audit.py`, `physico_audit.py`, `gender_sink_audit.py`).

| wid | class | original | re-run before | re-run after fix | n | what was wrong / what changed |
|---|---|---|---|---|---|---|
| W4403882451 (Strawberry Fields, PlanBench BW zero-shot) | **DEFECT** (scorer choice), fixed | 40.1 (241/600) | 54.67 (gpt-4o translation judge; seeds 52.3 / 57.0 / 54.7) | **34.89** (rule-based extraction; seeds 34.2 / 35.2 / 35.3; CI seed 0 [30.5, 38.0]) | 600 x 3 | The judge (LLM translation) is not the paper's extraction for this cell: the released `extracted_llm_plan` fields are reproduced 600/600 by the repository's pre-fix rule-based extractor, and the o1 paper's footnote 5 reserves the translation for o1. Hook now returns the rule-based number; pre-fix 30.8 and judge 54.7 are kept in `judge_summary.json`. |
| W4403758464 (LLMs Still Can't Plan, same cell) | **DEVIATION** (with reference-cell caveat) | 40.1 (241/600) | 35.89 (seeds 35.7 / 35.2 / 36.8) | 35.89 (unchanged) | 600 x 3 | Pipeline = repository's current rule-based extractor. The paper's 241 came from the pre-fix version that silently dropped markdown-bold action lines; the current extractor scores the paper's own released replies 254/600 = 42.3. Under a parenthetical-tolerant extraction the paper's replies (55.2) and ours (54.8) are equal: the model plans as well as before, but 87% of our replies (vs 65% of the paper's) add parenthetical block mentions that the arity check of the rule-based extractor rejects. |
| W4415035710 (gender entropy bias, Education) | **DEVIATION** (inside the metric's own noise) | t = 2.00 (p = 0.04) | -0.23 (seeds -0.26 / -0.36 / -0.07) | - | 158 x 3 (79 F vs 79 M) | Pipeline verified on the released data: the dataset's `shannonentropy_response_sample_2` column gives Welch t(F-M) = +2.005 = Table 4; recomputed character-level entropy reproduces it exactly (word-level would give -0.96), so entropy definition, sign convention (Female minus Male) and `metric.scale = 1` are right. A single-iteration t-statistic has sampling SD ~ 1; the 2.2 difference is ~1.6 SD of the difference of two independent draws. |
| W4404792825 (Sink or Swim, GSE base GPT-4o) | **DEVIATION** (instruction line reconstructed) | 31.36 | 29.0, CI [29, 29] | - | 10 administrations x 3 | All 30 replies are byte-identical (one fingerprint): every item rated 3 except item 2 rated 2 -> total 29. The unit (one administration = one 10-item questionnaire, 10-40 scale) is the paper's; the degenerate CI is zero variance at temperature 0.1, not a bootstrap-unit error. The paper's decimal mean implies varying replies under its unprinted instruction wording. |
| W4407571428 (PhysiCo CORE-Dev, GPT-4 text) | **DEVIATION** (grid serialisation unverifiable) | 41.3 +/- 1.3 | 35.67 (seeds 33.5 / 37.0 / 36.5; CI seed 0 [27, 40]) | - | 200 x 3 | Reference cell is right (Table 3 text-only GPT-4 = gpt-4-turbo-2024-04-09, CORE-Dev). Parse verified on all 600 replies: 593 end with an 'X. option' line, 5 name the option in prose (picks equal the stated choice), 0 unparsed/truncated; a last-line-only rule gives the identical 35.67. Only the grid/option serialisation (not printed anywhere) is an assumption. |
| W4404781158 (MultiPragEval, GPT-4 English Avg.) | **DEFECT** (reference cell / item set), fixed | 75.28 | 81.44 (all 300 units) | **76.94** (240 implicature units; seeds 76.7 / 78.3 / 75.8; CI seed 0 [70.8, 82.1]; 75.28 inside) | 240 x 3 (was 300 x 3) | Table 5 Avg. is the mean of the four maxim scores (65.00 / 83.89 / 82.22 / 70.00); the 60 literal-meaning units are a separate column (paper 100.00, ours 99.4). `items.filter = type != 'literal'` added; re-prepared (CSV re-fetch, no calls) and re-analysed. Per maxim ours vs paper: quantity 65.0 / 65.00, quality 84.4 / 83.89, relation 88.3 / 82.22, manner 70.0 / 70.00. |
| W4406058598 (Halu-J, GPT-4o ME-FEVER) | **DEVIATION** | 0.83 | 0.885 (seeds 0.887 / 0.886 / 0.881) | - | 1,238 x 3 | 3-way label accuracy as in Sec. 6.2; label map 0/1/2 -> True/Neutral/False confirmed by the confusion matrix (swapping 1<->2 would give 0.715); all 3,714 replies start with `{` and parse with plain `json.loads` (strict = lenient), none truncated; 7-10 evidences per prompt as in Sec. 4; same snapshot. Residual +0.055 is unexplained by the pipeline (paper's decoding temperature and evidence order not printed). |
| W4399404161 (MMLU-Pro, GPT-4-Turbo overall) | **DEVIATION** | 63.7 | 67.98, CI [65.7, 70.2] | - (reweighted to the full category shares: 67.4) | 1,652 of 12,032 | Cost-cap subset is a seeded random draw over the whole set (ids 85..12244; category shares within 1.7 points of the full set). Extraction follows the paper (1,627 primary regex, 0 secondary, 25 random fallbacks, 0 truncated at 4,000 tokens). Gap is entirely in the quantitative subjects: math 75.4 vs 62.8, physics 72.7 vs 61.0, engineering 50.8 vs 35.9, while law 45.2 vs 51.2, history 64.8 vs 67.7, psychology 77.7 vs 78.3. |

## Per-paper notes

### W4403882451 and W4403758464 (same PlanBench cell, 241/600 GPT-4 Turbo zero-shot)

- The two batteries are the same: 598/600 prompts byte-identical (the results files hold instance ids 1-500 / 1-100, the prompt files 2-501 / 2-101, so each run has one instance per file the other lacks). Both runs use gpt-4-turbo-2024-04-09, temperature 0, 3 seeds.
- Which scoring is the paper's: the released `results/{blocksworld,blocksworld_3}/gpt-4-turbo_chat/task_1_plan_generation_zero_shot.json` carries `extracted_llm_plan` and `llm_correct` for all 600 instances. The pre-fix repository extractor (`text_to_plan_blocksworld` without `line.replace('*','')`, cached as `external/data/tierb_items/pb_old_text_to_pddl.py`) reproduces every released plan (600/600) and the 241 flags; the current extractor (with the `*` strip) gives 254/600 on the same replies; a parenthetical-tolerant extraction gives 331/600 = 55.2. The o1 paper says the GPT-4o-mini translation was introduced because o1 ignores the format ("for previous models, the model itself enforced the desired plan format").
- Why the two hooks disagreed: purely the scorer. Rule-based extraction of the W4403882451 replies gives 34.9 (its judge gave 54.7); rule-based extraction of the W4403758464 replies gives 35.9. The judge agrees with a parenthetical-tolerant rule extraction in 1,790/1,800 replies, so 54.7 is the model's true plan validity, not the paper's metric.
- What the rule-based extractor drops (arity check: an action line must mention exactly 1 or 2 "<colour> block" strings):
  - "2. Put down the orange block on the table (now the orange block is on the table and clear, and the blue block is clear)." -> two blocks for put-down, line skipped.
  - "3. **Pick up the yellow block.** (The yellow block is clear and on the table, and your hand is empty after putting down the blue block.)" -> skipped.
  - Paper's own reply, instance 1: "2. **Put down the blue block on the table.**" -> dropped by the pre-fix extractor because of the bold markers; released plan `(unstack b c) (stack c b)`, marked incorrect.
- Judge artefacts (10/1,800): e.g. reply "1. Unstack the orange block from the yellow block." was translated as "(stack orange yellow)".
- Style shift vs the paper's replies: only 27/600 of our seed-0 replies are identical to the released ones (so the paper's "GPT-4 Turbo" replies were not temperature-0 gpt-4-turbo-2024-04-09 output); 86-89% of ours contain parentheticals vs 65% of the paper's; 24% vs 14% contain markdown bold. Under the pre-fix extractor our replies score 30.2-33.0.
- Fix applied (W4403882451 hook): `score_with_judge` returns the rule-based number and writes `judge_summary.json` (rule current 34.2 / 35.2 / 35.3, pre-fix 30.2 / 30.8 / 31.5, judge 52.3 / 57.0 / 54.7); `parse(strip_star=False)` added. Config: `metric.judge`, `task.approximation`, `output.parse`, `hook`, notes. W4403758464: notes only, number unchanged.

### W4415035710 (gender entropy)

- Released columns (Education, 158 rows): sample_1 t = -1.444 (paper ChatGPT-3.5-turbo -1.44), sample_2 +2.005 (ChatGPT-4-turbo 2.00), sample_3 -0.243 (Llama-3 -0.24), sample_4 -1.176 (DeepSeek-R1 -1.17); sign = Female minus Male; Welch = Student (equal n).
- Our three iterations: character entropy F 4.534 vs M 4.537 bits (t -0.26 / -0.36 / -0.07); word-level entropy would give +0.37 / +0.75 / +0.05; reply length t +0.06 / +1.21 / +0.36. No parsing involved (free text).
- Note: the runner's auto-scale heuristic (x100 when original > 1.5 and re-run <= 1) would have fired on a t-statistic; the config's explicit `scale: 1` prevents it.

### W4404792825 (Sink or Swim)

- Reply (x30): "1. 3\n2. 2\n3. 3\n4. 3\n5. 3\n6. 3\n7. 3\n8. 3\n9. 3\n10. 3".
- Paper protocol (Sec. 4.2): 10 runs per prompt and placement for GPT models, GSE on a 40-point scale, Table 2 Base 31.36; our unit and score range match. A different instruction line could only be tested with new calls (not run).

### W4407571428 (PhysiCo)

- Prompt = Figure 7 system + user text; options "A. text" one per line; grids as rows of space-separated digits (the parquet holds arrays only).
- Pick sources over 600 replies: 593 tail letter pattern, 1 "answer is X", 1 "(X)", 5 option text. Examples: "Therefore, the most suitable choice based on the patterns observed in the grids is: C. wave interference." (gold D; model wrong, parse right); "Your response should end with choice B, diffraction of waves." (text fallback, pick B = the stated choice).
- Pick distribution A 105 / B 153 / C 168 / D 174 against gold 45 / 54 / 61 / 40 (x3): no parser position bias.

### W4404781158 (MultiPragEval)

- CSV types: quantity / quality / relation / manner / literal, 60 each, 12 per answer letter. Gold and prompts match the CSV exactly.
- First-"(X)" vs last-"(X)" differ in 43/900 replies; first is the better rule on 4 of 5 types (e.g. id 45: "...is: (D) Emily had lunch at 12:00. ... The other" - the later (B) is a rejected option).
- Files changed: config (`items.filter`, `task.n_items 240`, `subset_rule`, `metric.definition`, notes); `items.jsonl` / `requests.jsonl` / `prepare.json` regenerated for the 240 ids; `calls.jsonl` untouched (the 60 literal replies remain archived).

### W4406058598 (Halu-J)

- Confusion (gold -> pred, 3 seeds): True 2446 / 45 Neutral / 47 False; False 789 / 21 Neutral / 39 True; Neutral 51 / 190 False / 86 True. Recall True 0.964, False 0.929, Neutral 0.156.
- Examples: gold Neutral -> "False": "...'Beautiful' reached number two on the 2001 charts. However, evidence 7 indicates that 'Beautiful' was released in the latter part of 2002"; gold False -> "True": "The claim that 'Gone with the Wind is a book' is supported by evidence" (ids 22-24); gold True -> "False": "Naomi Watts was not in a film directed by Tom Tykwer ... evidence 6 clearly states that Naomi Watts was in 'The International'" (misleading evidence, by design of ME-FEVER).

### W4399404161 (MMLU-Pro)

- Subset shares (subset / full): math .111/.112, physics .107/.108, chemistry .093/.094, law .075/.092, engineering .076/.081, psychology .073/.066, others within 0.7 points.
- Random fallbacks (25): replies that refuse to pick, e.g. "Therefore, the answer cannot be determined from the information given.", "The answer is (X), where X is the option closest to the calculated value of h.", "The answer is [1, 1]." 13 of them would be caught by the repository script's third-stage last-letter regex, which the paper does not describe.
- Dataset changelog after the paper (2024-07 to 2024-09): a handful of corrected math/engineering answers - too few for a 12-15 point gap; the pattern (quantitative subjects only) is consistent with the paper's run losing long CoT answers to truncation or extraction failure.

## Runner-level observations

1. `analyze()` switches to `hook.score_with_judge` whenever a `judge/` directory exists; the primary scorer is not chosen by the config. This is how a diagnostic translation stage became the headline number for W4403882451. A config field (e.g. `metric.primary_scorer: rule | judge`) would make this explicit.
2. The auto-scale heuristic in `analyze()` (`100.0 if original > 1.5 and re-run <= 1.0`) fires for any unbounded or signed metric that lacks `metric.scale` (t-statistics, deltas, counts). Restrict it to accuracy-like metric names or require an explicit scale.
3. A zero-variance per-item list yields a point CI ([29, 29]); `result.json` should also record the number of distinct reply texts / fingerprints so this is recognisable as deterministic output.
4. Changing the item set of an archived run (MultiPragEval) requires `--prepare`, which re-fetches the source and rewrites `items.jsonl` / `requests.jsonl`; applying `items.filter` at analyze time (or a `--reanalyze` that keeps the request files) would be cleaner.
5. `runs/tierb/batch1_tierb_summary.json` still carries the pre-fix values for W4404781158 (81.44) and W4403882451 (54.67) and needs regenerating by the queue's summary step.
6. Cosmetic: the two PlanBench batteries differ in one instance per file (1-500/1-100 vs 2-501/2-101) because the hooks read the results files and the prompt files respectively.
