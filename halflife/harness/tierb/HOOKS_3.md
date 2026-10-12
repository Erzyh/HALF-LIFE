# Hooks pass, group 3 (25 configs from data/tierb_triage/hooks_3.csv), 2026-09-07

Per-paper Python hooks (harness/tierb/hooks/<wid>.py) were written where a runner facility gap was the only
blocker; configs whose blocker no code can fix keep status needs_human with a precise open point. No model API
was called; every hook was checked with `python tierb_runner.py <wid> --prepare --dry-run`, its first rendered
prompt was compared with the paper's prompt, and parse/score functions carry an inline self-test
(`python tierb/hooks/<wid>.py`). Judge stages were exercised offline by feeding a fake archived response to
`judge_requests` and inspecting the request body.

## Counts

- ready: 8 (W4407374917, W4416339332, W4414758400, W4406058598, W4416034223, W4416035547, W4399317891, W7161421448)
- still needs_human: 17
  - image inputs, which the runner cannot send (4): W4397048985, W4404783148, W7166808082, W7140124165 (also gated)
  - items not released or requiring human rebuilding / extraction (6): W4404518515 (OCR of court transcripts, hand-built
    gold), W4405425991 (ProteinQA test split not released), W7164447651 (corpus must be rebuilt from leaderboard files,
    trajectory serialization not printed), W7155245470 (1,281-conversation subset not released; ground truth needs a
    separate GPT-4.1 grading pass and a Llama classifier), W4410417118 (45 vignettes only in supplementary material /
    Zenodo 10.5281/zenodo.12805048, which blocks scripted access), W4412889855 (Drive zip unverified, ACE05 LDC-gated,
    10-shot demonstrations from source training sets)
  - prompt not printed / policy decision on a code-release prompt (3): W4404782941 (three exemplar Reason passages
    abbreviated in Table 3, not in the repository), W4412944528 (Vanilla prompt only in code/vanilla.py), W4412944996
    (judge GRADER_TEMPLATE only in the release repository)
  - protocol beyond one main + one judge stage (1): W4412888091 (two chained judge calls per item)
  - dead auxiliary model + unprinted aggregation constants (1): W4403851744 (examiner gpt-4-1106-preview)
  - human-graded outcome needing a judge choice + unverified figshare source (1): W4402952718
  - sources above the 100 MB hook download limit and a $500 budget (1): W4404783788

Ready est_usd (prepare.json): 1.37 + 1.06 + 0.94 + 34.79 + 4.35 + 1.34 + 100.46 + 100.26 = 244.57 USD for the main
stages. The two values near 100 are the post-cap figures of the runner defect described below (the battery stops at
the 40 USD cap, so the effective main-stage spend is about 124 USD). Judge stages come on top: OR-Bench about 40 USD
(3,231 judge calls), ToM about 1-20 USD (300 o4-mini identification calls), implicit bias about 65 USD (3,219
analysis calls); a 25-replicate pilot of W7161421448 (task.replicates = 25) costs about 18 USD for both stages.

## Table

| wid | status | hook functions | n_items | est_usd (prepare.json / battery dry-run) | note |
|---|---|---|---|---|---|
| W4407374917 | ready | parse, score | 100 | 1.37 / 1.37 | list of 10 floats, binarized at 0.5, per-species accuracy averaged; invalid replies counted and excluded |
| W4416339332 | ready | load_items, parse, score | 66 | 1.06 / 2.31 | U.S. vote derived from vote.favour/against/abstention (33/27/6); weighted F1 with a seeded bootstrap CI in custom_metric.json |
| W4414758400 | ready | parse, score | 25 | 0.94 / 9.26 | stories split on numbered headings, stated gender by explicit gender words / pronouns; female share, gold-free; flagged stories counted |
| W4406058598 | ready | render, parse | 1,238 | 34.79 / 85.15 | evidences collected by field prefix, per-instance seeded shuffle, numbered; label map 0/1/2 -> True/Neutral/False confirmed on the rows |
| W4416034223 | ready | load_items, parse, score | 216 | 4.35 / 40.28 | 15 IFEval checkers re-implemented (strict, all five must pass); regex stand-ins for nltk punkt / word_tokenize, langdetect skipped |
| W4416035547 | ready | load_items, render, parse, score, judge_requests, score_with_judge | 100 | 1.34 / 21.65 (+ judge) | MATH-500 items = the repository's random.seed(42) draw reproduced exactly; stage 1 target solution, judge stage = Appendix C.2 identification by the same o4-mini; gold constant (A) |
| W4399317891 | ready | parse, score, judge_requests, score_with_judge | 1,077 of 1,319 (cap subset) | 100.46 post-cap (defect) | Appendix S judge prompt verbatim, judge gpt-4-turbo-2024-04-09 stands in for the undated GPT-4; rejection rate = direct + indirect refusals; Appendix M keyword rate printed as the cross-check |
| W7161421448 | ready | load_items, parse, score, judge_requests, score_with_judge | 3,219 of 5,000 (cap subset) | 100.26 post-cap (defect) | 20 prompts x 250 replicates expanded by load_items; Appendix 1 question prompt verbatim as the judge; odds ratio with Woolf CI in custom_metric.json; params.seed removed |
| W4410417118 | needs_human | - | 450 | 1.0 | vignettes and gold only in supplementary material / Zenodo (403 to scripts); set of 45 must be confirmed by a human |
| W4397048985 | needs_human | - | 210 | 8.0 | many-shot image classification (up to 855 images per request) |
| W4404783148 | needs_human | - | 1,240 | 10.32 | image input (VIVA) |
| W4412888091 | needs_human | - | 250 | 13.24 | Entity Correctness needs two chained judge calls (Figure A11 extraction, then A12 scoring) |
| W7164447651 | needs_human | - | 295 | 15.0 | tau2-bench trajectories must be rebuilt from leaderboard files; serialization not printed |
| W4412889855 | needs_human | - | 1,000 | 20.0 | RUIE-Bench.zip on Drive unverified; ACE05 gated; demonstrations need the training sets |
| W7166808082 | needs_human | - | 102 | 20.44 | image input; Turtle emulator scorer |
| W4404782941 | needs_human | - | 742 | 22.0 | exemplar Reason texts of Table 3 unrecoverable (repository prompt differs; not the CSV gold_reason); items.file_url and columns now recorded |
| W4412944528 | needs_human | - | 1,650 | 25.0 | Vanilla prompt not printed (code release only) or switch to the AFCE row (two-call protocol) |
| W4405425991 | needs_human | - | 1,025 | 31.0 | ProteinQA test split not released; FASTA per protein |
| W7140124165 | needs_human | - | 3,067 | 46.0 | gated dataset (manual approval, CC-BY-ND) and image input |
| W4402952718 | needs_human | - | 900 | 54.0 | paper graded by human reviewers: judge model must be chosen; figshare private link unreadable to scripts |
| W7155245470 | needs_human | - | 1,281 | 60.0 | subset not released; ground truth needs a ~13k-call GPT-4.1 pass and a Llama-3.1-8B classifier |
| W4412944996 | needs_human | - | 3,000 | 92.58 | judge prompt (GRADER_TEMPLATE) not printed in the paper; human must approve the repository template |
| W4403851744 | needs_human | - | 1,667 | 100.0 | examiner gpt-4-1106-preview (repository default) is dead; Diagnosis denominator and InfoGatherQA configuration unprinted; HF JSON keys verified |
| W4404518515 | needs_human | - | 50 | 150.0 | case list, OCR and gold juror lists must be built by hand |
| W4404783788 | needs_human | - | 1,930 | 500.0 | LongBench data.zip 114 MB and InfiniteBench 298 / 186 MB exceed the hook download limit; budget |

## Config edits

- W7161421448: model.params.seed removed (one fixed seed for all requests would make the replicates near-identical and
  the hook cannot set a per-request seed), model.seeds = 1, task.replicates = 250, n_items 5,000; open point = budget
  (full design ~180 USD vs a 25-replicate pilot ~18 USD).
- W4416035547: items switched to HuggingFaceH4/MATH-500 with the repository's 100 indices (sampled_data_indicies.py);
  subset_rule paper-defined; metric.judge = the identifier call; open point = the index reproduction assumes the
  CCP-sensitive-prompts dataset still has 1,360 rows.
- W4414758400, W4399317891: metric.scale set to 100 (hooks return fractions; the paper reports percent).
- W4404782941: items.file_url and verified columns added (data.csv, 742 rows) although the status stays needs_human.
- All 17 needs_human configs: open_points rewritten to name the exact blocker and the public-record facts found.

## Runner defects and limitations hit

1. Post-cap cost estimate: prepare() computes the cap fraction from the out_guess estimate but recomputes est_usd
   after subsetting with battery.estimate(reqs), which bills max_tokens per call; prepare.json then records
   est_usd about 100 USD for a 40 USD cap (W4399317891: 1,077 items kept, W7161421448: 3,219 items kept) and the
   battery stops at the cap with roughly 40 % of the subset archived. Use the same estimator in both places.
2. prepare.json est_usd and the --dry-run estimate differ by 2-8x for every config (out_guess vs max_tokens billing;
   e.g. W4406058598 34.79 vs 85.15); the two numbers should be labelled or unified.
3. score / score_with_judge are called per seed slice, so a statistic pooled over replicates (the odds ratio over 250
   stories per condition) needs the load_items expansion trick (replicate encoded in the item id, seeds = 1).
4. Hooks cannot touch the request body (render returns messages only): no per-item seed or parameters; W7161421448
   had to drop params.seed. A body(cfg, row, msgs) hook or a per-row params override would close this.
5. The bootstrap only supports per-item means; ratio and F1 statistics (odds ratio, weighted F1) get ci95 = None and
   the hooks write custom_metric.json side files with their own seeded CIs.
6. analyze() auto-scales only when the value is <= 1 and the original > 1.5; hooks that return fractions for
   percent-valued claims need metric.scale = 100 set explicitly.
7. Hooks cannot import tierb_runner without re-executing it as a second module (the runner runs as __main__), so the
   HF-parquet loader is duplicated in hooks/W4416035547.py; a library split would avoid that.
8. Minor: data/tierb_triage/hooks_3.csv carries a UTF-8 BOM (open with utf-8-sig); field() in the runner has a dead
   `for k in row: pass` loop; the built-in 'label from set' parse returns the first label in set order rather than
   the first in the reply (the UNSC hook parses itself).
