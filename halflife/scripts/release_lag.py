"""Decomposition of the time to loss (Table S43): time to loss = identifier lifespan - (publication - release).

For every paper in the curve (census_survival.build, born-dead papers excluded): the identifier that retires first,
its release date, the lag from that release to the paper's publication date as indexed (negative when the indexed date
precedes the release: the indexed version predates the model, and the survival analysis then starts the paper at the
release), the lifespan of the identifier from release to its published retirement date, and the time to loss from the
corrected origin. Summaries overall and by the vendor of the first-retiring identifier: medians and quartiles, the share
of papers published within six months of the release, the share dated before the release, and the as-of Kaplan-Meier
median (censored at the analysis date) for comparison. No API calls. Output: data/release_lag.csv.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from census_survival import MONTH, analyse, build  # noqa: E402


def q(s):
    s = s.dropna()
    return (round(float(s.median()), 1), round(float(s.quantile(0.25)), 1), round(float(s.quantile(0.75)), 1)) if len(s) else (None, None, None)


def main():
    tm = {m["id"]: m["vendor"] for m in __import__("json").load(open(ROOT / "target_models.json", encoding="utf-8"))["models"]}
    base = build()[0]
    live = base[base["first_shutdown"] > base["pub"]].copy()
    missing = int(live["release_first"].isna().sum())
    live = live[live["release_first"].notna()].copy()
    live["lag_months"] = [(p - r).days / MONTH for p, r in zip(live["pub_raw"], live["release_first"])]
    live["lifespan_months"] = [(s - r).days / MONTH for s, r in zip(live["first_shutdown"], live["release_first"])]
    live["loss_months"] = [(s - p).days / MONTH for s, p in zip(live["first_shutdown"], live["pub"])]
    live["vendor_first"] = [tm.get(m, "openai") for m in live["first_model"]]
    rows = []
    for name, sub in [("all papers in the curve", live)] + [(f"first-retiring identifier from {v}", live[live["vendor_first"] == v]) for v in ("openai", "anthropic", "google")]:
        asof = analyse(sub, "first_shutdown", known=False)[0]
        lag, lifespan, loss = q(sub["lag_months"]), q(sub["lifespan_months"]), q(sub["loss_months"])
        rows.append({"group": name, "papers": len(sub), "median_release_to_publication_months": lag[0], "lag_q25": lag[1], "lag_q75": lag[2],
                     "share_published_within_6_months_of_release_pct": round(100 * float((sub["lag_months"] <= 6).mean()), 1),
                     "share_dated_before_release_pct": round(100 * float((sub["lag_months"] < 0).mean()), 1),
                     "median_identifier_lifespan_months": lifespan[0], "lifespan_q25": lifespan[1], "lifespan_q75": lifespan[2],
                     "median_time_to_loss_months": loss[0], "loss_q25": loss[1], "loss_q75": loss[2],
                     "km_median_months_censored": asof["median_months"], "km_q25": asof["q25_months"], "km_q75": asof["q75_months"]})
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "data" / "release_lag.csv", index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))
    print(f"papers without a release date for the first-retiring identifier: {missing}")
    print("-> data/release_lag.csv")


if __name__ == "__main__":
    main()
