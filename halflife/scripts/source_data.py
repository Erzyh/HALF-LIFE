"""Source Data workbook for the figures of the manuscript (Nature asks for the numbers behind every graph).

One sheet per figure panel, copied verbatim from the data file the figure script reads, plus a README sheet that maps
each sheet to its figure, panel, source file and script. Kaplan-Meier curves whose coordinates are not stored as a
file (the sensitivity and still-served variants of Extended Data Fig. 5) are represented by their summary tables;
they regenerate from data/census_v2.csv with the named scripts. No API calls.
Output: paper/source_data/HALF-LIFE_source_data.xlsx (paper/ is local-only; the workbook is a submission file).
Usage: python scripts/source_data.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "source_data" / "HALF-LIFE_source_data.xlsx"

# sheet, figure, panel, source file, script
SHEETS = [
    ("Fig1a_trend_counts", "Fig. 1", "a", "data/trend_counts.csv", "scripts/trend_counts.py"),
    ("Fig1a_trend_fields", "Fig. 1", "a", "data/trend_fields.csv", "scripts/trend_counts.py"),
    ("Fig1b_model_lifecycles", "Fig. 1", "b", "data/model_lifecycles.csv", "scripts/lifecycle_figure.py"),
    ("Fig2_km_curves", "Fig. 2", "a-c", "data/census_survival_curves.csv", "scripts/census_survival.py"),
    ("Fig2_km_summary", "Fig. 2", "a-c", "data/census_survival_summary.csv", "scripts/census_survival.py"),
    ("Fig3_points", "Fig. 3", "a-b", "data/reexec_forest.csv", "scripts/reexec_forest_by_category.py"),
    ("Fig3_by_category", "Fig. 3", "a-b", "data/reexec_forest_by_category.csv", "scripts/reexec_forest_by_category.py"),
    ("Fig4_points", "Fig. 4", "a-b", "data/p3_figure.csv", "scripts/p3_figure_by_category.py"),
    ("Fig4_by_category", "Fig. 4", "a-b", "data/p3_figure_by_category.csv", "scripts/p3_figure_by_category.py"),
    ("Fig5_protocol_map", "Fig. 5", "", "data/protocol_map.csv", "scripts/protocol_figure.py"),
    ("Fig5_loss_typology", "Fig. 5", "bars", "data/loss_typology.csv", "scripts/loss_typology.py"),
    ("EDFig1_census_refresh", "Extended Data Fig. 1", "", "data/census_refresh_summary.json", "scripts/flow_figure.py"),
    ("EDFig1_successor_ledger", "Extended Data Fig. 1", "", "data/p3_summary.csv", "scripts/flow_figure.py"),
    ("EDFig2_points", "Extended Data Fig. 2", "", "data/reexec_forest.csv", "scripts/reexec_forest.py"),
    ("EDFig2_tiera_claims", "Extended Data Fig. 2", "", "data/tiera_claims.csv", "scripts/reexec_forest.py"),
    ("EDFig3_points", "Extended Data Fig. 3", "", "data/p3_figure.csv", "scripts/p3_figure.py"),
    ("EDFig3_summary", "Extended Data Fig. 3", "", "data/p3_summary.csv", "scripts/p3_figure.py"),
    ("EDFig4_fingerprints", "Extended Data Fig. 4", "c", "data/drift_fingerprints.csv", "scripts/drift_figure.py"),
    ("EDFig4_quantities", "Extended Data Fig. 4", "a-b", "data/drift_quantities.csv", "scripts/drift_figure.py"),
    ("EDFig5a_sensitivity", "Extended Data Fig. 5", "a", "data/sensitivity_survival.csv", "scripts/sensitivity.py"),
    ("EDFig5b_still_served", "Extended Data Fig. 5", "b", "data/census_survival_unconditional.csv", "scripts/census_extension.py"),
    ("EDFig6a_hazard_ratios", "Extended Data Fig. 6", "a", "data/cox_hazard_ratios.csv", "scripts/cox_model.py"),
    ("EDFig6b_schoenfeld", "Extended Data Fig. 6", "b", "data/cox_schoenfeld.csv", "scripts/cox_checks.py"),
    ("EDFig6b_period_hr", "Extended Data Fig. 6", "b", "data/cox_period_hr.csv", "scripts/cox_checks.py"),
]


def load(rel):
    p = ROOT / rel
    if p.suffix == ".json":
        return pd.json_normalize(json.load(open(p, encoding="utf-8")), sep=".").T.reset_index().rename(columns={"index": "key", 0: "value"})
    return pd.read_csv(p, encoding="utf-8-sig")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    readme = pd.DataFrame([{"sheet": s, "figure": f, "panel": pnl, "source file": src, "script": scr} for s, f, pnl, src, scr in SHEETS])
    note = pd.DataFrame({"note": [
        "Source Data for 'The half-life of science that depends on commercial language models'. One sheet per figure panel, copied from the data file the figure script reads.",
        "Kaplan-Meier curves of Extended Data Fig. 5 are drawn by the scripts from data/census_v2.csv; the sheets hold their summary tables (Supplementary Tables 5 and 36).",
        "Every file regenerates from the committed data with scripts/check_regeneration.py. Repository: https://github.com/Erzyh/HALF-LIFE.",
    ]})
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        note.to_excel(xw, sheet_name="README", index=False, startrow=0)
        readme.to_excel(xw, sheet_name="README", index=False, startrow=len(note) + 3)
        for s, _, _, src, _ in SHEETS:
            df = load(src)
            df.to_excel(xw, sheet_name=s, index=False)
            print(f"{s:26s} {len(df):6d} rows  <- {src}")
    print("->", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
