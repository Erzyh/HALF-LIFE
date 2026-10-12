"""Tier A claim table from the run_meta.json files: one row per judged quantity with the reported value, the
re-run value, its 95% interval, the scale rule used by the forest plot and the judgment: the three judges' majority
per claim when data/judgment_final.csv exists (the automatic judgment then moves to judgment_auto), else the run's own.

Extractors are explicit per paper because every adapter reports its own schema. Output: data/tiera_claims.csv
(read by scripts/reexec_forest.py) and a markdown table on stdout. No API calls.
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROWS = []


def meta(wid):
    p = ROOT / "runs" / wid / "run_meta.json"
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def add(wid, label, orig, rerun, ci, rule, judgment, note=""):
    ROWS.append({"wid": wid, "label": label, "original": orig, "rerun": rerun,
                 "ci_lo": None if not ci or ci[0] is None else ci[0], "ci_hi": None if not ci or ci[0] is None else ci[1],
                 "rule": rule, "judgment": judgment or "", "note": note})


def main():
    m = meta("T1")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        add("T1", "Bio-image code generation: pass@1", r["original"]["pass@1"], r["reexecution"]["pass@1"], r["reexecution"]["bootstrap95_pass@1"], "x100", j)
    m = meta("W7171749161")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        add("W7171749161", "Tag Questions: tag effect on agreement", m["target_paper"]["original_values"]["tageff"], r["reexecution"]["tageff"], r["reexecution"]["ci90"], "x100", j, "90% interval as in the paper")
    m = meta("W7140135941")
    if m:
        rows, j = m["results"]["rows"], m["results"].get("judgment")
        for key, lab in (("noCoT/NA", "MedAbstain: accuracy, no abstain option"), ("noCoT/A", "MedAbstain: accuracy, abstain option"),
                         ("noCoT/AP", "MedAbstain: accuracy, distractor + abstain")):
            add("W7140135941", lab, rows[key]["orig_acc"], rows[key]["acc"], rows[key]["acc_ci95"], "x100", j)
        add("W7140135941", "MedAbstain: abstention rate (abstain option)", rows["noCoT/A"].get("orig_abstention") or 0.0, rows["noCoT/A"]["abstention"], None, "x100", j)
    m = meta("W4362598103")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        add("W4362598103", "News credibility: Spearman rho x100 vs expert ratings", r["original"]["rho_own"], r["reexecution"]["rho_own"], r["reexecution"]["rho_own_ci95"], "x100", j)
        add("W4362598103", "News credibility: refusal share", r["original"]["unrated_share"], r["reexecution"]["unrated_share"], None, "x100", j)
    m = meta("W7144391134")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        add("W7144391134", "BlindingLLMs: Pearson r x100, 1000-shot", r["icl_1000"]["orig_r"], r["icl_1000"]["r"], r["icl_1000"]["ci95"], "pts", j)
        add("W7144391134", "BlindingLLMs: Pearson r x100, 60-shot", r["icl_60"]["orig_r"], r["icl_60"]["r"], r["icl_60"]["ci95"], "pts", j)
        add("W7144391134", "BlindingLLMs: Pearson r, 0-shot", r["zeroshot"]["orig_r"], r["zeroshot"]["r"], None, "x100", j)
    m = meta("W4402565126")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        add("W4402565126", "Cultural bias: distance reduction (107 countries)", r["original"]["mean_reduction"], r["reexecution"]["mean_reduction"], r["reexecution"]["mean_reduction_ci95"], "other:distance", j)
        add("W4402565126", "Cultural bias: share of countries improved", r["original"]["share_improved"], r["reexecution"]["share_improved"], None, "x100", j)
    m = meta("W4412887943")
    if m:
        rows, j = m["results"]["rows"], m["results"].get("judgment")
        add("W4412887943", "MEDEC: error flag accuracy (vs Table 2 GPT-4o)", rows["err_flag_acc"]["orig"], rows["err_flag_acc"]["value"], rows["err_flag_acc"]["ci95_pooled"], "x100", j, "MS subset 597/925; GPT-4o-mini row 0.6086")
        add("W4412887943", "MEDEC: error sentence accuracy (vs Table 2 GPT-4o)", rows["err_sentence_acc"]["orig"], rows["err_sentence_acc"]["value"], rows["err_sentence_acc"]["ci95_pooled"], "x100", j, "MS subset 597/925; GPT-4o-mini row 0.4757")
    m = meta("W4412945732")
    if m:
        rows = m["results"]["rows"]
        for key, rr in rows.items():
            if rr.get("secondary"):
                continue
            model, cell = key.split("/")
            short = "gpt-4o" if model.startswith("gpt-4o") else "gpt-4-turbo"
            add("W4412945732", f"Glianorex {short}: accuracy, {cell.replace('_', ' ')}", rr["orig_acc"], rr["acc"], rr["acc_ci95"], "x100", rr.get("verdict") or m["results"].get("judgment"))
    m = meta("W4396768794")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        t1, t2 = r["track1_judge_matched"], r["track2_reexecution"]
        add("W4396768794", "DxGPT: strict top-1 (new vs archived diagnoses, same judge)", t1["strict"], t2["median_strict"], t2["median_strict_ci95"], "pts", j, "judge-matched comparison; Table 3 with the original judge 54.0")
        add("W4396768794", "DxGPT: top-5 (new vs archived diagnoses, same judge)", t1["top5"], t2["median_top5"], t2["median_top5_ci95"], "pts", j)
    m = meta("W4405408496")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        orig, rer = r["original_paper_tables"]["gpt-4o"]["task1"], r["reexecution"]["gpt-4o"]["task1"]
        for T in ("0.00", "1.50", "1.75", "2.00"):
            ci = rer[T]["passes"]["0"]["ci95"]["formatted_pct"]
            add("W4405408496", f"Temperature study gpt-4o: formatted numeric answers, T={T}", orig[T]["formatted_pct"], rer[T]["median"]["formatted_pct"], ci, "pts", j,
                f"median over {rer[T]['n_passes']} pass(es)")
        for T in ("0.00", "2.00"):
            ci = rer[T]["passes"]["0"]["ci95"]["mape_pct"]
            add("W4405408496", f"Temperature study gpt-4o: MAPE of formatted answers, T={T}", orig[T]["mape_pct"], rer[T]["median"]["mape_pct"], ci, "pts", j)
        mo, mr = r["original_paper_tables"]["gpt-4o-mini"]["task1"], r["reexecution"]["gpt-4o-mini"]["task1"]
        add("W4405408496", "Temperature study gpt-4o-mini: formatted numeric answers, T=2.00", mo["2.00"]["formatted_pct"], mr["2.00"]["median"]["formatted_pct"], mr["2.00"]["passes"]["0"]["ci95"]["formatted_pct"], "pts", j)
    m = meta("W4400435289")
    if m:
        rows, j = m["results"]["rows"], m["results"].get("judgment")
        for key, rr in rows.items():
            if isinstance(rr, dict) and "acc" in rr and "orig_acc" in rr:
                add("W4400435289", f"SAD-mini {key}: accuracy", rr["orig_acc"], rr["acc"], rr.get("acc_ci95"), "x100", j, "substitute snapshot gpt-4o-2024-05-13")
            elif isinstance(rr, dict):
                val = rr.get("score", rr.get("value"))
                orig = rr.get("orig", rr.get("orig_score", rr.get("original")))
                if val is not None and orig is not None:
                    add("W4400435289", f"SAD-mini {key}", orig, val, rr.get("ci95"), "pts" if float(orig) > 1.5 else "x100", j, "substitute snapshot gpt-4o-2024-05-13")
    m = meta("W4404782878")
    if m:
        rows, j = m["results"]["rows"], m["results"].get("judgment")
        for key, lab in (("factual_error", "factual error"), ("gender", "gender"), ("reference", "reference"), ("rich_content", "rich content")):
            rr = rows[key]
            add("W4404782878", f"Judgement bias: attack success rate, {lab}", rr["orig_asr"], rr["asr"], rr.get("asr_ci95"), "x100", j, "substitute snapshot; 6-vote composition assumed")
    m = meta("W4411120389")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        rx, paper = r["reexecution"], r["original"]["paper"]
        b = rx.get("bootstrap95") or {}
        add("W4411120389", "Greedy vs sampling (HumanEval): greedy pass@1, median of 3 repeats", paper["greedy"], rx["greedy_median"], b.get("greedy_median_ci95"), "pts", j)
        add("W4411120389", "Greedy vs sampling (HumanEval): sampled pass@1, mean of 32 runs", paper["sample_mean"], rx["sample"]["mean"], b.get("sample_mean_ci95"), "pts", j, "paper states N=128; the released archive holds 32 runs")
        add("W4411120389", "Greedy vs sampling (HumanEval): greedy minus sampled gap", paper["gap"], rx["gap"], b.get("gap_ci95"), "pts", j)
    # ---- second-pass cards (2026-09-19/20); each adapter has its own results schema
    def g(d, *keys, default=None):
        for k in keys:
            if isinstance(d, dict) and d.get(k) is not None:
                return d[k]
        return default
    m = meta("W4416074906")
    if m:
        rows, j = m["results"]["rows"], m["results"].get("judgment")
        for persona, rr in rows.items():
            if isinstance(rr, dict) and rr.get("cms") is not None and rr.get("orig") is not None:
                add("W4416074906", f"AgentMisalignment: misalignment score, persona {persona}", rr["orig"], rr["cms"], rr.get("cms_ci95"), "x100", j, "6 scenarios per persona")
    m = meta("W4404781910")
    if m:
        rows, j = m["results"]["rows"], m["results"].get("judgment")
        for bias, rr in rows.items():
            if isinstance(rr, dict) and rr.get("acc") is not None and rr.get("orig") is not None:
                add("W4404781910", f"OffsetBias: EvalBiasBench accuracy, {bias.replace('_', ' ')}", rr["orig"], rr["acc"], rr.get("ci95"), "pts", j, f"n={rr.get('n')} pairs x 2 orders")
    m = meta("W4400103831")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        pub, rows = r.get("published_table2") or {}, (g(r.get("arms"), "primary") or {}).get("rows") or {}
        for writer, lab in (("gpt4", "GPT-4 reports"), ("gpt35", "GPT-3.5 reports"), ("human", "human reports")):
            rr = rows.get(writer) or {}
            if rr.get("avg") is not None and (pub.get(writer) or {}).get("avg") is not None:
                add("W4400103831", f"BADGE: GPT-4 judge score of {lab} (1-10)", pub[writer]["avg"], rr["avg"], g(rr, "ci95", "avg_ci95", "ci95_over_matches"), "other:1-10 judge score", j, "GPT-4 reports regenerated; other writers' released reports re-judged")
    m = meta("W7166808082")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        add("W7166808082", "TURTLEAI: symbolic success rate, DSReal (o3)", r["original_pct"], r["symbolic_success_rate_pct"], r.get("ci95_bootstrap_over_items"), "pts", j, "102 tasks x 3 seeds; 30 replies without code")
    m = meta("W4411119263")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        add("W4411119263", "ReIFE: evaluator accuracy vs human preference, macro mean of 4 datasets", r["original_avg"], r["macro_mean"], r.get("macro_ci95"), "pts", j, "repository run; prompt-level Tier B run 84.39")
        for ds, rr in (r.get("per_dataset") or {}).items():
            if isinstance(rr, dict) and rr.get("acc") is not None and rr.get("original") is not None:
                add("W4411119263", f"ReIFE: accuracy, {ds}", rr["original"], rr["acc"], g(rr, "ci95", "acc_ci95"), "pts", j)
    m = meta("W4416035547")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        add("W4416035547", "Interlocutor awareness: self-identification accuracy, MATH-500 (o4-mini)", r["original"], r["accuracy_median_over_seeds"], r.get("accuracy_ci95_items"), "x100", j, "card reads Figure 11 as 0.64; the Tier B config carried 0.93 (open)")
    m = meta("W4403885225")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        add("W4403885225", "Judge bias: verbosity robustness rate (500 fact items)", 0.915, r["rr"], r.get("rr_ci95"), "x100", j, "unparsable verdicts dropped (1%)")
        add("W4403885225", "Judge bias: unperturbed consistency rate (noise floor)", 0.990, r["cr"], r.get("cr_ci95"), "x100", j)
    m = meta("W4406880877")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        s0 = ((r.get("reexecution") or {}).get("per_seed") or {}).get("0") or {}
        orig = (r.get("original") or {}).get("overall") or {}
        if s0.get("tpr") and orig.get("tpr") is not None:
            add("W4406880877", "AI-text detection (o1 zero-shot CoT): true positive rate, 150 AI articles", orig["tpr"], s0["tpr"]["pct"], s0["tpr"].get("ci95"), "pts", j)
        if s0.get("fpr") and orig.get("fpr") is not None:
            add("W4406880877", "AI-text detection (o1 zero-shot CoT): false positive rate, 150 human articles", orig["fpr"], s0["fpr"]["pct"], s0["fpr"].get("ci95"), "pts", j)
    m = meta("W4412887747")
    if m:
        rows, j = m["results"]["rows"], m["results"].get("judgment")
        for ds, orig_v, lab in (("aitqa", 88.57, "AIT-QA"), ("infotabs", 58.60, "InfoTabs")):
            rr = rows.get(ds) or {}
            sm, ci = rr.get("scores_median") or {}, rr.get("ci95_over_items") or {}
            if sm.get("repo_original") is not None:
                add("W4412887747", f"TAMA: GPT-4-turbo exact-match accuracy, {lab} (repository scorer)", orig_v, sm["repo_original"], ci.get("repo_original"), "pts", j, "repository scorer counts containment; strict scorer 0.0 (verbose replies)")
    m = meta("W4407012395")
    if m:
        rows, j = m["results"]["rows"], m["results"].get("judgment")
        for model, splits in rows.items():
            for split, rr in (splits or {}).items():
                if isinstance(rr, dict) and rr.get("acc_pct") is not None and rr.get("orig_pct") is not None:
                    add("W4407012395", f"MedXpertQA Text: accuracy, {split} ({model})", rr["orig_pct"], rr["acc_pct"], rr.get("acc_ci95"), "pts", j if model.startswith("o1") else (m["results"].get("judgment_o3mini_row") or j), f"n={rr.get('n')}")
    m = meta("W4416034576")
    if m:
        rows, j = m["results"]["rows"], m["results"].get("judgment")
        for prompt, lab in (("COT", "CoT"), ("ROT", "RoT")):
            rr = rows.get(prompt)
            if rr and rr.get("repr_pct") is not None:
                add("W4416034576", f"AIRepr: o3-mini overall reproducibility on DiscoveryBench, {lab} prompt", rr["original"]["repr"], rr["repr_pct"], rr.get("repr_ci95"), "pts", j, f"n={rr.get('n_tasks_scored')} tasks x 3 seeds; o3-mini as inspector")
        d = m["results"].get("within_model_difference_RoT_minus_CoT")
        if d and d.get("point_pp") is not None:
            add("W4416034576", "AIRepr: RoT minus CoT reproducibility difference (pp)", d["original_pp"], d["point_pp"], d.get("ci95_pp"), "pts", j, "paired task-level bootstrap; the card's primary quantity")
    m = meta("W4399442646")
    if m:
        r, j = m["results"], m["results"].get("judgment")
        vs, boot = r.get("vs_original_figure3") or {}, (r.get("bootstrap") or {}).get("bins") or {}
        for key, v in sorted(vs.items()):
            if v.get("original") is None or v.get("rerun") is None:
                continue
            side, n = key.split("|n=")
            ci = (boot.get(n) or boot.get(int(n)) or {}).get(f"{side}_ci95")
            lab = "factual" if side == "f" else "anti-factual"
            add("W4399442646", f"ACCORD: gpt-4o {lab} accuracy at {n} reasoning hops (Figure 3 series)", v["original"], v["rerun"], ci, "x100", j,
                "reference digitised from the Figure 3 SVG; 95% CI = pairing-cluster bootstrap")
    out = ROOT / "data" / "tiera_claims.csv"
    jp = ROOT / "data" / "judgment_final.csv"  # the three judges' majority per claim (scripts/judgment_apply.py)
    if jp.exists():
        judged = {(r["wid"], r["label"]): r for r in csv.DictReader(open(jp, encoding="utf-8-sig")) if r["sheet"] == "TierA_claims"}
        for r in ROWS:
            j = judged.get((r["wid"], r["label"]))
            r["judgment_auto"] = r["judgment"]
            r["judgment"] = f"{j['majority']} (judged)" if j else r["judgment"]
            r["conclusion"] = j["conclusion_majority"] if j else ""
        print("judged claims applied:", sum(1 for r in ROWS if r["judgment"].endswith("(judged)")), "of", len(ROWS))
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(ROWS[0].keys()))
        w.writeheader()
        w.writerows(ROWS)
    print(f"{len(ROWS)} claim rows -> {out}")
    for r in ROWS:
        ci = f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]" if r["ci_lo"] is not None else "-"
        print(f"| {r['wid']} | {r['label']} | {r['original']:.4g} | {r['rerun']:.4g} {ci} | {r['judgment'][:24]} |")


if __name__ == "__main__":
    main()
