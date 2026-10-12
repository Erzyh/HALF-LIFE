# Anthropic model deprecations page, read 2026-10-11

Source: https://platform.claude.com/docs/en/about-claude/model-deprecations (HTTP 200, fetched by a web-reading agent; the table below is its extraction of every identifier on the page). Purpose: pre-submission check of the retirement vocabulary (target_models.json, 16 Anthropic identifiers). Compared by the first author on 2026-10-11: every date in the vocabulary matches the page; no deprecation announced on or after 2026-10-02; the newest announcement is 2026-09-30 (claude-sonnet-4-5-20250929, retirement 2026-11-30, still served). claude-mythos-preview is listed as deprecated since 2026-06-09 with retirement "to be announced" and no date, so it stays outside the retired-or-retiring vocabulary; tentative "not sooner than" dates of active models are not announcements.

| identifier | deprecated on | retired on | state | replacement (as shown today) |
| --- | --- | --- | --- | --- |
| claude-fable-5-1 | N/A | not sooner than 2027-09-01 (tentative) | Active | - |
| claude-mythos-5-1 | N/A | not sooner than 2027-09-01 (tentative) | Active | - |
| claude-fable-5 | N/A | not sooner than 2027-06-09 (tentative) | Active | - |
| claude-mythos-5 | N/A | not sooner than 2027-06-09 (tentative) | Active | - |
| claude-mythos-preview | 2026-06-09 | to be announced | Deprecated | - |
| claude-opus-5-5 | N/A | not sooner than 2027-09-22 (tentative) | Active | - |
| claude-opus-5 | N/A | not sooner than 2027-07-24 (tentative) | Active | - |
| claude-opus-4-8 | N/A | not sooner than 2027-05-28 (tentative) | Active | - |
| claude-opus-4-7 | N/A | not sooner than 2027-04-16 (tentative) | Active | - |
| claude-opus-4-6 | N/A | not sooner than 2027-02-05 (tentative) | Active | - |
| claude-opus-4-5-20251101 | N/A | not sooner than 2026-11-24 (tentative) | Active | - |
| claude-opus-4-1-20250805 | 2026-06-05 | 2026-08-05 | Retired | claude-opus-4-8 |
| claude-opus-4-20250514 | 2026-04-14 | 2026-06-15 | Retired | claude-opus-4-8 |
| claude-sonnet-5-5 | N/A | not sooner than 2027-09-28 (tentative) | Active | - |
| claude-sonnet-5 | N/A | not sooner than 2027-06-30 (tentative) | Active | - |
| claude-sonnet-4-6 | N/A | not sooner than 2027-02-17 (tentative) | Active | - |
| claude-sonnet-4-5-20250929 | 2026-09-30 | 2026-11-30 (scheduled) | Deprecated | claude-sonnet-5-5 |
| claude-sonnet-4-20250514 | 2026-04-14 | 2026-06-15 | Retired | claude-sonnet-5-5 |
| claude-3-7-sonnet-20250219 | 2025-10-28 | 2026-02-19 | Retired | claude-sonnet-5-5 |
| claude-haiku-5-5 | N/A | not sooner than 2027-10-07 (tentative) | Active | - |
| claude-haiku-4-5-20251001 | N/A | not sooner than 2026-10-15 (tentative) | Active | - |
| claude-3-5-haiku-20241022 | 2025-12-19 | 2026-02-19 | Retired | claude-haiku-4-5-20251001 |
| claude-3-haiku-20240307 | 2026-02-19 | 2026-04-20 | Retired | claude-haiku-4-5-20251001 |
| claude-3-5-sonnet-20240620 | 2025-08-13 | 2025-10-28 | Retired | claude-sonnet-5-5 |
| claude-3-5-sonnet-20241022 | 2025-08-13 | 2025-10-28 | Retired | claude-sonnet-5-5 |
| claude-3-opus-20240229 | 2025-06-30 | 2026-01-05 | Retired | claude-opus-4-8 |
| claude-2.0 | 2025-01-21 | 2025-07-21 | Retired | claude-opus-4-8 |
| claude-2.1 | 2025-01-21 | 2025-07-21 | Retired | claude-opus-4-8 |
| claude-3-sonnet-20240229 | 2025-01-21 | 2025-07-21 | Retired | claude-sonnet-5-5 |
| claude-1.0, claude-1.1, claude-1.2, claude-1.3 | 2024-09-04 | 2024-11-06 | Retired | claude-haiku-4-5-20251001 |
| claude-instant-1.0, claude-instant-1.1, claude-instant-1.2 | 2024-09-04 | 2024-11-06 | Retired | claude-haiku-4-5-20251001 |

Announcement sections on the page, newest first: 2026-09-30, 2026-06-05, 2026-04-14, 2026-02-19, 2025-12-19, 2025-10-28, 2025-08-13, 2025-06-30, 2025-01-21, 2024-09-04.

Page notes: dates apply to Anthropic-operated platforms (Claude API, Claude Platform on AWS, Microsoft Foundry); partner platforms set their own schedules; at least 60 days' notice before retirement. API parameters temperature, top_p and top_k are deprecated for Claude 4.7 and later models (400 error on non-default values).
