# Tier B run configs, group 5 (11 papers)

Configs written to `halflife/harness/tierb/configs/<wid>.json` following `CONFIG_SCHEMA.md`, one row of `halflife/data/tierb_triage/config_5.csv` each. Prompts were copied from the extracted texts in `halflife/external/papers_tierb/` and, where a paper prints a template but not its slot fillers, from the authors' own released code; every such substitution is named in `prompt.verbatim`. Dataset pages were checked with small HTTP requests and the item files were mirrored under `halflife/external/data/tierb_items/<wid>/` (largest download 3.8 MB, no dataset over 50 MB, no model API called). Each `ready` config was verified with `python tierb_runner.py <wid> --prepare --dry-run --cap 20` and the first rendered item in `runs/tierb/<wid>/items.jsonl` was compared against the paper. Date of the checks: 2026-09-19.

## Counts by status

- ready: 6
- needs_human: 5
- total estimated cost: USD 716 (USD 61 for the 6 ready configs; the rest are hand estimates for claims that cannot be run as written)

## Table

| wid | status | model | seeds | task | n_items | est $ | hook | open points | title |
|---|---|---|---|---|---|---|---|---|---|
| W4399911093 | ready | gpt-4-turbo-2024-04-09 | 3 | classification | 100 | 6.0 | yes | seeds 3 vs the paper's 5 runs at default temperature | Leveraging Large Language Models to Measure Gende... |
| W4407571270 | needs_human | gpt-4o-2024-05-13 | 3 | classification | 198 | 1.0 | no | no items, no gold labels, no prompt text | Web Publication of Local Assembly Minutes in Toka... |
| W4416034248 | ready | gpt-4-turbo-2024-04-09 | 3 | generation | 204 | 11.0 | yes | 1-shot demonstration is our seeded draw; Korean scoring regex reconstructed | Can LLMs Truly Plan? A Comprehensive Evaluation o... |
| W7160514285 | ready | gpt-4.1-nano | 3 | classification | 108 | 0.05 | yes | Table 2 says 0.935, the released outputs say 0.944; undated model alias | Large Language Models Show Metacognitive Sensitiv... |
| W4403580619 | ready | gpt-4-turbo-2024-04-09 | 3 | classification | 1816 | 31.0 | yes | run with a cap that keeps all 1,816 items or story pairs break | Evaluating Gender Bias of LLMs in Making Morality... |
| W4409369309 | needs_human | gpt-4-turbo-2024-04-09 | 1 | generation | 156 | 150.0 | no | agentic multi-call method; pass/fail needs a Verilog simulator | VerilogCoder: Autonomous Verilog Coding Agents wi... |
| W4416034022 | needs_human | gpt-4o-2024-05-13 | 1 | generation | 805 | 26.0 | no | judge prompt not printed; LC win rate needs the AlpacaEval GLM | CoTD-PO: Chain-of-Thought Distillation with Prefe... |
| W4403580145 | needs_human | gpt-4o-2024-05-13 | 1 | mcq | 14232 | 320.0 | no | multimodal items; the runner sends text only | Unearthing Skill-Level Insights for Understanding... |
| W4411119711 | ready | gpt-4-turbo-2024-04-09 | 1 | classification | 750 | 5.0 | yes | prompt taken from the authors' code, not the paper; gold pooling off by ~6 samples | FaithBench: A Diverse Hallucination Benchmark for... |
| W7129376919 | needs_human | gpt-4-turbo-2024-04-09 | 1 | classification | 11300 | 158.0 | no | linked repository is empty; PICOS slot of the prompt unpublished | Collaborative large language models (LLMs) are al... |
| W7162149911 | ready | gpt-5-2025-08-07 | 3 | extraction | 100 | 8.0 | yes | slot fillers and reasoning_effort inferred from the released code | Refining and Reusing Annotation Guidelines for LL... |

## Hooks

Six of the eleven papers need a hook (`harness/tierb/hooks/<wid>.py`, all under 140 lines, all with an inline self-test, none making any network or API call):

- `W4399911093.py` - loads the 100-sentence Spanish validation set, reimplements the authors' `parse_response` and their pooled precision/recall/F-score over word triples.
- `W4403580619.py` - splits the 908 GenMO pairs into 1,816 independent calls, renders the CoT prompt (the runner would read `${YOUR_STANCE}` as a placeholder slot), applies `get_stance` and re-pairs the answers for the Prediction Mismatch Rate.
- `W4411119711.py` - binarizes the 750 FaithBench samples with the released `binarize.py` configuration and computes balanced accuracy.
- `W4416034248.py` - reads the Multi-Plan parquet, attaches a seeded 1-shot demonstration, and scores the visit/fly event sequence with Appendix F.1's regular expressions (English as printed, Korean as the Math gold plans actually use).
- `W7160514285.py` - filters the frozen 135-trial manifest to its 108 forced-choice trials and derives the gold answer letter from `option_A` / `ground_truth_label`.
- `W7162149911.py` - loads the 100 PubAnnotation documents, realigns the returned spans and computes strict-match micro F1.

## Recurring difficulties

- **Prompts printed as templates, fillers only in the code.** Three of the six runnable papers print a template with empty slots (`{{guidelines}}` / `{{jsonSchema}}`, `<EXAMPLES>` / `<SENTENCE>`, `{example_task}`): the fillers come from the authors' released repositories, and `prompt.verbatim` names every substitution. FaithBench goes further - it cites its prompt to another paper and the exact strings had to be read out of the authors' own judge notebook (typo `correponding` included).
- **Released artefacts beat the paper text twice.** The GenMO evaluation script fixes seed 9897, `max_tokens` 500 and the stance parser; the metacognition manifest ships the rendered prompt of all 135 trials and its archived run records show `max_output_tokens` 300 where the script's constant says 200. Both configs follow the artefact and say so in `params_source`.
- **Metrics the runner does not implement.** Five of six ready configs score with a hook: pooled precision/recall F-score over word triples, strict-match NER F1, a paired mismatch rate, balanced accuracy, and an exact event-sequence match. Only the metacognition pilot fits `accuracy` directly.
- **Announced but absent data.** `github.com/Mihir3009/SR_LLMs` is promised in a data-availability statement and contains only a LICENSE and a one-line README, which alone blocks the largest claim in the group; the Tokachi minutes paper links nothing at all.
- **Claims that are not one call per item.** VerilogCoder is an Autogen multi-agent loop scored by a Verilog simulator, the CoTD-PO cell is an AlpacaEval length-controlled win rate fitted by a GLM over judge probabilities, and the skill-slice cell needs image inputs the runner cannot send. These three are harness or pipeline decisions, not missing text.
- **Snapshot niceties.** `gpt-4.1-nano` is an undated alias (kept as the triage resolved it); `gpt-5-2025-08-07` ignores temperature, so the config carries only `reasoning_effort: high` and a 12,000-token completion budget, and the runner drops the paper's strict `response_format` for reasoning models - recorded as an approximation.

