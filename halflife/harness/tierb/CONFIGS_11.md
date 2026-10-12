# Tier B run configs, group 11 (11 papers)

Source list: `halflife/data/tierb_triage/config_11.csv`. Configs: `halflife/harness/tierb/configs/<wid>.json` (schema in `CONFIG_SCHEMA.md`), hooks in `halflife/harness/tierb/hooks/<wid>.py`. Prompts were copied from the extracted texts in `halflife/external/papers_tierb/`; dataset pages were checked with small HTTP requests only (nothing over 50 MB downloaded, no model API called, no dataset licence or ethics agreement accepted). Date of the checks: 2026-09-19.

## Counts by status

| status | n |
|---|---|
| ready | 2 |
| needs_download_check | 0 |
| needs_human | 9 |
| **total** | **11** |

Total estimated API cost: **~$665** (sum of est_usd, seeds included); the two ready configs are ~$277 of that, or ~$30 when run at the standard `--cap 20`.

## Configs

| wid | status | model | seeds | task | n_items | est $ | hook | open points | title |
|---|---|---|---:|---|---:|---:|---|---|---|
| W4406192716 | needs_human | gpt-4o-2024-05-13 | 3 | classification | 36 | 1 | - | images not released; vision input; hand-scored | Vision Language Models as Values Detectors |
| W4415772780 | needs_human | o4-mini-2025-04-16 | 3 | other | 545 | 5 | - | prompt not printed (external Brysbaert guidelines); 545-word test split unreleased; Spearman not in the runner | Bridging Behavioral Gaps: Automatic Extrapolation of Concreteness Norms for Arabic and English |
| W7128864310 | needs_human | gpt-4o-2024-05-13 | 3 | classification | 243 | 4 | - | prompts only on OSF (API 401/403 here); HumanToM gold predictions not printed; logprob scoring | GPT-4o Lacks Core Features of Theory of Mind |
| W4402670901 | needs_human | gpt-4o-2024-05-13 | 3 | generation | 3709 | 220 | - | release asset with the data is missing; CircularEval x4 + composite metric; cost | MathBench: Evaluating the Theory and Application Proficiency of LLMs |
| W4407569651 | needs_human | gpt-4-turbo-2024-04-09 | 3 | generation | 510 | 60 | - | dataset never released; questions carry circuit diagrams | CIRCUIT: A Benchmark for Circuit Interpretation and Reasoning Capabilities of LLMs |
| W4414585650 | needs_human | o3-mini-2025-01-31 | 3 | other | 160 | 26 | - | multi-round two-agent simulation (no driver); six context template sets; o3-mini decoding unset | When Ethics and Payoffs Diverge: LLM Agents in Morally Charged Social Dilemmas |
| W4400065264 | ready | gpt-4-turbo-2024-04-09 | 1 | generation | 802 | 25 | yes | - | Following Length Constraints in Instructions |
| W4411113222 | needs_human | gpt-4-turbo-2024-04-09 | 1 | generation | 1209 | 50 | - | 3-shot examples elided in the figures; scoring executes generated .lp/Python with a solver | LLMs for Mathematical Modeling: Towards Bridging the Gap between Natural and Mathematical Languages |
| W4415332749 | ready | o1-2024-12-17 | 1 | classification | 1483 | 252 | yes | - (cost note in `notes`) | J4R: Learning to Judge with Equivalent Initial State Group Relative Policy Optimization |
| W7124513739 | needs_human | gpt-5-2025-08-07 | 3 | generation | 100 | 12 | - | dataset behind an ethics declaration (Duke/CSIRO); which 100 of the 1,100+ questions is unstated | MedRedFlag: Investigating how LLMs Redirect Misconceptions in Real-World Health Communication |
| W7166852523 | needs_human | gpt-5-2025-08-07 | 1 | generation | 1000 | 10 | yes | gemma-3-1b-pt tokenizer is gated (metric unit); 'thinking off' has no gpt-5 equivalent | Dark & Stormy: Modeling Humor in Sentences from the Bulwer-Lytton Fiction Contest |

## The two ready configs

- **W4400065264** (AlpacaEval-LI violation rate). Items are the authors' own release, `length_instructed_alpaca_baseline.json` from `dl.fbaipublicfiles.com` (802 rows, 1.36 MB, MIT repository), whose `instruction` field already carries the Figure 1 template and whose `max_len` field is the gold word limit. `--prepare --dry-run --cap 20`: 802 items, 0 unrenderable, $10.14 by prepare's estimate ($25.15 if every reply used all 1,024 tokens). First rendered item: *"Answer the following instruction using 186 words or less.\n\nWhich parts of France would be best for a moderate walking tour, without serious climbing?"* - identical to the paper's template. The hook implements Appendix A's word count (`nltk.word_tokenize` minus pure-punctuation tokens; `punkt_tab` was installed for it) and returns per-item violations for the bootstrap.
- **W4415332749** (ReasoningJudgeBench consistent accuracy). Items are `Salesforce/ReasoningJudgeBench` (config `default`, 13 splits, 1,483 rows, CC BY-NC 4.0); the hook expands each sample into the two response orders (2,966 rendered items), parses the last `[[A>B]]`/`[[B>A]]` verdict, and scores a sample correct only when both orders are right, micro-averaged as in the paper. Split sizes reproduce Appendix C exactly (598 / 260 / 325 / 300), and the o1 row's four split scores micro-average to 73.09 against the reported 73.10. `--prepare --dry-run --cap 20` succeeds; the full set is 2,966 calls / $251.78, so at the cap the runner keeps a seeded 235-item subset.

## Recurring difficulties

- **Data that is named but not reachable (4 of 11).** MathBench's README points at a release whose only assets are the auto-generated source archives (6 KB, no data), and there is no official Hugging Face or ModelScope mirror; CIRCUIT has no repository, DOI or download anywhere; MedRedFlag sits behind an ethics declaration inherited from MedRedQA; the concreteness paper's footnote says "available at Supplementary material" with no URL at all. Only the latter two even have a place to go and ask.
- **Prompts that point elsewhere (3 of 11).** The ToM paper's system prompt, JSON schema and vignette template are "available on OSF" and the OSF API answers 401/403 from this machine; the concreteness paper's prompt is another paper's annotation guidelines; Mamo prints its instruction block in full but replaces the three demonstrations with `[...]`. In each case writing the missing text would be authoring a new instrument, not copying one.
- **Claims that are not one call per item (4 of 11).** CircularEval asks each MathBench MCQ four times, ReasoningJudgeBench asks each sample twice, the social-dilemma paper runs a stateful two-agent game with rolling memory, and Mamo scores by executing the generated code in a solver. The runner's one-request-per-item model covers the first two through hooks; the last two need infrastructure this harness does not have.
- **Metric instruments outside the API.** Bulwer-Lytton reports mean token length under `gemma-3-1b-pt`, a gated repo (`gated: manual`), so the run is preparable but not scorable in the paper's units until a human accepts the licence or approves a mirror; the ToM agreement score is against a utility model whose parameters are not printed; the values-detector alignment score was assigned by hand.
- **Reported cells that are smaller than the dataset.** MedRedFlag's 88% is over 100 questions (169 false assumptions), not the 1,100+ released items - the triage record's `n_items` was the dataset size. Recorded in the config so the card is not compared against the wrong denominator.
- **Cost.** Two cells are far above the per-paper cap even at one seed (ReasoningJudgeBench $252 on o1, MathBench ~$73 per seed), and one more sits at the cap (AlpacaEval-LI). Reasoning-model output is the driver: the estimator bills the whole `max_completion_tokens`, so the dry-run figure is an upper bound rather than a forecast.
- **Extraction damage was light and repaired where unambiguous:** spaces inserted before apostrophes in monospace prompt blocks (J4R judge prompt, MedRedFlag system prompt), hard line wraps inside sentences in boxed prompts (Bulwer-Lytton, the social-dilemma listings), and typographic quotes left as printed where they are part of the prompt (values detector's 'none', MathBench's Chinese templates). The papers' own typos were kept (J4R's "Focus on the content each response", "Before providing an your final verdict"; Bulwer-Lytton's "worst novel never written").
