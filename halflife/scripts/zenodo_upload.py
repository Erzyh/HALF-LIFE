"""Zenodo helper for the HALF-LIFE deposit bundle (halflife/deposit/). Defaults are inert on purpose.

  target   sandbox (sandbox.zenodo.org, a test server whose content is not permanent and not indexed) unless
           --target production is given
  token    ZENODO_SANDBOX_TOKEN or ZENODO_TOKEN in the repository .env (personal access token with the
           deposit:write and deposit:actions scopes); the value is never printed
  publish  refused unless --target production, --publish and --confirm "PUBLISH <reserved doi>" are all given
           and deposit/CHECKS.md reports BLOCKERS: 0. Publishing is one-way: files can then only be changed
           through a new version.

Commands
  plan      list the files, sizes and metadata that would be sent (no network)
  create    create a draft record with the metadata from deposit/zenodo_metadata.json and reserve its DOI;
            the record id, bucket URL and DOI are saved to deposit/zenodo_state.json
  upload    upload every file of deposit/ into the draft; files already present with the same MD5 are skipped
  status    show the draft's files, size and reserved DOI
  publish   see above

Written against the Zenodo REST API (https://developers.zenodo.org, deposit endpoints and the files bucket) on
2026-09-24; not yet exercised against a live account.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
ROOT = HALF.parent
DEP = HALF / "deposit"
STATE = DEP / "zenodo_state.json"
API = {"sandbox": "https://sandbox.zenodo.org/api", "production": "https://zenodo.org/api"}
SKIP = {"zenodo_state.json", "checks.json", "CHECKS.md", "zenodo_metadata.json"}


def read_env():
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def token_for(target):
    env = read_env()
    key = "ZENODO_SANDBOX_TOKEN" if target == "sandbox" else "ZENODO_TOKEN"
    return env.get(key) or "", key


def bundle_files():
    return sorted(p for p in DEP.iterdir() if p.is_file() and p.name not in SKIP and not p.name.startswith("."))


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state(target):
    if STATE.exists():
        return json.load(open(STATE, encoding="utf-8")).get(target)
    return None


def save_state(target, rec):
    all_ = json.load(open(STATE, encoding="utf-8")) if STATE.exists() else {}
    all_[target] = rec
    json.dump(all_, open(STATE, "w", encoding="utf-8"), indent=1)


def session(token):
    import requests
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


def cmd_plan(args):
    files = bundle_files()
    total = sum(p.stat().st_size for p in files)
    print(f"target: {args.target} ({API[args.target]})")
    for p in files:
        print(f"  {p.stat().st_size / 1e6:10.1f} MB  {p.name}")
    print(f"  total {total / 1e9:.2f} GB in {len(files)} files (Zenodo: 50 GB per record)")
    meta = json.load(open(DEP / "zenodo_metadata.json", encoding="utf-8"))["metadata"]
    print("metadata:", json.dumps({k: meta[k] for k in ("title", "upload_type", "access_right", "license", "version")}, ensure_ascii=False))
    tok, key = token_for(args.target)
    print(f"token {key}: {'present' if tok else 'absent (plan only)'}")
    checks = DEP / "CHECKS.md"
    print("pre-flight:", checks.read_text(encoding='utf-8').split("**BLOCKERS: ")[1].split("**")[0] if checks.exists() and "**BLOCKERS: " in checks.read_text(encoding="utf-8") else "not run")


def cmd_create(args):
    tok, key = token_for(args.target)
    if not tok:
        sys.exit(f"no {key} in .env; add a personal access token first (deposit:write, deposit:actions)")
    if load_state(args.target) and not args.new:
        sys.exit(f"a {args.target} draft already exists in {STATE}; use --new to create another")
    s = session(tok)
    r = s.post(f"{API[args.target]}/deposit/depositions", json={})
    r.raise_for_status()
    dep = r.json()
    meta = json.load(open(DEP / "zenodo_metadata.json", encoding="utf-8"))
    r = s.put(f"{API[args.target]}/deposit/depositions/{dep['id']}", json=meta)
    r.raise_for_status()
    dep = r.json()
    doi = (dep.get("metadata", {}).get("prereserve_doi") or {}).get("doi", "")
    rec = {"id": dep["id"], "bucket": dep["links"]["bucket"], "html": dep["links"].get("html", ""), "doi": doi, "created": dep.get("created")}
    save_state(args.target, rec)
    print(f"draft created on {args.target}: id {rec['id']}, reserved DOI {doi or '(none returned)'}, page {rec['html']}")


def cmd_upload(args):
    tok, key = token_for(args.target)
    st = load_state(args.target)
    if not tok or not st:
        sys.exit("need a token in .env and an existing draft (run create first)")
    s = session(tok)
    if not st.get("bucket"):          # a draft created by hand in the web form: fetch its files bucket once and remember it
        r = s.get(f"{API[args.target]}/deposit/depositions/{st['id']}")
        r.raise_for_status()
        st["bucket"] = r.json()["links"]["bucket"]
        save_state(args.target, st)
    r = s.get(f"{API[args.target]}/deposit/depositions/{st['id']}/files")
    r.raise_for_status()
    present = {f["filename"]: f.get("checksum", "").replace("md5:", "") for f in r.json()}
    for p in bundle_files():
        local = md5_of(p)
        if present.get(p.name) == local:
            print(f"  = {p.name} already uploaded")
            continue
        print(f"  ^ {p.name} ({p.stat().st_size / 1e6:.1f} MB)", flush=True)
        with open(p, "rb") as fh:
            r = s.put(f"{st['bucket']}/{p.name}", data=fh)
        r.raise_for_status()
        remote = r.json().get("checksum", "").replace("md5:", "")
        print("    ok" if remote == local else f"    WARNING checksum mismatch (remote {remote[:8]}..., local {local[:8]}...)")
    print("upload finished; verify with: python scripts/zenodo_upload.py status --target", args.target)


def cmd_status(args):
    tok, key = token_for(args.target)
    st = load_state(args.target)
    if not tok or not st:
        sys.exit("need a token in .env and an existing draft (run create first)")
    s = session(tok)
    r = s.get(f"{API[args.target]}/deposit/depositions/{st['id']}")
    r.raise_for_status()
    dep = r.json()
    files = dep.get("files", [])
    print(f"{args.target} draft {dep['id']}: state {dep.get('state')}, submitted {dep.get('submitted')}, DOI {(dep.get('metadata', {}).get('prereserve_doi') or {}).get('doi', '')}")
    print(f"  {len(files)} files, {sum(f.get('filesize', 0) for f in files) / 1e9:.2f} GB")
    for f in files:
        print(f"    {f.get('filesize', 0) / 1e6:10.1f} MB  {f['filename']}")


def cmd_publish(args):
    if args.target != "production" or not args.publish:
        sys.exit("publishing needs --target production and --publish")
    st = load_state("production")
    if not st:
        sys.exit("no production draft in zenodo_state.json")
    checks = (DEP / "CHECKS.md").read_text(encoding="utf-8") if (DEP / "CHECKS.md").exists() else ""
    if "**BLOCKERS: 0**" not in checks:
        sys.exit("deposit/CHECKS.md does not report BLOCKERS: 0; run scripts/deposit_preflight.py and resolve the findings")
    if args.confirm != f"PUBLISH {st.get('doi', '')}" or not st.get("doi"):
        sys.exit(f"confirmation phrase must be exactly: PUBLISH {st.get('doi', '<reserved doi>')}")
    tok, _ = token_for("production")
    s = session(tok)
    r = s.post(f"{API['production']}/deposit/depositions/{st['id']}/actions/publish")
    r.raise_for_status()
    dep = r.json()
    print(f"published: DOI {dep.get('doi')} page {dep['links'].get('record_html', dep['links'].get('html', ''))}")
    print("this cannot be undone; later corrections go into a new version")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["plan", "create", "upload", "status", "publish"])
    ap.add_argument("--target", choices=["sandbox", "production"], default="sandbox")
    ap.add_argument("--new", action="store_true", help="create: start another draft even if one is recorded")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--confirm", default="")
    args = ap.parse_args()
    {"plan": cmd_plan, "create": cmd_create, "upload": cmd_upload, "status": cmd_status, "publish": cmd_publish}[args.command](args)


if __name__ == "__main__":
    main()
