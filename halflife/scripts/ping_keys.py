"""Verify API keys in .env work (free model-list calls). Never prints key values."""
import json, os, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_env():
    p = ROOT / ".env"
    if not p.exists():
        return {}
    env = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:200]
        return e.code, {"error": body}


def main():
    env = load_env()
    checks = []

    k = env.get("OPENAI_API_KEY", "")
    if k:
        st, d = get("https://api.openai.com/v1/models", {"Authorization": f"Bearer {k}"})
        ids = [m["id"] for m in d.get("data", [])] if st == 200 else []
        dying = [m for m in ("gpt-4-turbo", "gpt-4o-2024-05-13", "o1-2024-12-17", "o3-mini", "o4-mini", "gpt-5") if m in ids]
        checks.append(("OpenAI", st, f"{len(ids)} models visible; dying-model access: {dying}" if st == 200 else d["error"]))
    else:
        checks.append(("OpenAI", None, "key missing"))

    k = env.get("ANTHROPIC_API_KEY", "")
    if k:
        st, d = get("https://api.anthropic.com/v1/models",
                    {"x-api-key": k, "anthropic-version": "2023-06-01"})
        n = len(d.get("data", [])) if st == 200 else 0
        checks.append(("Anthropic", st, f"{n} models visible" if st == 200 else d["error"]))
    else:
        checks.append(("Anthropic", None, "key missing"))

    k = env.get("GOOGLE_API_KEY", "")
    if k:
        st, d = get(f"https://generativelanguage.googleapis.com/v1beta/models?key={k}", {})
        n = len(d.get("models", [])) if st == 200 else 0
        checks.append(("Google", st, f"{n} models visible" if st == 200 else d["error"]))
    else:
        checks.append(("Google", None, "key missing"))

    for name, st, msg in checks:
        print(f"[{name}] HTTP {st}: {msg}")


if __name__ == "__main__":
    main()
