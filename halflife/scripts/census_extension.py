"""Survival analysis with still-served identifiers included (approved 2026-10-02).

The base census (target_models.json, 55 retired or retiring identifiers) conditions the cohort on naming a model that is
eventually withdrawn. This script adds the papers harvested with data/census_ext_models.json (scripts/census_harvest.py
--models ... --raw data/census_ext_raw.jsonl): papers naming only still-served identifiers enter the Kaplan-Meier
estimate as right-censored observations at the analysis date, and identifiers retired or deprecated since the vocabulary
was fixed (Gemini 2.0, gpt-3.5-turbo-0125, gpt-5-pro, Claude Sonnet 4.5, the 2.5 and 3 previews) contribute events or
announced dates. Alias rules for dateless identifiers are in the vocabulary file (gpt-4o, gpt-3.5-turbo) and follow the
base census's gpt-4-turbo rule: a dated snapshot in the same paper decides; otherwise the snapshot the alias pointed to
on the publication date.

Variants (all censored at the base analysis date, census_survival.TODAY = 2026-10-11, born-dead papers excluded):
  A0 the main census before the refresh of 2026-10-02 (archived data/census_v2_2026-09-28.csv, vocabulary of 2026-09-02)
  A  the main census after the refresh (identifiers retired or given a retirement date after 2 September folded in)
  C  all identifiers, still-served ones censored: the unconditional cohort
  D  C restricted to papers published on or before 2025-09-15 (at least twelve months of potential follow-up)
  E  C projected to the announced retirement dates (censoring at 2026-12-31; still-served identifiers stay censored)
For each variant and vendor: papers named, born dead, papers in the curve, events, share lost, median and quartiles of the
time to first retirement (months), survival at 12 and 24 months.

Writes data/census_ext.csv (one row per harvested paper with a DOI: identifiers, dates, type, field, citations), data/census_survival_unconditional.csv,
data/census_ext_summary.json and figures/census_survival_unconditional.png. No API calls.
"""
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HALF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HALF / "scripts"))
from census_survival import GA, LAG, MONTH, PREVIEW_SHUTDOWN, TODAY, analyse, parse_date, parse_origin  # noqa: E402

ACTIVE = date(2099, 1, 1)                      # sentinel: never retires within the study window -> censored
RELEASE = {}                                   # release dates of the extension identifiers (vocabulary file)
MAIN_IDS = set()                               # identifiers of the main vocabulary (target_models.json)
PRE_RELEASE_TOLERANCE = 90                     # days: a paper dated earlier than this before every named extension identifier's release is a dating error
GPT4O_ALIAS_MOVED = date(2024, 10, 2)          # the gpt-4o alias moved from 2024-05-13 to 2024-08-06
GPT35_1106 = date(2023, 12, 11)                # gpt-3.5-turbo alias -> 1106 (retired 2026-09-28; in the vocabulary since 2026-10-11)
GPT35_0125 = date(2024, 2, 16)                 # gpt-3.5-turbo alias -> 0125
COLS = ["matched_models", "statuses", "citations", "year", "date", "type", "field", "topic", "language", "is_oa", "venue", "title", "doi", "oa_url", "openalex_id"]


def load_vocab():
    base = json.load(open(HALF / "target_models.json", encoding="utf-8"))["models"]
    ext = json.load(open(HALF / "data" / "census_ext_models.json", encoding="utf-8"))["models"]
    shut, vendor, group = {}, {}, {}
    global RELEASE, MAIN_IDS
    MAIN_IDS = {m["id"] for m in base}
    for m in base:
        shut[m["id"]] = parse_date(m["shutdown"]); vendor[m["id"]] = m["vendor"]; group[m["id"]] = "base"
    for m in ext:
        shut[m["id"]] = parse_date(m["shutdown"]) if m.get("shutdown") else ACTIVE
        vendor[m["id"]] = m["vendor"]; group[m["id"]] = m["group"]
        if m.get("release"):
            RELEASE[m["id"]] = parse_date(m["release"])
    return shut, vendor, group, {m["id"] for m in base}, ext


def build_ext_csv():
    """One row per harvested paper with a DOI. Rebuilt from the raw harvest when it is present (the 78 MB JSONL is in the
    Zenodo deposit, not in the repository); otherwise the committed data/census_ext.csv is read back."""
    raw = HALF / "data" / "census_ext_raw.jsonl"
    if not raw.exists():
        return pd.read_csv(HALF / "data" / "census_ext.csv", low_memory=False).reindex(columns=COLS)
    papers = {}
    for line in open(raw, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        e = papers.setdefault(r["openalex_id"], {**r, "matched": set()})
        e["matched"].add(r["matched_model"])
    rows = []
    for e in papers.values():
        rows.append({"matched_models": "|".join(sorted(e["matched"])), "statuses": "", "citations": e.get("citations"), "year": e.get("year"),
                     "date": e.get("date"), "type": e.get("type"), "field": e.get("field"), "topic": e.get("topic"), "language": e.get("language"),
                     "is_oa": e.get("is_oa"), "venue": e.get("venue"), "title": e.get("title"), "doi": e.get("doi"), "oa_url": e.get("oa_url"),
                     "openalex_id": e["openalex_id"]})
    df = pd.DataFrame(rows, columns=COLS)
    df = df[df.doi.astype(str).str.startswith("https://doi.org/")]          # persistent identifier, as in the base census
    slim = df[["openalex_id", "doi", "matched_models", "year", "date", "type", "field", "citations"]]   # what the analysis needs; titles and venues stay in the deposit
    slim.to_csv(HALF / "data" / "census_ext.csv", index=False, encoding="utf-8-sig")
    return df


def rows_from(df, shut, vendor, keep_ids, counters, guard=True):
    """One row per paper with the first shutdown among its resolvable identifiers (base rule for gpt-4-turbo, extension
    rules for gpt-4o and gpt-3.5-turbo). keep_ids limits which identifiers count."""
    out = []
    for r in df.itertuples(index=False):
        tag = f" ({r.src})" if hasattr(r, "src") else ""                     # which harvest the paper came from, for the drop counts
        pub = parse_origin(r.date)[0] if isinstance(r.date, str) else None   # year-only dates at 1 July, as in the main census
        if pub is None:
            try:
                pub = date(int(r.year), 7, 1)
            except Exception:
                counters["alias"]["dropped: no usable publication date" + tag] += 1
                continue
        models = [m for m in str(r.matched_models).split("|") if m and m != "nan" and m in keep_ids]
        rel = [RELEASE[m] for m in models if m in RELEASE]
        # dating-error guard (variants C-E; the main census keeps its own year filter): a paper dated more than 90 days before the
        # release of every identifier it names, when all of them have a release date on file, is an indexing or merge error
        if guard and rel and all((x - pub).days > PRE_RELEASE_TOLERANCE for x in rel) and not any(m not in RELEASE for m in models):
            counters["alias"]["dropped: dated more than 90 days before every named identifier's release" + tag] += 1
            continue
        ev = []
        for m in models:
            if m not in shut:
                counters["unknown"][m] += 1
                continue
            sd = shut[m]
            if m == "gpt-4-turbo":
                if "gpt-4-turbo-2024-04-09" in models:
                    continue
                if pub < GA:
                    sd = PREVIEW_SHUTDOWN
                elif pub < LAG:
                    counters["alias"]["gpt-4-turbo unresolved window (read as live snapshot)"] += 1
            elif m == "gpt-4o":
                if any(x.startswith("gpt-4o-2024-") for x in models):
                    continue
                if pub < GPT4O_ALIAS_MOVED:
                    sd = shut["gpt-4o-2024-05-13"]; counters["alias"]["gpt-4o -> 2024-05-13 (before 2024-10-02)"] += 1
                else:
                    sd = ACTIVE; counters["alias"]["gpt-4o -> still-served snapshot"] += 1
            elif m == "gpt-3.5-turbo":
                if any(x.startswith("gpt-3.5-turbo-") for x in models):
                    continue
                if pub < GPT35_1106:
                    sd = shut["gpt-3.5-turbo-0613"]; counters["alias"]["gpt-3.5-turbo -> 0613"] += 1
                elif pub < GPT35_0125:      # refresh of 2026-10-11: gpt-3.5-turbo-1106 (retired 2026-09-28) is in the main vocabulary
                    sd = shut["gpt-3.5-turbo-1106"]; counters["alias"]["gpt-3.5-turbo -> 1106"] += 1
                else:
                    sd = shut["gpt-3.5-turbo-0125"]; counters["alias"]["gpt-3.5-turbo -> 0125"] += 1
            ev.append((sd, m))
        if not ev:
            continue
        first_sd, first_m = min(ev)
        by_vendor = {}
        for sd, m in ev:
            v = vendor[m]
            if v not in by_vendor or sd < by_vendor[v]:
                by_vendor[v] = sd
        out.append({"openalex_id": r.openalex_id, "pub": pub, "year": int(r.year) if str(r.year) not in ("nan", "None") else pub.year,
                    "first_model": first_m, "first_shutdown": first_sd, "n_models": len(ev), "only_active": first_sd == ACTIVE,
                    "sd_openai": by_vendor.get("openai"), "sd_anthropic": by_vendor.get("anthropic"), "sd_google": by_vendor.get("google")})
    return pd.DataFrame(out)


def surv_at(t, s, m):
    idx = np.where(t <= m)[0]
    return round(float(s[idx[-1]]), 3) if len(idx) else 1.0


def summarise(d, label, today=TODAY):
    recs = []
    for name, col in (("all", "first_shutdown"), ("openai", "sd_openai"), ("anthropic", "sd_anthropic"), ("google", "sd_google")):
        sub = d[d[col].notna()] if col != "first_shutdown" else d
        if not len(sub):
            continue
        st, (t, s) = analyse(sub, col=col, today=today, known=False)   # still-served identifiers have no date: Kaplan-Meier, censored
        censored_active = int((sub[col] == ACTIVE).sum())
        recs.append({"variant": label, "group": name, **st, "censored_still_served": censored_active,
                     "surv_12m": surv_at(t, s, 12), "surv_24m": surv_at(t, s, 24), "surv_36m": surv_at(t, s, 36)})
    return recs, (t, s) if recs else None


def main():
    shut, vendor, group, base_ids, ext_models = load_vocab()
    ext_ids = {m["id"] for m in ext_models}
    omitted_ids = {m["id"] for m in ext_models if m["group"] in ("omitted_retired", "omitted_dying") or (m["group"] == "alias" and m.get("shutdown"))}
    ext = build_ext_csv()
    base = pd.read_csv(HALF / "data" / "census_v2.csv", low_memory=False)
    base["openalex_id"] = base.openalex_id.astype(str)
    # union of matched identifiers for papers in both files
    ext_m = dict(zip(ext.openalex_id, ext.matched_models))
    both = base.openalex_id.isin(ext_m)
    base_u = base.copy()
    base_u.loc[both, "matched_models"] = [f"{a}|{ext_m[i]}" for a, i in zip(base.loc[both, "matched_models"], base.loc[both, "openalex_id"])]
    ext_only = ext[~ext.openalex_id.isin(set(base.openalex_id))]
    allp = pd.concat([base_u[COLS], ext_only[COLS]], ignore_index=True)
    allp["src"] = ["main census"] * len(base_u) + ["extension"] * len(ext_only)
    counters = {"alias": Counter(), "unknown": Counter()}

    variants = []
    # A0: the main census as it stood before the refresh of 2 October (archived file and vocabulary of 2 September)
    old_ids = {m["id"] for m in json.load(open(HALF / "data" / "target_models_2026-09-28.json", encoding="utf-8"))["models"]}
    base_old = pd.read_csv(HALF / "data" / "census_v2_2026-09-28.csv", low_memory=False)
    A0 = rows_from(base_old, shut, vendor, old_ids, {"alias": Counter(), "unknown": Counter()}, guard=False)
    variants.append(("A0 main census under the vocabulary of 2026-09-02 (archived file of 2026-09-28)", A0, TODAY))
    # A: the main census under the completed vocabulary (refreshes of 2 October, 11 October and 12 October 2026)
    A = rows_from(base, shut, vendor, base_ids, {"alias": Counter(), "unknown": Counter()}, guard=False)
    variants.append(("A main census (vocabulary completed 2026-10-12)", A, TODAY))
    C = rows_from(allp, shut, vendor, base_ids | ext_ids, counters)
    variants.append(("C all identifiers, still-served censored (unconditional)", C, TODAY))
    D = C[C.pub <= date(2025, 9, 15)]
    variants.append(("D unconditional, papers published by 2025-09-15", D, TODAY))
    variants.append(("E unconditional, projected to announced retirement dates", C, date(2026, 12, 31)))
    recs, curves = [], {}
    for label, d, today in variants:
        r, curve = summarise(d, label, today)
        recs += r
        curves[label.split(" ")[0]] = (d, today)
    tab = pd.DataFrame(recs)
    tab.to_csv(HALF / "data" / "census_survival_unconditional.csv", index=False, encoding="utf-8-sig")

    # per-identifier counts and overlap
    per_id = Counter()
    for ms in ext.matched_models:
        for m in str(ms).split("|"):
            per_id[m] += 1
    summary = {"ext_papers_with_doi": int(len(ext)), "ext_only_papers": int(len(ext_only)), "ext_papers_also_in_base": int(both.sum()),
               "papers_in_C": int(len(C)), "papers_in_C_from_main_census": int(C.openalex_id.isin(set(base.openalex_id)).sum()),
               "papers_in_C_added_by_extension": int((~C.openalex_id.isin(set(base.openalex_id))).sum()),
               "papers_only_still_served_in_C": int(C.only_active.sum()), "alias_resolution": dict(counters["alias"]),
               "unknown_ids": dict(counters["unknown"]), "per_identifier_papers": dict(sorted(per_id.items(), key=lambda x: -x[1]))}
    json.dump(summary, open(HALF / "data" / "census_ext_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # figure: KM curves of A, B and C (overall)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from figstyle import apply, panel, BLUE, RED, GREY
    apply()
    fig, ax = plt.subplots(figsize=(7.2, 2.7), dpi=200)         # panel c of Extended Data Fig. 5 (scripts/ed_fig5_compose.py)
    styles = {"A0": (GREY, "main census, vocabulary of 2 Sept 2026"), "A": (BLUE, "main census, vocabulary completed 12 Oct 2026"),
              "C": (RED, "all identifiers, still-served ones censored")}
    for k, (d, today) in curves.items():
        if k not in styles:
            continue
        st, (t, s) = analyse(d, today=today, known=False)
        ax.step(t, s, where="post", color=styles[k][0], lw=1.2, label=f"{styles[k][1]} (n={st['n_curve']:,}; median {st['median_months'] if st['median_months'] is not None else 'not reached'})")
    ax.axhline(0.5, color="#999999", lw=0.8, ls="--")
    ax.set_xlabel("months since publication (first retirement among the named identifiers)")
    ax.set_ylabel("share of papers with all named identifiers served")
    ax.set_xlim(0, 42); ax.set_ylim(0, 1.0)
    ax.legend(fontsize=6.3, loc="upper right", frameon=False)
    panel(ax, "c", x=-0.07)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    (HALF / "figures").mkdir(exist_ok=True)
    fig.savefig(HALF / "figures" / "census_survival_unconditional.png", dpi=300)
    with pd.option_context("display.width", 240, "display.max_columns", 30):
        print(tab[["variant", "group", "n_named", "born_dead", "n_curve", "dead_by_today", "pct_dead_today", "median_months", "q25_months", "q75_months", "surv_12m", "surv_24m", "censored_still_served"]].to_string(index=False))
    print(json.dumps({k: v for k, v in summary.items() if k != "per_identifier_papers"}, ensure_ascii=False))
    print("top identifiers:", list(summary["per_identifier_papers"].items())[:12])


if __name__ == "__main__":
    main()
