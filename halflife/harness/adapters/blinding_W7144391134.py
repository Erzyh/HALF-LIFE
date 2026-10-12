"""Card W7144391134 - In-Context Molecular Property Prediction with LLMs: A Blinding Study on Memorization and
Knowledge Conflicts (Busch et al. 2026, MatthiasHBusch/BlindingLLMs). Scope here: Delaney/ESOL, input type
"names_only", approach "with_preanalysis" (blinding level L1), subject model gpt-4.1-nano.

Claim re-measured (results/zeroshot_accuracy.csv, results/bootstrap_correlation_ci.csv; ICL correlations x100):
  0-shot    : Pearson r = 0.407 over all 1,128 molecules (per-molecule mean of 5 repetitions), R2 = 0.105;
              memorization diagnostics: 3-sig-digit exact matches 0.14 %, retention R21 = 9.7 %, R32 = 9.0 %
  60-shot   : 0 extended + 60 in-context examples  -> r = 42.9 [28.2, 56.1]  (150 test molecules, 2 runs)
  1000-shot : 940 extended + 60 in-context examples -> r = 75.6 [68.5, 81.5]

Protocol ported from src/Run_Delaney_ZeroShot.jl, src/Run_Delaney_Experiments.jl, src/Delaney_Prompts.jl
(create_experiment_states / global_batch_execution) and src/lib/LLMUtils.jl (LLMChat defaults, get_body):
  * outer split: rows of data/delaney-processed.csv shuffled with MersenneTwister(42); first 150 = test set,
    next 940 = extended training set. Inner split: the 150 test rows shuffled again with MersenneTwister(42),
    5 folds of 30; the 60 in-context examples of a fold are the first 60 shuffled positions outside the fold
    (folds 3-5 therefore share one example set, so a run has 3 distinct analysis conversations).
  * in-context conversation: system prompt -> [user: extended set of 940 (Name/SMILES/value), 1000-shot only]
    -> user: analysis prompt with the 60 examples -> assistant analysis (call 1, one per fold group and run,
    shared by all molecules of the group exactly as the Julia de-duplication does) -> user: prediction prompt
    for the target molecule (call 2); the last number in the reply is the prediction.
  * zero-shot: system prompt + one question per molecule, 5 repetitions each over all 1,128 molecules.
  * parameters: temperature 0.7, top_p 0.95, no seed; max_tokens 4000 (ICL) / 800 (zero-shot, ask_gpt default).
  * metric: per-molecule mean of valid predictions (NaN and values >= 100 dropped; a molecule without any valid
    prediction counts as 0.0, as in src/bootstrap_correlation_ci.py), Pearson r vs measured log solubility,
    95 % percentile bootstrap over the 150 molecules (5,000 resamples, numpy default_rng(42)).

Approximations / deviations from the original run (everything else is byte-for-byte):
  1. Endpoint: OpenAI chat completions with the dated snapshot gpt-4.1-nano-2025-04-14 instead of the authors'
     Azure deployment "gpt-4.1-nano" (api-version 2024-12-01-preview); the served model string and
     system_fingerprint are archived per call.
  2. Message content is sent as plain strings; the Julia client wraps every message as
     [{"type": "text", "text": ...}] (identical text reaches the model). The "ephemeral" cache_control tag the
     Julia code attaches to two messages is only emitted for its OpenRouter client and is dropped for Azure /
     OpenAI (prompt caching on OpenAI is automatic).
  3. The molecule selection is reproduced with a pure-Python port of Julia's MersenneTwister (dSFMT-19937 seeded
     through Julia >= 1.11's SHA-256 seed hashing) and Random.shuffle!; --check verifies that the 150 test
     molecules equal the archived ones (a full-permutation identity check), so the fold membership and the
     940 extended molecules are the original ones too. No numpy fallback is used unless that check fails
     (then the adapter reports "reconstructed" and derives the test set from the archived JSON keys).
  4. Bootstrap CIs of the re-run use a fresh default_rng(42) per configuration; the repository draws all its
     configurations from one shared generator (--check replays that shared stream to confirm the archived CIs).
  5. Zero-shot: the Julia call passes reasoning_effort="none", which the Azure client ignores for gpt-4.1
     models; nothing is sent here either.

  python adapters/blinding_W7144391134.py --check      # re-score the archived predictions, verify split/prompts/parser
  python adapters/blinding_W7144391134.py --dry-run    # request counts and cost estimate, no API calls
  python adapters/blinding_W7144391134.py --run        # cap $20; zero-shot + analyses first, then predictions
  python adapters/blinding_W7144391134.py --analyze
"""
import argparse, csv, hashlib, json, math, random, re, struct, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, run_battery  # noqa: E402

HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / "W7144391134" / "MatthiasHBusch__BlindingLLMs"
DATA = REPO / "data" / "delaney-processed.csv"
RESULTS = REPO / "results"
RUN = HALF / "runs" / "W7144391134" / "baseline_alive"
MODEL, CAP = "gpt-4.1-nano-2025-04-14", 20.0
ORIG_KEY, ZS_KEY = "gpt-4.1-nano_2024-12-01-preview", "gpt-4.1-nano"
SEED, N_TEST, N_EXT, N_ICL, K_FOLDS, NUM_RUNS, ZS_ITER = 42, 150, 940, 60, 5, 2, 5
EXTS = (0, N_EXT)
TARGET = "measured log solubility in mols per litre"
N_BOOT = 5000
PRICE_IN, PRICE_IN_CACHED, PRICE_OUT = 0.10, 0.025, 0.40   # USD per 1M tokens, gpt-4.1-nano list price

# --- prompts, byte-exact copies of src/Delaney_Prompts.jl (names_only) and src/Run_Delaney_ZeroShot.jl ---
SYSTEM = ("**Your Role**\n"
          "You are a professional chemist with expert knowledge in physical chemistry and solubility prediction.\n"
          "You are tasked with predicting the log solubility (log(mol/L)) of organic molecules in water based on their IUPAC names and SMILES strings.\n"
          "\n"
          "**Problem Description**\n"
          "Solubility is a key property in drug discovery and agrochemistry.\n"
          "You will be provided with:\n"
          "1. A training dataset of molecules with their Names, SMILES, and known solubility values.\n"
          "2. A test molecule (Name and SMILES) for which you must predict the solubility.\n"
          "\n"
          "You have to use your knowledge and abilities to analyze the training datas molecules and the patterns and relationships between molecular properties and solubility to make an accurate prediction.\n")
ANALYSIS = ("    **Training Data:**\n"
            "    - Names: <molecule_names_training>\n"
            "    - SMILES: <smiles_strings_training>\n"
            "    - Log Solubility (mol/L): <solubilities_training>\n"
            "\n"
            "    **Analysis Task:**\n"
            "    1. Identify functional groups and structural features for each training sample.\n"
            "    2. Analyze how these features influence the solubility (e.g., hydrophilic vs hydrophobic groups).\n"
            "    3. Find pairs of similar molecules with different solubilities and explain the difference.\n"
            "    \n"
            "    Think step by step and provide a systematic analysis of the training data patterns.\n")
PREDICTION = ("    **Test Data:**\n"
              "    - Names: <molecule_names_test>\n"
              "    - SMILES: <smiles_strings_test>\n"
              "\n"
              "    **Target Molecule:**\n"
              "    - Name: <molecule_name>\n"
              "    - SMILES: <smiles_string>\n"
              "\n"
              "    **Prediction Guide:**\n"
              "    \n"
              "    **Similar Molecules Relations**\n"
              "    1. Similar Molecules: Find all similar molecules in the training data and analyze their relation to this compound wrt the solubility \n"
              "    process. Use the training data and the analyzed training data.\n"
              "    2. Similarity Analysis: Analyze similar molecules and rank them by similarity (wrt the mechanisms in the solubility process). \n"
              "    Assign them a similarity value (wrt the mechanisms in the solubility process).\n"
              "    \n"
              "    **Molecule Analysis**\n"
              "    3. Pattern Analysis: Analyze if found patterns apply to the molecule\n"
              "    4. Functional Groups: Analyze its functional groups and their influence on the solubility\n"
              "    5. Atomic Structure: Analyze its atomic structure and how this might influence the solubility\n"
              "    6. Weighted Average: Calculate a weighted average of the solubilities of the similar molecules. \n"
              "    Exclude molecules that have a small similarity value.\n"
              "    \n"
              "    **Review and Prediction**\n"
              "    7. Prediction: Review your analysis shortly and write down the weighted average.\n"
              "    8. Result: As a result, write down one value and nothing after that. Syntax: \"[Value]\"\n")
EXT_HEADER = "This is an extended set of samples from the same dataset as the test set:\n"
ZS_SYSTEM = ("You are an expert chemist and know the delaney solubility dataset very well. You are given a SMILES string of a "
             "molecule. Your task is to predict the measured solubility of that molecule in log solubility in mols per litre "
             "log(mol/L). Provide only the numerical value as output, without any additional text.")
ZS_QUESTION = ("What is the measured solubility in the delaney dataset in log(mol/L) of the molecule with the following "
               "SMILES string: {smiles}? Provide only the numerical value as output, without any additional text.")
NUMBER_RE = re.compile(r"(?:^|(?<=[^0-9.]))([-–−]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+))(?=[^0-9]|$)")


# ----------------------------------------------------------------------------------------------------------
# Julia MersenneTwister(seed) + Random.shuffle!  (Julia >= 1.11: stdlib/Random/src/{RNGs,misc}.jl, dSFMT-19937)
# ----------------------------------------------------------------------------------------------------------
class JuliaMT:
    """dSFMT-19937 exactly as libdSFMT, seeded like Julia >= 1.11 (dsfmt_init_by_array(SHA-256(seed words)));
    raw64() is the bit pattern of the next double in [1, 2) (Julia's float cache); shuffle() is Random.shuffle!."""
    N, POS1, SL1, SR = 191, 117, 19, 12
    MSK1, MSK2 = 0x000ffafffffffb3f, 0x000ffdfffc90fffd
    FIX1, FIX2, PCV1, PCV2 = 0x90014964b32f4329, 0x3b8d12ac548a7c7a, 0x3d84e1ac0dc82880, 0x0000000000000001
    M64, M32 = (1 << 64) - 1, (1 << 32) - 1

    def __init__(self, seed):
        self.buf, self.pos = [], 0
        self._init_by_array(self.hash_seed(seed))

    @staticmethod
    def hash_seed(n):                         # Random.hash_seed(::Integer): SHA-256 over the little-endian UInt32 words
        assert n >= 0
        ctx = hashlib.sha256()
        while True:
            ctx.update(struct.pack("<I", n & 0xffffffff))
            n >>= 32
            if n == 0:
                break
        return list(struct.unpack("<8I", ctx.digest()))    # reinterpret(UInt32, digest)

    def _init_by_array(self, key):            # dsfmt_init_by_array + initial_mask + period_certification
        N, M32 = self.N, self.M32
        size = (N + 1) * 4
        lag = 11 if size >= 623 else 7 if size >= 68 else 5 if size >= 39 else 3
        mid = (size - lag) // 2
        p = [0x8b8b8b8b] * size
        f1 = lambda x: ((x ^ (x >> 27)) * 1664525) & M32          # noqa: E731
        f2 = lambda x: ((x ^ (x >> 27)) * 1566083941) & M32       # noqa: E731
        count = max(len(key) + 1, size)
        r = f1(p[0] ^ p[mid % size] ^ p[(size - 1) % size])
        p[mid % size] = (p[mid % size] + r) & M32
        r = (r + len(key)) & M32
        p[(mid + lag) % size] = (p[(mid + lag) % size] + r) & M32
        p[0] = r
        count -= 1
        i, j = 1, 0
        while j < count and j < len(key):
            r = f1(p[i] ^ p[(i + mid) % size] ^ p[(i + size - 1) % size])
            p[(i + mid) % size] = (p[(i + mid) % size] + r) & M32
            r = (r + key[j] + i) & M32
            p[(i + mid + lag) % size] = (p[(i + mid + lag) % size] + r) & M32
            p[i] = r
            i, j = (i + 1) % size, j + 1
        while j < count:
            r = f1(p[i] ^ p[(i + mid) % size] ^ p[(i + size - 1) % size])
            p[(i + mid) % size] = (p[(i + mid) % size] + r) & M32
            r = (r + i) & M32
            p[(i + mid + lag) % size] = (p[(i + mid + lag) % size] + r) & M32
            p[i] = r
            i, j = (i + 1) % size, j + 1
        for _ in range(size):
            r = f2((p[i] + p[(i + mid) % size] + p[(i + size - 1) % size]) & M32)
            p[(i + mid) % size] ^= r
            r = (r - i) & M32
            p[(i + mid + lag) % size] ^= r
            p[i] = r
            i = (i + 1) % size
        u = [p[2 * k] | (p[2 * k + 1] << 32) for k in range(2 * (N + 1))]
        for k in range(2 * N):
            u[k] = (u[k] & 0x000FFFFFFFFFFFFF) | 0x3FF0000000000000
        inner = ((u[2 * N] ^ self.FIX1) & self.PCV1) ^ ((u[2 * N + 1] ^ self.FIX2) & self.PCV2)
        s = 32
        while s > 0:
            inner ^= inner >> s
            s >>= 1
        if inner & 1 == 0:
            u[2 * N + 1] ^= 1
        self.u = u

    def _gen_rand_all(self):
        N, POS1, u, M64 = self.N, self.POS1, self.u, self.M64
        L0, L1 = u[2 * N], u[2 * N + 1]
        for i in range(N):
            b = i + POS1 if i < N - POS1 else i + POS1 - N
            t0, t1 = u[2 * i], u[2 * i + 1]
            L0, L1 = (((t0 << self.SL1) ^ (L1 >> 32) ^ (L1 << 32) ^ u[2 * b]) & M64,
                      ((t1 << self.SL1) ^ (L0 >> 32) ^ (L0 << 32) ^ u[2 * b + 1]) & M64)
            u[2 * i] = (L0 >> self.SR) ^ (L0 & self.MSK1) ^ t0
            u[2 * i + 1] = (L1 >> self.SR) ^ (L1 & self.MSK2) ^ t1
        u[2 * N], u[2 * N + 1] = L0, L1
        self.buf, self.pos = list(u[:2 * N]), 0

    def raw64(self):
        if self.pos >= len(self.buf):
            self._gen_rand_all()
        x = self.buf[self.pos]
        self.pos += 1
        return x

    def rand(self):                           # rand(rng) = rand(CloseOpen12) - 1.0
        return struct.unpack("<d", struct.pack("<Q", self.raw64()))[0] - 1.0

    def shuffle(self, n):                     # shuffle(rng, 1:n) -> 1-based permutation (Random/misc.jl, ltm52)
        a, mask = list(range(1, n + 1)), 3
        for i in range(2, n + 1):
            while True:
                x = self.raw64() & mask
                if x <= i - 1:
                    break
            j = 1 + x
            a[i - 1], a[j - 1] = a[j - 1], a[i - 1]
            if i == 1 + mask:
                mask = 2 * mask + 1
        return a


# ----------------------------------------------------------------------------------------------------------
# data, split, prompts
# ----------------------------------------------------------------------------------------------------------
def load_rows():
    with open(DATA, encoding="utf-8", newline="") as f:
        rows = [{"name": r["Compound ID"], "smiles": r["smiles"], "y": float(r[TARGET]), "y_raw": r[TARGET]}
                for r in csv.DictReader(f)]
    for r in rows:
        r["y_str"] = repr(r["y"])             # Julia string(Float64): shortest round-trip, same as Python repr here
    return rows


def archived_leaf(ext):
    res = json.loads((RESULTS / "LLM_Results_delaney.json").read_text(encoding="utf-8"))
    return res["names_only"]["with_preanalysis"][ORIG_KEY][str(ext)][str(N_ICL)]


def make_split(rows, mode=None):
    """Returns dict(test=[150 rows in shuffled fold order], ext=[940 rows], folds=[(test_pos, train_pos)],
    groups={group_id: (train_pos tuple, [fold ids])}, mode='exact'|'reconstructed')."""
    archived = set(archived_leaf(N_EXT))
    perm = JuliaMT(SEED).shuffle(len(rows))
    test = [rows[i - 1] for i in perm[:N_TEST]]
    if mode is None:
        mode = "exact" if {r["name"] for r in test} == archived else "reconstructed"
    if mode == "exact":
        ext = [rows[i - 1] for i in perm[N_TEST:N_TEST + N_EXT]]
        inner = JuliaMT(SEED).shuffle(N_TEST)
        test = [test[i - 1] for i in inner]
    else:                                     # fallback: archived test names, CSV order for the rest
        test = [r for r in rows if r["name"] in archived]
        ext = [r for r in rows if r["name"] not in archived][:N_EXT]
        rng = np.random.default_rng(SEED)
        test = [test[i] for i in rng.permutation(N_TEST)]
    per = N_TEST // K_FOLDS
    folds, groups, gid = [], {}, {}
    for j in range(K_FOLDS):
        test_pos = list(range(per * j, per * (j + 1)))
        train_pos = tuple(p for p in range(N_TEST) if p not in test_pos)[:N_ICL]
        folds.append((test_pos, train_pos))
        if train_pos not in gid:
            gid[train_pos] = len(gid)
            groups[gid[train_pos]] = (train_pos, [])
        groups[gid[train_pos]][1].append(j)
    return {"test": test, "ext": ext, "folds": folds, "groups": groups, "mode": mode}


def bracket(xs):
    return "[" + ", ".join(xs) + "]"


def analysis_prompt(train_rows):
    return (ANALYSIS.replace("<molecule_names_training>", bracket(r["name"] for r in train_rows))
            .replace("<smiles_strings_training>", bracket(r["smiles"] for r in train_rows))
            .replace("<solubilities_training>", bracket(r["y_str"] for r in train_rows)))


def prediction_prompt(fold_test_rows, target):
    return (PREDICTION.replace("<molecule_names_test>", bracket(r["name"] for r in fold_test_rows))
            .replace("<smiles_strings_test>", bracket(r["smiles"] for r in fold_test_rows))
            .replace("<molecule_name>", target["name"]).replace("<smiles_string>", target["smiles"]))


def extended_message(ext_rows):
    return EXT_HEADER + "".join(f"Name: {r['name']}\nSMILES: {r['smiles']}\n{TARGET}: {r['y_str']}\n\n" for r in ext_rows)


def prefix_messages(split, ext):
    msgs = [{"role": "system", "content": SYSTEM}]
    if ext:
        msgs.append({"role": "user", "content": extended_message(split["ext"][:ext])})
    return msgs


def body(messages, max_tokens):
    return {"model": MODEL, "messages": messages, "temperature": 0.7, "top_p": 0.95, "max_tokens": max_tokens}


# ----------------------------------------------------------------------------------------------------------
# requests
# ----------------------------------------------------------------------------------------------------------
def zeroshot_requests(rows, keep=None):
    """keep: set of row indices to query (None = all 1,128 molecules); ids stay zs_<row index> so archived calls are reused."""
    return [{"id": f"zs_{i:04d}", "seed_idx": it, "meta": {"phase": "zeroshot", "name": r["name"]},
             "body": body([{"role": "system", "content": ZS_SYSTEM},
                           {"role": "user", "content": ZS_QUESTION.format(smiles=r["smiles"])}], 800)}
            for i, r in enumerate(rows) if keep is None or i in keep for it in range(ZS_ITER)]


def zeroshot_subset(rows, n, seed=20260907):
    """Seeded random subset of molecules for the zero-shot phase (cost cap device of the successor condition, 2026-10-01):
    the first n of one seeded permutation, so a larger n later extends the same subset."""
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    return set(order[:n])


def analysis_requests(split, runs=NUM_RUNS):
    reqs = []
    for ext in EXTS:
        for run in range(runs):
            for g, (train_pos, folds) in split["groups"].items():
                msgs = prefix_messages(split, ext) + [{"role": "user", "content": analysis_prompt([split["test"][p] for p in train_pos])}]
                reqs.append({"id": f"icl{ext}_analysis_g{g}", "seed_idx": run,
                             "meta": {"phase": "analysis", "ext": ext, "group": g, "folds": folds}, "body": body(msgs, 4000)})
    return reqs


def prediction_requests(split, analyses, runs=NUM_RUNS):
    """analyses: {(ext, run, group): assistant analysis text}. Only groups with an archived analysis are built."""
    reqs = []
    for ext in EXTS:
        for run in range(runs):
            for j, (test_pos, train_pos) in enumerate(split["folds"]):
                g = next(k for k, (tp, _) in split["groups"].items() if tp == train_pos)
                if (ext, run, g) not in analyses:
                    continue
                fold_rows = [split["test"][p] for p in test_pos]
                base = prefix_messages(split, ext) + [{"role": "user", "content": analysis_prompt([split["test"][p] for p in train_pos])},
                                                      {"role": "assistant", "content": analyses[(ext, run, g)]}]
                for p in test_pos:
                    t = split["test"][p]
                    reqs.append({"id": f"icl{ext}_pred_{p:03d}", "seed_idx": run,
                                 "meta": {"phase": "prediction", "ext": ext, "pos": p, "fold": j, "group": g, "name": t["name"]},
                                 "body": body(base + [{"role": "user", "content": prediction_prompt(fold_rows, t)}], 4000)})
    return reqs


def reply_text(rec):
    try:
        return rec["response"]["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError):
        return ""


def collect_analyses(res):
    out = {}
    for (rid, run), r in res.items():
        m = r.get("meta", {})
        if m.get("phase") == "analysis" and reply_text(r).strip():
            out[(m["ext"], run, m["group"])] = reply_text(r)
    return out


# ----------------------------------------------------------------------------------------------------------
# parsing and metrics (ports of search_for_last_number_in_string, bootstrap_correlation_ci.py, zeroshot_extended_si.py)
# ----------------------------------------------------------------------------------------------------------
def last_number(text):
    ms = NUMBER_RE.findall(text or "")
    if not ms:
        return math.nan
    m = ms[-1]
    for cand in (m, m + ".0", m.replace("–", "-"), m.replace("−", "-")):
        try:
            return float(cand)
        except ValueError:
            pass
    return math.nan


def clean_preds(lst):
    out = []
    for p in lst:
        try:
            p = float(p)
        except (TypeError, ValueError):
            continue
        if not math.isnan(p) and p < 100:
            out.append(p)
    return out


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    xm, ym = x - x.mean(), y - y.mean()
    return float(xm @ ym / math.sqrt((xm @ xm) * (ym @ ym)))


def bootstrap_ci(pred, true, rng, n_boot=N_BOOT):
    pred, true, n = np.asarray(pred, float), np.asarray(true, float), len(pred)
    rs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if np.std(pred[idx]) == 0 or np.std(true[idx]) == 0:
            continue
        rs.append(pearson(pred[idx], true[idx]))
    return [float(np.percentile(rs, 2.5)), float(np.percentile(rs, 97.5))]


def icl_metrics(pred_lists, lut, rng=None):
    """pred_lists: {name: [predictions]} -> r x100, CI x100, per-molecule means (repo aggregation)."""
    names = [n for n in pred_lists if n in lut]
    means = np.array([float(np.mean(cp)) if (cp := clean_preds(pred_lists[n])) else 0.0 for n in names])
    trues = np.array([lut[n] for n in names])
    n_valid = sum(len(clean_preds(pred_lists[n])) for n in names)
    n_total = sum(len(pred_lists[n]) for n in names)
    out = {"n": len(names), "r": round(100 * pearson(means, trues), 1), "n_pred_valid": n_valid, "n_pred_total": n_total,
           "n_mol_without_valid": int(sum(1 for n in names if not clean_preds(pred_lists[n])))}
    if rng is not None:
        out["ci"] = [round(100 * c, 1) for c in bootstrap_ci(means, trues, rng)]
    return out, dict(zip(names, means))


def sig_figs(v):
    if v == 0:
        return 1
    s = f"{v:.10g}".lstrip("-").replace(".", "").lstrip("0")
    return max(1, len(s.rstrip("0"))) if s else 1


def sig_round(x, n):
    return "0" if x == 0 else f"{x:.{n}g}"


def zeroshot_metrics(pred_lists, lut):
    """Per-molecule mean of finite predictions -> Pearson r, R2 (sklearn convention); 3-sig exact matches; R21, R32."""
    ts, ps, pairs = [], [], []
    for name, preds in pred_lists.items():
        if name not in lut:
            continue
        vals = [float(p) for p in preds if isinstance(p, (int, float)) and not math.isnan(float(p))]
        pairs.extend((lut[name], v) for v in vals)
        if vals:
            ts.append(lut[name])
            ps.append(float(np.mean(vals)))
    ts, ps = np.array(ts), np.array(ps)
    r = pearson(ts, ps)
    r2 = 1 - np.sum((ts - ps) ** 2) / np.sum((ts - np.mean(ts)) ** 2)
    m3 = tot3 = 0
    for tv, pv in pairs:
        if sig_figs(tv) >= 3:
            tot3 += 1
            m3 += sig_round(pv, 3) == sig_round(tv, 3)
    ret = {}
    for k in (2, 3):
        lo = hi = 0
        for tv, pv in pairs:
            if sig_figs(tv) < k or sig_figs(pv) < k:
                continue
            if sig_round(pv, k - 1) == sig_round(tv, k - 1):
                lo += 1
                hi += sig_round(pv, k) == sig_round(tv, k)
        ret[f"R{k}{k-1}"] = {"m_low": lo, "m_high": hi, "pct": round(100 * hi / lo, 1) if lo else None}
    return {"n": int(len(ts)), "pearson_r": round(r, 3), "r2": round(float(r2), 3), "n_predictions": len(pairs),
            "exact3": {"matches": m3, "total": tot3, "pct": round(100 * m3 / tot3, 2) if tot3 else None},
            "R21_pct": ret["R21"]["pct"], "R21_counts": [ret["R21"]["m_low"], ret["R21"]["m_high"]],
            "R32_pct": ret["R32"]["pct"], "R32_counts": [ret["R32"]["m_low"], ret["R32"]["m_high"]]}


# ----------------------------------------------------------------------------------------------------------
# environment check on the archived results
# ----------------------------------------------------------------------------------------------------------
def julia_triple_quoted(src, lhs):
    """Value of `lhs = \"\"\"...\"\"\"` in a Julia file with the triple-quote dedent rule applied."""
    start = src.index(lhs + ' = """') + len(lhs + ' = """')
    text = src[start:src.index('"""', start)]
    if text.startswith("\n"):
        text = text[1:]
    lines = text.split("\n")
    cands = [re.match(r"[ \t]*", ln).group(0) for ln in lines[:-1] if ln.strip()] + [re.match(r"[ \t]*", lines[-1]).group(0)]
    common = cands[0]
    for c in cands[1:]:
        k = 0
        while k < min(len(common), len(c)) and common[k] == c[k]:
            k += 1
        common = common[:k]
    return "\n".join(ln[len(common):] if ln.startswith(common) else ln for ln in lines)


def check_prompts():
    src = (REPO / "src" / "Delaney_Prompts.jl").read_text(encoding="utf-8")
    zs = (REPO / "src" / "Run_Delaney_ZeroShot.jl").read_text(encoding="utf-8")
    ok = {"system": julia_triple_quoted(src, 'prompts["names_only"]["input_output_prompting"]["system"]') == SYSTEM,
          "analysis": julia_triple_quoted(src, 'prompts["names_only"]["with_preanalysis"]["analysis"]') == ANALYSIS,
          "prediction": julia_triple_quoted(src, 'prompts["names_only"]["with_preanalysis"]["prediction"]') == PREDICTION,
          "zs_system": re.search(r'system_prompt = """(.*?)"""', zs, re.S).group(1) == ZS_SYSTEM,
          "zs_question": re.search(r'get_prediction_prompt\(smiles\) = "(.*?)"\n', zs).group(1) == ZS_QUESTION.replace("{smiles}", "$smiles"),
          "ext_header": '"This is an extended set of samples from the same dataset as the test set:\\n"' in src}
    return ok


def check_parser():
    """Re-parse the 2,700 archived prediction replies (LLM_Chats_delaney_sin.json) and compare with the numbers the
    Julia pipeline stored for them (LLM_Results_delaney_sin.json)."""
    chats = json.loads((RESULTS / "LLM_Chats_delaney_sin.json").read_text(encoding="utf-8"))["names_only"]
    vals = json.loads((RESULTS / "LLM_Results_delaney_sin.json").read_text(encoding="utf-8"))["names_only"]
    agree = total = 0
    for ap in chats:
        for m in chats[ap]:
            for mol, replies in chats[ap][m]["940"]["60"].items():
                for reply, v in zip(replies, vals[ap][m]["940"]["60"][mol]):
                    total += 1
                    p = last_number(reply)
                    agree += (math.isnan(p) and (v is None or (isinstance(v, float) and math.isnan(v)))) or (v is not None and p == v)
    return agree, total


def check_bootstrap_csv(lut):
    """Replay bootstrap_correlation_ci.py on LLM_Results_delaney.json with its shared default_rng(42) stream and
    compare every Delaney row of results/bootstrap_correlation_ci.csv; return the two L1 gpt-4.1-nano rows."""
    res = json.loads((RESULTS / "LLM_Results_delaney.json").read_text(encoding="utf-8"))
    csv_rows = {}
    with open(RESULTS / "bootstrap_correlation_ci.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["dataset"] == "delaney":
                csv_rows[r["config"]] = (int(r["n"]), float(r["r"]), float(r["ci_lo"]), float(r["ci_hi"]))

    def leaves(obj, path=()):
        if isinstance(obj, dict):
            vals = list(obj.values())
            if vals and all(isinstance(v, list) for v in vals):
                yield path, obj
            else:
                for k, v in obj.items():
                    yield from leaves(v, path + (k,))
    rng = np.random.default_rng(SEED)
    ours, n_match, n_rows = {}, 0, 0
    for path, leaf in leaves(res):
        m, _ = icl_metrics(leaf, lut)
        if m["n"] < 5:
            continue
        m["ci"] = [round(100 * c, 1) for c in bootstrap_ci([np.mean(clean_preds(v)) if clean_preds(v) else 0.0 for k, v in leaf.items() if k in lut],
                                                            [lut[k] for k in leaf if k in lut], rng)]
        cfg = "/".join(path)
        n_rows += 1
        n_match += cfg in csv_rows and csv_rows[cfg] == (m["n"], m["r"], m["ci"][0], m["ci"][1])
        if cfg in (f"names_only/with_preanalysis/{ORIG_KEY}/0/60", f"names_only/with_preanalysis/{ORIG_KEY}/940/60"):
            ours[cfg] = {"rescored": m, "csv": csv_rows.get(cfg)}
    return ours, n_match, n_rows


def original(verbose=True):
    rows = load_rows()
    lut = {r["name"]: r["y"] for r in rows}
    out = {"floats_print_like_julia": all(r["y_str"] == r["y_raw"] for r in rows)}
    split = make_split(rows)
    out["split"] = {"mode": split["mode"], "test_match": len({r["name"] for r in split["test"]} & set(archived_leaf(N_EXT))),
                    "groups": {g: {"folds": folds, "first_train_pos": list(tp[:3])} for g, (tp, folds) in split["groups"].items()},
                    "first_test": [split["test"][i]["name"] for i in range(3)], "first_ext": [split["ext"][i]["name"] for i in range(3)]}
    out["prompts_verbatim"] = check_prompts()
    agree, total = check_parser()
    out["parser_agreement"] = [agree, total]
    ours, n_match, n_rows = check_bootstrap_csv(lut)
    out["icl"] = {("60-shot" if "/0/60" in k else "1000-shot"): v for k, v in ours.items()}
    out["bootstrap_csv_rows_reproduced"] = [n_match, n_rows]
    zs = json.loads((RESULTS / "LLM_Results_delaney_zeroshot.json").read_text(encoding="utf-8"))["Smiles"]["NoReasoning"][ZS_KEY]
    out["zeroshot"] = zeroshot_metrics(zs, lut)
    out["zeroshot_reference"] = {"pearson_r": 0.407, "r2": 0.105, "n": 1128, "exact3_pct": 0.14, "R21_pct": 9.7, "R32_pct": 9.0}
    if verbose:
        print(f"split           : {split['mode']} (test-set match {out['split']['test_match']}/150; fold groups "
              f"{ {g: v['folds'] for g, v in out['split']['groups'].items()} })")
        print(f"prompts verbatim: {out['prompts_verbatim']}")
        print(f"parser          : {agree}/{total} archived replies re-parsed to the stored value")
        print(f"floats          : Python repr == CSV text for all measured values: {out['floats_print_like_julia']}")
        for k, v in out["icl"].items():
            m = v["rescored"]
            print(f"{k:9s} rescored r = {m['r']} CI {m['ci']} (n={m['n']}, valid {m['n_pred_valid']}/{m['n_pred_total']}) | csv (n, r, lo, hi) = {v['csv']}")
        print(f"bootstrap csv   : {n_match}/{n_rows} Delaney rows reproduced exactly with the shared rng stream")
        z = out["zeroshot"]
        print(f"0-shot rescored : r = {z['pearson_r']} R2 = {z['r2']} (n={z['n']}); exact3 {z['exact3']['matches']}/{z['exact3']['total']} = {z['exact3']['pct']} %; "
              f"R21 = {z['R21_pct']} % {z['R21_counts']}; R32 = {z['R32_pct']} % {z['R32_counts']} | reference {out['zeroshot_reference']}")
    return out


# ----------------------------------------------------------------------------------------------------------
# run / dry run / analyze
# ----------------------------------------------------------------------------------------------------------
def own_estimate(reqs):
    """Rough cost with realistic output lengths; cached variant assumes the 940-molecule prefix is served from cache."""
    out_tok = {"zeroshot": 10, "analysis": 1500, "prediction": 900}
    tin = tout = cached = 0.0
    for r in reqs:
        msgs = r["body"]["messages"]
        toks = [len(m["content"]) / 4 + 8 for m in msgs]
        tin += sum(toks)
        tout += out_tok[r["meta"]["phase"]]
        if r["meta"].get("ext"):
            cached += toks[1]
    full = tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT
    return tin, tout, full, full - cached / 1e6 * (PRICE_IN - PRICE_IN_CACHED)


def do_run(dry_run, workers, runs, zs_molecules=None, zs_last=False):
    rows = load_rows()
    split = make_split(rows)
    keep = zeroshot_subset(rows, zs_molecules) if zs_molecules and zs_molecules < len(rows) else None
    zs = zeroshot_requests(rows, keep)
    first = ([] if zs_last else zs) + analysis_requests(split, runs)
    if keep is not None or zs_last:
        print(f"zero-shot phase: {len(zs)} calls over {len(keep) if keep is not None else len(rows)} molecules"
              f"{' (seeded subset)' if keep is not None else ''}, run {'after' if zs_last else 'before'} the predictions")
    if dry_run:
        placeholder = {(e, r, g): "x" * 8000 for e in EXTS for r in range(runs) for g in split["groups"]}
        preds = prediction_requests(split, placeholder, runs)
        reqs = first + preds + (zs if zs_last else [])
        print(f"requests: zero-shot {len(first) - len(analysis_requests(split, runs))}, analyses {len(analysis_requests(split, runs))}, "
              f"predictions {len(preds)} (placeholder 8k-char analysis in the prediction context), total {len(reqs)}; split mode {split['mode']}")
        run_battery(reqs, RUN, CAP, dry_run=True, label="W7144391134")
        tin, tout, full, cach = own_estimate(reqs)
        print(f"[own estimate] ~{tin/1e6:.1f}M input / ~{tout/1e3:.0f}k output tokens -> ~${full:.2f} at list price, "
              f"~${cach:.2f} if the 940-molecule prefix is cached (cap ${CAP})")
        return
    run_battery(first, RUN, CAP, workers=workers, label="W7144391134 zero-shot+analyses")
    analyses = collect_analyses(load_results(RUN))
    preds = prediction_requests(split, analyses, runs)
    missing = len(EXTS) * runs * len(split["groups"]) - len(analyses)
    if missing:
        print(f"WARNING: {missing} analysis replies missing/empty; their predictions are skipped (re-run to resume)")
    run_battery(preds, RUN, CAP, workers=workers, label="W7144391134 predictions")
    if zs_last:
        run_battery(zs, RUN, CAP, workers=workers, label="W7144391134 zero-shot")


def analyze(runs):
    rows = load_rows()
    lut = {r["name"]: r["y"] for r in rows}
    split = make_split(rows)
    res = load_results(RUN)
    out = {"card": "W7144391134", "model": MODEL, "n_calls": len(res), "split_mode": split["mode"], "original": original(verbose=False)}
    zs, icl, truncated = {}, {e: {} for e in EXTS}, 0
    for (rid, s), r in res.items():
        m, txt = r["meta"], reply_text(r)
        if ((r.get("response") or {}).get("choices") or [{}])[0].get("finish_reason") == "length":
            truncated += 1
        if m["phase"] == "zeroshot":
            zs.setdefault(m["name"], []).append(last_number(txt))
        elif m["phase"] == "prediction":
            icl[m["ext"]].setdefault(m["name"], {})[s] = last_number(txt)
    out["n_truncated_replies"] = truncated
    if zs:
        out["zeroshot"] = zeroshot_metrics(zs, lut)
    means = {}
    for ext in EXTS:
        if not icl[ext]:
            continue
        pooled = {n: list(d.values()) for n, d in icl[ext].items()}
        m, means[ext] = icl_metrics(pooled, lut, np.random.default_rng(SEED))
        m["per_run_r"] = {}
        for run in range(runs):
            single = {n: [d[run]] for n, d in icl[ext].items() if run in d}
            if len(single) >= 5:
                m["per_run_r"][run] = icl_metrics(single, lut)[0]["r"]
        orig = archived_leaf(ext)
        om = {n: (np.mean(cp) if (cp := clean_preds(v)) else 0.0) for n, v in orig.items()}
        common = [n for n in means[ext] if n in om]
        m["item_level_vs_original"] = {"n": len(common), "pearson": round(pearson([means[ext][n] for n in common], [om[n] for n in common]), 3),
                                       "mean_abs_diff": round(float(np.mean([abs(means[ext][n] - om[n]) for n in common])), 3)}
        out["60-shot" if ext == 0 else "1000-shot"] = m
    # 0-shot -> ICL gain on the 150 test molecules, paired bootstrap over molecules
    if zs and N_EXT in means:
        names = [n for n in means[N_EXT] if n in zs and any(not math.isnan(p) for p in zs[n])]
        y = np.array([lut[n] for n in names])
        m0 = np.array([np.mean([p for p in zs[n] if not math.isnan(p)]) for n in names])
        rng = np.random.default_rng(SEED)
        for ext in [e for e in EXTS if e in means]:
            mi = np.array([means[ext][n] for n in names])
            gains = []
            for _ in range(N_BOOT):
                idx = rng.integers(0, len(names), len(names))
                if np.std(mi[idx]) > 0 and np.std(m0[idx]) > 0:
                    gains.append(pearson(mi[idx], y[idx]) - pearson(m0[idx], y[idx]))
            out[f"gain_{'60' if ext == 0 else '1000'}shot_minus_0shot_on_test150"] = {
                "n": len(names), "r_0shot_test150": round(100 * pearson(m0, y), 1), "r_icl": round(100 * pearson(mi, y), 1),
                "gain": round(100 * (pearson(mi, y) - pearson(m0, y)), 1),
                "ci": [round(100 * float(np.percentile(gains, 2.5)), 1), round(100 * float(np.percentile(gains, 97.5)), 1)]}
    out["served"] = {"models": sorted({r.get("model_served") for r in res.values() if r.get("model_served")}),
                     "n_fingerprints": len({r.get("system_fingerprint") for r in res.values() if r.get("system_fingerprint")})}
    if res:
        RUN.mkdir(parents=True, exist_ok=True)
        (RUN / "result.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    else:
        print("no archived calls in", RUN, "- run --run first")
    o = out["original"]
    if "zeroshot" in out:
        z = out["zeroshot"]
        print(f"0-shot   : re-run r = {z['pearson_r']} R2 = {z['r2']} (n={z['n']}); exact3 {z['exact3']['pct']} %, R21 {z['R21_pct']} %, R32 {z['R32_pct']} % "
              f"| original r = {o['zeroshot']['pearson_r']}, exact3 {o['zeroshot']['exact3']['pct']} %, R21 {o['zeroshot']['R21_pct']} %")
    for k in ("60-shot", "1000-shot"):
        if k in out:
            m, om = out[k], o["icl"][k]["rescored"]
            print(f"{k:9s}: re-run r = {m['r']} CI {m['ci']} per-run {m['per_run_r']} (valid {m['n_pred_valid']}/{m['n_pred_total']}) "
                  f"| original r = {om['r']} CI {om['ci']} | item-level vs original: {m['item_level_vs_original']}")
    for k in out:
        if k.startswith("gain_"):
            print(f"{k}: {out[k]}")
    print("served:", out["served"], "| truncated replies:", truncated, "| split:", split["mode"])
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--runs", type=int, default=NUM_RUNS, help="runs per ICL configuration (paper: 2; card allows 3)")
    ap.add_argument("--zs-molecules", type=int, default=None, help="zero-shot phase on a seeded random subset of this many molecules (default: all)")
    ap.add_argument("--zs-last", action="store_true", help="run the zero-shot phase after the in-context predictions (cap-stopped runs then lose zero-shot calls first)")
    a = ap.parse_args()
    if a.check:
        original()
    if a.dry_run:
        do_run(True, a.workers, a.runs, a.zs_molecules, a.zs_last)
    if a.run:
        do_run(False, a.workers, a.runs, a.zs_molecules, a.zs_last)
    if a.analyze:
        analyze(a.runs)


if __name__ == "__main__":
    main()
