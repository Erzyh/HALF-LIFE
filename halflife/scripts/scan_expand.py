"""Expanded artifact scan: fill Tier B domain strata + retry earlier fetch errors.

Target list from census_v2 (dying stratum, 2023+, OA URL present):
  - global top 1,200 by citations
  - per-field quotas so thin domains get enough coverage for Tier B
    (Medicine 500, Social Sciences 400, Psychology 300, BGMB 250, Engineering 250,
     Decision Sciences 250, Business 150, Arts&Humanities 150, Health Professions 150,
     Neuroscience 100, Economics 100, Materials: all)
Plus: rows in artifact_scan.csv with fetch errors are retried via https://doi.org/DOI.

Appends to data/artifact_scan.csv (same schema). IDs already parsed (pdf/html)
are skipped, so this is safely resumable. ~4 s between fetches.
"""
import csv, io, re, time, urllib.request, urllib.error
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "artifact_scan.csv"
SLEEP = 4.0
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-artifact-scan/0.2; academic research)"}

QUOTA = {
    "Medicine": 500, "Social Sciences": 400, "Psychology": 300,
    "Biochemistry, Genetics and Molecular Biology": 250, "Engineering": 250,
    "Decision Sciences": 250, "Business, Management and Accounting": 150,
    "Arts and Humanities": 150, "Health Professions": 150,
    "Neuroscience": 100, "Economics, Econometrics and Finance": 100,
    "Materials Science": 10**9,
}
GLOBAL_TOP = 1200

PAT = re.compile(
    r"(github\.com/[\w.\-]+/[\w.\-]+"
    r"|osf\.io/[a-z0-9]{4,6}"
    r"|zenodo\.org/(?:records?|record)/\d+"
    r"|huggingface\.co/(?:datasets/)?[\w.\-]+/[\w.\-]+)",
    re.I,
)


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


def extract_links(text):
    joined = text.replace("\n", "") + "\n" + text
    return sorted({m.group(0).rstrip(".,)]") for m in PAT.finditer(joined)})


def scan_one(url):
    try:
        ct, data = fetch(url)
        if "pdf" in ct or data[:4] == b"%PDF":
            text = pdf_text(data)
            return ("pdf" if text else "pdf_unparsed"), extract_links(text)
        text = data.decode("utf-8", "replace")
        return "html", extract_links(text)
    except Exception as e:
        return f"error:{type(e).__name__}", []


MARKER = DATA / "scan_complete.marker"


def self_teardown():
    """Kill and remove the HALFLIFE-scan scheduled task so the wrapper loop ends."""
    import subprocess
    try:
        subprocess.Popen(["schtasks", "/Delete", "/F", "/TN", "HALFLIFE-scan"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["schtasks", "/End", "/TN", "HALFLIFE-scan"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def main():
    if MARKER.exists():
        print("expanded scan complete (marker present)", flush=True)
        self_teardown()
        return
    census = list(csv.DictReader(open(DATA / "census_v2.csv", encoding="utf-8-sig")))
    scanned = list(csv.DictReader(open(OUT, encoding="utf-8-sig")))
    parsed_ok = {r["openalex_id"] for r in scanned if r["scan_status"] in ("pdf", "html", "pdf_unparsed")}
    error_rows = [r for r in scanned if r["scan_status"].startswith("error")
                  and r["openalex_id"] not in parsed_ok]

    dying = [r for r in census if "dying" in r["statuses"] and r["oa_url"]
             and r["year"] in ("2023", "2024", "2025", "2026")]
    dying.sort(key=lambda r: -int(r["citations"] or 0))

    targets, seen = [], set(parsed_ok)
    for r in dying[:GLOBAL_TOP]:
        if r["openalex_id"] not in seen:
            targets.append((r, r["oa_url"]))
            seen.add(r["openalex_id"])
    counts = {}
    for r in dying:
        f = r["field"]
        if f in QUOTA and counts.get(f, 0) < QUOTA[f] and r["openalex_id"] not in seen:
            targets.append((r, r["oa_url"]))
            seen.add(r["openalex_id"])
            counts[f] = counts.get(f, 0) + 1

    retries = []
    meta = {r["openalex_id"]: r for r in census}
    for e in error_rows:
        doi = (e["doi"] or "").replace("https://doi.org/", "")
        url = f"https://doi.org/{doi}" if doi else (meta.get(e["openalex_id"], {}) or {}).get("oa_url", "")
        if url:
            retries.append((e, url))

    print(f"targets: {len(targets)} new + {len(retries)} error retries", flush=True)

    with open(OUT, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        total = len(retries) + len(targets)
        i = 0
        for r, url in retries + targets:
            i += 1
            if "arxiv.org/abs/" in url:
                url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
            status, links = scan_one(url)
            w.writerow([r["openalex_id"], r["doi"], r["year"], r["citations"],
                        r["field"], status, len(links), "|".join(links), r["title"]])
            f.flush()
            if i % 25 == 0 or i == total:
                print(f"[{i}/{total}] last={status} links={len(links)}", flush=True)
            time.sleep(SLEEP)

    print("expanded scan complete", flush=True)
    MARKER.write_text("complete\n", encoding="ascii")
    self_teardown()


if __name__ == "__main__":
    main()
