"""Pre-extract evidence for the manual dependence coding (ANALYSIS_PLAN §5).

For every paper in data/coding/sample_v1.csv: fetch the OA full text (PDF via pypdf, HTML
fallback), locate each census-matched model ID, and record short snippets around the
mentions, whether they sit in the body or in the reference list, access-route hints
(API / web interface / Azure / OpenRouter ...), dates near the mentions, other versioned IDs
present, and repository links. Coders still open the paper; this only saves them the search.

Resumable: appends to data/coding/evidence_v1.jsonl and skips ids already present.
Polite: 2 s between arXiv fetches, 1 s otherwise. PDFs parsed in memory, never saved.
Snippets are short excerpts for internal coding use, not for redistribution.

Usage: python scripts/coding_evidence.py [--set pilot|main|reserve|all] [--limit N]
"""
import argparse, csv, io, json, re, time, urllib.parse, urllib.request
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "coding" / "sample_v1.csv"
OUT = ROOT / "data" / "coding" / "evidence_v1.jsonl"
LOG = ROOT / "data" / "coding" / "evidence.log"
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-coding-evidence/0.1; academic research)"}
MAX_PAGES, WIN, MAX_BODY, MAX_REFS = 60, 230, 3, 1

VOCAB = [m["id"] for m in json.load(open(ROOT / "target_models.json", encoding="utf-8"))["models"]]

REPO_PAT = re.compile(r"(github\.com/[\w.\-]+/[\w.\-]+|osf\.io/[a-z0-9]{4,6}"
                      r"|zenodo\.org/(?:records?|record)/\d+"
                      r"|huggingface\.co/(?:datasets/)?[\w.\-]+/[\w.\-]+)", re.I)
REFS_PAT = re.compile(r"\n\s*(?:\d+\.?\s*)?(references|bibliography|reference list|works cited)\s*\n", re.I)
HINTS = {
    "api": r"\bAPIs?\b|chat\.?completions?|ChatCompletion|openai\.com/v1|api key|api calls?",
    "webui": r"web interface|chat interface|ChatGPT interface|chat\.openai\.com|ChatGPT (?:Plus|app|website|web)"
             r"|conversational interface|user interface of ChatGPT|via the ChatGPT|through ChatGPT",
    "azure": r"Azure ?OpenAI|Azure (?:AI|cloud)",
    "openrouter": r"OpenRouter",
    "bedrock_vertex": r"Amazon Bedrock|Vertex ?AI|Google AI Studio",
    "temperature": r"temperature\s*(?:=|of|was|set to)?\s*[0-9.]+",
    "batch_or_playground": r"Batch API|Playground",
}
HINT_RE = {k: re.compile(v, re.I) for k, v in HINTS.items()}
MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December"
          "|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec")
DATE_RE = re.compile(r"(?:(?:" + MONTHS + r")\.?\s+\d{1,2},?\s+20\d\d|(?:" + MONTHS + r")\.?\s+20\d\d"
                     r"|20\d\d-\d\d(?:-\d\d)?|\d{1,2}\s+(?:" + MONTHS + r")\.?\s+20\d\d)")
KEYWORDS = re.compile(r"\bwe (?:use|used|employ|employed|query|queried|call|called|prompt|prompted|access|accessed"
                      r"|ran|run|evaluate|evaluated|test|tested|fine-tun)"
                      r"|\busing\b|\bvia\b|\bversion\b|\bsnapshot\b|\bAPI\b|\baccessed\b|\btemperature\b|\bprompt", re.I)
PRODUCT_RE = re.compile(r"\bChatGPT\b|\bGPT-?4o?\b|\bGemini\b|\bClaude\b", re.I)


def id_pattern(mid):
    toks = re.split(r"[-_.]", mid)
    return re.compile(r"(?<![a-z0-9])" + r"[\s\-_.]*".join(re.escape(t) for t in toks) + r"(?![a-z0-9])", re.I)


ID_RE = {m: id_pattern(m) for m in VOCAB}


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ct = (r.headers.get("Content-Type") or "").lower()
        return ct, r.read(30 * 1024 * 1024)


def pdf_text(data):
    rd = PdfReader(io.BytesIO(data))
    pages = [(p.extract_text() or "") for p in rd.pages[:MAX_PAGES]]
    return "\n".join(pages), len(rd.pages)


def html_text(data):
    t = data.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style|nav|header|footer).*?</\1>", " ", t)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&nbsp;|&#160;", " ", t)
    t = re.sub(r"&amp;", "&", t)
    return t


def normalize(text):
    text = text.replace("\r", "")
    text = re.sub(r"-\n(?=\w)", "-", text)          # hyphen at line end: gpt-4-\n0613
    text = re.sub(r"[ \t]+", " ", text)
    return text


def refs_start(text):
    last = None
    for m in REFS_PAT.finditer(text):
        if m.start() > len(text) * 0.4:
            last = m.start()
    return last


def snippet(text, a, b):
    lo, hi = max(0, a - WIN), min(len(text), b + WIN)
    s = text[lo:hi].replace("\n", " ")
    return ("..." if lo > 0 else "") + s.strip() + ("..." if hi < len(text) else "")


def analyse(text, matched):
    text = normalize(text)
    rs = refs_start(text)
    body = text if rs is None else text[:rs]
    out = {"refs_start_frac": None if rs is None else round(rs / max(1, len(text)), 3), "ids": {}}
    for mid in matched:
        pat = ID_RE.get(mid) or id_pattern(mid)
        hits = [(m.start(), m.end()) for m in pat.finditer(text)]
        body_hits = [h for h in hits if rs is None or h[0] < rs]
        ref_hits = [h for h in hits if rs is not None and h[0] >= rs]

        def score(h):
            ctx = text[max(0, h[0] - WIN):h[1] + WIN]
            return len(KEYWORDS.findall(ctx)) + (2 if DATE_RE.search(ctx) else 0)

        chosen, taken = [], []
        for h in sorted(body_hits, key=lambda h: -score(h)):
            if any(abs(h[0] - t) < WIN for t in taken):
                continue
            chosen.append(h)
            taken.append(h[0])
            if len(chosen) >= MAX_BODY:
                break
        chosen.sort()
        snips = [{"where": "body", "pos": round(h[0] / max(1, len(text)), 3), "text": snippet(text, *h)}
                 for h in chosen]
        for h in ref_hits[:MAX_REFS]:
            snips.append({"where": "refs", "pos": round(h[0] / max(1, len(text)), 3), "text": snippet(text, *h)})
        out["ids"][mid] = {"n_body": len(body_hits), "n_refs": len(ref_hits), "snippets": snips}
    out["other_ids_in_text"] = sorted(m for m in VOCAB if m not in matched and ID_RE[m].search(body))
    out["hints"] = {k: len(r.findall(body)) for k, r in HINT_RE.items()}
    near_dates = []
    for mid, d in out["ids"].items():
        for s in d["snippets"]:
            if s["where"] == "body":
                near_dates += DATE_RE.findall(s["text"])
    out["dates_near_mentions"] = sorted(set(near_dates))[:8]
    joined = body.replace("\n", "") + "\n" + body
    out["repo_links"] = sorted({m.group(0).rstrip(".,)]") for m in REPO_PAT.finditer(joined)})[:8]
    out["product_mentions"] = len(PRODUCT_RE.findall(body))
    return out


ARXIV_API = "http://export.arxiv.org/api/query?search_query=ti:%22{q}%22&max_results=3"


def norm_tokens(t):
    return set(re.sub(r"[^a-z0-9 ]", " ", t.lower()).split())


def arxiv_lookup(title):
    """Find an arXiv version by exact-ish title (token Jaccard >= 0.85). Returns (pdf_url, title) or None."""
    import xml.etree.ElementTree as ET
    q = urllib.parse.quote(re.sub(r"[^\w\s]", " ", title)[:200])
    _, data = fetch(ARXIV_API.format(q=q), timeout=60)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    want = norm_tokens(title)
    for e in ET.fromstring(data).findall("a:entry", ns):
        t = " ".join((e.findtext("a:title", default="", namespaces=ns)).split())
        got = norm_tokens(t)
        if len(want & got) / max(1, len(want | got)) >= 0.85:
            aid = e.findtext("a:id", default="", namespaces=ns)
            aid = re.sub(r"v\d+$", "", aid.strip())          # versioned PDF URLs 404 for some ids
            return aid.replace("/abs/", "/pdf/").replace("http://", "https://"), t
    return None


def arxiv_fallback(rows):
    """For records whose fetch failed, try the arXiv version found by title; rewrite the file."""
    recs = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    by_id = {r["openalex_id"]: r for r in rows}
    n_try = n_ok = 0
    for rec in recs:
        if not (rec["fetch"].startswith("error") or rec["fetch"] in ("none", "pdf_unparsed")):
            continue
        r = by_id.get(rec["openalex_id"])
        if not r:
            continue
        n_try += 1
        try:
            hit = arxiv_lookup(r["title"])
            time.sleep(3.0)
            if not hit:
                rec["arxiv_fallback"] = "no match"
                print(f"  no arXiv match: {r['title'][:70]}", flush=True)
                continue
            url, t = hit
            ct, data = fetch(url)
            text, n = pdf_text(data)
            if not text.strip():
                rec["arxiv_fallback"] = "pdf unparsed"
                continue
            rec.update({"fetch": "pdf_arxiv_fallback", "url": url, "n_pages": n, "text_chars": len(text),
                        "arxiv_fallback": t})
            rec.pop("error", None)
            rec.update(analyse(text, r["matched_models"].split("|")))
            n_ok += 1
            print(f"  recovered via arXiv: {r['title'][:70]}", flush=True)
            time.sleep(2.0)
        except Exception as e:
            rec["arxiv_fallback"] = f"error:{type(e).__name__}"
            print(f"  fallback error {type(e).__name__}: {r['title'][:60]}", flush=True)
    OUT.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in recs), encoding="utf-8")
    print(f"arxiv fallback: tried {n_try}, recovered {n_ok}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="all")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--retry-errors", action="store_true",
                    help="re-fetch papers whose record is an error; the old record is dropped")
    ap.add_argument("--arxiv-fallback", action="store_true",
                    help="for failed fetches, look up an arXiv version by title and extract from it")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(SAMPLE, encoding="utf-8-sig")))
    order = {"pilot": 0, "main": 1, "reserve": 2}
    rows.sort(key=lambda r: order[r["set"]])
    if a.set != "all":
        rows = [r for r in rows if r["set"] == a.set]
    if a.arxiv_fallback:
        arxiv_fallback(rows)
        return
    done = set()
    if OUT.exists():
        recs = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
        if a.retry_errors:
            keep = [r for r in recs if not r["fetch"].startswith("error")]
            OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep), encoding="utf-8")
            recs = keep
        done = {r["openalex_id"] for r in recs}
    todo = [r for r in rows if r["openalex_id"] not in done]
    if a.limit:
        todo = todo[:a.limit]
    log = open(LOG, "a", encoding="utf-8")
    with open(OUT, "a", encoding="utf-8") as f:
        for i, r in enumerate(todo, 1):
            matched = r["matched_models"].split("|")
            rec = {"openalex_id": r["openalex_id"], "set": r["set"], "fetch": "none", "url": r["oa_url"]}
            url = r["oa_url"].strip()
            t0 = time.time()
            if url:
                if "arxiv.org/abs/" in url:
                    url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
                url = urllib.parse.quote(url, safe=":/?&=%#+@")
                try:
                    ct, data = fetch(url)
                    if "pdf" in ct or data[:5] == b"%PDF-":
                        text, n = pdf_text(data)
                        rec["fetch"], rec["n_pages"] = ("pdf" if text.strip() else "pdf_unparsed"), n
                    else:
                        text = html_text(data)
                        rec["fetch"] = "html"
                    rec["text_chars"] = len(text)
                    rec.update(analyse(text, matched))
                except Exception as e:
                    rec["fetch"] = f"error:{type(e).__name__}"
                    rec["error"] = str(e)[:200]
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            found = sum(1 for d in rec.get("ids", {}).values() if d["n_body"] or d["n_refs"])
            wid = r["openalex_id"].rsplit("/", 1)[-1]
            msg = (f"[{i}/{len(todo)}] {r['set']} {wid} {rec['fetch']} "
                   f"ids_found={found}/{len(matched)} {time.time() - t0:.1f}s")
            print(msg, flush=True)
            log.write(msg + "\n")
            log.flush()
            time.sleep(2.0 if "arxiv.org" in url else 1.0)
    print("done", flush=True)


if __name__ == "__main__":
    main()
