"""Card scaffolding for the P0 pool: clone candidate repos, audit them, fetch paper text.

For each paper in data/p0_pool.csv:
  - candidate own-repos = GitHub links found in the paper minus a third-party blocklist
  - shallow, blob-limited clone into external/repos/<Wid>/<owner>__<repo>
  - audit: file counts, prompt/data/eval indicators, license, requirements, model IDs in code
  - fetch OA full text (pypdf) into external/papers/<Wid>.txt
Writes harness/scaffold/<Wid>.json (committed) — repos and PDFs stay in external/ (ignored).
"""
import csv, io, json, re, subprocess, time, urllib.request
from collections import Counter
from pathlib import Path
from pypdf import PdfReader

HALF = Path(__file__).resolve().parents[1]
DATA, EXT, OUT = HALF / "data", HALF / "external", HALF / "harness" / "scaffold"
BLOCK = re.compile(r"github\.com/(openai|huggingface|facebookresearch|EleutherAI|langchain-ai|tatsu-lab|lm-sys|"
                   r"meta-llama|google|google-research|microsoft|vllm-project|hiyouga|karpathy|deepseek-ai|"
                   r"nlpxucan|allenai|princeton-nlp|conversationai|qdrant|tylin|ggerganov|paul-gauthier|rjust|"
                   r"protagolabs|InternLM|centerforaisafety|anthropics|voidism|EdinburghNLP|mandarjoshi90|"
                   r"nelson-liu|yaolu|muguruzawang|open-compass|FasterDecoding|jondurbin|TsinghuaC3I/UltraMedical)", re.I)
MODEL_RE = re.compile(r"gpt-4o?-?(?:turbo|mini)?(?:-\d{4}-\d{2}-\d{2})?|o[134](?:-mini|-pro)?(?:-\d{4}-\d{2}-\d{2})?|gpt-5[\w.-]*|claude-[\w.-]+|gemini-[\w.-]+|gpt-3\.5[\w.-]*", re.I)
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-card-scaffold/0.1; academic research)"}


def run(cmd, timeout=180):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).returncode == 0
    except Exception:
        return False


def audit_repo(path):
    files = [p for p in path.rglob("*") if p.is_file() and ".git" not in p.parts]
    ext = Counter(p.suffix.lower() for p in files)
    text_like = [p for p in files if p.suffix.lower() in (".py", ".ipynb", ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".toml", ".cfg") and p.stat().st_size < 2_000_000]
    prompt_hits, eval_hits, model_ids = 0, 0, Counter()
    for p in text_like[:400]:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        prompt_hits += len(re.findall(r"prompt", t, re.I)) > 0
        eval_hits += bool(re.search(r"accuracy|f1|pass@|evaluat|metric|score", t, re.I))
        for m in MODEL_RE.findall(t):
            model_ids[m.lower()] += 1
    names = [p.name.lower() for p in files]
    return {
        "n_files": len(files), "ext_top": dict(ext.most_common(8)),
        "has_license": any(n.startswith("license") for n in names),
        "has_requirements": any(n in ("requirements.txt", "environment.yml", "pyproject.toml", "setup.py", "pipfile") for n in names),
        "has_readme": any(n.startswith("readme") for n in names),
        "n_notebooks": ext.get(".ipynb", 0), "n_py": ext.get(".py", 0),
        "n_data_files": sum(ext.get(e, 0) for e in (".jsonl", ".csv", ".json", ".parquet", ".tsv", ".xlsx")),
        "files_mentioning_prompt": prompt_hits, "files_with_eval_terms": eval_hits,
        "model_ids_in_code": dict(model_ids.most_common(10)),
        "readme_head": next((p.read_text(encoding="utf-8", errors="ignore")[:1500] for p in files if p.name.lower().startswith("readme")), ""),
    }


def fetch_pdf_text(url):
    if "arxiv.org/abs/" in url:
        url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read(30 * 1024 * 1024)
        ct = (r.headers.get("Content-Type") or "").lower()
    if "pdf" in ct or data[:4] == b"%PDF":
        rd = PdfReader(io.BytesIO(data))
        return "\n".join((pg.extract_text() or "") for pg in rd.pages[:45]), "pdf"
    return data.decode("utf-8", "replace"), "html"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pool = list(csv.DictReader(open(DATA / "p0_pool.csv", encoding="utf-8-sig")))
    scan = {}
    for r in csv.DictReader(open(DATA / "artifact_scan.csv", encoding="utf-8-sig")):
        if r["scan_status"] in ("pdf", "html") and int(r["n_links"] or 0) > int(scan.get(r["openalex_id"], {}).get("n_links", 0) or 0):
            scan[r["openalex_id"]] = r
    census = {r["openalex_id"]: r for r in csv.DictReader(open(DATA / "census_v2.csv", encoding="utf-8-sig"))}

    for i, p in enumerate(pool, 1):
        oid = p["openalex_id"]; wid = oid.rsplit("/", 1)[-1]
        out_path = OUT / f"{wid}.json"
        if out_path.exists():
            print(f"[{i}/{len(pool)}] {wid} skip (done)", flush=True); continue
        links = (scan.get(oid, {}).get("links") or "").split("|")
        gh = sorted({re.sub(r"\.git$", "", l.split("#")[0]) for l in links if l.lower().startswith("github.com/") and not BLOCK.search(l)})
        gh = [g for g in gh if len(g.split("/")) >= 3][:3]
        repos = []
        for g in gh:
            owner, repo = g.split("/")[1], re.sub(r"[^\w.\-]", "", g.split("/")[2])
            dest = EXT / "repos" / wid / f"{owner}__{repo}"
            ok = dest.exists() or run(["git", "clone", "--depth", "1", "--filter=blob:limit=2m", "-q", f"https://github.com/{owner}/{repo}", str(dest)])
            entry = {"url": f"https://github.com/{owner}/{repo}", "cloned": ok}
            if ok:
                entry["audit"] = audit_repo(dest)
                try:
                    entry["commit"] = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
                except Exception:
                    pass
            repos.append(entry)
        c = census.get(oid, {})
        paper_txt = EXT / "papers" / f"{wid}.txt"
        text_status = "cached" if paper_txt.exists() else "none"
        if not paper_txt.exists() and c.get("oa_url"):
            try:
                text, kind = fetch_pdf_text(c["oa_url"])
                paper_txt.write_text(text, encoding="utf-8"); text_status = kind
            except Exception as e:
                text_status = f"error:{type(e).__name__}"
            time.sleep(3)
        scaffold = {"openalex_id": oid, "title": p["title"], "doi": c.get("doi", ""), "field": p["field"], "year": p["year"],
                    "live_models": p["live_models"], "dead_models": p["dead_models"], "flags": p["flags"],
                    "all_links": links, "candidate_repos": repos, "paper_text": str(paper_txt) if text_status not in ("none",) else None,
                    "paper_text_status": text_status}
        out_path.write_text(json.dumps(scaffold, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{i}/{len(pool)}] {wid} repos={sum(r['cloned'] for r in repos)}/{len(repos)} text={text_status}", flush=True)


if __name__ == "__main__":
    main()
