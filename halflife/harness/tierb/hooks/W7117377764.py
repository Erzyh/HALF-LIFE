"""Hook for W7117377764 (colonial Virginia land-grant geolocation, o3 M-2 one-shot).

load_items: validation.csv (125 rows) restricted to the paper's 43 verified test grants = the rows whose
            results_row_index carries is_locatable == 1 in results/full_results.csv (43 of the 45 rows with
            has_ground_truth == 1; the two excluded rows are test_entry_17 and test_entry_98). Recomputing
            the M-2 mean over those 43 rows from the released per-grant errors gives 23.39 km = Table 4.
parse:      DMS reply -> [lat, lon] decimal degrees (lon negative for W); decimal-degree fallback.
score:      mean great-circle (haversine) error in km over parsed replies; per-item list for the bootstrap.
"""
import csv, io, math, re, urllib.request

RAW = "https://raw.githubusercontent.com/ryanmio/colonial-virginia-llm-geolocation/main/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read().decode("utf-8", "replace")


def load_items(cfg):
    val = list(csv.DictReader(io.StringIO(_get(RAW + "data/processed/validation.csv"))))
    res = list(csv.DictReader(io.StringIO(_get(RAW + "results/full_results.csv"))))
    locatable = {r["row_index"] for r in res if r.get("is_locatable") == "1"}
    rows = [r for r in val if r.get("results_row_index") and r["results_row_index"] in locatable
            and r.get("has_ground_truth") == "1" and r.get("latitude/longitude")]
    if len(rows) != 43:
        raise RuntimeError(f"expected the 43 verified grants, got {len(rows)}")
    return rows


_DMS = re.compile(r"(\d{1,2})\s*[°º]?\s*(\d{1,2})\s*['′]\s*(\d{1,2}(?:\.\d+)?)\s*[\"″]?\s*N[\s,]*"
                  r"(\d{1,3})\s*[°º]?\s*(\d{1,2})\s*['′]\s*(\d{1,2}(?:\.\d+)?)\s*[\"″]?\s*W", re.I)
_DEC = re.compile(r"(-?\d{2}\.\d{3,})\s*°?\s*N?[\s,]+(-?\d{2,3}\.\d{3,})\s*°?\s*W?", re.I)


def parse(text, cfg):
    if not text:
        return None
    t = text.replace("’", "'").replace("”", '"').replace("″", '"').replace("′", "'")
    m = _DMS.search(t)
    if m:
        d1, m1, s1, d2, m2, s2 = (float(x) for x in m.groups())
        return [d1 + m1 / 60 + s1 / 3600, -(d2 + m2 / 60 + s2 / 3600)]
    m = _DEC.search(t)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if 30 <= lat <= 45 and 70 <= abs(lon) <= 90:
            return [lat, -abs(lon)]
    return None


def haversine_km(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    dphi, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def score(preds, golds, cfg):
    per = []
    for p, g in zip(preds, golds):
        if p is None:
            per.append(float("nan"))
            continue
        glat, glon = (float(x) for x in str(g).split(","))
        per.append(haversine_km((p[0], p[1]), (glat, glon)))
    vals = [x for x in per if x == x]
    return (sum(vals) / len(vals) if vals else float("nan")), per


if __name__ == "__main__":
    tests = ["36°56'03.12\"N 77°23'23.41\"W", "3656'03.12\"N 07723'23.41\"W", "Coordinates: 36 56' 3.1\" N, 77 23' 23.4\" W",
             "36.934201, -77.389837", "I cannot geolocate this grant."]
    for t in tests:
        print(repr(t), "->", parse(t, {}))
    v, per = score([parse(tests[0], {}), parse(tests[3], {}), None], ["36.934201,-77.389837"] * 3, {})
    assert per[0] < 0.05 and per[1] < 0.001 and per[2] != per[2], per
    assert abs(haversine_km((36.934201, -77.389837), (37.1118778, -76.895924)) - 48.09) < 0.2
    print("mean", v, per)
