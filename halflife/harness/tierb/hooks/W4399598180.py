"""Hook W4399598180 (HalluDial hallucination detection, gpt-4o-2024-05-13, Table 2 accuracy).

load_items -> reads the HalluDial JSON files cached under external/data/tierb_items/W4399598180/ (Google Drive folder
              19POyHTlLc3iQKKR4oonZzIGLEQ94Wyjl, the same files the HF loading script FlagEval/HalluDial fetches):
              spontaneous_test.json + induced_test.json when they exist (the paper's evaluation split - NOT released, see
              github.com/flageval-baai/HalluDial issue #1), otherwise, only if items.use_public_train_sample is true, the
              public 10,000-row samples spontaneous/spontaneous_train.json and induced/induced_train.json (read from
              spontaneous.zip / induced.zip). Fields per row: dialogue_id, knowledge, dialogue_history, turn, response,
              target ("Yes. <rationale>" | "No." | "No. <...>"). The hook adds label = "Yes" | "No" from the first word of
              target, id = "<scenario>:<split>:<dialogue_id>:<turn>:<row index>", scenario and split; rows whose target starts with
              neither word (6 of the 20,000 public rows: "ERR", "Inc...", "###") are dropped and counted in
              items.dropped_malformed_target.
No render / parse / score: the config's "label from set [Yes, No]" parse and accuracy are runner facilities.
"""
import json
import zipfile
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4399598180"
SCENARIOS = ("spontaneous", "induced")


def _read(scenario, split):
    p = DATA / f"{scenario}_{split}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    z = DATA / f"{scenario}.zip"
    if split == "train" and z.exists():
        with zipfile.ZipFile(z) as zf:
            return json.loads(zf.read(f"{scenario}/{scenario}_{split}.json").decode("utf-8"))
    return None


def load_items(cfg):
    split = "test"
    data = {s: _read(s, "test") for s in SCENARIOS}
    if any(v is None for v in data.values()):
        if not (cfg.get("items") or {}).get("use_public_train_sample"):
            raise NeedsHuman("HalluDial test split (spontaneous_test.json / induced_test.json) is not public; set "  # noqa: F821
                             "items.use_public_train_sample = true to run on the released 10k-row train samples instead")
        split = "train"
        data = {s: _read(s, "train") for s in SCENARIOS}
        if any(v is None for v in data.values()):
            raise NeedsHuman(f"train samples missing under {DATA}")  # noqa: F821
    rows, dropped = [], 0
    for scenario in SCENARIOS:
        for i, r in enumerate(data[scenario]):
            words = str(r.get("target") or "").strip().split(".")[0].split()
            lab = words[0].strip(",:;") if words else ""
            if lab not in ("Yes", "No"):
                dropped += 1
                continue
            # (dialogue_id, turn) repeats within a file (several responses per context): the file row index keeps ids unique
            rows.append({**r, "label": lab, "scenario": scenario, "split": split,
                         "id": f"{scenario}:{split}:{r.get('dialogue_id')}:{r.get('turn')}:{i}"})
    cfg.setdefault("items", {})["dropped_malformed_target"] = dropped
    return rows


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    from collections import Counter
    cfg = {"items": {"use_public_train_sample": True}}
    rows = load_items(cfg)
    print(len(rows), "rows;", Counter((r["scenario"], r["label"]) for r in rows), "; dropped", cfg["items"]["dropped_malformed_target"])
    print("ids unique:", len({r["id"] for r in rows}) == len(rows), "| sample:", {k: str(v)[:60] for k, v in rows[0].items()})
