"""Card W4400103831 - BADGE: BADminton report Generation and Evaluation with LLM (Chiang et al.,
IJCAI 2024 workshop IT4PSS, arXiv 2406.18116; repo AndyChiangSH/BADGE @ 83a515a2, MIT).

Claim re-measured (Table 2, GPT-4 evaluation of the CSV+CoT condition, 10 ShuttleSet matches, scores 1-10):
  writer human 7.5 / 8.9 / 6.8 / 8.5 = 7.925   GPT-3.5 8.4 / 9.2 / 8.0 / 8.9 = 8.625   GPT-4 8.6 / 9.4 / 8.2 / 9.1 = 8.825
gpt-4-turbo-2024-04-09 is BOTH the writer under test and the G-Eval-style judge, so the paper's own
self-preference finding (LLM reports above human reports) rests twice on one dying snapshot.

Decisions 2026-09-19 (card key "decisions_2026_09_19"):
  primary arm    full protocol - regenerate the GPT-4 reports with prompt/generation/CSV+CoT.txt, then judge all
                 three writers' reports with prompt/evaluation/<criterion>.txt (GPT-3.5 is dead: its released
                 reports and the human reports are judged as fixed inputs)
  secondary arm  judge-only on the released reports -> isolates judge drift. The GPT-3.5 and human judge calls
                 are IDENTICAL in both arms and are issued once, so the secondary arm costs only the 10x4 calls
                 on the released GPT-4 reports.
  targets        the published 8.825 is primary; the 8.40 re-aggregated from the repo's own released judge
                 outputs is reported alongside (the like-for-like target of the secondary arm)
  parser         bare integer, else the last criterion-labelled number, else missing (1-10 enforced)
  scope          Table 1's 8-cell ICL grid is skipped; per-paper cap USD 15

Protocol, taken from the repository at run time (never copied): code/generation/GPT-4.py sends ONE user message
= prompt/generation/CSV+CoT.txt with "{CSV}" replaced by CSV/<game>/CSV.txt; code/evaluation/{GPT-4,GPT-3.5,
human}.py send ONE user message = prompt/evaluation/<criterion>.txt with "{Badminton Report}" replaced by the
report. Model, criterion list, placeholders and prompt paths are read out of those scripts with `ast` before any
request is built (repo_protocol()); the scripts cannot be imported for effect - each is a bare __main__ block
that would start calling the API. No temperature, max_tokens, top_p or seed is passed, exactly as the originals
do, so both stages run at the API default temperature 1.0 and the 3 seeds are the variance estimate.

  python adapters/badge_W4400103831.py --check      # offline re-aggregation of the released judge outputs + prompt rendering
  python adapters/badge_W4400103831.py --dry-run    # writer + secondary-arm judge requests, tokens, USD; writes the request files
  python adapters/badge_W4400103831.py --run        # stage 1 writer -> runs/W4400103831/baseline_alive/writer, stage 2 judge -> .../judge
  python adapters/badge_W4400103831.py --analyze    # Table 2 rows, bootstrap CIs over matches, judgment, run_meta.json

Findings of --check (2026-09-19): the released outputs reproduce the Table 2 GPT-3.5 row exactly (8.625) and give
8.400 for the GPT-4 row instead of the published 8.825 (its consistency column collapses: released scores 10, 4,
8, 10, [unparseable], 9, 3, 9, 9, 10). The human row reproduces coherence/consistency/fluency exactly and reaches
the published 7.925 once the one reply that renames the criterion ("- Excitiveness: 6") is counted, which the
criterion-stem sensitivity variant does - it changes exactly 1 of the 120 cells. With that reply dropped the row
is 7.947. The card's 7.933 needs a THIRD, markdown-blind parser that additionally drops "- **Fluency**: 9" (and
that parser breaks the GPT-3.5 row, 8.606): all three are computed so the card's figure stays traceable.
"""
import argparse, ast, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from battery import load_results, pricing_for, run_battery  # noqa: E402

CARD = "W4400103831"
HALF = HERE.parent.parent
REPO = HALF / "external" / "repos" / CARD / "AndyChiangSH__BADGE"
CARD_JSON = HALF / "harness" / "cards" / f"{CARD}.json"
RUNROOT = HALF / "runs" / CARD
WRITER_RUN, JUDGE_RUN = RUNROOT / "baseline_alive" / "writer", RUNROOT / "baseline_alive" / "judge"
REQ_DIR, CHECK_JSON = RUNROOT / "requests", RUNROOT / "environment_check.json"

MODEL = "gpt-4-turbo-2024-04-09"
ICL = "CSV+CoT"                       # Table 2 condition (its GPT-3.5 row equals the CSV+CoT row of Table 1)
CRITERIA = ["coherence", "consistency", "excitement", "fluency"]     # Table 2 column order
WRITERS = ["human", "gpt35", "gpt4"]
SRC_DIR = {"gpt4": "GPT-4", "gpt35": "GPT-3.5", "human": "human"}
SEEDS, BOOT, SEED0 = 3, 2000, 0
CAP, WRITER_CAP, JUDGE_CAP = 15.0, 3.0, 12.0
TABLE2 = {"human": {"coherence": 7.5, "consistency": 8.9, "excitement": 6.8, "fluency": 8.5, "avg": 7.925},
          "gpt35": {"coherence": 8.4, "consistency": 9.2, "excitement": 8.0, "fluency": 8.9, "avg": 8.625},
          "gpt4": {"coherence": 8.6, "consistency": 9.4, "excitement": 8.2, "fluency": 9.1, "avg": 8.825}}
CARD_RECOMPUTED_GPT4 = 8.40           # card artifacts.notes, re-derived here from the released files
CARD_HUMAN_AVG = 7.933                # card artifacts.notes; markdown-blind parser, see check()

# score parser: bare integer, else the last "<criterion> [Score][:] <n>" (markdown bold tolerated), else missing
TIGHT = {c: re.compile(rf"(?i)\b{c}\b\s*\**\s*(?:score)?\s*\**\s*[:\-]?\s*\**\s*(\d{{1,2}})\b") for c in CRITERIA}
BLIND = {c: re.compile(rf"(?i)\b{c}\b\s*[:\-]?\s*(\d{{1,2}})\b") for c in CRITERIA}   # card variant, no markdown
STEM = {c: re.compile(rf"(?i)\b{c[:5]}\w*\s*\**\s*(?:score)?\s*\**\s*[:\-]?\s*\**\s*(\d{{1,2}})\b") for c in CRITERIA}


def now():
    return datetime.now(timezone.utc).isoformat()


def _jd(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


# ------------------------------------------------------------------------------- repository (read, never copied)
def _ci(parent, name):
    """Case-insensitive child lookup: the repo stores evaluation/<game>/GPT-4/csv+CoT.txt for 9 games and
    CSV+CoT.txt for the tenth, so plain path joins are not portable off Windows."""
    if not parent.is_dir():
        return None
    for p in sorted(parent.iterdir()):
        if p.name.lower() == name.lower():
            return p
    return None


def repo_protocol():
    """Model, criteria, prompt paths and placeholders parsed out of the repository's own scripts with ast.
    The scripts are bare __main__ blocks that call the API on import, so they are read, not imported."""
    if not REPO.exists():
        sys.exit(f"repository not found at {REPO}")
    out = {}
    for role, rel in (("writer", "code/generation/GPT-4.py"), ("judge", "code/evaluation/GPT-4.py"),
                      ("judge_gpt35", "code/evaluation/GPT-3.5.py"), ("judge_human", "code/evaluation/human.py")):
        tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
        nodes = list(ast.walk(tree))
        assigns = {getattr(n.targets[0], "id", ""): n.value for n in nodes if isinstance(n, ast.Assign)}
        calls = lambda attr: [n for n in nodes if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == attr]
        fstr = ["".join(v.value if isinstance(v, ast.Constant) else "{}" for v in j.values)
                for j in nodes if isinstance(j, ast.JoinedStr)]
        out[role] = {"source": rel, "model": getattr(assigns.get("model"), "value", None),
                     "placeholders": [n.args[0].value for n in calls("replace") if n.args and isinstance(n.args[0], ast.Constant)],
                     "create_kwargs": sorted({k.arg for n in calls("create") for k in n.keywords}),
                     "prompt_paths": [f for f in fstr if f.startswith("prompt/")],
                     "criteria": [e.value for e in assigns["metrics"].elts] if "metrics" in assigns else None}
    if (any(v["model"] != MODEL for v in out.values())
            or out["writer"]["placeholders"][:1] != ["{CSV}"] or out["judge"]["placeholders"][:1] != ["{Badminton Report}"]
            or any(sorted(out[r]["criteria"] or []) != sorted(CRITERIA) for r in out if r.startswith("judge"))):
        sys.exit(f"repository protocol changed: {json.dumps(out, indent=2)}")
    return out


def games():
    gs = sorted(p.name for p in (REPO / "CSV").iterdir() if p.is_dir())
    assert len(gs) == 10, gs
    return gs


def csv_input(game):
    return (REPO / "CSV" / game / "CSV.txt").read_text(encoding="utf-8")


def released_report(game, writer):
    return _ci(REPO / "generation" / game / SRC_DIR[writer],
               "human.txt" if writer == "human" else f"{ICL}.txt").read_text(encoding="utf-8")


def released_judgement(game, writer, crit):
    d = REPO / "evaluation" / game / SRC_DIR[writer]
    d = d if writer == "human" else _ci(d, f"{ICL}.txt")
    return _ci(d, f"{crit}.txt").read_text(encoding="utf-8")


def writer_prompt(game):
    return (REPO / "prompt" / "generation" / f"{ICL}.txt").read_text(encoding="utf-8").replace("{CSV}", csv_input(game))


def judge_prompt(report, crit):
    return (REPO / "prompt" / "evaluation" / f"{crit}.txt").read_text(encoding="utf-8").replace("{Badminton Report}", report)


# ---------------------------------------------------------------------------------------------- parsing / statistics
def parse_score(text, crit, pats=TIGHT):
    s = (text or "").strip()
    if re.fullmatch(r"\d{1,2}", s):
        v = int(s)
        return v if 1 <= v <= 10 else None
    m = list(pats[crit].finditer(text or ""))
    for hit in reversed(m):                      # last criterion-labelled number that is a legal score
        v = int(hit.group(1))
        if 1 <= v <= 10:
            return v
    return None


def row(mat):
    """mat[match][crit] (values or None) -> per-criterion means, 4-criterion average, missing count."""
    per, miss = {}, 0
    for c in CRITERIA:
        vs = [m.get(c) for m in mat]
        miss += sum(v is None for v in vs)
        vs = [v for v in vs if v is not None]
        per[c] = float(np.mean(vs)) if vs else None
    got = [per[c] for c in CRITERIA if per[c] is not None]
    return {"per_criterion": per, "avg": float(np.mean(got)) if got else None, "n_matches": len(mat), "missing": miss}


def bootstrap_avg(mat, n_boot=BOOT, seed=SEED0):
    rng = np.random.default_rng(seed)
    n = len(mat)
    if n == 0:
        return None
    draws = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        r = row([mat[i] for i in idx])
        if r["avg"] is not None:
            draws.append(r["avg"])
    return {"ci95": [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))],
            "n_boot": n_boot, "seed": seed} if draws else None


def pool_seeds(per_seed):
    """[{match: {crit: v}}] over seeds -> one matrix of per-match seed means (None where every seed is missing)."""
    out = []
    for i in range(len(per_seed[0])):
        cell = {}
        for c in CRITERIA:
            vs = [s[i].get(c) for s in per_seed if s[i].get(c) is not None]
            cell[c] = float(np.mean(vs)) if vs else None
        out.append(cell)
    return out


def judge_row(mats):
    """mats: list over seeds of [match][crit]. -> row of the seed-pooled matrix + per-seed averages + CI."""
    pooled = pool_seeds(mats)
    r = row(pooled)
    r["per_seed_avg"] = [row(m)["avg"] for m in mats]
    got = [x for x in r["per_seed_avg"] if x is not None]
    r["median_over_seeds"] = float(np.median(got)) if got else None      # None, never nan: an empty row must stay unjudged
    r["bootstrap"] = bootstrap_avg(pooled)
    return r


def judgment(rows, target):
    """Card judgment rule (ANALYSIS_PLAN section 1): the ordering, not the level, is load-bearing."""
    g4, g35, hu = (rows[w]["median_over_seeds"] for w in ("gpt4", "gpt35", "human"))
    if None in (g4, g35, hu):
        return "미판정 (incomplete)", "one writer row is empty"
    if hu >= g4 or hu >= g35:
        return "사망 (dead)", f"human-written reports scored at or above the LLM-written ones (human {hu:.3f}, GPT-3.5 {g35:.3f}, GPT-4 {g4:.3f})"
    lo, hi = rows["gpt4"]["bootstrap"]["ci95"]
    inside, order = lo <= target <= hi, g4 >= g35
    ctx = f"(GPT-4 {g4:.3f}, CI [{lo:.3f}, {hi:.3f}]; GPT-3.5 {g35:.3f}; human {hu:.3f}; original {target})"
    if inside and order:
        return "생존 (survived)", f"the original is inside the match-bootstrap CI and GPT-4 >= GPT-3.5 > human {ctx}"
    broken = " and ".join(x for x in ("the original is outside the CI" if not inside else "",
                                      "GPT-4 < GPT-3.5" if not order else "") if x)
    return "부분 생존 (partial)", f"the LLM-over-human ordering holds but {broken} {ctx}"


# ------------------------------------------------------------------------------------------------------- --check
def released_matrix(writer, parser=TIGHT):
    return [{c: parse_score(released_judgement(g, writer, c), c, parser) for c in CRITERIA} for g in games()]


def check(verbose=True):
    proto = repo_protocol()
    gs = games()
    rows_t = {w: row(released_matrix(w, TIGHT)) for w in WRITERS}
    rows_b = {w: row(released_matrix(w, BLIND)) for w in WRITERS}
    rows_s = {w: row(released_matrix(w, STEM)) for w in WRITERS}
    raw = {w: [{c: released_judgement(g, w, c) for c in CRITERIA} for g in gs] for w in WRITERS}
    cells = [(w, gs[i], c, raw[w][i][c].strip()) for w in WRITERS for i in range(10) for c in CRITERIA]
    unparsed = [{"writer": w, "game": g, "criterion": c, "chars": len(t), "tail": t[-160:]}
                for w, g, c, t in cells if parse_score(t, c) is None]
    formats = {"bare_integer": sum(bool(re.fullmatch(r"\d{1,2}", t)) for _, _, _, t in cells),
               "labelled": sum(not re.fullmatch(r"\d{1,2}", t) and parse_score(t, c) is not None for _, _, c, t in cells),
               "unparseable": len(unparsed)}
    stem_diff = sum(parse_score(t, c, TIGHT) != parse_score(t, c, STEM) for _, _, c, t in cells)
    wp, jp = writer_prompt(gs[0]), judge_prompt(released_report(gs[0], "gpt4"), CRITERIA[0])
    matches = {"gpt35_row_matches_table2": abs(rows_t["gpt35"]["avg"] - TABLE2["gpt35"]["avg"]) < 5e-4,
               "gpt4_row_matches_card_recomputed_8_40": abs(rows_t["gpt4"]["avg"] - CARD_RECOMPUTED_GPT4) < 5e-3,
               "gpt4_row_matches_published_8_825": abs(rows_t["gpt4"]["avg"] - TABLE2["gpt4"]["avg"]) < 5e-4,
               "human_row_matches_table2": abs(rows_t["human"]["avg"] - TABLE2["human"]["avg"]) < 5e-4,
               "human_row_matches_card_7_933_markdown_blind": abs(rows_b["human"]["avg"] - CARD_HUMAN_AVG) < 5e-4,
               "human_row_matches_table2_criterion_stem_variant": abs(rows_s["human"]["avg"] - TABLE2["human"]["avg"]) < 5e-4,
               "stem_variant_changes_only_that_one_cell": stem_diff == 1}
    summary = {
        "card_id": CARD, "checked_utc": now(), "python": sys.version.split()[0], "model": MODEL, "condition": ICL,
        "repository": {"path": str(REPO), "commit": "83a515a2f618e118cebc4f55ae55096f2a4e7560", "license": "MIT",
                       "protocol_from_source": proto, "n_games": len(gs), "games": gs,
                       "released_reports": {w: 10 for w in WRITERS}, "released_judge_files": 680},
        "parser": {"rule": "bare integer, else the last '<criterion> [Score][:] <n>' with markdown bold tolerated, "
                           "1-10 enforced, otherwise missing", "regex": TIGHT["coherence"].pattern,
                   "card_variant_regex": BLIND["coherence"].pattern, "stem_variant_regex": STEM["coherence"].pattern,
                   "output_formats_table2_subset": formats, "unparseable": unparsed},
        "reaggregated_released_outputs": {w: rows_t[w] for w in WRITERS},
        "card_parser_variant_markdown_blind": {w: rows_b[w] for w in WRITERS},
        "criterion_stem_variant": {w: rows_s[w] for w in WRITERS},
        "published_table2": TABLE2, "targets_confirmed": matches,
        "decisions": json.loads(CARD_JSON.read_text(encoding="utf-8")).get("decisions_2026_09_19"),
        "prompt_rendering": {
            "writer": {"game": gs[0], "template": f"prompt/generation/{ICL}.txt", "placeholder": "{CSV}",
                       "data": f"CSV/{gs[0]}/CSV.txt", "chars": len(wp), "text": wp},
            "judge": {"game": gs[0], "writer": "gpt4", "template": f"prompt/evaluation/{CRITERIA[0]}.txt",
                      "placeholder": "{Badminton Report}", "report": f"generation/{gs[0]}/GPT-4/{ICL}.txt",
                      "chars": len(jp), "text": jp}},
        "notes": [
            "the released judge outputs are one pass of gpt-4-turbo-2024-04-09 at the API default temperature 1.0",
            "evaluation/<game>/GPT-4|GPT-3.5/ uses 'csv+...' for 9 games and 'CSV+...' for Kento_MOMOTA_CHOU_Tien_Chen: "
            "the lookup is case-insensitive",
            "human reports are third-party news text (card: non-redistributable); this file embeds only a GPT-4 report prompt"],
    }
    RUNROOT.mkdir(parents=True, exist_ok=True)
    CHECK_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=_jd), encoding="utf-8")
    if verbose:
        print(f"\n[{CARD} --check] repo {REPO.name}: model/criteria/placeholders read from "
              f"{', '.join(v['source'] for v in proto.values())}; create() kwargs {proto['writer']['create_kwargs']} "
              f"(no temperature/max_tokens/seed, as the card records)")
        print(f"  released judge outputs, Table 2 subset (3 writers x 10 matches x 4 criteria = 120): {formats}")
        print("\n  " + f"{'writer':8s}" + "".join(f"{c:>13s}" for c in CRITERIA) + f"{'avg':>9s}{'published':>11s}")
        for w in WRITERS:
            print(f"  {w:8s}" + "".join(f"{rows_t[w]['per_criterion'][c]:13.3f}" for c in CRITERIA)
                  + f"{rows_t[w]['avg']:9.3f}{TABLE2[w]['avg']:11.3f}"
                  + (f"   ({rows_t[w]['missing']} unparseable)" if rows_t[w]["missing"] else ""))
        print(f"  markdown-blind (card) parser avgs: " + ", ".join(f"{w} {rows_b[w]['avg']:.3f}" for w in WRITERS)
              + "   | criterion-stem variant: " + ", ".join(f"{w} {rows_s[w]['avg']:.3f}" for w in WRITERS))
        for k, v in matches.items():
            print(f"    {'OK ' if v else 'NO '} {k}")
        for u in unparsed:
            print(f"  unparseable: {u['writer']:6s} {u['criterion']:12s} {u['game'][:40]:40s} ...{u['tail'][-70:]!r}")
        print(f"\n  writer prompt ({gs[0]}), {len(wp)} chars, head/tail:\n    {wp[:150]!r}\n    ...{wp[-90:]!r}")
        print(f"  judge prompt ({CRITERIA[0]}, released GPT-4 report), {len(jp)} chars, head/tail:\n    {jp[:150]!r}\n    ...{jp[-120:]!r}")
        print(f"  -> {CHECK_JSON}")
    return summary


# ----------------------------------------------------------------------------------------------------- requests
def body(text):
    return {"model": MODEL, "messages": [{"role": "user", "content": text}]}      # exactly the repo's two arguments


def writer_requests(seeds=SEEDS):
    return [{"id": f"writer|{g}", "seed_idx": s, "meta": {"stage": "writer", "game": g, "icl": ICL, "seed": s},
             "body": body(writer_prompt(g))} for s in range(seeds) for g in games()]


def judge_requests(sources, seeds=SEEDS):
    """sources: {source_key: {(game, seed_idx): report_text}}. source_key in gpt4_new / gpt4_released /
    gpt35_released / human_released. gpt35_released and human_released are shared by both arms."""
    reqs = []
    for src, reports in sources.items():
        for s in range(seeds):
            for g in games():
                # released reports are frozen (one text, every seed); new reports must come from the matching writer seed
                rep = reports.get((g, s)) if not src.endswith("_released") else reports.get((g, 0))
                if rep is None:
                    continue
                for c in CRITERIA:
                    reqs.append({"id": f"judge|{src}|{g}|{c}", "seed_idx": s,
                                 "meta": {"stage": "judge", "source": src, "game": g, "criterion": c, "seed": s,
                                          "writer": src.split("_")[0], "report_chars": len(rep)},
                                 "body": body(judge_prompt(rep, c))})
    return reqs


def released_sources():
    return {"gpt4_released": {(g, 0): released_report(g, "gpt4") for g in games()},
            "gpt35_released": {(g, 0): released_report(g, "gpt35") for g in games()},
            "human_released": {(g, 0): released_report(g, "human") for g in games()}}


def refined_usd(reqs, out_chars):
    """Token estimate from measured characters (chars/4); out_chars = expected reply length per call."""
    pr = pricing_for(MODEL)
    tin = sum(len(r["body"]["messages"][0]["content"]) / 4 + 8 for r in reqs)
    tout = len(reqs) * out_chars / 4
    return tin, tout, tin / 1e6 * pr["input"] + tout / 1e6 * pr["output"]


# ------------------------------------------------------------------------------------------------------ --dry-run
def dry_run(seeds=SEEDS):
    repo_protocol()
    gs = games()
    wr = writer_requests(seeds)
    sec = judge_requests(released_sources(), seeds)
    REQ_DIR.mkdir(parents=True, exist_ok=True)
    for name, reqs in (("writer_requests.jsonl", wr), ("judge_secondary_requests.jsonl", sec)):
        (REQ_DIR / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs), encoding="utf-8")
    e_w = run_battery(wr, WRITER_RUN, WRITER_CAP, dry_run=True, label=f"{CARD} stage 1 writer {MODEL}")
    e_j = run_battery(sec, JUDGE_RUN, JUDGE_CAP, dry_run=True, label=f"{CARD} stage 2 judge, released reports {MODEL}")
    rep_chars = float(np.mean([len(released_report(g, "gpt4")) for g in gs]))
    jud_chars = float(np.mean([len(released_judgement(g, w, c)) for g in gs for w in WRITERS for c in CRITERIA]))
    wi, wo, w_usd = refined_usd(wr, rep_chars)
    ji, jo, j_usd = refined_usd(sec, jud_chars)
    new4 = [{"id": "x", "body": body(judge_prompt(released_report(g, "gpt4"), c))} for g in gs for c in CRITERIA] * seeds
    ni, no, n_usd = refined_usd(new4, jud_chars)                  # primary arm: judge the NEW GPT-4 reports
    tot = w_usd + j_usd + n_usd
    print(f"\n[{CARD} --dry-run] {seeds} seeds; no API calls made.")
    print(f"  stage 1 writer:              {len(wr):4d} calls (10 matches x {seeds} seeds), ~{wi/1e3:.0f}k in / ~{wo/1e3:.0f}k out -> ${w_usd:.2f}")
    print(f"  stage 2 judge, released:     {len(sec):4d} calls (3 writers x 10 x 4 criteria x {seeds}),  ~{ji/1e3:.0f}k in / ~{jo/1e3:.0f}k out -> ${j_usd:.2f}")
    print(f"  stage 2 judge, new GPT-4:    {len(new4):4d} calls (built at --run from the stage 1 replies), ~{ni/1e3:.0f}k in / ~{no/1e3:.0f}k out -> ${n_usd:.2f}")
    print(f"  TOTAL {len(wr)+len(sec)+len(new4)} calls, ~{(wi+ji+ni)/1e3:.0f}k input / ~{(wo+jo+no)/1e3:.0f}k output tokens, ~${tot:.2f} "
          f"(caps: writer ${WRITER_CAP}, judge ${JUDGE_CAP}, per-paper ${CAP})")
    print(f"  calibration: writer reply {rep_chars:.0f} chars, judge reply {jud_chars:.0f} chars (released files); "
          f"the [dry-run] lines above use the battery's 60-token default output")
    print(f"  primary arm   = new GPT-4 reports + released GPT-3.5 + released human ({40*seeds*3} judge calls)")
    print(f"  secondary arm = released GPT-4 + the SAME released GPT-3.5/human judgements ({40*seeds} extra calls only)")
    print(f"  -> {REQ_DIR / 'writer_requests.jsonl'}, {REQ_DIR / 'judge_secondary_requests.jsonl'}")
    out = {"seeds": seeds, "writer_calls": len(wr), "judge_released_calls": len(sec), "judge_new_calls": len(new4),
           "tokens_in": wi + ji + ni, "tokens_out": wo + jo + no, "usd_refined": tot,
           "usd_battery_upper_bound": e_w["est_usd"] + e_j["est_usd"], "built_utc": now()}
    (REQ_DIR / "dry_run.json").write_text(json.dumps(out, indent=2, default=_jd), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------------------------------------- --run
def reply_of(rec):
    ch = ((rec.get("response") or {}).get("choices") or [{}])[0]
    return (ch.get("message") or {}).get("content") or ""


def run(seeds=SEEDS, workers=4):
    repo_protocol()
    run_battery(writer_requests(seeds), WRITER_RUN, WRITER_CAP, workers=workers, label=f"{CARD} stage 1 writer")
    new = {(m["game"], sidx): reply_of(r) for (rid, sidx), r in load_results(WRITER_RUN).items()
           for m in [r.get("meta", {})] if m.get("stage") == "writer" and reply_of(r).strip()}
    if not new:
        sys.exit("stage 1 produced no reports; stage 2 not started")
    src = released_sources()
    src["gpt4_new"] = new
    run_battery(judge_requests(src, seeds), JUDGE_RUN, JUDGE_CAP, workers=workers, label=f"{CARD} stage 2 judge")


# ------------------------------------------------------------------------------------------------------ --analyze
def analyze(seeds=SEEDS):
    res = load_results(JUDGE_RUN)
    if not res:
        print(f"no archived judge calls in {JUDGE_RUN}; run --run first")
        return None
    gs = games()
    scores = {}                                             # (source, seed, game, crit) -> int|None
    finish, served, fps = {}, set(), set()
    for (rid, sidx), rec in res.items():
        m = rec.get("meta", {})
        scores[(m["source"], sidx, m["game"], m["criterion"])] = parse_score(reply_of(rec), m["criterion"])
        ch = ((rec.get("response") or {}).get("choices") or [{}])[0]
        finish[ch.get("finish_reason")] = finish.get(ch.get("finish_reason"), 0) + 1
        served.add(rec.get("model_served")); fps.add(rec.get("system_fingerprint"))
    seeds_seen = sorted({k[1] for k in scores})

    def mats(source):
        return [[{c: scores.get((source, s, g, c)) for c in CRITERIA} for g in gs] for s in seeds_seen]

    arms = {}
    for arm, srcs in (("primary", {"gpt4": "gpt4_new", "gpt35": "gpt35_released", "human": "human_released"}),
                      ("secondary", {"gpt4": "gpt4_released", "gpt35": "gpt35_released", "human": "human_released"})):
        rows = {w: judge_row(mats(s)) for w, s in srcs.items()}
        if any(r["median_over_seeds"] is None for r in rows.values()):
            arms[arm] = {"rows": rows, "sources": srcs, "judgment": "미판정 (incomplete)"}
            continue
        lab, why = judgment(rows, TABLE2["gpt4"]["avg"])
        lab2, why2 = judgment(rows, CARD_RECOMPUTED_GPT4)
        arms[arm] = {"sources": srcs, "rows": rows,
                     "vs_published_8_825": {"target": TABLE2["gpt4"]["avg"], "delta": rows["gpt4"]["median_over_seeds"] - TABLE2["gpt4"]["avg"],
                                            "judgment": lab, "why": why},
                     "vs_released_recomputed_8_40": {"target": CARD_RECOMPUTED_GPT4, "delta": rows["gpt4"]["median_over_seeds"] - CARD_RECOMPUTED_GPT4,
                                                     "judgment": lab2, "why": why2},
                     "ordering_gpt4_ge_gpt35_gt_human": bool(rows["gpt4"]["median_over_seeds"] >= rows["gpt35"]["median_over_seeds"] >
                                                             rows["human"]["median_over_seeds"]),
                     "judgment": lab}
    env = check(verbose=False)
    budget = {}
    for d in (WRITER_RUN, JUDGE_RUN):
        b = json.loads((d / "budget.json").read_text(encoding="utf-8")) if (d / "budget.json").exists() else {}
        budget[d.name] = b
    cost = sum(b.get("cost_usd", 0) for b in budget.values())
    calls = sum(b.get("calls", 0) for b in budget.values())
    label = arms["primary"].get("judgment", "미판정 (incomplete)")
    meta = {
        "card_id": CARD, "run_date_utc": datetime.now(timezone.utc).date().isoformat(),
        "target_paper": {"title": "BADGE: BADminton report Generation and Evaluation with LLM",
                         "doi": "10.48550/arxiv.2406.18116", "repo": "https://github.com/AndyChiangSH/BADGE",
                         "repo_commit": "83a515a2f618e118cebc4f55ae55096f2a4e7560", "repo_license": "MIT",
                         "original_values": {w: TABLE2[w]["avg"] for w in WRITERS},
                         "original_source": "Table 2 (GPT-4 evaluation, CSV+CoT condition, 10 matches)",
                         "released_outputs_reaggregated": {w: env["reaggregated_released_outputs"][w]["avg"] for w in WRITERS}},
        "generation": {"model_requested": MODEL, "model_served": sorted(x for x in served if x), "n_fingerprints": len(fps - {None}),
                       "endpoint": "POST https://api.openai.com/v1/chat/completions (harness/openai_client.py)",
                       "parameters": "one user message; no temperature / max_tokens / top_p / seed, exactly as "
                                     "code/generation/GPT-4.py and code/evaluation/*.py -> API default temperature 1.0",
                       "prompts": f"prompt/generation/{ICL}.txt ({{CSV}} <- CSV/<game>/CSV.txt) and "
                                  f"prompt/evaluation/<criterion>.txt ({{Badminton Report}} <- report), read from the repo at run time",
                       "battery": f"stage 1 writer {budget.get('writer', {}).get('calls')} calls, stage 2 judge "
                                  f"{budget.get('judge', {}).get('calls')} calls, {len(seeds_seen)} seeds, "
                                  f"score parser: {env['parser']['rule']}"},
        "results": {"arms": arms, "published_table2": TABLE2, "cost_usd": round(cost, 3), "calls": calls,
                    "errors": sum(b.get("errors", 0) for b in budget.values()),
                    "call_log_stats": {"finish_reasons": finish, "judge_calls_archived": len(res)},
                    "judgment": label,
                    "judged_by": "automatic rule per ANALYSIS_PLAN section 1 as the card instantiates it: survived = the "
                                 "published 8.825 lies inside the match-level bootstrap 95% CI of the re-run GPT-4 row AND "
                                 "GPT-4 >= GPT-3.5 > human; partial = ordering holds but level or CI does not; dead = human "
                                 "reports scored at or above the LLM-written ones; human double-coding pending",
                    "note": arms["primary"].get("vs_published_8_825", {}).get("why", "incomplete run")},
        "reproducibility_frictions_observed": [
            "the released judge outputs do not rebuild Table 2's GPT-4 row: our parser gives 8.400 (consistency 8.00 with "
            "released item scores 10, 4, 8, 10, unparseable, 9, 3, 9, 9, 10) against the published 8.825, while the GPT-3.5 "
            "row (8.625) reproduces exactly and the human row reaches 7.925 once one judge reply that renames the criterion "
            "('- Excitiveness: 6') is counted",
            "the repository ships no score parser and no table-building script; the parser above is a documented pipeline "
            "paraphrase, not a prompt change",
            "no decoding parameter is set anywhere in the repository, so writer and judge both run at temperature 1.0 on "
            "n = 10 matches; the published GPT-4 - GPT-3.5 gap of 0.20 is inside that noise",
            "path mismatch in the repository: the generation scripts write generation/<game>/<model>/ while the evaluation "
            "scripts read report/<game>/<model>/, and evaluation/ stores the report directory as 'csv+CoT.txt' for 9 of the "
            "10 games and 'CSV+CoT.txt' for the tenth",
            "the GPT-3.5 writer arm (gpt-3.5-turbo-0125, shut down 2026-03-26) cannot be regenerated; its released reports "
            "and the human reports are judged as fixed inputs",
            "Table 3 (human raters) and the r = 0.333 correlation cannot be re-executed",
            "the 10 human-written reports are third-party news text: they stay inside the L1 archive as prompt inputs only",
        ],
    }
    RUNROOT.mkdir(parents=True, exist_ok=True)
    (RUNROOT / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_jd), encoding="utf-8")
    print(f"\n[{CARD} --analyze] {len(res)} judge calls, seeds {seeds_seen}"
          f"{' (INCOMPLETE, %d requested)' % seeds if len(seeds_seen) < seeds else ''}, ${cost:.2f}")
    for arm, a in arms.items():
        if "rows" not in a:
            continue
        print(f"  {arm} arm ({a['sources']['gpt4']}):")
        for w in WRITERS:
            r = a["rows"][w]
            ci = r["bootstrap"]["ci95"] if r["bootstrap"] else [float("nan")] * 2
            med = f"{r['median_over_seeds']:.3f}" if r["median_over_seeds"] is not None else "  n/a"
            print(f"    {w:6s} avg {med} [CI {ci[0]:.3f}, {ci[1]:.3f}] per-seed "
                  f"{[round(x, 3) for x in r['per_seed_avg'] if x is not None]} published {TABLE2[w]['avg']}")
        if "vs_published_8_825" in a:
            print(f"    vs 8.825: {a['vs_published_8_825']['judgment']}   vs 8.40: {a['vs_released_recomputed_8_40']['judgment']}")
    print(f"  judgment (primary arm vs the published 8.825): {label}\n  -> {RUNROOT / 'run_meta.json'}")
    return meta


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="offline: re-aggregate the released judge outputs, render prompts")
    ap.add_argument("--dry-run", action="store_true", help="build the request files and estimate tokens/cost (no API calls)")
    ap.add_argument("--run", action="store_true", help="stage 1 writer, then stage 2 judge (paid API calls, capped)")
    ap.add_argument("--analyze", action="store_true", help="Table 2 rows, bootstrap CIs, judgment, run_meta.json")
    ap.add_argument("--seeds", type=int, default=SEEDS)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if not any((a.check, a.dry_run, a.run, a.analyze)):
        ap.print_help()
        return
    if a.check:
        check()
    if a.dry_run:
        dry_run(a.seeds)
    if a.run:
        run(a.seeds, a.workers)
    if a.analyze:
        analyze(a.seeds)


if __name__ == "__main__":
    main()
