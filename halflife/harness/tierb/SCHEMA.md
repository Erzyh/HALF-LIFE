# Tier B triage record (one JSON per paper, harness/tierb/<Wid>.json)

Purpose: decide whether a paper can be re-executed *without its code*: the exact prompt is printed
in the paper, one reported number is tied to a still-callable model, and the inputs are public.

```json
{
  "openalex_id": "W...", "title": "...",
  "verdict": "eligible | maybe | ineligible",
  "live_model": {
    "id_in_text": "gpt-4-turbo",
    "resolved": "gpt-4-turbo-2024-04-09 | gpt-4o-2024-05-13 | dead-preview | unresolved",
    "role": "S | B | A | C",
    "evidence": "quote of at most 200 characters + location (section/table)"
  },
  "prompt": {"verbatim": "full | partial | none", "location": "Appendix B / Figure 2 / Section 3.2", "note": ""},
  "claim": {
    "metric": "accuracy", "value": 0.83, "n_items": 500, "location": "Table 2, row GPT-4 Turbo",
    "task_type": "mcq | classification | extraction | generation | agentic | other",
    "judge": "none | human | llm:<model id>"
  },
  "data": {"public": "yes | partial | no", "source": "dataset name / URL / printed in the paper"},
  "cost": {"est_calls": 500, "tier": "low | mid | high"},
  "blockers": ["webui", "human_outcome", "dead_alias", "data_closed", "tos", "aux_model_dead", "no_number"],
  "notes": ""
}
```

Rules
- role S/B = the authors ran the live model and report its result; A = judge/annotator/parser only; C = mention only.
- eligible = role S or B, prompt full or partial, a numeric claim with n_items, data public or printed, no blockers.
- maybe = one soft gap (prompt partial with a clear template, or n_items unclear).
- ineligible otherwise; always fill blockers.
- Alias rule: "GPT-4 Turbo" in a paper dated before 2024-04-09, or alongside 1106/0125-preview strings, is a dead
  preview (blocker dead_alias). After 2024-07-01 with no preview string, resolve to gpt-4-turbo-2024-04-09.
- cost tiers at 3 seeds: low < $5, mid $5-30, high > $30 (gpt-4-turbo ~ $0.01 per short call; gpt-4o-2024-05-13 ~ $0.005;
  o-series ~ $0.05-0.2).
- Quote sparingly (<= 200 characters per field); never reproduce full prompts into the record, cite their location.
