"""Deposit manifest for the L1 archive: every request/response log and result file with its SHA-256, size and record
count, plus a per-run note on what was redacted and under which data licence the items were used.

Covers runs/<Wid>/ (Tier A), runs/tierb/<Wid>/ (Tier B baselines and their archived earlier versions), runs/tierb/<Wid>v2/
(prompt variants) and runs/tierb_p3/<arm>/<Wid>/ (successor arms). Writes data/deposit_manifest.csv and prints a
summary; the licence column comes from the Tier B config (items.license) or the Tier A card (artifacts.data_license).
Redactions are read from run_meta.json / result.json notes (question text redacted for MedXpertQA; TURTLEAI images not
archived). No API calls; hashing a few GB takes a few minutes.
"""
import csv, hashlib, json, os, re
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
FILES = ("calls.jsonl", "requests.jsonl", "items.jsonl", "result.json", "run_meta.json", "budget.json", "prepare.json",
         "environment_check.json", "executions.jsonl")


def sha_and_lines(p):
    h = hashlib.sha256(); n = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk); n += chunk.count(b"\n")
    return h.hexdigest(), n


def licence_for(wid, kind):
    if kind.startswith("tierb"):
        p = HALF / "harness" / "tierb" / "configs" / f"{wid}.json"
        if p.exists():
            c = json.load(open(p, encoding="utf-8"))
            return (c.get("items") or {}).get("license") or ""
    p = HALF / "harness" / "cards" / f"{wid}.json"
    if p.exists():
        c = json.load(open(p, encoding="utf-8"))
        return (c.get("artifacts") or {}).get("data_license") or ""
    return ""


def redaction_for(run_dir):
    for name in ("run_meta.json", "result.json"):
        p = run_dir / name
        if p.exists():
            txt = p.read_text(encoding="utf-8", errors="replace").lower()
            if "redact" in txt:
                return "item text redacted (hashes kept)"
            if "images" in txt and "not archived" in txt:
                return "image inputs not archived"
    return ""


def runs():
    for d in sorted((HALF / "runs").iterdir()):
        if d.is_dir() and re.fullmatch(r"(W\d+|T\d+)", d.name):
            yield "tierA", d.name, d
            for sub in d.iterdir():
                succ = sub.is_dir() and sub.name.startswith("successor_")      # successor condition of 2026-10-01 (scripts/tiera_successor.py)
                if sub.is_dir() and any((sub / f).exists() for f in FILES):
                    yield ("tierA_successor" if succ else "tierA"), d.name, sub
                if succ and (sub / "run").is_dir():
                    yield "tierA_successor", d.name, sub / "run"
    for d in sorted((HALF / "runs" / "tierb").iterdir()):
        if d.is_dir() and d.name.startswith("W"):
            base = re.match(r"W\d+", d.name).group(0)
            kind = "tierb" if re.fullmatch(r"W\d+", d.name) else "tierb_variant" if d.name.endswith("v2") else "tierb_superseded"
            yield kind, base, d
            if (d / "judge").is_dir():
                yield kind, base, d / "judge"
    cj = HALF / "runs" / "triage_crossjudge"            # cross-judgement of the triage verdicts (scripts/triage_crossjudge.py, 4 October 2026)
    if cj.is_dir():
        yield "triage_crossjudge", "triage", cj
    p3 = HALF / "runs" / "tierb_p3"
    if p3.is_dir():
        for arm in sorted(p3.iterdir()):
            for d in sorted(arm.iterdir()):
                if d.is_dir():
                    yield f"tierb_p3_{arm.name}", d.name, d
                    if (d / "judge").is_dir():
                        yield f"tierb_p3_{arm.name}", d.name, d / "judge"


def main():
    rows, total = [], 0
    for kind, wid, d in runs():
        red = redaction_for(d if d.name not in ("judge",) else d.parent)
        lic = licence_for(wid, kind)
        for name in FILES:
            p = d / name
            if not p.exists():
                continue
            digest, lines = sha_and_lines(p)
            size = p.stat().st_size; total += size
            rows.append({"kind": kind, "wid": wid, "path": p.relative_to(HALF).as_posix(), "bytes": size,
                         "records": lines if name.endswith(".jsonl") else "", "sha256": digest,
                         "data_licence": lic, "redaction": red,
                         "in_git": "no" if name in ("calls.jsonl", "requests.jsonl", "items.jsonl") and not kind.startswith("tierA") else "yes"})
    out = HALF / "data" / "deposit_manifest.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    kinds = {}
    for r in rows:
        k = kinds.setdefault(r["kind"], {"files": 0, "bytes": 0, "runs": set(), "calls": 0})
        k["files"] += 1; k["bytes"] += r["bytes"]; k["runs"].add(r["wid"])
        if r["path"].endswith("calls.jsonl"):
            k["calls"] += int(r["records"] or 0)
    print(f"{len(rows)} files, {total / 1e9:.2f} GB -> {out.relative_to(HALF)}")
    for k, v in kinds.items():
        print(f"  {k}: {len(v['runs'])} runs, {v['files']} files, {v['bytes'] / 1e6:.0f} MB, {v['calls']:,} archived calls")
    red = sorted({(r["wid"], r["redaction"]) for r in rows if r["redaction"]})
    print("redactions:", red)
    lic = {}
    for r in rows:
        if r["path"].endswith("calls.jsonl"):
            lic[r["data_licence"] or "(not recorded)"] = lic.get(r["data_licence"] or "(not recorded)", 0) + 1
    print("data licences over archived runs:", dict(sorted(lic.items(), key=lambda kv: -kv[1])[:12]))


if __name__ == "__main__":
    main()
