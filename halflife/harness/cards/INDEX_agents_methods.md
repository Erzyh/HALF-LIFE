# Claim-card index — agentic systems & methods batch (7 papers)

Cards: `harness/cards/<Wid>.json` (schema: `SCHEMA.md`, reference: `T1_bia_codegen.json`). Costs at pilot unit prices (gpt-4-turbo $10/$30, gpt-4o $5/$15 per 1M tokens), ANALYSIS_PLAN 3 seeds × 2 paraphrases unless the paper's own sampling scheme replaces seeds. Drafted 2026-09-04; no API calls were made.

| Wid | Short title | Live arm | Status | est_cost_usd (full / subset) | Top blocker | Core metric (orig value) |
|---|---|---|---|---|---|---|
| W4391591592 | TravelPlanner | gpt-4-turbo-2024-04-09 (proxy; paper used gpt-4-1106-preview, dead) | needs-user-check | 5,100 / 520 | Exact snapshot dead; test set scorable only via leaderboard (validation offline) | Two-stage Final Pass Rate, GPT-4-Turbo: 0.6% (val 1/180; test 0.6%), Table 3 |
| W4400337928 | Agentless | gpt-4o-2024-05-13 | needs-user-check | 635 / 142 (+ docker compute) | SWE-bench docker harness (300 images, ~100-150 GB, ~1 day/run) | SWE-bench Lite resolved: 96/300 = 32.00%, $0.70/issue, Table 1 |
| W4402684150 | LoCoMo | gpt-4-turbo-2024-04-09 (alias 'gpt-4-turbo', May-2024 API) | draft | 136 / 13 | Model given only as alias; unseeded adversarial option order | QA overall F1: 51.6 (adversarial 15.7; human 87.9), Table 2 |
| W4404782209 | Multi-Agent Debate | none (gpt-3.5-turbo-0301 & gpt-4-0314 dead; 'gpt-4-turbo' = census false positive from Table 6 text) | blocked | (760 / 105, successor-only hypothetical) | live model not an experimental arm | MAD vs Turbo, Common MT Lexical COMET 82.0 vs 80.3 / HUMAN 3.78 vs 3.14; CIAR acc 37.0 vs 26.0, Tables 1 & 3 |
| W4404783537 | Let Me Speak Freely | none (gpt-4-turbo-2024-04-09 only a parser reference, App. B) | blocked | (3,500 / 130, successor-only hypothetical) | live model not an experimental arm; parser model claude-3-haiku dead | GSM8K text vs JSON-schema: gpt-3.5-turbo 75.99 → 49.25; claude-3-haiku 86.51 → 23.44, Table 1 |
| W4405408496 | Temperature × clinical-trial extraction | gpt-4o-2024-05-13 | draft | 295 / 29 | No calling script in repo; CSV metadata ≠ paper description (journals/years/n) | % correctly formatted (task 1): 98.7% at T=0 → 95.6% (1.75) → 89.2% (2.00); MAPE flat, Table 1 |
| W4411120389 | Good/Bad/Greedy (non-determinism) | gpt-4-turbo-2024-04-09 | needs-user-check | 3,700 (3 judge-free benchmarks) / 106 (HumanEval N=32) | top-p mismatch (paper 1.0 vs Open-Instruct 0.95); judge-based benchmarks need dead gpt-4-1106-preview | HumanEval greedy 89.6 vs sampling mean 84.1 (std 2.65, N=128, p=1.1e-48), Table 2/8 |

## Patterns seen across the batch

1. **Alias ≠ snapshot.** Four of five "gpt-4-turbo" papers name only the alias; one (TravelPlanner) actually ran gpt-4-1106-preview (dead), one (LoCoMo) can only be inferred (May-2024 API → 2024-04-09), and two (MAD, Let-Me-Speak-Freely) never used it as a subject at all — the census string match caught table text ("GPT-4 Turbo GPT-4") and an appendix parser check.
2. **Hidden auxiliary dependence kills otherwise-live claims.** Plan-to-JSON extraction (TravelPlanner), the answer parser (claude-3-haiku, LMSF), and pairwise judges (gpt-4-1106-preview for AlpacaEval/Arena-Hard in GoodBadGreedy) are dead or must be substituted even when the subject model is alive.
3. **Released per-item outputs are the decisive artifact.** Agentless (v1.5.0 zip), GoodBadGreedy (HF zip), Temperature (CSV) and MAD (200 debate JSONs) allow paired re-scoring and an environment check before spending; TravelPlanner and LoCoMo only report aggregates, so their judgments rest on bootstrap CIs over items.
