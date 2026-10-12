"""Consolidate shortlist v1 + v2 into one eligibility sheet (data/p0_pool.csv).

Eligibility for P0 (pre-shutdown baseline) is computed from data, not judgment:
  live_arm   = matched model IDs whose status is 'dying' (still callable)
  P0-eligible = has live arm; otherwise P3-only (successor comparison)
Titles are matched from the markdown shortlists to the triage/top-up records.
"""
import csv, json, re
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data"
TM = json.loads((Path(__file__).resolve().parents[1] / "target_models.json").read_text(encoding="utf-8"))
status = {m["id"]: m["status"] for m in TM["models"]}
census = {r["openalex_id"]: r for r in csv.DictReader(open(D / "census_v2.csv", encoding="utf-8-sig"))}
triage = list(csv.DictReader(open(D / "p0_triage_v1.csv", encoding="utf-8-sig")))
topup = [json.loads(l) for l in open(D / "topup_candidates.jsonl", encoding="utf-8") if l.strip()]

TOS_RISK = re.compile(r"jailbreak|red team|attack|adversarial", re.I)
AGENTIC = re.compile(r"agent|travelplanner|agentless|swe-agent|codeagent|atomagents|debate", re.I)
NONPUBLIC = re.compile(r"board|clinical chemistry mcq|residency", re.I)


def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def bold_titles(md_path):
    out = []
    for line in open(md_path, encoding="utf-8"):
        m = re.search(r"\*\*(.+?)\*\*", line)
        if m and (re.match(r"^\s*(\d+\.|\|\s*T?\d+)", line)):
            out.append(m.group(1).split(" (")[0].strip())
    return out


STOP = {"a","an","the","of","for","in","on","and","with","to","vs","via","from","by","at","llm","llms","large","language","models","model"}

def toks(t):
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in STOP and len(w) > 2}

CENSUS_TOKS = [(oid, toks(r["title"])) for oid, r in census.items() if r["title"]]

MANUAL = {
    "durably reducing conspiracy": "durably reducing conspiracy beliefs through dialogues with ai",
    "deepseek-r1 vs openai o1": "deepseek-r1 in ophthalmology",
    "human vs ai: clinical chemistry": "chatgpt-4 outperforming bing",
    "cultural bias and cultural alignment": "cultural bias and cultural alignment of large language models",
    "genai and power imbalances": "power imbalances in global education",
    "length-controlled alpacaeval": "length-controlled alpacaeval",
    "radiation oncology physics": "radiation oncology physics using questions of randomly shuffled",
    "nano synthesis mechanism": "nano synthesis mechanism explanation",
    "matduck": "duck typing principles",
}

def manual_lookup(title):
    t = title.lower()
    for k, frag in MANUAL.items():
        if k in t:
            for oid, r in census.items():
                if frag in r["title"].lower():
                    return {"openalex_id": oid, "title": r["title"]}
    return None

def lookup(title, pool):
    m = manual_lookup(title)
    if m:
        return m
    k = norm(title)[:35]
    for r in pool:
        if norm(r["title"]).startswith(k) or k in norm(r["title"]):
            return r
    q = toks(title)
    best, score = None, 0.0
    for oid, tt in CENSUS_TOKS:
        if not tt:
            continue
        j = len(q & tt) / len(q | tt)
        if j > score:
            best, score = oid, j
    if best and score >= 0.45:
        return {"openalex_id": best, "title": census[best]["title"]}
    return None


rows = []
for src, md, pool in (("v1", D / "p0_shortlist_v1.md", triage), ("v2", D / "p0_shortlist_v2.md", topup)):
    for t in bold_titles(md):
        r = lookup(t, pool)
        oid = r["openalex_id"] if r else ""
        c = census.get(oid, {})
        models = c.get("matched_models", "").split("|") if c else []
        live = [m for m in models if status.get(m) == "dying"]
        dead = [m for m in models if status.get(m) == "dead"]
        title = c.get("title") or t
        flags = []
        if TOS_RISK.search(title): flags.append("tos-risk")
        if AGENTIC.search(title): flags.append("agentic/heavy")
        if NONPUBLIC.search(title): flags.append("data-check")
        rows.append({
            "source": src, "title": title, "field": c.get("field", ""), "year": c.get("year", ""),
            "citations": c.get("citations", ""), "live_models": "|".join(live), "dead_models": "|".join(dead),
            "p0_eligible": "yes" if live else ("no-live-arm" if models else "unmatched"),
            "flags": "|".join(flags), "openalex_id": oid,
        })

with open(D / "p0_pool.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

n = len(rows)
elig = [r for r in rows if r["p0_eligible"] == "yes"]
clean = [r for r in elig if not r["flags"]]
print(f"shortlist entries: {n}")
print(f"P0-eligible (live arm): {len(elig)} | no live arm (P3-only): {sum(r['p0_eligible']=='no-live-arm' for r in rows)} | unmatched: {sum(r['p0_eligible']=='unmatched' for r in rows)}")
print(f"eligible & no flags: {len(clean)} | flagged eligible: {len(elig)-len(clean)}")
from collections import Counter
print("eligible by field:", dict(Counter(r["field"] for r in elig).most_common()))
print("flags among eligible:", dict(Counter(f for r in elig for f in r["flags"].split("|") if f)))
print("\nunmatched titles:")
for r in rows:
    if r["p0_eligible"] == "unmatched":
        print("  -", r["title"][:80])
