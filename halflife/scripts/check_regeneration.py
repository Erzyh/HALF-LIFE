"""Regenerate the paper's tables from the committed data and check that nothing changed.

python scripts/check_regeneration.py [--skip-run] [--tolerance 1e-6]

Runs the analysis scripts that need no API access, in dependency order, then compares every CSV they write and
SUPPLEMENTARY_TABLES.md with the committed versions (git HEAD). Numeric cells are compared with a relative tolerance so
that a different platform's floating point does not count as a change; text cells must match exactly. Exit code 1 when
a table differs, 2 when a script fails. Figures are regenerated but not compared (font availability differs between
machines). Used by the public repository's GitHub Actions workflow; also handy before a commit.

Not covered on purpose: scripts/trend_counts.py (live OpenAlex counts), scripts/loss_typology.py (counts the deposited
call archives, which are not in the repository), scripts/drift_figure.py (reads a call archive) and
scripts/protocol_figure.py (layout differs between matplotlib builds). scripts/format_cases_summary.py (Table S33) is
run but re-scores the deposited item archives; where they are absent it leaves data/format_cases.csv unchanged.
"""
import argparse
import csv
import io
import subprocess
import sys
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
SCRIPTS = ["judgment_merge", "judgment_apply", "tiera_claims", "census_survival", "sensitivity", "cox_model", "cox_checks", "lifecycle_figure", "tierb_summary", "reexec_forest",
           "reexec_forest_by_category", "p3_summary", "p3_figure", "p3_figure_by_category", "p3_repeat_summary", "p3_bf16_summary", "p3_paraphrase_summary", "tiera_successor_summary", "p3_selection_bounds", "format_cases_summary", "census_extension", "claim_level_cases", "temperature_summary",
           "p3_agreement", "robustness_notes", "km_median_ci", "release_lag", "triage_audit", "flow_figure", "results_report", "coding_pilot_report", "coding_main_report",
           "coding_executed_halflife", "rule_across_designs", "threshold_sensitivity", "judgment_first_return", "supp_tables"]
COMPARE = ["SUPPLEMENTARY_TABLES.md"]   # plus every data/*.csv that the scripts above touch


def git_show(rel):
    r = subprocess.run(["git", "-C", str(HALF), "show", f"HEAD:halflife/{rel}"], capture_output=True)
    return r.stdout.decode("utf-8-sig") if r.returncode == 0 else None


def cells(text):
    return list(csv.reader(io.StringIO(text)))


def same_cell(a, b, tol):
    if a == b:
        return True
    try:
        x, y = float(a), float(b)
    except ValueError:
        return False
    if x != x and y != y:            # both NaN
        return True
    return abs(x - y) <= tol * max(1.0, abs(x), abs(y))


def compare(rel, tol):
    old = git_show(rel)
    new_p = HALF / rel
    if old is None or not new_p.exists():
        return f"{rel}: {'not in HEAD' if old is None else 'missing after regeneration'}"
    new = new_p.read_text(encoding="utf-8-sig")
    if rel.endswith(".csv"):
        A, B = cells(old), cells(new)
        if len(A) != len(B):
            return f"{rel}: {len(A)} rows in HEAD, {len(B)} regenerated"
        for i, (ra, rb) in enumerate(zip(A, B)):
            if len(ra) != len(rb) or not all(same_cell(a, b, tol) for a, b in zip(ra, rb)):
                return f"{rel}: row {i + 1} differs: {ra[:6]} != {rb[:6]}"
        return None
    if old.replace("\r\n", "\n") != new.replace("\r\n", "\n"):
        la, lb = old.replace("\r\n", "\n").splitlines(), new.replace("\r\n", "\n").splitlines()
        first = next((k for k, (x, y) in enumerate(zip(la, lb)) if x != y), min(len(la), len(lb)))
        return f"{rel}: line {first + 1} differs"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-run", action="store_true", help="only compare (after running the scripts yourself)")
    ap.add_argument("--tolerance", type=float, default=1e-6)
    a = ap.parse_args()
    before = {p: p.stat().st_mtime for p in (HALF / "data").glob("*.csv")}
    if not a.skip_run:
        for s in SCRIPTS:
            r = subprocess.run([sys.executable, str(HALF / "scripts" / f"{s}.py")], cwd=HALF, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"})
            print(f"{s:28s} rc={r.returncode}")
            if r.returncode:
                print((r.stderr or "").strip().splitlines()[-1][:300] if r.stderr else "")
                sys.exit(2)
    touched = [f"data/{p.name}" for p in (HALF / "data").glob("*.csv") if p.stat().st_mtime > before.get(p, 0) or a.skip_run]
    problems = [m for rel in sorted(set(COMPARE + touched)) for m in [compare(rel, a.tolerance)] if m]
    print(f"compared {len(set(COMPARE + touched))} files; differences: {len(problems)}")
    for m in problems:
        print("   " + m)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
