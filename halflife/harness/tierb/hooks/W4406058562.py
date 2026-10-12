"""Hook W4406058562 (UK-Abs legal judgement summarization, gpt4-summ, Table 4 RL-F1).

load_items -> reads the Zenodo dataset.zip (97.8 MB, cached under external/data/tierb_items/W4406058562/) and
              yields one row per UK-Abs test judgement: 'judgement' (full text), 'summary' (reference press
              summary, the gold), 'YY' = word count of the reference summary (Sec. 4.4 target-length rule with
              the whole judgement as a single chunk). The runner renders '{judgment} Summarize the document in
              {YY} words' from these fields and scores ROUGE-L itself.
"""
import shutil, urllib.request, zipfile
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W4406058562" / "dataset.zip"
PREFIX = "dataset/UK-Abs/test-data/"


def load_items(cfg):
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(cfg["items"]["file_url"], headers=UA)
        part = CACHE.with_suffix(".zip.part")
        with urllib.request.urlopen(req, timeout=900) as r, open(part, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        part.replace(CACHE)
    z = zipfile.ZipFile(CACHE)
    names = set(z.namelist())
    rows = []
    for name in sorted(names):
        if name.startswith(PREFIX + "judgement/") and name.endswith(".txt"):
            fid = name.rsplit("/", 1)[1][:-4]
            ref = PREFIX + "summary/full/" + fid + ".txt"
            if ref not in names:
                continue
            judgement = z.read(name).decode("utf-8", "replace").strip()
            summary = z.read(ref).decode("utf-8", "replace").strip()
            rows.append({"file": fid, "judgement": judgement, "summary": summary, "YY": str(len(summary.split()))})
    return rows


if __name__ == "__main__":
    if CACHE.exists():
        rows = load_items({"items": {"file_url": ""}})
        assert len(rows) == 100 and all(r["YY"].isdigit() and r["judgement"] for r in rows), len(rows)
        print("W4406058562 hook self-test ok:", len(rows), "rows; mean YY",
              sum(int(r["YY"]) for r in rows) / len(rows))
    else:
        print("W4406058562: cache missing, run --prepare to download")
