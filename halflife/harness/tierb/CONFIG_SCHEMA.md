# Tier B run config (one JSON per eligible paper, harness/tierb/configs/<Wid>.json)

The Tier B runner executes exactly what this file says: format each public item with the paper's
prompt, call the still-callable model with the stated parameters, parse the answer, compute one
metric, and compare it with the paper's reported value. Nothing else is consulted at run time.

```json
{
  "wid": "W...", "title": "...",
  "status": "ready | needs_download_check | needs_human",
  "model": {
    "id": "gpt-4-turbo-2024-04-09",
    "params": {"temperature": 0.0, "max_tokens": 512, "top_p": 1.0},
    "params_source": "paper Sec. 4.2 | assumed (paper silent) | ANALYSIS_PLAN default",
    "seeds": 3
  },
  "task": {
    "type": "mcq | classification | extraction | generation | other",
    "n_items": 500,
    "subset_rule": "all | seeded random N (seed 20260907) | paper-defined split <name>",
    "approximation": "none | what differs from the paper's exact setup"
  },
  "items": {
    "source_type": "hf | github | zenodo | url | in_paper",
    "source": "org/dataset or URL or 'Table 1 of the paper'",
    "config_or_split": "test",
    "filter": "e.g. subject == 'law'; none",
    "fields": {"input": "question", "options": "choices", "label": "answer", "id": "id"},
    "license": "as stated on the source page or 'unknown'",
    "access_checked": true,
    "size_mb": 12
  },
  "prompt": {
    "system": "verbatim system prompt or null",
    "user_template": "verbatim user prompt with {placeholders}",
    "placeholders": {"question": "items.input", "options": "items.options formatted as 'A. ...\nB. ...'"},
    "few_shot": "none | k=3 fixed examples printed in the paper | k=5 seeded from <split>",
    "source_location": "Appendix B.1",
    "verbatim": "full | partial (what was reconstructed)"
  },
  "output": {
    "parse": "letter (A-E) | label from set [...] | json field <name> | regex <pattern> | free text",
    "postprocess": "strip, lowercase, take first match; none"
  },
  "metric": {
    "name": "accuracy | macro_f1 | micro_f1 | exact_match | rouge_l | mean_error | custom",
    "definition": "one sentence; for custom, the formula",
    "judge": "none | rule | llm:<model id>, prompt location <...>",
    "original_value": 0.83,
    "original_location": "Table 2, row GPT-4 Turbo",
    "bootstrap_unit": "item"
  },
  "cost": {"est_calls": 1500, "est_usd": 12.0, "tier": "low | mid | high"},
  "open_points": ["anything a human must decide before the run"],
  "notes": ""
}
```

Rules
- Copy prompts verbatim from the paper text (these configs are internal working files in a private repository and are not redistributed). If the extraction mangled the prompt (line breaks inside words, missing braces), repair only what is unambiguous and say so in prompt.verbatim.
- Do not download datasets larger than 50 MB and never call a model API. A HEAD/GET of the dataset page to confirm it exists and to read the license is enough; set access_checked accordingly.
- params: if the paper does not state temperature, use 0.0 and mark params_source "assumed"; max_tokens generous enough for the answer format.
- seeds: 3 for low/mid cost tiers, 1 for high (item-level bootstrap gives the CI).
- status: "ready" only when every field is filled and the items source was confirmed; "needs_download_check" when the source exists but fields/splits could not be verified without downloading; "needs_human" when an open point remains.
- Never propose contacting the authors.

## Machine fields (required before a config can run; added 2026-09-07)

The runner (harness/tierb_runner.py) reads only these strict fields. Prose in the other fields is kept
for humans. A config is "ready" only when `python harness/tierb_runner.py <Wid> --prepare` succeeds.

```json
"items": {
  "hf": {"dataset": "qiaojin/PubMedQA", "config": "pqa_labeled", "split": "train"},   // source_type hf
  "file_url": "https://raw.githubusercontent.com/org/repo/main/data/test.jsonl",       // github / url / zenodo
  "inline": [{"id": "1", "question": "...", "answer": "A"}],                            // in_paper
  "fields": {"input": "question", "options": "choices", "label": "answer", "id": "id"}, // exact column names
  "label_map": {"maybe": "unanswerable"},                                                // optional gold remap
  "filter": "subject == 'law'"                                                           // pandas query or null
},
"prompt": {
  "placeholders": {"q": "items.question", "opts": "options_lettered(choices)", "ctx": "join(CONTEXTS, ' ')", "k": "literal:5"}
},
"output": {"parse": "letter | label from set [yes, no, unanswerable] | json field rating | regex Answer:\s*([A-E]) | number | free text"},
"metric": {"name": "accuracy | exact_match | macro_f1 | micro_f1 | rouge_l | mean_abs_error | pearson", "scale": 100, "original_value": 61.2}
```

- `metric.scale`: factor that maps the runner's 0-1 output to the paper's units (100 when the paper reports percent).
- Options stored as a list or a dict both work with options_lettered; a dict keeps its own keys.
- `output.parse` "letter" returns the first standalone capital letter A-J; gold labels must then be letters too
  (use `label_map` to convert an index or an option text into the letter).

## Per-paper hooks (added 2026-09-07)

When the mini-language is not enough, a config may ship a Python hook at harness/tierb/hooks/<Wid>.py.
The runner imports it and uses whichever of these functions exist (all optional):

```python
def load_items(cfg): ...                      # -> list of row dicts (replaces items.* loading)
def render(cfg, row): ...                     # -> [{"role": "system"|"user"|"assistant", "content": ...}]
def parse(text, cfg): ...                     # -> prediction (any type the scorer understands) or None
def score(preds, golds, cfg): ...             # -> (value, per_item_list or None); per-item gives the bootstrap CI
def judge_requests(cfg, items, responses): ...           # -> battery requests for an LLM-judge stage (run with --judge)
def score_with_judge(cfg, items, responses, judge_responses): ...  # -> (value, per_item or None)
```
`items` are the rows of runs/tierb/<Wid>/items.jsonl ({id, gold, messages}); `responses` and `judge_responses`
map (id, seed_idx) -> archived call records (see battery.load_results). Hooks must not call any API
themselves and must be deterministic (seed every shuffle with 20260907). Keep them under 200 lines.
