# Claim cards — Pass-2 Tier A batch (4 papers), drafted 2026-09-19

Cards: `harness/cards/<Wid>.json`. No API calls were made; all numbers are transcribed from the papers and their repositories. Costs are pilot unit-price estimates from `harness/pricing.json` (3 seeds unless the paper's own sampling scheme is stated otherwise). Repositories were shallow-cloned into the gitignored `external/repos/<Wid>/<owner>__<repo>/`.

| Wid | Short title | Live arm (as actually used) | Status | est_cost_usd | Top blocker | Core metric (orig value) |
|---|---|---|---|---|---|---|
| W4399442646 | ACCORD: commonsense measurability gap | gpt-4o-2024-05-13 (dated in App. I.2 and in the repo config filename) | needs-user-check | 18 | original per-bin values exist only as the Figure 3 plot — no result file released | factual vs anti-factual accuracy on 2,864 items; anti-factual falls below the 20% chance line as hops grow (Fig. 3) |
| W7166808082 | TURTLEAI: image-to-turtle-code | o3-2025-04-16 (reasoning_effort=medium, App. F.2) | draft | 15 | no item-level outputs; Tk-dependent scorer executes model-generated code; reasoning-token truncation risk | symbolic success rate on 102 DSReal tasks = 40.20% (Emb. 44.12%) (Table 1) |
| W7155245470 | Same Verdict: LLM judge vs clinicians | gpt-5-mini-2025-08-07 (temperature 1.0, Sec. 3.1) | needs-user-check | 55 | neither the 1,281-item filter nor the clinician ground truth is released; the labels need their own ~$46 GPT-4.1 pass | F1 (Incomplete) 0.76 / Prec 0.86 / Rec 0.68 / AUC 0.66 on 1,281 HealthBench conversations (Table 1) |
| W4400222256 | Scaling synthetic data with 1B personas | gpt-4o-2024-05-13 (Table 2; gpt-4-turbo-2024-04-09 second row) | needs-user-check | 125 | the Table 2 GPT rows are transcribed verbatim from OpenAI's simple-evals leaderboard, not measured; the paper's own live-model rows sit on the unreleased 11.6K set | MATH accuracy 76.6% (gpt-4o-2024-05-13); gpt-4-turbo-2024-04-09 73.4% (Table 2) |

Status tally: draft 1, needs-user-check 3, blocked 0. Sum of est_cost_usd ≈ USD 213, of which USD 33 belongs to the two cards that run under USD 20 (W7166808082, W4399442646). The 500-problem `math_500_test` option would cut W4400222256 from USD 125 to about USD 13.

## Repositories audited

| Wid | Repo | Commit (date) | Size | Licence |
|---|---|---|---|---|
| W4399442646 | github.com/francois-rd/accord | `dd75a4e0429877407b1059c617eee4a45c39fda0` (2024-06-06) | 28 MB | MIT (data CC BY-SA 4.0) |
| W7166808082 | github.com/machine-teaching-group/acl2026-turtleai | `d916dab0bcf6a0d0647e17cab4089d70d0b402d1` (2026-07-04) | 16 MB | no LICENSE file; dataset CC BY-NC 4.0 (App. C.1) |
| W7155245470 | — none published — | — | — | — |
| W4400222256 | github.com/tencent-ailab/persona-hub | `72bf19b886312041b32f7cae12c02dab8653c6fa` (2025-02-18) | 253 MB | code MIT, data CC BY-NC-SA 4.0 |
| W4400222256 (harness) | github.com/openai/simple-evals | `652c89d0ca9df547706735883097e9537d40dc47` (2026-04-22) | <1 MB | MIT |

## Patterns in this batch

1. **Four papers, four dated snapshots — no alias inference needed.** Every arm is printed with its date in the paper itself (`gpt-4o-2024-05-13`, `o3-2025-04-16`, `gpt-5-mini-2025-08-07`, `gpt-4o-2024-05-13`/`gpt-4-turbo-2024-04-09`), so the date rule was not applied once and no card is blocked on a dead snapshot. The dead snapshots that do appear are comparator rows only (gpt-3.5-turbo-0125; gpt-4-0125/1106-preview) — plus one that matters operationally: simple-evals' *equality checker* is `gpt-4-turbo-preview`, so a grader substitution is needed even though the subject arm is alive.
2. **The repository decides how much of the protocol survives, and only one of the four gives the full pipeline.** TURTLEAI ships prompt, data, images, the Turtle emulator, the symbolic scorer and an OpenAI runner — it is a clean upgrade from the prompt-level Tier B config, closing both runner gaps (image attachment, external program scorer). ACCORD ships the generator, configs and prompts but no benchmark instances and no results, so the items must be regenerated (deterministic at `random_seed 314159`) or fetched from Codabench. persona-hub ships generation demos only; its evaluation protocol lives in a third-party MIT repo. "Same Verdict" ships nothing at all — prompts exist only as appendix tables.
3. **What is unreleased is the label, not the data.** Three of the four can reach their items (ACCORD regenerates, TURTLEAI commits them, MATH is a public CSV), but two cannot reach the comparison target: "Same Verdict" must rebuild both the 1,281-item filter and the GPT-4.1-derived clinician ground truth before a single subject call, and persona-hub's own live-model numbers sit on a test set whose answers were never published. Cost follows the same split — the two cards that only need the subject arm land at USD 15–18, while the two that must also pay for labels or for 5,000 chain-of-thought completions land at USD 55 and USD 125.
4. **Published-number provenance is worth checking before costing a card.** persona-hub's Table 2 GPT rows match the openai/simple-evals README leaderboard digit for digit, so re-running that card re-tests OpenAI's published MATH figure under the paper's declared protocol rather than anything the persona authors measured — a distinction the census should record, analogous to the "alias false positive" pattern in the medicine batch.
5. **Two cards have no numeric original value at all.** ACCORD prints only Figure 3, and TURTLEAI/"Same Verdict" release no item-level outputs, so three of the four judgments are anchored on direction and threshold crossings (factual > anti-factual; anti-factual below chance; AUC stays near chance) rather than on point-value agreement.
