"""Hook W7166821175 (device-patent linking, GPT-4-turbo 0-shot direct classification, Table 14 / Table 2 R@Gold).

load_items -> joins the three released files of github.com/myqqhub/Bridge-MedDevKG (downloaded once into
              external/data/tierb_items/W7166821175/):
                gold_standard.parquet      672 rows; the 585 with is_valid == True are the expert-verified pairs
                                           (fda_id, pat_id, ent_names_d, ent_names_p; '|||'-delimited entities)
                baseline_fda_docs.parquet  434 FDA PMA documents (id, text = device name, company)
                baseline_patents.parquet   50,000 patents (id, text = patent title + abstract, company)
              Rows: {pair_id, device_name, device_entities_str, patent_title, patent_entities_str, label}.
              label is "Yes" for every row: R@Gold is the share of gold pairs the model calls linked, so
              accuracy against an all-"Yes" gold column is exactly the paper's recall.
              Both text fields are truncated to 400 characters, as the repository's own prompt filler does
              (code/add_fewshot_examp.py, fill_prompt).
No render / parse / score: the config's placeholders, "json field linked" parse and accuracy metric are
runner facilities.
"""
from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W7166821175"
MAX_CHARS = 400


def _text_map(path):
    import pandas as pd
    df = pd.read_parquet(path, columns=["id", "text"])
    return {str(r["id"]): (r["text"] or "") for _, r in df.iterrows()}


def load_items(cfg):
    import pandas as pd
    missing = [f for f in ("gold_standard.parquet", "baseline_fda_docs.parquet", "baseline_patents.parquet")
               if not (DATA / f).exists()]
    if missing:
        raise NeedsHuman(f"download {missing} from github.com/myqqhub/Bridge-MedDevKG into {DATA}")  # noqa: F821
    gold = pd.read_parquet(DATA / "gold_standard.parquet",
                           columns=["is_valid", "fda_id", "pat_id", "ent_names_d", "ent_names_p"])
    gold = gold[gold["is_valid"] == True]                                          # noqa: E712  -> the 585 pairs
    devices, patents = _text_map(DATA / "baseline_fda_docs.parquet"), _text_map(DATA / "baseline_patents.parquet")
    rows = []
    for _, r in gold.iterrows():
        d, p = str(r["fda_id"]), str(r["pat_id"])
        if d not in devices or p not in patents:
            raise NeedsHuman(f"gold pair {d}/{p} has no released document text")    # noqa: F821
        rows.append({
            "pair_id": f"{d}_{p}",
            "device_name": str(devices[d]).strip()[:MAX_CHARS],
            "device_entities_str": ", ".join(x for x in str(r["ent_names_d"] or "").split("|||") if x),
            "patent_title": str(patents[p]).strip()[:MAX_CHARS],
            "patent_entities_str": ", ".join(x for x in str(r["ent_names_p"] or "").split("|||") if x),
            "label": "Yes",
        })
    if len(rows) != 585:
        raise NeedsHuman(f"expected 585 gold pairs, built {len(rows)}")             # noqa: F821
    return rows


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    print(len(rows), "pairs;", len({r["pair_id"].split("_")[0] for r in rows}), "devices")
    print({k: (v[:90] + "..." if len(v) > 90 else v) for k, v in rows[0].items()})
