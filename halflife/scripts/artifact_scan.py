"""W1 artifact scan: which P0 candidates ship code/data artifacts?

Takes the dying-stratum papers from census_v0.csv (year >= 2023, OA URL present),
top-N by citations, fetches each OA full text (PDF preferred, HTML fallback),
and extracts repository links (GitHub, OSF, Zenodo, Hugging Face).

Resumable: appends to data/artifact_scan.csv and skips already-scanned works.
Polite: ~2.5 s between fetches (arXiv-heavy workload). PDFs parsed in memory,
never saved. Link extraction from PDFs is a lower bound (line breaks split URLs).
"""
import csv, io, re, time, urllib.request, urllib.error
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "artifact_scan.csv"
TOP_N = 500
SLEEP = 2.5
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-artifact-scan/0.1; academic research)"}

PAT = re.compile(
    r"(github\.com/[\w.\-]+/[\w.\-]+"
    r"|osf\.io/[a-z0-9]{4,6}"
    r"|zenodo\.org/(?:records?|record)/\d+"
    r"|huggingface\.co/(?:datasets/)?[\w.\-]+/[\w.\-]+)",
    re.I,
)
STOP_SUFFIX = (".pdf", ".png", ".jpg", ",", ".", ")", "]")


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ct = (r.headers.get("Content-Type") or "").lower()
        data = r.read(30 * 1024 * 1024)
    return ct, data


def pdf_text(data):
    try:
        rd = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in rd.pages[:40])
    except Exception:
        return ""


def clean_link(s):
    s = s.rstrip("".join(STOP_SUFFIX))
    return s


def extract_links(text):
    joined = text.replace("\n", "") + "\n" + text
    return sorted({clean_link(m.group(0)) for m in PAT.finditer(joined)})


def main():
    rows = list(csv.DictReader(open(DATA / "census_v0.csv", encoding="utf-8-sig")))
    cands = [r for r in rows
             if "dying" in r["statuses"]
             and r["year"] in ("2023", "2024", "2025", "2026")
             and r["oa_url"]]
    cands.sort(key=lambda r: -int(r["citations"] or 0))
    cands = cands[:TOP_N]

    done = set()
    new_file = not OUT.exists()
    if not new_file:
        done = {r["openalex_id"] for r in csv.DictReader(open(OUT, encoding="utf-8-sig"))}

    scanned = with_links = 0
    with open(OUT, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["openalex_id", "doi", "year", "citations", "field",
                        "scan_status", "n_links", "links", "title"])
        for i, r in enumerate(cands, 1):
            if r["openalex_id"] in done:
                continue
            url = r["oa_url"]
            if "arxiv.org/abs/" in url:
                url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
            status, links = "error", []
            try:
                ct, data = fetch(url)
                if "pdf" in ct or data[:4] == b"%PDF":
                    text = pdf_text(data)
                    status = "pdf" if text else "pdf_unparsed"
                else:
                    text = data.decode("utf-8", "replace")
                    status = "html"
                links = extract_links(text)
            except Exception as e:
                status = f"error:{type(e).__name__}"
            scanned += 1
            if links:
                with_links += 1
            w.writerow([r["openalex_id"], r["doi"], r["year"], r["citations"],
                        r["field"], status, len(links), "|".join(links), r["title"]])
            f.flush()
            print(f"[{i}/{len(cands)}] {status} links={len(links)} cites={r['citations']}",
                  flush=True)
            time.sleep(SLEEP)

    print(f"\nscanned this run: {scanned}, with >=1 repo link: {with_links}", flush=True)
    print(f"csv: {OUT}", flush=True)


if __name__ == "__main__":
    main()
