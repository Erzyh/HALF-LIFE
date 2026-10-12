"""Who got re-executed? Selection of the Tier B executed set within the eligible population, and post-stratified rates.

Population: the 216 papers the triage agents judged eligible (harness/tierb/<Wid>.json, verdict == eligible).
Executed: the 86 with a current runs/tierb/<Wid>/result.json. The rest could not be run without a human decision
(unprinted prompts, image input, agent loops, unpublished labels, human grading) or had gated data.
Strata come from the triage tables (field group, year), the census (document type, citations), the config tables
(task type, cost tier, prompt verbatim, data public, model) and the shutdown deadline. For each stratum the table
gives eligible n, executed n and share, and the provisional classes of the executed papers. The reweighted rates
re-weight each executed paper by (eligible share of its stratum) / (executed share of its stratum), one dimension at
a time, so that the executed set matches the eligible population on that dimension.
Writes data/tierb_selection.csv and data/tierb_selection_reweighted.csv. No API calls.
"""
import csv, glob, json, os, re, collections
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]


def load():
    recs = {}
    for p in sorted(glob.glob(str(HALF / "harness" / "tierb" / "W*.json"))):
        wid = os.path.basename(p)[:-5]
        if re.fullmatch(r"W\d+", wid):
            try:
                recs[wid] = json.load(open(p, encoding="utf-8"))
            except Exception:
                pass
    grp = {}
    for p in sorted(glob.glob(str(HALF / "data" / "tierb_triage" / "group_*.csv"))):
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            grp[r["wid"]] = r
    cfg = {}
    for p in sorted(glob.glob(str(HALF / "data" / "tierb_triage" / "config_*.csv"))):
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            cfg[r["wid"]] = r
    cen = {}
    for r in csv.DictReader(open(HALF / "data" / "census_v2.csv", encoding="utf-8-sig")):
        cen[r["openalex_id"].rsplit("/", 1)[-1]] = r
    summ = {r["wid"]: r for r in json.load(open(HALF / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8"))}
    return recs, grp, cfg, cen, summ


def model_family(mid):
    mid = (mid or "").lower()
    for k, v in (("gpt-4-turbo", "gpt-4-turbo"), ("gpt-4o", "gpt-4o"), ("gpt-4.1", "gpt-4.1"), ("o1", "o1"), ("o3", "o3 family"),
                 ("o4", "o4-mini"), ("gpt-5", "gpt-5"), ("gpt-3.5", "gpt-3.5")):
        if mid.startswith(k) or ("-" + k) in mid:
            return v
    return mid[:12] or "unknown"


def cit_band(c):
    try:
        c = int(float(c))
    except Exception:
        return "unknown"
    return "0" if c == 0 else "1-9" if c < 10 else "10-49" if c < 50 else "50+"


def main():
    recs, grp, cfg, cen, summ = load()
    elig = [w for w, r in recs.items() if r.get("verdict") == "eligible"]
    rows = []
    for w in elig:
        r, g, c, ce = recs[w], grp.get(w, {}), cfg.get(w, {}), cen.get(w, {})
        cost = r.get("cost") if isinstance(r.get("cost"), dict) else {}
        live = r.get("live_model") if isinstance(r.get("live_model"), dict) else {}
        rows.append({
            "wid": w, "executed": w in summ, "class": summ.get(w, {}).get("class"),
            "field group": g.get("group") or "unknown",
            "year": str(g.get("year") or ce.get("year") or "unknown"),
            "document type": ce.get("type") or "unknown",
            "citations": cit_band(ce.get("citations")),
            "cost tier": (c.get("cost_tier") or cost.get("tier") or "unknown"),
            "task type": c.get("task_type") or "no config",
            "prompt verbatim": c.get("prompt_verbatim") or (r.get("prompt") or {}).get("verbatim", "unknown") if isinstance(r.get("prompt"), dict) or c else "unknown",
            "data public": c.get("data_public") or ((r.get("data") or {}).get("public") if isinstance(r.get("data"), dict) else "unknown") or "unknown",
            "model family": model_family(c.get("resolved_model") or live.get("resolved")),
        })
    dims = ["field group", "year", "document type", "citations", "cost tier", "task type", "prompt verbatim", "data public",
            "model family"]
    out, rew = [], []
    classes = ("재현", "근접", "편차", "확인 필요")
    n_e, n_x = len(rows), sum(r["executed"] for r in rows)
    raw = collections.Counter(r["class"] for r in rows if r["executed"])
    rew.append({"dimension": "none (raw executed set)", "n_executed": n_x, **{k: round(100 * raw[k] / n_x, 1) for k in classes}})
    for d in dims:
        strata = sorted({r[d] for r in rows}, key=lambda x: (x == "unknown", str(x)))
        wsum = collections.Counter(); wtot = 0.0
        for s_ in strata:
            e = [r for r in rows if r[d] == s_]
            x = [r for r in e if r["executed"]]
            cc = collections.Counter(r["class"] for r in x)
            out.append({"dimension": d, "stratum": s_, "eligible": len(e), "executed": len(x),
                        "pct_executed": round(100 * len(x) / len(e), 1) if e else None,
                        **{k: cc[k] for k in classes},
                        "pct_reproduced_of_executed": round(100 * cc["재현"] / len(x), 1) if x else None})
            if x:
                wgt = (len(e) / n_e) / (len(x) / n_x)         # eligible share over executed share
                for r in x:
                    wsum[r["class"]] += wgt; wtot += wgt
        rew.append({"dimension": d, "n_executed": n_x, **{k: round(100 * wsum[k] / wtot, 1) for k in classes}})
    with open(HALF / "data" / "tierb_selection.csv", "w", newline="", encoding="utf-8-sig") as f:
        wri = csv.DictWriter(f, fieldnames=list(out[0].keys())); wri.writeheader(); wri.writerows(out)
    with open(HALF / "data" / "tierb_selection_reweighted.csv", "w", newline="", encoding="utf-8-sig") as f:
        wri = csv.DictWriter(f, fieldnames=list(rew[0].keys())); wri.writeheader(); wri.writerows(rew)
    print(f"eligible {n_e}, executed {n_x} ({100 * n_x / n_e:.0f}%)")
    for d in dims:
        cells = [o for o in out if o["dimension"] == d]
        print(f"  {d}: " + "; ".join(f"{o['stratum']} {o['executed']}/{o['eligible']}" for o in cells))
    print("reweighted reproduced share by dimension:", {r["dimension"]: r["재현"] for r in rew})
    print("-> data/tierb_selection.csv, data/tierb_selection_reweighted.csv")


if __name__ == "__main__":
    main()
