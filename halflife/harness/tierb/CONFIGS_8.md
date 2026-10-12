# Tier B run configs, group 8 (11 papers)

Source list: `halflife/data/tierb_triage/config_8.csv`, triage records `halflife/harness/tierb/<wid>.json`.
Configs: `halflife/harness/tierb/configs/<wid>.json` (schema in `CONFIG_SCHEMA.md`), hooks in `harness/tierb/hooks/`.
Prompts were copied from the extracted texts in `halflife/external/papers_tierb/`, or, where a paper points at its own
public repository instead of printing the prompt, from that repository. Item sources were checked with small HTTP
requests; three files (11 MB in total, for W7166821175) were downloaded into `external/data/tierb_items/`. No dataset
over 50 MB was fetched and no model API was called. Date of the checks: 2026-09-19.

## Counts by status

| status | n |
|---|---|
| ready | 3 |
| needs_download_check | 0 |
| needs_human | 8 |
| **total** | **11** |

Total estimated API cost of the group: **~$1,565** (sum of `cost.est_usd`, seeds included); the three ready configs
account for **~$116** of it, and $1,150 of the rest is the single M-RewardBench cell.

## Configs

| wid | status | model | seeds | task | n_items | est $ | hook | open points | title |
|---|---|---|---|---:|---:|---:|---|---|---|
| W7166821175 | ready | gpt-4-turbo-2024-04-09 | 3 | classification | 585 | 21 | y | entity-slot filling unreported (entity lists vs. the repo's overlap-score hint); released gold covers 74 devices, Table 14 says 85 | From Regulatory Approvals to Patents: Cross-Domain Linking for Cardiovascular Device Traceability |
| W7166872685 | ready | o3-mini-2025-01-31 | 3 | classification | 432 | 4.5 | y | 27 instances per cell reconstructed as 3 crimes x 3 closeness paraphrases x 3 templates; paper contradicts itself on 1 vs. 3 seeds | Machine Behavior in Relational Moral Dilemmas: Moral Rightness, Predicted Human Behavior, and Model Decisions |
| W4406975432 | ready | gpt-4-turbo-2024-04-09 | 1 | classification | 5600 | 90 | y | two-stage run (`--run` then `--judge`, ~11,200 calls) needs a go; Appendix B.2 pairs two scenario contexts with the wrong scenarios | Actions Speak Louder than Words: Agent Decisions Reveal Implicit Biases in Language Models |
| W4403928890 | needs_human | gpt-4-turbo-2024-04-09 | 3 | classification | 48 | 1 | n | dataset D1 unreleased ("URL will be added to camera-ready paper"); prompt only inside the app repo and since rewritten; intake rules are a placeholder file | Getting in the Door: Streamlining Intake in Civil Legal Services with Large Language Models |
| W4412714694 | needs_human | gpt-4-turbo-2024-04-09 | 3 | other | 20 | 1 | n | no prompt printed; success is judged by a human operator executing the steps on a physical robot | LA-RCS: LLM-agent-based Robot Control System |
| W4416907954 | needs_human | gpt-4-turbo-2024-04-09 | 3 | classification | 712 | 8 | n | neither the 712-trial cohort nor the expert Success/Failure labels are published; balanced accuracy not a runner metric | Role of Artificial Intelligence in Predicting Outcomes of Clinical Trials in Oncology |
| W7172029025 | needs_human | gpt-4-turbo-2024-04-09 | 3 | other | 200 | 12 | n | 200 video transcripts and the expert consensus scores unreleased; prompt only in Supplementary Additional File 5; Spearman not a runner metric | Agreement between artificial intelligence and expert evaluation in assessing the quality of asthma health education videos |
| W4404782900 | needs_human | gpt-4o-2024-05-13 | 3 | extraction | 442 | 220 | n | reranking needs a GritLM-7B index over the corpus (GPU, no retrieval output released); ~25k input tokens per call; claim cell is R@5, not R@20 | LitSearch: A Retrieval Benchmark for Scientific Literature Search |
| W4411120188 | needs_human | gpt-4o-2024-05-13 | 3 | classification | 300 | 55 | n | runner gap: the item is a meme image sent as an image_url part; the cell is a mean over six prompt variations | Multi3Hate: Multimodal, Multilingual, and Multicultural Hate Speech Detection with Vision-Language Models |
| W4412886932 | needs_human | gpt-4-turbo-2024-04-09 | 1 | classification | 65987 | 1150 | n | ~66,000 judge calls for the 23-language average; user-message template not printed (taken from the cited reward-bench code); A/B order and section weighting unstated | M-RewardBench: Evaluating Reward Models in Multilingual Settings |
| W7158423432 | needs_human | o3-2025-04-16 | 1 | generation | 21 | 3 | n | the metric is a human expert score from seven legal-faculty graders; system prompt only described; exam questions not released machine-readably | Expert Evaluation of LLM's Open-Ended Legal Reasoning on the Japanese Bar Exam Writing Task |

## Hooks

- `hooks/W7166821175.py` - joins `gold_standard.parquet` (585 valid pairs) with the released FDA-document and patent
  tables and truncates both texts to 400 characters, as the authors' own prompt filler does.
- `hooks/W7166872685.py` - enumerates the Whistleblower's Dilemma grid (4 severities x 4 closeness levels x 3 crime
  types x 3 closeness paraphrases x 3 template variants = 432 instances of one perspective) and renders each
  instance with its own template variant.
- `hooks/W4406975432.py` + `hooks/W4406975432_scenarios.json` - the paper's two-step technique: persona generation is
  the main stage (temperature 0.7), action generation runs through the runner's `--judge` stage against the same
  model (temperature 0.2, prompt printed in Appendix C), and `score_with_judge` computes the demographic parity
  difference per group x scenario case and averages over the 12 cases.

## Recurring difficulties

- **Data announced but not released (4 papers).** The civil-legal-intake scenarios (D1) are promised at a
  camera-ready URL that does not exist; the oncology-trial cohort and its expert Success/Failure labels, the 200
  asthma-video transcripts with their expert consensus scores, and the LA-RCS benchmark all stay with the authors.
  In each case the model snapshot is still callable and only the item side blocks the record.
- **Prompt not in the paper (5 papers).** Two papers point at a repository (W4403928890, W7166821175) and one at a
  supplementary file (W7172029025); one prints only the system half (W4412886932) and one only a paraphrase
  (W7158423432). The repository route worked once: Bridge-MedDevKG publishes `code/prompts/prompt_linking.txt`, which
  makes W7166821175 the group's cleanest ready config. It failed for the intake paper, whose prompt is assembled at
  run time by a library that has since moved to a 2026 model.
- **Metric not in the runner (5 papers).** Weighted-average F1, balanced accuracy, Spearman correlation, recall@k over
  a model-produced ranking and the paper's own DPD are all outside `score_items`. Only DPD was worth a hook, because
  only that paper's items were fully available.
- **A claim cell that the triage record mislabels (2 papers).** LitSearch's 79.2 is the average recall@**5** over
  specific questions, not recall@20 (the caption assigns R@5 and R@20 to different columns), and the intake paper's
  0.82 is Table 3's overall weighted F1, not a Table 4 per-jurisdiction value. Both corrections are recorded in
  `metric.original_location`.
- **Human or physical judges (2 papers).** The Japanese bar-exam scores come from seven legal-faculty graders and the
  LA-RCS success rate from a human operator driving a robot; neither can be replaced by an LLM judge, so both are
  needs_human by the schema's rule rather than for a data reason.
- **Runner gaps.** Image input keeps Multi3Hate out (the same gap as W4404352371 and W4404783148 in earlier groups),
  and a retrieval stage with a 7B embedding model keeps LitSearch out.
- **Two papers contradict themselves** on how many passes they ran (W7166872685: three seeded iterations in Sec. 4,
  one deterministic pass in Appendix B.3) or pair prompt components with the wrong scenarios (W4406975432, Appendix
  B.2). Both are recorded as open points on otherwise ready configs.
