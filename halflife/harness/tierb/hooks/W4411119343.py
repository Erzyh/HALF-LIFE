"""Hook W4411119343 (EMBER, GPT-4-turbo as QA judge, Table 14 Natural-Questions / QA_S accuracy).

load_items -> reads external/data/tierb_items/W4411119343/ember_qa_gpt4.json (Dongryeol/EMBER on the Hub,
              1,000 records). Records 0-499 are the Natural Questions subset (394 Correct / 106 Incorrect =
              Table 14), records 500-999 the TriviaQA subset (450 / 50 = Table 15); only the TriviaQA records
              carry a 'wiki' key, so the split is positional.
              Kept: the 394 Natural-Questions records with judge_gpt4 == True.
              Each row reproduces exactly what run_qaeval.py of the code release puts into the prompt:
                question  = d['question'][0].upper() + d['question'][1:]   (first letter upper-cased)
                reference = d['golden_answer'][0]                           (only the FIRST reference string)
                output    = d['answer_gpt4_str']                            (reader output + strengthener = QA_S)
                gold      = 'Yes'                                           (human verdict judge_gpt4 == True)
Neither of the two steps above is expressible in the config mini-language, which is the only reason for this hook.
No render / parse / score: the config's Table 12 prompt, the Yes/No label parse and accuracy are runner facilities.
"""
from pathlib import Path
import json

DATA = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4411119343"
FILE = DATA / "ember_qa_gpt4.json"
URL = "https://huggingface.co/datasets/Dongryeol/EMBER/resolve/main/ember_qa_gpt4.json"
N_NQ = 500  # records 0..499 are the Natural Questions subset


def load_items(cfg):
    if not FILE.exists():
        raise NeedsHuman(f"download {URL} to {FILE} before --prepare")  # noqa: F821 (injected by the runner)
    records = json.loads(FILE.read_text(encoding="utf-8"))
    if len(records) != 1000:
        raise NeedsHuman(f"expected 1000 EMBER-QA records, found {len(records)}")  # noqa: F821
    rows = []
    for i, d in enumerate(records[:N_NQ]):
        if not d.get("judge_gpt4"):
            continue
        q = d["question"]
        rows.append({
            "id": f"nq-{i:03d}",
            "question": q[0].upper() + q[1:],
            "reference": d["golden_answer"][0],
            "output": d["answer_gpt4_str"],
            "gold": "Yes",
        })
    if len(rows) != 394:
        raise NeedsHuman(f"expected the 394 Correct Natural-Questions samples of Table 14, built {len(rows)}")  # noqa: F821
    return rows


if __name__ == "__main__":
    class NeedsHuman(Exception):
        pass
    rows = load_items({})
    print(len(rows), "items")
    print(json.dumps(rows[0], ensure_ascii=False, indent=1))
