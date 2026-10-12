"""Card W4396768794 - Assessing DxGPT: Diagnosing Rare Diseases with Various Large Language Models
(do Olmo et al., Foundation 29, medRxiv 10.1101/2024.05.08.24307062; repo foundation29org/dxgpt_testing @ c7abe55).

Claim re-measured (Table 3, RAMEDIS, 200 real cases, 'GPT-4 Turbo 0409' = gpt-4-turbo-2024-04-09):
  Strict Accuracy (P1) 54.04 %  and  Top-5 Accuracy (P1+P5) 68.69 %
  = P1 107, P2-P5 29, P0 62 over 198 scored rows (2 of 200 rows are dropped by the paper's counting, see below).

Two-track design (card decisions_2026_09_18). The original judge, GPT-4-0613 behind the Azure deployment
'nav29', is dead, so every re-judged number is produced by ONE substitute judge, gpt-4o-2024-05-13:
  track 1  the ARCHIVED gpt-4-turbo-0409 diagnoses (repo data/diagnoses_RAMEDIS_gpt4turbo0409.csv) re-judged
           -> track 1 minus Table 3 = judge drift (same diagnoses, different judge)
  track 2  NEW diagnoses from gpt-4-turbo-2024-04-09 (200 cases x 3 repeats) judged the same way
           -> track 2 minus track 1 = generator drift (same judge, different generations)
The judgment (card 'judgment' + ANALYSIS_PLAN section 1) rests on the judge-matched comparison, track 2 vs
track 1; the comparison with the published 54.04 is secondary. PUMCH and the synthetic set are not run.

Stages
  python adapters/dxgpt_W4396768794.py --prepare   # public downloads only: RareBench RAMEDIS.jsonl + mappings, hp.obo
  python adapters/dxgpt_W4396768794.py --check     # rebuild prompts, reproduce Table 3 from the archived verdicts; no API
  python adapters/dxgpt_W4396768794.py --dry-run   # request lists + battery cost estimate per stage; no API
  python adapters/dxgpt_W4396768794.py --run       # generation, cap GEN_CAP  -> runs/W4396768794/baseline_alive/
  python adapters/dxgpt_W4396768794.py --judge [--track 1|2|both]   # -> judge_track1/ (independent), judge_track2/
  python adapters/dxgpt_W4396768794.py --analyze   # P1/P5/P0 + bootstrap CIs, result.json, per_case.csv, run_meta.json

Protocol (generation), copied from src/batch_diagnosis_v2.py: one user message = PROMPT_TEMPLATE with
{description} = the Python list repr of the case's HPO term names (langchain f-string formatting of the
list object); ChatOpenAI(model_name='gpt-4-turbo-2024-04-09', temperature=0, max_tokens=800); no system
message, no seed (langchain also sent n=1 and stream=false, which do not change the completion). The three
repeats (seed_idx 0..2) are identical requests; the API 'seed' parameter is NOT set because the original did
not set it, so the repeats measure API nondeterminism at temperature 0. Requests are ordered seed-major so a
run stopped at the cap leaves complete repeats. Served model and system_fingerprint are archived per call.

Protocol (judge), copied from src/diagnoses_analisis.py get_scores(): one user message = PROMPT_TEMPLATE with
{gt} = the GT CELL AS STORED in the diagnoses CSV, i.e. the Python list repr of the Orphanet preferred names
(brackets and quotes included, e.g. "['Vitamin B12-unresponsive methylmalonic acidemia']"), and
{predictions} = the full diagnosis text (the repo passes row[1] verbatim; its <top5> extraction only applies
to the 'improved' prompt). AzureChatOpenAI(deployment 'nav29', temperature=0, max_tokens=800). Substitute:
gpt-4o-2024-05-13, temperature 0, max_tokens 800 (kept although the answer is one label). Both templates are
hard-coded below and verified byte-for-byte against the repo sources with ast before any request is built
(the repo modules cannot be imported: they call HF, Orphanet and the LLM APIs at import time). The paper's
appendix prints the prompts with cosmetic differences ('hypothetical' vs the code's 'hypotethical', quoting
of "\\n\\n Symptoms"); the code version, which is what was actually sent, is used.

Assumptions and findings
* Archived CSV columns: data/diagnoses_RAMEDIS_gpt4turbo0409.csv has 'GT' (list repr of the Orphanet names
  the authors resolved through api.orphacode.org for the ORPHA codes of the case; reused here, NO Orphanet
  call) and 'Diagnosis 1' (full model text; 200 rows in HF file order). data/scores_RAMEDIS_gpt4turbo0409.csv
  has 'GT' (identical) and 'Score' (raw judge output). The git blobs are LF; the Windows checkout
  (core.autocrlf) shows CRLF, so both files are normalised to LF before use.
* P1/P5/P0 counting re-implemented from src/dashboard_scores.py get_stats_for_df: P1 = rows whose Score is
  exactly 'P1'; P5 = rows in {'P2','P3','P4','P5'} (the judge sometimes returned a rank although the prompt
  asks for P1/P5/P0); P0 = exactly 'P0'; every other value drops out of the denominator. In the archive two
  rows carry the label with literal quotes ('"P3"', '"P1"'), hence 198. Strict = P1/n, Top-5 = (P1+P5)/n.
* The 198 denominator is reproduced with that rule ('repo' counting). For the substitute judge a lenient
  parser (strip quotes/whitespace, first P0..P5 token, P2-P5 -> P5) is primary, and the original verdicts
  are also re-counted leniently (200 rows: 108/30/62 = 54.00/69.00) so that judge-matched comparisons use
  one parser on both sides. Both countings are reported.
* RAMEDIS cases: HF dataset chenxz/RareBench, config RAMEDIS, split test = data/RAMEDIS.jsonl inside
  data.zip (RareBench.py yields the file order, no shuffling; datasets 4.x no longer runs loading scripts,
  so the JSONL is read directly); the first 200 of its records (the repo's df[:200]). Alignment with the
  archive is validated in --check by mapping each record's ORPHA codes with RareBench's
  mapping/disease_mapping.json and comparing with the archived GT string.
* HPO id -> name: the repo calls pyhpo.Ontology.get_hpo_object(id).name with whatever hpo3 was installed;
  in April 2024 that was hpo3 1.2.0 (PyPI 2024-03-31; next release 2024-06-16), whose Rust core carries
  'Update to HPO 2024-03-09' (hpo crate 0.8.2), i.e. the HPO release v2024-03-06. --prepare fetches that
  release's hp.obo; alt_ids resolve to their primary term; ids still missing fall back to RareBench's
  mapping/phenotype_mapping.json (counts printed). The release choice is validated in --check by the share
  of mapped names echoed verbatim in the archived diagnosis text of the same case.
* Licence: HF chenxz/RareBench carries the license tag apache-2.0 (dataset card and /api/datasets, last
  modified 2024-12-12; the card asks for the Chen et al. 2024, arXiv 2402.06341 citation and states no
  further terms); GitHub chenxz1111/RareBench has an Apache-2.0 LICENSE; foundation29org/dxgpt_testing is
  MIT. Apache-2.0 permits redistribution with attribution, so the full request/response archive
  (calls.jsonl, which contains the HPO term lists) keeps the item text; RAMEDIS cases are published case
  reports. Notice and citation are recorded in run_meta.json. Should this reading be overruled, per_case.csv
  plus the case_sha256 in every request's meta support an id+hash archive instead.
* Empty ground truth: 13 of the 200 cases (rows 15, 20, 67, 69, 94, 120, 125, 146, 157, 159, 161, 179, 196)
  carry only OMIM/CCRD codes, so the authors' ORPHA-only mapping produced GT = '[]'; the original judge
  scored all 13 as P0 and the paper kept them in the denominator. They are kept identically here (they
  cap Strict/Top-5 at 93.5 % for every judge) and are listed by --check.
* Validation results of --check (2026-09-18): Table 3 reproduced exactly (P1 107, P2-P5 29, P0 62, n 198;
  excluded rows 12 '"P3"' and 81 '"P1"'); 200/200 records align with the archive (ORPHA count and
  disease_mapping names); 1,994 HPO ids, 1,988 primary + 6 via alt_id, none unmapped; 99 % of the mapped
  names are echoed verbatim by the archived diagnoses (no case without an echo), while 47/1,994 names differ
  from RareBench's own mapping, so the HPO release choice is confirmed as the one the authors used.
* Cost (--dry-run 2026-09-18): battery upper bounds (max_tokens 800 charged per call) $15.59 generation,
  $3.10 judge track 1, $9.30 judge track 2; refined estimate (archived mean output 496 tokens, ~3 judge
  output tokens) $10.11 + $0.71 + $2.12 = $12.94, in line with the card's $16. Caps 18/4/8 = $30 per paper.
"""
import argparse, ast, hashlib, io, json, re, sys, urllib.request, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import estimate, load_results, pricing_for, run_battery  # noqa: E402

CARD = "W4396768794"
HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / CARD / "foundation29org__dxgpt_testing"
DIAG_CSV = REPO / "data" / "diagnoses_RAMEDIS_gpt4turbo0409.csv"
SCORES_CSV = REPO / "data" / "scores_RAMEDIS_gpt4turbo0409.csv"
GEN_SRC = REPO / "src" / "batch_diagnosis_v2.py"
JUDGE_SRC = REPO / "src" / "diagnoses_analisis.py"
RUNROOT = HALF / "runs" / CARD
INPUTS = RUNROOT / "inputs"
GEN_RUN, J1_RUN, J2_RUN = RUNROOT / "baseline_alive", RUNROOT / "judge_track1", RUNROOT / "judge_track2"

GEN_MODEL, JUDGE_MODEL = "gpt-4-turbo-2024-04-09", "gpt-4o-2024-05-13"
N_CASES, N_SEEDS, BOOT = 200, 3, 1000
GEN_CAP, J1_CAP, J2_CAP = 18.0, 4.0, 8.0      # per-stage caps (USD), $30 per paper; see --dry-run for the estimates

HF_BASE = "https://huggingface.co/datasets/chenxz/RareBench/resolve/main/"
HPO_RELEASE = "v2024-03-06"
DOWNLOADS = {
    "data.zip": HF_BASE + "data.zip",
    "phenotype_mapping.json": HF_BASE + "mapping/phenotype_mapping.json",
    "disease_mapping.json": HF_BASE + "mapping/disease_mapping.json",
    "hp.obo": f"https://github.com/obophenotype/human-phenotype-ontology/releases/download/{HPO_RELEASE}/hp.obo",
}
RAMEDIS_JSONL = INPUTS / "RAMEDIS.jsonl"
TABLE3 = {"P1": 107, "P5": 29, "P0": 62, "n_scored": 198, "strict": 54.04, "top5": 68.69}

# src/batch_diagnosis_v2.py PROMPT_TEMPLATE (module level), verbatim; the \n escapes are real newlines there as well.
PROMPT_TEMPLATE = "Behave like a hypotethical doctor who has to do a diagnosis for a patient. Give me a list of potential diseases with a short description. Shows for each potential diseases always with '\n\n+' and a number, starting with '\n\n+1', for example '\n\n+23.' (never return \n\n-), the name of the disease and finish with ':'. Dont return '\n\n-', return '\n\n+' instead. You have to indicate which symptoms the patient has in common with the proposed disease and which symptoms the patient does not have in common. The text is \n Symptoms:{description}"

# src/diagnoses_analisis.py get_scores() PROMPT_TEMPLATE, verbatim. The indentation, the trailing spaces after
# 'classification: ', '"P1".  ' and '{predictions} ' and the final newline + 4 spaces are part of what the judge saw;
# they are written as explicit escapes (one physical line per template line) so editors cannot strip them silently.
JUDGE_TEMPLATE = (
    "Behave like a medical doctor reviewing patient diagnoses. You will be given a Ground Truth diagnosis (GT) and 5 "
    "Predicted diagnoses (P1-P5). Compare the GT to the predictions and return a classification: \n"
    "\n"
    "    If GT exactly matches P1, return \"P1\".  \n"
    "    If GT is contained within or is a broader term for P1-P5, return \"P5\".\n"
    "    If GT does not match any of P1-P5, return \"P0\".\n"
    "\n"
    "    The GT may be a more general diagnosis, while predictions may include specific conditions. Broadly match GT to "
    "any prediction it reasonably encompasses.\n"
    "    ----------------------------------------\n"
    "    The text is:\n"
    "\n"
    "    GT: {gt}\n"
    "\n"
    "    Predictions:\n"
    "\n"
    "    {predictions} \n"
    "    ----------------------------------------\n"
    "    Return either \"P1\", \"P5\", or \"P0\". Do not return any other text.\n"
    "    "
)

P5_SET = {"P2", "P3", "P4", "P5"}
LABEL_RE = re.compile(r"\bP([0-5])\b")
CODE = {"P1": 2, "P5": 1, "P0": 0}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------------- repo artefacts
def repo_literal(path, name):
    """String literal assigned to `name` in a repo source file (ast; the modules must not be imported)."""
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return node.value.value
    raise KeyError(f"{name} not found in {path}")


def verify_prompts():
    for label, mine, src in (("generation", PROMPT_TEMPLATE, GEN_SRC), ("judge", JUDGE_TEMPLATE, JUDGE_SRC)):
        theirs = repo_literal(src, "PROMPT_TEMPLATE")
        if theirs != mine:
            raise SystemExit(f"{label} prompt in this adapter differs from {src} - refusing to build requests")


def read_repo_csv(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")     # git blob is LF; autocrlf checkout shows CRLF
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)


def archived_rows():
    d, s = read_repo_csv(DIAG_CSV), read_repo_csv(SCORES_CSV)
    if list(d.columns) != ["GT", "Diagnosis 1"] or list(s.columns) != ["GT", "Score"]:
        raise SystemExit(f"unexpected columns: {list(d.columns)} / {list(s.columns)}")
    mism = int((d.GT != s.GT).sum())
    if len(d) != N_CASES or len(s) != N_CASES or mism:
        raise SystemExit(f"archive misaligned: {len(d)} diagnoses, {len(s)} scores, {mism} GT mismatches")
    return [{"id": f"RAMEDIS_{i:03d}", "row": i, "gt": d.GT.iloc[i], "orig_diagnosis": d["Diagnosis 1"].iloc[i],
             "orig_score": s.Score.iloc[i]} for i in range(N_CASES)]


# ----------------------------------------------------------------------------- scoring
def bucket_repo(raw):
    """src/dashboard_scores.py get_stats_for_df: exact 'P1'; P2..P5 -> P5; exact 'P0'; anything else excluded."""
    if raw == "P1":
        return "P1"
    if raw in P5_SET:
        return "P5"
    if raw == "P0":
        return "P0"
    return None


def bucket_lenient(raw):
    """First P0..P5 token after ignoring quotes/whitespace/punctuation; P2..P5 count as P5 (repo convention)."""
    if raw is None:
        return None
    m = LABEL_RE.search(str(raw))
    if not m:
        return None
    return {"0": "P0", "1": "P1"}.get(m.group(1), "P5")


def tally(buckets):
    c = Counter(b for b in buckets if b in CODE)
    n = sum(c.values())
    return {"P1": c["P1"], "P5": c["P5"], "P0": c["P0"], "n_scored": n, "n_unscored": len(buckets) - n,
            "strict": 100 * c["P1"] / n if n else None, "top5": 100 * (c["P1"] + c["P5"]) / n if n else None}


def _pct(v):
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else None


def boot_ci(buckets, rng, draws=BOOT):
    """Bootstrap over cases: resample the 200 case slots with replacement; unscored slots stay excluded."""
    arr = np.array([CODE.get(b, -1) for b in buckets])
    strict, top5 = [], []
    for _ in range(draws):
        s = arr[rng.integers(0, len(arr), len(arr))]
        s = s[s >= 0]
        if len(s):
            strict.append(100 * np.mean(s == 2))
            top5.append(100 * np.mean(s >= 1))
    return {"strict_ci95": _pct(strict), "top5_ci95": _pct(top5)}


def boot_median_ci(bucket_lists, rng, draws=BOOT):
    """Case bootstrap of the median-over-repeats statistic (seeds x cases matrix, same resampled cases per seed)."""
    mats = np.array([[CODE.get(b, -1) for b in bl] for bl in bucket_lists])
    n = mats.shape[1]
    s_vals, t_vals = [], []
    for _ in range(draws):
        sub = mats[:, rng.integers(0, n, n)]
        per_s, per_t = [], []
        for row in sub:
            v = row[row >= 0]
            if len(v):
                per_s.append(100 * np.mean(v == 2))
                per_t.append(100 * np.mean(v >= 1))
        if per_s:
            s_vals.append(np.median(per_s))
            t_vals.append(np.median(per_t))
    return _pct(s_vals), _pct(t_vals)


def agreement(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x and y]
    n = len(pairs)
    conf = Counter(f"{x}->{y}" for x, y in pairs)
    po = sum(x == y for x, y in pairs) / n if n else None
    pe = sum((sum(x == c for x, _ in pairs) / n) * (sum(y == c for _, y in pairs) / n) for c in CODE) if n else None
    kappa = (po - pe) / (1 - pe) if n and pe < 1 else None
    return {"n_pairs": n, "percent_agreement": po, "cohen_kappa": kappa, "confusion_original->substitute": dict(conf)}


def content(r):
    try:
        return r["response"]["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None


# ----------------------------------------------------------------------------- inputs (public downloads)
def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "halflife-harness/1.0 (research re-execution)"})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        f.write(r.read())


def prepare():
    INPUTS.mkdir(parents=True, exist_ok=True)
    manifest = {"fetched_utc": now(), "files": {}}
    for name, url in DOWNLOADS.items():
        dest = INPUTS / name
        if not dest.exists():
            print(f"downloading {url}", flush=True)
            download(url, dest)
        manifest["files"][name] = {"url": url, "bytes": dest.stat().st_size, "sha256": sha_file(dest)}
    if not RAMEDIS_JSONL.exists():
        with zipfile.ZipFile(INPUTS / "data.zip") as z:
            member = next(n for n in z.namelist() if n.endswith("RAMEDIS.jsonl"))
            RAMEDIS_JSONL.write_bytes(z.read(member))
            manifest["data_zip_members"] = z.namelist()
    manifest["files"]["RAMEDIS.jsonl"] = {"from": "data.zip", "bytes": RAMEDIS_JSONL.stat().st_size, "sha256": sha_file(RAMEDIS_JSONL)}
    (INPUTS / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest["files"], indent=1))


def hpo_names():
    """id -> name from hp.obo, plus alt_id -> primary id (small re-implementation of the pyhpo lookup)."""
    names, alt = {}, {}
    for stanza in (INPUTS / "hp.obo").read_text(encoding="utf-8").split("\n[Term]\n")[1:]:
        tid = name = None
        alts = []
        for line in stanza.split("\n"):
            if line.startswith("["):
                break
            if line.startswith("id: "):
                tid = line[4:].strip()
            elif line.startswith("name: "):
                name = line[6:].strip()
            elif line.startswith("alt_id: "):
                alts.append(line[8:].strip())
        if tid and name:
            names[tid] = name
            for a in alts:
                alt[a] = tid
    return names, alt


def map_name(v):
    """Name string out of a RareBench mapping value (str, or dict/list wrapping one)."""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        for k in ("name", "Name", "en", "label"):
            if isinstance(v.get(k), str):
                return v[k]
        return next((x for x in v.values() if isinstance(x, str)), json.dumps(v, ensure_ascii=False))
    if isinstance(v, list) and v:
        return map_name(v[0])
    return str(v)


def ramedis_records():
    if not RAMEDIS_JSONL.exists():
        raise SystemExit(f"{RAMEDIS_JSONL} missing - run --prepare first")
    with open(RAMEDIS_JSONL, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def cases(rows=None):
    """First N_CASES RAMEDIS records with HPO names mapped as the repo did; archived GT/diagnosis/score attached."""
    rows = rows or archived_rows()
    names, alt = hpo_names()
    fallback = json.loads((INPUTS / "phenotype_mapping.json").read_text(encoding="utf-8"))
    recs = ramedis_records()
    stats = Counter()
    out = []
    for i, rec in enumerate(recs[:N_CASES]):
        terms = []
        for h in rec["Phenotype"]:
            stats["hpo_ids"] += 1
            if h in names and not names[h].startswith("obsolete "):
                terms.append(names[h]); stats["primary"] += 1
            elif h in alt:
                terms.append(names[alt[h]]); stats["alt_id"] += 1
            elif h in fallback:
                terms.append(map_name(fallback[h])); stats["fallback_rarebench_mapping"] += 1
            else:
                terms.append(h); stats["unmapped_kept_as_id"] += 1
        out.append({**rows[i], "hpo_ids": list(rec["Phenotype"]), "terms": terms, "codes": list(rec.get("RareDisease") or []),
                    "case_sha256": hashlib.sha256(json.dumps(rec["Phenotype"]).encode("utf-8")).hexdigest()})
    return out, dict(stats), len(recs)


# ----------------------------------------------------------------------------- prompts and requests
def gen_prompt(terms):
    return PROMPT_TEMPLATE.format(description=terms)      # str.format of a list == its repr, as langchain did


def judge_prompt(gt, predictions):
    return JUDGE_TEMPLATE.format(gt=gt, predictions=predictions)


def judge_body(gt, predictions):
    return {"model": JUDGE_MODEL, "messages": [{"role": "user", "content": judge_prompt(gt, predictions)}],
            "temperature": 0, "max_tokens": 800}


def gen_requests(cs):
    return [{"id": c["id"], "seed_idx": s,
             "meta": {"row": c["row"], "gt": c["gt"], "case_sha256": c["case_sha256"], "n_hpo": len(c["hpo_ids"])},
             "body": {"model": GEN_MODEL, "messages": [{"role": "user", "content": gen_prompt(c["terms"])}],
                      "temperature": 0, "max_tokens": 800}}
            for s in range(N_SEEDS) for c in cs]


def judge_requests_track1(rows):
    return [{"id": r["id"], "seed_idx": 0, "meta": {"track": 1, "row": r["row"], "gt": r["gt"], "orig_score": r["orig_score"]},
             "body": judge_body(r["gt"], r["orig_diagnosis"])} for r in rows]


def judge_requests_track2(rows):
    res = load_results(GEN_RUN)
    reqs, missing = [], 0
    for s in range(N_SEEDS):
        for r in rows:
            g = res.get((r["id"], s))
            text = content(g)
            if text is None:
                missing += 1
                continue
            reqs.append({"id": r["id"], "seed_idx": s,
                         "meta": {"track": 2, "row": r["row"], "gt": r["gt"], "generation_sha_response": g.get("sha_response")},
                         "body": judge_body(r["gt"], text)})
    return reqs, missing


# ----------------------------------------------------------------------------- stages
def _norm(x):
    return re.sub(r"\s+", " ", str(x)).strip().lower() if x is not None else None


def check():
    verify_prompts()
    print("prompts: generation and judge templates identical to the repo sources (ast comparison)")
    rows = archived_rows()
    n_err = sum(r["orig_diagnosis"].strip() == "ERROR" for r in rows)
    n_empty = [r["row"] for r in rows if r["gt"].strip() in ("[]", "")]
    lens = [len(r["orig_diagnosis"]) for r in rows]
    print(f"archive: {len(rows)} diagnoses rows + {len(rows)} score rows, GT columns aligned; 'ERROR' diagnoses {n_err}; "
          f"diagnosis text mean {np.mean(lens):.0f} chars (max {max(lens)}); rows with EMPTY GT '[]' (case without ORPHA "
          f"code, judged anyway by the paper): {len(n_empty)} {n_empty[:20]}; their original verdicts: "
          f"{dict(Counter(r['orig_score'] for r in rows if r['row'] in n_empty))}")
    raw = [r["orig_score"] for r in rows]
    print("raw judge outputs:", dict(Counter(raw)))
    rep = tally([bucket_repo(x) for x in raw])
    excluded = [(r["row"], r["orig_score"]) for r in rows if bucket_repo(r["orig_score"]) is None]
    match = all(rep[k] == TABLE3[k] for k in ("P1", "P5", "P0", "n_scored")) and \
        round(rep["strict"], 2) == TABLE3["strict"] and round(rep["top5"], 2) == TABLE3["top5"]
    print(f"Table 3 reproduction (repo counting): P1 {rep['P1']} P2-P5 {rep['P5']} P0 {rep['P0']} n {rep['n_scored']} -> "
          f"strict {rep['strict']:.2f} (paper {TABLE3['strict']}), top-5 {rep['top5']:.2f} (paper {TABLE3['top5']}) "
          f"{'MATCH' if match else 'MISMATCH'}; rows excluded by the repo counting: {excluded}")
    len_ = tally([bucket_lenient(x) for x in raw])
    print(f"same verdicts, lenient parser: P1 {len_['P1']} P5 {len_['P5']} P0 {len_['P0']} n {len_['n_scored']} -> "
          f"strict {len_['strict']:.2f}, top-5 {len_['top5']:.2f}")
    if not RAMEDIS_JSONL.exists():
        print(f"inputs missing under {INPUTS} - run --prepare to build the generation prompts")
        return
    cs, stats, n_total = cases(rows)
    print(f"RAMEDIS.jsonl: {n_total} records, first {len(cs)} used; HPO mapping ({HPO_RELEASE}): {stats}")
    dm = json.loads((INPUTS / "disease_mapping.json").read_text(encoding="utf-8"))
    n_count = n_name = 0
    mism = []
    for c in cs:
        orpha = [x for x in c["codes"] if str(x).startswith("ORPHA")]
        try:
            gt_list = ast.literal_eval(c["gt"])
        except Exception:
            gt_list = None
        rb = [map_name(dm[x]) if x in dm else None for x in orpha]
        if gt_list is not None and len(gt_list) == len(orpha):
            n_count += 1
        # RareBench joins synonyms with '/', so an archived Orphanet name counts as matched if it equals any part
        if gt_list is not None and len(gt_list) == len(rb) and \
                all(_norm(g) in [_norm(p) for p in str(r).split("/")] for g, r in zip(gt_list, rb)):
            n_name += 1
        else:
            mism.append((c["row"], gt_list, rb))
    print(f"alignment archive <-> HF records: ORPHA-code count matches GT list length {n_count}/{len(cs)}; "
          f"RareBench disease_mapping names == archived GT names {n_name}/{len(cs)}")
    for m in mism[:5]:
        print("   name mismatch:", m)
    shares = [np.mean([t.lower() in c["orig_diagnosis"].lower() for t in c["terms"]]) if c["terms"] else 0 for c in cs]
    print(f"HPO names echoed verbatim in the archived diagnosis of the same case: mean share {np.mean(shares):.2f}, "
          f"cases with no echo {sum(s == 0 for s in shares)}/{len(cs)}")
    fb = json.loads((INPUTS / "phenotype_mapping.json").read_text(encoding="utf-8"))
    pairs = [(h, t) for c in cs for h, t in zip(c["hpo_ids"], c["terms"]) if h in fb]
    diff = [(h, t, map_name(fb[h])) for h, t in pairs if map_name(fb[h]) != t]
    print(f"names differing between hp.obo {HPO_RELEASE} and RareBench phenotype_mapping.json: {len(diff)}/{len(pairs)}"
          + (f"; e.g. {diff[:3]}" if diff else ""))
    g, j1 = gen_requests(cs), judge_requests_track1(rows)
    print(f"request lists: generation {len(g)} ({len(cs)} cases x {N_SEEDS} repeats, {GEN_MODEL}), judge track 1 {len(j1)} "
          f"({JUDGE_MODEL}); mean prompt chars generation {np.mean([len(r['body']['messages'][0]['content']) for r in g]):.0f}, "
          f"judge {np.mean([len(r['body']['messages'][0]['content']) for r in j1]):.0f}")
    print("generation prompt, row 0:", repr(g[0]["body"]["messages"][0]["content"]))
    print("judge prompt, row 0 (first 700 chars):", repr(j1[0]["body"]["messages"][0]["content"][:700]))


def dry_run():
    verify_prompts()
    rows = archived_rows()
    cs, _, _ = cases(rows)
    g = gen_requests(cs)
    run_battery(g, GEN_RUN, GEN_CAP, dry_run=True, label=f"{CARD} generation {GEN_MODEL}")
    j1 = judge_requests_track1(rows)
    run_battery(j1, J1_RUN, J1_CAP, dry_run=True, label=f"{CARD} judge track 1 {JUDGE_MODEL}")
    j2, missing = judge_requests_track2(rows)
    if j2:
        run_battery(j2, J2_RUN, J2_CAP, dry_run=True, label=f"{CARD} judge track 2 {JUDGE_MODEL} ({missing} generations missing)")
    else:
        j2 = [{"id": c["id"], "seed_idx": s, "meta": {}, "body": judge_body(c["gt"], c["orig_diagnosis"])}
              for s in range(N_SEEDS) for c in cs]
        run_battery(j2, J2_RUN, J2_CAP, dry_run=True,
                    label=f"{CARD} judge track 2 {JUDGE_MODEL} (projected with the archived texts; generation not run yet)")
    pg, pj = pricing_for(GEN_MODEL), pricing_for(JUDGE_MODEL)
    out_tok = np.mean([len(r["orig_diagnosis"]) for r in rows]) / 4
    ref_g = estimate(g)[0] / 1e6 * pg["input"] + len(g) * out_tok / 1e6 * pg["output"]
    ref_1 = estimate(j1)[0] / 1e6 * pj["input"] + len(j1) * 3 / 1e6 * pj["output"]
    ref_2 = estimate(j2)[0] / 1e6 * pj["input"] + len(j2) * 3 / 1e6 * pj["output"]
    print(f"refined estimate (generation output = archived mean {out_tok:.0f} tokens, judge output ~3 tokens): "
          f"generation ${ref_g:.2f}, judge track 1 ${ref_1:.2f}, judge track 2 ${ref_2:.2f}, total ${ref_g + ref_1 + ref_2:.2f}")
    print(f"caps in this file: generation ${GEN_CAP}, judge track 1 ${J1_CAP}, judge track 2 ${J2_CAP} "
          f"(per-paper ${GEN_CAP + J1_CAP + J2_CAP}); the battery lines above charge max_tokens=800 per call (upper bound)")


def run():
    verify_prompts()
    cs, _, _ = cases()
    run_battery(gen_requests(cs), GEN_RUN, GEN_CAP, workers=4, label=f"{CARD} generation")


def judge(track):
    verify_prompts()
    rows = archived_rows()
    if track in ("1", "both"):
        run_battery(judge_requests_track1(rows), J1_RUN, J1_CAP, workers=4, label=f"{CARD} judge track 1")
    if track in ("2", "both"):
        j2, missing = judge_requests_track2(rows)
        if not j2:
            print(f"track 2: no generation results under {GEN_RUN} - run --run first (track 1 is independent)")
            return
        if missing:
            print(f"track 2: {missing} of {N_CASES * N_SEEDS} generations missing; judging the rest")
        run_battery(j2, J2_RUN, J2_CAP, workers=4, label=f"{CARD} judge track 2")


def _served(res):
    return {"models": sorted({r.get("model_served") for r in res.values() if r.get("model_served")}),
            "n_fingerprints": len({r.get("system_fingerprint") for r in res.values() if r.get("system_fingerprint")})}


def _budget(d):
    p = d / "budget.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _inside(x, ci):
    return bool(ci and x is not None and ci[0] <= x <= ci[1])


def analyze():
    verify_prompts()
    rows = archived_rows()
    rng = np.random.default_rng(0)
    raw = [r["orig_score"] for r in rows]
    b_repo, b_len = [bucket_repo(x) for x in raw], [bucket_lenient(x) for x in raw]
    orig_repo = {**tally(b_repo), **boot_ci(b_repo, rng), "label": "original judge GPT-4-0613, repo counting (Table 3)"}
    orig_len = {**tally(b_len), **boot_ci(b_len, rng), "label": "original judge GPT-4-0613, lenient parser"}

    res1 = load_results(J1_RUN)
    t1 = None
    b1 = [bucket_lenient(content(res1.get((r["id"], 0)))) for r in rows]
    if res1:
        raw1 = [content(res1.get((r["id"], 0))) for r in rows]
        t1 = {**tally(b1), **boot_ci(b1, rng), "label": "track 1: archived diagnoses, substitute judge",
              "repo_counting": tally([bucket_repo((x or "").strip()) for x in raw1]),
              "n_calls": len(res1), "n_missing": sum(1 for r in rows if (r["id"], 0) not in res1),
              "raw_outputs": dict(Counter(raw1)) if len(set(raw1)) <= 12 else {"distinct": len(set(raw1))},
              "agreement_with_original_judge": agreement(b_len, b1), "served": _served(res1)}

    res2 = load_results(J2_RUN)
    t2 = None
    b2 = {s: [bucket_lenient(content(res2.get((r["id"], s)))) for r in rows] for s in range(N_SEEDS)}
    if res2:
        per_seed = {}
        for s in range(N_SEEDS):
            per_seed[str(s)] = {**tally(b2[s]), **boot_ci(b2[s], rng), "n_missing": sum(1 for r in rows if (r["id"], s) not in res2)}
        done = [s for s in range(N_SEEDS) if per_seed[str(s)]["n_scored"]]
        med_s = float(np.median([per_seed[str(s)]["strict"] for s in done])) if done else None
        med_t = float(np.median([per_seed[str(s)]["top5"] for s in done])) if done else None
        ci_s, ci_t = boot_median_ci([b2[s] for s in done], rng) if done else (None, None)
        t2 = {"label": "track 2: new gpt-4-turbo-2024-04-09 diagnoses, substitute judge", "per_seed": per_seed,
              "seeds_with_data": done, "median_strict": med_s, "median_top5": med_t,
              "median_strict_ci95": ci_s, "median_top5_ci95": ci_t, "n_calls": len(res2), "served": _served(res2)}

    gen = load_results(GEN_RUN)
    detail = {"rerun_P1_median": t2["median_strict"] if t2 else None,
              "in_ci_judge_matched_track1": _inside(t2["median_strict"], t1["strict_ci95"]) if (t1 and t2) else None,
              "in_ci_paper_table3": _inside(t2["median_strict"], orig_repo["strict_ci95"]) if t2 else None,
              "top5_direction_kept": (t2["median_top5"] > t2["median_strict"]) if (t2 and t2["median_strict"] is not None) else None,
              "top5_minus_strict_pp": (t2["median_top5"] - t2["median_strict"]) if (t2 and t2["median_strict"] is not None) else None,
              "paper_top5_minus_strict_pp": round(TABLE3["top5"] - TABLE3["strict"], 2)}
    if not (t1 and t2 and t2["median_strict"] is not None):
        label = "판정 보류 (pending)"
    elif not detail["top5_direction_kept"]:
        label = "사망 (death)"
    elif detail["in_ci_judge_matched_track1"] and detail["in_ci_paper_table3"]:
        label = "생존 (survival)"
    elif detail["in_ci_judge_matched_track1"] or detail["in_ci_paper_table3"]:
        label = "부분 생존 (partial)"
    else:
        label = "사망 (death)"
    drift = {"judge_drift_pp_strict": (t1["strict"] - orig_len["strict"]) if t1 and t1["strict"] is not None else None,
             "judge_drift_pp_top5": (t1["top5"] - orig_len["top5"]) if t1 and t1["top5"] is not None else None,
             "judge_drift_vs_table3_pp_strict": (t1["strict"] - TABLE3["strict"]) if t1 and t1["strict"] is not None else None,
             "generator_drift_pp_strict": (t2["median_strict"] - t1["strict"]) if (t1 and t2 and t2["median_strict"] is not None) else None,
             "generator_drift_pp_top5": (t2["median_top5"] - t1["top5"]) if (t1 and t2 and t2["median_top5"] is not None) else None,
             "definition": "judge drift = track 1 minus the original verdicts on the SAME archived diagnoses (lenient parser both; "
                           "also vs Table 3's 54.04); generator drift = track 2 (median over repeats) minus track 1 under the SAME "
                           "substitute judge. The two are additive: track 2 - Table 3 = judge drift + generator drift."}
    budgets = {"baseline_alive": _budget(GEN_RUN), "judge_track1": _budget(J1_RUN), "judge_track2": _budget(J2_RUN)}
    cost = sum((b or {}).get("cost_usd", 0) for b in budgets.values())
    result = {"card": CARD, "generated_utc": now(), "generation_model": GEN_MODEL, "judge_model": JUDGE_MODEL,
              "original_table3": orig_repo, "original_lenient": orig_len, "track1": t1, "track2": t2, "drift": drift,
              "judgment": {"label": label, "rule": "card judgment (ANALYSIS_PLAN section 1): survival = re-run P1 (median over 3 repeats) "
                           "inside the case-bootstrap 95% CI of track 1 (judge-matched) AND inside the CI of the paper's own verdicts, "
                           "with Top-5 > Strict; partial = inside exactly one CI; death = inside neither or Top-5 ordering reversed. "
                           "Reading chosen: the card's 'or vice versa' clause makes 'inside the judge-matched CI only' partial. "
                           "Top-5 >= Strict holds by construction (P5 adds to P1), so the direction check can only fail when no "
                           "case is P5; the Top-5 minus Strict gap is reported against the paper's 14.65 pp for the human coders.",
                           "detail": detail},
              "generation": {"n_calls": len(gen), "expected": N_CASES * N_SEEDS, "served": _served(gen)},
              "budgets": budgets, "cost_usd_total": round(cost, 4)}
    RUNROOT.mkdir(parents=True, exist_ok=True)
    (RUNROOT / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    table = pd.DataFrame([{"row": r["row"], "id": r["id"], "gt": r["gt"], "orig_score_raw": r["orig_score"],
                           "orig_bucket_repo": b_repo[i], "orig_bucket_lenient": b_len[i],
                           "track1_raw": content(res1.get((r["id"], 0))), "track1_bucket": b1[i],
                           **{f"track2_seed{s}_raw": content(res2.get((r["id"], s))) for s in range(N_SEEDS)},
                           **{f"track2_seed{s}_bucket": b2[s][i] for s in range(N_SEEDS)}} for i, r in enumerate(rows)])
    table.to_csv(RUNROOT / "per_case.csv", index=False, encoding="utf-8")
    write_run_meta(result, gen, res1, res2)

    def fmt(m):
        return (f"strict {m['strict']:.2f} {['%.1f' % v for v in m['strict_ci95']]} | top-5 {m['top5']:.2f} "
                f"{['%.1f' % v for v in m['top5_ci95']]} (n={m['n_scored']})") if m and m.get("strict") is not None else "no data"
    print(f"{'Table 3 (orig judge, repo count)':38s} {fmt(orig_repo)}")
    print(f"{'orig judge, lenient parser':38s} {fmt(orig_len)}")
    print(f"{'track 1 (archived dx, gpt-4o judge)':38s} {fmt(t1)}")
    if t2:
        for s, v in t2["per_seed"].items():
            print(f"{'track 2 repeat ' + s:38s} {fmt(v)}")
        ci = lambda v: ['%.1f' % x for x in v] if v else None  # noqa: E731
        print(f"{'track 2 median over repeats':38s} strict {t2['median_strict']:.2f} {ci(t2['median_strict_ci95'])} | "
              f"top-5 {t2['median_top5']:.2f} {ci(t2['median_top5_ci95'])}")
    else:
        print(f"{'track 2':38s} no data")
    print("drift:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in drift.items() if k != "definition"})
    if t1:
        print("judge agreement on archived diagnoses:", t1["agreement_with_original_judge"])
    print(f"judgment: {label} | {detail} | cost ${cost:.2f}")
    return result


def write_run_meta(result, gen, res1, res2):
    manifest = json.loads((INPUTS / "manifest.json").read_text(encoding="utf-8")) if (INPUTS / "manifest.json").exists() else None
    t1, t2 = result["track1"], result["track2"]
    frictions = [
        "judge model dead: GPT-4-0613 behind the Azure deployment 'nav29' (shut down 2024-09-13); substitute gpt-4o-2024-05-13 in a two-track design",
        "ground-truth disease names come from a live Orphanet API call with a hard-coded key in the repo; the archived GT strings were reused instead",
        "the HF loading script (RareBench.py) no longer runs under datasets 4.x; data/RAMEDIS.jsonl was read directly from data.zip in file order",
        f"HPO term names depend on the ontology bundled with the unpinned hpo3 package at run time; release {HPO_RELEASE} assumed (hpo3 1.2.0 era)",
        "2 of 200 archived judge outputs carry literal quotes and are dropped by the repo's counting (denominator 198); a lenient parser is used for the substitute judge",
        "repo scripts call HF, Orphanet and LLM APIs at import time; prompt templates were extracted with ast and verified byte-for-byte instead of importing",
        "Windows checkout (core.autocrlf) turns the LF CSV blobs into CRLF, including inside the diagnosis texts; normalised back to LF",
    ]
    if t1 and t1.get("n_unscored"):
        frictions.append(f"track 1: {t1['n_unscored']} substitute-judge outputs without a parseable P0..P5 label")
    if t2:
        unsc = sum(v.get("n_unscored", 0) for v in t2["per_seed"].values())
        if unsc:
            frictions.append(f"track 2: {unsc} substitute-judge outputs without a parseable P0..P5 label")
    meta = {
        "card_id": CARD,
        "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
        "target_paper": {
            "title": "Assessing DxGPT: Diagnosing Rare Diseases with Various Large Language Models",
            "repo": "https://github.com/foundation29org/dxgpt_testing",
            "repo_commit": "c7abe550ccad59465bdf53b67e9629e3f239f0eb",
            "original_source": "Table 3 (RAMEDIS, 200 cases) reproduced from data/scores_RAMEDIS_gpt4turbo0409.csv with the "
                               "src/dashboard_scores.py counting: P1 107, P2-P5 29, P0 62 of 198 -> 54.04 / 68.69"},
        "generation": {
            "model_requested": GEN_MODEL, "model_served": result["generation"]["served"]["models"],
            "n_fingerprints": result["generation"]["served"]["n_fingerprints"],
            "parameters": "temperature 0, max_tokens 800, one user message = PROMPT_TEMPLATE of src/batch_diagnosis_v2.py with the "
                          "Python list repr of the case's HPO term names; no system message, no seed parameter",
            "battery": f"{N_CASES} RAMEDIS cases x {N_SEEDS} repeats (seed_idx 0-2, identical requests); {result['generation']['n_calls']} calls archived"},
        "judge": {
            "original": "GPT-4-0613 via Azure deployment 'nav29' (src/diagnoses_analisis.py), temperature 0, max_tokens 800; dead",
            "substitute_requested": JUDGE_MODEL,
            "model_served": sorted(set((t1 or {}).get("served", {}).get("models", []) + (t2 or {}).get("served", {}).get("models", []))),
            "parameters": "temperature 0, max_tokens 800, one user message = PROMPT_TEMPLATE of src/diagnoses_analisis.py with the GT "
                          "cell as stored (list repr) and the full diagnosis text",
            "tracks": {"judge_track1": "the 200 archived gpt-4-turbo-0409 diagnoses re-judged",
                       "judge_track2": f"the {N_CASES * N_SEEDS} new diagnoses judged"},
            "label_parsing": "lenient (first P0..P5 token, P2-P5 -> P5) on both the original and the substitute verdicts; "
                             "the repo's exact counting (198 denominator for the original) is reported alongside"},
        "drift_separation": "Generator drift and judge drift are separated by design: judge drift = track 1 (archived diagnoses, "
                            "substitute judge) minus the original verdicts on the same diagnoses (Table 3 / lenient re-count); "
                            "generator drift = track 2 (new gpt-4-turbo-2024-04-09 diagnoses, median over 3 repeats) minus track 1 "
                            "under the same substitute judge. The judgment uses the judge-matched comparison; the comparison "
                            "with the published 54.04 is secondary because the original judge cannot be re-run.",
        "data": {
            "cases": "HF chenxz/RareBench, config RAMEDIS, split test: first 200 records of data/RAMEDIS.jsonl (file order)",
            "license": "RareBench: Apache-2.0 (HF dataset card license tag and GitHub chenxz1111/RareBench LICENSE); "
                       "dxgpt_testing repo: MIT (Foundation29hub 2023)",
            "citation": "Chen et al. 2024, RareBench: Can LLMs Serve as Rare Diseases Specialists? arXiv:2402.06341",
            "item_text_archived": True,
            "item_text_note": "Apache-2.0 permits redistribution with attribution; calls.jsonl therefore keeps the HPO term lists; "
                              "per_case.csv and the case_sha256 in each request meta allow an id+hash archive if needed",
            "ground_truth": "archived GT strings (Orphanet preferred names resolved by the authors); no Orphanet API call",
            "hpo_release": HPO_RELEASE,
            "inputs_manifest": manifest},
        "results": {
            "original_table3": {k: result["original_table3"][k] for k in ("P1", "P5", "P0", "n_scored", "strict", "top5", "strict_ci95", "top5_ci95")},
            "original_lenient": {k: result["original_lenient"][k] for k in ("P1", "P5", "P0", "n_scored", "strict", "top5", "strict_ci95", "top5_ci95")},
            "track1_judge_matched": ({k: t1[k] for k in ("P1", "P5", "P0", "n_scored", "n_unscored", "strict", "top5", "strict_ci95", "top5_ci95",
                                                          "n_missing", "agreement_with_original_judge")} if t1 else None),
            "track2_reexecution": ({k: t2[k] for k in ("per_seed", "median_strict", "median_top5", "median_strict_ci95", "median_top5_ci95",
                                                        "seeds_with_data")} if t2 else None),
            "drift": result["drift"],
            "cost_usd": result["cost_usd_total"],
            "calls": {k: (v or {}).get("calls") for k, v in result["budgets"].items()},
            "errors": {k: (v or {}).get("errors") for k, v in result["budgets"].items()},
            "judgment": result["judgment"]["label"],
            "judged_by": "automatic rule per card 'judgment' / ANALYSIS_PLAN section 1 (see result.json judgment.rule); human double-coding pending",
            "note": result["judgment"]["detail"]},
        "reproducibility_frictions_observed": frictions,
    }
    (RUNROOT / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for flag in ("prepare", "check", "dry-run", "run", "judge", "analyze"):
        ap.add_argument(f"--{flag}", action="store_true")
    ap.add_argument("--track", choices=["1", "2", "both"], default="both", help="judge stage(s) for --judge")
    a = ap.parse_args()
    if a.prepare:
        prepare()
    if a.check:
        check()
    if a.dry_run:
        dry_run()
    if a.run:
        run()
    if a.judge:
        judge(a.track)
    if a.analyze:
        analyze()


if __name__ == "__main__":
    main()
