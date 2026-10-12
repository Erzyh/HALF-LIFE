"""Tier B runner: execute one run config (harness/tierb/configs/<Wid>.json) end to end.

  python tierb_runner.py W4404782525 --prepare            # fetch items, format prompts, report counts
  python tierb_runner.py W4404782525 --dry-run            # token/cost estimate, no API calls
  python tierb_runner.py W4404782525 --run --cap 40       # call the model (battery.py archive)
  python tierb_runner.py W4404782525 --analyze            # parse, metric, bootstrap CI, compare

Outputs under runs/tierb/<Wid>/: items.jsonl (the exact inputs used, with the subset rule applied),
requests.jsonl, calls.jsonl + budget.json (from battery.py), result.json.

Supported pieces (anything else stops with status needs_human and a reason):
  items.source_type  hf (items.hf = {dataset, config|configs, split|splits}; parquet via the Hub API) | github |
                     url | zenodo (items.file_url: json / jsonl / csv / tsv / parquet by extension; JSON may be a
                     list, a dict with a list under data/items/instances/..., a dict of records, or a dict of
                     parallel lists) | in_paper (items.inline)
  items.label_map    {"maybe": "unanswerable"}; items.label_transform "index_to_letter" | "index_to_letter_1"
  placeholders       filled in both prompt.system and prompt.user_template; braces inside item text are safe
  placeholders       "items.<field>" | "options_lettered(<field>)" (A. .. B. ..) | "options_numbered(<field>)"
                     | "join(<field>, <sep>)" | "literal:<text>"
  output.parse       "letter" (first standalone A-Z option letter) | "label from set [a, b, c]" | "json field <name>"
                     | "regex <pattern>" (group 1) | "number" (last number in the reply) | "free text"
  metric.name        accuracy | exact_match | macro_f1 | micro_f1 | rouge_l | mean_error | mean_abs_error | pearson
Per-paper cost cap: if the dry-run estimate exceeds --cap, a seeded random subset (seed 20260907) of the
items is used and recorded in result.json (approximation).
"""
import argparse, csv, io, json, math, re, sys, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from battery import estimate, load_results, pricing_for, run_battery  # noqa: E402

HALF = HERE.parent
CONFIGS = HERE / "tierb" / "configs"
RUNS = HALF / "runs" / "tierb"
DATA = HALF / "external" / "data" / "tierb_items"
SEED = 20260907
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
MODEL_OVERRIDE = None       # --model: run the same config on another model (successor arm); see load_cfg()
SEEDS_OVERRIDE = None       # --seeds: passes per item for the arm (the successor arms use 1; the baseline used the config's 3)
MAX_ITEMS = None            # --max-items: seeded random subset for an arm whose provider rations requests per day (Gemini arm fallback)


def load_cfg(wid):
    """The paper's config; with --model the model id is swapped for the successor and the paper's own decoding
    parameters are kept (body_for drops the ones a reasoning model rejects). Archives then go to
    runs/tierb_p3/<arm>/<wid>/ instead of runs/tierb/<wid>/, so the pre-shutdown baseline is never touched."""
    cfg = json.loads((CONFIGS / f"{wid}.json").read_text(encoding="utf-8"))
    if MODEL_OVERRIDE:
        cfg["model"] = dict(cfg["model"], id=MODEL_OVERRIDE, config_id=cfg["model"]["id"])
        params = dict(cfg["model"].get("params") or {})
        if params.get("reasoning_effort") == "minimal" and MODEL_OVERRIDE.startswith("gpt-5.6"):
            params["reasoning_effort"] = "none"      # gpt-5.6 accepts none/low/medium/high/xhigh; 'minimal' is rejected (HTTP 400)
            cfg["model"]["params"] = params
            cfg["model"]["params_note"] = "reasoning_effort minimal -> none for the gpt-5.6 successor"
    if SEEDS_OVERRIDE:
        cfg["model"] = dict(cfg["model"], seeds=SEEDS_OVERRIDE, config_seeds=cfg["model"].get("seeds"))
    return cfg


class NeedsHuman(Exception):
    pass


# ----------------------------------------------------------------------------- items
def _get(url, timeout=120, limit=250 * 1024 * 1024):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(limit)


def _parse_table(data, name):
    name = name.lower()
    if name.endswith(".jsonl") or name.endswith(".ndjson"):
        return [json.loads(l) for l in data.decode("utf-8", "replace").splitlines() if l.strip()]
    if name.endswith(".json"):
        obj = json.loads(data.decode("utf-8", "replace"))
        if isinstance(obj, dict):
            for k in ("data", "items", "examples", "test", "questions", "rows", "instances", "samples", "records"):
                if isinstance(obj.get(k), list):
                    return obj[k]
            if all(isinstance(v, dict) for v in obj.values()):
                return [{"id": k, **v} for k, v in obj.items()]
            if all(isinstance(v, list) for v in obj.values()) and len({len(v) for v in obj.values()}) == 1:
                keys = list(obj)                                  # dict of parallel lists -> rows
                return [{k: obj[k][i] for k in keys} for i in range(len(obj[keys[0]]))]
        return obj
    if name.endswith(".csv") or name.endswith(".tsv"):
        sep = "\t" if name.endswith(".tsv") else ","
        return list(csv.DictReader(io.StringIO(data.decode("utf-8", "replace")), delimiter=sep))
    if name.endswith(".parquet"):
        import pandas as pd
        return pd.read_parquet(io.BytesIO(data)).to_dict("records")
    raise NeedsHuman(f"unknown table format for {name}")


def load_hf(dataset, config_or_split):
    """Hub parquet listing first; datasets-server rows as fallback. config_or_split: 'split' or 'config/split'."""
    import pandas as pd
    parts = (config_or_split or "test").split("/")
    config, split = (parts[0], parts[1]) if len(parts) == 2 else (None, parts[0])
    listing = json.loads(_get(f"https://huggingface.co/api/datasets/{dataset}/parquet").decode("utf-8"))
    if config is None:
        config = "default" if "default" in listing else next(iter(listing))
    if config not in listing or split not in listing[config]:
        raise NeedsHuman(f"hf parquet listing has no {config}/{split}; available: "
                         + "; ".join(f"{c}: {list(s)}" for c, s in listing.items()))
    frames = [pd.read_parquet(io.BytesIO(_get(u))) for u in listing[config][split]]
    return pd.concat(frames, ignore_index=True).to_dict("records")


def load_items(cfg):
    it = cfg["items"]
    st, src = it.get("source_type"), it.get("source", "")
    if st == "in_paper":
        rows = it.get("inline")
        if not rows:
            raise NeedsHuman("in_paper items but items.inline is empty")
    elif st == "hf":
        hf = it.get("hf")                      # machine fields (CONFIG_SCHEMA.md, 'machine fields')
        if isinstance(hf, dict) and hf.get("dataset"):
            configs = hf.get("configs") or [hf.get("config")]
            splits = hf.get("splits") or [hf.get("split", "test")]
            rows = []
            for cfg_name in configs:
                for split in splits:
                    cs = f"{cfg_name}/{split}" if cfg_name else split
                    part = load_hf(hf["dataset"], cs)
                    for r in part:
                        r.setdefault("_config", cfg_name)
                        r.setdefault("_split", split)
                    rows += part
        else:
            if not re.fullmatch(r"[\w.\-]+/[\w.\-]+", src.strip()):
                raise NeedsHuman(f"items.source is not a bare Hub id ({src!r}); add items.hf = {{dataset, config, split}}")
            rows = load_hf(src.strip(), it.get("config_or_split"))
    elif st in ("github", "url", "zenodo"):
        url = it.get("file_url") or src
        if "github.com" in url and "/blob/" in url:
            url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        if not url.startswith("http") or " " in url.strip():
            raise NeedsHuman(f"items.file_url must be a direct file URL (got {url!r})")
        rows = _parse_table(_get(url), urllib.parse.urlparse(url).path)
    else:
        raise NeedsHuman(f"unsupported items.source_type {st}")
    lm = it.get("label_map")
    lf = (it.get("fields") or {}).get("label")
    if lm and lf:
        for r in rows:
            if isinstance(r, dict) and lf in r and str(r[lf]) in lm:
                r[lf] = lm[str(r[lf])]
    lt = (it.get("label_transform") or "").strip()      # "index_to_letter" (0-based) | "index_to_letter_1" (1-based)
    if lt.startswith("index_to_letter") and lf:
        base = 1 if lt.endswith("_1") else 0
        for r in rows:
            try:
                r[lf] = chr(65 + int(r[lf]) - base)
            except (TypeError, ValueError):
                pass
    filt = (it.get("filter") or "").strip()
    if filt and filt.lower() not in ("none", "no filter", "-", ""):
        import pandas as pd
        df = pd.DataFrame(rows)
        try:
            rows = df.query(filt).to_dict("records")
        except Exception as e:
            raise NeedsHuman(f"cannot apply items.filter {filt!r}: {e}")
    return rows


def apply_subset(rows, rule, cap_fraction=1.0):
    rule = (rule or "all").strip()
    rng = np.random.default_rng(SEED)
    m = re.search(r"seeded random (\d+)", rule)
    if m:
        n = int(m.group(1))
        if n < len(rows):
            idx = rng.choice(len(rows), n, replace=False)
            rows = [rows[i] for i in sorted(idx)]
    if cap_fraction < 1.0:
        n = max(30, int(len(rows) * cap_fraction))
        idx = rng.choice(len(rows), n, replace=False)
        rows = [rows[i] for i in sorted(idx)]
    return rows


# ----------------------------------------------------------------------------- prompts
def field(row, name):
    if name in row:
        return row[name]
    for k in row:                       # nested like meta.x
        pass
    cur = row
    for part in name.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise NeedsHuman(f"item has no field {name!r}; fields: {list(row)[:12]}")
    return cur


def render_placeholder(spec, row):
    spec = spec.strip()
    if spec.startswith("literal:"):
        return spec[len("literal:"):]
    m = re.match(r"options_(lettered|numbered)\((\w[\w.]*)\)", spec)
    if m:
        opts = field(row, m.group(2))
        if isinstance(opts, dict):
            return "\n".join(f"{k}. {v}" for k, v in opts.items())
        if isinstance(opts, str):
            try:
                opts = json.loads(opts)
            except Exception:
                opts = [o.strip() for o in re.split(r"\n|\|", opts) if o.strip()]
        if m.group(1) == "lettered":
            return "\n".join(f"{chr(65 + i)}. {o}" for i, o in enumerate(opts))
        return "\n".join(f"{i + 1}. {o}" for i, o in enumerate(opts))
    m = re.match(r"join\((\w[\w.]*),\s*'(.*)'\)", spec)
    if m:
        return m.group(2).encode().decode("unicode_escape").join(str(x) for x in field(row, m.group(1)))
    m = re.match(r"items\.(\w[\w.]*)$", spec) or re.match(r'items\.\[(.+)\]$', spec) or re.match(r'items\."(.+)"$', spec)
    if m:
        v = field(row, m.group(1))
        return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    raise NeedsHuman(f"placeholder spec not machine-readable: {spec!r}")


def render(cfg, row):
    p = cfg["prompt"]
    values = {name: render_placeholder(spec, row) for name, spec in (p.get("placeholders") or {}).items()}

    def fill(template):
        # slots are checked on the template itself, so braces inside item text never count as slots
        missing = [n for n in re.findall(r"\{(\w+)\}", template) if n not in values]
        if missing:
            raise NeedsHuman(f"unfilled placeholders {missing}")
        for name, v in values.items():
            template = template.replace("{" + name + "}", str(v))
        return template
    msgs = []
    if p.get("system"):
        msgs.append({"role": "system", "content": fill(p["system"])})
    msgs.append({"role": "user", "content": fill(p["user_template"])})
    return msgs


def plain(obj):
    """numpy / pandas scalars and arrays -> plain Python for json.dumps."""
    if isinstance(obj, dict):
        return {str(k): plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [plain(v) for v in obj]
    if hasattr(obj, "tolist"):
        return plain(obj.tolist())
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            return obj.item()
        except Exception:
            return str(obj)
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


GEMINI_THINK_ALLOWANCE = 2048   # Gemini counts thinking tokens inside max_tokens; 3.1 Pro at its lowest level spends ~300
GEMINI_MAX_OUTPUT = 65536        # output limit of gemini-3.1-pro-preview and gemini-3.8-flash (models endpoint, 2026-09-21)


def gemini_body(body):
    """Make a request legal for Google's OpenAI-compatible endpoint (probed 2026-09-21): seed, logprobs, top_logprobs,
    frequency_penalty and presence_penalty are rejected as unknown fields; thinking cannot be switched off on 3.1 Pro,
    so the lowest level is requested (on 3.8 Flash 'low' means no thinking) and the paper's output allowance is raised
    by a fixed amount so that the hidden thinking does not truncate the answer. The thinking tokens actually consumed
    stay visible in usage.total_tokens - prompt_tokens - completion_tokens of every archived call."""
    b = dict(body)
    for k in ("seed", "logprobs", "top_logprobs", "frequency_penalty", "presence_penalty"):
        b.pop(k, None)
    b.setdefault("reasoning_effort", "low")
    if b.get("max_completion_tokens") is not None:
        b["max_tokens"] = b.pop("max_completion_tokens")
    b["max_tokens"] = min(int(b.get("max_tokens") or 1024) + GEMINI_THINK_ALLOWANCE, GEMINI_MAX_OUTPUT)
    return b


def normalize_body(body):
    """Make a hook-built request body legal for the model it names: reasoning models (o1/o3/o4/gpt-5 and the gpt-5.6
    successors) take max_completion_tokens instead of max_tokens and reject temperature/top_p/logprobs; a
    reasoning_effort of 'minimal' is not accepted by gpt-5.6 and becomes 'none'; Gemini bodies go through
    gemini_body(). Other models are returned unchanged."""
    mid = str(body.get("model", ""))
    if mid.startswith("gemini"):
        return gemini_body(body)
    if not mid.startswith(("o1", "o3", "o4", "gpt-5")):
        return body
    b = dict(body)
    if "max_tokens" in b:
        mt = b.pop("max_tokens")
        if mt is not None:
            b["max_completion_tokens"] = max(int(mt), 8192 if MODEL_OVERRIDE else 2048)
    for k in ("temperature", "top_p", "logprobs", "top_logprobs", "frequency_penalty", "presence_penalty", "seed"):
        b.pop(k, None)
    if b.get("reasoning_effort") == "minimal" and mid.startswith("gpt-5.6"):
        b["reasoning_effort"] = "none"
    return b


def body_for(cfg, msgs):
    m = cfg["model"]
    params = dict(m.get("params") or {})
    body = {"model": m["id"], "messages": msgs}
    reasoning = m["id"].startswith(("o1", "o3", "o4", "gpt-5"))
    other_model = bool(MODEL_OVERRIDE) and m.get("config_id") not in (None, m["id"])   # a same-model re-run keeps the baseline's body
    if reasoning:
        if params.get("max_tokens") is not None:
            body["max_completion_tokens"] = max(int(params["max_tokens"]), 8192 if other_model else 2048)
        for k in ("reasoning_effort",):
            if params.get(k) is not None:
                body[k] = params[k]
    else:
        for k in ("temperature", "max_tokens", "top_p", "seed", "response_format", "logprobs", "top_logprobs",
                  "frequency_penalty", "presence_penalty", "stop"):
            if k in params and params[k] is not None:
                body[k] = params[k]
        if other_model and "/" in m["id"] and body.get("max_tokens") and int(body["max_tokens"]) > 8192:
            # a reasoning paper's 100k output allowance is meaningless for an instruction model and exceeds the hosted
            # model's context check (HTTP 422 on Together); the arm keeps a generous but legal ceiling
            body["max_tokens"] = 8192
    if m["id"].startswith("gemini"):
        body = gemini_body(body)
    return body



def prepare_from_baseline(wid, cap):
    """Same-model re-run (the drift control): reuse the pre-retirement baseline's items and its seed-0 request bodies
    verbatim, so that the only thing that differs from the baseline call is the date on which it is made."""
    base = HALF / "runs" / "tierb" / wid
    out = RUNS / wid
    out.mkdir(parents=True, exist_ok=True)
    items = [l for l in open(base / "items.jsonl", encoding="utf-8") if l.strip()]
    reqs = [json.loads(l) for l in open(base / "requests.jsonl", encoding="utf-8") if l.strip()]
    reqs = [r for r in reqs if int(r.get("seed_idx", 0)) == 0]
    (out / "items.jsonl").write_text("".join(items), encoding="utf-8")
    (out / "requests.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs), encoding="utf-8")
    bp = json.load(open(base / "prepare.json", encoding="utf-8")) if (base / "prepare.json").exists() else {}
    note = ((bp.get("subset_note") + "; ") if bp.get("subset_note") else "") + "same-model re-run: items and seed-0 request bodies copied from the pre-retirement baseline"
    meta = {"wid": wid, "n_items": len(items), "n_requests": len(reqs), "seeds": 1, "est_usd": bp.get("est_usd"), "subset_note": note,
            "dropped_unrenderable": bp.get("dropped_unrenderable"), "model": bp.get("model"), "metric": bp.get("metric"),
            "original_value": bp.get("original_value"), "cap_usd": cap, "baseline_dir": str(base)}
    (out / "prepare.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))


def prepare_paraphrase(wid, cap, variant):
    """Wording sensitivity on the pinned model: the pre-retirement baseline's items and seed-0 request bodies with the
    fixed instruction text reworded (harness/tierb/paraphrase/paraphrases.json, variant p1 or p2). Each replacement is a
    [old, new] pair applied once per message where the old text occurs; item text, options, examples and the model
    stay as in the baseline. A pair that matches no message stops the preparation before any call is made."""
    base = HALF / "runs" / "tierb" / wid
    out = RUNS / wid
    out.mkdir(parents=True, exist_ok=True)
    table = json.loads((HERE / "tierb" / "paraphrase" / "paraphrases.json").read_text(encoding="utf-8"))
    for extra in ("format_adapt.json", "temperature.json"):       # format-adaptation cases (f1, f2) and the temperature check (t1), 2026-10-02
        fa = HERE / "tierb" / "paraphrase" / extra
        if fa.exists():
            for w, v in json.loads(fa.read_text(encoding="utf-8")).items():
                if w.startswith("W"):
                    table.setdefault(w, {}).update(v)
    if wid not in table or variant not in table[wid]:
        raise NeedsHuman(f"no paraphrase {variant} for {wid}")
    entry = table[wid][variant]
    pairs, extra_params = (entry, {}) if isinstance(entry, list) else (entry["pairs"], entry.get("params") or {})
    items = [l for l in open(base / "items.jsonl", encoding="utf-8") if l.strip()]
    reqs = [json.loads(l) for l in open(base / "requests.jsonl", encoding="utf-8") if l.strip()]
    reqs = [r for r in reqs if int(r.get("seed_idx", 0)) == 0]
    from_arm = entry.get("items_from_arm") if isinstance(entry, dict) else None
    if from_arm:                         # same items as an earlier successor arm that ran a cost-cap subset (item ids are shared)
        keep = {json.loads(l)["id"] for l in open(HALF / "runs" / "tierb_p3" / from_arm / wid / "items.jsonl", encoding="utf-8") if l.strip()}
        items = [l for l in items if json.loads(l).get("id") in keep]
        reqs = [r for r in reqs if r.get("id") in keep]
    hits = [0] * len(pairs)
    for r in reqs:
        for m in r["body"]["messages"]:
            if not isinstance(m.get("content"), str):
                continue
            for k, (old, new) in enumerate(pairs):
                if old in m["content"]:
                    m["content"] = m["content"].replace(old, new, 1)
                    hits[k] += 1
    missing = [pairs[k][0][:70] for k, h in enumerate(hits) if h == 0]
    if missing:
        raise NeedsHuman(f"paraphrase {variant} for {wid}: {len(missing)} replacement(s) match no message: {missing}")
    n_seeds = int(SEEDS_OVERRIDE or 1)
    if n_seeds > 1:                      # a sampling check repeats the seed-0 bodies as independent calls (seed_idx 0..n-1)
        reqs = [dict(r, seed_idx=si) for si in range(n_seeds) for r in reqs]
    rewritten = 0
    for r in reqs:                       # on a successor (--model), the bodies are made legal for it as in prepare_from_arm
        if MODEL_OVERRIDE and MODEL_OVERRIDE != r["body"].get("model"):
            r["body"] = normalize_body(dict(r["body"], model=MODEL_OVERRIDE))
            rewritten += 1
        if extra_params:
            r["body"].update(extra_params)
    (out / "items.jsonl").write_text("".join(items), encoding="utf-8")
    (out / "requests.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs), encoding="utf-8")
    bp = json.load(open(base / "prepare.json", encoding="utf-8")) if (base / "prepare.json").exists() else {}
    note = ((bp.get("subset_note") + "; ") if bp.get("subset_note") else "") + (
        f"paraphrase {variant}: {len(pairs)} instruction segment(s) reworded in the baseline's seed-0 request bodies, items and model unchanged; "
        f"replacements applied per message: {hits}" + (f"; {n_seeds} independent calls per item" if n_seeds > 1 else ""))
    if rewritten:
        note += f"; model field rewritten from {bp.get('model')} to {MODEL_OVERRIDE} in {rewritten} bodies"
    if extra_params:
        note += f"; parameters added {extra_params}"
    if from_arm:
        note += f"; items restricted to the {len(reqs)} items of the {from_arm} arm"
    meta = {"wid": wid, "n_items": len(items), "n_requests": len(reqs), "seeds": n_seeds, "est_usd": bp.get("est_usd"), "subset_note": note,
            "dropped_unrenderable": bp.get("dropped_unrenderable"), "model": MODEL_OVERRIDE or bp.get("model"), "source_model": bp.get("model"),
            "metric": bp.get("metric"), "original_value": bp.get("original_value"), "cap_usd": cap, "baseline_dir": str(base),
            "paraphrase": variant, "pairs": pairs, "params_added": extra_params}
    (out / "prepare.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "pairs"}, ensure_ascii=False))


def prepare_from_arm(wid, cap, src_arm, seeds):
    """Repeat of a successor condition (seed-variance check): reuse that condition's items and request bodies verbatim
    and issue `seeds` fresh calls per item, so that the spread between calls is measured on identical requests."""
    base = HALF / "runs" / "tierb_p3" / src_arm / wid
    out = RUNS / wid
    out.mkdir(parents=True, exist_ok=True)
    items = [l for l in open(base / "items.jsonl", encoding="utf-8") if l.strip()]
    src = [json.loads(l) for l in open(base / "requests.jsonl", encoding="utf-8") if l.strip()]
    src = [r for r in src if int(r.get("seed_idx", 0)) == 0]
    reqs = []
    src_model = src[0]["body"].get("model") if src else None
    for r in src:
        for sidx in range(seeds):
            r2 = dict(r, seed_idx=sidx)
            if MODEL_OVERRIDE and MODEL_OVERRIDE != r["body"].get("model"):
                # same body on another deployment of the model (e.g. the BF16 check): only the model field changes
                r2["body"] = dict(r["body"], model=MODEL_OVERRIDE)
            reqs.append(r2)
    (out / "items.jsonl").write_text("".join(items), encoding="utf-8")
    (out / "requests.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs), encoding="utf-8")
    bp = json.load(open(base / "prepare.json", encoding="utf-8")) if (base / "prepare.json").exists() else {}
    note = ((bp.get("subset_note") + "; ") if bp.get("subset_note") else "") + f"repeat of the {src_arm} condition: same items and request bodies, {seeds} fresh calls per item"
    if MODEL_OVERRIDE and src_model and MODEL_OVERRIDE != src_model:
        note += f"; model field rewritten from {src_model} to {MODEL_OVERRIDE}"
    meta = {"wid": wid, "n_items": len(items), "n_requests": len(reqs), "seeds": seeds, "est_usd": (bp.get("est_usd") or 0) * seeds, "subset_note": note,
            "dropped_unrenderable": bp.get("dropped_unrenderable"), "model": bp.get("model"), "metric": bp.get("metric"),
            "original_value": bp.get("original_value"), "cap_usd": cap, "source_dir": str(base), "source_model": src_model}
    (out / "prepare.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))


# ----------------------------------------------------------------------------- parsing + metrics
def parse_output(text, spec):
    spec = (spec or "free text").strip()
    if text is None:
        return None
    t = text.strip()
    if spec.startswith("letter"):
        # most specific first: "Answer: C", "(C)", "C." / "C)" at the start, then any standalone letter
        for pat in (r"(?i)answer\s*(?:is|:)?\s*\(?([A-J])\)?(?![A-Za-z])", r"\(([A-J])\)",
                    r"^\W*([A-J])(?:[\.\):]|\s*$)", r"(?<![A-Za-z])([A-J])(?![A-Za-z])"):
            m = re.search(pat, t)
            if m:
                return m.group(1).upper()
        return None
    if spec.startswith("label from set"):
        labels = re.findall(r"[\w\-/ ]+", spec[spec.find("[") + 1:spec.rfind("]")])
        labels = [l.strip() for l in labels if l.strip()]
        low = t.lower()
        hits = []                                  # first occurrence in the reply, not list order
        for l in labels:
            m = re.search(r"(?<!\w)" + re.escape(l.lower()) + r"(?!\w)", low)
            if m:
                hits.append((m.start(), -len(l), l))   # longer label wins at the same position ("partially correct" over "correct")
        return min(hits)[2] if hits else None
    if spec.startswith("json field"):
        name = spec.split()[-1]
        try:
            obj = json.loads(t)
        except Exception:
            m = re.search(r"\{.*\}", t, re.S)
            try:
                obj = json.loads(m.group(0)) if m else None
            except Exception:
                obj = None
        return None if not isinstance(obj, dict) else obj.get(name)
    if spec.startswith("regex"):
        m = re.search(spec[len("regex"):].strip(), t, re.S)
        return m.group(1) if m else None
    if spec.startswith("number"):
        nums = re.findall(r"-?\d+(?:\.\d+)?", t.replace(",", ""))
        return float(nums[-1]) if nums else None
    return t


def norm(s):
    return re.sub(r"\s+", " ", str(s).strip().lower())


def rouge_l(a, b):
    x, y = norm(a).split(), norm(b).split()
    if not x or not y:
        return 0.0
    dp = [[0] * (len(y) + 1) for _ in range(len(x) + 1)]
    for i in range(len(x)):
        for j in range(len(y)):
            dp[i + 1][j + 1] = dp[i][j] + 1 if x[i] == y[j] else max(dp[i][j + 1], dp[i + 1][j])
    lcs = dp[-1][-1]
    if lcs == 0:
        return 0.0
    p, r = lcs / len(y), lcs / len(x)
    return 2 * p * r / (p + r)


def score_items(preds, golds, name):
    name = (name or "accuracy").lower()
    per = []
    if name in ("accuracy", "exact_match"):
        per = [1.0 if p is not None and norm(p) == norm(g) else 0.0 for p, g in zip(preds, golds)]
        return float(np.mean(per)), per
    if name == "rouge_l":
        per = [rouge_l(p or "", g) for p, g in zip(preds, golds)]
        return float(np.mean(per)), per
    if name in ("mean_error", "mean_abs_error"):
        per = [abs(float(p) - float(g)) if p is not None else np.nan for p, g in zip(preds, golds)]
        return float(np.nanmean(per)), per
    if name == "pearson":
        pairs = [(float(p), float(g)) for p, g in zip(preds, golds) if p is not None]
        a = np.array(pairs)
        return float(np.corrcoef(a[:, 0], a[:, 1])[0, 1]), None
    if name in ("macro_f1", "micro_f1"):
        labels = sorted({norm(g) for g in golds})
        tp = Counter(); fp = Counter(); fn = Counter()
        for p, g in zip(preds, golds):
            p, g = (norm(p) if p is not None else None), norm(g)
            if p == g:
                tp[g] += 1
            else:
                fn[g] += 1
                if p is not None:
                    fp[p] += 1
        if name == "micro_f1":
            t, f_p, f_n = sum(tp.values()), sum(fp.values()), sum(fn.values())
            return (2 * t / max(1, 2 * t + f_p + f_n)), [1.0 if (p is not None and norm(p) == norm(g)) else 0.0 for p, g in zip(preds, golds)]
        f1s = []
        for l in labels:
            pr = tp[l] / max(1, tp[l] + fp[l]); rc = tp[l] / max(1, tp[l] + fn[l])
            f1s.append(0.0 if pr + rc == 0 else 2 * pr * rc / (pr + rc))
        return float(np.mean(f1s)), None
    raise NeedsHuman(f"metric {name!r} not implemented in the runner")


def bootstrap(per, draws=2000):
    per = np.array([x for x in per if x is not None and not (isinstance(x, float) and math.isnan(x))])
    if len(per) == 0:
        return [None, None]
    rng = np.random.default_rng(0)
    b = [rng.choice(per, len(per), replace=True).mean() for _ in range(draws)]
    return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


# ----------------------------------------------------------------------------- pipeline
def load_hook(wid):
    """Optional per-paper Python hook harness/tierb/hooks/<wid>.py. Any of these functions may be defined:
    load_items(cfg) -> rows; render(cfg, row) -> messages; parse(text, cfg) -> prediction;
    score(preds, golds, cfg) -> (value, per_item or None);
    judge_requests(cfg, items, responses) -> battery requests for an LLM-judge stage;
    score_with_judge(cfg, items, responses, judge_responses) -> (value, per_item or None)."""
    path = HERE / "tierb" / "hooks" / f"{wid}.py"
    if not path.exists():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"hook_{wid}", path)
    mod = importlib.util.module_from_spec(spec)
    mod.NeedsHuman = NeedsHuman            # the runner's own class, so hooks can raise it and main() catches it
    mod.RUN_DIR = RUNS / wid               # where this run's archive lives (runs/tierb/<wid>, or the successor arm's dir)
    spec.loader.exec_module(mod)
    return mod


def prepare(wid, cap):
    cfg = load_cfg(wid)
    out = RUNS / wid
    out.mkdir(parents=True, exist_ok=True)
    hook = load_hook(wid)
    rows = hook.load_items(cfg) if hook and hasattr(hook, "load_items") else load_items(cfg)
    rows = apply_subset(rows, cfg["task"].get("subset_rule"))
    label_field = (cfg["items"].get("fields") or {}).get("label")
    id_field = (cfg["items"].get("fields") or {}).get("id")
    seeds = int(cfg["model"].get("seeds") or 1)
    reqs, items, dropped, seen_ids = [], [], 0, set()
    for i, row in enumerate(rows):
        try:
            msgs = hook.render(cfg, row) if hook and hasattr(hook, "render") else render(cfg, row)
        except NeedsHuman as e:
            if i == 0:
                raise
            dropped += 1
            continue
        iid = str(field(row, id_field)) if id_field and id_field in row else str(i)
        if any(x["id"] == iid for x in items[-50:]) or iid in seen_ids:
            iid = f"{iid}#{i}"                    # duplicate source ids would mis-pair replies; make them unique
        seen_ids.add(iid)
        gold = field(row, label_field) if label_field else None
        items.append(plain({"id": iid, "gold": gold, "messages": msgs}))
        for s in range(seeds):
            reqs.append({"id": iid, "seed_idx": s, "meta": {}, "body": body_for(cfg, msgs)})
    # Items are visited in a seeded random order (all seeds of an item stay together), so a run that stops
    # at the cost cap leaves a random subset of items rather than a prefix of the dataset's own order.
    perm = np.random.default_rng(SEED).permutation(len(items))
    items = [items[i] for i in perm]
    reqs = [reqs[i * seeds + s] for i in perm for s in range(seeds)]
    parse = (cfg.get("output") or {}).get("parse", "free text")
    out_guess = 16 if parse.startswith(("letter", "label", "number")) else 120 if parse.startswith("json") else \
        min(int((cfg["model"].get("params") or {}).get("max_tokens") or 400), 400)
    if cfg["model"]["id"].startswith(("o1", "o3", "o4", "gpt-5")):
        out_guess += 600                                   # hidden reasoning tokens are billed as output
    elif cfg["model"]["id"].startswith("gemini"):
        out_guess += 500                                   # Gemini thinks even at its lowest level (~330 tokens per call on average, 2026-09-21)
    tin, tout = estimate(reqs, default_out=out_guess)
    tout = out_guess * len(reqs)
    pr = pricing_for(cfg["model"]["id"])
    est = tin / 1e6 * pr["input"] + tout / 1e6 * pr["output"]
    note = None
    if est > cap and len(items) > 30:
        frac = cap / est
        keep = set(str(x["id"]) for x in apply_subset(items, "all", cap_fraction=frac))
        items = [x for x in items if x["id"] in keep]
        reqs = [r for r in reqs if r["id"] in keep]
        tin, _ = estimate(reqs, default_out=out_guess)
        tout = out_guess * len(reqs)                          # same output guess as before subsetting
        est = tin / 1e6 * pr["input"] + tout / 1e6 * pr["output"]
        note = f"cost cap ${cap}: seeded random subset of {len(items)} items (seed {SEED})"
    if MAX_ITEMS and len(items) > MAX_ITEMS:
        # daily request quota of the arm's provider: same seeded random subset mechanism as the cost cap
        keep = set(str(x["id"]) for x in apply_subset(items, "all", cap_fraction=MAX_ITEMS / len(items)))
        items = [x for x in items if x["id"] in keep]
        reqs = [r for r in reqs if r["id"] in keep]
        tin, _ = estimate(reqs, default_out=out_guess)
        tout = out_guess * len(reqs)
        est = tin / 1e6 * pr["input"] + tout / 1e6 * pr["output"]
        note = ((note + "; ") if note else "") + f"request quota: seeded random subset of {len(items)} items (seed {SEED})"
    (out / "items.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in items), encoding="utf-8")
    (out / "requests.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs), encoding="utf-8")
    meta = {"wid": wid, "n_items": len(items), "n_requests": len(reqs), "seeds": seeds, "est_usd": round(est, 2),
            "subset_note": note, "dropped_unrenderable": dropped, "model": cfg["model"]["id"], "metric": cfg["metric"]["name"],
            "original_value": cfg["metric"].get("original_value"), "cap_usd": cap}
    (out / "prepare.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if (out / "needs_human.txt").exists():
        (out / "needs_human.txt").unlink()               # a successful prepare supersedes an older failure note
    print(json.dumps(meta))
    return meta


def analyze(wid):
    cfg = load_cfg(wid)
    out = RUNS / wid
    items = [json.loads(l) for l in open(out / "items.jsonl", encoding="utf-8") if l.strip()]
    res = load_results(out)
    seeds = int(cfg["model"].get("seeds") or 1)
    hook = load_hook(wid)
    judge_res = load_results(out / "judge") if (out / "judge").exists() else {}
    # archives made before ids were forced unique: pair replies by request hash when ids repeat
    from openai_client import sha256 as _sha
    dup_ids = len({it["id"] for it in items}) < len(items)
    by_sha = {}
    if dup_ids:                                   # read every archived call: load_results() collapses duplicate ids
        for line in open(out / "calls.jsonl", encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if r.get("status") == 200:
                    by_sha[(r.get("sha_request"), r.get("seed_idx", 0))] = r
    per_seed, unparsed = {}, 0
    for s in range(seeds):
        preds, golds, used, texts = [], [], [], []
        for it in items:
            r = by_sha.get((_sha(body_for(cfg, it["messages"])), s)) if dup_ids else res.get((it["id"], s))
            if not r:
                continue
            text = r["response"]["choices"][0]["message"].get("content")
            p = hook.parse(text, cfg) if hook and hasattr(hook, "parse") else parse_output(text, cfg["output"].get("parse"))
            if p is None:
                unparsed += 1
            preds.append(p); golds.append(it["gold"]); used.append(it); texts.append(r)
        if preds:
            if hook and hasattr(hook, "score_with_judge") and judge_res:
                val, per = hook.score_with_judge(cfg, used, texts, {k: v for k, v in judge_res.items() if k[1] == s})
                score_fn = None
            elif hook and hasattr(hook, "score"):
                val, per = hook.score(preds, golds, cfg)
                score_fn = lambda p, g: hook.score(p, g, cfg)[0]
            else:
                val, per = score_items(preds, golds, cfg["metric"]["name"])
                score_fn = lambda p, g: score_items(p, g, cfg["metric"]["name"])[0]
            if per:
                ci = bootstrap(per)
            elif score_fn is not None and len(preds) > 1:
                # set-level metric (F1, AUC, correlation ...): resample items and recompute the whole statistic
                rng = np.random.default_rng(0)
                vals_b = []
                for _ in range(500):
                    idx = rng.integers(0, len(preds), len(preds))
                    try:
                        vals_b.append(float(score_fn([preds[i] for i in idx], [golds[i] for i in idx])))
                    except Exception:
                        continue
                ci = [float(np.percentile(vals_b, 2.5)), float(np.percentile(vals_b, 97.5))] if len(vals_b) > 50 else None
            else:
                ci = None
            per_seed[s] = {"value": val, "n": len(preds), "ci95": ci, "ci_kind": "item-mean" if per else "set-level resample"}
    vals = [v["value"] for v in per_seed.values()]
    orig = cfg["metric"].get("original_value")
    result = {"wid": wid, "title": cfg.get("title"), "model": cfg["model"]["id"], "metric": cfg["metric"]["name"],
              "original_value": orig, "original_location": cfg["metric"].get("original_location"),
              "reexecution": {"mean_over_seeds": float(np.mean(vals)) if vals else None, "per_seed": per_seed, "unparsed": unparsed},
              "prepare": json.loads((out / "prepare.json").read_text(encoding="utf-8")),
              "served": {"models": sorted({r.get("model_served") for r in res.values() if r.get("model_served")}),
                         "n_fingerprints": len({r.get("system_fingerprint") for r in res.values() if r.get("system_fingerprint")})},
              "approximation": cfg["task"].get("approximation")}
    if MODEL_OVERRIDE:
        result["arm"] = {"model": MODEL_OVERRIDE, "config_model": cfg["model"].get("config_id"), "seeds": cfg["model"].get("seeds"),
                         "config_seeds": cfg["model"].get("config_seeds"), "runs_dir": str(out.relative_to(HALF))}
    if vals and orig is not None and per_seed:
        ci = per_seed[0].get("ci95")
        scale = float(cfg["metric"].get("scale") or (100.0 if (isinstance(orig, (int, float)) and orig > 1.5
                                                            and result["reexecution"]["mean_over_seeds"] <= 1.0) else 1.0))
        ours = result["reexecution"]["mean_over_seeds"] * scale
        result["comparison"] = {"scale_applied": scale, "reexecution_scaled": ours, "delta": ours - float(orig),
                                "original_inside_ci95": (ci is not None and ci[0] is not None and ci[0] * scale <= float(orig) <= ci[1] * scale)}
    (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("wid", "metric", "original_value", "reexecution", "comparison", "served") if k in result}, ensure_ascii=False))
    return result


def main():
    global RUNS, MODEL_OVERRIDE, SEEDS_OVERRIDE, MAX_ITEMS
    ap = argparse.ArgumentParser()
    ap.add_argument("wid")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--judge", action="store_true", help="run the hook's LLM-judge stage on the archived responses")
    ap.add_argument("--cap", type=float, default=40.0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--model", help="successor arm: run the config on this model id instead of the paper's")
    ap.add_argument("--arm", help="label for the successor arm's archive directory (default: the model id)")
    ap.add_argument("--seeds", type=int, help="passes per item for this run (successor arms use 1)")
    ap.add_argument("--max-items", type=int, help="seeded random subset of at most this many items (provider request quotas)")
    ap.add_argument("--paraphrase", help="wording check on the pinned model: p1 or p2 from harness/tierb/paraphrase/paraphrases.json")
    ap.add_argument("--copy-from", help="repeat of a successor condition: copy that arm's items and request bodies and issue --seeds fresh calls per item")
    a = ap.parse_args()
    if a.seeds:
        SEEDS_OVERRIDE = a.seeds
    if a.max_items:
        MAX_ITEMS = a.max_items
    if a.arm and not a.model:
        RUNS = HALF / "runs" / "tierb_p3" / a.arm      # an arm label alone (same pinned model, e.g. the temperature check) never writes into the baseline directory
    if a.model:
        MODEL_OVERRIDE = a.model
        RUNS = HALF / "runs" / "tierb_p3" / (a.arm or a.model)
    out = RUNS / a.wid
    try:
        if a.prepare or a.dry_run or (a.run and not (out / "requests.jsonl").exists()):
            cfg0 = json.loads((CONFIGS / f"{a.wid}.json").read_text(encoding="utf-8"))
            if a.paraphrase:
                prepare_paraphrase(a.wid, a.cap, a.paraphrase)                     # wording check: reworded instructions, same model
            elif a.copy_from:
                prepare_from_arm(a.wid, a.cap, a.copy_from, SEEDS_OVERRIDE or 1)   # seed-variance check of a successor condition
            elif MODEL_OVERRIDE and MODEL_OVERRIDE == cfg0["model"]["id"] and (HALF / "runs" / "tierb" / a.wid / "requests.jsonl").exists():
                prepare_from_baseline(a.wid, a.cap)      # drift control: same items, same bodies, later date
            else:
                prepare(a.wid, a.cap)
        if a.dry_run or a.run:
            reqs = [json.loads(l) for l in open(out / "requests.jsonl", encoding="utf-8") if l.strip()]
            run_battery(reqs, out, a.cap, workers=a.workers, dry_run=a.dry_run, label=a.wid)
        if a.judge:
            hook = load_hook(a.wid)
            if not (hook and hasattr(hook, "judge_requests")):
                raise NeedsHuman("no judge_requests() in the hook")
            cfg = load_cfg(a.wid)
            items = [json.loads(l) for l in open(out / "items.jsonl", encoding="utf-8") if l.strip()]
            jreqs = hook.judge_requests(cfg, items, load_results(out))
            for r in jreqs:                       # hook-built bodies use the paper's sampling fields; reasoning successors reject them
                r["body"] = normalize_body(r["body"])
            (out / "judge").mkdir(exist_ok=True)
            (out / "judge" / "requests.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in jreqs), encoding="utf-8")
            run_battery(jreqs, out / "judge", a.cap, workers=a.workers, dry_run=a.dry_run, label=f"{a.wid}-judge")
        if a.analyze:
            analyze(a.wid)
    except NeedsHuman as e:
        (out / "needs_human.txt").write_text(str(e), encoding="utf-8")
        print(f"NEEDS_HUMAN {a.wid}: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
