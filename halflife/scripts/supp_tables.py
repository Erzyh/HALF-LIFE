"""Supplementary tables assembled from the repository data. No API calls.

S1  Census cohort summary (Table 1 candidate): papers, born-dead share, share that has lost a named model by
    TODAY and median months to the first shutdown, by vendor mix, identifier status, year, document type and
    field; the alias-rule outcome; the identifiers per vendor.
S2  Why papers could not be re-executed: Tier B triage verdicts and ineligibility reasons, resolution of the
    conditional papers, run-configuration status with the reason a human is needed, Tier A card status with
    the blocking reason.
S3  Lifespan of the identifiers by type.
S4  Deviations in the re-executions and their causes after triage (curated from runs/tierb/TRIAGE_batch1_g*.md
    and the config notes; the wording follows those files).
Outputs: data/table1_census_summary.csv, data/failure_taxonomy.csv, data/model_type_lifespans.csv,
data/deviation_causes.csv and SUPPLEMENTARY_TABLES.md.
"""
import glob, json, re, sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from census_survival import TODAY, analyse, both, build  # noqa: E402


def md_table(df, floatfmt="{:g}"):
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float) and str(c) == "p" and not pd.isna(v):
                cells.append("<0.001" if v < 0.001 else f"{v:.3f}")
            elif isinstance(v, float) and not pd.isna(v) and float(v).is_integer() and abs(v) >= 10:
                cells.append(f"{int(v):,}")
            elif isinstance(v, float):
                cells.append("" if pd.isna(v) else (f"{v:,.1f}" if abs(v) >= 100 else f"{v:.1f}") if not float(v).is_integer() or abs(v) < 1000 else f"{int(v):,}")
            elif isinstance(v, int):
                cells.append(f"{v:,}")
            else:
                cells.append("" if v is None else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


# ----------------------------------------------------------------------------------------------- S1
def census_summary():
    d, alias, _, _ = build()
    cen = pd.read_csv(ROOT / "data" / "census_v2.csv", low_memory=False)[["openalex_id", "statuses"]]
    d = d.merge(cen, on="openalex_id", how="left")
    d["vendor_mix"] = d["vendors"].map(lambda v: "more than one vendor" if "|" in v else {"openai": "OpenAI only", "anthropic": "Anthropic only", "google": "Google only"}[v])
    d["status_mix"] = d["statuses"].map({"dead": "retired identifiers only", "dying": "announced identifiers only", "dead|dying": "both"})
    d["doc_type"] = d["type"].where(d["type"].isin(["preprint", "conference-paper", "article"]), "other")
    top_fields = list(d["field"].value_counts().head(6).index)
    d["field6"] = d["field"].where(d["field"].isin(top_fields), "other fields")
    groups = [("all papers", "all", d)]
    for col, label in (("vendor_mix", "vendor of the named identifiers"), ("status_mix", "identifier status"), ("year", "publication year"),
                       ("doc_type", "document type"), ("field6", "field (OpenAlex primary)")):
        order = sorted(d[col].unique(), key=lambda x: (str(x) == "other fields" or str(x) == "other", -len(d[d[col] == x])) if col != "year" else (x,))
        for val in order:
            groups.append((str(val), label, d[d[col] == val]))
    rows = []
    for name, label, sub in groups:
        st, _, _ = both(sub, "first_shutdown")
        rows.append({"grouping": label, "group": name, "papers": len(sub), "share_pct": round(100 * len(sub) / len(d), 1),
                     "cited_10plus_pct": round(100 * float((sub["citations"].fillna(0) >= 10).mean()), 1), "born_dead": st["born_dead"],
                     "born_dead_pct": round(100 * st["born_dead"] / len(sub), 1), "in_curve": st["n_curve"],
                     "lost_by_today_pct": st["pct_dead_today"], "lost_by_2026_end_pct": st["pct_lost_by_2026_end"],
                     "median_months": st["median_months"], "q25": st["q25_months"], "q75": st["q75_months"], "km_median_months": st["km_median_months"]})
    t1 = pd.DataFrame(rows)
    t1.to_csv(ROOT / "data" / "table1_census_summary.csv", index=False, encoding="utf-8-sig")
    n_alias = sum(alias.values())
    alias_df = pd.DataFrame([{"dateless alias mention": k, "papers": v, "share_pct": round(100 * v / n_alias, 1)} for k, v in alias.items()])
    tm = json.load(open(ROOT / "target_models.json", encoding="utf-8"))["models"]
    life = pd.read_csv(ROOT / "data" / "model_lifecycles.csv")
    vrows = []
    for v in ("openai", "anthropic", "google"):
        ids = [m for m in tm if m["vendor"] == v]
        lv = life[life["vendor"] == v]
        vrows.append({"vendor": v, "identifiers": len(ids), "retired": sum(m["status"] == "dead" for m in ids),
                      "shutdown announced": sum(m["status"] == "dying" for m in ids),
                      "papers naming one": int(d["vendors"].str.contains(v).sum()),
                      "median lifespan days (dated ids)": float(lv["lifespan_days"].median()), "shortest": int(lv["lifespan_days"].min()), "longest": int(lv["lifespan_days"].max())})
    return t1, alias_df, pd.DataFrame(vrows)


# ----------------------------------------------------------------------------------------------- S2
BLOCKER_LABEL = {"no_number": "reported number is not from a still-callable model, or is only in a figure",
                 "data_closed": "data not public", "no_prompt": "prompt not printed",
                 "dead_alias": "alias resolves to a retired snapshot", "human_outcome": "outcome measured on people",
                 "webui": "web interface only, no API snapshot", "aux_model_dead": "auxiliary model (judge, parser) retired",
                 "tos": "terms-of-service risk (jailbreak or harmful prompts)"}
HUMAN_RULES = [("image or video input", r"image|video|radiograph|diagram|cartoon|frames|VLM"),
               ("multi-stage protocol or execution sandbox", r"sandbox|execut|multi-call|multi-stage|agent loop|sequential|chained|sweep|protocol beyond|sub-step|simulation|web search|scraping|nine datasets|template selected"),
               ("judge or auxiliary model", r"judge|aux_model_dead|self-hosted|classifier|transformers|torch|examiner|embedding"),
               ("prompt not printed", r"prompt not|not printed|not fully printed|abbreviated|reconstruct|vanilla prompt|only a quoted"),
               ("items only in a PDF or figure", r"\bocr\b|pdf|text layer|transcri|figure \d+|an image"),
               ("gated or unreleased data", r"gated|on request|not released|not distributed|not public|private|could not be found|google form|dua\b|copyright|research-use|licen|omits|not shared|unreachable|google drive|mb\b|gb\b|download limit|tar|archive|not in the paper|must be taken|rebuild|assembled|not found"),
               ("decision needed", r"approve|decide|choose|select|confirm")]
CARD_RULES = [("web interface only, no API snapshot", r"web ui|web-ui|chat web|chatgpt-4 web|web interface"),
              ("outcome measured on people", r"human|belief|live sessions|respondents|ratings from"),
              ("data unavailable or licensed", r"private|licensed|copyright|not shared|supplemental material: none|author-granted"),
              ("repository gone", r"404|gone"),
              ("still-callable identifier is not what the paper ran (retired snapshot behind the alias)", r"not an experimental arm|live model dead|dead|unpinned")]


def classify(text, rules, default="other"):
    t = (text or "").lower()
    for label, rx in rules:
        if re.search(rx, t):
            return label
    return default


def failure_taxonomy():
    tri = json.load(open(ROOT / "data" / "tierb_triage_summary.json", encoding="utf-8"))
    rows = []
    rows += [{"stage": "Tier B triage, first pass (600 records, 598 papers)", "item": k, "count": v, "note": ""} for k, v in
             (("eligible", 70), ("conditional", 139), ("ineligible", 389))]
    rows += [{"stage": "Tier B triage, conditional papers resolved (139)", "item": k, "count": v, "note": ""} for k, v in
             (("promoted to eligible (approximate re-execution)", 57), ("need the paper's repository", 66), ("need a figure read from the PDF", 9), ("ineligible", 7))]
    rows += [{"stage": f"Tier B triage, final verdict ({tri['records']:,} records, {tri['unique_papers']:,} unique papers)", "item": k, "count": v, "note": ""} for k, v in tri["verdict"].items()]
    for k, v in sorted(tri["blockers_ineligible"].items(), key=lambda x: -x[1]):
        rows.append({"stage": "Tier B ineligible: reasons (a paper can carry several)", "item": BLOCKER_LABEL.get(k, k), "count": v, "note": k})
    status, reasons, per_wid, variants, ran_not_ready, gated = Counter(), Counter(), [], [], [], []
    executed = {r["wid"] for r in json.load(open(ROOT / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8"))}
    for f in sorted(glob.glob(str(ROOT / "harness" / "tierb" / "configs" / "*.json"))):
        c = json.load(open(f, encoding="utf-8"))
        if str(f)[:-5].endswith("v2"):               # a second configuration of our own design for an executed paper: not a paper's configuration
            variants.append(c["wid"])
            continue
        status[c["status"]] += 1
        if c["status"] != "ready":
            txt = " ".join((c.get("open_points") or []) + (c.get("runner_gaps") or []))
            lab = classify(txt, HUMAN_RULES)
            reasons[lab] += 1
            per_wid.append((c["wid"], c["status"], lab))
            if c["wid"] in executed:
                ran_not_ready.append(c["wid"])
            if c["status"] == "needs_download_check":
                gated.append(c["wid"])
    stage = f"Tier B run configurations ({sum(status.values())}, one per paper)"
    notes = {"ready": f"{len(executed)} executed: the {status['ready']} ready and {', '.join(ran_not_ready)} (run with the paper's prompt; the status records its unreported scoring rule)",
             "needs_human": f"includes {', '.join(ran_not_ready)}, which was executed (see the ready row)",
             "needs_download_check": f"data sets gated behind an access approval ({', '.join(gated)}); set aside at the outset"}
    for k, v in status.items():
        rows.append({"stage": stage, "item": k, "count": v, "note": notes.get(k, "")})
    rows.append({"stage": stage, "item": "second configuration of our own design for an executed paper (not counted above)", "count": len(variants), "note": ", ".join(variants)})
    for k, v in reasons.most_common():
        rows.append({"stage": "Tier B configurations that need a human or a data check: reason (keyword classification)", "item": k, "count": v, "note": ""})
    cstatus, creasons = Counter(), Counter()
    for f in sorted(glob.glob(str(ROOT / "harness" / "cards" / "*.json"))):
        c = json.load(open(f, encoding="utf-8"))
        cstatus[c.get("status")] += 1
        if c.get("status") == "blocked":
            creasons[classify((c.get("blockers") or [""])[0], CARD_RULES)] += 1
    for k, v in cstatus.items():
        rows.append({"stage": f"Tier A claim cards ({sum(cstatus.values())})", "item": k, "count": v, "note": ""})
    for k, v in creasons.most_common():
        rows.append({"stage": "Tier A blocked cards: first blocker (keyword classification)", "item": k, "count": v, "note": ""})
    ft = pd.DataFrame(rows)
    ft.to_csv(ROOT / "data" / "failure_taxonomy.csv", index=False, encoding="utf-8-sig")
    print("needs-human classification per config:")
    for w, s, l in per_wid:
        print("  ", w, s, "->", l)
    return ft


# ----------------------------------------------------------------------------------------------- S3
def model_types():
    life = pd.read_csv(ROOT / "data" / "model_lifecycles.csv")

    def kind(i):
        if i.startswith("text-"):
            return "legacy completion (text-*)"
        if "preview" in i:
            return "preview release"
        if i.startswith(("o1", "o3", "o4")):
            return "reasoning series (o1/o3/o4)"
        if i.startswith("gpt-5"):
            return "GPT-5 series"
        if re.search(r"20[0-9]{2}", i):
            return "dated chat snapshot"
        return "undated chat alias"
    life["type"] = life["id"].map(kind)
    rows = []
    for t, g in life.groupby("type"):
        rows.append({"type": t, "identifiers": len(g), "retired": int((g["status"] == "dead").sum()), "announced": int((g["status"] == "dying").sum()),
                     "median lifespan days": float(g["lifespan_days"].median()), "shortest": int(g["lifespan_days"].min()), "longest": int(g["lifespan_days"].max()),
                     "examples": ", ".join(g.sort_values("lifespan_days")["id"].head(3))})
    mt = pd.DataFrame(rows).sort_values("median lifespan days")
    mt.to_csv(ROOT / "data" / "model_type_lifespans.csv", index=False, encoding="utf-8-sig")
    return mt


# ----------------------------------------------------------------------------------------------- S4
DEVIATIONS = [
    ("W4414494504", "PGxRAG", "accuracy", "80.9", "78.8 (8.1 before the fix)", "reproduced", "scoring defect (parser), fixed",
     "replies quoted the option letter in prose; the first parser read the article 'a' as option A"),
    ("W4406880877", "o1 AI-text detector", "true positive rate", "54.0", "54.7 (30.0 before the fix)", "reproduced", "runner defect (duplicate item ids), fixed",
     "61 distinct ids for 150 articles; replies re-paired by request hash"),
    ("W4404781158", "MultiPragEval", "accuracy", "75.3", "76.9 (81.4 before the fix)", "reproduced", "reference cell mismatch, fixed",
     "Table 5 average covers the 240 implicature units, not the 60 literal-meaning units"),
    ("W4403882451", "Planning in Strawberry Fields (PlanBench)", "plan accuracy", "40.1", "34.9 (54.7 with an LLM judge)", "deviated", "scorer choice fixed; residual gap from the paper's extractor version",
     "rule-based extraction as in the release; the paper's 241/600 came from an extractor that dropped bold action lines; only 27/600 of the paper's replies match temperature-0 output of the dated snapshot"),
    ("W4403758464", "LLMs Still Can't Plan (same cell)", "plan accuracy", "40.1", "35.9", "close", "reference number from a pre-fix pipeline",
     "the current extractor scores the paper's own released replies 254/600"),
    ("W4399911213", "WikiContradict", "accuracy", "86.7", "81.1 (76.7 before the fix)", "deviated", "parser fixed; residual gap in judge behaviour",
     "341/720 replies omit the evaluation line; the model now labels partially-correct responses differently"),
    ("W4411080278", "Temperature-driven diagnostic variability", "leading-diagnosis accuracy", "100", "25.0 (50.1 before the fix)", "deviated", "output-style shift under the pinned snapshot",
     "keyword rule applied to the listed diagnosis as in the paper; the model now leads with the broader parent diagnosis plus an explanation; vignette transcription cannot be excluded"),
    ("W7166799942", "CMTD (MELD text-only)", "accuracy", "42.5", "13.2", "needs review", "protocol gap: unreported label mapping",
     "printed prompt names no label set; 1,705/2,610 utterances stay unlabelled under the 7-label parse; extended synonyms give 30.9"),
    ("W4401545735", "Financial PhraseBank (heterogeneous agents)", "accuracy", "74.6", "91.6", "deviated", "unreported prompt wording; the snapshot classifies better than the paper's naive cell",
     "subset and cell confirmed; snapshot pinned (6 fingerprints); a 17-point gap cannot come from parsing"),
    ("W7164614711", "M-EDESConv (I Understand How You Feel)", "macro-F1", "51.7", "41.6", "deviated", "class-prior shift under the pinned snapshot",
     "validate-class F1 matches (53.4 vs 54.4) but the model says 'validate' for 83% of utterances against about 69% implied by the paper"),
    ("W4415035710", "Gender entropy bias", "Welch t", "2.00", "-0.23", "close", "within the metric's own noise; the original was marginal (p = 0.04)",
     "pipeline verified on the released data (t = 2.005 recomputed); three iterations -0.26 / -0.36 / -0.07"),
    ("W4404792825", "Sink or Swim (GSE)", "GSE total, 10-40", "31.4", "29.0", "close", "instruction line reconstructed; zero variance at temperature 0",
     "all 30 replies byte-identical (one fingerprint)"),
    ("W4407571428", "PhysiCo (Stochastic Parrot)", "accuracy", "41.3", "35.7", "deviated", "grid serialisation not specified by the paper",
     "parse verified on all 600 replies; 593 end with an option line"),
    ("W4406058598", "Halu-J", "accuracy", "83.0", "88.5", "deviated", "unexplained under a pinned snapshot; decoding temperature and evidence order unreported",
     "label map confirmed by the confusion matrix; the model rarely answers Neutral (51 of 327)"),
    ("W4399404161", "MMLU-Pro", "accuracy", "63.7", "68.0", "close", "gap confined to quantitative subjects; consistent with lost long chain-of-thought answers in the paper's run",
     "physics 72.7 vs 61.0, engineering 50.8 vs 35.9; humanities match; cost-cap subset of 1,652 items"),
    ("W4403556032", "Healthcare trust, atypical presentations", "accuracy", "75.1", "81.1 (all 1,272 items)", "deviated", "unexplained under a pinned snapshot; the gap held when the run was extended from 823 to all 1,272 items",
     "Table 2 cell with the one-line prompt; three seeds agree; code repository exists"),
    ("W7161421448", "Implicit bias in LLM counselling (paternalism)", "odds ratio", "136.6", "247", "deviated", "direction and significance hold; magnitude larger",
     "all 2,348 generated stories judged: present 1012/214 vs absent 21/1097; CI [157, 390]"),
    ("W7197053912", "ANCHOR-RE baseline (SemRepGS)", "micro-F1", "65.4", "57.5", "deviated", "over-prediction of positive relations under an approximated prompt slot",
     "recall matches the paper (0.83 vs 0.84) but precision is 0.44 vs 0.53: the model assigns a relation to 60% of pairs where the gold set has 32%; the layout of the candidate definitions inside the Appendix A prompt is not printed and was taken from the code release; 6 of 9,633 replies unparsed"),
    ("W4416036577", "Cross-domain rumor detection (COVID-19 Twitter)", "accuracy", "64.3", "52.3", "deviated", "paper-side unreported step, partly confirmed: the stand-alone LLM baseline differs by source domain (64.3 vs 58.1 on the same 400 targets), which a zero-shot prompt cannot produce; adding four source-domain demonstrations (our layout) raised the re-run from 52.3 to 57.5, a third of the gap",
     "parse clean (0/1,200), label mapping confirmed against Table 6 (flipping would give 47.8); three seeds within 1.3 points; the model reads 'rumor' as misinformation and sits near chance on the PHEME-style label; variant run W4416036577v2 (2026-09-19): 57.5, seeds 58.3/58.0/56.3, CI 53.5-63.3, paper value still outside"),
    ("W4399912745", "ALiiCE (ASQA, GPT-4 5-passage correctness)", "exact-match recall", "47.0", "37.6", "deviated", "short answers from the pinned snapshot (format hypothesis rejected: the code release's prompt layout gives 37.1); the successor gpt-5.6-sol reproduced the paper's 47.0",
     "scorer matches ALCE utils/eval line for line; 907/907 stop, none empty; outputs average 19.6 words vs the paper's 28.1 and cover one sub-answer where the gold has two to six; 56% of sub-answers are present in the five passages; variant run W4399912745v2 (2026-09-19, all 948 items, code-release prompt): 37.1, CI 35.2-39.1, median reply 25 tokens under both prompts; P3 vendor arm on gpt-5.6-sol: 46.7"),
    ("W4412887943", "MEDEC (Tier A)", "error-flag / error-sentence accuracy", "65.8 / 56.7 (Table 2 'GPT-4o')", "56.1 / 46.1", "partial", "paper-side label ambiguity: the re-run matches the 'GPT-4o-mini' row (60.9 / 47.6) within 5 points",
     "MS subset 597/925; three passes agree; scorer reproduces the shared-task script on the released baseline run exactly"),
    ("W4411120389", "Greedy vs sampling, HumanEval (Tier A)", "greedy minus sampled pass@1", "5.5 (89.6 vs 84.1)", "1.5 (88.4 vs 86.9)", "partial", "direction holds (greedy above sampling, p < 0.001 over 32 runs) but the gap shrank from 5.5 to 1.5 points; sampled runs are now less variable (std 1.4 vs 2.65)",
     "released archive holds 32 sampled runs, not the 128 the paper states, and re-scoring it reproduces Table 2 (89.6 / 84.1 / 5.5); our 32 runs: min 82.9, max 90.9; 13 problems fail under greedy but pass in some sample"),
    ("W4404782878", "Judgement bias (Tier A)", "attack success rate x100", "6 / 16 / 32 / 7", "8.2 / 9.5 / 33.0 / 24.2", "partial", "scoring defect fixed (354 direct-variant verdicts written as sentences were dropped); residual rich-content bias is a judge-behaviour difference",
     "first pass read 37.1 for reference and 32.3 for rich content and was labelled dead; reading the verdict from the sentence subject recovers 334 replies; rich-content shift is consistent across the three prompts; substitute snapshot gpt-4o-2024-05-13 for the retired 1106-preview"),
]


def deviation_causes():
    dv = pd.DataFrame(DEVIATIONS, columns=["wid", "paper", "metric", "reported", "re-run", "provisional class", "cause after triage", "evidence"])
    dv.to_csv(ROOT / "data" / "deviation_causes.csv", index=False, encoding="utf-8-sig")
    return dv


def main():
    t1, alias_df, vend = census_summary()
    ft = failure_taxonomy()
    mt = model_types()
    dv = deviation_causes()
    parts = [
        "# Supplementary tables (generated by scripts/supp_tables.py)", "",
        f"Census time-to-loss numbers use the vendors' published retirement dates as the event (every identifier in the census has one; nothing is censored); 'km_median_months' is the Kaplan-Meier median censored at {TODAY}, the estimand of the earlier versions, and 'lost_by_today_pct' the share lost by that date. The origin is the publication date, with year-only dates (printed by OpenAlex as 1 January) placed at 1 July and papers dated before the release of the first-retiring identifier started at that release. Born-dead papers name a model that was already retired at the origin; they are excluded from the curves and reported separately.", "",
        "## Table S1. Census cohort summary", "",
        md_table(t1), "",
        "### S1a. How dateless aliases resolve (alias-date rules for gpt-4-turbo, gpt-3.5-turbo and gpt-4o)", "", md_table(alias_df), "",
        "### S1b. Identifiers per vendor", "", md_table(vend), "",
        "## Table S2. Why papers could not be re-executed", "", md_table(ft), "",
        "## Table S3. Lifespan of the identifiers by type", "", md_table(mt), "",
        "## Table S4. Deviations and their causes after triage", "", md_table(dv), "",
    ]
    for fn, title in (("sensitivity_survival.csv", "Table S5. Sensitivity of the time to loss to the analysis choices: the base row is the published-date estimand with the corrected origins; the second and third rows are the as-of Kaplan-Meier estimand of the earlier versions (censored at the analysis date and the day after the 23 October 2026 retirements); the last rows re-analyse the census as it stood under each earlier vocabulary with the current rules and dates (scripts/sensitivity.py)"),
                      ("sensitivity_tierb.csv", "Table S6. Sensitivity of the Tier B provisional classes to the class rule and to cost-cap subsets"),
                      ("cox_hazard_ratios.csv", "Table S7. Cox proportional-hazards model (Efron ties), hazard of losing the first named model"),
                      ("coding_main_summary.csv", "Table S8. Manual coding of dependence, main sample (codebook v1.3; 500 census papers, two coders per paper, third-coder adjudication of 60 identifiers in 47 papers): papers by resolution, dependence share with its Wilson interval and post-stratified to the 2 September sampling frame with the implied census counts, shares by identifier status, field group and stratum, Krippendorff's alpha and pairwise kappa per item, per-coder shares, and the designation, run-date and web-interface rates among dependent papers (scripts/coding_main_report.py). The pilot of 30 papers coded by all four coders (codebook v1.2) gave 77% (59-88%), alpha 0.78 for the role code and 0.94 for the dependence dichotomy."),
                      ("tierb_selection.csv", "Table S10. Tier B selection: eligible versus executed papers by stratum, with the judged classes of the executed papers"),
                      ("tierb_selection_reweighted.csv", "Table S11. Tier B provisional class shares (%) after re-weighting the executed papers to the eligible population, one dimension at a time"),
                      ("p3_agreement.csv", "Table S12. Agreement between successor arms on the papers scorable in both: deviated versus not deviated, Cohen's kappa and the exact McNemar p-value of the discordant counts"),
                      ("p3_leniency.csv", "Table S13. Successor arms: 'moved' as the class 편차 (used in the text) versus the raw |delta| > 5 rule, reproductions by the interval clause alone, and low-precision results"),
                      ("p3_figure_by_category.csv", "Table S14. Successor arms by task type and field group: papers, median difference from the reported value (points) with its bootstrap 95% interval, and the share of papers beyond 5 points"),
                      ("loss_typology.csv", "Table S15. Modes of reproducibility loss observed in this study: for each mode and stage the count, the denominator, the share and the preservation-protocol item that answers it"),
                      ("effort_accounting.csv", "Table S16. What the re-execution cost: papers, archived API calls, spend by provider, deposit size per stage and per paper, and the incidents that interrupted the work"),
                      ("p3_predictors_univariate.csv", "Table S17. Which successor results move: share of results classed as deviated by covariate level, with Wilson 95% intervals (unit: one scorable result, paper x arm)"),
                      ("p3_predictors_model.csv", "Table S18. Pooled logistic regression of a successor deviation on arm, task type, field group, metric family, baseline class, original model family, reported value and item count; odds ratios with 95% intervals, standard errors clustered by paper"),
                      ("reexec_forest_by_category.csv", "Table S19. Pre-shutdown re-execution by task type and OpenAlex field: claims or papers, judged classes, median difference from the reported value with bootstrap 95% interval, share within 5 points"),
                      ("drift_control.csv", "Table S20. Same-snapshot drift control: 20 prompt-level papers re-run on their own pinned model with the baseline's items and request bodies; value against the baseline's seed-0 value and the reported value, class by the Tier B rule, share of items with identical parsed answers and identical raw text, fingerprints and run dates"),
                      ("cox_schoenfeld.csv", "Table S21. Proportional-hazards test on the scaled Schoenfeld residuals (Grambsch-Therneau) for the Cox model of Table S7, per covariate and globally, with the Kaplan-Meier, rank and identity transforms of time"),
                      ("cox_stratified.csv", "Table S22. Stratified Cox models: baseline hazard per publication year, per vendor group, and per year x vendor group (covariates that define the strata are dropped)"),
                      ("cox_period_hr.csv", "Table S23. Period-specific hazard ratios from the episode-split Cox model (follow-up split at 6, 12 and 24 months; the vendor and citation terms interact with the period, the other covariates stay constant)"),
                      ("p3_format_bound_summary.csv", "Table S24. Format bound for the successor conditions: scorable and deviated results, direction of the deviations, share of replies the paper's parser could not read, and deviations no larger than that share (explainable by format failures alone); per-result rows are in data/p3_format_bound.csv"),
                      ("born_dead_lag.csv", "Table S25. Born-dead papers: lag from the retirement of the first named model to the publication date, by document type"),
                      ("baseline_seed_spread.csv", "Table S26. Seed-to-seed spread of the pre-retirement baselines: values, range and standard deviation over the seeds on the paper's scale"),
                      ("p3_repeat_spread.csv", "Table S27. Seed-variance check of the successor conditions: for 20 papers and each condition, the value of the original call and of two fresh calls on identical request bodies (paper's scale), their range and standard deviation, the class of each call against the reported value under the prompt-level rule, and whether the class is the same for all three calls"),
                      ("p3_repeat_summary.csv", "Table S28. Seed-variance check by condition: papers, median, upper quartile and maximum of the call-to-call range, papers whose range exceeds 2 and 5 points, and share of papers whose class is stable over the three calls"),
                      ("p3_bf16_compare.csv", "Table S29. BF16 check of the open-weight condition: 12 papers re-run with identical request bodies on a dedicated bfloat16 deployment of Llama 3.3 70B Instruct (4x H100) against the FP8 serverless build used in the condition; values on the paper's scale, difference, unparsed replies and class under each build"),
                      ("p3_paraphrase_spread.csv", "Table S30. Wording check on the pinned models: for 18 same-snapshot control papers, the value on the paper's scale of the pre-retirement baseline (seed 0), of the same-snapshot control and of two rewordings of the fixed instruction text (p1, p2) sent to the same pinned model; the wording range (maximum minus minimum over baseline, p1 and p2), the dating range (control minus baseline), the class of each run against the reported value under the prompt-level rule, whether the class is the same under all three wordings, and the shift and class of the same paper on the designated replacement"),
                      ("p3_paraphrase_summary.csv", "Table S31. Wording check summary: papers, median, upper quartile and maximum of the wording range, papers whose range exceeds 2 and 5 points, share of papers whose class is stable over the wordings, the dating range of the same papers, the successor shift on the same papers and the call-to-call range of the seed-variance repeat for comparison"),
                      ("tiera_successor_claims.csv", "Table S32. Successor condition for five repository-based papers: for each claim the reported value, the pre-retirement re-run and the value on the vendor's designated replacement with its interval, the differences in points on the paper's scale, whether the reported value lies inside the successor interval, and the provisional class against the reported value and against the pre-retirement re-run under the prompt-level rule"),
                      ("format_cases.csv", "Table S33. Format-adaptation case studies on the designated replacement: for the vendor-arm result left unscorable by format non-compliance, every scorable vendor-arm result with more than 5% unparsable replies and one contrast case, the reported value, the pre-retirement baseline, the vendor-arm result under the paper's own parser, the same replies re-scored after stripping markdown emphasis (L1, no new calls), and one pass each with one added format sentence (f1) and with that sentence plus the successor's lowest reasoning setting (f2), with unparsable counts, classes against the reported value and spend"),
                      ("p3_selection_raking.csv", "Table S34. Joint re-weighting (raking) of the executed papers to the 216 eligible papers over field group, year, document type, task type, model family and cost tier at once: raw and raked shares of results deviated on the designated replacement and of papers reproduced or deviated before retirement, with bootstrap 95% intervals, weight range, design effect, the one-dimension-at-a-time shares and the share of the population covered by the sample's strata"),
                      ("p3_selection_bounds.csv", "Table S35. Bounds for the eligible population: the share of eligible papers deviated on the designated replacement and the share whose result carries over, under stated assumptions about the papers without a scorable successor result (from no deviation to every one deviated), and the implied share of triaged candidates whose result demonstrably carries over, with and without the undecided candidates"),
                      ("census_survival_unconditional.csv", "Table S36. Kaplan-Meier survival analysis, censored at the analysis date (still-served identifiers have no retirement date, so the published-date estimand of Table S1 does not apply), with still-served identifiers included: papers naming only still-served identifiers enter as right-censored observations, and identifiers retired or deprecated since the vocabulary was fixed are added; for each variant the papers in the curve, events, share lost by the censoring date, median and quartiles of the time to first retirement, survival at 12 and 24 months, overall and by vendor"),
                      ("claim_level_cases.csv", "Table S37. Claim-level reading of the largest successor moves (the first author's reading of the cases; the judges' conclusion level for every result is in Table S44): the five repository-based papers run on the designated replacement and the three largest upward and three largest downward prompt-level moves, with the reported value, the pre-retirement baseline, the successor value, the kind of claim the paper builds on the number and what the successor value does to that claim"),
                      ("temperature_check.csv", "Table S38. Temperature sensitivity check: the prompt-level papers silent on decoding whose configuration assumed temperature 0 and whose task is generation or free text, re-run on their pinned model at temperature 1.0 (the API default) with the baseline's seed count; reported value, baseline at temperature 0 and re-run at 1.0 with intervals and unparsable counts, the class of each against the reported value, the difference in points and the spend"),
                      ("p3_threshold_sweep.csv", "Table S39. Threshold sweep for the successor conditions: for each condition the scorable results, the median absolute move from the reported value on the paper's 0-100 scale, the class 'deviated' count for comparison, and the number and share of results that move by more than 2, 3, 5, 10 and 20 points; the first row is the pre-retirement baseline (prompt-level papers measured on the points scale, re-run minus reported value). Unit: one scorable result; a move is |value - reported value| in points, computed from data/p3_summary.csv and data/reexec_forest.csv by scripts/p3_agreement.py."),
                      ("triage_audit.csv", "Table S40. Audit of the eligibility triage: completeness of the agent-written triage records (a quoted passage and a location for the resolved live model, a claim cell with metric, value and item count, a data source, blockers for ineligible verdicts), outcome-based validation of the eligible class by the 86 configurations executed without human input, and agreement of a second reader (gpt-4.1-2025-04-14, 4 October 2026) with the original verdicts on a seeded random sample of 60 records, 20 per verdict class (scripts/triage_audit.py, scripts/triage_crossjudge.py). Unit: triage records."),
                      ("triage_crossjudge.csv", "Table S41. Triage cross-judgement, per record: the original verdict (Claude agents, September 2026) and the second reader's verdict (gpt-4.1-2025-04-14, 4 October 2026) under the same written rules and census hints, with the resolved live model, the role and the blockers of each reader, the text length and whether the text was truncated at 120,000 characters (archive runs/triage_crossjudge/)."),
                      ("km_median_ci.csv", "Table S42. Median time to loss at the published retirement dates with cluster-bootstrap 95% confidence intervals (1,000 resamples of the identifiers that retire first, seed 20260907; every paper follows its identifier, because the retirement dates are a few dozen vendor decisions rather than independent observations; resampling papers instead gave the degenerate 20.4-20.4 interval of the earlier version) and, beside it, the as-of Kaplan-Meier median censored at the analysis date with the same intervals, overall, by vendor (earliest retirement among that vendor's identifiers, papers naming the vendor), by document type and for the six largest primary fields; point estimates equal Table S1 (scripts/km_median_ci.py)."),
                      ("release_lag.csv", "Table S43. Decomposition of the time to loss for the papers in the survival curve: the lag from the release of the first-retiring identifier to the paper's publication, the lifespan of that identifier from release to retirement, and the time to loss from the corrected origin at the published retirement dates, medians and quartiles overall and by the vendor of the first-retiring identifier, with the as-of Kaplan-Meier median (censored at the analysis date) for comparison (scripts/release_lag.py). Undated aliases are read as the dated snapshot of the family the alias pointed to on the paper's publication date. The lag is measured from the publication date as indexed; papers whose indexed date precedes the release of the identifier (mostly conference papers and preprints, whose indexed date can precede the version that names the model) have a negative lag and start their time at risk at the release in the survival analysis."),
                      ("judgment_by_condition.csv", "Table S44. Judgement of survival by three co-authors, blind to condition: for each condition the results, the majority class (reproduced or survived, close or partial, deviated or died, could not be judged), the results in which the majority overturned the written rule, and the conclusion level (whether the sentence the paper builds on the number still holds at the re-run value: holds, holds in part, fails, cannot judge), with the deviated results whose claim nevertheless holds (a limitation the paper points out that grew larger). Repository-based claims are aggregated to papers by the worst class among a paper's claims (scripts/judgment_apply.py from data/judgment_final.csv)."),
                      ("judgment_agreement.csv", "Table S45. Judgement of survival: agreement between the three judges (Krippendorff's alpha and pairwise Cohen's kappa for the survival class and the conclusion level, rows with identical answers, rows without a majority), the rows where the majority overturned the written rule, the rule and the conclusion-level reading the judges applied, and the query rounds: each return was compared with the written rule and the rows that departed from it without a stated reason were returned to the judge with the rule restated; answers with a stated reason were kept, judges never saw each other's answers; the final returns of the three judges and the four returns of judge A are archived (coding/results_judgment/, coding/results_judgment/versions/), the earlier returns of judges B and C were overwritten on receipt and are not available. The alpha of 1.00 therefore measures compliance with the written rule after the query rounds, not independent agreement; the agreement of judge A's first return with the final files is reported in Table S46."),
                      ("judgment_first_return.csv", "Table S46. Agreement before the query rounds, as far as it can be measured: the classes of judge A's first return (archived) against the final majority and against the final returns of judges B and C, prompt-level results and repository-based claims separately (scripts/judgment_first_return.py)."),
                      ("coding_executed_halflife.csv", "Table S47. Time to loss counted on the identifiers the coders marked as executed, for the 360 manually coded papers judged dependent: the census rule (first retirement among every named identifier) against the first retirement among executed identifiers only, unweighted and post-stratified to the sampling frame (scripts/coding_executed_halflife.py)."),
                      ("rule_across_designs.csv", "Table S48. One classification rule applied to both re-execution designs: the prompt-level four-class rule and the repository-based claim rule, each applied to the 91 repository-based claims and the 80 prompt-level results on a points scale (data/reexec_forest.csv); units and papers per class, a paper taking the worst class among its claims (scripts/rule_across_designs.py)."),
                      ("threshold_sensitivity.csv", "Table S49. Sensitivity of the successor 'moved' shares to the threshold, the reference and the scale: the share beyond 5 points against the reported value and against the pre-retirement baseline, beyond 10 points, beyond 10% and 20% of the reported value, by metric family, for percentage-type metrics only, and for the papers with a measured noise floor (seed range, same-snapshot control, wording check) the share beyond both 5 points and that floor (scripts/threshold_sensitivity.py).")):
        p = ROOT / "data" / fn
        if p.exists():
            parts += [f"## {title}", "", md_table(pd.read_csv(p, encoding="utf-8-sig").round(3)), ""]
    (ROOT / "SUPPLEMENTARY_TABLES.md").write_text("\n".join(parts), encoding="utf-8")
    print(md_table(t1))
    print(md_table(alias_df))
    print(md_table(vend))
    print(md_table(ft))
    print(md_table(mt))
    print("-> SUPPLEMENTARY_TABLES.md")


if __name__ == "__main__":
    main()
