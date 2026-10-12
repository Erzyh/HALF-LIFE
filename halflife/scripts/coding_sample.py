"""Draw the manual-validation sample for the dependence classification (ANALYSIS_PLAN §5).

Frame: data/census_v2.csv minus papers whose OpenAlex language is set and is not English
(coders read English; the exclusion is reported). Strata: model status (dead / dying /
dead|dying) x domain group (6). Allocation proportional to stratum size with a floor of
8 per non-empty cell; within a cell a systematic draw over rows sorted by year spreads the
sample across years. Three disjoint draws: pilot (30, codebook calibration), main (500),
reserve (60, only used if a main paper turns out to be unusable, decision logged).

Output: data/coding/sample_v1.csv with columns set, stratum, and the census fields.
Seed fixed; re-running reproduces the same draw.
"""
import csv, random, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "census_v2.csv"
OUT = ROOT / "data" / "coding" / "sample_v1.csv"
SEED = 20260905
N_MAIN, N_PILOT, N_RESERVE, FLOOR = 500, 30, 60, 8

GROUP = {
    "Computer Science": "CS",
    "Medicine": "MED", "Health Professions": "MED", "Dentistry": "MED", "Nursing": "MED",
    "Pharmacology, Toxicology and Pharmaceutics": "MED", "Immunology and Microbiology": "MED",
    "Veterinary": "MED",
    "Social Sciences": "SOC", "Psychology": "SOC", "Business, Management and Accounting": "SOC",
    "Economics, Econometrics and Finance": "SOC", "Arts and Humanities": "SOC",
    "Engineering": "ENG", "Decision Sciences": "ENG", "Materials Science": "ENG",
    "Physics and Astronomy": "ENG", "Mathematics": "ENG", "Chemistry": "ENG", "Energy": "ENG",
    "Chemical Engineering": "ENG", "Earth and Planetary Sciences": "ENG",
    "Environmental Science": "ENG",
    "Biochemistry, Genetics and Molecular Biology": "LIFE", "Neuroscience": "LIFE",
    "Agricultural and Biological Sciences": "LIFE",
    "": "UNK",
}


def allocate(sizes, n, floor):
    """Proportional allocation with a per-cell floor; cells at the floor are never cut."""
    total = sum(sizes.values())
    prop = {k: n * v / total for k, v in sizes.items() if v > 0}
    alloc = {k: min(sizes[k], max(floor, round(p))) for k, p in prop.items()}
    while sum(alloc.values()) > n:
        cand = [k for k in alloc if alloc[k] > floor]
        key = max(cand, key=lambda k: alloc[k] - prop[k])
        alloc[key] -= 1
    while sum(alloc.values()) < n:
        cand = [k for k in alloc if alloc[k] < sizes[k]]
        key = min(cand, key=lambda k: alloc[k] - prop[k])
        alloc[key] += 1
    return {k: v for k, v in alloc.items() if v > 0}


def systematic(rows, k, rng):
    if k <= 0:
        return []
    rows = sorted(rows, key=lambda r: (r["year"], r["_key"]))
    if k >= len(rows):
        return rows
    step = len(rows) / k
    start = rng.random() * step
    return [rows[int(start + i * step)] for i in range(k)]


def main():
    rng = random.Random(SEED)
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    n_all = len(rows)
    frame = [r for r in rows if r["language"] in ("en", "")]
    for r in frame:
        r["_key"] = rng.random()
        r["group"] = GROUP.get(r["field"], "ENG" if r["field"] else "UNK")
        r["stratum"] = f"{r['statuses']}|{r['group']}"
    by = collections.defaultdict(list)
    for r in frame:
        by[r["stratum"]].append(r)
    sizes = {k: len(v) for k, v in by.items()}

    taken = set()
    out = []
    for name, n in (("pilot", N_PILOT), ("main", N_MAIN), ("reserve", N_RESERVE)):
        alloc = allocate(sizes, n, FLOOR if name == "main" else 1)
        for stratum, k in alloc.items():
            pool = [r for r in by[stratum] if r["openalex_id"] not in taken]
            for r in systematic(pool, k, rng):
                taken.add(r["openalex_id"])
                out.append({"set": name, **r})
    order = {"pilot": 0, "main": 1, "reserve": 2}
    out.sort(key=lambda r: (order[r["set"]], r["stratum"], r["year"], r["_key"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["set", "stratum", "group", "openalex_id", "doi", "title", "year", "date", "type",
              "field", "topic", "venue", "is_oa", "oa_url", "matched_models", "statuses",
              "citations", "language"]
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)

    print(f"census rows {n_all}; frame after language filter {len(frame)} "
          f"(excluded {n_all - len(frame)} non-English)")
    for name in ("pilot", "main", "reserve"):
        sub = [r for r in out if r["set"] == name]
        print(f"{name}: {len(sub)}")
        if name == "main":
            c = collections.Counter(r["stratum"] for r in sub)
            for k in sorted(c):
                print(f"   {k:22s} {c[k]:4d}  (frame {sizes[k]})")
            print("   years:", sorted(collections.Counter(r["year"] for r in sub).items()))
            print("   oa:", collections.Counter(r["is_oa"] for r in sub))
    print("->", OUT)


if __name__ == "__main__":
    main()
