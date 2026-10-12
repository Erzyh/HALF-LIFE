"""Hook W7126280993 (WhatCounts, o3 semantic gap under the explicit-separator prompt, Table 1).

load_items -> reads the 24 archived benchmark reports of the explicit-separator condition
              (6 semantic classes x 4 count ranges x 20 questions = 480 items) that were downloaded from
              github.com/lamalab-org/whatcounts into external/data/tierb_items/W7126280993/reports/ as
              <entity>_<range>.json (source paths in reports/_index.json; upstream name
              "<entity>- | -range_<lo>-<hi>-20-default-general_entity_report.json" under
              reports/o3/reports/shuffle_entity/general_entity/reports/default_benchmark/).
              Every record carries the exact user message that was sent and the gold count in targets[0];
              the message is split back into list text / field name so the config can render the same
              string from its own template, and the split is verified by re-assembling it.
score      -> per-class accuracy (exact count match) over that class's 80 questions, then
              Delta_sem = max_class - min_class. Set-level, so no per-item vector is returned.

The paper's own numbers for this condition (data/semantic_gap_all_ablations.json, key
shuffle_entity_general_entity, model o3): addresses .8625 chemicals .5625 cities .9625 names .9375
phones .9125 symbols .9375 -> Delta_sem = .9625 - .5625 = 0.400 = Table 1.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W7126280993" / "reports"
ENTITIES = ["addresses", "chemicals", "cities", "names", "phones", "symbols"]
RANGES = ["7-17", "85-115", "550-650", "950-1050"]
HEAD = "The following is a question that you must answer as truthfully as possible.\n\nQuestion: "
TAIL_RE = re.compile(r"\n\nHow many (?P<field>.+?) separated by '(?P<sep>[^']*)' are above\?\n\n(?P<rest>.*)\Z", re.S)


def load_items(cfg):
    rows = []
    for entity in ENTITIES:
        for rng in RANGES:
            path = DATA / f"{entity}_{rng}.json"
            if not path.exists():
                raise NeedsHuman(f"missing {path}; re-download the 24 explicit-separator reports "  # noqa: F821
                                 f"(see items.download in the config)")
            report = json.loads(path.read_text(encoding="utf-8"))
            for rec in report["results"]:
                msg = rec["prompts"]["batch"][0]["messages"]
                if len(msg) != 1 or msg[0]["role"] != "user":
                    raise NeedsHuman(f"{path.name}: unexpected message shape {msg!r}")  # noqa: F821
                content = msg[0]["content"]
                m = TAIL_RE.search(content)
                if not content.startswith(HEAD) or not m:
                    raise NeedsHuman(f"{path.name}: archived prompt does not match Listing 2's wrapper")  # noqa: F821
                list_text = content[len(HEAD):m.start()]
                rows.append({
                    "id": rec["uuid"],
                    "entity": entity,
                    "count_range": rng,
                    "list_text": list_text,
                    "field_name": m.group("field"),
                    "separator": m.group("sep"),
                    "gold": f"{entity}|{rec['targets'][0]}",
                    "archived_prompt": content,
                })
    if len(rows) != 480:
        raise NeedsHuman(f"expected 6 classes x 4 ranges x 20 = 480 questions, built {len(rows)}")  # noqa: F821
    return rows


def score(preds, golds, cfg):
    hit, tot = defaultdict(int), defaultdict(int)
    for p, g in zip(preds, golds):
        entity, target = str(g).split("|")
        tot[entity] += 1
        try:
            hit[entity] += 1 if p is not None and abs(float(p) - float(target)) < 1e-9 else 0
        except (TypeError, ValueError):
            pass
    acc = {e: hit[e] / tot[e] for e in tot if tot[e]}
    if len(acc) < 2:
        return 0.0, None
    return max(acc.values()) - min(acc.values()), None


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    template = (HEAD + "{list_text}\n\nHow many {field_name} separated by '{separator}' are above?\n\n"
                "You MUST include the final answer within the following tags: [ANSWER] and [/ANSWER].\n"
                "For example, '[ANSWER]<answer>[/ANSWER]', where <answer> is only one number. Always answer "
                "in exactly this format, with ONE NUMBER between the two tags, even if you are unsure. "
                "Use dots as decimal separator. We require this because we use automatic parsing.")
    bad = [r["id"] for r in rows
           if template.format(**{k: r[k] for k in ("list_text", "field_name", "separator")}) != r["archived_prompt"]]
    print(len(rows), "items; template mismatches:", len(bad))
    from collections import Counter
    print(Counter(r["entity"] for r in rows), Counter(r["separator"] for r in rows))
    print({r["id"]: r["gold"] for r in rows[:3]})
    # the paper's own per-class accuracies reproduce Table 1 when fed to score()
    paper = {"addresses": .8625, "chemicals": .5625, "cities": .9625, "names": .9375, "phones": .9125, "symbols": .9375}
    fake_g, fake_p = [], []
    for e, a in paper.items():
        for i in range(80):
            fake_g.append(f"{e}|1")
            fake_p.append("1" if i < round(a * 80) else "2")
    print("score() on the paper's own per-class accuracies:", round(score(fake_p, fake_g, {})[0], 4), "(Table 1: 0.400)")
