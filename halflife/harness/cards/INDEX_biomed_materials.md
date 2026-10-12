# Claim cards — biomed / materials batch (drafted 2026-09-04)

Reference card: `T1_bia_codegen.json` (W4394986684, already complete — verified present, not redone).
Model status per `target_models.json` (all "dying" arms shut down 2026-10-23). Costs are pilot unit prices, 3 seeds unless noted, no batch discount.

| Wid | short title | live arm | status | est_cost_usd | top blocker | core metric (orig value) |
|---|---|---|---|---|---|---|
| W4396768794 | DxGPT rare-disease diagnosis | gpt-4-turbo-2024-04-09 | needs-user-check | 16 | LLM judge (gpt-4-0613) is dead — substitute judge + re-judge archived originals | RAMEDIS Strict Accuracy P1 = 54.04% (Top-5 68.69%), Table 3 |
| W4407012395 | MedXpertQA expert-level medical QA | o1-2024-12-17 (+ o3-mini-2025-01-31) | needs-user-check | 134 | o1 cost (~$125 for 244 items × 3 seeds); dataset asks not to publish examples (log policy) | o1 accuracy on Text 10% sample = 44.67% (o3-mini 37.30%), Table 5 |
| W4412945732 | Glianorex fictional-organ MCQs | gpt-4o-2024-05-13 (+ gpt-4-turbo-2024-04-09) | needs-user-check | 14 | eval code uses undated alias `gpt-4-turbo` + unpinned `guidance` select — must be re-implemented and pinned | gpt-4o accuracy EN 0.74/0.72, FR 0.69/0.71 (derived overall 0.715) vs physicians 27%, Table 6 |
| W4416034576 | AIRepr analyst–inspector reproducibility | o3-mini-2025-01-31 | needs-user-check | 283 | cost (judge pipeline gpt-4o-2024-11-20 ≈ $180) + code-execution sandbox + originals not released | RoT vs CoT reproducibility for o3-mini: 55.23→60.25 (DiscoveryBench), 75.06→81.68 (QRData), 81.0→84.25 (StatQA), Tables 6–7 |
| W4399425290 | Nanomaterial morphology prediction | none (paper's "GPT-4-turbo" = gpt-4-0125-preview, dead) | blocked | 0 | live model not an experimental arm (all closed arms dead); no license on repos | GPT-4 (0613) avg shape accuracy 0.81±0.07; GPT-4-turbo (0125) 0.69±0.11, Table 4 |
| W4400667840 | Nano synthesis mechanism MCQs (c-score) | none (`gpt-4-turbo` appears only in a reference title) | blocked | 0 | live model not an experimental arm (gpt-4-0125-preview / claude-3-opus dead); no license | GPT-4 (0125-preview) accuracy 80.5% mean over T=0.1–0.9 (Claude 3 Opus 84.8%), Fig. 3a |
| W4409346658 | MatDuck zero-shot materials text mining | GPT-4-Turbo (undated alias) | blocked | 0 | paper repo github.com/xinzcode/MatDuck is 404 — prompts/code unrecoverable; 169k-sample scale | MatDuck raises GPT-4 overall macro-F1 0.557→0.661 (micro 0.511→0.579), Table 2 |
| W7144391134 | Blinding study, in-context molecular property prediction | gpt-4.1-nano(-2025-04-14) | draft | 16 | original code in Julia (port needed); Azure→OpenAI channel change | Delaney r: 0-shot 0.41 → 1000-shot 0.76 [0.685,0.815]; L6 blinded 0.45; no verbatim recall (0.14% matches), Fig. 1/4, Table 3 |

Totals: 5 runnable cards ≈ $463 (of which AIRepr $283, MedXpertQA $134); 3 blocked.

## Common patterns
1. Two of the eight "live-arm" hits are false positives of the full-text census: the paper's "GPT-4-turbo" label meant the dead gpt-4-0125-preview snapshot (W4399425290) or the string only occurred in a cited reference (W4400667840) — alias resolution must be checked against the methods section, not just the string match.
2. LLM-as-judge is the hidden second dependence: DxGPT (gpt-4-0613, dead) and AIRepr (gpt-4o-2024-11-20, alive but unlisted) score their metrics with another model, so a "live subject" can still be un-reproducible unless the judge is substituted and, where originals are archived, re-judged.
3. Artifact completeness splits cleanly: DxGPT, nano-synthesis and BlindingLLMs publish item-level original outputs (L1-style, enabling per-item drift analysis), whereas MedXpertQA, Glianorex and AIRepr publish only aggregates, and MatDuck's repository has vanished within a year of publication.
