"""Minimal OpenAI chat-completions client with full request/response logging.

Raw HTTPS (stdlib) so the exact wire payloads are archived. Never logs the key.
"""
import datetime, hashlib, json, os, re, sys, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root (NMI_RS)


def load_env():
    p = ROOT / ".env"
    env = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def sha256(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


CREDIT_WAIT_S = 30 * 60      # how long a call waits for an auto-recharge before it counts as failed


PROVIDERS = {
    # OpenAI-compatible chat-completions endpoints; the provider is chosen from the model id. Open-weight models hosted
    # on Together carry an organisation prefix ("meta-llama/...", "Qwen/..."); everything else goes to OpenAI.
    "openai": {"url": "https://api.openai.com/v1/chat/completions", "env": "OPENAI_API_KEY"},
    "together": {"url": "https://api.together.xyz/v1/chat/completions", "env": "TOGETHER_API_KEY"},
    # Together dedicated endpoints (v2) answer on a separate inference host; the model field carries the project-
    # qualified endpoint name ("<project slug>/<endpoint>"). Used for the BF16 check of the open-weight condition.
    "together_dedicated": {"url": "https://api-inference.together.ai/v1/chat/completions", "env": "TOGETHER_API_KEY"},
    # Google's OpenAI-compatible endpoint for the Gemini API (key from a dedicated Google Cloud project)
    "gemini": {"url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "env": "GEMINI_API_KEY",
               "env_alt": "GOOGLE_API_KEY"},   # the .env slot prepared for the Google arm is named GOOGLE_API_KEY
}
TOGETHER_DEDICATED_PREFIXES = ("erzyh34-1842/",)   # project slug of the dedicated endpoint used on 2026-09-28
UA = "halflife-tierb/0.1 (academic reproducibility study; python-urllib)"


def provider_of(model):
    m = str(model)
    if m.startswith("gemini"):
        return "gemini"
    if m.startswith(TOGETHER_DEDICATED_PREFIXES):
        return "together_dedicated"
    return "together" if "/" in m else "openai"


class OpenAIClient:
    URL = PROVIDERS["openai"]["url"]

    def __init__(self, api_key=None, max_retries=6):
        env = load_env()
        self.keys = {name: (env.get(p["env"]) or os.environ.get(p["env"], "")
                            or env.get(p.get("env_alt", ""), "") or os.environ.get(p.get("env_alt", ""), ""))
                     for name, p in PROVIDERS.items()}
        if api_key:
            self.keys["openai"] = api_key
        self.key = self.keys["openai"]
        if not any(self.keys.values()):
            raise RuntimeError("no API key found in .env or environment (OPENAI_API_KEY / TOGETHER_API_KEY / GEMINI_API_KEY)")
        self.max_retries = max_retries

    def chat(self, body):
        """POST body (dict) -> (response_json, latency_ms, http_status). Retries 429/5xx/network."""
        data = json.dumps(body).encode("utf-8")
        prov = provider_of(body.get("model"))
        key = self.keys.get(prov) or ""
        if not key:
            raise RuntimeError(f"{PROVIDERS[prov]['env']} not found in .env or environment (model {body.get('model')})")
        url = PROVIDERS[prov]["url"]
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json", "User-Agent": UA}
        last = ""
        credit_wait = 0
        quota_wait = 0
        daily_waits = 0
        i = -1
        while i + 1 < self.max_retries:
            i += 1
            t0 = time.time()
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=600) as r:      # reasoning successors can take 2-5 min per reply; a timed-out reply is still billed
                    resp = json.loads(r.read().decode("utf-8"))
                    return resp, int((time.time() - t0) * 1000), r.status
            except urllib.error.HTTPError as e:
                text = e.read().decode("utf-8", "replace")
                if e.code == 429 and ("no credits" in text.lower() or "insufficient_quota" in text.lower()):
                    # The account balance is exhausted. With auto-recharge on, the balance comes back within minutes,
                    # so wait (up to CREDIT_WAIT_S) instead of burning the retry budget and losing the item.
                    if credit_wait >= CREDIT_WAIT_S:
                        raise RuntimeError(f"HTTP 429 (no credits) persisted for {credit_wait // 60} min: {text[:200]}")
                    if credit_wait == 0:
                        print(f"[openai_client] no credits remaining; waiting for the recharge (up to {CREDIT_WAIT_S // 60} min)", file=sys.stderr, flush=True)
                    time.sleep(60)
                    credit_wait += 60
                    i -= 1                                   # a credit wait does not consume a retry
                    continue
                if e.code == 429 and prov == "gemini" and ("RESOURCE_EXHAUSTED" in text or "quota" in text.lower()):
                    # Google AI Studio rate limits (Tier 1, 2026-09-21: 3.1 Pro 25 RPM / 250 RPD, 3.8 Flash 1K RPM / 10K RPD).
                    # A per-day quota resets at midnight Pacific time, a per-minute one clears within a minute; neither
                    # consumes the retry budget, otherwise the item would be lost. A quota message that names no period
                    # is treated as per-minute until ten minutes have passed, then as the daily quota.
                    daily = "perday" in text.lower().replace("_", "") or quota_wait >= 600
                    if daily:
                        if daily_waits >= 2:
                            raise RuntimeError(f"HTTP 429 (Google daily quota) persisted across two resets: {text[:200]}")
                        wait = seconds_to_pacific_midnight() + 90
                        print(f"[openai_client] Google daily quota reached for {body.get('model')}; sleeping {wait // 60} min "
                              f"until the Pacific-midnight reset ({text[:100]!r})", file=sys.stderr, flush=True)
                        time.sleep(wait)
                        daily_waits += 1
                        quota_wait = 0
                    else:
                        m = re.search(r'retryDelay[^0-9]*(\d+)', text)
                        pause = min(int(m.group(1)) if m else 20, 120) + 1
                        time.sleep(pause)
                        quota_wait += pause
                    i -= 1
                    continue
                if e.code in (429, 500, 502, 503, 504):
                    last = f"HTTP {e.code}: {text[:160]}"
                    time.sleep(min(2 ** i * 2, 60))
                    continue
                raise RuntimeError(f"HTTP {e.code}: {text[:300]}")
            except Exception as ex:
                last = f"{type(ex).__name__}: {str(ex)[:160]}"
                time.sleep(min(2 ** i * 2, 60))
        raise RuntimeError(f"exhausted retries (last: {last})")



def seconds_to_pacific_midnight():
    """Google AI Studio's per-day request quotas reset at midnight Pacific time."""
    try:
        from zoneinfo import ZoneInfo
        now = datetime.datetime.now(ZoneInfo("America/Los_Angeles"))
    except Exception:                                   # no tz database: assume PDT (UTC-7)
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-7)))
    nxt = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(60, int((nxt - now).total_seconds()))


def cost_usd(usage, pricing):
    """usage = response['usage']; pricing = {'input': $/1M, 'output': $/1M}."""
    pi = usage.get("prompt_tokens", 0)
    po = usage.get("completion_tokens", 0)
    # Gemini's OpenAI-compatible endpoint leaves thinking tokens out of completion_tokens but bills them as output;
    # they are visible only as total - prompt - completion. OpenAI counts reasoning inside completion_tokens, so
    # total - prompt equals completion_tokens there and this line changes nothing.
    if usage.get("total_tokens"):
        po = max(po, usage["total_tokens"] - pi)
    return pi / 1e6 * pricing["input"] + po / 1e6 * pricing["output"]
