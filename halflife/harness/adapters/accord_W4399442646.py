"""Card W4399442646 - ACCORD: Closing the Commonsense Measurability Gap (Roewer-Despres, Feng, Zhu, Rudzicz;
arXiv 2406.02804v2). Repository francois-rd/accord at dd75a4e (external/repos/W4399442646/francois-rd__accord).
Live arm gpt-4o-2024-05-13, the snapshot the paper itself benchmarked (App. I.2, configs/.../arguments/gpt-4o-2024-05-13.txt);
OpenAI shutdown 2026-10-23.

CLAIM (card): on ACCORD-CSQA Small 0-5 (2,864 zero-shot 5-option items) gpt-4o answers FACTUAL variants significantly
better than the ceteris-paribus ANTI-FACTUAL variants at every reasoning-hop count n and distractor count d, and
anti-factual accuracy falls below the 20% chance line once n exceeds its multi-hop capacity, with hops (not distractors)
dominating the degradation (Figure 3; Sec. 4). The paper prints NO per-cell table: Figure 3 is the only original value.

DECISIONS 2026-09-19 (project defaults, user delegated; mirrored into the card under decisions_2026_09_19): all 2,864
items; the paper's decoding untouched (max_tokens 20, API seed 314159, response_format json_object, NO temperature field
-> OpenAI default 1.0; no temperature-0 arm); 3 seeds (the paper ran one); items REGENERATED IN-REPO with random_seed
314159, because the frozen Codabench release is not downloadable anonymously (Files tab needs an account; GET
/api/datasets/<public_data key>/ -> HTTP 403), so no diff against it is possible; per-paper cap USD 25.

REFERENCE SERIES = Figure 3 GPT-4o, digitised exactly (runs/W4399442646/reference_series.json). The Codabench
leaderboard fallback does not exist - phase 5477 get_leaderboard returns an empty submissions list. The LaTeXML render
of v2 ships Figure 3 as SVG and its columns 1-2 are a grouped bar chart (px.bar, basic_pretty.yaml), so every bar is a
filled path: bar tops and the 0/50/100 y-ticks were read from SVG user-space geometry, not pixels. Every GPT-4o value
then has a unique integer pre-image over the Table 5 denominators (max |plotted - exact| 0.009 pp) and the plotted Wald
bars reproduce sqrt(p(1-p)/N) from those counts to within 0.003 pp, so the counts are recovered, not approximated:
factual by hop 458/465, 328/372, 191/279, 101/186, 47/93; anti-factual 416/465, 222/372, 79/279, 27/186, 14/93 - i.e.
anti-factual first drops below the 20% chance line at n=4. Judgment leans on direction and on that crossing first, on
per-bin values second.

THE REPOSITORY'S OWN CODE IS CALLED, NOT COPIED. items: src/main.py generate.{generic,relational,forest,group} +
prompt.dummy ... snapshot::ignore=false (the README's "Generating Official Benchmark Releases" recipe) by subprocess,
under runs/<card>/benchmark and never into the clone; sizes 0 and 1 need no generation step. prompts:
leaderboard/utils.py, the official starting-kit surfacer, with prefix_surfacer blanked exactly as
arguments/gpt-4o-2024-05-13.txt does, so the instruction appears only as the system message. parse:
accord.components.llm.SimpleLLMOutputParser (unparsed = FAILED). score: accord.commands.analyze.basic.base accuracy /
failed on AnswerLabels binned by the repository's own reasoning_hops / distractors; Wald SE is the paper's own
variation indicator.

  python adapters/accord_W4399442646.py --check      # offline: items, one exact request, parser+scorer on synthetic replies
  python adapters/accord_W4399442646.py --dry-run    # request list + token/cost estimate, no API calls
  python adapters/accord_W4399442646.py --run        # spends money, cap $25 -> runs/W4399442646/baseline_alive/
  python adapters/accord_W4399442646.py --analyze    # per-bin accuracy, bootstrap CI, chance test, judgment, run_meta.json
"""
import argparse, json, os, subprocess, sys, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, pricing_for, run_battery  # noqa: E402

CARD, HALF = "W4399442646", HERE.parent.parent
REPO = HALF / "external" / "repos" / CARD / "francois-rd__accord"
REPO_COMMIT = "dd75a4e0429877407b1059c617eee4a45c39fda0"
CFG = REPO / "configs" / "CSQA_and_ConceptNet"
RUN_ROOT, RUN = HALF / "runs" / CARD, HALF / "runs" / CARD / "baseline_alive"
GEN, SHIMS = RUN_ROOT / "benchmark", RUN_ROOT / "_shims"
CHECK_JSON, META = RUN_ROOT / "environment_check.json", RUN_ROOT / "run_meta.json"
REF_JSON = RUN_ROOT / "reference_series.json"   # digitised Figure 3 GPT-4o series, when one exists

MODEL, SEEDS, CAP, WORKERS = "gpt-4o-2024-05-13", 3, 25.0, 4
MAX_TOKENS, API_SEED, DRAW_SEED, N_BOOT = 20, 314159, 20260907, 2000
CHANCE, SIZES, ENCODING = 0.20, (0, 1, 2, 3, 4, 5), "o200k_base"
EXPECTED = {0: 74, 1: 186, 2: 372, 3: 558, 4: 744, 5: 930}          # paper Table 5 (App. E.1), total 2,864
WORDS = {0: 4700, 1: 28864, 2: 77756, 3: 145682, 4: 231834, 5: 337414}   # Table 5 "Number of Words w/ Prompt"
HOP_N = {1: 930, 2: 744, 3: 558, 4: 372, 5: 186}                   # Table 5 column totals = 2 x 93 x (6 - n)
CODABENCH = {"competition": "https://www.codabench.org/api/competitions/3160/",
             "public_data": "https://www.codabench.org/api/datasets/e42d606f-e587-4699-b7e9-fa1568cb2c6c/",
             "leaderboard": "https://www.codabench.org/api/phases/5477/get_leaderboard/"}
ANCHORS = {"factual_beats_antifactual": "'For any given n (Columns 1 and 3) or d (Columns 2 and 3) in Figure 3, factual "
                                        "reasoning significantly outperforms anti-factual reasoning.' (Sec. 4)",
           "below_chance": "'anti-factual performance quickly degrades to below random chance with only very moderate "
                           "scaling of reasoning complexity' (Sec. 4)",
           "hops_dominate": "'Reasoning hops are dominant while distractors' effect is negligible' (Figure 3 caption)",
           "extraction": "paper reports >99% answer-extraction success; FAILED table in App. E"}

now = lambda: datetime.now(timezone.utc).isoformat()
rel = lambda p: str(Path(p)).replace(str(HALF) + os.sep, "")


def _jd(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, np.bool_)):
        return float(o) if isinstance(o, np.floating) else bool(o)
    raise TypeError(type(o))


# ------------------------------------------------------------------ the repository, its shims and its generator
def shims():
    """Two import-time shims the repository needs on Windows; both are reported as frictions.
    plotly: accord.commands imports its figure modules at package import although no figure is made here.
    os.linesep: accord/io.py save_lines() appends os.linesep in text mode -> '\\r\\r\\n' on Windows, and every
    loader then splits on the bare CR and hits a blank line (JSONDecodeError). The generator cannot run without it."""
    (SHIMS / "plotly" / "express").mkdir(parents=True, exist_ok=True)
    w = lambda p, s: (SHIMS / p).write_text(s, encoding="utf-8")
    stub = "def __getattr__(n):\n    return type(n, (), {})\n"
    w("plotly/__init__.py", '__version__ = "stub (harness/adapters/accord_W4399442646.py)"\n')
    w("plotly/graph_objects.py", stub)
    w("plotly/subplots.py", stub)
    w("plotly/express/__init__.py", "from . import colors\n\n\n" + stub)
    w("plotly/express/colors.py", stub)
    w("sitecustomize.py", "import os\n\n# accord/io.py save_lines() appends os.linesep in text mode; on Windows that\n"
                          "# doubles the CR and every loader then hits a blank line.\nos.linesep = \"\\n\"\n")
    return SHIMS


def repo_env():
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(shims()), str(REPO / "src"), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    return env


def repo_import():
    """accord.* imported in-process (io, parser, scorer). Needs the plotly shim on sys.path."""
    for p in (str(shims()), str(REPO / "src")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import accord.io as aio                                                    # noqa: E402
    from accord.base import QAData, QAGroup                                    # noqa: E402
    from accord.commands.analyze.basic import base as scorer                   # noqa: E402
    from accord.components import AnswerLabels                                 # noqa: E402
    from accord.components.llm import SimpleLLMOutputParser                    # noqa: E402
    return aio, QAData, QAGroup, scorer, AnswerLabels, SimpleLLMOutputParser


def utils_py():
    """leaderboard/utils.py - the Codabench starting-kit surfacer - loaded by path (it is not a package)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("accord_leaderboard_utils", REPO / "leaderboard" / "utils.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main_py(args, log, ckpt):
    """One `python src/main.py ...` invocation with cwd = configs/CSQA_and_ConceptNet, as the README prescribes.
    checkpoint_dir is unique per step: SimpleQACheckpointManager skips every QAData already marked, and the
    repository's default job_id=-1 makes consecutive steps silently no-op (and writes into the clone)."""
    base = [f"all_results_dir={(GEN / 'results').as_posix()}", f"generic_trees_dir={(GEN / 'generic_trees').as_posix()}",
            f"checkpoint_dir={(GEN / 'ckpt' / ckpt).as_posix()}", "verbose=false"]
    cmd = [sys.executable, str(REPO / "src" / "main.py")] + args + base
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n$ {' '.join(cmd)}\n")
        f.flush()
        r = subprocess.run(cmd, cwd=str(CFG), env=repo_env(), stdout=f, stderr=subprocess.STDOUT, text=True)
    if r.returncode:
        sys.exit(f"{' '.join(args[:1])} (size step {ckpt}) failed with exit {r.returncode}; see {rel(log)}")


def snapshot_path(s):
    return GEN / "snapshots" / f"accord_csqa_small_{s}.jsonl"


def generate_size(s):
    """Regenerate ACCORD CSQA Small-<s> in-repo (random_seed 314159). Cached: returns immediately once the
    snapshot file holds the Table 5 count. Sizes 0 and 1 fall out of the committed preprocessing; 2-5 need the
    four combinatorial steps (measured: size 2 forest ~20 min on this machine, later sizes grow steeply)."""
    p = snapshot_path(s)
    if p.exists() and len(read_jsonl(p)) == EXPECTED[s]:
        return p
    out = GEN / "results" / "CSQA_and_ConceptNet"
    out.mkdir(parents=True, exist_ok=True)
    for f in ("relations.csv", "reductions.csv"):                    # committed inputs, copied out of the clone
        if not (out / f).exists():
            (out / f).write_bytes((REPO / "data" / "results" / "CSQA_and_ConceptNet" / f).read_bytes())
    log, flt = GEN / "generate.log", f"--filter-path=filters/filter_{s}.yaml"
    if s >= 2:
        for step in ("generate.generic", "generate.relational", "generate.forest.csqa.conceptnet",
                     "generate.group.csqa.conceptnet"):
            a = [step, f"tree_size={s}"] + ([flt] if step != "generate.group.csqa.conceptnet" else [])
            main_py(a, log, f"{step}_{s}")
    a = ["prompt.dummy.csqa.conceptnet", "llm=dummy", "snapshot::ignore=false", f"tree_size={s}",
         "default_num_llm_prompts=1", flt, f"snapshot_dir={(GEN / 'snapshots').as_posix()}",
         f"snapshots_file={p.as_posix()}"] + (["--surfacer-path=surfacer_tree_size_0.yaml"] if s == 0 else [])
    main_py(a, log, f"snapshot_{s}")
    n = len(read_jsonl(p))
    if n != EXPECTED[s]:
        sys.exit(f"size {s}: regenerated {n} instances, Table 5 says {EXPECTED[s]} (see {rel(log)})")
    return p


def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def qa_gold():
    """qa_id -> (correct label, answer_choices) from the committed data/CSQA/converted/dev_13_314159.jsonl."""
    aio, QAData = repo_import()[:2]
    qa = aio.load_dataclass_jsonl(str(REPO / "data" / "CSQA" / "converted" / "dev_13_314159.jsonl"), QAData)
    return {q.identifier: q for q in qa}


def hops_map(s):
    """group id -> reasoning hops, by the repository's own rule (accord.components.analysis.reasoning_hops):
    for size < 2 the hop count is the size; otherwise it is the reasoning_hops of any InstantiationData of the group."""
    if s < 2:
        return None
    aio, _, QAGroup = repo_import()[:3]
    out = {}
    for qa_dir in sorted((GEN / "results" / "CSQA_and_ConceptNet" / "qa_data" / str(s)).iterdir()):
        forest = aio.load_forest_jsonl(str(qa_dir / "forests" / "families.jsonl"), str(qa_dir / "forests" / "data.jsonl"))
        for g in aio.load_dataclass_jsonl(str(qa_dir / "groups" / "groups.jsonl"), QAGroup):
            out[(qa_dir.name, g.identifier)] = forest.data_map[next(iter(g.data_ids.values()))].reasoning_hops
    return out


# ------------------------------------------------------------------ items, prompts, requests
def surfacer(mod, s, blank_prefix=True):
    """The starting-kit InstanceSurfacer with the paper's CSQA parameters. arguments/gpt-4o-2024-05-13.txt sets
    prefix_surfacer.prefix='' and .text='', so the instruction is NOT repeated in the user turn for this arm."""
    forms = None if s == 0 else mod.load_surface_forms(str(GEN / "results" / "CSQA_and_ConceptNet" / "reductions.csv"))
    instr = "" if blank_prefix else (mod.SimpleCSQAPreprocessor.DEFAULT_BASELINE_INSTRUCTION_PROMPT if s == 0
                                     else mod.SimpleCSQAPreprocessor.DEFAULT_MAIN_INSTRUCTION_PROMPT)
    ordering = None if forms is None else mod.OrderingSurfacer(
        prefix="Statements:\n", statement_separator="\n",
        statement_surfacer=mod.StatementSurfacer(prefix="- ", term_surfacer=mod.TermSurfacer(prefix="[", suffix="]"), forms=forms))
    return mod.InstanceSurfacer(
        prefix="", surfacer_separator="\n",
        prefix_surfacer=mod.TextSurfacer(prefix="" if blank_prefix else "Instructions:\n", text=instr),
        ordering_surfacer=ordering,
        qa_data_surfacer=mod.QADataSurfacer(prefix="Question:\n", question_answer_separator="\n",
                                            answer_choice_separator="    ", answer_choice_formatter="{}: {}"),
        suffix_surfacer=mod.TextSurfacer(prefix="Answer:\n", text=""))


def system_prompt(s):
    f = "openai_tree_size_0.yaml" if s == 0 else "openai.yaml"
    return yaml.safe_load((CFG / f).read_text(encoding="utf-8"))["system_prompt"]


def pairing_key(item):
    """The 93 pairings are (CSQA item, pairing template). The pairing statement occurs once per answer tree; the term
    that is identical across those trees is the hand-crafted pairing term and the side it sits on is the `placement`
    column of data/CSQA/paired/*.csv, so (qa_id, placement, pairing term, flip_negative) names the template. The
    statement's surface form cannot be used: the reducer inflects it per tree (does/do). remove_duplicate_templates
    drops the statement from one tree in 12 of the 2,864 instances; the remaining four still fix the term. The term is
    case- and underscore-normalised because size 1 keeps the raw CSV spelling ('powering_Apaches') while sizes >= 2
    carry the lowercase ConceptNet spelling ('powering apaches'); relation_type is part of the key because one CSQA
    item registers two pairing templates on the same term with different relations. Yields exactly 93 keys."""
    if item["pairing"] is None:
        return (item["qa_id"], "no-context")
    sts = [v[item["pairing"]["id"]] for v in item["statements"].values() if item["pairing"]["id"] in v]
    src = len({s["source_term"] for s in sts}) == 1
    term = sts[0]["source_term"] if src else sts[0]["target_term"]
    return (item["qa_id"], "SOURCE" if src else "TARGET", term.replace("_", " ").lower(),
            item["pairing"]["relation_type"], item["pairing"]["flip_negative"])


def load_items(sizes, generate=True):
    """Every regenerated instance with its prompt, gold label, bin and pairing cluster."""
    mod, golds, rows = utils_py(), qa_gold(), []
    for s in sizes:
        p = generate_size(s) if generate else snapshot_path(s)
        if not p.exists():
            continue
        surf, hops, sysp = surfacer(mod, s), hops_map(s), system_prompt(s)
        for item in read_jsonl(p):
            g = golds[item["qa_id"]]
            md = mod.MetaData(item)
            n = s if s < 2 else hops[(item["qa_id"], item["id"].rsplit("_", 2)[0])]
            rows.append({"rid": f"{s}|{item['qa_id']}|{item['id']}", "size": s, "qa_id": item["qa_id"],
                         "chosen": item["label"], "correct": g.correct_answer_label, "hops": n, "distractors": s - n,
                         "factual": item["label"] == g.correct_answer_label, "pairing": pairing_key(item),
                         "pairing_stmt_trees": sum(1 for v in item["statements"].values()
                                                   if (item["pairing"] or {}).get("id") in v),
                         "system": sysp, "user": surf(md), "choices": item["answer_choices"]})
    return rows


def body(row):
    """The repository's own OpenAI body: openai.yaml query_params merged with arguments/gpt-4o-2024-05-13.txt
    (coma's CLI override merges, it does not replace - App. E.3 confirms max_tokens 20 was in force).
    NO temperature and NO top_p field: the paper used 'default hyper-parameters', i.e. the API default 1.0."""
    return {"model": MODEL, "messages": [{"role": "system", "content": row["system"]}, {"role": "user", "content": row["user"]}],
            "max_tokens": MAX_TOKENS, "seed": API_SEED, "response_format": {"type": "json_object"}}


def build_requests(rows, seeds=SEEDS):
    return [{"id": r["rid"], "seed_idx": s,
             "meta": {k: (list(r[k]) if k == "pairing" else r[k]) for k in
                      ("size", "qa_id", "chosen", "correct", "hops", "distractors", "factual", "pairing")},
             "body": body(r)} for s in range(seeds) for r in rows]


def estimate(rows, seeds=SEEDS):
    """tiktoken on the rendered prompts for the sizes on disk; Table 5 word counts extrapolate the missing sizes."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding(ENCODING)
    except Exception:
        return None
    tok, words, have = {}, {}, sorted({r["size"] for r in rows})
    for s in have:
        rs = [r for r in rows if r["size"] == s]
        tok[s] = sum(3 + sum(3 + len(enc.encode(m["role"])) + len(enc.encode(m["content"])) for m in body(r)["messages"]) for r in rs)
        words[s] = sum(len((r["system"] + " " + r["user"]).split()) for r in rs)
    ratio = (sum(tok[s] for s in have) / sum(words[s] for s in have)) if have else 1.35
    per_size = {s: {"items": EXPECTED[s], "measured": s in tok,
                    "tokens_in": tok.get(s, int(round(WORDS[s] * ratio)))} for s in SIZES}
    tin = seeds * sum(v["tokens_in"] for v in per_size.values())
    n_out = len(enc.encode('{"answer": "A"}'))
    calls, pr = seeds * sum(EXPECTED.values()), pricing_for(MODEL)
    return {"calls": calls, "tokens_in": tin, "tokens_out_expected": n_out * calls, "tokens_out_max": MAX_TOKENS * calls,
            "usd_expected": tin / 1e6 * pr["input"] + n_out * calls / 1e6 * pr["output"],
            "usd_max_tokens_bound": tin / 1e6 * pr["input"] + MAX_TOKENS * calls / 1e6 * pr["output"],
            "tokens_per_word": ratio, "per_size": per_size, "pricing": pr, "encoding": ENCODING, "seeds": seeds,
            "sizes_measured": have, "sizes_extrapolated": [s for s in SIZES if s not in tok]}


# ------------------------------------------------------------------ scoring, statistics, judgment
def score(records, scorer, AnswerLabels, bin_key):
    """The repository's own accuracy()/failed() over its own bin structure: bin -1 is the no-context baseline."""
    results = {}
    for r in records:
        b = -1 if r["size"] == 0 else r[bin_key]
        results.setdefault(b, []).append(AnswerLabels(r["parsed"], r["chosen"], r["correct"]))
    acc, fail = scorer.AnalysisTable(MODEL, None, None), scorer.AnalysisTable(MODEL, None, None)
    scorer.accuracy(acc, results)
    scorer.failed(fail, results)
    return acc, fail


def cluster_bootstrap(records, bins, n_boot=N_BOOT, seed=DRAW_SEED):
    """95% CI for factual, anti-factual and the gap in every hop bin, resampling the 93 pairings (the paper's own
    dispersion unit) with replacement. Records carry one row per item per seed; seeds are averaged first."""
    clusters = sorted({r["pairing"] for r in records}, key=str)
    idx = {c: i for i, c in enumerate(clusters)}
    f = {b: np.zeros((len(clusters), 2)) for b in bins}
    a = {b: np.zeros((len(clusters), 2)) for b in bins}
    for r in records:
        b = r["hops"]
        if b in bins:
            (f if r["factual"] else a)[b][idx[r["pairing"]]] += (int(r["parsed"] == r["chosen"]), 1)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(clusters), (n_boot, len(clusters)))
    out = {}
    for b in bins:
        fs, as_ = f[b][draws].sum(axis=1), a[b][draws].sum(axis=1)
        pf = np.divide(fs[:, 0], fs[:, 1], out=np.full(n_boot, np.nan), where=fs[:, 1] > 0)
        pa = np.divide(as_[:, 0], as_[:, 1], out=np.full(n_boot, np.nan), where=as_[:, 1] > 0)
        q = lambda v: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
        out[b] = {"f_ci95": q(pf), "af_ci95": q(pa), "gap_ci95": q(pf - pa),
                  "af_below_chance_prob": float(np.nanmean(pa < CHANCE))}
    return {"bins": out, "n_clusters": len(clusters), "n_boot": n_boot, "seed": seed, "unit": "pairing"}


def wald_gap(f, af):
    """Two-proportion z on the repository's own Wald standard errors (its variation indicator)."""
    se = (f[1] ** 2 + af[1] ** 2) ** 0.5
    z = (f[0] - af[0]) / se if se > 0 else float("nan")
    from math import erfc
    return {"gap": f[0] - af[0], "z": z, "p": float(erfc(abs(z) / 2 ** 0.5)) if se > 0 else None, "se": se}


def crossing(af_by_bin):
    """Smallest n at which anti-factual accuracy sits below the 20% chance line."""
    for n in sorted(af_by_bin):
        if af_by_bin[n] is not None and af_by_bin[n] < CHANCE:
            return n
    return None


def judge(gaps, cross, ref_cross, degrades):
    """ANALYSIS_PLAN section 1 as the card instantiates it (judgment.rule)."""
    pos = [g for g in gaps.values() if g["gap"] > 0 and (g["p"] is not None and g["p"] < 0.05)]
    if any(g["gap"] <= 0 for g in gaps.values()) or not degrades:
        return "사망 (dead)", "the factual advantage vanishes or reverses in some hop bin, or anti-factual accuracy no longer degrades with n"
    if len(pos) == len(gaps) and cross is not None and ref_cross is not None and abs(cross - ref_cross) <= 1:
        return "생존 (survived)", f"gap positive and Wald-significant at every n, chance crossing n={cross} within one hop of Figure 3 (n={ref_cross})"
    if len(pos) == len(gaps) and ref_cross is None and cross is not None and cross <= 3:
        return "생존 (survived)", (f"gap positive and Wald-significant at every n and anti-factual accuracy crosses below chance at n={cross}, "
                                 "which matches the paper's 'very moderate scaling' anchor; no digitised Figure 3 series to compare hop-for-hop")
    return "부분 생존 (partial)", (f"the factual-over-anti-factual gap survives (significant in {len(pos)}/{len(gaps)} bins) but the "
                                f"below-chance crossing moved or disappeared (ours n={cross}, reference n={ref_cross})")


# ------------------------------------------------------------------ reference series
def probe_codabench(timeout=20):
    """Anonymous reachability of the frozen release and of the leaderboard, recorded as provenance."""
    out = {}
    for k, url in CODABENCH.items():
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                d = r.read()
                out[k] = {"status": r.status, "bytes": len(d)}
                if k == "leaderboard":
                    out[k]["submissions"] = len(json.loads(d).get("submissions", []))
        except urllib.error.HTTPError as e:
            out[k] = {"status": e.code, "error": e.reason}
        except Exception as e:
            out[k] = {"status": None, "error": f"{type(e).__name__}: {e}"}
    return out


def reference():
    """Original GPT-4o series. The leaderboard is empty and the release is behind a login, so the only source is a
    digitisation of Figure 3, dropped into runs/<card>/reference_series.json by a human-verified reading."""
    if REF_JSON.exists():
        r = json.loads(REF_JSON.read_text(encoding="utf-8"))
        r.setdefault("available", True)
        return r
    return {"available": False, "f_acc": None, "af_acc": None, "af_below_chance_from_hop": None,
            "provenance": "not digitised: the paper prints no table, the Codabench release needs a logged-in account "
                          "(HTTP 403 anonymously) and the leaderboard holds zero submissions. Drop a digitised series "
                          f"into {rel(REF_JSON)} with keys f_acc/af_acc (hop -> accuracy), af_below_chance_from_hop, "
                          "method and reading_uncertainty_pp to enable hop-for-hop comparison.",
            "qualitative_anchors": ANCHORS}


# ------------------------------------------------------------------ --check
SYNTHETIC = {"oracle": "always the chosen (context-supported) label -> 100% in every bin",
             "gold_parrot": "always the CSQA factual label -> 100% factual, 0% anti-factual (the parroting extreme)",
             "always_a": "always {\"answer\": \"A\"} -> roughly chance",
             "prose": "'The answer is <chosen>.' - no JSON object; must still score 100% via the parser cascade",
             "refusal": "'I cannot answer that.' -> unparsed, counted FAILED and incorrect"}


def synthetic(row, kind):
    lab = row["correct"] if kind == "gold_parrot" else "A" if kind == "always_a" else row["chosen"]
    return {"oracle": '{"answer": "%s"}' % lab, "gold_parrot": '{"answer": "%s"}' % lab,
            "always_a": '{"answer": "A"}', "prose": "The answer is %s." % lab,
            "refusal": "I cannot answer that."}[kind]


def check(sizes=SIZES, generate=True, verbose=True):
    aio, QAData, QAGroup, scorer, AnswerLabels, Parser = repo_import()
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    rows = load_items(sizes, generate=generate)
    have = sorted({r["size"] for r in rows})
    if not rows:
        sys.exit(f"no items available for sizes {sizes}; run --check without --no-generate to regenerate them")
    golds, parser, mod = qa_gold(), Parser(), utils_py()
    counts = {s: sum(r["size"] == s for r in rows) for s in have}
    pairings = {r["pairing"] for r in rows if r["size"] > 0}
    cells = {}                       # the Small release is "one instance per pairing per hop per distractor" x2 variants
    for r in (x for x in rows if x["size"] > 0):
        cells[(r["pairing"], r["hops"], r["distractors"])] = cells.get((r["pairing"], r["hops"], r["distractors"]), 0) + 1
    per_bin = {}
    for r in rows:
        k = ("f" if r["factual"] else "af", r["hops"], r["distractors"])
        per_bin[k] = per_bin.get(k, 0) + 1

    # one exact request, rendered by the starting-kit surfacer, cross-checked against the experiment-side YAML config
    ex = next(r for r in rows if r["size"] == max(have))
    ycfg = yaml.safe_load((CFG / "surfacer.yaml").read_text(encoding="utf-8"))
    yaml_match = (ycfg["surfacer_separator"] == "\n" and ycfg["template_sequence_surfacer"]["prefix"] == "Statements:\n"
                  and ycfg["template_sequence_surfacer"]["template_separator"] == "\n"
                  and ycfg["qa_data_surfacer"]["prefix"] == "Question:\n" and ycfg["suffix_surfacer"]["prefix"] == "Answer:\n"
                  and ycfg["template_sequence_surfacer"]["template_surfacer"]["prefix"] == "- ")
    args_txt = (CFG / "arguments" / f"{MODEL}.txt").read_text(encoding="utf-8").strip().splitlines()

    # parser and per-bin scorer on synthetic replies
    runs = {}
    for kind in SYNTHETIC:
        recs = [dict(r, parsed=parser(synthetic(r, kind), golds[r["qa_id"]])) for r in rows]
        acc, fail = score(recs, scorer, AnswerLabels, "hops")
        runs[kind] = {"baseline_f_acc": acc.baseline,
                      "f_acc": {k: v[0] for k, v in acc.data.get("f_acc", {}).items()},
                      "af_acc": {k: v[0] for k, v in acc.data.get("af_acc", {}).items()},
                      "f_failed": {k: v[0] for k, v in fail.data.get("f_fails", {}).items()},
                      "parsed": sum(r["parsed"] is not None for r in recs) / max(len(recs), 1)}
    est = estimate(rows)
    out = {"card_id": CARD, "checked_utc": now(), "python": sys.version.split()[0], "model": MODEL,
           "repo": {"path": rel(REPO), "head": head, "card_commit": REPO_COMMIT, "head_matches_card": head == REPO_COMMIT,
                    "imported": ["src/accord/io.py", "src/accord/components/llm.py", "src/accord/commands/analyze/basic/base.py",
                                 "leaderboard/utils.py"],
                    "subprocess": "src/main.py generate.* and prompt.dummy.csqa.conceptnet (README 'Generating Official Benchmark Releases')",
                    "shims": {"plotly": "import-time stub; accord.commands imports plotly at package import although no figure is drawn",
                              "os.linesep": "forced to '\\n'; io.save_lines() otherwise writes '\\r\\r\\n' on Windows and every loader fails",
                              "coma": "requirements.txt pins coma>=1.0.1; PyPI now serves 3.0.1, whose API no longer has "
                                      "coma.register/initiate/forget - src/main.py does not import. Pinned to coma==1.0.1 (2022-05-23)."}},
           "items": {"source": "regenerated in-repo (random_seed 314159, filters/filter_<size>.yaml, default_num_llm_prompts=1)",
                     "codabench_release": "not used: anonymous download unavailable", "written_to": rel(GEN / "snapshots"),
                     "sizes_present": have, "counts": counts, "expected_table5": EXPECTED,
                     "counts_match_table5": all(counts.get(s) == EXPECTED[s] for s in have),
                     "total_present": len(rows), "total_expected": sum(EXPECTED.values()),
                     "distinct_pairings": len(pairings), "pairings_expected": 93,
                     "pairings_note": "counted over sizes >= 1; the no-context baseline has no pairing statement. "
                                      "data/CSQA/paired/dev_13_314159/*.csv holds exactly 93 rows with description "
                                      "'pairing' across the 74 files, which is the independent count",
                     "instances_with_a_deduplicated_pairing_statement":
                         sum(1 for r in rows if r["size"] > 0 and r["pairing_stmt_trees"] < 5),
                     "pairing_x_hop_x_distractor_cells": len(cells),
                     "cells_holding_exactly_one_factual_and_one_anti_factual": sum(1 for v in cells.values() if v == 2),
                     "per_bin_counts": {f"{k[0]}|n={k[1]}|d={k[2]}": v for k, v in sorted(per_bin.items())},
                     "hop_bin_totals_expected": HOP_N},
           "prompt": {"renderer": "leaderboard/utils.py InstanceSurfacer (Codabench starting kit)",
                      "experiment_side_yaml_parameters_match": yaml_match,
                      "prefix_surfacer_blanked": True, "arguments_file": args_txt,
                      "system_prompt_size0": system_prompt(0), "system_prompt_main": system_prompt(1),
                      "example": {"rid": ex["rid"], "size": ex["size"], "hops": ex["hops"], "distractors": ex["distractors"],
                                  "factual": ex["factual"], "body": body(ex)},
                      "parameters": {"max_tokens": MAX_TOKENS, "seed": API_SEED, "response_format": "json_object",
                                     "temperature": "not sent (OpenAI default 1.0, App. E.3)", "top_p": "not sent"}},
           "parser": {"class": "accord.components.llm.SimpleLLMOutputParser (default cascade)",
                      "examples": {t: parser(t, golds[ex["qa_id"]]) for t in
                                   ['{"answer": "B"}', '{"answer":"b"}', "B", 'Answer: B', '{"answer": "%s"}' % ex["choices"]["B"],
                                    "The answer is B.", "I cannot answer that.", ""]}},
           "scorer": {"code": "accord.commands.analyze.basic.base.accuracy / failed; bins from components.analysis "
                              "reasoning_hops / distractors; Wald SE sqrt(p(1-p)/n); baseline bin -1 = ACCORD0 (74 items)",
                      "synthetic_definitions": SYNTHETIC, "synthetic_runs": runs},
           "reference_series": {**reference(), "codabench_probe": probe_codabench(),
                                "leaderboard_note": "competition 3160 phase 5477 returns an empty submissions list: the "
                                                    "leaderboard carries no GPT-4o entry to compare against"},
           "estimate": est, "decisions": "card key decisions_2026_09_19", "chance": CHANCE}
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=_jd), encoding="utf-8")
    if verbose:
        print(f"[{CARD} --check] repository {rel(REPO)} HEAD {head[:7]} ({'matches' if head == REPO_COMMIT else 'DIFFERS FROM'} the card)")
        print(f"  items regenerated in-repo (seed 314159): sizes {have}, counts {counts}, total {len(rows)}/{sum(EXPECTED.values())}; "
              f"Table 5 match {out['items']['counts_match_table5']}; distinct pairings {len(pairings)} (expected 93); "
              f"pairing x hop x distractor cells holding exactly one factual + one anti-factual instance: "
              f"{out['items']['cells_holding_exactly_one_factual_and_one_anti_factual']}/{len(cells)}")
        print(f"  prompts rendered by leaderboard/utils.py; experiment-side surfacer.yaml parameters identical: {yaml_match}; "
              f"prefix blanked per arguments/{MODEL}.txt -> instruction only in the system message")
        print(f"  parser probes: {json.dumps(out['parser']['examples'], ensure_ascii=False)}")
        print(f"  repository scorer on synthetic replies (factual / anti-factual accuracy by hop):")
        for k, v in runs.items():
            print(f"    {k:12s} baseline {v['baseline_f_acc']}  f {[round(v['f_acc'].get(str(n), float('nan')), 3) for n in sorted(HOP_N)]}"
                  f"  af {[round(v['af_acc'].get(str(n), float('nan')), 3) for n in sorted(HOP_N)]}  parsed {v['parsed']:.3f}")
        cb = out["reference_series"]["codabench_probe"]
        print(f"  Codabench: public_data {cb['public_data']['status']}, leaderboard submissions "
              f"{cb['leaderboard'].get('submissions')} -> reference series available: {out['reference_series']['available']}")
        if est:
            print(f"  cost at {SEEDS} seeds: {est['calls']} calls, {est['tokens_in']:,} prompt tokens "
                  f"(measured sizes {est['sizes_measured']}, Table 5 extrapolation for {est['sizes_extrapolated']}) -> ${est['usd_expected']:.2f}")
        print(f"  -> {rel(CHECK_JSON)}")
    return out


# ------------------------------------------------------------------ --dry-run / --run
def dry_run(sizes=SIZES, seeds=SEEDS, cap=CAP, generate=True):
    rows = load_items(sizes, generate=generate)
    reqs, est = build_requests(rows, seeds), estimate(rows, seeds)
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "requests.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs), encoding="utf-8")
    bat = run_battery(reqs, RUN, cap, dry_run=True, label=f"{CARD} baseline_alive")
    print(f"[dry-run] {len(rows)} items x {seeds} seeds = {len(reqs)} requests written to {rel(RUN / 'requests.jsonl')} "
          f"(full benchmark: {sum(EXPECTED.values())} x {seeds} = {sum(EXPECTED.values()) * seeds})")
    if est:
        print(f"[dry-run] tiktoken {ENCODING}: {est['tokens_in']:,} prompt tokens, {est['tokens_out_expected']:,} expected output "
              f"tokens -> ${est['usd_expected']:.2f}; max_tokens bound ${est['usd_max_tokens_bound']:.2f} "
              f"(${est['pricing']['input']}/${est['pricing']['output']} per 1M)")
        print(f"[dry-run] per size (items, prompt tokens, measured?): "
              f"{ {s: (v['items'], v['tokens_in'], v['measured']) for s, v in est['per_size'].items()} }")
    print(f"[dry-run] battery chars/4 estimate on what is on disk: ${bat['est_usd']:.2f}; cap ${cap:.2f}; card budget $18; no API calls made")
    return {"requests_on_disk": len(reqs), "estimate": est, "battery_est_usd": bat["est_usd"]}


def run(sizes=SIZES, seeds=SEEDS, cap=CAP, workers=WORKERS):
    rows = load_items(sizes)
    if len(rows) != sum(EXPECTED.values()):
        sys.exit(f"refusing to run: {len(rows)} of {sum(EXPECTED.values())} items regenerated; finish --check first")
    reqs = build_requests(rows, seeds)
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "run_config.json").write_text(json.dumps(
        {"card_id": CARD, "model": MODEL, "items": len(rows), "seeds": seeds, "calls": len(reqs), "cap_usd": cap,
         "max_tokens": MAX_TOKENS, "api_seed": API_SEED, "response_format": "json_object",
         "temperature": "not sent (OpenAI default 1.0)", "repo_commit": REPO_COMMIT, "estimate": estimate(rows, seeds),
         "built_utc": now(), "decisions": "card key decisions_2026_09_19"}, indent=2, default=_jd), encoding="utf-8")
    return run_battery(reqs, RUN, cap, workers=workers, label=f"{CARD} baseline_alive")


# ------------------------------------------------------------------ --analyze
def analyze(sizes=SIZES, seeds=SEEDS):
    res = load_results(RUN)
    if not res:
        print(f"no archived calls in {rel(RUN)}; run --run first")
        return None
    aio, QAData, QAGroup, scorer, AnswerLabels, Parser = repo_import()
    rows = {r["rid"]: r for r in load_items(sizes, generate=False)}
    golds, parser = qa_gold(), Parser()
    env = json.loads(CHECK_JSON.read_text(encoding="utf-8")) if CHECK_JSON.exists() else {}
    budget = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    recs, served, fps, finish = [], set(), set(), {}
    for (rid, sidx), rec in res.items():
        ch = ((rec.get("response") or {}).get("choices") or [{}])[0]
        txt = (ch.get("message") or {}).get("content") or ""
        served.add(rec.get("model_served")); fps.add(rec.get("system_fingerprint"))
        finish[ch.get("finish_reason")] = finish.get(ch.get("finish_reason"), 0) + 1
        r = rows.get(rid)
        if r is not None:
            recs.append(dict(r, seed_idx=sidx, text=txt, parsed=parser(txt, golds[r["qa_id"]])))
    by_seed = {}
    for r in recs:
        by_seed.setdefault(r["seed_idx"], []).append(r)
    complete = sorted(s for s, v in by_seed.items() if len(v) == len(rows))
    if not complete:
        print(f"no complete seed (archived per seed: { {s: len(v) for s, v in by_seed.items()} }); cannot judge")
        return None
    per_seed, hop_rows, dis_rows = {}, {}, {}
    for s in complete:
        acc, fail = score(by_seed[s], scorer, AnswerLabels, "hops")
        accd, _ = score(by_seed[s], scorer, AnswerLabels, "distractors")
        per_seed[s] = {"baseline": acc.baseline, "hops": {"f": acc.data["f_acc"], "af": acc.data["af_acc"]},
                       "distractors": {"f": accd.data["f_acc"], "af": accd.data["af_acc"]},
                       "failed": {"f": fail.data["f_fails"], "af": fail.data["af_fails"]}}
    med = lambda vs: float(np.median(vs))
    present = lambda k, b: all(str(b) in per_seed[s][k]["f"] and str(b) in per_seed[s][k]["af"] for s in complete)
    for n in (b for b in sorted(HOP_N) if present("hops", b)):
        f = [per_seed[s]["hops"]["f"][str(n)] for s in complete]
        a = [per_seed[s]["hops"]["af"][str(n)] for s in complete]
        hop_rows[n] = {"f_acc": med([x[0] for x in f]), "af_acc": med([x[0] for x in a]),
                       "f_se": med([x[1] for x in f]), "af_se": med([x[1] for x in a]),
                       "f_per_seed": [x[0] for x in f], "af_per_seed": [x[0] for x in a], "n_items": HOP_N[n]}
        hop_rows[n].update(wald_gap((hop_rows[n]["f_acc"], hop_rows[n]["f_se"]), (hop_rows[n]["af_acc"], hop_rows[n]["af_se"])))
        hop_rows[n]["af_below_chance"] = hop_rows[n]["af_acc"] < CHANCE
    for d in (b for b in range(5) if present("distractors", b)):
        f = [per_seed[s]["distractors"]["f"][str(d)] for s in complete]
        a = [per_seed[s]["distractors"]["af"][str(d)] for s in complete]
        dis_rows[d] = {"f_acc": med([x[0] for x in f]), "af_acc": med([x[0] for x in a]),
                       "gap": med([x[0] for x in f]) - med([x[0] for x in a])}
    boot = cluster_bootstrap([r for r in recs if r["seed_idx"] in complete], sorted(hop_rows))
    ref, cross = reference(), crossing({n: hop_rows[n]["af_acc"] for n in hop_rows})
    vs_ref = None
    if ref.get("available"):
        vs_ref = {}
        for n in sorted(hop_rows):
            for s, key in (("f", "f_acc"), ("af", "af_acc")):
                o = ref[key].get(str(n))
                ci = boot["bins"][n][f"{s}_ci95"]
                vs_ref[f"{s}|n={n}"] = {"rerun": hop_rows[n][f"{s}_acc"], "original": o,
                                        "delta_pp": None if o is None else (hop_rows[n][f"{s}_acc"] - o) * 100,
                                        "original_inside_ci95": None if o is None else ci[0] <= o <= ci[1]}
    lo, hi = min(hop_rows), max(hop_rows)
    degrades = hi > lo and hop_rows[hi]["af_acc"] < hop_rows[lo]["af_acc"] and hop_rows[hi]["f_acc"] < hop_rows[lo]["f_acc"]
    label, why = judge({n: hop_rows[n] for n in hop_rows}, cross, ref.get("af_below_chance_from_hop"), degrades)
    if len(hop_rows) < len(HOP_N):
        label, why = "미판정 (incomplete)", (f"not judged: only hop bins {sorted(hop_rows)} of {sorted(HOP_N)} are present, "
                                          "so neither the every-bin gap test nor the chance-line crossing can be evaluated")
    failed_rate = float(np.mean([1 - (r["parsed"] is not None) for r in recs]))
    frictions = [
        "the paper prints no per-cell table and released no per-model result file: Figure 3 is the only original value, and "
        "the Codabench leaderboard the card offered as an alternative holds zero submissions. The comparison here rests on "
        "a vector digitisation of Figure 3 (columns 1-2 are a bar chart, so the SVG carries every bar); it happens to be "
        "exact - each value has a unique integer pre-image over the Table 5 denominators and the plotted Wald bars confirm "
        "it - but only because the figure was published as SVG, which is luck, not a reproducibility practice",
        "the frozen Codabench release is not downloadable anonymously (the Files tab requires a logged-in account; the "
        "public_data dataset endpoint returns HTTP 403), so the benchmark was regenerated in-repo and could not be diffed "
        "against the official release",
        "accord/io.py save_lines() appends os.linesep in text mode, which doubles the CR on Windows and makes every one of "
        "the repository's own loaders raise JSONDecodeError on its own output; the generator cannot run on Windows without "
        "forcing os.linesep to '\\n'",
        "SimpleQACheckpointManager keys on a checkpoint directory whose default job_id is -1, so the README's own command "
        "sequence silently no-ops after the first QAData-iterating step (and writes checkpoints into the clone); each step "
        "here gets its own checkpoint directory",
        "requirements.txt pins coma>=1.0.1 but PyPI now serves coma 3.0.1, whose API dropped register/initiate/forget: "
        "src/main.py does not even import on a fresh install; coma==1.0.1 (2022) had to be pinned by hand",
        "accord.commands imports plotly at package import although the benchmarking path draws no figure; plotly is stubbed",
        "the answer prompt is surfaced with the instruction blanked (arguments/gpt-4o-2024-05-13.txt), so the user turn "
        "starts with an empty first surfacer and a leading newline - reproduced verbatim rather than tidied",
        "statement order is fixed by the sequencer's shuffles under random_seed 314159 and frozen into the snapshot; it is "
        "reproducible only because that seed is pinned, and it cannot be verified against the authors' own 2024 ordering",
        f"temperature is the API default 1.0 with a best-effort seed, so the original single run is itself one draw; "
        f"{len(complete)} complete seeds were run and the median is judged",
    ]
    if budget.get("stopped_at_cap"):
        frictions.append(f"the run stopped at the ${budget.get('cap_usd')} cap")
    meta = {
        "card_id": CARD, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
        "target_paper": {"title": "ACCORD: Closing the Commonsense Measurability Gap", "doi": "10.48550/arxiv.2406.02804",
                         "repo": "https://github.com/francois-rd/accord", "repo_commit": REPO_COMMIT,
                         "repo_license": "MIT; ACCORD-CSQA CC BY-SA 4.0",
                         "original_source": "Figure 3 (p. 6), GPT-4o series; Table 5 (App. E.1) for the 2,864-item size "
                                            "distribution; App. E.3 for the run protocol",
                         "original_values": ref},
        "generation": {"model_requested": MODEL, "model_served": sorted(x for x in served if x), "n_fingerprints": len(fps - {None}),
                       "substitute_snapshot": "none - gpt-4o-2024-05-13 is the snapshot the paper benchmarked (App. I.2)",
                       "parameters": f"system + user message; max_tokens {MAX_TOKENS}; seed {API_SEED}; response_format json_object; "
                                     f"no temperature and no top_p field (openai.yaml query_params merged with "
                                     f"arguments/{MODEL}.txt; the API default temperature is 1.0)",
                       "prompt_template_source": "leaderboard/utils.py InstanceSurfacer with the paper's CSQA parameters, "
                                                 "prefix surfacer blanked per the arguments file",
                       "benchmark": f"ACCORD-CSQA Small 0-5 regenerated in-repo (random_seed 314159): {len(rows)} items",
                       "battery": f"{len(rows)} items x {len(complete)} complete seeds = {len(res)} archived calls in "
                                  f"{rel(RUN)}/calls.jsonl; median over seeds; 95% CI = pairing-cluster bootstrap "
                                  f"({N_BOOT} resamples, rng {DRAW_SEED})"},
        "results": {"baseline_no_context_f_acc": med([per_seed[s]["baseline"] for s in complete]),
                    "by_reasoning_hops": hop_rows, "by_distractors": dis_rows, "bootstrap": boot,
                    "per_seed": {str(s): per_seed[s] for s in complete}, "vs_original_figure3": vs_ref,
                    "chance": CHANCE, "af_below_chance_from_hop": cross,
                    "af_below_chance_from_hop_original": ref.get("af_below_chance_from_hop"),
                    "hops_dominate_distractors": {"hop_bins": sorted(hop_rows), "distractor_bins": sorted(dis_rows),
                                                  "hop_spread": hop_rows[lo]["f_acc"] - hop_rows[hi]["f_acc"],
                                                  "distractor_spread": (dis_rows[min(dis_rows)]["f_acc"] - dis_rows[max(dis_rows)]["f_acc"])
                                                  if dis_rows else None},
                    "answer_extraction_failure_rate": failed_rate, "paper_extraction_note": ANCHORS["extraction"],
                    "cost_usd": round(budget.get("cost_usd", sum(r.get("cost_usd", 0) for r in res.values())), 4),
                    "calls": budget.get("calls", len(res)), "errors": budget.get("errors", 0),
                    "call_log_stats": {"finish_reasons": finish, "distinct_fingerprints": len(fps - {None}),
                                       "tokens_in": budget.get("tokens_in"), "tokens_out": budget.get("tokens_out")},
                    "judgment": label,
                    "judged_by": "automatic rule per ANALYSIS_PLAN section 1 as the card instantiates it: survived = the "
                                 "factual-minus-anti-factual gap positive and Wald-significant at every hop bin AND the "
                                 "below-chance crossing within one hop of the reference; partial = gap survives but the "
                                 "crossing moves by more than one hop or disappears; dead = the gap vanishes or reverses, or "
                                 "anti-factual accuracy stops degrading in n. Human double-coding pending",
                    "note": why},
        "environment_check": {"file": rel(CHECK_JSON), "items_match_table5": env.get("items", {}).get("counts_match_table5"),
                              "distinct_pairings": env.get("items", {}).get("distinct_pairings")},
        "reproducibility_frictions_observed": frictions,
    }
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_jd), encoding="utf-8")
    (RUN / "result.json").write_text(json.dumps({"by_reasoning_hops": hop_rows, "by_distractors": dis_rows,
                                                 "judgment": label}, indent=2, ensure_ascii=False, default=_jd), encoding="utf-8")
    print(f"\n[{CARD} --analyze] {len(res)} calls, complete seeds {complete}, served {sorted(x for x in served if x)}, ${meta['results']['cost_usd']}")
    print(f"  {'hops':>5s}{'factual':>10s}{'orig':>8s}{'anti-f':>10s}{'orig':>8s}{'gap':>9s}{'z':>8s}   gap 95% CI")
    for n in sorted(hop_rows):
        r, b = hop_rows[n], boot["bins"][n]
        of = ref["f_acc"].get(str(n)) if ref.get("available") else None
        oa = ref["af_acc"].get(str(n)) if ref.get("available") else None
        print(f"  {n:5d}{r['f_acc']:10.3f}{(of if of is not None else float('nan')):8.3f}{r['af_acc']:10.3f}"
              f"{(oa if oa is not None else float('nan')):8.3f}{r['gap']:9.3f}{r['z']:8.2f}   "
              f"[{b['gap_ci95'][0]:.3f}, {b['gap_ci95'][1]:.3f}]{'  af<chance' if r['af_below_chance'] else ''}")
    print(f"  no-context baseline {meta['results']['baseline_no_context_f_acc']:.3f}; chance {CHANCE}; anti-factual crosses "
          f"below chance at n={cross} (Figure 3: n={ref.get('af_below_chance_from_hop')}); extraction failures {failed_rate:.4f}")
    print(f"  judgment: {label} - {why}\n  -> {rel(META)}")
    return meta


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="offline: items, one exact request, parser and scorer (no API calls)")
    ap.add_argument("--dry-run", action="store_true", help="build the request list and estimate cost (no API calls)")
    ap.add_argument("--run", action="store_true", help="execute the battery (paid API calls, capped)")
    ap.add_argument("--analyze", action="store_true", help="score the archived replies and write run_meta.json")
    ap.add_argument("--sizes", default="0,1,2,3,4,5", help="problem sizes to obtain/use (default all)")
    ap.add_argument("--no-generate", action="store_true", help="use only the sizes already regenerated on disk")
    ap.add_argument("--seeds", type=int, default=SEEDS)
    ap.add_argument("--cap", type=float, default=CAP)
    ap.add_argument("--workers", type=int, default=WORKERS)
    a = ap.parse_args()
    sizes = tuple(int(x) for x in a.sizes.split(",") if x.strip() != "")
    if not any((a.check, a.dry_run, a.run, a.analyze)):
        ap.print_help()
        return
    if a.check:
        check(sizes, generate=not a.no_generate)
    if a.dry_run:
        dry_run(sizes, a.seeds, a.cap, generate=not a.no_generate)
    if a.run:
        run(sizes, a.seeds, a.cap, a.workers)
    if a.analyze:
        analyze(sizes, a.seeds)


if __name__ == "__main__":
    main()
