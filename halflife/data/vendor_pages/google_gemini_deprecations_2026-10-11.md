# Google Gemini deprecations, read 2026-10-11

Sources (fetched by a web-reading agent, tables below are its extraction): https://ai.google.dev/gemini-api/docs/deprecations (last updated 2026-10-09), https://ai.google.dev/gemini-api/docs/changelog (last updated 2026-10-09), https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions (last updated 2026-10-10; the Vertex deprecations page lists no model rows). Purpose: pre-submission check of the retirement vocabulary (target_models.json, 18 Google identifiers). Previous snapshot: google_gemini_deprecations_2026-09-28.txt.

## Comparison with the vocabulary (first author, 2026-10-11)

- Dates in the vocabulary that the Gemini API page or changelog confirm: gemini-1.5-pro, gemini-1.5-flash, gemini-1.5-flash-8b shut down 2025-09-29 (changelog); gemini-2.5-flash-preview-05-20 2025-11-18; gemini-2.5-pro-preview-03-25, -05-06, -06-05 2025-12-02; gemini-2.5-flash-preview-09-25 2026-02-17; gemini-3-pro-preview 2026-03-09; gemini-2.5-flash-lite-preview-09-2025 2026-03-31; gemini-3.1-flash-lite-preview 2026-05-25; gemini-2.0-flash, -001, -lite, -lite-001 2026-06-01; gemini-3.1-flash-lite 2027-05-07 (scheduled).
- gemini-1.0-pro and text-bison (vocabulary 2025-04-09, from the Vertex release notes read on 2026-09-15): the Vertex model-versions page lists gemini-1.0-pro-001, gemini-1.0-pro-002, gemini-1.0-pro-vision-001, text-bison, chat-bison and code-gecko as retired on 2025-04-21; the Gemini API changelog says only "Gemini 1.0 Pro is no longer supported" (2025-02-18). Checked against the release notes on 2026-10-11 (see the audit note in target_models.json).
- Announcements after 2026-10-02: on 2026-10-08 gemini-3.7-flash (replaced by gemini-3.8-flash) and gemini-3.5-flash (replaced by gemini-3.6-flash) were deprecated on the Gemini API with automatic routing and no shutdown date; deep-research-pro-preview-12-2025 shuts down 2026-10-23; gemini-3.1-flash-image deprecated 2026-10-06 without a date. The Vertex page gives gemini-3.7-flash 2027-01-28, gemini-3.6-flash 2026-11-19 and gemini-2.5-pro, -flash, -flash-lite 2026-10-20, while the Gemini API says the 2.5 models "are not deprecated and will continue to be served until further notice" (access restricted to existing users since 2026-09-18). These identifiers are in the extension vocabulary (data/census_ext_models.json) as still served; they stay outside the retired-or-retiring census, whose vocabulary was fixed on 2 October 2026.

## Gemini API deprecations page: language-model rows (audio, image, video, embedding, robotics and agent rows omitted)

| identifier | shutdown | replacement | retired on 2026-10-11? | released |
| --- | --- | --- | --- | --- |
| gemini-3.8-flash | none announced | - | no | 2026-09-02 |
| gemini-3.7-flash | none announced (deprecated 2026-10-08, auto-routed) | gemini-3.8-flash | no | 2026-08-13 |
| gemini-3.6-flash | none announced | - | no | 2026-07-21 |
| gemini-3.5-flash-lite | none announced | - | no | 2026-07-21 |
| gemini-3.5-flash | none announced (deprecated 2026-10-08, auto-routed) | gemini-3.6-flash | no | 2026-05-19 |
| gemini-3.1-flash-lite | 2027-05-07 | gemini-3.5-flash-lite | no | 2026-05-07 |
| gemini-3.1-pro-preview | none announced | - | no | 2026-02-19 |
| gemini-3-flash-preview | none announced | gemini-3.6-flash | no | 2025-12-17 |
| gemini-3-pro-preview | 2026-03-09 | gemini-3.1-pro-preview | yes | 2025-11-18 |
| gemini-3.1-flash-lite-preview | 2026-05-25 | gemini-3.1-flash-lite | yes | 2026-03-03 |
| gemini-2.5-pro | none announced (access restricted) | - | no | 2025-06-17 |
| gemini-2.5-pro-preview-03-25, -05-06, -06-05 | 2025-12-02 | gemini-3.1-pro-preview | yes | 2025-03/05/06 |
| gemini-2.5-computer-use-preview-10-2025 | 2026-07-28 | gemini-3.8-flash | yes | 2025-10-07 |
| gemini-2.5-flash | none announced (access restricted) | - | no | 2025-06-17 |
| gemini-2.5-flash-lite | none announced (access restricted) | - | no | 2025-07-22 |
| gemini-2.5-flash-lite-preview-09-2025 | 2026-03-31 | gemini-3.1-flash-lite | yes | 2025-09-25 |
| gemini-2.5-flash-preview-05-20 | 2025-11-18 | gemini-3.6-flash | yes | 2025-05-20 |
| gemini-2.5-flash-preview-09-25 | 2026-02-17 | gemini-3.6-flash | yes | 2025-09-25 |
| gemini-2.0-flash, gemini-2.0-flash-001 | 2026-06-01 | gemini-3.6-flash | yes | 2025-02-05 |
| gemini-2.0-flash-lite, gemini-2.0-flash-lite-001 | 2026-06-01 | gemini-3.1-flash-lite | yes | 2025-02-25 |
| gemini-2.0-flash-lite-preview, -02-05 | 2025-12-09 | gemini-2.5-flash-lite | yes | 2025-02-05 |

Changelog shutdowns not on the deprecations page: gemini-1.5-pro, gemini-1.5-flash, gemini-1.5-flash-8b 2025-09-29; gemini-2.5-pro-exp-03-25 2025-06-26; gemini-2.5-flash-lite-preview-06-17 2025-11-18; gemini-2.0-flash-thinking-exp family 2025-12-02; gemini-2.0-flash-exp, gemini-2.0-pro-exp 2025-12-09; "Gemini 1.0 Pro is no longer supported" 2025-02-18.

## Vertex AI model-versions page: text-model rows

| identifier | retirement | replacement | released |
| --- | --- | --- | --- |
| gemini-3.5-flash-lite | 2027-07-21 or later | - | 2026-07-21 |
| gemini-3.5-flash | 2027-05-19 or later | - | 2026-05-19 |
| gemini-3.1-flash-lite | 2027-05-07 or later | - | 2026-05-07 |
| gemini-2.5-pro | 2026-10-20 | gemini-3.8-flash or gemini-3.5-flash | 2025-06-17 |
| gemini-2.5-flash | 2026-10-20 | gemini-3.8-flash, gemini-3.5-flash-lite or gemini-3.1-flash-lite | 2025-06-17 |
| gemini-2.5-flash-lite | 2026-10-20 | gemini-3.8-flash, gemini-3.1-flash-lite or Gemma 4 | 2025-07-22 |
| gemini-3.8-flash-cyber, gemini-3.8-flash | none announced | - | 2026-09-16, 2026-09-02 |
| gemini-3.7-flash | 2027-01-28 | gemini-3.8-flash | 2026-08-13 |
| gemini-3.6-flash | 2026-11-19 | gemini-3.8-flash | 2026-07-21 |
| gemini-2.0-flash, gemini-2.0-flash-lite | 2026-06-01 (retired) | gemini-3.1-flash-lite | 2025-02 |
| gemini-1.5-pro-001, gemini-1.5-flash-001 | 2025-05-24 (retired) | gemini-2.5-flash / -lite | 2024-05-24 |
| gemini-1.5-pro-002, gemini-1.5-flash-002 | 2025-09-24 (retired) | gemini-2.5-flash / -lite | 2024-09-24 |
| gemini-1.0-pro-001, gemini-1.0-pro-002, gemini-1.0-pro-vision-001 | 2025-04-21 (retired) | gemini-2.5-flash | 2024-02/04 |
| text-bison, chat-bison, code-gecko | 2025-04-21 (retired) | gemini-2.5-flash-lite | 2023-05 |

Cross-page discrepancies noted by the reader: the Gemini API and Vertex pages give different fates for gemini-3.5-flash, gemini-3.6-flash, gemini-3.7-flash and the 2.5 GA models (see above); release dates differ for a few models; gemini-omni-flash-preview's deprecation moved from 2026-09-30 (changelog of 2026-08-27) to a shutdown on 2026-10-22.
