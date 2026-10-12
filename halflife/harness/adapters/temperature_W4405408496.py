"""Card W4405408496 - The Impact of Temperature on Extracting Information From Clinical Trial Publications Using
Large Language Models (Windisch et al., Cureus 16(12):e75748, 2024; repo windisch-paul/temperature @ 26e3eec).

Claim re-measured (Tables 1-3; gpt-4o-2024-05-13 primary, gpt-4o-mini-2024-07-18 second model; nine temperatures
0.00-2.00 in steps of 0.25, one call per abstract per temperature):
  Task 1 (996 RCT abstracts): share of correctly formatted numeric predictions of the number randomized is flat at
      98.7-99.0% for T <= 1.50 and drops to 95.6% (T=1.75) and 89.2% (T=2.00); on the formatted subset MAPE
      (1.0-3.8%) and within-10% (96.2-98.0%) do not degrade.
  Task 2 (899 abstracts): [RCT, oncology] classification formatted 100% up to T=1.25, 99.9% at 1.50, 98.9% at 1.75,
      93.3% at 2.00; RCT F1 0.956-0.960 and oncology F1 0.965-0.977 flat.
  Judgment rule (card): SURVIVED if the median re-run has a formatted rate >= 97% at every T <= 1.50, a drop >= 3
  points at T=2.00 vs T=0.00 and MAPE within +/-2 points of Table 1 at every T; PARTIAL if the drop starts at
  T <= 1.25 or is < 3 points, or error metrics drift 2-5 points; DEAD if T=2.00 is within 1 point of T=0.00 or the
  formatted rate is < 95% already at T <= 1.00. gpt-4o Task 1 decides the label (the literal SURVIVED clause names
  MAPE only; within-10% drift is reported as a flag); gpt-4o-mini and Task 2 are reported, not judged.

Protocol (paper Methods, verbatim; the API-calling script is not in the repository):
  POST /v1/chat/completions with body = {model, messages: [system, user], temperature, max_tokens: 10} and nothing
  else (paper: 'max_tokens set to 10 ... All other API parameters were left at their default'). The paper used
  openai-python 1.40.3, whose chat.completions.create() sends exactly the parameters that are passed, so this is the
  original wire body; here the harness posts it over raw HTTPS (harness/openai_client.py).
  System prompt = SYS['task1'] / SYS['task2'] below, copied from the Methods; user message = the 'abstract' column
  exactly as stored in the released CSV (no title, no stripping; the CSV abstracts carry no surrounding whitespace).
  One pass per temperature (seed_idx 0) paired with the released per-item responses, plus two extra repeats
  (seed_idx 1, 2) at T=0.00 and T=2.00 for run-to-run variance (decisions_2026_09_18; no paraphrase arm).

Scoring = analysis.ipynb cells 17-20 / 23-26 (Task 1) and 30-34 / 38-42 (Task 2), re-implemented with numpy:
  formatted % = formatted replies / all abstracts; MAPE, within-10% and within-1% (strict <) over the formatted
  subset; accuracy = correct / formatted; precision = TP / predicted positives; recall = TP / (positives with a
  formatted reply); F1 = harmonic mean. The raw -> parsed step is NOT in the notebook (the CSVs already hold the
  parsed columns); the rules below were inferred and reproduce every released parsed value (--check reports the
  mismatch count, 0 at the time of writing):
    Task 1: formatted iff the whole reply is a string of ASCII digits (re.fullmatch r'\\d+'); 'null', '', '56,676',
            '216.', '600  ' (trailing blanks), '480\\n\\n\\n\\n', '618<gibberish>' are all unformatted. Python int()
            would accept the blank-padded replies but the authors' converter did not, so int() is not used.
    Task 2: ast.literal_eval(reply) on the UNSTRIPPED reply must yield a list or tuple of exactly two bools
            ('[True, False]', ' [False, False]', '[True, True]\\n', '(False, False)', 'False, False' are formatted;
            '[True, False]<gibberish>', '[[ False, False].', '\\u2028[True, True]', lower-case '[true, false]' are not).
Assumptions and data notes:
  * max_tokens = 10 is stated in the paper; finish_reason == 'length' is recorded per reply (expected for gibberish).
  * A missing message content (None) is scored as unformatted. Replies of exactly 'null' are counted separately.
  * CSV columns used: doi, date, journal, abstract, Number_randomized (Task 1); RCT_actual, Oncology_actual (Task 2);
    released replies '<M>_temp<TTT>_response_raw' / '<M>_temp<TTT>_response' (Task 1) and
    '<M>_rct_onc_temp<TTT>_response_raw' / '<M>_temp<TTT>_rct_response' / '<M>_temp<TTT>_oncology_response' (Task 2),
    M in {GPT-4o, GPT-4o-mini}, TTT in {000, 025, ..., 200}. CSVs are read with dtype=str, keep_default_na=False.
  * Five GPT-4o-mini Task 1 raw columns (T = 0.00, 0.25, 0.75, 1.00, 1.50) were float-cast when the authors wrote
    the CSV ('1072.0'); the '.0' is removed before parsing (only in columns where every non-empty cell is '<int>.0').
    About 90 raw cells per model are empty strings: most likely 'null' replies (pandas reads 'null' as NA) or empty
    replies; unformatted either way, but their text is lost, so paired agreement is measured on parsed values
    (identical formatted value; same formatted status), never on raw text.
  * Item set = the repository CSVs as they are (Task 1 n=996, Task 2 n=899). The paper describes seven journals and
    2010-2022 for both tasks and n=900 for Task 2; the Task 1 CSV holds four journal labels (NEJM, Lancet, JAMA, BMJ)
    and 2020-2023, the Task 2 CSV seven journals and 2010-2023 (documented discrepancy; --check prints the tables).
  * Public-archive policy: every request's meta carries doi, abstract_sha256 (sha256 of the exact user message) and
    the ground truth, so --analyze and the per-item CSV (items.csv) work without the abstract text.
  * Request order = priority blocks so that a budget cap cuts the least important calls: gpt-4o Task 1 pass 0,
    gpt-4o-mini Task 1 and Task 2 pass 0, gpt-4o Task 1 repeats, gpt-4o-mini repeats, gpt-4o Task 2 pass 0,
    gpt-4o Task 2 repeats. Inside a block abstracts are interleaved over temperatures, so a cut leaves every
    temperature with the same abstracts (the judgment then carries a '[subset: n/996]' suffix).
  * Pricing (harness/pricing.json): gpt-4o-2024-05-13 $5/$15, gpt-4o-mini-2024-07-18 $0.15/$0.60 per 1M tokens.
  * Bootstrap 95% CIs: 1,000 resamples of abstracts (numpy default_rng(0)); the same index matrix is reused for
    every model/temperature of the same size.

  python adapters/temperature_W4405408496.py --check      # data vs paper, request bodies, re-score released replies
  python adapters/temperature_W4405408496.py --dry-run    # request list + cost estimate per model and per block
  python adapters/temperature_W4405408496.py --run [--cap 40] [--workers 4]
  python adapters/temperature_W4405408496.py --analyze
"""
import argparse, ast, hashlib, json, re, sys, warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, pricing_for, run_battery  # noqa: E402

HALF = HERE.parent.parent
CARD_ID = "W4405408496"
REPO = HALF / "external" / "repos" / CARD_ID / "windisch-paul__temperature"
REPO_URL, REPO_COMMIT = "https://github.com/windisch-paul/temperature", "26e3eec096b9f5a733fc07c371f81800349570a6"
CSV = {"task1": REPO / "sample_size_gpt_responses_all.csv", "task2": REPO / "rct_oncology_gpt_responses_all.csv"}
RUN = HALF / "runs" / CARD_ID / "baseline_alive"
CAP = 40.0
MODELS = {"gpt-4o": "gpt-4o-2024-05-13", "gpt-4o-mini": "gpt-4o-mini-2024-07-18"}   # model key -> snapshot
CSV_PREFIX = {"gpt-4o": "GPT-4o", "gpt-4o-mini": "GPT-4o-mini"}                        # model key -> released column prefix
TEMPS = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
TCODE = {t: f"{int(round(t * 100)):03d}" for t in TEMPS}      # 0.25 -> '025' (CSV column names)
TKEY = {t: f"{t:.2f}" for t in TEMPS}                          # 0.25 -> '0.25' (JSON keys)
MAX_TOKENS = 10
REPEAT_TEMPS, REPEAT_SEEDS = (0.0, 2.0), (1, 2)
N_BOOT = 1000
BLOCKS = [("gpt-4o", "task1", "pass0"), ("gpt-4o-mini", "task1", "pass0"), ("gpt-4o-mini", "task2", "pass0"),
          ("gpt-4o", "task1", "repeats"), ("gpt-4o-mini", "task1", "repeats"), ("gpt-4o-mini", "task2", "repeats"),
          ("gpt-4o", "task2", "pass0"), ("gpt-4o", "task2", "repeats")]

SYS = {
    "task1": ("You will be provided with the abstract of an RCT. Your task will be to extract the number of people who "
              "underwent randomization. If this number is not explicitly mentioned, you may use other numerical information "
              "(e.g. the number of total participants or adding up the number of patients in each arm). Please return only "
              "the number as a single integer. If no information is available, please return null."),
    "task2": ("You will be provided with the abstract of a medical publication. Your task will be to determine if the "
              "abstract reports on a RCT. If the abstract reports on a systematic review or meta-analysis of RCTs or a "
              "commentary/editorial, return false. In addition, you will be asked to determine if the abstract focuses on an "
              "oncology topic which includes all papers dealing with the prevention, diagnosis or treatment of solid or "
              "hematologic cancers. Your response should be a list of two boolean values (True or False), the first "
              "indicating if the paper is an RCT and the second indicating if the paper is oncology-related. The list should "
              "be enclosed in brackets and separated by a comma, e.g. [True, False]."),
}

# Tables 1-3 of the paper. task1: (formatted %, MAPE %, within-10 %, within-1 %); rct/onc: (formatted %, accuracy, precision, recall, F1)
PAPER = {
    "gpt-4o": {
        "task1": {"0.00": (98.7, 1.7, 96.9, 94.1), "0.25": (98.8, 1.8, 97.0, 94.0), "0.50": (98.7, 1.5, 97.3, 94.3),
                  "0.75": (99.0, 2.3, 96.5, 93.6), "1.00": (98.8, 2.0, 96.5, 93.7), "1.25": (98.7, 1.7, 96.6, 93.7),
                  "1.50": (98.7, 3.8, 96.2, 93.4), "1.75": (95.6, 1.8, 96.7, 94.2), "2.00": (89.2, 1.0, 98.0, 95.3)},
        "rct": {"0.00": (100.0, 0.957, 0.915, 1.000, 0.956), "0.25": (100.0, 0.959, 0.919, 1.000, 0.958),
                "0.50": (100.0, 0.957, 0.915, 1.000, 0.956), "0.75": (100.0, 0.958, 0.917, 1.000, 0.957),
                "1.00": (100.0, 0.960, 0.921, 1.000, 0.959), "1.25": (100.0, 0.960, 0.921, 1.000, 0.959),
                "1.50": (99.9, 0.961, 0.923, 1.000, 0.960), "1.75": (98.9, 0.960, 0.921, 1.000, 0.959),
                "2.00": (93.3, 0.957, 0.916, 1.000, 0.956)},
        "onc": {"0.00": (100.0, 0.983, 0.967, 0.971, 0.969), "0.25": (100.0, 0.982, 0.963, 0.971, 0.967),
                "0.50": (100.0, 0.984, 0.967, 0.975, 0.971), "0.75": (100.0, 0.983, 0.963, 0.975, 0.969),
                "1.00": (100.0, 0.982, 0.963, 0.971, 0.967), "1.25": (100.0, 0.983, 0.963, 0.975, 0.969),
                "1.50": (99.9, 0.981, 0.963, 0.967, 0.965), "1.75": (98.9, 0.988, 0.967, 0.988, 0.977),
                "2.00": (93.3, 0.985, 0.970, 0.974, 0.972)},
    },
    "gpt-4o-mini": {
        "task1": {"0.00": (99.1, 1.5, 96.8, 92.7), "0.25": (99.1, 1.5, 96.8, 92.7), "0.50": (99.0, 1.3, 97.0, 93.1),
                  "0.75": (99.1, 1.4, 96.9, 92.7), "1.00": (99.1, 1.4, 96.7, 92.9), "1.25": (99.1, 1.3, 97.0, 93.1),
                  "1.50": (99.1, 1.5, 96.7, 92.8), "1.75": (97.5, 1.6, 96.4, 92.4), "2.00": (90.2, 1.6, 96.7, 92.9)},
        "rct": {"0.00": (100.0, 0.915, 0.847, 1.000, 0.917), "0.25": (100.0, 0.918, 0.851, 1.000, 0.919),
                "0.50": (100.0, 0.915, 0.847, 1.000, 0.917), "0.75": (100.0, 0.919, 0.852, 1.000, 0.920),
                "1.00": (100.0, 0.920, 0.854, 1.000, 0.921), "1.25": (100.0, 0.917, 0.849, 1.000, 0.918),
                "1.50": (99.6, 0.918, 0.852, 1.000, 0.920), "1.75": (97.7, 0.916, 0.849, 1.000, 0.918),
                "2.00": (92.4, 0.911, 0.842, 1.000, 0.914)},
        "onc": {"0.00": (100.0, 0.983, 0.952, 0.988, 0.970), "0.25": (100.0, 0.983, 0.952, 0.988, 0.970),
                "0.50": (100.0, 0.984, 0.956, 0.988, 0.972), "0.75": (100.0, 0.982, 0.945, 0.992, 0.968),
                "1.00": (100.0, 0.984, 0.956, 0.988, 0.972), "1.25": (100.0, 0.984, 0.956, 0.988, 0.972),
                "1.50": (99.6, 0.980, 0.937, 0.992, 0.964), "1.75": (97.7, 0.981, 0.940, 0.992, 0.965),
                "2.00": (92.4, 0.983, 0.953, 0.987, 0.970)},
    },
}
T1_KEYS = ("formatted_pct", "mape_pct", "within10_pct", "within1_pct")
T2_KEYS = ("formatted_pct", "accuracy", "precision", "recall", "f1")
PAPER_DESIGN = {"task1": {"n": 996, "journals": "seven journals (BMJ, JAMA, JAMA Oncology, J Clin Oncol, Lancet, Lancet Oncology, NEJM)",
                          "years": "2010-2022"},
                "task2": {"n": 900, "journals": "the same seven journals", "years": "2010-2022"}}


# ----------------------------------------------------------------------------------------------------------- data
def load_csv(task):
    return pd.read_csv(CSV[task], dtype=str, keep_default_na=False, encoding="utf-8")


def truth_of(task, df):
    """Task 1: float array of Number_randomized. Task 2: (RCT_actual, Oncology_actual) bool arrays."""
    if task == "task1":
        return df["Number_randomized"].astype(float).to_numpy()
    return df["RCT_actual"].eq("True").to_numpy(), df["Oncology_actual"].eq("True").to_numpy()


def raw_column(task, mkey, t):
    return f"{CSV_PREFIX[mkey]}_temp{TCODE[t]}_response_raw" if task == "task1" else f"{CSV_PREFIX[mkey]}_rct_onc_temp{TCODE[t]}_response_raw"


def released_raw(df, task, mkey, t):
    """Released raw replies as stored. Undoes the float cast ('1072.0' -> '1072') in columns where every non-empty
    cell has that shape (five GPT-4o-mini Task 1 columns). Returns (list of str, float_cast_flag)."""
    vals = df[raw_column(task, mkey, t)].tolist()
    nonempty = [v for v in vals if v != ""]
    floatcast = bool(nonempty) and all(re.fullmatch(r"\d+\.0", v) for v in nonempty)
    if floatcast:
        vals = [v[:-2] if v else v for v in vals]
    return vals, floatcast


def released_parsed(df, task, mkey, t):
    """The authors' own parsed columns as float arrays (NaN = unformatted); Task 2 returns (rct, onc)."""
    if task == "task1":
        return np.array([float(v) if v != "" else np.nan for v in df[f"{CSV_PREFIX[mkey]}_temp{TCODE[t]}_response"]])
    conv = {"": np.nan, "True": 1.0, "False": 0.0}
    return (np.array([conv[v] for v in df[f"{CSV_PREFIX[mkey]}_temp{TCODE[t]}_rct_response"]]),
            np.array([conv[v] for v in df[f"{CSV_PREFIX[mkey]}_temp{TCODE[t]}_oncology_response"]]))


# -------------------------------------------------------------------------------------------------------- parsing
def parse_int(text):
    """Authors' Task 1 rule (inferred): formatted iff the whole reply is ASCII digits."""
    if isinstance(text, str) and re.fullmatch(r"\d+", text):
        return int(text)
    return None


def parse_bools(text):
    """Authors' Task 2 rule (inferred): ast.literal_eval of the unstripped reply gives a 2-sequence of bools."""
    if not isinstance(text, str):
        return None
    try:
        v = ast.literal_eval(text)
    except Exception:
        return None
    if isinstance(v, (list, tuple)) and len(v) == 2 and all(type(x) is bool for x in v):
        return (v[0], v[1])
    return None


def parse(task, text):
    return parse_int(text) if task == "task1" else parse_bools(text)


def pred_arrays(task, parsed):
    """Parsed values -> float array(s) with NaN for unformatted replies."""
    if task == "task1":
        return np.array([np.nan if p is None else float(p) for p in parsed])
    return (np.array([np.nan if p is None else float(p[0]) for p in parsed]),
            np.array([np.nan if p is None else float(p[1]) for p in parsed]))


def reply_of(rec):
    """(message content, finish_reason) of an archived call."""
    try:
        ch = rec["response"]["choices"][0]
        return ch["message"].get("content"), ch.get("finish_reason")
    except (KeyError, IndexError, TypeError):
        return None, None


def is_null_reply(text):
    return isinstance(text, str) and text.strip().lower() == "null"


# -------------------------------------------------------------------------------------------------------- metrics
def _f(v):
    return None if v is None or (isinstance(v, (float, np.floating)) and np.isnan(v)) else float(v)


def _ci(arr):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return [_f(np.nanpercentile(arr, 2.5)), _f(np.nanpercentile(arr, 97.5))]


def t1_metrics(gt, pred, boot=None):
    """Notebook cells 17-20: formatted % over all items; MAPE / within-10 / within-1 over the formatted subset."""
    f = ~np.isnan(pred)
    with np.errstate(invalid="ignore", divide="ignore"):
        ape = np.abs(gt - pred) / gt
    out = {"n": int(len(gt)), "n_formatted": int(f.sum()), "formatted_pct": float(f.mean() * 100)}
    if f.any():
        out.update(mape_pct=float(np.nanmean(ape) * 100), within10_pct=float((ape < 0.1).sum() / f.sum() * 100),
                   within1_pct=float((ape < 0.01).sum() / f.sum() * 100))
    else:
        out.update(mape_pct=None, within10_pct=None, within1_pct=None)
    if boot is not None and f.any():
        F, A = f[boot], ape[boot]
        nf = F.sum(1)
        with np.errstate(invalid="ignore", divide="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            b = {"formatted_pct": F.mean(1) * 100, "mape_pct": np.nanmean(A, 1) * 100,
                 "within10_pct": (A < 0.1).sum(1) / nf * 100, "within1_pct": (A < 0.01).sum(1) / nf * 100}
        out["ci95"] = {k: _ci(v) for k, v in b.items()}
    return out


def t2_metrics(actual, pred, boot=None):
    """Notebook cells 30-34 for one label: formatted %, accuracy, precision, recall, F1 (formatted subset)."""
    f = ~np.isnan(pred)

    def calc(a, p, fm):
        with np.errstate(invalid="ignore", divide="ignore"):
            nf = fm.sum(-1)
            acc = (p == a).sum(-1) / nf                     # NaN never equals -> not correct, as in the notebook
            tp = ((p == 1) & a).sum(-1)
            prec = tp / (p == 1).sum(-1)
            rec = tp / (a & fm).sum(-1)
            f1 = 2 * prec * rec / (prec + rec)
        return {"formatted_pct": fm.mean(-1) * 100, "accuracy": acc, "precision": prec, "recall": rec, "f1": f1}

    point = calc(actual, pred, f)
    out = {"n": int(len(actual)), "n_formatted": int(f.sum())}
    out.update({k: _f(v) for k, v in point.items()})
    if boot is not None:
        out["ci95"] = {k: _ci(v) for k, v in calc(actual[boot], pred[boot], f[boot]).items()}
    return out


def score(task, truth, parsed, boot=None):
    """truth: task-1 float array or task-2 (rct, onc) bool arrays -> {label: metrics}."""
    if task == "task1":
        return {"task1": t1_metrics(truth, pred_arrays(task, parsed), boot)}
    p_r, p_o = pred_arrays(task, parsed)
    return {"rct": t2_metrics(truth[0], p_r, boot), "onc": t2_metrics(truth[1], p_o, boot)}


def rescore_released(dfs, use="raw"):
    """Tables 1-3 from the released CSVs. use='raw': our parser on the raw replies; use='parsed': the authors' columns."""
    out = {}
    for mkey in MODELS:
        out[mkey] = {}
        for task, df in dfs.items():
            truth = truth_of(task, df)
            for t in TEMPS:
                if use == "raw":
                    raws, _ = released_raw(df, task, mkey, t)
                    res = score(task, truth, [parse(task, x) for x in raws])
                elif task == "task1":
                    res = {"task1": t1_metrics(truth, released_parsed(df, task, mkey, t))}
                else:
                    p_r, p_o = released_parsed(df, task, mkey, t)
                    res = {"rct": t2_metrics(truth[0], p_r), "onc": t2_metrics(truth[1], p_o)}
                for lab, m in res.items():
                    out[mkey].setdefault(lab, {})[TKEY[t]] = m
    return out


def fmt(v, d):
    return "  n/a" if v is None else f"{v:.{d}f}"


def compare_tables(mine, label):
    """Print our numbers next to the paper's Tables 1-3; return the mismatches beyond rounding."""
    mism = []
    for mkey in MODELS:
        print(f"\n[{label}] {mkey}  Table 1 - T: formatted % | MAPE % | within-10 % | within-1 %   (ours vs paper)")
        for t in TEMPS:
            m, p = mine[mkey]["task1"][TKEY[t]], PAPER[mkey]["task1"][TKEY[t]]
            cells = []
            for k, pv in zip(T1_KEYS, p):
                bad = m[k] is None or abs(m[k] - pv) > 0.05 + 1e-9
                cells.append(f"{fmt(m[k], 1)} vs {pv:.1f}" + (" MISMATCH" if bad else ""))
                if bad:
                    mism.append((mkey, "task1", TKEY[t], k, m[k], pv))
            print(f"  T={TKEY[t]}  " + " | ".join(cells))
        for lab, name in (("rct", "Table 2 RCT"), ("onc", "Table 3 oncology")):
            print(f"[{label}] {mkey}  {name} - T: formatted % | accuracy | precision | recall | F1   (ours vs paper)")
            for t in TEMPS:
                m, p = mine[mkey][lab][TKEY[t]], PAPER[mkey][lab][TKEY[t]]
                cells = []
                for k, pv in zip(T2_KEYS, p):
                    d, tol = (1, 0.05) if k == "formatted_pct" else (3, 0.0005)
                    bad = m[k] is None or abs(m[k] - pv) > tol + 1e-9
                    cells.append(f"{fmt(m[k], d)} vs {pv:.{d}f}" + (" MISMATCH" if bad else ""))
                    if bad:
                        mism.append((mkey, lab, TKEY[t], k, m[k], pv))
                print(f"  T={TKEY[t]}  " + " | ".join(cells))
    return mism


def taxonomy(task, raws):
    """Counts of unformatted reply shapes (released data), for the frictions list."""
    c = {}
    for x in raws:
        if parse(task, x) is not None:
            continue
        s = x.strip()
        if x == "":
            k = "empty cell (a 'null' reply lost to pandas NA, or an empty reply)"
        elif s.lower() == "null":
            k = "'null'"
        elif task == "task1" and re.fullmatch(r"\d{1,3}(,\d{3})+", s):
            k = "thousands separator ('56,676')"
        elif task == "task1" and re.match(r"\d", s):
            k = "digits followed by blanks/text/gibberish"
        elif task == "task2" and re.match(r"[\[(]\s*(True|False)\s*,\s*(True|False)\s*[\])]", s):
            k = "list followed by text/gibberish"
        else:
            k = "other (prose or gibberish)"
        c[k] = c.get(k, 0) + 1
    return c


# ------------------------------------------------------------------------------------------------------- requests
def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def body(model, task, abstract, t):
    return {"model": model, "messages": [{"role": "system", "content": SYS[task]}, {"role": "user", "content": abstract}],
            "temperature": t, "max_tokens": MAX_TOKENS}


def item_requests(mkey, task, df, temps, seeds):
    """Abstracts interleaved over temperatures (and repeats) so that a budget cut keeps the temperatures balanced."""
    if task == "task1":
        truth = df["Number_randomized"].astype(float).astype(int).tolist()
    else:
        truth = [[bool(r), bool(o)] for r, o in zip(df["RCT_actual"].eq("True"), df["Oncology_actual"].eq("True"))]
    reqs = []
    for i, (doi, abstract) in enumerate(zip(df["doi"], df["abstract"])):
        for t in temps:
            for s in seeds:
                reqs.append({"id": f"{task}_{mkey}_T{TCODE[t]}_{doi}", "seed_idx": s,
                             "meta": {"task": task, "model_key": mkey, "temperature": t, "repeat": s, "row": i, "doi": doi,
                                      "abstract_sha256": sha(abstract), "truth": truth[i]},
                             "body": body(MODELS[mkey], task, abstract, t)})
    return reqs


def build_requests(dfs=None):
    """[(block, [requests])] in priority order (see module docstring)."""
    dfs = dfs or {k: load_csv(k) for k in CSV}
    blocks = []
    for mkey, task, kind in BLOCKS:
        temps, seeds = (TEMPS, (0,)) if kind == "pass0" else (REPEAT_TEMPS, REPEAT_SEEDS)
        blocks.append(((mkey, task, kind), item_requests(mkey, task, dfs[task], temps, seeds)))
    return blocks


# ----------------------------------------------------------------------------------------------------------- modes
def check():
    dfs = {k: load_csv(k) for k in CSV}
    print("== released data vs the paper's description ==")
    for task, df in dfs.items():
        d = PAPER_DESIGN[task]
        print(f"{task}: {len(df)} rows (paper n={d['n']}); DOIs unique: {df.doi.is_unique}; empty abstracts: "
              f"{int((df.abstract.str.strip() == '').sum())}; abstract chars mean {df.abstract.str.len().mean():.0f}, "
              f"max {df.abstract.str.len().max()}")
        print(f"  journals (paper: {d['journals']}): {df.journal.value_counts().to_dict()}")
        print(f"  years (paper: {d['years']}): {df.date.str[:4].value_counts().sort_index().to_dict()}")
    gt = truth_of("task1", dfs["task1"])
    print(f"  task1 Number_randomized median {np.median(gt):.0f} (IQR {np.percentile(gt, 25):.0f}-{np.percentile(gt, 75):.0f}); "
          f"paper 668 (300-1836); min {gt.min():.0f}, non-integer {int((gt % 1 != 0).sum())}")
    a_r, a_o = truth_of("task2", dfs["task2"])
    print(f"  task2 RCT share {a_r.mean() * 100:.1f}% (paper 46.8%), oncology share {a_o.mean() * 100:.1f}% (paper 26.9%)")
    print(f"  DOIs present in both tasks: {len(set(dfs['task1'].doi) & set(dfs['task2'].doi))}")

    print("\n== request bodies (paper Methods; openai-python 1.40.3 sends exactly these keys; harness posts them over raw HTTPS) ==")
    for task, df in dfs.items():
        ab = df.abstract.iloc[0]
        shown = body(MODELS["gpt-4o"], task, ab, 0.25)
        shown["messages"][1]["content"] = f"<abstract row 0: {len(ab)} chars, sha256 {sha(ab)[:16]}..., doi {df.doi.iloc[0]}>"
        print(f"{task}: {json.dumps(shown, ensure_ascii=False)}")
    try:
        import importlib.metadata as im
        local_openai = im.version("openai")
    except Exception:
        local_openai = "not installed"
    print(f"temperatures {TEMPS}; max_tokens {MAX_TOKENS}; no seed/top_p/n; models {list(MODELS.values())}; "
          f"repeats seed_idx {REPEAT_SEEDS} at T {REPEAT_TEMPS}; local openai package {local_openai} (unused; paper: 1.40.3)")

    print("\n== parser validation: our parser on the released raw replies vs the authors' parsed columns ==")
    total, n_all, fc_cols = 0, 0, []
    for task, df in dfs.items():
        for mkey in MODELS:
            for t in TEMPS:
                raws, fc = released_raw(df, task, mkey, t)
                if fc:
                    fc_cols.append(raw_column(task, mkey, t))
                mine = [parse(task, x) for x in raws]
                n_all += len(raws)
                if task == "task1":
                    theirs = released_parsed(df, task, mkey, t)
                    mm = sum((a is None) != bool(np.isnan(b)) or (a is not None and float(a) != b) for a, b in zip(mine, theirs))
                else:
                    r, o = released_parsed(df, task, mkey, t)
                    mm = sum((a is None) != bool(np.isnan(br)) or (a is not None and (float(a[0]) != br or float(a[1]) != bo))
                             for a, br, bo in zip(mine, r, o))
                total += mm
                if mm:
                    print(f"  {task} {mkey} T={TKEY[t]}: {mm} mismatches")
    print(f"  total mismatches: {total} over {n_all} released replies; float-cast raw columns undone: {fc_cols}")
    for task, df in dfs.items():
        for mkey in MODELS:
            raws = [x for t in TEMPS for x in released_raw(df, task, mkey, t)[0]]
            print(f"  unformatted shapes {task} {mkey} (all temperatures): {taxonomy(task, raws)}")

    print("\n== Tables 1-3 re-scored from the released raw replies with our parser and scorer ==")
    mine = rescore_released(dfs, "raw")
    mism = compare_tables(mine, "raw + our parser")
    theirs = rescore_released(dfs, "parsed")
    diff = max(abs((mine[mk][lab][tk][k] or 0) - (theirs[mk][lab][tk][k] or 0)) for mk in MODELS for lab in ("task1", "rct", "onc")
               for tk in TKEY.values() for k in (T1_KEYS if lab == "task1" else T2_KEYS))
    print(f"\nmismatches beyond rounding (ours vs paper): {len(mism)}")
    for m in mism:
        print("  ", m)
    print(f"max |our-parser route - authors'-parsed-columns route| over all table cells: {diff:.2e}")
    g = mine["gpt-4o"]["task1"]
    print(f"card repo_csv_recomputed: gpt-4o task1 formatted T=0.00 {g['0.00']['formatted_pct']:.2f} (card 98.69), "
          f"T=2.00 {g['2.00']['formatted_pct']:.2f} (card 89.16)")
    return {"rescored": mine, "mismatches": mism, "parser_mismatches": total}


def dry_run(cap):
    dfs = {k: load_csv(k) for k in CSV}
    blocks = build_requests(dfs)
    reqs = [r for _, rs in blocks for r in rs]
    keys = {(r["id"], r["seed_idx"]) for r in reqs}
    assert len(keys) == len(reqs), "duplicate (id, seed_idx)"
    print(f"{len(reqs)} requests in priority order: " + ", ".join(f"{m}/{t}/{k}={len(rs)}" for (m, t, k), rs in blocks))
    print(f"example id: {reqs[0]['id']} seed_idx {reqs[0]['seed_idx']} meta {json.dumps(reqs[0]['meta'])}")
    for mkey, model in MODELS.items():
        sub = [r for r in reqs if r["body"]["model"] == model]
        run_battery(sub, RUN, cap, dry_run=True, label=f"{CARD_ID} {model}")
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")
        how = "tiktoken o200k_base, +3 tokens per message +3 priming"
    except Exception:
        enc = None
        how = "chars/4 (tiktoken not installed)"
    cache = {}

    def ntok(text):
        if text not in cache:
            cache[text] = len(enc.encode(text)) if enc else len(text) / 4
        return cache[text]

    print(f"\ncost by priority block ({how}; output = max_tokens {MAX_TOKENS} per call):")
    cum, per_model, covered = 0.0, {}, []
    for (mkey, task, kind), rs in blocks:
        p = pricing_for(MODELS[mkey])
        tin = sum(ntok(m["content"]) + 3 for r in rs for m in r["body"]["messages"]) + 3 * len(rs)
        cost = tin / 1e6 * p["input"] + MAX_TOKENS * len(rs) / 1e6 * p["output"]
        cum += cost
        per_model[mkey] = per_model.get(mkey, 0.0) + cost
        if cum <= cap:
            covered.append(f"{mkey}/{task}/{kind}")
        print(f"  {mkey:12s} {task} {kind:8s} {len(rs):6d} calls  ~{tin / 1e6:5.2f}M in  ${cost:6.2f}   cumulative ${cum:6.2f}")
    print("per model: " + ", ".join(f"{k} ${v:.2f}" for k, v in per_model.items()) + f"; total ${cum:.2f}")
    print(f"cap ${cap:.0f} fully covers: {covered or 'nothing'}; the full decided design needs about ${cum:.0f}; "
          f"recommended cap for the full design: ${np.ceil(cum * 1.1 / 5) * 5:.0f} (10% margin)")
    return {"n_requests": len(reqs), "per_model": per_model, "total": cum}


def agreement(a, b):
    """a, b: parsed lists (None = unformatted). Share identical formatted values; a = re-run, b = reference."""
    n = len(a)
    both = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    ident = sum(x == y for x, y in both)
    return {"n": n, "n_both_formatted": len(both), "identical_given_both_formatted": (ident / len(both)) if both else None,
            "identical_overall": ident / n if n else None,
            "status_agreement": (sum((x is None) == (y is None) for x, y in zip(a, b)) / n) if n else None,
            "reference_formatted_only": sum(x is None and y is not None for x, y in zip(a, b)),
            "rerun_formatted_only": sum(x is not None and y is None for x, y in zip(a, b))}


def median_of(passes, keys):
    out = {}
    for k in keys:
        vals = [p[k] for p in passes.values() if p.get(k) is not None]
        out[k] = float(np.median(vals)) if vals else None
    return out


def judge(t1, n_items):
    """gpt-4o Task 1: t1[tkey] = {'median': {...}, 'n_items': int, 'complete': bool}. Returns (label, flags)."""
    missing = [tk for tk in TKEY.values() if tk not in t1 or t1[tk]["median"].get("formatted_pct") is None]
    if missing:
        return "미판정 (incomplete)", {"missing_temperatures": missing}
    fr = {tk: t1[tk]["median"]["formatted_pct"] for tk in TKEY.values()}
    mape_dev = {tk: (t1[tk]["median"]["mape_pct"] - PAPER["gpt-4o"]["task1"][tk][1]) if t1[tk]["median"]["mape_pct"] is not None else None
                for tk in fr}
    w10_dev = {tk: (t1[tk]["median"]["within10_pct"] - PAPER["gpt-4o"]["task1"][tk][2]) if t1[tk]["median"]["within10_pct"] is not None else None
               for tk in fr}
    drop = fr["0.00"] - fr["2.00"]
    onset = next((tk for t, tk in TKEY.items() if fr["0.00"] - fr[tk] >= 3), None)
    subset = {tk: t1[tk]["n_items"] for tk in fr} if not all(t1[tk]["complete"] for tk in fr) else None
    flags = {"formatted_ge97_for_T_le_1.50": bool(all(fr[TKEY[t]] >= 97 for t in TEMPS if t <= 1.5)),
             "drop_T2.00_vs_T0.00_points": round(drop, 2), "drop_ge3": bool(drop >= 3),
             "drop_onset_T": onset, "drop_starts_at_or_below_1.25": bool(onset is not None and float(onset) <= 1.25),
             "mape_within_2_at_every_T": bool(all(v is not None and abs(v) <= 2 for v in mape_dev.values())),
             "mape_dev_points": {k: (round(v, 2) if v is not None else None) for k, v in mape_dev.items()},
             "mape_max_abs_dev_points": round(max(abs(v) for v in mape_dev.values() if v is not None), 2),
             "within10_max_abs_dev_points": round(max(abs(v) for v in w10_dev.values() if v is not None), 2),
             "dead_T2.00_within_1_point_of_T0.00": bool(abs(drop) <= 1),
             "dead_formatted_below_95_at_T_le_1.00": bool(any(fr[TKEY[t]] < 95 for t in TEMPS if t <= 1.0)),
             "subset": subset}
    if flags["dead_T2.00_within_1_point_of_T0.00"] or flags["dead_formatted_below_95_at_T_le_1.00"]:
        label = "사망 (dead)"
    elif flags["formatted_ge97_for_T_le_1.50"] and flags["drop_ge3"] and flags["mape_within_2_at_every_T"] and not flags["drop_starts_at_or_below_1.25"]:
        label = "생존 (survived)"
    else:
        label = "부분 생존 (partial)"
    if subset:
        label += f" [subset: {min(subset.values())}/{n_items} abstracts]"
    return label, flags


def _json_default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return None if np.isnan(o) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def analyze():
    res = load_results(RUN)
    if not res:
        print(f"no archived calls in {RUN / 'calls.jsonl'}")
        return None
    dfs = {k: load_csv(k) for k in CSV if CSV[k].exists()}
    groups, truth = {}, {}
    for (rid, seed), r in res.items():
        m = r.get("meta") or {}
        if "task" not in m:
            continue
        key = (m["model_key"], m["task"], TKEY[float(m["temperature"])], int(seed))
        groups.setdefault(key, {})[int(m["row"])] = r
        truth[(m["task"], int(m["row"]))] = (m["doi"], m["abstract_sha256"], m["truth"])
    n_items = {task: (len(dfs[task]) if task in dfs else 1 + max(row for tk, row in truth if tk == task))
               for task in CSV if any(tk == task for tk, _ in truth)}
    released = {}
    for task, df in dfs.items():
        for mkey in MODELS:
            for t in TEMPS:
                raws, _ = released_raw(df, task, mkey, t)
                released[(task, mkey, TKEY[t])] = (raws, [parse(task, x) for x in raws])
    rng, boots = np.random.default_rng(0), {}

    def boot(n):
        if n not in boots:
            boots[n] = rng.integers(0, n, size=(N_BOOT, n))
        return boots[n]

    reex, paired, parsed_by_key, items, diag = {}, {}, {}, [], {"finish_reasons": {}, "null_replies": {}, "none_content": 0}
    for key in sorted(groups):
        mkey, task, tkey, seed = key
        g = groups[key]
        rows = sorted(g)
        texts, finishes = zip(*(reply_of(g[i]) for i in rows))
        parsed = [parse(task, x) for x in texts]
        parsed_by_key[key] = (rows, parsed)
        if task == "task1":
            tr = np.array([float(truth[(task, i)][2]) for i in rows])
        else:
            tr = (np.array([bool(truth[(task, i)][2][0]) for i in rows]), np.array([bool(truth[(task, i)][2][1]) for i in rows]))
        metrics = score(task, tr, parsed, boot(len(rows)))
        complete = len(rows) == n_items[task]
        for lab, m in metrics.items():
            m.update(n_items=len(rows), complete=complete, n_null_replies=int(sum(is_null_reply(x) for x in texts)),
                     n_none_content=int(sum(x is None for x in texts)),
                     finish_reasons={fr: int(sum(1 for x in finishes if x == fr)) for fr in set(finishes)})
            reex.setdefault(mkey, {}).setdefault(lab, {}).setdefault(tkey, {"passes": {}})["passes"][str(seed)] = m
        for fr_ in finishes:
            diag["finish_reasons"][str(fr_)] = diag["finish_reasons"].get(str(fr_), 0) + 1
        diag["none_content"] += int(sum(x is None for x in texts))
        rel = released.get((task, mkey, tkey))
        orig_parsed = [rel[1][i] for i in rows] if rel else None
        if rel:
            paired.setdefault(mkey, {}).setdefault(task, {}).setdefault(tkey, {})[str(seed)] = agreement(parsed, orig_parsed)
        with np.errstate(invalid="ignore", divide="ignore"):
            ape = (np.abs(tr - pred_arrays(task, parsed)) / tr) if task == "task1" else None
        for j, i in enumerate(rows):
            rec, p = g[i], parsed[j]
            doi, ab_sha, tv = truth[(task, i)]
            op = orig_parsed[j] if orig_parsed is not None else None
            items.append({
                "task": task, "model": MODELS[mkey], "temperature": tkey, "repeat": seed, "row": i, "doi": doi, "abstract_sha256": ab_sha,
                "truth": tv if task == "task1" else f"{tv[0]}|{tv[1]}",
                "reply": (texts[j] if texts[j] is not None else "").replace("\r", "\\r").replace("\n", "\\n"),
                "finish_reason": finishes[j], "parsed": "" if p is None else (p if task == "task1" else f"{p[0]}|{p[1]}"),
                "formatted": p is not None, "abs_pct_err": (round(float(ape[j]) * 100, 4) if task == "task1" and p is not None else ""),
                "within10": (bool(ape[j] < 0.1) if task == "task1" and p is not None else ""),
                "orig_reply": (rel[0][i].replace("\r", "\\r").replace("\n", "\\n") if rel else ""),
                "orig_parsed": "" if op is None else (op if task == "task1" else f"{op[0]}|{op[1]}"),
                "identical_to_orig": (p == op) if (p is not None and op is not None) else "",
                "model_served": rec.get("model_served"), "system_fingerprint": rec.get("system_fingerprint")})
    # medians over passes, run-to-run agreement between repeats
    for mkey in reex:
        for lab in reex[mkey]:
            keys = T1_KEYS if lab == "task1" else T2_KEYS
            for tkey, d in reex[mkey][lab].items():
                d["median"] = median_of(d["passes"], keys)
                d["n_passes"] = len(d["passes"])
                d["n_items"] = min(p["n_items"] for p in d["passes"].values())
                d["complete"] = all(p["complete"] for p in d["passes"].values())
    run_to_run = {}
    for (mkey, task, tkey, seed), (rows, parsed) in parsed_by_key.items():
        for (mk2, tk2, tkey2, seed2), (rows2, parsed2) in parsed_by_key.items():
            if (mk2, tk2, tkey2) == (mkey, task, tkey) and seed2 > seed:
                common = sorted(set(rows) & set(rows2))
                a = dict(zip(rows, parsed))
                b = dict(zip(rows2, parsed2))
                run_to_run.setdefault(mkey, {}).setdefault(task, {}).setdefault(tkey, {})[f"{seed}v{seed2}"] = \
                    agreement([a[i] for i in common], [b[i] for i in common])
    # judgment on gpt-4o Task 1
    t1 = reex.get("gpt-4o", {}).get("task1", {})
    label, flags = judge(t1, n_items.get("task1", 996))
    budget = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    served = sorted({r.get("model_served") for r in res.values() if r.get("model_served")})
    fps = {r.get("system_fingerprint") for r in res.values() if r.get("system_fingerprint")}
    fps_by_model = {mk: len({r.get("system_fingerprint") for r in res.values() if (r.get("model_served") or "").startswith(mk) and r.get("system_fingerprint")})
                    for mk in MODELS.values()}
    original = {mk: {lab: {tk: dict(zip(T1_KEYS if lab == "task1" else T2_KEYS, PAPER[mk][lab][tk])) for tk in TKEY.values()}
                     for lab in ("task1", "rct", "onc")} for mk in MODELS}
    rescored = rescore_released(dfs, "raw") if len(dfs) == 2 else None

    def med(mk, lab, tk, k):
        v = reex.get(mk, {}).get(lab, {}).get(tk, {}).get("median", {}).get(k)
        return "n/a" if v is None else f"{v:.1f}" if k.endswith("pct") else f"{v:.3f}"

    pair_t1 = paired.get("gpt-4o", {}).get("task1", {})
    ident = [d["0"]["identical_given_both_formatted"] for d in pair_t1.values() if "0" in d and d["0"]["identical_given_both_formatted"] is not None]
    note = (f"gpt-4o Task 1 formatted % (median over passes) T0.00 {med('gpt-4o', 'task1', '0.00', 'formatted_pct')} (paper 98.7), "
            f"T1.50 {med('gpt-4o', 'task1', '1.50', 'formatted_pct')} (98.7), T1.75 {med('gpt-4o', 'task1', '1.75', 'formatted_pct')} (95.6), "
            f"T2.00 {med('gpt-4o', 'task1', '2.00', 'formatted_pct')} (89.2); MAPE T0.00 {med('gpt-4o', 'task1', '0.00', 'mape_pct')} (1.7), "
            f"T2.00 {med('gpt-4o', 'task1', '2.00', 'mape_pct')} (1.0). gpt-4o Task 2 formatted % T2.00 {med('gpt-4o', 'rct', '2.00', 'formatted_pct')} (93.3), "
            f"RCT F1 T0.00 {med('gpt-4o', 'rct', '0.00', 'f1')} (0.956), oncology F1 T0.00 {med('gpt-4o', 'onc', '0.00', 'f1')} (0.969). "
            f"gpt-4o-mini Task 1 formatted % T0.00 {med('gpt-4o-mini', 'task1', '0.00', 'formatted_pct')} (99.1), T2.00 "
            f"{med('gpt-4o-mini', 'task1', '2.00', 'formatted_pct')} (90.2). Paired with the released replies (gpt-4o Task 1, pass 0): identical "
            f"formatted value for {min(ident) * 100:.1f}-{max(ident) * 100:.1f}% of abstracts formatted in both runs across temperatures. "
            if ident else "no paired comparison available. ") + f"Judgment flags: {json.dumps(flags, default=_json_default)}"
    frictions = [
        "the repository holds the analysis notebook and the per-item responses but not the API-calling script; the calls were rebuilt from the Methods (prompts verbatim, max_tokens 10, defaults otherwise; openai-python 1.40.3 sends exactly those keys)",
        "the raw -> parsed step is not in the notebook; the rules 'whole reply is ASCII digits' (Task 1) and 'ast.literal_eval gives two bools' (Task 2) were inferred and reproduce all released parsed values",
        "dataset description mismatch: Task 1 CSV = 996 abstracts from four journal labels (NEJM, Lancet, JAMA, BMJ), 2020-2023, vs the paper's seven journals and 2010-2022; Task 2 CSV = 899 rows (paper: 900), seven journals, 2010-2023",
        "five GPT-4o-mini Task 1 raw-reply columns were float-cast in the released CSV and about 90 raw cells per model are empty (most likely 'null' replies lost to pandas NA handling), so the original unformatted replies are only partly recoverable",
        "the abstracts are publisher-copyrighted PubMed abstracts; the public archive keeps doi + sha256 of the user message instead of the text (private archive keeps the full requests)",
        "gpt-4o-2024-05-13 is scheduled for shutdown on 2026-10-23 (card); the re-execution had to run before that date",
        f"{diag['finish_reasons'].get('length', 0)} of {len(items)} archived replies hit the 10-token limit (finish_reason 'length'); {diag['none_content']} had no message content",
    ]
    if budget.get("errors"):
        frictions.append(f"{budget['errors']} calls failed at the HTTP level and are not in the archive")
    if budget.get("stopped_at_cap"):
        frictions.append(f"the run stopped at the ${budget.get('cap_usd')} cap; blocks after the cut are missing (see per-temperature n_items)")
    meta = {"card_id": CARD_ID, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
            "target_paper": {"title": "The Impact of Temperature on Extracting Information From Clinical Trial Publications Using Large Language Models",
                             "repo": REPO_URL, "repo_commit": REPO_COMMIT,
                             "original_source": "Tables 1-3 (also re-scored from the released per-item responses in sample_size_gpt_responses_all.csv and rct_oncology_gpt_responses_all.csv)"},
            "generation": {"model_requested": list(MODELS.values()), "model_served": served, "n_fingerprints": len(fps),
                           "n_fingerprints_by_model": fps_by_model,
                           "parameters": f"system prompt verbatim from the Methods, user = abstract, temperature in {TEMPS}, max_tokens {MAX_TOKENS}, "
                                         "no other parameters (paper: API defaults; openai-python 1.40.3); raw HTTPS here",
                           "battery": f"{n_items.get('task1', 0)} Task 1 + {n_items.get('task2', 0)} Task 2 abstracts x 9 temperatures x 2 models, pass 0 paired "
                                      f"with the released replies, plus repeats seed_idx {REPEAT_SEEDS} at T {REPEAT_TEMPS}; {len(res)} archived calls"},
            "results": {"original_paper_tables": original, "original_rescored_from_released_replies": rescored, "reexecution": reex,
                        "paired_with_released": paired, "run_to_run": run_to_run, "judgment_flags": flags, "diagnostics": diag,
                        "cost_usd": round(budget.get("cost_usd", 0.0), 3), "calls": budget.get("calls", len(res)), "errors": budget.get("errors", 0),
                        "judgment": label,
                        "judged_by": "automatic rule per ANALYSIS_PLAN Sec. 1 as instantiated in the card (gpt-4o Task 1: formatted >= 97% for T <= 1.50, "
                                     "drop >= 3 points at T=2.00 vs 0.00, MAPE within 2 points of Table 1; median over passes); human double-coding pending",
                        "note": note},
            "reproducibility_frictions_observed": frictions}
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "result.json").write_text(json.dumps({"reexecution": reex, "paired_with_released": paired, "run_to_run": run_to_run,
                                                 "judgment": label, "judgment_flags": flags, "diagnostics": diag},
                                                indent=2, default=_json_default), encoding="utf-8")
    pd.DataFrame(items).to_csv(RUN / "items.csv", index=False, encoding="utf-8")
    (RUN.parent / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    for mkey in reex:
        for lab in reex[mkey]:
            print(f"\n{mkey} {lab} (median over passes; paper value in brackets)")
            for tkey in sorted(reex[mkey][lab]):
                d = reex[mkey][lab][tkey]
                p = PAPER[mkey][lab][tkey]
                if lab == "task1":
                    ci = d["passes"].get("0", {}).get("ci95", {}).get("formatted_pct", ["", ""])
                    print(f"  T={tkey} n={d['n_items']} passes={d['n_passes']}  formatted {med(mkey, lab, tkey, 'formatted_pct')} [{p[0]}] "
                          f"CI {ci}  MAPE {med(mkey, lab, tkey, 'mape_pct')} [{p[1]}]  within10 {med(mkey, lab, tkey, 'within10_pct')} [{p[2]}]  "
                          f"within1 {med(mkey, lab, tkey, 'within1_pct')} [{p[3]}]")
                else:
                    print(f"  T={tkey} n={d['n_items']} passes={d['n_passes']}  formatted {med(mkey, lab, tkey, 'formatted_pct')} [{p[0]}]  "
                          f"acc {med(mkey, lab, tkey, 'accuracy')} [{p[1]}]  prec {med(mkey, lab, tkey, 'precision')} [{p[2]}]  "
                          f"rec {med(mkey, lab, tkey, 'recall')} [{p[3]}]  F1 {med(mkey, lab, tkey, 'f1')} [{p[4]}]")
    for mkey in paired:
        for task in paired[mkey]:
            print(f"\npaired with released replies, {mkey} {task}, pass 0: " + "; ".join(
                f"T={tk} identical {d['0']['identical_given_both_formatted']:.3f} (both formatted n={d['0']['n_both_formatted']}), status agreement {d['0']['status_agreement']:.3f}"
                for tk, d in sorted(paired[mkey][task].items()) if "0" in d and d["0"]["identical_given_both_formatted"] is not None))
    print(f"\njudgment: {label} | served {served} fingerprints {len(fps)} | cost ${meta['results']['cost_usd']} | calls {meta['results']['calls']}")
    return meta


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--cap", type=float, default=CAP)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.check:
        check()
    if a.dry_run:
        dry_run(a.cap)
    if a.run:
        blocks = build_requests()
        run_battery([r for _, rs in blocks for r in rs], RUN, a.cap, workers=a.workers, label=CARD_ID)
    if a.analyze:
        analyze()


if __name__ == "__main__":
    main()
