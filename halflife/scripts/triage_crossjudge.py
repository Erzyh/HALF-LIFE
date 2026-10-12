"""Cross-judgement of the eligibility triage: a second, independent reader re-screens a seeded random sample of
triage records under the same written rules, and the agreement with the original verdict is reported.

The original verdicts (harness/tierb/<Wid>.json, 1,185 records) were produced by language-model agents reading the
full text against harness/tierb/SCHEMA.md (first pass and conditional resolution: Claude Fable 5.1; second pass:
Claude Sonnet 5 and Opus 5). This script sends the same full text, the same schema and rules, and the same census
hints (publication date, still-callable identifiers found in the text) to a model from another vendor and asks for
the record. The second reader never sees the original verdict. This measures consistency between two readers under
one rule set; it is not a human gold standard.

Sample: 20 records per original verdict class (eligible, maybe, ineligible), seeded random (seed 20260907) among the
records whose full text is on disk. Second reader: gpt-4.1-2025-04-14 (temperature 0, seed 20260907, JSON output);
texts are truncated at 120,000 characters (noted per record). Every request and response is archived in
runs/triage_crossjudge/calls.jsonl with SHA-256 hashes, and the spend is appended to budget_log.csv. Hard cap:
the run stops when the cumulative cost exceeds the --cap (default US$9).

Outputs: data/triage_crossjudge.csv (one row per sampled record), data/triage_crossjudge_summary.csv (agreement
and Cohen's kappa, overall and per class). Usage: python scripts/triage_crossjudge.py [--dry] [--cap 9]
Re-running resumes: records already in calls.jsonl are not sent again.
"""
import argparse, csv, datetime, glob, json, random, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
from openai_client import OpenAIClient, cost_usd, sha256  # noqa: E402

MODEL = "gpt-4.1-2025-04-14"
SEED = 20260907
PER_CLASS = 20
MAX_CHARS = 120_000
RUN = ROOT / "runs" / "triage_crossjudge"
CLASSES = ("eligible", "maybe", "ineligible")

SYSTEM = ("You screen research papers for a re-execution study. Read the paper text and fill the triage record exactly as "
          "the schema and rules below prescribe. Decide only from the paper text and the census hints given; do not guess "
          "beyond them. Answer with one JSON object and nothing else.")


def load_records():
    recs = {}
    for f in glob.glob(str(ROOT / "harness" / "tierb" / "W*.json")):
        d = json.load(open(f, encoding="utf-8"))
        if d.get("verdict") in CLASSES:
            recs[Path(f).stem] = d
    return recs


def load_hints():
    hints = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "tierb_triage" / "group_*.csv"))):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            hints.setdefault(r["wid"], {"title": r["title"], "year": r["year"], "live_ids": r["live_ids"], "alias_note": r["alias_note"],
                                        "text_path": r["text_path"]})
    dates = {}
    with open(ROOT / "data" / "census_v2.csv", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        dcol = next((c for c in rd.fieldnames if c in ("date", "publication_date", "pub_date")), None)
        for r in rd:
            dates[r["openalex_id"].split("/")[-1]] = r.get(dcol, "") if dcol else ""
    return hints, dates


def text_for(wid, hint):
    p = ROOT / "external" / "papers_tierb" / f"{wid}.txt"
    if not p.exists() and hint and hint.get("text_path"):
        p = ROOT.parent / hint["text_path"]
    return p if p.exists() else None


def sample(recs, hints):
    rng = random.Random(SEED)
    chosen = []
    for cls in CLASSES:
        pool = sorted(w for w, r in recs.items() if r["verdict"] == cls and text_for(w, hints.get(w)) is not None)
        chosen += rng.sample(pool, PER_CLASS)
    return chosen


def normalise(v):
    v = str(v or "").strip().lower()
    return v if v in CLASSES else ("unparsable" if not v else v)


def kappa(a, b, labels):
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] * cb[l] for l in labels) / (n * n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="list the sample and the cost estimate; no API call")
    ap.add_argument("--cap", type=float, default=9.0, help="stop when the cumulative cost exceeds this many USD")
    a = ap.parse_args()
    recs = load_records()
    hints, dates = load_hints()
    schema = (ROOT / "harness" / "tierb" / "SCHEMA.md").read_text(encoding="utf-8")
    pricing = json.load(open(ROOT / "harness" / "pricing.json", encoding="utf-8"))["usd_per_1m"][MODEL]
    wids = sample(recs, hints)
    texts = {}
    for w in wids:
        t = text_for(w, hints.get(w)).read_text(encoding="utf-8", errors="replace")
        texts[w] = (t[:MAX_CHARS], len(t) > MAX_CHARS, len(t))
    est_in = sum(len(schema) + len(t[0]) for t in texts.values()) / 4 + 400 * len(wids)
    est = est_in / 1e6 * pricing["input"] + 1200 * len(wids) / 1e6 * pricing["output"]
    print(f"sample {len(wids)} records ({PER_CLASS} per class), truncated texts {sum(t[1] for t in texts.values())}, "
          f"estimated input tokens {est_in:,.0f}, estimated cost US${est:.2f} (cap {a.cap})")
    if a.dry:
        for w in wids:
            print(" ", w, recs[w]["verdict"], texts[w][2], "chars", "truncated" if texts[w][1] else "")
        return
    if est > a.cap:
        sys.exit("estimate exceeds the cap; not started")
    RUN.mkdir(parents=True, exist_ok=True)
    calls_path = RUN / "calls.jsonl"
    done = {}
    if calls_path.exists():
        for line in open(calls_path, encoding="utf-8"):
            d = json.loads(line)
            done[d["wid"]] = d
    client = OpenAIClient()
    spent = sum(d["cost_usd"] for d in done.values())
    started = datetime.datetime.now().isoformat(timespec="seconds")
    for w in wids:
        if w in done:
            continue
        if spent > a.cap:
            print(f"cap reached at US${spent:.2f}; stopping before {w}")
            break
        h = hints.get(w, {})
        user = (f"{schema}\n\n---\nCensus hints for this paper\nOpenAlex id: {w}\nTitle: {h.get('title', '')}\n"
                f"Publication date: {dates.get(w, '')} (year {h.get('year', '')})\n"
                f"Still-callable identifier strings found in the text by the census search: {h.get('live_ids', '')}\n"
                f"Alias note from the census: {h.get('alias_note', '')}\n\n---\nPaper text"
                + (" (truncated at 120,000 characters)" if texts[w][1] else "") + f"\n\n{texts[w][0]}\n\n---\n"
                "Return the triage record for this paper as one JSON object following the schema above.")
        body = {"model": MODEL, "temperature": 0, "seed": SEED, "max_tokens": 1500, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}
        resp, latency, status = client.chat(body)
        usage = resp.get("usage", {})
        c = cost_usd(usage, pricing)
        spent += c
        content = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
        try:
            rec = json.loads(content)
        except json.JSONDecodeError:
            rec = {}
        row = {"wid": w, "request_sha256": sha256(body), "response_sha256": sha256(resp), "request": body, "response": resp,
               "latency_ms": latency, "http_status": status, "usage": usage, "cost_usd": round(c, 6),
               "served_model": resp.get("model"), "system_fingerprint": resp.get("system_fingerprint"),
               "text_chars": texts[w][2], "truncated": texts[w][1], "parsed": rec}
        with open(calls_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        done[w] = row
        print(f"{w}: original {recs[w]['verdict']:10s} second {normalise(rec.get('verdict')):10s} "
              f"tokens {usage.get('prompt_tokens', 0):>6}/{usage.get('completion_tokens', 0):<5} US${c:.3f} (cum {spent:.2f})", flush=True)
    finished = datetime.datetime.now().isoformat(timespec="seconds")
    json.dump({"model": MODEL, "calls": len(done), "cost_usd": round(spent, 4), "seed": SEED, "per_class": PER_CLASS,
               "max_chars": MAX_CHARS, "started": started, "finished": finished, "pricing_usd_per_1m": pricing},
              open(RUN / "budget.json", "w", encoding="utf-8"), indent=1)
    # ---- per-record table and summary
    rows = []
    for w in wids:
        if w not in done:
            continue
        o, p = recs[w], done[w]["parsed"]
        ov, sv = o["verdict"], normalise(p.get("verdict"))
        lm = p.get("live_model") or {}
        rows.append({"wid": w, "original_verdict": ov, "second_verdict": sv, "agree_3class": int(ov == sv),
                     "agree_eligible_vs_not": int((ov == "eligible") == (sv == "eligible")),
                     "original_resolved_model": (o.get("live_model") or {}).get("resolved", ""), "second_resolved_model": lm.get("resolved", ""),
                     "original_role": (o.get("live_model") or {}).get("role", ""), "second_role": lm.get("role", ""),
                     "original_blockers": " ".join(o.get("blockers") or []), "second_blockers": " ".join(p.get("blockers") or []) if isinstance(p.get("blockers"), list) else str(p.get("blockers") or ""),
                     "text_chars": done[w]["text_chars"], "truncated": int(done[w]["truncated"]), "cost_usd": done[w]["cost_usd"]})
    with open(ROOT / "data" / "triage_crossjudge.csv", "w", newline="", encoding="utf-8-sig") as f:
        wri = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wri.writeheader()
        wri.writerows(rows)
    a3 = [r["original_verdict"] for r in rows]
    b3 = [r["second_verdict"] for r in rows]
    print(f"three-class agreement {100 * sum(x == y for x, y in zip(a3, b3)) / len(rows):.1f}%, kappa {kappa(a3, b3, CLASSES + ('unparsable',))}; "
          f"the audit table (scripts/triage_audit.py -> data/triage_audit.csv, Table S40) summarises these records")
    # ---- spend ledger
    log = ROOT / "budget_log.csv"
    last = list(csv.DictReader(open(log, encoding="utf-8")))[-1]
    new_cost = round(spent - sum(float(r["cost_usd"]) for r in csv.DictReader(open(log, encoding="utf-8")) if r["arm"] == "triage_crossjudge"), 2)
    if new_cost > 0:
        with open(log, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.date.today().isoformat(), "triage_crossjudge", "triage_crossjudge", MODEL, len(done), f"{new_cost:.2f}",
                                    f"{float(last['cumulative_usd']) + new_cost:.2f}", f"triage cross-judgement, {len(done)} verdicts re-read by a second model"])
    print(f"-> {calls_path} ({len(done)} calls, US${spent:.2f}); data/triage_crossjudge.csv, data/triage_crossjudge_summary.csv")


if __name__ == "__main__":
    main()
