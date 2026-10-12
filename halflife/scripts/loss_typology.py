"""Two synthesis tables across the whole pipeline.

data/loss_typology.csv   - modes of reproducibility loss observed in this study, one row per mode and stage, with the
                           count, the denominator, the share and the preservation-protocol item that answers the mode.
                           Counts come from the census summary, the Tier B triage taxonomy (data/failure_taxonomy.csv),
                           the Tier A cards, the executed configurations, the successor archives and the deposit manifest.
data/effort_accounting.csv - what the re-execution cost per stage: papers, archived API calls, spend by provider,
                           deposit size and size per paper, plus the incidents that interrupted the work.
No API calls.
"""
import csv, glob, json, os, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def pct(a, b):
    return round(100.0 * a / b, 1) if b else ""


def main():
    tax = {}
    for r in csv.DictReader(open(ROOT / "data" / "failure_taxonomy.csv", encoding="utf-8-sig")):
        tax[(r["stage"], r["item"])] = int(r["count"])

    def tx(stage_prefix, item_sub):
        for (s, i), c in tax.items():
            if s.startswith(stage_prefix) and item_sub in i:
                return c
        return 0

    from supp_tables import census_summary
    t1, _, _ = census_summary()
    allrow = t1[t1["group"] == "all papers"].iloc[0]
    n_census, born_dead, in_curve = int(str(allrow["papers"]).replace(",", "")), int(str(allrow["born_dead"]).replace(",", "")), int(str(allrow["in_curve"]).replace(",", ""))
    lost_pct = float(allrow["lost_by_today_pct"])

    p3 = list(csv.DictReader(open(ROOT / "data" / "p3_summary.csv", encoding="utf-8-sig")))
    arms = ["vendor", "gpt41", "open70b", "gemini_flash"]
    unsc = {a: sum(1 for r in p3 if r["arm"] == a and r["class_vs_original"] == "확인 필요") for a in arms}
    scor = {a: sum(1 for r in p3 if r["arm"] == a and r["class_vs_original"] not in ("확인 필요", "해당없음")) for a in arms}
    dev = {a: sum(1 for r in p3 if r["arm"] == a and r["class_vs_original"] == "편차") for a in arms}
    tb = json.load(open(ROOT / "runs" / "tierb" / "batch1_tierb_summary.json", encoding="utf-8"))
    n_tb = len(tb)
    fps = [json.load(open(p, encoding="utf-8")).get("served", {}).get("n_fingerprints") for p in glob.glob(str(ROOT / "runs" / "tierb" / "W*" / "result.json"))
           if re.fullmatch("W[0-9]+", os.path.basename(os.path.dirname(p)))]
    fps = [f for f in fps if isinstance(f, int) and f > 0]          # models that return no fingerprint are left out
    judge_hooks = sum(1 for p in glob.glob(str(ROOT / "harness" / "tierb" / "hooks" / "W*.py")) if "def judge_requests" in open(p, encoding="utf-8").read())
    # parameters the third-party endpoint rejected, over the 67 papers of that arm (first request of each paper)
    rejected = Counter()
    n_third = 0
    for p in glob.glob(str(ROOT / "runs" / "tierb_p3" / "open70b" / "W*" / "requests.jsonl")):
        n_third += 1
        with open(p, encoding="utf-8") as fh:
            body = json.loads(fh.readline())["body"]
        for k in ("seed", "logprobs", "top_logprobs", "frequency_penalty", "presence_penalty"):
            if k in body:
                rejected[k] += 1
    n_rejected_papers = len({os.path.basename(os.path.dirname(p)) for p in glob.glob(str(ROOT / "runs" / "tierb_p3" / "open70b" / "W*" / "requests.jsonl"))
                             if any(k in json.loads(open(p, encoding="utf-8").readline())["body"] for k in ("seed", "logprobs", "top_logprobs", "frequency_penalty", "presence_penalty"))})
    minimal = sum(1 for p in glob.glob(str(ROOT / "harness" / "tierb" / "configs" / "W*.json"))
                  if (json.load(open(p, encoding="utf-8")).get("model", {}).get("params") or {}).get("reasoning_effort") == "minimal")
    # safety-blocked replies and hidden thinking on the Gemini arm
    blocked = 0
    think_pos = 0
    n_calls_g = 0
    for p in glob.glob(str(ROOT / "runs" / "tierb_p3" / "gemini_flash" / "W*" / "calls.jsonl")):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            n_calls_g += 1
            ch = (r["response"].get("choices") or [{}])[0]
            if "message" not in ch:
                blocked += 1
            u = r["response"].get("usage") or {}
            if u.get("total_tokens", 0) - u.get("prompt_tokens", 0) - u.get("completion_tokens", 0) > 0:
                think_pos += 1
    man = list(csv.DictReader(open(ROOT / "data" / "deposit_manifest.csv", encoding="utf-8-sig")))
    executed = {r["wid"] for r in tb}
    lic_unknown = len({r["wid"] for r in man if r["kind"] == "tierb" and r["wid"] in executed and str(r.get("data_licence", "")).lower().startswith("unknown")})
    lic_all = len({r["wid"] for r in man if r["kind"] == "tierb" and r["wid"] in executed})

    T = []  # mode, stage, count, denominator, share_pct, note, protocol item

    def add(mode, stage, count, denom, note, item):
        T.append({"mode": mode, "stage": stage, "count": count, "denominator": denom, "share_pct": pct(count, denom) if isinstance(count, (int, float)) and isinstance(denom, (int, float)) else "",
                  "note": note, "protocol_item": item})

    P1 = "dated snapshot identifier and fingerprint distribution in the paper; request-response logs deposited"
    add("1 identifier retired (access lost)", "census", round(lost_pct / 100 * in_curve), in_curve, f"papers in the survival curve whose first named model is already retired ({lost_pct}%); {born_dead:,} of {n_census:,} were born dead", P1)
    add("1 identifier retired (access lost)", "Tier B triage, ineligible reasons", tx("Tier B ineligible", "alias resolves to a retired") + tx("Tier B ineligible", "alias_unpinned"), 766, "alias resolves to a retired snapshot, or the alias was never pinned", P1)
    add("1 identifier retired (access lost)", "Tier A blocked cards", tx("Tier A blocked", "still-callable identifier is not what the paper ran"), 33, "the still-callable identifier is not the one the paper ran", P1)
    add("2 web interface only (no API snapshot)", "Tier B triage, ineligible reasons", tx("Tier B ineligible", "web interface"), 766, "results produced in a chat interface with no dated API snapshot", "run through the API with a dated snapshot, or record interface version and date with the transcripts")
    add("2 web interface only (no API snapshot)", "Tier A blocked cards", tx("Tier A blocked", "web interface"), 33, "", "same")
    add("1 identifier retired (access lost)", "Tier B triage, ineligible reasons (mixed with mode 3)", tx("Tier B ineligible", "not from a still-callable model, or is only in a figure"), 766, "the reported number is not from a still-callable model, or is given only in a figure; the triage code does not separate the two", P1)
    add("3 procedure under-reported (prompt, settings, item list)", "Tier B triage, ineligible reasons", tx("Tier B ineligible", "prompt not printed"), 766, "prompt not printed", "verbatim prompts, decoding parameters and item identifiers deposited")
    add("3 procedure under-reported (prompt, settings, item list)", "Tier B configurations needing a human", tx("Tier B configurations that need a human", "prompt not printed") + tx("Tier B configurations that need a human", "items only in a PDF"), 130, "prompt not printed or items only in a PDF among the eligible papers not executed", "same")
    add("3 procedure under-reported (prompt, settings, item list)", "Tier B deviations after triage", 2, 20, "deviations traced to an unreported step (prompt wording, label mapping) among the 20 deviated papers", "same")
    add("4 data unavailable, gated or licence-uncertain", "Tier B triage, ineligible reasons", tx("Tier B ineligible", "data not public"), 766, "", "items or their hashes deposited; licence recorded at submission")
    add("4 data unavailable, gated or licence-uncertain", "Tier B configurations needing a human", tx("Tier B configurations that need a human", "gated or unreleased data"), 130, "", "same")
    add("4 data unavailable, gated or licence-uncertain", "Tier A blocked cards", tx("Tier A blocked", "data unavailable") + tx("Tier A blocked", "repository gone"), 33, "data unavailable or licensed; repository gone", "same")
    add("4 data unavailable, gated or licence-uncertain", "deposit of this study", lic_unknown, lic_all, "executed Tier B runs whose data licence is still unknown", "same")
    add("5 auxiliary model dependency (LLM judge, parser, translator)", "Tier B triage, ineligible reasons", tx("Tier B ineligible", "auxiliary model"), 766, "judge or parser model already retired", "judge outputs deposited; judge snapshot pinned and dated")
    add("5 auxiliary model dependency (LLM judge, parser, translator)", "Tier B configurations needing a human", tx("Tier B configurations that need a human", "judge or auxiliary"), 130, "", "same")
    add("5 auxiliary model dependency (LLM judge, parser, translator)", "Tier B executed papers", judge_hooks, n_tb, "papers whose scoring needs a second model call; two successor runs could not be scored until the judge's account was restored", "same")
    add("5 auxiliary model dependency (LLM judge, parser, translator)", "Tier A executed papers", 1, 25, "DxGPT: retired judge replaced; judge swap (+4.5) separated from generator drift (-1.5)", "same")
    add("6 multi-stage, agentic or multimodal protocol", "Tier B configurations needing a human", tx("Tier B configurations that need a human", "multi-stage") + tx("Tier B configurations that need a human", "image or video"), 130, "multi-stage or sandboxed protocol; image or video input", "container or trace of the full pipeline, not only the prompt")
    add("6 multi-stage, agentic or multimodal protocol", "Tier B executed by task type", 1, 14, "agentic papers judged eligible versus executed", "same")
    add("7 outcome measured on people", "Tier B triage, ineligible reasons", tx("Tier B ineligible", "outcome measured on people"), 766, "cannot be re-executed by construction", "model outputs shown to participants deposited")
    add("7 outcome measured on people", "Tier A blocked cards", tx("Tier A blocked", "outcome measured on people"), 33, "", "same")
    add("8 terms-of-service and account policy", "Tier B triage, ineligible reasons", tx("Tier B ineligible", "terms-of-service"), 766, "jailbreak or harmful prompts not re-run on commercial APIs", "policy check before re-execution; bias audits kept on the original vendor")
    add("8 terms-of-service and account policy", "successor arms", 7, 74, "bias audits and one over-refusal benchmark kept off third-party accounts after an automated account termination", "same")
    add("9 provider-side change under a pinned identifier", "Tier B executed papers", sum(1 for f in fps if f >= 2), len(fps), f"papers served by two or more system fingerprints during one run, among papers whose model returns a fingerprint (range {min(fps) if fps else ''}-{max(fps) if fps else ''}); behavioural indices moved while item-level agreement stayed high (R5)", "fingerprint and date per call; at least three passes; same-snapshot re-run planned")
    dc = ROOT / "data" / "drift_control.csv"
    if dc.exists():
        drows = list(csv.DictReader(open(dc, encoding="utf-8-sig")))
        dev9 = sum(1 for r in drows if r["class_vs_baseline_seed0"] == "편차")
        deltas = sorted(abs(float(r["delta_vs_baseline_seed0_pts"])) for r in drows if r["delta_vs_baseline_seed0_pts"] != "")
        same = sorted(float(r["share_same_parsed"]) for r in drows if r["share_same_parsed"] != "")
        add("9 provider-side change under a pinned identifier", "same-snapshot re-run (drift control)", dev9, len(drows),
            f"papers whose metric moved to the deviated class when re-run on the same pinned snapshot with the same items and bodies 4-15 days later; median |delta| {deltas[len(deltas) // 2]:.1f} points, max {deltas[-1]:.1f}; median share of items with an identical parsed answer {same[len(same) // 2]:.2f}",
            "fingerprint and date per call; at least three passes; same-snapshot re-run before retirement")
    add("10 interface change on the successor", "successor arms", minimal, 74, "reasoning_effort 'minimal' rejected by the designated replacement (mapped to 'none')", "full request bodies archived, so a rejected field is visible")
    add("10 interface change on the successor", "third-party and open-weight arms", n_rejected_papers, n_third, f"papers whose body carries a field the third-party endpoint rejects ({dict(rejected)}); one 100k output allowance clamped by the hosted model", "same")
    add("11 hidden reasoning inside the output allowance", "Tier B executed papers", 2, n_tb, "o1 and gpt-5 papers: 36 of 128 and 97 of 113 replies empty at the authors' limits; repaired with a larger limit or the provider default", "max_tokens and consumed reasoning tokens recorded per call")
    add("11 hidden reasoning inside the output allowance", "Gemini arm", think_pos, n_calls_g, "calls that spent hidden thinking tokens at the lowest level; output allowance raised by 2,048 to keep answers", "same")
    add("12 format non-compliance or safety filtering on the successor", "successor arms", sum(unsc.values()), sum(scor.values()) + sum(unsc.values()), f"results unscorable because most replies did not carry the paper's answer field in a form its parser accepts (vendor {unsc['vendor']}, gpt-4.1 {unsc['gpt41']}, open-weight {unsc['open70b']}, Gemini {unsc['gemini_flash']})", "raw replies archived; parser rules deposited")
    add("12 format non-compliance or safety filtering on the successor", "Gemini arm", blocked, n_calls_g, "replies blocked by the provider's safety filter, scored as unparsable", "same")
    add("13 capability shift on replacement (the number moves)", "successor arms", sum(dev.values()), sum(scor.values()), f"scorable results more than 5 points from the reported value: vendor {dev['vendor']}/{scor['vendor']}, gpt-4.1 {dev['gpt41']}/{scor['gpt41']}, open-weight {dev['open70b']}/{scor['open70b']}, Gemini {dev['gemini_flash']}/{scor['gemini_flash']}", "report the number as a dated measurement; re-measure rather than cite when the model changes")
    with open(ROOT / "data" / "loss_typology.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(T[0].keys()))
        w.writeheader()
        w.writerows(T)

    # ---- effort accounting
    rows = list(csv.DictReader(open(ROOT / "budget_log.csv", encoding="utf-8")))
    cost = Counter()
    for r in rows:
        m, arm = r["model"], r["arm"]
        note = r.get("note") or ""
        key = ("Triage cross-judgement (60 verdicts, second reader)" if arm == "triage_crossjudge" else
               "Format-adaptation cases (three papers, two adaptations)" if "format_f" in note else
               "Temperature check (four papers)" if "temp1" in note else
               "Wording check (two rewordings, pinned model)" if "para_p" in note else
               "Repository-based successor (five papers)" if arm == "tierA_successor" else
               "BF16 check (open-weight, dedicated endpoint)" if "open70b_bf16" in note else
               "Seed-variance repeat (four conditions)" if "_rep" in note else
               "Drift control (same snapshot)" if "drift_ctrl" in note else
               "P3 vendor-designated (gpt-5.6)" if m.startswith("gpt-5.6") else "P3 gpt-4.1" if (m.startswith("gpt-4.1") and arm == "tierb_p3")
               else "P3 open-weight (Together)" if m.startswith("meta-llama") else "P3 Gemini 3.8 Flash (Google)" if m.startswith("gemini")
               else "Tier B prompt variants" if r["card"].endswith("v2") else "Tier B" if arm == "tierb" else "Tier A" if arm in ("tierA", "baseline_alive") else arm)
        cost[key] += float(r["cost_usd"])
    kinds = {"Tier A": ["tierA"], "Tier B": ["tierb", "tierb_superseded"], "Tier B prompt variants": ["tierb_variant"],
             "P3 vendor-designated (gpt-5.6)": ["tierb_p3_vendor"], "P3 gpt-4.1": ["tierb_p3_gpt41"],
             "P3 open-weight (Together)": ["tierb_p3_open70b"], "P3 Gemini 3.8 Flash (Google)": ["tierb_p3_gemini_flash"],
             "Drift control (same snapshot)": ["tierb_p3_drift_ctrl"],
             "Seed-variance repeat (four conditions)": ["tierb_p3_vendor_rep", "tierb_p3_gpt41_rep", "tierb_p3_open70b_rep", "tierb_p3_gemini_flash_rep"],
             "BF16 check (open-weight, dedicated endpoint)": ["tierb_p3_open70b_bf16"],
             "Wording check (two rewordings, pinned model)": ["tierb_p3_para_p1", "tierb_p3_para_p2"],
             "Repository-based successor (five papers)": ["tierA_successor"],
             "Format-adaptation cases (three papers, two adaptations)": ["tierb_p3_format_f1", "tierb_p3_format_f2"],
             "Temperature check (four papers)": ["tierb_p3_temp1"],
             "Triage cross-judgement (60 verdicts, second reader)": ["triage_crossjudge"]}
    papers = {"Tier A": 25, "Tier B": 86, "Tier B prompt variants": 2, "P3 vendor-designated (gpt-5.6)": 74, "P3 gpt-4.1": 49,
              "P3 open-weight (Together)": 67, "P3 Gemini 3.8 Flash (Google)": 67, "Drift control (same snapshot)": 20,
              "Seed-variance repeat (four conditions)": 80, "BF16 check (open-weight, dedicated endpoint)": 12,
              "Wording check (two rewordings, pinned model)": 36, "Repository-based successor (five papers)": 5,
              "Format-adaptation cases (three papers, two adaptations)": 6, "Temperature check (four papers)": 4,
              "Triage cross-judgement (60 verdicts, second reader)": 60}   # repeat: 20 papers x 4 conditions; wording: 18 papers x 2 rewordings; cross-judgement: 60 triage records
    provider = {"Tier A": "OpenAI", "Tier B": "OpenAI", "Tier B prompt variants": "OpenAI", "P3 vendor-designated (gpt-5.6)": "OpenAI", "P3 gpt-4.1": "OpenAI",
                "P3 open-weight (Together)": "Together AI (+ OpenAI second stages)", "P3 Gemini 3.8 Flash (Google)": "Google AI Studio (+ OpenAI second stages)",
                "Drift control (same snapshot)": "OpenAI",
                "Seed-variance repeat (four conditions)": "OpenAI, Together AI, Google AI Studio",
                "BF16 check (open-weight, dedicated endpoint)": "Together AI dedicated endpoint (4x H100, billed per minute)",
                "Wording check (two rewordings, pinned model)": "OpenAI", "Repository-based successor (five papers)": "OpenAI",
                "Format-adaptation cases (three papers, two adaptations)": "OpenAI", "Temperature check (four papers)": "OpenAI",
                "Triage cross-judgement (60 verdicts, second reader)": "OpenAI"}
    E = []
    for k, ks in kinds.items():
        mb = sum(int(float(r["bytes"])) for r in man if r["kind"] in ks) / 1e6
        calls = sum(int(float(r["records"] or 0)) for r in man if r["kind"] in ks and os.path.basename(r["path"]) == "calls.jsonl")
        n = papers[k]
        E.append({"stage": k, "papers": n, "archived_calls": calls, "cost_usd": round(cost[k], 2), "cost_per_paper_usd": round(cost[k] / n, 2),
                  "provider": provider[k], "deposit_MB": round(mb), "deposit_MB_per_paper": round(mb / n, 1)})
    E.append({"stage": "total", "papers": "", "archived_calls": sum(e["archived_calls"] for e in E), "cost_usd": round(sum(e["cost_usd"] for e in E), 2),
              "cost_per_paper_usd": "", "provider": "", "deposit_MB": round(sum(e["deposit_MB"] for e in E)), "deposit_MB_per_paper": ""})
    E.append({"stage": "incidents", "papers": "", "archived_calls": "", "cost_usd": "", "cost_per_paper_usd": "",
              "provider": "OpenAI credit exhaustion 4 times (client waits for auto-recharge); OpenAI account terminated once during bias-audit prompts, restored after appeal (about 30 h lost); Google Tier 1 quota (10K requests/day) until the paid tier changed; Together Cloudflare block without a User-Agent",
              "deposit_MB": "", "deposit_MB_per_paper": ""})
    with open(ROOT / "data" / "effort_accounting.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(E[0].keys()))
        w.writeheader()
        w.writerows(E)
    for e in E:
        print("  ", e)
    print(f"typology rows {len(T)} -> data/loss_typology.csv; effort rows {len(E)} -> data/effort_accounting.csv")


if __name__ == "__main__":
    main()
