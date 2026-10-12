"""Collect the open-access PDFs of the main coding sample into one folder for the coders.

python scripts/fetch_sample_pdfs.py [--limit N] [--out coding/pdfs_main]

For each of the 500 papers in data/coding/assignment_main_k4.csv the script asks OpenAlex for the work's locations,
takes the first direct PDF link (best open-access location, then any location with a pdf_url, then an arXiv PDF built
from the DOI, then the census oa_url when it already points at a PDF) and downloads it politely: one request at a
time, at least 3 s between arXiv requests and 1 s elsewhere, a descriptive User-Agent, no retries against a refusal.
Files are named <number>_<Wid>.pdf, the number being the sample number the coders see in their workbooks. A file is
kept only if it really is a PDF. The run is resumable (existing files are skipped) and writes manifest.csv (number,
Wid, title, source URL, licence, status, bytes, sha256) plus missing.csv with the DOI and landing page of every paper
that could not be fetched, so that coders can open those through the library. Papers that are not open access are
listed, never fetched from anywhere else. The folder is ignored by git and is not part of the deposit.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
UA = "halflife-census/0.1 (academic reproducibility study; mailto:erzyh34@gmail.com)"
DELAY = {"arxiv.org": 3.0, "export.arxiv.org": 3.0}
DEFAULT_DELAY = 1.0
_last = {}


def env_key():
    p = HALF.parent / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENALEX_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def polite(url):
    host = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    wait = DELAY.get(host, DEFAULT_DELAY)
    t = _last.get(host, 0)
    now = time.time()
    if now - t < wait:
        time.sleep(wait - (now - t))
    _last[host] = time.time()


def get(url, timeout=60, accept="*/*", max_seconds=150, max_bytes=80_000_000):
    """Read with a per-operation socket timeout and an overall deadline, so a trickling host cannot stall the run."""
    polite(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        chunks, total, t0 = [], 0, time.time()
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError("download larger than the size cap")
            if time.time() - t0 > max_seconds:
                raise TimeoutError("download slower than the deadline")
        return b"".join(chunks), r.headers.get("Content-Type", ""), r.geturl()


def openalex(wid, key):
    q = f"https://api.openalex.org/works/{wid}?select=id,doi,title,type,open_access,best_oa_location,locations"
    q += f"&api_key={key}" if key else "&mailto=erzyh34@gmail.com"
    body, _, _ = get(q, accept="application/json")
    return json.loads(body.decode("utf-8"))


def candidates(rec, census_row):
    out = []
    def add(url, lic, why):
        if url and url not in [u for u, _, _ in out]:
            out.append((url, lic or "", why))
    best = rec.get("best_oa_location") or {}
    add(best.get("pdf_url"), best.get("license"), "openalex best_oa_location")
    for loc in rec.get("locations") or []:
        if loc.get("pdf_url"):
            add(loc["pdf_url"], loc.get("license"), "openalex location")
    doi = rec.get("doi") or census_row.get("doi") or ""
    doi = doi if isinstance(doi, str) else ""          # the census leaves the DOI empty (NaN) for some records
    m = re.search(r"10\.48550/arxiv\.(.+)$", doi, re.I)
    if m:
        add(f"https://arxiv.org/pdf/{m.group(1)}", "arxiv", "arXiv id from DOI")
    for loc in rec.get("locations") or []:
        lp = loc.get("landing_page_url") or ""
        m2 = re.search(r"arxiv\.org/abs/([0-9.]+(?:v\d+)?)", lp)
        if m2:
            add(f"https://arxiv.org/pdf/{m2.group(1)}", loc.get("license") or "arxiv", "arXiv landing page")
    oa = census_row.get("oa_url") or ""
    if isinstance(oa, str) and (oa.lower().endswith(".pdf") or "arxiv.org/pdf/" in oa):
        add(oa, "", "census oa_url")
    # PubMed Central and Europe PMC answer scripted PDF requests with an HTML page or 403; those papers stay on the
    # missing list with their landing page and are opened by hand.
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", default="coding/pdfs_main")
    a = ap.parse_args()
    out = HALF / a.out
    out.mkdir(parents=True, exist_ok=True)
    key = env_key()
    sample = pd.read_csv(HALF / "data" / "coding" / "assignment_main_k4.csv", encoding="utf-8-sig")
    sample["wid"] = sample.openalex_id.str.rsplit("/", n=1).str[-1]
    census = pd.read_csv(HALF / "data" / "census_v2.csv", encoding="utf-8-sig", usecols=["openalex_id", "title", "doi", "oa_url", "is_oa", "type"])
    census["wid"] = census.openalex_id.str.rsplit("/", n=1).str[-1]
    census = census.drop_duplicates("wid").set_index("wid")
    manifest_p = out / "manifest.csv"
    done = {}
    if manifest_p.exists():
        for r in csv.DictReader(open(manifest_p, encoding="utf-8-sig")):
            done[r["wid"]] = r
    rows = list(done.values())
    todo = [r for r in sample.itertuples() if r.wid not in done or done[r.wid]["status"] != "ok"]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(sample)} papers, {sum(1 for d in done.values() if d['status'] == 'ok')} already fetched, {len(todo)} to try", flush=True)
    t0 = time.time()
    for i, r in enumerate(todo, 1):
        num, wid = int(r.num), r.wid
        crow = census.loc[wid].to_dict() if wid in census.index else {}
        title = str(crow.get("title") or "")
        fn = out / f"{num:03d}_{wid}.pdf"
        rec_row = {"num": num, "wid": wid, "title": title[:160], "doi": crow.get("doi") or "", "landing": "", "source_url": "", "licence": "",
                   "status": "", "bytes": 0, "sha256": "", "note": ""}
        try:
            rec = openalex(wid, key)
        except Exception as e:
            rec = {}
            rec_row["note"] = f"openalex: {type(e).__name__}"
        rec_row["landing"] = ((rec.get("best_oa_location") or {}).get("landing_page_url") or rec.get("doi") or crow.get("oa_url") or "")
        if rec and not (rec.get("open_access") or {}).get("is_oa", crow.get("is_oa", True)):
            rec_row["status"] = "not_oa"
            rec_row["note"] = "not open access; open through the library"
        else:
            cands = candidates(rec, crow)
            if not cands:
                rec_row["status"] = "no_pdf_url"
                rec_row["note"] = "open access but no direct PDF link listed"
            for url, lic, why in cands:
                try:
                    body, ctype, final = get(url, accept="application/pdf,*/*;q=0.8")
                except urllib.error.HTTPError as e:
                    rec_row["note"] = f"HTTP {e.code} at {urllib.parse.urlparse(url).netloc}"
                    continue
                except Exception as e:
                    rec_row["note"] = f"{type(e).__name__} at {urllib.parse.urlparse(url).netloc}"
                    continue
                if not body.startswith(b"%PDF"):
                    rec_row["note"] = f"not a PDF ({ctype.split(';')[0] or 'unknown type'}) at {urllib.parse.urlparse(final).netloc}"
                    continue
                fn.write_bytes(body)
                rec_row.update(source_url=url, licence=lic, status="ok", bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), note=why)
                break
            if rec_row["status"] == "":
                rec_row["status"] = "failed"
        done[wid] = rec_row
        with open(manifest_p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rec_row.keys()))
            w.writeheader()
            for d in sorted(done.values(), key=lambda d: int(d["num"])):
                w.writerow(d)
        print(f"[{i}/{len(todo)}] {num:03d} {wid} {rec_row['status']:10s} {rec_row['bytes']:>9,} B  {rec_row['note'][:70]}", flush=True)
    ok = [d for d in done.values() if d["status"] == "ok"]
    miss = [d for d in done.values() if d["status"] != "ok"]
    with open(out / "missing.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["num", "wid", "title", "doi", "landing_page", "status", "note"])
        for d in sorted(miss, key=lambda d: int(d["num"])):
            w.writerow([d["num"], d["wid"], d["title"], d["doi"], d["landing"], d["status"], d["note"]])
    total = sum(int(d["bytes"]) for d in ok)
    print(f"done in {time.time()-t0:.0f}s: {len(ok)} PDFs ({total/1e6:.0f} MB), {len(miss)} missing -> {out}", flush=True)
    (out / "README.txt").write_text(
        "HALF-LIFE 본표본 500편 PDF (수기 검증용, 배포 금지)\n\n"
        "파일명 = 워크북의 번호_OpenAlexID.pdf. manifest.csv에 출처 주소와 라이선스, 해시가 있고, missing.csv에는 받지 못한 논문의 DOI와 "
        "랜딩 페이지가 있으니 도서관 구독으로 열어 주세요. 모든 파일은 OpenAlex가 안내한 오픈액세스 위치(arXiv, ACL Anthology, 출판사 OA 페이지)에서 "
        "받은 것이며, 코딩 작업 안에서만 씁니다. 이 폴더는 저장소와 기탁물에 들어가지 않습니다.\n"
        f"\n수집: {time.strftime('%Y-%m-%d %H:%M')}, PDF {len(ok)}편, 미수집 {len(miss)}편.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
