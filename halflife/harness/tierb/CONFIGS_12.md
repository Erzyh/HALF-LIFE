# Tier B run configs, group 12 (11 papers)

Configs written to `halflife/harness/tierb/configs/<wid>.json` following `CONFIG_SCHEMA.md`, from the 11 rows of
`halflife/data/tierb_triage/config_12.csv`. Prompts were copied from the extracted texts in
`halflife/external/papers_tierb/` and, where the authors released their prompt files, cross-checked against the
code release (the differences are recorded in each config's `prompt.verbatim`). Dataset pages were checked with
small HTTP requests; four small files were downloaded into `halflife/external/data/tierb_items/<wid>/` (largest
single download 8.3 MB, total under 12 MB). No model API was called. Date of the checks: 2026-09-19.

Every "ready" config was verified with `python tierb_runner.py <wid> --prepare --dry-run --cap 20` from
`halflife/harness/`, and the first rendered item in `runs/tierb/<wid>/items.jsonl` was compared with the prompt as
printed in the paper.

## Counts by status

- ready: 3
- needs_download_check: 0
- needs_human: 8
- estimated cost of the three ready configs: USD 84 (W4411119343 0.83 + W4416036063 62.40 + W7126280993 20.90,
  all from the runner's own `--prepare` estimate; see the warning on W7126280993 below)
- estimated cost of the eight blocked configs if their blockers were removed: about USD 1,700, of which USD 1,500
  is W4403569908 alone; W7166872551 cannot be estimated at all

## Table

| wid | status | model | seeds | task | n_items | est $ | hook | open points | title |
|---|---|---|---|---|---|---|---|---|---|
| W4411119343 | ready | gpt-4-turbo-2024-04-09 | 1 | classification | 394 | 0.83 | yes | triage cell corrected (394, not 450) | Are LLM-Judges Robust to Expressions of Uncertainty? ... |
| W4416036063 | ready | o1-2024-12-17 | 1 | mcq | 1500 | 62.40 | no | the paper's own 1,500-question MMLU draw is behind an empty data link; seeded redraw | sudoLLM: On Multi-role Alignment of Language Models |
| W7126280993 | ready | o3-2025-04-16 | 3 | other | 480 | 20.90 | yes | output-token estimate is optimistic; a cap must be fixed before any run | Semantic Content Determines Algorithmic Performance |
| W4403365377 | needs_human | o4-mini-2025-04-16 | 3 | classification | 1000 | 36.00 | no | image input; no released dataset or generator | Chain-of-Sketch: Enabling Global Visual Reasoning |
| W4403569908 | needs_human | gpt-4-turbo-2024-04-09 | 1 | generation | 12200 | 1500.00 | no | prompt not published; nine images per call; BLEU-1 missing | EmbodiedCity: A Benchmark Platform for Embodied Agent ... |
| W4407425826 | needs_human | gpt-4o-2024-05-13 | 3 | generation | 71 | 120.00 | no | scoring needs GNATprove; multi-attempt retry loop; benchmark link lost | Verifying LLM-Generated Code ... with Ada/SPARK |
| W4407570954 | needs_human | gpt-4-turbo-2024-04-09 | 3 | classification | 386 | 25.00 | no | the released dataset still has no full_review column, so the with-context cell cannot be rendered | Beyond the Lens: Quantifying the Impact of Scientific Documentaries ... |
| W4414856810 | needs_human | o3-mini-2025-01-31 | 3 | other | 10 | 15.00 | no | multi-turn two-agent simulation; the battery issues independent single calls | Effects of Theory of Mind and Prosocial Beliefs ... in Ultimatum Games |
| W4416033558 | needs_human | gpt-4.1-nano | 3 | classification | 20 | 0.05 | no | the Imagen-4 stimulus images are not released; image input | Brown Like Chocolate: How Vision-Language Models Associate Skin Tone ... |
| W7134093983 | needs_human | gpt-4.1-nano-2025-04-14 | 3 | extraction | 154 | 0.40 | no | image input; the split file is Stanford course data and is not shipped | Using Vision + Language Models to Predict Item Difficulty |
| W7166872551 | needs_human | gpt-5-2025-08-07 | 1 | extraction | unknown | unknown | no | corpus not identified or linked; entity list, guidelines and examples unpublished | Post Hoc Agentic Refinement ... Multilingual Clinical Text De-identification |

## Hooks

- `hooks/W4411119343.py` - selects the 394 Correct Natural-Questions records of EMBER-QA and prepares the three
  prompt fields exactly as `run_qaeval.py` does (question with its first letter upper-cased, only the first
  reference string, the strengthener variant of the reader output). Neither step is expressible in the
  mini-language.
- `hooks/W7126280993.py` - rebuilds the 480 explicit-separator questions from the 24 benchmark reports archived
  in the WhatCounts repository (the paper's own prompts and gold counts, not a regeneration) and computes the
  Semantic Gap (max class accuracy - min class accuracy). Its self-test checks that the config template
  re-renders all 480 archived prompts byte-for-byte and that `score()` returns 0.400 when fed the paper's own
  per-class accuracies, i.e. Table 1.

## Corrections to the triage rows

- **W4411119343**: the triage record places the 83.8 cell at "450 Correct samples". 450 is the TriviaQA block of
  Table 15 (where GPT-4-turbo scores 98.0). 83.8 sits in Table 14, the Natural Questions table, whose GPT-4
  reader block has **394** Correct samples. The released `ember_qa_gpt4.json` confirms it: records 0-499 split
  394/106 on `judge_gpt4` and carry no `wiki` key, records 500-999 split 450/50 and do.
- **W7126280993**: the triage row records 120 items and 360 calls. Appendix A says "we select four different
  ranges" and then lists three, but the archived reports show four (7-17, 85-115, 550-650, 950-1050), so the
  condition is 6 classes x 4 ranges x 20 questions = **480** items (1,440 calls at three seeds). The per-class
  accuracies in the authors' own results move in steps of 1/80, which confirms 80 questions per class.
- **W4407425826**: the triage row records 140 items; the benchmark has **71** cases (Table 2), and 50.7% is
  36/71.
- **W7166872551**: the triage row's 24,145 is the number of gold PII spans, not a document or call count; the
  corpus size is never stated.

## Recurring difficulties in this group

- **Image input is the single biggest blocker (4 of 11).** W4403365377 (cycle-graph images), W4416033558
  (synthetic portraits), W7134093983 (chart images) and W4403569908 (nine city views per call) are all defined by
  what the model sees, and the runner sends text only. This repeats the pattern already recorded in groups 1-4
  (`runner_gaps: prompt: image attachment placeholder`), so the configs are staged the same way: the text part is
  written out and the image slot is named in `prompt.placeholders` as NOT EXPRESSIBLE.
- **Stimuli that were never published.** Three of those four are worse than a runner gap: the Imagen-4 portraits
  live only on the first author's disk, the cycle images have neither a dataset nor a released generator, and
  EmbodiedCity's host serves a self-signed certificate that blocks even a licence check. Regenerating any of them
  would replace the paper's benchmark with our own.
- **A promised column that never arrived.** W4407570954 is the cleanest case: the dataset is public, the prompt is
  printed in full, the model snapshot is pinned - and the `full_review` field that the claimed "with context" cell
  needs is still listed on the dataset card as "to be uploaded later (as of 02/26/2025)". The identical 0.69 in
  the "w/o context" row of the same table is runnable today and is offered in `open_points` as a fallback a human
  can approve.
- **Protocols the battery cannot drive (2 of 11).** W4414856810 is a two-agent negotiation over up to five rounds
  and W4407425826 is a generate-verify-retry loop around GNATprove; both need a reply to re-enter the next
  request, which `battery.py` never does. These would need Tier-A-style adapters, not configs.
- **Code releases rescued three papers.** W4411119343, W4416036063 and W7126280993 are ready only because the
  authors released their prompt files, their evaluation code or their raw benchmark reports. In all three the
  released artefact is strictly more informative than the paper: `qa_util.py` shows that the printed Table 12
  prompt differs from the shipped one by exactly the one mitigation line of footnote 7; `prompts/base_prompts/
  mmlu.txt` restores an opening sentence that Appendix D drops; and the WhatCounts reports hand over the exact
  480 prompts and gold counts, so that config needs no regeneration at all.
- **Cost estimation for reasoning models is unreliable.** The runner assumes 600 hidden reasoning tokens per
  call. For W7126280993 - o3 counting lists of up to 1,050 entries with `reasoning_effort: medium` and
  `max_completion_tokens: 100000` - that assumption gives USD 20.9 while the bound implied by the paper's own
  `max_completion_tokens` is about USD 1,100. The config records both numbers and marks the cap as a decision a
  human must take before the run, not after.
