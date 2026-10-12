"""Aggregate data/census_raw.jsonl -> data/census_v0.csv + summary.

Dedupes works across model IDs, joins model statuses from target_models.json.
Safe to re-run any time; later duplicate lines for a work just re-set identical fields.
"""
import json, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main():
    tm = json.loads((ROOT / "target_models.json").read_text(encoding="utf-8"))
    status_of = {m["id"]: m["status"] for m in tm["models"]}

    papers = {}
    with open(DATA / "census_raw.jsonl", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            wid = r["openalex_id"]
            e = papers.setdefault(wid, {**r, "matched_models": set()})
            e["matched_models"].add(r["matched_model"])

    rows = sorted(papers.values(), key=lambda r: -(r["citations"] or 0))
    csv_path = DATA / "census_v0.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["matched_models", "statuses", "citations", "year", "date", "type",
                    "field", "topic", "language", "is_oa", "venue", "title", "doi",
                    "oa_url", "openalex_id"])
        for r in rows:
            statuses = "|".join(sorted({status_of.get(m, "?") for m in r["matched_models"]}))
            w.writerow(["|".join(sorted(r["matched_models"])), statuses, r["citations"],
                        r["year"], r["date"], r["type"], r["field"], r["topic"],
                        r["language"], r["is_oa"], r["venue"], r["title"], r["doi"],
                        r["oa_url"], r["openalex_id"]])

    def touching(status):
        return sum(1 for r in rows
                   if any(status_of.get(m) == status for m in r["matched_models"]))

    by_year = {}
    for r in rows:
        by_year[r["year"]] = by_year.get(r["year"], 0) + 1

    summary = {
        "unique_works": len(rows),
        "touching_dead": touching("dead"),
        "touching_dying": touching("dying"),
        "touching_verify": touching("verify"),
        "by_year": {str(k): v for k, v in sorted(by_year.items(), key=lambda x: str(x[0]))},
    }
    (DATA / "census_v0_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"unique works: {len(rows)}")
    print(f"touching dead: {summary['touching_dead']} | dying: {summary['touching_dying']}"
          f" | verify: {summary['touching_verify']}")
    print(f"csv: {csv_path}")


if __name__ == "__main__":
    main()
