# OpenAI deprecations page, read 2026-10-11

Source: https://developers.openai.com/api/docs/deprecations (HTTP 200, fetched by a web-reading agent; the tables below are its extraction, reproduced as printed; no "last updated" stamp on the page). Purpose: pre-submission check of the retirement vocabulary (target_models.json, 41 OpenAI identifiers). Previous snapshot: openai_deprecations_2026-09-28.txt.

## Comparison with the vocabulary (first author, 2026-10-11)

- Every one of the 41 OpenAI identifiers in the vocabulary carries the same shutdown date on the page as in target_models.json (2024-01-04 InstructGPT models; 2024-09-13 gpt-3.5-turbo-0301/0613/16k; 2024-12-06 vision previews; 2025-06-06 gpt-4-32k; 2025-07-14 gpt-4.5-preview; 2025-07-28 o1-preview; 2025-10-27 o1-mini; 2026-02-17 chatgpt-4o-latest; 2026-03-26 gpt-4-0314, gpt-4-0125-preview, gpt-4-1106-preview; 2026-10-23 the legacy snapshots; 2026-12-11 the GPT-5 and o3 snapshots).
- No announcement dated on or after 2026-10-02. The newest sections are dated 2026-10-01: gpt-5.3-codex, gpt-5.1 and gpt-5.4-nano (shutdown 2027-04-01, replacements gpt-6-sol and gpt-6-luna) and the text-to-speech models (2027-01-06).
- The 2026-04-22 "Legacy GPT model snapshots" table (shutdown 2026-10-23) is filed under "Past deprecations" although the date is still ahead; gpt-4-1106-preview appears both there (2026-10-23) and in the 2025-09-26 table (2026-03-26); the vocabulary keeps 2026-03-26, confirmed by the 404 probe of 2026-09-28.
- Retired or scheduled text models that are NOT in the vocabulary (already on the page in the 2026-09-28 snapshot): gpt-3.5-turbo-instruct, babbage-002, davinci-002 and gpt-3.5-turbo-1106 (2026-09-28); the specialized variants retired 2026-07-23 (gpt-5-chat-latest, gpt-5-codex, gpt-5.1-chat-latest, gpt-5.1-codex, gpt-5.1-codex-max, gpt-5.1-codex-mini, gpt-5.2-codex, o3-deep-research, o4-mini-deep-research, computer-use-preview, gpt-4o-search-preview, gpt-4o-mini-search-preview), 2026-08-10 (gpt-5.2-chat-latest, gpt-5.3-chat-latest), 2026-10-01 (gpt-5.4-cyber), 2026-02-12 (codex-mini-latest); and the 2026-10-01 announcement (gpt-5.1, gpt-5.3-codex, gpt-5.4-nano, shutdown 2027-04-01). Audio, image, video, embedding and moderation models are outside the vocabulary by scope. See the decision recorded in target_models.json ("audit", 2026-10-11).

## Shutdown dates on or after 2026-10-02 (as of 2026-10-11)

| shutdown | identifiers | announcement section |
| --- | --- | --- |
| 2027-04-01 | gpt-5.3-codex, gpt-5.4-nano, gpt-5.1 | 2026-10-01 |
| 2027-02-26 | whisper-1, gpt-4o-transcribe, gpt-4o-mini-transcribe, gpt-4o-transcribe-diarize | 2026-08-26 |
| 2027-01-20 | gpt-realtime, gpt-audio, gpt-4o-audio, gpt-4o-realtime, gpt-realtime-mini, gpt-audio-mini, gpt-4o-mini-realtime, gpt-4o-mini-audio, gpt-4o-mini-transcribe-2025-03-20 | 2026-07-20 |
| 2027-01-06 | tts-1, tts-1-hd, gpt-4o-mini-tts-2025-03-20, gpt-4o-mini-tts-2025-12-15 | 2026-10-01 |
| 2026-12-11 | gpt-5-2025-08-07, gpt-5-mini-2025-08-07, gpt-5-nano-2025-08-07, gpt-5-pro-2025-10-06, o3-2025-04-16, o3-pro-2025-06-10 | 2026-06-11 |
| 2026-12-01 | gpt-image-1-mini, gpt-image-1.5, chatgpt-image-latest | 2026-06-02 |
| 2026-10-23 | gpt-3.5-turbo-0125 (gpt-3.5-turbo), gpt-4-0613 (gpt-4), gpt-4-1106-preview, gpt-4-turbo (gpt-4-turbo-2024-04-09), gpt-4.1-nano (gpt-4.1-nano-2025-04-14), gpt-4o-2024-05-13, gpt-image-1, o1-2024-12-17 (o1), o1-pro-2025-03-19 (o1-pro), o3-mini-2025-01-31 (o3-mini), o4-mini-2025-04-16 (o4-mini), fine-tuned ft-gpt-3.5-turbo, ft-gpt-4, ft-gpt-4.1-nano-2025-04-14, ft-o4-mini-2025-04-16, ft-babbage-002, ft-davinci-002 | 2026-04-22 |

Recently passed: sora-2 family and the Videos API (2026-09-24); gpt-3.5-turbo-instruct, babbage-002, davinci-002, gpt-3.5-turbo-1106 (2026-09-28); gpt-5.4-cyber (2026-10-01).

## Announcement sections on the page (newest first)

Upcoming: 2026-10-01 (GPT-5.3-Codex, GPT-5.1, GPT-5.4-Nano), 2026-10-01 (text-to-speech), 2026-08-26 (transcription), 2026-07-20 (legacy audio, realtime, transcription), 2026-06-11 (GPT-5 and o3), 2026-06-03 (reusable prompts; evals platform; Agent Builder), 2026-06-02 (GPT Image), undated (self-serve fine-tuning, notice 2026-05-07).
Past: 2026-09-11 (GPT-5.4-Cyber), 2026-05-08 (gpt-5.2-chat-latest, gpt-5.3-chat-latest), 2026-04-22 (legacy snapshots, October 2026), 2026-04-22 (legacy snapshots, July 2026), 2026-03-24 (Sora 2), 2025-11-18 (chatgpt-4o-latest), 2025-11-17 (codex-mini-latest), 2025-11-14 (DALL-E), 2025-09-26 (legacy snapshots, 2026-09-28), 2025-09-26 (legacy snapshots, March 2026), 2025-09-15 (Realtime beta; gpt-4o-realtime-preview), 2025-08-20 (Assistants API), 2025-06-10 (two realtime/audio previews), 2025-04-28 (text-moderation; o1-preview and o1-mini), 2025-04-14 (GPT-4.5-preview), 2024-10-02, 2024-08-29, 2024-06-06, 2023-11-06, 2023-08-22, 2023-07-06, 2023-06-13, 2023-03-20, 2022-06-03.

## Text-model rows with their dates (every language-model identifier on the page; audio, image, video, embedding, moderation and endpoint rows omitted here, full list in the agent transcript of 2026-10-11)

| identifier | shutdown | replacement | section |
| --- | --- | --- | --- |
| gpt-5.3-codex | 2027-04-01 | gpt-6-sol | 2026-10-01 |
| gpt-5.4-nano | 2027-04-01 | gpt-6-luna | 2026-10-01 |
| gpt-5.1 | 2027-04-01 | gpt-6-sol | 2026-10-01 |
| gpt-5-2025-08-07 | 2026-12-11 | gpt-5.6-sol | 2026-06-11 |
| gpt-5-mini-2025-08-07 | 2026-12-11 | gpt-5.6-terra | 2026-06-11 |
| gpt-5-nano-2025-08-07 | 2026-12-11 | gpt-5.6-luna | 2026-06-11 |
| gpt-5-pro-2025-10-06 | 2026-12-11 | gpt-5.6-sol (reasoning.mode pro) | 2026-06-11 |
| o3-2025-04-16 | 2026-12-11 | gpt-5.6-sol | 2026-06-11 |
| o3-pro-2025-06-10 | 2026-12-11 | gpt-5.6-sol (reasoning.mode pro) | 2026-06-11 |
| gpt-5.4-cyber | 2026-10-01 | (the most capable cyber model available) | 2026-09-11 |
| gpt-5.2-chat-latest, gpt-5.3-chat-latest | 2026-08-10 | gpt-5.6-sol | 2026-05-08 |
| gpt-3.5-turbo-0125 (gpt-3.5-turbo) | 2026-10-23 | gpt-5.6-terra | 2026-04-22 |
| gpt-4-0613 (gpt-4) | 2026-10-23 | gpt-5.6-sol | 2026-04-22 |
| gpt-4-1106-preview | 2026-10-23 (also 2026-03-26 in the 2025-09-26 table) | gpt-5.6-sol | 2026-04-22 |
| gpt-4-turbo (gpt-4-turbo-2024-04-09) | 2026-10-23 | gpt-5.6-sol | 2026-04-22 |
| gpt-4.1-nano (gpt-4.1-nano-2025-04-14) | 2026-10-23 | gpt-5.6-luna | 2026-04-22 |
| gpt-4o-2024-05-13 | 2026-10-23 | gpt-5.6-sol | 2026-04-22 |
| o1-2024-12-17 (o1) | 2026-10-23 | gpt-5.6-sol | 2026-04-22 |
| o1-pro-2025-03-19 (o1-pro) | 2026-10-23 | gpt-5.6-sol (reasoning.mode pro) | 2026-04-22 |
| o3-mini-2025-01-31 (o3-mini) | 2026-10-23 | gpt-5.6-sol | 2026-04-22 |
| o4-mini-2025-04-16 (o4-mini) | 2026-10-23 | gpt-5.6-terra | 2026-04-22 |
| computer-use-preview-2025-03-11, gpt-4o-mini-search-preview-2025-03-11, gpt-4o-search-preview-2025-03-11 | 2026-07-23 | gpt-5.6-terra | 2026-04-22 |
| gpt-5-chat-latest, gpt-5-codex, gpt-5.1-chat-latest, gpt-5.1-codex, gpt-5.1-codex-max, gpt-5.2-codex, o3-deep-research, o4-mini-deep-research | 2026-07-23 | gpt-5.6-sol | 2026-04-22 |
| gpt-5.1-codex-mini | 2026-07-23 | gpt-5.6-terra | 2026-04-22 |
| chatgpt-4o-latest | 2026-02-17 | gpt-5.1-chat-latest | 2025-11-18 |
| codex-mini-latest | 2026-02-12 | gpt-5-codex-mini | 2025-11-17 |
| gpt-3.5-turbo-instruct, babbage-002, davinci-002, gpt-3.5-turbo-1106 | 2026-09-28 | gpt-5.6-terra | 2025-09-26 |
| gpt-4-0314, gpt-4-1106-preview, gpt-4-0125-preview (gpt-4-turbo-preview) | 2026-03-26 | gpt-5 or gpt-4.1 | 2025-09-26 |
| o1-preview | 2025-07-28 | o3 | 2025-04-28 |
| o1-mini | 2025-10-27 | o4-mini | 2025-04-28 |
| gpt-4.5-preview | 2025-07-14 | gpt-4.1 | 2025-04-14 |
| gpt-4-32k, gpt-4-32k-0613, gpt-4-32k-0314 | 2025-06-06 | gpt-4o | 2024-06-06 |
| gpt-4-vision-preview, gpt-4-1106-vision-preview | 2024-12-06 | gpt-4o | 2024-06-06 |
| gpt-3.5-turbo-0613, gpt-3.5-turbo-16k-0613 | 2024-09-13 | gpt-3.5-turbo | 2023-11-06 |
| gpt-3.5-turbo-0301 | 2024-09-13 | gpt-3.5-turbo | 2023-06-13 |
| text-ada-001, text-babbage-001, text-curie-001, text-davinci-001, text-davinci-002, text-davinci-003 | 2024-01-04 | gpt-3.5-turbo-instruct | 2023-07-06 |
| ada, babbage, curie, davinci, code-davinci-002 | 2024-01-04 | babbage-002 / davinci-002 / gpt-3.5-turbo-instruct | 2023-07-06 |
| code-davinci-002, code-davinci-001, code-cushman-002, code-cushman-001 | 2023-03-23 | gpt-4o | 2023-03-20 |

Notice policy stated on the page: generally available models at least 6 months; specialized variants (chat, Codex, deep-research) at least 3 months; preview models possibly 2 weeks.
