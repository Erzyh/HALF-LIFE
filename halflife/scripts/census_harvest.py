"""HALF-LIFE census v0 harvester (resumable, budget-aware).

Cursor-paginates every target model ID on OpenAlex fulltext search.
- Appends each work incrementally to data/census_raw.jsonl (crash-safe).
- Tracks completed IDs in data/census_checkpoint.json; re-running skips them.
- Detects OpenAlex daily-budget exhaustion (resets midnight UTC) and exits
  cleanly with the checkpoint saved; just re-run after the reset to resume.
- Exponential backoff on transient 429/5xx/network errors.

After harvest completes, run census_build.py to aggregate into census_v0.csv.
stdlib only. No user email sent.
"""
import argparse, json, os, sys, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "halflife-census/0.4 (academic research harvester)"}
BASE = "https://api.openalex.org/works"
SLEEP = 1.0
RETRIES = 6
SELECT = ("id,doi,title,publication_year,publication_date,cited_by_count,type,"
          "primary_location,open_access,primary_topic,language")
MAX_PAGES_PER_ID = 80

DATA = ROOT / "data"
RAW = DATA / "census_raw.jsonl"
CKPT = DATA / "census_checkpoint.json"

BUDGET_EXHAUSTED = "BUDGET"


def api_key():
    """OPENALEX_API_KEY env var, or halflife/.openalex_key file (gitignored)."""
    k = os.environ.get("OPENALEX_API_KEY", "").strip()
    if not k:
        f = ROOT / ".openalex_key"
        if f.exists():
            k = f.read_text(encoding="utf-8").strip()
    return k


KEY = api_key()


def get(url):
    """Return parsed JSON, BUDGET_EXHAUSTED on daily-quota exhaustion, or None."""
    for i in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                body = ""
                try:
                    body = e.read().decode("utf-8", "replace")
                except Exception:
                    pass
                retry_after = None
                try:
                    retry_after = json.loads(body).get("retryAfter")
                except Exception:
                    ra = e.headers.get("Retry-After")
                    retry_after = int(ra) if ra and ra.isdigit() else None
                if "Insufficient budget" in body or (retry_after and retry_after > 3600):
                    return BUDGET_EXHAUSTED
                time.sleep(min(retry_after or 15 * (2 ** i), 120) + 1)
                continue
            if e.code >= 500:
                time.sleep(min(10 * (2 ** i), 120))
                continue
            raise
        except Exception:
            time.sleep(min(10 * (2 ** i), 120))
    return None


def load_ckpt():
    if CKPT.exists():
        return json.loads(CKPT.read_text(encoding="utf-8"))
    return {"done_ids": [], "failed_ids": []}


def save_ckpt(ck):
    CKPT.write_text(json.dumps(ck, ensure_ascii=False, indent=2), encoding="utf-8")


def slim(w):
    return {
        "openalex_id": w.get("id"),
        "doi": w.get("doi") or "",
        "title": (w.get("title") or "").strip(),
        "year": w.get("publication_year"),
        "date": w.get("publication_date"),
        "citations": w.get("cited_by_count", 0),
        "venue": (((w.get("primary_location") or {}).get("source") or {})
                  .get("display_name")) or "",
        "type": w.get("type") or "",
        "is_oa": (w.get("open_access") or {}).get("is_oa"),
        "oa_url": (w.get("open_access") or {}).get("oa_url") or "",
        "topic": ((w.get("primary_topic") or {}).get("display_name")) or "",
        "field": (((w.get("primary_topic") or {}).get("field") or {})
                  .get("display_name")) or "",
        "language": w.get("language") or "",
    }


def main():
    global RAW, CKPT, MAX_PAGES_PER_ID
    ap = argparse.ArgumentParser(description="OpenAlex full-text harvest of model identifiers (defaults: the base census)")
    ap.add_argument("--models", default=str(ROOT / "target_models.json"), help="vocabulary JSON with a 'models' list (id, priority)")
    ap.add_argument("--raw", default=str(RAW), help="output JSONL (appended)")
    ap.add_argument("--ckpt", default=str(CKPT), help="checkpoint JSON")
    ap.add_argument("--max-pages", type=int, default=MAX_PAGES_PER_ID, help="pages of 200 works per identifier")
    a = ap.parse_args()
    RAW, CKPT, MAX_PAGES_PER_ID = Path(a.raw), Path(a.ckpt), a.max_pages
    DATA.mkdir(exist_ok=True)
    tm = json.loads(Path(a.models).read_text(encoding="utf-8"))
    models = sorted(tm["models"], key=lambda m: m["priority"])  # dying IDs first
    ck = load_ckpt()
    done = set(ck["done_ids"])

    with open(RAW, "a", encoding="utf-8") as raw:
        for m in models:
            mid = m["id"]
            if mid in done:
                print(f"[skip] {mid} (checkpointed)", flush=True)
                continue
            q = urllib.parse.quote(f'"{mid}"')
            cursor, n, pages, ok = "*", 0, 0, True
            while cursor and pages < MAX_PAGES_PER_ID:
                url = (f"{BASE}?filter=fulltext.search:{q}&per-page=200"
                       f"&cursor={urllib.parse.quote(cursor)}&select={SELECT}")
                if KEY:
                    url += f"&api_key={urllib.parse.quote(KEY)}"
                d = get(url)
                if d == BUDGET_EXHAUSTED:
                    save_ckpt(ck)
                    print(f"[budget] OpenAlex daily budget exhausted at {mid} "
                          f"page {pages}. Checkpoint saved. Re-run after midnight "
                          f"UTC (09:00 KST) to resume.", flush=True)
                    sys.exit(0)
                if d is None:
                    ok = False
                    ck.setdefault("failed_ids", [])
                    if mid not in ck["failed_ids"]:
                        ck["failed_ids"].append(mid)
                    save_ckpt(ck)
                    print(f"[fail] {mid} at page {pages}; will retry next run",
                          flush=True)
                    break
                res = d.get("results", [])
                for w in res:
                    if not w.get("id"):
                        continue
                    row = slim(w)
                    row["matched_model"] = mid
                    raw.write(json.dumps(row, ensure_ascii=False) + "\n")
                raw.flush()
                n += len(res)
                cursor = (d.get("meta") or {}).get("next_cursor")
                pages += 1
                print(f"[page] {mid}: page {pages}, total {n}", flush=True)
                time.sleep(SLEEP)
                if not res:
                    break
            if ok:
                print(f"[done] {mid}: {n} works", flush=True)
                ck["done_ids"].append(mid)
                if mid in ck.get("failed_ids", []):
                    ck["failed_ids"].remove(mid)
                save_ckpt(ck)

    print(f"\ncompleted IDs: {len(ck['done_ids'])}/{len(models)}"
          f" | pending retry: {ck.get('failed_ids', [])}", flush=True)
    print("next: python census_build.py", flush=True)


if __name__ == "__main__":
    main()
