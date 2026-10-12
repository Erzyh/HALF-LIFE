"""Verify that each fetched full text in data/coding/evidence_v1.jsonl is the paper it claims to be.

About 15% of OA URLs in the census resolve to a landing page or a different document (seen in
the Tier B screen). For every record with a successful fetch, re-download the stored URL, take
the first 4,000 characters, and store title_match = share of the census title's long words found
there. Rows below 0.5 are flagged in the coder workbooks so nobody codes from the wrong paper.

Resumable (records already carrying title_match are skipped). Usage:
  python scripts/coding_evidence_check.py [--set pilot|main|reserve|all]
"""
import argparse, csv, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from coding_evidence import OUT, SAMPLE, fetch, html_text, pdf_text  # noqa: E402

STOP = {"the", "a", "an", "of", "for", "and", "in", "on", "to", "with", "from", "by", "via", "at", "is", "are", "using"}


def title_tokens(t):
    return [w for w in re.sub(r"[^a-z0-9 ]", " ", t.lower()).split() if len(w) > 3 and w not in STOP]


def match(title, head):
    t = title_tokens(title)
    if not t:
        return None
    head = head.lower()
    return round(sum(1 for w in t if w in head) / len(t), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="all")
    a = ap.parse_args()
    titles = {r["openalex_id"]: (r["title"], r["set"]) for r in csv.DictReader(open(SAMPLE, encoding="utf-8-sig"))}
    recs = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    n_try = n_bad = 0
    for i, rec in enumerate(recs, 1):
        title, set_ = titles.get(rec["openalex_id"], ("", ""))
        if a.set != "all" and set_ != a.set:
            continue
        if "title_match" in rec or rec["fetch"] not in ("pdf", "html", "pdf_arxiv_fallback"):
            continue
        n_try += 1
        url = rec["url"]
        if "arxiv.org/abs/" in url:
            url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
        try:
            ct, data = fetch(url)
            if "pdf" in ct or data[:5] == b"%PDF-":
                text, _ = pdf_text(data)
            else:
                text = html_text(data)
            rec["title_match"] = match(title, text[:4000])
        except Exception as e:
            rec["title_match"] = None
            rec["title_match_error"] = type(e).__name__
        if rec["title_match"] is not None and rec["title_match"] < 0.5:
            n_bad += 1
            print(f"  MISMATCH {rec['title_match']} {rec['openalex_id'].rsplit('/', 1)[-1]} {title[:60]}", flush=True)
        if n_try % 25 == 0:
            OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
            print(f"[{n_try}] checked, mismatches so far {n_bad}", flush=True)
        time.sleep(2.0 if "arxiv.org" in url else 1.0)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    print(f"done: checked {n_try}, mismatches {n_bad}", flush=True)


if __name__ == "__main__":
    main()
