"""Pre-flight checks for the Zenodo deposit. No API calls; nothing leaves the machine.

Scans (1) every archive file listed in data/deposit_manifest.csv and (2) every tracked repository file that
`git archive` would package, and reports
  - BLOCKERS: any of the real secrets held in the repository .env (exact substring, compared in memory and never
    printed), key-like strings whose first characters coincide with a real key, forbidden paths (.env, key files,
    halflife/external), manifest files missing on disk;
  - REVIEW: key-shaped strings that do not match any real key (datasets and papers quote example keys), text that
    looks like an authorization header, e-mail addresses, local absolute paths, files above 1 GB;
  - the item-text licence class of every re-executed paper, derived from the licence text that
    deposit_manifest.py copied out of the Tier B configs and Tier A cards.
Findings are reported as file, line and pattern name only; a matched string is never printed.

Writes deposit/CHECKS.md and deposit/checks.json, and creates data/deposit_licence_decisions.csv when it does not
exist yet (one row per paper: licence text, automatic class, default decision include / include-nc / redact).
Edit the decision column by hand; deposit_package.py reads it. Existing decisions are never overwritten; new
papers are appended.
"""
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
ROOT = HALF.parent
DEP = HALF / "deposit"
MANIFEST = HALF / "data" / "deposit_manifest.csv"
DECISIONS = HALF / "data" / "deposit_licence_decisions.csv"

KEY_SHAPES = {
    "openai-shaped key": r"sk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{32,}",
    "anthropic-shaped key": r"sk-ant-[A-Za-z0-9_-]{20,}",
    "google-shaped key": r"AIza[0-9A-Za-z_-]{35}",
    "together-shaped key": r"tgp_v1_[A-Za-z0-9_-]{20,}",
    "bearer token": r"[Bb]earer\s+[A-Za-z0-9._~+/-]{24,}=*",
    "aws-shaped key": r"AKIA[0-9A-Z]{16}",
    "github-shaped token": r"gh[pousr]_[A-Za-z0-9]{30,}",
    "huggingface-shaped token": r"hf_[A-Za-z0-9]{30,}",
    "private key block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
}
KEY_RX = re.compile("|".join(f"(?P<g{i}>{p})" for i, p in enumerate(KEY_SHAPES.values())))
KEY_NAMES = {f"g{i}": n for i, n in enumerate(KEY_SHAPES)}
AUTH_RX = re.compile(r"[\"']?[Aa]uthorization[\"']?\s*[:=]")
EMAIL_RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PATH_RX = re.compile(r"(?:[A-Za-z]:\\+Users\\+|/c/Users/|/Users/|/home/)[A-Za-z0-9._-]+")
TEXT_EXT = {".jsonl", ".json", ".csv", ".md", ".txt", ".py", ".js", ".cmd", ".yaml", ".yml", ".toml", ".cfg", ".ini",
            ".tex", ".bib", ".html", ".xml", ".log", ".sh", ".ps1"}
BIG = 1_000_000_000

# ---------------------------------------------------------------- licence classes (item text)
RESTRICTED = (r"data use agreement", r"\bdua\b", r"never appear in plaintext", r"not to share", r"do not share",
              r"not be shared", r"no redistribution", r"not redistribut", r"canary", r"\brestricted\b")
UNKNOWN = (r"unknown", r"not stated", r"no licen[cs]e", r"unlicensed", r"not read", r"not found", r"no LICENSE")
NC = (r"-nc\b", r"\bnc\b", r"non-?commercial", r"by-nc")
OPEN = (r"\bmit\b", r"apache", r"\bbsd\b", r"cc-by", r"cc by", r"cc0", r"odc-by", r"cdla", r"\bgpl", r"printed in the paper",
        r"public benchmark", r"zenodo record", r"reproducibility package", r"public domain", r"creative commons attribution")
SEVERITY = {"open": 0, "nc": 1, "unknown": 2, "restricted": 3}
DEFAULT_DECISION = {"open": "include", "nc": "include-nc", "unknown": "redact", "restricted": "redact"}


def classify_clause(t):
    t = t.lower()
    if any(re.search(p, t) for p in RESTRICTED):
        return "restricted"
    if any(re.search(p, t) for p in UNKNOWN):
        return "unknown"
    if any(re.search(p, t) for p in NC):
        return "nc"
    if any(re.search(p, t) for p in OPEN):
        return "open"
    return "unknown"


def classify(text):
    """Most restrictive class over the clauses that speak about data; clauses about the code repository are
    ignored unless they are all there is."""
    if not text or not str(text).strip():
        return "unknown"
    clauses = [c.strip() for c in re.split(r";", str(text)) if c.strip()]
    data = [c for c in clauses if not re.search(r"\b(code|repo|repository)\b", c, re.I) or re.search(r"dataset|data card|items|prompts", c, re.I)]
    if not data:
        data = clauses
    return max((classify_clause(c) for c in data), key=lambda c: SEVERITY[c])


def forbidden(rel):
    rel = rel.replace("\\", "/")
    name = rel.rsplit("/", 1)[-1]
    return name == ".env" or name.startswith(".env.") and name != ".env.example" or "/external/" in "/" + rel \
        or name == ".openalex_key" or name.endswith((".key", ".pem")) or name.startswith("id_rsa")


def real_secrets():
    """Values of the .env entries (16+ characters) as (sha256 -> length) plus their 10-character prefixes;
    the values themselves are kept only in this process."""
    vals = []
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if len(v) >= 16:
                    vals.append(v)
    return vals


# ---------------------------------------------------------------- scanning
def scan_text_file(path, rel, F, secrets, prefixes):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for ln, line in enumerate(f, 1):
                for s in secrets:
                    if s in line:
                        F["real"][rel] += 1
                        F["real_first"].setdefault(rel, ln)
                for m in KEY_RX.finditer(line):
                    hit = m.group(0)
                    if hit[:10] in prefixes:
                        F["real"][rel] += 1
                        F["real_first"].setdefault(rel, ln)
                    key = (rel, KEY_NAMES[m.lastgroup])
                    F["shape"][key] += 1
                    F["shape_first"].setdefault(key, ln)
                n = len(AUTH_RX.findall(line))
                if n:
                    F["auth"][rel] += n
                    F["auth_first"].setdefault(rel, ln)
                n = len(EMAIL_RX.findall(line))
                if n:
                    F["email"][rel] += n
                    F["email_first"].setdefault(rel, ln)
                n = len(PATH_RX.findall(line))
                if n:
                    F["path"][rel] += n
                    F["path_first"].setdefault(rel, ln)
    except OSError as e:
        F["unreadable"].append((rel, str(e)))


def table(L, counter, first, head):
    L += ["| file | hits | first line |", "|---|---|---|"]
    items = sorted(counter.items(), key=lambda kv: -kv[1])
    for rel, n in items[:head]:
        L.append(f"| {rel} | {n} | {first[rel]} |")
    if len(items) > head:
        L.append(f"| ... {len(items) - head} more files | | |")


def main():
    DEP.mkdir(exist_ok=True)
    secrets = real_secrets()
    prefixes = {s[:10] for s in secrets}
    F = {"real": Counter(), "real_first": {}, "shape": Counter(), "shape_first": {}, "auth": Counter(), "auth_first": {},
         "email": Counter(), "email_first": {}, "path": Counter(), "path_first": {}, "forbidden": [], "big": [], "missing": [], "unreadable": []}
    rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8-sig")))
    print(f"manifest rows: {len(rows):,}; real secrets loaded for comparison: {len(secrets)}")
    scanned = 0
    seen = set()
    for r in rows:
        rel = r["path"]
        p = HALF / rel
        seen.add(("halflife/" + rel).replace("\\", "/"))
        if not p.exists():
            F["missing"].append(rel)
            continue
        if forbidden(rel):
            F["forbidden"].append(rel)
        if int(r["bytes"]) > BIG:
            F["big"].append((rel, int(r["bytes"])))
        if p.suffix.lower() in TEXT_EXT:
            scan_text_file(p, rel, F, secrets, prefixes)
            scanned += 1
            if scanned % 400 == 0:
                print(f"  scanned {scanned} archive files", flush=True)
    tracked = [t for t in subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n") if t]
    n_repo = 0
    for t in tracked:
        if t in seen:
            continue
        if forbidden(t):
            F["forbidden"].append(t)
        p = ROOT / t
        if p.suffix.lower() in TEXT_EXT and p.exists():
            scan_text_file(p, t, F, secrets, prefixes)
            n_repo += 1
        if p.exists() and p.stat().st_size > BIG:
            F["big"].append((t, p.stat().st_size))
    print(f"scanned {scanned} archive files and {n_repo} tracked repository files")

    # licence classes per paper
    lic = {}
    for r in rows:
        wid = r["wid"]
        v = lic.setdefault(wid, {"wid": wid, "kinds": set(), "licence": "", "redacted_at_source": ""})
        v["kinds"].add(r["kind"])
        if not v["licence"] and r.get("data_licence"):
            v["licence"] = r["data_licence"]
        if r.get("redaction"):
            v["redacted_at_source"] = r["redaction"]
    for v in lic.values():
        v["class"] = classify(v["licence"])
    existing = {r["wid"]: r for r in csv.DictReader(open(DECISIONS, encoding="utf-8-sig"))} if DECISIONS.exists() else {}
    out_rows, added = [], 0
    for wid in sorted(lic):
        v = lic[wid]
        if wid in existing:
            row = existing[wid]
            row.update({"licence_text": v["licence"], "auto_class": v["class"], "kinds": "|".join(sorted(v["kinds"])), "redacted_at_source": v["redacted_at_source"]})
        else:
            row = {"wid": wid, "kinds": "|".join(sorted(v["kinds"])), "licence_text": v["licence"], "auto_class": v["class"],
                   "decision": DEFAULT_DECISION[v["class"]], "redacted_at_source": v["redacted_at_source"], "note": ""}
            added += 1
        out_rows.append(row)
    with open(DECISIONS, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["wid", "kinds", "licence_text", "auto_class", "decision", "redacted_at_source", "note"])
        w.writeheader()
        w.writerows(out_rows)
    classes = Counter(r["auto_class"] for r in out_rows)
    decisions = Counter(r["decision"] for r in out_rows)

    # report
    blockers = len(F["real"]) + len(F["forbidden"]) + len(F["missing"])
    review = len(F["shape"]) + len(F["auth"]) + len(F["email"]) + len(F["path"]) + len(F["big"])
    L = [f"# Deposit pre-flight ({date.today().isoformat()})", "",
         f"Archive files scanned: {scanned:,} of {len(rows):,} manifest rows (text files only); tracked repository files scanned: {n_repo:,}; "
         f"real secrets compared: {len(secrets)} values from .env.", "",
         f"**BLOCKERS: {blockers}** (files containing a real secret or a key sharing its prefix, forbidden paths, missing files). "
         f"**REVIEW: {review}** (key-shaped strings that match no real key, authorization-header text, e-mail addresses, local paths, files above 1 GB).", ""]
    L += ["## Files containing a real secret (blocker)", ""]
    if F["real"]:
        table(L, F["real"], F["real_first"], 100)
        L.append("")
        L.append("Rotate the key at the vendor and rebuild the archive; removing the string alone is not enough.")
    else:
        L.append("None: no value from .env, and no key sharing a real key's prefix, occurs in any scanned file.")
    L += ["", "## Forbidden paths (blocker)", ""] + ([f"- {x}" for x in F["forbidden"]] or ["None."])
    L += ["", "## Manifest files missing on disk (blocker)", ""] + ([f"- {x}" for x in F["missing"]] or ["None."])
    L += ["", "## Key-shaped strings that match no real key (review)", "",
          "Datasets about API security and papers about key leakage quote example keys; confirm each file is such a case.", ""]
    if F["shape"]:
        L += ["| file | shape | hits | first line |", "|---|---|---|---|"]
        for (rel, name), n in sorted(F["shape"].items(), key=lambda kv: -kv[1])[:100]:
            L.append(f"| {rel} | {name} | {n} | {F['shape_first'][(rel, name)]} |")
    else:
        L.append("None.")
    L += ["", "## Authorization-header text (review)", ""]
    if F["auth"]:
        table(L, F["auth"], F["auth_first"], 60)
    else:
        L.append("None.")
    L += ["", "## E-mail addresses (review; datasets and documents may legitimately contain them)", ""]
    if F["email"]:
        table(L, F["email"], F["email_first"], 60)
    else:
        L.append("None.")
    L += ["", "## Local absolute paths (review)", ""]
    if F["path"]:
        table(L, F["path"], F["path_first"], 60)
    else:
        L.append("None.")
    L += ["", "## Files above 1 GB", ""] + ([f"- {x} ({b / 1e9:.2f} GB)" for x, b in F["big"]] or ["None (Zenodo allows 50 GB per record)."])
    L += ["", "## Item-text licence classes (one row per paper)", "", "| class | papers | default decision |", "|---|---|---|"]
    for c in ("open", "nc", "unknown", "restricted"):
        L.append(f"| {c} | {classes.get(c, 0)} | {DEFAULT_DECISION[c]} |")
    L += ["", f"Decisions in `data/deposit_licence_decisions.csv` ({added} rows added this run): " + ", ".join(f"{k} {v}" for k, v in sorted(decisions.items())) + ".",
          "Papers classed unknown or restricted are packaged with item and message text replaced by SHA-256 hashes unless their decision is changed to include.", "",
          "| paper | kinds | class | decision | licence text |", "|---|---|---|---|---|"]
    for r in out_rows:
        if r["auto_class"] in ("unknown", "restricted") or r["decision"] == "redact":
            L.append(f"| {r['wid']} | {r['kinds']} | {r['auto_class']} | {r['decision']} | {str(r['licence_text'])[:140]} |")
    if F["unreadable"]:
        L += ["", "## Unreadable files", ""] + [f"- {x}: {e}" for x, e in F["unreadable"]]
    L += ["", "## Next steps", "",
          "1. Resolve every blocker (a real key must be rotated at the vendor, not only removed from the file).",
          "2. Go through the review lists; decide per file.",
          "3. Check the licence decisions, then run `python scripts/deposit_package.py` to build the bundle.",
          "4. Rehearse the upload on sandbox.zenodo.org with `python scripts/zenodo_upload.py plan` / `create` / `upload`.", ""]
    (DEP / "CHECKS.md").write_text("\n".join(L), encoding="utf-8")
    json.dump({"blockers": blockers, "review": review, "real_secret_files": dict(F["real"]), "forbidden": F["forbidden"], "missing": F["missing"],
               "key_shaped": {f"{k[0]}::{k[1]}": v for k, v in F["shape"].items()}, "auth_header": dict(F["auth"]), "emails": dict(F["email"]),
               "paths": dict(F["path"]), "big": F["big"], "classes": dict(classes), "decisions": dict(decisions)},
              open(DEP / "checks.json", "w", encoding="utf-8"), indent=1)
    print(f"BLOCKERS {blockers} | REVIEW {review} | classes {dict(classes)} | decisions {dict(decisions)}")
    print("->", DEP / "CHECKS.md", "|", DECISIONS)
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
