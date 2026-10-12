"""Yearly counts of LLM-related papers from OpenAlex group_by queries (no per-paper harvesting).

For the introduction figure: how many papers mention LLM terms per year, as a share of all works,
2018-2026. Uses OpenAlex's aggregation endpoint (one request per series), so it costs a handful of
API calls. Two flavours are recorded because full-text coverage differs by year:
  ta   title-and-abstract search (consistent coverage across years)
  ft   default search (title + abstract + full text where OpenAlex has it; higher, less uniform)
Denominator: all works with a publication year. Also a per-field split for the last complete year.

Output: data/trend_counts.csv, data/trend_fields.csv, figures/trend_llm_papers.png
  python scripts/trend_counts.py              # query OpenAlex, write the CSVs, draw the figure
  python scripts/trend_counts.py --plot-only  # redraw from data/trend_counts.csv, no requests
"""
import csv, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

API = "https://api.openalex.org/works"
YEARS = list(range(2018, 2027))
UA = {"User-Agent": "halflife-trend/0.1 (academic research)"}
OUT = ROOT / "data" / "trend_counts.csv"

# term sets; OpenAlex search supports quotes and OR
LLM_TERMS = '"large language model" OR "large language models" OR ChatGPT OR "GPT-4" OR "GPT-3.5" OR "GPT-4o" OR "GPT-3"'
SERIES = {
    "llm_ta": {"filter": f"title_and_abstract.search:{LLM_TERMS}"},
    "llm_ft": {"search": LLM_TERMS},
    "chatgpt_ta": {"filter": 'title_and_abstract.search:ChatGPT'},
    "all": {},
}


def get(params, key):
    q = dict(params)
    q["per_page"] = 200                      # per_page also caps the number of groups returned by group_by
    if key:
        q["api_key"] = key
    url = API + "?" + urllib.parse.urlencode(q, quote_via=urllib.parse.quote)
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            time.sleep(2 * (i + 1))
            err = e
    raise err


def by_year(spec, key):
    params = {"group_by": "publication_year"}
    flt = [f"publication_year:{YEARS[0]}-{YEARS[-1]}"]
    if spec.get("filter"):
        flt.append(spec["filter"])
    params["filter"] = ",".join(flt)
    if spec.get("search"):
        params["search"] = spec["search"]
    d = get(params, key)
    return {int(g["key"]): g["count"] for g in d.get("group_by", []) if g["key"].isdigit()}


def by_field(spec, year, key):
    params = {"group_by": "primary_topic.field.id"}
    flt = [f"publication_year:{year}"]
    if spec.get("filter"):
        flt.append(spec["filter"])
    params["filter"] = ",".join(flt)
    if spec.get("search"):
        params["search"] = spec["search"]
    d = get(params, key)
    return [(g["key_display_name"], g["count"]) for g in d.get("group_by", [])]


def fetch():
    from census_harvest import api_key
    key = api_key()
    counts = {}
    for name, spec in SERIES.items():
        counts[name] = by_year(spec, key)
        print(name, {y: counts[name].get(y, 0) for y in YEARS}, flush=True)
        time.sleep(1)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["year"] + list(SERIES) + ["llm_ta_share_pct", "llm_ft_share_pct"])
        for y in YEARS:
            a = counts["all"].get(y, 0) or 1
            w.writerow([y] + [counts[s].get(y, 0) for s in SERIES] + [round(100 * counts["llm_ta"].get(y, 0) / a, 3), round(100 * counts["llm_ft"].get(y, 0) / a, 3)])
    last_full = 2025
    fields = by_field(SERIES["llm_ta"], last_full, key)
    fields_all = dict(by_field(SERIES["all"], last_full, key))
    with open(ROOT / "data" / "trend_fields.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["field", f"llm_ta_{last_full}", f"all_{last_full}", "share_pct"])
        for name, c in fields:
            w.writerow([name, c, fields_all.get(name, ""), round(100 * c / fields_all[name], 2) if fields_all.get(name) else ""])
    print("fields:", fields[:10])
    return counts


def load():
    counts = {s: {} for s in SERIES}
    for row in csv.DictReader(open(OUT, encoding="utf-8-sig")):
        for s in SERIES:
            counts[s][int(row["year"])] = int(row[s])
    return counts


def draw(ax1, ax2, counts):
    """Panel a of Fig. 1: yearly counts (ax1) and the share of all indexed works (ax2); the caller styles the figure."""
    from figstyle import BLUE, BLUE_LIGHT, ORANGE
    ys = YEARS
    ax1.bar([y - 0.2 for y in ys], [counts["llm_ta"].get(y, 0) / 1000 for y in ys], width=0.4, color=BLUE, label="title or abstract")
    ax1.bar([y + 0.2 for y in ys], [counts["llm_ft"].get(y, 0) / 1000 for y in ys], width=0.4, color=BLUE_LIGHT, label="including full text")
    ax1.set_ylabel("papers mentioning LLM terms (thousands)")
    ax1.set_xlabel("publication year (2026 partial)")
    ax1.legend(loc="upper left")
    share = [100 * counts["llm_ta"].get(y, 0) / max(1, counts["all"].get(y, 0)) for y in ys]
    solid = [y for y in ys if y <= 2024]
    ax2.plot(solid, share[:len(solid)], color=ORANGE, marker="o", ms=3.5, lw=1.0)
    ax2.plot(ys[len(solid) - 1:], share[len(solid) - 1:], color=ORANGE, lw=1.0, ls=(0, (3, 2)))
    ax2.plot(ys[len(solid):], share[len(solid):], color=ORANGE, marker="o", ms=3.5, lw=0, mfc="white")
    ax2.set_ylabel("title/abstract mentions,\nshare of all indexed works (%)")
    ax2.set_xlabel("publication year (2025-26 provisional)")
    ax2.set_ylim(bottom=0)
    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)


def plot(counts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from figstyle import apply
    apply()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.4), dpi=200)   # two panels, one scale each (no dual axis)
    draw(ax1, ax2, counts)
    fig.tight_layout()
    (ROOT / "figures").mkdir(exist_ok=True)
    from figutil import savefig
    savefig(fig, ROOT / "figures" / "trend_llm_papers.png", bbox_inches="tight")
    print("->", ROOT / "figures" / "trend_llm_papers.png")


def main():
    counts = load() if "--plot-only" in sys.argv else fetch()
    plot(counts)


if __name__ == "__main__":
    main()
