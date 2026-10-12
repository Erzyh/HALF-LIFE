"""Build a top-up candidate set for under-represented domains from the expanded scan.

Selects parsed, linked, unflagged papers in the dying stratum whose field is one of the
target domains, joins census_v2 to get matched models (so we know which arm can still be
baselined), and fetches abstracts from OpenAlex. Output: data/topup_candidates.jsonl
"""
import csv, json, os, re, time, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UA = {"User-Agent": "halflife-census/0.4 (academic research harvester)"}
TARGET_FIELDS = {
    "Biochemistry, Genetics and Molecular Biology", "Materials Science",
    "Chemistry", "Chemical Engineering", "Pharmacology, Toxicology and Pharmaceutics",
    "Medicine", "Health Professions", "Neuroscience", "Environmental Science",
    "Agricultural and Biological Sciences", "Physics and Astronomy", "Earth and Planetary Sciences",
}
CAP_PER_FIELD = 15
REPORT = re.compile(r"technical report|: a (?:comprehensive )?survey|survey of|survey on|systematic review|scoping review", re.I)
LIVE = ("gpt-4o-2024-05-13", "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4.1-nano",
        "o1-2024-12-17", "o1-pro", "o3-mini", "o4-mini", "o3-2025-04-16", "o3-pro", "gpt-5-")


def api_key():
    k = os.environ.get("OPENALEX_API_KEY", "").strip()
    if not k:
        f = ROOT / ".openalex_key"
        if f.exists():
            k = f.read_text(encoding="utf-8").strip()
    return k


def rebuild(inv):
    if not inv:
        return ""
    pos = [(i, w) for w, idxs in inv.items() for i in idxs]
    return " ".join(w for _, w in sorted(pos))


def main():
    census = {r["openalex_id"]: r for r in csv.DictReader(open(DATA / "census_v2.csv", encoding="utf-8-sig"))}
    scan = list(csv.DictReader(open(DATA / "artifact_scan.csv", encoding="utf-8-sig")))
    already = {json.loads(l)["openalex_id"] for l in open(DATA / "p0_abstracts.jsonl", encoding="utf-8") if l.strip()}

    best = {}
    for r in scan:
        if r["scan_status"] not in ("pdf", "html") or int(r["n_links"] or 0) == 0:
            continue
        if REPORT.search(r["title"]):
            continue
        k = r["openalex_id"]
        if k in already or k in best:
            continue
        c = census.get(k)
        if not c or "dying" not in c["statuses"] or c["field"] not in TARGET_FIELDS:
            continue
        live_arms = [m for m in c["matched_models"].split("|") if any(m.startswith(x) for x in LIVE)]
        if not live_arms:
            continue
        best[k] = {"openalex_id": k, "field": c["field"], "year": c["year"],
                   "citations": int(c["citations"] or 0), "live_models": live_arms,
                   "all_models": c["matched_models"], "links": r["links"], "title": c["title"], "doi": c["doi"]}

    per_field, picked = {}, []
    for r in sorted(best.values(), key=lambda x: -x["citations"]):
        f = r["field"]
        if per_field.get(f, 0) < CAP_PER_FIELD:
            picked.append(r)
            per_field[f] = per_field.get(f, 0) + 1
    print("candidates per field:", per_field, flush=True)

    key = api_key()
    ids = [p["openalex_id"].rsplit("/", 1)[-1] for p in picked]
    abstracts = {}
    for i in range(0, len(ids), 50):
        flt = "openalex_id:" + "|".join(ids[i:i + 50])
        url = (f"https://api.openalex.org/works?filter={urllib.parse.quote(flt)}"
               f"&per-page=50&select=id,abstract_inverted_index")
        if key:
            url += f"&api_key={urllib.parse.quote(key)}"
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        for w in d.get("results", []):
            abstracts[w["id"]] = rebuild(w.get("abstract_inverted_index"))
        time.sleep(1.0)

    with open(DATA / "topup_candidates.jsonl", "w", encoding="utf-8") as f:
        for p in picked:
            p["abstract"] = abstracts.get(p["openalex_id"], "")
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"wrote {len(picked)} candidates ({sum(1 for p in picked if p['abstract'])} with abstracts)", flush=True)


if __name__ == "__main__":
    main()
