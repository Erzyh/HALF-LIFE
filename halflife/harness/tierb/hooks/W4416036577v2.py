"""Hook W4416036577v2 (variant with source-domain demonstrations) (cross-domain rumor detection, GPT-4o 'base' prompt on Twitter-COVID19, Table 1 accuracy).

load_items -> reads the two files unpacked from data/Twitter/COVID-19/Twitter-COVID19.7z of the Lin et al. (2022)
              ACLR4RUMOR release (unpacked once with py7zr into external/data/tierb_items/W4416036577/extracted/):
                Twitter_label_all.txt   event_id \t label          (1 = rumor, 0 = non-rumor: 252 / 148 as in Sec. 4.1)
                Twitter_data_all.txt    event_id \t parent_idx \t post_idx \t time_delay \t text, one line per post;
                                        the source post of an event has parent_idx 'None'.
              Rows: {id: event_id, event_content: source post text, label: 'rumor' | 'non-rumor'}. Only the 400
              labelled events are kept (the data file holds 402); the thread replies are not used (config approximation).
No render / parse / score: the config's regex parse and accuracy metric are runner facilities.
"""
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4416036577" / "extracted"
LABELS = {"1": "rumor", "0": "non-rumor"}
SOURCE = DATA.parent / "source"          # data/Twitter of the ACLR4RUMOR release (source domain of the Table 1 block)
_DEMOS = []


def demonstrations():
    """Four source-domain examples (2 rumor, 2 non-rumor), seeded, rendered in the base prompt's answer format."""
    if _DEMOS:
        return _DEMOS[0]
    import random
    labels = {}
    for line in (SOURCE / "Twitter_label_all.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            eid, y = line.rstrip("\n").split("\t")[:2]
            labels[eid] = LABELS.get(y.strip())
    roots = {}
    with open(SOURCE / "Twitter_data_all.txt", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 5 and parts[1] == "None" and parts[0] in labels and labels[parts[0]]:
                roots.setdefault(parts[0], parts[4])
    rng = random.Random(20260907)
    picked = []
    for lab in ("rumor", "non-rumor"):
        pool = sorted(eid for eid in roots if labels[eid] == lab)
        picked += [(eid, lab) for eid in rng.sample(pool, 2)]
    rng.shuffle(picked)
    block = "\n".join(f"Event: \n{roots[eid]}\nAnswer: [\"answer\":\"{lab}\"]" for eid, lab in picked)
    _DEMOS.append(block)
    return block


def load_items(cfg):
    if not (DATA / "Twitter_label_all.txt").exists():
        raise NeedsHuman(f"unpack Twitter-COVID19.7z into {DATA} (py7zr) before --prepare")  # noqa: F821 (injected by the runner)
    labels = {}
    for line in (DATA / "Twitter_label_all.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            eid, y = line.rstrip("\n").split("\t")[:2]
            labels[eid] = LABELS[y.strip()]
    roots = {}
    with open(DATA / "Twitter_data_all.txt", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 5 and parts[1] == "None" and parts[0] in labels:
                roots.setdefault(parts[0], parts[4])
    rows = [{"id": eid, "event_content": roots[eid], "label": labels[eid], "demonstrations": demonstrations()} for eid in labels if eid in roots]
    if len(rows) != len(labels):
        raise NeedsHuman(f"{len(labels) - len(rows)} labelled events have no source post")  # noqa: F821
    return rows


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    from collections import Counter
    print(len(rows), Counter(r["label"] for r in rows), rows[0])
