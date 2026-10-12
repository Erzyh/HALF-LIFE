"""HALF-LIFE W1 mini-census harvester.

Phase A: every target model ID -> OpenAlex fulltext hit count (census preview).
Phase B: priority 1&2 (dying) IDs -> top-200 papers by citations -> p0_candidates_raw.csv

stdlib only. Polite: 1 req/s baseline, honors Retry-After on 429. No user email sent.
"""
import json, csv, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "halflife-census/0.1 (academic research harvester)"}
BASE = "https://api.openalex.org/works"
SLEEP = 1.0


def get(url, retries=6):
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = e.headers.get("Retry-After")
                time.sleep(min(int(wait) if wait and wait.isdigit() else 10, 30) + 1)
                continue
            if e.code >= 500:
                time.sleep(5)
                continue
            raise
        except Exception:
            time.sleep(5)
    raise RuntimeError(f"failed after retries: {url}")


def works_url(model_id, per_page, sort=None):
    q = urllib.parse.quote(f'"{model_id}"')
    url = f"{BASE}?filter=fulltext.search:{q}&per-page={per_page}"
    if sort:
        url += f"&sort={sort}"
    return url


def main():
    tm = json.loads((ROOT / "target_models.json").read_text(encoding="utf-8"))
    models = tm["models"]
    outdir = ROOT / "data"
    outdir.mkdir(exist_ok=True)

    # Phase A: counts for every ID
    summary = {}
    for m in models:
        mid = m["id"]
        d = get(works_url(mid, 1))
        c = d.get("meta", {}).get("count", 0)
        summary[mid] = {"count": c, "status": m["status"], "priority": m["priority"],
                        "shutdown": m.get("shutdown"), "vendor": m["vendor"]}
        print(f"[count] {mid}: {c}")
        time.sleep(SLEEP)

    # Phase B: harvest top-200 by citations for priority 1 & 2
    papers = {}
    for m in [x for x in models if x["priority"] in (1, 2)]:
        mid = m["id"]
        d = get(works_url(mid, 200, sort="cited_by_count:desc"))
        res = d.get("results", [])
        print(f"[harvest] {mid}: {len(res)} fetched")
        for w in res:
            wid = w.get("id")
            if not wid:
                continue
            e = papers.setdefault(wid, {
                "matched_models": set(), "openalex_id": wid,
                "doi": w.get("doi") or "",
                "title": (w.get("title") or "").strip(),
                "year": w.get("publication_year"),
                "date": w.get("publication_date"),
                "citations": w.get("cited_by_count", 0),
                "venue": (((w.get("primary_location") or {}).get("source") or {}).get("display_name")) or "",
                "type": w.get("type") or "",
                "is_oa": (w.get("open_access") or {}).get("is_oa"),
                "oa_url": (w.get("open_access") or {}).get("oa_url") or "",
            })
            e["matched_models"].add(mid)
        time.sleep(SLEEP)

    rows = sorted(papers.values(), key=lambda r: -(r["citations"] or 0))
    csv_path = outdir / "p0_candidates_raw.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        wtr = csv.writer(f)
        wtr.writerow(["matched_models", "citations", "year", "date", "type", "is_oa",
                      "venue", "title", "doi", "oa_url", "openalex_id"])
        for r in rows:
            wtr.writerow(["|".join(sorted(r["matched_models"])), r["citations"], r["year"],
                          r["date"], r["type"], r["is_oa"], r["venue"], r["title"],
                          r["doi"], r["oa_url"], r["openalex_id"]])

    (outdir / "harvest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    dead = sum(v["count"] for v in summary.values() if v["status"] == "dead")
    dying = sum(v["count"] for v in summary.values() if v["status"] == "dying")
    ver = sum(v["count"] for v in summary.values() if v["status"] == "verify")
    print(f"\nunique P0 candidate papers (top-200 per dying ID, deduped): {len(rows)}")
    print(f"census preview, hits incl. duplicates - dead IDs: {dead} | dying IDs: {dying} | verify IDs: {ver}")
    print(f"csv: {csv_path}")


if __name__ == "__main__":
    main()
