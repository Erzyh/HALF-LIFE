"""Tier B screening, step 1: fetch full texts of the artifact-scan universe and score
'prompt-completeness' signals (proposal §3, SPRINT Week 2).

Tier B papers need no repository: the exact prompt is printed in the paper and a single
reported number (accuracy, F1, kappa, pass@k ...) can be re-measured on the still-alive
model. This pass fetches every paper that the artifact scan parsed (dying stratum, OA,
domain quotas; data/artifact_scan.csv joined to census_v2 for URLs and matched IDs),
saves the extracted text under external/papers_tierb/<Wid>.txt (gitignored), and writes
regex signal counts to data/tierb_screen.csv. Ranking and the human/LLM triage come later.

Resumable; ~2.5 s per paper. No API calls, no cost.
Usage: python scripts/tierb_fetch.py [--limit N]
"""
import argparse, csv, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from coding_evidence import ID_RE, VOCAB, fetch, html_text, normalize, pdf_text, refs_start  # noqa: E402

ROOT = HERE.parent
SCAN = ROOT / "data" / "artifact_scan.csv"
CENSUS = ROOT / "data" / "census_v2.csv"
TEXTS = ROOT / "external" / "papers_tierb"
OUT = ROOT / "data" / "tierb_screen.csv"
LOG = ROOT / "data" / "tierb_fetch.log"

STATUS = {m["id"]: m.get("status") for m in json.load(open(ROOT / "target_models.json", encoding="utf-8"))["models"]}
DYING = {m for m, s in STATUS.items() if s == "dying"}

SIGNALS = {
    "prompt_label": re.compile(r"(?im)^\s*(?:system prompt|user prompt|prompt template|prompt|instruction|instructions)\s*[:：]"),
    "you_are": re.compile(r"\bYou are (?:a|an|the)\b"),
    "prompt_words": re.compile(r"(?i)\b(?:exact|full|complete|verbatim) prompts?\b|prompts? (?:used|provided|given|shown) (?:in|to|for|are|is)\b"
                               r"|appendix\s+[A-Z0-9]+[.:]?\s+prompt|prompts? (?:are|is) (?:listed|provided|shown|given) in"),
    "long_quote": re.compile(r"[\"“]([^\"”]{150,1500})[\"”]"),
    "metric": re.compile(r"(?i)\b(?:accuracy|F1|exact match|pass@\d+|BLEU|ROUGE|Cohen'?s kappa|AUC|AUROC|precision|recall|macro-F1|micro-F1)\b"),
    "params": re.compile(r"(?i)\btemperature\b|\bmax[_ ]tokens\b|\btop[_ ]p\b|\bseed\b"),
    "api": re.compile(r"(?i)\bAPI\b|chat\.?completions?"),
    "webui": re.compile(r"(?i)web interface|chat interface|ChatGPT interface|chat\.openai\.com|through ChatGPT|via the ChatGPT"),
    "mcq": re.compile(r"(?i)multiple[- ]choice|\bMCQs?\b|answer options|choose the correct"),
    "human_outcome": re.compile(r"(?i)\bparticipants\b|\bpatients were\b|\bstudents were\b|\bsurvey of\b|\brespondents\b"),
}
FIELDS = ["openalex_id", "doi", "year", "citations", "field", "title", "matched_models", "live_ids_in_body",
          "fetch", "n_pages", "text_chars", "refs_frac", "n_links",
          *SIGNALS.keys(), "prompt_score"]


def score(text):
    text = normalize(text)
    rs = refs_start(text)
    body = text if rs is None else text[:rs]
    sig = {k: len(r.findall(body)) for k, r in SIGNALS.items()}
    live = sorted(m for m in DYING if ID_RE[m].search(body))
    ps = (2 * min(sig["prompt_label"], 5) + 2 * min(sig["you_are"], 5) + 2 * min(sig["prompt_words"], 3)
          + min(sig["long_quote"], 5) + min(sig["metric"], 5) + min(sig["params"], 3))
    return sig, live, ps, (None if rs is None else round(rs / max(1, len(text)), 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    census = {r["openalex_id"]: r for r in csv.DictReader(open(CENSUS, encoding="utf-8-sig"))}
    seen, frame = set(), []
    for r in csv.DictReader(open(SCAN, encoding="utf-8-sig")):
        wid = r["openalex_id"]
        if wid in seen or wid not in census:
            continue
        seen.add(wid)
        c = census[wid]
        frame.append({**c, "n_links": r.get("n_links", "0")})
    frame.sort(key=lambda r: -int(r["citations"] or 0))
    done = set()
    if OUT.exists():
        done = {r["openalex_id"] for r in csv.DictReader(open(OUT, encoding="utf-8-sig"))}
    todo = [r for r in frame if r["openalex_id"] not in done]
    if a.limit:
        todo = todo[:a.limit]
    print(f"frame {len(frame)} (scan ids with a census_v2 row); done {len(done)}; todo {len(todo)}", flush=True)
    TEXTS.mkdir(parents=True, exist_ok=True)
    new = not OUT.exists()
    log = open(LOG, "a", encoding="utf-8")
    with open(OUT, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        for i, r in enumerate(todo, 1):
            wid = r["openalex_id"].rsplit("/", 1)[-1]
            rec = {k: r.get(k, "") for k in ("openalex_id", "doi", "year", "citations", "field", "title", "matched_models", "n_links")}
            rec.update({"fetch": "none", "n_pages": "", "text_chars": 0, "refs_frac": "", "live_ids_in_body": "", "prompt_score": 0})
            rec.update({k: 0 for k in SIGNALS})
            url = r["oa_url"].strip()
            t0 = time.time()
            text = ""
            if url:
                if "arxiv.org/abs/" in url:
                    url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
                try:
                    ct, data = fetch(url)
                    if "pdf" in ct or data[:5] == b"%PDF-":
                        text, n = pdf_text(data)
                        rec["fetch"], rec["n_pages"] = ("pdf" if text.strip() else "pdf_unparsed"), n
                    else:
                        text = html_text(data)
                        rec["fetch"] = "html"
                except Exception as e:
                    rec["fetch"] = f"error:{type(e).__name__}"
            if text.strip():
                text = text.encode("utf-8", "replace").decode("utf-8")   # lone surrogates from PDF extraction
                (TEXTS / f"{wid}.txt").write_text(text, encoding="utf-8")
                sig, live, ps, rf = score(text)
                rec.update(sig)
                rec.update({"text_chars": len(text), "refs_frac": rf, "live_ids_in_body": "|".join(live), "prompt_score": ps})
            w.writerow(rec)
            f.flush()
            msg = f"[{i}/{len(todo)}] {wid} {rec['fetch']} score={rec['prompt_score']} live={rec['live_ids_in_body']} {time.time()-t0:.1f}s"
            print(msg, flush=True)
            log.write(msg + "\n")
            log.flush()
            time.sleep(2.5 if "arxiv.org" in url else 1.0)
    print("done", flush=True)


if __name__ == "__main__":
    main()
