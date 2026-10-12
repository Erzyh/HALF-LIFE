# Tier B run configs, group 7 (11 papers)

Source list: `halflife/data/tierb_triage/config_7.csv`. Configs: `halflife/harness/tierb/configs/<wid>.json` (schema in `CONFIG_SCHEMA.md`), hooks in `halflife/harness/tierb/hooks/<wid>.py`. Prompts were copied from the extracted texts in `halflife/external/papers_tierb/`; item sources were checked with small HTTP requests and, where a file was needed, downloaded into `halflife/external/data/tierb_items/<wid>/` (largest: 19.1 MB, the LiveCareer resume parquet). No model API was called. Date of the checks: 2026-09-19.

## Counts by status

| status | n |
|---|---|
| ready | 4 |
| needs_download_check | 0 |
| needs_human | 7 |
| **total** | **11** |

Total estimated API cost of the four ready configs: **~$266** (W4403574994 $0.94, W7169474262 $4.50, W4416683695 $130, W4411120580 $131; seeds included, judge stage included for W4416683695). The seven blocked configs would add ~$700 if their obstacles were ever cleared.

## Configs

| wid | status | model | seeds | task | n_items | est $ | hook | open points | title |
|---|---|---|---|---:|---:|---:|---|---|---|
| W4403574994 | ready | gpt-4-turbo-2024-04-09 | 3 | mcq | 133 | 0.94 | yes | direction of the Table 4 axis (52.97 vs 47.03) | Measuring Spiritual Values and Bias of Large Language Models |
| W4411120021 | needs_human | gpt-4o-2024-05-13 | 3 | other | 60 | 12 | no | ToolQuery is an interactive AgentBoard environment; episode loop outside the runner | xLAM: A Family of Large Action Models to Empower AI Agent Systems |
| W4416035030 | needs_human | gpt-4.1-nano-2025-04-14 | 3 | generation | 1703 | 4 | no | haystacks and needle sentences unpublished; metric is a conditional-logit odds ratio | Conflicting Needles in a Haystack: How LLMs behave when faced with contradictory information |
| W7169474262 | ready | gpt-4-turbo-2024-04-09 | 3 | generation | 124 | 4.5 | yes | headline surprisal needs the 44-model field; only self-distinctness is within-model | The One-Word Census: Answer-Choice Conformity Across 44 Language Models |
| W4404782618 | needs_human | gpt-4o-2024-05-13 | 3 | classification | 459 | 35 | no | dataset images still "coming soon"; multimodal input; SoV pipeline unreleased | Visual Prompting in LLMs for Enhancing Emotion Recognition |
| W4411120015 | needs_human | gpt-4o-2024-05-13 | 3 | classification | 417 | 30 | no | two prompt slots come from an unreleased GAT and comment selector; dataset of the 96.7% not named | Moderation Matters: Exploring LLMs for Effective Rumor Detection on Social Media |
| W4416683695 | ready | gpt-4-turbo-2024-04-09 | 1 | generation | 2243 | 130 | yes | A/B order unspecified (counterbalanced here); $130 needs a go | AI Self-preferencing in Algorithmic Hiring: Empirical Evidence and Insights |
| W4404396586 | needs_human | gpt-4o-2024-05-13 | 1 | other | 390 | 400 | no | WebArena sites plus the Magentic-One multi-agent loop; agent prompts only in code | Magentic-One: A Generalist Multi-Agent System for Solving Complex Tasks |
| W4411120580 | ready | gpt-4-turbo-2024-04-09 | 1 | generation | 50001 | 131 | yes | cost: a seeded subset is the sensible run; paper averages five runs | QSpell 250K: A Large-Scale, Practical Dataset for Chinese Search Query Spell Correction |
| W7164974000 | needs_human | gpt-4-turbo-2024-04-09 | 1 | other | 690 | 212 | no | 20-step tool-calling loop over a sandbox; the corrected benchmark is not linked | WorkBench Revisited: Workplace Agents Two Years On |
| W4415973405 | needs_human | gpt-5-2025-08-07 | 3 | classification | 736 | 18 | no | dataset only "upon reasonable request"; system prompt never quoted | Dual-Model LLM Ensemble ... for Systematic-Review Screening |

## Ready configs, verified with `python tierb_runner.py <wid> --prepare --dry-run --cap 20`

- **W4403574994** — 133 items x 3 seeds, $0.94. Items come from the SP-10Axes questionnaire itself (`questions.js` of github.com/bannnedb/Religious-values-test, MIT, named in Appendix C); the hook parses the JavaScript file and reimplements the quiz's own scoring (`fullquiz.html`: answer multipliers 1 / 0.5 / 0 / -0.5 / -1, score = 100(max+total)/2max, max = 236 on the tenth axis). The rendered prompt reproduces Figure 1's system prompt with its worked example and the `#Question#...#Choices#...#Answer#` template.
- **W7169474262** — 124 items (31 stimuli x 4 runs) x 3 seeds, $4.53. The 31 prompts are printed in Sec. 3.1 and are identical to `spec/stimulus.json` in the repository the paper names, which also settles the article in "Name a[n] X" (e.g. "Name an herb."). The hook transcribes the authors' `analyze.py`: the normalizer (junk guard, last alphabetic word) and self-distinctness (distinct answers / samples, averaged over categories).
- **W4416683695** — two stages, both with the paper's own prompts (Appendix B.1 generation, B.2 pairwise evaluation), evaluator = the same live snapshot, which is what makes it a self-preference test. The unspecified cleaning step was recovered: locating the executive summary through the `SECTION_SUMM` block of `Resume_html` leaves 2,243 usable resumes with summary length mean 68.8 words and quartiles 31 / 48 / 82, against the paper's 2,245 and 70.74 / 32 / 50 / 84 (Table 1).
- **W4411120580** — the repository ships the test set, the scorer and the authors' own GPT-4 outputs, so the metric could be checked before any call: running `eval_corrector.py`'s logic over `qspell_250k_gpt4.txt` gives P 0.7556 / R 0.3181 / F1 0.4477 against Table 3's 0.7409 / 0.3146 / 0.4416 (the paper averages five runs). The hook reproduces that scorer, including the full-width to half-width conversion.

## Recurring difficulties

- **Agentic papers dominate the blocked set (4 of 7).** ToolQuery (xLAM), WebArena (Magentic-One) and WorkBench are episode benchmarks: a live environment or sandbox, a multi-step tool-calling loop and an outcome checker. The runner sends one stateless completion per item and hooks may not call an API, so all three need a separate arm and a human decision; SePro (W4411120015) is the same shape without an environment - two of its four prompt slots are filled by a GAT and a graph-based comment selector the authors never released.
- **Data withheld or "coming soon" (3 papers).** The CCFERD emotion images are still a `ComingSoon.md` placeholder two years after acceptance; the Cochrane screening set is "available upon reasonable request"; the conflicting-needles haystacks were never published and cannot be rebuilt from the six Wikipedia article titles alone.
- **Prompts that are described but not printed.** W4415973405 refers the reader to the authors' earlier preprint instead of quoting the system prompt; W4404396586 prints one of four site clarifications and leaves the agent prompts to the code; W7164974000 prints none. Conversely, four papers print their prompts in full, and two of them (W7169474262, W4411120580) also ship the scoring code, which is what made those configs cheap to verify.
- **Metrics that are not per-item scores.** Three cells are set-level statistics: a questionnaire axis score, a mean over categories, and a conditional-logistic-regression odds ratio. The first two are handled with hook `score()` plus the runner's set-level resampling; the third (W4416035030) would additionally need the paper's full H1-H8 design matrix and is part of why that config is blocked.
- **Paper-side inconsistencies worth recording.** W4403574994's Appendix C sentence about score direction contradicts the column naming its own table inherits from the test; W4415973405's confusion counts (330 positives) do not match its stated 348 included / 388 excluded; W4411120015's Figure 11 accuracy (96.7%) is higher than the SePro row of its own Table 2 without explanation; W4416035030's Table 8 lists a GPT-4o-mini snapshot that was never released.
