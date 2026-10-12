r"""Extended Data tables as LaTeX fragments for the manuscript PDF (the image versions from scripts/ed_tables.py stay for
the Word files and for the separate table images Nature asks for at acceptance).

Same four data files as ed_tables.py: Extended Data Table 1 (census summary, data/table1_census_summary.csv, shown as
two stacked panels: a counts, b time to loss), 2 (modes of loss, data/loss_typology.csv, without the note column that
stays in Supplementary Table 15), 3 (effort accounting, data/effort_accounting.csv) and 4 (predictors of a successor
deviation: a, data/p3_predictors_univariate.csv; b, data/p3_predictors_model.csv). Every table is a portrait longtable
(\scriptsize, fixed paragraph widths, stacked headers) sized for the manuscript's text width of 372 pt (131 mm). A row
whose only text is a long sentence (the note under the model table, the incidents row of the effort table) becomes a
full-width row. Cell text is escaped by scripts/si_tex.esc and numbers are formatted by scripts/ed_tables.fmt, so the
two renderings show the same values. No API calls. Output: figures/ed_tables/ed_table{1..4}.tex.
Usage: python scripts/ed_tables_tex.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ed_tables import fmt  # noqa: E402
from si_tex import esc  # noqa: E402

OUT = ROOT / "figures" / "ed_tables"
BS = chr(92)
NL = BS + BS                                            # LaTeX line break
SIZE = BS + "scriptsize"


def P(mm):
    """Left-aligned paragraph column of a fixed width."""
    return ">{" + BS + "raggedright" + BS + "arraybackslash}p{" + f"{mm}mm" + "}"


def head(lines, align="l"):
    """A bold header cell; several lines are stacked."""
    parts = [BS + "textbf{" + esc(x) + "}" for x in lines]
    return parts[0] if len(parts) == 1 else BS + "shortstack[" + align + "]{" + NL.join(parts) + "}"


def longtable(specs, headers, rows, group_rows, sep="3pt"):
    """specs: one column spec per column; headers: header cells; rows: lists of cell strings, or a single string for a
    full-width row; group_rows: {row index: label} for a bold full-width label row inserted before that row."""
    hdr = " & ".join(headers) + " " + NL
    out = [BS + "begingroup" + SIZE + BS + "setlength{" + BS + "tabcolsep}{" + sep + "}" + BS + "renewcommand{" + BS + "arraystretch}{1.08}",
           BS + "begin{longtable}{" + "".join(specs) + "}",
           BS + "toprule", hdr, BS + "midrule", BS + "endfirsthead", BS + "toprule", hdr, BS + "midrule", BS + "endhead",
           BS + "bottomrule", BS + "endfoot"]
    for i, r in enumerate(rows):
        if i in group_rows:
            out.append(BS + "multicolumn{" + str(len(specs)) + "}{l}{" + BS + "textbf{" + esc(group_rows[i]) + "}} " + NL)
        out.append((r if isinstance(r, str) else " & ".join(r)) + " " + NL)
    out += [BS + "end{longtable}", BS + "endgroup"]
    return "\n".join(out) + "\n"


def frame(df, specs, headers, group_col=None, sep="3pt", note_width=118):
    """A DataFrame as a longtable; with group_col, that column becomes bold label rows (the value 'all' gets none). A row
    whose only content beyond its first cell is one long text becomes a full-width 'label: text' row."""
    cols = [c for c in df.columns if c != group_col]
    assert len(cols) == len(specs) == len(headers), (len(cols), len(specs), len(headers))
    rows, groups, last = [], {}, None
    for i, rec in enumerate(df.to_dict("records")):
        if group_col is not None and rec[group_col] != last:
            last = rec[group_col]
            if str(last) != "all":
                groups[i] = str(last)[0].upper() + str(last)[1:]
        vals = [tidy(fmt(rec[c])) for c in cols]
        long = [j for j, v in enumerate(vals) if j > 0 and len(v) > 60]
        if len(long) == 1 and all(v == "" for j, v in enumerate(vals) if j not in (0, long[0])):
            rows.append(BS + "multicolumn{" + str(len(specs)) + "}{" + P(note_width) + "}{" + BS + "textbf{" + esc(vals[0]) + ":} " + esc(vals[long[0]]) + "}")
            continue
        rows.append([esc(v) for v in vals])
    return longtable(specs, headers, rows, groups, sep)


def tidy(s):
    """Whole numbers of a thousand or more lose the trailing .0 that fmt gives float columns."""
    return s[:-2] if re.fullmatch(r"[0-9,]{5,}\.0", s) else s


def panel(letter):
    return BS + "noindent" + BS + "textbf{" + letter + "}" + BS + "par" + BS + "smallskip"


def write(name, blocks):
    (OUT / f"{name}.tex").write_text("\n".join(blocks), encoding="utf-8", newline="\n")
    print(f"figures/ed_tables/{name}.tex written")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rd = lambda f: pd.read_csv(ROOT / "data" / f, encoding="utf-8-sig")
    t1 = rd("table1_census_summary.csv")
    a = frame(t1[["grouping", "group", "papers", "share_pct", "cited_10plus_pct", "born_dead", "born_dead_pct", "in_curve"]], [P(30)] + ["r"] * 6,
              [head(["group"]), head(["papers"], "r"), head(["share", "(%)"], "r"), head(["cited", "≥10 (%)"], "r"), head(["born", "dead"], "r"),
               head(["born", "dead (%)"], "r"), head(["in", "curve"], "r")], group_col="grouping")
    b = frame(t1[["grouping", "group", "lost_by_today_pct", "lost_by_2026_end_pct", "median_months", "q25", "q75", "km_median_months"]], [P(30)] + ["r"] * 6,
              [head(["group"]), head(["lost by", "12 Oct", "2026 (%)"], "r"), head(["lost by", "end-2026", "(%)"], "r"), head(["median", "(months)"], "r"),
               head(["q25"], "r"), head(["q75"], "r"), head(["KM", "median"], "r")], group_col="grouping")
    write("ed_table1", [panel("a"), a, BS + "medskip", panel("b"), b])
    t2 = rd("loss_typology.csv").drop(columns=["note"])                 # the notes stay in Supplementary Table 15
    write("ed_table2", [frame(t2, [P(30), P(24), "r", "r", "r", P(34)],
          [head(["mode"]), head(["stage"]), head(["count"], "r"), head(["denomi-", "nator"], "r"), head(["share", "(%)"], "r"),
           head(["protocol item"])], sep="2.5pt")])
    t3 = rd("effort_accounting.csv")
    write("ed_table3", [frame(t3, [P(25), "r", "r", "r", "r", P(24), "r", "r"],
          [head(["stage"]), head(["papers"], "r"), head(["archived", "calls"], "r"), head(["cost", "(USD)"], "r"),
           head(["cost per", "paper", "(USD)"], "r"), head(["provider"]), head(["deposit", "(MB)"], "r"), head(["deposit", "MB per", "paper"], "r")], sep="1.5pt")])
    ua, ub = rd("p3_predictors_univariate.csv"), rd("p3_predictors_model.csv")
    a = frame(ua, [P(20), P(28), "r", "r", "r", "r", "r", "r"],
              [head(["covariate"]), head(["level"]), head(["results"], "r"), head(["papers"], "r"), head(["devi-", "ated"], "r"),
               head(["share", "(%)"], "r"), head(["Wilson", "low", "(%)"], "r"), head(["Wilson", "high", "(%)"], "r")], sep="2.5pt")
    b = frame(ub, [P(40), "r", "r", "r", "r"],
              [head(["term"]), head(["odds", "ratio"], "r"), head(["CI", "low"], "r"), head(["CI", "high"], "r"), head(["p"], "r")], sep="2.5pt", note_width=110)
    write("ed_table4", [panel("a"), a, BS + "medskip", panel("b"), b])


if __name__ == "__main__":
    main()
