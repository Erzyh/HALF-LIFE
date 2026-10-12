# Tier B batch 1 triage, group 1 (2026-09-09)

Scope: seven re-runs whose number fell outside the original's neighbourhood. Only hooks/configs were changed and
`--analyze` re-run on the archived replies; no model calls, no spend. Superseded result files are kept as
`runs/tierb/<wid>/result_before_triage.json`.

| wid | class | original | re-run before | re-run after fix | n | what was wrong / what changed |
|---|---|---|---|---|---|---|
| W4414494504 PGxRAG (gpt-4-turbo LLM-only, acc) | DEFECT (parse) | 80.89 | 8.15 (581 unparsed) | **78.81** (seeds 78.2 / 79.6 / 78.7; 22 unparsed; 80.89 inside every seed's CI) | 225 x 3 seeds | Replies answer as `The correct answer is "C": "..."` or open with `"B": "..."` (566/675); the hook had no quoted-letter rule and `(?i)` on the letter class read the article "a" as option A. |
| W4411080278 temperature-driven diagnostic variability (gpt-4o, leading-dx acc) | MIXED | 100 | 50.07 | **25.00** (all seeds) | 1,000 x 3 | Hook searched the whole first line, so "Hypothyroidism: ... potentially myxedema coma" was credited via its explanation; the paper's keyword rule applies to the listed diagnosis. After the fix only carbon-monoxide items pass: the model now leads with the broader parent condition for the other three cases. |
| W7166799942 CMTD, MELD Text-only (gpt-4.1-nano, acc) | MIXED (protocol gap) | 42.45 | 13.22 | 13.22 (no fix; extended-synonym sensitivity 30.9) | 2,610 utterances (280 calls) x 3 | Printed prompt (= repo `prompts/text_only.txt`, verified) names no label set; the model returns free emotion phrases and 1,705/2,610 utterances stay unlabelled under the 7-label parse; the paper does not say how it mapped them. Status -> needs_human. |
| W4401545735 FPB financial sentiment (gpt-4o, acc) | DEVIATION | 74.57 | 89.53 | **89.83** (first-occurrence parse) | 2,264 x 3 | Subset (2,264 all-agreement = Table 2) and cell (Table 4 "GPT-4" = naive gpt-4o) are right; the pinned snapshot simply classifies FPB better than the paper's naive cell. Small hook fix (list-order vs first-occurrence label, 21 replies). |
| W7164614711 M-EDESConv validate / non-validate (gpt-4.1-nano, macro-F1) | DEVIATION | 51.68 | 41.56 | 41.56 (config's no-match default: 42.0) | 12,780 x 3 | Cell right (Multilingual block, M-EDESConv). Validate-class F1 matches the paper (53.4 vs 54.41) but the model now says "validate" for 83% of utterances (about 69% implied by the paper's P/R), halving non-validate F1. |
| W4406880877 o1 AI-text detector (o1-2024-12-17, TPR) | DEFECT (runner) | 54 | 30.0 | **54.67** (sha-matched, CI 46.7-62.7; per block 80.0 / 96.7 / 56.7 / 23.3 / 16.7) | 150 x 1 | items.jsonl carries 61 distinct ids for 150 articles; `analyze()` keys replies by (id, seed), so 89 items were scored against another article's reply. Needs a runner patch; corrected file `result_sha_matched.json`. Status -> needs_human. |
| W4399911213 WikiContradict judge (gpt-4-turbo, acc) | MIXED | 86.7 | 76.67 | **81.11** (seeds 81.3 / 80.4 / 81.7) | 240 x 3 | 341/720 replies omit the `evaluation:` line; the fallback "last label anywhere" picked `correct` out of "one of the correct answers" (72 replies). Remaining gap: the judge itself labels partially-correct responses as incorrect/correct. |

## Per paper

### W4414494504 PGxRAG - DEFECT (parse), fixed
- Archived replies (gpt-4-turbo-2024-04-09, 10 fingerprints) never use the paper's Table 1 JSON response; they echo the query's quoted keys:
  `The correct answer is "A": "Phenytoin, Fosphenytoin, Carbamazepine, Oxcarbazepine".` /
  `"B": "It assesses the enzyme Dihydropyrimidine dehydrogenase (DPD) activity..."` /
  `The correct answer is:\n**A**: "Increase the dose to 150% of the standard dose..."`
- Old hook: JSON key, `correct answer is X`, then `\b([A-D])[\.\):]` anywhere, all with `re.I` -> 581/675 unparsed and false letters from "is a ...", "vitamin D." (8.1%).
- New hook (`harness/tierb/hooks/W4414494504.py`): JSON key -> last explicit answer statement -> first quoted/bold letter with colon -> single named `Option X` -> single line-start letter; uppercase letters only. Rule usage: statement 417 (330 correct), quoted 189 (166), JSON 12 (12), option/line 35 (24), none 22.
- Residual: 22 letter-less free-text replies count as wrong (the paper's SMEs mapped those by hand); 5 replies enumerate several quoted letters without a choice statement (ids 49, 119, 209) - at most +/-1 pp. Format deviation only (prose + explanation instead of JSON); the selected options reproduce the paper (78.8 vs 80.9).

### W4411080278 Temperature-driven diagnostic variability - MIXED
- Paper Methods: keyword search on the listed leading diagnosis (myxedema | cholangitis | carbon monoxide / co | cryptococcal meningitis ...). The hook returned the entire first list item, explanation included, so `1. **Hypothyroidism**: ... consistent with severe hypothyroidism, potentially myxedema coma.` scored correct (myxedema 100%), while cholangitis and cryptococcal scored 0 -> 50.1%.
- Fixed hook: diagnosis name = leading bold segment or text before `: ` -> 25.0% on all three seeds (CO 750/750; the other three cases 0/750).
- Deviation part (model, pinned gpt-4o-2024-05-13, 3 fingerprints): leading diagnoses are now the broader parents plus an explanation per item, despite "single condition without qualifiers":
  `1. **Hypothyroidism**: The patient's bradycardia, hypotension, hypothermia, dry skin...` (750/750),
  `1. **Cholecystitis**: The patient's right upper quadrant pain, mild scleral icterus, and jaundice...` (750/750),
  `1. **Meningitis**: The patient's presentation of a severe headache, myalgias, vomiting, and confusion...` (749/750).
  Only `1. Carbon monoxide poisoning` survives. Transcription of the Table 1 vignettes (separators assumed) cannot be excluded as a cause; both numbers (25.0 strict / 50.1 whole-line) are recorded in the config.

### W7166799942 CMTD MELD Text-only - MIXED (protocol gap), needs_human
- Prompt verified verbatim against the paper's Table 6 and the repository file `Shaun-le/CMTD/prompts/text_only.txt`: no label set, no output format.
- gpt-4.1-nano-2025-04-14 (pinned) answers per numbered utterance with free phrases:
  `1. Mark: Curious or inquisitive  \n2. Rachel: Amused or playful  \n3. Rachel: Frustrated or annoyed` /
  `1. Joey: Come on, Lydia, you can do it. - Encouragement / Support` /
  `**Emotion:** Understanding / Neutral`.
- Under the 7 MELD labels + small synonym map, 1,705 of 2,610 utterances are unlabelled (65%) -> 13.2% (per seed 13.4/12.9/13.3). An extended deterministic synonym map (scratch only) gives 31.2/29.9/31.8 with 111 unlabelled - still 11 pp below the paper's 42.45. The paper does not describe any mapping, so the number is not interpretable as a model deviation; a decision on the mapping rule is needed (offline), or the gap is a reporting gap. A label-set prompt would be our design (840 calls x 3, about USD 0.02-0.36).

### W4401545735 FPB - DEVIATION (small parse fix applied)
- Paper: Table 2 FPB total 2,264 (all-agreement) and Table 4 row "GPT-4" = naive prompting with gpt-4o-2024-05-13 (Acc 74.57, F1 77.99); config subset and cell are right. The naive prompt itself is only shown as Fig. 3 (image); the config uses the BloombergGPT template quoted in Sec. 2.2.
- Replies are clean single labels (`Positive.`, `The sentiment is neutral.`); per-seed confusion neutral->positive 108, positive->neutral 48, neutral->negative 27; the model is simply more accurate than the paper's cell (89.8 vs 74.6), and the snapshot is pinned (6 fingerprints), so the gap is on the paper's side (prompt wording / parsing), not drift.
- Hook `W4401545735.py`: first-occurrence label (the runner's `label from set` returned the first label in list order, reading `Neutral. ... does not convey any positive or negative sentiment` as negative in 21 replies): 89.53 -> 89.83.
- Limitation recorded as an open point: `max_tokens=16` truncates 1,404 of 6,792 replies; 53 per seed end before any label (`The sentiment of the statement "The project is expected...`) and count as wrong (52 are gold neutral) - at most +2.3 pp, needs a re-run to fix.

### W7164614711 M-EDESConv - DEVIATION
- Cell right (Table 2 Multilingual block, M-EDESConv Overall M-F1 51.68; target P/R/F1 41.43/79.25/54.41). Replies are bare labels: `validate` 10,645, `non-validate` 2,051, plus 77 `Please provide the utterances you'd like me to classify.`
- Our validate-class P/R/F1 38.3/88.0/53.4 reproduces the paper's F1 (54.41); the difference is the validate rate (83% vs about 69%), which cuts non-validate F1 to 29.7 (paper about 49) -> macro 41.5 (per seed 41.5/41.4/41.7). Per language: en 44.3 (paper 55.36), ja 37.5 (paper 47.03). The config's declared "no match = non-validate" default (not applied by the runner) would give 42.0.
- Pinned snapshot (9 fingerprints); most plausible cause is prompt placement/separator (the utterance is appended without a marker; 77 replies ask for the utterances). Nothing to fix offline.

### W4406880877 o1 AI-text detector - DEFECT (runner), needs_human
- Prompt = Table 20 verbatim; `reasoning_effort: medium` = footnote 22; 150 items with gold AI-GENERATED; all 150 replies carry `<answer>...</answer>`; parse fine.
- Bug: `human_detectors.json` is a dict keyed '0'-'299' whose records carry their own non-unique `id`; `tierb_runner._parse_table` builds `{"id": key, **record}`, so the record's `id` shadows the key -> 61 distinct ids for 150 items. `battery.load_results`/`analyze()` key replies by (id, seed_idx): 89 items were scored against another article's reply -> TPR 30.0.
- Re-matching each item to its own call through `sha_request` (= sha256 of the request body, all 150 distinct): TPR 54.67 (82/150), CI 46.7-62.7, paper 54 (inside CI); per 30-article block in release order 80.0 / 96.7 / 56.7 / 23.3 / 16.7 vs the paper's per-experiment 83.3 / 53.3 / 96.7 / 20 / 16.7. Written to `runs/tierb/W4406880877/result_sha_matched.json` (runner schema). `result.json` stays wrong until the runner is patched (patch spelled out in the config's open_points).
- Scan of all 73 run directories: this is the only run with duplicate item ids.

### W4399911213 WikiContradict judge - MIXED
- Format deviation: 341 of 720 replies drop the Appendix C `evaluation:` line and end with a verdict sentence: `...Thus, the response is partially correct.` (120), `Therefore, the response is partially correct as it only matches with one of the correct answers...`
- Parse defect: the fallback took the last label anywhere, so the phrase "correct answers" turned 72 replies into `correct` (e.g. `mixtral:2`, `:6`, `:26`, gold partially correct). New hook: `evaluation:` (379) -> last verdict sentence (339) -> bare label not followed by answer(s)/response (2); 0 unparsed; no reply has conflicting verdict sentences. 76.67 -> 81.11.
- Remaining gap (81.1 vs 86.7) is the judge's behaviour: over 3 seeds it calls 53/510 human-"partially correct" responses incorrect (`The response is incorrect because it only provides one answer ("No") and does not acknowledge...`), 44/510 correct (`The response is correct because it matches with one of the correct answers ("No")...`), and 18/60 human-"incorrect" correct. Pinned gpt-4-turbo-2024-04-09, 10 fingerprints.

## Runner-level defects noticed
1. **Duplicate item ids silently mis-pair replies.** `_parse_table` (dict-of-records branch) does `{"id": k, **v}`, letting a record's own `id` overwrite the unique key; `prepare()` has no uniqueness check; `battery.load_results` and `analyze()` key by `(id, seed_idx)`, so the last reply with a given id is scored for every item sharing it. Hit W4406880877 (150 items -> 61 keys, TPR 30 instead of 54.7). Fix: keep the key (e.g. `{**v, "id": k}`), raise `NeedsHuman` on duplicate ids in `prepare()`, and match by `sha_request` in `analyze()` as a fallback.
2. **`parse_output("label from set ...")` returns the first label in list order, not the first occurrence in the text** (`hits[0]` over the label list). FPB: 21 replies of the form "Neutral. ... no positive or negative sentiment" parsed as negative; configs that say "first occurrence" are not honoured. Configs work around it by ordering the label list (W7164614711 lists non-validate first).
3. Cosmetic: `result.json` reports `unparsed` summed over all seeds next to a per-seed `n` (e.g. 581 for 225 x 3), which reads like an impossible count.
4. Generic parsers ignore the model's answer format for MCQ hooks written before the run (PGxRAG): worth a dry `--analyze` on the first 20 archived replies of every queue run before the batch is summarised.

Note on "deviation of the still-alive model": five of the seven models are dated snapshots (gpt-4o-2024-05-13, gpt-4.1-nano-2025-04-14, o1-2024-12-17, gpt-4-turbo-2024-04-09). Where the pipeline is faithful and the number still differs (FPB, M-EDESConv, CMTD), the more likely reading is an unreported paper-side step (prompt wording, mapping, parsing) rather than served-model drift.
