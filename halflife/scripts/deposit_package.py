"""Build the Zenodo deposit bundle under halflife/deposit/. Nothing is uploaded; no API calls.

Inputs
  data/deposit_manifest.csv            every archive file with size, record count, SHA-256 and licence text
  data/deposit_licence_decisions.csv   per paper: include / include-nc / redact (written by deposit_preflight.py, edited by hand)
  the git tree at HEAD                 code, configs, cards, data tables, documents (tracked files only)

Outputs (deposit/)
  HALF-LIFE_code_and_data_<rev>.zip    the public release tree at <ref> (same selection as github.com/Erzyh/HALF-LIFE, built by
                                       release/build_public_release.py; Korean planning notes, raw harvests and call archives left out)
  HALF-LIFE_raw_harvests.zip           raw OpenAlex harvests behind the census (census_raw, census_ext_raw, census_add_raw_2026-10-11)
  HALF-LIFE_archive_<kind>.zip         request-response archives per stage: tierA, tierb, tierb_p3_<arm>, tierb_variant, ...
                                       (--max-zip-mb N [--split-kinds a,b] cuts a stage into HALF-LIFE_archive_<kind>_partNN.zip
                                       pieces of about N MB, whole papers kept together, for uploads over a lossy route)

Usage: python scripts/deposit_package.py [ref]   (ref = a tag such as v1.0.0, default HEAD; the version field takes the tag name)
  MANIFEST.csv                         every packaged file: zip, kind, paper, path, bytes, SHA-256 (of the packaged content),
                                       records, licence text, class decision, redaction
  LICENCE_DECISIONS.csv                copy of the decisions used
  README.md, LICENSE-data.txt, LICENSE-code.txt, zenodo_metadata.json

Redaction (decision 'redact'): in the JSONL files of that paper the text of every message (request and reply),
every item text and label field, and every logprob is replaced by {"sha256", "chars"}; identifiers, parameters,
usage, fingerprints, latencies, HTTP status and the request/response hashes recorded at call time are kept.
JSON summaries (result.json, run_meta.json, budget.json, prepare.json) are copied unchanged.
"""
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
ROOT = HALF.parent
DEP = HALF / "deposit"
MANIFEST = HALF / "data" / "deposit_manifest.csv"
DECISIONS = HALF / "data" / "deposit_licence_decisions.csv"

ITEM_KEYS = {"text", "question", "prompt", "input", "output", "options", "gold", "answer", "label", "context", "passage",
             "content", "reference", "target", "source_text", "completion", "response_text", "raw"}
AUTHORS = [("Gil, Hyeonwoo", "Hongik University"), ("Ahn, Sangsu", "Tongmyong University"), ("Hwang, Janghyuck", "Hongik University"),
           ("Kim, Junggi", "Hongik University"), ("Kim, Junmyeong", "Hongik University"), ("Kang, Shinjin", "Hongik University")]
TITLE = "HALF-LIFE: request-response archives, code and data"   # the title of the Zenodo record, as the user set it in the web form
REPO = "https://github.com/Erzyh/HALF-LIFE"   # the public release repository (to be created at submission, private until acceptance);
                                                # the working repository was renamed Erzyh/HALF-LIFE-DEV on 2026-09-28 and stays private


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def red(s):
    return {"sha256": hashlib.sha256(s.encode("utf-8")).hexdigest(), "chars": len(s)}


def redact_messages(msgs):
    out = []
    for m in msgs:
        if isinstance(m, dict):
            mm = dict(m)
            c = m.get("content")
            if isinstance(c, str):
                mm["content"] = red(c)
            elif isinstance(c, list):
                mm["content"] = [red(json.dumps(p, ensure_ascii=False, sort_keys=True)) for p in c]
            out.append(mm)
        else:
            out.append(red(str(m)))
    return out


def redact(o):
    if isinstance(o, dict):
        r = {}
        for k, v in o.items():
            if k == "messages" and isinstance(v, list):
                r[k] = redact_messages(v)
            elif k == "choices" and isinstance(v, list):
                cs = []
                for c in v:
                    if isinstance(c, dict):
                        c = dict(c)
                        c.pop("logprobs", None)
                        msg = c.get("message")
                        if isinstance(msg, dict):
                            msg = dict(msg)
                            if isinstance(msg.get("content"), str):
                                msg["content"] = red(msg["content"])
                            if isinstance(msg.get("reasoning_content"), str):
                                msg["reasoning_content"] = red(msg["reasoning_content"])
                            c["message"] = msg
                        if isinstance(c.get("text"), str):
                            c["text"] = red(c["text"])
                    cs.append(c)
                r[k] = cs
            elif k == "logprobs":
                r[k] = None
            elif k in ITEM_KEYS and isinstance(v, str):
                r[k] = red(v)
            elif k in ITEM_KEYS and isinstance(v, (list, dict)):
                r[k] = red(json.dumps(v, ensure_ascii=False, sort_keys=True))
            else:
                r[k] = redact(v)
        return r
    if isinstance(o, list):
        return [redact(x) for x in o]
    return o


def redact_jsonl(src, dst, note):
    n = 0
    with open(src, "r", encoding="utf-8", errors="replace") as f, open(dst, "w", encoding="utf-8") as g:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                row = {"unparsable_line": red(line)}
            if isinstance(row, dict):
                row = redact(row)
                row["_redaction"] = note
            else:
                row = {"row": redact(row), "_redaction": note}
            g.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def parts_of(kind, rows, max_zip, split_kinds):
    """One zip per kind, or, with --max-zip-mb, several parts of about that size (whole papers kept together) for the kinds
    named in --split-kinds (all kinds when the option is absent). Parts are independent zips, each a subset of the papers."""
    if not max_zip or (split_kinds is not None and kind not in split_kinds):
        return [(f"HALF-LIFE_archive_{kind}.zip", rows)]
    groups = {}
    for r in rows:
        groups.setdefault(r["wid"], []).append(r)
    parts, est = [[]], [0.0]
    for rs in groups.values():
        raw = sum(int(r.get("bytes") or 0) for r in rs) * 0.22        # the archives compress to about a fifth
        if parts[-1] and est[-1] + raw > max_zip:
            parts.append([])
            est.append(0.0)
        parts[-1].extend(rs)
        est[-1] += raw
    if len(parts) == 1:
        return [(f"HALF-LIFE_archive_{kind}.zip", rows)]
    return [(f"HALF-LIFE_archive_{kind}_part{i:02d}.zip", part) for i, part in enumerate(parts, 1)]


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()


def main():
    DEP.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="deposit_", dir=str(DEP)))
    rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8-sig")))
    if not DECISIONS.exists():
        sys.exit("run scripts/deposit_preflight.py first (it writes data/deposit_licence_decisions.csv)")
    dec = {r["wid"]: r for r in csv.DictReader(open(DECISIONS, encoding="utf-8-sig"))}
    ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"           # a tag such as v1.0.0, or HEAD
    rev = git("rev-parse", "--short", f"{ref}^{{commit}}")       # an annotated tag resolves to its commit
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    exact = subprocess.run(["git", "-C", str(ROOT), "describe", "--tags", "--exact-match", ref], capture_output=True, text=True)
    tag = exact.stdout.strip() if exact.returncode == 0 else git("describe", "--tags", "--always", ref)
    by_kind = defaultdict(list)
    for r in rows:
        by_kind[r["kind"]].append(r)

    # 1. code and data: the public release tree, built with the same selection as github.com/Erzyh/HALF-LIFE
    #    (release/build_public_release.py drops the Korean planning notes, the raw harvests and the call archives, adds the
    #    README, CITATION.cff, licences, workflow and MANIFEST.csv, and refuses to build if a secret is found)
    code_zip = DEP / f"HALF-LIFE_code_and_data_{rev}.zip"
    tree = ROOT / "dist" / "deposit_code_tree"
    subprocess.run([sys.executable, str(ROOT / "release" / "build_public_release.py"), "--ref", ref, "--out", "dist/deposit_code_tree", "--tag", tag],
                   check=True, cwd=str(ROOT), stdout=subprocess.DEVNULL)
    code_files = sorted(p for p in tree.rglob("*") if p.is_file())
    with zipfile.ZipFile(code_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for p in code_files:
            zf.write(p, arcname=f"HALF-LIFE-{rev}/{p.relative_to(tree).as_posix()}")
    print(f"code archive {code_zip.name}: {len(code_files)} files, {code_zip.stat().st_size / 1e6:.1f} MB (public release tree at {tag} = {rev}"
          f"{', working tree has uncommitted changes' if dirty else ''})")

    # 1b. raw OpenAlex harvests behind the census (census_ext_raw.jsonl is ignored by git; none of them is in the public tree)
    harvest_zip = DEP / "HALF-LIFE_raw_harvests.zip"
    harvest_rows = []
    with zipfile.ZipFile(harvest_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for name in ("census_raw.jsonl", "census_ext_raw.jsonl", "census_add_raw_2026-10-11.jsonl", "census_add_raw_2026-10-12.jsonl"):
            src = HALF / "data" / name
            if not src.exists():
                print("  harvest missing, skipped:", name)
                continue
            zf.write(src, arcname=f"data/{name}")
            with open(src, "rb") as fh:
                n_rec = sum(1 for _ in fh)
            harvest_rows.append({"zip": harvest_zip.name, "kind": "harvest", "wid": "", "path": f"data/{name}", "bytes": src.stat().st_size,
                                 "sha256": sha256_of(src), "records": n_rec, "data_licence": "OpenAlex metadata (CC0)", "licence_class": "open",
                                 "decision": "include", "redaction": ""})
    harvest_bytes = sum(r["bytes"] for r in harvest_rows)
    print(f"raw harvests {harvest_zip.name}: {len(harvest_rows)} files, {harvest_bytes / 1e6:.0f} MB raw -> {harvest_zip.stat().st_size / 1e6:.0f} MB zip")

    # 2. archives per stage
    manifest_out = []
    summary = []
    max_zip = float(sys.argv[sys.argv.index("--max-zip-mb") + 1]) * 1e6 if "--max-zip-mb" in sys.argv else None
    split_kinds = set(sys.argv[sys.argv.index("--split-kinds") + 1].split(",")) if "--split-kinds" in sys.argv else None
    for kind in sorted(by_kind):
      for zname, part_rows in parts_of(kind, by_kind[kind], max_zip, split_kinds):
        zpath = DEP / zname
        n_files = n_red = 0
        raw_bytes = 0
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
            for r in part_rows:
                src = HALF / r["path"]
                if not src.exists():
                    print("  missing, skipped:", r["path"])
                    continue
                d = dec.get(r["wid"], {})
                decision = d.get("decision", "redact")
                redaction = r.get("redaction") or ""
                if decision == "redact" and src.suffix == ".jsonl":
                    note = f"item and message text replaced by sha256 and length (licence: {(d.get('licence_text') or 'unknown')[:80]})"
                    dst = tmp / (r["path"].replace("/", "__"))
                    records = redact_jsonl(src, dst, note)
                    zf.write(dst, arcname=r["path"])
                    digest = sha256_of(dst)
                    size = dst.stat().st_size
                    dst.unlink()
                    redaction = (redaction + "; " if redaction else "") + "text redacted in the deposit"
                    n_red += 1
                else:
                    zf.write(src, arcname=r["path"])
                    digest = sha256_of(src)
                    size = src.stat().st_size
                    records = r.get("records") or ""
                raw_bytes += size
                n_files += 1
                manifest_out.append({"zip": zpath.name, "kind": kind, "wid": r["wid"], "path": r["path"], "bytes": size, "sha256": digest,
                                     "records": records, "data_licence": r.get("data_licence") or "", "licence_class": d.get("auto_class", ""),
                                     "decision": decision, "redaction": redaction})
        summary.append((zpath.name, n_files, n_red, raw_bytes, zpath.stat().st_size))
        print(f"  {zpath.name}: {n_files} files ({n_red} redacted), {raw_bytes / 1e6:.0f} MB raw -> {zpath.stat().st_size / 1e6:.0f} MB zip", flush=True)
    shutil.rmtree(tmp, ignore_errors=True)

    n_archive = len(manifest_out)
    with open(DEP / "MANIFEST.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest_out[0].keys()))
        w.writeheader()
        w.writerows(manifest_out + harvest_rows)
    shutil.copy2(DECISIONS, DEP / "LICENCE_DECISIONS.csv")

    # 3. licences, metadata, README
    (DEP / "LICENSE-data.txt").write_text(
        "The HALF-LIFE request-response archives, manifests, summaries and data tables are released under the Creative Commons\n"
        "Attribution 4.0 International licence (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/).\n\n"
        "Exception: benchmark items copied into items.jsonl and into request bodies keep the licence of their source dataset,\n"
        "recorded per paper in LICENCE_DECISIONS.csv and per file in MANIFEST.csv. Where that licence is non-commercial\n"
        "(CC BY-NC and similar) the text is included under that licence for research use; where it is unknown or restricted the\n"
        "text was replaced by SHA-256 hashes before deposit (column 'redaction').\n", encoding="utf-8")
    (DEP / "LICENSE-code.txt").write_text(
        f"MIT License\n\nCopyright (c) {date.today().year} the HALF-LIFE authors\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation\n"
        "files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy,\n"
        "modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the\n"
        "Software is furnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice\n"
        "shall be included in all copies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY\n"
        "OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR\n"
        "PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR\n"
        "THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n", encoding="utf-8")
    n_papers = len({r["wid"] for r in rows if r["wid"].startswith("W")})
    total_raw = sum(s[3] for s in summary)
    total_zip = sum(s[4] for s in summary) + code_zip.stat().st_size + harvest_zip.stat().st_size
    desc = (f"<p>Request-response archives, code and data behind the manuscript <em>The half-life of science that depends on commercial "
            f"language models</em>. The archives hold every API call of the pre-retirement re-executions of {n_papers} papers, the four "
            f"successor conditions and the same-snapshot control ({n_archive:,} files, {total_raw / 1e9:.2f} GB uncompressed), each with "
            f"its SHA-256 recorded at call time, the served model and the system fingerprint. Items whose source licence is unknown or "
            f"restricted are deposited as hashes (see MANIFEST.csv and LICENCE_DECISIONS.csv). Code and data tables are the public release "
            f"tree at {tag} (revision {rev}), identical to the repository {REPO}; the raw OpenAlex harvests behind the census are in "
            f"HALF-LIFE_raw_harvests.zip.</p>")
    meta = {"metadata": {
        "title": TITLE, "upload_type": "dataset", "description": desc,
        "creators": [{"name": n, "affiliation": a} for n, a in AUTHORS],
        "access_right": "restricted",
        "access_conditions": "Available to the editors and reviewers of the manuscript on request; the record is opened on publication.",
        "license": "cc-by-4.0",
        "keywords": ["reproducibility", "large language models", "model deprecation", "survival analysis", "research infrastructure", "re-execution"],
        "related_identifiers": [{"identifier": REPO, "relation": "isSupplementTo", "resource_type": "software"}],
        "version": tag, "language": "eng", "prereserve_doi": True,
        "notes": "Deposited before peer review as a restricted record with a reserved DOI; files are replaced only through new versions.",
    }}
    json.dump(meta, open(DEP / "zenodo_metadata.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    L = [f"# HALF-LIFE deposit bundle ({date.today().isoformat()}, revision {rev})", "",
         "Archives, code and data behind *The half-life of science that depends on commercial language models*.", "",
         "## Contents", "", "| file | files inside | redacted | uncompressed | zip |", "|---|---|---|---|---|",
         f"| {code_zip.name} | public release tree at {tag} ({rev}), {len(code_files)} files, identical to {REPO} | 0 | | {code_zip.stat().st_size / 1e6:.0f} MB |",
         f"| {harvest_zip.name} | raw OpenAlex harvests behind the census: {', '.join(r['path'].split('/')[-1] for r in harvest_rows)} | 0 | {harvest_bytes / 1e6:.0f} MB | {harvest_zip.stat().st_size / 1e6:.0f} MB |"]
    for name, nf, nr, raw, z in summary:
        L.append(f"| {name} | {nf} | {nr} | {raw / 1e6:.0f} MB | {z / 1e6:.0f} MB |")
    L += ["", f"Total: {n_archive:,} archive files, {total_raw / 1e9:.2f} GB uncompressed; {total_zip / 1e9:.2f} GB zipped including the code tree and the harvests.", "",
          "## Layout inside the archives", "",
          "`runs/<Wid>/` Tier A (repository-based) runs; `runs/tierb/<Wid>/` prompt-level baselines; `runs/tierb/<Wid>v2/` prompt variants;",
          "`runs/tierb_p3/<arm>/<Wid>/` successor conditions (vendor = designated replacement, gpt41, open70b = Llama 3.3 70B via Together,",
          "gemini_flash = Gemini 3.8 Flash, drift_ctrl = same-snapshot control, <arm>_rep = seed-variance repeat of that condition on 20 papers with the same request bodies and two fresh calls per item, open70b_bf16 = the open-weight condition on a dedicated bfloat16 deployment of the same model for 12 papers). Per run: items.jsonl (the item list), requests.jsonl (request bodies),",
          "calls.jsonl (one record per API call: request, full response, served model, system fingerprint, latency, cost, SHA-256 of request and",
          "response), result.json / run_meta.json / budget.json / prepare.json (summaries). Configurations, claim cards, codebooks, data tables and",
          "analysis scripts are in the code archive.", "",
          "## Verifying", "",
          "`MANIFEST.csv` lists every packaged file with its SHA-256 as packaged. After unzipping, compare with",
          "`python -c \"import csv,hashlib,sys; [print(r['path'], hashlib.sha256(open(r['path'],'rb').read()).hexdigest()==r['sha256']) for r in csv.DictReader(open('MANIFEST.csv',encoding='utf-8'))]\"`.",
          "Each call record also carries `sha_request` / `sha_response` computed at call time; redacted records keep them, so a redacted reply",
          "can still be matched against a re-issued call.", "",
          "## Licences", "",
          "Archives, manifests and data tables: CC BY 4.0 (LICENSE-data.txt). Code: MIT (LICENSE-code.txt). Benchmark items keep the licence of",
          "their source; `LICENCE_DECISIONS.csv` records the class and the decision per paper and `MANIFEST.csv` the redaction per file.", "",
          "## Citation", "", "Cite the paper and this record: https://doi.org/10.5281/zenodo.22995877 (DOI reserved on 27 September 2026; the record stays restricted until publication).", ""]
    (DEP / "README.md").write_text("\n".join(L), encoding="utf-8")
    print(f"bundle: {n_archive:,} archive files, {total_raw / 1e9:.2f} GB raw; {total_zip / 1e9:.2f} GB zipped with code tree and harvests -> {DEP}")


if __name__ == "__main__":
    main()
