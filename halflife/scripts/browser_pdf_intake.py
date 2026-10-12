"""Helpers for the papers the collector could not fetch: build a browser queue, and file the PDFs that the built-in
browser saved to the Downloads folder.

python scripts/browser_pdf_intake.py queue                  # write coding/pdfs_main/browser_queue.csv (num, wid, title, doi, url)
python scripts/browser_pdf_intake.py intake-batch           # file every recent PDF in Downloads that matches a queued paper
python scripts/browser_pdf_intake.py intake <num> <wid> <url>   # file the newest downloaded PDF as this paper

`queue` re-asks OpenAlex for each paper on the missing list and records the first direct PDF link (the collector's
candidate order) or, failing that, the landing page. `intake-batch` reads the first page of every PDF written to
Downloads in the last hour, matches it to a queued paper by DOI or by title words, moves it to
coding/pdfs_main/<num>_<wid>.pdf and records size, hash, source and the note "built-in browser download" in
manifest.csv; unmatched files stay in Downloads and are listed. Nothing here is committed or deposited.
"""
import csv
import hashlib
import re
import shutil
import sys
import time
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "scripts"))
import fetch_sample_pdfs as F  # noqa: E402

OUT = HALF / "coding" / "pdfs_main"
QUEUE = OUT / "browser_queue.csv"
DOWNLOADS = Path.home() / "Downloads"


def load_manifest():
    return list(csv.DictReader(open(OUT / "manifest.csv", encoding="utf-8-sig")))


def save_manifest(rows):
    with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda d: int(d["num"])))
    miss = [d for d in rows if d["status"] != "ok"]
    with open(OUT / "missing.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["num", "wid", "title", "doi", "landing_page", "status", "note"])
        for d in sorted(miss, key=lambda d: int(d["num"])):
            w.writerow([d["num"], d["wid"], d["title"], d["doi"], d["landing"], d["status"], d["note"]])


def queue():
    import pandas as pd
    key = F.env_key()
    census = pd.read_csv(HALF / "data" / "census_v2.csv", encoding="utf-8-sig", usecols=["openalex_id", "doi", "oa_url", "is_oa", "title"])
    census["wid"] = census.openalex_id.str.rsplit("/", n=1).str[-1]
    census = census.drop_duplicates("wid").set_index("wid")
    rows = load_manifest()
    out = []
    for d in sorted(rows, key=lambda d: int(d["num"])):
        if d["status"] == "ok":
            continue
        crow = census.loc[d["wid"]].to_dict() if d["wid"] in census.index else {}
        try:
            rec = F.openalex(d["wid"], key)
        except Exception:
            rec = {}
        cands = F.candidates(rec, crow)
        url = cands[0][0] if cands else (d["landing"] or crow.get("oa_url") or d["doi"] or "")
        title = d["title"] or str(crow.get("title") or "")
        out.append([int(d["num"]), d["wid"], title, d["doi"] or (rec.get("doi") or ""), url, d["status"], "direct pdf" if cands else "landing page"])
    with open(QUEUE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["num", "wid", "title", "doi", "url", "status", "kind"])
        w.writerows(out)
    for r in out:
        print(f"{r[0]:03d}\t{r[1]}\t{r[6]}\t{r[4]}")
    print(f"{len(out)} papers queued -> {QUEUE}")


def first_page_text(p):
    try:
        from pypdf import PdfReader
        rd = PdfReader(str(p))
        txt = ""
        for pg in rd.pages[:2]:
            txt += (pg.extract_text() or "") + "\n"
        return txt
    except Exception:
        return ""


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower())


def recent_pdfs(max_age_s=3600):
    out = []
    for p in DOWNLOADS.iterdir():
        if not p.is_file() or time.time() - p.stat().st_mtime > max_age_s:
            continue
        try:
            with open(p, "rb") as f:
                if f.read(5) != b"%PDF-":
                    continue
        except OSError:
            continue
        out.append(p)
    return sorted(out, key=lambda p: p.stat().st_mtime)


def file_pdf(p, num, wid, url, rows):
    dst = OUT / f"{int(num):03d}_{wid}.pdf"
    body = p.read_bytes()
    shutil.move(str(p), str(dst))
    for d in rows:
        if d["wid"] == wid:
            d.update(status="ok", source_url=url, bytes=str(len(body)), sha256=hashlib.sha256(body).hexdigest(), note="built-in browser download")
    print(f"filed {dst.name} ({len(body):,} bytes) from {p.name}")


def intake_batch():
    q = [r for r in csv.DictReader(open(QUEUE, encoding="utf-8-sig"))]
    rows = load_manifest()
    done_wids = {d["wid"] for d in rows if d["status"] == "ok"}
    pending = [r for r in q if r["wid"] not in done_wids]
    filed, unmatched = 0, []
    for p in recent_pdfs():
        text = norm(first_page_text(p))
        best, best_score = None, 0
        for r in pending:
            score = 0
            doi = (r["doi"] or "").replace("https://doi.org/", "").lower()
            if doi and doi in text.replace(" ", "").replace("/", "").replace(".", "") + text:
                score = 100
            words = [w for w in norm(r["title"]).split() if len(w) > 3]
            if words:
                hit = sum(1 for w in words if w in text)
                score = max(score, int(100 * hit / len(words)))
            if score > best_score:
                best, best_score = r, score
        if best and best_score >= 60:
            file_pdf(p, best["num"], best["wid"], best["url"], rows)
            pending.remove(best)
            filed += 1
        else:
            unmatched.append((p.name, best_score, best["title"][:40] if best else ""))
    if filed:
        save_manifest(rows)
    print(f"filed {filed}; still pending {len(pending)}; unmatched downloads {len(unmatched)}")
    for u in unmatched:
        print("   unmatched:", u)


def intake(num, wid, url):
    ps = recent_pdfs(600)
    if not ps:
        print("no recent PDF in Downloads"); return 1
    p = ps[-1]
    size0 = p.stat().st_size
    time.sleep(2)
    if p.stat().st_size != size0:
        print("still downloading"); return 2
    rows = load_manifest()
    file_pdf(p, num, wid, url, rows)
    save_manifest(rows)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "queue":
        queue()
    elif len(sys.argv) >= 2 and sys.argv[1] == "intake-batch":
        intake_batch()
    elif len(sys.argv) == 5 and sys.argv[1] == "intake":
        sys.exit(intake(sys.argv[2], sys.argv[3], sys.argv[4]))
    else:
        print(__doc__)
