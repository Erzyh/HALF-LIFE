"""Card W7166808082 - TURTLEAI: Benchmarking Multimodal Models for Visual Programming in Turtle Graphics
(Wen, Staub, Singla; Findings of ACL 2026). Re-executable arm: the DSReal symbolic success rate of o3-2025-04-16.

Paper, Table 1 (row o3, TURTLEAI-DSReal): 40.20% symbolic (44.12% embedding) over 102 real XLogoOnline tasks,
the best of 22 VLMs and still a failure on ~60% of tasks. No per-item outputs are released, so the comparison is
percentage-to-percentage; the repository ships the prompt, the reference programs and the scorer.

Protocol, from the repository (machine-teaching-group/acl2026-turtleai @ d916dab0, external/repos/W7166808082/):
  items     data/test/metadata.jsonl filtered to source == "dsreal" (102 of 823 rows), image = data/test/images/<file_name>.
            Loaded here straight from metadata.jsonl + PIL instead of load_dataset("imagefolder"), which is what that
            loader does internally (file_name -> PIL.Image.open); avoids the `datasets` dependency.
  prompt    src/turtleai/prompts/template_code_synthesis.md verbatim (2,586 chars, 364 words), read through the repo path.
  messages  ONE user message, content parts in the repository's order: {"type":"text"} then {"type":"image_url"} with
            url = turtleai.utils.base64img.convert_img_to_base64(PIL image) = "data:image/png;base64,<PIL PNG re-encode>"
            (examples/common.py:generate_code). detail is NOT set (API default).
  params    reasoning_effort "medium" + max_completion_tokens 8192 (paper App. F.3); no temperature/top_p/seed.
            examples/common.py passes NO decoding parameters at all, so these two are added to match the paper.
  scoring   turtleai.evaluate(code=..., ref_code=task["code"], method="symbolic") - the repository's own scorer,
            imported (never copied) and called in a fresh isolated interpreter per response with a wall-clock timeout.
            Per-response rule from src/turtleai/eval/eval_responses.py (paper App. F.3), NOT from
            examples/eval_model_dataset.py: extract_python_code_from_text() returns ALL fenced blocks and the task is a
            success as soon as ANY block executes and matches. The example script scores only codes[0].
Decisions 2026-09-19: DSReal only (102 items); single arm o3-2025-04-16; image sent exactly as the repo builds it;
repository symbolic scorer; 3 seeds; per-paper cap $25.

  python adapters/turtleai_W7166808082.py --check      # offline: items, one exact body, scorer on the 102 references
  python adapters/turtleai_W7166808082.py --dry-run    # 102 x 3 request list + token/cost estimate (no API calls)
  python adapters/turtleai_W7166808082.py --run        # cap $25 by default -> runs/W7166808082/baseline_alive/
  python adapters/turtleai_W7166808082.py --analyze    # score archived replies, bootstrap CI, judgment, run_meta.json
Model-generated turtle code runs only in a fresh isolated interpreter (subprocess, -I, cwd = temp dir, API key stripped
from the child environment, wall-clock timeout); the repo's own AST pass strips every import before exec.
"""
import argparse, hashlib, json, math, os, subprocess, sys, tempfile, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

CARD_ID = "W7166808082"
HERE = Path(__file__).resolve().parent
HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / CARD_ID / "machine-teaching-group__acl2026-turtleai"
REPO_SRC = REPO / "src"
DATA = REPO / "data" / "test"
META = DATA / "metadata.jsonl"
PROMPT_PATH = REPO_SRC / "turtleai" / "prompts" / "template_code_synthesis.md"
RUNS = HALF / "runs" / CARD_ID
RUN = RUNS / "baseline_alive"
CHECK_JSON = RUNS / "environment_check.json"
SCORE_CACHE = RUNS / "score_cache.jsonl"
WORKER_FLAG = "--score-worker"

MODEL = "o3-2025-04-16"
REASONING_EFFORT = "medium"                 # paper App. F.3
MAX_COMPLETION_TOKENS = 8192                # paper App. F.3
SOURCE = "dsreal"
N_ITEMS = 102
N_SEEDS = 3                                 # ANALYSIS_PLAN Sec. 3 (no seed parameter exists for o3; 3 repeats)
CAP = 25.0
SCORE_TIMEOUT_S = 120.0                     # eval_responses.py uses 60 s per response in its pebble pool
SCORE_WORKERS = 6
OUT_TOKENS_BUDGET = 6000                    # card budget: conservative billed reasoning+visible tokens under the 8192 cap
OUT_TOKENS_TYPICAL = 4000
IMG_BASE_TOKENS, IMG_TILE_TOKENS = 75, 150  # OpenAI "calculating costs" table, o1/o3 row
N_BOOT = 2000
ORIGINAL = {"dsreal_symbolic_pct": 40.20, "dsreal_embedding_pct": 44.12, "implied_successes_of_102": 41,
            "dscraft_symbolic_pct": 8.82, "dssyn_symbolic_pct": 10.18,
            "comparators_dsreal_symbolic_pct": {"o4-mini-2025-04-16": 36.27, "gpt-5-2025-08-07 (medium)": 27.45,
                                                "gpt-4o-2024-11-20": 26.47, "gpt-4-turbo-2024-04-09": 15.69},
            "source": "Table 1 (p. 6724) row o3, columns TURTLEAI-DSReal Sym./Emb.; App. F.2 version table; Sec. 5.2"}
DEATH_HIGH_PCT = 60.0                       # card judgment rule: above this the capability-limit claim fails
DEATH_LOW_PCT = 5.0                         # collapse to near zero for reasons other than truncation


# ============================================================= subprocess scorer (repository code, isolated)
def _score_worker(out_path):
    """Child entry point. stdin: {"codes": [...], "ref_code": str}. Writes the verdict to out_path.

    Imports and calls the repository's scorer; copies nothing. Nothing here touches the network.
    """
    job = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    sys.path.insert(0, str(REPO_SRC))
    import turtleai.emulate.emulator as em
    try:
        from PIL import EpsImagePlugin
        have_gs = bool(EpsImagePlugin.has_ghostscript())
    except Exception:
        have_gs = False
    if not have_gs:
        # emulator._turtle_worker rasterises the Tk canvas PostScript through PIL, which shells out to Ghostscript.
        # The symbolic metric never reads that raster - it compares the recorded turtle states (eval/lines.py) - so
        # without Ghostscript only the rasterisation is replaced by a placeholder; every other check (bbox, size,
        # aspect ratio, canvas.postscript itself) still runs. Reported in environment_check.json / run_meta.json.
        em.convert_img_to_base64 = lambda img: "data:image/x-eps-not-rasterised;base64,"
    from turtleai import evaluate
    out = {"eps_rasterised": have_gs, "blocks": []}
    for code in job["codes"]:
        try:
            r = evaluate(code=code, ref_code=job["ref_code"], method="symbolic")
            b = {"correct": bool(r.correct), "execution_status": r.execution_status,
                 "execution_message": (r.execution_message or "")[:300], "threshold": r.threshold}
        except Exception as e:                                    # evaluate() swallows execution errors; this is scorer breakage
            b = {"correct": False, "execution_status": "fail", "execution_message": f"scorer raised: {e}"[:300]}
        out["blocks"].append(b)
        if b["correct"]:
            break                                                 # eval_responses.py: any matching snippet ends the task
    out["success"] = any(b["correct"] for b in out["blocks"])
    Path(out_path).write_text(json.dumps(out), encoding="utf-8")


def score_one(codes, ref_code, timeout=SCORE_TIMEOUT_S):
    """One response -> verdict dict. Fresh isolated interpreter, temp cwd, no API key in the child env."""
    if not codes:
        return {"success": False, "blocks": [], "eps_rasterised": None, "outcome": "no_code_block"}
    env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
    with tempfile.TemporaryDirectory(prefix="turtleai_", ignore_cleanup_errors=True) as td:
        out_path = os.path.join(td, "verdict.json")
        payload = json.dumps({"codes": codes, "ref_code": ref_code}).encode("utf-8")
        try:
            p = subprocess.run([sys.executable, "-I", "-X", "utf8", str(Path(__file__).resolve()), WORKER_FLAG, out_path],
                               input=payload, capture_output=True, timeout=timeout, cwd=td, env=env)
        except subprocess.TimeoutExpired:
            return {"success": False, "blocks": [], "eps_rasterised": None, "outcome": "timeout"}
        if not os.path.exists(out_path):
            err = p.stderr.decode("utf-8", "replace").strip().splitlines()
            return {"success": False, "blocks": [], "eps_rasterised": None,
                    "outcome": "worker_error", "error": (err[-1][:300] if err else f"exit {p.returncode}")}
        v = json.loads(Path(out_path).read_text(encoding="utf-8"))
    v["outcome"] = "success" if v["success"] else "mismatch_or_exec_fail"
    return v


def score_many(jobs, cache_path, label=""):
    """jobs: [{key, codes, ref_code}] -> {key: verdict}. Cached by sha256 of (codes, ref_code)."""
    cache = {}
    if cache_path.exists():
        for line in open(cache_path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                cache[r["sha"]] = r["verdict"]
    out, todo = {}, []
    for j in jobs:
        j["sha"] = hashlib.sha256(json.dumps([j["codes"], j["ref_code"]], ensure_ascii=False).encode("utf-8")).hexdigest()
        if j["sha"] in cache:
            out[j["key"]] = cache[j["sha"]]
        else:
            todo.append(j)
    if todo:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        print(f"  scoring {len(todo)} responses ({label}; {len(jobs) - len(todo)} cached) ...", flush=True)
        with ThreadPoolExecutor(SCORE_WORKERS) as ex, open(cache_path, "a", encoding="utf-8") as f:
            futs = {ex.submit(score_one, j["codes"], j["ref_code"]): j for j in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                j, v = futs[fut], fut.result()
                out[j["key"]] = v
                f.write(json.dumps({"sha": j["sha"], "key": j["key"], "verdict": v}) + "\n")
                if i % 50 == 0:
                    print(f"    {i}/{len(todo)} ({time.time() - t0:.0f}s)", flush=True)
        print(f"  done in {time.time() - t0:.0f}s", flush=True)
    return out


# ================================================================================================ data / prompt
def now():
    return datetime.now(timezone.utc).isoformat()


def repo_extract():
    """The repository's fenced-block extractor (pure re, no execution) - imported, not copied."""
    if str(REPO_SRC) not in sys.path:
        sys.path.insert(0, str(REPO_SRC))
    from turtleai.utils.extract_python import extract_python_code_from_text
    return extract_python_code_from_text


def load_items():
    if not META.exists():
        sys.exit(f"missing {META} (clone machine-teaching-group/acl2026-turtleai into external/repos/{CARD_ID}/)")
    rows = [json.loads(l) for l in open(META, encoding="utf-8") if l.strip()]
    items = [r for r in rows if r["source"] == SOURCE]
    assert len(rows) == 823 and len(items) == N_ITEMS, (len(rows), len(items))
    for r in items:
        r["path"] = DATA / r["file_name"].replace("/", os.sep)
        if not r["path"].exists():
            sys.exit(f"missing image {r['path']}")
    return sorted(items, key=lambda r: r["id"])            # deterministic order


def prompt_text():
    return PROMPT_PATH.read_text(encoding="utf-8")


def image_data_url(path):
    """data:image/png;base64,... exactly as examples/common.py builds it (repo convert_img_to_base64 on the PIL image)."""
    if str(REPO_SRC) not in sys.path:
        sys.path.insert(0, str(REPO_SRC))
    from PIL import Image
    from turtleai.utils.base64img import convert_img_to_base64
    with Image.open(path) as im:
        im.load()
        return convert_img_to_base64(im)


def build_body(data_url):
    """examples/common.py:generate_code message layout + the paper's App. F.3 parameters."""
    return {"model": MODEL,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt_text()},
                                                      {"type": "image_url", "image_url": {"url": data_url}}]}],
            "reasoning_effort": REASONING_EFFORT, "max_completion_tokens": MAX_COMPLETION_TOKENS}


def build_requests(items=None, seeds=N_SEEDS):
    items = items or load_items()
    urls = {r["id"]: image_data_url(r["path"]) for r in items}
    reqs = []
    for k in range(seeds):
        for r in items:
            reqs.append({"id": f"{SOURCE}|{r['id']}", "seed_idx": k,
                         "meta": {"item_id": r["id"], "source": r["source"], "category": r["category"],
                                  "difficulty": r["difficulty"], "file_name": r["file_name"], "seed": k},
                         "body": build_body(urls[r["id"]])})
    return reqs


# ===================================================================================== tokens, cost, statistics
def image_tokens(w, h, upscale_small=False):
    """OpenAI tile rule, o1/o3 row of the 'calculating costs' table: 75 base + 150 per 512x512 tile.

    ASSUMPTION: the repository sets no `detail`, so the API default ("auto") applies; it is priced here as "high",
    the conservative branch (low detail would bill the 75 base tokens only). The documented resize is: fit inside
    2048x2048, then scale the shortest side to 768. These PNGs are 47x47 to 846x527, i.e. all below both bounds;
    the primary estimate therefore does NOT upscale them (downscale-only reading of the rule, ~249 tokens/image),
    and upscale_small=True gives the other reading (~993 tokens/image) as a sensitivity bound.
    """
    if w > 2048 or h > 2048:
        s = 2048 / max(w, h)
        w, h = w * s, h * s
    if upscale_small or min(w, h) > 768:
        s = 768 / min(w, h)
        w, h = w * s, h * s
    return IMG_BASE_TOKENS + IMG_TILE_TOKENS * math.ceil(w / 512) * math.ceil(h / 512)


def token_estimate(items, seeds=N_SEEDS):
    from PIL import Image
    text_tok = len(prompt_text()) / 4 + 8                      # battery.estimate convention (chars/4 + message overhead)
    lo = hi = 0
    for r in items:
        with Image.open(r["path"]) as im:
            w, h = im.size
        lo += image_tokens(w, h, False)
        hi += image_tokens(w, h, True)
    n = len(items) * seeds
    tin = seeds * (lo + len(items) * text_tok)
    tin_hi = seeds * (hi + len(items) * text_tok)
    return {"calls": n, "text_tokens_per_call": round(text_tok, 1),
            "image_tokens_mean_per_call": round(lo / len(items), 1), "image_tokens_mean_per_call_upscaled": round(hi / len(items), 1),
            "tokens_in": int(tin), "tokens_in_upscaled_variant": int(tin_hi),
            "tokens_out_budgeted": n * OUT_TOKENS_BUDGET, "tokens_out_typical": n * OUT_TOKENS_TYPICAL,
            "tokens_out_cap": n * MAX_COMPLETION_TOKENS}


def cost_of(est, out_per_call=OUT_TOKENS_BUDGET, tokens_in_key="tokens_in"):
    sys.path.insert(0, str(HERE.parent))
    from battery import pricing_for
    p = pricing_for(MODEL)
    return est[tokens_in_key] / 1e6 * p["input"] + est["calls"] * out_per_call / 1e6 * p["output"]


def bootstrap_rate_ci(flags_by_seed, rng, n_boot=N_BOOT):
    """flags_by_seed: items x seeds 0/1. Resample ITEMS; statistic = median over seeds of the per-seed rates."""
    import numpy as np
    a = np.asarray(flags_by_seed, float)
    if a.size == 0:
        return [None, None]
    idx = rng.integers(0, a.shape[0], size=(n_boot, a.shape[0]))
    stats = np.median(a[idx].mean(axis=1), axis=1) * 100
    return [round(float(np.percentile(stats, 2.5)), 2), round(float(np.percentile(stats, 97.5)), 2)]


def original_band(successes=41, n=N_ITEMS, n_boot=N_BOOT, seed=0):
    """Bootstrap 95% CI over the 102 items around the reported 40.20% (41/102), the card's survival band."""
    import numpy as np
    rng = np.random.default_rng(seed)
    v = np.zeros(n)
    v[:successes] = 1
    means = v[rng.integers(0, n, size=(n_boot, n))].mean(axis=1) * 100
    return [round(float(np.percentile(means, 2.5)), 2), round(float(np.percentile(means, 97.5)), 2)]


def judge(rate_pct, band, no_code_share):
    """Card judgment rule (ANALYSIS_PLAN Sec. 1 as instantiated in the card's judgment.rule)."""
    if rate_pct > DEATH_HIGH_PCT:
        return "사망 (death)", f"{rate_pct:.2f}% > {DEATH_HIGH_PCT}%: the 'models struggle at visual programming' claim would not hold"
    if rate_pct < DEATH_LOW_PCT and no_code_share < 0.5:
        return "사망 (death)", f"collapse to {rate_pct:.2f}% with only {no_code_share:.0%} no-code replies (not a truncation artefact)"
    if band[0] <= rate_pct <= band[1]:
        return "생존 (survived)", f"{rate_pct:.2f}% inside the item bootstrap band {band} around the reported 40.20%"
    if rate_pct < 50.0:
        return "부분 생존 (partial)", f"{rate_pct:.2f}% outside {band} but still failing the majority of tasks"
    return "부분 생존 (partial)", f"{rate_pct:.2f}% outside {band} and no longer failing the majority; single-arm, so the 'best arm' half of the rule is unchecked"


def _json_default(o):
    import numpy as np
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


# ============================================================================================== --check (offline)
def check(verbose=True):
    from PIL import Image
    items = load_items()
    p = prompt_text()
    sizes = {}
    for r in items:
        with Image.open(r["path"]) as im:
            sizes[r["id"]] = (im.size, im.mode)
    urls = {r["id"]: image_data_url(r["path"]) for r in items}
    body = build_body(urls[items[0]["id"]])

    refs = [{"key": r["id"], "codes": [r["code"]], "ref_code": r["code"]} for r in items]
    wrong_code = ("def draw(t):\n    t.setheading(37)\n    for i in range(9):\n        t.forward(17 + 5 * i)\n"
                  "        t.right(113)\n")                       # deliberately wrong: an irregular 9-segment spiral star
    wrongs = [{"key": f"wrong|{r['id']}", "codes": [wrong_code], "ref_code": r["code"]} for r in items]
    shifted = [{"key": f"shift|{r['id']}", "codes": [items[(i + 1) % len(items)]["code"]], "ref_code": r["code"]}
               for i, r in enumerate(items)]                      # permutation control: each reference vs the next task
    t0 = time.time()
    v_ref = score_many(refs, SCORE_CACHE, "reference solutions")
    v_wrong = score_many(wrongs, SCORE_CACHE, "deliberately wrong program")
    v_shift = score_many(shifted, SCORE_CACHE, "permutation control")
    elapsed = time.time() - t0

    ref_ok = sum(v["success"] for v in v_ref.values())
    ref_fail = {k: v for k, v in v_ref.items() if not v["success"]}
    extract = repo_extract()
    # the extractor strips each block, so the reference code round-trips up to surrounding whitespace
    fence_roundtrip = sum(extract(f"```python\n{r['code']}\n```") == [r["code"].strip()] for r in items)
    eps = {str(v.get("eps_rasterised")): 0 for v in v_ref.values()}
    for v in v_ref.values():
        eps[str(v.get("eps_rasterised"))] += 1

    summary = {
        "card_id": CARD_ID, "checked_utc": now(), "model_for_the_arm": MODEL, "python": sys.version.split()[0],
        "repo": {"path": str(REPO), "commit": "d916dab0bcf6a0d0647e17cab4089d70d0b402d1",
                 "prompt_file": str(PROMPT_PATH.relative_to(REPO).as_posix()), "prompt_chars": len(p), "prompt_words": len(p.split()),
                 "prompt_sha256": hashlib.sha256(p.encode("utf-8")).hexdigest()},
        "items": {"n": len(items), "source": SOURCE, "metadata_rows": 823,
                  "image_px_width_range": [min(s[0][0] for s in sizes.values()), max(s[0][0] for s in sizes.values())],
                  "image_px_height_range": [min(s[0][1] for s in sizes.values()), max(s[0][1] for s in sizes.values())],
                  "image_modes": dict(Counter(s[1] for s in sizes.values())),
                  "categories": dict(Counter(r["category"] for r in items)),
                  "difficulties": dict(Counter(r["difficulty"] for r in items)),
                  "data_url_mean_chars": int(sum(len(u) for u in urls.values()) / len(urls)),
                  "loader": "metadata.jsonl + PIL.Image.open (what load_dataset('imagefolder') does internally)"},
        "example_request": {"item_id": items[0]["id"], "file_name": items[0]["file_name"],
                            "body": {**body, "messages": [{"role": "user", "content": [
                                {"type": "text", "text": p},
                                {"type": "image_url", "image_url": {"url": urls[items[0]["id"]][:96] + f"... ({len(urls[items[0]['id']])} chars)"}}]}]},
                            "body_sha256": hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest(),
                            "source": "examples/common.py:generate_code (text part then image part) + App. F.3 params"},
        "scorer": {"api": "turtleai.evaluate(code=..., ref_code=..., method='symbolic')",
                   "per_response_rule": "all fenced blocks (extract_python_code_from_text); success if ANY executes and matches "
                                        "(src/turtleai/eval/eval_responses.py, paper App. F.3) - NOT examples/eval_model_dataset.py's codes[0]",
                   "isolation": f"fresh interpreter per response (subprocess -I, cwd=temp dir, OPENAI_API_KEY stripped), timeout {SCORE_TIMEOUT_S}s",
                   "tk_available": True, "eps_rasterised_counts": eps,
                   "ghostscript_shim": ("Ghostscript absent: emulator.convert_img_to_base64 (EPS -> PNG raster) replaced by a "
                                        "placeholder. The symbolic metric compares recorded turtle states, never that raster, so "
                                        "the score is unaffected; every other emulator check still runs.") if eps.get("False") else None,
                   "seconds_for_306_scorings": round(elapsed, 1), "workers": SCORE_WORKERS},
        "reference_solutions": {"passed": ref_ok, "n": len(items), "pct": round(100 * ref_ok / len(items), 2),
                                "failures": {k: v["blocks"][:1] for k, v in list(ref_fail.items())[:10]}},
        "deliberately_wrong_program": {"code": wrong_code, "successes": sum(v["success"] for v in v_wrong.values()),
                                       "n": len(items),
                                       "execution_status": dict(Counter(v["blocks"][0]["execution_status"] for v in v_wrong.values() if v["blocks"]))},
        "permutation_control": {"description": "each task's reference scored against the NEXT task's reference",
                                "successes": sum(v["success"] for v in v_shift.values()), "n": len(items)},
        "fenced_block_roundtrip": {"matches": fence_roundtrip, "n": len(items),
                                   "rule": "extract_python_code_from_text('```python\\n<code>\\n```') == [<code>.strip()] "
                                           "(the repo extractor uses ```python([^`]*)``` and strips each block)"},
        "paper": ORIGINAL,
        "original_item_bootstrap_band_95": original_band(),
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    CHECK_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    if verbose:
        it = summary["items"]
        print(f"\n[{CARD_ID} --check] {it['n']} DSReal items of {it['metadata_rows']} rows; images {it['image_px_width_range']} x "
              f"{it['image_px_height_range']} px, modes {it['image_modes']}; data URL {it['data_url_mean_chars']} chars mean")
        print(f"  prompt {summary['repo']['prompt_chars']} chars / {summary['repo']['prompt_words']} words, sha256 {summary['repo']['prompt_sha256'][:16]}")
        print(f"  example body: {MODEL}, reasoning_effort={REASONING_EFFORT}, max_completion_tokens={MAX_COMPLETION_TOKENS}, "
              f"1 user message with [text, image_url]; sha256 {summary['example_request']['body_sha256'][:16]}")
        print(f"  reference solutions score: {ref_ok}/{len(items)} ({summary['reference_solutions']['pct']}%)")
        print(f"  deliberately wrong program: {summary['deliberately_wrong_program']['successes']}/{len(items)} successes")
        print(f"  permutation control (ref vs next task's ref): {summary['permutation_control']['successes']}/{len(items)}")
        print(f"  fenced-block roundtrip: {fence_roundtrip}/{len(items)}; EPS rasterised: {eps}")
        if summary["scorer"]["ghostscript_shim"]:
            print(f"  NOTE {summary['scorer']['ghostscript_shim']}")
        print(f"  reported 40.20% -> item bootstrap band {summary['original_item_bootstrap_band_95']}; {elapsed:.0f}s of scoring")
        print(f"  -> {CHECK_JSON}")
    return summary


# ============================================================================================ --dry-run / --run
def dry_run(cap=CAP, seeds=N_SEEDS, write=True):
    sys.path.insert(0, str(HERE.parent))
    from battery import run_battery
    items = load_items()
    est = token_estimate(items, seeds)
    reqs = build_requests(items, seeds)
    if write:
        RUN.mkdir(parents=True, exist_ok=True)
        with open(RUN / "requests.jsonl", "w", encoding="utf-8") as f:
            for r in reqs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    usd_budget, usd_typical = cost_of(est), cost_of(est, OUT_TOKENS_TYPICAL)
    usd_ceiling = cost_of(est, MAX_COMPLETION_TOKENS, "tokens_in_upscaled_variant")
    batt = run_battery(reqs, RUN, cap, dry_run=True, label=f"{CARD_ID} {SOURCE}")
    print(f"[dry-run] {len(items)} DSReal items x {seeds} seeds = {est['calls']} calls, single arm {MODEL} "
          f"(reasoning_effort={REASONING_EFFORT}, max_completion_tokens={MAX_COMPLETION_TOKENS}, no temperature)")
    print(f"[dry-run] input  ~{est['tokens_in']/1e3:.0f}k tokens = {est['text_tokens_per_call']:.0f} text (chars/4) + "
          f"{est['image_tokens_mean_per_call']:.0f} image tokens per call (OpenAI tile rule, o3 row 75+150/tile, detail unset -> "
          f"priced as high, small images not upscaled; upscaled reading: {est['image_tokens_mean_per_call_upscaled']:.0f}/call)")
    print(f"[dry-run] output ~{est['tokens_out_budgeted']/1e3:.0f}k tokens budgeted at {OUT_TOKENS_BUDGET}/call "
          f"(billed reasoning + visible under the {MAX_COMPLETION_TOKENS} cap)")
    print(f"[dry-run] estimate ${usd_budget:.2f} at {OUT_TOKENS_BUDGET} out/call; ${usd_typical:.2f} at {OUT_TOKENS_TYPICAL}; "
          f"absolute ceiling ${usd_ceiling:.2f} (every reply hits the 8192 cap + upscaled image tokens). Cap ${cap:.0f}")
    print(f"[dry-run] battery's own estimator says ${batt['est_usd']:.2f} - it counts len(content), which is 2 for a multimodal "
          f"part list, so its input side (~3k) is meaningless; its output side assumes every reply hits the 8192 cap. Use the numbers above")
    if write:
        print(f"[dry-run] -> {RUN / 'requests.jsonl'} ({(RUN / 'requests.jsonl').stat().st_size/1e6:.1f} MB, base64 images inline)")
    return {"estimate": est, "usd_budgeted": usd_budget, "usd_typical": usd_typical, "usd_ceiling": usd_ceiling,
            "battery_est_usd": batt["est_usd"], "calls": est["calls"]}


def run(cap=CAP, seeds=N_SEEDS, workers=4):
    """PAID. Not executed during development."""
    sys.path.insert(0, str(HERE.parent))
    from battery import run_battery
    items = load_items()
    reqs = build_requests(items, seeds)
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "run_config.json").write_text(json.dumps({
        "card_id": CARD_ID, "model": MODEL, "reasoning_effort": REASONING_EFFORT,
        "max_completion_tokens": MAX_COMPLETION_TOKENS, "temperature": None, "top_p": None, "seed_param": None,
        "n_items": len(items), "n_seeds": seeds, "calls": len(reqs), "cap_usd": cap,
        "prompt_source": str(PROMPT_PATH.relative_to(REPO).as_posix()), "message_layout": "examples/common.py:generate_code (text, image_url)",
        "estimate": token_estimate(items, seeds), "built_utc": now()}, indent=2), encoding="utf-8")
    run_battery(reqs, RUN, cap, workers=workers, label=f"{CARD_ID} {SOURCE}")


# ==================================================================================================== --analyze
def analyze():
    import numpy as np
    sys.path.insert(0, str(HERE.parent))
    from battery import load_results
    res = load_results(RUN)
    if not res:
        print(f"no archived calls in {RUN}; run --run first")
        return None
    items = load_items()
    ref = {r["id"]: r for r in items}
    extract = repo_extract()
    env = check(verbose=False)
    budget = json.loads((RUN / "budget.json").read_text(encoding="utf-8")) if (RUN / "budget.json").exists() else {}
    cfg = json.loads((RUN / "run_config.json").read_text(encoding="utf-8")) if (RUN / "run_config.json").exists() else {}

    recs, jobs = {}, []
    for (rid, sidx), rec in res.items():
        iid = rid.split("|", 1)[1]
        ch = ((rec["response"] or {}).get("choices") or [{}])[0]
        reply = (ch.get("message") or {}).get("content") or ""
        usage = (rec["response"] or {}).get("usage") or {}
        codes = extract(reply)
        recs[(iid, sidx)] = {"reply_chars": len(reply), "n_blocks": len(codes), "finish": ch.get("finish_reason"),
                             "model": rec.get("model_served"), "fp": rec.get("system_fingerprint"), "latency": rec.get("latency_ms"),
                             "reasoning_tokens": ((usage.get("completion_tokens_details") or {}).get("reasoning_tokens")),
                             "completion_tokens": usage.get("completion_tokens"), "prompt_tokens": usage.get("prompt_tokens")}
        jobs.append({"key": f"{iid}|{sidx}", "codes": codes, "ref_code": ref[iid]["code"]})
    verdicts = score_many(jobs, RUN / "score_cache.jsonl", "archived replies")

    seeds = sorted({s for _, s in recs})
    complete = [s for s in seeds if all((r["id"], s) in recs for r in items)]
    M = np.array([[int(verdicts[f"{r['id']}|{s}"]["success"]) for s in complete] for r in items], int) if complete else np.zeros((len(items), 0), int)
    per_seed = [round(float(M[:, i].mean() * 100), 2) for i in range(M.shape[1])]
    rate = float(np.median(per_seed)) if per_seed else float("nan")
    rng = np.random.default_rng(0)
    ci = bootstrap_rate_ci(M, rng)
    band = env["original_item_bootstrap_band_95"]

    outcome = Counter(v["outcome"] for v in verdicts.values())
    no_code = sum(1 for k, v in verdicts.items() if v["outcome"] == "no_code_block")
    trunc = sum(1 for r in recs.values() if r["finish"] == "length")
    trunc_no_code = sum(1 for k, r in recs.items() if r["finish"] == "length" and verdicts[f"{k[0]}|{k[1]}"]["outcome"] == "no_code_block")
    label, why = judge(rate, band, no_code / max(len(verdicts), 1)) if per_seed else ("미판정 (incomplete)", "no complete seed")
    if per_seed and len(complete) < N_SEEDS:
        label += f" [subset: {len(complete)}/{N_SEEDS} complete seeds]"
    item_rate = M.mean(axis=1) if M.size else np.zeros(len(items))
    by = lambda f: {v: round(100 * float(item_rate[[i for i, r in enumerate(items) if r[f] == v]].mean()), 2)
                    for v in sorted({r[f] for r in items})}

    frictions = [
        "Table 1 reports only aggregate percentages; no per-item outputs are released, so the comparison is percentage-to-percentage "
        f"(n=102, item bootstrap band around 40.20% is {band})",
        "examples/eval_model_dataset.py scores only the first extracted code block; the paper's rule (App. F.3, "
        "src/turtleai/eval/eval_responses.py) executes every block and counts the task correct if any matches - the latter is used here",
        "examples/common.py passes no decoding parameters at all; reasoning_effort=medium and max_completion_tokens=8192 come from App. F.3",
        "the scorer executes model-generated turtle code: run here in a fresh isolated interpreter per response with a "
        f"{SCORE_TIMEOUT_S:.0f}s wall clock (the repo uses a pebble ProcessPool with a 60s timeout; pebble is not installed here)",
    ]
    if env["scorer"]["ghostscript_shim"]:
        frictions.append(env["scorer"]["ghostscript_shim"])
    if env["reference_solutions"]["passed"] != len(items):
        frictions.append(f"environment check: only {env['reference_solutions']['passed']}/{len(items)} reference programs "
                         f"reproduce themselves - emulator/Tk drift, not a model effect")
    if trunc:
        frictions.append(f"{trunc} of {len(recs)} replies hit finish_reason='length' ({trunc_no_code} of them with no code block): "
                         "reasoning-token truncation, reported separately before being folded into the failure count")
    if budget.get("stopped_at_cap"):
        frictions.append(f"the run stopped at the ${budget.get('cap_usd')} cap; complete seeds {len(complete)}/{N_SEEDS}")

    lat = sorted(r["latency"] for r in recs.values() if r["latency"] is not None)
    meta = {
        "card_id": CARD_ID, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
        "target_paper": {"title": "TURTLEAI: Benchmarking Multimodal Models for Visual Programming in Turtle Graphics",
                         "doi": "10.18653/v1/2026.findings-acl.334", "repo": "https://github.com/machine-teaching-group/acl2026-turtleai",
                         "repo_commit": "d916dab0bcf6a0d0647e17cab4089d70d0b402d1",
                         "repo_license": "no LICENSE file (code licence unstated); dataset CC BY-NC 4.0 per App. C.1",
                         "original_values": ORIGINAL, "original_source": ORIGINAL["source"]},
        "generation": {"model_requested": MODEL, "model_served": sorted({r["model"] for r in recs.values() if r["model"]}),
                       "n_fingerprints": len({r["fp"] for r in recs.values() if r["fp"]}),
                       "endpoint": "POST https://api.openai.com/v1/chat/completions (raw HTTPS, harness/openai_client.py)",
                       "parameters": f"one user message [text, image_url(data:image/png;base64)] per examples/common.py; "
                                     f"reasoning_effort {REASONING_EFFORT}; max_completion_tokens {MAX_COMPLETION_TOKENS}; "
                                     f"no temperature/top_p/seed; image detail unset",
                       "prompt_template_source": f"{PROMPT_PATH.relative_to(REPO).as_posix()} verbatim (sha256 {env['repo']['prompt_sha256'][:16]})",
                       "battery": f"{len(items)} DSReal items x {len(seeds)} seeds = {len(res)} archived calls in {RUN.name}/calls.jsonl",
                       "run_config": cfg, "python": sys.version.split()[0]},
        "evaluation": {"scorer": env["scorer"], "environment_check": {
            "reference_solutions": env["reference_solutions"]["passed"], "n": len(items),
            "deliberately_wrong_program_successes": env["deliberately_wrong_program"]["successes"],
            "permutation_control_successes": env["permutation_control"]["successes"]}},
        "results": {"symbolic_success_rate_pct": round(rate, 2), "per_seed_pct": per_seed, "n_complete_seeds": len(complete),
                    "ci95_bootstrap_over_items": ci, "n_items": len(items), "n_boot": N_BOOT,
                    "original_pct": ORIGINAL["dsreal_symbolic_pct"], "original_item_bootstrap_band_95": band,
                    "delta_points_vs_paper": round(rate - ORIGINAL["dsreal_symbolic_pct"], 2),
                    "original_inside_our_ci": bool(ci[0] is not None and ci[0] <= ORIGINAL["dsreal_symbolic_pct"] <= ci[1]),
                    "rerun_inside_original_band": bool(band[0] <= rate <= band[1]),
                    "items_always/never/unstable": [int((item_rate == 1).sum()), int((item_rate == 0).sum()),
                                                    int(((item_rate > 0) & (item_rate < 1)).sum())],
                    "by_difficulty_pct": by("difficulty"), "by_category_pct": by("category"),
                    "format_artifacts": {"no_code_block_replies": no_code, "finish_reason_length": trunc,
                                         "truncated_and_no_code": trunc_no_code, "scorer_timeouts": outcome.get("timeout", 0),
                                         "scorer_worker_errors": outcome.get("worker_error", 0)},
                    "cost_usd": round(budget.get("cost_usd", 0.0), 3), "calls": budget.get("calls", len(res)),
                    "errors": budget.get("errors", 0),
                    "call_log_stats": {"http_200": len(res), "finish_reasons": dict(Counter(r["finish"] for r in recs.values())),
                                       "mean_reasoning_tokens": round(float(np.mean([r["reasoning_tokens"] or 0 for r in recs.values()])), 1),
                                       "mean_completion_tokens": round(float(np.mean([r["completion_tokens"] or 0 for r in recs.values()])), 1),
                                       "mean_prompt_tokens": round(float(np.mean([r["prompt_tokens"] or 0 for r in recs.values()])), 1),
                                       "latency_ms_median": lat[len(lat) // 2] if lat else None,
                                       "tokens_in": budget.get("tokens_in"), "tokens_out": budget.get("tokens_out")},
                    "judgment": label, "judgment_reason": why,
                    "judged_by": "automatic rule per ANALYSIS_PLAN Sec. 1 as instantiated in the card: survived if the median-of-seeds "
                                 "rate falls inside the item bootstrap band around 40.20% and stays below 60%; partial if outside the band "
                                 "but still failing the majority; dead above 60% or on a non-truncation collapse. Human double-coding pending",
                    "subsidiary_claims_not_judged": "DSReal > DSCraft > DSSyn ordering and the o3 > o4-mini > gpt-5 ordering "
                                                    "(single arm, DSReal only)",
                    "note": (f"{rate:.2f}% [95% CI {ci[0]}, {ci[1]}] vs the reported 40.20% (band {band}); per seed {per_seed}; "
                             f"{no_code} no-code replies, {trunc} truncated." if per_seed else "incomplete run")},
        "reproducibility_frictions_observed": frictions,
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUN / "result.json").write_text(json.dumps({"per_item_rate": {r["id"]: float(item_rate[i]) for i, r in enumerate(items)},
                                                 "per_seed_pct": per_seed, "judgment": label}, indent=2, default=_json_default), encoding="utf-8")
    (RUNS / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    print(f"\n[{CARD_ID} --analyze] {len(res)} calls; served {meta['generation']['model_served']}; ${meta['results']['cost_usd']}")
    print(f"  symbolic success {rate:.2f}% [CI {ci[0]}, {ci[1]}] per seed {per_seed} (paper 40.20, band {band})")
    print(f"  no-code replies {no_code}, truncated {trunc}, scorer timeouts {outcome.get('timeout', 0)}")
    print(f"  judgment: {label} - {why}\n  -> {RUNS / 'run_meta.json'}")
    return meta


def main():
    if len(sys.argv) > 2 and sys.argv[1] == WORKER_FLAG:
        return _score_worker(sys.argv[2])
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="offline: items, one exact body, scorer on the references (no API calls)")
    ap.add_argument("--dry-run", action="store_true", help="build the 102x3 request list and estimate cost (no API calls)")
    ap.add_argument("--run", action="store_true", help="execute the battery (paid API calls, capped)")
    ap.add_argument("--analyze", action="store_true", help="score the archived replies and write run_meta.json")
    ap.add_argument("--cap", type=float, default=CAP, help=f"USD cap for --run (default {CAP:.0f})")
    ap.add_argument("--seeds", type=int, default=N_SEEDS)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if not any((a.check, a.dry_run, a.run, a.analyze)):
        ap.print_help()
        return
    if a.check:
        check()
    if a.dry_run:
        dry_run(a.cap, a.seeds)
    if a.run:
        run(a.cap, a.seeds, a.workers)
    if a.analyze:
        analyze()


if __name__ == "__main__":
    main()
