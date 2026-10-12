"""Fetch abstracts for the P0 triage pool from OpenAlex (batched, ~4 requests).

Reads data/p0_triage_v1.csv, pulls abstract_inverted_index for each work in
batches of 50 via the openalex_id filter, reconstructs plain-text abstracts,
and writes data/p0_abstracts.jsonl. Uses the same API key handling as the
census harvester.
"""
import csv, json, os, time, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UA = {"User-Agent": "halflife-census/0.4 (academic research harvester)"}


def api_key():
    k = os.environ.get("OPENALEX_API_KEY", "").strip()
    if not k:
        f = ROOT / ".openalex_key"
        if f.exists():
            k = f.read_text(encoding="utf-8").strip()
    return k


KEY = api_key()


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def rebuild(inv):
    if not inv:
        return ""
    pos = []
    for word, idxs in inv.items():
        for i in idxs:
            pos.append((i, word))
    return " ".join(w for _, w in sorted(pos))


def main():
    rows = list(csv.DictReader(open(DATA / "p0_triage_v1.csv", encoding="utf-8-sig")))
    ids = [r["openalex_id"].rsplit("/", 1)[-1] for r in rows]
    out = open(DATA / "p0_abstracts.jsonl", "w", encoding="utf-8")
    got = 0
    for i in range(0, len(ids), 50):
        batch = ids[i:i + 50]
        flt = "openalex_id:" + "|".join(batch)
        url = (f"https://api.openalex.org/works?filter={urllib.parse.quote(flt)}"
               f"&per-page=50&select=id,title,abstract_inverted_index")
        if KEY:
            url += f"&api_key={urllib.parse.quote(KEY)}"
        d = get(url)
        for w in d.get("results", []):
            abs_text = rebuild(w.get("abstract_inverted_index"))
            out.write(json.dumps({"openalex_id": w["id"], "title": w.get("title") or "",
                                  "abstract": abs_text}, ensure_ascii=False) + "\n")
            if abs_text:
                got += 1
        time.sleep(1.0)
    out.close()
    print(f"fetched {got}/{len(ids)} abstracts -> p0_abstracts.jsonl", flush=True)


if __name__ == "__main__":
    main()
